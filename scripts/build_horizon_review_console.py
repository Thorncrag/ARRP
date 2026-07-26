#!/usr/bin/env python3
"""Build the ARRP Project Console and public-input lookup."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

try:
    from project_tree import iter_project_files
except ModuleNotFoundError:  # Imported as scripts.build_horizon_review_console.
    from scripts.project_tree import iter_project_files

try:
    from source_monitor_recommendations import parse_source_monitor_recommendations
except ModuleNotFoundError:  # Imported as scripts.build_horizon_review_console.
    from scripts.source_monitor_recommendations import (
        parse_source_monitor_recommendations,
    )

try:
    from console_data_contracts import (
        feed_contract,
        file_sha256,
        source_hashes,
        source_revision,
        utc_timestamp,
        validate_contract,
    )
except ModuleNotFoundError:
    from scripts.console_data_contracts import (
        feed_contract,
        file_sha256,
        source_hashes,
        source_revision,
        utc_timestamp,
        validate_contract,
    )


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "research" / "trump-administration-preliminary-candidates.csv"
HORIZON_LOG = ROOT / "framework" / "logs" / "HORIZON_SCAN_LOG.md"
CHANGE_AUDIT_LOG = ROOT / "framework" / "logs" / "CHANGE_AUDIT_LOG.md"
AGENT_AUDIT_LOG = ROOT / "framework" / "logs" / "AGENT_AUDIT_LOG.md"
ELIM_RUN_LOG = ROOT / "framework" / "logs" / "ELIM_RUN_LOG.md"
SOURCE_CHECKER_CONFIG = ROOT / ".github" / "source-checker-bot.json"
SOURCE_MONITOR_LOG = ROOT / "framework" / "logs" / "SOURCE_MONITOR_LOG.md"
AGENT_RUNBOOKS = ROOT / "framework" / "agents"
ISSUE_REGISTRY = ROOT / "inventory" / "github_issue_registry.csv"
CITED_SOURCES = ROOT / "inventory" / "sources.csv"
PENDING_SOURCES = ROOT / "inventory" / "sources-pending.csv"
DIRECTIVES = ROOT / "inventory" / "presidential-directives.csv"
CASE_MONITOR_CONFIG = ROOT / ".github" / "case-monitor-bot.json"
DIRECTIVE_MONITOR_CONFIG = ROOT / ".github" / "presidential-directives-bot.json"
PRINT_ASSEMBLY_MANIFEST = ROOT / "framework" / "print-assembly.json"
REVIEW_EPOCHS = ROOT / "research" / "review-epochs.jsonl"
PUBLIC_PROPOSAL_PDF = ROOT / "exports" / "pdf" / "ARRP-public-proposal-draft.pdf"
OUTPUT = ROOT / "research" / "horizon-review-console" / "catalog-data.js"
CONSOLE_DATA_DIR = ROOT / "research" / "horizon-review-console" / "data"
PARTICIPATION_OUTPUT = ROOT / "participate" / "intake-data.js"
GITHUB_BLOB_ROOT = "https://github.com/Thorncrag/ARRP/blob/main/"
HORIZON_LOG_URL = GITHUB_BLOB_ROOT + "framework/logs/HORIZON_SCAN_LOG.md#horizon-integration-log"
PROGRESS_DATA_REF = "origin/project-console-data:progress.json"
INTEGRITY_DATA_REF = "origin/project-console-data:integrity.json"
RUN_CHAIN_DATA_REF = "origin/project-console-data:run-chain.json"
LOCAL_INTEGRITY_FEED = ROOT / ".tmp" / "project-console-integrity.json"
LOCAL_RUN_CHAIN_FEED = ROOT / ".tmp" / "run-chain.json"
SNAPSHOT_OVERRIDE_PATHS = {
    "ARRP_PROGRESS_SNAPSHOT": Path(
        ".tmp/project-console-progress-snapshot.json"
    ),
    "ARRP_INTEGRITY_SNAPSHOT": Path(".tmp/project-console-integrity.json"),
    "ARRP_SOURCE_CHECKER_SNAPSHOT": Path(".tmp/source-checker.json"),
}
LOCAL_RUN_COORDINATOR_CONTROL = (
    ROOT / ".tmp" / "run-coordinator" / "control.json"
)
PRINT_LEVEL_ORDER = (
    "public-proposal",
    "legislative-appendix",
    "executive-summary",
)
PRINT_LEVEL_LABELS = {
    "public-proposal": "Public proposal edition",
    "legislative-appendix": "Legislative appendix edition",
    "executive-summary": "Executive summary edition",
}


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
        help="Rebuild the ARRP Project Console without rewriting the public-input lookup.",
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


def source_payload(row: dict[str, str]) -> dict[str, object]:
    def value(key: str, default: str = "") -> str:
        return (row.get(key) or default).strip()

    return {
        "id": value("Source ID"),
        "record_ids": sorted(associated_record_ids(value("Associated Record IDs"))),
        "monitoring": value("Monitoring", "No") or "No",
        "inventory_status": row.get("_inventory_status", "Relied upon"),
        "type": value("Source Type"),
        "publisher": value("Authority / Publisher"),
        "title": value("Title or Description"),
        "date": value("Date"),
        "url": value("URL"),
        "proposition": value("Proposition Supported"),
        "reliability": value("Reliability Tier"),
        "reviewed": value("Reviewed?"),
        "notes": value("Notes"),
        "retention_rationale": value("Retention Rationale"),
        "pending_reason": value("Pending Reason"),
        "next_action": value("Next Action"),
        "blocker": value("Blocker"),
        "monitoring_rationale": value("Monitoring Rationale"),
        "monitoring_group": value("Monitoring Group"),
        # The console exposes whether an accepted watcher baseline exists, not
        # the raw fingerprint itself.
        "monitoring_baseline_present": bool(value("Monitoring Baseline")),
    }


def catalog_source_records(
    path: Path, inventory_status: str
) -> list[dict[str, object]]:
    records = [
        source_payload({**row, "_inventory_status": inventory_status})
        for row in read_csv(path)
        if row["Source ID"].strip()
    ]
    return sorted(records, key=lambda row: str(row["id"]))


def presidential_directive_records() -> list[dict[str, object]]:
    if not DIRECTIVES.exists():
        return []
    records: list[dict[str, object]] = []
    for row in read_csv(DIRECTIVES):
        directive_id = row.get("Directive ID", "").strip()
        if not directive_id:
            continue
        records.append(
            {
                "id": directive_id,
                "administration": row.get("Administration", "").strip(),
                "president": row.get("President", "").strip(),
                "type": row.get("Directive Type", "").strip(),
                "number": row.get("Number", "").strip(),
                "title": row.get("Title", "").strip(),
                "signed_date": row.get("Signed Date", "").strip(),
                "published_date": row.get("Published Date", "").strip(),
                "citation": row.get("Federal Register Citation", "").strip(),
                "official_url": (
                    row.get("Official PDF URL", "").strip()
                    or row.get("Federal Register URL", "").strip()
                ),
                "federal_register_url": row.get("Federal Register URL", "").strip(),
                "related_directive_ids": split_values(row.get("Related Directive IDs", "")),
                "first_seen": row.get("First Seen", "").strip(),
                "last_changed": row.get("Last Changed", "").strip(),
                "review_status": row.get("Review Status", "").strip() or "New since baseline screening",
                "arrp_record_ids": split_values(row.get("ARRP Record IDs", "")),
                "source_ids": split_values(row.get("Source IDs", "")),
                "disposition_rationale": row.get("Disposition Rationale", "").strip(),
                "reviewed_date": row.get("Reviewed Date", "").strip(),
            }
        )
    return sorted(
        records,
        key=lambda row: (
            str(row["signed_date"] or row["published_date"]),
            str(row["id"]),
        ),
        reverse=True,
    )


def markdown_front_matter(content: str) -> dict[str, object]:
    """Parse the small title/list subset used by ARRP page metadata."""
    if not content.startswith("---\n"):
        return {}
    end = content.find("\n---\n", 4)
    if end < 0:
        return {}
    values: dict[str, object] = {}
    active_list: str | None = None
    for raw_line in content[4:end].splitlines():
        if raw_line.startswith("  - ") and active_list:
            value = raw_line[4:].strip().strip('"\'')
            cast = values.setdefault(active_list, [])
            if isinstance(cast, list) and value:
                cast.append(value)
            continue
        active_list = None
        if not raw_line or raw_line.startswith(" ") or ":" not in raw_line:
            continue
        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        value = raw_value.strip().strip('"\'')
        if value:
            values[key] = value
        else:
            values[key] = []
            active_list = key
    return values


def repository_markdown_links(value: str, source_path: Path) -> str:
    """Resolve runbook-local Markdown links to stable GitHub URLs."""

    def replacement(match: re.Match[str]) -> str:
        label = match.group(1)
        target = match.group(2)
        parsed = urllib.parse.urlsplit(html.unescape(target))
        if parsed.scheme:
            return match.group(0)
        if target.startswith("#"):
            url = GITHUB_BLOB_ROOT + str(source_path.relative_to(ROOT)) + target
            return f"[{label}]({url})"
        target_path, separator, fragment = target.partition("#")
        if target_path.startswith("/"):
            resolved = ROOT / target_path.lstrip("/")
        else:
            resolved = source_path.parent / target_path
        try:
            relative = resolved.resolve().relative_to(ROOT.resolve())
        except ValueError:
            return label
        url = GITHUB_BLOB_ROOT + str(relative)
        if separator:
            url += f"#{fragment}"
        return f"[{label}]({url})"

    return re.sub(r"\[([^]\n]+)\]\(([^)\s]+)\)", replacement, value)


def runbook_sections(content: str, source_path: Path) -> list[dict[str, str]]:
    """Return each complete second-level runbook section for Console display."""
    body = content.split("\n---\n", 1)[-1]
    headings = list(re.finditer(r"^##\s+(.+?)\s*$", body, re.MULTILINE))
    sections: list[dict[str, str]] = []
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        section_markdown = body[start:end].strip()
        if not section_markdown:
            continue
        title = strip_markdown(heading.group(1))
        linked_markdown = repository_markdown_links(section_markdown, source_path)
        sections.append(
            {
                "id": re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-"),
                "title": title,
                "html": render_markdown_safe(linked_markdown),
                "text": strip_markdown(section_markdown),
            }
        )
    return sections


def agent_registry_records() -> list[dict[str, object]]:
    """Build the Console's operational registry from authoritative runbooks."""
    if not AGENT_RUNBOOKS.exists():
        return []
    records: list[dict[str, object]] = []
    for path in sorted(AGENT_RUNBOOKS.glob("*.md")):
        if path.name == "README.md":
            continue
        content = path.read_text(encoding="utf-8")
        metadata = markdown_front_matter(content)
        agent_id = str(metadata.get("agent_id", "")).strip()
        if not agent_id:
            continue
        body = content.split("\n---\n", 1)[-1]
        description_match = re.search(r"^# .+?\n\n(.+?)(?=\n\n|\n#)", body, re.MULTILINE | re.DOTALL)
        description = strip_markdown(description_match.group(1).strip()) if description_match else ""
        runtime_id = str(metadata.get("runtime_id", "")).strip()
        runtime_config = str(metadata.get("runtime_config", "")).strip()
        run_log_path = str(metadata.get("run_log_path", "")).strip()
        current_report = str(metadata.get("current_report", "")).strip()
        current_data = str(metadata.get("current_data", "")).strip()
        raw_checks = metadata.get("checks_included", [])
        checks = (
            [str(item).strip() for item in raw_checks if str(item).strip()]
            if isinstance(raw_checks, list)
            else []
        )
        runtime_url = (
            GITHUB_BLOB_ROOT + runtime_id
            if runtime_id.startswith(".github/")
            else ""
        )
        records.append(
            {
                "id": agent_id,
                "name": str(metadata.get("display_name", agent_id)).strip(),
                "type": str(metadata.get("agent_type", "")).strip(),
                "status": str(metadata.get("status", "unknown")).strip(),
                "trigger": str(metadata.get("trigger", "")).strip(),
                "schedule": str(metadata.get("schedule", "")).strip(),
                "runtime_id": runtime_id,
                "runtime_url": runtime_url,
                "runtime_config": runtime_config,
                "runtime_config_url": (
                    GITHUB_BLOB_ROOT + runtime_config if runtime_config else ""
                ),
                "execution_environment": str(metadata.get("execution_environment", "")).strip(),
                "model_policy": str(metadata.get("model_policy", "")).strip(),
                "log_path": str(metadata.get("log_path", "")).strip(),
                "run_log_path": run_log_path,
                "run_log_url": GITHUB_BLOB_ROOT + run_log_path if run_log_path else "",
                "current_report": current_report,
                "current_report_url": GITHUB_BLOB_ROOT + current_report if current_report else "",
                "current_data": current_data,
                "description": description,
                "checks": checks,
                "runbook_sections": runbook_sections(content, path),
                "runbook_path": str(path.relative_to(ROOT)),
                "runbook_url": GITHUB_BLOB_ROOT + str(path.relative_to(ROOT)),
            }
        )
    return sorted(
        records,
        key=lambda record: (
            0 if record["id"] == "elim" else 1,
            str(record["name"]),
        ),
    )


def page_section(relative: Path) -> str:
    parts = relative.parts
    if relative == Path("README.md"):
        return "Front matter"
    if not parts:
        return "Root"
    labels = {
        "areas": "Areas and proposals",
        "framework": "Framework and process",
        "legislation": "Legislation",
        "topics": "Topic guides",
        "research": "Research",
        "inventory": "Inventory",
        "website": "Website support",
        "participate": "Public participation",
        "sources": "Retained sources",
        "exports": "Exports",
    }
    return labels.get(parts[0], "Root project pages")


def markdown_body(content: str) -> str:
    if not content.startswith("---\n"):
        return content
    end = content.find("\n---\n", 4)
    return content[end + 5 :] if end >= 0 else content


def publication_document_type(relative: Path, metadata: dict[str, object]) -> str:
    if relative in {
        Path("README.md"),
        Path("ABOUT.md"),
        Path("PRINT_READERS_GUIDE.md"),
        Path("LICENSE.md"),
    }:
        return "front-matter"
    if relative == Path("SUBJECT_INDEX.md"):
        return "back-matter"
    parts = relative.parts
    if not parts:
        return "technical"
    if parts[0] == "topics":
        return "topic-guide"
    if parts[0] == "legislation":
        if relative.name == "README.md":
            return "legislation-index"
        return "state-legislation" if relative.stem.endswith("-state") else "federal-legislation"
    if parts[0] == "areas":
        if relative.name == "README.md":
            return "area-summary"
        if relative.name.endswith(".audit.md"):
            return "audit-history"
        if "evidence" in parts:
            return "evidence"
        if "research" in parts or metadata.get("record_type") == "source-development":
            return "research"
        if "issues" in parts:
            return "issue"
    if parts[0] == "research":
        return "research"
    return "technical"


def publication_sort_key(relative: Path, document_type: str, title: str) -> str:
    front_order = {
        "README.md": "000",
        "ABOUT.md": "010",
        "PRINT_READERS_GUIDE.md": "020",
        "LICENSE.md": "030",
    }
    if document_type == "front-matter":
        return front_order.get(relative.as_posix(), f"900-{title.casefold()}")
    if document_type == "back-matter":
        return "999-subject-index"
    if document_type == "topic-guide":
        return f"000-{title.casefold()}" if relative.name == "README.md" else f"100-{title.casefold()}"
    if document_type in {"area-summary", "issue", "audit-history", "evidence", "research"} and relative.parts[0] == "areas":
        area = relative.parts[1] if len(relative.parts) > 1 else ""
        category = {
            "area-summary": "000",
            "issue": "100",
            "evidence": "200",
            "research": "300",
            "audit-history": "400",
        }.get(document_type, "900")
        return f"{area}-{category}-{relative.stem.casefold()}"
    if document_type in {"federal-legislation", "state-legislation"}:
        stem = relative.stem
        base = re.match(r"([A-Z]+-\d{3})", stem)
        vehicle_order = (
            "000" if stem.endswith("-amendment") else
            "010" if stem.endswith("-preferred") else
            "030" if stem.endswith("-state") else "020"
        )
        return f"{base.group(1) if base else stem}-{vehicle_order}-{stem}"
    return f"{relative.parent.as_posix()}-{title.casefold()}"


def publication_page_metrics(content: str, words_per_page: int) -> dict[str, object]:
    body = markdown_body(content)
    text_only = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", body)
    text_only = re.sub(r"<[^>]+>", " ", text_only)
    text_only = re.sub(r"[`*_>#|~-]", " ", text_only)
    word_count = len(re.findall(r"\b[\w’'-]+\b", text_only))
    table_dividers = 0
    max_table_columns = 0
    for line in body.splitlines():
        if line.strip().startswith("|") and line.strip().endswith("|"):
            cells = markdown_table_cells(line)
            max_table_columns = max(max_table_columns, len(cells))
            if is_markdown_table_separator(line):
                table_dividers += 1
    heading_issues = 0
    prior_level = 0
    for match in re.finditer(r"^(#{1,6})\s+", body, re.MULTILINE):
        level = len(match.group(1))
        if (not prior_level and level > 1) or (prior_level and level > prior_level + 1):
            heading_issues += 1
        prior_level = level
    without_targets = re.sub(r"\]\([^)]+\)", "]", body)
    longest_token = max((len(token) for token in re.findall(r"\S+", without_targets)), default=0)
    return {
        "word_count": word_count,
        "estimated_pages": max(1, math.ceil(word_count / max(1, words_per_page))),
        "table_count": table_dividers,
        "max_table_columns": max_table_columns,
        "heading_issue_count": heading_issues,
        "longest_unbroken_token": longest_token,
    }


