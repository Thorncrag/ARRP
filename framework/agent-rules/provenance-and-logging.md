---
title: "Agent Rules — Provenance and Logging"
dependencies: "../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Agent Rules — Provenance and Logging

Load this module for every material autonomous or scheduled unit; whenever an agent or bot changes a source record; whenever a persistent LLM agent run opens or closes; and whenever rollback, revert, branch-replacement, or log ownership is implicated.

## Shared Agent Audit Log

All persistent agents and bots use the shared [`AGENT_AUDIT_LOG.md`](../logs/AGENT_AUDIT_LOG.md) for material operational provenance and rollback planning. Every material autonomous agent or bot unit records its action there under a stable Agent ID and Run ID. It does not replace issue audit histories, GitHub Project tracking, domain event records, replaceable current reports, [`CURRENT_AUDIT.md`](../logs/CURRENT_AUDIT.md) handoff checkpoints, or final user-facing reports.

Ordinary human-invoked audit or drafting sessions should not update the agent audit log unless the user expressly converts the work into an autonomous, batched, or scheduled run.

For each material unit, record:

1. date and time with local timezone if available;
2. stable Agent ID, Run ID, and Unit ID where applicable;
3. trigger, task type, outcome, and issue or project task;
4. link to the issue page;
5. link to the issue audit-history file;
6. link to the proposed legislation, constitutional amendment, rule, model text, or other proposal page where one exists;
7. requested tier or task;
8. files changed;
9. validation performed;
10. commit message;
11. commit hash;
12. push status;
13. rollback target or revert notes; and
14. any blockers, skipped checks, or human-review stop conditions.

Completely clean no-change runs remain in bounded Actions or Console history and do not append an entry to the Agent Audit Log. A material detected or routed finding and any repository or external-state change must be logged. When an agent adds, updates, moves, or removes a source record, the same source-changing pull request must append one entry identifying the affected stable source IDs, the action and reason, the destination and proposition or citation supported, the originating run, validation, commit and push status, and rollback reference.

The agent audit log should be append-only. If a commit is later reverted, add a new log entry identifying the revert commit and the original commit it reverses. Do not erase the original log entry.

The canonical prospective entry template is maintained in the log itself. Preserve historical generic labels and schemas; do not retroactively attribute older runs to a newly named agent without reliable evidence.

Persistent automation should write immutable structured event records or data-branch projections when several bots would otherwise edit the same shared Markdown log from concurrent or long-lived branches. A deterministic renderer may project those events into the human-readable log and Console after validation. The generated presentation never replaces the event provenance, and neither form creates substantive authority. This direction is intended to avoid merge conflicts and duplicated closeout prose; it does not authorize a bot to alter an issue, source identity, Project field, score, foundation, remedy, disposition, rubric, or human-reserved decision.

## Dedicated LLM-agent run logs

A persistent scheduled LLM agent may define a dedicated `run_log_path` in its authoritative runbook. That log accounts for every invocation of that agent, including clean, productive, usage-stopped, blocked, and failed runs. It records the run's usage posture, work examined, all actions taken, skipped or routed work, material-unit links, validation, commits and synchronization, human-review questions, stop reason, and exact continuation point.

The dedicated run log does not replace the shared Agent Audit Log. Material autonomous units still receive their ordinary project-wide provenance and rollback entry there. It also does not replace or duplicate issue audit histories: detailed T-audit and Change Audit findings remain in the affected issue audit sidecar and synchronized issue, inventory, dashboard, and GitHub records. The run report summarizes results and links those authoritative records. Sensitive or restricted intake content remains subject to its narrower privacy and moderation rules.

## Branch and rollback preservation

Agents and bots must never force-push `main`, a protected branch, a human-owned branch, or any shared working branch. A deterministic bot may replace only its own dedicated, disposable report or proposal branch when its authoritative runbook expressly allows that behavior, and it must use `--force-with-lease` so an unexpected intervening change prevents the replacement. Rollback on shared or durable branches should normally occur through a revert commit so GitHub history remains intelligible.
