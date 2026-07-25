---
title: "Source Catalogs and Monitoring Metadata"
status: active
authority_scope: "Admission to sources.csv, temporary use of sources-pending.csv, stable source identity, review state, monitoring fields, and the presidential-directive registry's relationship to the catalogs."
load_when: "Adding, reviewing, rerouting, monitoring, removing, or materially repurposing an external source or editing a cited record whose source locator may change."
dependencies: "../FRAMEWORK.md; ../evidence/annotation-and-source-standards.md; ../PROJECT_STRUCTURE.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Source Catalogs and Monitoring Metadata

## Authority and Dependencies

This file is the authoritative detailed rule for ARRP's two external-source catalogs and their monitoring metadata. Claim support belongs to [`../evidence/annotation-and-source-standards.md`](../evidence/annotation-and-source-standards.md), and physical repository placement belongs to [`../PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md). The presidential-directive discovery registry is governed by [`presidential-directives.md`](presidential-directives.md) and is not a third source catalog.

## Load When

Load this file when adding, reviewing, rerouting, monitoring, removing, or materially repurposing an external source; deciding whether a source belongs in `sources.csv` or `sources-pending.csv`; initializing or accepting a monitoring baseline; or editing a cited record whose catalog locator may change.

## Source Inventory Rules

`sources.csv` is the project-wide registry of distinct external sources affirmatively relied upon to support a factual, legal, historical, procedural, monitoring, or analytical assertion in a project-authored substantive record. The supporting record may be reader-facing prose, an internal source-development record, a maintained research dataset, a formal candidate, a structured preliminary candidate, or an accountable parent GitHub issue. A structured reference counts only when it cites the stable `SRC-####` identifier, states the action or proposition supported or under review, and identifies an accountable issue, candidate, or research record. A source may be cited provisionally with `Reviewed?` set to `No`; that status limits the claim and identifies unfinished verification but does not make the source unrouted. Mere topical similarity, raw-intake inclusion, bookmarking, or consultation without a selected owner does not qualify a source for `sources.csv`; retain it in `sources-pending.csv` only while a real choice among destinations remains unresolved, or remove it after documented adjudication.

Repository placement follows the authorship, ownership, and publication rules in [`../PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md). Placement does not change merely because a work product has been integrated into an issue. The source inventory remains the authoritative relied-upon source registry whether or not an external source is retained locally; reliance does not require downloading or committing a local copy.

Source rows may be captured before full verification. Use the `Reviewed?` field to distinguish a captured source from a source that has been checked against the proposition it is being used to support.

Use the `Monitoring` field in both source catalogs to identify whether the source itself is expected to change and warrants recurring review. Use `Yes` for a live docket, rolling agency page, maintained official dataset, or comparable changing record; use `No` for an ordinarily static opinion, filing, report, news article, or archived instrument. A row whose retained object is an open court case or live case-level docket must use `Monitoring = Yes`; an opinion, order, complaint, brief, or other fixed document remains `No` merely because the underlying litigation is open unless the row is deliberately serving as the case-level monitoring record. Every `Yes` row must state a concise `Monitoring Rationale` identifying the development or change being watched and a human-readable `Monitoring Group` that clusters sources concerning the same case family, directive, investigation, disclosure, or factual episode. `Monitoring Baseline` stores only the deterministic watcher fingerprint last accepted for that source; leave it blank when no validated watcher covers the row. A deliberate initialization pass may populate a blank baseline without treating the existing state as a change, but an ordinary scheduled run must not silently accept a missing baseline. These fields describe source-level monitoring and must not otherwise be inferred from source type alone. This designation is independent of issue-level monitoring: it does not apply `needs: monitoring` to an issue, and a project-wide pass for a labeled issue still checks all associated sources and searches for new developments.

[`../../inventory/presidential-directives.csv`](../../inventory/presidential-directives.csv) is a distinct discovery-and-screening registry, not a third source catalog. It records the covered universe of presidential directives, stable document identity, deterministic change metadata, and the project's screening disposition so later scans do not rediscover an already screened instrument. The completed baseline uses `Routed` for directives cross-referenced to retained ARRP source-development records and `Screened — no separate action` when the screening selected no distinct project action or retained route. Later deterministic scans use `New since baseline screening` or `Changed since screening` only to identify records requiring another substantive pass. A registry row does not establish evidentiary reliance. When ARRP relies on a directive or clearly routes it as a source-development lead, create or cross-reference its one bibliographic record in `sources.csv` and store the resulting stable `SRC-####` identifier in the directive registry. Use `sources-pending.csv` only when the directive's accountable destination remains genuinely unclear.

When a cited issue page, legislation file, or framework file is edited, refresh any affected `Project Location` line references in [`../../inventory/sources.csv`](../../inventory/sources.csv). Exact line references are useful for rapid verification, but they can become stale after otherwise unrelated edits.

## Stable Identity and Queue Boundary

Large discovery catalogs, routing ledgers, preliminary-candidate tables, generated worklists, and similar intake files are temporary work queues rather than permanent source registries. Every retained external source has one inventory home: [`../../inventory/sources.csv`](../../inventory/sources.csv) once an accountable project record is clear and actually cites the source, or [`../../inventory/sources-pending.csv`](../../inventory/sources-pending.csv) only while the project cannot confidently choose that destination. Verification status, issue-development status, an open lawsuit, a future monitoring event, or the absence of a completed reader-facing proposal does not independently justify pending placement. Git history preserves superseded queue states; the current repository tree should not retain resolved intake rows, promotion tombstones, or duplicate bibliographic records merely to show that a record once existed.

Source identifiers are permanent and must never be reassigned or renumbered. A documented removal may therefore leave a gap in the numeric sequence; allocate new identifiers above the highest identifier already used rather than filling a gap.
