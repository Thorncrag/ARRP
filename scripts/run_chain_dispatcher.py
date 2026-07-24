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
except ModuleNotFoundError:  # Imported as scripts.run_chain_dispatcher.
    from scripts.arrp_context import ContextError, contained_path
    from scripts.elim_execution import validate_work_unit


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
ELIM_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "unit_id",
        "work_type",
        "outcome",
        "authority",
        "issue_id",
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
    expected_run_id: str | None = None,
) -> tuple[int, bool, str]:
    if outcome != 0:
        try:
            handoff = read_current_audit(
                repo / "framework" / "logs" / "CURRENT_AUDIT.md",
                repo,
            )
        except (ContextError, OSError, TypeError, ValueError) as exc:
            return (
                outcome,
                False,
                f"Elim exited abnormally and its recovery checkpoint is invalid: {exc}",
            )
        state = handoff["Handoff state"]
        if state == "Open":
            return (
                outcome,
                False,
                "Elim exited abnormally with an Open recovery checkpoint. Treat the "
                "checkpoint as unfinished-work evidence, never runtime liveness, and "
                "reconcile it before retrying the same work unit.",
            )
        if state == "Inactive":
            return (
                outcome,
                False,
                "Elim exited abnormally without a recoverable Paused or Blocked "
                "checkpoint; inspect its preserved output before retrying.",
            )
        return outcome, False, ""
    try:
        result = read_elim_result(result_path, repo)
        if expected_run_id is not None and result["run_id"] != expected_run_id:
            raise ContextError(
                "Elim structured result does not match the current Chain ID"
            )
        if result["outcome"] in {"completed", "clean", "human_review"} and git:
            synchronize_canonical_repo(git, repo)
        complete, detail = verify_elim_closeout(repo, result)
    except (ContextError, OSError, TypeError, ValueError) as exc:
        return 6, False, f"Elim closeout verification failed: {exc}"
    if not complete:
        return 6, False, detail
    return 0, True, ""


def executable(config: dict[str, Any], key: str) -> str:
    expected = EXECUTABLES[key]
    configured = str(config["hostDispatcher"][key])
    if configured != expected:
        raise RuntimeError(f"configured {key} differs from the reviewed host path")
    if not Path(expected).is_file() or not os.access(expected, os.X_OK):
        raise RuntimeError(f"reviewed {key} is unavailable: {expected}")
    return expected


def alert_failures(
    config: dict[str, Any],
    control: dict[str, Any],
    manifest: dict[str, Any],
    repo: Path,
) -> bool:
    failures = list(manifest.get("failures") or [])
    problems = list((manifest.get("work_queue") or {}).get("problems") or [])
    action_items = list(control.get("action_items") or [])
    current_chain = manifest.get("chain_id")
    retained = [
        item
        for item in action_items
        if item.get("kind") != "automation_failure"
        or item.get("chain_id") == current_chain
    ]
    changed = retained != action_items
    control["action_items"] = retained
    if not failures and not problems and manifest.get("status") != "blocked":
        return changed
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
        return changed
    item = {
        "id": "automation-failure-" + fingerprint,
        "chain_id": manifest.get("chain_id"),
        "kind": "automation_failure",
        "owner": "human",
        "summary": "ARRP run chain requires attention.",
        "created_at": manifest.get("updated_at"),
        "failure_count": len(failures) + len(problems),
    }
    control.setdefault("action_items", []).append(item)
    control["action_items"] = control["action_items"][-50:]
    control["alert_fingerprints"] = [*seen, fingerprint][-100:]
    notification = executable(config, "notificationPath")
    if os.access(notification, os.X_OK):
        command(
            [
                notification,
                "-e",
                'display notification "Open the ARRP Console Action Items for details." '
                'with title "ARRP automation requires attention"',
            ],
            cwd=repo,
        )
    return True


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
    elim_started = owner_status in {"elim-running", "elim-closeout"}
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
    control["last_failed_chain_id"] = chain_id
    control["last_failed_exit_code"] = 130
    control["last_failed_reason"] = details

    payload["status"] = "failed"
    payload["updated_at"] = completed_at
    if runtime:
        payload["elim_runtime"] = runtime
    payload["next_action"] = next_action
    failures = [
        item
        for item in (payload.get("failures") or [])
        if item.get("stage") != stage
    ]
    failures.append(
        {
            "stage": stage,
            "classification": "blocking",
            "message": details,
        }
    )
    payload["failures"] = failures
    alert_failures(config, control, payload, repo)
    write_json(manifest_path, payload, root=repo)


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


