---
title: "ARRP Project Console — Implementation Prompt"
status: non-authoritative-reference
version: "1.0"
as_of: "2026-07-25"
implementation_baseline: "e45a0e711aa82ca147cdc827cbf18c8b348e4cdd"
print_status: excluded
print_exclusion_reason: "Nonauthoritative internal implementation handoff."
---

# ARRP Project Console implementation prompt

Use the prompt below in a fresh implementation task after the review report is accepted.

---

You are implementing the accepted recommendations in:

`framework/reports/project-console-comprehensive-review-2026-07-25.md`

The report is a non-authoritative product review. The Framework, Agent Operating Rules, Project Interface, Project Console Progress, GitHub Workflow, lifecycle rules, source/monitoring rules, publication rules, registered agent and bot runbooks, and canonical records remain controlling. If the report conflicts with a governing record, stop, document the conflict, and follow the governing record.

## Objective

Improve the complete ARRP Project Console so it is trustworthy, managerially useful, accessible, performant, and fully traceable. Reduce the project owner's cognitive and administrative burden without suppressing gaps or narrowing Elim's ability to discover and investigate credible project-related problems. Repair verified underlying project structural defects revealed by the work while preserving substantive and human-reserved authority.

Preserve:

- the nine primary screens;
- the approved compact Overview design;
- explicit unavailable states;
- Overview as primarily an administrative, technical, and operations briefing rather than an issue-development workspace;
- Progress as the primary detailed issue-development workspace;
- Action Items as a non-authoritative routing and oversight index, with the project owner's assignments primary and other owners' assignments secondary;
- project crosswalks and topic pages as the internal and published stages of one topic product, never as issues or proposals;
- exact-head recommendation invalidation;
- full candidate dossiers;
- complete specialist logs;
- read-only canonical data;
- reversible publication staging; and
- non-exhaustive Elim discovery and investigation, with change authority still bounded by governing rules; and
- the existing human/Elim/bot authority boundaries.

Do not add a tenth primary tab unless the human owner expressly approves it after reviewing a demonstrated need. Do not change Proposal Quality Score, Runs, lifecycle status, Project fields, candidate disposition, publication approval, or a human-reserved judgment merely to make the Console look consistent.

## Structural-defect rule

Console development is also a diagnostic pass over the structures that feed it. When the implementation verifies that a defect belongs to the underlying project rather than the presentation, correcting that structural defect is expressly within scope.

For every such finding:

1. identify the authoritative owning layer;
2. expand context under the route table before changing that layer;
3. distinguish an objectively demonstrated structural inconsistency from a substantive or judgment-dependent disagreement;
4. repair the authoritative source rather than hide the inconsistency with a Console-only translation;
5. regenerate every affected projection;
6. run the applicable project-level Change Audit, lifecycle, GitHub Project, publication, monitoring, or automation synchronization workflow; and
7. verify readback across every affected surface.

Structural defects include:

- incorrect entity classification;
- missing, duplicated, or unstable identity;
- incompatible schemas or controlled vocabularies;
- contradictory eligibility, lifecycle, routing, or ownership rules;
- broken canonical links or cross-surface joins;
- duplicated or missing authority;
- incomplete generated-feed or builder contracts; and
- incompatible repository, GitHub Project, automation, monitoring, or publication structures.

This authority does not permit a score change, candidate disposition, policy-merits judgment, publication approval, or other human-reserved decision merely because the Console exposed the question. Route those decisions normally. If a suspected structural defect cannot be objectively established, retain it as an explicit finding with owner, evidence, and next decision rather than guessing. A temporary compatibility layer is acceptable only when the authoritative repair is presently blocked and the limitation remains visible, tested, and assigned.

## Elim discovery, gap stewardship, and documentation rule

Treat every queue, work order, named detector, context route, Console category, and requested duty as minimum required coverage—not as an exhaustive whitelist of what Elim may notice or investigate. During an authorized run, Elim may pursue a credible project-related anomaly, omission, contradiction, emerging risk, latent structural defect, or connected question without a prior human prompt or queue entry. It may expand to the canonical context needed to understand that finding.

