---
title: "Component Registry Stage 2 Design"
status: adopted
print_status: excluded
print_exclusion_reason: "Adopted internal Component Registry design and provenance record."
---

# Component Registry Stage 2 Design

This is the adopted design and provenance record for the terminology and
structural model developed during Component Registry Stage 2 planning and
revised after read-only design audit. Benjamin approved this exact design for
implementation. The machine-readable Component Registry remains the authority
for adopted Registry data; this document records the approved design and does
not become a second Registry or a live-activation receipt.

## Terminology admission rule

A term enters the controlled vocabulary only when it is used as a Registry
field or controlled value, required to classify an existing component, needed
to distinguish concepts the Registry must treat differently, or required by a
governing rule whose meaning must remain stable. Ordinary project language is
not governed terminology merely because it can be defined.

## Cohesive Stage 2 proposal

Stage 2 replaces the transitional Stage 1 document-centered model with one
central inventory of whole project components. `framework/component-registry.json`
remains the sole machine-readable Component Registry authority. The redesign
does not make generated Console output, a schema, a report, or a predecessor
registry into a second authority.

The redesigned Registry contains these principal namespaces:

- `terminology`, containing only admitted controlled terms and values;
- `components`, containing one record for every registered component;
- `component_lifecycles`, containing lifecycle definitions, transitions, and
  assignments;
- `component_authorities`, containing typed authority sources and scoped
  assignments;
- `directory_scopes`, providing exhaustive structural coverage without
  treating every directory as a component;
- `relationships`, containing dependencies and other durable links between
  registered components;
- `migrations_and_aliases`, preserving identity and path transitions;
- `provenance_events`, recording normalized creation, change, migration,
  adoption, and disposition events and their affected items;
- `routing`, selecting the minimum complete governing context by stable
  component identity; and
- `supporting_artifact_rules`, assigning generated, temporary, cached, backup,
  and other noncomponent artifacts to an owner and disposition.

Each component record contains, as applicable:

- stable identity and human-readable name;
- component class and optional class-specific type;
- nonexclusive roles and capabilities;
- canonical source and source binding;
- component owner;
- information classification, disclosure rule, and disclosure boundary;
- retention bases, change mode, custody, and retirement condition;
- stable references to its lifecycle assignment, authority assignments,
  dependencies and relationships, migration records, and provenance events;
  and
- operational status for executable components only.

Each governed fact has one authoritative storage location. Lifecycle history
lives in `component_lifecycles`; authority sources and assignments live in
`component_authorities`; dependencies and other durable links live in
`relationships`; aliases and path or identity transitions live in
`migrations_and_aliases`; and change history lives in `provenance_events`.
Component records reference those records by stable ID and may expose a
generated summary, but they do not maintain a second editable copy.

Registration is selective, but repository coverage is exhaustive: every
in-scope item must be a component, a supporting artifact assigned to a
component, covered by an approved categorical rule, or an unresolved failure
requiring human review. No automated process may resolve an admission or
classification failure by invention.

The Project Console supplies nonauthoritative human-readable views of every
governed Registry dimension, including component inventory, lifecycle,
authority, relationships, retention, disclosure, source bindings, migrations,
provenance, routing, operational status, supporting-artifact coverage, and
unresolved coverage. Stage 2 adoption requires a deterministic migration from
the current Registry, complete repository classification, schema and validator
updates, Console reconciliation, and human approval of the resulting exact
Registry revision.

## Approved controlled terminology

### Namespace

A named domain within which identifiers or definitions have a specific,
governed meaning. The namespace may appear as an identifier prefix, such as
FED in FED-001, or as the name of a containing registry section or controlled
vocabulary.

### Artifact

Any identifiable item or body of material created, maintained, used,
generated, or preserved by the project. Artifacts include components as well
as fragments, intermediate outputs, temporary materials, and other items that
do not constitute whole project units.

### Component

An artifact that constitutes a whole, distinct unit representing a form,
function, product, or other identifiable element of the project.

### Registry

A governed, structured catalog of components that records their identifiers,
definitions, attributes, relationships, and status within one or more
namespaces.

A registry may reference supporting artifacts, but its registered entries are
components.

### Component class

A governed category describing what kind of whole unit a component is, based
on its fundamental form or function. The Stage 2 classes are document,
configuration, dataset, script, log, agent, bot, and interface. An inventory
item that cannot be classified coherently within this set creates a design
stop; it does not authorize an implementation-time extension.

### Configuration

A component that establishes structured values, definitions, mappings, or
operating parameters used by another component or project process.

### Dataset

A component consisting of a maintained, structured collection of related data
that is governed and used as a whole unit. A generated data file subordinate
to another component remains a supporting artifact unless it has independent
identity, maintenance, or governed treatment.

### Script

An executable source component that performs a defined computational or
automation function.

### Log

A component that preserves an ordered collection of entries documenting
states, events, transitions, observations, or work over time. A valid log may
presently contain a single entry, but the component's organizing form remains
an ordered entry collection rather than a current-state handoff or ordinary
document.

### Agent

An executable component capable of applying reasoning or adaptive judgment to
perform work within a governed scope.

### Bot

An executable component that performs a repeatable, bounded class of work
under defined configuration and authority.

### Interface

A component through which a human, machine, or both interact with project
information or functionality.

### Lifecycle model

