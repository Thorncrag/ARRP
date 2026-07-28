#!/usr/bin/env python3
"""Validated event authority and projection for ARRP operational incidents."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from path_authority import (
        PathAuthorityError,
        ProjectPathAuthority,
    )
except ModuleNotFoundError:
    from scripts.path_authority import (
        PathAuthorityError,
        ProjectPathAuthority,
    )


SCHEMA_VERSION = 1
PROJECTION_SCHEMA_VERSION = 1
UNRESOLVED_STATES = frozenset(
    {"open", "investigating", "mitigated", "monitoring"}
)
LIFECYCLE = ("open", "investigating", "mitigated", "monitoring", "resolved")
IMPACTS = frozenset({"blocking", "disrupted", "degraded", "near_miss"})
EVENT_TYPES = frozenset(
    {
        "opened",
        "occurrence",
        "status_changed",
        "ownership_updated",
        "recovery_evidence",
        "resolved",
    }
)
INCIDENT_ID = re.compile(r"^INC-(\d{4})-(\d{3,})$")
SAFE_REFERENCE = re.compile(
    r"^(?:run|incident-spool|restricted|repository-gate|security|platform|data|"
    r"automation-role|log|github|file):[A-Za-z0-9][A-Za-z0-9._:/#@+-]{0,511}$"
)
SECRET_PATTERNS = (
    re.compile(r"\b(?:gh[opusr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,})\b"),
    re.compile(r"(?i)\b(?:token|password|secret|private[_ -]?key|authorization)\s*[:=]\s*\S+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
)
MAX_TEXT = 2048
MAX_REPORTS = 16


class IncidentContractError(ValueError):
    """Raised when an incident event or report violates the contract."""


def iso_utc(value: datetime | None = None) -> str:
    return (value or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")


def normalized(value: object) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def sanitize_text(value: object, *, required: bool = False) -> str:
    text = " ".join(str(value or "").replace("\x00", " ").split())
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    text = text[:MAX_TEXT]
    if required and not text:
        raise IncidentContractError("required incident text is empty")
    return text


def safe_reference(value: object) -> str:
    reference = sanitize_text(value, required=True)
    if not SAFE_REFERENCE.fullmatch(reference):
        raise IncidentContractError(
            "incident evidence references must be typed opaque references"
        )
    return reference


def incident_identity_key(
    component: object, prerequisite: object, failure_class: object
) -> str:
    parts = [normalized(component), normalized(prerequisite), normalized(failure_class)]
    if not all(parts):
        raise IncidentContractError(
            "component, prerequisite, and failure_class are required for identity"
        )
    return "sha256:" + hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def event_hash(event: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key != "event_sha256"}
    return "sha256:" + hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def validate_incident_event(event: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(event)
    if value.get("schema_version") != SCHEMA_VERSION:
        raise IncidentContractError("unsupported incident event schema")
    if value.get("event_type") not in EVENT_TYPES:
        raise IncidentContractError("invalid incident event type")
    if not INCIDENT_ID.fullmatch(str(value.get("incident_id") or "")):
        raise IncidentContractError("invalid incident ID")
    if not str(value.get("event_id") or "").startswith(
        f"{value['incident_id']}:"
    ):
        raise IncidentContractError("event ID is not scoped to its incident")
    if value.get("status") not in LIFECYCLE:
        raise IncidentContractError("invalid incident lifecycle status")
    if value.get("impact") not in IMPACTS:
        raise IncidentContractError("invalid incident impact")
    expected_identity = incident_identity_key(
        value.get("component"),
        value.get("prerequisite"),
        value.get("failure_class"),
    )
    if value.get("identity_key") != expected_identity:
        raise IncidentContractError("incident identity key does not match typed fields")
    for field in (
        "recorded_at",
        "component",
        "prerequisite",
        "failure_class",
        "summary",
        "reported_by",
        "recommended_owner",
        "next_action",
    ):
        value[field] = sanitize_text(value.get(field), required=True)
    owner = value.get("owner")
    value["owner"] = sanitize_text(owner) or None
    for field in ("affected_runs", "active_links", "evidence_refs"):
        rows = value.get(field)
        if not isinstance(rows, list) or len(rows) > 128:
            raise IncidentContractError(f"{field} must be a bounded array")
    value["affected_runs"] = [
        sanitize_text(item, required=True) for item in value["affected_runs"]
    ]
    value["active_links"] = [safe_reference(item) for item in value["active_links"]]
    value["evidence_refs"] = [
        safe_reference(item) for item in value["evidence_refs"]
    ]
    occurrence = value.get("occurrence")
    if occurrence is not None:
        if not isinstance(occurrence, Mapping):
            raise IncidentContractError("occurrence must be an object or null")
        occurrence = dict(occurrence)
        for field in ("occurrence_id", "observed_at", "diagnostic"):
            occurrence[field] = sanitize_text(occurrence.get(field), required=True)
        occurrence["run_id"] = sanitize_text(occurrence.get("run_id")) or None
        occurrence["source_ref"] = safe_reference(occurrence.get("source_ref"))
        value["occurrence"] = occurrence
    recovery = value.get("recovery")
    if value["event_type"] in {"recovery_evidence", "resolved"}:
        if not isinstance(recovery, Mapping):
            raise IncidentContractError(
                "recovery_evidence and resolved events require exact recovery proof"
            )
        recovery = dict(recovery)
        for field in ("verified_at", "closure_test", "result", "recorded_by"):
            recovery[field] = sanitize_text(recovery.get(field), required=True)
        recovery["evidence_refs"] = [
            safe_reference(item) for item in recovery.get("evidence_refs") or []
        ]
        if not recovery["evidence_refs"]:
            raise IncidentContractError("recovery proof requires evidence references")
        value["recovery"] = recovery
    elif recovery is not None:
        raise IncidentContractError(
            "only recovery_evidence or resolved events may carry recovery proof"
        )
    expected_hash = event_hash(value)
    supplied_hash = value.get("event_sha256")
    if supplied_hash not in (None, expected_hash):
        raise IncidentContractError("incident event hash mismatch")
    value["event_sha256"] = expected_hash
    return value


def read_incident_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            raise IncidentContractError(
                f"incident event log line {line_number} is invalid JSON"
            ) from error
        if value.get("event_type") == "registry_initialized":
            if value.get("schema_version") != SCHEMA_VERSION:
                raise IncidentContractError("incident registry schema is unsupported")
            continue
        events.append(validate_incident_event(value))
    event_ids = [event["event_id"] for event in events]
    if len(event_ids) != len(set(event_ids)):
        raise IncidentContractError("duplicate incident event ID")
    return events


def _incident_sort_key(incident_id: str) -> tuple[int, int]:
    match = INCIDENT_ID.fullmatch(incident_id)
    return (int(match.group(1)), int(match.group(2))) if match else (0, 0)


def next_incident_id(events: Sequence[Mapping[str, Any]], now: datetime) -> str:
    year = now.astimezone(timezone.utc).year
    sequence = max(
        (
            _incident_sort_key(str(event.get("incident_id") or ""))[1]
            for event in events
            if _incident_sort_key(str(event.get("incident_id") or ""))[0] == year
        ),
        default=0,
    )
    return f"INC-{year}-{sequence + 1:03d}"


def append_incident_event(path: Path, event: Mapping[str, Any]) -> dict[str, Any]:
    validated = validate_incident_event(event)
    existing = read_incident_events(path)
    if any(row["event_id"] == validated["event_id"] for row in existing):
        return validated
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_APPEND,
        0o600,
    )
    try:
        os.write(
            descriptor,
            (
                json.dumps(validated, ensure_ascii=False, sort_keys=True)
                + "\n"
            ).encode("utf-8"),
        )
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return validated


def incident_projection(
    events: Sequence[Mapping[str, Any]],
    *,
    checked_at: str | None = None,
) -> dict[str, Any]:
    incidents: dict[str, dict[str, Any]] = {}
    ordered_events = sorted(
        (validate_incident_event(event) for event in events),
        key=lambda event: (event["recorded_at"], event["event_id"]),
    )
    for event in ordered_events:
        incident_id = event["incident_id"]
        current = incidents.get(incident_id)
        if current is None:
            if event["event_type"] != "opened":
                raise IncidentContractError(
                    f"{incident_id} begins without an opened event"
                )
            current = {
                "incident_id": incident_id,
                "identity_key": event["identity_key"],
                "component": event["component"],
                "prerequisite": event["prerequisite"],
                "failure_class": event["failure_class"],
                "summary": event["summary"],
                "status": event["status"],
                "impact": event["impact"],
                "reported_by": event["reported_by"],
                "owner": event["owner"],
                "recommended_owner": event["recommended_owner"],
                "next_action": event["next_action"],
                "first_observed": event["occurrence"]["observed_at"],
                "last_observed": event["occurrence"]["observed_at"],
                "occurrences": [],
                "affected_runs": [],
                "active_links": [],
                "evidence_refs": [],
                "recovery_evidence": [],
                "events": [],
                "prior_incident_id": event.get("prior_incident_id"),
            }
            incidents[incident_id] = current
        elif current["identity_key"] != event["identity_key"]:
            raise IncidentContractError(
                f"{incident_id} changes deterministic identity"
            )
        if current["status"] == "resolved" and event["event_type"] != "resolved":
            raise IncidentContractError(
                f"{incident_id} has events after verified resolution"
            )
        occurrence = event.get("occurrence")
        if occurrence is not None and not any(
            row["occurrence_id"] == occurrence["occurrence_id"]
            for row in current["occurrences"]
        ):
            current["occurrences"].append(occurrence)
            current["last_observed"] = max(
                current["last_observed"], occurrence["observed_at"]
            )
        for field in ("affected_runs", "active_links", "evidence_refs"):
            for item in event[field]:
                if item not in current[field]:
                    current[field].append(item)
        current.update(
            {
                "summary": event["summary"],
                "status": event["status"],
                "impact": event["impact"],
                "reported_by": event["reported_by"],
                "owner": event["owner"],
                "recommended_owner": event["recommended_owner"],
                "next_action": event["next_action"],
            }
        )
        if event.get("recovery") is not None:
            current["recovery_evidence"].append(event["recovery"])
        current["events"].append(event)
    rows = sorted(
        incidents.values(),
        key=lambda item: (
            item["last_observed"],
            _incident_sort_key(item["incident_id"]),
        ),
        reverse=True,
    )
    unresolved = [item for item in rows if item["status"] in UNRESOLVED_STATES]
    active_links: dict[str, list[str]] = {}
    for incident in unresolved:
        for link in incident["active_links"]:
            active_links.setdefault(link, []).append(incident["incident_id"])
    for ids in active_links.values():
        ids.sort()
    if any(
        item["impact"] in {"blocking", "disrupted"}
        and item["status"] in {"open", "investigating"}
        for item in unresolved
    ):
        impact_state = "red"
    elif unresolved:
        impact_state = "yellow"
    else:
        impact_state = "green"
    return {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "availability": "current",
        "complete": True,
        "checked_at": checked_at or iso_utc(),
        "count": len(rows),
        "unresolved_count": len(unresolved),
        "impact_state": impact_state,
        "items": rows,
        "active_links": active_links,
    }


def unavailable_projection(reason: object) -> dict[str, Any]:
    return {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "availability": "unavailable",
        "complete": False,
        "checked_at": iso_utc(),
        "count": None,
        "unresolved_count": None,
        "impact_state": "gray",
        "items": [],
        "active_links": {},
        "reason": sanitize_text(reason, required=True),
    }


def project_incident_log(path: Path) -> dict[str, Any]:
    try:
        return incident_projection(read_incident_events(path))
    except (OSError, IncidentContractError) as error:
        return unavailable_projection(str(error))


def _open_incident_for_identity(
    events: Sequence[Mapping[str, Any]], identity_key: str
) -> dict[str, Any] | None:
    projection = incident_projection(events)
    matches = [
        item
        for item in projection["items"]
        if item["identity_key"] == identity_key
        and item["status"] in UNRESOLVED_STATES
    ]
    if len(matches) > 1:
        raise IncidentContractError(
            "more than one unresolved incident has the same identity"
        )
    return matches[0] if matches else None


def record_incident_occurrence(
    path: Path,
    *,
    component: object,
    prerequisite: object,
    failure_class: object,
    impact: str,
    summary: object,
    reported_by: object,
    owner: object,
    recommended_owner: object,
    next_action: object,
    occurrence_id: object,
    observed_at: object,
    source_ref: object,
    diagnostic: object,
    run_id: object = None,
    evidence_refs: Iterable[object] = (),
    active_links: Iterable[object] = (),
    now: datetime | None = None,
) -> dict[str, Any]:
    if impact not in IMPACTS:
        raise IncidentContractError("invalid incident impact")
    recorded_now = now or datetime.now(timezone.utc)
    events = read_incident_events(path)
    identity_key = incident_identity_key(component, prerequisite, failure_class)
    current = _open_incident_for_identity(events, identity_key)
    prior = [
        item
        for item in incident_projection(events)["items"]
        if item["identity_key"] == identity_key and item["status"] == "resolved"
    ]
    incident_id = (
        current["incident_id"]
        if current is not None
        else next_incident_id(events, recorded_now)
    )
    occurrence_value = {
        "occurrence_id": sanitize_text(occurrence_id, required=True),
        "observed_at": sanitize_text(observed_at, required=True),
        "run_id": sanitize_text(run_id) or None,
        "source_ref": safe_reference(source_ref),
        "diagnostic": sanitize_text(diagnostic, required=True),
    }
    if current is not None and any(
        item["occurrence_id"] == occurrence_value["occurrence_id"]
        for item in current["occurrences"]
    ):
        return current
    event_type = "occurrence" if current is not None else "opened"
    event_index = sum(
        1 for event in events if event["incident_id"] == incident_id
    ) + 1
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_id": f"{incident_id}:{event_index:04d}",
        "incident_id": incident_id,
        "event_type": event_type,
        "recorded_at": iso_utc(recorded_now),
        "identity_key": identity_key,
        "component": sanitize_text(component, required=True),
        "prerequisite": sanitize_text(prerequisite, required=True),
        "failure_class": sanitize_text(failure_class, required=True),
        "summary": sanitize_text(summary, required=True),
        "status": current["status"] if current is not None else "open",
        "impact": impact,
        "reported_by": sanitize_text(reported_by, required=True),
        "owner": sanitize_text(owner) or None,
        "recommended_owner": sanitize_text(recommended_owner, required=True),
        "next_action": sanitize_text(next_action, required=True),
        "occurrence": occurrence_value,
        "affected_runs": [occurrence_value["run_id"]]
        if occurrence_value["run_id"]
        else [],
        "active_links": [safe_reference(item) for item in active_links],
        "evidence_refs": [safe_reference(item) for item in evidence_refs],
        "recovery": None,
        "prior_incident_id": (
            sorted(prior, key=lambda item: item["incident_id"])[-1]["incident_id"]
            if current is None and prior
            else None
        ),
    }
    return append_incident_event(path, event)


def transition_incident(
    path: Path,
    *,
    incident_id: str,
    status: str,
    recorded_by: object,
    next_action: object,
    recovery: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    events = read_incident_events(path)
    projection = incident_projection(events)
    current = next(
        (item for item in projection["items"] if item["incident_id"] == incident_id),
        None,
    )
    if current is None:
        raise IncidentContractError("unknown incident ID")
    if current["status"] == "resolved":
        raise IncidentContractError("resolved incidents are immutable")
    if status not in LIFECYCLE:
        raise IncidentContractError("invalid incident lifecycle status")
    if status == "resolved" and recovery is None:
        raise IncidentContractError("resolution requires exact recovery proof")
    event_type = "resolved" if status == "resolved" else "status_changed"
    if recovery is not None and status != "resolved":
        event_type = "recovery_evidence"
    event_index = sum(
        1 for event in events if event["incident_id"] == incident_id
    ) + 1
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_id": f"{incident_id}:{event_index:04d}",
        "incident_id": incident_id,
        "event_type": event_type,
        "recorded_at": iso_utc(now),
        "identity_key": current["identity_key"],
        "component": current["component"],
        "prerequisite": current["prerequisite"],
        "failure_class": current["failure_class"],
        "summary": current["summary"],
        "status": status,
        "impact": current["impact"],
        "reported_by": sanitize_text(recorded_by, required=True),
        "owner": current["owner"],
        "recommended_owner": current["recommended_owner"],
        "next_action": sanitize_text(next_action, required=True),
        "occurrence": None,
        "affected_runs": [],
        "active_links": list(current["active_links"]),
        "evidence_refs": [],
        "recovery": recovery,
        "prior_incident_id": current.get("prior_incident_id"),
    }
    return append_incident_event(path, event)


REPORT_REQUIRED_FIELDS = (
    "component",
    "prerequisite",
    "failure_class",
    "impact",
    "summary",
    "observed_at",
    "observations",
    "evidence_refs",
    "checks_performed",
    "ruled_out",
    "hypotheses",
    "attempted_remedies",
    "unresolved_boundary",
    "preferred_remedy",
    "alternatives",
    "recommended_owner",
    "required_authority",
    "next_action",
    "risk_if_deferred",
    "fallback",
    "closure_test",
    "active_links",
)


def validate_incident_report(report: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(report, Mapping):
        raise IncidentContractError("incident report must be an object")
    missing = [field for field in REPORT_REQUIRED_FIELDS if field not in report]
    if missing:
        raise IncidentContractError(
            "incident report missing required fields: " + ", ".join(missing)
        )
    value = dict(report)
    if value.get("impact") not in IMPACTS:
        raise IncidentContractError("incident report impact is invalid")
    for field in (
        "component",
        "prerequisite",
        "failure_class",
        "summary",
        "observed_at",
        "unresolved_boundary",
        "preferred_remedy",
        "recommended_owner",
        "required_authority",
        "next_action",
        "risk_if_deferred",
        "fallback",
        "closure_test",
    ):
        value[field] = sanitize_text(value.get(field), required=True)
    for field in (
        "observations",
        "checks_performed",
        "ruled_out",
        "attempted_remedies",
        "alternatives",
        "active_links",
    ):
        rows = value.get(field)
        if not isinstance(rows, list) or len(rows) > 32:
            raise IncidentContractError(f"incident report {field} must be bounded")
        value[field] = [
            safe_reference(item)
            if field == "active_links"
            else sanitize_text(item, required=True)
            for item in rows
        ]
    value["evidence_refs"] = [
        safe_reference(item) for item in value.get("evidence_refs") or []
    ]
    if (
        not value["observations"]
        or not value["evidence_refs"]
        or not value["checks_performed"]
        or not value["ruled_out"]
        or not value["attempted_remedies"]
        or not value["alternatives"]
    ):
        raise IncidentContractError(
            "incident report requires observations, evidence, checks, exclusions, "
            "attempted remedies, and alternatives"
        )
    hypotheses = value.get("hypotheses")
    if not isinstance(hypotheses, list) or not hypotheses or len(hypotheses) > 16:
        raise IncidentContractError("incident report hypotheses must be bounded")
    normalized_hypotheses = []
    for hypothesis in hypotheses:
        if not isinstance(hypothesis, Mapping):
            raise IncidentContractError("incident hypothesis must be an object")
        confidence = hypothesis.get("confidence")
        if confidence not in {"low", "medium", "high"}:
            raise IncidentContractError("incident hypothesis confidence is invalid")
        normalized_hypotheses.append(
            {
                "hypothesis": sanitize_text(
                    hypothesis.get("hypothesis"), required=True
                ),
                "confidence": confidence,
            }
        )
    value["hypotheses"] = normalized_hypotheses
    return value


def record_incident_reports(
    path: Path,
    reports: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
    reported_by: str = "Elim",
) -> list[dict[str, Any]]:
    if not isinstance(reports, Sequence) or isinstance(reports, (str, bytes)):
        raise IncidentContractError("incident_reports must be an array")
    if len(reports) > MAX_REPORTS:
        raise IncidentContractError("incident_reports exceeds its maximum")
    recorded: list[dict[str, Any]] = []
    for index, original in enumerate(reports, 1):
        report = validate_incident_report(original)
        diagnostic = "; ".join(
            (
                report["unresolved_boundary"],
                f"Preferred remedy: {report['preferred_remedy']}",
                f"Closure test: {report['closure_test']}",
            )
        )
        evidence_digest = hashlib.sha256(
            json.dumps(
                report, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()[:16]
        recorded.append(
            record_incident_occurrence(
                path,
                component=report["component"],
                prerequisite=report["prerequisite"],
                failure_class=report["failure_class"],
                impact=report["impact"],
                summary=report["summary"],
                reported_by=reported_by,
                owner=None,
                recommended_owner=report["recommended_owner"],
                next_action=report["next_action"],
                occurrence_id=f"{run_id}:elim:{index}:{evidence_digest}",
                observed_at=report["observed_at"],
                source_ref=f"restricted:elim-incident-report/{run_id}/{index}",
                diagnostic=diagnostic,
                run_id=run_id,
                evidence_refs=report["evidence_refs"],
                active_links=report["active_links"],
            )
        )
    return recorded


def spool_failure_incident(
    spool_path: Path,
    *,
    run_id: str,
    component: object,
    prerequisite: object,
    failure_class: object,
    diagnostic: object,
    observed_at: str | None = None,
    impact: str = "blocking",
    summary: object = (
        "Automation transaction failed before normal incident reconciliation."
    ),
    reported_by: object = "Run Coordinator failure spool",
    recommended_owner: object = "Run Coordinator",
    next_action: object = (
        "Inspect the preserved run status and reconcile the exact failure boundary."
    ),
    active_links: Iterable[object] = ("automation-role:run-coordinator-bot",),
) -> dict[str, Any]:
    if impact not in IMPACTS:
        raise IncidentContractError("invalid failure-spool impact")
    record = {
        "schema_version": 1,
        "spool_id": "spool:"
        + hashlib.sha256(
            f"{run_id}|{component}|{prerequisite}|{failure_class}".encode("utf-8")
        ).hexdigest(),
        "run_id": sanitize_text(run_id, required=True),
        "component": sanitize_text(component, required=True),
        "prerequisite": sanitize_text(prerequisite, required=True),
        "failure_class": sanitize_text(failure_class, required=True),
        "impact": impact,
        "summary": sanitize_text(summary, required=True),
        "diagnostic": sanitize_text(diagnostic, required=True),
        "observed_at": sanitize_text(observed_at or iso_utc(), required=True),
        "source_ref": f"incident-spool:{sanitize_text(run_id, required=True)}",
        "reported_by": sanitize_text(reported_by, required=True),
        "recommended_owner": sanitize_text(recommended_owner, required=True),
        "next_action": sanitize_text(next_action, required=True),
        "active_links": [safe_reference(item) for item in active_links],
    }
    spool_path.parent.mkdir(parents=True, exist_ok=True)
    existing_ids: set[str] = set()
    if spool_path.exists():
        for raw in spool_path.read_text(encoding="utf-8").splitlines():
            try:
                existing_ids.add(str(json.loads(raw).get("spool_id") or ""))
            except json.JSONDecodeError:
                continue
    if record["spool_id"] in existing_ids:
        return record
    descriptor = os.open(
        spool_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600
    )
    try:
        os.write(
            descriptor,
            (json.dumps(record, sort_keys=True) + "\n").encode("utf-8"),
        )
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return record


def reconcile_failure_spool(spool_path: Path, incident_path: Path) -> int:
    if not spool_path.exists():
        return 0
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(
        spool_path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            raise IncidentContractError(
                f"failure spool line {line_number} is invalid JSON"
            ) from error
        if value.get("schema_version") != 1:
            raise IncidentContractError("failure spool schema is unsupported")
        records.append(value)
    for value in records:
        record_incident_occurrence(
            incident_path,
            component=value["component"],
            prerequisite=value["prerequisite"],
            failure_class=value["failure_class"],
            impact=value["impact"],
            summary=value["summary"],
            reported_by=value.get("reported_by") or "Run Coordinator failure spool",
            owner=None,
            recommended_owner=value["recommended_owner"],
            next_action=value["next_action"],
            occurrence_id=value["spool_id"],
            observed_at=value["observed_at"],
            source_ref=value["source_ref"],
            diagnostic=value["diagnostic"],
            run_id=value["run_id"],
            evidence_refs=[value["source_ref"]],
            active_links=value["active_links"],
        )
    if records:
        spool_path.parent.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=".incident-spool-reconciled-",
            dir=spool_path.parent,
        )
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as stream:
                stream.write("")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, spool_path)
            os.chmod(spool_path, 0o600)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
    return len(records)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    project = commands.add_parser("project")
    project.add_argument("--events", default="operational-incidents.jsonl")
    return parser


def main(
    *,
    path_authority: ProjectPathAuthority | None = None,
) -> int:
    args = _parser().parse_args()
    if args.command == "project":
        event_name = os.path.basename(args.events)
        if event_name != args.events or event_name != "operational-incidents.jsonl":
            raise PathAuthorityError("unsupported operational-incident path")
        if path_authority is None:
            authority = ProjectPathAuthority.production()
        else:
            if path_authority.mode != "fixture":
                raise PathAuthorityError(
                    "injected path authority is reserved for isolated tests"
                )
            authority = path_authority
        events = authority.state_path(
            f"records/automation/{event_name}",
            owner_only=authority.mode == "production_canonical",
        )
        print(json.dumps(project_incident_log(events), indent=2))
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
