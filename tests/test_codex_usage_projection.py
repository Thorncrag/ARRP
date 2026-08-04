from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone

from scripts.codex_usage_projection import (
    MAX_ANOMALIES,
    MAX_HISTORY_ITEMS,
    MAX_RESET_WINDOWS,
    CodexUsageProjectionError,
    canonical_payload_digest,
    reset_identity,
    unavailable_projection,
    validate_projection,
)


CHECKED_AT = datetime(2026, 7, 29, 20, 20, tzinfo=timezone.utc)
RESET_AT = 1785908741
RESET_ID = reset_identity(10080, RESET_AT)


def current_projection() -> dict[str, object]:
    return {
        "schema_version": 2,
        "projection_id": "codex-usage",
        "producer_id": "owner-local-codex-usage-sampler",
        "sampler_cadence_seconds": 1800,
        "generated_at": "2026-07-29T20:20:00Z",
        "trustworthy_through": "2026-07-29T20:47:00Z",
        "availability": "current",
        "completeness": "complete",
        "reason_code": None,
        "current_through": "2026-07-29T20:17:00Z",
        "current": {
            "observed_at": "2026-07-29T20:17:00Z",
            "plan_type": "pro",
            "used_percent": 28,
            "remaining_percent": 72,
            "window_minutes": 10080,
            "resets_at": RESET_AT,
            "reset_identity": RESET_ID,
        },
        "history": [
            {
                "observed_at": "2026-07-29T19:47:00Z",
                "event_type": "baseline",
                "plan_type": "pro",
                "used_percent": 27,
                "remaining_percent": 73,
                "window_minutes": 10080,
                "resets_at": RESET_AT,
                "reset_identity": RESET_ID,
            }
        ],
        "reset_windows": [
            {
                "reset_identity": RESET_ID,
                "first_observed": "2026-07-29T19:47:00Z",
                "last_observed": "2026-07-29T20:17:00Z",
                "window_minutes": 10080,
                "resets_at": RESET_AT,
                "plan_types": ["pro"],
                "min_used_percent": 27,
                "max_used_percent": 28,
                "observation_count": 2,
                "material": True,
            }
        ],
        "anomalies": [],
        "estimates": {
            "available": True,
            "budget_available": True,
            "budget_reason_code": None,
            "burn_rate_available": False,
            "burn_rate_reason_code": "insufficient_observation_coverage",
            "coverage_hours": 0.5,
            "sample_count": 2,
            "average_percent_per_day": None,
            "projected_exhaustion_at": None,
            "remaining_percent_per_day_budget": 10.1,
            "confidence": "unavailable",
        },
    }


