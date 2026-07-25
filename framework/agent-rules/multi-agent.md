---
title: "Agent Rules — Multi-Agent Work"
dependencies: "../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Agent Rules — Multi-Agent Work

Load this module before delegating project work to another agent or coordinating concurrent agent responsibilities.

## Multi-Agent Use

Use multiple agents by default when work can be separated into non-overlapping responsibilities and parallel execution is expected to improve speed, coverage, or independent verification. Do not limit delegation because of historical subscription-usage assumptions or impose an arbitrary agent, time, token, or resource cap. Use one agent when the work is inherently sequential, requires repeated judgment over the same files, or would incur more coordination risk than benefit. Examples of suitable parallel work include:

1. one agent checking source sufficiency while another checks GitHub Project/source-inventory consistency;
2. one agent surveying prior legislation while another checks issue-to-legislation alignment; or
3. one agent validating links while another prepares a narrow issue-page cleanup.

Agents should not edit the same file set at the same time unless a coordinator assigns a clear merge responsibility. A coordinating agent remains responsible for reconciling findings, reviewing all edits, resolving conflicts, running final consistency checks, validating the complete worktree, and handling any commit and push.

This default governs interactive work and human-directed project reviews. The narrower single-LLM default for autonomous and scheduled execution is an approved operating design, not an audit-depth, token, or quality cap. A scheduled agent expands context or uses a justified subagent whenever the work itself requires it; it does not spend additional model turns merely to repeat deterministic inventory or no-op discovery.
