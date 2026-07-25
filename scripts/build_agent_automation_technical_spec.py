#!/usr/bin/env python3
"""Build the non-authoritative ARRP automation technical-reference PDF."""

from __future__ import annotations

import argparse
import html
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    ListFlowable,
    ListItem,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/reference-products/agent-automation-technical-spec.md"
OUTPUT = ROOT / "exports/pdf/ARRP-agent-automation-technical-spec.pdf"
GITHUB_BLOB = "https://github.com/Thorncrag/ARRP/blob/main/"

NAVY = colors.HexColor("#102A43")
BLUE = colors.HexColor("#1769AA")
SKY = colors.HexColor("#DCEFFC")
INK = colors.HexColor("#1B2633")
MUTED = colors.HexColor("#5D6B78")
LINE = colors.HexColor("#CBD5DF")
SOFT = colors.HexColor("#F3F6F9")
GOLD = colors.HexColor("#B67812")
GOLD_SOFT = colors.HexColor("#FFF3D6")
GREEN = colors.HexColor("#247A52")
GREEN_SOFT = colors.HexColor("#E1F3E9")
RED = colors.HexColor("#A43D3D")
RED_SOFT = colors.HexColor("#FBE7E7")
WHITE = colors.white


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument(
        "--baseline",
        help="Implementation revision shown in the generated reference.",
    )
    return parser.parse_args()


def current_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def reference_metadata(text: str) -> tuple[str, str, str]:
    """Return the version, ISO date, and display date from source front matter."""
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---":
        raise ValueError("technical reference is missing YAML front matter")
    closing_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.rstrip() == "---"
        ),
        None,
    )
    if closing_index is None:
        raise ValueError("technical reference is missing YAML front matter")
    values: dict[str, str] = {}
    for raw_line in lines[1:closing_index]:
        key, separator, value = raw_line.partition(":")
        if separator:
            values[key.strip()] = value.strip().strip("\"'")
    version = values.get("version", "")
    as_of = values.get("as_of", "")
    if not version or not as_of:
        raise ValueError("technical reference front matter requires version and as_of")
    parsed_date = date.fromisoformat(as_of)
    display_date = f"{parsed_date.strftime('%B')} {parsed_date.day}, {parsed_date.year}"
    return version, as_of, display_date


def register_fonts() -> tuple[str, str, str, str]:
    candidates = [
        (
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Italic.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"),
        ),
        (
            Path("/System/Library/Fonts/Supplemental/Helvetica.ttf"),
            Path("/System/Library/Fonts/Supplemental/Helvetica Bold.ttf"),
            Path("/System/Library/Fonts/Supplemental/Helvetica Oblique.ttf"),
            Path("/System/Library/Fonts/Supplemental/Helvetica Bold Oblique.ttf"),
        ),
    ]
    for regular, bold, italic, bold_italic in candidates:
        if all(path.is_file() for path in (regular, bold, italic, bold_italic)):
            pdfmetrics.registerFont(TTFont("ARRPSans", str(regular)))
            pdfmetrics.registerFont(TTFont("ARRPSans-Bold", str(bold)))
            pdfmetrics.registerFont(TTFont("ARRPSans-Italic", str(italic)))
            pdfmetrics.registerFont(TTFont("ARRPSans-BoldItalic", str(bold_italic)))
            pdfmetrics.registerFontFamily(
                "ARRPSans",
                normal="ARRPSans",
                bold="ARRPSans-Bold",
                italic="ARRPSans-Italic",
                boldItalic="ARRPSans-BoldItalic",
            )
            return (
                "ARRPSans",
                "ARRPSans-Bold",
                "ARRPSans-Italic",
                "ARRPSans-BoldItalic",
            )
    return ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique")


