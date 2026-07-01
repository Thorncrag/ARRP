---
title: "Print Assembly Framework"
print_levels:
  - full-technical
---

# Print Assembly Framework

This file defines how the modular Markdown project should be assembled into a single proposal document for printing, PDF generation, DOCX export, or other linear publication.

Markdown files, GitHub Project records, issue audit-history files, and the retained source inventory remain canonical within their respective scopes. Generated print, PDF, DOCX, and other compiled editions are convenience exports.

## Assembly Objectives

A compiled proposal document should:

1. present the project as one coherent public-facing reform proposal;
2. preserve the modular area and issue structure used in the repository;
3. let readers move from institutional problem to proposed remedy without hunting through files;
4. keep proposed legislation available but separated from the main analysis; and
5. make citations, authorship, rights, and drafting limitations visible at the front.

## Canonical Assembly Order

The compiled proposal document should use the following order.

### Front Matter

1. cover page using the project title and subtitle from [`../README.md`](../README.md);
2. reader notice from [`../README.md`](../README.md);
3. rights and reuse notice from [`../README.md`](../README.md) and [`../LICENSE.md`](../LICENSE.md);
4. citation notice from [`../README.md`](../README.md) and [`../CITATION.cff`](../CITATION.cff);
5. authorship notice from [`../AUTHORS.md`](../AUTHORS.md);
6. table of contents generated from the assembled document; and
7. optional one-page executive summary when one is later drafted.

### Main Proposal Body

The main body should then include:

1. foundational premise, mission, scope, and governing principles from [`../README.md`](../README.md);
2. project areas in the order listed in [`../areas/README.md`](../areas/README.md);
3. for each area, the area README as the area introduction;
4. for each area, existing issue pages in issue-identifier order;
5. within each issue, the issue page's existing heading structure, including Issue Snapshot, Institutional Anomaly, Manifestation of the Failure, Resulting Damage, Underlying Weakness, Proposal Survey, Least-Complex Adequate Remedy, Repair and Prevention, Proposed Legislation where present, Proposed Constitutional Amendment and Proposed Enabling Legislation where present, Adoption Viability Note where present, Relationship to Adjacent Proposals where present, Budgetary Impact Statement, Proposal Scoring, Annotation, source notes, and internal cross-references where present.

If an issue exists only in the inventory or area README and does not yet have its own issue page, it should remain summarized in the area page and should not be expanded artificially in the compiled document.

### Appendices

Proposed legislation should appear after the main proposal body in appendices, not inline inside the main analysis.

Appendices should use this order:

1. Appendix A - Proposed Federal Legislation and Constitutional Amendments;
2. Appendix B - Model State Legislation;
3. Appendix C - Source-development materials, crosswalks, or research notes selected for publication;
4. Appendix D - Technical framework, contribution rules, and release process, if included in a technical edition; and
5. Appendix E - issue audit-history files for full technical editions, when audit provenance is included.

Appendix A should include legislation and constitutional-amendment files in issue-identifier order. For amendment-dependent proposals, place the amendment text before the enabling legislation, for example `DOJ-007-amendment.md` before `DOJ-007.md`. For ordinary federal proposals, use unsuffixed filenames first, for example `DOJ-001.md`, `ELEC-001.md`, `JUD-001.md`, and `WAR-001.md`.

Appendix B should include model state legislation files in issue-identifier order, using `-state` filenames, for example `ELEC-002-state.md`.

The main issue page should refer to proposed legislation through its Issue Snapshot Vehicle line, Least-Complex Adequate Remedy, or other relevant cross-reference. Legislation pages may keep issue-page relationships in metadata, such as `framework_issue`, but should not render separate internal-reference sections such as "Framework Issue" or "Framework Cross-Reference." Except for legislation index pages, legislation pages should refer to related proposals by plain identifier rather than internal Markdown links. The bill text itself should remain free of Markdown links unless the project later adopts a different legislative-text convention.

Legislation pages should use a narrow publication structure:

1. introductory text only when necessary to identify a special vehicle or circumstance, such as a constitutional amendment, model state bill, Justice Manual provision, statutory analogue, or proposed amendment;
2. the proposed legislative, constitutional, regulatory, rule, or manual text;
3. `Budgetary Impact Statement`;
4. `Drafting Notes`; and
5. `Source Notes`, or `Authority Notes` where the proposal specifically needs a legal-authority or statutory-hook map.

Relation-to-law provisions, rules of construction, severability clauses, definitions, and similar material should remain inside the proposed text when they are operative provisions. Explanatory crosswalks, manifestation-to-remedy mapping, implementation principles, and other analysis should live on the issue page, source-development page, or selected technical appendix rather than as standalone sections on the legislation page, unless the user deliberately creates a publication-specific appendix.

