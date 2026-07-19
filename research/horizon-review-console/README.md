---
title: "Candidate Issue Intake"
print_levels:
  - full-technical
---

# Candidate Issue Intake

This read-only interface presents two stages of candidate review:

- **Preliminary candidates** are synthesized possible institutional defects with supporting sources but no `HOR-###` record.
- **Proposed candidates** are formal open `HOR-###` records whose lifecycle status is authoritative in GitHub Issues and the ARRP Project.

Sources are supporting material, not an independent human-review queue. Automated source adjudication must route every retained source to an existing issue or evidence record, a GitHub monitor attached to an existing record, or one clustered preliminary candidate. Irrelevant, political-only, redundant, and no-additional-value material receives a documented disposition and leaves temporary intake. The console therefore displays supporting sources inside preliminary-candidate cards and does not reproduce the source, monitoring, or completed-history ledgers as separate views.

Open [`index.html`](index.html) in the Codex in-app browser. The separate [public interaction service](https://arrp-public-intake.vercel.app/) remains the submission surface. The console contains no promote, defer, reject, agent-invocation, or GitHub-mutation controls; conduct every candidate disposition in Codex under the Horizon Candidate Adjudication Workflow.

## Candidate lifecycle

1. Source screening normalizes and clusters records describing the same episode or institutional weakness.
2. Evidence fitting an existing issue is routed there; external predicates become GitHub monitors attached to their owning issue or candidate.
3. A plausible distinct weakness with no existing owner automatically creates or updates one preliminary candidate, with its supporting sources attached.
4. Human review in Codex promotes, merges, defers, or rejects the candidate.
5. Promotion creates the formal `HOR-###` record and removes the preliminary row; every other final disposition likewise removes the resolved preliminary row.

## Refreshing the data

Rebuild the candidate view and the public-input lookup with:

```sh
python3 scripts/build_horizon_review_console.py
```

The ordinary build preserves the latest checked-in GitHub snapshot. Refresh formal proposed-candidate state in the approved host context where the Keychain-backed GitHub CLI credential is available:

```sh
python3 scripts/build_horizon_review_console.py --refresh-github
```

The generated `catalog-data.js` contains only preliminary candidates, formal proposed candidates, and the preserved GitHub snapshot needed for later refreshes. Canonical source and posture records remain in their CSV homes; monitoring workflow and status remain in issue-linked GitHub monitors and the Project Monitoring view.