REGULAR_FONT, BOLD_FONT, ITALIC_FONT, BOLD_ITALIC_FONT = register_fonts()


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontName=BOLD_FONT,
            fontSize=30,
            leading=33,
            textColor=WHITE,
            alignment=TA_LEFT,
            spaceAfter=14,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName=REGULAR_FONT,
            fontSize=15,
            leading=20,
            textColor=colors.HexColor("#D9EAF7"),
            spaceAfter=20,
        ),
        "CoverMeta": ParagraphStyle(
            "CoverMeta",
            parent=base["Normal"],
            fontName=REGULAR_FONT,
            fontSize=9,
            leading=13,
            textColor=MUTED,
        ),
        "Disclaimer": ParagraphStyle(
            "Disclaimer",
            parent=base["Normal"],
            fontName=BOLD_FONT,
            fontSize=10,
            leading=14,
            textColor=RED,
            alignment=TA_CENTER,
        ),
        "Heading1": ParagraphStyle(
            "Heading1",
            parent=base["Heading1"],
            fontName=BOLD_FONT,
            fontSize=19,
            leading=23,
            textColor=NAVY,
            spaceBefore=11,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName=BOLD_FONT,
            fontSize=14,
            leading=18,
            textColor=BLUE,
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "Heading3": ParagraphStyle(
            "Heading3",
            parent=base["Heading3"],
            fontName=BOLD_FONT,
            fontSize=11.3,
            leading=14,
            textColor=INK,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName=REGULAR_FONT,
            fontSize=9.2,
            leading=13.2,
            textColor=INK,
            spaceAfter=6,
            splitLongWords=False,
        ),
        "BodySmall": ParagraphStyle(
            "BodySmall",
            parent=base["BodyText"],
            fontName=REGULAR_FONT,
            fontSize=7.7,
            leading=10.2,
            textColor=INK,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName=REGULAR_FONT,
            fontSize=9,
            leading=12.6,
            textColor=INK,
            leftIndent=4,
            firstLineIndent=0,
            spaceAfter=2,
        ),
        "TOCTitle": ParagraphStyle(
            "TOCTitle",
            parent=base["Heading1"],
            fontName=BOLD_FONT,
            fontSize=21,
            leading=25,
            textColor=NAVY,
            spaceAfter=12,
        ),
        "TOC0": ParagraphStyle(
            "TOC0",
            parent=base["Normal"],
            fontName=BOLD_FONT,
            fontSize=9.2,
            leading=13,
            leftIndent=0,
            firstLineIndent=0,
            textColor=NAVY,
            spaceBefore=2,
        ),
        "TOC1": ParagraphStyle(
            "TOC1",
            parent=base["Normal"],
            fontName=REGULAR_FONT,
            fontSize=8.3,
            leading=11,
            leftIndent=15,
            firstLineIndent=0,
            textColor=INK,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName=BOLD_FONT,
            fontSize=7.2,
            leading=9,
            textColor=WHITE,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName=REGULAR_FONT,
            fontSize=7.1,
            leading=9.2,
            textColor=INK,
        ),
        "DiagramTitle": ParagraphStyle(
            "DiagramTitle",
            parent=base["Normal"],
            fontName=BOLD_FONT,
            fontSize=9.5,
            leading=12,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "Caption": ParagraphStyle(
            "Caption",
            parent=base["Normal"],
            fontName=ITALIC_FONT,
            fontSize=7.5,
            leading=10,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=7,
        ),
    }


def strip_front_matter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    return text[end + 5 :] if end >= 0 else text


def github_href(raw: str, source: Path) -> str:
    target = raw.strip()
    if target.startswith(("https://", "http://", "mailto:")):
        return target
    if target.startswith("#"):
        return target
    resolved = (source.parent / target.split("#", 1)[0]).resolve()
    try:
        relative = resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return target
    fragment = "#" + target.split("#", 1)[1] if "#" in target else ""
    return GITHUB_BLOB + relative + fragment


def inline_markup(text: str, source: Path) -> str:
    placeholders: list[str] = []

    def hold(value: str) -> str:
        placeholders.append(value)
        return f"@@ARRP{len(placeholders) - 1}@@"

    rendered: list[str] = []
    cursor = 0
    while cursor < len(text):
        opening = text.find("[", cursor)
        if opening < 0:
            rendered.append(text[cursor:])
            break
        label_end = text.find("]", opening + 1)
        if label_end < 0:
            rendered.append(text[cursor:])
            break
        if label_end + 1 >= len(text) or text[label_end + 1] != "(":
            rendered.append(text[cursor : label_end + 1])
            cursor = label_end + 1
            continue
        target_end = text.find(")", label_end + 2)
        if target_end < 0:
            rendered.append(text[cursor:])
            break
        label = text[opening + 1 : label_end]
        target = text[label_end + 2 : target_end]
        if not label or not target:
            rendered.append(text[cursor : target_end + 1])
            cursor = target_end + 1
            continue
        rendered.append(text[cursor:opening])
        rendered.append(
            hold(
                "<link href='"
                + html.escape(github_href(target, source), quote=True)
                + "' color='#1769AA'>"
                + html.escape(label, quote=False)
                + "</link>"
            )
        )
        cursor = target_end + 1
    text = "".join(rendered)
    text = re.sub(
        r"`([^`]+)`",
        lambda match: hold(
            "<font name='Courier' color='#324A5F'>"
            + html.escape(match.group(1), quote=False)
            + "</font>"
        ),
        text,
    )
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    for index, value in enumerate(placeholders):
        text = text.replace(f"@@ARRP{index}@@", value)
    return text


def heading_parts(line: str) -> tuple[int, str] | None:
    """Parse one ATX heading without a backtracking expression."""
    marker_count = 0
    while marker_count < len(line) and line[marker_count] == "#":
        marker_count += 1
    if not 1 <= marker_count <= 6 or marker_count >= len(line):
        return None
    if not line[marker_count].isspace():
        return None
    title = line[marker_count:].lstrip()
    return (marker_count, title) if title else None


def list_line_parts(line: str) -> tuple[str, str, str] | None:
    """Parse one Markdown list line in a single forward pass."""
    marker_start = 0
    while marker_start < len(line) and line[marker_start].isspace():
        marker_start += 1
    if marker_start >= len(line):
        return None

    marker_end = marker_start
    if line[marker_start] in "-*":
        marker_end += 1
    elif line[marker_start].isdecimal():
        while marker_end < len(line) and line[marker_end].isdecimal():
            marker_end += 1
        if marker_end >= len(line) or line[marker_end] != ".":
            return None
        marker_end += 1
    else:
        return None

    if marker_end >= len(line) or not line[marker_end].isspace():
        return None
    content_start = marker_end
    while content_start < len(line) and line[content_start].isspace():
        content_start += 1
    if content_start >= len(line):
        return None
    return line[:marker_start], line[marker_start:marker_end], line[content_start:]


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_divider(line: str) -> bool:
    cells = table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def column_widths(rows: list[list[str]], total: float) -> list[float]:
    count = max(len(row) for row in rows)
    maxima = []
    for index in range(count):
        maximum = max(
            len(re.sub(r"[*`\[\]()]", "", row[index])) if index < len(row) else 0
            for row in rows
        )
        maxima.append(max(8, min(maximum, 42)))
    if count == 2:
        maxima = [min(maxima[0], 24), max(maxima[1], 34)]
    floor = total * (0.14 if count <= 4 else 0.10)
    raw = [total * value / sum(maxima) for value in maxima]
    widths = [max(floor, width) for width in raw]
    scale = total / sum(widths)
    return [width * scale for width in widths]


def make_table(
    rows: list[list[str]],
    styles: dict[str, ParagraphStyle],
    source: Path,
    available_width: float,
) -> LongTable:
    count = max(len(row) for row in rows)
    normalized = [row + [""] * (count - len(row)) for row in rows]
    data = []
    for row_index, row in enumerate(normalized):
        style = styles["TableHeader"] if row_index == 0 else styles["TableCell"]
        data.append([Paragraph(inline_markup(cell, source), style) for cell in row])
    table = LongTable(
        data,
        colWidths=column_widths(normalized, available_width),
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SOFT]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


class Diagram(Flowable):
    """Compact vector architecture diagram."""

    TITLES = {
        "system-context": "System context and trust boundaries",
        "run-chain": "Due-aware persistent run chain",
        "execution-boundary": "Cloud, repository, and host execution boundary",
        "failure-state": "Deterministic stage outcomes and separate blocking state",
        "queue-selection": "Derived queue to exact selected unit",
        "context-routing": "Context profile and dependency expansion",
        "write-boundaries": "Three write classes and Elim split-closeout",
        "provenance": "Material-unit provenance destinations",
        "handoff-lifecycle": "Audit handoff ownership through an Elim run",
    }

    def __init__(self, kind: str, width: float):
        super().__init__()
        self.kind = kind
        self.width = width
        self.height = {
            "system-context": 245,
            "run-chain": 305,
            "execution-boundary": 240,
            "failure-state": 230,
            "queue-selection": 225,
            "context-routing": 230,
            "write-boundaries": 235,
            "provenance": 235,
            "handoff-lifecycle": 290,
        }[kind]

    def wrap(self, avail_width, avail_height):
        self.draw_width = min(self.width, avail_width)
        return self.draw_width, self.height

    def box(
        self,
        canvas,
        x: float,
        y: float,
        width: float,
        height: float,
        title: str,
        body: str = "",
        *,
        fill=SOFT,
        stroke=LINE,
        title_color=NAVY,
        radius=7,
    ) -> None:
        canvas.setFillColor(fill)
        canvas.setStrokeColor(stroke)
        canvas.setLineWidth(0.8)
        canvas.roundRect(x, y, width, height, radius, fill=1, stroke=1)
        canvas.setFillColor(title_color)
        canvas.setFont(BOLD_FONT, 8.2)
        self.centered_lines(canvas, title, x + width / 2, y + height - 14, width - 10, 8.2)
        if body:
            canvas.setFillColor(INK)
            canvas.setFont(REGULAR_FONT, 6.7)
            self.centered_lines(canvas, body, x + width / 2, y + height - 33, width - 10, 6.7)

    @staticmethod
    def centered_lines(canvas, text, center_x, top_y, max_width, font_size):
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if canvas.stringWidth(candidate, canvas._fontname, font_size) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        leading = font_size + 2
        for index, line in enumerate(lines[:4]):
            canvas.drawCentredString(center_x, top_y - index * leading, line)

    @staticmethod
    def arrow(canvas, x1, y1, x2, y2, *, color=BLUE, dashed=False):
        canvas.saveState()
        canvas.setStrokeColor(color)
        canvas.setFillColor(color)
        canvas.setLineWidth(1.2)
        if dashed:
            canvas.setDash(3, 2)
        canvas.line(x1, y1, x2, y2)
        angle = 5
        if abs(x2 - x1) >= abs(y2 - y1):
            direction = 1 if x2 >= x1 else -1
            canvas.line(x2, y2, x2 - direction * angle, y2 + 3)
            canvas.line(x2, y2, x2 - direction * angle, y2 - 3)
        else:
            direction = 1 if y2 >= y1 else -1
            canvas.line(x2, y2, x2 + 3, y2 - direction * angle)
            canvas.line(x2, y2, x2 - 3, y2 - direction * angle)
        canvas.restoreState()

    def label(self, canvas, text, x, y, *, color=MUTED, size=6.5):
        canvas.setFillColor(color)
        canvas.setFont(REGULAR_FONT, size)
        canvas.drawCentredString(x, y, text)

    def draw(self):
        canvas = self.canv
        width = getattr(self, "draw_width", self.width)
        canvas.saveState()
        canvas.setFillColor(WHITE)
        canvas.setStrokeColor(LINE)
        canvas.roundRect(0, 0, width, self.height - 8, 9, fill=1, stroke=1)
        canvas.setFillColor(NAVY)
        canvas.setFont(BOLD_FONT, 10)
        canvas.drawCentredString(width / 2, self.height - 25, self.TITLES[self.kind])
        getattr(self, f"draw_{self.kind.replace('-', '_')}")(canvas, width)
        canvas.restoreState()

    def draw_system_context(self, canvas, width):
        center_w, center_h = 148, 55
        cx = (width - center_w) / 2
        cy = 92
        self.box(
            canvas, cx, cy, center_w, center_h,
            "Run Coordinator", "serializes, binds, and gates",
            fill=SKY, stroke=BLUE,
        )
        boxes = [
            (18, 138, 148, 58, "GitHub Actions", "deterministic chain and projections"),
            (width - 166, 138, 148, 58, "Canonical GitHub", "records, Project, PR review"),
            (18, 40, 148, 58, "Local macOS host", "lease, usage, Codex, workspace"),
            (width - 166, 40, 148, 58, "Interfaces and public intake", "derived views and bounded requests"),
        ]
        for x, y, w, h, title, body in boxes:
            self.box(canvas, x, y, w, h, title, body)
            self.arrow(
                canvas,
                x + w if x < width / 2 else x,
                y + h / 2,
                cx if x < width / 2 else cx + center_w,
                cy + center_h / 2,
                dashed=True,
            )
        self.label(canvas, "External providers are bounded, untrusted inputs.", width / 2, 18)

    def draw_run_chain(self, canvas, width):
        labels = [
            ("Plan", "trigger + due"),
            ("Cases", "24 h"),
            ("Directives", "24 h"),
            ("Sources", "168 h"),
            ("Progress", "24 h"),
            ("Intake", "always"),
            ("Integrity", "always"),
            ("Queue", "select one"),
            ("Usage", "host gate"),
            ("Elim", "conditional"),
            ("Host Git", "exact diff"),
            ("Close", "read back"),
        ]
        x = 24
        box_w = (width - 78) / 2
        box_h = 32
        gap_y = 8
        positions = []
        for index, (title, body) in enumerate(labels):
            col = index % 2
            row = index // 2
            actual_col = col if row % 2 == 0 else 1 - col
            bx = x + actual_col * (box_w + 30)
            by = 232 - row * (box_h + gap_y)
            positions.append((bx, by))
            fill = GOLD_SOFT if title in {"Elim", "Host Git"} else SKY if title in {"Plan", "Queue", "Usage", "Close"} else SOFT
            stroke = GOLD if title in {"Elim", "Host Git"} else BLUE if title in {"Plan", "Queue", "Usage", "Close"} else LINE
            self.box(canvas, bx, by, box_w, box_h, title, body, fill=fill, stroke=stroke)
            if index:
                px, py = positions[index - 1]
                if abs(px - bx) > 1:
                    start_x = px + box_w if bx > px else px
                    end_x = bx if bx > px else bx + box_w
                    self.arrow(canvas, start_x, py + box_h / 2, end_x, by + box_h / 2)
                else:
                    self.arrow(canvas, px + box_w / 2, py, bx + box_w / 2, by + box_h)
        self.label(canvas, "Elim authors files; trusted-host Git and Close add no judgment.", width / 2, 13)

    def draw_execution_boundary(self, canvas, width):
        lane_w = (width - 52) / 3
        lanes = [
            (14, "GitHub Actions", "plan · bots · queue · context", SKY, BLUE),
            (26 + lane_w, "Canonical GitHub", "records · Project · PRs · data", SOFT, LINE),
            (38 + lane_w * 2, "Local host", "flock · usage · Elim files · trusted Git", GOLD_SOFT, GOLD),
        ]
        for x, title, body, fill, stroke in lanes:
            self.box(canvas, x, 56, lane_w, 118, title, body, fill=fill, stroke=stroke)
        self.arrow(canvas, 14 + lane_w, 115, 26 + lane_w, 115)
        self.arrow(canvas, 26 + lane_w * 2, 115, 38 + lane_w * 2, 115)
        self.arrow(canvas, 38 + lane_w * 2, 82, 26 + lane_w * 2, 82, dashed=True)
        self.label(canvas, "verified manifest + hashes", 26 + lane_w, 126)
        self.label(canvas, "matching reviewed revision", 38 + lane_w * 2, 126)
        self.label(canvas, "exact commit + host outcome evidence", 26 + lane_w * 2, 69)
        self.box(
            canvas, width / 2 - 118, 15, 236, 27,
            "Trust rule", "GitHub never launches Codex; the host never creates authority.",
            fill=RED_SOFT, stroke=RED, title_color=RED,
        )

    def draw_failure_state(self, canvas, width):
        root_w = 160
        root_x = width / 2 - root_w / 2
        self.box(
            canvas,
            root_x,
            160,
            root_w,
            36,
            "Deterministic stage evaluated",
            "apply due predicate",
            fill=SKY,
            stroke=BLUE,
        )
        self.box(
            canvas,
            18,
            104,
            105,
            38,
            "not_due",
            "continue",
            fill=GREEN_SOFT,
            stroke=GREEN,
            title_color=GREEN,
        )
        self.box(
            canvas,
            width / 2 - 72,
            104,
            144,
            38,
            "Stage attempted",
            "validate output",
            fill=SKY,
            stroke=BLUE,
        )
        scope_x = width - 164
        self.box(
            canvas,
            scope_x,
            104,
            146,
            38,
            "Chain / host / work / Elim",
            "prerequisite scope",
            fill=SOFT,
            stroke=LINE,
        )
        self.arrow(canvas, width / 2, 160, 70.5, 142, color=GREEN)
        self.arrow(canvas, width / 2, 160, width / 2, 142)

        outcome_w = 100
        outcome_gap = 10
        outcome_start = 18
        outcomes = [
            ("completed", "continue", GREEN_SOFT, GREEN),
            ("degraded", "restrict", GOLD_SOFT, GOLD),
            ("failed", "stop + route", RED_SOFT, RED),
        ]
        attempt_center = width / 2
        for index, (label, body, fill, stroke) in enumerate(outcomes):
            x = outcome_start + index * (outcome_w + outcome_gap)
            self.box(
                canvas,
                x,
                38,
                outcome_w,
                40,
                label,
                body,
                fill=fill,
                stroke=stroke,
                title_color=stroke,
            )
            self.arrow(canvas, attempt_center, 104, x + outcome_w / 2, 78, color=stroke)
        self.box(
            canvas,
            scope_x,
            38,
            146,
            40,
            "blocked",
            "preserve exact blocker",
            fill=RED_SOFT,
            stroke=RED,
            title_color=RED,
        )
        self.arrow(canvas, scope_x + 73, 104, scope_x + 73, 78, color=RED)
        self.label(
            canvas,
            "A deterministic stage never synthesizes blocked.",
            width / 2,
            17,
            color=RED,
            size=7,
        )

    def draw_queue_selection(self, canvas, width):
        items = [
            ("Failure", "1000"),
            ("Integrity error", "900"),
            ("Integrity warning", "800"),
            ("Change Audit", "700"),
            ("Issue audit", "600"),
            ("Intake", "500"),
            ("Development / candidate", "300 + age"),
        ]
        left = 18
        row_h = 20
        for index, (name, score) in enumerate(items):
            y = 172 - index * 22
            item_w = 180 - index * 10
            self.box(canvas, left + index * 5, y, item_w, row_h, name, score, fill=SOFT, stroke=LINE)
            self.arrow(canvas, left + item_w + index * 5, y + row_h / 2, width - 176, 106, dashed=True)
        self.box(
            canvas, width - 166, 77, 148, 58,
            "Exact selected unit", "identity + authority + route + revision",
            fill=SKY, stroke=BLUE,
        )
        self.box(
            canvas, width - 166, 18, 148, 36,
            "Comprehensive due?", "override ordinary score",
            fill=GOLD_SOFT, stroke=GOLD,
        )
        self.arrow(canvas, width - 92, 54, width - 92, 77, color=GOLD)

    def draw_context_routing(self, canvas, width):
        parts = [
            (16, 130, 112, 48, "Mandatory floor", "Framework · Rules · Handoff"),
            (144, 130, 112, 48, "Profile", "issue · audit · intake · epoch"),
            (272, 130, 112, 48, "Capabilities", "routed modules"),
            (400, 130, 112, 48, "Exact records", "issue · sources · Project"),
        ]
        scale = min(1, (width - 32) / 512)
        for x, y, w, h, title, body in parts:
            self.box(canvas, x * scale, y, w * scale, h, title, body)
            self.arrow(canvas, (x + w / 2) * scale, y, width / 2, 93, dashed=True)
        self.box(
            canvas, width / 2 - 110, 52, 220, 42,
            "Dependency closure + pin/hash/size checks", "",
            fill=SKY, stroke=BLUE,
        )
        self.arrow(canvas, width / 2, 52, width / 2, 38)
        self.box(
            canvas, width / 2 - 95, 8, 190, 30,
            "Bound context packet", "nonauthoritative exact-source projection",
            fill=GREEN_SOFT, stroke=GREEN, title_color=GREEN,
        )

    def draw_write_boundaries(self, canvas, width):
        lanes = [
            (
                16, "Substantive work", "interactive branch / Elim exact files",
                "host: non-force main or unmerged review PR", SKY, BLUE,
            ),
            (
                width / 3 + 8, "Bot proposal/report", "dedicated bot branch",
                "narrow diff · force-with-lease only · human merge", GOLD_SOFT, GOLD,
            ),
            (
                width * 2 / 3, "Generated data", "project-console-data",
                "direct deterministic commit · preserves unrelated tree", GREEN_SOFT, GREEN,
            ),
        ]
        lane_w = width / 3 - 18
        for x, title, body, detail, fill, stroke in lanes:
            self.box(canvas, x, 78, lane_w, 92, title, body, fill=fill, stroke=stroke, title_color=stroke)
            self.box(canvas, x, 24, lane_w, 42, "Acceptance boundary", detail, fill=WHITE, stroke=stroke, title_color=stroke)
            self.arrow(canvas, x + lane_w / 2, 78, x + lane_w / 2, 66, color=stroke)
        self.label(canvas, "No class creates authority; no bot or agent force-pushes main.", width / 2, 10)

    def draw_provenance(self, canvas, width):
        self.box(
            canvas, width / 2 - 82, 142, 164, 42,
            "Material work unit", "Chain ID · Unit ID · source revision",
            fill=SKY, stroke=BLUE,
        )
        destinations = [
            (16, 66, "Issue audit sidecar", "detailed findings"),
            (width / 2 - 75, 66, "Agent Audit Log", "provenance + rollback"),
            (width - 166, 66, "Elim Run Log", "invocation summary"),
            (16, 12, "Domain / intake ledger", "accepted event or action"),
            (width / 2 - 75, 12, "Git / PR / Project", "change + review evidence"),
            (width - 166, 12, "Console / Actions", "derived operational view"),
        ]
        for x, y, title, body in destinations:
            self.box(canvas, x, y, 150, 34, title, body, fill=SOFT, stroke=LINE)
            self.arrow(canvas, width / 2, 142, x + 75, y + 34, dashed=True)

    def draw_handoff_lifecycle(self, canvas, width):
        top_width = 142
        top_gap = (width - 3 * top_width - 32) / 2
        top_positions = [
            (
                16,
                "Before Elim",
                "Dispatcher reads only; project state is ordinarily Inactive",
                SOFT,
                LINE,
            ),
            (
                16 + top_width + top_gap,
                "Elim starts work",
                "Elim sets Open before the first substantive operation",
                SKY,
                BLUE,
            ),
            (
                16 + 2 * (top_width + top_gap),
                "Major phases",
                "Elim refreshes completed steps and the exact next action",
                SKY,
                BLUE,
            ),
        ]
        for x, title, body, fill, stroke in top_positions:
            self.box(
                canvas,
                x,
                205,
                top_width,
                48,
                title,
                body,
                fill=fill,
                stroke=stroke,
                title_color=stroke if stroke != LINE else NAVY,
            )
        self.arrow(canvas, 16 + top_width, 229, top_positions[1][0], 229)
        self.arrow(
            canvas,
            top_positions[1][0] + top_width,
            229,
            top_positions[2][0],
            229,
        )

        outcome_width = (width - 52) / 3
        outcomes = [
            (
                16,
                "Completed / clean / human review",
                "Elim clears the handoff to Inactive; host verifies synchronization",
                GREEN_SOFT,
                GREEN,
            ),
            (
                26 + outcome_width,
                "Usage stop / blocked",
                "Elim sets Paused or Blocked with the exact continuation",
                GOLD_SOFT,
                GOLD,
            ),
            (
                36 + 2 * outcome_width,
                "Abrupt termination",
                "Last Open checkpoint remains evidence; host never fabricates closure",
                RED_SOFT,
                RED,
            ),
        ]
        branch_x = top_positions[2][0] + top_width / 2
        for x, title, body, fill, stroke in outcomes:
            self.box(
                canvas,
                x,
                104,
                outcome_width,
                61,
                title,
                body,
                fill=fill,
                stroke=stroke,
                title_color=stroke,
            )
            self.arrow(
                canvas,
                branch_x,
                205,
                x + outcome_width / 2,
                165,
                color=stroke,
            )

        self.box(
            canvas,
            width / 2 - 205,
            28,
            410,
            45,
            "Three distinct authorities",
            "CURRENT_AUDIT is continuation state; the host lease proves runtime ownership; specialized logs and Git preserve history",
            fill=WHITE,
            stroke=NAVY,
        )
        for x, _, _, _, stroke in outcomes:
            self.arrow(
                canvas,
                x + outcome_width / 2,
                104,
                width / 2,
                73,
                color=stroke,
                dashed=True,
            )
        self.label(
            canvas,
            "The scheduler and deterministic bots never author the audit handoff.",
            width / 2,
            13,
            color=RED,
            size=7,
        )


class SpecDocTemplate(BaseDocTemplate):
    def __init__(
        self,
        filename: str,
        *,
        baseline: str,
        version: str,
        as_of: str,
    ):
        super().__init__(
            filename,
            pagesize=letter,
            leftMargin=0.62 * inch,
            rightMargin=0.62 * inch,
            topMargin=0.72 * inch,
            bottomMargin=0.62 * inch,
            title="ARRP Persistent Automation - Technical Specification and Traceability Map",
            author="American Restoration and Resilience Project",
            subject="Non-authoritative reference product",
            creator="ARRP ReportLab generator",
        )
        self.baseline = baseline
        self.version = version
        self.as_of = as_of
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
        )
        self.addPageTemplates(
            [
                PageTemplate(id="spec", frames=[frame], onPage=self.draw_page),
            ]
        )

    def draw_page(self, canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, letter[1] - 0.34 * inch, letter[0], 0.34 * inch, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont(BOLD_FONT, 7.2)
        canvas.drawString(
            self.leftMargin,
            letter[1] - 0.22 * inch,
            "ARRP PERSISTENT AUTOMATION",
        )
        canvas.setFillColor(colors.HexColor("#FFD78A"))
        canvas.drawRightString(
            letter[0] - self.rightMargin,
            letter[1] - 0.22 * inch,
            "NON-AUTHORITATIVE REFERENCE PRODUCT",
        )
        canvas.setStrokeColor(LINE)
        canvas.line(
            self.leftMargin,
            0.43 * inch,
            letter[0] - self.rightMargin,
            0.43 * inch,
        )
        canvas.setFillColor(MUTED)
        canvas.setFont(REGULAR_FONT, 6.8)
        canvas.drawString(
            self.leftMargin,
            0.26 * inch,
            f"Version {self.version} · {self.as_of} · baseline {self.baseline[:12]}",
        )
        canvas.drawRightString(
            letter[0] - self.rightMargin,
            0.26 * inch,
            f"Page {doc.page}",
        )
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            level = getattr(flowable, "toc_level", None)
            if level is None:
                return
            text = flowable.getPlainText()
            key = flowable.bookmark_name
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=False)
            self.notify("TOCEntry", (level, text, self.page, key))


