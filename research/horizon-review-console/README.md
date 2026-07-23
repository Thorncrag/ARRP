---
title: "ARRP Project Console"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# ARRP Project Console

This non-authoritative interface centralizes nine coordinated project areas:

- **Overview** is the default whole-project command center. It summarizes human action items, all visible problems, Review Ready progress, the complete current-record maturity pipeline, monitored issues, agents and bots, publication exceptions, and the freshness of each major data projection. Its cards route to complete owning views rather than creating another authority.

- **Progress** is the sole human-facing Review Ready planning view. Summary metrics are followed immediately by the compact six-stage development board; the largely duplicative closest-to-ready list has been removed. Schedule, trajectory, compact area coverage, workflow holds, and issue-level monitoring remain available as supporting sections. Compact area coverage, workflow-hold groups, and monitored-issue headings remain visible for at-a-glance scanning; each list-bearing group or issue is separately collapsible and initially collapsed. The board keeps all stages in one desktop row and uses identifier-only cards with score, live-page, GitHub-issue, and workflow cues. GitHub Project `Development level` remains the maturity authority and `Status` remains the workflow authority. The projected Status vocabulary is `Development`, `Human decision needed`, `Audit needed`, `Audit in progress`, `External review`, `Publication approval`, `Deferred`, and `Blocked`; `Development` describes the workflow category rather than whether someone is actively working at that moment. The checked-in bundle preserves an offline snapshot; when network access is available, the view refreshes from the data-only `project-console-data` feed.

- **Action Items**, immediately after Progress, is the central inbox for proposal and candidate records carrying `Human decision needed`, preliminary-candidate review, unresolved source routing, missing required `Deferred` or `Blocked` explanations, and new or changed watcher records requiring review. Routine issue monitoring is excluded unless a monitoring pass produces a decision or exception requiring attention. Each full-width Action Item container is collapsible, keeps its count visible when closed, and opens the complete owning view without creating a second workflow authority. Locally staged print-level changes remain exclusively in Publication.

- **Candidates** contains formal open `HOR-###` decision dossiers and a separate **Preliminary candidates** view for synthesized possible institutional defects that do not yet have a formal record.
- **Sources** contains the cited bibliography, the deliberately small unresolved-routing queue, and **Source watchers and bots** for Court Cases, Presidential Directives, and URL source checks. Issue-level monitoring is a project workflow concern and therefore appears only in Progress.
- **Integrity** preserves the complete inspectable exception inventory, not just matters requiring human attention. It combines deterministic Integrity findings, actionable source-check exceptions, candidate-dossier completeness gaps, Project tracking and lifecycle warnings, publication metadata exceptions, and operational-readiness conditions. Unrecognized or missing Status values remain visible here for correction instead of being silently translated. Problems within the screen are grouped first by the human, agent, bot, or observation state accountable for the next step, and every owner group shows its complete count. Each problem retains its category, stable reference, affected records, reporting source, responsibility class, state, severity, last-check date, and direct record link. Filters select an accountable owner, severity, or state; only the human subset enters Action Items.
- **Agents & Bots** is generated from the authoritative runbooks in `framework/agents/`. Each persistent worker appears as one full-width expandable record whose closed summary preserves the at-a-glance name, status, type, and cadence. Expanding it shows identity, trigger, execution environment, runtime, operating boundary, and direct runbook and runtime links. The Project Integrity Bot record also shows the authoritative **Checks included** inventory maintained in its runbook.
- **Logs** provides searchable, sortable, groupable, unpaginated views of the canonical Horizon Scan, Agent Audit, Source Monitor, and Change Audit logs. The latest matching record is presented in a dedicated summary, while earlier records appear as compact, full-width lines that expand on demand; the Markdown log remains authoritative. A fifth **Integrity Runs** view presents the Project Integrity Bot’s bounded scheduled, push-triggered, and manual run history directly from the integrity data feed; current unresolved findings remain in Integrity.
- **Publication** contains one complete publication-disposition inventory, edition-level composition and preflight analysis, and a section-by-section document builder with a generated table-of-contents preview. It separately counts and filters pages included in editions, explicitly excluded with reasons, unclassified, or conflicting. It can stage disposition or assembly-order changes and export instructions for Codex; reloading clears those drafts, while page front matter and `framework/print-assembly.json` remain authoritative.

