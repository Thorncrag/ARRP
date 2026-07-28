#!/usr/bin/env python3
"""Validate and mark one bounded Elim public-intake reply."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

try:
    from github_disclosure_gate import (
        DisclosureBlocked,
        artifact_from_text,
        require_outbound_bundle,
    )
except ModuleNotFoundError:
    from scripts.github_disclosure_gate import (
        DisclosureBlocked,
        artifact_from_text,
        require_outbound_bundle,
    )

ALLOWED_KEYS = {
    "submission_url",
    "basis_kind",
    "basis_url",
    "action_summary",
    "body",
}
ALLOWED_BASIS_KINDS = {"existing_coverage", "recorded_disposition"}
IDENTITY_PREFIXES = (
    "I'm Elim, an ARRP LLM agent.",
    "I’m Elim, an ARRP LLM agent.",
)
SUBMISSION_PATTERN = re.compile(
    r"^https://github\.com/Thorncrag/ARRP/discussions/\d+"
    r"#discussioncomment-\d+$"
)
URL_PATTERN = re.compile(r"https?://[^\s<>()\]]+")
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]\d{3}[-.\s]\d{4}(?!\d)")
SSN_PATTERN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.I)
PROHIBITED_AUTHORITY_PATTERN = re.compile(
    r"\bI\s+(?:have\s+)?(?:admitted|rejected|approved|endorsed|merged|split|"
    r"retired|deleted|hidden|moderated|published|closed)\b",
    re.I,
)
MARKER_PREFIX = "ARRP-ELIM-REPLY:v1:"


class ReplyValidationError(ValueError):
    """Raised when a proposed public reply exceeds Elim's authority."""


def marker_for_submission(submission_url: str) -> str:
    digest = hashlib.sha256(submission_url.encode("utf-8")).hexdigest()[:20]
    return f"<!-- {MARKER_PREFIX}{digest} -->"


def allowed_basis_url(value: str) -> bool:
    parsed = urlsplit(value)
    if parsed.scheme != "https":
        return False
    if parsed.hostname == "github.com":
        return parsed.path.startswith("/Thorncrag/ARRP/")
    if parsed.hostname == "thorncrag.github.io":
        return parsed.path == "/ARRP" or parsed.path.startswith("/ARRP/")
    return False


def validate_reply(payload: object) -> dict[str, str]:
    if not isinstance(payload, dict):
        raise ReplyValidationError("reply payload must be a JSON object")

    unknown = set(payload) - ALLOWED_KEYS
    missing = ALLOWED_KEYS - set(payload)
    if unknown:
        raise ReplyValidationError(f"unexpected field(s): {', '.join(sorted(unknown))}")
    if missing:
        raise ReplyValidationError(f"missing field(s): {', '.join(sorted(missing))}")

    values: dict[str, str] = {}
    for key in ALLOWED_KEYS:
        value = payload[key]
        if not isinstance(value, str) or not value.strip():
            raise ReplyValidationError(f"{key} must be a nonblank string")
        values[key] = value.strip()

    submission_url = values["submission_url"]
    basis_kind = values["basis_kind"]
    basis_url = values["basis_url"]
    action_summary = values["action_summary"]
    body = values["body"]

    if not SUBMISSION_PATTERN.fullmatch(submission_url):
        raise ReplyValidationError("submission_url must identify one ARRP Discussion comment")
    if basis_kind not in ALLOWED_BASIS_KINDS:
        raise ReplyValidationError("basis_kind must be existing_coverage or recorded_disposition")
    if not allowed_basis_url(basis_url):
        raise ReplyValidationError("basis_url must be an allowlisted public ARRP record")
    if basis_url == submission_url:
        raise ReplyValidationError("basis_url must be distinct from the submission")
    if len(action_summary) > 240:
        raise ReplyValidationError("action_summary exceeds 240 characters")
    if len(body) > 1_600:
        raise ReplyValidationError("body exceeds 1,600 characters")
    if not body.startswith(IDENTITY_PREFIXES):
        raise ReplyValidationError("body must begin by identifying Elim as an ARRP LLM agent")
    if "I reviewed" not in body:
        raise ReplyValidationError("body must state that Elim reviewed the submission")
    if basis_url not in body:
        raise ReplyValidationError("body must link the authoritative basis_url")
    if basis_kind == "recorded_disposition" and not re.search(
        r"\bARRP (?:previously|has previously|already)\b|\bproject(?:'s)? recorded\b",
        body,
        re.I,
    ):
        raise ReplyValidationError("a disposition reply must attribute the prior decision to ARRP")
    if PROHIBITED_AUTHORITY_PATTERN.search(body):
        raise ReplyValidationError("body implies human-reserved disposition authority")
    if MARKER_PREFIX in body or "<!--" in body or "-->" in body:
        raise ReplyValidationError("body may not supply its own HTML or idempotency marker")
    if re.search(r"!\[[^\]]*\]\(", body):
        raise ReplyValidationError("body may not embed images")

    combined = "\n".join((action_summary, body))
    if EMAIL_PATTERN.search(combined):
        raise ReplyValidationError("reply contains an email address")
    if PHONE_PATTERN.search(combined):
        raise ReplyValidationError("reply contains a telephone number")
    if SSN_PATTERN.search(combined):
        raise ReplyValidationError("reply contains an SSN-like value")
    if PRIVATE_KEY_PATTERN.search(combined):
        raise ReplyValidationError("reply contains a private-key marker")

    for url in URL_PATTERN.findall(body):
        cleaned = url.rstrip(".,;:")
        if not allowed_basis_url(cleaned):
            raise ReplyValidationError(f"reply contains a non-ARRP URL: {cleaned}")

    marker = marker_for_submission(submission_url)
    return {
        **values,
        "marker": marker,
        "validated_body": f"{body}\n\n{marker}",
    }


