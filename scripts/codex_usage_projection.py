#!/usr/bin/env python3
"""Strict public-safe schema and validation for owner-local Codex usage."""

from __future__ import annotations

import hashlib
import math
import re
import struct
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any


SCHEMA_VERSION = 2
PROJECTION_ID = "codex-usage"
PRODUCER_ID = "owner-local-codex-usage-sampler"
SAMPLER_CADENCE_SECONDS = 1800
WEEKLY_WINDOW_MINUTES = 10080
MAX_HISTORY_ITEMS = 512
MAX_RESET_WINDOWS = 64
MAX_ANOMALIES = 64
MAX_PLAN_TYPES = 8

TOP_FIELDS = frozenset(
    {
        "schema_version",
        "projection_id",
        "producer_id",
        "sampler_cadence_seconds",
        "generated_at",
        "trustworthy_through",
        "availability",
        "completeness",
        "reason_code",
        "current_through",
        "current",
        "history",
        "reset_windows",
        "anomalies",
        "estimates",
    }
)
CURRENT_FIELDS = frozenset(
    {
        "observed_at",
        "plan_type",
        "used_percent",
        "remaining_percent",
        "window_minutes",
        "resets_at",
        "reset_identity",
    }
)
HISTORY_FIELDS = frozenset({*CURRENT_FIELDS, "event_type"})
WINDOW_FIELDS = frozenset(
    {
        "reset_identity",
        "first_observed",
        "last_observed",
        "window_minutes",
        "resets_at",
        "plan_types",
        "min_used_percent",
        "max_used_percent",
        "observation_count",
        "material",
    }
)
ANOMALY_FIELDS = frozenset(
    {
        "anomaly_id",
        "type",
        "observed_at",
        "observed_reset_identity",
        "current_reset_identity",
    }
)
ESTIMATE_FIELDS = frozenset(
    {
        "available",
        "budget_available",
        "budget_reason_code",
        "burn_rate_available",
        "burn_rate_reason_code",
        "coverage_hours",
        "sample_count",
        "average_percent_per_day",
        "projected_exhaustion_at",
        "remaining_percent_per_day_budget",
        "confidence",
    }
)

PROJECTION_REASON_CODES = frozenset(
    {
        "no_valid_usage_observation",
        "owner_local_projection_required",
        "source_unavailable",
        "usage_readback_stale",
        "usage_readback_invalid",
    }
)
BUDGET_REASON_CODES = frozenset(
    {
        "projection_unavailable",
        "reset_boundary_elapsed",
        "budget_input_unavailable",
    }
)
BURN_RATE_REASON_CODES = frozenset(
    {
        "projection_unavailable",
        "burn_rate_input_unavailable",
        "insufficient_observation_coverage",
        "nonpositive_usage_change",
    }
)
EVENT_TYPES = frozenset(
    {"baseline", "usage_change", "reset_change", "plan_change"}
)
CONFIDENCE_VALUES = frozenset({"unavailable", "low", "medium", "high"})
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
RESET_ID = re.compile(r"^[1-9][0-9]{0,6}:[1-9][0-9]{0,11}$")
ANOMALY_ID = re.compile(
    r"^conflicting-reset-[1-9][0-9]{0,6}-[1-9][0-9]{0,11}-[1-9][0-9]{0,11}$"
)


class CodexUsageProjectionError(ValueError):
    """Raised when the minimized owner-local projection is incompatible."""


def iso_utc(value: datetime) -> str:
    """Return one timezone-aware timestamp in the projection's UTC form."""

    if value.tzinfo is None:
        raise CodexUsageProjectionError("timestamp must be timezone-aware")
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def parse_timestamp(value: object) -> datetime | None:
    """Parse a timezone-aware ISO timestamp without accepting date inference."""

    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def reset_identity(window_minutes: int, resets_at: int) -> str:
    """Return the exact stable reset identity used by the sampler."""

    return f"{window_minutes}:{(resets_at + 30) // 60}"


def trustworthy_through(observed_at: datetime, resets_at: int) -> datetime:
    """Bound one reading by the sampler cadence and exact reset boundary."""

    if observed_at.tzinfo is None:
        raise CodexUsageProjectionError("observation time must be timezone-aware")
    reset_at = datetime.fromtimestamp(resets_at, timezone.utc)
    return min(
        observed_at.astimezone(timezone.utc)
        + timedelta(seconds=SAMPLER_CADENCE_SECONDS),
        reset_at,
    )


