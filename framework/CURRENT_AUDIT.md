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
| Active issue/task | ELEC-012 post-*NRSC*/Maine issue-admission and source-development audit |
| Audit type/tier | T1-style issue-admission/source-development pass |
| Started | 2026-07-02 12:09:13 -0400 |
| Last checkpoint | 2026-07-02 12:17:14 -0400 to completion |
| User request | Run the next audit on ELEC-012. |
| Scope | Completed ELEC-012 current candidate-posture review after *NRSC*, Maine comparators, and prior campaign-finance reform proposals; updated the issue page, audit history, source inventory, GitHub Project fields, and handoff record. Generated exports were out of scope under the pre-1.0 export policy. |
| Files touched | `areas/ELEC/issues/ELEC-012.md`; `areas/ELEC/issues/ELEC-012.audit.md`; `inventory/sources.csv`; `framework/CURRENT_AUDIT.md`. |
| Completed steps | Ran bounded T1-style issue-admission/source-development pass; added prior-proposal routing for Democracy for All, We the People / Move to Amend, DISCLOSE Act, For the People Act, Freedom to Vote Act, and REAL Political Advertisements Act families; added source rows SRC-0370 through SRC-0376; kept score fixed at 0 pending remedy selection; synced GitHub Project issue #40 fields. |
| Next step | Run T2 remedy-selection and prior-proposal comparison. |
| Blockers/questions | None. |
| Validation status | Passed CSV parse, whitespace check, focused internal Markdown link target check, and GitHub Project field verification. |

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
