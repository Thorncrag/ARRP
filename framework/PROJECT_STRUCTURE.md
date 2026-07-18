---
title: "Repository Structure"
print_levels:
  - full-technical
---

# Repository Structure

```text
README.md                          Public project front door, scope, and reader navigation
SUBJECT_INDEX.md                   Cross-area subject and institutional-body lookup
AGENTS.md                          Repository-local operating instructions for Codex
AUTHORS.md                         Authorship and stewardship information
CONTRIBUTING.md                    Contribution and review expectations
LICENSE.md                         Rights and reuse terms
CITATION.cff                       Citation metadata
.github/                           GitHub automation, issue templates, and dashboard configuration
mkdocs.yml                         Public-site presentation and search configuration
requirements-pages.txt             Pinned public-site build dependencies
framework/                         Governing methodology, historical records, and operating rules
  FRAMEWORK.md                     Project framework and file-ownership rules
  METHODOLOGY.md                   Audit rules, scoring rules, and workflow rules
  REMEDY_FRAMEWORK.md              Remedy taxonomy and trigger stages
  PRINT_ASSEMBLY.md                Print/export assembly rules
  GITHUB_WORKFLOW.md               GitHub Issues/Projects workflow rules
  AGENT_OPERATING_RULES.md         Agent-assisted audit and batch-audit rules
  CURRENT_AUDIT.md                 Current long-running audit handoff checkpoint
  HORIZON_SCAN_LOG.md              Cumulative horizon-scan disposition and integration log
  AGENT_AUDIT_LOG.md               Autonomous-agent provenance, commits, and rollback references
  CHANGE_AUDIT_LOG.md              Read-only historical project-wide Change Audit record
  PROJECT_CONSISTENCY_AUDIT.md     Read-only historical July 2026 consistency-audit record
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
topics/                            Public reader guides and cross-proposal topic crosswalks
  README.md                        Selective public topic-guide index
participate/                       Separately deployed public-interaction service and minimal lookup data
website/                           Public-site policy and website-only presentation assets
inventory/                         Structured source and GitHub issue registries
research/                          ARRP-created analyses, crosswalks, catalogs, transformed datasets, and research tools
sources/                           External source and backup files retained locally
scripts/                           Repeatable maintenance, intake, synchronization, and publication utilities
tests/                             Regression tests for project automation and repository conventions
exports/                           Generated DOCX, PDF, and XLSX outputs
archive/                           Superseded or migrated source snapshots
```

## File ownership

- A defect has one primary issue file.
- A major public subject may have one canonical topic page under `topics/` that concisely routes to authoritative records and identifies materially related rejected or outside-scope concepts without acquiring ownership of proposal substance, rejection decisions, scoring, audits, workflow state, or development tasks. Deferred records remain regular routes; merged or integrated records appear through their current homes rather than separate topic-page disposition entries. The Topic Page Standard in `METHODOLOGY.md` governs admission, structure, concision, and the verbatim-transfer test. If an existing ARRP research crosswalk becomes the public topic page, move and convert that file rather than retaining parallel copies.
- `SUBJECT_INDEX.md` maps organizations, subjects, acronyms, and aliases in one alphabetical sequence to concise linked record identifiers, with the preferred route first and common alternate terms redirected through **See** entries, without changing issue ownership.
- `README.md`, `areas/README.md`, the affected area README, `SUBJECT_INDEX.md`, any affected canonical topic page, and the GitHub issue registry form the reader-navigation bundle and are synchronized immediately for routing changes, with mandatory verification at T1. The root README exposes topic-guide, subject-index, and area-first discovery near its opening.
- Related areas cross-reference the primary file instead of duplicating analysis.
- Legislative drafts use the corresponding issue identifier.
- GitHub Projects is the authoritative area, issue, status, milestone, roadmap, and horizon-queue tracker.
- Source records in `inventory/sources.csv` may be associated with issues, areas, framework files, research files, topic guides, or project-level pages.
- Authorship controls the research/source boundary: unpublished ARRP-created analyses, crosswalks, catalogs, transformed datasets, and visualizations belong in `research/`; a project-authored synthesis selected as a canonical public topic guide belongs in `topics/`; external reports, filings, raw downloads, and backup copies belong in `sources/` when local retention is useful and appropriate.
- `research/` is work product, not a second proposal corpus: its analyses and tools may support an issue or topic guide, but the canonical public treatment remains on the owning issue or topic page. Its directory README identifies the maintained research products and routes readers to them.
- `sources/` is deliberately selective local preservation, not a mirror of every citation. Its directory README identifies each retained external file and its source-inventory record.
- `scripts/` and `tests/` are implementation support for repeatable project maintenance; they are not reader-facing project content. `.tmp/` (local dependency environment) and `.site-build/` (generated Pages staging artifact) are ignored local build products and are intentionally not cataloged as project materials.
- `inventory/sources.csv` remains the citation catalog for external sources whether or not a local copy is retained. The repository does not download every cited source merely because it appears in the inventory.
- GitHub Project items/fields, retained source inventory, audit-history sidecars, and affected Markdown pages should be updated in the same change that adds, removes, renames, merges, retires, or materially revises an area, issue, legislative proposal, audit status, or cited source.
- GitHub Project fields provide the compact cross-issue workflow, audit-status, and release-triage view.
- The public website is generated from the canonical Markdown rather than maintained as a second copy. `website/README.md` owns the publication boundary; `scripts/prepare_public_site.py` admits only `public-proposal` pages within the approved root, `areas/`, `legislation/`, and `topics/` paths; and the Pages workflow uploads only the validated generated artifact.
- The separately deployed `participate/` service is separated from unpublished research tooling and contains no internal source, monitoring, history, or candidate-review queues. It remains outside the Pages artifact by design: its public-input route posts to a canonical GitHub Discussion, its author-contact route sends only to the configured private mailbox, and formal intake review remains manually initiated through Codex.
- The `progress-dashboard` branch remains repository-visible but is excluded from the website artifact, navigation, search index, and sitemap.
- `framework/CURRENT_AUDIT.md` is the active handoff checkpoint for long audits and should be read before resuming vague follow-up instructions.
- Project-wide structural and integration checks update the governing files, validation scripts, and tests that own their durable findings; they do not create a new cumulative audit ledger or stand-alone report. Existing historical audit records remain preserved read-only.
- Audit rules and scoring live in `METHODOLOGY.md`; print assembly rules live in `PRINT_ASSEMBLY.md`; remedy categories and trigger stages live in `REMEDY_FRAMEWORK.md`.
