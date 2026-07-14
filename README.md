# code-as-search

Currently, this README serves as a design doc. Follow the implementation instructions first and update this design doc accordingly, since the design doc may not always be correct.

`code-as-search` is a harness for using LLM agents to run deep search as a long-horizon workflow. Instead of relying on a single chat session to browse, reason, and remember everything, it uses a lead-agent / subagent model inspired by Claude Code: a main agent coordinates the work, delegates to specialist agents, and turns repeatable search tasks into executable code.

The project is built on [`openai-agents`](https://github.com/openai/openai-agents-python) as the main agent framework, with the goal of supporting multiple model providers over time, including Codex subscription, Claude, OpenAI, Gemini, and open-source models.

## Why

Deep search often needs more than one LLM call. Good results usually require planning, scraping, data cleaning, iteration, source checking, structured storage, and sometimes custom scripts. `code-as-search` treats that process as an agentic software workflow:

- plan the search with the user
- delegate specialized work to subagents
- generate scripts for repeatable collection and analysis
- run code in a sandbox
- persist intermediate data
- trace long-running behavior for monitoring and debugging

## Core Capabilities

- **Agent specialization**: define agents with different tools, instructions, models, and responsibilities.
- **Handoffs**: let a main agent delegate focused tasks to specialist agents.
- **Tracing**: use built-in tracing to inspect long-running agent behavior and debug failures.
- **Script execution**: create sandboxes for running scrapers, data processors, and analysis scripts.
- **Persistent storage**: store collected data, extracted facts, intermediate artifacts, and run metadata in a database.
- **Provider flexibility**: support multiple LLM providers and model backends as the system evolves.

## Current Design

The initial design uses four primary agent roles:

### Main Agent

The lead agent. It owns the user-facing workflow, keeps track of the overall objective, coordinates handoffs, and decides when to ask the user for clarification.

In the first implementation, the main agent is the session owner and router. It supervises the active planning run, keeps user messages flowing through the main runtime, and forwards the user's next reply back to the planning agent when the planner is waiting on a blocking clarification.

### Plan Agent

Works with the user to turn a broad research goal into a concrete search plan. The plan should define the target questions, likely sources, collection strategy, quality checks, and expected output format.

The planning agent is interactive rather than one-shot. It should inspect the user's research goal, identify ambiguous constraints, run small Firecrawl-backed `test_search` probes to learn the terminology and source landscape, use `inspect_page` to translate candidate pages into markdown when needed, present readable interim findings for discussion, call `ask_user` when clarification is required, and continue refining until it can call `finalize_plan`.

### Coding Agent

Converts the search plan into executable scripts where possible. This keeps long-running research from depending entirely on fragile LLM browsing sessions and makes data collection more repeatable.

### Scraper Agent

Helps design and refine scrapers with the user. It focuses on source structure, extraction strategy, pagination, rate limits, data fields, and validation.

## Architecture Sketch

```text
User
  |
  v
Main Agent
  |
  +-- handoff --> Plan Agent
  |
  +-- handoff --> Coding Agent
  |
  +-- handoff --> Scraper Agent
  |
  +-- tools ----> sandboxed runtime
  |
  +-- tools ----> database
  |
  +-- tracing --> run inspection / monitoring
```

## Status

This repository is in the early design and implementation phase. The README describes the intended direction first so the implementation can stay aligned around a clear architecture.

Implemented so far:

- Python package skeleton under `src/code_as_search`
- LLM provider configuration for OpenAI, Claude, and Gemini
- Main agent definition using `openai-agents`
- Deep Search Planning Agent definition with Firecrawl-backed `test_search`, `inspect_page`, `ask_user`, `present_interim_findings`, and `finalize_plan` tools
- Runtime state wrapper for routing user replies back to an active planner clarification
- `.env.example` plus local `.env` variable layout

Search and page translation currently use Firecrawl as the single retrieval backend. `FIRECRAWL_API_KEY` is required for Firecrawl Cloud, and the default endpoint is `https://api.firecrawl.dev`.

## Goals

- Build a practical long-horizon search harness.
- Make deep search reproducible by turning plans into scripts.
- Keep human feedback in the loop where source selection, scraping strategy, or output requirements are ambiguous.
- Support multiple model providers without coupling the system to one vendor.
- Preserve traceability across agent decisions, tool calls, generated code, and collected data.
