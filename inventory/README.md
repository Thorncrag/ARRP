# Structured Inventory

- `areas.csv` — top-level project areas
- `issues.csv` — compact issue-tracking index keyed to issue identifier
- `contents.csv` — combined area-and-issue navigation index suitable for table-of-contents development
- `audits.csv` — issue-level audit status and proposal-quality scoring
- `sources.csv` — source records associated with issues, areas, or project-level records
- `METHOD.md` — inventory and drafting rules

The CSV files are canonical structured records. Spreadsheet editions may be generated for convenience.

The project-wide human-readable audit tracker is [`../AUDIT_DASHBOARD.md`](../AUDIT_DASHBOARD.md). It summarizes audit posture for meta-analysis and should be refreshed whenever an audit changes issue score, audit status, last audit type, next audit need, issue link, legislation link, or development status.

## Issue Inventory Scope

`issues.csv` is intentionally a compact tracking index. It records only the issue identifier, area identifier, priority, and development status.

Substantive issue titles, descriptions, institutional-anomaly analysis, manifestations, remedies, source notes, and drafting annotations live in the relevant issue files and area README files. This avoids duplication between the master inventory and the substantive issue records.

## Combined Contents Index

`contents.csv` combines area rows and issue rows in document order. It exists so the inventory can also function as a future table-of-contents scaffold without collapsing the normalized working files.

Area and issue rows include relative links to the area page, issue page, and proposed legislation where available. Candidate or retired issues without standalone pages link to the nearest area page that contains the inventory entry.

## Audit Inventory Scope

`audits.csv` assigns every issue a current proposal-quality score, audit run count, audit status, score basis, and next audit need.

The proposal-quality score is a provisional planning value, not a claim that the issue is publication-ready or externally validated. Audit runs may support a higher score only when the audit resolves findings, broadens review, verifies sources, improves legal fit, improves drafting, or strengthens adoption prospects.

`AUDIT_DASHBOARD.md` is the compact reader-facing dashboard for cross-issue audit status. It should not replace issue-page audit records or the structured audit inventory.

## Source Inventory Scope

`sources.csv` is a master list of distinct external source URLs already cited in the project. It records associated project records, source type, publisher, title or citation label, source URL, and the project location where the source appears.

The current source inventory is a capture pass, not a completed verification pass. Rows marked `Reviewed?` as `No` should be checked against the cited proposition before publication, legislative outreach, or final compiled-document release.
