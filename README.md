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

### Plan Agent

Works with the user to turn a broad research goal into a concrete search plan. The plan should define the target questions, likely sources, collection strategy, quality checks, and expected output format.

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

## Goals

- Build a practical long-horizon search harness.
- Make deep search reproducible by turning plans into scripts.
- Keep human feedback in the loop where source selection, scraping strategy, or output requirements are ambiguous.
- Support multiple model providers without coupling the system to one vendor.
- Preserve traceability across agent decisions, tool calls, generated code, and collected data.
