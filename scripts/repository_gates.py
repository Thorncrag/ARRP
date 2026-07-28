#!/usr/bin/env python3
"""Produce the authoritative current ARRP repository-gate snapshot."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = Path(
    os.environ.get(
        "ARRP_STATE_ROOT",
        str(Path.home() / "Library/Application Support/ARRP"),
    )
).expanduser()
DEFAULT_DECLARATIONS = (
    STATE_ROOT / "records" / "automation" / "repository-gates.jsonl"
)
DEFAULT_OUTPUT = ROOT / ".tmp" / "repository-gates.json"
DEFAULT_REPOSITORY = "Thorncrag/ARRP"
REQUIRED_DECLARATION_FIELDS = {
    "gate_id",
    "pr_number",
    "pr_url",
    "head_sha",
    "blocks_automation",
    "gate_class",
    "reason",
    "affected_stages",
    "next_run_scope",
    "owner",
    "next_action",
    "unblock_predicate",
    "observed_since",
    "recorded_at",
    "source_id",
}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def read_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def load_gate_events(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.is_file():
        return [], [f"Gate declaration log is unavailable: {path}"]
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            errors.append(f"Line {line_number} is invalid JSON: {error.msg}")
            continue
        if not isinstance(value, dict):
            errors.append(f"Line {line_number} is not an object.")
            continue
        if value.get("event") == "registry_initialized":
            continue
        value["_line"] = line_number
        events.append(value)
    return events, errors


def active_gate_declarations(
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    active: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for event in events:
        event_type = str(event.get("event") or "")
        gate_id = str(event.get("gate_id") or "")
        if event_type not in {"declared", "resolved"} or not gate_id:
            errors.append(
                f"Line {event.get('_line', '?')} lacks a valid event and gate_id."
            )
            continue
        if event_type == "resolved":
            if gate_id not in active:
                errors.append(f"Gate {gate_id} resolves no active declaration.")
            active.pop(gate_id, None)
            continue
        missing = sorted(REQUIRED_DECLARATION_FIELDS - set(event))
        if missing:
            errors.append(f"Gate {gate_id} is missing: {', '.join(missing)}.")
            continue
        if event.get("blocks_automation") is not True:
            errors.append(f"Gate {gate_id} must declare blocks_automation=true.")
            continue
        if gate_id in active:
            errors.append(f"Gate {gate_id} has duplicate active declarations.")
            continue
        if not isinstance(event.get("affected_stages"), list):
            errors.append(f"Gate {gate_id} affected_stages must be an array.")
            continue
        if not isinstance(event.get("unblock_predicate"), dict):
            errors.append(f"Gate {gate_id} unblock_predicate must be an object.")
            continue
        active[gate_id] = {key: value for key, value in event.items() if key != "_line"}
    return list(active.values()), errors


def _paginate(
    request: Callable[[str], Any],
    path: str,
    *,
    page_size: int = 100,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page = 1
    while True:
        joiner = "&" if "?" in path else "?"
        value = request(f"{path}{joiner}per_page={page_size}&page={page}")
        if not isinstance(value, list):
            raise RuntimeError(f"GitHub pagination returned a non-array for {path}.")
        if not all(isinstance(item, dict) for item in value):
            raise RuntimeError(f"GitHub pagination returned a non-object row for {path}.")
        rows.extend(value)
        if len(value) < page_size:
            return rows, {
                "complete": True,
                "pages": page,
                "actual_count": len(rows),
                "page_size": page_size,
            }
        page += 1


def github_request_factory(repository: str, token: str) -> Callable[[str], Any]:
    def request(path: str) -> Any:
        url = (
            path
            if path.startswith("https://")
            else f"https://api.github.com/repos/{repository}/{path.lstrip('/')}"
        )
        request_value = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ARRP-repository-gates",
            },
        )
        with urllib.request.urlopen(request_value, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))

    return request


def collect_repository_inputs(
    request: Callable[[str], Any],
    declarations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[int, dict[str, Any]]]:
    pull_requests, pull_pagination = _paginate(
        request, "pulls?state=open&sort=created&direction=asc"
    )
    live_by_number = {
        int(item["number"]): item
        for item in pull_requests
        if isinstance(item.get("number"), int)
    }
    validation: dict[int, dict[str, Any]] = {}
    for declaration in declarations:
        number = int(declaration["pr_number"])
        pull = live_by_number.get(number)
        if not pull:
            continue
        head_sha = str((pull.get("head") or {}).get("sha") or "")
        reviews, review_pagination = _paginate(request, f"pulls/{number}/reviews")
        checks_value = request(
            f"commits/{urllib.parse.quote(head_sha)}/check-runs?per_page=100&page=1"
        )
        if not isinstance(checks_value, dict):
            raise RuntimeError(f"GitHub check-runs readback is invalid for PR {number}.")
        check_runs = checks_value.get("check_runs")
        total_count = checks_value.get("total_count")
        if not isinstance(check_runs, list) or not isinstance(total_count, int):
            raise RuntimeError(f"GitHub check-runs pagination is invalid for PR {number}.")
        if total_count > len(check_runs):
            raise RuntimeError(
                f"GitHub check-runs pagination is incomplete for PR {number}: "
                f"{len(check_runs)} of {total_count}."
            )
        detail = request(f"pulls/{number}")
        if not isinstance(detail, dict):
            raise RuntimeError(f"GitHub pull-request readback is invalid for PR {number}.")
        validation[number] = {
            "reviews": reviews,
            "review_pagination": review_pagination,
            "checks": check_runs,
            "check_pagination": {
                "complete": total_count == len(check_runs),
                "actual_count": len(check_runs),
                "total_count": total_count,
            },
            "mergeable": detail.get("mergeable"),
            "mergeable_state": detail.get("mergeable_state"),
        }
    return pull_requests, pull_pagination, validation


def build_repository_gate_snapshot(
    *,
    repository: str,
    events: list[dict[str, Any]],
    event_errors: list[str],
    open_pull_requests: list[dict[str, Any]],
    pull_pagination: dict[str, Any],
    validation: dict[int, dict[str, Any]],
    checked_at: str,
    last_good: dict[str, Any] | None = None,
) -> dict[str, Any]:
    declarations, declaration_errors = active_gate_declarations(events)
    errors = [*event_errors, *declaration_errors]
    open_by_number = {
        int(item["number"]): item
        for item in open_pull_requests
        if isinstance(item, dict) and isinstance(item.get("number"), int)
    }
    items: list[dict[str, Any]] = []
    for declaration in declarations:
        number = int(declaration["pr_number"])
        pull = open_by_number.get(number)
        predicate = declaration.get("unblock_predicate") or {}
        if not pull:
            if predicate.get("type") in {"pr_closed", "pr_closed_or_merged"}:
                continue
            errors.append(
                f"Gate {declaration['gate_id']} references PR {number}, which is "
                "not present in the complete open-PR scan."
            )
            items.append({**declaration, "validation_state": "live_pr_missing"})
            continue
        current_head = str((pull.get("head") or {}).get("sha") or "")
        exact_head_valid = current_head == str(declaration["head_sha"])
        if not exact_head_valid:
            errors.append(
                f"Gate {declaration['gate_id']} exact head changed from "
                f"{declaration['head_sha']} to {current_head or 'unavailable'}."
            )
        item = {
            **declaration,
            "current_head_sha": current_head,
            "base_sha": str((pull.get("base") or {}).get("sha") or ""),
            "exact_head_valid": exact_head_valid,
            "validation_state": "active" if exact_head_valid else "head_changed",
            "live": validation.get(number),
            "affected_latest_attempt": False,
        }
        items.append(item)
    complete = (
        pull_pagination.get("complete") is True
        and not errors
    )
    snapshot: dict[str, Any] = {
        "schema_version": 1,
        "repository": repository,
        "source_revision": checked_at,
        "checked_at": checked_at,
        "availability": "current" if complete else "incomplete",
        "complete": complete,
        "count": len(items) if complete else None,
        "known_blocker_count": len(items),
        "pagination": {
            "open_pull_requests": pull_pagination,
            "declarations_complete": not event_errors,
        },
        "declaration_errors": declaration_errors,
        "validation_errors": [error for error in errors if error not in declaration_errors],
        "last_good_identity": (
            {
                "checked_at": last_good.get("checked_at"),
                "source_revision": last_good.get("source_revision"),
            }
            if last_good and last_good.get("complete") is True
            else None
        ),
        "items": items,
    }
    return snapshot


def produce_repository_gate_snapshot(
    *,
    repository: str,
    declarations_path: Path,
    token: str,
    checked_at: str | None = None,
    last_good: dict[str, Any] | None = None,
    request: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    observed_at = checked_at or utc_timestamp()
    events, event_errors = load_gate_events(declarations_path)
    declarations, _declaration_errors = active_gate_declarations(events)
    request_value = request or github_request_factory(repository, token)
    try:
        pulls, pagination, validation = collect_repository_inputs(
            request_value, declarations
        )
        return build_repository_gate_snapshot(
            repository=repository,
            events=events,
            event_errors=event_errors,
            open_pull_requests=pulls,
            pull_pagination=pagination,
            validation=validation,
            checked_at=observed_at,
            last_good=last_good,
        )
    except Exception as error:
        retained_items = (
            list(last_good.get("items") or [])
            if last_good and last_good.get("complete") is True
            else []
        )
        return {
            "schema_version": 1,
            "repository": repository,
            "source_revision": observed_at,
            "checked_at": observed_at,
            "availability": "last_valid_retained" if retained_items else "unavailable",
            "complete": False,
            "count": None,
            "known_blocker_count": len(retained_items),
            "pagination": {
                "open_pull_requests": {"complete": False},
                "declarations_complete": not event_errors,
            },
            "declaration_errors": event_errors,
            "validation_errors": [str(error)],
            "last_good_identity": (
                {
                    "checked_at": last_good.get("checked_at"),
                    "source_revision": last_good.get("source_revision"),
                }
                if last_good and last_good.get("complete") is True
                else None
            ),
            "trustworthy_through": (
                last_good.get("checked_at")
                if last_good and last_good.get("complete") is True
                else None
            ),
            "items": retained_items,
        }


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--repository", default=DEFAULT_REPOSITORY)
    value.add_argument("--declarations", type=Path, default=DEFAULT_DECLARATIONS)
    value.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    value.add_argument("--last-good", type=Path)
    value.add_argument("--token-env", default="GH_TOKEN")
    return value


def main() -> int:
    args = parser().parse_args()
    token = os.environ.get(args.token_env, "")
    last_good = read_json(args.last_good)
    snapshot = produce_repository_gate_snapshot(
        repository=args.repository,
        declarations_path=args.declarations,
        token=token,
        last_good=last_good,
    )
    atomic_write(args.output, snapshot)
    return 0 if snapshot.get("complete") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
