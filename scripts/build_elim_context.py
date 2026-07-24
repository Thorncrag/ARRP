#!/usr/bin/env python3
"""Emit a bounded, hash-pinned ARRP context packet for one Elim work profile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from arrp_context import ContextError, ROOT, build_context_packet, manifest_hash_updates


DEFAULT_MANIFEST = ROOT / "framework" / "agents" / "elim-context-routes.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--profile")
    parser.add_argument("--issue")
    parser.add_argument("--review-epoch", type=Path)
    parser.add_argument("--max-total-bytes", type=int)
    parser.add_argument(
        "--print-hash-updates",
        action="store_true",
        help="Print document hashes for human-reviewed manifest integration; do not build context.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.print_hash_updates:
            value = {
                "schema_version": 1,
                "manifest": str(args.manifest),
                "document_hashes": manifest_hash_updates(args.manifest),
            }
        else:
            if not args.profile:
                raise ContextError("--profile is required unless --print-hash-updates is used")
            value = build_context_packet(
                args.manifest,
                args.profile,
                issue_id=args.issue,
                review_epoch_path=args.review_epoch,
                max_total_bytes=args.max_total_bytes,
            )
        json.dump(value, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0
    except ContextError as exc:
        json.dump({"schema_version": 1, "status": "blocked", "error": str(exc)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
