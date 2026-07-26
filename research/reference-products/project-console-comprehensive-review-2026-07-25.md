---
title: "ARRP Project Console — Comprehensive Review and Assessment"
status: non-authoritative-reference
version: "1.0"
as_of: "2026-07-25"
implementation_baseline: "e45a0e711aa82ca147cdc827cbf18c8b348e4cdd"
print_status: excluded
print_exclusion_reason: "Nonauthoritative internal product review."
---

# ARRP Project Console

## Comprehensive Review and Assessment

**Version 1.0 — July 25, 2026**

**NON-AUTHORITATIVE REFERENCE PRODUCT**

## Status and authority

This report assesses the Project Console as a project-management, research-development, automation-oversight, and publication-planning interface. It does not alter project authority, admit or dispose of a candidate, change a Proposal Quality Score, change a GitHub Project field, approve publication, resolve an automation alert, or authorize an agent or bot.

The [Framework](../../framework/FRAMEWORK.md), [Agent Operating Rules](../../framework/AGENT_OPERATING_RULES.md), [Project Interface](../../framework/PROJECT_INTERFACE.md), [Project Console Progress](../../framework/PROJECT_CONSOLE_PROGRESS.md), [GitHub Workflow](../../framework/GITHUB_WORKFLOW.md), and registered agent and bot runbooks remain controlling. The Console remains a read-only projection except for the explicitly bounded localhost coordinator requests and locally staged publication plans described by those authorities.

The review baseline is Git revision `e45a0e711aa82ca147cdc827cbf18c8b348e4cdd`, after the merge of pull request #421. Live GitHub state and repository data-branch feeds were checked on July 25, 2026. Counts in this report are point-in-time evidence, not durable targets.

### Root-cause implementation scope

Implementation should not be artificially limited to the Console's presentation layer. If Console development reveals and verifies an underlying project structural defect, correcting the owning project structure is within scope. The implementation should repair the authoritative source and regenerate the Console rather than add a display-layer exception that conceals the defect.

Structural defects include, for example:

- an entity classified as an issue when it is actually a product, source, task, or publication record;
- missing or duplicated stable identity;
- conflicting schemas, field vocabularies, lifecycle rules, or eligibility rules;
- broken canonical routing or cross-surface linkage;
- duplicated or missing authority;
- a generated feed or builder contract that cannot represent the canonical state completely; and
- incompatible repository, GitHub Project, automation, monitoring, or publication structures.

This scope does not authorize an implementation agent to decide policy merits, change a Proposal Quality Score or `Runs` for convenience, dispose of a candidate, approve publication, or make another human-reserved judgment. A verified structural repair must follow the governing context route, Change Audit and synchronization requirements, affected GitHub/project-field readback, and ordinary validation. An uncertain or judgment-dependent finding should be documented and routed rather than silently “fixed.”

### Elim discovery, action, and documentation

Implementation should reconcile the governing Elim and automation records so every prescribed work list is expressly a required floor, not an exhaustive whitelist. During an authorized run, Elim may notice and investigate a credible project-related anomaly, omission, contradiction, emerging risk, or connected question without a prior detector, queue entry, or human prompt. It may expand beyond its initial context packet when the evidence warrants it.

Discovery and investigation authority do not create change authority. After investigating an unprompted finding, Elim should:

1. create a distinct, traceable discovered work unit and repair the problem when the repair is objectively supported, inside delegated authority, and not prohibited;
2. preserve and report the exact finding when implementation is human-reserved, outside delegated scope, unsafe, or explicitly forbidden—without attempting a workaround; or
3. retain an unresolved obligation with the evidence, uncertainty, owner, and next investigation trigger when the result is inconclusive.

Every path requires thorough documentation. The canonical owning record and linked provenance should identify the discovery context and exact source revision; evidence and reasoning; affected records and likely consequence; authority analysis; action taken or reason no action was taken; changed surfaces; validation and readback; disposition; accountable owner; and next action or trigger. Shared logs and Console views should link that canonical detail rather than copy divergent narratives across the project.

When an otherwise authorized Elim run has little or no ordinary queued work, it should enter **project-governance review and discovery mode** rather than close merely because the predefined queue is quiet. This mode should inspect project structure, governing-rule integration, authority boundaries, workflow coherence, source and monitoring coverage, automation, publication, contributor-readiness, accumulated technical debt, and cross-surface consistency. It remains subject to the usage reserve, exact-source context, logging, validation, and human-reserved boundaries. Because the current governing automation design closes an empty LLM queue as a deterministic no-op, implementation requires a recorded automation-architecture Change Audit and synchronized updates to the Run Coordinator, Elim runbook, runtime configuration, context routing, queue schema, Console projections, and tests.

## Executive assessment

The Console should be retained and improved, not rebuilt.

Its nine-screen architecture is logical. It has become a substantial, coherent specialist workspace with unusually strong provenance, reversible publication planning, exact-head pull-request recommendations, rich candidate dossiers, complete logs, and a clear separation between canonical records and derived views. The approved compact Overview design remains the right visual and conceptual foundation.

The Console is strongest as:

- a complete inventory;
- a specialist inspection surface;
- a provenance and automation directory;
- a publication-assembly workbench; and
- a read-only route into canonical evidence.

It is not yet reliable enough to serve as the sole project-manager cockpit. Its main weakness is not missing data in the abstract; it is **signal governance**. Current condition, prior failure, active incident, retained history, portfolio inventory, and manager priority sometimes appear with similar visual weight. Several important counts are technically derived but managerially misleading.

Reducing the manager's cognitive load must not suppress the underlying gaps. With more than 100 developed issues and potential outside contributors, an unowned structural, coverage, monitoring, source, publication, or operational gap can persist indefinitely and become materially harder to repair. The durable operating model should therefore use deterministic checks as a minimum detection floor, retain each confirmed obligation in the Run Coordinator's queue, and make Elim responsible during its conditional runs for investigating, repairing within delegated authority, or routing it. The queue, named detectors, context routes, and enumerated runbook duties must not become a ceiling on discovery or unprompted investigation. Persistent oversight belongs in project records and queue state; it does not imply that Elim is a continuously running scheduler. The project owner should see only the subset requiring human judgment, posing material risk, or failing to progress.

The most important conclusions are:

