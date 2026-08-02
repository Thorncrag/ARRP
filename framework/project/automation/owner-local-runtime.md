---
title: "ARRP Owner-Local Runtime Authority"
status: active
module_id: project_runtime_authority
authority_scope: "Exact ARRP owner-local runtime locations, artifact classes, path resolution, access, retention, staging, migration, activation, cutover, rollback, and retirement boundaries."
load_when: "Reading, writing, moving, validating, projecting, migrating, activating, or retiring ARRP owner-local runtime state; resolving an owner-local path; or changing the owner Console staging boundary."
dependencies:
  - "../../AGENT_OPERATING_RULES.md"
  - "../../component-registry.json"
  - "../../standards/automation/autonomous-execution.md"
  - "../github/disclosure-boundary.md"
  - "schemas/private-staging-authority.schema.json"
print_status: excluded
print_exclusion_reason: "Internal runtime and storage authority."
---

# ARRP Owner-Local Runtime Authority

This is the single ARRP authority for owner-local runtime location, logical
path resolution, durability, staging, migration, cutover, rollback, and
retirement. Incident lifecycle, disclosure, scheduling, agent authority, and
Console presentation remain with their linked specialist authorities.

## Current authority and successor boundary

The fixed owner-only Application Support state root is the current production
runtime authority. Every unqualified `owner-local:` automation path resolves
there until a separately approved cutover changes this document, the typed
path authority, the installed bootstrap, and the host configuration as one
verified transaction.

The sibling `ARRP Private` workspace is the sole owner-local companion
workspace and inactive protected successor staging authority. It is not a Git
repository, a second project authority, the current scheduler state root, or
an implicit replacement for Application Support. Its owner-only staging
descriptor conforms to the
[`private-staging-authority` schema](schemas/private-staging-authority.schema.json)
and has five logical roles:

| Logical role | Intended authority after cutover |
| --- | --- |
| Runtime state | Runtime snapshots, controls, serialization state, bounded runs and worktrees, failure spools, current status, cadence evidence, caches, and other generated runtime state. |
| Durable records | Owner-local logs, event ledgers, review records, and retained runtime history. |
| Owner Console | Immutable owner Console versions and their exact bound private projections. |
| Security controls and evidence | Restricted security evidence, security-control material, and disclosure control packs under the applicable owner-local directive. |
| Migration evidence | Write-once inventories, comparison reports, cutover plans, activation receipts, rollback evidence, and retirement verification. |

Before cutover, the protected governance-record role may hold append-only
supplements keyed to the public `GOV` identity. This documentary exception is
not automation state, policy authority, control-pack activation, scheduler
input, or a change to production path resolution.

The `ARRP Private` workspace's `OWNER_DIRECTIVE.md` and `AGENTS.md` govern
access and handling. Nothing here changes those directives; staged artifacts
and successful tests remain review evidence until Benjamin expressly adopts
the exact change.

## Artifact classes

Each artifact has one current role. A copy, projection, or staged successor
does not become a competing authority.

| Artifact class | Current production role | Durability and projection rule |
| --- | --- | --- |
| Binary automation control and serialization | The owner-only `PAUSED` marker and operating-system-held `run.lock` live at the active state root. | `PAUSED` is an intentional control, not an incident. The lock is the sole run-liveness authority and its file is not proof of ownership without the operating-system lease. Both must remain quiescent and verified during migration. |
| Reviewed runtime snapshots | `runtime/<source-commit>/` contains the exact hash- and manifest-bound executable snapshot. | Versioned and immutable after materialization. A source checkout or nearby script is not a substitute. |
| Transaction work and output | Matching `worktrees/<run-id>/` and `runs/<run-id>/` pairs contain bounded transaction state. | A worktree is not a second repository authority. Failure preserves recoverable state and provenance; retirement follows the reviewed transaction or recoverable-removal procedure. |
| Current status and cadence | Typed status, `last-success`, local automation-status, and comparable current projections describe the latest verified state. | Replaceable, generation- or revision-bound projections. Missing, stale, malformed, or mismatched state is unavailable, never zero, healthy, or authoritative history. |
| Failure-safe spool | The independent incident spool preserves a sanitized failure signal before the ordinary chain or generated views can finish. | Reconciled deterministically into the Operational Incident authority; reconciliation never discards an unreconciled occurrence or makes the spool a second incident ledger. |
| Durable operational records | Agent and Elim logs, Operational Incident events, repository-gate declarations, Review Epoch records, and other registered histories use their governed `owner-local:records/...` paths. | Append-only or otherwise retained according to the owning contract. Public files contain only typed contracts or minimized summaries, not the complete record. |
| Security records and controls | Active disclosure controls continue to resolve from the fixed production state root. The Security Incident and incident-relation contracts are defined but remain inactive until their separately approved owner-local authority is activated. | Security evidence, Security Incident events, relations, control details, and private findings never become GitHub or public-Console artifacts. An absent or inactive authority is unavailable, not a zero count. |
| Governance change supplements | Protected decision context and evidence references use an append-only governance-record role keyed to the matching public `GOV` identity. | The public log remains the audit-facing provenance index and the changed governing file remains current-rule authority. A supplement is supporting evidence only, is never transmitted to GitHub, and may not modify or activate an adopted security policy. |
| Owner Console versions | The repository owns the one Console implementation; the owner-Console role holds immutable owner-only snapshots. | Each version binds the public generation, source revision, exact decoded file entrypoint, and every private projection's integrity digest. It is never overwritten and is not a live runtime control surface. |
| Caches and other generated runtime state | Caches, temporary projections, and regenerable status stay inside the active runtime boundary. | They cannot establish lifecycle, authority, closure, or currentness. Their eventual successor location is the protected runtime-state role; preservation or retirement must follow the applicable provenance and recoverable-removal rule. |
| Migration evidence | The migration-evidence role holds owner-only inventories and reports created for a proposed transition. | New-file, write-once evidence. It never authorizes activation and must not expose restricted entries in a public report. |

