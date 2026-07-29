---
title: "ARRP Project Update Workflow"
status: active
authority_scope: "Cross-surface synchronization checks required when project records, navigation, sources, proposals, audits, candidates, publication disposition, or tracking change."
load_when: "Closing any repository change that adds, moves, renames, promotes, retires, merges, audits, materially revises, or republishes project records."
dependencies:
  - "../../FRAMEWORK.md"
  - "../github/workflow.md"
  - "../../PROJECT_STRUCTURE.md"
  - "../publication/print-assembly.md"
  - "../publication/first-release.md"
  - "../../standards/audits/change-audits.md"
  - "navigation-sync.md"
  - "source-adjudication.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# ARRP Project Update Workflow

## Authority and Dependencies

This file is the authoritative cross-surface completion checklist for project
updates. It does not replace the subject-matter authority for any affected
record. Apply the governing module for the substantive change,
[GitHub Workflow](../github/workflow.md) for GitHub mechanics,
[Repository Structure](../../PROJECT_STRUCTURE.md) for placement,
[ARRP Navigation Synchronization](navigation-sync.md) for exact reader-route
maintenance, [ARRP Source Catalog and Adjudication](source-adjudication.md) for
source ownership and fields, [ARRP Print Assembly](../publication/print-assembly.md)
and [ARRP First Public Release](../publication/first-release.md) for
publication, and [Change Audits](../../standards/audits/change-audits.md) when
the change requires a Change Audit.

## Load When

Load this file at closeout whenever a project change adds, moves, renames, promotes, retires, merges, audits, materially revises, or republishes an area, issue, proposal vehicle, source, candidate, research record, topic guide, or governing rule. For a material governing decision, also load the [Governance Change Recording](governance-change-recording.md) workflow.

## Project-Update Checklist

When updating the project, check whether the change requires inventory maintenance:

1. If an area is added, renamed, retired, or materially reframed, update the GitHub Project area field/options and the relevant area README/index pages.
2. If an issue is added, renamed, promoted, retired, merged, moved, or given a new development level or workflow status, update the GitHub Project item/fields, the relevant area README contents entry, and the Subject and Institution Index route when affected. When merger, integration, retirement, or adjudication ends all active work, close the issue and remove its Project card after recording the disposition; do not delete the issue.
3. If proposed legislation, proposed constitutional amendment text, proposed enabling legislation, or another proposal vehicle is added, renamed, or removed, update the issue page, legislation index, and GitHub Project canonical-page, development-level, and workflow-status fields as applicable.
4. If an issue is audited, promoted, paused, retired, merged, given legislation, or materially revised, update the issue-page audit front matter, the issue-page **Proposal Scoring** summary, the sibling `ISSUE-ID.audit.md` audit-history file, and the GitHub Project item or fields. Detailed fields such as score basis, rubric version, Required Electoral Environment, Development Priority, Adoption Friction, legislation path, and notes belong in the issue page and audit-history sidecar, not as separate GitHub Project columns. `Score`, `Runs`, `Last audit`, `Next audit`, `Rebaseline status`, and `Change audit needed` are GitHub Project fields because they are operational audit-control flags needed for safe resumption and release triage.
5. If the scoring template, audit schema, rubric version, or audit sidecar structure changes, run a **Change Audit** across all affected issue pages with **Proposal Scoring** sections to keep front matter, visible scoring boxes, audit sidecars, GitHub Project fields, and the governing rule that owns the change synchronized. This prevents drift between human-facing scores and machine-readable metadata without creating another cumulative audit ledger.
6. If a candidate or source-development issue has no concrete draft vehicle, its **Proposed Legislation** section may use a single `Pending development` bullet. This is a page-content placeholder, not a Project Status. Do not treat it as a broken legislation link, but replace it with a linked bullet once a vehicle exists and update the Issue Snapshot vehicle, metadata, inventories, and GitHub Project fields if the issue's development level, workflow status, score, run count, last audit, or next audit changes.
7. If a Horizon Scan audit is run, create or update GitHub Issues for active horizon candidates and add them to the GitHub Project horizon queue. Use the [`Horizon Scan Log`](../../records/candidates/horizon-scan-log.md) for disposition and integration history, not as the active horizon queue. Do not update issue pages, legislation, scores, or source records unless the user separately approves implementation.
8. If an external source is newly relied upon, removed, or used for a
   materially different proposition, apply the exact catalog ownership,
   field, path, and monitoring mappings in
   [ARRP Source Catalog and Adjudication](source-adjudication.md).
