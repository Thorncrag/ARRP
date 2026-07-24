#!/usr/bin/env python3
"""Emit deterministic Elim validation, score, or closeout JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from arrp_context import ContextError, load_json
from elim_execution import calculate_score, compile_closeout, summarize_validation, validation_plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validation-plan")
    validate.add_argument("--task-type", required=True)
    validate.add_argument("files", nargs="*")
    summary = commands.add_parser("validation-summary")
    summary.add_argument("--plan", required=True, type=Path)
    summary.add_argument("--results", required=True, type=Path)
    score = commands.add_parser("score")
    score.add_argument("--input", required=True, type=Path)
    close = commands.add_parser("closeout")
    close.add_argument("--input", required=True, type=Path)
    close.add_argument("--queue-sha256", required=True)
    close.add_argument("--context-sha256", required=True)
    close.add_argument("--prior-state", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "validation-plan":
            result = validation_plan(args.files, args.task_type)
        elif args.command == "validation-summary":
            result = summarize_validation(load_json(args.plan), load_json(args.results))
        elif args.command == "score":
            result = calculate_score(load_json(args.input))
        else:
            result = compile_closeout(
                load_json(args.input),
                queue_sha256=args.queue_sha256,
                context_sha256=args.context_sha256,
                prior_state=load_json(args.prior_state) if args.prior_state else None,
            )
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    except ContextError as exc:
        json.dump({"schema_version": 1, "status": "blocked", "error": str(exc)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
