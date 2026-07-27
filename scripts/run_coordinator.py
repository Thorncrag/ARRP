#!/usr/bin/env python3
"""Plan, update, and finalize the deterministic ARRP run chain.

The coordinator never performs LLM work.  It creates the durable decision record
that a separate, explicitly activated host dispatcher may use to decide whether
Elim should be invoked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from console_data_contracts import status_projection_contract
except ModuleNotFoundError:  # Imported as scripts.run_coordinator.
    from scripts.console_data_contracts import status_projection_contract


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / ".github" / "run-coordinator-bot.json"
TERMINAL_SUCCESS = {"succeeded", "not_due", "skipped"}
STAGE_STATUSES = {
    "pending",
    "running",
    "succeeded",
    "failed",
    "degraded",
    "not_due",
    "skipped",
}
FAILURE_CLASSES = {"none", "transient", "blocking", "degraded", "configuration"}
CONTEXT_PROFILE_BY_WORK_KIND = {
    "bot_failure": "integrity_reconciliation",
    "integrity": "integrity_reconciliation",
    "public_intake": "public_intake",
    "change_audit": "change_audit",
    "issue_audit": "issue_audit",
    "issue_development": "issue_development",
    "candidate_research": "candidate_research",
    "comprehensive_review": "comprehensive_review",
}
MODEL_PROFILE_BY_CONTEXT_PROFILE = {
    "integrity_reconciliation": "substantive",
    "public_intake": "read-heavy-triage",
    "change_audit": "substantive",
    "issue_audit": "substantive",
    "issue_development": "substantive",
    "candidate_research": "substantive",
    "comprehensive_review": "comprehensive",
}
ISSUE_DOSSIER_WORK_KINDS = {
    "change_audit",
    "issue_audit",
    "issue_development",
}
WATCHER_STAGE_ARTIFACTS = {
    "case-monitor-bot": {
        "directory": "case-monitor",
        "report": "monitoring-report.json",
        "event": "case-monitor-domain-event.json",
        "attestation": "watcher-attempt.json",
        "destination": "case-monitor.json",
    },
    "presidential-directives-bot": {
        "directory": "presidential-directives",
        "report": "directives-report.json",
        "event": "presidential-directives-domain-event.json",
        "attestation": "watcher-attempt.json",
        "destination": "presidential-directives.json",
    },
    "source-checker-bot": {
        "directory": "source-checker",
        "report": "arrp-source-checker/source-checker.json",
        "event": "source-checker-domain-event.json",
        "attestation": "watcher-attempt.json",
        "destination": "source-checker.json",
    },
}
PERSISTENT_WATCHER_INPUTS = {
    "case-monitor-bot": {
        "filename": "case-monitor.json",
        "schema_version": 6,
        "timestamp_field": "checked_at",
        "required_types": {
            "changes": list,
            "source_development_modules": list,
        },
    },
    "presidential-directives-bot": {
        "filename": "presidential-directives.json",
        "schema_version": 2,
        "timestamp_field": "generated_at",
        "required_types": {
            "counts": dict,
            "changes": list,
            "directives": list,
        },
    },
    "source-checker-bot": {
        "filename": "source-checker.json",
        "schema_version": 2,
        "timestamp_field": "checked_at",
        "required_types": {
            "counts": dict,
            "results": list,
        },
    },
}
MAX_PERSISTENT_WATCHER_INPUT_BYTES = 20_000_000
MAX_PERSISTENT_WATCHER_FUTURE_SKEW_SECONDS = 600
GOVERNANCE_DISCOVERY_FIELDS = {
    "mode",
    "ordinary_selection_policy",
    "minimum_interval_hours",
    "selected_as_quiet_queue_fallback",
    "ordinary_eligible_count_before_fallback",
    "last_review",
    "next_due_at",
    "current_for_cadence",
    "waiting_for_ordinary_queue",
    "reason",
}
GOVERNANCE_REVIEW_FIELDS = {
    "last_reviewed_at",
    "run_id",
    "selected_unit_id",
    "discovered_work_unit_id",
    "source_revision",
    "disposition",
    "canonical_detail",
    "next_trigger",
}
GAP_OBLIGATION_STATUSES = {
    "open",
    "investigating",
    "blocked",
    "human_required",
    "resolved",
    "human_disposition",
}
GAP_AUTHORITY_CLASSIFICATIONS = {
    "mechanical",
    "delegated_judgment",
    "human_reserved",
}
GAP_AUTHORITY_DISPOSITIONS = {
    "permitted",
    "human_reserved",
    "forbidden",
    "unsafe",
    "out_of_scope",
    "uncertain",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path | None, default: Any = None) -> Any:
    if path is None or not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def run_git(repo: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    # Preserve leading spaces because porcelain status uses them as part of
    # its two-column state prefix. Only remove line terminators.
    return result.stdout.rstrip("\r\n") if result.returncode == 0 else None


def repository_state(repo: Path) -> dict[str, Any]:
    head = run_git(repo, "rev-parse", "HEAD")
    branch = run_git(repo, "branch", "--show-current") or "detached"
    status = run_git(repo, "status", "--porcelain")
    dirty = [] if status is None else [line[3:] for line in status.splitlines() if line]
    origin = run_git(repo, "rev-parse", "refs/remotes/origin/main")
    ahead = behind = None
    if head and origin:
        counts = run_git(repo, "rev-list", "--left-right", "--count", f"{origin}...{head}")
        if counts:
            behind, ahead = (int(value) for value in counts.split())
    clean = not dirty
    return {
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "clean": clean,
        "dirty_paths": dirty[:100],
        "dirty_path_count": len(dirty),
        "ahead_of_origin_main": ahead,
        "behind_origin_main": behind,
        "fresh": bool(head and origin and behind == 0),
    }


def file_hash(path: Path) -> str | None:
    if not path.is_file():
        return None
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def materialize_selected_watcher_artifacts(
    manifest: dict[str, Any],
    artifacts_root: Path,
    destination_root: Path,
) -> list[str]:
    """Verify and copy only the successful, chain-bound watcher attempts."""

    chain_id = str(manifest.get("chain_id") or "")
    if not chain_id:
        raise ValueError("run-chain manifest lacks its chain identity")
    stages = {
        str(stage.get("id") or ""): stage
        for stage in manifest.get("stages") or []
        if isinstance(stage, dict)
    }
    copied: list[str] = []
    destination_root.mkdir(parents=True, exist_ok=True)
    for stage_id, spec in WATCHER_STAGE_ARTIFACTS.items():
        stage = stages.get(stage_id)
        if not stage or stage.get("due") is not True:
            continue
        if stage.get("status") != "succeeded":
            continue
        attempt_key = str(stage.get("attempt_key") or "")
        if attempt_key not in {"primary", "retry"}:
            raise ValueError(
                f"successful stage {stage_id} lacks its exact attempt identity"
            )
        expected_run_id = str(stage.get("run_id") or "")
        if not expected_run_id or not expected_run_id.endswith(
            ":" + attempt_key
        ):
            raise ValueError(
                f"successful stage {stage_id} has an invalid run-attempt identity"
            )
        report = artifacts_root / str(spec["directory"]) / str(spec["report"])
        if not report.is_file() or report.is_symlink():
            raise ValueError(
                f"successful stage {stage_id} lacks its selected {attempt_key} artifact"
            )
        expected_report_hash = str(
            ((stage.get("output") or {}).get("sha256") or "")
        )
        actual_report_hash = file_hash(report) or ""
        if (
            not expected_report_hash.startswith("sha256:")
            or len(expected_report_hash) != 71
            or not secrets.compare_digest(
                actual_report_hash,
                expected_report_hash,
            )
        ):
            raise ValueError(
                f"successful stage {stage_id} report hash differs from its "
                f"selected {attempt_key} output"
            )

        event_metadata = stage.get("domain_event")
        attestation_path = (
            artifacts_root
            / str(spec["directory"])
            / str(spec["attestation"])
        )
        if not attestation_path.is_file() or attestation_path.is_symlink():
            raise ValueError(
                f"successful stage {stage_id} lacks its selected attempt attestation"
            )
        try:
            attestation = json.loads(
                attestation_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"successful stage {stage_id} attempt attestation is invalid JSON"
            ) from exc
        expected_attestation_fields = {
            "schema_version",
            "stage_id",
            "chain_id",
            "run_id",
            "attempt_key",
            "report_sha256",
            "domain_event",
        }
        if (
            not isinstance(attestation, dict)
            or set(attestation) != expected_attestation_fields
            or attestation.get("schema_version") != 1
            or attestation.get("stage_id") != stage_id
            or attestation.get("chain_id") != chain_id
            or attestation.get("run_id") != expected_run_id
            or attestation.get("attempt_key") != attempt_key
            or attestation.get("report_sha256") != expected_report_hash
            or attestation.get("domain_event") != event_metadata
        ):
            raise ValueError(
                f"successful stage {stage_id} attempt attestation is not bound "
                "to the selected chain, run attempt, report, and event"
            )
        event_path = (
            artifacts_root / str(spec["directory"]) / str(spec["event"])
        )
        if event_metadata is None:
            if event_path.exists():
                raise ValueError(
                    f"successful stage {stage_id} supplied an unbound event artifact"
                )
        else:
            if not isinstance(event_metadata, dict) or set(event_metadata) != {
                "id",
                "sha256",
                "json",
            }:
                raise ValueError(
                    f"successful stage {stage_id} has incomplete event identity"
                )
            if not event_path.is_file() or event_path.is_symlink():
                raise ValueError(
                    f"successful stage {stage_id} lacks its selected event artifact"
                )
            expected_event_hash = str(event_metadata["sha256"])
            actual_event_hash = file_hash(event_path) or ""
            if (
                not expected_event_hash.startswith("sha256:")
                or len(expected_event_hash) != 71
                or not secrets.compare_digest(
                    actual_event_hash,
                    expected_event_hash,
                )
            ):
                raise ValueError(
                    f"successful stage {stage_id} event hash differs from its "
                    f"selected {attempt_key} output"
                )
            embedded_event = event_metadata["json"]
            if not isinstance(embedded_event, dict):
                raise ValueError(
                    f"successful stage {stage_id} embedded event is not an object"
                )
            try:
                artifact_event = json.loads(event_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"successful stage {stage_id} event artifact is invalid JSON"
                ) from exc
            if artifact_event != embedded_event:
                raise ValueError(
                    f"successful stage {stage_id} embedded event differs from "
                    "the selected artifact"
                )
            proposal = artifact_event.get("proposal")
            proposal_revision = (
                proposal.get("proposal_revision")
                if isinstance(proposal, dict)
                else None
            )
            if (
                artifact_event.get("event_id") != event_metadata["id"]
                or artifact_event.get("chain_id") != chain_id
                or artifact_event.get("run_id") != expected_run_id
                or not isinstance(proposal_revision, str)
                or len(proposal_revision) != 40
                or any(
                    character not in "0123456789abcdef"
                    for character in proposal_revision
                )
            ):
                raise ValueError(
                    f"successful stage {stage_id} event identity is not bound "
                    "to the selected chain, run attempt, and proposal revision"
                )

        destination = destination_root / str(spec["destination"])
        shutil.copy2(report, destination)
        copied.append(destination.name)
    return copied


def json_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def model_profile_for_context(
    config: dict[str, Any],
    context_profile: str,
) -> tuple[str, dict[str, Any]]:
    profile_id = MODEL_PROFILE_BY_CONTEXT_PROFILE.get(context_profile)
    profiles = (config.get("llmRouting") or {}).get("profiles") or {}
    profile = profiles.get(profile_id) if profile_id else None
    if not isinstance(profile, dict):
        raise ValueError(
            f"no reviewed model profile is bound to context profile {context_profile!r}"
        )
    return profile_id, profile


def _nonblank_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_timestamp(value: Any) -> bool:
    if not _nonblank_string(value):
        return False
    try:
        return parse_time(value) is not None
    except (TypeError, ValueError):
        return False


def _exact_source_revision(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if value.startswith("sha256:"):
        revision = value[7:]
        expected_lengths = {64}
    else:
        revision = value
        expected_lengths = {40, 64}
    return (
        len(revision) in expected_lengths
        and all(character in "0123456789abcdef" for character in revision)
    )


def _safe_repository_relative_path(value: Any) -> bool:
    if not _nonblank_string(value):
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def governance_discovery_projection(
    queue: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate and retain the typed quiet-queue governance posture."""

    value = queue.get("governance_discovery")
    if not isinstance(value, dict) or set(value) != GOVERNANCE_DISCOVERY_FIELDS:
        raise ValueError(
            "Elim work queue governance_discovery fields do not match the "
            "approved projection"
        )
    policy = config["governanceDiscovery"]
    if (
        value.get("mode") != policy["mode"]
        or value.get("ordinary_selection_policy")
        != policy["ordinarySelectionPolicy"]
        or value.get("minimum_interval_hours")
        != policy["minimumIntervalHours"]
    ):
        raise ValueError(
            "Elim work queue governance_discovery differs from coordinator policy"
        )
    for field in (
        "selected_as_quiet_queue_fallback",
        "current_for_cadence",
        "waiting_for_ordinary_queue",
    ):
        if not isinstance(value.get(field), bool):
            raise ValueError(
                f"Elim work queue governance_discovery {field} must be boolean"
            )
    ordinary_count = value.get("ordinary_eligible_count_before_fallback")
    if (
        isinstance(ordinary_count, bool)
        or not isinstance(ordinary_count, int)
        or ordinary_count < 0
    ):
        raise ValueError(
            "Elim work queue governance_discovery ordinary count is invalid"
        )
    if not _nonblank_string(value.get("reason")):
        raise ValueError(
            "Elim work queue governance_discovery requires a reason"
        )
    next_due_at = value.get("next_due_at")
    if next_due_at is not None and not _valid_timestamp(next_due_at):
        raise ValueError(
            "Elim work queue governance_discovery next_due_at is invalid"
        )
    last_review = value.get("last_review")
    if last_review is not None:
        if (
            not isinstance(last_review, dict)
            or set(last_review) != GOVERNANCE_REVIEW_FIELDS
            or not _valid_timestamp(last_review.get("last_reviewed_at"))
            or not all(
                _nonblank_string(last_review.get(field))
                for field in (
                    "run_id",
                    "selected_unit_id",
                    "discovered_work_unit_id",
                    "next_trigger",
                )
            )
            or not _exact_source_revision(last_review.get("source_revision"))
            or last_review.get("disposition")
            not in {"no_material_finding", "review_completed"}
            or not _safe_repository_relative_path(
                last_review.get("canonical_detail")
            )
        ):
            raise ValueError(
                "Elim work queue governance_discovery last_review is invalid"
            )
        if next_due_at is None:
            raise ValueError(
                "Elim work queue governance_discovery reviewed state lacks next_due_at"
            )
    elif next_due_at is not None:
        raise ValueError(
            "Elim work queue governance_discovery has next_due_at without a review"
        )
    selected_fallback = value["selected_as_quiet_queue_fallback"]
    current = value["current_for_cadence"]
    waiting = value["waiting_for_ordinary_queue"]
    if selected_fallback and (current or waiting or ordinary_count != 0):
        raise ValueError(
            "Elim work queue governance discovery has contradictory fallback state"
        )
    if current and (waiting or ordinary_count != 0 or last_review is None):
        raise ValueError(
            "Elim work queue governance discovery has contradictory cadence state"
        )
    if waiting != (ordinary_count > 0):
        raise ValueError(
            "Elim work queue governance discovery ordinary-work posture is inconsistent"
        )
    governance_items = [
        item
        for item in queue.get("items") or []
        if isinstance(item, dict)
        and item.get("work_class") == "governance_discovery"
    ]
    if len(governance_items) != int(selected_fallback):
        raise ValueError(
            "Elim work queue governance discovery item count is inconsistent"
        )
    return {
        "mode": value["mode"],
        "ordinary_selection_policy": value["ordinary_selection_policy"],
        "minimum_interval_hours": value["minimum_interval_hours"],
        "selected_as_quiet_queue_fallback": value[
            "selected_as_quiet_queue_fallback"
        ],
        "ordinary_eligible_count_before_fallback": value[
            "ordinary_eligible_count_before_fallback"
        ],
        "last_review": (
            dict(value["last_review"])
            if isinstance(value["last_review"], dict)
            else None
        ),
        "next_due_at": value["next_due_at"],
        "current_for_cadence": value["current_for_cadence"],
        "waiting_for_ordinary_queue": value["waiting_for_ordinary_queue"],
        "reason": value["reason"],
    }


