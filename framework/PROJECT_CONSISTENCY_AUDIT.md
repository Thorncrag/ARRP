---
title: "Project Consistency Audit — July 18, 2026"
print_levels:
  - full-technical
---

# Project Consistency Audit — July 18, 2026

> **Historical record.** This July 18 snapshot is retained for provenance. Future Project Consistency Audits do not create a stand-alone report; they incorporate durable lessons into the governing method, validation scripts, or tests that own them.

## Scope and Authority

This non-tier, non-scoring audit reviewed cross-project structure, logic, reader-facing language, methodology, automation, inventories, proposal routing, and GitHub workflow alignment. It did not reevaluate proposal merits or change a Proposal Quality Score, lifecycle status, or audit **Runs** count. Substantive legal, evidentiary, fiscal, remedy, and scoring questions remain proposal-specific work.

## Baseline

- 41 issue pages and 41 sibling audit-history files.
- 39 proposed-legislation, amendment, or model-act pages.
- 24 area pages and 13 public topic guides.
- 277 GitHub issue-registry rows.
- 1,192 source-inventory records, sequentially numbered `SRC-0001` through `SRC-1192`.

## Checks Completed

The audit confirmed:

- every issue identifier, title heading, audit-history link, declared proposal route, legislation-to-issue route, and local reader-facing link resolves;
- every developed issue contains the required reader architecture, while candidate, deferred, and paused records are not forced into a developed-page template prematurely;
- every area page uses one ordered reader structure: concern, active issues, boundaries, and notes; optional candidate dispositions, former-developed-proposal lists, and source-development material remain distinct;
- topic guides use the public-facing `Public concern` / `Applicable proposals` routing structure and retain their nonauthoritative role;
- the unified **Supporting Record and Updates** subsection appears only at the end of Manifestations, with no legacy top-level monitoring or evidence headings;
- public proposal surfaces avoid unexplained tier, Change Audit, rebaseline, and loaded shorthand terminology;
- the JUD-011 architecture is coherent: REG-001 and FUND-001 use JUD-011 alone as the general preferred remedy and retain complete standalone alternatives; DOJ-007 uses only its separately authorized, firewalled shared-infrastructure pattern; listed exclusions are not presented as covered;
- registry GitHub issue numbers and Project object identifiers are unique, source identifiers are continuous, and all registry canonical paths resolve;
- all 40 automated tests pass, the public-site preparation succeeds, and `git diff --check` passes; and
- the GitHub Project audit-control readback identified one stale field only: FED-003's `Rebaseline status`. It was corrected from the canonical issue-page record to `Current fixed status` and a second readback found no remaining planned audit-field changes.

## Mechanical Corrections

The audit made only convention-governed or directly supported corrections:

- added a required Budgetary Impact Statement to the DOM-005 bill, consistent with its explicit authorization of appropriations and the issue-page classification;
- added [`../scripts/audit_project_consistency.py`](../scripts/audit_project_consistency.py), a repeatable non-scoring linter for issue/vehicle metadata, reader architecture, area and topic conventions, supporting-record placement, local links, registry identities, source numbering, and reader-language drift;
- incorporated that linter into the Project Consistency Audit method and retained the full test suite and public-site build as complementary validation;
- translated internal audit shorthand from reader-facing area, issue, and legislative surfaces while preserving exact terminology in metadata, audit histories, and methodology records;
- normalized the FED, DOM, HER, and IMM area-page heading order and boundary presentation; and
- corrected the verified FED-003 Project rebaseline field without changing its score, lifecycle status, or Runs count.

## Follow-Up Requiring Source Reconciliation

Normalized exact-URL comparison found 33 cited external URLs that do not currently have an exact match in `inventory/sources.csv` after excluding ARRP’s own GitHub, monitoring, Project, and public-contact links. The group includes alternate official or archival endpoints for sources already represented in the ledger, as well as citations that may need first-time source capture. This is a source-inventory reconciliation task, not a basis to weaken or expand any proposal now. A dedicated pass should compare source identity and proposition—not URL text alone—then either associate the existing canonical source, add a concise unreviewed capture record, or replace the page link with the already-registered canonical endpoint. The task should preserve the current qualitative evidence-placement rule and avoid creating unnecessary evidence pages.

## Audit-Count Result

This Project Consistency Audit does not increment **Runs**. It made no Proposal Quality Score, rubric, readiness, rebaseline, or lifecycle change other than the existing-record FED-003 Project-field synchronization described above.

## Validation

- `python3 scripts/audit_project_consistency.py` — 0 errors, 0 warnings.
- `python3 -m unittest discover -s tests -v` — 40 tests passed.
- `python3 scripts/prepare_public_site.py` — 123 canonical Markdown pages and one generated page prepared; 120 excluded internal links safely demoted in the staged public artifact.
- `git diff --check` — passed.
- `python3 scripts/sync_project_audit_fields.py` after the FED-003 correction — 0 planned changes.
