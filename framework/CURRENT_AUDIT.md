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
| Status | Active — correcting evidence-page integration for the judicial pilot |
| Active issue/task | Linked evidence records and restoration of unresolved existing-issue evidence |
| Audit type/tier | Project methodology and source development; no T-audit run |
| Started | 2026-07-16 |
| Last checkpoint | 2026-07-16; user correctly identified that source-inventory routing was not the linked evidence-subpage integration previously approved |
| User request | Correct the pilot so retained evidence is placed on a concise evidence subpage linked from the receiving issue page, rather than treating `sources.csv` associations as completed integration. |
| Scope | DOJ-002, REG-001, and RIGHTS-002 linked evidence records; the unresolved evidence for undeveloped receiving issues; governing source-adjudication methodology; migration safeguards; source associations; tests; and consolidated Change Audit documentation. |
| Files touched | `areas/DOJ/evidence/DOJ-002-evidence.md`; `areas/DOJ/issues/DOJ-002.md`; `areas/REG/evidence/REG-001-evidence.md`; `areas/REG/issues/REG-001.md`; `areas/RIGHTS/evidence/RIGHTS-002-evidence.md`; `areas/RIGHTS/issues/RIGHTS-002.md`; `framework/CHANGE_AUDIT_LOG.md`; `framework/FRAMEWORK.md`; `framework/ISSUE_EVIDENCE_TEMPLATE.md`; `framework/METHODOLOGY.md`; `inventory/sources.csv`; `research/existing-issue-evidence-integration.csv`; `research/horizon-review-console/catalog-data.js`; `research/horizon-review-console/index.html`; `research/trump-administration-legal-review-intake.md`; `scripts/apply_source_adjudication.py`; `scripts/build_horizon_review_console.py`; `tests/test_horizon_intake.py`; `tests/test_source_adjudication.py`. |
| Completed steps | Created and linked three reader-facing evidence records; restored 54 episode-level tasks to the undeveloped-or-unverified issue-integration queue; distinguished source registration from evidence integration throughout the governing rules; added a removal guard to the adjudication script; corrected console terminology and counts; synchronized the source registry; moved RIGHTS-002 to `In development` without changing its score or runs; passed all 33 tests, public-site preparation, and diff validation; and verified the affected GitHub Project rows. |
| Next step | Commit and push the completed correction, then perform final repository and GitHub readback. |
| Blockers/questions | None. |
| Validation status | Passed: 33 unit tests, public-site preparation, `git diff --check`, queue reconciliation, issue-to-evidence links, and GitHub Project readback. |

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
