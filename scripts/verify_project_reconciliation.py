#!/usr/bin/env python3
"""Collect and verify ARRP's fully reconciled operational state.

Local observations come only from the fixed typed ARRP path authority. Hosted
observations come from one owner-local, exact-revision readback produced by the
authenticated synchronization workflow. The verifier has no network,
credential, publishing, remediation, or host-configuration capability and
emits only fixed public-safe reason codes.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from path_authority import PathAuthorityError, ProjectPathAuthority
    from operational_incidents import project_incident_log
    from transaction_lifecycle import current_transaction_states
except ModuleNotFoundError:
    from scripts.path_authority import PathAuthorityError, ProjectPathAuthority
    from scripts.operational_incidents import project_incident_log
    from scripts.transaction_lifecycle import current_transaction_states


SCHEMA_VERSION = 2
LEDGER_RELATIVE_PATH = "records/reconciliation/project-reconciliation.json"
LIVE_READBACK_RELATIVE_PATH = "records/reconciliation/live-readback.json"
REQUIRED_INVENTORIES = (
    "canonical_checkout",
    "remote_revision",
    "registered_worktrees",
    "local_branches",
    "remote_branches",
    "stashes_operations",
    "runtime_runs",
    "runtime_worktrees",
    "transaction_lifecycle",
    "incident_spool",
    "handoff_state",
    "current_runtime_status",
    "operational_incidents",
    "control_state",
    "active_writer_lock_posture",
)
SAFE_CODES = frozenset(
    {
        "ACTIVE_LOCK",
        "AUTHORITY_UNAVAILABLE",
        "CANONICAL_DRIFT",
        "DIRTY_WORKTREE",
        "INCOMPLETE_GIT_OPERATION",
        "INVENTORY_INCOMPLETE",
        "LEDGER_INVALID",
        "LIVE_READBACK_INCOMPLETE",
        "LIVE_READBACK_MISMATCH",
        "LIVE_READBACK_MISSING",
        "LIVE_READBACK_STALE",
        "LOCAL_DISCOVERY_FAILED",
        "PENDING_REVIEW",
        "PRESERVED_TRANSACTION_UNRESOLVED",
        "RETAINED_STATE_INELIGIBLE",
        "RETAINED_STATE_ORPHANED",
        "RETAINED_STATE_UNBOUND",
        "UNREGISTERED_STATE",
    }
)
DISPOSITIONS = frozenset(
    {
        "retained_closed_request",
        "retained_failed_transaction",
        "retained_fixture",
        "retained_historical",
        "retained_superseded",
        "pending_human_review",
    }
)
NONRECONCILED_STATUSES = frozenset(
    {"active", "drifted", "incomplete", "mismatched", "pending", "unknown"}
)
GIT_OPERATION_MARKERS = (
    "MERGE_HEAD",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
    "BISECT_LOG",
    "rebase-apply",
    "rebase-merge",
    "sequencer",
)
MAX_LIVE_AGE_SECONDS = 3600
TRANSACTION_TERMINAL_STATES = frozenset(
    {"recoverably_retired", "completed_noop", "completed_published"}
)


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _identity_key(value: Any) -> tuple[str, str] | None:
    if not isinstance(value, dict):
        return None
    state_id, kind = value.get("id"), value.get("kind")
    if not _is_nonempty_text(state_id) or not _is_nonempty_text(kind):
        return None
    return state_id, kind


def _binding(value: Mapping[str, Any]) -> str | None:
    binding = value.get("identity_binding")
    if not isinstance(binding, dict) or not _is_nonempty_text(binding.get("sha256")):
        return None
    return binding["sha256"]


def _git_bytes(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", os.fspath(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=20,
    )
    if result.returncode:
        raise ValueError("local Git discovery failed")
    return result.stdout


def _git(repo: Path, *args: str) -> str:
    return _git_bytes(repo, *args).decode("utf-8").strip()


def _is_ancestor(repo: Path, older: str, newer: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            os.fspath(repo),
            "merge-base",
            "--is-ancestor",
            older,
            newer,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=20,
    )
    if result.returncode not in {0, 1}:
        raise ValueError("local Git ancestry discovery failed")
    return result.returncode == 0


def _item(
    kind: str,
    state_id: str,
    value: Any,
    status: str = "clear",
    **extra: Any,
) -> dict[str, Any]:
    return {
        "id": state_id,
        "kind": kind,
        "identity_binding": {"sha256": _digest(value)},
        "status": status,
        **extra,
    }


def _regular_file_digest(path: Path) -> str:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError("unsafe owner-local file")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _directory_digest(root: Path) -> str:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("unsafe owner-local directory")
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            target = os.readlink(path)
            rows.append(
                {
                    "path": relative,
                    "type": "symlink",
                    "target_sha256": "sha256:"
                    + hashlib.sha256(os.fsencode(target)).hexdigest(),
                }
            )
        elif stat.S_ISDIR(metadata.st_mode):
            rows.append({"path": relative, "type": "directory", "mode": stat.S_IMODE(metadata.st_mode)})
        elif stat.S_ISREG(metadata.st_mode):
            rows.append(
                {
                    "path": relative,
                    "type": "file",
                    "mode": stat.S_IMODE(metadata.st_mode),
                    "size": metadata.st_size,
                    "sha256": _regular_file_digest(path),
                }
            )
        else:
            raise ValueError("owner-local state contains an unsupported object")
    return _digest(rows)


def _worktree_delta(repo: Path) -> dict[str, Any]:
    status = _git_bytes(
        repo,
        "status",
        "--porcelain=v2",
        "-z",
        "--untracked-files=all",
    )
    diff = _git_bytes(repo, "diff", "HEAD", "--binary", "--no-ext-diff")
    untracked = [
        item
        for item in _git_bytes(
            repo, "ls-files", "--others", "--exclude-standard", "-z"
        ).split(b"\0")
        if item
    ]
    untracked_rows = []
    root = repo.resolve()
    for raw in sorted(untracked):
        relative = raw.decode("utf-8")
        candidate = (root / relative).resolve(strict=True)
        if root not in candidate.parents:
            raise ValueError("untracked path escapes worktree")
        untracked_rows.append(
            {"path": relative, "sha256": _regular_file_digest(candidate)}
        )
    return {
        "status_sha256": "sha256:" + hashlib.sha256(status).hexdigest(),
        "diff_sha256": "sha256:" + hashlib.sha256(diff).hexdigest(),
        "untracked": untracked_rows,
        "clean": not status,
    }


def _worktree_id(path: Path, authority: ProjectPathAuthority) -> str:
    resolved = path.resolve()
    repository = authority.repository_root.resolve()
    state_worktrees = (authority.state_root / "worktrees").resolve()
    if resolved == repository:
        return "canonical"
    if resolved.parent == state_worktrees:
        return f"runtime:{resolved.name}"
    if repository in resolved.parents:
        return "repository:" + resolved.relative_to(repository).as_posix()
    return "external:" + _digest(os.fspath(resolved))[-16:]


def _worktree_rows(authority: ProjectPathAuthority) -> list[dict[str, Any]]:
    lines = _git(
        authority.repository_root, "worktree", "list", "--porcelain"
    ).splitlines()
    blocks: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in [*lines, ""]:
        if not line:
            if current:
                blocks.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    rows = []
    for block in blocks:
        path = Path(block["worktree"]).resolve()
        state_id = _worktree_id(path, authority)
        delta = _worktree_delta(path)
        rows.append(
            _item(
                "worktree",
                state_id,
                {
                    "head": block.get("HEAD"),
                    "branch": block.get("branch"),
                    "delta": delta,
                },
                "clear"
                if state_id == "canonical" and delta["clean"]
                else "retained",
                clean=delta["clean"],
            )
        )
    return rows


def _runtime_directory_rows(root: Path, kind: str) -> list[dict[str, Any]]:
    if not root.exists():
        return [_item(kind, "directory-unavailable", "missing", "unknown")]
    if not root.is_dir() or root.is_symlink():
        return [_item(kind, "directory-invalid", "invalid", "unknown")]
    children = sorted(root.iterdir())
    if not children:
        return [_item(kind, "none", "empty")]
    rows = []
    for child in children:
        if child.is_symlink() or not child.is_dir():
            rows.append(_item(kind, child.name, "unsupported", "unknown"))
            continue
        rows.append(
            _item(
                kind,
                child.name,
                {
                    "name": child.name,
                    "manifest_sha256": _directory_digest(child),
                },
                "retained",
            )
        )
    return rows


def _locked(path: Path) -> bool:
    if not path.exists():
        return False
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError("runtime lock is not a regular file")
    with path.open("rb") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(stream, fcntl.LOCK_UN)
            return False
        except BlockingIOError:
            return True


def _handoff_is_inactive(text: str) -> bool:
    required = (
        "status: inactive",
        "| Handoff state | Inactive |",
        "| Active issue/task | None. |",
        "| Next step | None. |",
        "| Blockers/questions | None. |",
    )
    return all(marker in text for marker in required)


def collect_local(
    authority: ProjectPathAuthority,
    *,
    checked_at: datetime | None = None,
) -> dict[str, Any]:
    """Collect local facts from fixed production or an explicit test fixture."""

    if authority.mode not in {"production_canonical", "fixture"}:
        raise PathAuthorityError("unsupported reconciliation authority")
    repo, state = authority.repository_root, authority.state_root
    head = _git(repo, "rev-parse", "HEAD")
    branch = _git(repo, "branch", "--show-current")
    remote = _git(repo, "rev-parse", "refs/remotes/origin/main")
    canonical_delta = _worktree_delta(repo)
    inv = {name: [] for name in REQUIRED_INVENTORIES}
    inv["canonical_checkout"] = [
        _item(
            "canonical_checkout",
            "canonical",
            {"head": head, "branch": branch, "delta": canonical_delta},
            "clear"
            if branch == "main" and canonical_delta["clean"] and head == remote
            else "drifted",
            revision=head,
        )
    ]
    inv["remote_revision"] = [
        _item(
            "remote_revision",
            "origin-main",
            {"revision": remote},
            revision=remote,
        )
    ]
    inv["registered_worktrees"] = _worktree_rows(authority)

    for line in _git(
        repo,
        "for-each-ref",
        "--format=%(refname:short)|%(objectname)",
        "refs/heads",
    ).splitlines():
        name, revision = line.split("|", 1)
        inv["local_branches"].append(
            _item(
                "local_branch",
                name,
                {"name": name, "revision": revision},
                "clear" if name == "main" and revision == head else "retained",
                revision=revision,
                merged_into_origin_main=_is_ancestor(repo, revision, remote),
            )
        )
    for line in _git(
        repo,
        "for-each-ref",
        "--format=%(refname:short)|%(objectname)",
        "refs/remotes/origin",
    ).splitlines():
        name, revision = line.split("|", 1)
        inv["remote_branches"].append(
            _item(
                "remote_branch",
                name,
                {"name": name, "revision": revision},
                "clear" if name in {"origin", "origin/HEAD", "origin/main"} else "retained",
                revision=revision,
                merged_into_origin_main=_is_ancestor(repo, revision, remote),
            )
        )

    git_dir = Path(_git(repo, "rev-parse", "--git-dir"))
    if not git_dir.is_absolute():
        git_dir = (repo / git_dir).resolve()
    operations = [
        marker for marker in GIT_OPERATION_MARKERS if (git_dir / marker).exists()
    ]
    stashes = _git(repo, "stash", "list", "--format=%H").splitlines()
    if not stashes and not operations:
        inv["stashes_operations"] = [_item("git_operation", "none", "clear")]
    else:
        inv["stashes_operations"].extend(
            _item("stash", revision, revision, "retained")
            for revision in stashes
        )
        inv["stashes_operations"].extend(
            _item("git_operation", marker, marker, "incomplete")
            for marker in operations
        )

    inv["runtime_runs"] = _runtime_directory_rows(state / "runs", "runtime_run")
    runtime_root = state / "worktrees"
    if not runtime_root.is_dir() or runtime_root.is_symlink():
        inv["runtime_worktrees"] = [
            _item("runtime_worktree", "directory-invalid", "invalid", "unknown")
        ]
    else:
        registered_runtime = {
            row["id"].removeprefix("runtime:"): row
            for row in inv["registered_worktrees"]
            if row["id"].startswith("runtime:")
        }
        runtime_children = sorted(runtime_root.iterdir())
        runtime_names = [
            child.name
            for child in runtime_children
            if child.is_dir() and not child.is_symlink()
        ]
        inv["runtime_worktrees"] = [
            _item(
                "runtime_worktree",
                name,
                {
                    "registered_binding": _binding(registered_runtime[name])
                    if name in registered_runtime
                    else None,
                    "clean": (
                        registered_runtime[name].get("clean")
                        if name in registered_runtime
                        else None
                    ),
                },
                "retained" if name in registered_runtime else "unknown",
                clean=(
                    registered_runtime[name].get("clean")
                    if name in registered_runtime
                    else None
                ),
            )
            for name in runtime_names
        ]
        inv["runtime_worktrees"].extend(
            _item(
                "runtime_worktree",
                child.name,
                "unsupported",
                "unknown",
            )
            for child in runtime_children
            if child.is_symlink() or not child.is_dir()
        )
        if not inv["runtime_worktrees"]:
            inv["runtime_worktrees"] = [
                _item("runtime_worktree", "none", "empty")
            ]

    transaction_events = (
        state / "records" / "automation" / "transaction-events.jsonl"
    )
    transaction_states: dict[str, dict[str, Any]] = {}
    if not transaction_events.exists():
        inv["transaction_lifecycle"] = [
            _item(
                "transaction_lifecycle",
                "authority-unavailable",
                "missing",
                "unknown",
            )
        ]
    else:
        transaction_states = current_transaction_states(transaction_events)
        if not transaction_states:
            inv["transaction_lifecycle"] = [
                _item(
                    "transaction_lifecycle",
                    "none",
                    {"event_log_sha256": _regular_file_digest(transaction_events)},
                )
            ]
        else:
            inv["transaction_lifecycle"] = [
                _item(
                    "transaction_lifecycle",
                    run_id,
                    {
                        "event_sha256": event["event_sha256"],
                        "state": event["state"],
                        "branch": event["branch"],
                        "head": event["head"],
                        "package_digest": event["package_digest"],
                    },
                    (
                        "clear"
                        if event["state"] in TRANSACTION_TERMINAL_STATES
                        else "retained"
                    ),
                    event_sha256=event["event_sha256"],
                    lifecycle_state=event["state"],
                    branch=event["branch"],
                    revision=event["head"],
                    package_digest=event["package_digest"],
                )
                for run_id, event in sorted(transaction_states.items())
            ]

    spool = state / "incident-spool.jsonl"
    if spool.exists():
        spool_digest = _regular_file_digest(spool)
        inv["incident_spool"] = [
            _item(
                "incident_spool",
                "current",
                {"sha256": spool_digest, "size": spool.stat().st_size},
                "clear" if spool.stat().st_size == 0 else "pending",
            )
        ]
    else:
        inv["incident_spool"] = [
            _item("incident_spool", "current", "missing", "unknown")
        ]

    handoff = state / "records" / "handoffs" / "current-task.local.md"
    if handoff.exists():
        handoff_text = handoff.read_text(encoding="utf-8")
        inv["handoff_state"] = [
            _item(
                "owner_local_handoff",
                "current",
                {"sha256": _regular_file_digest(handoff)},
                "clear" if _handoff_is_inactive(handoff_text) else "pending",
            )
        ]
    else:
        inv["handoff_state"] = [
            _item("owner_local_handoff", "current", "missing", "unknown")
        ]

    status_path = state / "status.json"
    if status_path.exists():
        status_value = _load_json(status_path)
        status_name = str(status_value.get("status") or "unknown")
        run_id = str(status_value.get("run_id") or "unknown")
        terminal_event = transaction_states.get(run_id)
        terminal_status_bound = bool(
            terminal_event
            and terminal_event.get("state") in TRANSACTION_TERMINAL_STATES
        )
        inv["current_runtime_status"] = [
            _item(
                "runtime_status",
                run_id,
                {
                    "sha256": _regular_file_digest(status_path),
                    "status": status_name,
                    "stage": status_value.get("stage"),
                    "transaction_event_sha256": (
                        terminal_event.get("event_sha256")
                        if terminal_status_bound
                        else None
                    ),
                },
                (
                    "clear"
                    if status_name in {"idle", "ready"} or terminal_status_bound
                    else "retained"
                ),
            )
        ]
    else:
        inv["current_runtime_status"] = [
            _item("runtime_status", "current", "missing", "unknown")
        ]

    incident_path = state / "records" / "automation" / "operational-incidents.jsonl"
    incident_projection = project_incident_log(incident_path)
    incident_status = (
        "clear"
        if incident_projection.get("availability") == "current"
        and incident_projection.get("complete") is True
        and incident_projection.get("unresolved_count") == 0
        else "pending"
        if incident_projection.get("availability") == "current"
        and incident_projection.get("complete") is True
        else "unknown"
    )
    inv["operational_incidents"] = [
        _item(
            "operational_incident_projection",
            "current",
            {
                "event_log_sha256": (
                    _regular_file_digest(incident_path)
                    if incident_path.exists()
                    else None
                ),
                "unresolved_count": incident_projection.get("unresolved_count"),
            },
            incident_status,
        )
    ]

    paused = state / "PAUSED"
    inv["control_state"] = [
        _item(
            "automation_control",
            "global",
            {
                "mode": "paused" if paused.exists() else "run",
                "sha256": _regular_file_digest(paused) if paused.exists() else None,
            },
            "paused" if paused.exists() else "clear",
        )
    ]
    run_lock = state / "run.lock"
    lock_held = _locked(run_lock)
    inv["active_writer_lock_posture"] = [
        _item(
            "runtime_lock",
            "run-lock",
            {"present": run_lock.exists(), "held": lock_held},
            "active" if lock_held else "clear",
        )
    ]
    generated_at = checked_at or datetime.now(timezone.utc)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "inventory": inv,
        "inventory_digest": _digest(inv),
    }


def _validate_entry(entry: Any) -> bool:
    proof = entry.get("reconciliation_proof") if isinstance(entry, dict) else None
    proof_valid = (
        proof is None
        if isinstance(entry, dict)
        and entry.get("disposition") == "pending_human_review"
        else isinstance(proof, dict)
        and proof.get("proof_type")
        in {
            "git_ancestor",
            "transaction_terminal",
            "hosted_closed_request",
            "registered_fixture",
        }
        and _is_nonempty_text(proof.get("authority"))
        and isinstance(proof.get("proof_digest"), str)
        and proof["proof_digest"].startswith("sha256:")
        and len(proof["proof_digest"]) == 71
    )
    return bool(
        isinstance(entry, dict)
        and _identity_key(entry) is not None
        and _binding(entry) is not None
        and entry.get("disposition") in DISPOSITIONS
        and isinstance(entry.get("evidence_refs"), list)
        and entry["evidence_refs"]
        and all(_is_nonempty_text(ref) for ref in entry["evidence_refs"])
        and _is_nonempty_text(entry.get("reviewed_at"))
        and _is_nonempty_text(entry.get("next_action"))
        and proof_valid
    )


def _transaction_proofs(
    inventory: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    rows = inventory.get("transaction_lifecycle")
    if not isinstance(rows, list):
        return {}
    return {
        str(row["id"]): row
        for row in rows
        if isinstance(row, dict)
        and row.get("kind") == "transaction_lifecycle"
        and _is_nonempty_text(row.get("event_sha256"))
    }


def _hosted_closed_proof(
    item: Mapping[str, Any],
    proof: Mapping[str, Any],
    live_readback: Any,
) -> bool:
    if not isinstance(live_readback, dict):
        return False
    rows = live_readback.get("closed_pull_requests")
    if not isinstance(rows, list):
        return False
    branch = str(item.get("id") or "").removeprefix("origin/")
    revision = item.get("revision")
    matches = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("head_ref") == branch
        and row.get("head_revision") == revision
        and row.get("state") in {"closed", "merged"}
        and isinstance(row.get("number"), int)
    ]
    if len(matches) != 1:
        return False
    expected = _digest(
        {
            "proof_type": "hosted_closed_request",
            "number": matches[0]["number"],
            "state": matches[0]["state"],
            "head_ref": branch,
            "head_revision": revision,
        }
    )
    return (
        proof.get("authority") == "github-authenticated-readback"
        and proof.get("proof_digest") == expected
    )


def _retained_state_is_eligible(
    item: Mapping[str, Any],
    entry: Mapping[str, Any],
    inventory: Mapping[str, Any],
    live_readback: Any,
) -> bool:
    """Derive eligibility from current typed evidence, never a ledger flag."""

    proof = entry.get("reconciliation_proof")
    if not isinstance(proof, dict):
        return False
    kind = item.get("kind")
    if kind in {"worktree", "runtime_worktree"}:
        return False
    if proof.get("proof_type") == "git_ancestor":
        if kind not in {"local_branch", "remote_branch"}:
            return False
        remote_rows = inventory.get("remote_revision")
        origin_main = (
            remote_rows[0].get("revision")
            if isinstance(remote_rows, list)
            and len(remote_rows) == 1
            and isinstance(remote_rows[0], dict)
            else None
        )
        if not _is_nonempty_text(origin_main):
            return False
        expected = _digest(
            {
                "proof_type": "git_ancestor",
                "revision": item.get("revision"),
                "origin_main": origin_main,
            }
        )
        return (
            item.get("merged_into_origin_main") is True
            and proof.get("authority") == "local-git-ancestry"
            and proof.get("proof_digest") == expected
        )
    if proof.get("proof_type") == "transaction_terminal":
        run_id = (
            str(item.get("id") or "")
            if kind in {"runtime_run", "transaction_lifecycle"}
            else None
        )
        if kind in {"local_branch", "remote_branch"}:
            branch = str(item.get("id") or "").removeprefix("origin/")
            transaction = next(
                (
                    row
                    for row in _transaction_proofs(inventory).values()
                    if row.get("branch") == branch
                    and row.get("revision") == item.get("revision")
                ),
                None,
            )
        else:
            transaction = _transaction_proofs(inventory).get(str(run_id))
        if not transaction:
            return False
        return (
            transaction.get("lifecycle_state")
            in TRANSACTION_TERMINAL_STATES
            and proof.get("authority") == "transaction-lifecycle"
            and proof.get("proof_digest") == transaction.get("event_sha256")
        )
    if proof.get("proof_type") == "hosted_closed_request":
        return kind in {"local_branch", "remote_branch"} and _hosted_closed_proof(
            item, proof, live_readback
        )
    return False


def verify(
    ledger: Any,
    local_snapshot: Any,
    live_readback: Any,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Verify exact local discovery, retained dispositions, and hosted readback."""

    codes: set[str] = set()
    accounting_codes: set[str] = set()
    now = now or datetime.now(timezone.utc)
    if (
        not isinstance(local_snapshot, dict)
        or local_snapshot.get("schema_version") != SCHEMA_VERSION
        or local_snapshot.get("inventory_digest")
        != _digest(local_snapshot.get("inventory"))
        or not isinstance(local_snapshot.get("inventory"), dict)
    ):
        codes.add("LOCAL_DISCOVERY_FAILED")
        accounting_codes.add("LOCAL_DISCOVERY_FAILED")
        inventory: dict[str, Any] = {}
    else:
        inventory = local_snapshot["inventory"]

    entries = (
        ledger.get("retained_states", [])
        if isinstance(ledger, dict)
        and ledger.get("schema_version") == SCHEMA_VERSION
        else []
    )
    if (
        not isinstance(ledger, dict)
        or not _is_nonempty_text(ledger.get("ledger_id"))
        or not _is_nonempty_text(ledger.get("reviewed_at"))
        or not isinstance(entries, list)
        or ledger.get("local_snapshot_digest")
        != local_snapshot.get("inventory_digest")
    ):
        codes.add("LEDGER_INVALID")
        accounting_codes.add("LEDGER_INVALID")
    bound: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        key = _identity_key(entry)
        if not _validate_entry(entry) or key is None or key in bound:
            codes.add("LEDGER_INVALID")
            accounting_codes.add("LEDGER_INVALID")
            continue
        bound[key] = entry

    seen: set[tuple[str, str]] = set()
    for category in REQUIRED_INVENTORIES:
        items = inventory.get(category)
        if not isinstance(items, list) or not items:
            codes.add("INVENTORY_INCOMPLETE")
            accounting_codes.add("INVENTORY_INCOMPLETE")
            continue
        for item in items:
            key = _identity_key(item)
            if key is None or _binding(item) is None:
                codes.add("INVENTORY_INCOMPLETE")
                accounting_codes.add("INVENTORY_INCOMPLETE")
                continue
            status = item.get("status")
            if status == "drifted":
                codes.add("CANONICAL_DRIFT")
            elif status == "active":
                codes.add("ACTIVE_LOCK")
            elif status == "incomplete":
                codes.add("INCOMPLETE_GIT_OPERATION")
            elif status in {"pending", "unknown", "mismatched"}:
                codes.add("PENDING_REVIEW")
            if status in {"clear", "paused"} | NONRECONCILED_STATUSES:
                continue
            if status != "retained":
                codes.add("INVENTORY_INCOMPLETE")
                continue
            entry = bound.get(key)
            if entry is None:
                codes.add("UNREGISTERED_STATE")
                accounting_codes.add("UNREGISTERED_STATE")
                continue
            seen.add(key)
            if _binding(entry) != _binding(item):
                codes.add("RETAINED_STATE_UNBOUND")
                accounting_codes.add("RETAINED_STATE_UNBOUND")
            elif entry["disposition"] == "pending_human_review":
                codes.add("PENDING_REVIEW")
            elif not _retained_state_is_eligible(
                item,
                entry,
                inventory,
                live_readback,
            ):
                codes.add("RETAINED_STATE_INELIGIBLE")
            if item["kind"] in {"worktree", "runtime_worktree"}:
                if item.get("clean") is False:
                    codes.add("DIRTY_WORKTREE")
                if (
                    item["kind"] == "runtime_worktree"
                    or item["id"].startswith("runtime:")
                ):
                    codes.add("PRESERVED_TRANSACTION_UNRESOLVED")
    if set(bound) - seen:
        codes.add("RETAINED_STATE_ORPHANED")
        accounting_codes.add("RETAINED_STATE_ORPHANED")

    remote_rows = inventory.get("remote_revision") or []
    remote_revision = (
        remote_rows[0].get("revision")
        if isinstance(remote_rows, list)
        and len(remote_rows) == 1
        and isinstance(remote_rows[0], dict)
        else None
    )
    if not isinstance(live_readback, dict):
        codes.add("LIVE_READBACK_MISSING")
    else:
        checked_at = live_readback.get("checked_at")
        max_age = live_readback.get("max_age_seconds")
        try:
            checked = datetime.fromisoformat(str(checked_at).replace("Z", "+00:00"))
            age = (now - checked).total_seconds()
        except (TypeError, ValueError):
            age = MAX_LIVE_AGE_SECONDS + 1
        if (
            not isinstance(max_age, int)
            or max_age <= 0
            or max_age > MAX_LIVE_AGE_SECONDS
            or age > max_age
            or age < -300
        ):
            codes.add("LIVE_READBACK_STALE")
        if (
            live_readback.get("schema_version") != SCHEMA_VERSION
            or live_readback.get("complete") is not True
        ):
            codes.add("LIVE_READBACK_INCOMPLETE")
        if (
            not _is_nonempty_text(remote_revision)
            or live_readback.get("origin_main_revision") != remote_revision
            or live_readback.get("default_branch") != "main"
            or live_readback.get("open_pull_requests") != []
            or live_readback.get("in_progress_actions") != []
            or live_readback.get("required_actions_status") != "success"
            or live_readback.get("required_actions_revision") != remote_revision
            or live_readback.get("pages_status") != "success"
            or live_readback.get("pages_revision") != remote_revision
            or live_readback.get("vercel_status") != "success"
            or live_readback.get("vercel_revision") != remote_revision
        ):
            codes.add("LIVE_READBACK_MISMATCH")
    safe_codes = sorted(codes & SAFE_CODES)
    return {
        "schema_version": SCHEMA_VERSION,
        "inventory_accounted_for": not accounting_codes,
        "fully_reconciled": not safe_codes,
        "reason_codes": safe_codes,
        "inventories_checked": list(REQUIRED_INVENTORIES),
        "local_snapshot_digest": local_snapshot.get("inventory_digest")
        if isinstance(local_snapshot, dict)
        else None,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser


def main(argv: list[str] | None = None) -> int:
    _parser().parse_args(argv)
    try:
        authority = ProjectPathAuthority.production()
        ledger = _load_json(
            authority.state_path(LEDGER_RELATIVE_PATH, owner_only=True)
        )
        live_readback = _load_json(
            authority.state_path(LIVE_READBACK_RELATIVE_PATH, owner_only=True)
        )
        result = verify(ledger, collect_local(authority), live_readback)
    except (
        OSError,
        ValueError,
        PathAuthorityError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ):
        result = {
            "schema_version": SCHEMA_VERSION,
            "inventory_accounted_for": False,
            "fully_reconciled": False,
            "reason_codes": ["AUTHORITY_UNAVAILABLE"],
            "inventories_checked": [],
            "local_snapshot_digest": None,
        }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["fully_reconciled"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
