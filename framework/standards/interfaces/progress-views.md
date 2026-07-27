---
title: "Progress View Standard"
status: active
authority_scope: "Reusable rules for nonauthoritative progress boards, metrics, forecasts, history, holds, monitoring, and warnings."
load_when: "Designing, calculating, changing, or reviewing a project progress view."
dependencies:
  - "standard.md"
  - "../content/maturity-and-gates.md"
print_status: excluded
print_exclusion_reason: "Internal interface-governance documentation."
---

# Progress View Standard

A progress view is a read-only planning projection. Canonical content,
maturity, workflow, audit, and monitoring authorities remain outside the view.

## Required separations

- Maturity describes substantive development.
- Workflow state describes the current action or hold.
- Monitoring describes an external matter being watched.
- Governance, automation, or source gaps remain operational stewardship work
  unless the canonical content lifecycle independently makes them proposal work.

The view must not infer or repair canonical state. Missing, ambiguous, or
unrecognized inputs produce visible warnings or an unassigned state.

## Boards and metrics

Show the complete adopted maturity sequence without inventing extra stages from
workflow labels. Compact cards identify the stable record and link to both its
canonical content and authoritative work item.

Progress metrics define their numerator, denominator, baseline, exclusions,
and target explicitly. Administrative merger, retirement, rejection, or
rerouting may change the active denominator but is not attainment. A regression
reduces measured progress; new eligible work increases the denominator.

Required pace, rolling pace, forecast completion, and schedule variance are
planning signals rather than promises or measures of labor. A score change may
be a pipeline signal but does not itself measure work completed.

## History and provenance

Historical series must state the evidence and precedence used to reconstruct
earlier states. A retained validated snapshot supersedes an earlier seed for the
same date, and the current canonical build supersedes both. Corrections to an
adopted baseline or eligibility rule require the project's ordinary
change-control review.
