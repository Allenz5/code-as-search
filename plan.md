# Code as Search — Agent Framework Plan

## 1. Architecture

Build a Python system using the OpenAI Agents SDK’s manager pattern. The Research Controller remains user-facing and calls specialists through bounded function tools that internally run specialist agents. Do not use handoffs, because specialists must return control to the controller. This follows the SDK’s documented [manager orchestration pattern](https://openai.github.io/openai-agents-python/multi_agent/).

```text
Research Runtime
├── Research Controller
│   ├── research_web
│   │   └── Search Strategist
│   │       └── Firecrawl Search
│   ├── inspect_page
│   │   ├── Page Analyst
│   │   │   └── Firecrawl Scrape
│   │   └── Memory Curator
│   ├── interact_with_page
│   │   ├── Page Analyst
│   │   │   └── Firecrawl Interact
│   │   └── Memory Curator
│   ├── read_working_memory
│   └── request_user_guidance
├── Working Memory Service
├── Context Builder
└── Run Policy and Budget Controller
```

Use the strongest configured OpenAI reasoning model for all four agents, with the highest reasoning effort supported by that model. Pin the model in application configuration so runs remain reproducible.

## 2. Agent Designs

### Research Controller

The main agent has exactly three responsibilities:

- Read the current research state.
- Choose one next action.
- Determine when research is complete.

It receives only compact working-memory views and structured tool results. It never receives raw webpage content or direct Firecrawl access.

Available actions:

- Call `research_web` for an open question.
- Call `inspect_page` for a selected result or link.
- Call `interact_with_page` when a page requires navigation or dynamic interaction.
- Call `read_working_memory` when it needs a different memory view.
- Call `request_user_guidance` for a decision-critical ambiguity.
- Produce the final research report.

Every research action must reference at least one `open_question_id`. This keeps searches and browsing focused.

### Search Strategist

Responsible for:

- Converting one or more open questions into search queries.
- Refining queries based on previous searches and known evidence.
- Running Firecrawl Search.
- Ranking results for inspection.
- Explaining which open question each result may answer.

It receives:

- Research objective and constraints.
- Target open questions.
- Relevant findings and conflicts.
- Previous queries and visited URLs.

It returns a structured `SearchBatch`; it does not update memory directly.

### Page Analyst

Responsible for:

- Scraping or interacting with one page.
- Evaluating the page against the supplied inspection purpose.
- Extracting claims, supporting evidence, conflicts, useful links, and unanswered questions.
- Returning a structured `PageAnalysisResult`.

It receives:

- URL or active Firecrawl page handle.
- Research objective.
- Inspection purpose.
- Questions to answer.
- Selected prior findings and conflicts.
- Requested interaction, when applicable.

It does not receive the complete working memory. Its raw-content context is isolated to its nested run and destroyed after structured output is produced.

### Memory Curator

Responsible for:

- Comparing new analysis with existing memory.
- Deduplicating or merging findings.
- Classifying findings by importance and status.
- Detecting contradictions.
- Updating open questions and research progress.
- Producing a validated `MemoryPatch`.

It has no web tools and cannot independently create evidence. It may only transform supplied findings and existing memory.

## 3. Tools and Interfaces

### Controller Tools

#### `research_web(task: SearchTask) -> SearchBatch`

- Runs the Search Strategist.
- Uses Firecrawl Search without page-content scraping.
- Saves query history and result metadata deterministically.
- Returns ranked candidates and suggested next pages.

#### `inspect_page(task: PageInspectionTask) -> InspectionReceipt`

- Builds a focused context package.
- Runs the Page Analyst with Firecrawl Scrape.
- Passes the resulting analysis to the Memory Curator.
- Validates and commits the returned memory patch.
- Deletes raw page content and the nested analyst session.
- Returns only a compact receipt describing memory changes and suggested actions.

#### `interact_with_page(task: PageInteractionTask) -> InspectionReceipt`

- Continues from a stored Firecrawl scrape/session handle.
- Supports bounded actions: click, type, scroll, wait, follow link, and extract.
- Analyzes the resulting page state and commits it through the same curation pipeline.
- Stores interaction summaries, never page contents.

#### `read_working_memory(query: MemoryQuery) -> MemoryView`

Supports focused views:

- Current research status.
- Open questions.
- Findings for selected questions.
- Conflicts and rejected claims.
- Search history and inspected sources.
- Remaining budget.

#### `request_user_guidance(decision: UserDecisionRequest)`

Pauses and serializes the SDK run when:

- The research objective is materially ambiguous.
- High-impact evidence remains irreconcilable.
- Continuing requires expanding the agreed scope.

Resume the same run state after receiving the answer.

### Internal Firecrawl Tools

- `firecrawl_search`: Firecrawl v2 Search, returning only result metadata by default.
- `firecrawl_scrape`: Firecrawl v2 Scrape, returning main-content Markdown, links, metadata, and a page handle.
- `firecrawl_interact`: Firecrawl Interact, operating on the current page handle.

Firecrawl supports separate search, scrape, and interactive page operations, which matches this lifecycle. [Search](https://docs.firecrawl.dev/api-reference/endpoint/search), [Scrape](https://docs.firecrawl.dev/api-reference/endpoint/scrape), [Interact](https://docs.firecrawl.dev/features/interact).

### Core Structured Types

```text
SearchTask
├── open_question_ids
├── purpose
├── query_constraints
└── desired_source_types

SearchBatch
├── search_id
├── queries
├── ranked_candidates
├── coverage_notes
└── recommended_candidate_ids

PageInspectionTask
├── source_id
├── open_question_ids
├── inspection_purpose
└── relevant_finding_ids

PageAnalysisResult
├── page_summary
├── proposed_findings
├── evidence
├── conflicts
├── newly_identified_questions
├── useful_links
├── relevance
└── recommended_next_actions

MemoryPatch
├── findings_to_add
├── findings_to_update
├── questions_to_add
├── questions_to_update
├── conflicts_to_record
├── sources_to_update
└── progress_update
```

All agent outputs use Pydantic structured-output models. The SDK supports typed agent outputs and structured inputs for nested agent tools. [Agents and output types](https://openai.github.io/openai-agents-python/agents/), [agent tools](https://openai.github.io/openai-agents-python/tools/).

## 4. Working Memory

Use a per-research-run SQLite store behind a `WorkingMemoryService`. Archive the structured run record when research ends. Do not use the Agents SDK session as the research knowledge base; SDK sessions hold conversation history, while working memory holds curated research state.

```text
WorkingMemory
├── Run
│   ├── objective
│   ├── constraints
│   ├── status
│   └── budgets
├── OpenQuestions
├── Findings
├── Evidence
├── Conflicts
├── Sources
├── Searches
├── NavigationState
└── Progress
```

### Open Questions

Each question contains:

- Stable ID and text.
- Priority: `critical`, `high`, `normal`, or `low`.
- Status: `open`, `partial`, `resolved`, or `blocked`.
- Reason the question matters.
- Parent question, when decomposed.
- Supporting and conflicting finding IDs.
- Resolution summary or blocking reason.

Search and page tasks must connect to open questions. New questions discovered by specialists are added only through the Memory Curator.

### Findings

Each finding contains:

- Atomic claim.
- Importance: `important`, `supporting`, or `background`.
- Status: `supported`, `conflicting`, `rejected`, or `superseded`.
- Relevance and confidence assessments.
- Addressed open-question IDs.
- Evidence and source references.
- Creation and update timestamps.

Do not store completely unrelated content. Store only the inspected URL and a short rejection reason when necessary to prevent repeated work.

### Evidence and Sources

Retain:

- Minimal claim-supporting excerpt or precise paraphrase.
- Source URL, title, publisher, date, and access time.
- Page location or section when available.
- Source-quality assessment.
- Relationship to a finding.

Do not retain full Markdown, HTML, screenshots, or raw interaction output.

### Context Builder

Before every specialist run, build a bounded context package containing:

- The research objective and constraints.
- The target open questions.
- Findings directly related to those questions.
- Relevant conflicts.
- Previous attempts and visited URLs.
- The specialist’s exact task.

Agents logically share working memory through these views, but they never receive the entire database automatically.

### Memory Write Rules

- Agents never write directly to SQLite.
- The Memory Curator proposes a `MemoryPatch`.
- Application code validates IDs, source references, state transitions, and duplicate claims.
- Application code commits the patch atomically.
- Failed validation leaves memory unchanged and retries curation once.

## 5. Loop, Safety, and Completion

### Execution Loop

```text
Initialize objective and open questions
        ↓
Controller reads memory view
        ↓
Controller chooses one action
        ↓
Specialist performs bounded work
        ↓
Memory Curator proposes update
        ↓
Application validates and commits
        ↓
Controller receives compact receipt
        ↓
Repeat or finish
```

### Raw-Content Boundary

- Raw content exists only inside the Page Analyst’s nested run.
- Do not attach a persistent SDK session to Page Analyst runs.
- Disable sensitive payload capture for Page Analyst traces.
- Never log Firecrawl page bodies.
- Configure Firecrawl not to cache page bodies when supported; enable its zero-retention option when available to the account.
- Release raw response objects immediately after structured analysis succeeds or fails.

### Failure Handling

- Retry transient Firecrawl and model failures with bounded exponential backoff.
- Mark inaccessible sources without resolving their open questions.
- Deduplicate canonical URLs before inspection.
- Record material contradictions instead of overwriting earlier findings.
- Stop repeated search paths using query and URL history.
- Preserve partial memory when budgets or external services fail.

### Completion

The controller may finish when:

- Every critical and high-priority question is resolved or explicitly blocked.
- Important findings have source-backed evidence.
- Material conflicts are resolved or disclosed.
- Additional searching is unlikely to change the conclusion meaningfully.

It must finish when a configured time, tool-call, token, page, or Firecrawl-credit limit is reached. The final output must include conclusions, evidence, conflicts, unresolved questions, and limitations.

## 6. Test Plan

- Verify the controller can only access controller-level tools and never Firecrawl directly.
- Verify every search and inspection references an open question.
- Verify Search Strategist returns ranked metadata without page bodies.
- Verify Page Analyst receives focused context and returns valid structured output.
- Verify raw Markdown and HTML are absent from memory, logs, traces, and controller history.
- Verify the Memory Curator deduplicates findings and records contradictions without overwriting evidence.
- Verify open questions transition correctly through open, partial, resolved, and blocked states.
- Verify failed memory patches are atomic and leave the previous state intact.
- Verify dynamic pages can be inspected through scrape followed by interact.
- Verify duplicate URLs and repeated queries are suppressed.
- Verify decision-critical cases pause and resume the same SDK run.
- Verify budget exhaustion produces a partial report with unresolved questions.
- Run an end-to-end research scenario containing multiple searches, static pages, a dynamic page, conflicting sources, and at least one unresolved question.

## Assumptions

- The implementation is greenfield; the repository currently contains only its README.
- Python and the `openai-agents` SDK are used.
- Working memory persists for one research run and is archived afterward.
- The system runs autonomously except for decision-critical user checkpoints.
- Specialist agents are invoked through nested runner-backed function tools, not handoffs.
- Full raw webpage content is never persisted by the application.
