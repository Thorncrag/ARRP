---
title: "Repository Structure"
print_status: excluded
print_exclusion_reason: "Online technical documentation."
---

# Repository Structure

This file is the single authority for the purpose and placement of project directories and files. It describes where material belongs; substantive methodology remains in [`FRAMEWORK.md`](FRAMEWORK.md), GitHub lifecycle mechanics in [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md), and print rules in [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md).

## Root Files

| Path | Purpose |
| --- | --- |
| `README.md` | Public front door, premise, scope, reader guidance, and navigation. |
| `PRINT_READERS_GUIDE.md` | Front-matter guidance for compiled editions, including generated issue locators and online technical-record access. |
| `SUBJECT_INDEX.md` | Cross-area subject and institution lookup. |
| `ABOUT.md` | Public About page, authorship, stewardship, technical-access, and contact information. |
| `CONTRIBUTING.md` | Contribution and review expectations. |
| `LICENSE.md` | Rights and reuse terms. |
| `CITATION.cff` | Machine-readable citation metadata. |
| `AGENTS.md` | Required root-level bootstrap and task router for Codex. It remains at the repository root because agent tooling discovers it there; detailed rules live under `framework/`. |
| `mkdocs.yml` | Public-site presentation and search configuration. |
| `requirements-pages.txt` | Pinned GitHub Pages build dependencies. |
| `requirements-local-tools.txt` | Pinned local website and document-processing Python dependencies. |
| `.gitignore` | Local-product, credential, cache, and generated-artifact exclusions for Git. |

## Directories

| Path | Purpose |
| --- | --- |
| `.github/` | GitHub-native workflows and automation configuration. GitHub requires workflow files to remain here. |
| `assets/branding/` | Official project-emblem master and publication derivatives for the website and compiled editions. |
| `areas/` | One directory per institutional area; each area contains its reader index, issue pages, audit sidecars, and area-owned research or evidence. |
| `legislation/` | Proposed statutory, constitutional, regulatory, procedural, and model-state language keyed to issue identifiers. |
| `topics/` | Selective public guides connecting recognizable subjects to authoritative project proposals and final non-inclusion decisions. |
| `framework/` | Cross-project governance, methodology, remedy architecture, GitHub workflow, print assembly, agent rules, logs, and templates. |
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
| `framework/FRAMEWORK.md` | Canonical framework and methodology: scope, neutrality, issue architecture, evidence, sources, audits, candidate adjudication, and scoring. |
| `framework/REMEDY_FRAMEWORK.md` | Remedy taxonomy, trigger stages, and shared-remedy principles. |
| `framework/INTERBRANCH_REVIEW_FRAMEWORK.md` | Governing JUD-011 coverage and proposal-independence convention. |
| `framework/INTERBRANCH_REVIEW_COVERAGE_MATRIX.md` | Proposal inclusion, exclusion, and future-screening record for the interbranch framework. |
| `framework/GITHUB_WORKFLOW.md` | GitHub Issues and Project authority, lifecycle transitions, synchronization, and authenticated-operation rules. |
| `framework/AGENT_OPERATING_RULES.md` | Canonical detailed rules for ordinary and expressly authorized autonomous agent work. |
| `framework/INTAKE_AGENT_PROCESS.md` | Security-sensitive manual public-intake review process and future-automation boundary. It remains separate from general agent rules because contributor content is untrusted and review authority is deliberately narrower. |
| `framework/PRINT_ASSEMBLY.md` | Print-selection, ordering, locator, and export rules. |
| `framework/print-assembly.json` | Machine-readable compiled-edition section and ordering manifest. |
| `framework/PROJECT_CONSOLE_PROGRESS.md` | Project Console progress calculation and display governance. |
| `framework/PUBLIC_RELEASE.md` | Public-release preparation and verification rules. |
| `framework/PROJECT_STRUCTURE.md` | This repository-purpose and placement authority. |

## Logs and Templates

| Path | Purpose |
| --- | --- |
| `framework/logs/CURRENT_AUDIT.md` | Mutable handoff checkpoint for the current long-running audit or development task. It lives with logs for discoverability but is active state, not historical audit evidence. |
| `framework/logs/HORIZON_SCAN_LOG.md` | Cumulative candidate disposition and integration history. |
| `framework/logs/CHANGE_AUDIT_LOG.md` | Preserved historical project-wide Change Audit record. |
| `framework/logs/AGENT_AUDIT_LOG.md` | Provenance and rollback references for autonomous, batched, or scheduled agent commits. |
| `framework/logs/SOURCE_MONITOR_LOG.md` | Material deterministic watcher changes and workflow provenance. |
| `framework/logs/PROJECT_INTEGRITY_REPORT.md` | Overwritten current integrity findings; not a running audit log. |
| `framework/templates/` | Reusable project-authored drafting templates. Public input is routed through the separately deployed participation service rather than GitHub issue forms. |

## Content Placement Rules

- Every institutional defect has one primary issue page; adjacent areas and topic guides link to it instead of duplicating its analysis.
- Area-owned ARRP research belongs in `areas/<AREA>/research/`; research spanning areas or supporting project-wide infrastructure belongs in `research/`.
- Reader-facing supplemental evidence belongs in `areas/<AREA>/evidence/` only when separate treatment improves clarity or monitoring. Internal source-development records remain research material.
- External reports, filings, raw downloads, and backup copies belong in `sources/` only when local retention is useful. Their bibliographic status is governed by `inventory/sources.csv` and `inventory/sources-pending.csv`.
- Directory README files are either concise purpose-and-boundary notes for support directories or canonical reader indexes for public content collections. Project-wide rules belong in their governing framework file, not in directory READMEs.
- Generated public-site, console, and print artifacts are views of canonical Markdown, CSV, JSON, GitHub, and log records; they do not become independent authorities.
