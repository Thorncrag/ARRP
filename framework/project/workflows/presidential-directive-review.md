---
title: "Presidential-Directive Completeness and Review"
status: active
authority_scope: "Covered presidential instruments, registry identity, official-source hierarchy, deterministic versus substantive review boundaries, and LLM disposition of new or changed directives."
load_when: "Collecting, screening, reviewing, routing, monitoring, or adjudicating a presidential directive or a presidential-directives registry change."
dependencies:
  - "../../FRAMEWORK.md"
  - "../../standards/sources/source-records.md"
  - "../../standards/sources/source-adjudication.md"
  - "../../standards/content/scope-and-admission.md"
  - "source-adjudication.md"
  - "../automation/runbooks/presidential-directives-bot.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Presidential-Directive Completeness and Review

## Authority and Dependencies

This file is the authoritative substantive method for presidential-directive
completeness and review. Reusable source-record and route-centered disposition
rules belong to the [Source Record Standard](../../standards/sources/source-records.md)
and [Source Adjudication Standard](../../standards/sources/source-adjudication.md);
ARRP's exact catalogs, fields, and evidence paths belong to
[ARRP Source Catalog and Adjudication](source-adjudication.md). Scope and
admission belong to the
[Scope and Admission Standard](../../standards/content/scope-and-admission.md).
The deterministic watcher's schedule, configuration, exact write boundary,
validation, and failure behavior belong to the
[Presidential Directives Bot runbook](../automation/runbooks/presidential-directives-bot.md).

## Load When

Load this file when collecting, screening, reviewing, routing, monitoring, or adjudicating a presidential directive; responding to a new or materially changed directive; or checking the substantive meaning of a presidential-directives registry event.

## Presidential-Directive Completeness Scans

Maintain [`../../inventory/presidential-directives.csv`](../../../inventory/presidential-directives.csv) as the durable discovery, deduplication, and screening registry for publicly released presidential instruments from the first Trump administration, the Biden administration, and the second Trump administration. Coverage begins January 20, 2017 and continues prospectively. Apply the same collection and screening rules without regard to president or party. The covered universe includes executive orders, proclamations, memoranda, determinations, notices, presidential orders, permits, corrections, and comparable operative presidential instruments; it does not ordinarily include speeches, nominations, routine press releases, or every White House posting.

Use the registry and its watcher as a completeness backstop for litigation, media, and specialist-source intake—not as a presumption that every executive order or presidential document identifies a project issue. The unit of analysis remains the generalized institutional weakness. A directive, correction, implementing agency action, and related litigation may be parts of one evidence episode; several directives using the same institutional mechanism may support one candidate; and one directive may require one primary analytic home plus affected-record cross-references.

Begin with the official Federal Register presidential-document corpus for the applicable administration and signing-date range. Normalize Federal Register document number first, then directive subtype and number, canonical Federal Register or GovInfo URL, and finally signing date plus normalized title for an unnumbered instrument. Treat corrections as versions of the corrected instrument and amendment, revocation, continuation, and disposition references as relationships rather than duplicates. FederalRegister.gov supplies discovery metadata; verify publication-ready legal text against the linked official GovInfo edition. Cross-check the current and archived White House presidential-action collections and GovInfo Compilation of Presidential Documents for official actions not captured in the Federal Register corpus.

The deterministic watcher may discover instruments; normalize and deduplicate metadata; relate corrections, amendments, revocations, continuations, and superseding documents; compute content fingerprints; detect changed official records; and make exact identifier or URL matches to existing registry and source records. It must not determine whether conduct presents an institutional rather than political failure, select a substantive owner from ambiguous subject matter, decide remedy fit, admit or reject a candidate, or characterize legal significance. Those judgments require LLM-assisted review under the ordinary project admission, neutrality, evidence, and remedy rules.

Before substantive review, compare each directive against issue and evidence pages, legislation, formal proposed candidates, active preliminary candidates, both source inventories, parent GitHub issues carrying `needs: monitoring`, and earlier directive dispositions. Plainly ceremonial proclamations, routine administration, ordinary policy implementation within delegated discretion, cumulative records adding no evidentiary value, and already-owned directives may receive a documented no-project-action or redundant disposition. Document type or a keyword alone may not decide the question: an operative proclamation, delegation, emergency continuation, policy reversal, or unnumbered order must remain reviewable when it may bypass a safeguard or expose a durable remedial weakness.

LLM review assigns each unresolved or materially changed directive one review disposition: route to an existing issue or formal candidate; attach to an existing preliminary candidate; create a new clustered preliminary candidate; defer under a defined reconsideration condition; retain for monitoring under a defined reassessment trigger; or reviewed with no project action. Apply the ordinary first substantive pass and independent challenge pass, including the canonical human-consequence and institutional-defect conclusions, the Political-Failure Boundary, duplicate and route-fit checks, the least-complex-remedy rule, and a neutral analysis of materially different political control. The reviewer may apply an existing human reversed-control decision but may not answer or infer that decision. If a plausible distinct institutional weakness remains without an existing owner, create or update one clustered `INTAKE-GAP-###` preliminary candidate and attach the directive source. Cluster by actor and power used, safeguard bypassed or missing, resulting institutional risk, and likely remedy family—not by directive title alone. Uncertainty belongs in the candidate's unresolved question, a Deferred reconsideration condition, or a monitoring reassessment trigger selected under the mutually exclusive workflow rules; it does not justify an orphan source row.

Retain reviewed directive rows in the registry so exact identity, relationships, review history, and disposition prevent duplicate intake. Hide completed dispositions from the Console's active review view by default rather than deleting them. Route every directive used as evidence or retained as a source-development lead to `sources.csv` under its existing issue, evidence record, formal candidate, or preliminary candidate and cross-reference the resulting stable Source ID. Use `sources-pending.csv` only while the directive's destination is genuinely unclear; do not treat the directive registry as a bibliography. Later scans begin after the recorded coverage cutoff and must not recreate previously adjudicated directives.

The deterministic watcher's timing, read and write boundaries, pull-request
behavior, acceptance semantics, failure conditions, and Source Monitor Log
responsibilities are maintained only in the
[Presidential Directives Bot runbook](../automation/runbooks/presidential-directives-bot.md).
Its output may identify a record for review but may not make a project
disposition.
