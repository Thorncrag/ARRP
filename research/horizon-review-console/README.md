# Horizon Intake Review Console

This internal interface supports manual review of the Trump-administration legal-action catalog before any record is assigned a Horizon ID or admitted as an ARRP issue.

Open [`index.html`](index.html) in the **Codex in-app browser**. That is the console's intended review environment. The console begins with the six preliminary issue candidates, then provides separate queues for media-supported episodes, priority dispositions, open-litigation monitoring records, and the full source catalog.

The media queue is episode-based rather than article-based. Every included episode has been reported by at least two independent reliable news organizations. A primary record—such as an executive order, proclamation, memorandum, demand letter, court filing, official report, or corporate filing—is linked when located. The record also states when the primary instrument has only been described in reporting or still needs retrieval.

## Decisions

- **Yes** advances a record for a later, formal Horizon synthesis and adjudication pass.
- **No** records that the item should not advance from this intake.
- **Defer** preserves the item for additional legal, factual, duplicate, or litigation-posture review.

These selections are screening recommendations only. The console does not assign `HOR-###` identifiers, create or modify GitHub issues, change the GitHub Project, or alter canonical proposal records.

Decisions and notes save automatically in the Codex browser's local storage. They are not written back to the repository automatically and may be lost if that browser's stored site data is cleared. Use **Export decisions** regularly for a restorable JSON backup and **Export CSV** for a tabular review file. A JSON export can be re-imported into the console on the same or another computer.

Keyboard shortcuts are available when the cursor is not in a form field: `Y` for Yes, `N` for No, `D` for Defer, `J` or right arrow for next, `K` or left arrow for previous, and `O` to open the first source link.

## Refreshing the Catalog

After rebuilding the underlying legal-review catalog or updating the media intake, regenerate the console data with:

```sh
python3 scripts/build_horizon_review_console.py
```

The generated `catalog-data.js` retains the source record IDs used to associate saved or imported decisions with the refreshed catalog.
