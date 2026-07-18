# Candidate Issues and Source Intake Dashboard

This interface is the central view for candidate-issue and source-intake workflow. **Proposed Candidates** lists formal open `HOR-###` records from GitHub and displays authoritative lifecycle fields from the ARRP GitHub Project. **Preliminary Candidates** contains synthesized questions that do not yet have a `HOR-###` identifier or GitHub issue. **Sources** combines every unresolved source-related task regardless of whether it began as an evidence-placement record, a media-supported episode, or planned source ingestion. **Monitoring** preserves matters awaiting a defined external event. **History** preserves completed source-review statistics and closed proposed-candidate records without making historical material look like current work.

Every operational view identifies its purpose, the person or process responsible for the next step, the action that remains, and whether the user must decide anything. Proposed-candidate cards link to the authoritative GitHub issue and, where queue routing exists, open the Sources or Monitoring tab already filtered to the internal Horizon ID. Internal machine-readable source statuses remain in the underlying CSVs, but the dashboard translates them into plain-language work stages. Reference-only sources remain in the canonical source catalog and do not form another queue.

Open [`index.html`](index.html) in the **Codex in-app browser**. Raw source records are reviewed and routed outside the candidate view so a reader is not required to assess hundreds of articles, tracker rows, cases, or agency actions individually. When a preliminary candidate exists, its read-only card states the possible institutional defect, why it may be distinct, existing coverage considered, the best counterargument, unresolved questions, and supporting sources.

The separate [public interaction service](https://arrp-public-intake.vercel.app/) is linked from the dashboard but is not one of its operational views. This keeps submission and page-feedback interaction focused on the contributor while the dashboard remains a read-only catalog of candidate, source, monitoring, and intake-history records.

Unadjudicated refreshes enter the [legal-review catalog](../trump-administration-legal-review-catalog.csv), [media-supported episode intake](../trump-administration-media-review-intake.csv), and [evidence-routing ledger](../trump-administration-evidence-routing.csv). After adjudication, retained sources move to the canonical source registry and either the [existing-record integration queue](../existing-issue-evidence-integration.csv) or [defined-predicate litigation monitor](../trump-administration-litigation-monitoring.csv); resolved raw rows leave the catalog and routing ledger. The [completed batch report](../trump-administration-source-adjudication-report.md) records the July 16, 2026 reconciliation.

## Candidate terminology and disposition

- A **preliminary candidate** is a synthesized unresolved question with no `HOR-###` identifier or GitHub issue.
- A **proposed candidate** is a formal `HOR-###` record awaiting admission, merger, monitoring, retirement, or another documented disposition.
- **Horizon** remains the internal name for the scan, identifier, log, and GitHub workflow; reader-facing interface copy uses the two candidate stages above.

The dashboard is read-only. It contains no promote, defer, reject, reviewer-note, import, or decision-export controls. It does not invoke an agent, assign a `HOR-###` identifier, create or modify GitHub issues, change the GitHub Project, or alter canonical proposal records. Candidate analysis and every formal disposition are conducted in Codex under the ordinary Horizon workflow so the established duplicate, legal, political-failure, ripeness, neutrality, and issue-admission tests are applied before implementation.

After a preliminary candidate is approved and implemented through Codex, the formal `HOR-###` identifier and disposition are recorded in the Horizon Scan Log, GitHub issue, and GitHub Project card; supporting evidence is rerouted to that proposed candidate; and the preliminary row is removed. Rejected or merged rows are likewise removed after their approved disposition is implemented. The active preliminary queue therefore contains unresolved questions only.

Read-only keyboard shortcuts are available when the cursor is not in a form field: `J` or right arrow for next, `K` or left arrow for previous, and `O` to open the first source link.

## Refreshing the Catalog

After rebuilding the underlying legal-review catalog or updating the media intake, regenerate the source-routing ledger and then the dashboard data with:

```sh
python3 scripts/build_horizon_evidence_routing.py
python3 scripts/build_horizon_review_console.py
```

The ordinary build preserves the latest checked-in GitHub snapshot so rebuilding source data does not erase the Proposed Candidates tab. To refresh formal proposed-candidate state and authoritative Project fields, run the builder in the approved host context where the macOS Keychain-backed GitHub CLI credential is available:

```sh
python3 scripts/build_horizon_review_console.py --refresh-github
```

The dashboard displays the GitHub synchronization time so a reader can distinguish current Project data from a stale snapshot. The generated `catalog-data.js` retains stable preliminary-candidate IDs across rebuilds. The same command writes the separate service's minimal `participate/intake-data.js` lookup, which contains only active proposal and formal proposed-candidate identifiers needed for local screening. The canonical CSVs remain the machine-readable source records; GitHub Issues and the Project remain authoritative for formal proposed-candidate workflow status.
