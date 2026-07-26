#!/usr/bin/env python3
"""Shared truth-contract helpers for ARRP Project Console generated data."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


CONTRACT_SCHEMA_VERSION = 1
VALID_AVAILABILITY = {"available", "current", "stale", "unavailable"}


def utc_timestamp(value: str | None = None) -> str:
    """Return one validated UTC ISO-8601 timestamp."""
    if value:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def file_sha256(root: Path, path: Path) -> str:
    """Hash one regular file only after proving it remains within ``root``."""
    resolved_root = os.path.realpath(os.fspath(root))
    resolved_path = os.path.realpath(os.fspath(path))
    root_prefix = resolved_root.rstrip(os.sep) + os.sep
    if resolved_path != resolved_root and not resolved_path.startswith(root_prefix):
        raise ValueError(f"Refusing to hash a file outside {resolved_root}: {resolved_path}")
    digest = hashlib.sha256()
    with open(resolved_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def source_hashes(root: Path, paths: Iterable[Path]) -> dict[str, str]:
    result: dict[str, str] = {}
    resolved_root = os.path.realpath(os.fspath(root))
    root_prefix = resolved_root.rstrip(os.sep) + os.sep
    for path in paths:
        resolved = os.path.realpath(os.fspath(path))
        if resolved != resolved_root and not resolved.startswith(root_prefix):
            raise ValueError(
                f"Refusing to hash a source outside {resolved_root}: {resolved}"
            )
        label = os.path.relpath(resolved, resolved_root).replace(os.sep, "/")
        if os.path.isfile(resolved):
            result[label] = file_sha256(Path(resolved_root), Path(resolved))
    return dict(sorted(result.items()))


def source_revision(root: Path) -> str:
    configured = (
        os.environ.get("SOURCE_REVISION", "").strip()
        or os.environ.get("GITHUB_SHA", "").strip()
    )
    if configured:
        return configured
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def generation_id(
    feed_name: str,
    timestamp: str,
    revision: str,
    hashes: Mapping[str, str],
    expected_count: int,
    actual_count: int,
) -> str:
    material = json.dumps(
        {
            "feed": feed_name,
            "timestamp": timestamp,
            "source_revision": revision,
            "source_hashes": dict(sorted(hashes.items())),
            "expected_count": expected_count,
            "actual_count": actual_count,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"{feed_name}-{hashlib.sha256(material).hexdigest()[:20]}"


def feed_contract(
    *,
    feed_name: str,
    timestamp_field: str,
    timestamp: str,
    revision: str,
    hashes: Mapping[str, str],
    expected_count: int,
    actual_count: int,
    pagination: Mapping[str, Any] | None = None,
    projection_errors: Iterable[Mapping[str, Any]] = (),
    unavailable: bool = False,
) -> dict[str, Any]:
    errors = [dict(error) for error in projection_errors]
    pagination_payload = dict(pagination or {"complete": True, "sources": []})
    pagination_complete = pagination_payload.get("complete") is True
    complete = (
        not unavailable
        and expected_count == actual_count
        and pagination_complete
        and not any(error.get("severity", "error") == "error" for error in errors)
    )
    availability = "unavailable" if unavailable else "current" if complete else "stale"
    contract = {
        "contract_schema_version": CONTRACT_SCHEMA_VERSION,
        "generation_id": generation_id(
            feed_name,
            timestamp,
            revision,
            hashes,
            expected_count,
            actual_count,
        ),
        "source_revision": revision,
        timestamp_field: timestamp,
        "expected_count": expected_count,
        "actual_count": actual_count,
        "source_hashes": dict(sorted(hashes.items())),
        "availability": availability,
        "completeness": {
            "complete": complete,
            "expected_count": expected_count,
            "actual_count": actual_count,
            "missing_count": max(expected_count - actual_count, 0),
        },
        "pagination": pagination_payload,
        "projection_errors": errors,
        "freshness": {
            "status": availability,
            "basis": "source revision, completeness, and owning-process synchronization",
            "supersession_rule": (
                "A newer authoritative source revision or generation supersedes this "
                "projection immediately, regardless of elapsed age."
            ),
        },
    }
    return contract


def validate_contract(
    payload: Mapping[str, Any],
    *,
    timestamp_fields: tuple[str, ...],
    allow_legacy: bool = True,
) -> bool:
    if not isinstance(payload, Mapping):
        return False
    if not any(str(payload.get(field) or "").strip() for field in timestamp_fields):
        return False
    if "generation_id" not in payload:
        return allow_legacy
    availability = str(payload.get("availability") or "")
    if availability not in VALID_AVAILABILITY:
        return False
    completeness = payload.get("completeness")
    if not isinstance(completeness, Mapping):
        return False
    try:
        expected = int(payload.get("expected_count"))
        actual = int(payload.get("actual_count"))
    except (TypeError, ValueError):
        return False
    return expected >= 0 and actual >= 0
