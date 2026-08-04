#!/usr/bin/env python3
"""Build the ARRP Project Console and public-input lookup."""

from __future__ import annotations

import argparse
import copy
import csv
import functools
import hashlib
import html
import json
import math
import os
import re
import shutil
import stat
import subprocess
import tempfile
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from github_disclosure_gate import (
        DisclosureBlocked,
        OutboundArtifact,
        prohibited_secret_findings,
        require_outbound_bundle,
    )
except ModuleNotFoundError:
    from scripts.github_disclosure_gate import (
        DisclosureBlocked,
        OutboundArtifact,
        prohibited_secret_findings,
        require_outbound_bundle,
    )

try:
    from project_tree import iter_project_files
except ModuleNotFoundError:  # Imported as scripts.build_project_console.
    from scripts.project_tree import iter_project_files

try:
    from build_project_console_progress import (
        extract_field_values as extract_project_field_values,
        fetch_project,
    )
except ModuleNotFoundError:  # Imported as scripts.build_project_console.
    from scripts.build_project_console_progress import (
        extract_field_values as extract_project_field_values,
        fetch_project,
    )

try:
    from source_monitor_recommendations import parse_source_monitor_recommendations
except ModuleNotFoundError:  # Imported as scripts.build_project_console.
    from scripts.source_monitor_recommendations import (
        parse_source_monitor_recommendations,
    )

try:
    from console_data_contracts import (
        feed_contract,
        file_sha256,
        source_hashes,
        source_revision,
        utc_timestamp,
        validate_contract,
    )
except ModuleNotFoundError:
    from scripts.console_data_contracts import (
        feed_contract,
        file_sha256,
        source_hashes,
        source_revision,
        utc_timestamp,
        validate_contract,
    )

try:
    from codex_usage_projection import (
        projection_is_valid as codex_usage_projection_is_valid,
        unavailable_projection as build_unavailable_codex_usage_projection,
    )
except ModuleNotFoundError:
    from scripts.codex_usage_projection import (
        projection_is_valid as codex_usage_projection_is_valid,
        unavailable_projection as build_unavailable_codex_usage_projection,
    )

try:
    from component_registry import (
        RegistryError as ComponentRegistryError,
        ROUTING_PREDECESSOR_PATHS,
        activation_readiness_report as component_registry_activation_readiness_report,
        audit_terminology as audit_component_registry_terminology,
        canonical_json as component_registry_canonical_json,
        inventory_report as component_registry_inventory_report,
        load_component_registry_configuration_routing_view,
        load_fixture_component_registry_configuration_routing_view,
        parity_report as component_registry_parity_report,
        render_context_routing_rule as component_registry_render_routing_rule,
        routed_capability_preview_from_view as component_registry_routed_capability_preview,
        routed_profile_preview_from_view as component_registry_routed_profile_preview,
        stage2_codeowners_projection as component_registry_codeowners_projection,
    )
except ModuleNotFoundError:
    from scripts.component_registry import (
        RegistryError as ComponentRegistryError,
        ROUTING_PREDECESSOR_PATHS,
        activation_readiness_report as component_registry_activation_readiness_report,
        audit_terminology as audit_component_registry_terminology,
        canonical_json as component_registry_canonical_json,
        inventory_report as component_registry_inventory_report,
        load_component_registry_configuration_routing_view,
        load_fixture_component_registry_configuration_routing_view,
        parity_report as component_registry_parity_report,
        render_context_routing_rule as component_registry_render_routing_rule,
        routed_capability_preview_from_view as component_registry_routed_capability_preview,
        routed_profile_preview_from_view as component_registry_routed_profile_preview,
        stage2_codeowners_projection as component_registry_codeowners_projection,
    )

try:
    from repository_gates import produce_repository_gate_snapshot
except ModuleNotFoundError:
    from scripts.repository_gates import produce_repository_gate_snapshot

try:
    from operational_incidents import project_incident_log
except ModuleNotFoundError:
    from scripts.operational_incidents import project_incident_log

try:
    from security_incidents import (
        SecurityIncidentContractError,
        project_security_incident_log,
        read_relation_events,
        relationship_projection,
        unavailable_security_projection,
    )
except ModuleNotFoundError:
    from scripts.security_incidents import (
        SecurityIncidentContractError,
        project_security_incident_log,
        read_relation_events,
        relationship_projection,
        unavailable_security_projection,
    )

try:
    from governance_changes import (
        GovernanceChange,
        GovernanceChangeError,
        parse_public_changes,
        project_private_supplements,
    )
except ModuleNotFoundError:
    from scripts.governance_changes import (
        GovernanceChange,
        GovernanceChangeError,
        parse_public_changes,
        project_private_supplements,
    )

try:
    from path_authority import (
        APPROVED_STATE_ROOT,
        PathAuthorityError,
        PrivateProjectAuthority,
        ProjectPathAuthority,
    )
except ModuleNotFoundError:
    from scripts.path_authority import (
        APPROVED_STATE_ROOT,
        PathAuthorityError,
        PrivateProjectAuthority,
        ProjectPathAuthority,
    )


ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = APPROVED_STATE_ROOT
COMPONENT_REGISTRY = ROOT / "framework" / "component-registry.json"
COMPONENT_REGISTRY_SCHEMA = (
    ROOT / "framework" / "standards" / "automation"
    / "component-registry.schema.json"
)
COMPONENT_REGISTRY_ROUTE_SOURCE = (
    ROOT
    / ROUTING_PREDECESSOR_PATHS["context_routes_source"]["historical_path"]
)
CANDIDATES = ROOT / "research" / "trump-administration-preliminary-candidates.csv"
HORIZON_LOG = (
    ROOT / "framework" / "logs" / "candidates"
    / "candidate-discovery-log.md"
)
CHANGE_AUDIT_LOG = (
    ROOT / "framework" / "logs" / "audits" / "change-audit-log.md"
)
GOVERNANCE_CHANGE_LOG = (
    ROOT / "framework" / "logs" / "governance"
    / "governance-change-log.md"
)
GOVERNANCE_CHANGE_REGISTRY = (
    ROOT / "framework" / "project" / "workflows"
    / "governance-change-registry.json"
)
CONSOLE_DEVELOPMENT_LOG = (
    ROOT / "framework" / "logs" / "automation" / "console-development-log.md"
)
AGENT_AUDIT_LOG = STATE_ROOT / "records" / "automation" / "agent-audit-log.md"
ELIM_RUN_LOG = STATE_ROOT / "records" / "automation" / "elim-run-log.md"
SOURCE_CHECKER_CONFIG = ROOT / "framework/project/automation/configuration/bots/source-checker-bot.json"
SOURCE_MONITOR_LOG = (
    ROOT / "framework" / "logs" / "sources" / "source-monitor-log.md"
)
AGENT_RUNBOOKS = ROOT / "framework" / "project" / "automation" / "runbooks"
ISSUE_REGISTRY = ROOT / "inventory" / "github_issue_registry.csv"
CITED_SOURCES = ROOT / "inventory" / "sources.csv"
PENDING_SOURCES = ROOT / "inventory" / "sources-pending.csv"
DIRECTIVES = ROOT / "inventory" / "presidential-directives.csv"
CASE_MONITOR_CONFIG = ROOT / "framework/project/automation/configuration/bots/case-monitor-bot.json"
DIRECTIVE_MONITOR_CONFIG = ROOT / "framework/project/automation/configuration/bots/presidential-directives-bot.json"
RUN_COORDINATOR_CONFIG = ROOT / "framework/project/automation/configuration/bots/run-coordinator-bot.json"
PRINT_ASSEMBLY_MANIFEST = (
    ROOT / "framework" / "project" / "publication" / "print-assembly.json"
)
REVIEW_EPOCHS = STATE_ROOT / "records" / "automation" / "review-epochs.jsonl"
TRANSACTION_RECOVERY_CONSOLE_PROJECTION = (
    STATE_ROOT / "records" / "reconciliation" / "transaction-recovery"
    / "console-projection.json"
)
PUBLIC_REVIEW_EPOCH_SUMMARY = ROOT / "research" / "review-epochs-summary.json"
PUBLIC_PROPOSAL_PDF = ROOT / "exports" / "pdf" / "ARRP-public-proposal-draft.pdf"
PROJECT_CONSOLE_ROOT = (
    ROOT / "framework" / "project" / "interfaces" / "project-console"
)
OUTPUT = PROJECT_CONSOLE_ROOT / "catalog-data.js"
CONSOLE_DATA_DIR = PROJECT_CONSOLE_ROOT / "data"
PRIVATE_SECURITY_ASSURANCE_OUTPUT = (
    CONSOLE_DATA_DIR / "private-security-assurance.js"
)
PRIVATE_CODEX_USAGE_OUTPUT = CONSOLE_DATA_DIR / "private-codex-usage.js"
CONSOLE_CLASSIFICATION_REGISTRY = (
    ROOT / "framework" / "project" / "interfaces"
    / "project-console"
    / "configuration"
    / "classifications.json"
)
CONSOLE_DEVELOPMENT_LOG = (
    ROOT / "framework" / "logs" / "automation"
    / "console-development-log.md"
)
PRIVATE_OPERATIONS_OUTPUT = CONSOLE_DATA_DIR / "private-operations.js"
REPOSITORY_GATES_SNAPSHOT = ROOT / ".tmp" / "repository-gates.json"
REPOSITORY_GATES_LAST_GOOD = ROOT / ".tmp" / "repository-gates-last-good.json"
REPOSITORY_GATE_DECLARATIONS = (
    STATE_ROOT / "records" / "automation" / "repository-gates.jsonl"
)
OPERATIONAL_INCIDENT_LOG = (
    STATE_ROOT / "records" / "automation" / "operational-incidents.jsonl"
)
SECURITY_INCIDENT_RELATIVE = "automation/security-incidents.jsonl"
INCIDENT_RELATIONS_RELATIVE = "automation/incident-relations.jsonl"
GOVERNANCE_SUPPLEMENTS_RELATIVE = (
    "governance/governance-change-supplements.jsonl"
)
OWNER_MODE_UNAVAILABLE_MESSAGE = (
    "Data unavailable outside the bound owner-local Console."
)
ALLOW_PRIVATE_CONSOLE_INPUTS = True
PARTICIPATION_OUTPUT = ROOT / "participate" / "intake-data.js"
GITHUB_BLOB_ROOT = "https://github.com/Thorncrag/ARRP/blob/main/"
HORIZON_LOG_URL = GITHUB_BLOB_ROOT + "framework/logs/candidates/candidate-discovery-log.md#horizon-integration-log"


def validated_workbench_external_url(
    value: object,
    *,
    kind: str,
) -> str | None:
    """Return one typed ARRP GitHub link or an unavailable value."""

    text = str(value or "").strip()
    if not text or len(text) > 2048:
        return None
    try:
        parsed = urllib.parse.urlsplit(text)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
    ):
        return None
    if kind == "issue":
        valid = re.fullmatch(r"/Thorncrag/ARRP/issues/[1-9][0-9]*", parsed.path)
    elif kind in {"canonical", "audit"}:
        valid = re.fullmatch(
            r"/Thorncrag/ARRP/blob/(?:main|[0-9a-f]{40})/[^?#]+",
            parsed.path,
        )
    else:
        valid = None
    return text if valid else None


LOCAL_INTEGRITY_FEED = ROOT / ".tmp" / "project-console-integrity.json"
LOCAL_RUN_CHAIN_FEED = ROOT / ".tmp" / "run-chain.json"
PUBLIC_SOURCE_CHECKER_STAGE = (
    ROOT / ".tmp" / "project-console-source-checker.json"
)
CONSOLE_GENERATION_MANIFEST_PATH = (
    "framework/project/interfaces/project-console/data/"
    "generation-manifest.json"
)
CONSOLE_GENERATION_CATALOG_PATH = (
    "framework/project/interfaces/project-console/catalog-data.js"
)
CONSOLE_GENERATION_REPORT_PATHS = frozenset({
    "framework/status/integrity/project-integrity-report.md",
    "framework/status/sources/source-checker-report.md",
})
SNAPSHOT_OVERRIDE_PATHS = {
    "ARRP_PROGRESS_SNAPSHOT": Path(
        ".tmp/project-console-progress-snapshot.json"
    ),
    "ARRP_INTEGRITY_SNAPSHOT": Path(".tmp/project-console-integrity.json"),
    "ARRP_SOURCE_CHECKER_SNAPSHOT": Path(".tmp/source-checker.json"),
}
LEGACY_RUN_CHAIN_PATHS = {
    "framework/logs/ELIM_RUN_LOG.md":
        "owner-local:records/automation/elim-run-log.md",
}
PUBLIC_RUN_CHAIN_FIELDS = frozenset({
    "action_items",
    "actual_count",
    "availability",
    "baseline_commit",
    "bot_id",
    "bots",
    "chain_id",
    "completed_at",
    "completeness",
    "context_packet",
    "created_at",
    "degradations",
    "elim_decision",
    "expected_count",
    "failures",
    "final_revision",
    "llm_launch_allowed",
    "llm_launch_trigger",
    "latest_scheduled_attempt",
    "lock",
    "next_action",
    "projection_errors",
    "queue_counts",
    "repository",
    "repository_gates",
    "resume",
    "review_epoch",
    "run_id",
    "schema_version",
    "stages",
    "status",
    "trigger",
    "updated_at",
    "usage",
    "work_queue",
    "workflow_health",
})
AUTOMATION_OCCURRENCE_STAGE_SPECS: tuple[tuple[str, str], ...] = (
    ("case-monitor-bot", "Cases"),
    ("presidential-directives-bot", "Presidential directives"),
    ("source-checker-bot", "Sources"),
    ("public-intake", "Public input"),
    ("project-console-progress-bot", "Progress"),
    ("project-integrity-bot", "Integrity"),
    ("elim", "Elim"),
)
LOCAL_RUN_CHAIN_PATH_FIELDS = frozenset({
    "baselinePath",
    "baseline_path",
    "local_path",
    "status_path",
})
PRINT_LEVEL_ORDER = (
    "public-proposal",
    "legislative-appendix",
    "executive-summary",
)
PRINT_LEVEL_LABELS = {
    "public-proposal": "Public proposal edition",
    "legislative-appendix": "Legislative appendix edition",
    "executive-summary": "Executive summary edition",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-github",
        action="store_true",
        help="Refresh formal Horizon issue and Project data through authenticated gh commands.",
    )
    parser.add_argument(
        "--console-only",
        action="store_true",
        help="Rebuild the ARRP Project Console without rewriting the public-input lookup.",
    )
    parser.add_argument(
        "--public-only",
        action="store_true",
        help=(
            "Generate only tracked public Console outputs without opening ignored "
            "local Console projections or restoring owner-only projections."
        ),
    )
    parser.add_argument(
        "--public-source-checker-stage",
        action="store_true",
        help=(
            "Use the fixed repository-local Source Checker staging report "
            "for this public-only Console generation."
        ),
    )
    return parser.parse_args()


def validate_console_modes(args: argparse.Namespace) -> None:
    if args.public_only and args.refresh_github:
        raise RuntimeError(
            "--public-only cannot be combined with authenticated refresh."
        )
    if args.public_source_checker_stage and not args.public_only:
        raise RuntimeError(
            "--public-source-checker-stage requires --public-only."
        )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def split_values(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(";") if part.strip()]


def parse_links(raw: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for item in raw.split("||"):
        item = item.strip()
        if not item or "|" not in item:
            continue
        label, url = item.split("|", 1)
        if label.strip() and url.strip():
            links.append({"label": label.strip(), "url": url.strip()})
    return links


def all_source_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path, inventory_status in (
        (CITED_SOURCES, "Relied upon"),
        (PENDING_SOURCES, "Pending verification or placement"),
    ):
        for row in read_csv(path):
            if not row["Source ID"].strip():
                continue
            records.append({**row, "_inventory_status": inventory_status})
    return records


def source_index() -> dict[str, dict[str, str]]:
    return {row["Source ID"].strip(): row for row in all_source_records()}


def source_payload(row: dict[str, str]) -> dict[str, object]:
    def value(key: str, default: str = "") -> str:
        return (row.get(key) or default).strip()

    return {
        "id": value("Source ID"),
        "record_ids": sorted(associated_record_ids(value("Associated Record IDs"))),
        "monitoring": value("Monitoring", "No") or "No",
        "inventory_status": row.get("_inventory_status", "Relied upon"),
        "type": value("Source Type"),
        "publisher": value("Authority / Publisher"),
        "title": value("Title or Description"),
        "date": value("Date"),
        "url": value("URL"),
        "proposition": value("Proposition Supported"),
        "reliability": value("Reliability Tier"),
        "reviewed": value("Reviewed?"),
        "notes": value("Notes"),
        "retention_rationale": value("Retention Rationale"),
        "pending_reason": value("Pending Reason"),
        "next_action": value("Next Action"),
        "blocker": value("Blocker"),
        "monitoring_rationale": value("Monitoring Rationale"),
        "monitoring_group": value("Monitoring Group"),
        # The console exposes whether an accepted watcher baseline exists, not
        # the raw fingerprint itself.
        "monitoring_baseline_present": bool(value("Monitoring Baseline")),
    }


def catalog_source_records(
    path: Path, inventory_status: str
) -> list[dict[str, object]]:
    records = [
        source_payload({**row, "_inventory_status": inventory_status})
        for row in read_csv(path)
        if row["Source ID"].strip()
    ]
    return sorted(records, key=lambda row: str(row["id"]))


def presidential_directive_records() -> list[dict[str, object]]:
    if not DIRECTIVES.exists():
        return []
    records: list[dict[str, object]] = []
    for row in read_csv(DIRECTIVES):
        directive_id = row.get("Directive ID", "").strip()
        if not directive_id:
            continue
        records.append(
            {
                "id": directive_id,
                "administration": row.get("Administration", "").strip(),
                "president": row.get("President", "").strip(),
                "type": row.get("Directive Type", "").strip(),
                "number": row.get("Number", "").strip(),
                "title": row.get("Title", "").strip(),
                "signed_date": row.get("Signed Date", "").strip(),
                "published_date": row.get("Published Date", "").strip(),
                "citation": row.get("Federal Register Citation", "").strip(),
                "official_url": (
                    row.get("Official PDF URL", "").strip()
                    or row.get("Federal Register URL", "").strip()
                ),
                "federal_register_url": row.get("Federal Register URL", "").strip(),
                "related_directive_ids": split_values(row.get("Related Directive IDs", "")),
                "first_seen": row.get("First Seen", "").strip(),
                "last_changed": row.get("Last Changed", "").strip(),
                "review_status": row.get("Review Status", "").strip() or "New since baseline screening",
                "arrp_record_ids": split_values(row.get("ARRP Record IDs", "")),
                "source_ids": split_values(row.get("Source IDs", "")),
                "disposition_rationale": row.get("Disposition Rationale", "").strip(),
                "reviewed_date": row.get("Reviewed Date", "").strip(),
            }
        )
    return sorted(
        records,
        key=lambda row: (
            str(row["signed_date"] or row["published_date"]),
            str(row["id"]),
        ),
        reverse=True,
    )


def markdown_front_matter(content: str) -> dict[str, object]:
    """Parse the small title/list subset used by ARRP page metadata."""
    if not content.startswith("---\n"):
        return {}
    end = content.find("\n---\n", 4)
    if end < 0:
        return {}
    values: dict[str, object] = {}
    active_list: str | None = None
    for raw_line in content[4:end].splitlines():
        if raw_line.startswith("  - ") and active_list:
            value = raw_line[4:].strip().strip('"\'')
            cast = values.setdefault(active_list, [])
            if isinstance(cast, list) and value:
                cast.append(value)
            continue
        active_list = None
        if not raw_line or raw_line.startswith(" ") or ":" not in raw_line:
            continue
        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        value = raw_value.strip().strip('"\'')
        if value:
            values[key] = value
        else:
            values[key] = []
            active_list = key
    return values


def agent_registry_records() -> list[dict[str, object]]:
    """Build the Console's concise operational registry from authoritative runbooks."""
    if not AGENT_RUNBOOKS.exists():
        return []
    records: list[dict[str, object]] = []
    for path in sorted(AGENT_RUNBOOKS.glob("*.md")):
        if path.name == "README.md":
            continue
        content = path.read_text(encoding="utf-8")
        metadata = markdown_front_matter(content)
        agent_id = str(metadata.get("agent_id", "")).strip()
        if not agent_id:
            continue
        body = content.split("\n---\n", 1)[-1]
        description_match = re.search(r"^# .+?\n\n(.+?)(?=\n\n|\n#)", body, re.MULTILINE | re.DOTALL)
        description = strip_markdown(description_match.group(1).strip()) if description_match else ""
        runtime_id = str(metadata.get("runtime_id", "")).strip()
        runtime_config = str(metadata.get("runtime_config", "")).strip()
        runtime_configuration: dict[str, object] = {}
        if runtime_config:
            config_path = ROOT / runtime_config
            try:
                parsed_configuration = json.loads(config_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                parsed_configuration = {}
            if isinstance(parsed_configuration, dict):
                runtime_configuration = parsed_configuration
        run_log_path = str(metadata.get("run_log_path", "")).strip()
        current_report = str(metadata.get("current_report", "")).strip()
        current_data = str(metadata.get("current_data", "")).strip()
        raw_checks = metadata.get("checks_included", [])
        checks = (
            [str(item).strip() for item in raw_checks if str(item).strip()]
            if isinstance(raw_checks, list)
            else []
        )
        runtime_url = (
            GITHUB_BLOB_ROOT + runtime_id
            if runtime_id.startswith(".github/")
            else ""
        )
        records.append(
            {
                "id": agent_id,
                "name": str(metadata.get("display_name", agent_id)).strip(),
                "type": str(metadata.get("agent_type", "")).strip(),
                "status": str(metadata.get("status", "unknown")).strip(),
                "trigger": str(metadata.get("trigger", "")).strip(),
                "schedule": str(metadata.get("schedule", "")).strip(),
                "runtime_id": runtime_id,
                "runtime_url": runtime_url,
                "runtime_config": runtime_config,
                "execution_environment": str(metadata.get("execution_environment", "")).strip(),
                "model_policy": str(metadata.get("model_policy", "")).strip(),
                "log_path": str(metadata.get("log_path", "")).strip(),
                "run_log_path": run_log_path,
                "run_log_url": (
                    GITHUB_BLOB_ROOT + run_log_path
                    if run_log_path and not run_log_path.startswith("owner-local:")
                    else ""
                ),
                "current_report": current_report,
                "current_report_url": GITHUB_BLOB_ROOT + current_report if current_report else "",
                "current_data": current_data,
                "purpose": str(metadata.get("console_purpose", description)).strip(),
                "checks": checks,
                "runtime_configuration": runtime_configuration,
                "runbook_path": str(path.relative_to(ROOT)),
                "runbook_url": GITHUB_BLOB_ROOT + str(path.relative_to(ROOT)),
            }
        )
    display_order = {
        "run-coordinator-bot": 1,
        "case-monitor-bot": 2,
        "presidential-directives-bot": 3,
        "source-checker-bot": 4,
        "project-console-progress-bot": 5,
        "project-integrity-bot": 6,
        "elim": 7,
    }
    return sorted(
        records,
        key=lambda record: (
            display_order.get(str(record["id"]), 999),
            str(record["name"]),
        ),
    )


def public_safe_agent_registry(
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Allowlist the provider-neutral public summary for each automation role."""

    allowed = (
        "id",
        "name",
        "type",
        "status",
        "trigger",
        "schedule",
        "purpose",
    )
    return [
        {key: record.get(key) for key in allowed}
        for record in records
        if isinstance(record, dict)
    ]


def public_safe_project_logs(
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Retain public project-history ledgers; keep raw operations owner-local."""

    public_ids = {
        "horizon",
        "source-monitor",
        "changes",
        "governance-changes",
        "console-development",
    }
    projected: list[dict[str, object]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("id") in public_ids:
            projected.append(record)
            continue
        projected.append(
            {
                "id": record.get("id"),
                "title": record.get("title"),
                "description": record.get("description"),
                "source_url": None,
                "columns": record.get("columns") or [],
                "group_options": record.get("group_options") or [],
                "default_sort": record.get("default_sort")
                or {"key": "date", "direction": "desc"},
                "entries": [],
                "entry_count": None,
                "availability": "unavailable",
                "complete": False,
                "schema_errors": [],
                "current_through": None,
                "producer": record.get("producer"),
                "reason": OWNER_MODE_UNAVAILABLE_MESSAGE,
            }
        )
    return projected


def public_safe_integrity(
    integrity: dict[str, object],
) -> dict[str, object]:
    """Publish only typed Integrity posture; detailed diagnostics stay local."""

    if not isinstance(integrity, dict):
        return {}
    registry = console_classification_registry()
    finding_definitions = {
        str(entry.get("id")): entry
        for entry in registry.get("namespaces", {}).get("finding_code", [])
        if isinstance(entry, dict)
    }
    safe = {
        key: integrity.get(key)
        for key in (
            "schema_version",
            "availability",
            "complete",
            "generated_at",
            "revision",
            "current_through",
            "trustworthy_through",
        )
        if key in integrity
    }
    current = integrity.get("current")
    if isinstance(current, dict):
        safe_current = {
            key: current.get(key)
            for key in (
                "finding_count",
                "result",
                "checked_at",
                "generated_at",
                "revision",
                "scope",
                "availability",
                "complete",
            )
            if key in current
        }
        findings = current.get("findings")
        if isinstance(findings, list):
            safe_findings: list[dict[str, object]] = []
            for item in findings:
                if not isinstance(item, dict):
                    continue
                finding_code = str(
                    item.get("finding_code")
                    or item.get("condition_code")
                    or ""
                ).strip()
                definition = finding_definitions.get(finding_code)
                if not finding_code or definition is None:
                    raise RuntimeError(
                        "Integrity projection contains an unregistered finding code."
                    )
                severity = str(
                    item.get("severity") or "warning"
                ).strip().casefold()
                safe_findings.append(
                    {
                        "finding_id": item.get("finding_id"),
                        "finding_code": finding_code,
                        "severity": severity,
                        "category": item.get("category"),
                        "status": item.get("status"),
                        "owner": definition.get("lifecycle_owner"),
                        "route": definition.get("destination"),
                        "next_action": definition.get("next_action")
                        or (
                            "Open Integrity and resolve the registered "
                            "producer condition."
                        ),
                        "message": definition.get("public_summary")
                        or (
                            "A typed integrity error requires review."
                            if severity == "error"
                            else "A typed integrity finding requires review."
                        ),
                    }
                )
            safe_current["findings"] = safe_findings
        safe["current"] = safe_current
    safe["history"] = []
    return safe


def safe_automation_explanation(status: object, *, subject: str) -> str:
    """Return a generic, status-derived explanation suitable for public data."""

    normalized = str(status or "unavailable").strip().casefold().replace("-", "_")
    messages = {
        "succeeded": f"{subject} completed successfully.",
        "completed": f"{subject} completed successfully.",
        "running": f"{subject} is in progress.",
        "pending": f"{subject} is pending.",
        "not_due": f"{subject} was not due for this occurrence.",
        "skipped": f"{subject} was intentionally skipped.",
        "blocked": f"{subject} is blocked; protected diagnostic detail is owner-local.",
        "failed": f"{subject} did not complete; protected diagnostic detail is owner-local.",
        "degraded": f"{subject} completed with a degraded result.",
        "unavailable": f"{subject} status is unavailable.",
    }
    return messages.get(normalized, f"{subject} status is unavailable.")


def public_safe_trigger(value: object) -> str:
    """Keep trigger class, never host dispatcher or command detail."""

    text = str(value or "").casefold()
    if re.search(r"schedule|launchd|nightly|timer", text):
        return "scheduled"
    if re.search(r"manual|interactive", text):
        return "manual"
    if re.search(r"push|pull.request|workflow|event", text):
        return "event"
    return "unavailable"


def public_usage_projection(usage: dict[str, object]) -> dict[str, object]:
    """Report measurement posture without exporting the owner-local percentage."""

    remaining = usage.get("remaining_percent")
    measured = (
        usage.get("status") == "measured_owner_local"
        or (
            isinstance(remaining, (int, float))
            and not isinstance(remaining, bool)
            and usage.get("status") == "available"
        )
    )
    return {
        "hard_reserve_percent": usage.get("hard_reserve_percent"),
        "soft_run_target_percent": usage.get("soft_run_target_percent"),
        "remaining_percent": None,
        "status": "measured_owner_local" if measured else "unknown",
        "disclosure": (
            "The usage reserve was measured; the exact remaining percentage "
            "is retained owner-locally."
            if measured
            else "No current usage-reserve measurement is available."
        ),
    }


def public_safe_run_chain(
    chain: dict[str, object],
) -> dict[str, object]:
    """Allowlist compact run status without publishing operational diagnostics."""

    if not isinstance(chain, dict):
        return {}
    allowed_top_level = (
        "schema_version",
        "run_id",
        "chain_id",
        "bot_id",
        "status",
        "trigger",
        "created_at",
        "updated_at",
        "completed_at",
        "availability",
        "completeness",
        "expected_count",
        "actual_count",
        "baseline_commit",
        "repository",
        "queue_counts",
    )
    projection = {
        key: chain.get(key)
        for key in allowed_top_level
        if key in chain
    }
    stage_fields = (
        "id",
        "name",
        "order",
        "status",
        "due",
        "started_at",
        "updated_at",
        "completed_at",
        "last_success_at",
        "current_chain_label",
    )
    projection["stages"] = [
        {
            key: stage.get(key)
            for key in stage_fields
            if key in stage
        }
        | {
            "reason": safe_automation_explanation(
                stage.get("status"), subject="This stage"
            ),
            "current_chain_label": (
                "Not due this chain"
                if str(stage.get("status") or "").strip() == "not_due"
                else str(stage.get("status") or "unavailable").replace("_", " ").title()
            ),
        }
        for stage in chain.get("stages") or []
        if isinstance(stage, dict)
    ]
    epoch = chain.get("review_epoch")
    if isinstance(epoch, dict):
        epoch_fields = (
            "epoch_id",
            "review_id",
            "due",
            "interval_days",
            "last_completed_at",
            "next_due_at",
            "stability_status",
        )
        projection["review_epoch"] = {
            key: epoch.get(key)
            for key in epoch_fields
            if key in epoch
        }
    usage = chain.get("usage")
    if isinstance(usage, dict):
        projection["usage"] = public_usage_projection(usage)
    decision = chain.get("elim_decision")
    if isinstance(decision, dict):
        projection["elim_decision"] = {
            key: decision.get(key)
            for key in ("decision", "launch_recommended", "launched")
            if key in decision
        }
    return projection


def unavailable_incident_projection(
    incident_kind: str,
    *,
    reason_code: str = "owner-local-projection-required",
) -> dict[str, object]:
    """Return the only incident representation allowed in the public bundle."""

    if incident_kind not in {"operational", "security"}:
        raise RuntimeError("Unknown private incident projection kind.")
    return {
        "schema_version": 1,
        "incident_kind": incident_kind,
        "availability": "unavailable",
        "complete": False,
        "checked_at": None,
        "count": None,
        "unresolved_count": None,
        "items": [],
        "impact_state": "gray",
        "reason_code": reason_code,
        "detail_mode": "owner-local-file-only",
    }


def unavailable_incident_relations(
    reason_code: str = "owner-local-projection-required",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "authority": "owner-local-incident-relations",
        "availability": "unavailable",
        "complete": False,
        "checked_at": None,
        "active_relations": [],
        "relations": [],
        "by_operational_incident": {},
        "by_security_incident": {},
        "reason_code": reason_code,
    }


def public_safe_automation_role_status(
    projection: dict[str, object],
) -> dict[str, object]:
    """Remove owner-local incident relationships from public role status."""

    safe = copy.deepcopy(projection)
    safe["roles"] = [
        {
            key: value
            for key, value in role.items()
            if key != "active_incident_ids"
        }
        for role in safe.get("roles") or []
        if isinstance(role, dict)
    ]
    return safe


def public_safe_repository_gates(
    projection: dict[str, object],
) -> dict[str, object]:
    """Keep governed gate status public without exposing private incident links."""

    safe = copy.deepcopy(projection)
    safe["items"] = [
        {
            key: value
            for key, value in item.items()
            if key != "active_incident_ids"
        }
        for item in safe.get("items") or []
        if isinstance(item, dict)
    ]
    return safe


def public_safe_automation_occurrences(
    projection: dict[str, object],
) -> dict[str, object]:
    """Retain occurrence posture without exporting operational diagnostics."""

    safe = copy.deepcopy(projection)
    safe["role_currentness"] = {"state": "unavailable"}
    safe["trustworthy_through"] = None
    safe["occurrences"] = [
        {
            **{
                key: occurrence.get(key)
                for key in (
                    "occurrence_id",
                    "schedule_identity",
                    "status",
                    "source_revision",
                    "generation_id",
                    "created_at",
                    "started_at",
                    "completed_at",
                    "updated_at",
                    "scheduled_for",
                    "complete",
                    "control_state",
                    "control_state_checked_at",
                )
                if key in occurrence
            },
            "trigger": public_safe_trigger(occurrence.get("trigger")),
            "reason": safe_automation_explanation(
                occurrence.get("status"), subject="This occurrence"
            ),
            "stages": [
                {
                    key: stage.get(key)
                    for key in (
                        "stage_id",
                        "label",
                        "order",
                        "occurrence_id",
                        "status",
                        "current_chain_label",
                        "due",
                        "started_at",
                        "completed_at",
                        "prior_success_at",
                    )
                    if key in stage
                }
                | {
                    "reason": safe_automation_explanation(
                        stage.get("status"), subject="This stage"
                    )
                }
                for stage in occurrence.get("stages") or []
                if isinstance(stage, dict)
            ],
            "blockers": [
                {
                    "id": f"{occurrence.get('occurrence_id')}-blocker-{index}",
                    "stage_id": blocker.get("stage_id"),
                    "status": "blocked",
                    "recorded_at": blocker.get("recorded_at"),
                    "reason": safe_automation_explanation(
                        "blocked", subject="A recorded occurrence blocker"
                    ),
                }
                for index, blocker in enumerate(occurrence.get("blockers") or [], start=1)
                if isinstance(blocker, dict)
            ],
        }
        for occurrence in safe.get("occurrences") or []
        if isinstance(occurrence, dict)
    ]
    return safe


AUTOMATION_ROLE_CONTRACTS: tuple[dict[str, object], ...] = (
    {
        "id": "run-coordinator-bot",
        "display_order": 1,
        "menu_label": "Coordinator",
        "role_type": "Bot",
        "cadence": "Daily · 2:00 AM ET",
        "eligibility": "Scheduled local transaction or approved manual start",
    },
    {
        "id": "case-monitor-bot",
        "display_order": 2,
        "menu_label": "Case Monitor",
        "role_type": "Bot",
        "cadence": "Every 24 hours",
        "eligibility": "Runs in the serialized chain when its cadence is due",
    },
    {
        "id": "presidential-directives-bot",
        "display_order": 3,
        "menu_label": "Directives",
        "role_type": "Bot",
        "cadence": "Every 24 hours",
        "eligibility": "Runs in the serialized chain when its cadence is due",
    },
    {
        "id": "source-checker-bot",
        "display_order": 4,
        "menu_label": "Source Checker",
        "role_type": "Bot",
        "cadence": "Every 168 hours",
        "eligibility": "Runs in the serialized chain when its cadence is due",
    },
    {
        "id": "project-console-progress-bot",
        "display_order": 5,
        "menu_label": "Progress",
        "role_type": "Bot",
        "cadence": "Every 24 hours",
        "eligibility": "Runs in the serialized chain when its cadence is due",
    },
    {
        "id": "project-integrity-bot",
        "display_order": 6,
        "menu_label": "Integrity",
        "role_type": "Bot",
        "cadence": "Every serialized run",
        "eligibility": "Runs after the preceding serialized stages complete",
    },
    {
        "id": "elim",
        "display_order": 7,
        "menu_label": "Elim",
        "role_type": "Agent",
        "cadence": "Eligible serialized runs only",
        "eligibility": "One typed, eligible work unit selected by the coordinator",
    },
)


def automation_role_status_projection(
    *,
    agent_registry: list[dict[str, object]],
    run_chain: dict[str, object],
    progress: dict[str, object],
    integrity: dict[str, object],
    source_checker: dict[str, object],
    checked_at: str,
) -> dict[str, object]:
    """Publish the typed role status consumed by every Console role surface.

    The browser may join an exact owner-only Run/Paused record to this
    projection, but it must not reconstruct role health from runbook prose,
    log narratives, or a different successful run.
    """

    registry_by_id = {
        str(record.get("id") or ""): record
        for record in agent_registry
        if isinstance(record, dict) and str(record.get("id") or "")
    }
    stages = {
        str(stage.get("id") or stage.get("stage_id") or ""): stage
        for stage in (run_chain.get("stages") or [])
        if isinstance(stage, dict)
    }
    failures_by_role: dict[str, dict[str, object]] = {}
    for failure in (run_chain.get("failures") or []):
        if not isinstance(failure, dict):
            continue
        role_id = overview_automation_stage_id(
            failure.get("stage_id")
            or failure.get("stage")
            or failure.get("affected_stage")
        )
        if role_id:
            failures_by_role[role_id] = failure

    chain_checked_at = str(
        run_chain.get("host_updated_at")
        or run_chain.get("updated_at")
        or run_chain.get("completed_at")
        or checked_at
    )
    chain_trigger = str(run_chain.get("trigger") or "").casefold()
    chain_is_scheduled = bool(
        re.search(r"schedule|launchd|nightly|timer", chain_trigger)
    )
    feed_by_role = {
        "source-checker-bot": source_checker,
        "project-console-progress-bot": progress,
        "project-integrity-bot": integrity,
    }

    roles: list[dict[str, object]] = []
    for contract in AUTOMATION_ROLE_CONTRACTS:
        role_id = str(contract["id"])
        registry = registry_by_id.get(role_id, {})
        stage = stages.get(role_id, {})
        stage_status = str(stage.get("status") or "").casefold()
        stage_failed = bool(re.search(r"fail|block|error", stage_status))
        failure = failures_by_role.get(role_id)
        last_success_at = stage.get("last_success_at")

        latest_scheduled: dict[str, object] = {
            "available": False,
            "outcome": "unavailable",
            "at": None,
            "source": "run-chain",
            "reason": (
                "No typed latest scheduled occurrence is published for this role."
            ),
        }
        if role_id == "run-coordinator-bot" and chain_is_scheduled and run_chain:
            latest_scheduled = {
                "available": True,
                "outcome": str(
                    run_chain.get("status")
                    or run_chain.get("outcome")
                    or "unavailable"
                ),
                "at": chain_checked_at,
                "source": "run-chain",
                "run_id": run_chain.get("run_id") or run_chain.get("chain_id"),
                "reason": "",
            }
        elif role_id != "elim" and last_success_at:
            latest_scheduled = {
                "available": True,
                "outcome": "succeeded",
                "at": last_success_at,
                "source": "run-chain-stage-last-success",
                "run_id": run_chain.get("run_id") or run_chain.get("chain_id"),
                "reason": "",
            }
        elif role_id == "elim":
            latest_scheduled["reason"] = (
                "Elim is eligibility-triggered rather than independently scheduled."
            )

        current_blocker = None
        if failure or stage_failed:
            raw = failure or stage
            current_blocker = {
                "id": str(
                    raw.get("id")
                    or raw.get("failure_id")
                    or f"{role_id}-current-blocker"
                ),
                "summary": str(
                    raw.get("reason")
                    or raw.get("message")
                    or raw.get("details")
                    or raw.get("summary")
                    or "The current role occurrence is blocked."
                ),
                "route": f"automation:agents:{role_id}",
            }

        feed = feed_by_role.get(role_id)
        if isinstance(feed, dict) and feed:
            feed_availability = str(feed.get("availability") or "unavailable")
            feed_reason = str(
                feed.get("availability_reason")
                or feed.get("reason")
                or ""
            )
            data_currentness = {
                "state": feed_availability,
                "checked_at": (
                    feed.get("generated_at")
                    or feed.get("checked_at")
                    or checked_at
                ),
                "reason": feed_reason,
            }
        elif stage:
            if stage_failed:
                currentness_state = "error"
                currentness_reason = (
                    "The latest applicable role occurrence did not complete."
                )
            elif stage.get("due") is False or stage_status in {
                "succeeded",
                "success",
                "completed",
                "not_due",
            }:
                currentness_state = "current"
                currentness_reason = str(
                    stage.get("due_reason")
                    or "The Run Coordinator reports this role as current."
                )
            else:
                currentness_state = "unavailable"
                currentness_reason = (
                    "The Run Coordinator did not publish a conclusive currentness state."
                )
            data_currentness = {
                "state": currentness_state,
                "checked_at": chain_checked_at,
                "reason": currentness_reason,
            }
        elif role_id == "run-coordinator-bot" and run_chain:
            data_currentness = {
                "state": (
                    "error"
                    if re.search(
                        r"fail|block|error",
                        str(run_chain.get("status") or ""),
                        re.IGNORECASE,
                    )
                    else "current"
                ),
                "checked_at": chain_checked_at,
                "reason": "Derived by the producer from the typed run-chain record.",
            }
        else:
            data_currentness = {
                "state": "unavailable",
                "checked_at": checked_at,
                "reason": "No typed currentness record is published for this role.",
            }

        last_successful = {
            "available": bool(last_success_at),
            "at": last_success_at,
            "source": "run-chain-stage-last-success",
            "reason": (
                ""
                if last_success_at
                else "No typed last-successful occurrence is published."
            ),
        }
        if role_id == "run-coordinator-bot" and chain_is_scheduled:
            chain_status = str(run_chain.get("status") or "").casefold()
            if re.search(r"success|complete|healthy", chain_status):
                last_successful = {
                    "available": True,
                    "at": chain_checked_at,
                    "source": "run-chain",
                    "reason": "",
                }

        roles.append(
            {
                **contract,
                "display_name": str(
                    registry.get("name") or contract.get("menu_label") or role_id
                ),
                "latest_scheduled": latest_scheduled,
                "last_successful": last_successful,
                "next_due_at": None,
                "next_due_reason": (
                    "A typed next-due timestamp is not published."
                ),
                "pause_state": "unavailable",
                "current_blocker": current_blocker,
                "data_currentness": data_currentness,
                "checked_at": chain_checked_at,
            }
        )

    return {
        "schema_version": 1,
        "availability": "current" if agent_registry else "unavailable",
        "checked_at": chain_checked_at,
        "control_state": {
            "state": "unavailable",
            "source": "owner-only-local-status",
            "checked_at": None,
            "reason": (
                "The public producer does not read the owner-only host control."
            ),
        },
        "roles": roles,
    }


def page_section(relative: Path) -> str:
    parts = relative.parts
    if relative == Path("README.md"):
        return "Front matter"
    if not parts:
        return "Root"
    labels = {
        "areas": "Areas and proposals",
        "framework": "Framework and process",
        "legislation": "Legislation",
        "topics": "Topic guides",
        "research": "Research",
        "inventory": "Inventory",
        "website": "Website support",
        "participate": "Public participation",
        "sources": "Retained sources",
        "exports": "Exports",
    }
    return labels.get(parts[0], "Root project pages")


def markdown_body(content: str) -> str:
    if not content.startswith("---\n"):
        return content
    end = content.find("\n---\n", 4)
    return content[end + 5 :] if end >= 0 else content


def publication_document_type(relative: Path, metadata: dict[str, object]) -> str:
    if relative in {
        Path("README.md"),
        Path("ABOUT.md"),
        Path("PRINT_READERS_GUIDE.md"),
        Path("LICENSE.md"),
    }:
        return "front-matter"
    if relative == Path("SUBJECT_INDEX.md"):
        return "back-matter"
    parts = relative.parts
    if not parts:
        return "technical"
    if parts[0] == "topics":
        return "topic-guide"
    if parts[0] == "legislation":
        if relative.name == "README.md":
            return "legislation-index"
        return "state-legislation" if relative.stem.endswith("-state") else "federal-legislation"
    if parts[0] == "areas":
        if relative.name == "README.md":
            return "area-summary"
        if relative.name.endswith(".audit.md"):
            return "audit-history"
        if "evidence" in parts:
            return "evidence"
        if "research" in parts or metadata.get("record_type") == "source-development":
            return "research"
        if "issues" in parts:
            return "issue"
    if parts[0] == "research":
        return "research"
    return "technical"


def publication_sort_key(relative: Path, document_type: str, title: str) -> str:
    front_order = {
        "README.md": "000",
        "ABOUT.md": "010",
        "PRINT_READERS_GUIDE.md": "020",
        "LICENSE.md": "030",
    }
    if document_type == "front-matter":
        return front_order.get(relative.as_posix(), f"900-{title.casefold()}")
    if document_type == "back-matter":
        return "999-subject-index"
    if document_type == "topic-guide":
        return f"000-{title.casefold()}" if relative.name == "README.md" else f"100-{title.casefold()}"
    if document_type in {"area-summary", "issue", "audit-history", "evidence", "research"} and relative.parts[0] == "areas":
        area = relative.parts[1] if len(relative.parts) > 1 else ""
        category = {
            "area-summary": "000",
            "issue": "100",
            "evidence": "200",
            "research": "300",
            "audit-history": "400",
        }.get(document_type, "900")
        return f"{area}-{category}-{relative.stem.casefold()}"
    if document_type in {"federal-legislation", "state-legislation"}:
        stem = relative.stem
        base = re.match(r"([A-Z]+-\d{3})", stem)
        vehicle_order = (
            "000" if stem.endswith("-amendment") else
            "010" if stem.endswith("-preferred") else
            "030" if stem.endswith("-state") else "020"
        )
        return f"{base.group(1) if base else stem}-{vehicle_order}-{stem}"
    return f"{relative.parent.as_posix()}-{title.casefold()}"


def publication_page_metrics(content: str, words_per_page: int) -> dict[str, object]:
    body = markdown_body(content)
    text_only = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", body)
    text_only = re.sub(r"<[^>]+>", " ", text_only)
    text_only = re.sub(r"[`*_>#|~-]", " ", text_only)
    word_count = len(re.findall(r"\b[\w’'-]+\b", text_only))
    table_dividers = 0
    max_table_columns = 0
    for line in body.splitlines():
        if line.strip().startswith("|") and line.strip().endswith("|"):
            cells = markdown_table_cells(line)
            max_table_columns = max(max_table_columns, len(cells))
            if is_markdown_table_separator(line):
                table_dividers += 1
    heading_issues = 0
    prior_level = 0
    for match in re.finditer(r"^(#{1,6})\s+", body, re.MULTILINE):
        level = len(match.group(1))
        if (not prior_level and level > 1) or (prior_level and level > prior_level + 1):
            heading_issues += 1
        prior_level = level
    without_targets = re.sub(r"\]\([^)]+\)", "]", body)
    longest_token = max((len(token) for token in re.findall(r"\S+", without_targets)), default=0)
    return {
        "word_count": word_count,
        "estimated_pages": max(1, math.ceil(word_count / max(1, words_per_page))),
        "table_count": table_dividers,
        "max_table_columns": max_table_columns,
        "heading_issue_count": heading_issues,
        "longest_unbroken_token": longest_token,
    }


def internal_markdown_links(relative: Path, content: str) -> list[dict[str, object]]:
    links: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw_target in re.findall(r"\[[^]\n]+\]\(([^)\s]+)", content):
        target = html.unescape(raw_target).strip("<>")
        parsed = urllib.parse.urlsplit(target)
        if parsed.scheme or target.startswith("#"):
            continue
        path_part = urllib.parse.unquote(parsed.path)
        if not path_part or not path_part.lower().endswith(".md"):
            continue
        candidate = (ROOT / path_part.lstrip("/")) if path_part.startswith("/") else (ROOT / relative.parent / path_part)
        try:
            target_relative = candidate.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            continue
        if target_relative in seen:
            continue
        seen.add(target_relative)
        links.append({"path": target_relative, "exists": (ROOT / target_relative).exists()})
    return links


def publication_manifest() -> dict[str, object]:
    return json.loads(PRINT_ASSEMBLY_MANIFEST.read_text(encoding="utf-8"))


def default_assembly_sections(
    relative: Path, document_type: str, manifest: dict[str, object]
) -> dict[str, str]:
    placements: dict[str, str] = {}
    for edition in manifest.get("editions", []):
        if not isinstance(edition, dict):
            continue
        edition_id = str(edition.get("id", ""))
        overrides = edition.get("placement_overrides", {})
        if isinstance(overrides, dict) and relative.as_posix() in overrides:
            placements[edition_id] = str(overrides[relative.as_posix()])
            continue
        for section in edition.get("sections", []):
            if isinstance(section, dict) and document_type in section.get("accepts", []):
                placements[edition_id] = str(section.get("id", ""))
                break
    return placements


def page_inventory_records() -> list[dict[str, object]]:
    """Return every publication-controlled Markdown page and its disposition."""
    excluded_roots = {".git", ".site-build", ".tmp", ".venv"}
    local_only_roots = {Path("research/project-console/prototypes")}
    explicit_exceptions = {ROOT / "AGENTS.md", ROOT / "website" / "404.md"}
    records: list[dict[str, object]] = []
    manifest = publication_manifest()
    words_per_page = int(manifest.get("words_per_estimated_page", 650))
    for path in iter_project_files(ROOT, "*.md"):
        relative = path.relative_to(ROOT)
        if (
            excluded_roots.intersection(relative.parts)
            or any(relative.is_relative_to(root) for root in local_only_roots)
            or path in explicit_exceptions
        ):
            continue
        content = path.read_text(encoding="utf-8")
        metadata = markdown_front_matter(content)
        raw_levels = metadata.get("print_levels", [])
        levels = raw_levels if isinstance(raw_levels, list) else [str(raw_levels)]
        ordered_levels = [level for level in PRINT_LEVEL_ORDER if level in levels]
        ordered_levels.extend(sorted(set(levels) - set(ordered_levels)))
        print_status = str(metadata.get("print_status", "")).strip()
        exclusion_reason = str(metadata.get("print_exclusion_reason", "")).strip()
        if ordered_levels and print_status == "excluded":
            publication_disposition = "conflict"
        elif ordered_levels:
            publication_disposition = "included"
        elif print_status == "excluded":
            publication_disposition = "excluded"
        else:
            publication_disposition = "unclassified"
        relative_path = relative.as_posix()
        title = str(metadata.get("title") or markdown_title(path, content))
        document_type = publication_document_type(relative, metadata)
        records.append(
            {
                "title": title,
                "path": relative_path,
                "section": page_section(relative),
                "print_levels": ordered_levels,
                "print_level_labels": [
                    PRINT_LEVEL_LABELS.get(level, level.replace("-", " ").title())
                    for level in ordered_levels
                ],
                "print_status": print_status,
                "print_exclusion_reason": exclusion_reason,
                "publication_disposition": publication_disposition,
                "github_url": GITHUB_BLOB_ROOT + relative_path,
                "document_type": document_type,
                "print_metadata_present": "print_levels" in metadata or "print_status" in metadata,
                "invalid_print_levels": sorted(set(levels) - set(PRINT_LEVEL_ORDER)),
                "assembly_sections": default_assembly_sections(relative, document_type, manifest),
                "assembly_sort_key": publication_sort_key(relative, document_type, title),
                "internal_links": internal_markdown_links(relative, content),
                **publication_page_metrics(content, words_per_page),
            }
        )
    return sorted(records, key=lambda row: (str(row["section"]), str(row["title"])))


def pdf_page_count(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        result = subprocess.run(
            ["pdfinfo", str(path)], capture_output=True, text=True, check=True, timeout=20
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    return int(match.group(1)) if match else None


def topic_product_records() -> list[dict[str, object]]:
    """Project internal crosswalk and public Topic stages as one stable product."""
    index_path = ROOT / "research" / "README.md"
    content = index_path.read_text(encoding="utf-8")
    records: list[dict[str, object]] = []
    pattern = re.compile(
        r"^-\s+\[([^\]]+)\]\(([^)]+)\)\s+—\s+public topic home:\s+"
        r"\[([^\]]+)\]\((\.\./topics/[^)]+)\)\s*$",
        re.MULTILINE,
    )
    for match in pattern.finditer(content):
        internal_title, internal_target, public_title, public_target = match.groups()
        internal_path = (index_path.parent / internal_target).resolve()
        public_path = (index_path.parent / public_target).resolve()
        try:
            internal_relative = internal_path.relative_to(ROOT).as_posix()
            public_relative = public_path.relative_to(ROOT).as_posix()
        except ValueError as exc:
            raise RuntimeError("Topic-product route escapes the repository.") from exc
        product_key = Path(public_relative).stem
        records.append(
            {
                "product_id": "topic-product:" + product_key,
                "title": public_title,
                "is_issue": False,
                "issue_identifier": None,
                "current_stage": "published",
                "product_status": "published",
                "stages": [
                    {
                        "stage_id": "internal-crosswalk",
                        "label": internal_title,
                        "kind": "project_crosswalk",
                        "path": internal_relative,
                        "url": GITHUB_BLOB_ROOT + internal_relative,
                        "available": internal_path.is_file(),
                    },
                    {
                        "stage_id": "published-topic",
                        "label": public_title,
                        "kind": "topic_page",
                        "path": public_relative,
                        "url": GITHUB_BLOB_ROOT + public_relative,
                        "available": public_path.is_file(),
                    },
                ],
                "owner": None,
                "next_action": None,
                "validation_requirement": None,
                "completeness": {
                    "complete": internal_path.is_file() and public_path.is_file(),
                    "unavailable_fields": [
                        "owner",
                        "next_action",
                        "validation_requirement",
                    ],
                },
            }
        )
    converted = re.search(
        r"former Project 2025 research crosswalk has been converted, without "
        r"duplication, into the public \[([^\]]+)\]\((\.\./topics/[^)]+)\)",
        content,
        re.IGNORECASE,
    )
    if converted:
        public_title, public_target = converted.groups()
        public_path = (index_path.parent / public_target).resolve()
        public_relative = public_path.relative_to(ROOT).as_posix()
        records.append(
            {
                "product_id": "topic-product:" + Path(public_relative).stem,
                "title": public_title,
                "is_issue": False,
                "issue_identifier": None,
                "current_stage": "published",
                "product_status": "published",
                "stages": [
                    {
                        "stage_id": "internal-crosswalk",
                        "label": "Former Project 2025 research crosswalk",
                        "kind": "converted_internal_crosswalk",
                        "path": None,
                        "url": None,
                        "available": False,
                        "disposition": "converted_without_duplication",
                    },
                    {
                        "stage_id": "published-topic",
                        "label": public_title,
                        "kind": "topic_page",
                        "path": public_relative,
                        "url": GITHUB_BLOB_ROOT + public_relative,
                        "available": public_path.is_file(),
                    },
                ],
                "owner": None,
                "next_action": None,
                "validation_requirement": None,
                "completeness": {
                    "complete": public_path.is_file(),
                    "unavailable_fields": [
                        "owner",
                        "next_action",
                        "validation_requirement",
                    ],
                },
            }
        )
    return sorted(records, key=lambda record: str(record["product_id"]))


def repository_revision_for_path(path: Path) -> str | None:
    if not path.exists():
        return None
    completed = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", path.relative_to(ROOT).as_posix()],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    revision = completed.stdout.strip()
    return revision if completed.returncode == 0 and revision else None


def repository_revision_timestamp(root: Path, revision: str) -> str:
    """Return the immutable commit timestamp for a generated revision."""

    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise RuntimeError("Console source revision is not an exact Git object ID.")
    completed = subprocess.run(
        ["git", "-C", str(root), "show", "-s", "--format=%cI", revision],
        check=False,
        capture_output=True,
        text=True,
    )
    value = completed.stdout.strip()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError(
            "Console source revision lacks an exact commit timestamp."
        ) from exc
    if completed.returncode != 0 or parsed.tzinfo is None:
        raise RuntimeError("Console source revision timestamp is unavailable.")
    return parsed.isoformat(timespec="seconds")


def publication_release_readiness(
    page_inventory: list[dict[str, object]],
    builds: list[dict[str, object]],
    progress: dict[str, object] | None = None,
    integrity: dict[str, object] | None = None,
) -> dict[str, object]:
    """Project known release prerequisites without inferring approval or readiness."""
    progress_payload = progress if isinstance(progress, dict) else {}
    progress_available = bool(
        progress_payload
        and isinstance(progress_payload.get("proposals"), list)
        and isinstance(progress_payload.get("candidates"), list)
    )
    progress_contract_available = isinstance(
        progress_payload.get("completeness"), dict
    )
    progress_complete = (
        (progress_payload.get("completeness") or {}).get("complete") is True
        if progress_contract_available
        else False
    )
    delivery_available = isinstance(progress_payload.get("delivery_items"), list)
    delivery_items = (
        progress_payload.get("delivery_items")
        if isinstance(progress_payload.get("delivery_items"), list)
        else []
    )
    project_items = [
        item
        for collection in (
            progress_payload.get("proposals") or [],
            progress_payload.get("candidates") or [],
            delivery_items,
        )
        for item in collection
        if isinstance(item, dict)
    ]
    issue_development_items = [
        item
        for collection in (
            progress_payload.get("proposals") or [],
            progress_payload.get("candidates") or [],
        )
        for item in collection
        if isinstance(item, dict)
    ]
    release_fields_available = progress_available and all(
        ("releaseBlocker" in item or "release_blocker" in item)
        for item in project_items
    )
    audit_status_available = progress_available and all(
        "workflowStatus" in item for item in issue_development_items
    )
    audit_control_fields_complete = audit_status_available and all(
        "changeAuditNeeded" in item and "rebaselineStatus" in item
        for item in issue_development_items
    )

    def identity(item: dict[str, object]) -> dict[str, object]:
        return {
            "identifier": item.get("identifier"),
            "title": item.get("title"),
            "url": item.get("url"),
            "project_item_id": item.get("projectItemId"),
            "workstream": item.get("workstream"),
            "priority": item.get("priority"),
            "status": item.get("workflowStatus"),
        }

    blockers = [
        {
            **identity(item),
            "release_blocker": item.get("releaseBlocker")
            or item.get("release_blocker"),
        }
        for item in project_items
        if normalize_console_owner(
            item.get("releaseBlocker") or item.get("release_blocker")
        )
        in {"yes", "true"}
    ]
    audit_items: list[dict[str, object]] = []
    for item in project_items:
        reasons: list[str] = []
        status = normalize_console_owner(item.get("workflowStatus"))
        if status in {"audit needed", "audit in progress"}:
            reasons.append(str(item.get("workflowStatus")))
        if normalize_console_owner(item.get("changeAuditNeeded")) in {"yes", "true"}:
            reasons.append("Change audit needed")
        rebaseline = normalize_console_owner(item.get("rebaselineStatus"))
        if rebaseline and rebaseline not in {"current", "not applicable", "n/a"}:
            reasons.append(
                "Rebaseline status: " + str(item.get("rebaselineStatus"))
            )
        if reasons:
            audit_items.append(
                {
                    **identity(item),
                    "reasons": reasons,
                    "last_audit": item.get("lastAudit"),
                    "next_audit": item.get("nextAudit"),
                }
            )
    external_review_items = [
        {
            **identity(item),
            "last_audit": item.get("lastAudit"),
            "next_audit": item.get("nextAudit"),
        }
        for item in project_items
        if normalize_console_owner(item.get("workflowStatus")) == "external review"
    ]

    by_path = {
        str(record.get("path") or ""): record
        for record in page_inventory
        if str(record.get("path") or "")
    }
    missing_links: list[dict[str, object]] = []
    cross_edition: list[dict[str, object]] = []
    seen_cross: set[tuple[str, str, str]] = set()
    internal_link_count = 0
    for source in page_inventory:
        source_path = str(source.get("path") or "")
        source_levels = {
            str(level) for level in source.get("print_levels") or []
        }
        for link in source.get("internal_links") or []:
            if not isinstance(link, dict):
                continue
            internal_link_count += 1
            target_path = str(link.get("path") or "")
            if link.get("exists") is not True:
                missing_links.append(
                    {"source": source_path, "target": target_path}
                )
                continue
            target = by_path.get(target_path)
            if target is None:
                continue
            target_levels = {
                str(level) for level in target.get("print_levels") or []
            }
            for edition in sorted(source_levels - target_levels):
                key = (source_path, target_path, edition)
                if key in seen_cross:
                    continue
                seen_cross.add(key)
                cross_edition.append(
                    {
                        "source": source_path,
                        "target": target_path,
                        "source_edition": edition,
                        "target_disposition": target.get(
                            "publication_disposition"
                        ),
                        "review_disposition": None,
                    }
                )

    public_build = next(
        (
            build
            for build in builds
            if build.get("edition_id") == "public-proposal"
        ),
        None,
    )
    artifact_hash = (
        file_sha256(ROOT, PUBLIC_PROPOSAL_PDF)
        if PUBLIC_PROPOSAL_PDF.is_file()
        else None
    )
    license_text = (
        (ROOT / "LICENSE.md").read_text(encoding="utf-8")
        if (ROOT / "LICENSE.md").is_file()
        else ""
    )
    all_rights_reserved = bool(
        re.search(r"\ball rights reserved\b", license_text, re.IGNORECASE)
    )
    planned_later_license = bool(
        re.search(
            r"planned to be released at a later date.+(?:Creative Commons|reuse license)",
            license_text,
            re.IGNORECASE | re.DOTALL,
        )
    )
    integrity_payload = integrity if isinstance(integrity, dict) else {}
    integrity_current = (
        integrity_payload.get("current")
        if isinstance(integrity_payload.get("current"), dict)
        else {}
    )
    disposition_counts = {
        disposition: sum(
            1
            for record in page_inventory
            if record.get("publication_disposition") == disposition
        )
        for disposition in ("included", "excluded", "unclassified", "conflict")
    }
    assembly_valid = (
        disposition_counts["unclassified"] == 0
        and disposition_counts["conflict"] == 0
    )
    return {
        "status": "not_determined",
        "status_explanation": (
            "Structural assembly facts are available, but release readiness "
            "cannot be declared without lineage-backed export validation, "
            "completed prerequisites, and a recorded human go/no-go decision."
        ),
        "assembly": {
            "status": "valid" if assembly_valid else "action_required",
            "label": (
                "Assembly structurally valid"
                if assembly_valid
                else "Assembly structure requires correction"
            ),
            "disposition_counts": disposition_counts,
        },
        "delivery_tasks": {
            "available": delivery_available,
            "source_complete": progress_complete,
            "count": len(delivery_items) if delivery_available else None,
            "incomplete_metadata_count": (
                sum(
                    1
                    for item in delivery_items
                    if not (item.get("completeness") or {}).get("complete")
                )
                if delivery_available
                else None
            ),
            "items": [identity(item) for item in delivery_items]
            if delivery_available
            else [],
            "unavailable_reason": (
                None
                if delivery_available
                else "Authenticated Project delivery items are unavailable."
            ),
        },
        "release_blockers": {
            "available": release_fields_available,
            "source_complete": progress_complete,
            "count": len(blockers) if release_fields_available else None,
            "items": blockers if release_fields_available else [],
            "unavailable_reason": (
                None
                if release_fields_available
                else "Project Release blocker fields are absent from this projection."
            ),
        },
        "required_audits": {
            "available": audit_status_available,
            "source_complete": progress_complete,
            "control_fields_complete": audit_control_fields_complete,
            "count": len(audit_items)
            if audit_control_fields_complete
            else None,
            "known_count": len(audit_items) if audit_status_available else None,
            "items": audit_items,
            "unavailable_reason": (
                None
                if audit_control_fields_complete
                else "Change-audit and rebaseline controls are incomplete in this projection."
            ),
        },
        "external_review": {
            "available": progress_available,
            "source_complete": progress_complete,
            "count": len(external_review_items)
            if progress_available
            else None,
            "items": external_review_items,
            "completion_requirement": (
                "The Project records current External review workflow state; "
                "it does not itself prove that required external review is complete."
            ),
        },
        "link_export_validation": {
            "link_inventory_available": True,
            "internal_link_count": internal_link_count,
            "missing_link_count": len(missing_links),
            "missing_links": missing_links,
            "export_validation_available": False,
            "export_validation_status": "unavailable",
            "unavailable_reason": (
                "No lineage-bearing export validation manifest is recorded."
            ),
        },
        "export_lineage": {
            "available": False,
            "artifact_path": (
                PUBLIC_PROPOSAL_PDF.relative_to(ROOT).as_posix()
                if PUBLIC_PROPOSAL_PDF.is_file()
                else None
            ),
            "artifact_sha256": artifact_hash,
            "artifact_repository_revision": repository_revision_for_path(
                PUBLIC_PROPOSAL_PDF
            ),
            "build_source_revision": None,
            "input_hashes": None,
            "unavailable_reason": (
                "The existing PDF has no recorded build source revision and "
                "complete input-hash manifest."
            ),
        },
        "stale_pdf": {
            "revision_backed_status": "unavailable",
            "mtime_indicator": (
                public_build.get("stale") if isinstance(public_build, dict) else None
            ),
            "mtime_indicator_only": True,
            "explanation": (
                "Filesystem modification time is retained as a diagnostic only; "
                "it cannot establish current export lineage."
            ),
        },
        "cross_edition_references": {
            "available": True,
            "count": len(cross_edition),
            "items": cross_edition,
            "disposition_complete": not cross_edition,
            "explanation": (
                "A cross-edition or online-only target requires an explicit "
                "reader-route disposition; presence alone is not a broken link."
            ),
        },
        "copyright_reuse": {
            "rights_notice_available": bool(license_text),
            "all_rights_reserved": all_rights_reserved
            if license_text
            else None,
            "later_public_reuse_license_planned": planned_later_license
            if license_text
            else None,
            "public_reuse_license_adopted": False
            if all_rights_reserved and planned_later_license
            else None,
            "third_party_reuse_review": "unavailable",
            "status": (
                "human_decision_required"
                if all_rights_reserved and planned_later_license
                else "unavailable"
            ),
        },
        "integrity_validation": {
            "available": bool(integrity_current),
            "result": integrity_current.get("result"),
            "counts": integrity_current.get("counts") or {},
            "revision": integrity_current.get("revision"),
            "generated_at": integrity_current.get("generated_at"),
        },
        "human_go_no_go": {
            "available": False,
            "decision": None,
            "status": "human_decision_required",
            "question": (
                "After all release prerequisites and lineage-backed validation "
                "are complete, authorize this exact revision for public release?"
            ),
            "authority": "Human only",
        },
    }


def publication_data(page_inventory: list[dict[str, object]]) -> dict[str, object]:
    manifest = publication_manifest()
    builds: list[dict[str, object]] = []
    if PUBLIC_PROPOSAL_PDF.exists():
        modified = PUBLIC_PROPOSAL_PDF.stat().st_mtime
        assigned_paths = [
            ROOT / str(record["path"])
            for record in page_inventory
            if "public-proposal" in record.get("print_levels", [])
        ]
        latest_source = max((path.stat().st_mtime for path in assigned_paths if path.exists()), default=0)
        builds.append(
            {
                "edition_id": "public-proposal",
                "label": "Existing public-proposal draft PDF",
                "path": PUBLIC_PROPOSAL_PDF.relative_to(ROOT).as_posix(),
                "github_url": GITHUB_BLOB_ROOT + PUBLIC_PROPOSAL_PDF.relative_to(ROOT).as_posix(),
                "page_count": pdf_page_count(PUBLIC_PROPOSAL_PDF),
                "modified_at": datetime.fromtimestamp(modified, timezone.utc).isoformat(timespec="seconds"),
                "stale": latest_source > modified,
            }
        )
    disposition_counts = {
        disposition: sum(
            1 for record in page_inventory
            if record.get("publication_disposition") == disposition
        )
        for disposition in ("included", "excluded", "unclassified", "conflict")
    }
    exclusion_reasons: dict[str, int] = {}
    for record in page_inventory:
        if record.get("publication_disposition") != "excluded":
            continue
        reason = str(record.get("print_exclusion_reason") or "Reason not recorded")
        exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
    return {
        "manifest": manifest,
        "builds": builds,
        "disposition_counts": disposition_counts,
        "exclusion_reasons": exclusion_reasons,
        "topic_products": topic_product_records(),
        "release_readiness": publication_release_readiness(
            page_inventory,
            builds,
        ),
    }


def associated_record_ids(raw: str) -> set[str]:
    return {
        item.strip()
        for item in re.split(r"[;,]", raw)
        if item.strip()
    }


def sources_for_record(record_id: str) -> list[dict[str, str]]:
    matches = [
        source_payload(row)
        for row in all_source_records()
        if record_id in associated_record_ids(row["Associated Record IDs"])
    ]
    return sorted(matches, key=lambda row: row["id"])


def strip_markdown(value: str) -> str:
    value = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("`", "")
    return re.sub(r"\s+", " ", value).strip()


ISSUE_PAGE_PATTERN = re.compile(
    r"^areas/(?P<area>[A-Z0-9-]+)/issues/(?P<issue_id>[A-Z0-9-]+)\.md$"
)
AUDIT_ENTRY_PATTERN = re.compile(
    r"(?m)^###\s+(?P<date>20\d{2}-\d{2}-\d{2})\s+[—-]\s+(?P<title>.+?)\s*$"
)
SCORE_EFFECT_LINE_PATTERN = re.compile(
    r"(?im)^\*\*Score[^*\n]*:\*\*\s*(?P<effect>[^\n]+)$"
)
SCORE_TRANSITION_PATTERN = re.compile(
    r"(?i)\b(?:increase[sd]?|decrease[sd]?|change[sd]?|move[sd]?|advance[sd]?|rise[sd]?)\s+from\s+"
    r"(?P<old>[0-9]{1,3})\s+to\s+(?P<new>[0-9]{1,3})\b"
)


def active_issue_score_activity(
    progress: dict[str, object],
    *,
    repository_root: Path = ROOT,
    limit: int = 8,
) -> list[dict[str, object]]:
    """Project latest score-changing audit entries for current issue pages.

    The Project issue-development registry determines membership.  Exact issue
    pages and their declared sibling audit histories supply the displayed
    change summary and score transition; general project logs are not an
    activity fallback.
    """
    proposals = progress.get("proposals")
    if not isinstance(proposals, list):
        return []
    root = repository_root.resolve()
    activity: list[dict[str, object]] = []
    for record in proposals:
        if not isinstance(record, dict) or record.get("isIssueDevelopment") is not True:
            continue
        if str(record.get("state") or "").upper() not in {"", "OPEN"}:
            continue
        identifier = str(record.get("identifier") or "").strip()
        canonical_record = str(record.get("canonicalRecord") or "").strip()
        match = ISSUE_PAGE_PATTERN.fullmatch(canonical_record)
        if not match or match.group("issue_id") != identifier:
            continue
        issue_path = (root / canonical_record).resolve()
        try:
            issue_path.relative_to(root)
        except ValueError:
            continue
        audit_path = issue_path.with_name(f"{identifier}.audit.md")
        if not issue_path.is_file() or not audit_path.is_file():
            continue
        try:
            current_score = float(record.get("score"))
        except (TypeError, ValueError):
            continue
        audit_text = audit_path.read_text(encoding="utf-8")
        entries = list(AUDIT_ENTRY_PATTERN.finditer(audit_text))
        latest_change: dict[str, object] | None = None
        for index, entry in enumerate(entries):
            end = entries[index + 1].start() if index + 1 < len(entries) else len(audit_text)
            body = audit_text[entry.end():end]
            transition = next(
                (
                    candidate
                    for effect_line in SCORE_EFFECT_LINE_PATTERN.finditer(body)
                    if (
                        candidate := SCORE_TRANSITION_PATTERN.search(
                            effect_line.group("effect")
                        )
                    )
                ),
                None,
            )
            if not transition:
                continue
            old_score = int(transition.group("old"))
            new_score = int(transition.group("new"))
            if not math.isclose(float(new_score), current_score):
                continue
            display_title = re.sub(
                rf"^{re.escape(identifier)}\s*[:—-]\s*",
                "",
                str(record.get("title") or identifier).strip(),
            )
            latest_change = {
                "event_id": f"{identifier}-score-{entry.group('date')}",
                "occurred_at": entry.group("date"),
                "event_code": "active_issue_score_changed",
                "artifact_label": f"{identifier} · {display_title}",
                "artifact_ids": [identifier],
                "change_descriptor": strip_markdown(entry.group("title")),
                "score_change": f"{old_score} → {new_score}",
                "old_score": old_score,
                "new_score": new_score,
                "owner": record.get("owner"),
                "affected_count": 1,
                "route": f"{GITHUB_BLOB_ROOT}{canonical_record}",
                "producer": "Issue audit history",
                "source_record_id": audit_path.relative_to(root).as_posix(),
                "canonical_record": canonical_record,
            }
            break
        if latest_change:
            activity.append(latest_change)
    activity.sort(
        key=lambda item: (
            str(item.get("occurred_at") or ""),
            str(item.get("artifact_label") or ""),
        ),
        reverse=True,
    )
    return activity[:limit]


SAFE_LINK_SCHEMES = {"http", "https", "mailto"}


def safe_markdown_url(raw_url: str) -> str | None:
    """Return a safe Markdown-link target or None for unsafe protocols."""
    value = html.unescape(raw_url.strip())
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme:
        return value if parsed.scheme.casefold() in SAFE_LINK_SCHEMES else None
    if value.startswith(("#", "/", "./", "../")):
        return value
    return None


def render_markdown_inline(value: str) -> str:
    """Render a deliberately small, escaped GitHub-style inline Markdown subset."""
    replacements: list[str] = []

    def preserve(rendered: str) -> str:
        token = f"\x00{len(replacements)}\x00"
        replacements.append(rendered)
        return token

    def link_replacement(match: re.Match[str]) -> str:
        label = render_markdown_inline(match.group(1))
        target = safe_markdown_url(match.group(2))
        if not target:
            return preserve(label)
        return preserve(
            f'<a href="{html.escape(target, quote=True)}" target="_blank" '
            f'rel="noopener noreferrer">{label}</a>'
        )

    # Resolve links before protecting standalone code spans so code-formatted
    # link labels are rendered recursively without sharing placeholder tokens
    # with the outer inline pass.
    protected = re.sub(r"\[([^]\n]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", link_replacement, value)

    def code_replacement(match: re.Match[str]) -> str:
        return preserve(f"<code>{html.escape(match.group(1))}</code>")

    protected = re.sub(r"`([^`\n]+)`", code_replacement, protected)
    rendered = html.escape(protected)
    rendered = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"__([^_\n]+)__", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", rendered)
    rendered = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"<em>\1</em>", rendered)
    rendered = re.sub(r"~~([^~\n]+)~~", r"<del>\1</del>", rendered)
    for index, replacement in enumerate(replacements):
        rendered = rendered.replace(f"\x00{index}\x00", replacement)
    return rendered


def markdown_table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def markdown_table_records(
    content: str,
    required_headers: tuple[str, ...],
    projection_errors: list[dict[str, object]] | None = None,
    source: str = "",
) -> list[dict[str, str]]:
    """Return rows from the first Markdown table matching the requested headers."""
    lines = content.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    encountered_headers: list[list[str]] = []
    for index in range(len(lines) - 1):
        if "|" not in lines[index] or not is_markdown_table_separator(lines[index + 1]):
            continue
        headers = markdown_table_cells(lines[index])
        encountered_headers.append(headers)
        if tuple(headers) != required_headers:
            continue
        rows: list[dict[str, str]] = []
        index += 2
        while index < len(lines) and lines[index].strip() and "|" in lines[index]:
            cells = markdown_table_cells(lines[index])
            if len(cells) != len(headers):
                if projection_errors is not None:
                    projection_errors.append(
                        {
                            "code": "markdown_table_row_width",
                            "severity": "error",
                            "source": source,
                            "line": index + 1,
                            "expected_columns": len(headers),
                            "actual_columns": len(cells),
                            "message": "Markdown log row width does not match its governed header.",
                        }
                    )
                index += 1
                continue
            rows.append(dict(zip(headers, cells)))
            index += 1
        return rows
    if projection_errors is not None:
        projection_errors.append(
            {
                "code": (
                    "markdown_table_header_drift"
                    if encountered_headers
                    else "markdown_table_missing"
                ),
                "severity": "error",
                "source": source,
                "expected_headers": list(required_headers),
                "encountered_headers": encountered_headers,
                "message": "Governed Markdown log table was not found with its exact schema.",
            }
        )
    return []


def log_entry(
    entry_id: str,
    values: dict[str, str],
    raw_values: dict[str, str],
    details_markdown: str,
) -> dict[str, object]:
    return {
        "id": entry_id,
        "values": values,
        "values_html": {
            key: render_markdown_inline(raw_values.get(key, value))
            for key, value in values.items()
        },
        "details_html": render_markdown_safe(details_markdown),
        "search_text": " ".join(
            [entry_id, *values.values(), *(strip_markdown(value) for value in raw_values.values())]
        ),
    }


def horizon_disposition(decision: str) -> str:
    value = strip_markdown(decision).casefold()
    if "deferred" in value or "monitor" in value:
        return "Deferred or monitoring"
    if any(term in value for term in ("rejected", "retired", "outside scope")):
        return "Rejected or retired"
    if any(term in value for term in ("merged", "integrated", "folded")):
        return "Integrated or merged"
    if any(term in value for term in ("admitted", "promoted")):
        return "Admitted or promoted"
    return "Other disposition"


def horizon_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    headers = (
        "Horizon ID", "Decision date", "Original concern", "Decision",
        "Integrated into", "Rationale", "Follow-up",
    )
    entries: list[dict[str, object]] = []
    rows = markdown_table_records(
        HORIZON_LOG.read_text(encoding="utf-8"),
        headers,
        projection_errors,
        HORIZON_LOG.relative_to(ROOT).as_posix(),
    )
    for row in rows:
        disposition = horizon_disposition(row["Decision"])
        values = {
            "record": strip_markdown(row["Horizon ID"]),
            "date": strip_markdown(row["Decision date"]),
            "disposition": disposition,
            "destination": strip_markdown(row["Integrated into"]),
        }
        details = "\n".join(
            f"- **{label}:** {row[label]}" for label in headers[2:]
        )
        entries.append(log_entry(values["record"], values, {
            "record": row["Horizon ID"],
            "date": row["Decision date"],
            "disposition": disposition,
            "destination": row["Integrated into"],
        }, details))
    return {
        "id": "horizon",
        "title": "Horizon Scan Log",
        "description": "Candidate intake, disposition, integration, and follow-up history.",
        "source_url": GITHUB_BLOB_ROOT + "framework/logs/candidates/candidate-discovery-log.md",
        "columns": [
            {"key": "record", "label": "Record"},
            {"key": "date", "label": "Decision date"},
            {"key": "disposition", "label": "Disposition"},
            {"key": "destination", "label": "Current route"},
        ],
        "group_options": [
            {"key": "disposition", "label": "Disposition"},
            {"key": "date", "label": "Decision date"},
        ],
        "default_sort": {"key": "record", "direction": "desc"},
        "projection": {
            "expected_rows": len(rows),
            "actual_rows": len(entries),
            "complete": len(rows) == len(entries),
        },
        "entries": entries,
    }


def change_audit_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    headers = (
        "Date", "Change audited", "Scope", "Score/rebaseline effect",
        "Findings and corrections",
    )
    entries: list[dict[str, object]] = []
    rows = markdown_table_records(
        CHANGE_AUDIT_LOG.read_text(encoding="utf-8"),
        headers,
        projection_errors,
        CHANGE_AUDIT_LOG.relative_to(ROOT).as_posix(),
    )
    for index, row in enumerate(rows, 1):
        values = {
            "date": strip_markdown(row["Date"]),
            "change": strip_markdown(row["Change audited"]),
            "scope": strip_markdown(row["Scope"]),
            "effect": strip_markdown(row["Score/rebaseline effect"]),
        }
        details = "\n".join(
            f"- **{label}:** {row[label]}" for label in headers[1:]
        )
        entries.append(log_entry(f"change-{index:03d}", values, {
            "date": row["Date"],
            "change": row["Change audited"],
            "scope": row["Scope"],
            "effect": row["Score/rebaseline effect"],
        }, details))
    return {
        "id": "changes",
        "title": "Change Audit Log",
        "description": "Retained project-wide methodology, structure, and consistency changes.",
        "source_url": GITHUB_BLOB_ROOT + "framework/logs/audits/change-audit-log.md",
        "columns": [
            {"key": "date", "label": "Date"},
            {"key": "change", "label": "Change audited"},
            {"key": "scope", "label": "Scope"},
            {"key": "effect", "label": "Score or rebaseline effect"},
        ],
        "group_options": [{"key": "date", "label": "Date"}],
        "default_sort": {"key": "date", "direction": "desc"},
        "projection": {
            "expected_rows": len(rows),
            "actual_rows": len(entries),
            "complete": len(rows) == len(entries),
        },
        "entries": entries,
    }


def governance_change_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Project the registry-bound public Governance Change Log."""

    try:
        changes = parse_public_changes(
            GOVERNANCE_CHANGE_LOG,
            GOVERNANCE_CHANGE_REGISTRY,
        )
    except GovernanceChangeError as error:
        if projection_errors is not None:
            projection_errors.append(
                {
                    "code": "governance_change_log_contract",
                    "severity": "error",
                    "source": GOVERNANCE_CHANGE_LOG.relative_to(ROOT).as_posix(),
                    "message": str(error),
                }
            )
        changes = {}

    entries: list[dict[str, object]] = []
    for change in changes.values():
        supplement = (
            "Required"
            if change.private_supplement_required
            else "Not required"
        )
        values = {
            "governance_change_id": change.id,
            "entry_sha256": change.entry_sha256,
            "date": change.date,
            "status": change.status,
            "decision_class": change.decision_class,
            "policy_adoption": change.policy_adoption,
            "live_activation": change.live_activation,
            "supplement": supplement,
        }
        details = "\n".join(
            (
                f"## {change.id} — {change.title}",
                "",
                f"- **Decision class:** {change.decision_class}",
                f"- **Authorities:** {'; '.join(change.authorities)}",
                f"- **Decision:** {change.decision}",
                f"- **Evidence:** {change.evidence}",
                f"- **Policy adoption:** {change.policy_adoption}",
                f"- **Live activation:** {change.live_activation}",
                f"- **Relationships:** {change.relationships}",
                f"- **Validation:** {change.validation}",
                f"- **Owner-local supplement:** {supplement}.",
            )
        )
        entries.append(
            log_entry(
                change.id,
                values,
                {
                    "governance_change_id": change.id,
                    "entry_sha256": change.entry_sha256,
                    "date": change.date,
                    "status": change.status,
                    "decision_class": change.decision_class,
                    "policy_adoption": change.policy_adoption,
                    "live_activation": change.live_activation,
                    "supplement": supplement,
                },
                details,
            )
        )
        entries[-1]["title"] = change.title

    return {
        "id": "governance-changes",
        "title": "Governance Change Log",
        "description": (
            "Public-safe provenance for material project-governance decisions."
        ),
        "source_url": (
            GITHUB_BLOB_ROOT
            + "framework/logs/governance/governance-change-log.md"
        ),
        "columns": [
            {"key": "date", "label": "Decision date"},
            {"key": "decision_class", "label": "Decision class"},
            {"key": "status", "label": "Status"},
            {"key": "policy_adoption", "label": "Policy adoption"},
            {"key": "live_activation", "label": "Live activation"},
            {"key": "supplement", "label": "Protected supplement"},
        ],
        "group_options": [
            {"key": "decision_class", "label": "Decision class"},
            {"key": "status", "label": "Status"},
            {"key": "date", "label": "Decision date"},
        ],
        "default_sort": {"key": "governance_change_id", "direction": "desc"},
        "projection": {
            "expected_rows": len(changes),
            "actual_rows": len(entries),
            "complete": len(changes) == len(entries),
        },
        "entries": entries,
    }


def console_development_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    required_umbrella_fields = (
        "Console Change IDs",
        "Title",
        "Lifecycle",
        "Feature or component",
        "State",
        "Implementation commits",
        "Rollback baseline",
    )
    entries: list[dict[str, object]] = []
    content = CONSOLE_DEVELOPMENT_LOG.read_text(encoding="utf-8")
    records: list[tuple[str, str]] = []
    for title, body in section_records(content, 2):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", strip_markdown(title)):
            records.append((title, body))

    categories_by_label = {
        str(category["label"]): str(category["id"])
        for category in console_development_category_registry()
    }
    expected_rows = 0
    for title, body in records:
        recorded_date = strip_markdown(title)
        umbrella_fields = bullet_fields(body)
        umbrella_change_ids = re.findall(
            r"CONSOLE-\d{4}-\d{3}",
            str(umbrella_fields.get("Console Change IDs") or ""),
        )
        missing = [
            field for field in required_umbrella_fields
            if not str(umbrella_fields.get(field) or "").strip()
        ]
        category_sections = section_records(body, 3)
        expected_rows += len(category_sections)
        if (missing or not umbrella_change_ids) and projection_errors is not None:
            projection_errors.append(
                {
                    "code": "console_development_entry_schema",
                    "severity": "error",
                    "source": CONSOLE_DEVELOPMENT_LOG.relative_to(ROOT).as_posix(),
                    "heading": strip_markdown(title),
                    "missing_fields": missing,
                    "missing_change_id": not umbrella_change_ids,
                    "message": (
                        "Console Development umbrella is missing governed fields "
                        "or a registered Change ID."
                    ),
                }
            )
        if missing or not umbrella_change_ids:
            continue
        change_title = strip_markdown(umbrella_fields["Title"])
        for category_label, category_body in category_sections:
            category_id = categories_by_label.get(strip_markdown(category_label))
            category_fields = bullet_fields(category_body)
            category_change_ids = re.findall(
                r"CONSOLE-\d{4}-\d{3}",
                str(category_fields.get("Change ID") or ""),
            )
            missing_category_fields = [
                field
                for field in (
                    "Category ID",
                    "Change ID",
                    "Commit IDs",
                    "Material change",
                    "Validation",
                )
                if not str(category_fields.get(field) or "").strip()
            ]
            category_valid = (
                category_id is not None
                and strip_markdown(category_fields.get("Category ID", ""))
                == category_id
                and bool(category_change_ids)
                and set(category_change_ids) <= set(umbrella_change_ids)
                and not missing_category_fields
            )
            if not category_valid:
                if projection_errors is not None:
                    projection_errors.append(
                        {
                            "code": "console_development_category_schema",
                            "severity": "error",
                            "source": (
                                CONSOLE_DEVELOPMENT_LOG.relative_to(ROOT).as_posix()
                            ),
                            "heading": strip_markdown(category_label),
                            "date": recorded_date,
                            "missing_fields": missing_category_fields,
                            "message": (
                                "Console Development category is unregistered, "
                                "incomplete, or not bound to its dated umbrella."
                            ),
                        }
                    )
                continue
            entry_id = (
                f"console-development-{recorded_date}-{category_id}"
            )
            values = {
                "date": recorded_date,
                "category": strip_markdown(category_label),
                "change": ", ".join(category_change_ids),
                "lifecycle": strip_markdown(umbrella_fields["Lifecycle"]),
                "state": strip_markdown(umbrella_fields["State"]),
                "commit": strip_markdown(category_fields["Commit IDs"]),
                "title": change_title,
            }
            entries.append(
                log_entry(
                    entry_id,
                    values,
                    {
                        "date": recorded_date,
                        "category": category_label,
                        "change": category_fields["Change ID"],
                        "lifecycle": umbrella_fields["Lifecycle"],
                        "state": umbrella_fields["State"],
                        "commit": category_fields["Commit IDs"],
                        "title": umbrella_fields["Title"],
                    },
                    (
                        f"## {recorded_date} — {category_label}\n\n"
                        f"**{umbrella_fields['Title']}**\n\n"
                        f"{category_body}"
                    ),
                )
            )
    return {
        "id": "console-development",
        "title": "Console Development Log",
        "description": "Material Project Console feature and contract history.",
        "source_url": GITHUB_BLOB_ROOT
        + "framework/logs/automation/console-development-log.md",
        "columns": [
            {"key": "date", "label": "Recorded"},
            {"key": "category", "label": "Category"},
            {"key": "change", "label": "Change ID"},
            {"key": "lifecycle", "label": "Lifecycle"},
            {"key": "state", "label": "State"},
            {"key": "commit", "label": "Category commits"},
        ],
        "group_options": [
            {"key": "category", "label": "Category"},
            {"key": "lifecycle", "label": "Lifecycle"},
            {"key": "state", "label": "State"},
        ],
        "default_sort": {"key": "date", "direction": "desc"},
        "projection": {
            "expected_rows": expected_rows,
            "actual_rows": len(entries),
            "complete": expected_rows == len(entries),
        },
        "entries": entries,
    }


def section_records(content: str, heading_level: int, start_heading: str = "") -> list[tuple[str, str]]:
    """Split Markdown into titled sections, optionally beginning after an exact heading."""
    if start_heading:
        match = re.search(rf"^{re.escape(start_heading)}\s*$", content, re.MULTILINE)
        content = content[match.end():] if match else ""
    marker = "#" * heading_level
    matches = list(re.finditer(rf"^{re.escape(marker)}\s+(.+?)\s*$", content, re.MULTILINE))
    return [
        (match.group(1).strip(), content[match.end(): matches[index + 1].start() if index + 1 < len(matches) else len(content)].strip())
        for index, match in enumerate(matches)
    ]


def two_column_fields(
    content: str,
    projection_errors: list[dict[str, object]] | None = None,
    source: str = "",
) -> dict[str, str]:
    rows = markdown_table_records(
        content,
        ("Field", "Entry"),
        projection_errors,
        source,
    )
    return {strip_markdown(row["Field"]): row["Entry"] for row in rows}


OWNER_LOG_PUBLIC_SCHEMAS = {
    "agents": {
        "columns": (
            ("date", "Date and time"),
            ("record", "Issue or task"),
            ("task", "Task type"),
            ("agent", "Agent"),
            ("run", "Run ID"),
            ("outcome", "Outcome"),
        ),
        "group_options": (
            ("task", "Task type"),
            ("record", "Issue or task"),
            ("agent", "Agent"),
            ("run", "Run ID"),
            ("outcome", "Outcome"),
        ),
    },
    "elim": {
        "columns": (
            ("date", "Started"),
            ("outcome", "Outcome"),
            ("trigger", "Trigger"),
            ("summary", "Work summary"),
            ("usage", "Usage"),
            ("next", "Exact next action"),
        ),
        "group_options": (
            ("outcome", "Outcome"),
            ("trigger", "Trigger"),
        ),
    },
}


def owner_log_public_schema(log_id: str) -> dict[str, object]:
    """Return one immutable public-safe presentation schema without file I/O."""

    schema = OWNER_LOG_PUBLIC_SCHEMAS.get(log_id)
    if schema is None:
        raise RuntimeError(f"Unknown owner-log schema: {log_id}")
    return {
        "columns": [
            {"key": key, "label": label}
            for key, label in schema["columns"]
        ],
        "group_options": [
            {"key": key, "label": label}
            for key, label in schema["group_options"]
        ],
        "default_sort": {"key": "date", "direction": "desc"},
    }


def agent_audit_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    content = AGENT_AUDIT_LOG.read_text(encoding="utf-8")
    for index, (title, body) in enumerate(section_records(content, 3, "## Log"), 1):
        fields = two_column_fields(
            body,
            projection_errors,
            "{}#{}".format(
                "owner-local:records/automation/agent-audit-log.md",
                strip_markdown(title),
            ),
        )
        if not fields:
            continue
        header_parts = [part.strip() for part in title.split("—")]
        raw_agent = strip_markdown(fields.get("Agent", fields.get("Run/agent", "")))
        raw_run = strip_markdown(fields.get("Run ID", fields.get("Run/agent", "")))
        raw_task = strip_markdown(fields.get("Task type", fields.get("Tier", header_parts[2] if len(header_parts) > 2 else "")))
        blockers = strip_markdown(fields.get("Blockers/skipped checks", ""))
        raw_outcome = strip_markdown(fields.get("Outcome", ""))
        if not raw_outcome:
            no_blocker_recorded = bool(re.match(r"^no\b[^.]{0,80}\bblockers?\b", blockers, re.IGNORECASE))
            raw_outcome = "Blocked" if blockers and not no_blocker_recorded else "Completed"
        values = {
            "date": strip_markdown(fields.get("Date/time", header_parts[0] if header_parts else "")),
            "record": strip_markdown(fields.get("Issue/task", header_parts[1] if len(header_parts) > 1 else "")),
            "task": raw_task,
            "agent": raw_agent,
            "run": raw_run,
            "outcome": raw_outcome,
        }
        entries.append(log_entry(f"agent-{index:03d}", values, {
            "date": fields.get("Date/time", ""),
            "record": fields.get("Issue/task", ""),
            "task": fields.get("Task type", fields.get("Tier", "")),
            "agent": fields.get("Agent", fields.get("Run/agent", "")),
            "run": fields.get("Run ID", fields.get("Run/agent", "")),
            "outcome": fields.get("Outcome", raw_outcome),
        }, body))
    return {
        "id": "agents",
        "title": "Agent Audit Log",
        "description": "Autonomous, batched, and scheduled agent-run provenance and rollback records.",
        "source_url": None,
        **owner_log_public_schema("agents"),
        "entries": entries,
    }


def elim_run_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    content = ELIM_RUN_LOG.read_text(encoding="utf-8")
    for index, (title, body) in enumerate(section_records(content, 3, "## Runs"), 1):
        fields = two_column_fields(
            body,
            projection_errors,
            "{}#{}".format(
                "owner-local:records/automation/elim-run-log.md",
                strip_markdown(title),
            ),
        )
        if not fields:
            continue
        header_parts = [part.strip() for part in title.split("—")]
        values = {
            "date": strip_markdown(fields.get("Started", header_parts[0] if header_parts else "")),
            "outcome": strip_markdown(fields.get("Outcome", header_parts[2] if len(header_parts) > 2 else "")),
            "trigger": strip_markdown(fields.get("Trigger", "")),
            "summary": strip_markdown(fields.get("Work summary", "")),
            "usage": strip_markdown(fields.get("Usage", "")),
            "next": strip_markdown(fields.get("Exact next action", "")),
        }
        entries.append(log_entry(f"elim-run-{index:03d}", values, {
            "date": fields.get("Started", ""),
            "outcome": fields.get("Outcome", ""),
            "trigger": fields.get("Trigger", ""),
            "summary": fields.get("Work summary", ""),
            "usage": fields.get("Usage", ""),
            "next": fields.get("Exact next action", ""),
        }, body))
    return {
        "id": "elim",
        "title": "Elim Run Log",
        "description": "Complete per-run operational reports for ARRP's scheduled LLM agent.",
        "source_url": None,
        **owner_log_public_schema("elim"),
        "entries": entries,
    }


def bullet_fields(content: str) -> dict[str, str]:
    return {
        strip_markdown(match.group(1)): match.group(2).strip()
        for match in re.finditer(r"^-\s+([^:\n]+):\s*(.+)$", content, re.MULTILINE)
    }


def source_monitor_log_view(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    content = SOURCE_MONITOR_LOG.read_text(encoding="utf-8")
    for index, (title, body) in enumerate(section_records(content, 2), 1):
        if not re.match(r"\d{4}-\d{2}-\d{2}", title):
            continue
        parts = [part.strip() for part in title.split("—", 1)]
        fields = bullet_fields(body)
        missing = [
            key
            for key in ("Result",)
            if not str(fields.get(key) or "").strip()
        ]
        if missing and projection_errors is not None:
            projection_errors.append(
                {
                    "code": "source_monitor_entry_schema",
                    "severity": "error",
                    "source": SOURCE_MONITOR_LOG.relative_to(ROOT).as_posix(),
                    "heading": strip_markdown(title),
                    "missing_fields": missing,
                    "message": "Source Monitor entry is missing governed projection fields.",
                }
            )
        values = {
            "date": strip_markdown(parts[0]),
            "watcher": strip_markdown(parts[1] if len(parts) > 1 else ""),
            "result": strip_markdown(fields.get("Result", "")),
            "affected": strip_markdown(fields.get(
                "Affected source IDs",
                fields.get("Affected directive IDs", fields.get("Affected records", "")),
            )),
            "activity": strip_markdown(fields.get(
                "Activity code", fields.get("Recommendation ID", "")
            )),
        }
        entries.append(log_entry(f"source-monitor-{index:03d}", values, {
            "date": parts[0],
            "watcher": parts[1] if len(parts) > 1 else "",
            "result": fields.get("Result", ""),
            "affected": fields.get(
                "Affected source IDs",
                fields.get("Affected directive IDs", fields.get("Affected records", "")),
            ),
            "activity": fields.get(
                "Activity code", fields.get("Recommendation ID", "")
            ),
        }, body))
    return {
        "id": "source-monitor",
        "title": "Source Monitor Log",
        "description": "Material watcher changes and exact-head repository disposition recommendations.",
        "source_url": GITHUB_BLOB_ROOT + "framework/logs/sources/source-monitor-log.md",
        "columns": [
            {"key": "date", "label": "Date and time"},
            {"key": "watcher", "label": "Watcher"},
            {"key": "result", "label": "Result"},
            {"key": "affected", "label": "Affected records"},
            {"key": "activity", "label": "Activity or recommendation"},
        ],
        "group_options": [
            {"key": "watcher", "label": "Watcher"},
            {"key": "result", "label": "Result"},
        ],
        "default_sort": {"key": "date", "direction": "desc"},
        "entries": entries,
    }


def structured_affected_set(
    recommendation: dict[str, object],
    event: dict[str, object],
) -> dict[str, object]:
    event_id = str(recommendation.get("proposal_event_id") or "")
    if str(event.get("event_id") or "") != event_id:
        raise RuntimeError("Bound event identity does not match the recommendation.")
    proposal = event.get("proposal")
    if not isinstance(proposal, dict):
        raise RuntimeError("Bound event lacks its proposal identity.")
    if int(proposal.get("pull_request_number") or 0) != int(
        recommendation.get("pull_request_number") or 0
    ):
        raise RuntimeError("Bound event pull request does not match the recommendation.")
    if str(proposal.get("proposal_revision") or "") != str(
        recommendation.get("head_revision") or ""
    ):
        raise RuntimeError(
            "Bound event head revision does not match the recommendation."
        )
    affected = event.get("affected_records")
    if not isinstance(affected, list):
        raise RuntimeError("Bound event affected_records is not an array.")
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, record in enumerate(affected):
        if not isinstance(record, dict):
            raise RuntimeError(
                f"Bound event affected record {index} is not an object."
            )
        record_id = str(record.get("record_id") or "").strip()
        record_type = str(record.get("record_type") or "").strip()
        if not record_id or not record_type:
            raise RuntimeError(
                f"Bound event affected record {index} lacks identity or type."
            )
        key = (record_type, record_id)
        if key in seen:
            raise RuntimeError(
                f"Bound event duplicates affected record {record_type}:{record_id}."
            )
        seen.add(key)
        normalized.append({"record_id": record_id, "record_type": record_type})
    summary = event.get("summary")
    declared_count = (
        summary.get("affected_record_count")
        if isinstance(summary, dict)
        else None
    )
    if declared_count is None or int(declared_count) != len(normalized):
        raise RuntimeError(
            "Bound event affected count does not match its exact enumeration."
        )
    by_type: dict[str, list[str]] = {}
    for record in normalized:
        by_type.setdefault(record["record_type"], []).append(record["record_id"])
    by_type = {
        record_type: sorted(identifiers)
        for record_type, identifiers in sorted(by_type.items())
    }
    return {
        "complete": True,
        "total_count": len(normalized),
        "records": normalized,
        "record_ids": sorted(record["record_id"] for record in normalized),
        "by_type": by_type,
        "source_ids": by_type.get("source", []),
        "directive_ids": by_type.get("presidential-directive", []),
        "issue_development_ids": sorted(
            by_type.get("proposal", []) + by_type.get("candidate", [])
        ),
        "issue_development_count": len(
            by_type.get("proposal", []) + by_type.get("candidate", [])
        ),
    }


def repository_review_recommendations(
    projection_errors: list[dict[str, object]] | None = None,
    event_loader: object = None,
) -> list[dict[str, object]]:
    records = parse_source_monitor_recommendations(
        SOURCE_MONITOR_LOG.read_text(encoding="utf-8")
    )
    retained = {
        str(item.get("id") or ""): item
        for item in existing_console_payload().get(
            "repository_review_recommendations", []
        )
        if isinstance(item, dict)
    }
    display_fields = {
        "reviewer",
        "recommendation",
        "rationale",
        "affected_records",
        "confidence",
        "human_question",
        "reassessment_trigger",
        "heading",
    }
    projected: list[dict[str, object]] = []
    for record in records:
        event_id = str(record.get("proposal_event_id") or "")
        event_path = ""
        try:
            if event_loader is not None:
                loaded = event_loader(event_id)
                if isinstance(loaded, tuple):
                    event, event_path = loaded
                else:
                    event = loaded
            else:
                prior = retained.get(str(record.get("id") or ""), {})
                affected = prior.get("affected")
                if not isinstance(affected, dict):
                    raise RuntimeError(
                        "Retired source-domain event feed is no longer an active Console input."
                    )
                event = None
            if event is None:
                pass
            elif not isinstance(event, dict):
                raise RuntimeError("Structured event loader returned a non-object.")
            else:
                affected = structured_affected_set(record, event)
        except (RuntimeError, TypeError, ValueError) as exc:
            affected = {
                "complete": False,
                "total_count": None,
                "records": [],
                "record_ids": [],
                "by_type": {},
                "source_ids": [],
                "directive_ids": [],
                "issue_development_ids": [],
                "issue_development_count": None,
                "error": str(exc),
            }
            if projection_errors is not None:
                projection_errors.append(
                    {
                        "code": "recommendation_affected_set_unavailable",
                        "severity": "error",
                        "recommendation_id": record.get("id"),
                        "event_id": event_id,
                        "message": str(exc),
                    }
                )
        projected.append(
            {
            **{
                key: strip_markdown(str(value)) if key in display_fields else value
                for key, value in record.items()
            },
            "affected": affected,
            "event_source_url": None,
            "source_url": GITHUB_BLOB_ROOT
            + "framework/logs/sources/source-monitor-log.md",
            "console_target": "logs:source-monitor",
        }
        )
    return projected


def project_log_views(
    projection_errors: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    definitions = (
        ("horizon", horizon_log_view),
        ("elim", elim_run_log_view),
        ("agents", agent_audit_log_view),
        ("source-monitor", source_monitor_log_view),
        ("changes", change_audit_log_view),
        ("governance-changes", governance_change_log_view),
        ("console-development", console_development_log_view),
    )
    logs: list[dict[str, object]] = []
    for log_id, builder in definitions:
        local_errors: list[dict[str, object]] = []
        owner_source_unavailable = (
            not ALLOW_PRIVATE_CONSOLE_INPUTS
            and log_id in {"elim", "agents"}
        )
        if owner_source_unavailable:
            schema = owner_log_public_schema(log_id)
            record = {
                "id": log_id,
                "title": (
                    "Elim Run Log" if log_id == "elim" else "Agent Audit Log"
                ),
                "description": OWNER_MODE_UNAVAILABLE_MESSAGE,
                "source_url": None,
                **schema,
                "entries": [],
            }
        try:
            if not owner_source_unavailable:
                record = builder(local_errors)
        except OSError:
            record = {
                "id": log_id,
                "title": log_id.replace("-", " ").title(),
                "description": "The owning log is unavailable in this Console mode.",
                "source_url": None,
                "columns": [],
                "group_options": [],
                "default_sort": {"key": "date", "direction": "desc"},
                "entries": [],
            }
            local_errors.append(
                {
                    "code": "log_source_unavailable",
                    "severity": "error",
                    "log_id": log_id,
                    "message": "The owning log source is unavailable.",
                }
            )
        entries = (
            record.get("entries")
            if isinstance(record.get("entries"), list)
            else []
        )
        dates = [
            str((entry.get("values") or {}).get("date") or "")
            for entry in entries
            if isinstance(entry, dict)
            and isinstance(entry.get("values"), dict)
            and str((entry.get("values") or {}).get("date") or "")
        ]
        record.update(
            {
                "availability": (
                    "unavailable"
                    if owner_source_unavailable
                    else "current" if not local_errors else "stale"
                ),
                "complete": (
                    False if owner_source_unavailable else not local_errors
                ),
                "schema_errors": local_errors,
                "current_through": max(dates) if dates else None,
                "producer": f"{log_id}-log-projection",
                "reason": (
                    OWNER_MODE_UNAVAILABLE_MESSAGE
                    if owner_source_unavailable
                    else ""
                    if not local_errors
                    else "The log projection has source or schema errors."
                ),
            }
        )
        if projection_errors is not None:
            projection_errors.extend(local_errors)
        logs.append(record)
    return logs


def is_markdown_table_separator(line: str) -> bool:
    cells = markdown_table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def render_markdown_safe(value: str) -> str:
    """Render useful GitHub-style Markdown while escaping all source HTML.

    The console is intentionally dependency-free and works from ``file://``.
    Only tags emitted by this function can enter the generated data bundle.
    """
    lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    index = 0

    def starts_block(position: int) -> bool:
        if position >= len(lines):
            return False
        line = lines[position]
        return bool(
            not line.strip()
            or re.match(r"^#{1,6}\s+", line)
            or re.match(r"^\s*```", line)
            or re.match(r"^\s*>\s?", line)
            or re.match(r"^\s*[-+*]\s+", line)
            or re.match(r"^\s*\d+[.)]\s+", line)
            or re.match(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", line)
            or (
                position + 1 < len(lines)
                and "|" in line
                and is_markdown_table_separator(lines[position + 1])
            )
        )

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        fence = re.match(r"^\s*```\s*([A-Za-z0-9_-]*)\s*$", line)
        if fence:
            language = fence.group(1)
            index += 1
            code_lines: list[str] = []
            while index < len(lines) and not re.match(r"^\s*```\s*$", lines[index]):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            class_name = f' class="language-{language}"' if language else ""
            output.append(
                f"<pre><code{class_name}>{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading:
            level = len(heading.group(1))
            output.append(f"<h{level}>{render_markdown_inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        if re.match(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", line):
            output.append("<hr>")
            index += 1
            continue

        if re.match(r"^\s*>\s?", line):
            quoted: list[str] = []
            while index < len(lines):
                match = re.match(r"^\s*>\s?(.*)$", lines[index])
                if not match:
                    break
                quoted.append(match.group(1))
                index += 1
            output.append(f"<blockquote>{render_markdown_safe(chr(10).join(quoted))}</blockquote>")
            continue

        if index + 1 < len(lines) and "|" in line and is_markdown_table_separator(lines[index + 1]):
            headers = markdown_table_cells(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip() and "|" in lines[index]:
                rows.append(markdown_table_cells(lines[index]))
                index += 1
            head = "".join(f"<th>{render_markdown_inline(cell)}</th>" for cell in headers)
            body_rows = []
            for row in rows:
                padded = row[: len(headers)] + [""] * max(0, len(headers) - len(row))
                body_rows.append(
                    "<tr>" + "".join(f"<td>{render_markdown_inline(cell)}</td>" for cell in padded) + "</tr>"
                )
            output.append(
                f"<div class=\"markdown-table-wrap\"><table><thead><tr>{head}</tr></thead>"
                f"<tbody>{''.join(body_rows)}</tbody></table></div>"
            )
            continue

        unordered = re.match(r"^\s*[-+*]\s+(.+)$", line)
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if unordered or ordered:
            list_tag = "ul" if unordered else "ol"
            pattern = r"^\s*[-+*]\s+(.+)$" if unordered else r"^\s*\d+[.)]\s+(.+)$"
            items: list[str] = []
            while index < len(lines):
                item = re.match(pattern, lines[index])
                if not item:
                    break
                content = item.group(1)
                task = re.match(r"^\[([ xX])\]\s*(.*)$", content)
                if task:
                    checked = " checked" if task.group(1).casefold() == "x" else ""
                    rendered_item = (
                        f'<input type="checkbox" disabled{checked}> '
                        f"{render_markdown_inline(task.group(2))}"
                    )
                else:
                    rendered_item = render_markdown_inline(content)
                items.append(f"<li>{rendered_item}</li>")
                index += 1
            output.append(f"<{list_tag}>{''.join(items)}</{list_tag}>")
            continue

        paragraph = [line.strip()]
        index += 1
        while index < len(lines) and not starts_block(index):
            paragraph.append(lines[index].strip())
            index += 1
        output.append(f"<p>{render_markdown_inline(' '.join(paragraph))}</p>")

    return "\n".join(output)


MONITORING_SECTION_HEADING = re.compile(
    r"^##[ \t]+(?:"
    r"Watching for updates(?:[ \t]*[:—-][^\r\n]*)?"
    r"|Defined monitoring(?:[ \t]+and[ \t]+research)?[ \t]+triggers"
    r"|Monitoring status and (?:revisit[ \t]+trigger|next[ \t]+step)"
    r"|Monitoring predicates?"
    r"|Monitoring items?"
    r"|Next step"
    r")[ \t]*$"
    r"(.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)


def monitoring_section(value: str) -> str:
    """Extract a monitoring instruction from one of the headings used by current records."""
    section = MONITORING_SECTION_HEADING.search(value)
    return strip_markdown(section.group(1)) if section else ""


def monitoring_rationale_for_record(registry_row: dict[str, str], issue_body: str = "") -> str:
    """Return the most specific available human-authored monitoring instruction."""
    canonical = registry_row.get("Canonical Record", "").strip()
    if issue_body and (
        registry_row.get("Kind", "").strip() == "horizon"
        or canonical == str(HORIZON_LOG.relative_to(ROOT))
    ):
        section = monitoring_section(issue_body)
        if section:
            return section
    if canonical:
        path = ROOT / canonical
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            match = re.search(r'^audit_next:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
            if match and match.group(1).strip():
                return strip_markdown(match.group(1))
            section = monitoring_section(content)
            if section:
                return section
    if issue_body:
        section = monitoring_section(issue_body)
        if section:
            return section
    return "The owning issue is marked for monitoring, but its specific trigger has not yet been structured."


def markdown_links(value: str) -> list[dict[str, str]]:
    return [
        {"label": label.strip(), "url": url.strip()}
        for label, url in re.findall(r"\[([^]]+)\]\(([^)]+)\)", value)
        if label.strip() and url.strip()
    ]


def horizon_log_records(
    projection_errors: list[dict[str, object]] | None = None,
) -> dict[str, dict[str, object]]:
    fields = (
        "id",
        "decision_date",
        "original_concern",
        "decision",
        "integrated_into",
        "rationale",
        "follow_up",
    )
    records: dict[str, dict[str, object]] = {}
    for line_number, line in enumerate(
        HORIZON_LOG.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not re.match(r"^\|\s*HOR-\d+\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(fields):
            if projection_errors is not None:
                projection_errors.append(
                    {
                        "code": "horizon_log_row_width",
                        "severity": "error",
                        "source": HORIZON_LOG.relative_to(ROOT).as_posix(),
                        "line": line_number,
                        "expected_columns": len(fields),
                        "actual_columns": len(cells),
                        "message": "Horizon log row cannot be projected without loss.",
                    }
                )
            continue
        raw = dict(zip(fields, cells))
        record_id = raw["id"]
        links: list[dict[str, str]] = []
        for field in fields[1:]:
            links.extend(markdown_links(raw[field]))
        unique_links = {
            (link["label"], link["url"]): link for link in links
        }
        records[record_id] = {
            field: strip_markdown(raw[field]) for field in fields
        }
        records[record_id]["links"] = list(unique_links.values())
    return records


def markdown_title(path: Path, content: str) -> str:
    title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return heading_match.group(1).strip() if heading_match else path.stem.replace("-", " ").title()


def research_markdown_files() -> list[Path]:
    """Return maintained central and area-owned research records."""
    paths = list((ROOT / "research").rglob("*.md"))
    paths.extend((ROOT / "areas").glob("*/research/*.md"))
    return sorted(set(paths))


def research_for_record(record_id: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    identifier = re.compile(rf"(?<![A-Z0-9-]){re.escape(record_id)}(?![A-Z0-9-])")
    for path in research_markdown_files():
        relative = path.relative_to(ROOT)
        if "project-console" in relative.parts or relative.name == "README.md":
            continue
        content = path.read_text(encoding="utf-8")
        if not identifier.search(content):
            continue
        records.append(
            {
                "title": markdown_title(path, content),
                "path": relative.as_posix(),
                "url": GITHUB_BLOB_ROOT + relative.as_posix(),
            }
        )
    return records


def candidate_records() -> list[dict[str, object]]:
    sources = source_index()
    records: list[dict[str, object]] = []
    for row in read_csv(CANDIDATES):
        if row["review_status"] != "preliminary-candidate":
            continue
        source_ids = list(dict.fromkeys(split_values(row["source_record_ids"])))
        supporting_sources = []
        for source_id in source_ids:
            source = sources.get(source_id)
            if not source:
                raise RuntimeError(
                    f"Preliminary candidate {row['candidate_id']} references missing source {source_id}."
                )
            supporting_sources.append(source_payload(source))
        links = parse_links(row["source_links"])
        seen_urls = {link["url"] for link in links}
        for source in supporting_sources:
            if source["url"] and source["url"] not in seen_urls:
                label = f"{source['id']} · {source['publisher'] or source['title']}"
                links.append({"label": label, "url": source["url"]})
                seen_urls.add(source["url"])
        if not source_ids and not links:
            raise RuntimeError(
                f"Preliminary candidate {row['candidate_id']} has no supporting source."
            )
        records.append(
            {
                "id": row["candidate_id"],
                "kind": "preliminary_candidate",
                "title": row["title"],
                "term": row["term"],
                "summary": row["institutional_defect"],
                "proposed_area": row["proposed_area"],
                "distinctness": row["distinctness_rationale"],
                "coverage": row["existing_coverage_considered"],
                "counterargument": row["counterargument"],
                "unresolved": row["unresolved_questions"],
                "recommendation": row["recommendation"],
                "source_record_ids": source_ids,
                "evidence_records": [],
                "supporting_sources": supporting_sources,
                "links": links,
                "last_checked": row["last_reviewed"],
            }
        )
    return sorted(records, key=lambda record: str(record["id"]))


def proposal_index_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for row in read_csv(ISSUE_REGISTRY):
        if row["Kind"].strip() != "proposal":
            continue
        issue_id = row["Object ID"].strip()
        if not issue_id:
            continue
        title = re.sub(
            rf"^{re.escape(issue_id)}\s*:\s*", "", row["GitHub Title"].strip()
        )
        canonical = row["Canonical Record"].strip()
        records.append(
            {
                "id": issue_id,
                "title": title,
                "area": issue_id.split("-", 1)[0],
                "canonical_page": f"../{canonical}" if canonical else "",
                "issue_url": row["GitHub Issue"].strip(),
            }
        )
    return sorted(records, key=lambda record: record["id"])


def run_gh_json(arguments: list[str]) -> object:
    completed = subprocess.run(
        ["gh", *arguments], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return json.loads(completed.stdout)


@functools.lru_cache(maxsize=1)
def project_items_snapshot() -> dict[str, object]:
    """Read the personal Project by exact node ID with the Project-only token."""

    token = os.environ.get("ARRP_PROJECT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "ARRP_PROJECT_TOKEN is required for an authenticated Console refresh."
        )
    config = json.loads(
        (ROOT / "framework/project/interfaces/project-console/configuration/progress.json").read_text(
            encoding="utf-8"
        )
    )
    raw = fetch_project(config, token)
    items: list[dict[str, object]] = []
    for node in raw.get("items") or []:
        content = node.get("content") or {}
        content_type = str(content.get("__typename") or "")
        values = {
            str(name).strip().casefold(): value
            for name, value in extract_project_field_values(node).items()
            if str(name).strip()
        }
        labels = [
            str(label.get("name") or "")
            for label in ((content.get("labels") or {}).get("nodes") or [])
            if str(label.get("name") or "")
        ]
        items.append(
            {
                "id": node.get("id"),
                "content": {
                    "number": content.get("number"),
                    "title": content.get("title"),
                    "type": (
                        "Issue"
                        if content_type == "Issue"
                        else "PullRequest"
                        if content_type == "PullRequest"
                        else "DraftIssue"
                        if content_type == "DraftIssue"
                        else content_type
                    ),
                    "url": content.get("url"),
                },
                "labels": labels,
                **values,
            }
        )
    return {
        "items": items,
        "totalCount": len(items),
    }


def run_gh_paginated_json(endpoint: str) -> list[dict[str, object]]:
    completed = subprocess.run(
        ["gh", "api", "--paginate", "--slurp", endpoint],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    pages = json.loads(completed.stdout)
    if not isinstance(pages, list) or not all(
        isinstance(page, list) for page in pages
    ):
        raise RuntimeError(
            f"GitHub API pagination returned an invalid collection for {endpoint}."
        )
    records: list[dict[str, object]] = []
    for page in pages:
        records.extend(
            record for record in page if isinstance(record, dict)
        )
    return records


def _github_security_provider_snapshot() -> dict[str, object]:
    """Read only the minimum provider posture needed for local minimization."""
    repository = "Thorncrag/ARRP"
    checked_at = utc_timestamp()
    try:
        code_scanning = run_gh_paginated_json(
            f"repos/{repository}/code-scanning/alerts?state=open&per_page=100"
        )
        dependabot = run_gh_paginated_json(
            f"repos/{repository}/dependabot/alerts?state=open&per_page=100"
        )
        secret_scanning = run_gh_paginated_json(
            f"repos/{repository}/secret-scanning/alerts?state=open&per_page=100"
        )
    except Exception:
        return {
            "checked_at": checked_at,
            "availability": "unavailable",
            "complete": False,
            "human_attention": None,
            "elim_attention": None,
        }
    return {
        "checked_at": checked_at,
        "availability": "current",
        "complete": True,
        "human_attention": bool(secret_scanning),
        "elim_attention": bool(code_scanning or dependabot),
    }


SECURITY_ASSURANCE_FIELDS = {
    "tool_id",
    "label",
    "availability",
    "last_checked",
    "next_due",
    "source_revision",
    "coverage_state",
    "private_attention",
    "owner_class",
    "destination_class",
    "active_incident",
    "public_intake_state",
}


def console_classification_registry() -> dict[str, object]:
    registry = json.loads(
        CONSOLE_CLASSIFICATION_REGISTRY.read_text(encoding="utf-8")
    )
    if (
        not isinstance(registry, dict)
        or registry.get("schema_version") != 1
        or registry.get("registry_id") != "arrp-project-console-classifications"
        or not isinstance(registry.get("namespaces"), dict)
    ):
        raise RuntimeError("Console classification registry is invalid.")
    required = {
        "id",
        "label",
        "meaning",
        "inclusion_predicate",
        "authoritative_source",
        "producer",
        "lifecycle_owner",
        "destination",
        "resolution_rule",
        "allowed_consumers",
    }
    for namespace in ("work_kind", "finding_code", "queue_id", "workflow_view"):
        entries = registry["namespaces"].get(namespace)
        if not isinstance(entries, list) or not entries:
            raise RuntimeError(
                f"Console classification namespace {namespace} is unavailable."
            )
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or not required.issubset(entry)
                or not all(
                    str(entry.get(field) or "").strip()
                    for field in required - {"allowed_consumers"}
                )
                or not isinstance(entry.get("allowed_consumers"), list)
                or not entry["allowed_consumers"]
            ):
                raise RuntimeError(
                    f"Console classification namespace {namespace} has an incomplete entry."
                )
    return registry


def security_tool_registry() -> list[dict[str, object]]:
    registry = console_classification_registry()
    tools = (
        registry.get("namespaces", {}).get("security_tool")
    )
    if not isinstance(tools, list) or len(tools) != 7:
        raise RuntimeError("Security assurance tool registry is unavailable.")
    required = {
        "id",
        "label",
        "purpose",
        "authoritative_source",
        "producer",
        "lifecycle_owner",
        "destination_class",
        "allowed_consumers",
    }
    if any(
        not isinstance(tool, dict)
        or set(tool) != required
        or tool.get("producer") != "security-assurance-projection"
        for tool in tools
    ):
        raise RuntimeError("Security assurance tool registry is invalid.")
    ids = [str(tool["id"]) for tool in tools]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Security assurance tool registry has duplicate IDs.")
    return tools


def console_development_category_registry() -> list[dict[str, object]]:
    categories = console_classification_registry()["namespaces"].get(
        "console_development_category"
    )
    required = {"id", "label", "meaning", "allowed_consumers"}
    if (
        not isinstance(categories, list)
        or len(categories) != 7
        or any(
            not isinstance(category, dict)
            or set(category) != required
            or category.get("allowed_consumers") != ["console_development_log"]
            for category in categories
        )
    ):
        raise RuntimeError("Console Development Log category registry is invalid.")
    ids = [str(category["id"]) for category in categories]
    labels = [str(category["label"]) for category in categories]
    if len(ids) != len(set(ids)) or len(labels) != len(set(labels)):
        raise RuntimeError(
            "Console Development Log category registry has duplicate identities."
        )
    return categories


def validate_console_development_log_categories() -> None:
    text = CONSOLE_DEVELOPMENT_LOG.read_text(encoding="utf-8")
    registered = {
        str(category["label"]): str(category["id"])
        for category in console_development_category_registry()
    }
    umbrellas = section_records(text, 2)
    if not umbrellas:
        raise RuntimeError("Console Development Log has no dated umbrella entries.")
    dates: set[str] = set()
    for heading, body in umbrellas:
        date = strip_markdown(heading)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            raise RuntimeError(
                f"Console Development Log umbrella is not an ISO date: {date}"
            )
        if date in dates:
            raise RuntimeError(
                f"Console Development Log repeats a dated umbrella: {date}"
            )
        dates.add(date)
        fields = bullet_fields(body)
        change_ids = set(
            re.findall(
                r"CONSOLE-\d{4}-\d{3}",
                str(fields.get("Console Change IDs") or ""),
            )
        )
        if not change_ids or not str(fields.get("Title") or "").strip():
            raise RuntimeError(
                f"Console Development Log umbrella metadata is incomplete: {date}"
            )
        categories = list(re.finditer(r"(?m)^### (.+?)\s*$", body))
        if not categories:
            raise RuntimeError(
                f"Console Development Log has no category sections: {date}"
            )
        seen_categories: set[str] = set()
        for index, match in enumerate(categories):
            label = match.group(1)
            category_id = registered.get(label)
            if category_id is None:
                raise RuntimeError(
                    f"Unregistered Console Development Log category: {label}"
                )
            if category_id in seen_categories:
                raise RuntimeError(
                    f"Console Development Log repeats category {label}: {date}"
                )
            seen_categories.add(category_id)
            end = (
                categories[index + 1].start()
                if index + 1 < len(categories)
                else len(body)
            )
            section = body[match.end():end]
            required_lines = (
                f"- Category ID: `{category_id}`",
                "- Change ID:",
                "- Commit IDs:",
                "- Material change:",
                "- Validation:",
            )
            if any(line not in section for line in required_lines):
                raise RuntimeError(
                    "Console Development Log category metadata is incomplete: "
                    f"{label}"
                )
            section_change_ids = set(
                re.findall(
                    r"CONSOLE-\d{4}-\d{3}",
                    str(bullet_fields(section).get("Change ID") or ""),
                )
            )
            if not section_change_ids or not section_change_ids <= change_ids:
                raise RuntimeError(
                    "Console Development Log category has an unbound Change ID: "
                    f"{label}"
                )


def public_security_assurance_projection() -> dict[str, object]:
    tools = security_tool_registry()
    return {
        "schema_version": 2,
        "availability": "unavailable",
        "complete": False,
        "checked_at": None,
        "public_intake_state": "unverified",
        "private_attention": "unavailable",
        "active_incident": False,
        "tools": [
            {
                "tool_id": tool["id"],
                "label": tool["label"],
                "purpose": tool["purpose"],
                "availability": "unavailable",
                "last_checked": None,
                "next_due": None,
                "source_revision": None,
                "coverage_state": "unavailable",
                "private_attention": "unknown",
                "owner_class": tool["lifecycle_owner"],
                "destination_class": tool["destination_class"],
                "active_incident": False,
                "public_intake_state": (
                    "unverified"
                    if tool["id"] == "public-intake-protection"
                    else None
                ),
            }
            for tool in tools
        ],
    }


def security_assurance_snapshot() -> dict[str, object]:
    """Minimize authenticated security state before any Console persistence."""

    provider = _github_security_provider_snapshot()
    checked_at = provider.get("checked_at")
    public = public_security_assurance_projection()
    if (
        provider.get("availability") != "current"
        or provider.get("complete") is not True
    ):
        return {
            "schema_version": 2,
            "availability": "unavailable",
            "complete": False,
            "checked_at": checked_at,
            "public_intake_state": "unverified",
            "private_attention": "unavailable",
            "active_incident": False,
            "tools": [
                {
                    key: value for key, value in tool.items()
                    if key in SECURITY_ASSURANCE_FIELDS
                }
                for tool in public["tools"]
            ],
        }
    human_required = provider.get("human_attention") is True
    elim_required = provider.get("elim_attention") is True
    tool_attention = {
        "credential-access-review": "yes" if human_required else "no",
        "repository-change-protection": "yes" if elim_required else "no",
    }
    tools = []
    for tool in public["tools"]:
        minimized = {
            key: value for key, value in tool.items()
            if key in SECURITY_ASSURANCE_FIELDS
        }
        minimized["last_checked"] = checked_at
        minimized["private_attention"] = tool_attention.get(
            str(tool["tool_id"]), "unknown"
        )
        tools.append(minimized)
    return {
        "schema_version": 2,
        "availability": "current",
        "complete": True,
        "checked_at": checked_at,
        "public_intake_state": "unverified",
        "private_attention": (
            "required" if human_required or elim_required else "none_reported"
        ),
        "active_incident": False,
        "tools": tools,
    }


def valid_private_security_assurance(snapshot: object) -> bool:
    if not isinstance(snapshot, dict) or set(snapshot) != {
        "schema_version",
        "availability",
        "complete",
        "checked_at",
        "public_intake_state",
        "private_attention",
        "active_incident",
        "tools",
    }:
        return False
    if snapshot.get("schema_version") != 2 or not isinstance(
        snapshot.get("tools"), list
    ):
        return False
    if (
        snapshot.get("availability") not in {"current", "unavailable"}
        or not isinstance(snapshot.get("complete"), bool)
        or snapshot.get("public_intake_state")
        not in {"live", "paused", "unverified"}
        or snapshot.get("private_attention")
        not in {"required", "none_reported", "unavailable"}
        or not isinstance(snapshot.get("active_incident"), bool)
    ):
        return False
    registered = {
        str(tool["id"]): tool for tool in security_tool_registry()
    }
    expected_ids = set(registered)
    observed_ids: set[str] = set()
    for tool in snapshot["tools"]:
        if not isinstance(tool, dict) or set(tool) != SECURITY_ASSURANCE_FIELDS:
            return False
        tool_id = str(tool.get("tool_id") or "")
        if not tool_id or tool_id in observed_ids:
            return False
        definition = registered.get(tool_id)
        if (
            definition is None
            or tool.get("label") != definition["label"]
            or tool.get("owner_class") != definition["lifecycle_owner"]
            or tool.get("destination_class") != definition["destination_class"]
            or tool.get("availability") not in {"current", "unavailable"}
            or tool.get("coverage_state")
            not in {"current", "stale", "incomplete", "unavailable"}
            or tool.get("private_attention") not in {"yes", "no", "unknown"}
            or not isinstance(tool.get("active_incident"), bool)
            or tool.get("public_intake_state")
            not in {None, "live", "paused", "unverified"}
        ):
            return False
        observed_ids.add(tool_id)
    return observed_ids == expected_ids


def write_private_security_assurance(
    snapshot: dict[str, object] | None = None,
) -> dict[str, object]:
    if snapshot is None:
        snapshot = security_assurance_snapshot()
    if not valid_private_security_assurance(snapshot):
        raise RuntimeError(
            "Private security-assurance projection violates its field allowlist."
        )
    serialized = json.dumps(
        snapshot, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/")
    text = (
        "/* Private local projection; never commit or publish. */\n"
        f"window.ARRP_PRIVATE_SECURITY_ASSURANCE={serialized};\n"
    )
    secret_findings = prohibited_secret_findings(
        "framework/project/interfaces/project-console/data/private-security-assurance.js",
        text.encode("utf-8"),
    )
    if secret_findings:
        finding_ids = ",".join(
            str(item.get("finding_id") or "DISC-UNKNOWN")
            for item in secret_findings
        )
        raise RuntimeError(
            "Private security-assurance projection contains prohibited secret "
            f"material and was not persisted ({finding_ids})."
        )
    atomic_write_text(
        PRIVATE_SECURITY_ASSURANCE_OUTPUT,
        text,
    )
    return snapshot


def read_private_security_assurance() -> dict[str, object] | None:
    if not PRIVATE_SECURITY_ASSURANCE_OUTPUT.exists():
        return None
    prefix = (
        "/* Private local projection; never commit or publish. */\n"
        "window.ARRP_PRIVATE_SECURITY_ASSURANCE="
    )
    text = PRIVATE_SECURITY_ASSURANCE_OUTPUT.read_text(encoding="utf-8")
    if not text.startswith(prefix):
        return None
    try:
        value = json.loads(text.removeprefix(prefix).removesuffix(";\n"))
    except json.JSONDecodeError:
        return None
    if not valid_private_security_assurance(value):
        return None
    return value


def unavailable_governance_supplements(
    *,
    source_revision: str,
    checked_at: str,
    reason_code: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "availability": "unavailable",
        "complete": False,
        "checked_at": checked_at,
        "source_revision": source_revision,
        "public_log_sha256": file_sha256(ROOT, GOVERNANCE_CHANGE_LOG),
        "items": [],
        "reason_code": reason_code,
    }


def owner_governance_supplements(
    *,
    source_revision: str,
    checked_at: str,
    private_authority: PrivateProjectAuthority | None = None,
) -> dict[str, object]:
    """Project only Console-safe summaries from the fixed private authority."""

    try:
        public_changes = parse_public_changes(
            GOVERNANCE_CHANGE_LOG,
            GOVERNANCE_CHANGE_REGISTRY,
        )
        if private_authority is None:
            raise PathAuthorityError(
                "private staging authority is unavailable"
            )
        path = private_authority.records_path(
            GOVERNANCE_SUPPLEMENTS_RELATIVE,
            required=False,
        )
    except (GovernanceChangeError, OSError, PathAuthorityError):
        return unavailable_governance_supplements(
            source_revision=source_revision,
            checked_at=checked_at,
            reason_code="owner-local-governance-supplements-unavailable",
        )
    projection = project_private_supplements(path, public_changes)
    if (
        projection.get("availability") != "current"
        or projection.get("complete") is not True
        or not isinstance(projection.get("items"), list)
    ):
        return unavailable_governance_supplements(
            source_revision=source_revision,
            checked_at=checked_at,
            reason_code=str(
                projection.get("reason_code")
                or "owner-local-governance-supplements-unavailable"
            ),
        )
    items = [
        {
            "governance_change_id": str(event["governance_id"]),
            "public_entry_sha256": str(event["public_entry_sha256"]),
            "source_revision": source_revision,
            "recorded_at": str(event["recorded_at"]),
            "safe_summary": str(event["safe_summary"]),
        }
        for event in projection["items"]
        if isinstance(event, dict)
    ]
    return {
        "schema_version": 1,
        "availability": "current",
        "complete": True,
        "checked_at": checked_at,
        "source_revision": source_revision,
        "public_log_sha256": file_sha256(ROOT, GOVERNANCE_CHANGE_LOG),
        "items": items,
        "reason_code": None,
    }


def valid_private_governance_supplements(
    projection: object,
    *,
    source_revision: str,
    project_logs: list[dict[str, object]],
) -> bool:
    top_fields = {
        "schema_version",
        "availability",
        "complete",
        "checked_at",
        "source_revision",
        "public_log_sha256",
        "items",
        "reason_code",
    }
    item_fields = {
        "governance_change_id",
        "public_entry_sha256",
        "source_revision",
        "recorded_at",
        "safe_summary",
    }
    if (
        not isinstance(projection, dict)
        or set(projection) != top_fields
        or projection.get("schema_version") != 1
        or projection.get("source_revision") != source_revision
        or not re.fullmatch(
            r"sha256:[0-9a-f]{64}",
            str(projection.get("public_log_sha256") or ""),
        )
        or not isinstance(projection.get("items"), list)
    ):
        return False
    try:
        datetime.fromisoformat(
            str(projection.get("checked_at") or "").replace("Z", "+00:00")
        )
    except ValueError:
        return False
    if projection.get("complete") is not True:
        return bool(
            projection.get("availability") == "unavailable"
            and projection.get("items") == []
            and isinstance(projection.get("reason_code"), str)
            and projection.get("reason_code")
        )
    if (
        projection.get("availability") != "current"
        or projection.get("reason_code") is not None
    ):
        return False
    governance_log = next(
        (
            log
            for log in project_logs
            if isinstance(log, dict)
            and log.get("id") == "governance-changes"
        ),
        None,
    )
    if not isinstance(governance_log, dict):
        return False
    entries = governance_log.get("entries")
    if not isinstance(entries, list):
        return False
    public_entries = {
        str(entry.get("id") or ""): entry
        for entry in entries
        if isinstance(entry, dict)
    }
    required_ids = {
        identifier
        for identifier, entry in public_entries.items()
        if isinstance(entry.get("values"), dict)
        and entry["values"].get("supplement") == "Required"
    }
    observed: set[str] = set()
    for item in projection["items"]:
        if (
            not isinstance(item, dict)
            or set(item) != item_fields
            or item.get("source_revision") != source_revision
            or not isinstance(item.get("safe_summary"), str)
            or not item["safe_summary"].strip()
        ):
            return False
        identifier = str(item.get("governance_change_id") or "")
        public_entry = public_entries.get(identifier)
        if identifier in observed or not isinstance(public_entry, dict):
            return False
        values = public_entry.get("values")
        if (
            not isinstance(values, dict)
            or item.get("public_entry_sha256") != values.get("entry_sha256")
        ):
            return False
        try:
            datetime.fromisoformat(
                str(item.get("recorded_at") or "").replace("Z", "+00:00")
            )
        except ValueError:
            return False
        observed.add(identifier)
    return observed == required_ids


TRANSACTION_RECOVERY_STATES = {
    "active",
    "failed_preserved",
    "recovery_pending",
    "reconciled_or_superseded",
    "recovery_packaged",
    "recoverably_retired",
}
TRANSACTION_RECOVERY_ITEM_FIELDS = {
    "run_id",
    "attempt_group_id",
    "lifecycle_state",
    "preserved",
    "retirement_proof",
    "owner",
    "age_label",
    "failure_class",
    "next_action",
    "specialist_route",
}


def unavailable_transaction_recovery_projection(
    reason_code: str = "owner-local-transaction-recovery-projection-required",
) -> dict[str, object]:
    """Return a safe no-count projection when the owner binding is absent."""

    return {
        "schema_version": 1,
        "availability": "unavailable",
        "complete": False,
        "generated_at": None,
        "items": [],
        "reason_code": reason_code,
    }


def valid_codex_usage_projection(
    snapshot: object,
    *,
    now: datetime | None = None,
) -> bool:
    """Accept only the shared minimized Codex-usage projection schema."""

    return codex_usage_projection_is_valid(snapshot, now=now)


def unavailable_codex_usage_projection() -> dict[str, object]:
    return build_unavailable_codex_usage_projection()


def codex_usage_projection() -> dict[str, object]:
    """Keep the repository-source Console independent of private usage data."""

    return unavailable_codex_usage_projection()


def write_private_codex_usage(payload: dict[str, object]) -> dict[str, object]:
    if not valid_codex_usage_projection(payload):
        raise RuntimeError("Codex usage projection violates its strict allowlist.")
    text = "/* Private local projection; never commit or publish. */\nwindow.ARRP_PRIVATE_CODEX_USAGE=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";\n"
    if prohibited_secret_findings("framework/project/interfaces/project-console/data/private-codex-usage.js", text.encode("utf-8")):
        raise RuntimeError("Codex usage projection contains prohibited secret material.")
    atomic_write_text(PRIVATE_CODEX_USAGE_OUTPUT, text)
    return payload


def transaction_recovery_unresolved(item: dict[str, object]) -> bool:
    """Apply the fixed queue predicate; producers cannot self-authorize closure."""

    return bool(
        item.get("preserved") is True
        and item.get("lifecycle_state") != "recoverably_retired"
        and item.get("retirement_proof") != "recoverably_retired"
    )


def valid_transaction_recovery_projection(snapshot: object) -> bool:
    """Validate the minimized owner-only transaction-recovery Console feed."""

    expected = {
        "schema_version",
        "availability",
        "complete",
        "generated_at",
        "items",
        "reason_code",
    }
    if not isinstance(snapshot, dict) or set(snapshot) != expected:
        return False
    if snapshot.get("schema_version") != 1 or not isinstance(
        snapshot.get("complete"), bool
    ) or not isinstance(snapshot.get("items"), list):
        return False
    complete = snapshot.get("complete") is True
    if complete != (snapshot.get("availability") == "current"):
        return False
    if complete and snapshot.get("reason_code") is not None:
        return False
    if not complete and (
        snapshot.get("availability") != "unavailable"
        or snapshot.get("items")
        or not isinstance(snapshot.get("reason_code"), str)
    ):
        return False
    if snapshot.get("generated_at") is not None:
        try:
            datetime.fromisoformat(
                str(snapshot["generated_at"]).replace("Z", "+00:00")
            )
        except ValueError:
            return False
    seen: set[str] = set()
    for item in snapshot["items"]:
        if not isinstance(item, dict) or set(item) != TRANSACTION_RECOVERY_ITEM_FIELDS:
            return False
        run_id = str(item.get("run_id") or "").strip()
        if not run_id or run_id in seen:
            return False
        if (
            not str(item.get("attempt_group_id") or "").strip()
            or item.get("lifecycle_state") not in TRANSACTION_RECOVERY_STATES
            or not isinstance(item.get("preserved"), bool)
            or item.get("retirement_proof")
            not in {"not_retired", "recoverably_retired"}
            or not str(item.get("owner") or "").strip()
            or not str(item.get("age_label") or "").strip()
            or not str(item.get("failure_class") or "").strip()
            or not str(item.get("next_action") or "").strip()
            or item.get("specialist_route") != "automation:agents:run-coordinator-bot"
        ):
            return False
        retired = item.get("lifecycle_state") == "recoverably_retired"
        if retired != (item.get("retirement_proof") == "recoverably_retired"):
            return False
        seen.add(run_id)
    return True


def transaction_recovery_console_projection() -> dict[str, object]:
    """Read only a strict, minimized producer projection from owner-local state."""

    try:
        raw = json.loads(
            TRANSACTION_RECOVERY_CONSOLE_PROJECTION.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return unavailable_transaction_recovery_projection()
    return (
        raw
        if valid_transaction_recovery_projection(raw)
        else unavailable_transaction_recovery_projection(
            "owner-local-transaction-recovery-projection-invalid"
        )
    )


def valid_private_operations(
    snapshot: object,
    *,
    catalog_generation_id: str,
    source_revision: str,
) -> bool:
    expected_fields = {
        "schema_version",
        "availability",
        "generated_at",
        "catalog_generation_id",
        "source_revision",
        "agent_registry",
        "project_logs",
        "integrity",
        "run_chain",
        "action_snapshot",
        "queue_directory",
        "operational_incidents",
        "security_incidents",
        "incident_relations",
        "transaction_recovery",
        "governance_change_supplements",
        "privacy",
    }
    return bool(
        isinstance(snapshot, dict)
        and set(snapshot) == expected_fields
        and snapshot.get("schema_version") == 4
        and snapshot.get("availability") == "current"
        and snapshot.get("catalog_generation_id") == catalog_generation_id
        and snapshot.get("source_revision") == source_revision
        and isinstance(snapshot.get("generated_at"), str)
        and isinstance(snapshot.get("agent_registry"), list)
        and isinstance(snapshot.get("project_logs"), list)
        and isinstance(snapshot.get("integrity"), dict)
        and isinstance(snapshot.get("run_chain"), dict)
        and isinstance(snapshot.get("action_snapshot"), dict)
        and isinstance(snapshot["action_snapshot"].get("items"), list)
        and isinstance(snapshot.get("queue_directory"), dict)
        and isinstance(snapshot["queue_directory"].get("queues"), list)
        and isinstance(snapshot.get("operational_incidents"), dict)
        and isinstance(snapshot["operational_incidents"].get("items"), list)
        and isinstance(snapshot.get("security_incidents"), dict)
        and isinstance(snapshot["security_incidents"].get("items"), list)
        and isinstance(snapshot.get("incident_relations"), dict)
        and valid_transaction_recovery_projection(
            snapshot.get("transaction_recovery")
        )
        and valid_private_governance_supplements(
            snapshot.get("governance_change_supplements"),
            source_revision=source_revision,
            project_logs=snapshot["project_logs"],
        )
    )


def write_private_operations(
    *,
    catalog_generation_id: str,
    source_revision: str,
    agent_registry: list[dict[str, object]],
    project_logs: list[dict[str, object]],
    integrity: dict[str, object],
    run_chain: dict[str, object],
    action_snapshot: dict[str, object],
    queue_directory: dict[str, object],
    operational_incidents: dict[str, object],
    security_incidents: dict[str, object],
    incident_relations: dict[str, object],
    governance_change_supplements: dict[str, object],
    transaction_recovery: dict[str, object] | None = None,
) -> dict[str, object]:
    """Persist the complete owner-only Console operations projection safely."""

    snapshot = {
        "schema_version": 4,
        "availability": "current",
        "generated_at": utc_timestamp(),
        "catalog_generation_id": catalog_generation_id,
        "source_revision": source_revision,
        "agent_registry": agent_registry,
        "project_logs": project_logs,
        "integrity": integrity,
        "run_chain": run_chain,
        "action_snapshot": action_snapshot,
        "queue_directory": queue_directory,
        "operational_incidents": operational_incidents,
        "security_incidents": security_incidents,
        "incident_relations": incident_relations,
        "transaction_recovery": (
            transaction_recovery
            if valid_transaction_recovery_projection(transaction_recovery)
            else unavailable_transaction_recovery_projection()
        ),
        "governance_change_supplements": governance_change_supplements,
        "privacy": (
            "Owner-only local projection. This file is Git-ignored and must "
            "not be committed or published."
        ),
    }
    if not valid_private_operations(
        snapshot,
        catalog_generation_id=catalog_generation_id,
        source_revision=source_revision,
    ):
        raise RuntimeError("Private Console operations binding is invalid.")
    serialized = json.dumps(
        snapshot, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/")
    text = (
        "/* Private local projection; never commit or publish. */\n"
        f"window.ARRP_PRIVATE_OPERATIONS={serialized};\n"
    )
    secret_findings = prohibited_secret_findings(
        "framework/project/interfaces/project-console/data/private-operations.js",
        text.encode("utf-8"),
    )
    if secret_findings:
        finding_ids = ",".join(
            str(item.get("finding_id") or "DISC-UNKNOWN")
            for item in secret_findings
        )
        raise RuntimeError(
            "Private Console operations projection contains prohibited secret "
            f"material and was not persisted ({finding_ids})."
        )
    atomic_write_text(PRIVATE_OPERATIONS_OUTPUT, text)
    return snapshot


def require_complete_cli_collection(
    records: object,
    *,
    limit: int,
    source: str,
    reported_total: object = None,
) -> list[dict[str, object]]:
    if not isinstance(records, list):
        raise RuntimeError(f"{source} did not return a JSON array.")
    if len(records) >= limit:
        raise RuntimeError(
            f"{source} reached its explicit {limit}-record ceiling; completeness "
            "cannot be established."
        )
    if reported_total is not None:
        try:
            total = int(reported_total)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"{source} returned an invalid totalCount.") from exc
        if total != len(records):
            raise RuntimeError(
                f"{source} pagination is incomplete: totalCount={total}, "
                f"received={len(records)}."
            )
    return records


def existing_console_payload() -> dict[str, object]:
    """Assemble the compatibility snapshot and normalized Console data parts."""
    if not OUTPUT.exists():
        return {}
    text = OUTPUT.read_text(encoding="utf-8")
    prefix = (
        "/* Generated by scripts/build_project_console.py. */\n"
        "window.ARRP_HORIZON_REVIEW_DATA="
    )
    if not text.startswith(prefix):
        return {}
    try:
        payload = json.loads(text.removeprefix(prefix).removesuffix(";\n"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    part_prefix = (
        "/* Generated by scripts/build_project_console.py. */\n"
        "window.ARRP_HORIZON_REVIEW_DATA=window.ARRP_HORIZON_REVIEW_DATA||{};\n"
        "Object.assign(window.ARRP_HORIZON_REVIEW_DATA,"
    )
    for path in sorted(CONSOLE_DATA_DIR.glob("*.js")):
        if (
            not ALLOW_PRIVATE_CONSOLE_INPUTS
            and (
                path.name.startswith("private-")
                or path.name == "local-automation-status.js"
            )
        ):
            continue
        part_text = path.read_text(encoding="utf-8")
        if not part_text.startswith(part_prefix):
            continue
        try:
            part = json.loads(part_text.removeprefix(part_prefix).removesuffix(");\n"))
        except json.JSONDecodeError:
            continue
        if isinstance(part, dict):
            payload.update(part)
    private_operations = CONSOLE_DATA_DIR / "private-operations.js"
    if ALLOW_PRIVATE_CONSOLE_INPUTS and private_operations.exists():
        private_prefix = (
            "/* Private local projection; never commit or publish. */\n"
            "window.ARRP_PRIVATE_OPERATIONS="
        )
        private_text = private_operations.read_text(encoding="utf-8")
        if private_text.startswith(private_prefix):
            try:
                private_payload = json.loads(
                    private_text.removeprefix(private_prefix).removesuffix(";\n")
                )
            except json.JSONDecodeError:
                private_payload = {}
            if valid_private_operations(
                private_payload,
                catalog_generation_id=str(payload.get("generation_id") or ""),
                source_revision=str(payload.get("source_revision") or ""),
            ):
                for key in ("agent_registry", "project_logs"):
                    payload[key] = private_payload[key]
    source_chunk_keys = sorted(
        key for key in payload if key.startswith("cited_sources_chunk_")
    )
    if source_chunk_keys:
        payload["cited_sources"] = [
            record
            for key in source_chunk_keys
            for record in payload.pop(key, [])
        ]
        payload["cited_sources"].sort(key=lambda record: str(record.get("id", "")))
    directive_chunk_keys = sorted(
        key for key in payload if key.startswith("presidential_directives_chunk_")
    )
    if directive_chunk_keys:
        payload["presidential_directives"] = [
            record
            for key in directive_chunk_keys
            for record in payload.pop(key, [])
        ]
    return payload


def generated_console_part(text: str) -> dict[str, object]:
    marker = "Object.assign(window.ARRP_HORIZON_REVIEW_DATA,"
    if marker not in text:
        return {}
    serialized = text.split(marker, 1)[1].strip()
    if not serialized.endswith(");"):
        return {}
    try:
        payload = json.loads(serialized[:-2])
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


CATALOG_PREFIX = (
    "/* Generated by scripts/build_project_console.py. */\n"
    "window.ARRP_HORIZON_REVIEW_DATA="
)
PART_PREFIX = (
    "/* Generated by scripts/build_project_console.py. */\n"
    "window.ARRP_HORIZON_REVIEW_DATA=window.ARRP_HORIZON_REVIEW_DATA||{};\n"
    "Object.assign(window.ARRP_HORIZON_REVIEW_DATA,"
)
PARTICIPATION_PREFIX = (
    "/* Generated by scripts/build_project_console.py. */\n"
    "window.ARRP_PARTICIPATION_DATA="
)


def serialized_catalog(payload: dict[str, object]) -> str:
    serialized = "{\n" + ",\n".join(
        (
            f"{json.dumps(key, ensure_ascii=False)}:"
            f"{json.dumps(value, ensure_ascii=False, separators=(',', ':'))}"
        )
        for key, value in payload.items()
    ) + "\n}"
    serialized = serialized.replace("</", "<\\/")
    return f"{CATALOG_PREFIX}{serialized};\n"


def serialized_console_part(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2).replace(
        "</", "<\\/"
    )
    return f"{PART_PREFIX}{serialized});\n"


def participation_projection_is_unchanged(
    existing_text: str,
    current_payload: dict[str, object],
) -> bool:
    if not existing_text.startswith(PARTICIPATION_PREFIX) or not existing_text.endswith(";\n"):
        return False
    try:
        existing_payload = json.loads(
            existing_text[len(PARTICIPATION_PREFIX) : -2]
        )
    except json.JSONDecodeError:
        return False
    return (
        isinstance(existing_payload, dict)
        and set(existing_payload)
        == {"schema_version", "generated_at", "proposal_index", "horizon_index"}
        and isinstance(existing_payload.get("generated_at"), str)
        and bool(existing_payload["generated_at"])
        and all(
            existing_payload.get(key) == current_payload[key]
            for key in ("schema_version", "proposal_index", "horizon_index")
        )
    )


def payload_count(value: object) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return sum(payload_count(item) for item in value.values())
    return 0


def component_registry_projection_count(snapshot: dict[str, object]) -> int:
    """Count canonical v4 records once, excluding linked and derived views."""

    if snapshot.get("schema_version") != 4:
        raise RuntimeError("Component Registry projection requires schema 4.")
    records = snapshot.get("records")
    if not isinstance(records, dict) or any(
        not isinstance(value, list) for value in records.values()
    ):
        raise RuntimeError("Component Registry v4 record set is incomplete.")
    return sum(len(value) for value in records.values())


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def validated_local_automation_projection(path: Path) -> str | None:
    """Return a valid ignored local status projection for atomic preservation."""

    if not path.is_file() or path.is_symlink():
        return None
    prefix = "window.ARRP_LOCAL_AUTOMATION_STATUS = "
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if not text.startswith(prefix) or not text.endswith(";\n"):
        return None
    try:
        value = json.loads(text.removeprefix(prefix).removesuffix(";\n"))
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict) or not isinstance(value.get("status"), str):
        return None
    return text


def local_automation_status_snapshot(path: Path) -> dict[str, object]:
    """Read the ignored owner-local status without making it a public authority."""

    text = validated_local_automation_projection(path)
    if text is None:
        return {}
    prefix = "window.ARRP_LOCAL_AUTOMATION_STATUS = "
    value = json.loads(text.removeprefix(prefix).removesuffix(";\n"))
    return value if isinstance(value, dict) else {}


def parsed_utc(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalized_occurrence_stage(
    *,
    stage_id: str,
    label: str,
    source: dict[str, object] | None,
    occurrence_id: str,
    default_status: str = "unavailable",
    default_reason: str = "No stage result was published for this occurrence.",
) -> dict[str, object]:
    raw = source or {}
    status = str(
        raw.get("status")
        or ("not_due" if raw.get("due") is False else default_status)
    ).strip()
    if status not in {
        "pending",
        "running",
        "succeeded",
        "failed",
        "degraded",
        "not_due",
        "skipped",
        "blocked",
        "unavailable",
    }:
        status = "unavailable"
    current_label = (
        "Not due this chain"
        if status == "not_due"
        else str(raw.get("current_chain_label") or status.replace("_", " ").title())
    )
    return {
        "stage_id": stage_id,
        "label": label,
        "order": next(
            index
            for index, (registered_id, _) in enumerate(
                AUTOMATION_OCCURRENCE_STAGE_SPECS, start=1
            )
            if registered_id == stage_id
        ),
        "occurrence_id": occurrence_id,
        "status": status,
        "current_chain_label": current_label,
        "due": raw.get("due"),
        "reason": str(
            raw.get("due_reason")
            or raw.get("details")
            or raw.get("reason")
            or default_reason
        ).strip(),
        "started_at": raw.get("started_at"),
        "completed_at": raw.get("completed_at") or raw.get("updated_at"),
        "prior_success_at": raw.get("last_success_at"),
        "failure_class": raw.get("failure_class"),
        "active_incident_ids": (
            list(raw.get("active_incident_ids") or [])
            if isinstance(raw.get("active_incident_ids"), list)
            else []
        ),
    }


def chain_occurrence(run_chain: dict[str, object]) -> dict[str, object] | None:
    if not run_chain:
        return None
    occurrence_id = str(
        run_chain.get("run_id") or run_chain.get("chain_id") or ""
    ).strip()
    if not occurrence_id:
        return None
    stages_by_id = {
        str(stage.get("id") or stage.get("stage_id") or ""): stage
        for stage in run_chain.get("stages") or []
        if isinstance(stage, dict)
    }
    decision = (
        run_chain.get("elim_decision")
        if isinstance(run_chain.get("elim_decision"), dict)
        else {}
    )
    if decision.get("launched") is True:
        elim_status = (
            "succeeded"
            if decision.get("outcome") in {"succeeded", "completed"}
            else "running"
        )
    elif decision.get("launch_recommended") is True:
        elim_status = "pending"
    elif decision:
        elim_status = "not_due"
    else:
        elim_status = "unavailable"
    stages_by_id["elim"] = {
        "status": elim_status,
        "due": decision.get("launch_recommended"),
        "due_reason": decision.get("reason") or "No Elim decision was published.",
        "completed_at": run_chain.get("completed_at"),
    }
    stages = [
        normalized_occurrence_stage(
            stage_id=stage_id,
            label=label,
            source=stages_by_id.get(stage_id),
            occurrence_id=occurrence_id,
        )
        for stage_id, label in AUTOMATION_OCCURRENCE_STAGE_SPECS
    ]
    blockers = [
        {
            "id": str(
                item.get("id")
                or item.get("failure_id")
                or f"{occurrence_id}-{index}"
            ),
            "stage_id": overview_automation_stage_id(
                item.get("stage") or item.get("stage_id")
            ),
            "reason": str(
                item.get("reason")
                or item.get("message")
                or "Occurrence blocker recorded without safe detail."
            ),
            "recorded_at": item.get("recorded_at") or run_chain.get("updated_at"),
        }
        for index, item in enumerate(run_chain.get("failures") or [], start=1)
        if isinstance(item, dict)
    ]
    return {
        "occurrence_id": occurrence_id,
        "schedule_identity": (
            str(run_chain.get("schedule_identity") or "")
            or (
                "owner-local-nightly"
                if re.search(
                    r"schedule|launchd|nightly",
                    str(run_chain.get("trigger") or ""),
                    re.IGNORECASE,
                )
                else "event-driven"
            )
        ),
        "trigger": run_chain.get("trigger"),
        "status": run_chain.get("status") or "unavailable",
        "source_revision": (
            run_chain.get("final_revision") or run_chain.get("baseline_commit")
        ),
        "generation_id": run_chain.get("generation_id"),
        "created_at": run_chain.get("created_at"),
        "started_at": run_chain.get("started_at") or run_chain.get("created_at"),
        "completed_at": run_chain.get("completed_at"),
        "updated_at": run_chain.get("updated_at"),
        "scheduled_for": run_chain.get("scheduled_for"),
        "stages": stages,
        "blockers": blockers,
        "complete": len(stages) == len(AUTOMATION_OCCURRENCE_STAGE_SPECS),
    }


def local_status_occurrence(
    local_status: dict[str, object],
) -> dict[str, object] | None:
    if not local_status:
        return None
    occurrence_id = str(local_status.get("run_id") or "").strip()
    if not occurrence_id:
        return None
    validation = (
        local_status.get("validation_summary")
        if isinstance(local_status.get("validation_summary"), dict)
        else {}
    )
    no_run_reason = str(validation.get("reason") or "").strip()
    duplicate_claim = no_run_reason == "scheduled_slot_already_claimed"
    default_status = "not_due" if duplicate_claim else "unavailable"
    default_reason = (
        "The scheduled slot was already claimed; no duplicate chain was run."
        if duplicate_claim
        else "The owner-local status did not publish stage-level results."
    )
    stages = [
        normalized_occurrence_stage(
            stage_id=stage_id,
            label=label,
            source=None,
            occurrence_id=occurrence_id,
            default_status=default_status,
            default_reason=default_reason,
        )
        for stage_id, label in AUTOMATION_OCCURRENCE_STAGE_SPECS
    ]
    raw_status = str(local_status.get("status") or "unavailable")
    occurrence_status = "not_due" if duplicate_claim else raw_status
    blockers = []
    if occurrence_status in {"failed", "blocked", "usage-stopped", "missed"}:
        blockers.append(
            {
                "id": f"{occurrence_id}-local-status",
                "stage_id": None,
                "reason": str(
                    local_status.get("failure_reason")
                    or "The owner-local occurrence did not complete successfully."
                ),
                "recorded_at": local_status.get("updated_at"),
            }
        )
    return {
        "occurrence_id": occurrence_id,
        "schedule_identity": (
            "owner-local-nightly"
            if re.search(
                r"schedule|launchd|nightly",
                str(local_status.get("trigger") or ""),
                re.IGNORECASE,
            )
            else "event-driven"
        ),
        "trigger": local_status.get("trigger"),
        "status": occurrence_status,
        "source_revision": (
            local_status.get("runtime_commit")
            or local_status.get("starting_local_head")
        ),
        "generation_id": None,
        "created_at": local_status.get("started_at"),
        "started_at": local_status.get("started_at"),
        "completed_at": local_status.get("completed_at"),
        "updated_at": local_status.get("updated_at"),
        "scheduled_for": local_status.get("scheduled_for"),
        "stages": stages,
        "blockers": blockers,
        "complete": True,
        "control_state": local_status.get("control_state"),
        "control_state_checked_at": local_status.get("control_state_checked_at"),
    }


def next_local_schedule(
    after: datetime,
    *,
    local_time: str = "02:00",
    time_zone: str = "America/New_York",
) -> datetime:
    hour_text, minute_text = local_time.split(":", 1)
    local_zone = ZoneInfo(time_zone)
    local_after = after.astimezone(local_zone)
    candidate = local_after.replace(
        hour=int(hour_text),
        minute=int(minute_text),
        second=0,
        microsecond=0,
    )
    if candidate <= local_after:
        candidate += timedelta(days=1)
    return candidate.astimezone(timezone.utc)


def automation_occurrence_projection(
    run_chain: dict[str, object],
    local_status: dict[str, object],
    *,
    checked_at: str,
) -> dict[str, object]:
    """Build one typed occurrence directory without mixing exact runs."""

    checked = parsed_utc(checked_at) or datetime.now(timezone.utc)
    chain_item = chain_occurrence(run_chain)
    local_item = local_status_occurrence(local_status)
    if (
        chain_item is not None
        and local_item is not None
        and chain_item["occurrence_id"] == local_item["occurrence_id"]
    ):
        duplicate_claim = (
            isinstance(local_status.get("validation_summary"), dict)
            and local_status["validation_summary"].get("reason")
            == "scheduled_slot_already_claimed"
        )
        if duplicate_claim:
            occurrences = [local_item]
        else:
            chain_item = {
                **chain_item,
                "status": local_item.get("status") or chain_item.get("status"),
                "started_at": (
                    local_item.get("started_at") or chain_item.get("started_at")
                ),
                "completed_at": (
                    local_item.get("completed_at")
                    or chain_item.get("completed_at")
                ),
                "updated_at": (
                    local_item.get("updated_at") or chain_item.get("updated_at")
                ),
                "control_state": local_item.get("control_state"),
                "control_state_checked_at": local_item.get(
                    "control_state_checked_at"
                ),
            }
            occurrences = [chain_item]
    else:
        occurrences = [
            item for item in (chain_item, local_item) if item is not None
        ]
    occurrences.sort(
        key=lambda item: (
            parsed_utc(
                item.get("scheduled_for")
                or item.get("started_at")
                or item.get("updated_at")
            )
            or datetime.min.replace(tzinfo=timezone.utc)
        ),
        reverse=True,
    )
    latest = occurrences[0] if occurrences else None
    latest_scheduled = next(
        (
            item
            for item in occurrences
            if item.get("schedule_identity") == "owner-local-nightly"
        ),
        None,
    )
    explicit_full_success = (
        run_chain.get("last_fully_successful_occurrence")
        if isinstance(run_chain.get("last_fully_successful_occurrence"), dict)
        else None
    )
    local_checked_at = parsed_utc(
        local_status.get("updated_at")
        or local_status.get("completed_at")
        or local_status.get("started_at")
    )
    valid_until = (
        local_checked_at + timedelta(hours=36)
        if local_checked_at is not None
        else None
    )
    currentness = (
        "current"
        if valid_until is not None and valid_until >= checked
        else "stale"
        if valid_until is not None
        else "unavailable"
    )
    config = json.loads(RUN_COORDINATOR_CONFIG.read_text(encoding="utf-8"))
    schedule = config.get("schedule") or {}
    next_run = next_local_schedule(
        checked,
        local_time=str(schedule.get("localTime") or "02:00"),
        time_zone=str(schedule.get("timeZone") or "America/New_York"),
    )
    epoch = (
        run_chain.get("review_epoch")
        if isinstance(run_chain.get("review_epoch"), dict)
        else {}
    )
    epoch_due = parsed_utc(epoch.get("next_due_at"))
    next_epoch = (
        next_local_schedule(
            epoch_due - timedelta(seconds=1),
            local_time=str(schedule.get("localTime") or "02:00"),
            time_zone=str(schedule.get("timeZone") or "America/New_York"),
        )
        if epoch_due is not None
        else None
    )
    return {
        "schema_version": 2,
        "checked_at": checked_at,
        "occurrences": occurrences,
        "latest_attempt_id": latest.get("occurrence_id") if latest else None,
        "latest_scheduled_attempt_id": (
            latest_scheduled.get("occurrence_id") if latest_scheduled else None
        ),
        "last_fully_successful_occurrence": explicit_full_success,
        "next_ordinary_run": {
            "available": True,
            "scheduled_for": next_run.isoformat(),
            "schedule_identity": "owner-local-nightly",
        },
        "next_full_review_epoch": {
            "available": next_epoch is not None,
            "scheduled_for": next_epoch.isoformat() if next_epoch else None,
            "epoch_id": epoch.get("epoch_id") or epoch.get("review_id"),
            "reason": (
                ""
                if next_epoch is not None
                else "No typed next Review Epoch is published."
            ),
        },
        "role_currentness": {
            "state": currentness,
            "checked_at": (
                local_checked_at.isoformat() if local_checked_at else None
            ),
            "valid_until": valid_until.isoformat() if valid_until else None,
        },
        "trustworthy_through": (
            local_checked_at.isoformat() if local_checked_at else None
        ),
    }


def write_console_bundle(
    compatibility_payload: dict[str, object],
    parts: dict[str, dict[str, object]],
    *,
    generation_contract: dict[str, object],
    output: Path | None = None,
    data_dir: Path | None = None,
) -> dict[str, object]:
    """Stage, validate, hash, and atomically replace one Console data generation."""
    output = output or OUTPUT
    data_dir = data_dir or CONSOLE_DATA_DIR
    generation_id_value = str(generation_contract.get("generation_id") or "")
    if not generation_id_value:
        raise RuntimeError("Console bundle generation lacks a generation_id.")
    output.parent.mkdir(parents=True, exist_ok=True)
    local_status_text = (
        validated_local_automation_projection(
            data_dir / "local-automation-status.js"
        )
        if ALLOW_PRIVATE_CONSOLE_INPUTS
        else None
    )
    stage_root = Path(
        tempfile.mkdtemp(prefix=".console-generation-", dir=output.parent)
    )
    stage_data = stage_root / "data"
    stage_data.mkdir()
    try:
        domain_records: list[dict[str, object]] = []
        for name, original_part in sorted(parts.items()):
            if Path(name).name != name or not name.endswith(".js"):
                raise RuntimeError(f"Unsafe Console domain filename: {name}")
            part = {
                **original_part,
                "domain_generation": {name: generation_id_value},
            }
            text = serialized_console_part(part)
            path = stage_data / name
            path.write_text(text, encoding="utf-8")
            parsed = generated_console_part(text)
            if parsed != part:
                raise RuntimeError(f"Generated Console domain failed readback: {name}")
            domain_records.append(
                {
                    "file": name,
                    "sha256": file_sha256(stage_data, path),
                    "bytes": path.stat().st_size,
                    "keys": sorted(original_part),
                    "record_count": payload_count(original_part),
                }
            )
        manifest = {
            "manifest_schema_version": 1,
            "generation_id": generation_id_value,
            "generated_at": generation_contract.get("generated_at"),
            "source_revision": generation_contract.get("source_revision"),
            "availability": generation_contract.get("availability"),
            "completeness": generation_contract.get("completeness"),
            "domain_count": len(domain_records),
            "domains": domain_records,
            "files": {
                str(domain["file"]): {
                    "generation_id": generation_id_value,
                    "sha256": domain["sha256"],
                    "bytes": domain["bytes"],
                    "keys": domain["keys"],
                    "record_count": domain["record_count"],
                }
                for domain in domain_records
            },
        }
        manifest_path = stage_data / "generation-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        for domain in domain_records:
            path = stage_data / str(domain["file"])
            if file_sha256(stage_data, path) != domain["sha256"]:
                raise RuntimeError(
                    f"Generated Console domain hash failed readback: {domain['file']}"
                )
        staged_compatibility = {
            **compatibility_payload,
            **generation_contract,
            "generation_manifest": manifest,
        }
        stage_catalog = stage_root / output.name
        stage_catalog.write_text(
            serialized_catalog(staged_compatibility), encoding="utf-8"
        )
        catalog_payload = json.loads(
            stage_catalog.read_text(encoding="utf-8")
            .removeprefix(CATALOG_PREFIX)
            .removesuffix(";\n")
        )
        if catalog_payload.get("generation_id") != generation_id_value:
            raise RuntimeError("Generated Console catalog failed generation readback.")
        try:
            require_outbound_bundle(
                [
                    OutboundArtifact(
                        path=(
                            f"framework/project/interfaces/project-console/data/{path.name}"
                            if path.parent == stage_data
                            else "framework/project/interfaces/project-console/catalog-data.js"
                        ),
                        producer="console-public-bundle",
                        content=path.read_bytes(),
                        artifact_group=f"console-generation:{generation_id_value}",
                    )
                    for path in [stage_catalog, *sorted(stage_data.iterdir())]
                    if path.is_file()
                ],
                operation="console_public_bundle",
                source_revision=generation_id_value,
                complete=True,
            )
        except DisclosureBlocked as error:
            raise RuntimeError(str(error)) from error

        prior_data = stage_root / "prior-data"
        prior_catalog = stage_root / "prior-catalog.js"
        if not ALLOW_PRIVATE_CONSOLE_INPUTS:
            prior_data.mkdir()
            installed_public: list[Path] = []
            catalog_replaced = False
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
                for existing in sorted(data_dir.iterdir()):
                    if (
                        not existing.is_file()
                        or existing.name.startswith("private-")
                        or existing.name == "local-automation-status.js"
                    ):
                        continue
                    os.replace(existing, prior_data / existing.name)
                for staged in sorted(stage_data.iterdir()):
                    destination = data_dir / staged.name
                    os.replace(staged, destination)
                    installed_public.append(destination)
                if output.exists():
                    os.replace(output, prior_catalog)
                os.replace(stage_catalog, output)
                catalog_replaced = True
            except Exception:
                failed_data = stage_root / "failed-new-data"
                failed_data.mkdir(exist_ok=True)
                if catalog_replaced and output.exists():
                    os.replace(output, stage_root / "failed-new-catalog.js")
                if prior_catalog.exists():
                    os.replace(prior_catalog, output)
                for installed in installed_public:
                    if installed.exists():
                        os.replace(installed, failed_data / installed.name)
                for prior in sorted(prior_data.iterdir()):
                    os.replace(prior, data_dir / prior.name)
                raise
            return manifest
        data_replaced = False
        catalog_replaced = False
        try:
            if data_dir.exists():
                os.replace(data_dir, prior_data)
            os.replace(stage_data, data_dir)
            data_replaced = True
            if local_status_text is not None:
                local_status_path = data_dir / "local-automation-status.js"
                atomic_write_text(local_status_path, local_status_text)
                os.chmod(local_status_path, 0o600)
            if output.exists():
                os.replace(output, prior_catalog)
            os.replace(stage_catalog, output)
            catalog_replaced = True
        except Exception:
            if catalog_replaced and output.exists():
                output.unlink()
            if prior_catalog.exists():
                os.replace(prior_catalog, output)
            if data_replaced and data_dir.exists():
                rollback_new = stage_root / "failed-new-data"
                os.replace(data_dir, rollback_new)
            if prior_data.exists():
                os.replace(prior_data, data_dir)
            raise
        return manifest
    finally:
        if ALLOW_PRIVATE_CONSOLE_INPUTS:
            shutil.rmtree(stage_root, ignore_errors=True)


def snapshot_time(payload: dict[str, object]) -> datetime:
    candidates = [payload]
    current = payload.get("current")
    if isinstance(current, dict):
        candidates.append(current)
    for candidate in candidates:
        for field in ("generatedAt", "generated_at", "checked_at", "asOf", "as_of"):
            raw = str(candidate.get(field) or "").strip()
            if not raw:
                continue
            try:
                return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(
                    timezone.utc
                )
            except ValueError:
                continue
    return datetime.min.replace(tzinfo=timezone.utc)


PRODUCER_CONTRACT_FIELDS = (
    "contract_schema_version",
    "generation_id",
    "source_revision",
    "expected_count",
    "actual_count",
    "source_hashes",
    "availability",
    "completeness",
    "pagination",
    "projection_errors",
    "freshness",
)


def snapshot_contract_view(payload: dict[str, object]) -> dict[str, object]:
    """Return the producer contract, distinct from later currentness overlays."""
    producer = payload.get("producer_contract")
    if not isinstance(producer, dict):
        return payload
    return {**payload, **producer}


def declared_snapshot_revision(payload: dict[str, object]) -> str:
    contract = snapshot_contract_view(payload)
    revision = str(
        contract.get("source_revision")
        or contract.get("revision")
        or ""
    ).strip()
    current = payload.get("current")
    if not revision and isinstance(current, dict):
        revision = str(
            current.get("source_revision")
            or current.get("revision")
            or ""
        ).strip()
    return revision


def valid_snapshot(
    payload: object,
    *,
    timestamp_fields: tuple[str, ...],
    required_fields: tuple[str, ...] = (),
) -> bool:
    if not isinstance(payload, dict):
        return False
    if not all(field in payload for field in required_fields):
        return False
    contract = snapshot_contract_view(payload)
    if "generation_id" in contract:
        completeness = contract.get("completeness")
        if not isinstance(completeness, dict) or completeness.get("complete") is not True:
            return False
    return validate_contract(
        contract,
        timestamp_fields=timestamp_fields,
        allow_legacy=True,
    ) or (
        isinstance(payload.get("current"), dict)
        and validate_contract(
            payload["current"],
            timestamp_fields=timestamp_fields,
            allow_legacy=True,
        )
    )


def newest_snapshot(
    candidates: list[dict[str, object]],
    *,
    authority: str = "generation",
    expected_revision: str | None = None,
) -> dict[str, object]:
    """Select by the feed owner rather than treating every HEAD as authority.

    ``generation`` is used for authenticated Project synchronizations,
    ``repository_revision`` for repository-bound integrity output, and
    ``catalog`` for Source Checker generations projected against current
    catalog identity and hashes.
    """
    if not candidates:
        return {}
    if authority not in {"generation", "repository_revision", "catalog"}:
        raise ValueError(f"Unknown snapshot authority: {authority}")
    expected = (
        (expected_revision or source_revision(ROOT)).strip()
        if authority == "repository_revision"
        else ""
    )

    def revision_epoch(revision: str) -> int:
        if not revision:
            return 0
        completed = subprocess.run(
            ["git", "show", "-s", "--format=%ct", revision],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        try:
            return int(completed.stdout.strip()) if completed.returncode == 0 else 0
        except ValueError:
            return 0

    def completeness_rank(payload: dict[str, object]) -> int:
        completeness = snapshot_contract_view(payload).get("completeness")
        if isinstance(completeness, dict):
            return 2 if completeness.get("complete") is True else 0
        return 1

    def key(payload: dict[str, object]) -> tuple[object, ...]:
        revision = declared_snapshot_revision(payload)
        contract = snapshot_contract_view(payload)
        deterministic_identity = str(contract.get("generation_id") or "")
        if not deterministic_identity:
            deterministic_identity = hashlib.sha256(
                json.dumps(
                    payload, sort_keys=True, separators=(",", ":"), default=str
                ).encode("utf-8")
            ).hexdigest()
        common = (
            completeness_rank(payload),
            snapshot_time(payload),
            deterministic_identity,
        )
        if authority == "repository_revision":
            return (
                int(bool(expected and revision == expected)),
                completeness_rank(payload),
                revision_epoch(revision),
                snapshot_time(payload),
                deterministic_identity,
            )
        if authority == "catalog":
            coverage = payload.get("current_catalog_coverage")
            return (
                int(
                    isinstance(coverage, dict)
                    and coverage.get("complete") is True
                ),
                *common,
            )
        return common

    return max(candidates, key=key)


def with_repository_revision_currentness(
    payload: dict[str, object],
    *,
    expected_revision: str,
) -> dict[str, object]:
    """Overlay repository-authority currentness without changing producer validity."""
    if not payload:
        return {}
    projected = dict(payload)
    expected = expected_revision.strip()
    declared = declared_snapshot_revision(payload)
    freshness = dict(projected.get("freshness") or {})
    equivalent = integrity_parent_output_equivalent(
        declared,
        expected,
        root=ROOT,
    )
    current = bool(expected and (declared == expected or equivalent))
    status = "current" if current else "stale" if expected and declared else "unavailable"
    projected["currentness"] = {
        "authority": "repository_revision",
        "status": status,
        "current": current,
        "expected_source_revision": expected or None,
        "producer_source_revision": declared or None,
        "equivalent_inputs_established": equivalent,
        "supersession_rule": (
            "A different authoritative repository revision supersedes this "
            "integrity generation immediately, regardless of elapsed time."
        ),
    }
    producer_availability = snapshot_contract_view(payload).get("availability")
    if current:
        projected["availability"] = (
            str(producer_availability)
            if str(producer_availability or "") in {"current", "available"}
            else "current"
        )
    if not current:
        projected["producer_availability"] = producer_availability
        projected["availability"] = status
        errors = [
            error
            for error in projected.get("projection_errors") or []
            if isinstance(error, dict)
            and error.get("code") != "repository_revision_superseded"
        ]
        errors.append(
            {
                "code": "repository_revision_superseded",
                "severity": "warning",
                "message": (
                    "Integrity generation is not bound to the authoritative "
                    "repository revision."
                    if status == "stale"
                    else "Integrity currentness cannot be established."
                ),
                "expected_source_revision": expected or None,
                "producer_source_revision": declared or None,
            }
        )
        projected["projection_errors"] = errors
    freshness.update(
        {
            "status": status,
            "basis": "authoritative repository revision",
            "supersession_rule": projected["currentness"]["supersession_rule"],
        }
    )
    projected["freshness"] = freshness
    return projected


def _git_console_text(
    root: Path,
    arguments: list[str],
) -> str | None:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout if completed.returncode == 0 else None


def _committed_console_manifest_paths(
    root: Path,
    revision: str,
) -> set[str] | None:
    text = _git_console_text(
        root,
        ["show", f"{revision}:{CONSOLE_GENERATION_MANIFEST_PATH}"],
    )
    if text is None:
        return None
    try:
        manifest = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(manifest, dict):
        return None
    domains = manifest.get("domains")
    files = manifest.get("files")
    completeness = manifest.get("completeness")
    if (
        manifest.get("manifest_schema_version") != 1
        or not str(manifest.get("generation_id") or "").strip()
        or manifest.get("availability") != "current"
        or not isinstance(completeness, dict)
        or completeness.get("complete") is not True
        or not isinstance(domains, list)
        or not isinstance(files, dict)
        or manifest.get("domain_count") != len(domains)
    ):
        return None
    names: list[str] = []
    for record in domains:
        name = str(record.get("file") or "") if isinstance(record, dict) else ""
        if (
            not name
            or Path(name).name != name
            or not name.endswith(".js")
            or name.startswith("private-")
            or name == "local-automation-status.js"
            or not isinstance(files.get(name), dict)
            or files[name].get("sha256") != record.get("sha256")
        ):
            return None
        names.append(name)
    if len(names) != len(set(names)) or set(files) != set(names):
        return None
    prefix = CONSOLE_GENERATION_MANIFEST_PATH.rsplit("/", 1)[0]
    paths = {f"{prefix}/{name}" for name in names}
    tree = _git_console_text(
        root,
        ["ls-tree", revision, "--", *sorted(paths)],
    )
    if tree is None:
        return None
    observed: set[str] = set()
    for line in tree.splitlines():
        metadata, separator, path = line.partition("\t")
        fields = metadata.split()
        if (
            not separator
            or len(fields) != 3
            or fields[0] not in {"100644", "100755"}
            or fields[1] != "blob"
            or path not in paths
        ):
            return None
        observed.add(path)
    return paths if observed == paths else None


def integrity_parent_output_equivalent(
    producer_revision: str,
    expected_revision: str,
    *,
    root: Path = ROOT,
) -> bool:
    """Accept one exact generated-output child without trusting caller claims."""

    producer = producer_revision.strip()
    expected = expected_revision.strip()
    if (
        re.fullmatch(r"[0-9a-f]{40}", producer) is None
        or re.fullmatch(r"[0-9a-f]{40}", expected) is None
        or producer == expected
    ):
        return False
    try:
        if current_repository_head(root) != expected:
            return False
    except RuntimeError:
        return False
    ancestry = _git_console_text(
        root,
        ["rev-list", "--parents", "-n", "1", expected],
    )
    if ancestry is None or ancestry.strip().split() != [expected, producer]:
        return False
    parent_paths = _committed_console_manifest_paths(root, producer)
    current_paths = _committed_console_manifest_paths(root, expected)
    if parent_paths is None or current_paths is None:
        return False
    changed_text = _git_console_text(
        root,
        ["diff", "--name-only", "--no-renames", "-z", producer, expected, "--"],
    )
    if changed_text is None:
        return False
    changed = {path for path in changed_text.split("\0") if path}
    allowed = {
        CONSOLE_GENERATION_CATALOG_PATH,
        CONSOLE_GENERATION_MANIFEST_PATH,
        *CONSOLE_GENERATION_REPORT_PATHS,
        *parent_paths,
        *current_paths,
    }
    return bool(changed) and changed <= allowed


def with_project_generation_currentness(
    payload: dict[str, object],
) -> dict[str, object]:
    """Describe Project currentness using the latest complete synchronization."""
    if not payload:
        return {}
    projected = dict(payload)
    contract = snapshot_contract_view(payload)
    complete = (
        isinstance(contract.get("completeness"), dict)
        and contract["completeness"].get("complete") is True
    )
    contract_declared = bool(
        str(contract.get("generation_id") or "").strip()
        and isinstance(contract.get("completeness"), dict)
    )
    status = (
        str(contract.get("availability") or "current")
        if complete and contract_declared
        else "stale"
        if contract_declared
        else "unavailable"
    )
    projected["availability"] = status
    projected["currentness"] = {
        "authority": "authenticated_project_generation",
        "status": status,
        "current": (
            contract_declared
            and complete
            and status in {"current", "available"}
        ),
        "generation_id": contract.get("generation_id"),
        "synchronized_at": (
            payload.get("generatedAt")
            or payload.get("generated_at")
            or payload.get("asOf")
            or payload.get("as_of")
        ),
        "supersession_rule": (
            "A newer complete authenticated Project synchronization supersedes "
            "an older generation; repository HEAD alone does not."
        ),
    }
    return projected


def read_trusted_snapshot_file(
    raw_path: str,
    *,
    environment_name: str,
) -> dict[str, object]:
    """Read one JSON snapshot from its fixed repository staging location."""
    relative_path = SNAPSHOT_OVERRIDE_PATHS.get(environment_name)
    if relative_path is None:
        raise RuntimeError(f"{environment_name} is not an approved snapshot override.")
    trusted_path = os.path.realpath(os.fspath(ROOT / relative_path))
    full_path = os.path.realpath(raw_path)
    if full_path != trusted_path:
        raise RuntimeError(
            f"{environment_name} must select its fixed repository staging file "
            f"{relative_path.as_posix()}."
        )
    if not os.path.isfile(trusted_path):
        raise RuntimeError(
            f"{environment_name} must select an existing regular JSON snapshot."
        )
    try:
        with open(trusted_path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"{environment_name} explicitly selected an unreadable snapshot."
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"{environment_name} explicitly selected a non-object snapshot."
        )
    return payload


def read_snapshot_override(
    environment_name: str,
    *,
    timestamp_fields: tuple[str, ...],
    required_fields: tuple[str, ...] = (),
) -> dict[str, object] | None:
    raw_path = os.environ.get(environment_name, "").strip()
    if not raw_path:
        return None
    payload = read_trusted_snapshot_file(
        raw_path,
        environment_name=environment_name,
    )
    if not valid_snapshot(
        payload,
        timestamp_fields=timestamp_fields,
        required_fields=required_fields,
    ):
        raise RuntimeError(
            f"{environment_name} explicitly selected an invalid snapshot."
        )
    return payload


def tracked_progress_snapshot() -> dict[str, object]:
    """Recover the committed Console progress snapshot."""
    relative = (CONSOLE_DATA_DIR / "progress.js").relative_to(ROOT).as_posix()
    completed = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return {}
    part = generated_console_part(completed.stdout)
    payload = part.get("progress", {})
    return payload if isinstance(payload, dict) else {}


def apply_progress_navigation_overlay(
    payload: dict[str, object],
    *,
    registry_path: Path | None = None,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Reconcile projected links without altering the producer truth contract."""
    if not payload:
        return {}
    registry = registry_path or ISSUE_REGISTRY
    root = repository_root or ROOT
    rows = read_csv(registry)

    indices: dict[str, dict[str, int | None]] = {
        "number": {},
        "url": {},
        "identifier": {},
    }

    def add_identity(kind: str, value: str, position: int) -> None:
        if not value:
            return
        current = indices[kind].get(value)
        if current is None and value not in indices[kind]:
            indices[kind][value] = position
        elif current != position:
            indices[kind][value] = None

    def issue_number(value: object) -> str:
        raw = str(value or "").strip()
        return str(int(raw)) if raw.isdigit() else ""

    def issue_url(value: object) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        parsed = urllib.parse.urlsplit(raw)
        if not parsed.scheme or not parsed.netloc:
            return ""
        return urllib.parse.urlunsplit(
            (
                parsed.scheme.casefold(),
                parsed.netloc.casefold(),
                parsed.path.rstrip("/").casefold(),
                "",
                "",
            )
        )

    def identifier(value: object) -> str:
        return " ".join(str(value or "").strip().casefold().split())

    for position, row in enumerate(rows):
        add_identity("number", issue_number(row.get("GitHub Number")), position)
        add_identity("url", issue_url(row.get("GitHub Issue")), position)
        add_identity("identifier", identifier(row.get("Object ID")), position)

    replacement_count = 0
    projected = dict(payload)
    for collection_name in (
        "proposals",
        "candidates",
        "backlog",
        "delivery_items",
    ):
        collection = payload.get(collection_name)
        if not isinstance(collection, list):
            continue
        reconciled: list[object] = []
        for item in collection:
            if not isinstance(item, dict):
                reconciled.append(item)
                continue
            record_number = issue_number(item.get("number"))
            if not record_number:
                identity_match = re.search(
                    r"#(\d+)$", str(item.get("issueIdentity") or "").strip()
                )
                record_number = (
                    issue_number(identity_match.group(1)) if identity_match else ""
                )
            identity_values = (
                ("number", record_number),
                ("url", issue_url(item.get("url"))),
                ("identifier", identifier(item.get("identifier"))),
            )
            matched_positions = {
                position
                for kind, value in identity_values
                if value
                for position in (indices[kind].get(value),)
                if position is not None
            }
            if len(matched_positions) != 1:
                reconciled.append(item)
                continue
            row = rows[matched_positions.pop()]
            canonical_record = str(row.get("Canonical Record") or "").strip()
            item_changed = False
            if (
                canonical_record
                and canonical_record != str(item.get("canonicalRecord") or "").strip()
            ):
                item = {**item, "canonicalRecord": canonical_record}
                item_changed = True
            links = item.get("links")
            if (
                canonical_record
                and isinstance(links, dict)
                and "canonical" in links
                and canonical_record != str(links.get("canonical") or "").strip()
            ):
                item = {
                    **item,
                    "links": {**links, "canonical": canonical_record},
                }
                item_changed = True
            if item_changed:
                replacement_count += 1
            reconciled.append(item)
        projected[collection_name] = reconciled

    source_label = registry.resolve().relative_to(root.resolve()).as_posix()
    projected["local_navigation_overlay"] = {
        "source": source_label,
        "source_hash": file_sha256(root, registry),
        "replacement_count": replacement_count,
    }
    return projected


def progress_snapshot() -> dict[str, object]:
    """Read the latest generated progress data without making it authoritative."""
    override = read_snapshot_override(
        "ARRP_PROGRESS_SNAPSHOT",
        timestamp_fields=("generatedAt", "generated_at", "asOf", "as_of"),
        required_fields=("metrics",),
    )
    if override is not None:
        return apply_progress_navigation_overlay(
            with_project_generation_currentness(override)
        )
    candidates: list[dict[str, object]] = []
    tracked = tracked_progress_snapshot()
    if valid_snapshot(
        tracked,
        timestamp_fields=("generatedAt", "generated_at", "asOf", "as_of"),
        required_fields=("metrics",),
    ):
        candidates.append(tracked)
    existing = existing_console_payload()
    cached = existing.get("progress", existing.get("progress_dashboard", {}))
    if valid_snapshot(
        cached,
        timestamp_fields=("generatedAt", "generated_at", "asOf", "as_of"),
        required_fields=("metrics",),
    ):
        candidates.append(cached)
    return apply_progress_navigation_overlay(
        with_project_generation_currentness(
            newest_snapshot(candidates, authority="generation")
        )
    )


def integrity_snapshot() -> dict[str, object]:
    """Read the latest generated integrity feed without making it authoritative."""
    expected_revision = source_revision(ROOT)
    override = read_snapshot_override(
        "ARRP_INTEGRITY_SNAPSHOT",
        timestamp_fields=("generated_at",),
        required_fields=("current", "history"),
    )
    if override is not None:
        return with_repository_revision_currentness(
            override,
            expected_revision=expected_revision,
        )
    candidates: list[dict[str, object]] = []
    if LOCAL_INTEGRITY_FEED.exists():
        try:
            payload = json.loads(LOCAL_INTEGRITY_FEED.read_text(encoding="utf-8"))
            if valid_snapshot(
                payload,
                timestamp_fields=("generated_at",),
                required_fields=("current", "history"),
            ):
                candidates.append(payload)
        except (OSError, json.JSONDecodeError):
            pass
    existing = existing_console_payload()
    cached = existing.get("integrity", {})
    if valid_snapshot(
        cached,
        timestamp_fields=("generated_at",),
        required_fields=("current", "history"),
    ):
        candidates.append(cached)
    return with_repository_revision_currentness(
        newest_snapshot(
            candidates,
            authority="repository_revision",
            expected_revision=expected_revision,
        ),
        expected_revision=expected_revision,
    )


def successful_run_chain_stages(
    *snapshots: dict[str, object],
) -> list[dict[str, object]]:
    """Retain the newest known successful execution for each automation stage."""
    latest: dict[str, dict[str, object]] = {}
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        stage_groups = [
            snapshot.get("stages", []),
            snapshot.get("last_successful_stages", []),
        ]
        for stages in stage_groups:
            if not isinstance(stages, list):
                continue
            for stage in stages:
                if not isinstance(stage, dict):
                    continue
                stage_id = str(stage.get("id") or stage.get("stage_id") or "").strip()
                succeeded_at = str(
                    stage.get("last_success_at")
                    or (
                        stage.get("completed_at")
                        if re.search(
                            r"success|succeed|complete|healthy|pass",
                            str(stage.get("status") or ""),
                            re.IGNORECASE,
                        )
                        else ""
                    )
                    or ""
                ).strip()
                if not stage_id or not succeeded_at:
                    continue
                candidate = {
                    **stage,
                    "id": stage_id,
                    "status": "succeeded",
                    "last_success_at": succeeded_at,
                }
                existing = latest.get(stage_id)
                try:
                    candidate_time = datetime.fromisoformat(
                        succeeded_at.replace("Z", "+00:00")
                    ).astimezone(timezone.utc)
                except ValueError:
                    candidate_time = datetime.min.replace(tzinfo=timezone.utc)
                try:
                    existing_time = (
                        datetime.fromisoformat(
                            str(existing.get("last_success_at") or "").replace(
                                "Z", "+00:00"
                            )
                        ).astimezone(timezone.utc)
                        if existing
                        else datetime.min.replace(tzinfo=timezone.utc)
                    )
                except ValueError:
                    existing_time = datetime.min.replace(tzinfo=timezone.utc)
                if existing is None or candidate_time >= existing_time:
                    latest[stage_id] = candidate
    return sorted(latest.values(), key=lambda stage: str(stage["id"]))


def normalize_run_chain_paths(value: object) -> object:
    """Map retired repository paths in operational projections to live records."""
    if isinstance(value, list):
        return [normalize_run_chain_paths(item) for item in value]
    if not isinstance(value, dict):
        return value
    normalized: dict[str, object] = {}
    for key, item in value.items():
        if key == "canonical_detail" and isinstance(item, str):
            normalized[key] = LEGACY_RUN_CHAIN_PATHS.get(item, item)
        else:
            normalized[key] = normalize_run_chain_paths(item)
    return normalized


def strip_local_run_chain_metadata(value: object) -> object:
    """Remove host-only paths from a tracked Console projection."""
    if isinstance(value, list):
        return [strip_local_run_chain_metadata(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: strip_local_run_chain_metadata(item)
        for key, item in value.items()
        if key not in LOCAL_RUN_CHAIN_PATH_FIELDS
    }


def public_run_chain_projection(payload: dict[str, object]) -> dict[str, object]:
    """Project local chain state without publishing host control or usage state."""
    normalized = normalize_run_chain_paths(payload)
    if not isinstance(normalized, dict):
        return {}
    projection = {
        key: strip_local_run_chain_metadata(value)
        for key, value in normalized.items()
        if key in PUBLIC_RUN_CHAIN_FIELDS
    }
    usage = projection.get("usage")
    if isinstance(usage, dict):
        projection["usage"] = public_usage_projection(usage)
    return projection


def run_chain_snapshot() -> dict[str, object]:
    """Read the latest generated run-chain state without making it authoritative."""
    local_chain = os.environ.get("ARRP_RUN_CHAIN_SNAPSHOT", "").strip()
    candidates = [Path(local_chain)] if local_chain else [LOCAL_RUN_CHAIN_FEED]
    for path in candidates:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                history_sources = [payload]
                existing = existing_console_payload().get("run_chain", {})
                if isinstance(existing, dict):
                    history_sources.append(existing)
                payload = dict(payload)
                payload["last_successful_stages"] = successful_run_chain_stages(
                    *history_sources
                )
                return public_run_chain_projection(payload)
        except (OSError, json.JSONDecodeError):
            pass
    existing = existing_console_payload()
    cached = existing.get("run_chain", {})
    return (
        public_run_chain_projection(cached)
        if isinstance(cached, dict)
        else {}
    )


def current_repository_head(root: Path = ROOT) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    revision = completed.stdout.strip()
    if completed.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("The current repository revision is unavailable.")
    return revision


def read_public_source_checker_stage() -> dict[str, object]:
    """Read the one fixed nonproduction Source Checker staging report."""
    stage = PUBLIC_SOURCE_CHECKER_STAGE
    expected = ROOT / ".tmp" / "project-console-source-checker.json"
    try:
        if stage != expected:
            raise RuntimeError(
                "The public Source Checker stage is not the fixed repository slot."
            )
        root_stat = ROOT.lstat()
        tmp_stat = stage.parent.lstat()
        stage_stat = stage.lstat()
        if (
            stat.S_ISLNK(root_stat.st_mode)
            or stat.S_ISLNK(tmp_stat.st_mode)
            or stat.S_ISLNK(stage_stat.st_mode)
            or not stat.S_ISDIR(tmp_stat.st_mode)
            or not stat.S_ISREG(stage_stat.st_mode)
        ):
            raise RuntimeError(
                "The fixed public Source Checker stage is unavailable."
            )
        resolved_root = ROOT.resolve(strict=True)
        resolved_tmp = stage.parent.resolve(strict=True)
        resolved_stage = stage.resolve(strict=True)
        if (
            resolved_tmp != resolved_root / ".tmp"
            or resolved_stage.parent != resolved_tmp
        ):
            raise RuntimeError(
                "The fixed public Source Checker stage is unavailable."
            )
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(stage, flags)
        try:
            opened_stat = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened_stat.st_mode)
                or opened_stat.st_dev != stage_stat.st_dev
                or opened_stat.st_ino != stage_stat.st_ino
            ):
                raise RuntimeError(
                    "The fixed public Source Checker stage is unavailable."
                )
            with os.fdopen(descriptor, encoding="utf-8") as handle:
                descriptor = -1
                payload = json.load(handle)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "The fixed public Source Checker stage is unavailable."
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(
            "The fixed public Source Checker stage is unavailable."
        )
    return payload


def source_checker_snapshot(
    *,
    public_source_checker_stage: bool = False,
    public_only: bool = False,
) -> dict[str, object]:
    """Read the published source-checker feed or its explicit offline cache."""
    try:
        config = json.loads(SOURCE_CHECKER_CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        config = {}

    catalog_paths = [
        ROOT / str(relative) for relative in config.get("catalogs") or []
    ]
    current_catalog_ids: set[str] | None = set() if catalog_paths else None
    current_catalog_ids_by_path: dict[str, set[str]] = {}
    id_field = str(config.get("idField") or "Source ID")
    url_field = str(config.get("urlField") or "URL")
    for relative in config.get("catalogs") or []:
        path = ROOT / str(relative)
        if not path.is_file():
            current_catalog_ids = None
            break
        catalog_ids: set[str] = set()
        for row in read_csv(path):
            if str(row.get(url_field) or "").strip():
                identifier = str(row.get(id_field) or "").strip()
                if not identifier or (
                    current_catalog_ids is not None
                    and identifier in current_catalog_ids
                ):
                    current_catalog_ids = None
                    break
                if current_catalog_ids is not None:
                    current_catalog_ids.add(identifier)
                    catalog_ids.add(identifier)
        if current_catalog_ids is None:
            break
        current_catalog_ids_by_path[str(relative)] = catalog_ids
    current_catalog_hashes = (
        source_hashes(ROOT, catalog_paths)
        if current_catalog_ids is not None
        else {}
    )

    def candidate_is_valid(payload: object) -> bool:
        if not valid_snapshot(
            payload,
            timestamp_fields=("checked_at", "generated_at"),
            required_fields=("results",),
        ):
            return False
        assert isinstance(payload, dict)
        producer = snapshot_contract_view(payload)
        results = payload.get("results")
        counts = payload.get("counts")
        if not isinstance(results, list) or not isinstance(counts, dict):
            return False
        try:
            expected = int(
                producer.get("expected_count", payload.get("eligible_urls"))
            )
            actual = int(producer.get("actual_count", len(results)))
            classified = sum(int(value) for value in counts.values())
        except (TypeError, ValueError):
            return False
        identifiers = [
            str(item.get("source_id") or "").strip()
            for item in results
            if isinstance(item, dict)
        ]
        return (
            expected >= 0
            and actual == len(results)
            and expected == actual
            and classified == len(results)
            and len(identifiers) == len(results)
            and all(identifiers)
            and len(identifiers) == len(set(identifiers))
        )

    def with_current_catalog_coverage(
        payload: dict[str, object],
    ) -> dict[str, object]:
        projected = dict(payload)
        existing_producer = payload.get("producer_contract")
        producer_contract = (
            dict(existing_producer)
            if isinstance(existing_producer, dict)
            else {
                field: payload[field]
                for field in PRODUCER_CONTRACT_FIELDS
                if field in payload
            }
        )
        projected["producer_contract"] = producer_contract
        if current_catalog_ids is None:
            projected["availability"] = "unavailable"
            projected["completeness"] = {
                "complete": False,
                "expected_count": None,
                "actual_count": len(payload.get("results") or []),
                "missing_count": None,
            }
            projected["projection_errors"] = [
                {
                    "code": "current_catalog_unavailable",
                    "severity": "error",
                    "message": "Current source catalogs could not be validated.",
                }
            ]
            projected["currentness"] = {
                "authority": "source_catalog_identity_and_hashes",
                "status": "unavailable",
                "current": False,
                "supersession_rule": (
                    "Any catalog identity or content-hash change supersedes a "
                    "prior Source Checker generation immediately."
                ),
            }
            return projected
        results = payload.get("results") or []
        result_ids = {
            str(item.get("source_id") or "").strip()
            for item in results
            if isinstance(item, dict)
        }
        missing = sorted(current_catalog_ids - result_ids)
        unexpected = sorted(result_ids - current_catalog_ids)
        producer_hashes = producer_contract.get("source_hashes")
        producer_hashes = (
            producer_hashes if isinstance(producer_hashes, dict) else {}
        )
        missing_hashes = sorted(
            label
            for label in current_catalog_hashes
            if not str(producer_hashes.get(label) or "").strip()
        )
        hash_mismatches = sorted(
            label
            for label, digest in current_catalog_hashes.items()
            if str(producer_hashes.get(label) or "").strip()
            and producer_hashes.get(label) != digest
        )
        hash_contract_available = bool(current_catalog_hashes) and not missing_hashes
        complete = (
            not missing
            and not unexpected
            and hash_contract_available
            and not hash_mismatches
        )
        errors = [
            error
            for error in payload.get("projection_errors") or []
            if isinstance(error, dict)
            and error.get("code")
            not in {
                "current_catalog_source_missing",
                "superseded_catalog_source",
                "current_catalog_hash_missing",
                "current_catalog_hash_superseded",
            }
        ]
        errors.extend(
            {
                "code": "current_catalog_source_missing",
                "severity": "error",
                "source_id": identifier,
                "message": "Current source catalog ID is absent from this checker generation.",
            }
            for identifier in missing
        )
        errors.extend(
            {
                "code": "superseded_catalog_source",
                "severity": "warning",
                "source_id": identifier,
                "message": "Checker result is outside the current catalog identity set.",
            }
            for identifier in unexpected
        )
        errors.extend(
            {
                "code": "current_catalog_hash_missing",
                "severity": "error",
                "catalog": label,
                "message": (
                    "Checker generation does not declare the current catalog hash."
                ),
            }
            for label in missing_hashes
        )
        errors.extend(
            {
                "code": "current_catalog_hash_superseded",
                "severity": "error",
                "catalog": label,
                "message": (
                    "Current catalog content differs from the checker generation."
                ),
                "producer_hash": producer_hashes.get(label),
                "current_hash": current_catalog_hashes.get(label),
            }
            for label in hash_mismatches
        )
        projected.update(
            {
                "expected_count": len(current_catalog_ids),
                "actual_count": len(result_ids & current_catalog_ids),
                "availability": "current" if complete else "stale",
                "completeness": {
                    "complete": complete,
                    "expected_count": len(current_catalog_ids),
                    "actual_count": len(result_ids & current_catalog_ids),
                    "missing_count": len(missing),
                    "unexpected_count": len(unexpected),
                    "missing_hash_count": len(missing_hashes),
                    "hash_mismatch_count": len(hash_mismatches),
                },
                "missing_source_ids": missing,
                "unexpected_source_ids": unexpected,
                "projection_errors": errors,
                "current_catalog_coverage": {
                    "complete": complete,
                    "expected_count": len(current_catalog_ids),
                    "actual_count": len(result_ids & current_catalog_ids),
                    "missing_ids": missing,
                    "unexpected_ids": unexpected,
                    "source_hashes": current_catalog_hashes,
                    "producer_source_hashes": producer_hashes,
                    "hash_contract_available": hash_contract_available,
                    "missing_hashes": missing_hashes,
                    "hash_mismatches": hash_mismatches,
                },
                "currentness": {
                    "authority": "source_catalog_identity_and_hashes",
                    "status": "current" if complete else "stale",
                    "current": complete,
                    "supersession_rule": (
                        "Any catalog identity or content-hash change supersedes "
                        "a prior Source Checker generation immediately."
                    ),
                },
            }
        )
        freshness = dict(projected.get("freshness") or {})
        freshness.update(
            {
                "status": "current" if complete else "stale",
                "basis": "current source catalog identity coverage and content hashes",
                "supersession_rule": projected["currentness"][
                    "supersession_rule"
                ],
            }
        )
        projected["freshness"] = freshness
        return projected

    def public_stage_is_valid(payload: object) -> bool:
        if (
            current_catalog_ids is None
            or not current_catalog_ids_by_path
            or not candidate_is_valid(payload)
            or not isinstance(payload, dict)
        ):
            return False
        completeness = payload.get("completeness")
        pagination = payload.get("pagination")
        pagination_sources = (
            pagination.get("sources")
            if isinstance(pagination, dict)
            else None
        )
        results = payload.get("results")
        if (
            payload.get("schema_version") != 2
            or payload.get("contract_schema_version") != 1
            or payload.get("agent_id") != "source-checker-bot"
            or payload.get("mode") != "report-only"
            or not str(payload.get("generation_id") or "").strip()
            or payload.get("source_hashes") != current_catalog_hashes
            or payload.get("catalogs")
            != [str(relative) for relative in config.get("catalogs") or []]
            or payload.get("availability") != "current"
            or not isinstance(completeness, dict)
            or completeness.get("complete") is not True
            or not isinstance(pagination, dict)
            or pagination.get("complete") is not True
            or not isinstance(pagination_sources, list)
            or not isinstance(results, list)
            or payload.get("missing_source_ids") != []
            or payload.get("unexpected_source_ids") != []
            or payload.get("duplicate_result_ids") != []
            or payload.get("projection_errors") != []
        ):
            return False
        try:
            expected = int(payload.get("expected_count"))
            actual = int(payload.get("actual_count"))
            eligible = int(payload.get("eligible_urls"))
            classified = sum(
                int(value) for value in (payload.get("counts") or {}).values()
            )
            completeness_expected = int(completeness.get("expected_count"))
            completeness_actual = int(completeness.get("actual_count"))
            completeness_missing = int(completeness.get("missing_count"))
        except (AttributeError, TypeError, ValueError):
            return False
        result_ids = [
            str(item.get("source_id") or "").strip()
            for item in results
            if isinstance(item, dict)
        ]
        result_catalog_ids: dict[str, set[str]] = {
            relative: set() for relative in current_catalog_ids_by_path
        }
        for item in results:
            if not isinstance(item, dict):
                return False
            relative = str(item.get("catalog") or "")
            identifier = str(item.get("source_id") or "").strip()
            if relative not in result_catalog_ids or not identifier:
                return False
            result_catalog_ids[relative].add(identifier)
        pagination_by_source: dict[str, dict[str, object]] = {}
        for item in pagination_sources:
            if not isinstance(item, dict):
                return False
            relative = str(item.get("source") or "")
            if relative in pagination_by_source:
                return False
            pagination_by_source[relative] = item
        if set(pagination_by_source) != set(current_catalog_ids_by_path):
            return False
        for relative, identifiers in current_catalog_ids_by_path.items():
            page = pagination_by_source[relative]
            if (
                page.get("complete") is not True
                or page.get("expected_count") != len(identifiers)
                or page.get("actual_count") != len(identifiers)
                or result_catalog_ids.get(relative) != identifiers
            ):
                return False
        total = len(current_catalog_ids)
        return (
            expected == total
            and actual == total
            and eligible == total
            and classified == total
            and completeness_expected == total
            and completeness_actual == total
            and completeness_missing == 0
            and len(result_ids) == total
            and set(result_ids) == current_catalog_ids
            and len(result_ids) == len(set(result_ids))
        )

    if public_source_checker_stage:
        if os.environ.get("ARRP_SOURCE_CHECKER_SNAPSHOT", "").strip():
            raise RuntimeError(
                "The fixed public Source Checker stage cannot be combined "
                "with ARRP_SOURCE_CHECKER_SNAPSHOT."
            )
        stage_payload = read_public_source_checker_stage()
        if not public_stage_is_valid(stage_payload):
            raise RuntimeError(
                "The fixed public Source Checker stage is invalid."
            )
        projected = with_current_catalog_coverage(stage_payload)
        if (
            projected.get("availability") != "current"
            or not isinstance(projected.get("completeness"), dict)
            or projected["completeness"].get("complete") is not True
        ):
            raise RuntimeError(
                "The fixed public Source Checker stage is not current and complete."
            )
        return projected

    override_path = os.environ.get("ARRP_SOURCE_CHECKER_SNAPSHOT", "").strip()
    if override_path:
        override_payload = read_trusted_snapshot_file(
            override_path,
            environment_name="ARRP_SOURCE_CHECKER_SNAPSHOT",
        )
        if not candidate_is_valid(override_payload):
            raise RuntimeError(
                "ARRP_SOURCE_CHECKER_SNAPSHOT explicitly selected a Source "
                "Checker feed with an invalid producer generation."
            )
        return with_current_catalog_coverage(override_payload)

    candidates: list[dict[str, object]] = []
    existing = existing_console_payload()
    cached = existing.get("source_checker", {})
    if candidate_is_valid(cached):
        candidates.append(with_current_catalog_coverage(cached))
    if public_only:
        return newest_snapshot(candidates, authority="catalog")

    configured_cache = str(config.get("offlineCachePath") or "").strip()
    cache_candidates = [ROOT / configured_cache] if configured_cache else []

    for path in cache_candidates:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if candidate_is_valid(payload):
                candidates.append(with_current_catalog_coverage(payload))
        except (OSError, json.JSONDecodeError):
            pass

    return newest_snapshot(candidates, authority="catalog")


def existing_horizon_snapshot() -> tuple[list[dict[str, object]], str]:
    payload = existing_console_payload()
    return payload.get("horizon_records", []), str(payload.get("github_synced_at", ""))


def source_count_for_record(record_id: str) -> int:
    return sum(
        record_id in associated_record_ids(row["Associated Record IDs"])
        for row in all_source_records()
    )


def monitoring_issue_snapshot(
    refresh: bool, horizon_records: list[dict[str, object]] | None = None
) -> list[dict[str, object]]:
    eligible_kinds = {"proposal", "horizon"}
    horizon_issue_bodies: dict[str, str] = {}
    for record in horizon_records or []:
        body = str(record.get("issue_body", ""))
        if not body and isinstance(record.get("issue_body_lines"), list):
            body = "\n".join(str(line) for line in record["issue_body_lines"])
        if body:
            horizon_issue_bodies[str(record.get("id", ""))] = body
    if not refresh:
        records = existing_console_payload().get("monitoring_issues", [])
        if isinstance(records, list):
            registry_by_id = {
                row["Object ID"].strip(): row
                for row in read_csv(ISSUE_REGISTRY)
                if row["Object ID"].strip()
            }
            enriched: list[dict[str, object]] = []
            for record in records:
                record_id = str(record.get("id", ""))
                registry = registry_by_id.get(record_id, {})
                if registry.get("Kind", "").strip() not in eligible_kinds:
                    continue
                sources = sources_for_record(record_id)
                enriched.append(
                    {
                        **record,
                        "source_count": len(sources),
                        "sources": sources,
                        "monitoring_rationale": monitoring_rationale_for_record(
                            registry, horizon_issue_bodies.get(record_id, "")
                        ),
                    }
                )
            return enriched
        raise RuntimeError(
            "No preserved GitHub monitoring snapshot exists. Re-run with "
            "--refresh-github in an authenticated host context."
        )

    issue_limit = 1000
    issues = require_complete_cli_collection(
        run_gh_json(
        [
            "issue", "list", "--repo", "Thorncrag/ARRP", "--label",
            "needs: monitoring", "--state", "open", "--limit", str(issue_limit), "--json",
            "number,title,state,url,labels,updatedAt,body",
        ]
        ),
        limit=issue_limit,
        source="GitHub monitored-issue query",
    )
    project_limit = 1000
    project = project_items_snapshot()
    if not isinstance(project, dict):
        raise RuntimeError("GitHub Project query did not return a JSON object.")
    project_items = require_complete_cli_collection(
        project.get("items"),
        limit=project_limit,
        source="GitHub Project item query",
        reported_total=project.get("totalCount"),
    )
    project_by_number = {
        item.get("content", {}).get("number"): item
        for item in project_items
        if item.get("content", {}).get("type") == "Issue"
    }
    registry_by_number = {
        int(row["GitHub Number"]): row
        for row in read_csv(ISSUE_REGISTRY)
        if row["GitHub Number"].strip().isdigit()
    }
    kind_labels = {"proposal": "Proposal", "horizon": "Candidate"}
    records: list[dict[str, object]] = []
    for issue in issues:
        registry = registry_by_number.get(issue["number"], {})
        if registry.get("Kind", "").strip() not in eligible_kinds:
            continue
        project_item = project_by_number.get(issue["number"], {})
        record_id = registry.get("Object ID", "").strip()
        if not record_id:
            match = re.search(r"\b(?:HOR|[A-Z]{2,})-\d{3}\b", issue["title"])
            record_id = match.group(0) if match else f"Issue #{issue['number']}"
        title = re.sub(rf"^{re.escape(record_id)}\s*:\s*", "", issue["title"]).strip()
        records.append(
            {
                "id": record_id,
                "number": issue["number"],
                "title": title,
                "kind": kind_labels.get(registry.get("Kind", "").strip(), "Project record"),
                "area": project_item.get("area") or (
                    record_id.split("-", 1)[0] if "-" in record_id else "Unassigned"
                ),
                "development_level": project_item.get("development level") or "Development level unavailable",
                "workflow_status": project_item.get("status") or "Workflow status unavailable",
                "priority": project_item.get("priority") or "Unassigned",
                "source_count": source_count_for_record(record_id),
                "sources": sources_for_record(record_id),
                "monitoring_rationale": monitoring_rationale_for_record(
                    registry, issue.get("body", "")
                ),
                "issue_url": issue["url"],
                "updated_at": issue["updatedAt"],
            }
        )
    return sorted(records, key=lambda row: (str(row["kind"]), str(row["id"])))


def case_watcher_snapshot() -> tuple[list[dict[str, object]], dict[str, object]]:
    """Cataloged court sources covered by the tracker-assisted watcher."""
    if not CASE_MONITOR_CONFIG.exists():
        return [], {"enabled": False, "mode": "Not configured"}
    config = json.loads(CASE_MONITOR_CONFIG.read_text(encoding="utf-8"))
    verification = config.get("verification", config.get("provider", {}))
    allowed_hosts = set(verification.get("allowedHosts", []))
    registry_by_id = {
        row.get("Object ID", "").strip(): row
        for row in read_csv(ISSUE_REGISTRY)
        if row.get("Object ID", "").strip()
    }
    records: list[dict[str, object]] = []
    for raw in all_source_records():
        source = source_payload(raw)
        if source.get("monitoring") != "Yes":
            continue
        host = urllib.parse.urlsplit(str(source.get("url", ""))).hostname or ""
        if host not in allowed_hosts:
            continue
        owner_ids = list(source.get("record_ids", []))
        owner_id = owner_ids[0] if owner_ids else "Unassigned"
        registry = registry_by_id.get(owner_id, {})
        records.append(
            {
                **source,
                "owner_id": owner_id,
                "owner_title": registry.get("GitHub Title", "").strip() or owner_id,
                "owner_kind": registry.get("Kind", "").strip() or "Project record",
                "owner_status": "Source-level monitoring",
                "owner_issue_url": registry.get("GitHub Issue", "").strip(),
                "monitoring_rationale": source.get("monitoring_rationale") or source.get("proposition"),
                "monitoring_group": source.get("monitoring_group") or owner_id,
                "coverage": (
                    "Accepted per-source baseline"
                    if source.get("monitoring_baseline_present")
                    else "Baseline initialization required"
                ),
            }
        )
    records.sort(key=lambda row: (str(row["owner_id"]), str(row["monitoring_group"]), str(row["id"])))
    schedule = config.get("schedule", {})
    metadata = {
        "enabled": bool(config.get("enabled", False)),
        "mode": (
            "Manual dispatch only"
            if not config.get("enabled", False)
            else schedule.get("description", "Scheduled; manual dispatch available")
        ),
        "bot_name": config.get("botName", "case-monitor-bot"),
        "provider": " + ".join(
            value
            for value in (
                config.get("tracker", {}).get("type", ""),
                verification.get("type", ""),
            )
            if value
        )
        or "Not configured",
        "workflow_url": "https://github.com/Thorncrag/ARRP/actions/workflows/case-monitor-bot.yml",
    }
    return records, metadata


def directive_watcher_metadata() -> dict[str, object]:
    if not DIRECTIVE_MONITOR_CONFIG.exists():
        return {"enabled": False, "mode": "Not configured"}
    config = json.loads(DIRECTIVE_MONITOR_CONFIG.read_text(encoding="utf-8"))
    schedule = config.get("schedule", {})
    return {
        "enabled": bool(config.get("enabled", False)),
        "mode": (
            "Manual dispatch only"
            if not config.get("enabled", False)
            else schedule.get("description", "Scheduled; manual dispatch available")
        ),
        "bot_name": config.get("botName", "presidential-directives-bot"),
        "provider": config.get("provider", {}).get("type", "Not configured"),
        "workflow_url": "https://github.com/Thorncrag/ARRP/actions/workflows/presidential-directives-bot.yml",
    }


def horizon_snapshot(refresh: bool) -> tuple[list[dict[str, object]], str]:
    if not refresh:
        records, synced_at = existing_horizon_snapshot()
        if records:
            obsolete_queue_fields = {
                "source_task_count",
                "monitoring_task_count",
                "related_source_links",
            }
            normalized = []
            for record in records:
                cleaned = {
                    key: value
                    for key, value in record.items()
                    if key not in obsolete_queue_fields
                }
                if "issue_body_lines" in cleaned and "issue_body" not in cleaned:
                    cleaned["issue_body"] = "\n".join(cleaned.pop("issue_body_lines"))
                normalized.append(cleaned)
            return normalized, synced_at
        raise RuntimeError(
            "No preserved GitHub Horizon snapshot exists. Re-run with --refresh-github "
            "in an authenticated host context."
        )

    issue_limit = 1000
    issues = require_complete_cli_collection(
        run_gh_json(
        [
            "issue", "list", "--repo", "Thorncrag/ARRP", "--label", "kind: horizon",
            "--state", "all", "--limit", str(issue_limit), "--json",
            "number,title,state,url,body,labels,createdAt,updatedAt",
        ]
        ),
        limit=issue_limit,
        source="GitHub Horizon issue query",
    )
    project_limit = 1000
    project = project_items_snapshot()
    if not isinstance(project, dict):
        raise RuntimeError("GitHub Project query did not return a JSON object.")
    project_items = require_complete_cli_collection(
        project.get("items"),
        limit=project_limit,
        source="GitHub Project item query",
        reported_total=project.get("totalCount"),
    )
    project_by_number = {
        item.get("content", {}).get("number"): item
        for item in project_items
        if "kind: horizon" in (item.get("labels") or [])
        and item.get("content", {}).get("type") == "Issue"
    }
    records: list[dict[str, object]] = []
    for issue in issues:
        project_item = project_by_number.get(issue["number"], {})
        labels = [label["name"] for label in issue.get("labels", [])]
        match = re.search(r"HOR-\d+", issue["title"])
        horizon_id = match.group(0) if match else f"Issue #{issue['number']}"
        records.append(
            {
                "id": horizon_id,
                "number": issue["number"],
                "title": re.sub(r"^HOR-\d+:\s*", "", issue["title"]).strip(),
                "full_title": issue["title"],
                "issue_state": issue["state"].title(),
                "development_level": project_item.get("development level")
                or ("Closed" if issue["state"] == "CLOSED" else "Development level unavailable"),
                "workflow_status": project_item.get("status")
                or ("Closed" if issue["state"] == "CLOSED" else "Workflow status unavailable"),
                "area": project_item.get("area") or "Unassigned",
                "priority": project_item.get("priority") or "Unassigned",
                "release_blocker": project_item.get("release blocker") or "Unassigned",
                "last_audit": project_item.get("last audit") or "Not recorded",
                "next_audit": project_item.get("next audit") or "Not recorded",
                "canonical_page": project_item.get("canonical page") or issue["url"],
                "issue_url": issue["url"],
                "issue_body": issue.get("body") or "",
                "labels": labels,
                "needs_monitoring": "needs: monitoring" in labels,
                "created_at": issue["createdAt"],
                "updated_at": issue["updatedAt"],
            }
        )
    records.sort(
        key=lambda record: int(str(record["id"]).split("-")[-1])
        if str(record["id"]).startswith("HOR-") else 9999
    )
    return records, datetime.now(timezone.utc).isoformat(timespec="seconds")


def enrich_horizon_records(
    records: list[dict[str, object]],
    projection_errors: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    history_by_id = horizon_log_records(projection_errors)
    enriched: list[dict[str, object]] = []
    for original in records:
        record = dict(original)
        record_id = str(record["id"])
        issue_body = str(record.pop("issue_body", ""))
        record["issue_body_lines"] = issue_body.splitlines()
        record["issue_body_html"] = render_markdown_safe(issue_body) if issue_body.strip() else ""
        history = history_by_id.get(record_id)
        sources = sources_for_record(record_id)
        research = research_for_record(record_id)
        gaps: list[str] = []
        if not history:
            gaps.append("No Horizon Scan Log entry was found for this active candidate.")
        if not sources:
            gaps.append("No supporting source is associated with this candidate in either source catalog.")
        if not research:
            gaps.append("No identifier-linked research memorandum is currently available.")
        if str(record.get("next_audit", "")).strip() in {"", "Not recorded"}:
            gaps.append("The GitHub Project does not record a next review question.")
        if not issue_body.strip():
            gaps.append("The preserved snapshot does not include the GitHub issue body; refresh GitHub data to include it.")
        record.update(
            {
                "horizon_history": history or {},
                "horizon_log_url": HORIZON_LOG_URL,
                "supporting_sources": sources,
                "evidence_records": [],
                "research_records": research,
                "dossier_gaps": gaps,
            }
        )
        enriched.append(record)
    return enriched


PIPELINE_WORK_CLASS_ORDER = {
    "preliminary_candidate": 0,
    "formal_candidate": 1,
    "proposal": 2,
}
PIPELINE_PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "normal": 3,
    "low": 4,
    "parked": 5,
}
PIPELINE_HOLD_STATUSES = {"Blocked", "Deferred"}
PIPELINE_HUMAN_STATUSES = {"Human decision needed", "Publication approval"}


def markdown_heading_section(value: str, headings: tuple[str, ...]) -> str:
    """Return one exact Markdown heading section without interpreting its prose."""
    if not value.strip():
        return ""
    heading_pattern = "|".join(re.escape(heading) for heading in headings)
    match = re.search(
        rf"^##\s+(?:{heading_pattern})\s*$\n(.*?)(?=^##\s+|\Z)",
        value,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return strip_markdown(match.group(1)) if match else ""


def markdown_labeled_value(value: str, labels: tuple[str, ...]) -> str:
    """Read an explicitly labeled bold Markdown field."""
    if not value.strip():
        return ""
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"^\*\*(?:{label_pattern}):\*\*\s*(.+?)\s*$",
        value,
        re.MULTILINE | re.IGNORECASE,
    )
    return strip_markdown(match.group(1)) if match else ""


def audit_hold_provenance(
    identifier: str,
    canonical_record: str,
    workflow_status: str,
) -> dict[str, object]:
    """Project exact hold-transition and later-review dates from the audit sidecar."""
    result: dict[str, object] = {
        "holdSince": None,
        "lastReviewed": None,
        "provenanceUrl": None,
        "provenanceState": "missing",
    }
    if workflow_status not in PIPELINE_HOLD_STATUSES or not canonical_record:
        return result
    canonical_path = (ROOT / canonical_record).resolve()
    try:
        canonical_path.relative_to(ROOT)
    except ValueError:
        return result
    audit_path = canonical_path.with_suffix(".audit.md")
    if not audit_path.is_file():
        return result
    content = audit_path.read_text(encoding="utf-8")
    entries: list[dict[str, object]] = []
    for match in re.finditer(
        r"^###\s+(\d{4}-\d{2}-\d{2})\s+[—-]\s+(.+?)\s*$\n"
        r"(.*?)(?=^###\s+\d{4}-\d{2}-\d{2}\s+[—-]|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    ):
        entries.append(
            {
                "date": match.group(1),
                "title": match.group(2).strip(),
                "body": match.group(3),
                "line": content[: match.start()].count("\n") + 1,
            }
        )
    status_pattern = re.escape(workflow_status)
    identifier_pattern = re.escape(identifier)
    transitions = [
        entry
        for entry in entries
        if (
            re.search(
                rf"^\*\*Status:\*\*\s*{status_pattern}\b",
                str(entry["body"]),
                re.MULTILINE | re.IGNORECASE,
            )
            or re.search(
                rf"\bSet\s+{identifier_pattern}(?:'s)?\s+(?:issue\s+)?status\s+to\s+{status_pattern}\b",
                str(entry["body"]),
                re.IGNORECASE,
            )
            or re.search(
                rf"\b{status_pattern}\s+Status\s+(?:Update|Transition)\b",
                str(entry["title"]),
                re.IGNORECASE,
            )
        )
    ]
    if not transitions:
        result["provenanceState"] = "status_without_matching_transition"
        return result
    transition = sorted(
        transitions, key=lambda entry: (str(entry["date"]), int(entry["line"]))
    )[-1]
    relative = audit_path.relative_to(ROOT).as_posix()
    heading = f"{transition['date']} — {transition['title']}"
    anchor = re.sub(
        r"[^\w\- ]",
        "",
        heading.casefold(),
        flags=re.UNICODE,
    )
    anchor = re.sub(r"[\s\-]+", "-", anchor).strip("-")
    result.update(
        {
            "holdSince": transition["date"],
            "provenanceUrl": (
                f"{GITHUB_BLOB_ROOT}{relative}#{anchor}"
            ),
            "provenanceState": "verified",
        }
    )
    review_entries = [
        entry
        for entry in entries
        if (
            str(entry["date"]),
            int(entry["line"]),
        )
        > (
            str(transition["date"]),
            int(transition["line"]),
        )
        and re.search(
            r"\b(?:hold review|predicate check|deferral reconsideration|"
            r"blocker-predicate check|deferred-status review)\b",
            str(entry["title"]),
            re.IGNORECASE,
        )
    ]
    if review_entries:
        result["lastReviewed"] = sorted(
            review_entries,
            key=lambda entry: (str(entry["date"]), int(entry["line"])),
        )[-1]["date"]
    return result


def pipeline_readiness(item: dict[str, object], threshold: float) -> dict[str, object]:
    """Project the complete readiness predicate without inferring missing values."""
    if normalize_console_owner(item.get("kind")) != "proposal":
        return {"state": "not_applicable", "gaps": []}
    level = str(item.get("developmentLevel") or "")
    score = item.get("score")
    score_state = str(item.get("scoreState") or "missing")
    ready_level = normalize_console_owner(level) in {
        "review ready",
        "release candidate",
    }
    valid_score = (
        isinstance(score, (int, float))
        and not isinstance(score, bool)
        and 0 <= float(score) <= 100
    )
    score_ready = valid_score and float(score) >= threshold
    gaps: list[str] = []
    if score_state == "invalid":
        gaps.append("Development Score is invalid.")
    if ready_level and not valid_score:
        gaps.append("Ready development level lacks a valid Development Score.")
    elif ready_level and not score_ready:
        gaps.append("Ready development level is below the Review Ready score threshold.")
    if not ready_level and score_ready:
        gaps.append("Development Score meets the threshold but Development level is below Review Ready.")
    if gaps:
        return {"state": "conflict", "gaps": gaps}
    return {
        "state": "ready" if ready_level and score_ready else "not_ready",
        "gaps": [],
    }


def pipeline_hold_fields(
    item: dict[str, object],
    horizon_record: dict[str, object] | None = None,
) -> dict[str, object]:
    """Publish dedicated hold facts; never substitute Horizon rationale."""
    status = str(item.get("workflowStatus") or "")
    if status not in PIPELINE_HOLD_STATUSES:
        return {}
    body = "\n".join(
        str(line) for line in (horizon_record or {}).get("issue_body_lines", [])
    )
    if normalize_console_owner(item.get("kind")) == "horizon":
        reason = markdown_heading_section(
            body, (f"Why this is {status.casefold()}",)
        )
        trigger = markdown_heading_section(
            body,
            (
                "Reconsideration condition",
                "Reconsideration conditions",
                "Reconsideration trigger",
                "Reconsideration triggers",
            ),
        )
        if status == "Blocked":
            trigger = trigger or markdown_labeled_value(
                body, ("Concrete unblock trigger",)
            )
    else:
        reason = str(item.get("explanation") or "").strip()
        trigger = str(item.get("nextAudit") or item.get("nextAction") or "").strip()
    provenance = audit_hold_provenance(
        str(item.get("identifier") or ""),
        str(item.get("canonicalRecord") or ""),
        status,
    )
    milestone = item.get("milestone")
    review_due = (
        milestone.get("dueOn")
        if isinstance(milestone, dict) and milestone.get("dueOn")
        else None
    )
    return {
        "status": status,
        "reason": reason or None,
        "reasonState": "recorded" if reason else "missing",
        "blockedAction": (
            markdown_labeled_value(body, ("Blocked action",))
            if status == "Blocked"
            else None
        ),
        "missingPrerequisite": (
            markdown_labeled_value(
                body,
                (
                    "Indispensable unavailable prerequisite",
                    "Missing prerequisite",
                    "Indispensable prerequisite",
                ),
            )
            if status == "Blocked"
            else None
        ),
        "trigger": trigger or None,
        "triggerState": "recorded" if trigger else "missing",
        "holdSince": provenance["holdSince"],
        "lastReviewed": provenance["lastReviewed"],
        "reviewDue": review_due,
        "provenanceUrl": provenance["provenanceUrl"],
        "provenanceState": provenance["provenanceState"],
    }


def build_pipeline_projection(
    preliminary_records: list[dict[str, object]],
    horizon_records: list[dict[str, object]],
    progress: dict[str, object],
    *,
    generated_at: str,
) -> dict[str, object]:
    """Build the typed cross-cutting planning index consumed by the Console."""
    threshold = float((progress.get("goal") or {}).get("reviewReadyScore") or 75)
    progress_candidates = {
        str(item.get("identifier") or ""): item
        for item in progress.get("candidates") or []
        if isinstance(item, dict)
    }
    horizon_by_id = {
        str(item.get("id") or ""): item
        for item in horizon_records
        if isinstance(item, dict)
    }
    source_items: list[dict[str, object]] = []
    for record in preliminary_records:
        source_items.append(
            {
                "identifier": record.get("id"),
                "title": record.get("title"),
                "kind": "preliminary_candidate",
                "workflowStatus": "Preliminary intake",
                "developmentLevel": "Preliminary candidate",
                "score": None,
                "scoreState": "not_applicable",
                "nextAction": record.get("recommendation"),
                "priority": None,
                "owner": "Human intake review",
                "area": record.get("proposed_area"),
                "workstream": "Candidate intake",
                "url": None,
                "canonicalRecord": None,
                "dossierTarget": (
                    f"planning:preliminary:selected={record.get('id')}"
                ),
            }
        )
    for horizon in horizon_records:
        identifier = str(horizon.get("id") or "")
        project = progress_candidates.get(identifier, {})
        source_items.append(
            {
                **project,
                "identifier": identifier,
                "title": project.get("title") or horizon.get("title"),
                "kind": "horizon",
                "workflowStatus": (
                    project.get("workflowStatus")
                    or horizon.get("workflow_status")
                ),
                "developmentLevel": (
                    project.get("developmentLevel")
                    or horizon.get("development_level")
                ),
                "score": None,
                "scoreState": "not_applicable",
                "nextAction": project.get("nextAction"),
                "nextAudit": project.get("nextAudit"),
                "priority": project.get("priority") or horizon.get("priority"),
                "owner": project.get("owner") or horizon.get("owner"),
                "area": project.get("area") or horizon.get("area"),
                "workstream": (
                    project.get("workstream") or "Candidate development"
                ),
                "url": project.get("url") or horizon.get("issue_url"),
                "canonicalRecord": None,
                "dossierTarget": f"planning:candidates:selected={identifier}",
            }
        )
    source_items.extend(
        item
        for item in progress.get("proposals") or []
        if isinstance(item, dict)
    )

    items: list[dict[str, object]] = []
    data_gaps: list[dict[str, object]] = []
    integrity_findings: list[dict[str, object]] = []
    for source in source_items:
        identifier = str(source.get("identifier") or "")
        kind = str(source.get("kind") or "")
        work_class = {
            "preliminary_candidate": "Preliminary candidate",
            "horizon": "Formal candidate",
            "proposal": "Proposal",
        }.get(kind, "Unclassified")
        status = str(source.get("workflowStatus") or "")
        readiness = pipeline_readiness(source, threshold)
        if kind == "preliminary_candidate":
            mode = "active"
            membership_reason = (
                "Preliminary candidate retained in the authoritative intake catalog."
            )
        elif status in PIPELINE_HUMAN_STATUSES:
            mode = "human_action"
            membership_reason = (
                f"Workflow Status is {status}; the exact human decision belongs "
                "in Action Items and its owning dossier."
            )
        elif status in PIPELINE_HOLD_STATUSES:
            mode = "hold"
            membership_reason = (
                f"Authoritative Workflow Status is exactly {status}."
            )
        elif status not in {
            "Research",
            "Development",
            "Audit needed",
            "Audit in progress",
            "External review",
        }:
            mode = "unclassified"
            membership_reason = (
                "Workflow Status is missing, unrecognized, or contradictory; "
                "the record is not silently assigned to a Pipeline mode."
            )
            data_gaps.append(
                {
                    "gap_id": f"workflow-status-invalid:{identifier}",
                    "identifier": identifier,
                    "finding_code": "workflow_status_invalid",
                    "missing_field": "Status",
                    "recorded_value": status or None,
                    "owner": "Elim",
                    "detected_at": progress.get("generatedAt")
                    or progress.get("generated_at"),
                    "authority": "GitHub Project Status field",
                    "route": "integrity",
                    "remediation_route": (
                        source.get("dossierTarget") or "integrity"
                    ),
                }
            )
        else:
            mode = "active"
            membership_reason = (
                "Lifecycle-eligible candidate or proposal with an active "
                f"workflow Status ({status})."
            )
        next_action = str(
            source.get("nextAction") or source.get("nextAudit") or ""
        ).strip()
        score = source.get("score")
        valid_score = (
            isinstance(score, (int, float))
            and not isinstance(score, bool)
            and 0 <= float(score) <= 100
        )
        milestone = source.get("milestone")
        due_date = (
            milestone.get("dueOn")
            if isinstance(milestone, dict) and milestone.get("dueOn")
            else None
        )
        priority = str(source.get("priority") or "").strip()
        class_key = {
            "Preliminary candidate": "preliminary_candidate",
            "Formal candidate": "formal_candidate",
            "Proposal": "proposal",
        }.get(work_class, "unclassified")
        require_registered_classification("work_kind", class_key)
        sort_inputs = {
            "classRank": PIPELINE_WORK_CLASS_ORDER.get(class_key, 99),
            "scoreValid": bool(valid_score and work_class == "Proposal"),
            "scoreDescending": (
                -float(score)
                if valid_score and work_class == "Proposal"
                else None
            ),
            "nextStepMissing": not bool(next_action),
            "priorityRank": PIPELINE_PRIORITY_ORDER.get(
                priority.casefold(), 99
            ),
            "dueDate": due_date,
            "identifier": identifier,
        }
        position_parts = [f"{work_class} class"]
        if work_class == "Proposal":
            position_parts.append(
                f"Development Score {score:g}"
                if valid_score
                else "Development Score missing or invalid"
            )
        position_parts.append(
            "exact next step recorded"
            if next_action
            else "exact next step not recorded"
        )
        if priority:
            position_parts.append(f"{priority} priority")
        hold = pipeline_hold_fields(
            source, horizon_by_id.get(identifier)
        )
        if mode == "active" and not next_action:
            data_gaps.append(
                {
                    "gap_id": f"next-action-missing:{identifier}",
                    "identifier": identifier,
                    "finding_code": "next_action_missing",
                    "missing_field": "Next action",
                    "recorded_value": None,
                    "owner": source.get("owner") or "Elim",
                    "detected_at": progress.get("generatedAt")
                    or progress.get("generated_at"),
                    "authority": "GitHub Project Next action field",
                    "route": (
                        source.get("dossierTarget")
                        or source.get("url")
                        or "planning:workbench:pipeline"
                    ),
                    "remediation_route": source.get("dossierTarget")
                    or source.get("url")
                    or "planning:workbench:pipeline",
                }
            )
        if readiness["state"] == "conflict":
            for message in readiness["gaps"]:
                integrity_findings.append(
                    {
                        "finding_id": (
                            f"readiness-conflict:{identifier}:"
                            f"{hashlib.sha256(message.encode('utf-8')).hexdigest()[:10]}"
                        ),
                        "identifier": identifier,
                        "finding_code": "readiness_conflict",
                        "severity": "warning",
                        "message": message,
                        "owner": "Elim",
                        "detected_at": progress.get("generatedAt")
                        or progress.get("generated_at"),
                        "authority": "typed Pipeline readiness predicate",
                        "route": source.get("dossierTarget")
                        or source.get("url")
                        or "integrity",
                    }
                )
        if mode == "hold":
            for field, code, label in (
                ("reason", "hold_reason_missing", "required hold reason"),
                ("trigger", "hold_trigger_missing", "unblock or reconsideration trigger"),
                (
                    "provenanceUrl",
                    "hold_transition_provenance_missing",
                    "matching audit transition provenance",
                ),
            ):
                if hold.get(field):
                    continue
                integrity_findings.append(
                    {
                        "finding_id": f"{code.replace('_', '-')}:{identifier}",
                        "identifier": identifier,
                        "finding_code": code,
                        "severity": "warning",
                        "message": (
                            f"{identifier} is {status} but lacks {label}."
                        ),
                        "owner": "Elim",
                        "detected_at": progress.get("generatedAt")
                        or progress.get("generated_at"),
                        "authority": "typed Blocked/Deferred hold contract",
                        "route": source.get("dossierTarget")
                        or source.get("url")
                        or "integrity",
                    }
                )
        canonical_record = str(source.get("canonicalRecord") or "")
        canonical_url = (
            f"{GITHUB_BLOB_ROOT}{canonical_record}"
            if canonical_record
            else None
        )
        items.append(
            {
                "id": identifier,
                "title": source.get("title"),
                "workClass": work_class,
                "workKind": class_key,
                "mode": mode,
                "membershipReason": membership_reason,
                "status": status,
                "developmentLevel": source.get("developmentLevel"),
                "score": score if work_class == "Proposal" else None,
                "scoreState": (
                    source.get("scoreState")
                    if work_class == "Proposal"
                    else "not_applicable"
                ),
                "readinessState": readiness["state"],
                "readinessGaps": readiness["gaps"],
                "nextAction": next_action or None,
                "nextActionState": "recorded" if next_action else "missing",
                "owner": source.get("owner"),
                "workstream": source.get("workstream"),
                "area": source.get("area"),
                "priority": source.get("priority"),
                "dueDate": due_date,
                "releaseBlocker": source.get("releaseBlocker"),
                "sortInputs": sort_inputs,
                "positionReason": "; ".join(position_parts) + ".",
                "hold": hold,
                "links": {
                    "dossier": source.get("dossierTarget"),
                    "issue": validated_workbench_external_url(
                        source.get("url"),
                        kind="issue",
                    ),
                    "canonical": validated_workbench_external_url(
                        canonical_url,
                        kind="canonical",
                    ),
                    "audit": validated_workbench_external_url(
                        hold.get("provenanceUrl") if hold else None,
                        kind="audit",
                    ),
                },
            }
        )
    active_items = [item for item in items if item["mode"] == "active"]
    hold_items = [item for item in items if item["mode"] == "hold"]
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "progressGenerationId": progress.get("generation_id"),
        "progressSourceRevision": progress.get("source_revision"),
        "asOf": progress.get("asOf"),
        "availability": progress.get("availability", "unavailable"),
        "defaultMode": "active",
        "defaultViewId": require_registered_classification(
            "workflow_view", "workbench_active_pipeline"
        ),
        "holdViewId": require_registered_classification(
            "workflow_view", "workbench_blocked_deferred"
        ),
        "items": items,
        "counts": {
            "active": len(active_items),
            "blockedDeferred": len(hold_items),
            "humanAction": sum(
                item["mode"] == "human_action" for item in items
            ),
            "unclassified": sum(
                item["mode"] == "unclassified" for item in items
            ),
            "nextStepsMissing": sum(
                item.get("finding_code") == "next_action_missing"
                for item in data_gaps
            ),
            "workflowStatusExceptions": sum(
                item.get("finding_code") == "workflow_status_invalid"
                for item in data_gaps
            ),
        },
        "sourceCounts": {
            "preliminaryCandidates": len(preliminary_records),
            "formalCandidates": len(horizon_records),
            "proposals": len(progress.get("proposals") or []),
        },
        "dataGaps": data_gaps,
        "integrityFindings": integrity_findings,
    }


def registered_classification_ids(namespace: str) -> set[str]:
    entries = (
        console_classification_registry().get("namespaces", {}).get(namespace)
        or []
    )
    if not isinstance(entries, list):
        raise RuntimeError(f"Console classification namespace {namespace} is invalid.")
    identifiers = {
        str(entry.get("id") or "")
        for entry in entries
        if isinstance(entry, dict) and str(entry.get("id") or "")
    }
    if len(identifiers) != len(entries):
        raise RuntimeError(
            f"Console classification namespace {namespace} has invalid identities."
        )
    return identifiers


def require_registered_classification(namespace: str, identifier: object) -> str:
    exact = str(identifier or "").strip()
    if exact not in registered_classification_ids(namespace):
        raise RuntimeError(
            f"Unregistered Console classification {namespace}:{exact or '<missing>'}."
        )
    return exact


def build_action_snapshot(
    *,
    progress: dict[str, object],
    integrity: dict[str, object],
    review_recommendations: list[dict[str, object]],
    operational_incidents: dict[str, object],
    security_incidents: dict[str, object] | None = None,
    generated_at: str,
    require_private_incident_completeness: bool = False,
) -> dict[str, object]:
    """Assemble one typed cross-screen work snapshot.

    The browser may filter and format this list. It may not originate an item,
    category, owner, actionability decision, or route.
    """

    items: list[dict[str, object]] = []
    seen: set[str] = set()

    def add(item: dict[str, object]) -> None:
        item_id = str(item.get("item_id") or "").strip()
        if not item_id or item_id in seen:
            raise RuntimeError("Action snapshot contains a missing or duplicate item ID.")
        require_registered_classification("work_kind", item.get("work_kind"))
        if item.get("finding_code"):
            require_registered_classification(
                "finding_code", item.get("finding_code")
            )
        work_label = next(
            str(entry.get("label"))
            for entry in console_classification_registry()["namespaces"][
                "work_kind"
            ]
            if entry.get("id") == item.get("work_kind")
        )
        item.update(
            {
                "reference": item_id,
                "category": work_label,
                "severity": item.get("severity") or "warning",
                "attention": item.get("attention_class"),
                "reported_by": item.get("authority"),
                "message": item.get("label"),
                "source_url": (
                    item.get("route")
                    if str(item.get("route") or "").startswith("http")
                    else f"#{item.get('route')}"
                ),
                "checked_at": generated_at,
            }
        )
        seen.add(item_id)
        items.append(item)

    for item in review_recommendations:
        if normalize_console_owner(item.get("action_owner")) != "human":
            continue
        recommendation_id = str(item.get("id") or "").strip()
        if not recommendation_id:
            continue
        add(
            {
                "item_id": f"repository-decision:{recommendation_id}",
                "work_kind": "repository_human_decision",
                "finding_code": None,
                "label": item.get("human_question")
                or "Review the recorded repository recommendation.",
                "status": "open",
                "owner": "Human",
                "attention_class": "human",
                "authority": "typed Source Monitor recommendation",
                "source_record_id": recommendation_id,
                "detected_at": item.get("recorded_at"),
                "next_action": item.get("human_question"),
                "route": item.get("console_target") or "actions",
                "specialist_route": item.get("console_target")
                or "automation:logs:sources",
                "resolution_predicate": (
                    "The exact-head recommendation records a non-human disposition "
                    "or the pull request closes."
                ),
            }
        )

    progress_items = [
        item
        for collection in (
            progress.get("proposals") or [],
            progress.get("candidates") or [],
            progress.get("delivery_items") or [],
        )
        for item in collection
        if isinstance(item, dict)
    ]
    for item in progress_items:
        if str(item.get("workflowStatus") or "") != "Human decision needed":
            continue
        identifier = str(
            item.get("identifier") or item.get("projectItemId") or ""
        ).strip()
        if not identifier:
            continue
        add(
            {
                "item_id": f"project-human-decision:{identifier}",
                "work_kind": "project_human_decision",
                "finding_code": None,
                "label": item.get("title") or identifier,
                "status": "open",
                "owner": "Human",
                "attention_class": "human",
                "authority": "GitHub Project Status field",
                "source_record_id": identifier,
                "detected_at": progress.get("generatedAt")
                or progress.get("generated_at"),
                "next_action": item.get("nextAction")
                or "Record the exact human decision.",
                "route": "actions",
                "specialist_route": (
                    f"planning:workbench:pipeline:selected={identifier}"
                ),
                "resolution_predicate": (
                    "Authoritative Project Status no longer equals Human decision needed."
                ),
            }
        )

    pipeline = (
        progress.get("pipeline")
        if isinstance(progress.get("pipeline"), dict)
        else {}
    )
    for gap in pipeline.get("dataGaps") or []:
        if not isinstance(gap, dict):
            continue
        finding_code = require_registered_classification(
            "finding_code", gap.get("finding_code")
        )
        identifier = str(gap.get("identifier") or "").strip()
        add(
            {
                "item_id": str(gap.get("gap_id") or f"{finding_code}:{identifier}"),
                "work_kind": "producer_contract_exception",
                "finding_code": finding_code,
                "label": (
                    f"{identifier}: {gap.get('missing_field')} is not recorded"
                ),
                "status": "open",
                "owner": gap.get("owner") or "Elim",
                "attention_class": (
                    "human"
                    if normalize_console_owner(gap.get("owner")) == "human"
                    else "oversight"
                ),
                "authority": gap.get("authority"),
                "source_record_id": identifier,
                "detected_at": gap.get("detected_at"),
                "next_action": (
                    f"Record the authoritative {gap.get('missing_field')} value."
                ),
                "route": "integrity",
                "specialist_route": gap.get("remediation_route") or gap.get("route"),
                "resolution_predicate": (
                    f"The authoritative {gap.get('missing_field')} value is present "
                    "and accepted by the producing schema."
                ),
            }
        )
    for finding in pipeline.get("integrityFindings") or []:
        if not isinstance(finding, dict):
            continue
        code = require_registered_classification(
            "finding_code", finding.get("finding_code")
        )
        add(
            {
                "item_id": str(finding.get("finding_id")),
                "work_kind": "integrity_obligation",
                "finding_code": code,
                "label": finding.get("message"),
                "status": "open",
                "owner": finding.get("owner") or "Elim",
                "attention_class": "oversight",
                "authority": finding.get("authority"),
                "source_record_id": finding.get("identifier"),
                "detected_at": finding.get("detected_at"),
                "next_action": "Resolve the typed Integrity condition at its owner.",
                "route": "integrity",
                "specialist_route": finding.get("route") or "integrity",
                "resolution_predicate": (
                    "The producing typed predicate no longer emits this finding ID."
                ),
            }
        )

    current_integrity = (
        integrity.get("current")
        if isinstance(integrity.get("current"), dict)
        else {}
    )
    for finding in current_integrity.get("findings") or []:
        if not isinstance(finding, dict):
            continue
        finding_id = str(
            finding.get("finding_id") or finding.get("reference") or ""
        ).strip()
        finding_code = str(
            finding.get("finding_code")
            or finding.get("condition_code")
            or ""
        ).strip()
        if not finding_id or not finding_code:
            continue
        require_registered_classification("finding_code", finding_code)
        owner = str(finding.get("owner") or "Elim")
        add(
            {
                "item_id": f"integrity:{finding_id}",
                "work_kind": "integrity_obligation",
                "finding_code": finding_code,
                "label": finding.get("message") or finding_id,
                "status": finding.get("status") or "open",
                "owner": owner,
                "attention_class": (
                    "human"
                    if normalize_console_owner(owner) == "human"
                    else "oversight"
                ),
                "authority": "Project Integrity report",
                "source_record_id": finding_id,
                "detected_at": finding.get("detected_at")
                or current_integrity.get("generated_at"),
                "next_action": finding.get("next_action")
                or "Open the Integrity finding and follow its recorded remediation.",
                "route": "integrity",
                "specialist_route": "integrity",
                "resolution_predicate": (
                    "The same stable finding identity is absent from a newer complete report."
                ),
            }
        )

    unresolved_incident_states = {
        "open",
        "investigating",
        "mitigated",
        "monitoring",
    }
    for incident in operational_incidents.get("items") or []:
        if (
            not isinstance(incident, dict)
            or str(incident.get("status") or "").casefold()
            not in unresolved_incident_states
        ):
            continue
        incident_id = str(incident.get("incident_id") or "").strip()
        if not incident_id:
            continue
        owner = str(incident.get("owner") or "Unassigned")
        add(
            {
                "item_id": f"incident:{incident_id}",
                "work_kind": "operational_incident",
                "finding_code": None,
                "label": incident.get("summary") or incident_id,
                "status": incident.get("status"),
                "owner": owner,
                "attention_class": (
                    "human"
                    if normalize_console_owner(owner) == "human"
                    else "oversight"
                ),
                "authority": "Operational Incidents projection",
                "source_record_id": incident_id,
                "detected_at": incident.get("first_observed"),
                "next_action": incident.get("next_action"),
                "route": (
                    f"automation:logs:incidents:selected={urllib.parse.quote(incident_id)}"
                ),
                "specialist_route": (
                    f"automation:logs:incidents:selected={urllib.parse.quote(incident_id)}"
                ),
                "resolution_predicate": (
                    "The incident authority records exact recovery proof and Resolved status."
                ),
            }
        )

    unresolved_security_states = {
        "open",
        "investigating",
        "contained",
        "remediating",
        "monitoring",
    }
    security_projection = security_incidents or unavailable_incident_projection(
        "security",
        reason_code="security-incident-projection-not-supplied",
    )
    for incident in security_projection.get("items") or []:
        if (
            not isinstance(incident, dict)
            or str(incident.get("status") or "").casefold()
            not in unresolved_security_states
        ):
            continue
        incident_id = str(
            incident.get("security_incident_id") or ""
        ).strip()
        if not incident_id:
            continue
        owner = str(incident.get("owner") or "Unassigned")
        add(
            {
                "item_id": f"security-incident:{incident_id}",
                "work_kind": "security_incident",
                "finding_code": None,
                "label": incident.get("safe_summary") or incident_id,
                "status": incident.get("status"),
                "owner": owner,
                "attention_class": (
                    "human"
                    if normalize_console_owner(owner) == "human"
                    else "oversight"
                ),
                "authority": "Owner-local Security Incidents projection",
                "source_record_id": incident_id,
                "detected_at": incident.get("first_observed"),
                "next_action": incident.get("next_action"),
                "route": (
                    "automation:logs:security-incidents:selected="
                    f"{urllib.parse.quote(incident_id)}"
                ),
                "specialist_route": (
                    "automation:logs:security-incidents:selected="
                    f"{urllib.parse.quote(incident_id)}"
                ),
                "resolution_predicate": (
                    "The Security Incident authority records exact "
                    "security-specific closure proof and Resolved status."
                ),
            }
        )

    items.sort(
        key=lambda item: (
            0 if item.get("attention_class") == "human" else 1,
            str(item.get("detected_at") or ""),
            str(item.get("item_id") or ""),
        )
    )
    human_items = [
        item for item in items if item.get("attention_class") == "human"
    ]
    incident_sources_complete = (
        operational_incidents.get("complete") is True
        and security_projection.get("complete") is True
    )
    complete = (
        incident_sources_complete
        if require_private_incident_completeness
        else True
    )
    exact_counts = {
        "human": len(human_items),
        "oversight": len(items) - len(human_items),
        "all_open": len(items),
    }
    generation_id = "action-snapshot-" + hashlib.sha256(
        json.dumps(
            {
                "items": items,
                "complete": complete,
                "operational_incidents_complete": (
                    operational_incidents.get("complete") is True
                ),
                "security_incidents_complete": (
                    security_projection.get("complete") is True
                ),
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()[:20]
    return {
        "schema_version": 1,
        "generation_id": generation_id,
        "generated_at": generated_at,
        "availability": "current" if complete else "partial",
        "complete": complete,
        "items": items,
        "counts": exact_counts if complete else {
            "human": None,
            "oversight": None,
            "all_open": None,
        },
        "known_counts": exact_counts,
        "sources": {
            "operational_incidents": {
                "availability": operational_incidents.get("availability"),
                "complete": operational_incidents.get("complete") is True,
            },
            "security_incidents": {
                "availability": security_projection.get("availability"),
                "complete": security_projection.get("complete") is True,
            },
        },
        "predicates": {
            "human": {"attention_class": "human", "status": "unresolved"},
            "oversight": {"attention_class": "oversight", "status": "unresolved"},
            "all_open": {"status": "unresolved"},
        },
    }


def join_private_security_actions(
    action_snapshot: dict[str, object],
    security_snapshot: dict[str, object] | None,
) -> dict[str, object]:
    """Join minimized protected actions into one owner-local typed snapshot."""

    projected = copy.deepcopy(action_snapshot)
    items = [
        dict(item)
        for item in projected.get("items") or []
        if isinstance(item, dict)
    ]
    if not valid_private_security_assurance(security_snapshot):
        projected["private_join"] = {
            "security_assurance": "unavailable",
            "checked_at": None,
        }
        return projected
    for tool in security_snapshot.get("tools") or []:
        if (
            not isinstance(tool, dict)
            or tool.get("private_attention") != "yes"
            or tool.get("owner_class") not in {"Human", "Elim"}
        ):
            continue
        require_registered_classification(
            "work_kind", "security_protected_action"
        )
        tool_id = str(tool.get("tool_id") or "")
        human = tool.get("owner_class") == "Human"
        items.append(
            {
                "item_id": f"security-action:{tool_id}",
                "reference": f"security-action:{tool_id}",
                "work_kind": "security_protected_action",
                "finding_code": None,
                "label": (
                    "Review private security action"
                    if human
                    else "Private security remediation requires review"
                ),
                "category": "Protected security action",
                "severity": "warning",
                "status": "open",
                "owner": tool.get("owner_class"),
                "attention_class": "human" if human else "oversight",
                "attention": "human" if human else "oversight",
                "authority": "Owner-local security assurance projection",
                "reported_by": "Owner-local security assurance projection",
                "source_record_id": tool_id,
                "detected_at": tool.get("last_checked")
                or security_snapshot.get("checked_at"),
                "checked_at": security_snapshot.get("checked_at"),
                "next_action": (
                    "Open the protected security source and complete the "
                    "authorized review."
                ),
                "route": "automation:security",
                "specialist_route": "automation:security",
                "source_url": "#automation:security",
                "message": (
                    "Review private security action"
                    if human
                    else "Private security remediation requires review"
                ),
                "resolution_predicate": (
                    "A newer complete private security projection records "
                    "private_attention other than yes for this tool ID."
                ),
            }
        )
    item_ids = [str(item.get("item_id") or "") for item in items]
    if len(item_ids) != len(set(item_ids)):
        raise RuntimeError("Private Action snapshot contains duplicate item IDs.")
    human_count = sum(
        item.get("attention_class") == "human" for item in items
    )
    known_counts = {
        "human": human_count,
        "oversight": len(items) - human_count,
        "all_open": len(items),
    }
    complete = projected.get("complete") is True
    projected.update(
        {
            "items": items,
            "counts": known_counts if complete else {
                "human": None,
                "oversight": None,
                "all_open": None,
            },
            "known_counts": known_counts,
            "private_join": {
                "security_assurance": "complete",
                "checked_at": security_snapshot.get("checked_at"),
            },
        }
    )
    return projected


def build_queue_directory(
    *,
    progress: dict[str, object],
    preliminary_records: list[dict[str, object]],
    formal_candidates: list[dict[str, object]],
    pending_sources: list[dict[str, object]],
    review_recommendations: list[dict[str, object]],
    action_snapshot: dict[str, object],
    operational_incidents: dict[str, object],
    generated_at: str,
    security_incidents: dict[str, object] | None = None,
    transaction_recovery: dict[str, object] | None = None,
) -> dict[str, object]:
    pipeline = (
        progress.get("pipeline")
        if isinstance(progress.get("pipeline"), dict)
        else {}
    )
    active = [
        item
        for item in pipeline.get("items") or []
        if isinstance(item, dict) and item.get("mode") == "active"
    ]
    action_counts = (
        action_snapshot.get("counts")
        if isinstance(action_snapshot.get("counts"), dict)
        else {}
    )
    incident_complete = operational_incidents.get("complete") is True
    security_projection = security_incidents or unavailable_incident_projection(
        "security",
        reason_code="security-incident-projection-not-supplied",
    )
    security_incident_complete = security_projection.get("complete") is True
    transaction_projection = (
        transaction_recovery
        if valid_transaction_recovery_projection(transaction_recovery)
        else unavailable_transaction_recovery_projection()
    )
    transaction_complete = transaction_projection.get("complete") is True
    preserved_transaction_count = (
        sum(
            transaction_recovery_unresolved(item)
            for item in transaction_projection.get("items") or []
            if isinstance(item, dict)
        )
        if transaction_complete
        else None
    )
    definitions = [
        (
            "candidate_intake",
            len(preliminary_records),
            True,
            "preliminary candidate catalog membership",
            "planning:workbench:pipeline:work_class=Preliminary%20candidate",
            "planning:preliminary",
            "preliminary-candidate-catalog",
        ),
        (
            "formal_candidates",
            len(formal_candidates),
            True,
            "formal candidate dossier membership",
            "planning:workbench:pipeline:work_class=Formal%20candidate",
            "planning:candidates",
            "GitHub Issues and Project candidate projection",
        ),
        (
            "development",
            sum(item.get("status") == "Development" for item in active),
            True,
            "active Pipeline records with exact Status Development",
            "planning:workbench:pipeline:status=Development",
            "integrity",
            "typed Pipeline projection",
        ),
        (
            "research",
            sum(item.get("status") == "Research" for item in active),
            True,
            "active Pipeline records with exact Status Research",
            "planning:workbench:pipeline:status=Research",
            "integrity",
            "typed Pipeline projection",
        ),
        (
            "audits",
            sum(
                item.get("status") in {"Audit needed", "Audit in progress"}
                for item in active
            ),
            True,
            "active Pipeline records with an exact Audit Status",
            "planning:workbench:pipeline:status=Audit",
            "integrity",
            "typed Pipeline projection",
        ),
        (
            "external_review",
            sum(item.get("status") == "External review" for item in active),
            True,
            "Pipeline records in exact External review Status",
            "planning:workbench:pipeline:scope=review-ready-plus",
            "integrity",
            "typed Pipeline projection",
        ),
        (
            "pending_sources",
            len(pending_sources),
            True,
            "pending source catalog membership",
            "planning:sources:status=pending",
            "planning:sources",
            "pending source catalog",
        ),
        (
            "repository_reviews",
            len(review_recommendations),
            True,
            "typed exact-head Source Monitor recommendation",
            "automation:logs:sources",
            "automation:repository-gates",
            "Source Monitor recommendation projection",
        ),
        (
            "human_actions",
            action_counts.get("human"),
            action_snapshot.get("complete") is True,
            "shared Action snapshot attention_class equals human",
            "actions:my-items",
            "integrity",
            "typed Action snapshot",
        ),
        (
            "operational_incidents",
            (
                operational_incidents.get("unresolved_count")
                if incident_complete
                else None
            ),
            incident_complete,
            "unresolved Operational Incident lifecycle states",
            "automation:logs:incidents",
            "automation:logs:incidents",
            "Operational Incidents projection",
        ),
        (
            "security_incidents",
            (
                security_projection.get("unresolved_count")
                if security_incident_complete
                else None
            ),
            security_incident_complete,
            "unresolved owner-local Security Incident lifecycle states",
            "automation:logs:security-incidents",
            "automation:logs:security-incidents",
            "Owner-local Security Incidents projection",
        ),
        (
            "preserved_transactions",
            preserved_transaction_count,
            transaction_complete,
            "preserved transaction lacks recoverable-retirement proof",
            "automation:agents:run-coordinator-bot",
            "automation:agents:run-coordinator-bot",
            "Owner-local transaction lifecycle and recovery projection",
        ),
    ]
    queue_generation_id = "queue-directory-" + hashlib.sha256(
        json.dumps(definitions, sort_keys=True, ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()[:20]
    queues: list[dict[str, object]] = []
    for (
        queue_id,
        count,
        complete,
        predicate,
        route,
        problem_route,
        authority,
    ) in definitions:
        require_registered_classification("queue_id", queue_id)
        if queue_id == "operational_incidents":
            current_through = (
                operational_incidents.get("checked_at")
                or operational_incidents.get("trustworthy_through")
                or generated_at
            )
        elif queue_id == "security_incidents":
            current_through = (
                security_projection.get("checked_at")
                or security_projection.get("trustworthy_through")
            )
        elif queue_id == "preserved_transactions":
            current_through = transaction_projection.get("generated_at")
        elif queue_id == "human_actions":
            current_through = action_snapshot.get("generated_at") or generated_at
        elif queue_id == "repository_reviews":
            current_through = max(
                (
                    str(item.get("recorded_at") or "")
                    for item in review_recommendations
                    if isinstance(item, dict)
                ),
                default="",
            ) or generated_at
        elif queue_id in {"candidate_intake", "pending_sources"}:
            current_through = generated_at
        else:
            current_through = (
                progress.get("generatedAt")
                or progress.get("generated_at")
                or generated_at
            )
        queues.append(
            {
                "queue_id": queue_id,
                "label": next(
                    str(entry.get("label"))
                    for entry in console_classification_registry()[
                        "namespaces"
                    ]["queue_id"]
                    if entry.get("id") == queue_id
                ),
                "count": int(count) if complete and count is not None else None,
                "availability": "current" if complete else "unavailable",
                "complete": complete,
                "predicate": predicate,
                "authoritative_source": authority,
                "owner_writer": authority,
                "route": route,
                "problem_route": problem_route,
                "generation_id": queue_generation_id,
                "current_through": current_through,
                "problem_state": (
                    "problem"
                    if complete and isinstance(count, int) and count > 0
                    and queue_id in {
                        "operational_incidents",
                        "security_incidents",
                        "preserved_transactions",
                    }
                    else "none"
                    if complete
                    else "unavailable"
                ),
                "impact_state": (
                    operational_incidents.get("impact_state")
                    if queue_id == "operational_incidents"
                    else (
                        "yellow"
                        if queue_id == "security_incidents"
                        and complete
                        and isinstance(count, int)
                        and count > 0
                        else "green"
                        if queue_id == "security_incidents" and complete
                        else "gray"
                        if queue_id == "security_incidents"
                        else "yellow"
                        if queue_id == "preserved_transactions"
                        and complete
                        and isinstance(count, int)
                        and count > 0
                        else "green"
                        if queue_id == "preserved_transactions" and complete
                        else "gray"
                        if queue_id == "preserved_transactions"
                        else None
                    )
                ),
            }
        )
    directory_complete = all(item["complete"] for item in queues)
    return {
        "schema_version": 1,
        "generation_id": queue_generation_id,
        "generated_at": generated_at,
        "availability": "current" if directory_complete else "partial",
        "complete": directory_complete,
        "queues": queues,
    }


def overview_incident_identity(stage: str, message: str) -> tuple[str, str]:
    """Return a stable prerequisite/root-cause identity for compact incidents."""

    compact = re.sub(r"\s+", " ", message.casefold()).strip()
    if (
        "canonical arrp workspace is not reconciled with github" in compact
        or re.search(r"current branch (?:is )?.+ instead of main", compact)
    ):
        return (
            "host-repository-preflight",
            "Canonical ARRP workspace is off main and not reconciled with GitHub.",
        )
    if "isolated elim checkout contains a prior unsynchronized baseline" in compact:
        return (
            "elim-isolated-checkout",
            "The isolated Elim checkout contains a prior unsynchronized baseline.",
        )
    return (stage, message.strip() or "Unclassified automation incident.")


def overview_automation_stage_id(value: object) -> str | None:
    normalized = str(value or "").strip().casefold().replace("_", "-")
    aliases = {
        "case-monitor": "case-monitor-bot",
        "case-monitor-bot": "case-monitor-bot",
        "cases": "case-monitor-bot",
        "presidential-directives": "presidential-directives-bot",
        "presidential-directives-bot": "presidential-directives-bot",
        "directives": "presidential-directives-bot",
        "source-checker": "source-checker-bot",
        "source-checker-bot": "source-checker-bot",
        "sources": "source-checker-bot",
        "public-input": "public-intake",
        "public-intake": "public-intake",
        "progress": "project-console-progress-bot",
        "project-console-progress": "project-console-progress-bot",
        "project-console-progress-bot": "project-console-progress-bot",
        "integrity": "project-integrity-bot",
        "project-integrity": "project-integrity-bot",
        "project-integrity-bot": "project-integrity-bot",
        "elim": "elim",
    }
    return aliases.get(normalized)


def overview_automation_readiness(
    run_chain: dict[str, object],
    current_repository_gates: dict[str, object] | None = None,
    occurrence_projection: dict[str, object] | None = None,
) -> dict[str, object]:
    declared_repository_gates = (
        current_repository_gates
        if isinstance(current_repository_gates, dict)
        and current_repository_gates
        else run_chain.get("repository_gates")
        if isinstance(run_chain.get("repository_gates"), dict)
        else {}
    )
    gates_complete = declared_repository_gates.get("complete") is True
    future_run_gates = {
        "available": gates_complete,
        "count": (
            int(declared_repository_gates.get("count") or 0)
            if gates_complete
            else None
        ),
        "checked_at": declared_repository_gates.get("checked_at"),
        "oldest_age": declared_repository_gates.get("oldest_age"),
        "items": (
            declared_repository_gates.get("items")
            if isinstance(declared_repository_gates.get("items"), list)
            else []
        ),
        "reason": (
            declared_repository_gates.get("reason")
            or " · ".join(
                str(item)
                for item in (
                    declared_repository_gates.get("validation_errors") or []
                )
            )
            or "No complete typed automation-gate inventory is published."
        ),
        "availability": declared_repository_gates.get("availability"),
        "trustworthy_through": declared_repository_gates.get("trustworthy_through"),
        "known_blocker_count": declared_repository_gates.get("known_blocker_count"),
    }
    blockers: list[dict[str, object]] = []
    seen_blockers: set[tuple[str, str, str]] = set()

    def add_blocker(
        *,
        source: str,
        raw: dict[str, object],
        fallback_status: str = "blocked",
    ) -> None:
        stage_id = overview_automation_stage_id(
            raw.get("stage_id")
            or raw.get("stage")
            or raw.get("originating_stage")
            or raw.get("affected_stage")
        )
        reason = str(
            raw.get("reason")
            or raw.get("message")
            or raw.get("details")
            or raw.get("summary")
            or "Automation blocker recorded without detail."
        ).strip()
        blocker_id = str(
            raw.get("id")
            or raw.get("gate_id")
            or raw.get("number")
            or ""
        ).strip()
        key = (source, stage_id or "", blocker_id or reason.casefold())
        if key in seen_blockers:
            return
        seen_blockers.add(key)
        blockers.append(
            {
                "id": blocker_id or "blocker-"
                + hashlib.sha256("|".join(key).encode("utf-8")).hexdigest()[:12],
                "stage_id": stage_id,
                "status": str(
                    raw.get("status")
                    or raw.get("classification")
                    or fallback_status
                ).strip(),
                "reason": reason,
                "source": source,
                "recorded_at": (
                    raw.get("recorded_at")
                    or raw.get("created_at")
                    or raw.get("updated_at")
                ),
                "route": raw.get("route") or "automation:chain",
                "source_url": raw.get("url") or raw.get("source_url"),
            }
        )

    historical_repository_gates = (
        run_chain.get("repository_gates")
        if isinstance(run_chain.get("repository_gates"), dict)
        else {}
    )
    applied_stage_ids: set[str] = set()
    for gate in historical_repository_gates.get("items") or []:
        if not isinstance(gate, dict) or gate.get("affected_latest_attempt") is not True:
            continue
        affected_stages = (
            gate.get("affected_stages")
            if isinstance(gate.get("affected_stages"), list)
            else [gate.get("affected_stage")]
            if gate.get("affected_stage")
            else []
        )
        for stage_id in affected_stages:
            normalized_stage = overview_automation_stage_id(stage_id)
            if normalized_stage:
                applied_stage_ids.add(normalized_stage)
        add_blocker(
            source="repository_gate",
            raw={
                **gate,
                "affected_stage": affected_stages[0] if affected_stages else None,
            },
        )

    for failure in run_chain.get("failures") or []:
        if isinstance(failure, dict):
            if overview_automation_stage_id(failure.get("stage")) in applied_stage_ids:
                continue
            add_blocker(source="latest_attempt", raw=failure, fallback_status="failed")

    blocking_status = re.compile(r"fail|error|block|cancel|timeout", re.IGNORECASE)
    for stage in run_chain.get("stages") or []:
        if not isinstance(stage, dict):
            continue
        if blocking_status.search(str(stage.get("status") or "")):
            if overview_automation_stage_id(stage.get("id")) in applied_stage_ids:
                continue
            add_blocker(source="latest_attempt", raw=stage, fallback_status="failed")

    chain_status = str(run_chain.get("status") or "").strip()
    if run_chain and blocking_status.search(chain_status) and not blockers:
        add_blocker(
            source="latest_attempt",
            raw={
                "id": "run-coordinator",
                "status": chain_status,
                "reason": (
                    run_chain.get("next_action")
                    or "The latest attempt reports a blocking outcome without a typed stage."
                ),
                "recorded_at": (
                    run_chain.get("updated_at")
                    or run_chain.get("completed_at")
                ),
            },
        )

    declared_scheduled_attempt = (
        run_chain.get("latest_scheduled_attempt")
        if isinstance(run_chain.get("latest_scheduled_attempt"), dict)
        else {}
    )
    if re.search(
        r"schedule|launchd",
        str(run_chain.get("trigger") or ""),
        re.IGNORECASE,
    ):
        declared_scheduled_attempt = {
            "available": True,
            "chain_id": run_chain.get("chain_id"),
            "status": chain_status or "unavailable",
            "checked_at": (
                run_chain.get("host_updated_at")
                or run_chain.get("updated_at")
                or run_chain.get("completed_at")
            ),
            "failure_reason": run_chain.get("failure_reason"),
        }
    latest_scheduled_attempt = {
        "available": declared_scheduled_attempt.get("available") is True,
        "chain_id": declared_scheduled_attempt.get("chain_id"),
        "status": declared_scheduled_attempt.get("status") or "unavailable",
        "checked_at": (
            declared_scheduled_attempt.get("checked_at")
            or declared_scheduled_attempt.get("updated_at")
            or declared_scheduled_attempt.get("completed_at")
        ),
        "failure_reason": declared_scheduled_attempt.get("failure_reason"),
        "reason": (
            declared_scheduled_attempt.get("reason")
            or (
                ""
                if declared_scheduled_attempt.get("available") is True
                else "No typed latest scheduled-attempt record is published."
            )
        ),
    }

    result = {
        "schema_version": 1,
        "latest_attempt": {
            "available": bool(run_chain),
            "chain_id": run_chain.get("chain_id"),
            "status": chain_status or "unavailable",
            "trigger": run_chain.get("trigger"),
            "checked_at": (
                run_chain.get("host_updated_at")
                or run_chain.get("updated_at")
                or run_chain.get("completed_at")
            ),
            "blocker_count": len(blockers) if run_chain else None,
            "blockers": blockers,
            "reason": (
                ""
                if run_chain
                else "No run-chain snapshot is available."
            ),
        },
        "latest_scheduled_attempt": latest_scheduled_attempt,
        "future_run_gates": future_run_gates,
    }
    occurrences = (
        occurrence_projection.get("occurrences")
        if isinstance(occurrence_projection, dict)
        and isinstance(occurrence_projection.get("occurrences"), list)
        else []
    )
    by_id = {
        str(item.get("occurrence_id") or ""): item
        for item in occurrences
        if isinstance(item, dict) and str(item.get("occurrence_id") or "")
    }
    latest = by_id.get(
        str((occurrence_projection or {}).get("latest_attempt_id") or "")
    )
    latest_scheduled = by_id.get(
        str((occurrence_projection or {}).get("latest_scheduled_attempt_id") or "")
    )
    if latest:
        result["latest_attempt"] = {
            "available": True,
            "occurrence_id": latest.get("occurrence_id"),
            "chain_id": latest.get("occurrence_id"),
            "status": latest.get("status"),
            "trigger": latest.get("trigger"),
            "checked_at": (
                latest.get("updated_at")
                or latest.get("completed_at")
                or latest.get("started_at")
            ),
            "blocker_count": len(latest.get("blockers") or []),
            "blockers": latest.get("blockers") or [],
            "reason": "",
        }
    if latest_scheduled:
        result["latest_scheduled_attempt"] = {
            "available": True,
            "occurrence_id": latest_scheduled.get("occurrence_id"),
            "chain_id": latest_scheduled.get("occurrence_id"),
            "status": latest_scheduled.get("status"),
            "checked_at": (
                latest_scheduled.get("scheduled_for")
                or latest_scheduled.get("updated_at")
                or latest_scheduled.get("completed_at")
            ),
            "failure_reason": (
                (latest_scheduled.get("blockers") or [{}])[0].get("reason")
                if latest_scheduled.get("blockers")
                else None
            ),
            "reason": "",
        }
    return result


def public_safe_automation_readiness(
    projection: dict[str, object],
) -> dict[str, object]:
    """Keep readiness counts and timestamps while redacting diagnostic payloads."""

    safe = copy.deepcopy(projection)
    for key in ("latest_attempt", "latest_scheduled_attempt"):
        item = safe.get(key)
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        safe_item = {
            field: item.get(field)
            for field in (
                "available",
                "occurrence_id",
                "chain_id",
                "status",
                "checked_at",
                "blocker_count",
            )
            if field in item
        }
        safe_item["trigger"] = public_safe_trigger(item.get("trigger"))
        safe_item["reason"] = safe_automation_explanation(
            status, subject="The latest attempt"
        )
        safe_item["failure_reason"] = (
            safe_automation_explanation(status, subject="The latest scheduled attempt")
            if status in {"failed", "blocked", "degraded"}
            else None
        )
        safe_item["blockers"] = [
            {
                "id": f"public-blocker-{index}",
                "stage_id": blocker.get("stage_id"),
                "status": str(blocker.get("status") or "blocked"),
                "recorded_at": blocker.get("recorded_at"),
                "reason": safe_automation_explanation(
                    blocker.get("status") or "blocked",
                    subject="A recorded automation blocker",
                ),
            }
            for index, blocker in enumerate(item.get("blockers") or [], start=1)
            if isinstance(blocker, dict)
        ]
        safe[key] = safe_item
    gates = safe.get("future_run_gates")
    if isinstance(gates, dict):
        safe["future_run_gates"] = {
            field: gates.get(field)
            for field in (
                "available",
                "count",
                "checked_at",
                "oldest_age",
                "availability",
                "trustworthy_through",
                "known_blocker_count",
            )
            if field in gates
        } | {
            "reason": (
                "A complete typed automation-gate inventory is available."
                if gates.get("available") is True
                else "A complete typed automation-gate inventory is unavailable."
            ),
            "items": [
                {
                    "id": f"public-gate-{index}",
                    "affected_stages": item.get("affected_stages"),
                    "affected_latest_attempt": item.get("affected_latest_attempt"),
                }
                for index, item in enumerate(gates.get("items") or [], start=1)
                if isinstance(item, dict)
            ],
        }
    return safe


def overview_data(
    *,
    candidates: list[dict[str, object]],
    active_horizon_records: list[dict[str, object]],
    monitoring_issues: list[dict[str, object]],
    pending_sources: list[dict[str, object]],
    review_recommendations: list[dict[str, object]],
    progress: dict[str, object],
    integrity: dict[str, object],
    run_chain: dict[str, object],
    publication: dict[str, object],
    project_logs: list[dict[str, object]],
    agent_registry: list[dict[str, object]],
    watcher_metadata: dict[str, object],
    source_checker: dict[str, object],
    automation_occurrences: dict[str, object] | None = None,
    action_snapshot: dict[str, object] | None = None,
    queue_directory: dict[str, object] | None = None,
    repository_gates: dict[str, object] | None = None,
    operational_incidents: dict[str, object] | None = None,
    security_incidents: dict[str, object] | None = None,
) -> dict[str, object]:
    action_snapshot_supplied = action_snapshot is not None
    automation_occurrences = automation_occurrences or {
        "schema_version": 2,
        "checked_at": None,
        "occurrences": [],
        "latest_attempt_id": None,
        "latest_scheduled_attempt_id": None,
        "last_fully_successful_occurrence": None,
        "next_ordinary_run": {"available": False, "scheduled_for": None},
        "next_full_review_epoch": {"available": False, "scheduled_for": None},
        "role_currentness": {"state": "unavailable"},
        "trustworthy_through": None,
    }
    action_snapshot = action_snapshot or {
        "availability": "unavailable",
        "complete": False,
        "items": [],
        "counts": {"human": None, "oversight": None, "all_open": None},
    }
    queue_directory = queue_directory or {
        "availability": "unavailable",
        "complete": False,
        "queues": [],
    }
    progress_metrics = (
        progress.get("metrics") if isinstance(progress.get("metrics"), dict) else {}
    )
    integrity_current = (
        integrity.get("current")
        if isinstance(integrity.get("current"), dict)
        else {}
    )
    automation_readiness = public_safe_automation_readiness(
        overview_automation_readiness(
            run_chain, repository_gates or {}, automation_occurrences
        )
    )
    recommendation_ids = {
        str(item.get("id") or "").strip()
        for item in review_recommendations
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }
    activity: list[dict[str, object]] = []
    for log in project_logs:
        log_id = str(log.get("id") or "").strip()
        log_title = str(log.get("title") or log_id or "Project log").strip()
        for entry in log.get("entries") or []:
            if not isinstance(entry, dict):
                continue
            values = entry.get("values") if isinstance(entry.get("values"), dict) else {}
            # The typed repository-review projection already owns these Source
            # Monitor events. Keeping the corresponding generic log row would
            # show one governance action twice in the compact Overview.
            if (
                log_id == "source-monitor"
                and str(values.get("activity") or "").strip() in recommendation_ids
            ):
                continue
            actor = (
                values.get("agent")
                or values.get("actor")
                or (
                    "Human project governance"
                    if log_id in {"horizon", "changes"}
                    else log_title
                )
            )
            outcome = values.get("outcome") or values.get("result")
            affected_scope = (
                values.get("affected")
                or values.get("record")
                or values.get("record_ids")
                or values.get("scope")
            )
            summary = (
                values.get("summary")
                or values.get("change")
                or values.get("activity")
                or values.get("task")
            )
            manager_effect = (
                values.get("manager_action")
                or values.get("manager_effect")
                or values.get("next_action")
                or values.get("effect")
            )
            headline = (
                values.get("record")
                or values.get("watcher")
                or values.get("change")
                or outcome
                or entry.get("id")
            )
            activity.append(
                {
                    "id": entry.get("id"),
                    "log": log_id,
                    "date": values.get("date"),
                    "record": values.get("record"),
                    "title": " · ".join(
                        str(value).strip()
                        for value in (actor, headline)
                        if str(value or "").strip()
                    ),
                    "actor": actor,
                    "source": log_title,
                    "outcome": outcome,
                    "affected_scope": affected_scope,
                    "summary": summary,
                    "manager_effect": manager_effect,
                    "owner": values.get("owner") or values.get("agent"),
                    "kind": "project_log",
                    "route": f"logs:{log_id}",
                }
            )
    activity.sort(key=lambda item: str(item.get("date") or ""), reverse=True)
    delivery_items = (
        progress.get("delivery_items")
        if isinstance(progress.get("delivery_items"), list)
        else []
    )
    delivery_available = isinstance(progress.get("delivery_items"), list)
    progress_items = [
        item
        for collection in (
            progress.get("proposals") or [],
            progress.get("candidates") or [],
            delivery_items,
        )
        for item in collection
        if isinstance(item, dict)
    ]
    pipeline_items = [
        item
        for item in (progress.get("pipeline") or {}).get("items", [])
        if isinstance(item, dict)
    ]
    active_pipeline_items = [
        item for item in pipeline_items if item.get("mode") == "active"
    ]
    release_blocker_items = [
        {
            "identifier": item.get("identifier"),
            "title": item.get("title"),
            "priority": item.get("priority"),
            "status": item.get("workflowStatus"),
            "workstream": item.get("workstream"),
            "url": item.get("url"),
            "route": "progress",
        }
        for item in progress_items
        if normalize_console_owner(
            item.get("releaseBlocker") or item.get("release_blocker")
        )
        in {"yes", "true"}
    ]
    critical_high_blockers = [
        item
        for item in release_blocker_items
        if normalize_console_owner(item.get("priority")) in {"critical", "high"}
    ]
    release_fields_available = bool(progress_items) and all(
        ("releaseBlocker" in item or "release_blocker" in item)
        and "priority" in item
        for item in progress_items
    )
    human_actions: list[dict[str, object]] = []
    for item in review_recommendations:
        if normalize_console_owner(item.get("action_owner")) != "human":
            continue
        human_actions.append(
            {
                "id": item.get("id"),
                "kind": "repository_review_decision",
                "label": item.get("human_question") or item.get("recommendation"),
                "priority": "Human decision",
                "route": item.get("console_target") or "logs:source-monitor",
                "source_url": item.get("source_url"),
            }
        )
    for item in progress_items:
        if normalize_console_owner(item.get("workflowStatus")) != "human decision needed":
            continue
        human_actions.append(
            {
                "id": item.get("identifier") or item.get("projectItemId"),
                "kind": "project_human_decision",
                "label": item.get("title"),
                "priority": item.get("priority"),
                "route": "actions",
                "source_url": item.get("url"),
            }
        )
    unresolved_host_actions = [
        item
        for item in run_chain.get("host_action_items") or []
        if isinstance(item, dict)
        and item.get("resolved") is not True
        and normalize_console_owner(item.get("owner")) == "human"
    ]
    for item in unresolved_host_actions:
        action_kind = normalize_console_owner(item.get("kind")).replace(" ", "_")
        if action_kind not in {
            "approval",
            "authorization",
            "credential_required",
            "go_no_go",
            "human_decision",
            "policy_decision",
            "review_decision",
        }:
            # Operational failures belong in the grouped incident projection,
            # even when their recovery owner is human. Retry rows are not
            # separate human decisions.
            continue
        human_actions.append(
            {
                "id": item.get("id"),
                "kind": action_kind,
                "label": item.get("next_action") or item.get("summary"),
                "priority": "Automation attention",
                "route": "automation",
                "source_url": None,
            }
        )
    incident_projection = operational_incidents or {
        "availability": "unavailable",
        "complete": False,
        "unresolved_count": None,
        "items": [],
        "impact_state": "gray",
        "reason": "Operational incident projection was not supplied.",
    }
    security_incident_projection = (
        security_incidents
        or unavailable_incident_projection(
            "security",
            reason_code="security-incident-projection-not-supplied",
        )
    )
    incident_complete = incident_projection.get("complete") is True
    active_incidents = [
        item
        for item in incident_projection.get("items") or []
        if isinstance(item, dict)
        and item.get("status") in {"open", "investigating", "mitigated", "monitoring"}
    ]
    if not action_snapshot_supplied:
        action_snapshot = {
            "availability": "stale",
            "complete": False,
            "items": human_actions,
            "counts": {
                "human": len(human_actions),
                "oversight": None,
                "all_open": None,
            },
            "reason": (
                "Compatibility-only overview call did not supply the typed Action snapshot."
            ),
        }
    domain_signals = []
    for domain, payload, timestamp, route in (
        (
            "progress",
            progress,
            progress.get("generated_at") or progress.get("generatedAt"),
            "progress",
        ),
        (
            "integrity",
            integrity,
            integrity.get("generated_at") or integrity_current.get("generated_at"),
            "integrity",
        ),
        (
            "source_checker",
            source_checker,
            source_checker.get("checked_at"),
            "sources:assurance",
        ),
    ):
        availability = str(payload.get("availability") or "")
        if not payload:
            status = "unavailable"
            reason = "No valid feed generation is available."
        elif availability in {"stale", "unavailable"}:
            status = availability
            reason = "The feed does not completely cover its current authoritative source."
        elif not availability:
            status = "contract_unavailable"
            reason = "Legacy feed is present without a declared truth contract."
        else:
            status = availability
            reason = ""
        if status not in {"current", "available"}:
            domain_signals.append(
                {
                    "domain": domain,
                    "status": status,
                    "reason": reason,
                    "timestamp": timestamp,
                    "route": route,
                }
            )
    automation_failures = [
        item for item in run_chain.get("failures") or [] if isinstance(item, dict)
    ]
    if not run_chain:
        domain_signals.append(
            {
                "domain": "automation",
                "status": "unavailable",
                "reason": "No run-chain snapshot is available.",
                "timestamp": None,
                "route": "automation",
            }
        )
    elif automation_failures:
        domain_signals.append(
            {
                "domain": "automation",
                "status": "attention",
                "reason": "The current run chain reports an active failure or hold.",
                "timestamp": run_chain.get("updated_at")
                or run_chain.get("completed_at"),
                "route": "automation",
            }
        )
    release_readiness = (
        publication.get("release_readiness")
        if isinstance(publication.get("release_readiness"), dict)
        else {}
    )
    if release_readiness.get("status") != "ready":
        domain_signals.append(
            {
                "domain": "publication_release",
                "status": release_readiness.get("status") or "unavailable",
                "reason": release_readiness.get("status_explanation")
                or "Release readiness is unavailable.",
                "timestamp": None,
                "route": "publication:analysis",
            }
        )
    material_changes = active_issue_score_activity(progress)
    next_reviews: list[dict[str, object]] = []
    if ALLOW_PRIVATE_CONSOLE_INPUTS and REVIEW_EPOCHS.is_file():
        epoch_rows = [
            json.loads(line)
            for line in REVIEW_EPOCHS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if epoch_rows:
            epoch = epoch_rows[-1]
            next_reviews.append(
                {
                    "kind": "review_epoch",
                    "label": "Comprehensive Review Epoch",
                    "due_at": epoch.get("next_due_at"),
                    "status": epoch.get("stability_status"),
                    "trigger": epoch.get("triggering_reason"),
                    "route": "logs:agents",
                }
            )
    for item in progress_items:
        next_audit = item.get("nextAudit") or item.get("next_audit")
        if not str(next_audit or "").strip() or normalize_console_owner(
            next_audit
        ) == "not recorded":
            continue
        next_reviews.append(
            {
                "kind": "project_review_trigger",
                "label": item.get("identifier") or item.get("title"),
                "due_at": None,
                "status": item.get("workflowStatus"),
                "trigger": next_audit,
                "route": (
                    "actions"
                    if item.get("workflowStatus") == "Human decision needed"
                    else "planning:publication"
                    if item.get("workflowStatus") == "Publication approval"
                    else f"planning:workbench:pipeline:selected={item.get('identifier')}"
                ),
                "source_url": item.get("url"),
            }
        )
    source_completeness = (
        source_checker.get("completeness")
        if isinstance(source_checker.get("completeness"), dict)
        else {}
    )
    integrity_counts = (
        integrity_current.get("counts")
        if isinstance(integrity_current.get("counts"), dict)
        else {}
    )
    integrity_findings_value = integrity_counts.get("findings")
    integrity_findings_available = (
        bool(integrity)
        and str(integrity.get("availability") or "") != "unavailable"
        and isinstance(integrity_findings_value, (int, float))
        and not isinstance(integrity_findings_value, bool)
    )
    current_through_sources = [
        {
            "producer": "project-console-progress-bot",
            "value": progress.get("trustworthy_through")
            or progress.get("generated_at")
            or progress.get("generatedAt"),
            "availability": progress.get("availability"),
        },
        {
            "producer": "project-integrity-bot",
            "value": integrity.get("trustworthy_through")
            or integrity.get("generated_at")
            or integrity_current.get("generated_at"),
            "availability": integrity.get("availability"),
        },
        {
            "producer": "source-checker-bot",
            "value": source_checker.get("trustworthy_through")
            or source_checker.get("checked_at"),
            "availability": source_checker.get("availability"),
        },
        {
            "producer": "run-coordinator-bot",
            "value": automation_occurrences.get("trustworthy_through"),
            "availability": (
                (automation_occurrences.get("role_currentness") or {}).get("state")
                if isinstance(
                    automation_occurrences.get("role_currentness"), dict
                )
                else "unavailable"
            ),
        },
    ]
    parsed_current_through = [
        parsed_utc(item["value"])
        for item in current_through_sources
        if str(item.get("availability") or "")
        in {"current", "available", "stale"}
    ]
    parsed_current_through = [
        value for value in parsed_current_through if value is not None
    ]
    data_current_through = {
        "available": (
            len(parsed_current_through) == len(current_through_sources)
        ),
        "value": (
            min(parsed_current_through).isoformat()
            if len(parsed_current_through) == len(current_through_sources)
            else None
        ),
        "basis": "producer-declared trustworthy-through boundaries",
        "sources": current_through_sources,
        "reason": (
            ""
            if len(parsed_current_through) == len(current_through_sources)
            else "One or more required producers did not declare a trustworthy-through boundary."
        ),
    }
    def data_row(
        *,
        feed_id: str,
        label: str,
        producer: str,
        feed: dict[str, object],
        checked: object,
        route: str,
        recovery_route: str,
    ) -> dict[str, object]:
        completeness = (
            feed.get("completeness")
            if isinstance(feed.get("completeness"), dict)
            else {}
        )
        availability = str(feed.get("availability") or "unavailable")
        complete = completeness.get("complete") is True
        return {
            "feed_id": feed_id,
            "label": label,
            "availability": availability,
            "complete": complete,
            "reason": (
                feed.get("availability_reason")
                or feed.get("reason")
                or (
                    "The producer declares this projection complete."
                    if complete
                    else "The producer does not establish complete current coverage."
                )
            ),
            "trustworthy_through": feed.get("trustworthy_through") or checked,
            "producer": producer,
            "route": route,
            "recovery_route": recovery_route,
            "generation_id": feed.get("generation_id"),
            "schema_errors": feed.get("projection_errors") or [],
        }

    occurrence_currentness = (
        automation_occurrences.get("role_currentness")
        if isinstance(automation_occurrences.get("role_currentness"), dict)
        else {}
    )
    data_directory = {
        "schema_version": 1,
        "generated_at": automation_occurrences.get("checked_at"),
        "rows": [
            data_row(
                feed_id="progress",
                label="Progress",
                producer="project-console-progress-bot",
                feed=progress,
                checked=progress.get("generatedAt")
                or progress.get("generated_at"),
                route="progress",
                recovery_route="automation:agents:project-console-progress-bot",
            ),
            data_row(
                feed_id="sources",
                label="Sources",
                producer="source-checker-bot",
                feed=source_checker,
                checked=source_checker.get("checked_at"),
                route="planning:sources",
                recovery_route="automation:agents:source-checker-bot",
            ),
            {
                "feed_id": "automation_occurrences",
                "label": "Operations overview",
                "availability": occurrence_currentness.get("state")
                or "unavailable",
                "complete": bool(automation_occurrences.get("occurrences")),
                "reason": (
                    ""
                    if occurrence_currentness.get("state") == "current"
                    else "The authoritative occurrence projection is stale or unavailable."
                ),
                "trustworthy_through": automation_occurrences.get(
                    "trustworthy_through"
                ),
                "producer": "run-coordinator-occurrence-projection",
                "route": "automation:overview",
                "recovery_route": "automation:agents:run-coordinator-bot",
                "generation_id": None,
                "schema_errors": [],
            },
            {
                "feed_id": "candidates",
                "label": "Candidates",
                "availability": "current",
                "complete": True,
                "reason": "The current Console generation includes the complete candidate inputs.",
                "trustworthy_through": progress.get("generatedAt")
                or progress.get("generated_at"),
                "producer": "project-console-candidate-projection",
                "route": "planning:candidates",
                "recovery_route": "integrity",
                "generation_id": progress.get("generation_id"),
                "schema_errors": [],
                "new_updated_signal": {
                    "available": False,
                    "count": None,
                    "reason": "The candidate producer does not publish a typed new/updated signal.",
                },
            },
            data_row(
                feed_id="integrity",
                label="Integrity",
                producer="project-integrity-bot",
                feed=integrity,
                checked=integrity.get("generated_at")
                or integrity_current.get("generated_at"),
                route="integrity",
                recovery_route="automation:agents:project-integrity-bot",
            ),
        ],
    }
    usage_points = (
        run_chain.get("usage_points")
        if isinstance(run_chain.get("usage_points"), list)
        else []
    )
    typed_usage_points = [
        {
            "point_id": item.get("point_id"),
            "window_id": item.get("window_id"),
            "recorded_at": item.get("recorded_at"),
            "consumed_percent": item.get("consumed_percent"),
            "remaining_percent": item.get("remaining_percent"),
            "source_occurrence_id": item.get("source_occurrence_id"),
        }
        for item in usage_points
        if isinstance(item, dict)
        and str(item.get("point_id") or "").strip()
        and parsed_utc(item.get("recorded_at")) is not None
        and isinstance(item.get("consumed_percent"), (int, float))
        and not isinstance(item.get("consumed_percent"), bool)
    ]
    review_epoch = (
        run_chain.get("review_epoch")
        if isinstance(run_chain.get("review_epoch"), dict)
        else {}
    )
    capacity_history = {
        "schema_version": 1,
        "availability": "current" if typed_usage_points else "unavailable",
        "complete": bool(typed_usage_points),
        "points": typed_usage_points,
        "review_epochs": (
            [
                {
                    "epoch_id": review_epoch.get("epoch_id")
                    or review_epoch.get("review_id"),
                    "completed_at": review_epoch.get("last_completed_at"),
                }
            ]
            if (
                (review_epoch.get("epoch_id") or review_epoch.get("review_id"))
                and parsed_utc(review_epoch.get("last_completed_at")) is not None
            )
            else []
        ),
        "reason": (
            ""
            if typed_usage_points
            else "No typed usage points are published; narrative Elim prose is not parsed."
        ),
    }
    return {
        "automation_occurrences": automation_occurrences,
        "automation_readiness": automation_readiness,
        "data_current_through": data_current_through,
        "capacity_history": capacity_history,
        "data_directory": data_directory,
        "action_snapshot": action_snapshot,
        "queue_directory": queue_directory,
        "operational_incidents": incident_projection,
        "security_incidents": security_incident_projection,
        "manager_focus": {
            "human_decisions": (
                (action_snapshot.get("counts") or {}).get("human")
                if isinstance(action_snapshot.get("counts"), dict)
                else None
            ),
            "human_actions": [
                item
                for item in action_snapshot.get("items") or []
                if isinstance(item, dict)
                and item.get("attention_class") == "human"
            ][:20],
            "active_incidents": (
                int(incident_projection.get("unresolved_count") or 0)
                if incident_complete
                else None
            ),
            "incidents": active_incidents[:10],
            "release_blockers": (
                len(release_blocker_items) if release_fields_available else None
            ),
            "release_blocker_fields_available": release_fields_available,
            "critical_high_release_blockers": (
                len(critical_high_blockers) if release_fields_available else None
            ),
            "critical_high_blocker_items": critical_high_blockers[:15],
            "integrity_findings": (
                int(integrity_findings_value)
                if integrity_findings_available
                else None
            ),
            "integrity_findings_available": integrity_findings_available,
            "source_checker_complete": source_completeness.get("complete"),
            "delivery_items": len(delivery_items) if delivery_available else None,
            "delivery_items_available": delivery_available,
            "domain_attention": domain_signals,
            "next_reviews": next_reviews[:15],
        },
        "queue_counts": {
            "preliminary_candidates": len(candidates),
            "formal_candidates": len(active_horizon_records),
            "monitoring_issues": len(monitoring_issues),
            "pending_sources": len(pending_sources),
            "repository_recommendations": len(review_recommendations),
            "delivery_items": len(delivery_items) if delivery_available else None,
            "human_actions": (
                (action_snapshot.get("counts") or {}).get("human")
                if isinstance(action_snapshot.get("counts"), dict)
                else None
            ),
            "operational_incidents": (
                int(incident_projection.get("unresolved_count") or 0)
                if incident_complete
                else None
            ),
            "development": sum(
                1 for item in active_pipeline_items
                if item.get("status") == "Development"
            ),
            "research": sum(
                1 for item in active_pipeline_items
                if item.get("status") == "Research"
            ),
            "audits": sum(
                1 for item in active_pipeline_items
                if item.get("status") in {"Audit needed", "Audit in progress"}
            ),
            "external_review": sum(
                1 for item in active_pipeline_items
                if item.get("status") == "External review"
            ),
            "critical_high_release_blockers": (
                len(critical_high_blockers) if release_fields_available else None
            ),
        },
        "activity": material_changes[:12],
        "agents": {
            "registered": len(agent_registry),
            "last_chain_id": run_chain.get("chain_id") or run_chain.get("id"),
            "chain_status": run_chain.get("status"),
        },
        "services": watcher_metadata,
        "usage": run_chain.get("usage") or run_chain.get("usage_snapshot"),
        "progress_summary": {
            "generated_at": progress.get("generated_at") or progress.get("generatedAt"),
            "source_revision": progress.get("source_revision"),
            "availability": progress.get("availability"),
            "ready": progress_metrics.get("ready"),
            "total": progress_metrics.get("total"),
            "remaining": progress_metrics.get("remaining"),
            "track_status": progress_metrics.get("trackStatus"),
            "delivery_items": len(delivery_items) if delivery_available else None,
        },
        "integrity_summary": {
            "generated_at": integrity.get("generated_at")
            or integrity_current.get("generated_at"),
            "source_revision": integrity.get("source_revision")
            or integrity_current.get("revision"),
            "availability": integrity.get("availability"),
            "result": integrity_current.get("result"),
            "counts": integrity_current.get("counts") or {},
        },
        "automation_summary": {
            "chain_id": run_chain.get("chain_id") or run_chain.get("id"),
            "status": run_chain.get("status"),
            "generated_at": run_chain.get("generated_at")
            or run_chain.get("completed_at"),
            "stage_count": len(run_chain.get("stages") or []),
        },
        "publication_summary": {
            "disposition_counts": publication.get("disposition_counts") or {},
            "build_count": len(publication.get("builds") or []),
            "topic_product_count": len(publication.get("topic_products") or []),
        },
        "source_checker_summary": {
            "checked_at": source_checker.get("checked_at"),
            "source_revision": source_checker.get("source_revision"),
            "availability": source_checker.get("availability"),
            "expected_count": source_checker.get("expected_count"),
            "actual_count": source_checker.get("actual_count"),
            "counts": source_checker.get("counts") or {},
        },
    }


def normalize_console_owner(value: object) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def linked_incident_ids(
    projection: dict[str, object], *typed_links: str
) -> list[str]:
    active_links = (
        projection.get("active_links")
        if isinstance(projection.get("active_links"), dict)
        else {}
    )
    return sorted(
        {
            str(incident_id)
            for link in typed_links
            for incident_id in active_links.get(link, [])
            if str(incident_id).strip()
        }
    )


def run_stage_incident_ids(
    projection: dict[str, object], run_id: object, stage_id: object
) -> list[str]:
    exact_run = str(run_id or "").strip()
    exact_link = f"automation-role:{stage_id}"
    if not exact_run:
        return []
    return sorted(
        {
            str(incident.get("incident_id"))
            for incident in projection.get("items") or []
            if isinstance(incident, dict)
            and exact_run in (incident.get("affected_runs") or [])
            and exact_link in (incident.get("active_links") or [])
            and str(incident.get("incident_id") or "").strip()
        }
    )


def repository_gate_snapshot(refresh: bool) -> dict[str, object]:
    def loaded(path: Path) -> dict[str, object] | None:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    last_good = loaded(REPOSITORY_GATES_LAST_GOOD)
    if refresh:
        token = (
            os.environ.get("GH_TOKEN")
            or os.environ.get("GITHUB_TOKEN")
            or ""
        )
        if not token:
            credential = subprocess.run(
                ["gh", "auth", "token"],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if credential.returncode == 0:
                token = credential.stdout.strip()
        snapshot = produce_repository_gate_snapshot(
            repository="Thorncrag/ARRP",
            declarations_path=REPOSITORY_GATE_DECLARATIONS,
            token=token,
            last_good=last_good,
        )
        token = ""
        atomic_write_text(
            REPOSITORY_GATES_SNAPSHOT,
            json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        )
        if snapshot.get("complete") is True:
            atomic_write_text(
                REPOSITORY_GATES_LAST_GOOD,
                json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
            )
        return snapshot
    return loaded(REPOSITORY_GATES_SNAPSHOT) or {
        "schema_version": 1,
        "availability": "unavailable",
        "complete": False,
        "count": None,
        "known_blocker_count": 0,
        "items": [],
        "reason": "No current repository-gate snapshot is available.",
    }


def owner_incident_snapshots(
    private_authority: PrivateProjectAuthority | None = None,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    """Load private incident authorities without granting successor activation."""

    operational = project_incident_log(OPERATIONAL_INCIDENT_LOG)
    try:
        if private_authority is None:
            raise PathAuthorityError(
                "private staging authority is unavailable"
            )
    except PathAuthorityError:
        return (
            operational,
            unavailable_security_projection("private-authority-unavailable"),
            unavailable_incident_relations("private-authority-unavailable"),
        )

    security_path = private_authority.records_output(
        SECURITY_INCIDENT_RELATIVE
    )
    security = project_security_incident_log(security_path)
    if (
        operational.get("complete") is not True
        or security.get("complete") is not True
    ):
        return (
            operational,
            security,
            unavailable_incident_relations("incident-authority-incomplete"),
        )

    relation_path = private_authority.records_output(
        INCIDENT_RELATIONS_RELATIVE
    )
    if not relation_path.exists():
        return (
            operational,
            security,
            unavailable_incident_relations("incident-relations-missing"),
        )
    try:
        relations = relationship_projection(
            read_relation_events(relation_path),
            known_operational_ids={
                str(item.get("incident_id") or "")
                for item in operational.get("items") or []
                if isinstance(item, dict)
            },
            known_security_ids={
                str(item.get("security_incident_id") or "")
                for item in security.get("items") or []
                if isinstance(item, dict)
            },
        )
    except (OSError, SecurityIncidentContractError):
        relations = unavailable_incident_relations(
            "incident-relations-invalid"
        )
    return operational, security, relations


def _component_registry_source_record(
    component_id: str,
    component: dict[str, object],
) -> dict[str, object]:
    source = component["canonical_source"]
    if isinstance(source, str):
        return {
            "kind": "repository_path",
            "value": source,
            "url": (
                "https://github.com/Thorncrag/ARRP/blob/main/"
                + urllib.parse.quote(source)
            ),
        }
    if not isinstance(source, dict):
        raise RuntimeError(
            f"Component {component_id} has no canonical source."
        )
    kind = source.get("kind")
    value = source.get("value")
    if not isinstance(kind, str) or not isinstance(value, str):
        raise RuntimeError(
            f"Component {component_id} has an invalid canonical source."
        )
    url = None
    if kind == "repository_directory":
        url = (
            "https://github.com/Thorncrag/ARRP/tree/main/"
            + urllib.parse.quote(value.rstrip("/"))
        )
    return {"kind": kind, "value": value, "url": url}


def _component_registry_console_routes() -> dict[str, str]:
    modes = (
        "components",
        "classes",
        "types",
        "lifecycles",
        "authority",
        "relationships",
        "directories",
        "exemptions",
        "unresolved",
        "routing",
        "terminology",
        "codeowners",
    )
    return {
        mode: f"automation:component-registry:{mode}"
        for mode in modes
    }


def component_registry_console_snapshot(
    routing_view: dict[str, object],
    *,
    generated_at: str,
    root: Path = ROOT,
) -> dict[str, object]:
    """Project exact Registry v4 facts without duplicating canonical records."""

    validation_mode = routing_view.get("validation_mode")
    expected_posture = {
        "proposed_revision_validation": ("proposed", False),
        "adopted_configuration_validation": ("adopted", True),
    }.get(validation_mode)
    if (
        routing_view.get("schema_version") != 4
        or expected_posture is None
        or routing_view.get("registry_status") != expected_posture[0]
        or routing_view.get("authoritative") is not False
        or routing_view.get("executable") is not False
        or routing_view.get("source_bytes_current") is not expected_posture[1]
        or routing_view.get("predecessor_route_consulted") is not False
        or not isinstance(routing_view.get("_validated_registry"), dict)
    ):
        raise RuntimeError(
            "Console requires the exact Registry v4 configuration view."
        )
    registry = routing_view["_validated_registry"]
    if (
        registry.get("schema_version") != 4
        or registry.get("registry_revision") != 7
    ):
        raise RuntimeError(
            "Console requires exact Registry schema 4 and revision 7."
        )

    component_entries = registry["components"]["entries"]
    relationship_entries = registry["relationships"]["entries"]
    scope_entries = registry["directory_scopes"]["entries"]
    exemption_entries = registry["registration_exemptions"]["entries"]
    routes = _component_registry_console_routes()

    components: list[dict[str, object]] = []
    projected_component_fields = {
        "display_name",
        "classification",
        "canonical_source",
        "owner",
        "information_handling",
        "lifecycle",
        "revision_mode",
        "retention_bases",
        "supporting_artifacts",
        "operational_status",
        "execution_controls",
    }
    component_entry_fields: dict[str, list[str]] = {}
    for component_id, component in component_entries.items():
        component_entry_fields[component_id] = sorted(
            projected_component_fields.intersection(component)
        )
        components.append(
            {
                "stable_id": component_id,
                "display_name": component["display_name"],
                "classification": copy.deepcopy(
                    component["classification"]
                ),
                "canonical_source": _component_registry_source_record(
                    component_id,
                    component,
                ),
                "owner": component.get("owner", "@Thorncrag"),
                "information_handling": copy.deepcopy(
                    component.get(
                        "information_handling",
                        {
                            "information_classification": "public",
                            "disclosure_rule": "public_by_design",
                        },
                    )
                ),
                "lifecycle": component.get("lifecycle", "adopted"),
                "revision_mode": component.get(
                    "revision_mode", "maintained"
                ),
                "retention_bases": list(
                    component.get("retention_bases", ["operational_need"])
                ),
                "supporting_artifacts": list(
                    component.get("supporting_artifacts", [])
                ),
                "operational_status": component.get("operational_status"),
                "execution_controls": copy.deepcopy(
                    component.get("execution_controls")
                ),
                "console_route": (
                    f"{routes['components']}?component="
                    + urllib.parse.quote(component_id)
                ),
            }
        )

    enums = registry["implementation_enums"]
    class_records: list[dict[str, object]] = []
    type_records: list[dict[str, object]] = []
    for class_id in enums["component_classes"]:
        member_ids = [
            record["stable_id"]
            for record in components
            if record["classification"]["component_class"] == class_id
        ]
        type_ids = list(enums["component_types"].get(class_id, []))
        class_records.append(
            {
                "class_id": class_id,
                "label": class_id.replace("_", " "),
                "permitted_type_ids": type_ids,
                "component_ids": member_ids,
                "usage_count": len(member_ids),
                "console_route": (
                    f"{routes['classes']}?class="
                    + urllib.parse.quote(class_id)
                ),
            }
        )
        for type_id in type_ids:
            type_members = [
                record["stable_id"]
                for record in components
                if record["classification"].get("component_class")
                == class_id
                and record["classification"].get("component_type")
                == type_id
            ]
            classification_id = f"{class_id}:{type_id}"
            type_records.append(
                {
                    "classification_id": classification_id,
                    "class_id": class_id,
                    "type_id": type_id,
                    "label": type_id.replace("_", " "),
                    "component_ids": type_members,
                    "usage_count": len(type_members),
                    "console_route": (
                        f"{routes['types']}?type="
                        + urllib.parse.quote(classification_id)
                    ),
                }
            )

    lifecycle_assignments = [
        {
            "assignment_id": f"lifecycle:{record['stable_id']}",
            "component_id": record["stable_id"],
            "state": record["lifecycle"],
            "revision_mode": record["revision_mode"],
            "console_route": (
                f"{routes['lifecycles']}?assignment="
                + urllib.parse.quote(str(record["stable_id"]))
            ),
        }
        for record in components
    ]
    authority_assignments = [
        {
            "assignment_id": f"authority:{record['stable_id']}",
            "component_id": record["stable_id"],
            "authoritative": (
                record["lifecycle"] == "adopted"
                and record["classification"]["component_class"]
                in {"document", "configuration", "log"}
            ),
            "source": "component_registry",
            "effects": (
                ["govern_content"]
                if (
                    record["lifecycle"] == "adopted"
                    and record["classification"]["component_class"]
                    in {"document", "configuration", "log"}
                )
                else []
            ),
            "console_route": (
                f"{routes['authority']}?assignment="
                + urllib.parse.quote(str(record["stable_id"]))
            ),
        }
        for record in components
    ]

    relationships = [
        {
            "relationship_id": relationship_id,
            **copy.deepcopy(relationship),
            "console_route": (
                f"{routes['relationships']}?relationship="
                + urllib.parse.quote(relationship_id)
            ),
        }
        for relationship_id, relationship in relationship_entries.items()
    ]
    directories = [
        {
            "scope_id": scope_id,
            **copy.deepcopy(scope),
            "owner": scope.get("ownership", "@Thorncrag"),
            "console_route": (
                f"{routes['directories']}?directory="
                + urllib.parse.quote(scope_id)
            ),
        }
        for scope_id, scope in scope_entries.items()
    ]
    exemptions = [
        {
            "exemption_id": exemption_id,
            **copy.deepcopy(exemption),
            "console_route": (
                f"{routes['exemptions']}?exemption="
                + urllib.parse.quote(exemption_id)
            ),
        }
        for exemption_id, exemption in exemption_entries.items()
    ]

    route = routing_view["route"]
    routing_selections: list[dict[str, object]] = []
    for profile_id, profile in route["profiles"].items():
        routing_selections.append(
            {
                "routing_id": f"profile:{profile_id}",
                "routing_kind": "profile",
                "label": profile_id.replace("_", " "),
                "components": list(profile.get("modules", [])),
                "capabilities": list(profile.get("capabilities", [])),
                "console_route": (
                    f"{routes['routing']}?selection="
                    + urllib.parse.quote(f"profile:{profile_id}")
                ),
            }
        )
    for capability_id, component_ids in route["capabilities"].items():
        routing_selections.append(
            {
                "routing_id": f"capability:{capability_id}",
                "routing_kind": "capability",
                "label": capability_id.replace("_", " "),
                "components": list(component_ids),
                "capabilities": [capability_id],
                "console_route": (
                    f"{routes['routing']}?selection="
                    + urllib.parse.quote(f"capability:{capability_id}")
                ),
            }
        )
    routing_rules = [
        {
            "rule_id": rule_id,
            "namespace": namespace,
            "rule_version": 1,
            "status": "active",
            "predicate_type": rule_id,
            **copy.deepcopy(rule),
            "console_route": (
                f"{routes['routing']}?rule="
                + urllib.parse.quote(rule_id)
            ),
        }
        for namespace, group in registry["routing"]["rules"].items()
        for rule_id, rule in group.items()
    ]

    codeowners = component_registry_codeowners_projection(
        registry,
        root=root,
        compare_current=True,
    )
    if codeowners["problems"]:
        raise RuntimeError(
            "Tracked CODEOWNERS differs from the Registry authority."
        )
    for record in codeowners["records"]:
        record["console_route"] = (
            f"{routes['codeowners']}?assignment="
            + urllib.parse.quote(record["assignment_id"])
        )
    terminology = audit_component_registry_terminology(registry)
    for record in terminology["entries"]:
        record["console_route"] = (
            f"{routes['terminology']}?term="
            + urllib.parse.quote(record["term_id"])
        )

    component_relationships = {
        component_id: [
            record["relationship_id"]
            for record in relationships
            if record["from"] == component_id
            or record["to"] == component_id
        ]
        for component_id in component_entries
    }
    component_dependencies = {
        component_id: list(record.get("requires", []))
        for component_id, record in registry["routing"]["components"].items()
    }
    return {
        "schema_version": 4,
        "projection_id": "component-registry-console",
        "producer_id": "project-console-builder",
        "generated_at": generated_at,
        "availability": "current",
        "complete": True,
        "reason_code": None,
        "routes": routes,
        "defaults": {
            "mode": "components",
            "component": "COMPONENT-REGISTRY",
            "class": class_records[0]["class_id"],
            "type": type_records[0]["classification_id"],
            "lifecycle": lifecycle_assignments[0]["assignment_id"],
            "authority": authority_assignments[0]["assignment_id"],
            "relationship": relationships[0]["relationship_id"],
            "directory": directories[0]["scope_id"],
            "exemption": exemptions[0]["exemption_id"],
            "routing": routing_selections[0]["routing_id"],
            "terminology": terminology["entries"][0]["term_id"],
            "codeowners": codeowners["records"][0]["assignment_id"],
        },
        "registry": {
            "registry_id": registry["registry_id"],
            "registry_revision": registry["registry_revision"],
            "registry_status": routing_view["registry_status"],
            "validation_mode": validation_mode,
            "authoritative": False,
            "executable": False,
            "source_bytes_current": routing_view["source_bytes_current"],
            "predecessor_route_consulted": False,
            "registry_sha256": routing_view["registry_sha256"],
            "source_url": (
                "https://github.com/Thorncrag/ARRP/blob/main/"
                "framework/component-registry.json"
            ),
            "tracked_live_notice": (
                "This view reflects a proposed Registry revision that is not "
                "yet canonical or live authority."
                if validation_mode == "proposed_revision_validation"
                else
                "This view reflects tracked Registry configuration. Live "
                "authority is established only by the separately verified "
                "owner-local readback."
            ),
        },
        "records": {
            "components": components,
            "relationships": relationships,
            "directory_scopes": directories,
            "registration_exemptions": exemptions,
            "routing_rules": routing_rules,
            "terminology": terminology["entries"],
        },
        "linked": {
            "component_relationships": component_relationships,
            "component_dependencies": component_dependencies,
            "component_entry_fields": component_entry_fields,
        },
        "derived": {
            "classifications": {
                "classes": class_records,
                "types": type_records,
            },
            "lifecycles": {"assignments": lifecycle_assignments},
            "authorities": {"assignments": authority_assignments},
            "coverage": {
                "directories": directories,
                "exemptions": exemptions,
                "unresolved": [],
                "uncovered_count": 0,
                "multiply_treated_count": 0,
            },
            "routing": {
                "selections": routing_selections,
                "rules": routing_rules,
            },
            "codeowners": codeowners,
        },
    }


def load_component_registry_console_snapshot(
    *,
    generated_at: str,
    root: Path = ROOT,
) -> dict[str, object]:
    """Load tracked configuration without claiming live owner activation."""

    try:
        if root.resolve() == ROOT.resolve():
            routing_view = (
                load_component_registry_configuration_routing_view()
            )
        else:
            routing_view = (
                load_fixture_component_registry_configuration_routing_view(
                    ProjectPathAuthority.fixture(
                        root,
                        repository_root=root,
                        state_root=root,
                        output_root=root,
                    )
                )
            )
    except (ComponentRegistryError, PathAuthorityError) as error:
        raise RuntimeError(
            "Component Registry configuration validation is unavailable: "
            f"{error}"
        ) from error
    return component_registry_console_snapshot(
        routing_view,
        generated_at=generated_at,
        root=root,
    )


def component_registry_source_paths(
    snapshot: dict[str, object],
    *,
    root: Path = ROOT,
) -> list[Path]:
    """Return only sources consulted by the declared validation mode."""
    registry = snapshot.get("registry")
    if not isinstance(registry, dict):
        raise RuntimeError(
            "Component Registry source validation state is unavailable."
        )
    mode = registry.get("validation_mode")
    if mode not in {
        "proposed_revision_validation",
        "adopted_configuration_validation",
    }:
        raise RuntimeError(
            "Component Registry source validation mode is invalid."
        )
    paths = [
        root / "framework" / "component-registry.json",
        root / "framework" / "component-registry.schema.json",
    ]
    return paths


def main() -> None:
    global ALLOW_PRIVATE_CONSOLE_INPUTS
    args = parse_args()
    validate_console_modes(args)
    ALLOW_PRIVATE_CONSOLE_INPUTS = not args.public_only
    if args.public_only:
        private_authority = None
    else:
        try:
            private_authority = PrivateProjectAuthority.production_staging()
        except PathAuthorityError:
            private_authority = None
    validate_console_development_log_categories()
    projection_errors: list[dict[str, object]] = []
    if args.public_only:
        operational_incidents = unavailable_incident_projection("operational")
        security_incidents = unavailable_incident_projection("security")
        incident_relations = unavailable_incident_relations(
            "owner-local-data-not-loaded"
        )
    else:
        (
            operational_incidents,
            security_incidents,
            incident_relations,
        ) = owner_incident_snapshots(private_authority)
    public_operational_incidents = unavailable_incident_projection(
        "operational"
    )
    public_security_incidents = unavailable_incident_projection("security")
    public_incident_relations = unavailable_incident_relations()
    candidates = candidate_records()
    cited_sources = catalog_source_records(CITED_SOURCES, "Relied upon")
    pending_sources = catalog_source_records(
        PENDING_SOURCES, "Pending verification or placement"
    )
    presidential_directives = presidential_directive_records()
    horizon_records, github_synced_at = horizon_snapshot(args.refresh_github)
    private_security_assurance = (
        None
        if args.public_only
        else security_assurance_snapshot()
        if args.refresh_github
        else read_private_security_assurance()
    )
    public_security_assurance = public_security_assurance_projection()
    monitoring_issues = monitoring_issue_snapshot(args.refresh_github, horizon_records)
    court_watch_sources, case_watcher_metadata = case_watcher_snapshot()
    page_inventory = page_inventory_records()
    publication = publication_data(page_inventory)
    project_logs = project_log_views(projection_errors)
    review_recommendations = repository_review_recommendations(projection_errors)
    progress = progress_snapshot()
    integrity = integrity_snapshot()
    run_chain = run_chain_snapshot()
    run_chain = {
        **run_chain,
        "stages": [
            {
                **stage,
                "active_incident_ids": run_stage_incident_ids(
                    operational_incidents,
                    run_chain.get("run_id") or run_chain.get("chain_id"),
                    stage.get("id"),
                ),
            }
            for stage in run_chain.get("stages") or []
            if isinstance(stage, dict)
        ],
    }
    repository_gates = repository_gate_snapshot(args.refresh_github)
    repository_gates = {
        **repository_gates,
        "items": [
            {
                **item,
                "active_incident_ids": linked_incident_ids(
                    operational_incidents,
                    f"repository-gate:{item.get('gate_id')}",
                ),
            }
            for item in repository_gates.get("items") or []
            if isinstance(item, dict)
        ],
    }
    source_checker = source_checker_snapshot(
        public_source_checker_stage=args.public_source_checker_stage,
        public_only=args.public_only,
    )
    for feed_name, feed in (
        ("progress", progress),
        ("integrity", integrity),
        ("source_checker", source_checker),
    ):
        if not feed:
            projection_errors.append(
                {
                    "code": "required_feed_unavailable",
                    "severity": "error",
                    "feed": feed_name,
                    "message": (
                        f"The {feed_name} feed has no valid complete generation "
                        "for the current Console build."
                    ),
                }
            )
        else:
            if not str(feed.get("generation_id") or "").strip():
                projection_errors.append(
                    {
                        "code": "required_feed_contract_unavailable",
                        "severity": "error",
                        "feed": feed_name,
                        "message": (
                            f"The {feed_name} feed is preserved as legacy data "
                            "but lacks a generation truth contract."
                        ),
                    }
                )
            if str(feed.get("availability") or "") in {"stale", "unavailable"}:
                projection_errors.append(
                    {
                        "code": "required_feed_not_current",
                        "severity": "error",
                        "feed": feed_name,
                        "availability": feed.get("availability"),
                        "message": (
                            f"The {feed_name} feed is present but does not completely "
                            "cover its current authoritative source."
                        ),
                    }
                )
    agent_registry = agent_registry_records()
    public_agent_registry = public_safe_agent_registry(agent_registry)
    public_project_logs = public_safe_project_logs(project_logs)
    horizon_records = enrich_horizon_records(horizon_records, projection_errors)
    active_horizon_records = [
        record for record in horizon_records if record["issue_state"] == "Open"
    ]
    repository_revision = source_revision(ROOT)
    generated_at = repository_revision_timestamp(ROOT, repository_revision)
    progress["pipeline"] = build_pipeline_projection(
        candidates,
        active_horizon_records,
        progress,
        generated_at=generated_at,
    )
    delivery_items = (
        progress.get("delivery_items")
        if isinstance(progress.get("delivery_items"), list)
        else []
    )
    publication["release_readiness"] = publication_release_readiness(
        page_inventory,
        publication.get("builds") or [],
        progress,
        integrity,
    )
    publication["delivery_items"] = delivery_items
    component_registry_snapshot = load_component_registry_console_snapshot(
        generated_at=generated_at,
    )
    governance_change_supplements = (
        unavailable_governance_supplements(
            source_revision=repository_revision,
            checked_at=generated_at,
            reason_code="owner-local-data-not-loaded",
        )
        if args.public_only
        else owner_governance_supplements(
            source_revision=repository_revision,
            checked_at=generated_at,
            private_authority=private_authority,
        )
    )
    public_integrity = public_safe_integrity(integrity)
    transaction_recovery = (
        unavailable_transaction_recovery_projection(
            "owner-local-data-not-loaded"
        )
        if args.public_only
        else transaction_recovery_console_projection()
    )
    public_transaction_recovery = unavailable_transaction_recovery_projection()
    private_codex_usage = codex_usage_projection()
    action_snapshot = build_action_snapshot(
        progress=progress,
        integrity=public_integrity,
        review_recommendations=review_recommendations,
        operational_incidents=public_operational_incidents,
        security_incidents=public_security_incidents,
        generated_at=generated_at,
        require_private_incident_completeness=True,
    )
    private_action_snapshot = build_action_snapshot(
        progress=progress,
        integrity=integrity,
        review_recommendations=review_recommendations,
        operational_incidents=operational_incidents,
        security_incidents=security_incidents,
        generated_at=generated_at,
        require_private_incident_completeness=True,
    )
    private_action_snapshot = join_private_security_actions(
        private_action_snapshot,
        private_security_assurance,
    )
    queue_directory = build_queue_directory(
        progress=progress,
        preliminary_records=candidates,
        formal_candidates=active_horizon_records,
        pending_sources=pending_sources,
        review_recommendations=review_recommendations,
        action_snapshot=action_snapshot,
        operational_incidents=public_operational_incidents,
        security_incidents=public_security_incidents,
        transaction_recovery=public_transaction_recovery,
        generated_at=generated_at,
    )
    private_queue_directory = build_queue_directory(
        progress=progress,
        preliminary_records=candidates,
        formal_candidates=active_horizon_records,
        pending_sources=pending_sources,
        review_recommendations=review_recommendations,
        action_snapshot=private_action_snapshot,
        operational_incidents=operational_incidents,
        security_incidents=security_incidents,
        transaction_recovery=transaction_recovery,
        generated_at=generated_at,
    )
    local_automation_status = (
        {}
        if args.public_only
        else local_automation_status_snapshot(
            CONSOLE_DATA_DIR / "local-automation-status.js"
        )
    )
    automation_occurrences = automation_occurrence_projection(
        run_chain,
        local_automation_status,
        checked_at=generated_at,
    )
    public_automation_occurrences = public_safe_automation_occurrences(
        automation_occurrences
    )
    automation_role_status = automation_role_status_projection(
        agent_registry=agent_registry,
        run_chain=run_chain,
        progress=progress,
        integrity=integrity,
        source_checker=source_checker,
        checked_at=generated_at,
    )
    automation_role_status["roles"] = [
        {
            **item,
            "active_incident_ids": linked_incident_ids(
                operational_incidents,
                f"automation-role:{item.get('id')}",
            ),
        }
        for item in automation_role_status.get("roles") or []
        if isinstance(item, dict)
    ]
    public_automation_role_status = public_safe_automation_role_status(
        automation_role_status
    )
    public_repository_gates = public_safe_repository_gates(
        repository_gates
    )
    watcher_metadata = {
        "case_monitor": case_watcher_metadata,
        "presidential_directives": directive_watcher_metadata(),
    }
    overview = overview_data(
        candidates=candidates,
        active_horizon_records=active_horizon_records,
        monitoring_issues=monitoring_issues,
        pending_sources=pending_sources,
        review_recommendations=review_recommendations,
        progress=progress,
        integrity=integrity,
        run_chain=run_chain,
        repository_gates=public_repository_gates,
        operational_incidents=public_operational_incidents,
        security_incidents=public_security_incidents,
        publication=publication,
        project_logs=public_project_logs,
        agent_registry=public_agent_registry,
        watcher_metadata=watcher_metadata,
        source_checker=source_checker,
        automation_occurrences=public_automation_occurrences,
        action_snapshot=action_snapshot,
        queue_directory=queue_directory,
    )
    overview["run_chain"] = public_safe_run_chain(run_chain)
    input_paths = [
        CANDIDATES,
        HORIZON_LOG,
        CHANGE_AUDIT_LOG,
        GOVERNANCE_CHANGE_LOG,
        GOVERNANCE_CHANGE_REGISTRY,
        CONSOLE_DEVELOPMENT_LOG,
        SOURCE_MONITOR_LOG,
        SOURCE_CHECKER_CONFIG,
        ISSUE_REGISTRY,
        CITED_SOURCES,
        PENDING_SOURCES,
        DIRECTIVES,
        CASE_MONITOR_CONFIG,
        DIRECTIVE_MONITOR_CONFIG,
        PRINT_ASSEMBLY_MANIFEST,
        ROOT / "research" / "README.md",
    ]
    input_paths.extend(
        component_registry_source_paths(component_registry_snapshot)
    )
    hashes = source_hashes(ROOT, input_paths)
    for feed_name, feed in (
        ("progress", progress),
        ("integrity", integrity),
        ("run_chain", run_chain),
        ("source_checker", source_checker),
    ):
        if feed:
            hashes[f"feed:{feed_name}"] = "sha256:" + hashlib.sha256(
                json.dumps(
                    feed, sort_keys=True, separators=(",", ":"), default=str
                ).encode("utf-8")
            ).hexdigest()
    actual_count = (
        len(candidates)
        + len(horizon_records)
        + len(cited_sources)
        + len(pending_sources)
        + len(presidential_directives)
        + len(page_inventory)
        + sum(len(log.get("entries") or []) for log in public_project_logs)
        + len(review_recommendations)
        + len(delivery_items)
        + component_registry_projection_count(component_registry_snapshot)
    )
    pagination_sources: list[dict[str, object]] = [
        {
            "source": "horizon-issues",
            "complete": True,
            "actual_count": len(horizon_records),
            "mode": "authenticated-refresh" if args.refresh_github else "preserved-snapshot",
        },
        {
            "source": "monitoring-issues",
            "complete": True,
            "actual_count": len(monitoring_issues),
            "mode": "authenticated-refresh" if args.refresh_github else "preserved-snapshot",
        },
    ]
    for feed_name, feed in (
        ("progress", progress),
        ("source-checker", source_checker),
    ):
        feed_pagination = feed.get("pagination")
        pagination_sources.append(
            {
                "source": feed_name,
                "complete": (
                    isinstance(feed_pagination, dict)
                    and feed_pagination.get("complete") is True
                    and (
                        not isinstance(feed.get("completeness"), dict)
                        or feed["completeness"].get("complete") is True
                    )
                )
                if feed
                else False,
                "details": (
                    feed_pagination if isinstance(feed_pagination, dict) else None
                ),
            }
        )
    generation_contract = feed_contract(
        feed_name="project-console",
        timestamp_field="generated_at",
        timestamp=generated_at,
        revision=repository_revision,
        hashes=hashes,
        expected_count=actual_count,
        actual_count=actual_count,
        pagination={
            "complete": all(
                item.get("complete") is True for item in pagination_sources
            ),
            "sources": pagination_sources,
        },
        projection_errors=projection_errors,
    )
    payload = {
        "schema_version": 29,
        **generation_contract,
        "github_synced_at": github_synced_at,
        "candidate_questions": len(candidates),
        "horizon_issue_count": len(active_horizon_records),
        "records": candidates,
        "active_horizon_records": active_horizon_records,
        "cited_sources": cited_sources,
        "monitoring_issues": monitoring_issues,
        "court_watch_sources": court_watch_sources,
        "presidential_directives": presidential_directives,
        "watcher_metadata": watcher_metadata,
        "pending_sources": pending_sources,
        "page_inventory": page_inventory,
        "publication": publication,
        "topic_products": publication.get("topic_products") or [],
        "delivery_items": delivery_items,
        "project_logs": public_project_logs,
        "repository_review_recommendations": review_recommendations,
        "progress": progress,
        "integrity": public_safe_integrity(integrity),
        "run_chain": public_safe_run_chain(run_chain),
        "repository_gates": public_repository_gates,
        "operational_incidents": public_operational_incidents,
        "security_incidents": public_security_incidents,
        "incident_relations": public_incident_relations,
        "source_checker": source_checker,
        "agent_registry": public_agent_registry,
        "automation_role_status": public_automation_role_status,
        "automation_occurrences": public_automation_occurrences,
        "action_snapshot": action_snapshot,
        "queue_directory": queue_directory,
        "security_assurance": public_security_assurance,
        "overview": overview,
        # The full snapshot is retained only so an ordinary rebuild can preserve
        # authoritative GitHub state without requiring Keychain access.
        "horizon_records": horizon_records,
    }
    def select(record: dict[str, object], keys: tuple[str, ...]) -> dict[str, object]:
        return {key: record.get(key) for key in keys if key in record}

    compatibility_payload = {
        "schema_version": payload["schema_version"],
        **generation_contract,
        "github_synced_at": github_synced_at,
        "candidate_questions": len(candidates),
        "horizon_issue_count": len(active_horizon_records),
        "records": [
            select(record, ("id", "title", "summary", "kind"))
            for record in candidates
        ],
        "active_horizon_records": [
            {
                **select(record, ("id", "title", "issue_url", "workflow_status")),
                "horizon_history": select(
                    record.get("horizon_history", {})
                    if isinstance(record.get("horizon_history"), dict)
                    else {},
                    ("original_concern",),
                ),
            }
            for record in active_horizon_records
        ],
        "monitoring_issues": [
            select(record, ("id", "title", "summary", "issue_url"))
            for record in monitoring_issues
        ],
        "overview": overview,
        "automation_role_status": public_automation_role_status,
        "automation_occurrences": public_automation_occurrences,
        "action_snapshot": action_snapshot,
        "queue_directory": queue_directory,
        "repository_gates": public_repository_gates,
        "operational_incidents": public_operational_incidents,
        "security_incidents": public_security_incidents,
        "incident_relations": public_incident_relations,
        "security_assurance": public_security_assurance,
    }
    source_chunk_count = 16
    source_chunk_size = max(1, math.ceil(len(cited_sources) / source_chunk_count))
    source_chunks = {
        f"sources-catalog-{bucket + 1:03d}.js": {
            f"cited_sources_chunk_{bucket + 1:03d}":
                cited_sources[
                    bucket * source_chunk_size:(bucket + 1) * source_chunk_size
                ]
        }
        for bucket in range(source_chunk_count)
    }
    directive_chunk_count = 16
    directive_chunk_size = max(
        1, math.ceil(len(presidential_directives) / directive_chunk_count)
    )
    directive_chunks = {
        f"directives-catalog-{bucket + 1:03d}.js": {
            f"presidential_directives_chunk_{bucket + 1:03d}":
                presidential_directives[
                    bucket * directive_chunk_size:(bucket + 1) * directive_chunk_size
                ]
        }
        for bucket in range(directive_chunk_count)
    }
    public_run_chain = public_safe_run_chain(run_chain)
    parts = {
        "overview.js": {
            "overview": overview,
            "automation_occurrences": public_automation_occurrences,
            "action_snapshot": action_snapshot,
            "queue_directory": queue_directory,
            # The Overview must remain an atomic verification surface. Include
            # the same compact typed chain record used by its seven-stage
            # summary so opening Operations cannot change its rendered claim.
            "run_chain": public_run_chain,
        },
        "candidates.js": {
            "records": candidates,
            "active_horizon_records": active_horizon_records,
            # Retained so an ordinary rebuild can preserve authenticated GitHub
            # state without requiring Keychain access.
            "horizon_records": horizon_records,
        },
        "sources.js": {
            "cited_sources": [],
            "monitoring_issues": monitoring_issues,
            "court_watch_sources": court_watch_sources,
            "presidential_directives": [],
            "watcher_metadata": payload["watcher_metadata"],
            "pending_sources": pending_sources,
        },
        "source-checker.js": {"source_checker": source_checker},
        "progress.js": {"progress": progress},
        "integrity.js": {"integrity": public_integrity},
        "automation.js": {
            "agent_registry": public_agent_registry,
            "run_chain": public_run_chain,
            "automation_role_status": public_automation_role_status,
            "repository_gates": public_repository_gates,
            "operational_incidents": public_operational_incidents,
            "security_incidents": public_security_incidents,
            "incident_relations": public_incident_relations,
            "security_assurance": public_security_assurance,
            "repository_review_recommendations": review_recommendations,
        },
        "component-registry.js": {
            "component_registry": component_registry_snapshot,
        },
        "logs.js": {
            "project_logs": public_project_logs,
            "repository_review_recommendations": review_recommendations,
        },
        "publication.js": {
            "page_inventory": page_inventory,
            "publication": publication,
            "topic_products": publication.get("topic_products") or [],
            "delivery_items": delivery_items,
        },
        **source_chunks,
        **directive_chunks,
    }
    write_console_bundle(
        compatibility_payload,
        parts,
        generation_contract=generation_contract,
    )
    # Restore complete owner-only operations after the public generation swap.
    # This ignored projection is not part of the public manifest or catalog.
    if not args.public_only:
        write_private_operations(
            catalog_generation_id=str(generation_contract["generation_id"]),
            source_revision=str(generation_contract["source_revision"]),
            agent_registry=agent_registry,
            project_logs=project_logs,
            integrity=integrity,
            run_chain=run_chain,
            action_snapshot=private_action_snapshot,
            queue_directory=private_queue_directory,
            operational_incidents=operational_incidents,
            security_incidents=security_incidents,
            incident_relations=incident_relations,
            transaction_recovery=transaction_recovery,
            governance_change_supplements=governance_change_supplements,
        )
        if private_security_assurance is not None:
            # The public bundle replaces the complete data directory atomically.
            # Write the ignored authenticated projection only after that swap so
            # the local file:// Console keeps it without admitting it to the
            # public generation manifest or repository.
            write_private_security_assurance(private_security_assurance)
        write_private_codex_usage(private_codex_usage)

    if args.console_only:
        private_security_note = (
            " Minimized private security assurance refreshed."
            if private_security_assurance is not None
            else " Private security assurance unavailable."
        )
        print(
            f"Wrote {OUTPUT.relative_to(ROOT)} with {len(candidates)} preliminary "
            f"candidates, {len(active_horizon_records)} active proposed candidates, "
            f"{len(cited_sources)} cited sources, {len(monitoring_issues)} monitored "
            f"issues, {len(pending_sources)} pending sources, and "
            f"{len(presidential_directives)} presidential directives, plus "
            f"{len(page_inventory)} publication-controlled pages and "
            f"{sum(len(log['entries']) for log in project_logs)} project-log entries."
            f"{private_security_note}"
        )
        return

    participation_payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "proposal_index": proposal_index_records(),
        "horizon_index": [
            {
                "id": record["id"],
                "title": record["title"],
                "area": record["area"] if record["area"] != "Unassigned" else "Horizon",
                "canonical_page": record["canonical_page"],
                "issue_url": record["issue_url"],
            }
            for record in active_horizon_records
        ],
    }
    participation_serialized = json.dumps(
        participation_payload, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/")
    participation_text = (
        "/* Generated by scripts/build_project_console.py. */\n"
        f"window.ARRP_PARTICIPATION_DATA={participation_serialized};\n"
    )
    participation_changed = True
    if PARTICIPATION_OUTPUT.is_file() and not PARTICIPATION_OUTPUT.is_symlink():
        existing_text = PARTICIPATION_OUTPUT.read_text(encoding="utf-8")
        participation_changed = not participation_projection_is_unchanged(
            existing_text,
            participation_payload,
        )
    if participation_changed:
        try:
            require_outbound_bundle(
                [
                    OutboundArtifact(
                        path="participate/intake-data.js",
                        producer="console-public-bundle",
                        content=participation_text.encode("utf-8"),
                        artifact_group=(
                            f"console-generation:{generation_contract['generation_id']}"
                        ),
                    )
                ],
                operation="console_public_bundle",
                source_revision=str(generation_contract["generation_id"]),
                complete=True,
            )
        except DisclosureBlocked as error:
            raise RuntimeError(str(error)) from error
        atomic_write_text(
            PARTICIPATION_OUTPUT,
            participation_text,
        )
    print(
        f"Wrote {OUTPUT.relative_to(ROOT)} and {PARTICIPATION_OUTPUT.relative_to(ROOT)} "
        f"with {len(candidates)} preliminary candidates and "
        f"{len(active_horizon_records)} active proposed candidates, "
        f"{len(cited_sources)} cited sources, {len(monitoring_issues)} monitored "
        f"issues, {len(pending_sources)} pending sources, and "
        f"{len(presidential_directives)} presidential directives, plus "
        f"{len(page_inventory)} publication-controlled pages and "
        f"{sum(len(log['entries']) for log in project_logs)} project-log entries."
    )


if __name__ == "__main__":
    main()
