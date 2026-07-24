#!/usr/bin/env python3
"""Deterministic Elim arithmetic, validation planning, and closeout compilation."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from arrp_context import ContextError, ROOT, canonical_json, file_provenance, sha256_bytes


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
    if any(path.startswith("research/horizon-review-console/") for path in normalized):
        add(
            "console_tests",
            ["python3", "-m", "unittest", "tests.test_horizon_intake"],
            "Project Console",
        )
    if any(path.startswith((".github/", "framework/agents/")) for path in normalized):
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


def validate_work_unit(value: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "run_id",
        "unit_id",
        "work_type",
        "outcome",
        "authority",
        "files_touched",
        "validation",
        "continuation",
    }
    missing = sorted(required - set(value))
    if missing:
        raise ContextError(f"work-unit result is missing required fields: {missing}")
    if value["schema_version"] != 1:
        raise ContextError("work-unit result schema_version must be 1")
    allowed = required | {
        "issue_id",
        "source_ids",
        "commit",
        "synchronization",
        "human_questions",
    }
    extras = sorted(set(value) - allowed)
    if extras:
        raise ContextError(f"work-unit result contains unapproved fields: {extras}")
    if value["work_type"] not in {
        "integrity",
        "bot_failure",
        "public_intake",
        "change_audit",
        "issue_audit",
        "issue_development",
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
    if authority.get("classification") not in {"mechanical", "delegated_judgment", "human_reserved"}:
        raise ContextError("work-unit authority classification is invalid")
    if not str(authority.get("basis") or "").strip():
        raise ContextError("work-unit authority basis is required")
    continuation = value["continuation"]
    if continuation.get("state") not in {"complete", "retryable", "human_required", "none"}:
        raise ContextError("work-unit continuation state is invalid")
    if value["outcome"] == "completed" and continuation.get("state") in {"retryable", "human_required"}:
        raise ContextError("completed outcome contradicts an open continuation state")
    if authority.get("classification") == "human_reserved" and value["outcome"] == "completed":
        raise ContextError("a human-reserved work unit may not be reported as autonomously completed")
    for path in value["files_touched"]:
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise ContextError(f"work-unit file path is unsafe: {path}")
    if len(value["files_touched"]) != len(set(value["files_touched"])):
        raise ContextError("work-unit file paths must be unique")
    for result in value["validation"]:
        if result.get("status") not in {"passed", "failed", "skipped"} or not str(
            result.get("check") or ""
        ).strip():
            raise ContextError("work-unit validation requires check and valid status")


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
        "files_touched": sorted(set(value["files_touched"])),
        "source_ids": sorted(set(value.get("source_ids") or [])),
        "validation": value["validation"],
        "commit": value.get("commit"),
        "synchronization": value.get("synchronization") or [],
        "human_questions": value.get("human_questions") or [],
        "attempt_count": attempt,
        "queue_sha256": queue_sha256,
        "context_sha256": context_sha256,
        "continuation": continuation,
        "requeue": open_state,
    }
    compact["state_sha256"] = sha256_bytes(canonical_json(compact))
    return compact
