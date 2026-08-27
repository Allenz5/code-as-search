# Writing a Connection Digest row

Read this at the write step.

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
