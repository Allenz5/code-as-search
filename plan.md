# Code as Search — Long-Horizon Research Agent

A question-driven research agent that browses the web, forms hypotheses, and keeps searching
until its own open questions are resolved or explicitly blocked.

- **Harness:** Claude Code. We ship an MCP server, a subagent, and a skill — no orchestration code.
- **Web access:** our own MCP server over the Firecrawl HTTP API (search + scrape + interact).
- **Working memory:** an append-only JSONL event log on disk.

---

## 1. Core idea

**Questions are the unit of work.** The agent stops when every open question in its memory file
is `resolved` or `blocked`, not when it feels satisfied. Every search and page visit cites a
question ID. Questions discovered mid-run become work items, so the agent goes deeper rather
than wider-and-shallower.

**Memory lives on disk; conversation history is disposable.** The research state is
`memory.jsonl`, not the context window. When a long session auto-compacts, nothing is lost —
it was already appended to a file. Runs survive a crash and can be resumed.

**The director never sees raw page content.** Page bodies reach the explorer subagent only.
This is the rule the whole layout is built to enforce.

---

## 2. Layout

```
code-as-search/
├── .mcp.json                       registers the director profile
├── .claude/
│   ├── agents/page-explorer.md     subagent + inline explorer-profile server
│   └── skills/research/SKILL.md    the director loop → /research <objective>
├── server/
│   ├── __main__.py                 FastMCP, --profile director|explorer
│   ├── firecrawl.py                HTTP client
│   ├── sessions.py                 interact session registry + reaper
│   ├── memory.py                   event log: append, compact, render
│   └── runs.py                     run dirs, IDs, .active, budget
└── search/<id>/                    gitignored
```

Run state lives on disk at `search/.active`, so both server processes agree on the current run
and `--resume` works.

---

## 3. MCP server

One codebase, stdio transport, two profiles. `.mcp.json` registers only the director profile;
`page-explorer.md` declares the explorer profile inline via `mcpServers`. The main session
therefore cannot see a scrape tool.

### Director profile

| tool | wraps | returns |
|---|---|---|
| `research_start(objective, budget?)` | — | creates `search/<id>/`, writes `.active`, returns run ID |
| `search(query, limit, ...)` | `POST /v2/search` | title + URL + description + highlights. No page bodies. |
| `memory_append(records)` | — | assigned IDs |
| `memory_read(question_id?)` | — | rendered Markdown |

`search` passes through `sources`, `categories` (`github`/`research`/`pdf`), `includeDomains`,
`excludeDomains`, `tbs` (recency, e.g. `qdr:w`), `country`. It does **not** expose
`scrapeOptions` — that is how page bodies would reach the director.

### Explorer profile

| tool | wraps | notes |
|---|---|---|
| `scrape(url, formats?, wait_for?)` | `POST /v2/scrape` | returns markdown to the subagent and writes `pages/<pid>.md`; `scrape_id` comes from `data.metadata.scrapeId` |
| `interact(scrape_id, prompt \| code, language?, timeout?)` | `POST /v2/scrape/{id}/interact` | reuses the live browser session |
| `interact_stop(scrape_id)` | `DELETE /v2/scrape/{id}/interact` | also clears the registry entry |

Full markdown in the subagent's context is intended — that context is discarded on return.

---

## 4. Working memory

`<id>` is `YYYYMMDD-xxxx` (date + 4 hex) — sortable and greppable.

```
search/<id>/
  run.json          objective, budget, credits spent, status
  memory.jsonl      append-only event log — the source of truth
  pages/<pid>.md    raw captures
  report.md         final synthesis
```

### Event log

Three record types. One JSON object per line. An update is a re-append of the same `id` carrying
only the changed fields; the reader merges. Nothing is rewritten.

```jsonl
{"t":"question","id":"q1","text":"Who led the Series B?","status":"open"}
{"t":"finding","id":"f1","q":"q1","text":"Northwind led the $40M round","url":"https://..."}
{"t":"finding","id":"f2","q":"q1","text":"SEC filing lists Northwind as lead","url":"https://..."}
{"t":"question","id":"q1","status":"resolved","answer":"Northwind Capital"}
{"t":"question","id":"q2","text":"Was Northwind also in the Series A?","status":"open"}
{"t":"note","id":"n1","text":"TechCrunch and the SEC filing disagree on round size."}
```

- `question` — `text`, `status` (`open` | `resolved`), `answer` (when resolved)
- `finding` — `q` (question ID), `text`, `url`
- `note` — `text`, for anything that isn't tied to one question: a contradiction between sources,
  a dead end worth not repeating

