---
title: "Project Update Checklist"
status: active
authority_scope: "Cross-surface synchronization checks required when project records, navigation, sources, proposals, audits, candidates, publication disposition, or tracking change."
load_when: "Closing any repository change that adds, moves, renames, promotes, retires, merges, audits, materially revises, or republishes project records."
dependencies: "../FRAMEWORK.md; ../GITHUB_WORKFLOW.md; ../PROJECT_STRUCTURE.md; ../PRINT_ASSEMBLY.md; ../PUBLIC_RELEASE.md; ../audits/CHANGE_AUDITS.md; ../navigation/navigation-synchronization.md; ../sources/source-catalogs.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Project Update Checklist

## Authority and Dependencies

This file is the authoritative cross-surface completion checklist for project updates. It does not replace the subject-matter authority for any affected record. Apply the governing module for the substantive change, [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md) for GitHub mechanics, [`../PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md) for placement, [`../PRINT_ASSEMBLY.md`](../PRINT_ASSEMBLY.md) and [`../PUBLIC_RELEASE.md`](../PUBLIC_RELEASE.md) for publication, and [`../audits/CHANGE_AUDITS.md`](../audits/CHANGE_AUDITS.md) when the change requires a Change Audit.

## Load When

Load this file at closeout whenever a project change adds, moves, renames, promotes, retires, merges, audits, materially revises, or republishes an area, issue, proposal vehicle, source, candidate, research record, topic guide, or governing rule.

## Project-Update Checklist

When updating the project, check whether the change requires inventory maintenance:

1. If an area is added, renamed, retired, or materially reframed, update the GitHub Project area field/options and the relevant area README/index pages.
2. If an issue is added, renamed, promoted, retired, merged, moved, or given a new development level or workflow status, update the GitHub Project item/fields, the relevant area README contents entry, and the Subject and Institution Index route when affected. When merger, integration, retirement, or adjudication ends all active work, close the issue and remove its Project card after recording the disposition; do not delete the issue.
3. If proposed legislation, proposed constitutional amendment text, proposed enabling legislation, or another proposal vehicle is added, renamed, or removed, update the issue page, legislation index, and GitHub Project canonical-page, development-level, and workflow-status fields as applicable.
4. If an issue is audited, promoted, paused, retired, merged, given legislation, or materially revised, update the issue-page audit front matter, the issue-page **Proposal Scoring** summary, the sibling `ISSUE-ID.audit.md` audit-history file, and the GitHub Project item or fields. Detailed fields such as score basis, rubric version, Required Electoral Environment, Development Priority, Adoption Friction, legislation path, and notes belong in the issue page and audit-history sidecar, not as separate GitHub Project columns. `Score`, `Runs`, `Last audit`, `Next audit`, `Rebaseline status`, and `Change audit needed` are GitHub Project fields because they are operational audit-control flags needed for safe resumption and release triage.
5. If the scoring template, audit schema, rubric version, or audit sidecar structure changes, run a **Change Audit** across all affected issue pages with **Proposal Scoring** sections to keep front matter, visible scoring boxes, audit sidecars, GitHub Project fields, and the governing rule that owns the change synchronized. This prevents drift between human-facing scores and machine-readable metadata without creating another cumulative audit ledger.
6. If a candidate or source-development issue has no concrete draft vehicle, its **Proposed Legislation** section may use a single `Pending development` bullet. This is a page-content placeholder, not a Project Status. Do not treat it as a broken legislation link, but replace it with a linked bullet once a vehicle exists and update the Issue Snapshot vehicle, metadata, inventories, and GitHub Project fields if the issue's development level, workflow status, score, run count, last audit, or next audit changes.
7. If a Horizon Scan audit is run, create or update GitHub Issues for active horizon candidates and add them to the GitHub Project horizon queue. Use [`../logs/HORIZON_SCAN_LOG.md`](../logs/HORIZON_SCAN_LOG.md) for disposition and integration history, not as the active horizon queue. Do not update issue pages, legislation, scores, or source records unless the user separately approves implementation.
8. If an external source is newly relied upon, removed, or used for a materially different proposition, add or update it in [`../../inventory/sources.csv`](../../inventory/sources.csv). If its accountable issue, candidate, or research destination is clear, cite it in that record and place it in `sources.csv` even when verification, development, or monitoring remains incomplete; use `Reviewed?`, Notes, and the monitoring fields to state those limitations. Use [`../../inventory/sources-pending.csv`](../../inventory/sources-pending.csv) only while the destination itself remains genuinely unresolved, and remove the row as soon as routing is resolved.
9. If source review is completed, update `Reviewed?`, `Proposition Supported`, and any notes in the source file that currently owns the record. The project consistency check reports catalog citations it cannot mechanically locate and pending records that appear to have reached prose; reconcile those findings rather than treating a source ID as proof of reader-facing use.
10. Until version 1.0 or an explicit release, export, publication, or print-assembly pass, do not rebuild or commit generated PDF, DOCX, XLSX, or similar export files as part of ordinary proposal, source, audit, or GitHub Project updates. Generated exports may be refreshed only when the user asks for it, the export is the deliverable, export tooling is being tested, or the work is expressly part of release/publication preparation.
11. If issue counts change, update the area README front matter and any corresponding GitHub Project area metadata.
12. If a Markdown page is created, moved, promoted, retired, or repurposed, update its publication disposition—one or more `print_levels`, or `print_status: excluded` with a reason—under [`../PRINT_ASSEMBLY.md`](../PRINT_ASSEMBLY.md).
13. If a roadmap, backlog, or to-do item is added or revised, update the GitHub Project issue/milestone/roadmap item; framework files should link to GitHub rather than maintaining separate task lists.
14. If a roadmap, governance, audit, release, or publication task has meaningful child tasks, use GitHub native sub-issues rather than Markdown-only checklist substitutes.
15. If proposal development, horizon integration, or a material source update introduces a department, agency, office, court, other institutional body, acronym, alias, or plain-language subject that would help readers find the relevant work, add or revise the corresponding route under the canonical [Indexing and Contents Synchronization Standard](../../SUBJECT_INDEX.md#indexing-and-contents-synchronization-standard). If the preferred destination changes, update the canonical entry, all affected **See** references, and the affected contents page in the same change.
16. If a change creates, moves, retitles, or materially reroutes a public topic guide, update the guide, root discovery text, Subject and Institution Index, site navigation and allowlist, GitHub registry and Project canonical-page field when applicable, print assignment, and every affected internal reference in the same navigation-synchronization pass.