The table names logical authorities, not caller-constructed paths. Exact
resolution belongs to the owner-only descriptor and reviewed path authority;
the public schema contains roles and validation rules, not private topology.

## Path and access contract

Production repository, state, output, and control-pack roots come only from
the fixed reviewed runtime authority. An environment variable, generic CLI
argument, outbound payload path, current working directory, nearby `.git`
directory, symlink, or valid-looking candidate control pack cannot redefine
them.

The path-authority implementation must:

1. resolve the exact canonical repository and current production state root;
2. resolve successor staging through one fixed owner-only descriptor at the
   named companion root; its declared root must equal the descriptor's parent,
   and no production CLI, environment value, or caller-selected path may
   substitute another descriptor;
3. require owner-only modes and the expected owner for protected files and
   directories;
4. reject absolute child names, traversal, symlink ancestors, escapes,
   unsupported file types, mismatched run/worktree identities, and unsafe
   permissions;
5. reject a File Provider storage boundary for the named companion workspace;
6. permit fixture paths only through an explicit contained fixture authority
   that cannot overlap the repository, current state root, or named companion workspace;
7. keep candidate disclosure-control validation nonpublishing and unable to
   authorize production; and
8. return safe reason codes or descriptions to public projections without
   exposing absolute paths or restricted diagnostics.

Production publishers may choose the proposed outbound payload. They may not
choose the authority that decides whether it is safe.

## Component Registry activation readback

The tracked schema-version-4 Component Registry is reviewed configuration. A
separate schema-version-2 owner-local activation readback proves that the exact
Registry and its closed interpreter set completed the required owner review,
checks, merge, closeout, and canonical-remote readback. The verification-family
identifier remains `component_registry_stage3_authority_readback`. The readback
is evidence only: it cannot define routing, alter the Registry, authorize a
different revision, or make an operational component executable.

The logical production location is
`owner-local:records/governance/component-registry/activation-readbacks/`.
The only valid filename is `<registry-sha256>.json`, where the production
reader computes `registry-sha256` from the exact canonical registry itself.
The caller cannot supply the directory, filename, digest, registry path,
repository root, state root, readback payload, or a fallback source.
Production resolution uses only the fixed typed path authority.

Two exact version-4 validation modes keep tracked configuration separate from
live authority:

- `adopted_configuration_validation` validates the tracked active
  configuration without owner-local access. It is suitable for repository and
  CI configuration checks only and is nonauthoritative, nonexecutable, and
  unable to claim live activation.
- `live_authority_validation` is available only to a production-canonical or
  production-transaction reader after the exact digest-addressed readback has
  passed every fixed-path, file-safety, schema, approval, revision, content,
  chronology, interpreter, continuity, and ancestry check. This mode is
  authoritative verification but remains nonexecutable.

Version 4 never opens, hashes, selects, or falls back to a predecessor Registry
or routing source. Versions 1 through 3 remain rejection fixtures or historical
provenance only; they are not accepted compatibility inputs.

The readback binds exactly these five interpreter files, by SHA-256, in
addition to the full Registry SHA-256:

- `framework/component-registry.schema.json`
- `scripts/component_registry.py`
- `scripts/arrp_context.py`
- `scripts/run_coordinator.py`
- `scripts/finalize_component_registry_activation.py`

