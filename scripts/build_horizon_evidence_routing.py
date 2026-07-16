#!/usr/bin/env python3
"""Build the auditable evidence-routing ledger for Horizon intake sources.

This first-stage builder never deletes duplicate records. It translates known
routes to the current portfolio, identifies the use a record may serve, and
separates records requiring substantive agent review from material already
capable of entering an existing-issue integration queue.
"""

from __future__ import annotations

import csv
import hashlib
import re
from datetime import date
from pathlib import Path

from horizon_intake_common import current_routes


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research" / "trump-administration-legal-review-catalog.csv"
PRIORITY = ROOT / "research" / "trump-administration-priority-disposition-review.csv"
OUTPUT = ROOT / "research" / "trump-administration-evidence-routing.csv"

FIELDS = [
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


def normalized_title(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", value.lower())
    stop = {"a", "an", "and", "for", "in", "of", "on", "the", "to", "v", "versus"}
    return " ".join(word for word in words if word not in stop)


def evidence_group(row: dict[str, str]) -> str:
    """Create a conservative exact-key group while preserving every row."""
    if row["official_action_url"].strip():
        basis = f'official:{row["official_action_url"].strip().lower()}'
    elif row["representative_case_url"].strip():
        basis = f'case:{row["representative_case_url"].strip().lower()}'
    else:
        basis = f'title:{row["term"]}:{normalized_title(row["action_or_policy"])}'
    digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]
    return f"EVID-{digest.upper()}"


def source_value(row: dict[str, str]) -> str:
    if row["official_action_url"].strip() and row["representative_case_url"].strip():
        return "official-action-and-litigation-links"
    if row["official_action_url"].strip():
        return "official-action-link"
    if row["representative_case_url"].strip():
        return "litigation-link"
    return "specialist-source-lead"


def recommended_use(row: dict[str, str]) -> str:
    screening = row["screening_track"]
    record_type = row["record_type"]
    if screening.startswith("monitor-"):
        return "litigation-status-monitoring"
    if record_type == "adjudicated-agency-action":
        return "manifestation-and-controlling-posture-review"
    if record_type == "science-integrity-discovery-lead":
        return "source-development-and-manifestation-screening"
    if "litigat" in record_type:
        return "manifestation-and-litigation-source"
    return "source-development-lead"


FORMAL_HORIZON_EVIDENCE = {
    "TAC-IPT-138": "HOR-034",
    "TAC-IPT-143": "HOR-034",
    "TAC-IPT-154": "HOR-034",
    "TAC-IPT-006": "HOR-037",
    "TAC-IPT-043": "HOR-037",
    "TAC-IPT-112": "HOR-037",
    "TAC-IPT-220": "HOR-037",
    "TAC-IPT-243": "HOR-037",
    "TAC-IPT-248": "HOR-037",
    "TAC-IPT-127": "HOR-037",
    "TAC-IPT-202": "HOR-037",
    "TAC-HRT1-005": "HOR-037",
    "TAC-HRT1-007": "HOR-037",
    "TAC-HRT1-015": "HOR-037",
    "TAC-HRT1-016": "HOR-037",
    "TAC-HRT1-017": "HOR-037",
    "TAC-HRT1-018": "HOR-037",
    "TAC-HRT1-019": "HOR-037",
    "TAC-HRT1-022": "HOR-037",
    "TAC-HRT1-025": "HOR-037",
    "TAC-HRT1-026": "HOR-037",
    "TAC-HRT1-044": "HOR-037",
    "TAC-PCT2-038": "HOR-034",
}

PRIORITY_CLASS_BY_ID: dict[str, str] = {}

IPI_REVIEW_EVASION_IDS = {
    "TAC-IPI1-019",
    "TAC-IPI1-063",
    "TAC-IPI1-067",
    "TAC-IPI1-216",
    "TAC-IPI1-229",
    "TAC-IPI1-239",
}

# These records are retained only as leads for the narrower question whether an
# executive action operated before a court could supply effective merits
# review.  The broader text classifier is not sufficient for this assignment:
# several records it labeled "preliminary" or "mixed" include merits holdings.
IPI_TIMELY_MERITS_REVIEW_IDS = {
    "TAC-IPI1-007",  # preliminary relief denied for lack of immediate harm
    "TAC-IPI1-029",  # stay or summary vacatur denied
    "TAC-IPI1-041",  # statutory claim held unreviewable; other claim rejected
    "TAC-IPI1-044",  # preliminary injunction denied
    "TAC-IPI1-078",  # preliminary injunction denied
    "TAC-IPI1-126",  # waiver holding accompanied by some merits analysis
}


JUST_SECURITY_HORIZON_ROUTES = {
    "TAC-JS2-003": "HOR-033",
    "TAC-JS2-010": "HOR-034",
}


JUST_SECURITY_ROUTE_RULES: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("immigra", "asylum", "refugee", "alien enemies", "deport", "removal to", "cbp one", "temporary protected status", "visa policy", "border enforcement", "birthright citizenship", "unaccompanied minors"), ("RIGHTS-002", "DOM-001")),
    (("work permit", "habeas", "commercial driver", "worker credentials at ports"), ("RIGHTS-002", "DOM-001")),
    (("passport policy", "lgbtq", "transgender", "gender-affirming", "gender affirming", "dei discrimination", "deia", "dear colleague", "compelled political speech"), ("RIGHTS-001",)),
    (("law firms", "retaliation", "protected speech", "denial of federal grants", "actions toward universities"), ("RET-001",)),
    (("independent agencies", "independent agency leaders", "consumer financial protection bureau"), ("REG-001",)),
    (("dismantling", "revocation of government agencies", "federal mediation and conciliation service", "u.s. institute of peace", "us institute of peace"), ("REG-001", "CIV-005", "FUND-001")),
    (("changes to social security administration",), ("REG-001", "CIV-005")),
    (("large-scale reductions in force", "termination of probationary", "removal of career personnel", "schedule f", "fork directive", "return-to-work", "return to work", "career employees", "collective bargaining", "union petition", "labor organization financial"), ("CIV-001", "CIV-005")),
    (("government shutdown", "layoffs within"), ("CIV-001", "CIV-005")),
    (("doge", "personal and financial records", "civil servant personnel records", "solicitation of information from career", "biometric information", "sale of tiktok"), ("CIV-009", "DOM-009")),
    (("data collection requirements",), ("CIV-009", "RIGHTS-001")),
    (("fund", "grant", "loan", "tax credits", "reimbursement rate", "funding freeze", "funding of the innovation", "student loan"), ("FUND-001", "JUD-011")),
    (("state transgender athlete", "sanctuary cities", "state and local governments", "congestion pricing", "vehicle standards preemption"), ("FED-003", "FED-004")),
    (("federal jurisdiction over oil pipelines",), ("FED-004",)),
    (("records", "foia", "information from hhs websites", "climate change and environmental information", "apportionment information", "health directives"), ("REC-001", "FACT-001")),
    (("scientific", "environmental information", "climate change", "federal advisory committee"), ("FACT-001",)),
    (("press freedom", "global media", "public access to immigration proceedings"), ("PRESS-001", "PRESS-006")),
    (("lawyers to immigrants",), ("RIGHTS-002",)),
    (("fbi personnel", "criminal arrests and prosecutions", "anti-weaponization", "special counsel hur", "epstein files"), ("DOJ-002", "DOJ-003", "DOJ-007")),
    (("conditions of imprisonment", "death penalty"), ("DOJ-003", "DOM-001")),
    (("dea enforcement",), ("REG-002",)),
    (("federalization of national guard", "domestic use of military"), ("DOM-001",)),
    (("dhs/ice actions toward u.s. citizens", "border wall construction"), ("DOM-001", "DOM-005")),
    (("extrajudicial killings",), ("WAR-001", "DOM-001")),
    (("tariffs", "international criminal court", "export controls"), ("EMERG-003",)),
    (("chinese military companies", "federal acquisition supply chain security"), ("EMERG-003", "CLASS-006")),
    (("international cooperative agreements",), ("HOR-026",)),
    (("election law", "voter registration"), ("ELEC-001",)),
    (("government facilities", "museums", "public libraries", "american history", "ufc authorization"), ("HER-001",)),
    (("national parks pass",), ("HER-001",)),
    (("presidential records act", "response to foia"), ("REC-001",)),
    (("inspectors general",), ("OVS-001",)),
    (("agency control", "regulatory changes", "regulations", "emission standards", "clean air act enforcement", "delayed agency action", "previous executive orders", "environmental rollbacks", "land use", "public lands", "wind energy approvals", "offshore oil", "oil drilling"), ("REG-002", "REG-006")),
    (("unleashing american energy",), ("FUND-001", "JUD-011", "REG-006")),
    (("noncompliance",), ("JUD-001", "REG-006")),
    (("government employees' speech", "display and flying"), ("CIV-001",)),
    (("government agencies",), ("REG-001",)),
]


