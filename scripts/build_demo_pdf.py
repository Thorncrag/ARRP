#!/usr/bin/env python3
"""Build a focused ARRP demo PDF.

This export intentionally includes only the project front page, DOJ-001,
the DOJ-001 proposed legislation appendix, and the technical framework appendix.
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate

sys.dont_write_bytecode = True

from build_compiled_pdf import (
    ROOT,
    draw_footer,
    inline_markup,
    make_styles,
    markdown_to_flowables,
    read,
)


EXPORT_DIR = ROOT / "exports" / "pdf"
OUTPUT = EXPORT_DIR / "ARRP-DOJ-001-demo-packet.pdf"


def build_story() -> list:
    styles = make_styles()
    story = []

    story.append(Paragraph("American Restoration and Resilience Project", styles["Title"]))
    story.append(
        Paragraph(
            "Public Demo Packet: Front Page, DOJ-001, Proposed Legislation, and Framework",
            styles["Subtitle"],
        )
    )
    story.append(Paragraph("Generated from canonical Markdown sources.", styles["Body"]))
    story.append(PageBreak())

    story.append(Paragraph("Contents", styles["H1"]))
    for entry in [
        "Front Page",
        "DOJ-001 - Recent Presidential Personal Counsel in Senior DOJ Leadership",
        "Appendix A - Proposed Legislation for DOJ-001",
        "Appendix B - Technical Framework",
    ]:
        story.append(Paragraph(inline_markup(entry), styles["Body"]))
    story.append(PageBreak())

    story.append(Paragraph("Front Page", styles["H1"]))
    story.extend(markdown_to_flowables(read(ROOT / "README.md"), styles, heading_offset=0))

    story.append(PageBreak())
    story.append(Paragraph("DOJ-001", styles["H1"]))
    story.extend(markdown_to_flowables(read(ROOT / "areas" / "DOJ" / "issues" / "DOJ-001.md"), styles, heading_offset=0))

    story.append(PageBreak())
    story.append(Paragraph("Appendix A - Proposed Legislation for DOJ-001", styles["H1"]))
    story.extend(markdown_to_flowables(read(ROOT / "legislation" / "DOJ-001.md"), styles, heading_offset=0))

    story.append(PageBreak())
    story.append(Paragraph("Appendix B - Technical Framework", styles["H1"]))
    story.extend(markdown_to_flowables(read(ROOT / "framework" / "FRAMEWORK.md"), styles, heading_offset=0))

    return story


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=(8.5 * inch, 11 * inch),
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
        title="ARRP DOJ-001 Demo Packet",
        author="Benjamin Smith",
    )
    doc.build(build_story(), onFirstPage=draw_footer, onLaterPages=draw_footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
