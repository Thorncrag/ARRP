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

- Console Change ID: `CONSOLE-2026-003` (Proposed / unmerged; commit pending)
- Current runtime authority: Application Support production runtime
- Successor posture: named companion workspace, protected inactive staging descriptor only
- Closure posture: code and listed validations are implemented where stated;
  host cutover, policy activation, and Git publication remain pending explicit
  human approval.

| ID | Finding | Governing change | Required validation | State |
| --- | --- | --- | --- | --- |
| PRDI-001 | One incident ledger could conflate operational recovery with protected security investigation. | Separate immutable `INC` and owner-local `SEC` authorities; each has its own identity, lifecycle, owner, evidence boundary, and closure proof. | Operational/Security incident schema and lifecycle tests; no cross-domain closure mutation. | Implemented in code and tests; policy activation and Git publication pending human approval |
| PRDI-002 | A cross-domain relationship could become a covert third ledger. | Append-only typed relation journal is a navigation/index authority only and preserves source IDs plus separate counts. | Relation referential-integrity, recurrence, and lifecycle-independence tests. | Implemented in code and tests; policy activation and Git publication pending human approval |
| PRDI-003 | Public Console output could expose protected incident details or imply a zero count. | Repository-source direct-disk, loopback, and hosted modes expose both incident ledgers and counts as unavailable; only an exact generation- and revision-bound owner-file Console may load an active, complete allowlisted projection. | Public-bundle/DOM allowlist, file-mode binding, static-counter, stale/malformed projection, and unavailable-state tests. | Implemented in code and tests; policy activation and Git publication pending human approval |
| PRDI-004 | A documented private successor arrangement could be mistaken for a live runtime cutover. | The Application Support runtime remains production authority; the named companion workspace is a protected inactive staging descriptor until separate approved host cutover. | Path-authority/migration verifier; pause and no-host-mutation checks. | Implemented in code and tests; canonical adoption, host cutover, and Git publication pending human approval |
| PRDI-005 | Public documentation could reproduce restricted evidence while describing the new boundary. | Registry, interface, disclosure, and structure records use only safe typed authority descriptions and protected references. | Disclosure gate and restricted-content negative fixtures. | Implemented in code and tests; policy activation and Git publication pending human approval |
| PRDI-006 | Local public-site preparation could destructively replace a pre-existing ignored staging tree. | Site preparation now requires a fresh staging root and fails closed when an earlier tree exists; clean CI and governed transaction worktrees remain the supported preparation surfaces. | Fresh-stage generation and retained-sentinel regression; strict MkDocs build. | Implemented in code and tests; Git publication pending human approval |
| PRDI-007 | Current production paths, inactive successor staging, runtime artifact classes, owner Console copies, and cutover rules were described in several surface-specific documents without one scoped authority. | Added the governing Owner-Local Runtime Authority; registered and hash-pinned it; routed automation, incident, disclosure, Console, and logical owner-local references to it; retained each specialist document's narrower authority. | Context dependency/hash validation, documentation contract tests, local-link audit, and whole-project consistency audit. | Implemented in documentation and tests; Git publication pending human approval |

## Scope and closure rule

This matrix governs documentation and contract alignment only. It does not
authorize a host move, scheduler change, pause removal, incident migration,
runtime activation, GitHub mutation, policy activation, or private-record
transfer. The design is closed only when its code, schemas, Console
projections, and whole-project consistency checks satisfy the listed
validations; the required human approvals complete cutover, policy activation,
and Git publication; and the separate owner-local morning reports record the
final implementation state.
