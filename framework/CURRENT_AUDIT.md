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
| Active issue/task | Subject and institution index architecture |
| Audit type/tier | Project-level Change Audit |
| Started | 2026-07-14 |
| Last checkpoint | 2026-07-14; implementation complete |
| User request | Begin a project-wide subject index, including organization, department, and agency lookup, and preserve eventual print-edition page locators. |
| Scope | Root and area navigation; subject, agency, office, court, international-body, and State-institution routing; framework and methodology ownership; inventory boundaries; print assembly; first-pass PDF compiler; and Change Audit history. |
| Files touched | `SUBJECT_INDEX.md`; `README.md`; `areas/README.md`; `inventory/README.md`; `framework/FRAMEWORK.md`; `framework/METHODOLOGY.md`; `framework/PRINT_ASSEMBLY.md`; `framework/PROJECT_STRUCTURE.md`; `framework/CHANGE_AUDIT_LOG.md`; `framework/CURRENT_AUDIT.md`; `scripts/build_compiled_pdf.py`. |
| Completed steps | Created and seeded the many-to-many digital index; linked it from project navigation; required ongoing maintenance during proposal and source integration; preserved area/issue ownership and GitHub Project workflow authority; assigned public and technical print treatment; documented two-pass page and page-range resolution; and added the canonical index to the first-pass compiler's back matter and contents list. |
| Next step | Expand terms incrementally as remaining proposals are developed; implement edition-specific locator resolution during the next print/export tooling pass. |
| Blockers/questions | None. |
| Validation status | Passed front-matter parsing, repository-wide local-link checks, index table-shape and identifier-existence checks, `git diff --check`, Python syntax parsing, and bundled-runtime compiler import, 24-area discovery, and index-flowable construction. No GitHub Project or progress-dashboard sync is required because no proposal lifecycle, score, audit, eligibility, or Project field changed. |

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
