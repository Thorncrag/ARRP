#!/usr/bin/env python3
"""Select the context profile for the work unit authorized by the chain."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from arrp_context import ContextError, ROOT, apply_user_overrides, contained_path


PROFILE_BY_KIND = {
    "bot_failure": "integrity_reconciliation",
    "integrity": "integrity_reconciliation",
    "public_intake": "public_intake",
    "change_audit": "change_audit",
    "issue_audit": "issue_audit",
    "issue_development": "issue_development",
    "candidate_research": "candidate_research",
    "comprehensive_review": "comprehensive_review",
}
ISSUE_DOSSIER_KINDS = {"change_audit", "issue_audit", "issue_development"}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


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
    destination = Path(normalized_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=destination.parent,
        delete=False,
    ) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(destination)


def select_context_route(
    queue: dict[str, Any], chain: dict[str, Any]
) -> dict[str, str | None]:
    runtime_overrides = chain.get("user_overrides")
    if runtime_overrides is not None and not isinstance(runtime_overrides, dict):
        raise ContextError("chain user_overrides must be an object")
    items, _, _ = apply_user_overrides(
        (
            item
            for item in queue.get("items", [])
            if isinstance(item, dict)
        ),
        runtime_overrides,
    )
    eligible = [
        item
        for item in items
        if item.get("eligible_for_elim")
    ]
    full_context = bool(
        ((chain.get("elim_decision") or {}).get("profile") or {}).get(
            "full_context"
        )
    )
    repair_item = next(
        (
            candidate
            for candidate in eligible
            if candidate.get("kind") == "bot_failure"
            and candidate.get("safety_class") == 0
        ),
        None,
    )
    if repair_item is not None:
        item = repair_item
    elif full_context:
        item = next(
            (candidate for candidate in eligible if candidate.get("kind") == "comprehensive_review"),
            None,
        )
        if item is None:
            raise ValueError(
                "the chain authorized full context but the queue has no eligible "
                "comprehensive-review unit"
            )
    else:
        selected_id = (
            None
            if runtime_overrides
            else str(queue.get("selected_work_item_id") or "").strip() or None
        )
        item = (
            next(
                (
                    candidate
                    for candidate in eligible
                    if candidate.get("id") == selected_id
                ),
                None,
            )
            if selected_id
            else eligible[0] if eligible else None
        )
        if selected_id and item is None:
            raise ValueError(
                "the queue's exact selected work-item ID is not eligible"
            )

    if item is None:
        return {
            "profile": None,
            "issue": None,
            "work_item_id": None,
            "kind": None,
            "canonical_record": None,
        }
    work_item_id = str(item.get("id") or "").strip()
    if not work_item_id:
        raise ValueError("selected Elim work item has no deterministic ID")
    kind = str(item.get("kind") or "")
    profile = PROFILE_BY_KIND.get(kind)
    if profile is None:
        raise ValueError(f"no reviewed context profile exists for work kind {kind!r}")
    source = item.get("source") or {}
    if not isinstance(source, dict):
        raise ValueError(f"selected Elim work item {work_item_id} has invalid source metadata")
    identifier = str(source.get("identifier") or "").strip()
    canonical_record = str(
        source.get("canonicalRecord") or source.get("canonical_record") or ""
    ).strip()
    canonical_error = str(source.get("canonical_record_error") or "").strip()
    if canonical_error:
        raise ValueError(
            f"selected {kind} work item {work_item_id} has no usable canonical "
            f"record: {canonical_error}"
        )
    issue = None
    if kind in ISSUE_DOSSIER_KINDS:
        if not identifier or not canonical_record:
            raise ValueError(
                f"selected {kind} work item {work_item_id} lacks its identifier "
                "or canonical record"
            )
        area = identifier.split("-", 1)[0]
        expected = f"areas/{area}/issues/{identifier}.md"
        area_readme = f"areas/{area}/README.md"
        development_level = " ".join(
            str(source.get("development_level") or "").casefold().split()
        )
        workflow_status = " ".join(
            str(source.get("workflow_status") or "").casefold().split()
        )
        undeveloped_area_record = (
            kind == "issue_development"
            and development_level == "admitted / undeveloped"
            and workflow_status in {"development", "research"}
            and canonical_record == area_readme
        )
        if canonical_record != expected and not undeveloped_area_record:
            raise ValueError(
                f"selected {kind} work item {work_item_id} has canonical record "
                f"{canonical_record!r}; expected {expected!r}"
            )
        issue = identifier
    elif kind == "candidate_research" and not canonical_record:
        raise ValueError(
            f"selected candidate_research work item {work_item_id} lacks its "
            "canonical record"
        )
    return {
        "profile": profile,
        "issue": issue,
        "work_item_id": work_item_id,
        "kind": kind,
        "canonical_record": canonical_record or None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--chain", type=Path, required=True)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=ROOT,
        help="Exact reviewed run root containing the queue and chain.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Write the selected route as deterministic JSON under --input-root. "
            "When omitted, preserve the legacy five-line stdout interface."
        ),
    )
    args = parser.parse_args()
    try:
        queue = contained_path(args.queue, args.input_root)
        chain = contained_path(args.chain, args.input_root)
        route = select_context_route(read_json(queue), read_json(chain))
        if args.output is not None:
            write_json(args.output, route, args.input_root)
            return 0
    except (ContextError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"select-elim-context-route: {exc}", file=sys.stderr)
        return 2
    print(route["profile"] or "")
    print(route["issue"] or "")
    print(route["work_item_id"] or "")
    print(route["kind"] or "")
    print(route["canonical_record"] or "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
