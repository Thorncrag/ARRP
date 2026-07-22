#!/usr/bin/env python3
"""Synchronize controlled GitHub Project fields and issue-wrapper routes."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNER = "Thorncrag"
PROJECT_NUMBER = "2"
REPOSITORY = "Thorncrag/ARRP"
REGISTRY_PATH = ROOT / "inventory" / "github_issue_registry.csv"

REBASELINE_FIELD = "Rebaseline status"
CHANGE_AUDIT_FIELD = "Change audit needed"
DEVELOPMENT_LEVEL_FIELD = "Development level"

REBASELINE_MAP = {
    "current": "Current",
    "current-fixed-status": "Current fixed status",
    "soft-rebaseline-needed": "Soft rebaseline needed",
    "hard-rebaseline-needed": "Hard rebaseline needed",
    "rebaseline-complete": "Rebaseline complete",
}

CHANGE_AUDIT_MAP = {
    "false": "No",
    "no": "No",
    "0": "No",
    "true": "Yes",
    "yes": "Yes",
    "1": "Yes",
}


def development_level_from_metadata(meta: dict[str, str], current: str) -> str:
    """Return only maturity values that canonical metadata establishes unambiguously."""
    try:
        score = int(meta.get("audit_score", "0"))
    except ValueError:
        score = 0
    if score >= 75:
        return "Release candidate" if current == "Release candidate" else "Review ready"
    if score >= 1:
        return "Developed proposal"
    if meta.get("foundation_status", "").strip().lower() == "approved":
        return "Defined proposal"
    return ""


def run_gh(args: list[str]) -> str:
    proc = subprocess.run(
        ["gh", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=ROOT,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"gh {' '.join(args)} failed with exit {proc.returncode}\n{proc.stderr}"
        )
    return proc.stdout


def load_project() -> tuple[str, dict[str, dict[str, object]], list[dict[str, object]]]:
    project = json.loads(
        run_gh(["project", "view", PROJECT_NUMBER, "--owner", OWNER, "--format", "json"])
    )
    fields_raw = json.loads(
        run_gh(["project", "field-list", PROJECT_NUMBER, "--owner", OWNER, "--format", "json"])
    )
    items_raw = json.loads(
        run_gh(
            [
                "project",
                "item-list",
                PROJECT_NUMBER,
                "--owner",
                OWNER,
                "--limit",
                "300",
                "--format",
                "json",
            ]
        )
    )
    fields = {field["name"]: field for field in fields_raw["fields"]}
    return project["id"], fields, items_raw["items"]


def option_id(field: dict[str, object], option_name: str) -> str:
    for option in field.get("options", []):
        if option["name"] == option_name:
            return option["id"]
    raise KeyError(f"Option {option_name!r} not found for field {field['name']!r}")


def repo_path_from_item(item: dict[str, object]) -> Path | None:
    canonical = item.get("canonical page")
    if not isinstance(canonical, str) or "/blob/main/" not in canonical:
        return None
    rel = canonical.split("/blob/main/", 1)[1]
    path = ROOT / rel
    if not path.exists() or "/issues/" not in rel:
        return None
    return path


def front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    try:
        raw = text.split("---\n", 2)[1]
    except IndexError:
        return {}
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def set_select(
    *,
    apply: bool,
    project_id: str,
    item_id: str,
    field_id: str,
    option: str,
    option_id_value: str,
    label: str,
) -> bool:
    if not apply:
        print(f"DRY RUN: {label} -> {option}")
        return False
    run_gh(
        [
            "project",
            "item-edit",
            "--project-id",
            project_id,
            "--id",
            item_id,
            "--field-id",
            field_id,
            "--single-select-option-id",
            option_id_value,
        ]
    )
    print(f"updated: {label} -> {option}")
    return True


def set_text(
    *, apply: bool, project_id: str, item_id: str, field_id: str, value: str, label: str
) -> bool:
    if not apply:
        print(f"DRY RUN: {label} -> {value}")
        return False
    run_gh(
        [
            "project",
            "item-edit",
            "--project-id",
            project_id,
            "--id",
            item_id,
            "--field-id",
            field_id,
            "--text",
            value,
        ]
    )
    print(f"updated: {label} -> {value}")
    return True


def set_number(
    *, apply: bool, project_id: str, item_id: str, field_id: str, value: int, label: str
) -> bool:
    if not apply:
        print(f"DRY RUN: {label} -> {value}")
        return False
    run_gh(
        [
            "project",
            "item-edit",
            "--project-id",
            project_id,
            "--id",
            item_id,
            "--field-id",
            field_id,
            "--number",
            str(value),
        ]
    )
    print(f"updated: {label} -> {value}")
    return True


def registry_rows() -> dict[int, dict[str, str]]:
    with REGISTRY_PATH.open(newline="", encoding="utf-8") as handle:
        return {
            int(row["GitHub Number"]): row
            for row in csv.DictReader(handle)
            if row.get("GitHub Number", "").isdigit()
        }


def canonical_path(row: dict[str, str]) -> Path | None:
    value = row.get("Canonical Record", "").strip()
    path = ROOT / value
    return path if value and path.is_file() and "/issues/" in value else None


def ensure_issue_wrapper(
    *, apply: bool, number: int, row: dict[str, str], path: Path | None
) -> bool:
    if row.get("Kind") not in {"proposal", "horizon"}:
        return False
    body = json.loads(run_gh(["issue", "view", str(number), "--repo", REPOSITORY, "--json", "body"]))["body"]
    object_id = row.get("Object ID", "").strip()
    record = row.get("Canonical Record", "").strip()
    canonical_url = f"https://github.com/{REPOSITORY}/blob/main/{record}" if record else ""
    additions: list[str] = []
    if row.get("Kind") == "proposal" and canonical_url and canonical_url not in body:
        label = "Proposal page" if path is not None else "Canonical project record"
        additions.append(f"- [{label}]({canonical_url})")
    if object_id and object_id not in body:
        label = "Horizon ID" if row.get("Kind") == "horizon" else "Object ID"
        additions.append(f"- {label}: `{object_id}`")
    if not additions:
        return False
    heading = "## Canonical Project Page"
    if heading in body:
        updated = body.replace(heading, heading + "\n\n" + "\n".join(additions), 1)
    else:
        updated = heading + "\n\n" + "\n".join(additions) + "\n\n" + body.lstrip()
    if not apply:
        print(f"DRY RUN: GitHub issue #{number} wrapper add -> {'; '.join(additions)}")
        return True
    run_gh(["issue", "edit", str(number), "--repo", REPOSITORY, "--body", updated])
    print(f"updated: GitHub issue #{number} wrapper")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes to GitHub")
    parser.add_argument(
        "--all-controlled",
        action="store_true",
        help="also synchronize canonical page, Score, Last audit, and Next audit",
    )
    parser.add_argument(
        "--issue-wrappers",
        action="store_true",
        help="add missing canonical-page and object-ID routes to active GitHub issue wrappers",
    )
    args = parser.parse_args()

    project_id, fields, items = load_project()
    registry = registry_rows()
    rebaseline_field = fields[REBASELINE_FIELD]
    change_field = fields[CHANGE_AUDIT_FIELD]
    development_field = fields[DEVELOPMENT_LEVEL_FIELD]

    planned = 0
    updated = 0
    skipped = 0

    for item in items:
        content = item.get("content") or {}
        number = content.get("number") if isinstance(content, dict) else None
        row = registry.get(int(number)) if isinstance(number, int) else None
        path = canonical_path(row) if row else repo_path_from_item(item)
        if args.issue_wrappers and row:
            wrapper_needed = ensure_issue_wrapper(
                apply=False, number=int(number), row=row, path=path
            )
            planned += int(wrapper_needed)
            if args.apply and wrapper_needed:
                updated += int(
                    ensure_issue_wrapper(apply=True, number=int(number), row=row, path=path)
                )
        label = f"#{number} {path.relative_to(ROOT) if path else (row or {}).get('Canonical Record', '')}"
        if args.all_controlled and row and row.get("Kind") in {"proposal", "horizon"}:
            base_text = {
                "Canonical page": (
                    f"https://github.com/{REPOSITORY}/blob/main/{row.get('Canonical Record', '').strip()}"
                    if row.get("Kind") == "proposal" and row.get("Canonical Record", "").strip()
                    else row.get("GitHub Issue", "").strip()
                    if row.get("Kind") == "horizon"
                    else ""
                ),
            }
            for field_name, value in base_text.items():
                if value and str(item.get(field_name.lower()) or "") != value:
                    planned += 1
                    updated += set_text(
                        apply=args.apply,
                        project_id=project_id,
                        item_id=item["id"],
                        field_id=fields[field_name]["id"],
                        value=value,
                        label=f"{label} {field_name}",
                    )
        if path is None:
            skipped += 1
            continue

        meta = front_matter(path)

        if args.all_controlled and row:
            controlled_text: dict[str, str] = {}
            if meta.get("audit_last_type") and meta.get("audit_last_date"):
                controlled_text["Last audit"] = (
                    f"{meta.get('audit_last_type')} ({meta.get('audit_last_date')})"
                )
            if meta.get("audit_next"):
                controlled_text["Next audit"] = meta["audit_next"].strip()
            for field_name, value in controlled_text.items():
                if value and str(item.get(field_name.lower()) or "") != value:
                    planned += 1
                    updated += set_text(
                        apply=args.apply,
                        project_id=project_id,
                        item_id=item["id"],
                        field_id=fields[field_name]["id"],
                        value=value,
                        label=f"{label} {field_name}",
                    )
            if meta.get("audit_score", "").isdigit():
                score = int(meta["audit_score"])
                if item.get("score") != score:
                    planned += 1
                    updated += set_number(
                        apply=args.apply,
                        project_id=project_id,
                        item_id=item["id"],
                        field_id=fields["Score"]["id"],
                        value=score,
                        label=f"{label} Score",
                    )
            current_level = str(item.get(DEVELOPMENT_LEVEL_FIELD.lower()) or "")
            development_level = development_level_from_metadata(meta, current_level)
            if development_level and current_level != development_level:
                planned += 1
                updated += set_select(
                    apply=args.apply,
                    project_id=project_id,
                    item_id=item["id"],
                    field_id=development_field["id"],
                    option=development_level,
                    option_id_value=option_id(development_field, development_level),
                    label=f"{label} {DEVELOPMENT_LEVEL_FIELD}",
                )

        rebaseline_raw = meta.get("audit_rebaseline_status", "").strip().lower()
        rebaseline_option = REBASELINE_MAP.get(rebaseline_raw)
        if rebaseline_option:
            if item.get(REBASELINE_FIELD.lower()) != rebaseline_option:
                planned += 1
                updated += set_select(
                    apply=args.apply,
                    project_id=project_id,
                    item_id=item["id"],
                    field_id=rebaseline_field["id"],
                    option=rebaseline_option,
                    option_id_value=option_id(rebaseline_field, rebaseline_option),
                    label=f"{label} {REBASELINE_FIELD}",
                )

        change_raw = meta.get("change_audit_needed", "false").strip().lower()
        change_option = CHANGE_AUDIT_MAP.get(change_raw)
        if change_option:
            if item.get(CHANGE_AUDIT_FIELD.lower()) != change_option:
                planned += 1
                updated += set_select(
                    apply=args.apply,
                    project_id=project_id,
                    item_id=item["id"],
                    field_id=change_field["id"],
                    option=change_option,
                    option_id_value=option_id(change_field, change_option),
                    label=f"{label} {CHANGE_AUDIT_FIELD}",
                )


    print(
        f"summary: planned={planned} updated={updated} skipped={skipped} apply={args.apply}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
