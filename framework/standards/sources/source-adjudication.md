---
title: "Automated Source Adjudication"
status: active
authority_scope: "Reusable route-centered large-intake adjudication, source disposition, accountable ownership, preliminary-candidate synthesis, automation boundaries, and batch reconciliation."
load_when: "Processing a large source intake, resolving ambiguous source ownership, clustering episodes, routing sources among content and candidates, or synthesizing preliminary candidates from otherwise-unowned evidence."
dependencies:
  - "../../FRAMEWORK.md"
  - "source-records.md"
  - "../content/scope-and-admission.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Automated Source Adjudication

## Authority and Dependencies

This file is the authoritative detailed rule for route-centered source
adjudication and batch reconciliation. Apply
[`source-records.md`](source-records.md) to catalog ownership and qualitative
placement, and
[`scope-and-admission.md`](../content/scope-and-admission.md) to possible new
institutional weaknesses. Each project supplies its exact candidate workflow,
identifiers, catalogs, and interface projection in the project layer. Load
[`change-audits.md`](../audits/change-audits.md) additionally when evidence
materially changes developed content.

## Load When

Load this file when processing a large source intake; resolving genuinely ambiguous source ownership; clustering several records into episodes; routing retained sources among issues, candidates, or research records; or synthesizing a preliminary candidate from evidence that may identify a distinct unowned institutional weakness.

## Route-Centered Automated Adjudication

Process large intakes by receiving accountable content or candidate record so
the same institutional defect and remedy are loaded once for a coherent
route-fit review. A source associated with several records is adjudicated once,
assigned a primary evidentiary home when useful, and associated with additional
record identifiers in one stable-identity catalog row rather than duplicated
across relied-upon and unresolved-routing catalogs.

The automated workflow is:

1. **Normalize and cluster.** Normalize URLs, titles, case names,
   official-action identifiers, dates, and source identity; detect existing
   relied-upon and unresolved-routing catalog entries; group records describing
   the same action, case, order, or episode; distinguish underlying events from
   reports about them; and identify likely primary instruments. Preserve
   provenance until the batch reconciliation succeeds.
2. **First substantive pass.** For each episode packet, identify the government action, evidentiary posture, strongest available primary source, litigation or official disposition, possible institutional weakness, issue and remedy fit, political-failure risk, duplicate relationship, and proposed evidentiary use.
3. **Independent challenge pass.** Re-test whether the route is merely topical, whether the receiving remedy actually addresses the demonstrated defect, whether allegations or preliminary rulings are overstated, whether a broad proposal is operating as a catch-all, whether contrary evidence is missing, and whether the characterization remains neutral under reversed party control. High-confidence graduation requires agreement between the passes or resolution through controlling primary material.
4. **Disposition.** Assign a project-defined accountable route such as anchor
   evidence, supporting evidence, corroborating source, comparator or
   counterexample, defined monitoring item, different existing content,
   possible preliminary candidate, outside scope, or redundant without
   additional evidentiary value. Verification gaps and unresolved questions
   must be expressed within an accountable route—for example as a candidate's
   unresolved question or a monitor's revisit predicate—not retained as
   ownerless source dispositions.
5. **Route, cite, or remove.** Apply the catalog, stable-identity, review-state,
   monitoring, and unresolved-routing boundaries in
   [`source-records.md`](source-records.md#source-inventory-and-stable-identity).
   Record the selected disposition and its accountable owner, cite retained
   material in the owning substantive or source-development record, and
   preserve recoverable provenance before removing a discovery record. A
   redundant or irrelevant record need not enter a canonical source catalog
   merely because it was discovered.

Every retained source must leave adjudication with an accountable owner. That owner is (1) an existing issue or its linked evidence record; (2) a formal candidate; or (3) one preliminary candidate representing a plausible distinct institutional weakness not already owned by the project. Do not retain an orphan-source queue or ask the user to review individual source records. If verification remains incomplete but the material plausibly identifies an unowned weakness, state that uncertainty in the preliminary candidate's unresolved questions or defer predicate. If it does not yet support a plausible defect or an existing route, reject or remove it under a documented disposition rather than preserving an ownerless record.

## Preliminary-Candidate Synthesis

When the adjudication disposition is a possible preliminary candidate, the same
validated batch must create or update one stable preliminary-candidate record,
associate every retained source and catalog record with that identity, and
cluster later reporting about the same underlying weakness into that record.
Candidate synthesis requires a neutral defect statement, possible project
location, distinctness rationale, existing-coverage comparison, best
counterargument, unresolved questions, recommendation, and supporting source
record. It is not enough to label a source as potentially new without creating
the accountable candidate record.

The preliminary-candidate queue contains only unresolved questions awaiting
review. Promotion creates the project's formal candidate record and reroutes
supporting evidence to it. An approved rejection, merger, or existing-content
disposition likewise removes the preliminary row from the active queue. A
deferred preliminary candidate remains only while its documented reason and
reconsideration condition or date remain current. Do not leave evidence routes
pointing to obsolete active-queue entries.

Preliminary identifiers remain stable provenance keys even after their active
rows are removed. Allocate new identifiers above every identifier retained in
current content, candidate, source, or project history; never recycle a
resolved identifier merely because the active queue is empty.

Each project defines its reader-facing preliminary and formal candidate
terminology, identifier formats, tracking surfaces, and promotion procedure in
the project layer.

Source adjudication must leave the stable authoritative inputs needed for
candidate review; it must not create a separate narrative dossier as another
project record or let a generated interface projection replace the canonical
candidate and source records.

## Automation and Human-Decision Boundary

Within project-defined authority, an agent may automatically normalize,
cluster, verify, reroute, update source catalogs as the source's current use
requires, make and document a qualitative placement decision, maintain and
link an evidence or internal source-development record where warranted,
consolidate corroboration, assign a monitoring disposition, and remove
genuinely resolved temporary routing records when the result is high confidence
and does not materially change developed content's theory or remedy.
Incomplete verification remains with the routed owner; only unresolved
ownership remains pending. The human decision-maker need not review raw sources
one by one. The agent may not create a public evidence page merely because
material was routed to content, use a numeric threshold, or count catalog
association alone as evidence integration.

Create a user-facing preliminary candidate only when the evidence may expose a
distinct unowned institutional weakness. Present a focused recommendation when
evidence would materially expand, narrow, split, merge, or change developed
content or its remedy. Such a change triggers the project's change-control and
remedy-fit rules; corroborating evidence that does not alter the underlying
theory does not. A supplemental evidence record receives no independent
proposal score or audit-run count.

## Batch Reconciliation and Closeout

Every adjudication batch must reconcile:

`input records = canonical-content integrations + supplemental-evidence integrations + no-additional-value dispositions + pending integration tasks + candidate or monitoring integrations + rejected or redundant records + unresolved records`.

Before removing temporary routing rows, verify that every retained external
source has exactly one source-catalog home and a documented qualitative
placement; every retained existing-content episode has a canonical-content
destination, a justified linked evidence record, a documented
no-additional-value disposition, or an active integration task; every
reader-facing proposition has a source; no normalized source URL or document
identity was duplicated; no dangling temporary candidate identifier remains;
litigation posture is labeled accurately; and affected internal links resolve.
A batch report should state records processed, distinct episodes, source
records added or updated, duplicates consolidated, content integrations,
evidence records created and linked, no-additional-value dispositions, pending
integration tasks, anchor citations selected, monitoring items, rejection
categories, preliminary candidates, material content changes recommended, and
unresolved questions. Preserve complete batches separately enough to permit
rollback without restoring unrelated completed work.
