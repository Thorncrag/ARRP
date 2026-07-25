import unittest

from scripts.source_monitor_recommendations import (
    RecommendationError,
    exact_head_recommendation,
    parse_source_monitor_recommendations,
)


HEAD = "a" * 40


def recommendation_entry(
    *,
    recommendation_id: str = "SMR-20260725-PR9",
    action_owner: str = "Human",
    human_question: str = "Approve closing PR #9?",
    head_revision: str = HEAD,
) -> str:
    return f"""
## 2026-07-25T22:17:39Z — Repository review recommendation {recommendation_id}

- Recommendation ID: `{recommendation_id}`
- Recorded at: `2026-07-25T22:17:39Z`
- Reviewer: Elim
- Pull request number: `9`
- Pull request URL: `https://github.com/Thorncrag/ARRP/pull/9`
- Head revision: `{head_revision}`
- Proposal event ID: `SDE-1234567890ABCDEF12345678`
- Recommended disposition: Close without merge and regenerate.
- Rationale: The complete head is not accurately itemized.
- Affected records: 10 directive records.
- Confidence and uncertainty: High confidence in the mismatch; routing remains reviewable.
- Action owner: {action_owner}
- Human question: {human_question}
- Reassessment trigger: Any head change invalidates this recommendation.
"""


class SourceMonitorRecommendationTests(unittest.TestCase):
    def test_parses_and_matches_only_the_exact_head(self) -> None:
        records = parse_source_monitor_recommendations(recommendation_entry())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["pull_request_number"], 9)
        self.assertEqual(records[0]["action_owner"], "Human")
        self.assertIs(
            exact_head_recommendation(records, 9, HEAD),
            records[0],
        )
        self.assertIsNone(exact_head_recommendation(records, 9, "b" * 40))

    def test_latest_exact_head_recommendation_wins(self) -> None:
        earlier = recommendation_entry()
        later = recommendation_entry(
            recommendation_id="SMR-20260725-PR9B",
            action_owner="None",
            human_question="None",
        ).replace(
            "2026-07-25T22:17:39Z",
            "2026-07-25T22:18:39Z",
        )
        records = parse_source_monitor_recommendations(earlier + later)
        match = exact_head_recommendation(records, 9, HEAD)
        self.assertEqual(match["id"], "SMR-20260725-PR9B")
        self.assertEqual(match["action_owner"], "None")

    def test_human_owner_requires_an_exact_question(self) -> None:
        with self.assertRaisesRegex(
            RecommendationError, "assigns a human without an exact question"
        ):
            parse_source_monitor_recommendations(
                recommendation_entry(human_question="None")
            )

    def test_nonhuman_owner_cannot_create_a_human_question(self) -> None:
        with self.assertRaisesRegex(
            RecommendationError, "human question without human ownership"
        ):
            parse_source_monitor_recommendations(
                recommendation_entry(action_owner="Elim")
            )


if __name__ == "__main__":
    unittest.main()
