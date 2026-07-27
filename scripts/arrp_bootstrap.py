#!/usr/bin/env python3
"""Disabled-by-default bootstrap for the ARRP local transaction runner."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def runner_path() -> Path:
    return Path(__file__).resolve().with_name("arrp_nightly.py")


def build_command(args: argparse.Namespace) -> list[str]:
    command = [sys.executable, str(runner_path())]
    if args.fixture:
        command.extend(["--fixture", str(args.fixture)])
    if args.canonical_path:
        command.extend(["--canonical-path", str(args.canonical_path)])
    if args.state_root:
        command.extend(["--state-root", str(args.state_root)])
    if args.manual:
        command.append("--manual")
    if args.dry_run:
        command.append("--dry-run")
    if args.run_id:
        command.extend(["--run-id", args.run_id])
    if args.p5_supervised_plan:
        command.extend(["--p5-supervised-plan", str(args.p5_supervised_plan)])
    return command


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--canonical-path", type=Path)
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--manual", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-id")
    parser.add_argument("--p5-supervised-plan", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.p5_supervised_plan is not None:
        if args.fixture is not None or args.dry_run or not args.manual:
            print(
                "P5 supervised bootstrap requires --manual without fixture or dry-run",
                file=sys.stderr,
            )
            return 64
    elif args.fixture is None and not (args.manual and args.dry_run):
        print(
            "P1_DISABLED: bootstrap requires --fixture or explicit --manual --dry-run",
            file=sys.stderr,
        )
        return 64
    return subprocess.run(build_command(args), check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