1. **The Console omits the non-proposal delivery and release critical path.** The authenticated GitHub Project contained 110 items: 98 proposal/candidate records represented on the Progress board and 12 non-proposal delivery items that were not. Those twelve span governance, technical/publication, source/reference hardening, and topic-product work. The omitted set includes the Critical `Pre-publication final audit` and `Pre-publication technical` parents. Twenty-six Project items were marked `Release blocker = Yes`.
2. **Progress does not explain why the number of tracked proposals changed.** On July 13, ARRP counted 204 active proposals, 23 of them Review Ready. The approved appointments-area (`APPT`) consolidation reduced that count to 198; the approved July 16 [portfolio consolidation review](../portfolio-issue-consolidation-review.md) then merged overlapping manifestations, safeguards, and remedy components into 77 broader coherent proposals; four later proposal admissions brought the current portfolio to 81. The current result is 27 Review Ready of 81. Thus `-123` means 123 fewer separately counted proposal records than at baseline—not 123 completed proposals, failures, or deletions. The UI shows only the current total and “On track” without this history, making earned development and portfolio redesign difficult to distinguish.
3. **Watcher update badges understate exact pending changes.** The Court screen shows `+1` while the exact-head recommendation for PR #380 identifies 42 source rows plus the associated formal candidate. The Directives screen shows `+1` while the recommendation for PR #381 identifies 10 directives. A single proposal is being presented as a single changed record.
4. **Automation retries inflate the human inbox.** Twelve unresolved retry records represent recurring states in two broad failure families, not twelve independent managerial decisions.
5. **The Integrity total mixes different systems.** The latest Project Integrity Bot run is clean, while the Integrity tab reports 107 current problems: 98 source-health exceptions, seven candidate-dossier gaps, and two operational observations. That composite can be useful, but it needs source-specific naming, freshness, and delta.
6. **Useful prioritization fields exist but are not used.** Priority, Release blocker, Status, Development level, Score, Last audit, Next audit, Change audit needed, Rebaseline status, Runs, milestone, and workstream are available in the Project or generated feeds. The Console largely presents an identifier-sorted inventory instead of a transparent next-work view.
7. **The client is substantially over-rendered.** The initial payload is approximately 12.9 MB across 41 synchronous scripts. A rendered session contained about 70,814 elements, 4,387 table rows, 1,477 buttons, 854 selects, and 5,242 options, including the contents of hidden tabs.
8. **Gap oversight is not yet presented as a closed control loop.** The project has many detectors and specialist records, but the Console does not prove that every confirmed gap has a stable identity, accountable owner, next check or action, aging protection, resolution evidence, and complete documentation. That control becomes essential as the issue portfolio and contributor base grow.
9. **The current empty-queue no-op can suppress discovery.** Elim's present governing records say it is not launched merely to discover work when the compiled queue is empty. That is inconsistent with the requested stewardship model. A quiet ordinary queue should instead produce a documented governance-review and open-discovery work unit so missing detectors, latent structural problems, and cross-project risks can still be found.

The recommended end state does not require a tenth primary tab. It requires the existing screens to answer their intended questions more directly:

- **Overview:** What changed in the project's administrative, technical, and operational systems, what matters now, and where should I look next? Overview is generally an operations briefing and routing surface, not an issue-development workspace.
- **Progress:** What is the issue-development portfolio and release trajectory, and what issue-development work should happen next?
- **Action Items:** What exact decision or recovery action is assigned to me, what work assigned to others warrants my oversight, and which specialist screen owns each item? Action Items is a non-authoritative index into those screens.
- **Candidates and Sources:** What needs development, why, and with what evidence or assurance gap?
- **Integrity:** What is defective, in which system, since when, and who owns the next step?
- **Agents & Bots:** What is the current chain condition, what was the latest worker result, and what is the recoverable history?
- **Logs:** What is the complete authoritative history?
- **Publication:** Which internal products are ready to become published products, is the assembly structurally valid, and is the project actually ready for release?

## Review method

The review combined:

- complete reading of the governing Console, GitHub, lifecycle, monitoring, audit, agent, and publication modules;
- static review of `index.html`, `app.js`, `styles.css`, generated data, builders, workflows, and current tests;
- rendered review of every primary screen and sub-screen;
- desktop review at 1280 × 720 and responsive review at 390 × 844;
- interaction checks for search, sort, filters, disclosures, hash routes, staging, reset, and live-feed hydration;
- browser-console error review;
- authenticated GitHub reconciliation of open pull requests, Actions runs, and all 110 Project items;
- comparison of checked-in snapshots with `project-console-data` feeds; and
- three independent read-only reviews focused on frontend/accessibility, data lineage, and project-manager coverage.

No external record was changed. Publication staging was tested locally and reset. The localhost coordinator was not running, so consequential coordinator controls were inspected but not invoked.

## What should be preserved

The following design decisions are valuable and should survive implementation:

1. The nine primary screens and their conceptual boundaries.
2. The compact operations-briefing visual language on Overview.
3. The rule that unavailable data is shown as unavailable, never guessed as zero.
4. Action Items as the single non-authoritative attention-routing and oversight index, with the project owner's assignments primary and other owners' assignments secondary.
5. Exact-head recommendation matching and automatic invalidation when a pull-request head changes.
6. Full candidate dossiers and neutral presentation of evidence, uncertainty, counterarguments, and pending questions.
7. Complete specialist logs rather than a lossy synthesized ledger.
8. Read-only canonical data, bounded localhost requests, and reversible local publication staging.
9. Explicit links to controlling runbooks, workflows, reports, GitHub records, and source material.
10. Full agent and bot identity separation, including Elim as the LLM agent and `-bot` names only for deterministic programs.

## Point-in-time operating picture

### GitHub Project

Authenticated Project state contained:

| Measure | Current value |
| --- | ---: |
| Total Project items | 110 |
| Proposal and candidate portfolio items | 98 |
| Governance and operations items | 12 |
| Release blockers | 26 |
| Critical priority | 4 |
| High priority | 59 |
| Medium priority | 31 |
| Parked | 2 |
| Priority unassigned | 14 |
| Development | 64 |
| Research | 8 |
| Audit needed | 4 |
| External review | 25 |
| Blocked | 3 |
| Deferred | 5 |
| Human decision needed | 1 |

The twelve non-proposal delivery items omitted from the portfolio board were:

- Pre-publication final audit;
- Pre-publication technical;
- Source and external-reference hardening;
- Neutrality and bipartisan adoption review;
- Horizon proposal resolution for public release;
- Release-blocker audit posture review;
- Final link and export validation;
- Publication assembly workflow;
- Copyright infringement check;
- executive-summary audit work;
- Jack Smith reports crosswalks, an internal topic-product development stage rather than an issue; and
- the final sourcing-boundary verification for indictments and prosecutorial reports.

These records should not be mixed into the 81-proposal Review Ready goal count or the issue-development worklist, but they must be visible in a separate product/release-delivery view.

Project crosswalks and topic pages should be treated as two stages of one topic product:

1. **Project crosswalk — internal stage.** The project synthesizes and maps relevant issues, sources, institutions, and boundaries for internal development and review.
2. **Topic page — published-product stage.** After publication review, the same product becomes the public-facing topic treatment.

One stable product identity should connect the two stages. Neither stage is itself an ARRP issue, proposal, candidate, or evidence record; neither receives an issue-development level, Proposal Quality Score, `Runs`, or a place in the Review Ready goal count. A GitHub task may track production work, but that task does not convert the crosswalk or topic page into a substantive issue.

### Portfolio and publication

| Measure | Current Console value | Assessment |
| --- | ---: | --- |
| Review Ready | 27 of 81 | Current workload is useful; needs the documented consolidation history that explains why the portfolio moved from 204 records to 81 |
| Remaining | 54 | Correct for the current 81-proposal architecture |
| Rolling pace | 6 per week | Needs separate explanation of earned readiness and changes to the number of tracked proposals |
| Forecast | September 26, 2026 | Must be labeled “current scope” |
| Formal candidates | 17 | Complete count; Project-field freshness is mixed |
| Preliminary candidates | 1 | Rich dossier; triage and term handling need correction |
| Cited sources | 2,055 | Comprehensive inventory |
| Source Checker results | 2,048 | Seven current sources are outside the last scan |
| Publication-controlled pages | 344 | Complete disposition inventory |
| Included in print | 138 | Structurally classified |
| Explicitly excluded | 206 | Structurally classified |
| Unclassified/conflicting | 0 / 0 | Strong publication-metadata result |
| Public edition | 137 records, ~494 estimated pages | Existing 490-page PDF is stale |
| Public-edition cross-references outside edition | 119 | Material review queue, not a structural blocker |
| Long-page/layout threshold findings | 9 | Current table does not guarantee the complete flagged union |

