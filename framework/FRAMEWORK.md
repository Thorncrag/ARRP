---
title: "American Restoration and Resilience Project — Technical Framework"
print_levels:
  - full-technical
---

# American Restoration and Resilience Project — Technical Framework

This file contains the project's technical operating framework: method, issue architecture, evidence standards, remedy standards, repository structure, file conventions, and canonical development backlog. It also points to the separate files governing print assembly, contribution expectations, public release, audit scoring, source tracking, and remedy taxonomy.

The project's public-facing premise, mission, scope, and governing principles are maintained in [`../README.md`](../README.md).

## Repository Architecture

- [`../README.md`](../README.md) contains the public-facing proposal front matter, including the reader notice, foundational premise, mission, scope, governing principles, rights notice, citation pointer, and technical-framework pointer.
- `framework/` contains governing methodology and cross-cutting remedial architecture.
- `areas/` contains one directory per project area, area README indexes, developed issue pages, and sibling issue audit-history files.
- `legislation/` contains proposed statutory, constitutional, regulatory, procedural, and model-state language keyed to issue identifiers.
- `inventory/` contains structured area, issue, contents, audit, and source records.
- [`../AUDIT_DASHBOARD.md`](../AUDIT_DASHBOARD.md) contains the compact cross-issue audit dashboard for meta-analysis and audit planning.
- [`../agent.md`](../agent.md) contains agent-assisted audit and autonomous batch-audit operating rules.
- [`../AGENT_AUDIT_LOG.md`](../AGENT_AUDIT_LOG.md) contains autonomous-agent commit provenance and rollback references.
- [`../CHANGE_AUDIT_LOG.md`](../CHANGE_AUDIT_LOG.md) contains cumulative project-wide Change Audit history.
- [`../HORIZON_SCAN.md`](../HORIZON_SCAN.md) contains cumulative horizon-scan intake, recommendations, adjudications, and integration history.
- [`../PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md) contains the repository map for human orientation.
- `research/` contains material not yet integrated into a developed issue.
- `source-development/` contains source-development work products and crosswalks not yet fully absorbed into issue pages, inventories, or proposed legislation.
- `scripts/` contains project-maintenance and export-generation scripts.
- `exports/` contains generated DOCX, PDF, and XLSX editions.
- `archive/` contains superseded snapshots retained for provenance.

Markdown and CSV files are authoritative. Binary Office and PDF files are generated outputs.

## Canonical Sources

- [`FRAMEWORK.md`](FRAMEWORK.md) — technical framework, repository conventions, and development status
- [`../inventory/areas.csv`](../inventory/areas.csv) — structured area inventory
- [`../inventory/issues.csv`](../inventory/issues.csv) — structured issue inventory
- [`../inventory/contents.csv`](../inventory/contents.csv) — combined area-and-issue contents index
- [`../inventory/audits.csv`](../inventory/audits.csv) — issue-level audit status and proposal-quality scoring
- [`../inventory/sources.csv`](../inventory/sources.csv) — source-tracking table
- [`METHODOLOGY.md`](METHODOLOGY.md) — inventory maintenance, audit procedure, scoring rules, and Horizon Scan rules
- [`REMEDY_FRAMEWORK.md`](REMEDY_FRAMEWORK.md) — remedy categories, trigger stages, and cross-cutting remedial options
- [`../areas/`](../areas/) — modular area and issue analyses
- [`../legislation/`](../legislation/) — draft statutory and administrative language keyed to issue identifiers
- [`../AUDIT_DASHBOARD.md`](../AUDIT_DASHBOARD.md) — compact cross-issue audit tracker for meta-analysis and audit planning
- [`../agent.md`](../agent.md) — agent-assisted audit and autonomous batch-audit operating rules
- [`../AGENT_AUDIT_LOG.md`](../AGENT_AUDIT_LOG.md) — autonomous-agent commit provenance and rollback references
- [`../CHANGE_AUDIT_LOG.md`](../CHANGE_AUDIT_LOG.md) — cumulative Change Audit history
- [`../HORIZON_SCAN.md`](../HORIZON_SCAN.md) — cumulative Horizon Scan intake and integration ledger
- [`../PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md) — human-readable repository map
- [`../AUTHORS.md`](../AUTHORS.md) — authorship statement
- [`../LICENSE.md`](../LICENSE.md) — rights and reuse notice
- [`../CITATION.cff`](../CITATION.cff) — citation metadata
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution expectations
- [`../PUBLIC_RELEASE.md`](../PUBLIC_RELEASE.md) — public release process
- [`../source-development/`](../source-development/) — source-development work products and crosswalks
- [`../scripts/`](../scripts/) — project-maintenance and export-generation scripts
- [`../exports/`](../exports/) — generated, non-authoritative export files
- [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md) — compiled-document and print assembly framework

