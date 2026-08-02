---
title: "ARRP Candidate Discovery and Adjudication"
status: active
authority_scope: "ARRP Horizon discovery, formal-candidate investigation, recommendation, human decision, implementation, preservation, and verification."
load_when: "Running a Horizon Scan or addressing, reviewing, adjudicating, admitting, merging, retaining, rejecting, or retiring a formal HOR-### candidate."
dependencies:
  - "../../standards/content/candidate-review.md"
  - "../../standards/content/scope-and-admission.md"
  - "../profile/maturity-profile.md"
  - "../../standards/sources/source-records.md"
  - "../../standards/sources/source-adjudication.md"
  - "../github/workflow.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# ARRP Candidate Discovery and Adjudication

## Authority and Dependencies

This file implements the reusable
[Candidate Discovery and Review Standard](../../standards/content/candidate-review.md)
for ARRP's Horizon queue and `HOR-###` records. Apply ARRP's exact GitHub
mechanics in [`../github/workflow.md`](../github/workflow.md), source ownership
and catalog routing in
[`source-adjudication.md`](source-adjudication.md),
the exact lifecycle and foundation rules in the
[ARRP maturity profile](../profile/maturity-profile.md), and the
human-authority boundary in [`../../FRAMEWORK.md`](../../FRAMEWORK.md).

## Load When

Load this file when running or reviewing a Horizon Scan or when the user asks
to address, assess, adjudicate, ingest, merge, admit, retain, reject, or retire
a specific `HOR-###` candidate.

## Horizon discovery

The **Horizon Scan** is ARRP's project-wide discovery flavor for identifying
new, emerging, or newly salient institutional concerns within the project's
goals. It is not an issue-quality scoring tier.

A scan uses current reliable public sources, cross-checks each concern against
existing areas, issues, legislation, research, source-development records,
active Horizon issues, Project fields, and the Horizon Scan Log, and applies
the ordinary Issue-Admission Test. Each finding must state whether the concern
is a duplicate, manifestation, reason to revise existing work, source lead,
possible standalone issue, or outside current scope and must recommend an exact
next treatment.

Project 2025 crossover analysis treats Project 2025 as both an
implementation-tracking and weakness-discovery source. Lack of implementation
may affect urgency and manifestation evidence but does not by itself remove a
plausible structural weakness from review. Prefer official Heritage-controlled
material, use stable mirrors for location or preservation, and use ARRP's local
backup only when the official and stable online sources are unavailable or
insufficient.

A scan is recommendation-only. It does not directly create issue pages, revise
legislation, change scores, or alter inventories without separate
implementation authority. Active formal findings use sequential `HOR-###`
identifiers and GitHub Issues/Project records. The cumulative
[Candidate Discovery Log](../../logs/candidates/candidate-discovery-log.md) preserves
adjudicated outcomes rather than serving as the active queue.

Each formal scan result records its scan scope, source routes, concern,
overlap check, admission analysis, recommendation, proposed disposition,
supporting sources, uncertainty, and next action.

## Preliminary Candidate Synthesis and Promotion

ARRP uses **preliminary candidate** for a synthesized question that has no
`HOR-###` identifier or GitHub issue, and **proposed candidate** for a formal
`HOR-###` record awaiting admission, merger, deferral, retirement, or another
disposition. Preserve **Horizon** in internal technical names, identifiers,
logs, metadata, GitHub labels, and workflow instructions.

