---
title: "GitHub Workflow"
print_levels:
  - full-technical
---

# GitHub Workflow

GitHub is the project's authoritative workflow record. Active proposals, horizon proposals, release blockers, publication tasks, and contributor-facing suggestions should be visible as GitHub Issues and, where useful, on the project board.

The repository remains the authoritative substantive record. Proposal text, audit history, inventories, source records, proposed legislation, and framework rules belong in repo files and should be changed through normal repository edits or pull requests.

## CLI Authentication Boundary

The project's local macOS GitHub CLI credential should have one authoritative copy in the macOS Keychain. Sandboxed commands cannot read that credential and may report that the active account or token is invalid even when host-context authentication is healthy. Run authenticated `gh` commands, `gh auth status` diagnostics, GitHub Project synchronization, and authenticated Git network operations in the approved host context. Treat the host-context result as authoritative; do not begin another device authorization solely because a sandboxed diagnostic fails.

Do not use `--insecure-storage` as a workaround or retain a second token in `~/.config/gh/hosts.yml`. A duplicate file-stored token can become stale and recreate the apparent recurring failure. Reauthorize only if `gh auth status` fails in the host context. After authorization, verify that the account is reported as Keychain-backed, required scopes include `repo`, `workflow`, and `project`, `hosts.yml` contains account routing but no `oauth_token`, and a new process can read both the repository API and Project 2.

## Tracking Rule

Each active ARRP proposal or active horizon item should have a GitHub issue. The GitHub issue tracks discussion, assignment, contributor-facing workflow, and links back to the canonical repository record. The GitHub Project tracks structured workflow metadata. The canonical repo file records the adopted substance.

GitHub issues are durable records and should not be deleted unless they were created erroneously. When an issue is merged, integrated, retired, or otherwise adjudicated, close the issue and preserve its stable number, title, links, and disposition record. If no active work remains on that record, remove only its card from the active GitHub Project; removing a Project item does not delete or alter the underlying issue. Preserve the disposition in the Horizon Scan Log, relevant area page, audit sidecar, registry, or other canonical record as applicable.

When a Horizon candidate is admitted independently, convert its existing issue into the area-specific proposal issue: assign and retitle it with the new `AREA-###` identifier, replace `kind: horizon` with `kind: proposal`, preserve its original `HOR-###` provenance in the issue body and Horizon Scan Log, update the registry row in place, and keep the issue open. Do not create a duplicate proposal issue. When a Horizon candidate is merged, integrated, retired, or rejected, retain the `HOR-###` prefix, append the precise bracketed disposition, add a dated final-disposition section that supersedes active-intake language, synchronize the registry and Horizon Scan Log, close the issue if no independent work remains, and remove only its Project card. Read back all affected surfaces before closeout.

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

## Issue-Development Lifecycle

The lifecycle check applies whenever the user asks to focus on, research, develop, draft, revise, or otherwise work substantively on an issue. The user does not need to request an audit or separately mention status maintenance.

Use the Project `Status` options as follows:

- `Candidate issue` — an active candidate has not yet been admitted as an independent proposal.
- `Monitoring` — an active `ISSUE-ID-MON` source-review sub-issue is waiting on a defined external development. It is not a lifecycle status for the parent proposal.
- `Pending development` — an admitted proposal is not in active drafting and does not yet have a complete initial issue-and-vehicle package.
- `In development` — substantive work is active or the initial issue-and-vehicle package remains incomplete. A completed T-audit score of 1–49 also uses this status because the available Project vocabulary intentionally consolidates both Early/Partial Draft score bands.
- `Audit needed` — an unscored initial issue page and concrete proposal vehicle are complete enough for the next T-audit. The status does not itself assign a score or increment `Runs`.
- `Developed draft` — a completed score-bearing T-audit produces a score of 50–74. The exact issue-page threshold label remains `Developed Draft` at 50–64 and `Substantially Developed Draft` at 65–74.
- `Review ready` and higher — use the score bands and release rules in the methodology.
- `Deferred / Parked`, `Blocked`, and `Completed within scope` — use only when their stated routing or terminal conditions actually apply.

At the start of substantive work, read the current Project row, canonical page, linked vehicle, latest audit record, and next step. If work begins from `Pending development`, move the item to `In development` and read back the change. Do not regress an already scored or later-stage proposal merely because material revision begins; preserve its score-based status and set `Change audit needed` as required until the targeted review is resolved.

At closeout, keep an incomplete initial package `In development`; move an unscored initial package with a sufficiently complete issue page and concrete vehicle to `Audit needed`; or apply the score-based lifecycle status after a completed T-audit. Research, drafting, source development, status review, Change Audits, and other non-T-audit work do not change `Score` or increment `Runs`.

