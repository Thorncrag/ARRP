#!/usr/bin/env python3
"""Build the candidate-and-source intake console and public-input lookup."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import subprocess
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "research" / "trump-administration-preliminary-candidates.csv"
HORIZON_LOG = ROOT / "framework" / "logs" / "HORIZON_SCAN_LOG.md"
ISSUE_REGISTRY = ROOT / "inventory" / "github_issue_registry.csv"
CITED_SOURCES = ROOT / "inventory" / "sources.csv"
PENDING_SOURCES = ROOT / "inventory" / "sources-pending.csv"
DIRECTIVES = ROOT / "inventory" / "presidential-directives.csv"
CASE_MONITOR_CONFIG = ROOT / ".github" / "case-monitor-bot.json"
DIRECTIVE_MONITOR_CONFIG = ROOT / ".github" / "presidential-directives-bot.json"
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
    return sorted(records, key=lambda row: (str(row["signed_date"]), str(row["id"])))


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


def existing_horizon_snapshot() -> tuple[list[dict[str, object]], str]:
    payload = existing_console_payload()
    return payload.get("horizon_records", []), str(payload.get("github_synced_at", ""))


def source_count_for_record(record_id: str) -> int:
    return sum(
        record_id in associated_record_ids(row["Associated Record IDs"])
        for row in all_source_records()
    )


def monitoring_issue_snapshot(refresh: bool) -> list[dict[str, object]]:
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
                sources = sources_for_record(record_id)
                registry = registry_by_id.get(record_id, {})
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
    kind_labels = {
        "proposal": "Proposal",
        "horizon": "Candidate",
        "source review": "Maintained research",
    }
    records: list[dict[str, object]] = []
    for issue in issues:
        registry = registry_by_number.get(issue["number"], {})
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
                "status": project_item.get("status") or "Project status unavailable",
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


def case_watcher_snapshot(
    monitoring_issues: list[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Project court sources eligible for tracker-assisted mapping and verification."""
    if not CASE_MONITOR_CONFIG.exists():
        return [], {"enabled": False, "mode": "Not configured"}
    config = json.loads(CASE_MONITOR_CONFIG.read_text(encoding="utf-8"))
    eligible_types = {
        str(value).strip().casefold()
        for value in config.get(
            "eligibleSourceTypes",
            [
                "Court Docket or Judicial Record",
                "Court Filing or Judicial Record",
                "Court Docket",
                "Judicial Docket",
                "Supreme Court Docket",
                "Federal Court Docket",
                "Official court record",
            ],
        )
    }
    verification = config.get("verification", config.get("provider", {}))
    allowed_hosts = set(verification.get("allowedHosts", []))
    records: list[dict[str, object]] = []
    for issue in monitoring_issues:
        for source in issue.get("sources", []):
            if source.get("monitoring") != "Yes":
                continue
            if str(source.get("type", "")).strip().casefold() not in eligible_types:
                continue
            host = urllib.parse.urlsplit(str(source.get("url", ""))).hostname or ""
            if host not in allowed_hosts:
                continue
            rationale = (
                source.get("monitoring_rationale")
                or issue.get("monitoring_rationale")
                or source.get("proposition")
            )
            records.append(
                {
                    **source,
                    "owner_id": issue["id"],
                    "owner_title": issue["title"],
                    "owner_kind": issue["kind"],
                    "owner_status": issue["status"],
                    "owner_issue_url": issue["issue_url"],
                    "monitoring_rationale": rationale,
                    "monitoring_group": source.get("monitoring_group") or issue["id"],
                    "coverage": "Eligible for tracker-assisted mapping and targeted verification",
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
    court_watch_sources, case_watcher_metadata = case_watcher_snapshot(monitoring_issues)
    horizon_records = enrich_horizon_records(horizon_records)
    active_horizon_records = [
        record for record in horizon_records if record["issue_state"] == "Open"
    ]
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {
        "schema_version": 11,
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
            f"{len(presidential_directives)} presidential directives."
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
        f"{len(presidential_directives)} presidential directives."
    )


if __name__ == "__main__":
    main()
