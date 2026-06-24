# Print Assembly Framework

This file defines how the modular Markdown project should be assembled into a single proposal document for printing, PDF generation, DOCX export, or other linear publication.

Markdown and CSV files remain canonical. Generated print, PDF, DOCX, and other compiled editions are convenience exports.

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
2. project areas in the order listed in [`../areas/README.md`](../areas/README.md) and [`../inventory/areas.csv`](../inventory/areas.csv);
3. for each area, the area README as the area introduction;
4. for each area, existing issue pages in issue-identifier order;
5. within each issue, the issue page's existing heading structure, including Issue Snapshot, Institutional Anomaly, Manifestations, Resulting Damage, Underlying Weakness, Repair and Prevention, Least-Complex Adequate Remedy, Proposal Survey, Annotations, source notes, and internal cross-references where present.

If an issue exists only in the inventory or area README and does not yet have its own issue page, it should remain summarized in the area page and should not be expanded artificially in the compiled document.

### Appendices

Proposed legislation should appear after the main proposal body in appendices, not inline inside the main analysis.

Appendices should use this order:

1. Appendix A - Proposed Federal Legislation and Constitutional Amendments;
2. Appendix B - Model State Legislation;
3. Appendix C - Source-development materials, crosswalks, or research notes selected for publication;
4. Appendix D - Technical framework, print assembly framework, contribution rules, and release process, if included in a technical edition.

Appendix A should include legislation files in issue-identifier order, using unsuffixed filenames first, for example `DOJ-001.md`, `ELEC-001.md`, `JUD-001.md`, and `WAR-001.md`.

Appendix B should include model state legislation files in issue-identifier order, using `-state` filenames, for example `ELEC-002-state.md`.

The main issue page should refer to proposed legislation through its Issue Snapshot Vehicle line, Least-Complex Adequate Remedy, or other relevant cross-reference. The bill text itself should remain free of Markdown links unless the project later adopts a different legislative-text convention.

## Area and Issue Ordering Rules

Area order is controlled by area identifiers:

```text
A-01, A-02, A-03, ...
```

Issue order within an area is controlled by issue identifiers and the issue inventory:

```text
DOJ-001, DOJ-002, DOJ-003, ...
ELEC-001, ELEC-002, ELEC-003, ...
```

Developed issues should be included in full when an issue page exists.

Candidate issues without issue pages should not be expanded into placeholder sections in the compiled document. Their inventory descriptions remain visible through the area page unless and until developed issue pages are created.

Retired issues should be included only where necessary to preserve explanatory context. They should not receive standalone main-body sections unless a specific historical or cross-reference appendix is later created.

## Cross-References in Print

Internal Markdown links should be preserved for digital PDF and DOCX editions where possible.

For print-only editions, cross-references should remain textually meaningful even when links are not clickable. Prefer references such as:

```text
See ELEC-005.
See Appendix A, ELEC-005.
```

Issue pages that refer to proposed legislation should identify the appendix destination when practical, but the canonical Markdown may continue to link to the legislation file.

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

## Future Automation

A future export script should assemble files according to this framework, generate a table of contents, normalize heading levels, verify local links, and place proposed legislation into appendices automatically.

Future table-of-contents work should wait until the project is more fully developed. At that stage, the compiled document should use a page-numbered, clickable PDF table of contents limited to major sections, project areas, developed issues, and appendices.
