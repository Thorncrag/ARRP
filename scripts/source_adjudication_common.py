"""Shared helpers for ARRP source-adjudication packets and migrations."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _serialize_csv_row(row: dict[str, str], fieldnames: list[str]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writerow(row)
    return buffer.getvalue()


def write_csv_preserving_unchanged(
    path: Path,
    original_rows: list[dict[str, str]],
    rows: list[dict[str, str]],
    fieldnames: list[str],
    *,
    key_field: str,
) -> None:
    """Write a CSV while retaining the exact text of unchanged records.

    The source inventory contains legacy records with deliberate quoting and a
    few embedded line breaks. Re-serializing the entire file makes a small
    adjudication batch appear to rewrite hundreds of unrelated records. This
    writer preserves each unchanged raw record and serializes only changed or
    newly appended records.
    """
    raw = path.read_text(encoding="utf-8")
    physical_lines = raw.splitlines(keepends=True)
    reader = csv.DictReader(io.StringIO(raw, newline=""))
    raw_by_key: dict[str, str] = {}
    start_line = 1  # DictReader consumed the header record.
    for original in reader:
        end_line = reader.line_num
        raw_by_key[original[key_field]] = "".join(physical_lines[start_line:end_line])
        start_line = end_line

    original_by_key = {row[key_field]: row for row in original_rows}
    header = physical_lines[0] if physical_lines else ",".join(fieldnames) + "\n"
    output = [header]
    for row in rows:
        key = row[key_field]
        if key in raw_by_key and row == original_by_key.get(key):
            output.append(raw_by_key[key])
        else:
            output.append(_serialize_csv_row(row, fieldnames))
    path.write_text("".join(output), encoding="utf-8")


def normalize_url(raw: str) -> str:
    """Return a conservative document-identity key for an HTTP(S) URL."""
    value = raw.strip()
    if not value:
        return ""
    parts = urlsplit(value)
    if parts.scheme.lower() not in {"http", "https"}:
        return value
    scheme = "https"
    host = parts.netloc.lower()
    if host.endswith(":80"):
        host = host[:-3]
    if host.endswith(":443"):
        host = host[:-4]
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lower = key.lower()
        if lower.startswith("utm_") or lower in TRACKING_QUERY_KEYS:
            continue
        query.append((key, value))
    return urlunsplit((scheme, host, path, urlencode(sorted(query)), ""))


def split_routes(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(";") if part.strip()]


def merge_routes(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for route in group:
            if route and route not in merged:
                merged.append(route)
    return merged


def source_urls(row: dict[str, str]) -> list[dict[str, str]]:
    candidates = [
        ("official_action", row.get("official_action_url", "")),
        ("representative_case", row.get("representative_case_url", "")),
        ("source_entry", row.get("source_entry_url", "")),
    ]
    rendered: list[dict[str, str]] = []
    seen: set[str] = set()
    for kind, url in candidates:
        normalized = normalize_url(url)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        rendered.append({"kind": kind, "url": url.strip(), "normalized_url": normalized})
    return rendered
