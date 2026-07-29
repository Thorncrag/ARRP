---
title: "GitHub Disclosure Boundary"
module_id: github_disclosure_boundary
dependencies:
  - "../../FRAMEWORK.md"
  - "disclosure-policy.json"
print_status: excluded
print_exclusion_reason: "Online repository-governance summary."
---

# GitHub Disclosure Boundary

This document governs every ARRP-controlled transmission to GitHub. The
machine-readable category and artifact-family registry is
[`disclosure-policy.json`](disclosure-policy.json); the deterministic
enforcement module is the only project-operated authority for deciding whether
an exact outbound bundle may proceed. A generated `privacy_class: public`
value is advisory input, never proof.

## Category model

Every artifact must map deterministically to exactly one registered family by
producer, path rule, and artifact identity. Ordinary members of a known family
need no per-file label. A new or ambiguous family fails closed until a human
records its category. Exceptional public-safe overrides are exact,
revision-bound, centrally recorded, and never available for secrets.

The categories, from least to most restrictive, are:

1. `public_by_design` for approved public research, proposals, issues, source
   records, methodology, participation material, and release artifacts;
2. `public_operational_summary` for deliberately minimized public status and
   interface information;
3. `restricted_operational` for detailed automation, runtime, recovery,
   security, sensitive diagnostic, and materially revealing operational material;
4. `private` for correspondence, contact details, account-specific state, and
   owner-only records; and
5. `prohibited_secret` for usable credentials, secret fragments, and usable or
   recoverable derivatives.

The strictest applicable category controls. Unknown is never public.
Substantively controversial public-policy research is not restricted merely
because of its subject.

## Absolute secret rule

Credentials and secrets may not be ingested into a publishable artifact,
persisted in project output, rendered in the Console, logged, committed,
embedded in a URL, or transmitted through any GitHub surface. This includes
tokens, passwords, private keys, session material, authorization headers,
signed URLs, credential-bearing errors, fragments, and recoverable
derivatives. There is no approval exception.

Credential posture may be represented only through safe typed states and an
authorized remediation route. A blocked decision records an opaque finding
identifier, artifact family/path, detector class, and safe next action; it
never records matched text or an ordinary hash of matched material.

## Artifact-family and generated-output rule

A document, generated PDF, content-bearing generator or template, embedded
fixture, and content-bearing test are one artifact family when they carry the
same disclosure substance. Generated output inherits at least the strictest
source category and may be elevated when aggregation creates a more revealing
operational picture. Restricted or private originals require separately
reviewed sanitized derivatives; relabeling the original is insufficient.

The repository-visible Console bundle contains only allowlisted public-safe
projections. Complete runtime configuration, authenticated security state, and
detailed operational history remain in secret-scanned, Git-ignored owner-local
feeds and are not members of the public generation manifest.

## Public core and owner-local controls

The repository contains a portable, credential-free enforcement core:
category resolution, exact bundle and revision binding, conservative secret
checks, safe decision records, and the requirement for a compatible control
pack. Exact environment-specific detectors, operational topology, sensitive
signatures, and their complete adversarial fixtures are maintained in a
versioned owner-local control pack. The pack is not a GitHub artifact.

The public core validates the pack's schema, policy identity, completeness,
compatibility, status, and owner-local location before it can authorize an
outbound operation. A missing, unreadable, stale, incompatible, or unbound pack
fails closed. This separation permits public verification of the governing
invariant without publishing the sensitive controls used to enforce it.

Production authorization reads only the active pointer beneath the fixed
approved owner-local state root. A caller may select the proposed outbound
payload but may not select an authority root or substitute a control pack.
Candidate packs have a separate validation-only path: a successful candidate
check is nonauthoritative and cannot authorize any GitHub transmission.
Activation is an owner-approved atomic state change after the candidate,
public core, exact revision, and remote synchronization have been verified.
Fixtures are explicit, contained, nonoverlapping with production, and cannot
be selected through a production command or environment variable.

## Enforcement order and GitHub surfaces

The gate validates the complete exact content and source revision before every
project-operated Git push or GitHub API mutation and, where possible, before
credential access. It applies to branches and commits; pull requests, Issues,
Discussions, reviews, and comments; Project field text; workflow dispatch
payloads and generated Actions output; releases and assets; Pages; generated
PDFs; and every App, CLI, or API mutation.

GitHub-side checks are defense in depth because they run after transmission.
Repository code cannot make direct human credential use technically
impossible. The documented interactive workflow must invoke the same gate,
and every automated publisher or broker must fail closed when its decision is
missing, incomplete, stale, or bound to different content or revision.

Blocked local artifacts are preserved. A material prevented disclosure is
recorded as a sanitized near-miss Operational Incident; a confirmed disclosure
is an Operational Incident. Incident, Action Item, and Console projections
must never reproduce restricted evidence.

No ARRP-authored GitHub Issue, pull-request body, repository document, log,
audit record, Console-development entry, generated Console artifact, workflow
output, or other GitHub-hosted project record may contain a suspected or
confirmed vulnerability or actionable evidence about it. Affected paths or
components, rule identities, exploit conditions, raw evidence, credential
metadata, exact permission detail, detector configuration, and remediation
analysis remain owner-local or in GitHub's provider-native private Security
surfaces. Project records may retain only a safe typed posture, opaque
protected-action identity, and protected route. Unknown classification fails
closed rather than being copied for later review.

## Inventory and historical disclosure

The initial bounded classification inventory is represented by a minimized
public summary in
[`../../records/automation/disclosure-classification-summary-2026-07-28.json`](../../records/automation/disclosure-classification-summary-2026-07-28.json).
The complete path inventory is owner-local and does not grandfather restricted
material already present on GitHub.

`DISCLOSURE-HIST-001` records the removed agent-automation technical
specification family as the motivating prior disclosure. Its Markdown, PDF,
generator, and content-bearing tests are treated as one family. This record
does not authorize history rewriting, deletion, credential rotation,
repository-visibility changes, or other containment actions.