## Inventory Status and Development Phase

Current area and issue status is maintained in [`../inventory/areas.csv`](../inventory/areas.csv), [`../inventory/issues.csv`](../inventory/issues.csv), and the ordered contents scaffold in [`../inventory/contents.csv`](../inventory/contents.csv). [`../areas/README.md`](../areas/README.md) and area README files provide human-readable indexes, while developed issue pages contain the substantive analysis. Do not duplicate current area lists, issue lists, or developed-issue status snapshots in this framework file unless the list is generated from the inventory.

Project updates must keep the structured inventory, audit dashboard, Change Audit log, and Horizon Scan ledger current. When an area, issue, legislation file, audit status, quality score, or cited source is added, removed, renamed, merged, retired, or materially revised, update the relevant rows in [`../inventory/areas.csv`](../inventory/areas.csv), [`../inventory/issues.csv`](../inventory/issues.csv), [`../inventory/contents.csv`](../inventory/contents.csv), [`../inventory/audits.csv`](../inventory/audits.csv), [`../inventory/sources.csv`](../inventory/sources.csv), and [`../AUDIT_DASHBOARD.md`](../AUDIT_DASHBOARD.md) as part of the same change. When a Change Audit is run, update [`../CHANGE_AUDIT_LOG.md`](../CHANGE_AUDIT_LOG.md) as part of the same change. When a `HOR-###` candidate is added, adjudicated, integrated, retained, or retired, update [`../HORIZON_SCAN.md`](../HORIZON_SCAN.md) as part of the same change.

The project will proceed by applying this framework to retained issues, developing authoritative source records, resolving overlap through primary ownership and cross-reference, and revising the least-complex adequate remedy as legal and factual analysis matures.

The governing framework incorporates the project-wide rules for institutional focus, politically neutral application, issue admission, mandatory issue architecture, issue-level conciseness, standardized annotations, the Least-Complex Adequate Remedy, limited use of automatic institutional-failure triggers, audit sidecars, source tracking, print assignment, and cross-referencing instead of duplicative treatment.

## File and Metadata Conventions

Every substantive issue has a stable identifier such as `DOJ-001`. Legislative proposal files use the issue identifier as the base filename.

- Federal legislative proposals use the unsuffixed issue identifier: `XXX-NNN.md`.
- Model state legislative proposals use the state suffix: `XXX-NNN-state.md`.
- Constitutional amendment text uses the amendment suffix: `XXX-NNN-amendment.md`.
- Enabling legislation for a constitutional amendment normally uses the unsuffixed issue identifier: `XXX-NNN.md`.

For issues with both federal and state proposals, the federal proposal is the unsuffixed file and the model state proposal is the `-state` file. For issues with only a model state proposal, the proposal should still use the `-state` suffix.

For issues with both constitutional amendment text and enabling legislation, the amendment page should contain the proposed constitutional amendment itself and the unsuffixed page should contain the proposed enabling legislation. The issue page should link both vehicles.

Examples:

- `ELEC-003.md` — federal proposal.
- `ELEC-003-state.md` — model state proposal.
- `ELEC-002-state.md` — model state proposal where no federal proposal is yet maintained.
- `DOJ-007-amendment.md` — constitutional amendment text.
- `DOJ-007.md` — enabling legislation for the amendment.

