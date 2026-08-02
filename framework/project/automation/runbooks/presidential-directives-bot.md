---
title: "Presidential Directives Bot Runbook"
agent_id: presidential-directives-bot
display_name: Presidential Directives Bot
console_purpose: "Checks official Federal Register records for changes to tracked presidential directives."
agent_type: deterministic-bot
status: enabled-local-stage
trigger: local-chain-when-due
schedule: "Due every 24 hours within the 02:00 America/New_York local chain; no independent schedule"
runtime_id: scripts/check_presidential_directives.py
execution_environment: local-transaction-worktree
runtime_config: framework/project/automation/configuration/bots/presidential-directives-bot.json
log_path: owner-local:records/automation/agent-audit-log.md
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Presidential Directives Bot Runbook

## Inputs and permitted writes

The bot reads only its configured registry, provider scope, exact fixture or
response, and prior typed output. It may write only registry fingerprints, the
source-monitor log, and caller-selected run-directory reports. Validation
precedes acceptance. Publication occurs only through the coordinator's exact
reviewed pull-request boundary. Missing, malformed, stale, or unauthorized
input is an explicit stop.

The Presidential Directives Bot compares accepted registry metadata with the
official Federal Register API for the configured Trump I, Biden, and Trump II
coverage. It validates provider host, response and pagination bounds,
directive identity, fingerprint, and last-changed values.

## Local-stage contract

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

P6 enables this role only as a coordinator-owned local stage. The stage itself
has no branch, commit, pull-request, source-domain-event publication,
credential, or hosted-mutation authority.