def reviewed_just_security(row: dict[str, str]) -> tuple[list[str], str]:
    """Route the tracker action clusters after a title-by-title issue-fit pass."""
    horizon_id = JUST_SECURITY_HORIZON_ROUTES.get(row["catalog_id"], "")
    if horizon_id:
        return [], horizon_id
    title = row["action_or_policy"].lower()
    routes: list[str] = []
    for needles, rule_routes in JUST_SECURITY_ROUTE_RULES:
        if any(needle in title for needle in needles):
            for route in rule_routes:
                if route not in routes:
                    routes.append(route)
    return routes, ""


IMMIGRATION_ROUTE_RULES: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("asylum", "refugee", "temporary protected status", " tps ", "humanitarian", "parole", "credible fear", "withholding of removal", "daca", "deferred action"), ("RIGHTS-002",)),
    (("birthright",), ("RIGHTS-003",)),
    (("citizenship", "naturalization", "u.s. citizen", "us citizen", "passport"), ("RIGHTS-001", "RIGHTS-003")),
    (("eoir", "immigration judge", "immigration court", "bia ", "board of immigration appeals", "hearing", "adjudication", "administrative closure"), ("REG-003",)),
    (("detention", "ice ", "cbp ", "border patrol", "removal", "deport", "expedited removal", "interior enforcement", "arrest", "raid", "warrant"), ("DOM-001",)),
    (("operation metro surge", "protected areas", "national guard units", "physical barriers", "build the wall"), ("DOM-001",)),
    (("courthouse", "attending immigration-court hearings"), ("HOR-010",)),
    (("court order", "contempt", "injunction", "wrongfully deported"), ("JUD-001", "JUD-005")),
    (("sanctuary", "state and local", "state laws", "state judges", "localities", "byrne jag"), ("FED-003", "FED-004")),
    (("state immigration-enforcement laws", "right to privacy in the workplace"), ("FED-004",)),
    (("data", "information", "database", "social media questions", "subpoena", "records", "forms and information collection"), ("CIV-009", "REC-001")),
    (("voter", "voting", "election", "census"), ("ELEC-001", "ELEC-014")),
    (("fund", "grant", "stop-work", "fees", "fee rule"), ("FUND-001", "JUD-011")),
    (("fires", "firing", "employees", "personnel", "union"), ("CIV-001", "CIV-005")),
    (("inspector general", "ombudsman"), ("OVS-001",)),
    (("international criminal court", "icc-affiliated"), ("EMERG-003",)),
    (("imposing duties",), ("EMERG-003",)),
    (("national emergency", "alien enemies act", "invocation of the alien enemies"), ("EMERG-001", "RIGHTS-002")),
    (("waives statutory requirements",), ("REG-006", "DOM-001")),
    (("rule", "guidance", "policy memorandum", "public charge", "travel ban", "entry restrictions"), ("REG-006",)),
    (("religious", "discrimination", "abortion", "lgbt", "gender"), ("RIGHTS-001",)),
    (("labor-management relations",), ("CIV-001",)),
    (("jttf", "political violence and intimidation"), ("DOM-007", "DOM-009")),
]


