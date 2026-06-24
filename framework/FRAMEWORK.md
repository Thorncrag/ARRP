# American Restoration and Resilience Project — Technical Framework

This file contains the project's technical operating framework: method, issue architecture, evidence standards, remedy standards, repository structure, file conventions, contribution process, release process, and development backlog.

The project's public-facing premise, mission, scope, and governing principles are maintained in [`../README.md`](../README.md).

## Core Method

**Identify the problem.** Determine what institution or governing process failed, how the failure manifested, and what damage resulted.

**Identify the weakness.** Determine which law, structure, procedure, remedy, or norm permitted the failure or proved inadequate to constrain it.

**Identify repair and prevention.** Determine what must be restored or corrected now and what safeguards are necessary to prevent recurrence.

**Identify the least-complex adequate remedy.** Determine the least-complex measure, or package of measures, capable of adequately addressing the defect.

## Issue-Admission Test

Before promoting a candidate into a standalone issue, ask:

> Does this candidate identify a distinct institutional weakness requiring separate diagnosis or remedial analysis?

If not, merge it into a broader issue, treat it as a manifestation or example, cross-reference it, or retain it only in the research inventory.

## Mandatory Issue Architecture

Every developed issue should use the following structure:

1. **Institutional Anomaly** — a concise, generalized statement of the structural defect.
2. **Manifestation of the Failure** — only the representative facts necessary to show how the defect operates.
3. **Resulting Damage** — the principal institutional, legal, factual, administrative, or legitimacy harm.
4. **Underlying Weakness** — the law, structure, procedure, remedy, or norm that failed.
5. **Repair and Prevention** — restoration or correction of existing damage and prospective safeguards against recurrence.
6. **Least-Complex Adequate Remedy** — the least-complex measure or package capable of adequately addressing the defect.
7. **Annotation** — evidence, legal analysis, qualifications, alternatives, and implementation constraints.

The headings guide analysis but do not require artificial expansion. Each section should add a distinct proposition.

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

## Repository Architecture

- [`../README.md`](../README.md) contains the public-facing proposal front matter, including the reader notice, foundational premise, mission, scope, governing principles, rights notice, citation pointer, and technical-framework pointer.
- `framework/` contains governing methodology and cross-cutting remedial architecture.
- `areas/` contains one directory per project area and one file per developed issue.
- `legislation/` contains proposed statutory language keyed to issue identifiers.
- `inventory/` contains structured area, issue, and source records.
- `research/` contains material not yet integrated into a developed issue.
- `exports/` contains generated DOCX, PDF, and XLSX editions.
- `archive/` contains superseded snapshots retained for provenance.

Markdown and CSV files are authoritative. Binary Office and PDF files are generated outputs.

## Canonical Sources

- [`FRAMEWORK.md`](FRAMEWORK.md) — technical framework, methodology, repository conventions, and development status
- [`../inventory/areas.csv`](../inventory/areas.csv) — structured area inventory
- [`../inventory/issues.csv`](../inventory/issues.csv) — structured issue inventory
- [`../inventory/sources.csv`](../inventory/sources.csv) — source-tracking table
- [`../areas/`](../areas/) — modular area and issue analyses
- [`../legislation/`](../legislation/) — draft statutory and administrative language keyed to issue identifiers
- [`../AUTHORS.md`](../AUTHORS.md) — authorship statement
- [`../LICENSE.md`](../LICENSE.md) — rights and reuse notice
- [`../CITATION.cff`](../CITATION.cff) — citation metadata
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution expectations
- [`../PUBLIC_RELEASE.md`](../PUBLIC_RELEASE.md) — public release process

## Working Conventions

1. Every substantive issue has a stable identifier such as `DOJ-001`.
2. The framework governs analysis; the inventory tracks it; issue files contain the substantive work.
3. Each developed issue identifies the **Least-Complex Adequate Remedy**.
4. Supporting evidence, qualifications, and alternatives belong in annotation or source notes.
5. Where complete prevention is impracticable, a remedy may instead provide reliable detection, correction, deterrence, and institutional self-repair.
6. Candidate issues may be retired or merged when the issue-admission test shows substantial duplication.
7. A status such as **Awaiting merits adjudication** identifies a deliberately paused issue whose remedy depends materially on pending judicial resolution.
8. Markdown and CSV are canonical. DOCX, PDF, and XLSX files are generated exports.

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

Developed Department of Justice issues include:

- [`DOJ-001 — Recent Presidential Personal Counsel in Senior DOJ Leadership`](../areas/a-01-department-of-justice/issues/DOJ-001.md)
- [`DOJ-002 — White House Direction or Interference in Particular Federal Criminal Matters`](../areas/a-01-department-of-justice/issues/DOJ-002.md)
- [`DOJ-003 — Politically Selective Enforcement, Charging, and Favoritism`](../areas/a-01-department-of-justice/issues/DOJ-003.md)
- [`DOJ-007 — Independent Investigation of Presidential and Senior Executive Misconduct`](../areas/a-01-department-of-justice/issues/DOJ-007.md)

## Development Phase

The project will proceed by applying this framework to retained issues, developing authoritative source records, resolving overlap through primary ownership and cross-reference, and revising the least-complex adequate remedy as legal and factual analysis matures.

## Current Status

Developed Department of Justice issues currently include DOJ-001, DOJ-002, DOJ-003, DOJ-005, and DOJ-007. DOJ-004 is awaiting merits adjudication. DOJ-006 and DOJ-008 have been retired and merged into their primary issues. A-16 now includes developed issue IMM-001 and the proposed Presidential Criminal Accountability Amendment.

The governing framework already incorporates the project-wide rules for institutional focus, politically neutral application, issue admission, mandatory issue architecture, issue-level conciseness, standardized annotations, the Least-Complex Adequate Remedy, limited use of automatic institutional-failure triggers, and cross-referencing instead of duplicative treatment.

The area and issue inventories already include A-04 Judicial Independence and Enforcement (JUD-001 through JUD-008), A-05 Presidential Clemency and Pardon Power (PAR-001 through PAR-010), A-07 Classification, Declassification, and National-Security Information (CLASS-001 through CLASS-012), and A-21 Federal Reserve Independence and Monetary Policy (FRB-001 through FRB-008). The `FED` prefix remains reserved for A-20 Federalism and Presidential Coercion of States.

## Outstanding Development

The following work remains outstanding and should not be treated as an uncommitted framework revision:

- develop authoritative source records, annotations, and individual issue files for the JUD, PAR, and CLASS candidate inventories;
- analyze constitutional and implementation constraints for judicial-enforcement remedies, including appointments, appropriations, due process, and presidential control;
- analyze the constitutional limits on restricting the legal effect of presidential clemency while developing transparency, anti-corruption, review, recordkeeping, disclosure, and surrounding-liability remedies;
- preserve and source the distinctions among classification status, authorization to disclose, lawful custody or possession, and government ownership and records-preservation duties;
- develop the A-21 annotation explaining the systemic risks of sustained political subordination of monetary policy, including inflation, unanchored expectations, leverage, asset-price distortions, currency weakness, loss of credibility, and the possibility of a later severe corrective contraction;
- select and adopt an appropriate Creative Commons or other public reuse license when the project is ready for broader legislative and public engagement.

These are substantive research and issue-development tasks. They do not reopen the already committed governing framework or area inventories.
