---
title: "ARRP Console Development Log"
status: active
print_status: excluded
print_exclusion_reason: "Internal interface-development history."
---

# ARRP Console Development Log

This append-only record indexes material changes to the Project Console as a
product. Git remains the exact diff authority; this log explains introductions,
changes, moves, renames, retirements, restorations, and reversions across
commits. Routine data refreshes and ordinary operational state changes do not
belong here.

Every material Console change receives a stable `CONSOLE-YYYY-NNN` identity.
Semantic implementation commits use the trailer
`Console-Change-ID: CONSOLE-YYYY-NNN`. A change that has not yet been committed
or accepted on canonical `main` is explicitly labeled `Proposed / unmerged`.
Full 40-character Git identities are retained; the interface may abbreviate
them for display.

Each date uses one canonical umbrella divided into the registered broad-category
subheadings in the Console classification authority. The Console renders each
materially changed category as a separate selectable entry while retaining the
date and shared provenance from that umbrella. Rapid-fire revisions are
consolidated only when they belong to the same coherent category and change set.
Independent architectural, security, operational, data-contract, or user-facing
work remains separately traceable. Do not create one entry per commit, and do
not collapse the entire day into one oversized interface entry.

**Record requirements.**

Each date has one ISO-date `##` umbrella heading followed by the fixed metadata
list, including every applicable Console Change ID and the umbrella title. Its
`###` sections use only registered Console Development Log categories and
include Category ID, Change ID, applicable commit IDs, material change, and
validation. Only categories changed that day appear. Each category section
projects as one Console entry; the umbrella is not itself an additional entry.
A retirement names its replacement or states that no replacement exists. A
restoration or reversion identifies its related change IDs. GitHub-bound entries
contain no vulnerability evidence or restricted operational detail. History is
never rewritten.

Historical reconstruction before `CONSOLE-2026-001` is permitted only from
verified diffs and records. Reconstructed entries must say so and state their
confidence; commit subjects alone are insufficient evidence.

## 2026-07-30

- Console Change IDs: `CONSOLE-2026-006`
- Title: Make Component Registry readiness and public-only Console generation cycle-free and exactly verifiable
- Lifecycle: `CONSOLE-2026-006` changed
- Feature or component: Operations Component Registry specialist and public-only Console generation
- State: Proposed / unmerged
- Implementation commits: Proposed / unmerged
- Rollback baseline: `b82764f21a39c14e35c371cc6a4530d4a1b11c82`

### Operations & automation

- Category ID: `operations_automation`
- Change ID: `CONSOLE-2026-006`
- Commit IDs: Proposed / unmerged
- Material change: Added an explicit `--public-only` tracked-output operation that rebuilds the public Console without opening, restoring, or authorizing ignored owner-only projections. Owner Console staging remains a separate operation and may follow only an authorized normal owner-bound generation that restores and validates the exact bound owner-only projections.
- Validation: Public-only generation tests instrument owner-only paths, preserve unavailable owner-log and occurrence states, and reject owner staging without its separately restored bound inputs.

### Data, provenance & integrity

- Category ID: `data_provenance_integrity`
- Change ID: `CONSOLE-2026-006`
- Commit IDs: Proposed / unmerged
- Material change: Removed the terminal activation-readiness receipt from the candidate Console input graph. The public Component Registry readiness projection now derives only from the validated candidate namespace and exact requirement closure; after generation, the terminal receipt binds the catalog, embedded and standalone generation manifests, source-hash map, and every generated domain by exact identity, bytes, digest, and record count.
- Validation: Candidate-input instrumentation, exact generated-file-set checks, large-domain coverage, generation and source-binding mismatch tests, and terminal readback reproduction cover the new provenance boundary.

### Security, privacy & disclosure

- Category ID: `security_privacy_disclosure`
- Change ID: `CONSOLE-2026-006`
- Commit IDs: Proposed / unmerged
- Material change: Public-only generation neither reads nor restores private Console projections and never treats unavailable owner-only data as empty, zero, current, or healthy. The tracked public bundle and terminal readback exclude private scripts, owner-local paths, activation receipt content, and protected operational details.
- Validation: Private-input nonaccess, public-bundle allowlist, unavailable-state, manifest, source-hash, and disclosure-gate checks cover the boundary.

### Reliability, accessibility & performance

