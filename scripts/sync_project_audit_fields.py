#!/usr/bin/env python3
"""Sync GitHub Project audit-control fields from issue-page metadata."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNER = "Thorncrag"
PROJECT_NUMBER = "2"

REBASELINE_FIELD = "Rebaseline status"
CHANGE_AUDIT_FIELD = "Change audit needed"

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes to GitHub")
    args = parser.parse_args()

    project_id, fields, items = load_project()
    rebaseline_field = fields[REBASELINE_FIELD]
    change_field = fields[CHANGE_AUDIT_FIELD]

    planned = 0
    updated = 0
    skipped = 0

    for item in items:
        path = repo_path_from_item(item)
        if path is None:
            skipped += 1
            continue

        meta = front_matter(path)
        label = f"#{item['content']['number']} {path.relative_to(ROOT)}"

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
