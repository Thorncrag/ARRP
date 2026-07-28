import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import urllib.error


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_source_urls", ROOT / "scripts" / "check_source_urls.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Headers:
    def get_content_type(self): return "text/html"
    def get_content_charset(self): return "utf-8"


class Response:
    status = 200
    headers = Headers()

    def __init__(self, final_url, body=b"<title>H.R. 123 - Example Act</title>"):
        self.final_url, self.body = final_url, body

    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, limit): return self.body[:limit]
    def geturl(self): return self.final_url


class SourceCheckerTests(unittest.TestCase):
    base = "https://example.test"

    def settings(self):
        return {"timeoutSeconds": 2, "retries": 1, "backoffSeconds": 0, "minimumDomainIntervalSeconds": 0, "workers": 2, "maximumBytes": 4096}

    def row(self, path, title="Example source"):
        return {"URL": self.base + path, "Title or Description": title, "Authority / Publisher": "Congress"}

    def test_get_follows_redirect_and_confirms_stable_identity(self):
        with patch.object(MODULE.urllib.request, "urlopen", return_value=Response(self.base + "/bill/hr-123")):
            result = MODULE.fetch(self.row("/redirect", "H.R. 123 - Example Act"), self.settings(), MODULE.DomainPacer(0))
        self.assertEqual(result["classification"], "identity-preserving redirect")
        self.assertEqual(result["status_code"], 200)
        self.assertTrue(result["final_url"].endswith("/bill/hr-123"))

    def test_access_and_broken_are_distinct(self):
        def error(code, url):
            return urllib.error.HTTPError(url, code, "failure", Headers(), None)
        with patch.object(MODULE.urllib.request, "urlopen", side_effect=error(403, self.base + "/restricted")):
            restricted = MODULE.fetch(self.row("/restricted"), self.settings(), MODULE.DomainPacer(0))
        with patch.object(MODULE.urllib.request, "urlopen", side_effect=error(410, self.base + "/gone")):
            gone = MODULE.fetch(self.row("/gone"), self.settings(), MODULE.DomainPacer(0))
        self.assertEqual(restricted["classification"], "access restricted")
        self.assertEqual(gone["classification"], "broken")

    def test_transient_response_is_retried(self):
        error = urllib.error.HTTPError(self.base + "/unavailable", 503, "failure", Headers(), None)
        with patch.object(MODULE.urllib.request, "urlopen", side_effect=error):
            result = MODULE.fetch(self.row("/unavailable"), self.settings(), MODULE.DomainPacer(0))
        self.assertEqual(result["classification"], "transient failure")
        self.assertEqual(result["attempts"], 2)

    def test_stable_identifier_absence_requires_review(self):
        observation = {"status_code": 200, "final_url": self.base + "/other", "title": "Unrelated page", "content_type": "text/html"}
        self.assertEqual(MODULE.classify(self.row("/other", "H.R. 999 - Named Act"), observation), "review required")

    def test_conflicting_stable_identifier_is_identity_mismatch(self):
        observation = {"status_code": 200, "final_url": self.base + "/bill/hr-123", "title": "H.R. 123 - Other Act", "content_type": "text/html"}
        self.assertEqual(MODULE.classify(self.row("/other", "H.R. 999 - Named Act"), observation), "identity mismatch")

    def test_catalog_loader_accounts_for_every_nonblank_url(self):
        fields = ["Source ID", "URL", "Title or Description", "Authority / Publisher"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
                writer.writerow({"Source ID": "SRC-1", "URL": "https://example.com", "Title or Description": "A", "Authority / Publisher": "B"})
                writer.writerow({"Source ID": "SRC-2", "URL": "", "Title or Description": "C", "Authority / Publisher": "D"})
            relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else None
            old_root = MODULE.ROOT
            try:
                MODULE.ROOT = Path(directory)
                rows = MODULE.load_rows({"catalogs": ["sources.csv"], "idField": "Source ID", "urlField": "URL", "titleField": "Title or Description", "publisherField": "Authority / Publisher"})
            finally:
                MODULE.ROOT = old_root
            self.assertEqual([row["Source ID"] for row in rows], ["SRC-1"])

    def test_history_is_bounded(self):
        report = {"checked_at": "new", "eligible_urls": 1, "counts": {"verified": 1}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "old.json"
            path.write_text(json.dumps({"history": [{"checked_at": str(i)} for i in range(5)]}), encoding="utf-8")
            result = MODULE.with_history(report, path, 3)
        self.assertEqual(len(result["history"]), 3)
        self.assertEqual(result["history"][0]["checked_at"], "new")

    def test_markdown_has_no_trailing_whitespace(self):
        rendered = MODULE.markdown(
            {
                "mode": "report-only",
                "eligible_urls": 1,
                "counts": {"verified": 1},
                "results": [],
            }
        )
        self.assertFalse(
            any(line != line.rstrip() for line in rendered.splitlines())
        )

    def test_source_result_deltas_distinguish_new_regressed_resolved_and_aging(self):
        current = {
            "checked_at": "2026-07-25T12:00:00+00:00",
            "source_revision": "current-catalog",
            "results": [
                {"source_id": "SRC-NEW", "classification": "broken"},
                {
                    "source_id": "SRC-REG",
                    "classification": "access restricted",
                },
                {"source_id": "SRC-RES", "classification": "verified"},
                {"source_id": "SRC-OLD", "classification": "broken"},
                {"source_id": "SRC-ENTER", "classification": "verified"},
            ],
        }
        prior = {
            "checked_at": "2026-07-23T12:00:00+00:00",
            "source_revision": "prior-catalog",
            "results": [
                {"source_id": "SRC-REG", "classification": "verified"},
                {
                    "source_id": "SRC-RES",
                    "classification": "review required",
                },
                {
                    "source_id": "SRC-OLD",
                    "classification": "broken",
                    "exception_first_seen_at": "2026-07-20T12:00:00+00:00",
                },
                {"source_id": "SRC-LEFT", "classification": "verified"},
            ],
        }
        deltas = MODULE.source_result_deltas(current, prior)
        self.assertTrue(deltas["available"])
        self.assertEqual(deltas["new_exception_ids"], ["SRC-NEW"])
        self.assertEqual(deltas["regressed_exception_ids"], ["SRC-REG"])
        self.assertEqual(deltas["resolved_exception_ids"], ["SRC-RES"])
        self.assertEqual(deltas["ongoing_exception_ids"], ["SRC-OLD"])
        self.assertEqual(
            deltas["entered_scope_ids"],
            ["SRC-ENTER", "SRC-NEW"],
        )
        self.assertEqual(deltas["left_scope_ids"], ["SRC-LEFT"])
        oldest = next(
            item
            for item in deltas["aging_exceptions"]
            if item["source_id"] == "SRC-OLD"
        )
        self.assertEqual(oldest["age_days"], 5.0)
        current_old = next(
            item for item in current["results"] if item["source_id"] == "SRC-OLD"
        )
        self.assertEqual(
            current_old["exception_first_seen_at"],
            "2026-07-20T12:00:00+00:00",
        )

    def test_source_result_deltas_are_explicitly_unavailable_without_baseline(self):
        deltas = MODULE.source_result_deltas(
            {
                "checked_at": "2026-07-25T12:00:00+00:00",
                "results": [],
            },
            None,
        )
        self.assertFalse(deltas["available"])
        self.assertIn("prior", deltas["reason"])

    def test_report_contract_covers_current_catalog_ids_and_hashes(self):
        fields = [
            "Source ID",
            "URL",
            "Title or Description",
            "Authority / Publisher",
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "sources.csv"
            with catalog.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "Source ID": "SRC-1",
                        "URL": "https://example.test/1",
                        "Title or Description": "Source one",
                        "Authority / Publisher": "Publisher",
                    }
                )
                writer.writerow(
                    {
                        "Source ID": "SRC-2",
                        "URL": "https://example.test/2",
                        "Title or Description": "Source two",
                        "Authority / Publisher": "Publisher",
                    }
                )
            config = {
                "agentId": "source-checker-bot",
                "mode": "report-only",
                "catalogs": ["sources.csv"],
                "idField": "Source ID",
                "urlField": "URL",
                "titleField": "Title or Description",
                "publisherField": "Authority / Publisher",
                "request": {
                    "minimumDomainIntervalSeconds": 0,
                    "workers": 1,
                },
            }

            def observed(row, settings, pacer):
                return {
                    "requested_url": row["URL"],
                    "attempts": 1,
                    "status_code": 200,
                    "final_url": row["URL"],
                    "content_type": "text/html",
                    "title": row["Title or Description"],
                    "error": "",
                    "error_kind": "",
                    "classification": "verified",
                }

            old_root = MODULE.ROOT
            try:
                MODULE.ROOT = root
                rows = MODULE.load_rows(config)
                with patch.object(MODULE, "fetch", side_effect=observed):
                    report = MODULE.build_report(
                        config, rows, "2026-07-25T12:00:00Z"
                    )
            finally:
                MODULE.ROOT = old_root
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["expected_count"], 2)
        self.assertEqual(report["actual_count"], 2)
        self.assertTrue(report["completeness"]["complete"])
        self.assertIn(
            "catalog identity",
            report["freshness"]["basis"],
        )
        self.assertEqual(report["missing_source_ids"], [])
        self.assertEqual(report["catalog_coverage"][0]["actual_count"], 2)
        self.assertTrue(
            report["source_hashes"]["sources.csv"].startswith("sha256:")
        )

    def test_duplicate_source_identifiers_fail_closed(self):
        fields = [
            "Source ID",
            "URL",
            "Title or Description",
            "Authority / Publisher",
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "sources.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for suffix in ("one", "two"):
                    writer.writerow(
                        {
                            "Source ID": "SRC-1",
                            "URL": f"https://example.test/{suffix}",
                            "Title or Description": suffix,
                            "Authority / Publisher": "Publisher",
                        }
                    )
            old_root = MODULE.ROOT
            try:
                MODULE.ROOT = root
                with self.assertRaisesRegex(ValueError, "duplicate source identifier"):
                    MODULE.load_rows(
                        {
                            "catalogs": ["sources.csv"],
                            "idField": "Source ID",
                            "urlField": "URL",
                            "titleField": "Title or Description",
                            "publisherField": "Authority / Publisher",
                        }
                    )
            finally:
                MODULE.ROOT = old_root

    def test_missing_or_invalid_prior_history_fails_closed(self):
        report = {
            "checked_at": "2026-07-25T12:00:00+00:00",
            "eligible_urls": 0,
            "counts": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                MODULE.with_history(report, missing, 3)
            invalid = Path(directory) / "invalid.json"
            invalid.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "history contract"):
                MODULE.with_history(report, invalid, 3)

    def test_retired_workflow_is_absent(self):
        self.assertFalse(
            (ROOT / ".github/workflows/source-checker-bot.yml").exists()
        )

    def test_runtime_config_names_local_typed_data_and_prior_success(self):
        config = json.loads(
            (ROOT / ".github" / "source-checker-bot.json").read_text(encoding="utf-8")
        )
        self.assertEqual(config["deploymentStatus"], "local-first-enabled")
        self.assertNotIn("dataBranch", config)
        self.assertNotIn("currentDataPath", config)
        self.assertEqual(
            config["currentData"],
            "<run-dir>/stages/source-checker-bot/source-checker.json",
        )
        self.assertEqual(
            config["priorData"],
            "<last-success>/source-checker-bot/source-checker.json",
        )
        self.assertFalse(config["localStage"]["publication"])
        self.assertNotIn(
            "framework/records/status/source-checker.json", config.values()
        )


if __name__ == "__main__":
    unittest.main()
