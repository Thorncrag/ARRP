---
title: "Agent Rules — Validation and Closeout"
dependencies: "../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Agent Rules — Validation and Closeout

Load this module before closing an autonomous unit, issue audit, batched unit, or task that changes repository, GitHub Project, or Project Console state. Also load it whenever validation, preservation, synchronization, commit, push, or generated-view readback is implicated.

## Output and Preservation

Each completed issue audit should leave:

1. updated issue-page Proposal Scoring and metadata;
2. a new sibling audit-history entry;
3. updated GitHub Project fields where applicable;
4. updated `sources.csv` for sources used for audit credit;
5. validation notes;
6. a commit pushed to GitHub; and
7. when the audit changes an eligible proposal's Project `Development level`, `Status`, `Score`, or goal eligibility, a successful Project Console progress-data refresh and readback, or an explicit recorded blocker identifying the failed workflow or stale generated state.

GitHub Project fields are a completion-critical surface for audit work. If the Project row should change but cannot be updated because of authentication, permissions, API, tooling, sandbox, or connector limitations, the agent must notify the user clearly as soon as the failure is known, identify the exact field or row that remains unsynced, and treat the task as blocked or only partially complete until the Project row is updated or the user explicitly accepts a repo-only interim state. Updating the GitHub issue body may be used as a temporary visibility fallback, but it does not replace the required Project-field update.

Project Console progress data is a derived completion surface whenever an audit changes goal-relevant Project development level, score, workflow status, or eligibility. After the authoritative Project row has been updated and read back and the audit commit has been pushed, dispatch the workflow, wait for a successful run, and read back `project-console-data/progress.json`. If dispatch, authentication, workflow execution, publication, or data verification fails, preserve the audit work, identify the stale progress value, record the exact remaining sync step in [`CURRENT_AUDIT.md`](../logs/CURRENT_AUDIT.md), and do not describe the console as updated. In a multi-unit batch, one verified final refresh may close the whole batch as provided above.

If validation cannot be completed because of a tool or environment failure, preserve the work if possible, record the skipped check, and notify the user.

If commit or push fails, stop the batch after preserving the work locally, record the failure and changed files in the agent audit log or final report, and do not begin another issue until the repository state and authentication problem are resolved.

## Self-Validation Requirement

After each autonomous audit unit and before moving to the next issue, the agent must validate its own work.

If a project validation script exists, run it. If the script supports issue-specific validation, run the issue-specific check for the completed issue and any broader project-level check required by the files changed.

If no validation script exists, perform a manual validation checklist before marking the unit complete:

1. confirm changed Markdown files render structurally and contain no obvious broken local links;
2. confirm issue front matter matches the visible Proposal Scoring section;
3. confirm the sibling audit-history file contains a new entry for the completed audit;
4. confirm the issue page, sibling audit-history file, and GitHub Project fields agree where they overlap;
5. for T1 or a routing-affecting change, confirm the repository front door, project-area contents, affected area contents, Subject and Institution Index, and GitHub issue registry are synchronized under the Navigation Synchronization Check;
6. confirm [`inventory/sources.csv`](../../inventory/sources.csv) parses and includes any source used for audit credit;
7. run a whitespace or formatting check where available;
8. confirm the commit hash is recorded in [`AGENT_AUDIT_LOG.md`](../logs/AGENT_AUDIT_LOG.md);
9. if the unit changed goal-relevant Project fields, confirm the Review Ready dashboard workflow completed and the generated page reflects the new state, or record the exact blocker; and
10. confirm no unintended files remain changed for that unit, including generated PDF, DOCX, XLSX, or similar export files unless the user requested an export refresh, the export is the deliverable, export tooling is being tested, or the work is expressly part of a release/publication pass.

If a validation check is skipped, record the skipped check and reason in [`AGENT_AUDIT_LOG.md`](../logs/AGENT_AUDIT_LOG.md), in the issue audit history when relevant, or in the final user-facing report. A unit should not be marked complete if validation fails, except when the only failure is an explicitly documented environment or tooling limitation and the work has been preserved for human review.

Successful task closeout also follows [`handoff.md`](handoff.md): every completion-critical step must be finished before the current handoff becomes `Inactive`.
