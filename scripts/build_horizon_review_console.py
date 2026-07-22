#!/usr/bin/env python3
"""Build the ARRP Project Console and public-input lookup."""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import os
import re
import subprocess
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "research" / "trump-administration-preliminary-candidates.csv"
HORIZON_LOG = ROOT / "framework" / "logs" / "HORIZON_SCAN_LOG.md"
CHANGE_AUDIT_LOG = ROOT / "framework" / "logs" / "CHANGE_AUDIT_LOG.md"
AGENT_AUDIT_LOG = ROOT / "framework" / "logs" / "AGENT_AUDIT_LOG.md"
SOURCE_MONITOR_LOG = ROOT / "framework" / "logs" / "SOURCE_MONITOR_LOG.md"
CURRENT_AUDIT = ROOT / "framework" / "logs" / "CURRENT_AUDIT.md"
ISSUE_REGISTRY = ROOT / "inventory" / "github_issue_registry.csv"
CITED_SOURCES = ROOT / "inventory" / "sources.csv"
PENDING_SOURCES = ROOT / "inventory" / "sources-pending.csv"
DIRECTIVES = ROOT / "inventory" / "presidential-directives.csv"
CASE_MONITOR_CONFIG = ROOT / ".github" / "case-monitor-bot.json"
DIRECTIVE_MONITOR_CONFIG = ROOT / ".github" / "presidential-directives-bot.json"
PRINT_ASSEMBLY_MANIFEST = ROOT / "framework" / "print-assembly.json"
PUBLIC_PROPOSAL_PDF = ROOT / "exports" / "pdf" / "ARRP-public-proposal-draft.pdf"
OUTPUT = ROOT / "research" / "horizon-review-console" / "catalog-data.js"
PARTICIPATION_OUTPUT = ROOT / "participate" / "intake-data.js"
GITHUB_BLOB_ROOT = "https://github.com/Thorncrag/ARRP/blob/main/"
HORIZON_LOG_URL = GITHUB_BLOB_ROOT + "framework/logs/HORIZON_SCAN_LOG.md#horizon-integration-log"
PROGRESS_DATA_REF = "origin/project-console-data:progress.json"
INTEGRITY_DATA_REF = "origin/project-console-data:integrity.json"
LOCAL_INTEGRITY_FEED = ROOT / ".tmp" / "project-console-integrity.json"
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
    for path in ROOT.rglob("*.md"):
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

    def code_replacement(match: re.Match[str]) -> str:
        return preserve(f"<code>{html.escape(match.group(1))}</code>")

    protected = re.sub(r"`([^`\n]+)`", code_replacement, value)

    def link_replacement(match: re.Match[str]) -> str:
        label = render_markdown_inline(match.group(1))
        target = safe_markdown_url(match.group(2))
        if not target:
            return preserve(label)
        return preserve(
            f'<a href="{html.escape(target, quote=True)}" target="_blank" '
            f'rel="noopener noreferrer">{label}</a>'
        )

    protected = re.sub(r"\[([^]\n]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", link_replacement, protected)
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
    content: str, required_headers: tuple[str, ...]
) -> list[dict[str, str]]:
    """Return rows from the first Markdown table matching the requested headers."""
    lines = content.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    for index in range(len(lines) - 1):
        if "|" not in lines[index] or not is_markdown_table_separator(lines[index + 1]):
            continue
        headers = markdown_table_cells(lines[index])
        if tuple(headers) != required_headers:
            continue
        rows: list[dict[str, str]] = []
        index += 2
        while index < len(lines) and lines[index].strip() and "|" in lines[index]:
            cells = markdown_table_cells(lines[index])
            cells = cells[: len(headers)] + [""] * max(0, len(headers) - len(cells))
            rows.append(dict(zip(headers, cells)))
            index += 1
        return rows
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


def horizon_log_view() -> dict[str, object]:
    headers = (
        "Horizon ID", "Decision date", "Original concern", "Decision",
        "Integrated into", "Rationale", "Follow-up",
    )
    entries: list[dict[str, object]] = []
    for row in markdown_table_records(HORIZON_LOG.read_text(encoding="utf-8"), headers):
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
        "entries": entries,
    }