def unavailable_projection(
    reason_code: str = "owner_local_projection_required",
    *,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    """Return the one minimized unavailable projection shape."""

    if reason_code not in PROJECTION_REASON_CODES:
        raise CodexUsageProjectionError("unregistered projection reason code")
    return {
        "schema_version": SCHEMA_VERSION,
        "projection_id": PROJECTION_ID,
        "producer_id": PRODUCER_ID,
        "sampler_cadence_seconds": SAMPLER_CADENCE_SECONDS,
        "generated_at": iso_utc(generated_at) if generated_at is not None else None,
        "trustworthy_through": None,
        "availability": "unavailable",
        "completeness": "incomplete",
        "reason_code": reason_code,
        "current_through": None,
        "current": None,
        "history": [],
        "reset_windows": [],
        "anomalies": [],
        "estimates": {
            "available": False,
            "budget_available": False,
            "budget_reason_code": "projection_unavailable",
            "burn_rate_available": False,
            "burn_rate_reason_code": "projection_unavailable",
            "coverage_hours": None,
            "sample_count": None,
            "average_percent_per_day": None,
            "projected_exhaustion_at": None,
            "remaining_percent_per_day_budget": None,
            "confidence": None,
        },
    }


def _number(value: object, *, minimum: float = 0) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) >= minimum
    )


def _percentage(value: object) -> bool:
    return _number(value) and float(value) <= 100


def _safe_id(value: object, *, maximum: int = 128) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= maximum
        and SAFE_ID.fullmatch(value) is not None
    )


def _reset_time(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 946684800 <= value <= 4102444800
    )


def _valid_reset_identity(value: object, window: object, reset_at: object) -> bool:
    return (
        isinstance(value, str)
        and RESET_ID.fullmatch(value) is not None
        and isinstance(window, int)
        and not isinstance(window, bool)
        and isinstance(reset_at, int)
        and not isinstance(reset_at, bool)
        and value == reset_identity(window, reset_at)
    )


def _valid_usage_record(
    value: object,
    *,
    current: bool,
    generated_at: datetime,
) -> bool:
    expected = CURRENT_FIELDS if current else HISTORY_FIELDS
    if not isinstance(value, Mapping) or set(value) != expected:
        return False
    observed_at = parse_timestamp(value.get("observed_at"))
    if (
        observed_at is None
        or observed_at > generated_at
        or not _safe_id(value.get("plan_type"), maximum=64)
        or not _percentage(value.get("used_percent"))
        or not _percentage(value.get("remaining_percent"))
        or abs(
            float(value["used_percent"])
            + float(value["remaining_percent"])
            - 100
        )
        > 0.001
        or value.get("window_minutes") != WEEKLY_WINDOW_MINUTES
        or not _reset_time(value.get("resets_at"))
        or not _valid_reset_identity(
            value.get("reset_identity"),
            value.get("window_minutes"),
            value.get("resets_at"),
        )
        or datetime.fromtimestamp(value["resets_at"], timezone.utc) < observed_at
    ):
        return False
    return current or value.get("event_type") in EVENT_TYPES


def _valid_window(value: object, *, generated_at: datetime) -> bool:
    if not isinstance(value, Mapping) or set(value) != WINDOW_FIELDS:
        return False
    first = parse_timestamp(value.get("first_observed"))
    last = parse_timestamp(value.get("last_observed"))
    plan_types = value.get("plan_types")
    reset_at = value.get("resets_at")
    if (
        first is None
        or last is None
        or first > last
        or last > generated_at
        or value.get("window_minutes") != WEEKLY_WINDOW_MINUTES
        or not _reset_time(reset_at)
        or not _valid_reset_identity(
            value.get("reset_identity"),
            value.get("window_minutes"),
            reset_at,
        )
        or last > datetime.fromtimestamp(reset_at, timezone.utc)
        or not isinstance(plan_types, list)
        or not 1 <= len(plan_types) <= MAX_PLAN_TYPES
        or plan_types != sorted(set(plan_types))
        or not all(_safe_id(item, maximum=64) for item in plan_types)
        or not _percentage(value.get("min_used_percent"))
        or not _percentage(value.get("max_used_percent"))
        or float(value["min_used_percent"]) > float(value["max_used_percent"])
        or not isinstance(value.get("observation_count"), int)
        or isinstance(value.get("observation_count"), bool)
        or value["observation_count"] < 1
        or not isinstance(value.get("material"), bool)
    ):
        return False
    return True


