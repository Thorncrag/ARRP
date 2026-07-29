---
title: "ARRP Project Configuration"
status: active
print_status: excluded
print_exclusion_reason: "Internal project-configuration directory guide."
---

# ARRP Project Configuration

This directory contains governing choices and procedures specific to the ARRP
installation: its profile, GitHub workflow, named automation, exact manifests,
and Project Console configuration.

Reusable rules belong in [`../standards/`](../standards/). State and history
belong in [`../records/`](../records/). A file may be binding ARRP authority
without being a reusable standard.

Begin with the [ARRP Project Profile](PROJECT_PROFILE.md) for the installation
choices and the [ARRP Repository Map](REPOSITORY_MAP.md) for the exact content,
configuration, and record surfaces. Exact maturity values and thresholds are
maintained in the [ARRP Maturity Profile](profile/maturity-profile.md). The
current and staged owner-local runtime boundary is governed separately by the
[ARRP Owner-Local Runtime
Authority](automation/owner-local-runtime.md).
Material governance decisions are recorded through the
[Governance Change Recording](workflows/governance-change-recording.md)
workflow and its stable registry; the changed governing document remains the
current-rule authority.

Complete Git, runtime-transaction, automation-posture, pull-request, and hosted
surface closeout is governed by the
[Project-Wide Reconciliation policy](automation/project-wide-reconciliation.json)
specification. It is an operational synchronization check, not a content or
editorial classification.
