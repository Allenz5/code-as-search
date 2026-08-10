# Code as Search

Code as Search is a long-horizon research agent for deep internet search and browsing.

It is built around the idea that serious research should not stop at a search results page or a single synthesized answer. Like Claude Code applies an agent loop to software engineering tasks, Code as Search applies an agent loop to internet research: search, browse, inspect, compare, summarize, revise direction, and keep going until the answer is grounded in the best available evidence.

## Why This Exists

Most chat-based research tools are optimized for a direct question-and-answer flow. They can be useful for fast summaries, but they often rely heavily on search engine snippets, cached knowledge, or a narrow set of sources.

Code as Search is designed for deeper work:

- It interacts with the internet directly, not just search results.
- It browses pages, follows leads, and inspects primary sources where possible.
- It keeps a long research loop running instead of returning the first plausible answer.
- It compares conflicting information across sources.
- It explores multiple directions instead of locking onto one interpretation too early.
- It discusses intermediate findings with the user and adjusts course as new evidence appears.

## Core Idea

The agent treats research as an iterative process:

1. Understand the user's research goal.
2. Break the goal into possible search directions.
3. Search and browse across the open internet.
4. Extract concrete evidence.
5. Share intermediate findings with the user when the research direction is uncertain or changing.
6. Self-adjust the research direction based on current findings, contradictions, missing evidence, and user feedback.
7. Summarize what is known, what is uncertain, and what should be checked next.
8. Continue the loop until the result is deep enough to be useful.

## Firecrawl

Code as Search relies on Firecrawl for internet-facing capabilities. Firecrawl is used for searching the web, translating webpages into agent-readable content, and interacting with webpages during the research process.

## Example Use Cases

- Market, company, and competitor research
- Policy, legal, or regulatory landscape research
- Technical ecosystem research
- Product and vendor comparisons
- Academic or literature-adjacent discovery
- Investigative timelines
- Due diligence before a major decision
- Any question where source quality, recency, and conflicting evidence matter
