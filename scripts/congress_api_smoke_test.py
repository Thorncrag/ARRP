#!/usr/bin/env python3
"""Verify that a Congress.gov API key is available without printing it."""

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


def congress_key() -> str:
    load_env_file()
    key = os.environ.get("CONGRESS_API_KEY", "").strip()
    if key:
        return key
    return launchctl_getenv("CONGRESS_API_KEY")


def main() -> int:
    key = congress_key()
    if not key:
        print(
            "CONGRESS_API_KEY missing. Set it in .env.local, the environment, or launchctl.",
            file=sys.stderr,
        )
        return 2

    params = urllib.parse.urlencode({"format": "json", "api_key": key})
    url = f"https://api.congress.gov/v3/bill/119/hr/3445?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "ARRP congress-api-smoke-test"})

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        print(f"Congress API HTTP error: {exc.code}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Congress API connection error: {exc.reason}", file=sys.stderr)
        return 1

    bill = payload.get("bill", {})
    title = bill.get("title") or bill.get("shortTitle") or "(title unavailable)"
    latest_action = bill.get("latestAction", {}).get("text", "(latest action unavailable)")
    print("Congress API key works.")
    print(f"Smoke bill: {bill.get('type', 'HR')} {bill.get('number', '3445')} - {title}")
    print(f"Latest action: {latest_action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
