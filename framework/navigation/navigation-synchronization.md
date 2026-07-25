---
title: "Navigation Synchronization"
status: active
authority_scope: "The reader-navigation bundle, events requiring immediate synchronization, and the T1 navigation verification gate."
load_when: "An area, issue, candidate, topic guide, identifier, title, primary home, canonical page, or final disposition is created, renamed, moved, promoted, merged, retired, or materially rerouted."
dependencies: "../FRAMEWORK.md; inventory-and-indexes.md; topic-guides.md; ../GITHUB_WORKFLOW.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Navigation Synchronization

## Authority and Dependencies

This file is the authoritative detailed standard for synchronizing public discovery and canonical routes. Apply [`inventory-and-indexes.md`](inventory-and-indexes.md) to issue and area ownership, [`topic-guides.md`](topic-guides.md) to public subject routing, and [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md) to GitHub registry and Project mechanics.

## Load When

Load this file when an area, issue, candidate, topic guide, identifier, title, primary home, canonical page, or final disposition is created, renamed, moved, promoted, merged, retired, or materially rerouted.

## Navigation Synchronization Check

Treat the following as one reader-navigation bundle:

1. [`../../README.md`](../../README.md), the public repository front door and its topic-first and area-first routes;
2. [`../../areas/README.md`](../../areas/README.md), the project-area table of contents;
3. the affected `areas/AREA/README.md`, the issue-level table of contents for that area;
4. [`../../SUBJECT_INDEX.md`](../../SUBJECT_INDEX.md), the cross-area subject and institution lookup;
5. [`../../topics/README.md`](../../topics/README.md), the topic-guide index, and any affected canonical topic page when the routing event concerns a major public subject; and
6. [`../../inventory/github_issue_registry.csv`](../../inventory/github_issue_registry.csv), the stable GitHub-to-canonical-record navigation registry.

Update the affected surfaces immediately when an area or issue is created, renamed, moved, merged, retired, promoted, or materially rerouted. Do not wait for the next audit to repair known navigation drift. A source, analysis, scoring, or drafting edit need not change the navigation bundle unless it changes an identifier, title, area ownership, canonical page, disposition, or useful reader lookup route.

T1 is the mandatory verification gate because it is the first tier designed to test framework and project integration. A T1 Navigation Synchronization Check must confirm that the repository front door provides prominent topic-guide, subject-index, and area-first routes; any affected topic page points to the correct authoritative proposal homes without duplicating workflow state; the issue appears once in the correct area contents page; the project-area contents remains correct if an area changed; the Subject and Institution Index follows its canonical conventions and points to the correct stable record; the GitHub registry identifies the correct canonical page; and affected local links resolve. T0 should flag an obvious navigation defect for an already existing stable record, but a T0 triage scan does not add an unadmitted Horizon candidate to the contents, subject index, or topic guides. If T0 leads to an approved admission, promotion, move, merger, retirement, or other routing decision, update the navigation bundle immediately as part of implementing that decision.
