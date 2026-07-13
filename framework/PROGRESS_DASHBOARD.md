---
title: "Review Ready Progress Dashboard"
print_levels:
  - full-technical
---

# Review Ready Progress Dashboard

The [ARRP Review Ready Progress Dashboard](https://github.com/Thorncrag/ARRP/blob/progress-dashboard/PROGRESS.md) is a derived planning and visualization surface for the project's goal of bringing every eligible proposal to at least **Review Ready** by **December 31, 2026**. It does not replace the [ARRP GitHub Project](https://github.com/users/Thorncrag/projects/2), which remains the authoritative workflow record, or the repository issue pages and audit sidecars, which remain the authoritative substantive and audit records.

## Goal and Eligibility

The initial July 13, 2026 baseline is 23 Review Ready proposals out of 206 eligible proposal issues. Eligibility is determined from GitHub Project items that:

1. are GitHub Issues in `Thorncrag/ARRP`; and
2. carry the `kind: proposal` label.

Governance, horizon, source-review, and other non-proposal issues are excluded. Newly admitted `kind: proposal` issues automatically enlarge the current scope; the dashboard reports the difference from the 206-proposal baseline so that new intake cannot silently distort the goal.

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

The score threshold remains 75. The dashboard flags, but does not silently repair, a proposal whose score is at least 75 while its status remains below Review Ready, or whose Review Ready status is paired with a lower score. This preserves the Project readback rule and makes tracking drift visible.

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

The rolling pace is the net change in Review Ready count over the configured 28-day window, expressed per week. Until seven days of snapshots exist, the dashboard displays `Establishing pace` and withholds a rolling forecast. Once enough history exists, the forecast date is:

`current date + (remaining proposals / rolling weekly pace)`.

The calculation uses net portfolio movement. A proposal that regresses below Review Ready reduces measured progress; newly admitted proposals increase the denominator and required pace. Daily snapshots also retain ready identifiers and scores so the page can distinguish newly completed work, regressions, and pre-completion score movement after two comparable snapshots exist. Score movement is an early pipeline indicator, not a measure of hours worked. The forecast is therefore a planning signal, not a promise or a substitute for proposal-level judgment.

## Automation and Data Retention

The [`Review Ready progress dashboard`](../.github/workflows/review-ready-dashboard.yml) workflow runs daily, can be run manually, and also runs when its source, configuration, builder, or publisher changes. It:

1. reads the user-owned ARRP Project through GitHub's GraphQL API;
2. filters and calculates the private proposal metrics;
3. retrieves the previous `data/history.json` snapshot series from the generated dashboard branch;
4. validates and appends the current daily snapshot;
5. builds `PROGRESS.md`, accessible SVG charts, and machine-readable JSON; and
6. creates or updates the dedicated `progress-dashboard` branch through GitHub's Git data API.

History is retained on the generated branch rather than by opening a tracking issue or committing daily generated data to `main`. If branch history is unavailable or invalid, the builder safely restarts from the documented baseline and current snapshot. The publisher creates the branch as an independent root history, then uses non-forced, fast-forward updates. The generated branch contains only the dashboard, charts, and data; it is not a development branch and should not be edited manually.

The repository is private and GitHub Pages is unavailable under the current account configuration. A generated GitHub branch therefore provides a stable, private, GitHub-rendered page without making the repository public, requiring a plan upgrade, or adding generated daily commits to `main`.

## Authentication and Permissions

Because the ARRP Project belongs to the `Thorncrag` user account rather than an organization, the workflow requires a repository Actions secret named `ARRP_PROJECT_TOKEN`. Prefer a fine-grained personal access token limited to the `ARRP` repository, with account **Projects: read** and repository **Issues: read** permissions. A classic personal access token requires `read:project` plus the private-repository access needed to read the linked issues. No Project or issue write permission is needed. The builder never mutates the Project. GitHub's ordinary workflow token separately receives `contents: write` only so the publisher can update `progress-dashboard`; it does not write Project fields.

Do not place the token in the repository, dashboard data, workflow text, Project fields, or logs.

Until the secret is configured, workflow runs exit successfully with a visible setup notice and do not create or update the dashboard branch. This permits the implementation to remain on `main` without producing failed scheduled runs or publishing incomplete data.

For first-time activation:

1. create the read-only token in GitHub account settings;
2. save it as the `ARRP_PROJECT_TOKEN` repository Actions secret at `Settings` → `Secrets and variables` → `Actions`;
3. open the `Review Ready progress dashboard` workflow under `Actions`; and
4. choose `Run workflow` once to create the initial `progress-dashboard` branch and baseline page.

The daily schedule maintains the page thereafter. If the personal access token expires or is revoked, replace the secret and rerun the workflow; historical snapshots remain on the generated branch.

## Implementation Map

- [`.github/progress-dashboard.json`](../.github/progress-dashboard.json) owns the baseline, target, readiness statuses, field names, and forecast window.
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
  --input tests/fixtures/progress-project.json \
  --history tests/fixtures/progress-history.json \
  --as-of 2026-07-15 \
  --output /tmp/arrp-review-ready-site
```

The fixture contains one deliberately inconsistent status/score pair so the tracking-warning path remains tested. Local output is a branch-shaped directory whose entry page is `/tmp/arrp-review-ready-site/PROGRESS.md`.

## Governance Effect

This dashboard adds no proposal score, changes no audit result, creates no GitHub issue, assigns no milestone, and adds no new authoritative tracking database. It is a read-only view derived from existing Project fields. Changes to eligibility, the Review Ready rule, the official target, or the interpretation of readiness require a project-level Change Audit because they can materially change the displayed portfolio result.
