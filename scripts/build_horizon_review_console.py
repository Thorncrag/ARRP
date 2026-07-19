#!/usr/bin/env python3
"""Build the candidate-only intake console and public-input lookup."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "research" / "trump-administration-preliminary-candidates.csv"
ROUTING = ROOT / "research" / "trump-administration-evidence-routing.csv"
EVIDENCE_CATALOG = ROOT / "research" / "trump-administration-legal-review-catalog.csv"
HORIZON_LOG = ROOT / "framework" / "logs" / "HORIZON_SCAN_LOG.md"
ISSUE_REGISTRY = ROOT / "inventory" / "github_issue_registry.csv"
CITED_SOURCES = ROOT / "inventory" / "sources.csv"
PENDING_SOURCES = ROOT / "inventory" / "sources-pending.csv"
OUTPUT = ROOT / "research" / "horizon-review-console" / "catalog-data.js"
PARTICIPATION_OUTPUT = ROOT / "participate" / "intake-data.js"
GITHUB_BLOB_ROOT = "https://github.com/Thorncrag/ARRP/blob/main/"
HORIZON_LOG_URL = GITHUB_BLOB_ROOT + "framework/logs/HORIZON_SCAN_LOG.md#horizon-integration-log"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-github",
        action="store_true",
        help="Refresh formal Horizon issue and Project data through authenticated gh commands.",
    )
    parser.add_argument(
        "--console-only",
        action="store_true",
        help="Rebuild the candidate console without rewriting the public-input lookup.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def split_values(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(";") if part.strip()]


def parse_links(raw: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for item in raw.split("||"):
        item = item.strip()
        if not item or "|" not in item:
            continue
        label, url = item.split("|", 1)
        if label.strip() and url.strip():
            links.append({"label": label.strip(), "url": url.strip()})
    return links


def all_source_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path, inventory_status in (
        (CITED_SOURCES, "Relied upon"),
        (PENDING_SOURCES, "Pending verification or placement"),
    ):
        for row in read_csv(path):
            if not row["Source ID"].strip():
                continue
            records.append({**row, "_inventory_status": inventory_status})
    return records


def source_index() -> dict[str, dict[str, str]]:
    return {row["Source ID"].strip(): row for row in all_source_records()}


def source_payload(row: dict[str, str]) -> dict[str, str]:
    return {
        "id": row["Source ID"].strip(),
        "inventory_status": row.get("_inventory_status", "Relied upon"),
        "type": row["Source Type"].strip(),
        "publisher": row["Authority / Publisher"].strip(),
        "title": row["Title or Description"].strip(),
        "date": row["Date"].strip(),
        "url": row["URL"].strip(),
        "proposition": row["Proposition Supported"].strip(),
        "reliability": row["Reliability Tier"].strip(),
        "reviewed": row["Reviewed?"].strip(),
        "notes": row["Notes"].strip(),
    }


def associated_record_ids(raw: str) -> set[str]:
    return {
        item.strip()
        for item in re.split(r"[;,]", raw)
        if item.strip()
    }


def sources_for_record(record_id: str) -> list[dict[str, str]]:
    matches = [
        source_payload(row)
        for row in all_source_records()
        if record_id in associated_record_ids(row["Associated Record IDs"])
    ]
    return sorted(matches, key=lambda row: row["id"])


def catalog_payload(row: dict[str, str]) -> dict[str, object]:
    links = []
    for label, field in (
        ("Source entry", "source_entry_url"),
        ("Representative case", "representative_case_url"),
        ("Official action", "official_action_url"),
    ):
        url = row[field].strip()
        if url and all(link["url"] != url for link in links):
            links.append({"label": label, "url": url})
    return {
        "id": row["catalog_id"].strip(),
        "term": row["term"].strip(),
        "type": row["record_type"].strip(),
        "title": row["action_or_policy"].strip(),
        "date": row["action_date_or_period"].strip(),
        "actor": row["responsible_actor_or_category"].strip(),
        "legal_question": row["legal_question_or_outcome"].strip(),
        "litigation_posture": row["litigation_posture"].strip(),
        "source_family": row["source_family"].strip(),
        "last_checked": row["last_checked"].strip(),
        "notes": row["notes"].strip(),
        "links": links,
    }


def evidence_catalog_index() -> dict[str, dict[str, object]]:
    return {
        row["catalog_id"].strip(): catalog_payload(row)
        for row in read_csv(EVIDENCE_CATALOG)
        if row["catalog_id"].strip()
    }


def evidence_for_record(record_id: str) -> list[dict[str, object]]:
    records = [
        catalog_payload(row)
        for row in read_csv(EVIDENCE_CATALOG)
        if record_id in associated_record_ids(row["provisional_arrp_routes"])
    ]
    return sorted(records, key=lambda row: str(row["id"]))


def strip_markdown(value: str) -> str:
    value = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("`", "")
    return re.sub(r"\s+", " ", value).strip()


def markdown_links(value: str) -> list[dict[str, str]]:
    return [
        {"label": label.strip(), "url": url.strip()}
        for label, url in re.findall(r"\[([^]]+)\]\(([^)]+)\)", value)
        if label.strip() and url.strip()
    ]


def horizon_log_records() -> dict[str, dict[str, object]]:
    fields = (
        "id",
        "decision_date",
        "original_concern",
        "decision",
        "integrated_into",
        "rationale",
        "follow_up",
    )
    records: dict[str, dict[str, object]] = {}
    for line in HORIZON_LOG.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\|\s*HOR-\d+\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(fields):
            continue
        raw = dict(zip(fields, cells))
        record_id = raw["id"]
        links: list[dict[str, str]] = []
        for field in fields[1:]:
            links.extend(markdown_links(raw[field]))
        unique_links = {
            (link["label"], link["url"]): link for link in links
        }
        records[record_id] = {
            field: strip_markdown(raw[field]) for field in fields
        }
        records[record_id]["links"] = list(unique_links.values())
    return records


def markdown_title(path: Path, content: str) -> str:
    title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return heading_match.group(1).strip() if heading_match else path.stem.replace("-", " ").title()


def research_for_record(record_id: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    identifier = re.compile(rf"(?<![A-Z0-9-]){re.escape(record_id)}(?![A-Z0-9-])")
    for path in sorted((ROOT / "research").rglob("*.md")):
        relative = path.relative_to(ROOT)
        if "horizon-review-console" in relative.parts or relative.name == "README.md":
            continue
        content = path.read_text(encoding="utf-8")
        if not identifier.search(content):
            continue
        records.append(
            {
                "title": markdown_title(path, content),
                "path": relative.as_posix(),
                "url": GITHUB_BLOB_ROOT + relative.as_posix(),
            }
        )
    return records


def candidate_records(routing: list[dict[str, str]]) -> list[dict[str, object]]:
    evidence_ids: dict[str, list[str]] = {}
    for item in routing:
        candidate_id = item["candidate_id"].strip()
        if candidate_id:
            evidence_ids.setdefault(candidate_id, []).append(item["catalog_id"])

    sources = source_index()
    catalog = evidence_catalog_index()
    records: list[dict[str, object]] = []
    for row in read_csv(CANDIDATES):
        if row["review_status"] != "preliminary-candidate":
            continue
        source_ids = list(dict.fromkeys(split_values(row["source_record_ids"])))
        supporting_sources = []
        for source_id in source_ids:
            source = sources.get(source_id)
            if not source:
                raise RuntimeError(
                    f"Preliminary candidate {row['candidate_id']} references missing source {source_id}."
                )
            supporting_sources.append(source_payload(source))
        links = parse_links(row["source_links"])
        seen_urls = {link["url"] for link in links}
        for source in supporting_sources:
            if source["url"] and source["url"] not in seen_urls:
                label = f"{source['id']} · {source['publisher'] or source['title']}"
                links.append({"label": label, "url": source["url"]})
                seen_urls.add(source["url"])
        catalog_ids = evidence_ids.get(row["candidate_id"], [])
        if not source_ids and not links and not catalog_ids:
            raise RuntimeError(
                f"Preliminary candidate {row['candidate_id']} has no supporting source or catalog record."
            )
        records.append(
            {
                "id": row["candidate_id"],
                "kind": "preliminary_candidate",
                "title": row["title"],
                "term": row["term"],
                "summary": row["institutional_defect"],
                "proposed_area": row["proposed_area"],
                "distinctness": row["distinctness_rationale"],
                "coverage": row["existing_coverage_considered"],
                "counterargument": row["counterargument"],
                "unresolved": row["unresolved_questions"],
                "recommendation": row["recommendation"],
                "source_record_ids": source_ids,
                "catalog_ids": catalog_ids,
                "evidence_records": [
                    catalog[catalog_id]
                    for catalog_id in catalog_ids
                    if catalog_id in catalog
                ],
                "supporting_sources": supporting_sources,
                "links": links,
                "last_checked": row["last_reviewed"],
            }
        )
    return sorted(records, key=lambda record: str(record["id"]))


def proposal_index_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for row in read_csv(ISSUE_REGISTRY):
        if row["Kind"].strip() != "proposal":
            continue
        issue_id = row["Object ID"].strip()
        if not issue_id:
            continue
        title = re.sub(
            rf"^{re.escape(issue_id)}\s*:\s*", "", row["GitHub Title"].strip()
        )
        canonical = row["Canonical Record"].strip()
        records.append(
            {
                "id": issue_id,
                "title": title,
                "area": issue_id.split("-", 1)[0],
                "canonical_page": f"../{canonical}" if canonical else "",
                "issue_url": row["GitHub Issue"].strip(),
            }
        )
    return sorted(records, key=lambda record: record["id"])


def run_gh_json(arguments: list[str]) -> object:
    completed = subprocess.run(
        ["gh", *arguments], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return json.loads(completed.stdout)


def existing_horizon_snapshot() -> tuple[list[dict[str, object]], str]:
    if not OUTPUT.exists():
        return [], ""
    text = OUTPUT.read_text(encoding="utf-8")
    prefix = (
        "/* Generated by scripts/build_horizon_review_console.py. */\n"
        "window.ARRP_HORIZON_REVIEW_DATA="
    )
    if not text.startswith(prefix):
        return [], ""
    try:
        payload = json.loads(text.removeprefix(prefix).removesuffix(";\n"))
    except json.JSONDecodeError:
        return [], ""
    return payload.get("horizon_records", []), payload.get("github_synced_at", "")


def horizon_snapshot(refresh: bool) -> tuple[list[dict[str, object]], str]:
    if not refresh:
        records, synced_at = existing_horizon_snapshot()
        if records:
            obsolete_queue_fields = {
                "source_task_count",
                "monitoring_task_count",
                "related_source_links",
            }
            normalized = []
            for record in records:
                cleaned = {
                    key: value
                    for key, value in record.items()
                    if key not in obsolete_queue_fields
                }
                if "issue_body_lines" in cleaned and "issue_body" not in cleaned:
                    cleaned["issue_body"] = "\n".join(cleaned.pop("issue_body_lines"))
                normalized.append(cleaned)
            return normalized, synced_at
        raise RuntimeError(
            "No preserved GitHub Horizon snapshot exists. Re-run with --refresh-github "
            "in an authenticated host context."
        )

    issues = run_gh_json(
        [
            "issue", "list", "--repo", "Thorncrag/ARRP", "--label", "kind: horizon",
            "--state", "all", "--limit", "200", "--json",
            "number,title,state,url,body,labels,createdAt,updatedAt",
        ]
    )
    project = run_gh_json(
        [
            "project", "item-list", "2", "--owner", "Thorncrag", "--limit", "500",
            "--format", "json",
        ]
    )
    project_by_number = {
        item.get("content", {}).get("number"): item
        for item in project.get("items", [])
        if "kind: horizon" in (item.get("labels") or [])
        and item.get("content", {}).get("type") == "Issue"
    }
    records: list[dict[str, object]] = []
    for issue in issues:
        project_item = project_by_number.get(issue["number"], {})
        labels = [label["name"] for label in issue.get("labels", [])]
        match = re.search(r"HOR-\d+", issue["title"])
        horizon_id = match.group(0) if match else f"Issue #{issue['number']}"
        records.append(
            {
                "id": horizon_id,
                "number": issue["number"],
                "title": re.sub(r"^HOR-\d+:\s*", "", issue["title"]).strip(),
                "full_title": issue["title"],
                "issue_state": issue["state"].title(),
                "status": project_item.get("status")
                or ("Closed" if issue["state"] == "CLOSED" else "Project status unavailable"),
                "area": project_item.get("area") or "Unassigned",
                "priority": project_item.get("priority") or "Unassigned",
                "release_blocker": project_item.get("release blocker") or "Unassigned",
                "last_audit": project_item.get("last audit") or "Not recorded",
                "next_audit": project_item.get("next audit") or "Not recorded",
                "canonical_page": project_item.get("canonical page") or issue["url"],
                "issue_url": issue["url"],
                "issue_body": issue.get("body") or "",
                "labels": labels,
                "needs_monitoring": "needs: monitoring" in labels,
                "created_at": issue["createdAt"],
                "updated_at": issue["updatedAt"],
            }
        )
    records.sort(
        key=lambda record: int(str(record["id"]).split("-")[-1])
        if str(record["id"]).startswith("HOR-") else 9999
    )
    return records, datetime.now(timezone.utc).isoformat(timespec="seconds")


def enrich_horizon_records(
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    history_by_id = horizon_log_records()
    enriched: list[dict[str, object]] = []
    for original in records:
        record = dict(original)
        record_id = str(record["id"])
        issue_body = str(record.pop("issue_body", ""))
        record["issue_body_lines"] = issue_body.splitlines()
        history = history_by_id.get(record_id)
        sources = sources_for_record(record_id)
        evidence_records = evidence_for_record(record_id)
        research = research_for_record(record_id)
        gaps: list[str] = []
        if not history:
            gaps.append("No Horizon Scan Log entry was found for this active candidate.")
        if not sources and not evidence_records:
            gaps.append("No supporting source or evidence-catalog record is associated with this candidate.")
        if not research:
            gaps.append("No identifier-linked research memorandum is currently available.")
        if str(record.get("next_audit", "")).strip() in {"", "Not recorded"}:
            gaps.append("The GitHub Project does not record a next review question.")
        if not issue_body.strip():
            gaps.append("The preserved snapshot does not include the GitHub issue body; refresh GitHub data to include it.")
        record.update(
            {
                "horizon_history": history or {},
                "horizon_log_url": HORIZON_LOG_URL,
                "supporting_sources": sources,
                "evidence_records": evidence_records,
                "research_records": research,
                "dossier_gaps": gaps,
            }
        )
        enriched.append(record)
    return enriched


def main() -> None:
    args = parse_args()
    candidates = candidate_records(read_csv(ROUTING))
    horizon_records, github_synced_at = horizon_snapshot(args.refresh_github)
    horizon_records = enrich_horizon_records(horizon_records)
    active_horizon_records = [
        record for record in horizon_records if record["issue_state"] == "Open"
    ]
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {
        "schema_version": 6,
        "generated_at": generated_at,
        "github_synced_at": github_synced_at,
        "candidate_questions": len(candidates),
        "horizon_issue_count": len(active_horizon_records),
        "records": candidates,
        "active_horizon_records": active_horizon_records,
        # The full snapshot is retained only so an ordinary rebuild can preserve
        # authoritative GitHub state without requiring Keychain access.
        "horizon_records": horizon_records,
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "/* Generated by scripts/build_horizon_review_console.py. */\n"
        f"window.ARRP_HORIZON_REVIEW_DATA={serialized.replace('</', '<\\/')}\n;".replace("\n;", ";\n"),
        encoding="utf-8",
    )

    if args.console_only:
        print(
            f"Wrote {OUTPUT.relative_to(ROOT)} with {len(candidates)} preliminary "
            f"candidates and {len(active_horizon_records)} active proposed candidates."
        )
        return

    participation_payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "proposal_index": proposal_index_records(),
        "horizon_index": [
            {
                "id": record["id"],
                "title": record["title"],
                "area": record["area"] if record["area"] != "Unassigned" else "Horizon",
                "canonical_page": record["canonical_page"],
                "issue_url": record["issue_url"],
            }
            for record in active_horizon_records
        ],
    }
    participation_serialized = json.dumps(
        participation_payload, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/")
    PARTICIPATION_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PARTICIPATION_OUTPUT.write_text(
        "/* Generated by scripts/build_horizon_review_console.py. */\n"
        f"window.ARRP_PARTICIPATION_DATA={participation_serialized};\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {OUTPUT.relative_to(ROOT)} and {PARTICIPATION_OUTPUT.relative_to(ROOT)} "
        f"with {len(candidates)} preliminary candidates and "
        f"{len(active_horizon_records)} active proposed candidates."
    )


if __name__ == "__main__":
    main()
