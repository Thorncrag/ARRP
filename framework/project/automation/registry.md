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

> **Deployment status — retired 2026-07-27.** All registered ARRP
> maintenance roles are out of service pending the approved local-first
> replacement. Their GitHub workflows are disabled, both launchd services and
> labels are disabled with their installed definitions archived, and the
> scheduled Codex Elim automation has been archived and removed. The runbooks,
> workflows, scripts, and configuration below are retained as versioned
> implementation history and migration input; they are not evidence of a
> currently deployed or authorized automation.

| Agent ID | Type | Status | Authoritative runbook | Runtime |
| --- | --- | --- | --- | --- |
| `run-coordinator-bot` | Deterministic bot | Retired; source retained | [Run Coordinator Bot](runbooks/run-coordinator-bot.md) | Not deployed; former GitHub workflow and local dispatcher |
| `elim` | Conditional LLM agent | Retired; source retained | [Elim](runbooks/elim.md) | Not deployed; former scheduled Codex automation and isolated checkout |
| `project-integrity-bot` | Deterministic bot | Retired; source retained | [Project Integrity Bot](runbooks/project-integrity-bot.md) | Not deployed; former GitHub workflow |
| `case-monitor-bot` | Deterministic bot | Retired; source retained | [Case Monitor Bot](runbooks/case-monitor-bot.md) | Not deployed; former GitHub workflow |
| `presidential-directives-bot` | Deterministic bot | Retired; source retained | [Presidential Directives Bot](runbooks/presidential-directives-bot.md) | Not deployed; former GitHub workflow |
| `project-console-progress-bot` | Deterministic bot | Retired; source retained | [Project Console Progress Bot](runbooks/project-console-progress-bot.md) | Not deployed; former GitHub workflow |
| `source-checker-bot` | Deterministic bot | Retired; source retained | [Source Checker Bot](runbooks/source-checker-bot.md) | Not deployed; former report-only pilot workflow |

Temporary task agents and one-off delegated subagents do not receive runbooks unless they become persistent named roles.
