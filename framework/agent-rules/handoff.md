---
title: "Agent Rules — Context Handoff"
dependencies: "../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Agent Rules — Context Handoff

Load this module when a task may span many tool calls, user interruptions, context compaction, or a new chat; whenever [`CURRENT_AUDIT.md`](../logs/CURRENT_AUDIT.md) is opened or changed; and whenever the user asks to continue, follow up, or resume prior work without identifying the task.

## Context Handoff

Long audits and source-development passes should not depend on chat memory alone. Use [`CURRENT_AUDIT.md`](../logs/CURRENT_AUDIT.md) as the durable handoff checkpoint for any audit, drafting pass, source-development task, or batch run that may span many tool calls, user interruptions, or a new chat.

Before beginning a long audit, update `CURRENT_AUDIT.md` with the active issue or task, requested tier, scope, expected files, and first next step. During the work, refresh it after each major phase, before broad file edits, before risky or hard-to-reverse decisions, and whenever the conversation appears likely to approach a context handoff.

The checkpoint should identify:

1. active issue or task;
2. audit type or tier;
3. user request;
4. scope and files in play;
5. completed steps;
6. exact next step;
7. blockers or open questions;
8. validation status; and
9. whether the handoff is Open, Paused, Blocked, or Inactive.

`Open` means an unfinished task has an exact continuation point. `Paused` means the same unfinished task has been deliberately suspended and records who or what will resume it and under what condition. `Blocked` means the unfinished task cannot proceed because a concrete indispensable prerequisite is unavailable and records the blocked action, prerequisite, and unblock trigger. `Inactive` means there is no unfinished task handoff. These are continuation states only; none establishes runtime liveness.

`CURRENT_AUDIT.md` is a continuation checkpoint, not evidence that an agent, bot, automation chain, Codex task, or operating-system process is currently running. Runtime liveness must come from the owning runtime; for the automation chain, the sole host-side authority is the operating-system-held dispatcher lease. Its owner record and heartbeat are diagnostic state, not independent locks or grounds for declaring a process live.

When a user opens a new chat and asks to continue prior work, read `CURRENT_AUDIT.md` before inspecting recent commits or GitHub Project rows. Before resuming from a vague instruction such as `continue`, `follow up`, or `resume the audit`, use the handoff as the unfinished-task pointer. Do not infer the active issue from the newest local commit, the most recent Project marker, nearby audit markers, unrelated uncommitted changes, or the handoff by itself when it is inactive, stale, missing, or inconsistent with the user's latest instruction. If no valid active checkpoint exists, ask the user which issue or task to continue.

Successful task closeout requires `CURRENT_AUDIT.md` to be `Inactive` before the final report. Clear the active issue or task, audit type or tier, start time, user request, scope, files touched, completed steps, next step, blockers or questions, and validation status to the inactive sentinels defined in that file; this mutable checkpoint is not a completion ledger. The cleared checkpoint must be included in the final committed and synchronized change—a working-tree-only or unmerged branch copy is insufficient. A required commit, push, review or merge, synchronization, publication, validation, or human-reserved decision that remains part of the same task means the task is not complete: leave a `Paused` or `Blocked` checkpoint with the exact continuation point. If a required external step fails after an intended inactive closeout, reopen the checkpoint before ending. A separate future human-review question belongs in the appropriate Action Item and issue workflow status and does not keep an otherwise completed task open.
