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
- `Status` records lifecycle and workflow position.
- `Score`, `Runs`, `Last audit`, and `Next audit` provide compact audit-status summaries.
- `Rebaseline status` records whether the proposal score is current under the governing rubric or needs a soft/hard rebaseline.
- `Change audit needed` records whether a developed proposal has an unresolved targeted Change Audit / Internal Remedy-Fit Audit marker.
- `Canonical page` links to the repository page or GitHub issue that carries the authoritative substance or active intake record.
- `Parent issue` and `Sub-issues progress` should be used for native GitHub parent/sub-issue tracking where work naturally breaks down into child issues.

Do not duplicate these fields as issue-body metadata or as labels. If a field value changes, update the GitHub Project field directly.

## Issue-Development Lifecycle

The lifecycle check applies whenever the user asks to focus on, research, develop, draft, revise, or otherwise work substantively on an issue. The user does not need to request an audit or separately mention status maintenance.

The substantive lifecycle, Defined Proposal threshold, four-part human-governed foundation, delegated-development authority, uncertainty rule, tier-readiness guidelines, and recurring autonomous work order are maintained in [`FRAMEWORK.md`](FRAMEWORK.md#issue-lifecycle-discovery-through-publication-and-maintenance). This section implements those judgments through GitHub status and audit-control fields; it does not redefine them. `Defined Proposal` is not a separate Project status: the ordinary `Pending development`, `In development`, `Audit needed`, and score-derived statuses continue to describe operational position. For an unscored issue, the canonical page's `foundation_status`, `foundation_approved_date`, and optional `foundation_approval_note` preserve the human approval that makes scheduled development permissible; GitHub status alone does not establish that approval.

Use the Project `Status` options as follows:

- `Candidate issue` — an active candidate has not yet been admitted as an independent proposal.
- `Monitoring` — an independently managed non-proposal research, governance, or maintenance item is waiting on a defined external development. Proposal and Horizon monitoring does not use this status; the existing parent issue retains its ordinary lifecycle status and carries `needs: monitoring`.
- `Pending development` — an admitted proposal is not in active drafting and does not yet have a complete initial issue-and-vehicle package.
- `In development` — substantive work is active or the initial issue-and-vehicle package remains incomplete. A completed T-audit score of 1–49 also uses this status because the available Project vocabulary intentionally consolidates both Early/Partial Draft score bands.
- `Audit needed` — an unscored initial issue page and concrete proposal vehicle are complete enough for the next T-audit. The status does not itself assign a score or increment `Runs`.
- `Developed draft` — a completed score-bearing T-audit produces a score of 50–74. The exact issue-page threshold label remains `Developed Draft` at 50–64 and `Substantially Developed Draft` at 65–74.
- `Review ready` — use for a score of 75 or higher unless the item has separately entered the release-candidate workflow. The issue page preserves the more precise `Review Ready`, `Advanced Review Ready`, `Proposal Ready`, `Publication Ready`, or `Fully Validated` score-band label.
- `Release candidate` — use only when the separate release rules are satisfied; a high score alone does not establish release-candidate status.
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

## Project Console Progress

The **Progress** tab in the internal [ARRP Project Console](../research/horizon-review-console/index.html) is the sole human-facing planning view derived from the GitHub Project. It measures proposal records in the issue registry against the Review Ready goal without closing issues, assigning artificial milestones, or adding daily generated commits to `main`. Automation retains only machine-readable progress and history on the data-only `project-console-data` branch; it does not publish a second Markdown dashboard.

The Project `Status` field remains the lifecycle authority. The dashboard may use `Score` to detect status/score drift, but it must not infer or write a new status from the score alone. Governance, horizon, source-review, and other non-proposal items are excluded. Newly admitted proposal issues enlarge the tracked scope automatically and must be reported as scope change rather than hidden by resetting the baseline.

The progress view's registry-based eligibility rule, readiness statuses, baseline, target date, forecast window, and Project field mappings are maintained in [`.github/project-console-progress.json`](../.github/project-console-progress.json). The proposal identifier in the built-in Project `Title` joins each active proposal to its registry record, with `Canonical page` used only as a unique fallback; unmatched or ambiguous proposals remain visible as tracking warnings. The governing definitions, metrics, data-only retention boundary, and change-control rules are documented in [`PROJECT_CONSOLE_PROGRESS.md`](PROJECT_CONSOLE_PROGRESS.md). Changes to eligibility, the readiness rule, or the official target require a project-level Change Audit.

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

### Issue-Specific Monitoring

Monitor a proposal or formal Horizon candidate on its existing GitHub issue. Apply `needs: monitoring` to that parent issue and preserve its ordinary Project lifecycle status, canonical page, Area, and workstream. Do not create a monitoring-only child issue. The label indicates that a project-wide pass must revisit the whole issue; it does not establish a new proposal, source record, or workflow identity.

The parent issue is the monitoring-workflow record. Its wrapper should state the present reason for monitoring and, after each pass, retain a concise dated result or link to the resulting project change. A monitoring pass reviews every source associated with the issue in both source catalogs and performs an active search for material new developments; it is not limited to sources individually marked for monitoring. Remove `needs: monitoring` only when no defined continuing need remains. The proposal's repository issue page stays focused on the substantive analysis and does not receive a generic administrative monitoring link or section.

Individual external sources may independently warrant recurring checking, especially live dockets, rolling agency pages, or other changing official records. Record that source-level fact through the `Monitoring` field in `sources.csv` or `sources-pending.csv`. A `Yes` value helps identify which sources support recurring checks, but it neither applies the issue label nor narrows an issue-wide monitoring pass. News coverage and other static records ordinarily use `No` unless the record itself is expected to change materially.

A matter relevant to several proposals has one primary analytic home and any number of affected-issue associations. Each affected parent may carry `needs: monitoring` when the matter could materially affect its own analysis. Keep detailed evidence at its primary issue or evidence record and use tailored cross-references rather than duplicating case history. General GitHub sub-issues remain available for genuinely independent governance, release, audit, publication, dataset, catalog, or other maintenance work with separately completable obligations; they are not used merely to represent proposal monitoring.

The Project should maintain a dedicated **Monitoring** view filtered primarily to `needs: monitoring`. A project-wide monitoring pass reviews each labeled parent issue, checks all associated sources, searches for new developments, records the dated result on that parent, updates source inventory and evidence placement as needed, and removes the label when monitoring is no longer warranted. A material result requires the ordinary targeted Change Audit and Internal Remedy-Fit review.

The `case-monitor-bot` is scheduled daily at approximately midnight Eastern (12:17 a.m. EDT / 11:17 p.m. EST) and retains manual dispatch. It makes one respectful retrieval of the [Just Security Trump-administration litigation tracker](https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/), validates the tracker structure, and compares only cataloged `Monitoring = Yes` sources that can be mapped to stable tracker entries. Each covered source stores its accepted fingerprint in `Monitoring Baseline`. The watcher detects later changes to those mapped records; separate source-intake and project-wide monitoring scans remain responsible for entirely new or unmatched cases. A structurally incomplete, ambiguous, or implausibly reduced response fails closed.

When a changed mapped tracker entry links a CourtListener docket, the bot may use the CourtListener REST API to verify a narrow set of docket metadata for that changed source only. `COURTLISTENER_API_TOKEN` is optional: without it, the tracker comparison still succeeds and the affected source is reported as awaiting docket verification. Verification is conservatively capped and paced. Just Security's deliberate exclusions, grouped matters, selective case families, and editorial lag remain documented coverage limitations requiring the project-wide human monitoring pass.

On a material change, the bot updates only the authorized machine-observed fields on a dedicated automation branch, appends one stable-coded entry to the [Source Monitor Log](logs/SOURCE_MONITOR_LOG.md), and creates or updates a narrow pull request assigned to the project owner. The pull request identifies each affected `SRC-####`, the observed change, and the originating Actions run. GitHub's assignment notification supplies the review notice; no operational issue or temporary review label is used. Merging the pull request accepts the proposed per-source baseline. A no-change run creates no repository commit, log entry, or pull request and remains visible only in the Actions summary and retained artifact. A failed retrieval, structural check, or missing accepted baseline fails the workflow. Deterministic watcher events recorded in the Source Monitor Log are not duplicated in the Agent Audit Log. The bot cannot interpret a filing, decide that an issue requires revision, remove `needs: monitoring`, alter Project fields, revise project prose, create a candidate, or change a proposal's status, score, audit count, or remedy.

The ARRP Project Console consolidates monitoring presentation in the read-only **Watchers and bots** view under **Sources**, with Court Cases, Presidential Directives, and Issues being monitored subviews. Routine issue monitoring remains there for automated LLM-assisted review and does not enter the human **Action Items** count merely because `needs: monitoring` remains present. Action Items links only a resulting decision, exception, detected update, unresolved routing choice, or other matter requiring human attention back to its complete owning view. These views may link GitHub issues, source records, watcher coverage, Actions runs, open bot-review pull requests, and the material-change log, but they do not invoke a bot or mutate GitHub. Neutral badges state full queue size; a separate gold badge may count an unresolved new or changed record detected from the directive registry or an open deterministic-watcher pull request. The scheduled presidential-directives watcher also permits manual dispatch. It compares the registry's accepted `Content Fingerprint` and `Last Changed` values with official metadata; a material deterministic change may update those fields on a dedicated branch, append a stable-coded Source Monitor Log entry, and create or update a pull request assigned to the project owner. No-change runs remain in Actions, failures fail closed, and LLM-assisted review retains all substantive disposition authority. Merging the pull request accepts the proposed directive baseline.

For the current public-release workflow, `Pre-publication final audit` and `Pre-publication technical` are the parent governance issues. Their detailed work should remain attached through GitHub native sub-issues so the Project board can stay compact while preserving task detail.

## Issue Registry

The repository-side list of all GitHub issues is maintained at [`inventory/github_issue_registry.csv`](../inventory/github_issue_registry.csv). Add or update a row whenever an issue is created, renamed, reclassified, assigned a canonical record, or attached to a different parent. The registry supplies stable issue-to-record relationships for navigation and future table-of-contents generation. Treat the repository front door, registry, affected contents, and Subject and Institution Index as a navigation bundle under the methodology's T1 Navigation Synchronization Check. Retain closed merged records in the registry as `merged proposal` and closed independently rejected, retired, or outside-scope records as `retired proposal` rather than deleting the row or continuing to count either kind as active `proposal` records.

Do not place live status, priority, labels, scores, audit fields, or release posture in the registry. GitHub Project fields remain authoritative for those values. Creating an admitted or otherwise reader-facing issue is incomplete until its registry row, required Project fields, area contents entry, and affected Subject and Institution Index routes all read back correctly. A newly triaged but unadmitted Horizon candidate remains in the Horizon workflow and should not be added to the reader-facing contents or subject index.
