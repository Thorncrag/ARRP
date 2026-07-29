---
title: "Private runtime and dual-incident design closure matrix"
status: active
print_status: excluded
print_exclusion_reason: "Internal governance and validation record."
---

# Private Runtime and Dual-Incident Design Closure Matrix

This public-safe matrix records the approved design review boundary for
`ARRP-PRIVATE-RUNTIME-DUAL-INCIDENT-2026-07-29`, revision
`sha256:e189a14119161e91f4ce92c1bdfca7be71d9267449bcabf87745a3a43a92027b`.
It intentionally contains no
Security Incident evidence, vulnerability detail, private operational state,
credential material, local absolute path, or host-control instruction.

- Console Change ID: `CONSOLE-2026-003` (canonical through PR #487 and merge
  commit `ea57c9826270a12ae6e0275390a2c9555169f43d`)
- Current runtime authority: Application Support production runtime
- Successor posture: named companion workspace, protected inactive staging descriptor only
- Closure posture: the public design and implementation are canonical; host
  cutover, private-policy amendment, protected Security Incident/relation
  activation, pause removal, and production automation remain separately
  reserved and inactive.

## Post-merge reconciliation

This matrix was first recorded before publication. PR #487 preserved the
approved design on canonical history through implementation commits
`6167fc3554af006091ecee7d62be5a26514f7237`,
`8306f07e96302afdca6ba85eae105905fc18cb60`, and
`754efbacf7f578b74823dc91a2e71a63cae42ecd`. `GOV-2026-011`,
`GOV-2026-012`, and `GOV-2026-013` are canonical. `GOV-2026-014` remains
`Proposed / not adopted`; the existing owner directive remains controlling.
This reconciliation changes no runtime, host service, pause state, private
policy, or incident authority.

| ID | Finding | Governing change | Required validation | State |
| --- | --- | --- | --- | --- |
| PRDI-001 | One incident ledger could conflate operational recovery with protected security investigation. | Separate immutable `INC` and owner-local `SEC` authorities; each has its own identity, lifecycle, owner, evidence boundary, and closure proof. | Operational/Security incident schema and lifecycle tests; no cross-domain closure mutation. | Canonical design and implementation; protected `SEC` activation remains separately reserved |
| PRDI-002 | A cross-domain relationship could become a covert third ledger. | Append-only typed relation journal is a navigation/index authority only and preserves source IDs plus separate counts. | Relation referential-integrity, recurrence, and lifecycle-independence tests. | Canonical design and implementation; relation-authority activation remains separately reserved |
| PRDI-003 | Public Console output could expose protected incident details or imply a zero count. | Repository-source direct-disk, loopback, and hosted modes expose both incident ledgers and counts as unavailable; only an exact generation- and revision-bound owner-file Console may load an active, complete allowlisted projection. | Public-bundle/DOM allowlist, file-mode binding, static-counter, stale/malformed projection, and unavailable-state tests. | Canonical design and implementation; unavailable protected feeds remain unavailable rather than zero |
| PRDI-004 | A documented private successor arrangement could be mistaken for a live runtime cutover. | The Application Support runtime remains production authority; the named companion workspace is a protected inactive staging descriptor until separate approved host cutover. | Path-authority/migration verifier; pause and no-host-mutation checks. | Canonical contract; live host cutover remains separately reserved and inactive |
| PRDI-005 | Public documentation could reproduce restricted evidence while describing the new boundary. | Registry, interface, disclosure, and structure records use only safe typed authority descriptions and protected references. | Disclosure gate and restricted-content negative fixtures. | Canonical public-safe documentation; no protected evidence published |
| PRDI-006 | Local public-site preparation could destructively replace a pre-existing ignored staging tree. | Site preparation now requires a fresh staging root and fails closed when an earlier tree exists; clean CI and governed transaction worktrees remain the supported preparation surfaces. | Fresh-stage generation and retained-sentinel regression; strict MkDocs build. | Canonical implementation and validation |
| PRDI-007 | Current production paths, inactive successor staging, runtime artifact classes, owner Console copies, and cutover rules were described in several surface-specific documents without one scoped authority. | Added the governing Owner-Local Runtime Authority; registered and hash-pinned it; routed automation, incident, disclosure, Console, and logical owner-local references to it; retained each specialist document's narrower authority. | Context dependency/hash validation, documentation contract tests, local-link audit, and whole-project consistency audit. | Canonical documentation and validation; current production authority remains unchanged |

## Scope and closure rule

This matrix governs documentation and contract alignment only. It does not
authorize a host move, scheduler change, pause removal, incident migration,
runtime activation, GitHub mutation, policy activation, or private-record
transfer. The design is closed only when its code, schemas, Console
projections, and whole-project consistency checks satisfy the listed
validations; the required human approvals separately govern cutover, private
policy revision, protected-authority activation, and pause removal; and the
owner-local reports record implementation and post-finalization review.
