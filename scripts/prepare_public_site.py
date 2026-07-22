#!/usr/bin/env python3
"""Prepare the allowlisted ARRP public-proposal tree for MkDocs.

The canonical Markdown remains in the repository's existing root, areas, and
legislation paths. This script creates an ignored staging tree containing only
material admitted by both the public-proposal metadata and the website path
policy documented in website/README.md.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = ROOT / ".site-build"
DOCS_ROOT = BUILD_ROOT / "docs"
SITE_ROOT = BUILD_ROOT / "site"
PUBLIC_LEVEL = "public-proposal"
PUBLIC_ROOT_PAGES = {
    Path("README.md"),
    Path("PRINT_READERS_GUIDE.md"),
    Path("SUBJECT_INDEX.md"),
    Path("ABOUT.md"),
    Path("LICENSE.md"),
}
PUBLIC_DIRECTORIES = {"areas", "legislation", "topics"}
PUBLIC_SUPPORT_FILES = {Path("CITATION.cff")}
WEBSITE_FILES = {
    Path("website/extra.css"): Path("assets/stylesheets/extra.css"),
    Path("website/site.js"): Path("assets/javascripts/site.js"),
    Path("website/robots.txt"): Path("robots.txt"),
    Path("website/404.md"): Path("404.md"),
}
FORBIDDEN_TERMS = (
    "project-console-data",
    "arrp_project_token",
    "progress-history-seed",
)
FRONT_MATTER_END = re.compile(r"\n---\s*\n")
LOCAL_LINK = re.compile(
    r"(?P<image>!?)\[(?P<label>[^\]\n]+)\]"
    r"\((?P<target>(?!(?:https?://|mailto:|tel:|#))[^)\n]+)\)"
)
AREA_LINK = re.compile(
    r"^- \[(A-\d{2}) / ([A-Z]+) — ([^\]]+)\]"
    r"\(([^)]+)/README\.md\)$"
)
LEGISLATION_NAME = re.compile(r"^([A-Z]+-\d{3})(?:-(.+))?$")


def relative(path: Path) -> Path:
    return path.resolve().relative_to(ROOT.resolve())


def front_matter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    match = FRONT_MATTER_END.search(text, 4)
    if not match:
        return ""
    return text[4 : match.start()]


def has_public_level(path: Path) -> bool:
    metadata = front_matter(path.read_text(encoding="utf-8"))
    return bool(re.search(rf"(?m)^\s*-\s+{re.escape(PUBLIC_LEVEL)}\s*$", metadata))


def page_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    metadata = front_matter(text)
    match = re.search(r"(?m)^title:\s*(.+?)\s*$", metadata)
    if match:
        value = match.group(1).strip()
        if value.startswith('"'):
            try:
                return str(json.loads(value))
            except json.JSONDecodeError:
                pass
        return value.strip("'\"")
    heading = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return heading.group(1) if heading else path.stem


def git_revision_timestamp(path: Path) -> int:
    """Return the last committed revision time for a canonical source file."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%at", "--", relative(path).as_posix()],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    if not value:
        raise SystemExit(f"No Git revision history found for public source: {relative(path)}")
    return int(value)


def localized_revision_date(timestamp: int) -> str:
    """Format a stable English calendar date for Material's source footer."""
    rendered = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%B %d, %Y")
    return rendered.replace(" 0", " ")


def is_approved_markdown(path: Path) -> bool:
    rel = relative(path)
    if rel in PUBLIC_ROOT_PAGES:
        return True
    return len(rel.parts) > 1 and rel.parts[0] in PUBLIC_DIRECTORIES


