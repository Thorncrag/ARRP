#!/usr/bin/env python3
"""Fail-closed parsing for ARRP public governance changes and private supplements."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable


PUBLIC_ENTRY_CLASS = "governance_change"
SUPPLEMENT_CLASS = "governance_change_supplement"
GOVERNANCE_ID_RE = re.compile(r"^GOV-(?P<year>[0-9]{4})-(?P<number>[0-9]{3})$")
SUPPLEMENT_ID_RE = re.compile(r"^GOVSUP-(?P<year>[0-9]{4})-(?P<number>[0-9]{3})$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEADER_RE = re.compile(r"^## (?P<id>GOV-[0-9]{4}-[0-9]{3}) — (?P<title>[^\n]+)$")
BULLET_RE = re.compile(r"^- (?P<label>[A-Za-z ][A-Za-z -]*): (?P<value>.+)$")

PUBLIC_LABELS = {
    "Date": "date",
    "Status": "status",
    "Decision class": "decision_class",
    "Authorities": "authorities",
    "Decision": "decision",
    "Evidence": "evidence",
    "Policy adoption": "policy_adoption",
    "Live activation": "live_activation",
    "Relationships": "relationships",
    "Validation": "validation",
    "Owner-local supplement": "private_supplement_required",
}
PUBLIC_REQUIRED = frozenset(PUBLIC_LABELS.values())
REGISTRY_KEYS = frozenset(
    {
        "id",
        "date",
        "title",
        "decision_class",
        "authority",
        "source",
        "destination",
        "resolution",
        "consumers",
        "status",
        "policy_adoption",
        "live_activation",
        "relationships",
        "private_supplement_required",
    }
)
REGISTRY_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "title",
        "authority",
        "log",
        "historical_change_audit_log",
        "decision_classes",
        "entries",
    }
)
DECISION_CLASS_KEYS = frozenset(
    {
        "id",
        "label",
        "inclusion",
        "exclusion",
        "canonical_source",
        "producer",
        "lifecycle_owner",
        "destination",
        "resolution_rule",
        "allowed_consumers",
    }
)
SOURCE_KEYS = frozenset({"kind", "commits", "pull_requests"})
RELATIONSHIP_KEYS = frozenset(
    {"supersedes", "refines", "refined_by", "proposed_refinements"}
)
GOVERNANCE_STATUSES = frozenset(
    {
        "Canonical",
        "Proposed / unmerged",
        "Proposed / not adopted",
        "Superseded",
        "Retired",
    }
)
SUPPLEMENT_KEYS = frozenset(
    {
        "schema_version",
        "event_id",
        "event_class",
        "governance_id",
        "public_entry_sha256",
        "recorded_at",
        "provenance",
        "decision_context",
        "protected_references",
        "validation_references",
        "disclosure_review",
        "safe_summary",
    }
)


class GovernanceChangeError(ValueError):
    """Raised when governance provenance cannot be proven exactly."""


@dataclass(frozen=True)
class GovernanceChange:
    """One public-safe, registry-bound governance record."""

    id: str
    record_class: str
    date: str
    title: str
    decision_class: str
    authorities: tuple[str, ...]
    status: str
    decision: str
    evidence: str
    policy_adoption: str
    live_activation: str
    relationships: str
    validation: str
    private_supplement_required: bool
    entry_sha256: str

    def public_fields(self) -> dict[str, object]:
        return {
            "id": self.id,
            "record_class": self.record_class,
            "date": self.date,
            "title": self.title,
            "decision_class": self.decision_class,
            "authorities": list(self.authorities),
            "status": self.status,
            "decision": self.decision,
            "evidence": self.evidence,
            "policy_adoption": self.policy_adoption,
            "live_activation": self.live_activation,
            "relationships": self.relationships,
            "validation": self.validation,
            "private_supplement_required": self.private_supplement_required,
        }


def _canonical_digest(value: dict[str, object]) -> str:
    material = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(material).hexdigest()


def _require_identifier(value: object, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise GovernanceChangeError(f"invalid {label}")
    return value


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise GovernanceChangeError(f"{label} must be non-empty text")
    return value.strip()


def _require_date(value: object, label: str) -> str:
    text = _require_text(value, label)
    try:
        date.fromisoformat(text)
    except ValueError as error:
        raise GovernanceChangeError(f"invalid {label}") from error
    return text


def _require_timestamp(value: object) -> str:
    text = _require_text(value, "recorded_at")
    if not text.endswith("Z"):
        raise GovernanceChangeError("recorded_at must use UTC Z notation")
    try:
        datetime.fromisoformat(text.removesuffix("Z") + "+00:00")
    except ValueError as error:
        raise GovernanceChangeError("invalid recorded_at") from error
    return text


def _require_text_list(value: object, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or not all(
            isinstance(item, str) and item.strip() and "\x00" not in item
            for item in value
        )
    ):
        raise GovernanceChangeError(f"{label} must be a non-empty text list")
    normalized = [item.strip() for item in value]
    if len(normalized) != len(set(normalized)):
        raise GovernanceChangeError(f"{label} contains duplicate references")
    return normalized


def _parse_required(value: str) -> bool:
    if value == "Required.":
        return True
    if value == "Not required.":
        return False
    raise GovernanceChangeError("owner-local supplement must be Required. or Not required.")


def _read_registry(
    path: Path,
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GovernanceChangeError(
            "governance registry is unavailable or invalid"
        ) from error
    if not isinstance(value, dict) or set(value) != REGISTRY_TOP_LEVEL_KEYS:
        raise GovernanceChangeError(
            "governance registry has unknown or missing fields"
        )
    if (
        value.get("schema_version") != 1
        or not isinstance(value.get("entries"), list)
        or not isinstance(value.get("decision_classes"), list)
    ):
        raise GovernanceChangeError(
            "governance registry has an unsupported schema"
        )

    decision_classes: dict[str, dict[str, object]] = {}
    for raw_class in value["decision_classes"]:
        if (
            not isinstance(raw_class, dict)
            or set(raw_class) != DECISION_CLASS_KEYS
        ):
            raise GovernanceChangeError(
                "governance decision class has unknown or missing fields"
            )
        class_id = _require_text(
            raw_class.get("id"),
            "decision class id",
        )
        if (
            not re.fullmatch(r"[a-z][a-z0-9_]*", class_id)
            or class_id in decision_classes
        ):
            raise GovernanceChangeError(
                "governance decision class identity is invalid or duplicated"
            )
        for field in (
            "label",
            "inclusion",
            "exclusion",
            "canonical_source",
            "producer",
            "lifecycle_owner",
            "destination",
            "resolution_rule",
        ):
            _require_text(raw_class.get(field), f"decision class {field}")
        allowed = raw_class.get("allowed_consumers")
        if (
            not isinstance(allowed, list)
            or not allowed
            or not all(
                isinstance(item, str)
                and re.fullmatch(r"[a-z][a-z0-9_]*", item)
                for item in allowed
            )
            or len(allowed) != len(set(allowed))
        ):
            raise GovernanceChangeError(
                "decision class allowed consumers are invalid"
            )
        decision_classes[class_id] = raw_class

    entries: dict[str, dict[str, object]] = {}
    for raw in value["entries"]:
        if not isinstance(raw, dict) or set(raw) != REGISTRY_KEYS:
            raise GovernanceChangeError(
                "governance registry entry has unknown or missing fields"
            )
        identifier = _require_identifier(
            raw.get("id"),
            GOVERNANCE_ID_RE,
            "GOV id",
        )
        if identifier in entries:
            raise GovernanceChangeError(
                "duplicate GOV id in governance registry"
            )
        _require_date(raw.get("date"), "registry date")
        _require_text(raw.get("title"), "registry title")
        class_id = _require_text(
            raw.get("decision_class"),
            "registry decision class",
        )
        if class_id not in decision_classes:
            raise GovernanceChangeError(
                "governance registry entry uses an unknown decision class"
            )
        authority = raw.get("authority")
        if (
            not isinstance(authority, list)
            or not authority
            or not all(
                isinstance(item, str) and item.strip()
                for item in authority
            )
            or len(authority) != len(set(authority))
        ):
            raise GovernanceChangeError(
                "governance registry authority list is invalid"
            )
        source = raw.get("source")
        if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
            raise GovernanceChangeError(
                "governance registry source is invalid"
            )
        kind = source.get("kind")
        commits = source.get("commits")
        pull_requests = source.get("pull_requests")
        if (
            kind not in {"git_merge", "git_commit", "current_worktree"}
            or not isinstance(commits, list)
            or not all(
                isinstance(item, str)
                and re.fullmatch(r"[0-9a-f]{40}", item)
                for item in commits
            )
            or not isinstance(pull_requests, list)
            or not all(
                isinstance(item, int) and item > 0
                for item in pull_requests
            )
            or (
                kind == "current_worktree"
                and bool(commits or pull_requests)
            )
            or (
                kind in {"git_merge", "git_commit"}
                and not commits
            )
            or (kind == "git_merge" and not pull_requests)
        ):
            raise GovernanceChangeError(
                "governance registry source evidence is invalid"
            )
        expected_destination = (
            "framework/logs/governance/governance-change-log.md#"
            + identifier.casefold()
        )
        if raw.get("destination") != expected_destination:
            raise GovernanceChangeError(
                "governance registry destination is invalid"
            )
        _require_text(raw.get("resolution"), "registry resolution")
        consumers = raw.get("consumers")
        allowed_consumers = set(
            decision_classes[class_id]["allowed_consumers"]
        )
        if (
            not isinstance(consumers, list)
            or not consumers
            or not all(
                isinstance(item, str)
                and re.fullmatch(r"[a-z][a-z0-9_]*", item)
                for item in consumers
            )
            or len(consumers) != len(set(consumers))
            or not set(consumers) <= allowed_consumers
        ):
            raise GovernanceChangeError(
                "governance registry consumers are invalid"
            )
        status = _require_text(raw.get("status"), "registry status")
        if status not in GOVERNANCE_STATUSES:
            raise GovernanceChangeError(
                "governance registry status is invalid"
            )
        if (
            status == "Proposed / unmerged"
            and kind != "current_worktree"
        ) or (
            status != "Proposed / unmerged"
            and kind == "current_worktree"
        ):
            raise GovernanceChangeError(
                "governance registry status disagrees with source evidence"
            )
        for field in ("policy_adoption", "live_activation"):
            _require_text(raw.get(field), f"registry {field}")
        if not isinstance(raw["private_supplement_required"], bool):
            raise GovernanceChangeError(
                "registry supplement flag must be boolean"
            )
        relationships = raw.get("relationships")
        if (
            not isinstance(relationships, dict)
            or set(relationships) != RELATIONSHIP_KEYS
        ):
            raise GovernanceChangeError(
                "governance registry relationships are invalid"
            )
        for field in RELATIONSHIP_KEYS:
            values = relationships[field]
            if (
                not isinstance(values, list)
                or not all(
                    isinstance(item, str)
                    and GOVERNANCE_ID_RE.fullmatch(item)
                    for item in values
                )
                or len(values) != len(set(values))
            ):
                raise GovernanceChangeError(
                    f"registry relationship {field} is invalid"
                )
        entries[identifier] = raw

    known_ids = set(entries)
    for identifier, raw in entries.items():
        relationships = raw["relationships"]
        referenced = {
            item
            for field in RELATIONSHIP_KEYS
            for item in relationships[field]
        }
        if identifier in referenced or not referenced <= known_ids:
            raise GovernanceChangeError(
                "governance registry relationship target is invalid"
            )
    return entries, decision_classes


def _parse_log_blocks(path: Path) -> Iterable[tuple[str, str, dict[str, str]]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise GovernanceChangeError("governance change log is unavailable") from error
    blocks: list[tuple[str, str, dict[str, str]]] = []
    current: dict[str, str] | None = None
    identifier = title = active = None
    for line in lines:
        header = HEADER_RE.fullmatch(line)
        if header:
            if current is not None:
                blocks.append((identifier or "", title or "", current))
            identifier, title, current, active = header["id"], header["title"], {}, None
            continue
        if current is None:
            continue
        bullet = BULLET_RE.fullmatch(line)
        if bullet:
            label = bullet["label"]
            if label not in PUBLIC_LABELS:
                raise GovernanceChangeError("governance log has an unknown field")
            field = PUBLIC_LABELS[label]
            if field in current:
                raise GovernanceChangeError("governance log has a duplicate field")
            current[field] = bullet["value"].strip()
            active = field
        elif line.startswith("  ") and active:
            current[active] += " " + line.strip()
        elif line.strip():
            raise GovernanceChangeError("governance log has unstructured entry content")
    if current is not None:
        blocks.append((identifier or "", title or "", current))
    return blocks


def parse_public_changes(log_path: Path, registry_path: Path) -> dict[str, GovernanceChange]:
    """Return only exact, public-safe log entries registered by GOV ID."""

    registry, _decision_classes = _read_registry(registry_path)
    parsed: dict[str, GovernanceChange] = {}
    for identifier, title, fields in _parse_log_blocks(log_path):
        _require_identifier(identifier, GOVERNANCE_ID_RE, "GOV id")
        if identifier in parsed:
            raise GovernanceChangeError("duplicate GOV id in governance log")
        if set(fields) != PUBLIC_REQUIRED:
            raise GovernanceChangeError("governance log entry has missing fields")
        registry_entry = registry.get(identifier)
        if registry_entry is None:
            raise GovernanceChangeError("governance log GOV id is not registered")
        if (
            fields["date"] != registry_entry["date"]
            or title != registry_entry["title"]
            or fields["status"] != registry_entry["status"]
            or fields["decision_class"] != registry_entry["decision_class"]
            or tuple(
                item.strip() for item in fields["authorities"].split(";")
            )
            != tuple(registry_entry["authority"])
            or _parse_required(fields["private_supplement_required"])
            != registry_entry["private_supplement_required"]
            or fields["policy_adoption"] != registry_entry["policy_adoption"]
            or fields["live_activation"] != registry_entry["live_activation"]
        ):
            raise GovernanceChangeError("governance log entry disagrees with registry")
        public = {
            "id": identifier,
            "record_class": PUBLIC_ENTRY_CLASS,
            "date": _require_date(fields["date"], "log date"),
            "title": _require_text(title, "log title"),
            "decision_class": _require_text(
                fields["decision_class"],
                "decision class",
            ),
            "authorities": tuple(
                item.strip() for item in fields["authorities"].split(";")
            ),
            "status": _require_text(fields["status"], "log status"),
            "decision": _require_text(fields["decision"], "decision"),
            "evidence": _require_text(fields["evidence"], "evidence"),
            "policy_adoption": _require_text(fields["policy_adoption"], "policy adoption"),
            "live_activation": _require_text(fields["live_activation"], "live activation"),
            "relationships": _require_text(
                fields["relationships"],
                "relationships",
            ),
            "validation": _require_text(fields["validation"], "validation"),
            "private_supplement_required": _parse_required(fields["private_supplement_required"]),
        }
        parsed[identifier] = GovernanceChange(
            **public, entry_sha256=_canonical_digest(public)
        )
    if set(parsed) != set(registry):
        raise GovernanceChangeError("registry and governance log do not have the same GOV IDs")
    return parsed


def parse_private_supplements(
    path: Path,
    public_changes: dict[str, GovernanceChange],
) -> list[dict[str, object]]:
    """Read an append-only owner-local JSONL supplement without policy authority."""

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    except OSError as error:
        raise GovernanceChangeError("governance supplements are unavailable") from error
    events: list[dict[str, object]] = []
    seen: set[str] = set()
    seen_governance_ids: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            raise GovernanceChangeError("governance supplement JSONL may not contain blank events")
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise GovernanceChangeError(f"invalid governance supplement event at line {line_number}") from error
        if not isinstance(event, dict) or set(event) != SUPPLEMENT_KEYS:
            raise GovernanceChangeError("governance supplement has unknown or missing fields")
        event_id = _require_identifier(event.get("event_id"), SUPPLEMENT_ID_RE, "supplement event id")
        if event_id in seen:
            raise GovernanceChangeError("duplicate governance supplement event id")
        seen.add(event_id)
        if event.get("schema_version") != 1 or event.get("event_class") != SUPPLEMENT_CLASS:
            raise GovernanceChangeError("unregistered governance supplement class or schema")
        governance_id = _require_identifier(event.get("governance_id"), GOVERNANCE_ID_RE, "supplement GOV id")
        expected_event_id = governance_id.replace("GOV-", "GOVSUP-", 1)
        if event_id != expected_event_id:
            raise GovernanceChangeError(
                "governance supplement event identity does not match its GOV id"
            )
        if governance_id in seen_governance_ids:
            raise GovernanceChangeError(
                "a GOV entry may have only one retained supplement"
            )
        seen_governance_ids.add(governance_id)
        public = public_changes.get(governance_id)
        if public is None:
            raise GovernanceChangeError("governance supplement references an unknown GOV id")
        if event.get("public_entry_sha256") != public.entry_sha256:
            raise GovernanceChangeError("governance supplement public digest mismatch")
        _require_timestamp(event.get("recorded_at"))
        _require_text(event.get("provenance"), "supplement provenance")
        _require_text(event.get("decision_context"), "supplement decision context")
        _require_text_list(
            event.get("protected_references"),
            "supplement protected references",
        )
        _require_text_list(
            event.get("validation_references"),
            "supplement validation references",
        )
        if event.get("disclosure_review") != "owner_local_only":
            raise GovernanceChangeError(
                "governance supplement disclosure review is invalid"
            )
        _require_text(event.get("safe_summary"), "supplement safe summary")
        events.append(event)
    return events


def project_private_supplements(
    path: Path,
    public_changes: dict[str, GovernanceChange],
) -> dict[str, object]:
    """Produce unavailable rather than zero when required private evidence is absent."""

    try:
        events = parse_private_supplements(path, public_changes)
    except GovernanceChangeError as error:
        return {
            "availability": "unavailable",
            "complete": False,
            "items": [],
            "reason_code": "invalid-owner-local-governance-supplement",
            "reason": str(error),
        }
    event_ids = {str(event["governance_id"]) for event in events}
    required = {
        identifier
        for identifier, change in public_changes.items()
        if change.private_supplement_required
    }
    if required - event_ids:
        return {
            "availability": "unavailable",
            "complete": False,
            "items": [],
            "reason_code": "required-owner-local-governance-supplement-unavailable",
        }
    return {
        "availability": "current",
        "complete": True,
        "items": events,
        "reason_code": None,
    }
