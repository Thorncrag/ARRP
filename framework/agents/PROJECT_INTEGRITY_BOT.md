---
title: "Project Integrity Bot Runbook"
agent_id: project-integrity-bot
display_name: Project Integrity Bot
agent_type: deterministic-bot
status: enabled
trigger: run-chain-manual-and-main-push
schedule: "Final deterministic stage of every Run Coordinator chain; no independent schedule"
runtime_id: .github/workflows/project-integrity.yml
execution_environment: github-actions
log_path: framework/logs/AGENT_AUDIT_LOG.md
current_report: framework/logs/PROJECT_INTEGRITY_REPORT.md
checks_included:
  - Issue and proposal structure, including Issue Snapshot concision
  - Area and topic routing
  - Internal repository links
  - Markdown heading anchors
  - Orphaned Markdown pages
  - Page metadata and heading hierarchy
  - Cross-issue reference links
  - GitHub record references
  - GitHub Issue and Project synchronization
  - Lifecycle-field coherence and workflow explanations
  - GitHub Pages deployment synchronization
  - Source and citation catalogs
  - Research placement
  - Reader-facing language
  - Tool-interface conventions
  - Intake-workflow terminology
  - Publication-disposition metadata
  - Print-assembly configuration
  - Persistent-agent runbooks and runtime configuration
  - Structured-file and repository hygiene
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Project Integrity Bot Runbook

The Project Integrity Bot runs the deterministic project-consistency floor as
the final deterministic stage of every Run Coordinator chain. A push to
`main` or a manual request may also start the same coordinated path; the bot
has no independent clock. It compares repository metadata, registries, GitHub
Issues, controlled Project fields, generated routes, structured files, and
encoded conventions. A missing Project credential fails the authenticated
scope.

It publishes a structured current feed and bounded history to
`project-console-data`. When the replaceable current Markdown report changes,
it proposes that report through a narrow pull request. It does not make legal,
evidentiary, fiscal, remedial, lifecycle, rubric, or scoring judgments. It
emits immutable structured stage and finding events to the Run Coordinator;
accepted material provenance is rendered or recorded in the shared Agent Audit
Log under the common rule. A clean unchanged run remains only in Actions and
bounded Console history.

The bot may replace only its dedicated disposable report proposal branch using lease-protected replacement and may open or refresh the corresponding pull request. It may never force-push `main`, a protected branch, a human-owned branch, or a shared working branch.

Runtime authority is limited to `.github/workflows/project-integrity.yml`, `scripts/audit_project_consistency.py`, and the associated report/feed builders. Runtime drift from this runbook must fail validation.

## Checks included

The machine-readable `checks_included` list in this runbook is the authoritative
plain-language inventory displayed by the Project Console. The checker’s
published run scope must match it. Adding, removing, or materially redefining a
check requires updating both the implementation and this list in the same
reviewed change.

The lifecycle-field check distinguishes two separate authorities. Every
canonical issue page must carry a nonblank lowercase front-matter `status`
using the canonical issue-page metadata vocabulary: `awaiting-decision`,
`awaiting-merits-adjudication`, `blocked`, `candidate`, `deferred`,
`developed`, `in-development`, or `retired`. Missing, blank, or non-standard
values are findings. This page metadata is not the GitHub Project workflow
`Status`.

For active Project items, the bot also reports missing or non-standard
workflow Status values, incoherent `Development level` and Status
combinations, monitoring designations without the watched matter, material
relevance, reassessment trigger, and checking method, and required
`workflow_hold_reason` explanations that do not supply the status-specific
content for `Deferred` or `Blocked`. It may identify a missing explanation or
contradiction, but it must not invent the explanation, infer a substantive
classification, change a Project field, or auto-repair the record.

The issue-structure check parses every Issue Snapshot that is present. It
requires the standard Problem, Repair, and Vehicle fields and counts the
reader-visible words in each field. Markdown link destinations and HTML
formatting do not count, but visible link text does. A field above the
Framework's guideline of about twelve words produces an agent-owned warning,
not an error or automatic rewrite, because legal precision may require
editorial judgment.

## Inputs and permitted writes

The bot reads repository structure and metadata, issue and source registries, canonical issue and proposal pages, GitHub Issues, GitHub Project 2, published-page state, agent runbooks, runtime manifests, and generated-file conventions. It may write only its generated Console feed and replaceable current report, and it emits immutable structured provenance to the Run Coordinator. It does not edit the shared Markdown log from its proposal branch. It may not repair findings, alter substantive records, change Project fields, or make legal, evidentiary, lifecycle, rubric, or scoring judgments.

## Publication and review

The structured feed and bounded history publish to `project-console-data`. A changed Markdown snapshot is proposed only on the dedicated disposable `bot/project-integrity-report` branch and requires review before merge. The report branch may be replaced only with lease protection; no report change creates no commit.

## Validation, stop, and output

The bot validates Project credentials, checker execution, report schema, checked-page accounting, feed construction, data publication, report diff boundaries, commit/push status, and runbook/runtime agreement. Missing credentials, script or schema failure, unauthorized file changes, publication failure, or validation failure stops the run. Detected integrity findings are successful observations and remain visible as errors or warnings rather than being auto-repaired. Outputs are the Console integrity feed, bounded history, current report proposal when changed, immutable structured provenance, and Actions summary. Workflow failures enter the Run Coordinator failure state and notification path; findings route through the Integrity screen and report pull request.