### Current automation and repository state

- Five pull requests were open: #394, #381, #380, #378, and #361.
- Two exact-head recommendations were assigned to the human owner; three proposals remained Elim-owned.
- The current cloud run chain completed successfully at baseline revision `e45a0e7`.
- The latest recorded Elim invocation had failed before substantive work.
- Twelve retained host automation alerts remained unresolved in the local projection.
- The Review Epoch was due because a governing boundary had changed.

These facts can all be true at once. The Console needs clearer temporal and state labels so they do not read as contradictions.

## Screen-by-screen assessment

### 1. Overview

**Verdict: retain; strong design, incomplete decision briefing.**

Strengths:

- Compact daily-brief structure is effective.
- Operational portals distinguish counts from unavailable state.
- Every registered agent and bot is represented.
- Freshness, service health, private usage, and operational queues are brought together.
- Direct links route to specialist screens.

Defects and gaps:

- “7 latest results succeeded” appeared while the visible latest Elim result was Failed. The intended statement was about current-chain stages, not the latest result of every registered worker.
- Current chain, latest worker execution, and unresolved historical alert are not labeled as separate time dimensions.
- Integrity timestamps containing an ISO offset such as `+00:00` are parsed by a regular expression that accepts `+0000` but not `+00:00`. Recent Integrity activity can therefore appear four hours in the future in the Eastern time zone.
- Recent activity intentionally excludes human-authored actions and is dominated by repeated clean Integrity runs.
- Operational queue links for Development, Research, Audits, and External review all open unfiltered Progress.
- `Logs 220` is a lifetime mixed-log total, not a decision signal.
- `System currency` is unexplained technical shorthand and groups three different questions: whether project data reflects the latest authoritative state, whether connected services are available, and whether Codex usage reserve is sufficient.
- Overview applies a hard-coded 48-hour front-end default to the Console bundle, GitHub Project, Progress, Integrity, and Run Chain freshness cards. That value is not part of the Review Epoch design and has no documented authority as a Console-update rule. At the review baseline it labeled the GitHub Project timestamp `Current` at nearly 22 hours old solely because it was under 48 hours, despite a newer Progress feed. Passing a generic clock-age test does not prove that a projection represents the latest authoritative revision.
- The “Elim-eligible work: 156” portal exposes a large count but not the queue composition, ranking, age, blockers, or why only one coordinator-selectable work unit appears.

Recommended treatment:

- Keep the current visual design.
- Rename `System currency` to `Project data and services`. Within it, use plain sublabels: `Data status` for whether Console data reflects the latest authoritative project state, `Service status` for connected-service availability, and `Codex capacity` for the protected usage reserve. Do not use `currency` as a manager-facing label.
- Keep Review Epoch status as a separate governance signal—last completed, next due, and overdue—not as a Console feed-freshness clock.
- Give each data domain an owning currentness rule based on availability, completeness, last successful synchronization, source revision or generation, and whether a newer authoritative state supersedes it. Use a maximum age only when the owning process expressly defines one.
- Replace worker-result prose with explicit labels: `Current chain`, `Latest completed run`, `Unresolved incidents`, and `Next due`.
- Add a small “Manager focus” block containing:
  - critical release work;
  - human decisions;
  - active incidents;
  - material changes since the last review; and
  - data domains that are stale, incomplete, or unavailable.
- Collapse consecutive clean/no-op runs into one summary on Overview while preserving every run in Logs.
- Replace the Logs badge with `new since last visit` or no badge.

### 2. Progress

**Verdict: largest project-management gap.**

Strengths:

- Six-stage maturity board is understandable.
- Review Ready target, pace, forecast, holds, area coverage, and monitoring inventory are useful.
- Holds preserve reasons rather than inferring them.
- Proposal and candidate counts reconcile to the 98-record portfolio.

Defects and gaps:

- The screen does not explain the documented sequence: `204 baseline proposals → 198 after appointments-area (APPT) consolidation → 77 after the broader July 16 consolidation → 81 after four later admissions`.
- The shorthand `-123` does not tell the manager that overlapping proposal records were merged into broader coherent issues; it can be mistaken for completed work, deleted work, or a data error.
- “On track” is not explicitly limited to the current 81-proposal scope.
- The current ready count increased from 23 to 27, while most of the percentage change came from the approved portfolio redesign. Those two forms of movement are not presented separately.
- Twelve non-proposal delivery items and the release critical path are absent. Their exclusion from the proposal board is correct; the missing defect is a separate delivery surface.
- Twenty-six release blockers are not available as a cohort.
- Identifier sorting replaces decision-relevant ordering.
- The board omits or underuses Priority, Release blocker, Last audit, Next audit, Score, Runs, Change audit needed, Rebaseline status, age, milestone, workstream, and dependencies.
- A recorded score of `0` is rendered as `Score —` because the display condition treats a missing score and every numeric value at or below zero alike. ARRP uses `0` as a meaningful fixed-zero / Not Scored state, so the Console currently erases the distinction between “the recorded value is zero” and “no valid score is available.” Negative or otherwise out-of-range values would also disappear behind the same dash instead of surfacing as data defects.
- Generated `movement`, `backlog`, and distribution data are not surfaced.
- Workflow queue links cannot open a filtered worklist.

Recommended treatment:

- Preserve the six-stage board as the portfolio inventory.
- Add a subordinate **Portfolio next work** workbench using authoritative fields and an inspectable rationale.
- Keep Progress limited to issue development. Route non-proposal delivery, including the crosswalk-to-topic-page product lifecycle, to Publication rather than adding it to the issue-development board.
- Show a plain-language `Portfolio architecture history`: `204 baseline → 198 after APPT consolidation → 77 after the July 16 portfolio consolidation → 81 after four later admissions`.
- Show `Review Ready: 23 → 27` separately from changes in the number of independently counted proposals.
- Link the consolidation steps to the adopted portfolio-consolidation record and label the current 81 as the present issue architecture, not earned completion.
- Retain reason-coded additions, mergers, retirements, reroutes, and eligibility changes for future movement; never show a bare signed number without an explanation.
- Show “On track for current scope” only when reconciliation is complete.
- Add filter-aware hash routes for workflow Status, Development level, Priority, Release blocker, area, and owner.

### 3. Action Items

**Verdict: correct routing role; counts, oversight coverage, and item briefs need repair.**

Strengths:

- The screen correctly aims to centralize attention routing without replacing the specialist screens that own the underlying state.
- Exact-head recommendations prevent stale pull-request decisions.
- Integrity, automation, workflow decisions, repository reviews, preliminary candidates, and source routing are separated.
- Elim-owned pull requests do not increase the top human total.

Defects and gaps:

- The total was 16, but visible card headline counts summed to 19 because the Repository card showed all five pull requests while only two counted as human actions.
- Twelve retry events were presented as twelve independent human actions.
- Retry links expose cryptic `automation-failure-<hash>` identifiers and a generic Administration route, with no first occurrence, latest occurrence, recurrence count, root cause, or current proof of recovery.
- The human-decision item shows an identifier and title but not the exact reserved question.
- Preliminary intake can link to a supporting source instead of the owning Console dossier.
- Human-owned and Elim-owned repository proposals share one card.
- Some internal Console routes are created with an external-link helper and can open a new tab.

