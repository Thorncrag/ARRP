---
title: "Agent Rules — Validation and Closeout"
dependencies:
  - "../../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Agent Rules — Validation and Closeout

Load this module before closing an autonomous unit, issue audit, batched unit,
or task that changes repository, hosted-workflow, or generated-view state.
Also load it whenever validation, preservation, synchronization, publication,
or readback is implicated.

## Output and Preservation

Each completed audit should leave:

1. updated canonical content and review metadata;
2. a new preserved audit-history entry;
3. updated authoritative hosted-workflow fields where applicable;
4. updated retained-source records for sources used for audit credit;
5. validation notes;
6. preservation and synchronization through the project's reviewed publication
   boundary; and
7. a successful refresh and readback of every configured generated completion
   surface whose authoritative inputs changed, or an explicit recorded blocker
   identifying the failed process or stale generated state.

Configured hosted-workflow fields are a completion-critical surface for audit
work. If a field or row should change but cannot be updated because of
authentication, permissions, API, tooling, sandbox, or connector limitations,
notify the user as soon as the failure is known, identify the exact unsynced
field or row, and treat the task as blocked or partially complete until it is
updated or the user expressly accepts a repository-only interim state. A
temporary visibility fallback does not replace the authoritative structured
update.

When a generated view is completion-critical, refresh it only after its
authoritative inputs have been updated, synchronized, and read back. If
dispatch, authentication, generation, publication, or verification fails,
preserve the work, identify the stale value, record the exact remaining
synchronization step in the designated handoff checkpoint, and do not describe
the view as updated. One verified final refresh may close an expressly
authorized multi-unit batch when the project implementation permits it.

If validation cannot be completed because of a tool or environment failure, preserve the work if possible, record the skipped check, and notify the user.

If repository preservation or synchronization fails, stop the batch after
preserving the work locally, record the failure and changed files in the
configured provenance record or final report, and do not begin another issue
until repository state and authentication are resolved.

## Self-Validation Requirement

After each autonomous audit unit and before moving to the next issue, the agent
must validate its own work.

If a project validation script exists, run it. If the script supports issue-specific validation, run the issue-specific check for the completed issue and any broader project-level check required by the files changed.

If no validation script exists, perform a manual validation checklist before marking the unit complete:

1. confirm changed Markdown files render structurally and contain no obvious broken local links;
2. confirm canonical metadata matches the visible quality-review summary;
3. confirm the preserved audit history contains a new entry for the completed
   audit;
4. confirm canonical content, audit history, and hosted-workflow fields agree
   where they overlap;
5. for an integration-tier or routing-affecting change, confirm every
   configured navigation surface and stable registry is synchronized;
6. confirm the retained-source catalog parses and includes any source used for
   audit credit;
7. run a whitespace or formatting check where available;
8. confirm the synchronized revision is recorded in the configured provenance
   record when one is required;
9. if the unit changed goal-relevant fields, confirm the configured progress
   view reflects the new state or record the exact blocker; and
10. confirm no unintended files remain changed for that unit, including generated PDF, DOCX, XLSX, or similar export files unless the user requested an export refresh, the export is the deliverable, export tooling is being tested, or the work is expressly part of a release/publication pass.

If a validation check is skipped, record the check and reason in the configured
provenance record, the issue audit history when relevant, or the final
user-facing report. A unit should not be marked complete if validation fails,
except when the only failure is an explicitly documented environment or
tooling limitation and the work has been preserved for human review.

Successful task closeout also follows
[`task-handoffs.md`](task-handoffs.md): every completion-critical step must be
finished before the project's handoff checkpoint enters its completed state.
