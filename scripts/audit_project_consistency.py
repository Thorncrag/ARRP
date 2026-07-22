#!/usr/bin/env python3
"""Run ARRP's non-scoring repository-consistency checks.

This linter is an evolving baseline for structure, routing, and reader-facing
drift—not an exhaustive ceiling. Auditors must investigate credible problems
outside its current checks and add objectively repeatable verified discoveries
to this script or the test suite. It does not evaluate proposal merits, source
sufficiency, legal conclusions, or Proposal Quality Scores; those questions
remain issue-specific audit work.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]
ISSUE_PATH = ROOT / "areas"
LEGISLATION_PATH = ROOT / "legislation"
REGISTRY_PATH = ROOT / "inventory" / "github_issue_registry.csv"
SOURCE_PATH = ROOT / "inventory" / "sources.csv"
PENDING_SOURCE_PATH = ROOT / "inventory" / "sources-pending.csv"
PRELIMINARY_CANDIDATE_PATH = ROOT / "research" / "trump-administration-preliminary-candidates.csv"
GITHUB_REPOSITORY = "Thorncrag/ARRP"
GITHUB_PROJECT_OWNER = "Thorncrag"
GITHUB_PROJECT_NUMBER = 2
GITHUB_BLOB_PREFIX = f"https://github.com/{GITHUB_REPOSITORY}/blob/main/"
VALID_ISSUE_STATUSES = {
    "awaiting-merits-adjudication",
    "candidate",
    "deferred",
    "developed",
    "in-development",
    "retired",
}
VALID_REBASELINE_STATUSES = {
    "current",
    "current-fixed-status",
    "hard-rebaseline-needed",
    "rebaseline-complete",
    "soft-rebaseline-needed",
}
PROJECT_REBASELINE_VALUES = {
    "current": "Current",
    "current-fixed-status": "Current fixed status",
    "hard-rebaseline-needed": "Hard rebaseline needed",
    "rebaseline-complete": "Rebaseline complete",
    "soft-rebaseline-needed": "Soft rebaseline needed",
}
READY_PROJECT_DEVELOPMENT_LEVELS = {
    "release candidate",
    "review ready",
}
PROJECT_DEVELOPMENT_LEVELS = {
    "candidate",
    "admitted / undeveloped",
    "defined proposal",
    "developed proposal",
    "review ready",
    "release candidate",
}
AUTHORITATIVE_SOURCE_RECORDS = (
    (
        PRELIMINARY_CANDIDATE_PATH,
        ("source_record_ids", "source_links", "institutional_defect", "recommendation"),
    ),
)
TOOL_INTERFACES = (
    (
        ROOT / "research" / "horizon-review-console" / "index.html",
        ROOT / "research" / "horizon-review-console" / "styles.css",
    ),
    (ROOT / "participate" / "index.html", ROOT / "participate" / "styles.css"),
)
CURRENT_INTAKE_WORKFLOW_FILES = (
    ROOT / "framework" / "FRAMEWORK.md",
    ROOT / "framework" / "AGENT_OPERATING_RULES.md",
    ROOT / "framework" / "INTAKE_AGENT_PROCESS.md",
    ROOT / "framework" / "PROJECT_STRUCTURE.md",
    ROOT / "participate" / "README.md",
    ROOT / "participate" / "SECURITY.md",
    ROOT / "research" / "README.md",
    ROOT / "research" / "horizon-review-console" / "README.md",
    ROOT / "research" / "trump-administration-legal-review-summary.md",
    ROOT / "website" / "README.md",
)

MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
MARKDOWN_FENCE_RE = re.compile(r"^(?:```|~~~).*?^(?:```|~~~)\s*$", re.MULTILINE | re.DOTALL)
HTML_LINK_RE = re.compile(r"(?:href|src)\s*=\s*([\"'])(.*?)\1", re.IGNORECASE)
GITHUB_REPOSITORY_URL_RE = re.compile(
    r"https://(?:github\.com/Thorncrag/ARRP/(?:blob|tree)|raw\.githubusercontent\.com/Thorncrag/ARRP)/"
    r"(?P<ref>[^/\\\s)<>\"',\]}]+)/(?P<path>[^\\\s)<>\"',\]}]+)"
)
FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
ISSUE_ID_RE = re.compile(r"^[A-Z]+-\d{3}$")
PRINT_LEVELS = {
    "public-proposal",
    "legislative-appendix",
    "executive-summary",
}

ACTIVE_TREE_EXCLUSIONS = {
    ".git",
    ".site-build",
    ".tmp",
    ".venv",
    "__pycache__",
    "archive",
}
REPOSITORY_LINK_TEXT_SUFFIXES = {
    ".csv",
    ".html",
    ".js",
    ".json",
    ".md",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

REQUIRED_ISSUE_HEADINGS = (
    "Institutional Anomaly",
    "Manifestations? of the Failure",
    "Resulting Damage",
    "Underlying Weakness",
    "Proposal Survey",
    "Least-Complex Adequate Remedy",
    "Repair and Prevention",
    "Budgetary Impact Statements?",
    "Proposal Scoring",
    "Annotation",
)

READER_LANGUAGE_PATTERNS = {
    "unexplained audit-tier shorthand": re.compile(r"\bT[0-4]\b"),
    "unexplained Change Audit terminology": re.compile(r"\bChange Audit\b"),
    "unexplained rebaseline terminology": re.compile(r"\brebaseline\b", re.IGNORECASE),
    "loaded shorthand": re.compile(r"\bsham\b", re.IGNORECASE),
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def front_matter(path: Path) -> dict[str, str]:
    match = FRONT_MATTER_RE.match(read(path))
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line.startswith((" ", "-")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def front_matter_list(path: Path, key: str) -> list[str]:
    """Return a simple YAML list from the project's constrained front matter."""
    match = FRONT_MATTER_RE.match(read(path))
    if not match:
        return []
    values: list[str] = []
    active = False
    for line in match.group(1).splitlines():
        if line == f"{key}:":
            active = True
            continue
        if active and line.startswith("  - "):
            value = line[4:].strip().strip('"\'')
            if value:
                values.append(value)
            continue
        if active:
            break
    return values


def markdown_body(path: Path) -> str:
    return FRONT_MATTER_RE.sub("", read(path), count=1)


def local_target(path: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().strip("<>").split(" ", 1)[0]
    if not target or target.startswith(("#", "http://", "https://", "mailto:", "data:")):
        return None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not target:
        return None
    if path == ROOT / "website" / "404.md" and target == "index.md":
        return ROOT / "README.md"
    link_base = ROOT if path == ROOT / "website" / "404.md" else path.parent
    return (link_base / target).resolve()


def active_project_files(*suffixes: str) -> list[Path]:
    """Return files in the active project tree, excluding generated and historical copies."""
    allowed = set(suffixes)
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower() in allowed
        and not ACTIVE_TREE_EXCLUSIONS.intersection(path.relative_to(ROOT).parts)
    )


def issue_pages() -> list[Path]:
    return sorted(path for path in ISSUE_PATH.glob("*/issues/*.md") if not path.name.endswith(".audit.md"))


def research_files(*suffixes: str) -> list[Path]:
    """Return maintained cross-project and area-owned research files."""
    allowed = set(suffixes)
    paths = [
        path
        for path in (ROOT / "research").rglob("*")
        if path.is_file()
        and path.suffix.lower() in allowed
        and "horizon-review-console" not in path.relative_to(ROOT).parts
    ]
    paths.extend(
        path
        for path in (ROOT / "areas").glob("*/research/*")
        if path.is_file() and path.suffix.lower() in allowed
    )
    return sorted(set(paths))


def report(category: str, message: str, failures: list[str], warnings: list[str]) -> None:
    (failures if category == "ERROR" else warnings).append(f"{category}: {message}")


def normalized_text(value: object) -> str:
    """Normalize controlled prose fields without erasing substantive wording."""
    return " ".join(str(value or "").strip().casefold().split())


def markdown_heading_title(path: Path) -> str:
    match = re.search(r"^#\s+(?:[A-Z]+-\d{3}\s+[—-]\s+)?(.+?)\s*$", markdown_body(path), re.MULTILINE)
    return match.group(1).strip() if match else ""


def markdown_anchor_ids(path: Path) -> set[str]:
    """Return conservative GitHub/MkDocs-compatible anchors for a Markdown page."""
    body = MARKDOWN_FENCE_RE.sub("", markdown_body(path))
    anchors = set(re.findall(r"\bid=[\"']([^\"']+)[\"']", body))
    counts: Counter[str] = Counter()
    for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", body, re.MULTILINE):
        heading = match.group(1).strip()
        explicit = re.search(r"\{#([^}\s]+)[^}]*\}\s*$", heading)
        if explicit:
            anchors.add(explicit.group(1))
            heading = heading[: explicit.start()].strip()
        heading = re.sub(r"\s+\{[^}]+\}\s*$", "", heading)
        heading = re.sub(r"!?(?:\[([^]]*)\])\([^)]*\)", r"\1", heading)
        heading = re.sub(r"[`*_~]", "", heading)
        heading = re.sub(r"<[^>]+>", "", heading)
        slug = re.sub(r"[^\w\- ]", "", heading.casefold(), flags=re.UNICODE)
        slug = re.sub(r"[\s\-]+", "-", slug).strip("-")
        if not slug:
            continue
        occurrence = counts[slug]
        counts[slug] += 1
        anchors.add(slug if occurrence == 0 else f"{slug}-{occurrence}")
        anchors.add(slug if occurrence == 0 else f"{slug}_{occurrence}")
    return anchors


def check_markdown_fragment(
    target: Path,
    fragment: str,
    source_label: str,
    failures: list[str],
    warnings: list[str],
) -> None:
    if not fragment or target.suffix.lower() != ".md" or not target.exists():
        return
    decoded = unquote(fragment).strip()
    if decoded and decoded not in markdown_anchor_ids(target):
        report(
            "ERROR",
            f"broken Markdown heading anchor in {source_label}: #{decoded} "
            f"(missing in {target.relative_to(ROOT)})",
            failures,
            warnings,
        )