The list order is the priority order; the director works from the top. No tree, no priority
field, no confidence scores — if a finding is shaky, the agent says so in its `text`.

### Reading

`memory_read(question_id?)` folds the log — for each `(t, id)`, later records shallow-merge onto
earlier ones — and renders Markdown. A pure function, no model involved. With no argument it
returns everything, which stays small because findings are one line each:

```markdown
# Objective
Who backed Acme, and when?

## Open
- [q2] Was Northwind also in the Series A?

## Resolved
- [q1] Who led the Series B? → Northwind Capital
  - [f1] Northwind led the $40M round — https://...
  - [f2] SEC filing lists Northwind as lead — https://...

## Notes
- [n1] TechCrunch and the SEC filing disagree on round size.
```

Passing a `question_id` returns just that question and its findings.

`memory_append` assigns IDs for new records and returns them, so the agent never invents
colliding ones.

Verification is a rule in the director's prompt, not in the tool: don't resolve a question on a
single source unless that source is authoritative, and say which it was in the `answer`.

---

## 5. Agents

### Director — `.claude/skills/research/SKILL.md`, invoked as `/research <objective>`

The main session. The skill body is the loop:

```
1. research_start(objective) → run id
2. Decompose into 2–5 root questions → memory_append
3. Repeat:
     memory_read()
     take the top open question(s)
     search(...) → pick the URLs worth reading
     delegate to page-explorer — up to 3 in parallel when the pages are
       independent, one at a time when the next choice depends on this one
     append findings / new questions / resolutions
4. Stop when nothing is left under "Open" and the last 2 turns produced no new findings
   and no new questions; or the budget is exhausted, in which case the report is partial
   and lists what remains open
5. Write report.md
```

The skill also tells it to re-read `memory_read()` every few actions, which is what makes
compaction survivable: whatever the summarizer drops, the next read restores.

### Page Explorer — `.claude/agents/page-explorer.md`

```yaml
---
name: page-explorer
description: Fetches one URL and answers a specific research question from it.
             Handles dynamic pages via browser interaction. Returns findings, never raw content.
model: sonnet
tools: mcp__cas_explorer__scrape, mcp__cas_explorer__interact, mcp__cas_explorer__interact_stop
mcpServers:
  - cas_explorer:
      type: stdio
      command: ./.venv/bin/python
      args: ["-m", "server", "--profile", "explorer"]
---
```

`mcpServers` is a YAML *list* of entries, not a mapping. As a mapping the server never
connects, the `tools` allowlist then matches nothing, and the subagent spawns with zero tools.

Invoked in the foreground, up to three at once — the director needs the batch before choosing
its next action, but pages that don't inform each other are no reason to read in turn. Each
prompt carries the URL, the question IDs it is answering, the purpose, and what is already known
so it doesn't return duplicates. It returns a fixed template:

```
ANSWERED: yes | partial | no
SUMMARY: ≤150 words
CLAIMS:  - <atomic claim> | quote: "..." | confidence: 0.0-1.0
LINKS:   - <url> | why worth following
NEW QUESTIONS: - <question this page raised>
INTERACTED: yes/no    CREDITS: n    PAGE_ID: p3
```

It does not write to memory. One writer keeps the log coherent.

### Parallel explorers

Each explorer subagent gets its own server process, so the state they share is guarded across
processes, not just across threads: `server/lock.py` wraps every read-modify-write in an
`flock`, and `run.json` is replaced atomically rather than truncated in place. That covers
credit accounting, `pages/<pid>.md` id allocation, and the session registry.

A session in the registry records the PID that opened it. Startup reaping takes only the
sessions whose owner is gone, so a starting explorer cannot close the browser session of a
sibling that is still reading. The 120s age cap still applies to everyone.

Budget is checked per call, so a batch already in flight can overshoot the ceiling by a few
credits. The director is told to stop batching as it approaches the limit.

---

## 6. Build order

1. `memory.py` — append, compact, render. Pure functions, unit-tested with no model in the loop.
2. `runs.py` — run dirs, IDs, `.active`, budget accounting.
3. `firecrawl.py` + `sessions.py` — HTTP client and reaper.
4. FastMCP wiring, both profiles; register the director profile in `.mcp.json`; smoke-test `search`.
5. `page-explorer.md`; test on one static page and one JS-heavy page needing `interact`.
6. `SKILL.md`; end-to-end on a question needing ~5 searches and one conflicting source.
7. `report.md` synthesis and `--resume`.
```
