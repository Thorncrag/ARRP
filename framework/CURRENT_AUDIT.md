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
| Last checkpoint | 2026-07-14; subject index carried into the implemented public-website architecture |
| User request | Make the Subject and Institution Index readily accessible in the first pages because many readers will look for a topic before learning the project-area taxonomy. |
| Scope | Repository, Project Areas, and public-website front doors; canonical index convention; print and digital assembly; navigation-bundle ownership; T1 verification; and consolidated same-day Change Audit history. |
| Files touched | `README.md`; `areas/README.md`; `SUBJECT_INDEX.md`; `mkdocs.yml`; `requirements-pages.txt`; `.github/workflows/public-site.yml`; `scripts/prepare_public_site.py`; `tests/test_prepare_public_site.py`; `website/`; `framework/PRINT_ASSEMBLY.md`; `framework/FRAMEWORK.md`; `framework/METHODOLOGY.md`; `framework/AGENT_OPERATING_RULES.md`; `framework/GITHUB_WORKFLOW.md`; `framework/PROJECT_STRUCTURE.md`; `framework/PROGRESS_DASHBOARD.md`; `framework/CHANGE_AUDIT_LOG.md`; `framework/CURRENT_AUDIT.md`. |
| Completed steps | Added a prominent topic-first entry route near the beginning of the repository homepage; elevated the index above the Project Areas list; carried that route into the generated website's opening navigation; retained the complete print index in back matter while requiring a resolved front-matter pointer; added the root README to the navigation bundle; established a two-gate public-site allowlist; excluded the progress dashboard and internal apparatus from the Pages artifact; and synchronized T1, workflow, structure, dashboard, validation, and Change Audit conventions. |
| Next step | Verify the first live GitHub Pages deployment after repository publication; thereafter preserve the allowlist and topic-first navigation through ordinary T1 checks. |
| Blockers/questions | None. |
| Validation status | Passed: the repository, Project Areas, and website front doors expose the Subject and Institution Index prominently; the generated site admits 103 canonical public-proposal pages plus one generated legislation index; 114 links to excluded internal Markdown are safely demoted; the dashboard and internal directories are absent from the artifact; all 14 repository tests pass; the strict MkDocs build succeeds; desktop and mobile visual checks show no horizontal overflow; and `git diff --check` passes. No GitHub Project or progress-dashboard data sync is required because no proposal lifecycle, score, audit, eligibility, or Project field changes. |

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
