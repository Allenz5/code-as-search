# Roadmap

_2026-08-11_

## TODO

1. Add temperature to control search variation intensity
2. Add a YouTube transcript reader for the subagent

## Done

- Vendor reddit, x, linkedin and xiaohongshu MCP servers into `servers/` and register them
  in the plugin — the subagent can now read those platforms directly
- Add parallel sub-agent — the director dispatches up to 3 page-explorers per message; shared
  run state is locked across processes
- Pin `model: sonnet` in `agents/page-explorer.md`
- Deny built-in `WebFetch` in `.claude/settings.json`
