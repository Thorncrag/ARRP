---
title: "ARRP Project Console"
print_levels:
  - full-technical
---

# ARRP Project Console

This non-authoritative interface centralizes five coordinated project areas:

- **Progress** is the sole human-facing Review Ready planning view. It shows the current goal, trajectory graph, pace, forecast, area coverage, and closest-to-ready backlog while leaving GitHub Project fields authoritative. The checked-in bundle preserves an offline snapshot; when network access is available, the view refreshes from the data-only `project-console-data` feed.

- **Action Items**, immediately after Progress, is the central inbox for non-deferred candidate decisions, preliminary-candidate review, unresolved source routing, issue-level manual monitoring, new or changed watcher records, and locally staged print-level edits. Every card opens the complete owning view; the inbox does not create a second workflow authority.

- **Candidates** contains formal open `HOR-###` decision dossiers and a separate **Preliminary candidates** view for synthesized possible institutional defects that do not yet have a formal record.
- **Sources** contains the cited bibliography, the deliberately small unresolved-routing queue, and **Watchers and bots**. The watcher workspace opens directly to Court Cases and also includes Presidential Directives and Manual Monitoring; the duplicative overview screen is omitted.
- **Publication** begins with one complete, sortable, unpaginated inventory of every compiled-edition Markdown page and its `print_levels` assignments. Each row can stage an added level or an × removal. The resulting JSON export is an instruction list for Codex to validate and apply; reloading the console clears the staged changes, and page front matter remains authoritative throughout.

Every view is an assembled projection, not a new narrative or tracking authority. GitHub Issues and the ARRP Project remain authoritative for lifecycle and workflow state; the Horizon Scan Log remains authoritative for intake and disposition history; source inventories remain authoritative for retained external sources; page front matter controls print assignment; and linked research files remain the project-authored analysis. Correct information at its owning record and rebuild the console rather than editing `catalog-data.js` by hand.

Every tabular view uses sortable column-header buttons. The active column exposes ascending or descending order to assistive technology and shows a direction indicator; each table retains a task-appropriate default order until another header is selected. Presidential directives therefore open with the most recent signed or published date first.

Neutral count badges report each queue's complete size. Gold `+N` badges appear only for preliminary intake or genuinely new or changed bot records. The console checks the public repository's open bot pull requests when it loads so an unresolved case- or directive-watcher update can appear without waiting for a full data rebuild; the checked-in data remains available if that live request fails.

GitHub issue bodies are rendered during the rebuild through the console's dependency-free, allowlisted Markdown renderer. Source HTML is escaped, unsafe link protocols are discarded, and the generated console retains the original Markdown as a plain-text fallback. The browser therefore makes no live Markdown-service request and the console continues to work from `file://`.

One canonical source row may support more than one proposed candidate by naming multiple stable identifiers in `Associated Record IDs`. The builder displays that same row in every applicable dossier; it does not duplicate the row in either source inventory.

The cited and pending source views are streamlined catalog projections, not additional manually maintained ledgers. Every console view that presents source records sorts `Monitoring = Yes` entries first so changing records remain conspicuous; this presentation order does not rewrite either catalog. A pending row is incomplete unless it identifies the competing destinations, the reason the project cannot yet choose among them, and the next routing decision. Once ownership is clear, cite the source in the proposal's or candidate's substantive or internal source-development record and move the stable row into `sources.csv`, even if `Reviewed?` remains `No` or the source is still monitored. Irrelevant, political-only, redundant, and no-additional-value material receives a documented disposition and leaves temporary intake.

The **Watchers and bots** source view does not replace GitHub issue-level monitoring or source-level `Monitoring` designations. GitHub supplies the proposal and formal-candidate issues carrying `needs: monitoring`; the two source catalogs identify changing sources; the Court Cases view identifies cataloged records covered by the daily Just Security comparison and whether an accepted per-source baseline exists; and Manual Monitoring preserves every issue-wide search, tracker exclusion, new-case discovery, or unsupported source obligation that automation does not cover. Material watcher changes appear as owner-assigned pull requests and stable-coded entries in the Source Monitor Log; the console itself remains non-mutating.

The Presidential Directives view is generated from `inventory/presidential-directives.csv`, the durable discovery-and-screening registry covering the first Trump administration, the Biden administration, and the second Trump administration. The baseline corpus has already been screened: `Routed` identifies directives cross-referenced to retained ARRP source-development records, while `Screened — no separate action` means the baseline pass selected no distinct project action or retained route. Registry inclusion is not a project finding or source citation. The scheduled watcher may discover, normalize, deduplicate, and detect changes in official instruments. Material deterministic metadata changes are proposed through an owner-assigned pull request and recorded in the Source Monitor Log; later LLM-assisted screening decides project relevance, routing, preliminary-candidate creation, deferral, or no project action.

Open [`index.html`](index.html) in the Codex in-app browser. The separate [public interaction service](https://arrp-public-intake.vercel.app/) remains the submission surface. The console contains no promote, defer, reject, agent-invocation, or GitHub-mutation controls; its publication controls only produce a local change-list download. Conduct every candidate disposition and canonical metadata edit in Codex under the applicable workflow.

## Print-level change export

Use the × on an existing assignment to stage its removal, or select **Add print level…** to stage an additional assignment. The summary cards, filters, and inventory immediately reflect the proposed state. **Undo page changes** restores one page; **Reset** clears the full draft. **Export changes** downloads this schema:

```json
{
  "schema_version": 1,
  "purpose": "ARRP print-level metadata changes",
  "exported_at": "2026-07-21T00:00:00.000Z",
  "changes": [
    {
      "path": "areas/AREA/ISSUE.md",
      "title": "Page title",
      "add": ["executive-summary"],
      "remove": ["full-technical"]
    }
  ]
}
```

Give the exported file to Codex. Before applying it, Codex must confirm that every path and print-level value is valid, preserve unrelated front matter, rebuild the Project Console, and run the ordinary consistency checks. The browser does not save drafts in local storage or modify the repository.

## Candidate lifecycle

1. Source screening normalizes and clusters records describing the same episode or institutional weakness.
2. Evidence fitting an existing issue is routed there; external predicates become GitHub monitors attached to their owning issue or candidate.
3. A plausible distinct weakness with no existing owner automatically creates or updates one preliminary candidate, with its supporting sources attached.
4. Human review in Codex promotes, merges, defers, or rejects the candidate.
5. Promotion creates the formal `HOR-###` record and removes the preliminary row; every other final disposition likewise removes the resolved preliminary row.

## Refreshing the data

Rebuild all candidate and source views plus the public-input lookup with:

```sh
python3 scripts/build_horizon_review_console.py
```

The ordinary build preserves the latest checked-in GitHub snapshot. Refresh formal proposed-candidate state in the approved host context where the Keychain-backed GitHub CLI credential is available:

```sh
python3 scripts/build_horizon_review_console.py --refresh-github
```

The generated `catalog-data.js` contains the print-level page inventory, an offline progress snapshot, preliminary candidates, enriched formal candidate views, source-catalog views, watcher projections, and the preserved GitHub snapshots needed for later refreshes. The generated enrichment is rebuilt from page metadata, the data-only Project Console progress feed, the Horizon Scan Log, both source inventories, the presidential-directives registry, the GitHub issue registry, watcher configuration, and identifier-linked research. Canonical source records remain in their owning inventories; directive identity and review history remains in its registry; and issue-level monitoring workflow remains on the labeled parent issues and in the Project Monitoring view.

For console-only presentation work that should not rewrite the separately deployed public-input lookup, use:

```sh
python3 scripts/build_horizon_review_console.py --console-only
```
