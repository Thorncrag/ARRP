---
title: "ARRP Governance Change Recording"
status: active
authority_scope: "Public-safe provenance recording for material ARRP governance decisions."
load_when: "Recording, reconciling, or reading a material project-governance decision, its public provenance, supersession, validation, or activation posture."
dependencies:
  - "../../FRAMEWORK.md"
  - "../../component-registry.json"
  - "../../standards/audits/change-audits.md"
  - "project-update.md"
print_status: excluded
print_exclusion_reason: "Internal governance and provenance workflow."
---

# ARRP Governance Change Recording

This workflow governs the public-safe Governance Change Log and its registry.
The log records material adoption, revision, supersession, validation, and
activation posture. It is provenance only: the governing document remains the
current-rule authority, and Git remains the exact-diff authority.

## When to record

Create or revise a `GOV-YYYY-NNN` entry when a change materially adopts,
revises, retires, supersedes, or proposes a cross-project governance boundary,
including a disclosure, runtime, incident, workflow, interface, publication,
or public-input policy boundary. Do not record routine implementation commits,
generated-view refreshes, ordinary operational state, or Console-only user
interface refinements unless they change a governing boundary.

The stable identity is allocated in
[`governance-change-registry.json`](governance-change-registry.json). Its
matching heading in the
[`Governance Change Log`](../../logs/governance/governance-change-log.md)
is the reader-facing entry. One coherent decision may cite multiple commits or
pull requests; unrelated decisions must have separate entries.

## One primary record and cross-reference rule

Each fact has one primary record. The Governance Change Log is the primary
public-safe record for a material governance decision's stable identity,
meaning, adoption posture, supersession, validation posture, and activation
posture. The governing document remains the primary current-rule authority.
Git remains the primary exact-diff and commit-history authority.

The Console Development Log records only the Console product consequence of a
governance change: for example, a new selector, projection, route, bounded
owner-mode behavior, or user-visible unavailable state. It must cite the GOV
identity and link to its authority rather than restating the decision,
evidence, activation posture, or protected context. Change Audits remain the
primary records for audit method, findings, scoring, rebaseline, and reviewed
content; issue, candidate, source, and other product histories retain their
own substantive records. A cross-reference is not a second record, count, or
narrative copy.

When one implementation affects several authorities, record it in each
primary record only for the fact that record owns and use stable identifiers to
link the others. Do not duplicate protected material while cross-referencing.

## Required public fields

Every entry must state:

1. stable GOV identity and concise title;
2. decision date and status (`Canonical`, `Proposed / unmerged`,
   `Proposed / not adopted`, `Superseded`, or `Retired`);
3. public-safe decision statement and affected authority families;
4. exact Git evidence, including full commit identities and, when available,
   pull-request evidence;
5. supersession or relationship to earlier GOV entries;
6. validation evidence or a precise statement that validation remains pending;
7. policy-adoption posture separately from live-activation posture; and
8. whether a restricted owner-local supplement is required.

The registry additionally requires a decision class plus compact `authority`,
`source`, `destination`, `resolution`, and `consumer` metadata. These fields
make the entry's current-rule authority, evidence origin, public record,
disposition, and required readers deterministic without turning the registry
into a second narrative ledger.

`Canonical` means the decision is present on canonical history, not that a
host control, private policy, scheduler, or runtime is active. `Proposed /
unmerged` is reserved for a proposal not yet present on canonical history; a
proposal preserved on canonical history without the exact required approval
is `Proposed / not adopted`. A live-activation field may never be inferred
from a merge, test result, staged file, or availability of credentials.

## Public-safety boundary

The log and registry may retain only a safe abstract description, public
authority names, opaque safe identifiers, commit and pull-request identities,
and validation names or outcomes. They must not include security incident
records or counts, credentials, private paths or topology, detector details,
affected components, vulnerability conditions, raw evidence, protected
references, private projection bindings, or host-control instructions.

When a decision needs restricted provenance, mark the entry as requiring an
owner-local supplement without naming its contents or location. The supplement
is governed by the applicable owner-local authority and is never created,
copied, or activated by this workflow.

## Protected supplement contract

A required supplement is one append-only owner-local record with the same
`GOV-YYYY-NNN` identity and a matching `GOVSUP-YYYY-NNN` event identity. It
binds to the exact public-entry SHA-256 digest and retains protected decision
context plus opaque protected and validation references. It does not become a
second governance authority, alter the public entry, activate a policy, or
authorize a runtime change. A correction receives a later GOV entry rather
than rewriting either record.

The supplement schema is
[`governance-change-supplement.schema.json`](../automation/schemas/governance-change-supplement.schema.json).
Only its separately reviewed `safe_summary`, stable GOV identity, public-entry
digest, recorded time, and Console source revision may enter an exact-bound
owner Console. Decision context, provenance, protected references, validation
references, private paths, counts, and evidence never enter the Console
projection or GitHub. Missing, malformed, duplicate, incomplete, or
digest-mismatched required supplements are unavailable, never an empty or
healthy result.

## Relationship to Change Audits and closeout

The Governance Change Log does not replace a Change Audit, issue audit history,
Console Development Log, GitHub workflow record, or the historical
[`Change Audit Log`](../../logs/audits/change-audit-log.md). A GOV entry
must link to an applicable Change Audit when one is required, but it does not
create an audit run, change a score, alter a rubric, or clear a rebaseline
marker.

At project-update closeout, reconcile each material governance decision with
its authoritative document, registry entry, log heading, Git evidence,
supersession statement, validation, and activation posture. Preserve historical
entries; correct an error with a later entry or explicitly labeled correction,
never by silently rewriting prior provenance.
