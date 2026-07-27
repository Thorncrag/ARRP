---
title: "ARRP Navigation and Index Synchronization"
status: active
authority_scope: "Exact ARRP work tracker, repository paths, area-list presentation, topic-guide configuration, and reader-navigation synchronization bundle."
load_when: "Creating, moving, renaming, promoting, merging, retiring, or rerouting an ARRP area, issue, candidate, topic guide, or developed proposal."
dependencies:
  - "../../standards/content/navigation-and-indexes.md"
  - "../../standards/content/topic-guides.md"
  - "../github/workflow.md"
  - "../REPOSITORY_MAP.md"
  - "../interfaces/visual-identity.md"
print_status: excluded
print_exclusion_reason: "Internal project configuration."
---

# ARRP Navigation and Index Synchronization

This file supplies the exact ARRP implementation of the reusable
[`navigation-and-indexes.md`](../../standards/content/navigation-and-indexes.md)
and [`topic-guides.md`](../../standards/content/topic-guides.md) standards.

## Authoritative ARRP surfaces

- The [ARRP GitHub Project](https://github.com/users/Thorncrag/projects/2)
  controls area, issue, lifecycle, milestone, roadmap, workstream, and Horizon
  queue tracking under [`workflow.md`](../github/workflow.md).
- [`../../../inventory/sources.csv`](../../../inventory/sources.csv) catalogs
  external sources affirmatively relied upon in substantive ARRP records.
- [`../../../inventory/sources-pending.csv`](../../../inventory/sources-pending.csv)
  is the temporary routing queue for retained sources whose accountable
  destination is genuinely unclear.
- [`../../../README.md`](../../../README.md) is the public front door;
  [`../../../areas/README.md`](../../../areas/README.md) is the ordered area
  index; [`../../../SUBJECT_INDEX.md`](../../../SUBJECT_INDEX.md) is the single
  alphabetical subject and institution index; and
  [`../../../topics/README.md`](../../../topics/README.md) indexes selective
  public topic guides.
- [`../../../inventory/github_issue_registry.csv`](../../../inventory/github_issue_registry.csv)
  is the stable GitHub-item-to-canonical-page registry.
- [`../../records/candidates/horizon-scan-log.md`](../../records/candidates/horizon-scan-log.md),
  closed GitHub issues, issue audit histories, area pages, registry rows, and
  source records preserve final dispositions.

GitHub Project fields—not labels or issue-body metadata—are authoritative for
the routing, maturity, workflow, scoring, audit-control, and parent/sub-issue
values defined in [`workflow.md`](../github/workflow.md). Labels are limited to
issue kind or temporary triage not already represented by a Project field.
Project, inventory, registry, and page updates occur in the same change as the
substantive update requiring them.

Substantive maturity uses `Development level`; current workflow action or hold
uses `Status`; monitoring is independent of both. Every canonical issue page
also carries the separate lowercase `status` field governed, including its
accepted vocabulary and validation behavior, by
[`workflow.md`](../github/workflow.md). Do not copy Project `Status` values into
the page field.

Area `issue_count` front matter counts active candidates, deferred or blocked
records, developing issues, and developed proposals. It excludes records
finally merged, integrated, retired, rejected, or moved elsewhere.

## Area-page issue lists

Every area page uses **Active Issues** for its principal bulleted list. Each
entry uses `IDENTIFIER — Proposal title`. When a standalone issue page exists,
link the entire bold identifier-and-title label; otherwise display the entire
label as bold plain text. The list includes unreviewed or source-development
candidates and developed proposals, but not finally merged, integrated,
retired, rejected, or rerouted records. It does not reproduce lifecycle,
score, priority, audit, or roadmap fields.

Identifiers assigned during preliminary review that did not produce standalone
proposals appear in a compact bulleted **Prior Issue Numbers** list. Introduce
the list in reader-facing language explaining that the numbers did not become
separate proposals and appear only to explain sequence gaps. Begin each entry
with the bold identifier or consolidated range, followed by an em dash and the
disposition. Route readers to the current home or final disposition,
consolidate records with the same destination, and omit obsolete titles,
priorities, and underlying analysis.

A developed proposal later made inactive appears under **Former Developed
Proposals** with its linked bold identifier-and-title label, an em dash, a
concise disposition, and its current destination. Do not demote it into the
undeveloped-candidate list or delete its page. Omit empty disposition sections,
but retain **Active Issues** and its list.

## Developed-work and synchronization bundle

When an issue becomes developed, synchronize:

- its GitHub Project item;
- its area README entry;
- all applicable Subject and Institution Index entries;
- its `inventory/github_issue_registry.csv` row;
- its canonical `areas/<AREA>/issues/<ISSUE>.md` page;
- any `legislation/<ISSUE>.md` vehicle; and
- retained source-development or research notes.

Treat `README.md`, `areas/README.md`, the affected area README,
`SUBJECT_INDEX.md`, `topics/README.md`, the affected topic guide, and
`inventory/github_issue_registry.csv` as the exact ARRP reader-navigation
bundle. Keep topic, area, and issue links stable; give GitHub Project items a
clickable canonical-page link where practical. Repair known navigation drift
in the same change; do not wait for the next audit.

T1 is ARRP's mandatory navigation verification gate because it is the first
tier designed to test framework and project integration. A T1 Navigation
Synchronization Check verifies that the front door exposes topic, subject, and
area-first discovery; affected topic pages point to authoritative proposal
homes without duplicating workflow state; each issue appears once in its
correct area; `areas/README.md` remains correct when an area changes; the
subject index follows its conventions and points to stable records; the GitHub
registry identifies each correct canonical page; and affected local links
resolve. T0 flags an obvious navigation defect for an existing stable record
but does not publish an unadmitted Horizon candidate into the area contents,
subject index, or topic guides. An approved admission, promotion, move, merger,
retirement, or other routing decision triggers immediate bundle
synchronization.

Edition-specific print page locators are generated during two-pass export
rather than maintained in the canonical index.

## ARRP topic-guide configuration

ARRP topic guides live in `topics/`. Their front matter uses:

- `page_type: topic-guide`;
- `status: maintained`;
- `purpose: "Help readers find the ARRP proposals addressing [public subject]."`;
  and
- `print_levels: [public-proposal]`.

The exact reader-facing sequence and labels are:

1. **Overview**;
2. **Applicable Proposals**, with `Public concern | Proposal | How ARRP
   addresses it`;
3. optional **Related Ideas Not Included**, with `Idea | Record | Why it is not
   included`; and
4. **What ARRP Does and Does Not Address**.

An optional **Sources and Updates** note follows when needed. Use `Public
concern`, not `Reader concern`; use `Applicable Proposals` and `Proposal`, not
`Authoritative ARRP route`, `ARRP route`, or `Function`.

ARRP proposal identifiers use the established area prefix and number, such as
`JUD-011` or `ELEC-012`. A routing-table row contains exactly one identifier.
Use `Pending` for an unresolved concern without a stable proposal or candidate
identifier. `Pending` is not a Project lifecycle status, a development promise,
a score, or a priority. Developed identifiers link directly to
`areas/<AREA>/issues/<ISSUE>.md`; identifiers without standalone pages remain
plain text. Area pages do not substitute for issue links in the table, though
an overview may link a broad area by its descriptive title rather than only
its `A-##` designation.

Event- and document-centered guides such as **January 6** and **Project 2025**
may intentionally cross several subject guides because the event or source is
itself the public entry point. ARRP-created crosswalks converted to topic
guides move into `topics/` rather than retaining parallel research copies.
Issue pages own diagnosis and remedies; legislation pages own proposed text;
the Horizon Scan Log and closed records own final adverse dispositions;
`inventory/sources.csv` owns citation administration; and the GitHub Project
owns live status.

Because `research/` is excluded from the GitHub Pages artifact, a public topic
guide links to a retained research crosswalk through its stable GitHub
repository URL rather than a local Markdown link the publication process would
demote.

Use the title and table classes, screen behavior, and print behavior configured
in [`visual-identity.md`](../interfaces/visual-identity.md); do not reproduce
their CSS rules in individual topic pages.