- Category ID: `reliability_accessibility_performance`
- Change ID: `CONSOLE-2026-006`
- Commit IDs: Proposed / unmerged
- Material change: Replaced the former circular readiness dependency with one directional sequence: validated candidate and requirement closure, then one complete public Console generation, then one terminal readiness receipt. Later validation is read-only; any changed generated file invalidates terminal readback rather than starting a regeneration loop.
- Validation: Cycle-exclusion, byte-stability, missing/extra/swapped/modified output, and post-receipt mutation regressions cover the sequence.

### Governance & documentation

- Category ID: `governance_documentation`
- Change ID: `CONSOLE-2026-006`
- Commit IDs: Proposed / unmerged
- Material change: Documented the public-only operation, its unavailable owner-data posture, and the prohibition on treating it as owner Console staging authority. The Component Registry remains candidate, nonauthoritative, nonexecutable, and pending separate human activation.
- Validation: Console specification, README, registered-category, existing-change-ID, unmerged-state, and candidate-posture checks cover the documentation.

## 2026-07-29

- Console Change IDs: `CONSOLE-2026-002`; `CONSOLE-2026-003`; `CONSOLE-2026-004`; `CONSOLE-2026-005`; `CONSOLE-2026-006`
- Title: Authenticated owner refresh, private-runtime/dual-incident and transaction-recovery architecture, canonical Project Console package naming, owner-bound Codex usage, and the typed Component Registry specialist
- Lifecycle: `CONSOLE-2026-002` introduced; `CONSOLE-2026-003` introduced; `CONSOLE-2026-004` introduced; `CONSOLE-2026-005` proposed; `CONSOLE-2026-006` proposed
- Feature or component: Authenticated owner refresh; private-runtime, dual-incident, and preserved-transaction Console boundary; canonical source package and entrypoint; Codex usage Overview projection and Operations Capacity specialist; Operations Component Registry specialist
- State: `CONSOLE-2026-002` canonical through PR #485 and merge commit `10ec1342713e11543377b89de5f5ffc8cf5ddf8d`; `CONSOLE-2026-003` canonical through PR #490 and merge commit `5ce10580852b462be47d3a0f4cbe398684cbd096`; `CONSOLE-2026-004` canonical through PR #494 and merge commit `f39fb6b7ea4e43fe12099c022d50a5c0bd3db7da`; `CONSOLE-2026-005` proposed / unmerged; `CONSOLE-2026-006` proposed / unmerged
- Implementation commits: `CONSOLE-2026-002`: `8eae5943551ffe471dd9f53a30dd309e890dc360`, `fef0beacf4277b68c0164337b82344b1e56df8ae`, `fcf430a065e02e8c65c00290bec2193949319720`, `71e547155ce3b9c81972a50e9e9e8a0b493d0cbc`, `e1f7d37b95502ee590a324a6b5294082605703ac`, `8c1eb765ace51edd4f9782cf26692bad4b6e6a2f`, `15657d443f1a054fac42e8b5bc1c794c3b9935e7`, `d44cef748fff9f18abfada7466b8d5e0646bc224`, and `78381a335f16d9e2e4e16a9b4dcbd6f627da33c3`; `CONSOLE-2026-003`: `6167fc3554af006091ecee7d62be5a26514f7237`, `8306f07e96302afdca6ba85eae105905fc18cb60`, `754efbacf7f578b74823dc91a2e71a63cae42ecd`, `d81c688ccf84b61951852320c64d6da10d567039`, `7ca28d49940447caf46f00e04682a9af5053eb67`, `fa324b83ad4e787b9ac7497e59c632e222eed9d3`, `f234812661605d1f1e3776fd8835fb96b6e09ab3`, `d0d0adcd3249351f3b4de1118bd133f0a27aa08f`, `1d6e533688c8b2bdabfe3f06322ce4dbc5432abc`, `0de96259e1212595bbb10a9f3fe1165604fe6059`, `738f3c53970f64a86551c6327bcfd88be1e4bae8`, `5d1632e2a8e8f0eec809903ddb53db10f1c0d515`, `61dbb0895527b4007ae8509d1d33b11f3d221702`, `e834a381f5ee45254cd9e6eddd95c94a16c7a987`, `80fe2ef05453c9d536967bcf1a44b6cbae2dd65c`, `46d8300bb5b2cf8c2520eab2991a5196977366ae`, and `df1e54c6e00eae31a1a40d10022d9a66ac036942`; `CONSOLE-2026-004`: `e7be3ec12c09139c07959db7e25e2146b1f91a55`; `CONSOLE-2026-005`: Proposed / unmerged; `CONSOLE-2026-006`: Proposed / unmerged
- Rollback baseline: `CONSOLE-2026-002`: `4e6f2c293daf47a4584d1c25866cb6fc4f4e36ac`; `CONSOLE-2026-003`: `572e1db1ebfff49cc26004cced1d0933934fa4c6`; `CONSOLE-2026-004`: `509c636672c7154a946e95981ed3da4094ff8ce5`; `CONSOLE-2026-005`: `b82764f21a39c14e35c371cc6a4530d4a1b11c82`; `CONSOLE-2026-006`: `b82764f21a39c14e35c371cc6a4530d4a1b11c82`