def broker_intent(
    validated: dict[str, str],
    *,
    source_revision: str,
    authority_record: str,
) -> dict[str, object]:
    """Render the exact deterministic broker request; this does not post it."""

    if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        raise ReplyValidationError("source_revision must be a full lowercase Git SHA")
    if not authority_record.startswith("framework/"):
        raise ReplyValidationError("authority_record must be a framework path")
    parsed = urlsplit(validated["submission_url"])
    discussion_number = int(parsed.path.rstrip("/").rsplit("/", 1)[-1])
    comment_id = int(parsed.fragment.rsplit("-", 1)[-1])
    target = json.dumps(
        {
            "discussion_number": discussion_number,
            "reply_to_comment_id": comment_id,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    try:
        require_outbound_bundle(
            [
                artifact_from_text(
                    f"github/discussion/{discussion_number}/reply/{comment_id}",
                    "arrp-semantic-broker",
                    validated["validated_body"],
                    family_id="github-discussion-text",
                )
            ],
            operation="github_api_mutation",
            source_revision=source_revision,
        )
    except DisclosureBlocked as error:
        raise ReplyValidationError(str(error)) from error
    return {
        "operation_type": "post_discussion_reply",
        "repository": "Thorncrag/ARRP",
        "target_node_or_number": target,
        "source_revision": source_revision,
        "authority_record": authority_record,
        "expected_old_state": {"reply_absent": validated["marker"]},
        "new_state_or_content": {"body": validated["validated_body"]},
        "idempotency_key": validated["marker"],
        "privacy_class": "public",
        "human_reserved": False,
        "rollback_or_correction": "post a transparent correction; never silently edit history",
        "readback_contract": "exactly_one_discussion_reply",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a proposed Elim Discussion reply JSON file."
    )
    parser.add_argument("payload", type=Path, help="Path to the proposed reply JSON")
    parser.add_argument(
        "--body-only",
        action="store_true",
        help="Print only the exact validated body to post",
    )
    parser.add_argument("--broker-intent", action="store_true")
    parser.add_argument("--source-revision")
    parser.add_argument(
        "--authority-record",
        default="framework/project/workflows/public-input-review.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
        result = validate_reply(payload)
    except (OSError, json.JSONDecodeError, ReplyValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.body_only and args.broker_intent:
        print("ERROR: select only one output mode", file=sys.stderr)
        return 1
    if args.broker_intent:
        if not args.source_revision:
            print("ERROR: --source-revision is required with --broker-intent", file=sys.stderr)
            return 1
        try:
            result = broker_intent(
                result,
                source_revision=args.source_revision,
                authority_record=args.authority_record,
            )
        except ReplyValidationError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2, sort_keys=True))
    elif args.body_only:
        print(result["validated_body"])
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