def synchronize_canonical_repo(git: str, repo: Path) -> None:
    """Require clean main and fast-forward it to the authenticated remote."""
    require_clean_repo(git, repo)
    branch = command([git, "branch", "--show-current"], cwd=repo)
    if branch.returncode != 0 or branch.stdout.strip() != "main":
        raise RuntimeError("ARRP is not on main; automated dispatch deferred")
    fetched = command([git, "fetch", "origin", "main"], cwd=repo)
    if fetched.returncode != 0:
        raise RuntimeError("could not refresh origin/main: " + fetched.stderr.strip())
    head = command([git, "rev-parse", "HEAD"], cwd=repo)
    remote = command([git, "rev-parse", "refs/remotes/origin/main"], cwd=repo)
    if head.returncode != 0 or remote.returncode != 0:
        raise RuntimeError("could not compare local main with origin/main")
    if head.stdout.strip() == remote.stdout.strip():
        return
    ancestry = command(
        [git, "merge-base", "--is-ancestor", "HEAD", "refs/remotes/origin/main"],
        cwd=repo,
    )
    if ancestry.returncode != 0:
        raise RuntimeError("local main diverges from origin/main; automated dispatch deferred")
    advanced = command(
        [git, "merge", "--ff-only", "refs/remotes/origin/main"],
        cwd=repo,
    )
    if advanced.returncode != 0:
        raise RuntimeError("could not fast-forward local main to origin/main")
    require_clean_repo(git, repo)


def manifest_matches_current_repo(
    git: str,
    repo: Path,
    payload: dict[str, Any],
) -> bool:
    expected = payload.get("final_revision") or payload.get("baseline_commit")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise RuntimeError("run-chain manifest does not record a valid final revision")
    head = command([git, "rev-parse", "HEAD"], cwd=repo)
    if head.returncode != 0:
        raise RuntimeError("could not read the current main revision")
    return head.stdout.strip() == expected


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
        "review_epoch": "review-epoch.json",
        "chain": "chain.json",
    }
    for name in ("integrity", "progress", "intake", "review_epoch", "chain"):
        metadata = inputs.get(name) or {}
        digest = metadata.get("sha256")
        if not isinstance(digest, str) or not digest:
            raise RuntimeError(f"the Elim queue did not preserve a hash for {name}")
        expected = digest if digest.startswith("sha256:") else "sha256:" + digest
        filename = filenames[name]
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


