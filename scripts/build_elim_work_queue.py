#!/usr/bin/env python3
"""Compile current deterministic ARRP feeds into a compact, read-only Elim work queue."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from arrp_context import ContextError, ROOT, build_work_queue, canonical_json, contained_path
from elim_execution import reconstruct_gap_obligation_state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integrity", required=True, type=Path)
    parser.add_argument("--progress", required=True, type=Path)
    parser.add_argument("--intake", required=True, type=Path)
    parser.add_argument("--chain", required=True, type=Path)
    parser.add_argument("--recovery", type=Path)
    parser.add_argument("--run-log-reconciliation", type=Path)
    parser.add_argument("--gap-obligations", type=Path)
    parser.add_argument("--review-epoch", type=Path)
    parser.add_argument("--source-checker", type=Path)
    parser.add_argument("--case-monitor", type=Path)
    parser.add_argument("--presidential-directives", type=Path)
    parser.add_argument(
        "--overrides",
        type=Path,
        help=(
            "Optional approved local-console control state. Overrides are applied "
            "before the exact work-unit selection."
        ),
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=ROOT,
        help="Exact reviewed run root containing every queue input path.",
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        help=(
            "Exact reviewed repository root used for repository-owned policy and "
            "Run Log inputs. Defaults to --input-root for compatibility."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Write the queue atomically as a direct child of --input-root. "
            "When omitted, preserve the legacy stdout interface."
        ),
    )
    parser.add_argument("--max-age-hours", type=int, default=36)
    parser.add_argument("--source-checker-max-age-hours", type=int, default=192)
    parser.add_argument("--as-of", help="ISO-8601 timestamp for deterministic tests")
    return parser.parse_args()


def write_json(path: Path, value: object, root: Path) -> None:
    normalized_root = os.path.realpath(os.fspath(root))
    normalized_path = os.path.realpath(
        os.path.join(normalized_root, os.fspath(path))
    )
    if (
        normalized_path != normalized_root
        and not normalized_path.startswith(normalized_root + os.sep)
    ):
        raise ContextError(f"path escapes allowed root: {path}")
    if os.path.dirname(normalized_path) != normalized_root:
        raise ContextError(f"path is not a direct child of allowed root: {path}")
    destination = Path(normalized_root) / os.path.basename(normalized_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=destination.parent,
        delete=False,
    ) as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(destination)


def emit(value: object, *, output: Path | None, root: Path) -> None:
    if output is not None:
        write_json(output, value, root)
        return
    json.dump(value, sys.stdout, indent=2, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")


def main() -> int:
    args = parse_args()
    try:
        repository_root = args.repository_root or args.input_root
        now = None
        if args.as_of:
            now = datetime.fromisoformat(args.as_of.replace("Z", "+00:00"))
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
        gap_obligations = args.gap_obligations
        if gap_obligations is None:
            run_log = contained_path(
                repository_root
                / "framework"
                / "records"
                / "automation"
                / "elim-run-log.md",
                repository_root,
            )
            if not run_log.is_file():
                raise ContextError(
                    "committed Elim Run Log is required to reconstruct gap obligations"
                )
            reconstructed = reconstruct_gap_obligation_state(
                run_log.read_text(encoding="utf-8")
            )
            gap_obligations = contained_path(
                args.chain.parent / "gap-obligations-reconstructed.json",
                args.input_root,
            )
            gap_obligations.write_bytes(canonical_json(reconstructed) + b"\n")
        governance_minimum_interval_hours = 168
        coordinator_config = contained_path(
            repository_root / ".github/run-coordinator-bot.json",
            repository_root,
        )
        if coordinator_config.is_file():
            try:
                config = json.loads(
                    coordinator_config.read_text(encoding="utf-8")
                )
            except json.JSONDecodeError as error:
                raise ContextError(
                    "run-coordinator governance-discovery config is invalid JSON"
                ) from error
            governance = (
                config.get("governanceDiscovery")
                if isinstance(config, dict)
                else None
            )
            if (
                not isinstance(governance, dict)
                or governance.get("enabled") is not True
                or governance.get("mode")
                != "Project governance review and discovery"
                or governance.get("ordinarySelectionPolicy")
                != "after-ordinary-queue-clears"
                or governance.get("minimumIntervalHours") != 168
            ):
                raise ContextError(
                    "run-coordinator governance-discovery policy is invalid"
                )
            governance_minimum_interval_hours = int(
                governance["minimumIntervalHours"]
            )
        value = build_work_queue(
            integrity_path=args.integrity,
            progress_path=args.progress,
            intake_path=args.intake,
            chain_path=args.chain,
            recovery_path=args.recovery,
            run_log_reconciliation_path=args.run_log_reconciliation,
            gap_obligations_path=gap_obligations,
            review_epoch_path=args.review_epoch,
            source_checker_path=args.source_checker,
            case_monitor_path=args.case_monitor,
            presidential_directives_path=args.presidential_directives,
            overrides_path=args.overrides,
            now=now,
            max_age_hours=args.max_age_hours,
            source_checker_max_age_hours=args.source_checker_max_age_hours,
            governance_minimum_interval_hours=(
                governance_minimum_interval_hours
            ),
            input_root=args.input_root,
            repository_root=repository_root,
        )
        emit(value, output=args.output, root=args.input_root)
        return 0 if value["ready_for_elim"] else 3
    except ContextError as exc:
        value = {"schema_version": 1, "status": "blocked", "error": str(exc)}
        try:
            emit(value, output=args.output, root=args.input_root)
        except ContextError:
            json.dump(value, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
