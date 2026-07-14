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
| Active issue/task | Unified subject and institution index; common-term, functional-name, and disposition routing |
| Audit type/tier | Project-level Change Audit |
| Started | 2026-07-14 |
| Last checkpoint | 2026-07-14; common-term redirects, functional institutional names, and centralized rejected-candidate routing implemented |
| User request | Trim and streamline the subject index, replace full proposal titles with precise identifiers, remove the unclear `Material related issues` structure, merge entity and topic entries, add high-value conventional redirects for common terms readers are likely to seek, alphabetize departments and other institutions by familiar functional names or acronyms rather than generic prefixes, and catalog rejected or outside-scope candidates in one place rather than listing each independently. |
| Scope | `SUBJECT_INDEX.md`; the Horizon disposition catalog; governing index rules in the framework, methodology, and print-assembly instructions; consolidated same-day Change Audit history. |
| Files touched | `SUBJECT_INDEX.md`; `framework/HORIZON_SCAN_LOG.md`; `framework/FRAMEWORK.md`; `framework/METHODOLOGY.md`; `framework/PRINT_ASSEMBLY.md`; `framework/PROJECT_STRUCTURE.md`; `framework/CHANGE_AUDIT_LOG.md`; `framework/CURRENT_AUDIT.md`. |
| Completed steps | Replaced full destination titles and explanatory prose with linked record identifiers; removed the primary/related schema; merged entities, topics, acronyms, and aliases into one alphabetical table; consolidated closely overlapping ICC, Inspector General, and IRS entries; added common-term **See** redirects; reordered departments, courts, offices, and services by familiar functional names or acronyms while preserving formal names; established the Horizon Scan Log as the single catalog for rejected, retired, and outside-scope candidates; replaced individual D.C. and Puerto Rico statehood entries with one general disposition route; marked the preferred destination first; retained alternate routes only when useful; and synchronized governing and print-assembly rules. |
| Next step | Maintain the single alphabetical format, using functional institutional names, adding **See** redirects only for genuinely common alternate terms, and routing rejected candidates only through the disposition catalog. |
| Blockers/questions | None. |
| Validation status | Passed front-matter parsing for the index and Horizon log; alphabetical-order and duplicate-term checks across 133 unique entries; two-column index table-shape validation; resolution of all 46 **See** and **See also** targets to 88 canonical entries; functional-name validation with no generic `Department of`, `United States`, or `Office of` opening entries; centralized disposition validation with no individual D.C. or Puerto Rico statehood rows and one general Horizon-log route; repository-wide local-link validation across 177 Markdown files; stale-schema scans; and `git diff --check`. No GitHub Project or progress-dashboard sync is required because no proposal lifecycle, score, audit, eligibility, or Project field changes. |

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
