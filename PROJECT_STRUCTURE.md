# Repository Structure

```text
framework/                         Governing methodology and cross-cutting remedial architecture
areas/                             One directory per project area
  a-01-.../
    README.md                      Area concern and issue index
    issues/
      DOJ-001.md                   Developed issue analysis
legislation/                       Proposed statutory language keyed to issue ID
inventory/                         Structured CSV inventories and working method
research/                          Research notes not yet integrated
exports/                           Generated DOCX, PDF, and XLSX outputs
archive/                           Superseded or migrated source snapshots
```

## File ownership

- A defect has one primary issue file.
- Related areas cross-reference the primary file instead of duplicating analysis.
- Legislative drafts use the corresponding issue identifier.
- Source records use the issue identifier in `inventory/sources.csv`.
