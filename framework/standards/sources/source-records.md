---
title: "Source and Evidence Records"
status: active
authority_scope: "Reusable stable source identity, source catalogs, monitoring metadata, and qualitative placement among content, evidence, and source-development records."
load_when: "Adding, reviewing, routing, monitoring, removing, or materially repurposing a source or deciding which project record should own retained evidence."
dependencies:
  - "claims-and-citations.md"
  - "../content/record-architecture.md"
  - "../../PROJECT_STRUCTURE.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Source and Evidence Records

## Authority and Dependencies

This file is the authoritative detailed rule for stable source identity, catalog
boundaries, monitoring metadata, qualitative evidence placement, and
source-development records. Claim support belongs to
[`claims-and-citations.md`](claims-and-citations.md), issue-level monitoring to
[`monitoring.md`](monitoring.md), content-record structure to
[`record-architecture.md`](../content/record-architecture.md), and physical
placement to [`PROJECT_STRUCTURE.md`](../../PROJECT_STRUCTURE.md).

## Load When

Load this file when routing retained evidence to content or a candidate;
deciding whether evidence belongs in the canonical content, a linked public
evidence record, an internal source-development record, or a
source-development shell; or reconciling source placement during substantive
development or review.

## Evidence Architecture

1. **Canonical content record.** The canonical content remains authoritative
   for its diagnosis, material manifestations, resulting damage, weakness,
   remedy, implementation vehicle, and conclusions. It should cite the
   strongest primary authority, controlling or material official findings, and
   representative evidence needed to establish each material proposition. A
   linked evidence record supplements but never excuses missing nearby
   citations for claims essential to the content.
2. **Supplemental evidence record.** Once the canonical content record already
   contains sufficiently strong evidence for its material propositions, place
   additional reader-useful evidence in a separate record when doing so
   preserves clarity and concision. Use the
   [Evidence Record Template](templates/evidence-record.md) at the
   project-configured reader-facing evidence location. The record may organize
   verified distinct episodes, primary instruments, judicial and official
   dispositions, corroborating sources, counterexamples, and defined
   monitoring items. It must not create an independent diagnosis, remedy,
   proposal, score, workflow state, or audit history. It links back to the
   canonical content and cites sources registered in the project's
   relied-upon source catalog. Publication treatment is configured separately
   in the project layer.
3. **Internal source-development record.** When routed sources are not yet
   appropriate for concise reader-facing prose, cite them in a content- or
   candidate-specific internal source-development record at the
   project-configured location. The record states the proposition or
   verification question, review status, and monitoring qualification without
   treating the material as an adjudicated finding. A generic statement that
   the source concerns the described action, litigation, or episode is not
   sufficient; identify what institutional proposition, boundary, controlling
   action, or procedural question later review is expected to resolve. It is
   an accountable use of the source and therefore places the source in the
   relied-upon catalog; it is not a substitute for later selecting the
   strongest evidence for the public content or evidence page.
4. **Source-development shell.** If an admitted or unresolved content
   identifier lacks a standalone page, create an internal shell using the
   [Source-Development Record Template](templates/source-development-record.md)
   and the project-configured publication disposition. The shell owns and
   links the content-specific source-development record but does not imply
   completed admission analysis, diagnosis, remedy, proposal text, score,
   audit, or public-release readiness. It requires no audit sidecar until
   substantive development begins.

The accountable-record monitoring rule is maintained in
[`monitoring.md`](monitoring.md).

## Routing and Qualitative Placement

Unresolved routing leads belong in the project's pending-routing catalog with
the plausible competing destinations, the reason ownership cannot yet be
selected, and the exact next routing decision. A pending row must not name one
clear accountable owner; once an owner is clear, create or use that owner's
source-development record and move the row to the relied-upon catalog.
Temporary batch files may exist while a scan is running, but the active project
must not retain a parallel source, litigation, integration, or routing ledger
after reconciliation. Inclusion by a tracker or classifier does not make a lead
public evidence.

The evidence-page decision is qualitative, not quantitative. There is no
source-count or episode-count threshold, and neither a large intake nor an
additional source automatically requires a separate reader-facing page. First
ask whether the canonical content already establishes each material
proposition with sufficiently strong, representative evidence. A stronger or
necessary new source belongs in the canonical content, replacing weaker
support where appropriate. Once the canonical content is sufficiently
evidenced, place additional material in a linked evidence record only when it
has meaningful reader-facing value and the separate record improves clarity,
organization, or continuing monitoring. Routed material that still warrants
verification or later selection belongs in the internal source-development
record, not the pending-routing catalog. Cumulative corroboration adding no
project value may be removed after a documented no-additional-value
disposition.