Every view is an assembled projection, not a new narrative or tracking authority. GitHub Issues and the ARRP Project remain authoritative for substantive development level and workflow state; the Horizon Scan Log remains authoritative for intake and disposition history; source inventories remain authoritative for retained external sources; page front matter controls edition inclusion or documented exclusion from print; and linked research files remain the project-authored analysis. Correct information at its owning record and rebuild the console rather than editing `catalog-data.js` by hand.

## Personal layout

**Arrange layout** turns on direct reordering for main tabs, subtabs, major view sections, Action Item cards, Overview sections, and agent/bot cards. Drag a highlighted item, use its arrow controls, or press Alt plus an arrow key while it is focused. **Done arranging** exits the mode. The × on the introductory workspace banner dismisses it across later sessions; **Show intro** in the header restores it. **Reset this view** restores the active screen's sections while preserving other preferences; **Reset all** restores every default, including the introductory banner.

The selected order and each collapsible container's explicit default are device-local interface preferences stored in the browser and persist across Console reloads and later sessions. Every collapsible has a small **Default: open** or **Default: collapsed** button; activating it selects the saved loading state and immediately applies that state. Simply opening or closing a container for temporary inspection does not overwrite its selected default. Dense candidate dossiers, data tables, problem groups, agent and bot runbooks, and Progress supporting sections initially default to collapsed; the development board remains visible. These preferences never change GitHub, repository metadata, authoritative ordering, publication assembly, or another user's Console. Newly added sections remain visible even when an older saved order exists.

The structural rule is: a **compact summary list**, **group of groups**, or **index of expandable records** normally remains visible when collapsing it would hide the available headings. Each **group or record containing a potentially long list or detailed body** is collapsible and initially collapsed, as is a large standalone dataset. An explicitly saved default may override that initial state. This makes the available list scannable at a glance without forcing the underlying data onto the page.

Every tabular view uses sortable column-header buttons. The active column exposes ascending or descending order to assistive technology and shows a direction indicator; each table retains a task-appropriate default order until another header is selected. Presidential directives therefore open with the most recent signed or published date first.

Neutral count badges report each genuine queue or inventory's complete size. The broad **Overview**, **Progress**, and **Publication** navigation tabs do not carry counts because no single number accurately describes those mixed-purpose workspaces. Gold `+N` badges appear only for preliminary intake or genuinely new or changed bot records. Whenever a `+N` badge represents only part of a larger list, the complete owning view must identify those records, place them first, and provide an updated-only filter; a parent badge may instead route to a child view that supplies those features. Queues in which every record awaits review, and findings views already composed entirely of the counted records, do not need a redundant filter. A collapsed dense-data container keeps its current filtered count visible in its summary so the user can understand the result set without opening it. The console checks the public repository's open bot pull requests when it loads so an unresolved case- or directive-watcher update can appear without waiting for a full data rebuild; the checked-in data remains available if that live request fails.

GitHub issue bodies are rendered during the rebuild through the console's dependency-free, allowlisted Markdown renderer. Source HTML is escaped, unsafe link protocols are discarded, and the generated console retains the original Markdown as a plain-text fallback. The browser therefore makes no live Markdown-service request and the console continues to work from `file://`.

One canonical source row may support more than one proposed candidate by naming multiple stable identifiers in `Associated Record IDs`. The builder displays that same row in every applicable dossier; it does not duplicate the row in either source inventory.

The cited and pending source views are streamlined catalog projections, not additional manually maintained ledgers. Every console view that presents source records sorts `Monitoring = Yes` entries first so changing records remain conspicuous; this presentation order does not rewrite either catalog. A pending row is incomplete unless it identifies the competing destinations, the reason the project cannot yet choose among them, and the next routing decision. Once ownership is clear, cite the source in the proposal's or candidate's substantive or internal source-development record and move the stable row into `sources.csv`, even if `Reviewed?` remains `No` or the source is still monitored. Irrelevant, political-only, redundant, and no-additional-value material receives a documented disposition and leaves temporary intake.

The **Source watchers and bots** view does not replace GitHub issue-level monitoring or source-level `Monitoring` designations. GitHub supplies the proposal and formal-candidate issues carrying `needs: monitoring`; this designation is independent of Status because monitoring can continue while the issue's ordinary workflow proceeds. Progress preserves each complete issue-wide review obligation, including active searches, tracker exclusions, new-case discovery, and unsupported sources. The two source catalogs identify changing sources, while the Court Cases view identifies cataloged records covered by the daily Just Security comparison and whether an accepted per-source baseline exists. Routine monitoring is reserved for LLM-assisted review rather than the human Action Items inbox. Material watcher changes appear as owner-assigned pull requests and stable-coded entries in the Source Monitor Log; the console itself remains non-mutating.

