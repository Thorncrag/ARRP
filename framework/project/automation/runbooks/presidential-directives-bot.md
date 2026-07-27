---
title: "Presidential Directives Bot Runbook"
agent_id: presidential-directives-bot
display_name: Presidential Directives Bot
agent_type: deterministic-bot
status: disabled
trigger: local-chain-when-due
schedule: "Due every 24 hours after cutover; no independent schedule"
runtime_id: scripts/check_presidential_directives.py
execution_environment: local-transaction-worktree
runtime_config: .github/presidential-directives-bot.json
log_path: framework/records/automation/agent-audit-log.md
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Presidential Directives Bot Runbook

## Inputs and permitted writes

The bot reads only its configured registry, provider scope, exact fixture or
response, and prior typed output. It may write only registry fingerprints, the
source-monitor log, and caller-selected run-directory reports. Validation
precedes acceptance. Publication is disabled in P2. Missing, malformed, stale,
or unauthorized input is an explicit stop.

The Presidential Directives Bot compares accepted registry metadata with the
official Federal Register API for the configured Trump I, Biden, and Trump II
coverage. It validates provider host, response and pagination bounds,
directive identity, fingerprint, and last-changed values.

## P2 local-stage contract

The coordinator runs the stage locally when due and supplies exact fixture or
transaction inputs and output paths under
`<run-dir>/stages/presidential-directives-bot`. The stage must not depend on
GitHub Actions variables, workflow events, artifacts, a proposal branch, a
data branch, or hosted publication.

The bot may update only authorized deterministic directive-registry metadata
in the transaction worktree and write its typed run-directory output. It
cannot decide relevance, characterize legal or political significance, route
evidence, revise prose, create a candidate, or change Project, audit,
scoring, foundation, remedy, or disposition fields.

Provider, schema, identity, scope, pagination, or authorized-path failure is
blocking. Valid new or changed directive observations are successful stage
output and enter the current review queue; they are not automatically
accepted or published.

P2 leaves the role disabled outside fixtures and manual dry-run validation.
No branch, commit, pull request, source-domain event publication, credential,
or hosted mutation is authorized.
