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


if __name__ == "__main__":
    unittest.main()
