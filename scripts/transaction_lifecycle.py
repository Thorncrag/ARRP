#!/usr/bin/env python3
"""Owner-local append-only transaction lifecycle authority (fixture-safe only).

This module deliberately takes an explicit event-log path and never resolves a
production state root, manipulates a Git worktree, retires material, or starts
automation. The Run Coordinator binds it through the owner-local path authority
and retains its separate retirement-approval boundary.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import fcntl

SCHEMA_VERSION = 1
EVENT_TYPES = frozenset(
    {
        "started",
        "state_changed",
        "retry_authorized",
        "retry_claimed",
        "abandoned",
        "historical_imported",
    }
)
STATES = ("active", "failed_preserved", "recovery_pending", "reconciled_or_superseded", "recovery_packaged", "recoverably_retired", "completed_noop", "completed_published")
TERMINAL_STATES = frozenset({"recoverably_retired", "completed_noop", "completed_published"})
RESOLVED_PREDECESSOR_STATES = frozenset({"reconciled_or_superseded", "recovery_packaged", "recoverably_retired", "completed_noop", "completed_published"})
ALLOWED_TRANSITIONS = {
    "active": frozenset({"failed_preserved", "completed_noop", "completed_published"}),
    "failed_preserved": frozenset({"recovery_pending"}),
    "recovery_pending": frozenset({"reconciled_or_superseded", "recovery_packaged"}),
    "reconciled_or_superseded": frozenset({"recovery_packaged"}),
    "recovery_packaged": frozenset({"recoverably_retired"}),
}
RUN_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
INCIDENT_ID = re.compile(r"^INC-\d{4}-\d{3,}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
OPAQUE_REF = re.compile(r"^owner-local:(?:transaction-evidence|transaction-recovery)/[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
FIELDS = frozenset(
    {
        "schema_version",
        "event_id",
        "run_id",
        "attempt_group_id",
        "attempt_number",
        "event_type",
        "recorded_at",
        "state",
        "trigger",
        "branch",
        "head",
        "base",
        "logical_worktree_id",
        "logical_run_id",
        "delta_digest",
        "package_digest",
        "failure_code",
        "incident_id",
        "owner",
        "next_action",
        "evidence_refs",
        "predecessor_run_id",
        "predecessor_terminal_digest",
        "retry_authorization",
        "terminal_proof",
        "recovery_proof",
        "migration_batch_id",
        "migration_member_count",
        "migration_member_digest",
        "migration_source_slots",
        "event_sha256",
    }
)

class TransactionLifecycleError(ValueError):
    """A transaction event or lifecycle transition is invalid."""

def iso_utc(value: datetime | None = None) -> str:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise TransactionLifecycleError("time must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def _text(value: object, field: str, *, required: bool = True) -> str | None:
    text = " ".join(str(value or "").replace("\x00", " ").split())
    if any(part in text for part in ("/Users/", "\\", "file://", "\n")):
        raise TransactionLifecycleError(f"{field} contains non-public-safe path material")
    if len(text) > 512:
        raise TransactionLifecycleError(f"{field} exceeds the bounded safe-text limit")
    if required and not text:
        raise TransactionLifecycleError(f"{field} is required")
    return text or None

def _identity(value: object, field: str) -> str:
    text = _text(value, field)
    if not RUN_ID.fullmatch(str(text)):
        raise TransactionLifecycleError(f"{field} must be a typed identity")
    return str(text)

def _digest(value: object, field: str, *, required: bool = True) -> str | None:
    if value is None and not required:
        return None
    text = _text(value, field, required=required)
    if text is None:
        return None
    if not DIGEST.fullmatch(text):
        raise TransactionLifecycleError(f"{field} must be a sha256 digest")
    return text

def _timestamp(value: object, field: str) -> str:
    text = _text(value, field)
    if not TIMESTAMP.fullmatch(str(text)):
        raise TransactionLifecycleError(f"{field} must be a canonical UTC timestamp")
    try:
        datetime.strptime(str(text), "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise TransactionLifecycleError(f"{field} is invalid") from exc
    return str(text)

def _hash(value: Mapping[str, Any], excluded: str = "event_sha256") -> str:
    payload = {key: item for key, item in value.items() if key != excluded}
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def _proof(value: object, field: str, *, required: bool) -> dict[str, str] | None:
    if value is None:
        if required:
            raise TransactionLifecycleError(f"{field} is required")
        return None
    if not isinstance(value, Mapping) or set(value) != {"proof_digest", "evidence_ref"}:
        raise TransactionLifecycleError(f"{field} must contain only proof_digest and evidence_ref")
    proof = {"proof_digest": _digest(value["proof_digest"], f"{field}.proof_digest"), "evidence_ref": str(value["evidence_ref"])}
    if not OPAQUE_REF.fullmatch(proof["evidence_ref"]):
        raise TransactionLifecycleError(f"{field}.evidence_ref must be an opaque owner-local reference")
    return proof

def _authorization(value: object, *, required: bool = False) -> dict[str, str] | None:
    if value is None:
        if required:
            raise TransactionLifecycleError("retry_authorization is required")
        return None
    if not isinstance(value, Mapping) or set(value) != {"authorization_id", "predecessor_run_id", "predecessor_terminal_digest", "expires_at"}:
        raise TransactionLifecycleError("retry_authorization has invalid fields")
    return {"authorization_id": _identity(value["authorization_id"], "authorization_id"), "predecessor_run_id": _identity(value["predecessor_run_id"], "predecessor_run_id"), "predecessor_terminal_digest": str(_digest(value["predecessor_terminal_digest"], "predecessor_terminal_digest")), "expires_at": _timestamp(value["expires_at"], "expires_at")}

def validate_event(event: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(event, Mapping) or frozenset(event) != FIELDS:
        raise TransactionLifecycleError("transaction event fields do not match the deny-by-default contract")
    value = dict(event)
    if value["schema_version"] != SCHEMA_VERSION or value["event_type"] not in EVENT_TYPES or value["state"] not in STATES:
        raise TransactionLifecycleError("unsupported transaction event schema, type, or state")
    value["run_id"] = _identity(value["run_id"], "run_id")
    value["attempt_group_id"] = _identity(value["attempt_group_id"], "attempt_group_id")
    if not isinstance(value["attempt_number"], int) or value["attempt_number"] < 1:
        raise TransactionLifecycleError("attempt_number must be a positive integer")
    value["event_id"] = str(value["event_id"])
    if not re.fullmatch(re.escape(value["run_id"]) + r":\d{4,}", value["event_id"]):
        raise TransactionLifecycleError("event_id must be scoped to run_id")
    value["recorded_at"] = _timestamp(value["recorded_at"], "recorded_at")
    for key in ("trigger", "branch", "head", "base", "logical_run_id", "owner", "next_action"):
        value[key] = str(_text(value[key], key))
    value["logical_worktree_id"] = _identity(value["logical_worktree_id"], "logical_worktree_id") if value["logical_worktree_id"] is not None else None
    value["delta_digest"] = str(_digest(value["delta_digest"], "delta_digest"))
    value["package_digest"] = _digest(value["package_digest"], "package_digest", required=False)
    value["failure_code"] = _identity(value["failure_code"], "failure_code") if value["failure_code"] is not None else None
    value["incident_id"] = str(value["incident_id"]) if value["incident_id"] is not None else None
    if value["incident_id"] is not None and not INCIDENT_ID.fullmatch(value["incident_id"]):
        raise TransactionLifecycleError("incident_id must be a typed Operational Incident ID")
    if not isinstance(value["evidence_refs"], list) or len(value["evidence_refs"]) > 32 or not all(isinstance(ref, str) and OPAQUE_REF.fullmatch(ref) for ref in value["evidence_refs"]):
        raise TransactionLifecycleError("evidence_refs must be bounded opaque owner-local references")
    value["predecessor_run_id"] = _identity(value["predecessor_run_id"], "predecessor_run_id") if value["predecessor_run_id"] is not None else None
    value["predecessor_terminal_digest"] = _digest(value["predecessor_terminal_digest"], "predecessor_terminal_digest", required=False)
    value["retry_authorization"] = _authorization(value["retry_authorization"])
    value["terminal_proof"] = _proof(value["terminal_proof"], "terminal_proof", required=value["state"] in {"reconciled_or_superseded", "completed_noop", "completed_published"})
    value["recovery_proof"] = _proof(value["recovery_proof"], "recovery_proof", required=value["state"] in {"recovery_packaged", "recoverably_retired"})
    value["migration_batch_id"] = (
        _identity(value["migration_batch_id"], "migration_batch_id")
        if value["migration_batch_id"] is not None
        else None
    )
    if value["migration_member_count"] is not None and (
        not isinstance(value["migration_member_count"], int)
        or value["migration_member_count"] < 1
    ):
        raise TransactionLifecycleError(
            "migration_member_count must be null or a positive integer"
        )
    value["migration_member_digest"] = _digest(
        value["migration_member_digest"],
        "migration_member_digest",
        required=False,
    )
    if (
        not isinstance(value["migration_source_slots"], list)
        or len(value["migration_source_slots"]) > 8
        or not all(
            isinstance(slot, str) and _text(slot, "migration_source_slot")
            for slot in value["migration_source_slots"]
        )
    ):
        raise TransactionLifecycleError(
            "migration_source_slots must be a bounded safe-text list"
        )
    historical = value["event_type"] == "historical_imported"
    migration_fields = (
        value["migration_batch_id"],
        value["migration_member_count"],
        value["migration_member_digest"],
    )
    if historical:
        common_invalid = (
            any(item is None for item in migration_fields)
            or not value["migration_source_slots"]
            or value["predecessor_run_id"] is not None
            or value["predecessor_terminal_digest"] is not None
            or value["retry_authorization"] is not None
        )
        if value["logical_worktree_id"] is None:
            if (
                common_invalid
                or value["migration_member_count"] != 1
                or value["state"] not in {"completed_noop", "completed_published"}
                or value["terminal_proof"] is None
                or value["package_digest"] is not None
                or value["recovery_proof"] is not None
                or value["failure_code"] is not None
            ):
                raise TransactionLifecycleError(
                    "historical terminal import does not match the no-worktree contract"
                )
        else:
            expected_failure = (
                "preexisting-multi-live-group"
                if value["migration_member_count"] > 1
                else "preexisting-retained-transaction"
            )
            if (
                common_invalid
                or value["state"] != "recovery_packaged"
                or value["failure_code"] != expected_failure
                or value["package_digest"] is None
                or value["recovery_proof"] is None
                or value["terminal_proof"] is not None
            ):
                raise TransactionLifecycleError(
                    "historical import does not match the migration-only contract"
                )
    else:
        has_any_migration = (
            any(item is not None for item in migration_fields)
            or bool(value["migration_source_slots"])
        )
        has_complete_migration = (
            all(item is not None for item in migration_fields)
            and bool(value["migration_source_slots"])
        )
        if has_any_migration and (
            not has_complete_migration
            or value["event_type"] not in {"state_changed", "retry_authorized"}
        ):
            raise TransactionLifecycleError(
                "ordinary transaction events cannot originate migration authority"
            )
    if value["state"] == "failed_preserved" and value["failure_code"] is None:
        raise TransactionLifecycleError("failed_preserved requires a typed failure_code")
    if value["state"] == "recoverably_retired" and value["package_digest"] is None:
        raise TransactionLifecycleError("recoverably_retired requires a recovery package digest")
    expected = _hash(value)
    if value["event_sha256"] not in (None, expected):
        raise TransactionLifecycleError("transaction event hash mismatch")
    value["event_sha256"] = expected
    return value

def _parse_events(raw_text: str) -> list[dict[str, Any]]:
    records = []
    for number, line in enumerate(raw_text.splitlines(), 1):
        if not line.strip(): continue
        try: records.append(validate_event(json.loads(line)))
        except (json.JSONDecodeError, TransactionLifecycleError) as exc: raise TransactionLifecycleError(f"transaction event log line {number} is invalid: {exc}") from exc
    if len({event["event_id"] for event in records}) != len(records): raise TransactionLifecycleError("duplicate transaction event ID")
    return records


def _migration_member_payload(event: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "run_id": event["run_id"],
        "attempt_number": event["attempt_number"],
        "branch": event["branch"],
        "head": event["head"],
        "base": event["base"],
        "logical_worktree_id": event["logical_worktree_id"],
        "logical_run_id": event["logical_run_id"],
        "delta_digest": event["delta_digest"],
        "package_digest": event["package_digest"],
        "recovery_proof": event["recovery_proof"],
        "evidence_refs": event["evidence_refs"],
    }


def _migration_members_digest(events: Sequence[Mapping[str, Any]]) -> str:
    members = sorted(
        (_migration_member_payload(event) for event in events),
        key=lambda item: (item["attempt_number"], item["run_id"]),
    )
    return "sha256:" + hashlib.sha256(
        json.dumps(members, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _validate_global_history(events: Sequence[Mapping[str, Any]]) -> None:
    """Validate complete migration batches and cross-run live-worktree rules."""

    by_run: dict[str, list[Mapping[str, Any]]] = {}
    for event in events:
        by_run.setdefault(str(event["run_id"]), []).append(event)
    imported_first = [
        rows[0]
        for rows in by_run.values()
        if rows and rows[0]["event_type"] == "historical_imported"
    ]
    imported_runs = {str(event["run_id"]) for event in imported_first}
    for run_id, rows in by_run.items():
        migration_rows = [row for row in rows if row["migration_batch_id"]]
        if migration_rows and run_id not in imported_runs:
            raise TransactionLifecycleError(
                "migration authority was not established by a historical import"
            )
        if run_id in imported_runs:
            first = rows[0]
            for row in rows:
                if (
                    row["migration_batch_id"] != first["migration_batch_id"]
                    or row["migration_member_count"]
                    != first["migration_member_count"]
                    or row["migration_member_digest"]
                    != first["migration_member_digest"]
                    or row["migration_source_slots"]
                    != first["migration_source_slots"]
                ):
                    raise TransactionLifecycleError(
                        "historical migration identity changes within a run"
                    )

    batches: dict[str, list[Mapping[str, Any]]] = {}
    for event in imported_first:
        batches.setdefault(str(event["migration_batch_id"]), []).append(event)
    for batch_id, members in batches.items():
        counts = {member["migration_member_count"] for member in members}
        groups = {member["attempt_group_id"] for member in members}
        digests = {member["migration_member_digest"] for member in members}
        slots = {
            tuple(member["migration_source_slots"])
            for member in members
        }
        if (
            len(counts) != 1
            or next(iter(counts)) != len(members)
            or len(groups) != 1
            or len(digests) != 1
            or len(slots) != 1
            or sorted(member["attempt_number"] for member in members)
            != list(range(1, len(members) + 1))
            or next(iter(digests)) != _migration_members_digest(members)
        ):
            raise TransactionLifecycleError(
                f"historical migration batch {batch_id} is incomplete or mismatched"
            )
        group = next(iter(groups))
        ordinary_group_runs = {
            str(event["run_id"])
            for event in events
            if event["attempt_group_id"] == group
            and event["run_id"] not in imported_runs
        }
        if ordinary_group_runs:
            current = _latest(events)
            if any(
                current[str(member["run_id"])]["state"] not in TERMINAL_STATES
                for member in members
            ):
                raise TransactionLifecycleError(
                    "ordinary retry exists before historical group closure"
                )
            for run_id in ordinary_group_runs:
                rows = by_run[run_id]
                first = rows[0]
                authorization = first["retry_authorization"]
                if (
                    first["event_type"] != "retry_claimed"
                    or not authorization
                    or authorization["predecessor_run_id"] not in imported_runs
                ):
                    raise TransactionLifecycleError(
                        "ordinary and historical transactions share one attempt group"
                    )

    current = _latest(events)
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in current.values():
        if (
            row["logical_worktree_id"] is not None
            and row["state"] not in TERMINAL_STATES
        ):
            groups.setdefault(str(row["attempt_group_id"]), []).append(row)
    for rows in groups.values():
        if len(rows) <= 1:
            continue
        batch_ids = {row["migration_batch_id"] for row in rows}
        if None in batch_ids or len(batch_ids) != 1:
            raise TransactionLifecycleError(
                "attempt group has more than one live runtime worktree"
            )


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    _assert_owner_regular_file(path)
    events = _parse_events(path.read_text(encoding="utf-8"))
    _validate_history_sequences(events)
    _validate_global_history(events)
    return events


def _validate_append_sequence(
    existing: Sequence[Mapping[str, Any]], candidate: Mapping[str, Any]
) -> None:
    """Enforce per-run sequencing and one-use retry claims while locked."""
    run_events = [row for row in existing if row["run_id"] == candidate["run_id"]]
    expected_sequence = len(run_events) + 1
    suffix = int(str(candidate["event_id"]).rsplit(":", 1)[1])
    if suffix != expected_sequence:
        raise TransactionLifecycleError("transaction event sequence is not contiguous")
    if expected_sequence == 1 and candidate["event_type"] not in {
        "started",
        "retry_claimed",
        "historical_imported",
    }:
        raise TransactionLifecycleError("a transaction run must begin with a start event")
    if expected_sequence > 1 and candidate["event_type"] in {"started", "retry_claimed"}:
        raise TransactionLifecycleError("a transaction run cannot have a second start event")
    authorization = candidate.get("retry_authorization")
    if candidate["event_type"] == "retry_claimed":
        if not authorization:
            raise TransactionLifecycleError("retry claim requires an authorization")
        authorization_id = authorization["authorization_id"]
        if any(
            row["event_type"] == "retry_claimed"
            and row["retry_authorization"]
            and row["retry_authorization"]["authorization_id"] == authorization_id
            for row in existing
        ):
            raise TransactionLifecycleError("retry authorization is already used")


def _validate_history_sequences(events: Sequence[Mapping[str, Any]]) -> None:
    """Reject a pre-existing event history whose run sequences are malformed."""
    by_run: dict[str, list[Mapping[str, Any]]] = {}
    for event in events:
        by_run.setdefault(str(event["run_id"]), []).append(event)
    for run_events in by_run.values():
        for expected, event in enumerate(run_events, 1):
            suffix = int(str(event["event_id"]).rsplit(":", 1)[1])
            if suffix != expected:
                raise TransactionLifecycleError("transaction history sequence is malformed")
            if expected == 1 and event["event_type"] not in {
                "started",
                "retry_claimed",
                "historical_imported",
            }:
                raise TransactionLifecycleError("transaction history lacks a start event")

def _assert_owner_regular_file(path: Path) -> None:
    """Reject a symlink, special file, unsafe mode, or unexpected owner."""
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise TransactionLifecycleError("transaction event log must be a regular non-symlink file")
    if metadata.st_uid != os.getuid() or metadata.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise TransactionLifecycleError("transaction event log is not owner-only")


def _append(path: Path, event: Mapping[str, Any]) -> dict[str, Any]:
    """Append a validated event under an exclusive owner-only file lock."""
    valid = validate_event(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise TransactionLifecycleError("transaction event log parent cannot be a symlink")
    existed = path.exists()
    flags = os.O_RDWR | os.O_APPEND | os.O_CREAT
    if not existed:
        flags |= os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        # Another writer created the log between the observation and open.
        # Re-enter through the existing-file path and validate under its lock.
        return _append(path, event)
    except OSError as exc:
        raise TransactionLifecycleError("transaction event log cannot be opened safely") from exc
    try:
        if existed:
            _assert_owner_regular_file(path)
        else:
            os.fchmod(descriptor, 0o600)
            _assert_owner_regular_file(path)
        with os.fdopen(descriptor, "a", encoding="utf-8", closefd=False) as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                opened = os.fstat(handle.fileno())
                named = path.lstat()
                if (opened.st_dev, opened.st_ino) != (named.st_dev, named.st_ino):
                    raise TransactionLifecycleError("transaction event path changed during locked append")
                os.lseek(handle.fileno(), 0, os.SEEK_SET)
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(handle.fileno(), 65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                existing = _parse_events(b"".join(chunks).decode("utf-8"))
                _validate_history_sequences(existing)
                if valid["event_id"] in {row["event_id"] for row in existing}:
                    raise TransactionLifecycleError("event ID already exists")
                _validate_append_sequence(existing, valid)
                # Recheck global live-worktree invariant while serialized.
                transaction_projection([*existing, valid])
                handle.write(json.dumps(valid, sort_keys=True, separators=(",", ":")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        os.close(descriptor)
    return valid

def _latest(events: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in events:
        run_id = str(event["run_id"])
        if event["event_type"] != "retry_authorized": latest[run_id] = dict(event)
    return latest

def _event(run_id: str, sequence: int, *, group: str, attempt: int, event_type: str, state: str, now: datetime | None, **overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {"schema_version": 1, "event_id": f"{run_id}:{sequence:04d}", "run_id": run_id, "attempt_group_id": group, "attempt_number": attempt, "event_type": event_type, "recorded_at": iso_utc(now), "state": state, "trigger": "scheduled", "branch": "unknown", "head": "unknown", "base": "unknown", "logical_worktree_id": None, "logical_run_id": run_id, "delta_digest": "sha256:" + "0" * 64, "package_digest": None, "failure_code": None, "incident_id": None, "owner": "owner", "next_action": "Review transaction lifecycle.", "evidence_refs": [], "predecessor_run_id": None, "predecessor_terminal_digest": None, "retry_authorization": None, "terminal_proof": None, "recovery_proof": None, "migration_batch_id": None, "migration_member_count": None, "migration_member_digest": None, "migration_source_slots": [], "event_sha256": None}
    value.update(overrides); return value


MIGRATION_MEMBER_FIELDS = frozenset(
    {
        "run_id",
        "attempt_number",
        "branch",
        "head",
        "base",
        "logical_worktree_id",
        "logical_run_id",
        "delta_digest",
        "package_digest",
        "recovery_proof",
        "evidence_refs",
        "incident_id",
    }
)


def import_preexisting_attempt_group(
    path: Path,
    *,
    migration_batch_id: str,
    attempt_group_id: str,
    source_slots: Sequence[str],
    members: Sequence[Mapping[str, Any]],
    owner: str,
    next_action: str,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Atomically install one complete migration-only historical batch."""

    existing_authority = path.exists()
    if existing_authority and len(members) != 1:
        raise TransactionLifecycleError(
            "multi-member historical migration requires an absent authority"
        )
    batch_id = _identity(migration_batch_id, "migration_batch_id")
    group_id = _identity(attempt_group_id, "attempt_group_id")
    slots = sorted(
        {str(_text(slot, "migration_source_slot")) for slot in source_slots}
    )
    if not slots:
        raise TransactionLifecycleError(
            "historical migration requires recorded source slots"
        )
    if not members:
        raise TransactionLifecycleError(
            "historical migration requires at least one member"
        )
    imported: list[dict[str, Any]] = []
    for member in members:
        if (
            not isinstance(member, Mapping)
            or frozenset(member) != MIGRATION_MEMBER_FIELDS
        ):
            raise TransactionLifecycleError(
                "historical migration member fields do not match the contract"
            )
        imported.append(
            _event(
                _identity(member["run_id"], "run_id"),
                1,
                group=group_id,
                attempt=member["attempt_number"],
                event_type="historical_imported",
                state="recovery_packaged",
                now=now,
                trigger="historical-migration",
                branch=member["branch"],
                head=member["head"],
                base=member["base"],
                logical_worktree_id=member["logical_worktree_id"],
                logical_run_id=member["logical_run_id"],
                delta_digest=member["delta_digest"],
                package_digest=member["package_digest"],
                failure_code=(
                    "preexisting-multi-live-group"
                    if len(members) > 1
                    else "preexisting-retained-transaction"
                ),
                incident_id=member["incident_id"],
                owner=owner,
                next_action=next_action,
                evidence_refs=list(member["evidence_refs"]),
                recovery_proof=member["recovery_proof"],
                migration_batch_id=batch_id,
                migration_member_count=len(members),
                migration_member_digest="sha256:" + "0" * 64,
                migration_source_slots=slots,
            )
        )
    if len({event["run_id"] for event in imported}) != len(imported):
        raise TransactionLifecycleError("historical migration has duplicate run IDs")
    member_digest = _migration_members_digest(imported)
    validated = []
    for event in imported:
        event["migration_member_digest"] = member_digest
        validated.append(validate_event(event))
    _validate_history_sequences(validated)
    _validate_global_history(validated)
    if existing_authority:
        return [_append(path, validated[0])]

    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise TransactionLifecycleError(
            "transaction lifecycle parent must be a regular directory"
        )
    os.chmod(path.parent, 0o700)
    payload = "".join(
        json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
        for event in validated
    ).encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(
        prefix=".transaction-events.",
        dir=path.parent,
    )
    try:
        os.fchmod(descriptor, 0o600)
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise TransactionLifecycleError(
                    "historical migration staging write was incomplete"
                )
            offset += written
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError as error:
            raise TransactionLifecycleError(
                "historical migration cannot replace lifecycle history"
            ) from error
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        read_events(path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return validated


def import_historical_terminal_run(
    path: Path,
    *,
    migration_batch_id: str,
    attempt_group_id: str,
    source_slot: str,
    run_id: str,
    attempt_number: int,
    trigger: str,
    branch: str,
    head: str,
    base: str,
    logical_run_id: str,
    delta_digest: str,
    state: str,
    terminal_proof: Mapping[str, str],
    owner: str,
    next_action: str,
    incident_id: str | None = None,
    evidence_refs: Sequence[str] = (),
    now: datetime | None = None,
) -> dict[str, Any]:
    """Append one explicitly terminal legacy run that never had a worktree."""
    if state not in {"completed_noop", "completed_published"}:
        raise TransactionLifecycleError(
            "historical terminal import requires a completed terminal state"
        )
    event = _event(
        _identity(run_id, "run_id"),
        1,
        group=_identity(attempt_group_id, "attempt_group_id"),
        attempt=attempt_number,
        event_type="historical_imported",
        state=state,
        now=now,
        trigger=trigger,
        branch=branch,
        head=head,
        base=base,
        logical_worktree_id=None,
        logical_run_id=logical_run_id,
        delta_digest=delta_digest,
        incident_id=incident_id,
        owner=owner,
        next_action=next_action,
        evidence_refs=list(evidence_refs),
        terminal_proof=terminal_proof,
        migration_batch_id=_identity(migration_batch_id, "migration_batch_id"),
        migration_member_count=1,
        migration_member_digest="sha256:" + "0" * 64,
        migration_source_slots=[str(_text(source_slot, "migration_source_slot"))],
    )
    event["migration_member_digest"] = _migration_members_digest([event])
    return _append(path, event)


def start_transaction(path: Path, *, run_id: str, attempt_group_id: str, attempt_number: int, trigger: str, branch: str, head: str, base: str, logical_worktree_id: str | None, logical_run_id: str, delta_digest: str, owner: str, next_action: str, incident_id: str | None = None, retry_authorization: Mapping[str, str] | None = None, now: datetime | None = None) -> dict[str, Any]:
    events = read_events(path); latest = _latest(events)
    if run_id in latest: raise TransactionLifecycleError("run_id is already immutable history")
    auth = _authorization(retry_authorization)
    if attempt_number == 1 and auth is not None: raise TransactionLifecycleError("primary attempt cannot claim retry authorization")
    if attempt_number > 1:
        if auth is None: raise TransactionLifecycleError("linked retry requires authorization")
        if any(e["event_type"] == "retry_claimed" and e["retry_authorization"] and e["retry_authorization"]["authorization_id"] == auth["authorization_id"] for e in events): raise TransactionLifecycleError("retry authorization is already used")
        if iso_utc(now) > auth["expires_at"]: raise TransactionLifecycleError("retry authorization has expired")
        predecessor = latest.get(auth["predecessor_run_id"])
        if not predecessor or predecessor["attempt_group_id"] != attempt_group_id or predecessor["state"] not in RESOLVED_PREDECESSOR_STATES or predecessor["event_sha256"] != auth["predecessor_terminal_digest"]: raise TransactionLifecycleError("retry predecessor is unresolved or authorization binding is stale")
    live = [
        event
        for event in latest.values()
        if event["attempt_group_id"] == attempt_group_id
        and event["logical_worktree_id"] is not None
        and event["state"] not in TERMINAL_STATES
    ]
    if live: raise TransactionLifecycleError("attempt group already has a live runtime worktree")
    group_history = [
        event
        for event in events
        if event["attempt_group_id"] == attempt_group_id
        and event["event_type"] != "retry_authorized"
    ]
    if attempt_number == 1 and group_history:
        raise TransactionLifecycleError("attempt group already has immutable history")
    sequence = sum(1 for e in events if e["run_id"] == run_id) + 1
    event = _event(run_id, sequence, group=attempt_group_id, attempt=attempt_number, event_type="retry_claimed" if auth else "started", state="active", now=now, trigger=trigger, branch=branch, head=head, base=base, logical_worktree_id=logical_worktree_id, logical_run_id=logical_run_id, delta_digest=delta_digest, owner=owner, next_action=next_action, incident_id=incident_id, predecessor_run_id=auth["predecessor_run_id"] if auth else None, predecessor_terminal_digest=auth["predecessor_terminal_digest"] if auth else None, retry_authorization=auth)
    return _append(path, event)

def transition_transaction(path: Path, *, run_id: str, state: str, owner: str, next_action: str, failure_code: str | None = None, terminal_proof: Mapping[str, str] | None = None, recovery_proof: Mapping[str, str] | None = None, package_digest: str | None = None, incident_id: str | None = None, now: datetime | None = None) -> dict[str, Any]:
    events = read_events(path); current = _latest(events).get(run_id)
    if not current: raise TransactionLifecycleError("unknown transaction run")
    if current["state"] in TERMINAL_STATES: raise TransactionLifecycleError("terminal transaction cannot transition")
    abandoned = current["state"] == "active" and state == "recovery_pending" and failure_code == "abandoned-released-lock"
    retained_live = current["state"] == "active" and state == "recovery_pending" and failure_code == "retained-live-worktree"
    if not (abandoned or retained_live) and state not in ALLOWED_TRANSITIONS.get(current["state"], frozenset()):
        raise TransactionLifecycleError("transaction state transition is not permitted")
    sequence = sum(1 for e in events if e["run_id"] == run_id) + 1
    return _append(path, _event(run_id, sequence, group=current["attempt_group_id"], attempt=current["attempt_number"], event_type="abandoned" if abandoned else "state_changed", state=state, now=now, trigger=current["trigger"], branch=current["branch"], head=current["head"], base=current["base"], logical_worktree_id=current["logical_worktree_id"], logical_run_id=current["logical_run_id"], delta_digest=current["delta_digest"], owner=owner, next_action=next_action, failure_code=failure_code, package_digest=package_digest, terminal_proof=terminal_proof, recovery_proof=recovery_proof, incident_id=incident_id or current["incident_id"], predecessor_run_id=current["predecessor_run_id"], predecessor_terminal_digest=current["predecessor_terminal_digest"], retry_authorization=current["retry_authorization"], migration_batch_id=current["migration_batch_id"], migration_member_count=current["migration_member_count"], migration_member_digest=current["migration_member_digest"], migration_source_slots=current["migration_source_slots"]))

def authorize_retry(path: Path, *, predecessor_run_id: str, owner: str, expires_at: str, now: datetime | None = None) -> dict[str, Any]:
    events = read_events(path); predecessor = _latest(events).get(predecessor_run_id)
    if not predecessor or predecessor["state"] not in RESOLVED_PREDECESSOR_STATES: raise TransactionLifecycleError("retry predecessor has no resolved or sealed disposition")
    if predecessor["migration_batch_id"] is not None:
        current = _latest(events)
        if any(
            row["migration_batch_id"] == predecessor["migration_batch_id"]
            and row["state"] not in TERMINAL_STATES
            for row in current.values()
        ):
            raise TransactionLifecycleError(
                "historical attempt group remains live and cannot authorize retry"
            )
    auth = {"authorization_id": f"retry:{predecessor_run_id}:{len(events)+1}", "predecessor_run_id": predecessor_run_id, "predecessor_terminal_digest": predecessor["event_sha256"], "expires_at": expires_at}
    _authorization(auth)
    event = _event(predecessor_run_id, sum(1 for e in events if e["run_id"] == predecessor_run_id) + 1, group=predecessor["attempt_group_id"], attempt=predecessor["attempt_number"], event_type="retry_authorized", state=predecessor["state"], now=now, trigger=predecessor["trigger"], branch=predecessor["branch"], head=predecessor["head"], base=predecessor["base"], logical_worktree_id=predecessor["logical_worktree_id"], logical_run_id=predecessor["logical_run_id"], delta_digest=predecessor["delta_digest"], owner=owner, next_action="Claim the linked retry before authorization expiry.", incident_id=predecessor["incident_id"], predecessor_run_id=predecessor_run_id, predecessor_terminal_digest=predecessor["event_sha256"], retry_authorization=auth, terminal_proof=predecessor["terminal_proof"], recovery_proof=predecessor["recovery_proof"], package_digest=predecessor["package_digest"], migration_batch_id=predecessor["migration_batch_id"], migration_member_count=predecessor["migration_member_count"], migration_member_digest=predecessor["migration_member_digest"], migration_source_slots=predecessor["migration_source_slots"])
    _append(path, event); return auth

def mark_abandoned_transactions(path: Path, *, released_lock_run_ids: Sequence[str], owner: str, now: datetime | None = None) -> list[dict[str, Any]]:
    events = read_events(path); current = _latest(events); records = []
    for run_id in released_lock_run_ids:
        row = current.get(run_id)
        if row is None or row["state"] in TERMINAL_STATES | {"recovery_pending"}:
            continue
        records.append(transition_transaction(path, run_id=run_id, state="recovery_pending", owner=owner, next_action="Recover or package preserved transaction material.", failure_code="abandoned-released-lock", incident_id=row["incident_id"], now=now))
    return records

def transaction_projection(events: Sequence[Mapping[str, Any]], *, now: datetime | None = None) -> dict[str, Any]:
    validated = [validate_event(event) for event in events]
    _validate_history_sequences(validated)
    _validate_global_history(validated)
    current = _latest(validated)
    unresolved = [row for row in current.values() if row["state"] not in TERMINAL_STATES]
    reference = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    items = []
    for row in sorted(unresolved, key=lambda item: item["run_id"]):
        started = datetime.strptime(row["recorded_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        items.append({"run_id": row["run_id"], "attempt_group_id": row["attempt_group_id"], "attempt_number": row["attempt_number"], "state": row["state"], "owner": row["owner"], "age_seconds": max(0, int((reference - started).total_seconds())), "failure_code": row["failure_code"], "next_action": row["next_action"]})
    return {"schema_version": 1, "authority": "owner-local-transaction-lifecycle", "complete": True, "unresolved_count": len(unresolved), "items": items}

def project_transaction_log(path: Path) -> dict[str, Any]:
    return transaction_projection(read_events(path))


def current_transaction_states(path: Path) -> dict[str, dict[str, Any]]:
    """Return validated latest immutable events for owner-local coordination."""
    return _latest(read_events(path))


def build_console_projection(
    events: Sequence[Mapping[str, Any]], *, now: datetime | None = None
) -> dict[str, Any]:
    """Build the strict, public-safe owner Console transaction queue view."""
    source = transaction_projection(events, now=now)
    reference = iso_utc(now)
    items = []
    for row in source["items"]:
        if row["state"] not in {
            "active", "failed_preserved", "recovery_pending",
            "reconciled_or_superseded", "recovery_packaged",
        }:
            continue
        days = row["age_seconds"] // 86400
        items.append({
            "run_id": row["run_id"],
            "attempt_group_id": row["attempt_group_id"],
            "lifecycle_state": row["state"],
            "preserved": row["state"] != "active",
            "retirement_proof": "not_retired",
            "owner": row["owner"],
            "age_label": f"{days}d",
            "failure_class": row["failure_code"] or "none",
            "next_action": row["next_action"],
            "specialist_route": "automation:agents:run-coordinator-bot",
        })
    return {
        "schema_version": 1,
        "availability": "current",
        "complete": True,
        "generated_at": reference,
        "items": items,
        "reason_code": None,
    }

def validate_recovery_package_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    expected = {"schema_version", "recovery_package_id", "run_id", "created_at", "branch", "head", "base", "commit_digest", "diff_digest", "untracked_digest", "package_digest", "manifest_sha256"}
    if not isinstance(manifest, Mapping) or set(manifest) != expected or manifest["schema_version"] != 1: raise TransactionLifecycleError("invalid recovery package manifest fields or schema")
    value = dict(manifest)
    if not re.fullmatch(r"trp:[A-Za-z][A-Za-z0-9_.:-]{0,127}", str(value["recovery_package_id"])): raise TransactionLifecycleError("invalid recovery package identity")
    value["run_id"] = _identity(value["run_id"], "run_id"); value["created_at"] = _timestamp(value["created_at"], "created_at")
    for field in ("branch", "head", "base"):
        value[field] = str(_text(value[field], field))
    for field in ("commit_digest", "diff_digest", "untracked_digest", "package_digest"): value[field] = str(_digest(value[field], field))
    expected_hash = _hash(value, "manifest_sha256")
    if value["manifest_sha256"] not in (None, expected_hash): raise TransactionLifecycleError("recovery package manifest hash mismatch")
    value["manifest_sha256"] = expected_hash; return value


def inventory_transaction_material(
    *,
    run_id: str,
    branch: str,
    head: str,
    base: str,
    commit_bundle: bytes,
    diff: bytes,
    untracked: Mapping[str, bytes],
) -> dict[str, Any]:
    """Return a deterministic, path-free inventory for a recovery package.

    The caller supplies Git-derived bytes; this function never invokes Git or
    inspects a worktree.  Untracked names are logical relative names only.
    """
    run_id = _identity(run_id, "run_id")
    for field, value in (("branch", branch), ("head", head), ("base", base)):
        _text(value, field)
    if not isinstance(commit_bundle, bytes) or not isinstance(diff, bytes):
        raise TransactionLifecycleError("recovery inputs must be immutable bytes")
    rows = []
    for name, content in sorted(untracked.items()):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,191}", name) or name.startswith("/") or ".." in name.split("/"):
            raise TransactionLifecycleError("untracked recovery names must be safe relative names")
        if not isinstance(content, bytes):
            raise TransactionLifecycleError("untracked recovery content must be bytes")
        rows.append({"name": name, "digest": "sha256:" + hashlib.sha256(content).hexdigest(), "size": len(content)})
    untracked_index = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return {
        "run_id": run_id,
        "branch": str(branch),
        "head": str(head),
        "base": str(base),
        "commit_digest": "sha256:" + hashlib.sha256(commit_bundle).hexdigest(),
        "diff_digest": "sha256:" + hashlib.sha256(diff).hexdigest(),
        "untracked_digest": "sha256:" + hashlib.sha256(untracked_index).hexdigest(),
        "untracked_entries": rows,
    }


def create_recovery_package(
    recovery_root: Path,
    *,
    run_id: str,
    branch: str,
    head: str,
    base: str,
    commit_bundle: bytes,
    diff: bytes,
    untracked: Mapping[str, bytes],
    now: datetime | None = None,
) -> dict[str, Any]:
    """Create one owner-only non-checkout package; never retire source state."""
    inventory = inventory_transaction_material(
        run_id=run_id, branch=branch, head=head, base=base,
        commit_bundle=commit_bundle, diff=diff, untracked=untracked,
    )
    recovery_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if recovery_root.is_symlink() or not recovery_root.is_dir():
        raise TransactionLifecycleError("recovery root must be a non-symlink directory")
    os.chmod(recovery_root, 0o700)
    package_seed = "|".join((inventory["run_id"], inventory["commit_digest"], inventory["diff_digest"], inventory["untracked_digest"]))
    package_id = "trp:" + inventory["run_id"] + ":" + hashlib.sha256(package_seed.encode()).hexdigest()[:16]
    package_path = recovery_root / package_id.replace(":", "-")
    if package_path.exists():
        raise TransactionLifecycleError("recovery package already exists and is immutable")
    package_path.mkdir(mode=0o700)
    try:
        artifacts = {
            "commits.bundle": commit_bundle,
            "delta.patch": diff,
            "untracked-index.json": json.dumps(inventory["untracked_entries"], sort_keys=True, separators=(",", ":")).encode(),
        }
        for name, content in untracked.items():
            target = package_path / "untracked" / name
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            target.write_bytes(content)
            os.chmod(target, 0o600)
        for name, content in artifacts.items():
            target = package_path / name
            target.write_bytes(content)
            os.chmod(target, 0o600)
        package_digest = "sha256:" + hashlib.sha256(
            "|".join((inventory["commit_digest"], inventory["diff_digest"], inventory["untracked_digest"])).encode()
        ).hexdigest()
        manifest = {
            "schema_version": 1,
            "recovery_package_id": package_id,
            "run_id": inventory["run_id"],
            "created_at": iso_utc(now),
            "branch": inventory["branch"],
            "head": inventory["head"],
            "base": inventory["base"],
            "commit_digest": inventory["commit_digest"],
            "diff_digest": inventory["diff_digest"],
            "untracked_digest": inventory["untracked_digest"],
            "package_digest": package_digest,
            "manifest_sha256": None,
        }
        manifest = validate_recovery_package_manifest(manifest)
        (package_path / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        os.chmod(package_path / "manifest.json", 0o400)
        for item in package_path.rglob("*"):
            if item.is_file(): os.chmod(item, 0o400)
            elif item.is_dir(): os.chmod(item, 0o500)
        os.chmod(package_path, 0o500)
    except Exception:
        # Do not delete a partly preserved package; leave it for recovery review.
        raise
    return manifest