def check_issue_pages(failures: list[str], warnings: list[str]) -> dict[str, Path]:
    pages = issue_pages()
    known: dict[str, Path] = {}
    for path in pages:
        data = front_matter(path)
        issue_id = data.get("issue_id", "")
        if not ISSUE_ID_RE.fullmatch(issue_id):
            report("ERROR", f"{path.relative_to(ROOT)} lacks a valid issue_id", failures, warnings)
            continue
        if issue_id != path.stem:
            report("ERROR", f"{path.relative_to(ROOT)} issue_id {issue_id} does not match filename", failures, warnings)
        if issue_id in known:
            report("ERROR", f"duplicate issue page identifier {issue_id}", failures, warnings)
        known[issue_id] = path
        body = markdown_body(path)
        relative = path.relative_to(ROOT)
        area = path.parents[1].name
        if issue_id.split("-", 1)[0] != area:
            report("ERROR", f"{relative} is stored under the wrong area directory", failures, warnings)
        area_readme = path.parents[1] / "README.md"
        expected_area_id = front_matter(area_readme).get("area_id") if area_readme.exists() else ""
        if data.get("area_id") and expected_area_id and data.get("area_id") != expected_area_id:
            report(
                "ERROR",
                f"{issue_id} area_id {data.get('area_id')} does not match {expected_area_id}",
                failures,
                warnings,
            )
        if not re.search(rf"^# {re.escape(issue_id)}\s+—\s+", body, re.MULTILINE):
            report("ERROR", f"{issue_id} title heading does not begin with its identifier", failures, warnings)
        heading_title = markdown_heading_title(path)
        if data.get("title") and heading_title != data.get("title"):
            report(
                "ERROR",
                f"{issue_id} title metadata does not match its H1: {data.get('title')!r} != {heading_title!r}",
                failures,
                warnings,
            )
        sidecar = path.with_name(f"{issue_id}.audit.md")
        if data.get("record_type") == "source-development":
            front_matter_match = FRONT_MATTER_RE.match(read(path))
            front_matter_text = front_matter_match.group(1) if front_matter_match else ""
            if data.get("print_status") != "excluded" or "public-proposal" in front_matter_text:
                report(
                    "ERROR",
                    f"{issue_id} source-development shell must remain explicitly excluded from print",
                    failures,
                    warnings,
                )
            if sidecar.exists():
                report(
                    "ERROR",
                    f"{issue_id} source-development shell must not have an audit sidecar",
                    failures,
                    warnings,
                )
            if "**Source-development record only.**" not in body:
                report(
                    "ERROR",
                    f"{issue_id} source-development shell lacks the required development notice",
                    failures,
                    warnings,
                )
            for heading in ("Scope Under Review", "Source-Development Record", "Next Development Step"):
                if not re.search(rf"^## {re.escape(heading)}$", body, re.MULTILINE):
                    report(
                        "ERROR",
                        f"{issue_id} source-development shell lacks required heading: {heading}",
                        failures,
                        warnings,
                    )
            for heading in (
                "Issue Snapshot",
                "Manifestation of the Failure",
                "Manifestations of the Failure",
                "Proposed Legislation",
                "Budgetary Impact Statement",
                "Proposal Scoring",
                "Annotation",
            ):
                if re.search(rf"^## {re.escape(heading)}$", body, re.MULTILINE):
                    report(
                        "ERROR",
                        f"{issue_id} source-development shell improperly uses mature issue heading: {heading}",
                        failures,
                        warnings,
                    )
            continue
        required_metadata = (
            "area_id",
            "title",
            "status",
            "audit_score",
            "audit_status",
            "audit_last_type",
            "audit_last_date",
            "audit_next",
            "audit_rubric_version",
            "audit_rebaseline_status",
        )
        missing_metadata = [field for field in required_metadata if not data.get(field)]
        if missing_metadata:
            report(
                "ERROR",
                f"{issue_id} lacks required issue metadata: {', '.join(missing_metadata)}",
                failures,
                warnings,
            )
        if data.get("status") and data.get("status") not in VALID_ISSUE_STATUSES:
            report("ERROR", f"{issue_id} has invalid status {data.get('status')!r}", failures, warnings)
        try:
            score = int(data.get("audit_score", ""))
            if not 0 <= score <= 100:
                raise ValueError
        except ValueError:
            report("ERROR", f"{issue_id} has invalid audit_score {data.get('audit_score')!r}", failures, warnings)
        try:
            if data.get("audit_last_date"):
                date.fromisoformat(data["audit_last_date"])
        except ValueError:
            report("ERROR", f"{issue_id} has invalid audit_last_date {data.get('audit_last_date')!r}", failures, warnings)
        rebaseline = data.get("audit_rebaseline_status")
        if rebaseline and rebaseline not in VALID_REBASELINE_STATUSES:
            report("ERROR", f"{issue_id} has invalid audit_rebaseline_status {rebaseline!r}", failures, warnings)
        if data.get("change_audit_needed") not in (None, "true", "false"):
            report(
                "ERROR",
                f"{issue_id} has invalid change_audit_needed {data.get('change_audit_needed')!r}",
                failures,
                warnings,
            )
        for field in ("change_audit_needed", "change_audit_reason"):
            if field not in data:
                report(
                    "ERROR",
                    f"{issue_id} lacks required audit-control metadata: {field}",
                    failures,
                    warnings,
                )
        foundation_status = data.get("foundation_status")
        if foundation_status and foundation_status not in {"approved", "pending"}:
            report(
                "ERROR",
                f"{issue_id} has invalid foundation_status {foundation_status!r}",
                failures,
                warnings,
            )
        if foundation_status == "approved" and not data.get("foundation_approved_date"):
            report(
                "ERROR",
                f"{issue_id} has approved foundations without foundation_approved_date",
                failures,
                warnings,
            )
        if data.get("status") == "in-development" and data.get("audit_score") == "0" and not foundation_status:
            report(
                "WARNING",
                f"{issue_id} is an unscored in-development issue without a machine-readable foundation decision",
                failures,
                warnings,
            )
        if not sidecar.exists():
            report("ERROR", f"{issue_id} lacks sibling audit-history file", failures, warnings)
        elif front_matter(sidecar).get("issue_id") != issue_id:
            report("ERROR", f"{issue_id} audit-history metadata does not match its issue page", failures, warnings)
        declared_sidecar = data.get("audit_history", "").strip('"')
        if declared_sidecar and declared_sidecar != sidecar.name:
            report("ERROR", f"{issue_id} audit_history metadata is {declared_sidecar}, expected {sidecar.name}", failures, warnings)
        vehicles = {
            key: value.strip('"')
            for key, value in data.items()
            if key.endswith("legislative_proposal") or key == "constitutional_proposal"
        }
        for field, vehicle in vehicles.items():
            target = local_target(path, vehicle)
            if target and not target.exists():
                report("ERROR", f"{issue_id} {field} target is missing: {vehicle}", failures, warnings)
        if data.get("status") == "developed":
            if not re.search(r"^> ## Issue Snapshot$", body, re.MULTILINE):
                report("ERROR", f"{issue_id} lacks the required Issue Snapshot block", failures, warnings)
            for heading in REQUIRED_ISSUE_HEADINGS:
                if not re.search(rf"^## {heading}$", body, re.MULTILINE):
                    report("ERROR", f"{issue_id} lacks required heading: {heading}", failures, warnings)
    return known


def check_legislation(issue_map: dict[str, Path], failures: list[str], warnings: list[str]) -> None:
    index = read(LEGISLATION_PATH / "README.md")
    indexed_targets = {
        target.resolve()
        for raw_target in MARKDOWN_LINK_RE.findall(index)
        if (target := local_target(LEGISLATION_PATH / "README.md", raw_target))
    }
    for path in sorted(LEGISLATION_PATH.glob("*.md")):
        if path.name == "README.md":
            continue
        data = front_matter(path)
        front_matter_match = FRONT_MATTER_RE.match(read(path))
        front_matter_text = front_matter_match.group(1) if front_matter_match else ""
        if not re.search(r"^\s+- legislative-appendix$", front_matter_text, re.MULTILINE):
            report(
                "ERROR",
                f"{path.relative_to(ROOT)} lacks legislative-appendix print assignment",
                failures,
                warnings,
            )
        proposal_id = data.get("proposal_id", "")
        if proposal_id != path.stem:
            report(
                "ERROR",
                f"{path.relative_to(ROOT)} proposal_id {proposal_id!r} does not match filename",
                failures,
                warnings,
            )
        issue_id = re.sub(r"-(?:state|amendment|preferred)$", "", proposal_id)
        if not ISSUE_ID_RE.fullmatch(issue_id):
            report("ERROR", f"{path.relative_to(ROOT)} lacks a valid issue_id", failures, warnings)
            continue
        if issue_id not in issue_map:
            report("ERROR", f"{path.relative_to(ROOT)} identifies unknown issue {issue_id}", failures, warnings)
        if data.get("issue_id") != issue_id:
            report(
                "ERROR",
                f"{path.relative_to(ROOT)} issue_id {data.get('issue_id')!r} does not match {issue_id}",
                failures,
                warnings,
            )
        if path.resolve() not in indexed_targets:
            report("ERROR", f"{path.relative_to(ROOT)} is missing from legislation/README.md", failures, warnings)
        framework_issue = data.get("framework_issue", "").strip('"')
        if not framework_issue:
            report("ERROR", f"{path.relative_to(ROOT)} lacks framework_issue metadata", failures, warnings)
        else:
            target = local_target(path, framework_issue)
            if target and not target.exists():
                report("ERROR", f"{path.relative_to(ROOT)} framework_issue target is missing", failures, warnings)
        body = markdown_body(path)
        if len(re.findall(r"^# ", body, re.MULTILINE)) != 1:
            report("ERROR", f"{path.relative_to(ROOT)} must contain exactly one H1", failures, warnings)
        if re.search(r"^## A BILL$", body, re.MULTILINE) and not re.search(
            r"^Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled,$",
            body,
            re.MULTILINE,
        ):
            report(
                "ERROR",
                f"{path.relative_to(ROOT)} is a federal bill draft without the standard enacting clause",
                failures,
                warnings,
            )
        visible_ids = {issue_id, proposal_id}
        expected_h1 = (
            rf"^# (?:{'|'.join(re.escape(value) for value in sorted(visible_ids))})\s+[—-]\s+"
            rf"{re.escape(data.get('title', ''))}(?:\s+\((?:Preferred|Independent Alternative)\))?$"
        )
        if not re.search(expected_h1, body, re.MULTILINE):
            report("ERROR", f"{path.relative_to(ROOT)} title metadata does not match its H1", failures, warnings)
        if not re.search(r"^## Budgetary Impact Statement$", body, re.MULTILINE):
            report("WARNING", f"{path.relative_to(ROOT)} lacks Budgetary Impact Statement", failures, warnings)

    for issue_id, issue_path in issue_map.items():
        data = front_matter(issue_path)
        if data.get("record_type") == "source-development":
            continue
        declared: dict[str, Path] = {}
        for field, raw_value in data.items():
            if not (field.endswith("legislative_proposal") or field == "constitutional_proposal"):
                continue
            target = local_target(issue_path, raw_value.strip('"'))
            if target:
                declared[field] = target
        body_targets = {
            target.resolve()
            for raw_target in MARKDOWN_LINK_RE.findall(markdown_body(issue_path))
            if (target := local_target(issue_path, raw_target))
        }
        for field, target in declared.items():
            if target.exists() and target.resolve() not in body_targets:
                report(
                    "ERROR",
                    f"{issue_id} declares {field} but does not link it in the issue page: {target.relative_to(ROOT)}",
                    failures,
                    warnings,
                )
        preferred = declared.get("legislative_proposal") or declared.get("federal_legislative_proposal")
        if issue_id != "JUD-011" and preferred and preferred.name == "JUD-011.md":
            alternative = declared.get("alternative_legislative_proposal")
            if not alternative or not alternative.exists():
                report(
                    "ERROR",
                    f"{issue_id} uses JUD-011 as its preferred remedy without a valid standalone alternative",
                    failures,
                    warnings,
                )
            if not re.search(r"^## Budgetary Impact Statements$", markdown_body(issue_path), re.MULTILINE):
                report(
                    "ERROR",
                    f"{issue_id} uses JUD-011 as its preferred remedy without separate Budgetary Impact Statements",
                    failures,
                    warnings,
                )