def gap_obligation_projections(
    queue: dict[str, Any],
    *,
    maximum: int,
) -> list[dict[str, Any]]:
    """Project bounded queue metadata without duplicating gap narratives."""

    items = queue.get("items")
    if not isinstance(items, list):
        raise ValueError("Elim work queue items must be an array")
    gap_items = [
        item
        for item in items
        if isinstance(item, dict) and item.get("work_class") == "gap_stewardship"
    ]
    if len(gap_items) > maximum:
        raise ValueError(
            "Elim work queue gap obligations exceed the configured projection bound"
        )
    required_projection_fields = {
        "severity",
        "owner",
        "authority",
        "authority_disposition",
        "disposition",
        "first_seen",
        "last_checked",
        "occurrence_count",
        "age_days",
        "canonical_detail",
        "exact_next_action",
        "next_trigger",
        "source_revision",
    }
    projected: list[dict[str, Any]] = []
    identities: set[str] = set()
    for item in gap_items:
        source = item.get("source")
        projection = (
            source.get("obligation_projection")
            if isinstance(source, dict)
            else None
        )
        if (
            not isinstance(source, dict)
            or source.get("input") != "gap_obligations"
            or source.get("finding_type") != "gap_obligation"
            or not isinstance(projection, dict)
            or set(projection) != required_projection_fields
        ):
            raise ValueError(
                "Elim work queue gap obligation lacks its compact canonical projection"
            )
        obligation_id = source.get("obligation_id")
        queue_item_id = item.get("id")
        if (
            not _nonblank_string(obligation_id)
            or obligation_id in identities
            or item.get("gap_obligation_id") != obligation_id
            or not _nonblank_string(queue_item_id)
            or not _nonblank_string(item.get("title"))
        ):
            raise ValueError(
                "Elim work queue gap obligation has invalid or duplicate identity"
            )
        identities.add(obligation_id)
        status = source.get("obligation_status")
        if status not in GAP_OBLIGATION_STATUSES - {
            "resolved",
            "human_disposition",
        }:
            raise ValueError("Elim work queue gap obligation status is invalid")
        authority = projection.get("authority")
        if (
            not isinstance(authority, dict)
            or set(authority) != {"classification", "basis"}
            or authority.get("classification")
            not in GAP_AUTHORITY_CLASSIFICATIONS
            or not _nonblank_string(authority.get("basis"))
            or projection.get("authority_disposition")
            not in GAP_AUTHORITY_DISPOSITIONS
            or projection.get("disposition")
            not in {"fixed", "reported", "retained"}
        ):
            raise ValueError("Elim work queue gap obligation authority is invalid")
        for field in (
            "severity",
            "owner",
            "canonical_detail",
            "exact_next_action",
            "next_trigger",
        ):
            if not _nonblank_string(projection.get(field)):
                raise ValueError(
                    f"Elim work queue gap obligation requires {field}"
                )
        if (
            not _safe_repository_relative_path(projection["canonical_detail"])
            or not _valid_timestamp(projection.get("first_seen"))
            or not _valid_timestamp(projection.get("last_checked"))
            or not _exact_source_revision(projection.get("source_revision"))
        ):
            raise ValueError(
                "Elim work queue gap obligation canonical metadata is invalid"
            )
        for field in ("occurrence_count", "age_days"):
            number = projection.get(field)
            minimum = 1 if field == "occurrence_count" else 0
            if (
                isinstance(number, bool)
                or not isinstance(number, int)
                or number < minimum
            ):
                raise ValueError(
                    f"Elim work queue gap obligation {field} is invalid"
                )
        if (
            not isinstance(item.get("eligible_for_elim"), bool)
            or not isinstance(item.get("requires_human"), bool)
            or not _nonblank_string(item.get("eligibility_reason"))
            or (
                item.get("blocking_reason") is not None
                and not _nonblank_string(item.get("blocking_reason"))
            )
            or item.get("exact_next_action") != projection["exact_next_action"]
        ):
            raise ValueError(
                "Elim work queue gap obligation eligibility metadata is invalid"
            )
        if (
            projection["authority_disposition"]
            in {"forbidden", "unsafe", "out_of_scope"}
            and item["eligible_for_elim"]
        ):
            raise ValueError(
                "Elim work queue prohibited gap obligation is incorrectly eligible"
            )
        human_reserved = (
            authority["classification"] == "human_reserved"
            or projection["authority_disposition"] == "human_reserved"
            or status == "human_required"
        )
        if human_reserved and (
            not item["requires_human"] or item["eligible_for_elim"]
        ):
            raise ValueError(
                "Elim work queue human-reserved gap obligation has invalid eligibility"
            )
        if status == "blocked" and item["eligible_for_elim"]:
            raise ValueError(
                "Elim work queue blocked gap obligation is incorrectly eligible"
            )
        projected.append(
            {
                "queue_item_id": queue_item_id,
                "obligation_id": obligation_id,
                "title": item["title"],
                "status": status,
                "severity": projection["severity"],
                "owner": projection["owner"],
                "authority": dict(authority),
                "authority_disposition": projection["authority_disposition"],
                "disposition": projection["disposition"],
                "eligible_for_elim": item["eligible_for_elim"],
                "requires_human": item["requires_human"],
                "eligibility_reason": item["eligibility_reason"],
                "blocking_reason": item.get("blocking_reason"),
                "first_seen": projection["first_seen"],
                "last_checked": projection["last_checked"],
                "occurrence_count": projection["occurrence_count"],
                "age_days": projection["age_days"],
                "canonical_detail": projection["canonical_detail"],
                "exact_next_action": projection["exact_next_action"],
                "next_trigger": projection["next_trigger"],
                "source_revision": projection["source_revision"],
            }
        )
    return projected


