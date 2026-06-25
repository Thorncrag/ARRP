---
title: "Inventory Maintenance Method"
status: active
---

# Inventory Maintenance Method

## Purpose

Maintain the project's living inventory of institutional areas and issues before and during substantive development.

This file is limited to inventory maintenance. The canonical drafting method, issue architecture, source standard, Issue Snapshot format, Proposal Survey requirement, remedy standard, and cross-reference rules are maintained in [`../framework/FRAMEWORK.md`](../framework/FRAMEWORK.md).

## Inventory Files

The structured inventory is maintained in:

- [`areas.csv`](areas.csv) — project areas, generalized institutional concerns, status, issue counts, and notes.
- [`issues.csv`](issues.csv) — issue identifiers, area ownership, priority, and development status.
- [`contents.csv`](contents.csv) — combined area-and-issue navigation index for table-of-contents planning.
- [`audits.csv`](audits.csv) — issue-level proposal-quality scores, audit counts, audit status, score basis, and next audit need.
- [`sources.csv`](sources.csv) — source-tracking records.

## Inventory Rules

1. Each substantive issue should have a stable issue identifier, such as `DOJ-001`.
2. Each issue should have one primary area home.
3. Candidate issues may remain inventory-only until they receive a developed issue page.
4. Retired or merged issues should remain traceable in the inventory rather than disappearing silently.
5. Area issue counts should be updated when issues are added, retired, merged, or moved.
6. Development status should use consistent labels, such as `Candidate`, `Developed`, `Awaiting merits adjudication`, or `Retired—merged into ...`.
7. Every issue should have a row in [`audits.csv`](audits.csv), even if the issue is only a candidate or has been retired or merged.
8. Inventory updates should be made in the same change as the substantive project update that requires them.

## Project-Update Checklist

When updating the project, check whether the change requires inventory maintenance:

1. If an area is added, renamed, retired, or materially reframed, update [`areas.csv`](areas.csv) and [`contents.csv`](contents.csv).
2. If an issue is added, renamed, promoted, retired, merged, moved, or given a new development status, update [`issues.csv`](issues.csv), [`contents.csv`](contents.csv), and the relevant area README.
3. If proposed legislation is added, renamed, or removed, update the `Legislation Path` field in [`contents.csv`](contents.csv).
4. If an issue is audited, promoted, paused, retired, merged, given legislation, or materially revised, update [`audits.csv`](audits.csv), including `Audit Runs`, `Proposal Quality Score`, `Audit Status`, `Score Basis`, and `Next Audit Need`.
5. If an external source is newly cited, removed, or used for a materially different proposition, update [`sources.csv`](sources.csv).
6. If source review is completed, update `Reviewed?`, `Proposition Supported`, and any notes in [`sources.csv`](sources.csv).
7. If issue counts change, update both the area README front matter and [`areas.csv`](areas.csv).

## Contents Index Rules

`contents.csv` may combine areas and issues because its purpose is navigation, ordering, and eventual table-of-contents development.

The normalized `areas.csv` and `issues.csv` files should remain available for compact tracking, but the combined contents index should include relative links to the area page, issue page, and proposed legislation where those files exist.

## Source Inventory Rules

`sources.csv` should capture distinct external sources already cited in the project. A row may be associated with an issue, area, framework file, research file, or project-level page.

Source rows may be captured before full verification. Use the `Reviewed?` field to distinguish a captured source from a source that has been checked against the proposition it is being used to support.

When a cited issue page, legislation file, or framework file is edited, refresh any affected `Project Location` line references in [`sources.csv`](sources.csv). Exact line references are useful for rapid verification, but they can become stale after otherwise unrelated edits.

## Audit Inventory Rules

`audits.csv` should assign every issue a current proposal-quality score using the rubric in [`../framework/FRAMEWORK.md`](../framework/FRAMEWORK.md).

The score is a conservative planning value. It should reflect the issue's current development quality, audit history, source support, legal support, judicial-scrutiny review, proposal survey, remedy adequacy, drafting clarity, abuse resistance, support appeal, current public-support evidence, and adoption prospects.

Audit updates should identify the resource tier used: T0 triage scan, T1 framework check, T2 development audit, T3 readiness audit, or T4 publication-ready audit. Do not treat a lower-tier audit as a completed higher-tier audit. If the user does not specify a tier, ask which tier to run and recommend the lowest useful tier. Before running a higher-tier audit, confirm that the immediately lower tier has already been completed and remains reasonably current; otherwise ask whether to run the lower tier first or explicitly skip it. T4 requires additional explicit user confirmation before it is run.

Audits should be run on exactly one issue at a time. Before starting, identify the target issue by issue ID and page path. If the request could refer to more than one issue, or if the issue ID is missing or unclear, ask the user to identify the issue before beginning the audit.

Before starting a new audit for an issue, check the most recent audit row or audit record for unresolved blocking findings, skipped prerequisites, source-development tasks, or user-input needs that must be resolved before further audit work can proceed. If blocking unresolved items remain, cancel the new audit request, notify the user, and ask whether to resolve the existing items, override the block, or revise the audit scope. Ordinary next-audit recommendations do not block a new audit when the requested audit is meant to address them.

The audit tier controls scope and confidence, not scoring weight. Apply the same component weights at every tier; do not award or subtract points merely because a higher or lower tier was selected. Unreviewed components should be marked unresolved and receive no favorable credit until reviewed.