def check_area_indexes(issue_map: dict[str, Path], failures: list[str], warnings: list[str]) -> None:
    for issue_id, page in issue_map.items():
        area_readme = page.parents[1] / "README.md"
        if not area_readme.exists():
            report("ERROR", f"{issue_id} has no area README", failures, warnings)
            continue
        if not re.search(rf"\b{re.escape(issue_id)}\b", read(area_readme)):
            report("ERROR", f"{issue_id} is absent from {area_readme.relative_to(ROOT)}", failures, warnings)

    for area_readme in sorted(ROOT.glob("areas/*/README.md")):
        body = markdown_body(area_readme)
        headings = re.findall(r"^## (.+)$", body, re.MULTILINE)
        for heading in ("Generalized Institutional Concern", "Active Issues", "Issue Boundaries", "Notes"):
            if headings.count(heading) != 1:
                report("ERROR", f"{area_readme.relative_to(ROOT)} must contain one {heading!r} heading", failures, warnings)
        if all(heading in headings for heading in ("Generalized Institutional Concern", "Active Issues", "Issue Boundaries", "Notes")):
            order = [headings.index(heading) for heading in ("Generalized Institutional Concern", "Active Issues", "Issue Boundaries", "Notes")]
            if order != sorted(order):
                report("ERROR", f"{area_readme.relative_to(ROOT)} has out-of-order standard headings", failures, warnings)
        active_match = re.search(r"^## Active Issues\s*$([\s\S]*?)(?=^## |\Z)", body, re.MULTILINE)
        active = active_match.group(1) if active_match else ""
        active_entries = re.findall(
            r"^- \[\*\*([A-Z]+-\d{3}) — ([^*]+)\*\*\]\(([^)]+)\)\s*$",
            active,
            re.MULTILINE,
        )
        plain_active_entries = re.findall(
            r"^- \*\*([A-Z]+-\d{3}) — ([^*]+)\*\*\s*$",
            active,
            re.MULTILINE,
        )
        active_ids = {entry[0] for entry in active_entries} | {
            entry[0] for entry in plain_active_entries
        }
        all_active_ids = set(re.findall(r"\b[A-Z]+-\d{3}\b", active))
        malformed = sorted(all_active_ids - active_ids)
        if malformed:
            report(
                "ERROR",
                f"{area_readme.relative_to(ROOT)} has nonstandard Active Issues entries: {', '.join(malformed)}",
                failures,
                warnings,
            )
        raw_count = front_matter(area_readme).get("issue_count", "")
        try:
            declared_count = int(raw_count)
        except ValueError:
            declared_count = -1
        if declared_count != len(active_ids):
            report(
                "ERROR",
                f"{area_readme.relative_to(ROOT)} issue_count is {raw_count!r}; Active Issues contains {len(active_ids)} record(s)",
                failures,
                warnings,
            )
        for issue_id, title, raw_target in active_entries:
            target = local_target(area_readme, raw_target)
            if not target or not target.exists():
                continue
            target_data = front_matter(target)
            if target.stem != issue_id:
                report(
                    "ERROR",
                    f"{area_readme.relative_to(ROOT)} routes {issue_id} to {target.relative_to(ROOT)}",
                    failures,
                    warnings,
                )
            if target_data.get("title") and title.strip() != target_data.get("title"):
                report(
                    "ERROR",
                    f"{area_readme.relative_to(ROOT)} title for {issue_id} does not match its issue page",
                    failures,
                    warnings,
                )
        area = area_readme.parent.name
        for issue_id, page in issue_map.items():
            if page.parents[1].name != area:
                continue
            status = front_matter(page).get("status")
            if status == "retired":
                former_match = re.search(r"^## Former Developed Proposals\s*$([\s\S]*?)(?=^## |\Z)", body, re.MULTILINE)
                former = former_match.group(1) if former_match else ""
                if not re.search(rf"\b{re.escape(issue_id)}\b", former):
                    report(
                        "ERROR",
                        f"{issue_id} is retired but is not listed under Former Developed Proposals",
                        failures,
                        warnings,
                    )
            elif issue_id not in active_ids:
                report(
                    "ERROR",
                    f"{issue_id} is an active issue page but is not in the area's Active Issues section",
                    failures,
                    warnings,
                )


def check_issue_layout(issue_map: dict[str, Path], failures: list[str], warnings: list[str]) -> None:
    for issue_id, path in issue_map.items():
        body = markdown_body(path)
        manifest = re.search(r"^## Manifestation(?:s)? of the Failure$", body, re.MULTILINE)
        support = re.search(r"^### Supporting Record and Updates$", body, re.MULTILINE)
        if support and not manifest:
            report("ERROR", f"{issue_id} has a supporting-record subsection without Manifestations", failures, warnings)
        if support and manifest:
            following = re.search(r"^## ", body[manifest.end():], re.MULTILINE)
            end = len(body) if not following else manifest.end() + following.start()
            if not manifest.end() <= support.start() < end:
                report("ERROR", f"{issue_id} supporting-record subsection is not at the end of Manifestations", failures, warnings)
        if re.search(r"^## (?:Watching for Updates|Additional Supporting Record)$", body, re.MULTILINE):
            report("ERROR", f"{issue_id} retains a legacy top-level monitoring/evidence heading", failures, warnings)


def check_topic_pages(failures: list[str], warnings: list[str]) -> None:
    required = ("Overview", "Applicable Proposals", "What ARRP Does and Does Not Address")
    map_wrapper = '<div class="arrp-topic-table arrp-topic-table--map" markdown>'
    map_header = "| Public concern | Proposal | How ARRP addresses it |"
    related_wrapper = '<div class="arrp-topic-table arrp-topic-table--related" markdown>'
    related_header = "| Idea | Record | Why it is not included |"
    for path in sorted((ROOT / "topics").glob("*.md")):
        if path.name == "README.md":
            continue
        body = markdown_body(path)
        relative = path.relative_to(ROOT)
        if not re.search(r"^# .+ \{\.arrp-topic-guide-title\}$", body, re.MULTILINE):
            report("ERROR", f"{relative} lacks the standard topic-guide title class", failures, warnings)
        for heading in required:
            if not re.search(rf"^## {re.escape(heading)}$", body, re.MULTILINE):
                report("ERROR", f"{relative} lacks topic-page heading: {heading}", failures, warnings)
        for legacy_heading in ("Relevant Proposals", "How Concerns Map to Proposals"):
            if re.search(rf"^## {re.escape(legacy_heading)}$", body, re.MULTILINE):
                report("ERROR", f"{relative} retains legacy topic-page heading: {legacy_heading}", failures, warnings)
        prohibited_headings = (
            "Budgetary Impact Statement",
            "Budgetary Impact Statements",
            "Proposal Scoring",
            "Proposed Legislation",
            "Proposed Constitutional Amendment",
            "Next Action",
            "Next Steps",
            "Audit History",
        )
        for heading in prohibited_headings:
            if re.search(rf"^## {re.escape(heading)}$", body, re.MULTILINE):
                report(
                    "ERROR",
                    f"{relative} contains methodology-prohibited topic-page section: {heading}",
                    failures,
                    warnings,
                )
        prohibited_phrases = (
            "Authoritative ARRP route",
            "Reader concern",
            "Project lifecycle",
            "Development priority",
        )
        for phrase in prohibited_phrases:
            if phrase.casefold() in body.casefold():
                report(
                    "ERROR",
                    f"{relative} contains methodology-prohibited topic-page terminology: {phrase}",
                    failures,
                    warnings,
                )

        applicable = body.split("## Applicable Proposals", 1)[-1].split("\n## ", 1)[0]
        if map_wrapper not in applicable or map_header not in applicable or "</div>" not in applicable:
            report("ERROR", f"{relative} lacks the standard Applicable Proposals table", failures, warnings)
        else:
            table_rows = [line for line in applicable.splitlines() if line.startswith("|")]
            if len(table_rows) < 3:
                report("ERROR", f"{relative} has no Applicable Proposals data row", failures, warnings)
            for row in table_rows[2:]:
                cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
                if len(cells) != 3:
                    continue
                proposal_ids = set(re.findall(r"\b[A-Z]+-\d{3}\b", cells[1]))
                pending = cells[1] == "Pending"
                if (len(proposal_ids) != 1 or pending) and not (pending and not proposal_ids):
                    report(
                        "ERROR",
                        f"{relative} Applicable Proposals row must identify exactly one proposal or Pending: {cells[0]}",
                        failures,
                        warnings,
                    )
        if re.search(r"\]\(\.\./areas/[^)]+/README\.md\)", applicable):
            report("ERROR", f"{relative} routes an Applicable Proposals row through an area page", failures, warnings)

        if re.search(r"^## Related Ideas Not Included$", body, re.MULTILINE):
            related = body.split("## Related Ideas Not Included", 1)[-1].split("\n## ", 1)[0]
            if related_wrapper not in related or related_header not in related or "</div>" not in related:
                report("ERROR", f"{relative} lacks the standard Related Ideas table", failures, warnings)
            else:
                related_rows = [line for line in related.splitlines() if line.startswith("|")]
                if len(related_rows) < 3:
                    report("ERROR", f"{relative} has no Related Ideas data row", failures, warnings)
        if body.count('<div class="arrp-topic-table') != body.count("</div>"):
            report("ERROR", f"{relative} has unbalanced topic-table wrappers", failures, warnings)


def reader_pages() -> list[Path]:
    pages = [ROOT / "README.md", ROOT / "SUBJECT_INDEX.md"]
    pages.extend(ROOT.glob("areas/*/README.md"))
    pages.extend(issue_pages())
    pages.extend(LEGISLATION_PATH.glob("*.md"))
    pages.extend((ROOT / "topics").glob("*.md"))
    return sorted(set(pages))


def framework_pages() -> list[Path]:
    """Return technical framework pages used by source-citation checks."""
    return sorted(
        path
        for path in (ROOT / "framework").rglob("*.md")
        if "templates" not in path.parts
    )


def check_markdown_links(failures: list[str], warnings: list[str]) -> None:
    """Validate relative links and images in every active project Markdown file."""
    for path in active_project_files(".md"):
        body = MARKDOWN_FENCE_RE.sub("", read(path))
        for raw_target in MARKDOWN_LINK_RE.findall(body):
            target = local_target(path, raw_target)
            if target and not target.exists():
                report("ERROR", f"broken local link in {path.relative_to(ROOT)}: {raw_target}", failures, warnings)
            link_text = raw_target.strip().strip("<>").split(" ", 1)[0]
            if link_text.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            fragment = link_text.split("#", 1)[1] if "#" in link_text else ""
            fragment_target = target or path
            check_markdown_fragment(
                fragment_target,
                fragment,
                str(path.relative_to(ROOT)),
                failures,
                warnings,
            )


def check_html_links(failures: list[str], warnings: list[str]) -> None:
    """Validate static relative href and src targets in active project HTML."""
    for path in active_project_files(".html"):
        for _, raw_target in HTML_LINK_RE.findall(read(path)):
            if "{{" in raw_target or "{%" in raw_target:
                continue
            target = local_target(path, raw_target)
            if target and not target.exists():
                report("ERROR", f"broken local link in {path.relative_to(ROOT)}: {raw_target}", failures, warnings)


def check_orphaned_markdown_pages(failures: list[str], warnings: list[str]) -> None:
    """Report active Markdown pages with no inbound project link."""
    pages = active_project_files(".md")
    page_set = {path.resolve() for path in pages}
    incoming: dict[Path, int] = {path.resolve(): 0 for path in pages}
    for source in pages:
        body = MARKDOWN_FENCE_RE.sub("", read(source))
        for raw_target in MARKDOWN_LINK_RE.findall(body):
            target = local_target(source, raw_target)
            if target and target.resolve() in incoming:
                incoming[target.resolve()] += 1
    for source in active_project_files(".html"):
        for _, raw_target in HTML_LINK_RE.findall(read(source)):
            target = local_target(source, raw_target)
            if target and target.resolve() in incoming:
                incoming[target.resolve()] += 1
    for source in active_project_files(*REPOSITORY_LINK_TEXT_SUFFIXES):
        for _, _, target in github_repository_targets(read(source)):
            if target.resolve() in incoming:
                incoming[target.resolve()] += 1

    entry_points = {
        (ROOT / "README.md").resolve(),
        (ROOT / "AGENTS.md").resolve(),
        (ROOT / "website" / "404.md").resolve(),
    }
    for path in pages:
        resolved = path.resolve()
        if resolved in entry_points or resolved not in page_set:
            continue
        if incoming[resolved] == 0:
            report(
                "WARNING",
                f"orphaned Markdown page has no inbound project link: {path.relative_to(ROOT)}",
                failures,
                warnings,
            )


