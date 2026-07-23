import unittest
from pathlib import Path

from scripts.validate_elim_discussion_reply import (
    ReplyValidationError,
    marker_for_submission,
    validate_reply,
)


SUBMISSION_URL = (
    "https://github.com/Thorncrag/ARRP/discussions/12"
    "#discussioncomment-345"
)
BASIS_URL = "https://github.com/Thorncrag/ARRP/blob/main/areas/CIV/issues/CIV-010.md"
ROOT = Path(__file__).resolve().parents[1]


def valid_payload() -> dict[str, str]:
    return {
        "submission_url": SUBMISSION_URL,
        "basis_kind": "existing_coverage",
        "basis_url": BASIS_URL,
        "action_summary": "Identified existing coverage in CIV-010.",
        "body": (
            "I'm Elim, an ARRP LLM agent. I reviewed this submission and "
            "identified existing ARRP coverage in [CIV-010]"
            f"({BASIS_URL}). I have linked that record for the contributor and "
            "later readers; I have not made a new admission or disposition."
        ),
    }


class ElimDiscussionReplyValidationTest(unittest.TestCase):
    def test_valid_existing_coverage_reply_gets_stable_marker(self) -> None:
        result = validate_reply(valid_payload())

        self.assertEqual(result["marker"], marker_for_submission(SUBMISSION_URL))
        self.assertTrue(result["validated_body"].endswith(result["marker"]))

    def test_recorded_disposition_must_be_attributed_to_project(self) -> None:
        payload = valid_payload()
        payload["basis_kind"] = "recorded_disposition"

        with self.assertRaisesRegex(ReplyValidationError, "attribute"):
            validate_reply(payload)

        payload["body"] = (
            "I'm Elim, an ARRP LLM agent. I reviewed this submission. "
            "ARRP previously recorded its disposition in "
            f"[the Horizon log]({BASIS_URL}); I am linking that existing "
            "project decision rather than making a new one."
        )
        self.assertEqual(validate_reply(payload)["basis_kind"], "recorded_disposition")

    def test_private_or_non_arrp_content_is_rejected(self) -> None:
        payload = valid_payload()
        payload["body"] += " Contact reader@example.org."
        with self.assertRaisesRegex(ReplyValidationError, "email"):
            validate_reply(payload)

        payload = valid_payload()
        payload["body"] += " See https://example.org/details."
        with self.assertRaisesRegex(ReplyValidationError, "non-ARRP URL"):
            validate_reply(payload)

    def test_human_reserved_authority_claim_is_rejected(self) -> None:
        payload = valid_payload()
        payload["body"] = (
            "I'm Elim, an ARRP LLM agent. I reviewed this submission and "
            f"I rejected it. See [the record]({BASIS_URL})."
        )

        with self.assertRaisesRegex(ReplyValidationError, "human-reserved"):
            validate_reply(payload)

    def test_submission_must_be_one_discussion_comment(self) -> None:
        payload = valid_payload()
        payload["submission_url"] = "https://github.com/Thorncrag/ARRP/discussions/12"

        with self.assertRaisesRegex(ReplyValidationError, "Discussion comment"):
            validate_reply(payload)

    def test_governing_records_share_the_same_limited_authority(self) -> None:
        intake = (ROOT / "framework" / "INTAKE_AGENT_PROCESS.md").read_text()
        elim = (ROOT / "framework" / "agents" / "ELIM.md").read_text()
        participation = (ROOT / "participate" / "README.md").read_text()
        security = (ROOT / "participate" / "SECURITY.md").read_text()

        for content in (intake, elim, participation, security):
            self.assertIn("informative", content)
            self.assertIn("reply", content)
            self.assertIn("preliminary", content.lower())
        self.assertIn("validate_elim_discussion_reply.py", intake)
        self.assertIn("validate_elim_discussion_reply.py", elim)
        self.assertIn("Human approval remains required before promotion", intake)


if __name__ == "__main__":
    unittest.main()
