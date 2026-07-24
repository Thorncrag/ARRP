import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "record_intake_review", ROOT / "scripts" / "record_intake_review.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class IntakeReviewLedgerTests(unittest.TestCase):
    def test_records_minimized_review_and_is_idempotent(self):
        queue = {
            "items": [
                {
                    "id": "PUBLIC-INTAKE-abc",
                    "kind": "public_intake",
                    "source": {
                        "submission": {
                            "id": "DC_1",
                            "url": "https://github.com/Thorncrag/ARRP/discussions/1#discussioncomment-2",
                            "content_hash": "sha256:abc",
                        }
                    },
                }
            ]
        }
        result = {
            "work_type": "public_intake",
            "outcome": "completed",
            "unit_id": "PUBLIC-INTAKE-abc",
            "run_id": "ELIM-1",
        }
        record = MODULE.build_record(queue, result)
        self.assertFalse(record["content_included"])
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ledger.jsonl"
            self.assertTrue(MODULE.append(ledger, record))
            self.assertFalse(MODULE.append(ledger, record))
            saved = json.loads(ledger.read_text().strip())
        self.assertNotIn("body", saved)

    def test_rejects_non_intake_or_failed_result(self):
        with self.assertRaisesRegex(ValueError, "completed public-intake"):
            MODULE.build_record({}, {"work_type": "issue_audit", "outcome": "failed"})


if __name__ == "__main__":
    unittest.main()
