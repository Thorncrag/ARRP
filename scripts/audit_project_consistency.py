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

import csv
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
ISSUE_PATH = ROOT / "areas"
LEGISLATION_PATH = ROOT / "legislation"
REGISTRY_PATH = ROOT / "inventory" / "github_issue_registry.csv"
SOURCE_PATH = ROOT / "inventory" / "sources.csv"
PENDING_SOURCE_PATH = ROOT / "inventory" / "sources-pending.csv"
PRELIMINARY_CANDIDATE_PATH = ROOT / "research" / "trump-administration-preliminary-candidates.csv"
GITHUB_REPOSITORY = "Thorncrag/ARRP"
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
    ROOT / "framework" / "METHODOLOGY.md",
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


def markdown_body(path: Path) -> str:
    return FRONT_MATTER_RE.sub("", read(path), count=1)


def local_target(path: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().strip("<>").split(" ", 1)[0]
    if not target or target.startswith(("#", "http://", "https://", "mailto:", "data:")):
        return None
    target = unquote(target.split("#", 1)[0])
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
        if not re.search(rf"^# {re.escape(issue_id)}\s+—\s+", body, re.MULTILINE):
            report("ERROR", f"{issue_id} title heading does not begin with its identifier", failures, warnings)
        sidecar = path.with_name(f"{issue_id}.audit.md")
        if data.get("record_type") == "source-development":
            front_matter_match = FRONT_MATTER_RE.match(read(path))
            front_matter_text = front_matter_match.group(1) if front_matter_match else ""
            if "public-proposal" in front_matter_text:
                report(
                    "ERROR",
                    f"{issue_id} source-development shell must remain full-technical only",
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
        issue_id = re.sub(r"-(?:state|amendment|preferred)$", "", proposal_id)
        if not ISSUE_ID_RE.fullmatch(issue_id):
            report("ERROR", f"{path.relative_to(ROOT)} lacks a valid issue_id", failures, warnings)
            continue
        if issue_id not in issue_map:
            report("ERROR", f"{path.relative_to(ROOT)} identifies unknown issue {issue_id}", failures, warnings)
        framework_issue = (data.get("framework_issue") or data.get("linked_issue") or "").strip('"')
        if not framework_issue:
            report("ERROR", f"{path.relative_to(ROOT)} lacks framework_issue metadata", failures, warnings)
        else:
            target = local_target(path, framework_issue)
            if target and not target.exists():
                report("ERROR", f"{path.relative_to(ROOT)} framework_issue target is missing", failures, warnings)
        body = markdown_body(path)
        if not re.search(r"^## Budgetary Impact Statement$", body, re.MULTILINE):
            report("WARNING", f"{path.relative_to(ROOT)} lacks Budgetary Impact Statement", failures, warnings)


def check_area_indexes(issue_map: dict[str, Path], failures: list[str], warnings: list[str]) -> None:
    for issue_id, page in issue_map.items():
        area_readme = page.parents[1] / "README.md"
        if not area_readme.exists():
            report("ERROR", f"{issue_id} has no area README", failures, warnings)
            continue
        if not re.search(rf"\b{re.escape(issue_id)}\b", read(area_readme)):
            report("ERROR", f"{issue_id} is absent from {area_readme.relative_to(ROOT)}", failures, warnings)

    for area_readme in sorted(ROOT.glob("areas/*/README.md")):
        headings = re.findall(r"^## (.+)$", markdown_body(area_readme), re.MULTILINE)
        for heading in ("Generalized Institutional Concern", "Active Issues", "Issue Boundaries", "Notes"):
            if headings.count(heading) != 1:
                report("ERROR", f"{area_readme.relative_to(ROOT)} must contain one {heading!r} heading", failures, warnings)
        if all(heading in headings for heading in ("Generalized Institutional Concern", "Active Issues", "Issue Boundaries", "Notes")):
            order = [headings.index(heading) for heading in ("Generalized Institutional Concern", "Active Issues", "Issue Boundaries", "Notes")]
            if order != sorted(order):
                report("ERROR", f"{area_readme.relative_to(ROOT)} has out-of-order standard headings", failures, warnings)


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


def check_html_links(failures: list[str], warnings: list[str]) -> None:
    """Validate static relative href and src targets in active project HTML."""
    for path in active_project_files(".html"):
        for _, raw_target in HTML_LINK_RE.findall(read(path)):
            if "{{" in raw_target or "{%" in raw_target:
                continue
            target = local_target(path, raw_target)
            if target and not target.exists():
                report("ERROR", f"broken local link in {path.relative_to(ROOT)}: {raw_target}", failures, warnings)


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


def check_github_issue_links(failures: list[str], warnings: list[str]) -> str:
    """Validate issue-body repository links and return bodies for source reconciliation."""
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
        "number,title,body,url",
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        report(
            "WARNING",
            "GitHub issue-body link check skipped because the gh CLI is unavailable",
            failures,
            warnings,
        )
        return ""
    if completed.returncode:
        detail = completed.stderr.strip().splitlines()
        suffix = f": {detail[-1]}" if detail else ""
        report(
            "WARNING",
            "GitHub issue-body link check could not query the repository; rerun the consistency audit "
            f"in the authenticated host context{suffix}",
            failures,
            warnings,
        )
        return ""
    try:
        issues = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        report(
            "ERROR",
            f"GitHub issue-body link check received invalid JSON: {error}",
            failures,
            warnings,
        )
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
    return "\n".join(issue.get("body") or "" for issue in issues)


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
    numbers = [row.get("GitHub Issue Number", "") for row in rows if row.get("GitHub Issue Number")]
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
        if "print_levels" not in front_matter(path):
            report(
                "ERROR",
                f"{path.relative_to(ROOT)} lacks required print_levels metadata",
                failures,
                warnings,
            )


def main() -> int:
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
    github_issue_bodies = check_github_issue_links(failures, warnings)
    check_registry_and_sources(issue_map, failures, warnings, github_issue_bodies)
    check_research_placement(failures, warnings)
    check_reader_language(failures, warnings)
    check_tool_interface_theme(failures, warnings)
    check_duplicate_copy_artifacts(failures, warnings)
    check_intake_workflow_language(failures, warnings)
    check_retired_monitor_identifiers(github_issue_bodies, failures, warnings)
    check_print_assignment_metadata(failures, warnings)
    print(f"Checked {len(issue_map)} issue pages, {len(list(LEGISLATION_PATH.glob('*.md'))) - 1} proposal pages, and project links/inventories.")
    for line in failures + warnings:
        print(line)
    print(f"Result: {len(failures)} error(s), {len(warnings)} warning(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