Every Markdown page must carry `print_levels` metadata under [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md#print-assignment-metadata).

## Compiled Appendix Catalog

The detailed print and export rules are maintained in [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md), but the governing framework should preserve the appendix catalog for quick reference.

Compiled public, legislative, and technical editions use this appendix allocation unless a publication-specific export plan deliberately supersedes it:

1. **Appendix A** - Proposed Federal Legislation and Constitutional Amendments;
2. **Appendix B** - Model State Legislation;
3. **Appendix C** - source-development materials, crosswalks, or research notes selected for publication;
4. **Appendix D** - technical framework, contribution rules, and release process, if included in a technical edition; and
5. **Appendix E** - issue audit-history files for full technical editions, when audit provenance is included.

Final print exports should resolve stable issue and legislation identifiers into appendix labels and page numbers through the export layer rather than manually maintained page-number references in canonical Markdown.

## Neutrality and Language Guidelines

The project applies neutral standards without pretending to be neutral about institutional harm. Language should help a skeptical but fair reader understand the project as structural reform analysis rather than campaign argument, while still naming abuse, corruption, illegality, coercion, falsehood, or institutional damage when the record supports those descriptions.

### Institutional Focus

Frame issues around institutional weakness, structural damage, and legal repair. Name individual actors only when their conduct is necessary to understand the failure, source the example, or explain the remedy.

### Neutral Application

Apply the same evidentiary, legal, and remedial standards regardless of party, ideology, officeholder, administration, or movement. Do not create partisan exemptions, manufacture false equivalence, make unsupported accusations for balance, or design rules that depend on who currently holds power.

### Public-Actor References

Project-authored prose should use office-respecting, institutionally neutral references for public actors when doing so improves precision and avoids avoidable partisan tone. For example, use `President Trump` rather than `Trump` or `Donald Trump` when referring to him as an officeholder, actor, or case-study subject in the project's own analysis.

This convention does not alter exact source material. Preserve formal case names, article titles, source titles, URLs, direct quotations, formal legal labels, and other citation text exactly as written unless the underlying source itself is being corrected or replaced.

When a phrase such as `Trump-era`, `anti-Trump`, or `pre-Trump` appears in project-authored prose, rewrite it into a more precise institutional formulation, such as `incidents from President Trump's administration`, `framed as targeting President Trump`, or `pre-2017 institutional status quo`, as context requires.

### Accuracy Over Softening

Neutrality does not require euphemism. If the record supports a term such as `unlawful`, `false`, `retaliatory`, `corrupt`, `coercive`, `abusive`, or `pretextual`, use the accurate term and cite the supporting basis. If the record is incomplete, contested, pending, or inferential, identify that limitation directly.

### Motive and Intent

Do not state motive, bad faith, corrupt purpose, retaliation, or pretext as fact unless supported by findings, admissions, contemporaneous records, credible reporting, or a clearly explained documented inference. Use qualified formulations such as `may indicate`, `raises concern`, `alleged`, `reported`, or `not yet adjudicated` when the record requires qualification.

### Conduct Before Character

Avoid standalone character labels and ideological epithets where a conduct-based description would be more precise. Instead of relying on labels such as `authoritarian`, `fascist`, `extremist`, or `radical`, describe the mechanism: concentration of removal power, weakened adjudicatory independence, reduced reviewability, coercive use of funding, manipulation of factual records, or similar institutional effects.

### Project 2025 Treatment

Treat Project 2025 and comparable ideological programs as source material for institutional-risk analysis, not as partisan enemy documents. The project may state its opposition to unitary executive theory, institutional capture, and efforts to subordinate public institutions to personal or factional control, but analysis should focus on the mechanism, legal vulnerability, implementation pathway, and institutional effect.

### Collective Labels

Avoid loaded collective labels that imply every Republican, conservative, Trump voter, Democrat, progressive, independent, or other broad political group supports the conduct or institutional weakness being analyzed. Use narrower sourced formulations such as `MAGA-aligned`, `Project 2025-associated`, `President Trump's administration`, `the administration`, `the proposal's sponsors`, or `identified supporters` only when analytically necessary.

### Coalition Reality

The project should not describe itself as a Democratic Party agenda or allow likely audience interest to substitute for institutional analysis. It may, however, acknowledge that certain proposals are likely to be more immediately interesting to Democratic, independent, civil-libertarian, good-government, institutionalist, or other audiences because of the present political alignment of the abuses being studied. That coalition reality should inform adoption analysis, objection handling, and framing, but it should not change the evidentiary standard, legal analysis, remedy design, or neutrality of application.

### Advocacy Tone

Avoid campaign-style language such as `fight back`, `defeat`, `crush`, `resist`, `anti-Trump`, or `pro-democracy side` in proposal analysis. Prefer institutional verbs such as `repair`, `prevent recurrence`, `constrain`, `restore`, `stabilize`, `harden`, `detect`, `correct`, `deter`, and `contain`.

## Analytical Method

**Identify the problem.** Determine what institution or governing process failed, how the failure manifested, and what damage resulted.

**Identify the weakness.** Determine which law, structure, procedure, remedy, or norm permitted the failure or proved inadequate to constrain it.

**Identify repair and prevention.** Determine what must be restored or corrected now and what safeguards are necessary to prevent recurrence.

**Identify the least-complex adequate remedy.** Determine the least-complex measure, or package of measures, capable of adequately addressing the defect.

### Issue-Admission Test

Before promoting a candidate into a standalone issue, ask:

> Does this candidate identify a distinct institutional weakness requiring separate diagnosis or remedial analysis?

If not, merge it into a broader issue, treat it as a manifestation or example, cross-reference it, or retain it only in the research inventory.

Candidate issues may be retired or merged when the issue-admission test shows substantial duplication. A status such as **Awaiting merits adjudication** identifies a deliberately paused issue whose remedy depends materially on pending judicial resolution.

### Unit of Analysis

Each issue must identify a generalized structural defect. Incidents from President Trump's administration or any other administration illustrate the defect but do not define it.

### Overlap and Cross-Reference Rule

Each institutional defect should have one primary home. Related areas should cross-reference the primary issue instead of repeating the same diagnosis, evidence, and remedy. The issue inventory may identify related areas without creating duplicate substantive sections.

## Mandatory Issue Architecture

Every developed issue should use the following structure:

1. **Issue Snapshot** — a short reader-navigation box summarizing problem, repair, and vehicle.
2. **Institutional Anomaly** — a concise, generalized statement of the structural defect.
3. **Manifestation of the Failure** — titled representative instances or categories showing only the facts necessary to show how the defect operates.
4. **Resulting Damage** — the principal institutional, legal, factual, administrative, or legitimacy harm.
5. **Underlying Weakness** — the law, structure, procedure, remedy, or norm that failed.
6. **Proposal Survey** — concise review of prior or adjacent models bearing on the remedy.
7. **Least-Complex Adequate Remedy** — the least-complex measure or package capable of adequately addressing the defect.
8. **Repair and Prevention** — restoration or correction of existing damage and prospective safeguards against recurrence.
9. **Proposed Legislation** — link to the proposed legislative, rule, constitutional, or procedural vehicle when one exists. For amendment-dependent issues, use **Proposed Constitutional Amendment** and **Proposed Enabling Legislation** instead.
10. **Budgetary Impact Statement** — a concise preliminary fiscal classification using the project rubric.
11. **Proposal Scoring** — a succinct audit and scoring box showing the proposal-quality score, any companion scores, Required Electoral Environment, Development Priority, and any assessed coalition-support estimates first, separated by an em dash divider from audit status, rubric version, rebaseline status, next audit need, and a link to the sibling full audit-history file.
12. **Annotation** — evidence, legal analysis, qualifications, alternatives, and implementation constraints.

The headings guide analysis but do not require artificial expansion. Each section should add a distinct proposition.

The **Manifestation of the Failure** section should use short `###` instance titles in the style of `DOJ-005`, such as `### Example actor or episode` or `### Functional category of failure`. Use one titled instance even when the page currently has only one principal manifestation. Where the section discusses both general mechanisms and concrete episodes, separate them into titled subsections rather than leaving untitled paragraphs. Titles should be descriptive, neutral, concise, and supported by the text that follows.

Custom section headings are permitted where they make a developed issue clearer or more natural to read, provided the issue still performs the required analytical functions. A custom heading should be meaningfully distinct from the canonical heading it replaces rather than a trivial restatement. Where custom headings are used, the required function should remain clear from the heading itself, the surrounding structure, or a short orienting sentence.

Where proposed legislation or another concrete reform vehicle exists, the issue page should include a **Proposed Legislation** section immediately after **Repair and Prevention**. **Repair and Prevention** and **Proposed Legislation** should appear after **Least-Complex Adequate Remedy**, so the page first compares available models and identifies the preferred remedy before presenting the repair frame and concrete vehicle. Proposed vehicles should always be presented as a Markdown bullet list, even when there is only one linked item.

Where a proposal requires a constitutional amendment and separate implementing legislation, the issue page should use **Proposed Constitutional Amendment** for the amendment page and **Proposed Enabling Legislation** for the implementing statute. Both sections should appear as Markdown bullet lists. The amendment text itself should live on its own proposal page, not inside the issue page. The enabling legislation page should identify the amendment dependency in front matter or introductory text.

Candidate or source-development pages may keep a **Proposed Legislation** section with a single `Pending development` bullet when no draft vehicle exists yet. That placeholder is a development-status marker, not a legislation link failure. Once a concrete vehicle exists, replace the placeholder with a linked bullet and update the Issue Snapshot vehicle line, metadata, inventories, and dashboard.

Where a proposal is legally available under current law but depends on a future or amenable institutional actor for realistic adoption, the issue page may include an **Adoption Viability Note** immediately after **Proposed Legislation**, or after **Proposed Enabling Legislation** for amendment-dependent issues. The note should be concise and should distinguish legal vehicle availability from practical adoption likelihood.

Where a proposal may be confused with, overlap with, partially replace, or depend on another ARRP proposal, the issue page should include an optional **Relationship to Adjacent Proposals** section after **Proposed Legislation** or **Proposed Enabling Legislation** and any **Adoption Viability Note**, but before **Budgetary Impact Statement**. The section should briefly identify what the current proposal owns, what each adjacent proposal owns, whether there is partial overlap or merger, and whether the adjacent proposal complements or replaces the current remedy.

The issue page and its linked proposed legislation, constitutional amendment text, enabling legislation, or other proposal vehicle must remain substantively aligned. When either page changes, the next framework, drafting, or project-integration audit should cross-check the Issue Snapshot vehicle, Least-Complex Adequate Remedy, Repair and Prevention, Proposed Legislation or amendment/enabling sections, Annotation, and Proposal Scoring summary against the linked legislative, constitutional, rule, or procedural text. The check should confirm that the issue page still accurately describes the vehicle, covered actors, legal hook, remedy type, enforcement mechanism, deadlines, responsible institutions, scope limits, and material drafting notes. If an audit discovers a substantive discrepancy, document it as an unresolved finding, report it to the user, and treat it as requiring human review before updating either the issue page or the proposed legislation.

Every developed issue page and every proposal page should include a **Budgetary Impact Statement** before **Annotation** on issue pages and before **Drafting Notes** on legislation or proposal pages. The statement is a preliminary ARRP planning classification, not an official fiscal score. It must be short, source-conscious, and must not include a dollar figure unless the figure is tied to a cited government source, historical appropriation, CBO score, agency budget material, audited program cost, or comparable source-backed basis. The substantive classification should appear first. The project disclaimer should appear below it as an italicized note: `*Note: Preliminary ARRP assessment only; not a CBO, OMB, agency, or legislative-counsel score.*`

Use one of the following baseline classifications unless a source-backed estimate justifies a narrower formulation:

- `No direct appropriation is anticipated.`
- `Administrative workload is possible; no new appropriation is specified.`
- `Budget authority is likely required; no dollar estimate is assigned pending source-backed cost data.`
- `Not estimated pending proposal development.`
- `No direct appropriation is anticipated for the amendment itself; implementing legislation may have costs.`
- `Budget authority may be required if the chosen remedy funds postage, tracking, or election-administration support; no dollar estimate is assigned pending source-backed cost data.`

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

Each annotation segment should begin with a bold inline title followed by a period, then the paragraph text.

**Basis and Evidence.** Explain why the anomaly has been identified and cite representative authoritative support.

**Qualification.** State material uncertainty, competing interpretations, and limits necessary to keep the main assertion accurate.

**Remedial Alternatives and Constraints.** Briefly identify materially serious fallback options and the constitutional, statutory, administrative, or practical limits affecting the least-complex remedy.

**Budgetary Impact.** Explain any fiscal, workload, or implementation-burden classification that needs more support than the short Budgetary Impact Statement can provide.

Scoring annotations should mirror the labels used in the **Proposal Scoring** box where practical. Use **Quality Score**, **Adoption Score**, **Coalition Support Estimates**, **Adoption Friction**, **Required Electoral Environment**, and **Development Priority** as needed. Place these scoring annotation segments after **Budgetary Impact** when they appear, so score explanations can incorporate fiscal, implementation, adoption, friction, and readiness findings without crowding the Proposal Scoring box.

When the **Proposal Scoring** box includes **Coalition Support Estimates**, keep the box visually compact: put the label on its own line, then list each audience estimate on indented lines using inline `<br />` breaks and `&nbsp;` spacing. Do not place evidentiary caveats such as "provisional," "not polling," or "stakeholder judgment" in the compact scoring box when the same point is explained in the matching **Coalition Support Estimates** annotation segment.

Use this compact format when coalition estimates are displayed:

```markdown
> **Coalition Support Estimates:**<br />&nbsp;&nbsp;&nbsp;&nbsp;Democratic 80%<br />&nbsp;&nbsp;&nbsp;&nbsp;Independent 60%<br />&nbsp;&nbsp;&nbsp;&nbsp;Republican 40%<br />&nbsp;&nbsp;&nbsp;&nbsp;Bipartisan viability 55%
```

### Assertion Discipline

State each institutional conclusion as directly as the record permits. An annotation must substantiate rather than retreat from the main assertion. Distinguish established fact, legal conclusion, institutional inference, and normative judgment.

### Source Standard

Use primary legal and governmental records first. Use authoritative institutional and academic sources for doctrine, design, and comparative analysis. Use high-quality secondary reporting mainly for synthesis and discovery.

Every factual, legal, and causal proposition must remain independently supportable. When an issue file refers to a real-life event, case, official action, report, statute, rule, hearing, order, or other source material, include a nearby citation or link. Do not name concrete examples in issue text without enough source information for later verification.

Source inventory updates are required whenever a new external source is cited or an existing cited source is repurposed for a materially different proposition. A source may remain marked `Reviewed?` as `No` until verification is complete, but the citation should still be captured promptly.

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

## Proposal Quality Audit

Before an issue or proposal is treated as ready for external circulation, it should undergo a quality audit. The framework requirement is structural: developed issue pages must expose a compact **Proposal Scoring** section, link to the sibling full audit-history file, and keep scoring visible without overloading the main issue page.

The canonical audit rules, resource tiers, Horizon Scan procedure, hallucination-resistance protocol, scoring formula, adoption-score formula, international-support score, output requirements, and audit-preservation rules are maintained in [`METHODOLOGY.md`](METHODOLOGY.md#audit-rules-and-proposal-quality-scoring).

The **Proposal Scoring** section should group all scores and viability indicators at the top, followed by an em dash divider and then audit status, routing fields, rubric version, rebaseline status, and the audit-history link. [`../AUDIT_DASHBOARD.md`](../AUDIT_DASHBOARD.md) provides the compact cross-issue view.

## Outstanding Development

The following canonical backlog items remain outstanding:

- develop authoritative source records, annotations, and individual issue files for remaining JUD, PAR, and CLASS candidate issues;
- analyze constitutional and implementation constraints for judicial-enforcement remedies, including appointments, appropriations, due process, and presidential control;
- analyze the constitutional limits on restricting the legal effect of presidential clemency while developing transparency, anti-corruption, review, recordkeeping, disclosure, and surrounding-liability remedies;
- preserve and source the distinctions among classification status, authorization to disclose, lawful custody or possession, and government ownership and records-preservation duties;
- develop the A-21 annotation explaining the systemic risks of sustained political subordination of monetary policy, including inflation, unanchored expectations, leverage, asset-price distortions, currency weakness, loss of credibility, and the possibility of a later severe corrective contraction;
- conduct a systematic review of each proposal's potential bipartisan support, including cross-party institutional interests, likely objections, possible neutral framing, and risks of partisan capture or misuse;
- complete the Project 2025 / ARRP crosswalk source-development pass, including official Mandate chapter records, chapter-level and major-proposal rows, page or section citations, implementation-status labels, weakness-vehicle analysis for proposals whether or not enacted or attempted, ARRP area and issue mappings, coverage-status labels, newly needed issue candidates, and area-priority review;
- maintain and improve the compiled-export workflow, including lightweight table-of-contents generation, heading normalization, local-link verification, appendix placement for proposed legislation, and compact document layout;
- before public release, implement two-pass PDF/DOCX export support for stable appendix labels, page-numbered cross-references, and a page-numbered table of contents or appendix index, so body references can point to proposed legislation and technical appendices without manually maintained page numbers;
- defer full clickable table-of-contents work until the project is more developed, then limit it to major sections, project areas, developed issues, and appendices;
- select and adopt an appropriate Creative Commons or other public reuse license when the project is ready for broader legislative and public engagement.

These are substantive research and issue-development tasks, not exceptions to the governing framework above.