Recommended treatment:

- Make `Assigned to you` the primary view and make its count equal the number assigned to the project owner.
- Add a clearly secondary `Other assigned work to oversee` view covering Elim, bots, automation, and any other owner. Preserve the real owner and status, but do not add those items to the project owner's action total.
- Keep Action Items strictly non-authoritative. It may summarize and route, but it must not independently own status, priority, evidence, resolution, or disposition.
- Route every item first to the specialist Console screen that owns its domain—such as Progress, Candidates, Sources, Integrity, Agents & Bots, or Publication. That specialist screen may then link to the canonical repository or GitHub record.
- Convert retry events into incidents keyed by root cause and prerequisite, retaining complete occurrence history.
- Every human item should show:
  - exact question;
  - current recommendation or options;
  - why it is assigned now;
  - consequence of delay;
  - age or due trigger;
  - owner; and
  - the owning specialist-screen route, where evidence and authoritative state remain available.
- Separate `Assigned to you` from `Other assigned work to oversee`.

### 4. Candidates — formal

**Verdict: strong dossiers; weak triage and mixed freshness.**

Strengths:

- All 17 formal candidates are present.
- Dossiers preserve issue-admission reasoning, overlap, sources, Project links, and current disposition.
- Development level, workflow Status, area, and Priority are available.

Defects and gaps:

- Lifecycle queues and the candidate board use `active_horizon_records`, while the live Progress feed already contains candidate Project fields. Live Progress refresh does not update the board.
- The board can therefore combine a fresh Progress feed with a roughly day-old candidate snapshot.
- Filters omit Priority, last review, next audit/reassessment trigger, monitoring, and dossier gaps.
- Default order does not identify the candidates most ready for work or human review.
- Disclosure-preference identities for court-watcher groupings can collide when one owner appears in multiple monitoring groups.

Recommended treatment:

- Use `progress.candidates` for authoritative Project fields and merge only dossier-specific material by stable candidate ID.
- Add priority, age, next trigger, monitoring, and gap facets.
- Provide transparent sorting such as `human decision`, `high priority`, `trigger reached`, `dossier gap`, and `oldest review`.

### 5. Candidates — preliminary

**Verdict: substantively strong; filtering and copy have confirmed defects.**

Strengths:

- The preliminary dossier clearly states the possible institutional defect, overlap, counterargument, open questions, recommendation, and sources.
- The current Smithsonian record is neutrally framed and does not presume unlawfulness or admission.

Defects:

- The record stores `Trump II`, but `termLabel()` accepts only `1`, `2`, and `both`. The card is labeled `Both terms`.
- Selecting First term or Second term removes the record instead of classifying it correctly.
- Copy says `1 preliminary candidate require human review` and `1 candidates shown`.

Recommended treatment:

- Normalize term values at the schema boundary or support the actual canonical enumeration.
- Add schema validation and generated-data fixtures.
- Apply singular/plural helpers throughout the Console.

### 6. Sources — catalog

**Verdict: comprehensive inventory; poor assurance and taxonomy support.**

Strengths:

- 2,055 cited-source records are searchable and sortable.
- Record identity, ownership, source metadata, and canonical links are preserved.
- Pagination is present.

Defects and gaps:

- The Source type control exposes about 199 raw type labels, including near-synonyms such as `News Report` and `News Reporting`.
- Reviewed and Reliability values are searchable but are not first-class table columns or filters.
- Point-in-time counts included 1,057 `Reviewed: No`, 239 `Partial`, and 742 `Yes`; the Console does not expose the assurance gap.
- The raw type dropdown and owner/domain selectors become unwieldy.
- Source-health status, last check, monitoring state, and owner are not integrated into a compact assurance view.

Recommended treatment:

- Preserve raw canonical type values.
- Add a derived Console-only family: Government, Judicial, Legislative, Scholarly, News, Advocacy, Tracker, and Other, with an advanced exact-type filter.
- Add Reviewed, reliability/identity class, monitoring, owner, and health facets.
- Treat incomplete review as agent/coverage work, not thousands of human actions.

### 7. Sources — pending

**Verdict: correct empty state; unnecessarily busy when empty.**

The screen correctly reports zero pending sources. When empty, active search and routing filters add no value. Replace them with a compact empty state and reveal controls only when records exist.

### 8. Sources — Court watcher

**Verdict: useful specialist view; exact-delta linkage and scale need correction.**

Strengths:

- The full 497-source watch inventory remains inspectable.
- Updated records can be brought forward.
- PR evidence is linked.

Defects and gaps:

- The `+1` signal represents one proposal, while the exact-head recommendation identifies 42 changed source rows plus the associated formal candidate.
- The watcher surface links to the pull request but not primarily to the Action Item recommendation that owns the disposition.
- Large groups are eagerly rendered without pagination or virtualization.
- Group disclosure preference keys are not unique across monitoring groups for the same owner.

Recommended treatment:

- Label `1 proposal / 43 affected records` when the exact head remains unchanged.
- Route the primary review action to the exact-head recommendation; keep GitHub as supporting evidence.
- Paginate or virtualize the inventory.

### 9. Sources — Presidential directives watcher

**Verdict: useful catalog; update semantics are misleading.**

Strengths:

- Complete 3,007-directive catalog with pagination and sorting.
- Administration and screening-status filters are meaningful.

Defects and gaps:

- The `+1` signal represents one proposal, while the exact-head recommendation identifies 10 affected directives.
- Live PR parsing relies on narrative body counts and does not ingest the exact bound affected-ID set.
- An in-session state transition can leave `updated only` active after live hydration determines that no affected rows exist in the checked-in catalog, producing a zero-result trap.
- A second stable sort pins updates ahead of the user-selected sort while `aria-sort` describes a simple global sort.

Recommended treatment:

- Label `1 proposal / 10 affected directives`.
- Ingest structured exact-head affected IDs.
- Clear or disable the updated-only state when the exact set is unavailable in the checked-in view.
- Make compound sorting explicit in the header or remove the hidden update-first override.

### 10. Sources — Source Checker Bot

**Verdict: valuable raw evidence; completeness and prioritization are misleading.**

Strengths:

- All 2,048 returned results are inspectable.
- Classifications reconcile: 1,074 verified; 772 access restricted; 95 identity-preserving redirects; 81 review required; 14 broken; nine transient; and three identity mismatches.
- The Integrity projection correctly narrows the actionable classes to 98 broken, identity-mismatch, or review-required records.

Defects and gaps:

- The current catalog contains 2,055 sources, so seven sources (`SRC-2648`–`SRC-2654`) were outside the last scan. The UI presents 2,048 as complete configured-catalog coverage.
- The schema uses `checked_at`, but Integrity tests for `generated_at`, producing a false `Baseline not established` problem.
- A second observation repeats that Source Checker is a report-only pilot.
- Live Source Checker refresh does not reject an older payload before replacement.
- `879 exceptions` gives access-restricted records the same apparent weight as broken or identity-mismatched records.
- There is no new/regressed/resolved trend, age, recurrence, current-catalog revision, catalog hash, or missing-ID list.
- All 2,048 rows are eagerly rendered.