def change_audit_log_view() -> dict[str, object]:
    headers = (
        "Date", "Change audited", "Scope", "Score/rebaseline effect",
        "Findings and corrections",
    )
    entries: list[dict[str, object]] = []
    for index, row in enumerate(
        markdown_table_records(CHANGE_AUDIT_LOG.read_text(encoding="utf-8"), headers), 1
    ):
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


def two_column_fields(content: str) -> dict[str, str]:
    rows = markdown_table_records(content, ("Field", "Entry"))
    return {strip_markdown(row["Field"]): row["Entry"] for row in rows}


def agent_audit_log_view() -> dict[str, object]:
    entries: list[dict[str, object]] = []
    content = AGENT_AUDIT_LOG.read_text(encoding="utf-8")
    for index, (title, body) in enumerate(section_records(content, 3, "## Log"), 1):
        fields = two_column_fields(body)
        if not fields:
            continue
        header_parts = [part.strip() for part in title.split("—")]
        values = {
            "date": strip_markdown(fields.get("Date/time", header_parts[0] if header_parts else "")),
            "record": strip_markdown(fields.get("Issue/task", header_parts[1] if len(header_parts) > 1 else "")),
            "tier": strip_markdown(fields.get("Tier", header_parts[2] if len(header_parts) > 2 else "")),
            "agent": strip_markdown(fields.get("Run/agent", "")),
            "status": strip_markdown(fields.get("Push status", "")),
        }
        entries.append(log_entry(f"agent-{index:03d}", values, {
            "date": fields.get("Date/time", ""),
            "record": fields.get("Issue/task", ""),
            "tier": fields.get("Tier", ""),
            "agent": fields.get("Run/agent", ""),
            "status": fields.get("Push status", ""),
        }, body))
    return {
        "id": "agents",
        "title": "Agent Audit Log",
        "description": "Autonomous, batched, and scheduled agent-run provenance and rollback records.",
        "source_url": GITHUB_BLOB_ROOT + "framework/logs/AGENT_AUDIT_LOG.md",
        "columns": [
            {"key": "date", "label": "Date and time"},
            {"key": "record", "label": "Issue or task"},
            {"key": "tier", "label": "Tier or task"},
            {"key": "agent", "label": "Run or agent"},
            {"key": "status", "label": "Push status"},
        ],
        "group_options": [
            {"key": "tier", "label": "Tier or task"},
            {"key": "record", "label": "Issue or task"},
            {"key": "agent", "label": "Run or agent"},
        ],
        "default_sort": {"key": "date", "direction": "desc"},
        "entries": entries,
    }


def bullet_fields(content: str) -> dict[str, str]:
    return {
        strip_markdown(match.group(1)): match.group(2).strip()
        for match in re.finditer(r"^-\s+([^:\n]+):\s*(.+)$", content, re.MULTILINE)
    }


def source_monitor_log_view() -> dict[str, object]:
    entries: list[dict[str, object]] = []
    content = SOURCE_MONITOR_LOG.read_text(encoding="utf-8")
    for index, (title, body) in enumerate(section_records(content, 2), 1):
        if not re.match(r"\d{4}-\d{2}-\d{2}", title):
            continue
        parts = [part.strip() for part in title.split("—", 1)]
        fields = bullet_fields(body)
        values = {
            "date": strip_markdown(parts[0]),
            "watcher": strip_markdown(parts[1] if len(parts) > 1 else ""),
            "result": strip_markdown(fields.get("Result", "")),
            "affected": strip_markdown(fields.get("Affected source IDs", fields.get("Affected directive IDs", ""))),
            "activity": strip_markdown(fields.get("Activity code", "")),
        }
        entries.append(log_entry(f"source-monitor-{index:03d}", values, {
            "date": parts[0],
            "watcher": parts[1] if len(parts) > 1 else "",
            "result": fields.get("Result", ""),
            "affected": fields.get("Affected source IDs", fields.get("Affected directive IDs", "")),
            "activity": fields.get("Activity code", ""),
        }, body))
    return {
        "id": "source-monitor",
        "title": "Source Monitor Log",
        "description": "Material changes detected by deterministic source and directive watchers.",
        "source_url": GITHUB_BLOB_ROOT + "framework/logs/SOURCE_MONITOR_LOG.md",
        "columns": [
            {"key": "date", "label": "Date and time"},
            {"key": "watcher", "label": "Watcher"},
            {"key": "result", "label": "Result"},
            {"key": "affected", "label": "Affected records"},
            {"key": "activity", "label": "Activity code"},
        ],
        "group_options": [
            {"key": "watcher", "label": "Watcher"},
            {"key": "result", "label": "Result"},
        ],
        "default_sort": {"key": "date", "direction": "desc"},
        "entries": entries,
    }


