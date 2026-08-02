---
title: "ARRP Source Catalog and Adjudication Workflow"
status: active
authority_scope: "ARRP source-catalog files and fields, repository paths, adjudication-route names, candidate handoff, and source-monitoring and interface closeout mappings."
load_when: "Adding, reviewing, routing, monitoring, removing, or materially repurposing an ARRP source; processing a large source intake; or reconciling ARRP source catalogs and source-development records."
dependencies:
  - "../../standards/sources/claims-and-citations.md"
  - "../../standards/sources/source-records.md"
  - "../../standards/sources/source-adjudication.md"
  - "../../standards/sources/monitoring.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# ARRP Source Catalog and Adjudication Workflow

## Authority and Dependencies

This file applies the reusable
[source-record standard](../../standards/sources/source-records.md) and
[source-adjudication standard](../../standards/sources/source-adjudication.md)
to ARRP's exact catalogs, identifiers, paths, fields, and workflow surfaces.
Apply the [candidate workflow](candidate-review.md) when source adjudication
identifies a possible preliminary or formal Horizon candidate, and apply the
[GitHub workflow](../github/workflow.md) when issue-level monitoring or hosted
workflow state changes.

## Canonical Source Catalogs

ARRP configures the two catalog roles in the
[source-record standard](../../standards/sources/source-records.md#source-inventory-and-stable-identity)
as follows:

- [`inventory/sources.csv`](../../../inventory/sources.csv) is the relied-upon
  source catalog. Its permanent stable identifiers use `SRC-####`.
- [`inventory/sources-pending.csv`](../../../inventory/sources-pending.csv) is
  the temporary unresolved-routing catalog. A pending row names the plausible
  competing destinations and exact routing decision.

Use `Reviewed? = No` in the catalog that currently owns the row when
verification remains incomplete. `Proposition Supported` identifies the
assertion or question the source supports or is being reviewed to support, and
`Notes` states any material qualification.

Use `Monitoring = Yes` only when the retained source is itself a changing
record. Every `Yes` row states the watched change in `Monitoring Rationale` and
uses a human-readable `Monitoring Group` to cluster the same case family,
directive, investigation, disclosure, or factual episode. `Monitoring
Baseline` stores only the last accepted deterministic-watcher fingerprint;
leave it blank when no validated watcher covers the row. A deliberate
initialization may populate a blank baseline without reporting the existing
state as a change, but an ordinary scheduled run must not silently accept a
missing baseline.

An open case-level docket row uses `Monitoring = Yes`. A fixed opinion, order,
complaint, brief, filing, report, article, or archived instrument remains
`Monitoring = No` merely because the surrounding matter is active, unless that
row deliberately serves as the changing case-level record.

## ARRP Evidence and Source-Development Paths

Use the following exact homes:

1. **Canonical issue page.** The issue page owns the diagnosis, material
   manifestations, damage, weakness, remedy, proposal vehicle, and conclusions,
   and carries the strongest evidence needed for its material propositions.
2. **Reader-facing issue evidence record.** When separate treatment adds
   meaningful reader value after the issue page is sufficiently supported,
   create `areas/<AREA>/evidence/<ISSUE-ID>-evidence.md` using the
   [evidence-record template](../../standards/sources/templates/evidence-record.md).
   The issue page links it concisely from the end of **Manifestation of the
   Failure** as **Additional supporting record**. The evidence record does not
   receive an independent proposal score, audit run, remedy, audit history, or
   GitHub proposal issue.
3. **Issue source-development record.** Place internal proposition-bearing
   source development at
   `areas/<AREA>/research/<ISSUE-ID>-source-development.md`.
4. **Formal Horizon source-development record.** Place formal-candidate source
   development at
   `research/candidate-source-development/<HOR-ID>-source-development.md`.
5. **Source-development shell.** When an admitted or unresolved area-specific
   identifier lacks a substantive issue page, keep its shell at
   `areas/<AREA>/issues/<ISSUE-ID>.md`, mark it
   `record_type: source-development`, and link it to
   `../research/<ISSUE-ID>-source-development.md` using the
   [source-development template](../../standards/sources/templates/source-development-record.md).
   The shell does not establish admission, diagnosis, remedy, legislation,
   score, audit status, or public-release readiness and requires no audit
   sidecar until substantive proposal development begins.

Publication disposition for evidence and source-development records is
governed by the
[ARRP print configuration](../publication/print-assembly.md#evidence-and-source-development-metadata).

## ARRP Route-Centered Adjudication

Process a large intake by receiving issue or Horizon record so one coherent
packet supplies the institutional defect, remedy, and current source context.
Apply the reusable normalization, substantive-pass, independent-challenge, and
accountable-owner requirements in the
[source-adjudication standard](../../standards/sources/source-adjudication.md#route-centered-automated-adjudication)
before assigning one of these ARRP route names:

- anchor evidence;
- supporting evidence;
- corroborating source;
- comparator or counterexample;
- defined monitoring item;
- different existing proposal;
- possible preliminary Horizon candidate;
- political failure or outside scope; or
- redundant without additional evidentiary value.

When evidence may identify a distinct unowned institutional weakness, follow
the [preliminary-candidate synthesis and promotion
rules](candidate-review.md#preliminary-candidate-synthesis-and-promotion).

## ARRP Closeout Mappings

Apply the reusable
[automation boundary](../../standards/sources/source-adjudication.md#automation-and-human-decision-boundary)
and
[batch reconciliation](../../standards/sources/source-adjudication.md#batch-reconciliation-and-closeout)
without restating them as separate ARRP rules. For ARRP closeout, map
canonical-content integrations to issue-page integrations, formal candidates
to Horizon records, and supplemental evidence to the linked evidence-record
path above.

Continued issue-level monitoring is represented by `needs: monitoring` on the
existing GitHub issue. A changing source that independently warrants recurring
checks uses `Monitoring = Yes` in the catalog that owns it. These states are
independent.

The [Project Console source projections and rebuild
triggers](../interfaces/project-console/specification.md#source-projection-refresh) and the
[publication source-list rules](../publication/print-assembly.md#generated-sources-and-supporting-materials-list)
are downstream views of these canonical records; neither creates another
source authority.