Recommended treatment:

- Show `2,048 checked / 2,055 current`, seven unscanned, source revision, per-catalog expected/actual count, and catalog hash.
- Define baseline validity as schema-valid `checked_at`, nonempty results when eligible count is nonzero, and count reconciliation.
- Separate actionable exceptions from access limitations.
- Add new, regressed, resolved, and aging views.
- Paginate or virtualize.

### 11. Integrity

**Verdict: valuable composite concept; naming and accounting reduce trust.**

Strengths:

- Every projected problem remains inspectable.
- Human, agent, bot, and observed ownership classes are explicit.
- Search and filters cover owner, severity, and state.
- Full Project Integrity run history is linked.

Current composition:

| Component | Count | Freshness owner |
| --- | ---: | --- |
| Source integrity | 98 | Source Checker |
| Candidate dossier completeness | 7 | GitHub Project/candidate snapshot |
| Operational observations | 2 | Agent registry and Console readiness logic |
| Total | 107 | No single common timestamp |

The 107 include 17 errors, 81 warnings, and nine informational records.

Defects and gaps:

- The screen says `Project integrity` while the Project Integrity Bot’s latest run is clean.
- A clean deterministic run and 107 composite exceptions can therefore look contradictory.
- The overall timestamp is not a valid common freshness statement for all components.
- The two Source Checker observations are duplicative, and one is false because it tests the wrong timestamp field.
- Missing-feed paths can render clean zeroes rather than unavailable state.
- Human ownership can be inferred from message substrings, so wording changes can reroute an item.
- Source exceptions open the observed external URL rather than the internal catalog record that should own remediation.

Recommended treatment:

- Present four source-specific sections:
  - Project consistency;
  - Source health;
  - Candidate completeness; and
  - Operational readiness.
- Show each section’s checked time, source revision, current count, new, regressed, and resolved.
- Keep one composite total only as a secondary count.
- Require typed `attention`, `owner`, `action`, and `decision_question` fields.
- Give every confirmed gap a stable obligation key, first-seen and last-checked times, affected records, severity, evidence, accountable owner, exact next action or review trigger, and resolution proof. Repeated detection should update one obligation rather than create noise; a gap may disappear only after verified resolution or a recorded human disposition.
- Move informational runbook state to Agents & Bots unless it represents an actual exception.

### 12. Agents & Bots — Administration

**Verdict: operationally rich; current, historical, and queued state are conflated.**

Strengths:

- Registered worker counts, current chain, stage status, recovery posture, queue, Review Epoch, usage, and coordinator controls are present.
- Controls fail read-only when the localhost coordinator is absent.
- Consequential requests are bounded and described.

Defects and gaps:

- Current chain can be complete while the Elim status card prominently says Failed from the latest prior invocation.
- The checked-in fallback chain is failed with zero stages, but the Administration renderer treats zero stages as `Awaiting first projection`, hiding the failure unless live hydration succeeds.
- Overview can mark planning succeeded merely because a chain ID exists.
- `156` Elim-eligible items have no inspectable composition or ranking.
- Retained alert records remain individually actionable even when later successful chains objectively supersede their immediate condition.
- Repeated non-main-branch preflight attempts are classified as new failures instead of one expected hold or incident.

Recommended treatment:

- Separate:
  - Current chain result;
  - Latest run per worker;
  - Active incidents;
  - Superseded-but-unconfirmed alerts; and
  - Retained history.
- Treat an active feature branch as an inhibited/expected hold unless a distinct failure remains after returning to main.
- Show the queue by work class, owner, safety class, age, release relevance, and exact next item.
- Add an inspectable `Gap stewardship` queue covering project structure, source and monitoring coverage, candidate completeness, publication, automation, and contribution-integrity findings. Deterministic stages detect and recheck objective conditions; the Run Coordinator retains and prioritizes obligations; Elim investigates, repairs within authority, validates closure, or routes a human-reserved decision. Aging must prevent lower-severity gaps from persisting indefinitely.
- Apply the same checks to outside contributions at their exact current revision before integration: identity, classification, required fields, canonical linkage, evidence and provenance, lifecycle/authority boundaries, affected generated views, and validation. Do not treat acceptance, merge, or a later clean aggregate run as proof that a specific gap was resolved.

### 13. Agents & Bots — role directory

**Verdict: authoritative and useful; too long for routine scanning.**

Strengths:

- All seven persistent roles have stable identity, runbook, runtime, current result, latest success, recovery posture, filtered log, and full runbook-derived detail.
- Authority boundaries remain linked to controlling sources.

Gaps:

- All role cards and all runbook sections are rendered in one long page.
- Current status is duplicated from Overview and Administration.
- No quick role index, status filter, or exception-only mode exists.

Recommended treatment:

- Keep complete role detail.
- Add a compact index and `exceptions only` filter.
- Render runbook sections only when opened.
- Leave daily state on Overview/Administration and treat this screen as the durable directory.

### 14. Logs — Horizon

**Verdict: retain as complete specialist history.**

The 45-entry candidate disposition history is searchable, sortable, groupable, and links current route with complete entry detail. Add recency filters and affected-record links where possible, but do not replace the canonical Horizon log.

### 15. Logs — Elim

**Verdict: strong provenance.**

The ten-run history contains usage, work summary, outcome, stop reason, and exact next action. It is valuable. Add incident linkage and clearer separation of failed-before-substance, failed-during-work, human-review, and completed outcomes.

### 16. Logs — Bots

**Verdict: useful, but identity and task filters should drive a unified recent view.**

The full agent audit history is retained. Filtered deep links from each role are a strong linkage. Add direct affected-record and run-chain links, and validate source-domain event references rather than relying only on recommendation text.

### 17. Logs — Sources

**Verdict: strong exact-head recommendation record.**

The Source Monitor Log correctly holds five material watcher/recommendation events and preserves exact-head recommendations. The Console should make this the source for affected record IDs and counts instead of re-parsing abbreviated PR narratives.

### 18. Logs — Integrity

**Verdict: useful bounded history; excessive clean runs on Overview.**

Thirty retained runs make the deterministic history inspectable. Preserve all here, collapse consecutive clean runs elsewhere, and link each run to its workflow/revision.

### 19. Logs — Changes

**Verdict: valuable methodology history.**

Forty Change Audit entries preserve project-wide method and consistency changes. Add recency filters and affected surfaces, but do not turn the derived recent-activity stream into a competing log.

### 20. Publication — page assignments

**Verdict: strong completeness control; heavy rendering and incomplete conflict recovery.**

Strengths:

- Every one of 344 controlled Markdown pages is classified.
- Zero unclassified and zero metadata conflicts is a meaningful structural result.
- Staging is reversible and export-based.

Defects and gaps:

- All 344 rows and hundreds of per-row controls are eagerly constructed.
- Keyboard focus is lost after rerendering staging actions.
- A conflict row can remove edition assignments but does not provide a direct `keep editions / clear exclusion` resolution path.
- Changes count affected page records, not user operations.
- Project crosswalks and public topic pages lack a shared product identity and explicit internal-to-published stage relationship.

Recommended treatment:

- Paginate or virtualize the inventory and render the row editor only when opened.
- Preserve focus and announce staged changes.
- Show `operations staged` separately from `records affected`.
- Provide an explicit conflict-resolution control.
- Add a topic-product view that connects each internal project crosswalk to its published topic page without treating either stage as an issue.