def discover_public_markdown() -> list[Path]:
    marked: list[Path] = []
    for path in ROOT.rglob("*.md"):
        rel = relative(path)
        if rel.parts[0] in {".git", ".site-build"}:
            continue
        if has_public_level(path):
            marked.append(path)

    unexpected = sorted(relative(path).as_posix() for path in marked if not is_approved_markdown(path))
    if unexpected:
        rendered = "\n".join(f"  - {item}" for item in unexpected)
        raise SystemExit(
            "Files marked public-proposal fall outside the website path allowlist. "
            "Review the publication policy before building:\n" + rendered
        )

    selected = sorted((path for path in marked if is_approved_markdown(path)), key=relative)
    missing = sorted(
        path.as_posix()
        for path in PUBLIC_ROOT_PAGES
        if ROOT / path not in selected
    )
    if missing:
        raise SystemExit("Required public root pages are missing public-proposal metadata: " + ", ".join(missing))
    return selected


def staged_markdown_path(source: Path) -> Path:
    rel = relative(source)
    if rel.name == "README.md":
        rel = rel.with_name("index.md")
    return DOCS_ROOT / rel


def split_link_target(raw: str) -> tuple[str, str]:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        end = value.index(">")
        return value[1:end], value[end + 1 :]
    parts = value.split(maxsplit=1)
    return parts[0], (" " + parts[1]) if len(parts) == 2 else ""


def path_and_fragment(target: str) -> tuple[str, str]:
    path, separator, fragment = target.partition("#")
    return path, (separator + fragment) if separator else ""


def staged_relative_link(source_stage: Path, target_stage: Path) -> str:
    return os.path.relpath(target_stage, source_stage.parent).replace(os.sep, "/")


def rewrite_markdown(
    source: Path,
    text: str,
    markdown_map: dict[Path, Path],
    support_map: dict[Path, Path],
    demoted_links: list[dict[str, str]],
) -> str:
    source_stage = markdown_map[source.resolve()]

    def replace(match: re.Match[str]) -> str:
        label = match.group("label")
        target_raw, title_suffix = split_link_target(match.group("target"))
        path_text, fragment = path_and_fragment(target_raw)
        canonical_target = (source.parent / path_text).resolve()

        if canonical_target in markdown_map:
            href = staged_relative_link(source_stage, markdown_map[canonical_target]) + fragment
            return f"{match.group('image')}[{label}]({href}{title_suffix})"
        if canonical_target in support_map:
            href = staged_relative_link(source_stage, support_map[canonical_target]) + fragment
            return f"{match.group('image')}[{label}]({href}{title_suffix})"

        demoted_links.append(
            {
                "source": relative(source).as_posix(),
                "target": target_raw,
                "label": label,
            }
        )
        return label

    return LOCAL_LINK.sub(replace, text)


def ordered_areas() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for line in (ROOT / "areas" / "README.md").read_text(encoding="utf-8").splitlines():
        match = AREA_LINK.match(line.strip())
        if match:
            area_id, code, title, linked_code = match.groups()
            if code != linked_code:
                raise SystemExit(f"Area navigation code mismatch: {line}")
            rows.append((area_id, code, title))
    if not rows:
        raise SystemExit("No project areas were found in areas/README.md")
    return rows


def legislation_sort_key(path: Path) -> tuple[str, int, str]:
    match = LEGISLATION_NAME.match(path.stem)
    if not match:
        return path.stem, 9, ""
    issue_id, suffix = match.groups()
    rank = {"amendment": 0, "preferred": 1, None: 2, "state": 3}.get(suffix, 4)
    return issue_id, rank, suffix or ""


def write_legislation_index(legislation: list[Path], areas: list[tuple[str, str, str]]) -> Path:
    destination = DOCS_ROOT / "legislation" / "index.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    area_titles = {code: title for _area_id, code, title in areas}
    grouped: dict[str, list[Path]] = defaultdict(list)
    for path in legislation:
        grouped[path.stem.split("-", 1)[0]].append(path)

    area_order = [code for _area_id, code, _title in areas]
    group_order = [code for code in area_order if code in grouped]
    group_order.extend(sorted(code for code in grouped if code not in set(group_order)))

    lines = [
        "---",
        'title: "Proposed Legislation"',
        f'git_revision_date_localized: "{localized_revision_date(max(git_revision_timestamp(path) for path in legislation))}"',
        "---",
        "",
        "# Proposed Legislation",
        "",
        "These are illustrative working drafts associated with developed ARRP issue pages. They have not been reviewed or approved by legislative counsel and should not be treated as ready-to-introduce text.",
        "",
    ]
    for code in group_order:
        lines.extend([f"## {code} — {area_titles.get(code, code)}", ""])
        for path in sorted(grouped[code], key=legislation_sort_key):
            label = f"{path.stem} — {page_title(path)}"
            lines.append(f"- [{label}]({path.name})")
        lines.append("")
    destination.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return destination


