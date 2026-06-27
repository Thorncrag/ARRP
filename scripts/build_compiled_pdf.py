#!/usr/bin/env python3
"""Build a first-pass compiled ARRP proposal PDF.

The generator follows framework/PRINT_ASSEMBLY.md and intentionally keeps the
format conservative: readable typography, stable ordering, page numbers, and
legislation in appendices.
"""

from __future__ import annotations

import csv
import html
import os
import re
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "pdf"
OUTPUT = EXPORT_DIR / "ARRP-public-proposal-draft.pdf"
OMIT_SECTION_TITLES = {"Framework Issue", "Technical Framework"}
OMIT_LINE_PATTERNS = [
    re.compile(r"framework analysis", re.IGNORECASE),
]


@dataclass(frozen=True)
class Area:
    area_id: str
    title: str
    slug: str


def load_areas() -> list[Area]:
    rows: list[Area] = []
    with (ROOT / "inventory" / "areas.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            area_id = row["Area ID"]
            title = row["Area"]
            slug = find_area_slug(area_id)
            rows.append(Area(area_id=area_id, title=title, slug=slug))
    return rows


def find_area_slug(area_id: str) -> str:
    prefix = area_id.lower()
    matches = sorted((ROOT / "areas").glob(f"{prefix}-*/README.md"))
    if not matches:
        raise FileNotFoundError(f"No area README found for {area_id}")
    return matches[0].parent.name


def load_issue_order() -> dict[str, list[str]]:
    by_area: dict[str, list[str]] = {}
    with (ROOT / "inventory" / "issues.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            by_area.setdefault(row["Area ID"], []).append(row["Issue ID"])
    return by_area


def legislation_files() -> tuple[list[Path], list[Path]]:
    files = sorted((ROOT / "legislation").glob("*.md"))
    files = [p for p in files if p.name != "README.md"]
    state = [p for p in files if p.stem.endswith("-state")]
    federal = [p for p in files if not p.stem.endswith("-state")]
    return federal, state


def strip_front_matter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :].lstrip()
    return text


def escape(text: str) -> str:
    return html.escape(text, quote=False)


def inline_markup(text: str) -> str:
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = escape(text)
    text = text.replace("\n", "<br/>")
    text = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    return text


def printable_code(text: str) -> str:
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"<br\s*/?>", "\n", text)
    return text


def compact_title(line: str) -> str:
    return re.sub(r"^#+\s*", "", line).strip()


def should_omit_line(line: str) -> bool:
    return any(pattern.search(line) for pattern in OMIT_LINE_PATTERNS)


def heading_style(level: int, styles: dict[str, ParagraphStyle]) -> ParagraphStyle:
    if level <= 1:
        return styles["H1"]
    if level == 2:
        return styles["H2"]
    return styles["H3"]


def is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_divider(line: str) -> bool:
    cells = table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def table_column_widths(rows: list[list[str]], total_width: float = 7.06 * inch) -> list[float]:
    column_count = max(len(row) for row in rows)
    weights = [1] * column_count
    for row in rows:
        for index, cell in enumerate(row):
            weights[index] = max(weights[index], min(len(cell), 42))
    total_weight = sum(weights)
    return [total_width * weight / total_weight for weight in weights]


