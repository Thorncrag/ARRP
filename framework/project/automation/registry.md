---
title: "ARRP Agent and Bot Registry"
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# ARRP Agent and Bot Registry

This directory contains the one authoritative runbook for every persistent named ARRP agent or bot. All runbooks inherit the [Framework](../../FRAMEWORK.md) and [Agent Operating Rules](../../AGENT_OPERATING_RULES.md); they define only the identity, deployed configuration, narrower authority, work order, and stop conditions of the named role. Runtime manifests and workflows must match these records.

Every registered role also inherits the exact
[ARRP task-handoff](agent-policy.md#arrp-task-handoff) and
[provenance and log-ownership](agent-policy.md#arrp-provenance-and-log-ownership)
policies. A runbook may name its dedicated run log and narrower event records,
but it may not replace the shared Agent Audit Log, issue audit histories,
domain event records, or the current-task checkpoint.

ARRP uses **bot** for a deterministic script or program and **agent** for an LLM-directed worker. A bot uses a stable `-bot` designation; an LLM agent does not, regardless of whether either one runs manually, on a schedule, or in response to an event. Elim is an LLM agent.

| Agent ID | Type | Status | Authoritative runbook | Runtime |
| --- | --- | --- | --- | --- |
| `run-coordinator-bot` | Deterministic bot | Enabled | [Run Coordinator Bot](runbooks/run-coordinator-bot.md) | `.github/workflows/run-coordinator-bot.yml` with local Codex dispatch |
| `elim` | Conditional LLM agent | Enabled | [Elim](runbooks/elim.md) | Codex automation `elim`, dispatcher-managed isolated full checkout |
| `project-integrity-bot` | Deterministic bot | Enabled | [Project Integrity Bot](runbooks/project-integrity-bot.md) | `.github/workflows/project-integrity.yml` |
| `case-monitor-bot` | Deterministic bot | Enabled | [Case Monitor Bot](runbooks/case-monitor-bot.md) | `.github/workflows/case-monitor-bot.yml` |
| `presidential-directives-bot` | Deterministic bot | Enabled | [Presidential Directives Bot](runbooks/presidential-directives-bot.md) | `.github/workflows/presidential-directives-bot.yml` |
| `project-console-progress-bot` | Deterministic bot | Enabled | [Project Console Progress Bot](runbooks/project-console-progress-bot.md) | `.github/workflows/project-console-progress.yml` |
| `source-checker-bot` | Deterministic bot | Report-only pilot | [Source Checker Bot](runbooks/source-checker-bot.md) | `.github/workflows/source-checker-bot.yml` |

Temporary task agents and one-off delegated subagents do not receive runbooks unless they become persistent named roles.