def reviewed_immigration(row: dict[str, str]) -> list[str]:
    text = f'{row["action_or_policy"]} {row["responsible_actor_or_category"]}'.lower()
    routes: list[str] = []
    for needles, rule_routes in IMMIGRATION_ROUTE_RULES:
        if any(needle in text for needle in needles):
            for route in rule_routes:
                if route not in routes:
                    routes.append(route)
    return routes


HUMAN_RIGHTS_ROUTE_RULES: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("immigrant", "migrant", "asylum", "refugee", "travel ban", "temporary protected status", " tps ", "daca", "deport", "sanctuary", "border wall", "bans entry", "undocumented kids"), ("RIGHTS-002", "DOM-001")),
    (("lgbtq", "transgender", "equal pay", "civil rights investigations", "bathroom", "employment discrimination", "women in the workplace", "birth control"), ("RIGHTS-001",)),
    (("journalists", "press"), ("PRESS-001", "PRESS-003", "PRESS-006")),
    (("tracked", "social media information", "privacy rights"), ("DOM-009", "CIV-009")),
    (("airstrikes", "cluster munitions", "counterterrorism operations", "arms sale"), ("WAR-001",)),
    (("federal workers", "freeze pay", "government shutdown"), ("CIV-001", "CIV-005", "FUND-001")),
    (("justice department", "attorney general", "doj ", "sentencing"), ("DOJ-002", "DOJ-003", "DOJ-007")),
    (("climate change content", "distorts data", "human rights report", "animal welfare reports"), ("FACT-001", "REC-001")),
    (("climate", "mercury", "toxic air", "drilling", "coal", "pipeline", "environment"), ("REG-002", "REG-006", "FACT-001")),
    (("cost sharing reduction", "federal funding", "payments", "global gag", "funding to sanctuary"), ("FUND-001", "JUD-011")),
    (("unesco", "global compact", "human rights council", "inter-american commission"), ("HOR-026",)),
    (("state department", "secretary of state"), ("HOR-026",)),
    (("voter id",), ("ELEC-001", "ELEC-014")),
    (("federal rules", "new rules", "repeals rule", "regulation", "policy"), ("REG-006",)),
]


