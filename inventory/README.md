---
title: "Structured Inventory"
print_levels:
  - full-technical
---

# Structured Inventory

- `sources.csv` — source records associated with issues, areas, or project-level records

GitHub Projects is the authoritative structured tracker for areas, issues, lifecycle status, milestones, roadmap tasks, workstreams, canonical-page links, and horizon-queue status. Issue pages and sibling audit-history files are authoritative for proposal scoring and audit rationale. This directory retains only the structured CSV records that are still useful as local source inventories.

The historical GitHub import ledger, [`github_issue_import.csv`](github_issue_import.csv), is retained only to preserve migration provenance. Columns prefixed with `Legacy` preserve the values used during the original import and should not be treated as current workflow metadata. It is not the live area, issue, priority, status, label, or release-blocker tracker. Current values belong in GitHub Project fields.

The project-wide human-readable audit tracker is [`../framework/AUDIT_DASHBOARD.md`](../framework/AUDIT_DASHBOARD.md). It summarizes audit posture for meta-analysis and should be refreshed whenever an audit changes issue score, status band, run count, last audit type and date, next audit need, issue link, area, priority, or snapshot counts. Detailed audit fields remain in issue pages and issue audit histories.

The Change Audit history is [`../framework/CHANGE_AUDIT_LOG.md`](../framework/CHANGE_AUDIT_LOG.md). It records project-wide rubric, template, scoring, and structural-consistency changes separately from the compact dashboard.

The Agent Audit Log is [`../framework/AGENT_AUDIT_LOG.md`](../framework/AGENT_AUDIT_LOG.md). It records autonomous-agent commits, validation, blockers, and rollback references separately from the compact dashboard.

Project methodology, audit rules, scoring rules, and dashboard update rules are maintained in [`../framework/METHODOLOGY.md`](../framework/METHODOLOGY.md).

The Horizon Scan Log is [`../framework/HORIZON_SCAN_LOG.md`](../framework/HORIZON_SCAN_LOG.md). It preserves adjudicated `HOR-###` disposition history separately from the audit-score dashboard and the active GitHub horizon queue.

## Project Tracking Scope

Area and issue tracking now lives in the [ARRP GitHub Project](https://github.com/users/Thorncrag/projects/2). Substantive issue titles, descriptions, institutional-anomaly analysis, manifestations, remedies, source notes, and drafting annotations live in the relevant issue files and area README files. This avoids duplication between GitHub Project metadata and the substantive issue records.

## Audit Tracking Scope

The proposal-quality score is a provisional planning value, not a claim that the issue is publication-ready or externally validated. Audit runs may support a higher score only when the audit resolves findings, broadens review, verifies sources, improves legal fit, improves drafting, or strengthens adoption prospects.

`AUDIT_DASHBOARD.md` is the compact reader-facing dashboard for cross-issue audit status. It should contain only the snapshot counts, Quick Jump links, and compact issue audit index. It should not replace issue-page Proposal Scoring summaries, sibling audit-history sidecars, GitHub Project tracking, or separate Change/Horizon/Agent logs.

`CHANGE_AUDIT_LOG.md` is the cumulative reader-facing tracker for Change Audit history. It should not replace issue-page audit histories, GitHub Project status fields, or dashboard score/status summaries.

`HORIZON_SCAN_LOG.md` is the cumulative reader-facing log for Horizon Scan findings and integration decisions. It should not replace issue-page source development, audit histories, GitHub Project tracking, or retained source records once a horizon item is admitted, merged, or retired.

## Source Inventory Scope

`sources.csv` is a master list of distinct external source URLs already cited in the project. It records associated project records, source type, publisher, title or citation label, source URL, and the project location where the source appears.

The current source inventory is a capture pass, not a completed verification pass. Rows marked `Reviewed?` as `No` should be checked against the cited proposition before publication, legislative outreach, or final compiled-document release.