### Interface & information architecture

- Category ID: `interface_information_architecture`
- Change ID: `CONSOLE-2026-003`; `CONSOLE-2026-006`
- Commit IDs: `CONSOLE-2026-003`: `6167fc3554af006091ecee7d62be5a26514f7237`, `8306f07e96302afdca6ba85eae105905fc18cb60`, `754efbacf7f578b74823dc91a2e71a63cae42ecd`, `738f3c53970f64a86551c6327bcfd88be1e4bae8`, and `61dbb0895527b4007ae8509d1d33b11f3d221702`; `CONSOLE-2026-006`: Proposed / unmerged
- Material change: Made the exact owner-file Console the sole owner-mode consumer of the bound private projection. Repository-source direct-disk, hosted, and loopback Console modes retain a public-only shell; the owner Console may show only approved private projections bound to their exact public generation, source revision, and integrity digests. Renamed the maintained source package to `research/project-console/` and its sole entrypoint to `project-console.html`, retiring the former source path without a duplicate compatibility directory or redirect. `CONSOLE-2026-006` adds Component Registry after Operations > Data and before Logs, with Documents, Directories, Routing, and Terminology modes and no Overview portlet. Registered legacy `operations:component-registry:*` document routes normalize one way to canonical `automation:component-registry:*` destinations.
- Validation: Owner-file binding, public-shell exclusion, unavailable-state, stale or malformed projection, canonical-path inventory, private-file exclusion, exact-entrypoint, tab-order, four-mode, no-Overview, and canonical/legacy-route tests cover the change.

### Operations & automation

- Category ID: `operations_automation`
- Change ID: `CONSOLE-2026-003`; `CONSOLE-2026-004`; `CONSOLE-2026-005`
- Commit IDs: `CONSOLE-2026-003`: `6167fc3554af006091ecee7d62be5a26514f7237`, `8306f07e96302afdca6ba85eae105905fc18cb60`, and `754efbacf7f578b74823dc91a2e71a63cae42ecd`; `CONSOLE-2026-004`: `e7be3ec12c09139c07959db7e25e2146b1f91a55`; `CONSOLE-2026-005`: Proposed / unmerged
- Material change: `CONSOLE-2026-003` implemented the canonical separate-authority Console specification for immutable Operational Incident (`INC`) and Security Incident (`SEC`) records with independently typed lifecycle and closure responsibility. Public shells expose neither incident ledger nor count; unavailable protected data cannot appear as zero. The protected `SEC` and relation data authorities remain inactive pending separate approval. The intentional binary `Paused` status remains preserved and is not itself an incident. `CONSOLE-2026-004` adds a registered owner-local `Preserved transactions` queue whose count and records come only from the typed transaction-lifecycle projection. The public Console has no transaction count or records, and a missing, incomplete, stale, or unbound private projection is unavailable rather than zero. `CONSOLE-2026-005` makes Operations > Capacity the sole detailed Codex usage home and retains Overview as its compact projection; both consume one exact-bound minimized owner-local usage projection. The fixed producer now emits schema version 2 with a 30-minute trustworthy-through boundary, exact weekly-reset identity, bounded typed history, independently available budget and burn-rate estimates, and no credit fields. Owner staging rejects production source substitution and binds a canonical semantic payload digest.
- Validation: Incident-authority, lifecycle, relation-integrity, path-authority, private-migration, transaction-projection, exact-count, retirement-proof, public-unavailable, shared-usage-projection, exact currentness, reset identity, payload-digest parity, source-substitution rejection, and Capacity-route checks cover the category.

