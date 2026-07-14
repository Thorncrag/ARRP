---
title: "ARRP Agent Operating Rules"
print_levels:
  - full-technical
---

# ARRP Agent Operating Rules

This file governs agent-assisted maintenance, audit execution, and autonomous batch-audit work. It does not replace the project framework or methodology. Agents must begin from [`FRAMEWORK.md`](FRAMEWORK.md), then follow [`METHODOLOGY.md`](METHODOLOGY.md), [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md), the relevant issue page, the linked proposed legislation, and the issue's audit-history file.

Autonomous run provenance is maintained in [`AGENT_AUDIT_LOG.md`](AGENT_AUDIT_LOG.md). Each autonomous batch unit should record its commits there. Ordinary human-invoked audit or drafting sessions should not update the agent audit log unless the user expressly converts the work into an autonomous, batched, or scheduled run.

Active long-running audit handoff state is maintained in [`CURRENT_AUDIT.md`](CURRENT_AUDIT.md). Before resuming from a vague instruction such as "continue," "follow up," or "resume the audit," agents must read that file and use it as the active-task pointer. If `CURRENT_AUDIT.md` is inactive, stale, missing, or inconsistent with the user's latest instruction, ask for the active issue or task instead of inferring from recent commits, GitHub Project rows, or nearby audit markers.

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

## Context Handoff

Long audits and source-development passes should not depend on chat memory alone. Use [`CURRENT_AUDIT.md`](CURRENT_AUDIT.md) as the durable handoff checkpoint for any audit, drafting pass, source-development task, or batch run that may span many tool calls, user interruptions, or a new chat.

Before beginning a long audit, update `CURRENT_AUDIT.md` with the active issue or task, requested tier, scope, expected files, and first next step. During the work, refresh it after each major phase, before broad file edits, before risky or hard-to-reverse decisions, and whenever the conversation appears likely to approach a context handoff.

The checkpoint should identify:

1. active issue or task;
2. audit type or tier;
3. user request;
4. scope and files in play;
5. completed steps;
6. exact next step;
7. blockers or open questions;
8. validation status; and
9. whether work is active, paused, blocked, complete, or inactive.

When a user opens a new chat and asks to continue prior work, read `CURRENT_AUDIT.md` before inspecting recent commits or GitHub Project rows. Do not infer the active issue from the newest local commit, the most recent Project marker, or unrelated uncommitted changes. If no active checkpoint exists, ask the user which issue or task to continue.

When the task is complete, clear `CURRENT_AUDIT.md` back to inactive or leave a final paused checkpoint if the user intends to resume later.

## Single-Issue Default

Issue-quality audits are single-issue workflows by default. An agent should not audit multiple issues in one pass unless the user expressly requests batch mode or a project-wide Change Audit.

Before running a T-audit, an agent must identify:

1. the issue ID;
2. the requested tier or the next tier shown by GitHub Project fields or the issue page;
3. the issue page;
4. the linked legislation page or pages;
5. the sibling audit-history file;
6. the relevant GitHub Project item;
7. the relevant `sources.csv` rows; and
8. any unresolved findings from the latest audit.

Before starting substantive audit work, the agent must also check whether the issue has a linked proposed legislation file, constitutional amendment, enabling legislation, rule text, manual text, model act, or other concrete proposal vehicle. If the issue has only a `Pending development` placeholder or otherwise lacks concrete proposal text, stop and notify the user that no proposed legislation or equivalent vehicle exists yet. Ask for confirmation before proceeding, and make clear that the audit will be limited to source development, issue admission, remedy selection, or fixed-zero/candidate review unless the user wants drafting added to the scope. Do not assign a formula-based Proposal Quality Score until a concrete draft exists.

If the issue ID is unclear, ask the user before running the audit.

## Autonomous Batch Audit Mode

Autonomous Batch Audit Mode is used only when the user expressly asks for autonomous batch auditing.

The batch objective is to move eligible developed proposals toward T4 readiness while conserving resources and avoiding unsupervised substantive overreach.

### Batch Preflight

Before starting an autonomous batch run, the agent must:

1. confirm the working tree is clean, or stop and report the existing uncommitted files without beginning new audit work;
2. confirm the current branch and remote target are understood;
3. confirm the repository can read the latest local project rules, including this file, [`FRAMEWORK.md`](FRAMEWORK.md), [`METHODOLOGY.md`](METHODOLOGY.md), [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md), [`CHANGE_AUDIT_LOG.md`](CHANGE_AUDIT_LOG.md), [`HORIZON_SCAN_LOG.md`](HORIZON_SCAN_LOG.md), and [`AGENT_AUDIT_LOG.md`](AGENT_AUDIT_LOG.md);
4. check the latest relevant audit record before each issue and skip any issue with unresolved human-review blockers unless the user has expressly authorized proceeding; and
5. if the run is scheduled inside a defined work window, confirm that the first planned unit can reasonably fit inside the remaining window.

