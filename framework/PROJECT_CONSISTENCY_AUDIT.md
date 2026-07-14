---
title: "Project Consistency Audit — July 14, 2026"
print_levels:
  - full-technical
---

# Project Consistency Audit — July 14, 2026

## Scope and Authority

This non-tier, non-scoring audit checked cross-project structure and integration. It covered current issue and audit files, legislation metadata and section architecture, area and subject navigation, source and GitHub registries, JUD-011 cross-issue treatment, audit-run nomenclature, GitHub Project alignment, and the public-site boundary. It did not reevaluate proposal merits or change any Proposal Quality Score, lifecycle status, or audit **Runs** count.

## Baseline

- 38 current issue pages and 38 sibling audit-history files.
- 37 proposed-legislation pages.
- 24 area pages.
- 245 GitHub issue-registry rows.
- 731 source-inventory rows, sequentially numbered `SRC-0001` through `SRC-0731` without duplication.
- 180 project Markdown files in the checked repository surface, excluding generated site environments and dependency files.

## Checks Completed

The audit confirmed:

- all issue identifiers, area prefixes, filenames, sidecars, `source_issue` values, and audit-history links align;
- all current issue pages contain the required core front matter;
- all legislation pages identify an issue and a valid framework target;
- all registry canonical paths exist, with no duplicate GitHub issue numbers or Project object identifiers;
- every current issue is linked exactly once from its correct area page, and every area is linked correctly from the area index;
- required issue-section order and Issue Snapshot placement pass on 37 of 38 pages;
- JUD-011 treatment is consistent across REG-001, FUND-001, and DOJ-007, including independent alternatives and separate pathway budget presentations;
- source/research ownership follows the authorship rule, with no remaining `source-development/` paths;
- the public-site allowlist excludes internal framework, audit, progress-dashboard, research, and retained-source material as intended; and
- repository scores, lifecycle statuses, and Change Audit flags match the GitHub Project for all 38 current issues.

## Mechanical Corrections

The audit made only corrections traceable to an existing convention or authoritative record:

- added missing full-technical print metadata to the two governing JUD-011 framework files;
- corrected variant proposal identifiers for `ELEC-002-state` and `ELEC-009-amendment`;
- added the missing DOJ-004 route to the Subject and Institution Index;
- normalized both DOJ-007 proposal pages to the required `Budgetary Impact Statement` heading while retaining a clear preferred-path or independent-alternative label;
- restored the required section order on the EMERG-003 legislation page;
- normalized EMOL-015's audit-history heading hierarchy;
- clarified historical T-audit headings whose wording could incorrectly imply an extra or completed tier;
- removed invalid `T5` terminology from ELEC-012 and recast the continuing work as a repeat T4 legal-readiness follow-up without changing its four completed runs; and
- synchronized demonstrably stale GitHub Project rebaseline and Last/Next Audit fields to their authoritative repository records.

## Findings Reserved for Proposal-Specific Work

The following findings require judgment or substantive development and were not silently corrected:

1. **DOM-009 architecture.** DOM-009 remains the single current page using its expressly retained candidate/source-development structure rather than the full developed-issue architecture. Its next source-development or T1 pass should migrate the page while preserving every proposition and citation.
2. **Legislation support sections.** DOM-005 lacks a proposal-page Budgetary Impact Statement and Source/Authority Notes; EMERG-003 and FUND-001 lack proposal-page Source/Authority Notes. These should be completed during their next proposal-specific T1 or T4 work from verified sources rather than supplied as empty or invented sections.
3. **Source-inventory reconciliation.** Exact URL comparison found 52 non-project citation targets without an exact inventory match. The set includes normalization variants, alternate official URLs, and potentially uncatalogued sources. A dedicated reconciliation pass should deduplicate equivalents and add only genuinely missing source records.
4. **Snapshot concision judgment.** Six Issue Snapshots contain one or more cells longer than the ordinary concise-target guideline: DOJ-007, DOM-005, ELEC-008, ELEC-012, EMERG-003, and RIGHTS-004. Because the limit is advisory and the recent style audit already reviewed these pages, future issue-specific editing should tighten them only where precision and meaning are preserved.

## Audit-Count Result

This Project Consistency Audit is not a T0–T4 issue-quality audit. It changes no **Runs** count. Historical heading corrections clarify the existing count; they do not create, erase, or relabel substantive work as a completed tier.

## Validation

Repository structure, links, metadata, registry and Project synchronization, source numbering, public-site boundary tests, and the strict site build were rerun after correction. Validation results are recorded in the completing commit and continuous-integration run.