def usage_gate(
    python: str,
    repo: Path,
    config: dict[str, Any],
    baseline_path: Path,
) -> dict[str, Any]:
    result = command(
        [
            python,
            str(repo / "scripts" / "check_codex_usage_reserve.py"),
            "--reserve-percent",
            str(config["usage"]["hardReservePercent"]),
            "--soft-target-percent",
            str(config["usage"]["softRunTargetPercent"]),
            "--run-baseline",
            str(baseline_path),
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
    return read_json(manifest)


def elim_prompt(manifest: Path, payload: dict[str, Any]) -> str:
    profile = payload["elim_decision"]["profile"]
    monitor = (payload.get("usage") or {}).get("host_monitor") or {}
    mode = (
        "Conduct the due comprehensive full-context review and establish the next review epoch."
        if profile["full_context"]
        else "Process the highest-priority eligible work unit from the refreshed chain queue."
    )
    return (
        "You are Elim, the ARRP LLM agent. Follow the authoritative Elim runbook and all "
        "governing project rules. The deterministic run chain completed and its manifest is "
        f"at {manifest}. {mode} Verify the manifest and bot outputs before substantive work; "
        "the manifest's verified_inputs map identifies locally preserved, hash-checked copies "
        "of every deterministic input used to build the queue. "
        "bot failures or stale data take priority. Record ordinary issue/audit work in its "
        "canonical location and record this run in Elim's run log. Respect the 15 percent hard "
        "reserve and ten-point soft run target. The approved host dispatcher, not the Elim "
        "sandbox, owns the official usage probe. Do not launch a second Codex app-server. "
        f"Read the host-attested usage snapshot at {monitor.get('status_path')} before "
        "substantive work, before and after every major unit, between T-audit tiers, and before "
        "closeout. Fail closed if its status is not pass or if it is older than "
        f"{monitor.get('snapshot_max_age_seconds')} seconds. For a completed public-intake assessment, "
        "validate the structured result and run scripts/record_intake_review.py against the "
        "pinned work queue before the final commit so the submission is not reviewed again. "
        "For a completed comprehensive review, prepare the complete Review Epoch record and run "
        "scripts/record_review_epoch.py before the final commit; set triggering_run_id to the "
        f"current chain ID {payload.get('chain_id')}."
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


def launch_elim(
    codex: str,
    repo: Path,
    manifest: Path,
    payload: dict[str, Any],
    state_dir: Path,
    usage_probe: Callable[[], dict[str, Any]],
    usage_status_path: Path,
    usage_attestation_args: dict[str, Any],
    monitor_interval_seconds: int,
    dispatcher_lock: DispatchLease,
    existing_thread_id: str | None = None,
) -> tuple[int, str | None, dict[str, Any]]:
    profile = payload["elim_decision"]["profile"]
    chain_id = payload["chain_id"]
    output = state_dir / f"elim-{chain_id}.jsonl"
    last = state_dir / f"elim-{chain_id}-last-message.txt"
    common = [
        "--json",
        "--model",
        profile["model"],
        "-c",
        f'model_reasoning_effort="{profile["reasoning_effort"]}"',
        "--output-schema",
        str(repo / "framework" / "agents" / "elim-work-unit-result.schema.json"),
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
            str(repo),
            "--sandbox",
            "workspace-write",
            "-",
        ]
    with output.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen(
            argv,
            cwd=repo,
            stdin=subprocess.PIPE,
            text=True,
            stdout=handle,
            stderr=subprocess.STDOUT,
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
            },
        )
        if process.stdin is None:
            process.kill()
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
                write_usage_attestation(
                    usage_status_path,
                    gate=gate,
                    **usage_attestation_args,
                )
                write_dispatch_lock_owner(
                    dispatcher_lock,
                    updates={
                        "status": "elim-running",
                        "elim_thread_id": (
                            thread_id_from_jsonl(output) or existing_thread_id
                        ),
                        "usage_status_path": repo_relative(usage_status_path, repo),
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
                "elim_thread_id": thread_id_from_jsonl(output) or existing_thread_id,
                "usage_status_path": repo_relative(usage_status_path, repo),
            },
        )
    return (
        return_code,
        thread_id_from_jsonl(output) or existing_thread_id,
        last_gate,
    )


def enforce_usage_monitor_closeout(outcome: int, gate: dict[str, Any]) -> int:
    if outcome == 0 and gate.get("status") != "pass":
        return 5
    return outcome


def comprehensive_epoch_recorded(repo: Path, chain_id: str) -> bool:
    ledger = repo / "research" / "review-epochs.jsonl"
    if not ledger.is_file():
        return False
    rows = [line for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        return False
    return json.loads(rows[-1]).get("triggering_run_id") == chain_id


def record_elim_runtime(
    *,
    repo: Path,
    config: dict[str, Any],
    control: dict[str, Any],
    payload: dict[str, Any],
    outcome: int,
) -> None:
    completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    runtime = {
        "id": "elim",
        "name": "Elim",
        "status": "completed" if outcome == 0 else "failed",
        "chain_id": payload.get("chain_id"),
        "completed_at": completed_at,
        "exit_code": outcome,
        "details": (
            "Elim completed and the dispatcher verified its required closeout."
            if outcome == 0
            else control.get("last_failed_reason")
            or f"Elim exited with code {outcome}; inspect the Elim Run Log."
        ),
    }
    control["elim_runtime"] = runtime
    local_manifest = read_json(
        repo / config["manifest"]["localFallback"],
        payload,
        root=repo,
    )
    local_manifest["elim_runtime"] = runtime
    write_json(repo / config["manifest"]["localFallback"], local_manifest, root=repo)


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
    args = parser.parse_args()
    config = read_json(CONFIG)
    host = config["hostDispatcher"]
    repo = Path(host["repositoryPath"])
    if repo != ROOT or not repo.is_dir():
        raise RuntimeError(f"configured ARRP repository path is unavailable: {repo}")
    python = executable(config, "pythonPath")
    git = executable(config, "gitPath")
    gh = executable(config, "githubCliPath")
    codex = executable(config, "codexPath")
    configured_state = str(host["stateDirectory"])
    if configured_state != ".tmp/run-coordinator":
        raise RuntimeError("configured dispatcher state directory is not approved")
    state_dir = contained_path(repo / configured_state, repo)
    state_dir.mkdir(parents=True, exist_ok=True)
    control_path = state_dir / "control.json"
    control = read_json(control_path, {"requests": [], "overrides": {}})
    lock = state_dir / "host-dispatch.lock"
    _, dispatch_lease = acquire_dispatch_lock(
        lock,
        repo=repo,
        config=config,
        control=control,
    )
    write_json(control_path, control)
    if args.recover_stale_lock_only:
        release_dispatch_lock(dispatch_lease)
        return 0
    try:
        synchronize_canonical_repo(git, repo)
        requested = control.get("requested_run")
        comprehensive = control.get("requested_comprehensive_review")
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
                "Latest run-chain manifest is older than current main; waiting for "
                "the matching GitHub chain."
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
        if payload.get("context_packet"):
            context_path = fetch_data_projection(
                config,
                "elim-context.json",
                state_dir / payload["chain_id"] / "elim-context.json",
                payload["context_packet"].get("sha256"),
            )
            payload["context_packet"]["local_path"] = str(context_path)
        write_json(manifest, payload)
        if alert_failures(config, control, payload, repo):
            write_json(control_path, control)
        invocation_id = (
            payload["chain_id"]
            + "-"
            + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        )
        baseline_path = state_dir / f"usage-{invocation_id}.json"
        usage_status_path = (
            state_dir / payload["chain_id"] / f"usage-status-{invocation_id}.json"
        )
        attestation_args = {
            "repo": repo,
            "chain_id": payload["chain_id"],
            "invocation_id": invocation_id,
            "baseline_path": baseline_path,
            "config": config,
        }
        gate = usage_gate(python, repo, config, baseline_path)
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
                    "status_path": repo_relative(usage_status_path, repo),
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
        write_json(manifest, payload)
        if gate.get("status") != "pass":
            write_json(repo / config["manifest"]["localFallback"], payload)
            return 0
        payload = refinalize(
            python,
            repo,
            CONFIG,
            manifest,
            float(gate["lowestRemainingPercent"]),
        )
        write_json(repo / config["manifest"]["localFallback"], payload)
        if not payload["elim_decision"]["launch_recommended"]:
            control["last_consumed_chain_id"] = payload["chain_id"]
            control["last_consumed_at"] = payload["updated_at"]
            control.pop("requested_run", None)
            control.pop("requested_comprehensive_review", None)
            write_json(control_path, control)
            return 0
        if not args.launch_codex:
            print(
                "Elim launch is recommended, but --launch-codex was not supplied; no LLM was invoked."
            )
            return 0
        synchronize_canonical_repo(git, repo)
        outcome, elim_thread_id, final_gate = launch_elim(
            codex,
            repo,
            manifest,
            payload,
            state_dir,
            usage_probe=lambda: usage_gate(
                python,
                repo,
                config,
                baseline_path,
            ),
            usage_status_path=usage_status_path,
            usage_attestation_args=attestation_args,
            monitor_interval_seconds=int(
                config["usage"]["monitorIntervalSeconds"]
            ),
            dispatcher_lock=dispatch_lease,
            existing_thread_id=control.get("elim_thread_id"),
        )
        outcome = enforce_usage_monitor_closeout(outcome, final_gate)
        if elim_thread_id:
            control["elim_thread_id"] = elim_thread_id
        outcome, semantic_closeout_complete, closeout_failure_reason = (
            enforce_elim_result_closeout(
                outcome,
                repo=repo,
                result_path=(
                    state_dir
                    / f"elim-{payload['chain_id']}-last-message.txt"
                ),
                git=git,
                expected_run_id=payload["chain_id"],
            )
        )
        epoch_closeout_missing = False
        if (
            outcome == 0
            and semantic_closeout_complete
            and payload["elim_decision"]["profile"]["full_context"]
            and not comprehensive_epoch_recorded(repo, payload["chain_id"])
        ):
            outcome = 4
            epoch_closeout_missing = True
            control["last_failed_reason"] = (
                "Comprehensive Elim closeout did not record the required Review Epoch."
            )
        if outcome == 0:
            control["last_consumed_chain_id"] = payload["chain_id"]
            control["last_consumed_at"] = payload["updated_at"]
            control.pop("last_failed_chain_id", None)
            control.pop("last_failed_exit_code", None)
            control.pop("last_failed_reason", None)
            control.pop("requested_run", None)
            control.pop("requested_comprehensive_review", None)
        else:
            control["last_failed_chain_id"] = payload["chain_id"]
            control["last_failed_exit_code"] = outcome
            if closeout_failure_reason:
                control["last_failed_reason"] = closeout_failure_reason
            elif not epoch_closeout_missing:
                control["last_failed_reason"] = (
                    "The host usage monitor did not end in a passing state; inspect "
                    "the Elim Run Log and usage attestation."
                    if outcome == 5
                    else f"Elim exited with code {outcome}; inspect the Elim Run Log."
                )
        record_elim_runtime(
            repo=repo,
            config=config,
            control=control,
            payload=payload,
            outcome=outcome,
        )
        write_json(control_path, control)
        return outcome
    finally:
        release_dispatch_lock(dispatch_lease)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        print(f"run-chain-dispatcher: {exc}", file=sys.stderr)
        raise SystemExit(1)
