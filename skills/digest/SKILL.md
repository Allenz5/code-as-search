---
name: digest
description: Pull the recommendation feeds from X, Reddit, Xiaohongshu and LinkedIn, screen them down to what is actually worth reading, verify what the survivors claim, and write the result to the Feed Digest database in Notion. Use when the user says "/digest", or on a scheduled run.
---

# Digest

You are replacing four scroll sessions with one list. The user does not want to open X,
Reddit, Xiaohongshu and LinkedIn today; they want the handful of things from those feeds
that are worth their attention, with a reason attached to each.

The standard is not "is this interesting" — it is `skills/digest/interests.md`, which is
this person's own account of what they care about. Read it first, every run. Judge against
it, not against your own taste.

An empty run is a real outcome. Some days the feeds have nothing. Writing three mediocre
things to Notion because three feels like the right number is the one failure mode that
destroys the list's value — once it contains filler, it has to be skimmed, and then it is
just another feed.

## Start

1. Read `skills/digest/interests.md`.
2. Fold in feedback: query the Notion database for rows where `Rating` is set and
   `Learned` is unchecked. Each one is the user telling you that you got it right or
   wrong. Append them to the examples section of `interests.md`, rewrite the prose when
   the misses share a cause rather than being one-offs, and check `Learned` on the rows
   you consumed. Real feedback should displace the seed examples over time.

Do this before pulling feeds — this run should be judged by the updated standard.

## The funnel

Each level costs more than the last, so the expensive ones go last. How much survives each
level is yours to judge: if the feeds are rich today, more survives.

**Pull the feeds.** All four, and note that Reddit is not like the others — the server
uses an anonymous client, so there is no personalised front page. Use the subreddit list in
`interests.md`.

| | tool |
|---|---|
| x | `scrape_timeline(type="following", ...)` |
| xiaohongshu | `list_feeds()` |
| linkedin | `get_feed(...)` |
| reddit | `get_subreddit_hot_posts(subreddit, ...)` per subreddit |

**Drop what you have already delivered.** Query the database for recent URLs first and
skip anything already there. This runs three times a day against feeds that turn over
slowly; without this the same post arrives every morning.

**Screen on metadata.** Title, author, engagement, excerpt. This is cheap — no browser —
so it should be generous. You are only ruling out what is plainly off-topic; anything that
might be good goes to the next level. A title is weak evidence about a post's substance,
which is exactly why the next level exists.

**Read the survivors.** Dispatch `post-screener`, at most three at a time — each one
drives a browser, X rate-limits concurrent sessions on one account, and Xiaohongshu
launches a Chromium per request. Give each one the URL and what this person cares about.
It reads the body and the comments and comes back with a judgement plus whatever it could
not check for itself.

LinkedIn is the exception: there is no tool to read a single LinkedIn post, so its posts
never go to `post-screener`. Judge them from the body text `get_feed` returns, and know
that you are working without the comments — which is the strongest signal for spotting a
post that only exists to promote its author. Be correspondingly stricter with LinkedIn.

**Verify.** The screener hands back claims it could not check. Chase the ones the post
stands or falls on — not every number in it. What to check and how far to go is a judgement
about that specific post; there is no fixed procedure.

| | |
|---|---|
| who someone is, where they worked, what they studied | `linkedin:get_person_profile` |
| whether a company is real, how big, how old | `linkedin:get_company_profile`, `search_companies` |
| funding, news, third-party coverage | `search` |

These are all you get. When they cannot settle a claim, the claim stays unsettled — say so
in `Verified` and let the score carry it. Do not go looking for another way in.

LinkedIn is a résumé database, which makes it better than a general search for checking
who someone actually is. The user's standard: **does this person's background support what
they are claiming?** Someone announcing a platform shift should have the track record to
know; someone who does not is making noise. When it does not hold up, drop the post and
say so in `Why` — the user wants to see what you rejected them on.

## Writing to Notion

Database: `Feed Digest` under the `Work` page.
Data source: `collection://7ad5f30e-fdd5-4fc9-ae87-cbc551d03705`

One row per surviving post. `Why` is the column that earns the list its trust: name the
thing in `interests.md` it hits and what in the post makes it worth opening. "Relevant to
AI agents" is not a reason. `Verified` gets what you actually established — a specific
fact, not "could not verify" as a placeholder.

**`Score` runs 0-100.** The width is the point: it exists so that things which differ can be
scored differently. When a third of the list lands on the same number the score has stopped
carrying information, and the list loses the ordering that makes it scannable.

**`URL` is always the post itself** — the thing you actually found, on the platform you
found it on, so the row stays checkable against its source. Often the thing worth reading
is somewhere else: a paper, a repo, a company page. Put those links in `Why` and say what
each one is. A row whose real payload is an arXiv link should say so in `Why` rather than
quietly swapping the URL, because the post and the paper are different claims — the post
is what the feed served you, and whether it represented the paper honestly is exactly what
the reader needs to be able to check.

Two mechanical notes: the URL column is addressed as `userDefined:URL`, not `URL`, because
`URL` is reserved. `Rating` and `Learned` are the user's and yours respectively — never
set `Rating` yourself.

## Ending the run

Report to the user: how many posts each feed returned, roughly what you dropped and why,
what made it through, and anything that went unread because a platform was cooling down —
that last one matters, because it is the difference between "nothing good today" and "I
couldn't look".

If a platform failed outright — not logged in, server down — say which and keep going with
the rest. Three feeds and an honest note beats no run at all.
