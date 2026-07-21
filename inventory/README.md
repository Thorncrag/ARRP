---
title: "Structured Inventory"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Structured Inventory

This directory holds the local structured records that support source tracking and stable GitHub navigation; it is not a second workflow or proposal record.

- [`sources.csv`](sources.csv) is the relied-upon source registry for external sources affirmatively used to support an assertion in a project-authored substantive record, whether reader-facing prose or an accountable research, GitHub monitoring, evidence, or candidate record.
- [`sources-pending.csv`](sources-pending.csv) is a temporary routing queue limited to retained sources whose accountable issue, candidate, or research destination is genuinely unclear. Verification, monitoring, an open external matter, or an undeveloped destination does not justify pending placement once an owner is known; cite the source provisionally in that owner's source-development record, move it to `sources.csv`, and state unfinished review through `Reviewed?`, Notes, or the monitoring fields.
- [`presidential-directives.csv`](presidential-directives.csv) is the durable discovery, deduplication, change-detection, and screening registry for publicly released presidential instruments from January 20, 2017 forward. The initial three-administration corpus has already been screened; later watcher results identify only new or changed records requiring another pass. It is not a source catalog: any directive relied upon or retained as a source-development lead must also have one stable record in `sources.csv` or `sources-pending.csv`, cross-referenced by Source ID.
- [`github_issue_registry.csv`](github_issue_registry.csv) preserves stable GitHub issue navigation: number, URL, Project object ID where available, kind, title, canonical repository record, and parent relationship.

Both source catalogs use `Monitoring` to identify changing records. A monitored source must also carry a concise `Monitoring Rationale` explaining the development being watched and a `Monitoring Group` that joins records concerning the same matter. `Monitoring Baseline` contains the accepted fingerprint only when a validated deterministic watcher covers that source; it remains blank otherwise. Material watcher changes are proposed through a dedicated pull request and recorded in [`../framework/logs/SOURCE_MONITOR_LOG.md`](../framework/logs/SOURCE_MONITOR_LOG.md); merging the pull request accepts the new baseline. No-change checks remain in GitHub Actions. Those source-level fields do not replace `needs: monitoring` on a proposal or formal-candidate GitHub issue, which triggers review of the whole issue and an active search for additional developments.

The [ARRP GitHub Project](https://github.com/users/Thorncrag/projects/2) is authoritative for active lifecycle, priority, audit posture, and horizon workflow. Canonical issue pages and sibling audit histories own substantive analysis, scoring rationale, and detailed review history. The [Subject and Institution Index](../SUBJECT_INDEX.md) remains the reader-facing discovery layer.

For maintenance and synchronization rules, see [`../framework/METHODOLOGY.md`](../framework/METHODOLOGY.md) and [`../framework/GITHUB_WORKFLOW.md`](../framework/GITHUB_WORKFLOW.md). Historical cross-project records are in [`../framework/logs/`](../framework/logs/).
