#!/usr/bin/env python3
"""Publish generated Project Console progress data to a dedicated GitHub branch."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


API_ROOT = "https://api.github.com"
USER_AGENT = "ARRP-project-console-progress-publisher/1.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    return parser.parse_args()


def api_request(
    token: str,
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    allow_not_found: bool = False,
) -> Optional[Dict[str, Any]]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        API_ROOT + path,
        data=body,
        method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2026-03-10",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status == 204:
                return {}
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if allow_not_found and exc.code == 404:
            return None
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError("GitHub REST request failed: {} {}".format(exc.code, detail))


def collect_files(source: Path) -> List[Tuple[str, str]]:
    if not source.is_dir():
        raise RuntimeError("Progress-data source directory does not exist: {}".format(source))
    files = []
    for path in sorted(candidate for candidate in source.rglob("*") if candidate.is_file()):
        relative = path.relative_to(source).as_posix()
        files.append((relative, path.read_text(encoding="utf-8")))
    if not files:
        raise RuntimeError("Progress-data source directory is empty: {}".format(source))
    return files


def get_ref_path(repository: str, branch: str) -> str:
    return "/repos/{}/git/ref/heads/{}".format(repository, urllib.parse.quote(branch, safe=""))


def update_ref_path(repository: str, branch: str) -> str:
    return "/repos/{}/git/refs/heads/{}".format(repository, urllib.parse.quote(branch, safe=""))


def publish(source: Path, repository: str, branch: str, token: str) -> str:
    files = collect_files(source)
    existing = api_request(token, "GET", get_ref_path(repository, branch), allow_not_found=True)
    parents = [str((existing.get("object") or {})["sha"])] if existing else []

    tree_entries = []
    for path, content in files:
        blob = api_request(
            token,
            "POST",
            "/repos/{}/git/blobs".format(repository),
            {"content": content, "encoding": "utf-8"},
        ) or {}
        tree_entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})

    tree = api_request(
        token,
        "POST",
        "/repos/{}/git/trees".format(repository),
        {"tree": tree_entries},
    ) or {}
    progress_data = json.loads((source / "progress.json").read_text(encoding="utf-8"))
    commit = api_request(
        token,
        "POST",
        "/repos/{}/git/commits".format(repository),
        {
            "message": "Refresh Project Console progress {}".format(progress_data["asOf"]),
            "tree": tree["sha"],
            "parents": parents,
        },
    ) or {}
    commit_sha = str(commit["sha"])

    if existing:
        api_request(
            token,
            "PATCH",
            update_ref_path(repository, branch),
            {"sha": commit_sha, "force": False},
        )
    else:
        api_request(
            token,
            "POST",
            "/repos/{}/git/refs".format(repository),
            {"ref": "refs/heads/{}".format(branch), "sha": commit_sha},
        )
    return commit_sha


def main() -> int:
    args = parse_args()
    token = os.environ.get(args.token_env, "").strip()
    if not token:
        raise RuntimeError("Missing {} for progress-data publication.".format(args.token_env))
    commit_sha = publish(args.source, args.repository, args.branch, token)
    print("Published {} to {} at {}".format(args.source, args.branch, commit_sha[:12]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        print("error: {}".format(exc), file=sys.stderr)
        sys.exit(1)
