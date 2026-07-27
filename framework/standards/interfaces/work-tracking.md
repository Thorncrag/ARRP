---
title: "Work-Tracking Standard"
status: active
authority_scope: "Reusable separation of substantive records, maturity, workflow action, holds, monitoring, and hosted collaboration."
load_when: "Creating or changing a work item, workflow field, hold, monitoring record, roadmap item, or hosted collaboration rule."
dependencies:
  - "../content/maturity-and-gates.md"
  - "../automation/validation-and-closeout.md"
print_status: excluded
print_exclusion_reason: "Internal workflow documentation."
---

# Work-Tracking Standard

The repository owns adopted substance. A hosted work item owns discussion,
assignment, and the current collaboration record. Structured project fields may
own workflow metadata. No one surface substitutes for another.

- Maturity records substantive development.
- Workflow state records the current next action or hold.
- Monitoring records a matter being watched and its reassessment trigger.
- Audit fields record review control and results.
- Labels carry only kind or temporary triage not already represented by a
  structured field.

Preserve stable work-item identity and disposition history. Close an item when
no active obligation remains, but do not delete it merely because it was
merged, integrated, retired, or rejected. Remove only its active-board
projection when appropriate.

Meaningful child work should use the hosted platform's native relationship
rather than a competing Markdown-only task list. After any mutation, read back
the authoritative item and every field the change was intended to update.
