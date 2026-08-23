# claude-toolkit

A Claude Code plugin: a long-horizon research agent, plus the MCP servers it reads the world
through. Installed once, it loads in every project.

## Install

```bash
make setup
ln -s "$PWD" ~/.claude/skills/claude-toolkit
echo "FIRECRAWL_API_KEY=fc-..." > .env
```

`make setup` builds three dependency trees — a Python venv for the servers in
`servers/mcp_servers/`, npm packages for X, and a Go binary for Xiaohongshu. `make check`
shows what Claude Code can actually reach.

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

The three social servers split the same way, by tool rather than by profile: the main loop
searches, `social-explorer` reads. `search` returns one line per post — title, author and
engagement, URL — and `get_post` returns the body and the comment tree. Only the subagent is
given `get_post`.

### One shape across four sources

`search` means the same thing on all four servers, and answers in the same lines:

```
20 results for "CRM 推荐" · xiaohongshu

1. 终于找到了一个适合startup的CRM
   @Sunmin的美国创业笔记 · ♥50 💬22 ⭐35
   https://www.xiaohongshu.com/explore/6998e040...?xsec_token=ABFnmZk...
```

Every result is addressed by URL — a Xiaohongshu note folds its `xsec_token` into the query
string — so the director hands a URL to a subagent without caring which platform it came from.
Reddit's search truncates post bodies at 2,000 characters, because a search that returns whole
bodies is unbounded: the longest measured here was 19,426 characters, and one call cost 18k
tokens.

## Servers

| | `servers/` | runtime | transport | login |
|---|---|---|---|---|
| research / explorer | `mcp_servers/firecrawl_server` | Python | stdio | Firecrawl API key |
| reddit | `mcp_servers/reddit_server` | Python | stdio | none |
| x | `x/` | Node | stdio | manual, visible browser |
| xiaohongshu | `xiaohongshu/` | Go | **HTTP** | QR code |

Xiaohongshu is the odd one out: it speaks HTTP on `:18060`, so it has to be running before
Claude Code can reach it. The other three are spawned on demand.

```bash
make xhs        # start it
make xhs-login  # same, with a window, when a login needs watching
```

Log in by fetching the QR and scanning it; that works headless. Restart the server if a call
ever hangs — a process left up for a day gets into a state where the login page stops
rendering, and `FetchQrcodeImage` used to wait for it forever.

`servers/x/` is a de-vendored fork of `@barresider/x-mcp` and `servers/xiaohongshu/` of
`xpzouying/xiaohongshu-mcp`. Full history for the first lives at `Allenz5/x-mcp-server`.
They are maintained here now — there is no upstream sync.

## A warning about the social servers

X and Xiaohongshu both impersonate a logged-in session, which both platforms forbid. Use a
throwaway account, cap daily volume rather than just per-minute rate, and do not run around the
clock — a request stream with no circadian rhythm is the easiest thing in the world to spot.
`social-explorer` is capped at three in flight for the same reason, and because each one drives
its own browser.

Every tool that posts, messages or reacts is in `deny` in `.claude/settings.json`. A research
run reads.
