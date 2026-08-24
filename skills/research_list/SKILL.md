---
name: research_list
description: Show the most recent research runs — their ids, what each one was after, and how far each got. Use when the user says "/research_list", or asks which research runs exist, what has been researched before, or for the id of an earlier run.
---

# Research list

Call `research_list(10)` — or whatever count the user asked for — and show what it returns.

Each run comes back as its id, the date it started, credits spent, whether a report was
written, its objective, and how many questions and findings its memory holds. That is the
whole answer. Do not open the run directories to embellish it: reading ten reports to
summarise them is exactly the context cost this command exists to avoid.

The id is the part that matters — it is what `/research_resume <id> <feedback>` takes.
