# Horizon Intake Review Console

This internal interface supports user review of synthesized preliminary institutional questions before any question is assigned a Horizon ID. Raw source records are reviewed and routed outside this interface so the user is not required to adjudicate hundreds of articles, tracker rows, cases, or agency actions individually.

Open [`index.html`](index.html) in the **Codex in-app browser**. That is the console's intended review environment. The console contains only preliminary candidates that may warrant promotion into the formal Horizon queue. Each card states the possible institutional defect, why it may be distinct, existing coverage considered, the best counterargument, unresolved questions, and supporting sources.

The underlying evidence remains in the [legal-review catalog](../trump-administration-legal-review-catalog.csv), [media-supported episode intake](../trump-administration-media-review-intake.csv), and [evidence-routing ledger](../trump-administration-evidence-routing.csv). The routing ledger preserves duplicate source records when they add corroboration, litigation posture, a primary instrument, or other evidentiary value. It separately identifies material likely to support an existing proposal and records still requiring agent review.

## Decisions

- **Yes** approves promotion of the synthesized question into a formal `HOR-###` candidate.
- **No** declines Horizon promotion. Supporting evidence may still be routed to an existing proposal or retained as source development.
- **Defer** keeps the preliminary candidate available for additional legal, factual, duplicate, or litigation-posture review.

The local console does not itself assign a `HOR-###` identifier, create or modify GitHub issues, change the GitHub Project, or alter canonical proposal records. Exported decisions must be applied through the ordinary Horizon workflow. A promoted Horizon candidate still requires formal duplicate and issue-admission analysis before it may become an area-specific proposal.

After an exported **Yes** decision is implemented, the preliminary-candidate ledger records the resulting `HOR-###` identifier and marks the record `promoted-to-horizon`. The console builder omits promoted records from the active review queue; their continuing workflow moves to the Horizon Scan Log, GitHub issue, and GitHub Project card.

Decisions and notes save automatically in the Codex browser's local storage under the version-two candidate-review schema. They are not written back to the repository automatically and may be lost if that browser's stored site data is cleared. Earlier raw-record decisions are deliberately not reinterpreted because a former **Yes** meant only “retain for synthesis,” while a current **Yes** means “promote to Horizon.” Use **Export decisions** regularly for a restorable JSON backup and **Export CSV** for a tabular review file. A JSON export can be re-imported into the console on the same or another computer.

Keyboard shortcuts are available when the cursor is not in a form field: `Y` for Yes, `N` for No, `D` for Defer, `J` or right arrow for next, `K` or left arrow for previous, and `O` to open the first source link.

## Refreshing the Catalog

After rebuilding the underlying legal-review catalog or updating the media intake, regenerate the source-routing ledger and then the candidate console data with:

```sh
python3 scripts/build_horizon_evidence_routing.py
python3 scripts/build_horizon_review_console.py
```

The generated `catalog-data.js` retains the stable preliminary candidate IDs used to associate saved or imported decisions with the refreshed candidate queue. The source-routing ledger remains separate from the console bundle.
