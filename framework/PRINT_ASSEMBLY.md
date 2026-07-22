---
title: "Print Assembly Framework"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Print Assembly Framework

This file defines how the modular Markdown project should be assembled into a single proposal document for printing, PDF generation, DOCX export, or other linear publication.

Markdown files, GitHub Project records, issue audit-history files, and the retained source inventory remain canonical within their respective scopes. Generated print, PDF, DOCX, and other compiled editions are convenience exports.

[`print-assembly.json`](print-assembly.json) is the machine-readable companion to this framework. Page-level publication-disposition metadata determines whether a page belongs in one or more editions or is deliberately excluded from print; the manifest determines each edition's named sections, default routing, and explicit placement or order overrides. The Project Console may stage a revised disposition or sequence and export it for Codex review, but neither the browser draft nor a generated table of contents changes the manifest or page metadata directly.

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
2. [`../ABOUT.md`](../ABOUT.md), containing the reader notice, project approach, authorship, technical-record access, contact, citation, and reuse routes;
3. [`../PRINT_READERS_GUIDE.md`](../PRINT_READERS_GUIDE.md), with the generated quick issue lookup and online technical-record notice;
4. table of contents generated from the assembled document; and
5. optional one-page executive summary when one is later drafted.

### Main Proposal Body

The main body should then include:

1. foundational premise, mission, scope, and governing principles from [`../README.md`](../README.md);
2. selected public topic guides from [`../topics/`](../topics/) when they materially improve cross-proposal navigation, in alphabetical order unless an edition-specific editorial plan requires another order;
3. project areas in the order listed in [`../areas/README.md`](../areas/README.md);
4. for each area, the area README as the area introduction;
5. for each area, existing substantive issue pages in issue-identifier order, excluding internal source-development shells;
6. within each issue, the issue page's existing heading structure, including Issue Snapshot, Institutional Anomaly, Manifestation of the Failure, Resulting Damage, Underlying Weakness, Proposal Survey, Least-Complex Adequate Remedy, Repair and Prevention, Proposed Legislation where present, Proposed Constitutional Amendment and Proposed Enabling Legislation where present, Adoption Viability Note where present, Relationship to Adjacent Proposals where present, Budgetary Impact Statement, Proposal Scoring, Annotation, source notes, and internal cross-references where present.

If an issue exists only in the inventory or area README and does not yet have its own substantive issue page, it should remain summarized in the area page and should not be expanded artificially in the compiled document. A `record_type: source-development` shell is an internal routing record, is excluded from compiled editions and the public website, and does not count as developed, audited, scored, review ready, or otherwise mature for print or progress reporting.

### Appendices

Proposed legislation should appear after the main proposal body in appendices, not inline inside the main analysis.

Appendices should use this order:

1. Appendix A - Proposed Federal Legislation and Constitutional Amendments;
2. Appendix B - Model State Legislation;
3. Appendix C - reader-useful ARRP evidence, research, crosswalks, catalogs, or other project work product deliberately selected for publication.

Reader-facing issue evidence records are supplemental rather than additional issue proposals. A public edition may place selected records in an evidence appendix when their inclusion materially supports the documented pattern without overloading the main issue page. A concise edition may omit them while retaining the issue page's anchor evidence and digital link.

Appendix A should include legislation and constitutional-amendment files in issue-identifier order. For amendment-dependent proposals, place the amendment text before enabling legislation. When both preferred and independent implementing Acts exist, use amendment, preferred, then independent order—for example `DOJ-007-amendment.md`, `DOJ-007-preferred.md`, then `DOJ-007.md`. For ordinary federal proposals, use unsuffixed filenames first, for example `DOJ-001.md`, `ELEC-001.md`, `JUD-001.md`, and `WAR-001.md`.

Appendix B should include model state legislation files in issue-identifier order, using `-state` filenames, for example `ELEC-002-state.md`.

