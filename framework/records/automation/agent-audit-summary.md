---
title: "ARRP Agent Audit Summary"
print_status: excluded
print_exclusion_reason: "Online operational summary."
---

# ARRP Agent Audit Summary

ARRP keeps the complete append-only Agent Audit Log in the owner-local runtime
authority at `owner-local:records/automation/agent-audit-log.md`. That ledger
records material bot and autonomous-agent actions, exact run provenance,
validation, synchronization, rollback references, and unresolved boundaries.
It is not transmitted to GitHub.

The Project Console receives a minimized, allowlisted projection of that local
authority. The browser does not read the local ledger directly and cannot
reconstruct omitted operational evidence. Public change history for the
Console itself remains in
[`console-development-log.md`](console-development-log.md).

## Retention contract

- The owner-local log is append-only and preserves distinct material events.
- Ordinary clean no-change runs remain in bounded local run history.
- Public projections contain only fields approved by their typed producer.
- Exact runtime topology, restricted diagnostics, account-specific state, and
  sensitive evidence remain owner-local.
- Operational Incident identity and lifecycle are governed separately by the
  owner-local incident event authority and its public typed contract.