The governed progression of lifecycle states applicable to a component.

### Lifecycle state

A standardized, named position within that progression describing a
component's current relationship to the project.

### Canonical source

The component designated as the controlling source for a defined body of
content, data, configuration, rules, or functionality.

Other components may derive from, render, copy, or use it, but they do not
replace its controlling role unless that role is formally reassigned.

### Generated output

An artifact produced by a defined process from one or more source components,
artifacts, or governed inputs. A generated output may be a partial artifact or
a whole component, and it is maintained by reproducing its generating process
rather than by independently editing the output.

### Temporary artifact

An artifact created or retained for a bounded, temporary purpose during a
process and not intended to remain a canonical or durable project unit after
that purpose is fulfilled.

An artifact is temporary because of its governed purpose and disposition—not
merely because of its name, path, or apparent age.

### Cache

An artifact or component that stores a replaceable copy, derived result, or
reusable material to improve access or execution efficiency. A cache is not
the canonical source of what it contains and may be refreshed or regenerated
from its governing source or process.

### Component relationship

A governed connection between two or more components that identifies how they
interact or relate, such as dependency, implementation, validation,
verification, consumption, or succession.

### Dependency

A component relationship in which one component requires another component
for its intended function, valid interpretation, or governed operation.
Without the required component, the dependent component cannot be treated as
complete or operating as intended.

### Producer

The person, process, tool, or component responsible for creating or updating
an artifact or component through a defined method.

A producer identifies how an item comes into being or is maintained; it does
not by itself determine the item's authority or ownership.

### Component owner

The person or governed role accountable for a component's stewardship,
including its maintenance, review, and lifecycle disposition.

Ownership does not necessarily mean that the owner created the component,
produces its outputs, or may change it without required approval.

### Authority model

A governed assignment of control over decisions, rules, content, state, or
actions within a defined scope, including who or what may establish, approve,
or change them.

Authority is scope-specific. Ownership, production, possession, or technical
ability does not by itself create authority.

### Validation

A governed process for determining whether an artifact or component satisfies
defined requirements using specified evidence or methods.

A successful validation establishes conformity with those requirements; it
does not by itself confer approval, authority, adoption, or activation.

### Validator

The person, process, tool, or component responsible for checking whether an
artifact or component conforms to defined requirements using specified
evidence or methods.

A validator applies the requirements; it does not define, waive, or change
them unless separately assigned that authority.

### Approval

A recorded decision by an authorized person or process accepting an artifact,
component, change, or action for a defined purpose or stage.

Approval is limited to its stated scope. It does not imply activation,
publication, execution, or broader authority unless those outcomes are
expressly included.

### Adoption

A logged, authorized act that incorporates an artifact, component, definition,
rule, or change into the project's current governed state.

Adoption makes the adopted item part of the project's governing structure, but
it does not necessarily activate execution or authorize publication unless
separately stated.

### Activation

A logged, authorized act that places a component into governed operational use
for a defined scope.

### Active (operational status)

Authorized and enabled to execute within a defined operational scope. An
active executable component may currently be idle.

### Paused (operational status)

Temporarily prevented from executing while retained for possible resumption.

### Inactive (operational status)

Not enabled to execute within the applicable operational scope.

### Current (applicability status)

Designated as the presently governing or applicable version of a component. A
component can be active without being current.

### Draft (lifecycle state)

Under development and not yet submitted for possible adoption.

### Proposed (lifecycle state)

Submitted for possible adoption but not yet incorporated into the project’s
governed state.

### Adopted (lifecycle state)

Incorporated into the project's governed state through an authorized adoption.

### Retired (lifecycle state)

No longer designated for current use in its former role. Retirement does not
determine whether the component is retained or archived.

### Archived (retention outcome)

Retained for historical, evidentiary, or provenance purposes rather than
current operational use.

### Supersession (relationship)

The governed replacement of one component by another in a defined role,
function, or authority.

### Predecessor (relationship role)

The earlier component in a succession relationship.

### Successor (relationship role)

The component that follows or replaces a predecessor in a defined role,
function, or authority.

### Alias (identifier relationship)

An alternate identifier or locator that refers to the same component without
creating a separate component.

### Identifier

A name or code that distinguishes an artifact or component within a namespace.

### Stable identifier

An identifier intended to remain unchanged when a component’s name, location,
revision, or status changes.

### Locator

A value indicating where an artifact or component can be found or accessed. A
locator may change without changing the component’s identity.

### Revision

A particular changed state in the continuing history of the same artifact or
component.

### Version

A formally designated edition of an artifact or component, which may encompass
one or more revisions.

### Attribute

A governed property recorded about an artifact or component, such as its class,
owner, status, or disclosure posture.

### Classification

The governed assignment of an artifact or component to one or more defined
categories based on specified characteristics.

### Disposition

A governed determination of how an artifact or component will be retained,
transferred, superseded, archived, or otherwise handled.

### Migration

A governed change in a component’s location, structure, identifier, or
technical form that preserves defined continuity with its prior state.

### Redirect

A mechanism that directs use of an earlier identifier or locator to a
designated current identifier or locator.

### Provenance

The documented origin and complete governed history of an artifact or
component, including every logged change to its identity, content, location,
form, status, relationships, authority, ownership, or disposition. This
includes revision, derivation, migration, adoption, activation, supersession,
retirement, and archival.

