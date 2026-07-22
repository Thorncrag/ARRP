---
title: "ARRP Agent Operating Rules"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# ARRP Agent Operating Rules

This file is the canonical detailed manual for all agents and bots, including ordinary agent-assisted maintenance, audit execution, deterministic automation, and expressly authorized autonomous or scheduled work. In ARRP terminology, a **bot** is a deterministic script or program, while an **agent** is an LLM-directed worker. Scheduling or event triggering does not change that distinction: every deterministic bot uses a stable `-bot` designation, and an LLM agent does not. This file does not replace the substantive [`FRAMEWORK.md`](FRAMEWORK.md), GitHub mechanics in [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md), or the narrower security-sensitive public-intake rules in [`INTAKE_AGENT_PROCESS.md`](INTAKE_AGENT_PROCESS.md). Agents must begin with the Framework, then read the GitHub workflow and specialized records implicated by the task, together with the relevant issue page, proposed vehicle, and audit history when issue work is involved.

Persistent-agent provenance is maintained in the shared [`AGENT_AUDIT_LOG.md`](logs/AGENT_AUDIT_LOG.md). Every material autonomous agent or bot unit records its action there under a stable Agent ID and Run ID. Ordinary human-invoked audit or drafting sessions should not update the agent audit log unless the user expressly converts the work into an autonomous, batched, or scheduled run.

Active long-running audit handoff state is maintained in [`CURRENT_AUDIT.md`](logs/CURRENT_AUDIT.md). Before resuming from a vague instruction such as "continue," "follow up," or "resume the audit," agents must read that file and use it as the active-task pointer. If `CURRENT_AUDIT.md` is inactive, stale, missing, or inconsistent with the user's latest instruction, ask for the active issue or task instead of inferring from recent commits, GitHub Project rows, or nearby audit markers.

## Issue-Development Lifecycle Trigger

Any request to focus on, research, develop, draft, revise, or otherwise work substantively on an issue invokes the issue-development lifecycle workflow even when the user does not mention an audit or status update. Before editing, read the canonical issue page, linked vehicle, latest audit entry, next step, and authoritative GitHub Project row.

