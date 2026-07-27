---
title: "Agent Rules — Provenance and Logging"
dependencies:
  - "../../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Agent Rules — Provenance and Logging

Load this module for every material autonomous or scheduled unit; whenever an agent or bot changes a source record; whenever a persistent LLM agent run opens or closes; and whenever rollback, revert, branch-replacement, or log ownership is implicated.

## Shared Agent Audit Log

A project should designate one shared operational provenance record for
material persistent-agent and bot work and rollback planning. Every material
autonomous unit records its action under stable actor, run, and unit
identifiers. This record does not replace issue audit histories, hosted
workflow tracking, domain event records, replaceable current reports, handoff
checkpoints, or final user-facing reports.

Ordinary human-invoked work should not update the persistent-automation log
unless the user expressly converts it into an autonomous, batched, or scheduled
run.

For each material unit, record:

1. date and time with local timezone if available;
2. stable Agent ID, Run ID, and Unit ID where applicable;
3. trigger, task type, outcome, and issue or project task;
4. link to the canonical content record;
5. link to the audit-history record;
6. link to the proposal vehicle where one exists;
7. requested tier or task;
8. files changed;
9. validation performed;
10. preservation message;
11. synchronized revision;
12. synchronization status;
13. rollback target or revert notes; and
14. any blockers, skipped checks, or human-review stop conditions.

Completely clean no-change runs may remain in bounded runtime or interface
history without appending to the shared material-work log. A material detected
or routed finding and any repository or external-state change must be logged.
When an agent changes a source record, the same reviewed change must append one
entry identifying affected stable source IDs, the action and reason, the
destination and proposition or citation supported, the originating run,
validation, preservation and synchronization status, and rollback reference.

The shared provenance record should be append-only. If a revision is later
reverted, add a new entry identifying the revert and the original revision it
reverses. Do not erase the original entry.

The canonical prospective entry template is maintained in the log itself. Preserve historical generic labels and schemas; do not retroactively attribute older runs to a newly named agent without reliable evidence.

Persistent automation should write immutable structured event records or
replaceable projections when several bots would otherwise edit one shared
human-readable log from concurrent or long-lived branches. A deterministic
renderer may project those events after validation. Generated presentation
never replaces event provenance, and neither form creates substantive
authority. A logging or rendering mechanism does not authorize a bot to alter
content, source identity, hosted fields, scores, foundations, remedies,
dispositions, rubrics, or human-reserved decisions.

## Dedicated LLM-agent run logs

A persistent scheduled LLM agent may define a dedicated run-log path in its
authoritative configuration. That log accounts for every invocation, including
clean, productive, usage-stopped, blocked, and failed runs. It records the
run's usage posture, work examined, actions taken, skipped or routed work,
material-unit links, validation, preservation and synchronization, human-review
questions, stop reason, and exact continuation point.

The dedicated run log does not replace shared material-work provenance or issue
audit histories. The run report summarizes results and links the authoritative
records. Sensitive or restricted input remains subject to its narrower privacy
and moderation rules.

## Branch and rollback preservation

Agents and bots must never force-update the canonical branch, a protected
branch, a human-owned branch, or any shared working branch. A deterministic bot
may replace only its own dedicated disposable branch when its authoritative
runbook expressly allows that behavior, using a concurrency-safe lease so an
unexpected intervening change prevents replacement. Rollback on shared or
durable branches should normally occur through a new reversing revision so
history remains intelligible.
