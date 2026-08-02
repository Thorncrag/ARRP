---
title: "Project Console Progress Bot Runbook"
agent_id: project-console-progress-bot
display_name: Project Console Progress Bot
console_purpose: "Calculates Review Ready progress, the development board, metrics, and forecast."
agent_type: deterministic-bot
status: enabled-local-stage
trigger: local-chain-when-due
schedule: "Due every 24 hours within the 02:00 America/New_York local chain; no independent schedule"
runtime_id: scripts/build_project_console_progress.py
execution_environment: local-transaction-worktree
runtime_config: framework/project/interfaces/project-console/configuration/progress.json
log_path: owner-local:records/automation/agent-audit-log.md
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Project Console Progress Bot Runbook

## Inputs and permitted writes

The bot reads the exact configured Project snapshot, issue registry, history,
and progress configuration. It may write only its caller-selected typed
run-directory output. Validation precedes acceptance. Publication occurs only
through the coordinator's exact reviewed pull-request boundary. Missing
authentication, malformed input, or an unapproved output path is an explicit
stop.

The Project Console Progress Bot reads the issue registry and an authenticated
GitHub Project snapshot supplied by deterministic code, then calculates the
configured Review Ready goal, six-stage board, metrics, forecast, warnings,
and bounded history. It is read-only with respect to GitHub and canonical
substantive records.

## Local-stage contract

The coordinator runs the stage locally when due and supplies exact inputs and
`<run-dir>/progress` as the output root. The stage must not fetch credentials
from Elim, require GitHub Actions variables, publish to
`project-console-data`, or mutate Project fields.

The Project field names, goal, baseline, target, readiness rule, source
registry, and history seed remain defined in
[`../../interfaces/project-console/configuration/progress.json`](../../interfaces/project-console/configuration/progress.json).
A valid typed prior history may be carried forward through the runner.
Missing, malformed, stale, or unhashed prior output makes the stage due.

Authentication, schema, registry join, identity, completeness, or output
failure is blocking. Unknown or unmatched records remain visible warnings and
are not repaired automatically. Generated progress output is a local
transaction projection, not authority and not publication.

P6 enables this role only as a coordinator-owned local stage. The stage itself
has no data-branch, workflow, credential-provisioning, or hosted-mutation
authority.
