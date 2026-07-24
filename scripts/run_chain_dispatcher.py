#!/usr/bin/env python3
"""Host-side ARRP run-chain dispatcher.

This script is inert until invoked (for example, by an explicitly installed
launchd job).  It may trigger/wait for the GitHub chain, applies the first-party
Codex usage gate, and invokes Codex only when the finalized manifest authorizes
an Elim unit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    from arrp_context import ContextError, contained_path
except ModuleNotFoundError:  # Imported as scripts.run_chain_dispatcher.
    from scripts.arrp_context import ContextError, contained_path


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
    for name in ("integrity", "progress", "intake", "review_epoch", "chain"):
        metadata = inputs.get(name) or {}
        digest = metadata.get("sha256")
        if not isinstance(digest, str) or not digest:
            raise RuntimeError(f"the Elim queue did not preserve a hash for {name}")
        expected = digest if digest.startswith("sha256:") else "sha256:" + digest
        target = destination / f"{name}.json"
        artifact = manifest_path.parent / "inputs" / f"{name}.json"
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
                f"inputs/{name}.json",
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
    lock = state_dir / "host-dispatch.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise RuntimeError("another host dispatcher owns the run-chain lock") from exc
    try:
        synchronize_canonical_repo(git, repo)
        control_path = state_dir / "control.json"
        control = read_json(control_path, {"requests": [], "overrides": {}})
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
            existing_thread_id=control.get("elim_thread_id"),
        )
        outcome = enforce_usage_monitor_closeout(outcome, final_gate)
        if elim_thread_id:
            control["elim_thread_id"] = elim_thread_id
        epoch_closeout_missing = False
        if (
            outcome == 0
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
            if not epoch_closeout_missing:
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
        lock.rmdir()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        print(f"run-chain-dispatcher: {exc}", file=sys.stderr)
        raise SystemExit(1)