### Derivation

A relationship in which an artifact or component is produced from one or more
sources through copying, extraction, transformation, calculation, generation,
or synthesis.

Synthesis is a specific type of derivation: synthesis combines multiple
sources into a new coherent whole, whereas other derivations may be copies,
extracts, renders, hashes, conversions, or generated reports.

### Source

An artifact, component, or governed input from which material is obtained,
produced, or evaluated. A source is not necessarily the canonical source.

### Source binding

A recorded connection between an artifact or component and the exact source
content or revision upon which it depends.

### Evidence

Information or material used to support a determination, decision, validation,
or verification.

### Receipt

A logged artifact documenting that a defined action or transaction occurred
and recording the evidence needed to verify it.

### Governing

Assigned to establish or control requirements, meaning, behavior, or decisions
within a defined scope.

### Authoritative

Possessing governed control over a defined decision, rule, content, state, or
action within a specified scope.

### Nonauthoritative

Informational or supporting in purpose and not permitted to establish or
control the matter it describes.

### Verification

A process for confirming a specific claim, fact, identity, or result through
direct comparison with defined evidence. Unlike validation, verification
confirms what is true or occurred; validation determines whether requirements
are satisfied.

### Document

A whole artifact organized to communicate, preserve, or govern information in
a readable form.

### Specification

A document that defines the required characteristics, structure, behavior, or
interfaces of a particular component, product, system, or output, including
the requirements by which conformity can be validated by human or automated
processes.

### Governing document

A document assigned authority to establish requirements, definitions,
decisions, or procedures within a defined scope.

### Schema

A component that formally defines the permitted structure, fields, values, and
constraints of a class of structured artifacts.

### Implementation

A component that technically realizes a defined function, process, interface,
rule, or specification.

### Test suite

A script type containing a maintained collection of executable checks used to
verify or validate defined behavior or requirements. A test suite defines the
checks; an individual execution result, report, or log is a separate artifact.

### Consumer

A person, process, tool, or component that uses an artifact, component,
service, or output for a defined purpose.

### Consumption

A relationship in which one component uses another component or its output
without assuming ownership or authority over it.

These dimensions are not mutually exclusive. A component may concurrently be
retired, archived, a predecessor, and superseded by another component; its
successor may concurrently be current and, when executable, active.

## Approved structural design

### Proposal scope and planned canonical location

Stage 2 adoption creates the directory scope `framework_proposals` with these
properties:

- display name: `Public-safe project proposals`;
- path pattern: `framework/proposals/`;
- match kind: `prefix`;
- specificity rank: `20`;
- ancestors: `repository_root`, `framework`;
- disclosure boundary: `public_safe_only`;
- lifecycle posture: `current`;
- fallback: `human_review`; and
- purpose: public-safe project designs, plans, governance changes, and
  implementation proposals that are not themselves adopted governing
  authorities or implementations.

The scope excludes substantive ARRP public-policy proposals, research, working
notes, completed reports, adopted standards or configurations, current status
or handoff material, temporary drafts, and restricted owner-local proposals.

As part of the coordinated Stage 2 implementation transaction, this design is
registered at `framework/proposals/component-registry-stage2-design.md` as
`component_registry_stage2_design_proposal`, class `document`, type
`specification`, role `proposal`, lifecycle `adopted`. Its real creation,
approval, audit, and migration history remain in provenance. The former
research path is migration provenance only, not a second current component or
redirect.

### Registration and repository coverage

Component registration is selective, but repository coverage is exhaustive.
Every in-scope repository item must satisfy exactly one applicable treatment:

1. it has a component entry;
2. it is a supporting artifact assigned beneath a component;
3. it is covered by an approved generated, temporary, cache, backup, or
   directory rule; or
4. validation fails and requires human review.

Every persistent, non-supporting file receives a component entry. Maintained
project-structure directories ordinarily receive directory entries. A
directory entry is a structure and coverage record, not a component merely
because the directory exists. Minute dynamic subdirectories may be omitted
only where a registered parent scope expressly permits them.

A supporting artifact is a maintained or generated file, directory, fragment,
or output that is subordinate to a registered component or categorical rule
and does not require an independently governed identity. Whether it is
maintained or generated is recorded separately from its supporting status.
Supporting artifacts remain assigned to an owning component or approved rule
rather than becoming component entries automatically. An artifact that has
independent controlled content, lifecycle, authority, ownership, or
disposition is a component rather than a supporting artifact.

An item may enter the Registry through owner designation, approved baseline
adoption, or creation under an authorized rule. The Registry must never infer
registration, assignment, relocation, deletion, or authority merely from a
path or apparent purpose. Any unresolved coverage or admission failure is
preserved and sent for human review.

### Unified component inventory

The redesigned Registry uses one `components` collection for component
records. The current `operational_documents` collection is absorbed into it
while preserving identity continuity. The specifically proposed identity
renames use exact migration aliases and provenance rather than silently
creating replacement components. Other Registry records—such as directory
scopes, relationships, authority assignments, migrations, routing, and
supporting-artifact rules—remain structured Registry records but are not
therefore components.

Every component has one Registry record. Supporting artifacts are recorded
beneath their owning component or applicable rule and do not receive separate
component records unless they themselves constitute whole project units.

