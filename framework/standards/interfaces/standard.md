---
title: "Project Interface Standard"
status: active
authority_scope: "Reusable accessibility, projection, interaction, warning, control, and canonical-authority rules for project-operated interfaces."
load_when: "Designing, changing, or reviewing a dashboard, console, form, or other application-like interface."
dependencies:
  - "../../PROJECT_STRUCTURE.md"
print_status: excluded
print_exclusion_reason: "Internal interface-governance documentation."
---

# Project Interface Standard

Project-operated interfaces are projections and controls around canonical
records. They must identify the record that owns each displayed fact, show
missing or stale inputs as gaps, and never silently infer, overwrite, or become
a competing authority.

## Presentation and accessibility

- Use a centered responsive shell, clear hierarchy, concise labels, and
  functional groupings that remain readable on narrow screens.
- Preserve strong keyboard focus, adequate contrast, semantic form labels,
  skip navigation, explicit hover and disabled states, and layouts that do not
  hide information when columns collapse.
- Sortable tables use keyboard-accessible header buttons, expose the active
  direction through `aria-sort`, show a restrained direction indicator, and
  retain a meaningful default order.
- Keep bounded management inventories complete. Paginate only when scale or
  performance materially requires it.
- Security, privacy, public-posting, disabled-service, stale-data, and error
  notices remain prominent functional warnings.

## Authority and controls

A read-only view may filter, sort, summarize, and link to canonical records. A
planning control may stage reversible local changes and export a structured
instruction list only when it:

- identifies the canonical target;
- retains nothing silently across reloads;
- does not directly mutate project records or hosted-platform state; and
- requires the ordinary authorized validation and implementation path.

A local control request is a request for the authoritative coordinator to
evaluate. It may not bypass repository, context, authority, usage, freshness,
locking, validation, or human-reserved gates and may not claim execution before
verified readback.

## Action items and records

An Action Items view contains actual human-required judgments, credentials,
unsafe external actions, owner-gated decisions, or interventions. Routine
monitoring, agent-owned work, staged drafts, and informational warnings remain
in their owning views. Every summary count links to its complete owning record;
the interface does not create a second narrative ledger.

Cached or generated presentations are rebuildable projections. Cache absence,
staleness, or inconsistency must appear as unavailable or rebuilding, never as
an empty authoritative result.
