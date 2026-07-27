---
title: "Case Monitor Bot Runbook"
agent_id: case-monitor-bot
display_name: Case Monitor Bot
agent_type: deterministic-bot
status: disabled
trigger: local-chain-when-due
schedule: "Due every 24 hours after cutover; no independent schedule"
runtime_id: scripts/check_case_updates.py
execution_environment: local-transaction-worktree
runtime_config: .github/case-monitor-bot.json
log_path: framework/records/automation/agent-audit-log.md
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Case Monitor Bot Runbook

## Inputs and permitted writes

The bot reads only its configured source catalogs, provider fixture or
response, and exact prior typed output. It may write only the contract-listed
catalog baselines, source-development records, log entry, and run-directory
reports. Validation precedes acceptance. Publication is disabled in P2.
Missing, malformed, stale, or unauthorized input is an explicit stop.

The Case Monitor compares expressly monitored source rows with the configured
Just Security litigation tracker and may perform the configured narrow,
paced CourtListener verification. It may also refresh exact marker-bounded
machine-lead sections for named existing source-development records.

It preserves stable case identity, accepted monitoring baselines, primary and
related-appeal distinctions, exact status fields, tracker limitations, request
ceilings, allowed hosts, and the rule that a machine lead is not an admitted
source or substantive conclusion.

## P2 local-stage contract

The coordinator runs the stage locally when due and supplies exact fixture or
transaction inputs and output paths under
`<run-dir>/stages/case-monitor-bot`. The stage must not depend on GitHub
Actions variables, workflow events, artifacts, a proposal branch, a data
branch, or hosted publication.

The bot may change only the authorized machine-observed source fields and
exact configured lead markers in the transaction worktree, plus its typed
run-directory output. It cannot interpret legal significance, create or admit
a candidate, edit project-authored analysis, change Project fields, scores,
`Runs`, foundations, remedies, or permanent dispositions.

Execution, provider, schema, identity, marker, ceiling, or authorized-path
failure is blocking. Valid findings and observed changes are successful stage
output and enter the current queue; they are not automatically accepted or
published.

P2 leaves the role disabled outside fixtures and manual dry-run validation.
No branch, commit, pull request, source-domain event publication, credential,
or hosted mutation is authorized.
