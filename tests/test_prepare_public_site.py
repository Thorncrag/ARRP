import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prepare_public_site",
    ROOT / "scripts" / "prepare_public_site.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PublicSitePreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = MODULE.prepare()
        cls.docs = ROOT / ".site-build" / "docs"

    def test_public_corpus_is_allowlisted(self):
        sources = self.manifest["canonicalSources"]
        self.assertGreater(len(sources), 100)
        self.assertIn("README.md", sources)
        self.assertIn("SUBJECT_INDEX.md", sources)
        self.assertTrue(
            all(
                source in {"README.md", "SUBJECT_INDEX.md", "AUTHORS.md", "LICENSE.md"}
                or source.startswith("areas/")
                or source.startswith("legislation/")
                for source in sources
            )
        )

    def test_dashboard_and_internal_apparatus_are_absent(self):
        self.assertFalse((self.docs / "framework").exists())
        self.assertFalse((self.docs / ".github").exists())
        self.assertFalse((self.docs / "inventory").exists())
        staged_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore").lower()
            for path in self.docs.rglob("*")
            if path.is_file()
        )
        self.assertNotIn("progress-dashboard", staged_text)
        self.assertNotIn("progress dashboard", staged_text)

    def test_reader_navigation_is_generated(self):
        config = (ROOT / ".site-build" / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn('"Subject and Institution Index": SUBJECT_INDEX.md', config)
        self.assertIn('"A-01 / DOJ — Department of Justice"', config)
        self.assertIn('"Proposed Legislation"', config)
        self.assertIn("git-revision-date-localized:", config)
        self.assertIn("../website/git_revision_dates.py", config)
        self.assertTrue((self.docs / "legislation" / "index.md").exists())

    def test_generated_legislation_index_has_revision_date(self):
        index = (self.docs / "legislation" / "index.md").read_text(encoding="utf-8")
        self.assertRegex(
            index,
            r'(?m)^git_revision_date_localized: "[A-Z][a-z]+ [1-9][0-9]?, 20[0-9]{2}"$',
        )

    def test_manifest_is_written(self):
        written = json.loads((ROOT / ".site-build" / "public-manifest.json").read_text())
        self.assertEqual(written["canonicalSources"], self.manifest["canonicalSources"])


if __name__ == "__main__":
    unittest.main()