The main issue page should refer to proposed legislation through its Issue Snapshot Vehicle line, Least-Complex Adequate Remedy, or other relevant cross-reference. Legislation pages may keep issue-page relationships in metadata, such as `framework_issue`, but should not render separate internal-reference sections such as "Framework Issue" or "Framework Cross-Reference." Except for legislation index pages, legislation pages should refer to related proposals by plain identifier rather than internal Markdown links. The bill text itself should remain free of Markdown links unless the project later adopts a different legislative-text convention.

Legislation pages should use a narrow publication structure:

1. introductory text only when necessary to identify a special vehicle or circumstance, such as a constitutional amendment, model state bill, Justice Manual provision, statutory analogue, or proposed amendment;
2. the proposed legislative, constitutional, regulatory, rule, or manual text;
3. `Budgetary Impact Statement`;
4. `Drafting Notes`; and
5. `Source Notes`, or `Authority Notes` where the proposal specifically needs a legal-authority or statutory-hook map.

Relation-to-law provisions, rules of construction, severability clauses, definitions, and similar material should remain inside the proposed text when they are operative provisions. Explanatory crosswalks, manifestation-to-remedy mapping, implementation principles, and other analysis should live on the issue page, a research page, or a deliberately selected reader appendix rather than as standalone sections on the legislation page, unless the user creates a publication-specific appendix.

Issue audit-history files named `ISSUE-ID.audit.md` are online technical sidecars and are omitted from ordinary compiled editions. A separately requested audit-specific export may include them without creating a permanent technical-edition classification. Public proposal editions keep only the issue page's compact Proposal Scoring section.

Issue evidence records under `areas/AREA/evidence/` are reader-facing supplements, not audit sidecars. Their placement should follow the edition-specific evidence-appendix rule above; they should not be inserted automatically after their parent issue in a way that makes them appear to be an independent proposal.

### Back Matter

The public-proposal edition should end with a generated **Subject and Institution Index** based on [`../SUBJECT_INDEX.md`](../SUBJECT_INDEX.md). The canonical index supplies one alphabetical sequence of entities, subjects, acronyms, and aliases together with ordered stable identifiers, digital links, a marked preferred route, and conventional **See** redirects for especially common alternate terms. The export layer supplies the page numbers for the particular edition.

Keeping the complete index in back matter does not make it a secondary discovery path. The opening front matter must point readers to it prominently, and digital navigation should make it reachable directly without requiring readers to traverse the linear table of contents.

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

Developed issues should be included in full when a substantive issue page exists.

Candidate issues without substantive issue pages should not be expanded into placeholder sections in the compiled document. Their inventory descriptions remain visible through the area page unless and until developed issue pages are created. Internal source-development shells do not change this rule.

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

Final public, legislative-appendix, and executive-summary editions should support stable references with resolved page numbers where their contents require them. Because page numbers are known only after pagination, the export workflow should use a two-pass build:

1. generate the document and record the start page for each major section, area, developed issue, legislation appendix item, and selected appendix item;
2. regenerate the document with the opening quick issue lookup in [`../PRINT_READERS_GUIDE.md`](../PRINT_READERS_GUIDE.md), the Subject and Institution Index pointer, page-numbered cross-references, a page-numbered table of contents or appendix index, and references such as `Appendix A-1, DOJ-001 proposed legislation, p. 10`.

Manual page-number references should not be maintained in canonical Markdown because they will drift whenever content changes. Canonical issue pages should keep stable links and identifiers; the export layer should resolve those identifiers into appendix labels and page numbers for final print products.

## Subject-Index Assembly

The subject and institution index requires edition-specific page locators and should use the same two-pass principle as other resolved cross-references:

1. during the first pass, record the start and end pages for every area page, developed issue, legislation item, and selected appendix item;
2. map each stable target linked from [`../SUBJECT_INDEX.md`](../SUBJECT_INDEX.md) to the page or page range where that target appears in the assembled edition;
3. when a candidate issue has no standalone page, resolve its locator to the page containing the candidate entry on the applicable area page;
4. render each **See** entry as a cross-reference to its canonical index term without assigning the redirect its own page locator;
5. during the second pass, render a conventional alphabetical back-of-book index with comma-separated pages or page ranges while preserving clickable links in digital PDF and DOCX editions; and
6. collapse duplicate locators and omit targets not included in the selected edition, without changing the canonical subject-to-issue mapping.