Keep discovery authority distinct from implementation authority:

1. If the finding is objectively supported, the repair is inside delegated authority, and no rule forbids it, create a distinct discovered work unit, make the repair, propagate every affected surface, validate it, and document it.
2. If the finding requires a human-reserved decision, exceeds delegated authority, is unsafe, or is explicitly forbidden, do not implement or work around the restriction. Preserve the evidence, analysis, consequence, recommendation, and exact human question or required authority.
3. If the result remains uncertain, retain one unresolved obligation with the uncertainty, owner, and next investigation trigger. Do not discard it merely because it was not part of the original task.

When an otherwise authorized run has little or no ordinary eligible work, the Run Coordinator must place Elim into `Project governance review and discovery` mode rather than close solely because the predefined queue is quiet. The mode is deliberately non-exhaustive. It reviews project structure, governing-rule integration, authority boundaries, workflow coherence, source and monitoring coverage, automation, publication, contributor readiness, accumulated technical debt, and cross-surface consistency; it may follow credible connected findings beyond those examples. It remains subject to the protected usage reserve, exact-source controls, validation, and all human-reserved and prohibited-action boundaries.

Implementing that idle-state rule changes the current approved automation architecture, which presently closes an empty LLM queue as a deterministic no-op. Record the required project-level automation-architecture Change Audit and synchronize the Framework/operating rules as implicated, Elim runbook, Run Coordinator runbook and dispatcher, runtime manifest/configuration, context routes, queue schema, Console projections, generated data, tests, and documentation. Do not implement this only as Console copy.

Thorough documentation is required for every discovered finding, including findings fixed immediately, reported without implementation, retained as uncertain, or resolved as no material defect. Use one canonical detail record with linked provenance rather than duplicating narratives. Record:

- Chain ID, Run ID, discovered work-unit ID, discovery context, and exact source revision;
- evidence, reasoning, uncertainty, affected records, and likely consequence;
- the governing authority analysis and why action was permitted, deferred, or forbidden;
- every change made—or the reason no change was made;
- affected repository, GitHub, Project, source, monitoring, automation, Console, publication, and public surfaces;
- validation, synchronization, and readback results;
- disposition and resolution evidence; and
- accountable owner plus the exact next action or review trigger.

Deterministic checks should detect objective conditions where possible, but they are a floor, not a substitute for Elim's judgment or open discovery. Repeated observations update one stable obligation with first-seen, last-checked, occurrence, aging, and status history. A finding may close only through verified resolution or a recorded human disposition; a rebuild, merge, later clean aggregate run, or temporary absence from one feed is not closure proof.

## Required startup

1. Start from current synchronized `main`, not the historical report baseline.
2. Confirm no overlapping Console task is still active.
3. Read `AGENTS.md`, the mandatory Framework and Agent Operating Rules kernels, `CURRENT_AUDIT.md`, Context Routing, Project Structure, GitHub Workflow, Project Interface, Project Console Progress, the Console README, lifecycle/development-level rules, monitoring rules, publication rules, audit rules, and all dependencies selected by context routing.
4. Refresh authenticated GitHub Project, open pull-request, Actions, and current data-branch state before designing changes.
5. Record the exact implementation baseline.
6. Classify findings by owning layer: Console presentation, builder/feed, canonical record, Project schema/workflow, governing rule, automation, monitoring, or publication.
7. Use parallel agents only for independent, non-overlapping responsibilities. The coordinating agent owns architecture, root-cause classification, integration, validation, and closeout.
8. Before changing Elim's empty-queue behavior or discovery contract, open the required automation-architecture Change Audit and identify every governing, runtime, queue, projection, and validation surface that must remain synchronized.

## Delivery strategy

Implement in reviewed phases. Each phase must leave the repository valid and must have executable tests. Do not combine all work into one unreviewable rewrite.

### Phase 0 — data truth and executable contracts

Implement a uniform feed and bundle contract:

