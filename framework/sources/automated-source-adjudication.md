---
title: "Automated Source Adjudication"
status: active
authority_scope: "Route-centered large-intake adjudication, source disposition, accountable ownership, preliminary-candidate synthesis, automation boundaries, and batch reconciliation."
load_when: "Processing a large source intake, resolving sources-pending ownership, clustering episodes, routing sources among issues and candidates, or synthesizing preliminary candidates from otherwise-unowned evidence."
dependencies: "../FRAMEWORK.md; source-catalogs.md; ../evidence/evidence-records.md; ../methodology/scope-and-admission.md; ../candidates/candidate-adjudication.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Automated Source Adjudication

## Authority and Dependencies

This file is the authoritative detailed rule for route-centered source adjudication and batch reconciliation. Apply [`source-catalogs.md`](source-catalogs.md) to catalog ownership and stable identity, [`../evidence/evidence-records.md`](../evidence/evidence-records.md) to qualitative placement, [`../methodology/scope-and-admission.md`](../methodology/scope-and-admission.md) to new institutional weaknesses, and [`../candidates/candidate-adjudication.md`](../candidates/candidate-adjudication.md) to formal candidates. Load [`../audits/CHANGE_AUDITS.md`](../audits/CHANGE_AUDITS.md) additionally when evidence materially changes a developed proposal.

## Load When

Load this file when processing a large source intake; resolving genuinely ambiguous source ownership; clustering several records into episodes; routing retained sources among issues, candidates, or research records; or synthesizing a preliminary candidate from evidence that may identify a distinct unowned institutional weakness.

## Route-Centered Automated Adjudication

Process large intakes by receiving proposal or Horizon record so the same institutional defect and remedy are loaded once for a coherent route-fit review. A source associated with several records is adjudicated once, assigned a primary evidentiary home when useful, and associated with additional record identifiers in one stable-ID source row rather than duplicated across the cited and pending catalogs.

The automated workflow is:

1. **Normalize and cluster.** Normalize URLs, titles, case names, official-action identifiers, dates, and source identity; detect existing `sources.csv` and `sources-pending.csv` entries; group records describing the same action, case, order, or episode; distinguish underlying events from reports about them; and identify likely primary instruments. Preserve provenance until the batch reconciliation succeeds.
2. **First substantive pass.** For each episode packet, identify the government action, evidentiary posture, strongest available primary source, litigation or official disposition, possible institutional weakness, issue and remedy fit, political-failure risk, duplicate relationship, and proposed evidentiary use.
3. **Independent challenge pass.** Re-test whether the route is merely topical, whether the receiving remedy actually addresses the demonstrated defect, whether allegations or preliminary rulings are overstated, whether a broad proposal is operating as a catch-all, whether contrary evidence is missing, and whether the characterization remains neutral under reversed party control. High-confidence graduation requires agreement between the passes or resolution through controlling primary material.
4. **Disposition.** Assign one of: anchor evidence; supporting evidence; corroborating source; comparator or counterexample; defined monitoring item; different existing proposal; possible preliminary Horizon candidate; political failure or outside scope; or redundant without additional evidentiary value. Verification gaps and unresolved legal questions must be expressed within one of those accountable routes—for example as a preliminary candidate's unresolved question or a monitor's revisit predicate—not retained as ownerless source dispositions.
5. **Route, cite, or remove.** If a retained source has a clear owner, cite it in that proposal's, candidate's, or preliminary candidate's substantive or source-development record and place its stable row in `sources.csv` immediately. Set `Reviewed?` to `No` when verification remains incomplete and `Monitoring` to `Yes` when the source itself is a changing record that warrants recurring checks. Use `sources-pending.csv` only when the project cannot yet choose among plausible destinations; record those competing routes and the exact decision needed. Update an existing row by normalized document identity instead of creating another. Remove a discovery record only after its disposition is documented. A redundant source adding no evidentiary value and an irrelevant or political-only record may be removed without entering either catalog; Git history supplies rollback and provenance.

Every retained source must leave adjudication with an accountable owner. That owner is (1) an existing issue or its linked evidence record; (2) a formal candidate; or (3) one preliminary candidate representing a plausible distinct institutional weakness not already owned by the project. Do not retain an orphan-source queue or ask the user to review individual source records. If verification remains incomplete but the material plausibly identifies an unowned weakness, state that uncertainty in the preliminary candidate's unresolved questions or defer predicate. If it does not yet support a plausible defect or an existing route, reject or remove it under a documented disposition rather than preserving an ownerless record.