def internal_markdown_links(relative: Path, content: str) -> list[dict[str, object]]:
    links: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw_target in re.findall(r"\[[^]\n]+\]\(([^)\s]+)", content):
        target = html.unescape(raw_target).strip("<>")
        parsed = urllib.parse.urlsplit(target)
        if parsed.scheme or target.startswith("#"):
            continue
        path_part = urllib.parse.unquote(parsed.path)
        if not path_part or not path_part.lower().endswith(".md"):
            continue
        candidate = (ROOT / path_part.lstrip("/")) if path_part.startswith("/") else (ROOT / relative.parent / path_part)
        try:
            target_relative = candidate.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            continue
        if target_relative in seen:
            continue
        seen.add(target_relative)
        links.append({"path": target_relative, "exists": (ROOT / target_relative).exists()})
    return links


def publication_manifest() -> dict[str, object]:
    return json.loads(PRINT_ASSEMBLY_MANIFEST.read_text(encoding="utf-8"))


def default_assembly_sections(
    relative: Path, document_type: str, manifest: dict[str, object]
) -> dict[str, str]:
    placements: dict[str, str] = {}
    for edition in manifest.get("editions", []):
        if not isinstance(edition, dict):
            continue
        edition_id = str(edition.get("id", ""))
        overrides = edition.get("placement_overrides", {})
        if isinstance(overrides, dict) and relative.as_posix() in overrides:
            placements[edition_id] = str(overrides[relative.as_posix()])
            continue
        for section in edition.get("sections", []):
            if isinstance(section, dict) and document_type in section.get("accepts", []):
                placements[edition_id] = str(section.get("id", ""))
                break
    return placements


def page_inventory_records() -> list[dict[str, object]]:
    """Return every publication-controlled Markdown page and its disposition."""
    excluded_roots = {".git", ".site-build", ".tmp", ".venv"}
    explicit_exceptions = {ROOT / "AGENTS.md", ROOT / "website" / "404.md"}
    records: list[dict[str, object]] = []
    manifest = publication_manifest()
    words_per_page = int(manifest.get("words_per_estimated_page", 650))
    for path in iter_project_files(ROOT, "*.md"):
        relative = path.relative_to(ROOT)
        if excluded_roots.intersection(relative.parts) or path in explicit_exceptions:
            continue
        content = path.read_text(encoding="utf-8")
        metadata = markdown_front_matter(content)
        raw_levels = metadata.get("print_levels", [])
        levels = raw_levels if isinstance(raw_levels, list) else [str(raw_levels)]
        ordered_levels = [level for level in PRINT_LEVEL_ORDER if level in levels]
        ordered_levels.extend(sorted(set(levels) - set(ordered_levels)))
        print_status = str(metadata.get("print_status", "")).strip()
        exclusion_reason = str(metadata.get("print_exclusion_reason", "")).strip()
        if ordered_levels and print_status == "excluded":
            publication_disposition = "conflict"
        elif ordered_levels:
            publication_disposition = "included"
        elif print_status == "excluded":
            publication_disposition = "excluded"
        else:
            publication_disposition = "unclassified"
        relative_path = relative.as_posix()
        title = str(metadata.get("title") or markdown_title(path, content))
        document_type = publication_document_type(relative, metadata)
        records.append(
            {
                "title": title,
                "path": relative_path,
                "section": page_section(relative),
                "print_levels": ordered_levels,
                "print_level_labels": [
                    PRINT_LEVEL_LABELS.get(level, level.replace("-", " ").title())
                    for level in ordered_levels
                ],
                "print_status": print_status,
                "print_exclusion_reason": exclusion_reason,
                "publication_disposition": publication_disposition,
                "github_url": GITHUB_BLOB_ROOT + relative_path,
                "document_type": document_type,
                "print_metadata_present": "print_levels" in metadata or "print_status" in metadata,
                "invalid_print_levels": sorted(set(levels) - set(PRINT_LEVEL_ORDER)),
                "assembly_sections": default_assembly_sections(relative, document_type, manifest),
                "assembly_sort_key": publication_sort_key(relative, document_type, title),
                "internal_links": internal_markdown_links(relative, content),
                **publication_page_metrics(content, words_per_page),
            }
        )
    return sorted(records, key=lambda row: (str(row["section"]), str(row["title"])))


