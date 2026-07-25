---
title: "Project Inventory, Area Lists, and Cross-References"
status: active
authority_scope: "Authoritative tracking surfaces, stable issue identity, active and historical area-page lists, issue counts, and nonduplicative cross-references."
load_when: "Creating, moving, renaming, promoting, merging, retiring, or otherwise rerouting an area, issue, candidate, or developed proposal."
dependencies: "../FRAMEWORK.md; ../PROJECT_STRUCTURE.md; ../GITHUB_WORKFLOW.md; ../lifecycle/development-levels.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Project Inventory, Area Lists, and Cross-References

## Authority and Dependencies

This file is the authoritative detailed standard for substantive project inventory and area-page listing conventions. Repository placement belongs to [`../PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md), GitHub fields and mechanics to [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md), and substantive maturity to [`../lifecycle/development-levels.md`](../lifecycle/development-levels.md). Apply [`navigation-synchronization.md`](navigation-synchronization.md) whenever a route changes.

## Load When

Load this file when creating, moving, renaming, promoting, merging, retiring, rejecting, or otherwise rerouting an area, issue, candidate, or developed proposal; changing an area's active issue count; or deciding where historical dispositions and cross-references belong.

## Inventory Files

The authoritative project-tracking surfaces are:

- [ARRP GitHub Project](https://github.com/users/Thorncrag/projects/2) — area, issue, lifecycle-status, milestone, roadmap, workstream, and horizon-queue tracking.
- [`../../inventory/sources.csv`](../../inventory/sources.csv) — external sources affirmatively relied upon to support assertions in substantive ARRP records.
- [`../../inventory/sources-pending.csv`](../../inventory/sources-pending.csv) — temporary routing queue for retained external sources whose accountable project destination is genuinely unclear.

The reader-facing [Subject and Institution Index](../../SUBJECT_INDEX.md) and selective [`../../topics/`](../../topics/) guides are navigation surfaces, not authoritative project trackers or retained inventory CSVs.

## Inventory Rules

1. Each substantive issue should have a stable issue identifier, such as `DOJ-001`.
2. Each issue should have one primary area home.
3. Candidate and horizon issues may remain GitHub Project items until they receive a developed issue page.
4. Retired, merged, integrated, or otherwise adjudicated issues must remain traceable through their closed GitHub issue and the Horizon Scan Log, relevant area page, issue audit-history file, registry, or source record rather than disappearing silently. GitHub issues should not be deleted unless created erroneously. If an adjudicated record has no remaining active work, remove only its card from the active GitHub Project while preserving the closed issue and canonical disposition record.
5. Area `issue_count` front matter counts active records only, including active candidates, deferred or blocked records, developing issues, and developed proposals. It excludes records finally merged, integrated, retired, rejected, or moved elsewhere. Update the count when any such transition occurs.
6. Substantive maturity uses the GitHub Project `Development level` field, while the separate Project `Status` field records the current workflow action or hold; their exact values and mechanics are governed by [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md). Monitoring is independent of both. Every canonical issue page must also carry a nonblank lowercase `status` field in front matter. That issue-page field is substantive page/disposition metadata, not the GitHub Project workflow field; its canonical values are `awaiting-decision`, `awaiting-merits-adjudication`, `blocked`, `candidate`, `deferred`, `developed`, `in-development`, and `retired`. Do not copy Project Status values into that field merely because the words look similar. The Project Integrity Bot reports a missing, blank, or non-standard issue-page `status` rather than inferring one.
7. Every developed proposal issue should carry audit front matter, a visible **Proposal Scoring** summary, and a sibling audit-history file.
8. GitHub Project, source inventory, and page updates should be made in the same change as the substantive project update that requires them.
9. GitHub Project fields, not labels or issue-body metadata, are authoritative for the Project-controlled routing, maturity, workflow, scoring, audit-control, and parent/sub-issue values defined in [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md).
10. Labels should be limited to issue kind or temporary triage that is not already represented by a Project field.
11. The Subject and Institution Index should map plain-language terms and institutional names to stable area and issue homes without duplicating volatile Project fields or creating a second issue taxonomy.
12. A major public subject may receive one canonical topic guide when it spans multiple proposals or areas and explanatory synthesis materially improves navigation. Use the topic's name as commonly known to the public for the visible page title and navigation label. Topic pages are concise, nonauthoritative routing surfaces governed by [`topic-guides.md`](topic-guides.md); they do not own proposal substance, rejection decisions, scores, audits, or workflow state. Convert and move an existing project-authored crosswalk when it becomes the topic guide rather than maintaining parallel versions.

## Area and Issue Index Rules

The root [`../../README.md`](../../README.md) is the public repository front door and must expose topic-guide, subject-index, and area-first discovery prominently. Selective public topic guides live in [`../../topics/`](../../topics/); the ordered project-area index is maintained in [`../../areas/README.md`](../../areas/README.md). Cross-area lookup by subject, department, agency, office, court, acronym, alias, or other institutional body is maintained in one alphabetical sequence in [`../../SUBJECT_INDEX.md`](../../SUBJECT_INDEX.md). Current status, lifecycle, workstream, milestone, and horizon-queue metadata are maintained in the [ARRP GitHub Project](https://github.com/users/Thorncrag/projects/2). Topic, area, and issue pages should carry stable repository links for human navigation; GitHub Project items should carry clickable canonical-page links where practical. Topic guides may explain relationships among linked proposals but must not duplicate volatile Project fields. The subject index should contain only concise, ordered routes and must not become a relationship narrative or a parallel status, score, priority, or audit tracker. Edition-specific print page locators are generated during the two-pass export process and are not maintained manually in the canonical index.

### Area-Page Issue Lists

An area page must present its live work before historical dispositions. Use **Active Issues** for the principal list on every area page and format it as a bulleted list. Each entry uses the form `IDENTIFIER — Proposal title`. When a standalone issue page exists, link the entire bold identifier-and-title label to that page; when no page yet exists, display the entire label as bold plain text. The active list includes unreviewed or source-development candidates as well as developed proposals, because those records still present an unresolved project question. Do not mix finally merged, integrated, retired, rejected, or rerouted records into that list. Do not reproduce volatile lifecycle status, score, priority, audit, or roadmap fields in the area-page index; the GitHub Project remains authoritative for those fields.

When a number was assigned during preliminary review but did not produce a standalone proposal, preserve it below the active list in a compact bulleted **Prior Issue Numbers** list. Introduce the list in reader-facing language explaining that the numbers did not become separate proposals and appear only to explain gaps in the sequence. Each entry begins with the bold record identifier or consolidated identifier range, followed by an em dash and the disposition. Route readers to the current home or final disposition, consolidate records with the same destination, omit obsolete titles and priorities, and do not reproduce the underlying analysis. The closed GitHub issue, registry, Horizon Scan Log, or destination issue remains the detailed record.

A developed proposal that is later merged, retired, or otherwise made inactive is not merely a numbering gap. Preserve the linked bold identifier-and-title label under **Former Developed Proposals**, followed by an em dash, a concise disposition, and the current destination. Do not demote it into the undeveloped-candidate list or delete its page. If an area has no inactive identifiers, omit the empty disposition sections but retain the **Active Issues** heading and list.

## Links to Developed Work

When an issue becomes developed, maintain consistency among:

- the GitHub Project item for the issue;
- the area README entry;
- the Subject and Institution Index entry or entries;
- the GitHub issue registry row;
- the issue page under the relevant area directory;
- any proposed legislation under [`../../legislation/`](../../legislation/); and
- any source-development or research notes that remain relevant.

## Cross-References

Tracking entries should not duplicate developed analysis. Where a related issue is developed elsewhere, cross-reference the primary area or issue instead of repeating the same diagnosis, evidence, or remedy.