The printed index should preserve the canonical distinction between the preferred route and any alternate locators, but it should not add relationship analysis or reproduce proposal status, score, priority, or audit metadata. If pagination changes, regenerate the index rather than editing page numbers in `SUBJECT_INDEX.md`.

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

The project may maintain three compiled editions:

1. **Public proposal edition** - includes front matter, topic guides, area pages, developed issue pages, legislation appendices, and deliberately selected reader-useful evidence or research, while omitting technical repository-process materials.
2. **Legislative appendix edition** - includes proposed legislation and related drafting notes.
3. **Executive summary edition** - includes front matter, brief area summaries, selected priority issues, and references to the public proposal.

The repository and public website provide the complete technical record. Audit histories or other specialized technical materials may be assembled on request without maintaining a permanent technical print edition or assigning every online record to print.

Unless otherwise specified, "compiled proposal document" means the public proposal edition.

Before version 1.0, compiled PDF, DOCX, XLSX, and similar export files are not expected to remain synchronized after ordinary proposal or source edits. Treat them as generated snapshots. Rebuild them only when the user requests an export refresh, the export is the deliverable, export tooling is being tested, or the project is in an explicit release, publication, or print-assembly pass.

## Print Assignment Metadata

Every publication-controlled Markdown page must carry exactly one of two dispositions: inclusion in one or more compiled editions, or explicit exclusion from print with a reason. The disposition belongs in page metadata so it is available to export tooling and review workflows without adding repetitive visible text to rendered pages. Tool-discovered control files such as root `AGENTS.md` and website-only assets such as `website/404.md` are not publication-controlled pages and are exempt.

Use the metadata key `print_levels` with one or more of these stable values:

| Metadata value | Visible label | Use |
| --- | --- | --- |
| `public-proposal` | Public proposal edition | Main public-facing proposal pages, topic guides, area pages, developed issue pages, and legislation appendices used by the public proposal edition. |
| `legislative-appendix` | Legislative appendix edition | Proposed legislation pages and legislation-index pages intended for a legislation-only export. |
| `executive-summary` | Executive summary edition | Front-matter and area-summary pages that can support a short summary edition. |

Pages may belong to multiple levels. The metadata values should follow the order shown above. Evidence or research receives `public-proposal` only when its inclusion materially improves the reader edition; otherwise it remains available online and is explicitly excluded from print.

If a page is not suitable for any compiled edition, omit `print_levels` and record both:

```yaml
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
```

Do not combine `print_status: excluded` with `print_levels`. An excluded page must state a concise reason. A page with neither an edition assignment nor an exclusion is **unclassified** and blocks publication preflight; a page with both dispositions is a metadata conflict and likewise blocks preflight. Typical exclusions include internal logs, templates, source-development records, tooling instructions, and working-process files. Exclusion from print does not remove a file from the repository or necessarily from the public website.

## Publication Analysis and Assembly Preview

The Project Console Publication workspace provides three non-authoritative views: complete page dispositions, edition-level composition and preflight analysis, and a section-by-section document builder. Its assignment view must separately count and filter pages included in each edition, pages explicitly excluded with reasons, unclassified pages, and conflicting metadata so the effect of publication decisions is visible at a glance. Estimated pages are planning approximations based on source length; an actual PDF page count, when available, is authoritative only for that generated snapshot. The preflight should surface unclassified or conflicting dispositions, missing exclusion reasons, invalid metadata, unplaced pages, unusually long pages, wide Markdown tables, heading anomalies, and stale generated builds without automatically rewriting source material.

The document builder derives a proposed table of contents and appendix sequence from the manifest and current page assignments. Section and page moves remain local until exported. Codex must validate any export, update the manifest or page front matter as appropriate, rebuild the console, and run the ordinary project-consistency checks before treating the change as canonical.

## Backlog Reference

Roadmap, backlog, and to-do items are maintained in the GitHub Project and Issues under [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md). This file records print-assembly rules and does not maintain a separate roadmap.