### 21. Publication — edition analysis

**Verdict: good assembly analysis; not a release-readiness decision.**

Strengths:

- Composition, words, estimated pages, actual build, shared pages, preflight, and risk records are useful.
- Structural validity is accurately derived from publication metadata.

Defects and gaps:

- `READY — No structural blockers detected` can appear with a stale PDF, 119 out-of-edition references, nine long-page findings, 25 external-review items, 26 release blockers, and incomplete governance work.
- The current “Length and layout review” preselects the 30 longest pages, so shorter pages with wide-table or heading defects can be omitted from the table even though they contribute to the metric.
- Publication staleness is inferred from filesystem modification time rather than export revision and input hashes.
- Singular copy says `1 pages`.

Recommended treatment:

- Rename the current result `Assembly structurally valid`.
- Add a separate `Release readiness` section tied to governance items, release blockers, external review, required audits, export revision, link checks, and the human go/no-go decision.
- Show the complete union of flagged pages; optionally provide a separate `30 largest pages` table.

### 22. Publication — document builder

**Verdict: useful and functional; needs clearer change accounting and accessibility.**

The move/reset flow worked in rendered testing. Moving one section produced `21 staged`, because 21 page records changed order, and reset restored the canonical sequence. The tool should say `1 operation · 21 affected records`.

Additional defects:

- Page-level arrow buttons announce only `up` or `down`, not the page title.
- Rerendering loses keyboard focus.
- Several sections say `1 records`.
- Full table-of-contents content is eagerly rendered.

Recommended treatment:

- Add contextual accessible names.
- Preserve focus and announce changes.
- Lazy-render page lists and long table-of-contents branches.
- Distinguish operations from affected records.

## Cross-cutting linkage and data findings

### Data freshness and lineage

The Console combines:

- a checked-in bundle;
- locally cached generated feeds;
- live `project-console-data` feeds;
- live GitHub REST pull-request state;
- authenticated GitHub Project state generated elsewhere; and
- optional localhost host/coordinator state.

This architecture is reasonable, but each domain needs a uniform data contract:

| Required field | Purpose |
| --- | --- |
| `schema_version` | Reject incompatible payloads |
| `generation_id` | Prevent mixed-generation bundles |
| `source_revision` | Identify the canonical source state |
| `generated_at` or schema-defined `checked_at` | Establish comparable time |
| `expected_count` / `actual_count` | Detect incomplete projection |
| `source_hashes` | Verify exact inputs |
| `available` / `current` / `stale` / `unavailable` | Prevent guessed zeroes |
| `projection_errors` | Report partial parsing instead of silently dropping data |

Confirmed lineage defects:

1. The builder selects a local Integrity cache before considering a newer data-branch feed.
2. Candidate Project fields can remain stale after live Progress refresh.
3. Source Checker does not report its seven-current-record coverage gap.
4. Source Checker live refresh does not reject an older payload.
5. Progress, Integrity, and Source Checker history workflows can publish truncated history after a transient prior-history read failure.
6. Generated-domain files can be assembled from mixed generations without a manifest or atomic swap.
7. GitHub issue, Project, and pull-request queries have fixed caps without completeness indicators.
8. Log parser header mismatch can silently yield an empty projection.

### Routing

Static primary and sub-screen hashes resolved in testing, and no browser-console errors or warnings were observed. Remaining routing work:

- make workflow queue destinations filter-aware;
- route preliminary intake to its owning dossier;
- route source-health findings to the internal source record first;
- distinguish internal Console routes from external links;
- link exact-head recommendations to their source-domain event; and
- detect incomplete result pagination.

### Accessibility

Confirmed concerns:

- sort, pagination, publication staging, and builder rerenders can discard keyboard focus;
- top-level, section, and watcher panels are keyboard-focusable but their outline is removed;
- the skip link targets a navigation element that is not reliably focusable;
- builder arrow controls lack contextual accessible names;
- updates-first sorting can disagree with `aria-sort`;
- state changes are not consistently announced in a live region; and
- the enormous eager DOM increases screen-reader and keyboard burden.

Responsive layout did not produce page-level horizontal overflow at 390 pixels. Wide tables remained inside scrollable containers. That is a meaningful strength, but it does not replace keyboard and assistive-technology testing.

### Personalization

Layout preferences work for many cards and disclosures, but registration is incomplete:

- one configured `overview-overnight-grid` target does not exist;
- Overview queue directories and some Automation groups are not registered;
- court-watcher preference keys can collide across monitoring groups; and
- persistence behavior lacks executable cross-screen tests.

### Performance and scalability

Point-in-time rendered scale:

| Measure | Observed |
| --- | ---: |
| Raw Console payload | ~12.9 MB |
| Synchronous scripts | 41 |
| DOM elements | 70,814 |
| Articles | 2,197 |
| Table rows | 4,387 |
| Buttons | 1,477 |
| Selects | 854 |
| Options | 5,242 |

The client loads all catalog chunks and renders all hidden screens at startup. Recommended architecture:

1. Load only the Overview shell and essential summary feeds initially.
2. Load domain data when its primary or sub-screen is first opened.
3. Render only the active screen.
4. Paginate or virtualize Source Checker, court watcher, publication assignments, logs, and other large collections.
5. Render detail editors and runbook bodies only when opened.
6. Build generated domain files into a temporary directory, validate one generation manifest, then atomically replace the bundle.

## Project-manager coverage model

### Questions the Console should answer

| Manager question | Current coverage | Required improvement |
| --- | --- | --- |
| What needs my decision or recovery action now? | Action Items | Exact brief, age, consequence, owner, and route to the owning specialist screen |
| What work assigned to others needs my oversight? | Partial repository and automation counts | Secondary owner-preserving oversight view that does not inflate my action total |
| Are project gaps being found and closed without me tracking each one? | Fragmented Integrity, source, candidate, monitoring, publication, and automation findings | Durable Run Coordinator obligations with Elim investigation/repair/routing, aging protection, and verified closure |
| What issue-development work should Elim or the project do next? | Progress counts and board | Ranked, inspectable issue-development worklist with reason |
| Are we on pace? | Current-scope metrics | Scope reconciliation and movement explanation |
| What changed since I last looked? | Automated-only recent list | Unified material human + automation digest |
| What is blocked or deferred? | Holds with reasons | Age, reassessment trigger, escalation posture |
| What requires monitoring? | Monitoring inventory | Last pass, cadence, method, gap, latest posture |
| Are sources adequate? | Catalog and checker | Review coverage, current-scan coverage, deltas |
| Is automation healthy? | Rich raw state | Current/history/incident separation |
| Which candidates deserve work? | Dossiers | Priority, readiness, age, gaps, trigger |
| Which internal crosswalks are ready to become public topic pages? | No coherent product-stage view | One crosswalk-to-topic-page lifecycle under Publication |
| Is publication ready? | Assembly validity | Release critical path and go/no-go readiness |

### Recommended manager workbench

Do not add a tenth primary tab. Add coordinated subordinate views:

#### Overview — Manager focus

Overview should remain primarily an administrative, technical, and operations briefing. It may surface a high-level issue-development exception when it materially affects project operations, but detailed issue development belongs in Progress, Candidates, and Sources.

- Human decisions due now.
- Active incidents, grouped by root cause.
- Critical release blockers.
- Top material changes since last review.
- Stale/incomplete/unavailable data domains.
- Next scheduled or triggered review.

