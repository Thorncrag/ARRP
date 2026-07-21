---
title: "Issue Evidence Record Template"
print_levels:
  - full-technical
---

# Issue Evidence Record Template

Use this structure only after the [source-adjudication standard](../METHODOLOGY.md#automated-source-adjudication-and-issue-evidence-records) determines qualitatively that the issue page already contains sufficiently strong evidence and additional material warrants reader-facing treatment outside the concise issue page. No source-count or episode-count threshold applies. Replace bracketed instructions, omit empty optional sections, and keep the page organized by institutional mechanism or manifestation rather than by source order. The canonical issue page must contain a short link to the evidence record.

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

An evidence record does not receive a proposal score, audit run, independent remedy, or separate GitHub proposal issue. Do not create one merely because an intake routed evidence to an issue. A stronger or necessary source belongs on the issue page. Additional material belongs on a reader-facing evidence page only when separate treatment adds meaningful clarity, organization, or monitoring value; otherwise, retained source-development material belongs in the issue's internal source-development record and [`inventory/sources.csv`](../../inventory/sources.csv). Adding corroboration that leaves the issue theory unchanged is source development; changing the diagnosis, scope, or remedy remains subject to the ordinary Change Audit rules. If the receiving issue is undeveloped or the episode still requires verification, create or use its internal full-technical source-development shell, cite the source there, and express incomplete verification through the source record rather than the pending queue. [`inventory/sources-pending.csv`](../../inventory/sources-pending.csv) is reserved for sources whose accountable destination is genuinely unclear.