- `schema_version`;
- `generation_id`;
- `source_revision`;
- schema-defined `generated_at` or `checked_at`;
- `expected_count`;
- `actual_count`;
- `source_hashes`;
- explicit `available`, `current`, `stale`, or `unavailable`;
- `projection_errors`; and
- pagination/completeness metadata.

Whether Console data reflects the latest authoritative state must be determined separately for each source. The Review Epoch cadence schedules comprehensive project review; it was not designed to control Console updates and must not be reused as a feed-freshness threshold. The existing front-end default of 48 hours is likewise not authority. For each feed, define the owning source, update trigger or expressly authorized cadence, expected source revision or generation, last successful synchronization, completeness requirements, and supersession rule. A newer authoritative revision makes an older projection stale immediately regardless of its elapsed age. Show Review Epoch status separately as last completed, next due, and overdue.

Requirements:

1. Build all generated Console files in a temporary location.
2. Implement and document how every freshness card determines whether its data reflects the latest authoritative state. Revision supersession and incompleteness must outrank elapsed age; use a maximum-age rule only when the owning process defines it.
3. Keep Review Epoch due state independent from whether Console data reflects the latest authoritative state.
4. Emit and validate one generation manifest containing every domain file and hash.
5. Atomically replace the generated bundle only after all validations pass.
6. Reject mixed-generation and older-live payloads.
7. Make explicit environment overrides the only inputs allowed to outrank a newer valid source merely because a local cache exists.
8. Fail closed or use compare-and-swap when retained history cannot be read. Never replace retained history with an empty history after a transient network or decode error.
9. Detect incomplete GitHub issue, Project, and pull-request pagination.
10. Make log parsers report expected/parsed counts and fail or expose projection errors on header/schema drift.
11. Add browser/runtime tests. Source-string substring tests are not sufficient.
12. Add regression tests at the authoritative layer for every project structural defect repaired during implementation.

### Phase 1 — correctness and trust

#### A. Progress scope

- Replace the unexplained signed `scopeChange` presentation with a plain-language portfolio-architecture history.
- For the review fixture, show: `204 active proposals at the July 13 baseline → 198 after the approved APPT consolidation → 77 after the approved July 16 portfolio consolidation → 81 after four later admissions`.
- Explain that the net `-123` means 123 fewer separately counted proposal records—not 123 completions, failures, or deletions.
- Display earned readiness separately: `23 Review Ready at baseline → 27 currently`.
- Link the consolidation steps to the adopted portfolio-consolidation record.
- Preserve reason-coded additions, mergers, retirements, reroutes, and eligibility changes for future movement; never show a bare signed count without its explanation.
- Label the forecast `on track for current scope`.
- Do not count consolidation, merger, retirement, rerouting, or another denominator change as substantive attainment or regression.

#### B. Release-delivery coverage

- Continue to show the 98-record proposal/candidate portfolio independently.
- Keep Progress limited to issue development.
- Add a Publication `Product and release delivery` workbench for the twelve non-proposal delivery items.
- Include Priority, Release blocker, Status, milestone, parent/sub-issue completion, owner, dependency, validation requirement, and next action.
- Do not add these items to the Review Ready denominator or apply issue-development lifecycle fields to them.
- Treat `Project crosswalk — internal` and `Topic page — published product` as two stages of one topic product with one stable product identity.
- Do not assign the product an issue identifier, Development level, Proposal Quality Score, `Runs`, or issue-development Status. A GitHub task may track production work without making the crosswalk or topic page a substantive issue.

#### C. Watcher exact-head state

- Drive affected-record counts and IDs from the structured exact-head bound event/recommendation, not abbreviated PR prose.
- Show distinct semantics such as `1 proposal / 43 affected records`.
- Preserve exact-head invalidation.
- If enumeration is unavailable, display `affected count unavailable/incomplete`; never guess one.
- Clear or disable an `updated only` filter when the affected rows are not present in the checked-in catalog.

#### D. Automation incidents