def pdf_page_count(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        result = subprocess.run(
            ["pdfinfo", str(path)], capture_output=True, text=True, check=True, timeout=20
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    return int(match.group(1)) if match else None


def topic_product_records() -> list[dict[str, object]]:
    """Project internal crosswalk and public Topic stages as one stable product."""
    index_path = ROOT / "research" / "README.md"
    content = index_path.read_text(encoding="utf-8")
    records: list[dict[str, object]] = []
    pattern = re.compile(
        r"^-\s+\[([^\]]+)\]\(([^)]+)\)\s+—\s+public topic home:\s+"
        r"\[([^\]]+)\]\((\.\./topics/[^)]+)\)\s*$",
        re.MULTILINE,
    )
    for match in pattern.finditer(content):
        internal_title, internal_target, public_title, public_target = match.groups()
        internal_path = (index_path.parent / internal_target).resolve()
        public_path = (index_path.parent / public_target).resolve()
        try:
            internal_relative = internal_path.relative_to(ROOT).as_posix()
            public_relative = public_path.relative_to(ROOT).as_posix()
        except ValueError as exc:
            raise RuntimeError("Topic-product route escapes the repository.") from exc
        product_key = Path(public_relative).stem
        records.append(
            {
                "product_id": "topic-product:" + product_key,
                "title": public_title,
                "is_issue": False,
                "issue_identifier": None,
                "current_stage": "published",
                "product_status": "published",
                "stages": [
                    {
                        "stage_id": "internal-crosswalk",
                        "label": internal_title,
                        "kind": "project_crosswalk",
                        "path": internal_relative,
                        "url": GITHUB_BLOB_ROOT + internal_relative,
                        "available": internal_path.is_file(),
                    },
                    {
                        "stage_id": "published-topic",
                        "label": public_title,
                        "kind": "topic_page",
                        "path": public_relative,
                        "url": GITHUB_BLOB_ROOT + public_relative,
                        "available": public_path.is_file(),
                    },
                ],
                "owner": None,
                "next_action": None,
                "validation_requirement": None,
                "completeness": {
                    "complete": internal_path.is_file() and public_path.is_file(),
                    "unavailable_fields": [
                        "owner",
                        "next_action",
                        "validation_requirement",
                    ],
                },
            }
        )
    converted = re.search(
        r"former Project 2025 research crosswalk has been converted, without "
        r"duplication, into the public \[([^\]]+)\]\((\.\./topics/[^)]+)\)",
        content,
        re.IGNORECASE,
    )
    if converted:
        public_title, public_target = converted.groups()
        public_path = (index_path.parent / public_target).resolve()
        public_relative = public_path.relative_to(ROOT).as_posix()
        records.append(
            {
                "product_id": "topic-product:" + Path(public_relative).stem,
                "title": public_title,
                "is_issue": False,
                "issue_identifier": None,
                "current_stage": "published",
                "product_status": "published",
                "stages": [
                    {
                        "stage_id": "internal-crosswalk",
                        "label": "Former Project 2025 research crosswalk",
                        "kind": "converted_internal_crosswalk",
                        "path": None,
                        "url": None,
                        "available": False,
                        "disposition": "converted_without_duplication",
                    },
                    {
                        "stage_id": "published-topic",
                        "label": public_title,
                        "kind": "topic_page",
                        "path": public_relative,
                        "url": GITHUB_BLOB_ROOT + public_relative,
                        "available": public_path.is_file(),
                    },
                ],
                "owner": None,
                "next_action": None,
                "validation_requirement": None,
                "completeness": {
                    "complete": public_path.is_file(),
                    "unavailable_fields": [
                        "owner",
                        "next_action",
                        "validation_requirement",
                    ],
                },
            }
        )
    return sorted(records, key=lambda record: str(record["product_id"]))


def repository_revision_for_path(path: Path) -> str | None:
    if not path.exists():
        return None
    completed = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", path.relative_to(ROOT).as_posix()],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    revision = completed.stdout.strip()
    return revision if completed.returncode == 0 and revision else None


def publication_release_readiness(
    page_inventory: list[dict[str, object]],
    builds: list[dict[str, object]],
    progress: dict[str, object] | None = None,
    integrity: dict[str, object] | None = None,
) -> dict[str, object]:
    """Project known release prerequisites without inferring approval or readiness."""
    progress_payload = progress if isinstance(progress, dict) else {}
    progress_available = bool(
        progress_payload
        and isinstance(progress_payload.get("proposals"), list)
        and isinstance(progress_payload.get("candidates"), list)
    )
    progress_contract_available = isinstance(
        progress_payload.get("completeness"), dict
    )
    progress_complete = (
        (progress_payload.get("completeness") or {}).get("complete") is True
        if progress_contract_available
        else False
    )
    delivery_available = isinstance(progress_payload.get("delivery_items"), list)
    delivery_items = (
        progress_payload.get("delivery_items")
        if isinstance(progress_payload.get("delivery_items"), list)
        else []
    )
    project_items = [
        item
        for collection in (
            progress_payload.get("proposals") or [],
            progress_payload.get("candidates") or [],
            delivery_items,
        )
        for item in collection
        if isinstance(item, dict)
    ]
    issue_development_items = [
        item
        for collection in (
            progress_payload.get("proposals") or [],
            progress_payload.get("candidates") or [],
        )
        for item in collection
        if isinstance(item, dict)
    ]
    release_fields_available = progress_available and all(
        ("releaseBlocker" in item or "release_blocker" in item)
        for item in project_items
    )
    audit_status_available = progress_available and all(
        "workflowStatus" in item for item in issue_development_items
    )
    audit_control_fields_complete = audit_status_available and all(
        "changeAuditNeeded" in item and "rebaselineStatus" in item
        for item in issue_development_items
    )

    def identity(item: dict[str, object]) -> dict[str, object]:
        return {
            "identifier": item.get("identifier"),
            "title": item.get("title"),
            "url": item.get("url"),
            "project_item_id": item.get("projectItemId"),
            "workstream": item.get("workstream"),
            "priority": item.get("priority"),
            "status": item.get("workflowStatus"),
        }

    blockers = [
        {
            **identity(item),
            "release_blocker": item.get("releaseBlocker")
            or item.get("release_blocker"),
        }
        for item in project_items
        if normalize_console_owner(
            item.get("releaseBlocker") or item.get("release_blocker")
        )
        in {"yes", "true"}
    ]
    audit_items: list[dict[str, object]] = []
    for item in project_items:
        reasons: list[str] = []
        status = normalize_console_owner(item.get("workflowStatus"))
        if status in {"audit needed", "audit in progress"}:
            reasons.append(str(item.get("workflowStatus")))
        if normalize_console_owner(item.get("changeAuditNeeded")) in {"yes", "true"}:
            reasons.append("Change audit needed")
        rebaseline = normalize_console_owner(item.get("rebaselineStatus"))
        if rebaseline and rebaseline not in {"current", "not applicable", "n/a"}:
            reasons.append(
                "Rebaseline status: " + str(item.get("rebaselineStatus"))
            )
        if reasons:
            audit_items.append(
                {
                    **identity(item),
                    "reasons": reasons,
                    "last_audit": item.get("lastAudit"),
                    "next_audit": item.get("nextAudit"),
                }
            )
    external_review_items = [
        {
            **identity(item),
            "last_audit": item.get("lastAudit"),
            "next_audit": item.get("nextAudit"),
        }
        for item in project_items
        if normalize_console_owner(item.get("workflowStatus")) == "external review"
    ]

    by_path = {
        str(record.get("path") or ""): record
        for record in page_inventory
        if str(record.get("path") or "")
    }
    missing_links: list[dict[str, object]] = []
    cross_edition: list[dict[str, object]] = []
    seen_cross: set[tuple[str, str, str]] = set()
    internal_link_count = 0
    for source in page_inventory:
        source_path = str(source.get("path") or "")
        source_levels = {
            str(level) for level in source.get("print_levels") or []
        }
        for link in source.get("internal_links") or []:
            if not isinstance(link, dict):
                continue
            internal_link_count += 1
            target_path = str(link.get("path") or "")
            if link.get("exists") is not True:
                missing_links.append(
                    {"source": source_path, "target": target_path}
                )
                continue
            target = by_path.get(target_path)
            if target is None:
                continue
            target_levels = {
                str(level) for level in target.get("print_levels") or []
            }
            for edition in sorted(source_levels - target_levels):
                key = (source_path, target_path, edition)
                if key in seen_cross:
                    continue
                seen_cross.add(key)
                cross_edition.append(
                    {
                        "source": source_path,
                        "target": target_path,
                        "source_edition": edition,
                        "target_disposition": target.get(
                            "publication_disposition"
                        ),
                        "review_disposition": None,
                    }
                )

    public_build = next(
        (
            build
            for build in builds
            if build.get("edition_id") == "public-proposal"
        ),
        None,
    )
    artifact_hash = (
        file_sha256(ROOT, PUBLIC_PROPOSAL_PDF)
        if PUBLIC_PROPOSAL_PDF.is_file()
        else None
    )
    license_text = (
        (ROOT / "LICENSE.md").read_text(encoding="utf-8")
        if (ROOT / "LICENSE.md").is_file()
        else ""
    )
    all_rights_reserved = bool(
        re.search(r"\ball rights reserved\b", license_text, re.IGNORECASE)
    )
    planned_later_license = bool(
        re.search(
            r"planned to be released at a later date.+(?:Creative Commons|reuse license)",
            license_text,
            re.IGNORECASE | re.DOTALL,
        )
    )
    integrity_payload = integrity if isinstance(integrity, dict) else {}
    integrity_current = (
        integrity_payload.get("current")
        if isinstance(integrity_payload.get("current"), dict)
        else {}
    )
    disposition_counts = {
        disposition: sum(
            1
            for record in page_inventory
            if record.get("publication_disposition") == disposition
        )
        for disposition in ("included", "excluded", "unclassified", "conflict")
    }
    assembly_valid = (
        disposition_counts["unclassified"] == 0
        and disposition_counts["conflict"] == 0
    )
    return {
        "status": "not_determined",
        "status_explanation": (
            "Structural assembly facts are available, but release readiness "
            "cannot be declared without lineage-backed export validation, "
            "completed prerequisites, and a recorded human go/no-go decision."
        ),
        "assembly": {
            "status": "valid" if assembly_valid else "action_required",
            "label": (
                "Assembly structurally valid"
                if assembly_valid
                else "Assembly structure requires correction"
            ),
            "disposition_counts": disposition_counts,
        },
        "delivery_tasks": {
            "available": delivery_available,
            "source_complete": progress_complete,
            "count": len(delivery_items) if delivery_available else None,
            "incomplete_metadata_count": (
                sum(
                    1
                    for item in delivery_items
                    if not (item.get("completeness") or {}).get("complete")
                )
                if delivery_available
                else None
            ),
            "items": [identity(item) for item in delivery_items]
            if delivery_available
            else [],
            "unavailable_reason": (
                None
                if delivery_available
                else "Authenticated Project delivery items are unavailable."
            ),
        },
        "release_blockers": {
            "available": release_fields_available,
            "source_complete": progress_complete,
            "count": len(blockers) if release_fields_available else None,
            "items": blockers if release_fields_available else [],
            "unavailable_reason": (
                None
                if release_fields_available
                else "Project Release blocker fields are absent from this projection."
            ),
        },
        "required_audits": {
            "available": audit_status_available,
            "source_complete": progress_complete,
            "control_fields_complete": audit_control_fields_complete,
            "count": len(audit_items)
            if audit_control_fields_complete
            else None,
            "known_count": len(audit_items) if audit_status_available else None,
            "items": audit_items,
            "unavailable_reason": (
                None
                if audit_control_fields_complete
                else "Change-audit and rebaseline controls are incomplete in this projection."
            ),
        },
        "external_review": {
            "available": progress_available,
            "source_complete": progress_complete,
            "count": len(external_review_items)
            if progress_available
            else None,
            "items": external_review_items,
            "completion_requirement": (
                "The Project records current External review workflow state; "
                "it does not itself prove that required external review is complete."
            ),
        },
        "link_export_validation": {
            "link_inventory_available": True,
            "internal_link_count": internal_link_count,
            "missing_link_count": len(missing_links),
            "missing_links": missing_links,
            "export_validation_available": False,
            "export_validation_status": "unavailable",
            "unavailable_reason": (
                "No lineage-bearing export validation manifest is recorded."
            ),
        },
        "export_lineage": {
            "available": False,
            "artifact_path": (
                PUBLIC_PROPOSAL_PDF.relative_to(ROOT).as_posix()
                if PUBLIC_PROPOSAL_PDF.is_file()
                else None
            ),
            "artifact_sha256": artifact_hash,
            "artifact_repository_revision": repository_revision_for_path(
                PUBLIC_PROPOSAL_PDF
            ),
            "build_source_revision": None,
            "input_hashes": None,
            "unavailable_reason": (
                "The existing PDF has no recorded build source revision and "
                "complete input-hash manifest."
            ),
        },
        "stale_pdf": {
            "revision_backed_status": "unavailable",
            "mtime_indicator": (
                public_build.get("stale") if isinstance(public_build, dict) else None
            ),
            "mtime_indicator_only": True,
            "explanation": (
                "Filesystem modification time is retained as a diagnostic only; "
                "it cannot establish current export lineage."
            ),
        },
        "cross_edition_references": {
            "available": True,
            "count": len(cross_edition),
            "items": cross_edition,
            "disposition_complete": not cross_edition,
            "explanation": (
                "A cross-edition or online-only target requires an explicit "
                "reader-route disposition; presence alone is not a broken link."
            ),
        },
        "copyright_reuse": {
            "rights_notice_available": bool(license_text),
            "all_rights_reserved": all_rights_reserved
            if license_text
            else None,
            "later_public_reuse_license_planned": planned_later_license
            if license_text
            else None,
            "public_reuse_license_adopted": False
            if all_rights_reserved and planned_later_license
            else None,
            "third_party_reuse_review": "unavailable",
            "status": (
                "human_decision_required"
                if all_rights_reserved and planned_later_license
                else "unavailable"
            ),
        },
        "integrity_validation": {
            "available": bool(integrity_current),
            "result": integrity_current.get("result"),
            "counts": integrity_current.get("counts") or {},
            "revision": integrity_current.get("revision"),
            "generated_at": integrity_current.get("generated_at"),
        },
        "human_go_no_go": {
            "available": False,
            "decision": None,
            "status": "human_decision_required",
            "question": (
                "After all release prerequisites and lineage-backed validation "
                "are complete, authorize this exact revision for public release?"
            ),
            "authority": "Human only",
        },
    }


def publication_data(page_inventory: list[dict[str, object]]) -> dict[str, object]:
    manifest = publication_manifest()
    builds: list[dict[str, object]] = []
    if PUBLIC_PROPOSAL_PDF.exists():
        modified = PUBLIC_PROPOSAL_PDF.stat().st_mtime
        assigned_paths = [
            ROOT / str(record["path"])
            for record in page_inventory
            if "public-proposal" in record.get("print_levels", [])
        ]
        latest_source = max((path.stat().st_mtime for path in assigned_paths if path.exists()), default=0)
        builds.append(
            {
                "edition_id": "public-proposal",
                "label": "Existing public-proposal draft PDF",
                "path": PUBLIC_PROPOSAL_PDF.relative_to(ROOT).as_posix(),
                "github_url": GITHUB_BLOB_ROOT + PUBLIC_PROPOSAL_PDF.relative_to(ROOT).as_posix(),
                "page_count": pdf_page_count(PUBLIC_PROPOSAL_PDF),
                "modified_at": datetime.fromtimestamp(modified, timezone.utc).isoformat(timespec="seconds"),
                "stale": latest_source > modified,
            }
        )
    disposition_counts = {
        disposition: sum(
            1 for record in page_inventory
            if record.get("publication_disposition") == disposition
        )
        for disposition in ("included", "excluded", "unclassified", "conflict")
    }
    exclusion_reasons: dict[str, int] = {}
    for record in page_inventory:
        if record.get("publication_disposition") != "excluded":
            continue
        reason = str(record.get("print_exclusion_reason") or "Reason not recorded")
        exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
    return {
        "manifest": manifest,
        "builds": builds,
        "disposition_counts": disposition_counts,
        "exclusion_reasons": exclusion_reasons,
        "topic_products": topic_product_records(),
        "release_readiness": publication_release_readiness(
            page_inventory,
            builds,
        ),
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


def strip_markdown(value: str) -> str:
    value = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("`", "")
    return re.sub(r"\s+", " ", value).strip()


SAFE_LINK_SCHEMES = {"http", "https", "mailto"}


def safe_markdown_url(raw_url: str) -> str | None:
    """Return a safe Markdown-link target or None for unsafe protocols."""
    value = html.unescape(raw_url.strip())
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme:
        return value if parsed.scheme.casefold() in SAFE_LINK_SCHEMES else None
    if value.startswith(("#", "/", "./", "../")):
        return value
    return None


def render_markdown_inline(value: str) -> str:
    """Render a deliberately small, escaped GitHub-style inline Markdown subset."""
    replacements: list[str] = []

    def preserve(rendered: str) -> str:
        token = f"\x00{len(replacements)}\x00"
        replacements.append(rendered)
        return token

    def link_replacement(match: re.Match[str]) -> str:
        label = render_markdown_inline(match.group(1))
        target = safe_markdown_url(match.group(2))
        if not target:
            return preserve(label)
        return preserve(
            f'<a href="{html.escape(target, quote=True)}" target="_blank" '
            f'rel="noopener noreferrer">{label}</a>'
        )

    # Resolve links before protecting standalone code spans so code-formatted
    # link labels are rendered recursively without sharing placeholder tokens
    # with the outer inline pass.
    protected = re.sub(r"\[([^]\n]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", link_replacement, value)

    def code_replacement(match: re.Match[str]) -> str:
        return preserve(f"<code>{html.escape(match.group(1))}</code>")

    protected = re.sub(r"`([^`\n]+)`", code_replacement, protected)
    rendered = html.escape(protected)
    rendered = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"__([^_\n]+)__", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", rendered)
    rendered = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"<em>\1</em>", rendered)
    rendered = re.sub(r"~~([^~\n]+)~~", r"<del>\1</del>", rendered)
    for index, replacement in enumerate(replacements):
        rendered = rendered.replace(f"\x00{index}\x00", replacement)
    return rendered


def markdown_table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def markdown_table_records(
    content: str,
    required_headers: tuple[str, ...],
    projection_errors: list[dict[str, object]] | None = None,
    source: str = "",
) -> list[dict[str, str]]:
    """Return rows from the first Markdown table matching the requested headers."""
    lines = content.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    encountered_headers: list[list[str]] = []
    for index in range(len(lines) - 1):
        if "|" not in lines[index] or not is_markdown_table_separator(lines[index + 1]):
            continue
        headers = markdown_table_cells(lines[index])
        encountered_headers.append(headers)
        if tuple(headers) != required_headers:
            continue
        rows: list[dict[str, str]] = []
        index += 2
        while index < len(lines) and lines[index].strip() and "|" in lines[index]:
            cells = markdown_table_cells(lines[index])
            if len(cells) != len(headers):
                if projection_errors is not None:
                    projection_errors.append(
                        {
                            "code": "markdown_table_row_width",
                            "severity": "error",
                            "source": source,
                            "line": index + 1,
                            "expected_columns": len(headers),
                            "actual_columns": len(cells),
                            "message": "Markdown log row width does not match its governed header.",
                        }
                    )
                index += 1
                continue
            rows.append(dict(zip(headers, cells)))
            index += 1
        return rows
    if projection_errors is not None:
        projection_errors.append(
            {
                "code": (
                    "markdown_table_header_drift"
                    if encountered_headers
                    else "markdown_table_missing"
                ),
                "severity": "error",
                "source": source,
                "expected_headers": list(required_headers),
                "encountered_headers": encountered_headers,
                "message": "Governed Markdown log table was not found with its exact schema.",
            }
        )
    return []


def log_entry(
    entry_id: str,
    values: dict[str, str],
    raw_values: dict[str, str],
    details_markdown: str,
) -> dict[str, object]:
    return {
        "id": entry_id,
        "values": values,
        "values_html": {
            key: render_markdown_inline(raw_values.get(key, value))
            for key, value in values.items()
        },
        "details_html": render_markdown_safe(details_markdown),
        "search_text": " ".join(
            [entry_id, *values.values(), *(strip_markdown(value) for value in raw_values.values())]
        ),
    }


def horizon_disposition(decision: str) -> str:
    value = strip_markdown(decision).casefold()
    if "deferred" in value or "monitor" in value:
        return "Deferred or monitoring"
    if any(term in value for term in ("rejected", "retired", "outside scope")):
        return "Rejected or retired"
    if any(term in value for term in ("merged", "integrated", "folded")):
        return "Integrated or merged"
    if any(term in value for term in ("admitted", "promoted")):
        return "Admitted or promoted"
    return "Other disposition"


def horizon_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    headers = (
        "Horizon ID", "Decision date", "Original concern", "Decision",
        "Integrated into", "Rationale", "Follow-up",
    )
    entries: list[dict[str, object]] = []
    rows = markdown_table_records(
        HORIZON_LOG.read_text(encoding="utf-8"),
        headers,
        projection_errors,
        HORIZON_LOG.relative_to(ROOT).as_posix(),
    )
    for row in rows:
        disposition = horizon_disposition(row["Decision"])
        values = {
            "record": strip_markdown(row["Horizon ID"]),
            "date": strip_markdown(row["Decision date"]),
            "disposition": disposition,
            "destination": strip_markdown(row["Integrated into"]),
        }
        details = "\n".join(
            f"- **{label}:** {row[label]}" for label in headers[2:]
        )
        entries.append(log_entry(values["record"], values, {
            "record": row["Horizon ID"],
            "date": row["Decision date"],
            "disposition": disposition,
            "destination": row["Integrated into"],
        }, details))
    return {
        "id": "horizon",
        "title": "Horizon Scan Log",
        "description": "Candidate intake, disposition, integration, and follow-up history.",
        "source_url": GITHUB_BLOB_ROOT + "framework/logs/HORIZON_SCAN_LOG.md",
        "columns": [
            {"key": "record", "label": "Record"},
            {"key": "date", "label": "Decision date"},
            {"key": "disposition", "label": "Disposition"},
            {"key": "destination", "label": "Current route"},
        ],
        "group_options": [
            {"key": "disposition", "label": "Disposition"},
            {"key": "date", "label": "Decision date"},
        ],
        "default_sort": {"key": "record", "direction": "desc"},
        "projection": {
            "expected_rows": len(rows),
            "actual_rows": len(entries),
            "complete": len(rows) == len(entries),
        },
        "entries": entries,
    }


def change_audit_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    headers = (
        "Date", "Change audited", "Scope", "Score/rebaseline effect",
        "Findings and corrections",
    )
    entries: list[dict[str, object]] = []
    rows = markdown_table_records(
        CHANGE_AUDIT_LOG.read_text(encoding="utf-8"),
        headers,
        projection_errors,
        CHANGE_AUDIT_LOG.relative_to(ROOT).as_posix(),
    )
    for index, row in enumerate(rows, 1):
        values = {
            "date": strip_markdown(row["Date"]),
            "change": strip_markdown(row["Change audited"]),
            "scope": strip_markdown(row["Scope"]),
            "effect": strip_markdown(row["Score/rebaseline effect"]),
        }
        details = "\n".join(
            f"- **{label}:** {row[label]}" for label in headers[1:]
        )
        entries.append(log_entry(f"change-{index:03d}", values, {
            "date": row["Date"],
            "change": row["Change audited"],
            "scope": row["Scope"],
            "effect": row["Score/rebaseline effect"],
        }, details))
    return {
        "id": "changes",
        "title": "Change Audit Log",
        "description": "Retained project-wide methodology, structure, and consistency changes.",
        "source_url": GITHUB_BLOB_ROOT + "framework/logs/CHANGE_AUDIT_LOG.md",
        "columns": [
            {"key": "date", "label": "Date"},
            {"key": "change", "label": "Change audited"},
            {"key": "scope", "label": "Scope"},
            {"key": "effect", "label": "Score or rebaseline effect"},
        ],
        "group_options": [{"key": "date", "label": "Date"}],
        "default_sort": {"key": "date", "direction": "desc"},
        "projection": {
            "expected_rows": len(rows),
            "actual_rows": len(entries),
            "complete": len(rows) == len(entries),
        },
        "entries": entries,
    }


def section_records(content: str, heading_level: int, start_heading: str = "") -> list[tuple[str, str]]:
    """Split Markdown into titled sections, optionally beginning after an exact heading."""
    if start_heading:
        match = re.search(rf"^{re.escape(start_heading)}\s*$", content, re.MULTILINE)
        content = content[match.end():] if match else ""
    marker = "#" * heading_level
    matches = list(re.finditer(rf"^{re.escape(marker)}\s+(.+?)\s*$", content, re.MULTILINE))
    return [
        (match.group(1).strip(), content[match.end(): matches[index + 1].start() if index + 1 < len(matches) else len(content)].strip())
        for index, match in enumerate(matches)
    ]


def two_column_fields(
    content: str,
    projection_errors: list[dict[str, object]] | None = None,
    source: str = "",
) -> dict[str, str]:
    rows = markdown_table_records(
        content,
        ("Field", "Entry"),
        projection_errors,
        source,
    )
    return {strip_markdown(row["Field"]): row["Entry"] for row in rows}


def agent_audit_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    content = AGENT_AUDIT_LOG.read_text(encoding="utf-8")
    for index, (title, body) in enumerate(section_records(content, 3, "## Log"), 1):
        fields = two_column_fields(
            body,
            projection_errors,
            "{}#{}".format(
                AGENT_AUDIT_LOG.relative_to(ROOT).as_posix(),
                strip_markdown(title),
            ),
        )
        if not fields:
            continue
        header_parts = [part.strip() for part in title.split("—")]
        raw_agent = strip_markdown(fields.get("Agent", fields.get("Run/agent", "")))
        raw_run = strip_markdown(fields.get("Run ID", fields.get("Run/agent", "")))
        raw_task = strip_markdown(fields.get("Task type", fields.get("Tier", header_parts[2] if len(header_parts) > 2 else "")))
        blockers = strip_markdown(fields.get("Blockers/skipped checks", ""))
        raw_outcome = strip_markdown(fields.get("Outcome", ""))
        if not raw_outcome:
            no_blocker_recorded = bool(re.match(r"^no\b[^.]{0,80}\bblockers?\b", blockers, re.IGNORECASE))
            raw_outcome = "Blocked" if blockers and not no_blocker_recorded else "Completed"
        values = {
            "date": strip_markdown(fields.get("Date/time", header_parts[0] if header_parts else "")),
            "record": strip_markdown(fields.get("Issue/task", header_parts[1] if len(header_parts) > 1 else "")),
            "task": raw_task,
            "agent": raw_agent,
            "run": raw_run,
            "outcome": raw_outcome,
        }
        entries.append(log_entry(f"agent-{index:03d}", values, {
            "date": fields.get("Date/time", ""),
            "record": fields.get("Issue/task", ""),
            "task": fields.get("Task type", fields.get("Tier", "")),
            "agent": fields.get("Agent", fields.get("Run/agent", "")),
            "run": fields.get("Run ID", fields.get("Run/agent", "")),
            "outcome": fields.get("Outcome", raw_outcome),
        }, body))
    return {
        "id": "agents",
        "title": "Agent Audit Log",
        "description": "Autonomous, batched, and scheduled agent-run provenance and rollback records.",
        "source_url": GITHUB_BLOB_ROOT + "framework/logs/AGENT_AUDIT_LOG.md",
        "columns": [
            {"key": "date", "label": "Date and time"},
            {"key": "record", "label": "Issue or task"},
            {"key": "task", "label": "Task type"},
            {"key": "agent", "label": "Agent"},
            {"key": "run", "label": "Run ID"},
            {"key": "outcome", "label": "Outcome"},
        ],
        "group_options": [
            {"key": "task", "label": "Task type"},
            {"key": "record", "label": "Issue or task"},
            {"key": "agent", "label": "Agent"},
            {"key": "run", "label": "Run ID"},
            {"key": "outcome", "label": "Outcome"},
        ],
        "default_sort": {"key": "date", "direction": "desc"},
        "entries": entries,
    }


def elim_run_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    content = ELIM_RUN_LOG.read_text(encoding="utf-8")
    for index, (title, body) in enumerate(section_records(content, 3, "## Runs"), 1):
        fields = two_column_fields(
            body,
            projection_errors,
            "{}#{}".format(
                ELIM_RUN_LOG.relative_to(ROOT).as_posix(),
                strip_markdown(title),
            ),
        )
        if not fields:
            continue
        header_parts = [part.strip() for part in title.split("—")]
        values = {
            "date": strip_markdown(fields.get("Started", header_parts[0] if header_parts else "")),
            "outcome": strip_markdown(fields.get("Outcome", header_parts[2] if len(header_parts) > 2 else "")),
            "trigger": strip_markdown(fields.get("Trigger", "")),
            "summary": strip_markdown(fields.get("Work summary", "")),
            "usage": strip_markdown(fields.get("Usage", "")),
            "next": strip_markdown(fields.get("Exact next action", "")),
        }
        entries.append(log_entry(f"elim-run-{index:03d}", values, {
            "date": fields.get("Started", ""),
            "outcome": fields.get("Outcome", ""),
            "trigger": fields.get("Trigger", ""),
            "summary": fields.get("Work summary", ""),
            "usage": fields.get("Usage", ""),
            "next": fields.get("Exact next action", ""),
        }, body))
    return {
        "id": "elim",
        "title": "Elim Run Log",
        "description": "Complete per-run operational reports for ARRP's scheduled LLM agent.",
        "source_url": GITHUB_BLOB_ROOT + "framework/logs/ELIM_RUN_LOG.md",
        "columns": [
            {"key": "date", "label": "Started"},
            {"key": "outcome", "label": "Outcome"},
            {"key": "trigger", "label": "Trigger"},
            {"key": "summary", "label": "Work summary"},
            {"key": "usage", "label": "Usage"},
            {"key": "next", "label": "Exact next action"},
        ],
        "group_options": [
            {"key": "outcome", "label": "Outcome"},
            {"key": "trigger", "label": "Trigger"},
        ],
        "default_sort": {"key": "date", "direction": "desc"},
        "entries": entries,
    }


def bullet_fields(content: str) -> dict[str, str]:
    return {
        strip_markdown(match.group(1)): match.group(2).strip()
        for match in re.finditer(r"^-\s+([^:\n]+):\s*(.+)$", content, re.MULTILINE)
    }


def source_monitor_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    content = SOURCE_MONITOR_LOG.read_text(encoding="utf-8")
    for index, (title, body) in enumerate(section_records(content, 2), 1):
        if not re.match(r"\d{4}-\d{2}-\d{2}", title):
            continue
        parts = [part.strip() for part in title.split("—", 1)]
        fields = bullet_fields(body)
        missing = [
            key
            for key in ("Result",)
            if not str(fields.get(key) or "").strip()
        ]
        if missing and projection_errors is not None:
            projection_errors.append(
                {
                    "code": "source_monitor_entry_schema",
                    "severity": "error",
                    "source": SOURCE_MONITOR_LOG.relative_to(ROOT).as_posix(),
                    "heading": strip_markdown(title),
                    "missing_fields": missing,
                    "message": "Source Monitor entry is missing governed projection fields.",
                }
            )
        values = {
            "date": strip_markdown(parts[0]),
            "watcher": strip_markdown(parts[1] if len(parts) > 1 else ""),
            "result": strip_markdown(fields.get("Result", "")),
            "affected": strip_markdown(fields.get(
                "Affected source IDs",
                fields.get("Affected directive IDs", fields.get("Affected records", "")),
            )),
            "activity": strip_markdown(fields.get(
                "Activity code", fields.get("Recommendation ID", "")
            )),
        }
        entries.append(log_entry(f"source-monitor-{index:03d}", values, {
            "date": parts[0],
            "watcher": parts[1] if len(parts) > 1 else "",
            "result": fields.get("Result", ""),
            "affected": fields.get(
                "Affected source IDs",
                fields.get("Affected directive IDs", fields.get("Affected records", "")),
            ),
            "activity": fields.get(
                "Activity code", fields.get("Recommendation ID", "")
            ),
        }, body))
    return {
        "id": "source-monitor",
        "title": "Source Monitor Log",
        "description": "Material watcher changes and exact-head repository disposition recommendations.",
        "source_url": GITHUB_BLOB_ROOT + "framework/logs/SOURCE_MONITOR_LOG.md",
        "columns": [
            {"key": "date", "label": "Date and time"},
            {"key": "watcher", "label": "Watcher"},
            {"key": "result", "label": "Result"},
            {"key": "affected", "label": "Affected records"},
            {"key": "activity", "label": "Activity or recommendation"},
        ],
        "group_options": [
            {"key": "watcher", "label": "Watcher"},
            {"key": "result", "label": "Result"},
        ],
        "default_sort": {"key": "date", "direction": "desc"},
        "entries": entries,
    }


def source_domain_event_index() -> dict[str, str]:
    completed = subprocess.run(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            "origin/project-console-data",
            "source-domain-events/proposed",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return {}
    return {
        Path(path).stem: path
        for path in completed.stdout.splitlines()
        if path.strip().endswith(".json")
    }


def load_source_domain_event(
    event_id: str,
    event_paths: dict[str, str] | None = None,
) -> tuple[dict[str, object], str]:
    paths = event_paths if event_paths is not None else source_domain_event_index()
    path = paths.get(event_id, "")
    if not path:
        raise RuntimeError(
            f"Structured source-domain event {event_id} is unavailable."
        )
    completed = subprocess.run(
        ["git", "show", f"origin/project-console-data:{path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Structured source-domain event {event_id} could not be read."
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Structured source-domain event {event_id} is invalid JSON."
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Structured source-domain event {event_id} is not a JSON object."
        )
    return payload, path


def structured_affected_set(
    recommendation: dict[str, object],
    event: dict[str, object],
) -> dict[str, object]:
    event_id = str(recommendation.get("proposal_event_id") or "")
    if str(event.get("event_id") or "") != event_id:
        raise RuntimeError("Bound event identity does not match the recommendation.")
    proposal = event.get("proposal")
    if not isinstance(proposal, dict):
        raise RuntimeError("Bound event lacks its proposal identity.")
    if int(proposal.get("pull_request_number") or 0) != int(
        recommendation.get("pull_request_number") or 0
    ):
        raise RuntimeError("Bound event pull request does not match the recommendation.")
    if str(proposal.get("proposal_revision") or "") != str(
        recommendation.get("head_revision") or ""
    ):
        raise RuntimeError(
            "Bound event head revision does not match the recommendation."
        )
    affected = event.get("affected_records")
    if not isinstance(affected, list):
        raise RuntimeError("Bound event affected_records is not an array.")
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, record in enumerate(affected):
        if not isinstance(record, dict):
            raise RuntimeError(
                f"Bound event affected record {index} is not an object."
            )
        record_id = str(record.get("record_id") or "").strip()
        record_type = str(record.get("record_type") or "").strip()
        if not record_id or not record_type:
            raise RuntimeError(
                f"Bound event affected record {index} lacks identity or type."
            )
        key = (record_type, record_id)
        if key in seen:
            raise RuntimeError(
                f"Bound event duplicates affected record {record_type}:{record_id}."
            )
        seen.add(key)
        normalized.append({"record_id": record_id, "record_type": record_type})
    summary = event.get("summary")
    declared_count = (
        summary.get("affected_record_count")
        if isinstance(summary, dict)
        else None
    )
    if declared_count is None or int(declared_count) != len(normalized):
        raise RuntimeError(
            "Bound event affected count does not match its exact enumeration."
        )
    by_type: dict[str, list[str]] = {}
    for record in normalized:
        by_type.setdefault(record["record_type"], []).append(record["record_id"])
    by_type = {
        record_type: sorted(identifiers)
        for record_type, identifiers in sorted(by_type.items())
    }
    return {
        "complete": True,
        "total_count": len(normalized),
        "records": normalized,
        "record_ids": sorted(record["record_id"] for record in normalized),
        "by_type": by_type,
        "source_ids": by_type.get("source", []),
        "directive_ids": by_type.get("presidential-directive", []),
        "issue_development_ids": sorted(
            by_type.get("proposal", []) + by_type.get("candidate", [])
        ),
        "issue_development_count": len(
            by_type.get("proposal", []) + by_type.get("candidate", [])
        ),
    }


def repository_review_recommendations(
    projection_errors: list[dict[str, object]] | None = None,
    event_loader: object = None,
) -> list[dict[str, object]]:
    records = parse_source_monitor_recommendations(
        SOURCE_MONITOR_LOG.read_text(encoding="utf-8")
    )
    event_paths = source_domain_event_index() if event_loader is None else {}
    display_fields = {
        "reviewer",
        "recommendation",
        "rationale",
        "affected_records",
        "confidence",
        "human_question",
        "reassessment_trigger",
        "heading",
    }
    projected: list[dict[str, object]] = []
    for record in records:
        event_id = str(record.get("proposal_event_id") or "")
        event_path = ""
        try:
            if event_loader is None:
                event, event_path = load_source_domain_event(event_id, event_paths)
            else:
                loaded = event_loader(event_id)
                if isinstance(loaded, tuple):
                    event, event_path = loaded
                else:
                    event = loaded
            if not isinstance(event, dict):
                raise RuntimeError("Structured event loader returned a non-object.")
            affected = structured_affected_set(record, event)
        except (RuntimeError, TypeError, ValueError) as exc:
            affected = {
                "complete": False,
                "total_count": None,
                "records": [],
                "record_ids": [],
                "by_type": {},
                "source_ids": [],
                "directive_ids": [],
                "issue_development_ids": [],
                "issue_development_count": None,
                "error": str(exc),
            }
            if projection_errors is not None:
                projection_errors.append(
                    {
                        "code": "recommendation_affected_set_unavailable",
                        "severity": "error",
                        "recommendation_id": record.get("id"),
                        "event_id": event_id,
                        "message": str(exc),
                    }
                )
        projected.append(
            {
            **{
                key: strip_markdown(str(value)) if key in display_fields else value
                for key, value in record.items()
            },
            "affected": affected,
            "event_source_url": (
                "https://github.com/Thorncrag/ARRP/blob/project-console-data/"
                + event_path
                if event_path
                else None
            ),
            "source_url": GITHUB_BLOB_ROOT
            + "framework/logs/SOURCE_MONITOR_LOG.md",
            "console_target": "logs:source-monitor",
        }
        )
    return projected


def project_log_views(
    projection_errors: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    return [
        horizon_log_view(projection_errors),
        elim_run_log_view(projection_errors),
        agent_audit_log_view(projection_errors),
        source_monitor_log_view(projection_errors),
        change_audit_log_view(projection_errors),
    ]


def is_markdown_table_separator(line: str) -> bool:
    cells = markdown_table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def render_markdown_safe(value: str) -> str:
    """Render useful GitHub-style Markdown while escaping all source HTML.

    The console is intentionally dependency-free and works from ``file://``.
    Only tags emitted by this function can enter the generated data bundle.
    """
    lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    index = 0

    def starts_block(position: int) -> bool:
        if position >= len(lines):
            return False
        line = lines[position]
        return bool(
            not line.strip()
            or re.match(r"^#{1,6}\s+", line)
            or re.match(r"^\s*```", line)
            or re.match(r"^\s*>\s?", line)
            or re.match(r"^\s*[-+*]\s+", line)
            or re.match(r"^\s*\d+[.)]\s+", line)
            or re.match(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", line)
            or (
                position + 1 < len(lines)
                and "|" in line
                and is_markdown_table_separator(lines[position + 1])
            )
        )

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        fence = re.match(r"^\s*```\s*([A-Za-z0-9_-]*)\s*$", line)
        if fence:
            language = fence.group(1)
            index += 1
            code_lines: list[str] = []
            while index < len(lines) and not re.match(r"^\s*```\s*$", lines[index]):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            class_name = f' class="language-{language}"' if language else ""
            output.append(
                f"<pre><code{class_name}>{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading:
            level = len(heading.group(1))
            output.append(f"<h{level}>{render_markdown_inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        if re.match(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", line):
            output.append("<hr>")
            index += 1
            continue

        if re.match(r"^\s*>\s?", line):
            quoted: list[str] = []
            while index < len(lines):
                match = re.match(r"^\s*>\s?(.*)$", lines[index])
                if not match:
                    break
                quoted.append(match.group(1))
                index += 1
            output.append(f"<blockquote>{render_markdown_safe(chr(10).join(quoted))}</blockquote>")
            continue

        if index + 1 < len(lines) and "|" in line and is_markdown_table_separator(lines[index + 1]):
            headers = markdown_table_cells(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip() and "|" in lines[index]:
                rows.append(markdown_table_cells(lines[index]))
                index += 1
            head = "".join(f"<th>{render_markdown_inline(cell)}</th>" for cell in headers)
            body_rows = []
            for row in rows:
                padded = row[: len(headers)] + [""] * max(0, len(headers) - len(row))
                body_rows.append(
                    "<tr>" + "".join(f"<td>{render_markdown_inline(cell)}</td>" for cell in padded) + "</tr>"
                )
            output.append(
                f"<div class=\"markdown-table-wrap\"><table><thead><tr>{head}</tr></thead>"
                f"<tbody>{''.join(body_rows)}</tbody></table></div>"
            )
            continue

        unordered = re.match(r"^\s*[-+*]\s+(.+)$", line)
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if unordered or ordered:
            list_tag = "ul" if unordered else "ol"
            pattern = r"^\s*[-+*]\s+(.+)$" if unordered else r"^\s*\d+[.)]\s+(.+)$"
            items: list[str] = []
            while index < len(lines):
                item = re.match(pattern, lines[index])
                if not item:
                    break
                content = item.group(1)
                task = re.match(r"^\[([ xX])\]\s*(.*)$", content)
                if task:
                    checked = " checked" if task.group(1).casefold() == "x" else ""
                    rendered_item = (
                        f'<input type="checkbox" disabled{checked}> '
                        f"{render_markdown_inline(task.group(2))}"
                    )
                else:
                    rendered_item = render_markdown_inline(content)
                items.append(f"<li>{rendered_item}</li>")
                index += 1
            output.append(f"<{list_tag}>{''.join(items)}</{list_tag}>")
            continue

        paragraph = [line.strip()]
        index += 1
        while index < len(lines) and not starts_block(index):
            paragraph.append(lines[index].strip())
            index += 1
        output.append(f"<p>{render_markdown_inline(' '.join(paragraph))}</p>")

    return "\n".join(output)


MONITORING_SECTION_HEADING = re.compile(
    r"^##[ \t]+(?:"
    r"Watching for updates(?:[ \t]*[:—-][^\r\n]*)?"
    r"|Defined monitoring(?:[ \t]+and[ \t]+research)?[ \t]+triggers"
    r"|Monitoring status and (?:revisit[ \t]+trigger|next[ \t]+step)"
    r"|Monitoring predicates?"
    r"|Monitoring items?"
    r"|Next step"
    r")[ \t]*$"
    r"(.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)


def monitoring_section(value: str) -> str:
    """Extract a monitoring instruction from one of the headings used by current records."""
    section = MONITORING_SECTION_HEADING.search(value)
    return strip_markdown(section.group(1)) if section else ""


def monitoring_rationale_for_record(registry_row: dict[str, str], issue_body: str = "") -> str:
    """Return the most specific available human-authored monitoring instruction."""
    canonical = registry_row.get("Canonical Record", "").strip()
    if issue_body and (
        registry_row.get("Kind", "").strip() == "horizon"
        or canonical == str(HORIZON_LOG.relative_to(ROOT))
    ):
        section = monitoring_section(issue_body)
        if section:
            return section
    if canonical:
        path = ROOT / canonical
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            match = re.search(r'^audit_next:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
            if match and match.group(1).strip():
                return strip_markdown(match.group(1))
            section = monitoring_section(content)
            if section:
                return section
    if issue_body:
        section = monitoring_section(issue_body)
        if section:
            return section
    return "The owning issue is marked for monitoring, but its specific trigger has not yet been structured."


def markdown_links(value: str) -> list[dict[str, str]]:
    return [
        {"label": label.strip(), "url": url.strip()}
        for label, url in re.findall(r"\[([^]]+)\]\(([^)]+)\)", value)
        if label.strip() and url.strip()
    ]


def horizon_log_records(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, dict[str, object]]:
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
    for line_number, line in enumerate(
        HORIZON_LOG.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not re.match(r"^\|\s*HOR-\d+\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(fields):
            if projection_errors is not None:
                projection_errors.append(
                    {
                        "code": "horizon_log_row_width",
                        "severity": "error",
                        "source": HORIZON_LOG.relative_to(ROOT).as_posix(),
                        "line": line_number,
                        "expected_columns": len(fields),
                        "actual_columns": len(cells),
                        "message": "Horizon log row cannot be projected without loss.",
                    }
                )
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


def research_markdown_files() -> list[Path]:
    """Return maintained central and area-owned research records."""
    paths = list((ROOT / "research").rglob("*.md"))
    paths.extend((ROOT / "areas").glob("*/research/*.md"))
    return sorted(set(paths))


def research_for_record(record_id: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    identifier = re.compile(rf"(?<![A-Z0-9-]){re.escape(record_id)}(?![A-Z0-9-])")
    for path in research_markdown_files():
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


def candidate_records() -> list[dict[str, object]]:
    sources = source_index()
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
        if not source_ids and not links:
            raise RuntimeError(
                f"Preliminary candidate {row['candidate_id']} has no supporting source."
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
                "evidence_records": [],
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


def require_complete_cli_collection(
    records: object,
    *,
    limit: int,
    source: str,
    reported_total: object = None,
) -> list[dict[str, object]]:
    if not isinstance(records, list):
        raise RuntimeError(f"{source} did not return a JSON array.")
    if len(records) >= limit:
        raise RuntimeError(
            f"{source} reached its explicit {limit}-record ceiling; completeness "
            "cannot be established."
        )
    if reported_total is not None:
        try:
            total = int(reported_total)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"{source} returned an invalid totalCount.") from exc
        if total != len(records):
            raise RuntimeError(
                f"{source} pagination is incomplete: totalCount={total}, "
                f"received={len(records)}."
            )
    return records


def existing_console_payload() -> dict[str, object]:
    """Assemble the compatibility snapshot and normalized Console data parts."""
    if not OUTPUT.exists():
        return {}
    text = OUTPUT.read_text(encoding="utf-8")
    prefix = (
        "/* Generated by scripts/build_horizon_review_console.py. */\n"
        "window.ARRP_HORIZON_REVIEW_DATA="
    )
    if not text.startswith(prefix):
        return {}
    try:
        payload = json.loads(text.removeprefix(prefix).removesuffix(";\n"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    part_prefix = (
        "/* Generated by scripts/build_horizon_review_console.py. */\n"
        "window.ARRP_HORIZON_REVIEW_DATA=window.ARRP_HORIZON_REVIEW_DATA||{};\n"
        "Object.assign(window.ARRP_HORIZON_REVIEW_DATA,"
    )
    for path in sorted(CONSOLE_DATA_DIR.glob("*.js")):
        part_text = path.read_text(encoding="utf-8")
        if not part_text.startswith(part_prefix):
            continue
        try:
            part = json.loads(part_text.removeprefix(part_prefix).removesuffix(");\n"))
        except json.JSONDecodeError:
            continue
        if isinstance(part, dict):
            payload.update(part)
    source_chunk_keys = sorted(
        key for key in payload if key.startswith("cited_sources_chunk_")
    )
    if source_chunk_keys:
        payload["cited_sources"] = [
            record
            for key in source_chunk_keys
            for record in payload.pop(key, [])
        ]
        payload["cited_sources"].sort(key=lambda record: str(record.get("id", "")))
    directive_chunk_keys = sorted(
        key for key in payload if key.startswith("presidential_directives_chunk_")
    )
    if directive_chunk_keys:
        payload["presidential_directives"] = [
            record
            for key in directive_chunk_keys
            for record in payload.pop(key, [])
        ]
    return payload


def generated_console_part(text: str) -> dict[str, object]:
    marker = "Object.assign(window.ARRP_HORIZON_REVIEW_DATA,"
    if marker not in text:
        return {}
    serialized = text.split(marker, 1)[1].strip()
    if not serialized.endswith(");"):
        return {}
    try:
        payload = json.loads(serialized[:-2])
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


CATALOG_PREFIX = (
    "/* Generated by scripts/build_horizon_review_console.py. */\n"
    "window.ARRP_HORIZON_REVIEW_DATA="
)
PART_PREFIX = (
    "/* Generated by scripts/build_horizon_review_console.py. */\n"
    "window.ARRP_HORIZON_REVIEW_DATA=window.ARRP_HORIZON_REVIEW_DATA||{};\n"
    "Object.assign(window.ARRP_HORIZON_REVIEW_DATA,"
)


def serialized_catalog(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2).replace(
        "</", "<\\/"
    )
    return f"{CATALOG_PREFIX}{serialized};\n"


def serialized_console_part(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2).replace(
        "</", "<\\/"
    )
    return f"{PART_PREFIX}{serialized});\n"


def payload_count(value: object) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return sum(payload_count(item) for item in value.values())
    return 0


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def write_console_bundle(
    compatibility_payload: dict[str, object],
    parts: dict[str, dict[str, object]],
    *,
    generation_contract: dict[str, object],
    output: Path | None = None,
    data_dir: Path | None = None,
) -> dict[str, object]:
    """Stage, validate, hash, and atomically replace one Console data generation."""
    output = output or OUTPUT
    data_dir = data_dir or CONSOLE_DATA_DIR
    generation_id_value = str(generation_contract.get("generation_id") or "")
    if not generation_id_value:
        raise RuntimeError("Console bundle generation lacks a generation_id.")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(
        tempfile.mkdtemp(prefix=".console-generation-", dir=output.parent)
    )
    stage_data = stage_root / "data"
    stage_data.mkdir()
    try:
        domain_records: list[dict[str, object]] = []
        for name, original_part in sorted(parts.items()):
            if Path(name).name != name or not name.endswith(".js"):
                raise RuntimeError(f"Unsafe Console domain filename: {name}")
            part = {
                **original_part,
                "domain_generation": {name: generation_id_value},
            }
            text = serialized_console_part(part)
            path = stage_data / name
            path.write_text(text, encoding="utf-8")
            parsed = generated_console_part(text)
            if parsed != part:
                raise RuntimeError(f"Generated Console domain failed readback: {name}")
            domain_records.append(
                {
                    "file": name,
                    "sha256": file_sha256(stage_data, path),
                    "bytes": path.stat().st_size,
                    "keys": sorted(original_part),
                    "record_count": payload_count(original_part),
                }
            )
        manifest = {
            "manifest_schema_version": 1,
            "generation_id": generation_id_value,
            "generated_at": generation_contract.get("generated_at"),
            "source_revision": generation_contract.get("source_revision"),
            "availability": generation_contract.get("availability"),
            "completeness": generation_contract.get("completeness"),
            "domain_count": len(domain_records),
            "domains": domain_records,
            "files": {
                str(domain["file"]): {
                    "generation_id": generation_id_value,
                    "sha256": domain["sha256"],
                    "bytes": domain["bytes"],
                    "keys": domain["keys"],
                    "record_count": domain["record_count"],
                }
                for domain in domain_records
            },
        }
        manifest_path = stage_data / "generation-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        for domain in domain_records:
            path = stage_data / str(domain["file"])
            if file_sha256(stage_data, path) != domain["sha256"]:
                raise RuntimeError(
                    f"Generated Console domain hash failed readback: {domain['file']}"
                )
        staged_compatibility = {
            **compatibility_payload,
            **generation_contract,
            "generation_manifest": manifest,
        }
        stage_catalog = stage_root / output.name
        stage_catalog.write_text(
            serialized_catalog(staged_compatibility), encoding="utf-8"
        )
        catalog_payload = json.loads(
            stage_catalog.read_text(encoding="utf-8")
            .removeprefix(CATALOG_PREFIX)
            .removesuffix(";\n")
        )
        if catalog_payload.get("generation_id") != generation_id_value:
            raise RuntimeError("Generated Console catalog failed generation readback.")

        prior_data = stage_root / "prior-data"
        prior_catalog = stage_root / "prior-catalog.js"
        data_replaced = False
        catalog_replaced = False
        try:
            if data_dir.exists():
                os.replace(data_dir, prior_data)
            os.replace(stage_data, data_dir)
            data_replaced = True
            if output.exists():
                os.replace(output, prior_catalog)
            os.replace(stage_catalog, output)
            catalog_replaced = True
        except Exception:
            if catalog_replaced and output.exists():
                output.unlink()
            if prior_catalog.exists():
                os.replace(prior_catalog, output)
            if data_replaced and data_dir.exists():
                rollback_new = stage_root / "failed-new-data"
                os.replace(data_dir, rollback_new)
            if prior_data.exists():
                os.replace(prior_data, data_dir)
            raise
        return manifest
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)


def snapshot_time(payload: dict[str, object]) -> datetime:
    candidates = [payload]
    current = payload.get("current")
    if isinstance(current, dict):
        candidates.append(current)
    for candidate in candidates:
        for field in ("generatedAt", "generated_at", "checked_at", "asOf", "as_of"):
            raw = str(candidate.get(field) or "").strip()
            if not raw:
                continue
            try:
                return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(
                    timezone.utc
                )
            except ValueError:
                continue
    return datetime.min.replace(tzinfo=timezone.utc)


PRODUCER_CONTRACT_FIELDS = (
    "contract_schema_version",
    "generation_id",
    "source_revision",
    "expected_count",
    "actual_count",
    "source_hashes",
    "availability",
    "completeness",
    "pagination",
    "projection_errors",
    "freshness",
)


def snapshot_contract_view(payload: dict[str, object]) -> dict[str, object]:
    """Return the producer contract, distinct from later currentness overlays."""
    producer = payload.get("producer_contract")
    if not isinstance(producer, dict):
        return payload
    return {**payload, **producer}


def declared_snapshot_revision(payload: dict[str, object]) -> str:
    contract = snapshot_contract_view(payload)
    revision = str(
        contract.get("source_revision")
        or contract.get("revision")
        or ""
    ).strip()
    current = payload.get("current")
    if not revision and isinstance(current, dict):
        revision = str(
            current.get("source_revision")
            or current.get("revision")
            or ""
        ).strip()
    return revision


def valid_snapshot(
    payload: object,
    *,
    timestamp_fields: tuple[str, ...],
    required_fields: tuple[str, ...] = (),
) -> bool:
    if not isinstance(payload, dict):
        return False
    if not all(field in payload for field in required_fields):
        return False
    contract = snapshot_contract_view(payload)
    if "generation_id" in contract:
        completeness = contract.get("completeness")
        if not isinstance(completeness, dict) or completeness.get("complete") is not True:
            return False
    return validate_contract(
        contract,
        timestamp_fields=timestamp_fields,
        allow_legacy=True,
    ) or (
        isinstance(payload.get("current"), dict)
        and validate_contract(
            payload["current"],
            timestamp_fields=timestamp_fields,
            allow_legacy=True,
        )
    )


def newest_snapshot(
    candidates: list[dict[str, object]],
    *,
    authority: str = "generation",
    expected_revision: str | None = None,
) -> dict[str, object]:
    """Select by the feed owner rather than treating every HEAD as authority.

    ``generation`` is used for authenticated Project synchronizations,
    ``repository_revision`` for repository-bound integrity output, and
    ``catalog`` for Source Checker generations projected against current
    catalog identity and hashes.
    """
    if not candidates:
        return {}
    if authority not in {"generation", "repository_revision", "catalog"}:
        raise ValueError(f"Unknown snapshot authority: {authority}")
    expected = (
        (expected_revision or source_revision(ROOT)).strip()
        if authority == "repository_revision"
        else ""
    )

    def revision_epoch(revision: str) -> int:
        if not revision:
            return 0
        completed = subprocess.run(
            ["git", "show", "-s", "--format=%ct", revision],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        try:
            return int(completed.stdout.strip()) if completed.returncode == 0 else 0
        except ValueError:
            return 0

    def completeness_rank(payload: dict[str, object]) -> int:
        completeness = snapshot_contract_view(payload).get("completeness")
        if isinstance(completeness, dict):
            return 2 if completeness.get("complete") is True else 0
        return 1

    def key(payload: dict[str, object]) -> tuple[object, ...]:
        revision = declared_snapshot_revision(payload)
        contract = snapshot_contract_view(payload)
        deterministic_identity = str(contract.get("generation_id") or "")
        if not deterministic_identity:
            deterministic_identity = hashlib.sha256(
                json.dumps(
                    payload, sort_keys=True, separators=(",", ":"), default=str
                ).encode("utf-8")
            ).hexdigest()
        common = (
            completeness_rank(payload),
            snapshot_time(payload),
            deterministic_identity,
        )
        if authority == "repository_revision":
            return (
                int(bool(expected and revision == expected)),
                completeness_rank(payload),
                revision_epoch(revision),
                snapshot_time(payload),
                deterministic_identity,
            )
        if authority == "catalog":
            coverage = payload.get("current_catalog_coverage")
            return (
                int(
                    isinstance(coverage, dict)
                    and coverage.get("complete") is True
                ),
                *common,
            )
        return common

    return max(candidates, key=key)


def with_repository_revision_currentness(
    payload: dict[str, object],
    *,
    expected_revision: str,
) -> dict[str, object]:
    """Overlay repository-authority currentness without changing producer validity."""
    if not payload:
        return {}
    projected = dict(payload)
    expected = expected_revision.strip()
    declared = declared_snapshot_revision(payload)
    freshness = dict(projected.get("freshness") or {})
    equivalent_revisions = {
        str(value).strip()
        for value in freshness.get("equivalent_source_revisions") or []
        if str(value).strip()
    }
    equivalent = bool(expected and expected in equivalent_revisions)
    current = bool(expected and (declared == expected or equivalent))
    status = "current" if current else "stale" if expected and declared else "unavailable"
    projected["currentness"] = {
        "authority": "repository_revision",
        "status": status,
        "current": current,
        "expected_source_revision": expected or None,
        "producer_source_revision": declared or None,
        "equivalent_inputs_established": equivalent,
        "supersession_rule": (
            "A different authoritative repository revision supersedes this "
            "integrity generation immediately, regardless of elapsed time."
        ),
    }
    producer_availability = snapshot_contract_view(payload).get("availability")
    if current:
        projected["availability"] = (
            str(producer_availability)
            if str(producer_availability or "") in {"current", "available"}
            else "current"
        )
    if not current:
        projected["producer_availability"] = producer_availability
        projected["availability"] = status
        errors = [
            error
            for error in projected.get("projection_errors") or []
            if isinstance(error, dict)
            and error.get("code") != "repository_revision_superseded"
        ]
        errors.append(
            {
                "code": "repository_revision_superseded",
                "severity": "warning",
                "message": (
                    "Integrity generation is not bound to the authoritative "
                    "repository revision."
                    if status == "stale"
                    else "Integrity currentness cannot be established."
                ),
                "expected_source_revision": expected or None,
                "producer_source_revision": declared or None,
            }
        )
        projected["projection_errors"] = errors
    freshness.update(
        {
            "status": status,
            "basis": "authoritative repository revision",
            "supersession_rule": projected["currentness"]["supersession_rule"],
        }
    )
    projected["freshness"] = freshness
    return projected


def with_project_generation_currentness(
    payload: dict[str, object],
) -> dict[str, object]:
    """Describe Project currentness using the latest complete synchronization."""
    if not payload:
        return {}
    projected = dict(payload)
    contract = snapshot_contract_view(payload)
    complete = (
        isinstance(contract.get("completeness"), dict)
        and contract["completeness"].get("complete") is True
    )
    contract_declared = bool(
        str(contract.get("generation_id") or "").strip()
        and isinstance(contract.get("completeness"), dict)
    )
    status = (
        str(contract.get("availability") or "current")
        if complete and contract_declared
        else "stale"
        if contract_declared
        else "unavailable"
    )
    projected["availability"] = status
    projected["currentness"] = {
        "authority": "authenticated_project_generation",
        "status": status,
        "current": (
            contract_declared
            and complete
            and status in {"current", "available"}
        ),
        "generation_id": contract.get("generation_id"),
        "synchronized_at": (
            payload.get("generatedAt")
            or payload.get("generated_at")
            or payload.get("asOf")
            or payload.get("as_of")
        ),
        "supersession_rule": (
            "A newer complete authenticated Project synchronization supersedes "
            "an older generation; repository HEAD alone does not."
        ),
    }
    return projected


def read_trusted_snapshot_file(
    raw_path: str,
    *,
    environment_name: str,
) -> dict[str, object]:
    """Read one JSON snapshot from its fixed repository staging location."""
    relative_path = SNAPSHOT_OVERRIDE_PATHS.get(environment_name)
    if relative_path is None:
        raise RuntimeError(f"{environment_name} is not an approved snapshot override.")
    trusted_path = os.path.realpath(os.fspath(ROOT / relative_path))
    full_path = os.path.realpath(raw_path)
    if full_path != trusted_path:
        raise RuntimeError(
            f"{environment_name} must select its fixed repository staging file "
            f"{relative_path.as_posix()}."
        )
    if not os.path.isfile(trusted_path):
        raise RuntimeError(
            f"{environment_name} must select an existing regular JSON snapshot."
        )
    try:
        with open(trusted_path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"{environment_name} explicitly selected an unreadable snapshot."
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"{environment_name} explicitly selected a non-object snapshot."
        )
    return payload


def read_snapshot_override(
    environment_name: str,
    *,
    timestamp_fields: tuple[str, ...],
    required_fields: tuple[str, ...] = (),
) -> dict[str, object] | None:
    raw_path = os.environ.get(environment_name, "").strip()
    if not raw_path:
        return None
    payload = read_trusted_snapshot_file(
        raw_path,
        environment_name=environment_name,
    )
    if not valid_snapshot(
        payload,
        timestamp_fields=timestamp_fields,
        required_fields=required_fields,
    ):
        raise RuntimeError(
            f"{environment_name} explicitly selected an invalid snapshot."
        )
    return payload


def tracked_progress_snapshot() -> dict[str, object]:
    """Recover the committed Console snapshot when it is newer than the data branch."""
    relative = (CONSOLE_DATA_DIR / "progress.js").relative_to(ROOT).as_posix()
    completed = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return {}
    part = generated_console_part(completed.stdout)
    payload = part.get("progress", {})
    return payload if isinstance(payload, dict) else {}


def progress_snapshot() -> dict[str, object]:
    """Read the latest generated progress data without making it authoritative."""
    override = read_snapshot_override(
        "ARRP_PROGRESS_SNAPSHOT",
        timestamp_fields=("generatedAt", "generated_at", "asOf", "as_of"),
        required_fields=("metrics",),
    )
    if override is not None:
        return with_project_generation_currentness(override)
    candidates: list[dict[str, object]] = []
    try:
        completed = subprocess.run(
            ["git", "show", PROGRESS_DATA_REF],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        if valid_snapshot(
            payload,
            timestamp_fields=("generatedAt", "generated_at", "asOf", "as_of"),
            required_fields=("metrics",),
        ):
            candidates.append(payload)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    tracked = tracked_progress_snapshot()
    if valid_snapshot(
        tracked,
        timestamp_fields=("generatedAt", "generated_at", "asOf", "as_of"),
        required_fields=("metrics",),
    ):
        candidates.append(tracked)
    existing = existing_console_payload()
    cached = existing.get("progress", existing.get("progress_dashboard", {}))
    if valid_snapshot(
        cached,
        timestamp_fields=("generatedAt", "generated_at", "asOf", "as_of"),
        required_fields=("metrics",),
    ):
        candidates.append(cached)
    return with_project_generation_currentness(
        newest_snapshot(candidates, authority="generation")
    )


def integrity_snapshot() -> dict[str, object]:
    """Read the latest generated integrity feed without making it authoritative."""
    expected_revision = source_revision(ROOT)
    override = read_snapshot_override(
        "ARRP_INTEGRITY_SNAPSHOT",
        timestamp_fields=("generated_at",),
        required_fields=("current", "history"),
    )
    if override is not None:
        return with_repository_revision_currentness(
            override,
            expected_revision=expected_revision,
        )
    candidates: list[dict[str, object]] = []
    if LOCAL_INTEGRITY_FEED.exists():
        try:
            payload = json.loads(LOCAL_INTEGRITY_FEED.read_text(encoding="utf-8"))
            if valid_snapshot(
                payload,
                timestamp_fields=("generated_at",),
                required_fields=("current", "history"),
            ):
                candidates.append(payload)
        except (OSError, json.JSONDecodeError):
            pass
    try:
        completed = subprocess.run(
            ["git", "show", INTEGRITY_DATA_REF],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        if valid_snapshot(
            payload,
            timestamp_fields=("generated_at",),
            required_fields=("current", "history"),
        ):
            candidates.append(payload)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    existing = existing_console_payload()
    cached = existing.get("integrity", {})
    if valid_snapshot(
        cached,
        timestamp_fields=("generated_at",),
        required_fields=("current", "history"),
    ):
        candidates.append(cached)
    return with_repository_revision_currentness(
        newest_snapshot(
            candidates,
            authority="repository_revision",
            expected_revision=expected_revision,
        ),
        expected_revision=expected_revision,
    )


def successful_run_chain_stages(
    *snapshots: dict[str, object],
) -> list[dict[str, object]]:
    """Retain the newest known successful execution for each automation stage."""
    latest: dict[str, dict[str, object]] = {}
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        stage_groups = [
            snapshot.get("stages", []),
            snapshot.get("last_successful_stages", []),
        ]
        for stages in stage_groups:
            if not isinstance(stages, list):
                continue
            for stage in stages:
                if not isinstance(stage, dict):
                    continue
                stage_id = str(stage.get("id") or stage.get("stage_id") or "").strip()
                succeeded_at = str(
                    stage.get("last_success_at")
                    or (
                        stage.get("completed_at")
                        if re.search(
                            r"success|succeed|complete|healthy|pass",
                            str(stage.get("status") or ""),
                            re.IGNORECASE,
                        )
                        else ""
                    )
                    or ""
                ).strip()
                if not stage_id or not succeeded_at:
                    continue
                candidate = {
                    **stage,
                    "id": stage_id,
                    "status": "succeeded",
                    "last_success_at": succeeded_at,
                }
                existing = latest.get(stage_id)
                try:
                    candidate_time = datetime.fromisoformat(
                        succeeded_at.replace("Z", "+00:00")
                    ).astimezone(timezone.utc)
                except ValueError:
                    candidate_time = datetime.min.replace(tzinfo=timezone.utc)
                try:
                    existing_time = (
                        datetime.fromisoformat(
                            str(existing.get("last_success_at") or "").replace(
                                "Z", "+00:00"
                            )
                        ).astimezone(timezone.utc)
                        if existing
                        else datetime.min.replace(tzinfo=timezone.utc)
                    )
                except ValueError:
                    existing_time = datetime.min.replace(tzinfo=timezone.utc)
                if existing is None or candidate_time >= existing_time:
                    latest[stage_id] = candidate
    return sorted(latest.values(), key=lambda stage: str(stage["id"]))


def run_chain_snapshot() -> dict[str, object]:
    """Read the latest generated run-chain state without making it authoritative."""
    local_chain = os.environ.get("ARRP_RUN_CHAIN_SNAPSHOT", "").strip()
    candidates = [Path(local_chain)] if local_chain else [LOCAL_RUN_CHAIN_FEED]
    for path in candidates:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                if not local_chain and path == LOCAL_RUN_CHAIN_FEED:
                    try:
                        control = json.loads(
                            LOCAL_RUN_COORDINATOR_CONTROL.read_text(
                                encoding="utf-8"
                            )
                        )
                    except (OSError, json.JSONDecodeError):
                        control = {}
                    action_items = (
                        control.get("action_items")
                        if isinstance(control, dict)
                        else None
                    )
                    if isinstance(action_items, list):
                        payload = dict(payload)
                        payload["host_action_items"] = action_items
                history_sources = [payload]
                try:
                    published = subprocess.run(
                        ["git", "show", RUN_CHAIN_DATA_REF],
                        cwd=ROOT,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    published_payload = json.loads(published.stdout)
                    if isinstance(published_payload, dict):
                        history_sources.append(published_payload)
                except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
                    pass
                existing = existing_console_payload().get("run_chain", {})
                if isinstance(existing, dict):
                    history_sources.append(existing)
                payload = dict(payload)
                payload["last_successful_stages"] = successful_run_chain_stages(
                    *history_sources
                )
                return payload
        except (OSError, json.JSONDecodeError):
            pass
    try:
        completed = subprocess.run(
            ["git", "show", RUN_CHAIN_DATA_REF],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        if isinstance(payload, dict):
            return payload
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    existing = existing_console_payload()
    cached = existing.get("run_chain", {})
    return cached if isinstance(cached, dict) else {}


def source_checker_snapshot() -> dict[str, object]:
    """Read the published source-checker feed or its explicit offline cache."""
    try:
        config = json.loads(SOURCE_CHECKER_CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        config = {}

    catalog_paths = [
        ROOT / str(relative) for relative in config.get("catalogs") or []
    ]
    current_catalog_ids: set[str] | None = set() if catalog_paths else None
    id_field = str(config.get("idField") or "Source ID")
    url_field = str(config.get("urlField") or "URL")
    for relative in config.get("catalogs") or []:
        path = ROOT / str(relative)
        if not path.is_file():
            current_catalog_ids = None
            break
        for row in read_csv(path):
            if str(row.get(url_field) or "").strip():
                identifier = str(row.get(id_field) or "").strip()
                if not identifier or (
                    current_catalog_ids is not None
                    and identifier in current_catalog_ids
                ):
                    current_catalog_ids = None
                    break
                if current_catalog_ids is not None:
                    current_catalog_ids.add(identifier)
        if current_catalog_ids is None:
            break
    current_catalog_hashes = (
        source_hashes(ROOT, catalog_paths)
        if current_catalog_ids is not None
        else {}
    )

    def candidate_is_valid(payload: object) -> bool:
        if not valid_snapshot(
            payload,
            timestamp_fields=("checked_at", "generated_at"),
            required_fields=("results",),
        ):
            return False
        assert isinstance(payload, dict)
        producer = snapshot_contract_view(payload)
        results = payload.get("results")
        counts = payload.get("counts")
        if not isinstance(results, list) or not isinstance(counts, dict):
            return False
        try:
            expected = int(
                producer.get("expected_count", payload.get("eligible_urls"))
            )
            actual = int(producer.get("actual_count", len(results)))
            classified = sum(int(value) for value in counts.values())
        except (TypeError, ValueError):
            return False
        identifiers = [
            str(item.get("source_id") or "").strip()
            for item in results
            if isinstance(item, dict)
        ]
        return (
            expected >= 0
            and actual == len(results)
            and expected == actual
            and classified == len(results)
            and len(identifiers) == len(results)
            and all(identifiers)
            and len(identifiers) == len(set(identifiers))
        )

    def with_current_catalog_coverage(
        payload: dict[str, object],
    ) -> dict[str, object]:
        projected = dict(payload)
        existing_producer = payload.get("producer_contract")
        producer_contract = (
            dict(existing_producer)
            if isinstance(existing_producer, dict)
            else {
                field: payload[field]
                for field in PRODUCER_CONTRACT_FIELDS
                if field in payload
            }
        )
        projected["producer_contract"] = producer_contract
        if current_catalog_ids is None:
            projected["availability"] = "unavailable"
            projected["completeness"] = {
                "complete": False,
                "expected_count": None,
                "actual_count": len(payload.get("results") or []),
                "missing_count": None,
            }
            projected["projection_errors"] = [
                {
                    "code": "current_catalog_unavailable",
                    "severity": "error",
                    "message": "Current source catalogs could not be validated.",
                }
            ]
            projected["currentness"] = {
                "authority": "source_catalog_identity_and_hashes",
                "status": "unavailable",
                "current": False,
                "supersession_rule": (
                    "Any catalog identity or content-hash change supersedes a "
                    "prior Source Checker generation immediately."
                ),
            }
            return projected
        results = payload.get("results") or []
        result_ids = {
            str(item.get("source_id") or "").strip()
            for item in results
            if isinstance(item, dict)
        }
        missing = sorted(current_catalog_ids - result_ids)
        unexpected = sorted(result_ids - current_catalog_ids)
        producer_hashes = producer_contract.get("source_hashes")
        producer_hashes = (
            producer_hashes if isinstance(producer_hashes, dict) else {}
        )
        missing_hashes = sorted(
            label
            for label in current_catalog_hashes
            if not str(producer_hashes.get(label) or "").strip()
        )
        hash_mismatches = sorted(
            label
            for label, digest in current_catalog_hashes.items()
            if str(producer_hashes.get(label) or "").strip()
            and producer_hashes.get(label) != digest
        )
        hash_contract_available = bool(current_catalog_hashes) and not missing_hashes
        complete = (
            not missing
            and not unexpected
            and hash_contract_available
            and not hash_mismatches
        )
        errors = [
            error
            for error in payload.get("projection_errors") or []
            if isinstance(error, dict)
            and error.get("code")
            not in {
                "current_catalog_source_missing",
                "superseded_catalog_source",
                "current_catalog_hash_missing",
                "current_catalog_hash_superseded",
            }
        ]
        errors.extend(
            {
                "code": "current_catalog_source_missing",
                "severity": "error",
                "source_id": identifier,
                "message": "Current source catalog ID is absent from this checker generation.",
            }
            for identifier in missing
        )
        errors.extend(
            {
                "code": "superseded_catalog_source",
                "severity": "warning",
                "source_id": identifier,
                "message": "Checker result is outside the current catalog identity set.",
            }
            for identifier in unexpected
        )
        errors.extend(
            {
                "code": "current_catalog_hash_missing",
                "severity": "error",
                "catalog": label,
                "message": (
                    "Checker generation does not declare the current catalog hash."
                ),
            }
            for label in missing_hashes
        )
        errors.extend(
            {
                "code": "current_catalog_hash_superseded",
                "severity": "error",
                "catalog": label,
                "message": (
                    "Current catalog content differs from the checker generation."
                ),
                "producer_hash": producer_hashes.get(label),
                "current_hash": current_catalog_hashes.get(label),
            }
            for label in hash_mismatches
        )
        projected.update(
            {
                "expected_count": len(current_catalog_ids),
                "actual_count": len(result_ids & current_catalog_ids),
                "availability": "current" if complete else "stale",
                "completeness": {
                    "complete": complete,
                    "expected_count": len(current_catalog_ids),
                    "actual_count": len(result_ids & current_catalog_ids),
                    "missing_count": len(missing),
                    "unexpected_count": len(unexpected),
                    "missing_hash_count": len(missing_hashes),
                    "hash_mismatch_count": len(hash_mismatches),
                },
                "missing_source_ids": missing,
                "unexpected_source_ids": unexpected,
                "projection_errors": errors,
                "current_catalog_coverage": {
                    "complete": complete,
                    "expected_count": len(current_catalog_ids),
                    "actual_count": len(result_ids & current_catalog_ids),
                    "missing_ids": missing,
                    "unexpected_ids": unexpected,
                    "source_hashes": current_catalog_hashes,
                    "producer_source_hashes": producer_hashes,
                    "hash_contract_available": hash_contract_available,
                    "missing_hashes": missing_hashes,
                    "hash_mismatches": hash_mismatches,
                },
                "currentness": {
                    "authority": "source_catalog_identity_and_hashes",
                    "status": "current" if complete else "stale",
                    "current": complete,
                    "supersession_rule": (
                        "Any catalog identity or content-hash change supersedes "
                        "a prior Source Checker generation immediately."
                    ),
                },
            }
        )
        freshness = dict(projected.get("freshness") or {})
        freshness.update(
            {
                "status": "current" if complete else "stale",
                "basis": "current source catalog identity coverage and content hashes",
                "supersession_rule": projected["currentness"][
                    "supersession_rule"
                ],
            }
        )
        projected["freshness"] = freshness
        return projected

    override_path = os.environ.get("ARRP_SOURCE_CHECKER_SNAPSHOT", "").strip()
    if override_path:
        override_payload = read_trusted_snapshot_file(
            override_path,
            environment_name="ARRP_SOURCE_CHECKER_SNAPSHOT",
        )
        if not candidate_is_valid(override_payload):
            raise RuntimeError(
                "ARRP_SOURCE_CHECKER_SNAPSHOT explicitly selected a Source "
                "Checker feed with an invalid producer generation."
            )
        return with_current_catalog_coverage(override_payload)

    candidates: list[dict[str, object]] = []
    configured_cache = str(config.get("offlineCachePath") or "").strip()
    cache_candidates = [ROOT / configured_cache] if configured_cache else []

    for path in cache_candidates:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if candidate_is_valid(payload):
                candidates.append(with_current_catalog_coverage(payload))
        except (OSError, json.JSONDecodeError):
            pass

    current_data = str(config.get("currentData") or "").strip()
    data_branch = str(config.get("dataBranch") or "").strip()
    data_path = str(config.get("currentDataPath") or "").strip()
    if current_data and ":" in current_data:
        configured_branch, configured_path = current_data.split(":", 1)
        if not data_branch:
            data_branch = configured_branch
        if not data_path:
            data_path = configured_path
    if data_branch and data_path:
        try:
            completed = subprocess.run(
                ["git", "show", f"origin/{data_branch}:{data_path}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            if candidate_is_valid(payload):
                candidates.append(with_current_catalog_coverage(payload))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            pass

    existing = existing_console_payload()
    cached = existing.get("source_checker", {})
    if candidate_is_valid(cached):
        candidates.append(with_current_catalog_coverage(cached))
    return newest_snapshot(candidates, authority="catalog")


def existing_horizon_snapshot() -> tuple[list[dict[str, object]], str]:
    payload = existing_console_payload()
    return payload.get("horizon_records", []), str(payload.get("github_synced_at", ""))


def source_count_for_record(record_id: str) -> int:
    return sum(
        record_id in associated_record_ids(row["Associated Record IDs"])
        for row in all_source_records()
    )


def monitoring_issue_snapshot(
    refresh: bool, horizon_records: list[dict[str, object]] | None = None
) -> list[dict[str, object]]:
    eligible_kinds = {"proposal", "horizon"}
    horizon_issue_bodies: dict[str, str] = {}
    for record in horizon_records or []:
        body = str(record.get("issue_body", ""))
        if not body and isinstance(record.get("issue_body_lines"), list):
            body = "\n".join(str(line) for line in record["issue_body_lines"])
        if body:
            horizon_issue_bodies[str(record.get("id", ""))] = body
    if not refresh:
        records = existing_console_payload().get("monitoring_issues", [])
        if isinstance(records, list):
            registry_by_id = {
                row["Object ID"].strip(): row
                for row in read_csv(ISSUE_REGISTRY)
                if row["Object ID"].strip()
            }
            enriched: list[dict[str, object]] = []
            for record in records:
                record_id = str(record.get("id", ""))
                registry = registry_by_id.get(record_id, {})
                if registry.get("Kind", "").strip() not in eligible_kinds:
                    continue
                sources = sources_for_record(record_id)
                enriched.append(
                    {
                        **record,
                        "source_count": len(sources),
                        "sources": sources,
                        "monitoring_rationale": monitoring_rationale_for_record(
                            registry, horizon_issue_bodies.get(record_id, "")
                        ),
                    }
                )
            return enriched
        raise RuntimeError(
            "No preserved GitHub monitoring snapshot exists. Re-run with "
            "--refresh-github in an authenticated host context."
        )

    issue_limit = 1000
    issues = require_complete_cli_collection(
        run_gh_json(
        [
            "issue", "list", "--repo", "Thorncrag/ARRP", "--label",
            "needs: monitoring", "--state", "open", "--limit", str(issue_limit), "--json",
            "number,title,state,url,labels,updatedAt,body",
        ]
        ),
        limit=issue_limit,
        source="GitHub monitored-issue query",
    )
    project_limit = 1000
    project = run_gh_json(
        [
            "project", "item-list", "2", "--owner", "Thorncrag", "--limit", str(project_limit),
            "--format", "json",
        ]
    )
    if not isinstance(project, dict):
        raise RuntimeError("GitHub Project query did not return a JSON object.")
    project_items = require_complete_cli_collection(
        project.get("items"),
        limit=project_limit,
        source="GitHub Project item query",
        reported_total=project.get("totalCount"),
    )
    project_by_number = {
        item.get("content", {}).get("number"): item
        for item in project_items
        if item.get("content", {}).get("type") == "Issue"
    }
    registry_by_number = {
        int(row["GitHub Number"]): row
        for row in read_csv(ISSUE_REGISTRY)
        if row["GitHub Number"].strip().isdigit()
    }
    kind_labels = {"proposal": "Proposal", "horizon": "Candidate"}
    records: list[dict[str, object]] = []
    for issue in issues:
        registry = registry_by_number.get(issue["number"], {})
        if registry.get("Kind", "").strip() not in eligible_kinds:
            continue
        project_item = project_by_number.get(issue["number"], {})
        record_id = registry.get("Object ID", "").strip()
        if not record_id:
            match = re.search(r"\b(?:HOR|[A-Z]{2,})-\d{3}\b", issue["title"])
            record_id = match.group(0) if match else f"Issue #{issue['number']}"
        title = re.sub(rf"^{re.escape(record_id)}\s*:\s*", "", issue["title"]).strip()
        records.append(
            {
                "id": record_id,
                "number": issue["number"],
                "title": title,
                "kind": kind_labels.get(registry.get("Kind", "").strip(), "Project record"),
                "area": project_item.get("area") or (
                    record_id.split("-", 1)[0] if "-" in record_id else "Unassigned"
                ),
                "development_level": project_item.get("development level") or "Development level unavailable",
                "workflow_status": project_item.get("status") or "Workflow status unavailable",
                "priority": project_item.get("priority") or "Unassigned",
                "source_count": source_count_for_record(record_id),
                "sources": sources_for_record(record_id),
                "monitoring_rationale": monitoring_rationale_for_record(
                    registry, issue.get("body", "")
                ),
                "issue_url": issue["url"],
                "updated_at": issue["updatedAt"],
            }
        )
    return sorted(records, key=lambda row: (str(row["kind"]), str(row["id"])))


def case_watcher_snapshot() -> tuple[list[dict[str, object]], dict[str, object]]:
    """Cataloged court sources covered by the tracker-assisted watcher."""
    if not CASE_MONITOR_CONFIG.exists():
        return [], {"enabled": False, "mode": "Not configured"}
    config = json.loads(CASE_MONITOR_CONFIG.read_text(encoding="utf-8"))
    verification = config.get("verification", config.get("provider", {}))
    allowed_hosts = set(verification.get("allowedHosts", []))
    registry_by_id = {
        row.get("Object ID", "").strip(): row
        for row in read_csv(ISSUE_REGISTRY)
        if row.get("Object ID", "").strip()
    }
    records: list[dict[str, object]] = []
    for raw in all_source_records():
        source = source_payload(raw)
        if source.get("monitoring") != "Yes":
            continue
        host = urllib.parse.urlsplit(str(source.get("url", ""))).hostname or ""
        if host not in allowed_hosts:
            continue
        owner_ids = list(source.get("record_ids", []))
        owner_id = owner_ids[0] if owner_ids else "Unassigned"
        registry = registry_by_id.get(owner_id, {})
        records.append(
            {
                **source,
                "owner_id": owner_id,
                "owner_title": registry.get("GitHub Title", "").strip() or owner_id,
                "owner_kind": registry.get("Kind", "").strip() or "Project record",
                "owner_status": "Source-level monitoring",
                "owner_issue_url": registry.get("GitHub Issue", "").strip(),
                "monitoring_rationale": source.get("monitoring_rationale") or source.get("proposition"),
                "monitoring_group": source.get("monitoring_group") or owner_id,
                "coverage": (
                    "Accepted per-source baseline"
                    if source.get("monitoring_baseline_present")
                    else "Baseline initialization required"
                ),
            }
        )
    records.sort(key=lambda row: (str(row["owner_id"]), str(row["monitoring_group"]), str(row["id"])))
    schedule = config.get("schedule", {})
    metadata = {
        "enabled": bool(config.get("enabled", False)),
        "mode": (
            "Manual dispatch only"
            if not config.get("enabled", False)
            else schedule.get("description", "Scheduled; manual dispatch available")
        ),
        "bot_name": config.get("botName", "case-monitor-bot"),
        "provider": " + ".join(
            value
            for value in (
                config.get("tracker", {}).get("type", ""),
                verification.get("type", ""),
            )
            if value
        )
        or "Not configured",
        "workflow_url": "https://github.com/Thorncrag/ARRP/actions/workflows/case-monitor-bot.yml",
    }
    return records, metadata


def directive_watcher_metadata() -> dict[str, object]:
    if not DIRECTIVE_MONITOR_CONFIG.exists():
        return {"enabled": False, "mode": "Not configured"}
    config = json.loads(DIRECTIVE_MONITOR_CONFIG.read_text(encoding="utf-8"))
    schedule = config.get("schedule", {})
    return {
        "enabled": bool(config.get("enabled", False)),
        "mode": (
            "Manual dispatch only"
            if not config.get("enabled", False)
            else schedule.get("description", "Scheduled; manual dispatch available")
        ),
        "bot_name": config.get("botName", "presidential-directives-bot"),
        "provider": config.get("provider", {}).get("type", "Not configured"),
        "workflow_url": "https://github.com/Thorncrag/ARRP/actions/workflows/presidential-directives-bot.yml",
    }


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

    issue_limit = 1000
    issues = require_complete_cli_collection(
        run_gh_json(
        [
            "issue", "list", "--repo", "Thorncrag/ARRP", "--label", "kind: horizon",
            "--state", "all", "--limit", str(issue_limit), "--json",
            "number,title,state,url,body,labels,createdAt,updatedAt",
        ]
        ),
        limit=issue_limit,
        source="GitHub Horizon issue query",
    )
    project_limit = 1000
    project = run_gh_json(
        [
            "project", "item-list", "2", "--owner", "Thorncrag", "--limit", str(project_limit),
            "--format", "json",
        ]
    )
    if not isinstance(project, dict):
        raise RuntimeError("GitHub Project query did not return a JSON object.")
    project_items = require_complete_cli_collection(
        project.get("items"),
        limit=project_limit,
        source="GitHub Project item query",
        reported_total=project.get("totalCount"),
    )
    project_by_number = {
        item.get("content", {}).get("number"): item
        for item in project_items
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
                "development_level": project_item.get("development level")
                or ("Closed" if issue["state"] == "CLOSED" else "Development level unavailable"),
                "workflow_status": project_item.get("status")
                or ("Closed" if issue["state"] == "CLOSED" else "Workflow status unavailable"),
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
    projection_errors: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    history_by_id = horizon_log_records(projection_errors)
    enriched: list[dict[str, object]] = []
    for original in records:
        record = dict(original)
        record_id = str(record["id"])
        issue_body = str(record.pop("issue_body", ""))
        record["issue_body_lines"] = issue_body.splitlines()
        record["issue_body_html"] = render_markdown_safe(issue_body) if issue_body.strip() else ""
        history = history_by_id.get(record_id)
        sources = sources_for_record(record_id)
        research = research_for_record(record_id)
        gaps: list[str] = []
        if not history:
            gaps.append("No Horizon Scan Log entry was found for this active candidate.")
        if not sources:
            gaps.append("No supporting source is associated with this candidate in either source catalog.")
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
                "evidence_records": [],
                "research_records": research,
                "dossier_gaps": gaps,
            }
        )
        enriched.append(record)
    return enriched


def overview_incident_identity(stage: str, message: str) -> tuple[str, str]:
    """Return a stable prerequisite/root-cause identity for compact incidents."""

    compact = re.sub(r"\s+", " ", message.casefold()).strip()
    if (
        "canonical arrp workspace is not reconciled with github" in compact
        or re.search(r"current branch (?:is )?.+ instead of main", compact)
    ):
        return (
            "host-repository-preflight",
            "Canonical ARRP workspace is off main and not reconciled with GitHub.",
        )
    if "isolated elim checkout contains a prior unsynchronized baseline" in compact:
        return (
            "elim-isolated-checkout",
            "The isolated Elim checkout contains a prior unsynchronized baseline.",
        )
    return (stage, message.strip() or "Unclassified automation incident.")


def overview_data(
    *,
    candidates: list[dict[str, object]],
    active_horizon_records: list[dict[str, object]],
    monitoring_issues: list[dict[str, object]],
    pending_sources: list[dict[str, object]],
    review_recommendations: list[dict[str, object]],
    progress: dict[str, object],
    integrity: dict[str, object],
    run_chain: dict[str, object],
    publication: dict[str, object],
    project_logs: list[dict[str, object]],
    agent_registry: list[dict[str, object]],
    watcher_metadata: dict[str, object],
    source_checker: dict[str, object],
) -> dict[str, object]:
    progress_metrics = (
        progress.get("metrics") if isinstance(progress.get("metrics"), dict) else {}
    )
    integrity_current = (
        integrity.get("current")
        if isinstance(integrity.get("current"), dict)
        else {}
    )
    recommendation_ids = {
        str(item.get("id") or "").strip()
        for item in review_recommendations
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }
    activity: list[dict[str, object]] = []
    for log in project_logs:
        log_id = str(log.get("id") or "").strip()
        log_title = str(log.get("title") or log_id or "Project log").strip()
        for entry in (log.get("entries") or [])[-4:]:
            if not isinstance(entry, dict):
                continue
            values = entry.get("values") if isinstance(entry.get("values"), dict) else {}
            # The typed repository-review projection already owns these Source
            # Monitor events. Keeping the corresponding generic log row would
            # show one governance action twice in the compact Overview.
            if (
                log_id == "source-monitor"
                and str(values.get("activity") or "").strip() in recommendation_ids
            ):
                continue
            actor = (
                values.get("agent")
                or values.get("actor")
                or (
                    "Human project governance"
                    if log_id in {"horizon", "changes"}
                    else log_title
                )
            )
            outcome = values.get("outcome") or values.get("result")
            affected_scope = (
                values.get("affected")
                or values.get("record")
                or values.get("record_ids")
            )
            summary = (
                values.get("summary")
                or values.get("change")
                or values.get("activity")
                or values.get("task")
            )
            manager_effect = (
                values.get("manager_action")
                or values.get("manager_effect")
                or values.get("next_action")
            )
            headline = (
                values.get("record")
                or values.get("watcher")
                or values.get("change")
                or outcome
                or entry.get("id")
            )
            activity.append(
                {
                    "id": entry.get("id"),
                    "log": log_id,
                    "date": values.get("date"),
                    "record": values.get("record"),
                    "title": " · ".join(
                        str(value).strip()
                        for value in (actor, headline)
                        if str(value or "").strip()
                    ),
                    "actor": actor,
                    "source": log_title,
                    "outcome": outcome,
                    "affected_scope": affected_scope,
                    "summary": summary,
                    "manager_effect": manager_effect,
                    "owner": values.get("owner") or values.get("agent"),
                    "kind": "project_log",
                    "route": f"logs:{log_id}",
                }
            )
    activity.sort(key=lambda item: str(item.get("date") or ""), reverse=True)
    delivery_items = (
        progress.get("delivery_items")
        if isinstance(progress.get("delivery_items"), list)
        else []
    )
    delivery_available = isinstance(progress.get("delivery_items"), list)
    progress_items = [
        item
        for collection in (
            progress.get("proposals") or [],
            progress.get("candidates") or [],
            delivery_items,
        )
        for item in collection
        if isinstance(item, dict)
    ]
    release_blocker_items = [
        {
            "identifier": item.get("identifier"),
            "title": item.get("title"),
            "priority": item.get("priority"),
            "status": item.get("workflowStatus"),
            "workstream": item.get("workstream"),
            "url": item.get("url"),
            "route": "progress",
        }
        for item in progress_items
        if normalize_console_owner(
            item.get("releaseBlocker") or item.get("release_blocker")
        )
        in {"yes", "true"}
    ]
    critical_high_blockers = [
        item
        for item in release_blocker_items
        if normalize_console_owner(item.get("priority")) in {"critical", "high"}
    ]
    release_fields_available = bool(progress_items) and all(
        ("releaseBlocker" in item or "release_blocker" in item)
        and "priority" in item
        for item in progress_items
    )
    human_actions: list[dict[str, object]] = []
    for item in review_recommendations:
        if normalize_console_owner(item.get("action_owner")) != "human":
            continue
        human_actions.append(
            {
                "id": item.get("id"),
                "kind": "repository_review_decision",
                "label": item.get("human_question") or item.get("recommendation"),
                "priority": "Human decision",
                "route": item.get("console_target") or "logs:source-monitor",
                "source_url": item.get("source_url"),
            }
        )
    for item in progress_items:
        if normalize_console_owner(item.get("workflowStatus")) != "human decision needed":
            continue
        human_actions.append(
            {
                "id": item.get("identifier") or item.get("projectItemId"),
                "kind": "project_human_decision",
                "label": item.get("title"),
                "priority": item.get("priority"),
                "route": "progress",
                "source_url": item.get("url"),
            }
        )
    unresolved_host_actions = [
        item
        for item in run_chain.get("host_action_items") or []
        if isinstance(item, dict)
        and item.get("resolved") is not True
        and normalize_console_owner(item.get("owner")) == "human"
    ]
    for item in unresolved_host_actions:
        action_kind = normalize_console_owner(item.get("kind")).replace(" ", "_")
        if action_kind not in {
            "approval",
            "authorization",
            "credential_required",
            "go_no_go",
            "human_decision",
            "policy_decision",
            "review_decision",
        }:
            # Operational failures belong in the grouped incident projection,
            # even when their recovery owner is human. Retry rows are not
            # separate human decisions.
            continue
        human_actions.append(
            {
                "id": item.get("id"),
                "kind": action_kind,
                "label": item.get("next_action") or item.get("summary"),
                "priority": "Automation attention",
                "route": "automation",
                "source_url": None,
            }
        )
    incident_groups: dict[tuple[str, str], dict[str, object]] = {}
    seen_incident_events: set[tuple[str, str, str]] = set()
    incident_rows = [
        item
        for item in run_chain.get("failures") or []
        if isinstance(item, dict)
    ] + unresolved_host_actions
    for item in incident_rows:
        stage = str(item.get("stage") or "unknown-stage")
        message = str(item.get("message") or item.get("details") or item.get("summary") or "")
        timestamp = str(item.get("recorded_at") or item.get("created_at") or "")
        event_key = (stage, timestamp, normalize_console_owner(message))
        if event_key in seen_incident_events:
            continue
        seen_incident_events.add(event_key)
        prerequisite, root_cause = overview_incident_identity(stage, message)
        key = (prerequisite, normalize_console_owner(root_cause))
        group = incident_groups.setdefault(
            key,
            {
                "incident_id": "incident-"
                + hashlib.sha256(
                    "{}|{}".format(*key).encode("utf-8")
                ).hexdigest()[:16],
                "stage": stage,
                "failed_prerequisite": prerequisite,
                "root_cause": root_cause,
                "classification": (
                    "hold"
                    if "instead of main" in message.casefold()
                    or "non-main" in message.casefold()
                    else item.get("classification") or "blocking"
                ),
                "message": root_cause,
                "occurrence_count": 0,
                "first_seen": timestamp,
                "latest_seen": timestamp,
                "chain_ids": [],
                "route": "automation",
            },
        )
        group["occurrence_count"] = int(group["occurrence_count"]) + int(
            item.get("failure_count") or 1
        )
        if timestamp and (
            not group.get("first_seen") or timestamp < str(group["first_seen"])
        ):
            group["first_seen"] = timestamp
        if timestamp and timestamp > str(group.get("latest_seen") or ""):
            group["latest_seen"] = timestamp
        chain_id = str(item.get("chain_id") or run_chain.get("chain_id") or "")
        if chain_id and chain_id not in group["chain_ids"]:
            group["chain_ids"].append(chain_id)
    active_incidents = sorted(
        incident_groups.values(),
        key=lambda item: str(item.get("latest_seen") or ""),
        reverse=True,
    )
    domain_signals = []
    for domain, payload, timestamp, route in (
        (
            "progress",
            progress,
            progress.get("generated_at") or progress.get("generatedAt"),
            "progress",
        ),
        (
            "integrity",
            integrity,
            integrity.get("generated_at") or integrity_current.get("generated_at"),
            "integrity",
        ),
        (
            "source_checker",
            source_checker,
            source_checker.get("checked_at"),
            "sources:assurance",
        ),
    ):
        availability = str(payload.get("availability") or "")
        if not payload:
            status = "unavailable"
            reason = "No valid feed generation is available."
        elif availability in {"stale", "unavailable"}:
            status = availability
            reason = "The feed does not completely cover its current authoritative source."
        elif not availability:
            status = "contract_unavailable"
            reason = "Legacy feed is present without a declared truth contract."
        else:
            status = availability
            reason = ""
        if status not in {"current", "available"}:
            domain_signals.append(
                {
                    "domain": domain,
                    "status": status,
                    "reason": reason,
                    "timestamp": timestamp,
                    "route": route,
                }
            )
    automation_failures = [
        item for item in run_chain.get("failures") or [] if isinstance(item, dict)
    ]
    if not run_chain:
        domain_signals.append(
            {
                "domain": "automation",
                "status": "unavailable",
                "reason": "No run-chain snapshot is available.",
                "timestamp": None,
                "route": "automation",
            }
        )
    elif automation_failures:
        domain_signals.append(
            {
                "domain": "automation",
                "status": "attention",
                "reason": "The current run chain reports an active failure or hold.",
                "timestamp": run_chain.get("updated_at")
                or run_chain.get("completed_at"),
                "route": "automation",
            }
        )
    release_readiness = (
        publication.get("release_readiness")
        if isinstance(publication.get("release_readiness"), dict)
        else {}
    )
    if release_readiness.get("status") != "ready":
        domain_signals.append(
            {
                "domain": "publication_release",
                "status": release_readiness.get("status") or "unavailable",
                "reason": release_readiness.get("status_explanation")
                or "Release readiness is unavailable.",
                "timestamp": None,
                "route": "publication:analysis",
            }
        )
    material_changes: list[dict[str, object]] = [
        {
            "id": item.get("id"),
            "date": item.get("recorded_at"),
            "kind": "repository_review_recommendation",
            "title": (
                f"{item.get('reviewer') or 'Repository reviewer'} · "
                f"PR #{item.get('pull_request_number')}"
            ),
            "actor": item.get("reviewer") or "Repository reviewer",
            "source": "Source Monitor Log",
            "outcome": "Recommendation recorded",
            "affected_scope": item.get("affected_records")
            or (
                f"{(item.get('affected') or {}).get('total_count')} affected records"
                if isinstance(item.get("affected"), dict)
                and (item.get("affected") or {}).get("total_count") is not None
                else None
            ),
            "summary": item.get("recommendation"),
            "manager_effect": item.get("human_question"),
            "owner": item.get("action_owner"),
            "affected_count": (
                (item.get("affected") or {}).get("total_count")
                if isinstance(item.get("affected"), dict)
                else None
            ),
            "route": item.get("console_target") or "logs:source-monitor",
            "tone": "warning",
        }
        for item in review_recommendations
    ]
    material_changes.extend(activity[:8])
    material_changes.sort(
        key=lambda item: str(item.get("date") or ""), reverse=True
    )
    collapsed_material_changes: list[dict[str, object]] = []
    for item in material_changes:
        outcome_summary = " ".join(
            str(item.get(key) or "") for key in ("outcome", "summary")
        )
        clean_noop = bool(
            re.search(
                r"clean|no.?op|no material|no change|unchanged|succeed|complete",
                outcome_summary,
                re.IGNORECASE,
            )
        ) and not bool(
            re.search(
                r"fail|error|block|warn|finding|changed|update",
                outcome_summary,
                re.IGNORECASE,
            )
        )
        collapse_identity = (
            str(item.get("log") or ""),
            str(item.get("actor") or ""),
            str(item.get("outcome") or ""),
            str(item.get("affected_scope") or ""),
        )
        prior = collapsed_material_changes[-1] if collapsed_material_changes else None
        if (
            clean_noop
            and prior
            and prior.get("_collapse_identity") == collapse_identity
        ):
            count = int(prior.get("collapsed_count") or 1) + 1
            prior.update(
                {
                    "kind": "collapsed_activity",
                    "collapsed_count": count,
                    "title": f"{count} consecutive clean / no-op activities",
                    "affected_scope": f"{count} retained log activities",
                    "summary": (
                        "Consecutive identical routine outcomes are collapsed "
                        "here; the owning log retains every entry."
                    ),
                    "manager_effect": (
                        "No manager action is recorded; open the owning log for "
                        "complete retained history."
                    ),
                }
            )
            continue
        collapsed_material_changes.append(
            {
                **item,
                "collapsed_count": 1,
                "_collapse_identity": collapse_identity if clean_noop else None,
            }
        )
    material_changes = [
        {key: value for key, value in item.items() if key != "_collapse_identity"}
        for item in collapsed_material_changes
    ]
    next_reviews: list[dict[str, object]] = []
    if REVIEW_EPOCHS.is_file():
        epoch_rows = [
            json.loads(line)
            for line in REVIEW_EPOCHS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if epoch_rows:
            epoch = epoch_rows[-1]
            next_reviews.append(
                {
                    "kind": "review_epoch",
                    "label": "Comprehensive Review Epoch",
                    "due_at": epoch.get("next_due_at"),
                    "status": epoch.get("stability_status"),
                    "trigger": epoch.get("triggering_reason"),
                    "route": "logs:agents",
                }
            )
    for item in progress_items:
        next_audit = item.get("nextAudit") or item.get("next_audit")
        if not str(next_audit or "").strip() or normalize_console_owner(
            next_audit
        ) == "not recorded":
            continue
        next_reviews.append(
            {
                "kind": "project_review_trigger",
                "label": item.get("identifier") or item.get("title"),
                "due_at": None,
                "status": item.get("workflowStatus"),
                "trigger": next_audit,
                "route": "progress",
                "source_url": item.get("url"),
            }
        )
    source_completeness = (
        source_checker.get("completeness")
        if isinstance(source_checker.get("completeness"), dict)
        else {}
    )
    integrity_counts = (
        integrity_current.get("counts")
        if isinstance(integrity_current.get("counts"), dict)
        else {}
    )
    integrity_findings_value = integrity_counts.get("findings")
    integrity_findings_available = (
        bool(integrity)
        and str(integrity.get("availability") or "") != "unavailable"
        and isinstance(integrity_findings_value, (int, float))
        and not isinstance(integrity_findings_value, bool)
    )
    return {
        "manager_focus": {
            "human_decisions": len(human_actions),
            "human_actions": human_actions[:20],
            "active_incidents": len(active_incidents),
            "incidents": active_incidents[:10],
            "release_blockers": (
                len(release_blocker_items) if release_fields_available else None
            ),
            "release_blocker_fields_available": release_fields_available,
            "critical_high_release_blockers": (
                len(critical_high_blockers) if release_fields_available else None
            ),
            "critical_high_blocker_items": critical_high_blockers[:15],
            "integrity_findings": (
                int(integrity_findings_value)
                if integrity_findings_available
                else None
            ),
            "integrity_findings_available": integrity_findings_available,
            "source_checker_complete": source_completeness.get("complete"),
            "delivery_items": len(delivery_items) if delivery_available else None,
            "delivery_items_available": delivery_available,
            "domain_attention": domain_signals,
            "next_reviews": next_reviews[:15],
        },
        "queue_counts": {
            "preliminary_candidates": len(candidates),
            "formal_candidates": len(active_horizon_records),
            "monitoring_issues": len(monitoring_issues),
            "pending_sources": len(pending_sources),
            "repository_recommendations": len(review_recommendations),
            "delivery_items": len(delivery_items) if delivery_available else None,
            "human_actions": len(human_actions),
            "active_incidents": len(active_incidents),
            "critical_high_release_blockers": (
                len(critical_high_blockers) if release_fields_available else None
            ),
        },
        "activity": material_changes[:12],
        "agents": {
            "registered": len(agent_registry),
            "last_chain_id": run_chain.get("chain_id") or run_chain.get("id"),
            "chain_status": run_chain.get("status"),
        },
        "services": watcher_metadata,
        "usage": run_chain.get("usage") or run_chain.get("usage_snapshot"),
        "progress_summary": {
            "generated_at": progress.get("generated_at") or progress.get("generatedAt"),
            "source_revision": progress.get("source_revision"),
            "availability": progress.get("availability"),
            "ready": progress_metrics.get("ready"),
            "total": progress_metrics.get("total"),
            "remaining": progress_metrics.get("remaining"),
            "track_status": progress_metrics.get("trackStatus"),
            "delivery_items": len(delivery_items) if delivery_available else None,
        },
        "integrity_summary": {
            "generated_at": integrity.get("generated_at")
            or integrity_current.get("generated_at"),
            "source_revision": integrity.get("source_revision")
            or integrity_current.get("revision"),
            "availability": integrity.get("availability"),
            "result": integrity_current.get("result"),
            "counts": integrity_current.get("counts") or {},
        },
        "automation_summary": {
            "chain_id": run_chain.get("chain_id") or run_chain.get("id"),
            "status": run_chain.get("status"),
            "generated_at": run_chain.get("generated_at")
            or run_chain.get("completed_at"),
            "stage_count": len(run_chain.get("stages") or []),
        },
        "publication_summary": {
            "disposition_counts": publication.get("disposition_counts") or {},
            "build_count": len(publication.get("builds") or []),
            "topic_product_count": len(publication.get("topic_products") or []),
        },
        "source_checker_summary": {
            "checked_at": source_checker.get("checked_at"),
            "source_revision": source_checker.get("source_revision"),
            "availability": source_checker.get("availability"),
            "expected_count": source_checker.get("expected_count"),
            "actual_count": source_checker.get("actual_count"),
            "counts": source_checker.get("counts") or {},
        },
    }


def normalize_console_owner(value: object) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def main() -> None:
    args = parse_args()
    projection_errors: list[dict[str, object]] = []
    candidates = candidate_records()
    cited_sources = catalog_source_records(CITED_SOURCES, "Relied upon")
    pending_sources = catalog_source_records(
        PENDING_SOURCES, "Pending verification or placement"
    )
    presidential_directives = presidential_directive_records()
    horizon_records, github_synced_at = horizon_snapshot(args.refresh_github)
    monitoring_issues = monitoring_issue_snapshot(args.refresh_github, horizon_records)
    court_watch_sources, case_watcher_metadata = case_watcher_snapshot()
    page_inventory = page_inventory_records()
    publication = publication_data(page_inventory)
    project_logs = project_log_views(projection_errors)
    review_recommendations = repository_review_recommendations(projection_errors)
    progress = progress_snapshot()
    integrity = integrity_snapshot()
    run_chain = run_chain_snapshot()
    source_checker = source_checker_snapshot()
    for feed_name, feed in (
        ("progress", progress),
        ("integrity", integrity),
        ("source_checker", source_checker),
    ):
        if not feed:
            projection_errors.append(
                {
                    "code": "required_feed_unavailable",
                    "severity": "error",
                    "feed": feed_name,
                    "message": (
                        f"The {feed_name} feed has no valid complete generation "
                        "for the current Console build."
                    ),
                }
            )
        else:
            if not str(feed.get("generation_id") or "").strip():
                projection_errors.append(
                    {
                        "code": "required_feed_contract_unavailable",
                        "severity": "error",
                        "feed": feed_name,
                        "message": (
                            f"The {feed_name} feed is preserved as legacy data "
                            "but lacks a generation truth contract."
                        ),
                    }
                )
            if str(feed.get("availability") or "") in {"stale", "unavailable"}:
                projection_errors.append(
                    {
                        "code": "required_feed_not_current",
                        "severity": "error",
                        "feed": feed_name,
                        "availability": feed.get("availability"),
                        "message": (
                            f"The {feed_name} feed is present but does not completely "
                            "cover its current authoritative source."
                        ),
                    }
                )
    agent_registry = agent_registry_records()
    horizon_records = enrich_horizon_records(horizon_records, projection_errors)
    active_horizon_records = [
        record for record in horizon_records if record["issue_state"] == "Open"
    ]
    delivery_items = (
        progress.get("delivery_items")
        if isinstance(progress.get("delivery_items"), list)
        else []
    )
    publication["release_readiness"] = publication_release_readiness(
        page_inventory,
        publication.get("builds") or [],
        progress,
        integrity,
    )
    publication["delivery_items"] = delivery_items
    generated_at = utc_timestamp()
    watcher_metadata = {
        "case_monitor": case_watcher_metadata,
        "presidential_directives": directive_watcher_metadata(),
    }
    overview = overview_data(
        candidates=candidates,
        active_horizon_records=active_horizon_records,
        monitoring_issues=monitoring_issues,
        pending_sources=pending_sources,
        review_recommendations=review_recommendations,
        progress=progress,
        integrity=integrity,
        run_chain=run_chain,
        publication=publication,
        project_logs=project_logs,
        agent_registry=agent_registry,
        watcher_metadata=watcher_metadata,
        source_checker=source_checker,
    )
    input_paths = [
        CANDIDATES,
        HORIZON_LOG,
        CHANGE_AUDIT_LOG,
        AGENT_AUDIT_LOG,
        ELIM_RUN_LOG,
        SOURCE_MONITOR_LOG,
        SOURCE_CHECKER_CONFIG,
        ISSUE_REGISTRY,
        CITED_SOURCES,
        PENDING_SOURCES,
        DIRECTIVES,
        CASE_MONITOR_CONFIG,
        DIRECTIVE_MONITOR_CONFIG,
        PRINT_ASSEMBLY_MANIFEST,
        ROOT / "research" / "README.md",
    ]
    hashes = source_hashes(ROOT, input_paths)
    for feed_name, feed in (
        ("progress", progress),
        ("integrity", integrity),
        ("run_chain", run_chain),
        ("source_checker", source_checker),
    ):
        if feed:
            hashes[f"feed:{feed_name}"] = "sha256:" + hashlib.sha256(
                json.dumps(
                    feed, sort_keys=True, separators=(",", ":"), default=str
                ).encode("utf-8")
            ).hexdigest()
    actual_count = (
        len(candidates)
        + len(horizon_records)
        + len(cited_sources)
        + len(pending_sources)
        + len(presidential_directives)
        + len(page_inventory)
        + sum(len(log.get("entries") or []) for log in project_logs)
        + len(review_recommendations)
        + len(delivery_items)
    )
    pagination_sources: list[dict[str, object]] = [
        {
            "source": "horizon-issues",
            "complete": True,
            "actual_count": len(horizon_records),
            "mode": "authenticated-refresh" if args.refresh_github else "preserved-snapshot",
        },
        {
            "source": "monitoring-issues",
            "complete": True,
            "actual_count": len(monitoring_issues),
            "mode": "authenticated-refresh" if args.refresh_github else "preserved-snapshot",
        },
    ]
    for feed_name, feed in (
        ("progress", progress),
        ("source-checker", source_checker),
    ):
        feed_pagination = feed.get("pagination")
        pagination_sources.append(
            {
                "source": feed_name,
                "complete": (
                    isinstance(feed_pagination, dict)
                    and feed_pagination.get("complete") is True
                    and (
                        not isinstance(feed.get("completeness"), dict)
                        or feed["completeness"].get("complete") is True
                    )
                )
                if feed
                else False,
                "details": (
                    feed_pagination if isinstance(feed_pagination, dict) else None
                ),
            }
        )
    generation_contract = feed_contract(
        feed_name="project-console",
        timestamp_field="generated_at",
        timestamp=generated_at,
        revision=source_revision(ROOT),
        hashes=hashes,
        expected_count=actual_count,
        actual_count=actual_count,
        pagination={
            "complete": all(
                item.get("complete") is True for item in pagination_sources
            ),
            "sources": pagination_sources,
        },
        projection_errors=projection_errors,
    )
    payload = {
        "schema_version": 27,
        **generation_contract,
        "github_synced_at": github_synced_at,
        "candidate_questions": len(candidates),
        "horizon_issue_count": len(active_horizon_records),
        "records": candidates,
        "active_horizon_records": active_horizon_records,
        "cited_sources": cited_sources,
        "monitoring_issues": monitoring_issues,
        "court_watch_sources": court_watch_sources,
        "presidential_directives": presidential_directives,
        "watcher_metadata": watcher_metadata,
        "pending_sources": pending_sources,
        "page_inventory": page_inventory,
        "publication": publication,
        "topic_products": publication.get("topic_products") or [],
        "delivery_items": delivery_items,
        "project_logs": project_logs,
        "repository_review_recommendations": review_recommendations,
        "progress": progress,
        "integrity": integrity,
        "run_chain": run_chain,
        "source_checker": source_checker,
        "agent_registry": agent_registry,
        "overview": overview,
        # The full snapshot is retained only so an ordinary rebuild can preserve
        # authoritative GitHub state without requiring Keychain access.
        "horizon_records": horizon_records,
    }
    def select(record: dict[str, object], keys: tuple[str, ...]) -> dict[str, object]:
        return {key: record.get(key) for key in keys if key in record}

    compatibility_payload = {
        "schema_version": payload["schema_version"],
        **generation_contract,
        "github_synced_at": github_synced_at,
        "candidate_questions": len(candidates),
        "horizon_issue_count": len(active_horizon_records),
        "records": [
            select(record, ("id", "title", "summary", "kind"))
            for record in candidates
        ],
        "active_horizon_records": [
            {
                **select(record, ("id", "title", "issue_url", "workflow_status")),
                "horizon_history": select(
                    record.get("horizon_history", {})
                    if isinstance(record.get("horizon_history"), dict)
                    else {},
                    ("original_concern",),
                ),
            }
            for record in active_horizon_records
        ],
        "monitoring_issues": [
            select(record, ("id", "title", "summary", "issue_url"))
            for record in monitoring_issues
        ],
        "repository_review_recommendations": review_recommendations,
        "overview": overview,
    }
    source_chunk_count = 16
    source_chunk_size = max(1, math.ceil(len(cited_sources) / source_chunk_count))
    source_chunks = {
        f"sources-catalog-{bucket + 1:03d}.js": {
            f"cited_sources_chunk_{bucket + 1:03d}":
                cited_sources[
                    bucket * source_chunk_size:(bucket + 1) * source_chunk_size
                ]
        }
        for bucket in range(source_chunk_count)
    }
    directive_chunk_count = 16
    directive_chunk_size = max(
        1, math.ceil(len(presidential_directives) / directive_chunk_count)
    )
    directive_chunks = {
        f"directives-catalog-{bucket + 1:03d}.js": {
            f"presidential_directives_chunk_{bucket + 1:03d}":
                presidential_directives[
                    bucket * directive_chunk_size:(bucket + 1) * directive_chunk_size
                ]
        }
        for bucket in range(directive_chunk_count)
    }
    parts = {
        "overview.js": {
            "overview": overview,
        },
        "candidates.js": {
            "records": candidates,
            "active_horizon_records": active_horizon_records,
            # Retained so an ordinary rebuild can preserve authenticated GitHub
            # state without requiring Keychain access.
            "horizon_records": horizon_records,
        },
        "sources.js": {
            "cited_sources": [],
            "monitoring_issues": monitoring_issues,
            "court_watch_sources": court_watch_sources,
            "presidential_directives": [],
            "watcher_metadata": payload["watcher_metadata"],
            "pending_sources": pending_sources,
        },
        "source-checker.js": {"source_checker": source_checker},
        "progress.js": {"progress": progress},
        "integrity.js": {"integrity": integrity},
        "automation.js": {
            "agent_registry": agent_registry,
            "run_chain": run_chain,
        },
        "logs.js": {
            "project_logs": project_logs,
            "repository_review_recommendations": review_recommendations,
        },
        "publication.js": {
            "page_inventory": page_inventory,
            "publication": publication,
            "topic_products": publication.get("topic_products") or [],
            "delivery_items": delivery_items,
        },
        **source_chunks,
        **directive_chunks,
    }
    write_console_bundle(
        compatibility_payload,
        parts,
        generation_contract=generation_contract,
    )

    if args.console_only:
        print(
            f"Wrote {OUTPUT.relative_to(ROOT)} with {len(candidates)} preliminary "
            f"candidates, {len(active_horizon_records)} active proposed candidates, "
            f"{len(cited_sources)} cited sources, {len(monitoring_issues)} monitored "
            f"issues, {len(pending_sources)} pending sources, and "
            f"{len(presidential_directives)} presidential directives, plus "
            f"{len(page_inventory)} publication-controlled pages and "
            f"{sum(len(log['entries']) for log in project_logs)} project-log entries."
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
    atomic_write_text(
        PARTICIPATION_OUTPUT,
        "/* Generated by scripts/build_horizon_review_console.py. */\n"
        f"window.ARRP_PARTICIPATION_DATA={participation_serialized};\n",
    )
    print(
        f"Wrote {OUTPUT.relative_to(ROOT)} and {PARTICIPATION_OUTPUT.relative_to(ROOT)} "
        f"with {len(candidates)} preliminary candidates and "
        f"{len(active_horizon_records)} active proposed candidates, "
        f"{len(cited_sources)} cited sources, {len(monitoring_issues)} monitored "
        f"issues, {len(pending_sources)} pending sources, and "
        f"{len(presidential_directives)} presidential directives, plus "
        f"{len(page_inventory)} publication-controlled pages and "
        f"{sum(len(log['entries']) for log in project_logs)} project-log entries."
    )


if __name__ == "__main__":
    main()
