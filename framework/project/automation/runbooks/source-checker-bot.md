---
title: "Source Checker Bot Runbook"
agent_id: source-checker-bot
display_name: Source Checker Bot
console_purpose: "Checks catalogued source URLs for availability and identity changes."
agent_type: deterministic-bot
status: report-only-enabled-local-stage
trigger: local-chain-when-due
schedule: "Due every 168 hours within the 02:00 America/New_York local chain; no independent schedule"
runtime_id: scripts/check_source_urls.py
execution_environment: local-transaction-worktree
runtime_config: framework/project/automation/configuration/bots/source-checker-bot.json
log_path: owner-local:records/automation/agent-audit-log.md
current_report: framework/status/source-checker-report.md
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Source Checker Bot Runbook

## Inputs and permitted writes

The bot reads only configured source catalogs and the exact prior typed
report. It may write only its run-directory JSON and declared current Markdown
report. Validation precedes acceptance. Publication occurs only through the
coordinator's exact reviewed pull-request boundary. A malformed catalog,
unsafe response, or unapproved path is an explicit stop.

The Source Checker accounts for every nonblank URL in the configured source
catalogs and reports `verified`, `identity-preserving redirect`, `access
restricted`, `transient failure`, `broken`, `identity mismatch`, or `review
required`. It uses paced `GET` requests, bounded retries and response size,
and stable identity signals. It never substitutes a source or edits a
catalog.

## Local-stage contract

The coordinator runs the report-only stage locally when due and supplies exact
prior-output and current-output paths under
`<run-dir>/stages/source-checker-bot`. The stage must not require GitHub
Actions variables, artifacts, a report branch, data-branch history, or
publication.

Current JSON/history and any replaceable Markdown report are transaction
outputs only. A valid typed prior output may support cadence and bounded
history. Missing, malformed, stale, or unhashed prior output makes the stage
due.

Access restrictions are not broken links; transient failures remain distinct;
identity contradiction requires review. Catalog/schema or incomplete
accounting failure stops the stage. Because this stage is degraded by default,
independent queue work may continue, but it becomes blocking when selected
work depends on current source-check evidence.

P6 enables this role only as a coordinator-owned local stage. The stage itself
has no branch, commit, pull-request, data-feed, credential, or hosted-mutation
authority.
