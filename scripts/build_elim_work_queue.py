#!/usr/bin/env python3
"""Compile current deterministic ARRP feeds into a compact, read-only Elim work queue."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from arrp_context import ContextError, build_work_queue


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integrity", required=True, type=Path)
    parser.add_argument("--progress", required=True, type=Path)
    parser.add_argument("--intake", required=True, type=Path)
    parser.add_argument("--chain", required=True, type=Path)
    parser.add_argument("--recovery", type=Path)
    parser.add_argument("--review-epoch", type=Path)
    parser.add_argument("--max-age-hours", type=int, default=36)
    parser.add_argument("--as-of", help="ISO-8601 timestamp for deterministic tests")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        now = None
        if args.as_of:
            now = datetime.fromisoformat(args.as_of.replace("Z", "+00:00"))
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
        value = build_work_queue(
            integrity_path=args.integrity,
            progress_path=args.progress,
            intake_path=args.intake,
            chain_path=args.chain,
            recovery_path=args.recovery,
            review_epoch_path=args.review_epoch,
            now=now,
            max_age_hours=args.max_age_hours,
        )
        json.dump(value, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0 if value["ready_for_elim"] else 3
    except ContextError as exc:
        json.dump({"schema_version": 1, "status": "blocked", "error": str(exc)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
