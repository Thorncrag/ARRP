---
title: "ARRP Agent and Bot Registry"
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# ARRP Agent and Bot Registry

This directory contains the one authoritative runbook for every persistent named ARRP agent or bot. All runbooks inherit the [Framework](../FRAMEWORK.md) and [Agent Operating Rules](../AGENT_OPERATING_RULES.md); they define only the identity, deployed configuration, narrower authority, work order, and stop conditions of the named role. Runtime manifests and workflows must match these records.

ARRP uses **bot** for a deterministic script or program and **agent** for an LLM-directed worker. A bot uses a stable `-bot` designation; an LLM agent does not, regardless of whether either one runs manually, on a schedule, or in response to an event. Elim is an LLM agent.

| Agent ID | Type | Status | Authoritative runbook | Runtime |
| --- | --- | --- | --- | --- |
| `elim` | Scheduled LLM agent | Paused pending pilot | [Elim](ELIM.md) | Codex automation `elim`, isolated worktree |
| `project-integrity-bot` | Deterministic bot | Enabled | [Project Integrity Bot](PROJECT_INTEGRITY_BOT.md) | `.github/workflows/project-integrity.yml` |
| `case-monitor-bot` | Deterministic bot | Enabled | [Case Monitor Bot](CASE_MONITOR_BOT.md) | `.github/workflows/case-monitor-bot.yml` |
| `presidential-directives-bot` | Deterministic bot | Enabled | [Presidential Directives Bot](PRESIDENTIAL_DIRECTIVES_BOT.md) | `.github/workflows/presidential-directives-bot.yml` |
| `project-console-progress-bot` | Deterministic bot | Enabled | [Project Console Progress Bot](PROJECT_CONSOLE_PROGRESS_BOT.md) | `.github/workflows/project-console-progress.yml` |
| `source-checker-bot` | Deterministic bot | Report-only pilot | [Source Checker Bot](SOURCE_CHECKER_BOT.md) | `.github/workflows/source-checker-bot.yml` |

Temporary task agents and one-off delegated subagents do not receive runbooks unless they become persistent named roles.
