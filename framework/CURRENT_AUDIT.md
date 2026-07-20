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
| Status | Active — completed locally; awaiting commit and GitHub reconciliation |
| Active issue/task | Consolidate retained sources, remove redundant ledgers, and colocate single-area research with its owning area |
| Audit type/tier | Project-wide source and structure reconciliation; no T-audit or score change |
| Started | 2026-07-20 |
| Last checkpoint | 2026-07-20; two-catalog migration, obsolete-file cleanup, complete monitor-bot migration, area-research relocation, console rebuild, and validation completed locally. |
| User request | Review every research-directory document, route all sources into the two canonical catalogs, clean up obsolete files, and move issue-specific research into its most relevant area. |
| Scope | Root and area `research/` directories; source inventories; candidate console; monitoring automation and GitHub monitor wrappers; governing methodology, structure, tests, and internal links. |
| Files touched | `inventory/sources.csv`; `inventory/sources-pending.csv`; central and area research; governing framework; console builder; consistency audit; monitoring configuration and tests; obsolete research and source-adjudication files. |
| Completed steps | Classified the research directory; consolidated 34 duplicate source IDs; reconciled every retained source into one of the two catalogs; removed obsolete source, media, litigation, integration, and directive queues and their dedicated tooling; made GitHub monitoring issues authoritative; replaced the five-record monitor pilot with dynamic discovery of all 37 open `needs: monitoring` records and permanent `SRC-####` mappings; retired the obsolete standalone monitor-row identifiers from the repository and live issue descriptions; moved eleven single-area research assets into six area `research/` directories; updated local and GitHub links and source locators; expanded console and consistency-check discovery to area research; rebuilt the candidate console; and verified that every `sources.csv` row is used while every pending row has an accountable owner. |
| Next step | Commit and reconcile the completed pass with GitHub, manually dispatch the complete monitor workflow, and verify all rolling comments, owner notification, and read-only safeguards before the first scheduled run. |
| Blockers/questions | None. |
| Validation status | Complete locally: 46 tests passed; the full 37-record read-only monitor test completed with 22 adapter-supported and 15 manual-only records; authenticated consistency audit returned 0 errors and 0 warnings; strict public-site build passed; `git diff --check` passed. |

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