Each `components.<stable_id>` record uses this field ownership:

- `stable_id` and `display_name` identify the component;
- `classification` contains `component_class`, optional `component_type`,
  `roles`, `capabilities`, and class-specific `attributes`;
- `canonical_source` contains the canonical locator and its source-binding
  record;
- `owner` identifies the component owner;
- `information_handling` contains information classification, disclosure rule,
  and disclosure boundary;
- `retention` contains bases, change mode, custody, review condition, and
  retirement condition;
- `supporting_artifacts` contains exact maintained or generated subordinate
  paths assigned specifically to this component;
- `operational_status` is present only when `capabilities` contains
  `executable`; and
- `record_refs` contains arrays of stable IDs for lifecycle assignment,
  authority assignments, relationships, migrations, and provenance events.

The schema forbids lifecycle history, authority-source payloads, relationship
objects, migration details, or full provenance events inside a component
record. Those objects live only in their named top-level structures.
`supporting_artifact_rules` covers only categorical producer or directory
classes; an exact artifact appears either under one component or under one
categorical rule, never both.

The separate ARRP Agent and Bot Registry is consolidated into the central
Component Registry. Each governed agent and bot becomes a direct component
entry with its own stable identity, class, lifecycle, authority, operational
status, configuration, and relationships. Its runbook remains a configuration
component linked to that executable component. After verified migration, the
former Agent and Bot Registry is retained only as a retired, archived
predecessor and may not remain a second current registry.

The Stage 2 component classes are exactly `document`, `configuration`,
`dataset`, `script`, `log`, `agent`, `bot`, and `interface`. Complete inventory
classification must stop if an independently governed component cannot be
placed in one of those classes without distorting its primary form or function;
the implementation may not invent another class. Classification uses four
separate dimensions so one primary type is not forced to carry every fact:

1. `component_class` identifies the fundamental kind of whole unit;
2. `component_type` identifies a meaningful subtype within that class;
3. `roles` records additional nonexclusive functions; and
4. class-specific attributes and capabilities record distinctions such as
   audience, operating
   boundary, subject, and capabilities.

Stage 2 does not create a component-family namespace. System or project-purpose
groupings are expressed through relationships, routing, ownership, or Console
filters until an actual governed distinction requires another dimension.

The initial controlled roles are `proposal`, `handoff`,
`workflow_entrypoint`, and `routing_entrypoint`. The initial controlled
capabilities are `executable`, `monitor`, `validator`, `coordinator`,
`operator`, and `generator`. A component may have multiple roles or
capabilities. The implementation may not add a value merely to accommodate an
unclear classification; it must stop for design review.

A controlled type is retained when it describes a coherent recurring function
or a materially distinct governed treatment. A low current count triggers a
wider inventory check rather than automatic retention or removal. A neighboring
type may be broadened when it can absorb the component without obscuring a
distinction the Registry must enforce.

Documents use one primary type from `policy`, `standard`, `workflow`,
`specification`, `framework`, `report`, `template`, and `guide`. `Proposal` is
a nonexclusive document role rather than a primary type.

Configurations use a type only where the distinction is material:
`registry`, `schema`, `runbook`, `controlled_vocabulary`, `manifest`, `model`,
or `bootstrap`. A configuration outside those categories needs no redundant
`settings` type. Its scope and relationships identify what it configures.

Datasets have no Stage 2 subtype. Existing maintained source, candidate, issue,
and research data collections are `dataset` components when they have
independent identity or governed maintenance. Generated Console feeds and
similar subordinate data remain supporting artifacts of their producer
component.

Scripts use one primary type from `validator`, `generator`, `operator`,
`coordinator`, and `test_suite`.

Logs use a subject type from `governance_change`, `audit`,
`candidate_discovery`, `source_monitoring`, `automation`,
`operational_incident`, and `security_incident`. A log preserves a logged
ordered collection of entries; it may presently contain one entry or many.
Entry count alone does not determine whether the component is a log, but a
current-state handoff without an ordered entry structure is not a log.

Agents use `internal` or `external` as their operating-boundary type. Bots use
one primary work type from `monitor`, `validator`, `coordinator`, `operator`,
and `generator`, with additional work expressed as capabilities. Interfaces
use `human`, `machine`, or `hybrid` according to their intended consumers.

The Codex bootstrap is `configuration / bootstrap` with the nonexclusive roles
`workflow_entrypoint` and `routing_entrypoint`. Its workflow participation does
not require classifying the complete component as a workflow document.

The proposed functionally descriptive stable-identity migrations are:

- `public_premise` to `project_premise`;
- `current_audit` to `task_handoff`;
- `project_profile` to `project_configuration`;
- `maturity_profile` to `proposal_development_model`; and
- `scoring_quality_rubric` to `proposal_scoring_model`.

The two models are `configuration / model`; `project_configuration` needs no
subtype; and `task_handoff` is `document` with the nonexclusive role
`handoff`. A handoff records current continuity state; it is not classified as
a log unless it is an ordered collection of entries. The Stage 2 migration must
update each component entry and every current relationship, routing reference,
dependency, and consumer. Each former identity remains only as a migration
alias and historical provenance, not as a second component.