Issue audit-history files named `ISSUE-ID.audit.md` are technical sidecars. They should be included only in full technical editions or audit-specific exports unless the user deliberately chooses to publish audit provenance. Public proposal editions should generally keep only the issue page's compact Proposal Scoring section and omit the full audit-history sidecars.

## Area and Issue Ordering Rules

Area order is controlled by area identifiers:

```text
A-01, A-02, A-03, ...
```

Issue order within an area is controlled by issue identifiers and the area page:

```text
DOJ-001, DOJ-002, DOJ-003, ...
ELEC-001, ELEC-002, ELEC-003, ...
```

Developed issues should be included in full when an issue page exists.

Candidate issues without issue pages should not be expanded into placeholder sections in the compiled document. Their inventory descriptions remain visible through the area page unless and until developed issue pages are created.

Retired issues should be included only where necessary to preserve explanatory context. They should not receive standalone main-body sections unless a specific historical or cross-reference appendix is later created.

## Cross-References in Print

Internal Markdown links should be preserved for digital PDF and DOCX editions where possible, subject to the legislation-page limits above.

For print-only editions, cross-references should remain textually meaningful even when links are not clickable. Prefer references such as:

```text
See ELEC-005.
See Appendix A, ELEC-005.
See Appendix A, ELEC-005, p. 42.
```

Issue pages that refer to proposed legislation should identify the appendix destination when practical, but the canonical Markdown may continue to link to the legislation file.

Final public, legislative, and technical editions should support stable appendix references with resolved page numbers. Because page numbers are known only after pagination, the export workflow should eventually use a two-pass build:

1. generate the document and record the start page for each major section, area, developed issue, legislation appendix item, and technical appendix item;
2. regenerate the document with page-numbered cross-references, a page-numbered table of contents or appendix index, and references such as `Appendix A-1, DOJ-001 proposed legislation, p. 10`.

Manual page-number references should not be maintained in canonical Markdown because they will drift whenever content changes. Canonical issue pages should keep stable links and identifiers; the export layer should resolve those identifiers into appendix labels and page numbers for final print products.

## Heading Levels

The assembly process may normalize heading levels so the compiled document has a coherent hierarchy:

1. project title as the document title;
2. major front-matter sections as first-level sections;
3. each area as a first-level or second-level section, depending on export format;
4. each issue as a subsection under its area;
5. issue-internal headings nested below the issue heading;
6. each legislative appendix item as a separate appendix section.

The export process should preserve original issue titles and identifiers even if heading levels are adjusted.

## Citations and Source Notes

Citations should remain in the main body when they substantiate real-world events, legal materials, named actors, reports, or examples discussed there.

Source-development notes may be included in the main body, moved to a source appendix, or omitted from public-facing print editions depending on the intended audience. They should not be silently converted into unsupported claims.

## Export Variants

The project may later maintain more than one compiled edition:

1. **Full technical edition** - includes front matter, all area pages, all developed issue pages, legislation appendices, source-development appendices, and technical framework appendices.
2. **Public proposal edition** - includes front matter, area pages, developed issue pages, and legislation appendices, but omits technical repository-process materials.
3. **Legislative appendix edition** - includes only proposed legislation and related drafting notes.
4. **Executive summary edition** - includes front matter, brief area summaries, selected priority issues, and references to the full edition.

Unless otherwise specified, "compiled proposal document" means the public proposal edition.

## Print Assignment Metadata

Every Markdown page should identify the compiled edition or editions in which it belongs. The assignment belongs in page metadata so it is available to export tooling and review workflows without adding repetitive visible text to rendered pages.

Use the metadata key `print_levels` with one or more of these stable values:

| Metadata value | Visible label | Use |
| --- | --- | --- |
| `public-proposal` | Public proposal edition | Main public-facing proposal pages, area pages, developed issue pages, and legislation appendices used by the public proposal edition. |
| `full-technical` | Full technical edition | All pages that should remain available in the complete technical record, including framework, inventory, audit, research, source-development, archive, and process pages. |
| `legislative-appendix` | Legislative appendix edition | Proposed legislation pages and legislation-index pages intended for a legislation-only export. |
| `executive-summary` | Executive summary edition | Front-matter and area-summary pages that can support a short summary edition. |

Pages may belong to multiple levels. The metadata values should follow the order shown above. If a page is not appropriate for the public proposal, legislative appendix, or executive summary editions, assign it to `full-technical` only rather than omitting the print assignment.

## Backlog Reference

Roadmap, backlog, and to-do items are maintained only in [`FRAMEWORK.md`](FRAMEWORK.md). This file records print-assembly rules and should not maintain a separate roadmap.
