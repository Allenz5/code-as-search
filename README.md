# claude-toolkit

A Claude Code plugin: a long-horizon research agent, plus the MCP servers it reads the world
through. Installed once, it loads in every project.

## Install

```bash
make setup
ln -s "$PWD" ~/.claude/skills/claude-toolkit
echo "FIRECRAWL_API_KEY=fc-..." > .env
```

`make setup` builds four dependency trees — a Python venv for the servers in
`servers/mcp_servers/`, a separate uv-managed venv for LinkedIn, npm packages for X, and a Go
binary for Xiaohongshu. `make check` shows what Claude Code can actually reach.

## The research agent

```
/claude-toolkit:research <what you want to find out>
```

It is question-driven: it decomposes an objective into questions, searches, reads pages through
subagents, writes what it learns to disk, and keeps going until its own open questions are
answered. See [plan.md](plan.md) for the design.

A run lands in `search/<id>/`:

```
run.json        objective, status, credits spent
memory.jsonl    working memory — the append-only source of truth
pages/          raw page captures
report.md       the answer
```

`memory.jsonl` is the research state, not the context window, so a run survives compaction,
interruption and restarts. To resume an earlier run, point `search/.active` at its id.

### Why raw pages never reach the main loop

One codebase in `servers/mcp_servers/firecrawl_server/` runs as two processes, and the split is
the whole point:

| profile | server | tools | who gets it |
|---|---|---|---|
| director | `research` | `research_start` `search` `memory_append` `memory_read` | the main loop |
| explorer | `explorer` | `scrape` `interact` `interact_stop` | `page-explorer` subagent |

The main loop has no scrape tool at all, so page content stops in the subagent's context and on
disk — only findings come back. `deny: WebFetch` in `.claude/settings.json` closes the last door.

## Servers

| | `servers/` | runtime | transport | login |
|---|---|---|---|---|
| research / explorer | `mcp_servers/firecrawl_server` | Python | stdio | Firecrawl API key |
| reddit | `mcp_servers/reddit_server` | Python | stdio | none |
| x | `x/` | Node | stdio | manual, visible browser |
| linkedin | `linkedin/` | Python (uv) | stdio | `--login --no-headless` |
| xiaohongshu | `xiaohongshu/` | Go | **HTTP** | QR code |

Xiaohongshu is the odd one out: it speaks HTTP on `:18060`, so it has to be running before
Claude Code can reach it. The other four are spawned on demand.

```bash
make xhs      # start it
```

`servers/x/` and `servers/linkedin/` are de-vendored forks of `@barresider/x-mcp` and
`stickerdaniel/linkedin-mcp-server`; `servers/xiaohongshu/` of `xpzouying/xiaohongshu-mcp`.
Full history for the first two lives at `Allenz5/x-mcp-server` and
`Allenz5/linkedin-mcp-server`. They are maintained here now — there is no upstream sync.

## A warning about the three social servers

All three impersonate a logged-in session, which every one of those platforms forbids. LinkedIn
enforces it hardest and specifically targets browser automation: read-only scraping is enough to
get an account restricted, and first-offence suspensions happen. Use a throwaway account, cap
daily volume rather than just per-minute rate, and do not run around the clock — a request
stream with no circadian rhythm is the easiest thing in the world to spot.
