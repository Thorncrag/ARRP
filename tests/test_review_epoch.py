import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "record_review_epoch", ROOT / "scripts" / "record_review_epoch.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def record():
    return {
        "epoch_id": "REVIEW-2026-07-24",
        "triggering_run_id": "arrp-chain-1",
        "baseline_commit": "a" * 40,
        "completion_commit": "b" * 40,
        "governing_hashes": {"framework/FRAMEWORK.md": "sha256:" + "c" * 64},
        "reviewed_domains": ["governance", "issues"],
        "unresolved_findings": [],
        "sampling_record": ["DOJ-001", "ELEC-001"],
        "completed_at": "2026-07-24T12:00:00+00:00",
        "next_due_at": "2026-08-07T12:00:00+00:00",
        "cadence_status": "biweekly",
        "stability_status": "evolving",
        "triggering_reason": "Periodic consistency boundary.",
    }


class ReviewEpochTests(unittest.TestCase):
    def test_validated_epoch_is_append_only_and_updates_current(self):
        value = MODULE.validate(record())
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "epochs.jsonl"
            current = Path(directory) / "current.json"
            self.assertTrue(MODULE.append(ledger, current, value))
            self.assertFalse(MODULE.append(ledger, current, value))
            self.assertEqual(len(ledger.read_text().splitlines()), 1)
            self.assertIn("record_sha256", current.read_text())

    def test_next_due_must_follow_completion(self):
        value = record()
        value["next_due_at"] = value["completed_at"]
        with self.assertRaisesRegex(ValueError, "must follow"):
            MODULE.validate(value)


if __name__ == "__main__":
    unittest.main()
