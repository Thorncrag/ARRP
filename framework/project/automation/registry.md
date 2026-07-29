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

## P6 local-first runtime status

The former GitHub Actions, data-branch, host-dispatcher, and scheduled Codex
chain is retired and has no runtime authority. P6 enables the retained roles
through one local-first source chain in `scripts/arrp_nightly.py`, with typed stage
outputs under a transaction run directory and cadence evidence in owner-only
`~/Library/Application Support/ARRP/last-success.json`.

One owner LaunchAgent, `com.thorncrag.arrp-nightly`, is the only scheduled
ARRP coordinator. It runs at 02:00 local time in `America/New_York` and uses
`RunAtLoad` only for due evaluation. The protected `CODEOWNERS`,
required-validation workflow, GitHub App exact-PR boundary, and registered
semantic-action broker remain controlling. Retired maintenance workflows,
bot branches, and `project-console-data` are not runtime or publication
surfaces.

| Agent ID | Type | P6 status | Authoritative runbook | Local runtime |
| --- | --- | --- | --- | --- |
| `run-coordinator-bot` | Deterministic bot | Enabled; sole scheduled coordinator | [Run Coordinator Bot](runbooks/run-coordinator-bot.md) | `scripts/arrp_nightly.py` |
| `elim` | Conditional LLM agent | Enabled only for one selected unit per eligible run; never credentialed | [Elim](runbooks/elim.md) | One fresh sealed `codex exec` subprocess |
| `case-monitor-bot` | Deterministic bot | Enabled local stage | [Case Monitor Bot](runbooks/case-monitor-bot.md) | `scripts/check_case_updates.py` |
| `presidential-directives-bot` | Deterministic bot | Enabled local stage | [Presidential Directives Bot](runbooks/presidential-directives-bot.md) | `scripts/check_presidential_directives.py` |
| `source-checker-bot` | Deterministic bot | Enabled local report stage | [Source Checker Bot](runbooks/source-checker-bot.md) | `scripts/check_source_urls.py` |
| `project-console-progress-bot` | Deterministic bot | Enabled local projection stage | [Project Console Progress Bot](runbooks/project-console-progress-bot.md) | `scripts/build_project_console_progress.py` |
| `project-integrity-bot` | Deterministic bot | Enabled local integrity stage | [Project Integrity Bot](runbooks/project-integrity-bot.md) | `scripts/audit_project_consistency.py` |

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

Before dependent stages, scheduled and manual production runs invoke the shared
`scripts/repository_gates.py` producer with the GitHub App token. Its sole
classification authority is the append-only
owner-local `records/automation/repository-gates.jsonl` event record governed by
[`repository-gates.json`](repository-gates.json). A complete paginated open-PR
scan and complete declaration scan are both required before the producer may
emit `complete: true` or a zero count. Applicable gates are attached and
hash-bound to the run chain, and only their declared dependent stages are
stopped. Source Monitor recommendations, browser prose, and an untyped open
pull request do not create a repository gate.

All roles use the shared provenance and handoff rules in
[`agent-policy.md`](agent-policy.md). The run directory is operational
evidence, not a new source of substantive authority.

## Operational Incident authority

[`operational-incidents.json`](operational-incidents.json) governs the one
project-wide Operational Incident event record at the owner-local path
`records/automation/operational-incidents.jsonl`.
The deterministic `scripts/operational_incidents.py` module validates,
sanitizes, deduplicates, appends immutable events, and produces the current
projection. No persistent role, LLM result, browser calculation, run log, or
specialist status feed is a competing incident authority.

The coordinator records typed run failures and degradations and validates any
bounded advisory `incident_reports` returned by Elim before recording them.
If Elim fails, times out, or returns an invalid result, the transaction writes
an owner-only sanitized failure event to the local spool independently of
normal generated-view completion. The next valid transaction reconciles that
event into the canonical record. Repeated typed occurrences preserve exact run
identity under one unresolved incident; recurrence after exact verified
resolution creates a new linked incident.

Specialist producers retain their own state and may publish only typed
`active_incident_ids`. Routine findings, remediation work, repository gates,
and intentional Paused state do not become incidents merely because they
exist.
