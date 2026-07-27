#!/usr/bin/env python3
"""Emit a bounded, hash-pinned ARRP context packet for one Elim work profile."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from arrp_context import (
    ContextError,
    ROOT,
    build_context_packet,
    contained_path,
    manifest_hash_updates,
)


DEFAULT_MANIFEST = (
    ROOT / "framework" / "project" / "automation" / "context-routes.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=ROOT,
        help="Exact reviewed repository root used to build the packet.",
    )
    parser.add_argument(
        "--review-epoch-root",
        type=Path,
        help=(
            "Exact reviewed run root containing --review-epoch. Defaults to "
            "--input-root."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the packet atomically instead of emitting it on stdout.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help=(
            "Exact reviewed root containing --output. Defaults to --input-root."
        ),
    )
    parser.add_argument("--profile")
    parser.add_argument("--issue")
    parser.add_argument("--work-item-id")
    parser.add_argument("--work-kind")
    parser.add_argument("--canonical-record")
    parser.add_argument("--review-epoch", type=Path)
    parser.add_argument("--max-total-bytes", type=int)
    parser.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Add an independently triggered context capability and its dependency closure.",
    )
    parser.add_argument(
        "--print-hash-updates",
        action="store_true",
        help="Print document hashes for human-reviewed manifest integration; do not build context.",
    )
    return parser.parse_args()


def write_json(path: Path, value: object, root: Path) -> None:
    normalized_root = os.path.realpath(os.fspath(root))
    normalized_path = os.path.realpath(os.fspath(path))
    if (
        normalized_path != normalized_root
        and not normalized_path.startswith(normalized_root + os.sep)
    ):
        raise ContextError(f"path escapes allowed root: {path}")
    destination = Path(normalized_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=destination.parent,
        delete=False,
    ) as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(destination)


def emit(
    value: object,
    *,
    output: Path | None,
    output_root: Path,
) -> None:
    if output is not None:
        write_json(output, value, output_root)
        return
    json.dump(value, sys.stdout, indent=2, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")


def main() -> int:
    args = parse_args()
    try:
        if args.print_hash_updates:
            value = {
                "schema_version": 2,
                "manifest": str(args.manifest),
                "document_hashes": manifest_hash_updates(
                    args.manifest,
                    root=args.input_root,
                ),
            }
        else:
            if not args.profile:
                raise ContextError("--profile is required unless --print-hash-updates is used")
            value = build_context_packet(
                args.manifest,
                args.profile,
                root=args.input_root,
                issue_id=args.issue,
                review_epoch_path=args.review_epoch,
                review_epoch_root=args.review_epoch_root,
                max_total_bytes=args.max_total_bytes,
                capabilities=args.capability,
                work_item_id=args.work_item_id,
                work_kind=args.work_kind,
                canonical_record=args.canonical_record,
            )
        emit(
            value,
            output=args.output,
            output_root=args.output_root or args.input_root,
        )
        return 0
    except ContextError as exc:
        value = {"schema_version": 2, "status": "blocked", "error": str(exc)}
        try:
            emit(
                value,
                output=args.output,
                output_root=args.output_root or args.input_root,
            )
        except ContextError:
            json.dump(value, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