- Retain every event.
- Create an incident identity from root cause, failed prerequisite, and materially relevant checkout/runtime state.
- Show one active incident with occurrence count, first/latest occurrence, affected chains, current-chain state, exact repair, evidence of supersession, and full history.
- Treat expected non-main-branch inhibition as a hold unless a distinct failure persists after main is restored.
- Do not auto-resolve a human-required incident merely to reduce a count. A proven later success may mark it `superseded / confirmation available`.

#### E. Action Items

- Make `Assigned to you` the primary view and make its total equal only the items assigned to the project owner.
- Add a clearly secondary `Other assigned work to oversee` view for Elim-, bot-, automation-, and other-owner assignments. Preserve actual owner and status without inflating the project owner's action total.
- Treat Action Items as a derived, non-authoritative index only. It may summarize and route; it must not independently own status, priority, evidence, resolution, or disposition.
- Route every item first to the specialist Console screen that owns its domain—Progress, Candidates, Sources, Integrity, Agents & Bots, or Publication. The specialist screen may then link to the canonical repository or GitHub authority.
- Every project-owner item must show the exact question or recovery action, recommendation/options, why now, consequence of delay, age/due trigger, owner, and the owning specialist-screen route. Evidence and authoritative state remain on that specialist screen.
- Route preliminary intake to the owning dossier.
- Route source remediation to the internal catalog record first.
- Internal Console routes must remain in the Console rather than using an external new-tab helper.

#### F. Feed truth

- Missing/invalid feeds must be Unavailable, never zero or Clean.
- Render a failed zero-stage chain as failed.
- Distinguish current chain, latest worker run, active incident, and retained history.
- Make Source Checker baseline validation use its schema-defined `checked_at`, nonempty-results expectations, and count reconciliation.
- Display `checked / current`, missing IDs, source revision, per-catalog counts, and hashes.
- Reject an older live Source Checker payload.
- Remove the false and duplicative Source Checker readiness findings.

#### G. Small correctness fixes

- Rename the Overview heading `System currency` to `Project data and services`.
- Within that section, use `Data status` for whether Console data reflects the latest authoritative project state, `Service status` for connected-service availability, and `Codex capacity` for the protected usage reserve. Do not use `currency` as a manager-facing label.
- Parse ISO-8601 `Z`, `+0000`, and `+00:00` consistently for display and sorting.
- Normalize or support the actual preliminary-candidate term enumeration.
- Preserve three distinct score states: display every valid numeric score from `0` through `100` exactly, including `Score 0`; display an unavailable state only for absent score data; and surface nonnumeric or out-of-range scores as integrity defects instead of hiding them behind a dash. Do not infer a maturity or workflow status from zero; continue to display the authoritative Development level and Status independently.
- Use nullish checks in generic fallback helpers so `0` and `false` are not replaced by missing-value text.
- Use shared singular/plural helpers.
- Make compound sort behavior agree with `aria-sort`.
- Map major outage and maintenance service states to an appropriate severity.

### Phase 2 — project-manager decision support

#### A. Overview `Manager focus`

Add a compact block, using the established Overview visual language:

- human decisions;
- active incidents;
- Critical/High release blockers;
- top material changes since the last review;
- stale/incomplete/unavailable data domains; and
- next scheduled or triggered review.

Overview is primarily an administrative, technical, and operations briefing. Do not turn it into an issue-development workbench. It may surface a high-level issue-development exception when that exception materially affects operations, but it must route detailed issue work to Progress, Candidates, or Sources.

Do not duplicate full role cards. Summarize exceptions and material results; link to the owning specialist screen for detail.

#### B. Progress `Next work`

Make Progress the primary detailed issue-development workspace. It should explain portfolio maturity, workflow posture, issue-development priorities, holds, monitoring triggers, and the next work needed to move records responsibly. Route non-issue product and release-delivery work to Publication rather than placing it in Progress.

Create transparent cohorts using authoritative fields:

- human-reserved decisions;
- active critical incidents;
- Critical/High release blockers;
- audit-needed work with prerequisites met;
- fired monitoring triggers;
- stale or incomplete source/candidate work;
- external-review follow-up; and
- ordinary development backlog.

For every row show:

