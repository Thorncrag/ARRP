---
title: "Candidate and Source Intake"
print_levels:
  - full-technical
---

# Candidate and Source Intake

This read-only interface presents five coordinated views:

- **Candidates** are formal open `HOR-###` records presented as decision dossiers. Each dossier derives its lifecycle data from GitHub, its intake history and overlap analysis from the Horizon Scan Log, its sources from the source inventories, and its research links from identifier-matched project work product.
- **Preliminaries** are synthesized possible institutional defects with supporting sources but no `HOR-###` record.
- **Sources** visualizes the complete cited-source bibliography in `inventory/sources.csv`, including each source's structured `Monitoring` designation.
- **Pending** presents the deliberately small routing queue from `inventory/sources-pending.csv`. Every entry identifies plausible competing destinations, explains why ownership is genuinely unclear, and states the source-specific review needed to select its accountable record. Verification, monitoring, an open lawsuit, or an undeveloped destination does not place an otherwise routed source in this tab.
- **Watchers** consolidates monitoring into **Overview**, **Court Cases**, **Presidential Directives**, and **Manual Monitoring** views. It distinguishes why a matter is monitored, what development would trigger review, which deterministic or human process covers it, and the latest known posture.

The dossier is a read-only assembled view, not a new narrative record. GitHub Issues and the ARRP Project remain authoritative for lifecycle and workflow state; the Horizon Scan Log remains authoritative for intake and disposition history; source inventories remain authoritative for retained external sources; and the linked research files remain the project-authored analysis. Correct information at its owning record and rebuild the console rather than editing `catalog-data.js` by hand.

GitHub issue bodies are rendered during the rebuild through the console's dependency-free, allowlisted Markdown renderer. Source HTML is escaped, unsafe link protocols are discarded, and the generated console retains the original Markdown as a plain-text fallback. The browser therefore makes no live Markdown-service request and the console continues to work from `file://`.

One canonical source row may support more than one proposed candidate by naming multiple stable identifiers in `Associated Record IDs`. The builder displays that same row in every applicable dossier; it does not duplicate the row in either source inventory.

The source and pending tabs are streamlined catalog views, not additional manually maintained ledgers. A pending row is incomplete unless it identifies the competing destinations, the reason the project cannot yet choose among them, and the next routing decision. Once ownership is clear, cite the source in the proposal's or candidate's substantive or internal source-development record and move the stable row into `sources.csv`, even if `Reviewed?` remains `No` or the source is still monitored. Irrelevant, political-only, redundant, and no-additional-value material receives a documented disposition and leaves temporary intake.

The Watchers tab does not replace GitHub issue-level monitoring or source-level `Monitoring` designations. GitHub supplies the proposal and formal-candidate issues carrying `needs: monitoring`; the two source catalogs identify changing sources; the Court Cases view identifies which CourtListener-linked records are eligible for mapping when the daily Just Security tracker comparison detects a change; and Manual Monitoring preserves every issue-wide search, tracker exclusion, or unsupported source obligation that automation does not cover.

The Presidential Directives view is generated from `inventory/presidential-directives.csv`, the durable discovery-and-screening registry covering the first Trump administration, the Biden administration, and the second Trump administration. The baseline corpus has already been screened: `Routed` identifies directives cross-referenced to retained ARRP source-development records, while `Screened — no separate action` means the baseline pass selected no distinct project action or retained route. Registry inclusion is not a project finding or source citation. The scheduled, read-only watcher may discover, normalize, deduplicate, and detect changes in official instruments; later LLM-assisted screening decides project relevance, routing, preliminary-candidate creation, deferral, or no project action for new or changed records. It preserves proposed metadata changes as review artifacts and does not alter the canonical registry automatically.

Open [`index.html`](index.html) in the Codex in-app browser. The separate [public interaction service](https://arrp-public-intake.vercel.app/) remains the submission surface. The console contains no promote, defer, reject, agent-invocation, or GitHub-mutation controls; conduct every candidate disposition in Codex under the Horizon Candidate Adjudication Workflow.

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

The generated `catalog-data.js` contains preliminary candidates, enriched formal candidate views, source-catalog views, watcher projections, and the preserved GitHub snapshots needed for later refreshes. The generated enrichment is rebuilt from the Horizon Scan Log, both source inventories, the presidential-directives registry, the GitHub issue registry, watcher configuration, and identifier-linked research. Canonical source records remain in their owning inventories; directive identity and review history remains in its registry; and issue-level monitoring workflow remains on the labeled parent issues and in the Project Monitoring view.

For console-only presentation work that should not rewrite the separately deployed public-input lookup, use:

```sh
python3 scripts/build_horizon_review_console.py --console-only
```
