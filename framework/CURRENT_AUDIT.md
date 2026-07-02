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
| Active issue/task | ELEC-012 Maine campaign-finance comparator integration |
| Audit type/tier | Source-development / targeted current-status update |
| Started | 2026-07-02 10:49:30 -0400 |
| Last checkpoint | 2026-07-02 10:52:58 -0400 to completion |
| User request | Integrate Maine campaign-finance laws into the ELEC-012 discussion. |
| Scope | Completed ELEC-012 update with Maine's independent-expenditure PAC contribution-limit experiment and foreign-government-influenced entity restrictions; added source inventory rows; updated audit history, public PDF export, and GitHub Project audit fields. |
| Files touched | `areas/ELEC/issues/ELEC-012.md`; `areas/ELEC/issues/ELEC-012.audit.md`; `inventory/sources.csv`; `exports/pdf/ARRP-public-proposal-draft.pdf`; `framework/CURRENT_AUDIT.md`. |
| Completed steps | Integrated Maine's super PAC contribution-limit law as a direct *SpeechNow* source-development comparator; integrated Maine's foreign government-influenced entity law as a foreign-money/entity-control comparator with litigation caution; added source rows SRC-0365 through SRC-0369; rebuilt the public PDF; synced GitHub Project fields for issue #40. |
| Next step | None unless the user requests a deeper post-*NRSC*/Maine issue-admission and source-development pass. |
| Blockers/questions | None. |
| Validation status | Passed CSV parse, text-file whitespace check excluding generated PDF internals, focused internal Markdown link target check, PDF rebuild, and GitHub Project field verification. |

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
