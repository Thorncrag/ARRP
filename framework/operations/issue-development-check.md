---
title: "Issue-Development Lifecycle Check"
status: active
authority_scope: "The mandatory preflight and closeout classification for substantive issue work."
load_when: "Any request focuses on, researches, develops, drafts, revises, or otherwise works substantively on an issue."
dependencies: "../FRAMEWORK.md; ../AGENT_OPERATING_RULES.md; ../lifecycle/development-levels.md; ../lifecycle/foundation-and-development-gates.md; ../GITHUB_WORKFLOW.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Issue-Development Lifecycle Check

## Authority and Dependencies

This file is the authoritative substantive preflight and closeout check for issue-development work. The governing principles in [`../FRAMEWORK.md`](../FRAMEWORK.md), maturity rules in [`../lifecycle/development-levels.md`](../lifecycle/development-levels.md), and foundation and gates in [`../lifecycle/foundation-and-development-gates.md`](../lifecycle/foundation-and-development-gates.md) control. GitHub Status definitions, field values, and synchronization mechanics belong to [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md). Agent execution behavior belongs to [`../AGENT_OPERATING_RULES.md`](../AGENT_OPERATING_RULES.md).

## Load When

Load this file for any request to focus on, research, develop, draft, revise, or otherwise work substantively on an issue, even when the request does not mention an audit or status update.

## Required Check

Before substantive work, read the canonical issue page, concrete proposal vehicle if any, latest audit entry, next step, and authoritative GitHub Project row.

Do not change workflow status merely because a work session starts or stops. Classify the actual next action or hold under [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md). Do not reduce development level merely because research or revision begins. If the revision is material, preserve the established maturity and use the separate Change Audit control and the status identifying the actual next action or hold until the review is resolved.

At closeout, apply the six-level maturity lifecycle in [`../lifecycle/development-levels.md`](../lifecycle/development-levels.md), the substantive gates in [`../lifecycle/foundation-and-development-gates.md`](../lifecycle/foundation-and-development-gates.md), and the Project-field implementation in [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md). Keep development level separate from the next workflow status, and record monitoring independently.

Lifecycle synchronization is workflow maintenance, not an audit event. Research, drafting, source development, a lifecycle check, a Change Audit, and other non-T-audit work do not independently assign a formula score or increment `Runs`.