For an automated large-intake review, each retained source routed to existing
content must receive the same qualitative placement decision:
canonical-content integration when it strengthens necessary support; linked
evidence-record integration when the canonical content is already sufficiently
supported and the additional material warrants reader-facing treatment; a
proposition-bearing citation in the internal source-development record when
verification or later selection remains incomplete; or removal after a
documented no-additional-value finding. Association with an identifier alone is
not a citation and does not justify placement in the relied-upon catalog, but
unfinished verification, monitoring, or content development does not justify
leaving a clearly routed source pending. The canonical content should link a
supplemental evidence record concisely from the relevant evidentiary section.
Do not add a generic administrative monitoring link, administrative
monitoring subsection, missing-target placeholder, or monitoring boilerplate
to reader-facing content.

Do not create a reader-facing evidence page merely to empty a queue. When the
receiving content is undeveloped or lacks a canonical page, create the internal
source-development shell and its proposition-bearing source record instead of
leaving clearly owned sources pending. A formal or preliminary candidate's
canonical intake or source-development record supplies the citation for
candidate-owned material. Organize any public evidence page by institutional
manifestation or mechanism rather than source order. Prefer prose headings and
concise bullets over wide source tables that render poorly on mobile or in
print.

## Source Reconciliation During Issue Work

At the start of substantive content development or an applicable audit, check
the cited and source-development records and the accountable record's
monitoring state. A source awaiting verification remains associated with its
owner in the relied-upon catalog and carries the configured incomplete-review
state; a changing external record uses the configured source-monitoring state.
Neither returns to pending unless later review genuinely makes ownership
unclear. Development and higher-depth review should verify sources, test route
and remedy fit, select the strongest material for reader-facing integration,
remove no-additional-value records, and preserve qualified or monitored
source-development material without mistaking catalog placement for
substantive integration.

Source reconciliation is part of content-development or audit work and does not
create a separate audit run. Corroborating or cumulative-source placement that
does not alter the content theory requires no Change Audit. A source that
materially changes developed content's manifestation, diagnosis, damage theory,
remedy, proposal vehicle, or score basis triggers the ordinary change-control
and remedy-fit rules. At closeout, confirm that no clearly routed source remains
pending, every pending row identifies competing destinations and an exact
routing decision, continued content-level monitoring is recorded on the
accountable work item, and every changing source that independently warrants
recurring checks carries the configured source-monitoring state. Project
interfaces are generated views of these authorities and do not become separate
tracking records.

## Source Inventory and Stable Identity

Every project must configure one relied-upon source catalog for distinct
external sources affirmatively used to support factual, legal, historical,
procedural, monitoring, or analytical assertions. The cited record must
identify the stable source ID, the proposition or question supported, and an
accountable content, candidate, or research owner.

A source may be captured before full verification. Use its review state to
distinguish capture from verification. Topical similarity, bookmarking, or raw
intake does not establish reliance. Retain a source in the pending-routing
catalog only while a real choice among accountable destinations remains
unresolved; once an owner is clear, cite it in that owner's record and move it
to the relied-upon catalog even when verification or development remains
incomplete.

Every retained external source has one inventory home. Large discovery
catalogs, routing ledgers, preliminary-candidate tables, and generated
worklists are temporary queues, not parallel source registries. Source
identifiers are permanent and must never be reassigned or renumbered; allocate
above the highest identifier rather than filling a gap.

Repository placement does not establish bibliographic status and reliance does
not require committing a local copy. When a cited locator changes, refresh any
affected project-location reference in the source inventory.

## Monitoring Metadata

Use source-level monitoring only for a changing external record such as a live
docket, rolling official page, or maintained dataset. A fixed opinion, filing,
report, article, or archived instrument remains static even when its broader
subject is active. Every monitored source identifies the change being watched,
a human-readable group, and any validated deterministic baseline. Do not
silently accept a missing baseline during an ordinary scheduled run.

Source-level monitoring is independent of issue-level workflow monitoring. It
does not by itself place an issue on hold or create a human action item.

A project may maintain a separate completeness or screening registry for a
defined source universe. Such a registry records discovery and disposition; it
does not become a third bibliographic catalog or establish evidentiary reliance.
When a screened item becomes relied-upon evidence, cross-reference its one
stable source-catalog record.
