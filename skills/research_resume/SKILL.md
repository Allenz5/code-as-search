---
name: research_resume
description: Continue an earlier research run with new feedback, keeping everything it already established. Use when the user says "/research_resume", or wants to push further on a research run that was already reported.
---

# Research resume

Continuing a run is the same investigation as `/research`, begun from a memory that is already
full rather than empty. The feedback is what makes it a continuation and not a rerun.

## Start

1. **Identify the run.** The arguments are `<run id> <feedback>`. If no id was given, or the id
   does not exist, call `research_list()` and ask which one. Never guess a run from its
   objective — two runs on one subject are common, and resuming the wrong one is silent.
2. `research_resume(run_id, feedback)`. It makes that run active again and returns its whole
   memory: resolved questions with their answers, findings, notes. Read it before doing
   anything else. Never call `research_start` here — that opens an empty run, and everything
   the earlier one established becomes unreachable.
3. **Turn the feedback into questions**, then `memory_append` them. This is the actual work of
   a resume:
   - What the feedback asks for is rarely already a question. Write the new ones as you would
     at the start of a run: specific enough to be answered by a page, and wrong-able.
   - What is already resolved is not to be researched again. Reopen a resolved question —
     append it with `status: "open"` — only where the feedback gives you reason to doubt its
     answer, and append a `note` saying what that reason was.
   - If the feedback asks only for *more of the same*, the new question is a widening of the
     old one rather than a copy: name what the earlier pass did not reach.

## Then

Run the investigation exactly as `/research` does. Read `~/.claude/skills/research/SKILL.md`
and follow it from `## Loop` onward. The loop, the judgment rules and the stop condition are
the same for a resumed run, and they are deliberately not repeated here.

## Report

`research_resume` has already moved the run's previous `report.md` aside as `report-<n>.md`.
The report you write replaces it, so write the whole investigation — everything the run knows
now, the earlier findings included — not just this round of it. The reader should never have
to open both.
