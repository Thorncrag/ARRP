#!/usr/bin/env python3
"""Complete the route-centered adjudication of the Trump legal-review catalog.

This migration applies the project's qualitative evidence architecture to the
already normalized catalog.  It deliberately does not treat every tracker row
as an ARRP manifestation.  It retains current litigation for monitoring,
selects representative high-value source-development leads, routes incomplete
but useful episodes to the existing-record integration queue, and removes
cumulative, topical-only, or insufficiently specific records from the active
intake.  Git history and the batch report preserve the completed intake state.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from source_adjudication_common import (
    merge_routes,
    normalize_url,
    read_csv,
    source_urls,
    split_routes,
    write_csv,
    write_csv_preserving_unchanged,
)
from build_horizon_evidence_routing import (
    FORMAL_HORIZON_EVIDENCE,
    IPI_REVIEW_EVASION_IDS,
    IPI_TIMELY_MERITS_REVIEW_IDS,
    JUST_SECURITY_HORIZON_ROUTES,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research" / "trump-administration-legal-review-catalog.csv"
ROUTING = ROOT / "research" / "trump-administration-evidence-routing.csv"
PRIORITY = ROOT / "research" / "trump-administration-priority-disposition-review.csv"
INTEGRATION = ROOT / "research" / "existing-issue-evidence-integration.csv"
MONITORING = ROOT / "research" / "trump-administration-litigation-monitoring.csv"
SOURCES = ROOT / "inventory" / "sources.csv"
REPORT = ROOT / "research" / "trump-administration-source-adjudication-report.md"

TODAY = "2026-07-16"

MONITOR_FIELDS = [
    "monitor_id",
    "catalog_ids",
    "evidence_group",
    "integration_routes",
    "action_or_policy",
    "litigation_posture",
    "canonical_source_ids",
    "source_family",
    "monitoring_status",
    "revisit_trigger",
    "last_checked",
    "notes",
]

INTEGRATION_FIELDS = [
    "catalog_id",
    "canonical_source_ids",
    "integration_routes",
    "integration_status",
    "action_or_policy",
    "legal_question_or_outcome",
    "litigation_posture",
    "source_family",
    "source_entry_url",
    "representative_case_url",
    "official_action_url",
    "preliminary_disposition",
    "review_note",
    "last_reviewed",
]

STOPWORDS = {
    "a", "an", "and", "against", "at", "by", "for", "from", "in", "of",
    "on", "or", "the", "to", "toward", "towards", "united", "states", "v",
    "versus", "with",
}

FAMILY_LABELS = {
    "Just Security litigation tracker": "Just Security",
    "Institute for Policy Integrity Trump court roundup": "Institute for Policy Integrity",
    "Immigration Policy Tracking Project": "Immigration Policy Tracking Project",
    "Columbia Trump Administration Human Rights Tracker": "Columbia Law School",
    "Protect Democracy Retaliatory Actions Tracker": "Protect Democracy",
    "Public Citizen Trump Administration 2.0 Lawsuit Tracker": "Public Citizen",
    "Silencing Science Tracker": "Climate Science Legal Defense Fund and Sabin Center",
}

FAMILY_CAPS = {
    "Institute for Policy Integrity Trump court roundup": 12,
    "Immigration Policy Tracking Project": 35,
    "Columbia Trump Administration Human Rights Tracker": 12,
    "Silencing Science Tracker": 36,
}

ROUTE_CAPS = {
    "RIGHTS-002": 20,
    "DOM-001": 12,
    "FACT-001": 36,
    "FUND-001": 8,
    "REG-003": 8,
    "FED-003": 8,
    "REG-006": 12,
}

SCIENCE_INTEGRITY_CATEGORIES = {
    "government censorship",
    "bias and misrepresentation",
    "research hindrance",
    "self-censorship",
}

SCIENCE_EVIDENCE_TERMS = re.compile(
    r"assess|censor|claim|communicat|data|database|delete|finding|guidance|"
    r"information|integrity|message|misrepresent|publish|publication|report|"
    r"scientific study|scrub|terminology|website|word",
    re.I,
)

HUMAN_RIGHTS_MECHANISM_TERMS = re.compile(
    r"access to lawyer|censor|civil rights investigation|data|deported without|"
    r"forced|human rights report|impeded|information|privacy|record|report|separat|tracked|"
    r"unable and unwilling|website",
    re.I,
)

FORMAL_HORIZON_ROUTES_BY_ID = {
    **FORMAL_HORIZON_EVIDENCE,
    **JUST_SECURITY_HORIZON_ROUTES,
    **{catalog_id: "HOR-035" for catalog_id in IPI_REVIEW_EVASION_IDS},
    **{catalog_id: "HOR-036" for catalog_id in IPI_TIMELY_MERITS_REVIEW_IDS},
}

INSTITUTIONAL_TERMS = re.compile(
    r"access|adjudicat|appeal|archive|asylum|censor|citizen|compliance|condition|"
    r"court|data|detain|disclos|enjoin|evidence|fund|grant|hearing|information|"
    r"investigat|judge|notice|order|oversight|privacy|publication|record|remov|"
    r"report|retaliat|rule|science|suppress|terminat|transparen|website|withhold",
    re.I,
)


@dataclass
class Episode:
    group: str
    records: list[dict[str, str]]
    routes: list[str]
    primary: dict[str, str]
    score: int
    disposition: str = ""
    reason: str = ""


class UnionFind:
    def __init__(self, keys: list[str]) -> None:
        self.parent = {key: key for key in keys}

    def find(self, key: str) -> str:
        while self.parent[key] != key:
            self.parent[key] = self.parent[self.parent[key]]
            key = self.parent[key]
        return key

    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[b] = a


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def tokens(value: str) -> set[str]:
    return {
        word for word in re.findall(r"[a-z0-9]+", value.lower())
        if word not in STOPWORDS and len(word) > 2
    }


def cluster_records(
    catalog: list[dict[str, str]], routing: dict[str, dict[str, str]]
) -> list[Episode]:
    """Conservatively join exact instruments and strong cross-source title matches."""
    ids = [row["catalog_id"] for row in catalog]
    uf = UnionFind(ids)
    identity: dict[str, str] = {}
    for row in catalog:
        title_key = " ".join(sorted(tokens(row["action_or_policy"])))
        if title_key:
            key = f"title:{row['term']}:{title_key}"
            if key in identity:
                uf.union(row["catalog_id"], identity[key])
            else:
                identity[key] = row["catalog_id"]
        for field in ("official_action_url", "representative_case_url"):
            key = normalize_url(row[field])
            if not key:
                continue
            key = f"url:{key}"
            if key in identity:
                uf.union(row["catalog_id"], identity[key])
            else:
                identity[key] = row["catalog_id"]

    by_term: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in catalog:
        by_term[row["term"]].append(row)
    for rows in by_term.values():
        for index, left in enumerate(rows):
            left_tokens = tokens(left["action_or_policy"])
            if len(left_tokens) < 4:
                continue
            for right in rows[index + 1 :]:
                if left["source_family"] == right["source_family"]:
                    continue
                right_tokens = tokens(right["action_or_policy"])
                if len(right_tokens) < 4:
                    continue
                union = left_tokens | right_tokens
                similarity = len(left_tokens & right_tokens) / len(union)
                containment = len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))
                if similarity >= 0.72 or (containment >= 0.88 and len(left_tokens & right_tokens) >= 5):
                    uf.union(left["catalog_id"], right["catalog_id"])

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in catalog:
        grouped[uf.find(row["catalog_id"])].append(row)

    episodes: list[Episode] = []
    for rows in grouped.values():
        all_routes: list[str] = []
        for row in rows:
            all_routes = merge_routes(all_routes, split_routes(routing[row["catalog_id"]]["integration_routes"]))
        primary = max(rows, key=record_score)
        digest = hashlib.sha1(";".join(sorted(row["catalog_id"] for row in rows)).encode()).hexdigest()[:12]
        episodes.append(
            Episode(
                group=f"EP-{digest.upper()}",
                records=sorted(rows, key=lambda row: row["catalog_id"]),
                routes=all_routes,
                primary=primary,
                score=max(record_score(row) for row in rows),
            )
        )
    return sorted(episodes, key=lambda episode: episode.primary["catalog_id"])


def record_score(row: dict[str, str]) -> int:
    text = " ".join(
        (row["action_or_policy"], row["legal_question_or_outcome"], row["litigation_posture"])
    )
    score = 0
    score += 5 if row["official_action_url"].strip() else 0
    score += 5 if row["representative_case_url"].strip() else 0
    score += 2 if row["term"] == "2" else 0
    score += 2 if INSTITUTIONAL_TERMS.search(text) else 0
    score += 2 if re.search(r"held|vacat|enjoin|dismiss|final|closed", row["litigation_posture"], re.I) else 0
    score += 1 if re.search(r"statut|constitution|jurisdiction|standing|reviewab|moot", text, re.I) else 0
    return score


def is_open_episode(episode: Episode) -> bool:
    return any(
        row["screening_track"].startswith("monitor-")
        or re.search(r"pending|ongoing|open or interlocutory|pending appeal", row["litigation_posture"], re.I)
        for row in episode.records
    )


def science_category(row: dict[str, str]) -> str:
    parts = [part.strip().lower() for part in row["responsible_actor_or_category"].split(";")]
    return next((part for part in parts[1:] if any(term in part for term in SCIENCE_INTEGRITY_CATEGORIES)), "")


def preliminary_classification(episode: Episode) -> tuple[str, str]:
    families = {row["source_family"] for row in episode.records}
    if not episode.routes:
        return "rejected", "No current structural route survived the independent route-fit check."
    if any(row["catalog_id"] in FORMAL_HORIZON_ROUTES_BY_ID for row in episode.records):
        if is_open_episode(episode):
            return "monitoring", "Formal Horizon source with an active or unresolved external posture."
        return "integration", "Formal Horizon source-development lead retained for the admitted intake record."
    if "Just Security litigation tracker" in families or "Public Citizen Trump Administration 2.0 Lawsuit Tracker" in families:
        if is_open_episode(episode):
            return "monitoring", "Current litigation retained until a final merits or controlling threshold disposition."
        return "integration-candidate", "Resolved or mixed litigation record requires qualitative placement review."
    if "Protect Democracy Retaliatory Actions Tracker" in families:
        if is_open_episode(episode):
            return "monitoring", "Ongoing reported retaliation episode retained for defined posture monitoring."
        return "integration", "Completed tracker episode retained for primary-record verification and placement."
    if "Immigration Policy Tracking Project" in families:
        return "shortlist", "Litigation-marked policy lead retained only if selected as a distinct representative mechanism."
    if "Institute for Policy Integrity Trump court roundup" in families:
        return "shortlist", "Completed agency-action case retained only if it adds a representative mechanism or Horizon question."
    if "Columbia Trump Administration Human Rights Tracker" in families:
        text = " ".join(row["action_or_policy"] for row in episode.records)
        if HUMAN_RIGHTS_MECHANISM_TERMS.search(text):
            return "shortlist", "Human-rights lead contains a potentially institutional mechanism but requires primary verification."
        return "rejected", "The record identifies policy impact without a sufficiently specific institutional mechanism."
    if "Silencing Science Tracker" in families:
        if any(
            science_category(row) and SCIENCE_EVIDENCE_TERMS.search(row["action_or_policy"])
            for row in episode.records
        ):
            return "shortlist", "Science-integrity mechanism is potentially probative but the tracker entry is not itself a legal conclusion."
        return "rejected", "Budget or personnel policy alone does not establish the FACT-001 information-integrity defect."
    return "rejected", "No high-confidence evidentiary use remained after the independent challenge pass."


def select_shortlists(episodes: list[Episode]) -> None:
    for episode in episodes:
        episode.routes = placement_routes(episode)
    candidates: dict[str, list[Episode]] = defaultdict(list)
    for episode in episodes:
        disposition, reason = preliminary_classification(episode)
        episode.disposition = disposition
        episode.reason = reason
        if disposition == "shortlist":
            family = episode.primary["source_family"]
            candidates[family].append(episode)

    for family, items in candidates.items():
        family_cap = FAMILY_CAPS.get(family, 20)
        selected: list[Episode] = []
        route_counts: Counter[str] = Counter()
        diversity: Counter[str] = Counter()
        ordered = sorted(items, key=lambda item: (-item.score, item.primary["catalog_id"]))
        while ordered and len(selected) < family_cap:
            best = max(
                ordered,
                key=lambda item: (
                    item.score
                    - 2 * route_counts[item.routes[0]]
                    - diversity[diversity_key(item)],
                    item.primary["catalog_id"],
                ),
            )
            ordered.remove(best)
            primary_route = best.routes[0]
            cap = ROUTE_CAPS.get(primary_route, 5)
            if route_counts[primary_route] >= cap:
                continue
            selected.append(best)
            route_counts[primary_route] += 1
            diversity[diversity_key(best)] += 1

        selected_groups = {item.group for item in selected}
        for item in items:
            if item.group in selected_groups:
                item.disposition = "integration"
                item.reason = (
                    "Selected as a representative, route-specific source-development episode; "
                    "primary verification and reader-facing placement remain required."
                )
            elif family == "Silencing Science Tracker":
                item.disposition = "redundant"
                item.reason = (
                    "The canonical tracker and selected representative episodes preserve the breadth finding; "
                    "this entry adds no distinct reader-facing proposition."
                )
            else:
                item.disposition = "rejected"
                item.reason = (
                    "Not selected after route, source-strength, and mechanism-diversity review; the record is "
                    "cumulative, insufficiently specific, or primarily a substantive policy dispute."
                )

    for episode in episodes:
        if episode.disposition == "integration-candidate":
            if episode.score >= 9:
                episode.disposition = "integration"
                episode.reason = "Strong official or litigation record retained for qualitative proposal placement."
            else:
                episode.disposition = "registry-only"
                episode.reason = (
                    "The canonical tracker preserves the adjudicated posture; this entry adds no distinct "
                    "reader-facing value beyond existing proposal evidence."
                )


def placement_routes(episode: Episode) -> list[str]:
    """Convert provisional topical routes into one accountable evidence home."""
    formal_routes = []
    for row in episode.records:
        horizon = FORMAL_HORIZON_ROUTES_BY_ID.get(row["catalog_id"], "")
        if horizon and horizon not in formal_routes:
            formal_routes.append(horizon)
    non_horizon = [route for route in episode.routes if not route.startswith("HOR-")]
    if formal_routes:
        # The formal Horizon record owns the intake. One existing proposal may
        # remain as a useful boundary or future integration route.
        return [*formal_routes, *non_horizon[:1]]
    return non_horizon[:1]


def diversity_key(episode: Episode) -> str:
    row = episode.primary
    if row["source_family"] == "Silencing Science Tracker":
        agency = row["responsible_actor_or_category"].split(";")[0].strip()
        return f"{agency}|{science_category(row)}|{row['term']}"
    return " ".join(sorted(tokens(row["action_or_policy"]))[:4])


def next_source_number(rows: list[dict[str, str]]) -> int:
    numbers = []
    for row in rows:
        match = re.fullmatch(r"SRC-(\d+)", row["Source ID"])
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers, default=0) + 1


def source_metadata(row: dict[str, str], kind: str, url: str) -> dict[str, str]:
    host = urlsplit(url).netloc.lower()
    family = row["source_family"]
    reliability = "Secondary"
    if kind == "official_action":
        source_type = "Official Government Record"
        authority = "Federal government"
        reliability = "Primary"
        if "whitehouse.gov" in host:
            authority = "White House"
        elif "federalregister.gov" in host or "govinfo.gov" in host:
            authority = "Federal Register or GovInfo"
    elif kind == "representative_case":
        primary_hosts = (
            "courtlistener.com",
            "supremecourt.gov",
            "uscourts.gov",
            "law.justia.com",
        )
        if any(marker in host for marker in primary_hosts) or host.endswith(".gov"):
            source_type = "Court Docket or Judicial Record"
            authority = "CourtListener/RECAP" if "courtlistener.com" in host else host
            reliability = "Primary"
        else:
            source_type = "Supporting Source or Litigation Record"
            authority = FAMILY_LABELS.get(family, family)
    else:
        source_type = "Specialist Tracker Entry"
        authority = FAMILY_LABELS.get(family, family)
    return {
        "Source Type": source_type,
        "Authority / Publisher": authority,
        "Title or Description": row["action_or_policy"],
        "Date": row["action_date_or_period"] or f"reviewed {TODAY}",
        "URL": url,
        "Proposition Supported": (
            "Source-development record for the described government action, litigation, or institutional episode; "
            "the individual legal and factual propositions remain subject to the stated verification posture."
        ),
        "Reliability Tier": reliability,
        "Reviewed?": "No",
        "Notes": (
            f"Graduated from catalog record {row['catalog_id']} during the {TODAY} route-centered adjudication. "
            "Retention does not establish illegality, motive, or final judicial posture."
        ),
    }


def register_sources(
    episodes: list[Episode], source_rows: list[dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, list[str]], int, int]:
    retained = {"integration", "monitoring"}
    rows = [dict(row) for row in source_rows]
    by_url = {normalize_url(row["URL"]): row for row in rows if normalize_url(row["URL"])}
    next_id = next_source_number(rows)
    episode_sources: dict[str, list[str]] = defaultdict(list)
    added = 0
    updated_ids: set[str] = set()
    for episode in episodes:
        if episode.disposition not in retained:
            continue
        for record in episode.records:
            for item in source_urls(record):
                key = item["normalized_url"]
                existing = by_url.get(key)
                if existing:
                    existing["Associated Record IDs"] = "; ".join(
                        merge_routes(split_routes(existing["Associated Record IDs"]), episode.routes)
                    )
                    source_id = existing["Source ID"]
                    updated_ids.add(source_id)
                else:
                    source_id = f"SRC-{next_id:04d}"
                    next_id += 1
                    metadata = source_metadata(record, item["kind"], item["url"])
                    existing = {
                        "Source ID": source_id,
                        "Associated Record IDs": "; ".join(episode.routes),
                        **metadata,
                    }
                    rows.append(existing)
                    by_url[key] = existing
                    added += 1
                if source_id not in episode_sources[episode.group]:
                    episode_sources[episode.group].append(source_id)
    return rows, episode_sources, added, len(updated_ids)


def integration_rows(
    episodes: list[Episode], episode_sources: dict[str, list[str]], existing: list[dict[str, str]]
) -> list[dict[str, str]]:
    rows = [dict(row) for row in existing]
    known = {row["catalog_id"] for row in rows}
    for episode in episodes:
        if episode.disposition != "integration":
            continue
        primary = episode.primary
        catalog_ids = "; ".join(row["catalog_id"] for row in episode.records)
        if any(row["catalog_id"] in known for row in episode.records):
            continue
        rows.append(
            {
                "catalog_id": catalog_ids,
                "canonical_source_ids": "; ".join(episode_sources[episode.group]),
                "integration_routes": "; ".join(episode.routes),
                "integration_status": "awaiting-primary-verification-and-reader-placement",
                "action_or_policy": primary["action_or_policy"],
                "legal_question_or_outcome": primary["legal_question_or_outcome"],
                "litigation_posture": primary["litigation_posture"],
                "source_family": "; ".join(sorted({row["source_family"] for row in episode.records})),
                "source_entry_url": primary["source_entry_url"],
                "representative_case_url": primary["representative_case_url"],
                "official_action_url": primary["official_action_url"],
                "preliminary_disposition": "representative-source-development",
                "review_note": episode.reason,
                "last_reviewed": TODAY,
            }
        )
    return rows


def monitoring_rows(
    episodes: list[Episode], episode_sources: dict[str, list[str]]
) -> list[dict[str, str]]:
    rows = []
    for episode in episodes:
        if episode.disposition != "monitoring":
            continue
        primary = episode.primary
        rows.append(
            {
                "monitor_id": f"MON-{len(rows) + 1:04d}",
                "catalog_ids": "; ".join(row["catalog_id"] for row in episode.records),
                "evidence_group": episode.group,
                "integration_routes": "; ".join(episode.routes),
                "action_or_policy": primary["action_or_policy"],
                "litigation_posture": primary["litigation_posture"],
                "canonical_source_ids": "; ".join(episode_sources[episode.group]),
                "source_family": "; ".join(sorted({row["source_family"] for row in episode.records})),
                "monitoring_status": "active-defined-predicate",
                "revisit_trigger": (
                    "Final merits ruling, controlling threshold decision, dismissal, settlement or withdrawal, "
                    "or another material change in posture."
                ),
                "last_checked": primary["last_checked"] or TODAY,
                "notes": episode.reason,
            }
        )
    return rows


def report_text(
    episodes: list[Episode], source_added: int, source_updated: int,
    integration_count: int, monitor_count: int,
) -> str:
    records_by_disposition: Counter[str] = Counter()
    episodes_by_disposition: Counter[str] = Counter()
    rejection_reasons: Counter[str] = Counter()
    family_counts: dict[str, Counter[str]] = defaultdict(Counter)
    route_counts: Counter[str] = Counter()
    for episode in episodes:
        episodes_by_disposition[episode.disposition] += 1
        records_by_disposition[episode.disposition] += len(episode.records)
        if episode.disposition in {"rejected", "redundant", "registry-only"}:
            rejection_reasons[episode.reason] += len(episode.records)
        for row in episode.records:
            family_counts[row["source_family"]][episode.disposition] += 1
        if episode.disposition in {"integration", "monitoring"}:
            for route in episode.routes:
                route_counts[route] += 1

    record_total = sum(records_by_disposition.values())
    lines = [
        "---",
        'title: "Trump Administration Source Adjudication Report"',
        "print_levels:",
        "  - full-technical",
        "---",
        "",
        "# Trump Administration Source Adjudication Report",
        "",
        f"**Completed:** {TODAY}",
        "",
        "## Outcome",
        "",
        f"The route-centered review processed all **{record_total:,}** remaining discovery records as "
        f"**{len(episodes):,}** conservatively clustered episodes. The raw catalog and routing ledger are now "
        "empty active queues. Retained work moved to the canonical source registry, the existing-record "
        "integration queue, or the defined-predicate litigation monitor; no raw tracker row was promoted to a "
        "new proposal merely because it alleged illegality or carried a topical route.",
        "",
        "This was source development, not a T-audit. It changed no proposal score or Runs field and did not "
        "treat tracker characterization as proof of illegality, motive, or final judicial posture.",
        "",
        "## Reconciliation",
        "",
        "| Destination | Records | Episodes |",
        "| --- | ---: | ---: |",
    ]
    labels = {
        "integration": "Pending qualitative integration",
        "monitoring": "Defined-predicate monitoring",
        "registry-only": "Registry-only; no additional reader value",
        "redundant": "Redundant without additional evidentiary value",
        "rejected": "Political, topical-only, cumulative, or insufficiently specific",
    }
    for key in ("integration", "monitoring", "registry-only", "redundant", "rejected"):
        lines.append(
            f"| {labels[key]} | {records_by_disposition[key]:,} | {episodes_by_disposition[key]:,} |"
        )
    lines.extend(
        [
            f"| **Total** | **{record_total:,}** | **{len(episodes):,}** |",
            "",
            f"Canonical sources added: **{source_added:,}**. Existing source rows associated with additional "
            f"routes: **{source_updated:,}**. Active integration rows after the migration: **{integration_count:,}**. "
            f"Active monitoring rows: **{monitor_count:,}**.",
            "",
            "No preliminary Horizon candidate was created. The independent route-fit pass found that the six "
            "unrouted records were substantive policy disputes, unresolved litigation without a current ARRP home, "
            "or allegations that did not yet identify a distinct repairable institutional weakness.",
            "",
            "## Source-family results",
            "",
            "| Source family | Integration | Monitoring | Registry-only | Redundant | Rejected |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for family in sorted(family_counts):
        count = family_counts[family]
        lines.append(
            f"| {family} | {count['integration']:,} | {count['monitoring']:,} | "
            f"{count['registry-only']:,} | {count['redundant']:,} | {count['rejected']:,} |"
        )
    lines.extend(
        [
            "",
            "## Highest-volume retained routes",
            "",
            "These counts are retained episodes associated with a route, not findings of illegality and not "
            "independent proposal counts.",
            "",
            "| Route | Retained episodes |",
            "| --- | ---: |",
        ]
    )
    for route, count in route_counts.most_common(20):
        lines.append(f"| {route} | {count:,} |")
    lines.extend(
        [
            "",
            "## Qualitative placement rules applied",
            "",
            "- Current or interlocutory cases with a plausible existing route moved to defined-predicate monitoring; "
            "they did not enter proposal prose as established manifestations.",
            "- Final or mixed records were retained for integration only when the catalog supplied a strong official "
            "or litigation record, a formal Horizon route, or a representative institutional mechanism.",
            "- Immigration-policy tracker rows without normalized dockets were sampled by route and mechanism; "
            "selected records remain explicit verification tasks rather than claimed evidence.",
            "- Science-integrity entries were retained only when they illustrated censorship, misrepresentation, "
            "research hindrance, or self-censorship. Budget and personnel policy alone did not establish FACT-001.",
            "- The completed first-term court roundup chiefly demonstrates that ordinary APA and statutory review "
            "often worked. Cumulative cases were not used to inflate REG-006 or other proposal evidence.",
            "- Tracker-level sources preserve breadth. Individual entries adding no distinct reader-facing proposition "
            "were removed from the active intake rather than duplicated across permanent ledgers.",
            "",
            "## Remaining work",
            "",
            "The raw catalog review is complete. Remaining rows are narrower work obligations: verify and place the "
            "selected integration episodes when their receiving issue is developed, and revisit monitored litigation "
            "only when its stated external predicate occurs. A receiving proposal should use its strongest necessary "
            "sources on the issue page and create a linked evidence record only when the additional verified record has "
            "qualitative reader-facing value.",
            "",
        ]
    )
    return "\n".join(lines)


def validate(
    catalog: list[dict[str, str]], episodes: list[Episode],
    integration: list[dict[str, str]], monitoring: list[dict[str, str]],
    sources: list[dict[str, str]], original_sources: list[dict[str, str]],
) -> None:
    input_ids = {row["catalog_id"] for row in catalog}
    clustered_ids = [row["catalog_id"] for episode in episodes for row in episode.records]
    if set(clustered_ids) != input_ids or len(clustered_ids) != len(input_ids):
        raise SystemExit("Episode clustering did not reconcile every input record exactly once.")
    if any(not episode.disposition for episode in episodes):
        raise SystemExit("At least one episode lacks a disposition.")
    source_ids = {row["Source ID"] for row in sources}
    for row in integration:
        if not set(split_routes(row["canonical_source_ids"])).issubset(source_ids):
            raise SystemExit(f"Integration row has unknown source ID: {row['catalog_id']}")
    for row in monitoring:
        if not set(split_routes(row["canonical_source_ids"])).issubset(source_ids):
            raise SystemExit(f"Monitoring row has unknown source ID: {row['monitor_id']}")
        if not row["revisit_trigger"].strip():
            raise SystemExit(f"Monitoring row lacks a revisit trigger: {row['monitor_id']}")
    def duplicate_count(rows: list[dict[str, str]]) -> int:
        normalized = [normalize_url(row["URL"]) for row in rows if normalize_url(row["URL"])]
        return len(normalized) - len(set(normalized))

    # The inventory contains historical duplicate rows outside this migration's
    # scope.  Do not worsen that known condition; new URLs are allocated only
    # through the normalized identity map above.
    if duplicate_count(sources) > duplicate_count(original_sources):
        raise SystemExit("The adjudication would add a duplicate normalized source URL.")


def main() -> None:
    args = parse_args()
    catalog = read_csv(CATALOG)
    if not catalog:
        raise SystemExit("Catalog is already empty; nothing to adjudicate.")
    routing_rows = read_csv(ROUTING)
    routing = {row["catalog_id"]: row for row in routing_rows}
    if {row["catalog_id"] for row in catalog} != set(routing):
        raise SystemExit("Catalog and routing ledger are not in one-to-one reconciliation.")

    episodes = cluster_records(catalog, routing)
    select_shortlists(episodes)
    original_sources = read_csv(SOURCES)
    new_sources, episode_sources, added, updated = register_sources(episodes, original_sources)
    original_integration = read_csv(INTEGRATION)
    new_integration = integration_rows(episodes, episode_sources, original_integration)
    new_monitoring = monitoring_rows(episodes, episode_sources)
    validate(catalog, episodes, new_integration, new_monitoring, new_sources, original_sources)
    report = report_text(episodes, added, updated, len(new_integration), len(new_monitoring))

    counts = Counter(episode.disposition for episode in episodes)
    record_counts = Counter()
    for episode in episodes:
        record_counts[episode.disposition] += len(episode.records)
    print(f"Validated {len(catalog):,} records as {len(episodes):,} episodes.")
    print("Episode dispositions:", dict(sorted(counts.items())))
    print("Record dispositions:", dict(sorted(record_counts.items())))
    print(
        f"Would add {added:,} source rows, update {updated:,}, retain {len(new_integration):,} "
        f"integration rows, and create {len(new_monitoring):,} monitoring rows."
    )
    if not args.apply:
        print("Dry run only; pass --apply to write the reconciled batch.")
        return

    write_csv_preserving_unchanged(
        SOURCES,
        original_sources,
        new_sources,
        list(original_sources[0]),
        key_field="Source ID",
    )
    write_csv(INTEGRATION, new_integration, INTEGRATION_FIELDS)
    write_csv(MONITORING, new_monitoring, MONITOR_FIELDS)
    write_csv(CATALOG, [], list(catalog[0]))
    write_csv(ROUTING, [], list(routing_rows[0]))
    priority_rows = read_csv(PRIORITY)
    if priority_rows:
        write_csv(PRIORITY, [], list(priority_rows[0]))
    REPORT.write_text(report, encoding="utf-8")
    print("Applied the fully reconciled source-adjudication batch.")


if __name__ == "__main__":
    main()