### Data, provenance & integrity

- Category ID: `data_provenance_integrity`
- Change ID: `CONSOLE-2026-003`; `CONSOLE-2026-006`
- Commit IDs: `CONSOLE-2026-003`: `6167fc3554af006091ecee7d62be5a26514f7237`, `8306f07e96302afdca6ba85eae105905fc18cb60`, `754efbacf7f578b74823dc91a2e71a63cae42ecd`, `7ca28d49940447caf46f00e04682a9af5053eb67`, `e834a381f5ee45254cd9e6eddd95c94a16c7a987`, and `df1e54c6e00eae31a1a40d10022d9a66ac036942`; `CONSOLE-2026-006`: Proposed / unmerged
- Material change: `CONSOLE-2026-003` corrected stale or generated-data handling so unavailable, stale, malformed, or revision-mismatched data cannot appear current or healthy. Added typed classifications and context pins for incident, projection, and authority routing; public and private projections remain separate and retain their exact generation and revision relationship. Registered distinct unavailable-readback conditions for GitHub Issues, Project access, Project readback, and Pages so each Integrity finding retains a stable code, safe explanation, owner, next action, and destination rather than collapsing into indistinguishable generic findings. `CONSOLE-2026-005` adds exact nested validation for percentage, reset-window, anomaly, and estimate fields, including independent producer declarations for budget and burn-rate availability. `CONSOLE-2026-006` adds one strict builder projection from the validated Component Registry helper, hashing the candidate, schema, and context-route source and preserving producer-supplied typed document, directory, route, parity, and deferred-namespace facts. Invalid or stale registry state stops generation rather than yielding a fallback snapshot.
- Validation: Typed-classification, context-routing, generation-binding, stale-data, unavailable-state, registered-code, public-safe projection, unknown-code, nested usage-schema, estimate-dependency, Component Registry projection, exact parity, inventory-completeness, generated-domain, and stale-candidate fail-closed checks cover the category.

### Security, privacy & disclosure

- Category ID: `security_privacy_disclosure`
- Change ID: `CONSOLE-2026-002`; `CONSOLE-2026-003`; `CONSOLE-2026-005`
- Commit IDs: `CONSOLE-2026-002`: `8eae5943551ffe471dd9f53a30dd309e890dc360`, `fef0beacf4277b68c0164337b82344b1e56df8ae`, `fcf430a065e02e8c65c00290bec2193949319720`, `71e547155ce3b9c81972a50e9e9e8a0b493d0cbc`, `e1f7d37b95502ee590a324a6b5294082605703ac`, and `78381a335f16d9e2e4e16a9b4dcbd6f627da33c3`; `CONSOLE-2026-003`: `6167fc3554af006091ecee7d62be5a26514f7237`, `8306f07e96302afdca6ba85eae105905fc18cb60`, and `754efbacf7f578b74823dc91a2e71a63cae42ecd`
- Material change: `CONSOLE-2026-002` separated an owner-invoked authenticated
  refresh from the static Console, which remains unable to initiate that
  refresh. `CONSOLE-2026-003`
  preserved the public/private projection split: public surfaces report
  both incident ledgers and their counts only as unavailable, while the
  exact-bound owner-file Console can consume active, complete minimized
  owner-local projections. `SEC` and its relation authority remain inactive
  pending separate approval; this public record contains no protected evidence
  or incident detail. `CONSOLE-2026-005` permits detailed usage only through
  the exact generation-bound owner-file Console; repository-source, loopback,
  and hosted modes expose no private usage projection or fallback estimate.
  The minimized projection excludes account identity, prompts, task content,
  credentials, raw logs, local paths, and absolute capacity. The owner loader
  checks each requested private script against the exact `relative_path`
  registered for that same feed identity; a path registered to another feed
  cannot satisfy the request.
- Validation: The authenticated owner refresh completed its credential-
  confinement and data-contract checks. Disclosure-boundary, public-bundle
  allowlist, protected-field rejection, private-projection binding, and
  swapped-feed-path rejection checks cover the proposed changes.

### Reliability, accessibility & performance

