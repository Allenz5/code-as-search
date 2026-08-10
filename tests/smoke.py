"""End-to-end smoke test: spawn both MCP profiles as subprocesses and drive them.

Hits the live Firecrawl API and spends a few credits. Tool logic is covered by
test_tools.py without a network; this checks that the servers actually boot the
way Claude Code will boot them, and that the real API still answers as expected.

    .venv/bin/python tests/smoke.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp import Client  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

from server import runs  # noqa: E402

PY = str(Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python")
failures: list[str] = []
blocked: list[str] = []


def server(profile):
    """Launch a profile exactly as .mcp.json / page-explorer.md do."""
    return stdio_client(StdioServerParameters(
        command=PY, args=["-m", "server", "--profile", profile]))


def text(result):
    return "\n".join(c.text for c in result.content if getattr(c, "type", "") == "text")


def expect(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        failures.append(label)
        if detail:
            print(f"        {detail}")


def note_blocked(label, why):
    print(f"  SKIP  {label}")
    print(f"        {why}")
    blocked.append(label)


async def director():
    print("\ndirector profile")
    async with Client(server("director")) as c:
        names = sorted(t.name for t in (await c.list_tools()).tools)
        expect("exposes exactly the director tools",
               names == ["memory_append", "memory_read", "research_start", "search"], str(names))
        expect("page tools are unreachable from the director",
               not any(n in names for n in ("scrape", "interact", "interact_stop")))

        out = text(await c.call_tool("research_start",
                                     {"objective": "smoke test run", "budget": 50}))
        run_id = out.split()[1]
        expect("research_start creates a run", (runs.SEARCH / run_id).is_dir(), out)
        expect("run becomes active", runs.active() == run_id)

        out = text(await c.call_tool("memory_append", {"records": [
            {"t": "question", "text": "Does the memory tool assign ids?"},
            {"t": "finding", "q": "q1", "text": "it returned q1", "url": "https://example.com"},
        ]}))
        expect("memory_append assigns and returns ids", "q1" in out and "f1" in out, out)

        await c.call_tool("memory_append", {"records": [
            {"t": "question", "id": "q1", "status": "resolved", "answer": "yes"}]})
        out = text(await c.call_tool("memory_read", {}))
        expect("a question resolves by appending", "→ yes" in out and "smoke test run" in out, out)

        out = text(await c.call_tool("memory_append", {"records": [
            {"t": "finding", "q": "q99", "text": "bad", "url": "https://x"}]}))
        expect("a bad record is refused with a usable message", "q99" in out, out)

        out = text(await c.call_tool("search", {"query": "Firecrawl API", "limit": 3}))
        expect("search returns live results", "http" in out and "credits" in out, out[:300])
        expect("search leaks no page bodies", len(out) < 4000, f"{len(out)} chars")
        print("        " + "\n        ".join(out.splitlines()[:4]))


async def explorer():
    print("\nexplorer profile")
    async with Client(server("explorer")) as c:
        names = sorted(t.name for t in (await c.list_tools()).tools)
        expect("exposes exactly the explorer tools",
               names == ["interact", "interact_stop", "scrape"], str(names))
        expect("search and memory are unreachable from the explorer",
               not any(n in names for n in ("search", "memory_append", "memory_read")))

        out = text(await c.call_tool("scrape", {"url": "https://example.com"}))
        expect("scrape returns live markdown", "Example Domain" in out, out[:300])
        expect("scrape reports page_id and scrape_id",
               "page_id: p1" in out and "scrape_id: " in out)

        pages = list((runs.run_dir() / "pages").glob("*.md"))
        expect("scrape saved the page to disk", len(pages) == 1, str(pages))
        expect("the saved page records its url",
               bool(pages) and "https://example.com" in pages[0].read_text())

        scrape_id = out.split("scrape_id: ")[1].split()[0]
        out = text(await c.call_tool("interact", {
            "scrape_id": scrape_id,
            "prompt": "What is the exact text of the main heading?",
            "timeout": 40,
        }))
        if "concurrency limit" in out:
            note_blocked("interact drives the live page",
                         "Firecrawl account is at its concurrency cap; the tool degraded "
                         "gracefully as designed (see test_tools.py for the covered path)")
        else:
            expect("interact drives the live page", "Example Domain" in out, out[:400])
            expect("interact reports the session clock", "session closes in" in out)

        out = text(await c.call_tool("interact_stop", {"scrape_id": scrape_id}))
        expect("interact_stop always clears the session",
               "closed" in out or "already gone" in out, out)


async def main():
    await director()
    await explorer()

    meta = runs.load_meta()
    print(f"\ncredits: {meta['credits']}/{meta['budget']}   run: {meta['id']}")
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("ALL PASSED" + (f"  ({len(blocked)} blocked by account limits)" if blocked else ""))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
