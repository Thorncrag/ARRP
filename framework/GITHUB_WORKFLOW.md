---
title: "GitHub Workflow"
print_levels:
  - full-technical
---

# GitHub Workflow

GitHub is the project's authoritative workflow record. Active proposals, horizon proposals, release blockers, publication tasks, and contributor-facing suggestions should be visible as GitHub Issues and, where useful, on the project board.

The repository remains the authoritative substantive record. Proposal text, audit history, inventories, source records, proposed legislation, and framework rules belong in repo files and should be changed through normal repository edits or pull requests.

## Tracking Rule

Each active ARRP proposal or active horizon item should have a GitHub issue. The GitHub issue tracks discussion, assignment, contributor-facing workflow, and links back to the canonical repository record. The GitHub Project tracks structured workflow metadata. The canonical repo file records the adopted substance.

GitHub issues are durable records and should not be deleted unless they were created erroneously. When an issue is merged, integrated, retired, or otherwise adjudicated, close the issue and preserve its stable number, title, links, and disposition record. If no active work remains on that record, remove only its card from the active GitHub Project; removing a Project item does not delete or alter the underlying issue. Preserve the disposition in the Horizon Scan Log, relevant area page, audit sidecar, registry, or other canonical record as applicable.

Milestones should not be assigned automatically to every proposal. A milestone means the issue is an obligation for that release phase. Proposal and horizon issues may remain unmilestoned until they are pulled into a specific release path.

## Project Fields

Use GitHub Project fields as the authoritative structured workflow metadata:

- `Area` identifies the primary ARRP area or governance/export category.
- `Workstream` distinguishes proposal development from project governance and operations.
- `Priority` records the current project priority.
- `Release blocker` records whether the item blocks the active release.
- `Status` records lifecycle and workflow position.
- `Score`, `Runs`, `Last audit`, and `Next audit` provide compact audit-status summaries.
- `Rebaseline status` records whether the proposal score is current under the governing rubric or needs a soft/hard rebaseline.
- `Change audit needed` records whether a developed proposal has an unresolved targeted Change Audit / Internal Remedy-Fit Audit marker.
- `Canonical page` links to the repository page or GitHub issue that carries the authoritative substance or active intake record.
- `Parent issue` and `Sub-issues progress` should be used for native GitHub parent/sub-issue tracking where work naturally breaks down into child issues.

Do not duplicate these fields as issue-body metadata or as labels. If a field value changes, update the GitHub Project field directly.

Use `Done / Published` for work that was actually completed or published within its own scope. Do not use it as a substitute for `Merged`, `Integrated`, `Retired`, or another archival disposition. A closed adjudicated record with no active work should ordinarily leave the active Project instead of occupying a misleading terminal-status card.

Project-field updates are not optional bookkeeping. When audit work changes a proposal's score, status, run count, last-audit note, next-audit note, rebaseline status, change-audit marker, priority, release-blocker posture, or canonical page, the corresponding GitHub Project row must be updated before the task is reported complete. If the agent cannot update a Project field, it must tell the user immediately, identify the affected issue and field values, preserve the repo work, and either fix the Project access problem with the user or report the work as partially complete. The issue body may carry a temporary snapshot, but the Project field remains the authoritative workflow tracker.

After updating a GitHub issue wrapper or GitHub Project row for an issue-status or audit-control change, perform a readback before closeout. The readback should verify that the GitHub issue body and Project fields match the repository issue metadata for status, score, run count, last audit, next audit, rebaseline status, change-audit flag, canonical page, and release-blocker posture where those fields are in scope. Do not report the task complete until any mismatch is corrected or explicitly disclosed as a blocked sync item.

Use these options for audit-control fields:

- `Rebaseline status`: `Current`, `Current fixed status`, `Soft rebaseline needed`, `Hard rebaseline needed`, `Rebaseline complete`, `Not applicable`, `Unknown`.
- `Change audit needed`: `No`, `Yes`, `Pending review`, `Blocked`.

