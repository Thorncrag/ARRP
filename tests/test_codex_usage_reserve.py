import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.check_codex_usage_reserve import (
    RESET_TIME_JITTER_SECONDS,
    UsageGateError,
    apply_run_budget,
    evaluate_rate_limits,
    read_usage_with_window_confirmation,
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

    def test_run_budget_marks_ten_point_soft_target_with_room_to_continue(self):
        with TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            starting = evaluate_rate_limits(payload(codex_used=20), 15)

            initial = apply_run_budget(starting, baseline, 10)

            self.assertEqual(initial["status"], "pass")
            self.assertEqual(initial["runBudget"]["highestSpentPercent"], 0)
            later = evaluate_rate_limits(payload(codex_used=30), 15)
            continued = apply_run_budget(later, baseline, 10)

        self.assertEqual(continued["status"], "pass")
        self.assertEqual(continued["runBudget"]["highestSpentPercent"], 10)
        self.assertTrue(continued["runBudget"]["softTargetReached"])
        self.assertEqual(continued["runBudget"]["reserveBufferFloorPercent"], 25)

    def test_soft_target_stops_within_reserve_buffer(self):
        with TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            apply_run_budget(evaluate_rate_limits(payload(codex_used=65), 15), baseline, 10)
            later = evaluate_rate_limits(payload(codex_used=75), 15)
            stopped = apply_run_budget(later, baseline, 10)

        self.assertEqual(stopped["status"], "abort")
        self.assertEqual(stopped["lowestRemainingPercent"], 25)
        self.assertIn("soft per-run target reached", stopped["blockers"][-1])

    def test_run_budget_accepts_small_reset_time_jitter(self):
        with TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            apply_run_budget(evaluate_rate_limits(payload(), 15), baseline, 10)
            later = payload()
            later["rateLimitsByLimitId"]["codex"]["primary"][
                "resetsAt"
            ] += RESET_TIME_JITTER_SECONDS

            result = apply_run_budget(evaluate_rate_limits(later, 15), baseline, 10)

        self.assertEqual(result["status"], "pass")
        self.assertFalse(result["runBudget"]["softTargetReached"])

    def test_run_budget_fails_closed_if_window_changes_materially(self):
        with TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            apply_run_budget(evaluate_rate_limits(payload(), 15), baseline, 10)
            later = payload()
            later["rateLimitsByLimitId"]["codex"]["primary"][
                "resetsAt"
            ] += RESET_TIME_JITTER_SECONDS + 1

            with self.assertRaisesRegex(UsageGateError, "changed materially"):
                apply_run_budget(evaluate_rate_limits(later, 15), baseline, 10)

    def test_transient_material_window_change_is_rechecked(self):
        with TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            apply_run_budget(evaluate_rate_limits(payload(), 15), baseline, 10)
            responses = [payload(), payload()]
            responses[0]["rateLimitsByLimitId"]["codex"]["primary"]["resetsAt"] += 60

            result = read_usage_with_window_confirmation(
                lambda: responses.pop(0),
                15,
                baseline,
                10,
                recheck_delay_seconds=0,
            )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["windowChangeRechecks"], 1)

    def test_persistent_material_window_change_fails_closed(self):
        with TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            apply_run_budget(evaluate_rate_limits(payload(), 15), baseline, 10)

            def changed_payload():
                data = payload()
                data["rateLimitsByLimitId"]["codex"]["primary"]["resetsAt"] += 60
                return data

            with self.assertRaisesRegex(UsageGateError, "changed materially"):
                read_usage_with_window_confirmation(
                    changed_payload,
                    15,
                    baseline,
                    10,
                    recheck_delay_seconds=0,
                )

    def test_reserve_hit_is_immediate_even_after_window_change_signal(self):
        with TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            apply_run_budget(evaluate_rate_limits(payload(), 15), baseline, 10)
            responses = [payload(), payload(codex_used=85)]
            responses[0]["rateLimitsByLimitId"]["codex"]["primary"]["resetsAt"] += 60

            result = read_usage_with_window_confirmation(
                lambda: responses.pop(0),
                15,
                baseline,
                10,
                recheck_delay_seconds=0,
            )

        self.assertEqual(result["status"], "abort")
        self.assertIn("codex primary: 15% remaining", result["blockers"])


if __name__ == "__main__":
    unittest.main()
