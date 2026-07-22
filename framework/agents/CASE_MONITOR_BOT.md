---
title: "Case Monitor Bot Runbook"
agent_id: case-monitor-bot
display_name: Case Monitor Bot
agent_type: deterministic-bot
status: enabled
trigger: schedule-or-manual
schedule: "17 4 * * * UTC; approximately midnight Eastern"
runtime_id: .github/workflows/case-monitor-bot.yml
execution_environment: github-actions
runtime_config: .github/case-monitor-bot.json
log_path: framework/logs/AGENT_AUDIT_LOG.md
domain_event_log: framework/logs/SOURCE_MONITOR_LOG.md
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Case Monitor Bot Runbook

The Case Monitor Bot performs one respectful daily comparison for cataloged `Monitoring = Yes` sources mapped to stable entries in the Just Security litigation tracker. It validates tracker structure and accepted baselines before comparing fingerprints. For a changed mapped CourtListener docket it may perform the configured narrow, paced metadata verification.

It may update only authorized machine-observed source fields on `bot/case-monitor-updates`, record the domain event, and create or update the owner-assigned review pull request. It may not discover every new case, interpret legal significance, revise project prose, change Project fields, create a candidate, remove monitoring, or change a score, audit count, foundation, or remedy. Failures are closed; no-change runs create no commit.

The JSON manifest and GitHub workflow are deployed projections of this runbook and must match its identity, status, cadence, branch, and log locations. Material actions use the shared Agent Audit Log in addition to any source-domain event required for evidentiary traceability.

## Inputs and permitted writes

The bot reads the two canonical source catalogs, rows expressly marked `Monitoring = Yes`, accepted monitoring baselines, the configured Just Security tracker table, and at most the configured number of eligible CourtListener dockets. It may change only authorized machine-observed fields in `inventory/sources.csv` or `inventory/sources-pending.csv` and append the resulting event and provenance entries. It may not change source meaning, project prose, issue disposition, Project fields, or audit/scoring records.

## Publication and review

Material changes are committed only to the dedicated `bot/case-monitor-updates` proposal branch and presented through an owner-assigned pull request. The branch is replaceable only with lease protection under the shared branch-safety rule. No-change runs create no commit. Every proposed catalog change requires human review before merge.

## Validation, stop, and output

Before publication, the bot validates tracker structure and bounds, source eligibility, accepted baselines, allowed hosts, docket identity, the configured 20-docket ceiling, 13-second CourtListener pacing, and the authorized change boundary. Missing or malformed inputs, identity ambiguity, network/provider failure, boundary violations, commit/push failure, or validation failure stop the run without a misleading update. Outputs are the proposed catalog delta, Source Monitor event, shared Agent Audit Log entry, Actions summary, and retained diagnostic artifact. Workflow failures use the configured GitHub failure notification; routed content changes rely on the assigned pull request.
