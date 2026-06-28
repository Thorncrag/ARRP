---
title: "ARRP Agent Operating Rules"
print_levels:
  - full-technical
---

# ARRP Agent Operating Rules

This file governs agent-assisted maintenance, audit execution, and autonomous batch-audit work. It does not replace the project framework or methodology. Agents must begin from [`framework/FRAMEWORK.md`](framework/FRAMEWORK.md), then follow [`framework/METHODOLOGY.md`](framework/METHODOLOGY.md), [`AUDIT_DASHBOARD.md`](AUDIT_DASHBOARD.md), the relevant issue page, the linked proposed legislation, and the issue's audit-history file.

Autonomous run provenance is maintained in [`AGENT_AUDIT_LOG.md`](AGENT_AUDIT_LOG.md). Each autonomous batch unit should record its commits there.

## Purpose

Agent work should improve the project carefully, conservatively, and reproducibly. The goal is not maximum speed. The goal is reliable stewardship of the project record, the user's attention, and GPT/account resources.

Agents should prefer steady, bounded work over broad speculative work. When an agent can complete a reasonable check in less time or with fewer sources than allocated, it should stop rather than fill the available time.

## Resource Stewardship

Agents should use the least resource-intensive method that can responsibly satisfy the assigned task.

1. Start with local project files before using external searches.
2. Use targeted searches rather than broad repeated queries.
3. Prefer primary sources and already-captured source inventory rows.
4. Reuse verified source records where still current and relevant.
5. Avoid duplicating completed audit work unless a changed rule, changed fact, or explicit user request requires it.
6. Do not run multiple agents on the same files or same unresolved question.
7. Do not continue researching after the audit tier's question has been responsibly answered.
8. If a source path or theory is not producing useful results, document the limitation and move on.
9. If a proposal is blocked by a human-review issue, document the blocker and advance to the next eligible item rather than spending the batch budget on speculative repair.
10. Commit and push completed units promptly so work is preserved and later agents do not repeat it.

## Single-Issue Default

Issue-quality audits are single-issue workflows by default. An agent should not audit multiple issues in one pass unless the user expressly requests batch mode or a project-wide Change Audit.

Before running a T-audit, an agent must identify:

1. the issue ID;
2. the requested tier or the next tier shown by the dashboard;
3. the issue page;
4. the linked legislation page or pages;
5. the sibling audit-history file;
6. the relevant `audits.csv` row;
7. the relevant `sources.csv` rows; and
8. any unresolved findings from the latest audit.

If the issue ID is unclear, ask the user before running the audit.

## Autonomous Batch Audit Mode

Autonomous Batch Audit Mode is used only when the user expressly asks for autonomous batch auditing.

The batch objective is to move eligible developed proposals toward T4 readiness while conserving resources and avoiding unsupervised substantive overreach.

### Eligible Items

By default, include only developed issues with issue pages and linked proposal vehicles. Exclude retired, merged, candidate, pending-development, paused, or awaiting-finding issues unless the user expressly includes them.

Process issues in [`AUDIT_DASHBOARD.md`](AUDIT_DASHBOARD.md) order unless the user gives a different queue.

### Tier Progression

For each issue:

1. read the latest issue page, linked legislation, sibling audit history, dashboard row, and inventory rows;
2. determine the next required audit tier;
3. run only the next appropriate tier unless the prior tier completes cleanly and the next tier is clearly mechanical or already authorized;
4. stop tier progression for that issue if a material unresolved finding requires human review;
5. update the issue page, audit-history file, dashboard, and inventory rows;
6. validate the changed files;
7. commit and push the completed issue audit; and
8. move to the next eligible issue.

An agent should not spend the entire autonomous run trying to perfect one issue. If an issue reaches a blocker, document it, preserve it, and proceed.

### Permitted Autonomous Corrections

In batch mode, agents may autonomously fix defects that are mechanical, framework-governed, or directly supported by existing project records, including:

1. broken internal links;
2. missing audit metadata;
3. dashboard and CSV inconsistencies;
4. missing or stale source-inventory capture;
5. missing Proposal Scoring fields required by the current template;
6. missing audit-history entries;
7. obvious primary-source substitutions for secondary legal references;
8. citation placement and source-note cleanup;
9. budgetary-impact placeholder formatting where no substantive estimate is added; and
10. spelling, heading, metadata, and template conformance fixes.

### Human-Review Stop Conditions

In batch mode, agents must document and stop work on the affected issue before making any of the following changes unless the user has expressly pre-authorized that class of change:

1. retiring, merging, admitting, or materially reclassifying an issue;
2. changing the core institutional diagnosis;
3. changing the least-complex adequate remedy;
4. rewriting proposed legislation into a materially different legal vehicle;
5. converting a freestanding bill into amendments to existing law;
6. adding a constitutional amendment or removing one;
7. resolving a substantive discrepancy between an issue page and proposed legislation;
8. making unsupported claims about real-world events, motives, legal effect, polling, or public support;
9. increasing a score based on judgment rather than documented audit findings; or
10. marking a proposal as proposal-ready, publication-ready, or externally validated without the required record.

When a stop condition appears, record the finding in the issue's audit-history file, update the compact audit status and next-audit need, commit and push if files changed, and move on.

## Multi-Agent Use

Multiple agents may be used only for separable work with non-overlapping responsibilities. Examples include:

