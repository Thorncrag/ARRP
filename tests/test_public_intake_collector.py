import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "collect_public_intake", ROOT / "scripts" / "collect_public_intake.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixture(reply=""):
    return {
        "data": {
            "repository": {
                "discussions": {
                    "pageInfo": {"hasNextPage": False},
                    "nodes": [
                        {
                            "url": "https://github.com/Thorncrag/ARRP/discussions/1",
                            "body": "<!-- ARRP-INTAKE-ROUTE:GENERAL -->",
                            "comments": {
                                "pageInfo": {"hasNextPage": False},
                                "nodes": [
                                    {
                                        "id": "DC_kwABC",
                                        "url": "https://github.com/Thorncrag/ARRP/discussions/1#discussioncomment-2",
                                        "createdAt": "2026-07-24T10:00:00Z",
                                        "body": (
                                            "<!-- ARRP-INTAKE-SUBMISSION:record-1 -->\n"
                                            "<!-- ARRP-INTAKE-ELIGIBLE:1 -->\n"
                                            "private-looking content is hashed, never emitted"
                                        ),
                                        "replies": {
                                            "pageInfo": {"hasNextPage": False},
                                            "nodes": [{"body": reply}] if reply else [],
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                }
            }
        }
    }


class PublicIntakeCollectorTests(unittest.TestCase):
    def test_emits_only_minimized_pending_event(self):
        result = MODULE.collect(fixture(), {}, set())
        self.assertTrue(result["pending"])
        self.assertEqual(result["counts"]["pending"], 1)
        self.assertNotIn("body", result["items"][0])
        self.assertTrue(result["items"][0]["content_hash"].startswith("sha256:"))
        self.assertEqual(result["items"][0]["route"], "GENERAL")

    def test_reply_marker_or_ledger_marks_processed(self):
        url = "https://github.com/Thorncrag/ARRP/discussions/1#discussioncomment-2"
        replied = MODULE.collect(
            fixture(f"<!-- {MODULE.reply_marker(url)} -->"), {}, set()
        )
        self.assertFalse(replied["pending"])
        ledger = MODULE.collect(fixture(), {}, {url})
        self.assertFalse(ledger["pending"])

    def test_ambiguous_pagination_fails_closed(self):
        payload = fixture()
        payload["data"]["repository"]["discussions"]["pageInfo"]["hasNextPage"] = True
        with self.assertRaisesRegex(ValueError, "pagination"):
            MODULE.collect(payload, {}, set())


if __name__ == "__main__":
    unittest.main()
