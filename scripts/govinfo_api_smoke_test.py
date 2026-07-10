#!/usr/bin/env python3
"""Verify that a GovInfo API key is available without printing it."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env.local"


def load_env_file() -> None:
    if not ENV_PATH.exists():
        return
    for raw_line in ENV_PATH.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def launchctl_getenv(name: str) -> str:
    try:
        proc = subprocess.run(
            ["launchctl", "getenv", name],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return ""
    return proc.stdout.strip()


def govinfo_key() -> str:
    load_env_file()
    key = os.environ.get("GOVINFO_API_KEY", "").strip()
    if key:
        return key
    return launchctl_getenv("GOVINFO_API_KEY")


def main() -> int:
    key = govinfo_key()
    if not key:
        print(
            "GOVINFO_API_KEY missing. Set it in .env.local, the environment, or launchctl.",
            file=sys.stderr,
        )
        return 2

    timestamp = urllib.parse.quote("2026-07-01T00:00:00Z", safe="")
    params = urllib.parse.urlencode({"offset": 0, "pageSize": 1, "api_key": key})
    url = f"https://api.govinfo.gov/collections/BILLS/{timestamp}?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "ARRP govinfo-api-smoke-test"})

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        print(f"GovInfo API HTTP error: {exc.code}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"GovInfo API connection error: {exc.reason}", file=sys.stderr)
        return 1

    packages = payload.get("packages", [])
    package = packages[0] if packages else {}
    print("GovInfo API key works.")
    print(f"Matching packages: {payload.get('count', 0)}")
    if package:
        print(
            f"Sample package: {package.get('packageId', '(unavailable)')} - "
            f"{package.get('title', '(title unavailable)')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