def project_log_views() -> list[dict[str, object]]:
    return [
        horizon_log_view(),
        agent_audit_log_view(),
        source_monitor_log_view(),
        change_audit_log_view(),
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


def monitoring_rationale_for_record(registry_row: dict[str, str], issue_body: str = "") -> str:
    """Return the most specific available human-authored monitoring instruction."""
    canonical = registry_row.get("Canonical Record", "").strip()
    if canonical:
        path = ROOT / canonical
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            match = re.search(r'^audit_next:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
            if match and match.group(1).strip():
                return strip_markdown(match.group(1))
            section = re.search(
                r"^##\s+(?:Watching for updates|Defined monitoring and research triggers|Next step)\s*$"
                r"(.*?)(?=^##\s+|\Z)",
                content,
                re.MULTILINE | re.DOTALL | re.IGNORECASE,
            )
            if section:
                return strip_markdown(section.group(1))
    if issue_body:
        section = re.search(
            r"^##\s+(?:Watching for updates|Defined monitoring and research triggers|Next step)\s*$"
            r"(.*?)(?=^##\s+|\Z)",
            issue_body,
            re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )
        if section:
            return strip_markdown(section.group(1))
    return "The owning issue is marked for monitoring, but its specific trigger has not yet been structured."


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


def existing_console_payload() -> dict[str, object]:
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
        return json.loads(text.removeprefix(prefix).removesuffix(";\n"))
    except json.JSONDecodeError:
        return {}


def progress_snapshot() -> dict[str, object]:
    """Read the latest generated progress data without making it authoritative."""
    local_progress = os.environ.get("ARRP_PROGRESS_SNAPSHOT", "").strip()
    if local_progress:
        try:
            payload = json.loads(Path(local_progress).read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except (OSError, json.JSONDecodeError):
            pass
    try:
        completed = subprocess.run(
            ["git", "show", PROGRESS_DATA_REF],
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
    cached = existing.get("progress", existing.get("progress_dashboard", {}))
    return cached if isinstance(cached, dict) else {}


def integrity_snapshot() -> dict[str, object]:
    """Read the latest generated integrity feed without making it authoritative."""
    if LOCAL_INTEGRITY_FEED.exists():
        try:
            payload = json.loads(LOCAL_INTEGRITY_FEED.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
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
        if isinstance(payload, dict):
            return payload
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    existing = existing_console_payload()
    cached = existing.get("integrity", {})
    return cached if isinstance(cached, dict) else {}


def current_consistency_audit() -> dict[str, object]:
    """Expose the current long-form consistency findings without creating another audit log."""
    if not CURRENT_AUDIT.exists():
        return {}
    content = CURRENT_AUDIT.read_text(encoding="utf-8")
    task = two_column_fields(content)
    entries: list[dict[str, str]] = []
    labels = ("Disposition", "Problem", "Why it mattered", "Correction", "Effect", "Remaining work")
    for title, body in section_records(content, 3, "## Detailed Findings and Corrections"):
        fields: dict[str, str] = {}
        for label in labels:
            match = re.search(
                rf"^- \*\*{re.escape(label)}:\*\*\s*(.+?)(?=^- \*\*[^\n]+:\*\*|\Z)",
                body,
                re.MULTILINE | re.DOTALL,
            )
            fields[label.lower().replace(" ", "_")] = strip_markdown(match.group(1).strip()) if match else ""
        if fields["problem"]:
            entries.append({"title": strip_markdown(title), **fields})
    return {
        "title": str(task.get("Active issue/task", "Latest consistency audit")),
        "status": strip_markdown(str(task.get("Status", ""))),
        "last_checkpoint": strip_markdown(str(task.get("Last checkpoint", ""))),
        "records_checked": 371,
        "entries": entries,
        "source_path": "framework/logs/CURRENT_AUDIT.md",
        "source_url": GITHUB_BLOB_ROOT + "framework/logs/CURRENT_AUDIT.md#detailed-findings-and-corrections",
    }


def existing_horizon_snapshot() -> tuple[list[dict[str, object]], str]:
    payload = existing_console_payload()
    return payload.get("horizon_records", []), str(payload.get("github_synced_at", ""))


def source_count_for_record(record_id: str) -> int:
    return sum(
        record_id in associated_record_ids(row["Associated Record IDs"])
        for row in all_source_records()
    )


def monitoring_issue_snapshot(refresh: bool) -> list[dict[str, object]]:
    eligible_kinds = {"proposal", "horizon"}
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
                        "monitoring_rationale": monitoring_rationale_for_record(registry),
                    }
                )
            return enriched
        raise RuntimeError(
            "No preserved GitHub monitoring snapshot exists. Re-run with "
            "--refresh-github in an authenticated host context."
        )

    issues = run_gh_json(
        [
            "issue", "list", "--repo", "Thorncrag/ARRP", "--label",
            "needs: monitoring", "--state", "open", "--limit", "200", "--json",
            "number,title,state,url,labels,updatedAt,body",
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
) -> list[dict[str, object]]:
    history_by_id = horizon_log_records()
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


def main() -> None:
    args = parse_args()
    candidates = candidate_records()
    cited_sources = catalog_source_records(CITED_SOURCES, "Relied upon")
    pending_sources = catalog_source_records(
        PENDING_SOURCES, "Pending verification or placement"
    )
    presidential_directives = presidential_directive_records()
    horizon_records, github_synced_at = horizon_snapshot(args.refresh_github)
    monitoring_issues = monitoring_issue_snapshot(args.refresh_github)
    court_watch_sources, case_watcher_metadata = case_watcher_snapshot()
    page_inventory = page_inventory_records()
    publication = publication_data(page_inventory)
    project_logs = project_log_views()
    progress = progress_snapshot()
    integrity = integrity_snapshot()
    horizon_records = enrich_horizon_records(horizon_records)
    active_horizon_records = [
        record for record in horizon_records if record["issue_state"] == "Open"
    ]
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {
        "schema_version": 20,
        "generated_at": generated_at,
        "github_synced_at": github_synced_at,
        "candidate_questions": len(candidates),
        "horizon_issue_count": len(active_horizon_records),
        "records": candidates,
        "active_horizon_records": active_horizon_records,
        "cited_sources": cited_sources,
        "monitoring_issues": monitoring_issues,
        "court_watch_sources": court_watch_sources,
        "presidential_directives": presidential_directives,
        "watcher_metadata": {
            "case_monitor": case_watcher_metadata,
            "presidential_directives": directive_watcher_metadata(),
        },
        "pending_sources": pending_sources,
        "page_inventory": page_inventory,
        "publication": publication,
        "project_logs": project_logs,
        "progress": progress,
        "integrity": integrity,
        "consistency_audit": current_consistency_audit(),
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
    PARTICIPATION_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PARTICIPATION_OUTPUT.write_text(
        "/* Generated by scripts/build_horizon_review_console.py. */\n"
        f"window.ARRP_PARTICIPATION_DATA={participation_serialized};\n",
        encoding="utf-8",
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
