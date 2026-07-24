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
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


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


def stage_due(
    definition: dict[str, Any],
    previous: dict[str, Any],
    signals: dict[str, Any],
    now: datetime,
) -> tuple[bool, str]:
    due = definition["due"]
    kind = due["kind"]
    if definition["id"] in set(signals.get("force_stages", [])):
        return True, "forced"
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
    recorded_due = parse_time(signals.get("comprehensive_review_next_due_at"))
    due_at = recorded_due or (last + timedelta(days=interval) if last else now)
    due = forced or last is None or now >= due_at
    boundary = (
        signals.get("comprehensive_review_boundary_commit")
        or prior.get("boundary_commit")
        or previous.get("baseline_commit")
    )
    return {
        "interval_days": interval,
        "last_completed_at": iso(last) if last else None,
        "next_due_at": iso(due_at),
        "due": due,
        "due_reason": (
            "forced"
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
        "bot_id": config["agentId"],
        "chain_id": chain_id,
        "run_id": args.run_id or chain_id,
        "trigger": args.trigger,
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


def apply_stage_results(manifest: dict[str, Any], results: dict[str, Any], now: datetime) -> None:
    config_by_id = {
        stage["id"]: stage for stage in read_json(DEFAULT_CONFIG, {}).get("stages", [])
    }
    for stage in manifest["stages"]:
        raw = results.get(stage["id"])
        if not stage["due"] or stage["status"] == "succeeded":
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
    apply_stage_results(manifest, results, now)
    failures = list(manifest.get("failures", []))
    degradations = []
    queue = dict(manifest["queue_counts"])
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
    blockers = [item["message"] for item in failures]
    gateway = manifest.get("work_queue")
    if gateway and not gateway.get("ready_for_elim"):
        blockers.extend(str(item) for item in gateway.get("problems") or [])
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
    if blockers:
        decision, reason = False, "Blocking bot or preflight failure requires correction."
    elif not prior_complete:
        decision, reason = False, "One or more due deterministic stages is incomplete."
    elif remaining is None:
        decision, reason = False, "Codex usage reserve has not been measured."
    elif remaining <= reserve:
        decision, reason = False, "Codex usage is at or below the hard reserve."
    elif not needs_llm:
        decision, reason = False, "No LLM-owned work or comprehensive review is due."
    else:
        decision, reason = True, (
            "Comprehensive review is due."
            if manifest["review_epoch"]["due"]
            else "The refreshed queue contains LLM-owned work."
        )
    if manifest["review_epoch"]["due"]:
        profile_name = "comprehensive"
        profile_reason = "The periodic comprehensive review epoch is due."
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
        "blocked" if failures else "degraded" if degradations else "complete"
    )
    manifest["next_action"] = (
        "Authorized host dispatcher may launch Elim."
        if decision
        else "Resolve the blocking run-chain failure."
        if failures
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
    queue_path = args.queue.resolve()
    manifest["work_queue"] = {
        "path": "project-console-data:elim-work-queue.json",
        "sha256": file_hash(queue_path),
        "ready_for_elim": bool(queue.get("ready_for_elim")),
        "launch_recommended": bool(queue.get("launch_recommended")),
        "counts": queue.get("counts") or {},
        "problems": queue.get("problems") or [],
        "next_item": (queue.get("items") or [None])[0],
    }
    manifest["queue_counts"]["total"] = int(
        (queue.get("counts") or {}).get("total", 0)
    )
    if args.context:
        context = read_json(args.context)
        if context.get("schema_version") != 1 or context.get("status") == "blocked":
            raise ValueError("Elim context packet is blocked or unsupported")
        context_path = args.context.resolve()
        manifest["context_packet"] = {
            "path": "project-console-data:elim-context.json",
            "sha256": file_hash(context_path),
            "profile": context.get("profile"),
            "repository_revision": context.get("repository_revision"),
            "provenance_complete": bool(context.get("provenance_complete")),
            "limits": context.get("limits"),
        }
    else:
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
        manifest["elim_decision"]["reason"] = "No LLM-owned work is present."
        manifest["next_action"] = "No Elim launch; wait for the next trigger."
    manifest["updated_at"] = iso(utc_now())
    atomic_write(args.output or args.manifest, manifest)
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
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--queue", type=Path, required=True)
    p.add_argument("--context", type=Path)
    p.add_argument("--output", type=Path)
    p.set_defaults(function=attach_context)
    return main


def main() -> int:
    args = parser().parse_args()
    return args.function(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"run-coordinator-bot: {exc}")