#### Progress — Next work

Progress should be the primary detailed issue-development workspace: portfolio maturity, workflow posture, issue-development priorities, holds, monitoring triggers, and the next work needed to move records responsibly. Do not place non-issue product or release-delivery work here; route it to Publication.

Each row should include:

- identifier and title;
- workstream;
- Priority;
- Release blocker;
- workflow Status;
- Development level;
- Score and Runs where applicable;
- Last audit;
- Next audit or exact next action;
- Change audit needed;
- Rebaseline status;
- age;
- milestone/due date;
- owner;
- blocker/dependency;
- monitoring trigger; and
- an explicit explanation of why it appears in the current cohort.

Ranking must be transparent and deterministic. It must not silently make a substantive priority decision. Suitable cohorts include:

1. human-reserved decisions;
2. active critical incidents;
3. Critical/High release blockers;
4. audit-needed work with prerequisites met;
5. monitoring triggers that have fired;
6. stale or incomplete source/candidate work;
7. external-review follow-up; and
8. ordinary development backlog.

#### Publication — Product and release delivery

- the twelve non-proposal delivery items;
- Public Release 1.0 milestone;
- parent/sub-issue completion;
- Priority and Release blocker;
- current Status;
- owner;
- dependency;
- required validation;
- next action; and
- human go/no-go conditions.

Add a `Topic products` subsection that treats each project crosswalk and topic page as one product with two stages:

1. `Project crosswalk — internal`;
2. `Topic page — published product`.

Show the stable product identity, internal crosswalk route, public topic-page route when published, current stage, owner, publication prerequisites, and transition decision. Do not assign an issue identifier, Development level, Proposal Quality Score, `Runs`, or issue-development Status to the product itself. Any GitHub tracking item remains a production task, not the substantive product identity.

#### Sources/Progress — Monitoring health

- watched matter;
- why it matters;
- trigger;
- checking method;
- last checked;
- next due/cadence;
- coverage sources;
- coverage gaps;
- latest posture;
- change since last pass; and
- owner.

Routine monitoring remains outside Action Items until a material development or reserved choice exists.

#### Publication — Release readiness

Keep structural assembly analysis separate from:

- open release blockers;
- required audits;
- external review;
- link/export validation;
- current export revision;
- source and input hashes;
- stale PDF status;
- cross-edition reference disposition;
- copyright/reuse checks; and
- human approval.

## Prioritized defect and improvement register

| ID | Priority | Finding | Required outcome |
| --- | --- | --- | --- |
| CON-001 | P0 | Twelve non-proposal delivery items and 26 release blockers lack a PM surface | Add a Publication product/release-delivery workbench without adding them to the proposal goal count |
| CON-002 | P0 | The Console does not explain how approved consolidation changed 204 separately counted proposals into the current 81-record architecture | Plain-language portfolio history, separate earned-readiness movement, and a current-scope forecast |
| CON-003 | P0 | Watcher badges show proposals as changed records | Show proposal count and exact affected-record count from bound exact head |
| CON-004 | P0 | Twelve retry events inflate human actions | Incident grouping with full retained occurrence history |
| CON-005 | P0 | Source Checker reports 2,048 as complete against 2,055 current | Coverage ratio, missing IDs, revision, expected/actual counts |
| CON-006 | P0 | False Source Checker baseline finding | Validate baseline using schema-defined `checked_at` and count consistency |
| CON-007 | P0 | Missing feeds can appear as clean zeroes | Uniform availability/current/stale/unavailable contract |
| CON-008 | P0 | Checked-in fallback can hide a failed zero-stage chain | Render failure/preflight state independently of stage rows |
| CON-009 | P1 | Candidate board does not hydrate from live Progress fields | Merge authoritative `progress.candidates` fields by ID |
| CON-010 | P1 | Integrity conflates four systems under one total/timestamp | Component sections with source-specific freshness and delta |
| CON-011 | P1 | No ranked, inspectable next-work list | Transparent authoritative-field cohorts and rationale |
| CON-012 | P1 | No material human + automation “since last review” view | Derived chronological digest; no new ledger |
| CON-013 | P1 | Queue routes are unfiltered | Filter-aware hashes and worklists |
| CON-014 | P1 | Integrity `+00:00` timestamps can display in the future | Standards-compliant ISO-8601 parsing and timezone tests |
| CON-015 | P1 | Preliminary term mapping is wrong | Canonical enumeration and executable filter tests |
| CON-016 | P1 | A recorded score of `0` is rendered as `Score —`; generic fallbacks can also replace `0` or `false` with missing-value text | Display valid scores from `0` through `100` exactly; reserve unavailable for absent data, flag invalid scores, and use nullish generic fallbacks |
| CON-017 | P1 | Publication “Ready” means only structural validity | Rename and add true release-readiness section |
| CON-018 | P1 | Layout-risk table can omit flagged records | Complete union of risks plus optional largest-pages view |
| CON-019 | P1 | History can be truncated after prior-feed read failure | Fail closed or compare-and-swap current/history |
| CON-020 | P1 | Mixed-generation bundle can be assembled | Generation manifest, validation, and atomic replacement |
| CON-021 | P1 | Keyboard focus is lost and focus outlines removed | Focus retention, focus-visible styling, live announcements, skip target |
| CON-022 | P1 | 12.9 MB / 70k-node eager application | Lazy data/rendering, pagination/virtualization, performance budgets |
| CON-023 | P1 | Source taxonomy and assurance are not decision-usable | Derived type families and review/reliability/health facets |
| CON-024 | P1 | Monitoring lacks cadence, method, gap, and latest posture | Monitoring-health view conforming to Project Interface |
| CON-025 | P2 | Pending screen shows controls for zero records | Compact conditional empty state |
| CON-026 | P2 | Overview repeats worker cards and clean runs | Exception/material-result summaries; detail in Administration/Logs |
| CON-027 | P2 | Lifetime Logs badge has no PM meaning | Remove or replace with new-since-last-visit |
| CON-028 | P2 | Singular/plural defects recur | Shared grammar helpers and tests |
| CON-029 | P2 | Layout-preference registration and keys are incomplete | Complete registration, unique composite keys, persistence tests |
| CON-030 | P2 | Major outage/maintenance status lacks severity mapping | Complete provider-status tone mapping |
| CON-031 | P0 | A Console-only workaround could conceal a verified project structural defect | Classify the defect by owning layer, repair the authoritative structure, and regenerate all affected projections |
| CON-032 | P1 | Most Overview feeds are labeled Current under an undocumented hard-coded 48-hour default | Source-specific latest-state rules in which authoritative revision and completeness outrank elapsed age; show Review Epoch state separately |
| CON-033 | P0 | Confirmed gaps can remain fragmented, repeatedly rediscovered, or silently disappear; enumerated queues can also be misconstrued as limiting Elim's discovery | Durable deduplicated obligations plus non-exhaustive Elim discovery and investigation, authority-bounded repair or reporting, age protection, contributor checks, and complete canonical documentation |
| CON-034 | P0 | An empty ordinary queue currently closes as a no-op instead of using Elim for governance review and discovery | A Change-Audited low/no-work governance-discovery mode synchronized across the coordinator, Elim, runtime, queue, Console, and tests |
| CON-035 | P1 | `System currency` is unclear and combines data recency, service availability, and Codex capacity | Rename the section `Project data and services` and label the three questions plainly |

