---
title: "Issue-Page Architecture and Concision"
status: active
authority_scope: "Required analytical functions, section order, Issue Snapshot, proposal links, budget statements, adjacent-proposal treatment, and issue-level concision."
load_when: "Creating, developing, restructuring, materially revising, or checking a canonical issue page or its alignment with a proposal vehicle."
dependencies:
  - "../../FRAMEWORK.md"
  - "scope-and-admission.md"
  - "neutrality-and-language.md"
  - "../sources/claims-and-citations.md"
  - "remedies.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Issue-Page Architecture and Concision

## Authority and Dependencies

This file is the authoritative reusable standard for canonical issue-page
architecture. The adopting project's guiding principle and human-authority
boundary control. Apply
[`scope-and-admission.md`](scope-and-admission.md) to issue identity and scope,
[`neutrality-and-language.md`](neutrality-and-language.md) to prose,
[`../sources/claims-and-citations.md`](../sources/claims-and-citations.md) to
support, and [`remedies.md`](remedies.md) to remedy classification. Exact
quality-summary fields, fiscal disclaimers, and additional adopted
classifications belong in the project profile.

## Load When

Load this file when creating, developing, restructuring, or materially revising an issue page; drafting its Issue Snapshot, budget statement, proposal survey, or proposal links; checking issue-to-vehicle alignment; or reviewing whether a page is developed enough for the next maturity gate.

## Mandatory Issue Architecture

Every developed issue should use the following structure:

1. **Issue Snapshot** — a short reader-navigation box summarizing problem, repair, and vehicle.
2. **Institutional Anomaly** — a concise, generalized statement of the structural defect.
3. **Manifestation of the Failure** or **Manifestations of the Failure** — titled representative instances or categories showing only the facts necessary to show how the defect operates; use the singular or plural form according to the section's contents.
4. **Resulting Damage** — the principal institutional, legal, factual, administrative, or legitimacy harm.
5. **Underlying Weakness** — the law, structure, procedure, remedy, or norm that failed.
6. **Proposal Survey** — concise review of prior or adjacent models bearing on the remedy.
7. **Least-Complex Adequate Remedy** — the least-complex measure or package capable of adequately addressing the defect.
8. **Repair and Prevention** — restoration or correction of existing damage and prospective safeguards against recurrence.
9. **Proposed Legislation** — link to the proposed legislative, rule, constitutional, or procedural vehicle when one exists. For amendment-dependent issues, use **Proposed Constitutional Amendment** and **Proposed Enabling Legislation** instead.
10. **Budgetary Impact Statement** — a concise preliminary fiscal
    classification using the adopted project rubric.
11. **Quality Review Summary** — a succinct reader-facing summary using the
    project-configured heading and fields, with a link to the preserved full
    audit-history record.
12. **Annotation** — evidence, legal analysis, qualifications, alternatives, and implementation constraints.

The headings guide analysis but do not require artificial expansion. Each section should add a distinct proposition.

The **Manifestation of the Failure** section should use short `###` instance
titles, such as `### Example actor or episode` or `### Functional category of
failure`. Use one titled instance even when the page currently has only one
principal manifestation. Where the section discusses both general mechanisms
and concrete episodes, separate them into titled subsections rather than
leaving untitled paragraphs. Titles should be descriptive, neutral, concise,
and supported by the text that follows.

Custom section headings are permitted where they make a developed issue clearer or more natural to read, provided the issue still performs the required analytical functions. A custom heading should be meaningfully distinct from the canonical heading it replaces rather than a trivial restatement. Where custom headings are used, the required function should remain clear from the heading itself, the surrounding structure, or a short orienting sentence.

## Proposal-Vehicle Presentation

Where proposed legislation or another concrete reform vehicle exists, the issue page should include a **Proposed Legislation** section immediately after **Repair and Prevention**. **Repair and Prevention** and **Proposed Legislation** should appear after **Least-Complex Adequate Remedy**, so the page first compares available models and identifies the preferred remedy before presenting the repair frame and concrete vehicle. Proposed vehicles should always be presented as a Markdown bullet list, even when there is only one linked item.

Where a proposal requires a constitutional amendment and separate implementing legislation, the issue page should use **Proposed Constitutional Amendment** for the amendment page and **Proposed Enabling Legislation** for the implementing statute. Both sections should appear as Markdown bullet lists. The amendment text itself should live on its own proposal page, not inside the issue page. The enabling legislation page should identify the amendment dependency in front matter or introductory text.

Candidate or development-stage issue pages may keep a **Proposed
Legislation** section with a single project-configured placeholder when no
draft vehicle exists yet. That wording is page content, not a hosted workflow
status or a legislation-link failure. Once a concrete vehicle exists, replace
the placeholder with a linked bullet and update the Issue Snapshot vehicle
line, metadata, inventories, and hosted workflow fields if the development
status, score, last audit, or next audit changes.

