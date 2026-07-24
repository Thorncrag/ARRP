#!/usr/bin/env python3
"""Protect the user reserve and track Elim's soft per-run usage target."""

from __future__ import annotations

import argparse
import json
import select
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


DEFAULT_RESERVE_PERCENT = 15
DEFAULT_SOFT_TARGET_PERCENT = 10
DEFAULT_TIMEOUT_SECONDS = 20
RESET_TIME_JITTER_SECONDS = 5
WINDOW_CHANGE_RECHECKS = 2
WINDOW_CHANGE_RECHECK_DELAY_SECONDS = 1
CODEX_EXECUTABLE = Path("/Applications/ChatGPT.app/Contents/Resources/codex")


class UsageGateError(RuntimeError):
    """Raised when the official rate-limit state cannot be read confidently."""


class RateLimitWindowChanged(UsageGateError):
    """Raised when a material window change requires confirmation."""


def iso_timestamp(unix_seconds: int) -> str:
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc).isoformat(timespec="seconds")


def fetch_rate_limits(codex_executable: str, timeout_seconds: int) -> dict[str, Any]:
    """Read the first-party account/rateLimits/read app-server response."""
    process = subprocess.Popen(
        [codex_executable, "app-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    if process.stdin is None or process.stdout is None:
        process.kill()
        raise UsageGateError("Codex app-server did not expose its JSONL transport")

    requests = (
        {
            "method": "initialize",
            "id": 0,
            "params": {
                "clientInfo": {
                    "name": "arrp_elim_usage_gate",
                    "title": "ARRP Elim Usage Gate",
                    "version": "1.0.0",
                }
            },
        },
        {"method": "initialized", "params": {}},
        {"method": "account/rateLimits/read", "id": 1, "params": None},
    )

    try:
        for request in requests:
            process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
        process.stdin.flush()

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            ready, _, _ = select.select([process.stdout], [], [], min(1, deadline - time.monotonic()))
            if not ready:
                continue
            line = process.stdout.readline()
            if not line:
                break
            try:
                response = json.loads(line)
            except json.JSONDecodeError:
                continue
            if response.get("id") != 1:
                continue
            if response.get("error"):
                message = response["error"].get("message", "unknown app-server error")
                raise UsageGateError(f"Codex rate-limit request failed: {message}")
            result = response.get("result")
            if not isinstance(result, dict):
                raise UsageGateError("Codex returned no rate-limit result")
            return result
        raise UsageGateError("Codex rate-limit request timed out")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def rate_limit_snapshots(payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    by_id = payload.get("rateLimitsByLimitId")
    if isinstance(by_id, dict) and by_id:
        snapshots = [
            (str(limit_id), snapshot)
            for limit_id, snapshot in sorted(by_id.items())
            if isinstance(snapshot, dict)
        ]
        if snapshots:
            return snapshots

    fallback = payload.get("rateLimits")
    if isinstance(fallback, dict):
        limit_id = str(fallback.get("limitId") or "default")
        return [(limit_id, fallback)]
    return []


def evaluate_rate_limits(payload: dict[str, Any], reserve_percent: int) -> dict[str, Any]:
    """Normalize all applicable hard-limit windows and apply the protected reserve."""
    windows: list[dict[str, Any]] = []
    blockers: list[str] = []

    for fallback_id, snapshot in rate_limit_snapshots(payload):
        limit_id = str(snapshot.get("limitId") or fallback_id)
        limit_name = str(snapshot.get("limitName") or limit_id)
        if snapshot.get("rateLimitReachedType"):
            blockers.append(f"{limit_name}: {snapshot['rateLimitReachedType']}")
        if snapshot.get("spendControlReached") is True:
            blockers.append(f"{limit_name}: spend control reached")

        for window_name in ("primary", "secondary"):
            window = snapshot.get(window_name)
            if window is None:
                continue
            if not isinstance(window, dict):
                raise UsageGateError(f"{limit_name} {window_name} window is unreadable")
            used_percent = window.get("usedPercent")
            resets_at = window.get("resetsAt")
            if not isinstance(used_percent, int) or not 0 <= used_percent <= 100:
                raise UsageGateError(f"{limit_name} {window_name} usage percentage is unavailable")
            if not isinstance(resets_at, int) or resets_at <= 0:
                raise UsageGateError(f"{limit_name} {window_name} reset time is unavailable")
            windows.append(
                {
                    "limitId": limit_id,
                    "limitName": limit_name,
                    "window": window_name,
                    "usedPercent": used_percent,
                    "remainingPercent": 100 - used_percent,
                    "resetsAt": resets_at,
                    "resetsAtUtc": iso_timestamp(resets_at),
                    "windowDurationMins": window.get("windowDurationMins"),
                }
            )

        individual = snapshot.get("individualLimit")
        if individual is not None:
            if not isinstance(individual, dict):
                raise UsageGateError(f"{limit_name} individual limit is unreadable")
            remaining = individual.get("remainingPercent")
            resets_at = individual.get("resetsAt")
            if not isinstance(remaining, int) or not 0 <= remaining <= 100:
                raise UsageGateError(f"{limit_name} individual remaining percentage is unavailable")
            if not isinstance(resets_at, int) or resets_at <= 0:
                raise UsageGateError(f"{limit_name} individual reset time is unavailable")
            windows.append(
                {
                    "limitId": limit_id,
                    "limitName": limit_name,
                    "window": "individual",
                    "usedPercent": 100 - remaining,
                    "remainingPercent": remaining,
                    "resetsAt": resets_at,
                    "resetsAtUtc": iso_timestamp(resets_at),
                    "windowDurationMins": None,
                }
            )

    if not windows:
        raise UsageGateError("Codex returned no applicable rate-limit windows")

    reserve_hits = [
        f"{window['limitName']} {window['window']}: {window['remainingPercent']}% remaining"
        for window in windows
        if window["remainingPercent"] <= reserve_percent
    ]
    blockers.extend(reserve_hits)
    status = "abort" if blockers else "pass"
    return {
        "status": status,
        "reservePercent": reserve_percent,
        "checkedAtUtc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "lowestRemainingPercent": min(window["remainingPercent"] for window in windows),
        "windows": windows,
        "blockers": blockers,
    }


def window_key(window: dict[str, Any]) -> str:
    return f"{window['limitId']}:{window['window']}"


def apply_run_budget(
    result: dict[str, Any],
    baseline_path: Path,
    soft_target_percent: int,
) -> dict[str, Any]:
    """Create or compare a per-run baseline without weakening the absolute reserve."""
    current_windows = {window_key(window): window for window in result["windows"]}
    if not baseline_path.exists():
        baseline = {
            "schemaVersion": 1,
            "createdAtUtc": result["checkedAtUtc"],
            "windows": {
                key: {
                    "usedPercent": window["usedPercent"],
                    "resetsAt": window["resetsAt"],
                }
                for key, window in current_windows.items()
            },
        }
        try:
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            with baseline_path.open("x", encoding="utf-8") as handle:
                json.dump(baseline, handle, indent=2, sort_keys=True)
                handle.write("\n")
        except OSError as error:
            raise UsageGateError(f"could not create run-usage baseline: {error}") from error
    else:
        try:
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise UsageGateError(f"run-usage baseline is unreadable: {error}") from error

    baseline_windows = baseline.get("windows")
    if not isinstance(baseline_windows, dict) or not baseline_windows:
        raise UsageGateError("run-usage baseline contains no windows")
    if set(baseline_windows) != set(current_windows):
        raise RateLimitWindowChanged("applicable rate-limit windows changed during the run")

    spent_by_window: dict[str, int] = {}
    for key, current in current_windows.items():
        starting = baseline_windows.get(key)
        if not isinstance(starting, dict):
            raise UsageGateError(f"run-usage baseline window {key} is unreadable")
        starting_used = starting.get("usedPercent")
        starting_reset = starting.get("resetsAt")
        if not isinstance(starting_used, int) or not isinstance(starting_reset, int):
            raise UsageGateError(f"run-usage baseline window {key} is incomplete")
        reset_difference = abs(current["resetsAt"] - starting_reset)
        if reset_difference > RESET_TIME_JITTER_SECONDS:
            raise RateLimitWindowChanged(
                f"rate-limit window {key} changed materially during the run"
            )
        if current["usedPercent"] < starting_used:
            raise RateLimitWindowChanged(
                f"rate-limit usage for {key} moved backward during the run"
            )
        spent_by_window[key] = current["usedPercent"] - starting_used

    highest_spent = max(spent_by_window.values(), default=0)
    result["runBudget"] = {
        "baselinePath": str(baseline_path),
        "softTargetPercent": soft_target_percent,
        "highestSpentPercent": highest_spent,
        "spentPercentByWindow": spent_by_window,
    }
    soft_target_reached = highest_spent >= soft_target_percent
    reserve_buffer_floor = result["reservePercent"] + soft_target_percent
    result["runBudget"]["softTargetReached"] = soft_target_reached
    result["runBudget"]["reserveBufferFloorPercent"] = reserve_buffer_floor
    if soft_target_reached and result["lowestRemainingPercent"] <= reserve_buffer_floor:
        result["status"] = "abort"
        result["blockers"].append(
            "soft per-run target reached within the protected reserve buffer: "
            f"{highest_spent}% spent and {result['lowestRemainingPercent']}% remaining"
        )
    return result


def read_usage_with_window_confirmation(
    fetcher: Callable[[], dict[str, Any]],
    reserve_percent: int,
    baseline_path: Path | None,
    soft_target_percent: int,
    *,
    window_change_rechecks: int = WINDOW_CHANGE_RECHECKS,
    recheck_delay_seconds: float = WINDOW_CHANGE_RECHECK_DELAY_SECONDS,
) -> dict[str, Any]:
    """Retry only material window-change signals; never retry through a reserve hit."""
    if window_change_rechecks < 0:
        raise ValueError("window-change rechecks cannot be negative")

    transient_window_changes = 0
    for attempt in range(window_change_rechecks + 1):
        payload = fetcher()
        result = evaluate_rate_limits(payload, reserve_percent)

        # The protected reserve and any backend hard-stop state take precedence
        # over window-change confirmation and return immediately.
        if result["status"] != "pass" or baseline_path is None:
            return result

        try:
            result = apply_run_budget(result, baseline_path, soft_target_percent)
        except RateLimitWindowChanged:
            if attempt >= window_change_rechecks:
                raise
            transient_window_changes += 1
            if recheck_delay_seconds:
                time.sleep(recheck_delay_seconds)
            continue

        if transient_window_changes:
            result["windowChangeRechecks"] = transient_window_changes
        return result

    raise AssertionError("window-change confirmation loop ended unexpectedly")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reserve-percent", type=int, default=DEFAULT_RESERVE_PERCENT)
    parser.add_argument(
        "--soft-target-percent",
        "--max-run-percent",
        dest="soft_target_percent",
        type=int,
        default=DEFAULT_SOFT_TARGET_PERCENT,
    )
    parser.add_argument("--run-baseline", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 0 <= args.reserve_percent <= 100:
        print(json.dumps({"status": "unavailable", "error": "reserve percent must be 0 through 100"}))
        return 3
    if not 1 <= args.soft_target_percent <= 100:
        print(
            json.dumps(
                {"status": "unavailable", "error": "soft target percent must be 1 through 100"}
            )
        )
        return 3
    if args.timeout_seconds <= 0:
        print(json.dumps({"status": "unavailable", "error": "timeout must be positive"}))
        return 3
    if not CODEX_EXECUTABLE.is_file():
        print(
            json.dumps(
                {
                    "status": "unavailable",
                    "error": f"trusted Codex executable was not found at {CODEX_EXECUTABLE}",
                }
            )
        )
        return 3

    try:
        result = read_usage_with_window_confirmation(
            lambda: fetch_rate_limits(str(CODEX_EXECUTABLE), args.timeout_seconds),
            args.reserve_percent,
            args.run_baseline,
            args.soft_target_percent,
        )
    except (OSError, UsageGateError) as error:
        result = {
            "status": "unavailable",
            "reservePercent": args.reserve_percent,
            "checkedAtUtc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
            "error": str(error),
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 3

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
