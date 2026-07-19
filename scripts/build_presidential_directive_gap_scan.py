#!/usr/bin/env python3
"""Build a temporary ARRP completeness scan of Trump presidential directives.

The Federal Register supplies the official-action index and GovInfo PDF links.
This script identifies directives already present in active ARRP records, removes
plainly ceremonial material from the review burden, and places only unmatched
operative directives into the existing legal-review catalog and routing staging
files. It does not create issue pages, formal Horizon records, or a permanent
directive queue.

Substantive disposition remains governed by ``apply_source_adjudication.py``:
an unmatched directive that plausibly exposes a distinct unowned institutional
weakness must create or update one clustered preliminary candidate; other
records must be integrated, monitored, rejected, or removed before closeout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from source_adjudication_common import normalize_url, read_csv, write_csv


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research" / "trump-administration-legal-review-catalog.csv"
ROUTING = ROOT / "research" / "trump-administration-evidence-routing.csv"

FEDERAL_REGISTER_ENDPOINT = "https://www.federalregister.gov/api/v1/documents.json"
DIRECTIVE_TYPES = (
    "executive_order",
    "proclamation",
    "determination",
    "memorandum",
    "notice",
    "other",
    "presidential_order",
)
TYPE_LABELS = {
    "executive_order": "Executive Order",
    "proclamation": "Proclamation",
    "determination": "Presidential Determination",
    "memorandum": "Presidential Memorandum",
    "notice": "Presidential Notice",
    "other": "Other Presidential Document",
    "presidential_order": "Presidential Order",
}
TERM_BOUNDS = {
    "first": ("2017-01-20", "2021-01-20", "1"),
    "second": ("2025-01-20", None, "2"),
}

CATALOG_FIELDS = [
    "catalog_id",
    "term",
    "record_type",
    "action_or_policy",
    "action_date_or_period",
    "responsible_actor_or_category",
    "legal_question_or_outcome",
    "litigation_posture",
    "screening_track",
    "source_family",
    "source_entry_url",
    "representative_case",
    "representative_case_url",
    "official_action_url",
    "arrp_coverage_status",
    "provisional_arrp_routes",
    "normalization_status",
    "last_checked",
    "notes",
]
ROUTING_FIELDS = [
    "catalog_id",
    "evidence_group",
    "disposition",
    "integration_routes",
    "recommended_use",
    "source_value",
    "review_basis",
    "review_status",
    "candidate_id",
    "last_reviewed",
]

ACTIVE_SEARCH_ROOTS = (
    "areas",
    "framework/logs",
    "inventory",
    "legislation",
    "research",
    "topics",
)
SEARCH_SUFFIXES = {".csv", ".json", ".md"}
SEARCH_EXCLUSIONS = {
    "research/trump-administration-legal-review-catalog.csv",
    "research/trump-administration-evidence-routing.csv",
    "research/horizon-review-console/catalog-data.js",
}

CEREMONIAL_PROCLAMATION = re.compile(
    r"\b(?:day|days|week|month|anniversary|commemoration|heritage month|"
    r"awareness month|recognition month|honor(?:ing)?|tribute|flag day)\b",
    re.IGNORECASE,
)

# These are discovery signals, not findings of illegality or issue admission.
RELEVANCE_SIGNALS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("congressional-displacement", re.compile(
        r"\b(?:impound|appropriat(?:e|ed|ion)|withhold(?:ing)? funds?|"
        r"redirect(?:ing)? funds?|congressional mandate|statutory mandate|"
        r"notwithstanding .*act|pause .*funding|terminate .*grant)\b", re.I)),
    ("appointments-personnel", re.compile(
        r"\b(?:acting official|vacanc(?:y|ies)|appoint(?:ment|ed)?|remove|removal|"
        r"reclassif|civil service|schedule f|schedule policy/career|loyalty|"
        r"delegat(?:e|ion).*(?:authority|function))\b", re.I)),
    ("enforcement-adjudication", re.compile(
        r"\b(?:prosecut|investigat|nonenforcement|non-enforcement|enforcement discretion|"
        r"adjudicat|law firm|security clearance|regulatory action against|"
        r"criminal action against)\b", re.I)),
    ("emergency-force-foreign-authority", re.compile(
        r"\b(?:national emergency|emergency authorit|insurrection act|military force|"
        r"armed forces|domestic deployment|alien enemies act|ieepa|sanction|tariff)\b", re.I)),
    ("federalism-coercion", re.compile(
        r"\b(?:state or local|state and local|sanctuary|federal funding.*state|"
        r"condition.*grant|withhold.*state|governor|state official|voter roll)\b", re.I)),
    ("records-information-integrity", re.compile(
        r"\b(?:records retention|presidential records|delete .*record|remove .*website|"
        r"classif(?:y|ied|ication)|declassif|scientific integrity|official statistics|"
        r"historical record|government data|public access to .*record)\b", re.I)),
    ("private-benefit-protection", re.compile(
        r"\b(?:financial interest|private benefit|conflict of interest|emolument|"
        r"presidential library|pardon|clemency|immunity|official social media)\b", re.I)),
    ("civil-rights-reviewability", re.compile(
        r"\b(?:due process|equal protection|civil rights|asylum|refugee|deport|removal proceedings|"
        r"detention|birthright citizenship|disabilit|humanitarian protection)\b", re.I)),
    ("oversight-judicial-correction", re.compile(
        r"\b(?:inspector general|congressional oversight|subpoena|court order|judicial review|"
        r"reviewability|evidence preservation|whistleblower|contempt of court)\b", re.I)),
    ("specialized-institutional-assets", re.compile(
        r"\b(?:national monument|antiquities act|tribal lands?|federal reserve|"
        r"press access|election administration|transfer of power)\b", re.I)),
)

ISSUE_ID = re.compile(r"\b(?:INTAKE-GAP|HOR|[A-Z]{2,})-\d{3}(?:-MON)?\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--term", choices=("first", "second", "both"), default="second")
    parser.add_argument("--through", default=date.today().isoformat())
    parser.add_argument("--since", help="override the term's inclusive start date")
    parser.add_argument(
        "--types",
        default=",".join(DIRECTIVE_TYPES),
        help="comma-separated Federal Register presidential-document types",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write unmatched review records into the existing staging files",
    )
    parser.add_argument(
        "--catalog-ids",
        help=(
            "comma-separated unmatched catalog IDs to stage; requires --apply and "
            "allows an adjudicated subset to enter the canonical intake workflow"
        ),
    )
    parser.add_argument(
        "--fetch-text",
        action="store_true",
        help="also fetch unmatched directive text for richer triage signals",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="optional JSON report path; otherwise the report is written to stdout",
    )
    return parser.parse_args()


def _http_json(url: str) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": "ARRP-directive-gap-scan/1.0"})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def federal_register_url(
    start: str,
    end: str,
    *,
    page: int = 1,
) -> str:
    fields = (
        "document_number",
        "type",
        "subtype",
        "title",
        "executive_order_number",
        "proclamation_number",
        "presidential_document_number",
        "signing_date",
        "publication_date",
        "raw_text_url",
        "full_text_xml_url",
        "pdf_url",
        "html_url",
        "json_url",
        "mods_url",
        "citation",
        "disposition_notes",
        "executive_order_notes",
        "correction_of",
        "not_received_for_publication",
    )
    params: list[tuple[str, str | int]] = [
        ("conditions[president][]", "donald-trump"),
        ("conditions[type][]", "PRESDOCU"),
        ("conditions[signing_date][gte]", start),
        ("conditions[signing_date][lte]", end),
        ("order", "oldest"),
        ("per_page", 1000),
        ("page", page),
    ]
    params.extend(("fields[]", field) for field in fields)
    return f"{FEDERAL_REGISTER_ENDPOINT}?{urlencode(params)}"


def fetch_directives(
    directive_types: Iterable[str],
    start: str,
    end: str,
    fetch_json: Callable[[str], dict[str, object]] = _http_json,
) -> list[dict[str, str]]:
    directives: list[dict[str, str]] = []
    selected = set(directive_types)
    page = 1
    while True:
        payload = fetch_json(federal_register_url(start, end, page=page))
        results = payload.get("results", [])
        if not isinstance(results, list):
            raise RuntimeError("Federal Register response has no results list")
        for item in results:
            if not isinstance(item, dict):
                continue
            row = {key: str(value or "").strip() for key, value in item.items()}
            directive_type = re.sub(r"[^a-z0-9]+", "_", row.get("subtype", "").lower()).strip("_")
            if directive_type not in selected:
                continue
            row["directive_type"] = directive_type
            directives.append(row)
        total_pages = int(payload.get("total_pages", 1) or 1)
        if page >= total_pages:
            break
        page += 1
    return directives


def directive_identity_keys(row: dict[str, str]) -> list[str]:
    keys: list[str] = []
    document_number = row.get("document_number", "").strip().lower()
    if document_number:
        keys.append(document_number)
    executive_order = row.get("executive_order_number", "").strip().lower()
    if executive_order:
        keys.extend(
            (
                f"executive order {executive_order}",
                f"eo {executive_order}",
                f"eo-{executive_order}",
            )
        )
    proclamation = row.get("proclamation_number", "").strip().lower()
    if proclamation:
        keys.extend(
            (
                f"proclamation {proclamation}",
                f"proclamation no. {proclamation}",
            )
        )
    for field in ("html_url", "pdf_url"):
        value = normalize_url(row.get(field, ""))
        if value:
            keys.append(value.lower())
    return list(dict.fromkeys(keys))


def normalize_title(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def catalog_id(row: dict[str, str]) -> str:
    document_number = re.sub(r"[^A-Za-z0-9]", "", row["document_number"]).upper()
    return f"TAC-PD-{document_number}"


def evidence_group(row: dict[str, str]) -> str:
    identity = row.get("document_number") or row.get("html_url") or row.get("title")
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:12].upper()
    return f"EVID-{digest}"


def iter_active_records(root: Path = ROOT) -> Iterable[tuple[Path, str]]:
    for relative_root in ACTIVE_SEARCH_ROOTS:
        base = root / relative_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SEARCH_SUFFIXES:
                continue
            relative = path.relative_to(root).as_posix()
            if relative in SEARCH_EXCLUSIONS:
                continue
            yield path, path.read_text(encoding="utf-8", errors="replace")


def existing_project_matches(
    directive: dict[str, str],
    records: Iterable[tuple[Path, str]],
    *,
    root: Path = ROOT,
) -> tuple[list[str], list[str]]:
    identities = directive_identity_keys(directive)
    title = normalize_title(directive.get("title", ""))
    title_date = directive.get("signing_date", "") or directive.get("publication_date", "")
    matched_files: list[str] = []
    routes: list[str] = []
    for path, text in records:
        lowered = text.lower()
        exact = any(identity in lowered for identity in identities)
        if not exact and title and title_date:
            exact = directive.get("title", "").lower() in lowered and title_date in text
        if not exact:
            continue
        relative = path.relative_to(root).as_posix()
        matched_files.append(relative)
        path_routes = ISSUE_ID.findall(relative)
        if not path_routes:
            for line in text.splitlines():
                line_lower = line.lower()
                if any(key in line_lower for key in identities):
                    path_routes.extend(ISSUE_ID.findall(line))
                elif title and title in normalize_title(line):
                    path_routes.extend(ISSUE_ID.findall(line))
        for route in path_routes:
            if route not in routes:
                routes.append(route)
    return matched_files, routes


def relevance_signals(text: str) -> list[str]:
    return [name for name, pattern in RELEVANCE_SIGNALS if pattern.search(text)]


def presumptively_ceremonial(directive: dict[str, str], signals: list[str]) -> bool:
    return (
        directive.get("directive_type") == "proclamation"
        and bool(CEREMONIAL_PROCLAMATION.search(directive.get("title", "")))
        and not signals
    )


def classify_directive(
    directive: dict[str, str],
    matched_files: list[str],
    routes: list[str],
    *,
    full_text: str = "",
) -> dict[str, object]:
    signals = relevance_signals(f"{directive.get('title', '')}\n{full_text}")
    if matched_files:
        status = "existing-project-match"
    elif presumptively_ceremonial(directive, signals):
        status = "routine-ceremonial-no-project-action"
    else:
        status = "unmatched-agent-review"
    return {
        "status": status,
        "signals": signals,
        "matched_files": matched_files,
        "routes": routes,
    }


def fetch_text(directive: dict[str, str]) -> str:
    url = directive.get("raw_text_url", "")
    if not url:
        return ""
    request = Request(url, headers={"User-Agent": "ARRP-directive-gap-scan/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def staging_rows(
    directive: dict[str, str],
    classification: dict[str, object],
    checked: str,
    term_number: str,
) -> tuple[dict[str, str], dict[str, str]]:
    routes = [str(route) for route in classification["routes"]]
    signals = [str(signal) for signal in classification["signals"]]
    identifiers = []
    for label, field in (
        ("EO", "executive_order_number"),
        ("proclamation", "proclamation_number"),
        ("presidential-document", "presidential_document_number"),
    ):
        if directive.get(field):
            identifiers.append(f"{label}={directive[field]}")
    identifiers.append(f"directive-type={directive['directive_type']}")
    if directive.get("publication_date") and directive["publication_date"] > checked:
        identifiers.append(f"scheduled-publication={directive['publication_date']}")
    if signals:
        identifiers.append("signals=" + "|".join(signals))
    catalog = {
        "catalog_id": catalog_id(directive),
        "term": term_number,
        "record_type": "presidential-directive-gap-scan",
        "action_or_policy": directive["title"],
        "action_date_or_period": directive.get("signing_date") or directive.get("publication_date", ""),
        "responsible_actor_or_category": "President; formal presidential directive",
        "legal_question_or_outcome": "Unmatched official action; institutional-defect and route-fit review required.",
        "litigation_posture": "not-litigation-derived",
        "screening_track": "verify-institutional-defect-and-existing-coverage",
        "source_family": "Federal Register Presidential Documents",
        "source_entry_url": directive.get("html_url", ""),
        "representative_case": "",
        "representative_case_url": "",
        "official_action_url": directive.get("pdf_url", ""),
        "arrp_coverage_status": "unmatched-potential-gap",
        "provisional_arrp_routes": "; ".join(routes),
        "normalization_status": "official-document-identity-normalized",
        "last_checked": checked,
        "notes": "; ".join(identifiers),
    }
    routing = {
        "catalog_id": catalog["catalog_id"],
        "evidence_group": evidence_group(directive),
        "disposition": "agent-review-needed",
        "integration_routes": "; ".join(routes),
        "recommended_use": "institutional-defect, duplicate, and route-fit review",
        "source_value": "official-presidential-directive",
        "review_basis": "Unmatched formal directive from the official Federal Register corpus.",
        "review_status": "agent-review-needed",
        "candidate_id": "",
        "last_reviewed": checked,
    }
    return catalog, routing


def merge_staging(
    existing: list[dict[str, str]],
    additions: list[dict[str, str]],
) -> list[dict[str, str]]:
    by_id = {row["catalog_id"]: row for row in existing}
    for row in additions:
        current = by_id.get(row["catalog_id"])
        if current and current != row:
            raise SystemExit(
                f"Staging record {row['catalog_id']} already exists with different content."
            )
        by_id[row["catalog_id"]] = row
    return list(by_id.values())


def select_staging_rows(
    catalog_rows: list[dict[str, str]],
    routing_rows: list[dict[str, str]],
    requested_ids: set[str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Select a reconciled adjudicated subset for canonical staging."""
    catalog_by_id = {row["catalog_id"]: row for row in catalog_rows}
    routing_by_id = {row["catalog_id"]: row for row in routing_rows}
    available = set(catalog_by_id)
    if available != set(routing_by_id):
        raise SystemExit("Generated catalog and routing staging rows are not reconciled.")
    missing = requested_ids - available
    if missing:
        raise SystemExit(
            "Requested catalog IDs are not unmatched scan records: "
            + ", ".join(sorted(missing))
        )
    ordered_ids = [row["catalog_id"] for row in catalog_rows if row["catalog_id"] in requested_ids]
    return (
        [catalog_by_id[catalog_id] for catalog_id in ordered_ids],
        [routing_by_id[catalog_id] for catalog_id in ordered_ids],
    )


