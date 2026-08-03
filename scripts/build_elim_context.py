#!/usr/bin/env python3
"""Emit a bounded, hash-pinned ARRP context packet for one Elim work profile."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from arrp_context import (
    ContextError,
    ROOT,
    build_context_packet,
    contained_path,
    manifest_hash_updates,
)
from component_registry import (
    RegistryError,
    ROUTING_PREDECESSOR_PATHS,
    RoutingRuleFailure,
    build_context_packet_from_view,
    load_validated_component_registry_routing_view,
)
from path_authority import (
    PathAuthorityError,
    ProjectPathAuthority,
)


DEFAULT_MANIFEST = (
    ROOT
    / ROUTING_PREDECESSOR_PATHS["context_routes_source"]["historical_path"]
)


def _resolved_requested_root(
    requested: Path,
    expected: Path,
    label: str,
) -> Path:
    normalized_requested = os.path.normpath(
        os.path.abspath(os.path.expanduser(os.fspath(requested)))
    )
    normalized_expected = os.path.normpath(
        os.path.abspath(os.fspath(expected))
    )
    if normalized_requested != normalized_expected:
        raise PathAuthorityError(f"{label} does not match its authority")
    return expected


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        help=(
            "Fixture-only context route or nonexecuting hash-inspection source. "
            "Production packet construction rejects this predecessor input."
        ),
    )
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
            "repository-validation",
        ),
        default=None,
        help="Explicit trust boundary for every repository and output path.",
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
    return parser.parse_args(argv)


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


def main(
    argv: Sequence[str] | None = None,
    *,
    path_authority: ProjectPathAuthority | None = None,
) -> int:
    args = parse_args(argv)
    authority: ProjectPathAuthority | None = None
    try:
        if path_authority is not None:
            if path_authority.mode != "fixture":
                raise PathAuthorityError(
                    "injected path authority is reserved for isolated tests"
                )
            if args.path_authority is not None:
                raise PathAuthorityError(
                    "injected tests cannot select a production path authority"
                )
            if args.input_root != ROOT or args.output_root is not None:
                raise PathAuthorityError(
                    "injected tests receive repository and output roots from their authority"
                )
            authority = path_authority
        elif (args.path_authority or "production-canonical") == "production-canonical":
            authority = ProjectPathAuthority.production()
            _resolved_requested_root(
                args.input_root,
                authority.repository_root,
                "production input root",
            )
        elif args.path_authority == "production-transaction":
            if args.output_root is None:
                raise PathAuthorityError(
                    "production transaction requires an exact run root"
                )
            authority = ProjectPathAuthority.production_transaction(
                repository_root=args.input_root,
                run_root=args.output_root,
            )
        else:
            if not args.print_hash_updates:
                raise PathAuthorityError(
                    "repository validation is limited to hash inspection"
                )
            authority = ProjectPathAuthority.repository_validation(ROOT)
            _resolved_requested_root(
                args.input_root,
                authority.repository_root,
                "repository validation root",
            )
        input_root = authority.repository_root
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
            manifest_path = authority.requested_repository_file(
                args.manifest or DEFAULT_MANIFEST
            )
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
            packet_options = {
                "root": input_root,
                "issue_id": args.issue,
                "review_epoch_path": args.review_epoch,
                "review_epoch_root": review_epoch_root,
                "max_total_bytes": args.max_total_bytes,
                "capabilities": args.capability,
                "work_item_id": args.work_item_id,
                "work_kind": args.work_kind,
                "canonical_record": args.canonical_record,
                "path_authority": authority,
            }
            if authority.mode == "fixture":
                if args.manifest is None:
                    raise ContextError(
                        "fixture context construction requires an exact --manifest"
                    )
                manifest_path = authority.requested_repository_file(
                    args.manifest
                )
                value = build_context_packet(
                    manifest_path,
                    args.profile,
                    **packet_options,
                )
            else:
                if args.manifest is not None:
                    raise ContextError(
                        "production context construction forbids predecessor "
                        "--manifest routing"
                    )
                routing_view = load_validated_component_registry_routing_view(
                    authority,
                )
                if (
                    routing_view.get("schema_version") != 4
                    or routing_view.get("validation_mode")
                    != "live_authority_validation"
                    or routing_view.get("authoritative") is not True
                    or routing_view.get("executable") is not False
                    or routing_view.get("live_authority_verified") is not True
                    or routing_view.get("authority_effective") is not True
                    or routing_view.get("source_revision_authorized") is not True
                    or routing_view.get("source_bytes_current") is not True
                    or routing_view.get("canonical_history_confirmed") is not True
                    or routing_view.get("receipt_trusted") is not True
                    or routing_view.get("runtime_live") != "not_checked"
                    or routing_view.get("activation_receipt_consulted")
                    is not True
                    or routing_view.get("predecessor_route_consulted")
                    is not False
                    or routing_view.get("registry_component_executable")
                    is not False
                ):
                    raise RegistryError(
                        "production Elim context requires live-authority "
                        "Component Registry routing without predecessor "
                        "consultation"
                    )
                value = build_context_packet_from_view(
                    routing_view,
                    args.profile,
                    **packet_options,
                )
        emit(
            value,
            output=args.output,
            output_root=output_root,
        )
        return 0
    except (ContextError, PathAuthorityError, RegistryError) as exc:
        value = {"schema_version": 2, "status": "blocked", "error": str(exc)}
        if isinstance(exc, RoutingRuleFailure):
            value["routing_failure"] = exc.safe_evidence()
        try:
            emit(
                value,
                output=args.output,
                output_root=(
                    authority.output_root
                    if authority is not None
                    else args.output_root or args.input_root
                ),
            )
        except ContextError:
            json.dump(value, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