Where a proposal is legally available under current law but depends on a future or amenable institutional actor for realistic adoption, the issue page may include an **Adoption Viability Note** immediately after **Proposed Legislation**, or after **Proposed Enabling Legislation** for amendment-dependent issues. The note should be concise and should distinguish legal vehicle availability from practical adoption likelihood.

Where a proposal may be confused with, overlap with, partially replace, or
depend on another project proposal, the issue page should include an optional
**Relationship to Adjacent Proposals** section after **Proposed Legislation**
or **Proposed Enabling Legislation** and any **Adoption Viability Note**, but
before **Budgetary Impact Statement**. The section should briefly identify what
the current proposal owns, what each adjacent proposal owns, whether there is
partial overlap or merger, and whether the adjacent proposal complements or
replaces the current remedy.

When an issue uses a shared remedy or presents a separately enactable
alternative, apply the [Shared Remedies and Independent
Alternatives](remedies.md#shared-remedies-and-independent-alternatives) rules.

## Issue-to-Vehicle Alignment

The issue page and its linked proposed legislation, constitutional amendment text, enabling legislation, or other proposal vehicle must remain substantively aligned. When either page changes, the next framework, drafting, or project-integration audit should cross-check the Issue Snapshot vehicle, Least-Complex Adequate Remedy, Repair and Prevention, Proposed Legislation or amendment/enabling sections, Annotation, and Proposal Scoring summary against the linked legislative, constitutional, rule, or procedural text. The check should confirm that the issue page still accurately describes the vehicle, covered actors, legal hook, remedy type, enforcement mechanism, deadlines, responsible institutions, scope limits, and material drafting notes. If an audit discovers a substantive discrepancy, document it and reconcile the records when the correction remains within the human-approved foundation. Request human review only when reconciliation would alter a reserved foundation, materially contract the approved proposal, or make another change reserved by the human-governed foundation rule.

## Budgetary Impact Statement

Every developed issue page and every proposal page should include a
**Budgetary Impact Statement** before **Annotation** on issue pages and before
**Drafting Notes** on legislation or proposal pages. An issue page presenting
a preferred shared-remedy path and a separately enactable alternative must
instead use **Budgetary Impact Statements** with two separately labeled
subsections, one for each path. The statements are preliminary project
planning classifications, not official fiscal scores. They must be short,
source-conscious, and must not include a dollar figure unless the figure is
tied to a cited government source, historical appropriation, official fiscal
score, agency budget material, audited program cost, or comparable
source-backed basis. The substantive classification should appear first. A
project-configured disclaimer may follow the statement or both subsections.

Use one of the following baseline classifications unless a source-backed estimate justifies a narrower formulation:

- `No direct appropriation is anticipated.`
- `Administrative workload is possible; no new appropriation is specified.`
- `Budget authority is likely required; no dollar estimate is assigned pending source-backed cost data.`
- `Not estimated pending proposal development.`
- `No direct appropriation is anticipated for the amendment itself; implementing legislation may have costs.`

When a proposal authorizes appropriations or clearly requires new funded capacity, use the budget-authority classification unless a tighter source-backed range is available. When a proposal is a constitutional amendment, distinguish the amendment itself from later implementing legislation.

## Issue Snapshot Format

Each developed issue page should place an **Issue Snapshot** blockquote immediately after the issue title and before **Institutional Anomaly**. The snapshot is a reader-navigation device: it should let a reader move quickly from problem to proposed solution without reading the full issue page first.

The Issue Snapshot should be extremely concise. Each line should normally
convey its point in about twelve words or fewer. To render consistently across
supported Markdown previews, keep the snapshot fields in a single blockquote
paragraph and separate **Problem**, **Repair**, and **Vehicle** with inline
`<br />` tags:

1. **Problem:** the institutional weakness.
2. **Repair:** the core proposed fix.
3. **Vehicle:** the legal or institutional form of the remedy, with a relative Markdown link to proposed legislation or amendment text where a draft exists.

Use this format:

```markdown
> ## Issue Snapshot
> **Problem:** Short problem statement.<br />**Repair:** Short repair statement.<br />**Vehicle:** Remedy vehicle ([draft link]).
>
```

## Proposal Survey

Each developed issue should include a concise survey of prior legislative, regulatory, constitutional, procedural, or institutional models that bear on the proposed remedy. The survey should identify the closest models, cite or link them, and explain why the project adopts, narrows, rejects, or combines them. It should appear before **Least-Complex Adequate Remedy** so the preferred remedy follows the comparison.

## Issue-Level Conciseness

Conciseness is an area-level and issue-level constraint, not an overall document-length limit. Each issue should be stated in the minimum space necessary to identify the defect, damage, weakness, repair, prevention, and remedy. Additional detail belongs in annotation or source notes.

Representative incidents should illustrate the structural defect, not become exhaustive narrative histories.
