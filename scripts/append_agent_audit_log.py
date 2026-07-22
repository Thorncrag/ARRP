#!/usr/bin/env python3
"""Append one structured persistent-agent provenance entry."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "framework" / "logs" / "AGENT_AUDIT_LOG.md"


def entry(args: argparse.Namespace) -> str:
    timestamp = args.timestamp or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    heading_date = timestamp[:10]
    return f"""

### {heading_date} — {args.issue_task} — {args.task_type}

| Field | Entry |
| --- | --- |
| Date/time | {timestamp} |
| Agent | {args.agent} |
| Run ID | {args.run_id} |
| Unit ID | {args.unit_id} |
| Trigger | {args.trigger} |
| Task type | {args.task_type} |
| Outcome | {args.outcome} |
| Issue/task | {args.issue_task} |
| Issue page | {args.issue_page} |
| Audit history | {args.audit_history} |
| Proposal page | {args.proposal_page} |
| Tier | {args.tier} |
| Files changed | {args.files_changed} |
| Validation | {args.validation} |
| Commit | {args.commit} |
| Push status | {args.push_status} |
| Rollback notes | {args.rollback_notes} |
| Blockers/skipped checks | {args.blockers} |
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--unit-id", default="N/A")
    parser.add_argument("--trigger", required=True)
    parser.add_argument("--task-type", required=True)
    parser.add_argument("--outcome", required=True)
    parser.add_argument("--issue-task", required=True)
    parser.add_argument("--issue-page", default="N/A")
    parser.add_argument("--audit-history", default="N/A")
    parser.add_argument("--proposal-page", default="N/A")
    parser.add_argument("--tier", default="none")
    parser.add_argument("--files-changed", required=True)
    parser.add_argument("--validation", required=True)
    parser.add_argument("--commit", default="This automation commit")
    parser.add_argument("--push-status", required=True)
    parser.add_argument("--rollback-notes", required=True)
    parser.add_argument("--blockers", default="None.")
    parser.add_argument("--timestamp")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.log.exists():
        raise FileNotFoundError(args.log)
    with args.log.open("a", encoding="utf-8") as handle:
        handle.write(entry(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
