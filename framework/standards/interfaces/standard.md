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
- Keep compact portals, status cells, and metric summaries on one deliberate
  desktop row whenever their content can remain legible. Prefer tighter copy,
  smaller fixed spans, or bounded horizontal overflow to an accidental second
  row. A stacked or multi-row arrangement is an intentional narrow-screen
  adaptation, not the desktop default.
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
- Navigation status conditions use fixed-size colored dots with an accessible
  text label or equivalent tooltip; they do not use variable-width status text
  that shifts neighboring controls. A number appears only when it is the exact
  actionable-queue count owned by that destination; inventory, history, role,
  or displayed-record totals do not become navigation badges. A red dot marks
  a typed current blocker represented in the destination independently from
  its count, but exact Blocked or Deferred workflow Status alone does not
  trigger it. Color is never the only accessible statement of the condition.

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

## Typed classification and projection authority

A generated interface must not originate taxonomy. View and browser code may
format, filter, sort, and select supplied typed records, but it must not infer
or assign stable identity, category or type, severity, ownership or attention,
lifecycle state, actionability, queue membership, or canonical route from
message text, titles, paths, CSS or UI labels, missing values, list position,
or ad hoc fallback logic. Presentation wording is never identity or authority.

Every cross-screen classification uses a registered stable machine ID supplied
by a named authoritative source or registered deterministic producer mapping.
An unknown or unregistered value fails closed as `classification unavailable`
and a producer contract violation. It routes to the owning Integrity surface
and must not become a new category, queue, zero count, or human action item.

One semantic classification has one registered definition and one specialist
home. Aliases are display text only and do not create another count or ledger.
Stable record identities combine typed source or check identity with a
canonical target and condition; message text and list position are prohibited
identity inputs. GitHub labels, Project fields, catalogs, operational
incidents, and gap obligations retain their separate authorities; an interface
registry maps them for display and never supersedes them.

A new or changed classification is incomplete until its registry entry defines
meaning, inclusion and exclusion predicate, canonical source, producer,
lifecycle owner, destination, resolution rule, and allowed consumers, and the
producer schema and consumer tests change under the same governed interface
Change ID. UI-only classification additions are prohibited. Generation must
validate every emitted classification and destination against the registry and
fail on unknown IDs or missing required provenance. Whole-bundle tests must
reconcile each displayed count with its exact registered destination predicate
and reject prose-keyword classification, message-derived IDs, list-order IDs,
and unregistered literals.

## Security-assurance disclosure boundary

A project-operated interface may present only minimized security-assurance
states needed to verify coverage, currentness, protected-surface review,
private-attention posture, and a protected destination. It must never ingest,
persist, render, export, or log a suspected or confirmed vulnerability,
affected path or component, rule identity, exploit condition, raw evidence,
credential metadata, exact permission detail, detector configuration, or
remediation analysis. Provider-native private security systems and owner-local
review records remain authoritative; the interface links to them without
copying their contents.

Unknown or incomplete security evidence fails closed as unavailable. A
successful check means only that the registered check completed; it is not a
claim that a system is secure or contains no vulnerabilities. Security tools
use registered stable machine identities and deny-by-default field allowlists.
Browser code may filter, sort, and render those records but may not infer a
finding, category, ownership, action, route, or clean result from prose or the
absence of private data.
