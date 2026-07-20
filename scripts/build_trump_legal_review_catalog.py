#!/usr/bin/env python3
"""Build a temporary tracker-extraction catalog for ARRP source review.

The script transforms locally downloaded HTML snapshots from four public
trackers into a common CSV. It deliberately preserves source-level records;
cross-source deduplication and ARRP issue admission are later human reviews.

This is research tooling, not a finding that every listed action was unlawful.
It requires lxml and accepts any subset of the supported inputs.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

try:
    from lxml import html
except ImportError as exc:  # pragma: no cover - environment guidance
    raise SystemExit("This research extraction script requires lxml.") from exc


JUST_SECURITY_URL = (
    "https://www.justsecurity.org/107087/"
    "tracker-litigation-legal-challenges-trump-administration/"
)
POLICY_INTEGRITY_URL = "https://policyintegrity.org/trump-court-roundup"
IMMIGRATION_TRACKER_URL = "https://immpolicytracking.org/policies/?status=in-litigation"
HUMAN_RIGHTS_TRACKER_URL = "https://trumphumanrightstracker.law.columbia.edu/"
RETALIATION_TRACKER_URL = "https://protectdemocracy.org/work/retaliatory-action-tracker/"
PUBLIC_CITIZEN_URL = "https://www.citizen.org/article/trump-administration-2-0-lawsuit-tracker/"
SILENCING_SCIENCE_URL = "https://silencingscience.org/"


FIELDS = [
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

PRIORITY_FIELDS = [
    "catalog_id",
    "term",
    "action_or_case",
    "preliminary_disposition_class",
    "litigation_posture",
    "disposition_basis_excerpt",
    "institutional_screen",
    "provisional_arrp_routes",
    "source_family",
    "source_entry_url",
    "representative_case_url",
    "official_action_url",
    "review_status",
    "last_checked",
]


def clean(value: str) -> str:
    return " ".join(value.split())


def node_text(node) -> str:
    return clean(" ".join(node.itertext()))


def class_xpath(name: str) -> str:
    return f'contains(concat(" ", normalize-space(@class), " "), " {name} ")'


def first(values, default=""):
    return values[0] if values else default


def provisional_routes(text: str) -> str:
    """Return broad, non-dispositive ARRP routes for later manual cross-check."""
    t = text.lower()
    routes: list[str] = []
    rules = [
        (("election", "voter", "voting", "ballot"), "ELEC-001; A-02"),
        (("campaign", "hatch act", "partisan"), "A-08; OVS-008; ELEC-012"),
        (("immigra", "asylum", "refugee", "visa", "deport", "removal", "alien enemies", "border"), "RIGHTS-002; RIGHTS-003; RIGHTS-004; A-14"),
        (("independent agency", "removal of independent", "agency leader", "agency operations", "usaid", "institute of peace", "department of education"), "REG-001"),
        (("grant", "funding", "appropriat", "impound", "loan", "federal assistance"), "A-11; FED-003; A-19; JUD-011"),
        (("law firm", "university", "retaliat", "security clearance"), "RET-001; A-19"),
        (("prosecut", "criminal investigation", "department of justice", "fbi", "charging"), "DOJ-002; DOJ-003; DOJ-007"),
        (("press", "journalist", "news media", "broadcast", "usagm"), "A-22"),
        (("record", "foia", "website", "dataset", "information removal"), "A-13; A-18"),
        (("science", "scientific", "statistic", "climate data", "public health guidance"), "A-18"),
        (("doge", "civil service", "federal employee", "career", "reduction in force", "union", "labor"), "A-08; CIV-009"),
        (("inspector general", "whistleblower", "ethics"), "A-09"),
        (("acting official", "vacancies reform", "appointment", "senate confirm"), "A-12"),
        (("tariff", "ieepa", "emergency economic"), "EMERG-003"),
        (("national emergency", "emergency declaration", "emergency authority"), "A-10"),
        (("military", "national guard", "airstrike", "use of force", "civilian casualt"), "WAR-001; A-14"),
        (("monument", "historic", "museum", "library", "civic"), "A-23"),
        (("state law", "state and local", "sanctuary", "congestion pricing", "federalism"), "A-20"),
        (("emolument", "conflict of interest", "trump organization", "presidential business"), "A-06"),
        (("pardon", "clemency"), "A-05"),
        (("presidential record", "archives"), "A-13"),
        (("social media", "official account"), "A-13; A-22; HOR-029"),
        (("international criminal court",), "EMERG-003; HOR-030"),
        (("international organization", "withdrawal from", "world health organization"), "HOR-026"),
        (("court order", "noncompliance", "contempt"), "JUD-001; JUD-005"),
        (("birthright",), "RIGHTS-003"),
        (("temporary protected status", "tps"), "RIGHTS-002"),
        (("gender", "transgender", "lgbt", "civil rights", "discrimination"), "RIGHTS-001"),
        (("surveillance", "data sharing", "privacy", "personal data"), "DOM-009; CIV-009; A-24"),
    ]
    for needles, route in rules:
        if any(n in t for n in needles):
            for part in route.split("; "):
                if part not in routes:
                    routes.append(part)
    return "; ".join(routes)


def base_record(**values) -> dict[str, str]:
    row = {field: "" for field in FIELDS}
    row.update(values)
    combined = " ".join(
        [row["action_or_policy"], row["responsible_actor_or_category"], row["legal_question_or_outcome"]]
    )
    routes = provisional_routes(combined)
    row["provisional_arrp_routes"] = routes
    row["arrp_coverage_status"] = (
        "possible-existing-coverage" if routes else "coverage-review-needed"
    )
    row["normalization_status"] = "source-normalized; cross-source deduplication pending"
    row["last_checked"] = date.today().isoformat()
    return row


def preliminary_disposition(row: dict[str, str]) -> tuple[str, str]:
    text = f'{row["litigation_posture"]} {row["legal_question_or_outcome"]}'.lower()
    if any(
        phrase in text
        for phrase in (
            "unreviewable",
            "lack of standing",
            "lacked standing",
            "jurisdiction",
            "waived their claims",
            "dismissed",
            "moot",
            "not ripe",
        )
    ):
        kind = "threshold-or-reviewability-disposition"
        screen = "High priority: determine whether standing, jurisdiction, reviewability, waiver, or mootness left executive authority untested."
    elif any(
        phrase in text
        for phrase in (
            "denied a motion to enjoin",
            "denied plaintiffs’ motion for an order enjoining",
            "declined to enjoin",
            "denied a motion for a preliminary injunction",
            "denied a request to vacate",
            "denied a motion for a stay",
            "irreparable harm",
            "temporary block",
        )
    ):
        kind = "preliminary-or-remedial-denial"
        screen = "Do not treat as merits approval; identify later merits posture and whether harm occurred before effective review."
    elif any(phrase in text for phrase in ("reversed", "however", "separately", "majority of", "in several respects")):
        kind = "mixed-or-later-modified-disposition"
        screen = "Normalize claim-by-claim and appellate history before identifying any institutional gap."
    elif any(
        phrase in text
        for phrase in (
            "upheld",
            "permissible interpretation",
            "had not violated",
            "did not violate",
            "complied with",
            "consistent with",
            "not arbitrary and capricious",
            "was not arbitrary and capricious",
            "had authority",
            "rejected a challenge",
        )
    ):
        kind = "apparent-merits-permission"
        screen = "Review whether the permitted action reveals a generalizable statutory or procedural weakness rather than a substantive policy disagreement."
    else:
        kind = "manual-disposition-review-required"
        screen = "Read the controlling opinion and code the exact merits, threshold, finality, and remedy grounds."
    return kind, screen


def write_priority_review(rows: list[dict[str, str]], output: Path) -> None:
    priority = [
        row
        for row in rows
        if row["screening_track"]
        in {
            "priority-review-action-permitted",
            "priority-review-action-permitted-or-challenge-dismissed",
        }
    ]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PRIORITY_FIELDS)
        writer.writeheader()
        for row in priority:
            kind, screen = preliminary_disposition(row)
            writer.writerow(
                {
                    "catalog_id": row["catalog_id"],
                    "term": row["term"],
                    "action_or_case": row["action_or_policy"],
                    "preliminary_disposition_class": kind,
                    "litigation_posture": row["litigation_posture"],
                    "disposition_basis_excerpt": row["legal_question_or_outcome"],
                    "institutional_screen": screen,
                    "provisional_arrp_routes": row["provisional_arrp_routes"],
                    "source_family": row["source_family"],
                    "source_entry_url": row["source_entry_url"],
                    "representative_case_url": row["representative_case_url"],
                    "official_action_url": row["official_action_url"],
                    "review_status": "preliminary text classification; controlling opinion review pending",
                    "last_checked": row["last_checked"],
                }
            )


def parse_just_security(path: Path) -> list[dict[str, str]]:
    doc = html.parse(str(path))
    tables = doc.xpath('//table[@id="tablepress-42"]')
    if not tables:
        raise ValueError(f"Just Security tablepress-42 not found in {path}")
    table = tables[0]
    headers = [node_text(x) for x in table.xpath(".//thead//th")]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for tr in table.xpath(".//tbody/tr"):
        cells = tr.xpath("./td")
        if len(cells) != len(headers):
            continue
        data = {headers[i]: node_text(cells[i]) for i in range(len(headers))}
        data["_cells"] = {headers[i]: cells[i] for i in range(len(headers))}
        action = data.get("Executive Action", "").strip()
        if action:
            grouped[action].append(data)

    output = []
    for index, action in enumerate(sorted(grouped), 1):
        rows = grouped[action]
        statuses = Counter(r.get("Case Status", "") for r in rows)
        summary = "; ".join(f"{k}={v}" for k, v in sorted(statuses.items()))
        open_markers = (
            "Pending",
            "Temporarily",
            "Pending Appeal",
            "Temporary Block",
        )
        if any(any(marker in status for marker in open_markers) for status in statuses):
            track = "monitor-open-or-interlocutory-litigation"
            posture = "open or interlocutory; " + summary
        elif statuses and set(statuses) <= {"Case Closed/Dismissed in Favor of Government"}:
            track = "priority-review-action-permitted-or-challenge-dismissed"
            posture = "closed in favor of government; " + summary
        elif "Case Closed in Favor of Plaintiff" in statuses and len(statuses) == 1:
            track = "resolved-action-blocked-review-repeatability"
            posture = "closed in favor of plaintiff; " + summary
        else:
            track = "resolved-or-mixed-posture-manual-review"
            posture = summary

        representative = rows[0]
        case_cell = representative["_cells"].get("Case Name")
        case_link = first(case_cell.xpath('.//a[contains(@href,"courtlistener.com")]/@href')) if case_cell is not None else ""
        summary_cell = representative["_cells"].get("Case Summary")
        action_links = summary_cell.xpath(".//a[@href]/@href") if summary_cell is not None else []
        official = first(
            [
                u
                for u in action_links
                if any(host in u for host in ("federalregister.gov", "whitehouse.gov", "govinfo.gov"))
            ]
        )
        dates = sorted(r.get("Date Case Filed", "") for r in rows if r.get("Date Case Filed", ""))
        output.append(
            base_record(
                catalog_id=f"TAC-JS2-{index:03d}",
                term="2",
                record_type="litigated-action-cluster",
                action_or_policy=action,
                action_date_or_period=(f"case filings {dates[0]} to {dates[-1]}" if dates else ""),
                responsible_actor_or_category=representative.get("Issue", ""),
                legal_question_or_outcome=representative.get("Case Summary", "")[:1200],
                litigation_posture=posture,
                screening_track=track,
                source_family="Just Security litigation tracker",
                source_entry_url=JUST_SECURITY_URL,
                representative_case=representative.get("Case Name", ""),
                representative_case_url=case_link,
                official_action_url=official,
                notes=f"{len(rows)} case row(s) consolidated under the tracker's Executive Action label.",
            )
        )
    return output


def parse_policy_integrity(path: Path) -> list[dict[str, str]]:
    doc = html.parse(str(path))
    items = doc.xpath(f'//li[{class_xpath("deregulation-item")}]')
    output = []
    for index, item in enumerate(items, 1):
        entry = first(item.xpath(f'./div[{class_xpath("deregulation-entry")}]'))
        if entry is None:
            continue
        paragraphs = entry.xpath("./p")
        case_name = node_text(paragraphs[0]) if paragraphs else node_text(entry)
        outcome_text = " ".join(node_text(p) for p in paragraphs[1:])
        outcome = item.get("data-outcome", "")
        category = item.get("data-category", "").replace(",", "; ")
        links = entry.xpath(".//a[@href]/@href")
        official = first(
            [u for u in links if any(host in u for host in ("federalregister.gov", "govinfo.gov", "gpo.gov"))]
        )
        case_url = first([u for u in links if u != official])
        if outcome == "successful":
            posture = "adjudicated-action-permitted"
            track = "priority-review-action-permitted"
        else:
            posture = "adjudicated-action-blocked-or-withdrawn"
            track = "lower-priority-review-repeatability-or-incomplete-relief"
        date_match = re.match(r"^([^:]{4,30}):", outcome_text)
        output.append(
            base_record(
                catalog_id=f"TAC-IPI1-{index:03d}",
                term="1",
                record_type="adjudicated-agency-action",
                action_or_policy=case_name,
                action_date_or_period=date_match.group(1) if date_match else "",
                responsible_actor_or_category=category,
                legal_question_or_outcome=outcome_text[:1800],
                litigation_posture=posture,
                screening_track=track,
                source_family="Institute for Policy Integrity Trump court roundup",
                source_entry_url=POLICY_INTEGRITY_URL,
                representative_case=case_name,
                representative_case_url=case_url,
                official_action_url=official,
                notes=(
                    "Tracker outcome terminology preserved: successful means the agency won without "
                    "withdrawing the challenged action; unsuccessful means a court ruled against the "
                    "agency or the agency withdrew after suit."
                ),
            )
        )
    return output


def parse_immigration(paths: list[Path]) -> list[dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for path in paths:
        doc = html.parse(str(path))
        for item in doc.xpath(f'//li[{class_xpath("policy-row")}]'):
            link = first(item.xpath(f'.//a[{class_xpath("timeline__l2__heading-link")}]'))
            if not hasattr(link, "get"):
                continue
            url = urljoin("https://immpolicytracking.org", link.get("href", ""))
            title = node_text(link)
            announced = first(item.xpath(f'.//span[{class_xpath("announced-date")}]'))
            date_text = node_text(announced) if announced is not None else ""
            term = "2" if item.xpath(f'.//span[{class_xpath("second-term-tag")}]') else "1"
            labels = [node_text(x) for x in item.xpath(f'.//span[{class_xpath("meta__label")}]')]
            records[url] = {
                "term": term,
                "title": title,
                "date": date_text,
                "labels": "; ".join(labels),
            }

    output = []
    for index, (url, data) in enumerate(sorted(records.items(), key=lambda pair: (pair[1]["term"], pair[1]["date"], pair[1]["title"])), 1):
        output.append(
            base_record(
                catalog_id=f"TAC-IPT-{index:03d}",
                term=data["term"],
                record_type="immigration-policy-marked-in-litigation",
                action_or_policy=data["title"],
                action_date_or_period=data["date"],
                responsible_actor_or_category=data["labels"],
                legal_question_or_outcome="Tracker marks this policy action as subject to litigation; case and final-posture normalization remains pending.",
                litigation_posture="litigation identified; current or final posture not yet normalized",
                screening_track="posture-normalization-required-before-horizon-screen",
                source_family="Immigration Policy Tracking Project",
                source_entry_url=url,
                notes=f"Discovered through {IMMIGRATION_TRACKER_URL}",
            )
        )
    return output


def parse_human_rights(path: Path) -> list[dict[str, str]]:
    doc = html.parse(str(path))
    items = doc.xpath(f'//div[{class_xpath("entry")}]')
    output = []
    for index, item in enumerate(items, 1):
        title_node = first(item.xpath(f'./h2[{class_xpath("entry-title")}]'))
        if title_node is None:
            continue
        date_node = first(item.xpath(f'.//span[{class_xpath("entry-date")}]'))
        content_node = first(item.xpath(f'./div[{class_xpath("entry-content")}]'))
        source_links = item.xpath(f'.//div[{class_xpath("entry-sidebar")}]/descendant::a[@href]/@href')
        output.append(
            base_record(
                catalog_id=f"TAC-HRT1-{index:03d}",
                term="1",
                record_type="human-rights-impact-discovery-lead",
                action_or_policy=node_text(title_node),
                action_date_or_period=node_text(date_node) if date_node is not None else "",
                legal_question_or_outcome=node_text(content_node)[:1600] if content_node is not None else "",
                litigation_posture="not necessarily litigated; legal-threshold verification required",
                screening_track="verify-legal-question-and-institutional-defect",
                source_family="Columbia Trump Administration Human Rights Tracker",
                source_entry_url=HUMAN_RIGHTS_TRACKER_URL,
                representative_case_url=first(source_links),
                notes="Discovery source uses a human-rights impact standard; inclusion is not an ARRP legal conclusion.",
            )
        )
    return output


def parse_retaliation(path: Path) -> list[dict[str, str]]:
    doc = html.parse(str(path))
    cards = doc.xpath(f'//div[{class_xpath("item-card")}]')
    output = []
    for index, card in enumerate(cards, 1):
        header = first(card.xpath(f'./div[{class_xpath("card-header")}]'))
        body = first(card.xpath(f'./div[{class_xpath("card-body")}]'))
        if header is None:
            continue
        header_text = node_text(header)
        status_match = re.search(r"Status\s+(Ongoing|Failed|Succeeded|Closed|Resolved)", header_text, re.I)
        status = status_match.group(1) if status_match else "not normalized"
        name = re.sub(r"\s+Status\s+.*$", "", header_text, flags=re.I)
        links = card.xpath(".//a[@href]/@href")
        output.append(
            base_record(
                catalog_id=f"TAC-RAT2-{index:03d}",
                term="2",
                record_type="retaliatory-enforcement-discovery-lead",
                action_or_policy=name,
                legal_question_or_outcome=node_text(body)[:1800] if body is not None else "",
                litigation_posture=f"tracker status: {status}",
                screening_track=(
                    "monitor-open-enforcement-or-litigation" if status.lower() == "ongoing" else "review-completed-retaliation-posture"
                ),
                source_family="Protect Democracy Retaliatory Actions Tracker",
                source_entry_url=RETALIATION_TRACKER_URL,
                representative_case_url=first([u for u in links if "courtlistener.com" in u]),
                notes="Tracker applies stated retaliation indicators; ARRP must independently verify motive, process, and outcome.",
            )
        )
    return output


def parse_public_citizen(path: Path) -> list[dict[str, str]]:
    doc = html.parse(str(path))
    tables = doc.xpath("//table")
    if not tables:
        return []
    table = tables[0]
    headers = [node_text(x) for x in table.xpath(".//th")]
    output = []
    for index, tr in enumerate(table.xpath(".//tbody/tr"), 1):
        cells = tr.xpath("./td")
        if len(cells) != len(headers):
            continue
        data = {headers[i]: node_text(cells[i]) for i in range(len(headers))}
        links = tr.xpath(".//a[@href]/@href")
        status = data.get("Status", "")
        status_lower = status.lower()
        if any(word in status_lower for word in ("pending", "filed", "briefing", "underway", "appeal")):
            track = "monitor-open-or-interlocutory-litigation"
        else:
            track = "resolved-or-mixed-posture-manual-review"
        output.append(
            base_record(
                catalog_id=f"TAC-PCT2-{index:03d}",
                term="2",
                record_type="plaintiff-litigation-action-record",
                action_or_policy=data.get("Topic", ""),
                action_date_or_period=data.get("Date Filed", ""),
                responsible_actor_or_category=data.get("Case Number", ""),
                legal_question_or_outcome=data.get("Description", "")[:1600],
                litigation_posture=status,
                screening_track=track,
                source_family="Public Citizen Trump Administration 2.0 Lawsuit Tracker",
                source_entry_url=PUBLIC_CITIZEN_URL,
                representative_case=data.get("Lawsuit", ""),
                representative_case_url=first(links),
                notes="Plaintiff-maintained tracker; source provenance retained pending cross-tracker deduplication and docket verification.",
            )
        )
    return output


def parse_silencing_science(paths: list[Path]) -> list[dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for path in paths:
        doc = html.parse(str(path))
        for article in doc.xpath(f'//article[{class_xpath("sst_action")}]'):
            link = first(article.xpath(f'.//h2[{class_xpath("entry-title")}]/a[@href]'))
            if hasattr(link, "get"):
                url = link.get("href", "")
                title = node_text(link)
            else:
                url = first(doc.xpath('//link[@rel="canonical"]/@href'))
                title = clean(first(doc.xpath(f'//h1[{class_xpath("entry-title")}]/text()')))
                if not url or not title:
                    continue
            text = node_text(article)
            if "Trump Administration (First)" in text:
                term = "1"
            elif "Trump Administration (Second)" in text:
                term = "2"
            else:
                continue
            date_match = re.search(r"(?:Action )?Date:\s*(.+?)\s+Explanation:", text)
            explanation_match = re.search(r"Explanation:\s*(.+?)\s+Scientists Affected:", text)
            agency_match = re.search(r"Agency\(s\):\s*(.+?)\s+Presidential Administration:", text)
            summary_match = re.search(r"Summary:\s*(.+?)\s+Update Status:", text)
            if not summary_match:
                summary_match = re.search(
                    r"Presidential Administration:\s*Trump Administration \((?:First|Second)\)\s*(.+?)(?:\s+Update Status:|\s+Sources?:|$)",
                    text,
                )
            update_match = re.search(r"Update Status:\s*(.+)$", text)
            records[url] = {
                "term": term,
                "title": title,
                "date": date_match.group(1) if date_match else "",
                "explanation": explanation_match.group(1) if explanation_match else "",
                "agency": agency_match.group(1) if agency_match else "",
                "summary": summary_match.group(1) if summary_match else "",
                "update": update_match.group(1) if update_match else "",
            }

    output = []
    for index, (url, data) in enumerate(sorted(records.items()), 1):
        output.append(
            base_record(
                catalog_id=f"TAC-SST-{index:03d}",
                term=data["term"],
                record_type="science-integrity-discovery-lead",
                action_or_policy=data["title"],
                action_date_or_period=data["date"],
                responsible_actor_or_category=f'{data["agency"]}; {data["explanation"]}'.strip("; "),
                legal_question_or_outcome=data["summary"][:1800],
                litigation_posture=f'specialist tracker update status: {data["update"]}',
                screening_track="verify-legal-question-and-institutional-defect",
                source_family="Silencing Science Tracker",
                source_entry_url=url,
                notes=(
                    "Specialist science-integrity source. Budget proposals, statements, policy choices, "
                    "and state or non-Trump records were not treated as legal conclusions; only entries "
                    "coded by the source to a Trump administration were retained."
                ),
            )
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--just-security", type=Path)
    parser.add_argument("--policy-integrity", type=Path)
    parser.add_argument("--immigration", type=Path, nargs="*")
    parser.add_argument("--human-rights", type=Path)
    parser.add_argument("--retaliation", type=Path)
    parser.add_argument("--public-citizen", type=Path)
    parser.add_argument("--silencing-science", type=Path, nargs="*")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--priority-output", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    if args.just_security:
        rows.extend(parse_just_security(args.just_security))
    if args.policy_integrity:
        rows.extend(parse_policy_integrity(args.policy_integrity))
    if args.immigration:
        rows.extend(parse_immigration(args.immigration))
    if args.human_rights:
        rows.extend(parse_human_rights(args.human_rights))
    if args.retaliation:
        rows.extend(parse_retaliation(args.retaliation))
    if args.public_citizen:
        rows.extend(parse_public_citizen(args.public_citizen))
    if args.silencing_science:
        rows.extend(parse_silencing_science(args.silencing_science))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} source-normalized records to {args.output}")
    if args.priority_output:
        write_priority_review(rows, args.priority_output)
        print(f"wrote priority disposition review to {args.priority_output}")


if __name__ == "__main__":
    main()