Before migration, every occurrence of a former stable ID is classified as a
current operational reference or typed historical provenance. The migration
rewrites every current occurrence, preserves only the explicitly typed
historical occurrences, and then runs a residual scan that rejects an old ID
anywhere outside its validated alias or provenance location. Count-only or
whole-file exceptions are insufficient.

The current `artifact_classes`, `artifact_families`, and
`artifact_lifecycles` namespace names are replaced by component-centered
classification and `component_lifecycles`. Artifact rules remain available
for supporting artifacts that are not components.

### Component lifecycle

`component_lifecycles` lives inside `component-registry.json`. Its lifecycle
states are:

- `draft`
- `proposed`
- `adopted`
- `retired`

Its permitted transitions are:

- draft to proposed
- draft to retired
- proposed to draft
- proposed to adopted
- proposed to retired
- adopted to retired
- retired to draft

Rejected, withdrawn, abandoned, obsolete, consolidated, and superseded are
reasons, dispositions, or relationships rather than lifecycle states.
Lifecycle assignments are keyed by stable component ID and retain effective
dates and complete transition provenance.

### Authority

Authority is modeled in a top-level `component_authorities` structure rather
than an `authority_role` label. The authority chain may include:

1. Benjamin's owner authorization;
2. an approved design, plan, or proposal component;
3. an exact design-contract revision;
4. a delegated authority; and
5. the resulting authorized implementation or change.

Effective authority is the intersection of every applicable source and
constraint. A lower layer may narrow but may not enlarge the authority granted
by its sources.

`component_authorities` records typed authority sources, assignments keyed by
component ID, subjects, effects, exclusions, effective dates, termination
conditions, governing precedence, and provenance. The Registry records and
validates authority; it does not create authority. A design contract is bound
by exact ID and revision, while its full payload remains in its governed
storage location.

The current `authority_role` field is removed. Its former values are assigned
to their actual dimensions: authority, component class, lifecycle, evidence,
relationship, or retention.

### Retention

The overloaded `retention_posture` field is replaced by structured retention.
A component or artifact may have multiple concurrent retention bases:

- `operational_need`
- `historical_provenance`
- `evidentiary_requirement`
- `recovery_protection`
- `regeneration_support`

Its change mode is one of `maintained`, `append_only`, `immutable`, or
`replaceable`. Custody is `repository`, `owner_local`, or `external`.
Retention also records its review condition and retirement condition.

Security-related material uses the ordinary retention basis that explains why
it is retained; security sensitivity does not create a separate retention
basis. An individual backup is ordinarily a supporting artifact retained for
`recovery_protection`; a governed backup system or package may itself be a
component.

`current` remains applicability, and `archived` remains the retention outcome
of a retired item kept for history, evidence, or provenance. External digest
handling belongs to source binding rather than retention.

### Executable operational status

Operational status applies only to components explicitly assigned the
`executable` capability. It is therefore not inferred from a class name and
does not require creating speculative service or tool classes. Its values are
`active`, `paused`, and `inactive`. Components without the executable
capability omit operational status. Literal running or not-running condition
is runtime observation rather than Registry status.

### Temporary artifacts and directories

Temporary run files and directories are categorically exempt from individual
component registration when they remain within an approved temporary scope and
retain a bounded current-run purpose. The `.tmp` directory receives a
directory-scope entry whose child policy permits those dynamic supporting
artifacts. Minute temporary children do not receive individual entries.

The exemption ends when an item is retained as evidence, maintained output,
or another durable project artifact. Owner-local guarded temporary storage
remains a separate scope. Uncertainty fails closed and requires preservation
and human review.

### Information classification and disclosure

Disclosure uses three distinct concepts:

- `information_classification` describes the sensitivity of the information;
- `disclosure_rule` describes what may be disclosed and under what
  conditions; and
- `disclosure_boundary` identifies where disclosure controls are enforced.

A location never changes an artifact's information classification. When a
sensitive source permits only nonsensitive disclosure, a distinct public-safe
artifact is derived from it, retains safe provenance, and is validated before
crossing the public boundary. The source remains restricted. Any uncertain or
incompatible combination fails validation and requires human review.

### Source binding and content verification

The current `digest_policy` field is removed, but its useful facts are retained
as separate source-binding dimensions rather than compressed into one mixed
enumeration. A source binding records:

- `binding_basis`: the exact identity being bound, such as a content digest,
  repository revision, governed external identifier, or runtime observation;
- `applicability`: whether the binding establishes current or historical
  content;
- `verification_methods`: one or more methods such as pinned comparison,
  runtime verification, or external-authority verification;
- `verifying_authority`, when an external authority participates;
- `verified_at`, when time is material; and
- `evidence_ref`, identifying the evidence used for verification.

The schema requires the fields applicable to each method and rejects
incompatible or unexplained combinations. A binding may legitimately be both
historical and externally verified, or both digest-pinned and runtime-checked.
Historical content never claims currentness. A mismatch, missing required
authority, or absent evidence requires human review.

### Routing and Codex usage

The primary purpose of Registry routing is to reduce Codex context usage while
still loading the complete governing set for an operation.

The current `context_routing` structure becomes a compact `routing` namespace.
It retains operation or route selection, applicable conditions, stable
component IDs, and exclusions. It does not duplicate component paths, hashes,
or dependency definitions. Those facts live once in `components`.

