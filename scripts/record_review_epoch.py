#!/usr/bin/env python3
"""Validate and persist one completed comprehensive-review epoch."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REQUIRED = {
    "epoch_id",
    "triggering_run_id",
    "baseline_commit",
    "completion_commit",
    "governing_hashes",
    "reviewed_domains",
    "unresolved_findings",
    "sampling_record",
    "completed_at",
    "next_due_at",
    "cadence_status",
    "stability_status",
    "triggering_reason",
}
CADENCE = {"biweekly", "monthly", "event-triggered"}
STABILITY = {"evolving", "stable", "drift-detected"}


def validate(value: dict) -> dict:
    if set(value) != REQUIRED:
        raise ValueError(
            f"review epoch fields differ; missing={sorted(REQUIRED-set(value))}, "
            f"extra={sorted(set(value)-REQUIRED)}"
        )
    for key in ("epoch_id", "triggering_run_id", "baseline_commit", "completion_commit", "triggering_reason"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(f"{key} must be a nonblank string")
    if value["cadence_status"] not in CADENCE or value["stability_status"] not in STABILITY:
        raise ValueError("review epoch cadence or stability status is invalid")
    hashes = value["governing_hashes"]
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("governing_hashes must be a nonempty object")
    for path, digest in hashes.items():
        if not isinstance(path, str) or not isinstance(digest, str) or not digest.startswith("sha256:"):
            raise ValueError("governing hash entries require path and sha256 digest")
    for key in ("reviewed_domains", "unresolved_findings", "sampling_record"):
        if not isinstance(value[key], list):
            raise ValueError(f"{key} must be an array")
    completed = datetime.fromisoformat(value["completed_at"].replace("Z", "+00:00"))
    due = datetime.fromisoformat(value["next_due_at"].replace("Z", "+00:00"))
    if due <= completed:
        raise ValueError("next_due_at must follow completed_at")
    return {"schema_version": 1, **value}


def append(ledger: Path, current: Path, record: dict) -> bool:
    if ledger.is_file():
        rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
        if any(row.get("epoch_id") == record["epoch_id"] for row in rows):
            return False
    digest = hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    record = {**record, "record_sha256": "sha256:" + digest}
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    current.parent.mkdir(parents=True, exist_ok=True)
    current.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--ledger", type=Path, default=Path("research/review-epochs.jsonl")
    )
    parser.add_argument(
        "--current", type=Path, default=Path(".tmp/run-coordinator/review-epoch.json")
    )
    args = parser.parse_args()
    record = validate(json.loads(args.input.read_text()))
    changed = append(args.ledger, args.current, record)
    print(json.dumps({"recorded": changed, "epoch_id": record["epoch_id"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"review-epoch: {exc}")
