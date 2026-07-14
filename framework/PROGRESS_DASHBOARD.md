---
title: "Review Ready Progress Dashboard"
print_levels:
  - full-technical
---

# Review Ready Progress Dashboard

The [ARRP Review Ready Progress Dashboard](https://github.com/Thorncrag/ARRP/blob/progress-dashboard/PROGRESS.md) is a derived planning and visualization surface for the project's goal of bringing every eligible proposal to at least **Review Ready** by **December 31, 2026**. It does not replace the [ARRP GitHub Project](https://github.com/users/Thorncrag/projects/2), which remains the authoritative workflow record, or the repository issue pages and audit sidecars, which remain the authoritative substantive and audit records.

## Goal and Eligibility

The corrected July 13, 2026 goal baseline is 23 Review Ready proposals out of 204 eligible proposal issues. A retrospective series begins on June 24 and reconstructs how those 23 proposals reached Review Ready before the dashboard was activated. Eligibility and issue identity are determined from [`inventory/github_issue_registry.csv`](../inventory/github_issue_registry.csv) rows whose `Kind` is `proposal`. Closed merged records remain in the registry as `merged proposal` but are excluded from the active portfolio. The builder matches the proposal identifier in the registry title to the identifier in the Project's built-in `Title` field. `Canonical page` is used only as a fallback when it identifies exactly one Project item.

Governance, horizon, source-review, merged-proposal, and other non-active-proposal registry rows are excluded. Newly admitted proposal rows automatically enlarge the current scope; the dashboard reports the difference from the 204-proposal baseline so that new intake cannot silently distort the goal. A proposal without an unambiguous Project identity remains in the denominator, is treated as not ready, and produces a visible tracking warning instead of disappearing from the goal. This matters because merged, integrated, and undeveloped records may legitimately share a canonical proposal or area page; a shared page must not allow one item's lifecycle fields to be attributed to another.

The official target date is stored in [`.github/progress-dashboard.json`](../.github/progress-dashboard.json). A rolling forecast may move as observed progress changes, but it does not silently replace the official target. Revising the target requires an intentional configuration edit and a short explanation in the commit or accompanying Change Audit entry.

## Review Ready Rule

The dashboard uses the GitHub Project `Status` field as the lifecycle authority. An eligible proposal counts as complete for this goal when its status is one of:

- `Review ready`;
- `Advanced review ready`;
- `Proposal ready`;
- `Publication ready`;
- `Fully validated`;
- `Release candidate`; or
- `Done / Published`.

The score threshold remains 75. The dashboard flags, but does not silently repair, a proposal whose score is at least 75 while its status remains below Review Ready, whose Review Ready status is paired with a lower score, or whose Review Ready status has no Project score with which to verify the threshold. This preserves the Project readback rule and makes tracking drift visible.

## Metrics

The dashboard reports:

- eligible, Review Ready, and remaining proposal counts;
- percent of the eligible portfolio at Review Ready or higher;
- current scope growth or contraction relative to the July 13 baseline;
- completions per week required to meet December 31;
- rolling 28-day and since-baseline completion velocity once at least seven days of history exist;
- the completion date implied by the rolling velocity;
- variance from a linear baseline-to-target path;
- monthly cumulative checkpoints;
- lifecycle-status and score-proximity distributions;
- newly Review Ready and regressed proposals over the rolling comparison period;
- counts of proposals whose Project scores rose or fell, plus net score movement as an early pipeline indicator;
- progress and remaining backlog by ARRP area;
- the highest-scoring proposals that remain below Review Ready; and
- Project status/score consistency warnings.

The completion-date scenario table is exploratory only. It shows the date produced by several sustained weekly paces and does not alter the official goal or Project data.

## Forecast Method

The required weekly pace is:

`remaining eligible proposals / weeks remaining before the official target`.

The rolling pace is the net change in Review Ready count over the configured 28-day window, expressed per week. The initial calculation may use the documented retrospective series rather than waiting seven days after dashboard activation. If fewer than seven days of supported history exist, the dashboard displays `Establishing pace` and withholds a rolling forecast. Once enough history exists, the forecast date is:

`current date + (remaining proposals / rolling weekly pace)`.

The calculation uses net portfolio movement. A proposal that regresses below Review Ready reduces measured progress; newly admitted proposals increase the denominator and required pace. Daily snapshots also retain ready identifiers and scores so the page can distinguish newly completed work, regressions, and pre-completion score movement after two comparable snapshots exist. The retrospective seed retains supported ready identifiers but does not invent historical Project-score snapshots, so score-movement comparisons begin only when comparable automated scores exist. Score movement is an early pipeline indicator, not a measure of hours worked. The forecast is therefore a planning signal, not a promise or a substitute for proposal-level judgment.

## Retrospective Pace Evidence

The checked-in [retrospective seed](../.github/progress-history-seed.json) records the earliest dated score-bearing audit at or above 75 for each proposal in the official 23-proposal baseline. The repository audit sidecar is the attainment-date authority because it states the audit date, score, and Review Ready finding. Git commit history was checked as corroboration, but commit timestamps do not replace an explicit audit date: several audit packages were committed on a different calendar date, and commits may bundle or publish work after the audit itself.

The reconstructed cumulative series begins at zero on June 24, the day before the first qualifying attainment, then records 1 on June 25, 3 on June 27, 16 on June 28, 17 on July 2, 22 on July 4, and 23 on July 9. That result independently reproduces the official July 13 baseline. Each of the 23 attainment records links to its controlling audit-sidecar path in the seed file. If an earlier qualifying audit is later discovered, the seed and this method note should be corrected together with a project-level Change Audit entry.

The seed does not override current GitHub Project data. A retained automated snapshot wins over the seed on the same date, and the current build always wins over both. This lets the dashboard use supported pre-activation history while preserving the Project as the current lifecycle authority.

## Automation and Data Retention

The [`Review Ready progress dashboard`](../.github/workflows/review-ready-dashboard.yml) workflow runs daily, can be run manually, and also runs when its source, configuration, builder, or publisher changes. It:

1. reads only field values, including the built-in `Title`, from the user-owned ARRP Project through GitHub's GraphQL API;
2. joins those fields to proposal identity and links from the checked-out issue registry by proposal identifier, with unique `Canonical page` fallback;
3. loads the checked-in audit-derived retrospective seed;
4. retrieves the previous `data/history.json` snapshot series from the generated dashboard branch;
5. validates and combines the seed, retained history, and current daily snapshot with later sources taking precedence on matching dates;
6. builds `PROGRESS.md`, accessible SVG charts, and machine-readable JSON; and
7. creates or updates the dedicated `progress-dashboard` branch through GitHub's Git data API.

The ordinary `main` push trigger intentionally watches dashboard implementation and configuration files, not every issue or audit file. Therefore, when a scored audit changes an eligible proposal's authoritative Project `Status`, `Score`, or goal eligibility, audit closeout must manually dispatch this workflow after the Project fields have been updated and read back and the audit commit has been pushed. The auditor must wait for a successful run and verify the generated page reflects the changed portfolio state. An authorized multi-issue or successive-tier batch may use one verified final dispatch after all included Project updates and pushes. The daily run is a recovery backstop, not proof that a same-session audit updated the dashboard.

History is retained on the generated branch rather than by opening a tracking issue or committing daily generated data to `main`. If branch history is unavailable or invalid, the builder safely restarts from the documented baseline and current snapshot. The publisher creates the branch as an independent root history, then uses non-forced, fast-forward updates. The generated branch contains only the dashboard, charts, and data; it is not a development branch and should not be edited manually.

The dashboard was initially placed on a generated GitHub branch because the repository was private and GitHub Pages was unavailable under the account configuration then in use. The repository may now be public and have a separate Pages site, but the branch design remains useful because it keeps generated daily history out of `main`. The dashboard branch is repository-visible to deliberate GitHub readers but is excluded from the public Pages artifact, website navigation, search index, and sitemap under [`../website/README.md`](../website/README.md).

## Authentication and Permissions

Because the ARRP Project belongs to the `Thorncrag` user account rather than an organization, fine-grained personal access tokens cannot read it. The workflow therefore requires a classic personal access token stored as the repository Actions secret `ARRP_PROJECT_TOKEN`, with only the `read:project` scope. Do not select `project` or `repo`. The GraphQL query requests Project field values but no repository issue content; the built-in Project `Title` supplies the proposal identifier, while links come from the checked-out registry. The builder never mutates the Project. GitHub's ordinary workflow token separately receives `contents: write` only so the publisher can read retained history and update `progress-dashboard`; it does not write Project fields.

Do not place the token in the repository, dashboard data, workflow text, Project fields, or logs.

Until the secret is configured, workflow runs exit successfully with a visible setup notice and do not create or update the dashboard branch. This permits the implementation to remain on `main` without producing failed scheduled runs or publishing incomplete data.

For first-time activation:

1. create a classic personal access token in GitHub account settings with only `read:project` selected;
2. save it as the `ARRP_PROJECT_TOKEN` repository Actions secret at `Settings` → `Secrets and variables` → `Actions`;
3. open the `Review Ready progress dashboard` workflow under `Actions`; and
4. choose `Run workflow` once to create the initial `progress-dashboard` branch and baseline page.

The daily schedule maintains the page thereafter. If the personal access token expires or is revoked, replace the secret and rerun the workflow; historical snapshots remain on the generated branch.

## Implementation Map

- [`.github/progress-dashboard.json`](../.github/progress-dashboard.json) owns the official baseline, retrospective-history start, target, readiness statuses, field names, and forecast window.
- [`.github/progress-history-seed.json`](../.github/progress-history-seed.json) owns the audit-derived pre-activation attainment evidence and cumulative snapshots.
- [`.github/workflows/review-ready-dashboard.yml`](../.github/workflows/review-ready-dashboard.yml) owns the daily, manual, and source-change automation and its permission boundary.
- [`scripts/build_review_ready_dashboard.py`](../scripts/build_review_ready_dashboard.py) reads and filters Project data, validates history, calculates metrics and forecasts, and generates Markdown, SVG, and JSON output.
- [`scripts/publish_review_ready_dashboard.py`](../scripts/publish_review_ready_dashboard.py) creates the independent generated branch and applies non-forced updates to it.
- [`tests/test_review_ready_dashboard.py`](../tests/test_review_ready_dashboard.py) and its fixtures cover eligibility, status authority, forecast inputs, score/status drift, generated files, and isolated-branch publication behavior.
- `progress-dashboard/PROGRESS.md`, its `assets/`, and its `data/` directory are generated outputs visible only on the dedicated branch; they are intentionally absent from `main`.

## Local Validation

Run:

```bash
python3 -m unittest tests/test_review_ready_dashboard.py
python3 scripts/build_review_ready_dashboard.py \
  --config tests/fixtures/progress-config.json \
  --registry tests/fixtures/progress-registry.csv \
  --input tests/fixtures/progress-project.json \
  --history tests/fixtures/progress-history.json \
  --as-of 2026-07-15 \
  --output /tmp/arrp-review-ready-site
```

The fixture contains one deliberately inconsistent status/score pair so the tracking-warning path remains tested. Local output is a branch-shaped directory whose entry page is `/tmp/arrp-review-ready-site/PROGRESS.md`.

## Governance Effect

This dashboard adds no proposal score, changes no audit result, creates no GitHub issue, assigns no milestone, and adds no new authoritative tracking database. It is a read-only view derived from existing Project fields. Changes to eligibility, the Review Ready rule, the official target, or the interpretation of readiness require a project-level Change Audit because they can materially change the displayed portfolio result.
