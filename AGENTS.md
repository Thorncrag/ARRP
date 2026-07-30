---
module_id: codex_bootstrap
dependencies:
  - "framework/FRAMEWORK.md"
  - "framework/AGENT_OPERATING_RULES.md"
  - "framework/handoffs/current-task.md"
  - "framework/component-registry.json"
---

# ARRP Codex Guidance

Before substantive ARRP work, read the compact mandatory kernels in [`framework/FRAMEWORK.md`](framework/FRAMEWORK.md) and [`framework/AGENT_OPERATING_RULES.md`](framework/AGENT_OPERATING_RULES.md), plus the live continuation checkpoint in [`framework/handoffs/current-task.md`](framework/handoffs/current-task.md). These files are the required floor, not the complete context for every task.

Use the module route table in the Framework and the validated routing view in
[`framework/component-registry.json`](framework/component-registry.json) to
load the additive union of every operation and capability implicated by the
work, together with each selected module's dependencies. Expand context before
taking an action that newly implicates another authority. Read
[`framework/project/github/workflow.md`](framework/project/github/workflow.md)
whenever GitHub issues, Project fields, lifecycle status, or authenticated
synchronization may be affected.

Use parallel agents by default when work divides into independent,
non-overlapping responsibilities and the expected gain exceeds coordination
risk. Prefer lower-reasoning subagents for bounded, routine, mechanical, or
independently verifiable subtasks when that setting is sufficient, conserving
token usage without reducing required context, coverage, evidence, audit depth,
or validation. Retain the coordinating thread's reasoning level for
architecture, security, governance, ambiguity resolution, reconciliation, and
final acceptance. The coordinating agent owns reconciliation, validation, and
closeout.

On this macOS workspace, GitHub CLI credentials are stored in the macOS Keychain. Run authenticated `gh` commands and authenticated Git network operations in the approved host context; do not treat a sandbox-only credential failure as revocation or create a plaintext fallback token.

Use the project-local `.venv` and host tools provisioned by [`scripts/bootstrap_local_tools.sh`](scripts/bootstrap_local_tools.sh) for reproducible website, PDF, OCR, and document validation. GitHub Actions remains the publication authority.

When the local Codex project includes the owner-local sibling folder `ARRP Private` as a secondary folder, keep this ARRP repository as the primary folder for chats and Git operations. Before reading or changing anything in the secondary folder, read and obey its `OWNER_DIRECTIVE.md` and `AGENTS.md`. Treat all of its contents as owner-local restricted material: never copy them into this repository, the public Console bundle, GitHub, or another external service unless Benjamin expressly approves the exact transfer and the governing disclosure control separately authorizes it. The fixed Application Support state root remains the current production runtime; `ARRP Private` is inactive successor staging unless the exact cutover in the [owner-local runtime authority](framework/project/automation/owner-local-runtime.md) is separately approved and verified.

Any substantive issue work invokes the issue-development lifecycle check in the Framework and GitHub workflow even when the user does not mention status or audit work. Read and synchronize both `Development level` (substantive maturity) and `Status` (current workflow action or hold); never use one as a substitute for the other. Do not change `Score` or `Runs` for research, drafting, source development, Change Audits, or other non-T-audit work.

Apply neutral characterization and reader-friendly language in project-authored public prose. Preserve exact internal terminology in technical records, machine-readable metadata, and attributed source material.

This file is the required tool-discovered bootstrap, not a second detailed
rulebook. The
[`Component Registry`](framework/component-registry.json) identifies every
governing file, its scope, and its current routing relationships.
