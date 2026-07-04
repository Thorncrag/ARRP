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
| Active issue/task | ELEC-012 |
| Audit type/tier | T3 source and legal-readiness audit |
| Started | 2026-07-04 16:19:53 -0400 |
| Last checkpoint | 2026-07-04 16:30:10 -0400 |
| User request | Audit ELEC-012. |
| Scope | Run the next progressive audit for ELEC-012, focused on FECA codification, amendment conformity, state comparators, disclosure/privacy tailoring, adoption evidence, source inventory, issue-page scoring, linked legislation notes, and GitHub Project synchronization. |
| Files touched | `framework/CURRENT_AUDIT.md`; `areas/ELEC/issues/ELEC-012.md`; `areas/ELEC/issues/ELEC-012.audit.md`; `legislation/ELEC-012.md`; `legislation/ELEC-012-amendment.md`; `inventory/sources.csv`. |
| Completed steps | Completed T3 source and legal-readiness audit; updated ELEC-012 score to 69/100; added full audit sidecar entry; refreshed issue-page annotations, source notes, linked legislation notes, source inventory rows, and stale next-audit language; validated CSV width and duplicate IDs; ran whitespace and stale-score checks. |
| Next step | Commit and push the ELEC-012 T3 audit, then synchronize GitHub Project issue #40 with score 69, Developed draft status, updated run count, last audit, next audit, rebaseline current, and change audit no. |
| Blockers/questions | Qualified external constitutional-law, election-law, legislative-counsel, FEC practitioner, state-campaign-finance, fiscal, and stakeholder review is unavailable in-session. |
| Validation status | Passed locally; GitHub Project synchronization pending. |

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
