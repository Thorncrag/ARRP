---
title: "Inventory Maintenance Method"
status: active
---

# Inventory Maintenance Method

## Purpose

Maintain the project's living inventory of institutional areas and issues before and during substantive development.

This file is limited to inventory maintenance. The canonical drafting method, issue architecture, source standard, Issue Snapshot format, Proposal Survey requirement, remedy standard, and cross-reference rules are maintained in [`../framework/FRAMEWORK.md`](../framework/FRAMEWORK.md).

## Inventory Files

The structured inventory is maintained in:

- [`areas.csv`](areas.csv) — project areas, generalized institutional concerns, status, issue counts, and notes.
- [`issues.csv`](issues.csv) — issue identifiers, area ownership, priority, and development status.
- [`contents.csv`](contents.csv) — combined area-and-issue navigation index for table-of-contents planning.
- [`sources.csv`](sources.csv) — source-tracking records.

## Inventory Rules

1. Each substantive issue should have a stable issue identifier, such as `DOJ-001`.
2. Each issue should have one primary area home.
3. Candidate issues may remain inventory-only until they receive a developed issue page.
4. Retired or merged issues should remain traceable in the inventory rather than disappearing silently.
5. Area issue counts should be updated when issues are added, retired, merged, or moved.
6. Development status should use consistent labels, such as `Candidate`, `Developed`, `Awaiting merits adjudication`, or `Retired—merged into ...`.
7. Inventory updates should be made in the same change as the substantive project update that requires them.

## Project-Update Checklist

When updating the project, check whether the change requires inventory maintenance:

1. If an area is added, renamed, retired, or materially reframed, update [`areas.csv`](areas.csv) and [`contents.csv`](contents.csv).
2. If an issue is added, renamed, promoted, retired, merged, moved, or given a new development status, update [`issues.csv`](issues.csv), [`contents.csv`](contents.csv), and the relevant area README.
3. If proposed legislation is added, renamed, or removed, update the `Legislation Path` field in [`contents.csv`](contents.csv).
4. If an external source is newly cited, removed, or used for a materially different proposition, update [`sources.csv`](sources.csv).
5. If source review is completed, update `Reviewed?`, `Proposition Supported`, and any notes in [`sources.csv`](sources.csv).
6. If issue counts change, update both the area README front matter and [`areas.csv`](areas.csv).

## Contents Index Rules

`contents.csv` may combine areas and issues because its purpose is navigation, ordering, and eventual table-of-contents development.

The normalized `areas.csv` and `issues.csv` files should remain available for compact tracking, but the combined contents index should include relative links to the area page, issue page, and proposed legislation where those files exist.

## Source Inventory Rules

`sources.csv` should capture distinct external sources already cited in the project. A row may be associated with an issue, area, framework file, research file, or project-level page.

Source rows may be captured before full verification. Use the `Reviewed?` field to distinguish a captured source from a source that has been checked against the proposition it is being used to support.

## Adding or Promoting Issues

Before adding or promoting a candidate into a standalone issue, apply the issue-admission test in [`../framework/FRAMEWORK.md`](../framework/FRAMEWORK.md).

If a candidate is duplicative, keep it as a manifestation, example, cross-reference, or research note rather than creating a separate issue.

## Links to Developed Work

When an issue becomes developed, maintain consistency among:

- the issue row in [`issues.csv`](issues.csv);
- the area README entry;
- the issue page under the relevant area directory;
- any proposed legislation under [`../legislation/`](../legislation/); and
- any source-development or research notes that remain relevant.

## Cross-References

Inventory entries should not duplicate developed analysis. Where a related issue is developed elsewhere, cross-reference the primary area or issue instead of repeating the same diagnosis, evidence, or remedy.