def check_markdown_metadata_and_headings(
    failures: list[str], warnings: list[str]
) -> None:
    """Check universal page metadata and objectively testable heading hierarchy."""
    metadata_exceptions = {ROOT / "AGENTS.md", ROOT / "website" / "404.md"}
    for path in active_project_files(".md"):
        relative = path.relative_to(ROOT)
        if path not in metadata_exceptions and not front_matter(path).get("title"):
            report(
                "ERROR",
                f"{relative} lacks required title metadata",
                failures,
                warnings,
            )
        body = MARKDOWN_FENCE_RE.sub("", markdown_body(path))
        headings = [
            (len(match.group(1)), match.group(2).strip(), body.count("\n", 0, match.start()) + 1)
            for match in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", body, re.MULTILINE)
        ]
        if not headings:
            report("ERROR", f"{relative} has no Markdown heading", failures, warnings)
            continue
        if headings[0][0] != 1:
            report(
                "ERROR",
                f"{relative} begins with heading level {headings[0][0]} instead of H1",
                failures,
                warnings,
            )
        if relative.parts[0] != "legislation":
            h1_count = sum(level == 1 for level, _, _ in headings)
            if h1_count != 1:
                report(
                    "ERROR",
                    f"{relative} contains {h1_count} H1 headings; non-legislation pages require exactly one",
                    failures,
                    warnings,
                )
        previous_level = headings[0][0]
        for level, title, line_number in headings[1:]:
            if level > previous_level + 1:
                report(
                    "ERROR",
                    f"{relative} skips heading level {previous_level} to {level} at line {line_number}: {title}",
                    failures,
                    warnings,
                )
            previous_level = level


def check_reader_navigation_coverage(
    issue_map: dict[str, Path], failures: list[str], warnings: list[str]
) -> None:
    """Check deterministic issue coverage in the subject index and topic guides."""
    subject_index = read(ROOT / "SUBJECT_INDEX.md")
    topic_corpus = "\n".join(read(path) for path in sorted((ROOT / "topics").glob("*.md")))
    for issue_id, path in issue_map.items():
        metadata = front_matter(path)
        if metadata.get("record_type") == "source-development":
            continue
        if metadata.get("status") != "retired" and not re.search(
            rf"\b{re.escape(issue_id)}\b", subject_index
        ):
            report(
                "ERROR",
                f"{issue_id} is missing from SUBJECT_INDEX.md",
                failures,
                warnings,
            )
        coverage = metadata.get("topic_coverage", "")
        coverage_reason = metadata.get("topic_coverage_reason", "")
        if coverage and coverage != "institution-specific":
            report(
                "ERROR",
                f"{issue_id} has invalid topic_coverage {coverage!r}",
                failures,
                warnings,
            )
        if coverage == "institution-specific" and not coverage_reason:
            report(
                "ERROR",
                f"{issue_id} uses institution-specific topic coverage without topic_coverage_reason",
                failures,
                warnings,
            )
        if (
            metadata.get("status") == "developed"
            and coverage != "institution-specific"
            and not re.search(rf"\b{re.escape(issue_id)}\b", topic_corpus)
        ):
            report(
                "WARNING",
                f"{issue_id} is a developed issue missing from every topic guide",
                failures,
                warnings,
            )


def check_cross_issue_links(
    issue_map: dict[str, Path], failures: list[str], warnings: list[str]
) -> None:
    """Require at least one link when a reader page names another existing issue."""
    link_pattern = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
    pages = sorted([*ROOT.glob("areas/*/README.md"), *issue_pages()])
    for path in pages:
        body = MARKDOWN_FENCE_RE.sub("", markdown_body(path))
        own_id = front_matter(path).get("issue_id", "")
        linked_ids: set[str] = set()
        for label, target in link_pattern.findall(body):
            linked_ids.update(re.findall(r"\b[A-Z]+-\d{3}\b", label))
            linked_ids.update(re.findall(r"\b[A-Z]+-\d{3}\b", target))
            local = local_target(path, target)
            if local and local.stem in issue_map:
                linked_ids.add(local.stem)
        unlinked_text = link_pattern.sub("", body)
        unlinked_text = re.sub(r"`[^`]*`", "", unlinked_text)
        mentions = {
            value
            for value in re.findall(r"\b[A-Z]+-\d{3}\b", unlinked_text)
            if value in issue_map and value != own_id
        }
        for issue_id in sorted(mentions - linked_ids):
            report(
                "ERROR",
                f"reader-facing {path.relative_to(ROOT)} names {issue_id} without linking its existing issue page",
                failures,
                warnings,
            )

def github_repository_targets(body: str) -> list[tuple[str, str, Path]]:
    """Return main-branch ARRP repository targets embedded in an issue body."""
    targets: list[tuple[str, str, Path]] = []
    for match in GITHUB_REPOSITORY_URL_RE.finditer(body):
        ref = unquote(match.group("ref"))
        if ref != "main":
            continue
        raw_url = match.group(0)
        target_text = unquote(urlsplit(raw_url).path)
        if target_text.startswith("/Thorncrag/ARRP/"):
            target_text = re.sub(
                r"^/Thorncrag/ARRP/(?:blob|tree)/main/",
                "",
                target_text,
            )
        elif target_text.startswith("/Thorncrag/ARRP/main/"):
            target_text = target_text.removeprefix("/Thorncrag/ARRP/main/")
        else:
            continue
        targets.append((raw_url, target_text, (ROOT / target_text).resolve()))
    return targets


def check_embedded_repository_links(failures: list[str], warnings: list[str]) -> None:
    """Validate main-branch ARRP repository URLs stored anywhere in the active tree."""
    for path in active_project_files(*REPOSITORY_LINK_TEXT_SUFFIXES):
        for raw_url, target_text, target in github_repository_targets(read(path)):
            if not target.exists():
                report(
                    "ERROR",
                    f"broken repository link in {path.relative_to(ROOT)}: {raw_url} (missing {target_text})",
                    failures,
                    warnings,
                )
            fragment = urlsplit(raw_url.replace("\\/", "/")).fragment
            check_markdown_fragment(
                target,
                fragment,
                str(path.relative_to(ROOT)),
                failures,
                warnings,
            )


def run_gh_json(command: list[str]) -> tuple[object | None, str]:
    """Run a read-only gh command and return parsed JSON plus a concise failure."""
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None, "the gh CLI is unavailable"
    if completed.returncode:
        detail = completed.stderr.strip().splitlines()
        return None, detail[-1] if detail else "the GitHub query failed"
    try:
        return json.loads(completed.stdout), ""
    except json.JSONDecodeError as error:
        return None, f"GitHub returned invalid JSON: {error}"


def fetch_github_issues(failures: list[str], warnings: list[str]) -> list[dict[str, object]] | None:
    command = [
        "gh",
        "issue",
        "list",
        "--repo",
        GITHUB_REPOSITORY,
        "--state",
        "all",
        "--limit",
        "1000",
        "--json",
        "number,title,body,url,state,labels",
    ]
    payload, error = run_gh_json(command)
    if payload is None:
        report(
            "WARNING",
            "GitHub issue synchronization check skipped; rerun in the authenticated host context: " + error,
            failures,
            warnings,
        )
        return None
    return list(payload) if isinstance(payload, list) else []


def fetch_github_project_items(failures: list[str], warnings: list[str]) -> list[dict[str, object]] | None:
    """Read the user-owned Project directly, avoiding gh owner-type discovery in Actions."""
    query = """
query($owner:String!,$number:Int!,$after:String){
  user(login:$owner){
    projectV2(number:$number){
      items(first:100,after:$after){
        pageInfo{hasNextPage endCursor}
        nodes{
          id
          content{... on Issue{number title url}}
          fieldValues(first:50){
            nodes{
              ... on ProjectV2ItemFieldTextValue{text field{... on ProjectV2Field{name}}}
              ... on ProjectV2ItemFieldNumberValue{number field{... on ProjectV2Field{name}}}
              ... on ProjectV2ItemFieldSingleSelectValue{name field{... on ProjectV2SingleSelectField{name}}}
            }
          }
        }
      }
    }
  }
}
""".strip()
    after = ""
    items: list[dict[str, object]] = []
    while True:
        command = [
            "gh",
            "api",
            "graphql",
            "-F",
            f"owner={GITHUB_PROJECT_OWNER}",
            "-F",
            f"number={GITHUB_PROJECT_NUMBER}",
            "-f",
            f"query={query}",
        ]
        if after:
            command.extend(["-F", f"after={after}"])
        payload, error = run_gh_json(command)
        if payload is None:
            report(
                "WARNING",
                "GitHub Project synchronization check skipped; rerun in the authenticated host context: " + error,
                failures,
                warnings,
            )
            return None
        try:
            page = payload["data"]["user"]["projectV2"]["items"]
        except (KeyError, TypeError):
            report(
                "WARNING",
                "GitHub Project synchronization check skipped; the Project GraphQL response was incomplete",
                failures,
                warnings,
            )
            return None
        for node in page.get("nodes") or []:
            item: dict[str, object] = {
                "id": node.get("id"),
                "content": node.get("content") or {},
            }
            for value in (node.get("fieldValues") or {}).get("nodes") or []:
                field = value.get("field") or {}
                field_name = str(field.get("name") or "").casefold()
                if not field_name:
                    continue
                if "text" in value:
                    item[field_name] = value.get("text")
                elif "number" in value:
                    item[field_name] = value.get("number")
                elif "name" in value:
                    item[field_name] = value.get("name")
            items.append(item)
        page_info = page.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        after = str(page_info.get("endCursor") or "")
        if not after:
            report(
                "WARNING",
                "GitHub Project synchronization check stopped at an invalid pagination cursor",
                failures,
                warnings,
            )
            return None
    return items


def check_github_issue_links(
    issues: list[dict[str, object]] | None,
    failures: list[str],
    warnings: list[str],
) -> str:
    """Validate issue-body repository links and return bodies for source reconciliation."""
    if issues is None:
        return ""
    for issue in issues:
        for raw_url, target_text, target in github_repository_targets(issue.get("body") or ""):
            if not target.exists():
                report(
                    "ERROR",
                    f"broken repository link in GitHub issue #{issue.get('number')}: {raw_url} "
                    f"(missing {target_text})",
                    failures,
                    warnings,
                )
            fragment = urlsplit(raw_url.replace("\\/", "/")).fragment
            check_markdown_fragment(
                target,
                fragment,
                f"GitHub issue #{issue.get('number')}",
                failures,
                warnings,
            )
    return "\n".join(str(issue.get("body") or "") for issue in issues)


def expected_project_development_level(metadata: dict[str, str]) -> set[str]:
    """Return unambiguous Project maturity values implied by canonical issue metadata."""
    status = metadata.get("status", "")
    try:
        score = int(metadata.get("audit_score", "0"))
    except ValueError:
        score = 0
    if status == "developed" and score >= 75:
        return READY_PROJECT_DEVELOPMENT_LEVELS
    if status == "developed" and 1 <= score <= 74:
        return {"developed proposal"}
    return set()


def expected_project_workflow_status(metadata: dict[str, str]) -> set[str]:
    """Return workflow states that are unambiguously implied by canonical metadata."""
    status = metadata.get("status", "")
    return {
        "awaiting-merits-adjudication": {"deferred / parked", "blocked"},
        "deferred": {"deferred / parked"},
    }.get(status, set())


