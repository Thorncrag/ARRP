---
title: "Agent Rules — Context and Research"
dependencies:
  - "../../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Agent Rules — Context and Research

Load this module when selecting context, conducting research, refreshing sources, or deciding whether additional investigation is useful. It supplements the universal context-expansion and no-hallucination rules in [`AGENT_OPERATING_RULES.md`](../../AGENT_OPERATING_RULES.md) and the substantive evidence rules routed through [`FRAMEWORK.md`](../../FRAMEWORK.md).

## Research Proportionality

Agents should use a proportionate and reliable method that fully satisfies the assigned task.

1. Start with local project files before using external searches.
2. Use targeted searches rather than broad repeated queries.
3. Prefer primary sources and already-captured source-catalog records.
4. Reuse verified source records where still current and relevant.
5. Avoid duplicating completed audit work unless a changed rule, changed fact, or explicit user request requires it.
6. Do not run multiple agents on the same files or same unresolved question.
7. Do not continue researching after the audit tier's question has been responsibly answered.
8. If a source path or theory is not producing useful results, document the limitation and move on.
9. If a proposal requires a human-reserved decision, document the exact
   question, use the project-configured human-decision route, and advance to
   the next eligible item rather than attempting speculative repair.
10. Preserve and synchronize completed units promptly through the project's
    reviewed boundary so later agents do not repeat them.

Research efficiency never authorizes a narrower result than the assigned operation requires. If bounded context reveals ambiguity, conflicting authority, an unfamiliar issue class, a likely omission, a changed governing rule, or a validation failure, expand to the canonical source before acting.
