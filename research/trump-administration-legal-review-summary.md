---
title: "Trump Administration Legal-Review Research Summary"
print_levels:
  - full-technical
---

# Trump Administration Legal-Review Research Summary

## Purpose and Boundary

This record summarizes the completed first- and second-term source-discovery review used to identify legally or institutionally questionable executive conduct that might expose a repairable weakness. It is a research history and completeness aid—not a continuing source queue, a conclusion that any action was unlawful, or an automatic basis for admitting a proposal.

The review applied the project's ordinary institutional-failure, political-failure, duplicate, reversed-party, durable-harm, source-quality, and least-complex-remedy tests. Litigation posture was used to prioritize review, not to treat the filing of a lawsuit or entry of preliminary relief as proof of a defect.

## Completed Tracker Review

The machine-normalized baseline contained 1,322 records from seven differently structured sources. After the initial priority review, the project adjudicated the remaining 1,266 records as 1,250 conservatively clustered episodes. The review retained 160 records for qualitative issue integration, retained 178 records as 174 defined-predicate monitoring episodes, and found that 928 records were cumulative, topical-only, ordinary-policy, insufficiently specific, or otherwise did not warrant a continuing project record.

The source families were the [Just Security litigation tracker](https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/), [Institute for Policy Integrity court roundup](https://policyintegrity.org/trump-court-roundup), [Immigration Policy Tracking Project](https://immpolicytracking.org/policies/?status=in-litigation), [Columbia Human Rights Tracker](https://trumphumanrightstracker.law.columbia.edu/), [Protect Democracy retaliatory-actions tracker](https://protectdemocracy.org/work/retaliatory-action-tracker/), [Public Citizen lawsuit tracker](https://www.citizen.org/article/trump-administration-2-0-lawsuit-tracker/), and [Silencing Science Tracker](https://silencingscience.org/).

The completed review established several methodological limits:

- tracker entries are discovery aids and do not replace underlying dockets, orders, official instruments, or final findings;
- several records can concern one action, while one action can affect several proposals;
- litigation over ordinary policy implementation does not itself establish an institutional defect;
- open and interlocutory cases ordinarily belong in a defined GitHub monitor rather than proposal prose;
- cumulative reporting should not inflate either the number of manifestations or the number of candidate issues; and
- a source remains in `sources-pending.csv` until an accountable project record actually relies on it.

## Media-Corroboration Review

A separate episode-based review examined 33 matters reported by at least two independent reliable news organizations and sought a primary instrument for each. The lane located events that might never produce litigation, but it did not treat two-source reporting as a substitute for an obtainable executive order, memorandum, demand, filing, official report, contract record, or comparable primary material.

The completed episode worksheet has been retired. Sources not already used in project prose remain in `sources-pending.csv` with their proposed owner, evidentiary purpose, and remaining placement question.

## Presidential-Directive Completeness Review

The [Federal Register presidential-documents collection](https://www.federalregister.gov/presidential-documents) supplied the official discovery corpus. The review covered 1,125 first-term documents and 579 second-term documents through July 18, 2026. It treated corrections as versions of the corrected instrument and distinguished presumptively ceremonial material from potentially operative directives requiring substantive review.

Across both terms, the review identified 1,069 unmatched operative records. It routed 534 to existing project mechanisms, found 424 required no further project action, and retained 111 directives as evidence for five formal proposed candidates:

| Proposed candidate | Supporting directives | Question preserved for review |
| --- | ---: | --- |
| `HOR-040` | 51 | Safeguards for broad presidential tariff delegations outside IEEPA. |
| `HOR-041` | 21 | Safeguards for class-based presidential entry suspensions. |
| `HOR-042` | 26 | Minimum safeguards for express presidential statutory waivers. |
| `HOR-043` | 1 | Presidential recognition of international bodies receiving domestic legal privileges. |
| `HOR-044` | 12 | Statutory standards for presidential cross-border infrastructure permits. |

Each retained directive now has its own stable `sources.csv` entry associated with its formal candidate. The former directive catalog and routing table were removed because they duplicated the bibliography and candidate associations.

## Current Source and Monitoring Architecture

The completed intake now resolves into the project's ordinary records:

- `inventory/sources.csv` contains external sources affirmatively relied upon by an issue, topic, research record, formal candidate, or GitHub monitor;
- `inventory/sources-pending.csv` contains useful source-development, verification, monitoring, and placement leads not yet relied upon;
- GitHub proposed-candidate issues own candidate status and decision questions;
- `ISSUE-ID-MON` GitHub issues own current posture, last-checked dates, and reassessment triggers; and
- issue pages and evidence records contain reader-facing analysis only when the qualitative placement standard is satisfied.

No separate litigation ledger, source-universe ledger, media intake, evidence-integration queue, or candidate-evidence routing table is authoritative. Git history preserves those completed intermediate states.

## Remaining Completeness Work

Future scans should begin with the canonical source catalogs and GitHub monitoring records so they do not recreate resolved queues. Useful remaining lanes include official findings from GAO, the Office of Special Counsel, inspectors general, congressional reports, judicial noncompliance records, and specialized ethics, environmental, civil-rights, election, appointments, records, and war-powers sources.

A newly discovered source must leave review in one of three conditions: relied upon by a substantive record, GitHub monitor, or candidate dossier and placed in `sources.csv`; retained with an accountable owner in `sources-pending.csv`; or removed after a documented finding that it is duplicative, irrelevant, political-only, or adds no material evidentiary value.
