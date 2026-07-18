#!/usr/bin/env python3
"""Create and synchronize GitHub-native issue monitoring sub-issues.

The script turns each active proposal route in the litigation-monitoring ledger
into one ISSUE-ID-MON source-review sub-issue. Horizon routes remain on their
own Horizon issues. Run without --apply to review the planned changes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MONITORING = ROOT / "research" / "trump-administration-litigation-monitoring.csv"
REGISTRY = ROOT / "inventory" / "github_issue_registry.csv"

REPOSITORY = "Thorncrag/ARRP"
PROJECT_ID = "PVT_kwHOABOhzc4BcGD4"
STATUS_FIELD = "PVTSSF_lAHOABOhzc4BcGD4zhWxVN8"
MONITORING_STATUS = "286cda33"
AREA_FIELD = "PVTSSF_lAHOABOhzc4BcGD4zhW1Pts"
WORKSTREAM_FIELD = "PVTSSF_lAHOABOhzc4BcGD4zhW1Qa0"
PROPOSAL_DEVELOPMENT = "06336768"
CANONICAL_FIELD = "PVTF_lAHOABOhzc4BcGD4zhW3Cps"
LAST_AUDIT_FIELD = "PVTF_lAHOABOhzc4BcGD4zhW21aI"
NEXT_AUDIT_FIELD = "PVTF_lAHOABOhzc4BcGD4zhW21gE"

AREA_OPTIONS = {
    "DOJ": "87604ff1", "ELEC": "b42f90e4", "WAR": "5f9d5fc9",
    "JUD": "d07b50d9", "EMOL": "6ed7a404", "CIV": "ed7ecb93",
    "OVS": "289e47eb", "EMERG": "7a10e95c", "FUND": "fe165f00",
    "REC": "975196ae", "DOM": "78d0f232", "REG": "d4d5df04",
    "FACT": "2257e10b", "RET": "5d0e15ba", "FED": "99ecb4d8",
    "PRESS": "9d208381", "HER": "38f2186d", "RIGHTS": "d4afb302",
}


def command(arguments: list[str], *, apply: bool) -> str:
    if not apply:
        return ""
    completed = subprocess.run(
        ["gh", *arguments], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), reader.fieldnames or []


def monitor_groups(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["monitoring_status"] != "active-defined-predicate":
            continue
        for route in (part.strip() for part in row["integration_routes"].split(";")):
            if route and not route.startswith("HOR-"):
                grouped[route].append(row)
    return dict(sorted(grouped.items()))


def monitor_body(issue_id: str, parent_number: str, rows: list[dict[str, str]]) -> str:
    last_checked = max(row["last_checked"] for row in rows)
    entries = "\n".join(
        f"- `{row['monitor_id']}` — {row['action_or_policy']} "
        f"({row['litigation_posture']}; sources: {row['canonical_source_ids']})."
        for row in rows
    )
    triggers = sorted({row["revisit_trigger"] for row in rows})
    trigger_text = "\n".join(f"- {trigger}" for trigger in triggers)
    return f"""## Purpose

