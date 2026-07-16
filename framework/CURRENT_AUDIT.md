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
| Status | Active — restoring the established qualitative evidence-page standard |
| Active issue/task | Evidence placement correction for DOJ-002, REG-001, and RIGHTS-002 |
| Audit type/tier | Project methodology and source development; no T-audit run |
| Started | 2026-07-16 |
| Last checkpoint | 2026-07-16; user confirmed that evidence-page creation is governed by whether the issue page already contains sufficient strong support, not by evidence quantity |
| User request | Restore the previously established qualitative placement rule and correct the mechanical creation of one-item evidence pages. |
| Scope | DOJ-002, REG-001, and RIGHTS-002 evidence placement; issue-evidence methodology and template; adjudication safeguards; source records; tests; and consolidated Change Audit documentation. |
| Files touched | `areas/DOJ/evidence/DOJ-002-evidence.md` (removed); `areas/DOJ/issues/DOJ-002.md`; `areas/REG/evidence/REG-001-evidence.md` (removed); `areas/REG/issues/REG-001.md`; `areas/RIGHTS/evidence/RIGHTS-002-evidence.md` (removed); `areas/RIGHTS/issues/RIGHTS-002.md`; `framework/CHANGE_AUDIT_LOG.md`; `framework/CURRENT_AUDIT.md`; `framework/ISSUE_EVIDENCE_TEMPLATE.md`; `framework/METHODOLOGY.md`; `inventory/sources.csv`; `research/trump-administration-legal-review-intake.md`; `scripts/apply_source_adjudication.py`; `tests/test_horizon_intake.py`; `tests/test_source_adjudication.py`. |
| Completed steps | Removed the three unwarranted one-item evidence pages; placed the DOJ-002 and REG-001 boundary decisions concisely in Annotation and the vacated RIGHTS-002 opinion in Source Notes; restored a qualitative sufficiency-and-reader-value standard throughout methodology, template, intake instructions, source records, automation, tests, and the consolidated Change Audit entry; retained the 54 incomplete episode tasks; and passed all 34 tests, public-site preparation, stale-link review, and diff validation. |
| Next step | Commit and push the completed correction, verify the affected GitHub Project rows remain unchanged, and close this handoff. |
| Blockers/questions | None. |
| Validation status | Passed: 34 unit tests, public-site preparation, stale evidence-link search, and `git diff --check`. |

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
