"""MCP tool tests against an in-memory server and a fake Firecrawl. No network."""

import asyncio
import sys
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp import Client  # noqa: E402

from server import __main__ as srv, memory, runs, sessions  # noqa: E402
from server.firecrawl import Saturated  # noqa: E402


class FakeFirecrawl:
    """Records calls; returns the shapes the real API returns."""

    def __init__(self):
        self.calls = []
        self.saturated = False
        self.stopped = []

    def search(self, query, limit=8, **opts):
        self.calls.append(("search", query, opts))
        return {
            "creditsUsed": 2,
            "data": {"web": [
                {"title": "Result one", "url": "https://one.example",
                 "description": "first snippet"},
                {"title": "Result two", "url": "https://two.example",
                 "description": "second snippet"},
            ]},
        }

    def scrape(self, url, wait_for=0, max_age=None):
        self.calls.append(("scrape", url, wait_for))
        return {"data": {
            "markdown": f"# Page at {url}\n\nbody text",
            "metadata": {"scrapeId": "sid-1", "creditsUsed": 1, "statusCode": 200,
                         "cacheState": "miss", "title": "A Page"},
        }}

    def interact(self, scrape_id, prompt=None, code=None, language="node", timeout=30):
        self.calls.append(("interact", scrape_id, prompt, timeout))
        if self.saturated:
            raise Saturated("concurrent jobs")
        return {"success": True, "output": "the heading says Example Domain"}

    def interact_stop(self, scrape_id):
        self.stopped.append(scrape_id)
        return {"success": True}


def run(coro):
    return asyncio.run(coro)


def text(result):
    return "\n".join(c.text for c in result.content if getattr(c, "type", "") == "text")


