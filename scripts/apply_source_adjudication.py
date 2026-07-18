#!/usr/bin/env python3
"""Apply a validated ARRP source-adjudication decision batch.

The decision file is intentionally explicit. The script enforces canonical URL
identity, source-ID allocation, route association merging, queue reconciliation,
and all-or-nothing validation before writing project files.
"""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path

from source_adjudication_common import (
    merge_routes,
    normalize_url,
    read_csv,
    split_routes,
    write_csv,
    write_csv_preserving_unchanged,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research" / "trump-administration-legal-review-catalog.csv"
ROUTING = ROOT / "research" / "trump-administration-evidence-routing.csv"
PRIORITY = ROOT / "research" / "trump-administration-priority-disposition-review.csv"
CITED_SOURCES = ROOT / "inventory" / "sources.csv"
PENDING_SOURCES = ROOT / "inventory" / "sources-pending.csv"
EXISTING_ISSUE_QUEUE = ROOT / "research" / "existing-issue-evidence-integration.csv"

ALLOWED_DISPOSITIONS = {
    "anchor-evidence",
    "supporting-evidence",
    "corroborating-source",
    "comparator-or-counterexample",
    "monitoring-item",
    "different-existing-proposal",
    "preliminary-horizon-candidate",
    "political-failure-or-outside-scope",
    "redundant-without-additional-value",
    "insufficiently-verified",
    "unresolved-legal-question",
}

UNRESOLVED_DISPOSITIONS = {
    "preliminary-horizon-candidate",
    "insufficiently-verified",
    "unresolved-legal-question",
}

RETAINED_EVIDENCE_DISPOSITIONS = {
    "anchor-evidence",
    "supporting-evidence",
    "corroborating-source",
    "comparator-or-counterexample",
    "monitoring-item",
    "different-existing-proposal",
}

NO_ADDITIONAL_VALUE_DISPOSITIONS = {"corroborating-source"}


def validate_integration_targets(
    decision: dict[str, object], existing_issue_queue_ids: set[str]
) -> None:
    """Prevent source-inventory registration from masquerading as integration."""
    if decision.get("disposition") not in RETAINED_EVIDENCE_DISPOSITIONS:
        return
    raw_targets = decision.get("integration_targets", [])
    if isinstance(raw_targets, str):
        targets = [raw_targets]
    else:
        targets = [str(target) for target in raw_targets]
    targets = [target.strip() for target in targets if target.strip()]
    if not targets:
        no_additional_value = decision.get("reader_facing_value") == "no-additional-value"
        rationale = str(decision.get("no_additional_value_rationale", "")).strip()
        if (
            decision.get("disposition") in NO_ADDITIONAL_VALUE_DISPOSITIONS
            and no_additional_value
            and rationale
        ):
            return
        raise SystemExit(
            "Every retained-evidence decision requires an issue, evidence-record, "
            "monitoring, or queue target unless cumulative corroboration has an "
            "explicit no-additional-reader-value finding and rationale; a source-inventory "
            "association alone is not completed integration."
        )

    queue_target = EXISTING_ISSUE_QUEUE.relative_to(ROOT).as_posix()
    for target in targets:
        if target == queue_target:
            missing = set(decision.get("catalog_ids", [])) - existing_issue_queue_ids
            if missing:
                raise SystemExit(
                    "Existing-issue queue target is missing catalog records: "
                    + ", ".join(sorted(missing))
                )
            continue
        destination = ROOT / target
        if not destination.is_file():
            raise SystemExit(f"Integration target does not exist: {target}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("decisions", type=Path)
    parser.add_argument("--apply", action="store_true", help="write validated changes; default is dry-run")
    return parser.parse_args()


def next_source_number(rows: list[dict[str, str]]) -> int:
    numbers = []
    for row in rows:
        match = re.fullmatch(r"SRC-(\d+)", row["Source ID"])
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers, default=0) + 1


def main() -> None:
    args = parse_args()
    decisions_path = args.decisions if args.decisions.is_absolute() else ROOT / args.decisions
    payload = json.loads(decisions_path.read_text(encoding="utf-8"))
    decisions = payload.get("decisions", [])
    if not decisions:
        raise SystemExit("Decision file contains no decisions.")

    catalog = read_csv(CATALOG)
    routing = read_csv(ROUTING)
    priority = read_csv(PRIORITY)
    cited_sources = read_csv(CITED_SOURCES)
    pending_sources = read_csv(PENDING_SOURCES)
    existing_issue_queue = read_csv(EXISTING_ISSUE_QUEUE)
    existing_issue_queue_ids = {row["catalog_id"] for row in existing_issue_queue}
    original_ids = {row["catalog_id"] for row in catalog}
    routing_ids = {row["catalog_id"] for row in routing}
    if original_ids != routing_ids:
        raise SystemExit("Catalog and routing queues are not in one-to-one reconciliation.")

    decided_ids: list[str] = []
    resolved_ids: list[str] = []
    for decision in decisions:
        disposition = decision.get("disposition", "")
        if disposition not in ALLOWED_DISPOSITIONS:
            raise SystemExit(f"Invalid disposition: {disposition!r}")
        ids = decision.get("catalog_ids", [])
        if not ids:
            raise SystemExit("Every decision requires at least one catalog_id.")
        for catalog_id in ids:
            if catalog_id not in original_ids:
                raise SystemExit(f"Decision references missing catalog record: {catalog_id}")
            if catalog_id in decided_ids:
                raise SystemExit(f"Catalog record appears in more than one decision: {catalog_id}")
            decided_ids.append(catalog_id)
            if disposition not in UNRESOLVED_DISPOSITIONS:
                resolved_ids.append(catalog_id)
        if decision.get("material_issue_change"):
            raise SystemExit("Material issue changes require separate user approval and cannot be applied by this script.")
        validate_integration_targets(decision, existing_issue_queue_ids)

    new_cited_sources = deepcopy(cited_sources)
    new_pending_sources = deepcopy(pending_sources)
    by_url = {
        normalize_url(row["URL"]): row
        for row in [*new_cited_sources, *new_pending_sources]
        if normalize_url(row["URL"])
    }
    next_id = next_source_number([*new_cited_sources, *new_pending_sources])
    added = 0
    updated = 0
    touched_existing: set[str] = set()
    for decision in decisions:
        routes = merge_routes(
            [decision.get("primary_route", "")],
            decision.get("additional_routes", []),
        )
        for source in decision.get("sources", []):
            normalized = normalize_url(source.get("URL", ""))
            if not normalized:
                raise SystemExit("Every retained source requires a valid URL.")
            existing = by_url.get(normalized)
            if existing:
                merged = merge_routes(split_routes(existing["Associated Record IDs"]), routes)
                existing["Associated Record IDs"] = "; ".join(merged)
                if source.get("Reviewed?") == "Yes":
                    existing["Reviewed?"] = "Yes"
                source_id = existing["Source ID"]
                if source_id not in touched_existing:
                    updated += 1
                    touched_existing.add(source_id)
                continue
            required = [
                "Source Type",
                "Authority / Publisher",
                "Title or Description",
                "Date",
                "URL",
                "Proposition Supported",
                "Reliability Tier",
                "Reviewed?",
                "Notes",
            ]
            missing = [field for field in required if not source.get(field, "").strip()]
            if missing:
                raise SystemExit(f"New source is missing required fields: {', '.join(missing)}")
            row = {
                "Source ID": f"SRC-{next_id:04d}",
                "Associated Record IDs": "; ".join(routes),
                **{field: source[field].strip() for field in required},
            }
            next_id += 1
            added += 1
            new_pending_sources.append(row)
            by_url[normalized] = row

    resolved = set(resolved_ids)
    remaining_catalog = [row for row in catalog if row["catalog_id"] not in resolved]
    remaining_routing = [row for row in routing if row["catalog_id"] not in resolved]
    remaining_priority = [row for row in priority if row["catalog_id"] not in resolved]
    if len(remaining_catalog) + len(resolved) != len(catalog):
        raise SystemExit("Catalog batch reconciliation failed.")
    if {row["catalog_id"] for row in remaining_catalog} != {row["catalog_id"] for row in remaining_routing}:
        raise SystemExit("Post-batch catalog and routing queues would diverge.")

    print(
        f"Validated {len(decided_ids):,} decisions: {len(resolved):,} resolved records, "
        f"{len(decided_ids) - len(resolved):,} unresolved records retained, {added:,} pending sources added, "
        f"{updated:,} existing source rows updated, {len(remaining_catalog):,} intake rows remain."
    )
    if not args.apply:
        print("Dry run only; pass --apply to write files.")
        return

    write_csv_preserving_unchanged(
        CITED_SOURCES,
        cited_sources,
        new_cited_sources,
        list(cited_sources[0]),
        key_field="Source ID",
    )
    write_csv_preserving_unchanged(
        PENDING_SOURCES,
        pending_sources,
        new_pending_sources,
        list(pending_sources[0]),
        key_field="Source ID",
    )
    write_csv(CATALOG, remaining_catalog, list(catalog[0]))
    write_csv(ROUTING, remaining_routing, list(routing[0]))
    write_csv(PRIORITY, remaining_priority, list(priority[0]))
    print("Applied source adjudication and removed resolved records from temporary queues.")


if __name__ == "__main__":
    main()
