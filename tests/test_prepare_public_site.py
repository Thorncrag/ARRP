import importlib.util
import json
import re
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
        self.assertIn("PRINT_READERS_GUIDE.md", sources)
        self.assertIn("SUBJECT_INDEX.md", sources)
        self.assertIn("topics/README.md", sources)
        self.assertIn("topics/project-2025.md", sources)
        self.assertIn("topics/campaign-finance.md", sources)
        self.assertIn("topics/civil-rights.md", sources)
        self.assertIn("topics/doge-and-agency-dismantling.md", sources)
        self.assertIn("topics/elections.md", sources)
        self.assertIn("topics/epstein-files.md", sources)
        self.assertIn("topics/executive-orders-and-presidential-power.md", sources)
        self.assertIn("topics/federal-pressure-on-states-and-cities.md", sources)
        self.assertIn("topics/government-spending-and-impoundment.md", sources)
        self.assertIn("topics/immigration-system-reform.md", sources)
        self.assertIn("topics/january-6.md", sources)
        self.assertIn("topics/presidential-accountability.md", sources)
        self.assertIn("topics/weaponization-of-justice.md", sources)
        self.assertTrue(
            all(
                source in {
                    "README.md",
                    "PRINT_READERS_GUIDE.md",
                    "SUBJECT_INDEX.md",
                    "ABOUT.md",
                    "LICENSE.md",
                }
                or source.startswith("areas/")
                or source.startswith("legislation/")
                or source.startswith("topics/")
                for source in sources
            )
        )

    def test_project_console_and_internal_apparatus_are_absent(self):
        self.assertFalse((self.docs / "framework").exists())
        self.assertFalse((self.docs / ".github").exists())
        self.assertFalse((self.docs / "inventory").exists())
        self.assertFalse((self.docs / "research").exists())
        self.assertFalse((self.docs / "sources").exists())
        staged_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore").lower()
            for path in self.docs.rglob("*")
            if path.is_file()
        )
        self.assertNotIn("project-console-data", staged_text)

    def test_reader_navigation_is_generated(self):
        config = (ROOT / ".site-build" / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn('"Topics"', config)
        self.assertIn('"About the Project": ABOUT.md', config)
        self.assertIn('"Using a Print Edition": PRINT_READERS_GUIDE.md', config)
        self.assertIn('"Technical Record on GitHub": https://github.com/Thorncrag/ARRP', config)
        self.assertIn('"Overview": topics/index.md', config)
        self.assertIn(
            '"Project 2025": topics/project-2025.md',
            config,
        )
        self.assertIn('"Campaign Finance": topics/campaign-finance.md', config)
        self.assertIn('"Civil Rights": topics/civil-rights.md', config)
        self.assertIn(
            '"DOGE and Agency Dismantling": topics/doge-and-agency-dismantling.md',
            config,
        )
        self.assertIn('"Elections": topics/elections.md', config)
        self.assertIn('"Epstein Files": topics/epstein-files.md', config)
        self.assertIn(
            '"Executive Orders and Presidential Power": topics/executive-orders-and-presidential-power.md',
            config,
        )
        self.assertIn(
            '"Federal Pressure on States and Cities": topics/federal-pressure-on-states-and-cities.md',
            config,
        )
        self.assertIn(
            '"Government Spending and Impoundment": topics/government-spending-and-impoundment.md',
            config,
        )
        self.assertIn(
            '"Immigration System Reform": topics/immigration-system-reform.md',
            config,
        )
        self.assertIn('"January 6": topics/january-6.md', config)
        self.assertIn(
            '"Presidential Accountability": topics/presidential-accountability.md',
            config,
        )
        self.assertIn(
            '"Weaponization of Justice": topics/weaponization-of-justice.md',
            config,
        )
        self.assertIn('"Subject and Institution Index": SUBJECT_INDEX.md', config)
        self.assertIn('"A-01 / DOJ — Department of Justice"', config)
        self.assertIn('"Proposed Legislation"', config)
        self.assertIn("git-revision-date-localized:", config)
        self.assertIn("../website/git_revision_dates.py", config)
        self.assertIn("navigation.path", config)
        self.assertIn("custom_dir: ../website/overrides", config)
        self.assertIn("navigation.tracking", config)
        self.assertIn("toc.follow", config)
        self.assertIn("search.share", config)
        self.assertTrue((self.docs / "legislation" / "index.md").exists())
        path_template = ROOT / "website" / "overrides" / "partials" / "path.html"
        path_item_template = ROOT / "website" / "overrides" / "partials" / "path-item.html"
        toc_template = ROOT / "website" / "overrides" / "partials" / "toc.html"
        self.assertTrue(path_template.exists())
        self.assertTrue(path_item_template.exists())
        self.assertTrue(toc_template.exists())
        self.assertIn('aria-current="page"', path_template.read_text(encoding="utf-8"))
        self.assertIn('title.startswith("A-")', path_item_template.read_text(encoding="utf-8"))
        toc = toc_template.read_text(encoding="utf-8")
        self.assertIn('class="arrp-page-tools"', toc)
        self.assertIn("arrp-page-action--contact", toc)
        self.assertIn("Contact or review", toc)
        self.assertIn('data-arrp-print', toc)
        self.assertIn('data-arrp-feedback', toc)

    def test_public_page_action_assets_are_staged(self):
        self.assertTrue((ROOT / "assets" / "branding" / "arrp-emblem-master.png").exists())
        self.assertTrue((ROOT / "assets" / "branding" / "arrp-emblem-print.png").exists())
        self.assertTrue((ROOT / "assets" / "branding" / "arrp-emblem-dark.png").exists())
        self.assertTrue((self.docs / "assets" / "javascripts" / "site.js").exists())
        self.assertTrue((self.docs / "assets" / "branding" / "arrp-emblem-dark.webp").exists())
        self.assertTrue((self.docs / "assets" / "branding" / "arrp-emblem-web.webp").exists())
        self.assertTrue((ROOT / "website" / "overrides" / "home.html").exists())
        stylesheet = (self.docs / "assets" / "stylesheets" / "extra.css").read_text()
        self.assertIn(".arrp-issue-status", stylesheet)
        self.assertIn(".arrp-page-actions", stylesheet)
        self.assertIn(".arrp-page-tools", stylesheet)
        self.assertIn(".arrp-page-action--contact::before", stylesheet)
        self.assertIn("h1#explore-by-topic", stylesheet)
        self.assertIn("grid-template-columns: repeat(2", stylesheet)
        self.assertIn(".arrp-topic-guide-title", stylesheet)
        self.assertIn(".arrp-topic-table", stylesheet)
        self.assertIn(".arrp-home-emblem", stylesheet)
        self.assertRegex(
            stylesheet,
            r"\.md-nav \.md-status\s*\{\s*display: none;\s*\}",
        )

    def test_generated_legislation_index_has_revision_date(self):
        index = (self.docs / "legislation" / "index.md").read_text(encoding="utf-8")
        self.assertRegex(
            index,
            r'(?m)^git_revision_date_localized: "[A-Z][a-z]+ [1-9][0-9]?, 20[0-9]{2}"$',
        )

    def test_topic_guide_is_a_nonauthoritative_routing_page(self):
        guides = sorted((ROOT / "topics").glob("*.md"))
        guides = [guide for guide in guides if guide.name != "README.md"]
        for path in guides:
            with self.subTest(guide=path.name):
                guide = path.read_text(encoding="utf-8")
                for heading in (
                    "## Overview",
                    "## Applicable Proposals",
                    "## What ARRP Does and Does Not Address",
                ):
                    self.assertIn(heading, guide)
                self.assertRegex(guide, r"(?m)^# .+ \{\.arrp-topic-guide-title\}$")
                self.assertNotIn("## Relevant Proposals", guide)
                self.assertNotIn("## How Concerns Map to Proposals", guide)

                applicable = guide.split("## Applicable Proposals", 1)[1].split("\n## ", 1)[0]
                self.assertIn(
                    '<div class="arrp-topic-table arrp-topic-table--map" markdown>',
                    applicable,
                )
                self.assertIn(
                    "| Public concern | Proposal | How ARRP addresses it |",
                    applicable,
                )
                self.assertIn("</div>", applicable)
                self.assertGreaterEqual(
                    len([line for line in applicable.splitlines() if line.startswith("|")]),
                    3,
                )
                table_rows = [line for line in applicable.splitlines() if line.startswith("|")]
                for row in table_rows[2:]:
                    cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
                    self.assertEqual(len(cells), 3)
                    proposal_ids = set(re.findall(r"\b[A-Z]+-\d{3}\b", cells[1]))
                    self.assertTrue(
                        len(proposal_ids) == 1 or (cells[1] == "Pending" and not proposal_ids),
                        msg=f"{path.name} must identify exactly one proposal or Pending per row: {row}",
                    )
                self.assertNotRegex(applicable, r"\]\(\.\./areas/[^)]+/README\.md\)")

                if "## Related Ideas Not Included" in guide:
                    related = guide.split("## Related Ideas Not Included", 1)[1].split("\n## ", 1)[0]
                    self.assertIn(
                        '<div class="arrp-topic-table arrp-topic-table--related" markdown>',
                        related,
                    )
                    self.assertIn(
                        "| Idea | Record | Why it is not included |",
                        related,
                    )
                    self.assertIn("</div>", related)
                    self.assertGreaterEqual(
                        len([line for line in related.splitlines() if line.startswith("|")]),
                        3,
                    )
                self.assertEqual(
                    guide.count('<div class="arrp-topic-table'),
                    guide.count("</div>"),
                )
                for disallowed in (
                    "Reader concern",
                    "## Topic Overview",
                    "## Relevant ARRP Records",
                    "## Topic Crosswalk",
                    "## Scope Boundary",
                    "## Sources and Currency",
                    "## Rejected or Outside-Scope Concepts",
                    "Authoritative ARRP route",
                    "nonauthoritative reader guide",
                    "records that own",
                    "proposal vehicles",
                    "institutional homes",
                    "| Public concern | ARRP route |",
                    "| Record | Function |",
                    "## Methodology",
                    "Gap / next action",
                    "## ARRP Coverage Assessment",
                    "### Highest-priority gaps",
                    "## Proposal Scoring",
                    "## Budgetary Impact",
                    "## Prior ARRP Dispositions",
                    "HOR-011",
                    "HOR-015",
                    "HOR-018",
                ):
                    self.assertNotIn(disallowed, guide)

    def test_manifest_is_written(self):
        written = json.loads((ROOT / ".site-build" / "public-manifest.json").read_text())
        self.assertEqual(written["canonicalSources"], self.manifest["canonicalSources"])


if __name__ == "__main__":
    unittest.main()