- identifier/title;
- workstream;
- Priority;
- Release blocker;
- Status;
- Development level;
- Score and Runs where applicable;
- Last audit;
- Next audit/exact next action;
- Change audit needed;
- Rebaseline status;
- age;
- milestone/due date;
- owner;
- blocker/dependency;
- monitoring trigger; and
- the deterministic reason it appears in that cohort.

This is a projection, not a competing tracker or unexplained automated ranking.

#### C. Recent material activity

Derive one chronological digest from canonical logs and GitHub lifecycle changes:

- human and automation activity;
- actor;
- outcome;
- affected records;
- timestamp;
- owning link; and
- whether it changed manager action.

Collapse repeated clean/no-op activity on Overview. Preserve complete entries in the canonical logs. Do not create a new authoritative ledger.

#### D. Monitoring health

Show:

- watched matter;
- material relevance;
- reassessment trigger;
- checking method;
- last checked;
- cadence/next due;
- coverage sources;
- coverage gaps;
- latest posture;
- change since last pass; and
- owner.

Routine monitoring remains outside Action Items until a development or reserved decision occurs.

#### E. Source assurance

- Add Reviewed, reliability/identity class, monitoring, owner, and health facets.
- Add a derived high-level source-type family while preserving the raw canonical type.
- Show new, regressed, resolved, and aging source-health exceptions.
- Separate actionable failures from access limitations.

#### F. Integrity

Present:

1. Project consistency;
2. Source health;
3. Candidate completeness; and
4. Operational readiness.

Each component needs its own count, source, checked time, source revision, new, regressed, resolved, and owner. A composite total may remain secondary. Typed ownership/action fields must control Action Item routing; wording must not.

#### G. Elim gap stewardship and governance discovery

Add an inspectable specialist view within Agents & Bots or Integrity—do not add a tenth primary tab—that shows:

- stable obligation or discovered work-unit ID;
- discovery source and exact revision;
- work class and affected records;
- first seen, last checked, age, and occurrence history;
- evidence and concise reasoning;
- actual owner and authority classification;
- authorized repair, exact human question, explicit prohibition, or next investigation trigger;
- current status and validation/resolution evidence; and
- canonical detail and provenance links.

Show routine Elim-owned gaps here and only summarize their count and risk on Overview. Send an item to the owner's primary Action Items view only when it requires the owner's judgment, authority, credential, unsafe external action, or intervention after failure to progress. The secondary oversight view may show Elim and other-owner obligations without transferring ownership.

Expose `Project governance review and discovery` as a real Elim mode with last run, reason selected, domains reviewed, findings opened/fixed/reported/retained, documentation links, validation, and next review posture. An empty ordinary queue must not appear as “nothing to review” if this mode was due or executed. Preserve a documented no-material-finding result when a review finds no defect.

Apply the same discovery and obligation process to outside contributions at their exact current revision before integration. Check identity, classification, required fields, canonical linkage, evidence and provenance, lifecycle and authority boundaries, affected generated views, tests, and documentation. A merge does not by itself close a related obligation.

#### H. Publication release readiness

Rename the current success state `Assembly structurally valid`.

Add a `Topic products` subsection. Model each product as one stable identity with exactly two lifecycle stages:

1. `Project crosswalk — internal`, for project synthesis, mapping, and review;
2. `Topic page — published product`, for the approved public-facing treatment.

Show the internal crosswalk route, public topic-page route when published, current stage, owner, publication prerequisites, and transition decision. Do not model either stage as an issue, proposal, candidate, or evidence record. Do not duplicate the product merely because it changes stage.

Add a separate release-readiness section containing:

- non-proposal delivery tasks;
- release blockers;
- required audits;
- external review;
- link/export validation;
- export revision and input hashes;
- stale PDF status;
- cross-edition reference disposition;
- copyright/reuse checks; and
- the human go/no-go question.

Show the complete union of layout-risk records. If useful, show a separate `30 largest pages` table.

### Phase 3 — interaction and accessibility

