#!/usr/bin/env python3
"""Append one privacy-minimized completed Elim intake assessment."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


COMPLETED = {"completed", "clean", "human_review"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_record(queue: dict, result: dict) -> dict:
    if result.get("work_type") != "public_intake" or result.get("outcome") not in COMPLETED:
        raise ValueError("only a completed public-intake assessment may enter the review ledger")
    unit = str(result.get("unit_id") or "")
    item = next((item for item in queue.get("items", []) if item.get("id") == unit), None)
    if not item or item.get("kind") != "public_intake":
        raise ValueError("work-unit result does not match a queued public-intake item")
    submission = (item.get("source") or {}).get("submission") or {}
    required = ("id", "url", "content_hash")
    if any(not submission.get(key) for key in required):
        raise ValueError("queued intake item lacks minimized submission provenance")
    return {
        "schema_version": 1,
        "submission_url": submission["url"],
        "submission_id": submission["id"],
        "content_hash": submission["content_hash"],
        "reviewed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "run_id": result["run_id"],
        "unit_id": unit,
        "disposition_category": result["outcome"],
        "action_ledger_reference": None,
        "content_included": False,
    }


def append(path: Path, record: dict) -> bool:
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            prior = json.loads(line)
            if (
                prior.get("submission_id") == record["submission_id"]
                and prior.get("content_hash") == record["content_hash"]
            ):
                return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument(
        "--ledger",
        type=Path,
        default=Path("research/intake-review-ledger.jsonl"),
    )
    args = parser.parse_args()
    record = build_record(load(args.queue), load(args.result))
    changed = append(args.ledger, record)
    print(json.dumps({"recorded": changed, "submission_id": record["submission_id"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"intake-review-ledger: {exc}")
