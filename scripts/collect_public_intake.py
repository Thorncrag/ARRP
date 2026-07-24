#!/usr/bin/env python3
"""Collect privacy-minimized pending ARRP Discussion intake events."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


API = "https://api.github.com/graphql"
ROUTE = re.compile(r"<!--\s*ARRP-INTAKE-ROUTE:([A-Z0-9:_-]+)\s*-->")
SUBMISSION = re.compile(r"<!--\s*ARRP-INTAKE-SUBMISSION:([A-Za-z0-9-]+)\s*-->")
ELIGIBLE = "<!-- ARRP-INTAKE-ELIGIBLE:1 -->"
REPLY_PREFIX = "ARRP-ELIM-REPLY:v1:"
QUERY = """
query Intake($owner:String!, $name:String!) {
  repository(owner:$owner, name:$name) {
    discussions(first:100, orderBy:{field:CREATED_AT,direction:ASC}) {
      pageInfo { hasNextPage }
      nodes {
        url
        body
        comments(first:100) {
          pageInfo { hasNextPage }
          nodes {
            id
            url
            createdAt
            body
            replies(first:20) {
              pageInfo { hasNextPage }
              nodes { body }
            }
          }
        }
      }
    }
  }
}
"""


def reply_marker(url: str) -> str:
    return REPLY_PREFIX + hashlib.sha256(url.encode()).hexdigest()[:20]


def load_ledger(path: Path | None) -> set[str]:
    urls: set[str] = set()
    if path is None or not path.is_file():
        return urls
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"intake ledger line {number} is invalid") from exc
        url = record.get("discussion_url")
        if isinstance(url, str):
            urls.add(url)
    return urls


def collect(payload: dict[str, Any], prior: dict[str, Any], ledger: set[str]) -> dict[str, Any]:
    repository = (payload.get("data") or {}).get("repository")
    if not isinstance(repository, dict):
        raise ValueError("GitHub response lacks repository data")
    discussions = repository.get("discussions")
    if not isinstance(discussions, dict) or not isinstance(discussions.get("nodes"), list):
        raise ValueError("GitHub response lacks Discussion nodes")
    if (discussions.get("pageInfo") or {}).get("hasNextPage"):
        raise ValueError("more than 100 canonical Discussions requires reviewed pagination")
    prior_states = {
        str(item.get("id")): str(item.get("state"))
        for item in prior.get("items", [])
        if item.get("id")
    }
    items = []
    for discussion in discussions["nodes"]:
        route_match = ROUTE.search(str(discussion.get("body") or ""))
        if not route_match:
            continue
        comments = discussion.get("comments")
        if not isinstance(comments, dict) or not isinstance(comments.get("nodes"), list):
            raise ValueError("canonical Discussion lacks comment nodes")
        if (comments.get("pageInfo") or {}).get("hasNextPage"):
            raise ValueError("more than 100 intake comments requires reviewed pagination")
        for comment in comments["nodes"]:
            body = str(comment.get("body") or "")
            submission = SUBMISSION.search(body)
            if ELIGIBLE not in body or not submission:
                continue
            replies = comment.get("replies")
            if not isinstance(replies, dict) or not isinstance(replies.get("nodes"), list):
                raise ValueError("eligible intake comment lacks reply nodes")
            if (replies.get("pageInfo") or {}).get("hasNextPage"):
                raise ValueError("more than 20 replies requires reviewed pagination")
            url = str(comment.get("url") or "")
            identity = str(comment.get("id") or "")
            created = str(comment.get("createdAt") or "")
            if not url or not identity or not created:
                raise ValueError("eligible intake comment lacks stable identity metadata")
            replied = any(
                reply_marker(url) in str(reply.get("body") or "")
                for reply in replies["nodes"]
            )
            processed = replied or url in ledger or prior_states.get(identity) == "processed"
            items.append(
                {
                    "id": identity,
                    "url": url,
                    "created_at": created,
                    "content_hash": "sha256:" + hashlib.sha256(body.encode()).hexdigest(),
                    "route": route_match.group(1),
                    "submission_id": submission.group(1),
                    "state": "processed" if processed else "pending",
                }
            )
    items.sort(key=lambda item: (item["created_at"], item["id"]))
    pending = [item for item in items if item["state"] == "pending"]
    processed = [item for item in items if item["state"] == "processed"]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "pending": bool(pending),
        "last_processed_id": processed[-1]["id"] if processed else None,
        "counts": {
            "eligible": len(items),
            "pending": len(pending),
            "processed": len(processed),
        },
        "items": items[-500:],
        "content_included": False,
    }


def live_payload(token: str) -> dict[str, Any]:
    body = json.dumps(
        {
            "query": QUERY,
            "variables": {"owner": "Thorncrag", "name": "ARRP"},
        }
    ).encode()
    request = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "ARRP-public-intake-collector/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        messages = sorted(
            {
                str(error.get("message") or "unspecified GraphQL error")
                for error in payload["errors"]
                if isinstance(error, dict)
            }
        )
        raise ValueError("GitHub GraphQL returned errors: " + "; ".join(messages))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--prior", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--review-ledger", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get("GH_TOKEN", "")
    if args.fixture:
        payload = json.loads(args.fixture.read_text())
    elif token:
        payload = live_payload(token)
    else:
        raise SystemExit("public-intake collector requires GH_TOKEN or --fixture")
    prior = json.loads(args.prior.read_text()) if args.prior and args.prior.is_file() else {}
    processed = load_ledger(args.ledger) | load_ledger(args.review_ledger)
    result = collect(payload, prior, processed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, urllib.error.URLError, ValueError) as exc:
        raise SystemExit(f"public-intake collector: {exc}")
