---
title: "Repository Structure"
print_levels:
  - full-technical
---

# Repository Structure

```text
framework/                         Governing methodology, remedy taxonomy, and print assembly rules
areas/                             One directory per project area
  DOJ/                             Folder name matches the issue identifier prefix
    README.md                      Area concern and issue index
    issues/
      DOJ-001.md                   Developed issue analysis
legislation/                       Proposed statutory language keyed to issue ID
inventory/                         Structured CSV inventories
AUDIT_DASHBOARD.md                 Compact audit snapshot and issue audit index
CHANGE_AUDIT_LOG.md                Cumulative project-wide Change Audit history
HORIZON_SCAN.md                    Cumulative horizon-scan intake and integration ledger
AGENT_AUDIT_LOG.md                 Autonomous-agent provenance, commits, and rollback references
research/                          Research notes not yet integrated
exports/                           Generated DOCX, PDF, and XLSX outputs
archive/                           Superseded or migrated source snapshots
```

## File ownership

- A defect has one primary issue file.
- Related areas cross-reference the primary file instead of duplicating analysis.
- Legislative drafts use the corresponding issue identifier.
- `inventory/contents.csv` combines area and issue rows for navigation and future table-of-contents planning.
- Source records in `inventory/sources.csv` may be associated with issues, areas, framework files, research files, or project-level pages.
- Inventory CSVs should be updated in the same change that adds, removes, renames, merges, retires, or materially revises an area, issue, legislative proposal, or cited source.
- `AUDIT_DASHBOARD.md` is compact and should not duplicate detailed scoring, Horizon Scan, Change Audit, or Agent Audit Log content.
- Audit rules and scoring live in `framework/METHODOLOGY.md`; print assembly rules live in `framework/PRINT_ASSEMBLY.md`; remedy categories and trigger stages live in `framework/REMEDY_FRAMEWORK.md`.
