---
title: "Supplemental Evidence Record Template"
dependencies:
  - "../source-records.md"
print_status: excluded
print_exclusion_reason: "Internal drafting template."
---

# Supplemental Evidence Record Template

Use this structure only after the
[source-record standard](../source-records.md#routing-and-qualitative-placement)
determines qualitatively that the canonical content already contains
sufficiently strong evidence and additional material warrants reader-facing
treatment outside that concise record. No source-count or episode-count
threshold applies. Replace bracketed instructions, omit empty optional
sections, and keep the page organized by institutional mechanism or
manifestation rather than by source order. The canonical content must contain a
short link to the evidence record. Replace the generic metadata below with the
project's configured identifiers, paths, and publication disposition.

```markdown
---
record_id: RECORD-000
title: "RECORD-000 Evidence Record"
record_type: evidence
canonical_record: "<relative path to canonical content>"
last_evidence_review: YYYY-MM-DD
# Add the project-configured publication metadata here.
---

# RECORD-000 Evidence Record

This page supplements [the canonical content record](<relative path>). The canonical record remains authoritative for the diagnosis, remedy, proposal, score, and conclusions.

## Record Scope

[One short paragraph defining what this evidence record includes and excludes. State distinct-episode and source-record counts only when useful.]

## Verified Manifestations

### [Mechanism or manifestation]

- **[Date — concise episode label].** [Neutral description of the verified event, legal posture, and evidentiary significance, with nearby primary or official citations.]

## Judicial and Official Dispositions

- **[Case or official finding].** [State whether the matter reached the merits, was resolved on a threshold ground, remains open, was later modified, or supplies a comparator. Do not equate denial of interim relief with final approval.]

## Comparators and Counterexamples

- **[Comparator].** [Explain briefly why it narrows, tests, or contradicts the proposed pattern.]

## Monitoring Items

- **[Matter].** [State the exact event or document that will trigger renewed review.]

## Source Note

All retained external materials are registered in the project's relied-upon source catalog. This page selects evidence for reader use and does not reproduce that catalog.
```

An evidence record does not receive an independent proposal score, audit run,
diagnosis, or remedy. Do not create one merely because an intake routed
evidence to content. A stronger or necessary source belongs in the canonical
content. Additional material belongs on a reader-facing evidence page only when
separate treatment adds meaningful clarity, organization, or monitoring value;
otherwise, retained source-development material belongs in the internal
source-development record and relied-upon source catalog. Adding corroboration
that leaves the content theory unchanged is source development; changing the
diagnosis, scope, or remedy remains subject to the ordinary change-control
rules. If the receiving content is undeveloped or the episode still requires
verification, create or use its internal source-development shell, cite the
source there, and express incomplete verification through the source record
rather than the pending-routing catalog. The pending catalog is reserved for
sources whose accountable destination is genuinely unclear.
