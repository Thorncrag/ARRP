#!/usr/bin/env python3
"""Deterministic Elim arithmetic, validation planning, and closeout compilation."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from operational_incidents import (
        IncidentContractError,
        validate_incident_report,
    )
except ModuleNotFoundError:
    from scripts.operational_incidents import (
        IncidentContractError,
        validate_incident_report,
    )

try:
    from arrp_context import (
        ContextError,
        GAP_OBLIGATION_CLOSED_STATUSES,
        GAP_OBLIGATION_STATUSES,
        ROOT,
        canonical_json,
        file_provenance,
        parse_time,
        sha256_bytes,
        validate_gap_obligation_state,
    )
except ModuleNotFoundError:  # Imported as scripts.elim_execution.
    from scripts.arrp_context import (
        ContextError,
        GAP_OBLIGATION_CLOSED_STATUSES,
        GAP_OBLIGATION_STATUSES,
        ROOT,
        canonical_json,
        file_provenance,
        parse_time,
        sha256_bytes,
        validate_gap_obligation_state,
    )


RUBRIC_VERSION = "2026-06-27.2"
COMPONENTS = {
    "structural": 8,
    "evidence": 12,
    "legal_fit": 10,
    "prior_proposal": 8,
    "remedy": 12,
    "implementation": 8,
    "abuse_resistance": 8,
    "drafting": 8,
    "cogency": 6,
    "adoption": 12,
    "project_integration": 4,
    "external_review": 4,
}
PENALTIES = {
    "unsupported_material_factual_claim": 5,
    "unsupported_material_legal_claim": 5,
    "missing_nearby_event_citation": 3,
    "missing_source_inventory_row": 2,
    "citation_mismatch": 5,
    "invented_or_unverified_authority": 10,
    "unchecked_currency_claim": 5,
    "missing_internal_project_link": 1,
    "same_failed_institution_without_fallback": 8,
    "serious_abuse_risk_unaddressed": 8,
    "unjustified_legislative_convention_departure": 5,
    "judicial_scrutiny_risk_unidentified": 5,
    "pending_controlling_case_unchecked": 5,
    "existing_law_path_unchecked": 5,
    "duplicative_ownership_unresolved": 5,
    "required_status_or_reframing_check_missing": 5,
    "material_reframing_not_reflected": 10,
}
AUTHORITY_DISPOSITIONS = {
    "permitted",
    "human_reserved",
    "forbidden",
    "unsafe",
    "out_of_scope",
    "uncertain",
}
AFFECTED_SURFACES = {
    "repository",
    "github_issue",
    "github_project",
    "source",
    "monitoring",
    "automation",
    "console",
    "publication",
    "public",
}
DISCOVERY_DISPOSITIONS = {
    "fixed",
    "reported",
    "retained",
    "no_material_finding",
    "review_completed",
}
OUTSIDE_CONTRIBUTION_CHECKS = {
    "identity",
    "classification",
    "required_fields",
    "canonical_linkage",
    "evidence_and_provenance",
    "lifecycle_and_authority",
    "generated_views",
    "tests",
    "documentation",
}
SAFE_DISCOVERY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
EXACT_REVISION = re.compile(r"^(?:[0-9a-f]{40}|sha256:[0-9a-f]{64}|[0-9a-f]{64})$")
DISCOVERY_MARKER_RE = re.compile(
    r"^<!-- ELIM-DISCOVERY-V1 ([A-Za-z0-9+/=]+) -->$",
    re.MULTILINE,
)


def score_band(score: int) -> str:
    if score == 0:
        return "Not Scored"
    if score <= 49:
        return "Early/Partial Draft"
    if score <= 64:
        return "Developed Draft"
    if score <= 74:
        return "Substantially Developed Draft"
    if score <= 84:
        return "Review Ready"
    if score <= 89:
        return "Advanced Review Ready"
    if score <= 94:
        return "Proposal Ready"
    if score <= 99:
        return "Publication Ready"
    return "Fully Validated"


def calculate_score(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("rubric_version") != RUBRIC_VERSION:
        raise ContextError(f"score input must declare human-approved rubric {RUBRIC_VERSION}")
    supplied = value.get("components")
    if not isinstance(supplied, dict) or set(supplied) != set(COMPONENTS):
        missing = sorted(set(COMPONENTS) - set(supplied or {}))
        extra = sorted(set(supplied or {}) - set(COMPONENTS))
        raise ContextError(f"score components differ from rubric; missing={missing}, extra={extra}")
    component_rows = []
    subtotal = 0.0
    for name, maximum in COMPONENTS.items():
        row = supplied[name]
        if not isinstance(row, dict):
            raise ContextError(f"component {name} must contain rating and evidence_ref")
        rating = row.get("rating")
        if rating not in {"zero", "half", "full"}:
            raise ContextError(f"component {name} rating must be zero, half, or full")
        evidence_ref = str(row.get("evidence_ref") or "").strip()
        if not evidence_ref:
            raise ContextError(f"component {name} requires an evidence_ref supplied by the auditor")
        points = {"zero": 0, "half": maximum / 2, "full": maximum}[rating]
        subtotal += points
        component_rows.append(
            {
                "component": name,
                "maximum": maximum,
                "rating": rating,
                "points": points,
                "evidence_ref": evidence_ref,
            }
        )
    penalty_rows = []
    penalty_total = 0
    for row in value.get("penalties") or []:
        code = str(row.get("code") or "")
        count = row.get("count")
        evidence_ref = str(row.get("evidence_ref") or "").strip()
        if code not in PENALTIES or not isinstance(count, int) or count < 1 or not evidence_ref:
            raise ContextError("each penalty requires an approved code, positive integer count, and evidence_ref")
        points = PENALTIES[code] * count
        penalty_total += points
        penalty_rows.append(
            {"code": code, "count": count, "points": -points, "evidence_ref": evidence_ref}
        )
    raw = max(0.0, min(100.0, subtotal - penalty_total))
    # Framework rule: ordinary whole-number rounding, exact halves round down.
    final_score = math.floor(raw + 0.499999999)
    return {
        "schema_version": 1,
        "rubric_version": RUBRIC_VERSION,
        "calculation_only": True,
        "judgment_supplied_externally": True,
        "components": component_rows,
        "subtotal": subtotal,
        "penalties": penalty_rows,
        "penalty_total": penalty_total,
        "raw_score": raw,
        "final_score": final_score,
        "band": score_band(final_score),
    }


def validation_plan(files: list[str], task_type: str) -> dict[str, Any]:
    normalized = sorted(set(path.strip().replace("\\", "/") for path in files if path.strip()))
    if any(path.startswith("/") or ".." in Path(path).parts for path in normalized):
        raise ContextError("validation paths must be repository-relative and may not escape the repository")
    checks: dict[str, dict[str, Any]] = {}

    def add(identifier: str, command: list[str], scope: str) -> None:
        checks[identifier] = {"id": identifier, "command": command, "scope": scope}

    add("diff_hygiene", ["git", "diff", "--check"], "changed files")
    if any(path.endswith(".py") for path in normalized):
        add("python_compile", ["python3", "-m", "compileall", "-q", "scripts"], "Python syntax")
    test_files = [path for path in normalized if path.startswith("tests/") and path.endswith(".py")]
    for path in test_files:
        add(
            f"test:{path}",
            ["python3", "-m", "unittest", path[:-3].replace("/", ".")],
            path,
        )
    if any(path.startswith(("areas/", "legislation/", "framework/", "inventory/")) for path in normalized):
        add(
            "repository_consistency",
            ["python3", "scripts/audit_project_consistency.py", "--exit-zero-on-findings"],
            "repository structure and metadata",
        )
    if any(path.startswith("research/project-console/") for path in normalized):
        add(
            "console_tests",
            ["python3", "-m", "unittest", "tests.test_horizon_intake"],
            "Project Console",
        )
    if any(
        path.startswith((".github/", "framework/project/automation/"))
        for path in normalized
    ):
        add(
            "automation_tests",
            ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*bot.py"],
            "persistent automation",
        )
    if task_type in {"comprehensive_review", "governance_change"}:
        add(
            "full_repository_tests",
            ["python3", "-m", "unittest", "discover", "-s", "tests"],
            "complete repository test suite",
        )
    issue_ids = sorted(
        {
            part.removesuffix(".audit").removesuffix(".md")
            for path in normalized
            for part in [Path(path).name]
            if path.startswith("areas/") and re_issue_id(part)
        }
    )
    return {
        "schema_version": 1,
        "task_type": task_type,
        "changed_files": normalized,
        "issue_ids": issue_ids,
        "checks": list(checks.values()),
        "full_suite_required": task_type in {"comprehensive_review", "governance_change"},
    }


def re_issue_id(filename: str) -> bool:
    stem = filename.split(".", 1)[0]
    parts = stem.split("-")
    return len(parts) == 2 and parts[0].isupper() and parts[1].isdigit()


def summarize_validation(plan: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    expected = {row["id"] for row in plan.get("checks") or []}
    observed: set[str] = set()
    compact = []
    for row in results:
        identifier = str(row.get("id") or "")
        status = str(row.get("status") or "")
        if identifier not in expected:
            raise ContextError(f"validation result was not planned: {identifier}")
        if identifier in observed:
            raise ContextError(f"duplicate validation result: {identifier}")
        if status not in {"passed", "failed", "skipped"}:
            raise ContextError(f"invalid validation status for {identifier}: {status}")
        observed.add(identifier)
        compact.append(
            {
                "id": identifier,
                "status": status,
                "duration_seconds": row.get("duration_seconds"),
                "summary": str(row.get("summary") or "")[:500],
            }
        )
    missing = sorted(expected - observed)
    return {
        "schema_version": 1,
        "status": (
            "failed"
            if any(row["status"] == "failed" for row in compact)
            else "incomplete"
            if missing or any(row["status"] == "skipped" for row in compact)
            else "passed"
        ),
        "counts": {
            "expected": len(expected),
            "reported": len(observed),
            "passed": sum(row["status"] == "passed" for row in compact),
            "failed": sum(row["status"] == "failed" for row in compact),
            "skipped": sum(row["status"] == "skipped" for row in compact),
        },
        "missing": missing,
        "results": compact,
    }


def _nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_relative_path(value: Any) -> bool:
    if not _nonblank(value):
        return False
    path = Path(str(value))
    return not path.is_absolute() and ".." not in path.parts


def _validate_validation_readback(value: Any, *, label: str) -> None:
    if not isinstance(value, list) or not value:
        raise ContextError(f"{label} validation_readback must be a nonempty array")
    expected = {"check", "status", "evidence"}
    for row in value:
        if (
            not isinstance(row, dict)
            or set(row) != expected
            or not _nonblank(row.get("check"))
            or row.get("status") not in {"passed", "failed", "skipped"}
            or not _nonblank(row.get("evidence"))
        ):
            raise ContextError(f"{label} validation_readback entry is malformed")


def _validate_outside_contribution(value: Any, *, label: str) -> None:
    if value is None:
        return
    expected = {
        "identity",
        "revision",
        "classification",
        "checks",
        "integration_posture",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ContextError(f"{label} outside_contribution fields are malformed")
    if (
        not _nonblank(value.get("identity"))
        or not isinstance(value.get("revision"), str)
        or EXACT_REVISION.fullmatch(value["revision"]) is None
        or not _nonblank(value.get("classification"))
        or value.get("integration_posture")
        not in {"ready", "blocked", "human_review", "not_applicable"}
    ):
        raise ContextError(f"{label} outside_contribution identity is invalid")
    checks = value.get("checks")
    if not isinstance(checks, list):
        raise ContextError(f"{label} outside_contribution checks must be an array")
    by_name: dict[str, dict[str, Any]] = {}
    for row in checks:
        if (
            not isinstance(row, dict)
            or set(row) != {"check", "status", "evidence"}
            or row.get("check") not in OUTSIDE_CONTRIBUTION_CHECKS
            or row.get("status") not in {"passed", "failed", "blocked"}
            or not _nonblank(row.get("evidence"))
        ):
            raise ContextError(f"{label} outside_contribution check is malformed")
        if row["check"] in by_name:
            raise ContextError(f"{label} repeats an outside_contribution check")
        by_name[row["check"]] = row
    if set(by_name) != OUTSIDE_CONTRIBUTION_CHECKS:
        raise ContextError(
            f"{label} outside_contribution checks do not cover the required floor"
        )
    if value["integration_posture"] == "ready" and any(
        row["status"] != "passed" for row in checks
    ):
        raise ContextError(
            f"{label} outside contribution cannot be ready with an incomplete check"
        )


def validate_discovery_records(value: dict[str, Any]) -> None:
    """Validate canonical discovery detail plus stable obligation transitions."""
    discovered = value.get("discovered_work_units")
    updates = value.get("gap_obligation_updates")
    if not isinstance(discovered, list) or not isinstance(updates, list):
        raise ContextError(
            "discovered_work_units and gap_obligation_updates must be arrays"
        )
    if len(discovered) > 128 or len(updates) > 128:
        raise ContextError("Elim discovery result exceeds its bounded capacity")

    unit_fields = {
        "id",
        "obligation_id",
        "domain",
        "discovery_context",
        "observed_at",
        "source_revision",
        "evidence",
        "reasoning",
        "uncertainty",
        "affected_records",
        "consequence",
        "authority",
        "action_rationale",
        "changed_files",
        "affected_surfaces",
        "validation_readback",
        "disposition",
        "canonical_detail",
        "provenance",
        "owner",
        "next_action",
        "next_trigger",
        "outside_contribution",
    }
    units: dict[str, dict[str, Any]] = {}
    declared_files = set(value.get("files_touched") or [])
    for row in discovered:
        if not isinstance(row, dict) or set(row) != unit_fields:
            raise ContextError(
                "discovered work-unit fields do not match the approved schema"
            )
        unit_id = str(row.get("id") or "")
        if not SAFE_DISCOVERY_ID.fullmatch(unit_id) or unit_id in units:
            raise ContextError("discovered work-unit identity is invalid or repeated")
        units[unit_id] = row
        for field in (
            "domain",
            "discovery_context",
            "reasoning",
            "consequence",
            "action_rationale",
            "owner",
            "next_action",
            "next_trigger",
        ):
            if not _nonblank(row.get(field)):
                raise ContextError(f"discovered work unit requires {field}")
        if parse_time(row.get("observed_at")) is None:
            raise ContextError(
                "discovered work unit requires an exact observation time"
            )
        if (
            not isinstance(row.get("source_revision"), str)
            or EXACT_REVISION.fullmatch(row["source_revision"]) is None
        ):
            raise ContextError(
                "discovered work unit requires an exact source revision"
            )
        for field in ("evidence", "affected_records", "provenance"):
            entries = row.get(field)
            if not isinstance(entries, list) or not all(_nonblank(x) for x in entries):
                raise ContextError(
                    f"discovered work-unit {field} must be a string array"
                )
        if not row["evidence"] or not row["provenance"]:
            raise ContextError(
                "discovered work-unit evidence and linked provenance may not be empty"
            )
        if row.get("uncertainty") is not None and not _nonblank(
            row.get("uncertainty")
        ):
            raise ContextError(
                "discovered work-unit uncertainty must be null or nonblank"
            )
        authority = row.get("authority")
        if not isinstance(authority, dict) or set(authority) != {
            "classification",
            "basis",
            "disposition",
        }:
            raise ContextError("discovered work-unit authority is malformed")
        if (
            authority.get("classification")
            not in {"mechanical", "delegated_judgment", "human_reserved"}
            or not _nonblank(authority.get("basis"))
            or authority.get("disposition") not in AUTHORITY_DISPOSITIONS
        ):
            raise ContextError("discovered work-unit authority is invalid")
        if (
            authority["classification"] == "human_reserved"
            and authority["disposition"] == "permitted"
        ):
            raise ContextError(
                "human-reserved discovery may not claim permitted implementation"
            )
        surfaces = row.get("affected_surfaces")
        if (
            not isinstance(surfaces, list)
            or not surfaces
            or len(surfaces) != len(set(surfaces))
            or not set(surfaces) <= AFFECTED_SURFACES
        ):
            raise ContextError("discovered work-unit affected_surfaces are invalid")
        changed = row.get("changed_files")
        if (
            not isinstance(changed, list)
            or len(changed) != len(set(changed))
            or not all(_safe_relative_path(path) for path in changed)
            or not set(changed) <= declared_files
        ):
            raise ContextError(
                "discovered work-unit changed_files are unsafe or undeclared"
            )
        if not _safe_relative_path(row.get("canonical_detail")):
            raise ContextError("discovered work-unit canonical detail path is unsafe")
        if row["canonical_detail"] not in declared_files:
            raise ContextError(
                "discovered work-unit canonical detail is not in files_touched"
            )
        _validate_validation_readback(row["validation_readback"], label=unit_id)
        _validate_outside_contribution(
            row.get("outside_contribution"),
            label=unit_id,
        )
        disposition = row.get("disposition")
        if disposition not in DISCOVERY_DISPOSITIONS:
            raise ContextError("discovered work-unit disposition is invalid")
        obligation_id = row.get("obligation_id")
        if disposition in {"no_material_finding", "review_completed"}:
            if obligation_id is not None:
                raise ContextError(
                    "review-control record may not create a gap obligation"
                )
        elif (
            not isinstance(obligation_id, str)
            or SAFE_DISCOVERY_ID.fullmatch(obligation_id) is None
        ):
            raise ContextError(
                "a confirmed discovered finding requires a stable obligation ID"
            )
        if disposition == "fixed":
            if (
                authority["disposition"] != "permitted"
                or authority["classification"] == "human_reserved"
                or not changed
                or any(
                    check["status"] != "passed"
                    for check in row["validation_readback"]
                )
            ):
                raise ContextError(
                    "fixed discovery requires permitted authority, changed files, "
                    "and passing validation/readback"
                )
        if authority["disposition"] in {
            "forbidden",
            "unsafe",
            "out_of_scope",
            "uncertain",
        } and disposition == "fixed":
            raise ContextError(
                "forbidden, unsafe, out-of-scope, or uncertain discovery may not "
                "be reported as fixed"
            )
        if (
            disposition == "review_completed"
            and row["domain"] != "project-governance-review"
        ):
            raise ContextError(
                "review_completed is reserved for the governance-review control record"
            )
        if (
            row["domain"] == "project-governance-review"
            and disposition not in {"no_material_finding", "review_completed"}
        ):
            raise ContextError(
                "project-governance review control has an invalid disposition"
            )

    governance_controls = [
        unit
        for unit in units.values()
        if unit["domain"] == "project-governance-review"
    ]
    if len(governance_controls) > 1:
        raise ContextError(
            "Elim result repeats the project-governance review control record"
        )
    if governance_controls:
        control = governance_controls[0]
        confirmed = [
            unit
            for unit in units.values()
            if unit is not control
            and unit["disposition"]
            not in {"no_material_finding", "review_completed"}
        ]
        expected_control_disposition = (
            "review_completed" if confirmed else "no_material_finding"
        )
        if control["disposition"] != expected_control_disposition:
            raise ContextError(
                "project-governance review-control disposition contradicts its "
                "confirmed discovered findings"
            )

    update_fields = {
        "obligation_id",
        "discovered_work_unit_id",
        "status",
        "observed_at",
        "resolution",
    }
    updates_by_unit: dict[str, dict[str, Any]] = {}
    obligation_ids: set[str] = set()
    for update in updates:
        if not isinstance(update, dict) or set(update) != update_fields:
            raise ContextError(
                "gap-obligation update fields do not match the approved schema"
            )
        obligation_id = str(update.get("obligation_id") or "")
        unit_id = str(update.get("discovered_work_unit_id") or "")
        if (
            SAFE_DISCOVERY_ID.fullmatch(obligation_id) is None
            or obligation_id in obligation_ids
            or unit_id not in units
            or unit_id in updates_by_unit
            or update.get("status") not in GAP_OBLIGATION_STATUSES
            or parse_time(update.get("observed_at")) is None
        ):
            raise ContextError("gap-obligation update identity or status is invalid")
        obligation_ids.add(obligation_id)
        updates_by_unit[unit_id] = update
        unit = units[unit_id]
        if unit.get("obligation_id") != obligation_id:
            raise ContextError(
                "gap-obligation update does not match its discovered work unit"
            )
        if update["observed_at"] != unit["observed_at"]:
            raise ContextError(
                "gap-obligation update time differs from its discovered work unit"
            )
        resolution = update.get("resolution")
        if update["status"] in GAP_OBLIGATION_CLOSED_STATUSES:
            if not isinstance(resolution, dict) or set(resolution) != {
                "kind",
                "verified_at",
                "evidence",
                "source_revision",
                "recorded_by",
            }:
                raise ContextError(
                    "closed gap-obligation update lacks resolution proof"
                )
            if (
                resolution.get("kind")
                not in {"verified_resolution", "human_disposition"}
                or parse_time(resolution.get("verified_at")) is None
                or not _nonblank(resolution.get("evidence"))
                or not isinstance(resolution.get("source_revision"), str)
                or EXACT_REVISION.fullmatch(resolution["source_revision"]) is None
                or not _nonblank(resolution.get("recorded_by"))
            ):
                raise ContextError("gap-obligation resolution proof is invalid")
            if update["status"] == "resolved":
                if (
                    resolution["kind"] != "verified_resolution"
                    or unit["disposition"] != "fixed"
                    or unit["authority"]["disposition"] != "permitted"
                    or any(
                        check["status"] != "passed"
                        for check in unit["validation_readback"]
                    )
                ):
                    raise ContextError(
                        "verified gap closure lacks permitted repair and full "
                        "validation/readback proof"
                    )
            elif resolution["kind"] != "human_disposition":
                raise ContextError(
                    "human-disposition closure lacks recorded human disposition"
                )
        elif resolution is not None:
            raise ContextError(
                "open gap-obligation update may not carry resolution proof"
            )
        if unit["authority"]["disposition"] in {
            "forbidden",
            "unsafe",
            "out_of_scope",
            "uncertain",
        } and update["status"] == "resolved":
            raise ContextError(
                "a prohibited, unsafe, out-of-scope, or uncertain finding may not "
                "close as a verified repair"
            )
        if unit["disposition"] == "fixed" and update["status"] != "resolved":
            raise ContextError("fixed discovery must close with verified resolution")
        if unit["disposition"] == "reported" and update["status"] == "resolved":
            raise ContextError("reporting a finding is not closure proof")
        if unit["disposition"] == "retained" and update["status"] in {
            "resolved",
            "human_disposition",
        }:
            raise ContextError("retained uncertainty may not be reported as closed")

    expected_updates = {
        unit_id
        for unit_id, unit in units.items()
        if unit["disposition"] not in {"no_material_finding", "review_completed"}
    }
    if set(updates_by_unit) != expected_updates:
        raise ContextError(
            "every confirmed discovered finding requires exactly one linked "
            "gap-obligation update"
        )


def merge_gap_obligation_state(
    prior_state: dict[str, Any] | None,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Merge validated discoveries without closing absent or merely reported gaps."""
    validate_discovery_records(result)
    prior = prior_state or {
        "schema_version": 1,
        "updated_at": None,
        "governance_review": None,
        "items": [],
    }
    prior_items = validate_gap_obligation_state(prior)
    by_id = {item["obligation_id"]: dict(item) for item in prior_items}
    units = {
        item["id"]: item for item in result.get("discovered_work_units") or []
    }
    latest = parse_time(prior.get("updated_at"))
    governance_review = prior.get("governance_review")
    governance_controls = [
        item
        for item in result.get("discovered_work_units") or []
        if item["domain"] == "project-governance-review"
    ]
    if governance_controls:
        control = governance_controls[0]
        observed = parse_time(control["observed_at"])
        assert observed is not None
        prior_reviewed = parse_time(
            (governance_review or {}).get("last_reviewed_at")
        )
        if prior_reviewed is not None and observed < prior_reviewed:
            raise ContextError(
                "governance-review control predates the retained review boundary"
            )
        if not _nonblank(result.get("unit_id")):
            raise ContextError(
                "governance-review control requires its selected work-unit ID"
            )
        governance_review = {
            "last_reviewed_at": control["observed_at"],
            "run_id": result["run_id"],
            "selected_unit_id": result["unit_id"],
            "discovered_work_unit_id": control["id"],
            "source_revision": control["source_revision"],
            "disposition": control["disposition"],
            "canonical_detail": control["canonical_detail"],
            "next_trigger": control["next_trigger"],
        }
        if latest is None or observed > latest:
            latest = observed
    for update in result.get("gap_obligation_updates") or []:
        unit = units[update["discovered_work_unit_id"]]
        observed = parse_time(update["observed_at"])
        assert observed is not None
        existing = by_id.get(update["obligation_id"])
        if existing:
            previous_checked = parse_time(existing["last_checked"])
            if previous_checked is not None and observed < previous_checked:
                raise ContextError(
                    "gap-obligation update predates its retained last-checked time"
                )
            if existing["domain"] != unit["domain"]:
                raise ContextError(
                    "gap-obligation stable identity changed its discovery domain"
                )
            first_seen = existing["first_seen"]
            occurrences = [*existing["occurrences"]]
            status_history = [*existing["status_history"]]
            count = int(existing["occurrence_count"]) + 1
        else:
            first_seen = update["observed_at"]
            occurrences = []
            status_history = []
            count = 1
        first = parse_time(first_seen)
        assert first is not None
        occurrences.append(
            {
                "at": update["observed_at"],
                "run_id": result["run_id"],
                "discovered_work_unit_id": unit["id"],
                "source_revision": unit["source_revision"],
                "status": update["status"],
                "canonical_detail": unit["canonical_detail"],
            }
        )
        resolution = update.get("resolution")
        status_history.append(
            {
                "status": update["status"],
                "at": update["observed_at"],
                "run_id": result["run_id"],
                "evidence": (
                    resolution["evidence"]
                    if isinstance(resolution, dict)
                    else unit["action_rationale"]
                ),
                "resolution": resolution,
            }
        )
        by_id[update["obligation_id"]] = {
            "obligation_id": update["obligation_id"],
            "title": unit["consequence"],
            "domain": unit["domain"],
            "severity": (
                "high"
                if unit["authority"]["disposition"]
                in {"forbidden", "unsafe", "human_reserved"}
                else "normal"
            ),
            "status": update["status"],
            "owner": unit["owner"],
            "authority": {
                "classification": unit["authority"]["classification"],
                "basis": unit["authority"]["basis"],
            },
            "authority_disposition": unit["authority"]["disposition"],
            "canonical_detail": unit["canonical_detail"],
            "provenance": list(unit["provenance"]),
            "source_revision": unit["source_revision"],
            "evidence": list(unit["evidence"]),
            "reasoning": unit["reasoning"],
            "uncertainty": unit["uncertainty"],
            "affected_records": list(unit["affected_records"]),
            "affected_surfaces": list(unit["affected_surfaces"]),
            "consequence": unit["consequence"],
            "action_rationale": unit["action_rationale"],
            "validation_readback": list(unit["validation_readback"]),
            "disposition": unit["disposition"],
            "exact_next_action": unit["next_action"],
            "next_trigger": unit["next_trigger"],
            "first_seen": first_seen,
            "last_checked": update["observed_at"],
            "occurrence_count": count,
            "age_days": max(
                0,
                int((observed - first).total_seconds() // 86400),
            ),
            "last_discovered_work_unit_id": unit["id"],
            "occurrences": occurrences,
            "status_history": status_history,
            "resolution": resolution,
        }
        if latest is None or observed > latest:
            latest = observed
    merged = {
        "schema_version": 1,
        "updated_at": (
            latest.isoformat(timespec="seconds") if latest is not None else None
        ),
        "governance_review": governance_review,
        "items": [by_id[key] for key in sorted(by_id)],
    }
    validate_gap_obligation_state(merged)
    return merged


def discovery_marker_payloads(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the exact committed payload for each discovery work unit."""
    validate_discovery_records(result)
    chain_id = result.get("run_id")
    selected_unit_id = result.get("unit_id")
    if not _nonblank(chain_id) or not _nonblank(selected_unit_id):
        raise ContextError(
            "discovery markers require the Chain ID and selected work-unit ID"
        )
    updates = {
        row["discovered_work_unit_id"]: row
        for row in result.get("gap_obligation_updates") or []
    }
    return [
        {
            "schema_version": 1,
            # The current run-chain contract uses the Chain ID as the Elim Run ID.
            # Preserve both names so the durable record remains explicit if those
            # concepts become distinct later.
            "chain_id": chain_id,
            "run_id": chain_id,
            "selected_unit_id": selected_unit_id,
            "discovered_work_unit": row,
            "gap_obligation_update": updates.get(row["id"]),
        }
        for row in result.get("discovered_work_units") or []
    ]


def render_discovery_markers(result: dict[str, Any]) -> str:
    """Render hidden, canonical, reconstructible markers for the Elim Run Log."""
    markers: list[str] = []
    for payload in discovery_marker_payloads(result):
        encoded = base64.b64encode(canonical_json(payload)).decode("ascii")
        markers.append(f"<!-- ELIM-DISCOVERY-V1 {encoded} -->")
    return "\n".join(markers)


def parse_discovery_markers(text: str) -> list[dict[str, Any]]:
    """Parse and validate canonical discovery markers from committed Run Log text."""
    payloads: list[dict[str, Any]] = []
    identities: set[tuple[str, str]] = set()
    expected_fields = {
        "schema_version",
        "chain_id",
        "run_id",
        "selected_unit_id",
        "discovered_work_unit",
        "gap_obligation_update",
    }
    for match in DISCOVERY_MARKER_RE.finditer(text):
        try:
            decoded = base64.b64decode(match.group(1), validate=True)
            payload = json.loads(decoded.decode("utf-8"))
        except (
            UnicodeDecodeError,
            ValueError,
            binascii.Error,
            json.JSONDecodeError,
        ) as error:
            raise ContextError("Elim discovery marker is not valid canonical JSON") from error
        if (
            not isinstance(payload, dict)
            or set(payload) != expected_fields
            or payload.get("schema_version") != 1
            or not _nonblank(payload.get("chain_id"))
            or payload.get("run_id") != payload.get("chain_id")
            or not _nonblank(payload.get("selected_unit_id"))
            or not isinstance(payload.get("discovered_work_unit"), dict)
        ):
            raise ContextError("Elim discovery marker fields are malformed")
        unit = payload["discovered_work_unit"]
        update = payload.get("gap_obligation_update")
        unit_id = str(unit.get("id") or "")
        if SAFE_DISCOVERY_ID.fullmatch(unit_id) is None:
            raise ContextError("Elim discovery marker has an invalid work-unit ID")
        identity = (payload["run_id"], unit_id)
        if identity in identities:
            raise ContextError("Elim Run Log repeats a discovery marker identity")
        identities.add(identity)
        # Require the marker bytes themselves to be canonical, not merely
        # parseable, so reconstruction cannot admit two encodings of one record.
        if decoded != canonical_json(payload):
            raise ContextError("Elim discovery marker JSON is not canonical")
        payloads.append(payload)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for payload in payloads:
        key = (payload["run_id"], payload["selected_unit_id"])
        grouped.setdefault(key, []).append(payload)
    for (run_id, selected_unit_id), group in grouped.items():
        units = [payload["discovered_work_unit"] for payload in group]
        updates = [
            payload["gap_obligation_update"]
            for payload in group
            if payload["gap_obligation_update"] is not None
        ]
        files: set[str] = set()
        for unit in units:
            canonical_detail = unit.get("canonical_detail")
            if isinstance(canonical_detail, str):
                files.add(canonical_detail)
            changed_files = unit.get("changed_files")
            if isinstance(changed_files, list):
                files.update(path for path in changed_files if isinstance(path, str))
        validate_discovery_records(
            {
                "run_id": run_id,
                "unit_id": selected_unit_id,
                "files_touched": sorted(files),
                "discovered_work_units": units,
                "gap_obligation_updates": updates,
            }
        )
    return payloads


def verify_discovery_markers(text: str, result: dict[str, Any]) -> None:
    """Require the current Run Log section to encode exactly the result detail."""
    expected = discovery_marker_payloads(result)
    actual = parse_discovery_markers(text)
    if actual != expected:
        raise ContextError(
            "Elim Run Log discovery markers do not exactly match the structured result"
        )


def reconstruct_gap_obligation_state(text: str) -> dict[str, Any]:
    """Reconstruct the complete gap ledger solely from committed Run Log markers."""
    payloads = parse_discovery_markers(text)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for payload in payloads:
        key = (payload["run_id"], payload["selected_unit_id"])
        grouped.setdefault(key, []).append(payload)
    observations = [
        group
        for group in grouped.values()
        if any(
            payload.get("gap_obligation_update") is not None
            or payload["discovered_work_unit"].get("domain")
            == "project-governance-review"
            for payload in group
        )
    ]
    observations.sort(
        key=lambda group: (
            min(
                parse_time(payload["discovered_work_unit"]["observed_at"])
                for payload in group
            ),
            group[0]["run_id"],
            group[0]["selected_unit_id"],
        )
    )
    state: dict[str, Any] | None = None
    for group in observations:
        units = [payload["discovered_work_unit"] for payload in group]
        updates = [
            payload["gap_obligation_update"]
            for payload in group
            if payload["gap_obligation_update"] is not None
        ]
        files = sorted(
            {
                path
                for unit in units
                for path in [unit["canonical_detail"], *unit["changed_files"]]
            }
        )
        state = merge_gap_obligation_state(
            state,
            {
                "run_id": group[0]["run_id"],
                "unit_id": group[0]["selected_unit_id"],
                "files_touched": files,
                "discovered_work_units": units,
                "gap_obligation_updates": updates,
            },
        )
    return state or {
        "schema_version": 1,
        "updated_at": None,
        "governance_review": None,
        "items": [],
    }


def validate_work_unit(value: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise ContextError("work-unit result must be an object")
    required = {
        "schema_version",
        "run_id",
        "unit_id",
        "work_type",
        "outcome",
        "authority",
        "issue_id",
        "canonical_record",
        "files_touched",
        "source_ids",
        "validation",
        "commit",
        "synchronization",
        "human_questions",
        "incident_reports",
        "github_action_requests",
        "continuation",
        "discovered_work_units",
        "gap_obligation_updates",
    }
    missing = sorted(required - set(value))
    if missing:
        raise ContextError(f"work-unit result is missing required fields: {missing}")
    if isinstance(value["schema_version"], bool) or value["schema_version"] != 2:
        raise ContextError("work-unit result schema_version must be 2")
    extras = sorted(set(value) - required)
    if extras:
        raise ContextError(f"work-unit result contains unapproved fields: {extras}")
    for field in ("run_id", "unit_id"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ContextError(f"work-unit {field} must be a nonblank string")
    if value["work_type"] not in {
        "integrity",
        "bot_failure",
        "public_intake",
        "change_audit",
        "issue_audit",
        "issue_development",
        "candidate_research",
        "comprehensive_review",
    }:
        raise ContextError("work-unit type is invalid")
    if value["outcome"] not in {
        "completed",
        "clean",
        "blocked",
        "failed",
        "human_review",
        "usage_stopped",
    }:
        raise ContextError("work-unit outcome is invalid")
    authority = value["authority"]
    if not isinstance(authority, dict) or set(authority) != {
        "classification",
        "basis",
    }:
        raise ContextError(
            "work-unit authority fields do not match the approved schema"
        )
    if authority.get("classification") not in {
        "mechanical",
        "delegated_judgment",
        "human_reserved",
    }:
        raise ContextError("work-unit authority classification is invalid")
    if not isinstance(authority.get("basis"), str) or not authority["basis"].strip():
        raise ContextError("work-unit authority basis is required")
    incident_reports = value["incident_reports"]
    if not isinstance(incident_reports, list) or len(incident_reports) > 16:
        raise ContextError("work-unit incident_reports must be a bounded array")
    try:
        for report in incident_reports:
            validate_incident_report(report)
    except IncidentContractError as error:
        raise ContextError(f"work-unit incident report is invalid: {error}") from error
    continuation = value["continuation"]
    if not isinstance(continuation, dict) or set(continuation) != {
        "state",
        "next_action",
    }:
        raise ContextError(
            "work-unit continuation fields do not match the approved schema"
        )
    if continuation.get("state") not in {"complete", "retryable", "human_required", "none"}:
        raise ContextError("work-unit continuation state is invalid")
    if continuation.get("next_action") is not None and not isinstance(
        continuation["next_action"], str
    ):
        raise ContextError("work-unit continuation next_action must be null or a string")
    if value["outcome"] == "completed" and continuation.get("state") in {"retryable", "human_required"}:
        raise ContextError("completed outcome contradicts an open continuation state")
    if authority.get("classification") == "human_reserved" and value["outcome"] == "completed":
        raise ContextError("a human-reserved work unit may not be reported as autonomously completed")
    issue_id = value.get("issue_id")
    if issue_id is not None and (
        not isinstance(issue_id, str) or not issue_id.strip()
    ):
        raise ContextError("work-unit issue_id must be null or a nonblank string")
    canonical_record = value.get("canonical_record")
    if canonical_record is not None and (
        not isinstance(canonical_record, str) or not canonical_record.strip()
    ):
        raise ContextError(
            "work-unit canonical_record must be null or a nonblank string"
        )
    if not isinstance(value["files_touched"], list) or not all(
        isinstance(path, str) and bool(path)
        for path in value["files_touched"]
    ):
        raise ContextError("work-unit files_touched must be an array of strings")
    if not isinstance(value["source_ids"], list) or not all(
        isinstance(source_id, str)
        and re.fullmatch(r"SRC-[0-9]{4,}", source_id) is not None
        for source_id in value["source_ids"]
    ):
        raise ContextError(
            "work-unit source_ids must contain only canonical SRC identifiers"
        )
    if not isinstance(value["validation"], list):
        raise ContextError("work-unit validation must be an array")
    if value["commit"] is not None and not isinstance(value["commit"], str):
        raise ContextError("work-unit commit must be null or a string")
    for field in ("synchronization", "human_questions"):
        if not isinstance(value[field], list) or not all(
            isinstance(item, str) for item in value[field]
        ):
            raise ContextError(f"work-unit {field} must be an array of strings")
    if value["github_action_requests"] != []:
        raise ContextError(
            "work-unit github_action_requests must be an empty array"
        )
    for path in value["files_touched"]:
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise ContextError(f"work-unit file path is unsafe: {path}")
    if len(value["files_touched"]) != len(set(value["files_touched"])):
        raise ContextError("work-unit file paths must be unique")
    for result in value["validation"]:
        if not isinstance(result, dict) or set(result) != {
            "check",
            "status",
            "detail",
        }:
            raise ContextError(
                "work-unit validation fields do not match the approved schema"
            )
        if (
            result.get("status") not in {"passed", "failed", "skipped"}
            or not isinstance(result.get("check"), str)
            or not result["check"].strip()
            or not isinstance(result.get("detail"), str)
        ):
            raise ContextError("work-unit validation requires check and valid status")
    validate_discovery_records(value)


def compile_closeout(
    value: dict[str, Any],
    *,
    queue_sha256: str,
    context_sha256: str,
    prior_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_work_unit(value)
    for label, digest in (("queue", queue_sha256), ("context", context_sha256)):
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ContextError(f"{label} sha256 must be a lowercase 64-character digest")
    prior_state = prior_state or {}
    attempt = int(prior_state.get("attempt_count") or 0) + 1
    continuation = value["continuation"]
    open_state = continuation["state"] in {"retryable", "human_required"}
    compact = {
        "schema_version": 1,
        "compiled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": value["run_id"],
        "unit_id": value["unit_id"],
        "work_type": value["work_type"],
        "outcome": value["outcome"],
        "authority": value["authority"],
        "issue_id": value.get("issue_id"),
        "canonical_record": value.get("canonical_record"),
        "files_touched": sorted(set(value["files_touched"])),
        "source_ids": sorted(set(value.get("source_ids") or [])),
        "validation": value["validation"],
        "commit": value.get("commit"),
        "synchronization": value.get("synchronization") or [],
        "human_questions": value.get("human_questions") or [],
        "incident_reports": value.get("incident_reports") or [],
        "github_action_requests": [],
        "discovered_work_units": value.get("discovered_work_units") or [],
        "gap_obligation_updates": value.get("gap_obligation_updates") or [],
        "attempt_count": attempt,
        "queue_sha256": queue_sha256,
        "context_sha256": context_sha256,
        "continuation": continuation,
        "requeue": open_state,
    }
    compact["state_sha256"] = sha256_bytes(canonical_json(compact))
    return compact


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and render durable Elim discovery records."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    render = subparsers.add_parser(
        "render-discovery-markers",
        help="render canonical hidden Run Log markers from a result JSON file",
    )
    render.add_argument("--result", type=Path, required=True)
    rebuild = subparsers.add_parser(
        "reconstruct-gap-obligations",
        help="reconstruct the gap ledger from a committed Elim Run Log",
    )
    rebuild.add_argument("--run-log", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "render-discovery-markers":
        value = json.loads(args.result.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ContextError("Elim result JSON must be an object")
        markers = render_discovery_markers(value)
        if markers:
            print(markers)
        return 0
    if args.command == "reconstruct-gap-obligations":
        state = reconstruct_gap_obligation_state(
            args.run_log.read_text(encoding="utf-8")
        )
        print(canonical_json(state).decode("utf-8"))
        return 0
    raise ContextError("unsupported Elim execution helper command")


if __name__ == "__main__":
    raise SystemExit(main())
