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
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
ISSUE_PATH = ROOT / "areas"
LEGISLATION_PATH = ROOT / "legislation"
REGISTRY_PATH = ROOT / "inventory" / "github_issue_registry.csv"
SOURCE_PATH = ROOT / "inventory" / "sources.csv"
PENDING_SOURCE_PATH = ROOT / "inventory" / "sources-pending.csv"

LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
ISSUE_ID_RE = re.compile(r"^[A-Z]+-\d{3}$")

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
    return (path.parent / target).resolve()


def issue_pages() -> list[Path]:
    return sorted(path for path in ISSUE_PATH.glob("*/issues/*.md") if not path.name.endswith(".audit.md"))


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
    required = ("Overview", "Relevant Proposals", "How Concerns Map to Proposals", "What ARRP Does and Does Not Address")
    for path in sorted((ROOT / "topics").glob("*.md")):
        if path.name == "README.md":
            continue
        body = markdown_body(path)
        for heading in required:
            if not re.search(rf"^## {re.escape(heading)}$", body, re.MULTILINE):
                report("ERROR", f"{path.relative_to(ROOT)} lacks topic-page heading: {heading}", failures, warnings)
        if "| Public concern | Applicable proposals |" not in body:
            report("ERROR", f"{path.relative_to(ROOT)} lacks the standard public-concern routing table", failures, warnings)


def reader_pages() -> list[Path]:
    pages = [ROOT / "README.md", ROOT / "SUBJECT_INDEX.md"]
    pages.extend(ROOT.glob("areas/*/README.md"))
    pages.extend(issue_pages())
    pages.extend(LEGISLATION_PATH.glob("*.md"))
    pages.extend((ROOT / "topics").glob("*.md"))
    return sorted(set(pages))


def framework_pages() -> list[Path]:
    """Return technical framework pages for link-integrity checking only.

    Framework documents may appropriately use internal audit terminology, so
    they are intentionally excluded from the reader-language review.
    """
    return sorted(
        path
        for path in (ROOT / "framework").rglob("*.md")
        if "templates" not in path.parts
    )


def check_markdown_links(failures: list[str], warnings: list[str]) -> None:
    for path in [*reader_pages(), *framework_pages()]:
        if not path.exists():
            continue
        for raw_target in LINK_RE.findall(read(path)):
            target = local_target(path, raw_target)
            if target and not target.exists():
                report("ERROR", f"broken local link in {path.relative_to(ROOT)}: {raw_target}", failures, warnings)


def source_citation_corpus() -> str:
    """Return project-authored Markdown in which a source may be cited.

    Queue CSVs deliberately do not count: a retained lead, monitoring record,
    or source identifier is not a reader-facing ARRP citation.
    """
    paths = [ROOT / "README.md", ROOT / "SUBJECT_INDEX.md"]
    paths.extend((ROOT / "areas").rglob("*.md"))
    paths.extend(LEGISLATION_PATH.glob("*.md"))
    paths.extend((ROOT / "topics").glob("*.md"))
    paths.extend((ROOT / "research").glob("*.md"))
    return "\n".join(read(path) for path in sorted(set(paths)) if path.exists())


def normalized_citation_url(url: str) -> str:
    return url.strip().replace("&amp;", "&").split("#", 1)[0].split("?", 1)[0].rstrip("/")


def mechanically_cited_source_ids(rows: list[dict[str, str]], corpus: str) -> set[str]:
    referenced_ids = set(re.findall(r"\bSRC-\d{4}\b", corpus))
    cited: set[str] = set()
    for row in rows:
        source_id = row.get("Source ID", "").strip()
        url = normalized_citation_url(row.get("URL", ""))
        if source_id in referenced_ids or (url and url in corpus):
            cited.add(source_id)
    return cited


def check_registry_and_sources(issue_map: dict[str, Path], failures: list[str], warnings: list[str]) -> None:
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
    if source_rows and pending_rows and set(source_rows[0]) != set(pending_rows[0]):
        report("ERROR", "sources.csv and sources-pending.csv use different columns", failures, warnings)
    source_ids = [row.get("Source ID", "") for row in [*source_rows, *pending_rows] if row.get("Source ID")]
    for value, count in Counter(source_ids).items():
        if count > 1:
            report("ERROR", f"duplicate source identifier across source catalogs: {value}", failures, warnings)
    numeric_source_ids = sorted(
        int(value.removeprefix("SRC-"))
        for value in source_ids
        if re.fullmatch(r"SRC-\d{4}", value)
    )
    if numeric_source_ids and numeric_source_ids != list(range(1, numeric_source_ids[-1] + 1)):
        report("ERROR", "source identifiers across both catalogs are not a continuous SRC-0001 sequence", failures, warnings)
    corpus = source_citation_corpus()
    cited_catalog = mechanically_cited_source_ids(source_rows, corpus)
    uncited_catalog = [row["Source ID"] for row in source_rows if row.get("Source ID") not in cited_catalog]
    if uncited_catalog:
        sample = ", ".join(uncited_catalog[:10])
        report(
            "WARNING",
            f"{len(uncited_catalog)} cited-catalog source row(s) lack a machine-detectable Markdown citation; reconcile before treating them as confirmed citations (for example: {sample})",
            failures,
            warnings,
        )
    cited_pending = mechanically_cited_source_ids(pending_rows, corpus)
    if cited_pending:
        report(
            "ERROR",
            "pending source row(s) appear in ARRP Markdown and must move to sources.csv: "
            + ", ".join(sorted(cited_pending)),
            failures,
            warnings,
        )


def check_reader_language(failures: list[str], warnings: list[str]) -> None:
    for path in reader_pages():
        body = markdown_body(path)
        for label, pattern in READER_LANGUAGE_PATTERNS.items():
            if pattern.search(body):
                report("WARNING", f"{label} in reader-facing {path.relative_to(ROOT)}", failures, warnings)


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []
    issue_map = check_issue_pages(failures, warnings)
    check_legislation(issue_map, failures, warnings)
    check_area_indexes(issue_map, failures, warnings)
    check_issue_layout(issue_map, failures, warnings)
    check_topic_pages(failures, warnings)
    check_markdown_links(failures, warnings)
    check_registry_and_sources(issue_map, failures, warnings)
    check_reader_language(failures, warnings)
    print(f"Checked {len(issue_map)} issue pages, {len(list(LEGISLATION_PATH.glob('*.md'))) - 1} proposal pages, and project links/inventories.")
    for line in failures + warnings:
        print(line)
    print(f"Result: {len(failures)} error(s), {len(warnings)} warning(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
