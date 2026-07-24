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
from typing import Any

from arrp_context import ContextError, contained_path


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
    # codeql[py/path-injection]
    if not safe_path.is_file():
        return default
    # safe_path has passed the symlink-aware repository-root containment check.
    # codeql[py/path-injection]
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
    # codeql[py/command-line-injection]
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


def usage_gate(
    python: str,
    repo: Path,
    config: dict[str, Any],
    state_dir: Path,
    chain_id: str,
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
            str(state_dir / f"usage-{chain_id}.json"),
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
    mode = (
        "Conduct the due comprehensive full-context review and establish the next review epoch."
        if profile["full_context"]
        else "Process the highest-priority eligible work unit from the refreshed chain queue."
    )
    return (
        "You are Elim, the ARRP LLM agent. Follow the authoritative Elim runbook and all "
        "governing project rules. The deterministic run chain completed and its manifest is "
        f"at {manifest}. {mode} Verify the manifest and bot outputs before substantive work; "
        "bot failures or stale data take priority. Record ordinary issue/audit work in its "
        "canonical location and record this run in Elim's run log. Respect the 15 percent hard "
        "reserve and ten-point soft run target. For a completed public-intake assessment, "
        "validate the structured result and run scripts/record_intake_review.py against the "
        "pinned work queue before the final commit so the submission is not reviewed again. "
        "For a completed comprehensive review, prepare the complete Review Epoch record and run "
        "scripts/record_review_epoch.py before the final commit; set triggering_run_id to the "
        f"current chain ID {payload.get('chain_id')}."
    )


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
    existing_thread_id: str | None = None,
) -> tuple[int, str | None]:
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
        process = subprocess.run(
            argv,
            cwd=repo,
            input=elim_prompt(manifest, payload),
            text=True,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )
    return process.returncode, thread_id_from_jsonl(output) or existing_thread_id


def comprehensive_epoch_recorded(repo: Path, chain_id: str) -> bool:
    ledger = repo / "research" / "review-epochs.jsonl"
    if not ledger.is_file():
        return False
    rows = [line for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        return False
    return json.loads(rows[-1]).get("triggering_run_id") == chain_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--trigger-chain", action="store_true")
    parser.add_argument("--launch-codex", action="store_true")
    args = parser.parse_args()
    args.config = contained_path(args.config, ROOT)
    config = read_json(args.config)
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
        if payload.get("work_queue"):
            queue_path = fetch_data_projection(
                config,
                "elim-work-queue.json",
                state_dir / payload["chain_id"] / "elim-work-queue.json",
                payload["work_queue"].get("sha256"),
            )
            payload["work_queue"]["local_path"] = str(queue_path)
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
        if control.get("last_consumed_chain_id") == payload.get("chain_id"):
            return 0
        gate = usage_gate(python, repo, config, state_dir, payload["chain_id"])
        if gate.get("status") != "pass":
            payload.setdefault("usage", {}).update(
                {
                    "status": gate.get("status", "unavailable"),
                    "remaining_percent": gate.get("lowestRemainingPercent"),
                    "gate": gate,
                }
            )
            write_json(repo / config["manifest"]["localFallback"], payload)
            return 0
        payload = refinalize(
            python,
            repo,
            args.config,
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
        outcome, elim_thread_id = launch_elim(
            codex,
            repo,
            manifest,
            payload,
            state_dir,
            existing_thread_id=control.get("elim_thread_id"),
        )
        if elim_thread_id:
            control["elim_thread_id"] = elim_thread_id
        if (
            outcome == 0
            and payload["elim_decision"]["profile"]["full_context"]
            and not comprehensive_epoch_recorded(repo, payload["chain_id"])
        ):
            outcome = 4
            control["last_failed_reason"] = (
                "Comprehensive Elim closeout did not record the required Review Epoch."
            )
        if outcome == 0:
            control["last_consumed_chain_id"] = payload["chain_id"]
            control["last_consumed_at"] = payload["updated_at"]
            control.pop("requested_run", None)
            control.pop("requested_comprehensive_review", None)
        else:
            control["last_failed_chain_id"] = payload["chain_id"]
            control["last_failed_exit_code"] = outcome
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
