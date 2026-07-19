#!/usr/bin/env python3
"""Apply a validated ARRP source-adjudication decision batch.

The decision file is intentionally explicit. The script enforces canonical URL
identity, source-ID allocation, route association merging, queue reconciliation,
and all-or-nothing validation before writing project files.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from copy import deepcopy
from datetime import date
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
CANDIDATES = ROOT / "research" / "trump-administration-preliminary-candidates.csv"
CITED_SOURCES = ROOT / "inventory" / "sources.csv"
PENDING_SOURCES = ROOT / "inventory" / "sources-pending.csv"
EXISTING_ISSUE_QUEUE = ROOT / "research" / "existing-issue-evidence-integration.csv"
MONITORING_LEDGER = ROOT / "research" / "trump-administration-litigation-monitoring.csv"
GITHUB_REGISTRY = ROOT / "inventory" / "github_issue_registry.csv"

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
}

UNRESOLVED_DISPOSITIONS = {
    "preliminary-horizon-candidate",
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

ALLOWED_PENDING_SOURCE_ACTIONS = {
    "move-to-cited",
    "monitor",
    "reroute",
    "remove",
    "new-preliminary-candidate",
}

CANDIDATE_FIELDS = [
    "candidate_id",
    "horizon_id",
    "title",
    "term",
    "proposed_area",
    "institutional_defect",
    "distinctness_rationale",
    "existing_coverage_considered",
    "counterargument",
    "unresolved_questions",
    "recommendation",
    "source_record_ids",
    "source_links",
    "review_status",
    "last_reviewed",
]

CANDIDATE_REQUIRED_FIELDS = [
    "title",
    "term",
    "proposed_area",
    "institutional_defect",
    "distinctness_rationale",
    "existing_coverage_considered",
    "counterargument",
    "unresolved_questions",
    "recommendation",
]


def candidate_identity(value: str) -> str:
    """Return a conservative identity key for preliminary-candidate clustering."""
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def historical_candidate_ids(root: Path = ROOT) -> set[str]:
    """Return preliminary IDs retained in durable project records.

    Resolved preliminary rows deliberately leave the active queue, but their
    identifiers remain in Horizon and issue provenance. Do not reuse those IDs.
    """
    identifiers: set[str] = set()
    for relative_root in ("areas", "framework", "inventory", "research", "topics"):
        base = root / relative_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".csv", ".md"}:
                continue
            identifiers.update(re.findall(r"\bINTAKE-GAP-\d+\b", path.read_text(encoding="utf-8", errors="replace")))
    return identifiers


def next_candidate_number(
    rows: list[dict[str, str]], reserved_candidate_ids: set[str] | None = None
) -> int:
    numbers = []
    identifiers = [row["candidate_id"] for row in rows]
    identifiers.extend(sorted(reserved_candidate_ids or set()))
    for candidate_id in identifiers:
        match = re.fullmatch(r"INTAKE-GAP-(\d+)", candidate_id)
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers, default=0) + 1


def upsert_preliminary_candidate(
    rows: list[dict[str, str]],
    decision: dict[str, object],
    reserved_candidate_ids: set[str] | None = None,
) -> tuple[str, dict[str, str]]:
    """Create or update one clustered preliminary candidate from an adjudication decision."""
    payload = decision.get("candidate")
    if not isinstance(payload, dict):
        raise SystemExit(
            "A preliminary-horizon-candidate disposition requires a candidate object."
        )
    missing = [
        field
        for field in CANDIDATE_REQUIRED_FIELDS
        if not str(payload.get(field, "")).strip()
    ]
    if missing:
        raise SystemExit(
            "Preliminary candidate is missing required fields: " + ", ".join(missing)
        )

    requested_id = str(payload.get("candidate_id", "")).strip()
    title_key = candidate_identity(str(payload["title"]))
    by_id = {row["candidate_id"]: row for row in rows}
    title_matches = [
        row for row in rows
        if row["review_status"] == "preliminary-candidate"
        and candidate_identity(row["title"]) == title_key
    ]
    if requested_id:
        if requested_id not in by_id:
            raise SystemExit(f"Candidate ID does not exist: {requested_id}")
        row = by_id[requested_id]
    elif len(title_matches) == 1:
        row = title_matches[0]
    elif len(title_matches) > 1:
        raise SystemExit(
            "Multiple active candidates share this normalized title; provide candidate_id explicitly."
        )
    else:
        candidate_id = f"INTAKE-GAP-{next_candidate_number(rows, reserved_candidate_ids):03d}"
        row = {field: "" for field in CANDIDATE_FIELDS}
        row["candidate_id"] = candidate_id
        rows.append(row)

    for field in CANDIDATE_REQUIRED_FIELDS:
        row[field] = str(payload[field]).strip()
    row["horizon_id"] = ""
    row["review_status"] = "preliminary-candidate"
    row["last_reviewed"] = (
        str(payload.get("last_reviewed", "")).strip()
        or row["last_reviewed"]
        or date.today().isoformat()
    )
    row["source_links"] = str(payload.get("source_links", row["source_links"])).strip()
    return row["candidate_id"], row


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
    if decision.get("disposition") == "monitoring-item":
        validate_monitoring_owner(
            decision,
            targets,
            read_csv(MONITORING_LEDGER),
            {row["Object ID"] for row in read_csv(GITHUB_REGISTRY) if row["Object ID"]},
        )
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


def validate_monitoring_owner(
    decision: dict[str, object],
    targets: list[str],
    monitoring_rows: list[dict[str, str]],
    registry_object_ids: set[str],
) -> None:
    """Require a defined-predicate GitHub owner before resolving monitoring intake."""
    monitoring_target = MONITORING_LEDGER.relative_to(ROOT).as_posix()
    if monitoring_target not in targets:
        raise SystemExit(
            "A monitoring-item disposition must target the canonical source-and-posture ledger."
        )

    additional_routes = decision.get("additional_routes", [])
    if isinstance(additional_routes, str):
        additional_routes = [additional_routes]
    routes = merge_routes(
        [str(decision.get("primary_route", ""))],
        [str(route) for route in additional_routes],
    )
    analytic_routes: set[str] = set()
    expected_monitor_ids: set[str] = set()
    for route in routes:
        if re.fullmatch(r"HOR-\d{3}", route):
            analytic_routes.add(route)
            expected_monitor_ids.add(route)
        elif re.fullmatch(r"[A-Z]+-\d{3}-MON", route):
            analytic_routes.add(route.removesuffix("-MON"))
            expected_monitor_ids.add(route)
        elif re.fullmatch(r"[A-Z]+-\d{3}", route):
            analytic_routes.add(route)
            expected_monitor_ids.add(f"{route}-MON")
    if not expected_monitor_ids or not expected_monitor_ids.intersection(registry_object_ids):
        raise SystemExit(
            "A monitoring-item disposition requires an established ISSUE-ID-MON record "
            "or a formal Horizon candidate in the GitHub issue registry."
        )

    for catalog_id in decision.get("catalog_ids", []):
        matches = [
            row
            for row in monitoring_rows
            if catalog_id in split_routes(row.get("catalog_ids", ""))
            and analytic_routes.intersection(split_routes(row.get("integration_routes", "")))
            and row.get("revisit_trigger", "").strip()
            and row.get("monitoring_status", "").startswith("active")
        ]
        if not matches:
            raise SystemExit(
                f"Monitoring source {catalog_id} lacks an active source-and-posture row "
                "with the selected owner and a defined revisit predicate."
            )


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


def csv_fieldnames(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def apply_pending_source_decisions(
    decisions: list[dict[str, object]],
    cited_sources: list[dict[str, str]],
    pending_sources: list[dict[str, str]],
    require_empty: bool,
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, int]]:
    """Graduate or remove already-cataloged pending sources after qualitative review."""
    pending_by_id = {row["Source ID"]: row for row in pending_sources}
    if len(pending_by_id) != len(pending_sources):
        raise SystemExit("Pending source IDs are not unique.")
    cited_ids = {row["Source ID"] for row in cited_sources}
    if cited_ids.intersection(pending_by_id):
        raise SystemExit("A source ID appears in both cited and pending catalogs.")

    decided: set[str] = set()
    moved_rows: list[dict[str, str]] = []
    removed = 0
    for decision in decisions:
        source_id = str(decision.get("source_id", "")).strip()
        action = str(decision.get("action", "")).strip()
        owner = str(decision.get("owner", "")).strip()
        target = str(decision.get("integration_target", "")).strip()
        rationale = str(decision.get("rationale", "")).strip()
        if not source_id or source_id not in pending_by_id:
            raise SystemExit(f"Pending-source decision references missing source: {source_id!r}")
        if source_id in decided:
            raise SystemExit(f"Pending source appears in more than one decision: {source_id}")
        if action not in ALLOWED_PENDING_SOURCE_ACTIONS:
            raise SystemExit(f"Invalid pending-source action for {source_id}: {action!r}")
        if not rationale:
            raise SystemExit(f"Pending-source decision lacks a rationale: {source_id}")
        if action == "new-preliminary-candidate":
            raise SystemExit(
                f"{source_id} requires candidate synthesis before pending-source graduation."
            )
        decided.add(source_id)
        if action == "remove":
            removed += 1
            continue
        if not owner or not target:
            raise SystemExit(
                f"Retained pending source requires an owner and integration target: {source_id}"
            )
        destination = ROOT / target
        if not destination.is_file():
            raise SystemExit(f"Pending-source integration target does not exist: {target}")
        row = deepcopy(pending_by_id[source_id])
        if action == "reroute":
            row["Associated Record IDs"] = "; ".join(split_routes(owner))
        else:
            row["Associated Record IDs"] = "; ".join(
                merge_routes(split_routes(row["Associated Record IDs"]), split_routes(owner))
            )
        for stale_prefix in (
            "Pending source record; not yet cited in ARRP prose. ",
            "Pending source record; not yet cited in repository Markdown or an authoritative GitHub issue. ",
        ):
            if row["Notes"].startswith(stale_prefix):
                row["Notes"] = row["Notes"][len(stale_prefix):]
        note = (
            f"Adjudicated {date.today().isoformat()}: {rationale} "
            f"Integrated through {target}."
        )
        if note not in row["Notes"]:
            row["Notes"] = f"{row['Notes'].rstrip()} {note}".strip()
        moved_rows.append(row)

    if require_empty and decided != set(pending_by_id):
        missing = sorted(set(pending_by_id) - decided)
        extra = sorted(decided - set(pending_by_id))
        detail = []
        if missing:
            detail.append(f"missing {len(missing)} source decisions")
        if extra:
            detail.append(f"unexpected {len(extra)} source decisions")
        raise SystemExit("Pending-source batch is incomplete: " + "; ".join(detail))

    remaining = [row for row in pending_sources if row["Source ID"] not in decided]
    graduated = [*cited_sources, *moved_rows]
    def source_id_key(row: dict[str, str]) -> tuple[int, int | str]:
        match = re.fullmatch(r"SRC-(\d+)", row["Source ID"])
        return (0, int(match.group(1))) if match else (1, row["Source ID"])

    graduated.sort(key=source_id_key)
    all_ids = [row["Source ID"] for row in [*graduated, *remaining]]
    if len(all_ids) != len(set(all_ids)):
        raise SystemExit("Source IDs would not remain globally unique after graduation.")
    existing_cited_urls = {
        normalize_url(row["URL"])
        for row in cited_sources
        if normalize_url(row["URL"])
    }
    moved_urls = [
        normalize_url(row["URL"])
        for row in moved_rows
        if normalize_url(row["URL"])
    ]
    if existing_cited_urls.intersection(moved_urls) or len(moved_urls) != len(set(moved_urls)):
        raise SystemExit("Pending-source graduation would introduce a normalized URL duplicate.")
    return graduated, remaining, {
        "decided": len(decided),
        "moved": len(moved_rows),
        "removed": removed,
    }


def main() -> None:
    args = parse_args()
    decisions_path = args.decisions if args.decisions.is_absolute() else ROOT / args.decisions
    payload = json.loads(decisions_path.read_text(encoding="utf-8"))
    decisions = payload.get("decisions", [])
    pending_source_decisions = list(payload.get("pending_source_decisions", []))
    for relative_path in payload.get("pending_source_decision_files", []):
        path = Path(str(relative_path))
        if not path.is_absolute():
            path = ROOT / path
        pending_source_decisions.extend(read_csv(path))
    if not decisions and not pending_source_decisions:
        raise SystemExit("Decision file contains no decisions.")

    catalog = read_csv(CATALOG)
    routing = read_csv(ROUTING)
    priority = read_csv(PRIORITY)
    candidates = read_csv(CANDIDATES)
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
    new_candidates = deepcopy(candidates)
    reserved_candidate_ids = historical_candidate_ids()
    candidate_rows_by_decision: dict[int, dict[str, str]] = {}
    candidate_ids_by_decision: dict[int, str] = {}
    for decision_index, decision in enumerate(decisions):
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
        if disposition == "preliminary-horizon-candidate":
            candidate_id, candidate_row = upsert_preliminary_candidate(
                new_candidates, decision, reserved_candidate_ids
            )
            reserved_candidate_ids.add(candidate_id)
            candidate_ids_by_decision[decision_index] = candidate_id
            candidate_rows_by_decision[decision_index] = candidate_row

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
    decision_source_ids: dict[int, list[str]] = {}
    for decision_index, decision in enumerate(decisions):
        routes = merge_routes(
            [decision.get("primary_route", "")],
            decision.get("additional_routes", []),
        )
        candidate_id = candidate_ids_by_decision.get(decision_index, "")
        if candidate_id:
            routes = merge_routes([candidate_id], routes)
        decision_source_ids[decision_index] = []
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
                if source_id not in decision_source_ids[decision_index]:
                    decision_source_ids[decision_index].append(source_id)
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
            decision_source_ids[decision_index].append(row["Source ID"])

    pending_result = {"decided": 0, "moved": 0, "removed": 0}
    if pending_source_decisions:
        new_cited_sources, new_pending_sources, pending_result = apply_pending_source_decisions(
            pending_source_decisions,
            new_cited_sources,
            new_pending_sources,
            bool(payload.get("require_empty_pending_sources")),
        )

    new_routing = deepcopy(routing)
    routing_by_id = {row["catalog_id"]: row for row in new_routing}
    for decision_index, candidate_row in candidate_rows_by_decision.items():
        decision = decisions[decision_index]
        candidate_id = candidate_ids_by_decision[decision_index]
        source_ids = merge_routes(
            split_routes(candidate_row["source_record_ids"]),
            decision_source_ids[decision_index],
        )
        candidate_row["source_record_ids"] = "; ".join(source_ids)
        source_links = [
            item.strip()
            for item in candidate_row["source_links"].split("||")
            if item.strip()
        ]
        for source in decision.get("sources", []):
            url = str(source.get("URL", "")).strip()
            if not url:
                continue
            label = str(source.get("Authority / Publisher", "Source")).strip() or "Source"
            link = f"{label}|{url}"
            if link not in source_links:
                source_links.append(link)
        candidate_row["source_links"] = " || ".join(source_links)
        if not candidate_row["source_record_ids"] and not candidate_row["source_links"]:
            raise SystemExit(
                f"Preliminary candidate {candidate_id} has no retained supporting source."
            )
        for catalog_id in decision["catalog_ids"]:
            route = routing_by_id[catalog_id]
            route["disposition"] = "preliminary-candidate-evidence"
            route["integration_routes"] = "; ".join(
                merge_routes([candidate_id], split_routes(route["integration_routes"]))
            )
            route["recommended_use"] = "Support preliminary-candidate review"
            route["review_status"] = "candidate-synthesized"
            route["candidate_id"] = candidate_id

    resolved = set(resolved_ids)
    remaining_catalog = [row for row in catalog if row["catalog_id"] not in resolved]
    remaining_routing = [row for row in new_routing if row["catalog_id"] not in resolved]
    remaining_priority = [row for row in priority if row["catalog_id"] not in resolved]
    if len(remaining_catalog) + len(resolved) != len(catalog):
        raise SystemExit("Catalog batch reconciliation failed.")
    if {row["catalog_id"] for row in remaining_catalog} != {row["catalog_id"] for row in remaining_routing}:
        raise SystemExit("Post-batch catalog and routing queues would diverge.")

    print(
        f"Validated {len(decided_ids):,} decisions: {len(resolved):,} resolved records, "
        f"{len(decided_ids) - len(resolved):,} unresolved records retained, {added:,} pending sources added, "
        f"{updated:,} existing source rows updated, {len(remaining_catalog):,} intake rows remain; "
        f"{pending_result['moved']:,} pending sources graduated and "
        f"{pending_result['removed']:,} removed."
    )
    if not args.apply:
        print("Dry run only; pass --apply to write files.")
        return

    write_csv_preserving_unchanged(
        CITED_SOURCES,
        cited_sources,
        new_cited_sources,
        csv_fieldnames(CITED_SOURCES),
        key_field="Source ID",
    )
    write_csv_preserving_unchanged(
        PENDING_SOURCES,
        pending_sources,
        new_pending_sources,
        csv_fieldnames(PENDING_SOURCES),
        key_field="Source ID",
    )
    write_csv(CATALOG, remaining_catalog, csv_fieldnames(CATALOG))
    write_csv(ROUTING, remaining_routing, csv_fieldnames(ROUTING))
    write_csv(PRIORITY, remaining_priority, csv_fieldnames(PRIORITY))
    write_csv(CANDIDATES, new_candidates, CANDIDATE_FIELDS)
    print("Applied source adjudication and removed resolved records from temporary queues.")


if __name__ == "__main__":
    main()