The routing tool resolves selected component IDs, adds their dependency
closure, and returns only the exact file paths Codex must read. Validation
confirms that routed IDs exist, are current, and have complete dependency
closure. Human-readable Console routing is generated from the same data and is
nonauthoritative.

### Relationships, migration, and provenance

The general component relationship graph contains durable relationships
between governed identities. The presently proposed types are:

- `implemented_by`
- `validated_by`
- `verified_by`
- `consumes`
- `supersedes`

`consumes` is used only when its endpoints are registered components or
governed external sources. Migration details and redirects belong to migration
and alias records. Derivation belongs to source binding and derivation
provenance. Creation under an approved proposal belongs to change provenance,
not the general relationship graph.

`provenance_events` stores each creation, material change, migration, adoption,
retirement, or disposition event once. An event records its originating
proposal or plan when applicable, authorization source, exact design-contract
revision, change identity, introduced revision, and affected component,
directory, or durable supporting-artifact IDs. Affected records reference the
event by stable ID rather than repeating the full chain. This supports lookup
from an item to its originating changes and from a change to every affected
item without multiplying authority or provenance payloads. Rollback remains
human-reviewed rather than automatic.

### Human-readable Console interfaces

The Project Console provides nonauthoritative human-readable interfaces
generated from the validated Registry. It does not infer missing assignments,
create authority, or become a second source of Registry data.

Operations > Component Registry > Lifecycles includes:

- one portal for each lifecycle-state count;
- the permitted transition flow;
- lifecycle-state definitions;
- searchable component assignments; and
- each component's lifecycle history and effective dates.

Operations > Component Registry > Authority includes:

- authority sources and assignments;
- subjects, effects, and exclusions;
- effective and termination conditions;
- exact design-contract bindings; and
- the authority chain applicable to each component.

The Console never exposes private authorization or design-contract payloads;
it displays only the public-safe identities, scopes, and bindings supplied by
the Registry. The routing interface likewise renders the compact validated
routing data without becoming a routing authority.

Every other governed dimension remains inspectable without requiring a
separate screen for each one. The component detail interface includes:

- dependencies and durable relationships, with direction and related stable
  IDs;
- retention bases, change mode, custody, review condition, and retirement
  condition;
- information classification, disclosure rule, and disclosure boundary;
- canonical source and source-binding evidence;
- migrations, aliases, and identity history;
- normalized provenance events and originating changes;
- operational status for executable components; and
- supporting artifacts and directory or categorical coverage rules.

Cross-component relationship and unresolved-coverage views provide searchable
navigation where a single component detail would be insufficient. The Console
renders only validated Registry data and public-safe evidence references; it
does not reproduce private payloads or maintain independent interpretations.

### Registry revision and adoption validation

Removing a permanent Registry-level `candidate` field does not remove the
machine-verifiable distinction between proposed content, adopted
configuration, and live authority. The validator exposes three closed modes:

1. `proposed_revision_validation` validates unadopted Registry bytes against
   the schema and an exact design-contract and repository-base binding. It
   makes no adoption or authority claim.
2. `adopted_configuration_validation` requires the exact Registry bytes and
   revision recorded by the completed adoption transaction on canonical Git
   history. It validates the adopted tracked configuration but does not claim
   that owner-local operational activation has been verified.
3. `live_authority_validation` additionally requires the fixed external
   activation or adoption readback that binds the exact adopted Registry
   digest and canonical revision. Only this mode may report live authority.

The validation mode and its evidence envelope are supplied by the fixed
validator entrypoint and governed storage, not authored inside the Registry
being validated and not inferred merely from a dirty or clean worktree.
Unknown, contradictory, self-referential, or incomplete posture fails closed.

### Removed transitional and overlapping structures

The following current structures or fields are removed from the redesigned
Registry rather than admitted as permanent controlled terminology:

- `representations`; its contents move to canonical-source fields, generated
  supporting artifacts, Console configuration, directory rules, or
  aliases/migrations as applicable;
- repeated `review_policy`; human review remains the fail-closed default for
  autonomous changes unless an explicit scoped autonomous-change authority
  permits otherwise;
- `repository_ref_lifecycle`; Git-reference handling remains in Git workflow
  and implementation artifact-disposition rules;
- `reference_policy`; canonical-path validation and provenance already govern
  current and historical references;
- `activation_state`; the fixed validation evidence envelope distinguishes
  proposed content, adopted configuration, and live authority, while
  component lifecycle and executable status remain separate facts;
- namespace-level `complete` and `enforced`; adopted namespaces validate and
  enforce by definition, while finite audit and receipt results may still
  report their own completeness;
- permanent `source_baseline`; the originating revision belongs in adoption
  provenance; and
- Registry-level `candidate`; unadopted work remains in its plan, design
  contract, or Git change until adoption and is validated only through
  `proposed_revision_validation`.

The rejected umbrella concepts `representation`, `projection`, `association`,
and `aggregation` are not reintroduced merely because the current Stage 1
schema uses related labels.

## Adopted post-audit design

The frozen proposal at SHA-256
`0866b19bbb1116855f677b7155de007467fbe80b246a4ee24c570897a8c32e13`
received the required read-only design audit. This post-audit revision records
the following design decisions approved by Benjamin:

1. Use exactly eight component classes: `document`, `configuration`,
   `dataset`, `script`, `log`, `agent`, `bot`, and `interface`.
