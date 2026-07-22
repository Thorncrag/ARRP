#!/usr/bin/env python3
"""Discover, compare, and optionally stage presidential-directive baselines.

The scheduled watcher reads public Federal Register API metadata for presidential
documents issued during Trump I, Biden, and Trump II. It deduplicates records by
Federal Register document number and compares discovery-controlled fields with the
committed registry. In its default mode it writes only caller-selected reports. With
``--apply``, it updates the canonical registry's per-row fingerprints and appends one
material event to the source-monitor log; the workflow then presents those changes in
a narrow pull request.

Substantive ARRP relevance and routing remain human/LLM screening functions. The bot
does not classify a directive as an institutional defect merely because it exists.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html as html_lib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / ".github" / "presidential-directives-bot.json"
DEFAULT_REGISTRY = ROOT / "inventory" / "presidential-directives.csv"
DEFAULT_LOG = ROOT / "framework" / "logs" / "SOURCE_MONITOR_LOG.md"
USER_AGENT = "ARRP presidential-directives-watcher/1.0"

CSV_FIELDS = [
    "Directive ID",
    "Administration",
    "President",
    "Directive Type",
    "Number",
    "Title",
    "Signed Date",
    "Published Date",
    "Federal Register Citation",
    "Federal Register URL",
    "Official PDF URL",
    "Related Directive IDs",
    "Relationship Notes",
    "First Seen",
    "Last Changed",
    "Content Fingerprint",
    "Review Status",
    "ARRP Record IDs",
    "Source IDs",
    "Disposition Rationale",
    "Reviewed Date",
]

DISCOVERY_FIELDS = [
    "Directive ID",
    "Administration",
    "President",
    "Directive Type",
    "Number",
    "Title",
    "Signed Date",
    "Published Date",
    "Federal Register Citation",
    "Federal Register URL",
    "Official PDF URL",
    "Related Directive IDs",
    "Relationship Notes",
]

API_FIELDS = [
    "document_number",
    "title",
    "type",
    "subtype",
    "president",
    "signing_date",
    "publication_date",
    "presidential_document_number",
    "executive_order_number",
    "proclamation_number",
    "citation",
    "html_url",
    "pdf_url",
    "correction_of",
    "corrections",
    "disposition_notes",
]


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split())


def markdown_cell(value: Any) -> str:
    text = html_lib.escape(normalize_text(value)[:500], quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>-])", r"\\\1", text)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(row: dict[str, str]) -> str:
    material = {field: normalize_text(row.get(field, "")) for field in DISCOVERY_FIELDS}
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_registry(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"directive registry not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != CSV_FIELDS:
            raise ValueError("presidential-directives.csv header does not match the bot schema")
        rows = [{field: row.get(field, "") for field in CSV_FIELDS} for row in reader]
    ids = [row["Directive ID"].strip() for row in rows]
    if any(not value for value in ids):
        raise ValueError("directive registry contains a blank Directive ID")
    if len(ids) != len(set(ids)):
        raise ValueError("directive registry contains duplicate Directive IDs")
    return rows


def write_registry(path: Path, rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in CSV_FIELDS} for row in rows)


def parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def administration_for(
    result: dict[str, Any], scope: list[dict[str, str]]
) -> dict[str, str] | None:
    president = result.get("president") or {}
    identifier = normalize_text(president.get("identifier") if isinstance(president, dict) else "")
    signed = parse_iso_date(normalize_text(result.get("signing_date")))
    published = parse_iso_date(normalize_text(result.get("publication_date")))
    observed_date = signed or published
    if observed_date is None:
        return None
    for item in scope:
        if identifier != item["presidentIdentifier"]:
            continue
        lower = date.fromisoformat(item["signedOnOrAfter"])
        upper_raw = item.get("signedOnOrBefore", "")
        upper = date.fromisoformat(upper_raw) if upper_raw else None
        if observed_date >= lower and (upper is None or observed_date <= upper):
            return item
    return None


def related_ids(result: dict[str, Any]) -> str:
    values: set[str] = set()
    correction_of = normalize_text(result.get("correction_of"))
    if correction_of:
        values.add(correction_of.rstrip("/").rsplit("/", 1)[-1])
    corrections = result.get("corrections") or []
    if isinstance(corrections, list):
        for correction in corrections:
            if isinstance(correction, dict):
                candidate = normalize_text(
                    correction.get("document_number")
                    or correction.get("document_number_url")
                    or correction.get("url")
                )
            else:
                candidate = normalize_text(correction)
            if candidate:
                values.add(candidate.rstrip("/").rsplit("/", 1)[-1])
    return "; ".join(sorted(values))


def normalize_result(
    result: dict[str, Any], scope: list[dict[str, str]], seen_on: str
) -> dict[str, str] | None:
    scoped = administration_for(result, scope)
    if scoped is None:
        return None
    directive_id = normalize_text(result.get("document_number"))
    if not directive_id:
        raise ValueError("Federal Register result is missing document_number")
    president = result.get("president") or {}
    president_name = normalize_text(
        president.get("name") if isinstance(president, dict) else ""
    ) or scoped["presidentName"]
    number = normalize_text(
        result.get("presidential_document_number")
        or result.get("executive_order_number")
        or result.get("proclamation_number")
    )
    row = {
        "Directive ID": directive_id,
        "Administration": scoped["administration"],
        "President": president_name,
        "Directive Type": normalize_text(result.get("subtype")) or "Presidential Document",
        "Number": number,
        "Title": normalize_text(result.get("title")),
        "Signed Date": normalize_text(result.get("signing_date")),
        "Published Date": normalize_text(result.get("publication_date")),
        "Federal Register Citation": normalize_text(result.get("citation")),
        "Federal Register URL": normalize_text(result.get("html_url")),
        "Official PDF URL": normalize_text(result.get("pdf_url")),
        "Related Directive IDs": related_ids(result),
        "Relationship Notes": normalize_text(result.get("disposition_notes")),
        "First Seen": seen_on,
        "Last Changed": seen_on,
        "Content Fingerprint": "",
        "Review Status": "New since baseline screening",
        "ARRP Record IDs": "",
        "Source IDs": "",
        "Disposition Rationale": "",
        "Reviewed Date": "",
    }
    row["Content Fingerprint"] = fingerprint(row)
    return row


def build_query_url(config: dict[str, Any], president_identifier: str) -> str:
    provider = config["provider"]
    params: list[tuple[str, str]] = [
        ("per_page", str(provider["pageSize"])),
        ("order", "oldest"),
        ("conditions[type][]", provider["presidentialDocumentType"]),
        ("conditions[president]", president_identifier),
    ]
    for field in API_FIELDS:
        params.append(("fields[]", field))
    return f"{provider['apiRoot'].rstrip('/')}/documents.json?{urllib.parse.urlencode(params)}"


def validate_provider_url(url: str, config: dict[str, Any]) -> None:
    parsed = urllib.parse.urlsplit(url)
    allowed = set(config["provider"].get("allowedHosts", []))
    if parsed.scheme != "https" or parsed.hostname not in allowed:
        raise ValueError("Federal Register request URL is outside the HTTPS allowlist")


def fetch_page(url: str, config: dict[str, Any]) -> dict[str, Any]:
    validate_provider_url(url, config)
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            if response.headers.get_content_type() != "application/json":
                raise ValueError("Federal Register returned a non-JSON response")
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Federal Register API failed: HTTP {exc.code} {detail}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("Federal Register returned an invalid document response")
    return payload


def discover_live(config: dict[str, Any]) -> list[dict[str, Any]]:
    identifiers = sorted({item["presidentIdentifier"] for item in config["scope"]})
    results: list[dict[str, Any]] = []
    for identifier in identifiers:
        url = build_query_url(config, identifier)
        seen_urls: set[str] = set()
        pages = 0
        while url:
            if url in seen_urls:
                raise ValueError("Federal Register pagination loop detected")
            seen_urls.add(url)
            pages += 1
            if pages > int(config["provider"]["maxPagesPerQuery"]):
                raise ValueError("Federal Register result exceeded the configured page limit")
            payload = fetch_page(url, config)
            results.extend(payload["results"])
            url = normalize_text(payload.get("next_page_url"))
    return results


def fixture_results(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path)
    if isinstance(payload, dict):
        payload = payload.get("results")
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError("fixture must be a result list or an object with a results list")
    return payload


def merge_discovery(
    current_rows: list[dict[str, str]],
    raw_results: list[dict[str, Any]],
    config: dict[str, Any],
    seen_on: str,
) -> dict[str, Any]:
    discovered: dict[str, dict[str, str]] = {}
    out_of_scope = 0
    for result in raw_results:
        row = normalize_result(result, config["scope"], seen_on)
        if row is None:
            out_of_scope += 1
            continue
        directive_id = row["Directive ID"]
        prior = discovered.get(directive_id)
        if prior and prior != row:
            raise ValueError(f"conflicting duplicate directive: {directive_id}")
        discovered[directive_id] = row

    current = {row["Directive ID"]: row for row in current_rows}
    proposed: list[dict[str, str]] = []
    changes: list[dict[str, Any]] = []
    new_ids: list[str] = []
    unchanged_ids: list[str] = []

    for directive_id, found in discovered.items():
        existing = current.get(directive_id)
        if existing is None:
            proposed.append(found)
            new_ids.append(directive_id)
            continue
        new_fingerprint = found["Content Fingerprint"]
        old_fingerprint = existing.get("Content Fingerprint", "") or fingerprint(existing)
        if new_fingerprint == old_fingerprint:
            proposed.append(existing)
            unchanged_ids.append(directive_id)
            continue
        changed_fields = [
            field
            for field in DISCOVERY_FIELDS
            if normalize_text(existing.get(field, "")) != normalize_text(found.get(field, ""))
        ]
        merged = dict(existing)
        for field in DISCOVERY_FIELDS:
            merged[field] = found[field]
        merged["Content Fingerprint"] = new_fingerprint
        merged["Last Changed"] = seen_on
        if normalize_text(existing.get("Review Status")) not in {
            "",
            "New since baseline screening",
        }:
            merged["Review Status"] = "Changed since screening"
        else:
            merged["Review Status"] = "New since baseline screening"
        proposed.append(merged)
        changes.append({"directive_id": directive_id, "changed_fields": changed_fields})

    missing_ids = sorted(set(current) - set(discovered))
    proposed.extend(current[directive_id] for directive_id in missing_ids)
    proposed.sort(key=lambda row: (row["Signed Date"], row["Directive ID"]))

    status_by_id = {directive_id: "unchanged" for directive_id in unchanged_ids}
    status_by_id.update({directive_id: "new" for directive_id in new_ids})
    status_by_id.update({item["directive_id"]: "changed" for item in changes})
    status_by_id.update({directive_id: "not_seen" for directive_id in missing_ids})
    report_rows = [
        {**row, "Bot Status": status_by_id.get(row["Directive ID"], "unchanged")}
        for row in proposed
    ]
    return {
        "raw_result_count": len(raw_results),
        "out_of_scope_count": out_of_scope,
        "new_ids": sorted(new_ids),
        "changes": sorted(changes, key=lambda item: item["directive_id"]),
        "unchanged_ids": sorted(unchanged_ids),
        "missing_ids": missing_ids,
        "proposed_rows": proposed,
        "report_rows": report_rows,
    }


def render_summary(report: dict[str, Any]) -> str:
    counts = report["counts"]
    lines = [
        "## ARRP presidential-directives watcher",
        "",
        "Comparison against the committed presidential-directives registry baseline.",
        "",
        f"- Discovered in scope: **{counts['discovered']}**",
        f"- New: **{counts['new']}**",
        f"- Changed: **{counts['changed']}**",
        f"- Unchanged: **{counts['unchanged']}**",
        f"- Existing rows not seen: **{counts['not_seen']}**",
        f"- Filtered outside the three-administration scope: **{counts['out_of_scope']}**",
        "",
        (
            "A catalog-and-log update was staged for review in a pull request."
            if report.get("applied")
            else "No catalog or log update was necessary."
        ),
    ]
    by_administration = Counter(row["Administration"] for row in report["directives"])
    by_type = Counter(row["Directive Type"] for row in report["directives"])
    if by_administration:
        lines.extend(["", "### Scope totals", ""])
        lines.extend(
            f"- {markdown_cell(name)}: {count}"
            for name, count in sorted(by_administration.items())
        )
    if by_type:
        lines.extend(["", "### Directive types", ""])
        lines.extend(
            f"- {markdown_cell(name)}: {count}" for name, count in by_type.most_common()
        )
    review_items = [
        row for row in report["directives"] if row["Bot Status"] in {"new", "changed"}
    ]
    if review_items:
        lines.extend(["", "### Items requiring screening", ""])
        for row in review_items[:100]:
            lines.append(
                f"- **{markdown_cell(row['Bot Status'].title())}:** "
                f"{markdown_cell(row['Directive ID'])} — {markdown_cell(row['Title'])}"
            )
        if len(review_items) > 100:
            lines.append(f"- …and {len(review_items) - 100} more in the JSON/CSV report.")
    return "\n".join(lines) + "\n"


def build_report(
    merged: dict[str, Any], config: dict[str, Any], generated_at: str
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "bot_name": config["botName"],
        "generated_at": generated_at,
        "mode": "baseline-update" if merged.get("applied") else "read-only-comparison",
        "scope": config["scope"],
        "counts": {
            "raw_results": merged["raw_result_count"],
            "discovered": len(merged["report_rows"]) - len(merged["missing_ids"]),
            "new": len(merged["new_ids"]),
            "changed": len(merged["changes"]),
            "unchanged": len(merged["unchanged_ids"]),
            "not_seen": len(merged["missing_ids"]),
            "out_of_scope": merged["out_of_scope_count"],
        },
        "changes": merged["changes"],
        "not_seen_ids": merged["missing_ids"],
        "directives": merged["report_rows"],
    }


def render_log_entry(report: dict[str, Any], run_url: str = "") -> str:
    """Render one concise, auditable entry for a material catalog update."""

    changes = report["changes"]
    new_ids = [
        row["Directive ID"]
        for row in report["directives"]
        if row["Bot Status"] == "new"
    ]
    changed_ids = [item["directive_id"] for item in changes]
    digest_material = {
        "new": sorted(new_ids),
        "changed": sorted(changed_ids),
        "fingerprints": {
            row["Directive ID"]: row["Content Fingerprint"]
            for row in report["directives"]
            if row["Bot Status"] in {"new", "changed"}
        },
    }
    activity_code = "PDM-" + hashlib.sha256(
        canonical_json(digest_material).encode("utf-8")
    ).hexdigest()[:10].upper()
    lines = [
        f"## {report['generated_at']} — Presidential directives watcher ({activity_code})",
        "",
        f"- Added directives: **{len(new_ids)}**",
        f"- Changed directives: **{len(changed_ids)}**",
    ]
    if new_ids:
        listed = ", ".join(markdown_cell(value) for value in sorted(new_ids))
        lines.append(f"- Added IDs: {listed}")
    if changed_ids:
        lines.append(
            f"- Changed IDs: {', '.join(markdown_cell(value) for value in sorted(changed_ids))}"
        )
    if run_url:
        lines.append(f"- Workflow run: {run_url}")
    lines.extend(
        [
            "- Action: Updated machine-observed Federal Register metadata and per-row baselines for human review.",
            "- Boundary: No substantive ARRP classification or disposition was performed.",
            "",
        ]
    )
    return "\n".join(lines)


def append_log(path: Path, entry: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        separator = "" if not existing or existing.endswith("\n\n") else "\n"
        path.write_text(existing + separator + entry, encoding="utf-8")
    else:
        path.write_text(
            '---\ntitle: "Source Monitor Log"\nprint_status: excluded\nprint_exclusion_reason: "Operational monitoring log."\n---\n\n'
            "# Source Monitor Log\n\n"
            "This log records material updates proposed by automated source watchers. "
            "Routine no-change runs remain in GitHub Actions.\n\n"
            + entry,
            encoding="utf-8",
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--fixture", type=Path, help="Use deterministic API fixture data")
    parser.add_argument("--summary", type=Path, help="Write a Markdown run summary")
    parser.add_argument("--report-json", type=Path, help="Write console-ready JSON state")
    parser.add_argument(
        "--proposed-csv",
        type=Path,
        help="Write proposed registry to a noncanonical path",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write material changes to the registry and append the source-monitor log",
    )
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument(
        "--run-url", default="", help="Actions URL recorded in a material log entry"
    )
    parser.add_argument("--as-of", help="Override the UTC observation timestamp for tests")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = read_json(args.config)
    registry_path = args.registry.resolve()
    proposed_path = args.proposed_csv.resolve() if args.proposed_csv else None
    if proposed_path == registry_path:
        raise SystemExit(
            "refusing to write the canonical registry; choose a proposed output path"
        )
    generated_at = args.as_of or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat()
    seen_on = generated_at[:10]
    rows = read_registry(args.registry)
    raw_results = fixture_results(args.fixture) if args.fixture else discover_live(config)
    merged = merge_discovery(rows, raw_results, config, seen_on)
    material = bool(merged["new_ids"] or merged["changes"])
    if args.apply and merged["missing_ids"]:
        raise SystemExit(
            "refusing to update the baseline because existing directives were absent "
            "from discovery"
        )
    merged["applied"] = bool(args.apply and material)
    report = build_report(merged, config, generated_at)
    report["material_update"] = material
    report["applied"] = merged["applied"]
    summary = render_summary(report)

    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(summary, encoding="utf-8")
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    if args.proposed_csv:
        write_registry(args.proposed_csv, merged["proposed_rows"])
    if args.apply and material:
        write_registry(args.registry, merged["proposed_rows"])
        append_log(args.log, render_log_entry(report, args.run_url))
    if not args.summary:
        print(summary, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
