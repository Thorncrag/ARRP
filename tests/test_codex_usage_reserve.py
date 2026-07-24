import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.check_codex_usage_reserve import (
    UsageGateError,
    apply_run_budget,
    evaluate_rate_limits,
)


def payload(*, codex_used: int = 57, spark_used: int = 1) -> dict:
    return {
        "rateLimitsByLimitId": {
            "codex": {
                "limitId": "codex",
                "limitName": None,
                "primary": {
                    "usedPercent": codex_used,
                    "resetsAt": 1_785_367_074,
                    "windowDurationMins": 10_080,
                },
                "secondary": None,
                "individualLimit": None,
                "rateLimitReachedType": None,
                "spendControlReached": False,
            },
            "codex_bengalfox": {
                "limitId": "codex_bengalfox",
                "limitName": "GPT-5.3-Codex-Spark",
                "primary": {
                    "usedPercent": spark_used,
                    "resetsAt": 1_785_416_536,
                    "windowDurationMins": 10_080,
                },
                "secondary": None,
                "individualLimit": None,
                "rateLimitReachedType": None,
                "spendControlReached": None,
            },
        }
    }


class CodexUsageReserveTests(unittest.TestCase):
    def test_all_windows_above_reserve_pass(self):
        result = evaluate_rate_limits(payload(), 15)

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["lowestRemainingPercent"], 43)
        self.assertEqual([window["remainingPercent"] for window in result["windows"]], [43, 99])

    def test_exact_reserve_aborts(self):
        result = evaluate_rate_limits(payload(codex_used=85), 15)

        self.assertEqual(result["status"], "abort")
        self.assertIn("codex primary: 15% remaining", result["blockers"])

    def test_backend_reached_state_aborts(self):
        data = payload()
        data["rateLimitsByLimitId"]["codex"]["rateLimitReachedType"] = "rate_limit_reached"

        result = evaluate_rate_limits(data, 15)

        self.assertEqual(result["status"], "abort")
        self.assertIn("codex: rate_limit_reached", result["blockers"])

    def test_missing_reset_time_fails_closed(self):
        data = payload()
        data["rateLimitsByLimitId"]["codex"]["primary"]["resetsAt"] = None

        with self.assertRaisesRegex(UsageGateError, "reset time is unavailable"):
            evaluate_rate_limits(data, 15)

    def test_legacy_single_snapshot_is_supported(self):
        data = {
            "rateLimits": {
                "limitId": "codex",
                "primary": {
                    "usedPercent": 20,
                    "resetsAt": 1_785_367_074,
                    "windowDurationMins": 10_080,
                },
                "secondary": None,
                "individualLimit": None,
                "rateLimitReachedType": None,
                "spendControlReached": False,
            }
        }

        result = evaluate_rate_limits(data, 15)

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["lowestRemainingPercent"], 80)

    def test_run_budget_creates_baseline_and_stops_at_ten_points(self):
        with TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            starting = evaluate_rate_limits(payload(codex_used=57), 15)

            initial = apply_run_budget(starting, baseline, 10)

            self.assertEqual(initial["status"], "pass")
            self.assertEqual(initial["runBudget"]["highestSpentPercent"], 0)
            later = evaluate_rate_limits(payload(codex_used=67), 15)
            stopped = apply_run_budget(later, baseline, 10)

        self.assertEqual(stopped["status"], "abort")
        self.assertEqual(stopped["runBudget"]["highestSpentPercent"], 10)
        self.assertIn("per-run usage budget reached", stopped["blockers"][-1])

    def test_run_budget_fails_closed_if_window_resets(self):
        with TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            apply_run_budget(evaluate_rate_limits(payload(), 15), baseline, 10)
            later = payload()
            later["rateLimitsByLimitId"]["codex"]["primary"]["resetsAt"] += 1

            with self.assertRaisesRegex(UsageGateError, "reset during the run"):
                apply_run_budget(evaluate_rate_limits(later, 15), baseline, 10)


if __name__ == "__main__":
    unittest.main()
