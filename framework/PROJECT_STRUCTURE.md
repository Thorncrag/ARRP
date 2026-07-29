---
title: "Repository Structure"
status: active
print_status: excluded
print_exclusion_reason: "Online technical documentation."
---

# Repository Structure

This file is the single authority for where project material belongs. It uses
one placement test:

1. **Standard:** Does the rule apply broadly across the project and remain
   useful when this repository is adapted as a future project template? Put it
   in [`standards/`](standards/).
2. **Project choice:** Does the record configure this ARRP installation, name
   an ARRP role or service, or adopt an ARRP-specific workflow or presentation?
   Put it in [`project/`](project/).
3. **Record:** Does the file primarily preserve state, history, evidence,
   results, or a baseline? Put it in [`records/`](records/).

Actual public and research content remains outside `framework/`. An issue,
legislative draft, topic guide, source-development record, research matrix, or
other substantive project product does not become Framework merely because it
is important or used by several files.

Each rule has one authoritative home. Entry points, route tables, runbooks,
configuration, and generated views may point to that authority but may not
create competing definitions.

A legacy file that mixes layers must be reorganized by meaning, not preserved
as an indivisible unit. Move reusable rules to the applicable standard,
ARRP-specific values and procedures to the project layer, and historical state
to records. Merge a section into an existing authority when that produces one
clearer rule; split it into separate authorities when the scopes differ. Retain
a historical baseline or version-control provenance when needed, but do not
keep duplicate live rules merely to preserve the former file boundary.

The layer directory guides are
[`standards/README.md`](standards/README.md),
[`project/README.md`](project/README.md), and
[`records/README.md`](records/README.md).

## Framework entry points

Only four governing entry points live directly in `framework/`:

