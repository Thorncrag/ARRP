---
title: "Annotation, Claims, and Source Standards"
status: active
authority_scope: "Annotation structure, assertion discipline, source hierarchy, nearby citations, claim qualification, and prosecutorial-source limits."
load_when: "Drafting or revising factual, legal, causal, fiscal, polling, implementation, or scoring claims; adding annotations; selecting sources; or checking citation sufficiency."
dependencies: "../FRAMEWORK.md; ../methodology/neutrality-and-language.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Annotation, Claims, and Source Standards

## Authority and Dependencies

This file is the authoritative detailed standard for project annotations, claims, and evidentiary support. The guiding principle and truthfulness obligations in [`../FRAMEWORK.md`](../FRAMEWORK.md) control. Apply [`../methodology/neutrality-and-language.md`](../methodology/neutrality-and-language.md) to characterization and [`../sources/source-catalogs.md`](../sources/source-catalogs.md) to source registration, ownership, review state, and monitoring metadata.

## Load When

Load this file whenever project-authored factual, legal, causal, historical, fiscal, polling, implementation, or scoring claims are drafted or revised; annotations are added or reorganized; sources are selected; or citation sufficiency and claim status are reviewed.

## Annotation and Evidence

### Standard Annotation

Each annotation segment should begin with a bold inline title followed by a period, then the paragraph text.

**Basis and Evidence.** Explain why the anomaly has been identified and cite representative authoritative support.

**Qualification.** State material uncertainty, competing interpretations, and limits necessary to keep the main assertion accurate.

**Remedial Alternatives and Constraints.** Briefly identify materially serious fallback options and the constitutional, statutory, administrative, or practical limits affecting the least-complex remedy.

**Budgetary Impact.** Explain any fiscal, workload, or implementation-burden classification that needs more support than the short Budgetary Impact Statement can provide.

Scoring annotations should mirror the labels used in the **Proposal Scoring** box where practical. Use **Quality Score**, **Adoption Score**, **Coalition Support Estimates**, **Adoption Friction**, **Required Electoral Environment**, and **Development Priority** as needed. Place these scoring annotation segments after **Budgetary Impact** when they appear, so score explanations can incorporate fiscal, implementation, adoption, friction, and readiness findings without crowding the Proposal Scoring box.

When the **Proposal Scoring** box includes **Coalition Support Estimates**, follow the compact display and caveat-placement rules in [`../audits/AUDIT_CORE.md`](../audits/AUDIT_CORE.md#audit-output). This file remains authoritative for the matching annotation's evidentiary explanation; Audit Core remains authoritative for the box format.

### Assertion Discipline

State each institutional conclusion as directly as the record permits. An annotation must substantiate rather than retreat from the main assertion. Distinguish established fact, legal conclusion, institutional inference, and normative judgment.

### Source Standard

Use primary legal and governmental records first. Use authoritative institutional and academic sources for doctrine, design, and comparative analysis. Use high-quality secondary reporting mainly for synthesis and discovery.

Every factual, legal, and causal proposition must remain independently supportable. When an issue file refers to a real-life event, case, official action, report, statute, rule, hearing, order, or other source material, include a nearby citation or link. Do not name concrete examples in issue text without enough source information for later verification.

Indictments, criminal complaints, informations, prosecutorial reports, press releases describing charges, and comparable advocacy-position records may be used to identify alleged fact patterns, procedural posture, source leads, and potential institutional weaknesses. They must not be used as evidentiary support for the truth of an allegation unless the project separately verifies the allegation through specific cited evidence, admitted records, judicial findings, official records, or other reliable corroboration. When used, label them as allegations, prosecution assessments, charging documents, or source-development leads rather than adjudicated facts.

Source inventory updates are required whenever a new external source is affirmatively relied upon or an existing source is repurposed for a materially different proposition. [`../../inventory/sources.csv`](../../inventory/sources.csv) is the relied-upon source registry; a source may remain marked `Reviewed?` as `No` when the project carefully attributes a provisional assertion or monitoring posture, but the supported proposition and verification status must remain clear. [`../../inventory/sources-pending.csv`](../../inventory/sources-pending.csv) is only a temporary routing queue for retained sources whose accountable destination cannot yet be selected with confidence. Once an existing proposal, undeveloped proposal, formal candidate, preliminary candidate, or project-authored research record clearly owns the source, cite it in that record, move its stable row into `sources.csv`, and preserve incomplete verification through `Reviewed?`, Notes, or a defined monitoring field rather than leaving it pending.

When referring to another page in this project, use a relative Markdown link whenever the target page exists. If the referenced issue exists only as an inventory or area-index entry, link to the nearest project page that contains that entry.
