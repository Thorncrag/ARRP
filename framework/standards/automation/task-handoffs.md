---
title: "Agent Rules — Context Handoff"
dependencies:
  - "../../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Agent Rules — Context Handoff

Load this module when a task may span many tool calls, user interruptions,
context compaction, or a new session; whenever the project's durable handoff
checkpoint is opened or changed; and whenever the user asks to continue,
follow up, or resume prior work without identifying the task.

## Context Handoff

Long audits, source-development passes, and other substantial tasks should not
depend on chat memory alone. Use the project-designated durable handoff
checkpoint whenever work may span many tool calls, user interruptions, context
compaction, or a new session.

Before beginning substantial work, update the checkpoint with the active issue
or task, requested operation, scope, expected files, and first next step.
Refresh it after each major phase, before broad file edits, before risky or
hard-to-reverse decisions, and whenever the conversation approaches a context
handoff.

The checkpoint should identify:

1. active issue or task;
2. audit type or tier;
3. user request;
4. scope and files in play;
5. completed steps;
6. exact next step;
7. blockers or open questions;
8. validation status; and
9. the project-configured continuation state.

Continuation states describe whether work is unfinished, deliberately paused,
blocked by an indispensable prerequisite, or complete. The project
implementation must define their exact names and required evidence. A
continuation state never establishes runtime liveness.

The handoff is a continuation checkpoint, not evidence that an agent, bot,
automation chain, task, or operating-system process is currently running.
Runtime liveness must come from the owning runtime.

When a user opens a new session and asks to continue prior work, read the
handoff before inspecting recent revisions or hosted-workflow rows. For a vague
instruction such as `continue`, `follow up`, or `resume the audit`, use it as
the unfinished-task pointer. Do not infer the active issue from the newest
revision, nearby markers, unrelated uncommitted changes, or a handoff that is
complete, stale, missing, or inconsistent with the user's latest instruction.
If no valid active checkpoint exists, ask which issue or task to continue.

Successful closeout requires the checkpoint to enter its configured completed
state before the final report. Clear mutable task fields to the sentinels
defined by the checkpoint; it is not a completion ledger. The cleared
checkpoint must be included in the final synchronized change—a working-tree
copy or unmerged branch is insufficient. Any required preservation, review,
merge, synchronization, publication, validation, or human-reserved decision
that remains part of the same task means the task is unfinished: retain the
exact continuation point. If an external step fails after intended closeout,
reopen the checkpoint before ending. A separate future human-review question
belongs in the project's decision-routing surface and does not keep an
otherwise completed task open.
