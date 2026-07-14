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
| Active issue/task | Unified subject and institution index; navigation synchronization and audit integration |
| Audit type/tier | Project-level Change Audit |
| Started | 2026-07-14 |
| Last checkpoint | 2026-07-14; indexing conventions centralized and navigation synchronization attached to T1 |
| User request | Memorialize all subject-index conventions; update the index with the ordinary table of contents; and attach formal verification to T0 or T1 using the best-fitting audit design. |
| Scope | `SUBJECT_INDEX.md`; project-area and area-level contents ownership; framework, methodology, GitHub workflow, agent validation, project structure, and consolidated same-day Change Audit history. |
| Files touched | `SUBJECT_INDEX.md`; `framework/FRAMEWORK.md`; `framework/METHODOLOGY.md`; `framework/AGENT_OPERATING_RULES.md`; `framework/GITHUB_WORKFLOW.md`; `framework/PROJECT_STRUCTURE.md`; `framework/CHANGE_AUDIT_LOG.md`; `framework/CURRENT_AUDIT.md`. |
| Completed steps | Preserved the prior streamlined single-table, common-term redirect, functional-name, and centralized-disposition conventions; consolidated all reader-index rules in the index's `Indexing and Contents Synchronization Standard`; identified `areas/README.md`, the affected area README, `SUBJECT_INDEX.md`, and the GitHub issue registry as one navigation bundle; required immediate same-change updates for routing events; made T1 the mandatory Navigation Synchronization Check within project integration and formatting preflight; limited T0 to flagging obvious drift for existing stable records; prohibited indexing unadmitted Horizon candidates; and synchronized framework, methodology, workflow, agent-validation, structure, and Change Audit rules. |
| Next step | Apply the Navigation Synchronization Check at T1 and update the navigation bundle immediately whenever routing changes rather than waiting for an audit. |
| Blockers/questions | None. |
| Validation status | Passed: eight changed files have valid YAML front matter; the subject index contains 133 alphabetized entries, including 88 canonical entries and 45 `See` entries whose 46 references all resolve to canonical terms; all local links resolve across 177 Markdown files; the project-area contents matches all 24 area directories; the GitHub issue registry parses as 245 seven-column records; T0/T1 navigation rules are present on the governing surfaces; and `git diff --check` passes. No GitHub Project or progress-dashboard sync is required because no proposal lifecycle, score, audit, eligibility, or Project field changes. |

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
