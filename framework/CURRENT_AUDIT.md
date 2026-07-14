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
| Active issue/task | Subject and Institution Index; front-door discovery convention |
| Audit type/tier | Project-level Change Audit |
| Started | 2026-07-14 |
| Last checkpoint | 2026-07-14; subject index elevated to a primary opening discovery route |
| User request | Make the Subject and Institution Index readily accessible in the first pages because many readers will look for a topic before learning the project-area taxonomy. |
| Scope | Repository and Project Areas front doors; canonical index convention; print and digital assembly; navigation-bundle ownership; T1 verification; and consolidated same-day Change Audit history. |
| Files touched | `README.md`; `areas/README.md`; `SUBJECT_INDEX.md`; `framework/PRINT_ASSEMBLY.md`; `framework/FRAMEWORK.md`; `framework/METHODOLOGY.md`; `framework/AGENT_OPERATING_RULES.md`; `framework/GITHUB_WORKFLOW.md`; `framework/PROJECT_STRUCTURE.md`; `framework/CHANGE_AUDIT_LOG.md`; `framework/CURRENT_AUDIT.md`. |
| Completed steps | Added a prominent topic-first entry route near the beginning of the repository homepage; elevated the index above the Project Areas list; required future websites and comparable digital editions to expose the index in opening navigation; retained the complete print index in back matter while requiring a resolved front-matter pointer; added the root README to the navigation bundle; and synchronized T1, workflow, structure, agent-validation, and Change Audit conventions. |
| Next step | Carry this front-door convention into the public-website architecture when that framework is implemented. |
| Blockers/questions | None. |
| Validation status | Passed: all 11 changed Markdown files have valid YAML front matter; the repository and Project Areas front doors expose the Subject and Institution Index within their opening lines; the repository front door also exposes area-first discovery; the index remains alphabetized with 133 entries, 88 canonical terms, and 45 valid `See` entries; the front-matter print-pointer and two-pass resolution rules are present; the root README is included consistently in the T1 navigation bundle; all local links resolve across 177 Markdown files; and `git diff --check` passes. No GitHub Project or progress-dashboard sync is required because no proposal lifecycle, score, audit, eligibility, or Project field changes. |

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