def selected_work_item(
    queue: dict[str, Any],
    *,
    comprehensive_required: bool,
) -> dict[str, Any] | None:
    items = queue.get("items")
    if not isinstance(items, list):
        raise ValueError("Elim work queue items must be an array")
    eligible = [
        item
        for item in items
        if isinstance(item, dict) and item.get("eligible_for_elim") is True
    ]
    repair_item = next(
        (
            candidate
            for candidate in eligible
            if candidate.get("kind") == "bot_failure"
            and candidate.get("safety_class") == 0
        ),
        None,
    )
    if repair_item is not None:
        return repair_item
    if comprehensive_required:
        item = next(
            (
                candidate
                for candidate in eligible
                if candidate.get("kind") == "comprehensive_review"
            ),
            None,
        )
        if item is None:
            raise ValueError(
                "the chain requires comprehensive context but the queue has no "
                "eligible comprehensive-review work item"
            )
        return item
    selected_id = str(queue.get("selected_work_item_id") or "").strip()
    if selected_id:
        item = next(
            (
                candidate
                for candidate in eligible
                if candidate.get("id") == selected_id
            ),
            None,
        )
        if item is None:
            raise ValueError(
                "the queue's exact selected work-item ID is not eligible"
            )
        return item
    return eligible[0] if eligible else None


def selected_repair_unit(gateway: Any) -> dict[str, Any] | None:
    if not isinstance(gateway, dict):
        return None
    selected = gateway.get("next_item")
    if (
        isinstance(selected, dict)
        and selected.get("kind") == "bot_failure"
        and selected.get("safety_class") == 0
        and selected.get("eligible_for_elim") is True
    ):
        return selected
    return None