def heading(
    text: str,
    level: int,
    styles: dict[str, ParagraphStyle],
    bookmark_name: str,
) -> Paragraph:
    style_name = "Heading1" if level <= 2 else "Heading2" if level == 3 else "Heading3"
    paragraph = Paragraph(text, styles[style_name])
    paragraph.toc_level = 0 if level <= 2 else 1 if level == 3 else 2
    paragraph.bookmark_name = bookmark_name
    return paragraph


def markdown_flowables(
    text: str,
    *,
    source: Path,
    styles: dict[str, ParagraphStyle],
    available_width: float,
) -> list:
    lines = strip_front_matter(text).splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.startswith("## Status and authority"))
        lines = lines[start:]
    except StopIteration:
        pass
    story: list = []
    index = 0
    heading_index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        diagram = re.fullmatch(r"<!--\s*diagram:([a-z-]+)\s*-->", stripped)
        if diagram:
            kind = diagram.group(1)
            story.append(Spacer(1, 4))
            story.append(Diagram(kind, available_width))
            story.append(
                Paragraph(
                    "Figure: "
                    + Diagram.TITLES[kind]
                    + ". Arrows show data or control flow, not grants of authority.",
                    styles["Caption"],
                )
            )
            index += 1
            continue
        heading_match = heading_parts(stripped)
        if heading_match:
            level, title = heading_match
            story.append(
                heading(
                    inline_markup(title, source),
                    level,
                    styles,
                    f"heading-{heading_index}",
                )
            )
            heading_index += 1
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines) and is_table_divider(lines[index + 1].strip()):
            rows = [table_cells(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(table_cells(lines[index].strip()))
                index += 1
            if story and isinstance(story[-1], Paragraph):
                story[-1].keepWithNext = True
            table_lead = Spacer(1, 3)
            table_lead.keepWithNext = True
            story.append(table_lead)
            story.append(make_table(rows, styles, source, available_width))
            story.append(Spacer(1, 7))
            continue
        list_match = list_line_parts(line)
        if list_match:
            ordered = list_match[1].endswith(".")
            items = []
            while index < len(lines):
                current = list_line_parts(lines[index])
                if not current or current[1].endswith(".") != ordered:
                    break
                items.append(
                    ListItem(
                        Paragraph(inline_markup(current[2], source), styles["Bullet"]),
                        leftIndent=13,
                    )
                )
                index += 1
            list_options = {
                "bulletType": "1" if ordered else "bullet",
                "leftIndent": 16,
                "bulletFontName": REGULAR_FONT,
                "bulletFontSize": 8,
                "bulletColor": BLUE,
                "spaceAfter": 5,
            }
            if ordered:
                list_options["start"] = "1"
            story.append(ListFlowable(items, **list_options))
            continue
        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if (
                not candidate
                or candidate.startswith("#")
                or candidate.startswith("<!--")
                or candidate.startswith("|")
                or re.match(r"^(\s*)([-*]|\d+\.)\s+", lines[index])
            ):
                break
            paragraph_lines.append(candidate)
            index += 1
        body = " ".join(paragraph_lines)
        style = styles["Disclaimer"] if body == "**NON-AUTHORITATIVE REFERENCE PRODUCT**" else styles["Body"]
        story.append(Paragraph(inline_markup(body, source), style))
    return story


def cover_story(
    styles: dict[str, ParagraphStyle],
    baseline: str,
    version: str,
    display_date: str,
) -> list:
    title_block = Table(
        [
            [Paragraph("ARRP", styles["CoverTitle"])],
            [Paragraph("Persistent Automation", styles["CoverTitle"])],
            [
                Paragraph(
                    "Technical Specification and Traceability Map",
                    styles["CoverSubtitle"],
                )
            ],
        ],
        colWidths=[6.95 * inch],
        rowHeights=[0.56 * inch, 0.56 * inch, 0.68 * inch],
    )
    title_block.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 24),
                ("RIGHTPADDING", (0, 0), (-1, -1), 24),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0, NAVY),
            ]
        )
    )
    notice = Table(
        [
            [
                Paragraph(
                    "NON-AUTHORITATIVE REFERENCE PRODUCT",
                    styles["Disclaimer"],
                )
            ],
            [
                Paragraph(
                    "Describes the reviewed system; creates no authority, schedule, permission, or project decision.",
                    styles["CoverMeta"],
                )
            ],
        ],
        colWidths=[6.45 * inch],
    )
    notice.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), RED_SOFT),
                ("BOX", (0, 0), (-1, -1), 1, RED),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    return [
        Spacer(1, 0.46 * inch),
        title_block,
        Spacer(1, 0.48 * inch),
        notice,
        Spacer(1, 0.54 * inch),
        Paragraph(
            f"<b>Version {html.escape(version)}</b><br/>{html.escape(display_date)}<br/><br/>"
            "American Restoration and Resilience Project<br/><br/>"
            f"Reviewed implementation baseline: <font name='Courier'>{baseline}</font>",
            styles["CoverMeta"],
        ),
        Spacer(1, 0.62 * inch),
        Paragraph(
            "This PDF is generated from the repository's non-authoritative Markdown reference. "
            "The Framework, Agent Operating Rules, routed modules, registered runbooks, and "
            "reviewed runtime configuration remain the controlling sources.",
            styles["CoverMeta"],
        ),
        PageBreak(),
    ]


