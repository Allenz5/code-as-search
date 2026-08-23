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
This is the rule the whole layout is built to enforce — and it is enforced by capability, not
by instruction: the explorer profile is declared inside the subagent that needs it and is
registered nowhere else, so the director has no tool that returns a page body.

This is also why none of this ships as a plugin. Plugin-shipped agents ignore the `mcpServers`
frontmatter field for security reasons — `command:` is an arbitrary executable, so a plugin
could otherwise smuggle in servers that never appear in its manifest. But that field is the
only mechanism that gives a subagent a server the main conversation lacks. Permissions are no
substitute: `deny` is inherited by subagents, so denying the director denies the explorer with
it. Tested, not assumed.

---

## 2. Layout

```
claude-toolkit/
├── agents/
│   ├── page-explorer.md.in         subagent + inline explorer-profile server
│   └── pdf-reader.md               no MCP, so no template needed
├── skills/research/SKILL.md        the director loop → /research <objective>
├── servers/mcp_servers/firecrawl_server/
│   ├── __main__.py                 FastMCP, --profile director|explorer
│   ├── firecrawl.py                HTTP client
│   ├── sessions.py                 interact session registry + reaper
│   ├── memory.py                   event log: append, compact, render
│   └── runs.py                     run dirs, IDs, .active, budget
├── scripts/install.sh              renders agents, links them, registers directors
├── build/agents/                   rendered agents, gitignored
└── search/<id>/                    gitignored
```

Run state lives on disk at `search/.active`, so both server processes agree on the current run
and `--resume` works.

Nothing is installed by copying. `make install` symlinks agents into `~/.claude/agents/` and
skills into `~/.claude/skills/`, and registers the director profiles at user scope, so the repo
stays the source of truth and everything works from any directory.

**Agents are checked in as `.md.in` templates.** A user-level agent may declare its own MCP
servers — that is what makes the rule above enforceable — but neither `${HOME}` nor `~` expands
in agent frontmatter, so `command:` has to be an absolute path. The template holds
`@@TOOLKIT_ROOT@@` and `install.sh` renders it. Re-run it after moving the repo.

---

## 3. MCP server

One codebase, stdio transport, two profiles. Only the director is registered globally (as
`websearch`, by `install.sh`); `page-explorer.md.in` declares the explorer profile inline via
`mcpServers`, and it exists nowhere else. The main session therefore has no scrape tool.

The three social servers are split the same way — `reddit`, `x` and `xiaohongshu` each take a
`--profile` flag, with `get_post` on the explorer side. Xiaohongshu speaks HTTP rather than
stdio, so its two profiles are two endpoints on one process (`/mcp` and `/mcp/explorer`) rather
than two processes, which would fight over one cookie jar and one browser.

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

### Director — `skills/research/SKILL.md`, invoked as `/research <objective>`

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

### Page Explorer — `agents/page-explorer.md.in`

```yaml
---
name: page-explorer
description: Reads one web page and answers a specific research question from it.
             Handles dynamic pages by interacting with them. Returns findings, never raw content.
model: sonnet
tools: mcp__explorer__scrape, mcp__explorer__interact, mcp__explorer__interact_stop
mcpServers:
  - explorer:
      type: stdio
      command: @@TOOLKIT_ROOT@@/.venv/bin/python
      args: ["-m", "mcp_servers.firecrawl_server", "--profile", "explorer"]
      env:
        PYTHONPATH: @@TOOLKIT_ROOT@@/servers
---
```

Three things here will each silently produce a subagent with zero tools:

- `mcpServers` must be a YAML *list* of entries, not a mapping. As a mapping the server never
  connects and the `tools` allowlist matches nothing.
- The path must be absolute. A relative one follows whatever cwd the agent is spawned with,
  and `${HOME}` / `~` do not expand here — hence the template.
- The agent must not be shipped by a plugin, which ignores this field entirely.

The failure mode is the same in all three cases and says nothing about the cause: *"would be
spawned with zero tools — refusing."*

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
processes, not just across threads: `servers/mcp_servers/firecrawl_server/lock.py` wraps every read-modify-write in an
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