- Category ID: `reliability_accessibility_performance`
- Change ID: `CONSOLE-2026-003`; `CONSOLE-2026-005`; `CONSOLE-2026-006`
- Commit IDs: `CONSOLE-2026-003`: `6167fc3554af006091ecee7d62be5a26514f7237`, `8306f07e96302afdca6ba85eae105905fc18cb60`, `754efbacf7f578b74823dc91a2e71a63cae42ecd`, and `80fe2ef05453c9d536967bcf1a44b6cbae2dd65c`; `CONSOLE-2026-005`: Proposed / unmerged; `CONSOLE-2026-006`: Proposed / unmerged
- Material change: Retained the deliberate initial synchronous JavaScript ceiling of 655 KiB while adding the owner-mode boundary and fail-closed projection behavior; unavailable data remains visible rather than silently substituted or treated as a zero result.
  Public shells use the single explanation `Data unavailable outside the bound
  owner-local Console.`, and incident-related static counters initialize as
  unavailable rather than briefly presenting a false zero.
  The public-site preparer now also fails closed when a prior staging tree
  exists instead of destructively replacing that tree; clean CI and governed
  transaction worktrees remain the supported preparation surfaces.
  The consistency scanner excludes the registered ignored owner-only Console
  projections from public repository-link and orphan analysis while retaining
  their separate schema, binding, and disclosure validation, so immutable
  private history cannot create a false public broken-link finding.
  `CONSOLE-2026-005` adds one responsive SVG history graph with a focusable
  image role, bound title and description, typed reset markers, and a textual
  equivalent. Capacity validation, digest verification, graphing, and
  specialist rendering are deferred through the public `capacity.js` module,
  which is copied into owner snapshots but absent from the static entrypoint,
  retaining the existing synchronous-script ceiling. `CONSOLE-2026-006`
  likewise defers both the Component Registry shell module and generated
  domain until its Operations subtab is opened, retains the 655 KiB startup
  ceiling, and copies both exact artifacts into immutable owner snapshots.
- Validation: Resource-budget, direct-disk and public-shell mode,
  stale/malformed feed, fresh-site-staging, and retained-sentinel regressions
  cover the change, together with an explicit owner-projection scope exclusion
  test, together with Codex-usage graph accessibility and resource-budget
  regressions, plus Component Registry strict-allowlist, keyboard-mode,
  startup-budget, lazy-entrypoint, owner-copy, and direct-file regressions.

### Governance & documentation

- Category ID: `governance_documentation`
- Change ID: `CONSOLE-2026-003`; `CONSOLE-2026-005`; `CONSOLE-2026-006`
- Commit IDs: `CONSOLE-2026-003`: `6167fc3554af006091ecee7d62be5a26514f7237`, `8306f07e96302afdca6ba85eae105905fc18cb60`, `754efbacf7f578b74823dc91a2e71a63cae42ecd`, `d81c688ccf84b61951852320c64d6da10d567039`, `5d1632e2a8e8f0eec809903ddb53db10f1c0d515`, and `46d8300bb5b2cf8c2520eab2991a5196977366ae`; `CONSOLE-2026-005`: Proposed / unmerged; `CONSOLE-2026-006`: Proposed / unmerged
- Material change: Added the Operations > Logs Governance changes selector and the bounded projection of registered public `GOV` entries. The Console preserves a Governance Change entry's stable identity and public-safe summary, routes to its complete record, and exposes an allowlisted owner-mode supplement summary only when the exact binding validates. This is a Console provenance feature, not a second governance ledger; governing decisions and their adoption or activation posture remain in the Governance Change Log and linked authorities. Reconciled the post-merge public governance evidence, including the canonical package-name adoption and its exact implementation provenance, while keeping protected supplements in the bound owner-local projection. `CONSOLE-2026-005` records the owner-bound Capacity specialist, projection boundary, estimate semantics, and accessibility requirements without copying private values or paths. `CONSOLE-2026-006` records the Component Registry specialist, its exact producer authority, explicit non-enforcement state, canonical and legacy route policy, builder failure boundary, deferred loading, and owner-copy behavior without duplicating the registry as a second authority.
- Validation: Governance Change Log parser, canonical-source/status consistency, projection, selection, exact supplement binding, unavailable-state, specification, README, same-day category, and Component Registry authority-boundary checks provide the Console-specific traceability.

## 2026-07-28