## Preliminary-Candidate Synthesis

When the adjudication disposition is a possible preliminary Horizon candidate, the same validated batch must create or update the preliminary-candidate record, assign the next stable `INTAKE-GAP-###` identifier when no matching candidate exists, associate every retained source and catalog record with that identifier, and cluster later reporting about the same underlying weakness into that record. Candidate synthesis requires a neutral defect statement, possible area, distinctness rationale, existing-coverage comparison, best counterargument, unresolved questions, recommendation, and supporting source record. It is not enough to label a source as potentially new without creating the candidate readers will review.

The preliminary-candidate queue contains only unresolved questions awaiting review. When the user approves promotion through Codex, create a formal `HOR-###`, reroute supporting evidence to that formal record, and remove the preliminary row. An approved rejection or existing-issue disposition likewise removes the row. A deferred preliminary candidate remains only while its documented reason for postponement and reconsideration condition or date remain current. Do not retain promoted, rejected, or merged rows in the active preliminary queue or leave evidence routes pointing to obsolete `INTAKE-GAP-*` identifiers.

Preliminary identifiers remain stable provenance keys even after their active rows are removed. Allocate the next number above every `INTAKE-GAP-###` identifier retained in current issue, Horizon, source, or project history; never recycle a resolved identifier merely because the active preliminary-candidate CSV is empty.

Reader-facing intake terminology uses **preliminary candidate** for a synthesized question that has no `HOR-###` identifier or GitHub issue, and **proposed candidate** for a formal `HOR-###` record awaiting admission, merger, deferral, retirement, or another disposition. Preserve **Horizon** in internal technical names, identifiers, logs, metadata, GitHub labels, and workflow instructions.

Source adjudication must leave the stable authoritative inputs needed for candidate review; it must not create a separate narrative dossier as a new project record. Candidate Console presentation, derived-data ownership, read-only behavior, and decision controls are governed by [`../PROJECT_INTERFACE.md`](../PROJECT_INTERFACE.md#project-console-information-architecture).

## Automation and Human-Decision Boundary

The agent may automatically normalize, cluster, verify, reroute, update the source catalogs as the source's current use requires, make and document the qualitative placement decision, maintain and link an evidence or internal source-development record where warranted, consolidate corroboration, assign a monitoring disposition, and remove genuinely resolved temporary records when the result is high confidence and does not materially change a developed proposal's theory or remedy. Incomplete verification remains in the routed owner's `sources.csv` record; only unresolved ownership remains in `sources-pending.csv`. The user need not review individual sources. The agent may not create a public evidence page merely because material was routed to an issue, use a numeric threshold, or count inventory association alone as evidence integration.

Create a user-facing preliminary candidate only when the evidence may expose a distinct unowned institutional weakness. Present a focused recommendation when evidence would materially expand, narrow, split, merge, or change a developed proposal or its remedy. Such a change triggers the ordinary Change Audit / Internal Remedy-Fit rules; corroborating evidence that does not alter the issue theory does not. An evidence record receives no proposal score and no audit-run count.

## Batch Reconciliation and Closeout

Every adjudication batch must reconcile:

`input records = issue-page integrations + linked evidence-record integrations + no-additional-value dispositions + pending integration tasks + Horizon or monitoring integrations + rejected or redundant records + unresolved records`.

Before deleting temporary rows, verify that every retained external source has exactly one source-inventory home and a documented qualitative placement; every retained existing-issue episode has an issue-page destination, a justified linked evidence record, a documented no-additional-value disposition, or an active integration row; every reader-facing proposition has a source; no normalized source URL or document identity was duplicated; no dangling temporary candidate identifier remains; litigation posture is labeled accurately; and affected internal links resolve. A batch report should state records processed, distinct episodes, source records added or updated, duplicates consolidated, issue-page integrations, evidence records created and linked, no-additional-value dispositions, pending integration tasks, anchor citations selected, monitoring items, rejection categories, preliminary candidates, material issue changes recommended, and unresolved questions. Commit complete batches separately enough to permit rollback without restoring unrelated completed work.
