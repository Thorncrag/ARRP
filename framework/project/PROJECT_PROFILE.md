---
title: "ARRP Project Profile"
status: active
dependencies:
  - "../standards/content/scope-and-admission.md"
  - "../standards/content/record-architecture.md"
  - "../standards/content/neutrality-and-language.md"
print_status: excluded
print_exclusion_reason: "Internal project configuration."
---

# ARRP Project Profile

This record identifies the choices that make this installation the American
Restoration and Resilience Project. It supplements the reusable standards; it
does not restate them.

## Canonical public identity

- The public premise, mission, scope, authorship, and reader orientation are
  maintained in [`../../README.md`](../../README.md) and
  [`../../ABOUT.md`](../../ABOUT.md).
- Cross-cutting ARRP principles and authority boundaries are maintained in the
  root [`../FRAMEWORK.md`](../FRAMEWORK.md) entry point.
- Adopted ARRP-specific conventions are grouped in [`profile/`](profile/).

## Installation choices

ARRP uses:

- institutional issue identifiers and area-owned issue records;
- proposed legislation keyed to those identifiers;
- GitHub Issues and a GitHub Project as the hosted collaboration and workflow
  surface;
- GitHub Pages as the public publication surface;
- a separately deployed public-input service;
- the local ARRP Project Console as a generated administrative view; and
- named deterministic bots and bounded LLM agents whose exact authority is
  recorded under [`automation/`](automation/).

These are ARRP configuration choices. A future project may replace them without
changing the reusable standards unless the underlying general rule also
changes.

## Adopted scope applications

President Trump's administrations and Project 2025 are principal ARRP case
studies and stress tests, not the project's outer boundary. Older, continuing,
and future-facing defects remain eligible under the reusable
[`scope-and-admission.md`](../standards/content/scope-and-admission.md)
standard.

As current applications of the political-failure boundary—not definitions of
that boundary—ARRP treats District of Columbia statehood and the selection of
Puerto Rico's final political status, including statehood, as outside scope on
the present record. Congress and the affected electorates retain political and
constitutional avenues for considering those choices, and ARRP has not
identified an independent process defect whose repair would determine the
result without substituting the project's judgment for the political decision.
Narrower issues involving either jurisdiction may still qualify when they
identify a separable institutional defect and a remedy that does not
presuppose statehood or another final-status outcome.

## Adopted issue-page configuration

ARRP applies the reusable
[`record-architecture.md`](../standards/content/record-architecture.md)
standard with these exact choices:

- Candidate or development-stage issue pages without a draft vehicle use
  `Pending development` as the single **Proposed Legislation** bullet. This is
  page-content text, not a GitHub Project `Status` value.
- The quality-review section is headed **Proposal Scoring**. It shows the
  proposal-quality score, any companion scores, Required Electoral
  Environment, Development Priority, and any assessed coalition-support
  estimates first, separated by an em dash divider from audit status, rubric
  version, rebaseline status, next audit need, and a link to the sibling full
  audit-history file.
- The fiscal disclaimer is `*Note: Preliminary ARRP assessment only; not a
  CBO, OMB, agency, or legislative-counsel score.*`
- When the chosen remedy may fund postage, tracking, or election-administration
  support, the available supplemental classification is `Budget authority may
  be required if the chosen remedy funds postage, tracking, or
  election-administration support; no dollar estimate is assigned pending
  source-backed cost data.`

## Reader-facing technical vocabulary

Reader-facing ARRP prose does not rely on unexplained internal shorthand such
as `T0` through `T4`, `Change Audit`, `Internal Remedy-Fit Audit`, `rebaseline`,
or `fixed zero`. State the substantive result directly. When provenance
matters, use a formulation such as `A July 2026 internal project review found
...` or, when the formal audit character matters, `A July 2026 internal project
audit found ...`, with a link to the technical history where appropriate.
Exact terminology remains appropriate on technical and administrative
surfaces under the reusable
[`neutrality-and-language.md`](../standards/content/neutrality-and-language.md)
standard.