def _valid_anomaly(value: object, *, generated_at: datetime) -> bool:
    return (
        isinstance(value, Mapping)
        and set(value) == ANOMALY_FIELDS
        and isinstance(value.get("anomaly_id"), str)
        and ANOMALY_ID.fullmatch(value["anomaly_id"]) is not None
        and value.get("type") == "conflicting_reset_identity"
        and (observed := parse_timestamp(value.get("observed_at"))) is not None
        and observed <= generated_at
        and isinstance(value.get("observed_reset_identity"), str)
        and RESET_ID.fullmatch(value["observed_reset_identity"]) is not None
        and isinstance(value.get("current_reset_identity"), str)
        and RESET_ID.fullmatch(value["current_reset_identity"]) is not None
        and value["observed_reset_identity"] != value["current_reset_identity"]
    )


def _valid_estimates(
    value: object,
    *,
    projection_current: bool,
    current_through: datetime | None,
) -> bool:
    if not isinstance(value, Mapping) or set(value) != ESTIMATE_FIELDS:
        return False
    if any(
        not isinstance(value.get(key), bool)
        for key in ("available", "budget_available", "burn_rate_available")
    ):
        return False
    if value["available"] is not (
        value["budget_available"] or value["burn_rate_available"]
    ):
        return False
    if not projection_current:
        return (
            value["available"] is False
            and value["budget_available"] is False
            and value["budget_reason_code"] == "projection_unavailable"
            and value["burn_rate_available"] is False
            and value["burn_rate_reason_code"] == "projection_unavailable"
            and all(
                value.get(field) is None
                for field in (
                    "coverage_hours",
                    "sample_count",
                    "average_percent_per_day",
                    "projected_exhaustion_at",
                    "remaining_percent_per_day_budget",
                    "confidence",
                )
            )
        )
    if (
        not _number(value.get("coverage_hours"))
        or not isinstance(value.get("sample_count"), int)
        or isinstance(value.get("sample_count"), bool)
        or value["sample_count"] < 1
        or value.get("confidence") not in CONFIDENCE_VALUES
    ):
        return False
    if value["budget_available"]:
        if (
            value.get("budget_reason_code") is not None
            or not _number(value.get("remaining_percent_per_day_budget"))
        ):
            return False
    elif (
        value.get("budget_reason_code") not in BUDGET_REASON_CODES
        or value.get("remaining_percent_per_day_budget") is not None
    ):
        return False
    if value["burn_rate_available"]:
        exhaustion = parse_timestamp(value.get("projected_exhaustion_at"))
        if (
            value.get("burn_rate_reason_code") is not None
            or not _number(value.get("average_percent_per_day"))
            or exhaustion is None
            or current_through is None
            or exhaustion < current_through
            or value.get("confidence") == "unavailable"
        ):
            return False
    elif (
        value.get("burn_rate_reason_code") not in BURN_RATE_REASON_CODES
        or value.get("average_percent_per_day") is not None
        or value.get("projected_exhaustion_at") is not None
    ):
        return False
    return True