This is the metadata-only GitHub monitoring record for [#{parent_number}](https://github.com/{REPOSITORY}/issues/{parent_number}) (`{issue_id}`). It does not create a new proposal, finding, remedy, or score.

## Current monitoring record

The canonical source and posture ledger is [`research/trump-administration-litigation-monitoring.csv`](https://github.com/{REPOSITORY}/blob/main/research/trump-administration-litigation-monitoring.csv). Reader-facing placement belongs on `{issue_id}` or its linked evidence record when qualitatively warranted.

**Last checked:** {last_checked}

### Matters

{entries}

## Defined reassessment trigger

{trigger_text}

## Closeout

On a project-wide monitoring pass, refresh each listed matter. Close this sub-issue and remove `needs: monitoring` only when no continuing external-watch obligation remains; preserve the issue as the durable record.
"""


def parent_notice(issue_id: str, monitor_url: str, evidence_link: str | None) -> str:
    lines = ["### Supporting Record and Updates", ""]
    if evidence_link:
        lines.append(
            f"- **Additional supporting record:** [{issue_id} Evidence Record]({evidence_link})."
        )
    lines.append(
        f"- **Watching for updates:** [{issue_id}-MON]({monitor_url}) tracks pending litigation, "
        "agency action, disclosures, and other defined events that could affect this proposal. "
        "It does not alter the proposal's current analysis."
    )
    return "\n".join(lines) + "\n"


def append_registry(
    rows: list[dict[str, str]], fieldnames: list[str], additions: list[dict[str, str]]
) -> None:
    rows.extend(additions)
    with REGISTRY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def existing_github_monitors(*, apply: bool) -> dict[str, tuple[str, str]]:
    if not apply:
        return {}
    payload = command([
        "issue", "list", "--repo", REPOSITORY, "--label", "kind: source review",
        "--state", "all", "--limit", "100", "--json", "number,title,url",
    ], apply=True)
    monitors: dict[str, tuple[str, str]] = {}
    for item in json.loads(payload):
        title = item["title"]
        if "-MON:" in title:
            monitor_id = title.split(":", 1)[0]
            monitors[monitor_id] = (str(item["number"]), item["url"])
    return monitors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Create missing monitor sub-issues and update the registry.")
    parser.add_argument("--routes", help="Comma-separated proposal IDs to synchronize; defaults to every active proposal route.")
    parser.add_argument(
        "--write-parent-notices",
        action="store_true",
        help="Add the concise monitoring-record link to each eligible parent issue page.",
    )
    args = parser.parse_args()

    monitoring_rows, _ = read_csv(MONITORING)
    registry_rows, fieldnames = read_csv(REGISTRY)
    registry_by_id = {row["Object ID"]: row for row in registry_rows if row["Object ID"]}
    groups = monitor_groups(monitoring_rows)
    if args.routes:
        selected = {route.strip() for route in args.routes.split(",") if route.strip()}
        groups = {route: rows for route, rows in groups.items() if route in selected}
        missing = selected - set(groups)
        if missing:
            raise RuntimeError(f"No active proposal monitoring route(s): {', '.join(sorted(missing))}.")
    github_monitors = existing_github_monitors(apply=args.apply)
    additions: list[dict[str, str]] = []

    for issue_id, rows in groups.items():
        monitor_id = f"{issue_id}-MON"
        if monitor_id in registry_by_id:
            print(f"present {monitor_id}")
            continue
        parent = registry_by_id.get(issue_id)
        if not parent:
            raise RuntimeError(f"No GitHub registry row for active monitoring route {issue_id}.")
        area = issue_id.split("-", 1)[0]
        if area not in AREA_OPTIONS:
            raise RuntimeError(f"No Project Area option configured for {issue_id}.")
        title = f"{monitor_id}: {issue_id} External Developments Watch"
        body = monitor_body(issue_id, parent["GitHub Number"], rows)
        existing = github_monitors.get(monitor_id)
        action = "adopt" if existing else "create"
        print(f"{action} {monitor_id} ({len(rows)} monitored matters; parent #{parent['GitHub Number']})")
        if not args.apply:
            continue

        if existing:
            number, url = existing
            command([
                "issue", "edit", number, "--repo", REPOSITORY, "--title", title,
                "--body", body, "--add-label", "kind: source review", "--add-label", "needs: monitoring",
            ], apply=True)
        else:
            url = command([
                "issue", "create", "--repo", REPOSITORY, "--title", title,
                "--body", body, "--label", "kind: source review", "--label", "needs: monitoring",
            ], apply=True)
            number = url.rstrip("/").rsplit("/", 1)[-1]
            command([
                "issue", "edit", number, "--repo", REPOSITORY, "--parent", parent["GitHub Number"],
            ], apply=True)
        item_json = command([
            "project", "item-add", "2", "--owner", "Thorncrag", "--url", url, "--format", "json",
        ], apply=True)
        item_id = json.loads(item_json)["id"]
        edits = [
            ["--field-id", STATUS_FIELD, "--single-select-option-id", MONITORING_STATUS],
            ["--field-id", AREA_FIELD, "--single-select-option-id", AREA_OPTIONS[area]],
            ["--field-id", WORKSTREAM_FIELD, "--single-select-option-id", PROPOSAL_DEVELOPMENT],
            ["--field-id", CANONICAL_FIELD, "--text", url],
            ["--field-id", LAST_AUDIT_FIELD, "--text", f"Monitoring baseline ({max(row['last_checked'] for row in rows)})"],
            ["--field-id", NEXT_AUDIT_FIELD, "--text", "Defined external trigger"],
        ]
        for edit in edits:
            command([
                "project", "item-edit", "--project-id", PROJECT_ID, "--id", item_id, *edit,
            ], apply=True)
        additions.append({
            "GitHub Number": number,
            "GitHub Issue": url,
            "Object ID": monitor_id,
            "Kind": "source review",
            "GitHub Title": title,
            "Canonical Record": "research/trump-administration-litigation-monitoring.csv",
            "Parent GitHub Number": parent["GitHub Number"],
        })

    if args.apply and additions:
        append_registry(registry_rows, fieldnames, additions)
        registry_rows.extend(additions)
        registry_by_id.update({row["Object ID"]: row for row in additions})
    if args.write_parent_notices:
        if not args.apply:
            raise RuntimeError("--write-parent-notices requires --apply.")
        for issue_id in groups:
            monitor = registry_by_id.get(f"{issue_id}-MON")
            parent = registry_by_id.get(issue_id)
            if not monitor or not parent:
                raise RuntimeError(f"Cannot locate monitor and parent registry rows for {issue_id}.")
            page = ROOT / parent["Canonical Record"]
            if not page.exists() or page.suffix != ".md" or "issues" not in page.parts:
                print(f"no parent-page notice for {issue_id} (no canonical Markdown issue page)")
                continue
            original = page.read_text(encoding="utf-8")
            text = original
            area = issue_id.split("-", 1)[0]
            evidence = ROOT / "areas" / area / "evidence" / f"{issue_id}-evidence.md"
            evidence_link = f"../evidence/{evidence.name}" if evidence.exists() else None
            standard = parent_notice(issue_id, monitor["GitHub Issue"], evidence_link)
            generated_sections = re.compile(
                r"(?ms)^(?:## (?:Additional Supporting Record|Watching for Updates)|### Supporting Record and Updates)\n\n.*?(?=^## |\Z)"
            )
            text = generated_sections.sub("", text)
            manifestation = re.search(r"^## Manifestation(?:s)? of the Failure\s*$", text, re.MULTILINE)
            if not manifestation:
                print(f"no parent-page notice for {issue_id} (issue page lacks a Manifestation section)")
                continue
            following = re.search(r"^## ", text[manifestation.end():], re.MULTILINE)
            if not following:
                print(f"no parent-page notice for {issue_id} (no section after Manifestations)")
                continue
            insert_at = manifestation.end() + following.start()
            updated = text[:insert_at].rstrip() + "\n\n" + standard + "\n" + text[insert_at:]
            if updated == original:
                print(f"parent-page notice present {issue_id}")
                continue
            page.write_text(updated, encoding="utf-8")
            print(f"wrote parent-page notice {issue_id}")
    print(f"{'applied' if args.apply else 'planned'} {len(additions) if args.apply else len([key for key in groups if f'{key}-MON' not in registry_by_id])} monitor sub-issues")


if __name__ == "__main__":
    main()
