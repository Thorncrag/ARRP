---
title: "ARRP Agent and Bot Registry"
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# ARRP Agent and Bot Registry

This registry identifies every persistent named ARRP automation role. Each role
inherits the [Framework](../../FRAMEWORK.md), [Agent Operating
Rules](../../AGENT_OPERATING_RULES.md), the ARRP [autonomous-execution
policy](autonomous-execution.md), and its linked runbook. A runbook narrows
authority; it cannot create authority.

ARRP uses **bot** for deterministic code and **agent** for an LLM-directed
worker. Temporary interactive or delegated agents are not persistent roles.

## P4 transition status

The former GitHub Actions, data-branch, host-dispatcher, and scheduled Codex
chain is retired and has no runtime authority. P4 adapts the retained roles to
one local-first source chain in `scripts/arrp_nightly.py`, with typed stage
outputs under a transaction run directory and cadence evidence in owner-only
`~/Library/Application Support/ARRP/last-success.json`.

This source remains disabled for canonical and unattended execution. P4 adds
the protected `CODEOWNERS` and validation-workflow source plus a fixture-tested
GitHub App, exact-PR, and registered semantic-action broker boundary. No
LaunchAgent is installed, no scheduler is active, and no retired workflow is
reactivated. Live publication remains limited to expressly approved P4
fixtures; role status may change to enabled only at an expressly authorized
cutover.

| Agent ID | Type | P4 status | Authoritative runbook | Local runtime |
| --- | --- | --- | --- | --- |
| `run-coordinator-bot` | Deterministic bot | Source implemented; disabled | [Run Coordinator Bot](runbooks/run-coordinator-bot.md) | `scripts/arrp_nightly.py` |
| `elim` | Conditional LLM agent | Fixture invocation only; disabled for canonical runs and never credentialed | [Elim](runbooks/elim.md) | One fresh sealed `codex exec` subprocess |
| `case-monitor-bot` | Deterministic bot | Local stage source; disabled | [Case Monitor Bot](runbooks/case-monitor-bot.md) | `scripts/check_case_updates.py` |
| `presidential-directives-bot` | Deterministic bot | Local stage source; disabled | [Presidential Directives Bot](runbooks/presidential-directives-bot.md) | `scripts/check_presidential_directives.py` |
| `source-checker-bot` | Deterministic bot | Local report stage source; disabled | [Source Checker Bot](runbooks/source-checker-bot.md) | `scripts/check_source_urls.py` |
| `project-console-progress-bot` | Deterministic bot | Local projection stage source; disabled | [Project Console Progress Bot](runbooks/project-console-progress-bot.md) | `scripts/build_project_console_progress.py` |
| `project-integrity-bot` | Deterministic bot | Local integrity stage source; disabled | [Project Integrity Bot](runbooks/project-integrity-bot.md) | `scripts/audit_project_consistency.py` |

Public-intake collection is a deterministic coordinator stage, not a separate
persistent named role.

## Common local-stage contract

The coordinator supplies every exact input and output path. A stage may read
only its canonical inputs and prior successful typed output. It writes only
its declared run-directory output and any exact worktree path expressly
authorized by its runbook. A stage cannot create a branch, commit, pull
request, data-branch projection, Project mutation, Discussion reply, or other
external action.

A stage is `not_due` only when `last-success.json` points to prior successful
typed output that is present, schema-valid, hashable, and within cadence.
Missing, stale, malformed, or unhashed output makes the stage due. Execution
or schema failure is blocking or degraded exactly as listed in the
coordinator configuration; findings produced by a successful detector are not
execution failures.

All roles use the shared provenance and handoff rules in
[`agent-policy.md`](agent-policy.md). The run directory is operational
evidence, not a new source of substantive authority.
