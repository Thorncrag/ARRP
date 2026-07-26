#!/usr/bin/env python3
"""Build the Console's independent cloud-automation health projection."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FAILED_CONCLUSIONS = frozenset(
    {
        "action_required",
        "cancelled",
        "failure",
        "skipped",
        "stale",
        "startup_failure",
        "timed_out",
    }
)


def parse_timestamp(value: Any) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError("automation run has no timestamp")
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("automation timestamp has no timezone")
    return parsed.astimezone(timezone.utc)


def completed_at(run: dict[str, Any]) -> str:
    for key in ("updated_at", "run_started_at", "created_at"):
        value = run.get(key)
        if value:
            parse_timestamp(value)
            return str(value)
    raise ValueError("automation run has no usable completion timestamp")


def run_identity(run: dict[str, Any]) -> str:
    value = str(run.get("id") or "").strip()
    if not value:
        raise ValueError("automation run has no identity")
    return value


def base_projection(
    run: dict[str, Any],
    *,
    status: str,
    conclusion: str,
    updated_at: str,
    chain_prefix: str,
) -> dict[str, Any]:
    run_id = run_identity(run)
    return {
        "schema_version": 1,
        "projection_kind": "cloud-automation-health",
        "chain_id": f"{chain_prefix}-{run_id}",
        "workflow_run_id": run_id,
        "workflow_name": str(
            run.get("name") or "ARRP Run Coordinator Bot"
        ),
        "status": status,
        "conclusion": conclusion,
        "event": str(run.get("event") or ""),
        "head_branch": str(run.get("head_branch") or ""),
        "source_revision": str(run.get("head_sha") or ""),
        "created_at": run.get("created_at"),
        "started_at": run.get("run_started_at"),
        "updated_at": updated_at,
        "completed_at": updated_at,
        "run_url": str(run.get("html_url") or ""),
    }


def workflow_run_projection(event: dict[str, Any]) -> dict[str, Any]:
    run = event.get("workflow_run")
    if not isinstance(run, dict):
        raise ValueError("workflow_run event has no workflow run object")
    conclusion = str(run.get("conclusion") or "unknown")
    healthy = conclusion == "success"
    updated_at = completed_at(run)
    projection = base_projection(
        run,
        status="healthy" if healthy else "failed",
        conclusion=conclusion,
        updated_at=updated_at,
        chain_prefix="cloud-run",
    )
    projection["failure"] = (
        None
        if healthy
        else {
            "stage": "github-actions-run-coordinator",
            "classification": "blocking",
            "message": (
                "The Run Coordinator GitHub workflow ended with "
                f"conclusion {conclusion!r} before a successful current "
                "run-chain projection was guaranteed."
            ),
        }
    )
    projection["next_action"] = (
        "No cloud workflow recovery is required."
        if healthy
        else (
            "Open the linked GitHub Actions run, repair the failed stage, "
            "and dispatch a fresh current chain."
        )
    )
    return projection


def first_run(payload: dict[str, Any]) -> dict[str, Any] | None:
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list):
        raise ValueError("workflow-runs response has no workflow_runs array")
    for run in runs:
        if isinstance(run, dict):
            return run
    return None


def run_created_at(run: dict[str, Any]) -> datetime:
    for key in ("created_at", "run_started_at", "updated_at"):
        if run.get(key):
            return parse_timestamp(run[key])
    raise ValueError("automation run has no usable creation timestamp")


def watchdog_projection(
    scheduled_runs: dict[str, Any],
    all_runs: dict[str, Any],
    *,
    now: datetime,
    maximum_age_hours: int,
) -> dict[str, Any]:
    if now.tzinfo is None:
        raise ValueError("watchdog time must include a timezone")
    if (
        isinstance(maximum_age_hours, bool)
        or not isinstance(maximum_age_hours, int)
        or maximum_age_hours < 1
    ):
        raise ValueError("maximum scheduled-run age must be a positive integer")
    now = now.astimezone(timezone.utc)
    scheduled = first_run(scheduled_runs)
    latest = first_run(all_runs)
    if scheduled is None:
        placeholder_id = now.strftime("%Y%m%dT%H%M%SZ")
        scheduled = {
            "id": f"missing-{placeholder_id}",
            "name": "ARRP Run Coordinator Bot",
            "event": "schedule",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        scheduled_age_hours: float | None = None
        scheduled_conclusion = "missing"
        scheduled_failure = (
            "No scheduled Run Coordinator workflow is available for the "
            "daily automation heartbeat."
        )
    else:
        scheduled_age_hours = (
            now - run_created_at(scheduled)
        ).total_seconds() / 3600
        scheduled_conclusion = str(scheduled.get("conclusion") or "incomplete")
        if scheduled_age_hours > maximum_age_hours:
            scheduled_failure = (
                "The latest scheduled Run Coordinator workflow is "
                f"{scheduled_age_hours:.1f} hours old, beyond the reviewed "
                f"{maximum_age_hours}-hour heartbeat boundary."
            )
        elif scheduled_conclusion != "success":
            scheduled_failure = (
                "The latest scheduled Run Coordinator workflow has not "
                f"completed successfully; conclusion is {scheduled_conclusion!r}."
            )
        else:
            scheduled_failure = ""

    latest_failure = ""
    latest_conclusion = ""
    if latest is not None:
        latest_conclusion = str(latest.get("conclusion") or "incomplete")
        latest_is_newer = (
            run_created_at(latest) >= run_created_at(scheduled)
        )
        if latest_is_newer and latest_conclusion in FAILED_CONCLUSIONS:
            latest_failure = (
                "A newer Run Coordinator workflow ended with "
                f"conclusion {latest_conclusion!r}."
            )
    failure_message = scheduled_failure or latest_failure
    healthy = not failure_message
    if scheduled_failure:
        relevant = scheduled
        projected_conclusion = scheduled_conclusion
    elif latest_failure and latest is not None:
        relevant = latest
        projected_conclusion = latest_conclusion
    else:
        relevant = (
            latest
            if latest is not None
            and run_created_at(latest) >= run_created_at(scheduled)
            else scheduled
        )
        projected_conclusion = str(
            relevant.get("conclusion") or "unknown"
        )
    projection = base_projection(
        relevant,
        status="healthy" if healthy else "failed",
        conclusion=projected_conclusion,
        updated_at=now.replace(microsecond=0).isoformat(),
        chain_prefix="cloud-watchdog",
    )
    projection["event"] = "schedule-watchdog"
    projection["heartbeat"] = {
        "checked_at": now.replace(microsecond=0).isoformat(),
        "maximum_scheduled_run_age_hours": maximum_age_hours,
        "scheduled_run_id": run_identity(scheduled),
        "scheduled_run_created_at": scheduled.get("created_at"),
        "scheduled_run_conclusion": scheduled_conclusion,
        "scheduled_run_age_hours": (
            None
            if scheduled_age_hours is None
            else round(scheduled_age_hours, 2)
        ),
    }
    projection["failure"] = (
        None
        if healthy
        else {
            "stage": "scheduled-chain-heartbeat",
            "classification": "blocking",
            "message": failure_message,
        }
    )
    projection["next_action"] = (
        "No cloud workflow recovery is required."
        if healthy
        else (
            "Inspect the scheduled Run Coordinator history, repair or rerun the "
            "latest failed or missing daily chain, and verify a new health projection."
        )
    )
    return projection


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} does not contain a JSON object")
    return value


def write_projection(path: Path, projection: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(projection, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("workflow-run", "watchdog"),
        required=True,
    )
    parser.add_argument("--event", type=Path)
    parser.add_argument("--scheduled-runs", type=Path)
    parser.add_argument("--all-runs", type=Path)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(".github/run-coordinator-bot.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "workflow-run":
        if args.event is None:
            parser.error("--event is required in workflow-run mode")
        projection = workflow_run_projection(read_object(args.event))
    else:
        if args.scheduled_runs is None or args.all_runs is None:
            parser.error(
                "--scheduled-runs and --all-runs are required in watchdog mode"
            )
        config = read_object(args.config)
        policy = config.get("automationHealthProjection")
        if not isinstance(policy, dict) or policy.get("enabled") is not True:
            raise ValueError("automation-health projection policy is unavailable")
        projection = watchdog_projection(
            read_object(args.scheduled_runs),
            read_object(args.all_runs),
            now=datetime.now(timezone.utc),
            maximum_age_hours=policy.get("maximumScheduledRunAgeHours"),
        )
    write_projection(args.output, projection)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
