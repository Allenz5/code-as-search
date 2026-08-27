---
name: connection_digest
description: Search LinkedIn for Bay Area technical people building AI products who are worth reaching out to, verify them, and write the survivors to the Connection Digest database in Notion. Learns which searches work from the ratings on earlier rows. Use when the user says "/connection_digest", or on a scheduled run.
---

# Connection Digest

You are looking for people worth reaching out to. One list a day, each row with a reason
attached and the search that found them recorded.

The standard is `skills/connection_digest/profile.md` — four axes, all of which must hold.
Read it first, every run. Judge against it, not against your own sense of who is
impressive.

Unlike a feed, nothing hands you candidates. You generate them, which means **the searches
are the product**. A run that finds nobody because it asked the wrong questions looks
exactly like a day when there was nobody to find, and `queries.md` exists so those two
stop being indistinguishable.

An empty run is a real outcome. Writing four mediocre people to Notion because four feels
like the right number destroys the list — once it contains people you would not actually
contact, every row has to be re-judged by hand, and then it is just LinkedIn again.

## Safety comes before everything else here

This run is heavier on one account than anything else in this repo: reading a feed is a
couple of page loads, ten searches three pages deep plus twenty profiles is closer to
seventy-five. **Getting the account restricted costs more than any missed day of results.**

The server enforces most of this and you must not work around it:

- Tool calls are serialised and paced 6–12s apart. You will wait. That is correct.
- A rate limit puts the server in a cooldown that **refuses** calls, escalating one minute
  to thirty. **When you see that refusal, the run is over.** Write what you already have,
  report it as incomplete, and say which stage stopped. Do not retry, do not switch
  channels to keep going, do not wait it out — retrying into a restriction is how a
  warning becomes a ban.
- **90 minutes wall clock, hard.** Not because anybody is waiting, but because `/feed_digest`
  runs at 12:23 on the same account and this starts at 10:31. Overrunning means two jobs
  scraping one account at once. Stop at 90 minutes wherever you are and report it.

Never open a second LinkedIn session. Every profile read goes through the one server.

## Start

**First, `date -Iseconds`.** Hold on to it. `run-logger` needs the run's start time at the
end, and this run has a 90-minute budget it can only spend if it knows when it started.

