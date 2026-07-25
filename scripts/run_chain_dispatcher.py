#!/usr/bin/env python3
"""Host-side ARRP run-chain dispatcher.

This script is inert until invoked (for example, by an explicitly installed
launchd job).  It may trigger/wait for the GitHub chain, applies the first-party
Codex usage gate, and invokes Codex only when the finalized manifest authorizes
an Elim unit.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    from arrp_context import ContextError, contained_path
    from elim_execution import validate_work_unit
    from record_review_epoch import (
        validate as validate_review_epoch,
        validate_finding_continuity,
    )
except ModuleNotFoundError:  # Imported as scripts.run_chain_dispatcher.
    from scripts.arrp_context import ContextError, contained_path
    from scripts.elim_execution import validate_work_unit
    from scripts.record_review_epoch import (
        validate as validate_review_epoch,
        validate_finding_continuity,
    )


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".github" / "run-coordinator-bot.json"
RUN_URL = re.compile(r"/actions/runs/(\d+)")
THREAD_ID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
EXECUTABLES = {
    "pythonPath": "/opt/homebrew/bin/python3",
    "gitPath": "/usr/bin/git",
    "githubCliPath": "/opt/homebrew/bin/gh",
    "codexPath": "/Applications/ChatGPT.app/Contents/Resources/codex",
    "notificationPath": "/usr/bin/osascript",
}
ALLOWED_EXECUTABLES = frozenset(EXECUTABLES.values())
REPOSITORY_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WORKFLOW_NAME = re.compile(r"^[A-Za-z0-9_.-]+\.ya?ml$")
APPROVED_ORIGIN_URLS = frozenset(
    {
        "https://github.com/Thorncrag/ARRP.git",
        "git@github.com:Thorncrag/ARRP.git",
    }
)
ELIM_RESULT_FIELDS = frozenset(
    {
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
        "continuation",
    }
)
ELIM_RESULT_OUTCOMES = frozenset(
    {"completed", "clean", "blocked", "failed", "human_review", "usage_stopped"}
)
CURRENT_AUDIT_STATES = frozenset({"Open", "Paused", "Blocked", "Inactive"})
CURRENT_AUDIT_INACTIVE_FIELDS = {
    "Active issue/task": "None.",
    "Audit type/tier": "None.",
    "Started": "None.",
    "User request": "None.",
    "Scope": "None.",
    "Files touched": "None.",
    "Completed steps": "None.",
    "Next step": "None.",
    "Blockers/questions": "None.",
    "Validation status": "Not applicable.",
}
WORK_TYPE_BY_QUEUE_KIND = {
    "integrity": "integrity",
    "bot_failure": "bot_failure",
    "public_intake": "public_intake",
    "change_audit": "change_audit",
    "issue_audit": "issue_audit",
    "issue_development": "issue_development",
    "candidate_research": "candidate_research",
    "comprehensive_review": "comprehensive_review",
}
ISSUE_WORK_TYPES = frozenset(
    {"change_audit", "issue_audit", "issue_development"}
)
ELIM_RUN_LOG = "framework/logs/ELIM_RUN_LOG.md"
AGENT_AUDIT_LOG = "framework/logs/AGENT_AUDIT_LOG.md"
CURRENT_AUDIT_LOG = "framework/logs/CURRENT_AUDIT.md"
INTAKE_REVIEW_LEDGER = "research/intake-review-ledger.jsonl"
ELIM_RUN_REPORT_FIELDS = frozenset(
    {
        "Started",
        "Ended",
        "Run ID",
        "Trigger",
        "Outcome",
        "Usage",
        "Work summary",
        "Material units",
        "Issue audit records",
        "Commits and synchronization",
        "Validation",
        "Human review",
        "Stop reason",
        "Exact next action",
    }
)
NONMATERIAL_RESULT_PATHS = frozenset(
    {ELIM_RUN_LOG, AGENT_AUDIT_LOG, CURRENT_AUDIT_LOG}
)
SAFE_CHAIN_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
AUTOMATION_RUNTIME_PATHS = (
    ".github/run-coordinator-bot.json",
    "scripts/arrp_context.py",
    "scripts/build_elim_context.py",
    "scripts/build_elim_work_queue.py",
    "scripts/check_codex_usage_reserve.py",
    "scripts/elim_execution.py",
    "scripts/record_review_epoch.py",
    "scripts/run_chain_dispatcher.py",
    "scripts/run_coordinator.py",
    "scripts/run_coordinator_control.py",
    "scripts/select_elim_context_route.py",
)
ELIM_RECOVERY_STATE = ".tmp/run-coordinator/elim-recovery.json"
ELIM_RUN_LOG_RECONCILIATION_STATE = (
    ".tmp/run-coordinator/elim-run-log-reconciliation.json"
)
MAX_PENDING_RUN_LOG_RECONCILIATIONS = 128
MAX_BOOTSTRAP_FAILURE_EVENTS = 128
HOST_OUTCOME_HISTORY = ".tmp/run-coordinator/run-chain-history.json"
USAGE_BASELINE_DIRECTORY = ".tmp/run-coordinator/usage-baselines"
ELIM_CHECKOUT_PATH = ".tmp/run-coordinator/elim-checkout"
HOST_CLOSEOUT_BRANCH_PREFIX = "codex/elim-"
HOST_GIT_IDENTITY = {
    "name": "ARRP Run Coordinator",
    "email": "arrp-run-coordinator@users.noreply.github.com",
}
HOST_CLOSEOUT_POLICY = {
    "owner": "trusted-host-dispatcher",
    "modelGitMutation": "forbidden",
    "changedPathPolicy": "exact-declared-set",
    "defaultPublication": "non-force-fast-forward-main",
    "humanReviewPublication": "open-unmerged-pull-request",
}
CANONICAL_WORKSPACE_RECONCILIATION_POLICY = {
    "requiredBranch": "main",
    "dirtyMainAction": "commit-fast-forward-push-and-defer",
    "changedPathPolicy": "complete-workspace",
    "commitMessage": "Preserve local ARRP changes before automated run",
    "requireConflictFree": True,
    "requireStagedDiffCheck": True,
    "divergentHistoryAction": "fail-closed",
}


class ControlSelectionChanged(RuntimeError):
    """Raised when user queue controls change after exact work selection."""


class DispatchLease:
    def __init__(
        self,
        *,
        lock_path: Path,
        owner_path: Path,
        descriptor: int,
        owner_token: str,
        repo: Path,
    ) -> None:
        self.lock_path = lock_path
        self.owner_path = owner_path
        self.descriptor = descriptor
        self.owner_token = owner_token
        self.repo = repo
        self.mutex = threading.Lock()
        self.heartbeat_stop = threading.Event()
        self.heartbeat_thread: threading.Thread | None = None


def read_json(path: Path, default: Any = None, root: Path = ROOT) -> Any:
    safe_path = contained_path(path, root)
    # safe_path has passed the symlink-aware repository-root containment check.
    if not safe_path.is_file():
        return default
    # safe_path has passed the symlink-aware repository-root containment check.
    return json.loads(safe_path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], root: Path = ROOT) -> None:
    safe_path = contained_path(path, root)
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = safe_path.with_suffix(safe_path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(safe_path)


def merge_control_states(
    latest: dict[str, Any],
    proposed: dict[str, Any],
    *,
    consumed_requests: dict[str, str] | None = None,
) -> dict[str, Any]:
    merged = dict(latest)
    merged.update(proposed)
    merged["schema_version"] = 1
    # User-owned queue state is always taken from the latest locked read.
    merged["overrides"] = dict(latest.get("overrides") or {})
    request_rows: dict[str, dict[str, Any]] = {}
    for row in [
        *(proposed.get("requests") or []),
        *(latest.get("requests") or []),
    ]:
        if isinstance(row, dict) and str(row.get("request_id") or ""):
            request_rows[str(row["request_id"])] = dict(row)
    merged["requests"] = list(request_rows.values())[-100:]
    for key in ("requested_run", "requested_comprehensive_review"):
        latest_request = latest.get(key)
        proposed_request = proposed.get(key)
        selected = latest_request if latest_request is not None else proposed_request
        consumed_id = (consumed_requests or {}).get(key)
        if (
            isinstance(selected, dict)
            and selected.get("request_id") != consumed_id
        ):
            merged[key] = selected
        else:
            merged.pop(key, None)

    proposed_items = {
        str(item.get("id")): dict(item)
        for item in proposed.get("action_items") or []
        if isinstance(item, dict) and item.get("id")
    }
    item_order = list(proposed_items)
    for item in latest.get("action_items") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        item_id = str(item["id"])
        if item_id not in item_order:
            item_order.append(item_id)
        proposed_items[item_id] = {
            **proposed_items.get(item_id, {}),
            **item,
        }
    merged["action_items"] = [proposed_items[item_id] for item_id in item_order]

    history_rows: dict[str, dict[str, Any]] = {}
    for row in [
        *(proposed.get("action_item_history") or []),
        *(latest.get("action_item_history") or []),
    ]:
        if not isinstance(row, dict):
            continue
        identity = str(
            row.get("request_id")
            or hashlib.sha256(
                json.dumps(row, sort_keys=True).encode()
            ).hexdigest()
        )
        history_rows[identity] = dict(row)
    merged["action_item_history"] = list(history_rows.values())
    merged["alert_fingerprints"] = sorted(
        {
            str(value)
            for value in [
                *(proposed.get("alert_fingerprints") or []),
                *(latest.get("alert_fingerprints") or []),
            ]
            if str(value)
        }
    )[-100:]
    merged["updated_at"] = datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat()
    return merged


def persist_control_state(
    path: Path,
    control: dict[str, Any],
    *,
    repo: Path,
    consumed_requests: dict[str, str] | None = None,
) -> None:
    safe_path = contained_path(path, repo)
    lock_path = contained_path(safe_path.with_suffix(".lock"), repo)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        lock_path,
        os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        latest = read_json(safe_path, {}, root=repo)
        if not isinstance(latest, dict):
            raise RuntimeError("coordinator control state is malformed")
        merged = merge_control_states(
            latest,
            control,
            consumed_requests=consumed_requests,
        )
        write_json(safe_path, merged, root=repo)
        control.clear()
        control.update(merged)
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def read_control_state_locked(path: Path, *, repo: Path) -> dict[str, Any]:
    safe_path = contained_path(path, repo)
    lock_path = contained_path(safe_path.with_suffix(".lock"), repo)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        lock_path,
        os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        fcntl.flock(descriptor, fcntl.LOCK_SH)
        value = read_json(safe_path, {}, root=repo)
        if not isinstance(value, dict):
            raise RuntimeError("coordinator control state is malformed")
        return value
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def canonical_json_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def control_overrides_match_selection(
    control: dict[str, Any],
    payload: dict[str, Any],
) -> bool:
    latest = control.get("overrides") or {}
    if not isinstance(latest, dict):
        raise RuntimeError("coordinator queue overrides are malformed")
    recorded = (
        ((payload.get("work_queue") or {}).get("user_overrides") or {}).get(
            "request_sha256"
        )
    )
    return recorded == canonical_json_hash(latest)


def read_elim_result(path: Path, repo: Path) -> dict[str, Any]:
    safe_path = contained_path(path, repo)
    if not safe_path.is_file():
        raise ContextError("Elim did not emit its required structured result")
    try:
        value = json.loads(safe_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContextError("Elim structured result is not valid JSON") from exc
    if not isinstance(value, dict) or set(value) != ELIM_RESULT_FIELDS:
        raise ContextError("Elim structured result fields do not match the approved schema")
    try:
        validate_work_unit(value)
    except (AttributeError, TypeError) as exc:
        raise ContextError("Elim structured result has invalid field types") from exc
    if value.get("outcome") not in ELIM_RESULT_OUTCOMES:
        raise ContextError("Elim structured result has an invalid outcome")
    continuation = value.get("continuation")
    if not isinstance(continuation, dict) or set(continuation) != {
        "state",
        "next_action",
    }:
        raise ContextError("Elim structured result has an invalid continuation")
    if continuation["state"] not in {
        "complete",
        "retryable",
        "human_required",
        "none",
    }:
        raise ContextError("Elim structured result has an invalid continuation state")
    if not isinstance(value.get("human_questions"), list):
        raise ContextError("Elim structured result human_questions must be a list")
    return value


def selected_manifest_unit(payload: dict[str, Any]) -> dict[str, Any]:
    queue = payload.get("work_queue")
    if not isinstance(queue, dict):
        raise ContextError("current Chain Manifest has no selected work queue")
    selected = queue.get("next_item")
    if not isinstance(selected, dict):
        raise ContextError("current Chain Manifest has no selected Elim work item")
    selected_id = str(queue.get("selected_work_item_id") or "").strip()
    item_id = str(selected.get("id") or "").strip()
    if not selected_id or item_id != selected_id:
        raise ContextError(
            "current Chain Manifest selected work-item identity is inconsistent"
        )
    kind = str(selected.get("kind") or "").strip()
    if kind not in WORK_TYPE_BY_QUEUE_KIND:
        raise ContextError(
            f"current Chain Manifest has unapproved work kind {kind!r}"
        )
    return selected


def verify_elim_result_binding(
    payload: dict[str, Any],
    result: dict[str, Any],
) -> None:
    chain_id = str(payload.get("chain_id") or "").strip()
    if not chain_id or result["run_id"] != chain_id:
        raise ContextError(
            "Elim structured result does not match the current Chain ID"
        )
    selected = selected_manifest_unit(payload)
    selected_id = str(selected["id"])
    selected_kind = str(selected["kind"])
    if result["unit_id"] != selected_id:
        raise ContextError(
            "Elim structured result does not match the selected work-unit ID"
        )
    expected_work_type = WORK_TYPE_BY_QUEUE_KIND[selected_kind]
    if result["work_type"] != expected_work_type:
        raise ContextError(
            "Elim structured result work_type does not match the selected "
            f"{selected_kind!r} queue kind"
        )

    source = selected.get("source") or {}
    if not isinstance(source, dict):
        raise ContextError("selected Elim work item has invalid source identity")
    source_canonical = [
        str(source.get(name) or "").strip()
        for name in ("canonicalRecord", "canonical_record")
        if source.get(name) is not None
    ]
    if len(set(source_canonical)) > 1:
        raise ContextError("selected Elim work item has conflicting canonical records")
    expected_canonical = source_canonical[0] if source_canonical else ""
    context = payload.get("context_packet") or {}
    if not isinstance(context, dict):
        raise ContextError("selected Elim work item has no valid context packet")
    if context.get("work_item_id") != selected_id:
        raise ContextError(
            "Elim context packet does not match the selected work-unit ID"
        )
    context_canonical = str(context.get("canonical_record") or "").strip()
    if context_canonical != expected_canonical:
        raise ContextError(
            "Elim context packet canonical identity differs from the selected work item"
        )
    result_canonical = str(result.get("canonical_record") or "").strip()
    if result_canonical != expected_canonical:
        raise ContextError(
            "Elim structured result canonical identity differs from the selected work item"
        )

    expected_issue = (
        str(context.get("issue_id") or source.get("identifier") or "").strip()
        if expected_work_type in ISSUE_WORK_TYPES
        else ""
    )
    result_issue = str(result.get("issue_id") or "").strip()
    if result_issue != expected_issue:
        raise ContextError(
            "Elim structured result issue identity differs from the selected work item"
        )


def persist_validated_recovery(
    repo: Path,
    path: Path,
    payload: dict[str, Any],
    result: dict[str, Any],
) -> None:
    verify_elim_result_binding(payload, result)
    prior = read_json(path, {"schema_version": 1, "items": []}, root=repo)
    if not isinstance(prior, dict) or not isinstance(prior.get("items"), list):
        raise ContextError("local Elim recovery state is malformed")
    by_id = {
        str(item.get("work_id") or ""): dict(item)
        for item in prior["items"]
        if isinstance(item, dict) and str(item.get("work_id") or "")
    }
    previous = by_id.get(result["unit_id"], {})
    selected = selected_manifest_unit(payload)
    state = str((result.get("continuation") or {}).get("state") or "none")
    if result["outcome"] in {"completed", "clean"}:
        state = "complete"
    by_id[result["unit_id"]] = {
        "work_id": result["unit_id"],
        "state": state,
        "attempt_count": int(previous.get("attempt_count") or 0) + 1,
        "continuation": result.get("continuation") or {},
        "last_outcome": result["outcome"],
        "next_retry_at": None,
        "source_revision": selected.get("source_revision"),
        "recorded_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    write_json(
        path,
        {
            "schema_version": 1,
            "items": [by_id[key] for key in sorted(by_id)],
        },
        root=repo,
    )


def read_pending_run_log_reconciliations(
    repo: Path,
    path: Path,
) -> dict[str, Any]:
    payload = read_json(
        path,
        {"schema_version": 1, "items": []},
        root=repo,
    )
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ContextError("Elim Run Log reconciliation state is malformed")
    rows = payload.get("items")
    if not isinstance(rows, list):
        raise ContextError("Elim Run Log reconciliation items must be an array")
    if len(rows) > MAX_PENDING_RUN_LOG_RECONCILIATIONS:
        raise ContextError(
            "Elim Run Log reconciliation state exceeds its bounded capacity"
        )
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ContextError(
                "Elim Run Log reconciliation state contains a non-object item"
            )
        chain_id = str(row.get("chain_id") or "").strip()
        invocation_id = str(row.get("invocation_id") or "").strip()
        if not SAFE_CHAIN_ID.fullmatch(chain_id):
            raise ContextError(
                "Elim Run Log reconciliation item has an invalid Chain ID"
            )
        if not SAFE_CHAIN_ID.fullmatch(invocation_id):
            raise ContextError(
                "Elim Run Log reconciliation item has an invalid invocation ID"
            )
        if chain_id in seen:
            raise ContextError(
                "Elim Run Log reconciliation state repeats a Chain ID"
            )
        seen.add(chain_id)
        execution_checkout = str(
            row.get("execution_checkout") or ""
        ).strip()[:240]
        if not execution_checkout:
            raise ContextError(
                "Elim Run Log reconciliation item lacks its execution checkout"
            )
        artifact_root = contained_path(repo / execution_checkout, repo)
        artifacts = row.get("artifacts") or {}
        if not isinstance(artifacts, dict):
            raise ContextError(
                "Elim Run Log reconciliation artifacts must be an object"
            )
        safe_artifacts: dict[str, str] = {}
        for name in (
            "output",
            "last_message",
            "usage_status",
            "current_audit",
        ):
            value = str(artifacts.get(name) or "").strip()
            if not value:
                continue
            artifact = contained_path(artifact_root / value, artifact_root)
            if not artifact.is_file():
                raise ContextError(
                    "Elim Run Log reconciliation evidence is missing: "
                    f"{chain_id}:{name}"
                )
            safe_artifacts[name] = value
        normalized.append(
            {
                "chain_id": chain_id,
                "invocation_id": invocation_id,
                "recorded_at": str(row.get("recorded_at") or "").strip(),
                "spawned_at": str(row.get("spawned_at") or "").strip(),
                "failure_stage": str(row.get("failure_stage") or "").strip()[:120],
                "reason_code": str(row.get("reason_code") or "").strip()[:80],
                "failure_summary": " ".join(
                    str(row.get("failure_summary") or "").split()
                )[:500],
                "selected_work_item_id": str(
                    row.get("selected_work_item_id") or ""
                ).strip()[:160],
                "selected_kind": str(row.get("selected_kind") or "").strip()[:80],
                "source_revision": str(row.get("source_revision") or "").strip()[:80],
                "execution_checkout": execution_checkout,
                "artifacts": safe_artifacts,
            }
        )
    return {
        "schema_version": 1,
        "updated_at": str(payload.get("updated_at") or "").strip() or None,
        "items": normalized,
    }


def persist_pending_run_log_reconciliation(
    repo: Path,
    path: Path,
    *,
    payload: dict[str, Any],
    invocation_id: str,
    failure_stage: str,
    reason_code: str,
    failure_summary: str,
    launch_state: dict[str, Any],
) -> bool:
    """Persist one bounded repair obligation only for a process that was spawned."""
    if launch_state.get("spawned") is not True:
        return False
    if launch_state.get("run_log_verified") is True:
        return False
    chain_id = str(payload.get("chain_id") or "").strip()
    if not SAFE_CHAIN_ID.fullmatch(chain_id):
        raise ContextError(
            "cannot persist Run Log reconciliation without a safe Chain ID"
        )
    if not SAFE_CHAIN_ID.fullmatch(str(invocation_id or "")):
        raise ContextError(
            "cannot persist Run Log reconciliation without a safe invocation ID"
        )
    state = read_pending_run_log_reconciliations(repo, path)
    by_chain = {row["chain_id"]: row for row in state["items"]}
    if (
        chain_id not in by_chain
        and len(by_chain) >= MAX_PENDING_RUN_LOG_RECONCILIATIONS
    ):
        raise ContextError(
            "Elim Run Log reconciliation state is full; human intervention is required"
        )
    selected = (payload.get("work_queue") or {}).get("next_item") or {}
    execution_checkout = str(
        launch_state.get("execution_checkout") or ""
    ).strip()[:240]
    if not execution_checkout:
        raise ContextError(
            "cannot persist Run Log reconciliation without its execution checkout"
        )
    artifact_root = contained_path(repo / execution_checkout, repo)
    artifacts: dict[str, str] = {}
    for key in ("output", "last_message", "usage_status", "current_audit"):
        value = str((launch_state.get("artifacts") or {}).get(key) or "").strip()
        if value:
            source = contained_path(artifact_root / value, artifact_root)
            if not source.is_file():
                continue
            if key == "current_audit":
                snapshot = contained_path(
                    artifact_root
                    / ".tmp"
                    / "run-coordinator"
                    / chain_id
                    / "current-audit-checkpoint.md",
                    artifact_root,
                )
                snapshot.parent.mkdir(parents=True, exist_ok=True)
                if source.stat().st_size > 1_000_000:
                    raise ContextError(
                        "CURRENT_AUDIT checkpoint exceeds the evidence size limit"
                    )
                temporary = snapshot.with_suffix(".md.tmp")
                temporary.write_bytes(source.read_bytes())
                temporary.replace(snapshot)
                artifacts[key] = repo_relative(snapshot, artifact_root)
            else:
                artifacts[key] = value
    existing = by_chain.get(chain_id) or {}
    recorded_at = (
        str(existing.get("recorded_at") or "").strip()
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )
    by_chain[chain_id] = {
        "chain_id": chain_id,
        "invocation_id": str(invocation_id),
        "recorded_at": recorded_at,
        "spawned_at": str(launch_state.get("spawned_at") or "").strip(),
        "failure_stage": str(failure_stage or "")[:120],
        "reason_code": str(reason_code or "")[:80],
        "failure_summary": " ".join(str(failure_summary or "").split())[:500],
        "selected_work_item_id": str(selected.get("id") or "")[:160],
        "selected_kind": str(selected.get("kind") or "")[:80],
        "source_revision": str(
            payload.get("final_revision")
            or payload.get("baseline_commit")
            or ""
        )[:80],
        "execution_checkout": execution_checkout,
        "artifacts": artifacts,
    }
    write_json(
        path,
        {
            "schema_version": 1,
            "updated_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "items": [by_chain[key] for key in sorted(by_chain)],
        },
        root=repo,
    )
    return True


def reconciliation_chain_ids(payload: dict[str, Any]) -> list[str]:
    selected = (payload.get("work_queue") or {}).get("next_item") or {}
    source = selected.get("source") or {}
    if source.get("input") != "run_log_reconciliation":
        return []
    values = source.get("pending_chain_ids")
    if not isinstance(values, list):
        raise ContextError(
            "Run Log reconciliation work unit lacks pending Chain IDs"
        )
    chain_ids = [str(value or "").strip() for value in values]
    if (
        not chain_ids
        or len(chain_ids) != len(set(chain_ids))
        or any(not SAFE_CHAIN_ID.fullmatch(value) for value in chain_ids)
    ):
        raise ContextError(
            "Run Log reconciliation work unit has invalid pending Chain IDs"
        )
    if str(payload.get("chain_id") or "").strip() in chain_ids:
        raise ContextError(
            "Run Log reconciliation cannot treat the current Chain ID as prior"
        )
    return chain_ids


def clear_reconciled_run_log_items(
    repo: Path,
    path: Path,
    *,
    payload: dict[str, Any],
    result: dict[str, Any],
) -> None:
    pending_ids = reconciliation_chain_ids(payload)
    if not pending_ids:
        return
    if result.get("outcome") != "completed":
        return
    selected = (payload.get("work_queue") or {}).get("next_item") or {}
    expected_revision = str(selected.get("source_revision") or "").strip()
    safe_path = contained_path(path, repo)
    actual_revision = (
        hashlib.sha256(safe_path.read_bytes()).hexdigest()
        if safe_path.is_file()
        else ""
    )
    if not expected_revision or actual_revision != expected_revision:
        raise ContextError(
            "Run Log reconciliation state changed after exact queue selection"
        )
    state = read_pending_run_log_reconciliations(repo, path)
    current_ids = {row["chain_id"] for row in state["items"]}
    missing = sorted(set(pending_ids) - current_ids)
    if missing:
        raise ContextError(
            "Run Log reconciliation state no longer contains selected Chain IDs: "
            + ", ".join(missing)
        )
    retained = [
        row for row in state["items"] if row["chain_id"] not in set(pending_ids)
    ]
    write_json(
        path,
        {
            "schema_version": 1,
            "updated_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "items": retained,
        },
        root=repo,
    )


def markdown_log_sections_from_text(body: str) -> list[str]:
    starts = [match.start() for match in re.finditer(r"(?m)^### (?!#)", body)]
    return [
        body[start : starts[index + 1] if index + 1 < len(starts) else len(body)]
        for index, start in enumerate(starts)
    ]


def markdown_log_sections(path: Path, repo: Path) -> list[str]:
    safe_path = contained_path(path, repo)
    if not safe_path.is_file():
        raise ContextError(f"required closeout log is missing: {repo_relative(path, repo)}")
    return markdown_log_sections_from_text(safe_path.read_text(encoding="utf-8"))


def markdown_table_value(section: str, field: str) -> str | None:
    match = re.search(
        rf"(?m)^\|\s*{re.escape(field)}\s*\|\s*([^|\n]+?)\s*\|\s*$",
        section,
    )
    if not match:
        return None
    return match.group(1).strip().strip("`").strip()


def matching_log_section(
    path: Path,
    repo: Path,
    *,
    run_id: str,
    unit_id: str | None = None,
) -> str | None:
    for section in markdown_log_sections(path, repo):
        if markdown_table_value(section, "Run ID") != run_id:
            continue
        if unit_id is not None and markdown_table_value(section, "Unit ID") != unit_id:
            continue
        return section
    return None


def git_text_at_commit(git: str, repo: Path, commit: str, relative: str) -> str:
    shown = command([git, "show", f"{commit}:{relative}"], cwd=repo)
    if shown.returncode != 0:
        raise ContextError(
            f"reported Elim commit does not contain required provenance file {relative}"
        )
    return shown.stdout


def matching_log_section_in_text(
    body: str,
    *,
    run_id: str,
    unit_id: str | None = None,
) -> str | None:
    for section in markdown_log_sections_from_text(body):
        if markdown_table_value(section, "Run ID") != run_id:
            continue
        if unit_id is not None and markdown_table_value(section, "Unit ID") != unit_id:
            continue
        return section
    return None


def matching_log_sections_in_text(
    body: str,
    *,
    run_id: str,
    unit_id: str | None = None,
) -> list[str]:
    return [
        section
        for section in markdown_log_sections_from_text(body)
        if markdown_table_value(section, "Run ID") == run_id
        and (
            unit_id is None
            or markdown_table_value(section, "Unit ID") == unit_id
        )
    ]


def markdown_table_fields(section: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for name, value in re.findall(
        r"(?m)^\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|\s*$",
        section,
    ):
        name = name.strip()
        value = value.strip().strip("`").strip()
        if name in {"Field", "---"}:
            continue
        if name in fields:
            raise ContextError(f"Elim Run Log report repeats field {name!r}")
        fields[name] = value
    return fields


def run_log_outcome_matches(result_outcome: str, log_outcome: str) -> bool:
    normalized = re.sub(r"\s+", " ", log_outcome.strip().casefold())
    if result_outcome == "human_review":
        return normalized.startswith("human review")
    expected_prefix = {
        "completed": "completed",
        "clean": "clean",
        "blocked": "blocked",
        "failed": "failed",
        "usage_stopped": "usage stopped",
    }.get(result_outcome)
    return bool(expected_prefix and normalized.startswith(expected_prefix))


def verify_reconciled_run_log_reports(
    *,
    current_body: str,
    prior_body: str,
    pending_chain_ids: list[str],
) -> None:
    for pending_chain_id in pending_chain_ids:
        current_sections = matching_log_sections_in_text(
            current_body,
            run_id=pending_chain_id,
        )
        if len(current_sections) != 1:
            raise ContextError(
                "Run Log reconciliation must synchronize exactly one report for "
                f"prior Chain ID {pending_chain_id}"
            )
        prior_sections = matching_log_sections_in_text(
            prior_body,
            run_id=pending_chain_id,
        )
        if prior_sections:
            raise ContextError(
                "Run Log reconciliation cannot clear a pending Chain ID whose "
                f"report predates the reviewed repair boundary: {pending_chain_id}"
            )
        fields = markdown_table_fields(current_sections[0])
        missing = sorted(ELIM_RUN_REPORT_FIELDS - set(fields))
        if missing:
            raise ContextError(
                f"reconciled Run Log report for {pending_chain_id} is incomplete; "
                "missing fields: " + ", ".join(missing)
            )
        blank = sorted(
            field
            for field in ELIM_RUN_REPORT_FIELDS
            if not fields[field].strip()
        )
        if blank:
            raise ContextError(
                f"reconciled Run Log report for {pending_chain_id} has blank fields: "
                + ", ".join(blank)
            )
        if not run_log_outcome_matches("failed", fields["Outcome"]):
            raise ContextError(
                f"reconciled Run Log report for {pending_chain_id} has an "
                "outcome other than Failed"
            )


def material_result_files(result: dict[str, Any]) -> list[str]:
    generated_prefixes = (
        "research/horizon-review-console/data/",
        ".tmp/",
    )
    generated_exact = {
        "research/horizon-review-console/catalog-data.js",
    }
    return sorted(
        path
        for path in result["files_touched"]
        if path not in NONMATERIAL_RESULT_PATHS
        and path not in generated_exact
        and not path.startswith(generated_prefixes)
    )


def verify_intake_review_ledger(
    repo: Path,
    result: dict[str, Any],
    *,
    git: str | None = None,
    commit: str | None = None,
) -> None:
    if git and commit:
        body = git_text_at_commit(git, repo, commit, INTAKE_REVIEW_LEDGER)
    else:
        ledger = contained_path(repo / INTAKE_REVIEW_LEDGER, repo)
        if not ledger.is_file():
            raise ContextError(
                "completed public-intake work has no Intake Review Ledger"
            )
        body = ledger.read_text(encoding="utf-8")
    for line in body.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContextError("Intake Review Ledger is not valid JSONL") from exc
        if not isinstance(row, dict):
            raise ContextError("Intake Review Ledger contains a non-object record")
        if (
            row.get("run_id") == result["run_id"]
            and row.get("unit_id") == result["unit_id"]
            and row.get("content_included") is False
        ):
            return
    raise ContextError(
        "completed public-intake result has no matching content-free ledger record"
    )


def verify_commit_and_synchronization(
    git: str | None,
    gh: str | None,
    repo: Path,
    result: dict[str, Any],
    *,
    baseline_commit: str,
) -> tuple[set[str], str]:
    commit = result.get("commit")
    if (
        git is None
        or not isinstance(commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", commit) is None
    ):
        raise ContextError(
            "completed material Elim work requires a full verified Git commit hash"
        )
    exists = command([git, "cat-file", "-e", f"{commit}^{{commit}}"], cwd=repo)
    if exists.returncode != 0:
        raise ContextError("Elim result commit is not a reachable Git commit object")
    if re.fullmatch(r"[0-9a-f]{40}", baseline_commit) is None:
        raise ContextError(
            "successful Elim closeout requires the pinned manifest baseline"
        )
    baseline_exists = command(
        [git, "cat-file", "-e", f"{baseline_commit}^{{commit}}"],
        cwd=repo,
    )
    if baseline_exists.returncode != 0:
        raise ContextError("pinned Elim manifest baseline is not a Git commit object")
    fetched = command([git, "fetch", "--prune", "origin"], cwd=repo)
    if fetched.returncode != 0:
        raise ContextError("could not refresh remote refs for Elim closeout")
    head = command([git, "rev-parse", "HEAD"], cwd=repo)
    remote = command([git, "rev-parse", "refs/remotes/origin/main"], cwd=repo)
    synchronization = result.get("synchronization")
    if not isinstance(synchronization, list) or not synchronization:
        raise ContextError(
            "completed material Elim work requires synchronization evidence"
        )
    normalized = " ".join(str(item).casefold() for item in synchronization)
    if result["outcome"] == "human_review":
        if gh is None:
            raise ContextError(
                "review-ready Elim work requires GitHub PR verification"
            )
        branches = command(
            [git, "branch", "-r", "--contains", commit],
            cwd=repo,
        )
        remote_branches = [
            line.strip()
            for line in branches.stdout.splitlines()
            if line.strip() and line.strip() != "origin/main"
        ]
        if branches.returncode != 0 or not remote_branches:
            raise ContextError(
                "review-ready Elim commit is not preserved on a remote branch"
            )
        prs = command(
            [
                gh,
                "pr",
                "list",
                "--repo",
                "Thorncrag/ARRP",
                "--state",
                "open",
                "--json",
                "number,headRefOid,baseRefName,baseRefOid,url",
                "--limit",
                "100",
            ],
            cwd=repo,
        )
        try:
            open_prs = json.loads(prs.stdout)
        except json.JSONDecodeError as exc:
            raise ContextError("GitHub PR readback is unreadable") from exc
        open_pr_rows = open_prs if isinstance(open_prs, list) else []
        matching_pr = next(
            (
                row
                for row in open_pr_rows
                if isinstance(row, dict)
                and row.get("headRefOid") == commit
                and row.get("baseRefName") == "main"
                and isinstance(row.get("baseRefOid"), str)
                and re.fullmatch(r"[0-9a-f]{40}", row["baseRefOid"]) is not None
                and str(row.get("url") or "").startswith(
                    "https://github.com/Thorncrag/ARRP/pull/"
                )
            ),
            None,
        )
        if (
            prs.returncode != 0
            or not isinstance(open_prs, list)
            or matching_pr is None
        ):
            raise ContextError(
                "review-ready Elim commit has no verifiable open pull request"
            )
        pr_base = str(matching_pr["baseRefOid"])
        base_ancestry = command(
            [git, "merge-base", "--is-ancestor", baseline_commit, pr_base],
            cwd=repo,
        )
        if base_ancestry.returncode != 0:
            raise ContextError(
                "review-ready pull request base does not descend from the pinned "
                "manifest baseline"
            )
        pr_files = command(
            [
                gh,
                "pr",
                "diff",
                str(matching_pr["number"]),
                "--repo",
                "Thorncrag/ARRP",
                "--name-only",
            ],
            cwd=repo,
        )
        if pr_files.returncode != 0:
            raise ContextError("could not read back the review-ready PR file set")
        if not all(
            marker in normalized
            for marker in ("pushed", "pull request", "readback")
        ):
            raise ContextError(
                "review-ready Elim synchronization evidence must record push, "
                "open pull request, and readback"
            )
        return (
            {
                line.strip()
                for line in pr_files.stdout.splitlines()
                if line.strip()
            },
            pr_base,
        )

    reachable = command(
        [
            git,
            "merge-base",
            "--is-ancestor",
            commit,
            "refs/remotes/origin/main",
        ],
        cwd=repo,
    )
    if reachable.returncode != 0:
        raise ContextError(
            "applied Elim result commit is not reachable from origin/main"
        )
    if (
        head.returncode != 0
        or remote.returncode != 0
        or head.stdout.strip() != remote.stdout.strip()
    ):
        raise ContextError("isolated checkout is not synchronized with origin/main")
    if commit != remote.stdout.strip():
        raise ContextError(
            "applied Elim result must report the exact reviewed origin/main boundary"
        )
    if not any(
        marker in normalized
        for marker in ("origin/main", "merged", "synchronized", "readback")
    ):
        raise ContextError(
            "Elim synchronization evidence does not identify a reviewed Git boundary"
        )
    topology = command(
        [git, "rev-list", "--parents", "-n", "1", commit],
        cwd=repo,
    )
    topology_parts = topology.stdout.split()
    if (
        topology.returncode != 0
        or not topology_parts
        or topology_parts[0] != commit
        or len(topology_parts) not in {2, 3}
        or any(re.fullmatch(r"[0-9a-f]{40}", part) is None for part in topology_parts)
    ):
        raise ContextError(
            "applied Elim result has an unsupported or unverifiable commit topology"
        )
    if len(topology_parts) == 3:
        comparison_base = topology_parts[1]
        baseline_ancestry = command(
            [
                git,
                "merge-base",
                "--is-ancestor",
                baseline_commit,
                comparison_base,
            ],
            cwd=repo,
        )
        if baseline_ancestry.returncode != 0:
            raise ContextError(
                "applied Elim merge first parent does not descend from the pinned "
                "manifest baseline"
            )
    else:
        comparison_base = baseline_commit
        baseline_ancestry = command(
            [git, "merge-base", "--is-ancestor", baseline_commit, commit],
            cwd=repo,
        )
        if baseline_ancestry.returncode != 0 or baseline_commit == commit:
            raise ContextError(
                "applied Elim boundary does not advance the pinned manifest baseline"
            )
    changed = command(
        [
            git,
            "diff",
            "--name-only",
            comparison_base,
            commit,
        ],
        cwd=repo,
    )
    if changed.returncode != 0:
        raise ContextError("could not verify the reported commit's reviewed file set")
    return (
        {
            line.strip()
            for line in changed.stdout.splitlines()
            if line.strip()
        },
        comparison_base,
    )


def verify_successful_elim_evidence(
    repo: Path,
    result: dict[str, Any],
    *,
    git: str | None,
    gh: str | None = None,
    expected_manifest: dict[str, Any] | None = None,
) -> None:
    material_files = material_result_files(result)
    if result["outcome"] == "clean" and material_files:
        raise ContextError("clean Elim result reports material files touched")
    baseline_commit = (
        expected_manifest.get("final_revision")
        or expected_manifest.get("baseline_commit")
        if isinstance(expected_manifest, dict)
        else None
    )
    if not isinstance(baseline_commit, str):
        raise ContextError(
            "successful Elim closeout requires its pinned Chain Manifest baseline"
        )
    reviewed_paths, comparison_base = verify_commit_and_synchronization(
        git,
        gh,
        repo,
        result,
        baseline_commit=baseline_commit,
    )
    required_changed = {ELIM_RUN_LOG}
    if material_files:
        required_changed.update(material_files)
        required_changed.add(AGENT_AUDIT_LOG)
    missing_from_boundary = sorted(required_changed - reviewed_paths)
    if missing_from_boundary:
        raise ContextError(
            "reported Elim commit or pull request does not contain the declared "
            "reviewed file set: " + ", ".join(missing_from_boundary)
        )
    unreported_changes = sorted(reviewed_paths - set(result["files_touched"]))
    if unreported_changes:
        raise ContextError(
            "reported Elim commit or pull request contains unreported changed files: "
            + ", ".join(unreported_changes)
        )
    commit = str(result["commit"])
    if git is None:
        raise ContextError("successful Elim provenance requires Git verification")
    current_run_log = git_text_at_commit(git, repo, commit, ELIM_RUN_LOG)
    prior_run_log = git_text_at_commit(git, repo, comparison_base, ELIM_RUN_LOG)
    run_sections = matching_log_sections_in_text(
        current_run_log,
        run_id=result["run_id"],
    )
    if not run_sections:
        raise ContextError(
            "reported Elim commit has no Run Log report for the current Chain ID"
        )
    if len(run_sections) != 1:
        raise ContextError(
            "reported Elim commit must contain exactly one Run Log report for "
            "the current Chain ID"
        )
    prior_run_sections = matching_log_sections_in_text(
        prior_run_log,
        run_id=result["run_id"],
    )
    if prior_run_sections:
        raise ContextError(
            "current Elim Run Log report predates the reviewed Git boundary"
        )
    run_fields = markdown_table_fields(run_sections[0])
    missing_run_fields = sorted(ELIM_RUN_REPORT_FIELDS - set(run_fields))
    if missing_run_fields:
        raise ContextError(
            "current Elim Run Log report is incomplete; missing fields: "
            + ", ".join(missing_run_fields)
        )
    blank_run_fields = sorted(
        field for field in ELIM_RUN_REPORT_FIELDS if not run_fields[field].strip()
    )
    if blank_run_fields:
        raise ContextError(
            "current Elim Run Log report has blank fields: "
            + ", ".join(blank_run_fields)
        )
    if not run_log_outcome_matches(result["outcome"], run_fields["Outcome"]):
        raise ContextError(
            "current Elim Run Log outcome does not match the structured result"
        )
    pending_chain_ids = reconciliation_chain_ids(expected_manifest or {})
    if pending_chain_ids and result["outcome"] == "completed":
        verify_reconciled_run_log_reports(
            current_body=current_run_log,
            prior_body=prior_run_log,
            pending_chain_ids=pending_chain_ids,
        )
    if material_files:
        shared_section = matching_log_section_in_text(
            git_text_at_commit(git, repo, commit, AGENT_AUDIT_LOG),
            run_id=result["run_id"],
            unit_id=result["unit_id"],
        )
        if shared_section is None:
            raise ContextError(
                "reported Elim commit lacks its shared Agent Audit Log entry"
            )
        if AGENT_AUDIT_LOG not in result["files_touched"]:
            raise ContextError(
                "completed material Elim work does not account for shared provenance"
            )
    if result["work_type"] == "public_intake":
        verify_intake_review_ledger(
            repo,
            result,
            git=git if material_files else None,
            commit=str(result.get("commit") or "") if material_files else None,
        )


def read_current_audit(path: Path, repo: Path) -> dict[str, str]:
    safe_path = contained_path(path, repo)
    if not safe_path.is_file():
        raise ContextError("CURRENT_AUDIT.md is missing")
    body = safe_path.read_text(encoding="utf-8")
    section = re.search(
        r"^## Current Task\s*$([\s\S]*?)(?=^## |\Z)",
        body,
        re.MULTILINE,
    )
    if not section:
        raise ContextError("CURRENT_AUDIT.md lacks its Current Task table")
    fields: dict[str, str] = {}
    for name, value in re.findall(
        r"^\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|\s*$",
        section.group(1),
        re.MULTILINE,
    ):
        if name in {"Field", "---"}:
            continue
        if name in fields:
            raise ContextError(f"CURRENT_AUDIT.md repeats field {name!r}")
        fields[name] = value.strip()
    required = {"Handoff state", "Last checkpoint"} | set(
        CURRENT_AUDIT_INACTIVE_FIELDS
    )
    if set(fields) != required:
        raise ContextError("CURRENT_AUDIT.md fields do not match the approved handoff table")
    if fields["Handoff state"] not in CURRENT_AUDIT_STATES:
        raise ContextError(
            f"CURRENT_AUDIT.md has invalid Handoff state {fields['Handoff state']!r}"
        )
    return fields


def verify_elim_closeout(repo: Path, result: dict[str, Any]) -> tuple[bool, str]:
    handoff = read_current_audit(
        repo / "framework" / "logs" / "CURRENT_AUDIT.md",
        repo,
    )
    outcome = result["outcome"]
    continuation = result["continuation"]
    state = continuation["state"]
    next_action = continuation["next_action"]

    if outcome in {"completed", "clean"}:
        if state not in {"complete", "none"}:
            raise ContextError(
                f"Elim outcome {outcome!r} contradicts continuation state {state!r}"
            )
        complete = True
    elif outcome == "human_review":
        if state != "human_required" or not result["human_questions"]:
            raise ContextError(
                "Elim human_review closeout requires a routed human question"
            )
        if not isinstance(next_action, str) or not next_action.strip():
            raise ContextError(
                "Elim human_review closeout requires an exact routed next action"
            )
        complete = True
    else:
        if state != "retryable":
            raise ContextError(
                f"Elim outcome {outcome!r} requires a retryable continuation"
            )
        if not isinstance(next_action, str) or not next_action.strip():
            raise ContextError(
                f"Elim outcome {outcome!r} requires an exact continuation"
            )
        complete = False

    if complete:
        failed_checks = [
            item.get("check")
            for item in result["validation"]
            if item.get("status") == "failed"
        ]
        if failed_checks:
            raise ContextError(
                "completed Elim work reports failed validation: "
                + ", ".join(str(item) for item in failed_checks)
            )
        if handoff["Handoff state"] != "Inactive":
            raise ContextError(
                "completed Elim work requires CURRENT_AUDIT.md Handoff state Inactive"
            )
        uncleared = {
            name: (handoff[name], expected)
            for name, expected in CURRENT_AUDIT_INACTIVE_FIELDS.items()
            if handoff[name] != expected
        }
        if uncleared:
            names = ", ".join(sorted(uncleared))
            raise ContextError(
                f"inactive CURRENT_AUDIT.md has uncleared task fields: {names}"
            )
        return True, "Elim completed and the dispatcher verified its required closeout."

    if handoff["Handoff state"] not in {"Paused", "Blocked"}:
        raise ContextError(
            f"Elim outcome {outcome!r} requires a Paused or Blocked handoff"
        )
    for name in ("Active issue/task", "Audit type/tier", "Scope", "Next step"):
        if handoff[name] in {"", "None."}:
            raise ContextError(
                f"{handoff['Handoff state']} CURRENT_AUDIT.md lacks {name}"
            )
    if handoff["Blockers/questions"] in {"", "None."}:
        raise ContextError(
            f"{handoff['Handoff state']} CURRENT_AUDIT.md lacks blocker semantics"
        )
    if handoff["Next step"] != next_action.strip():
        raise ContextError(
            "CURRENT_AUDIT.md Next step does not match Elim's exact continuation"
        )
    return False, f"Elim safely closed with outcome {outcome!r}; continuation is preserved."


def enforce_elim_result_closeout(
    outcome: int,
    *,
    repo: Path,
    result_path: Path,
    git: str | None = None,
    gh: str | None = None,
    expected_run_id: str | None = None,
    expected_manifest: dict[str, Any] | None = None,
    execution_repo: Path | None = None,
    accounting: dict[str, Any] | None = None,
) -> tuple[int, bool, str]:
    execution_repo = execution_repo or repo
    if accounting is not None:
        accounting["run_log_verified"] = False

    def verify_structured_result() -> tuple[dict[str, Any], bool, str]:
        result = read_elim_result(result_path, execution_repo)
        if expected_manifest is not None:
            verify_elim_result_binding(expected_manifest, result)
        elif expected_run_id is not None and result["run_id"] != expected_run_id:
            raise ContextError(
                "Elim structured result does not match the current Chain ID"
            )
        complete, detail = verify_elim_closeout(execution_repo, result)
        if git and result.get("commit"):
            require_clean_repo(git, execution_repo)
        verify_successful_elim_evidence(
            execution_repo,
            result,
            git=git,
            gh=gh,
            expected_manifest=expected_manifest,
        )
        if accounting is not None:
            accounting["run_log_verified"] = True
            accounting["result_outcome"] = result["outcome"]
        return result, complete, detail

    if outcome != 0:
        structured_failure = ""
        if result_path.is_file():
            try:
                _result, complete, detail = verify_structured_result()
                return (
                    outcome,
                    False,
                    (
                        "Elim process exited abnormally after its terminal Run Log "
                        "report was verified; the invocation remains failed."
                        if complete
                        else detail
                    ),
                )
            except (ContextError, OSError, RuntimeError, TypeError, ValueError) as exc:
                structured_failure = (
                    f" Its structured terminal result was not accountably closed: {exc}"
                )
        try:
            handoff = read_current_audit(
                execution_repo / CURRENT_AUDIT_LOG,
                execution_repo,
            )
        except (ContextError, OSError, RuntimeError, TypeError, ValueError) as exc:
            return (
                outcome,
                False,
                "Elim exited abnormally and its recovery checkpoint is invalid: "
                f"{exc}.{structured_failure}",
            )
        state = handoff["Handoff state"]
        if state == "Open":
            return (
                outcome,
                False,
                "Elim exited abnormally with an Open recovery checkpoint. Treat the "
                "checkpoint as unfinished-work evidence, never runtime liveness, and "
                "reconcile it before retrying the same work unit."
                + structured_failure,
            )
        if state == "Inactive":
            return (
                outcome,
                False,
                "Elim exited abnormally without a recoverable Paused or Blocked "
                "checkpoint; inspect its preserved output before retrying."
                + structured_failure,
            )
        return outcome, False, structured_failure.strip()
    try:
        _result, complete, detail = verify_structured_result()
    except (ContextError, OSError, RuntimeError, TypeError, ValueError) as exc:
        return 6, False, f"Elim closeout verification failed: {exc}"
    if not complete:
        return {
            "blocked": 4,
            "usage_stopped": 5,
            "failed": 6,
        }.get(str(_result.get("outcome") or ""), 6), False, detail
    return 0, True, ""


def executable(config: dict[str, Any], key: str) -> str:
    expected = EXECUTABLES[key]
    configured = str(config["hostDispatcher"][key])
    if configured != expected:
        raise RuntimeError(f"configured {key} differs from the reviewed host path")
    if not Path(expected).is_file() or not os.access(expected, os.X_OK):
        raise RuntimeError(f"reviewed {key} is unavailable: {expected}")
    return expected


def validate_host_closeout_policy(config: dict[str, Any]) -> None:
    configured = config.get("hostDispatcher", {}).get("repositoryCloseout")
    if configured != HOST_CLOSEOUT_POLICY:
        raise RuntimeError(
            "configured repository closeout policy differs from the reviewed "
            "trusted-host boundary"
        )
    workspace_policy = config.get("hostDispatcher", {}).get(
        "canonicalWorkspaceReconciliation"
    )
    if workspace_policy != CANONICAL_WORKSPACE_RECONCILIATION_POLICY:
        raise RuntimeError(
            "configured canonical-workspace reconciliation differs from the "
            "reviewed trusted-host boundary"
        )


def alert_failures(
    config: dict[str, Any],
    control: dict[str, Any],
    manifest: dict[str, Any],
    repo: Path,
) -> bool:
    failures = list(manifest.get("failures") or [])
    problems = list((manifest.get("work_queue") or {}).get("problems") or [])
    action_items = list(control.get("action_items") or [])
    control["action_items"] = action_items
    if not failures and not problems and manifest.get("status") != "blocked":
        return False
    material = json.dumps(
        {
            "chain_id": manifest.get("chain_id"),
            "failures": failures,
            "problems": problems,
        },
        sort_keys=True,
    )
    fingerprint = hashlib.sha256(material.encode()).hexdigest()[:20]
    seen = set(control.get("alert_fingerprints") or [])
    if fingerprint in seen:
        return False
    item = {
        "id": "automation-failure-" + fingerprint,
        "chain_id": manifest.get("chain_id"),
        "kind": "automation_failure",
        "owner": "human",
        "summary": "ARRP run chain requires attention.",
        "created_at": manifest.get("updated_at"),
        "failure_count": len(failures) + len(problems),
        "stage": (
            failures[-1].get("stage")
            if failures and isinstance(failures[-1], dict)
            else "run-coordinator"
        ),
        "details": (
            failures[-1].get("message")
            if failures and isinstance(failures[-1], dict)
            else "; ".join(str(problem) for problem in problems)
        ),
        "next_action": manifest.get("next_action"),
        "resolved": False,
    }
    control.setdefault("action_items", []).append(item)
    control["alert_fingerprints"] = [*sorted(seen), fingerprint][-100:]
    try:
        notification = executable(config, "notificationPath")
        notified = command(
            [
                notification,
                "-e",
                'display notification "Open the ARRP Console Action Items for details." '
                'with title "ARRP automation requires attention"',
            ],
            cwd=repo,
        )
        if notified.returncode != 0:
            control["last_notification_error"] = (
                notified.stderr.strip() or "macOS notification returned a failure"
            )
        else:
            control.pop("last_notification_error", None)
    except (OSError, RuntimeError, ValueError) as exc:
        control["last_notification_error"] = str(exc)
    return True


def append_host_outcome_history(
    config: dict[str, Any],
    repo: Path,
    *,
    chain_id: str | None,
    status: str,
    stage: str,
    exit_code: int,
    payload: dict[str, Any] | None = None,
) -> None:
    limit = config.get("manifest", {}).get("historyLimit")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise RuntimeError("manifest.historyLimit must be an integer from 1 through 100")
    payload = payload or {}
    selected = ((payload.get("work_queue") or {}).get("next_item") or {})
    usage = payload.get("usage") or {}
    record = {
        "recorded_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "chain_id": str(chain_id or payload.get("chain_id") or "") or None,
        "status": status,
        "stage": stage,
        "exit_code": int(exit_code),
        "work_item_id": (
            str(selected.get("id") or "") or None
            if isinstance(selected, dict)
            else None
        ),
        "elim_launch_recommended": bool(
            (payload.get("elim_decision") or {}).get("launch_recommended")
        ),
        "usage_status": str(usage.get("status") or "") or None,
        "action_required": status in {"failed", "blocked"},
    }
    history_path = repo / HOST_OUTCOME_HISTORY
    value = read_json(history_path, {"schema_version": 1, "items": []}, root=repo)
    if not isinstance(value, dict) or not isinstance(value.get("items"), list):
        raise RuntimeError("local host-outcome history is malformed")
    items = [item for item in value["items"] if isinstance(item, dict)]
    items.append(record)
    write_json(
        history_path,
        {"schema_version": 1, "items": items[-limit:]},
        root=repo,
    )


def record_terminal_failure(
    config: dict[str, Any],
    control: dict[str, Any],
    repo: Path,
    *,
    stage: str,
    message: str,
    exit_code: int,
    next_action: str,
    payload: dict[str, Any] | None = None,
    chain_id: str | None = None,
    control_path: Path | None = None,
) -> dict[str, Any]:
    recorded_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    fallback_path = repo / config["manifest"]["localFallback"]
    resolved_chain_id = (
        chain_id
        or (payload or {}).get("chain_id")
        or "host-dispatch-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    projection = (
        dict(payload)
        if isinstance(payload, dict)
        and payload.get("chain_id") == resolved_chain_id
        else {
            "schema_version": 1,
            "chain_id": resolved_chain_id,
            "stages": [],
            "work_queue": None,
            "context_packet": None,
            "action_items": [],
        }
    )
    projection["schema_version"] = 1
    projection["chain_id"] = resolved_chain_id
    projection["status"] = "failed"
    projection["updated_at"] = recorded_at
    projection["completed_at"] = recorded_at
    projection["next_action"] = next_action
    failure = {
        "stage": stage,
        "classification": "blocking",
        "message": message,
        "exit_code": exit_code,
        "recorded_at": recorded_at,
    }
    failures = list(projection.get("failures") or [])
    if not any(
        isinstance(item, dict)
        and item.get("stage") == stage
        and item.get("message") == message
        for item in failures
    ):
        failures.append(failure)
    projection["failures"] = failures[-100:]

    control["last_failed_chain_id"] = resolved_chain_id
    control["last_failed_exit_code"] = exit_code
    control["last_failed_reason"] = message
    control["updated_at"] = recorded_at
    alert_failures(config, control, projection, repo)
    projection["host_action_items"] = list(control.get("action_items") or [])
    write_json(fallback_path, projection, root=repo)
    append_host_outcome_history(
        config,
        repo,
        chain_id=resolved_chain_id,
        status="failed",
        stage=stage,
        exit_code=exit_code,
        payload=projection,
    )
    if control_path is not None:
        persist_control_state(control_path, control, repo=repo)
    return projection


def bootstrap_failure_config(repo: Path) -> dict[str, Any]:
    return {
        "repository": "Thorncrag/ARRP",
        "hostDispatcher": {
            "repositoryPath": str(repo),
            "notificationPath": EXECUTABLES["notificationPath"],
        },
        "manifest": {
            "localFallback": ".tmp/run-chain.json",
            "historyLimit": 24,
        },
    }


def prune_bootstrap_failure_events(
    repo: Path,
    event_dir: Path,
    *,
    keep: int = MAX_BOOTSTRAP_FAILURE_EVENTS,
) -> None:
    if isinstance(keep, bool) or not isinstance(keep, int) or keep < 1:
        raise ContextError("bootstrap-failure retention must be a positive integer")
    safe_dir = contained_path(event_dir, repo)
    if not safe_dir.is_dir():
        return
    recognized: list[Path] = []
    for candidate in safe_dir.iterdir():
        if (
            candidate.is_symlink()
            or not candidate.is_file()
            or re.fullmatch(
                r"\d{8}T\d{12}Z-\d+\.json",
                candidate.name,
            )
            is None
        ):
            continue
        recognized.append(contained_path(candidate, safe_dir))
    recognized.sort(key=lambda candidate: candidate.name)
    for expired in recognized[:-keep]:
        expired.unlink()


def record_bootstrap_failure_best_effort(
    repo: Path,
    *,
    stage: str,
    message: str,
    exit_code: int = 1,
) -> dict[str, Any]:
    """Preserve bootstrap health without racing an active dispatcher."""
    recorded_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    state_dir = contained_path(repo / ".tmp/run-coordinator", repo)
    event = {
        "schema_version": 1,
        "recorded_at": recorded_at,
        "status": "failed",
        "stage": stage,
        "message": " ".join(str(message).split())[:1000],
        "exit_code": int(exit_code),
        "shared_projection": False,
        "action_item": {
            "kind": "automation_failure",
            "owner": "human",
            "summary": "ARRP host dispatcher initialization requires attention.",
            "next_action": (
                "Inspect the dispatcher bootstrap failure, repair the exact "
                "prerequisite, and launch a fresh current chain."
            ),
        },
    }
    try:
        event_dir = state_dir / "bootstrap-failures"
        event_dir.mkdir(parents=True, exist_ok=True)
        event_path = event_dir / (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            + f"-{os.getpid()}.json"
        )
        write_json(event_path, event, root=repo)
    except (ContextError, OSError, TypeError, ValueError) as exc:
        event["durable_event_error"] = str(exc)
        event_path = None

    lock_path = state_dir / "host-dispatch.lock"
    descriptor: int | None = None
    if not lock_path.is_dir():
        try:
            state_dir.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            control_path = state_dir / "control.json"
            control = read_json(
                control_path,
                {"requests": [], "overrides": {}},
                root=repo,
            )
            if not isinstance(control, dict):
                control = {"requests": [], "overrides": {}}
            record_terminal_failure(
                bootstrap_failure_config(repo),
                control,
                repo,
                stage=stage,
                message=event["message"],
                exit_code=exit_code,
                next_action=event["action_item"]["next_action"],
                chain_id=(
                    "host-dispatch-"
                    + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                ),
                control_path=control_path,
            )
            event["shared_projection"] = True
        except (BlockingIOError, ContextError, OSError, RuntimeError, ValueError) as exc:
            event["shared_projection_error"] = str(exc)
        finally:
            if descriptor is not None:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                finally:
                    os.close(descriptor)

    if not event["shared_projection"]:
        try:
            notification = executable(
                bootstrap_failure_config(repo),
                "notificationPath",
            )
            notified = command(
                [
                    notification,
                    "-e",
                    'display notification "Open the ARRP Console Action Items '
                    'or bootstrap-failures for details." with title '
                    '"ARRP dispatcher initialization failed"',
                ],
                cwd=repo,
            )
            if notified.returncode != 0:
                event["notification_error"] = (
                    notified.stderr.strip()
                    or "macOS notification returned a failure"
                )
        except (OSError, RuntimeError, ValueError) as exc:
            event["notification_error"] = str(exc)
    if event_path is not None:
        try:
            write_json(event_path, event, root=repo)
            prune_bootstrap_failure_events(repo, event_path.parent)
        except (ContextError, OSError, TypeError, ValueError):
            pass
    return event


def command(
    argv: list[str],
    *,
    cwd: Path,
    stdin: str | None = None,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    if not argv or argv[0] not in ALLOWED_EXECUTABLES:
        raise RuntimeError("attempted to execute a command outside the reviewed allowlist")
    if any(not isinstance(value, str) or "\0" in value for value in argv):
        raise RuntimeError("command contains an invalid argument")
    # argv[0] is one of the fixed absolute executables above; shell=False is implicit.
    return subprocess.run(
        argv,
        cwd=cwd,
        input=stdin,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=False,
    )


def process_is_alive(pid: int) -> bool:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def write_dispatch_lock_owner(
    lease: DispatchLease,
    *,
    updates: dict[str, Any],
) -> dict[str, Any]:
    with lease.mutex:
        owner = read_json(lease.owner_path, {}, root=lease.repo)
        if owner.get("owner_token") != lease.owner_token:
            raise RuntimeError("run-chain lock ownership changed unexpectedly")
        owner.update(updates)
        owner["heartbeat_at"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )
        write_json(lease.owner_path, owner, root=lease.repo)
        return owner


def start_dispatch_heartbeat(
    lease: DispatchLease,
    *,
    interval_seconds: int,
) -> None:
    def refresh() -> None:
        while not lease.heartbeat_stop.wait(interval_seconds):
            try:
                write_dispatch_lock_owner(lease, updates={})
            except (OSError, RuntimeError, ValueError):
                return

    lease.heartbeat_thread = threading.Thread(
        target=refresh,
        name="arrp-dispatch-heartbeat",
        daemon=True,
    )
    lease.heartbeat_thread.start()


def record_interrupted_dispatch(
    *,
    repo: Path,
    config: dict[str, Any],
    control: dict[str, Any],
    owner: dict[str, Any],
) -> None:
    completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    manifest_path = repo / config["manifest"]["localFallback"]
    payload = read_json(manifest_path, {}, root=repo)
    chain_id = owner.get("chain_id") or payload.get("chain_id") or "unknown-chain"
    owner_status = owner.get("status")
    elim_started = owner_status in {
        "elim-running",
        "elim-soft-closeout",
        "elim-stop-requested",
        "elim-closeout",
    }
    output_path = owner.get("output_path")
    if elim_started and not output_path and chain_id != "unknown-chain":
        output_path = f".tmp/run-coordinator/elim-{chain_id}.jsonl"
    if elim_started:
        details = (
            "Elim was interrupted before dispatcher-verified closeout. Its preserved "
            "task and JSONL output may contain incomplete analysis, but no substantive "
            "result may be treated as applied until the run is reconciled."
        )
        stage = "elim"
        next_action = (
            "Review the interrupted Elim task and preserved output, reconcile any "
            "safe partial work, clear the stale handoff, and launch a fresh current "
            "chain."
        )
    else:
        details = (
            "The host run coordinator was interrupted before Elim began. No Elim "
            "failure or substantive work is inferred from the abandoned dispatcher."
        )
        stage = "run-coordinator"
        next_action = (
            "Review the interrupted coordinator stage and launch a fresh current chain."
        )
    if elim_started and owner.get("run_log_verified") is not True:
        try:
            execution_checkout = str(
                owner.get("execution_checkout") or ""
            ).strip()
            execution_repo = contained_path(repo / execution_checkout, repo)
            isolated_manifest = (
                execution_repo
                / ".tmp"
                / "run-coordinator"
                / str(chain_id)
                / "run-chain.json"
            )
            isolated_payload = read_json(
                isolated_manifest,
                payload,
                root=repo,
            )
            if not isinstance(isolated_payload, dict):
                isolated_payload = payload
            isolated_payload = dict(isolated_payload)
            isolated_payload["chain_id"] = chain_id

            def execution_relative(owner_key: str) -> str:
                value = str(owner.get(owner_key) or "").strip()
                if not value:
                    return ""
                artifact = contained_path(repo / value, repo)
                return repo_relative(artifact, execution_repo)

            persist_pending_run_log_reconciliation(
                repo,
                repo / ELIM_RUN_LOG_RECONCILIATION_STATE,
                payload=isolated_payload,
                invocation_id=str(owner.get("invocation_id") or ""),
                failure_stage="elim-execution",
                reason_code="abandoned-post-spawn-dispatch",
                failure_summary=details,
                launch_state={
                    "spawned": True,
                    "run_log_verified": False,
                    "spawned_at": owner.get("started_at"),
                    "execution_checkout": execution_checkout,
                    "artifacts": {
                        "output": execution_relative("output_path"),
                        "last_message": execution_relative(
                            "last_message_path"
                        ),
                        "usage_status": execution_relative(
                            "usage_status_path"
                        ),
                        "current_audit": CURRENT_AUDIT_LOG,
                    },
                },
            )
        except (ContextError, OSError, RuntimeError, TypeError, ValueError) as exc:
            details += (
                " The bounded Run Log reconciliation obligation could not be "
                f"persisted automatically: {exc}."
            )
    if output_path:
        details += f" Preserved output: {output_path}."
    runtime = None
    if elim_started:
        runtime = {
            "id": "elim",
            "name": "Elim",
            "status": "failed",
            "chain_id": chain_id,
            "started_at": owner.get("started_at"),
            "completed_at": completed_at,
            "exit_code": 130,
            "details": details,
        }
        control["elim_runtime"] = runtime
    if runtime:
        payload["elim_runtime"] = runtime
    record_terminal_failure(
        config,
        control,
        repo,
        stage=stage,
        message=details,
        exit_code=130,
        next_action=next_action,
        payload=payload,
        chain_id=chain_id,
    )


def recover_legacy_dispatch_lock(
    lock: Path,
    *,
    repo: Path,
    config: dict[str, Any],
    control: dict[str, Any],
) -> bool:
    if not lock.is_dir():
        return False
    owner_path = lock / "owner.json"
    owner = read_json(owner_path, {}, root=repo)
    owner_pid = owner.get("pid")
    owner_alive = process_is_alive(owner_pid) if isinstance(owner_pid, int) else False
    age_seconds = max(0.0, time.time() - lock.stat().st_mtime)
    stale_seconds = int(config["hostDispatcher"]["staleLockSeconds"])
    recoverable = (isinstance(owner_pid, int) and not owner_alive) or (
        not isinstance(owner_pid, int) and age_seconds >= stale_seconds
    )
    if not recoverable:
        raise RuntimeError("a legacy host dispatcher may own the run-chain lock")
    allowed = {"owner.json", "owner.json.tmp"}
    unexpected = {item.name for item in lock.iterdir()} - allowed
    if unexpected:
        raise RuntimeError(
            "stale run-chain lock contains unexpected files; human review required"
        )
    for name in allowed:
        candidate = lock / name
        if candidate.is_file():
            candidate.unlink()
    lock.rmdir()
    record_interrupted_dispatch(
        repo=repo,
        config=config,
        control=control,
        owner=owner,
    )
    return True


def acquire_dispatch_lock(
    lock: Path,
    *,
    repo: Path,
    config: dict[str, Any],
    control: dict[str, Any],
) -> tuple[bool, DispatchLease]:
    recovered = recover_legacy_dispatch_lock(
        lock,
        repo=repo,
        config=config,
        control=control,
    )
    descriptor = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        os.close(descriptor)
        raise RuntimeError("another host dispatcher owns the run-chain lock") from exc
    owner_path = lock.with_name(f"{lock.name}.owner.json")
    prior_owner = read_json(owner_path, {}, root=repo)
    if prior_owner:
        record_interrupted_dispatch(
            repo=repo,
            config=config,
            control=control,
            owner=prior_owner,
        )
        recovered = True
    local_manifest = read_json(
        repo / config["manifest"]["localFallback"],
        {},
        root=repo,
    )
    owner_token = secrets.token_hex(24)
    lease = DispatchLease(
        lock_path=lock,
        owner_path=owner_path,
        descriptor=descriptor,
        owner_token=owner_token,
        repo=repo,
    )
    write_json(
        owner_path,
        {
            "owner_token": owner_token,
            "pid": os.getpid(),
            "started_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "status": "dispatcher-running",
            "chain_id": local_manifest.get("chain_id"),
            "heartbeat_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
        },
        root=repo,
    )
    heartbeat_interval = max(
        5,
        min(30, int(config["hostDispatcher"]["staleLockSeconds"]) // 3),
    )
    start_dispatch_heartbeat(lease, interval_seconds=heartbeat_interval)
    return recovered, lease


def release_dispatch_lock(lease: DispatchLease) -> None:
    lease.heartbeat_stop.set()
    if lease.heartbeat_thread is not None:
        lease.heartbeat_thread.join(timeout=5)
    ownership_error: RuntimeError | None = None
    with lease.mutex:
        owner = read_json(lease.owner_path, {}, root=lease.repo)
        if owner.get("owner_token") != lease.owner_token:
            ownership_error = RuntimeError(
                "refusing to remove a run-chain owner record held by another acquisition"
            )
        elif lease.owner_path.is_file():
            lease.owner_path.unlink()
    try:
        fcntl.flock(lease.descriptor, fcntl.LOCK_UN)
    finally:
        os.close(lease.descriptor)
    if ownership_error:
        raise ownership_error


def require_clean_repo(git: str, repo: Path) -> None:
    status = command([git, "status", "--porcelain"], cwd=repo)
    if status.returncode != 0:
        raise RuntimeError("could not inspect the ARRP working tree")
    if status.stdout.strip():
        raise RuntimeError("ARRP working tree is not clean; automated dispatch deferred")


def worktree_changed_paths(git: str, repo: Path) -> set[str]:
    """Return the exact changed-path set without trusting shell parsing."""
    status = command(
        [
            git,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ],
        cwd=repo,
    )
    if status.returncode != 0:
        raise RuntimeError("could not inspect the isolated Elim working tree")
    changed: set[str] = set()
    for record in status.stdout.split("\0"):
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            raise ContextError("isolated Elim Git status contains an invalid record")
        code = record[:2]
        relative = record[3:]
        if "R" in code or "C" in code:
            raise ContextError(
                "host closeout does not accept an implicit rename or copy; "
                "Elim must report explicit stable paths"
            )
        if "U" in code or code in {"AA", "DD", "AU", "UA", "DU", "UD"}:
            raise ContextError("isolated Elim checkout contains an unresolved Git state")
        candidate = Path(relative)
        if (
            not relative
            or candidate.is_absolute()
            or ".." in candidate.parts
            or relative.startswith(".git/")
        ):
            raise ContextError(f"isolated Elim checkout reports an unsafe path: {relative}")
        contained_path(repo / candidate, repo)
        changed.add(candidate.as_posix())
    return changed


def verify_uncommitted_elim_evidence(
    git: str,
    repo: Path,
    result: dict[str, Any],
    *,
    expected_manifest: dict[str, Any],
) -> set[str]:
    """Verify the model-authored working tree before the trusted host stages it."""
    if result.get("commit") is not None:
        raise ContextError(
            "Elim must leave commit creation to the trusted host dispatcher"
        )
    declared = set(result["files_touched"])
    changed = worktree_changed_paths(git, repo)
    if changed != declared:
        missing = sorted(changed - declared)
        absent = sorted(declared - changed)
        details: list[str] = []
        if missing:
            details.append("unreported=" + ", ".join(missing))
        if absent:
            details.append("not_changed=" + ", ".join(absent))
        raise ContextError(
            "Elim working-tree changes do not match files_touched"
            + (": " + "; ".join(details) if details else "")
        )
    if ELIM_RUN_LOG not in changed:
        raise ContextError("every launched Elim outcome must update the Elim Run Log")

    material_files = material_result_files(result)
    if result["outcome"] == "clean" and material_files:
        raise ContextError("clean Elim result reports material files touched")
    if material_files and AGENT_AUDIT_LOG not in changed:
        raise ContextError(
            "material Elim work must update the shared Agent Audit Log"
        )

    baseline_commit = (
        expected_manifest.get("final_revision")
        or expected_manifest.get("baseline_commit")
    )
    if (
        not isinstance(baseline_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", baseline_commit) is None
    ):
        raise ContextError("host closeout lacks the pinned manifest baseline")
    current_run_log = contained_path(repo / ELIM_RUN_LOG, repo).read_text(
        encoding="utf-8"
    )
    prior_run_log = git_text_at_commit(
        git,
        repo,
        baseline_commit,
        ELIM_RUN_LOG,
    )
    run_sections = matching_log_sections_in_text(
        current_run_log,
        run_id=result["run_id"],
    )
    if len(run_sections) != 1:
        raise ContextError(
            "current working tree must contain exactly one Elim Run Log report "
            "for the current Chain ID"
        )
    if matching_log_sections_in_text(prior_run_log, run_id=result["run_id"]):
        raise ContextError(
            "current Elim Run Log report predates the selected host boundary"
        )
    run_fields = markdown_table_fields(run_sections[0])
    missing_run_fields = sorted(ELIM_RUN_REPORT_FIELDS - set(run_fields))
    if missing_run_fields:
        raise ContextError(
            "current Elim Run Log report is incomplete; missing fields: "
            + ", ".join(missing_run_fields)
        )
    blank_run_fields = sorted(
        field for field in ELIM_RUN_REPORT_FIELDS if not run_fields[field].strip()
    )
    if blank_run_fields:
        raise ContextError(
            "current Elim Run Log report has blank fields: "
            + ", ".join(blank_run_fields)
        )
    if not run_log_outcome_matches(result["outcome"], run_fields["Outcome"]):
        raise ContextError(
            "current Elim Run Log outcome does not match the structured result"
        )

    pending_chain_ids = reconciliation_chain_ids(expected_manifest)
    if pending_chain_ids and result["outcome"] == "completed":
        verify_reconciled_run_log_reports(
            current_body=current_run_log,
            prior_body=prior_run_log,
            pending_chain_ids=pending_chain_ids,
        )
    if material_files:
        shared_section = matching_log_section(
            repo / AGENT_AUDIT_LOG,
            repo,
            run_id=result["run_id"],
            unit_id=result["unit_id"],
        )
        if shared_section is None:
            raise ContextError(
                "material Elim working tree lacks its shared Agent Audit Log entry"
            )
    if result["work_type"] == "public_intake":
        verify_intake_review_ledger(repo, result)
    return changed


def host_closeout_branch(chain_id: str) -> str:
    if not SAFE_CHAIN_ID.fullmatch(chain_id):
        raise ContextError("host closeout received an unsafe Chain ID")
    branch = HOST_CLOSEOUT_BRANCH_PREFIX + chain_id.casefold()
    if len(branch) > 180:
        raise ContextError("host closeout branch name exceeds its bounded length")
    return branch


def host_preserve_elim_result(
    *,
    git: str,
    gh: str,
    repo: Path,
    result_path: Path,
    expected_manifest: dict[str, Any],
    repository: str,
) -> dict[str, Any]:
    """Validate model output, then perform the narrow trusted-host Git closeout."""
    if REPOSITORY_NAME.fullmatch(repository) is None:
        raise ContextError("host closeout repository identity is invalid")
    result = read_elim_result(result_path, repo)
    verify_elim_result_binding(expected_manifest, result)
    semantic_complete, _ = verify_elim_closeout(repo, result)
    if (
        semantic_complete
        and result["work_type"] == "comprehensive_review"
        and result["outcome"] == "completed"
    ):
        context_path = (expected_manifest.get("context_packet") or {}).get(
            "local_path"
        )
        if not context_path or not comprehensive_epoch_recorded(
            repo,
            result["run_id"],
            repo / str(context_path),
        ):
            raise ContextError(
                "completed comprehensive review lacks its validated Review Epoch"
            )
    changed = verify_uncommitted_elim_evidence(
        git,
        repo,
        result,
        expected_manifest=expected_manifest,
    )
    baseline_commit = str(
        expected_manifest.get("final_revision")
        or expected_manifest.get("baseline_commit")
    )

    origin = command([git, "remote", "get-url", "origin"], cwd=repo)
    if origin.returncode != 0 or origin.stdout.strip() not in APPROVED_ORIGIN_URLS:
        raise ContextError("isolated Elim checkout origin is not approved")
    fetched = command([git, "fetch", "--no-tags", "origin", "main"], cwd=repo)
    if fetched.returncode != 0:
        raise RuntimeError(
            "trusted host could not refresh origin/main before closeout: "
            + fetched.stderr.strip()
        )
    head = command([git, "rev-parse", "HEAD"], cwd=repo)
    remote = command([git, "rev-parse", "refs/remotes/origin/main"], cwd=repo)
    if (
        head.returncode != 0
        or remote.returncode != 0
        or head.stdout.strip() != baseline_commit
        or remote.stdout.strip() != baseline_commit
    ):
        raise ContextError(
            "origin/main or the isolated checkout advanced beyond the manifest; "
            "the reviewed Elim changes remain preserved but were not published"
        )

    branch = host_closeout_branch(result["run_id"])
    branch_exists = command(
        [git, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=repo,
    )
    if branch_exists.returncode == 0:
        raise ContextError(
            f"host closeout branch already exists and will not be replaced: {branch}"
        )
    switched = command(
        [git, "switch", "-c", branch, baseline_commit],
        cwd=repo,
    )
    if switched.returncode != 0:
        raise RuntimeError(
            "trusted host could not create the bounded Elim closeout branch: "
            + switched.stderr.strip()
        )
    staged = command(
        [git, "add", "--", *sorted(changed)],
        cwd=repo,
    )
    if staged.returncode != 0:
        raise RuntimeError(
            "trusted host could not stage the declared Elim files: "
            + staged.stderr.strip()
        )
    cached = command(
        [git, "diff", "--cached", "--name-only", "-z"],
        cwd=repo,
    )
    if cached.returncode != 0:
        raise RuntimeError("trusted host could not inspect the staged Elim boundary")
    staged_paths = {value for value in cached.stdout.split("\0") if value}
    if staged_paths != changed:
        raise ContextError(
            "trusted-host staged paths differ from the verified Elim working tree"
        )
    hygiene = command([git, "diff", "--cached", "--check"], cwd=repo)
    if hygiene.returncode != 0:
        raise ContextError(
            "trusted-host Elim closeout failed staged diff hygiene: "
            + hygiene.stdout.strip()
        )
    committed = command(
        [
            git,
            "-c",
            f"user.name={HOST_GIT_IDENTITY['name']}",
            "-c",
            f"user.email={HOST_GIT_IDENTITY['email']}",
            "commit",
            "-m",
            f"Preserve Elim {result['run_id']} {result['outcome']} closeout",
        ],
        cwd=repo,
    )
    if committed.returncode != 0:
        raise RuntimeError(
            "trusted host could not commit the verified Elim boundary: "
            + committed.stderr.strip()
        )
    commit_result = command([git, "rev-parse", "HEAD"], cwd=repo)
    commit = commit_result.stdout.strip()
    if (
        commit_result.returncode != 0
        or re.fullmatch(r"[0-9a-f]{40}", commit) is None
    ):
        raise RuntimeError("trusted host could not resolve the Elim closeout commit")
    parent = command([git, "rev-parse", f"{commit}^"], cwd=repo)
    committed_paths = command(
        [git, "diff", "--name-only", "-z", baseline_commit, commit],
        cwd=repo,
    )
    committed_path_set = {
        value for value in committed_paths.stdout.split("\0") if value
    }
    if (
        parent.returncode != 0
        or parent.stdout.strip() != baseline_commit
        or committed_paths.returncode != 0
        or committed_path_set != changed
    ):
        raise ContextError(
            "trusted-host commit topology or file set differs from the "
            "verified pre-commit boundary"
        )
    require_clean_repo(git, repo)

    synchronization: list[str]
    if result["outcome"] == "human_review":
        pushed = command(
            [git, "push", "origin", f"{commit}:refs/heads/{branch}"],
            cwd=repo,
        )
        if pushed.returncode != 0:
            raise RuntimeError(
                "trusted host could not push the human-review branch: "
                + pushed.stderr.strip()
            )
        title = f"Elim review: {result['unit_id']}"[:200]
        body = (
            f"Automated Elim run `{result['run_id']}` preserved a bounded "
            "human-review result. The host verified the exact declared diff; "
            "this pull request is intentionally not merged automatically."
        )
        created = command(
            [
                gh,
                "pr",
                "create",
                "--repo",
                repository,
                "--base",
                "main",
                "--head",
                branch,
                "--title",
                title,
                "--body",
                body,
            ],
            cwd=repo,
        )
        pr_url = created.stdout.strip()
        if (
            created.returncode != 0
            or not pr_url.startswith(f"https://github.com/{repository}/pull/")
        ):
            raise RuntimeError(
                "trusted host could not open the human-review pull request: "
                + created.stderr.strip()
            )
        readback = command(
            [
                gh,
                "pr",
                "view",
                pr_url,
                "--repo",
                repository,
                "--json",
                "state,url,headRefOid,baseRefOid",
            ],
            cwd=repo,
        )
        try:
            pr = json.loads(readback.stdout)
        except json.JSONDecodeError as exc:
            raise ContextError("human-review pull-request readback is unreadable") from exc
        if (
            readback.returncode != 0
            or not isinstance(pr, dict)
            or pr.get("state") != "OPEN"
            or pr.get("headRefOid") != commit
            or pr.get("baseRefOid") != baseline_commit
            or pr.get("url") != pr_url
        ):
            raise ContextError(
                "human-review pull-request readback differs from the verified boundary"
            )
        synchronization = [
            f"Trusted host pushed commit {commit} to {branch}.",
            f"Trusted host opened pull request {pr_url} without merging it.",
            "Trusted host read back the open pull request head and pinned main base.",
        ]
    else:
        pushed = command(
            [git, "push", "origin", f"{commit}:refs/heads/main"],
            cwd=repo,
        )
        if pushed.returncode != 0:
            raise RuntimeError(
                "trusted host compare-and-swap push to origin/main failed; "
                "the local closeout commit remains preserved: "
                + pushed.stderr.strip()
            )
        fetched = command([git, "fetch", "--no-tags", "origin", "main"], cwd=repo)
        remote = command([git, "rev-parse", "refs/remotes/origin/main"], cwd=repo)
        if (
            fetched.returncode != 0
            or remote.returncode != 0
            or remote.stdout.strip() != commit
        ):
            raise ContextError(
                "trusted host could not read back the exact pushed origin/main boundary"
            )
        detached = command(
            [git, "switch", "--detach", "refs/remotes/origin/main"],
            cwd=repo,
        )
        if detached.returncode != 0:
            raise RuntimeError(
                "trusted host could not return the isolated checkout to origin/main"
            )
        synchronization = [
            f"Trusted host committed the exact declared file set as {commit}.",
            "Trusted host used a non-forced fast-forward push to origin/main.",
            "Trusted host fetched and read back the exact origin/main commit.",
        ]

    model_result_path = result_path.with_name(
        result_path.stem + "-model-result.json"
    )
    write_json(model_result_path, result, root=repo)
    host_result = dict(result)
    host_result["commit"] = commit
    host_result["synchronization"] = synchronization
    host_result["validation"] = [
        *result["validation"],
        {
            "check": "Trusted-host Git closeout",
            "status": "passed",
            "detail": (
                "The dispatcher verified the exact declared working-tree boundary, "
                "created the commit, synchronized it without force, and read it back."
            ),
        },
    ]
    write_json(result_path, host_result, root=repo)
    require_clean_repo(git, repo)
    return host_result


def verify_canonical_runtime_boundary(
    git: str,
    repo: Path,
) -> tuple[str, str | None]:
    """Reconcile ordinary main-workspace edits, then verify the host runtime."""
    origin = command([git, "remote", "get-url", "origin"], cwd=repo)
    if (
        origin.returncode != 0
        or origin.stdout.strip() not in APPROVED_ORIGIN_URLS
    ):
        raise RuntimeError(
            "canonical ARRP origin does not match the reviewed GitHub repository"
        )
    fetched = command(
        [git, "fetch", "--no-tags", "origin", "main"],
        cwd=repo,
    )
    if fetched.returncode != 0:
        raise RuntimeError("could not refresh origin/main: " + fetched.stderr.strip())
    remote = command([git, "rev-parse", "refs/remotes/origin/main"], cwd=repo)
    revision = remote.stdout.strip()
    if remote.returncode != 0 or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise RuntimeError("could not resolve the reviewed origin/main revision")

    branch = command([git, "branch", "--show-current"], cwd=repo)
    if branch.returncode != 0:
        raise RuntimeError("could not identify the canonical ARRP workspace branch")
    status = command([git, "status", "--porcelain"], cwd=repo)
    if status.returncode != 0:
        raise RuntimeError("could not inspect the canonical ARRP working tree")
    head = command([git, "rev-parse", "HEAD"], cwd=repo)
    local_revision = head.stdout.strip()
    if (
        head.returncode != 0
        or re.fullmatch(r"[0-9a-f]{40}", local_revision) is None
    ):
        raise RuntimeError("could not resolve the canonical ARRP workspace revision")

    current_branch = branch.stdout.strip()
    required_branch = CANONICAL_WORKSPACE_RECONCILIATION_POLICY["requiredBranch"]
    if current_branch != required_branch:
        raise RuntimeError(
            "canonical ARRP workspace is not reconciled with GitHub: current branch "
            f"is {current_branch or 'detached HEAD'} instead of {required_branch}. Merge the "
            "intended branch through GitHub, return local main to origin/main, and "
            "retry automated dispatch."
        )
    if local_revision != revision:
        raise RuntimeError(
            "canonical ARRP workspace is not reconciled with GitHub: local HEAD "
            "does not equal the fetched origin/main revision. Reconcile the "
            "divergent history through GitHub and retry automated dispatch."
        )

    changed_paths = [
        line for line in status.stdout.splitlines() if line.strip()
    ]
    workspace_commit: str | None = None
    if changed_paths:
        unmerged = command(
            [git, "diff", "--name-only", "--diff-filter=U"],
            cwd=repo,
        )
        if unmerged.returncode != 0:
            raise RuntimeError(
                "could not inspect the canonical ARRP workspace for conflicts"
            )
        if unmerged.stdout.strip():
            raise RuntimeError(
                "canonical ARRP workspace contains unresolved conflicts; "
                "automated reconciliation stopped without staging or committing"
            )
        staged = command([git, "add", "-A"], cwd=repo)
        if staged.returncode != 0:
            raise RuntimeError(
                "could not stage the canonical ARRP workspace for automated "
                "reconciliation"
            )
        staged_paths = command(
            [git, "diff", "--cached", "--name-only"],
            cwd=repo,
        )
        if staged_paths.returncode != 0 or not staged_paths.stdout.strip():
            raise RuntimeError(
                "canonical ARRP workspace reported changes but produced no staged "
                "reconciliation boundary"
            )
        diff_check = command([git, "diff", "--cached", "--check"], cwd=repo)
        if diff_check.returncode != 0:
            raise RuntimeError(
                "staged canonical ARRP changes failed git diff --check; "
                "automated reconciliation stopped before commit"
            )
        committed = command(
            [
                git,
                "-c",
                f"user.name={HOST_GIT_IDENTITY['name']}",
                "-c",
                f"user.email={HOST_GIT_IDENTITY['email']}",
                "commit",
                "-m",
                CANONICAL_WORKSPACE_RECONCILIATION_POLICY["commitMessage"],
            ],
            cwd=repo,
        )
        if committed.returncode != 0:
            raise RuntimeError(
                "could not commit the staged canonical ARRP workspace"
            )
        committed_head = command([git, "rev-parse", "HEAD"], cwd=repo)
        workspace_commit = committed_head.stdout.strip()
        if (
            committed_head.returncode != 0
            or re.fullmatch(r"[0-9a-f]{40}", workspace_commit) is None
        ):
            raise RuntimeError(
                "could not resolve the automated workspace-reconciliation commit"
            )
        pushed = command([git, "push", "origin", "main:main"], cwd=repo)
        if pushed.returncode != 0:
            raise RuntimeError(
                "automated workspace reconciliation created local commit "
                f"{workspace_commit} but could not fast-forward push it to "
                "origin/main; preserve and reconcile that commit before retrying"
            )
        refreshed = command(
            [git, "fetch", "--no-tags", "origin", "main"],
            cwd=repo,
        )
        if refreshed.returncode != 0:
            raise RuntimeError(
                "automated workspace reconciliation pushed a commit but could not "
                "refresh origin/main for readback"
            )
        remote_readback = command(
            [git, "rev-parse", "refs/remotes/origin/main"],
            cwd=repo,
        )
        if (
            remote_readback.returncode != 0
            or remote_readback.stdout.strip() != workspace_commit
        ):
            raise RuntimeError(
                "automated workspace-reconciliation commit did not read back "
                "exactly from origin/main"
            )
        clean_readback = command([git, "status", "--porcelain"], cwd=repo)
        if clean_readback.returncode != 0 or clean_readback.stdout.strip():
            raise RuntimeError(
                "canonical ARRP workspace is not clean after automated "
                "reconciliation"
            )
        revision = workspace_commit

    drifted: list[str] = []
    for relative in AUTOMATION_RUNTIME_PATHS:
        local_path = contained_path(repo / relative, repo)
        if not local_path.is_file():
            drifted.append(relative)
            continue
        local_blob = command([git, "hash-object", relative], cwd=repo)
        remote_blob = command(
            [git, "rev-parse", f"refs/remotes/origin/main:{relative}"],
            cwd=repo,
        )
        if (
            local_blob.returncode != 0
            or remote_blob.returncode != 0
            or local_blob.stdout.strip() != remote_blob.stdout.strip()
        ):
            drifted.append(relative)
    if drifted:
        raise RuntimeError(
            "host automation runtime differs from reviewed origin/main: "
            + ", ".join(drifted)
        )
    return revision, workspace_commit


def archive_reconciled_elim_checkout(
    git: str,
    repo: Path,
    config: dict[str, Any],
    control: dict[str, Any],
    *,
    chain_id: str,
) -> dict[str, Any]:
    """Preserve a reconciled dirty checkout and release the fixed launch path."""
    if SAFE_CHAIN_ID.fullmatch(chain_id) is None:
        raise ContextError("checkout reconciliation received an unsafe Chain ID")
    configured = str(
        config["hostDispatcher"].get("isolatedCheckoutPath") or ""
    )
    if configured != ELIM_CHECKOUT_PATH:
        raise ContextError("configured Elim isolated checkout path is not approved")
    checkout = contained_path(repo / ELIM_CHECKOUT_PATH, repo)
    if not checkout.is_dir() or not (checkout / ".git").is_dir():
        raise ContextError("there is no preserved full Elim checkout to archive")

    pending = read_json(
        repo / ELIM_RUN_LOG_RECONCILIATION_STATE,
        {"schema_version": 1, "items": []},
        root=repo,
    )
    if not isinstance(pending, dict) or reconciliation_chain_ids(pending):
        raise ContextError(
            "pending Elim Run Log reconciliation must be cleared by proof first"
        )
    action_items = control.get("action_items") or []
    if not isinstance(action_items, list) or not any(
        isinstance(item, dict)
        and item.get("chain_id") == chain_id
        and item.get("resolved") is True
        for item in action_items
    ):
        raise ContextError(
            "checkout reconciliation requires the matching resolved Action Item"
        )

    canonical_origin = command([git, "remote", "get-url", "origin"], cwd=repo)
    checkout_origin = command([git, "remote", "get-url", "origin"], cwd=checkout)
    if (
        canonical_origin.returncode != 0
        or checkout_origin.returncode != 0
        or canonical_origin.stdout.strip() not in APPROVED_ORIGIN_URLS
        or checkout_origin.stdout.strip() != canonical_origin.stdout.strip()
    ):
        raise ContextError("preserved Elim checkout origin is not approved")
    canonical_revision = command(
        [git, "rev-parse", "refs/remotes/origin/main"],
        cwd=repo,
    )
    checkout_head = command([git, "rev-parse", "HEAD"], cwd=checkout)
    if (
        canonical_revision.returncode != 0
        or checkout_head.returncode != 0
        or re.fullmatch(
            r"[0-9a-f]{40}",
            canonical_revision.stdout.strip(),
        )
        is None
        or re.fullmatch(r"[0-9a-f]{40}", checkout_head.stdout.strip()) is None
    ):
        raise ContextError("checkout reconciliation lacks a verifiable Git boundary")

    current_run_log = git_text_at_commit(
        git,
        repo,
        canonical_revision.stdout.strip(),
        ELIM_RUN_LOG,
    )
    prior_run_log = git_text_at_commit(
        git,
        checkout,
        checkout_head.stdout.strip(),
        ELIM_RUN_LOG,
    )
    verify_reconciled_run_log_reports(
        current_body=current_run_log,
        prior_body=prior_run_log,
        pending_chain_ids={chain_id},
    )
    changed_paths = worktree_changed_paths(git, checkout)
    if not changed_paths:
        raise ContextError(
            "preserved Elim checkout is already clean and does not require archival"
        )
    history = control.setdefault("checkout_archive_history", [])
    if not isinstance(history, list):
        raise ContextError("checkout archive history is malformed")

    archived_at = datetime.now(timezone.utc).replace(microsecond=0)
    archive_root = contained_path(
        repo / ".tmp/run-coordinator/reconciled-checkouts",
        repo,
    )
    archive_root.mkdir(parents=True, exist_ok=True)
    archive_key = hashlib.sha256(
        (
            f"{chain_id}\0{checkout_head.stdout.strip()}\0"
            f"{archived_at.isoformat()}"
        ).encode("utf-8")
    ).hexdigest()
    archive_path = contained_path(
        archive_root / archive_key,
        repo,
    )
    if archive_path.exists():
        raise ContextError("reconciled checkout archive path already exists")

    record = {
        "chain_id": chain_id,
        "archived_at": archived_at.isoformat(),
        "source_head": checkout_head.stdout.strip(),
        "canonical_revision": canonical_revision.stdout.strip(),
        "archive_path": repo_relative(archive_path, repo),
        "changed_paths": sorted(changed_paths),
        "proof": (
            "Canonical origin/main contains one complete failed-run report that "
            "is absent from the preserved checkout baseline; the matching Action "
            "Item is resolved and the pending reconciliation queue is empty."
        ),
    }
    write_json(
        checkout / ".arrp-reconciled-checkout.json",
        record,
        root=checkout,
    )
    checkout.replace(archive_path)

    history.append(record)
    control["checkout_archive_history"] = history[-100:]
    if control.get("elim_thread_checkout") == configured:
        if control.get("elim_thread_id"):
            control["prior_elim_thread_id"] = control["elim_thread_id"]
        control.pop("elim_thread_id", None)
        control.pop("elim_thread_checkout", None)
    control.pop("elim_checkout_synced_head", None)
    return record


def prepare_elim_checkout(
    git: str,
    repo: Path,
    config: dict[str, Any],
    *,
    safe_prior_head: str | None = None,
    expected_revision: str | None = None,
) -> Path:
    configured = str(config["hostDispatcher"].get("isolatedCheckoutPath") or "")
    if configured != ELIM_CHECKOUT_PATH:
        raise RuntimeError("configured Elim isolated checkout path is not approved")
    checkout = contained_path(repo / ELIM_CHECKOUT_PATH, repo)
    origin = command([git, "remote", "get-url", "origin"], cwd=repo)
    origin_url = origin.stdout.strip()
    if origin.returncode != 0 or origin_url not in APPROVED_ORIGIN_URLS:
        raise RuntimeError(
            "canonical ARRP origin does not match the reviewed GitHub repository"
        )
    if not checkout.exists():
        checkout.parent.mkdir(parents=True, exist_ok=True)
        created = command(
            [
                git,
                "clone",
                "--no-tags",
                origin_url,
                str(checkout),
            ],
            cwd=repo,
        )
        if created.returncode != 0:
            raise RuntimeError(
                "could not create the permanent isolated Elim checkout: "
                + created.stderr.strip()
            )
    git_directory = checkout / ".git"
    if not git_directory.is_dir():
        raise RuntimeError(
            "reviewed Elim checkout lacks local Git metadata inside its sandbox root"
        )
    checkout_origin = command([git, "remote", "get-url", "origin"], cwd=checkout)
    if checkout_origin.returncode != 0 or checkout_origin.stdout.strip() != origin_url:
        raise RuntimeError("isolated Elim checkout origin differs from canonical origin")
    require_clean_repo(git, checkout)
    fetched = command([git, "fetch", "origin", "main"], cwd=checkout)
    if fetched.returncode != 0:
        raise RuntimeError("could not refresh origin/main in the isolated Elim checkout")
    current = command([git, "rev-parse", "HEAD"], cwd=checkout)
    remote = command(
        [git, "rev-parse", "refs/remotes/origin/main"],
        cwd=checkout,
    )
    if current.returncode != 0 or remote.returncode != 0:
        raise RuntimeError("could not verify the isolated Elim checkout baseline")
    if (
        expected_revision is not None
        and remote.stdout.strip() != expected_revision
    ):
        raise RuntimeError(
            "isolated origin/main advanced beyond the chain-manifest boundary"
        )
    if current.stdout.strip() != remote.stdout.strip():
        if (
            not isinstance(safe_prior_head, str)
            or re.fullmatch(r"[0-9a-f]{40}", safe_prior_head) is None
            or current.stdout.strip() != safe_prior_head
        ):
            raise RuntimeError(
                "isolated Elim checkout contains a prior unsynchronized baseline; "
                "preserve and reconcile it before a new run"
            )
        switched = command(
            [git, "switch", "--detach", "refs/remotes/origin/main"],
            cwd=checkout,
        )
        if switched.returncode != 0:
            raise RuntimeError(
                "could not advance the clean isolated Elim checkout to origin/main"
            )
    require_clean_repo(git, checkout)
    verified = command([git, "rev-parse", "HEAD"], cwd=checkout)
    if verified.returncode != 0 or verified.stdout.strip() != remote.stdout.strip():
        raise RuntimeError(
            "isolated Elim checkout does not match the synchronized main baseline"
        )
    return checkout


def manifest_matches_current_repo(
    git: str,
    repo: Path,
    payload: dict[str, Any],
) -> bool:
    expected = payload.get("final_revision") or payload.get("baseline_commit")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise RuntimeError("run-chain manifest does not record a valid final revision")
    remote = command([git, "rev-parse", "refs/remotes/origin/main"], cwd=repo)
    if remote.returncode != 0:
        raise RuntimeError("could not read the reviewed origin/main revision")
    return remote.stdout.strip() == expected


def trigger_chain(
    gh: str,
    repo: Path,
    repository: str,
    workflow: str,
    *,
    intake: bool,
    comprehensive: bool,
) -> int:
    if REPOSITORY_NAME.fullmatch(repository) is None:
        raise RuntimeError("configured repository name is invalid")
    if WORKFLOW_NAME.fullmatch(workflow) is None:
        raise RuntimeError("configured workflow name is invalid")
    requested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    result = command(
        [
            gh,
            "workflow",
            "run",
            workflow,
            "--repo",
            repository,
            "--ref",
            "main",
            "-f",
            f"intake_pending={str(intake).lower()}",
            "-f",
            f"force_comprehensive_review={str(comprehensive).lower()}",
        ],
        cwd=repo,
    )
    if result.returncode != 0:
        raise RuntimeError("could not dispatch the GitHub run chain: " + result.stderr.strip())
    match = RUN_URL.search(result.stdout)
    if match:
        return int(match.group(1))
    # Some GitHub CLI versions accept the dispatch but do not print its URL.
    # The coordinator's workflow-level concurrency guarantees a single active
    # chain, so the newest matching post-dispatch run is the intended run.
    for _attempt in range(10):
        listed = command(
            [
                gh,
                "run",
                "list",
                "--repo",
                repository,
                "--workflow",
                workflow,
                "--event",
                "workflow_dispatch",
                "--branch",
                "main",
                "--created",
                f">={requested_at}",
                "--limit",
                "5",
                "--json",
                "databaseId,createdAt,status,url",
            ],
            cwd=repo,
        )
        if listed.returncode == 0:
            try:
                rows = json.loads(listed.stdout)
            except json.JSONDecodeError:
                rows = []
            if isinstance(rows, list) and rows:
                rows.sort(key=lambda row: str(row.get("createdAt") or ""), reverse=True)
                run_id = rows[0].get("databaseId")
                if isinstance(run_id, int):
                    return run_id
        time.sleep(2)
    raise RuntimeError("GitHub accepted the dispatch but its run ID was not discoverable")


def wait_and_download(
    gh: str, repo: Path, repository: str, run_id: int, destination: Path
) -> Path:
    watched = command(
        [
            gh,
            "run",
            "watch",
            str(run_id),
            "--repo",
            repository,
            "--compact",
            "--exit-status",
        ],
        cwd=repo,
        capture=False,
    )
    if watched.returncode != 0:
        raise RuntimeError(f"GitHub run chain {run_id} did not complete successfully")
    destination.mkdir(parents=True, exist_ok=True)
    downloaded = command(
        [
            gh,
            "run",
            "download",
            str(run_id),
            "--repo",
            repository,
            "--name",
            "run-chain-manifest",
            "--dir",
            str(destination),
        ],
        cwd=repo,
    )
    if downloaded.returncode != 0:
        raise RuntimeError("could not download the completed run-chain manifest")
    manifest = destination / "run-chain.json"
    if not manifest.is_file():
        raise RuntimeError("completed GitHub run did not supply run-chain.json")
    return manifest


def fetch_latest_manifest(config: dict[str, Any], destination: Path) -> Path:
    branch = config["manifest"]["dataBranch"]
    path = config["manifest"]["path"]
    url = (
        f"https://raw.githubusercontent.com/{config['repository']}/{branch}/{path}"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as response:
        destination.write_bytes(response.read())
    payload = read_json(destination)
    if payload.get("schema_version") != 1:
        raise RuntimeError("latest run-chain manifest has an unsupported schema")
    return destination


def fetch_data_projection(
    config: dict[str, Any], name: str, destination: Path, expected_hash: str | None
) -> Path:
    branch = config["manifest"]["dataBranch"]
    url = f"https://raw.githubusercontent.com/{config['repository']}/{branch}/{name}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as response:
        destination.write_bytes(response.read())
    digest = "sha256:" + hashlib.sha256(destination.read_bytes()).hexdigest()
    if expected_hash and digest != expected_hash:
        raise RuntimeError(f"{name} differs from the hash recorded by the run chain")
    return destination


def materialize_verified_inputs(
    config: dict[str, Any],
    *,
    repo: Path,
    manifest_path: Path,
    queue_path: Path,
    destination: Path,
) -> dict[str, dict[str, Any]]:
    queue = read_json(queue_path, root=repo)
    inputs = queue.get("inputs") or {}
    verified: dict[str, dict[str, Any]] = {}
    filenames = {
        "integrity": "integrity.json",
        "progress": "progress.json",
        "intake": "intake.json",
        "source_checker": "source-checker.json",
        "case_monitor": "case-monitor.json",
        "presidential_directives": "presidential-directives.json",
        "recovery": "recovery.json",
        "review_epoch": "review-epoch.json",
        "chain": "chain.json",
    }
    required = {"integrity", "progress", "intake", "review_epoch", "chain"}
    for name, filename in filenames.items():
        metadata = inputs.get(name) or {}
        digest = metadata.get("sha256")
        if not isinstance(digest, str) or not digest:
            if name in required:
                raise RuntimeError(
                    f"the Elim queue did not preserve a hash for {name}"
                )
            continue
        expected = digest if digest.startswith("sha256:") else "sha256:" + digest
        target = destination / filename
        artifact = manifest_path.parent / "inputs" / filename
        if artifact.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(artifact.read_bytes())
            actual = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
            if actual != expected:
                raise RuntimeError(
                    f"preserved {name} input differs from the queue hash"
                )
        else:
            fetch_data_projection(
                config,
                f"inputs/{filename}",
                target,
                expected,
            )
        verified[name] = {
            "path": repo_relative(target, repo),
            "sha256": expected,
            "bytes": target.stat().st_size,
        }
    return verified


def copy_verified_file(
    source: Path,
    destination: Path,
    *,
    expected_hash: str | None,
    source_root: Path,
    destination_root: Path,
) -> None:
    safe_source = contained_path(source, source_root)
    safe_destination = contained_path(destination, destination_root)
    if not safe_source.is_file():
        raise RuntimeError(f"verified chain input is missing: {safe_source}")
    safe_destination.parent.mkdir(parents=True, exist_ok=True)
    safe_destination.write_bytes(safe_source.read_bytes())
    actual = "sha256:" + hashlib.sha256(safe_destination.read_bytes()).hexdigest()
    if expected_hash and actual != expected_hash:
        raise RuntimeError(
            f"mirrored chain input failed hash verification: {safe_destination.name}"
        )


def merge_recovery_inputs(
    remote_path: Path | None,
    local_path: Path,
    destination: Path,
    *,
    remote_root: Path,
    local_root: Path,
    destination_root: Path,
) -> None:
    merged: dict[str, dict[str, Any]] = {}
    for path, root in ((remote_path, remote_root), (local_path, local_root)):
        if path is None:
            continue
        value = read_json(path, {}, root=root)
        if not isinstance(value, dict):
            raise RuntimeError("Elim recovery state must be a JSON object")
        for item in value.get("items") or []:
            if not isinstance(item, dict):
                raise RuntimeError("Elim recovery state contains a non-object item")
            work_id = str(item.get("work_id") or "").strip()
            if not work_id:
                raise RuntimeError("Elim recovery state contains an item without work_id")
            merged[work_id] = dict(item)
    write_json(
        destination,
        {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "items": [merged[key] for key in sorted(merged)],
        },
        root=destination_root,
    )


def mirror_and_rebuild_chain(
    python: str,
    *,
    repo: Path,
    execution_repo: Path,
    payload: dict[str, Any],
    verified_inputs: dict[str, dict[str, Any]],
    overrides: dict[str, Any],
    local_recovery_path: Path,
    local_run_log_reconciliation_path: Path,
) -> tuple[Path, dict[str, Any], Path]:
    """Build the exact locally controlled queue/context inside Elim's sandbox."""
    chain_id = str(payload.get("chain_id") or "")
    if not SAFE_CHAIN_ID.fullmatch(chain_id):
        raise RuntimeError("chain ID is unsafe for isolated execution")
    chain_dir = contained_path(
        execution_repo / ".tmp" / "run-coordinator" / chain_id,
        execution_repo,
    )
    inputs_dir = chain_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    mirrored_inputs: dict[str, dict[str, Any]] = {}
    for name, metadata in sorted(verified_inputs.items()):
        if not isinstance(metadata, dict):
            raise RuntimeError(f"verified input metadata is invalid for {name}")
        source = contained_path(repo / str(metadata.get("path") or ""), repo)
        destination = inputs_dir / source.name
        copy_verified_file(
            source,
            destination,
            expected_hash=str(metadata.get("sha256") or "") or None,
            source_root=repo,
            destination_root=execution_repo,
        )
        mirrored_inputs[name] = {
            "path": repo_relative(destination, execution_repo),
            "sha256": metadata.get("sha256"),
            "bytes": destination.stat().st_size,
        }

    remote_recovery = (
        inputs_dir / Path(str(mirrored_inputs["recovery"]["path"])).name
        if "recovery" in mirrored_inputs
        else None
    )
    effective_recovery = inputs_dir / "recovery-effective.json"
    merge_recovery_inputs(
        remote_recovery,
        local_recovery_path,
        effective_recovery,
        remote_root=execution_repo,
        local_root=repo,
        destination_root=execution_repo,
    )
    mirrored_inputs["recovery_effective"] = {
        "path": repo_relative(effective_recovery, execution_repo),
        "sha256": "sha256:"
        + hashlib.sha256(effective_recovery.read_bytes()).hexdigest(),
        "bytes": effective_recovery.stat().st_size,
    }
    run_log_reconciliation = inputs_dir / "run-log-reconciliation.json"
    if local_run_log_reconciliation_path.is_file():
        read_pending_run_log_reconciliations(
            repo,
            local_run_log_reconciliation_path,
        )
        copy_verified_file(
            local_run_log_reconciliation_path,
            run_log_reconciliation,
            expected_hash=None,
            source_root=repo,
            destination_root=execution_repo,
        )
    else:
        write_json(
            run_log_reconciliation,
            {"schema_version": 1, "items": []},
            root=execution_repo,
        )
    mirrored_inputs["run_log_reconciliation"] = {
        "path": repo_relative(run_log_reconciliation, execution_repo),
        "sha256": "sha256:"
        + hashlib.sha256(run_log_reconciliation.read_bytes()).hexdigest(),
        "bytes": run_log_reconciliation.stat().st_size,
    }
    overrides_path = inputs_dir / "user-overrides.json"
    write_json(
        overrides_path,
        {"overrides": overrides},
        root=execution_repo,
    )
    mirrored_inputs["overrides"] = {
        "path": repo_relative(overrides_path, execution_repo),
        "sha256": "sha256:" + hashlib.sha256(overrides_path.read_bytes()).hexdigest(),
        "bytes": overrides_path.stat().st_size,
    }

    manifest_path = chain_dir / "run-chain.json"
    local_payload = json.loads(json.dumps(payload))
    local_payload["user_overrides"] = overrides
    local_payload["verified_inputs"] = mirrored_inputs
    write_json(manifest_path, local_payload, root=execution_repo)

    queue_path = chain_dir / "elim-work-queue.json"
    queue_args = [
        python,
        str(execution_repo / "scripts" / "build_elim_work_queue.py"),
        "--input-root",
        str(execution_repo),
        "--integrity",
        str(inputs_dir / "integrity.json"),
        "--progress",
        str(inputs_dir / "progress.json"),
        "--intake",
        str(inputs_dir / "intake.json"),
        "--chain",
        str(inputs_dir / "chain.json"),
        "--recovery",
        str(effective_recovery),
        "--run-log-reconciliation",
        str(run_log_reconciliation),
        "--review-epoch",
        str(inputs_dir / "review-epoch.json"),
        "--overrides",
        str(overrides_path),
    ]
    for option, filename in (
        ("--source-checker", "source-checker.json"),
        ("--case-monitor", "case-monitor.json"),
        ("--presidential-directives", "presidential-directives.json"),
    ):
        candidate = inputs_dir / filename
        if candidate.is_file():
            queue_args.extend([option, str(candidate)])
    built = command(queue_args, cwd=execution_repo)
    if built.returncode not in {0, 3}:
        raise RuntimeError(
            "could not rebuild the exact local Elim queue: " + built.stderr.strip()
        )
    try:
        queue_value = json.loads(built.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("local Elim queue builder emitted unreadable JSON") from exc
    if not isinstance(queue_value, dict):
        raise RuntimeError("local Elim queue builder emitted a non-object")
    write_json(queue_path, queue_value, root=execution_repo)

    route = command(
        [
            python,
            str(execution_repo / "scripts" / "select_elim_context_route.py"),
            "--queue",
            str(queue_path),
            "--chain",
            str(manifest_path),
        ],
        cwd=execution_repo,
    )
    if route.returncode != 0:
        raise RuntimeError(
            "could not select the locally overridden context route: "
            + route.stderr.strip()
        )
    lines = route.stdout.splitlines()
    if len(lines) < 5:
        raise RuntimeError("local context route did not preserve its exact identity")
    profile, issue_id, work_item_id, work_kind, canonical_record = lines[:5]
    context_path: Path | None = None
    if profile:
        context_path = chain_dir / "elim-context.json"
        context_args = [
            python,
            str(execution_repo / "scripts" / "build_elim_context.py"),
            "--profile",
            profile,
            "--review-epoch",
            str(inputs_dir / "review-epoch.json"),
            "--work-item-id",
            work_item_id,
            "--work-kind",
            work_kind,
            "--canonical-record",
            canonical_record,
        ]
        if issue_id:
            context_args.extend(["--issue", issue_id])
        context = command(context_args, cwd=execution_repo)
        if context.returncode != 0:
            raise RuntimeError(
                "could not rebuild the selected Elim context packet: "
                + context.stderr.strip()
            )
        try:
            context_value = json.loads(context.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "local Elim context builder emitted unreadable JSON"
            ) from exc
        if not isinstance(context_value, dict):
            raise RuntimeError("local Elim context builder emitted a non-object")
        write_json(context_path, context_value, root=execution_repo)

    attach_args = [
        python,
        str(execution_repo / "scripts" / "run_coordinator.py"),
        "attach-context",
        "--config",
        str(execution_repo / ".github" / "run-coordinator-bot.json"),
        "--manifest",
        str(manifest_path),
        "--queue",
        str(queue_path),
    ]
    if context_path is not None:
        attach_args.extend(["--context", str(context_path)])
    attached = command(attach_args, cwd=execution_repo)
    if attached.returncode != 0:
        raise RuntimeError(
            "could not bind the rebuilt queue/context to the chain manifest: "
            + attached.stderr.strip()
        )
    local_payload = read_json(manifest_path, root=execution_repo)
    local_payload["user_overrides"] = overrides
    local_payload["verified_inputs"] = mirrored_inputs
    local_payload["work_queue"]["local_path"] = repo_relative(
        queue_path, execution_repo
    )
    if local_payload.get("context_packet") is not None and context_path is not None:
        local_payload["context_packet"]["local_path"] = repo_relative(
            context_path, execution_repo
        )
    write_json(manifest_path, local_payload, root=execution_repo)
    return manifest_path, local_payload, chain_dir


def managed_usage_baseline_path(repo: Path, invocation_id: str) -> Path:
    if SAFE_CHAIN_ID.fullmatch(invocation_id) is None:
        raise ContextError("usage baseline received an unsafe invocation ID")
    digest = hashlib.sha256(invocation_id.encode("utf-8")).hexdigest()
    return contained_path(
        repo / USAGE_BASELINE_DIRECTORY / f"{digest}.json",
        repo,
    )


def usage_gate(
    python: str,
    repo: Path,
    config: dict[str, Any],
    baseline_id: str,
) -> dict[str, Any]:
    result = command(
        [
            python,
            str(repo / "scripts" / "check_codex_usage_reserve.py"),
            "--reserve-percent",
            str(config["usage"]["hardReservePercent"]),
            "--soft-target-percent",
            str(config["usage"]["softRunTargetPercent"]),
            "--run-baseline-id",
            baseline_id,
        ],
        cwd=repo,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Codex usage gate returned unreadable output") from exc
    if result.returncode not in {0, 2, 3}:
        raise RuntimeError("Codex usage gate exited unexpectedly")
    return payload


def repo_relative(path: Path, repo: Path) -> str:
    return contained_path(path, repo).relative_to(repo.resolve()).as_posix()


def write_usage_attestation(
    path: Path,
    *,
    repo: Path,
    chain_id: str,
    invocation_id: str,
    baseline_path: Path,
    gate: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    run_budget = gate.get("runBudget") or {}
    soft_target_reached = run_budget.get("softTargetReached") is True
    stop_requested = gate.get("status") != "pass"
    if stop_requested:
        new_unit_policy = "no"
        directive = (
            "Finish only the already-started atomic operation, validate and preserve "
            "it, begin no new substantive unit, and close out."
        )
    elif soft_target_reached:
        new_unit_policy = "one-high-value-bounded-unit-after-recheck"
        directive = (
            "Close out after the current major unit unless the runbook's single "
            "high-value bounded-unit exception is deliberately selected and the "
            "official snapshot is rechecked before and after it."
        )
    else:
        new_unit_policy = "yes"
        directive = "Continue only through the next runbook usage checkpoint."
    value = {
        "schema_version": 1,
        "chain_id": chain_id,
        "invocation_id": invocation_id,
        "source": "approved-host-dispatcher",
        "checked_at": gate.get("checkedAtUtc"),
        "status": gate.get("status", "unavailable"),
        "lowest_remaining_percent": gate.get("lowestRemainingPercent"),
        "reserve_percent": config["usage"]["hardReservePercent"],
        "soft_run_target_percent": config["usage"]["softRunTargetPercent"],
        "monitor_interval_seconds": config["usage"]["monitorIntervalSeconds"],
        "snapshot_max_age_seconds": config["usage"]["snapshotMaxAgeSeconds"],
        "baseline_path": repo_relative(baseline_path, repo),
        "stop_requested": stop_requested,
        "soft_closeout_recommended": soft_target_reached,
        "new_substantive_unit_policy": new_unit_policy,
        "host_directive": directive,
        "gate": gate,
    }
    write_json(path, value, root=repo)
    return value


def refinalize(
    python: str,
    repo: Path,
    config_path: Path,
    manifest: Path,
    remaining: float,
) -> dict[str, Any]:
    empty = manifest.parent / "completed-stage-results.json"
    empty.write_text("{}\n", encoding="utf-8")
    result = command(
        [
            python,
            str(repo / "scripts" / "run_coordinator.py"),
            "finalize",
            "--config",
            str(config_path),
            "--manifest",
            str(manifest),
            "--stage-results",
            str(empty),
            "--usage-remaining",
            str(remaining),
        ],
        cwd=repo,
    )
    if result.returncode != 0:
        raise RuntimeError("could not apply the host-side usage decision")
    return read_json(manifest, root=repo)


def elim_prompt(manifest: Path, payload: dict[str, Any]) -> str:
    profile = payload["elim_decision"]["profile"]
    monitor = (payload.get("usage") or {}).get("host_monitor") or {}
    context_packet = (payload.get("context_packet") or {}).get("local_path")
    selected = (payload.get("work_queue") or {}).get("next_item") or {}
    selected_source = selected.get("source") or {}
    selected_canonical = (
        (payload.get("context_packet") or {}).get("canonical_record")
        or selected_source.get("canonicalRecord")
        or selected_source.get("canonical_record")
    )
    selected_issue = (payload.get("context_packet") or {}).get("issue_id")
    if selected_source.get("input") == "run_log_reconciliation":
        pending_chain_ids = selected_source.get("pending_chain_ids") or []
        mode = (
            "Process only the selected safety-class-0 Elim Run Log reconciliation "
            "unit. Use its bounded preserved artifact references to reconstruct a "
            "truthful complete report for every listed prior Chain ID "
            f"({', '.join(str(value) for value in pending_chain_ids)}), plus the "
            "current Chain ID. Do not invent actions or findings; if the preserved "
            "evidence is insufficient, route the ambiguity and leave the pending "
            "record unresolved. A completed repair must newly commit and synchronize "
            "all listed prior reports to origin/main before they can be cleared. "
            "Do not begin a due comprehensive review or any other work; the Review "
            "Epoch remains due for a later clean chain."
        )
    elif selected.get("kind") == "bot_failure" and selected.get("safety_class") == 0:
        mode = (
            "Process only the selected safety-class-0 bot-failure repair unit. "
            "Do not begin a due comprehensive review or any other work; the Review "
            "Epoch remains due for a later clean chain."
        )
    elif profile["full_context"]:
        mode = (
            "Conduct the due comprehensive full-context review and establish the "
            "next review epoch."
        )
    else:
        mode = (
            "Process the highest-priority eligible work unit from the refreshed "
            "chain queue."
        )
    return (
        "You are Elim, the ARRP LLM agent. Follow the authoritative Elim runbook and all "
        "governing project rules. The deterministic run chain completed and its manifest is "
        f"at {manifest}. {mode} Verify the manifest and bot outputs before substantive work; "
        "the manifest's verified_inputs map identifies locally preserved, hash-checked copies "
        "of every deterministic input used to build the queue. "
        "This verified manifest and packet define the sole active unit. Earlier messages "
        "in this persistent task are historical context only: they provide no current "
        "authority or freshness and must not be reprocessed unless the current verified "
        "inputs select them. "
        "Bot failures or stale data take priority. Record ordinary issue/audit work in its "
        "canonical location and record this run in Elim's run log. Respect the 15 percent hard "
        "reserve and ten-point soft run target. The approved host dispatcher, not the Elim "
        "sandbox, owns the official usage probe. Do not launch a second Codex app-server. "
        f"Read the host-attested usage snapshot at {monitor.get('status_path')} before "
        "substantive work, before and after every major unit, between T-audit tiers, and before "
        "closeout. Fail closed if its status is not pass or if it is older than "
        f"{monitor.get('snapshot_max_age_seconds')} seconds. "
        "Treat the host attestation's stop_requested, soft_closeout_recommended, "
        "new_substantive_unit_policy, and host_directive fields as the cooperative "
        "host stop signal. The host will not hard-kill an atomic operation, but a "
        "stop request forbids starting another substantive unit. "
        "The required structured result represents exactly the one manifest-selected "
        f"unit: run_id={payload.get('chain_id')!r}, unit_id={selected.get('id')!r}, "
        f"work_type={selected.get('kind')!r}, issue_id={selected_issue!r}, and "
        f"canonical_record={selected_canonical!r}. Do not report a different or "
        "additional queue item in that result; consecutive audit tiers for the same "
        "selected issue remain one selected unit and retain their detailed canonical "
        "audit records. The trusted host dispatcher—not this workspace-write sandbox—"
        "owns repository Git staging, branch creation, commit, push, pull-request "
        "creation, and synchronization readback. Do not run repository Git mutations "
        "or GitHub branch or pull-request mutations. Authorized GitHub Issue, Project, "
        "Discussion, and other semantic operations remain governed by the selected "
        "work unit and must be validated and reported normally. Leave commit null, "
        "leave synchronization empty, and list every changed working-tree file exactly "
        "once in files_touched. The host will reject any undeclared or missing path, "
        "validate the complete run report and continuation state, stage only that exact "
        "file set, and use a non-forced compare-and-swap publication. "
        "For human_review, the host pushes a bounded branch and opens but does not merge "
        "its pull request. Every cooperative terminal launched outcome—including "
        "completed, clean, human-review, blocked, failed, and usage-stopped—must leave "
        "one complete current ELIM_RUN_LOG report in the working tree for host closeout. "
        "For a completed public-intake assessment, "
        "validate the structured result and run scripts/record_intake_review.py against the "
        "pinned work queue before the final commit so the submission is not reviewed again. "
        "For a completed comprehensive review, prepare the complete Review Epoch record and run "
        "scripts/record_review_epoch.py before the final commit, passing the reviewed packet with "
        f"--context-packet {context_packet}; set triggering_run_id to the current chain ID "
        f"{payload.get('chain_id')}."
    )


def monitored_usage_probe(
    probe: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    try:
        return probe()
    except (OSError, RuntimeError, ValueError) as exc:
        return {
            "status": "unavailable",
            "checkedAtUtc": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "error": str(exc),
        }


def thread_id_from_jsonl(path: Path) -> str | None:
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        candidate = (
            event.get("thread_id")
            or event.get("threadId")
            or event.get("session_id")
        )
        if event.get("type") in {"thread.started", "session.started"} and isinstance(
            candidate, str
        ) and THREAD_ID.fullmatch(candidate):
            return candidate
    return None


def validate_elim_launch_containment(
    execution_repo: Path,
    *,
    manifest: Path,
    payload: dict[str, Any],
    usage_status_path: Path,
    output_path: Path,
    last_message_path: Path,
) -> None:
    candidates = [
        manifest,
        usage_status_path,
        output_path,
        last_message_path,
        execution_repo
        / "framework"
        / "agents"
        / "elim-work-unit-result.schema.json",
    ]
    for section, key in (
        (payload.get("work_queue") or {}, "local_path"),
        (payload.get("context_packet") or {}, "local_path"),
    ):
        value = section.get(key) if isinstance(section, dict) else None
        if value:
            candidates.append(execution_repo / str(value))
    for metadata in (payload.get("verified_inputs") or {}).values():
        if isinstance(metadata, dict) and metadata.get("path"):
            candidates.append(execution_repo / str(metadata["path"]))
    for candidate in candidates:
        contained_path(Path(candidate), execution_repo)


def terminate_process_group(
    process: subprocess.Popen[str],
    *,
    timeout_seconds: float = 10.0,
) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            process.wait()
        return
    try:
        process.wait(timeout=timeout_seconds)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        process.wait()
        return
    process.wait()


def launch_elim(
    codex: str,
    repo: Path,
    execution_repo: Path,
    manifest: Path,
    payload: dict[str, Any],
    state_dir: Path,
    usage_probe: Callable[[], dict[str, Any]],
    usage_status_path: Path,
    usage_attestation_args: dict[str, Any],
    monitor_interval_seconds: int,
    dispatcher_lock: DispatchLease,
    existing_thread_id: str | None = None,
    control_path: Path | None = None,
    control_repo: Path | None = None,
    launch_state: dict[str, Any] | None = None,
) -> tuple[int, str | None, dict[str, Any]]:
    profile = payload["elim_decision"]["profile"]
    chain_id = payload["chain_id"]
    output = state_dir / f"elim-{chain_id}.jsonl"
    last = state_dir / f"elim-{chain_id}-last-message.txt"
    if launch_state is not None:
        launch_state.clear()
        launch_state.update(
            {
                "spawned": False,
                "run_log_verified": False,
                "execution_checkout": repo_relative(execution_repo, repo),
                "artifacts": {
                    "output": repo_relative(output, execution_repo),
                    "last_message": repo_relative(last, execution_repo),
                    "usage_status": repo_relative(
                        usage_status_path,
                        execution_repo,
                    ),
                    "current_audit": CURRENT_AUDIT_LOG,
                },
            }
        )
    validate_elim_launch_containment(
        execution_repo,
        manifest=manifest,
        payload=payload,
        usage_status_path=usage_status_path,
        output_path=output,
        last_message_path=last,
    )
    common = [
        "--json",
        "--model",
        profile["model"],
        "-c",
        f'model_reasoning_effort="{profile["reasoning_effort"]}"',
        "--output-schema",
        str(
            execution_repo
            / "framework"
            / "agents"
            / "elim-work-unit-result.schema.json"
        ),
        "--output-last-message",
        str(last),
    ]
    if existing_thread_id:
        if not THREAD_ID.fullmatch(existing_thread_id):
            raise RuntimeError("stored Elim task identifier is invalid")
        argv = [codex, "exec", "resume", *common, existing_thread_id, "-"]
    else:
        argv = [
            codex,
            "exec",
            *common,
            "--cd",
            str(execution_repo),
            "--sandbox",
            "workspace-write",
            "-",
        ]
    process: subprocess.Popen[str] | None = None
    try:
        with output.open("w", encoding="utf-8") as handle:
            if control_path is not None:
                if control_repo is None:
                    raise RuntimeError(
                        "final control-state launch guard lacks its repository root"
                    )
                safe_control = contained_path(control_path, control_repo)
                control_lock = contained_path(
                    safe_control.with_suffix(".lock"),
                    control_repo,
                )
                descriptor = os.open(
                    control_lock,
                    os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                )
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX)
                    latest_control = read_json(
                        safe_control,
                        {},
                        root=control_repo,
                    )
                    if not isinstance(latest_control, dict):
                        raise RuntimeError(
                            "coordinator control state is malformed"
                        )
                    if not control_overrides_match_selection(
                        latest_control,
                        payload,
                    ):
                        raise ControlSelectionChanged(
                            "coordinator controls changed after exact queue selection"
                        )
                    process = subprocess.Popen(
                        argv,
                        cwd=execution_repo,
                        stdin=subprocess.PIPE,
                        text=True,
                        stdout=handle,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                    if launch_state is not None:
                        launch_state.update(
                            {
                                "spawned": True,
                                "spawned_at": datetime.now(timezone.utc)
                                .replace(microsecond=0)
                                .isoformat(),
                            }
                        )
                finally:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                    os.close(descriptor)
            else:
                process = subprocess.Popen(
                    argv,
                    cwd=execution_repo,
                    stdin=subprocess.PIPE,
                    text=True,
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                if launch_state is not None:
                    launch_state.update(
                        {
                            "spawned": True,
                            "spawned_at": datetime.now(timezone.utc)
                            .replace(microsecond=0)
                            .isoformat(),
                        }
                    )
            write_dispatch_lock_owner(
                dispatcher_lock,
                updates={
                    "status": "elim-running",
                    "chain_id": chain_id,
                    "child_pid": process.pid,
                    "output_path": repo_relative(output, repo),
                    "last_message_path": repo_relative(last, repo),
                    "elim_thread_id": existing_thread_id,
                    "execution_checkout": repo_relative(execution_repo, repo),
                },
            )
            if process.stdin is None:
                terminate_process_group(process)
                raise RuntimeError("Elim process did not expose its prompt input")
            try:
                process.stdin.write(elim_prompt(manifest, payload))
                process.stdin.close()
            except BrokenPipeError:
                process.wait()
            last_gate = read_json(usage_status_path, {}, root=repo).get("gate") or {}
            next_probe = time.monotonic() + monitor_interval_seconds
            while process.poll() is None:
                now_monotonic = time.monotonic()
                if now_monotonic >= next_probe:
                    gate = monitored_usage_probe(usage_probe)
                    last_gate = gate
                    usage_state = write_usage_attestation(
                        usage_status_path,
                        gate=gate,
                        **usage_attestation_args,
                    )
                    write_dispatch_lock_owner(
                        dispatcher_lock,
                        updates={
                            "status": (
                                "elim-stop-requested"
                                if usage_state["stop_requested"]
                                else "elim-soft-closeout"
                                if usage_state["soft_closeout_recommended"]
                                else "elim-running"
                            ),
                            "elim_thread_id": (
                                thread_id_from_jsonl(output) or existing_thread_id
                            ),
                            "usage_status_path": repo_relative(
                                usage_status_path, repo
                            ),
                        },
                    )
                    next_probe = time.monotonic() + monitor_interval_seconds
                time.sleep(min(1, max(0.1, next_probe - time.monotonic())))
            return_code = int(process.returncode or 0)
            final_gate = monitored_usage_probe(usage_probe)
            last_gate = final_gate
            write_usage_attestation(
                usage_status_path,
                gate=final_gate,
                **usage_attestation_args,
            )
            write_dispatch_lock_owner(
                dispatcher_lock,
                updates={
                    "status": "elim-closeout",
                    "elim_thread_id": (
                        thread_id_from_jsonl(output) or existing_thread_id
                    ),
                    "usage_status_path": repo_relative(usage_status_path, repo),
                },
            )
    except ControlSelectionChanged:
        raise
    except BaseException:
        if process is not None:
            terminate_process_group(process)
        try:
            write_dispatch_lock_owner(
                dispatcher_lock,
                updates={
                    "status": "elim-interrupted",
                    "child_pid": None,
                    "elim_thread_id": (
                        thread_id_from_jsonl(output) or existing_thread_id
                    ),
                    "output_path": repo_relative(output, repo),
                    "last_message_path": repo_relative(last, repo),
                },
            )
        except Exception:
            # Preserve the original post-spawn exception after the child has
            # been stopped and reaped; the outer dispatcher records it.
            pass
        raise
    return (
        return_code,
        thread_id_from_jsonl(output) or existing_thread_id,
        last_gate,
    )


def enforce_usage_monitor_closeout(outcome: int, gate: dict[str, Any]) -> int:
    if outcome == 0 and gate.get("status") != "pass":
        return 5
    return outcome


def enforce_trigger_launch_boundary(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("llm_launch_allowed") is True:
        return payload
    payload["elim_decision"]["launch_recommended"] = False
    payload["elim_decision"]["reason"] = (
        "Host dispatcher rejected an LLM launch from a deterministic-only "
        "or unspecified trigger."
    )
    payload["next_action"] = (
        "No Elim launch; wait for the daily schedule, an eligible event, "
        "or explicit manual dispatch."
    )
    return payload


def comprehensive_epoch_recorded(
    repo: Path,
    chain_id: str,
    context_packet_path: Path | None,
) -> bool:
    ledger = repo / "research" / "review-epochs.jsonl"
    if not ledger.is_file() or context_packet_path is None:
        return False
    try:
        rows = [
            line
            for line in ledger.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not rows:
            return False
        persisted = json.loads(rows[-1])
        if not isinstance(persisted, dict):
            return False
        if persisted.get("schema_version") != 1:
            return False
        if persisted.get("triggering_run_id") != chain_id:
            return False
        recorded_digest = persisted.get("record_sha256")
        if not isinstance(recorded_digest, str) or not recorded_digest.startswith(
            "sha256:"
        ):
            return False
        unsigned = {
            key: value
            for key, value in persisted.items()
            if key != "record_sha256"
        }
        actual_digest = "sha256:" + hashlib.sha256(
            json.dumps(
                unsigned,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        if not secrets.compare_digest(recorded_digest, actual_digest):
            return False
        recorder_input = {
            key: value
            for key, value in unsigned.items()
            if key != "schema_version"
        }
        packet_path = contained_path(context_packet_path, repo)
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        validate_review_epoch(
            recorder_input,
            manifest_path=repo / "framework" / "context-routes.json",
            context_packet=packet,
            root=repo,
        )
        prior = json.loads(rows[-2]) if len(rows) > 1 else None
        validate_finding_continuity(prior, recorder_input)
    except (
        ContextError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return False
    return True


def record_elim_runtime(
    *,
    repo: Path,
    config: dict[str, Any],
    control: dict[str, Any],
    payload: dict[str, Any],
    outcome: int,
    result_outcome: str | None = None,
    details: str | None = None,
) -> None:
    completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    status = {
        "completed": "completed",
        "clean": "completed",
        "human_review": "human-review",
        "usage_stopped": "usage-stopped",
        "blocked": "blocked",
        "failed": "failed",
    }.get(str(result_outcome or ""), "completed" if outcome == 0 else "failed")
    runtime_details = details
    if not runtime_details:
        runtime_details = {
            "completed": (
                "Elim completed and the dispatcher verified its required closeout."
            ),
            "usage-stopped": (
                "Elim safely stopped at the usage boundary and preserved its continuation."
            ),
            "blocked": "Elim preserved a blocked continuation.",
            "human-review": (
                "Elim routed a human-review result on an unmerged pull request."
            ),
        }.get(
            status,
            control.get("last_failed_reason")
            or f"Elim exited with code {outcome}; inspect the Elim Run Log.",
        )
    runtime = {
        "id": "elim",
        "name": "Elim",
        "status": status,
        "chain_id": payload.get("chain_id"),
        "completed_at": completed_at,
        "exit_code": outcome,
        "details": runtime_details,
    }
    control["elim_runtime"] = runtime
    payload["elim_runtime"] = runtime
    payload["host_status"] = status
    payload["host_updated_at"] = completed_at
    write_json(
        repo / config["manifest"]["localFallback"],
        payload,
        root=repo,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trigger-chain", action="store_true")
    parser.add_argument("--launch-codex", action="store_true")
    parser.add_argument(
        "--recover-stale-lock-only",
        action="store_true",
        help=(
            "Recover and report only a provably abandoned dispatcher lock; "
            "do not fetch, synchronize, trigger a chain, or launch Codex."
        ),
    )
    parser.add_argument(
        "--archive-reconciled-checkout",
        metavar="CHAIN_ID",
        help=(
            "After independent reconciliation proof, preserve the dirty isolated "
            "checkout under the private archive tree and release its fixed path; "
            "do not trigger a chain or launch Codex."
        ),
    )
    args = parser.parse_args()
    if args.archive_reconciled_checkout and (
        args.trigger_chain or args.launch_codex or args.recover_stale_lock_only
    ):
        parser.error(
            "--archive-reconciled-checkout cannot be combined with run or lock modes"
        )
    repo = ROOT
    config: dict[str, Any] = {}
    control: dict[str, Any] = {}
    dispatch_lease: DispatchLease | None = None
    bootstrap_stage = "dispatcher-config"
    try:
        config = read_json(CONFIG)
        if not isinstance(config, dict):
            raise RuntimeError("reviewed dispatcher config is not a JSON object")
        validate_host_closeout_policy(config)
        host = config["hostDispatcher"]
        configured_repo = Path(host["repositoryPath"])
        if configured_repo != ROOT or not configured_repo.is_dir():
            raise RuntimeError(
                "configured ARRP repository path is unavailable: "
                f"{configured_repo}"
            )
        repo = configured_repo
        bootstrap_stage = "dispatcher-executables"
        python = executable(config, "pythonPath")
        git = executable(config, "gitPath")
        gh = executable(config, "githubCliPath")
        codex = executable(config, "codexPath")
        configured_state = str(host["stateDirectory"])
        if configured_state != ".tmp/run-coordinator":
            raise RuntimeError(
                "configured dispatcher state directory is not approved"
            )
        bootstrap_stage = "dispatcher-state"
        state_dir = contained_path(repo / configured_state, repo)
        state_dir.mkdir(parents=True, exist_ok=True)
        control_path = state_dir / "control.json"
        control = read_json(
            control_path,
            {"requests": [], "overrides": {}},
        )
        if not isinstance(control, dict):
            raise RuntimeError("dispatcher control state is not a JSON object")
        lock = state_dir / "host-dispatch.lock"
        bootstrap_stage = "dispatcher-lock"
        _, dispatch_lease = acquire_dispatch_lock(
            lock,
            repo=repo,
            config=config,
            control=control,
        )
        persist_control_state(control_path, control, repo=repo)
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        if dispatch_lease is not None:
            release_dispatch_lock(dispatch_lease)
        message = f"{bootstrap_stage} failed: {exc}"
        record_bootstrap_failure_best_effort(
            ROOT,
            stage=bootstrap_stage,
            message=message,
        )
        print(f"run-chain-dispatcher: {message}", file=sys.stderr)
        return 1
    assert dispatch_lease is not None
    prior_sigterm_handler = signal.getsignal(signal.SIGTERM)

    def interrupt_dispatch(_signum: int, _frame: Any) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupt_dispatch)
    if args.recover_stale_lock_only:
        signal.signal(signal.SIGTERM, prior_sigterm_handler)
        release_dispatch_lock(dispatch_lease)
        return 0
    payload: dict[str, Any] = {}
    invocation_id = ""
    launch_state: dict[str, Any] = {
        "spawned": False,
        "run_log_verified": False,
    }
    current_stage = "host-repository-preflight"
    try:
        origin_revision, workspace_commit = verify_canonical_runtime_boundary(
            git,
            repo,
        )
        if workspace_commit is not None:
            print(
                "Committed and synchronized canonical workspace changes as "
                f"{workspace_commit}. Automated dispatch is deferred until the "
                "next host poll so the reviewed runtime is reloaded."
            )
            return 0
        if args.archive_reconciled_checkout:
            current_stage = "reconciled-checkout-archive"
            record = archive_reconciled_elim_checkout(
                git,
                repo,
                config,
                control,
                chain_id=args.archive_reconciled_checkout,
            )
            persist_control_state(control_path, control, repo=repo)
            print(
                "Archived reconciled Elim checkout at "
                f"{record['archive_path']} after canonical proof."
            )
            return 0
        requested = control.get("requested_run")
        comprehensive = control.get("requested_comprehensive_review")
        current_stage = "chain-manifest"
        if args.trigger_chain or requested or comprehensive:
            run_id = trigger_chain(
                gh,
                repo,
                config["repository"],
                host["workflow"],
                intake=bool(requested and requested.get("intake_pending")),
                comprehensive=bool(comprehensive),
            )
            manifest = wait_and_download(
                gh, repo, config["repository"], run_id, state_dir / str(run_id)
            )
        else:
            manifest = fetch_latest_manifest(config, state_dir / "latest-run-chain.json")
        payload = read_json(manifest)
        payload["user_overrides"] = control.get("overrides", {})
        if not manifest_matches_current_repo(git, repo, payload):
            print(
                "Latest run-chain manifest does not match reviewed origin/main; "
                "waiting for the matching GitHub chain."
            )
            return 0
        if control.get("last_consumed_chain_id") == payload.get("chain_id"):
            return 0
        if (
            control.get("last_failed_chain_id") == payload.get("chain_id")
            and not requested
            and not comprehensive
        ):
            return 0
        current_stage = "context-gateway-inputs"
        if payload.get("work_queue"):
            queue_path = fetch_data_projection(
                config,
                "elim-work-queue.json",
                state_dir / payload["chain_id"] / "elim-work-queue.json",
                payload["work_queue"].get("sha256"),
            )
            payload["work_queue"]["local_path"] = str(queue_path)
            payload["verified_inputs"] = materialize_verified_inputs(
                config,
                repo=repo,
                manifest_path=manifest,
                queue_path=queue_path,
                destination=state_dir / payload["chain_id"] / "inputs",
            )
        else:
            raise RuntimeError("current Chain Manifest has no Elim work queue")
        current_stage = "elim-isolated-checkout"
        execution_repo = prepare_elim_checkout(
            git,
            repo,
            config,
            safe_prior_head=control.get("elim_checkout_synced_head"),
            expected_revision=origin_revision,
        )
        execution_checkout = repo_relative(execution_repo, repo)
        current_stage = "local-queue-context-rebuild"
        manifest, payload, execution_state_dir = mirror_and_rebuild_chain(
            python,
            repo=repo,
            execution_repo=execution_repo,
            payload=payload,
            verified_inputs=payload["verified_inputs"],
            overrides=control.get("overrides", {}),
            local_recovery_path=repo / ELIM_RECOVERY_STATE,
            local_run_log_reconciliation_path=(
                repo / ELIM_RUN_LOG_RECONCILIATION_STATE
            ),
        )
        if alert_failures(config, control, payload, repo):
            persist_control_state(control_path, control, repo=repo)
        invocation_id = (
            payload["chain_id"]
            + "-"
            + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        )
        baseline_path = managed_usage_baseline_path(
            execution_repo,
            invocation_id,
        )
        usage_status_path = (
            execution_state_dir / f"usage-status-{invocation_id}.json"
        )
        attestation_args = {
            "repo": execution_repo,
            "chain_id": payload["chain_id"],
            "invocation_id": invocation_id,
            "baseline_path": baseline_path,
            "config": config,
        }
        current_stage = "usage-gate"
        gate = usage_gate(python, execution_repo, config, invocation_id)
        attestation = write_usage_attestation(
            usage_status_path,
            gate=gate,
            **attestation_args,
        )
        write_dispatch_lock_owner(
            dispatch_lease,
            updates={
                "chain_id": payload["chain_id"],
                "invocation_id": invocation_id,
                "status": "usage-gated",
                "usage_status_path": repo_relative(usage_status_path, repo),
            },
        )
        payload.setdefault("usage", {}).update(
            {
                "status": gate.get("status", "unavailable"),
                "remaining_percent": gate.get("lowestRemainingPercent"),
                "gate": gate,
                "host_monitor": {
                    "source": attestation["source"],
                    "status_path": repo_relative(
                        usage_status_path, execution_repo
                    ),
                    "baseline_path": attestation["baseline_path"],
                    "monitor_interval_seconds": attestation[
                        "monitor_interval_seconds"
                    ],
                    "snapshot_max_age_seconds": attestation[
                        "snapshot_max_age_seconds"
                    ],
                },
            }
        )
        write_json(manifest, payload, root=execution_repo)
        if gate.get("status") != "pass":
            blockers = "; ".join(str(item) for item in gate.get("blockers") or [])
            message = (
                f"Codex usage gate returned {gate.get('status')!r}"
                + (f": {blockers}" if blockers else "")
            )
            record_terminal_failure(
                config,
                control,
                repo,
                stage="usage-gate",
                message=message,
                exit_code=5,
                next_action=(
                    "Wait for an applicable usage window to recover or restore a "
                    "complete official usage reading, then launch a fresh current chain."
                ),
                payload=payload,
                chain_id=payload.get("chain_id"),
                control_path=control_path,
            )
            return 5
        current_stage = "host-refinalization"
        payload = refinalize(
            python,
            execution_repo,
            execution_repo / ".github" / "run-coordinator-bot.json",
            manifest,
            float(gate["lowestRemainingPercent"]),
        )
        payload = enforce_trigger_launch_boundary(payload)
        payload["host_action_items"] = list(control.get("action_items") or [])
        write_json(manifest, payload, root=execution_repo)
        write_json(
            repo / config["manifest"]["localFallback"],
            payload,
            root=repo,
        )
        if not payload["elim_decision"]["launch_recommended"]:
            control["last_consumed_chain_id"] = payload["chain_id"]
            control["last_consumed_at"] = payload["updated_at"]
            control.pop("requested_run", None)
            control.pop("requested_comprehensive_review", None)
            consumed = {
                key: str(value.get("request_id"))
                for key, value in (
                    ("requested_run", requested),
                    ("requested_comprehensive_review", comprehensive),
                )
                if isinstance(value, dict) and value.get("request_id")
            }
            persist_control_state(
                control_path,
                control,
                repo=repo,
                consumed_requests=consumed,
            )
            append_host_outcome_history(
                config,
                repo,
                chain_id=payload["chain_id"],
                status="not-launched",
                stage="host-refinalization",
                exit_code=0,
                payload=payload,
            )
            return 0
        if not args.launch_codex:
            print(
                "Elim launch is recommended, but --launch-codex was not supplied; no LLM was invoked."
            )
            append_host_outcome_history(
                config,
                repo,
                chain_id=payload["chain_id"],
                status="launch-deferred",
                stage="elim-launch-boundary",
                exit_code=0,
                payload=payload,
            )
            return 0
        latest_control = read_control_state_locked(control_path, repo=repo)
        if not control_overrides_match_selection(latest_control, payload):
            control.clear()
            control.update(latest_control)
            print(
                "Coordinator controls changed after exact queue selection; "
                "Elim launch deferred for a fresh queue/context evaluation."
            )
            append_host_outcome_history(
                config,
                repo,
                chain_id=payload["chain_id"],
                status="launch-deferred",
                stage="post-selection-control-check",
                exit_code=0,
                payload=payload,
            )
            return 0
        control.clear()
        control.update(latest_control)
        existing_thread_id = (
            control.get("elim_thread_id")
            if control.get("elim_thread_checkout") == execution_checkout
            else None
        )
        if control.get("elim_thread_id") and existing_thread_id is None:
            control["prior_elim_thread_id"] = control["elim_thread_id"]
            control.pop("elim_thread_id", None)
        current_stage = "elim-execution"
        try:
            outcome, elim_thread_id, final_gate = launch_elim(
                codex,
                repo,
                execution_repo,
                manifest,
                payload,
                execution_state_dir,
                usage_probe=lambda: usage_gate(
                    python,
                    execution_repo,
                    config,
                    invocation_id,
                ),
                usage_status_path=usage_status_path,
                usage_attestation_args=attestation_args,
                monitor_interval_seconds=int(
                    config["usage"]["monitorIntervalSeconds"]
                ),
                dispatcher_lock=dispatch_lease,
                existing_thread_id=existing_thread_id,
                control_path=control_path,
                control_repo=repo,
                launch_state=launch_state,
            )
        except ControlSelectionChanged:
            print(
                "Coordinator controls changed at the exact launch boundary; "
                "Elim was not started and a fresh queue/context evaluation is required."
            )
            append_host_outcome_history(
                config,
                repo,
                chain_id=payload["chain_id"],
                status="launch-deferred",
                stage="post-selection-control-check",
                exit_code=0,
                payload=payload,
            )
            return 0
        outcome = enforce_usage_monitor_closeout(outcome, final_gate)
        payload.setdefault("usage", {}).update(
            {
                "status": final_gate.get("status", "unavailable"),
                "remaining_percent": final_gate.get("lowestRemainingPercent"),
                "gate": final_gate,
            }
        )
        write_json(manifest, payload, root=execution_repo)
        write_json(
            repo / config["manifest"]["localFallback"],
            payload,
            root=repo,
        )
        if elim_thread_id:
            control["elim_thread_id"] = elim_thread_id
            control["elim_thread_checkout"] = execution_checkout
        result_path = (
            execution_state_dir
            / f"elim-{payload['chain_id']}-last-message.txt"
        )
        if result_path.is_file():
            current_stage = "elim-host-git-closeout"
            preserved_result = host_preserve_elim_result(
                git=git,
                gh=gh,
                repo=execution_repo,
                result_path=result_path,
                expected_manifest=payload,
                repository=config["repository"],
            )
            payload["host_closeout"] = {
                "outcome": preserved_result["outcome"],
                "commit": preserved_result["commit"],
                "synchronization": preserved_result["synchronization"],
                "validated_at": datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat(),
            }
            write_json(manifest, payload, root=execution_repo)
            write_json(
                repo / config["manifest"]["localFallback"],
                payload,
                root=repo,
            )
        current_stage = "elim-closeout"
        closeout_accounting: dict[str, Any] = {}
        outcome, semantic_closeout_complete, closeout_failure_reason = (
            enforce_elim_result_closeout(
                outcome,
                repo=repo,
                result_path=result_path,
                git=git,
                gh=gh,
                expected_manifest=payload,
                execution_repo=execution_repo,
                accounting=closeout_accounting,
            )
        )
        result_outcome = str(closeout_accounting.get("result_outcome") or "")
        launch_state["run_log_verified"] = bool(
            closeout_accounting.get("run_log_verified")
        )
        write_dispatch_lock_owner(
            dispatch_lease,
            updates={
                "status": "elim-closeout",
                "run_log_verified": launch_state["run_log_verified"],
            },
        )
        validated_result: dict[str, Any] | None = None
        if semantic_closeout_complete:
            validated_result = read_elim_result(result_path, execution_repo)
            persist_validated_recovery(
                repo,
                repo / ELIM_RECOVERY_STATE,
                payload,
                validated_result,
            )
            clear_reconciled_run_log_items(
                repo,
                repo / ELIM_RUN_LOG_RECONCILIATION_STATE,
                payload=payload,
                result=validated_result,
            )
        elif result_path.is_file():
            try:
                retryable_result = read_elim_result(result_path, execution_repo)
                verify_elim_result_binding(payload, retryable_result)
                retry_complete, _ = verify_elim_closeout(
                    execution_repo,
                    retryable_result,
                )
                if not retry_complete:
                    validated_result = retryable_result
                    persist_validated_recovery(
                        repo,
                        repo / ELIM_RECOVERY_STATE,
                        payload,
                        retryable_result,
                    )
            except (ContextError, OSError, RuntimeError, TypeError, ValueError):
                # The central closeout failure already records the invalid result.
                # Never let an unverified continuation alter the next exact queue.
                pass
        epoch_closeout_missing = False
        if (
            outcome == 0
            and semantic_closeout_complete
            and payload["elim_decision"]["profile"]["full_context"]
            and not comprehensive_epoch_recorded(
                execution_repo,
                payload["chain_id"],
                execution_repo
                / Path((payload.get("context_packet") or {}).get("local_path"))
                if (payload.get("context_packet") or {}).get("local_path")
                else None,
            )
        ):
            outcome = 4
            epoch_closeout_missing = True
            control["last_failed_reason"] = (
                "Comprehensive Elim closeout did not record the required Review Epoch."
            )
        accounted_noncomplete = (
            launch_state["run_log_verified"]
            and result_outcome in {"usage_stopped", "blocked"}
            and not epoch_closeout_missing
        )
        if outcome == 0 or accounted_noncomplete:
            checkout_head = command([git, "rev-parse", "HEAD"], cwd=execution_repo)
            if (
                checkout_head.returncode != 0
                or re.fullmatch(r"[0-9a-f]{40}", checkout_head.stdout.strip()) is None
            ):
                raise RuntimeError(
                    "could not preserve the successful Elim checkout boundary"
                )
            control["elim_checkout_synced_head"] = checkout_head.stdout.strip()
            control["last_consumed_chain_id"] = payload["chain_id"]
            control["last_consumed_at"] = payload["updated_at"]
            if outcome == 0:
                control["last_successful_chain_id"] = payload["chain_id"]
                control["last_successful_at"] = (
                    datetime.now(timezone.utc).replace(microsecond=0).isoformat()
                )
            control.pop("requested_run", None)
            control.pop("requested_comprehensive_review", None)
            append_host_outcome_history(
                config,
                repo,
                chain_id=payload["chain_id"],
                status=(
                    result_outcome.replace("_", "-")
                    if accounted_noncomplete
                    else
                    "human-review"
                    if validated_result
                    and validated_result.get("outcome") == "human_review"
                    else "completed"
                ),
                stage="elim-closeout",
                exit_code=outcome,
                payload=payload,
            )
        else:
            if closeout_failure_reason:
                failure_reason = closeout_failure_reason
            elif not epoch_closeout_missing:
                failure_reason = (
                    "The host usage monitor did not end in a passing state; inspect "
                    "the Elim Run Log and usage attestation."
                    if outcome == 5
                    else f"Elim exited with code {outcome}; inspect the Elim Run Log."
                )
            else:
                failure_reason = control["last_failed_reason"]
            control["last_failed_reason"] = failure_reason
            persist_pending_run_log_reconciliation(
                repo,
                repo / ELIM_RUN_LOG_RECONCILIATION_STATE,
                payload=payload,
                invocation_id=invocation_id,
                failure_stage=(
                    "elim-closeout"
                    if closeout_failure_reason or epoch_closeout_missing
                    else "elim-execution"
                ),
                reason_code="terminal-run-log-unaccounted",
                failure_summary=failure_reason,
                launch_state=launch_state,
            )
        record_elim_runtime(
            repo=repo,
            config=config,
            control=control,
            payload=payload,
            outcome=outcome,
            result_outcome=result_outcome or None,
        )
        if outcome == 0 or accounted_noncomplete:
            consumed = {
                key: str(value.get("request_id"))
                for key, value in (
                    ("requested_run", requested),
                    ("requested_comprehensive_review", comprehensive),
                )
                if isinstance(value, dict) and value.get("request_id")
            }
            persist_control_state(
                control_path,
                control,
                repo=repo,
                consumed_requests=consumed,
            )
        else:
            record_terminal_failure(
                config,
                control,
                repo,
                stage=(
                    "elim-closeout"
                    if closeout_failure_reason or epoch_closeout_missing
                    else "elim-execution"
                ),
                message=failure_reason,
                exit_code=outcome,
                next_action=(
                    "Inspect the preserved Elim task, isolated checkout, run log, "
                    "usage attestation, and exact checkpoint; reconcile safely and "
                    "launch a fresh current chain."
                ),
                payload=payload,
                chain_id=payload.get("chain_id"),
                control_path=control_path,
            )
        return 0 if accounted_noncomplete else outcome
    except KeyboardInterrupt:
        message = (
            f"{current_stage} was interrupted; the child process group was "
            "confirmed stopped and preserved evidence requires review."
        )
        try:
            persist_pending_run_log_reconciliation(
                repo,
                repo / ELIM_RUN_LOG_RECONCILIATION_STATE,
                payload=payload,
                invocation_id=invocation_id,
                failure_stage=current_stage,
                reason_code="post-spawn-interruption",
                failure_summary=message,
                launch_state=launch_state,
            )
        except (ContextError, OSError, TypeError, ValueError) as exc:
            message += f" Run Log reconciliation persistence also failed: {exc}"
        if launch_state.get("spawned") is True and payload:
            control["last_failed_reason"] = message
            try:
                record_elim_runtime(
                    repo=repo,
                    config=config,
                    control=control,
                    payload=payload,
                    outcome=130,
                    result_outcome="failed",
                    details=message,
                )
            except (ContextError, OSError, RuntimeError, TypeError, ValueError):
                pass
        record_terminal_failure(
            config,
            control,
            repo,
            stage=current_stage,
            message=message,
            exit_code=130,
            next_action=(
                "Inspect the preserved isolated checkout, JSONL output, Elim task, "
                "usage attestation, and CURRENT_AUDIT checkpoint before retrying."
            ),
            payload=payload or None,
            chain_id=(
                payload.get("chain_id")
                if payload
                else "host-dispatch-"
                + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            ),
            control_path=control_path,
        )
        print(f"run-chain-dispatcher: {message}", file=sys.stderr)
        return 130
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        message = f"{current_stage} failed: {exc}"
        try:
            persist_pending_run_log_reconciliation(
                repo,
                repo / ELIM_RUN_LOG_RECONCILIATION_STATE,
                payload=payload,
                invocation_id=invocation_id,
                failure_stage=current_stage,
                reason_code="post-spawn-dispatcher-failure",
                failure_summary=message,
                launch_state=launch_state,
            )
        except (ContextError, OSError, TypeError, ValueError) as reconciliation_exc:
            message += (
                " Run Log reconciliation persistence also failed: "
                f"{reconciliation_exc}"
            )
        if launch_state.get("spawned") is True and payload:
            control["last_failed_reason"] = message
            try:
                record_elim_runtime(
                    repo=repo,
                    config=config,
                    control=control,
                    payload=payload,
                    outcome=1,
                    result_outcome="failed",
                    details=message,
                )
            except (ContextError, OSError, RuntimeError, TypeError, ValueError):
                pass
        record_terminal_failure(
            config,
            control,
            repo,
            stage=current_stage,
            message=message,
            exit_code=1,
            next_action=(
                "Inspect the host dispatcher failure and preserved local projection, "
                "repair the exact failed prerequisite, and launch a fresh current chain."
            ),
            payload=payload or None,
            chain_id=(
                payload.get("chain_id")
                if payload
                else "host-dispatch-"
                + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            ),
            control_path=control_path,
        )
        print(f"run-chain-dispatcher: {message}", file=sys.stderr)
        return 1
    finally:
        signal.signal(signal.SIGTERM, prior_sigterm_handler)
        release_dispatch_lock(dispatch_lease)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        print(f"run-chain-dispatcher: {exc}", file=sys.stderr)
        raise SystemExit(1)
