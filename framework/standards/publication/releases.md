---
title: "Release Standard"
status: active
authority_scope: "Reusable snapshot, provenance, citation, rights, limitation, approval, and verification rules for public releases."
load_when: "Planning, creating, reviewing, or changing a public release."
dependencies:
  - "print-assembly.md"
  - "../automation/validation-and-closeout.md"
print_status: excluded
print_exclusion_reason: "Internal publication standard."
---

# Release Standard

A public release is a dated, reproducible snapshot authorized for a defined
audience and reuse posture. Availability for public review is not the same as a
license for public reuse.

Before release:

1. identify the exact version, source revision, scope, and release date;
2. verify public entry pages, authorship, citation metadata, rights, reader
   notices, and known limitations;
3. verify all selected content, sources, links, generated locators, and export
   artifacts;
4. confirm that private, ignored, temporary, credential, local-state, and
   review-only material is excluded;
5. require the governing GitHub disclosure gate to approve the exact complete
   release family and revision, including source documents, generated PDFs,
   content-bearing generators, templates, fixtures, tests, release notes, and
   assets; unknown, restricted, private, or secret material fails closed;
6. confirm hosted settings, publication checks, branch protection, and final
   human authorization;
7. preserve the final manifest, checksums, build provenance, disclosure
   decision, and readback; and
8. publish concise release notes that distinguish completed, draft, and
   unresolved work.

Licensing changes require an express human decision and synchronized updates to
the license, public notices, citation guidance, and release record.