The approved implementation pull-request head anchors the Registry and all
five interpreter blobs. Their canonical bytes must remain identical to that
head at four continuity gates: after the implementation merge and before the
closeout branch is created; before the closeout pull request is merged; before
the owner-local receipt is created after that merge; and during every live
readback. Added consumers do not become receipt-bound authorities. Any byte
change to one of the five files requires a new Registry revision, full Registry
digest, approval, and receipt.

The readback has no age-only expiry. It remains valid only while its exact
Registry, five interpreter digests, approval, governance-change,
implementation, review, checks, canonical-remote, and ancestry bindings remain
valid. A missing, malformed, unsafe, stale, incompatible, incomplete, or
mismatched readback blocks before context construction. The reader never falls
back to an older readback, predecessor routing source, network lookup, summary,
or inferred success.

Only the separately approved authenticated activation finalizer may create a
production readback. It derives the evidence from the exact reviewed pull
request and canonical-remote observations, creates the digest-addressed file
once and atomically with mode `0600` beneath owner-only `0700` directories,
and never overwrites an earlier receipt. Ordinary schedulers, agents, Console
builders, repository validators, and generic command-line tools are read-only
and cannot select or update this evidence. The Console is not a readback
consumer; repository-visible projections distinguish tracked configuration
state from live activation and never expose protected readback evidence.

## Incident and record resolution

The [Operational Incident policy](operational-incidents.json), [Security
Incident policy](security-incidents.json), and [incident-relation
policy](incident-relations.json) own identity and lifecycle. This document
resolves only their owner-local record location.

- `INC` owns operational disruption, occurrences, recovery proof, and
  operational closure.
- `SEC` owns protected security investigation, containment, remediation,
  verification, and security closure.
- The relation journal owns only the existence and history of a typed
  reciprocal link.

All three records are owner-local. Public Console data shows unavailable, not
zero. An exact-bound owner Console may load only active, complete, allowlisted
projections; `SEC` and relations stay unavailable until separately activated.
Governance supplements likewise require matching schema, GOV identity, entry
digest, and Console generation, and never alter policy or activation.

## Owner Console staging

`scripts/build_owner_console.py` is a staging and verification tool, not a
runtime activator. It:

1. validates the complete public Console manifest, domain hashes, generation,
   and source revision;
2. validates each ignored owner projection against its strict schema and
   public generation/revision;
3. records each projection's SHA-256 digest in the owner binding;
4. secret-scans the normalized private output;
5. creates one new owner-only immutable version without overwriting an
   existing version; and
6. binds private loading to that version's exact canonical `file://`
   entrypoint.

Repository-source `file://`, loopback, and hosted modes are public shells and
never load private projections. The owner copy is credential-free and local.
Outside its exact binding, it says
`Data unavailable outside the bound owner-local Console.` without a false
zero or internal reason. A Governance
Change supplement contributes only its allowlisted, digest-bound summary.

## Migration and cutover

`scripts/verify_arrp_private_migration.py` inventories and validates the
inactive successor. A successful result means only that the inspected state
was suitable for review at that time. It expressly records
`activation_authorized: false`.

A production cutover requires a separate exact approval and one reconciled
plan that identifies:

1. the approved source and replacement baseline;
2. the exact scheduler, bootstrap, typed path-authority, and state-root change;
3. an intentional Paused state and proof that no process owns the production
   lock;
4. complete current and successor inventories, safe permissions, no symlink or
   File Provider boundary, and no unsupported or unresolved object;
5. the disposition of every durable record, current projection, run/worktree,
   spool, cache, control pack, owner Console version, and background-process
   reference;
6. byte- or record-level reconciliation and validation of each migrated
   authority;
7. atomic activation with immediate readback and proof that only
   one runtime authority and one scheduler remain;
8. a tested rollback baseline that does not depend on deleting the prior
   authority; and
9. a separate recoverable retirement decision after provenance, automation
   references, recovery value, and untracked material are reconciled.

No symlink alias, environment override, duplicate checkout, dual-write period,
staged manifest, owner Console build, or policy candidate may serve as an
implicit cutover. Host configuration, background-service state, pause removal,
and production execution each retain their separate immediate-approval
boundary.

## Fail-closed interpretation

When the current root, successor layout, record, projection, binding, control,
inventory, or activation state cannot be proven, report it as unavailable or
incomplete and preserve the last trustworthy identity with its time where
permitted. Never infer a zero count, healthy state, successful migration,
active authority, resolved incident, or permission to run from absence,
proximity, naming, or a valid-looking staged artifact.
