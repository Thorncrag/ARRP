---
title: "Agent Rules — Audit Execution"
dependencies: "../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Agent Rules — Audit Execution

Load this module before beginning, selecting, advancing, batching, or resuming a T-audit or another issue-quality audit unit; before a project-wide monitoring pass; and before substantive review of a presidential-directive discovery batch. Load the substantive audit, monitoring, source, or candidate modules routed through [`FRAMEWORK.md`](../FRAMEWORK.md) in addition to this operational module.

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
10. whether the issue's parent GitHub issue carries `needs: monitoring`, whether its wrapper states the watched external matter, material relevance, reassessment trigger, and checking method, and every associated source marked `Yes` in the catalogs' `Monitoring` field, including whether a validated watcher covers it and whether its accepted `Monitoring Baseline` is present.

Apply the tier-scaled Source Reconciliation rule in the methodology. T0 and T1 may inventory applicable tasks; development and T2-T4 work should resolve applicable tasks through verification, route and remedy-fit review, qualitative reader-facing placement, a documented no-additional-value disposition, or a precise continuing predicate. Update and read back the parent GitHub issue when its `needs: monitoring` state changes. Rebuild the ARRP Project Console whenever candidate data, either canonical source catalog, a source-level `Monitoring` value, an issue-level monitoring label, the presidential-directives registry, watcher configuration, a canonical project log, page-level publication-disposition metadata, or `framework/print-assembly.json` changes. This reconciliation does not create a separate audit run.

A project-wide monitoring pass is a separate non-scoring workflow governed by [`FRAMEWORK.md`](../FRAMEWORK.md#project-wide-monitoring-pass). Begin from the GitHub Project Monitoring view, not from the local console. For each labeled proposal or formal candidate, confirm that the parent wrapper identifies the watched external matter, its material relevance to future issue development, the reassessment trigger, and the checking method; review all associated sources in `sources.csv`; actively search for material new developments; and record the dated result on the existing parent issue. A monitored source does not remain pending once its owner is known. Remove `needs: monitoring` when the issue no longer warrants recurring review. Monitoring does not change the ordinary Status, score, or Runs merely because the external matter remains open. Use `Blocked` only if intended work cannot proceed without a concrete indispensable prerequisite, `Deferred` only when the project affirmatively postpones work that could proceed, and `Human decision needed` for a human-reserved choice.

A deterministic monitoring bot may place configured high-recall leads in a marker-bounded section of an existing issue or candidate source-development record when its runbook and configuration expressly authorize that target. Such a lead is an observed routing signal, not a source-catalog admission, verified manifestation, legal conclusion, issue disposition, or substitute for agent review. The bot must label every entry as unreviewed, preserve stable identity and provenance, write only through its reviewed proposal branch, and leave source verification, qualitative placement, analysis, and disposition to Elim, an interactive agent, and the human author as their respective authority allows.

When reviewing a presidential-directive discovery batch, accept deterministic metadata and exact-match results only as routing aids. Apply the canonical Issue-Admission Test, the Political-Failure Boundary, duplicate and route-fit checks, and the least-complex-remedy rule; prepare neutral alternative-control analysis; and apply only an already recorded human reversed-control answer before assigning project relevance or recommending a disposition. If that answer is material and missing, route the exact question through `Human decision needed`. Record the result in `presidential-directives.csv`; route any directive actually used or retained as a lead to one stable source-catalog record; and create a preliminary candidate only for a plausible distinct institutional weakness without an existing owner. The validated watcher may propose only authorized deterministic registry metadata through its dedicated, owner-assigned pull request, may verify only whether any required human answer exists, and must record each material event in the Source Monitor Log. It may not perform the substantive review or disposition.

Before starting substantive audit work, apply the concrete-vehicle preflight in [`../audits/TIERED_AUDITS.md`](../audits/TIERED_AUDITS.md#audit-depth-tiers). The agent must honor its notice and confirmation boundary and may not assign a formula-based Proposal Quality Score until the required concrete draft exists.

If the issue ID is unclear, ask the user before running the audit.

## Tier Progression

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

## Audit Completion and Batch Boundaries

Audit tiers are defined by required depth and output, not by elapsed-time ceilings, token allowances, account-usage limits, or subscription-driven resource budgets. Complete the selected tier before moving to the next issue unless a genuine evidentiary, access, external-review, human-review, or user-defined boundary prevents completion.

For a batch window expressly defined by the user, do not begin a new audit unit that cannot reasonably be completed, validated, committed, pushed, and logged inside the remaining user-defined window. If a unit is already near completion when that window ends, preserve the work and follow the user's stated stopping instruction; absent an express window, no default time boundary applies.

When deciding whether to continue research, ask:

1. Will this likely change the score, remedy, source reliability, or next-audit need?
2. Is there a primary source likely to answer the question reliably?
3. Has the issue already hit a human-review stop condition?
4. Has further research become duplicative, or has the question reached a genuine blocker that should be documented?

If the answer favors stopping, stop.
