#!/usr/bin/env python3
"""Create GitHub tracking issues from the historical import ledger.

This legacy helper creates issue wrappers and attaches them to the GitHub
Project, but Project fields remain authoritative and must be populated there.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "inventory" / "github_issue_import.csv"
REPO = "Thorncrag/ARRP"


def run_gh(args: list[str], input_text: str | None = None) -> str:
    proc = subprocess.run(
        ["gh", *args],
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        cwd=ROOT,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"gh {' '.join(args)} failed with exit {proc.returncode}\n{proc.stderr}"
        )
    return proc.stdout.strip()


def issue_body(row: dict[str, str]) -> str:
    return "\n".join(
        [
            "## Canonical Record",
            "",
            f"- Repo record: `{row['Canonical Record']}`",
            f"- Object ID: `{row['Object ID']}`",
            "",
            "## Workflow Purpose",
            "",
            "This GitHub issue is the public workflow wrapper for the ARRP proposal. "
            "Discussion, assignment, and contributor-facing workflow should happen "
            "here. Structured workflow metadata belongs in GitHub Project fields.",
            "",
            "The repository remains the authoritative substantive record for the "
            "proposal text, audit history, source records, and proposed legislation.",
            "",
            "## Next Step",
            "",
            "Use the Project fields to identify whether this proposal "
            "needs development, source review, audit work, release review, or deferral.",
        ]
    )


def kind_label(row: dict[str, str]) -> str:
    return f"kind: {row['Kind'].strip()}"


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    limit = None
    for arg in sys.argv[1:]:
        if arg.startswith("--limit="):
            limit = int(arg.split("=", 1)[1])

    with LEDGER.open(newline="") as f:
        rows = list(csv.DictReader(f))

    existing_raw = run_gh(
        ["issue", "list", "--repo", REPO, "--state", "all", "--limit", "1000", "--json", "title,url"]
    )
    existing = {item["title"]: item["url"] for item in json.loads(existing_raw)}

    changed = False
    created = 0
    matched = 0
    processed = 0
    skipped = 0

    for row in rows:
        if row["Kind"] != "proposal" or row["Import Status"] == "created":
            skipped += 1
            continue

        title = row["GitHub Title"]
        if title in existing:
            row["GitHub Issue"] = existing[title]
            row["Import Status"] = "created"
            changed = True
            matched += 1
            processed += 1
            continue

        if limit is not None and processed >= limit:
            skipped += 1
            continue

        labels = [kind_label(row)]
        if dry_run:
            print(f"DRY RUN: would create {title} [{', '.join(labels)}]")
            processed += 1
            skipped += 1
            continue

        args = [
            "issue",
            "create",
            "--repo",
            REPO,
            "--title",
            title,
            "--body",
            issue_body(row),
            "--project",
            "American Restoration and Resilience Project",
        ]
        for label in labels:
            args.extend(["--label", label])
        url = run_gh(args)
        row["GitHub Issue"] = url
        row["Import Status"] = "created"
        existing[title] = url
        changed = True
        created += 1
        processed += 1
        print(f"created {row['Object ID']}: {url}", flush=True)

    if changed and not dry_run:
        with LEDGER.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    print(f"summary: created={created} matched={matched} skipped={skipped} dry_run={dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
