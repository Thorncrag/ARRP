import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from scripts.build_agent_automation_technical_spec import (
    ROOT,
    build,
    heading_parts,
    inline_markup,
    list_line_parts,
    reference_metadata,
)


class AgentAutomationTechnicalSpecTests(unittest.TestCase):
    def test_reference_metadata_is_derived_from_front_matter(self):
        self.assertEqual(
            reference_metadata(
                '---\nversion: "2.5"\nas_of: "2027-01-03"\n---\n# Reference\n'
            ),
            ("2.5", "2027-01-03", "January 3, 2027"),
        )

    def test_markdown_parsers_are_bounded_and_preserve_supported_forms(self):
        self.assertEqual(heading_parts("### Heading"), (3, "Heading"))
        self.assertIsNone(heading_parts("####### Not a supported heading"))
        self.assertEqual(list_line_parts("  12. Item"), ("  ", "12.", "Item"))
        self.assertEqual(list_line_parts("* Item"), ("", "*", "Item"))
        self.assertEqual(list_line_parts("١٢. Item"), ("", "١٢.", "Item"))
        self.assertIsNone(list_line_parts("². Not decimal"))
        self.assertIsNone(list_line_parts(f"{' ' * 200_000}not-a-list"))
        self.assertIsNone(heading_parts("# " + " " * 200_000))
        self.assertIsNone(list_line_parts("* " + " " * 200_000))
        linked = inline_markup(
            "[Framework](../../framework/FRAMEWORK.md)",
            ROOT
            / "research"
            / "reference-products"
            / "agent-automation-technical-spec.md",
        )
        self.assertIn("<link href=", linked)
        self.assertIn("Framework</link>", linked)
        for malformed in ("[" * 200_000, "[x](" * 100_000):
            self.assertEqual(inline_markup(malformed, ROOT / "README.md"), malformed)

    def test_front_matter_scan_rejects_an_unclosed_large_header(self):
        with self.assertRaisesRegex(ValueError, "missing YAML front matter"):
            reference_metadata("---\n" + "\n " * 100_000)
        with self.assertRaisesRegex(ValueError, "missing YAML front matter"):
            reference_metadata("  ---\nversion: 1\nas_of: 2026-07-24\n---\n")

    def test_reference_source_is_explicitly_nonauthoritative_and_visual(self):
        source = (
            ROOT
            / "research"
            / "reference-products"
            / "agent-automation-technical-spec.md"
        )
        text = source.read_text(encoding="utf-8")
        self.assertIn("status: non-authoritative-reference", text)
        self.assertIn("**NON-AUTHORITATIVE REFERENCE PRODUCT**", text)
        self.assertGreaterEqual(text.count("<!-- diagram:"), 8)
        self.assertIn("Only a human may permanently remove", text)
        self.assertIn("A queue identifies work; it never creates authority.", text)
        self.assertIn(
            "Human-directed development remains task-shaped and comprehensive",
            text,
        )
        self.assertIn(
            "the additive union of every implicated module",
            text,
        )
        self.assertIn(
            "The obligation does not expire with age.",
            text,
        )
        self.assertIn(
            "retains the 128 newest recognized events",
            text,
        )
        self.assertIn(
            "The workspace-write model does not stage, branch, commit, push",
            text,
        )
        self.assertIn(
            "A window at zero use is dormant",
            text,
        )
        self.assertIn(
            "cloud completion with an eligible Elim unit remains `host_pending`",
            text,
        )
        self.assertIn(
            "reconciled-checkout archive mode",
            text,
        )

    def test_generated_pdf_preserves_status_core_controls_and_diagrams(self):
        source = (
            ROOT
            / "research"
            / "reference-products"
            / "agent-automation-technical-spec.md"
        )
        baseline = "a" * 40
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "automation-reference.pdf"
            build(source, output, baseline)
            reader = PdfReader(output)
            self.assertGreaterEqual(len(reader.pages), 20)
            self.assertEqual(
                reader.metadata.title,
                "ARRP Persistent Automation - Technical Specification and Traceability Map",
            )
            page_text = [page.extract_text() or "" for page in reader.pages]
            content = "\n".join(page_text)
            self.assertIn("NON-AUTHORITATIVE REFERENCE PRODUCT", content)
            self.assertIn("Due-aware persistent run chain", content)
            self.assertIn(
                "Deterministic stage outcomes and separate blocking state",
                content,
            )
            self.assertIn(
                "A deterministic stage never synthesizes blocked.",
                content,
            )
            self.assertIn(
                "Three write classes and Elim split-closeout",
                content,
            )
            self.assertNotIn("Public stage outcomes and recovery routing", content)
            self.assertIn("15 percent is the absolute protected user reserve", content)
            self.assertIn("Only a human may permanently remove", content)
            self.assertIn(baseline, content)
            appendix_page = next(
                text
                for text in page_text
                if "Appendix D. Project Integrity Bot check inventory" in text
                and "This table mirrors the runbook" in text
            )
            self.assertIn("Check family", appendix_page)


if __name__ == "__main__":
    unittest.main()
