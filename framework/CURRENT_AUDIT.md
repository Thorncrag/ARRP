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
| Active issue/task | RIGHTS-003 / RIGHTS-004 immigration proposal update |
| Audit type/tier | Source-development update / issue admission |
| Started | 2026-07-06 13:26:27 -0400 |
| Last checkpoint | 2026-07-06 13:35:16 -0400 |
| User request | Update RIGHTS-003 after the June 30, 2026 Supreme Court birthright-citizenship ruling and add comprehensive immigration reform as a new RIGHTS proposal. |
| Scope | Reframe RIGHTS-003 as a post-*Trump v. Barbara* statutory and records-continuity proposal, incorporating the separate statutory-vulnerability analysis; admit a new RIGHTS issue for comprehensive immigration reform; sync area, source, audit, GitHub, and Project tracking surfaces. |
| Files touched | `areas/RIGHTS/issues/RIGHTS-003.md`; `areas/RIGHTS/issues/RIGHTS-003.audit.md`; `areas/RIGHTS/issues/RIGHTS-004.md`; `areas/RIGHTS/issues/RIGHTS-004.audit.md`; `areas/RIGHTS/README.md`; `inventory/sources.csv`; `inventory/github_issue_import.csv`; `source-development/project-2025-arrp-crosswalk.md`; `framework/CURRENT_AUDIT.md`. |
| Completed steps | Reframed RIGHTS-003 as a post-*Trump v. Barbara* statutory-recognition and records-continuity issue, including Justice Kavanaugh's separate statutory-vulnerability analysis of 8 U.S.C. § 1401(a); admitted RIGHTS-004 as the A-24 comprehensive immigration reform issue; updated A-24 index, Project 2025 crosswalk, source inventory, GitHub import ledger, GitHub issue #223 title, new GitHub issue #238, and GitHub Project fields for RIGHTS-003 and RIGHTS-004. |
| Next step | For RIGHTS-003, source-develop or draft a statutory citizenship-recognition and records-continuity backstop. For RIGHTS-004, run a no-draft preflight and source-development/remedy-selection pass to decide whether to draft one modular title 8 bill or split narrower vehicles. |
| Blockers/questions | None. |
| Validation status | Passed locally before handoff: `git diff --check`, CSV column-width check for `inventory/sources.csv` and `inventory/github_issue_import.csv`, changed Markdown local-link check, and GitHub Project readback for issues #223 and #238. |

## Handoff Rules

1. Before starting or resuming a long audit, read this file after the governing framework and methodology files.
2. If this file identifies an active issue or task, continue from that checkpoint unless the user gives newer contrary instructions.
3. If this file is inactive or stale and the user says "continue," ask which issue or task to continue instead of inferring from nearby repo state.
4. Update this file at the start of any long audit, after each major phase, before risky edits, and before any likely context handoff.
5. Clear this file back to `Inactive` only after the task is complete, committed/pushed when required, or explicitly paused with a final checkpoint.

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
