---
title: "GitHub Workflow"
---

# GitHub Workflow

GitHub is the project's authoritative workflow record. Active proposals, horizon proposals, release blockers, publication tasks, and contributor-facing suggestions should be visible as GitHub Issues and, where useful, on the project board.

The repository remains the authoritative substantive record. Proposal text, audit history, inventories, source records, proposed legislation, and framework rules belong in repo files and should be changed through normal repository edits or pull requests.

## Tracking Rule

Each active ARRP proposal or active horizon item should have a GitHub issue. The GitHub issue tracks discussion, status, labels, assignment, project-board placement, and release workflow. The canonical repo file records the adopted substance.

Milestones should not be assigned automatically to every proposal. A milestone means the issue is an obligation for that release phase. Proposal and horizon issues may remain unmilestoned until they are pulled into a specific release path.

## Labels

Use labels as filtering metadata:

- `kind:*` labels identify the type of issue.
- `area:*` labels identify the ARRP area.
- `stage:*` labels identify the proposal's repo-development stage.
- `status:*` labels identify the current workflow need.
- `priority:*` labels mirror the repo inventory priority.
- `release:*` labels identify release relationship or release-blocking status.

## Import Ledger

The current proposal-to-GitHub migration ledger is maintained at [`inventory/github_issue_import.csv`](../inventory/github_issue_import.csv). Rows marked `created` have a GitHub issue URL. Rows marked `pending` still need individual GitHub tracking issues created.