Audit updates should not let one audit area, source dispute, or legal question consume the entire tier estimate. Tier times are planning estimates rather than hard caps, but an audit should not exceed 150% of the selected tier's estimated time without explicit user approval. On a first run, the auditor may use reasonable overage up to that 150% ceiling to calibrate complexity, but moving beyond it or reaching T4 requires explicit user approval. Document any overage and use prior results to scope later audits more tightly.

Tier estimates are not minimums. If a responsible audit can be completed in less than the selected tier's estimated time, finish early, record that result, and use it to calibrate future audit budgeting for comparable issues.

Audit count may influence the score only through the mathematical formulation in the framework and only when the audit changes the basis for confidence. Do not increase a score merely because the same unresolved defects were reviewed again.

When updating a proposal-quality score, apply the same component scores, penalties, public-support inputs, and baseline-status rules each time. A repeated audit of unchanged materials should produce the same score. Record the score basis clearly enough that a later reviewer can reproduce the calculation.

Audit rows created before adoption of the component formula are provisional status scores. Recalculate them under the formula during the next T2, T3, or T4 audit.

Retired, merged, and pending-controlling-finding issues must remain scored at `0` while that status remains in effect. Candidate issues may depart from the candidate baseline only when a written audit justifies a formula-based score.

Polling, survey, referendum, state-practice, or popular-support evidence should affect the score only through the Adoption Score formula in the framework. Such evidence must be cited, current for the proposition asserted, methodologically credible, specific to the proposal or reform principle, and captured in [`sources.csv`](sources.csv).

Audit scores should not credit model-generated assertions, memory-based assertions, uncited claims, invented authorities, stale public-support claims, or citations that do not support the proposition asserted. When support is missing, record the item as unresolved and identify the source-development task rather than assigning favorable credit.

Before updating an audit score, perform a current-source refresh rather than assuming the project record contains the latest relevant support. Check recent primary legal materials, official records, legislation, court activity, agency action, relevant government institutions, public-access legal-research hubs, official blogs and journals, public-opinion evidence, professional journals, latest research, international sources, reputable news, local media, independent media, well-regarded blogs, advocacy materials, stakeholder statements, and other relevant discovery sources. Broad discovery may identify leads, examples, objections, supporters, public salience, or international-relations implications, but audit credit requires reliable verification, proper characterization, citation, and source-inventory capture.

When legal-research sources such as CourtListener, RECAP, Justia, Google Scholar, Congress.gov, GovInfo, Federal Register, eCFR, state legislative portals, state court portals, agency adjudication databases, public law-library guides, bar-association materials, legal blogs, or legal newsletters are relevant, record which public resources were checked. Paid-access legal databases are not required audit sources.

Where international effects are materially relevant, record the International Support and Relations Score described in the framework. If no material international dimension exists, record `N/A` and explain briefly. If an international dimension may exist but current international sources have not been checked, record `0` and identify the source-refresh task.

When an audit uncertainty cannot be resolved independently, do not pause the entire audit for user input. Skip only the unresolved portion, document the missing source or decision, assign no favorable score credit for that portion, continue the remaining audit work, and notify the user immediately and concisely.

Audits should fix identified defects when the correction can be made within the selected tier, follows the framework, and does not require unresolved user judgment. Record what was corrected, what remains unresolved, and whether the correction changed the proposal-quality score.

Audit inventory rows should not hide material audit results. When an audit updates [`audits.csv`](audits.csv), also update the relevant issue page with a concise public-facing audit record that includes the latest audit tier, date, proposal-quality score, corrections made, unresolved findings, and next audit need.

Each completed audit should include a brief audit-process feedback note on the issue page or audit record. The note should identify whether the selected tier was adequate, whether the audit finished under or over estimate, what slowed or improved the audit, and whether the framework, inventory method, source rules, scoring rules, or issue-page template should be revised before future audits. Recommended rule changes should explain the reason and should improve consistency, source reliability, transparency, resource control, or implementation quality.

After an audit is completed, or if an audit is interrupted after changes have been made, preserve the work promptly. Where the repository and remote are available, create the necessary non-interactive commit or commits and push them to the configured GitHub remote without asking the user additional process questions, unless approval is required by the working environment or by the framework. Optional local validation, formatting, pre-commit hooks, or other nonessential local checks may be bypassed solely to preserve interrupted audit work, but source verification, citation rules, scoring rules, unresolved-claim treatment, T4 confirmation, and audit-overage approval must not be bypassed. Record any skipped check, local-only commit, or failed push.

## Adding or Promoting Issues

Before adding or promoting a candidate into a standalone issue, apply the issue-admission test in [`../framework/FRAMEWORK.md`](../framework/FRAMEWORK.md).

If a candidate is duplicative, keep it as a manifestation, example, cross-reference, or research note rather than creating a separate issue.

## Links to Developed Work

When an issue becomes developed, maintain consistency among:

- the issue row in [`issues.csv`](issues.csv);
- the area README entry;
- the issue page under the relevant area directory;
- any proposed legislation under [`../legislation/`](../legislation/); and
- any source-development or research notes that remain relevant.

## Cross-References

Inventory entries should not duplicate developed analysis. Where a related issue is developed elsewhere, cross-reference the primary area or issue instead of repeating the same diagnosis, evidence, or remedy.
