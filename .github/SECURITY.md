---
title: "Security Policy"
print_status: excluded
print_exclusion_reason: "GitHub repository security-reporting policy."
---

# Security Policy

ARRP welcomes responsible reports of vulnerabilities that could compromise the project, its contributors, its infrastructure, or its public services.

## Supported Scope

Security support covers the current `main` branch and the project-operated production services derived from it, including:

- the GitHub Pages publication;
- the public-input and private-author-contact service;
- GitHub Actions workflows and ARRP bot automation; and
- ARRP-operated GitHub App, deployment, and email integrations.

Historical commits, abandoned branches, local prototypes, and third-party forks are not independently supported. A vulnerability in one of those materials remains in scope if it also affects the current project or production services.

## Report a Vulnerability Privately

Use [GitHub private vulnerability reporting](https://github.com/Thorncrag/ARRP/security/advisories/new) to submit a report.

Do **not** disclose vulnerability details through a public GitHub issue, pull request, Discussion, public-input submission, or private-author-contact form. If GitHub private vulnerability reporting is unavailable, open a public issue containing no vulnerability details and ask the maintainer to establish a private channel.

Please include, when available:

- the affected URL, file, workflow, integration, or component;
- a concise description of the vulnerability and potential impact;
- reproducible steps or a minimal proof of concept;
- relevant logs or screenshots with secrets and personal information removed; and
- any known conditions that limit or amplify the risk.

ARRP will acknowledge and assess reports as promptly as reasonably practicable, may request additional information, and will coordinate remediation and disclosure according to the risk. ARRP does not currently operate a paid bug-bounty program.

## Responsible Testing Boundaries

Use only accounts, submissions, and data you control. Do not:

- access, retain, alter, or disclose another person's data;
- use discovered credentials or attempt to expand access;
- perform denial-of-service, high-volume automated scanning, spam, or service-degradation testing;
- use social engineering or target project contributors or service providers; or
- continue testing after encountering sensitive information or evidence of unintended access.

Stop testing and report immediately if sensitive data, credentials, or access to another person's information is encountered. Provide the minimum evidence needed to reproduce the problem and do not publish vulnerability details before remediation has been coordinated.

## Operational Controls

The public interaction service's implementation and operational safeguards are documented separately in [`participate/SECURITY.md`](../participate/SECURITY.md). That checklist is not a vulnerability-reporting channel.