- Console Change IDs: `CONSOLE-2026-001`
- Title: Adopt holistic Console design and operational information architecture
- Lifecycle: Changed
- Feature or component: Whole Console
- State: Canonical through PR #483 and merge commit `1da18c49db38d4f6d6bc50fe1f5d21d46ac9f5e3`
- Implementation commits: `3f0f1d3d48b4aea148de9da92c946fe36f2c8a35`, `35e6e37203ccb117910360618c05362b91d3f06a`, `cf5ca6a32c1eb2d604be278d3c7b0feccb3db97b`, `c134191a6b440a979fea0f6049376ba9b0a66c8e`, `83a96daac1951c4379f3bbea069ddcb9e0cfb74a`, `c1480889f0f02fbb09dd075b1cbbb87a0ad43226`, `9a387f8add96a6555fc60d1054b7699f69ff939e`, `3b8ce0199619ad56ecc563cb49ca6e18ebe6c176`, `5e674630a41c91a0391af596c4c2f66324debe06`, `bb8a4e89c0ff2583f1317a669ceba6d8c710633b`, `35c78fa35b4f51123ab14dc5007f56856befe7f5`, `12a48c8d37cbf7455d6cc6368b91d54f5a76bdc8`, `3ee638f796c4f266261f18d13344d80ef5669a8f`, `b5133fc543121d884c91c0df3dcf752480f7c162`, and `d6077638eec28f3c1056382f9cd7d95708e53911`
- Rollback baseline: `a47082d0a684de38626c68fec325337765f35b9a`

### Interface & information architecture

- Category ID: `interface_information_architecture`
- Change ID: `CONSOLE-2026-001`
- Commit IDs: `3f0f1d3d48b4aea148de9da92c946fe36f2c8a35`, `35e6e37203ccb117910360618c05362b91d3f06a`, `c134191a6b440a979fea0f6049376ba9b0a66c8e`, `9a387f8add96a6555fc60d1054b7699f69ff939e`, `3ee638f796c4f266261f18d13344d80ef5669a8f`
- Material change: Consolidated the six-tab architecture; compacted Overview
  into dated verification, work queues, automation readiness, status, and
  material activity; standardized bounded master/detail workspaces and compact
  specialist menus; added browser-local grid Design mode without creating
  duplicate ledgers; and made the Overview projection immutable within one
  exact generated snapshot.
- Validation: Route-alias, responsive-layout, navigation-count, bounded-list,
  and frontend interaction tests passed.

### Planning & work management

- Category ID: `planning_work_management`
- Change ID: `CONSOLE-2026-001`
- Commit IDs: `3f0f1d3d48b4aea148de9da92c946fe36f2c8a35`, `35e6e37203ccb117910360618c05362b91d3f06a`, `9a387f8add96a6555fc60d1054b7699f69ff939e`, `3ee638f796c4f266261f18d13344d80ef5669a8f`
- Material change: Replaced Next Work with Planning > Workbench > Pipeline,
  retained Progress as measurement, moved deterministic human Priority
  attention above the complete Action Inbox, and kept Blocked/Deferred hold
  evidence and human decisions in their authoritative homes. Replaced the
  vague planning-gap total with separate typed next-action and workflow-status
  conditions.
- Validation: Inclusion, precedence, score-zero, missing-next-step, hold
  provenance, count/route, legacy-route, keyboard, and responsive tests passed.

### Operations & automation

- Category ID: `operations_automation`
- Change ID: `CONSOLE-2026-001`
- Commit IDs: `3f0f1d3d48b4aea148de9da92c946fe36f2c8a35`, `c134191a6b440a979fea0f6049376ba9b0a66c8e`, `9a387f8add96a6555fc60d1054b7699f69ff939e`, `3b8ce0199619ad56ecc563cb49ca6e18ebe6c176`, `3ee638f796c4f266261f18d13344d80ef5669a8f`
- Material change: Made Operations Overview the compact manager surface;
  separated the latest seven-stage run from seven cadence-aware role cards;
  added typed repository gates, provider-neutral platform status, and one
  event-backed Operational Incidents ledger; and moved complete history under
  Operations > Logs. Added one exact occurrence directory so a scheduled local
  occurrence cannot be combined with an older push chain, and refreshed the
  current repository-gate inventory through its authenticated producer.
- Validation: Run-chain, role-status, repository-gate, incident,
  platform-adapter, and current-exception tests passed.

### Data, provenance & integrity