def reviewed_human_rights(row: dict[str, str]) -> list[str]:
    title = f' {row["action_or_policy"].lower()} '
    routes: list[str] = []
    for needles, rule_routes in HUMAN_RIGHTS_ROUTE_RULES:
        if any(needle in title for needle in needles):
            for route in rule_routes:
                if route not in routes:
                    routes.append(route)
    return routes


PUBLIC_CITIZEN_ROUTE_RULES: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("foia", "seeking records", "seeking information"), ("REC-001",)),
    (("slush fund",), ("EMOL-001", "EMOL-015", "DOJ-007")),
    (("asylum", "refugee", "daca", "work permits", "visa program", "commercial drivers"), ("RIGHTS-002",)),
    (("credit protection", "cfpb", "cpsc commissioners"), ("REG-001", "REG-002")),
    (("arch", "white house ballroom"), ("HER-001",)),
    (("endangerment finding", "environmental justice", "climate change", "health data", "institute of education sciences"), ("FACT-001", "REG-006")),
    (("tax credits", "grantmaking", "funding freeze", "funds needed", "public service loan", "hunger hotline", "teen pregnancy prevention"), ("FUND-001", "JUD-011")),
    (("job corps", "niosh", "usaid", "global labor rights", "dismantling", "shutdown"), ("REG-001", "CIV-005")),
    (("discrimination", "civil rights offices"), ("RIGHTS-001",)),
    (("spending database", "webpages", "government spending"), ("REC-001", "FACT-001")),
    (("doge", "payments system", "dept. of education data"), ("CIV-009",)),
    (("out-of-office emails",), ("CIV-001", "FACT-009")),
]


def reviewed_public_citizen(row: dict[str, str]) -> list[str]:
    title = row["action_or_policy"].lower()
    routes: list[str] = []
    for needles, rule_routes in PUBLIC_CITIZEN_ROUTE_RULES:
        if any(needle in title for needle in needles):
            for route in rule_routes:
                if route not in routes:
                    routes.append(route)
    return routes