1. Preserve keyboard focus after sort, pagination, staging, reset, filter, and builder actions.
2. Announce sort/page/filter/staging changes in a scoped live region.
3. Remove unnecessary `tabindex=0` panel stops or provide strong `:focus-visible` treatment.
4. Give the skip link a reliable focus target.
5. Give every builder move control a contextual accessible name containing the page or section title.
6. Resolve publication conflicts with explicit `keep editions / clear exclusion` and inverse paths.
7. Make preference registration complete and persistence keys unique to owner plus monitoring group.
8. Add automated keyboard, responsive, and accessibility checks across every primary and sub-screen.

### Phase 4 — performance

1. Initial-load only the shell, Overview summaries, and data required for current navigation.
2. Lazy-load domain data when its screen is opened.
3. Render only the active screen.
4. Paginate or virtualize Source Checker, court watcher, publication assignments, logs, and other large collections.
5. Render runbook bodies, row editors, and large table-of-contents branches only when opened.
6. Remove unused duplicate preservation payloads from the browser bundle.
7. Add automated budgets for initial transferred bytes, initial DOM nodes, route activation, and interaction latency.

Use the report baseline of approximately 12.9 MB and 70,814 rendered elements as the condition to improve, not as an acceptable limit. Propose realistic budgets, document them, and make CI fail on material regression.

## Required tests

At minimum, execute:

- all existing repository tests;
- focused builder/feed tests;
- runtime browser tests for all nine primary screens and every sub-screen;
- current/stale/unavailable/malformed feed fixtures;
- a projection less than 48 hours old that has been superseded by a newer authoritative revision;
- independent Review Epoch due/overdue and latest-authoritative-data states;
- the `Project data and services` heading with separate `Data status`, `Service status`, and `Codex capacity` labels and no manager-facing `System currency`;
- mixed-generation rejection;
- older-live rejection;
- history-read failure and concurrent-update tests;
- authoritative-layer repair and affected-projection propagation for each discovered structural defect;
- rejection or visible deferral of any Console-only shim that would conceal an unresolved authoritative defect;
- GitHub pagination/incomplete-result tests;
- exact-head match and changed-head invalidation;
- exact affected-record counts;
- action-total reconciliation;
- primary `Assigned to you` and secondary `Other assigned work to oversee` reconciliation;
- Action Items routing to specialist screens without independent status or disposition state;
- incident grouping without history loss;
- candidate live-field hydration;
- preliminary term filtering;
- ISO timezone parsing and sort;
- zero/false display;
- workflow filter-aware routes;
- publication conflict and export staging;
- stable crosswalk-to-topic-page product identity and stage transition;
- exclusion of crosswalks and topic pages from issue counts, Development level, Score, and Runs;
- stable gap-obligation identity across repeat detections and generated-feed rebuilds;
- an unprompted discovered finding that becomes an authorized, validated repair;
- an unprompted finding outside delegated scope or explicitly forbidden that produces complete documentation and an exact report without mutation;
- an inconclusive finding retained with evidence, owner, and next investigation trigger;
- a quiet ordinary queue that selects and completes documented project-governance review and discovery mode instead of an empty-queue no-op;
- governance-discovery documentation for both material-findings and no-material-finding outcomes;
- aging protection that prevents a lower-severity unresolved gap from disappearing or starving indefinitely;
- exact-revision structural, provenance, authority, linkage, and validation checks for an outside contribution;
- focus retention and live announcements;
- desktop and 390-pixel responsive checks;
- automated accessibility checks; and
- performance budgets.

Add explicit regression fixtures for the July 25 review baseline:

- 110 Project items = 98 proposal/candidate portfolio + 12 non-proposal delivery items;
- 26 release blockers;
- portfolio architecture: 204 baseline → 198 after APPT consolidation → 77 after the broader approved consolidation → 81 after four later admissions;
- earned readiness: 23 baseline → 27 current, measured separately from the denominator change;
- PR #380 recommendation affecting 42 sources plus the associated formal candidate;
- PR #381 recommendation affecting 10 directives;
- 2,048 Source Checker results against 2,055 current sources;
- clean Project Integrity run plus composite source/candidate/operational exceptions;
- a failed zero-stage checked-in chain;
- an ISO timestamp containing `+00:00`;
- a preliminary record with `Trump II`;
- a recorded score of `0`, an absent score, and invalid scores below `0` and above `100`;
- an empty ordinary work queue that requires governance-review/discovery selection;
- one repeated gap detection that must retain its first-seen identity and occurrence history;
- one authorized unprompted repair, one explicitly forbidden unprompted action, and one inconclusive discovery; and
- one section move that affects multiple page records.

