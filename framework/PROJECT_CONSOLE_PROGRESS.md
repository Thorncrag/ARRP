---
title: "Project Console Progress"
print_levels:
  - full-technical
---

# Project Console Progress

The **Progress** tab in the internal [ARRP Project Console](../research/horizon-review-console/index.html) is the project's sole human-facing progress dashboard. It visualizes the goal of bringing every eligible proposal to at least **Review Ready** by **December 31, 2026**. It does not replace the [ARRP GitHub Project](https://github.com/users/Thorncrag/projects/2), which remains the lifecycle authority, or repository issue pages and audit sidecars, which remain the substantive and audit authorities.

ARRP does not maintain a second Markdown dashboard on GitHub. Automation publishes only `progress.json` and `history.json` to the data-only `project-console-data` branch. The console consumes that feed and retains a checked-in offline snapshot. The data branch is infrastructure, not a second reader interface, and must not contain a rendered dashboard, narrative page, or chart files.

## Goal and eligibility

The corrected July 13, 2026 baseline is 23 Review Ready proposals out of 204 eligible proposal issues. A retrospective series begins June 24 and reconstructs how those 23 proposals reached Review Ready before automated tracking began. Eligibility and identity come from [`inventory/github_issue_registry.csv`](../inventory/github_issue_registry.csv) rows whose `Kind` is `proposal`. Closed merged records remain preserved as `merged proposal` rows but are excluded from the active portfolio.

The builder joins the proposal identifier in the registry title to the identifier in the GitHub Project's built-in `Title` field. `Canonical page` is a fallback only when it uniquely identifies one Project item. Governance, horizon, source-review, merged-proposal, and other non-active-proposal records are excluded. A proposal without an unambiguous Project identity remains in the denominator, is treated as not ready, and produces a tracking warning.

The official target and calculation settings are stored in [`.github/project-console-progress.json`](../.github/project-console-progress.json). A rolling forecast may move as progress changes, but it does not replace the official target. Changes to eligibility, the readiness rule, or the official target require a project-level Change Audit.

## Review Ready rule

An eligible proposal counts toward the goal only when its GitHub Project score is at least 75 and its Project status is one of:

- `Review ready`;
- `Advanced review ready`;
- `Proposal ready`;
- `Publication ready`;
- `Fully validated`; or
- `Release candidate`.

`Completed within scope` and other administrative dispositions do not count as development progress. Merging, integrating, retiring, rejecting, or rerouting a record may change the active denominator, but it does not increase the Review Ready numerator or attainment velocity. The calculation flags status/score inconsistencies and undeveloped lifecycle drift but never repairs Project data automatically.

## Metrics and forecast

The console reports eligible, Review Ready, and remaining counts; current portfolio coverage; scope change from baseline; required and rolling weekly pace; forecast completion; schedule variance; area coverage; closest-to-ready proposals; and tracking warnings. Its trajectory graph compares actual attainment with the pace required to reach the official target.

Required weekly pace is:

`remaining eligible proposals / weeks remaining before the official target`.

Rolling pace is the net change in Review Ready count during the configured 28-day window, expressed per week. A regression reduces measured progress; a newly admitted proposal increases the denominator. Administrative reductions in the denominator may change coverage and the forecast but are excluded from attainment velocity. Score movement is a pipeline signal, not a measure of labor. Forecasts are planning signals, not promises or substitutes for proposal-level judgment.

## Retrospective evidence

The checked-in [retrospective seed](../.github/progress-history-seed.json) records the earliest dated score-bearing audit at or above 75 for each proposal in the official 23-proposal baseline. Audit sidecars control the attainment date; commit history corroborates but does not replace an explicit audit date.

The reconstructed series begins at zero on June 24, then records 1 on June 25, 3 on June 27, 16 on June 28, 17 on July 2, 22 on July 4, and 23 on July 9. A retained automated snapshot overrides the seed on the same date, and the current build overrides both. If an earlier qualifying audit is discovered, correct the seed and this explanation together through a project-level Change Audit.

## Automation and retention

The [`Project Console progress data`](../.github/workflows/project-console-progress.yml) workflow runs daily, supports manual dispatch, and runs when its implementation or configuration changes. It:

1. reads GitHub Project fields through the GraphQL API;
2. joins them to active proposal identity from the issue registry;
3. loads the retrospective seed and retained `history.json`;
4. validates and combines the retained and current snapshots;
5. calculates the metrics, forecast, area results, backlog, and warnings; and
6. publishes only `progress.json` and `history.json` to `project-console-data` through non-forced Git data API updates.

The ordinary `main` push trigger watches implementation and configuration files, not every issue or audit. When a scored audit changes an eligible proposal's Project `Status`, `Score`, or goal eligibility, audit closeout must dispatch this workflow after Project readback and the repository push, wait for success, and verify `project-console-data/progress.json`. One final verified dispatch may close an expressly authorized multi-issue or successive-tier batch. The daily schedule is a recovery backstop.

History remains off `main` so automated daily snapshots do not create ordinary development commits. If retained history is unavailable or invalid, the builder safely restarts from the supported retrospective seed and current snapshot. Never edit the data branch manually.

## Authentication and permissions

The workflow requires the repository Actions secret `ARRP_PROJECT_TOKEN`, containing a classic personal access token limited to `read:project`. The GraphQL request reads Project field values and never mutates the Project. GitHub's workflow token receives `contents: write` only to update the data branch. Do not place either token in repository files, generated data, Project fields, or logs.

If the secret is absent, the workflow exits successfully with a visible notice and leaves the existing data unchanged. If the token expires or is revoked, replace the secret and rerun the workflow; retained snapshots remain on the data branch.

## Implementation map

- [`.github/project-console-progress.json`](../.github/project-console-progress.json) owns the goal, readiness, field-mapping, and forecast settings.
- [`.github/progress-history-seed.json`](../.github/progress-history-seed.json) owns the supported pre-automation attainment evidence.
- [`.github/workflows/project-console-progress.yml`](../.github/workflows/project-console-progress.yml) owns scheduling and permissions.
- [`scripts/build_project_console_progress.py`](../scripts/build_project_console_progress.py) calculates and writes the two data files.
- [`scripts/publish_project_console_progress.py`](../scripts/publish_project_console_progress.py) updates the independent data branch.
- [`tests/test_project_console_progress.py`](../tests/test_project_console_progress.py) covers eligibility, authority, history, forecast inputs, data-only output, and branch publication.
- [`research/horizon-review-console/`](../research/horizon-review-console/) owns the sole human-facing visualization, including the trajectory graph.

## Local validation

Run:

```bash
python3 -m unittest tests/test_project_console_progress.py
python3 scripts/build_project_console_progress.py \
  --config tests/fixtures/progress-config.json \
  --registry tests/fixtures/progress-registry.csv \
  --input tests/fixtures/progress-project.json \
  --history tests/fixtures/progress-history.json \
  --as-of 2026-07-15 \
  --output /tmp/arrp-project-console-progress
```

The output directory must contain only `progress.json` and `history.json`.

## Governance effect

This view changes no proposal score, audit result, GitHub issue, milestone, or Project field. It remains a derived read-only planning tool. Changes to eligibility, the Review Ready rule, the official target, or the interpretation of readiness require a project-level Change Audit because they can materially change the displayed result.