def reviewed_policy_integrity(row: dict[str, str]) -> tuple[list[str], str]:
    """Route administrative-law cases while preserving disposition uncertainty."""
    if row["catalog_id"] in IPI_REVIEW_EVASION_IDS:
        return [], "HOR-035"
    if row["catalog_id"] in IPI_TIMELY_MERITS_REVIEW_IDS:
        return [], "HOR-036"

    category = row["responsible_actor_or_category"].lower()
    routes: list[str] = []
    category_rules = [
        (("immigration",), ("RIGHTS-002", "REG-003")),
        (("worker",), ("CIV-001", "REG-006")),
        (("environment", "energy", "natural resources", "deregulation"), ("REG-006", "FACT-001")),
        (("health", "consumer protection", "education", "housing", "public assistance"), ("REG-006", "RIGHTS-001")),
        (("public safety",), ("REG-002", "DOM-001")),
    ]
    for needles, rule_routes in category_rules:
        if any(needle in category for needle in needles):
            for route in rule_routes:
                if route not in routes:
                    routes.append(route)
    if not routes:
        routes.append("REG-006")
    return routes, ""


def disposition(
    row: dict[str, str], routes: list[str]
) -> tuple[str, list[str], str, str, str]:
    horizon_id = FORMAL_HORIZON_EVIDENCE.get(row["catalog_id"], "")
    if horizon_id:
        return (
            "existing-record-integration",
            list(dict.fromkeys([horizon_id, *routes])),
            "promoted preliminary evidence rerouted to the formal Horizon candidate; final source graduation remains subject to route-fit and source verification",
            "agent-reviewed-for-active-horizon-routing",
            "",
        )
    if row["source_family"] == "Silencing Science Tracker":
        reviewed_routes = ["FACT-001", *routes]
        return (
            "existing-record-integration",
            list(dict.fromkeys(reviewed_routes)),
            "source-family and record-scope review: retain as a FACT-001 source-development lead; inclusion does not establish that the episode warrants publication as a manifestation",
            "agent-reviewed-for-existing-record-routing",
            "",
        )
    if row["source_family"] == "Protect Democracy Retaliatory Actions Tracker":
        reviewed_routes = ["RET-001", *routes]
        return (
            "existing-record-integration",
            list(dict.fromkeys(reviewed_routes)),
            "source-family and record-scope review: retain under RET-001 for anti-retaliation source development and manifestation screening",
            "agent-reviewed-for-existing-record-routing",
            "",
        )
    if row["source_family"] == "Just Security litigation tracker":
        reviewed_routes, horizon_id = reviewed_just_security(row)
        if horizon_id:
            return (
                "existing-record-integration",
                list(dict.fromkeys([horizon_id, *reviewed_routes])),
                "promoted preliminary evidence rerouted to the formal Horizon candidate; controlling source and route-fit verification remain required",
                "agent-reviewed-for-active-horizon-routing",
                "",
            )
        if reviewed_routes:
            return (
                "existing-record-integration",
                reviewed_routes,
                "record-level action-cluster review identified current proposal homes; retain as litigation-status or manifestation source subject to controlling-record verification",
                "agent-reviewed-for-existing-record-routing",
                "",
            )
        return (
            "research-retained-no-current-route",
            [],
            "record-level action-cluster review did not establish a current ARRP issue fit; retain the source without treating the underlying policy dispute as an institutional defect",
            "agent-reviewed-retained-research",
            "",
        )
    if row["source_family"] == "Immigration Policy Tracking Project":
        reviewed_routes = reviewed_immigration(row)
        if reviewed_routes:
            return (
                "existing-record-integration",
                reviewed_routes,
                "record-level immigration-policy review identified current proposal or Horizon homes; retain as source development, litigation monitoring, or manifestation evidence according to final posture",
                "agent-reviewed-for-existing-record-routing",
                "",
            )
        return (
            "research-retained-no-current-route",
            [],
            "record-level review did not establish a current ARRP issue fit; retain the source without converting the underlying substantive immigration-policy dispute into an institutional defect",
            "agent-reviewed-retained-research",
            "",
        )
    if row["source_family"] == "Columbia Trump Administration Human Rights Tracker":
        reviewed_routes = reviewed_human_rights(row)
        if reviewed_routes:
            return (
                "existing-record-integration",
                reviewed_routes,
                "record-level human-rights source review identified current proposal or Horizon homes; retain as a discovery lead and require primary-source verification before proposal-page use",
                "agent-reviewed-for-existing-record-routing",
                "",
            )
        return (
            "research-retained-no-current-route",
            [],
            "record-level review found no present structural issue fit or found only a substantive domestic or foreign-policy dispute; retain the source for provenance without Horizon promotion",
            "agent-reviewed-retained-research",
            "",
        )
    if row["source_family"] == "Public Citizen Trump Administration 2.0 Lawsuit Tracker":
        reviewed_routes = reviewed_public_citizen(row)
        if reviewed_routes:
            return (
                "existing-record-integration",
                reviewed_routes,
                "record-level litigation-tracker review identified current proposal homes; retain the complaint or requested record as source development and verify controlling posture before substantive use",
                "agent-reviewed-for-existing-record-routing",
                "",
            )
        return (
            "research-retained-no-current-route",
            [],
            "record-level review did not establish a current ARRP issue fit; retain the litigation source for provenance and later reconsideration",
            "agent-reviewed-retained-research",
            "",
        )
    if row["source_family"] == "Institute for Policy Integrity Trump court roundup":
        reviewed_routes, horizon_id = reviewed_policy_integrity(row)
        if horizon_id:
            basis = (
                "disposition-level intake review retained this case under HOR-035 as a lead for possible review evasion; "
                "controlling-opinion verification remains required"
                if horizon_id == "HOR-035"
                else "curated disposition review retained this case under HOR-036 as a lead for the possible timely-merits-review gap; controlling-opinion verification remains required"
            )
            return (
                "existing-record-integration",
                list(dict.fromkeys([horizon_id, *reviewed_routes])),
                basis,
                "agent-reviewed-for-active-horizon-routing",
                "",
            )
        return (
            "existing-record-integration",
            reviewed_routes,
            "administrative-law disposition review retained this case as existing-proposal manifestation, statutory-authority, or judicial-correction comparator evidence; controlling-opinion verification remains required before citation",
            "agent-reviewed-for-existing-record-routing",
            "",
        )
    if routes:
        return (
            "agent-review-needed",
            routes,
            "machine-assisted historical route translated to the current portfolio; substantive issue fit has not yet been verified",
            "agent-review-pending",
            "",
        )
    return (
        "agent-review-needed",
        routes,
        "no reliable current proposal route has yet been assigned",
        "agent-review-pending",
        "",
    )