def scan_term(
    term: str,
    directive_types: list[str],
    through: str,
    since_override: str | None,
    records: list[tuple[Path, str]],
    *,
    fetch_full_text: bool = False,
) -> tuple[list[dict[str, object]], list[dict[str, str]], list[dict[str, str]]]:
    default_start, term_end, term_number = TERM_BOUNDS[term]
    start = since_override or default_start
    end = min(through, term_end) if term_end else through
    directives = fetch_directives(directive_types, start, end)
    results: list[dict[str, object]] = []
    catalog_rows: list[dict[str, str]] = []
    routing_rows: list[dict[str, str]] = []
    for directive in directives:
        if directive.get("correction_of"):
            all_routes: list[str] = []
            results.append(
                {
                    "catalog_id": catalog_id(directive),
                    "term": term_number,
                    "directive_type": directive["directive_type"],
                    "document_number": directive.get("document_number", ""),
                    "directive_number": "",
                    "title": directive.get("title", ""),
                    "signing_date": directive.get("signing_date", ""),
                    "publication_date": directive.get("publication_date", ""),
                    "html_url": directive.get("html_url", ""),
                    "pdf_url": directive.get("pdf_url", ""),
                    "status": "correction-attached-no-new-directive",
                    "signals": [],
                    "matched_files": [],
                    "routes": all_routes,
                    "correction_of": directive["correction_of"],
                }
            )
            continue
        matched_files, routes = existing_project_matches(directive, records)
        title_signals = relevance_signals(directive.get("title", ""))
        full_text = ""
        if (
            fetch_full_text
            and not matched_files
            and not presumptively_ceremonial(directive, title_signals)
        ):
            try:
                full_text = fetch_text(directive)
            except Exception as error:  # Preserve the lead; do not silently drop it.
                full_text = ""
                directive["text_retrieval_error"] = str(error)
        classification = classify_directive(
            directive, matched_files, routes, full_text=full_text
        )
        result = {
            "catalog_id": catalog_id(directive),
            "term": term_number,
            "directive_type": directive["directive_type"],
            "document_number": directive.get("document_number", ""),
            "directive_number": (
                directive.get("executive_order_number")
                or directive.get("proclamation_number")
                or directive.get("presidential_document_number")
                or ""
            ),
            "title": directive.get("title", ""),
            "signing_date": directive.get("signing_date", ""),
            "publication_date": directive.get("publication_date", ""),
            "html_url": directive.get("html_url", ""),
            "pdf_url": directive.get("pdf_url", ""),
            "scheduled_publication": bool(
                directive.get("publication_date")
                and directive["publication_date"] > through
            ),
            **classification,
        }
        if directive.get("text_retrieval_error"):
            result["text_retrieval_error"] = directive["text_retrieval_error"]
        results.append(result)
        if classification["status"] == "unmatched-agent-review":
            catalog, routing = staging_rows(
                directive, classification, through, term_number
            )
            catalog_rows.append(catalog)
            routing_rows.append(routing)
    return results, catalog_rows, routing_rows


