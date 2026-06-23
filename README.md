# American Restoration and Resilience Project (ARRP)

**A Roadmap for Repairing Institutional Damage, Restoring Trustworthy Government, and Preventing Future Personalist Capture**

This private repository is the canonical working source for the American Restoration and Resilience Project.

## Canonical sources

- [`framework/FRAMEWORK.md`](framework/FRAMEWORK.md) — governing framework and current project-area inventory
- [`inventory/areas.csv`](inventory/areas.csv) — structured area inventory
- [`inventory/issues.csv`](inventory/issues.csv) — structured issue inventory
- [`inventory/sources.csv`](inventory/sources.csv) — source-tracking table
- [`areas/`](areas/) — modular area and issue analyses
- [`legislation/`](legislation/) — draft statutory and administrative language keyed to issue identifiers

## Working conventions

1. Every substantive issue has a stable identifier such as `DOJ-001`.
2. The framework governs analysis; the inventory tracks it; issue files contain the substantive work.
3. Each developed issue identifies the **Least-Complex Adequate Remedy**.
4. Supporting evidence, qualifications, and alternatives belong in annotation or source notes.
5. Where complete prevention is impracticable, a remedy may instead provide reliable detection, correction, deterrence, and institutional self-repair.
6. Candidate issues may be retired or merged when the issue-admission test shows substantial duplication.
7. A status such as **Awaiting merits adjudication** identifies a deliberately paused issue whose remedy depends materially on pending judicial resolution.
8. Markdown and CSV are canonical. DOCX, PDF, and XLSX files are generated exports.

## Legislation filename convention

Legislative proposal files use the issue identifier as the base filename.

- Federal legislative proposals use the unsuffixed issue identifier: `XXX-NNN.md`.
- Model state legislative proposals use the state suffix: `XXX-NNN-state.md`.

For issues with both federal and state proposals, the federal proposal is the unsuffixed file and the model state proposal is the `-state` file. For issues with only a model state proposal, the proposal should still use the `-state` suffix.

Examples:

- `ELEC-003.md` — federal proposal.
- `ELEC-003-state.md` — model state proposal.
- `ELEC-002-state.md` — model state proposal where no federal proposal is yet maintained.

## Current status

Developed Department of Justice issues currently include DOJ-001, DOJ-002, DOJ-003, DOJ-005, and DOJ-007. DOJ-004 is awaiting merits adjudication. DOJ-006 and DOJ-008 have been retired and merged into their primary issues. A-16 now includes developed issue IMM-001 and the proposed Presidential Criminal Accountability Amendment.

The governing framework already incorporates the project-wide rules for institutional focus, politically neutral application, issue admission, mandatory issue architecture, issue-level conciseness, standardized annotations, the Least-Complex Adequate Remedy, limited use of automatic institutional-failure triggers, and cross-referencing instead of duplicative treatment.

The area and issue inventories already include A-04 Judicial Independence and Enforcement (JUD-001 through JUD-008), A-05 Presidential Clemency and Pardon Power (PAR-001 through PAR-010), A-07 Classification, Declassification, and National-Security Information (CLASS-001 through CLASS-012), and A-21 Federal Reserve Independence and Monetary Policy (FRB-001 through FRB-008). The `FED` prefix remains reserved for A-20 Federalism and Presidential Coercion of States.

## Outstanding development

The following work remains outstanding and should not be treated as an uncommitted framework revision:

- develop authoritative source records, annotations, and individual issue files for the JUD, PAR, and CLASS candidate inventories;
- analyze constitutional and implementation constraints for judicial-enforcement remedies, including appointments, appropriations, due process, and presidential control;
- analyze the constitutional limits on restricting the legal effect of presidential clemency while developing transparency, anti-corruption, review, recordkeeping, disclosure, and surrounding-liability remedies;
- preserve and source the distinctions among classification status, authorization to disclose, lawful custody or possession, and government ownership and records-preservation duties;
- develop the A-21 annotation explaining the systemic risks of sustained political subordination of monetary policy, including inflation, unanchored expectations, leverage, asset-price distortions, currency weakness, loss of credibility, and the possibility of a later severe corrective contraction.

These are substantive research and issue-development tasks. They do not reopen the already committed governing framework or area inventories.