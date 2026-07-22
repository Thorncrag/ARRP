# ARRP Codex Guidance

Before substantive ARRP work, read [`framework/FRAMEWORK.md`](framework/FRAMEWORK.md), [`framework/AGENT_OPERATING_RULES.md`](framework/AGENT_OPERATING_RULES.md), and [`framework/logs/CURRENT_AUDIT.md`](framework/logs/CURRENT_AUDIT.md). Read [`framework/GITHUB_WORKFLOW.md`](framework/GITHUB_WORKFLOW.md) whenever GitHub issues, Project fields, lifecycle status, or authenticated synchronization may be affected. Read specialized framework files only when their subject is implicated.

Use parallel agents by default when work divides into independent, non-overlapping responsibilities and the expected gain exceeds coordination risk. The coordinating agent owns reconciliation, validation, and closeout.

On this macOS workspace, GitHub CLI credentials are stored in the macOS Keychain. Run authenticated `gh` commands and authenticated Git network operations in the approved host context; do not treat a sandbox-only credential failure as revocation or create a plaintext fallback token.

Use the project-local `.venv` and host tools provisioned by [`scripts/bootstrap_local_tools.sh`](scripts/bootstrap_local_tools.sh) for reproducible website, PDF, OCR, and document validation. GitHub Actions remains the publication authority.

Any substantive issue work invokes the issue-development lifecycle check in the Framework and GitHub workflow even when the user does not mention status or audit work. Read and synchronize both `Development level` (substantive maturity) and `Status` (current workflow action or hold); never use one as a substitute for the other. Do not change `Score` or `Runs` for research, drafting, source development, Change Audits, or other non-T-audit work.

Apply neutral characterization and reader-friendly language in project-authored public prose. Preserve exact internal terminology in technical records, machine-readable metadata, and attributed source material.

This file is the required tool-discovered bootstrap, not a second detailed rulebook. The repository-purpose map in [`framework/PROJECT_STRUCTURE.md`](framework/PROJECT_STRUCTURE.md) identifies every governing file and its scope.