9. If source review is completed, reconcile the owning catalog and substantive
   destination under that same workflow. Treat consistency findings as
   reconciliation obligations rather than treating a source identifier as
   proof of reader-facing use.
10. Until version 1.0 or an explicit release, export, publication, or print-assembly pass, do not rebuild or commit generated PDF, DOCX, XLSX, or similar export files as part of ordinary proposal, source, audit, or GitHub Project updates. Generated exports may be refreshed only when the user asks for it, the export is the deliverable, export tooling is being tested, or the work is expressly part of release/publication preparation.
11. If issue counts change, update the area README front matter and any corresponding GitHub Project area metadata.
12. If a Markdown page is created, moved, promoted, retired, or repurposed, update its publication disposition—one or more `print_levels`, or `print_status: excluded` with a reason—under the [`ARRP Print Assembly`](../publication/print-assembly.md).
13. If a roadmap, backlog, or to-do item is added or revised, update the GitHub Project issue/milestone/roadmap item; framework files should link to GitHub rather than maintaining separate task lists.
14. If a roadmap, governance, audit, release, or publication task has meaningful child tasks, use GitHub native sub-issues rather than Markdown-only checklist substitutes.
15. If proposal development, horizon integration, or a material source update introduces a department, agency, office, court, other institutional body, acronym, alias, or plain-language subject that would help readers find the relevant work, add or revise the corresponding route under the canonical [Indexing and Contents Synchronization Standard](../../../SUBJECT_INDEX.md#indexing-and-contents-synchronization-standard). If the preferred destination changes, update the canonical entry, all affected **See** references, and the affected contents page in the same change.
16. If a change creates, moves, retitles, or materially reroutes a public topic guide, update the guide, root discovery text, Subject and Institution Index, site navigation and allowlist, GitHub registry and Project canonical-page field when applicable, print assignment, and every affected internal reference in the same navigation-synchronization pass.
17. If a material governance boundary is adopted, revised, superseded, retired, or proposed for canonical adoption, reconcile the public-safe Governance Change Log and its registry with the governing authority, exact Git evidence, validation, supersession, policy-adoption posture, live-activation posture, and any required owner-local supplement. Do not use the governance record to replace a Change Audit, issue audit history, or protected record.

## Audit Closeout and Preservation

When an audit changes repository records, preserve completed work promptly,
including interrupted work that has already made useful changes. Where the
repository and remote are available, create the necessary noninteractive
commit or commits and push them through the configured GitHub workflow without
asking another process question, unless the working environment or governing
method requires approval. If a push cannot be completed, preserve a local
commit where possible, record the failure, and notify the user immediately.

Before treating an audited issue as complete:

1. update its issue-page front matter, visible **Proposal Scoring** summary,
   sibling audit-history file, and every affected GitHub issue or Project field;
2. read back the GitHub issue wrapper and Project row and confirm that all
   in-scope workflow fields match the repository;
3. keep the GitHub wrapper concise and link it to the canonical issue page,
   audit-history sidecar, proposal vehicle when one exists, and area page; do
   not duplicate detailed audit-history entries as issue comments unless the
   user requests that comment;
4. complete local validation, or document exactly which checks were skipped;
5. confirm the working tree is clean or intentionally described, the commit
   exists, the push was attempted when a remote is available, and every
   completion-critical hosted update and readback succeeded; and
6. leave
   [`framework/records/handoffs/current-task.md`](../../records/handoffs/current-task.md)
   `Paused` or `Blocked` with the exact remaining synchronization step when an
   approval, authentication, network, remote, workflow, or publication failure
   prevents completion. Do not mark it `Inactive` while a completion-critical
   step remains.

If local validation, formatting, pre-commit hooks, or optional checks cannot be
completed during an interruption, they may be bypassed only to preserve the
work. Record every skipped check. This preservation exception does not bypass
source verification, citation requirements, scoring rules, unresolved-claim
treatment, selected-tier scope, or another substantive safeguard.

## Project Console Progress Refresh

If an audit changes an eligible proposal's GitHub Project `Development level`,
`Status`, `Score`, or goal eligibility, first push and read back the
authoritative repository and Project changes. Then manually dispatch the
local Project Console Progress stage, wait for completion, and verify that its
checked-in Console projection reflects the complete portfolio,
development-board, workflow-status, score, and area effects. The nightly
schedule is a recovery backstop, not a substitute for same-session
verification. An expressly authorized multi-issue or successive-tier batch may
use one final refresh after all included Project changes and pushes, provided
the readback covers the complete batch.
