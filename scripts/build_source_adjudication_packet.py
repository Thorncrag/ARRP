#!/usr/bin/env python3
"""Build a route-centered packet for substantive ARRP source adjudication.

The packet is a temporary review artifact. It does not decide legal questions,
change proposal text, or mutate the canonical source inventory.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from source_adjudication_common import normalize_url, read_csv, source_urls, split_routes


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research" / "trump-administration-legal-review-catalog.csv"
ROUTING = ROOT / "research" / "trump-administration-evidence-routing.csv"
PRIORITY = ROOT / "research" / "trump-administration-priority-disposition-review.csv"
SOURCES = ROOT / "inventory" / "sources.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--priority-only", action="store_true")
    parser.add_argument("--route", action="append", default=[])
    parser.add_argument("--catalog-id", action="append", default=[])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    catalog = {row["catalog_id"]: row for row in read_csv(CATALOG)}
    routing = {row["catalog_id"]: row for row in read_csv(ROUTING)}
    priority = {row["catalog_id"]: row for row in read_csv(PRIORITY)}
    source_index: dict[str, list[str]] = defaultdict(list)
    for row in read_csv(SOURCES):
        key = normalize_url(row["URL"])
        if key:
            source_index[key].append(row["Source ID"])

    selected_ids = list(catalog)
    if args.priority_only:
        selected_ids = [catalog_id for catalog_id in selected_ids if catalog_id in priority]
    if args.catalog_id:
        requested = set(args.catalog_id)
        selected_ids = [catalog_id for catalog_id in selected_ids if catalog_id in requested]
    if args.route:
        requested_routes = set(args.route)
        selected_ids = [
            catalog_id
            for catalog_id in selected_ids
            if requested_routes.intersection(split_routes(routing[catalog_id]["integration_routes"]))
        ]

    route_packets: dict[str, list[dict[str, object]]] = defaultdict(list)
    for catalog_id in selected_ids:
        item = catalog[catalog_id]
        route = routing[catalog_id]
        urls = source_urls(item)
        for url in urls:
            url["existing_source_ids"] = source_index.get(url["normalized_url"], [])
        routes = split_routes(route["integration_routes"])
        primary_route = routes[0] if routes else "UNROUTED"
        route_packets[primary_route].append(
            {
                "catalog_id": catalog_id,
                "evidence_group": route["evidence_group"],
                "title": item["action_or_policy"],
                "term": item["term"],
                "record_type": item["record_type"],
                "source_family": item["source_family"],
                "source_urls": urls,
                "current_routes": routes,
                "recommended_use": route["recommended_use"],
                "route_review_basis": route["review_basis"],
                "legal_question_or_outcome": item["legal_question_or_outcome"],
                "litigation_posture": item["litigation_posture"],
                "priority_review": priority.get(catalog_id, {}),
            }
        )

    route_counts = Counter()
    packets = []
    for route_name in sorted(route_packets):
        records = route_packets[route_name]
        route_counts[route_name] = len(records)
        packets.append({"primary_route": route_name, "record_count": len(records), "records": records})
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "temporary": True,
        "record_count": len(selected_ids),
        "route_counts": dict(route_counts),
        "routes": packets,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {output}: {len(selected_ids):,} records in {len(packets):,} route packets.")


if __name__ == "__main__":
    main()
