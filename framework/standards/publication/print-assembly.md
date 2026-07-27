---
title: "Print and Edition Assembly Standard"
status: active
authority_scope: "Reusable selection, ordering, cross-reference, locator, metadata, and validation rules for linear editions and exports."
load_when: "Assigning publication disposition, designing an edition, or building or validating a PDF, DOCX, print, or other linear export."
dependencies:
  - "../content/navigation-and-indexes.md"
print_status: excluded
print_exclusion_reason: "Internal publication standard."
---

# Print and Edition Assembly Standard

Canonical content and records remain authoritative. A compiled edition is a
versioned convenience export with an explicit selection and order.

## Assembly rules

An edition must:

1. identify its intended audience, scope, version, and date;
2. select pages through explicit publication metadata or an exact manifest;
3. distinguish included, excluded, unclassified, and conflicting pages;
4. preserve one canonical content source rather than maintaining export-only
   substantive copies;
5. generate its table of contents, cross-references, indexes, and page locators
   from the final pagination;
6. separate main analysis, proposed instruments, supporting appendices, and
   technical records according to the edition plan; and
7. state authorship, rights, limitations, citation guidance, and where current
   online records can be found.

Page metadata owns whether a page may appear in an edition. The project manifest
owns named sections, default routing, and explicit placement or order
overrides. A browser or Console may stage a draft instruction list, but only an
authorized repository change alters either authority.

## Cross-references and locators

Canonical Markdown keeps stable digital links. The export process may replace
internal links with print locators only after final pagination is known. Use a
two-pass build when page numbers affect the assembled source. Never maintain
edition-specific page numbers manually in canonical content.

External authorities and project-created supporting records must remain
distinguishable. Generated source lists preserve the exact cited locator and
record class.

## Validation

Validate manifest schema, page classification, duplicate or missing
assignments, order, heading hierarchy, links, generated locators, page count,
metadata, visual layout, and reproducibility. Generated exports are not
committed during ordinary content work unless the export is the requested
deliverable or part of an authorized release pass.