def main() -> None:
    args = parse_args()
    if args.catalog_ids and not args.apply:
        raise SystemExit("--catalog-ids requires --apply.")
    directive_types = [value.strip() for value in args.types.split(",") if value.strip()]
    invalid = set(directive_types) - set(DIRECTIVE_TYPES)
    if invalid:
        raise SystemExit("Unknown directive types: " + ", ".join(sorted(invalid)))
    date.fromisoformat(args.through)
    if args.since:
        date.fromisoformat(args.since)

    terms = ["first", "second"] if args.term == "both" else [args.term]
    records = list(iter_active_records())
    all_results: list[dict[str, object]] = []
    all_catalog: list[dict[str, str]] = []
    all_routing: list[dict[str, str]] = []
    for term in terms:
        results, catalog_rows, routing_rows = scan_term(
            term,
            directive_types,
            args.through,
            args.since,
            records,
            fetch_full_text=args.fetch_text,
        )
        all_results.extend(results)
        all_catalog.extend(catalog_rows)
        all_routing.extend(routing_rows)

    counts = Counter(str(row["status"]) for row in all_results)
    report = {
        "schema_version": 1,
        "generated_at": date.today().isoformat(),
        "coverage_through": args.through,
        "term": args.term,
        "directive_types": directive_types,
        "full_text_signal_scan": args.fetch_text,
        "counts": {
            "input_directives": len(all_results),
            "existing_project_match": counts["existing-project-match"],
            "routine_ceremonial_no_project_action": counts[
                "routine-ceremonial-no-project-action"
            ],
            "corrections_attached": counts["correction-attached-no-new-directive"],
            "unmatched_agent_review": counts["unmatched-agent-review"],
            "text_retrieval_errors": sum(
                1 for row in all_results if row.get("text_retrieval_error")
            ),
        },
        "records": all_results,
    }

    if args.apply:
        requested_ids = {
            value.strip() for value in (args.catalog_ids or "").split(",") if value.strip()
        }
        if requested_ids:
            all_catalog, all_routing = select_staging_rows(
                all_catalog, all_routing, requested_ids
            )
        existing_catalog = read_csv(CATALOG)
        existing_routing = read_csv(ROUTING)
        if {row["catalog_id"] for row in existing_catalog} != {
            row["catalog_id"] for row in existing_routing
        }:
            raise SystemExit("Existing catalog and routing staging files are not reconciled.")
        write_csv(CATALOG, merge_staging(existing_catalog, all_catalog), CATALOG_FIELDS)
        write_csv(ROUTING, merge_staging(existing_routing, all_routing), ROUTING_FIELDS)
        report["staged_catalog_ids"] = [row["catalog_id"] for row in all_catalog]

    output = json.dumps(report, indent=2) + "\n"
    if args.report:
        report_path = args.report if args.report.is_absolute() else ROOT / args.report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
