---
title: "American Restoration and Resilience Project — Technical Framework"
print_levels:
  - full-technical
---

# American Restoration and Resilience Project — Technical Framework

This file contains the project's technical operating framework: method, issue architecture, evidence standards, remedy standards, repository structure, file conventions, print assembly, contribution process, release process, and canonical development backlog.

The project's public-facing premise, mission, scope, and governing principles are maintained in [`../README.md`](../README.md).

## Canonical Roadmap and Backlog

The only canonical project roadmap, backlog, and to-do list is the [`Outstanding Development`](#outstanding-development) section of this file. Other project files may describe local context or link here, but should not maintain separate roadmap, backlog, or to-do lists.

## Core Method

**Identify the problem.** Determine what institution or governing process failed, how the failure manifested, and what damage resulted.

**Identify the weakness.** Determine which law, structure, procedure, remedy, or norm permitted the failure or proved inadequate to constrain it.

**Identify repair and prevention.** Determine what must be restored or corrected now and what safeguards are necessary to prevent recurrence.

**Identify the least-complex adequate remedy.** Determine the least-complex measure, or package of measures, capable of adequately addressing the defect.

## Issue-Admission Test

Before promoting a candidate into a standalone issue, ask:

> Does this candidate identify a distinct institutional weakness requiring separate diagnosis or remedial analysis?

If not, merge it into a broader issue, treat it as a manifestation or example, cross-reference it, or retain it only in the research inventory.

## Unit of Analysis

Each issue must identify a generalized structural defect. Trump-era or other-administration incidents illustrate the defect but do not define it.

## Mandatory Issue Architecture

Every developed issue should use the following structure:

1. **Issue Snapshot** — a short reader-navigation box summarizing problem, repair, and vehicle.
2. **Institutional Anomaly** — a concise, generalized statement of the structural defect.
3. **Manifestation of the Failure** — only the representative facts necessary to show how the defect operates.
4. **Resulting Damage** — the principal institutional, legal, factual, administrative, or legitimacy harm.
5. **Underlying Weakness** — the law, structure, procedure, remedy, or norm that failed.
6. **Proposal Survey** — concise review of prior or adjacent models bearing on the remedy.
7. **Least-Complex Adequate Remedy** — the least-complex measure or package capable of adequately addressing the defect.
8. **Repair and Prevention** — restoration or correction of existing damage and prospective safeguards against recurrence.
9. **Proposed Legislation** — link to the proposed legislative, rule, constitutional, or procedural vehicle when one exists.
10. **Budgetary Impact Statement** — a concise preliminary fiscal classification using the project rubric.
11. **Proposal Scoring** — a succinct audit and scoring box showing the proposal-quality score, audit status, rubric version, rebaseline status, Required Electoral Environment, Development Priority, Adoption Friction, next audit need, and a link to the sibling full audit-history file.
12. **Annotation** — evidence, legal analysis, qualifications, alternatives, and implementation constraints.

The headings guide analysis but do not require artificial expansion. Each section should add a distinct proposition.

Custom section headings are permitted where they make a developed issue clearer or more natural to read, provided the issue still performs the required analytical functions. A custom heading should be meaningfully distinct from the canonical heading it replaces rather than a trivial restatement. Where custom headings are used, the required function should remain clear from the heading itself, the surrounding structure, or a short orienting sentence.

Where proposed legislation or another concrete reform vehicle exists, the issue page should include a **Proposed Legislation** section immediately after **Repair and Prevention**. **Repair and Prevention** and **Proposed Legislation** should appear after **Least-Complex Adequate Remedy**, so the page first compares available models and identifies the preferred remedy before presenting the repair frame and concrete vehicle. Proposed vehicles should always be presented as a Markdown bullet list, even when there is only one linked item.

Every developed issue page and every proposal page should include a **Budgetary Impact Statement** before **Annotation** on issue pages and before **Drafting Notes** on legislation or proposal pages. The statement is a preliminary ARRP planning classification, not an official fiscal score. It must be short, source-conscious, and must not include a dollar figure unless the figure is tied to a cited government source, historical appropriation, CBO score, agency budget material, audited program cost, or comparable source-backed basis.

Use one of the following baseline classifications unless a source-backed estimate justifies a narrower formulation:

- `Preliminary ARRP assessment only; not a CBO, OMB, agency, or legislative-counsel score. No direct appropriation is anticipated.`
- `Preliminary ARRP assessment only; not a CBO, OMB, agency, or legislative-counsel score. Administrative workload is possible; no new appropriation is specified.`
- `Preliminary ARRP assessment only; not a CBO, OMB, agency, or legislative-counsel score. Budget authority is likely required; no dollar estimate is assigned pending source-backed cost data.`
- `Preliminary ARRP assessment only; not a CBO, OMB, agency, or legislative-counsel score. Not estimated pending proposal development.`
- `Preliminary ARRP assessment only; not a CBO, OMB, agency, or legislative-counsel score. No direct appropriation is anticipated for the amendment itself; implementing legislation may have costs.`
- `Preliminary ARRP assessment only; not a CBO, OMB, agency, or legislative-counsel score. Budget authority may be required if the chosen remedy funds postage, tracking, or election-administration support; no dollar estimate is assigned pending source-backed cost data.`

When a proposal authorizes appropriations or clearly requires new funded capacity, use the budget-authority classification unless a tighter source-backed range is available. When a proposal is a constitutional amendment, distinguish the amendment itself from later implementing legislation.

### Issue Snapshot Format

Each developed issue page should place an **Issue Snapshot** blockquote immediately after the issue title and before **Institutional Anomaly**. The snapshot is a reader-navigation device: it should let a reader move quickly from problem to proposed solution without reading the full issue page first.

The Issue Snapshot should be extremely concise. Each line should normally convey its point in about twelve words or fewer. To render consistently in both GitHub and Codex previews, keep the snapshot fields in a single blockquote paragraph and separate **Problem**, **Repair**, and **Vehicle** with inline `<br />` tags:

1. **Problem:** the institutional weakness.
2. **Repair:** the core proposed fix.
3. **Vehicle:** the legal or institutional form of the remedy, with a relative Markdown link to proposed legislation or amendment text where a draft exists.

Use this format:

```markdown
> ## Issue Snapshot
> **Problem:** Short problem statement.<br />**Repair:** Short repair statement.<br />**Vehicle:** Remedy vehicle ([draft link]).
>
```

### Proposal Survey

Each developed issue should include a concise survey of prior legislative, regulatory, constitutional, procedural, or institutional models that bear on the proposed remedy. The survey should identify the closest models, cite or link them, and explain why the project adopts, narrows, rejects, or combines them. It should appear before **Least-Complex Adequate Remedy** so the preferred remedy follows the comparison.

## Issue-Level Conciseness

Conciseness is an area-level and issue-level constraint, not an overall document-length limit. Each issue should be stated in the minimum space necessary to identify the defect, damage, weakness, repair, prevention, and remedy. Additional detail belongs in annotation or source notes.

Representative incidents should illustrate the structural defect, not become exhaustive narrative histories.

## Annotation and Evidence

### Standard Annotation

**Basis and Evidence.** Explain why the anomaly has been identified and cite representative authoritative support.

**Qualification.** State material uncertainty, competing interpretations, and limits necessary to keep the main assertion accurate.

**Remedial Alternatives and Constraints.** Briefly identify materially serious fallback options and the constitutional, statutory, administrative, or practical limits affecting the least-complex remedy.

### Assertion Discipline

State each institutional conclusion as directly as the record permits. An annotation must substantiate rather than retreat from the main assertion. Distinguish established fact, legal conclusion, institutional inference, and normative judgment.

### Source Standard

Use primary legal and governmental records first. Use authoritative institutional and academic sources for doctrine, design, and comparative analysis. Use high-quality secondary reporting mainly for synthesis and discovery.

Every factual, legal, and causal proposition must remain independently supportable. When an issue file refers to a real-life event, case, official action, report, statute, rule, hearing, order, or other source material, include a nearby citation or link. Do not name concrete examples in issue text without enough source information for later verification.

When referring to another page in this project, use a relative Markdown link whenever the target page exists. If the referenced issue exists only as an inventory or area-index entry, link to the nearest project page that contains that entry.

## Least-Complex Adequate Remedy

The Least-Complex Adequate Remedy is mandatory in every developed issue and functions as the project’s provisional preferred remedy.

Complexity should be assessed by legal difficulty, administrative burden, implementation speed, enforceability, durability, cost, and need for constitutional change. Simplicity is not sufficient where the simpler measure would be ineffective, temporary, unenforceable, or easily evaded.

The main text need not catalogue every conceivable remedy. It should identify the least-complex adequate measure or package and explain why it is adequate. Annotation should briefly note materially simpler but insufficient options and more complex fallback options that may be necessary for completeness, durability, or constitutional reasons.

Adequacy should be evaluated against the remedy’s proper function. Where prevention is feasible, the remedy should prevent. Where necessary discretion or constitutional structure makes complete prevention impracticable, adequacy may instead require reliable detection, evidence preservation, independent review, mandatory reporting, correction, discipline, compensation, legislative response, or another credible self-corrective mechanism.

The assessment remains provisional rather than irrevocable and may be revised as the record develops.

## Repair and Prevention

Every issue must consider both repair and prevention. Some issues may require restoration, investigation, disclosure, recovery, correction of the public record, rebuilding of capacity, or compensation. Prevention may require substantive legal limits, structural independence, professional safeguards, oversight, enforcement, transparency, procedural reform, or constitutional change.

The distinction is mandatory to consider but need not receive equal prose where one side is not materially relevant. Issues should also identify whether the proposed safeguard primarily prevents, detects, corrects, deters, or contains institutional abuse.

## Constitutional Amendments

Constitutional amendments are within scope and must not be excluded. Adequate non-amendment remedies should generally receive greater emphasis because Article V is unusually difficult and slow. Amendment options must nevertheless be preserved where lesser measures cannot lawfully, completely, or durably solve the problem.

## Automatic Constitutional Stabilizers and Institutional-Failure Triggers

A constitutional system should not permit persistent failure of essential governing processes to continue indefinitely without changing the legal allocation of power.

Trigger mechanisms are a limited, cross-cutting remedial tool. They may include mandatory notice, fixed deadlines, compulsory votes, expiration of temporary authority, caretaker succession, expedited review, temporary contraction of discretionary authority, or constitutional mechanisms for extraordinary cumulative failure.

Triggers are not a universal solution and do not organize or subsume the rest of the project. Apply them only where persistent institutional failure can be addressed through objective, measurable, proportionate, manipulation-resistant escalation or reallocation mechanisms. Many issues will instead require substantive limits, structural independence, disclosure, professional safeguards, enforcement, oversight, funding reform, or constitutional change.

## Overlap and Cross-Reference Rule

Each institutional defect should have one primary home. Related areas should cross-reference the primary issue instead of repeating the same diagnosis, evidence, and remedy. The issue inventory may identify related areas without creating duplicate substantive sections.

## Proposal Quality Audit

Before an issue or proposal is treated as ready for external circulation, it should undergo a quality audit assessing issue definition, legal authority, source support, proposal survey, remedy adequacy, abuse resistance, political adoption prospects, drafting clarity, and integration with the project inventory.

The canonical audit rules, resource tiers, Horizon Scan procedure, hallucination-resistance protocol, scoring formula, adoption-score formula, international-support score, output requirements, and audit-preservation rules are maintained in [`../inventory/METHOD.md`](../inventory/METHOD.md#audit-rules-and-proposal-quality-scoring).

Every issue should have a corresponding row in [`../inventory/audits.csv`](../inventory/audits.csv). That row records the current proposal-quality score, audit count, audit status, score basis, next audit need, audit-rubric version, rebaseline status, Required Electoral Environment, Development Priority, and Adoption Friction Score where assessed. The relevant issue page should contain a compact **Proposal Scoring** summary, and its full technical audit history should be maintained in a sibling `ISSUE-ID.audit.md` file linked from that section. [`../AUDIT_DASHBOARD.md`](../AUDIT_DASHBOARD.md) provides the compact cross-issue view. Scores should not be compared across different rubric versions without noting the rebaseline status. Adoption Friction should not be treated as part of the Proposal Quality Score, while the Required Electoral Environment should feed Adoption and Implementation scoring under the audit rubric.

## Repository Architecture

- [`../README.md`](../README.md) contains the public-facing proposal front matter, including the reader notice, foundational premise, mission, scope, governing principles, rights notice, citation pointer, and technical-framework pointer.
- `framework/` contains governing methodology and cross-cutting remedial architecture.
- `areas/` contains one directory per project area and one file per developed issue.
- `legislation/` contains proposed statutory language keyed to issue identifiers.
- `inventory/` contains structured area, issue, audit, source, and method records.
- `research/` contains material not yet integrated into a developed issue.
- `exports/` contains generated DOCX, PDF, and XLSX editions.
- `archive/` contains superseded snapshots retained for provenance.

Markdown and CSV files are authoritative. Binary Office and PDF files are generated outputs.

## Canonical Sources

- [`FRAMEWORK.md`](FRAMEWORK.md) — technical framework, methodology, repository conventions, and development status
- [`../inventory/areas.csv`](../inventory/areas.csv) — structured area inventory
- [`../inventory/issues.csv`](../inventory/issues.csv) — structured issue inventory
- [`../inventory/contents.csv`](../inventory/contents.csv) — combined area-and-issue contents index
- [`../inventory/audits.csv`](../inventory/audits.csv) — issue-level audit status and proposal-quality scoring
- [`../inventory/sources.csv`](../inventory/sources.csv) — source-tracking table
- [`../inventory/METHOD.md`](../inventory/METHOD.md) — inventory maintenance, audit procedure, scoring rules, and Horizon Scan rules
- [`REMEDY_FRAMEWORK.md`](REMEDY_FRAMEWORK.md) — remedy categories, trigger stages, and cross-cutting remedial options
- [`../areas/`](../areas/) — modular area and issue analyses
- [`../legislation/`](../legislation/) — draft statutory and administrative language keyed to issue identifiers
- [`../AUDIT_DASHBOARD.md`](../AUDIT_DASHBOARD.md) — compact cross-issue audit tracker for meta-analysis and audit planning
- [`../AUTHORS.md`](../AUTHORS.md) — authorship statement
- [`../LICENSE.md`](../LICENSE.md) — rights and reuse notice
- [`../CITATION.cff`](../CITATION.cff) — citation metadata
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution expectations
- [`../PUBLIC_RELEASE.md`](../PUBLIC_RELEASE.md) — public release process
- [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md) — compiled-document and print assembly framework

## Working Conventions

1. Every substantive issue has a stable identifier such as `DOJ-001`.
2. The framework governs analysis; the inventory tracks it; issue files contain the substantive work.
3. Each developed issue identifies the **Least-Complex Adequate Remedy**, using [`REMEDY_FRAMEWORK.md`](REMEDY_FRAMEWORK.md) as the shared remedy taxonomy where helpful.
4. Supporting evidence, qualifications, and alternatives belong in annotation or source notes.
5. Where complete prevention is impracticable, a remedy may instead provide reliable detection, correction, deterrence, and institutional self-repair.
6. Candidate issues may be retired or merged when the issue-admission test shows substantial duplication.
7. A status such as **Awaiting merits adjudication** identifies a deliberately paused issue whose remedy depends materially on pending judicial resolution.
8. Markdown and CSV are canonical. DOCX, PDF, and XLSX files are generated exports.
9. Project updates must keep the structured inventory and audit dashboard current. When an area, issue, legislation file, audit status, quality score, or cited source is added, removed, renamed, merged, retired, or materially revised, update the relevant rows in [`../inventory/areas.csv`](../inventory/areas.csv), [`../inventory/issues.csv`](../inventory/issues.csv), [`../inventory/contents.csv`](../inventory/contents.csv), [`../inventory/audits.csv`](../inventory/audits.csv), [`../inventory/sources.csv`](../inventory/sources.csv), and [`../AUDIT_DASHBOARD.md`](../AUDIT_DASHBOARD.md) as part of the same change.
10. Source inventory updates are required whenever a new external source is cited or an existing cited source is repurposed for a materially different proposition. A source may remain marked `Reviewed?` as `No` until verification is complete, but the citation should still be captured promptly.
11. Every Markdown page must carry `print_levels` metadata under [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md#print-assignment-metadata).
12. Every audit tier must check pending judicial matters, scaled to the tier, where a pending Supreme Court, appellate, district-court, state high-court, emergency, stay, or remand posture could materially affect the proposal's authority, remedy design, urgency, scope, or issue-admission result.

## Legislation Filename Convention

Legislative proposal files use the issue identifier as the base filename.

- Federal legislative proposals use the unsuffixed issue identifier: `XXX-NNN.md`.
- Model state legislative proposals use the state suffix: `XXX-NNN-state.md`.

For issues with both federal and state proposals, the federal proposal is the unsuffixed file and the model state proposal is the `-state` file. For issues with only a model state proposal, the proposal should still use the `-state` suffix.

Examples:

- `ELEC-003.md` — federal proposal.
- `ELEC-003-state.md` — model state proposal.
- `ELEC-002-state.md` — model state proposal where no federal proposal is yet maintained.

## Current Areas

The current area inventory is maintained in [`../areas/README.md`](../areas/README.md) and [`../inventory/areas.csv`](../inventory/areas.csv). The issue inventory is maintained in [`../inventory/issues.csv`](../inventory/issues.csv).

## Developed Issues

The developed-issue list is maintained in [`../inventory/contents.csv`](../inventory/contents.csv), with source-of-truth status tracking in [`../inventory/issues.csv`](../inventory/issues.csv). Avoid duplicating the developed-issue list in prose unless the list is generated from the inventory.

## Development Phase

The project will proceed by applying this framework to retained issues, developing authoritative source records, resolving overlap through primary ownership and cross-reference, and revising the least-complex adequate remedy as legal and factual analysis matures.

## Current Status

Current issue status is maintained in [`../inventory/issues.csv`](../inventory/issues.csv) and the ordered contents scaffold in [`../inventory/contents.csv`](../inventory/contents.csv). Area README files provide the nearest human-readable issue indexes, while developed issue pages contain the substantive analysis.

The governing framework already incorporates the project-wide rules for institutional focus, politically neutral application, issue admission, mandatory issue architecture, issue-level conciseness, standardized annotations, the Least-Complex Adequate Remedy, limited use of automatic institutional-failure triggers, and cross-referencing instead of duplicative treatment.

The area and issue inventories already include A-04 Judicial Independence and Enforcement (JUD-001 through JUD-009, with JUD-002, JUD-003, JUD-004, and JUD-006 retired into JUD-001), A-05 Presidential Clemency and Pardon Power (PAR-001 through PAR-010), A-07 Classification, Declassification, and National-Security Information (CLASS-001 through CLASS-012), and A-21 Federal Reserve Independence and Monetary Policy (FRB-001 through FRB-008). The `FED` prefix remains reserved for A-20 Federalism and Presidential Coercion of States.

## Outstanding Development

The following work remains outstanding and should not be treated as an uncommitted framework revision:

- develop authoritative source records, annotations, and individual issue files for the JUD, PAR, and CLASS candidate inventories;
- analyze constitutional and implementation constraints for judicial-enforcement remedies, including appointments, appropriations, due process, and presidential control;
- analyze the constitutional limits on restricting the legal effect of presidential clemency while developing transparency, anti-corruption, review, recordkeeping, disclosure, and surrounding-liability remedies;
- preserve and source the distinctions among classification status, authorization to disclose, lawful custody or possession, and government ownership and records-preservation duties;
- develop the A-21 annotation explaining the systemic risks of sustained political subordination of monetary policy, including inflation, unanchored expectations, leverage, asset-price distortions, currency weakness, loss of credibility, and the possibility of a later severe corrective contraction;
- conduct a systematic review of each proposal's potential bipartisan support, including cross-party institutional interests, likely objections, possible neutral framing, and risks of partisan capture or misuse;
- complete the Project 2025 / ARRP crosswalk source-development pass, including official Mandate chapter records, chapter-level and major-proposal rows, page or section citations, implementation-status labels, weakness-vehicle analysis for proposals whether or not enacted or attempted, ARRP area and issue mappings, coverage-status labels, newly needed issue candidates, and area-priority review;
- build an export script to assemble compiled proposal editions, generate a table of contents, normalize heading levels, verify local links, and move proposed legislation into appendices;
- defer full page-numbered and clickable table-of-contents work until the project is more developed, then limit it to major sections, project areas, developed issues, and appendices;
- select and adopt an appropriate Creative Commons or other public reuse license when the project is ready for broader legislative and public engagement.

These are substantive research and issue-development tasks. They do not reopen the already committed governing framework or area inventories.
