---
title: "ARRP Elim Run Summary"
print_status: excluded
print_exclusion_reason: "Online operational summary."
---

# ARRP Elim Run Summary

The complete per-invocation Elim journal is retained at
`owner-local:records/automation/elim-run-log.md`. It records exact run
provenance, selected work, validation, continuation, and links to material-unit
records. It is not transmitted to GitHub. The logical path currently resolves
to the fixed Application Support production root under the [ARRP Owner-Local
Runtime Authority](../../project/automation/owner-local-runtime.md); it does
not imply that the inactive protected successor staging descriptor is live.

The Project Console receives a minimized typed projection of this authority.
Every invocation remains distinct in the local journal; same-day presentation
grouping never erases a run or occurrence.

## Public contract

- Elim never receives GitHub credentials or mutation authority.
- Deterministic code validates its bounded result before any dependent action.
- Material work is recorded in the owner-local Agent Audit Log.
- Operational disruptions are recorded through the separate incident
  authority, even when Elim fails before returning a valid result.
- Console projections contain only allowlisted public-safe fields and links.