- Category ID: `data_provenance_integrity`
- Change ID: `CONSOLE-2026-001`
- Commit IDs: `c134191a6b440a979fea0f6049376ba9b0a66c8e`, `9a387f8add96a6555fc60d1054b7699f69ff939e`, `3b8ce0199619ad56ecc563cb49ca6e18ebe6c176`, `3ee638f796c4f266261f18d13344d80ef5669a8f`
- Material change: Preserved Integrity as the exact report, added per-fact
  currentness and outcome provenance, made unavailable data nonzero and
  nonhealthy, refreshed the Console from authenticated Project data, and bound
  private Operations to the exact public generation and source revision.
  Added registered queue, shared Action, Operations Data, typed activity, and
  typed capacity projections; refreshed all 2,055 Source Checker records; and
  retained a current Integrity report with explicit Project-readback
  unavailability rather than a false clean result.
- Validation: Data-contract, generation-manifest, exact-count, stale-feed,
  same-run Integrity, and private-generation-binding tests passed.

### Security, privacy & disclosure

- Category ID: `security_privacy_disclosure`
- Change ID: `CONSOLE-2026-001`
- Commit IDs: `83a96daac1951c4379f3bbea069ddcb9e0cfb74a`, `c1480889f0f02fbb09dd075b1cbbb87a0ad43226`, `9a387f8add96a6555fc60d1054b7699f69ff939e`, `3b8ce0199619ad56ecc563cb49ca6e18ebe6c176`, `3ee638f796c4f266261f18d13344d80ef5669a8f`
- Material change: Replaced the alert inventory with seven registered,
  allowlisted Security assurance checks; kept detailed evidence at protected
  authorities; made protected Action Items generic; and established one
  public enforcement core with a required owner-local disclosure control pack.
  Moved the generic protected-action mapping into the exact-bound owner-local
  Action producer so the browser cannot originate Security work taxonomy.
- Validation: The active control pack approved the complete 575-artifact
  prospective tree and exact 67-artifact outgoing change with zero findings.
  Security allowlist,
  no-detail, path-authority, route-validation, and secret-sanitization tests
  passed.

### Reliability, accessibility & performance

- Category ID: `reliability_accessibility_performance`
- Change ID: `CONSOLE-2026-001`
- Commit IDs: `c134191a6b440a979fea0f6049376ba9b0a66c8e`, `9a387f8add96a6555fc60d1054b7699f69ff939e`, `3b8ce0199619ad56ecc563cb49ca6e18ebe6c176`, `3ee638f796c4f266261f18d13344d80ef5669a8f`
- Material change: Restored the canonical direct-disk Console as a supported
  owner mode, gated all ignored local feeds to canonical `file://` or loopback,
  kept hosted HTTPS public-only, added accessible fact dots and keyboard list
  selection, applied route state only after required data readiness, and
  retained bounded DOM and script budgets.
- Validation: Canonical/unrelated file-path, loopback/public-host, missing and
  malformed local-feed, accessibility, strict public-site, and resource-budget
  tests passed.

### Governance & documentation

- Category ID: `governance_documentation`
- Change ID: `CONSOLE-2026-001`
- Commit IDs: `3f0f1d3d48b4aea148de9da92c946fe36f2c8a35`, `9a387f8add96a6555fc60d1054b7699f69ff939e`, `3b8ce0199619ad56ecc563cb49ca6e18ebe6c176`, `5e674630a41c91a0391af596c4c2f66324debe06`, `bb8a4e89c0ff2583f1317a669ceba6d8c710633b`, `35c78fa35b4f51123ab14dc5007f56856befe7f5`, `12a48c8d37cbf7455d6cc6368b91d54f5a76bdc8`, `3ee638f796c4f266261f18d13344d80ef5669a8f`
- Material change: Established the comprehensive Console contract,
  heading-based Development Log, stable Change IDs, public/private data
  boundary, and registered development-log categories whose materially changed
  sections render as separate selectable entries. Configuration exports remain
  staged only and persistent host changes still require immediate approval.
  Made typed classification authority an executable build rule, added a
  finding-to-change-to-test closure matrix, and preserved the approved
  no-duplicate-checkout safeguard.
- Validation: Context-route hashes, classification registry, development-log
  category metadata, seven-entry category projection, governing documentation,
  and full regression suites passed.
