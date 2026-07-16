"""Shared routing helpers for the ARRP Horizon source-intake pipeline."""

from __future__ import annotations


# Historical source records retain the routes that existed when they were
# collected. Translate those labels to the current proposal architecture at
# presentation and routing time without rewriting the source record itself.
ROUTE_ALIASES: dict[str, list[str]] = {
    "A-01": ["DOJ-002", "DOJ-003", "DOJ-007"],
    "A-02": ["ELEC-001"],
    "A-05": ["PAR-001"],
    "A-06": ["EMOL-001"],
    "A-08": ["CIV-001", "CIV-005", "CIV-009"],
    "A-09": ["OVS-001", "OVS-004", "OVS-008"],
    "A-10": ["EMERG-001"],
    "A-11": ["FUND-001"],
    "A-12": ["APPT-001", "APPT-004"],
    "A-13": ["REC-001"],
    "A-14": ["DOM-001"],
    "A-18": ["FACT-001"],
    "A-19": ["RET-001"],
    "A-20": ["FED-002", "FED-003", "FED-004"],
    "A-22": ["PRESS-001", "PRESS-003", "PRESS-006"],
    "A-23": ["HER-001"],
    "A-24": ["RIGHTS-001"],
    "CIV-002": ["CIV-001"],
    "CIV-003": ["CIV-001"],
    "CIV-006": ["CIV-001"],
    "CIV-007": ["CIV-001"],
    "CIV-008": ["CIV-005"],
    "CLASS-002": ["CLASS-001"],
    "CLASS-003": ["CLASS-001"],
    "CLASS-005": ["CLASS-001"],
    "CLASS-007": ["CLASS-001"],
    "CLASS-008": ["CLASS-004"],
    "CLASS-009": ["CLASS-004"],
    "CLASS-010": ["CLASS-004"],
    "CLASS-012": ["CLASS-006"],
    "DOM-002": ["DOM-001"],
    "DOM-003": ["DOM-001"],
    "DOM-004": ["DOM-001"],
    "DOM-006": ["DOM-001"],
    "DOM-008": ["DOM-001"],
    "EMERG-002": ["FUND-001"],
    "EMERG-004": ["EMERG-001"],
    "EMERG-005": ["EMERG-001"],
    "EMERG-006": ["EMERG-001"],
    "EMERG-007": ["EMERG-001"],
    "EMERG-008": ["EMERG-001"],
    "FACT-002": ["FACT-001"],
    "FACT-003": ["FACT-001"],
    "FACT-004": ["FACT-001"],
    "FACT-005": ["FACT-001"],
    "FACT-006": ["FACT-001"],
    "FACT-008": ["FACT-001"],
    "FED-001": ["FED-003"],
    "FED-005": ["DOM-001"],
    "FED-006": ["ELEC-014"],
    "FED-007": ["FED-002"],
    "FED-008": ["FED-003"],
    "FUND-003": ["FUND-001"],
    "FUND-004": ["FED-003", "RET-001"],
    "FUND-005": ["FUND-001"],
    "FUND-006": ["FUND-001"],
    "FUND-007": ["FUND-001"],
    "FUND-008": ["FUND-001"],
    "HOR-030": ["EMERG-003"],
    "IMM-003": ["IMM-001"],
    "IMM-004": ["IMM-001"],
    "IMM-005": ["IMM-001"],
    "IMM-006": ["IMM-001"],
    "IMM-007": ["IMM-001", "DOJ-007"],
    "IMM-008": ["DOJ-007"],
    "JUD-007": ["JUD-001"],
    "JUD-008": ["JUD-005"],
    "OVS-002": ["OVS-001"],
    "OVS-003": ["OVS-001"],
    "OVS-005": ["OVS-001"],
    "OVS-006": ["OVS-001"],
    "OVS-007": ["OVS-001"],
    "PRESS-002": ["PRESS-001"],
    "PRESS-004": ["PRESS-006"],
    "PRESS-005": ["PRESS-006"],
    "PRESS-007": ["FACT-001", "FACT-009"],
    "PRESS-008": ["PRESS-006"],
    "PRESS-009": ["PRESS-003"],
    "PRESS-010": ["PRESS-006"],
    "PRESS-011": ["PRESS-006"],
    "PRESS-012": ["PRESS-001", "PRESS-003", "PRESS-006"],
    "REG-007": ["REG-001"],
    "REG-008": ["REG-001"],
    "RIGHTS-004": ["RIGHTS-002", "DOM-001", "FED-003"],
}


def current_routes(raw: str) -> list[str]:
    """Return unique current routes for a semicolon-delimited historical field."""
    routes: list[str] = []
    for route in (part.strip() for part in raw.split(";")):
        if not route:
            continue
        for current in ROUTE_ALIASES.get(route, [route]):
            if current not in routes:
                routes.append(current)
    return routes

