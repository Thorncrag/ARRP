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
| Audit type/tier | T4/T5 drafting-conversion follow-up |
| Started | 2026-07-04 18:49:20 -0400 |
| Last checkpoint | 2026-07-04 18:57:44 -0400 |
| User request | Restructure ELEC-012 as an amendment to existing election law. |
| Scope | Convert ELEC-012 enabling legislation from a freestanding post-ratification statute into conforming amendments to FECA; rerun score logic; update issue/audit/source bookkeeping and GitHub Project fields. |
| Files touched | `legislation/ELEC-012.md`; `areas/ELEC/issues/ELEC-012.md`; `areas/ELEC/issues/ELEC-012.audit.md`; `areas/ELEC/README.md`; `legislation/README.md`; `inventory/sources.csv`; `framework/CURRENT_AUDIT.md`. |
| Completed steps | Recast ELEC-012 enabling legislation as a FECA conforming-amendment package; raised current score to 75/100 Review Ready; updated issue metadata, scoring summary, audit history, source inventory, and local indexes; ran local validation checks. |
| Next step | T5 legal-readiness audit: legislative-counsel codification check, full Dinner Table merits-document review, Hawaii Act 011 legal-theory comparison, H.J.Res. 54 tailoring, federal cost model, and external constitutional/election-law review. |
| Blockers/questions | GitHub Project field sync could not be applied from this machine because the local `gh` token is invalid and the available GitHub connector does not expose Project V2 field writes. |
| Validation status | Local checks passed: CSV row width, score/front-matter consistency, no trailing whitespace, and `git diff --check`. |

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