## Review Ready Progress Dashboard

The private [ARRP Review Ready Progress Dashboard](https://github.com/Thorncrag/ARRP/blob/progress-dashboard/PROGRESS.md) is a read-only planning view derived from the GitHub Project and generated on a dedicated branch. It measures proposal records in the GitHub issue registry against the project's current Review Ready goal without closing proposal issues, assigning artificial milestones, creating tracking-only issues, or adding daily generated commits to `main`.

The Project `Status` field remains the lifecycle authority. The dashboard may use `Score` to detect status/score drift, but it must not infer or write a new status from the score alone. Governance, horizon, source-review, and other non-proposal items are excluded. Newly admitted proposal issues enlarge the tracked scope automatically and must be reported as scope change rather than hidden by resetting the baseline.

The dashboard's registry-based eligibility rule, readiness statuses, baseline, target date, forecast window, and Project field mappings are maintained in [`.github/progress-dashboard.json`](../.github/progress-dashboard.json). The proposal identifier in the built-in Project `Title` joins each active proposal to its registry record, with `Canonical page` used only as a unique fallback; unmatched or ambiguous proposals remain visible as tracking warnings. The governing definitions, metrics, forecast limits, credential boundary, and change-control rules are documented in [`PROGRESS_DASHBOARD.md`](PROGRESS_DASHBOARD.md). Changes to eligibility, the readiness rule, or the official target require a project-level Change Audit.

## Labels

Use labels sparingly. Labels should not duplicate Project fields.

- `kind:*` labels identify the type of issue, such as `kind: proposal` or `kind: horizon`.
- `needs: monitoring` identifies an evidence- or event-dependent item whose next substantive step requires an investigation, litigation development, documentary disclosure, scheduled event, or other defined follow-up predicate. It must not replace the Project `Status` field; the canonical record should state what development will trigger renewed review, and the label should be removed when that predicate is resolved.
- Temporary labels may be used for ad hoc contributor triage only when no existing Project field captures the need.
- Do not use `area:*`, `priority:*`, `stage:*`, `status:*`, or `release:*` labels unless the Project field model is deliberately changed.

## Sub-Issues

Use GitHub native sub-issues rather than Markdown task lists when a governance, release, audit, or publication item has meaningful child tasks. Parent issues should describe the umbrella objective and completion standard. Child issues should carry the executable work and close independently.

A living repository surface may receive a maintenance sub-issue when it has a genuine recurring review obligation, such as an agency or event catalog, election dataset, litigation tracker, legislation survey, recurring crosswalk, or deferred evidence watch. The child issue must use a metadata-only body linking the canonical page and parent issue, state a review cadence or concrete event predicate, carry `kind: source review` and `needs: monitoring`, and remain separate from substantive analysis. Do not create maintenance sub-issues for static citations, ordinary adjacent pages, or every linked source. Close the child issue and remove `needs: monitoring` when the page is retired, absorbed into a nonrecurring record, or no longer requires periodic review.

For the current public-release workflow, `Pre-publication final audit` and `Pre-publication technical` are the parent governance issues. Their detailed work should remain attached through GitHub native sub-issues so the Project board can stay compact while preserving task detail.

## Issue Registry

The repository-side list of all GitHub issues is maintained at [`inventory/github_issue_registry.csv`](../inventory/github_issue_registry.csv). Add or update a row whenever an issue is created, renamed, reclassified, assigned a canonical record, or attached to a different native parent. The registry supplies stable issue-to-record relationships for navigation and future table-of-contents generation. Retain closed merged records in the registry and classify them as `merged proposal` rather than deleting the row or continuing to count them as active `proposal` records.

Do not place live status, priority, labels, scores, audit fields, or release posture in the registry. GitHub Project fields remain authoritative for those values. Creating an issue is incomplete until its registry row and required Project fields both read back correctly.
