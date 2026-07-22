---
title: "Project Integrity Bot Runbook"
agent_id: project-integrity-bot
display_name: Project Integrity Bot
agent_type: deterministic-bot
status: enabled
trigger: schedule-and-main-push
schedule: "35 5 * * * UTC; daily near 1:35 a.m. EDT / 12:35 a.m. EST"
runtime_id: .github/workflows/project-integrity.yml
execution_environment: github-actions
log_path: framework/logs/AGENT_AUDIT_LOG.md
current_report: framework/logs/PROJECT_INTEGRITY_REPORT.md
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Project Integrity Bot Runbook

The Project Integrity Bot runs the deterministic project-consistency floor after every push to `main` and on its daily schedule. It compares repository metadata, registries, GitHub Issues, controlled Project fields, generated routes, structured files, and encoded conventions. A missing Project credential fails the authenticated scope.

It publishes a structured current feed and bounded history to `project-console-data`. When the replaceable current Markdown report changes, it proposes that report through a narrow pull request. It does not make legal, evidentiary, fiscal, remedial, lifecycle, rubric, or scoring judgments. Material actions or routed findings use the shared Agent Audit Log; a clean unchanged run remains only in Actions and bounded Console history.

The bot may replace only its dedicated disposable report proposal branch using lease-protected replacement and may open or refresh the corresponding pull request. It may never force-push `main`, a protected branch, a human-owned branch, or a shared working branch.

Runtime authority is limited to `.github/workflows/project-integrity.yml`, `scripts/audit_project_consistency.py`, and the associated report/feed builders. Runtime drift from this runbook must fail validation.

## Inputs and permitted writes

The bot reads repository structure and metadata, issue and source registries, canonical issue and proposal pages, GitHub Issues, GitHub Project 2, published-page state, agent runbooks, runtime manifests, and generated-file conventions. It may write only its generated Console feed, replaceable current report, and shared provenance entry. It may not repair findings, alter substantive records, change Project fields, or make legal, evidentiary, lifecycle, rubric, or scoring judgments.

## Publication and review

The structured feed and bounded history publish to `project-console-data`. A changed Markdown snapshot is proposed only on the dedicated disposable `bot/project-integrity-report` branch and requires review before merge. The report branch may be replaced only with lease protection; no report change creates no commit.

## Validation, stop, and output

The bot validates Project credentials, checker execution, report schema, checked-page accounting, feed construction, data publication, report diff boundaries, commit/push status, and runbook/runtime agreement. Missing credentials, script or schema failure, unauthorized file changes, publication failure, or validation failure stops the run. Detected integrity findings are successful observations and remain visible as errors or warnings rather than being auto-repaired. Outputs are the Console integrity feed, bounded history, current report proposal when changed, Agent Audit Log entry for material routing, and Actions summary. Workflow failures use the configured GitHub failure notification; findings route through the Integrity screen and report pull request.