If the preflight fails, do not begin autonomous edits. Record the reason in [`AGENT_AUDIT_LOG.md`](AGENT_AUDIT_LOG.md) when appropriate and notify the user.

### Eligible Items

By default, include only developed issues with issue pages and linked proposal vehicles. Exclude retired, merged, candidate, pending-development, paused, or awaiting-finding issues unless the user expressly includes them.

Process issues in the GitHub Project queue unless the user gives a different queue. Use issue-page metadata and audit-history sidecars as the detailed audit-score and next-audit record.

### Tier Progression

For each issue:

1. read the latest issue page, linked legislation, sibling audit history, GitHub Project item, and relevant source records;
2. determine the next required audit tier;
3. run only the next appropriate tier unless the prior tier completes cleanly and the next tier is clearly mechanical or already authorized;
4. stop tier progression for that issue if a material unresolved finding requires human review;
5. update the issue page, audit-history file, GitHub Project fields, and source records;
6. validate the changed files;
7. commit and push the completed issue audit;
8. when the audit changes an eligible proposal's Project `Status`, `Score`, or goal eligibility, manually dispatch the Review Ready progress-dashboard workflow after Project readback and push, wait for completion, and verify the generated `progress-dashboard/PROGRESS.md` reflects the new portfolio state; and
9. move to the next eligible issue.

For an expressly authorized batch containing multiple scored audit units, one final dashboard dispatch after the last synchronized Project update and push is sufficient if every unit is already committed and pushed and the generated-page readback confirms the complete batch. The daily schedule is a recovery backstop, not a substitute for audit closeout. Do not edit the generated branch manually.

An agent should not spend the entire autonomous run trying to perfect one issue. If an issue reaches a blocker, document it, preserve it, and proceed.

If an agent adds or materially changes a source, manifestation, institutional framing, damage theory, weakness theory, remedy language, repair/prevention language, or proposal vehicle for a developed issue without running the targeted Change Audit required by the methodology, the agent must mark the issue as needing a targeted Change Audit and Internal Remedy-Fit Audit before treating the score as fully current. The marker should appear in issue front matter, the visible Proposal Scoring or Next Audit line, the issue audit-history file, and any corresponding GitHub Project field.

### Permitted Autonomous Corrections

In batch mode, agents may autonomously fix defects that are mechanical, framework-governed, or directly supported by existing project records, including:

1. broken internal links;
2. missing audit metadata;
3. GitHub Project field and retained source-inventory inconsistencies;
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
8. clearing a `change_audit_needed` marker without performing the targeted Change Audit and Internal Remedy-Fit Audit required by the methodology;
9. making unsupported claims about real-world events, motives, legal effect, polling, or public support;
10. increasing a score based on judgment rather than documented audit findings; or
11. marking a proposal as proposal-ready, publication-ready, or externally validated without the required record.

When a stop condition appears, record the finding in the issue's audit-history file, update the issue-page audit status, next-audit need, and GitHub Project fields, commit and push if files changed, and move on.

## Multi-Agent Use

Multiple agents may be used only for separable work with non-overlapping responsibilities. Examples include:

1. one agent checking source sufficiency while another checks GitHub Project/source-inventory consistency;
2. one agent surveying prior legislation while another checks issue-to-legislation alignment; or
3. one agent validating links while another prepares a narrow issue-page cleanup.

Agents should not edit the same file set at the same time unless a coordinator assigns a clear merge responsibility. A coordinating agent remains responsible for final consistency, validation, commit, and push.

## Resource Budgeting

Batch work should apply the audit tier time estimates as planning ceilings, not obligations. If a tier is complete early, stop early. If a tier is running long, finish only if it is likely to complete within the methodology's overage limit and is not crowding out the rest of the batch.

For scheduled batch windows, the agent should stop before beginning a new audit unit that cannot reasonably be completed, validated, committed, pushed, and logged inside the remaining window. If a unit is already near completion when the window is ending, the agent may finish the current validation/commit/push cycle if doing so is safer than leaving partial work, but should not start a new issue.

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
3. updated GitHub Project fields where applicable;
4. updated `sources.csv` for sources used for audit credit;
5. validation notes; and
6. a commit pushed to GitHub; and
7. when the audit changes an eligible proposal's Project `Status`, `Score`, or goal eligibility, a successful Review Ready progress-dashboard refresh and generated-page readback, or an explicit recorded blocker identifying the failed workflow or stale generated state.

GitHub Project fields are a completion-critical surface for audit work. If the Project row should change but cannot be updated because of authentication, permissions, API, tooling, sandbox, or connector limitations, the agent must notify the user clearly as soon as the failure is known, identify the exact field or row that remains unsynced, and treat the task as blocked or only partially complete until the Project row is updated or the user explicitly accepts a repo-only interim state. Updating the GitHub issue body may be used as a temporary visibility fallback, but it does not replace the required Project-field update.