class CodexUsageProjectionTests(unittest.TestCase):
    def test_reset_identity_normalizes_provider_second_drift(self) -> None:
        minute = 2_976_9490
        self.assertEqual(reset_identity(10080, minute * 60 - 2), f"10080:{minute}")
        self.assertEqual(reset_identity(10080, minute * 60 - 1), f"10080:{minute}")
        self.assertEqual(reset_identity(10080, minute * 60), f"10080:{minute}")

    def assert_invalid(self, payload: object) -> None:
        with self.assertRaises(CodexUsageProjectionError):
            validate_projection(payload, now=CHECKED_AT)

    def test_current_projection_is_valid_through_exact_boundary(self) -> None:
        payload = current_projection()
        self.assertEqual(
            validate_projection(payload, now=CHECKED_AT),
            ("current", True),
        )
        self.assertEqual(
            validate_projection(
                payload,
                now=datetime(2026, 7, 29, 20, 47, tzinfo=timezone.utc),
            ),
            ("current", True),
        )
        with self.assertRaisesRegex(CodexUsageProjectionError, "stale"):
            validate_projection(
                payload,
                now=datetime(
                    2026, 7, 29, 20, 47, 0, 1, tzinfo=timezone.utc
                ),
            )

    def test_currentness_and_reset_identity_are_not_inferred(self) -> None:
        for field, value in (
            ("trustworthy_through", "2026-07-29T20:48:00Z"),
            ("current_through", "2026-07-29T20:16:00Z"),
        ):
            payload = current_projection()
            payload[field] = value
            self.assert_invalid(payload)
        payload = current_projection()
        payload["current"]["reset_identity"] = "10080:1"
        self.assert_invalid(payload)
        payload = current_projection()
        payload["current"]["window_minutes"] = 7200
        self.assert_invalid(payload)

    def test_unknown_sensitive_or_credit_fields_fail_closed(self) -> None:
        payload = current_projection()
        payload["current"]["credit_balance"] = "0"
        self.assert_invalid(payload)
        payload = current_projection()
        payload["source_path"] = "/Users/example/private"
        self.assert_invalid(payload)
        payload = current_projection()
        payload["current"]["plan_type"] = "Benjamin@example.com"
        self.assert_invalid(payload)

    def test_chronology_identity_and_bounds_fail_closed(self) -> None:
        payload = current_projection()
        payload["history"].append(copy.deepcopy(payload["history"][0]))
        self.assert_invalid(payload)
        payload = current_projection()
        payload["history"][0]["observed_at"] = "2026-07-29T20:18:00Z"
        payload["history"].append(
            {
                **copy.deepcopy(payload["history"][0]),
                "observed_at": "2026-07-29T20:10:00Z",
            }
        )
        self.assert_invalid(payload)
        for field, maximum, item in (
            ("history", MAX_HISTORY_ITEMS, current_projection()["history"][0]),
            (
                "reset_windows",
                MAX_RESET_WINDOWS,
                current_projection()["reset_windows"][0],
            ),
            (
                "anomalies",
                MAX_ANOMALIES,
                {
                    "anomaly_id": "conflicting-reset-10080-29765144-29765145",
                    "type": "conflicting_reset_identity",
                    "observed_at": "2026-07-29T20:00:00Z",
                    "observed_reset_identity": "10080:29765144",
                    "current_reset_identity": RESET_ID,
                },
            ),
        ):
            payload = current_projection()
            payload[field] = [copy.deepcopy(item) for _ in range(maximum + 1)]
            self.assert_invalid(payload)

    def test_budget_and_burn_estimates_are_independently_typed(self) -> None:
        payload = current_projection()
        payload["estimates"].update(
            {
                "budget_available": False,
                "budget_reason_code": "budget_input_unavailable",
                "burn_rate_available": True,
                "burn_rate_reason_code": None,
                "average_percent_per_day": 4.5,
                "projected_exhaustion_at": "2026-08-03T12:00:00Z",
                "remaining_percent_per_day_budget": None,
                "confidence": "medium",
            }
        )
        self.assertEqual(
            validate_projection(payload, now=CHECKED_AT),
            ("current", True),
        )
        payload["estimates"]["budget_reason_code"] = None
        self.assert_invalid(payload)

    def test_unavailable_projection_has_one_exact_safe_shape(self) -> None:
        payload = unavailable_projection(
            "source_unavailable",
            generated_at=CHECKED_AT,
        )
        self.assertEqual(
            validate_projection(payload, now=CHECKED_AT),
            ("unavailable", False),
        )
        payload["history"] = [current_projection()["history"][0]]
        self.assert_invalid(payload)

    def test_semantic_digest_is_order_stable_and_value_sensitive(self) -> None:
        payload = current_projection()
        reordered = dict(reversed(list(payload.items())))
        self.assertEqual(
            canonical_payload_digest(payload),
            canonical_payload_digest(reordered),
        )
        numeric = copy.deepcopy(payload)
        numeric["current"]["used_percent"] = 28.0
        self.assertEqual(
            canonical_payload_digest(payload),
            canonical_payload_digest(numeric),
        )
        changed = copy.deepcopy(payload)
        changed["current"]["used_percent"] = 29
        changed["current"]["remaining_percent"] = 71
        self.assertNotEqual(
            canonical_payload_digest(payload),
            canonical_payload_digest(changed),
        )


if __name__ == "__main__":
    unittest.main()
