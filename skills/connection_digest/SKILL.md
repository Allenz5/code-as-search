---
name: connection_digest
description: Search LinkedIn for Bay Area technical people building AI products who are worth reaching out to, and write the survivors to the Connection Digest database in Notion. Learns which searches work from the ratings on earlier rows. Use when the user says "/connection_digest", or on a scheduled run.
---

# Connection Digest

You are looking for people worth reaching out to. One list a day, each row with a reason
attached and the search that found them recorded.

The standard is `skills/connection_digest/profile.md` — four axes, all of which must hold —
not your own sense of who is impressive.

Nothing hands you candidates here, so **the searches are the product**. A run that finds
nobody because it asked the wrong questions looks exactly like a day with nobody to find;
`queries.md` exists so those two stop being indistinguishable.

An empty run is a real outcome. Four mediocre people because four feels like the right number
destroys the list: once it holds people you would not actually contact, every row has to be
re-judged by hand, and then it is just LinkedIn again.

Three steps: `criteria-keeper`, the funnel, `run-logger`.

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

**First, `date -Iseconds`.** `run-logger` needs the run's start time, and this run has a
90-minute budget it can only spend if it knows when it started.

**Then dispatch `criteria-keeper` with `DIGEST: Connection Digest`, and wait.** It is the
only thing that edits the documents this run is judged by — the control-page comments, the
rated rows, the query pool, the mirrors — and it holds the page ↔ file list and the pool
rules itself, so there is nothing else to send it.

Then **read `skills/connection_digest/profile.md` and `queries.md`**. This run is judged by
what they say now. The `NOTABLE` lines handed back go to `run-logger` verbatim.

## The funnel

Each level costs more than the last, and the expensive one is bounded by the account, not
by time.

### Pull

Proven queries and new ones in a 7 : 3 split. Only running what already works means never
discovering what you have not tried, and that loss is invisible from the results.

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

### Drop what you have already delivered

Query the database for existing profile URLs and skip them. Dedupe across queries within the
run too — high overlap between related queries is normal.

### Screen on the search-result line

Headline, location, current and past role, often a follower count — already in the text, no
page load, no cost. This layer has to cut about 96% of what you pulled, because the next one
is capped at twenty.

Reject for one reason: this person plainly fails one of the four axes on evidence visible in
the line. Not because the claim looks inflated or the title looks generic — that is what
reading is for. Do reject on the demerit words in `profile.md` when nothing else offsets them.

### Read the survivors

Dispatch `profile-screener`, up to three at a time, giving each `profile.md` in full and the
person's search-result line. Three is safe: the server serialises and paces every call, so the
request rate is the same whether one agent asks or three — only the thinking runs in parallel.

**Twenty profiles is the ceiling for a run.** Pick the twenty best by the cheap screen; more
than twenty worth reading is a good problem and the rest wait for tomorrow. Say in the report
how many you left unread.

### Write

Data source: `collection://3c068caf-1e11-4ca0-9164-c3c744dac2b3`, `Connection Digest` under
`Work`. One row per person who passed all four axes, and **read
`skills/connection_digest/reference/notion-columns.md` before writing the first one** — it
holds the twelve columns and what each has to contain.

Two things there fail silently: a column this file never names goes missing without erroring,
and the URL column is addressed as `userDefined:URL` because `URL` is reserved. `Verified` is
the screener's own VERIFIED line — nothing downstream re-checks it now.

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

**Log the run.** The report above goes to `~/.local/state/connection-digest/`, which nobody
reads and next week's run cannot. Dispatch `run-logger` once, at the very end — even when a
cooldown ended the run early, especially then: a run that stopped at the first refusal and
wrote no row is indistinguishable from a day with nobody to find. Its row is what lets the
retire rules be computed from history instead of remembered.

`agents/run-logger.md` defines the report it expects; send exactly that, with
`DIGEST: Connection Digest` and one `FUNNEL` line for each of `search_people`, `search_posts`,
`company_employees`, `company_posts`, `feed`, `sidebar` — all six every run, a channel that
never ran written as `—  (why)` rather than as zero. `NOTABLE` takes what this run changed and
what it wants, five lines at most, including `criteria-keeper`'s lines verbatim.