| Path | Purpose |
| --- | --- |
| [`FRAMEWORK.md`](FRAMEWORK.md) | Cross-cutting project principles, authority boundaries, and the human-readable module route table. |
| [`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md) | Universal agent and bot execution kernel. |
| [`CONTEXT_ROUTING.md`](CONTEXT_ROUTING.md) | Additive context-selection, dependency, freshness, and fail-closed rules. |
| [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) | This placement authority and repository-purpose map. |

## Framework layers

| Path | Contains | Must not contain |
| --- | --- | --- |
| [`framework/standards/`](standards/) | Reusable standards, schemas, and templates arranged by the thing governed: content, sources, audits, publication, interfaces, and automation. | Named ARRP bots, exact GitHub fields, current project state, historical logs, or issue-specific substance. |
| [`framework/project/`](project/) | ARRP-specific profile choices, hosted-platform workflow, named runbooks, exact manifests, interface configuration, and adopted project procedures. | General methods that can govern all project content, or historical run results. |
| [`framework/records/`](records/) | Handoffs, audit histories, run logs, monitoring histories, current reports, and preserved baselines. | Methodology, permissions, schemas, or configuration authority. |

Records may provide evidence that a governing rule was followed. Their location
does not make them governing methodology or enlarge any actor's authority.

## Reusable standard families

| Path | Single purpose |
| --- | --- |
| [`framework/standards/content/`](standards/content/) | Admission, neutral characterization, content-record architecture, maturity, remedies, navigation, topic guides, and content templates. |
| [`framework/standards/sources/`](standards/sources/) | Claims, citations, source records, adjudication, monitoring, and source-record templates. |
| [`framework/standards/audits/`](standards/audits/) | Audit levels and methods, verification, Change Audits, consistency review, legal and prior-work review, and scoring disciplines. |
| [`framework/standards/publication/`](standards/publication/) | Print, export, edition, and release assembly. Topic guides remain content standards even when published on the website. |
| [`framework/standards/interfaces/`](standards/interfaces/) | Interface, progress-view, public-input, and work-tracking standards independent of one implementation. |
| [`framework/standards/automation/`](standards/automation/) | Reusable autonomous-execution, context, handoff, delegation, provenance, validation, and closeout rules plus schemas and templates. |

## ARRP project families

| Path | Single purpose |
| --- | --- |
| [`framework/project/profile/`](project/profile/) | ARRP-specific scope, public-actor, scoring, and other adopted profile decisions. |
| [`framework/project/github/`](project/github/) | Exact GitHub Issues and Project implementation plus the central outbound-disclosure category registry and enforcement boundary used by ARRP. |
| [`framework/project/workflows/`](project/workflows/) | ARRP audit, candidate, navigation, source-adjudication, public-input, presidential-directive, and project-update procedures. |
| [`framework/project/publication/`](project/publication/) | ARRP edition manifests and release-specific decisions. |
| [`framework/project/interfaces/`](project/interfaces/) | ARRP visual identity and Project Console configuration. |
| [`framework/project/automation/`](project/automation/) | ARRP agent policy, owner-local runtime authority, context registry, named runbooks, and exact automation schemas. |

Project-wide reconciliation uses the public
[`policy`](project/automation/project-wide-reconciliation.json) and
[`ledger schema`](project/automation/project-wide-reconciliation.schema.json);
complete evidence remains owner-local.

## Record families

| Path | Single purpose |
| --- | --- |
| [`framework/records/handoffs/`](records/handoffs/) | Mutable continuation state for unfinished work. |
| [`framework/records/audits/`](records/audits/) | Preserved project-wide audit history. |
| [`framework/records/automation/`](records/automation/) | Public-safe automation contracts and summaries, including Console development history and minimized disclosure classification. Complete agent/run, incident, gate, review-epoch, and active-operation authorities remain owner-local. |
| [`framework/records/governance/`](records/governance/) | Public-safe provenance for material governance decisions, including stable identity, Git evidence, validation, supersession, and separate adoption/activation posture. It does not replace governing authority, Change Audit history, or owner-local supplements. |
| [`framework/records/candidates/`](records/candidates/) | Candidate discovery and disposition history. |
| [`framework/records/sources/`](records/sources/) | Source-monitoring event history and dispositions. |
| [`framework/records/status/`](records/status/) | Current generated or overwritten status reports. |
| [`framework/records/baselines/`](records/baselines/) | Retired governing records retained as historical implementation baselines. |

## Repository content and support directories

| Path | Purpose |
| --- | --- |
| `areas/` | Institutional-area indexes, issue pages, audit sidecars, and area-owned research or evidence. |
| `legislation/` | Proposed statutory, constitutional, regulatory, procedural, and model-state language keyed to issue identifiers. |
| `topics/` | Public topic guides connecting recognizable subjects to authoritative project content and final non-inclusion decisions. |
| `research/` | Cross-project analysis, source-development records, crosswalks, transformed data, and nonauthoritative reference products. |
| `inventory/` | Canonical source catalogs, screening registries, and stable repository navigation data. |
| `sources/` | Selectively retained external materials and backups; bibliographic authority remains in the inventories. |
| `participate/` | Separately deployed public-input and private-contact service. |
| `website/` | GitHub Pages publication policy and website-only presentation assets. |
| `scripts/` | Deterministic maintenance, validation, monitoring, Console, and publication utilities. |
| `tests/` | Regression tests for automation and repository conventions. |
| `exports/` | Generated PDF, DOCX, XLSX, and related export artifacts. |
| `.github/` | GitHub-native community, security, workflow, and automation configuration required at GitHub-recognized paths. |

## Owner-local companion authority

`ARRP Private`, when present beside this repository in the verified local
Automation Workspaces boundary, is the sole owner-local companion workspace and
inactive successor staging authority. It is not a Git checkout, publication
source, second project authority, or current production runtime. It stages the
successor layout for restricted runtime state, private records, Security
Incident evidence and ledger, control packs, local Console
copies/projections, migration manifests, and recoverable quarantine material.
Its `OWNER_DIRECTIVE.md` and `AGENTS.md` govern access before any read or
change.

The current production runtime remains at the fixed Application Support
authority. The companion workspace has an inactive protected staging descriptor
with five logical roles: runtime state, durable records, owner Console copies,
security controls/evidence, and migration evidence. It does not become a live
runtime layout until Benjamin separately approves a host cutover with an exact
baseline and reconciliation plan. Exact path roles, logical `owner-local:`
resolution, and cutover requirements are governed by the [ARRP Owner-Local
Runtime Authority](project/automation/owner-local-runtime.md). Public
repository contracts may name owner-local authorities and schemas, but never
copy restricted records, evidence, or private topology into Git, the public
Console, or GitHub.

## Content placement rules

- Every institutional defect has one primary issue page. Adjacent areas and
  topic guides link to it instead of duplicating its analysis.
- Issue-specific research belongs with its owning issue or in an explicitly
  linked research record. Cross-area or project-wide analysis belongs in
  `research/`.
- A matrix applying a standard to named issues is research or project content,
  not the standard itself.
- Topic-guide structure belongs in `framework/standards/content/`; individual
  topic guides remain in `topics/`.
- Print and release rules belong in
  `framework/standards/publication/`; exact ARRP edition composition belongs in
  `framework/project/publication/`.
- Generated website, Console, and print artifacts are views of canonical
  Markdown, CSV, JSON, hosted-platform, and record data. They do not become
  independent authorities.
- Directory README files may explain a directory boundary or provide a public
  index. Project-wide rules belong in their governing standard, not in a
  README.
