---
title: "Repository Structure"
print_status: excluded
print_exclusion_reason: "Online technical documentation."
---

# Repository Structure

This file is the single authority for the purpose and placement of project directories and files. It describes where material belongs; it does not duplicate the substantive rules housed there. Cross-cutting principles, authority boundaries, and the human-readable module route table remain in the compact [`FRAMEWORK.md`](FRAMEWORK.md) kernel. Universal agent-execution rules remain in the compact [`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md) kernel. Detailed rules live in the independently loadable modules identified below and registered through [`CONTEXT_ROUTING.md`](CONTEXT_ROUTING.md) and [`context-routes.json`](context-routes.json). GitHub lifecycle mechanics remain in [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md), and print rules remain in [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md).

Each governing rule family has one authoritative home. Kernels, modules, runbooks, manifests, and generated views may link to or route to that authority, but must not create a competing definition.

## Root Files

| Path | Purpose |
| --- | --- |
| `README.md` | Public front door, premise, scope, reader guidance, and navigation. |
| `UNDER_REVIEW.md` | Public, generated-status page listing formal candidates, active investigations, held questions, and established issues with external developments being monitored. |
| `PRINT_READERS_GUIDE.md` | Front-matter guidance for compiled editions, including generated issue locators and online technical-record access. |
| `SUBJECT_INDEX.md` | Cross-area subject and institution lookup. |
| `ABOUT.md` | Public About page, authorship, stewardship, technical-access, and contact information. |
| `SUPPORT.md` | Public website-only support, funding-independence, access, rights, and tax-status notice. |
| `CONTRIBUTING.md` | Contribution and review expectations. |
| `LICENSE.md` | Rights and reuse terms. |
| `CITATION.cff` | Machine-readable citation metadata. |
| `AGENTS.md` | Required root-level bootstrap and task router for Codex. It remains at the repository root because agent tooling discovers it there; detailed rules live under `framework/`. |
| `.rgignore` | Search-performance exclusions for generated, dependency, cache, and bulk Console projections; it does not change Git tracking or publication. |
| `mkdocs.yml` | Public-site presentation and search configuration. |
| `requirements-pages.txt` | Pinned GitHub Pages build dependencies. |
| `requirements-local-tools.txt` | Pinned local website and document-processing Python dependencies. |
| `.gitignore` | Local-product, credential, cache, and generated-artifact exclusions for Git. |

## Directories

| Path | Purpose |
| --- | --- |
| `.github/` | GitHub-native community-health files, security reporting policy, workflows, and automation configuration. GitHub requires these recognized files to remain here. |
| `assets/branding/` | Official project-emblem master and publication derivatives for the website and compiled editions. |
| `areas/` | One directory per institutional area; each area contains its reader index, issue pages, audit sidecars, and area-owned research or evidence. |
| `legislation/` | Proposed statutory, constitutional, regulatory, procedural, and model-state language keyed to issue identifiers. |
| `topics/` | Selective public guides connecting recognizable subjects to authoritative project proposals and final non-inclusion decisions. |
| `framework/` | Cross-project governing kernels, independently loadable rule modules, specialized authorities, routing records, logs, and templates. |
| `inventory/` | Canonical source catalogs, presidential-directive screening registry, and stable GitHub issue navigation. |
| `research/` | Cross-project ARRP-created analyses, crosswalks, transformed datasets, and internal research tools. |
| `sources/` | Selectively retained external source files and backup copies; it is not a mirror of the bibliography. |
| `participate/` | Separately deployed public-input and private-author-contact service. |
| `website/` | GitHub Pages publication policy and website-only presentation assets. `website/404.md` remains here because it is a website asset, not a print-controlled page. |
| `scripts/` | Repeatable maintenance, synchronization, validation, monitoring, console, and publication utilities. |
| `tests/` | Regression tests for automation and repository conventions. |
| `exports/` | Generated PDF, DOCX, XLSX, and related export artifacts. |

Ignored local products such as `.venv/`, `.tmp/`, and `.site-build/` are not project materials and are not cataloged individually.

## Framework Files

| Path | Purpose |
| --- | --- |
| `framework/FRAMEWORK.md` | Compact mandatory project kernel: guiding principle, cross-cutting rules, authority boundaries, module routes, and compatibility anchors. Detailed rule families remain authoritative in their routed modules. |
| `framework/CONTEXT_ROUTING.md` | Human-readable authority for additive context assembly, dependency closure, dynamic expansion, hash maintenance, fail-closed behavior, and comprehensive-review boundaries. |
| `framework/context-routes.json` | Machine-readable registry of stable governing-document IDs, dependencies, capabilities, operation profiles, hash policies, and packet limits. It routes to authority but does not replace it. |
| `framework/REMEDY_FRAMEWORK.md` | Remedy taxonomy, trigger stages, and shared-remedy principles. |
| `framework/INTERBRANCH_REVIEW_FRAMEWORK.md` | Governing JUD-011 coverage and proposal-independence convention. |
| `framework/INTERBRANCH_REVIEW_COVERAGE_MATRIX.md` | Proposal inclusion, exclusion, and future-screening record for the interbranch framework. |
| `framework/GITHUB_WORKFLOW.md` | GitHub Issues and Project authority, lifecycle transitions, synchronization, and authenticated-operation rules. |
| `framework/AGENT_OPERATING_RULES.md` | Compact mandatory execution kernel for every agent and bot: universal authority, human-reserved boundaries, persistent-runbook rules, and routes to detailed operating modules. |
| `framework/PROJECT_INTERFACE.md` | Authoritative visual, interaction, accessibility, data-presentation, and information-architecture standard for project-operated consoles, forms, dashboards, and similar tools. |
| `framework/agents/` | Registry and one authoritative configuration/runbook for every persistent named agent or bot. Runtime manifests and workflows are validated projections of these records. |
| `framework/INTAKE_AGENT_PROCESS.md` | Security-sensitive public-intake review process, limited Elim reply and preliminary-candidate authority, and future-automation boundary. It remains separate from general agent rules because contributor content is untrusted and review authority is deliberately narrower. |
| `framework/PRINT_ASSEMBLY.md` | Print-selection, ordering, locator, and export rules. |
| `framework/print-assembly.json` | Machine-readable compiled-edition section and ordering manifest. |
| `framework/PROJECT_CONSOLE_PROGRESS.md` | Project Console progress calculation and display governance. |
| `framework/PUBLIC_RELEASE.md` | Public-release preparation and verification rules. |
| `framework/PROJECT_STRUCTURE.md` | This repository-purpose and placement authority. |

## Framework Module Directories

The kernel route table and context registry determine which modules an operation must load. Routes are additive: selecting one operation never excludes another implicated module, and every selected module brings its dependency closure. Directory placement identifies a module's subject; it does not permit that module to redefine another subject's authority.

| Path | Single purpose |
| --- | --- |
| `framework/agent-rules/` | Detailed operating rules shared by agents and bots: audit execution, autonomous execution, research context, handoff, issue and candidate work, delegation, provenance, validation, and closeout. Persistent role-specific configuration belongs in `framework/agents/`. |
| `framework/audits/` | Audit methods and evidence-bearing review protocols, including audit core rules, T-audits, Change Audits, project-consistency review, legal and prior-proposal review, and verification. Scoring formulas and rubric definitions belong in `framework/scoring/`. |
| `framework/scoring/` | Proposal-quality rubrics, score consistency, adoption and pathway analysis, external review, and international-support scoring. Audit execution and preservation belong in `framework/audits/`. |
| `framework/methodology/` | Substantive analytical method: scope and admission, neutrality and language, and treatment of partisan perception and public actors. |
| `framework/issues/` | Canonical issue-page architecture, proposal-vehicle presentation, issue-to-vehicle alignment, snapshot form, and issue-level conciseness. |
| `framework/lifecycle/` | Substantive maturity levels, human-governed foundations, and post-admission development gates. GitHub workflow Status, hold predicates, and field mechanics remain in `framework/GITHUB_WORKFLOW.md`. |
| `framework/evidence/` | Annotation, assertion, and source-quality standards plus issue evidence-record architecture and reconciliation. Source-catalog and monitoring mechanics belong in `framework/sources/`. |
| `framework/sources/` | Source catalogs, stable routing identities, project monitoring, automated source adjudication, and presidential-directive completeness methods. Retained source files themselves remain in the repository-root `sources/` directory. |
| `framework/candidates/` | Horizon discovery and formal candidate adjudication methodology. GitHub candidate-queue mechanics remain in `framework/GITHUB_WORKFLOW.md`. |
| `framework/navigation/` | Inventory and area-index conventions, public topic-guide standards, canonical cross-references, and navigation synchronization. |
| `framework/operations/` | Cross-module operational checks for issue-development preflight and closeout and for project-wide update reconciliation. These checklists invoke, but do not replace, the implicated subject authorities. |

## Logs and Templates

| Path | Purpose |
| --- | --- |
| `framework/logs/CURRENT_AUDIT.md` | Mutable continuation checkpoint for the current unfinished long-running audit or development task. It lives with logs for discoverability but is neither runtime-liveness state nor historical audit evidence. |
| `framework/logs/HORIZON_SCAN_LOG.md` | Cumulative candidate disposition and integration history. |
| `framework/logs/CHANGE_AUDIT_LOG.md` | Preserved historical project-wide Change Audit record. |
| `framework/logs/AGENT_AUDIT_LOG.md` | Shared provenance and rollback ledger for material actions by every persistent agent and bot. |
| `framework/logs/ELIM_RUN_LOG.md` | Complete per-run operational reports for Elim, with links to issue audit histories and shared material-action provenance. |
| `framework/logs/SOURCE_MONITOR_LOG.md` | Source-domain event record for accepted or proposed monitoring changes; it does not replace shared agent provenance. |
| `framework/logs/PROJECT_INTEGRITY_REPORT.md` | Overwritten current integrity findings; not a running audit log. |
| `research/intake-review-ledger.jsonl` | Append-only, content-free processing cursor created after the first completed public-submission assessment; it prevents repeat review without copying submission text or private contact data. |
| `research/intake-action-ledger.jsonl` | Append-only provenance for actions taken on public submissions; it is created only when the first action occurs. |
| `research/review-epochs.jsonl` | Append-only boundaries for completed comprehensive automated reviews, including governing hashes, reviewed scope, unresolved exceptions, and the next due date. |
| `framework/templates/` | Reusable project-authored drafting templates. Public input is routed through the separately deployed participation service rather than GitHub issue forms. |

## Content Placement Rules

- Every institutional defect has one primary issue page; adjacent areas and topic guides link to it instead of duplicating its analysis.
- Area-owned ARRP research belongs in `areas/<AREA>/research/`; research spanning areas or supporting project-wide infrastructure belongs in `research/`.
- Every issue-specific research record must be linked from its owning issue or area page.
- Reader-facing supplemental evidence belongs in `areas/<AREA>/evidence/` only when separate treatment improves clarity or monitoring. Internal source-development records remain research material.
- External reports, filings, raw downloads, and backup copies belong in `sources/` only when local retention is useful and legally and practically appropriate for verification, preservation, or backup. Their bibliographic status is governed by `inventory/sources.csv` and `inventory/sources-pending.csv`.
- Directory README files are either concise purpose-and-boundary notes for support directories or canonical reader indexes for public content collections. Project-wide rules belong in their governing framework file, not in directory READMEs.
- Generated public-site, console, and print artifacts are views of canonical Markdown, CSV, JSON, GitHub, and log records; they do not become independent authorities.