2. Omit component families from Stage 2. Use the exact controlled roles and
   capabilities defined above; do not create undeclared implementation-time
   values.
3. Classify a maintained or generated item as a supporting artifact only when
   it is subordinate to one component or categorical rule and has no
   independent governed identity, lifecycle, authority, owner, or disposition.
4. Rename `current_audit` to `task_handoff` and classify it as `document` with
   role `handoff`. Define logs as ordered entry collections.
5. Store lifecycle, authority, relationships, migrations, and provenance in
   their respective top-level structures exactly once. Component records carry
   stable references, not editable duplicates.
6. Replace the mixed `digest_policy` values with the exact source-binding
   dimensions defined above.
7. Remove permanent Registry-level candidate and activation fields, but retain
   the exact three external validation modes for proposed revisions, adopted
   configuration, and receipt-verified live authority.
8. Store change and authority provenance as normalized events and sources;
   affected items reference their stable IDs.
9. Make every governed Registry dimension inspectable through the Console,
   using component details plus cross-component relationship and unresolved
   coverage views rather than a separate screen for every field.
10. Treat the 94-entry table as the exact migration seed, not the complete
    inventory. The implementation must classify every remaining persistent
    path as a component, supporting artifact, directory or categorical rule,
    or preserved human-review failure before Stage 2 adoption.

These decisions are implemented only through the separately approved
schema-version-2 implementation contract, bounded migration, validation,
artifact disposition, and exact adoption readback. Approval of this design
does not by itself claim that the tracked Registry revision is live.

## Implementation boundary

Implement the accepted design through its bound Stage 2 implementation
contract. Complete inventory classification is part of that migration and
must stop on any item the accepted design cannot classify. Add another
controlled term only through a later design revision approved before
implementation.

## Provisional current-entry classification review

This review table maps every entry in the current `operational_documents`
inventory to the proposed Stage 2 classification. It is a review aid, not an
adopted Registry change. “Current label” records the existing
`document_class.value`; the proposed class and type apply the post-audit
taxonomy.

