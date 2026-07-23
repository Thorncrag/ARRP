---
title: "GitHub Workflow"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# GitHub Workflow

GitHub is the project's authoritative workflow record. Active proposals, horizon proposals, release blockers, publication tasks, and contributor-facing suggestions should be visible as GitHub Issues and, where useful, on the project board.

The repository remains the authoritative substantive record. Proposal text, audit history, inventories, source records, proposed legislation, and framework rules belong in repo files and should be changed through normal repository edits or pull requests.

## CLI Authentication Boundary

The project's local macOS GitHub CLI credential should have one authoritative copy in the macOS Keychain. Sandboxed commands cannot read that credential and may report that the active account or token is invalid even when host-context authentication is healthy. Run authenticated `gh` commands, `gh auth status` diagnostics, GitHub Project synchronization, and authenticated Git network operations in the approved host context. Treat the host-context result as authoritative; do not begin another device authorization solely because a sandboxed diagnostic fails.

Do not use `--insecure-storage` as a workaround or retain a second token in `~/.config/gh/hosts.yml`. A duplicate file-stored token can become stale and recreate the apparent recurring failure. Reauthorize only if `gh auth status` fails in the host context. After authorization, verify that the account is reported as Keychain-backed, required scopes include `repo`, `workflow`, and `project`, `hosts.yml` contains account routing but no `oauth_token`, and a new process can read both the repository API and Project 2.

## Tracking Rule

Each active ARRP proposal or active horizon item should have a GitHub issue. The GitHub issue tracks discussion, assignment, contributor-facing workflow, and links back to the canonical repository record. The GitHub Project tracks structured workflow metadata. The canonical repo file records the adopted substance.

GitHub issues are durable records and should not be deleted unless they were created erroneously. When an issue is merged, integrated, retired, or otherwise adjudicated, close the issue and preserve its stable number, title, links, and disposition record. If no active work remains on that record, remove only its card from the active GitHub Project; removing a Project item does not delete or alter the underlying issue. Preserve the disposition in the Horizon Scan Log, relevant area page, audit sidecar, registry, or other canonical record as applicable. A tracking-only child created solely under the superseded proposal-monitoring convention is an erroneous administrative artifact for this purpose and may be deleted after `needs: monitoring` is confirmed on the existing parent. Its administrative child text need not be migrated because the parent-level pass reviews all associated sources and searches for new developments. This narrow exception does not authorize deletion of a substantive proposal, candidate, evidence, contributor, or adjudication record.

When a Horizon candidate is admitted independently, convert its existing issue into the area-specific proposal issue: assign and retitle it with the new `AREA-###` identifier, replace `kind: horizon` with `kind: proposal`, preserve its original `HOR-###` provenance in the issue body and Horizon Scan Log, update the registry row in place, and keep the issue open. Do not create a duplicate proposal issue. When a Horizon candidate is merged, integrated, retired, or rejected, retain the `HOR-###` prefix, append the precise bracketed disposition, add a dated final-disposition section that supersedes active-intake language, synchronize the registry and Horizon Scan Log, close the issue if no independent work remains, and remove only its Project card. Read back all affected surfaces before closeout.

Milestones should not be assigned automatically to every proposal. A milestone means the issue is an obligation for that release phase. Proposal and horizon issues may remain unmilestoned until they are pulled into a specific release path.

## Project Fields

Use GitHub Project fields as the authoritative structured workflow metadata:

- `Area` identifies the primary ARRP area or governance/export category.
- `Workstream` distinguishes proposal development from project governance and operations.
- `Priority` records the current project priority.
- `Release blocker` records whether the item blocks the active release.
- `Development level` records substantive proposal maturity independently of the next task or temporary hold.
- `Status` records the current workflow action or hold. Monitoring is an independent `needs: monitoring` designation, and inactive completed records leave the active Project rather than using a terminal Status.
- `Score`, `Runs`, `Last audit`, and `Next audit` provide compact audit-status summaries.
- `Rebaseline status` records whether the proposal score is current under the governing rubric or needs a soft/hard rebaseline.
- `Change audit needed` records whether a developed proposal has an unresolved targeted Change Audit / Internal Remedy-Fit Audit marker.
- `Canonical page` links to the repository page or GitHub issue that carries the authoritative substance or active intake record.
- `Parent issue` and `Sub-issues progress` should be used for native GitHub parent/sub-issue tracking where work naturally breaks down into child issues.