If substantive work begins from `Status: Pending development`, change the workflow `Status` to `In development` and read it back. At closeout, synchronize the independent `Development level` and `Status` fields: an incomplete package with an approved foundation uses `Development level: In development`; its workflow `Status` is `In development` while work is active or `Pending development` while queued. Move an unscored issue-and-vehicle package complete enough for the next T-audit to `Development level: Developed proposal` and `Status: Audit needed`. Do not change `Score` or `Runs` merely because drafting or source work occurred. Do not reduce an established development level when revision begins; preserve it and use `Change audit needed` plus the appropriate workflow status until the required targeted review is complete. Apply the exact transition rules in [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md#issue-development-lifecycle) and [`FRAMEWORK.md`](FRAMEWORK.md#issue-development-lifecycle-check).

Apply the [`Human-Governed Foundation and Delegated Development`](FRAMEWORK.md#human-governed-foundation-and-delegated-development) rule before issue development. Once the institutional failure, at least one manifestation, the remedy, and the remedy vehicle are established, the issue moves to `Development level: In development` and agents have broad authority to improve it within that foundation. Ordinarily the human establishes those criteria. Elim during an authorized recurring run and an interactive Codex agent working directly with the user may also determine from the canonical record that all four criteria are substantively present and synchronize the lifecycle classification without a separate confirmation. Other scheduled agents may not infer approval. Reserved foundational or materially consequential departures still require human approval. When uncertain, document the question, skip only the disputed action or issue, request human review, preserve completed work, and continue other eligible batch work. Use the [`Audit-Readiness Assessment`](FRAMEWORK.md#audit-readiness-assessment) to determine whether a proposal should move to `Audit needed` or undergo its next expressly authorized T-audit. A persistent agent must follow its authoritative [`agents/`](agents/) runbook; a runbook may narrow but may not enlarge these rules.

## Persistent-Agent Runbooks

Every persistent named agent or bot has exactly one authoritative runbook registered in [`agents/README.md`](agents/README.md). The runbook records its stable ID and display name, type, enabled status, trigger and schedule, runtime deployment ID, execution environment, model policy when applicable, inputs, work order, read/write boundary, human-reserved actions, branch and pull-request behavior, validation, logging, notifications, retry and stop behavior, and outputs. Secrets and credentials never appear in a runbook. Deployed configuration must match the runbook; detectable drift must fail closed or be reported rather than silently accepted.

Runbooks inherit this file and the Framework instead of repeating general rules. Temporary task agents and one-off delegated subagents do not require individual runbooks unless they become persistent named roles.

## Purpose

Agent work should improve the project carefully, conservatively, and reproducibly. The goal is not maximum speed. The goal is reliable stewardship of the project record and the user's attention.

Agents should prefer focused, evidence-bearing work over broad speculative work. Once the selected audit tier's required question has been responsibly answered, stop rather than adding duplicative research; no audit should be truncated or downgraded merely to conserve tokens, account usage, elapsed time, or subscription resources.

## User-Framing Neutrality Check

Treat a user's candid political judgment as context or an analytical hypothesis, not automatically as project-ready language or an established factual premise. If an instruction appears to rest on partisan preference, collective blame, unsupported motive attribution, a loaded characterization, or a standard that would change under reversed party control, identify the concern before implementing it and propose a neutral formulation, narrower institutional question, stronger evidentiary requirement, or political-failure disposition. Push back when the requested framing would violate the Framework even if the requested substantive outcome is understandable or consistent with the user's stated views.

This check does not require false equivalence. When authoritative evidence establishes material asymmetry, identify the responsible actors, conduct, dates, decisions, and consequences accurately rather than manufacturing equal blame. Distinguish supported descriptions of who sponsored, opposed, blocked, abandoned, implemented, or benefited from an action from claims about collective motive or intent. Attribute motive only when supported by statements, records, findings, or other evidence adequate for that proposition. Apply the same evidentiary, legal, admission, and remedial standards regardless of which party or coalition would benefit from the conclusion.

Do not treat informal language used during discussion as approved reader-facing prose merely because the user used it candidly. Preserve the substance of the concern, explain any neutrality problem, and obtain or reasonably infer approval for the compliant formulation before committing it to the project record.

## Research Proportionality

Agents should use a proportionate and reliable method that fully satisfies the assigned task.

1. Start with local project files before using external searches.
2. Use targeted searches rather than broad repeated queries.
3. Prefer primary sources and already-captured source inventory rows.
4. Reuse verified source records where still current and relevant.
5. Avoid duplicating completed audit work unless a changed rule, changed fact, or explicit user request requires it.
6. Do not run multiple agents on the same files or same unresolved question.
7. Do not continue researching after the audit tier's question has been responsibly answered.
8. If a source path or theory is not producing useful results, document the limitation and move on.
9. If a proposal is blocked by a human-review issue, document the blocker and advance to the next eligible item rather than attempting speculative repair.
10. Commit and push completed units promptly so work is preserved and later agents do not repeat it.

## Context Handoff

Long audits and source-development passes should not depend on chat memory alone. Use [`CURRENT_AUDIT.md`](logs/CURRENT_AUDIT.md) as the durable handoff checkpoint for any audit, drafting pass, source-development task, or batch run that may span many tool calls, user interruptions, or a new chat.

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
7. the relevant `sources.csv` rows;
8. every `sources.csv` source-development record owned by or cross-referenced to the issue, plus any genuinely unrouted `sources-pending.csv` record listing the issue as one plausible destination;
9. any unresolved findings from the latest audit; and
10. whether the issue's parent GitHub issue carries `needs: monitoring`, the current reason for that label, and every associated source marked `Yes` in the catalogs' `Monitoring` field, including whether a validated watcher covers it and whether its accepted `Monitoring Baseline` is present.

Apply the tier-scaled Source Reconciliation rule in the methodology. T0 and T1 may inventory applicable tasks; development and T2-T4 work should resolve applicable tasks through verification, route and remedy-fit review, qualitative reader-facing placement, a documented no-additional-value disposition, or a precise continuing predicate. Update and read back the parent GitHub issue when its `needs: monitoring` state changes. Rebuild the ARRP Project Console whenever candidate data, either canonical source catalog, a source-level `Monitoring` value, an issue-level monitoring label, the presidential-directives registry, watcher configuration, a canonical project log, page-level publication-disposition metadata, or `framework/print-assembly.json` changes. This reconciliation does not create a separate audit run.

A project-wide monitoring pass is a separate non-scoring workflow governed by [`FRAMEWORK.md`](FRAMEWORK.md#project-wide-monitoring-pass). Begin from the GitHub Project Monitoring view, not from the local console. For each labeled proposal or formal candidate, review all associated sources in `sources.csv`, actively search for material new developments, and record the dated result on the existing parent issue. A monitored source does not remain pending once its owner is known. Remove `needs: monitoring` when the issue no longer warrants recurring review. Do not change a proposal's lifecycle status, score, or Runs unless a material result independently requires the ordinary targeted Change Audit and Internal Remedy-Fit review.

When reviewing a presidential-directive discovery batch, accept deterministic metadata and exact-match results only as routing aids. Apply the full political-failure, reversed-party neutrality, durable-harm, duplicate, route-fit, and least-complex-remedy tests before assigning project relevance or disposition. Record the result in `presidential-directives.csv`; route any directive actually used or retained as a lead to one stable source-catalog record; and create a preliminary candidate only for a plausible distinct institutional weakness without an existing owner. The validated watcher may propose only authorized deterministic registry metadata through its dedicated, owner-assigned pull request and must record each material event in the Source Monitor Log. It may not perform the substantive review or disposition.

Before starting substantive audit work, the agent must also check whether the issue has a linked proposed legislation file, constitutional amendment, enabling legislation, rule text, manual text, model act, or other concrete proposal vehicle. If the issue has only a `Pending development` placeholder or otherwise lacks concrete proposal text, stop and notify the user that no proposed legislation or equivalent vehicle exists yet. Ask for confirmation before proceeding, and make clear that the audit will be limited to source development, issue admission, remedy selection, or fixed-zero/candidate review unless the user wants drafting added to the scope. Do not assign a formula-based Proposal Quality Score until a concrete draft exists.

If the issue ID is unclear, ask the user before running the audit.

## Autonomous and Scheduled Execution

Autonomous or scheduled execution is used only when the user expressly authorizes it or enables a persistent agent through its approved runbook and runtime configuration.

The batch objective is to move eligible developed proposals toward T4 readiness while avoiding unsupervised substantive overreach.

### Batch Preflight

Before starting an autonomous batch run, the agent must:

1. confirm the working tree is clean, or stop and report the existing uncommitted files without beginning new audit work;
2. confirm the current branch and remote target are understood;
3. confirm the repository can read the latest local project rules, including this file, [`FRAMEWORK.md`](FRAMEWORK.md), [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md), [`HORIZON_SCAN_LOG.md`](logs/HORIZON_SCAN_LOG.md), and [`AGENT_AUDIT_LOG.md`](logs/AGENT_AUDIT_LOG.md);
4. check the latest relevant audit record before each issue and skip any issue with unresolved human-review blockers unless the user has expressly authorized proceeding; and
5. if the user expressly scheduled the run inside a defined work window, respect that user-defined boundary when selecting the next audit unit.

If the preflight fails, do not begin autonomous edits. Record the reason in [`AGENT_AUDIT_LOG.md`](logs/AGENT_AUDIT_LOG.md) when appropriate and notify the user.

### Eligible Items

For an ordinary audit-only batch, include only developed issues with issue pages and linked proposal vehicles. Exclude retired, merged, candidate, foundation-pending, paused, or awaiting-finding issues unless the user expressly includes them. An expressly authorized recurring development run may also include issues whose canonical metadata records `foundation_status: approved`; those items use `Development level: In development` and are eligible for development, not automatically for a score-bearing audit. Before applying that filter, Elim reconciles admitted, unscored issues whose foundation metadata is absent, pending, or inconsistent: it may set `approved` and advance the lifecycle only after recording why all four criteria are substantively present, or set/retain `pending`, route a genuinely missing choice to `Awaiting decision`, and skip the issue. Mere drafted language, headings, placeholders, or unresolved alternatives are not sufficient.

Process issues in the GitHub Project queue unless the user gives a different queue. Use issue-page metadata and audit-history sidecars as the detailed audit-score and next-audit record.

### Tier Progression

For each issue:

1. read the latest issue page, linked legislation, sibling audit history, GitHub Project item, and relevant source records;
2. determine the next required audit tier;
3. follow the tier-progression strategy authorized by the agent's runbook or the user's instruction, while completing and memorializing every tier separately;
4. stop tier progression for that issue if a material unresolved finding requires human review;
5. update the issue page, audit-history file, GitHub Project fields, and source records;
6. validate the changed files;
7. commit and push the completed issue audit;
8. when the audit changes an eligible proposal's Project `Development level`, `Status`, `Score`, or goal eligibility, manually dispatch the Project Console progress-data workflow after Project readback and push, wait for completion, and verify `project-console-data/progress.json` reflects the new portfolio state; and
9. move to the next eligible issue.

For an expressly authorized batch containing multiple scored audit units, one final progress-data dispatch after the last synchronized Project update and push is sufficient if every unit is already committed and pushed and the data readback confirms the complete batch. The daily schedule is a recovery backstop, not a substitute for audit closeout. Do not edit the generated data branch manually.

Complete the selected tier for one issue before proceeding. If an issue reaches a genuine evidentiary, access, external-review, or human-review blocker, document it, preserve it, and proceed.

If an agent adds or materially changes a source, manifestation, institutional framing, damage theory, weakness theory, remedy language, repair/prevention language, or proposal vehicle for a developed issue without running the targeted Change Audit required by the methodology, the agent must mark the issue as needing a targeted Change Audit and Internal Remedy-Fit Audit before treating the score as fully current. The marker should appear in issue front matter, the visible **Proposal Scoring** or **Next Review** line, the issue audit-history file, and any corresponding GitHub Project field. Reader-facing wording should follow the terminology convention in the methodology while technical records preserve the exact audit terms.

### Permitted Autonomous Corrections

In batch mode, agents may autonomously fix defects that are mechanical, framework-governed, or directly supported by existing project records, including:

1. broken internal links, including stale repository paths embedded in GitHub issue bodies;
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
7. resolving a substantive discrepancy between an issue page and proposed legislation when the correction would change a reserved foundation, materially contract the approved proposal, or make another human-reserved change;
8. clearing a `change_audit_needed` marker without performing the targeted Change Audit and Internal Remedy-Fit Audit required by the methodology;
9. making unsupported claims about real-world events, motives, legal effect, polling, or public support;
10. increasing a score based on judgment rather than documented audit findings; or
11. marking a proposal as proposal-ready, publication-ready, or externally validated without the required record.

When a stop condition appears, record the finding in the issue's audit-history file, update the issue-page audit status, next-audit need, and GitHub Project fields, commit and push if files changed, and move on.

## Multi-Agent Use

Use multiple agents by default when work can be separated into non-overlapping responsibilities and parallel execution is expected to improve speed, coverage, or independent verification. Do not limit delegation because of historical subscription-usage assumptions or impose an arbitrary agent, time, token, or resource cap. Use one agent when the work is inherently sequential, requires repeated judgment over the same files, or would incur more coordination risk than benefit. Examples of suitable parallel work include:

1. one agent checking source sufficiency while another checks GitHub Project/source-inventory consistency;
2. one agent surveying prior legislation while another checks issue-to-legislation alignment; or
3. one agent validating links while another prepares a narrow issue-page cleanup.

Agents should not edit the same file set at the same time unless a coordinator assigns a clear merge responsibility. A coordinating agent remains responsible for reconciling findings, reviewing all edits, resolving conflicts, running final consistency checks, validating the complete worktree, and handling any commit and push.

## Audit Completion and Batch Boundaries

Audit tiers are defined by required depth and output, not by elapsed-time ceilings, token allowances, account-usage limits, or subscription-driven resource budgets. Complete the selected tier before moving to the next issue unless a genuine evidentiary, access, external-review, human-review, or user-defined boundary prevents completion.

For a batch window expressly defined by the user, do not begin a new audit unit that cannot reasonably be completed, validated, committed, pushed, and logged inside the remaining user-defined window. If a unit is already near completion when that window ends, preserve the work and follow the user's stated stopping instruction; absent an express window, no default time boundary applies.

When deciding whether to continue research, ask:

1. Will this likely change the score, remedy, source reliability, or next-audit need?
2. Is there a primary source likely to answer the question reliably?
3. Has the issue already hit a human-review stop condition?
4. Has further research become duplicative, or has the question reached a genuine blocker that should be documented?

If the answer favors stopping, stop.

## Output and Preservation

Each completed issue audit should leave:

1. updated issue-page Proposal Scoring and metadata;
2. a new sibling audit-history entry;
3. updated GitHub Project fields where applicable;
4. updated `sources.csv` for sources used for audit credit;
5. validation notes; and
6. a commit pushed to GitHub; and
7. when the audit changes an eligible proposal's Project `Development level`, `Status`, `Score`, or goal eligibility, a successful Project Console progress-data refresh and readback, or an explicit recorded blocker identifying the failed workflow or stale generated state.

GitHub Project fields are a completion-critical surface for audit work. If the Project row should change but cannot be updated because of authentication, permissions, API, tooling, sandbox, or connector limitations, the agent must notify the user clearly as soon as the failure is known, identify the exact field or row that remains unsynced, and treat the task as blocked or only partially complete until the Project row is updated or the user explicitly accepts a repo-only interim state. Updating the GitHub issue body may be used as a temporary visibility fallback, but it does not replace the required Project-field update.

Project Console progress data is a derived completion surface whenever an audit changes goal-relevant Project development level, score, workflow status, or eligibility. After the authoritative Project row has been updated and read back and the audit commit has been pushed, dispatch the workflow, wait for a successful run, and read back `project-console-data/progress.json`. If dispatch, authentication, workflow execution, publication, or data verification fails, preserve the audit work, identify the stale progress value, record the exact remaining sync step in `CURRENT_AUDIT.md`, and do not describe the console as updated. In a multi-unit batch, one verified final refresh may close the whole batch as provided above.

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
8. confirm the commit hash is recorded in [`AGENT_AUDIT_LOG.md`](logs/AGENT_AUDIT_LOG.md); and
9. if the unit changed goal-relevant Project fields, confirm the Review Ready dashboard workflow completed and the generated page reflects the new state, or record the exact blocker; and
10. confirm no unintended files remain changed for that unit, including generated PDF, DOCX, XLSX, or similar export files unless the user requested an export refresh, the export is the deliverable, export tooling is being tested, or the work is expressly part of a release/publication pass.

If a validation check is skipped, record the skipped check and reason in [`AGENT_AUDIT_LOG.md`](logs/AGENT_AUDIT_LOG.md), in the issue audit history when relevant, or in the final user-facing report. A unit should not be marked complete if validation fails, except when the only failure is an explicitly documented environment or tooling limitation and the work has been preserved for human review.

## Shared Agent Audit Log

All persistent agents and bots use the shared [`AGENT_AUDIT_LOG.md`](logs/AGENT_AUDIT_LOG.md) for material operational provenance and rollback planning. It does not replace issue audit histories, GitHub Project tracking, domain event records, replaceable current reports, `CURRENT_AUDIT.md` handoff checkpoints, or final user-facing reports.

For each material unit, record:

1. date and time with local timezone if available;
2. stable Agent ID, Run ID, and Unit ID where applicable;
3. trigger, task type, outcome, and issue or project task;
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

Completely clean no-change runs remain in bounded Actions or Console history and do not append an entry to the Agent Audit Log. A material detected or routed finding and any repository or external-state change must be logged. When an agent adds, updates, moves, or removes a source record, the same source-changing pull request must append one entry identifying the affected stable source IDs, the action and reason, the destination and proposition or citation supported, the originating run, validation, commit and push status, and rollback reference.

The agent audit log should be append-only. If a commit is later reverted, add a new log entry identifying the revert commit and the original commit it reverses. Do not erase the original log entry.

The canonical prospective entry template is maintained in the log itself. Preserve historical generic labels and schemas; do not retroactively attribute older runs to a newly named agent without reliable evidence.

Agents and bots must never force-push `main`, a protected branch, a human-owned branch, or any shared working branch. A deterministic bot may replace only its own dedicated, disposable report or proposal branch when its authoritative runbook expressly allows that behavior, and it must use `--force-with-lease` so an unexpected intervening change prevents the replacement. Rollback on shared or durable branches should normally occur through a revert commit so GitHub history remains intelligible.

## Conservative Scoring

Agents should not treat repeated audit runs as proof of quality. Scores increase only when the record improves under the methodology: better sources, better legal fit, clearer drafting, stronger implementation analysis, resolved defects, stronger adoption evidence, or documented external review.

Agents and bots may not change a scoring rubric, formula, component, weight, penalty, threshold, or score band without the recorded human approval and project-level Change Audit required by the Framework. They may never change a scoring rule to engineer a desired issue score or portfolio result.

Increment the GitHub Project **Runs** field only for a completed, separately recorded T0, T1, T2, T3, or T4 issue-quality audit. Change Audits, Internal Remedy-Fit Audits, Horizon Scans, source-development or drafting passes, formatting checks, predicate checks, validation reruns, and continuation of the same open tier do not count as separate runs.

When two reasonable auditors could differ, use the lower score and document why.

## No-Hallucination Rule

Agents must not invent support, sources, facts, polling, legislative history, court posture, professional review, or public reaction. If a claim cannot be verified from the project record or a reliable current source, mark it unresolved and award no favorable score credit for it.
