---
title: "Current Audit Handoff"
status: active
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Current Audit Handoff

This file is the first place to check when an ARRP audit, source-development pass, or long-running drafting task resumes in a new chat. It exists to prevent chat-context loss from causing the next agent to infer the wrong active issue from recent commits, GitHub Project rows, or nearby source-development markers.

## Current Task

| Field | Entry |
| --- | --- |
| Status | Active |
| Active issue/task | Surface open pull requests requiring human disposition in the Console Action Items view. |
| Audit type/tier | Console administration and human-review routing |
| Started | 2026-07-24 12:30:00 -0400 |
| Last checkpoint | 2026-07-24 12:30:00 -0400 |
| User request | Show unresolved pull or merge requests in Action Items so every human-review obligation is visible in one place. |
| Scope | Console data generation and Action Items presentation; open ARRP pull requests; no automatic merge or disposition. |
| Files touched | None yet for the new task. |
| Completed steps | Host-reconciled Elim's linked-vehicle context repair through pull request [#391](https://github.com/Thorncrag/ARRP/pull/391) after its required checks passed. Identified four pre-existing open human-review pull requests: #381, #380, #378, and #361. |
| Next step | Add a deterministic open-pull-request feed to Action Items, distinguish bot/dependency review from automation failure, link each item to GitHub, add regression coverage, rebuild the Console, validate, and reconcile through the reviewed workflow. |
| Blockers/questions | None. |
| Validation status | Linked-vehicle repair passed 194 repository tests, 24 participation-service tests, authenticated consistency with 0 errors and 0 warnings, CodeQL, Vercel, syntax, and diff hygiene. New Console work not yet started. |

## Handoff Rules

1. Before starting or resuming a long audit, read this file after the governing Framework and Agent Operating Rules.
2. If this file identifies an active issue or task, continue from that checkpoint unless the user gives newer contrary instructions.
3. If this file is inactive or stale and the user says "continue," ask which issue or task to continue instead of inferring from nearby repo state.
4. Update this file at the start of any long audit, after each major phase, before risky edits, and before any likely context handoff.
5. Clear this file back to `Inactive` only after the task is complete, committed and pushed when a GitHub remote is available, the related GitHub issue wrapper and GitHub Project item have been updated or verified when the task changes tracked fields, and any unfinished sync step is either completed or explicitly paused with a final checkpoint.
6. Do not use GitHub issue comments as the ordinary audit-history record. Keep substantive audit history in the issue's sibling audit-history file; use the GitHub issue wrapper and Project fields for workflow status, links, score, last audit, next audit, rebaseline status, and change-audit flags.

## Checkpoint Template

```markdown
## Current Task

| Field | Entry |
| --- | --- |
| Status | Active / Paused / Blocked / Inactive |
| Active issue/task | ISSUE-ID or project task |
| Audit type/tier | T0 / T1 / T2 / T3 / T4 / Change Audit / Horizon Scan / drafting |
| Started | YYYY-MM-DD HH:MM:SS -0400 |
| Last checkpoint | YYYY-MM-DD HH:MM:SS -0400 |
| User request | Short restatement of the user's instruction |
| Scope | Files/issues/sources being reviewed |
| Files touched | `path`; `path`; or None yet |
| Completed steps | Short progress summary |
| Next step | Exact next action for a new chat |
| Blockers/questions | None, or concise blocker |
| Validation status | Not started / In progress / Passed / Failed with reason |
```
