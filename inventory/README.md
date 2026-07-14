---
title: "Structured Inventory"
print_levels:
  - full-technical
---

# Structured Inventory

- `sources.csv` — source records associated with issues, areas, or project-level records

GitHub Projects is the authoritative structured tracker for areas, issues, lifecycle status, milestones, roadmap tasks, workstreams, canonical-page links, and horizon-queue status. Issue pages and sibling audit-history files are authoritative for proposal scoring and audit rationale. This directory retains structured CSV records that remain useful as local source and navigation inventories. The human-facing [Subject and Institution Index](../SUBJECT_INDEX.md) is maintained as a separate discovery layer so agency and topic routing do not become workflow metadata.

The GitHub issue registry, [`github_issue_registry.csv`](github_issue_registry.csv), is the repository-side list of all GitHub issues. It preserves stable navigation data for each issue: GitHub number and URL, project object ID where one exists, kind, title, canonical repository record, and native parent issue. Keep it synchronized when an issue is created, renamed, reclassified, assigned a canonical record, or attached to a different parent. It may be used to generate a project table of contents or other navigation surfaces. A closed issue remains in the registry; merged proposal records use `merged proposal` so they remain traceable without being counted as active proposals.

The registry is not the live lifecycle, priority, label, score, audit, or release-blocker tracker. Those values belong in GitHub Project fields and must not be copied into the registry as parallel metadata.

GitHub Project fields summarize audit posture for meta-analysis and should be refreshed whenever an audit changes issue score, status band, run count, last audit type and date, next audit need, issue link, area, priority, rebaseline status, change-audit need, or release posture. Detailed audit fields remain in issue pages and issue audit histories.

The Change Audit history is [`../framework/CHANGE_AUDIT_LOG.md`](../framework/CHANGE_AUDIT_LOG.md). It records project-wide rubric, template, scoring, and structural-consistency changes separately from GitHub Project workflow fields.

The Agent Audit Log is [`../framework/AGENT_AUDIT_LOG.md`](../framework/AGENT_AUDIT_LOG.md). It records autonomous, batched, or scheduled agent commits, validation, blockers, and rollback references separately from GitHub Project workflow fields. It is not used for ordinary human-invoked audits.

Project methodology, audit rules, scoring rules, and GitHub Project update rules are maintained in [`../framework/METHODOLOGY.md`](../framework/METHODOLOGY.md).

The Horizon Scan Log is [`../framework/HORIZON_SCAN_LOG.md`](../framework/HORIZON_SCAN_LOG.md). It preserves adjudicated `HOR-###` disposition history separately from the active GitHub horizon queue.

## Project Tracking Scope

Area and issue tracking now lives in the [ARRP GitHub Project](https://github.com/users/Thorncrag/projects/2). Substantive issue titles, descriptions, institutional-anomaly analysis, manifestations, remedies, source notes, and drafting annotations live in the relevant issue files and area README files. This avoids duplication between GitHub Project metadata and the substantive issue records.

## Audit Tracking Scope

The proposal-quality score is a provisional planning value, not a claim that the issue is publication-ready or externally validated. The GitHub Project **Runs** field counts only completed, separately recorded T0–T4 issue-quality audits; Change Audits, source-development and drafting passes, formatting checks, predicate checks, and validation reruns do not increment it. Audit runs may support a higher score only when the audit resolves findings, broadens review, verifies sources, improves legal fit, improves drafting, or strengthens adoption prospects.

GitHub Project fields are the compact reader-facing tracker for cross-issue audit status and release triage. They should not replace issue-page Proposal Scoring summaries, sibling audit-history sidecars, or separate Change/Horizon/Agent logs.

`CHANGE_AUDIT_LOG.md` is the cumulative reader-facing tracker for Change Audit history. It should not replace issue-page audit histories or GitHub Project status fields.

`HORIZON_SCAN_LOG.md` is the cumulative reader-facing log for Horizon Scan findings and integration decisions. It should not replace issue-page source development, audit histories, GitHub Project tracking, or retained source records once a horizon item is admitted, merged, or retired.

## Source Inventory Scope

`sources.csv` is a master list of distinct external source URLs already cited in the project. It records associated project records, source type, publisher, title or citation label, source URL, and the project location where the source appears.

The current source inventory is a capture pass, not a completed verification pass. Rows marked `Reviewed?` as `No` should be checked against the cited proposition before publication, legislative outreach, or final compiled-document release.
