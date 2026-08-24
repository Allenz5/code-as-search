# claude-toolkit

A long-horizon research agent and a social-feed triage agent, plus the MCP servers they read
the world through. Installed once, they load in every project.

## Install

```bash
make setup
echo "FIRECRAWL_API_KEY=fc-..." > .env
make install
```

`make setup` builds four dependency trees — a Python venv for the servers in
`servers/mcp_servers/`, a separate uv-managed venv for LinkedIn, npm packages for X, and a Go
binary for Xiaohongshu.

`make install` symlinks the agents and skills into `~/.claude/` and registers the director
MCP servers at user scope, so everything works from any directory. Nothing is copied: the repo
stays the source of truth and git stays in charge. `make uninstall` reverses it; `make check`
shows what Claude Code can actually reach.

The one thing `make install` generates rather than links is the agent files. A user-level agent
may declare its own MCP servers — that is the entire reason this is not a plugin — but neither
`${HOME}` nor `~` expands in agent frontmatter, so the command has to be an absolute path. The
agents are therefore checked in as `agents/*.md.in` templates and rendered into `build/`
(gitignored) at install time. Re-run `make install` after moving the repo.

## The research agent

```
/research <what you want to find out>
/research_list                          the last 10 runs, and how far each got
/research_resume <run id> <feedback>    carry one on, keeping what it already knows
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
interruption and restarts — which is what makes `/research_resume` possible. It reopens a run
in place: resolved questions are not researched again, the feedback becomes the new questions,
and the previous `report.md` is kept as `report-1.md` rather than overwritten.

### Why raw content cannot reach the main loop

Every server runs as two profiles over one codebase. The director finds things; the explorer
reads them.

| server | director has | explorer has |
|---|---|---|
| websearch | `research_*` `search` `memory_*` | `scrape` `interact` `interact_stop` |
| reddit | feeds, `search`, subreddit info | `get_post` `get_post_comments` |
| x | timeline, `search`, profiles, trending | `get_post` |
| xiaohongshu | `list_feeds` `search`, profiles | `get_post` |

The line is bounded vs unbounded. A director tool answers in one line per item — title, author,
engagement, URL, and an excerpt capped at 2,000 characters. An explorer tool returns a whole
body and a whole comment tree, which has no ceiling at all.

**Only the director profiles are registered globally.** The explorer profiles are declared
inside the frontmatter of the agents that need them and exist nowhere else, so the main loop
has no tool to read a page or a post body with. This is a capability boundary, not a rule in a
prompt — the director cannot leak raw content into its own context because it cannot fetch any.

### Why this is not a plugin

It was one, and being one is what broke the boundary. Plugin-shipped agents ignore the
`mcpServers` frontmatter field ("for security reasons", per the plugins reference) — reasonably,
since `command:` is an arbitrary executable and a plugin could otherwise smuggle in servers that
never appear in its manifest. But that field is the only mechanism that gives a subagent a
server the main conversation lacks, so as a plugin the explorer profiles had to be registered
globally, and the boundary degraded into an instruction. Permissions cannot patch it either:
`deny` is inherited by subagents, so denying the main loop denies the explorer with it (tested,
not assumed).

The trade is real and it goes the other way too — as a plugin this installs with one symlink,
carries a version, and answers to `claude plugin validate`. Here it costs a script, absolute
paths in generated files, and a re-run of `make install` whenever the repo moves. That price
buys a boundary the harness enforces instead of one the prompt requests.

One consequence to know about: `.claude/settings.json` is project-scoped, so the `deny` list
that blocks posting, liking and messaging only applies inside this repo. Running `/digest` from
elsewhere leaves those write tools reachable — copy the deny list into `~/.claude/settings.json`
to have it everywhere.

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
tokens. The recommendation feeds go through the same renderers for the same reason — before
they did, one `list_feeds` call returned 56,831 characters of JSON.

## The digest agent

`/digest` replaces four scroll sessions with one list. It pulls the recommendation feed from
each platform, screens it down, and writes what survives to a Notion database with a reason
attached to every row.

Screening is a funnel, because each level costs more than the last:

```
feeds  →  metadata (cheap, no browser)
       →  post-screener reads body + comments
       →  verify what the survivors claim
       →  Notion
```

The comments carry the second level. A post is its author's best case for itself; the replies
are where that case survives or falls apart, and they are the only reliable way to tell a
write-up from an ad for its writer. LinkedIn is the exception — there is no tool to read a
single LinkedIn post, so its posts are judged on body text alone, without that signal.

The third level is why LinkedIn is worth having at all: it is a résumé database, so
`get_person_profile` answers "does this person's background support what they are claiming?"
better than any general search.

`skills/digest/interests.md` is the standard, and it updates itself — rate a row in Notion and
the next run folds that into the file. `git log -p skills/digest/interests.md` is a record of
how the taste drifted.

An empty run is a real outcome. Once the list contains filler it has to be skimmed, and then
it is just another feed.

## Servers

| | `servers/` | runtime | transport | login |
|---|---|---|---|---|
| websearch / explorer | `mcp_servers/websearch_server` | Python | stdio | Firecrawl API key |
| research | `mcp_servers/research_server` | Python | stdio | none |
| reddit | `mcp_servers/reddit_server` | Python | stdio | none |
| x | `x/` | Node | stdio | manual, visible browser |
| linkedin | `linkedin/` | Python (uv) | stdio | `--login --no-headless` |
| xiaohongshu | `xiaohongshu/` | Go | **HTTP** | QR code |

Xiaohongshu is the odd one out: it speaks HTTP on `:18060`, so it has to be running before
Claude Code can reach it. The other four are spawned on demand.

```bash
make xhs        # start it
make xhs-login  # same, with a window, when a login needs watching
```

Log in by fetching the QR and scanning it; that works headless. Restart the server if a call
ever hangs — a process left up for a day gets into a state where the login page stops
rendering, and `FetchQrcodeImage` used to wait for it forever.

`servers/x/` and `servers/linkedin/` are de-vendored forks of `@barresider/x-mcp` and
`stickerdaniel/linkedin-mcp-server`; `servers/xiaohongshu/` of `xpzouying/xiaohongshu-mcp`.
Full history for the first two lives at `Allenz5/x-mcp-server` and
`Allenz5/linkedin-mcp-server`. They are maintained here now — there is no upstream sync.

## A warning about the three social servers

All three impersonate a logged-in session, which every one of those platforms forbids. LinkedIn
enforces it hardest and specifically targets browser automation: read-only scraping is enough to
get an account restricted, and first-offence suspensions happen. Use a throwaway account, cap
daily volume rather than just per-minute rate, and do not run around the clock — a request
stream with no circadian rhythm is the easiest thing in the world to spot. Subagents that drive
a browser are capped at three in flight for the same reason, and because each one drives its
own browser.

Every tool that posts, messages or reacts is in `deny` in `.claude/settings.json`. A research
run reads.
