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
from path_authority import (
    PathAuthorityError,
    ProjectPathAuthority,
)


DEFAULT_MANIFEST = (
    ROOT / "framework" / "project" / "automation" / "context-routes.json"
)


def _resolved_requested_root(
    requested: Path,
    expected: Path,
    label: str,
) -> Path:
    try:
        resolved = requested.expanduser().resolve(strict=True)
    except OSError as error:
        raise PathAuthorityError(f"{label} is unavailable") from error
    if resolved != expected:
        raise PathAuthorityError(f"{label} does not match its authority")
    return resolved


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
        "--path-authority",
        choices=(
            "production-canonical",
            "production-transaction",
            "fixture",
            "repository-validation",
        ),
        default="production-canonical",
        help="Explicit trust boundary for every repository and output path.",
    )
    parser.add_argument("--fixture-root", type=Path)
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
        help=(
            "Write the packet atomically as a direct child of --output-root "
            "instead of emitting it on stdout."
        ),
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
    normalized_path = os.path.realpath(
        os.path.join(normalized_root, os.fspath(path))
    )
    if (
        normalized_path != normalized_root
        and not normalized_path.startswith(normalized_root + os.sep)
    ):
        raise ContextError(f"path escapes allowed root: {path}")
    if os.path.dirname(normalized_path) != normalized_root:
        raise ContextError(f"path is not a direct child of allowed root: {path}")
    destination = Path(normalized_root) / os.path.basename(normalized_path)
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
        if args.path_authority == "production-canonical":
            if args.fixture_root is not None:
                raise PathAuthorityError(
                    "production authority does not accept a fixture root"
                )
            authority = ProjectPathAuthority.production()
            if args.input_root.resolve() != authority.repository_root:
                raise PathAuthorityError(
                    "production input root is not the approved repository"
                )
        elif args.path_authority == "production-transaction":
            if args.fixture_root is not None or args.output_root is None:
                raise PathAuthorityError(
                    "production transaction requires an exact run root"
                )
            authority = ProjectPathAuthority.production_transaction(
                repository_root=args.input_root,
                run_root=args.output_root,
            )
        elif args.path_authority == "fixture":
            if args.fixture_root is None:
                raise PathAuthorityError("fixture authority requires --fixture-root")
            authority = ProjectPathAuthority.fixture(
                args.fixture_root,
                repository_root=args.input_root,
                state_root=args.fixture_root,
                output_root=args.output_root or args.input_root,
            )
        else:
            if not args.print_hash_updates or args.fixture_root is not None:
                raise PathAuthorityError(
                    "repository validation is limited to hash inspection"
                )
            authority = ProjectPathAuthority.repository_validation(ROOT)
            if args.input_root.resolve() != authority.repository_root:
                raise PathAuthorityError(
                    "repository validation cannot select another checkout"
                )
        input_root = authority.repository_root
        manifest_path = authority.requested_repository_file(args.manifest)
        if args.review_epoch_root is not None:
            review_epoch_root = _resolved_requested_root(
                args.review_epoch_root,
                authority.output_root,
                "review epoch root",
            )
        else:
            review_epoch_root = authority.output_root
        output_root = authority.output_root
        if args.print_hash_updates:
            value = {
                "schema_version": 2,
                "manifest": str(manifest_path),
                "document_hashes": manifest_hash_updates(
                    manifest_path,
                    root=input_root,
                ),
            }
        else:
            if not args.profile:
                raise ContextError("--profile is required unless --print-hash-updates is used")
            value = build_context_packet(
                manifest_path,
                args.profile,
                root=input_root,
                issue_id=args.issue,
                review_epoch_path=args.review_epoch,
                review_epoch_root=review_epoch_root,
                max_total_bytes=args.max_total_bytes,
                capabilities=args.capability,
                work_item_id=args.work_item_id,
                work_kind=args.work_kind,
                canonical_record=args.canonical_record,
                path_authority=authority,
            )
        emit(
            value,
            output=args.output,
            output_root=output_root,
        )
        return 0
    except (ContextError, PathAuthorityError) as exc:
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