def main() -> None:
    global PRIORITY_CLASS_BY_ID
    with CATALOG.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with PRIORITY.open(newline="", encoding="utf-8") as handle:
        PRIORITY_CLASS_BY_ID = {
            row["catalog_id"]: row["preliminary_disposition_class"]
            for row in csv.DictReader(handle)
        }

    rendered: list[dict[str, str]] = []
    for row in rows:
        routes = current_routes(row["provisional_arrp_routes"])
        record_disposition, reviewed_routes, basis, status, candidate_id = disposition(row, routes)
        rendered.append(
            {
                "catalog_id": row["catalog_id"],
                "evidence_group": evidence_group(row),
                "disposition": record_disposition,
                "integration_routes": "; ".join(reviewed_routes),
                "recommended_use": recommended_use(row),
                "source_value": source_value(row),
                "review_basis": basis,
                "review_status": status,
                "candidate_id": candidate_id,
                "last_reviewed": date.today().isoformat(),
            }
        )

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rendered)

    routed = sum(row["disposition"] == "existing-record-integration" for row in rendered)
    candidate_evidence = sum(row["disposition"] == "preliminary-candidate-evidence" for row in rendered)
    pending = sum(row["disposition"] == "agent-review-needed" for row in rendered)
    print(
        f"Wrote {OUTPUT.relative_to(ROOT)}: {routed:,} reviewed and routed; "
        f"{candidate_evidence:,} assigned to unresolved preliminary candidates; {pending:,} require agent review."
    )


if __name__ == "__main__":
    main()
