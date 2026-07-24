#!/usr/bin/env python3
"""Select the context profile for the work unit authorized by the chain."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROFILE_BY_KIND = {
    "bot_failure": "integrity_reconciliation",
    "integrity": "integrity_reconciliation",
    "public_intake": "public_intake",
    "change_audit": "change_audit",
    "issue_audit": "issue_audit",
    "issue_development": "issue_development",
    "comprehensive_review": "comprehensive_review",
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def select_context_route(
    queue: dict[str, Any], chain: dict[str, Any]
) -> dict[str, str | None]:
    eligible = [
        item
        for item in queue.get("items", [])
        if isinstance(item, dict) and item.get("eligible_for_elim")
    ]
    full_context = bool(
        ((chain.get("elim_decision") or {}).get("profile") or {}).get(
            "full_context"
        )
    )
    if full_context:
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
        item = eligible[0] if eligible else None

    if item is None:
        return {"profile": None, "issue": None, "work_item_id": None}
    kind = str(item.get("kind") or "")
    profile = PROFILE_BY_KIND.get(kind)
    if profile is None:
        raise ValueError(f"no reviewed context profile exists for work kind {kind!r}")
    source = item.get("source") or {}
    issue = source.get("identifier") if isinstance(source, dict) else None
    return {
        "profile": profile,
        "issue": str(issue) if issue else None,
        "work_item_id": str(item.get("id") or "") or None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--chain", type=Path, required=True)
    args = parser.parse_args()
    try:
        route = select_context_route(read_json(args.queue), read_json(args.chain))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"select-elim-context-route: {exc}", file=sys.stderr)
        return 2
    print(route["profile"] or "")
    print(route["issue"] or "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