1. one agent checking source sufficiency while another checks dashboard/CSV consistency;
2. one agent surveying prior legislation while another checks issue-to-legislation alignment; or
3. one agent validating links while another prepares a narrow issue-page cleanup.

Agents should not edit the same file set at the same time unless a coordinator assigns a clear merge responsibility. A coordinating agent remains responsible for final consistency, validation, commit, and push.

## Resource Budgeting

Batch work should apply the audit tier time estimates as planning ceilings, not obligations. If a tier is complete early, stop early. If a tier is running long, finish only if it is likely to complete within the methodology's overage limit and is not crowding out the rest of the batch.

When deciding whether to continue research, ask:

1. Will this likely change the score, remedy, source reliability, or next-audit need?
2. Is there a primary source likely to answer the question quickly?
3. Has the issue already hit a human-review stop condition?
4. Would the same time be better spent documenting the blocker and moving to the next issue?

If the answer favors stopping, stop.

## Output and Preservation

Each completed issue audit should leave:

1. updated issue-page Proposal Scoring and metadata;
2. a new sibling audit-history entry;
3. updated dashboard row and aggregate counts where applicable;
4. updated `audits.csv`;
5. updated `sources.csv` for sources used for audit credit;
6. validation notes; and
7. a commit pushed to GitHub.

If validation cannot be completed because of a tool or environment failure, preserve the work if possible, record the skipped check, and notify the user.

## Self-Validation Requirement

After each autonomous audit unit and before moving to the next issue, the agent must validate its own work.

If a project validation script exists, run it. If the script supports issue-specific validation, run the issue-specific check for the completed issue and any broader project-level check required by the files changed.

If no validation script exists, perform a manual validation checklist before marking the unit complete:

1. confirm changed Markdown files render structurally and contain no obvious broken local links;
2. confirm issue front matter matches the visible Proposal Scoring section;
3. confirm the sibling audit-history file contains a new entry for the completed audit;
4. confirm [`inventory/audits.csv`](inventory/audits.csv) parses and matches the issue page and [`AUDIT_DASHBOARD.md`](AUDIT_DASHBOARD.md);
5. confirm [`inventory/sources.csv`](inventory/sources.csv) parses and includes any source used for audit credit;
6. confirm dashboard aggregate counts changed when relevant;
7. run a whitespace or formatting check where available;
8. confirm the commit hash is recorded in [`AGENT_AUDIT_LOG.md`](AGENT_AUDIT_LOG.md); and
9. confirm no unintended files remain changed for that unit.

If a validation check is skipped, record the skipped check and reason in [`AGENT_AUDIT_LOG.md`](AGENT_AUDIT_LOG.md), in the issue audit history when relevant, or in the final user-facing report. A unit should not be marked complete if validation fails, except when the only failure is an explicitly documented environment or tooling limitation and the work has been preserved for human review.

## Agent Audit Log

Autonomous batch mode must maintain an independent agent audit log in [`AGENT_AUDIT_LOG.md`](AGENT_AUDIT_LOG.md). This log is for operational provenance and rollback planning. It should not replace issue audit histories, the Audit Dashboard, `audits.csv`, or source records.

For each autonomous issue unit, record:

1. date and time if available;
2. agent or run identifier if available;
3. issue ID;
4. link to the issue page;
5. link to the proposed legislation, constitutional amendment, rule, model text, or other proposal page where one exists;
6. requested tier or task;
7. files changed;
8. validation performed;
9. commit message;
10. commit hash;
11. push status;
12. rollback target or revert notes; and
13. any blockers, skipped checks, or human-review stop conditions.

The agent audit log should be append-only. If a commit is later reverted, add a new log entry identifying the revert commit and the original commit it reverses. Do not erase the original log entry.

Each log entry should be formatted as its own short section with an independent two-column table rather than as a row in a single cumulative table. This keeps long validation notes, rollback notes, and blocker descriptions readable in GitHub and Codex previews. Use this structure:

```markdown
### YYYY-MM-DD — ISSUE-ID — Audit tier or task

| Field | Entry |
| --- | --- |
| Date/time | YYYY-MM-DD |
| Run/agent | Agent or run label |
| Issue/task | ISSUE-ID or project task |
| Issue page | Link to issue page, or `N/A` |
| Proposal page | Link to proposed legislation, amendment, rule, or model text; use `N/A` if none exists |
| Tier | T1/T2/T3/T4/change/etc. |
| Files changed | `path`; `path` |
| Validation | Checks performed |
| Commit | `Commit message` (`hash`) |
| Push status | Pushed to `origin/main` |
| Rollback notes | Revert `hash` to roll back this unit. |
| Blockers/skipped checks | No blocker, or concise blocker/skipped-check note. |
```

Autonomous agents must not force-push. Rollback should normally occur through a revert commit so GitHub history remains intelligible.

## Conservative Scoring

Agents should not treat repeated audit runs as proof of quality. Scores increase only when the record improves under the methodology: better sources, better legal fit, clearer drafting, stronger implementation analysis, resolved defects, stronger adoption evidence, or documented external review.

When two reasonable auditors could differ, use the lower score and document why.

## No-Hallucination Rule

Agents must not invent support, sources, facts, polling, legislative history, court posture, professional review, or public reaction. If a claim cannot be verified from the project record or a reliable current source, mark it unresolved and award no favorable score credit for it.
