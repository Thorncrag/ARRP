---
title: "ARRP Project Console Progress Configuration"
status: active
authority_scope: "ARRP Progress goal, eligibility, board, metrics, forecast, history, and source mapping."
load_when: "Calculating, changing, or reviewing the Project Console Progress view."
dependencies:
  - "../../standards/interfaces/progress-views.md"
  - "../profile/maturity-profile.md"
  - "../github/workflow.md"
  - "project-console-progress.json"
print_status: excluded
print_exclusion_reason: "Internal interface configuration."
---

# ARRP Project Console Progress Configuration

The Project Console **Progress** tab is ARRP's sole Console progress and
portfolio-measurement projection. It is a read-only projection of repository
records, the issue registry, and authoritative GitHub Project fields. It owns
the development-level board, Review Ready coverage, trajectory and history,
and routine issue monitoring. It does not replace or automatically repair its
authoritative inputs. Planning > Workbench > Pipeline is the separate
work-sequencing projection.

## Goal and eligibility

ARRP's goal is to bring every eligible active proposal to at least
`Review ready` by December 31, 2026. The exact target, field mappings, baseline,
forecast window, and eligible maturity values are maintained in
[`project-console-progress.json`](project-console-progress.json).

Eligibility comes from active `proposal` rows in
`inventory/github_issue_registry.csv`. Closed merged records remain preserved
as `merged proposal` rows but are excluded. The proposal identifier in the
registry title joins to the GitHub Project `Title`; `Canonical page` is a
fallback only when it identifies one item uniquely. An unmatched or ambiguous
proposal remains in the denominator, counts as not ready, and produces a
warning.

An eligible proposal counts as ready only when its Project score is at least 75
and `Development level` is `Review ready` or `Release candidate`. Workflow
`Status` explains the next action or hold and does not change readiness.

## Board and metrics

The board shows all six ARRP maturity values in one desktop row. Each card
contains the stable identifier, score when available, workflow cue, canonical
proposal link, and GitHub issue link. Unknown maturity remains visibly
unassigned.

The view reports eligible, ready, remaining, coverage, scope change, required
and rolling pace, forecast completion, variance, area coverage, monitoring,
compact hold counts, and tracking warnings. Detailed Blocked and Deferred
records live only in Planning > Workbench; Progress links there and does not
duplicate the hold ledger. Governance discovery and automation gaps are not
proposal progress unless an ordinary canonical lifecycle or audit update makes
them so.

Required weekly pace is remaining eligible proposals divided by the weeks
before the target. Rolling pace is net new ready proposals during the configured
28-day window, expressed per week. Administrative denominator reductions are
excluded from attainment velocity.

## History and local-first implementation

The supported retrospective seed begins June 24, 2026. The preserved former
combined record and its reconstructed July baseline are retained at
[`project-console-progress.md`](../../archive/baselines/project-console-progress.md).

In the P6 production chain, the coordinator supplies an authenticated Project
snapshot and exact local output paths. The bot writes current progress
and bounded history under the transaction run directory; it does not publish
to a data branch, obtain credentials through Elim, or mutate Project fields.
Scheduling, credential isolation, local history carry-forward, failure
behavior, validation, and the production boundary belong to the [Project
Console Progress Bot
runbook](../automation/runbooks/project-console-progress-bot.md).

Changes to eligibility, readiness, the official target, or historical baseline
require a project-level Change Audit.