The Review Ready progress dashboard is a derived completion surface whenever an audit changes goal-relevant Project status, score, or eligibility. After the authoritative Project row has been updated and read back and the audit commit has been pushed, dispatch the workflow, wait for a successful run, and read back the generated page. If dispatch, authentication, workflow execution, publication, or generated-page verification fails, preserve the audit work, identify the stale dashboard value, record the exact remaining sync step in `CURRENT_AUDIT.md`, and do not describe the dashboard as updated. In a multi-unit batch, one verified final refresh may close the whole batch as provided above.

If validation cannot be completed because of a tool or environment failure, preserve the work if possible, record the skipped check, and notify the user.

If commit or push fails, stop the batch after preserving the work locally, record the failure and changed files in the agent audit log or final report, and do not begin another issue until the repository state and authentication problem are resolved.

## Self-Validation Requirement

After each autonomous audit unit and before moving to the next issue, the agent must validate its own work.

If a project validation script exists, run it. If the script supports issue-specific validation, run the issue-specific check for the completed issue and any broader project-level check required by the files changed.

If no validation script exists, perform a manual validation checklist before marking the unit complete:

1. confirm changed Markdown files render structurally and contain no obvious broken local links;
2. confirm issue front matter matches the visible Proposal Scoring section;
3. confirm the sibling audit-history file contains a new entry for the completed audit;
4. confirm the issue page, sibling audit-history file, and GitHub Project fields agree where they overlap;
5. for T1 or a routing-affecting change, confirm the repository front door, project-area contents, affected area contents, Subject and Institution Index, and GitHub issue registry are synchronized under the Navigation Synchronization Check;
6. confirm [`inventory/sources.csv`](../inventory/sources.csv) parses and includes any source used for audit credit;
7. run a whitespace or formatting check where available;
8. confirm the commit hash is recorded in [`AGENT_AUDIT_LOG.md`](AGENT_AUDIT_LOG.md); and
9. if the unit changed goal-relevant Project fields, confirm the Review Ready dashboard workflow completed and the generated page reflects the new state, or record the exact blocker; and
10. confirm no unintended files remain changed for that unit, including generated PDF, DOCX, XLSX, or similar export files unless the user requested an export refresh, the export is the deliverable, export tooling is being tested, or the work is expressly part of a release/publication pass.

If a validation check is skipped, record the skipped check and reason in [`AGENT_AUDIT_LOG.md`](AGENT_AUDIT_LOG.md), in the issue audit history when relevant, or in the final user-facing report. A unit should not be marked complete if validation fails, except when the only failure is an explicitly documented environment or tooling limitation and the work has been preserved for human review.

## Agent Audit Log

Autonomous batch mode must maintain an independent agent audit log in [`AGENT_AUDIT_LOG.md`](AGENT_AUDIT_LOG.md). This log is for operational provenance and rollback planning for unattended or autorun work. It should not replace issue audit histories, GitHub Project tracking, source records, `CURRENT_AUDIT.md` handoff checkpoints, or final user-facing reports.

For each autonomous issue unit, record:

1. date and time with local timezone if available;
2. agent or run identifier if available;
3. issue ID;
4. link to the issue page;
5. link to the issue audit-history file;
6. link to the proposed legislation, constitutional amendment, rule, model text, or other proposal page where one exists;
7. requested tier or task;
8. files changed;
9. validation performed;
10. commit message;
11. commit hash;
12. push status;
13. rollback target or revert notes; and
14. any blockers, skipped checks, or human-review stop conditions.

The agent audit log should be append-only. If a commit is later reverted, add a new log entry identifying the revert commit and the original commit it reverses. Do not erase the original log entry.

Each log entry should be formatted as its own short section with an independent two-column table rather than as a row in a single cumulative table. This keeps long validation notes, rollback notes, and blocker descriptions readable in GitHub and Codex previews. Use this structure:

```markdown
### YYYY-MM-DD — ISSUE-ID — Audit tier or task

| Field | Entry |
| --- | --- |
| Date/time | YYYY-MM-DD HH:MM:SS ±TZ |
| Run/agent | Agent or run label |
| Issue/task | ISSUE-ID or project task |
| Issue page | Link to issue page, or `N/A` |
| Audit history | Link to issue audit-history file, or `N/A` |
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

Increment the GitHub Project **Runs** field only for a completed, separately recorded T0, T1, T2, T3, or T4 issue-quality audit. Change Audits, Internal Remedy-Fit Audits, Horizon Scans, source-development or drafting passes, formatting checks, predicate checks, validation reruns, and continuation of the same open tier do not count as separate runs.

When two reasonable auditors could differ, use the lower score and document why.

## No-Hallucination Rule

Agents must not invent support, sources, facts, polling, legislative history, court posture, professional review, or public reaction. If a claim cannot be verified from the project record or a reliable current source, mark it unresolved and award no favorable score credit for it.
