# ARRP Codex Guidance

Before substantive ARRP work, read [`framework/FRAMEWORK.md`](framework/FRAMEWORK.md), [`framework/METHODOLOGY.md`](framework/METHODOLOGY.md), [`framework/AGENT_OPERATING_RULES.md`](framework/AGENT_OPERATING_RULES.md), and [`framework/CURRENT_AUDIT.md`](framework/CURRENT_AUDIT.md). Read [`framework/GITHUB_WORKFLOW.md`](framework/GITHUB_WORKFLOW.md) whenever GitHub issues, Project fields, or lifecycle status may be affected.

Use parallel agents by default whenever the work can be divided into independent, non-overlapping responsibilities and doing so is expected to improve speed or coverage. Do not impose an arbitrary agent, time, token, or usage cap based on historical subscription limits. Keep overlapping edits under one agent, and make the coordinating agent responsible for reconciliation, validation, and closeout. Use a single agent when coordination overhead or shared-file risk would outweigh the expected gain.

On this macOS workspace, GitHub CLI credentials are stored in the macOS Keychain, which sandboxed commands cannot read. Run authenticated `gh` commands, `gh auth status` diagnostics, and authenticated Git network operations in the approved host context. Do not treat a sandbox-only "invalid" result as a revoked credential, do not create a plaintext fallback token with `--insecure-storage`, and reauthorize only if the host-context check also fails.

Do not rely on Python packages or document binaries bundled inside the Codex application: that runtime may change during an app update. For reproducible local website, PDF, and document validation, run [`scripts/bootstrap_local_tools.sh`](scripts/bootstrap_local_tools.sh) once and use `.venv/bin/python` for project Python commands that require third-party packages. The macOS host should provide the Homebrew tools listed in that script, including Poppler, Tesseract/OCRmyPDF, QPDF/Ghostscript, Pandoc, Node.js, ripgrep, ShellCheck, and ExifTool. When invoking those host tools from a sandboxed Codex command, put Homebrew first and keep Fontconfig's cache inside the ignored workspace: `PATH="/opt/homebrew/bin:$PATH" XDG_CACHE_HOME="$PWD/.tmp/cache"`. GitHub Actions remains the publication authority and installs its own pinned website dependencies.

In project-authored reader-facing prose, apply the framework's neutral-characterization and reader-language rules: avoid unsupported conclusory shorthand such as `sham`, describe the relevant conduct or criteria, and translate unexplained `T0`–`T4` or audit-workflow terminology into reader-friendly prose. Preserve exact terms in internal technical records, machine-readable metadata, and attributed source material.

Any request to focus on, research, develop, draft, revise, or otherwise work substantively on an issue invokes the issue-development lifecycle check even when the user does not mention an audit or status update.

At the start of issue work:

1. Read the canonical issue page, linked proposal vehicle, latest audit entry, next step, and authoritative GitHub Project row.
2. If substantive development begins while the Project status is `Pending development`, change it to `In development` and read it back. Do not regress a later lifecycle status merely because revision begins.
3. Do not change `Score` or `Runs` for research, drafting, source development, a Change Audit, or other non-T-audit work.

At closeout:

1. Leave an incomplete initial issue-and-vehicle package `In development`.
2. Set an unscored initial package to `Audit needed` once the issue page and concrete proposal vehicle are complete enough for the next T-audit.
3. After a completed score-bearing T-audit, apply the score and lifecycle rules in the methodology. For a materially revised scored proposal, preserve the score-based status and use `Change audit needed` until the required review is complete.
4. Synchronize and read back all affected GitHub Project fields. Refresh and verify the Review Ready dashboard whenever its governing workflow requires it.

The GitHub Project is the lifecycle-status authority. Detailed transition, audit, validation, preservation, and publication rules remain in the linked governing files; this file routes Codex into those rules and does not replace them.
