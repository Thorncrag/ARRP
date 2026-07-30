---
title: "ARRP Audit Execution and Closeout"
status: active
authority_scope: "Exact ARRP audit preflight, source and monitoring reconciliation, specialized discovery review, tier progression, Change Audit markers, validation, Console refresh, and readback."
load_when: "Beginning, selecting, advancing, batching, resuming, validating, or closing an ARRP T-audit; running a project-wide monitoring pass; or substantively reviewing a presidential-directive discovery batch."
dependencies:
  - "../../standards/automation/audit-execution.md"
  - "../../standards/automation/validation-and-closeout.md"
  - "../../standards/audits/levels.md"
  - "../../standards/audits/change-audits.md"
  - "../../standards/sources/source-records.md"
  - "../../standards/sources/monitoring.md"
  - "../automation/agent-policy.md"
  - "../github/workflow.md"
  - "navigation-sync.md"
  - "source-adjudication.md"
  - "../interfaces/project-console.md"
  - "../interfaces/project-console-progress.md"
print_status: excluded
print_exclusion_reason: "Internal project workflow."
---

# ARRP Audit Execution and Closeout

This module implements the reusable
[`audit-execution.md`](../../standards/automation/audit-execution.md) and
[`validation-and-closeout.md`](../../standards/automation/validation-and-closeout.md)
standards for ARRP. The substantive audit method remains in
[`levels.md`](../../standards/audits/levels.md); exact GitHub field and
monitoring meanings remain in [`workflow.md`](../github/workflow.md).

## ARRP Audit Preflight

ARRP issue-quality audits are single-issue workflows unless the user expressly
requests batch mode or a project-wide Change Audit. Before a T-audit, identify:

1. the issue ID;
2. the requested tier or the next tier shown by the GitHub Project fields or
   issue page;
3. `areas/<AREA>/issues/<ISSUE>.md`;
4. every linked `legislation/<ISSUE>*.md` vehicle;
5. the sibling `areas/<AREA>/issues/<ISSUE>.audit.md` history;
6. the authoritative GitHub Project item;
7. every relevant `inventory/sources.csv` row;
8. every source-development record owned by or cross-referenced to the issue,
   plus any genuinely unrouted `inventory/sources-pending.csv` row listing the
   issue as a plausible destination;
9. unresolved findings from the latest audit; and
10. the parent GitHub issue's `needs: monitoring` posture, required monitoring
    explanation, every associated source whose `Monitoring` value is `Yes`,
    its accepted `Monitoring Baseline`, and any validated watcher covering it.

