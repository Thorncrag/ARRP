#!/usr/bin/env python3
"""Build the internal intake console and its separate public-input lookup."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "research" / "trump-administration-preliminary-candidates.csv"
ROUTING = ROOT / "research" / "trump-administration-evidence-routing.csv"
CATALOG = ROOT / "research" / "trump-administration-legal-review-catalog.csv"
MEDIA = ROOT / "research" / "trump-administration-media-review-intake.csv"
EXISTING_ISSUE_INTEGRATION = ROOT / "research" / "existing-issue-evidence-integration.csv"
LITIGATION_MONITORING = ROOT / "research" / "trump-administration-litigation-monitoring.csv"
SOURCE_UNIVERSE = ROOT / "research" / "trump-administration-source-universe.csv"
ISSUE_REGISTRY = ROOT / "inventory" / "github_issue_registry.csv"
CITED_SOURCES = ROOT / "inventory" / "sources.csv"
PENDING_SOURCES = ROOT / "inventory" / "sources-pending.csv"
OUTPUT = ROOT / "research" / "horizon-review-console" / "catalog-data.js"
PARTICIPATION_OUTPUT = ROOT / "participate" / "intake-data.js"


COMPLETED_ADJUDICATION = {
    "completed_on": "2026-07-16",
    "baseline_records": 1322,
    "priority_records": 56,
    "records": 1266,
    "episodes": 1250,
    "integration_records": 160,
    "monitoring_records": 178,
    "monitoring_episodes": 174,
    "redundant_records": 109,
    "excluded_records": 819,
    "source_records_added": 373,
}


INTEGRATION_STAGES = {
    "awaiting-primary-verification-and-reader-placement": (
        "Verify and assess for placement",
        "Codex must verify the strongest underlying record, compare it with the receiving issue, and add it only when it materially improves the issue's evidence.",
    ),
    "verified-high-value-awaiting-issue-development": (
        "Hold for receiving-issue development",
        "The evidence is already verified, but its receiving issue is not developed enough for responsible reader-facing placement.",
    ),
}


SOURCE_ROLES = {
    "adjudicated-2026-07-16": (
        "Included in completed source scan",
        "No current action. Its individual records were screened and routed; this does not decide legality or proposal merit.",
    ),
    "registered-as-primary-backbone": (
        "Official primary-source collection",
        "Use it to verify executive actions when a related issue or episode is developed.",
    ),
    "registered-for-domain-ingestion": (
        "Specialist source for future ingestion",
        "Codex should review this subject-specific source during the next relevant domain scan.",
    ),
    "registered-for-ingestion": (
        "Specialist source for future ingestion",
        "Codex should ingest and route its relevant records in a future source-development pass.",
    ),
    "registered-for-official-findings": (
        "Official findings source",
        "Codex should use it to locate authoritative findings relevant to existing or future issues.",
    ),
    "registered-as-case-backbone": (
        "Case and docket reference",
        "Use it to retrieve filings and normalize procedural posture when litigation requires review.",
    ),
    "registered-for-final-posture-normalization": (
        "Case and docket reference",
        "Use it to verify final Supreme Court posture before characterizing litigation outcomes.",
    ),
    "registered-for-case-normalization": (
        "Case and docket reference",
        "Use it to identify and normalize court-order compliance episodes before publication.",
    ),
    "registered-as-safety-net": (
        "Case and docket reference",
        "Use it as a completeness check when a case or executive action may be missing elsewhere.",
    ),
    "registered-for-comparison": (
        "Comparison source",
        "Use it to test whether the principal catalog missed cases or materially different coverage.",
    ),
    "already-crosswalked": (
        "Existing project source",
        "No new ingestion is required; the project already maintains the corresponding crosswalk.",
    ),
    "registered-existing-crosswalk-source": (
        "Existing project source",
        "Maintain it through the existing project crosswalk rather than a separate intake queue.",
    ),
    "registered-existing-horizon-source": (
        "Existing project source",
        "Maintain it through its existing Horizon record rather than a separate intake queue.",
    ),
    "registered-for-crosswalk-refresh": (
        "Existing project source",
        "Use it when the existing Project 2025 crosswalk is next refreshed.",
    ),
    "registered-for-two-source-media-corroboration": (
        "Independent reporting source",
        "Use it with a second reliable outlet to identify or corroborate an episode; then seek a primary record.",
    ),
    "registered-for-doctrine-and-legislation": (
        "Legal and legislative reference",
        "Use it to verify doctrine, statutory background, and prior legislation when relevant.",
    ),
    "registered-as-gap-source": (
        "Targeted evidence source",
        "Use this official report for the identified enforcement gap when the receiving issue is developed.",
    ),
    "reviewed-2026-07-15": (
        "Reviewed source directory",
        "No immediate action. Revisit individual listed resources only when a coverage gap appears.",
    ),
}


MEDIA_STAGES = {
    "existing-manifestation": (
        "Route to an existing proposal",
        "Codex should verify the strongest sources and decide whether the episode materially improves the identified proposal.",
    ),
    "existing-proposal-likely": (
        "Confirm the existing-proposal route",
        "Codex should complete duplicate and remedy-fit review before placing the episode.",
    ),
    "incorporated-existing-proposal": (
        "Already incorporated",
        "No current action. The episode has already been placed in its existing proposal.",
    ),
    "existing-horizon-monitor": (
        "Monitor through an existing Horizon record",
        "No current action. Revisit it only when the Horizon record's external predicate occurs.",
    ),
    "coverage-review-needed": (
        "Codex scope review needed",
        "Codex should determine whether the episode identifies a repairable institutional defect or belongs in an existing proposal.",
    ),
    "political-or-constitutional-boundary": (
        "Codex scope review needed",
        "Codex should apply the political-failure and constitutional-remedy boundaries before asking the user for any project-scope decision.",
    ),
}


ACTIONABLE_SOURCE_STATUSES = {
    "registered-for-domain-ingestion",
    "registered-for-ingestion",
    "registered-for-official-findings",
    "registered-for-comparison",
    "registered-for-crosswalk-refresh",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-github",
        action="store_true",
        help="Refresh Horizon issue and Project-field data through authenticated gh commands.",
    )
    return parser.parse_args()


def run_gh_json(arguments: list[str]) -> object:
    completed = subprocess.run(
        ["gh", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def existing_horizon_snapshot() -> tuple[list[dict[str, object]], str]:
    if not OUTPUT.exists():
        return [], ""
    text = OUTPUT.read_text(encoding="utf-8")
    prefix = "/* Generated by scripts/build_horizon_review_console.py. */\nwindow.ARRP_HORIZON_REVIEW_DATA="
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
            return records, synced_at
        raise RuntimeError(
            "No preserved GitHub Horizon snapshot exists. Re-run with --refresh-github in an authenticated host context."
        )

    issues = run_gh_json([
        "issue",
        "list",
        "--repo",
        "Thorncrag/ARRP",
        "--label",
        "kind: horizon",
        "--state",
        "all",
        "--limit",
        "200",
        "--json",
        "number,title,state,url,labels,createdAt,updatedAt",
    ])
    project = run_gh_json([
        "project",
        "item-list",
        "2",
        "--owner",
        "Thorncrag",
        "--limit",
        "500",
        "--format",
        "json",
    ])
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
        display_title = re.sub(r"^HOR-\d+:\s*", "", issue["title"]).strip()
        records.append({
            "id": horizon_id,
            "number": issue["number"],
            "title": display_title,
            "full_title": issue["title"],
            "issue_state": issue["state"].title(),
            "status": project_item.get("status") or ("Closed" if issue["state"] == "CLOSED" else "Project status unavailable"),
            "area": project_item.get("area") or "Unassigned",
            "priority": project_item.get("priority") or "Unassigned",
            "release_blocker": project_item.get("release blocker") or "Unassigned",
            "last_audit": project_item.get("last audit") or "Not recorded",
            "next_audit": project_item.get("next audit") or "Not recorded",
            "canonical_page": project_item.get("canonical page") or issue["url"],
            "issue_url": issue["url"],
            "labels": labels,
            "needs_monitoring": "needs: monitoring" in labels,
            "created_at": issue["createdAt"],
            "updated_at": issue["updatedAt"],
        })
    records.sort(key=lambda record: int(str(record["id"]).split("-")[-1]) if str(record["id"]).startswith("HOR-") else 9999)
    return records, datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def candidate_records(routing: list[dict[str, str]]) -> list[dict[str, object]]:
    evidence_ids: dict[str, list[str]] = {}
    for item in routing:
        candidate_id = item["candidate_id"].strip()
        if candidate_id:
            evidence_ids.setdefault(candidate_id, []).append(item["catalog_id"])
    records: list[dict[str, object]] = []
    for row in read_csv(CANDIDATES):
        if row["review_status"] != "preliminary-candidate":
            continue
        attached_ids = evidence_ids.get(row["candidate_id"], [])
        explicit_ids = [item.strip() for item in row["source_record_ids"].split(";") if item.strip()]
        combined_ids = list(dict.fromkeys([*explicit_ids, *attached_ids]))
        records.append(
            {
                "id": row["candidate_id"],
                "horizon_id": row["horizon_id"],
                "kind": "preliminary_candidate",
                "title": row["title"],
                "term": row["term"],
                "category": "preliminary institutional question",
                "summary": row["institutional_defect"],
                "review_prompt": "Should this preliminary candidate be promoted to a formal HOR candidate?",
                "proposed_area": row["proposed_area"],
                "distinctness": row["distinctness_rationale"],
                "coverage": row["existing_coverage_considered"],
                "counterargument": row["counterargument"],
                "unresolved": row["unresolved_questions"],
                "recommendation": row["recommendation"],
                "source_record_ids": "; ".join(combined_ids),
                "links": parse_links(row["source_links"]),
                "review_status": row["review_status"],
                "last_checked": row["last_reviewed"],
            }
        )
    return records


def proposal_index_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for row in read_csv(ISSUE_REGISTRY):
        if row["Kind"].strip() != "proposal":
            continue
        issue_id = row["Object ID"].strip()
        if not issue_id:
            continue
        title = row["GitHub Title"].strip()
        title = re.sub(rf"^{re.escape(issue_id)}\s*:\s*", "", title)
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


def route_links(integration: list[dict[str, str]]) -> list[dict[str, object]]:
    counts: Counter[str] = Counter()
    for row in integration:
        counts.update(
            route.strip()
            for route in row["integration_routes"].split(";")
            if route.strip()
        )

    canonical_paths = {
        row["Object ID"].strip(): row["Canonical Record"].strip()
        for row in read_csv(ISSUE_REGISTRY)
        if row["Object ID"].strip() and row["Canonical Record"].strip()
    }
    return [
        {
            "route": route,
            "records": count,
            "path": f"../../{canonical_paths[route]}" if route in canonical_paths else "",
        }
        for route, count in counts.most_common(8)
    ]


def split_routes(raw: str) -> list[str]:
    return [route.strip() for route in raw.split(";") if route.strip()]


def labeled_links(*items: tuple[str, str]) -> list[dict[str, str]]:
    return [
        {"label": label, "url": url.strip()}
        for label, url in items
        if url.strip()
    ]


def integration_records(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in rows:
        stage, next_action = INTEGRATION_STAGES.get(
            row["integration_status"],
            ("Codex review needed", "Codex should review and resolve this record's placement."),
        )
        records.append({
            "id": row["catalog_id"],
            "title": row["action_or_policy"],
            "question": row["legal_question_or_outcome"],
            "posture": row["litigation_posture"],
            "routes": split_routes(row["integration_routes"]),
            "status": row["integration_status"],
            "stage": stage,
            "owner": "Codex",
            "next_action": next_action,
            "user_attention": "None unless issue review reveals an unresolved scope or policy choice.",
            "record_kind": "integration",
            "work_type": "Evidence placement",
            "family": row["source_family"],
            "note": row["review_note"],
            "date": row["last_reviewed"],
            "links": labeled_links(
                ("Source entry", row["source_entry_url"]),
                ("Representative case", row["representative_case_url"]),
                ("Official action", row["official_action_url"]),
            ),
        })
    return records


def inventory_routes(raw: str) -> list[str]:
    """Extract stable proposal or Horizon identifiers from inventory associations."""
    return list(dict.fromkeys(re.findall(r"\b(?:HOR|[A-Z]{2,})-\d{3}\b", raw)))


def pending_source_records(
    rows: list[dict[str, str]], represented_source_ids: set[str]
) -> list[dict[str, object]]:
    """Expose pending sources not already owned by an integration or monitor task."""
    records: list[dict[str, object]] = []
    for row in rows:
        source_id = row["Source ID"].strip()
        if not source_id or source_id in represented_source_ids:
            continue
        records.append(
            {
                "id": source_id,
                "title": row["Title or Description"].strip() or source_id,
                "question": row["Proposition Supported"].strip(),
                "posture": "Retained source record; citation or disposition remains pending.",
                "routes": inventory_routes(row["Associated Record IDs"]),
                "status": "pending-source-placement",
                "stage": "Verify and assess for placement",
                "owner": "Codex",
                "next_action": (
                    "During work on the routed proposal or candidate, verify whether this source materially "
                    "strengthens the record; cite it where genuinely used, retain it pending with a precise "
                    "predicate, or remove it after a documented no-additional-value disposition."
                ),
                "user_attention": "None unless review reveals an unresolved scope or policy choice.",
                "record_kind": "pending-source",
                "work_type": "Source verification and placement",
                "family": row["Authority / Publisher"].strip(),
                "source_type": row["Source Type"].strip(),
                "note": row["Notes"].strip(),
                "date": row["Date"].strip(),
                "links": labeled_links(("Source", row["URL"])),
            }
        )
    return records


def monitoring_records(
    rows: list[dict[str, str]],
    source_records: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    registry = {
        row["Object ID"].strip(): row["GitHub Issue"].strip()
        for row in read_csv(ISSUE_REGISTRY)
        if row["Object ID"].strip() and row["GitHub Issue"].strip()
    }

    def links_for(row: dict[str, str]) -> list[dict[str, str]]:
        links: list[dict[str, str]] = []
        for route in split_routes(row["integration_routes"]):
            monitor_id = f"{route}-MON"
            monitor_url = registry.get(monitor_id)
            if monitor_url:
                links.append({"label": f"{route} monitoring record", "url": monitor_url})
            elif route.startswith("HOR-") and registry.get(route):
                links.append({"label": f"{route} candidate", "url": registry[route]})
        for source_id in split_routes(row["source_record_ids"]):
            source = source_records.get(source_id)
            if not source or not source["URL"].strip():
                continue
            authority = source["Authority / Publisher"].strip()
            links.append(
                {
                    "label": f"{source_id} · {authority}" if authority else source_id,
                    "url": source["URL"].strip(),
                }
            )
        return links

    return [
        {
            "id": row["monitor_id"],
            "title": row["action_or_policy"],
            "posture": row["litigation_posture"],
            "routes": split_routes(row["integration_routes"]),
            "trigger": row["revisit_trigger"],
            "status": row["monitoring_status"],
            "stage": "Waiting for an external event",
            "owner": "Codex after the recorded trigger",
            "next_action": "Take no action until the stated ruling, dismissal, settlement, withdrawal, or other posture change occurs.",
            "user_attention": "None while the external predicate remains unsatisfied.",
            "family": row["source_family"],
            "note": row["notes"],
            "date": row["last_checked"],
            "links": links_for(row),
            "record_kind": "monitoring",
        }
        for row in rows
    ]


def source_universe_records(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in rows:
        role, next_action = SOURCE_ROLES.get(
            row["intake_status"],
            ("Research reference", "Codex should determine how this source supports future project research."),
        )
        records.append({
            "id": row["source_id"],
            "title": row["source_name"],
            "term": row["term_scope"],
            "domain": row["coverage_domain"],
            "source_type": row["source_type"],
            "status": row["intake_status"],
            "role": role,
            "owner": "Codex",
            "next_action": next_action,
            "user_attention": "None.",
            "record_kind": "source",
            "work_type": "Source ingestion",
            "value": row["expected_value"],
            "limitation": row["known_limitation"],
            "date": row["last_checked"],
            "links": labeled_links(("Open source", row["url"])),
        })
    return records


def media_records(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in rows:
        stage, next_action = MEDIA_STAGES.get(
            row["arrp_coverage_status"],
            ("Codex review needed", "Codex should determine the episode's project route and evidentiary value."),
        )
        records.append({
            "id": row["media_id"],
            "title": row["episode"],
            "term": row["term"],
            "period": row["date_or_period"],
            "question": row["institutional_question"],
            "coverage": row["arrp_coverage_status"],
            "stage": stage,
            "owner": "Codex",
            "next_action": next_action,
            "user_attention": "None now; Codex should surface only a genuinely unresolved project-scope choice.",
            "record_kind": "media",
            "work_type": "Media episode review",
            "routes": split_routes(row["provisional_arrp_routes"]),
            "recommendation": row["screening_recommendation"],
            "primary_status": row["primary_source_status"],
            "note": row["notes"],
            "date": row["last_checked"],
            "links": labeled_links(
                (row["source_1_name"] or "Source 1", row["source_1_url"]),
                (row["source_2_name"] or "Source 2", row["source_2_url"]),
                (row["primary_source_name"] or "Primary record", row["primary_source_url"]),
            ),
        })
    return records


def media_monitoring_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "id": record["id"],
            "title": record["title"],
            "posture": "Monitored through an existing Horizon record",
            "routes": record["routes"],
            "trigger": "Revisit when the existing Horizon record's stated litigation or external-review predicate occurs.",
            "status": "active-defined-predicate",
            "stage": "Waiting for an external event",
            "owner": "Codex after the recorded trigger",
            "next_action": "Take no action until the existing Horizon monitoring predicate occurs.",
            "user_attention": "None while the external predicate remains unsatisfied.",
            "family": "Two-source media intake",
            "note": record["note"],
            "date": record["date"],
            "links": record["links"],
            "record_kind": "monitoring",
        }
        for record in records
        if record["stage"] == "Monitor through an existing Horizon record"
    ]


def attach_related_queue_work(
    horizon_records: list[dict[str, object]],
    source_queue: list[dict[str, object]],
    monitoring_queue: list[dict[str, object]],
) -> None:
    for horizon in horizon_records:
        horizon_id = horizon["id"]
        related_sources = [record for record in source_queue if horizon_id in record.get("routes", [])]
        related_monitoring = [record for record in monitoring_queue if horizon_id in record.get("routes", [])]
        horizon["source_task_count"] = len(related_sources)
        horizon["monitoring_task_count"] = len(related_monitoring)
        seen_urls: set[str] = set()
        links: list[dict[str, str]] = []
        for record in related_sources:
            for link in record.get("links", []):
                url = link.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                links.append({
                    "label": f"{record['id']} · {link['label']}",
                    "url": url,
                })
                break
        horizon["related_source_links"] = links


def main() -> None:
    args = parse_args()
    routing = read_csv(ROUTING)
    candidates = candidate_records(routing)
    integration = read_csv(EXISTING_ISSUE_INTEGRATION)
    monitoring = read_csv(LITIGATION_MONITORING)
    source_universe = read_csv(SOURCE_UNIVERSE)
    catalog = read_csv(CATALOG)
    media = read_csv(MEDIA)
    cited_sources = read_csv(CITED_SOURCES)
    pending_sources = read_csv(PENDING_SOURCES)
    source_records = {
        row["Source ID"].strip(): row
        for row in [*cited_sources, *pending_sources]
        if row["Source ID"].strip()
    }
    routing_counts = Counter(row["disposition"] for row in routing)
    rendered_integration = integration_records(integration)
    rendered_sources = source_universe_records(source_universe)
    rendered_media = media_records(media)
    represented_source_ids = {
        source_id
        for row in [*integration, *monitoring]
        for source_id in split_routes(row["source_record_ids"])
    }
    rendered_pending_sources = pending_source_records(
        pending_sources, represented_source_ids
    )
    rendered_monitoring = [
        *monitoring_records(monitoring, source_records),
        *media_monitoring_records(rendered_media),
    ]
    source_queue = [
        *rendered_integration,
        *rendered_pending_sources,
        *[
            record
            for record in rendered_media
            if record["stage"] not in {
                "Already incorporated",
                "Monitor through an existing Horizon record",
            }
        ],
        *[
            record
            for row, record in zip(source_universe, rendered_sources)
            if row["intake_status"] in ACTIONABLE_SOURCE_STATUSES
        ],
    ]
    horizon_records, github_synced_at = horizon_snapshot(args.refresh_github)
    attach_related_queue_work(horizon_records, source_queue, rendered_monitoring)
    active_horizon_records = [record for record in horizon_records if record["issue_state"] == "Open"]
    closed_horizon_records = [record for record in horizon_records if record["issue_state"] == "Closed"]
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {
        "schema_version": 4,
        "generated_at": generated_at,
        "github_synced_at": github_synced_at,
        "candidate_source": CANDIDATES.name,
        "candidate_questions": len(candidates),
        "evidence_records": len(routing),
        "existing_issue_queue": len(integration),
        "source_queue_count": len(source_queue),
        "litigation_monitoring_queue": len(rendered_monitoring),
        "source_universe_entries": len(source_universe),
        "automated_existing_issue_review": routing_counts["existing-record-integration"],
        "preliminary_candidate_evidence": routing_counts["preliminary-candidate-evidence"],
        "agent_review_pending": routing_counts["agent-review-needed"],
        "retained_research": routing_counts["research-retained-no-current-route"],
        "media_episodes": len(media),
        "catalog_records": len(catalog),
        "adjudication": COMPLETED_ADJUDICATION,
        "integration_routes": route_links(integration),
        "source_queue_records": source_queue,
        "horizon_issue_count": len(active_horizon_records),
        "closed_horizon_issue_count": len(closed_horizon_records),
        "horizon_records": horizon_records,
        "active_horizon_records": active_horizon_records,
        "closed_horizon_records": closed_horizon_records,
        "integration_records": rendered_integration,
        "monitoring_records": rendered_monitoring,
        "source_universe_records": rendered_sources,
        "media_records": rendered_media,
        "records": candidates,
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    serialized = serialized.replace("</", "<\\/")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "/* Generated by scripts/build_horizon_review_console.py. */\n"
        f"window.ARRP_HORIZON_REVIEW_DATA={serialized};\n",
        encoding="utf-8",
    )
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
        participation_payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")
    PARTICIPATION_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PARTICIPATION_OUTPUT.write_text(
        "/* Generated by scripts/build_horizon_review_console.py. */\n"
        f"window.ARRP_PARTICIPATION_DATA={participation_serialized};\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {OUTPUT.relative_to(ROOT)} and {PARTICIPATION_OUTPUT.relative_to(ROOT)} "
        f"with {len(candidates)} preliminary candidates, "
        f"{len(active_horizon_records)} active Horizon issues, {len(source_queue):,} source tasks, "
        f"and {len(rendered_monitoring):,} monitored episodes."
    )


if __name__ == "__main__":
    main()
