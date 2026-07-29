#!/usr/bin/env python3
"""Merge one ARRP integrity report into the Project Console history feed."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

try:
    from console_data_contracts import feed_contract, file_sha256, utc_timestamp
except ModuleNotFoundError:
    from scripts.console_data_contracts import feed_contract, file_sha256, utc_timestamp


DEFAULT_HISTORY_LIMIT = 30
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_TEMP_ROOT = Path(tempfile.gettempdir()).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--existing-file",
        type=Path,
        help=(
            "Optional trusted local JSON or generated Console integrity.js "
            "whose bounded history should be retained."
        ),
    )
    parser.add_argument("--history-limit", type=int, default=DEFAULT_HISTORY_LIMIT)
    return parser.parse_args()


def trusted_report_path(
    path: Path,
    allowed_suffixes: tuple[str, ...] = (".json",),
) -> tuple[Path, Path]:
    """Resolve an integrity report beneath the repository or system temp root."""
    resolved_path = os.path.realpath(os.fspath(path))
    for trusted_root in (REPOSITORY_ROOT, SYSTEM_TEMP_ROOT):
        resolved_root = os.path.realpath(os.fspath(trusted_root))
        root_prefix = resolved_root.rstrip(os.sep) + os.sep
        if (
            resolved_path.startswith(root_prefix)
            and resolved_path.endswith(allowed_suffixes)
            and os.path.isfile(resolved_path)
        ):
            return Path(resolved_path), Path(resolved_root)
    raise ValueError(
        "Integrity report must be a regular JSON file within the repository "
        "or system temporary directory."
    )


def read_json(path: Path) -> dict[str, Any]:
    trusted_path, _ = trusted_report_path(path)
    with open(os.fspath(trusted_path), encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {trusted_path}")
    return payload


def existing_feed_file(path: Path | None) -> dict[str, Any]:
    """Read retained history from a trusted local JSON or Console domain file."""

    if path is None:
        return {}
    trusted_path, _ = trusted_report_path(path, (".json", ".js"))
    text = trusted_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        marker = "Object.assign(window.ARRP_HORIZON_REVIEW_DATA,"
        private_marker = "window.ARRP_PRIVATE_OPERATIONS="
        if marker in text:
            serialized = text.split(marker, 1)[1].strip()
            if not serialized.endswith(");"):
                raise RuntimeError("Existing Console integrity domain is malformed.")
            serialized = serialized[:-2]
            container_key = "integrity"
        elif private_marker in text:
            serialized = text.split(private_marker, 1)[1].strip()
            if not serialized.endswith(";"):
                raise RuntimeError(
                    "Existing private operations projection is malformed."
                )
            serialized = serialized[:-1]
            container_key = "integrity"
        else:
            raise RuntimeError(
                "Existing local integrity feed is neither JSON nor a generated "
                "Console domain."
            )
        try:
            domain = json.loads(serialized)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Existing Console integrity domain contains invalid JSON."
            ) from exc
        payload = (
            domain.get(container_key) if isinstance(domain, dict) else None
        )
    if not isinstance(payload, dict):
        raise RuntimeError("Existing local integrity feed is not an object.")
    return payload


def history_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": report.get("generated_at", ""),
        "revision": report.get("revision", ""),
        "result": report.get("result", "unknown"),
        "counts": report.get("counts", {}),
        "duration_seconds": report.get("duration_seconds", 0),
    }


def build_feed(
    report: dict[str, Any],
    existing: dict[str, Any],
    history_limit: int,
    *,
    report_path: Path | None = None,
) -> dict[str, Any]:
    raw_generated_at = str(report.get("generated_at") or "").strip()
    if not raw_generated_at:
        raise RuntimeError("Integrity report lacks a generated_at timestamp.")
    generated_at = utc_timestamp(raw_generated_at)
    revision = str(report.get("revision") or "").strip()
    if not revision:
        raise RuntimeError("Integrity report lacks its checked source revision.")
    counts = report.get("counts")
    findings = report.get("findings")
    if not isinstance(counts, dict) or not isinstance(findings, list):
        raise RuntimeError(
            "Integrity report lacks structured counts or findings."
        )
    if int(counts.get("findings", -1)) != len(findings):
        raise RuntimeError(
            "Integrity report finding count does not match its finding array."
        )
    if existing and not isinstance(existing.get("history"), list):
        raise RuntimeError(
            "Existing integrity feed does not satisfy the history contract."
        )
    prior = existing.get("history", [])
    history = [history_summary(report)]
    seen = {str(report.get("generated_at", ""))}
    for item in prior:
        if not isinstance(item, dict):
            raise RuntimeError(
                "Existing integrity history contains a non-object snapshot."
            )
        timestamp = str(item.get("generated_at", ""))
        if not timestamp:
            raise RuntimeError(
                "Existing integrity history contains an undated snapshot."
            )
        if timestamp in seen:
            continue
        seen.add(timestamp)
        history.append(item)
    scope = report.get("scope") or []
    if not isinstance(scope, list):
        raise RuntimeError("Integrity report scope must be an array.")
    hashes: dict[str, str] = {}
    if report_path is not None:
        trusted_path, trusted_root = trusted_report_path(report_path)
        hashes[trusted_path.name] = file_sha256(trusted_root, trusted_path)
    contract = feed_contract(
        feed_name="project-integrity",
        timestamp_field="generated_at",
        timestamp=generated_at,
        revision=revision,
        hashes=hashes,
        expected_count=len(scope),
        actual_count=len(scope),
        pagination={
            "complete": True,
            "sources": [
                {
                    "source": "integrity-check-inventory",
                    "complete": True,
                    "expected_count": len(scope),
                    "actual_count": len(scope),
                }
            ],
        },
        projection_errors=[],
    )
    return {
        "schema_version": 2,
        **contract,
        "current": report,
        "history": history[: max(1, history_limit)],
    }


def main() -> int:
    args = parse_args()
    if args.history_limit < 1:
        raise ValueError("--history-limit must be positive")
    report_path, _ = trusted_report_path(args.report)
    existing = existing_feed_file(args.existing_file)
    feed = build_feed(
        read_json(report_path),
        existing,
        args.history_limit,
        report_path=report_path,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(feed, indent=2) + "\n", encoding="utf-8")
    print(
        "Wrote {} with {} retained integrity run(s).".format(
            args.output, len(feed["history"])
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
