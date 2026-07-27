---
title: "ARRP Repository Map"
status: active
print_status: excluded
print_exclusion_reason: "Internal project configuration."
---

# ARRP Repository Map

This is the ARRP installation map. General placement rules remain authoritative
in [`../PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md).

## Public entry records

| Path | Purpose |
| --- | --- |
| `README.md` | Public front door, premise, scope, and navigation. |
| `UNDER_REVIEW.md` | Generated public status of candidates, investigations, holds, and monitored issues. |
| `PRINT_READERS_GUIDE.md` | Front matter for compiled editions. |
| `SUBJECT_INDEX.md` | Cross-area subject and institution lookup. |
| `areas/README.md` | Ordered public index of ARRP institutional areas. |
| `topics/README.md` | Public index of selective topic guides. |
| `ABOUT.md` | Project authorship, stewardship, and contact orientation. |
| `SUPPORT.md` | Funding-independence, access, rights, and tax-status notice. |
| `CONTRIBUTING.md` | Contribution and review expectations. |

## Canonical substantive records

| Path | Purpose |
| --- | --- |
| `areas/<AREA>/issues/<ISSUE>.md` | Canonical issue diagnosis, remedy, and proposal summary. |
| `areas/<AREA>/issues/<ISSUE>.audit.md` | Preserved issue-specific audit history. |
| `areas/<AREA>/README.md` | Public area page containing active and historical issue routes. |
| `legislation/<ISSUE>.md` | Proposed legal or procedural vehicle. |
| `topics/*.md` | Public topic guides. |
| `research/` and `areas/<AREA>/research/` | Project-authored research and source-development records. |
| `inventory/sources.csv` | Canonical retained-source catalog. |
| `inventory/sources-pending.csv` | Temporary unresolved-source routing catalog. |
| `inventory/presidential-directives.csv` | Directive discovery and screening registry. |
| `inventory/github_issue_registry.csv` | Stable GitHub-item-to-canonical-page registry. |

## ARRP governing configuration

| Path | Purpose |
| --- | --- |
| [`PROJECT_PROFILE.md`](PROJECT_PROFILE.md) | ARRP identity, adopted scope applications, issue-page choices, and reader-facing technical vocabulary. |
| [`REPOSITORY_MAP.md`](REPOSITORY_MAP.md) | This exact ARRP installation map. |
| [`profile/`](profile/) | Additional ARRP-specific scoring, maturity, and public-actor conventions. |
| [`github/workflow.md`](github/workflow.md) | Exact GitHub lifecycle, field, and synchronization implementation. |
| [`workflows/`](workflows/) | ARRP-specific review and reconciliation procedures. |
| [`workflows/navigation-sync.md`](workflows/navigation-sync.md) | Exact ARRP navigation, area-list, topic-guide, and synchronization implementation. |
| [`publication/`](publication/) | Exact edition manifests and release decisions. |
| [`interfaces/`](interfaces/) | Project Console and visual-identity configuration. |
| [`automation/`](automation/) | Context registry, named runbooks, and exact agent/bot configuration. |

## Project records

Current state and historical evidence live under [`../records/`](../records/).
Those records do not become methodology or authority merely because runtime
tools consume them.
