---
title: "Project Methodology"
status: active
print_levels:
  - full-technical
---

# Project Methodology

## Purpose

Maintain the project's living GitHub Project tracking surface and retained source inventory before and during substantive development, and provide the canonical audit procedure, scoring rules, Horizon Scan rules, and audit-output requirements.

GitHub Projects is the authoritative tracking surface for area, issue, lifecycle-status, milestone, roadmap, and horizon-queue fields. Retained inventory CSV files are limited to source tracking. Human-relevant audit material should be visible in two layers: each issue page should carry a compact **Proposal Scoring** summary and audit front matter, and the full audit history should live in the sibling `ISSUE-ID.audit.md` sidecar. The canonical drafting method, issue architecture, source standard, Issue Snapshot format, Proposal Survey requirement, remedy standard, and cross-reference rules are maintained in [`FRAMEWORK.md`](FRAMEWORK.md). The canonical audit rules are maintained in this file under [Audit Rules and Proposal Quality Scoring](#audit-rules-and-proposal-quality-scoring).

## Inventory Files

The authoritative project-tracking surfaces are:

- [ARRP GitHub Project](https://github.com/users/Thorncrag/projects/2) — area, issue, lifecycle-status, milestone, roadmap, workstream, and horizon-queue tracking.
- [`sources.csv`](../inventory/sources.csv) — source-tracking records.

## Inventory Rules

1. Each substantive issue should have a stable issue identifier, such as `DOJ-001`.
2. Each issue should have one primary area home.
3. Candidate and horizon issues may remain GitHub Project items until they receive a developed issue page.
4. Retired or merged issues should remain traceable in GitHub Projects, the Horizon Scan integration log, the relevant area page, an issue audit-history file, or a source record rather than disappearing silently.
5. Area issue counts should be updated in area README front matter when issues are added, retired, merged, or moved.
6. Development status should use the GitHub Project `Status` field lifecycle options.
7. Every developed proposal issue should carry audit front matter, a visible **Proposal Scoring** summary, and a sibling audit-history file.
8. GitHub Project, source inventory, and page updates should be made in the same change as the substantive project update that requires them.
9. GitHub Project fields, not labels or issue-body metadata, are authoritative for `Area`, `Workstream`, `Priority`, `Release blocker`, `Status`, `Score`, `Runs`, `Last audit`, `Next audit`, `Rebaseline status`, `Change audit needed`, `Canonical page`, and parent/sub-issue tracking.
10. Labels should be limited to issue kind or temporary triage that is not already represented by a Project field.

## Project-Update Checklist

When updating the project, check whether the change requires inventory maintenance:

1. If an area is added, renamed, retired, or materially reframed, update the GitHub Project area field/options and the relevant area README/index pages.
2. If an issue is added, renamed, promoted, retired, merged, moved, or given a new development status, update the GitHub Project item/fields and the relevant area README.
3. If proposed legislation, proposed constitutional amendment text, proposed enabling legislation, or another proposal vehicle is added, renamed, or removed, update the issue page, legislation index, and GitHub Project canonical-page/status fields as applicable.
4. If an issue is audited, promoted, paused, retired, merged, given legislation, or materially revised, update the issue-page audit front matter, the issue-page **Proposal Scoring** summary, the sibling `ISSUE-ID.audit.md` audit-history file, and the GitHub Project item or fields. Detailed fields such as score basis, rubric version, Required Electoral Environment, Development Priority, Adoption Friction, legislation path, and notes belong in the issue page and audit-history sidecar, not as separate GitHub Project columns. `Score`, `Runs`, `Last audit`, `Next audit`, `Rebaseline status`, and `Change audit needed` are GitHub Project fields because they are operational audit-control flags needed for safe resumption and release triage.
5. If the scoring template, audit schema, rubric version, or audit sidecar structure changes, run a **Change Audit** across all affected issue pages with **Proposal Scoring** sections to keep front matter, visible scoring boxes, audit sidecars, GitHub Project fields, and [`CHANGE_AUDIT_LOG.md`](CHANGE_AUDIT_LOG.md) synchronized. This prevents drift between human-facing scores and machine-readable metadata without restoring separate tracking sections that now live in the issue pages, GitHub Project, or separate logs.
6. If a candidate or source-development issue has no concrete draft vehicle, its **Proposed Legislation** section may use a single `Pending development` bullet. Do not treat that placeholder as a broken legislation link, but replace it with a linked bullet once a vehicle exists and update the Issue Snapshot vehicle, metadata, inventories, and GitHub Project fields if the issue's status band, score, run count, last audit, or next audit changes.
7. If a Horizon Scan audit is run, create or update GitHub Issues for active horizon candidates and add them to the GitHub Project horizon queue. Use [`HORIZON_SCAN_LOG.md`](HORIZON_SCAN_LOG.md) for disposition and integration history, not as the active horizon queue. Do not update issue pages, legislation, scores, or source records unless the user separately approves implementation.
8. If an external source is newly cited, removed, or used for a materially different proposition, update [`sources.csv`](../inventory/sources.csv).
9. If source review is completed, update `Reviewed?`, `Proposition Supported`, and any notes in [`sources.csv`](../inventory/sources.csv).
10. If issue counts change, update the area README front matter and any corresponding GitHub Project area metadata.
11. If a Markdown page is created, moved, promoted, retired, or repurposed, update its `print_levels` metadata under the rules in [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md#print-assignment-metadata).
12. If a roadmap, backlog, or to-do item is added or revised, update the GitHub Project issue/milestone/roadmap item; framework files should link to GitHub rather than maintaining separate task lists.
13. If a roadmap, governance, audit, release, or publication task has meaningful child tasks, use GitHub native sub-issues rather than Markdown-only checklist substitutes.

## Area and Issue Index Rules

The ordered project-area index is maintained in [`../areas/README.md`](../areas/README.md). Current status, lifecycle, workstream, milestone, and horizon-queue metadata are maintained in the [ARRP GitHub Project](https://github.com/users/Thorncrag/projects/2). Area pages and issue pages should carry stable repository links for human navigation; GitHub Project items should carry clickable canonical-page links where practical.

## Source Inventory Rules

`sources.csv` should capture distinct external sources already cited in the project. A row may be associated with an issue, area, framework file, research file, or project-level page.

Source rows may be captured before full verification. Use the `Reviewed?` field to distinguish a captured source from a source that has been checked against the proposition it is being used to support.

When a cited issue page, legislation file, or framework file is edited, refresh any affected `Project Location` line references in [`sources.csv`](../inventory/sources.csv). Exact line references are useful for rapid verification, but they can become stale after otherwise unrelated edits.

## Audit Rules and Proposal Quality Scoring

Before an issue or proposal is treated as ready for external circulation, it should undergo a quality audit assessing issue definition, legal authority, source support, proposal survey, remedy adequacy, abuse resistance, political adoption prospects, drafting clarity, and integration with the project inventory.

The audit should identify unresolved legal, factual, remedial, implementation, and adoption risks rather than treating completion of a draft as evidence of readiness.

Every developed issue should have audit front matter, a visible **Proposal Scoring** summary, and a sibling audit-history file. Current proposal-quality score, audit status, next audit need, audit-rubric version, rebaseline status, Required Electoral Environment, Development Priority, Adoption Friction, and related score-basis narrative belong on the issue page and in the audit-history sidecar. Cross-project routing, audit-control, and release-triage fields belong in the GitHub Project.

### Pre-Audit Orientation

Every audit should begin from [`FRAMEWORK.md`](FRAMEWORK.md), then proceed to this methodology file, then follow the linked governing files relevant to the audit's scope before applying the audit to an issue, proposal, GitHub Project item, inventory, horizon candidate, or export product. The auditor need not reread every project file for every audit, but must consult enough governing material to avoid applying stale rules.

At minimum:

- all audits should consult [`FRAMEWORK.md`](FRAMEWORK.md) for the project's governing structure, issue architecture, drafting method, neutrality rules, source standards, Issue Snapshot format, Proposal Survey requirements, annotation conventions, appendix catalog, cross-reference rules, and proposal-page alignment rules;
- all audits should consult this file for audit procedure, scoring rules, tier requirements, current-status checks, output requirements, and audit-preservation rules;
- remedy-type, least-complex-remedy, or remedial-adequacy audits should consult [`REMEDY_FRAMEWORK.md`](REMEDY_FRAMEWORK.md);
- print, appendix, compiled-document, PDF, DOCX, public-release, or export-placement audits should consult [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md);
- Change Audits should consult every governing project material listed in the Change Audit workflow before updating individual proposal pages; and
- audits that update human-facing or machine-readable status should consult the affected issue page, sibling audit-history file, GitHub Project item, and relevant retained source records before finalizing changes.

If a linked governing file appears inconsistent with [`FRAMEWORK.md`](FRAMEWORK.md) or this methodology file, document the inconsistency as a Change Audit issue and resolve or report it before relying on either rule for downstream scoring or page updates.

### Change Audit

A **Change Audit** is the consistency check run when the audit framework, scoring rubric, issue-page template, GitHub Project field schema, inventory schema, audit sidecar structure, other governing project rule, or a substantive developed proposal changes. It must begin with project-level consistency when the change affects governing rules or cross-project conventions, and may be targeted to a single proposal when the change is limited to that proposal's issue page, linked proposal vehicle, source basis, remedy design, implementation design, or scoring-relevant analysis. Its purpose is to prevent newer rules or substantive proposal revisions from leaving older scores, metadata, GitHub Project fields, audit histories, issue-page summaries, or proposal-to-legislation alignment silently stale.

Project-wide Change Audits should be recorded in [`CHANGE_AUDIT_LOG.md`](CHANGE_AUDIT_LOG.md). Proposal-specific Change Audits should be recorded in the affected proposal's sibling audit-history file, not duplicated in the project-wide Change Audit Log, unless the proposal-specific audit also changes a governing rule, template, schema, rubric, or cross-project convention.

When several related substantive edits or Change Audit clarifications occur in rapid succession, they may be collapsed into a single coherent change entry in the appropriate log. Consolidation is acceptable only if the entry still preserves the material changes made, the affected files or proposal, the score or rebaseline effect, unresolved findings, and the reason the edits are treated as one change set.

When a developed issue page, proposed legislation page, rule text, constitutional amendment text, or other proposal vehicle receives a substantive update that could affect legal fit, prior-proposal grounding, remedy design, implementation design, abuse resistance, drafting quality, adoption posture, source support, budgetary impact, or proposal-to-legislation alignment, the assistant should remind the user to consider a Change Audit before treating the proposal score as current. Do not run the Change Audit automatically unless the user asks, because the user may intend to make additional substantive edits before auditing. Formatting-only edits, typo fixes, link repairs, and other non-substantive maintenance do not require this reminder unless they reveal a score-affecting defect.

If a developed issue receives a new source, manifestation, institutional-anomaly framing, damage theory, underlying-weakness theory, remedy description, repair/prevention language, or proposal-vehicle change without a contemporaneous Change Audit, mark the issue as needing a targeted Change Audit. This marker is required even when the score does not change. At minimum, update the issue front matter with `change_audit_needed: true`, add a concise `change_audit_reason`, update the visible **Proposal Scoring** summary or **Next Audit** line, update the GitHub Project item if a relevant field exists, and append a no-score entry to the sibling audit-history file explaining the update and the unresolved consistency check. Candidate or source-development-only issues may use ordinary source-development notes instead of this marker unless they already have a developed proposal and score.

The targeted Change Audit should include an **Internal Remedy-Fit Audit**. It must confirm that the issue's Institutional Anomaly, Manifestations of the Failure, Resulting Damage, Underlying Weakness, Proposal Survey, Least-Complex Adequate Remedy, Repair and Prevention, proposed legislation or other proposal vehicle, and Annotation still describe the same institutional defect and that the proposed remedy still addresses the defect as reframed. If a new manifestation or source expands, narrows, or changes the issue's theory, the audit should document whether the remedy still fits, whether the issue should be narrowed, whether the manifestation belongs in another issue, whether the proposed legislation should be revised, or whether human review is required before further score reliance.

The current audit rubric version is **2026-06-27.2**.

Rubric version log:

| Version | Change | Rebaseline effect |
| --- | --- | --- |
| `2026-06-26.1` | First explicit rubric-version and rebaseline-tracking system. | Marked prior developed scores for rebaseline and fixed-status zero scores as current fixed-status values. |
| `2026-06-26.2` | Added Adoption Friction Score as a companion metric outside the 100-point Proposal Quality Score. | Soft rebaseline for otherwise-current developed proposals; hard rebaseline remains for developed proposals already awaiting formula rebaseline. |
| `2026-06-27.1` | Added required T1 Enactment Pathway Check, including Required Electoral Environment, Pathway Viability, Development Priority, and Pathway Adjustment. The check is evidence-bound and feeds Adoption and Implementation scoring rather than creating a standalone score. | Hard rebaseline for developed proposals because the new required check can materially change Adoption and Implementation component credit. Fixed-status zero scores remain current fixed-status values. |
| `2026-06-27.2` | Clarified that legal availability is not adoption viability where a proposal depends on voluntary self-limitation by the same institutional actor whose discretion the proposal constrains. Added `conditional-current` Pathway Viability value and required Adoption Score and Adoption Friction treatment for institutionally adverse adopters. | Hard rebaseline for developed proposals whose pathway depends on discretionary adoption by an institution or officer materially adverse to the reform, especially current-law or internal-policy vehicles. No rebaseline is required for proposals whose adoption path does not depend on that condition. |

Every proposal-quality score must be tied to the audit rubric version used to produce it. This prevents older scores from appearing directly comparable to newer scores after the project changes scoring weights, required filters, current-status checks, source rules, or audit-output requirements.

Use these fields in issue-page front matter for developed issues when the page is next audited or materially revised:

```yaml
audit_rubric_version: 2026-06-27.1
audit_rebaseline_status: current
change_audit_needed: false
change_audit_reason: null
adoption_friction_score: null
adoption_friction_band: unassessed
required_electoral_environment: unassessed
pathway_viability: unassessed
development_priority: unassessed
pathway_adjustment: unassessed
```

Use these fields in issue front matter and visible **Proposal Scoring** summaries when applicable:

- `Audit Rubric Version`
- `Rebaseline Status`
- `Rebaseline Notes`
- `Adoption Friction Score`
- `Adoption Friction Band`
- `Adoption Friction Notes`
- `Required Electoral Environment`
- `Pathway Viability`
- `Development Priority`
- `Pathway Adjustment`
- `Enactment Pathway Notes`

Rebaseline statuses:

| Status | Meaning |
| --- | --- |
| `current` | The score was calculated under the current rubric version and may be compared to other current scores. |
| `current-fixed-status` | The issue has a fixed non-formula status, usually candidate, paused, retired, merged, pending controlling finding, or reliably moot; the zero score is current until the status changes. |
| `soft-rebaseline-needed` | The rubric changed in a way that adds useful context or a new non-score field, but the existing score remains usable with a caveat until the next audit. |
| `hard-rebaseline-needed` | The rubric changed in a way that could materially change the score; treat the existing score as provisional until the next substantive audit recalculates it. |
| `rebaseline-complete` | A rebaseline audit was completed; this status should normally be converted to `current` after the GitHub Project fields and issue metadata are updated. |

Map issue-page rebaseline metadata to the GitHub Project `Rebaseline status` field as follows:

| Issue-page value | GitHub Project value |
| --- | --- |
| `current` | `Current` |
| `current-fixed-status` | `Current fixed status` |
| `soft-rebaseline-needed` | `Soft rebaseline needed` |
| `hard-rebaseline-needed` | `Hard rebaseline needed` |
| `rebaseline-complete` | `Rebaseline complete` |
| Not applicable to the item | `Not applicable` |
| Unknown or not yet reviewed | `Unknown` |

Map issue-page `change_audit_needed` metadata to the GitHub Project `Change audit needed` field as follows: `false` maps to `No`; `true` maps to `Yes`; unresolved intake or unclear cases map to `Pending review`; blocked audit-resolution cases map to `Blocked`.

When the audit framework or scoring system changes, classify the change before applying it:

| Change type | Required action |
| --- | --- |
| Wording clarification, formatting, or examples only | No rebaseline required. |
| New metadata, GitHub Project field, or non-score tracking category | Soft rebaseline unless the change exposes a score-affecting defect. |
| New required check, source rule, penalty, scoring component, component weight, baseline rule, or current-status gate | Hard rebaseline for already scored developed proposals unless the issue was already audited under the new rule. |
| Change to fixed zero-score categories | Rebaseline affected candidate, retired, merged, pending-finding, or moot rows. |

Change Audit workflow:

1. Assign a new rubric version before changing scoring rules or required audit filters.
2. Record governing-rule changes in this section and update [`CHANGE_AUDIT_LOG.md`](CHANGE_AUDIT_LOG.md). For proposal-specific Change Audits that do not alter governing rules or cross-project conventions, record the audit in the affected issue's sibling audit-history file and update the issue page and GitHub Project fields where applicable, but do not add a duplicative project-wide Change Audit Log entry.
3. Conduct a systematic internal-consistency review of governing project materials before applying the change to any individual proposal. This review should be deep enough to catch the kinds of drift that arise from repeated structural edits rather than only obvious formatting errors. The following checks are a required floor, not an exhaustive ceiling; the auditor should follow any additional inconsistency, ambiguity, broken reference, stale convention, or implementation defect discovered during the review. At minimum, check [`FRAMEWORK.md`](FRAMEWORK.md), this methodology file, [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md), [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md), retained source-inventory headers, issue-page templates as reflected in developed pages, audit sidecar conventions, and Horizon Scan rules for:
   - misplaced ownership between Framework, Methodology, print assembly, GitHub Project, source inventory, issue pages, legislation pages, and Horizon Scan;
   - duplicated rules, conflicting instructions, obsolete rubric versions, stale terminology, inconsistent section names, and dead conventions;
   - broken or stale internal links, heading anchors, file paths, issue IDs, legislation paths, GitHub Project canonical-page links, audit-history links, and cross-references;
   - metadata/front-matter drift, including `issue_id`, `area_id`, `status`, `remedy_type`, `legislative_proposal`, `constitutional_proposal`, `audit_*` fields, `print_levels`, and audit-history paths;
   - tracking drift between GitHub Project items/fields, `sources.csv`, area README files, issue pages, legislation pages, and Horizon Scan;
   - language-rule drift, including neutrality conventions, title conventions, President/public-actor references, Project 2025 framing, and unsupported partisan or advocacy wording;
   - source-rule drift, including missing nearby citations, uncaptured cited sources, stale source line references, overconfident source characterization, and source claims that no longer match the page text;
   - proposal-to-legislation alignment risks that should be documented and reported for human review rather than automatically corrected; and
   - rule changes, inconsistencies, or factual/legal uncertainties that require human review before correction.
4. If the consistency review finds a governing-rule defect, correct the governing file that properly owns the rule when the correction is mechanical. If the defect requires a substantive judgment, document the discrepancy as an unresolved Change Audit finding and report it to the user before updating downstream pages.
5. Mark affected already-audited proposals as `soft-rebaseline-needed` or `hard-rebaseline-needed` in issue front matter, the visible **Proposal Scoring** summary, and the GitHub Project `Rebaseline status` field.
6. Preserve old scores, but treat non-current scores as provisional in summaries, comparisons, and prioritization.
7. During the next targeted Change Audit, T2, T3, or T4 audit of an affected developed proposal, resolve any `change_audit_needed` marker by performing the Internal Remedy-Fit Audit and any other affected checks. If the remedy, source basis, and scoring remain valid, clear `change_audit_needed`, update the issue-page metadata, update the issue-page **Proposal Scoring** summary, append the full audit entry to the sibling `ISSUE-ID.audit.md` file, and update GitHub Project fields where applicable. If the check changes the score, recalculate under the current rubric and set the rebaseline status to `current`. In GitHub Project fields, update `Change audit needed` to `No` and `Rebaseline status` to `Current` once the relevant checks are resolved.
8. Do not compare scores across rubric versions without noting the mismatch.
9. Do not rerun every proposal immediately unless the user asks; use the rebaseline status to queue the work responsibly.

Formatting-only or template-only changes may require a Change Audit even when they do not require score rebaseline. In that case, update affected pages, metadata, sidecars, GitHub Project fields, and source records as needed, but leave proposal-quality scores unchanged unless the change reveals a substantive scoring defect.

### Audit Workflow

Each developed proposal should be audited through the following sequence. The sequence may be run as a full review or as a targeted review, but the audit record should identify which parts were completed.

1. **Issue-identification audit.** Confirm that the issue identifies a distinct institutional weakness, has the correct primary area home, is not duplicative of another issue, and is framed as a structural defect rather than as a narrative about one person or episode.
2. **Framework-compliance audit.** Confirm that the issue performs the required analytical functions: Issue Snapshot, Institutional Anomaly, Manifestation of the Failure with titled instances or categories, Resulting Damage, Underlying Weakness, Proposal Survey, Least-Complex Adequate Remedy, Repair and Prevention, Proposed Legislation where applicable, Proposed Constitutional Amendment and Proposed Enabling Legislation where applicable, Relationship to Adjacent Proposals where overlap would otherwise cause confusion, and Annotation.
3. **Enactment-pathway audit.** Confirm the minimum electoral environment required for the proposal to become seriously actionable, whether the proposal can be narrowed or staged to fit a more realistic environment, and whether further development is immediate, active, conditional, reserve, or deprioritized. This check begins at T1 and must be evidence-bound rather than speculative.
4. **Evidence and citation audit.** Confirm that factual, legal, and causal claims are supported by nearby citations, that real-world examples link to source material, and that all cited external sources are captured in [`sources.csv`](../inventory/sources.csv).
5. **Legal-support audit.** Confirm that the proposal accurately identifies the constitutional, statutory, regulatory, procedural, or institutional authority on which it depends and discloses material uncertainty, doctrine, limits, or litigation risk.
6. **Existing-law and prior-proposal audit.** Confirm that the proposal checks existing law first, prefers amendment of existing vehicles where adequate, searches direct and functional analogues, and weighs prior proposals according to enacted use, institutional review, sponsorship, co-sponsorship, bipartisan support, and legislative progress.
7. **Remedy-adequacy audit.** Confirm that the proposed remedy is the least-complex adequate remedy, addresses both repair and prevention where relevant, identifies why simpler options are insufficient, and preserves more complex fallback options where necessary.
8. **Internal remedy-fit audit.** Confirm that the issue's anomaly, manifestations, resulting damage, underlying weakness, least-complex adequate remedy, repair/prevention language, proposed legislation or other vehicle, and scoring annotations still address the same institutional defect. If recent source-development or framing updates create a mismatch, document the mismatch and do not treat the proposal score as current until the user approves narrowing, reframing, moving the manifestation, or revising the remedy.
9. **Implementation and enforcement audit.** Confirm that the remedy can be administered, enforced, funded, reviewed, and updated without relying on the same failed institution or norm that created the problem.
10. **Budgetary-impact audit.** Confirm that the issue page and proposal page contain the required preliminary **Budgetary Impact Statement** and that any fiscal characterization is appropriately sourced, caveated, tier-scaled, and checked against available budget or appropriations analogues.
11. **Abuse-resistance audit.** Confirm that the remedy includes safeguards against capture, selective enforcement, evasion, delay, retaliation, pretextual use, or partisan conversion.
12. **Drafting-quality audit.** Confirm that proposed legislation or rules use the appropriate legal vehicle, maintain legislative drafting conventions, define operative terms, assign responsible actors, specify procedures, and include remedies, deadlines, reporting, review, and severability where appropriate.
13. **Proposal-to-legislation consistency audit.** Where an issue page links to proposed legislation, proposed constitutional amendment text, proposed enabling legislation, or another proposal vehicle, compare the Issue Snapshot vehicle, Least-Complex Adequate Remedy, Repair and Prevention section, Proposed Legislation or amendment/enabling sections, Annotation, and scoring/audit summary against the linked bill, rule, constitutional amendment, or procedural text. Confirm that the issue page still accurately describes the operative vehicle, covered actors, legal hook, remedy type, enforcement mechanism, deadlines, responsible institutions, scope limits, and any material drafting notes. If the audit discovers a substantive discrepancy between the issue page and proposed legislation, document the mismatch as an unresolved finding, report it to the user, and do not update either page or related inventories to resolve the discrepancy unless the user separately approves the correction.
14. **Hallucination-resistance and verification audit.** Confirm that the issue contains no invented, uncited, stale, unverifiable, or overconfident claims, and that every material factual, legal, polling, legislative-history, scholarly, real-world-example, or fiscal-impact assertion is traceable to reliable source material.
15. **Judicial and scholarly scrutiny audit.** Confirm that the proposal has been tested against likely Supreme Court, relevant lower-court, and serious legal-scholar objections, and that the issue records deeply researched recommendations for increasing the likelihood that the proposal would be upheld.
16. **Argument and cogency audit.** Confirm that the problem, weakness, damage, remedy, and implementation logic follow from each other without hidden premises, overclaiming, unsupported causation, or remedy mismatch.
17. **Support and adoption audit.** Confirm that the issue can be explained to likely supporters, skeptics, lawmakers, staff, experts, and the public in terms of institutional repair rather than partisan advantage.
18. **Political-language and coalition-appeal audit.** Confirm that the proposal remains candid about misconduct while using institution-focused language and estimating likely support from bipartisan, independent, Democratic, and Republican audiences.
19. **Project-integration audit.** Confirm that internal links, legislation links, issue status, remedy type, source inventory, audit metadata, audit-history sidecar, GitHub Project canonical-page links, area page, and compiled-document placement remain consistent.

### Formatting Preflight

Every issue-quality audit tier must include a brief formatting-consistency preflight before substantive scoring or revision. The preflight is meant to catch template drift, not to become a separate deep audit. It should be scaled to the selected tier and should not materially expand the audit unless it reveals a substantive defect.

At minimum, the preflight should check:

1. required front-matter fields exist and match the visible issue-page status;
2. the **Issue Snapshot** uses the current blockquote and inline `<br />` format;
3. **Manifestation of the Failure** uses concise titled examples or categories;
4. **Proposed Legislation**, **Proposed Constitutional Amendment**, or **Proposed Enabling Legislation** uses Markdown bullet links or an approved `Pending development` placeholder;
5. the **Budgetary Impact Statement** has the substantive statement first and the italicized `Note:` disclaimer below it;
6. **Proposal Scoring** groups all scores and viability indicators at the top, uses the coalition-estimate indentation format when estimates appear, separates audit metadata with an em dash divider, and links the full audit-history sidecar;
7. scoring annotations mirror visible scoring labels where practical, including **Quality Score**, **Adoption Score**, **Coalition Support Estimates**, **External Review Status**, **Adoption Friction**, **Required Electoral Environment**, and **Development Priority** when those fields appear; and
8. the issue page, sibling audit-history file, and GitHub Project agree on the fields each surface owns: GitHub should match lifecycle, audit-control, release-triage, and routing fields, while detailed rubric, pathway, development-priority, adoption-friction, legislation-path, and score-basis data should remain on the issue page and audit-history sidecar.

Tier scaling:

- **T0/T1:** check the most recent audit entry, visible front matter, Issue Snapshot, Budgetary Impact Statement, Proposal Scoring box, and audit-history link.
- **T2:** also check GitHub Project field alignment, proposal-to-legislation link shape, annotation scoring labels, and whether prior format findings were carried forward.
- **T3/T4:** also check the audit-history sidecar, source-inventory references affected by visible citations, legislation-page budget/source-note structure, and any template changes adopted since the prior audit.

Formatting preflight corrections may be made during the audit when mechanical. If the preflight reveals a substantive discrepancy between issue analysis, scoring, and proposed legislation, document and report it under the proposal-to-legislation consistency rule rather than silently correcting it without user review.

### Audit Resource Tiers

Audits should be scoped to a stated resource tier before work begins. A smaller tier is not a failed larger audit; it is a deliberately budgeted review. The audit record should identify the tier used, what was completed, what was skipped, and what the next higher tier should examine.

Issue-quality audits should be run on exactly one issue at a time. Before starting, identify the target issue by issue ID and page path. If the request could refer to more than one issue, or if the issue ID is missing or unclear, ask the user to identify the issue before beginning the audit. The project-wide Horizon Scan audit is the only standing exception because its purpose is to identify possible new or changed issues across the project; it must not be used as a substitute for scoring or revising an individual issue.

Before starting a new audit for an issue, check the most recent audit record for unresolved blocking findings, skipped prerequisites, source-development tasks, or user-input needs that must be resolved before further audit work can proceed. If blocking unresolved items remain from the last audit, cancel the new audit request, notify the user, and ask whether to resolve the existing items, explicitly override the block, or revise the audit scope. Do not begin a new audit until the user gives direction. Ordinary next-audit recommendations do not block a new audit when the requested audit is meant to address them.

If the user requests an audit without specifying a tier, ask which tier to run rather than guessing. The default recommendation should be the lowest level that appears useful, usually **T0: Triage scan** for a new or ambiguous request. Do not silently escalate to a higher tier.

Before running a higher-tier audit, confirm that the immediately lower tier has already been completed for the issue and remains reasonably current. If the lower tier has not been completed, ask the user whether to run the lower tier first or explicitly skip it. If the user confirms skipping a lower tier, record that skipped prerequisite in the audit output.

For an issue placed on pause, fixed at `0`, or assigned `current-fixed-status` because it is awaiting a judicial merits ruling, controlling external finding, completed factual predicate, reliable mootness determination, retirement, merger, or issue-admission decision, the next audit should normally be limited to a **paused-status predicate check**. That check should verify whether the predicate that justified the pause has changed, using current reliable sources appropriate to the issue. Unless the predicate has changed or the user expressly asks for exploratory development despite the pause, do not perform substantive proposal development, formula scoring, prior-proposal surveys, budget development, adoption analysis, drafting revisions, or higher-tier publication work. If the predicate remains unchanged, update the issue page, audit-history file, GitHub Project fields, inventories, and sources only as needed to document the status check and preserve the fixed-zero status. If the predicate has changed, document the change, identify the next ordinary audit tier, and update status before resuming substantive work.

| Tier | Estimated time | Purpose | Expected output |
| --- | ---: | --- | --- |
| **T0: Triage scan** | 5 minutes or less | Catch obvious blockers before deeper work. | One-paragraph status, obvious defects, obvious mootness or material-reframing flags, obvious pending-judicial-opinion flags, and whether deeper audit is needed. |
| **T1: Framework check** | 30 minutes or less | Check internal project consistency, visible framework compliance, basic current-status risk, and initial enactment-pathway fit. | Short checklist covering structure, links, metadata, legislation link, issue status, remedy type, source-inventory presence, Budgetary Impact Statement presence and basic classification, obvious unsupported claims, initial Required Electoral Environment, Pathway Viability, Development Priority, Pathway Adjustment, a basic mootness or material-reframing check, and an obvious pending-judicial-opinion check. |
| **T2: Development audit** | 2 hours or less | Verify the proposal enough to guide revision and provisional scoring. | Component-level score estimate, key source checks, current public-source refresh, mootness or material-reframing assessment, pending-judicial-opinion vulnerability assessment, legal-fit notes, remedy-fit notes, provisional budget or implementation-burden analysis where material, major risks, and next audit needs. |
| **T3: Readiness audit** | 6 hours or less | Test whether a proposal is close to external circulation. | Reproducible score, source-refresh log, verified claims, unresolved claims, mootness or material-reframing assessment, pending-judicial-opinion vulnerability assessment, legal and judicial-scrutiny risks, direct and functional analogue review, source-backed fiscal or burden claims where asserted, adoption/support notes, international score or `N/A`, and recommended revisions. |
| **T4: Publication-ready audit** | 18 hours or less | Resolve every publication concern that can reasonably be resolved through deep public-source research before external circulation. | Publication-readiness memo, cumulative T1-T3 criteria confirmation, final score recommendation, deep source-refresh log, verified and unresolved claims table, mootness and material-reframing determination, pending-judicial-opinion vulnerability assessment, legal-durability analysis, direct and functional prior-proposal comparison, adoption and opposition analysis, source-backed fiscal or burden review including available budget analogues where material, international score or `N/A`, drafting recommendations, and expert-review needs. |

Every audit tier must include a current-status check for mootness and material reframing, scaled to the tier's time budget. The auditor should check whether recent decisions, pending judicial opinions, pending merits cases, certiorari grants, emergency or stay applications, lower-court injunctions, legal opinions, enacted laws, pending or completed legislation, regulations, agency actions, court orders, factual developments, elections, appointments, repeals, superseding events, implementation experience, or other current developments have made the proposal unnecessary, partially obsolete, legally impossible, materially stronger, materially weaker, or structurally different from the issue as drafted. If the check identifies a serious mootness, pending-judicial-vulnerability, or reframing concern, document it prominently in the audit record, update the issue page when source support permits, and adjust the Proposal Quality Score. If reliable current sources show that the standalone proposal has become completely moot, set the score to `0` while that condition remains true.

Every audit tier must also include a **pending judicial vulnerability check**, scaled to the tier's time budget. The check should identify whether the Supreme Court, a federal court of appeals, a relevant district court, a state supreme court, or another controlling tribunal has a pending case, argued case, granted petition, emergency application, stayed order, remand, or imminent merits decision that could materially affect the proposal's constitutional footing, statutory authority, remedy design, enforcement mechanism, standing theory, scope, urgency, or issue-admission result. This includes cases related to unitary executive theory, removal power, appointments, presidential control of agencies, administrative-state limits, spending conditions, election rules, federalism, speech, equal protection, due process, immunity, judicial enforcement, and other doctrines implicated by the issue under audit.

If the pending judicial vulnerability check cannot be completed at the selected tier, mark it `Unresolved` or `Verification pending` and assign no favorable current-status or legal-fit credit for that component. If a pending case is likely to control the remedy or issue-admission result, the audit should recommend pausing, narrowing, or expressly conditioning the proposal until the decision issues. If a pending case merely creates legal risk without controlling the proposal, the audit should document the risk and identify drafting adjustments that would remain valid under plausible outcomes.

Tier times are planning estimates rather than hard caps. If an audit exceeds the estimate by a reasonable degree and is close to a responsible stopping point, the auditor may finish the current audit unit. The audit should not exceed 150% of the selected tier's estimated time without explicit user approval.

Tier estimates are not minimums. If a responsible audit can be completed in less than the selected tier's estimated time, finish early rather than filling the allotted time. Record that the audit finished under estimate and use that result to calibrate future audit budgeting for comparable issues.

The **T4: Publication-ready audit** should be run when the user requests T4, publication-ready review, or an equivalent deep audit. It no longer requires a separate confirmation step merely because it is T4. Before starting, state the expected time estimate and likely scope, and note that the audit may still identify issues requiring attorney, legislative-counsel, subject-matter expert, or stakeholder review.

A T4 audit is cumulative. Before undertaking publication-ready analysis, it must confirm that the material criteria from T1, T2, and T3 have been satisfied, carried forward as unresolved, or intentionally scoped into the T4 work. This cumulative check should include framework compliance, formatting preflight, metadata/GitHub Project/inventory alignment, current-status and mootness review, pending-judicial vulnerability, existing-law and prior-proposal review, functional analogues, budgetary-impact treatment, proposal-to-legislation alignment, source verification posture, adoption-pathway posture, and unresolved prior-audit findings. If a lower-tier criterion remains unresolved, the T4 audit should either resolve it, document why it cannot be resolved within T4, or treat it as a publication blocker.

A T4 audit should address every reasonably researchable publication concern, including source verification, current-law status, prior-proposal history, legislative drafting vulnerabilities, constitutional and administrative-law risks, judicial-scrutiny concerns, implementation feasibility, abuse resistance, adoption strategy, opposition arguments, public-support evidence, international implications where material, and consistency with the project's framework and inventories. It should not claim to replace professional legal advice, legislative counsel, empirical polling, fiscal scoring, or stakeholder validation.

Budgetary-impact review is tier-scaled. T1 confirms that the required **Budgetary Impact Statement** exists and uses a permissible preliminary classification. T2 develops provisional funding, workload, or implementation-burden analysis where materially relevant. T3 and T4 source-check any fiscal or burden claims that the issue or proposal affirmatively makes and search for budget or appropriations analogues when the proposal requires funding. Do not include a dollar estimate unless it is tied to a cited government source, historical appropriation, authorization of appropriations, CBO score, agency budget material, audited program cost, or comparable source-backed basis. The substantive classification should appear first, followed by the italicized project disclaimer note. Never describe ARRP's budgetary statement as an official CBO, OMB, agency, or legislative-counsel score.

If the selected tier cannot responsibly complete a required check within the estimate plus reasonable overage, skip that portion, mark it unresolved, assign no favorable credit for it, and identify it as work for the next tier. Do not expand beyond the selected tier unless the user asks for a deeper audit.

The selected resource tier affects audit scope and confidence, not the weighting of the scoring formula. Do not give a proposal extra credit because it was reviewed under a higher tier, and do not penalize a proposal merely because the user selected a lower tier. Apply the same component weights at every tier. Components not actually reviewed or supported within the selected tier should be marked unresolved and receive no favorable credit until reviewed.

The auditor should not allow any single audit area, source dispute, legal question, factual cluster, or research thread to consume the whole tier estimate. Allocate time across the major audit areas, use conservative scoring for unresolved portions, and move unresolved clusters into the next-audit list rather than continuing indefinitely.

On the first audit run for an issue, the auditor should do what can reasonably be accomplished within the selected target tier. If calibration requires more time, the auditor may use reasonable overage up to 150% of the selected tier's estimated time. Moving beyond that ceiling, including spillover into the next tier's full estimate, requires explicit user approval. T4 should not be reached by spillover from a lower tier unless the user requested T4, publication-ready review, or an equivalent deep audit.

Future audits should use prior audit results to adjust scope within the selected timeframe. If prior work already verified a component and the underlying sources have not changed, spend less time there and use the saved time on unresolved or changed components. If prior work showed an area is unusually complex, timebox that area earlier and document the follow-up need instead of allowing it to crowd out the rest of the audit.

Successive audits should be improvement-targeted. After the first audit, the auditor should identify the unresolved components, penalties, or source gaps most likely to raise the Proposal Quality Score within the selected tier and target work there first. The goal is to improve the proposal's actual quality, reliability, and adoption readiness, not merely to repeat completed checks. A score should rise only when the audit actually resolves findings, verifies support, improves legal fit, strengthens drafting, reduces risk, or otherwise satisfies the scoring rules.

### Horizon Scan Audit

The **Horizon Scan audit** is a special project-wide audit flavor for identifying new, emerging, or newly salient issues of concern within the project's goals, including threats to democracy, rule-of-law failure, personalist capture, institutional damage, evasion of checks and balances, or comparable structural risks. It is a discovery and recommendation workflow, not an issue-quality scoring tier.

A Horizon Scan audit should:

1. perform a current-source discovery pass using recent reliable public sources, including current news, official records, court activity, legislation, agency action, government reports, public legal-research sources, watchdog materials, expert commentary, and other relevant sources;
2. identify possible new concerns, emerging manifestations, or changed factual or legal conditions that may matter to the project;
3. cross-check each concern against existing areas, issue pages, proposals, proposed legislation, source-development notes, active GitHub horizon issues, GitHub Project fields, and the Horizon Scan Log;
4. apply the ordinary Issue-Admission Test rather than bypassing it;
5. determine whether the concern is substantially duplicative, a manifestation of an existing issue, a reason to expand or amend an existing issue, a reason to reformulate existing proposed legislation, a candidate for a new standalone issue, or outside current ARRP scope;
6. make an explicit new-issue or existing-issue recommendation for each finding, stating whether to create a new issue, merge into an existing issue, expand or amend an existing issue, retain only as source development, or decline as duplicative or out of scope;
7. recommend whether to expand, adapt, amend, merge, cross-reference, source-develop, or decline the concern; and
8. document sources, uncertainty, duplicate checks, and the basis for each recommendation.

Project 2025 crossover analysis should treat Project 2025 as both an implementation-tracking source and a weakness-discovery source. A Project 2025 initiative does not need to have been enacted, attempted, litigated, or adopted to remain relevant to ARRP. If the initiative identifies a legal, statutory, administrative, procedural, personnel, funding, records, enforcement, or institutional vehicle that could be used for personalist capture, retaliation, civil-rights erosion, factual suppression, congressional evasion, or other structural abuse, the audit should still evaluate whether ARRP should cure that vulnerability. Current implementation status affects urgency, source confidence, and manifestation evidence; it should not by itself be used to dismiss the weakness or mark it out of scope.

Project 2025 source verification should follow a strict source hierarchy. First, prefer official Heritage-controlled sources when available: Heritage Foundation pages, `project2025.org` pages, `mandateforleadership.org`, and official Project 2025 or Heritage publications. Second, use stable mirrors such as DocumentCloud only to locate text, preserve access, or identify search terms, and record both the official source and the mirror used for retrieval. Third, use the local fallback copy at [`../source-development/project-2025-mandate-for-leadership-2023-documentcloud-backup.pdf`](../source-development/project-2025-mandate-for-leadership-2023-documentcloud-backup.pdf) only if official sources and stable online mirrors become unavailable, changed, or insufficient for the needed text. News summaries and advocacy summaries may identify leads or public salience but should not replace the official source, stable mirror, or local fallback in the citation record.

A Horizon Scan audit should not directly create new issue pages, modify existing issue pages, revise legislation, change scores, update inventories, or change source records unless the user separately approves implementation after reviewing the scan. Its active output should be captured in GitHub Issues and the GitHub Project horizon queue, with a concise and easily readable listing of each flagged concern and recommendation. [`HORIZON_SCAN_LOG.md`](HORIZON_SCAN_LOG.md) should be updated when a candidate is admitted, merged, deferred, retired, or otherwise adjudicated. If the scan identifies urgent or high-confidence concerns, present them prominently to the user before implementation work begins.

Each Horizon Scan finding should receive a stable **Horizon ID** in the form `HOR-###`, assigned sequentially in the cumulative Horizon Scan list. The Horizon ID is a temporary intake reference, not a formal issue ID. If a finding is later developed into a proposal, the new issue should receive the ordinary area-specific issue ID, and the Horizon ID should remain in the Horizon Integration Log as the intake reference.

Each Horizon Scan list update should normally include:

1. Horizon ID;
2. scan date and scope;
3. source categories checked;
4. search terms or discovery routes used where practical;
5. concise list of flagged concerns;
6. duplicate or overlap check against existing issues and legislation;
7. issue-admission result;
8. explicit new-issue or existing-issue recommendation;
9. recommended disposition;
10. suggested existing issue or area link;
11. source links or source-development needs;
12. confidence level and unresolved questions; and
13. recommended next action.

### Horizon Candidate Adjudication Workflow

When the user asks to address, review, assess, adjudicate, ingest, merge, admit, or retire a specific `HOR-###` candidate, use this workflow unless the user gives narrower instructions. A Horizon candidate adjudication is different from running a new Horizon Scan: it decides what to do with an already identified intake item.

1. **Locate the candidate.** Find the `HOR-###` GitHub Issue for active horizon candidates, or find the `HOR-###` row in [`HORIZON_SCAN_LOG.md`](HORIZON_SCAN_LOG.md) if the candidate has already been adjudicated.
2. **Verify the factual premise.** Check the cited sources and, where the matter is current or source-sensitive, refresh with reliable current public sources. Prefer primary materials when the claim depends on a court order, statute, regulation, bill, executive action, agency action, official vote, or formal record.
3. **Cross-check existing project coverage.** Search existing areas, issue pages, proposed legislation, source-development notes, inventories, and GitHub Project items/fields for overlap. Identify the best existing home if the concern is a manifestation, source-development lead, or expansion of an existing issue.
4. **Apply the issue-admission test.** Ask whether the candidate identifies a distinct institutional weakness requiring separate diagnosis or remedial analysis, rather than only a disliked policy outcome, ordinary political bargaining, a single unresolved episode, or a manifestation already covered elsewhere.
5. **Test ripeness and outcome status.** Do not admit a candidate merely because the event is troubling. Check whether the relevant event has matured enough to show a durable institutional defect, legal gap, repeated pattern, completed harm, controlling ruling, official action, or remedy need. If the outcome is still unfolding, consider retirement or source-development retention with a clear revisit trigger.
6. **Test neutrality and overcorrection risk.** Ask whether creating a remedy would restructure institutions to force a preferred political result rather than to repair a generalizable institutional weakness. If the same mechanism would be concerning when used by an opposing faction, that supports admission; if not, retire or narrow the candidate.
7. **Make a disposition recommendation.** Present the user with a concise recommendation: admit as a new issue, merge into an existing issue, expand or amend an existing issue, retain as source development only, retire without admission, or reject as outside scope. Include the best counter-argument if the recommendation is not obvious.
8. **Wait for user approval before implementation.** Do not create, merge, retire, or update issue records from an adjudication recommendation until the user agrees or gives direct implementation instructions.
9. **Implement the approved disposition.** If admitted as a new issue, assign the next stable area-specific issue ID, update the area page and `issue_count`, and update the GitHub Project item/fields, [`sources.csv`](../inventory/sources.csv), and [`HORIZON_SCAN_LOG.md`](HORIZON_SCAN_LOG.md). If merged or retained as source development, update the relevant area or issue page, source inventory, GitHub Project item, and Horizon Scan Log. If retired, close or update the active GitHub horizon issue and add an Integration Log row preserving the static `HOR-###` ID, original concern, rationale, and revisit trigger.
10. **Maintain the Horizon Scan state.** Active horizon candidates should live as GitHub Issues and GitHub Project items. Adjudicated candidates should appear in the Horizon Scan Log.
11. **Preserve source traceability.** Add or update [`sources.csv`](../inventory/sources.csv) rows for external sources relied on in the adjudication or implementation, even when the candidate is retired.
12. **Validate and preserve.** Run lightweight formatting and inventory checks appropriate to the files changed. Commit and push the adjudication update when repository access is available, unless the user has asked not to commit.

### Audit Autonomy and Unknowns

Audits should be conducted with the assumption that the user wants as few questions as possible. The auditor should attempt to resolve uncertainties through the project record, current-source refresh, primary-source checks, reasonable inference from documented framework rules, and conservative scoring before asking the user.

If an unknown cannot be resolved without user input, do not block the entire audit. Instead:

1. skip only the unresolved portion of the audit;
2. mark the skipped portion as `Unresolved`, `Source needed`, `Verification pending`, or `User input needed`;
3. record why the issue could not be resolved;
4. record what source, fact, preference, or decision is needed;
5. continue and complete every other audit portion that can be handled responsibly; and
6. notify the user immediately and concisely that the portion was skipped and what is needed to complete it.

When uncertainty affects scoring, assign no favorable credit for the unresolved portion, apply any required penalty, and identify the next audit need. Do not ask the user to resolve matters that can be answered through reliable sources or the project's existing framework.

When a defect can be corrected without user input, correct it rather than only noting it. Examples include broken links, missing internal links, stale source rows or GitHub Project fields, missing source-inventory capture, obvious citation-placement defects, metadata inconsistencies, formatting defects, issue-status inconsistencies, and framework-compliance gaps that can be fixed from the existing record. Do not make substantive policy choices, legal judgments, or factual claims that require unresolved source support; mark those unresolved and notify the user.

### Audit Preservation and GitHub Storage

After an audit is completed, or if an audit is interrupted after changes have been made, preserve the work promptly. Where the repository and remote are available, create the necessary non-interactive commit or commits and push them to the configured GitHub remote without asking the user additional process questions, unless approval is required by the working environment or by this method.

If local validation, formatting, pre-commit hooks, or optional checks cannot be completed in the interruption context, they may be bypassed solely to preserve audit work. Record any skipped local check in the audit output or final note. This preservation rule does not permit bypassing source-verification requirements, citation requirements, scoring rules, unresolved-claim treatment, T4 scope warnings, the 150% audit-overage rule, or any other substantive audit safeguard.

If the push cannot be completed, preserve a local commit where possible, record the failure, and notify the user immediately.

### Audit Output

Audits are corrective workflows, not documentation-only reviews. When an audit identifies a defect that can be fixed within the selected tier, within the project's framework, and without requiring unresolved user judgment, the auditor should make the correction as part of the audit. The audit record should distinguish issues fixed during the audit from issues left unresolved for later work.

Human-relevant audit results should be visible without making issue pages unwieldy. GitHub Project fields are for tracking, filtering, triage, and machine-readable maintenance; they are not a substitute for human-facing disclosure. The retained CSV inventory is limited to source tracking. Each issue page should contain a succinct but usable **Proposal Scoring** section with the at-a-glance proposal-quality score, Adoption Score when separately reported, Coalition Support Estimates when assessed, Required Electoral Environment, Development Priority, External Review Status when assessed, Adoption Friction, and any other companion score or viability indicator grouped at the top, followed by an em dash divider, then audit status, last audit, rubric version, rebaseline status, next audit need, and a visible link to the full audit-history page. When an Adoption Score is displayed, it should include the consistent descriptor in parentheses after the score, for example: `5 / 12 (Limited Adoption Basis)`. If the compact scoring box includes Coalition Support Estimates, put the label on its own line, then list each audience estimate on indented lines using inline `<br />` breaks and `&nbsp;` spacing. Keep the compact box free of evidentiary caveats when those caveats are explained in the matching annotation segment. If visible scores or descriptors require explanation, place that explanation in annotation segments after any **Budgetary Impact** annotation segment, using labels that mirror the scoring box where practical: **Quality Score**, **Adoption Score**, **Coalition Support Estimates**, **External Review Status**, **Adoption Friction**, **Required Electoral Environment**, and **Development Priority**.

Use this compact format when coalition estimates are displayed:

```markdown
> **Coalition Support Estimates:**<br />&nbsp;&nbsp;&nbsp;&nbsp;Democratic 80%<br />&nbsp;&nbsp;&nbsp;&nbsp;Independent 60%<br />&nbsp;&nbsp;&nbsp;&nbsp;Republican 40%<br />&nbsp;&nbsp;&nbsp;&nbsp;Bipartisan viability 55%
```

The full audit history should live in a sibling file named `ISSUE-ID.audit.md` beside the issue page. For example, `areas/DOJ/issues/DOJ-001.md` should link to `areas/DOJ/issues/DOJ-001.audit.md`. The sibling audit file is the append-only technical record. New audits should add a new dated entry under **Audit History** rather than replacing, deleting, or compressing prior audit entries. Use newest-first ordering unless a page already uses another clear chronological convention. Older audit entries may be corrected only to fix clerical errors, broken links, stale line references, or clearly identified inaccuracies; do not remove them merely because the audit file becomes long. Public-facing compiled editions may omit or trim audit-history files, but source control should retain the complete technical audit history.

Each issue page with a **Proposal Scoring** section should also carry compact audit metadata in front matter: `audit_status`, `audit_score`, `audit_last_type`, `audit_last_date`, `audit_next`, `audit_rubric_version`, `audit_rebaseline_status`, `change_audit_needed`, `change_audit_reason`, and `audit_history` where applicable. Where external professional review has occurred, the page should also carry compact external-review metadata when practical: `external_review_status`, `external_review_type`, `external_review_date`, `external_review_reviewer_role`, and `external_review_notes`. These fields are for tooling and quick scanning only. They should match the issue-page **Proposal Scoring** section and sibling audit-history file. The metadata should not replace the human-readable scoring summary or audit explanation.

Each completed audit should leave a detailed sibling audit-history record that identifies:

1. audit scope;
2. audit date;
3. source record reviewed;
4. material claims verified;
5. claims left unresolved or marked for source development;
6. defects corrected during the audit;
7. unresolved findings;
8. source, legal, judicial-scrutiny, remedial, drafting, implementation, adoption, and political-language risks;
9. international-support and foreign-relations score, or why it is not applicable;
10. recommended next audit or revision;
11. whether issue-page audit front matter and Proposal Scoring were updated;
12. whether the proposal-quality score changed; and
13. why any score change is justified.

For higher-tier audits, successive audits, or audits that change the proposal-quality score, the sibling audit-history record should normally include a short narrative of the audit's major findings, a list or paragraph of sources and source categories checked, a clear distinction between verified findings and unresolved claims, a score explanation tied to the scoring rubric, and enough detail on corrected defects that a future reader can see why the proposal improved. The issue page should keep only the compact Proposal Scoring summary plus any cumulative audit findings that are genuinely useful to a reader evaluating the proposal itself.

Each completed audit should also include a brief **Audit Process Feedback** note. The note should identify whether the selected tier was adequate, whether the audit finished under or over estimate, what slowed or improved the audit, what recurring defect or workflow friction appeared, and whether the audit framework, inventory method, source rules, scoring rules, or issue-page template should be revised before future audits. If a rule change is recommended, record the reason and apply the change only when it improves consistency, source reliability, transparency, resource control, or implementation quality.

If an audit finds serious unresolved defects, the proposal should remain below external-circulation readiness even if the page is otherwise developed.

### Hallucination-Resistance and Verification Protocol

The audit must be designed to minimize invented, overstated, or unverifiable claims. The default rule is: **if the project record does not contain reliable support for a claim, the claim is unresolved and receives no audit credit.**

Apply the following rules in every audit:

1. **Current-source refresh.** Do not assume the project record, prior audit, or model memory contains the latest relevant information. At the start of any substantive audit, check current sources for recent legal developments, legislation, court action, agency action, news, public-opinion evidence, stakeholder statements, scholarship, advocacy activity, implementation experience, international reactions, and other materials that could support, weaken, refine, or reframe the proposal.
2. **Mootness and material-reframing check.** At every tier, scaled to the tier's time budget, check whether intervening decisions, pending judicial opinions, pending merits cases, certiorari grants, emergency or stay applications, opinions, laws, regulations, orders, agency actions, factual developments, repeals, superseding enactments, or other events have made the proposal moot, partially obsolete, legally impossible, already satisfied, or materially in need of restructuring. Treat this as a required current-status gate, not an optional research enhancement. If the check cannot be completed at the selected tier, mark it unresolved and assign no favorable current-status credit.
3. **Government and institutional source sweep.** Check relevant government institutions and public bodies, including federal, state, local, tribal, territorial, and international sources where relevant; courts and court dockets; legislative bodies and committee materials; administrations, departments, bureaus, agencies, offices, inspectors general, commissions, boards, independent agencies, public authorities, and official blogs, journals, reports, guidance, data portals, press releases, and enforcement records.
4. **Public legal-research source sweep.** Check public-access legal research hubs and legal-information services relevant to the issue, such as CourtListener, RECAP, Justia, Google Scholar, Congress.gov, GovInfo, Federal Register, eCFR, state legislative portals, state court portals, agency adjudication databases, public law-library guides, bar-association materials, legal blogs, legal newsletters, and comparable open resources. Do not require paid-access legal databases, and do not imply that paywalled systems were checked.
5. **Professional and research source sweep.** Where relevant, check current professional journals, law reviews, policy journals, latest research, working papers, technical reports, and comparable data-bearing sources.
6. **Broad discovery, careful validation.** Discovery may include official records, court dockets, agency materials, congressional and state-legislative records, reputable news organizations, local news, trade publications, well-regarded blogs, independent media, newsletters, watchdog organizations, advocacy groups, think tanks, and academic commentary where relevant. These sources may identify leads, examples, objections, public salience, possible supporters, diplomatic concerns, or international reactions, but audit credit requires reliable verification and appropriate characterization.
7. **Primary-source preference.** When a discovery source points to a statute, bill, amendment, hearing, vote, court filing, order, agency action, poll, report, quotation, official statement, or international action, verify the underlying primary material before treating the proposition as established.
8. **Recency log.** Record the date the current-source refresh was performed, the source categories checked, the search terms or repositories used where practical, and any fresh sources added or intentionally rejected. Paid-access database nonuse need not be treated as an audit defect.
9. **No invented authority.** Do not cite or rely on a case, statute, bill, rule, executive order, regulation, report, poll, scholar, organization, official, quotation, date, docket, vote count, sponsor count, co-sponsor count, international body, foreign-government statement, or factual episode unless it is verified from a reliable source.
10. **No source laundering.** Do not cite a secondary source as though it were primary authority. Where a secondary source identifies a case, bill, report, poll, official action, or international reaction, verify the underlying primary material before treating the proposition as established.
11. **Nearby-source rule.** Every material factual, legal, causal, polling, legislative-history, international-relations, or real-world-example claim should have a nearby citation or a clearly identified source note.
12. **Source-inventory rule.** Every external source used for audit credit must be captured in [`sources.csv`](../inventory/sources.csv), with enough context to check what proposition it supports.
13. **Claim-status rule.** Classify important propositions as established fact, legal conclusion, institutional inference, policy judgment, public-opinion evidence, international-relations assessment, prediction, discovery lead, allegation, or unresolved question. Do not let one category masquerade as another.
14. **Current-law and pending-case check.** For statutes, regulations, rules, official roles, court doctrine, agency structures, pending legislation, and pending judicial matters that could affect the proposal, verify that the cited authority is current or clearly label it as historical, pending, stayed, argued, granted, unresolved, or superseded.
15. **Polling and public-support check.** Polling, survey, referendum, state-practice, and popular-support claims must identify the source, date, jurisdiction, population, sample or methodology where available, question wording where material, and whether the evidence supports the actual mechanism or only an adjacent principle.
16. **Legislative-history check.** Sponsor counts, co-sponsor counts, bipartisan status, committee action, chamber passage, enactment, or repeated introduction must be verified from congressional, state-legislative, or other authoritative legislative records.
17. **Judicial-doctrine check.** Supreme Court, lower-court, and state-court claims must identify the relevant case, holding or pending posture, doctrine, standard of review, and uncertainty. Do not infer current doctrine from memory where direct verification is feasible.
18. **Scholarly-authority check.** Do not invoke legal scholars, experts, journals, research consensus, or professional consensus unless the audit identifies the author or institution, work, claim, publication context, methodology where material, and any meaningful disagreement.
19. **International-relations check.** International-support, diplomatic, treaty, alliance, foreign-government, multilateral-institution, democracy-index, rule-of-law, human-rights, security, or comparative-law claims must identify the jurisdiction or institution, source, date, relevance, and any countervailing evidence.
20. **Media-source characterization.** News, blogs, independent media, and newsletters should be characterized according to what they can reliably support: reported facts, allegations, public salience, stakeholder framing, emerging examples, opposition arguments, international reactions, or leads requiring confirmation.
21. **Quote discipline.** Direct quotations must be exact, limited, and traceable to a cited source. Paraphrases should not imply stronger support than the source provides.
22. **No false precision.** Do not give numerical estimates, probabilities, dates, vote counts, support percentages, fiscal impacts, litigation odds, adoption likelihoods, or diplomatic impacts unless the basis is identified. If an estimate is judgment-based, label it as such and explain the inputs.
23. **Temporal discipline.** Distinguish current, pending, superseded, expired, proposed, enacted, stayed, vacated, reversed, alleged, reported, projected, or historical authorities.
24. **Adverse-evidence rule.** If reliable sources materially undermine the claim, identify the conflict rather than selecting only favorable evidence.
25. **Unverified-placeholder rule.** Use explicit placeholders such as `Source needed`, `Verification pending`, `Discovery lead only`, or `Unresolved` rather than drafting around missing support.

An audit may recommend research, but it may not award score credit for research that has not been performed. Hallucination-resistance failures should be treated as source, legal-fit, adoption, or drafting defects as applicable.

### Proposal Quality Score

The **Proposal Quality Score** is a provisional 0-100 planning value. It measures how ready the proposal is for reliance, external review, legislative outreach, or publication as a mature recommendation. It is not a measure of how important the underlying problem is.

Scores must be calculated consistently. A repeated audit using the same record, same rubric, and same findings should produce the same score. Audit count may inform the score only through the formula below; repetition alone must not increase the value. A score should increase only when an audit meaningfully broadens review, resolves findings, verifies sources, improves legal fit, strengthens drafting, reduces implementation risk, or improves adoption prospects without weakening the least-complex adequate remedy.

Use this mathematical formulation only for developed proposals. A proposal is **Developed** when the project has created a basic proposal framework for the issue: a distinct issue page or equivalent proposal page that identifies the institutional anomaly, manifestation, damage, underlying weakness, proposal survey or source-development basis, least-complex adequate remedy, repair/prevention approach, and proposed legislative or non-legislative vehicle where appropriate. Candidate inventory entries, area-page issue bullets, and source-development notes are not developed proposals and receive no proposal-quality score until that framework exists.

```
Proposal Quality Score =
  Structural Score
+ Evidence Score
+ Legal Fit Score
+ Prior-Proposal Score
+ Remedy Score
+ Implementation Score
+ Abuse-Resistance Score
+ Drafting Score
+ Cogency Score
+ Adoption Score
+ Project-Integration Score
+ External-Review Score
- Penalties
```

| Component | Maximum points |
| --- | ---: |
| Structural Score | 8 |
| Evidence Score | 12 |
| Legal Fit Score | 10 |
| Prior-Proposal Score | 8 |
| Remedy Score | 12 |
| Implementation Score | 8 |
| Abuse-Resistance Score | 8 |
| Drafting Score | 8 |
| Cogency Score | 6 |
| Adoption Score | 12 |
| Project-Integration Score | 4 |
| External-Review Score | 4 |
| **Total before penalties** | **100** |

For consistent application, use these component definitions:

| Component | Full-score standard |
| --- | --- |
| Structural Score | The issue has the required architecture, correct issue ownership, accurate status, and no unresolved duplication. |
| Evidence Score | Material factual, legal, causal, and real-world-example claims have nearby citations and source-inventory coverage. |
| Legal Fit Score | The proposal identifies verified authority, limits, doctrines, vulnerabilities, and judicial-scrutiny issues. |
| Prior-Proposal Score | Existing law, direct analogues, functional analogues, budget analogues where relevant, and prior models have been checked against authoritative records and weighted by enacted use, institutional review, sponsorship, co-sponsorship, bipartisan support, and legislative progress. |
| Remedy Score | The remedy is the least-complex adequate remedy and addresses repair, prevention, fallback options, and remedy mismatch risk. |
| Implementation Score | The proposal can be administered, funded, enforced, reviewed, updated, and moved through a vehicle that matches its required electoral environment without unrealistic institutional assumptions. |
| Abuse-Resistance Score | Capture, evasion, delay, retaliation, pretext, selective enforcement, and partisan conversion risks are identified and mitigated. |
| Drafting Score | Legislative or rule text uses proper vehicle, conventions, definitions, responsible actors, procedures, remedies, deadlines, review, and severability. |
| Cogency Score | The problem, weakness, damage, remedy, and implementation logic follow from each other without hidden premises or overclaiming. |
| Adoption Score | Support and adoption analysis, public-support evidence, audience fit, objection handling, adoption vehicle, coalition strategy, and required electoral environment are documented with evidence. |
| Project-Integration Score | Internal links, legislation links, issue status, remedy type, source inventory, audit metadata, audit-history sidecar, GitHub Project canonical-page links, area page, and compiled-document placement are consistent. |
| External-Review Score | Qualified expert, practitioner, legislative, stakeholder, judicial-scrutiny, or scholarly review has been documented, incorporated, and matched to the reviewer's domain. |

Apply each component as follows:

1. Award full points only when the relevant audit is complete and no material unresolved finding remains.
2. Award half points when the element is substantially present but has unresolved nonfatal findings.
3. Award zero points when the element is missing, materially unsupported, internally inconsistent, or not yet audited.
4. Do not estimate a component from general confidence. If evidence is unavailable, score the component as zero and record the missing work as the next audit need.
5. Do not award component credit based on memory, assumed expertise, model-generated assertions, or uncited background knowledge where verification is feasible.
6. Round only the final score, using ordinary whole-number rounding. If the result is exactly halfway between two whole numbers, round down.
7. If two auditors applying the same record would plausibly differ, use the lower score and record the ambiguity.

### External Review Status and Qualified Reviewers

External Review Score credit may be awarded only when the project record identifies the reviewer category, review date, review scope, reviewer domain, material comments or approval status, and how the review changed or validated the proposal. The project should not identify a reviewer by name, quote private feedback, or imply endorsement unless the reviewer has given permission.

Use careful language. Prefer `reviewed by a qualified reviewer`, `reviewed with comments incorporated`, `reviewed without unresolved material objection within the reviewer's domain`, or `approved for circulation by reviewer within stated scope`. Do not say that proposed legislation is legally approved, professionally certified, final, or guaranteed valid unless that exact characterization is supported by the reviewer's written authorization.

A **qualified reviewer** is a person whose professional role, training, or institutional experience is relevant to the specific part of the proposal being credited. Qualified reviewers may include:

1. a licensed attorney who is not reviewing only as a legislator or political advocate and whose practice, public-law experience, litigation experience, compliance work, or drafting experience is relevant to the proposal;
2. legislative counsel, a professional bill drafter, or a legislative attorney;
3. a legislator, committee staff member, or legislative staff member with jurisdictional, drafting, oversight, or implementation experience relevant to the proposal, with legal-credit limited to the person's actual expertise unless the person is also acting as a lawyer;
4. a law professor, legal scholar, public-administration scholar, political scientist, economist, historian, or other academic whose field directly bears on the legal, institutional, fiscal, empirical, or implementation claim being reviewed;
5. a current or former government official, inspector general staff member, agency counsel, ethics official, election administrator, prosecutor, defender, judge, court administrator, or comparable practitioner with direct institutional knowledge relevant to the proposal;
6. a civil-rights, civil-liberties, good-government, transparency, election, budget, national-security, labor, procurement, privacy, or other subject-matter professional whose expertise directly bears on the proposal's operation; or
7. an affected institutional stakeholder with implementation knowledge, where the credit is limited to implementation feasibility, burden, practical effect, or stakeholder response.

The following do not qualify by themselves for External Review Score credit: general reader approval, ordinary political agreement, media praise, social-media engagement, anonymous comments without verifiable credentials, LLM output, reviewer status outside the relevant domain, or review that cannot be documented in the project record.

External Review Status should use one of these values:

| Status | Meaning |
| --- | --- |
| `not-reviewed` | No qualified external review has been incorporated. |
| `informal-review` | A qualified reviewer gave limited or conversational feedback; comments are documented at a high level. |
| `substantive-review` | A qualified reviewer reviewed the relevant proposal and material comments were incorporated or documented. |
| `reviewed-with-caveats` | A qualified reviewer found the proposal supportable within scope but identified caveats, limits, or unresolved risks that remain disclosed. |
| `reviewed-no-material-objection` | A qualified reviewer raised no unresolved material objection within the stated review domain. |
| `approved-for-circulation` | A qualified reviewer affirmatively approved circulation within the stated scope, with permission to describe the review that way. |

External Review Score should be awarded conservatively:

| External Review Score | Required showing |
| ---: | --- |
| 0 | No qualified external professional review incorporated, or review is undocumented, outside the reviewer's domain, or unresolved. |
| 1 | Informal qualified review with limited notes, no major contradiction, and no claim of approval. |
| 2 | Substantive qualified review with comments incorporated or documented, but material caveats or limited scope remain. |
| 3 | Substantive review by a highly relevant attorney, legislative counsel, legislative staffer, legal scholar, practitioner, former official, or subject-matter expert, with material issues resolved or clearly disclosed. |
| 4 | Multiple relevant qualified reviewers, or formal written review by a highly relevant reviewer, with no unresolved material objection within the reviewed domain or with objections fully documented and addressed. |

External review increases the Proposal Quality Score only through the External-Review Score component unless the review actually improves another component, such as Legal Fit, Drafting, Implementation, Remedy, Abuse Resistance, or Adoption. A professional title alone never increases the score. The audit must identify what changed, what was validated, and what remains unresolved.

Apply penalties after adding component scores:

| Penalty | Points |
| --- | ---: |
| Unsupported material factual claim | -5 each |
| Unsupported material legal claim | -5 each |
| Missing nearby citation for a named real-world event | -3 each |
| Missing source inventory row for an external source | -2 each |
| Citation does not support the proposition for which it is used | -5 each |
| Invented or unverified case, statute, bill, poll, report, scholar, official action, quotation, sponsor count, or vote count | -10 each |
| Current-law, pending-legislation, pending-judicial-matter, polling, or public-support claim not checked for currency | -5 each |
| Internal project link missing where target exists | -1 each |
| Remedy depends on the same failed institution without fallback | -8 |
| Serious abuse, evasion, or selective-enforcement risk unaddressed | -8 |
| Proposed legislation departs from legislative conventions without justification | -5 |
| Judicial-scrutiny risk not identified for a legally vulnerable proposal | -5 |
| Pending judicial opinion or pending controlling case not checked where it could materially affect the proposal | -5 |
| Existing-law amendment path not checked before new architecture | -5 |
| Duplicative issue ownership unresolved | -5 |
| Required current-status, mootness, or material-reframing check not completed at the selected tier | -5 |
| Reliable current source shows material reframing, partial mootness, or superseding development not reflected in the issue page | -10 |

The final score may not be lower than 0 or higher than 100. Penalties should be recorded as findings so a later audit can reproduce the same calculation and remove the penalty only when the defect has been corrected.

### Adoption Score Formula

The **Adoption Score** is part of the 100-point proposal-quality score and is capped at 12 points. It should be calculated the same way in each audit:

| Adoption subcomponent | Points |
| --- | ---: |
| Audience segmentation and audience-specific value proposition | 1.5 |
| Good-faith objection handling across partisan, independent, federalism, civil-liberties, administrative, and constitutional perspectives | 1.5 |
| Adoption vehicle, required electoral environment, and plausible sponsor, validator, or coalition map | 1.5 |
| Public-trust and reciprocity showing the proposal applies fairly across parties and administrations | 1.5 |
| Current, methodologically credible national polling or survey evidence supports the underlying reform principle | 1.5 |
| Current, methodologically credible state-level polling, referendum results, enacted-state practice, or comparable state evidence supports the underlying reform principle | 1.5 |
| The cited public-support evidence is specific to the proposal's actual mechanism rather than only a vague adjacent value | 1.5 |
| The proposal explains how popular support can be used without compromising legality, rights, minority protections, institutional independence, or remedy adequacy | 1.5 |

Adoption score bands are interpreted as follows:

| Score | Descriptor | Meaning |
| --- | --- | --- |
| 0 | Unassessed | Adoption path has not been scored. |
| 1-3 | Weak Adoption Basis | Adoption path is mostly undeveloped or unsupported. |
| 4-6 | Limited Adoption Basis | Some adoption logic exists, but key evidence is missing. |
| 7-9 | Credible Adoption Basis | Adoption path is reasonably developed and partly evidenced. |
| 10-11 | Strong Adoption Basis | Adoption path is well developed and well supported. |
| 12 | Exceptional Adoption Basis | Adoption path is unusually complete and strongly evidenced. |

Do not award polling or public-support points unless the evidence is cited, current enough for the claim being made, methodologically credible, and captured in [`sources.csv`](../inventory/sources.csv). For volatile political questions, polling should normally be treated as current only if it was released within the last two years or if the audit explains why older evidence remains probative. For durable structural preferences, older evidence may be used only with a qualification.

State-level and federal-level support should be evaluated separately. National polling may show broad federal salience; state polling, referendum results, enacted-state practice, or bipartisan state adoption may show practical political viability. Neither should be substituted for the other without explanation.

Public support should increase only the Adoption Score. It should not override legal defects, source weaknesses, abuse risks, or an inadequate remedy. A popular proposal can still receive a low overall score if it is legally vulnerable, poorly drafted, unsupported by sources, or unlikely to survive implementation.

Do not award full adoption-vehicle credit unless the proposal identifies its Required Electoral Environment and Pathway Viability using the Enactment Pathway Check. If the pathway is `currently-dead-on-arrival`, full Adoption Score credit requires a credible narrowing, staging, oversight, state-model, or reserve strategy. If the pathway is `unassessed`, adoption-vehicle credit is zero until assessed.

### Enactment Pathway Check

Every developed proposal should receive an early **Enactment Pathway Check** beginning at T1. The check asks: **what kind of electoral environment is required to make this proposal seriously actionable, and can the proposal be adjusted to fit a more realistic environment without weakening the remedy below adequacy?**

This check is not a standalone score. It feeds the **Adoption Score** and **Implementation Score**:

- Adoption credit requires a realistic political pathway, coalition threshold, and evidence-supported account of the electoral or institutional conditions needed for passage.
- Implementation credit requires a vehicle that matches the pathway, such as oversight, statute, appropriations rider, rules reform, agency action, omnibus package, state model, or constitutional amendment.

Use these required values:

| Field | Allowed values |
| --- | --- |
| Required Electoral Environment | `current-law-available`; `house-oversight-majority`; `narrow-unified-government`; `filibuster-constrained-unified-government`; `sixty-vote-senate`; `filibuster-reform-or-exception`; `wave-election-mandate`; `post-crisis-repair-mandate`; `constitutional-amendment-environment`; `state-level-pathway`; `not-electorally-dependent`; `unassessed` |
| Pathway Viability | `current`; `conditional-current`; `plausible-after-wave`; `post-crisis-only`; `currently-dead-on-arrival`; `unassessed` |
| Development Priority | `immediate`; `active`; `conditional`; `reserve`; `deprioritized`; `unassessed` |
| Pathway Adjustment | `proceed`; `narrow`; `reframe`; `split`; `stage`; `convert-to-oversight`; `convert-to-state-model`; `reserve`; `unassessed` |

The pathway finding must be source-based and reproducible. Do not assign a favorable pathway value from intuition, hope, a single speculative scenario, or assumed partisan advantage. Use the most concrete reliable evidence available for the tier, including:

- current chamber control, seat margins, committee control, veto posture, and filibuster or cloture constraints;
- recent relevant votes, sponsor and co-sponsor patterns, bipartisan sponsorship, committee action, discharge attempts, vetoes, overrides, and enacted analogues;
- current and recent polling on the underlying reform principle, with method, date, sample, and source recorded when relied upon;
- historical wave or collapse-election data only when used as scenario context, not as proof that a future wave will occur;
- recent ballot-measure, referendum, state-enactment, or local-enactment results where the proposal has state or local analogues;
- recent judicial decisions, pending cases, injunctions, agency actions, executive orders, regulations, and enforcement developments that change viability;
- credible voter-sentiment, trust, legitimacy, or institutional-confidence data where directly relevant and properly sourced;
- public statements, platform commitments, leadership positions, or committee agendas from relevant lawmakers or institutional actors, characterized cautiously.

At T1, the check may be preliminary, but it must still be evidence-bound. If sufficient evidence is not available within T1, record `unassessed` or the least favorable supported pathway and identify the source work needed for T2. At T2 or higher, do not award full Adoption or Implementation credit unless the pathway is supported by cited evidence and the proposal explains whether narrowing, staging, reframing, oversight conversion, state-model conversion, or reserve status would improve viability without sacrificing remedy adequacy.

Speculative election-scenario modeling may inform planning but must not itself increase the Proposal Quality Score. A proposal receives credit for correctly identifying its minimum required environment and adjusting the vehicle realistically, not for assuming that a favorable election environment will occur.

#### Institutional Self-Limitation Rule

Legal availability and adoption viability are distinct. A proposal may be `current-law-available` because an agency, officer, court, chamber, committee, or other institution already has authority to adopt it, while still having little or no realistic adoption potential because the required adopter is the same actor whose discretion, power, secrecy, flexibility, or political advantage the proposal would constrain.

When adoption depends on voluntary self-limitation by an institution or officer that is materially adverse to the reform, the audit must:

1. keep `current-law-available` only as a statement of legal vehicle availability, not as proof of adoption likelihood;
2. use `conditional-current` for Pathway Viability unless reliable evidence shows the required adopter is presently willing to adopt the reform;
3. award low or zero Adoption Score credit for the adoption-vehicle subcomponent absent evidence of leadership support, binding external mandate, enforceable statutory fallback, appropriations condition, court order, settlement, or comparable adoption pressure;
4. reflect institutional self-limitation resistance in Adoption Friction, including stakeholder opposition, institutional disruption, public-understanding burden, and implementation friction where applicable;
5. consider `stage`, `convert-to-oversight`, `convert-to-state-model`, or `reserve` as Pathway Adjustment values when the internal or current-law path is formally available but practically nonviable under current leadership; and
6. document the distinction in the issue-page **Adoption Score**, **Adoption Friction**, and **Required Electoral Environment** annotations when those fields are visible.

This rule is a hallucination-resistance guardrail: do not treat a formally available vehicle as realistically adoptable merely because the project can write the rule text.

### Adoption Friction Score

Each developed proposal should receive a separate **Adoption Friction Score** from 0-100. This is a companion metric, not part of the 100-point Proposal Quality Score. It measures the expected intensity of organized opposition, litigation, procedural blockade, public misunderstanding, or institutional resistance. Higher friction does not mean lower quality; a proposal can be high-quality and high-friction.

Use this formula:

| Friction subcomponent | Points |
| --- | ---: |
| Partisan salience: the proposal is likely to be treated as helping or harming a party, administration, movement, candidate, or named political figure | 0-15 |
| Constitutional or doctrinal controversy: the proposal depends on contested constitutional doctrine, uncertain judicial review, or significant statutory interpretation | 0-15 |
| Institutional disruption: the proposal changes authority, procedure, tenure, jurisdiction, funding, enforcement, or decision rights of powerful institutions | 0-15 |
| Rights or identity sensitivity: the proposal touches voting, speech, religion, equal protection, criminal process, immigration, privacy, bodily autonomy, or comparable high-salience rights | 0-10 |
| Stakeholder opposition intensity: concentrated or well-resourced actors are likely to oppose implementation | 0-15 |
| Public-understanding burden: opponents can plausibly caricature the proposal or the proposal requires substantial explanation to avoid misunderstanding | 0-10 |
| Implementation friction: the proposal requires new systems, appropriations, intergovernmental coordination, agency capacity, data-sharing, or complex administration | 0-10 |
| Litigation likelihood: prompt facial, as-applied, emergency, or strategic litigation is likely | 0-10 |
| **Total** | **100** |

Bands:

| Score range | Band |
| --- | --- |
| `0-20` | Low Resistance |
| `21-40` | Manageable Resistance |
| `41-60` | Significant Resistance |
| `61-80` | High Resistance |
| `81-100` | Extreme Resistance |
| Unscored | Unassessed |

Apply the score conservatively:

1. Do not infer a friction score from general political intuition alone; record the basis in the issue page, sibling audit-history file, or both.
2. Do not treat friction as opposition to the proposal's merits. Friction is about expected resistance and adoption difficulty.
3. Do not subtract friction from Proposal Quality Score. Use it to prioritize framing, coalition work, litigation preparation, implementation planning, and public explanation.
4. If the proposal has not yet received an adoption-friction review, record the score as blank or `N/A` and the band as `Unassessed`.
5. If a developed proposal is otherwise current but lacks an adoption-friction score after version `2026-06-26.2`, mark it `soft-rebaseline-needed` until the next audit assigns or expressly defers the score. If the proposal already has `hard-rebaseline-needed` status for a later score-affecting rubric change, keep the hard-rebaseline status rather than downgrading it to soft.
6. Fixed zero-status rows should use `N/A` unless and until the issue becomes developed.
7. When an issue page displays an assessed Adoption Friction Score, the band should appear in parentheses immediately after the score, for example: `72 / 100 (High Resistance)`.

### International Support and Relations Score

Each developed proposal should receive a separate **International Support and Relations Score** from 0-10 where international effects are materially relevant. This score is a companion metric, not part of the 100-point Proposal Quality Score, because some strong domestic institutional repairs may have little direct international dimension.

Use this formula:

| International subcomponent | Points |
| --- | ---: |
| Comparative democratic practice, foreign constitutional practice, or international institutional precedent supports the reform principle | 1 |
| Foreign governments, multilateral institutions, treaty bodies, democracy organizations, human-rights institutions, or allied policy communities have expressed support for similar institutional safeguards | 1 |
| The proposal would likely improve rule-of-law, democratic-resilience, anti-corruption, human-rights, or institutional-stability perceptions of the United States | 1 |
| The proposal would likely strengthen allied trust, treaty reliability, diplomatic credibility, or U.S. soft power | 1 |
| The proposal is unlikely to create serious adverse foreign-policy, national-security, treaty, intelligence-sharing, or alliance-management consequences | 1 |
| Public international, comparative-law, or allied-government sources identify the reform as consistent with democratic or rule-of-law practice | 1 |
| International legal, comparative-law, diplomatic, or policy scholarship supports the reform or identifies manageable concerns | 1 |
| The proposal accounts for likely international criticism or misunderstanding without distorting the remedy | 1 |
| The proposal distinguishes domestic constitutional necessity from international preference and does not rely on foreign or international support as a substitute for U.S. legal authority | 1 |
| The international assessment is current, sourced, balanced, and includes adverse evidence or unresolved uncertainty | 1 |

Do not assign international-support points without current, cited, and properly characterized evidence. International commentary, foreign media, or foreign-government statements may show salience or perception, but they should not be treated as proof of domestic legal adequacy.

If a proposal has no material international-relations dimension, record the score as `N/A` with a short explanation. If the proposal may materially affect foreign relations but the audit has not checked current international sources, record `0` and identify the source-refresh task.

For non-developed issues, use the fixed scores below. Retired, merged, pending-controlling-finding, reliably moot, paused-status, and candidate inventory issues are fixed at `0` and should not receive a formula-based proposal-quality score while that status remains in effect. A paused or fixed-zero issue should receive only a paused-status predicate check until the predicate changes or the user expressly directs exploratory development despite the pause. A candidate issue may receive a formula-based score only after it is promoted to `Developed` by creating the basic proposal framework described above.

| Issue status | Baseline score |
| --- | ---: |
| Retired or merged | 0 |
| Pending judicial finding, merits adjudication, or other controlling external finding | 0 |
| Reliably moot as a standalone proposal | 0 |
| Candidate inventory entry only | 0 |
| Candidate with source-development notes but no basic proposal framework | 0 |

### Score Consistency Rules

To keep scoring reproducible across audits:

1. Record the component scores, penalties, audit date, audit scope, and source record used to calculate the final score.
2. Record whether each component received full, half, or zero credit and identify the evidence supporting that choice.
3. Do not change a score unless at least one component score, penalty, public-support input, or baseline status changes.
4. Do not award points for intended future work, uncited knowledge, informal confidence, assumed public opinion, or repeated review of unchanged material.
5. Treat unknown, unavailable, stale, methodologically weak, uncited, or unreviewed inputs as unresolved rather than favorable.
6. Use the lower score where a component sits between two values.
7. If separate reviewers would assign different scores, require them to identify the disputed component, cited evidence, and specific rule causing disagreement; absent resolution, use the lower score.
8. Keep prior audit scores visible in the audit record where practical so score movement can be explained.
9. If the scoring formula is later amended, assign a new audit rubric version, record the version used for the audit, and update the rebaseline status of affected proposals.
10. A higher score should reflect stronger reliability, not merely a longer or more elaborate proposal.

Use the following bands to interpret formula-based scores. These bands do not replace the scoring formula and should not be used to award points independently:

| Score range | Threshold status | Meaning |
| --- | --- | --- |
| 0 | Not Scored | Retired, merged, blocked by pending controlling finding, reliably moot, pending development, or no standalone proposal quality score. |
| 1-24 | Early/Partial Draft | Developed proposal with severe unresolved defects or only minimal audit support. |
| 25-49 | Early/Partial Draft | Partial draft or early development with significant unresolved source, legal, remedy, or structure issues. |
| 50-64 | Developed Draft | Developed draft with meaningful framework structure but incomplete source, legal-fit, prior-proposal, adoption, or implementation review. |
| 65-74 | Substantially Developed Draft | Substantially developed proposal with several audit components complete; useful internally but still carrying material unresolved issues. |
| 75-84 | Review Ready | Strong enough for knowledgeable external critique, with source verification, existing-law fit, prior-proposal review, and remedy analysis substantially complete. |
| 85-89 | Advanced Review Ready | Most internal checks are complete, but key external validation, adoption evidence, judicial-risk resolution, or implementation support remains incomplete. |
| 90-94 | Proposal Ready | Mature enough for serious proposal packets or stakeholder circulation, with any remaining caveats clearly disclosed. |
| 95-99 | Publication Ready | Publication-ready or near-publication-ready proposal with external expert, practitioner, legislative, stakeholder, or comparable review incorporated. |
| 100 | Fully Validated | Fully validated under the current rubric; theoretically possible, but not expected for most institutional-reform proposals. |

When an issue page displays a Proposal Quality Score, the threshold status should appear in parentheses immediately after the score, for example: `82 / 100 (Review Ready)`. GitHub Project status fields should use the same threshold-status labels for formula-based proposal scores when practical; fixed zero-status items may use routing labels such as `Deferred / Parked`, `Done / Published`, or `Pending development` when those labels are more informative.

Scores should remain conservative. When in doubt, record the lower score and identify the next audit needed to justify advancement.

Audit rows created before adoption of the component formula should be treated as provisional status scores. They should be recalculated under the formula when the next T2, T3, or T4 audit is performed.

### Support and Adoption Audit

Each developed proposal should be reviewed for support and adoption prospects among the audiences most likely to affect adoption, implementation, public legitimacy, and long-term durability.

Support estimates, audience-appeal percentages, coalition viability estimates, and similar scoring judgments should be consolidated here, in the issue's `Proposal Scoring` summary, or in the issue's audit-history sidecar. When an audit has assigned audience-class percentage estimates, the issue-page `Proposal Scoring` summary should display them in the top score group as **Coalition Support Estimates** unless the estimate has been superseded or withdrawn. They should not appear as standalone `Support Appeal` annotations unless the issue also needs a non-scoring substantive support discussion. When estimates are not based on polling or comparable evidence, label them as provisional planning judgments in the matching **Coalition Support Estimates** annotation segment or audit-history sidecar, not necessarily in the compact scoring box, and do not award polling or public-support score credit for them.

The audit should include:

1. **Audience segmentation.** Identify the proposal's likely audiences, including lawmakers, legislative staff, policy organizations, good-government groups, civil-liberties groups, institutional conservatives, election administrators, federalism advocates, legal academics, journalists, affected administrators, practitioners, and informed citizens where relevant.
2. **Audience-specific value proposition.** Confirm that each important audience can quickly see why the proposal matters to its own concerns, duties, incentives, or institutional commitments.
3. **Objection handling.** Identify the strongest good-faith objections from Democratic, Republican, independent, bipartisan, federalism, civil-libertarian, constitutional, administrative-burden, cost, implementation, and separation-of-powers perspectives, and determine whether the proposal answers them.
4. **Bad-faith misuse and caricature.** Identify how opponents could misstate, weaponize, or caricature the proposal, then revise framing or drafting to reduce avoidable misreading without weakening the remedy below adequacy.
5. **Institutional-conservative appeal.** Test whether the proposal can be defended in terms of restraint, rule of law, separation of powers, federalism, anti-corruption, predictability, reciprocity, and protection against future abuse by either party.
6. **Civil-liberties appeal.** Test whether the proposal protects due process, speech, association, equal treatment, privacy, fair notice, neutral enforcement, and limits on coercive state power.
7. **Administrative burden.** Determine whether the proposal is too complex, costly, paperwork-heavy, litigation-dependent, or agency-dependent, and whether a simpler implementation design would preserve adequacy.
8. **Lawyer and legislative-counsel seriousness.** Test whether a legally trained reader would see clear authority, precise terms, correct statutory hooks, clean definitions, appropriate severability, enforceable procedures, and no avoidable overclaiming.
9. **Staffer one-page test.** Confirm that a congressional staffer or policy aide can understand the problem, proposed repair, legal authority, cost or burden, likely opposition, and core talking point in under five minutes.
10. **Neutrality versus candor.** Confirm that the proposal avoids partisan framing while still naming objectively documented misconduct, institutional damage, and constitutional stakes where the record supports doing so.
11. **Adoption path.** Identify the most realistic vehicle, such as standalone legislation, amendment to a moving bill, appropriations rider, oversight hearing, committee report language, agency rule, state model law, court rule, professional standard, or constitutional amendment.
12. **Coalition sponsor map.** Identify plausible champions, co-sponsors, validators, and unusual coalitions, including civil-liberties groups, institutional conservatives, election officials, veterans' organizations, former officials, inspectors general, state administrators, legal scholars, policy centers, or professional associations where relevant.
13. **Current public-support evidence.** Identify whether credible current polling, survey evidence, referendum results, state practice, federal legislative support, or bipartisan adoption evidence supports the proposal's actual mechanism at the federal level, state level, or both.
14. **Public trust.** Confirm that an ordinary reader would see the proposal as fair, reciprocal, and applicable to future officeholders of either party.

The audit should produce a concise support plan identifying likely supporters, likely skeptics, likely opposition arguments, possible validators, preferred adoption vehicle, public-support evidence, and changes that could increase support without weakening the least-complex adequate remedy.

### Political-Language and Coalition-Appeal Audit

Each developed proposal should be reviewed for political-language neutrality and potential appeal across the likely adoption coalition.

The audit should check whether the proposal:

1. uses institution-focused language rather than partisan slogans, unnecessary personal attacks, or avoidably factional framing;
2. states concrete misconduct or institutional damage directly where supported by evidence, without diluting the project's truth-telling function;
3. explains why the safeguard should appeal to Democrats, Republicans, independents, institutionalists, civil libertarians, federalists, good-government advocates, and other plausible cross-pressured constituencies;
4. identifies likely objections from Democratic, Republican, independent, bipartisan, institutional, civil-libertarian, federalism, administrative, and implementation perspectives;
5. distinguishes objections to the proposal's policy merits from objections arising from partisan loyalty, short-term advantage, or bad-faith opposition;
6. considers whether neutral wording, narrower triggers, safer enforcement procedures, sunset review, reporting requirements, or clearer safe harbors could increase support without weakening the remedy below adequacy; and
7. identifies risks that the proposal could be captured, selectively enforced, or rhetorically reframed as a partisan weapon.

The audit should include provisional percentage estimates of likely support or appeal for at least the following audience classes:

| Audience class | Required estimate |
| --- | --- |
| Bipartisan / cross-party institutionalist support | Estimated percentage likely to find the proposal supportable in principle |
| Independent support | Estimated percentage likely to find the proposal reasonable or confidence-building |
| Democratic support | Estimated percentage likely to support the proposal as framed |
| Republican support | Estimated percentage likely to support the proposal as framed |

Percentage estimates are not polling claims. They are disciplined planning judgments that should be stated as provisional, briefly justified, and revised as better evidence, stakeholder feedback, polling, legislative behavior, expert review, or coalition analysis becomes available.

Each estimate should identify the principal reason for support, the principal reason for resistance, and any framing or design change that could increase adoption prospects without compromising the least-complex adequate remedy.

### Judicial and Scholarly Scrutiny Audit

Each developed proposal should be tested against likely judicial and scholarly scrutiny before it is treated as ready for external circulation, especially where the proposal alters institutional power, regulates executive discretion, affects elections, touches speech, creates enforcement mechanisms, changes judicial procedure, limits removal or appointment authority, or depends on contested constitutional doctrine.

The audit should identify:

1. the Supreme Court doctrines most likely to control or constrain the proposal;
2. the relevant lower-court doctrines, circuit splits, procedural doctrines, and standards of review;
3. any state constitutional doctrines or state-court constraints for model state legislation;
4. the most likely plaintiffs, defendants, claims, defenses, remedies, and justiciability barriers;
5. standing, ripeness, mootness, political-question, sovereign-immunity, official-immunity, and reviewability issues;
6. separation-of-powers, federalism, nondelegation, appointments, removal, due-process, equal-protection, First Amendment, criminal-procedure, spending-power, commandeering, and Article III concerns where relevant;
7. the strongest originalist, textualist, structural, precedential, functionalist, federalism, liberty-protective, and administrability objections;
8. the strongest arguments that the proposal is within congressional, state, judicial, agency, or constitutional authority;
9. how current Supreme Court justices or relevant lower-court judges might plausibly scrutinize the proposal's theory, text, tailoring, enforcement mechanism, and remedy;
10. how well-respected legal scholars, legislative counsel, former judges, former executive-branch lawyers, and institutional-design experts might criticize or strengthen the proposal;
11. whether narrowing, clearer definitions, severability, safe harbors, sunset review, factual findings, procedural protections, exhaustion rules, heightened mens rea, judicial review provisions, or alternative enforcement channels would increase the likelihood of being upheld; and
12. whether a constitutional amendment, court rule, state-law approach, appropriations condition, reporting requirement, or nonbinding institutional mechanism would be more durable than ordinary federal legislation.

The audit should produce deeply researched recommendations for increasing the likelihood that courts would uphold the proposal. Recommendations should distinguish:

1. changes that materially improve legal durability without weakening the remedy;
2. changes that improve legal durability but reduce remedial strength;
3. arguments that should appear in legislative findings or annotation;
4. authorities that should be cited before publication;
5. questions that require attorney, legislative-counsel, scholar, or practitioner review; and
6. fallback designs if the preferred remedy is likely to be invalidated.

Judicial-scrutiny analysis should not pretend to predict case outcomes with certainty. It should identify litigation risk, explain the best arguments on both sides, and make the proposal more careful, better supported, and more likely to survive review.

### Existing-Law and Prior-Proposal Consistency Audit

Each developed proposal should be checked against existing law, rules, regulations, procedures, and institutional practice before new legislative architecture is proposed.

The audit should apply the following preference order:

1. **Existing law, rule, regulation, procedure, or institutional practice.** Prefer amending or extending an existing legal or institutional vehicle where it can adequately solve the problem.
2. **Prior enacted or formally adopted models.** Prefer models that have already operated in federal, state, judicial, administrative, congressional, or comparative institutional practice.
3. **Prior proposed legislation or formal reform proposals.** Prefer proposals with meaningful demonstrated support over one-off or purely symbolic proposals.
4. **New project-drafted architecture.** Use a new structure only where existing law and prior models are inadequate, unavailable, or too compromised to adapt.

When prior legislation is used as a model, the audit should give greater weight to:

1. legislation with more than one sponsor;
2. legislation with co-sponsors, with increasing corresponding weight as the number of co-sponsors increases;
3. legislation with at least two co-sponsors as a minimum signal of support beyond symbolic introduction;
4. legislation with broad co-sponsorship across committees, states, regions, ideological factions, or institutional constituencies relevant to the proposal;
5. legislation with bipartisan co-sponsors, which should receive additional weight beyond the raw number of co-sponsors;
6. legislation that advanced beyond introduction, such as committee consideration, reported text, chamber passage, conference use, enactment in related form, or repeated reintroduction across Congresses; and
7. legislation supported by hearings, expert testimony, committee reports, agency analysis, inspector-general reports, CRS analysis, or comparable institutional review.

Co-sponsor count is a proxy for demonstrated political and institutional support, not a substitute for adequacy. A bill with many co-sponsors may still be rejected if it fails the least-complex adequate remedy standard, and a bill with few co-sponsors may remain useful if it supplies strong language, a well-tested mechanism, or an important institutional model.

The audit should identify whether the proposal:

1. amends existing law rather than creating a new standalone title where amendment is adequate;
2. explains why any existing vehicle is insufficient if the proposal departs from it;
3. distinguishes borrowed legislative language from ARRP-drafted language;
4. notes the sponsorship, co-sponsorship, bipartisan status, and legislative history of cited prior bills where available; and
5. avoids overstating the significance of a prior bill that had only a single sponsor, no co-sponsors, no bipartisan support, or no meaningful legislative activity.

This preference order does not require adopting weak prior proposals. Adequacy remains controlling: a better-supported model may still be rejected if it fails to repair the institutional weakness, lacks enforceability, creates abuse risk, or cannot satisfy the least-complex adequate remedy standard.

### Functional Analogue Search

The existing-law and prior-proposal audit must not stop at `no direct analogue found`. If no direct existing-law vehicle or prior proposal is identified, or if the direct analogue is weak, the audit must conduct a functional-analogue search before closing the issue.

A functional analogue is an enacted law, rule, regulation, institutional practice, budget authorization, oversight model, reporting requirement, or formal proposal that uses a similar method to solve a different problem. Functional analogues do not prove the ARRP proposal is correct, but they can show that Congress or another institution has already used the same kind of mechanism.

At T2 and above, the audit should attempt to identify at least three functional analogues or document why fewer could be found. Search by:

1. **Institution:** DOJ, OIG, GAO, BJS, FBI, agency heads, congressional committees, courts, state agencies, or comparable implementing bodies.
2. **Mechanism:** data collection, statistical review, anomaly detection, confidential notice, congressional reporting, compliance certification, audit, random sampling, pilot implementation, methodology validation, or public reporting.
3. **Safeguards:** privacy, confidentiality, classified information, grand jury material, protected records, fair-trial rights, sensitive populations, or limited disclosure.
4. **Budget model:** authorization of appropriations, pilot funding, grant funding, staffing, data systems, implementation timelines, agency budget material, CBO scores, or historical program costs.
5. **Oversight path:** annual report, inspector-general notice, GAO review, committee notice, public report, secure report, enforcement referral, or corrective-action plan.

Classify each useful analogue as one or more of:

| Analogue type | Meaning |
| --- | --- |
| Direct analogue | Same or nearly same subject and mechanism. |
| Functional analogue | Different subject but similar institutional method. |
| Budget analogue | Useful primarily for appropriations, staffing, or implementation scale. |
| Safeguard analogue | Useful primarily for privacy, secrecy, confidentiality, rights, or abuse-resistance design. |
| Cautionary analogue | Shows a failure mode, abuse risk, underfunding problem, implementation burden, or litigation vulnerability. |

When a functional analogue is used, state its limits. Do not imply that a functional analogue supplies direct legislative precedent, public support, constitutionality, fiscal sufficiency, or stakeholder agreement unless the source actually supports that claim.

## Adding or Promoting Issues

Before adding or promoting a candidate into a standalone issue, apply the issue-admission test in [`FRAMEWORK.md`](FRAMEWORK.md).

If a candidate is duplicative, keep it as a manifestation, example, cross-reference, or research note rather than creating a separate issue.

## Links to Developed Work

When an issue becomes developed, maintain consistency among:

- the GitHub Project item for the issue;
- the area README entry;
- the issue page under the relevant area directory;
- any proposed legislation under [`../legislation/`](../legislation/); and
- any source-development or research notes that remain relevant.

## Cross-References

Tracking entries should not duplicate developed analysis. Where a related issue is developed elsewhere, cross-reference the primary area or issue instead of repeating the same diagnosis, evidence, or remedy.