**Then take the comments off your control page.** [`Digest Controls`](https://app.notion.com/p/3c9ba5489378819199f6c8174886964f) in Notion
mirrors the documents that govern this run, one child page each:

| document | page id |
|---|---|
| `skills/connection_digest/SKILL.md` | `3c9ba548-9378-81c5-9129-f1c4f82fcd7b` |
| `skills/connection_digest/profile.md` | `3c9ba548-9378-81ef-a7fe-d04a7717d091` |
| `skills/connection_digest/queries.md` | `3c9ba548-9378-81a1-bc80-c6dd87310618` |

Call `notion-get-comments(page_id, include_all_blocks=true)` on each. It returns unresolved
threads by default, which is what you want. Two things decide whether a thread is live:

- A thread whose newest comment is your own `✅ 已改：…` is consumed — skip it.
- A thread where the user has replied *under* that ✅ is live again, and what he says there
  outranks what you decided last time.

For each live thread, work by `/update_skill`: the comment is evidence about the instruction
that produced the behaviour, so find that instruction and rewrite it. **Do not paste his
words into the file.** That is the exact failure `/update_skill` exists to prevent, and
these documents have a 200-line ceiling that appending would spend on one example.

The "one comment changes nothing" rule below does not apply here. That rule is about
`Comment` on a digest row, which is evidence about a single person. A comment on the control
page is the user talking about the document itself, at the level the document is written —
act on it the first time.

**When the comment is a complaint with no wanted behaviour attached**, and you cannot infer
it from the document, do not guess. Reply `❓ <the question>` and leave the thread live.
Nobody is awake at 10:31 to answer, and a standard bent the wrong way costs more than a
run that carried one comment over to tomorrow.

Reply `✅ 已改：<which instruction changed, and what it said before>` on every thread you did
act on. Then re-read the files you edited — this run is judged by the updated standard.

`queries.md` is on the page too, and it is the one you should expect comments on: it holds
the live query list, so "retire this one", "don't try that word" and "raise it to three pages"
all land there. It stopped being a log on 2026-08-27 — the per-run production tables and the
cut record came out, because `Run Log` and `git log -p` already hold both — so **do not put
run history back into it.** A new observation either changes the pool or rewrites one
judgement in `定性笔记`, undated.

1. Read `skills/connection_digest/profile.md` and `skills/connection_digest/queries.md`.

2. **Fold in feedback.** Query `Connection Digest` for rows where `Rating` is set or
   `Comment` is non-empty, and `Learned` is unchecked. Check `Learned` on every row you consume.

   The three ratings do not do the same job, and mixing them is the main way this loop can
   go wrong:

   | | means | changes |
   |---|---|---|
   | 👍 值得 | I would connect | `profile.md` examples, and the query's score |
   | 😐 一般 | right kind of person, not enough weight | **only** the query's score |
   | 👎 不对 | should not have been here at all | `profile.md` examples, and the query's score |

   **😐 never becomes a `profile.md` example.** It does not say the profile is wrong; it
   says the bar is too low. Filing it as a negative example would teach the screen to drop
   a kind of person the user still wants.

   **Comments are evidence about one row, never a rule.** The user may write free text in
   `Comment` saying what was good or wrong about a specific item. Read those alongside the
   ratings — but four things govern what you do with them, and they exist because the
   obvious handling destroys the file:

   - **Never copy comment text into `profile.md`.** A comment is about one item; the file holds
     general standards. Pasting the words in is exactly how a criteria file becomes hundreds
     of accumulated demands that nobody can apply and nothing can be judged against.
   - **One comment changes nothing.** Read it, check `Learned`, move on. Only when two or
     more comments point at the same underlying cause does the file change at all. A single
     remark about a single item is an observation, not a pattern.
   - **When it does change, rewrite — never append.** `profile.md` has a ceiling of 200 lines.
     At the ceiling a new idea must displace an older one, which forces the distillation
     that keeps the file usable. The archive lives in Notion, where every comment stays
     attached to its row forever; the file is the distillation, not the log.
   - **Test any change against the 👍 rows before writing it.** Overcorrection is the real
     danger: one sharp comment about one item easily becomes a rule that swings the standard
     too far. If the rule you are about to write would have rejected someone the user
     already marked 👍, it is too strong. Weaken it, or leave it unwritten and wait for more
     evidence.


3. **Maintain the query pool.** Group the rated rows by `Source` and by `Channel`, compute
   hit rate = 👍 ÷ (👍 + 😐 + 👎), and apply the rules in `queries.md`. The one that needs
   judgement is the split between *tighten* and *retire*: a query returning mostly 😐 with
   almost no 👎 found the right population and set the bar too low — tighten its wording,
   do not kill it. Mostly 👎 means it found the wrong population; retire it.

   Then **add**. Three mechanical sources, in order of evidence:
   - Terms that appear in the headlines of 👍 people and **not** in any current query.
   - Companies of 👍 people → `search_companies` for the numeric URN → a
     `current_company=<urn>` query.
   - Vocabulary used by any post author who passed. This is worth doing even when the post
     channel produces nobody: its words can be useful when its people are not.

   Write the changes into `queries.md` with a one-line reason each. A pool that changed
   without a recorded reason cannot be reasoned about next week.

   **Types, not just queries.** For the post channel the unit that matters is the *type* of
   post, and a new type is worth more than a dozen new queries inside an old one. Do not try
   to generate types — that is the user's job, and both of the best ones in the pool (hiring
   posts) came from them. **Ask for a new type in every run report**
   instead; that request is the mechanism.

   A type retires differently from a query: only when all of its queries together have
   written zero rows across ten runs. Its budget then goes to a new type rather than being
   spread over the survivors.

4. **Cold start only.** If `profile.md` still carries the calibration section marked
   "尚未运行", run `search_people(network=["F"], geo_urn="90000084")` once against two or
   three broad terms, read a handful of those profiles, and write the recurring patterns
   into that section. Then never again — and delete the whole section once 👍 rows outnumber
   the calibration sample, per the rule written there.

## The funnel

Each level costs more than the last, and the expensive one is bounded by the account, not
by time.