def review_epoch_boundary_changes(signals: dict[str, Any]) -> dict[str, list[str]] | None:
    value = signals.get("comprehensive_review_boundary_changes")
    if value is None:
        return None
    fields = {"missing", "extra", "mismatched"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(
            "Review Epoch boundary changes must contain exactly missing, extra, "
            "and mismatched"
        )
    normalized: dict[str, list[str]] = {}
    for field in sorted(fields):
        entries = value[field]
        if (
            not isinstance(entries, list)
            or any(not isinstance(entry, str) or not entry.strip() for entry in entries)
            or len(entries) != len(set(entries))
        ):
            raise ValueError(
                f"Review Epoch boundary changes {field} must be a unique string array"
            )
        normalized[field] = list(entries)
    return normalized


def review_epoch_boundary_status(
    latest_epoch: dict[str, Any] | None,
    context_registry: dict[str, Any],
    context_registry_sha256: str,
    *,
    context_registry_path: str = "framework/context-routes.json",
) -> dict[str, Any]:
    """Compare one recorded Review Epoch with the current registry boundary."""
    if context_registry.get("schema_version") != 2:
        raise ValueError("Review Epoch boundary comparison requires a schema-2 registry")
    if (
        len(context_registry_sha256) != 64
        or any(
            character not in "0123456789abcdef"
            for character in context_registry_sha256
        )
    ):
        raise ValueError("context registry hash must be an unprefixed SHA-256 digest")
    documents = context_registry.get("documents")
    if not isinstance(documents, dict) or not documents:
        raise ValueError("context registry has no documents")
    current: dict[str, str] = {}
    for document_id, spec in documents.items():
        if not isinstance(spec, dict):
            raise ValueError(f"context registry document {document_id} is not an object")
        if spec.get("governing") is not True:
            continue
        if spec.get("hash_policy") != "pinned":
            raise ValueError(
                f"governing context registry document {document_id} is not pinned"
            )
        path = spec.get("path")
        digest = spec.get("sha256")
        if not isinstance(path, str) or not path:
            raise ValueError(
                f"governing context registry document {document_id} has no path"
            )
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError(
                f"governing context registry document {document_id} has no valid hash"
            )
        if path in current:
            raise ValueError(f"context registry repeats governing path {path}")
        current[path] = "sha256:" + digest
    if context_registry_path in current:
        raise ValueError(
            "context registry manifest must not self-register as a governing document"
        )
    current[context_registry_path] = "sha256:" + context_registry_sha256

    recorded = (
        (latest_epoch or {}).get("governing_hashes")
        if isinstance(latest_epoch, dict)
        else None
    )
    recorded = recorded if isinstance(recorded, dict) else {}
    missing = sorted(set(current) - set(recorded))
    extra = sorted(set(recorded) - set(current))
    mismatched = sorted(
        path
        for path in set(current) & set(recorded)
        if recorded[path] != current[path]
    )
    required = bool(missing or extra or mismatched)
    return {
        "off_cycle_required": required,
        "reason": "governing_boundary_changed" if required else "boundary_current",
        "missing": missing,
        "extra": extra,
        "mismatched": mismatched,
        "current_governing_hashes": current,
    }


def previous_stage(previous: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for stage in previous.get("stages", []):
        if stage.get("id") == stage_id:
            return stage
    return {}


def last_success_at(previous: dict[str, Any], stage_id: str) -> str | None:
    stage = previous_stage(previous, stage_id)
    if stage.get("status") == "succeeded":
        return stage.get("completed_at") or previous.get("updated_at")
    return stage.get("last_success_at")


def watcher_input_refresh_requirements(
    input_root: Path,
    stage_definitions: list[dict[str, Any]],
    now: datetime | None = None,
) -> dict[str, str]:
    """Return watcher stages whose durable current input cannot be trusted."""
    requirements: dict[str, str] = {}
    definitions = {
        str(definition.get("id") or ""): definition
        for definition in stage_definitions
        if isinstance(definition, dict)
    }
    checked_at = (now or utc_now()).astimezone(timezone.utc)
    for stage_id, spec in PERSISTENT_WATCHER_INPUTS.items():
        definition = definitions.get(stage_id)
        if not definition:
            raise ValueError(f"persistent watcher stage is not configured: {stage_id}")
        due = definition.get("due") or {}
        if due.get("kind") != "interval":
            raise ValueError(
                f"persistent watcher stage must use an interval due rule: {stage_id}"
            )
        interval_hours = due.get("hours")
        if (
            not isinstance(interval_hours, int)
            or isinstance(interval_hours, bool)
            or interval_hours <= 0
        ):
            raise ValueError(
                f"persistent watcher stage has an invalid interval: {stage_id}"
            )

        path = input_root / str(spec["filename"])
        if not path.is_file() or path.is_symlink():
            requirements[stage_id] = "persistent watcher input is missing"
            continue
        try:
            if path.stat().st_size > MAX_PERSISTENT_WATCHER_INPUT_BYTES:
                requirements[stage_id] = "persistent watcher input is oversized"
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            requirements[stage_id] = "persistent watcher input is malformed"
            continue
        if not isinstance(payload, dict):
            requirements[stage_id] = "persistent watcher input is not an object"
            continue
        if (
            str(payload.get("collection_status") or "").strip().casefold()
            == "unavailable"
        ):
            requirements[stage_id] = "persistent watcher input is unavailable"
            continue
        schema_version = payload.get("schema_version")
        if type(schema_version) is not int or schema_version != spec[
            "schema_version"
        ] or any(
            not isinstance(payload.get(field), expected_type)
            for field, expected_type in spec["required_types"].items()
        ):
            requirements[stage_id] = "persistent watcher input schema is invalid"
            continue
        timestamp = payload.get(spec["timestamp_field"])
        if not isinstance(timestamp, str) or not timestamp.strip():
            requirements[stage_id] = "persistent watcher input is undated"
            continue
        try:
            reported_at = parse_time(timestamp)
        except (TypeError, ValueError):
            reported_at = None
        if reported_at is None:
            requirements[stage_id] = "persistent watcher input timestamp is malformed"
            continue
        reported_at = reported_at.astimezone(timezone.utc)
        if (
            reported_at - checked_at
        ).total_seconds() > MAX_PERSISTENT_WATCHER_FUTURE_SKEW_SECONDS:
            requirements[stage_id] = "persistent watcher input is future-dated"
            continue
        if checked_at - reported_at > timedelta(hours=interval_hours):
            requirements[stage_id] = "persistent watcher input is stale"
    return requirements


def stage_due(
    definition: dict[str, Any],
    previous: dict[str, Any],
    signals: dict[str, Any],
    now: datetime,
) -> tuple[bool, str]:
    due = definition["due"]
    kind = due["kind"]
    if definition["id"] in set(signals.get("force_stages", [])):
        reasons = signals.get("force_stage_reasons") or {}
        reason = reasons.get(definition["id"]) if isinstance(reasons, dict) else None
        return True, str(reason).strip() if str(reason or "").strip() else "forced"
    if kind == "always":
        return True, "required every chain"
    if kind == "flag":
        active = bool(signals.get(due["signal"], False))
        return active, f"{due['signal']} {'set' if active else 'not set'}"
    if kind == "interval":
        prior = parse_time(last_success_at(previous, definition["id"]))
        if prior is None:
            return True, "no recorded successful run"
        deadline = prior + timedelta(hours=int(due["hours"]))
        return now >= deadline, (
            f"interval elapsed at {iso(deadline)}"
            if now >= deadline
            else f"last success remains current until {iso(deadline)}"
        )
    raise ValueError(f"unsupported due kind: {kind}")


def workflow_health(config: dict[str, Any], repo: Path) -> dict[str, Any]:
    checks = []
    for stage in config["stages"]:
        workflow = stage.get("workflow")
        if workflow:
            path = repo / workflow
            checks.append(
                {
                    "stage": stage["id"],
                    "workflow": workflow,
                    "exists": path.is_file(),
                    "sha256": file_hash(path),
                }
            )
    missing = [check["workflow"] for check in checks if not check["exists"]]
    return {"healthy": not missing, "missing": missing, "checks": checks}


def acquire_lock(path: Path | None, chain_id: str, resume: bool) -> dict[str, Any]:
    if path is None:
        return {
            "key": "arrp-run-chain",
            "path": None,
            "status": "github-concurrency",
            "owner_chain_id": chain_id,
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        owner = read_json(path, {})
        if not (resume and owner.get("chain_id") == chain_id):
            raise RuntimeError(
                f"run-chain lock is held by {owner.get('chain_id', 'unknown')}"
            )
    atomic_write(path, {"chain_id": chain_id, "acquired_at": iso(utc_now())})
    return {
        "key": "arrp-run-chain",
        "path": str(path),
        "status": "acquired",
        "owner_chain_id": chain_id,
    }


def release_lock(lock: dict[str, Any]) -> None:
    raw = lock.get("path")
    if raw:
        path = Path(raw)
        if path.is_file():
            owner = read_json(path, {})
            if owner.get("chain_id") == lock.get("owner_chain_id"):
                path.unlink()
        lock["status"] = "released"
    elif lock.get("status") == "github-concurrency":
        lock["status"] = "released-by-workflow"


def review_epoch(
    config: dict[str, Any],
    previous: dict[str, Any],
    signals: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    interval = int(config["reviewEpoch"]["intervalDays"])
    prior = previous.get("review_epoch", {})
    completed = signals.get("comprehensive_review_completed_at") or prior.get(
        "last_completed_at"
    )
    last = parse_time(completed)
    forced = bool(signals.get("force_comprehensive_review", False))
    forced_reason = signals.get("comprehensive_review_trigger_reason")
    if not isinstance(forced_reason, str) or not forced_reason.strip():
        forced_reason = "forced"
    else:
        forced_reason = forced_reason.strip()
    recorded_due = parse_time(signals.get("comprehensive_review_next_due_at"))
    due_at = recorded_due or (last + timedelta(days=interval) if last else now)
    due = forced or last is None or now >= due_at
    boundary = (
        signals.get("comprehensive_review_boundary_commit")
        or prior.get("boundary_commit")
        or previous.get("baseline_commit")
    )
    unresolved = signals.get(
        "comprehensive_review_unresolved_findings",
        signals.get("unresolved_findings", prior.get("unresolved_findings", [])),
    )
    if not isinstance(unresolved, list):
        raise ValueError("Review Epoch unresolved findings signal must be an array")
    boundary_changes = review_epoch_boundary_changes(signals)
    return {
        "interval_days": interval,
        "last_completed_at": iso(last) if last else None,
        "next_due_at": iso(due_at),
        "due": due,
        "due_reason": (
            forced_reason
            if forced
            else "no completed review epoch"
            if last is None
            else "interval elapsed"
            if due
            else "interval current"
        ),
        "boundary_commit": boundary,
        "epoch_id": signals.get("comprehensive_review_epoch_id") or prior.get("epoch_id"),
        "stability_status": (
            signals.get("comprehensive_review_stability_status")
            or prior.get("stability_status")
        ),
        "unresolved_findings": unresolved,
        "boundary_changes": boundary_changes,
    }


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schemaVersion") != 1:
        raise ValueError("unsupported run-coordinator config schemaVersion")
    if config.get("agentId") != "run-coordinator-bot":
        raise ValueError("run coordinator must use run-coordinator-bot")
    ids = [stage["id"] for stage in config.get("stages", [])]
    if len(ids) != len(set(ids)):
        raise ValueError("run-coordinator stage IDs must be unique")
    if ids[-1:] != ["project-integrity-bot"]:
        raise ValueError("project-integrity-bot must be the last deterministic stage")
    launch_policy = config.get("llmLaunchPolicy") or {}
    authorized = launch_policy.get("authorizedTriggers")
    deterministic_only = launch_policy.get("deterministicOnlyTriggers")
    if not isinstance(authorized, list) or not all(
        isinstance(item, str) and item for item in authorized
    ):
        raise ValueError("llmLaunchPolicy authorizedTriggers must be a string list")
    if not isinstance(deterministic_only, list) or not all(
        isinstance(item, str) and item for item in deterministic_only
    ):
        raise ValueError(
            "llmLaunchPolicy deterministicOnlyTriggers must be a string list"
        )
    if set(authorized) & set(deterministic_only):
        raise ValueError("LLM-authorized and deterministic-only triggers must be disjoint")
    if "push" not in deterministic_only:
        raise ValueError("main-branch pushes must remain deterministic-only")
    usage = config.get("usage") or {}
    interval = usage.get("monitorIntervalSeconds")
    max_age = usage.get("snapshotMaxAgeSeconds")
    if not isinstance(interval, int) or not 10 <= interval <= 300:
        raise ValueError("usage monitor interval must be 10 through 300 seconds")
    if not isinstance(max_age, int) or not interval <= max_age <= 600:
        raise ValueError(
            "usage snapshot maximum age must be at least the monitor interval "
            "and no more than 600 seconds"
        )
    if config.get("governanceDiscovery") != {
        "enabled": True,
        "mode": "Project governance review and discovery",
        "ordinarySelectionPolicy": "after-ordinary-queue-clears",
        "minimumIntervalHours": 168,
    }:
        raise ValueError(
            "governanceDiscovery must preserve the reviewed quiet-queue fallback"
        )
    if config.get("gapStewardship") != {
        "statePath": ".tmp/run-coordinator/elim-gap-obligations.json",
        "stateRole": "replaceable-cache",
        "durableAuthority": (
            "framework/logs/ELIM_RUN_LOG.md#machine-readable-discovery-markers"
        ),
        "reconstructBeforeQueueBuild": True,
        "maximumObligations": 512,
        "closureProofRequired": True,
        "outsideContributionExactRevisionRequired": True,
    }:
        raise ValueError(
            "gapStewardship must preserve exact history and closure-proof controls"
        )


def plan(args: argparse.Namespace) -> int:
    config = read_json(args.config)
    validate_config(config)
    previous = read_json(args.previous, {})
    signals = read_json(args.signals, {})
    now = parse_time(args.now) or utc_now()
    chain_id = args.chain_id or f"arrp-{now.strftime('%Y%m%dT%H%M%SZ')}"
    is_resume = bool(args.resume and previous)
    if is_resume:
        chain_id = previous["chain_id"]
    lock = acquire_lock(args.lock_path, chain_id, is_resume)
    repo = repository_state(args.repo)
    health = workflow_health(config, args.repo)
    stages = []
    for order, definition in enumerate(config["stages"], start=1):
        due, reason = stage_due(definition, previous, signals, now)
        old = previous_stage(previous, definition["id"]) if is_resume else {}
        retained = old.get("status") == "succeeded"
        status = "succeeded" if retained else ("pending" if due else "not_due")
        stages.append(
            {
                "id": definition["id"],
                "order": order,
                "workflow": definition.get("workflow"),
                "due": due,
                "due_reason": reason,
                "status": status,
                "started_at": old.get("started_at") if retained else None,
                "completed_at": old.get("completed_at") if retained else (
                    iso(now) if not due else None
                ),
                "last_success_at": last_success_at(previous, definition["id"]),
                "retry_limit": int(definition["retry"]["maximumAttempts"]),
                "retries": list(old.get("retries", [])) if retained else [],
                "failure_class": "none",
                "details": "Retained from resumed chain" if retained else "",
                "output": old.get("output") if retained else None,
            }
        )
    manifest = {
        "schema_version": 1,
        **status_projection_contract(len(stages)),
        "bot_id": config["agentId"],
        "chain_id": chain_id,
        "run_id": args.run_id or chain_id,
        "trigger": args.trigger,
        "llm_launch_allowed": bool(signals.get("allow_elim_launch", False)),
        "llm_launch_trigger": signals.get("elim_launch_trigger") or args.trigger,
        "created_at": previous.get("created_at", iso(now)) if is_resume else iso(now),
        "updated_at": iso(now),
        "status": "planned",
        "baseline_commit": repo["head"],
        "resume": {
            "count": int(previous.get("resume", {}).get("count", 0)) + int(is_resume),
            "from_run_id": previous.get("run_id") if is_resume else None,
        },
        "lock": lock,
        "repository": repo,
        "workflow_health": health,
        "stages": stages,
        "failures": [],
        "degradations": [],
        "queue_counts": {
            "integrity": 0,
            "monitoring": 0,
            "sources": 0,
            "intake": int(bool(signals.get("intake_pending", False))),
            "total": int(bool(signals.get("intake_pending", False))),
        },
        "elim_decision": {
            "launch_recommended": False,
            "reason": "Chain stages have not completed.",
            "blockers": [],
            "last_substantive_stage": True,
        },
        "review_epoch": review_epoch(config, previous, signals, now),
        "usage": {
            "hard_reserve_percent": config["usage"]["hardReservePercent"],
            "soft_run_target_percent": config["usage"]["softRunTargetPercent"],
            "remaining_percent": None,
            "status": "not_checked",
        },
        "next_action": "Run the first due deterministic stage.",
    }
    if not repo["clean"]:
        manifest["failures"].append(
            {
                "stage": "preflight",
                "classification": "blocking",
                "message": "Repository working tree is not clean.",
            }
        )
    if not health["healthy"]:
        manifest["failures"].append(
            {
                "stage": "preflight",
                "classification": "configuration",
                "message": "One or more configured workflows are missing.",
            }
        )
    atomic_write(args.output, manifest)
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            for stage in stages:
                key = stage["id"].replace("-", "_") + "_due"
                handle.write(f"{key}={str(stage['due'] and stage['status'] != 'succeeded').lower()}\n")
            handle.write(f"chain_id={chain_id}\n")
            handle.write(
                "comprehensive_due="
                + str(manifest["review_epoch"]["due"]).lower()
                + "\n"
            )
    return 0


def find_stage(manifest: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for stage in manifest["stages"]:
        if stage["id"] == stage_id:
            return stage
    raise ValueError(f"unknown run-chain stage: {stage_id}")


def record(args: argparse.Namespace) -> int:
    if args.status not in STAGE_STATUSES:
        raise ValueError(f"invalid stage status: {args.status}")
    if args.failure_class not in FAILURE_CLASSES:
        raise ValueError(f"invalid failure classification: {args.failure_class}")
    manifest = read_json(args.manifest)
    stage = find_stage(manifest, args.stage)
    now = parse_time(args.now) or utc_now()
    if args.status == "running" and stage.get("started_at") is None:
        stage["started_at"] = iso(now)
    if args.status in STAGE_STATUSES - {"pending", "running"}:
        stage["completed_at"] = iso(now)
    stage["status"] = args.status
    stage["failure_class"] = args.failure_class
    stage["details"] = args.details
    if args.retry:
        stage["retries"].append(
            {
                "attempt": len(stage["retries"]) + 1,
                "at": iso(now),
                "classification": args.failure_class,
                "details": args.details,
            }
        )
    if args.output_file:
        stage["output"] = {
            "path": args.output_label or str(args.output_file),
            "sha256": file_hash(args.output_file),
        }
    if args.work_count is not None:
        stage["work_count"] = max(0, args.work_count)
    if args.status == "succeeded":
        stage["last_success_at"] = iso(now)
    manifest["updated_at"] = iso(now)
    atomic_write(args.manifest, manifest)
    return 0


def apply_stage_results(
    manifest: dict[str, Any],
    results: dict[str, Any],
    now: datetime,
    config: dict[str, Any],
) -> None:
    config_by_id = {
        stage["id"]: stage for stage in config.get("stages", [])
    }
    for stage in manifest["stages"]:
        raw = results.get(stage["id"])
        if not stage["due"]:
            continue
        if raw is None and stage.get("status") in {
            "succeeded",
            "failed",
            "degraded",
        }:
            # A host-side usage check re-finalizes the already completed cloud
            # manifest with no new stage results. Preserve every terminal
            # outcome, including an expressly nonblocking degradation.
            continue
        if raw is None:
            stage["status"] = "failed"
            stage["failure_class"] = "blocking"
            stage["details"] = "Due stage supplied no result."
        else:
            result = raw if isinstance(raw, dict) else {"result": raw}
            conclusion = result.get("result", "failure")
            if conclusion == "success":
                stage["status"] = "succeeded"
                stage["failure_class"] = "none"
                stage["last_success_at"] = iso(now)
            elif conclusion == "skipped":
                stage["status"] = "failed"
                stage["failure_class"] = "blocking"
            else:
                fallback = config_by_id.get(stage["id"], {}).get(
                    "failureClass", "blocking"
                )
                stage["status"] = "degraded" if fallback == "degraded" else "failed"
                stage["failure_class"] = fallback
            stage["details"] = str(result.get("details", conclusion))
            stage["work_count"] = max(0, int(result.get("work_count", 0) or 0))
            attempt_key = str(result.get("attempt_key") or "")
            if attempt_key:
                if attempt_key not in {"primary", "retry"}:
                    raise ValueError(
                        f"stage {stage['id']} has invalid attempt identity"
                    )
                stage["attempt_key"] = attempt_key
            run_id = str(result.get("run_id") or "")
            if run_id:
                if not attempt_key or not run_id.endswith(":" + attempt_key):
                    raise ValueError(
                        f"stage {stage['id']} run ID differs from its attempt identity"
                    )
                stage["run_id"] = run_id
            domain_event = result.get("domain_event")
            if domain_event is not None:
                if not isinstance(domain_event, dict) or set(domain_event) != {
                    "id",
                    "sha256",
                    "json",
                }:
                    raise ValueError(
                        f"stage {stage['id']} has malformed domain-event identity"
                    )
                stage["domain_event"] = domain_event
            else:
                stage.pop("domain_event", None)
            if result.get("retried"):
                stage.setdefault("retries", []).append(
                    {
                        "attempt": len(stage.get("retries", [])) + 1,
                        "at": iso(now),
                        "classification": "transient",
                        "details": f"First attempt: {result.get('first_result', 'failure')}",
                    }
                )
            if result.get("output_hash"):
                stage["output"] = {
                    "path": str(result.get("output_path", "workflow-output")),
                    "sha256": str(result["output_hash"]),
                }
        stage["completed_at"] = iso(now)


def finalize(args: argparse.Namespace) -> int:
    config = read_json(args.config)
    validate_config(config)
    manifest = read_json(args.manifest)
    now = parse_time(args.now) or utc_now()
    results = read_json(args.stage_results, {})
    apply_stage_results(manifest, results, now, config)
    stage_ids = {stage["id"] for stage in manifest["stages"]}
    failures = [
        item
        for item in manifest.get("failures", [])
        if item.get("stage") not in stage_ids
    ]
    degradations = []
    queue = dict(manifest["queue_counts"])
    for key in ("integrity", "monitoring", "sources"):
        queue[key] = 0
    for stage in manifest["stages"]:
        count = int(stage.get("work_count", 0))
        if stage["id"] == "project-integrity-bot":
            queue["integrity"] = count
        elif stage["id"] == "source-checker-bot":
            queue["sources"] = count
        elif stage["id"] in {"case-monitor-bot", "presidential-directives-bot"}:
            queue["monitoring"] = int(queue.get("monitoring", 0)) + count
        if stage["status"] == "failed":
            failures.append(
                {
                    "stage": stage["id"],
                    "classification": stage["failure_class"],
                    "message": stage["details"] or "Stage failed.",
                }
            )
        elif stage["status"] == "degraded":
            degradations.append(
                {
                    "stage": stage["id"],
                    "classification": stage["failure_class"],
                    "message": stage["details"] or "Stage completed in degraded mode.",
                }
            )
    queue["total"] = sum(
        int(queue.get(key, 0)) for key in ("integrity", "monitoring", "sources", "intake")
    )
    manifest["queue_counts"] = queue
    manifest["failures"] = failures
    manifest["degradations"] = degradations
    manifest["action_items"] = [
        {
            "id": "chain-failure-"
            + hashlib.sha256(
                f"{manifest.get('chain_id')}:{item.get('stage')}:{item.get('message')}".encode()
            ).hexdigest()[:16],
            "owner": "human",
            "kind": "automation_failure",
            "stage": item.get("stage"),
            "classification": item.get("classification"),
            "summary": "Run-chain stage requires attention.",
        }
        for item in failures
    ]
    reserve = float(config["usage"]["hardReservePercent"])
    remaining = args.usage_remaining
    usage_status = (
        "unknown"
        if remaining is None
        else "blocked"
        if remaining <= reserve
        else "available"
    )
    manifest["usage"]["remaining_percent"] = remaining
    manifest["usage"]["status"] = usage_status
    gateway = manifest.get("work_queue")
    repair_unit = selected_repair_unit(gateway)
    blockers = [] if repair_unit is not None else [item["message"] for item in failures]
    if gateway and not gateway.get("ready_for_elim"):
        blockers.extend(str(item) for item in gateway.get("problems") or [])
    runtime_overrides = manifest.get("user_overrides") or {}
    attached_overrides = (
        (gateway.get("user_overrides") or {})
        if isinstance(gateway, dict)
        else {}
    )
    if not isinstance(runtime_overrides, dict):
        blockers.append("Local queue overrides are not a valid object.")
    elif runtime_overrides and (
        attached_overrides.get("request_sha256") != json_hash(runtime_overrides)
    ):
        blockers.append(
            "Local queue overrides have not been applied to exact queue selection "
            "and its bound context packet."
        )
    prior_complete = all(
        stage["status"] in TERMINAL_SUCCESS or stage["status"] == "degraded"
        for stage in manifest["stages"]
    )
    needs_llm = bool(
        (
            gateway.get("launch_recommended")
            if gateway
            else queue["total"]
        )
        or manifest["review_epoch"]["due"]
    )
    governance_current = bool(
        isinstance(gateway, dict)
        and isinstance(gateway.get("governance_discovery"), dict)
        and gateway["governance_discovery"].get("current_for_cadence")
    )
    governance_waiting_for_ordinary = bool(
        isinstance(gateway, dict)
        and isinstance(gateway.get("governance_discovery"), dict)
        and gateway["governance_discovery"].get("waiting_for_ordinary_queue")
    )
    if not manifest.get("llm_launch_allowed", False):
        decision, reason = (
            False,
            "This trigger authorizes deterministic refresh only; Elim waits for "
            "the daily schedule, an eligible event, or explicit manual dispatch.",
        )
    elif blockers:
        decision, reason = False, "Blocking bot or preflight failure requires correction."
    elif not prior_complete and repair_unit is None:
        decision, reason = False, "One or more due deterministic stages is incomplete."
    elif remaining is None:
        decision, reason = False, "Codex usage reserve has not been measured."
    elif remaining <= reserve:
        decision, reason = False, "Codex usage is at or below the hard reserve."
    elif not needs_llm:
        if governance_current:
            decision, reason = (
                False,
                "No ordinary LLM-owned work remains and the last committed "
                "governance review is current for its minimum cadence.",
            )
        elif governance_waiting_for_ordinary:
            decision, reason = (
                False,
                "Ordinary work remains ahead of governance discovery but is not "
                "currently launchable under the recorded queue controls.",
            )
        else:
            decision, reason = (
                False,
                "No LLM-owned work is due because the Context Gateway did not supply "
                "the required quiet-queue governance-discovery fallback.",
            )
    else:
        if repair_unit is not None:
            decision, reason = (
                True,
                "A safety-class-0 bot-failure unit is authorized for repair-only "
                "work before any other Elim unit.",
            )
        else:
            decision, reason = True, (
                "Comprehensive review is due."
                if manifest["review_epoch"]["due"]
                else "The refreshed queue contains LLM-owned work."
            )
    attached_context_profile = str(
        ((manifest.get("context_packet") or {}).get("profile") or "")
    )
    if attached_context_profile:
        profile_name, profile = model_profile_for_context(
            config,
            attached_context_profile,
        )
        selected_id = str(
            ((manifest.get("work_queue") or {}).get("selected_work_item_id") or "")
        )
        profile_reason = (
            f"Bound to selected work item {selected_id} and context profile "
            f"{attached_context_profile}."
        )
    elif manifest["review_epoch"]["due"]:
        profile_name = "comprehensive"
        profile_reason = "The periodic comprehensive review epoch is due."
        profile = config["llmRouting"]["profiles"][profile_name]
    else:
        active_classes = {
            key
            for key in ("integrity", "monitoring", "sources", "intake")
            if int(queue.get(key, 0)) > 0
        }
        triage_classes = set(
            config["llmRouting"]["profiles"]["read-heavy-triage"][
                "eligibleQueueClasses"
            ]
        )
        if active_classes and active_classes <= triage_classes:
            profile_name = "read-heavy-triage"
            profile_reason = "Only read-heavy monitoring, source, or intake triage is queued."
        else:
            profile_name = config["llmRouting"]["defaultProfile"]
            profile_reason = "The queue may require substantive project judgment."
        profile = config["llmRouting"]["profiles"][profile_name]
    manifest["elim_decision"] = {
        "launch_recommended": decision,
        "reason": reason,
        "blockers": blockers,
        "last_substantive_stage": True,
        "predecessors_complete": prior_complete,
        "profile": {
            "id": profile_name,
            "model": profile["model"],
            "reasoning_effort": profile["reasoningEffort"],
            "full_context": profile["fullContext"],
            "reason": profile_reason,
        },
    }
    manifest["status"] = (
        "blocked"
        if blockers
        else "degraded"
        if degradations or (failures and repair_unit is not None)
        else "complete"
    )
    manifest["next_action"] = (
        "Authorized host dispatcher may launch Elim."
        if decision
        else "Resolve the blocking run-chain or Context Gateway condition."
        if blockers
        else "No Elim launch; wait for the next trigger."
    )
    manifest["updated_at"] = iso(now)
    manifest["completed_at"] = iso(now)
    manifest["final_revision"] = (
        manifest.get("repository", {}).get("head") or manifest.get("baseline_commit")
    )
    normalized = {
        "succeeded": "completed",
        "not_due": "not_due",
        "skipped": "not_due",
        "degraded": "degraded",
        "failed": "failed",
        "pending": "pending",
        "running": "running",
    }
    manifest["bots"] = [
        {
            "id": stage["id"],
            "name": stage["id"],
            "due": stage["due"],
            "status": normalized.get(stage["status"], stage["status"]),
            "started_at": stage.get("started_at"),
            "completed_at": stage.get("completed_at"),
            "error": (
                stage.get("details")
                if stage["status"] in {"failed", "degraded"}
                else None
            ),
        }
        for stage in manifest["stages"]
        if stage.get("workflow")
    ]
    release_lock(manifest["lock"])
    atomic_write(args.output or args.manifest, manifest)
    return 0


def attach_context(args: argparse.Namespace) -> int:
    manifest = read_json(args.manifest)
    queue = read_json(args.queue)
    if queue.get("schema_version") != 1:
        raise ValueError("Elim work queue has an unsupported schema")
    config = read_json(getattr(args, "config", DEFAULT_CONFIG))
    validate_config(config)
    comprehensive_due = bool((manifest.get("review_epoch") or {}).get("due"))
    selected = selected_work_item(
        queue,
        comprehensive_required=comprehensive_due,
    )
    selected_id = str((selected or {}).get("id") or "")
    selected_kind = str((selected or {}).get("kind") or "")
    repair_selected = bool(
        selected
        and selected_kind == "bot_failure"
        and selected.get("safety_class") == 0
    )
    prior_full_context = bool(
        ((manifest.get("elim_decision") or {}).get("profile") or {}).get(
            "full_context"
        )
    )
    if prior_full_context != comprehensive_due and not (
        repair_selected and comprehensive_due and prior_full_context
    ):
        raise ValueError(
            "the chain's model profile and Review Epoch state disagree about "
            "whether comprehensive context is required"
        )
    finalized_revision = manifest.get("final_revision")
    if (
        not isinstance(finalized_revision, str)
        or len(finalized_revision) != 40
        or any(character not in "0123456789abcdef" for character in finalized_revision)
    ):
        raise ValueError("run-chain final_revision must be a 40-character Git hash")
    queue_revision = queue.get("repository_revision")
    if (
        not isinstance(queue_revision, str)
        or len(queue_revision) != 40
        or any(character not in "0123456789abcdef" for character in queue_revision)
    ):
        raise ValueError(
            "Elim work queue repository_revision must be a 40-character Git hash"
        )
    if queue_revision != finalized_revision:
        raise ValueError(
            "Elim work queue repository revision differs from the finalized chain"
        )
    if selected and not selected_id:
        raise ValueError("selected Elim work item has no deterministic ID")
    expected_context_profile = (
        CONTEXT_PROFILE_BY_WORK_KIND.get(selected_kind) if selected else None
    )
    launch_ready = bool(
        queue.get("ready_for_elim")
        and (queue.get("launch_recommended") or comprehensive_due)
    )
    if launch_ready and not selected:
        raise ValueError(
            "the launch-ready Elim queue has no selected eligible work item"
        )
    if selected and not expected_context_profile:
        raise ValueError(
            f"no reviewed context profile exists for work kind {selected_kind!r}"
        )
    queue_path = args.queue.resolve()
    queue_overrides = queue.get("user_overrides") or {}
    if not isinstance(queue_overrides, dict):
        raise ValueError("Elim work queue user_overrides must be an object")
    applied_override_ids = queue_overrides.get("applied") or []
    unmatched_override_ids = queue_overrides.get("unmatched") or []
    if not all(
        isinstance(values, list)
        and all(isinstance(value, str) for value in values)
        for values in (applied_override_ids, unmatched_override_ids)
    ):
        raise ValueError("Elim work queue override IDs must be string arrays")
    override_hash = str(queue_overrides.get("request_sha256") or "")
    if override_hash and (
        len(override_hash) != 71
        or not override_hash.startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in override_hash[7:])
    ):
        raise ValueError("Elim work queue override request hash is invalid")
    governance_discovery = governance_discovery_projection(queue, config)
    gap_obligations = gap_obligation_projections(
        queue,
        maximum=config["gapStewardship"]["maximumObligations"],
    )
    queue_counts = queue.get("counts") or {}
    if not isinstance(queue_counts, dict):
        raise ValueError("Elim work queue counts must be an object")
    expected_special_counts = {
        "gap_obligations": len(gap_obligations),
        "governance_discovery": int(
            governance_discovery["selected_as_quiet_queue_fallback"]
        ),
    }
    for field, actual in expected_special_counts.items():
        declared = queue_counts.get(field)
        if declared is not None and (
            isinstance(declared, bool)
            or not isinstance(declared, int)
            or declared != actual
        ):
            raise ValueError(
                f"Elim work queue {field} count differs from its typed projection"
            )
    manifest["work_queue"] = {
        "path": "project-console-data:elim-work-queue.json",
        "sha256": file_hash(queue_path),
        "ready_for_elim": bool(queue.get("ready_for_elim")),
        "launch_recommended": bool(queue.get("launch_recommended")),
        "counts": queue_counts,
        "problems": queue.get("problems") or [],
        "next_item": selected,
        "selected_work_item_id": selected_id or None,
        "governance_discovery": governance_discovery,
        "gap_obligations": gap_obligations,
        "user_overrides": {
            "applied": sorted(applied_override_ids),
            "unmatched": sorted(unmatched_override_ids),
            "request_sha256": override_hash or json_hash({}),
        },
    }
    manifest["queue_counts"]["total"] = int(
        (queue.get("counts") or {}).get("total", 0)
    )
    if args.context:
        context = read_json(args.context)
        if not isinstance(context, dict):
            raise ValueError("Elim context packet must be a JSON object")
        if context.get("schema_version") != 2 or context.get("status") == "blocked":
            raise ValueError("Elim context packet is blocked or unsupported")
        if context.get("provenance_complete") is not True:
            raise ValueError("Elim context packet provenance is incomplete")
        limits = context.get("limits")
        if not isinstance(limits, dict):
            raise ValueError("Elim context packet has no valid limits")
        actual = limits.get("actual_bytes")
        maximum = limits.get("max_bytes")
        if (
            isinstance(actual, bool)
            or isinstance(maximum, bool)
            or not isinstance(actual, int)
            or not isinstance(maximum, int)
            or actual <= 0
            or maximum <= 0
            or actual > maximum
        ):
            raise ValueError("Elim context packet byte limits are invalid")
        if context.get("repository_revision") != finalized_revision:
            raise ValueError(
                "Elim context packet repository revision differs from the finalized chain"
            )
        if not selected:
            raise ValueError(
                "an Elim context packet was attached without a selected eligible work item"
            )
        source = selected.get("source") or {}
        if not isinstance(source, dict):
            raise ValueError(
                f"selected work item {selected_id} has invalid source metadata"
            )
        canonical_aliases = [
            str(source.get(key) or "").strip()
            for key in ("canonical_record", "canonicalRecord")
            if source.get(key) is not None
        ]
        if len(set(canonical_aliases)) > 1:
            raise ValueError(
                f"selected work item {selected_id} has conflicting canonical records"
            )
        expected_canonical = canonical_aliases[0] if canonical_aliases else ""
        selection = context.get("selection")
        if launch_ready and not isinstance(selection, dict):
            raise ValueError(
                "launch-ready Elim context packet has no exact work-item selection"
            )
        if isinstance(selection, dict):
            if not {
                "work_item_id",
                "kind",
                "canonical_record",
            } <= set(selection):
                raise ValueError(
                    "Elim context packet selection is missing required identity fields"
                )
            selected_canonical = str(selection.get("canonical_record") or "").strip()
            if (
                selection.get("work_item_id") != selected_id
                or selection.get("kind") != selected_kind
                or selected_canonical != expected_canonical
            ):
                raise ValueError(
                    "Elim context packet selection differs from the selected queue "
                    f"work item {selected_id}"
                )
        if context.get("profile") != expected_context_profile:
            raise ValueError(
                f"selected work item {selected_id} requires context profile "
                f"{expected_context_profile!r}, but the packet uses "
                f"{context.get('profile')!r}"
            )
        expected_issue = (
            str(source.get("identifier") or "")
            if selected_kind in ISSUE_DOSSIER_WORK_KINDS
            else ""
        )
        dossier = context.get("issue_dossier")
        actual_issue = (
            str(dossier.get("issue_id") or "")
            if isinstance(dossier, dict)
            else ""
        )
        if expected_issue and actual_issue != expected_issue:
            raise ValueError(
                f"selected work item {selected_id} requires issue {expected_issue}, "
                f"but the context packet carries {actual_issue or 'no issue dossier'}"
            )
        if expected_issue:
            if not expected_canonical:
                raise ValueError(
                    f"selected work item {selected_id} has no canonical record"
                )
            canonical_record = (
                dossier.get("canonical_record")
                if isinstance(dossier, dict)
                else None
            )
            issue_page = (
                dossier.get("issue_page") if isinstance(dossier, dict) else None
            )
            actual_canonical = str(
                (
                    canonical_record.get("path")
                    if isinstance(canonical_record, dict)
                    else ""
                )
                or (
                    issue_page.get("path")
                    if isinstance(issue_page, dict)
                    else ""
                )
                or (
                    dossier.get("canonical_record_path")
                    if isinstance(dossier, dict)
                    else ""
                )
                or ""
            ).strip()
            if actual_canonical != expected_canonical:
                raise ValueError(
                    f"selected work item {selected_id} requires canonical record "
                    f"{expected_canonical!r}, but the context packet carries "
                    f"{actual_canonical or 'no canonical record'!r}"
                )
        if not expected_issue and actual_issue:
            raise ValueError(
                f"selected work item {selected_id} is not issue-specific, but the "
                f"context packet carries issue {actual_issue}"
            )
        model_profile_id, model_profile = model_profile_for_context(
            config,
            str(expected_context_profile),
        )
        manifest["elim_decision"]["profile"] = {
            "id": model_profile_id,
            "model": model_profile["model"],
            "reasoning_effort": model_profile["reasoningEffort"],
            "full_context": model_profile["fullContext"],
            "reason": (
                f"Bound to selected work item {selected_id} and context profile "
                f"{expected_context_profile}."
            ),
        }
        context_path = args.context.resolve()
        manifest["context_packet"] = {
            "path": "project-console-data:elim-context.json",
            "sha256": file_hash(context_path),
            "profile": context.get("profile"),
            "work_item_id": selected_id,
            "issue_id": expected_issue or None,
            "canonical_record": expected_canonical or None,
            "selection": (
                {
                    "work_item_id": selected_id,
                    "kind": selected_kind,
                    "canonical_record": expected_canonical or None,
                }
                if isinstance(selection, dict)
                else None
            ),
            "repository_revision": context.get("repository_revision"),
            "provenance_complete": True,
            "limits": limits,
        }
    else:
        if launch_ready:
            raise ValueError(
                f"launch-ready work item {selected_id or 'unknown'} has no context packet"
            )
        manifest["context_packet"] = None
    if not queue.get("ready_for_elim"):
        manifest["elim_decision"]["launch_recommended"] = False
        manifest["elim_decision"]["reason"] = (
            "Context Gateway blocked launch: "
            + "; ".join(queue.get("problems") or ["queue input is not current"])
        )
        manifest["elim_decision"]["blockers"] = list(queue.get("problems") or [])
        manifest["status"] = "blocked"
        manifest["next_action"] = "Refresh or repair the blocked Context Gateway input."
    elif not queue.get("launch_recommended") and not manifest["review_epoch"]["due"]:
        manifest["elim_decision"]["launch_recommended"] = False
        governance = queue.get("governance_discovery") or {}
        if governance.get("current_for_cadence"):
            manifest["elim_decision"]["reason"] = (
                "No ordinary LLM-owned work remains and the last committed "
                "governance review is current for its minimum cadence."
            )
            manifest["next_action"] = (
                "Wait for the recorded governance next-due time or new ordinary work."
            )
        elif governance.get("waiting_for_ordinary_queue"):
            manifest["elim_decision"]["reason"] = (
                "Ordinary work remains ahead of governance discovery but is not "
                "currently launchable under the recorded queue controls."
            )
            manifest["next_action"] = (
                "Wait for or revise the recorded ordinary-work queue control."
            )
        else:
            manifest["elim_decision"]["reason"] = (
                "No LLM-owned work is present; verify the required quiet-queue "
                "governance-discovery fallback before treating this as a no-op."
            )
            manifest["next_action"] = (
                "Rebuild the current queue or repair the governance-discovery fallback."
            )
    manifest["updated_at"] = iso(utc_now())
    atomic_write(args.output or args.manifest, manifest)
    return 0


def materialize_watcher_inputs(args: argparse.Namespace) -> int:
    manifest = read_json(args.manifest)
    if not isinstance(manifest, dict):
        raise ValueError("run-chain manifest must be a JSON object")
    materialize_selected_watcher_artifacts(
        manifest,
        args.artifacts,
        args.destination,
    )
    return 0


def parser() -> argparse.ArgumentParser:
    main = argparse.ArgumentParser(description=__doc__)
    commands = main.add_subparsers(dest="command", required=True)
    p = commands.add_parser("plan")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--previous", type=Path)
    p.add_argument("--signals", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--github-output", type=Path)
    p.add_argument("--lock-path", type=Path)
    p.add_argument("--chain-id")
    p.add_argument("--run-id")
    p.add_argument("--trigger", default="manual")
    p.add_argument("--now")
    p.add_argument("--resume", action="store_true")
    p.set_defaults(function=plan)

    p = commands.add_parser("record")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--stage", required=True)
    p.add_argument("--status", required=True)
    p.add_argument("--failure-class", default="none")
    p.add_argument("--details", default="")
    p.add_argument("--work-count", type=int)
    p.add_argument("--output-file", type=Path)
    p.add_argument("--output-label")
    p.add_argument("--retry", action="store_true")
    p.add_argument("--now")
    p.set_defaults(function=record)

    p = commands.add_parser("finalize")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--stage-results", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--usage-remaining", type=float)
    p.add_argument("--now")
    p.set_defaults(function=finalize)

    p = commands.add_parser("attach-context")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--queue", type=Path, required=True)
    p.add_argument("--context", type=Path)
    p.add_argument("--output", type=Path)
    p.set_defaults(function=attach_context)

    p = commands.add_parser("materialize-watcher-inputs")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--artifacts", type=Path, required=True)
    p.add_argument("--destination", type=Path, required=True)
    p.set_defaults(function=materialize_watcher_inputs)
    return main


def main() -> int:
    args = parser().parse_args()
    return args.function(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"run-coordinator-bot: {exc}")
