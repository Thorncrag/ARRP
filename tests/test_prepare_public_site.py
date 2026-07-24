import importlib.util
import json
import re
import unittest
from pathlib import Path
from unittest import mock


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
        self.assertIn("UNDER_REVIEW.md", sources)
        self.assertIn("SUPPORT.md", sources)
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
                    "UNDER_REVIEW.md",
                    "SUPPORT.md",
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
        self.assertIn('"Under Review": UNDER_REVIEW.md', config)
        self.assertIn('"About the Project": ABOUT.md', config)
        self.assertIn('"Support": SUPPORT.md', config)
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
        self.assertLess(
            config.index('"Proposed Legislation"'),
            config.index('"Under Review": UNDER_REVIEW.md'),
        )
        self.assertLess(
            config.index('"Under Review": UNDER_REVIEW.md'),
            config.index('"About":'),
        )
        self.assertLess(
            config.index('"About":'),
            config.index('"Support": SUPPORT.md'),
        )
        self.assertLess(
            config.index('"Support": SUPPORT.md'),
            config.index('"Contact":'),
        )
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

    def test_under_review_page_is_current_and_reader_safe(self):
        page = (self.docs / "UNDER_REVIEW.md").read_text(encoding="utf-8")
        data = MODULE.console_snapshot()
        horizon = [
            record
            for record in data["active_horizon_records"]
            if isinstance(record, dict)
        ]
        monitored = [
            record
            for record in data["monitoring_issues"]
            if isinstance(record, dict)
            and not str(record.get("id", "")).startswith("HOR-")
        ]
        investigations = [
            record
            for record in horizon
            if str(record.get("workflow_status", "")).casefold() == "research"
        ]
        held = [
            record
            for record in horizon
            if str(record.get("workflow_status", "")).casefold() in {"blocked", "deferred"}
        ]
        developing = [
            record
            for record in horizon
            if record not in investigations and record not in held
        ]
        preliminary = [
            record
            for record in data["records"]
            if isinstance(record, dict)
            and str(record.get("kind", "")).casefold() == "preliminary_candidate"
        ]

        self.assertNotIn(MODULE.UNDER_REVIEW_DATA_MARKER, page)
        self.assertIn("# Issues Under Review", page)
        self.assertIn("Request an Issue or Submit New Evidence", page)
        self.assertIn("Submit an issue or source", page)
        self.assertIn("Contact the author privately", page)
        self.assertIn("Appearing here does **not** mean", page)
        self.assertIn(f"**{len(investigations)}** active investigations", page)
        self.assertIn(f"**{len(developing)}** other formal candidates", page)
        self.assertIn(f"**{len(held)}** candidates waiting on evidence", page)
        if preliminary:
            self.assertIn("## Early Review", page)
            self.assertIn(
                f"**{len(preliminary)}** preliminary candidates in early review",
                page,
            )
        else:
            self.assertNotIn("## Early Review", page)
            self.assertNotIn("preliminary candidates in early review", page)
        self.assertIn(
            f"**{len(monitored)}** established issues watching external developments",
            page,
        )
        for record in preliminary:
            self.assertIn(f"{record['id']} — {record['title']}", page)
        for record in horizon:
            self.assertIn(
                f"{record['id']} — {record['title']}",
                page,
            )
        for record in monitored:
            self.assertIn(
                f"{record['id']} — {record['title']}",
                page,
            )
        for forbidden in (
            "project-console-data",
            "ARRP_HORIZON_REVIEW_DATA",
            "dossier_gaps",
            "supporting_sources",
            "issue_body_html",
        ):
            self.assertNotIn(forbidden, page)

    def test_support_routes_through_one_reader_safe_page(self):
        support = (self.docs / "SUPPORT.md").read_text(encoding="utf-8")
        about = (self.docs / "ABOUT.md").read_text(encoding="utf-8")

        self.assertIn("# Support ARRP", support)
        self.assertIn("## Funding and Editorial Independence", support)
        self.assertIn("## Public Access and Reuse", support)
        self.assertIn("should not be treated as a tax-deductible", support)
        self.assertIn("One-time support has a $3 minimum", support)
        self.assertIn("Choose a one-time amount", support)
        self.assertIn("Support monthly — $5/month", support)
        self.assertIn(
            "https://donate.stripe.com/7sY6oJ6So8CI9QndGY6Vq00",
            support,
        )
        self.assertIn(
            "https://buy.stripe.com/9B628tb8EdX29Qn46o6Vq01",
            support,
        )
        self.assertNotIn("coming soon", support)
        self.assertIn("[Support ARRP](SUPPORT.md){ .md-button }", about)

    def test_preliminary_candidates_appear_only_when_present(self):
        snapshot = {
            "generated_at": "2026-07-23T22:20:11+00:00",
            "github_synced_at": "2026-07-23T22:20:04+00:00",
            "records": [
                {
                    "id": "PRE-999",
                    "kind": "preliminary_candidate",
                    "title": "Illustrative early-review concern",
                    "summary": "A possible institutional weakness requiring initial screening.",
                    "supporting_sources": [{"internal": "must not render"}],
                    "unresolved": "Internal review notes must not render.",
                }
            ],
            "active_horizon_records": [],
            "monitoring_issues": [],
        }
        with mock.patch.object(MODULE, "console_snapshot", return_value=snapshot):
            rendered = MODULE.render_under_review_data()
        self.assertIn("## Early Review", rendered)
        self.assertIn("**1** preliminary candidates in early review", rendered)
        self.assertIn("PRE-999 — Illustrative early-review concern", rendered)
        self.assertIn("A possible institutional weakness requiring initial screening.", rendered)
        self.assertNotIn("supporting_sources", rendered)
        self.assertNotIn("Internal review notes", rendered)

        snapshot["records"] = []
        with mock.patch.object(MODULE, "console_snapshot", return_value=snapshot):
            rendered_without_preliminary = MODULE.render_under_review_data()
        self.assertNotIn("## Early Review", rendered_without_preliminary)
        self.assertNotIn("preliminary candidates in early review", rendered_without_preliminary)

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
        self.assertIn(".arrp-under-review-cta", stylesheet)
        self.assertIn(".arrp-under-review-summary", stylesheet)
        self.assertIn(".arrp-under-review-table", stylesheet)
        self.assertIn(".arrp-support-cta", stylesheet)
        self.assertIn(".arrp-support-panel", stylesheet)
        self.assertIn(".arrp-support-actions", stylesheet)
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
