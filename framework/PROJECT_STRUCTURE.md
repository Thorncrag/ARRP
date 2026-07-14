---
title: "Repository Structure"
print_levels:
  - full-technical
---

# Repository Structure

```text
SUBJECT_INDEX.md                   Cross-area subject and institutional-body lookup
framework/                         Governing methodology, tracking logs, and operating rules
  FRAMEWORK.md                     Project framework and file-ownership rules
  METHODOLOGY.md                   Audit rules, scoring rules, and workflow rules
  REMEDY_FRAMEWORK.md              Remedy taxonomy and trigger stages
  PRINT_ASSEMBLY.md                Print/export assembly rules
  GITHUB_WORKFLOW.md               GitHub Issues/Projects workflow rules
  AGENT_OPERATING_RULES.md         Agent-assisted audit and batch-audit rules
  CURRENT_AUDIT.md                 Current long-running audit handoff checkpoint
  CHANGE_AUDIT_LOG.md              Cumulative project-wide Change Audit history
  HORIZON_SCAN_LOG.md              Cumulative horizon-scan disposition and integration log
  AGENT_AUDIT_LOG.md               Autonomous-agent provenance, commits, and rollback references
  INTERBRANCH_REVIEW_FRAMEWORK.md
                                   Governing JUD-011 coverage and proposal-independence convention
  INTERBRANCH_REVIEW_COVERAGE_MATRIX.md
                                   Proposal inclusion, exclusion, and future-screening record
  PROJECT_STRUCTURE.md             Repository map and file ownership summary
areas/                             One directory per project area
  DOJ/                             Folder name matches the issue identifier prefix
    README.md                      Area concern and issue index
    issues/
      DOJ-001.md                   Developed issue analysis
legislation/                       Proposed statutory language keyed to issue ID
inventory/                         Structured source and GitHub issue registries
research/                          Research notes not yet integrated
exports/                           Generated DOCX, PDF, and XLSX outputs
archive/                           Superseded or migrated source snapshots
```

## File ownership

- A defect has one primary issue file.
- `SUBJECT_INDEX.md` maps organizations, subjects, acronyms, and aliases in one alphabetical sequence to concise linked record identifiers, with the preferred route first, without changing issue ownership.
- Related areas cross-reference the primary file instead of duplicating analysis.
- Legislative drafts use the corresponding issue identifier.
- GitHub Projects is the authoritative area, issue, status, milestone, roadmap, and horizon-queue tracker.
- Source records in `inventory/sources.csv` may be associated with issues, areas, framework files, research files, or project-level pages.
- GitHub Project items/fields, retained source inventory, audit-history sidecars, and affected Markdown pages should be updated in the same change that adds, removes, renames, merges, retires, or materially revises an area, issue, legislative proposal, audit status, or cited source.
- GitHub Project fields provide the compact cross-issue workflow, audit-status, and release-triage view.
- `framework/CURRENT_AUDIT.md` is the active handoff checkpoint for long audits and should be read before resuming vague follow-up instructions.
- Audit rules and scoring live in `METHODOLOGY.md`; print assembly rules live in `PRINT_ASSEMBLY.md`; remedy categories and trigger stages live in `REMEDY_FRAMEWORK.md`.
