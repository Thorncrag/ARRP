---
title: "ARRP Project Console and Interface Configuration"
status: active
print_status: excluded
print_exclusion_reason: "Internal interface-governance documentation."
module_id: project_interface
load_when:
  - "Designing, changing, or reviewing an ARRP dashboard, console, form, or other application-like interface."
dependencies:
  - "../../standards/interfaces/standard.md"
  - "../../standards/interfaces/progress-views.md"
  - "visual-identity.md"
  - "project-console-progress.md"
  - "../workflows/candidate-review.md"
  - "../workflows/source-adjudication.md"
---

# ARRP Project Console and Interface Configuration

This file configures the ARRP Project Console under the reusable
[Project Interface Standard](../../standards/interfaces/standard.md), the
[Progress View Standard](../../standards/interfaces/progress-views.md), and
ARRP's [tool visual identity](visual-identity.md).

## Project Console Information Architecture

Candidate terminology and identifiers are governed by the
[ARRP candidate workflow](../workflows/candidate-review.md#preliminary-candidate-synthesis-and-promotion),
and the exact source catalogs and routing fields are governed by the
[ARRP source workflow](../workflows/source-adjudication.md). This file governs
where and how those records are presented in project-operated interfaces.

The ARRP Project Console has nine primary tabs in this order: **Overview**, a compact project-wide orientation; **Progress**, containing the proposal-development board, workflow summaries, holds, and monitored issues; **Action Items**, the central linked inbox for matters requiring human review or intervention; **Candidates**, containing proposed-candidate and preliminary-candidate subviews; **Sources**, containing cited sources, pending sources, automated watchers, and source-bot views; **Integrity**, grouping current exceptions and retained project gaps by accountable owner and authority disposition; **Agents & Bots**, presenting authoritative runbooks, runtime posture, governance-discovery activity, and Elim-owned obligation status; **Logs**, containing searchable, sortable, groupable projections of the canonical Horizon Scan, Agent Audit, Source Monitor, retained Integrity-run, historical Change Audit, and Elim discovery-detail records; and **Publication**, containing page publication dispositions, edition analysis, and a document builder.

Those views are nonauthoritative projections: lifecycle and candidate authority remains in GitHub, bibliographic authority remains in the two source catalogs, each project log remains authoritative in its canonical Markdown file, committed Elim Run Log discovery markers remain the durable gap-reconstruction authority, presidential-directive identity and review history remains in the directive registry, and print disposition and assembly authority remain in page front matter and [`print-assembly.json`](../publication/print-assembly.json). The Publication assignment view must make included, explicitly excluded, unclassified, and conflicting outcomes independently visible. Routine issue monitoring remains in Progress and does not count as a human Action Item unless it produces an exception or decision requiring attention; automated watcher and source-bot operations remain in Sources. Routine Elim-owned gap review, and retained `forbidden`, `unsafe`, `out_of_scope`, or `uncertain` observations that do not require a human act, remain in Integrity or Agents & Bots. They enter Action Items only when an exact human judgment, credential, unsafe external action, owner-gated decision, or intervention is required. Locally staged publication changes remain in Publication and likewise do not count as Action Items. The Action Items view must route each count to its complete owning view and must not duplicate narrative workflow records. The Logs view is read-only, retains complete entries without pagination, and links to each authoritative log or retained bounded feed; it must not become a separately maintained ledger. Publication controls may stage and export instruction lists for Codex, but do not persist drafts or edit canonical files.

### Governance discovery and gap obligations

The Console presents closed-loop governance discovery without creating another backlog or narrative ledger. The primary manager view must distinguish: current governance-discovery mode; the last committed review outcome and time; its next-due time under the 168-hour minimum interval; open, investigating, blocked, human-required, resolved, and human-disposition obligation states; severity; owner; authority classification; separate `permitted`, `human_reserved`, `forbidden`, `unsafe`, `out_of_scope`, or `uncertain` disposition; first seen; last checked; occurrence count; age; exact next action; next trigger; and a canonical-detail link. A current `no_material_finding` review remains visible but must not imply that Elim will relaunch on every poll. Repeated observations remain one stable obligation. A missing later observation, clean aggregate, rebuilt feed, merge, or report-only result must not appear as resolution. Closed rows require visible verified-repair or recorded-human-disposition evidence.

Compact cards and queue rows must link to full canonical detail rather than copy evidence, reasoning, uncertainty, consequence, affected records or surfaces, validation, and provenance. The full record remains available through the Logs projection of the committed Elim Run Log. If the temporary gap cache is missing, stale, or inconsistent with reconstructible committed markers, show the cache as unavailable or rebuilding; never present cache absence as zero gaps. An outside-contribution review must expose the exact reviewed revision and separate results for identity, classification, required fields, canonical linkage, evidence and provenance, lifecycle and authority, generated views, tests, and documentation; a changed head invalidates the earlier ready posture.

Each proposed-candidate view should be a decision dossier assembled from existing authoritative records: GitHub supplies issue and lifecycle data; the Horizon Scan Log supplies intake history, overlap, rationale, and follow-up; the two source inventories supply evidentiary records; and identifier-linked research supplies project analysis. Display missing inputs as record gaps rather than filling them with generated conclusions. The console may cache this derived presentation data, but it must not become a manually maintained narrative ledger or override its inputs; corrections belong in the record that owns the information. Canonical records remain read-only to the console. The Console may submit an authenticated request to the localhost-only Run Coordinator control plane asking the coordinator to evaluate a run, comprehensive review, reprioritization, or suppression under its own rules. That request does not directly invoke or select an agent and does not guarantee execution. No interface control may bypass repository, context, authority, usage, freshness, locking, or human-reserved gates; directly invoke or select an agent; record or implement a disposition; or mutate GitHub or project files. A local print-level draft and export is not an implementation; Codex must validate and apply it separately. Conduct every formal candidate decision within Codex under the full Horizon Candidate Adjudication Workflow.

## Monitoring and Source Inspection

GitHub Issues and the Project Monitoring view are the issue-level monitoring-workflow authority. The Console separates issue workflow from source inspection: **Progress** contains the read-only **Issues being monitored** group, while **Sources** contains Court Cases, Presidential Directives, and Source Checks. The Progress group organizes monitored matters by accountable ARRP owner and, where useful, by a named case family, executive-action episode, or other factual matter.

Every view must distinguish: (1) the external matter being watched; (2) why it is materially relevant to future issue development; (3) what development triggers reassessment; (4) whether a deterministic watcher, an LLM-assisted pass, or another stated checking method covers it; and (5) its latest known posture. Routine issue monitoring is intended for automated LLM-assisted review and is not itself a human Action Item merely because `needs: monitoring` remains present. Only a detected development, exception, or resulting decision that requires human attention enters Action Items. The console does not create, close, edit, or adjudicate an issue.

The **Sources** and **Pending sources** subviews expose each source's `Monitoring` value so a changing docket or similar record remains identifiable even when the owning issue is not currently in an issue-wide monitoring pass. Ordinary badges state the complete queue size. A visually distinct update badge states only a genuinely new or changed record awaiting review, using the directive registry status or an unresolved deterministic-watcher pull request; do not use the update color merely to restate a queue total. The substantive distinctions among issue monitoring, source monitoring, deferral, and blockage remain governed by [`monitoring.md`](../../standards/sources/monitoring.md), [`source-records.md`](../../standards/sources/source-records.md), and the [ARRP GitHub workflow](../github/workflow.md).

## Source Projection Refresh

Rebuild the ARRP Project Console whenever candidate data, either canonical
source catalog, a source-monitoring designation, an issue-level monitoring
label, the presidential-directive registry, watcher configuration, a canonical
project log, page-level publication-disposition metadata, or
[`print-assembly.json`](../publication/print-assembly.json) changes.

The Console's progress, source, pending, watcher, integrity, log, and
publication presentations are generated views. A rebuild refreshes those views
but does not create another workflow, source, candidate, log, or publication
authority.

## Pending Source Presentation

The **Pending** tab is a small routing-decision view, not a development or monitoring backlog. Each retained row must identify the plausible competing destinations, explain why the project cannot yet choose among them, and state the exact source-specific review needed to decide ownership. Do not group pending records as citation-ready, litigation, monitoring, or general project development: once any one of those records has a clear owner, it belongs in that owner's source-development record and `sources.csv`. The tab projects `sources-pending.csv`; it does not duplicate or supersede the underlying record.