The **Runs** field counts only completed and separately recorded T0, T1, T2, T3, or T4 issue-quality audits. Do not increment it for Change Audits, Internal Remedy-Fit Audits, Horizon Scans, source development, drafting, formatting reviews, predicate checks, external-review intake, validation or dashboard reruns, bookkeeping, or continuation of the same open tier. A cumulative T4 is one run unless lower tiers were separately completed and recorded; a successive multi-tier sequence counts each tier actually completed and separately memorialized.

Use `Completed within scope` only when the item's defined obligation is actually complete. Do not use it as a substitute for `Merged`, `Integrated`, `Retired`, another archival disposition, or merely publishing an unfinished item. A closed adjudicated record with no active work should ordinarily leave the active Project instead of occupying a misleading terminal-status card.

Project-field updates are not optional bookkeeping. When audit work changes a proposal's score, status, run count, last-audit note, next-audit note, rebaseline status, change-audit marker, priority, release-blocker posture, or canonical page, the corresponding GitHub Project row must be updated before the task is reported complete. If the agent cannot update a Project field, it must tell the user immediately, identify the affected issue and field values, preserve the repo work, and either fix the Project access problem with the user or report the work as partially complete. The issue body may carry a temporary snapshot, but the Project field remains the authoritative workflow tracker.

After updating a GitHub issue wrapper or GitHub Project row for an issue-status or audit-control change, perform a readback before closeout. The readback should verify that the GitHub issue body and Project fields match the repository issue metadata for status, score, run count, last audit, next audit, rebaseline status, change-audit flag, canonical page, and release-blocker posture where those fields are in scope. Do not report the task complete until any mismatch is corrected or explicitly disclosed as a blocked sync item.

Use these options for audit-control fields:

- `Rebaseline status`: `Current`, `Current fixed status`, `Soft rebaseline needed`, `Hard rebaseline needed`, `Rebaseline complete`, `Not applicable`, `Unknown`.
- `Change audit needed`: `No`, `Yes`, `Pending review`, `Blocked`.

## Review Ready Progress Dashboard

