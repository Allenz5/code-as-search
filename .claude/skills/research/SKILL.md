---
name: research
description: Run a long-horizon web research investigation on a topic or question. Searches, reads pages through the page-explorer subagent, keeps a question-driven working memory on disk, and writes a report when its open questions are answered. Use when the user says "/research" or asks for deep research on a subject.
---

# Research

You are running an investigation, not a search. The job is finished when every question in
working memory is answered — not when you have gathered enough to say something plausible.

Your context window is not the research state. `memory.jsonl` is. Write everything that
matters into memory as you go, and this session can be compacted, interrupted or resumed
without losing anything.

## Start

1. `research_start(objective)` with the user's objective. Note the run id it returns.
2. Decompose the objective into 2–5 questions that would actually settle it, and
   `memory_append` them. Order matters: the list is the priority order, most decisive first.

Good questions are specific enough to be answered by a page and wrong-able. "What is Acme's
revenue?" is a question. "Tell me about Acme" is not.

## Loop

Repeat until the stop condition below holds:

1. `memory_read()` — this is your ground truth, not your memory of the conversation.
2. Take the top open question.
3. `search(...)` for it. Read the titles and snippets and pick the single most promising URL.
   Prefer primary sources: filings, papers, docs, official pages. Prefer specific over general.
4. Delegate that URL to the **page-explorer** subagent. Give it: the URL, the exact question,
   and a one-line summary of what is already known so it does not hand back what you have.
   Delegate one page at a time so each choice is informed by the last.
5. `memory_append` what came back:
   - each real claim as a `finding` against its question, with the source URL
   - any new question the page raised, if it matters to the objective
   - a `note` for a contradiction between sources, or a dead end worth not repeating
   - the question as `resolved` with an `answer`, once you actually believe it
6. Re-read `memory_read()` every few actions.

## Judgment

- **Do not resolve a question on a single source** unless that source is authoritative for
  the fact — a filing for a funding round, a spec for a spec question. When you do, name the
  source in the `answer`.
- **Follow contradictions.** Two sources disagreeing is the most valuable thing you can find.
  Write a `note`, then open a question to settle it.
- **Follow surprises.** A finding that does not fit is a lead, not noise.
- **Prune.** If a question turns out not to matter to the objective, resolve it with an
  answer saying so. Do not leave it open to be re-searched.
- **Vary your queries.** If a search returns the same pages you have already read, the query
  is wrong, not the web. Change the wording, narrow the domain, add `tbs` for recency.
- **Never invent an id.** `memory_append` assigns them and returns them.

## Stop

Stop when nothing is left under **Open**, and the last two pages you read produced no new
findings and no new questions. Then write `report.md`.

Also stop when the budget runs out — the tools will tell you. Then write the report anyway,
and say plainly which questions are still open.

## Report

Write `report.md` into the run directory:

- **Answer** — the objective, answered directly, in a few sentences.
- **What we found** — the resolved questions and their answers, each with source links.
- **Conflicts** — where sources disagreed and which you believed, and why.
- **Still open** — questions you could not settle, and what it would take to settle them.

Cite with links. Never state a conclusion that no finding in memory supports.