def yaml_label(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def generate_navigation(
    public_markdown: list[Path],
    areas: list[tuple[str, str, str]],
    legislation_index: Path,
) -> str:
    by_relative = {relative(path): path for path in public_markdown}
    lines = [
        "nav:",
        f"  - {yaml_label('Home')}: index.md",
    ]

    topic_pages = sorted(
        (
            path
            for path in public_markdown
            if relative(path).parts[0] == "topics"
        ),
        key=lambda path: page_title(path).casefold(),
    )
    if topic_pages:
        lines.append(f"  - {yaml_label('Topics')}:")
        topic_overview = by_relative.get(Path("topics") / "README.md")
        if topic_overview is not None:
            lines.append(f"      - {yaml_label('Overview')}: topics/index.md")
        for path in topic_pages:
            if path == topic_overview:
                continue
            lines.append(
                f"      - {yaml_label(page_title(path))}: "
                f"{staged_markdown_path(path).relative_to(DOCS_ROOT).as_posix()}"
            )

    lines.extend(
        [
            f"  - {yaml_label('Subject and Institution Index')}: SUBJECT_INDEX.md",
            f"  - {yaml_label('Project Areas')}: ",
            f"      - {yaml_label('Overview')}: areas/index.md",
        ]
    )

    for area_id, code, area_title in areas:
        area_source = Path("areas") / code / "README.md"
        if area_source not in by_relative:
            continue
        label = f"{area_id} / {code} — {area_title}"
        lines.append(f"      - {yaml_label(label)}:")
        lines.append(f"          - {yaml_label('Overview')}: areas/{code}/index.md")
        issue_dir = ROOT / "areas" / code / "issues"
        issue_pages = sorted(
            (
                path
                for path in public_markdown
                if path.parent == issue_dir and path.suffix == ".md"
            ),
            key=lambda path: path.stem,
        )
        for issue in issue_pages:
            issue_label = f"{issue.stem} — {page_title(issue)}"
            lines.append(
                f"          - {yaml_label(issue_label)}: "
                f"areas/{code}/issues/{issue.name}"
            )

    legislation = sorted(
        (path for path in public_markdown if relative(path).parts[0] == "legislation"),
        key=legislation_sort_key,
    )
    grouped: dict[str, list[Path]] = defaultdict(list)
    for path in legislation:
        grouped[path.stem.split("-", 1)[0]].append(path)
    area_order = [code for _area_id, code, _title in areas]
    group_order = [code for code in area_order if code in grouped]
    group_order.extend(sorted(code for code in grouped if code not in set(group_order)))

    lines.extend(
        [
            f"  - {yaml_label('Proposed Legislation')}:",
            f"      - {yaml_label('Overview')}: {legislation_index.relative_to(DOCS_ROOT).as_posix()}",
        ]
    )
    for code in group_order:
        lines.append(f"      - {yaml_label(code)}:")
        for path in sorted(grouped[code], key=legislation_sort_key):
            label = f"{path.stem} — {page_title(path)}"
            lines.append(f"          - {yaml_label(label)}: legislation/{path.name}")

    lines.extend(
        [
            f"  - {yaml_label('About')}:",
            f"      - {yaml_label('About the Project')}: ABOUT.md",
            f"      - {yaml_label('Using a Print Edition')}: PRINT_READERS_GUIDE.md",
            f"      - {yaml_label('Technical Record on GitHub')}: https://github.com/Thorncrag/ARRP",
            f"      - {yaml_label('Rights and Reuse')}: LICENSE.md",
            f"  - {yaml_label('Contact')}: https://arrp-public-intake.vercel.app/",
        ]
    )
    return "\n".join(lines) + "\n"


def validate_staged_site() -> None:
    failures: list[str] = []
    for path in DOCS_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(DOCS_ROOT)
        lowered = path.read_text(encoding="utf-8", errors="ignore").lower()
        for term in FORBIDDEN_TERMS:
            if term in lowered:
                failures.append(f"forbidden dashboard reference {term!r} in {rel.as_posix()}")

        if path.suffix != ".md":
            continue
        for match in LOCAL_LINK.finditer(path.read_text(encoding="utf-8")):
            raw, _title = split_link_target(match.group("target"))
            target_text, _fragment = path_and_fragment(raw)
            target = (path.parent / target_text).resolve()
            try:
                target.relative_to(DOCS_ROOT.resolve())
            except ValueError:
                failures.append(f"link escapes staged site in {rel.as_posix()}: {raw}")
                continue
            if not target.exists():
                failures.append(f"missing local target in {rel.as_posix()}: {raw}")

    forbidden_paths = [
        path.relative_to(DOCS_ROOT).as_posix()
        for path in DOCS_ROOT.rglob("*")
        if path.is_file()
        and path.relative_to(DOCS_ROOT).parts[0]
        in {".github", "archive", "exports", "framework", "inventory", "research", "scripts", "sources", "tests"}
    ]
    failures.extend(f"forbidden published path: {path}" for path in forbidden_paths)
    if failures:
        raise SystemExit("Public-site validation failed:\n" + "\n".join(f"  - {item}" for item in failures))


def prepare() -> dict[str, object]:
    public_markdown = discover_public_markdown()
    if BUILD_ROOT.exists():
        shutil.rmtree(BUILD_ROOT)
    DOCS_ROOT.mkdir(parents=True)

    markdown_map = {path.resolve(): staged_markdown_path(path) for path in public_markdown}
    support_map = {
        (ROOT / rel).resolve(): DOCS_ROOT / rel
        for rel in PUBLIC_SUPPORT_FILES
    }
    demoted_links: list[dict[str, str]] = []

    for source in public_markdown:
        destination = markdown_map[source.resolve()]
        destination.parent.mkdir(parents=True, exist_ok=True)
        rewritten = rewrite_markdown(
            source,
            source.read_text(encoding="utf-8"),
            markdown_map,
            support_map,
            demoted_links,
        )
        destination.write_text(rewritten, encoding="utf-8")

    for source, destination in support_map.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    for source_rel, destination_rel in WEBSITE_FILES.items():
        destination = DOCS_ROOT / destination_rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / source_rel, destination)

    areas = ordered_areas()
    legislation = [
        path for path in public_markdown if relative(path).parts[0] == "legislation"
    ]
    legislation_index = write_legislation_index(legislation, areas)

    base_config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8").rstrip()
    generated_config = base_config + "\n\n" + generate_navigation(public_markdown, areas, legislation_index)
    (BUILD_ROOT / "mkdocs.yml").write_text(generated_config, encoding="utf-8")

    validate_staged_site()
    manifest: dict[str, object] = {
        "schemaVersion": 1,
        "printLevel": PUBLIC_LEVEL,
        "canonicalSources": [relative(path).as_posix() for path in public_markdown],
        "generatedPages": [legislation_index.relative_to(DOCS_ROOT).as_posix()],
        "supportFiles": sorted(path.as_posix() for path in PUBLIC_SUPPORT_FILES),
        "demotedLinks": demoted_links,
    }
    (BUILD_ROOT / "public-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    manifest = prepare()
    print(
        "Prepared public site: "
        f"{len(manifest['canonicalSources'])} canonical Markdown pages, "
        f"{len(manifest['generatedPages'])} generated page, and "
        f"{len(manifest['demotedLinks'])} internal links demoted."
    )


if __name__ == "__main__":
    main()