def validate_projection(
    value: object,
    *,
    now: datetime | None = None,
) -> tuple[str, bool]:
    """Validate the complete projection and return owner-envelope posture."""

    if not isinstance(value, Mapping) or set(value) != TOP_FIELDS:
        raise CodexUsageProjectionError(
            "Codex usage projection has unknown or missing fields"
        )
    current = value.get("availability") == "current"
    if (
        value.get("schema_version") != SCHEMA_VERSION
        or value.get("projection_id") != PROJECTION_ID
        or value.get("producer_id") != PRODUCER_ID
        or value.get("sampler_cadence_seconds") != SAMPLER_CADENCE_SECONDS
        or value.get("availability") not in {"current", "unavailable"}
        or value.get("completeness") not in {"complete", "incomplete"}
        or not isinstance(value.get("history"), list)
        or not isinstance(value.get("reset_windows"), list)
        or not isinstance(value.get("anomalies"), list)
        or not isinstance(value.get("estimates"), Mapping)
        or len(value["history"]) > MAX_HISTORY_ITEMS
        or len(value["reset_windows"]) > MAX_RESET_WINDOWS
        or len(value["anomalies"]) > MAX_ANOMALIES
    ):
        raise CodexUsageProjectionError(
            "Codex usage projection violates its fixed schema"
        )
    generated_at = parse_timestamp(value.get("generated_at"))
    if current:
        current_through = parse_timestamp(value.get("current_through"))
        trustworthy = parse_timestamp(value.get("trustworthy_through"))
        if (
            value.get("completeness") != "complete"
            or value.get("reason_code") is not None
            or generated_at is None
            or current_through is None
            or trustworthy is None
            or current_through > generated_at
            or not _valid_usage_record(
                value.get("current"),
                current=True,
                generated_at=generated_at,
            )
            or current_through
            != parse_timestamp(value["current"].get("observed_at"))
            or trustworthy
            != trustworthy_through(
                current_through,
                value["current"]["resets_at"],
            )
            or generated_at > trustworthy
        ):
            raise CodexUsageProjectionError(
                "Codex usage currentness or chronology is invalid"
            )
        checked_at = now or datetime.now(timezone.utc)
        if checked_at.tzinfo is None:
            raise CodexUsageProjectionError("validation time must be timezone-aware")
        if checked_at.astimezone(timezone.utc) > trustworthy:
            raise CodexUsageProjectionError("Codex usage projection is stale")
    else:
        current_through = None
        if (
            value.get("completeness") != "incomplete"
            or value.get("reason_code") not in PROJECTION_REASON_CODES
            or value.get("current") is not None
            or value.get("current_through") is not None
            or value.get("trustworthy_through") is not None
            or value["history"]
            or value["reset_windows"]
            or value["anomalies"]
            or (
                value.get("generated_at") is not None
                and generated_at is None
            )
        ):
            raise CodexUsageProjectionError(
                "Codex usage unavailable projection is incompatible"
            )
    if current:
        if not all(
            _valid_usage_record(
                item,
                current=False,
                generated_at=generated_at,
            )
            for item in value["history"]
        ):
            raise CodexUsageProjectionError("Codex usage history is invalid")
        history_order = [
            parse_timestamp(item["observed_at"]) for item in value["history"]
        ]
        history_ids = [
            (
                item["observed_at"],
                item["event_type"],
                item["reset_identity"],
            )
            for item in value["history"]
        ]
        if (
            history_order != sorted(history_order)
            or len(history_ids) != len(set(history_ids))
            or any(item > current_through for item in history_order)
        ):
            raise CodexUsageProjectionError(
                "Codex usage history order or identity is invalid"
            )
        if not all(
            _valid_window(item, generated_at=generated_at)
            for item in value["reset_windows"]
        ):
            raise CodexUsageProjectionError("Codex usage reset windows are invalid")
        window_ids = [item["reset_identity"] for item in value["reset_windows"]]
        if (
            window_ids != list(dict.fromkeys(window_ids))
            or [item["resets_at"] for item in value["reset_windows"]]
            != sorted(item["resets_at"] for item in value["reset_windows"])
        ):
            raise CodexUsageProjectionError(
                "Codex usage reset-window identity or order is invalid"
            )
        if not all(
            _valid_anomaly(item, generated_at=generated_at)
            for item in value["anomalies"]
        ):
            raise CodexUsageProjectionError("Codex usage anomalies are invalid")
        anomaly_ids = [item["anomaly_id"] for item in value["anomalies"]]
        if (
            len(anomaly_ids) != len(set(anomaly_ids))
            or [item["observed_at"] for item in value["anomalies"]]
            != sorted(item["observed_at"] for item in value["anomalies"])
        ):
            raise CodexUsageProjectionError(
                "Codex usage anomaly identity or order is invalid"
            )
    if not _valid_estimates(
        value["estimates"],
        projection_current=current,
        current_through=current_through,
    ):
        raise CodexUsageProjectionError("Codex usage estimates are invalid")
    return ("current", True) if current else ("unavailable", False)


def projection_is_valid(
    value: object,
    *,
    now: datetime | None = None,
) -> bool:
    """Return false instead of exposing detailed validation diagnostics."""

    try:
        validate_projection(value, now=now)
    except CodexUsageProjectionError:
        return False
    return True


def _integrity_material(value: object) -> bytes:
    """Encode JSON-compatible data identically in Python and the browser."""

    if value is None:
        return b"n;"
    if value is True:
        return b"b1;"
    if value is False:
        return b"b0;"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        if not math.isfinite(number):
            raise CodexUsageProjectionError("non-finite payload number")
        return b"f" + struct.pack(">d", number).hex().encode("ascii") + b";"
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return b"s" + str(len(encoded)).encode("ascii") + b":" + encoded
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return (
            b"a"
            + str(len(value)).encode("ascii")
            + b"["
            + b"".join(_integrity_material(item) for item in value)
            + b"]"
        )
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise CodexUsageProjectionError("payload object keys must be strings")
        keys = sorted(value)
        return (
            b"o"
            + str(len(keys)).encode("ascii")
            + b"{"
            + b"".join(
                _integrity_material(key) + _integrity_material(value[key])
                for key in keys
            )
            + b"}"
        )
    raise CodexUsageProjectionError("unsupported payload value")


def canonical_payload_digest(value: Mapping[str, Any]) -> str:
    """Return the semantic payload digest verified by the owner Console."""

    return "sha256:" + hashlib.sha256(_integrity_material(value)).hexdigest()
