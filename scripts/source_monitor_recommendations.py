#!/usr/bin/env python3
"""Parse exact-revision repository review recommendations from the source log."""

from __future__ import annotations

import re
from typing import Any


RECOMMENDATION_HEADING = "Repository review recommendation"
PR_URL_RE = re.compile(r"^https://github\.com/Thorncrag/ARRP/pull/([1-9][0-9]*)$")
REVISION_RE = re.compile(r"^[a-f0-9]{40}$")
EVENT_ID_RE = re.compile(r"^SDE-[A-F0-9]{24}$")
RECOMMENDATION_ID_RE = re.compile(r"^SMR-[A-Z0-9-]{6,80}$")
ACTION_OWNERS = {"Elim", "Human", "None"}


class RecommendationError(ValueError):
    """A malformed recommendation that must never suppress agent review."""


def _sections(content: str) -> list[tuple[str, str]]:
    headings = list(re.finditer(r"^##\s+(.+?)\s*$", content, re.MULTILINE))
    return [
        (
            match.group(1).strip(),
            content[
                match.end() : headings[index + 1].start()
                if index + 1 < len(headings)
                else len(content)
            ].strip(),
        )
        for index, match in enumerate(headings)
    ]


def _plain(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        value = value[1:-1]
    return value.strip()


def _fields(body: str) -> dict[str, str]:
    return {
        match.group(1).strip(): _plain(match.group(2))
        for match in re.finditer(r"^-\s+([^:\n]+):\s*(.+)$", body, re.MULTILINE)
    }


def _required(fields: dict[str, str], name: str, recommendation_id: str) -> str:
    value = fields.get(name, "").strip()
    if not value:
        raise RecommendationError(
            f"{recommendation_id or 'repository recommendation'} lacks {name}"
        )
    return value


def parse_source_monitor_recommendations(content: str) -> list[dict[str, Any]]:
    """Return validated recommendation records in log order.

    A record binds its analysis to one exact pull-request head. A later head
    revision therefore cannot inherit or reuse the recommendation.
    """

    recommendations: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for heading, body in _sections(content):
        if RECOMMENDATION_HEADING.casefold() not in heading.casefold():
            continue
        fields = _fields(body)
        recommendation_id = _required(fields, "Recommendation ID", "")
        if not RECOMMENDATION_ID_RE.fullmatch(recommendation_id):
            raise RecommendationError(
                f"invalid repository recommendation ID: {recommendation_id}"
            )
        if recommendation_id in seen_ids:
            raise RecommendationError(
                f"duplicated repository recommendation ID: {recommendation_id}"
            )
        seen_ids.add(recommendation_id)
        recorded_at = _required(fields, "Recorded at", recommendation_id)
        reviewer = _required(fields, "Reviewer", recommendation_id)
        pull_request_url = _required(fields, "Pull request URL", recommendation_id)
        url_match = PR_URL_RE.fullmatch(pull_request_url)
        if not url_match:
            raise RecommendationError(
                f"{recommendation_id} has an invalid pull-request URL"
            )
        pull_request_number = int(
            _required(fields, "Pull request number", recommendation_id)
        )
        if pull_request_number != int(url_match.group(1)):
            raise RecommendationError(
                f"{recommendation_id} pull-request number and URL disagree"
            )
        head_revision = _required(fields, "Head revision", recommendation_id)
        if not REVISION_RE.fullmatch(head_revision):
            raise RecommendationError(
                f"{recommendation_id} has an invalid head revision"
            )
        event_id = _required(fields, "Proposal event ID", recommendation_id)
        if not EVENT_ID_RE.fullmatch(event_id):
            raise RecommendationError(
                f"{recommendation_id} has an invalid proposal event ID"
            )
        action_owner = _required(fields, "Action owner", recommendation_id)
        if action_owner not in ACTION_OWNERS:
            raise RecommendationError(
                f"{recommendation_id} has an invalid action owner"
            )
        human_question = _required(fields, "Human question", recommendation_id)
        if action_owner == "Human" and human_question.casefold() == "none":
            raise RecommendationError(
                f"{recommendation_id} assigns a human without an exact question"
            )
        if action_owner != "Human" and human_question.casefold() != "none":
            raise RecommendationError(
                f"{recommendation_id} records a human question without human ownership"
            )
        recommendations.append(
            {
                "id": recommendation_id,
                "recorded_at": recorded_at,
                "reviewer": reviewer,
                "pull_request_number": pull_request_number,
                "pull_request_url": pull_request_url,
                "head_revision": head_revision,
                "proposal_event_id": event_id,
                "recommendation": _required(
                    fields, "Recommended disposition", recommendation_id
                ),
                "rationale": _required(fields, "Rationale", recommendation_id),
                "affected_records": _required(
                    fields, "Affected records", recommendation_id
                ),
                "confidence": _required(
                    fields, "Confidence and uncertainty", recommendation_id
                ),
                "action_owner": action_owner,
                "human_question": human_question,
                "reassessment_trigger": _required(
                    fields, "Reassessment trigger", recommendation_id
                ),
                "heading": heading,
            }
        )
    return recommendations


def exact_head_recommendation(
    recommendations: list[dict[str, Any]],
    pull_request_number: int,
    head_revision: str,
) -> dict[str, Any] | None:
    """Return the latest recommendation for one exact open proposal revision."""

    matches = [
        record
        for record in recommendations
        if record["pull_request_number"] == pull_request_number
        and record["head_revision"] == head_revision
    ]
    if not matches:
        return None
    return max(matches, key=lambda record: str(record["recorded_at"]))
