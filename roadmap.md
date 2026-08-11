# Roadmap

_2026-08-11_

## TODO

1. Add temperature to control search variation intensity
2. Add more scrape tools for sub agent (YouTube video transcript, Reddit post reader, X MCP, etc.)

## Done

- Add parallel sub-agent — the director dispatches up to 3 page-explorers per message; shared
  run state is locked across processes
- Pin `model: sonnet` in `.claude/agents/page-explorer.md`
- Deny built-in `WebFetch` in `.claude/settings.json`
