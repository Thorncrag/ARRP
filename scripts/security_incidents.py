#!/usr/bin/env python3
"""Owner-local Security Incident event authority and fixture projection tools.

This module deliberately has no production path or writer activation.  Its
filesystem functions operate only on an explicitly supplied path, and its CLI
accepts only an injected ``ProjectPathAuthority.fixture``.  A future live
producer must bind the owner-local authority separately before calling these
functions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from path_authority import PathAuthorityError, ProjectPathAuthority
except ModuleNotFoundError:
    from scripts.path_authority import PathAuthorityError, ProjectPathAuthority


EVENT_SCHEMA_VERSION = 1
PROJECTION_SCHEMA_VERSION = 1
RELATION_EVENT_SCHEMA_VERSION = 1
RELATION_PROJECTION_SCHEMA_VERSION = 1

LIFECYCLE = (
    "Open",
    "Investigating",
    "Contained",
    "Remediating",
    "Monitoring",
    "Resolved",
)
UNRESOLVED_STATES = frozenset(LIFECYCLE[:-1])
EVENT_TYPES = frozenset(
    {
        "opened",
        "occurrence",
        "status_changed",
        "ownership_updated",
        "resolved",
    }
)
RELATION_EVENT_TYPES = frozenset({"linked", "unlinked"})

SECURITY_INCIDENT_ID = re.compile(r"^SEC-(\d{4})-(\d{3,})$")
OPERATIONAL_INCIDENT_ID = re.compile(r"^INC-(\d{4})-(\d{3,})$")
TYPED_IDENTITY = re.compile(r"^[a-z][a-z0-9_.:-]{0,127}$")
OPAQUE_EVIDENCE_REFERENCE = re.compile(
    r"^(?:restricted:security-evidence|provider-native:security)/"
    r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
)
UTC_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)

MAX_SAFE_TEXT = 1024
MAX_REFERENCES = 64
MAX_OCCURRENCES = 256

SECRET_PATTERNS = (
    re.compile(
        r"\b(?:gh[opusr]_[A-Za-z0-9_]{16,}|"
        r"github_pat_[A-Za-z0-9_]{16,})\b"
    ),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(
        r"(?i)\b(?:token|password|secret|private[_ -]?key|authorization)"
        r"\s*[:=]\s*\S+"
    ),
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?"
        r"-----END [A-Z ]*PRIVATE KEY-----",
        re.S,
    ),
    re.compile(
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\."
        r"[A-Za-z0-9_-]{8,}\b"
    ),
    re.compile(
        r"(?i)https?://[^\s?]+\?[^\s]*(?:token|secret|signature|sig|key)="
    ),
)

SECURITY_EVENT_FIELDS = frozenset(
    {
        "schema_version",
        "event_id",
        "security_incident_id",
        "event_type",
        "recorded_at",
        "identity_key",
        "security_domain",
        "protected_surface",
        "event_class",
        "safe_summary",
        "status",
        "reported_by",
        "owner",
        "recommended_owner",
        "next_action",
        "occurrence",
        "restricted_evidence_refs",
        "closure",
        "prior_security_incident_id",
        "event_sha256",
    }
)
OCCURRENCE_FIELDS = frozenset(
    {
        "occurrence_id",
        "observed_at",
        "source_ref",
        "safe_observation",
    }
)
CLOSURE_FIELDS = frozenset(
    {
        "verified_at",
        "disposition_code",
        "closure_test",
        "result",
        "recorded_by",
        "restricted_evidence_refs",
    }
)
RELATION_EVENT_FIELDS = frozenset(
    {
        "schema_version",
        "relation_event_id",
        "relation_id",
        "event_type",
        "recorded_at",
        "operational_incident_id",
        "security_incident_id",
        "relationship_type",
        "recorded_by",
        "safe_summary",
        "event_sha256",
    }
)


class SecurityIncidentContractError(ValueError):
    """Raised when a Security Incident record violates the contract."""


def _utc_datetime(value: datetime | None = None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise SecurityIncidentContractError("incident time must be timezone-aware")
    return current.astimezone(timezone.utc)


def iso_utc(value: datetime | None = None) -> str:
    return _utc_datetime(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def validate_timestamp(value: object, *, field: str) -> str:
    text = str(value or "")
    if not UTC_TIMESTAMP.fullmatch(text):
        raise SecurityIncidentContractError(
            f"{field} must be a canonical UTC timestamp"
        )
    try:
        datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise SecurityIncidentContractError(
            f"{field} must be a valid UTC timestamp"
        ) from error
    return text


def safe_text(value: object, *, required: bool = False) -> str:
    text = " ".join(str(value or "").replace("\x00", " ").split())
    if len(text) > MAX_SAFE_TEXT:
        raise SecurityIncidentContractError("safe incident text exceeds its maximum")
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        raise SecurityIncidentContractError(
            "security incident text contains prohibited secret-shaped material"
        )
    if required and not text:
        raise SecurityIncidentContractError("required safe incident text is empty")
    return text


def typed_identity(value: object, *, field: str) -> str:
    text = safe_text(value, required=True)
    if not TYPED_IDENTITY.fullmatch(text):
        raise SecurityIncidentContractError(
            f"{field} must be a registered lower-case typed identity"
        )
    return text


def opaque_evidence_reference(value: object) -> str:
    reference = safe_text(value, required=True)
    if not OPAQUE_EVIDENCE_REFERENCE.fullmatch(reference):
        raise SecurityIncidentContractError(
            "security evidence must use an opaque restricted reference"
        )
    return reference


def _bounded_references(value: object) -> list[str]:
    if not isinstance(value, list) or len(value) > MAX_REFERENCES:
        raise SecurityIncidentContractError(
            "restricted_evidence_refs must be a bounded array"
        )
    return [opaque_evidence_reference(item) for item in value]


def security_identity_key(
    security_domain: object,
    protected_surface: object,
    event_class: object,
) -> str:
    fields = (
        typed_identity(security_domain, field="security_domain"),
        typed_identity(protected_surface, field="protected_surface"),
        typed_identity(event_class, field="event_class"),
    )
    return "sha256:" + hashlib.sha256("|".join(fields).encode("utf-8")).hexdigest()


def _security_event_hash(event: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key != "event_sha256"}
    return "sha256:" + hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _relation_event_hash(event: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key != "event_sha256"}
    return "sha256:" + hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _validate_exact_fields(
    value: Mapping[str, Any],
    expected: frozenset[str],
    *,
    record_type: str,
) -> None:
    supplied = frozenset(value)
    if supplied != expected:
        raise SecurityIncidentContractError(
            f"{record_type} fields do not match the deny-by-default contract"
        )


def validate_security_event(event: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(event, Mapping):
        raise SecurityIncidentContractError("security incident event must be an object")
    value = dict(event)
    _validate_exact_fields(
        value,
        SECURITY_EVENT_FIELDS,
        record_type="security incident event",
    )
    if value["schema_version"] != EVENT_SCHEMA_VERSION:
        raise SecurityIncidentContractError(
            "unsupported security incident event schema"
        )
    incident_id = str(value["security_incident_id"] or "")
    if not SECURITY_INCIDENT_ID.fullmatch(incident_id):
        raise SecurityIncidentContractError("invalid Security Incident ID")
    if value["event_type"] not in EVENT_TYPES:
        raise SecurityIncidentContractError(
            "invalid Security Incident event type"
        )
    expected_event_prefix = f"{incident_id}:"
    if not str(value["event_id"] or "").startswith(expected_event_prefix):
        raise SecurityIncidentContractError(
            "Security Incident event ID is not scoped to its incident"
        )
    event_suffix = str(value["event_id"])[len(expected_event_prefix) :]
    if not re.fullmatch(r"\d{4,}", event_suffix):
        raise SecurityIncidentContractError("invalid Security Incident event ID")
    if value["status"] not in LIFECYCLE:
        raise SecurityIncidentContractError(
            "invalid Security Incident lifecycle state"
        )

    value["recorded_at"] = validate_timestamp(
        value["recorded_at"],
        field="recorded_at",
    )
    value["security_domain"] = typed_identity(
        value["security_domain"],
        field="security_domain",
    )
    value["protected_surface"] = typed_identity(
        value["protected_surface"],
        field="protected_surface",
    )
    value["event_class"] = typed_identity(
        value["event_class"],
        field="event_class",
    )
    expected_identity = security_identity_key(
        value["security_domain"],
        value["protected_surface"],
        value["event_class"],
    )
    if value["identity_key"] != expected_identity:
        raise SecurityIncidentContractError(
            "Security Incident identity does not match its typed fields"
        )

    for field in (
        "safe_summary",
        "reported_by",
        "recommended_owner",
        "next_action",
    ):
        value[field] = safe_text(value[field], required=True)
    value["owner"] = safe_text(value["owner"]) or None
    value["restricted_evidence_refs"] = _bounded_references(
        value["restricted_evidence_refs"]
    )

    prior_id = value["prior_security_incident_id"]
    if prior_id is not None:
        prior_id = str(prior_id)
        if not SECURITY_INCIDENT_ID.fullmatch(prior_id) or prior_id == incident_id:
            raise SecurityIncidentContractError(
                "invalid prior Security Incident reference"
            )
    value["prior_security_incident_id"] = prior_id

    occurrence = value["occurrence"]
    if occurrence is not None:
        if not isinstance(occurrence, Mapping):
            raise SecurityIncidentContractError(
                "security occurrence must be an object or null"
            )
        occurrence = dict(occurrence)
        _validate_exact_fields(
            occurrence,
            OCCURRENCE_FIELDS,
            record_type="security occurrence",
        )
        occurrence["occurrence_id"] = safe_text(
            occurrence["occurrence_id"],
            required=True,
        )
        occurrence["observed_at"] = validate_timestamp(
            occurrence["observed_at"],
            field="observed_at",
        )
        occurrence["source_ref"] = opaque_evidence_reference(
            occurrence["source_ref"]
        )
        occurrence["safe_observation"] = safe_text(
            occurrence["safe_observation"],
            required=True,
        )
        value["occurrence"] = occurrence

    closure = value["closure"]
    if value["event_type"] == "resolved":
        if value["status"] != "Resolved" or not isinstance(closure, Mapping):
            raise SecurityIncidentContractError(
                "resolution requires exact closure evidence"
            )
        closure = dict(closure)
        _validate_exact_fields(
            closure,
            CLOSURE_FIELDS,
            record_type="security closure evidence",
        )
        closure["verified_at"] = validate_timestamp(
            closure["verified_at"],
            field="verified_at",
        )
        closure["disposition_code"] = typed_identity(
            closure["disposition_code"],
            field="disposition_code",
        )
        for field in ("closure_test", "result", "recorded_by"):
            closure[field] = safe_text(closure[field], required=True)
        closure["restricted_evidence_refs"] = _bounded_references(
            closure["restricted_evidence_refs"]
        )
        if not closure["restricted_evidence_refs"]:
            raise SecurityIncidentContractError(
                "closure evidence requires at least one opaque restricted reference"
            )
        value["closure"] = closure
    elif closure is not None:
        raise SecurityIncidentContractError(
            "only a resolved event may carry closure evidence"
        )
    elif value["status"] == "Resolved":
        raise SecurityIncidentContractError(
            "Resolved status requires a resolved event with closure evidence"
        )

    if value["event_type"] in {"opened", "occurrence"}:
        if value["occurrence"] is None:
            raise SecurityIncidentContractError(
                "opened and occurrence events require an exact occurrence"
            )
    elif value["occurrence"] is not None:
        raise SecurityIncidentContractError(
            "only opened and occurrence events may carry an occurrence"
        )
    if value["event_type"] == "opened" and value["status"] != "Open":
        raise SecurityIncidentContractError(
            "a Security Incident must open in Open state"
        )

    expected_hash = _security_event_hash(value)
    if value["event_sha256"] not in (None, expected_hash):
        raise SecurityIncidentContractError(
            "Security Incident event hash mismatch"
        )
    value["event_sha256"] = expected_hash
    return value


def read_security_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        1,
    ):
        if not raw.strip():
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as error:
            raise SecurityIncidentContractError(
                f"security incident event line {line_number} is invalid JSON"
            ) from error
        events.append(validate_security_event(parsed))
    event_ids = [event["event_id"] for event in events]
    if len(event_ids) != len(set(event_ids)):
        raise SecurityIncidentContractError(
            "duplicate Security Incident event ID"
        )
    return events


def _incident_sort_key(incident_id: str) -> tuple[int, int]:
    match = SECURITY_INCIDENT_ID.fullmatch(incident_id)
    if match is None:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2)))


def next_security_incident_id(
    events: Sequence[Mapping[str, Any]],
    now: datetime,
) -> str:
    year = _utc_datetime(now).year
    sequence = max(
        (
            _incident_sort_key(str(event.get("security_incident_id") or ""))[1]
            for event in events
            if _incident_sort_key(
                str(event.get("security_incident_id") or "")
            )[0]
            == year
        ),
        default=0,
    )
    return f"SEC-{year}-{sequence + 1:03d}"


def _validate_security_stream(
    events: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    validated = [validate_security_event(event) for event in events]
    incident_state: dict[str, dict[str, Any]] = {}
    seen_occurrences: dict[str, set[str]] = {}
    for event in validated:
        incident_id = event["security_incident_id"]
        current = incident_state.get(incident_id)
        event_number = int(event["event_id"].rsplit(":", 1)[1])
        expected_number = 1 if current is None else current["event_number"] + 1
        if event_number != expected_number:
            raise SecurityIncidentContractError(
                f"{incident_id} has a nonsequential event stream"
            )
        if current is None:
            if event["event_type"] != "opened":
                raise SecurityIncidentContractError(
                    f"{incident_id} begins without an opened event"
                )
            prior_id = event["prior_security_incident_id"]
            prior = incident_state.get(prior_id) if prior_id is not None else None
            resolved_same_identity = [
                prior_incident_id
                for prior_incident_id, prior_state in incident_state.items()
                if prior_state["identity_key"] == event["identity_key"]
                and prior_state["status"] == "Resolved"
            ]
            if prior_id is not None and (
                prior is None
                or prior["status"] != "Resolved"
                or prior["identity_key"] != event["identity_key"]
            ):
                raise SecurityIncidentContractError(
                    f"{incident_id} has an invalid recurrence link"
                )
            if resolved_same_identity and prior_id is None:
                raise SecurityIncidentContractError(
                    f"{incident_id} omits its prior resolved recurrence link"
                )
            if (
                resolved_same_identity
                and prior_id
                != max(resolved_same_identity, key=_incident_sort_key)
            ):
                raise SecurityIncidentContractError(
                    f"{incident_id} does not link the latest resolved recurrence"
                )
            current = {
                "identity_key": event["identity_key"],
                "status": event["status"],
                "recorded_at": event["recorded_at"],
                "event_number": event_number,
                "prior_security_incident_id": prior_id,
            }
            incident_state[incident_id] = current
            seen_occurrences[incident_id] = set()
        else:
            if current["status"] == "Resolved":
                raise SecurityIncidentContractError(
                    f"{incident_id} has events after verified resolution"
                )
            if current["identity_key"] != event["identity_key"]:
                raise SecurityIncidentContractError(
                    f"{incident_id} changes deterministic identity"
                )
            if event["recorded_at"] < current["recorded_at"]:
                raise SecurityIncidentContractError(
                    f"{incident_id} event time moves backward"
                )
            if event["event_type"] == "opened":
                raise SecurityIncidentContractError(
                    f"{incident_id} has more than one opened event"
                )
            if (
                event["prior_security_incident_id"]
                != current["prior_security_incident_id"]
            ):
                raise SecurityIncidentContractError(
                    f"{incident_id} changes its recurrence link"
                )
            prior_status = current["status"]
            if (
                event["event_type"] in {"occurrence", "ownership_updated"}
                and event["status"] != prior_status
            ):
                raise SecurityIncidentContractError(
                    f"{incident_id} changes lifecycle through the wrong event type"
                )
            if (
                event["event_type"] == "status_changed"
                and (
                    event["status"] == prior_status
                    or event["status"] == "Resolved"
                )
            ):
                raise SecurityIncidentContractError(
                    f"{incident_id} has an invalid status-change event"
                )
            if event["event_type"] == "resolved" and event["status"] != "Resolved":
                raise SecurityIncidentContractError(
                    f"{incident_id} has an invalid resolved event"
                )
            current.update(
                {
                    "status": event["status"],
                    "recorded_at": event["recorded_at"],
                    "event_number": event_number,
                }
            )
        occurrence = event["occurrence"]
        if occurrence is not None:
            occurrence_id = occurrence["occurrence_id"]
            if occurrence_id in seen_occurrences[incident_id]:
                raise SecurityIncidentContractError(
                    f"{incident_id} repeats an occurrence identity"
                )
            seen_occurrences[incident_id].add(occurrence_id)
            if len(seen_occurrences[incident_id]) > MAX_OCCURRENCES:
                raise SecurityIncidentContractError(
                    f"{incident_id} exceeds its bounded occurrence history"
                )
    unresolved_identity: dict[str, str] = {}
    for incident_id, current in incident_state.items():
        if current["status"] not in UNRESOLVED_STATES:
            continue
        identity_key = current["identity_key"]
        if identity_key in unresolved_identity:
            raise SecurityIncidentContractError(
                "one security identity has multiple unresolved incidents"
            )
        unresolved_identity[identity_key] = incident_id
    return validated


def security_incident_projection(
    events: Sequence[Mapping[str, Any]],
    *,
    checked_at: str | None = None,
) -> dict[str, Any]:
    validated = _validate_security_stream(events)
    incidents: dict[str, dict[str, Any]] = {}
    for event in validated:
        incident_id = event["security_incident_id"]
        current = incidents.get(incident_id)
        if current is None:
            occurrence = event["occurrence"]
            current = {
                "security_incident_id": incident_id,
                "identity_key": event["identity_key"],
                "security_domain": event["security_domain"],
                "protected_surface": event["protected_surface"],
                "event_class": event["event_class"],
                "safe_summary": event["safe_summary"],
                "status": event["status"],
                "reported_by": event["reported_by"],
                "owner": event["owner"],
                "recommended_owner": event["recommended_owner"],
                "next_action": event["next_action"],
                "first_observed": occurrence["observed_at"],
                "last_observed": occurrence["observed_at"],
                "occurrences": [],
                "restricted_evidence_refs": [],
                "closure_evidence": None,
                "events": [],
                "prior_security_incident_id": event[
                    "prior_security_incident_id"
                ],
            }
            incidents[incident_id] = current
        current.update(
            {
                "safe_summary": event["safe_summary"],
                "status": event["status"],
                "reported_by": event["reported_by"],
                "owner": event["owner"],
                "recommended_owner": event["recommended_owner"],
                "next_action": event["next_action"],
            }
        )
        occurrence = event["occurrence"]
        if occurrence is not None:
            current["occurrences"].append(occurrence)
            current["last_observed"] = max(
                current["last_observed"],
                occurrence["observed_at"],
            )
        for reference in event["restricted_evidence_refs"]:
            if reference not in current["restricted_evidence_refs"]:
                current["restricted_evidence_refs"].append(reference)
        if event["closure"] is not None:
            current["closure_evidence"] = event["closure"]
        current["events"].append(event)

    rows = sorted(
        incidents.values(),
        key=lambda item: (
            item["last_observed"],
            _incident_sort_key(item["security_incident_id"]),
        ),
        reverse=True,
    )
    unresolved = [item for item in rows if item["status"] in UNRESOLVED_STATES]
    checked = checked_at or iso_utc()
    checked = validate_timestamp(checked, field="checked_at")
    return {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "authority": "owner-local-security-incidents",
        "availability": "current",
        "complete": True,
        "checked_at": checked,
        "count": len(rows),
        "unresolved_count": len(unresolved),
        "items": rows,
    }


def unavailable_security_projection(reason_code: object) -> dict[str, Any]:
    code = typed_identity(reason_code, field="reason_code")
    return {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "authority": "owner-local-security-incidents",
        "availability": "unavailable",
        "complete": False,
        "checked_at": iso_utc(),
        "count": None,
        "unresolved_count": None,
        "items": [],
        "reason_code": code,
    }


def project_security_incident_log(path: Path) -> dict[str, Any]:
    if not path.exists():
        return unavailable_security_projection("missing-security-incident-feed")
    try:
        return security_incident_projection(read_security_events(path))
    except (OSError, SecurityIncidentContractError):
        return unavailable_security_projection("invalid-security-incident-feed")


def _verify_append_target(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
    ):
        raise SecurityIncidentContractError(
            "Security Incident ledger is not a safe regular owner file"
        )
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise SecurityIncidentContractError(
            "Security Incident ledger permissions are not owner-only"
        )


def _append_json_line(path: Path, value: Mapping[str, Any]) -> None:
    _verify_append_target(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) & 0o077
        ):
            raise SecurityIncidentContractError(
                "Security Incident ledger descriptor is unsafe"
            )
        os.write(
            descriptor,
            (
                json.dumps(value, ensure_ascii=False, sort_keys=True)
                + "\n"
            ).encode("utf-8"),
        )
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def append_security_event(
    path: Path,
    event: Mapping[str, Any],
) -> dict[str, Any]:
    validated = validate_security_event(event)
    existing = read_security_events(path)
    _validate_security_stream(existing)
    for prior in existing:
        if prior["event_id"] != validated["event_id"]:
            continue
        if prior["event_sha256"] == validated["event_sha256"]:
            return prior
        raise SecurityIncidentContractError(
            "Security Incident event ID conflicts with existing history"
        )
    _validate_security_stream([*existing, validated])
    _append_json_line(path, validated)
    return validated


def _open_security_incident(
    projection: Mapping[str, Any],
    identity_key: str,
) -> dict[str, Any] | None:
    matches = [
        item
        for item in projection["items"]
        if item["identity_key"] == identity_key
        and item["status"] in UNRESOLVED_STATES
    ]
    if len(matches) > 1:
        raise SecurityIncidentContractError(
            "one security identity has multiple unresolved incidents"
        )
    return matches[0] if matches else None


def record_security_occurrence(
    path: Path,
    *,
    security_domain: object,
    protected_surface: object,
    event_class: object,
    safe_summary: object,
    reported_by: object,
    owner: object,
    recommended_owner: object,
    next_action: object,
    occurrence_id: object,
    observed_at: object,
    source_ref: object,
    safe_observation: object,
    restricted_evidence_refs: Iterable[object],
    now: datetime | None = None,
) -> dict[str, Any]:
    recorded_now = _utc_datetime(now)
    events = read_security_events(path)
    projection = security_incident_projection(events)
    identity_key = security_identity_key(
        security_domain,
        protected_surface,
        event_class,
    )
    current = _open_security_incident(projection, identity_key)
    occurrence_value = {
        "occurrence_id": safe_text(occurrence_id, required=True),
        "observed_at": validate_timestamp(observed_at, field="observed_at"),
        "source_ref": opaque_evidence_reference(source_ref),
        "safe_observation": safe_text(safe_observation, required=True),
    }
    if current is not None:
        for event in current["events"]:
            occurrence = event["occurrence"]
            if (
                occurrence is not None
                and occurrence["occurrence_id"]
                == occurrence_value["occurrence_id"]
            ):
                return event

    prior = [
        item
        for item in projection["items"]
        if item["identity_key"] == identity_key
        and item["status"] == "Resolved"
    ]
    incident_id = (
        current["security_incident_id"]
        if current is not None
        else next_security_incident_id(events, recorded_now)
    )
    event_number = (
        len(
            [
                event
                for event in events
                if event["security_incident_id"] == incident_id
            ]
        )
        + 1
    )
    event = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": f"{incident_id}:{event_number:04d}",
        "security_incident_id": incident_id,
        "event_type": "occurrence" if current is not None else "opened",
        "recorded_at": iso_utc(recorded_now),
        "identity_key": identity_key,
        "security_domain": typed_identity(
            security_domain,
            field="security_domain",
        ),
        "protected_surface": typed_identity(
            protected_surface,
            field="protected_surface",
        ),
        "event_class": typed_identity(event_class, field="event_class"),
        "safe_summary": safe_text(safe_summary, required=True),
        "status": current["status"] if current is not None else "Open",
        "reported_by": safe_text(reported_by, required=True),
        "owner": safe_text(owner) or None,
        "recommended_owner": safe_text(recommended_owner, required=True),
        "next_action": safe_text(next_action, required=True),
        "occurrence": occurrence_value,
        "restricted_evidence_refs": [
            opaque_evidence_reference(item)
            for item in restricted_evidence_refs
        ],
        "closure": None,
        "prior_security_incident_id": (
            max(
                prior,
                key=lambda item: _incident_sort_key(
                    item["security_incident_id"]
                ),
            )["security_incident_id"]
            if current is None and prior
            else None
        ),
        "event_sha256": None,
    }
    return append_security_event(path, event)


def transition_security_incident(
    path: Path,
    *,
    security_incident_id: str,
    status: str,
    recorded_by: object,
    next_action: object,
    owner: object | None = None,
    closure: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    events = read_security_events(path)
    projection = security_incident_projection(events)
    current = next(
        (
            item
            for item in projection["items"]
            if item["security_incident_id"] == security_incident_id
        ),
        None,
    )
    if current is None:
        raise SecurityIncidentContractError("unknown Security Incident ID")
    if current["status"] == "Resolved":
        raise SecurityIncidentContractError(
            "resolved Security Incidents are immutable"
        )
    if status not in LIFECYCLE:
        raise SecurityIncidentContractError(
            "invalid Security Incident lifecycle state"
        )
    if status == current["status"] and owner is None:
        raise SecurityIncidentContractError(
            "Security Incident transition makes no state change"
        )
    if status == "Resolved" and closure is None:
        raise SecurityIncidentContractError(
            "resolution requires exact closure evidence"
        )
    if status != "Resolved" and closure is not None:
        raise SecurityIncidentContractError(
            "closure evidence is reserved for resolution"
        )
    event_number = len(current["events"]) + 1
    event_type = "resolved" if status == "Resolved" else "status_changed"
    if owner is not None and status == current["status"]:
        event_type = "ownership_updated"
    event = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": f"{security_incident_id}:{event_number:04d}",
        "security_incident_id": security_incident_id,
        "event_type": event_type,
        "recorded_at": iso_utc(now),
        "identity_key": current["identity_key"],
        "security_domain": current["security_domain"],
        "protected_surface": current["protected_surface"],
        "event_class": current["event_class"],
        "safe_summary": current["safe_summary"],
        "status": status,
        "reported_by": safe_text(recorded_by, required=True),
        "owner": safe_text(owner) if owner is not None else current["owner"],
        "recommended_owner": current["recommended_owner"],
        "next_action": safe_text(next_action, required=True),
        "occurrence": None,
        "restricted_evidence_refs": [],
        "closure": dict(closure) if closure is not None else None,
        "prior_security_incident_id": current[
            "prior_security_incident_id"
        ],
        "event_sha256": None,
    }
    return append_security_event(path, event)


def relation_identity(
    operational_incident_id: object,
    security_incident_id: object,
    relationship_type: object,
) -> tuple[str, str]:
    operational_id = str(operational_incident_id or "")
    security_id = str(security_incident_id or "")
    if not OPERATIONAL_INCIDENT_ID.fullmatch(operational_id):
        raise SecurityIncidentContractError(
            "invalid Operational Incident relation target"
        )
    if not SECURITY_INCIDENT_ID.fullmatch(security_id):
        raise SecurityIncidentContractError(
            "invalid Security Incident relation target"
        )
    relation_type = typed_identity(
        relationship_type,
        field="relationship_type",
    )
    key = hashlib.sha256(
        f"{operational_id}|{security_id}|{relation_type}".encode("utf-8")
    ).hexdigest()
    return f"REL-{key[:24]}", relation_type


def validate_relation_event(event: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(event, Mapping):
        raise SecurityIncidentContractError(
            "incident relation event must be an object"
        )
    value = dict(event)
    _validate_exact_fields(
        value,
        RELATION_EVENT_FIELDS,
        record_type="incident relation event",
    )
    if value["schema_version"] != RELATION_EVENT_SCHEMA_VERSION:
        raise SecurityIncidentContractError(
            "unsupported incident relation event schema"
        )
    if value["event_type"] not in RELATION_EVENT_TYPES:
        raise SecurityIncidentContractError(
            "invalid incident relation event type"
        )
    expected_id, relationship_type = relation_identity(
        value["operational_incident_id"],
        value["security_incident_id"],
        value["relationship_type"],
    )
    if value["relation_id"] != expected_id:
        raise SecurityIncidentContractError("incident relation identity mismatch")
    prefix = f"{expected_id}:"
    if not str(value["relation_event_id"] or "").startswith(prefix):
        raise SecurityIncidentContractError(
            "incident relation event is not scoped to its relation"
        )
    suffix = str(value["relation_event_id"])[len(prefix) :]
    if not re.fullmatch(r"\d{4,}", suffix):
        raise SecurityIncidentContractError("invalid incident relation event ID")
    value["relationship_type"] = relationship_type
    value["recorded_at"] = validate_timestamp(
        value["recorded_at"],
        field="recorded_at",
    )
    value["recorded_by"] = safe_text(value["recorded_by"], required=True)
    value["safe_summary"] = safe_text(value["safe_summary"], required=True)
    expected_hash = _relation_event_hash(value)
    if value["event_sha256"] not in (None, expected_hash):
        raise SecurityIncidentContractError("incident relation event hash mismatch")
    value["event_sha256"] = expected_hash
    return value


def read_relation_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        1,
    ):
        if not raw.strip():
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as error:
            raise SecurityIncidentContractError(
                f"incident relation line {line_number} is invalid JSON"
            ) from error
        events.append(validate_relation_event(parsed))
    event_ids = [event["relation_event_id"] for event in events]
    if len(event_ids) != len(set(event_ids)):
        raise SecurityIncidentContractError(
            "duplicate incident relation event ID"
        )
    return events


def relationship_projection(
    events: Sequence[Mapping[str, Any]],
    *,
    known_operational_ids: Iterable[str],
    known_security_ids: Iterable[str],
    checked_at: str | None = None,
) -> dict[str, Any]:
    operational_ids = set(known_operational_ids)
    security_ids = set(known_security_ids)
    validated = [validate_relation_event(event) for event in events]
    relations: dict[str, dict[str, Any]] = {}
    for event in validated:
        if event["operational_incident_id"] not in operational_ids:
            raise SecurityIncidentContractError(
                "incident relation references an unknown Operational Incident"
            )
        if event["security_incident_id"] not in security_ids:
            raise SecurityIncidentContractError(
                "incident relation references an unknown Security Incident"
            )
        relation_id = event["relation_id"]
        current = relations.get(relation_id)
        event_number = int(event["relation_event_id"].rsplit(":", 1)[1])
        if current is None:
            if event["event_type"] != "linked" or event_number != 1:
                raise SecurityIncidentContractError(
                    "incident relation must begin with its first linked event"
                )
            current = {
                "relation_id": relation_id,
                "operational_incident_id": event["operational_incident_id"],
                "security_incident_id": event["security_incident_id"],
                "relationship_type": event["relationship_type"],
                "active": True,
                "safe_summary": event["safe_summary"],
                "events": [],
                "last_recorded_at": event["recorded_at"],
            }
            relations[relation_id] = current
        else:
            if event_number != len(current["events"]) + 1:
                raise SecurityIncidentContractError(
                    "incident relation has a nonsequential event stream"
                )
            if event["recorded_at"] < current["last_recorded_at"]:
                raise SecurityIncidentContractError(
                    "incident relation event time moves backward"
                )
            expected = (
                current["operational_incident_id"],
                current["security_incident_id"],
                current["relationship_type"],
            )
            supplied = (
                event["operational_incident_id"],
                event["security_incident_id"],
                event["relationship_type"],
            )
            if supplied != expected:
                raise SecurityIncidentContractError(
                    "incident relation changes typed identity"
                )
            if event["event_type"] == "linked" and current["active"]:
                raise SecurityIncidentContractError(
                    "incident relation is already linked"
                )
            if event["event_type"] == "unlinked" and not current["active"]:
                raise SecurityIncidentContractError(
                    "incident relation is already unlinked"
                )
            current["active"] = event["event_type"] == "linked"
            current["safe_summary"] = event["safe_summary"]
            current["last_recorded_at"] = event["recorded_at"]
        current["events"].append(event)

    active = [relation for relation in relations.values() if relation["active"]]
    active.sort(
        key=lambda item: (
            item["operational_incident_id"],
            item["security_incident_id"],
            item["relationship_type"],
        )
    )
    by_operational: dict[str, list[str]] = {}
    by_security: dict[str, list[str]] = {}
    for relation in active:
        operational_id = relation["operational_incident_id"]
        security_id = relation["security_incident_id"]
        by_operational.setdefault(operational_id, []).append(security_id)
        by_security.setdefault(security_id, []).append(operational_id)
    for values in (*by_operational.values(), *by_security.values()):
        values.sort()
    checked = validate_timestamp(
        checked_at or iso_utc(),
        field="checked_at",
    )
    return {
        "schema_version": RELATION_PROJECTION_SCHEMA_VERSION,
        "authority": "owner-local-incident-relations",
        "availability": "current",
        "complete": True,
        "checked_at": checked,
        "active_relations": active,
        "relations": sorted(
            relations.values(),
            key=lambda item: item["relation_id"],
        ),
        "by_operational_incident": by_operational,
        "by_security_incident": by_security,
    }


def append_relation_event(
    path: Path,
    event: Mapping[str, Any],
    *,
    known_operational_ids: Iterable[str],
    known_security_ids: Iterable[str],
) -> dict[str, Any]:
    validated = validate_relation_event(event)
    existing = read_relation_events(path)
    relationship_projection(
        existing,
        known_operational_ids=known_operational_ids,
        known_security_ids=known_security_ids,
    )
    for prior in existing:
        if prior["relation_event_id"] != validated["relation_event_id"]:
            continue
        if prior["event_sha256"] == validated["event_sha256"]:
            return prior
        raise SecurityIncidentContractError(
            "incident relation event ID conflicts with existing history"
        )
    relationship_projection(
        [*existing, validated],
        known_operational_ids=known_operational_ids,
        known_security_ids=known_security_ids,
    )
    _append_json_line(path, validated)
    return validated


def link_incidents(
    path: Path,
    *,
    operational_incident_id: str,
    security_incident_id: str,
    relationship_type: object,
    recorded_by: object,
    safe_summary: object,
    known_operational_ids: Iterable[str],
    known_security_ids: Iterable[str],
    now: datetime | None = None,
) -> dict[str, Any]:
    relation_id, relation_type = relation_identity(
        operational_incident_id,
        security_incident_id,
        relationship_type,
    )
    existing = read_relation_events(path)
    prior_events = [
        event for event in existing if event["relation_id"] == relation_id
    ]
    if prior_events:
        projection = relationship_projection(
            existing,
            known_operational_ids=known_operational_ids,
            known_security_ids=known_security_ids,
        )
        current = next(
            item
            for item in projection["relations"]
            if item["relation_id"] == relation_id
        )
        if current["active"]:
            return current["events"][-1]
    event = {
        "schema_version": RELATION_EVENT_SCHEMA_VERSION,
        "relation_event_id": f"{relation_id}:{len(prior_events) + 1:04d}",
        "relation_id": relation_id,
        "event_type": "linked",
        "recorded_at": iso_utc(now),
        "operational_incident_id": operational_incident_id,
        "security_incident_id": security_incident_id,
        "relationship_type": relation_type,
        "recorded_by": safe_text(recorded_by, required=True),
        "safe_summary": safe_text(safe_summary, required=True),
        "event_sha256": None,
    }
    return append_relation_event(
        path,
        event,
        known_operational_ids=known_operational_ids,
        known_security_ids=known_security_ids,
    )


def unlink_incidents(
    path: Path,
    *,
    relation_id: str,
    recorded_by: object,
    safe_summary: object,
    known_operational_ids: Iterable[str],
    known_security_ids: Iterable[str],
    now: datetime | None = None,
) -> dict[str, Any]:
    existing = read_relation_events(path)
    projection = relationship_projection(
        existing,
        known_operational_ids=known_operational_ids,
        known_security_ids=known_security_ids,
    )
    current = next(
        (
            item
            for item in projection["relations"]
            if item["relation_id"] == relation_id
        ),
        None,
    )
    if current is None or not current["active"]:
        raise SecurityIncidentContractError(
            "unknown or inactive incident relation"
        )
    event = {
        "schema_version": RELATION_EVENT_SCHEMA_VERSION,
        "relation_event_id": f"{relation_id}:{len(current['events']) + 1:04d}",
        "relation_id": relation_id,
        "event_type": "unlinked",
        "recorded_at": iso_utc(now),
        "operational_incident_id": current["operational_incident_id"],
        "security_incident_id": current["security_incident_id"],
        "relationship_type": current["relationship_type"],
        "recorded_by": safe_text(recorded_by, required=True),
        "safe_summary": safe_text(safe_summary, required=True),
        "event_sha256": None,
    }
    return append_relation_event(
        path,
        event,
        known_operational_ids=known_operational_ids,
        known_security_ids=known_security_ids,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "project-fixture",
        help="Project an explicitly injected fixture ledger.",
    )
    return parser


def main(
    *,
    path_authority: ProjectPathAuthority | None = None,
) -> int:
    args = _parser().parse_args()
    if path_authority is None or path_authority.mode != "fixture":
        raise PathAuthorityError(
            "Security Incident CLI is fixture-only and has no production authority"
        )
    if args.command == "project-fixture":
        events = path_authority.state_path(
            "records/automation/security-incidents.jsonl",
            required=False,
            owner_only=False,
        )
        print(json.dumps(project_security_incident_log(events), indent=2))
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
