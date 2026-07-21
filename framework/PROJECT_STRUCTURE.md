---
title: "Repository Structure"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Repository Structure

```text
README.md                          Public project front door, scope, and reader navigation
SUBJECT_INDEX.md                   Cross-area subject and institutional-body lookup
AGENTS.md                          Repository-local operating instructions for Codex
AUTHORS.md                         Authorship and stewardship information
CONTRIBUTING.md                    Contribution and review expectations
LICENSE.md                         Rights and reuse terms
CITATION.cff                       Citation metadata
.github/                           GitHub automation, issue templates, and dashboard configuration
mkdocs.yml                         Public-site presentation and search configuration
requirements-pages.txt             Pinned public-site build dependencies
requirements-local-tools.txt       Pinned local website and document-processing Python dependencies
framework/                         Governing methodology, historical records, and operating rules
  FRAMEWORK.md                     Project framework and file-ownership rules
  METHODOLOGY.md                   Audit rules, scoring rules, and workflow rules
  REMEDY_FRAMEWORK.md              Remedy taxonomy and trigger stages
  PRINT_ASSEMBLY.md                Print/export assembly rules
  print-assembly.json              Machine-readable edition sections and ordering
  GITHUB_WORKFLOW.md               GitHub Issues/Projects workflow rules
  AGENT_OPERATING_RULES.md         Agent-assisted audit and batch-audit rules
  INTAKE_AGENT_PROCESS.md          Manual public-intake review and future-automation boundary
  CURRENT_AUDIT.md                 Current long-running audit handoff checkpoint
  PROJECT_CONSOLE_PROGRESS.md       Project Console progress governance and calculation rules
  PUBLIC_RELEASE.md                Public-release preparation and verification rules
  logs/                            Historical and operational cross-project logs
    SOURCE_MONITOR_LOG.md          Material deterministic watcher-change events and workflow provenance
    HORIZON_SCAN_LOG.md            Cumulative horizon-scan disposition and integration log
    AGENT_AUDIT_LOG.md             Autonomous-agent provenance, commits, and rollback references
    CHANGE_AUDIT_LOG.md            Read-only historical project-wide Change Audit record
    PROJECT_INTEGRITY_REPORT.md     Overwritten current integrity findings; not a running log
  templates/                       Reusable project-authored drafting templates
    ISSUE_EVIDENCE_TEMPLATE.md     Reader-facing evidence-record structure
    TOPIC_PAGE_TEMPLATE.md         Public topic-guide structure and table wrappers
  INTERBRANCH_REVIEW_FRAMEWORK.md
                                   Governing JUD-011 coverage and proposal-independence convention
  INTERBRANCH_REVIEW_COVERAGE_MATRIX.md
                                   Proposal inclusion, exclusion, and future-screening record
  PROJECT_STRUCTURE.md             Repository map and file ownership summary
areas/                             One directory per project area
  DOJ/                             Folder name matches the issue identifier prefix
    README.md                      Area concern and issue index
    issues/
      DOJ-001.md                   Developed issue analysis
    research/                      Issue-specific ARRP work product owned by this area
legislation/                       Proposed statutory language keyed to issue ID
topics/                            Public reader guides and cross-proposal topic crosswalks
  README.md                        Selective public topic-guide index
participate/                       Separately deployed public-interaction service and minimal lookup data
website/                           Public-site policy and website-only presentation assets
inventory/                         Structured source and GitHub issue registries
  sources.csv                      Relied-upon external-source registry
  sources-pending.csv              Temporary unresolved-routing source queue
  presidential-directives.csv      Presidential-instrument discovery and screening registry
  github_issue_registry.csv        Stable GitHub issue navigation registry
research/                          Cross-project ARRP research, crosswalks, and research tools
sources/                           External source and backup files retained locally
scripts/                           Repeatable maintenance, intake, synchronization, and publication utilities
tests/                             Regression tests for project automation and repository conventions
exports/                           Generated DOCX, PDF, and XLSX outputs
```

## File ownership