**Pull.** Take proven queries and new ones in a 7 : 3 split. Only running what already
works means never discovering what you have not tried, and that loss is invisible from the
results.

| channel | call | notes |
|---|---|---|
| search_people | `search_people(kw, geo_urn="90000084", network=["S","O"], pages=3)` | ~28 people per query, location genuinely filtered |
| search_posts | `search_posts(kw, date_posted="past-week")` | 12–15 queries, drawn from several post *types* — see queries.md |
| company_employees | `get_company_employees(slug, keywords)` | slug via `search_companies` |
| company_posts | `get_company_posts(slug)` | authors who showed up |
| feed | `get_feed(num_posts=100)` | once |
| sidebar | `get_sidebar_profiles(username)` | seed must be an already-👍 person |

Four things that will otherwise cost you:

- **`pages=3`, not 5.** Pages four and five bring `Discover more great results` (blurred
  profiles with no name and no link) and `Related results` (LinkedIn loosening the match).
  Those are not this query's results, and counting them against it poisons the scoreboard
  the whole learning loop rests on.
- **Parse candidates out of the text, not out of `references`.** On second-degree results
  LinkedIn lists your *mutual connections*, and the reference extractor picks them up as
  people. One test returned 51 references for 47 candidates that way.
- **The post channel has no location facet — gate it with a name lookup, not a profile
  read.** LinkedIn content search filters by time, type and author's own words, never by
  place, so a post author's location is unknown until you check. Do not spend a profile read
  on that: `search_people(keywords="<their name>", geo_urn="90000084")` answers it in one
  cheap search, and hands back their headline and city as well. A name that returns nothing
  is not in the Bay Area; that gate alone would have saved two of the three profile reads
  the post channel cost on 2026-08-24. Two cautions — LinkedIn fuzzy-matches names ("Did you
  mean…"), so confirm the returned name and headline are actually your author, and unusual
  spellings or emoji in a display name can produce a false negative.
- **Post queries need more invention than people queries, and that is a requirement, not a
  preference.** People search is one stable population phrased different ways. Post search
  is different *kinds of post exposing different kinds of person*, and the kinds have to be
  thought up. A hiring post exposes the founder who wrote it whatever its content; a
  job-change post exposes someone who just joined a frontier lab; an open-source post
  exposes the person who shipped the repo. Draw each run's queries from several types in
  `queries.md`, never all from one. Broad common words scrolled to the bottom beat rare
  precise phrases read one screen deep — that was learned the expensive way.

**Drop what you have already delivered.** Query the database for existing profile URLs
first and skip them. Also dedupe across queries within the run — high overlap between
related queries is normal.

**Screen on the search-result line.** Headline, location, current and past role, and often
a follower count — all of it is already in the text, no page load, no cost. This layer has
to cut about 96% of what you pulled, because the next one is capped at twenty.

Reject here for one reason only: this person plainly fails one of the four axes on
evidence visible in the line. Do not reject because the claim looks inflated or the title
looks generic — that is what reading is for. Do reject on the demerit words listed in
`profile.md` when nothing else in the line offsets them.

**Read the survivors.** Dispatch `profile-screener`, up to three at a time. Three is safe
now and was not before: the server serialises and paces every call, so the request rate is
the same whether one agent asks or three — only the thinking runs in parallel.

**Twenty profiles is the ceiling for a run.** Pick the twenty best by the cheap screen; if
more than twenty look worth reading, that is a good problem and the rest can wait for
tomorrow. Say in the report how many you left unread.

**Verify.** The screener hands back what it could not settle. Chase only what the decision
turns on — usually whether the company is real and notable. `get_company_profile` and
`search_companies` are what you have; when they cannot settle it, the claim stays unsettled
and goes into `Verified` as such.

## Writing to Connection Digest

Database: `Connection Digest` under the `Work` page.
Data source: `collection://3c068caf-1e11-4ca0-9164-c3c744dac2b3`

One row per person who passed all four axes, and **every row gets all twelve columns**:
`Name`, `URL`, `Headline`, `Company`, `Role`, `Location`, `Channel`, `Source`, `Score`,
`Why`, `Verified`, `Captured`. A column the schema has and this file never names is one
that goes missing without erroring.

- **`Source` is the exact query text, verbatim.** Not a paraphrase, not a summary. It is
  the join key between the user's ratings and the searches, and the entire learning loop
  is downstream of it. When several queries surfaced the same person, record the first one
  and name the others in `Why`.
- **`Channel`** is the select that lets channel-level rules run without parsing `Source`.
- **`Why`** names what they actually built and which axis carries them. "Works on AI at a
  startup" is not a reason.
- **`Verified`** gets the specific facts — headcount, founding year, followers, funding.
- **`URL`** is addressed as `userDefined:URL`, because `URL` is reserved.
- **`Score` runs 0-100** and should use its range. When a third of the list lands on one
  number the score has stopped carrying information.
- `Rating` is the user's and `Learned` is yours — **never set `Rating` yourself.**

## Ending the run

Report, in this order:

**The funnel per channel**: pulled → already delivered → screened out → read → written.
One row per channel, including channels that produced nothing — a channel that returned a
full page and contributed nobody is a claim about that channel, and it only becomes
checkable if the zero is written down.

**The query scoreboard**: for each query run today, how many it produced, and its standing
hit rate from earlier ratings. Then what you changed in `queries.md` and why — promoted,
tightened, retired, revived, added.

**A request for a new post type**, every time. Say which types produced today and which
produced nothing, then ask. The reverse-lookup above is the only generator the skill has and
it is a weak one — the two best types in the pool were handed over by the user, so asking is
the mechanism, not a courtesy.

**What you left undone**: profiles beyond the twenty, queries not reached inside 90
minutes, anything cut off by a cooldown. This is the difference between "there was nobody"
and "I ran out of budget", and only one of those is a fact about LinkedIn.

**Bugs, not bad days.** A tool that returned someone else's data, a scrape that came back
empty, a rate limit — count those separately and name them. They are yours to fix, not the
platform's bad day.

**Refresh the mirror.** If this run changed one of the documents on `Digest Controls` — from
a comment, or from the ratings loop — republish that child page from the file with
`notion-update-page` / `replace_content`. Only the files that actually changed: the page is a
mirror, and nothing else ever writes to it, so a page you skip stays stale until some later
run touches its file. Do this before dispatching `run-logger`, and say in `NOTABLE` which
documents you republished and why.

**Then log the run.** The report above goes to `~/.local/state/connection-digest/`, which nobody reads
and next week's run cannot. Dispatch `run-logger` once, at the very end, and it becomes a
row in `Run Log` — which is what lets the retire rules be computed from history instead of
remembered. `queries.md` already says the standing record should be recalculated rather than
stored twice; this is the same argument one level up, for the channels.

Dispatch it even when a cooldown ended the run early — especially then. A run that stopped
at the first refusal and wrote no row is indistinguishable from a day with nobody to find.

```
DIGEST:   Connection Digest
STARTED:  the timestamp from the top of this run
FINISHED: `date -Iseconds`, now
STATUS:   完成 | 部分（读取预算 20 个用尽，还有人没读）| 中断（cooldown 拒绝调用、90 分钟到、被 kill）| 失败
FUNNEL:   one line per channel — search_people, search_posts, company_employees,
          company_posts, feed, sidebar — as
          `<name>  pulled → new → shortlisted → read → written`. All six every run. A channel
          you never ran this round is `<name>  —  (why)`: no 👍 seed for sidebar, no company
          slug worth an employee search. That is a different claim from zero, and the
          difference decides whether a channel deserves retiring.
BUGS:     one line each, `[channel] what broke → what it cost`. `none` when nothing did.
NOTABLE:  what you changed in `queries.md` and why — promoted, tightened, retired, revived,
          added — which post types produced and which produced nothing, and your request for
          a new post type. Keep the request in your own words; it is the only generator this
          skill has.
UNREAD:   profiles beyond the twenty, queries never reached, anything a cooldown cut off.
          Omit only when STATUS is 完成.
```

Every one of the five numbers is **how many were left**, never how many were cut: `new` is
what survived the already-delivered check, `shortlisted` is what survived the cheap screen.
The report above phrases those two as removals; the row wants the survivors, because only
survivors chain into the next level.

`run-logger` hands back the row URL and any defect it had to record on your behalf. Put
those in your report too: a hand-off that broke quietly is worse than one that broke loudly.
