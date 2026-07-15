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
| Status | Active |
| Active issue/task | Topic-page methodology and Project 2025 guide |
| Audit type/tier | Project-level Change Audit continuation |
| Started | 2026-07-15 |
| Last checkpoint | 2026-07-15; topic-page standard codified and Project 2025 guide rewritten |
| User request | Codify concise, nonauthoritative topic-page methodology; track canonical rejected or otherwise adjudicated records and reasons; move reusable methodology off the Project 2025 page; bring that page into compliance. |
| Scope | `topics/`; governing topic-page conventions; Project 2025 crosswalk and documented dispositions; related tests, records, and GitHub governance wrapper. |
| Files touched | `framework/CURRENT_AUDIT.md`; `framework/METHODOLOGY.md`; `framework/FRAMEWORK.md`; `framework/PROJECT_STRUCTURE.md`; `framework/CHANGE_AUDIT_LOG.md`; `topics/README.md`; `topics/project-2025.md`; `tests/test_prepare_public_site.py` |
| Completed steps | Added the reusable Topic Page Standard to the main methodology, including admission, nonauthority, required sections, concise crosswalk fields, canonical disposition treatment, source discipline, the verbatim-transfer ownership test, and prohibited content. Tightened framework and repository ownership summaries. Replaced the Project 2025 development memorandum with a concise overview, routing table, three-column crosswalk, documented HOR-011/HOR-015/HOR-018 dispositions, scope boundary, and source/currency note. Added a regression test and consolidated the work into the existing July 15 topic-guide Change Audit entry. |
| Next step | Validate repository and public-site output, synchronize and read back GitHub issue #8, then commit, push, and verify the Pages deployment. |
| Blockers/questions | None. This governance and navigation pass does not alter proposal substance, score, lifecycle status, rebaseline status, or T-audit Runs. |
| Validation status | In progress. |

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