## Recommended implementation sequence

### Phase 0 — establish executable truth contracts

1. Add a generated bundle manifest with schema, generation ID, source revision, timestamps, file hashes, and expected/actual record counts.
2. Define availability and source-specific latest-state rules for every feed; a superseded revision is stale immediately even if it is younger than a generic age threshold, and Review Epoch cadence remains separate.
3. Add runtime/browser fixtures using current generated payload shapes.
4. Make history publication fail closed or compare-and-swap.
5. Add pagination-completeness checks for GitHub issues, Project items, and pull requests.
6. Classify every verified finding as presentation, builder/feed, canonical-record, Project schema/workflow, governing-rule, automation, or publication structure; repair the owning layer rather than masking it downstream.

### Phase 1 — correct trust-level defects

1. Scope reconciliation.
2. Exact-head watcher affected records.
3. Automation incident model.
4. Source Checker coverage and baseline validity.
5. Checked-in/live candidate and chain reconciliation.
6. Count semantics and human decision briefs.
7. ISO timestamps, term values, zero values, and grammar.
8. Closed-loop Elim gap stewardship and outside-contribution integrity.
9. Non-exhaustive Elim discovery and low/no-work governance-review mode.

### Phase 2 — add project-manager decision support

1. Release-delivery workbench.
2. Transparent portfolio next-work cohorts.
3. Unified material-activity digest.
4. Monitoring health.
5. Source assurance.
6. Integrity component accounting.
7. Publication release readiness.

### Phase 3 — accessibility and interaction quality

1. Focus retention and live announcements.
2. Focus-visible panels and reliable skip target.
3. Contextual accessible names.
4. Correct compound-sort semantics.
5. Internal/external link handling.
6. Unique and complete personalization keys.

### Phase 4 — performance and scale

1. Lazy data loading by domain.
2. Active-screen-only rendering.
3. Pagination/virtualization.
4. Deferred detail/runbook rendering.
5. Initial-load, DOM-node, interaction-latency, and generated-file budgets.

## Acceptance criteria

Implementation is not complete until all of the following are true:

1. The 98 proposal/candidate portfolio items are visible in Progress and the 12 non-proposal delivery items are visible in Publication without mixing their counts or lifecycle fields.
2. All current release blockers can be filtered and inspected.
3. Progress explains `204 → 198 → 77 → 81` in plain language, links the approved consolidation, and separately displays earned Review Ready movement from 23 to 27.
4. A scope removal cannot be counted as Review Ready attainment or regression without its disposition.
5. A watcher proposal displays both proposal count and complete exact-head affected-record count.
6. A changed PR head invalidates its recommendation and affected-record projection.
7. Automation retry occurrences are retained but counted as one active incident per current root cause.
8. The primary Action Items total equals only the items assigned to the project owner; a clearly secondary oversight view shows work assigned to others without inflating that total.
9. Every Action Items entry includes an exact question or recovery action, its actual owner, and a route to the specialist Console screen that owns the underlying state; Action Items carries no independent authority.
10. Missing or invalid feeds display Unavailable, never zero or Clean.
11. Source Checker reports checked/current coverage, missing IDs, and baseline validity correctly.
12. Project consistency, source health, candidate completeness, and operational readiness have separate counts and freshness.
13. Current chain, latest worker result, and unresolved incident are visibly distinct.
14. ISO timestamps with `Z`, `+0000`, and `+00:00` render and sort identically.
15. Preliminary term filters correctly classify the actual canonical values.
16. A recorded score of `0` displays explicitly as `Score 0`; absent score data displays as unavailable; nonnumeric or out-of-range scores surface as integrity defects; and Boolean `false` is not replaced by missing-value text.
17. Workflow queue links open a filtered Progress issue-development worklist.
18. Publication distinguishes assembly validity, topic-product stage, and release readiness.
19. The complete union of layout-risk records is inspectable.
20. Keyboard focus remains on a logical control after sort, pagination, stage, reset, and builder actions.
21. Screen changes and staged changes are announced accessibly.
22. All primary and sub-screen routes pass desktop and mobile browser tests.
23. Large collections are paginated or virtualized and hidden screens are not eagerly rendered.
24. Generated history cannot be truncated by a transient prior-feed failure.
25. One generation manifest proves every loaded domain file belongs to the same build.
26. Overview remains primarily an administrative, technical, and operations briefing and routes detailed issue development to the owning specialist screen.
27. Progress is recognizably the primary detailed issue-development workspace while non-issue product and release delivery are routed to Publication.
28. Each project crosswalk and corresponding topic page share one product identity and appear as the internal and published stages of that product; neither is classified or counted as an issue, proposal, candidate, or evidence record.
29. Every verified project structural defect discovered during implementation is either repaired at its authoritative owning layer and propagated through affected projections or explicitly deferred with owner, reason, and required decision.
30. No Console-only compatibility rule masks a canonical classification, identity, schema, routing, authority, or lifecycle defect.
31. Review Epoch status is displayed independently from whether Console data reflects the latest authoritative state, and no feed is labeled Current solely because it falls below the present hard-coded 48-hour default when a newer authoritative revision or incomplete synchronization proves otherwise.
32. Every confirmed gap has one stable obligation with first seen, last checked, severity, affected records, evidence, owner, next action or review trigger, aging posture, and resolution proof.
33. Repeated detections update the same obligation, and neither a rebuild, merge, later clean aggregate run, nor temporary absence from one feed silently closes it.
34. The Run Coordinator retains and prioritizes routine gap obligations; Elim investigates, repairs within delegated authority, verifies closure, or routes the exact human-reserved question. Routine Elim-owned work remains outside the project owner's primary Action Items total.
35. Outside contributions receive exact-revision structural, provenance, authority, linkage, and validation checks before integration, and any resulting obligation follows the same closed-loop process.
36. Elim's queue, work order, context packet, named detectors, and Console categories are implemented as minimum required coverage rather than an exhaustive limit on credible project-related discovery or unprompted investigation.
37. An unprompted finding becomes a traceable discovered work unit: Elim fixes and validates it when authorized, reports it without implementation when outside scope or explicitly forbidden, and preserves it with a next trigger when inconclusive.
38. Every discovered finding records its source revision, evidence, reasoning, affected scope, authority determination, action or non-action rationale, validation/readback, disposition, owner, and next action or trigger in one canonical detail record with linked—not duplicated—provenance.
39. An otherwise authorized run with little or no ordinary queued work enters documented project-governance review and discovery mode rather than closing solely because the predefined queue is quiet.
40. The governance-discovery mode is implemented through the required automation-architecture Change Audit and synchronized governing/runtime updates; it preserves the usage reserve, exact-source controls, validation, and all explicit prohibitions and human-reserved boundaries.
41. Overview uses `Project data and services`, not `System currency`, and separately answers whether project data is up to date, connected services are available, and Codex capacity is sufficient.

## Final recommendation

Adopt the report as an implementation backlog, not as authority. Repair the trust-level defects first, including any verified project structural defects the work exposes; then add decision support and optimize the client. Preserve the nine-screen architecture and the approved Overview style. The goal is not to make the Console display more information; it is to make the information already available answer the project manager’s next question with clear scope, provenance, recency, ownership, and consequence—and to correct the project structure when the Console proves that the source itself is defective.