| Stable ID | Current label | Proposed class | Proposed type | Note |
|---|---|---|---|---|
| `public_premise` | `routed_governing_document` | `document` | `policy` | Rename stable ID to `project_premise` |
| `codex_bootstrap` | `routed_governing_document` | `configuration` | `bootstrap` | Roles: `workflow_entrypoint`, `routing_entrypoint` |
| `framework_kernel` | `routed_governing_document` | `document` | `framework` | — |
| `agent_rules_kernel` | `routed_governing_document` | `document` | `policy` | — |
| `github_disclosure_boundary` | `routed_governing_document` | `document` | `policy` | — |
| `github_disclosure_policy` | `routed_governing_document` | `document` | `policy` | — |
| `current_audit` | `routed_operational_document` | `document` | — | Rename stable ID to `task_handoff`; role `handoff` |
| `context_routing` | `routed_governing_document` | `document` | `specification` | Retired archived predecessor |
| `project_structure` | `routed_governing_document` | `document` | `specification` | Retired archived predecessor |
| `github_workflow` | `routed_governing_document` | `document` | `workflow` | — |
| `remedy_framework` | `routed_governing_document` | `document` | `standard` | — |
| `print_assembly` | `routed_governing_document` | `document` | `specification` | — |
| `public_release` | `routed_governing_document` | `document` | `workflow` | — |
| `project_console_progress` | `routed_governing_document` | `document` | `specification` | — |
| `project_console_classifications` | `routed_governing_document` | `configuration` | `controlled_vocabulary` | — |
| `project_tool_interface` | `routed_governing_document` | `document` | `specification` | — |
| `intake_process` | `routed_governing_document` | `document` | `workflow` | — |
| `agent_audit_execution` | `routed_governing_document` | `document` | `standard` | — |
| `agent_autonomous_execution` | `routed_governing_document` | `document` | `standard` | — |
| `private_staging_authority_schema` | `routed_governing_document` | `configuration` | `schema` | — |
| `project_runtime_authority` | `routed_governing_document` | `document` | `policy` | — |
| `transaction_lifecycle` | `routed_governing_document` | `document` | `policy` | — |
| `transaction_lifecycle_schema` | `routed_governing_document` | `configuration` | `schema` | — |
| `transaction_recovery_package_schema` | `routed_governing_document` | `configuration` | `schema` | — |
| `project_reconciliation` | `routed_governing_document` | `document` | `policy` | — |
| `project_reconciliation_schema` | `routed_governing_document` | `configuration` | `schema` | — |
| `project_autonomous_execution` | `routed_governing_document` | `document` | `policy` | — |
| `repository_gate_policy` | `routed_governing_document` | `document` | `policy` | — |
| `operational_incident_policy` | `routed_governing_document` | `document` | `policy` | — |
| `security_incident_policy` | `routed_governing_document` | `document` | `policy` | — |
| `incident_relation_policy` | `routed_governing_document` | `document` | `policy` | — |
| `agent_context_research` | `routed_governing_document` | `document` | `standard` | — |
| `agent_handoff` | `routed_governing_document` | `document` | `standard` | — |
| `agent_issue_candidate_work` | `routed_governing_document` | `document` | `policy` | — |
| `agent_multi_agent` | `routed_governing_document` | `document` | `standard` | — |
| `agent_provenance_logging` | `routed_governing_document` | `document` | `standard` | — |
| `agent_validation_closeout` | `routed_governing_document` | `document` | `standard` | — |
| `agent_registry` | `routed_governing_document` | `configuration` | `registry` | Retire and archive after agent/bot migration |
| `runbook_elim` | `routed_governing_document` | `configuration` | `runbook` | — |
| `runbook_case_monitor_bot` | `routed_governing_document` | `configuration` | `runbook` | — |
| `runbook_presidential_directives_bot` | `routed_governing_document` | `configuration` | `runbook` | — |
| `runbook_console_progress_bot` | `routed_governing_document` | `configuration` | `runbook` | — |
| `runbook_integrity_bot` | `routed_governing_document` | `configuration` | `runbook` | — |
| `runbook_run_coordinator_bot` | `routed_governing_document` | `configuration` | `runbook` | — |
| `runbook_source_checker_bot` | `routed_governing_document` | `configuration` | `runbook` | — |
| `audit_core` | `routed_governing_document` | `document` | `standard` | — |
| `audit_verification` | `routed_governing_document` | `document` | `standard` | — |
| `audit_tiered` | `routed_governing_document` | `document` | `standard` | — |
| `audit_legal_prior_proposal` | `routed_governing_document` | `document` | `standard` | — |
| `audit_project_consistency` | `routed_governing_document` | `document` | `standard` | — |
| `scoring_quality_rubric` | `routed_governing_document` | `configuration` | `model` | Rename stable ID to `proposal_scoring_model` |
| `audit_change` | `routed_governing_document` | `document` | `standard` | — |
| `scoring_adoption_pathway` | `routed_governing_document` | `document` | `standard` | — |
| `scoring_external_international` | `routed_governing_document` | `document` | `standard` | — |
| `method_neutrality_language` | `routed_governing_document` | `document` | `standard` | — |
| `method_scope_admission` | `routed_governing_document` | `document` | `standard` | — |
| `method_partisan_perception` | `routed_governing_document` | `document` | `policy` | — |
| `evidence_standards` | `routed_governing_document` | `document` | `standard` | — |
| `source_catalogs` | `routed_governing_document` | `document` | `standard` | — |
| `issue_architecture` | `routed_governing_document` | `document` | `standard` | — |
| `development_levels` | `routed_governing_document` | `document` | `standard` | — |
| `navigation_inventory` | `routed_governing_document` | `document` | `standard` | — |
| `navigation_topic_guides` | `routed_governing_document` | `document` | `standard` | — |
| `candidate_adjudication` | `routed_governing_document` | `document` | `workflow` | — |
| `source_automated_adjudication` | `routed_governing_document` | `document` | `standard` | — |
| `source_presidential_directives` | `routed_governing_document` | `document` | `workflow` | — |
| `source_project_monitoring` | `routed_governing_document` | `document` | `standard` | — |
| `operation_project_update` | `routed_governing_document` | `document` | `workflow` | — |
| `operation_governance_change_recording` | `routed_governing_document` | `document` | `workflow` | — |
| `governance_change_registry` | `routed_governing_document` | `configuration` | `registry` | Register the separate readable governance-change log as `log / governance_change` |
| `project_profile` | `routed_governing_document` | `configuration` | — | Rename stable ID to `project_configuration` |
| `repository_map` | `routed_governing_document` | `configuration` | `registry` | Retired archived predecessor |
| `maturity_profile` | `routed_governing_document` | `configuration` | `model` | Rename stable ID to `proposal_development_model` |
| `scoring_standard` | `routed_governing_document` | `document` | `standard` | — |
| `candidate_review_standard` | `routed_governing_document` | `document` | `standard` | — |
| `print_assembly_standard` | `routed_governing_document` | `document` | `standard` | — |
| `release_standard` | `routed_governing_document` | `document` | `standard` | — |
| `interface_standard` | `routed_governing_document` | `document` | `standard` | — |
| `progress_view_standard` | `routed_governing_document` | `document` | `standard` | — |
| `public_input_standard` | `routed_governing_document` | `document` | `standard` | — |
| `work_tracking_standard` | `routed_governing_document` | `document` | `standard` | — |
| `visual_identity` | `routed_governing_document` | `document` | `standard` | — |
| `print_manifest` | `routed_governing_document` | `configuration` | `manifest` | — |
| `progress_config` | `routed_governing_document` | `configuration` | — | Configures the Progress interface |
| `elim_result_schema` | `routed_governing_document` | `configuration` | `schema` | — |
| `project_source_adjudication` | `routed_governing_document` | `document` | `workflow` | — |
| `navigation_project_sync` | `routed_governing_document` | `document` | `workflow` | — |
| `project_audit_execution` | `routed_governing_document` | `document` | `workflow` | — |
| `COMPONENT-REGISTRY` | `component_registry` | `configuration` | `registry` | — |
| `component_registry_schema` | `schema` | `configuration` | `schema` | — |
| `component_registry_tool` | `maintained_implementation` | `script` | `validator` | — |
| `component_registry_activation_finalizer` | `maintained_implementation` | `script` | `operator` | — |
| `component_registry_tests` | `test_source` | `script` | `test_suite` | — |
| `context_routes_source` | `archived_route_data_authority` | `configuration` | — | Retired archived predecessor; routing purpose is historical provenance |