class ToolTest(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        # Point every module at a throwaway search/ directory.
        for mod, attr, val in (
            (runs, "SEARCH", root / "search"),
            (runs, "ACTIVE", root / "search" / ".active"),
            (sessions, "REGISTRY", root / "search" / ".sessions.json"),
        ):
            old = getattr(mod, attr)
            setattr(mod, attr, val)
            self.addCleanup(setattr, mod, attr, old)

        self.fc = FakeFirecrawl()
        old_client = srv._client
        srv._client = self.fc
        self.addCleanup(setattr, srv, "_client", old_client)

        self.director = srv.build("director")
        self.explorer = srv.build("explorer")

    def call(self, server, tool, args=None):
        async def go():
            async with Client(server) as c:
                return text(await c.call_tool(tool, args or {}))
        return run(go())

    def start_run(self, budget=100):
        return self.call(self.director, "research_start",
                         {"objective": "test objective", "budget": budget}).split()[1]

    # --- profiles ---------------------------------------------------------

    def test_profiles_expose_disjoint_tools(self):
        async def names(server):
            async with Client(server) as c:
                return sorted(t.name for t in (await c.list_tools()).tools)
        d, e = run(names(self.director)), run(names(self.explorer))
        self.assertEqual(d, ["memory_append", "memory_read", "research_start", "search"])
        self.assertEqual(e, ["interact", "interact_stop", "scrape"])
        self.assertFalse(set(d) & set(e), "a page tool leaked into the director")

    # --- director ---------------------------------------------------------

    def test_research_start_creates_the_run_and_activates_it(self):
        run_id = self.start_run()
        self.assertTrue((runs.SEARCH / run_id / "memory.jsonl").exists())
        self.assertTrue((runs.SEARCH / run_id / "pages").is_dir())
        self.assertEqual(runs.active(), run_id)

    def test_search_renders_results_and_charges_credits(self):
        self.start_run()
        out = self.call(self.director, "search", {"query": "acme series b", "limit": 3})
        self.assertIn("https://one.example", out)
        self.assertIn("first snippet", out)
        self.assertIn("2/100 credits", out)
        self.assertEqual(runs.load_meta()["credits"], 2)

    def test_search_passes_filters_through(self):
        self.start_run()
        self.call(self.director, "search", {"query": "x", "tbs": "qdr:w",
                                            "include_domains": ["sec.gov"]})
        _, _, opts = self.fc.calls[-1]
        self.assertEqual(opts["tbs"], "qdr:w")
        self.assertEqual(opts["includeDomains"], ["sec.gov"])

    def test_memory_round_trip_through_the_tools(self):
        self.start_run()
        out = self.call(self.director, "memory_append", {"records": [
            {"t": "question", "text": "Who led it?"},
            {"t": "finding", "q": "q1", "text": "Northwind led", "url": "https://a"},
        ]})
        self.assertIn("q1", out)
        self.assertIn("f1", out)

        self.call(self.director, "memory_append", {"records": [
            {"t": "question", "id": "q1", "status": "resolved", "answer": "Northwind"}]})
        out = self.call(self.director, "memory_read")
        self.assertIn("→ Northwind", out)
        self.assertIn("test objective", out)

    def test_memory_read_can_focus_one_question(self):
        self.start_run()
        self.call(self.director, "memory_append", {"records": [
            {"t": "question", "text": "first"}, {"t": "question", "text": "second"}]})
        out = self.call(self.director, "memory_read", {"question_id": "q2"})
        self.assertIn("second", out)
        self.assertNotIn("first", out)

    def test_budget_exhaustion_blocks_search_and_says_what_to_do(self):
        self.start_run(budget=1)
        self.call(self.director, "search", {"query": "one"})  # spends 2 of 1
        out = self.call(self.director, "search", {"query": "two"})
        self.assertIn("budget exhausted", out)
        self.assertIn("report.md", out)

    # --- explorer ---------------------------------------------------------

    def test_scrape_returns_markdown_and_saves_the_page(self):
        self.start_run()
        out = self.call(self.explorer, "scrape", {"url": "https://one.example"})
        self.assertIn("body text", out)
        self.assertIn("page_id: p1", out)
        self.assertIn("scrape_id: sid-1", out)

        saved = (runs.run_dir() / "pages" / "p1.md").read_text()
        self.assertIn("https://one.example", saved)
        self.assertIn("body text", saved)

    def test_page_ids_increment_across_scrapes(self):
        self.start_run()
        self.call(self.explorer, "scrape", {"url": "https://one.example"})
        out = self.call(self.explorer, "scrape", {"url": "https://two.example"})
        self.assertIn("page_id: p2", out)

    def test_scrape_alone_registers_no_session(self):
        # A scrape has no live browser behind it; only interact opens one.
        self.start_run()
        self.call(self.explorer, "scrape", {"url": "https://one.example"})
        self.assertEqual(sessions._load(), {})

    def test_interact_returns_output_and_the_session_clock(self):
        self.start_run()
        out = self.call(self.explorer, "interact",
                        {"scrape_id": "sid-1", "prompt": "read the heading"})
        self.assertIn("Example Domain", out)
        self.assertIn("session closes in", out)
        self.assertIn("sid-1", sessions._load())

    def test_interact_timeout_is_capped(self):
        self.start_run()
        self.call(self.explorer, "interact",
                  {"scrape_id": "sid-1", "prompt": "x", "timeout": 999})
        self.assertEqual(self.fc.calls[-1][3], 60)

    def test_interact_needs_a_prompt_or_code(self):
        self.start_run()
        self.assertIn("error", self.call(self.explorer, "interact", {"scrape_id": "sid-1"}))

    def test_saturated_account_gives_actionable_guidance_not_a_crash(self):
        self.start_run()
        self.fc.saturated = True
        out = self.call(self.explorer, "interact",
                        {"scrape_id": "sid-1", "prompt": "read the heading"})
        self.assertIn("concurrency", out)
        self.assertIn("Do not retry", out)
        self.assertNotIn("sid-1", sessions._load(), "a failed interact must not register a session")

    def test_interact_stop_clears_the_registry(self):
        self.start_run()
        self.call(self.explorer, "interact", {"scrape_id": "sid-1", "prompt": "x"})
        out = self.call(self.explorer, "interact_stop", {"scrape_id": "sid-1"})
        self.assertIn("closed", out)
        self.assertEqual(sessions._load(), {})
        self.assertEqual(self.fc.stopped, ["sid-1"])

    # --- the reaper -------------------------------------------------------

    def test_reaper_stops_sessions_past_the_age_limit(self):
        sessions.note_open("old-1", "https://x")
        self.assertEqual(sessions.reap(self.fc, max_age=0.0), ["old-1"])
        self.assertEqual(self.fc.stopped, ["old-1"])
        self.assertEqual(sessions._load(), {})

    def test_reaper_leaves_young_sessions_alone(self):
        sessions.note_open("fresh", "https://x")
        self.assertEqual(sessions.reap(self.fc, max_age=300), [])
        self.assertIn("fresh", sessions._load())

    def test_reaper_drops_sessions_the_api_has_already_forgotten(self):
        def boom(_):
            raise RuntimeError("404 Browser session not found")
        self.fc.interact_stop = boom
        sessions.note_open("ghost", "https://x")
        self.assertEqual(sessions.reap(self.fc, max_age=0.0), ["ghost"])
        self.assertEqual(sessions._load(), {}, "a ghost session must still leave the registry")

    # --- parallel explorers -----------------------------------------------

    def test_startup_reaping_spares_a_live_siblings_session(self):
        sessions.note_open("sibling", "https://x")  # owned by this, a running process
        self.assertEqual(sessions.reap_orphans(self.fc), [])
        self.assertIn("sibling", sessions._load(),
                      "startup reaping killed a session another explorer is still reading")

    def test_startup_reaping_takes_sessions_whose_owner_is_gone(self):
        sessions.note_open("orphan", "https://x")
        registry = sessions._load()
        registry["orphan"]["pid"] = 4_194_303  # no such process
        sessions._save(registry)
        self.assertEqual(sessions.reap_orphans(self.fc), ["orphan"])
        self.assertEqual(sessions._load(), {})

    def test_concurrent_spending_loses_no_credits(self):
        self.start_run()
        self.run_together([lambda: runs.spend(1)] * 12)
        self.assertEqual(runs.load_meta()["credits"], 12)

    def test_concurrent_scrapes_get_distinct_page_ids(self):
        self.start_run()
        ids, guard = [], threading.Lock()

        def save(i):
            page_id = srv._save_page(f"https://{i}.example", f"body {i}")
            with guard:
                ids.append(page_id)

        self.run_together([lambda i=i: save(i) for i in range(8)])
        self.assertEqual(sorted(ids), sorted(f"p{n}" for n in range(1, 9)))

    def run_together(self, calls):
        threads = [threading.Thread(target=c) for c in calls]
        for t in threads:
            t.start()
        for t in threads:
            t.join()


if __name__ == "__main__":
    unittest.main(verbosity=2)
