---
title: "Content Navigation, Indexes, and Synchronization"
status: active
authority_scope: "Stable content identity, active and historical indexes, nonduplicative cross-references, canonical routes, and synchronized reader navigation."
load_when: "Creating, moving, renaming, promoting, merging, retiring, or otherwise rerouting an area, issue, candidate, or developed proposal."
dependencies:
  - "../../FRAMEWORK.md"
  - "../../component-registry.json"
  - "maturity-and-gates.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Content Navigation, Indexes, and Synchronization

## Authority and Dependencies

This file is the authoritative detailed standard for substantive project
inventory, index, and listing conventions. Repository placement belongs to
the [`Component Registry`](../../component-registry.json), and substantive
maturity to [`maturity-and-gates.md`](maturity-and-gates.md). The project configuration
must identify the exact repository paths, hosted-platform fields, labels,
views, headings, and synchronization mechanics that implement this standard.
Apply the synchronization section below whenever a route changes.

## Load When

Load this file when creating, moving, renaming, promoting, merging, retiring,
rejecting, or otherwise rerouting a collection, issue, candidate, or developed
proposal; changing a collection's active issue count; or deciding where
historical dispositions and cross-references belong.

## Inventory Files

A project adopting this standard must designate:

- one authoritative work-tracking surface for current workflow and lifecycle
  state;
- one retained-source catalog and, when needed, one temporary unresolved-source
  queue;
- one public front door, one ordered collection index, and one cross-collection
  subject or institution index; and
- an optional set of selective topic guides governed by
  [`topic-guides.md`](topic-guides.md).

Reader-facing indexes and topic guides are navigation surfaces. They do not
become authoritative work trackers, source catalogs, disposition logs, or
parallel taxonomies.

## Inventory Rules

1. Each substantive issue should have a stable identifier using the
   project-configured identifier scheme.
2. Each issue should have one primary collection or area home.
3. Candidates may remain work-tracker items until they receive a developed
   issue page.
4. Retired, merged, integrated, or otherwise adjudicated issues must remain
   traceable through a closed work item and the designated disposition record,
   collection page, audit history, registry, or source record rather than
   disappearing silently. Hosted work items should not be deleted unless
   created erroneously. When an adjudicated record has no remaining active
   work, remove it only from the active view while preserving the closed item
   and canonical disposition record.
5. A collection's active-count metadata counts active records only, including
   active candidates, deferred or blocked records, developing issues, and
   developed proposals. It excludes records finally merged, integrated,
   retired, rejected, or moved elsewhere. Update the count when any such
   transition occurs.
6. Substantive maturity and current workflow action or hold must remain
   separate concepts. Monitoring is independent of both. Canonical issue-page
   disposition metadata must use the values adopted by the project and must
   not copy superficially similar work-tracker values. Deterministic validation
   reports missing, blank, or nonstandard metadata rather than inferring it.
7. Every developed proposal issue should carry the configured review metadata,
   a visible quality-review summary, and a preserved audit-history record.
8. Work-tracker, source-catalog, registry, and page updates should be made in
   the same change as the substantive update that requires them.
9. The designated structured fields, rather than duplicate labels or body
   metadata, are authoritative for project-controlled routing, maturity,
   workflow, scoring, audit control, and parent-child values.
10. Labels should be limited to record kind or temporary triage not already
    represented by an authoritative structured field.
11. The cross-collection subject index should map plain-language terms and
    institutional names to stable collection and issue homes without
    duplicating volatile workflow fields or creating a second issue taxonomy.
12. A major public subject may receive one canonical topic guide when it spans
    multiple proposals or collections and explanatory synthesis materially
    improves navigation. Use the subject's commonly known name for the visible
    title and navigation label. Topic pages are concise, nonauthoritative
    routing surfaces governed by [`topic-guides.md`](topic-guides.md); they do
    not own proposal substance, disposition decisions, scores, audits, or
    workflow state. Convert and move an existing project-authored crosswalk
    when it becomes the topic guide rather than maintaining parallel versions.

## Area and Issue Index Rules

The public front door must expose topic, subject, and collection-first discovery
prominently. The project configuration identifies the exact files and
directories for those surfaces. Cross-collection lookup should be maintained
in one ordered sequence using subjects, departments, agencies, offices, courts,
acronyms, aliases, or other useful institutional names. Topic, collection, and
issue pages should carry stable repository links; hosted work items should
carry clickable canonical-page links where practical. Topic guides may explain
relationships among linked proposals but must not duplicate volatile workflow
fields. The subject index should contain only concise routes and must not
become a relationship narrative or parallel status, score, priority, or audit
tracker. Edition-specific page locators should be generated during export
rather than maintained manually in the canonical index.

### Area-Page Issue Lists

A collection page must present live work before historical dispositions. Its
principal list includes unresolved candidates as well as developed proposals,
because both present live project questions. It must not mix finally merged,
integrated, retired, rejected, or rerouted records into the active list, or
reproduce volatile workflow, score, priority, audit, or roadmap fields.

When an identifier was assigned during preliminary review but did not produce a
standalone proposal, preserve the identifier below the active list with a
concise disposition and route to its current home. Consolidate records sharing
one destination, omit obsolete titles and priorities, and leave detailed
analysis in the canonical disposition record.

A developed proposal later made inactive is not merely a numbering gap.
Preserve its linked identifier and title, a concise disposition, and its
current destination. Do not demote it into an undeveloped-candidate list or
delete its page. Omit empty historical sections. Exact headings, list syntax,
and identifier presentation belong in the project configuration.

## Links to Developed Work

When an issue becomes developed, maintain consistency among its hosted work
item, collection index entry, cross-collection subject routes, stable registry,
canonical issue page, proposal vehicles, and retained source-development or
research records. The project configuration identifies the exact surfaces.

## Cross-References

Tracking entries should not duplicate developed analysis. Where a related issue is developed elsewhere, cross-reference the primary area or issue instead of repeating the same diagnosis, evidence, or remedy.

## Navigation Synchronization

Treat the public front door, collection index, affected collection page,
subject index, topic-guide index and affected guide, and stable
hosted-platform-to-content registry as one reader-navigation bundle.

Update the affected surfaces in the same change whenever an area, issue,
candidate, topic guide, identifier, title, primary home, canonical page, or
final disposition is created, renamed, moved, promoted, merged, retired, or
materially rerouted. A source, analysis, scoring, or drafting edit need not
change the bundle unless it changes identity, ownership, disposition, canonical
location, or a useful reader route.

The first integration-level review of a record must verify that:

- the public front door exposes topic, subject, and collection discovery;
- affected topic guides point to authoritative content without duplicating
  workflow state;
- the record appears once in its correct collection;
- the subject index follows its canonical conventions and routes correctly;
- the stable registry identifies the correct canonical page; and
- affected local links resolve.

An initial triage scan may flag an obvious navigation defect, but it must not
publish an unadmitted candidate into public navigation. Once a promotion,
merger, retirement, or other routing decision is authorized, navigation
synchronization is part of implementing that decision, not a later cleanup.
