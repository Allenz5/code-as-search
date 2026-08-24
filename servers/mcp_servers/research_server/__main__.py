"""MCP server for research runs: the run directory and its working memory.

Split out of the websearch server, which is a Firecrawl client and has no business
owning a research run's bookkeeping. The two still meet on disk — `search` and
`scrape` charge credits and file pages against the active run — but that meeting
point is `mcp_servers.runs`, not a shared process.

One profile only. Nothing here returns a page body, so there is nothing to keep
out of the director's context.

    python -m mcp_servers.research_server
"""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from .. import runs
from . import memory


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    def research_start(objective: str) -> str:
        """Begin a research run. Creates its directory and makes it the active run.

        Args:
            objective: What the research is trying to find out.
        """
        run_id = runs.new_run(objective)
        return f"run {run_id} started\ndirectory: {runs.run_dir(run_id)}"

    @mcp.tool()
    def research_list(limit: int = 10) -> str:
        """List recent research runs, newest first: what each was after, and how far it got.

        Args:
            limit: How many runs to show (default 10).
        """
        metas = runs.recent(limit)
        if not metas:
            return "no runs yet"

        blocks = []
        for meta in metas:
            state = memory.fold(memory.read_records(runs.memory_path(meta["id"])))
            questions = state["question"].values()
            resolved = sum(1 for q in questions if q.get("status") == "resolved")
            objective = meta["objective"]
            if len(objective) > 200:
                objective = objective[:200].rstrip() + "…"
            blocks.append(
                f"{meta['id']}  {meta['created'][:10]}  {meta['credits']} credits  "
                f"{'report written' if (runs.run_dir(meta['id']) / 'report.md').exists() else 'no report'}\n"
                f"  {objective}\n"
                f"  {len(questions)} questions ({resolved} resolved) · {len(state['finding'])} findings"
            )
        return "\n\n".join(blocks)

    @mcp.tool()
    def research_resume(run_id: str, feedback: str) -> str:
        """Continue an earlier run: make it active again and return everything it knows.

        What the run already established stands — a resolved question is not to be
        researched again. The feedback is appended as a note so it survives a
        compaction, and any existing report.md is kept as report-<n>.md.

        Args:
            run_id: From research_list.
            feedback: What the earlier result missed, got wrong, or should chase
                instead. This is what makes it a continuation and not a rerun.
        """
        runs.set_active(run_id)
        kept = runs.archive_report(run_id)
        path = runs.memory_path(run_id)
        memory.append(path, [{"t": "note", "text": f"Resumed. Feedback: {feedback}"}])
        head = f"resumed {run_id}"
        if kept:
            head += f" — previous report kept as {kept}"
        return f"{head}\n\n" + memory.render(runs.load_meta(run_id), memory.read_records(path))

    @mcp.tool()
    def memory_append(records: list[dict[str, Any]]) -> str:
        """Write to working memory. Appends records; never rewrites.

        Each record needs a type `t`:
          {"t": "question", "text": "..."}                     -> new question
          {"t": "question", "id": "q1", "status": "resolved", "answer": "..."}
          {"t": "finding", "q": "q1", "text": "...", "url": "https://..."}
          {"t": "note", "text": "..."}
        Omit `id` to create; pass `id` with only the changed fields to update.
        IDs are assigned here and returned — never invent one.
        """
        ids = memory.append(runs.memory_path(), records)
        return "appended: " + ", ".join(ids)

    @mcp.tool()
    def memory_read(question_id: str | None = None) -> str:
        """Read working memory as Markdown.

        Args:
            question_id: Return only this question and its findings. Omit for everything.
        """
        return memory.render(
            runs.load_meta(),
            memory.read_records(runs.memory_path()),
            question_id,
        )


def build() -> MCPServer:
    mcp = MCPServer(name="research")
    register(mcp)
    return mcp


def main() -> None:
    build().run("stdio")


if __name__ == "__main__":
    main()