def check_github_synchrony(
    issue_map: dict[str, Path],
    issues: list[dict[str, object]] | None,
    project_items: list[dict[str, object]] | None,
    failures: list[str],
    warnings: list[str],
) -> None:
    """Compare registry, GitHub Issue, Project, and canonical issue metadata."""
    with REGISTRY_PATH.open(newline="", encoding="utf-8") as handle:
        registry = list(csv.DictReader(handle))
    issues_by_number = {
        int(issue["number"]): issue
        for issue in issues or []
        if str(issue.get("number", "")).isdigit()
    }
    project_by_number: dict[int, dict[str, object]] = {}
    for item in project_items or []:
        content = item.get("content") or {}
        if isinstance(content, dict) and str(content.get("number", "")).isdigit():
            project_by_number[int(content["number"])] = item

    for row in registry:
        number_text = row.get("GitHub Number", "").strip()
        if not number_text.isdigit():
            continue
        number = int(number_text)
        expected_issue_url = f"https://github.com/{GITHUB_REPOSITORY}/issues/{number}"
        if row.get("GitHub Issue", "").strip() != expected_issue_url:
            report("ERROR", f"registry issue #{number} has a noncanonical GitHub Issue URL", failures, warnings)
        issue = issues_by_number.get(number)
        if issues is not None and not issue:
            report("ERROR", f"registry issue #{number} does not exist on GitHub", failures, warnings)
            continue
        if issue:
            live_title = str(issue.get("title") or "")
            if live_title != row.get("GitHub Title", ""):
                report(
                    "ERROR",
                    f"registry title for GitHub issue #{number} differs from GitHub: {row.get('GitHub Title')!r} != {live_title!r}",
                    failures,
                    warnings,
                )
            if str(issue.get("url") or "") != expected_issue_url:
                report("ERROR", f"GitHub issue #{number} returned a noncanonical URL", failures, warnings)

        kind = row.get("Kind", "").strip()
        active_kind = kind in {"proposal", "horizon"}
        object_id = row.get("Object ID", "").strip()
        canonical = row.get("Canonical Record", "").strip()
        canonical_url = GITHUB_BLOB_PREFIX + canonical if canonical else ""
        metadata: dict[str, str] = {}
        if object_id in issue_map:
            page = issue_map[object_id]
            metadata = front_matter(page)
            expected_record = page.relative_to(ROOT).as_posix()
            if canonical != expected_record:
                report(
                    "ERROR",
                    f"registry canonical record for {object_id} is {canonical!r}; expected {expected_record}",
                    failures,
                    warnings,
                )
            expected_title = f"{object_id}: {metadata.get('title', '')}"
            if kind == "proposal" and row.get("GitHub Title") != expected_title:
                report(
                    "ERROR",
                    f"registry title for {object_id} does not match canonical issue metadata",
                    failures,
                    warnings,
                )

        if issue and active_kind:
            labels = {
                str(label.get("name") if isinstance(label, dict) else label)
                for label in issue.get("labels") or []
            }
            required_label = f"kind: {kind}"
            if required_label not in labels:
                report("ERROR", f"GitHub issue #{number} lacks required label {required_label!r}", failures, warnings)
            if str(issue.get("state") or "").upper() != "OPEN":
                report("ERROR", f"active {kind} GitHub issue #{number} is not open", failures, warnings)
            body = str(issue.get("body") or "")
            if kind == "proposal" and canonical_url and canonical_url not in body:
                report(
                    "ERROR",
                    f"GitHub issue #{number} does not link its canonical record {canonical}",
                    failures,
                    warnings,
                )
            if object_id and object_id not in body:
                report("ERROR", f"GitHub issue #{number} body does not identify Object ID {object_id}", failures, warnings)

        if not active_kind:
            continue
        project_item = project_by_number.get(number)
        if project_items is not None and not project_item:
            report("ERROR", f"active {kind} GitHub issue #{number} is absent from Project {GITHUB_PROJECT_NUMBER}", failures, warnings)
            continue
        if not project_item:
            continue
        project_content = project_item.get("content") or {}
        project_title = str(
            project_content.get("title") if isinstance(project_content, dict) else ""
        )
        if project_title != row.get("GitHub Title", ""):
            report("ERROR", f"Project title for issue #{number} differs from the registry", failures, warnings)
        project_canonical = str(project_item.get("canonical page") or "")
        allowed_canonical_pages = {canonical_url} if canonical_url else set()
        if kind == "horizon":
            allowed_canonical_pages.add(expected_issue_url)
        if allowed_canonical_pages and project_canonical not in allowed_canonical_pages:
            report(
                "ERROR",
                f"Project canonical page for issue #{number} is {project_canonical!r}; expected one of {', '.join(sorted(allowed_canonical_pages))}",
                failures,
                warnings,
            )
        if kind == "proposal" and object_id and "-" in object_id:
            project_area = str(project_item.get("area") or "")
            expected_area = object_id.split("-", 1)[0]
            if project_area != expected_area:
                report(
                    "ERROR",
                    f"Project Area for {object_id} is {project_area!r}; expected {expected_area}",
                    failures,
                    warnings,
                )
        project_level = normalized_text(project_item.get("development level"))
        if not project_level:
            report(
                "ERROR",
                f"active {kind} {object_id or '#' + number_text} lacks a Project Development level",
                failures,
                warnings,
            )
        elif project_level not in PROJECT_DEVELOPMENT_LEVELS:
            report(
                "ERROR",
                f"active {kind} {object_id or '#' + number_text} has unknown Project Development level {project_item.get('development level')!r}",
                failures,
                warnings,
            )
        elif kind == "horizon" and project_level != "candidate":
            report(
                "ERROR",
                f"active horizon {object_id or '#' + number_text} has Development level {project_item.get('development level')!r}; expected 'Candidate'",
                failures,
                warnings,
            )
        elif kind == "proposal" and project_level == "candidate":
            report(
                "ERROR",
                f"active proposal {object_id or '#' + number_text} cannot use Development level 'Candidate'",
                failures,
                warnings,
            )
        if not metadata or metadata.get("record_type") == "source-development":
            continue
        if metadata.get("audit_score"):
            try:
                project_score = int(float(str(project_item.get("score"))))
                repository_score = int(metadata["audit_score"])
            except (TypeError, ValueError):
                project_score = -1
                repository_score = int(metadata["audit_score"])
            if project_score != repository_score:
                report(
                    "ERROR",
                    f"Project Score for {object_id} is {project_item.get('score')!r}; repository audit_score is {repository_score}",
                    failures,
                    warnings,
                )
        allowed_levels = expected_project_development_level(metadata)
        project_level = normalized_text(project_item.get("development level"))
        if allowed_levels and project_level not in allowed_levels:
            report(
                "ERROR",
                f"Project Development level for {object_id} is {project_item.get('development level')!r}; repository metadata implies {', '.join(sorted(allowed_levels))}",
                failures,
                warnings,
            )
        allowed_statuses = expected_project_workflow_status(metadata)
        project_status = normalized_text(project_item.get("status"))
        if allowed_statuses and project_status not in allowed_statuses:
            report(
                "ERROR",
                f"Project Status for {object_id} is {project_item.get('status')!r}; repository metadata implies {', '.join(sorted(allowed_statuses))}",
                failures,
                warnings,
            )
        expected_last = f"{metadata.get('audit_last_type', '')} ({metadata.get('audit_last_date', '')})"
        if normalized_text(project_item.get("last audit")) != normalized_text(expected_last):
            report(
                "ERROR",
                f"Project Last audit for {object_id} differs from repository audit metadata",
                failures,
                warnings,
            )
        if normalized_text(project_item.get("next audit")) != normalized_text(metadata.get("audit_next")):
            report(
                "ERROR",
                f"Project Next audit for {object_id} differs from repository audit_next",
                failures,
                warnings,
            )
        rebaseline = metadata.get("audit_rebaseline_status")
        expected_rebaseline = PROJECT_REBASELINE_VALUES.get(rebaseline, "")
        if expected_rebaseline and normalized_text(project_item.get("rebaseline status")) != normalized_text(expected_rebaseline):
            report(
                "ERROR",
                f"Project Rebaseline status for {object_id} differs from repository metadata",
                failures,
                warnings,
            )
        change_needed = metadata.get("change_audit_needed")
        if change_needed in {"true", "false"}:
            expected_change = "Yes" if change_needed == "true" else "No"
            if normalized_text(project_item.get("change audit needed")) != normalized_text(expected_change):
                report(
                    "ERROR",
                    f"Project Change audit needed for {object_id} differs from repository metadata",
                    failures,
                    warnings,
                )


