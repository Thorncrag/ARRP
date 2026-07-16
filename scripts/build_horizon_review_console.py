#!/usr/bin/env python3
"""Build the data bundle for the internal ARRP Horizon intake review console."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research" / "trump-administration-legal-review-catalog.csv"
PRIORITY = ROOT / "research" / "trump-administration-priority-disposition-review.csv"
MEDIA = ROOT / "research" / "trump-administration-media-review-intake.csv"
OUTPUT = ROOT / "research" / "horizon-review-console" / "catalog-data.js"

# Preserve the source catalogs as historical research records while presenting
# current proposal routes in the review console after portfolio consolidation.
ROUTE_ALIASES = {
    "CIV-002": ["CIV-001"], "CIV-003": ["CIV-001"], "CIV-006": ["CIV-001"],
    "CIV-007": ["CIV-001"], "CIV-008": ["CIV-005"],
    "CLASS-002": ["CLASS-001"], "CLASS-003": ["CLASS-001"], "CLASS-005": ["CLASS-001"],
    "CLASS-007": ["CLASS-001"], "CLASS-008": ["CLASS-004"], "CLASS-009": ["CLASS-004"],
    "CLASS-010": ["CLASS-004"], "CLASS-012": ["CLASS-006"],
    "DOM-002": ["DOM-001"], "DOM-003": ["DOM-001"], "DOM-004": ["DOM-001"],
    "DOM-006": ["DOM-001"], "DOM-008": ["DOM-001"],
    "EMERG-002": ["FUND-001"], "EMERG-004": ["EMERG-001"], "EMERG-005": ["EMERG-001"],
    "EMERG-006": ["EMERG-001"], "EMERG-007": ["EMERG-001"], "EMERG-008": ["EMERG-001"],
    "FACT-002": ["FACT-001"], "FACT-003": ["FACT-001"], "FACT-004": ["FACT-001"],
    "FACT-005": ["FACT-001"], "FACT-006": ["FACT-001"], "FACT-008": ["FACT-001"],
    "FED-001": ["FED-003"], "FED-005": ["DOM-001"], "FED-006": ["ELEC-014"],
    "FED-007": ["FED-002"], "FED-008": ["FED-003"],
    "FUND-003": ["FUND-001"], "FUND-004": ["FED-003", "RET-001"],
    "FUND-005": ["FUND-001"], "FUND-006": ["FUND-001"], "FUND-007": ["FUND-001"],
    "FUND-008": ["FUND-001"],
    "IMM-003": ["IMM-001"], "IMM-004": ["IMM-001"], "IMM-005": ["IMM-001"],
    "IMM-006": ["IMM-001"], "IMM-007": ["IMM-001", "DOJ-007"], "IMM-008": ["DOJ-007"],
    "JUD-007": ["JUD-001"], "JUD-008": ["JUD-005"],
    "OVS-002": ["OVS-001"], "OVS-003": ["OVS-001"], "OVS-005": ["OVS-001"],
    "OVS-006": ["OVS-001"], "OVS-007": ["OVS-001"],
    "PRESS-002": ["PRESS-001"], "PRESS-004": ["PRESS-006"], "PRESS-005": ["PRESS-006"],
    "PRESS-007": ["FACT-001", "FACT-009"], "PRESS-008": ["PRESS-006"],
    "PRESS-009": ["PRESS-003"], "PRESS-010": ["PRESS-006"], "PRESS-011": ["PRESS-006"],
    "PRESS-012": ["PRESS-001", "PRESS-003", "PRESS-006"],
    "REG-007": ["REG-001"], "REG-008": ["REG-001"],
    "RIGHTS-004": ["RIGHTS-002", "A-14", "FED-003"],
}


PRELIMINARY_GAPS = [
    {
        "id": "INTAKE-GAP-001",
        "title": "Senior-official Hatch Act enforcement",
        "term": "1",
        "category": "Election integrity and official resources",
        "summary": (
            "Senior White House officials used official authority, personnel, property, communications, "
            "or events for campaign activity, while ordinary enforcement against presidential appointees "
            "depended substantially on presidential discipline. The present question is whether ARRP lacks "
            "a proposal addressing that enforcement gap."
        ),
        "review_prompt": (
            "Advance this question to formal Horizon duplicate and issue-admission review, including whether "
            "independent civil enforcement is needed and whether ELEC-012 or OVS-008 already owns the gap."
        ),
        "routes": "A-08; OVS-008; ELEC-012",
        "coverage": "advance-for-formal-horizon-adjudication",
        "normalization": "not an APPT issue; election and senior-official enforcement duplicate review required",
        "notes": "Approved for the next formal Horizon adjudication pass; no Horizon ID or proposal admission yet.",
        "links": [
            {
                "label": "Office of Special Counsel report",
                "url": "https://www.osc.gov/news/2021-11-09/osc-issues-hatch-act-report-documenting-violations-by-13-senior-trump-administration-officials-including-at-the-2020-republican-national-convention/",
            }
        ],
    },
    {
        "id": "INTAKE-GAP-002",
        "title": "Accessible presidential and executive communications",
        "term": "both",
        "category": "Disability access and presidential communications",
        "summary": (
            "Section 504 of the Rehabilitation Act already prohibits disability-based exclusion from programs "
            "or activities conducted by an Executive agency, and Executive Office regulations expressly cover "
            "the White House Office. In 2020 and again in November 2025, the U.S. District Court for the District "
            "of Columbia found plaintiffs likely to succeed under that duty and ordered ASL access for specified "
            "White House briefings. The unresolved institutional question is therefore not whether a legal duty "
            "exists, but whether Congress left its private enforceability or remedial path insufficiently explicit."
        ),
        "review_prompt": (
            "Should this advance only if the pending appeal or later proceedings reveal a recurring enforcement "
            "gap—such as no clear cause of action, delayed prospective relief, or unresolved coverage of particular "
            "presidential communications—rather than mere noncompliance with an existing duty?"
        ),
        "routes": "A-18; A-22; A-24; RIGHTS-001; JUD-001; JUD-005",
        "links": [
            {
                "label": "29 U.S.C. § 794 (Rehabilitation Act § 504)",
                "url": "https://uscode.house.gov/view.xhtml?edition=prelim&req=granuleid:USC-prelim-title29-section794",
            },
            {
                "label": "2020 district-court opinion",
                "url": "https://law.justia.com/cases/federal/district-courts/district-of-columbia/dcdce/1%3A2020cv02107/220596/18/",
            },
            {
                "label": "2025 district-court opinion",
                "url": "https://clearinghouse-umich-production.s3.amazonaws.com/media/doc/164821.pdf",
            },
            {
                "label": "Pending D.C. Circuit enforceability dispute",
                "url": "https://www.acludc.org/cases/national-association-of-the-deaf-v-trump-asl-interpretation-during-white-house-press-briefings-protecting-the-rule-of-law-and-separation-of-powers-by-urging-the-d-c-circuit-to-apply-the/",
            }
        ],
    },
    {
        "id": "INTAKE-GAP-003",
        "title": "Cross-agency repurposing of protected personal data",
        "term": "2",
        "category": "Privacy and interagency data use",
        "summary": (
            "Administrative records have reportedly been repurposed across agencies for immigration, election, "
            "or other enforcement objectives. The unresolved question is whether the recurring defect is broader "
            "than DOGE access, surveillance procurement, or a subject-specific manifestation."
        ),
        "review_prompt": (
            "Advance this question to a formal duplicate and scope review of unauthorized secondary use, purpose "
            "incompatibility, bulk disclosure, political use, and independent approval or auditing."
        ),
        "routes": "CIV-009; DOM-009; A-24",
        "coverage": "advance-for-formal-horizon-adjudication",
        "normalization": "privacy and data-governance duplicate review required; not an APPT issue",
        "notes": "Approved for the next formal Horizon adjudication pass; prefer expansion of an existing privacy home unless a broader recurring defect is established.",
        "links": [],
    },
    {
        "id": "INTAKE-GAP-004",
        "title": "Unofficial or inadequately supervised presidential representatives",
        "term": "2",
        "category": "Appointments and international representation",
        "summary": (
            "Private individuals or presidential relatives may exercise sustained diplomatic or governmental "
            "authority without appointment, defined duties, ethics coverage, records duties, security review, "
            "departmental supervision, or Senate-confirmed accountability."
        ),
        "review_prompt": (
            "Source-develop APPT-004 by distinguishing lawful special envoys, temporary presidential agents, "
            "advisers, and private intermediaries from persons exercising continuing significant authority."
        ),
        "routes": "APPT-004; A-06; A-13; A-15",
        "coverage": "incorporated-existing-candidate",
        "normalization": "incorporated into reframed APPT-004; HOR-028 integrated; no separate issue",
        "notes": "The appointment-status and accountability question is now part of APPT-004 source development rather than a separate preliminary or Horizon proposal.",
        "links": [
            {
                "label": "22 U.S.C. § 3942",
                "url": "https://uscode.house.gov/view.xhtml?req=%28title%3A22+section%3A3942+edition%3Aprelim%29",
            }
        ],
    },
    {
        "id": "INTAKE-GAP-005",
        "title": "Review evasion through withdrawal, replacement, settlement, or mootness",
        "term": "both",
        "category": "Judicial review and repeatability",
        "summary": (
            "Executive defendants may withdraw, replace, narrow, or settle a challenged action after imposing "
            "harm, potentially avoiding a durable merits precedent without repairing the underlying weakness."
        ),
        "review_prompt": (
            "Should this advance as a general, repeatable judicial-review gap after testing voluntary cessation "
            "and existing ARRP coverage?"
        ),
        "routes": "JUD-001; JUD-011; REG-006",
        "links": [],
    },
    {
        "id": "INTAKE-GAP-006",
        "title": "Threshold dismissal that leaves executive authority untested",
        "term": "both",
        "category": "Standing, reviewability, and remedies",
        "summary": (
            "Standing, ripeness, jurisdiction, reviewability, remedial limits, irreparable-harm findings, and "
            "emergency stays can leave executive authority unresolved while permitting the challenged action "
            "to operate. A government win therefore may not be a merits endorsement."
        ),
        "review_prompt": (
            "Should disposition-level review proceed to determine whether an existing subject proposal, a "
            "general judicial-review proposal, or no ARRP proposal should address the gap?"
        ),
        "routes": "JUD-001; JUD-011; subject-specific proposals",
        "links": [],
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def link(label: str, url: str) -> dict[str, str] | None:
    if not url.strip():
        return None
    return {"label": label, "url": url.strip()}


def current_routes(raw: str) -> str:
    """Translate historical candidate routes to active proposal homes for display."""
    routes: list[str] = []
    for route in (part.strip() for part in raw.split(";")):
        if not route:
            continue
        for current in ROUTE_ALIASES.get(route, [route]):
            if current not in routes:
                routes.append(current)
    return "; ".join(routes)


def candidate_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for gap in PRELIMINARY_GAPS:
        records.append(
            {
                **gap,
                "kind": "candidate_question",
                "period": "",
                "actor": "",
                "posture": "Preliminary research question; no Horizon ID assigned",
                "screening": "preliminary-coverage-gap",
                "source_family": "ARRP legal-review intake",
                "coverage": gap.get("coverage", "coverage-review-needed"),
                "normalization": gap.get(
                    "normalization", "full duplicate, legal, and political-failure review required"
                ),
                "priority": True,
                "notes": gap.get(
                    "notes",
                    "A Yes decision advances this question for formal Horizon adjudication; it does not admit an issue.",
                ),
            }
        )
    return records


def source_records(priority_ids: set[str]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in read_csv(CATALOG):
        links = [
            link("Source entry", row["source_entry_url"]),
            link("Representative case", row["representative_case_url"]),
            link("Official action", row["official_action_url"]),
        ]
        records.append(
            {
                "id": row["catalog_id"],
                "kind": "source_record",
                "title": row["action_or_policy"],
                "term": row["term"],
                "category": row["record_type"].replace("-", " "),
                "summary": row["legal_question_or_outcome"],
                "review_prompt": (
                    "Should this record be included in the next Horizon synthesis and duplicate-check pass?"
                ),
                "period": row["action_date_or_period"],
                "actor": row["responsible_actor_or_category"],
                "posture": row["litigation_posture"],
                "screening": row["screening_track"],
                "source_family": row["source_family"],
                "coverage": row["arrp_coverage_status"],
                "routes": current_routes(row["provisional_arrp_routes"]),
                "normalization": row["normalization_status"],
                "priority": row["catalog_id"] in priority_ids,
                "links": [item for item in links if item],
                "notes": row["notes"],
                "representative_case": row["representative_case"],
                "last_checked": row["last_checked"],
            }
        )
    return records


def media_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in read_csv(MEDIA):
        links = [
            link(row["source_1_name"], row["source_1_url"]),
            link(row["source_2_name"], row["source_2_url"]),
            link(row["primary_source_name"], row["primary_source_url"]),
        ]
        records.append(
            {
                "id": row["media_id"],
                "kind": "media_episode",
                "title": row["episode"],
                "term": row["term"],
                "category": "media-supported episode",
                "summary": row["institutional_question"],
                "review_prompt": (
                    "Should this independently corroborated episode advance to formal Horizon synthesis, "
                    "duplicate review, or an existing proposal's manifestation record?"
                ),
                "period": row["date_or_period"],
                "actor": "",
                "posture": row["screening_recommendation"].replace("-", " "),
                "screening": row["screening_recommendation"],
                "source_family": f"{row['source_1_name']} + {row['source_2_name']}",
                "coverage": row["arrp_coverage_status"],
                "routes": current_routes(row["provisional_arrp_routes"]),
                "normalization": row["primary_source_status"],
                "priority": row["screening_recommendation"].startswith("advance-"),
                "links": [item for item in links if item],
                "notes": row["notes"],
                "representative_case": "",
                "last_checked": row["last_checked"],
            }
        )
    return records


def main() -> None:
    priority_ids = {row["catalog_id"] for row in read_csv(PRIORITY)}
    media = media_records()
    source = source_records(priority_ids)
    records = candidate_records() + media + source
    catalog_rows = len(source)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "catalog_source": CATALOG.name,
        "catalog_records": catalog_rows,
        "candidate_questions": len(PRELIMINARY_GAPS),
        "media_episodes": len(media),
        "priority_records": len(priority_ids),
        "records": records,
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    serialized = serialized.replace("</", "<\\/")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "/* Generated by scripts/build_horizon_review_console.py. */\n"
        f"window.ARRP_HORIZON_REVIEW_DATA={serialized};\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {OUTPUT.relative_to(ROOT)} with {len(records):,} review records "
        f"({len(PRELIMINARY_GAPS)} candidate questions, {len(media)} media episodes, "
        f"and {catalog_rows:,} source records)."
    )


if __name__ == "__main__":
    main()
