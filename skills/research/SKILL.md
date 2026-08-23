---
name: research
description: Run a long-horizon web research investigation on a topic or question. Searches, reads pages through the page-explorer subagent and papers through the pdf-reader subagent, keeps a question-driven working memory on disk, and writes a report when its open questions are answered. Use when the user says "/research" or asks for deep research on a subject.
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

Explorers do not block you. You dispatch one and keep working; its report arrives later, on
its own. So never end a turn having only waited — waiting is what you do when there is
nothing else left, not the shape of the loop.

Every turn: `memory_read()` first, then do as much of 1–3 as there is work for, then 4.

1. **Drain.** For each report that has landed, `memory_append` what it gave you:
   - each real claim as a `finding` against its question, with the source URL
   - any new question the page raised, if it matters to the objective
   - a `note` for a contradiction between sources, or a dead end worth not repeating
   - the question as `resolved` with an `answer`, once you actually believe it

   Judge each report as it lands rather than holding it for its siblings. The one thing you
   cannot judge alone is corroboration — see Judgment.

2. **Dispatch.** There is no cap on explorers in flight. Every page that is worth reading
   right now goes out right now, in this turn. Give each explorer: the URL, the exact
   question it is answering, and a one-line summary of what is already known so it does not
   hand back what you have.

   Worth reading means: you would read it whatever the in-flight explorers come back with —
   another source for a question you are trying to corroborate, or the top URL for a
   different open question. This is the only thing that governs how many go out. Hold a page
   back only when it is genuinely downstream: an index page you expect to yield the URL you
   actually want, or a question whose wording changes once the one above it is answered.
   That test does not get stricter as the number in flight grows.

   Route by document, not by habit: `claude-toolkit:page-explorer` for web pages,
   `claude-toolkit:pdf-reader` for papers
   and anything else that has a PDF, `claude-toolkit:social-explorer` for a Reddit, X or
   Xiaohongshu post. A long document overflows the scraper and comes back
   as an error with no content at all, so send `pdf-reader` the `/pdf/` URL rather than
   sending an explorer the `/html/` one.

   Social explorers are the one exception to "no cap": send at most 3 at a time. Each one
   drives a browser — X rate-limits a single account across concurrent sessions, and
   Xiaohongshu launches a Chromium per request.

3. **Search ahead.** Before you stop for the turn, search the next open question and
   pick its URLs, so the next turn opens with somewhere to send explorers instead of having
   to go find out. Prefer primary sources: filings, papers, docs, official pages. Prefer
   specific over general.

   Four search tools answer four different questions, and they all return the same shape —
   title, author and engagement, URL, excerpt — so pick by what you are asking, not by
   habit:

   | | reaches |
   |---|---|
   | `search` | the open web: filings, docs, papers, news |
   | `reddit:search` | what practitioners argue about, in threads |
   | `x:search` | what is being said this week |
   | `xiaohongshu:search` | Chinese-language consumer and purchase experience |

   A social platform answers "what do people report" — never "what is true". Reach for one
   when the question is about experience, reception or practice, and for the open web when
   it is about fact. Hand every URL they return to `social-explorer`; the post body and its
   comments are not yours to read.

4. **Wait** — only now, and only if nothing landed, nothing is dispatchable, and explorers
   are still out.

`memory_read()` is your ground truth, not your memory of the conversation. After a
compaction it is all you have.

## Judgment

- **Do not resolve a question on a single source** unless that source is authoritative for
  the fact — a filing for a funding round, a spec for a spec question. When you do, name the
  source in the `answer`.
- **Follow contradictions.** Two sources disagreeing is the most valuable thing you can find.
  Write a `note`, then open a question to settle it.
- **Two explorers agreeing is not two sources** when both pages trace to the same origin — the
  same press release, quoted twice. Look at the URLs before you count a report as
  corroborating one you already drained.
- **Follow surprises.** A finding that does not fit is a lead, not noise.
- **Prune.** If a question turns out not to matter to the objective, resolve it with an
  answer saying so. Do not leave it open to be re-searched.
- **Vary your queries.** If a search returns the same pages you have already read, the query
  is wrong, not the web. Change the wording, narrow the domain, add `tbs` for recency.
- **Never invent an id.** `memory_append` assigns them and returns them.

## Stop

Stop when nothing is left under **Open**, nothing is in flight, and the last three reports you
drained produced no new findings and no new questions. Then write `report.md`.

There is no credit ceiling. Nothing will stop the run for you, so the stop condition above is
the only thing that ends it — hold yourself to it. `memory_read()` reports credits spent; that
is for the record, not a limit to steer by.

## Report

Write `report.md` into the run directory:

- **Answer** — the objective, answered directly, in a few sentences.
- **What we found** — the resolved questions and their answers, each with source links.
- **Conflicts** — where sources disagreed and which you believed, and why.
- **Still open** — questions you could not settle, and what it would take to settle them.

Cite with links. Never state a conclusion that no finding in memory supports.
