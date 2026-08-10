# Code as Search

A long-horizon web research agent that runs inside Claude Code. It is question-driven: it
decomposes an objective into questions, searches, reads pages through a subagent, writes what
it learns to a file, and keeps going until its own open questions are answered.

See [plan.md](plan.md) for the design.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
echo "FIRECRAWL_API_KEY=fc-..." > .env
```

## Use

Inside Claude Code, from this directory:

```
/research <what you want to find out>
```

The run lands in `search/<id>/`:

```
run.json        objective, budget, credits spent
memory.jsonl    working memory — the append-only source of truth
pages/          raw page captures
report.md       the answer
```

`memory.jsonl` is the research state, not the context window, so a run survives compaction,
interruption and restarts. To pick up an earlier run, point `search/.active` at its id.

## How it fits together

| piece | role |
|---|---|
| `.claude/skills/research/SKILL.md` | the director loop — the main session runs this |
| `.claude/agents/page-explorer.md` | subagent that reads one page and reports findings |
| `server/` | one MCP server, two profiles |

The MCP server runs as two profiles so page content cannot reach the director:

- **director** (`.mcp.json`) — `research_start`, `search`, `memory_append`, `memory_read`
- **explorer** (declared inside `page-explorer.md`) — `scrape`, `interact`, `interact_stop`

The main session has no scrape tool at all, so raw pages stay in the subagent's context and
on disk. Only findings come back.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests    # 38 tests, no network
.venv/bin/python tests/smoke.py                   # live API, spends a few credits
```

`interact` needs a free browser slot. On a plan with `maxConcurrency: 2`, a backlog of queued
jobs will block it; the tool reports that and tells the agent to work from the scrape instead.
Check with:

```bash
.venv/bin/python -c "from server.firecrawl import Firecrawl; print(Firecrawl()._call('GET','/team/queue-status'))"
```