- **Required locations and exceptions.** Root `AGENTS.md` remains at the repository root because Codex discovers repository-wide instructions there; detailed rules belong in `framework/AGENT_OPERATING_RULES.md`. As a tool-discovered control file, it is exempt from compiled-edition metadata. `website/404.md` is likewise a website-only asset rather than a compiled-edition page. `.github/ISSUE_TEMPLATE/` remains in `.github/` because GitHub recognizes native issue forms and configuration only there; reusable ARRP drafting templates belong in `framework/templates/`. `framework/CURRENT_AUDIT.md` remains at the framework root because it is the current handoff checkpoint, not a historical log. `INTERBRANCH_REVIEW_FRAMEWORK.md` and `INTERBRANCH_REVIEW_COVERAGE_MATRIX.md` remain in `framework/` because they govern the cross-project JUD-011 remedy architecture rather than serving as research work product.
- A defect has one primary issue file.
- A major public subject may have one canonical topic page under `topics/` that concisely routes to authoritative records and identifies materially related rejected or outside-scope concepts without acquiring ownership of proposal substance, rejection decisions, scoring, audits, workflow state, or development tasks. Deferred records remain regular routes; merged or integrated records appear through their current homes rather than separate topic-page disposition entries. The Topic Page Standard in `METHODOLOGY.md` governs admission, structure, concision, and the verbatim-transfer test. If an existing ARRP research crosswalk becomes the public topic page, move and convert that file rather than retaining parallel copies.
- `SUBJECT_INDEX.md` maps organizations, subjects, acronyms, and aliases in one alphabetical sequence to concise linked record identifiers, with the preferred route first and common alternate terms redirected through **See** entries, without changing issue ownership.
- `README.md`, `areas/README.md`, the affected area README, `SUBJECT_INDEX.md`, any affected canonical topic page, and the GitHub issue registry form the reader-navigation bundle and are synchronized immediately for routing changes, with mandatory verification at T1. The root README exposes topic-guide, subject-index, and area-first discovery near its opening.
- Related areas cross-reference the primary file instead of duplicating analysis.
- Legislative drafts use the corresponding issue identifier.
- GitHub Projects is the authoritative area, issue, status, milestone, roadmap, and horizon-queue tracker.
- Source records in `inventory/sources.csv` are the relied-upon external-source registry and support assertions or explicitly qualified source-development questions in issues, areas, framework files, research files, topic guides, candidate records, or project-level pages. `inventory/sources-pending.csv` is a temporary queue limited to stable-ID sources whose accountable destination remains genuinely unclear. Verification, monitoring, or incomplete issue development remains recorded with the routed source in `sources.csv`. Both catalogs use `Monitoring` to distinguish changing sources that independently warrant recurring checks from static records; monitored rows also state a `Monitoring Rationale` and `Monitoring Group` so the reason and common matter remain intelligible.
- Authorship controls the research/source boundary: unpublished ARRP-created analyses, crosswalks, catalogs, transformed datasets, and visualizations belong in an area `research/` directory when one area owns them, or in the root `research/` directory when they span areas or support project-wide research infrastructure. A project-authored synthesis selected as a canonical public topic guide belongs in `topics/`; external reports, filings, raw downloads, and backup copies belong in `sources/` when local retention is useful and appropriate.
- Research work product is not a second proposal corpus: its analyses and tools may support an issue or topic guide, but the canonical public treatment remains on the owning issue or topic page. An issue-specific research record must be linked from its owning issue or area page. The root research README identifies cross-project products and routes readers to area research. The internal ARRP Project Console is a non-authoritative view of Review Ready progress, preliminary candidates, GitHub-authoritative formal candidates, both canonical source catalogs, the four canonical project logs, the presidential-directives registry, proposal or formal-candidate issues carrying `needs: monitoring`, automated integrity findings, and every controlled page's publication disposition. Its second primary tab, Action Items, is a linked inbox for matters requiring human decisions or review; routine issue monitoring stays in Sources for automated LLM-assisted review until a detected development or exception requires attention. Its Integrity workspace presents the generated consistency report and bounded run history without creating a new canonical audit ledger. Its Logs workspace makes complete canonical entries searchable, sortable, and groupable without creating another ledger. Its Publication workspace separately exposes pages included in editions, explicitly excluded with reasons, unclassified, or conflicting, and can stage or export disposition and assembly-order changes for later Codex validation without editing canonical files; its Watchers workspace provides Court Cases, Presidential Directives, and Issues being monitored views without replacing their owning CSV, registry, GitHub, log, or front-matter records.
- `sources/` is deliberately selective local preservation, not a mirror of every citation. Its directory README identifies each retained external file and its source-inventory record.
- `scripts/` and `tests/` are implementation support for repeatable project maintenance; they are not reader-facing project content. `.venv/` (project-local Python environment), `.tmp/` (temporary work), and `.site-build/` (generated Pages staging artifact) are ignored local build products and are intentionally not cataloged as project materials.
- `.github/workflows/case-monitor-bot.yml`, `.github/case-monitor-bot.json`, and `scripts/check_case_updates.py` implement the scheduled `case-monitor-bot`, which runs daily near midnight Eastern and retains manual dispatch. It compares cataloged, mapped court-case sources against the Just Security tracker and stores each accepted fingerprint in that source row's `Monitoring Baseline`. A material change produces a dedicated, owner-assigned pull request and a stable-coded entry in `framework/logs/SOURCE_MONITOR_LOG.md`; no-change runs remain in Actions, and failures fail closed. New or unmatched-case discovery remains part of separate intake and project-wide monitoring scans.
- The presidential-directives watcher is a scheduled deterministic comparator that also permits manual dispatch. It uses the registry's `Content Fingerprint` and `Last Changed` fields as its accepted baseline. A material change proposes only authorized metadata updates through a dedicated, owner-assigned pull request and records the event in `framework/logs/SOURCE_MONITOR_LOG.md`; no-change runs remain in Actions, and failures fail closed. LLM-assisted review owns project relevance, issue routing, preliminary-candidate synthesis, deferral, and no-action dispositions.
- Directory README files serve only one of two roles: a concise purpose-and-boundary description for a support directory, or the canonical reader index for a public content collection such as areas, legislation, or topics. Global audit, source, lifecycle, drafting, and agent instructions belong in the governing framework, methodology, GitHub workflow, or agent-operating rules rather than being repeated in directory READMEs. A subsystem README may retain local deployment, security, build, or operation instructions that cannot usefully live in a project-wide rule.
- `inventory/sources.csv` remains the relied-upon registry for external sources whether or not a local copy is retained; `inventory/sources-pending.csv` is only the unresolved-routing queue. The repository does not download every registered source merely because it appears in the inventory.
- `inventory/presidential-directives.csv` retains directive identity and disposition history across the first Trump, Biden, and second Trump administrations so automated discovery does not recreate reviewed instruments. It is not a bibliography and does not replace either source catalog.
- GitHub Project items/fields, retained source inventory, audit-history sidecars, and affected Markdown pages should be updated in the same change that adds, removes, renames, merges, retires, or materially revises an area, issue, legislative proposal, audit status, or cited source.
- GitHub Project fields provide the compact cross-issue workflow, audit-status, and release-triage view.
- The public website is generated from the canonical Markdown rather than maintained as a second copy. `website/README.md` owns the publication boundary; `scripts/prepare_public_site.py` admits only `public-proposal` pages within the approved root, `areas/`, `legislation/`, and `topics/` paths; and the Pages workflow uploads only the validated generated artifact.
- The separately deployed `participate/` service is separated from unpublished research tooling and contains no internal source, monitoring, history, or candidate-review queues. It remains outside the Pages artifact by design: its public-input route posts to a canonical GitHub Discussion, its author-contact route sends only to the configured private mailbox, and formal intake review remains manually initiated through Codex. It and the internal ARRP Project Console follow the project-operated interface visual standard in `METHODOLOGY.md`; the canonical GitHub Pages and print themes remain separate.
- The `project-console-data` branch retains only generated progress/history and integrity-report JSON for the internal Project Console; it contains no duplicate reader-facing dashboard and remains excluded from the website artifact.
- `framework/CURRENT_AUDIT.md` is the active handoff checkpoint for long audits and should be read before resuming vague follow-up instructions.
- Project-wide structural and integration checks update the governing files, validation scripts, and tests that own their durable findings; they do not create a new cumulative audit ledger or stand-alone report. Existing historical audit records remain preserved read-only.
- Audit rules and scoring live in `METHODOLOGY.md`; print assembly rules live in `PRINT_ASSEMBLY.md`; remedy categories and trigger stages live in `REMEDY_FRAMEWORK.md`.