The Presidential Directives view is generated from `inventory/presidential-directives.csv`, the durable discovery-and-screening registry covering the first Trump administration, the Biden administration, and the second Trump administration. The baseline corpus has already been screened: `Routed` identifies directives cross-referenced to retained ARRP source-development records, while `Screened — no separate action` means the baseline pass selected no distinct project action or retained route. Registry inclusion is not a project finding or source citation. The scheduled watcher may discover, normalize, deduplicate, and detect changes in official instruments. Material deterministic metadata changes are proposed through an owner-assigned pull request and recorded in the Source Monitor Log; later LLM-assisted screening decides project relevance, routing, preliminary-candidate creation, deferral, or no project action.

Open [`index.html`](index.html) in the Codex in-app browser. The separate [public interaction service](https://arrp-public-intake.vercel.app/) remains the submission surface. The console contains no promote, defer, reject, agent-invocation, or GitHub-mutation controls; its publication controls only produce a local change-list download. Conduct every candidate disposition and canonical metadata edit in Codex under the applicable workflow.

## Publication-disposition change export

Use the × on an existing assignment to stage its removal, select **Add print level…** to stage an additional assignment, or choose **Exclude from print…** and a reason. The summary cards, filters, and inventory immediately reflect the proposed state. **Undo page changes** restores one page; **Reset** clears the full draft. **Export changes** downloads this schema:

```json
{
  "schema_version": 2,
  "purpose": "ARRP publication-disposition metadata changes",
  "exported_at": "2026-07-21T00:00:00.000Z",
  "changes": [
    {
      "path": "areas/AREA/ISSUE.md",
      "title": "Page title",
      "add": ["executive-summary"],
      "remove": ["executive-summary"],
      "print_status": "excluded",
      "print_exclusion_reason": "Internal workflow or tool documentation."
    }
  ]
}
```

Give the exported file to Codex. Before applying it, Codex must confirm that every path, print-level value, disposition, and exclusion reason is valid, preserve unrelated front matter, rebuild the Project Console, and run the ordinary consistency checks. Publication drafts are not saved in local storage and the browser does not modify the repository. Personal Console ordering and disclosure preferences are the sole local-storage exceptions.

Assembly-order exports follow the same rule: they are complete proposed edition structures, not direct edits. Codex validates the page set and section routing before updating `framework/print-assembly.json`.

## Integrity feed

The `Project Integrity Bot` GitHub Action runs the repeatable consistency checker daily at approximately 1:35 a.m. Eastern, after pushes to `main`, and on manual dispatch. It publishes `integrity.json` to the data-only `project-console-data` branch, retaining the current detailed report and up to 30 compact run summaries. Integrity displays the current exception set, while Logs displays the bounded run history. The Project Integrity Bot runbook owns the plain-language check inventory, and the generated integrity report must project that same inventory rather than maintain a second list. Findings do not fail the observation workflow or trigger automatic repairs; execution failures still fail the Action. The console refreshes this feed when online and preserves its latest embedded snapshot for offline use.

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

For a deliberate local preview of a newly built progress feed before the data branch is published, set `ARRP_PROGRESS_SNAPSHOT` to that `progress.json` path for the console rebuild. The override is opt-in so an old local file cannot silently supersede the current data branch in later builds.

The generated `catalog-data.js` contains the page inventory, publication analysis, assembly manifest, offline progress and integrity snapshots, the authoritative agent-and-bot runbook registry, preliminary candidates, enriched formal candidate views, source-catalog views, watcher projections, read-only project-log views, and the preserved GitHub snapshots needed for later refreshes. The generated enrichment is rebuilt from page metadata, `framework/print-assembly.json`, `framework/agents/`, the data-only Project Console feeds, the four canonical project logs, both source inventories, the presidential-directives registry, the GitHub issue registry, watcher configuration, and identifier-linked research. The integrity run history remains a direct projection of the bounded data feed rather than a fifth canonical Markdown log. Canonical logs and source records remain in their owning files; directive identity and review history remains in its registry; and issue-level monitoring workflow remains on the labeled parent issues and in the Project Monitoring view.

For console-only presentation work that should not rewrite the separately deployed public-input lookup, use:

```sh
python3 scripts/build_horizon_review_console.py --console-only
```
