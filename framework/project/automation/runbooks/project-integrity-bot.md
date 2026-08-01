---
title: "Project Integrity Bot Runbook"
agent_id: project-integrity-bot
display_name: Project Integrity Bot
console_purpose: "Checks repository structure, metadata, links, lifecycle coherence, and record wiring."
agent_type: deterministic-bot
status: enabled-local-stage
trigger: local-chain-after-other-inputs
schedule: "Every local chain after other deterministic inputs; no independent schedule"
runtime_id: scripts/audit_project_consistency.py
execution_environment: local-transaction-worktree
log_path: owner-local:records/automation/agent-audit-log.md
current_report: framework/status/project-integrity-report.md
checks_included:
  - Issue and proposal structure, including Issue Snapshot concision
  - Area and topic routing
  - Internal repository links
  - Markdown heading anchors
  - Orphaned Markdown pages
  - Page metadata and heading hierarchy
  - Cross-issue reference links
  - GitHub record references
  - GitHub Issue and Project synchronization
  - Lifecycle-field coherence and workflow explanations
  - GitHub Pages deployment synchronization
  - Source and citation catalogs
  - Research placement
  - Reader-facing language
  - Tool-interface conventions
  - Intake-workflow terminology
  - Publication-disposition metadata
  - Print-assembly configuration
  - Governing context registry, hashes, and module coverage
  - Persistent-agent runbooks and runtime configuration
  - Local-first source-monitoring and provenance wiring
  - Structured-file and repository hygiene
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Project Integrity Bot Runbook

## Inputs and permitted writes

The bot reads the repository, registries, routed governing records, and
runner-supplied authenticated snapshots. It may write only its declared
run-directory JSON and current Markdown status report. Validation is the
purpose of the stage. Publication occurs only through the coordinator's exact
reviewed pull-request boundary. Execution or schema failure is an explicit
stop; ordinary findings enter the queue.

The Project Integrity Bot deterministically checks repository structure,
metadata, identity, links, lifecycle coherence, source and proposal wiring,
navigation, structured files, and tracked-file hygiene. Its encoded checks are
detectors, not substantive judgments. A clean result means only that those
checks found no defect.

## Checks included

The machine-readable `checks_included` front matter is the authoritative
deterministic coverage floor for the current implementation.

## Local-stage contract

The coordinator runs the bot after the other current inputs and supplies exact
JSON and Markdown output paths. The typed integrity JSON is written under the
run directory; the replaceable current Markdown report may be updated only in
the transaction worktree. The stage must not require GitHub Actions, a report
branch, a data branch, workflow artifacts, or publication.

When hosted Issue or Project state is in scope, deterministic host code
supplies the authenticated snapshot. Elim never receives the credential. A
repository-only check must remain distinguishable from a hosted-surface
check.

Script, schema, accounting, or authorized-path failure is blocking. Detected
errors and warnings are successful observations and enter the integrity feed
and work queue; the bot cannot repair them, infer classifications, change
Project fields, or make legal, evidentiary, lifecycle, rubric, scoring, or
human-reserved decisions.

## Component Registry routing authority

Every invocation selects one closed routing-authority mode explicitly. The
script never infers the mode from a path, environment value, registry status,
or nearby repository:

- `repository-validation` derives the repository-validation path authority
  from the running script's canonical repository root. It validates candidate
  or tracked-active configuration without owner-local access. A candidate
  result is `proposed_revision_validation`; a tracked-active result is
  `adopted_configuration_validation`. Both are nonauthoritative and
  nonexecutable.
- `production-canonical` constructs the fixed production path authority
  internally and requires the running script's repository root to be the
  canonical checkout. An active result is valid only as
  `live_authority_validation` after the fixed activation readback succeeds.
- `production-transaction` derives the repository root from the running
  script and accepts only the run-root identity needed by the fixed
  worktree/run-pair validator. It cannot redefine the production state root,
  registry path, or activation-readback source.

Fixture injection is available only through contained Python test
authorities; it is not a production command-line mode. No invocation accepts
a caller-selected repository root, state root, registry authority path,
activation-readback path, or activation-readback payload.

The typed JSON report includes a closed authority envelope containing
`authority_mode`, `validation_mode`,
`registry_revision`, `registry_sha256`, `configuration_valid`,
`live_authority_verified`, `authoritative`, `executable`,
`predecessor_route_consulted`, and `activation_receipt_consulted`.
Repository and CI checks may accept configuration validity only. Production
callers must require the exact authoritative, executable
`live_authority_validation` mode. Missing or incompatible authority evidence
is a fatal validation failure and remains fatal when ordinary findings are
otherwise configured for an exit-zero report.

GitHub Actions validates repository configuration only. It has no
owner-local access and cannot claim that live activation was verified.

While the Component Registry remains a candidate, repository validation
preserves the exact predecessor-source read, digest, and parity checks. For a
tracked active configuration or live active routing, the bot consumes only
the embedded Component Registry route. It continues validating front matter,
module identity, dependencies, pinned and runtime currentness, required-floor
order, governing coverage, and comprehensive-review membership for every
current routed document. Archived predecessor records are validated only as
typed historical provenance; active validation never opens or hashes either
the original or archived predecessor and never includes either in the current
governing-document set.

P6 enables this role only as a coordinator-owned local stage. The stage itself
has no branch, commit, pull-request, data-projection, credential-provisioning,
or hosted-mutation authority.
