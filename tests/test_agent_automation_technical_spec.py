import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from scripts.build_agent_automation_technical_spec import ROOT, build, reference_metadata


class AgentAutomationTechnicalSpecTests(unittest.TestCase):
    def test_reference_metadata_is_derived_from_front_matter(self):
        self.assertEqual(
            reference_metadata(
                '---\nversion: "2.5"\nas_of: "2027-01-03"\n---\n# Reference\n'
            ),
            ("2.5", "2027-01-03", "January 3, 2027"),
        )

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
