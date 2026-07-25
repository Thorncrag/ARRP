#!/usr/bin/env python3
"""Publish one immutable structured event to the generated data branch.

Existing identical content is a successful no-op. Existing different content
fails closed; this tool never updates or deletes an immutable event and never
force-pushes a branch.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from source_domain_events import data_path, read_json, validate_event
except ModuleNotFoundError:  # Imported as ``scripts.publish_immutable_data_file`` in tests.
    from scripts.source_domain_events import data_path, read_json, validate_event


API_ROOT = "https://api.github.com"
USER_AGENT = "ARRP-immutable-source-event-publisher/1.0"
REMOTE_PATH_RE = re.compile(
    r"^source-domain-events/(proposed|accepted)/"
    r"(case-monitor-bot|presidential-directives-bot|source-checker-bot)/"
    r"SDE-[A-F0-9]{24}\.json$"
)


class PublishError(RuntimeError):
    """An immutable data publication failure."""


def validate_inputs(
    *,
    repository: str,
    branch: str,
    local_file: Path,
    remote_path: str,
) -> bytes:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise PublishError("repository must use the owner/name form")
    if branch != "project-console-data":
        raise PublishError("immutable source events publish only to project-console-data")
    if not REMOTE_PATH_RE.fullmatch(remote_path) or ".." in Path(remote_path).parts:
        raise PublishError("invalid immutable source-event path")
    content = local_file.read_bytes()
    if not content or len(content) > 262_144:
        raise PublishError("immutable source event must be 1-262144 bytes")
    event = read_json(local_file)
    validate_event(event)
    if data_path(event) != remote_path:
        raise PublishError("remote path does not match the source-domain event identity")
    return content


def api_request(
    token: str,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    allow_not_found: bool = False,
) -> dict[str, Any] | None:
    if not url.startswith(API_ROOT + "/repos/"):
        raise PublishError("refusing a non-GitHub API endpoint")
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if allow_not_found and exc.code == 404:
            return None
        # Never copy an API response body into Actions output or logs.
        raise PublishError(f"GitHub API request failed with HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise PublishError("GitHub API request failed before receiving a response") from exc


def contents_url(repository: str, remote_path: str, branch: str) -> str:
    encoded_path = urllib.parse.quote(remote_path, safe="/")
    encoded_ref = urllib.parse.quote(branch, safe="")
    return f"{API_ROOT}/repos/{repository}/contents/{encoded_path}?ref={encoded_ref}"


def create_url(repository: str, remote_path: str) -> str:
    encoded_path = urllib.parse.quote(remote_path, safe="/")
    return f"{API_ROOT}/repos/{repository}/contents/{encoded_path}"


def decode_existing(payload: dict[str, Any]) -> bytes:
    if payload.get("type") != "file" or payload.get("encoding") != "base64":
        raise PublishError("existing immutable path is not a base64 GitHub file")
    content = payload.get("content")
    if not isinstance(content, str):
        raise PublishError("existing immutable event has no readable content")
    try:
        return base64.b64decode(content, validate=False)
    except ValueError as exc:
        raise PublishError("existing immutable event has invalid base64 content") from exc


def publish(
    *,
    repository: str,
    branch: str,
    local_file: Path,
    remote_path: str,
    token: str,
    attempts: int = 3,
) -> str:
    content = validate_inputs(
        repository=repository,
        branch=branch,
        local_file=local_file,
        remote_path=remote_path,
    )
    get_url = contents_url(repository, remote_path, branch)
    for attempt in range(attempts):
        existing = api_request(token, "GET", get_url, allow_not_found=True)
        if existing is not None:
            if decode_existing(existing) == content:
                return "unchanged"
            raise PublishError(
                "immutable source-event path already exists with different content"
            )
        try:
            api_request(
                token,
                "PUT",
                create_url(repository, remote_path),
                {
                    "message": f"Preserve source-domain event {local_file.stem}",
                    "content": base64.b64encode(content).decode("ascii"),
                    "branch": branch,
                },
            )
            return "created"
        except PublishError:
            if attempt + 1 >= attempts:
                raise
            # A concurrent writer may have advanced the data branch. Re-read the
            # exact immutable path; never overwrite it.
            time.sleep(0.25 * (attempt + 1))
    raise PublishError("immutable source-event publication did not complete")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", default="project-console-data")
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--path", required=True)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.environ.get(args.token_env, "").strip()
    if not token:
        raise PublishError(f"missing {args.token_env} for immutable event publication")
    result = publish(
        repository=args.repository,
        branch=args.branch,
        local_file=args.file,
        remote_path=args.path,
        token=token,
    )
    print(f"Immutable source-domain event publication: {result}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, PublishError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
