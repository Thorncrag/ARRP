#!/usr/bin/env python3
"""Search recently issued legislation through the GovInfo API."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

try:
    from govinfo_api_smoke_test import govinfo_key
except ModuleNotFoundError:
    from scripts.govinfo_api_smoke_test import govinfo_key


API_ROOT = "https://api.govinfo.gov"
INTRODUCED_VERSION_RE = re.compile(r"(?:ih|is)$", re.IGNORECASE)


def api_url(path: str, key: str, **params: object) -> str:
    params["api_key"] = key
    return f"{API_ROOT}{path}?{urllib.parse.urlencode(params)}"


def request(url: str, *, as_json: bool, attempts: int = 5) -> object:
    for attempt in range(attempts):
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "ARRP govinfo-legislation-search"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                if as_json:
                    return json.load(response)
                return response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == attempts - 1:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2 ** attempt
            time.sleep(min(delay, 30))
    raise RuntimeError("GovInfo request failed after retries")


def collection_packages(key: str, since: date) -> list[dict[str, object]]:
    timestamp = urllib.parse.quote(f"{since.isoformat()}T00:00:00Z", safe="")
    packages: list[dict[str, object]] = []
    offset = 0
    page_size = 100

    while True:
        url = api_url(
            f"/collections/BILLS/{timestamp}",
            key,
            offset=offset,
            pageSize=page_size,
        )
        payload = request(url, as_json=True)
        assert isinstance(payload, dict)
        page = payload.get("packages", [])
        if not isinstance(page, list) or not page:
            break
        packages.extend(item for item in page if isinstance(item, dict))
        offset += len(page)
        if offset >= int(payload.get("count", offset)):
            break

    return packages


def issued_on_or_after(package: dict[str, object], since: date) -> bool:
    raw = str(package.get("dateIssued", ""))[:10]
    try:
        return date.fromisoformat(raw) >= since
    except ValueError:
        return False


def introduced_package(package: dict[str, object]) -> bool:
    return bool(INTRODUCED_VERSION_RE.search(str(package.get("packageId", ""))))


def normalize_text(raw: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def matching_terms(text: str, terms: list[str]) -> list[str]:
    lowered = text.casefold()
    return [term for term in terms if term.casefold() in lowered]


def hit_context(text: str, terms: list[str], radius: int) -> str:
    lowered = text.casefold()
    positions = [lowered.find(term.casefold()) for term in terms]
    positions = [position for position in positions if position >= 0]
    if not positions:
        return ""
    position = min(positions)
    start = max(0, position - radius)
    end = min(len(text), position + radius)
    prefix = "..." if start else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def markdown_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search introduced bill text issued on or after a date.",
    )
    parser.add_argument("--since", required=True, type=parse_date)
    parser.add_argument(
        "--term",
        action="append",
        required=True,
        help="Literal case-insensitive search term; repeat for additional terms.",
    )
    parser.add_argument(
        "--all-versions",
        action="store_true",
        help="Search every bill version instead of introduced versions only.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay between bill-text requests in seconds (default: 0.1).",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=0,
        metavar="CHARS",
        help="Include context around the first match.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    key = govinfo_key()
    if not key:
        print("GOVINFO_API_KEY is missing.", file=sys.stderr)
        return 2

    try:
        packages = collection_packages(key, args.since)
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"GovInfo collection request failed: {exc}", file=sys.stderr)
        return 1

    candidate_by_id = {
        str(package.get("packageId", "")): package
        for package in packages
        if issued_on_or_after(package, args.since)
        and (args.all_versions or introduced_package(package))
    }
    candidates = list(candidate_by_id.values())
    candidates.sort(key=lambda item: (str(item.get("dateIssued", "")), str(item.get("packageId", ""))))

    results: list[tuple[dict[str, object], list[str], str]] = []
    for index, package in enumerate(candidates):
        package_id = str(package.get("packageId", ""))
        title = str(package.get("title", ""))
        hits = matching_terms(title, args.term)
        searchable_text = title
        if len(hits) != len(args.term):
            try:
                url = api_url(f"/packages/{package_id}/htm", key)
                body = request(url, as_json=False)
                assert isinstance(body, str)
                searchable_text = f"{title} {normalize_text(body)}"
                hits = matching_terms(searchable_text, args.term)
            except (urllib.error.URLError, urllib.error.HTTPError) as exc:
                print(f"Warning: could not read {package_id}: {exc}", file=sys.stderr)
                continue
        if hits:
            context = hit_context(searchable_text, hits, args.context) if args.context else ""
            results.append((package, hits, context))
        if args.delay > 0 and index < len(candidates) - 1:
            time.sleep(args.delay)

    print(f"Scanned {len(candidates)} introduced packages issued since {args.since.isoformat()}.")
    print(f"Found {len(results)} packages matching at least one supplied term.")
    if not results:
        return 0

    print()
    print("| Issued | Package | Matching terms | Title |")
    print("|---|---|---|---|")
    for package, hits, context in results:
        package_id = str(package.get("packageId", ""))
        link = f"https://www.govinfo.gov/app/details/{package_id}"
        print(
            f"| {markdown_escape(str(package.get('dateIssued', ''))[:10])} "
            f"| [{markdown_escape(package_id)}]({link}) "
            f"| {markdown_escape(', '.join(hits))} "
            f"| {markdown_escape(package.get('title', ''))} |"
        )
        if context:
            print(f"  Context: {context}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