When source adjudication identifies a possible preliminary Horizon candidate,
apply the reusable
[preliminary-candidate synthesis requirements](../../standards/sources/source-adjudication.md#preliminary-candidate-synthesis).
ARRP records each unresolved preliminary candidate in
[`research/trump-administration-preliminary-candidates.csv`](../../../research/trump-administration-preliminary-candidates.csv)
and uses `INTAKE-GAP-###` as its stable preliminary identifier. When no matching
candidate exists, allocate the next number above every `INTAKE-GAP-###`
identifier preserved in issue, Horizon, source, candidate, or project history.
Do not recycle a resolved identifier merely because the active queue is empty.
Associate every retained source and catalog record with the stable identifier.

When the user approves promotion through Codex, create the formal `HOR-###`
record and GitHub issue, reroute supporting evidence to that formal record, and
remove the preliminary row from the active queue. An approved rejection,
merger, or existing-issue disposition likewise removes the row. Do not retain
promoted, rejected, merged, or otherwise resolved rows in the active
preliminary queue or leave evidence routes pointing to obsolete
`INTAKE-GAP-*` identifiers.

The
[Project Console candidate views](../interfaces/project-console/specification.md#project-console-information-architecture)
are read-only projections of these records and do not change a disposition.

## Horizon Candidate Adjudication Workflow

1. **Locate the candidate.** Find the `HOR-###` GitHub Issue for active horizon candidates, or find the `HOR-###` row in the [`Candidate Discovery Log`](../../logs/candidates/candidate-discovery-log.md) if the candidate has already been adjudicated.
2. **Verify the factual premise.** Check the cited sources and, where the matter is current or source-sensitive, refresh with reliable current public sources. Prefer primary materials when the claim depends on a court order, statute, regulation, bill, executive action, agency action, official vote, or formal record.
3. **Cross-check existing project coverage.** Search existing areas, issue pages, proposed legislation, source-development notes, inventories, and GitHub Project items/fields for overlap. Identify the best existing home if the concern is a manifestation, source-development lead, or expansion of an existing issue.
4. **Apply the canonical Issue-Admission Test.** Record the candidate-level answer to each of its three conclusions: human consequence, institutional cause and repairability, and standalone fit. Evidence must support a concrete institutional pathway, but do not require completed harm, repetition, or multiple episodes when one well-established episode reliably exposes a generalizable defect. Candidate review requires a plausible neutral remedy class, not selection of the final remedy or vehicle.
5. **Prepare the human reversed-control analysis.** Explain neutrally how the existing arrangement and any plausible remedy class could operate under materially different political control, including overcorrection and misuse risks. Do not answer the human reversed-control question or treat it as satisfied; identify the exact decision for the human author when it is material.
6. **Make a disposition recommendation.** Present the user with a concise recommendation: admit as a new issue, merge into an existing issue, expand or amend an existing issue, retain as source development only, retire without admission, or reject as outside scope. Include the best counter-argument if the recommendation is not obvious.
7. **Wait for a record-specific human decision before implementation.** Do not admit, merge, integrate, retire, reject, remove from active scope, or otherwise implement a permanent disposition until the human author's decision identifying that candidate and outcome is recorded. Preserve the candidate and route the exact question through `Status: Human decision needed` while the decision remains pending.
8. **Implement the approved disposition.** Apply the following record rules so the intake history remains traceable without creating duplicate issues:
   - **Admitted independently:** reuse the existing GitHub issue unless it was created erroneously or a documented technical limitation makes reuse impossible. Assign the next stable area-specific issue ID; retitle the same issue from `HOR-###` to `AREA-###`; replace `kind: horizon` with `kind: proposal`; keep the issue open; preserve the originating `HOR-###` in the issue body and Horizon Scan Log; update the existing registry row in place so its issue number and URL remain stable; create the canonical issue page and any proposal vehicle; and synchronize the area page and `issue_count`, Subject and Institution Index, sources, and all required GitHub Project fields. Do not create a second proposal issue for the same admitted candidate.
   - **Merged, integrated, or retained only as source development:** preserve the `HOR-###` title prefix, append a precise bracketed disposition such as `[Merged into REG-001]` or `[Integrated into REG-001]`, add a dated final-disposition section to the issue body that supersedes the active-intake language, update the registry title and Horizon Scan Log, and update the receiving issue, area, and source records. If the disposition ends all independent work, close the issue and remove its card from the active Project without deleting the issue.
   - **Retired or rejected:** preserve the `HOR-###` title prefix, append a precise bracketed disposition such as `[Outside scope]` or `[Retired]`, add a dated final-disposition section to the issue body, update the registry title and Horizon Scan Log with the rationale and revisit trigger, close the issue, and remove its card from the active Project without deleting the issue. Do not create or retain an individual Subject and Institution Index entry for the rejected candidate.
9. **Maintain and verify the Horizon Scan state.** Active horizon candidates should live as open GitHub Issues and active GitHub Project items. Independently admitted candidates should live as open area-specific proposal issues while retaining their static Horizon provenance in the Horizon Scan Log. Other adjudicated candidates should remain available through their closed GitHub issues and Horizon Scan Log rows; they should not remain on the active Project unless a specific continuing workflow obligation is documented. After implementation, read back the issue title, state, body disposition, labels, registry row, Horizon Scan Log row, receiving record, and Project presence or removal as applicable.
10. **Preserve source traceability.** Apply the
    [ARRP source catalog workflow](source-adjudication.md#canonical-source-catalogs)
    to every external source relied on in adjudication or implementation, even
    when the candidate is retired.
11. **Validate and preserve.** Run lightweight formatting and inventory checks appropriate to the files changed. Commit and push the adjudication update when repository access is available, unless the user has asked not to commit.
