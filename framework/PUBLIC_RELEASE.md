---
title: "Public Release Process"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Public Release Process

This project is not yet formally released for broad public reuse. The first public release should create a clear dated snapshot of the project for citation, provenance, review, and public engagement.

## Purpose of a Release

A release should:

1. identify the version of the project being made available for public review;
2. preserve a timestamped snapshot of authorship and project scope;
3. make citation and rights information easy to find;
4. distinguish public-review availability from any later public reuse license; and
5. summarize known limitations, drafting status, and next development priorities.

## Before the First Public Release

Before creating a public release, complete a final review of:

1. [`README.md`](../README.md), including About This Project, the topic-and-institution index route, rights notice, citation pointer, and project status;
2. [`LICENSE.md`](../LICENSE.md), including the all-rights-reserved status and planned future public reuse license note;
3. [`AUTHORS.md`](../AUTHORS.md), including the author-directed project statement;
4. [`CITATION.cff`](../CITATION.cff), including author, title, repository URL, abstract, and citation message;
5. source citations for named real-world events, public actors, legal materials, reports, and institutional examples;
6. Git history and author metadata;
7. repository settings for issues, discussions, pull requests, branch protection, and contributor permissions; and
8. any draft material that should remain private, be archived, or be revised before publication.

## Suggested First Release

Use a pre-release label until the project is ready for broader legislative engagement.

Suggested tag:

```text
v0.1-public-preview
```

Suggested release title:

```text
ARRP Public Preview v0.1
```

Suggested release notes:

```markdown
This is the first public-preview snapshot of the American Restoration and Resilience Project.

ARRP is an author-directed public-policy research and drafting project focused on institutional repair, democratic resilience, rule-of-law safeguards, and prevention of future personalist capture.

This release is made available for public reading, citation, review, and feedback. It is not legal advice, has not been reviewed by legislative counsel, and does not grant a public reuse license beyond the rights described in LICENSE.md. The project is planned to be released at a later date, in whole or in part, under a Creative Commons license or other public reuse license.

Known limitations:

- many candidate areas and issues remain under development;
- source development and citation review are ongoing;
- proposed legislation remains illustrative working draft language;
- issue classifications and remedies may change.
```

## Later Release-Licensing Decision

When the project is ready for broader legislative and public engagement, select and adopt an appropriate Creative Commons or other public reuse license, update [`LICENSE.md`](../LICENSE.md), update [`README.md`](../README.md), and create a new release that clearly identifies the first version available under that public reuse license.
