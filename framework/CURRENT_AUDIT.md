---
title: "Current Audit Handoff"
status: active
print_levels:
  - full-technical
---

# Current Audit Handoff

This file is the first place to check when an ARRP audit, source-development pass, or long-running drafting task resumes in a new chat. It exists to prevent chat-context loss from causing the next agent to infer the wrong active issue from recent commits, GitHub Project rows, or nearby source-development markers.

## Current Task

| Field | Entry |
| --- | --- |
| Status | Inactive |
| Active issue/task | None; ELEC-015 deferred |
| Audit type/tier | Source-development posture / no-audit development note |
| Started | 2026-07-09 15:23:00 -0400 |
| Last checkpoint | 2026-07-10 |
| User request | Set ELEC-015 to deferred pending additional data and additional input. |
| Scope | Defer ELEC-015 after Maine RCV participation synthesis showed no current basis to treat RCV as a primary competition remedy; preserve fixed-zero status and no-draft posture. |
| Files touched | `framework/CURRENT_AUDIT.md`; `areas/ELEC/README.md`; `areas/ELEC/issues/ELEC-015.md`; `areas/ELEC/issues/ELEC-015.audit.md`; GitHub issue #237 and Project item fields. |
| Completed steps | Updated ELEC-015 issue page, audit history, and ELEC area summary to deferred pending additional certified election-outcome data and additional election-method, ballot-access, party-system, and implementation input. |
| Next step | None active. Revisit ELEC-015 after the next midterm election cycle with certified outcome data for RCV jurisdictions and additional expert or stakeholder input. |
| Blockers/questions | None. |
| Validation status | Passed lightweight validation: `inventory/sources.csv` parses with 11 columns across 533 rows; GitHub issue #237 and Project fields read back after sync. |

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