def table_to_flowable(table_lines: list[str], styles: dict[str, ParagraphStyle]) -> Table | None:
    rows = [table_cells(line) for line in table_lines if is_table_line(line) and not is_table_divider(line)]
    if not rows:
        return None
    column_count = max(len(row) for row in rows)
    normalized = []
    for row in rows:
        padded = row + [""] * (column_count - len(row))
        normalized.append([Paragraph(inline_markup(cell), styles["TableCell"]) for cell in padded])
    table = Table(normalized, colWidths=table_column_widths(rows), repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return table


def markdown_to_flowables(
    text: str,
    styles: dict[str, ParagraphStyle],
    *,
    heading_offset: int = 0,
) -> list:
    flow = []
    text = strip_front_matter(text)
    lines = text.splitlines()
    para: list[str] = []
    code: list[str] = []
    quote: list[str] = []
    table: list[str] = []
    in_code = False
    skip_heading_level: int | None = None

    def flush_para() -> None:
        nonlocal para
        if para:
            joined = " ".join(line.strip() for line in para).strip()
            if joined:
                flow.append(Paragraph(inline_markup(joined), styles["Body"]))
            para = []

    def flush_code() -> None:
        nonlocal code
        if code:
            flow.append(Preformatted(printable_code("\n".join(code)), styles["Code"]))
            code = []

    def flush_table() -> None:
        nonlocal table
        if table:
            rendered_table = table_to_flowable(table, styles)
            if rendered_table is not None:
                flow.append(rendered_table)
                flow.append(Spacer(1, 3))
            table = []

    def normalize_quote_line(line: str) -> str:
        line = line.strip()
        line = re.sub(r"^#{1,6}\s+", "", line)
        return line.strip()

    def flush_quote() -> None:
        nonlocal quote
        if quote:
            parts = [inline_markup(line) for line in quote if line.strip()]
            if parts:
                flow.append(Paragraph("<br/>".join(parts), styles["Quote"]))
            quote = []

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            flush_table()
            flush_quote()
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_para()
                in_code = True
            continue
        if in_code:
            if skip_heading_level is not None:
                continue
            code.append(line)
            continue
        if should_omit_line(line):
            flush_para()
            flush_quote()
            flush_table()
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#")) + heading_offset
            title = compact_title(line)
            raw_level = len(line) - len(line.lstrip("#"))
            if skip_heading_level is not None:
                if raw_level > skip_heading_level:
                    continue
                skip_heading_level = None
            if title in OMIT_SECTION_TITLES:
                flush_para()
                flush_quote()
                flush_table()
                skip_heading_level = raw_level
                continue
            flush_para()
            flush_quote()
            flush_table()
            flow.append(Paragraph(inline_markup(title), heading_style(level, styles)))
            continue
        if skip_heading_level is not None:
            continue
        if not line.strip():
            flush_para()
            flush_quote()
            flush_table()
            continue
        if line.startswith(">"):
            flush_para()
            flush_table()
            cleaned = normalize_quote_line(line.lstrip("> "))
            if cleaned:
                quote.append(cleaned)
            continue
        if re.match(r"^\s*[-*]\s+", line):
            flush_para()
            flush_quote()
            flush_table()
            item = re.sub(r"^\s*[-*]\s+", "", line)
            flow.append(Paragraph(f"- {inline_markup(item)}", styles["Bullet"]))
            continue
        if re.match(r"^\s*\d+\.\s+", line):
            flush_para()
            flush_quote()
            flush_table()
            flow.append(Paragraph(inline_markup(line.strip()), styles["Bullet"]))
            continue
        if is_table_line(line):
            flush_para()
            flush_quote()
            table.append(line)
            continue
        flush_table()
        flush_quote()
        para.append(line)

    flush_para()
    flush_quote()
    flush_table()
    flush_code()
    return flow


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}
    styles["Title"] = ParagraphStyle(
        "ARRPTitle",
        parent=base["Title"],
        fontName="Times-Bold",
        fontSize=20,
        leading=23,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    styles["Subtitle"] = ParagraphStyle(
        "ARRPSubtitle",
        parent=base["BodyText"],
        fontName="Times-Italic",
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        spaceAfter=16,
    )
    styles["H1"] = ParagraphStyle(
        "ARRPH1",
        parent=base["Heading1"],
        fontName="Times-Bold",
        fontSize=15,
        leading=17,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    styles["H2"] = ParagraphStyle(
        "ARRPH2",
        parent=base["Heading2"],
        fontName="Times-Bold",
        fontSize=12.5,
        leading=14.5,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    )
    styles["H3"] = ParagraphStyle(
        "ARRPH3",
        parent=base["Heading3"],
        fontName="Times-BoldItalic",
        fontSize=10.5,
        leading=12.5,
        spaceBefore=5,
        spaceAfter=2,
        keepWithNext=True,
    )
    styles["Body"] = ParagraphStyle(
        "ARRPBody",
        parent=base["BodyText"],
        fontName="Times-Roman",
        fontSize=9,
        leading=10.6,
        alignment=TA_LEFT,
        spaceAfter=1.4,
    )
    styles["Bullet"] = ParagraphStyle(
        "ARRPBullet",
        parent=styles["Body"],
        leftIndent=0.18 * inch,
        firstLineIndent=-0.12 * inch,
    )
    styles["Quote"] = ParagraphStyle(
        "ARRPQuote",
        parent=styles["Body"],
        leftIndent=0.16 * inch,
        rightIndent=0.08 * inch,
        borderColor=colors.lightgrey,
        borderWidth=0.5,
        borderPadding=3,
        backColor=colors.whitesmoke,
        spaceBefore=2,
        spaceAfter=3,
    )
    styles["TableCell"] = ParagraphStyle(
        "ARRPTableCell",
        parent=styles["Body"],
        fontSize=7.4,
        leading=8.4,
        spaceAfter=0,
    )
    styles["Code"] = ParagraphStyle(
        "ARRPCode",
        parent=base["Code"],
        fontName="Courier",
        fontSize=6.5,
        leading=7.4,
        leftIndent=0.06 * inch,
        rightIndent=0.06 * inch,
        spaceBefore=2,
        spaceAfter=3,
    )
    styles["Footer"] = ParagraphStyle(
        "ARRPFooter",
        parent=base["BodyText"],
        fontName="Times-Roman",
        fontSize=8,
        textColor=colors.grey,
    )
    return styles


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def toc_entries(areas: list[Area], issue_order: dict[str, list[str]]) -> list[str]:
    entries = ["Front Matter", "Foundational Premise, Mission, Scope, and Governing Principles"]
    for area in areas:
        entries.append(f"{area.area_id} - {area.title}")
        for issue_id in issue_order.get(area.area_id, []):
            issue_path = ROOT / "areas" / area.slug / "issues" / f"{issue_id}.md"
            if issue_path.exists():
                entries.append(f"  {issue_id}")
    entries.extend(
        [
            "Appendix A - Proposed Federal Legislation and Constitutional Amendments",
            "Appendix B - Model State Legislation",
        ]
    )
    return entries


def build_story(styles: dict[str, ParagraphStyle]) -> list:
    areas = load_areas()
    issue_order = load_issue_order()
    federal_bills, state_bills = legislation_files()
    story = []

    story.append(Paragraph("American Restoration and Resilience Project", styles["Title"]))
    story.append(
        Paragraph(
            "A Roadmap for Repairing Institutional Damage, Restoring Trustworthy Government, and Preventing Future Personalist Capture",
            styles["Subtitle"],
        )
    )
    story.append(Paragraph("Public Proposal Draft", styles["H2"]))
    story.append(Paragraph("Generated from canonical Markdown sources.", styles["Body"]))
    story.append(PageBreak())

    story.append(Paragraph("Table of Contents", styles["H1"]))
    for entry in toc_entries(areas, issue_order):
        story.append(Paragraph(inline_markup(entry), styles["Body"]))
    story.append(PageBreak())

    story.extend(markdown_to_flowables(read(ROOT / "README.md"), styles, heading_offset=0))
    story.append(PageBreak())

    story.append(Paragraph("Project Areas and Issues", styles["H1"]))
    for area in areas:
        area_readme = ROOT / "areas" / area.slug / "README.md"
        story.append(PageBreak())
        story.extend(markdown_to_flowables(read(area_readme), styles, heading_offset=0))
        for issue_id in issue_order.get(area.area_id, []):
            issue_path = ROOT / "areas" / area.slug / "issues" / f"{issue_id}.md"
            if issue_path.exists():
                story.append(PageBreak())
                story.extend(markdown_to_flowables(read(issue_path), styles, heading_offset=0))

    story.append(PageBreak())
    story.append(Paragraph("Appendix A - Proposed Federal Legislation and Constitutional Amendments", styles["H1"]))
    for path in federal_bills:
        story.append(PageBreak())
        story.extend(markdown_to_flowables(read(path), styles, heading_offset=0))

    story.append(PageBreak())
    story.append(Paragraph("Appendix B - Model State Legislation", styles["H1"]))
    for path in state_bills:
        story.append(PageBreak())
        story.extend(markdown_to_flowables(read(path), styles, heading_offset=0))

    return story


def draw_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(0.72 * inch, 0.45 * inch, "American Restoration and Resilience Project")
    canvas.drawRightString(7.78 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    styles = make_styles()
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
        title="American Restoration and Resilience Project - Public Proposal Draft",
        author="Benjamin Smith",
    )
    doc.build(build_story(styles), onFirstPage=draw_footer, onLaterPages=draw_footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