Treat those numbers as fixtures, not permanent production assumptions.

## Validation and closeout

1. Rebuild all generated Console data through the canonical builders.
2. Validate the generation manifest and hashes.
3. Run focused tests, the full suite, repository validation, and Project Integrity.
4. Render every screen at desktop and mobile widths.
5. Confirm no browser-console errors or warnings.
6. Verify authenticated GitHub counts and exact-head recommendations.
7. Verify that publication and public-site generated surfaces remain synchronized where implicated.
8. For every structural repair, verify the authoritative source, affected schemas, GitHub Project fields, generated feeds, Console projection, publication surfaces, and public site as applicable.
9. Record the implementation in the Change Audit Log when required by the governing audit rules.
10. Verify that every discovered work unit has the required canonical documentation, authority analysis, affected-surface accounting, validation/readback, disposition, owner, and next trigger.
11. Update the Console README and every governing or workflow document whose durable rule changed.
12. Clear `CURRENT_AUDIT.md` only after the complete closeout is documented.
13. Commit intentionally, push, open a reviewable pull request, wait for required checks, and perform the full GitHub/publication reconciliation required by ARRP workflow.

## Definition of done

The work is done only when:

- every recommendation accepted for the implementation scope is either implemented and tested or explicitly deferred with owner and reason;
- every verified project structural defect discovered during implementation is repaired at its authoritative owning layer or explicitly deferred with owner, evidence, reason, and required decision;
- no Console-only compatibility rule silently conceals a canonical classification, identity, schema, routing, authority, lifecycle, automation, monitoring, or publication defect;
- counts reconcile across Overview, Action Items, specialist screens, feeds, and authenticated GitHub state;
- Overview remains primarily an administrative, technical, and operations briefing and does not absorb detailed issue development;
- Progress is recognizably the primary detailed issue-development workspace;
- the Publication product-delivery view treats each project crosswalk and topic page as the internal and published stages of one stable topic product;
- no crosswalk or topic page is counted or classified as an issue, proposal, candidate, or evidence record;
- current state, latest run, incident, and history cannot be confused;
- non-proposal product/release work is visible in Publication without contaminating proposal progress;
- every data domain reports completeness and freshness honestly;
- Overview says `Project data and services`, separately labels data status, service status, and Codex capacity, and does not use `System currency`;
- Review Epoch scheduling remains separate from whether Console data reflects the latest authoritative state, and no generic 48-hour default is treated as update authority;
- Elim's enumerated duties, queues, detectors, and context packets are enforced as minimum required coverage rather than a ceiling on credible project-related discovery or unprompted investigation;
- a quiet ordinary queue enters documented project-governance review and discovery mode under the synchronized, Change-Audited automation design;
- every discovered finding is thoroughly documented with source revision, evidence, reasoning, impact, authority analysis, action or non-action rationale, affected surfaces, validation/readback, disposition, owner, and next action or trigger;
- authorized discovered repairs are applied and validated; out-of-scope, human-reserved, unsafe, or explicitly forbidden actions are reported without implementation or workaround; inconclusive findings remain durable obligations;
- outside contributions receive the same exact-revision gap and integrity stewardship before integration;
- every project-owner item is an actionable brief, other owners' items are available in a clearly secondary oversight view, and every Action Items entry routes to its owning specialist screen;
- Action Items holds no independent authority for status, priority, evidence, resolution, or disposition;
- every large screen is responsive and keyboard-usable;
- the client no longer eagerly loads and renders the entire 12.9 MB / 70k-node application;
- complete history and provenance are preserved; and
- all required checks and review boundaries pass.

---