def toc_story(styles: dict[str, ParagraphStyle]) -> list:
    toc = TableOfContents()
    toc.levelStyles = [styles["TOC0"], styles["TOC1"], styles["TOC1"]]
    source_link = GITHUB_BLOB + "research/reference-products/agent-automation-technical-spec.md"
    return [
        Paragraph("Contents", styles["TOCTitle"]),
        Paragraph(
            "This table is generated from the document's section structure. "
            f"<link href='{source_link}' color='#1769AA'>Open the source reference on GitHub.</link>",
            styles["Body"],
        ),
        Spacer(1, 8),
        toc,
        PageBreak(),
    ]


def build(source: Path, output: Path, baseline: str) -> None:
    styles = make_styles()
    text = source.read_text(encoding="utf-8").replace("{{GIT_COMMIT}}", baseline)
    version, as_of, display_date = reference_metadata(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SpecDocTemplate(
        str(output),
        baseline=baseline,
        version=version,
        as_of=as_of,
    )
    story = cover_story(styles, baseline, version, display_date)
    story.extend(toc_story(styles))
    story.extend(
        markdown_flowables(
            text,
            source=source,
            styles=styles,
            available_width=doc.width,
        )
    )
    doc.multiBuild(story)


def main() -> int:
    args = parse_args()
    baseline = args.baseline or current_revision()
    build(args.source.resolve(), args.output.resolve(), baseline)
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
