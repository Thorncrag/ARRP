#!/usr/bin/env python3
"""Merge one ARRP integrity report into the Project Console history feed."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from console_data_contracts import feed_contract, file_sha256, utc_timestamp
except ModuleNotFoundError:
    from scripts.console_data_contracts import feed_contract, file_sha256, utc_timestamp


DEFAULT_HISTORY_LIMIT = 30
ALLOWED_HISTORY_HOST = "raw.githubusercontent.com"
ALLOWED_HISTORY_PATH = "/Thorncrag/ARRP/project-console-data/integrity.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--existing-url")
    parser.add_argument("--history-limit", type=int, default=DEFAULT_HISTORY_LIMIT)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return payload


def existing_feed(url: str | None) -> dict[str, Any]:
    if not url:
        return {}
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_HISTORY_HOST
        or parsed.port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path != ALLOWED_HISTORY_PATH
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Existing integrity feed URL is not the approved ARRP history endpoint")
    request = urllib.request.Request(url, headers={"User-Agent": "ARRP-integrity-feed/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
            if not isinstance(payload, dict):
                raise RuntimeError(
                    "Existing integrity history endpoint returned a non-object payload."
                )
            return payload
    except RuntimeError:
        raise
    except (OSError, ValueError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise RuntimeError(
            "Existing integrity history could not be fetched and validated; "
            "refusing to replace it with an empty history."
        ) from exc


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
    hashes = (
        {report_path.name: file_sha256(report_path)}
        if report_path is not None and report_path.is_file()
        else {}
    )
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
    feed = build_feed(
        read_json(args.report),
        existing_feed(args.existing_url),
        args.history_limit,
        report_path=args.report,
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
