---
title: "Current Audit Handoff"
status: inactive
print_levels:
  - full-technical
---

# Current Audit Handoff

This file is the first place to check when an ARRP audit, source-development pass, or long-running drafting task resumes in a new chat. It exists to prevent chat-context loss from causing the next agent to infer the wrong active issue from recent commits, GitHub Project rows, or nearby source-development markers.

## Current Task

| Field | Entry |
| --- | --- |
| Status | Inactive |
| Active issue/task | None |
| Audit type/tier | None |
| Started | — |
| Last checkpoint | 2026-07-15; canonical Project 2025 topic-guide conversion and topic-index architecture completed |
| User request | — |
| Scope | — |
| Files touched | — |
| Completed steps | Moved and converted the existing Project 2025 crosswalk into the single canonical public `topics/project-2025.md` guide; added a lightweight `topics/README.md` index beside the Subject Index link; redirected all references and registries; added top-level site navigation, print-builder support, governance conventions, tests, and a consolidated Change Audit entry; retitled and read back GitHub issue #8. The governance issue has no active ARRP Project card, so no Project field required synchronization. |
| Next step | None. Future public-interest topic guides should follow the recorded single-home convention and update the topic index, Subject Index, and authoritative proposal links together. |
| Blockers/questions | None. Proposal scores, statuses, rebaseline fields, and T-audit Runs were unaffected. |
| Validation status | Passed: 18 repository tests; strict MkDocs build; public-manifest and generated-navigation checks; Python syntax checks; compiled-PDF topic discovery; CSV integrity; changed-page local links; stale-path scan; `git diff --check`; and signed-in GitHub issue readback. |

## Handoff Rules

1. Before starting or resuming a long audit, read this file after the governing framework and methodology files.
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
