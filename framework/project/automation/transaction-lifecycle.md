---
title: "ARRP Transaction Lifecycle and Recovery Authority"
status: active
authority_scope: "Owner-local append-only transaction attempt history, retry authorization, recovery-package proof, and safe projection."
dependencies:
  - "owner-local-runtime.md"
  - "operational-incidents.json"
  - "transaction-lifecycle.schema.json"
  - "transaction-recovery-package.schema.json"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# ARRP Transaction Lifecycle and Recovery Authority

`owner-local:records/automation/transaction-events.jsonl` is the single
append-only authority for each runtime transaction attempt. `status.json` and
`last-scheduled-slot.json` are replaceable projections only; neither can
create, close, retry, or retire an attempt.

Each attempt has a stable `run_id`, an occurrence-wide `attempt_group_id`, and
an increasing `attempt_number`. Its immutable events bind trigger, branch,
head, base, logical worktree/run identities, delta/package digests, failure
code, typed Operational Incident link, owner, next action, and opaque evidence
references. Incident linkage is reciprocal work for the Incident authority;
it does not close either lifecycle by implication.

The permitted transaction states are `active`, `failed_preserved`,
`recovery_pending`, `reconciled_or_superseded`, `recovery_packaged`,
`recoverably_retired`, `completed_noop`, and `completed_published`.
Completion requires an exact terminal proof. A released lock with no terminal
event is recorded as `abandoned` / `recovery_pending`, never inferred to be a
success. A worktree remains live until deterministic reconciliation or a
digest-bound recovery package and recoverable-retirement proof establish its
disposition. No more than one live worktree may exist in an attempt group.

A pre-activation estate that already violates that invariant may enter the
authority only through one atomic `historical_imported` batch. Every member
must carry the same registered migration identity, attempt group, complete
member-set digest, source-slot evidence, and exact recovery-package proof.
The batch remains live and retry-blocking until every source worktree has its
own exact recoverable-retirement proof. This migration-only observation does
not make packaging a disposition and does not weaken ordinary creation: a
missing, extra, duplicated, truncated, mixed, or mismatched member makes the
entire lifecycle authority unavailable.

A distinct single-member `historical_imported` record is permitted only for a
legacy run that never had a runtime worktree. It carries one migration identity
and source slot, has `logical_worktree_id: null`, and is immediately
`completed_noop` or `completed_published` with exact terminal proof. It may
not carry a package, recovery proof, failure code, predecessor, or retry
authorization. This terminal reconstruction is not a shortcut for retained
worktree migration and cannot alter the multi-member batch contract above.

A retry is a linked event, not a slot action. It requires a one-use,
expiry-checked authorization bound to the predecessor run ID and its terminal
event digest. Before claim, the predecessor must be reconciled/superseded or
sealed in a recovery package; an unresolved predecessor fails closed.

Recovery manifests conform to
[`transaction-recovery-package.schema.json`](transaction-recovery-package.schema.json).
They are owner-only non-checkout archives sufficient to reconstruct commits,
diffs, and untracked material. A manifest authorizes neither deletion nor
retirement. Exact target approval and recoverable handling remain separate.
The deterministic [`recover_transactions.py`](../../../scripts/recover_transactions.py)
tool accepts only a stable run ID, resolves the fixed production authority,
verifies the registered branch/worktree/run identity and Git containment, and
can create the package without changing or removing its source.

The Console projection is a minimized public-safe shape, but it is produced
and loaded only for the exact bound owner-local Console. It contains only typed
IDs, states, count, owner, age, failure class, and next action. It excludes
paths, raw diagnostics, private deltas, and owner-local evidence, and the
public or hosted Console receives an unavailable state rather than records or
a count.