def check_github_pages_deployment(failures: list[str], warnings: list[str]) -> None:
    """Verify that the successful Pages deployment tracks canonical main after a grace period."""
    deployments, error = run_gh_json(
        [
            "gh",
            "api",
            f"repos/{GITHUB_REPOSITORY}/deployments?environment=github-pages&per_page=1",
        ]
    )
    if deployments is None:
        report(
            "WARNING",
            "GitHub Pages synchronization check skipped; rerun in the authenticated host context: " + error,
            failures,
            warnings,
        )
        return
    if not isinstance(deployments, list) or not deployments:
        report("ERROR", "GitHub Pages has no recorded deployment", failures, warnings)
        return
    deployment = deployments[0]
    deployment_id = deployment.get("id")
    deployed_sha = str(deployment.get("sha") or "")
    statuses, status_error = run_gh_json(
        ["gh", "api", f"repos/{GITHUB_REPOSITORY}/deployments/{deployment_id}/statuses?per_page=1"]
    )
    if statuses is None:
        report(
            "WARNING",
            "GitHub Pages deployment-status check skipped: " + status_error,
            failures,
            warnings,
        )
    elif not statuses or str(statuses[0].get("state") or "") != "success":
        state = statuses[0].get("state") if statuses else "missing"
        report("ERROR", f"latest GitHub Pages deployment is not successful: {state}", failures, warnings)

    current_sha = git_revision()
    if not current_sha or not deployed_sha or deployed_sha == current_sha:
        return
    try:
        committed_at = int(
            subprocess.run(
                ["git", "show", "-s", "--format=%ct", current_sha],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (subprocess.CalledProcessError, ValueError):
        committed_at = 0
    age_seconds = int(datetime.now(timezone.utc).timestamp()) - committed_at if committed_at else 999999
    if age_seconds <= 1800:
        return
    report(
        "ERROR",
        f"GitHub Pages deployment is stale: deployed {deployed_sha[:12]}, canonical main is {current_sha[:12]}",
        failures,
        warnings,
    )


def source_citation_corpus(github_issue_bodies: str = "") -> str:
    """Return maintained prose and structured records in which a source may be cited."""
    paths = [ROOT / "README.md", ROOT / "SUBJECT_INDEX.md"]
    paths.extend((ROOT / "areas").rglob("*.md"))
    paths.extend(LEGISLATION_PATH.glob("*.md"))
    paths.extend((ROOT / "topics").glob("*.md"))
    paths.extend(research_files(".md", ".csv"))
    paths.extend(framework_pages())
    corpus = "\n".join(read(path) for path in sorted(set(paths)) if path.exists())
    return corpus + ("\n" + github_issue_bodies if github_issue_bodies else "")


def check_research_placement(failures: list[str], warnings: list[str]) -> None:
    """Keep single-area research beside its owning issue while allowing cross-project work centrally."""
    for path in research_files(".md", ".csv", ".svg"):
        relative = path.relative_to(ROOT)
        issue_match = re.match(r"^([A-Z]+-\d{3})(?:-|\.)", path.name)
        if not issue_match:
            continue
        issue_id = issue_match.group(1)
        area = issue_id.split("-", 1)[0]
        if area == "HOR" and path.parent == ROOT / "research" / "horizon-source-records":
            continue
        expected_parent = ROOT / "areas" / area / "research"
        if path.parent != expected_parent:
            report(
                "ERROR",
                f"issue-specific research {relative} should be under areas/{area}/research/",
                failures,
                warnings,
            )


def structured_source_citation_ids(failures: list[str], warnings: list[str]) -> set[str]:
    """Return citations from accountable structured records with real assertions."""
    cited: set[str] = set()
    for path, required_fields in AUTHORITATIVE_SOURCE_RECORDS:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for row_number, row in enumerate(rows, start=2):
            missing = [field for field in required_fields if not row.get(field, "").strip()]
            source_ids = [
                value.strip()
                for value in row.get("source_record_ids", "").split(";")
                if value.strip()
            ]
            malformed = [value for value in source_ids if not re.fullmatch(r"SRC-\d{4}", value)]
            if missing:
                report(
                    "ERROR",
                    f"incomplete structured source citation in {path.relative_to(ROOT)}:{row_number}; missing "
                    + ", ".join(missing),
                    failures,
                    warnings,
                )
            if not source_ids:
                report(
                    "ERROR",
                    f"structured source citation has no source IDs in {path.relative_to(ROOT)}:{row_number}",
                    failures,
                    warnings,
                )
            if malformed:
                report(
                    "ERROR",
                    f"malformed structured source citation in {path.relative_to(ROOT)}:{row_number}: "
                    + ", ".join(malformed),
                    failures,
                    warnings,
                )
            if path == PRELIMINARY_CANDIDATE_PATH:
                source_links = [
                    value.strip()
                    for value in row.get("source_links", "").split("||")
                    if value.strip()
                ]
                if len(source_links) != len(source_ids):
                    report(
                        "ERROR",
                        f"preliminary-candidate source ID/link mismatch in {path.relative_to(ROOT)}:{row_number}",
                        failures,
                        warnings,
                    )
            if not missing and source_ids and not malformed:
                cited.update(source_ids)
    return cited


def normalized_citation_url(url: str) -> str:
    return url.strip().replace("&amp;", "&").split("#", 1)[0].split("?", 1)[0].rstrip("/")


def normalized_source_url(url: str) -> str:
    """Normalize bibliographic identity while preserving document-selecting queries."""
    clean = url.strip().replace("&amp;", "&").split("#", 1)[0].rstrip("/")
    parsed = urlsplit(clean)
    host = (parsed.hostname or "").lower()
    query = parse_qs(parsed.query)
    if host == "scholar.google.com" and parsed.path == "/scholar_case" and query.get("case"):
        return f"https://scholar.google.com/scholar_case?case={query['case'][0]}"
    if host == "www.supremecourt.gov" and parsed.path.lower() == "/search.aspx" and query.get("filename"):
        return "https://www.supremecourt.gov" + unquote(query["filename"][0]).lower()
    return clean


def normalized_source_label(value: str) -> str:
    """Normalize a source title or citation for conservative prose matching."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def source_label_is_distinctive(value: str) -> bool:
    """Reject labels too short or generic to identify a source reliably."""
    normalized = normalized_source_label(value)
    tokens = normalized.split()
    legal_citation = re.search(
        r"(?:U\.S\.C\.|C\.F\.R\.|Federal Rule|\bv\.)", value, re.IGNORECASE
    )
    return bool(legal_citation) or (len(normalized) >= 16 and len(tokens) >= 3)


def mechanically_cited_source_ids(
    rows: list[dict[str, str]],
    corpus: str,
    *,
    count_identifier_references: bool = True,
    count_label_references: bool = True,
) -> set[str]:
    referenced_ids = set(re.findall(r"\bSRC-\d{4}\b", corpus)) if count_identifier_references else set()
    corpus_lower = corpus.lower()
    normalized_corpus = normalized_source_label(corpus)
    cited: set[str] = set()
    for row in rows:
        source_id = row.get("Source ID", "").strip()
        url = normalized_citation_url(row.get("URL", ""))
        labels = [row.get("Title or Description", "").strip()]
        label_match = count_label_references and any(
            source_label_is_distinctive(label)
            and (
                label.lower() in corpus_lower
                or normalized_source_label(label) in normalized_corpus
            )
            for label in labels
            if label
        )
        if source_id in referenced_ids or (url and url in corpus) or label_match:
            cited.add(source_id)
    return cited


def check_registry_and_sources(
    issue_map: dict[str, Path],
    failures: list[str],
    warnings: list[str],
    github_issue_bodies: str = "",
) -> None:
    with REGISTRY_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    numbers = [row.get("GitHub Number", "") for row in rows if row.get("GitHub Number")]
    for value, count in Counter(numbers).items():
        if count > 1:
            report("ERROR", f"duplicate GitHub issue number in registry: {value}", failures, warnings)
    object_ids = [row.get("Object ID", "") for row in rows if row.get("Object ID")]
    for value, count in Counter(object_ids).items():
        if count > 1:
            report("ERROR", f"duplicate GitHub Project object identifier in registry: {value}", failures, warnings)
    for row in rows:
        canonical = row.get("Canonical Record", "").strip()
        if canonical.startswith(("areas/", "legislation/", "topics/", "framework/")) and not (ROOT / canonical).exists():
            report("ERROR", f"registry canonical record is missing: {canonical}", failures, warnings)
    with SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    with PENDING_SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        pending_rows = list(csv.DictReader(handle))
    source_workflow_fields = {
        "Retention Rationale",
        "Pending Reason",
        "Next Action",
        "Blocker",
        "Monitoring Rationale",
        "Monitoring Group",
        "Monitoring Baseline",
    }
    for catalog_name, catalog_rows in (
        ("sources.csv", source_rows),
        ("sources-pending.csv", pending_rows),
    ):
        if catalog_rows:
            missing_fields = source_workflow_fields - set(catalog_rows[0])
            if missing_fields:
                report(
                    "ERROR",
                    f"{catalog_name} lacks source-workflow field(s): "
                    + ", ".join(sorted(missing_fields)),
                    failures,
                    warnings,
                )
    if source_rows and pending_rows and set(source_rows[0]) != set(pending_rows[0]):
        report("ERROR", "sources.csv and sources-pending.csv use different columns", failures, warnings)
    for row in pending_rows:
        source_id = row.get("Source ID", "unnumbered pending source")
        for field in ("Retention Rationale", "Pending Reason", "Next Action"):
            if not row.get(field, "").strip():
                report(
                    "ERROR",
                    f"{source_id} lacks required pending-source field: {field}",
                    failures,
                    warnings,
                )
    for catalog_name, catalog_rows in (
        ("sources.csv", source_rows),
        ("sources-pending.csv", pending_rows),
    ):
        for row in catalog_rows:
            source_url = row.get("URL", "").strip()
            if source_url and not source_url.startswith(("http://", "https://")):
                report(
                    "ERROR",
                    f"{row.get('Source ID', 'unnumbered source')} in {catalog_name} is not an external source URL",
                    failures,
                    warnings,
                )
            tracker_status = re.search(
                r"tracker status:\s*([^.;]+(?:\([^)]*\))?)",
                row.get("Proposition Supported", ""),
                flags=re.IGNORECASE,
            )
            if (
                row.get("Source Type", "").strip() == "Court Docket or Judicial Record"
                and tracker_status
                and not tracker_status.group(1).casefold().startswith("case closed")
                and row.get("Monitoring", "").strip() != "Yes"
            ):
                report(
                    "ERROR",
                    f"{row.get('Source ID', 'unnumbered source')} in {catalog_name} "
                    "is an open tracker case record but is not marked for monitoring",
                    failures,
                    warnings,
                )
            if row.get("Monitoring", "").strip() != "Yes":
                continue
            source_id = row.get("Source ID", "unnumbered monitored source")
            for field in ("Monitoring Rationale", "Monitoring Group"):
                if not row.get(field, "").strip():
                    report(
                        "ERROR",
                        f"{source_id} in {catalog_name} lacks required monitored-source field: {field}",
                        failures,
                        warnings,
                    )
            baseline = row.get("Monitoring Baseline", "").strip()
            if baseline and not baseline.startswith("arrp-case-monitor:v1:"):
                report(
                    "ERROR",
                    f"{source_id} in {catalog_name} has an unrecognized Monitoring Baseline format",
                    failures,
                    warnings,
                )
    source_ids = [row.get("Source ID", "") for row in [*source_rows, *pending_rows] if row.get("Source ID")]
    for value, count in Counter(source_ids).items():
        if count > 1:
            report("ERROR", f"duplicate source identifier across source catalogs: {value}", failures, warnings)
    malformed_source_ids = [value for value in source_ids if not re.fullmatch(r"SRC-\d{4}", value)]
    if malformed_source_ids:
        report(
            "ERROR",
            "malformed source identifier(s): " + ", ".join(sorted(malformed_source_ids)),
            failures,
            warnings,
        )
    normalized_urls: dict[str, list[tuple[str, str]]] = {}
    for catalog_name, catalog_rows in (("sources.csv", source_rows), ("sources-pending.csv", pending_rows)):
        for row in catalog_rows:
            normalized = normalized_source_url(row.get("URL", ""))
            if normalized:
                normalized_urls.setdefault(normalized, []).append((catalog_name, row.get("Source ID", "")))
    duplicate_urls = {
        url: records for url, records in normalized_urls.items() if len(records) > 1
    }
    for url, records in sorted(duplicate_urls.items()):
        labels = ", ".join(f"{catalog}:{source_id}" for catalog, source_id in records)
        report("ERROR", f"duplicate source URL across catalogs: {url} ({labels})", failures, warnings)

    corpus = source_citation_corpus(github_issue_bodies)
    structured_citations = structured_source_citation_ids(failures, warnings)
    unknown_structured_sources = structured_citations - set(source_ids)
    if unknown_structured_sources:
        report(
            "ERROR",
            "structured records cite source IDs absent from both source catalogs: "
            + ", ".join(sorted(unknown_structured_sources)),
            failures,
            warnings,
        )
    cited_catalog = mechanically_cited_source_ids(source_rows, corpus) | structured_citations
    uncited_catalog = [row["Source ID"] for row in source_rows if row.get("Source ID") not in cited_catalog]
    if uncited_catalog:
        sample = ", ".join(uncited_catalog[:10])
        report(
            "WARNING",
            f"{len(uncited_catalog)} cited-catalog source row(s) lack a machine-detectable Markdown citation; reconcile before treating them as confirmed citations (for example: {sample})",
            failures,
            warnings,
        )
    cited_pending = mechanically_cited_source_ids(
        pending_rows,
        corpus,
        count_identifier_references=False,
        count_label_references=False,
    ) | ({row.get("Source ID", "") for row in pending_rows} & structured_citations)
    if cited_pending:
        report(
            "ERROR",
            "pending source row(s) appear in ARRP Markdown and must move to sources.csv: "
            + ", ".join(sorted(cited_pending)),
            failures,
            warnings,
        )

    research_paths = [
        path
        for suffix in ("*.md", "*.csv")
        for path in (ROOT / "research").glob(suffix)
        if path.name != "trump-administration-preliminary-candidates.csv"
    ]
    url_pattern = re.compile(r"https?://[^\s<>'\"\]\),]+")
    ignored_hosts = {"127.0.0.1", "localhost", "www.w3.org"}
    for path in sorted(research_paths):
        for raw_url in url_pattern.findall(read(path)):
            url = raw_url.rstrip(".,;:")
            parsed = urlsplit(url)
            if parsed.hostname in ignored_hosts:
                continue
            if parsed.hostname in {"github.com", "raw.githubusercontent.com"} and "/Thorncrag/ARRP" in parsed.path:
                continue
            normalized = normalized_source_url(url)
            if normalized and normalized not in normalized_urls:
                report(
                    "ERROR",
                    f"research source URL is absent from both source catalogs in {path.relative_to(ROOT)}: {url}",
                    failures,
                    warnings,
                )

    accountable_id = re.compile(r"\b(?:INTAKE-GAP|HOR|[A-Z]{2,})-\d{3}(?:-MON)?\b")
    for row in pending_rows:
        association = row.get("Associated Record IDs", "").strip()
        possible_destinations = {
            match.group(0)
            for match in accountable_id.finditer(association)
            if not match.group(0).endswith("-MON")
        }
        research_owners = [
            part.strip()
            for part in association.split(";")
            if part.strip().startswith("research/")
        ]
        valid_research_owner = any((ROOT / owner).exists() for owner in research_owners)
        if not association or not (accountable_id.search(association) or valid_research_owner):
            report(
                "ERROR",
                f"pending source {row.get('Source ID', '<unknown>')} lacks an accountable issue, monitor, candidate, or research-record owner",
                failures,
                warnings,
            )
        elif len(possible_destinations) < 2 and not valid_research_owner:
            report(
                "ERROR",
                f"pending source {row.get('Source ID', '<unknown>')} has a single clear destination and must be cited by that owner and moved to sources.csv",
                failures,
                warnings,
            )
        routing_action = row.get("Next Action", "").casefold()
        if not routing_action or not any(
            term in routing_action
            for term in ("route", "choose", "determine", "identify")
        ):
            report(
                "ERROR",
                f"pending source {row.get('Source ID', '<unknown>')} lacks an explicit routing decision in Next Action",
                failures,
                warnings,
            )

    with PRELIMINARY_CANDIDATE_PATH.open(newline="", encoding="utf-8") as handle:
        candidates = list(csv.DictReader(handle))
    known_source_ids = set(source_ids)
    required_candidate_fields = (
        "candidate_id",
        "title",
        "term",
        "proposed_area",
        "institutional_defect",
        "distinctness_rationale",
        "existing_coverage_considered",
        "counterargument",
        "unresolved_questions",
        "recommendation",
    )
    for row in candidates:
        if row.get("review_status") != "preliminary-candidate":
            continue
        missing = [field for field in required_candidate_fields if not row.get(field, "").strip()]
        if missing:
            report(
                "ERROR",
                f"preliminary candidate {row.get('candidate_id', '<unknown>')} lacks: {', '.join(missing)}",
                failures,
                warnings,
            )
        attached_sources = {
            source_id.strip()
            for source_id in row.get("source_record_ids", "").split(";")
            if source_id.strip()
        }
        if not attached_sources and not row.get("source_links", "").strip():
            report(
                "ERROR",
                f"preliminary candidate {row.get('candidate_id', '<unknown>')} has no supporting source",
                failures,
                warnings,
            )
        unknown = attached_sources - known_source_ids
        if unknown:
            report(
                "ERROR",
                f"preliminary candidate {row.get('candidate_id', '<unknown>')} references unknown sources: {', '.join(sorted(unknown))}",
                failures,
                warnings,
            )


def check_reader_language(failures: list[str], warnings: list[str]) -> None:
    for path in reader_pages():
        body = markdown_body(path)
        for label, pattern in READER_LANGUAGE_PATTERNS.items():
            if pattern.search(body):
                report("WARNING", f"{label} in reader-facing {path.relative_to(ROOT)}", failures, warnings)


def check_tool_interface_theme(failures: list[str], warnings: list[str]) -> None:
    required_variables = (
        "--ink:",
        "--muted:",
        "--line:",
        "--soft:",
        "--blue:",
        "--blue-soft:",
        "--gold:",
        "--gold-soft:",
        "--green:",
        "--shadow:",
    )
    for html_path, css_path in TOOL_INTERFACES:
        if not html_path.exists() or not css_path.exists():
            report(
                "ERROR",
                f"project-operated interface is missing HTML or CSS: {html_path.relative_to(ROOT)}",
                failures,
                warnings,
            )
            continue
        if 'data-interface-theme="arrp-tool"' not in read(html_path):
            report(
                "ERROR",
                f"{html_path.relative_to(ROOT)} lacks the ARRP tool-interface theme marker",
                failures,
                warnings,
            )
        css = read(css_path)
        missing = [variable for variable in required_variables if variable not in css]
        if missing:
            report(
                "ERROR",
                f"{css_path.relative_to(ROOT)} lacks interface variables: {', '.join(missing)}",
                failures,
                warnings,
            )
        if "linear-gradient(120deg, #152743, #244c85)" not in css:
            report(
                "ERROR",
                f"{css_path.relative_to(ROOT)} lacks the standard tool-interface header gradient",
                failures,
                warnings,
            )


def check_duplicate_copy_artifacts(failures: list[str], warnings: list[str]) -> None:
    """Flag common Finder-style copies when the unsuffixed sibling still exists."""
    excluded_roots = {".git", ".site-build", ".tmp", ".venv"}
    copy_suffix = re.compile(r"(?: copy| \([0-9]+\)| [0-9]+)$", re.IGNORECASE)
    for path in ROOT.rglob("*"):
        if not path.is_file() or excluded_roots.intersection(path.relative_to(ROOT).parts):
            continue
        canonical_stem = copy_suffix.sub("", path.stem)
        if canonical_stem == path.stem:
            continue
        canonical = path.with_name(f"{canonical_stem}{path.suffix}")
        if canonical.exists():
            report(
                "WARNING",
                f"possible duplicate-copy artifact {path.relative_to(ROOT)} has canonical sibling {canonical.relative_to(ROOT)}",
                failures,
                warnings,
            )


def check_intake_workflow_language(failures: list[str], warnings: list[str]) -> None:
    stale_phrases = (
        "unified Sources queue",
        "Source Intake Dashboard",
        "Monitoring queue",
        "candidate-and-source dashboard",
        "Candidate Issues and Source Intake",
        "Candidate and Source Intake",
        "Candidate Issue Intake",
    )
    for path in CURRENT_INTAKE_WORKFLOW_FILES:
        if not path.exists():
            report(
                "ERROR",
                f"current intake-workflow file is missing: {path.relative_to(ROOT)}",
                failures,
                warnings,
            )
            continue
        content = read(path)
        for phrase in stale_phrases:
            if phrase.lower() in content.lower():
                report(
                    "ERROR",
                    f"stale intake-workflow phrase {phrase!r} in {path.relative_to(ROOT)}",
                    failures,
                    warnings,
                )


def check_retired_monitor_identifiers(
    github_issue_bodies: str, failures: list[str], warnings: list[str]
) -> None:
    """Prevent restoration of the retired standalone monitoring-row identifier series."""
    retired = re.compile(r"\bMON-" r"\d{4}\b")
    for path in active_project_files(".csv", ".js", ".json", ".md", ".py", ".yml", ".yaml"):
        if retired.search(read(path)):
            report(
                "ERROR",
                f"retired standalone monitoring identifier remains in {path.relative_to(ROOT)}",
                failures,
                warnings,
            )
    if retired.search(github_issue_bodies):
        report(
            "ERROR",
            "retired standalone monitoring identifier remains in an open GitHub issue body",
            failures,
            warnings,
        )


def check_print_assignment_metadata(failures: list[str], warnings: list[str]) -> None:
    excluded_roots = {".git", ".site-build", ".tmp", ".venv"}
    explicit_exceptions = {
        ROOT / "AGENTS.md",
        ROOT / "website" / "404.md",
    }
    for path in ROOT.rglob("*.md"):
        if excluded_roots.intersection(path.relative_to(ROOT).parts) or path in explicit_exceptions:
            continue
        metadata = front_matter(path)
        levels = front_matter_list(path, "print_levels")
        status = metadata.get("print_status", "")
        reason = metadata.get("print_exclusion_reason", "")
        invalid_levels = sorted(set(levels) - PRINT_LEVELS)
        if invalid_levels:
            report(
                "ERROR",
                f"{path.relative_to(ROOT)} has invalid print level(s): {', '.join(invalid_levels)}",
                failures,
                warnings,
            )
        if status and status != "excluded":
            report(
                "ERROR",
                f"{path.relative_to(ROOT)} has invalid print_status {status!r}",
                failures,
                warnings,
            )
        if levels and status == "excluded":
            report(
                "ERROR",
                f"{path.relative_to(ROOT)} has conflicting publication disposition: print levels and excluded status",
                failures,
                warnings,
            )
        elif not levels and status != "excluded":
            report(
                "ERROR",
                f"{path.relative_to(ROOT)} is unclassified for publication: add print_levels or print_status excluded",
                failures,
                warnings,
            )
        elif status == "excluded" and not reason:
            report(
                "ERROR",
                f"{path.relative_to(ROOT)} is excluded from print without a print_exclusion_reason",
                failures,
                warnings,
            )
        elif status != "excluded" and reason:
            report(
                "ERROR",
                f"{path.relative_to(ROOT)} has a print_exclusion_reason without excluded print_status",
                failures,
                warnings,
            )


def check_front_door_routes(failures: list[str], warnings: list[str]) -> None:
    """Require the three reader-discovery routes named by the methodology."""
    root = ROOT / "README.md"
    targets = {
        target.resolve()
        for raw_target in MARKDOWN_LINK_RE.findall(markdown_body(root))
        if (target := local_target(root, raw_target))
    }
    required = {
        ROOT / "SUBJECT_INDEX.md": "Subject and Institution Index",
        ROOT / "topics" / "README.md": "Explore by Topic",
        ROOT / "areas" / "README.md": "area-first discovery",
    }
    for path, label in required.items():
        if path.resolve() not in targets:
            report("ERROR", f"README.md lacks the required {label} route", failures, warnings)


def check_structured_files_and_repository_hygiene(
    failures: list[str], warnings: list[str]
) -> None:
    """Validate deterministic file formats and common repository hygiene rules."""
    for path in active_project_files(".json"):
        try:
            json.loads(read(path))
        except json.JSONDecodeError as error:
            report(
                "ERROR",
                f"invalid JSON in {path.relative_to(ROOT)}:{error.lineno}: {error.msg}",
                failures,
                warnings,
            )
    for path in active_project_files(".yml", ".yaml"):
        try:
            yaml.safe_load(read(path))
        except yaml.YAMLError as error:
            mark = getattr(error, "problem_mark", None)
            location = f":{mark.line + 1}" if mark is not None else ""
            report(
                "ERROR",
                f"invalid YAML in {path.relative_to(ROOT)}{location}: {getattr(error, 'problem', str(error))}",
                failures,
                warnings,
            )
    for path in active_project_files(".csv"):
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                fields = reader.fieldnames or []
                if not fields or any(not field for field in fields):
                    report("ERROR", f"{path.relative_to(ROOT)} has an empty CSV header", failures, warnings)
                    continue
                duplicates = sorted(field for field, count in Counter(fields).items() if count > 1)
                if duplicates:
                    report(
                        "ERROR",
                        f"{path.relative_to(ROOT)} has duplicate CSV columns: {', '.join(duplicates)}",
                        failures,
                        warnings,
                    )
                for row_number, row in enumerate(reader, start=2):
                    if None in row:
                        report(
                            "ERROR",
                            f"{path.relative_to(ROOT)}:{row_number} has more values than CSV columns",
                            failures,
                            warnings,
                        )
        except csv.Error as error:
            report("ERROR", f"invalid CSV in {path.relative_to(ROOT)}: {error}", failures, warnings)

    for path in reader_pages():
        content = read(path)
        if re.search(r"(?:file:///|/Users/[^\s)]+)", content):
            report(
                "ERROR",
                f"reader-facing {path.relative_to(ROOT)} contains a local filesystem reference",
                failures,
                warnings,
            )

    participation_source = ROOT / "participate" / "intake-data.js"
    participation_index = ROOT / "participate" / "api" / "route-index.js"
    try:
        source_text = read(participation_source)
        source_prefix = "window.ARRP_PARTICIPATION_DATA="
        source_payload = json.loads(source_text.split(source_prefix, 1)[1].strip().removesuffix(";"))
        expected_routes = [
            {
                "id": record["id"],
                "title": record["title"],
                "area": record["area"],
                "canonical_page": record["canonical_page"],
                "issue_url": record["issue_url"],
            }
            for record in [*source_payload["proposal_index"], *source_payload["horizon_index"]]
        ]
        index_text = read(participation_index)
        index_match = re.search(
            r"const records = Object\.freeze\((\[.*?\])\);\n\nconst proposals",
            index_text,
            re.DOTALL,
        )
        if not index_match:
            raise ValueError("route-record marker is missing")
        actual_routes = json.loads(index_match.group(1))
        if actual_routes != expected_routes:
            report(
                "ERROR",
                "participate/api/route-index.js is stale relative to participate/intake-data.js",
                failures,
                warnings,
            )
    except (IndexError, KeyError, json.JSONDecodeError, ValueError) as error:
        report(
            "ERROR",
            f"participation route-index validation failed: {error}",
            failures,
            warnings,
        )

    generic_source_phrases = (
        "Source-development record for the described government action",
        "Supports HOR-0",
    )
    horizon_source_records = sorted(
        (ROOT / "research" / "horizon-source-records").glob("HOR-*-source-development.md")
    )
    for path in horizon_source_records:
        content = read(path)
        for phrase in generic_source_phrases:
            if phrase in content:
                report(
                    "ERROR",
                    f"{path.relative_to(ROOT)} retains a generic source-development proposition beginning {phrase!r}",
                    failures,
                    warnings,
                )

    area_source_records = sorted(
        path
        for path in (ROOT / "areas").glob("*/research/*-source-development.md")
        if path.is_file()
    )
    for path in area_source_records:
        content = read(path)
        matches = sum(content.count(phrase) for phrase in generic_source_phrases)
        if matches:
            report(
                "WARNING",
                f"{path.relative_to(ROOT)} contains {matches} generic source-development "
                "proposition(s) requiring source-specific review",
                failures,
                warnings,
            )

    try:
        tracked = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        ).stdout.decode("utf-8", errors="replace").split("\0")
    except FileNotFoundError:
        tracked = []
    forbidden_names = {".DS_Store", ".env", ".env.local"}
    for value in tracked:
        if not value:
            continue
        name = Path(value).name
        if name in forbidden_names or name.endswith((".bak", ".orig", ".rej", "~")):
            report("ERROR", f"tracked repository artifact should not be committed: {value}", failures, warnings)


def check_print_assembly_configuration(failures: list[str], warnings: list[str]) -> None:
    path = ROOT / "framework" / "print-assembly.json"
    try:
        config = json.loads(read(path))
    except (OSError, json.JSONDecodeError):
        return
    editions = config.get("editions") or []
    edition_ids = [str(edition.get("id") or "") for edition in editions]
    duplicates = sorted(value for value, count in Counter(edition_ids).items() if value and count > 1)
    if duplicates:
        report("ERROR", f"print-assembly.json has duplicate edition IDs: {', '.join(duplicates)}", failures, warnings)
    missing = PRINT_LEVELS - set(edition_ids)
    extra = set(edition_ids) - PRINT_LEVELS
    if missing or extra:
        report(
            "ERROR",
            "print-assembly.json edition IDs differ from allowed print levels"
            + (f"; missing {', '.join(sorted(missing))}" if missing else "")
            + (f"; unexpected {', '.join(sorted(extra))}" if extra else ""),
            failures,
            warnings,
        )
    for edition in editions:
        sections = edition.get("sections") or []
        section_ids = [str(section.get("id") or "") for section in sections]
        if not section_ids or any(not value for value in section_ids):
            report("ERROR", f"print edition {edition.get('id')!r} has an unnamed or empty section", failures, warnings)
        repeated = sorted(value for value, count in Counter(section_ids).items() if value and count > 1)
        if repeated:
            report(
                "ERROR",
                f"print edition {edition.get('id')!r} has duplicate sections: {', '.join(repeated)}",
                failures,
                warnings,
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Write a structured integrity report for the Project Console.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        help="Write a deterministic current-findings snapshot in Markdown.",
    )
    parser.add_argument(
        "--exit-zero-on-findings",
        action="store_true",
        help="Report detected findings without failing an automated observation run.",
    )
    return parser.parse_args()


def finding_category(message: str) -> str:
    lowered = message.lower()
    categories = (
        ("Internal links", ("broken local link", "repository link", "orphaned markdown")),
        ("Sources and citations", ("source", "citation", "bibliograph")),
        ("GitHub records", ("github issue", "github pages", "project object", "registry", "deployment")),
        ("Print metadata", ("print_levels", "print level", "print_status", "publication disposition", "print exclusion")),
        ("Issue structure", ("issue page", "required heading", "heading level", "h1 headings", "audit-history", "title metadata")),
        ("Topic guides", ("topic", "applicable proposals", "related ideas", "subject_index")),
        ("Research placement", ("research", "source-development")),
        ("Reader-facing language", ("reader-facing", "sham", "audit-tier", "rebaseline")),
        ("Tool interfaces", ("interface", "theme", "console", "participat")),
        ("Intake workflow", ("intake", "candidate", "horizon")),
    )
    for label, signals in categories:
        if any(signal in lowered for signal in signals):
            return label
    return "Project structure"


def finding_path(message: str) -> str:
    match = re.search(
        r"(?<![\w.-])((?:areas|framework|inventory|legislation|participate|research|scripts|tests|topics|website)/[^\s:,)]+)",
        message,
    )
    return match.group(1).rstrip(".\"'") if match else ""


def git_revision() -> str:
    configured = os.environ.get("GITHUB_SHA", "").strip()
    if configured:
        return configured
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def structured_report(
    failures: list[str],
    warnings: list[str],
    issue_count: int,
    proposal_count: int,
    duration_seconds: float,
) -> dict[str, object]:
    findings = []
    for severity, messages in (("error", failures), ("warning", warnings)):
        for position, message in enumerate(messages, start=1):
            clean = re.sub(r"^(?:ERROR|WARNING):\s*", "", message)
            findings.append(
                {
                    "id": f"{severity}-{position:04d}",
                    "severity": severity,
                    "category": finding_category(clean),
                    "message": clean,
                    "path": finding_path(clean),
                }
            )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "revision": git_revision(),
        "result": "findings" if findings else "clean",
        "counts": {
            "errors": len(failures),
            "warnings": len(warnings),
            "findings": len(findings),
            "issue_pages": issue_count,
            "proposal_pages": proposal_count,
        },
        "duration_seconds": round(duration_seconds, 3),
        "scope": [
            "Issue and proposal structure",
            "Area and topic routing",
            "Internal repository links",
            "Markdown heading anchors",
            "Orphaned Markdown pages",
            "Page metadata and heading hierarchy",
            "Cross-issue reference links",
            "GitHub record references",
            "GitHub Issue and Project synchronization",
            "GitHub Pages deployment synchronization",
            "Source and citation catalogs",
            "Research placement",
            "Reader-facing language",
            "Tool-interface conventions",
            "Intake-workflow terminology",
            "Publication-disposition metadata",
            "Print-assembly configuration",
            "Structured-file and repository hygiene",
        ],
        "findings": findings,
    }


def markdown_report(report_data: dict[str, object]) -> str:
    """Render a stable current-state report without accumulating run history."""
    counts = report_data.get("counts", {})
    findings = report_data.get("findings", [])
    lines = [
        "---",
        'title: "Current Project Integrity Report"',
        "print_status: excluded",
        'print_exclusion_reason: "Internal operational report."',
        "---",
        "",
        "# Current Project Integrity Report",
        "",
        "> This file is an overwritten current-state snapshot, not a running log or an audit tier. "
        "GitHub Actions and the Project Console retain the latest run time and bounded run history. "
        "The file changes only when the finding set, checked-page counts, or check scope changes.",
        "",
        "## Current Result",
        "",
        f"- **Result:** {'Findings require review' if findings else 'Clean'}",
        f"- **Errors:** {int(counts.get('errors', 0))}",
        f"- **Warnings:** {int(counts.get('warnings', 0))}",
        f"- **Issue pages checked:** {int(counts.get('issue_pages', 0))}",
        f"- **Proposal pages checked:** {int(counts.get('proposal_pages', 0))}",
        "",
        "## Current Findings",
        "",
    ]
    if not findings:
        lines.extend(["No repeatable integrity findings are currently reported.", ""])
    else:
        grouped: dict[str, list[dict[str, object]]] = {}
        for finding in findings:
            grouped.setdefault(str(finding.get("category", "Project structure")), []).append(finding)
        for category in sorted(grouped):
            lines.extend([f"### {category}", ""])
            for finding in grouped[category]:
                severity = str(finding.get("severity", "warning")).upper()
                message = str(finding.get("message", "Unspecified finding"))
                lines.append(f"- **{severity}:** {message}")
            lines.append("")
    lines.extend(["## Checks Included", ""])
    lines.extend(f"- {item}" for item in report_data.get("scope", []))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    failures: list[str] = []
    warnings: list[str] = []
    issue_map = check_issue_pages(failures, warnings)
    check_legislation(issue_map, failures, warnings)
    check_area_indexes(issue_map, failures, warnings)
    check_issue_layout(issue_map, failures, warnings)
    check_topic_pages(failures, warnings)
    check_markdown_links(failures, warnings)
    check_html_links(failures, warnings)
    check_embedded_repository_links(failures, warnings)
    check_orphaned_markdown_pages(failures, warnings)
    check_markdown_metadata_and_headings(failures, warnings)
    check_reader_navigation_coverage(issue_map, failures, warnings)
    check_cross_issue_links(issue_map, failures, warnings)
    check_front_door_routes(failures, warnings)
    github_issues = fetch_github_issues(failures, warnings)
    project_items = fetch_github_project_items(failures, warnings)
    github_issue_bodies = check_github_issue_links(github_issues, failures, warnings)
    check_github_synchrony(issue_map, github_issues, project_items, failures, warnings)
    check_github_pages_deployment(failures, warnings)
    check_registry_and_sources(issue_map, failures, warnings, github_issue_bodies)
    check_research_placement(failures, warnings)
    check_reader_language(failures, warnings)
    check_tool_interface_theme(failures, warnings)
    check_duplicate_copy_artifacts(failures, warnings)
    check_intake_workflow_language(failures, warnings)
    check_retired_monitor_identifiers(github_issue_bodies, failures, warnings)
    check_print_assignment_metadata(failures, warnings)
    check_print_assembly_configuration(failures, warnings)
    check_structured_files_and_repository_hygiene(failures, warnings)
    proposal_count = len(list(LEGISLATION_PATH.glob("*.md"))) - 1
    print(f"Checked {len(issue_map)} issue pages, {proposal_count} proposal pages, and project links/inventories.")
    for line in failures + warnings:
        print(line)
    print(f"Result: {len(failures)} error(s), {len(warnings)} warning(s).")
    report_data = structured_report(
        failures,
        warnings,
        len(issue_map),
        proposal_count,
        time.monotonic() - started,
    )
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(report_data, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote structured report to {args.json_output}.")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown_report(report_data), encoding="utf-8")
        print(f"Wrote current Markdown report to {args.markdown_output}.")
    return 1 if failures and not args.exit_zero_on_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
