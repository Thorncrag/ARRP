---
title: "Issue Evidence Record Template"
print_levels:
  - full-technical
---

# Issue Evidence Record Template

Use this structure only when the [source-adjudication standard](METHODOLOGY.md#automated-source-adjudication-and-issue-evidence-records) calls for a separate evidence record. Replace bracketed instructions, omit empty optional sections, and keep the page organized by institutional mechanism or manifestation rather than by source order.

```markdown
---
issue_id: ISSUE-000
title: "ISSUE-000 Evidence Record"
record_type: issue-evidence
canonical_issue: "../issues/ISSUE-000.md"
last_evidence_review: YYYY-MM-DD
print_levels:
  - public-proposal
  - full-technical
---

# ISSUE-000 Evidence Record

This page supplements [ISSUE-000 — Precise Issue Title](../issues/ISSUE-000.md). The issue page remains authoritative for the diagnosis, remedy, legislation, score, and conclusions.

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

All retained external materials are registered in [`inventory/sources.csv`](../../../inventory/sources.csv). This page selects evidence for reader use and does not reproduce the source inventory.
```

An evidence record does not receive a proposal score, audit run, independent remedy, or separate GitHub proposal issue. Adding corroboration that leaves the issue theory unchanged is source development; changing the diagnosis, scope, or remedy remains subject to the ordinary Change Audit rules.
