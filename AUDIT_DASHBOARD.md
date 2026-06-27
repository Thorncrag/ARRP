---
title: "Audit Dashboard"
print_levels:
  - full-technical
---

# Audit Dashboard

This dashboard is the compact project-wide audit tracker. It is for meta-analysis, triage, and audit planning only; compact proposal-scoring summaries belong on issue pages, full audit histories belong in sibling `ISSUE-ID.audit.md` files, and machine-readable tracking data belongs in [`inventory/audits.csv`](inventory/audits.csv).

Update this page whenever an audit changes an issue score, audit status, last audit type, next audit need, proposal-page link or status, legislation link, development status, or other dashboard field.

> **Quick Jump**
>
> [Score Bands](#score-bands) · [Rubric Rebaseline](#rubric-rebaseline) · [Enactment Pathway](#enactment-pathway) · [Adoption Friction](#adoption-friction) · [Next Audit Queue](#next-audit-queue) · [Change Audit Log](#change-audit-log) · [Horizon Scan](#horizon-scan) · [Issue Audit Index](#issue-audit-index)

## Snapshot

[Back to top](#audit-dashboard)

- Issues tracked: 213
- Issues with proposed legislation links: 19
- Developed issues: 20
- Candidate issues: 179
- Retired or merged issues: 13
- Paused for controlling finding: 1

## Score Bands

[Back to top](#audit-dashboard)

| Band | Count |
| --- | ---: |
| Retired/merged | 13 |
| Paused | 1 |
| Pending development | 179 |
| Developed draft | 20 |
| Audit in progress | 0 |

## Rubric Rebaseline

[Back to top](#audit-dashboard)

Current audit rubric version: `2026-06-27.1`

| Rebaseline status | Count |
| --- | ---: |
| Current | 1 |
| Current fixed-status score | 193 |
| Soft rebaseline needed | 0 |
| Hard rebaseline needed | 19 |

## Enactment Pathway

[Back to top](#audit-dashboard)

Required Electoral Environment is a T1 gate that identifies the minimum electoral or institutional condition needed to make a proposal seriously actionable. It is evidence-bound and feeds Adoption and Implementation scoring rather than creating a standalone score.

| Required electoral environment | Count |
| --- | ---: |
| Current-law available | 0 |
| House oversight majority | 0 |
| Narrow unified government | 0 |
| Filibuster-constrained unified government | 0 |
| Sixty-vote Senate | 1 |
| Filibuster reform or exception | 0 |
| Wave-election mandate | 0 |
| Post-crisis repair mandate | 0 |
| Constitutional amendment environment | 0 |
| State-level pathway | 0 |
| Not electorally dependent | 0 |
| Unassessed | 19 |
| N/A | 193 |

## Adoption Friction

[Back to top](#audit-dashboard)

Adoption Friction Score is a companion metric outside the Proposal Quality Score. Higher friction means greater expected organized opposition, litigation, procedural blockade, public misunderstanding, or institutional resistance.

| Adoption friction band | Count |
| --- | ---: |
| Low | 0 |
| Manageable | 0 |
| Significant | 0 |
| High | 1 |
| Extreme | 0 |
| Unassessed | 19 |
| N/A | 193 |

## Next Audit Queue

[Back to top](#audit-dashboard)

| Next audit indicator | Count |
| --- | ---: |
| Advanced audit | 17 |
| Cross-reference check | 13 |
| Development audit | 1 |
| Issue-admission test | 179 |
| Reassess predicate | 1 |
| T2 | 1 |
| T3 | 0 |
| T4 | 1 |

## Change Audit Log

[Back to top](#audit-dashboard)

| Date | Change audited | Scope | Score/rebaseline effect | Findings and corrections |
| --- | --- | --- | --- | --- |
| 2026-06-27 | Framework hierarchy reorganization and neutrality/language guidelines | Project-wide Markdown and CSV sweep for duplicated framework sections, broken framework links, stale architecture references, and obvious project-authored language conflicts with the new neutrality rules. | No score or rubric rebaseline effect. The change clarified structure and language conventions but did not alter the proposal-quality scoring formula, required audit fields, or issue-page scoring template. Existing hard-rebaseline queue remains unchanged. | Consolidated `FRAMEWORK.md` hierarchy; confirmed no duplicate framework headings or broken framework links; corrected two project-authored wording issues (`radically` to more precise neutral phrasing) in source-development and ELEC-006. Remaining flagged terms were legal/statutory uses, source titles, framework examples, or ordinary institutional terminology. |

## Horizon Scan

[Back to top](#audit-dashboard)

Horizon Scan intake and integration decisions are maintained on the separate [Horizon Scan](HORIZON_SCAN.md) page. This dashboard remains the compact cross-issue score, audit-status, and next-audit tracker.


## Issue Audit Index

[Back to top](#audit-dashboard)

| Issue | Area | Priority | Status | Score | Band | Runs | Last audit | Last date | Next | Proposal page/status | Legislation | Rubric | Rebaseline | Pathway | Priority | Friction |
| --- | --- | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DOJ-001 | A-01 | High | Developed | 82 | Developed draft | 14 | T4 publication-ready audit | 2026-06-27 | T4 follow-up | [Issue](areas/DOJ/issues/DOJ-001.md) | [Bill](legislation/DOJ-001.md) | 2026-06-27.1 | current | sixty-vote-senate | active | High |
| DOJ-002 | A-01 | High | Developed | 62 | Developed draft | 2 | T1 framework check | 2026-06-25 | T2 | [Issue](areas/DOJ/issues/DOJ-002.md) | [Bill](legislation/DOJ-002.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| DOJ-003 | A-01 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/DOJ/issues/DOJ-003.md) | [Bill](legislation/DOJ-003.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| DOJ-004 | A-01 | High | Awaiting merits adjudication | 0 | Paused | 1 | Initial inventory audit | 2026-06-24 | Reassess predicate | [Issue](areas/DOJ/issues/DOJ-004.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOJ-005 | A-01 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/DOJ/issues/DOJ-005.md) | [Bill](legislation/DOJ-005.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| DOJ-006 | A-01 | High | Retired—merged into DOJ-002 and DOJ-007 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/DOJ/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOJ-007 | A-01 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/DOJ/issues/DOJ-007.md) | [Bill](legislation/DOJ-007.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| DOJ-008 | A-01 | High | Retired—merged into DOJ-003 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/DOJ/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOJ-009 | A-01 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/DOJ/issues/DOJ-009.md) | [Bill](legislation/DOJ-009.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| ELEC-001 | A-02 | High | Developed | 60 | Developed draft | 2 | Horizon integration decision | 2026-06-25 | Advanced audit | [Issue](areas/ELEC/issues/ELEC-001.md) | [Bill](legislation/ELEC-001.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| ELEC-002 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/ELEC/issues/ELEC-002.md) | [Bill](legislation/ELEC-002-state.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| ELEC-003 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/ELEC/issues/ELEC-003.md) | [Bill 1](legislation/ELEC-003-state.md)<br />[Bill 2](legislation/ELEC-003.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| ELEC-004 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/ELEC/issues/ELEC-004.md) | [Bill 1](legislation/ELEC-004-state.md)<br />[Bill 2](legislation/ELEC-004.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| ELEC-005 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/ELEC/issues/ELEC-005.md) | [Bill](legislation/ELEC-005.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| ELEC-006 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/ELEC/issues/ELEC-006.md) | [Bill](legislation/ELEC-006.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| ELEC-007 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/ELEC/issues/ELEC-007.md) | [Bill](legislation/ELEC-007.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| ELEC-008 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/ELEC/issues/ELEC-008.md) | [Bill](legislation/ELEC-008.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| ELEC-009 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/ELEC/issues/ELEC-009.md) | [Bill](legislation/ELEC-009.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| ELEC-010 | A-02 | High | Developed | 55 | Developed draft | 2 | Horizon integration decision | 2026-06-25 | Development audit | [Issue](areas/ELEC/issues/ELEC-010.md) | — | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| ELEC-011 | A-02 | High | Candidate | 0 | Pending development | 1 | Horizon integration decision | 2026-06-25 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| ELEC-012 | A-02 | High | Candidate | 0 | Pending development | 1 | Horizon integration decision | 2026-06-25 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| ELEC-013 | A-02 | High | Candidate | 0 | Pending development | 1 | Horizon integration decision | 2026-06-25 | Issue-admission test | [Issue](areas/ELEC/issues/ELEC-013.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| WAR-001 | A-03 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/WAR/issues/WAR-001.md) | [Bill](legislation/WAR-001.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| WAR-002 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/WAR/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| WAR-003 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/WAR/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| WAR-004 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/WAR/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| WAR-005 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/WAR/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| WAR-006 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/WAR/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| WAR-007 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/WAR/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| WAR-008 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/WAR/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| JUD-001 | A-04 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/JUD/issues/JUD-001.md) | [Bill](legislation/JUD-001.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| JUD-002 | A-04 | High | Retired—merged into JUD-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/JUD/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| JUD-003 | A-04 | High | Retired—merged into JUD-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/JUD/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| JUD-004 | A-04 | High | Retired—merged into JUD-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/JUD/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| JUD-005 | A-04 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| JUD-006 | A-04 | High | Retired—merged into JUD-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/JUD/README.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| JUD-007 | A-04 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| JUD-008 | A-04 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| JUD-009 | A-04 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/JUD/issues/JUD-009.md) | [Bill](legislation/JUD-009.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| JUD-010 | A-04 | High | Candidate | 0 | Pending development | 1 | Horizon integration decision | 2026-06-25 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PAR-001 | A-05 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PAR-002 | A-05 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PAR-003 | A-05 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PAR-004 | A-05 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PAR-005 | A-05 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PAR-006 | A-05 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PAR-007 | A-05 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PAR-008 | A-05 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PAR-009 | A-05 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PAR-010 | A-05 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-001 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-002 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-003 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-004 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-005 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-006 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-007 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-008 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-009 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-010 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-011 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-012 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-013 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMOL-014 | A-06 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-001 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-002 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-003 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-004 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-005 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-006 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-007 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-008 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-009 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-010 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-011 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CLASS-012 | A-07 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CIV-001 | A-08 | High | Candidate | 0 | Pending development | 2 | Horizon integration decision | 2026-06-25 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CIV-002 | A-08 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CIV-003 | A-08 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CIV-004 | A-08 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CIV-005 | A-08 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CIV-006 | A-08 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CIV-007 | A-08 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CIV-008 | A-08 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CIV-009 | A-08 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| OVS-001 | A-09 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| OVS-002 | A-09 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| OVS-003 | A-09 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| OVS-004 | A-09 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| OVS-005 | A-09 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| OVS-006 | A-09 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| OVS-007 | A-09 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| OVS-008 | A-09 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMERG-001 | A-10 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMERG-002 | A-10 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMERG-003 | A-10 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMERG-004 | A-10 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMERG-005 | A-10 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMERG-006 | A-10 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMERG-007 | A-10 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| EMERG-008 | A-10 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FUND-001 | A-11 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FUND-002 | A-11 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FUND-003 | A-11 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FUND-004 | A-11 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FUND-005 | A-11 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FUND-006 | A-11 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FUND-007 | A-11 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FUND-008 | A-11 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| APPT-001 | A-12 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| APPT-002 | A-12 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| APPT-003 | A-12 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| APPT-004 | A-12 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| APPT-005 | A-12 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| APPT-006 | A-12 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| APPT-007 | A-12 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| APPT-008 | A-12 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REC-001 | A-13 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REC-002 | A-13 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REC-003 | A-13 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REC-004 | A-13 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REC-005 | A-13 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REC-006 | A-13 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REC-007 | A-13 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REC-008 | A-13 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOM-001 | A-14 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOM-002 | A-14 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOM-003 | A-14 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOM-004 | A-14 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOM-005 | A-14 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOM-006 | A-14 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOM-007 | A-14 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOM-008 | A-14 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| DOM-009 | A-14 | High | Candidate | 0 | Pending development | 1 | Horizon integration decision | 2026-06-25 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CONG-001 | A-15 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CONG-002 | A-15 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CONG-003 | A-15 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CONG-004 | A-15 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CONG-005 | A-15 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CONG-006 | A-15 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CONG-007 | A-15 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| CONG-008 | A-15 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| IMM-001 | A-16 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/IMM/issues/IMM-001.md) | [Bill](legislation/IMM-001.md) | pre-2026-06-26.1 | hard-rebaseline-needed | unassessed | unassessed | Unassessed |
| IMM-002 | A-16 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| IMM-003 | A-16 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| IMM-004 | A-16 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| IMM-005 | A-16 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| IMM-006 | A-16 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| IMM-007 | A-16 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| IMM-008 | A-16 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REG-001 | A-17 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REG-002 | A-17 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REG-003 | A-17 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REG-004 | A-17 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REG-005 | A-17 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REG-006 | A-17 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REG-007 | A-17 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| REG-008 | A-17 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FACT-001 | A-18 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FACT-002 | A-18 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FACT-003 | A-18 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FACT-004 | A-18 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FACT-005 | A-18 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FACT-006 | A-18 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FACT-007 | A-18 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FACT-008 | A-18 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FACT-009 | A-18 | High | Candidate | 0 | Pending development | 1 | Horizon integration decision | 2026-06-25 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| RET-001 | A-19 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| RET-002 | A-19 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| RET-003 | A-19 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| RET-004 | A-19 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| RET-005 | A-19 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| RET-006 | A-19 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| RET-007 | A-19 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| RET-008 | A-19 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FED-001 | A-20 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FED-002 | A-20 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FED-003 | A-20 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FED-004 | A-20 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FED-005 | A-20 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FED-006 | A-20 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FED-007 | A-20 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FED-008 | A-20 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FRB-001 | A-21 | Critical | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FRB-002 | A-21 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FRB-003 | A-21 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FRB-004 | A-21 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FRB-005 | A-21 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FRB-006 | A-21 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FRB-007 | A-21 | Critical | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| FRB-008 | A-21 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-001 | A-22 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-002 | A-22 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-003 | A-22 | Critical | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-004 | A-22 | Critical | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-005 | A-22 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-006 | A-22 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-007 | A-22 | Critical | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-008 | A-22 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-009 | A-22 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-010 | A-22 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-011 | A-22 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| PRESS-012 | A-22 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| HER-001 | A-23 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| HER-002 | A-23 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| HER-003 | A-23 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| HER-004 | A-23 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| HER-005 | A-23 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| HER-006 | A-23 | Medium | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| HER-007 | A-23 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| HER-008 | A-23 | High | Candidate | 0 | Pending development | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | Pending Development | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| RIGHTS-001 | A-24 | High | Candidate | 0 | Pending development | 1 | Horizon integration decision | 2026-06-25 | Issue-admission test | [Issue](areas/RIGHTS/issues/RIGHTS-001.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
| RIGHTS-002 | A-24 | High | Candidate | 0 | Pending development | 1 | Horizon integration decision | 2026-06-25 | Issue-admission test | [Issue](areas/RIGHTS/issues/RIGHTS-002.md) | — | 2026-06-26.1 | current-fixed-status | N/A | N/A | N/A |