The [ARRP Review Ready Progress Dashboard](https://github.com/Thorncrag/ARRP/blob/progress-dashboard/PROGRESS.md) is a read-only planning view derived from the GitHub Project and generated on a dedicated branch. It measures proposal records in the GitHub issue registry against the project's current Review Ready goal without closing proposal issues, assigning artificial milestones, creating tracking-only issues, or adding daily generated commits to `main`. The branch may be viewed by a reader who deliberately browses the public repository, but it is excluded from the public website, website navigation, search index, and sitemap.

The Project `Status` field remains the lifecycle authority. The dashboard may use `Score` to detect status/score drift, but it must not infer or write a new status from the score alone. Governance, horizon, source-review, and other non-proposal items are excluded. Newly admitted proposal issues enlarge the tracked scope automatically and must be reported as scope change rather than hidden by resetting the baseline.

The dashboard's registry-based eligibility rule, readiness statuses, baseline, target date, forecast window, and Project field mappings are maintained in [`.github/progress-dashboard.json`](../.github/progress-dashboard.json). The proposal identifier in the built-in Project `Title` joins each active proposal to its registry record, with `Canonical page` used only as a unique fallback; unmatched or ambiguous proposals remain visible as tracking warnings. The governing definitions, metrics, forecast limits, credential boundary, and change-control rules are documented in [`PROGRESS_DASHBOARD.md`](PROGRESS_DASHBOARD.md). Changes to eligibility, the readiness rule, or the official target require a project-level Change Audit.

## Public Website

The public website uses GitHub Pages without a second repository or publication branch. The repository's `main` branch remains canonical, while [`.github/workflows/public-site.yml`](../.github/workflows/public-site.yml) builds and deploys only an allowlisted artifact. The publication boundary, local validation commands, and deployment design are maintained in [`../website/README.md`](../website/README.md).

Every admitted page must both declare `public-proposal` in `print_levels` and fall within the approved root-page, `areas/`, `legislation/`, or `topics/` path boundary. The build must fail rather than silently expand that boundary. Internal framework, audit, Project, unpublished research, retained-source, inventory, archive, test, script, export, secret, and repository-administration materials remain outside the artifact. A project-authored analysis selected for public topic treatment must move into `topics/` rather than remain duplicated in `research/`. A future decision to publish another excluded class requires an explicit publication-policy change and project-level Change Audit.

## Labels

Use labels sparingly. Labels should not duplicate Project fields.

- `kind:*` labels identify the type of issue, such as `kind: proposal` or `kind: horizon`.
- `needs: monitoring` identifies an evidence- or event-dependent item whose next substantive step requires an investigation, litigation development, documentary disclosure, scheduled event, or other defined follow-up predicate. It must not replace the Project `Status` field; the canonical record should state what development will trigger renewed review, and the label should be removed when that predicate is resolved.
- Temporary labels may be used for ad hoc contributor triage only when no existing Project field captures the need.
- Do not use `area:*`, `priority:*`, `stage:*`, `status:*`, or `release:*` labels unless the Project field model is deliberately changed.

## Sub-Issues

Use GitHub native sub-issues rather than Markdown task lists when a governance, release, audit, or publication item has meaningful child tasks. Parent issues should describe the umbrella objective and completion standard. Child issues should carry the executable work and close independently.

A living repository surface may receive a maintenance sub-issue when it has a genuine recurring review obligation, such as an agency or event catalog, election dataset, litigation tracker, legislation survey, recurring crosswalk, or deferred evidence watch. The child issue must use a metadata-only body linking the canonical page and parent issue, state a review cadence or concrete event predicate, carry `kind: source review` and `needs: monitoring`, and remain separate from substantive analysis. Do not create maintenance sub-issues for static citations, ordinary adjacent pages, or every linked source. Close the child issue and remove `needs: monitoring` when the page is retired, absorbed into a nonrecurring record, or no longer requires periodic review.

### Issue-Specific Monitoring Records

When a live proposal has one coherent body of external matters awaiting a ruling, agency action, disclosure, scheduled event, or other defined predicate, create one native monitoring sub-issue named `ISSUE-ID-MON`, for example `DOJ-001-MON: DOJ-001 External Developments Watch`. It is the GitHub workflow wrapper for that proposal's monitoring work, not a new substantive proposal or a separate source record.

Set the monitoring sub-issue's Project `Status` to `Monitoring`; apply `kind: source review` and `needs: monitoring`; set the proposal as its native GitHub parent; and use the parent proposal's Area and ordinary proposal-development workstream. The monitor body must state its parent, the primary evidence record or source inventory location, the monitored matters or a concise grouped index, their current posture, the last checked date, and the defined reassessment trigger. The `Canonical page` field points to the monitoring issue itself.

The parent issue page stays concise. When a monitor or a qualitatively warranted evidence record exists, add one short **Supporting Record and Updates** subsection at the end of **Manifestation of the Failure**. It should link to the `ISSUE-ID-MON` record as **Watching for updates** and, when an evidence record exists, link to it as **Additional supporting record**. State that monitoring tracks pending external developments without changing the proposal's current analysis. Omit a missing link; never create a placeholder. The evidence record holds the detailed account of individual cases or actions. The source inventory and monitoring ledger retain source IDs, primary and affected proposal routes, exact posture, source links, and checking history.

A matter relevant to several proposals has one primary analytic home and any number of affected-issue links. Treat the primary monitor or evidence record as the detailed account; affected issue pages and monitoring records should cross-reference it with a tailored explanation rather than duplicate the case history. Do not create one monitor sub-issue per lawsuit, one monitor per raw source, or duplicate native sub-issues solely because a matter has more than one affected proposal. Create a second `ISSUE-ID-MON-02` record only when a distinct, long-lived monitoring stream cannot be managed coherently within the original monitor.

Horizon candidates remain their own active monitoring records while unadmitted. Do not create `HOR-###-MON` merely to duplicate an active Horizon issue carrying `needs: monitoring`.

The Project should maintain a dedicated **Monitoring** view filtered to `Status: Monitoring` and/or `needs: monitoring`. A project-wide monitoring pass reviews every open monitor in that view, refreshes the external posture and last-checked date, updates its source inventory and evidence placement, performs a targeted Change Audit when a result materially changes a developed proposal, and closes/removes resolved monitors without deleting their GitHub issues.

For the current public-release workflow, `Pre-publication final audit` and `Pre-publication technical` are the parent governance issues. Their detailed work should remain attached through GitHub native sub-issues so the Project board can stay compact while preserving task detail.

## Issue Registry

The repository-side list of all GitHub issues is maintained at [`inventory/github_issue_registry.csv`](../inventory/github_issue_registry.csv). Add or update a row whenever an issue is created, renamed, reclassified, assigned a canonical record, or attached to a different parent. The registry supplies stable issue-to-record relationships for navigation and future table-of-contents generation. Treat the repository front door, registry, affected contents, and Subject and Institution Index as a navigation bundle under the methodology's T1 Navigation Synchronization Check. Retain closed merged records in the registry as `merged proposal` and closed independently rejected, retired, or outside-scope records as `retired proposal` rather than deleting the row or continuing to count either kind as active `proposal` records.

Do not place live status, priority, labels, scores, audit fields, or release posture in the registry. GitHub Project fields remain authoritative for those values. Creating an admitted or otherwise reader-facing issue is incomplete until its registry row, required Project fields, area contents entry, and affected Subject and Institution Index routes all read back correctly. A newly triaged but unadmitted Horizon candidate remains in the Horizon workflow and should not be added to the reader-facing contents or subject index.