Do not duplicate these fields as issue-body metadata or as labels. If a field value changes, update the GitHub Project field directly.

## Issue-Development Lifecycle

The lifecycle check applies whenever the user asks to focus on, research, develop, draft, revise, or otherwise work substantively on an issue. The user does not need to request an audit or separately mention status maintenance.

The substantive `In development` threshold, four-part human-governed foundation, delegated-development authority, uncertainty rule, and tier-readiness guidelines are maintained in [`FRAMEWORK.md`](FRAMEWORK.md#issue-lifecycle-discovery-through-publication-and-maintenance). Agent execution belongs in [`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md) and the registered [`agents/`](agents/) runbooks. This section implements those judgments through GitHub maturity, workflow, and audit-control fields; it does not redefine them. For an unscored proposal, the canonical page's `foundation_status`, `foundation_approved_date`, and concise optional `foundation_approval_note` preserve the human decision or recorded Elim or interactive-agent sufficiency determination supporting `Development level: In development`. Workflow `Status` alone does not establish that foundation.

Use the Project `Development level` options as follows:

- `Candidate` — a formal active `HOR-###` candidate has not yet been admitted as an independent proposal.
- `Admitted / undeveloped` — an area-specific proposal has been admitted, but the four-part foundation or initial proposal architecture remains unresolved.
- `In development` — the institutional failure, at least one manifestation, the remedy, and the remedy vehicle have been established either directly by the human or through a recorded Elim or interactive-agent four-criterion sufficiency determination; development may proceed within that foundation.
- `Developed proposal` — the initial issue-and-vehicle package is complete enough for meaningful T-audit review, or a completed T-audit has assigned a score below Review Ready.
- `Review ready` — the proposal has a score of at least 75 under the current rubric and is strong enough for knowledgeable external critique.
- `Release candidate` — the separate release-candidate requirements have been affirmatively satisfied; a score alone does not establish this level.

Leave `Development level` blank for governance, publication, export, source-review, and other nonproposal Project items. A hold or revision does not automatically reduce an established development level. If the evidence supporting a maturity value is inconsistent, use the lower defensible level and flag the discrepancy for review.

Use exactly these Project `Status` options as workflow states:

- `Research` — active evidence gathering, source development, empirical investigation, or candidate testing is the next workflow. The record is not yet ready for substantive drafting or a human disposition decision. `Next audit` must identify the defined question or investigation.
- `Development` — framing, drafting, structural work, remedy design, implementation development, or revision is the next workflow. Use it whether that work is waiting to begin or already underway; do not toggle Status merely to indicate that a person or agent is active today. Supporting research may occur within development, but use `Research` when investigation is itself the primary next action.
- `Human decision needed` — a specific human-reserved disposition, foundational choice, or other decision is the next action. State the exact question and why an agent may not decide it. Do not use this Status when Elim or an interactive Codex agent has authority to determine four-part foundation sufficiency from the existing canonical record.
- `Audit needed` — a named initial or successive T-audit, Change Audit, Internal Remedy-Fit Audit, or other identified internal review is the next action. The `Next audit` field must identify it.
- `Audit in progress` — a named audit has formally begun and remains incomplete. Preserve the active audit record or checkpoint and replace this Status when the audit closes or stops.
- `External review` — qualified outside critique or validation is currently being sought or conducted. Record the reviewer type and review scope; once feedback is received, assign the next workflow it actually creates.
- `Publication approval` — a release candidate is ready for the final human go/no-go decision authorizing circulation or publication. Do not use it as a general production, editing, or publication-development queue.
- `Deferred` — the project has affirmatively decided to postpone further development even though work could proceed, because proceeding now would be premature, unusually nuanced, dependent on broader expertise, or otherwise inadvisable. Record why the project is postponing the work and the condition or date for reconsideration. A canonical page must state both in its nonblank `workflow_hold_reason`.
- `Blocked` — intended work cannot proceed because a concrete, indispensable prerequisite is unavailable. Record the blocked action, the missing prerequisite, and the event that will unblock it. A canonical page must state all three in its nonblank `workflow_hold_reason`. A `Release blocker` value does not imply `Status: Blocked`, and a missing human-reserved choice uses `Human decision needed`.

No other Status values are authoritative. `Development level: In development` remains a separate substantive maturity value; it is not a workflow Status.

Do not confuse the GitHub Project `Status` field with lowercase `status` in canonical issue-page front matter. Every issue page must carry a nonblank front-matter `status` using the issue-page metadata vocabulary `awaiting-decision`, `awaiting-merits-adjudication`, `blocked`, `candidate`, `deferred`, `developed`, `in-development`, or `retired`. That field describes the page's substantive or disposition posture; it does not replace, duplicate, or expand the Project workflow vocabulary. Missing, blank, or non-standard issue-page values are integrity findings, and Project Status values should not be copied into the page field merely because their wording is similar.

At the start of substantive work, read the current Project row, canonical page, linked vehicle, latest audit record, next step, any required `workflow_hold_reason`, and any `needs: monitoring` explanation. Do not change Status merely because a work session starts or stops. If ordinary development is next, use `Status: Development`. Do not reduce `Development level` merely because material revision begins; preserve its established maturity and set `Change audit needed` and the Status identifying the actual next action or hold until the targeted review is resolved.

At closeout, synchronize both fields. An incomplete package with an approved foundation remains at `Development level: In development`; use `Status: Research` when a defined investigation is next and `Status: Development` when framing, drafting, structural, remedy-design, or revision work is next. Move an unscored audit-ready package to `Development level: Developed proposal` and `Status: Audit needed`; after a completed T-audit, update the development level from the score band and use Status for the actual next action. A score of at least 75 ordinarily uses `Development level: Review ready` and `Status: External review`; a qualified release candidate uses `Status: Publication approval` only when final human authorization is next. Research, drafting, source development, status review, Change Audits, and other non-T-audit work do not change `Score` or increment `Runs`.

The **Runs** field counts only completed and separately recorded T0, T1, T2, T3, or T4 issue-quality audits. Do not increment it for Change Audits, Internal Remedy-Fit Audits, Horizon Scans, source development, drafting, formatting reviews, predicate checks, external-review intake, validation or dashboard reruns, bookkeeping, or continuation of the same open tier. A cumulative T4 is one run unless lower tiers were separately completed and recorded; a successive multi-tier sequence counts each tier actually completed and separately memorialized.

A closed adjudicated record or completed governance item with no active obligation should leave the active Project instead of occupying a terminal-status card. Preserve the underlying issue and canonical disposition record; do not delete a substantive issue merely because its Project card is removed.

Project-field updates are not optional bookkeeping. When audit or development work changes a proposal's development level, workflow status, score, run count, last-audit note, next-audit note, rebaseline status, change-audit marker, priority, release-blocker posture, or canonical page, the corresponding GitHub Project row must be updated before the task is reported complete. If the agent cannot update a Project field, it must tell the user immediately, identify the affected issue and field values, preserve the repo work, and either fix the Project access problem with the user or report the work as partially complete. The issue body may carry a temporary snapshot, but the Project fields remain authoritative.

After updating a GitHub issue wrapper or GitHub Project row for a maturity, workflow, or audit-control change, perform a readback before closeout. The readback should verify development level, status, score, run count, last audit, next audit, rebaseline status, change-audit flag, canonical page, and release-blocker posture where those fields are in scope. Do not report the task complete until any mismatch is corrected or explicitly disclosed as a blocked sync item.

Use these options for audit-control fields:

- `Rebaseline status`: `Current`, `Current fixed status`, `Soft rebaseline needed`, `Hard rebaseline needed`, `Rebaseline complete`, `Not applicable`, `Unknown`.
- `Change audit needed`: `No`, `Yes`, `Pending review`, `Blocked`.

## Project Console Progress

The **Progress** tab in the internal [ARRP Project Console](../research/horizon-review-console/index.html) is the sole human-facing planning view derived from the GitHub Project. It measures proposal records in the issue registry against the Review Ready goal without closing issues, assigning artificial milestones, or adding daily generated commits to `main`. Automation retains only machine-readable progress and history on the data-only `project-console-data` branch; it does not publish a second Markdown dashboard.

The Project `Development level` field is the substantive maturity authority; `Status` remains the workflow authority. The dashboard requires both `Development level: Review ready` or `Release candidate` and a score of at least 75 for goal attainment, and it may detect but must not silently repair maturity/score drift. Governance, horizon, source-review, and other non-proposal items are excluded from the Review Ready denominator. Newly admitted proposal issues enlarge the tracked scope automatically and must be reported as scope change rather than hidden by resetting the baseline.

The progress view's registry-based eligibility rule, readiness statuses, baseline, target date, forecast window, and Project field mappings are maintained in [`.github/project-console-progress.json`](../.github/project-console-progress.json). The proposal identifier in the built-in Project `Title` joins each active proposal to its registry record, with `Canonical page` used only as a unique fallback; unmatched or ambiguous proposals remain visible as tracking warnings. The governing definitions, metrics, data-only retention boundary, and change-control rules are documented in [`PROJECT_CONSOLE_PROGRESS.md`](PROJECT_CONSOLE_PROGRESS.md). Changes to eligibility, the readiness rule, or the official target require a project-level Change Audit.

## Public Website

The public website uses GitHub Pages without a second repository or publication branch. The repository's `main` branch remains canonical, while [`.github/workflows/public-site.yml`](../.github/workflows/public-site.yml) builds and deploys only an allowlisted artifact. The publication boundary, local validation commands, and deployment design are maintained in [`../website/README.md`](../website/README.md).

Every admitted page must both declare `public-proposal` in `print_levels` and fall within the approved root-page, `areas/`, `legislation/`, or `topics/` path boundary. The build must fail rather than silently expand that boundary. Internal framework, audit, Project, unpublished research, retained-source, inventory, archive, test, script, export, secret, and repository-administration materials remain outside the artifact. A project-authored analysis selected for public topic treatment must move into `topics/` rather than remain duplicated in `research/`. A future decision to publish another excluded class requires an explicit publication-policy change and project-level Change Audit.

## Labels

Use labels sparingly. Labels should not duplicate Project fields.

- `kind:*` labels identify the type of issue, such as `kind: proposal` or `kind: horizon`.
- `needs: monitoring` identifies an external development that is materially relevant to an issue's future development while the underlying issue and permissible work remain regardless of what happens externally. It must not replace the Project `Status` field or imply that work must wait. The existing parent issue wrapper must state the matter being watched, why it is materially relevant, what development triggers reassessment, and how the project will check for it. Remove the label when no continuing monitoring need remains.
- Temporary labels may be used for ad hoc contributor triage only when no existing Project field captures the need.
- Do not use `area:*`, `priority:*`, `stage:*`, `status:*`, or `release:*` labels unless the Project field model is deliberately changed.

## Sub-Issues

Use GitHub native sub-issues rather than Markdown task lists when a governance, release, audit, or publication item has meaningful child tasks. Parent issues should describe the umbrella objective and completion standard. Child issues should carry the executable work and close independently.

A living repository surface may receive a maintenance sub-issue when it has a genuine recurring review obligation, such as an agency or event catalog, election dataset, litigation tracker, legislation survey, recurring crosswalk, or defined evidence watch. The child issue must use a metadata-only body linking the canonical page and parent issue, state a review cadence or concrete event predicate, carry `kind: source review` and `needs: monitoring`, and remain separate from substantive analysis. Do not create maintenance sub-issues for static citations, ordinary adjacent pages, or every linked source. Close the child issue and remove `needs: monitoring` when the page is retired, absorbed into a nonrecurring record, or no longer requires periodic review.

### Issue-Specific Monitoring

Monitor a proposal or formal Horizon candidate on its existing GitHub issue. Apply `needs: monitoring` only when an external development is being watched, it is materially relevant to future development of the issue, and useful issue work may continue because the underlying issue remains regardless of the external outcome. Preserve the parent issue's Project development level, ordinary workflow Status, canonical page, Area, and workstream. Do not create a monitoring-only child issue. The label indicates that a project-wide pass must revisit the whole issue; it does not establish a new proposal, source record, or workflow identity.

The parent issue is the monitoring-workflow record. Its wrapper must identify the external matter being watched, why it is materially relevant to future issue development, the development that triggers reassessment, and the checking method. After each pass, retain a concise dated result or link to the resulting project change. A monitoring pass reviews every source associated with the issue in both source catalogs and performs an active search for material new developments; it is not limited to sources individually marked for monitoring. Remove `needs: monitoring` only when no defined continuing need remains. The proposal's repository issue page stays focused on the substantive analysis and does not receive a generic administrative monitoring link or section.

Monitoring, deferral, and blockage are mutually exclusive classifications for this purpose. If useful issue work can continue while the external matter is watched, retain the ordinary Status and use `needs: monitoring`. If work could proceed but the project has affirmatively decided it should not, use `Deferred` and record the reason and reconsideration condition or date. If intended work cannot proceed because the external event or another concrete prerequisite is indispensable, use `Blocked` and record the blocked action, prerequisite, and unblock trigger in `workflow_hold_reason` and `Next audit`; do not apply `needs: monitoring` merely to watch for that trigger. If the missing prerequisite is a human-reserved choice, use `Human decision needed`.

Individual external sources may independently warrant recurring checking, especially live dockets, rolling agency pages, or other changing official records. Record that source-level fact through the `Monitoring` field in `sources.csv` or `sources-pending.csv`. A `Yes` value helps identify which sources support recurring checks, but it neither applies the issue label nor narrows an issue-wide monitoring pass. News coverage and other static records ordinarily use `No` unless the record itself is expected to change materially.

A matter relevant to several proposals has one primary analytic home and any number of affected-issue associations. Each affected parent may carry `needs: monitoring` when the matter could materially affect its own analysis. Keep detailed evidence at its primary issue or evidence record and use tailored cross-references rather than duplicating case history. General GitHub sub-issues remain available for genuinely independent governance, release, audit, publication, dataset, catalog, or other maintenance work with separately completable obligations; they are not used merely to represent proposal monitoring.

The Project should maintain a dedicated **Monitoring** view filtered primarily to `needs: monitoring`. A project-wide monitoring pass reviews each labeled parent issue, checks all associated sources, searches for new developments, records the dated result on that parent, updates source inventory and evidence placement as needed, and removes the label when monitoring is no longer warranted. A material result requires the ordinary targeted Change Audit and Internal Remedy-Fit review.

The authoritative deterministic monitoring configurations and authority boundaries are maintained in the [Case Monitor Bot](agents/CASE_MONITOR_BOT.md) and [Presidential Directives Bot](agents/PRESIDENTIAL_DIRECTIVES_BOT.md) runbooks. Their GitHub implementations use dedicated automation branches and narrow owner-assigned pull requests. Merging such a pull request accepts the proposed machine-observed baseline; the bot may not merge it. A material action records both the applicable domain event and shared Agent Audit Log provenance. A no-change run remains only in Actions and bounded Console history.

The ARRP Project Console places issue-level **Issues being monitored** under **Progress** and reserves **Sources** for Court Cases, Presidential Directives, and Source Checks. Routine monitoring does not enter the human **Action Items** count merely because a monitoring designation remains present. Action Items link only a resulting decision, exception, detected update, unresolved routing choice, missing required explanation or reason, or other matter requiring human attention. These views may link GitHub issues, source records, run history, open bot-review pull requests, domain event records, and the shared Agent Audit Log, but they do not invoke a bot or mutate GitHub.

For the current public-release workflow, `Pre-publication final audit` and `Pre-publication technical` are the parent governance issues. Their detailed work should remain attached through GitHub native sub-issues so the Project board can stay compact while preserving task detail.

## Issue Registry

The repository-side list of all GitHub issues is maintained at [`inventory/github_issue_registry.csv`](../inventory/github_issue_registry.csv). Add or update a row whenever an issue is created, renamed, reclassified, assigned a canonical record, or attached to a different parent. The registry supplies stable issue-to-record relationships for navigation and future table-of-contents generation. Treat the repository front door, registry, affected contents, and Subject and Institution Index as a navigation bundle under the methodology's T1 Navigation Synchronization Check. Retain closed merged records in the registry as `merged proposal` and closed independently rejected, retired, or outside-scope records as `retired proposal` rather than deleting the row or continuing to count either kind as active `proposal` records.

Do not place live status, priority, labels, scores, audit fields, or release posture in the registry. GitHub Project fields remain authoritative for those values. Creating an admitted or otherwise reader-facing issue is incomplete until its registry row, required Project fields, area contents entry, and affected Subject and Institution Index routes all read back correctly. A newly triaged but unadmitted Horizon candidate remains in the Horizon workflow and should not be added to the reader-facing contents or subject index.
