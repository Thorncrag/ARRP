---
title: "Issue and Project-Wide Monitoring"
status: active
authority_scope: "The distinction between monitoring and workflow holds, parent-issue monitoring records, and the project-wide non-scoring monitoring pass."
load_when: "Applying, reviewing, or removing issue-level monitoring; checking monitored issues; responding to a watched external development; or deciding whether an external dependency is monitoring, deferral, or blockage."
dependencies: "../FRAMEWORK.md; source-catalogs.md; ../evidence/evidence-records.md; ../GITHUB_WORKFLOW.md; ../agents/CASE_MONITOR_BOT.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Issue and Project-Wide Monitoring

## Authority and Dependencies

This file is the authoritative detailed rule for issue-level monitoring and the project-wide monitoring pass. Source-level monitoring metadata belongs to [`source-catalogs.md`](source-catalogs.md), evidence placement to [`../evidence/evidence-records.md`](../evidence/evidence-records.md), exact workflow Status and hold mechanics to [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md), and deterministic case-watcher behavior to [`../agents/CASE_MONITOR_BOT.md`](../agents/CASE_MONITOR_BOT.md).

## Load When

Load this file when applying, reviewing, or removing issue-level monitoring; conducting a project-wide monitoring pass; responding to a detected external development; or deciding whether an external matter is merely being watched, is an affirmative project deferral, or is an indispensable blocker.

## Parent-Issue Monitoring

Apply `needs: monitoring` to an existing proposal or formal-candidate issue when an external development is being watched, it is materially relevant to the issue's future development, and useful issue work may continue because the underlying issue remains regardless of the external outcome. Preserve the issue's ordinary lifecycle status and do not create a monitoring-only sub-issue. The parent wrapper must identify the watched matter, its material relevance, the reassessment trigger, and the checking method. The parent issue owns the monitoring work, and each pass checks all associated sources plus material new developments. A monitored matter with several implications receives one primary analytic home and any number of affected-issue associations; do not duplicate the case history or its source record.

Monitoring is independent of workflow status. If useful work may continue while the external matter is watched, retain the ordinary status plus `needs: monitoring`. If intended work cannot proceed without the external event because it is a concrete indispensable prerequisite, apply the Blocked rule in [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md) instead. If work could proceed but the project has affirmatively chosen not to continue, apply the Deferred rule there. A missing human-reserved choice is a human decision, not monitoring or blockage.

## Project-Wide Monitoring Pass

A **project-wide monitoring pass** is a non-scoring review of every open proposal or formal candidate carrying `needs: monitoring`. It is distinct from a T-audit and does not alter proposal scores, development level, workflow status, or audit-run counts merely because an external matter remains open. Monitoring presumes that useful issue work can continue.

For each labeled issue, review every associated source in `sources.csv`, including sources whose `Monitoring` value is `No`, and actively search for material new developments that the catalog may not yet contain. Refresh changing source or docket posture, record a concise dated result on the parent GitHub issue, update source and reader-facing evidence placement as needed, and remove `needs: monitoring` only when no continuing review need remains. If a result materially changes an issue's manifestations, diagnosis, remedy, legislative vehicle, or score basis, run the ordinary targeted Change Audit and Internal Remedy-Fit review before treating the proposal as current. If a new source's ownership is genuinely unclear, it may enter `sources-pending.csv` until routed; monitoring itself is not a pending disposition.

GitHub Issues and the Project Monitoring view are the issue-level monitoring-workflow authority. The Console is a nonauthoritative projection governed by [`../PROJECT_CONSOLE_PROGRESS.md`](../PROJECT_CONSOLE_PROGRESS.md). Routine issue monitoring is not itself a human Action Item merely because `needs: monitoring` remains present. Only a detected development, exception, or resulting decision that requires human attention enters Action Items.

The scheduled `case-monitor-bot` may assist without replacing the project-wide pass. Its exact deterministic coverage, write boundary, validation, and failure behavior are governed by [`../agents/CASE_MONITOR_BOT.md`](../agents/CASE_MONITOR_BOT.md). Its observations are routing signals, not legal significance, route-fit, disposition, or issue-development decisions.

Source volume may establish recurrence, breadth, cross-agency use, or persistence, but a raw record count is not itself evidence of legality, severity, motive, or institutional failure. Evidence records should distinguish verified distinct episodes, primary governmental or judicial records, official findings, final adjudications, open matters, corroborating source records, and internal unverified leads. State both episode and source-record counts when volume is material; do not imply that multiple reports concerning one event are separate manifestations.