Apply the concrete-vehicle preflight in
[`levels.md`](../../standards/audits/levels.md#audit-depth-tiers). Honor its
notice and confirmation boundary; do not assign a formula-based Proposal
Quality Score before the required concrete draft exists. Ask the user if the
issue ID is unclear.

## Source, Monitoring, and Console Surfaces

Apply the tier-scaled Source Reconciliation rule. T0 and T1 may inventory
applicable work; development and T2-T4 work resolve it through verification,
route and remedy-fit review, qualitative reader-facing placement, a documented
no-additional-value disposition, or a precise continuing predicate. When
`needs: monitoring` changes, update and read back the parent GitHub issue under
[`workflow.md`](../github/workflow.md#issue-specific-monitoring). Do not use a
workflow Status as a substitute for source or issue monitoring.

Use the exact source catalogs, fields, paths, and reconciliation rules in
[ARRP Source Catalog and Adjudication](source-adjudication.md). Apply the
[Project Console source-projection refresh](../interfaces/project-console.md#source-projection-refresh)
whenever one of its canonical inputs changes. Source and Console
reconciliation does not create another audit run.

A project-wide monitoring pass is separate and non-scoring. Begin from the
ARRP GitHub Project **Monitoring** view, not the local Console. Follow the exact
parent-wrapper, source coverage, dated-result, label, hold, and readback rules
in [`workflow.md`](../github/workflow.md#issue-specific-monitoring). Monitoring
does not change `Development level`, ordinary `Status`, `Score`, or `Runs`
merely because an external matter remains open. Use the workflow's exact
`Blocked`, `Deferred`, and `Human decision needed` distinctions rather than
redefining them here.

## Named Bot and Directive Review

The [Case Monitor Bot](../automation/runbooks/case-monitor-bot.md) may place
only the marker-bounded, unreviewed leads authorized by its runbook. Treat
those leads as routing signals, not source-catalog admissions, verified
manifestations, legal conclusions, or dispositions. Elim or an interactive
agent performs source verification, qualitative placement, analysis, and
authorized routing.

For a presidential-directive discovery batch, treat deterministic metadata and
exact-match results from the
[Presidential Directives Bot](../automation/runbooks/presidential-directives-bot.md)
only as routing aids. Apply the Issue-Admission Test, Political-Failure
Boundary, duplicate and route-fit checks, and least-complex-remedy rule;
prepare neutral alternative-control analysis; and apply only a previously
recorded human reversed-control answer. Route a materially missing answer
through the [ARRP Human-Decision Route](../automation/agent-policy.md#arrp-human-decision-route).

Record the substantive review in `inventory/presidential-directives.csv`.
Route a directive actually used or retained as a lead to one stable
source-catalog record. Create a preliminary candidate only for a plausible
distinct institutional weakness without an existing owner. The deterministic
watcher may propose only the registry metadata authorized by its runbook,
verify only whether a required human answer exists, and record its material
event in `framework/logs/sources/source-monitor-log.md`; it may not perform
the substantive review or disposition.

## ARRP Tier Progression

For each issue:

1. read the current issue page, linked vehicles, sibling audit history, GitHub
   Project item, and relevant source records;
2. determine the next required tier;
3. follow the user's instruction or applicable runbook while memorializing
   every completed tier separately;
4. stop progression for that issue when a material unresolved finding requires
   human review;
5. update the issue page, audit history, GitHub Project fields, and source
   records;
6. run issue-specific and complete changed-surface validation;
7. commit and push the completed audit through the reviewed GitHub boundary;
8. when the audit changes an eligible proposal's `Development level`, `Status`,
   `Score`, or goal eligibility, run the local Project Console Progress stage
   after Project readback and push, wait for success, and verify its checked-in
   Console projection; and
9. only then move to the next eligible issue.

For an expressly authorized multi-unit scored batch, one final progress-data
refresh after the last synchronized Project update and push is sufficient
when every unit is committed and pushed and readback confirms the complete
batch. The nightly schedule is a recovery backstop, not audit closeout.

## Change Audit Markers

When an agent materially changes a developed issue's source basis,
manifestation, institutional framing, damage or weakness theory, remedy,
repair/prevention language, or proposal vehicle without the targeted Change
Audit and Internal Remedy-Fit Audit required by
[`change-audits.md`](../../standards/audits/change-audits.md), do not treat the
score as fully current.

Set the exact `change_audit_needed` or corresponding current marker in issue
front matter, the visible **Proposal Scoring** or **Next Review** line, the
issue audit-history file, and the corresponding GitHub Project field. Clear it
only after the targeted review and complete synchronization required by the
Change Audit standard.

## ARRP Validation and Closeout

Each completed issue audit leaves:

1. synchronized issue-page Proposal Scoring and metadata;
2. a new sibling audit-history entry;
3. updated GitHub Project fields where applicable;
4. updated `inventory/sources.csv` rows for sources used for audit credit;
5. validation notes;
6. a commit pushed through the reviewed GitHub boundary; and
7. when goal-relevant Project fields changed, a successful Project Console
   progress-data refresh and readback, or an explicit blocker identifying the
   stale value and failed step.

After each autonomous unit, validate:

1. Markdown structure and local links;
2. agreement between issue front matter and visible **Proposal Scoring**;
3. the new sibling audit-history entry;
4. agreement among the issue page, audit history, and GitHub Project row;
5. for T1 or routing changes, the exact ARRP navigation bundle under
   [`navigation-sync.md`](navigation-sync.md);
6. parsing and inclusion of every credited source under
   [ARRP Source Catalog and Adjudication](source-adjudication.md);
7. whitespace and formatting;
8. the required commit hash in the owner-local Agent Audit Log;
9. the Review Ready local progress stage and generated readback when
   goal-relevant fields changed; and
10. absence of unintended changed files, including generated exports unless
    the user requested or the task expressly requires them.

If the Project row should change but cannot be updated, notify the user
immediately, identify the issue and exact unsynchronized fields, preserve the
repository work, and treat the unit as partial until the row is synchronized
or the user expressly accepts a repository-only interim state. An issue-body
snapshot is temporary visibility, not a substitute.

If Console dispatch or readback fails, preserve the audit, identify the stale
progress value, record the remaining step in
[`current-task.md`](../../records/handoffs/current-task.md), and do not describe
the Console as current. If validation, commit, or push fails, preserve the
work, record the failed step and changed files, stop the batch, and do not
begin another issue until repository state or access is resolved.
