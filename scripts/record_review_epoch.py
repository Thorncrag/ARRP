#!/usr/bin/env python3
"""Validate and persist one completed comprehensive-review epoch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from path_authority import (
        APPROVED_STATE_ROOT,
        PathAuthorityError,
        ProjectPathAuthority,
    )
except ModuleNotFoundError:
    from scripts.path_authority import (
        APPROVED_STATE_ROOT,
        PathAuthorityError,
        ProjectPathAuthority,
    )


ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = APPROVED_STATE_ROOT
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from arrp_context import (  # noqa: E402
    extract_exact_heading,
    sha256_path,
    within_root,
)
try:  # noqa: E402
    from scripts.component_registry import (
        RegistryError,
        RoutingRuleFailure,
        load_fixture_component_registry_routing_view,
        load_validated_component_registry_routing_view,
        routed_configuration_documents_from_view,
        routed_documents_from_view,
    )
except ModuleNotFoundError:  # Direct execution uses scripts/ on sys.path.
    from component_registry import (
        RegistryError,
        RoutingRuleFailure,
        load_fixture_component_registry_routing_view,
        load_validated_component_registry_routing_view,
        routed_configuration_documents_from_view,
        routed_documents_from_view,
    )


REQUIRED = {
    "epoch_id",
    "triggering_run_id",
    "baseline_commit",
    "completion_commit",
    "governing_hashes",
    "project_snapshot",
    "registry_snapshot",
    "reviewed_domains",
    "resolved_findings",
    "unresolved_findings",
    "sampling_record",
    "automation_health",
    "completed_at",
    "next_due_at",
    "cadence_status",
    "stability_status",
    "triggering_reason",
}
CADENCE = {"biweekly", "monthly", "event-triggered"}
STABILITY = {"evolving", "stable", "drift-detected"}
SHA256_PREFIX = "sha256:"
COMPREHENSIVE_PROFILE = "comprehensive_review"
AUTOMATION_HEALTH = {"healthy", "degraded", "failed"}


def _prefixed_sha256(value: str) -> str:
    return SHA256_PREFIX + value


def _valid_sha256(value: object, *, prefixed: bool) -> bool:
    if not isinstance(value, str):
        return False
    digest = value
    if prefixed:
        if not digest.startswith(SHA256_PREFIX):
            return False
        digest = digest[len(SHA256_PREFIX) :]
    return len(digest) == 64 and all(character in "0123456789abcdef" for character in digest)


def _valid_commit(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_snapshot(value: object, name: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    source = value.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValueError(f"{name}.source must be a nonblank string")
    if not _valid_sha256(value.get("sha256"), prefixed=True):
        raise ValueError(f"{name}.sha256 must be a prefixed SHA-256 digest")
    record_count = value.get("record_count")
    if (
        isinstance(record_count, bool)
        or not isinstance(record_count, int)
        or record_count < 0
    ):
        raise ValueError(f"{name}.record_count must be a nonnegative integer")


def _validate_entries(value: object, name: str, *, nonempty: bool) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    if nonempty and not value:
        raise ValueError(f"{name} must not be empty")
    for entry in value:
        if isinstance(entry, str):
            valid = bool(entry.strip())
        elif isinstance(entry, dict):
            valid = bool(entry)
        else:
            valid = False
        if not valid:
            raise ValueError(
                f"{name} entries must be nonblank strings or nonempty objects"
            )


def _finding_ids(value: object, name: str) -> set[str]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    identifiers: list[str] = []
    for finding in value:
        if not isinstance(finding, dict):
            raise ValueError(f"{name} entries must be objects with stable IDs")
        identifier = finding.get("id")
        if (
            not isinstance(identifier, str)
            or not identifier.strip()
            or identifier != identifier.strip()
        ):
            raise ValueError(
                f"{name} entries must have a nonblank stable id without outer whitespace"
            )
        identifiers.append(identifier)
    duplicates = sorted(
        identifier
        for identifier in set(identifiers)
        if identifiers.count(identifier) > 1
    )
    if duplicates:
        raise ValueError(f"{name} repeats finding IDs: {duplicates}")
    return set(identifiers)


def _validate_finding_lists(record: dict) -> tuple[set[str], set[str]]:
    resolved = _finding_ids(record.get("resolved_findings"), "resolved_findings")
    unresolved = _finding_ids(
        record.get("unresolved_findings"),
        "unresolved_findings",
    )
    overlap = sorted(resolved & unresolved)
    if overlap:
        raise ValueError(
            "finding IDs may not appear in both resolved_findings and "
            f"unresolved_findings: {overlap}"
        )
    return resolved, unresolved


def _historical_unresolved_ids(epoch: dict) -> set[str]:
    """Read unresolved IDs without imposing the current schema on old rows."""
    entries = epoch.get("unresolved_findings", [])
    if not isinstance(entries, list):
        raise ValueError("prior epoch unresolved_findings must be an array")
    identifiers: set[str] = set()
    for finding in entries:
        if isinstance(finding, dict):
            identifier = finding.get("id")
        elif isinstance(finding, str):
            # Early append-only rows allowed unstructured strings. Treat the
            # complete historical text as its carried-forward identity rather
            # than rewriting or silently dropping it.
            identifier = finding
        else:
            identifier = None
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError(
                "prior epoch contains an unresolved finding without a stable ID"
            )
        identifiers.add(identifier.strip())
    return identifiers


def _validate_finding_continuity_untyped(
    latest_prior_epoch: dict | None,
    current_epoch: dict,
) -> dict:
    """Require every prior unresolved finding to remain open or be resolved."""
    resolved, unresolved = _validate_finding_lists(current_epoch)
    if latest_prior_epoch is None:
        return current_epoch
    if not isinstance(latest_prior_epoch, dict):
        raise ValueError("latest prior Review Epoch must be an object")
    prior_unresolved = _historical_unresolved_ids(latest_prior_epoch)
    omitted = sorted(prior_unresolved - resolved - unresolved)
    if omitted:
        raise ValueError(
            "Review Epoch omits prior unresolved finding IDs: "
            f"{omitted}; carry each forward or record it as resolved"
        )
    return current_epoch


def validate_finding_continuity(
    latest_prior_epoch: dict | None,
    current_epoch: dict,
) -> dict:
    """Require continuity and retain typed safe routing evidence."""

    try:
        return _validate_finding_continuity_untyped(
            latest_prior_epoch,
            current_epoch,
        )
    except ValueError as exc:
        raise RoutingRuleFailure(
            failure_code="CTXR_UNRESOLVED_MATERIAL_GOVERNING_GAP",
            phase="review_epoch",
            rule_ids=(
                "ctxr.review.unresolved_findings_carry_forward",
                "ctxr.review.next_epoch_uses_delta_and_carry_forward",
            ),
            message=f"Review Epoch finding continuity is invalid: {exc}",
        ) from exc


def _validate_automation_health(value: object) -> None:
    if not isinstance(value, dict):
        raise ValueError("automation_health must be an object")
    chain_id = value.get("chain_id")
    if not isinstance(chain_id, str) or not chain_id.strip():
        raise ValueError("automation_health.chain_id must be a nonblank string")
    if value.get("status") not in AUTOMATION_HEALTH:
        raise ValueError(
            "automation_health.status must be healthy, degraded, or failed"
        )
    for field in ("failures", "degradations"):
        if not isinstance(value.get(field), list):
            raise ValueError(f"automation_health.{field} must be an array")


def _valid_registry_revision(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and (
            (isinstance(value, int) and value >= 1)
            or (isinstance(value, str) and bool(value.strip()))
        )
    )


def _validated_routing_authority(
    routing_view: dict[str, Any],
    routing_selection: dict[str, Any],
    *,
    allow_candidate_validation: bool,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Validate the exact Component Registry route used for epoch closeout."""
    if routing_view.get("schema_version") != 2:
        raise ValueError(
            "Review Epoch closeout requires a validated Component Registry "
            "routing view"
        )
    mode = routing_view.get("validation_mode")
    if mode == "live_authority_validation":
        if (
            routing_view.get("authoritative") is not True
            or routing_view.get("executable") is not True
            or routing_view.get("live_authority_verified") is not True
            or routing_view.get("predecessor_route_consulted") is not False
        ):
            raise ValueError(
                "active Review Epoch closeout must use only the authoritative "
                "Component Registry"
            )
        expected_authoritative = True
        expected_selection_kind = "executable_packet"
        expected_executable = True
    elif mode == "proposed_revision_validation" and allow_candidate_validation:
        if (
            routing_view.get("authoritative") is not False
            or routing_view.get("executable") is not False
            or routing_view.get("live_authority_verified") is not False
            or routing_view.get("predecessor_route_consulted") is not False
        ):
            raise ValueError(
                "proposed Review Epoch closeout lacks nonexecuting Stage 2 "
                "configuration validation"
            )
        expected_authoritative = False
        expected_selection_kind = "configuration_validation_packet"
        expected_executable = False
    else:
        raise ValueError(
            "Review Epoch closeout requires active Component Registry authority; "
            "candidate validation must be explicitly enabled"
        )

    if (
        routing_view.get("registry_path")
        != "framework/component-registry.json"
        or not _valid_sha256(
            routing_view.get("registry_sha256"),
            prefixed=False,
        )
        or not isinstance(routing_view.get("registry_id"), str)
        or not routing_view["registry_id"].strip()
        or not _valid_registry_revision(
            routing_view.get("registry_revision")
        )
    ):
        raise ValueError(
            "Review Epoch routing has an invalid Component Registry identity"
        )
    if (
        routing_selection.get("selection_kind") != expected_selection_kind
        or routing_selection.get("executable") is not expected_executable
        or routing_selection.get("profile") != COMPREHENSIVE_PROFILE
        or routing_selection.get("capabilities") != []
        or routing_selection.get("authoritative") is not expected_authoritative
    ):
        raise ValueError(
            "Review Epoch closeout requires the exact comprehensive_review "
            "executable routing selection"
        )
    for field in (
        "registry_id",
        "registry_revision",
        "registry_sha256",
        "registry_path",
    ):
        if routing_selection.get(field) != routing_view.get(field):
            raise ValueError(
                f"Review Epoch routing selection {field} differs from its "
                "validated Component Registry view"
            )

    route = routing_view.get("route")
    documents = route.get("documents") if isinstance(route, dict) else None
    profile = (
        (route.get("profiles") or {}).get(COMPREHENSIVE_PROFILE)
        if isinstance(route, dict)
        else None
    )
    if (
        not isinstance(documents, dict)
        or not documents
        or not isinstance(profile, dict)
        or profile.get("include_all_governing") is not True
    ):
        raise ValueError(
            "Component Registry comprehensive_review routing is unavailable "
            "or incomplete"
        )
    modules = routing_selection.get("modules")
    if not isinstance(modules, list) or not modules:
        raise ValueError(
            "Review Epoch comprehensive routing selection has no modules"
        )
    by_id: dict[str, dict[str, Any]] = {}
    ordered_ids: list[str] = []
    for module in modules:
        if not isinstance(module, dict):
            raise ValueError(
                "Review Epoch comprehensive routing contains a non-object module"
            )
        document_id = module.get("id")
        path = module.get("path")
        if (
            not isinstance(document_id, str)
            or not document_id
            or document_id in by_id
            or not isinstance(path, str)
            or not path
        ):
            raise ValueError(
                "Review Epoch comprehensive routing has an invalid or duplicate "
                "module identity"
            )
        document = documents.get(document_id)
        if (
            not isinstance(document, dict)
            or document.get("path") != path
            or document.get("governing") is not module.get("governing")
            or document.get("hash_policy") != module.get("hash_policy")
        ):
            raise ValueError(
                f"Review Epoch routing module {document_id} differs from the "
                "validated Component Registry view"
            )
        if module.get("governing") is True and (
            module.get("hash_policy") != "pinned"
            or not _valid_sha256(module.get("sha256"), prefixed=False)
        ):
            raise ValueError(
                f"governing Review Epoch module {document_id} is not "
                "integration-pinned"
            )
        if module.get("hash_policy") == "runtime" and (
            document_id != "task_handoff"
            or module.get("governing") is not False
            or module.get("sha256") is not None
        ):
            raise ValueError(
                "task_handoff must be the sole unpinned runtime module in the "
                "Review Epoch route"
            )
        by_id[document_id] = module
        ordered_ids.append(document_id)

    seeds = [
        *(route.get("required_modules") or []),
        *(profile.get("modules") or []),
    ]
    capabilities = route.get("capabilities") or {}
    for capability in profile.get("capabilities") or []:
        members = capabilities.get(capability)
        if not isinstance(members, list):
            raise ValueError(
                f"Review Epoch profile references unknown capability {capability}"
            )
        seeds.extend(members)
    seeds.extend(
        document_id
        for document_id, document in documents.items()
        if isinstance(document, dict) and document.get("governing") is True
    )
    expected_ids: list[str] = []
    visiting: list[str] = []

    def include(document_id: str) -> None:
        document = documents.get(document_id)
        if not isinstance(document, dict):
            raise ValueError(
                f"Review Epoch route references unknown document {document_id}"
            )
        if document_id in visiting:
            raise ValueError("Review Epoch routing dependency cycle")
        if document_id in expected_ids:
            return
        visiting.append(document_id)
        dependencies = document.get("requires") or []
        if not isinstance(dependencies, list):
            raise ValueError(
                f"Review Epoch document {document_id} dependencies are invalid"
            )
        for dependency in dependencies:
            include(str(dependency))
        visiting.pop()
        expected_ids.append(document_id)

    for seed in seeds:
        include(str(seed))
    if ordered_ids != expected_ids:
        raise ValueError(
            "Review Epoch comprehensive routing does not select the exact "
            "governing boundary and dependency closure"
        )
    expected_sections = profile.get("sections") or []
    if routing_selection.get("sections") != expected_sections:
        raise ValueError(
            "Review Epoch comprehensive routing section selection differs "
            "from the validated Component Registry view"
        )
    return route, by_id


def _packet_modules(
    packet: dict,
    selected_modules: dict[str, dict[str, Any]],
    *,
    root: Path,
) -> dict[str, dict]:
    expected_ids = set(selected_modules)
    modules = packet.get("modules")
    if not isinstance(modules, list):
        raise ValueError("comprehensive context packet modules must be an array")
    by_id: dict[str, dict] = {}
    for module in modules:
        if not isinstance(module, dict):
            raise ValueError("comprehensive context packet contains a non-object module")
        document_id = module.get("document")
        if not isinstance(document_id, str) or not document_id:
            raise ValueError("comprehensive context packet module has no document identity")
        if document_id in by_id:
            raise ValueError(
                f"comprehensive context packet duplicates module {document_id}"
            )
        by_id[document_id] = module
    actual_ids = set(by_id)
    if actual_ids != expected_ids:
        raise ValueError(
            "comprehensive context packet module boundary differs; "
            f"missing={sorted(expected_ids-actual_ids)}, "
            f"extra={sorted(actual_ids-expected_ids)}"
        )
    for document_id, module in by_id.items():
        spec = selected_modules[document_id]
        expected_path = str(spec["path"])
        if module.get("path") != expected_path:
            raise ValueError(
                f"comprehensive context packet path differs for {document_id}"
            )
        digest = module.get("sha256")
        if not _valid_sha256(digest, prefixed=False):
            raise ValueError(
                f"comprehensive context packet has an invalid hash for {document_id}"
            )
        content = module.get("content")
        if not isinstance(content, str):
            raise ValueError(
                f"comprehensive context packet has no exact content for {document_id}"
            )
        content_bytes = content.encode("utf-8")
        if module.get("bytes") != len(content_bytes):
            raise ValueError(
                f"comprehensive context packet byte count differs for {document_id}"
            )
        if hashlib.sha256(content_bytes).hexdigest() != digest:
            raise ValueError(
                f"comprehensive context packet content hash differs for {document_id}"
            )
        policy = str(spec.get("hash_policy") or "pinned")
        if module.get("hash_policy") != policy:
            raise ValueError(
                f"comprehensive context packet hash policy differs for {document_id}"
            )
        if policy == "pinned":
            if digest != spec.get("sha256"):
                raise ValueError(
                    f"comprehensive context packet pinned hash differs for "
                    f"{document_id}"
                )
            current = sha256_path(within_root(root, expected_path), root)
            if digest != current:
                raise ValueError(
                    f"comprehensive context packet is stale for {document_id}"
                )
    return by_id


def _validate_packet_sections(
    packet: dict,
    route: dict[str, Any],
    expected_sections: list[dict[str, Any]],
    *,
    root: Path,
) -> None:
    expected_routes = {
        (str(route["document"]), str(route["heading"])): route
        for route in expected_sections
    }
    sections = packet.get("sections")
    if not isinstance(sections, list):
        raise ValueError("comprehensive context packet sections must be an array")
    actual_routes: dict[tuple[str, str], dict] = {}
    for section in sections:
        if not isinstance(section, dict):
            raise ValueError("comprehensive context packet contains a non-object section")
        identity = (str(section.get("document") or ""), str(section.get("heading") or ""))
        if identity in actual_routes:
            raise ValueError(
                "comprehensive context packet duplicates section "
                f"{identity[0]}: {identity[1]}"
            )
        actual_routes[identity] = section
    if set(actual_routes) != set(expected_routes):
        raise ValueError(
            "comprehensive context packet section boundary differs; "
            f"missing={sorted(set(expected_routes)-set(actual_routes))}, "
            f"extra={sorted(set(actual_routes)-set(expected_routes))}"
        )
    for (document_id, heading), section in actual_routes.items():
        spec = route["documents"][document_id]
        expected_path = str(spec["path"])
        if section.get("path") != expected_path:
            raise ValueError(
                f"comprehensive context packet section path differs for {document_id}"
            )
        source = within_root(root, expected_path)
        expected_content, _, _ = extract_exact_heading(
            source.read_text(encoding="utf-8"), heading
        )
        content = section.get("content")
        if content != expected_content:
            raise ValueError(
                f"comprehensive context packet section content differs for {document_id}: {heading}"
            )
        content_bytes = expected_content.encode("utf-8")
        digest = sha256_path(source, root)
        if section.get("sha256") != digest or section.get("bytes") != len(content_bytes):
            raise ValueError(
                f"comprehensive context packet section provenance differs for {document_id}: {heading}"
            )


def _validate_governing_boundary_untyped(
    hashes: dict,
    *,
    routing_view: dict[str, Any],
    routing_selection: dict[str, Any],
    context_packet: dict,
    root: Path,
    allow_candidate_validation: bool,
) -> None:
    route, selected_modules = _validated_routing_authority(
        routing_view,
        routing_selection,
        allow_candidate_validation=allow_candidate_validation,
    )
    if not isinstance(context_packet, dict):
        raise ValueError("comprehensive context packet must be an object")
    if context_packet.get("schema_version") != 2:
        raise ValueError("Review Epoch closeout requires a schema-version-2 context packet")
    if context_packet.get("profile") != COMPREHENSIVE_PROFILE:
        raise ValueError(
            "Review Epoch closeout requires the comprehensive_review context packet"
        )
    if context_packet.get("provenance_complete") is not True:
        raise ValueError("comprehensive context packet provenance is not complete")

    registry_identity = context_packet.get("manifest")
    expected_identity = {
        "path": routing_view["registry_path"],
        "sha256": routing_view["registry_sha256"],
    }
    if registry_identity != expected_identity:
        raise ValueError(
            "comprehensive context packet registry identity does not match "
            "the validated Component Registry view"
        )
    routing_manifest = context_packet.get("routing_manifest")
    if not isinstance(routing_manifest, dict):
        raise ValueError(
            "comprehensive context packet lacks its bound routing manifest"
        )
    expected_routing_identity = {
        "registry_id": routing_view["registry_id"],
        "registry_path": routing_view["registry_path"],
        "registry_revision": routing_view["registry_revision"],
        "validation_mode": routing_view["validation_mode"],
        "authoritative": routing_view["authoritative"],
        "executable": routing_view["executable"],
        "registry_digest": routing_view["registry_sha256"],
        "selected_profile": COMPREHENSIVE_PROFILE,
        "selected_capabilities": [],
    }
    for field, expected in expected_routing_identity.items():
        if routing_manifest.get(field) != expected:
            raise ValueError(
                f"comprehensive context packet routing {field} differs from "
                "the validated Component Registry selection"
            )
    expected_order = list(selected_modules)
    if routing_manifest.get("resolved_document_order") != expected_order:
        raise ValueError(
            "comprehensive context packet routed document order differs"
        )
    expected_closure = {
        document_id: list(
            route["documents"][document_id].get("requires") or []
        )
        for document_id in expected_order
    }
    if routing_manifest.get("dependency_closure") != expected_closure:
        raise ValueError(
            "comprehensive context packet dependency closure differs"
        )
    expected_revisions = {
        document_id: {
            "path": selected_modules[document_id]["path"],
            "hash_policy": selected_modules[document_id]["hash_policy"],
        }
        for document_id in expected_order
    }
    if routing_manifest.get("resolved_document_revisions") != expected_revisions:
        raise ValueError(
            "comprehensive context packet routed document revisions differ"
        )
    packet_modules = _packet_modules(
        context_packet,
        selected_modules,
        root=root,
    )
    expected_digests = {
        document_id: packet_modules[document_id]["sha256"]
        for document_id in expected_order
    }
    if routing_manifest.get("resolved_document_digests") != expected_digests:
        raise ValueError(
            "comprehensive context packet routed document digests differ"
        )
    expected_reasons = {
        document_id: selected_modules[document_id].get(
            "inclusion_reasons",
            [],
        )
        for document_id in expected_order
    }
    if routing_manifest.get("inclusion_reasons") != expected_reasons:
        raise ValueError(
            "comprehensive context packet inclusion reasons differ"
        )
    if routing_manifest.get("dynamic_expansions") != []:
        raise ValueError(
            "Review Epoch closeout requires an exact empty dynamic-expansion "
            "boundary"
        )
    expected_sections = routing_selection.get("sections")
    _validate_packet_sections(
        context_packet,
        route,
        expected_sections,
        root=root,
    )
    packet_section_identity = [
        {
            key: section[key]
            for key in (
                "document",
                "path",
                "sha256",
                "hash_policy",
                "heading",
                "start_line",
                "end_line",
                "bytes",
            )
        }
        for section in context_packet["sections"]
    ]
    if routing_manifest.get("exact_sections") != packet_section_identity:
        raise ValueError(
            "comprehensive context packet exact-section manifest differs"
        )

    expected_hashes = {
        str(spec["path"]): _prefixed_sha256(
            sha256_path(within_root(root, str(spec["path"])), root)
        )
        for spec in selected_modules.values()
        if spec.get("governing") is True
    }
    registry_path = str(routing_view["registry_path"])
    if registry_path in expected_hashes:
        raise ValueError(
            "the Component Registry must be represented by routing identity, "
            "not self-registered"
        )
    expected_hashes[registry_path] = _prefixed_sha256(
        str(routing_view["registry_sha256"])
    )
    if hashes != expected_hashes:
        missing = sorted(set(expected_hashes) - set(hashes))
        extra = sorted(set(hashes) - set(expected_hashes))
        mismatched = sorted(
            path
            for path in set(hashes) & set(expected_hashes)
            if hashes[path] != expected_hashes[path]
        )
        raise ValueError(
            "Review Epoch governing boundary is incomplete or stale; "
            f"missing={missing}, extra={extra}, mismatched={mismatched}"
        )


def _validate_governing_boundary(
    hashes: dict,
    *,
    routing_view: dict[str, Any],
    routing_selection: dict[str, Any],
    context_packet: dict,
    root: Path,
    allow_candidate_validation: bool,
) -> None:
    """Validate the exact boundary and retain typed safe routing evidence."""

    try:
        _validate_governing_boundary_untyped(
            hashes,
            routing_view=routing_view,
            routing_selection=routing_selection,
            context_packet=context_packet,
            root=root,
            allow_candidate_validation=allow_candidate_validation,
        )
    except RoutingRuleFailure:
        raise
    except ValueError as exc:
        detail = str(exc)
        if "runtime" in detail or "task_handoff" in detail:
            failure_code = "CTXR_RUNTIME_DIGEST_UNREADABLE"
            rule_ids = (
                "ctxr.cur.runtime_nongoverning_excluded_from_review_boundary",
            )
        else:
            failure_code = "CTXR_PINNED_DIGEST_ABSENT_OR_STALE"
            rule_ids = (
                "ctxr.review.boundary_exact",
                "ctxr.review.any_valid_boundary_difference_due",
                "ctxr.review.invalid_drift_is_integrity_failure",
                "ctxr.review.recorder_requires_exact_current_boundary",
            )
        raise RoutingRuleFailure(
            failure_code=failure_code,
            phase="review_epoch",
            rule_ids=rule_ids,
            message=f"Review Epoch governing boundary is invalid: {detail}",
        ) from exc


def _validate_untyped(
    value: dict,
    *,
    routing_view: dict[str, Any],
    routing_selection: dict[str, Any],
    context_packet: dict,
    root: Path = ROOT,
    allow_candidate_validation: bool = False,
) -> dict:
    if set(value) != REQUIRED:
        raise ValueError(
            f"review epoch fields differ; missing={sorted(REQUIRED-set(value))}, "
            f"extra={sorted(set(value)-REQUIRED)}"
        )
    for key in ("epoch_id", "triggering_run_id", "triggering_reason"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(f"{key} must be a nonblank string")
    for key in ("baseline_commit", "completion_commit"):
        if not _valid_commit(value[key]):
            raise ValueError(f"{key} must be a 40-character Git commit hash")
    packet_revision = context_packet.get("repository_revision")
    if value["completion_commit"] != packet_revision:
        raise ValueError(
            "completion_commit must equal the comprehensive context packet "
            "repository_revision"
        )
    if value["cadence_status"] not in CADENCE or value["stability_status"] not in STABILITY:
        raise ValueError("review epoch cadence or stability status is invalid")
    hashes = value["governing_hashes"]
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("governing_hashes must be a nonempty object")
    for path, digest in hashes.items():
        if not isinstance(path, str) or not path or not _valid_sha256(digest, prefixed=True):
            raise ValueError("governing hash entries require path and sha256 digest")
    _validate_governing_boundary(
        hashes,
        routing_view=routing_view,
        routing_selection=routing_selection,
        context_packet=context_packet,
        root=root,
        allow_candidate_validation=allow_candidate_validation,
    )
    _validate_snapshot(value["project_snapshot"], "project_snapshot")
    _validate_snapshot(value["registry_snapshot"], "registry_snapshot")
    _validate_entries(value["reviewed_domains"], "reviewed_domains", nonempty=True)
    _validate_finding_lists(value)
    _validate_entries(value["sampling_record"], "sampling_record", nonempty=True)
    _validate_automation_health(value["automation_health"])
    completed = datetime.fromisoformat(value["completed_at"].replace("Z", "+00:00"))
    due = datetime.fromisoformat(value["next_due_at"].replace("Z", "+00:00"))
    if due <= completed:
        raise ValueError("next_due_at must follow completed_at")
    return {"schema_version": 1, **value}


def validate(
    value: dict,
    *,
    routing_view: dict[str, Any],
    routing_selection: dict[str, Any],
    context_packet: dict,
    root: Path = ROOT,
    allow_candidate_validation: bool = False,
) -> dict:
    """Validate closeout and retain typed safe routing evidence."""

    try:
        return _validate_untyped(
            value,
            routing_view=routing_view,
            routing_selection=routing_selection,
            context_packet=context_packet,
            root=root,
            allow_candidate_validation=allow_candidate_validation,
        )
    except RoutingRuleFailure:
        raise
    except ValueError as exc:
        detail = str(exc)
        if detail.startswith("review epoch fields differ"):
            failure_code = "CTXR_UNKNOWN_OR_MISSING_SELECTION"
            rule_ids = (
                "ctxr.review.periodic_epoch_required",
                "ctxr.review.completion_fields_exact",
            )
        elif "governing" in detail or "boundary" in detail:
            failure_code = "CTXR_PINNED_DIGEST_ABSENT_OR_STALE"
            rule_ids = (
                "ctxr.review.periodic_epoch_required",
                "ctxr.review.invalid_drift_is_integrity_failure",
                "ctxr.review.recorder_requires_exact_current_boundary",
            )
        else:
            failure_code = "CTXR_UNKNOWN_OR_MISSING_SELECTION"
            rule_ids = (
                "ctxr.review.periodic_epoch_required",
                "ctxr.review.completion_fields_exact",
            )
        raise RoutingRuleFailure(
            failure_code=failure_code,
            phase="review_epoch",
            rule_ids=rule_ids,
            message=f"Review Epoch completion is invalid: {detail}",
        ) from exc


def append(ledger: Path, current: Path, record: dict) -> bool:
    if ledger.is_file():
        rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
        if any(row.get("epoch_id") == record["epoch_id"] for row in rows):
            return False
    digest = hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    record = {**record, "record_sha256": "sha256:" + digest}
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    current.parent.mkdir(parents=True, exist_ok=True)
    current.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return True


def _latest_epoch(ledger: Path) -> dict | None:
    if not ledger.is_file():
        return None
    rows = [
        json.loads(line)
        for line in ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        return None
    latest = rows[-1]
    if not isinstance(latest, dict):
        raise ValueError("latest prior Review Epoch must be an object")
    return latest


def main(
    *,
    path_authority: ProjectPathAuthority | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--context-packet",
        type=Path,
        required=True,
        help="Complete comprehensive_review packet used for this Review Epoch.",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=STATE_ROOT / "records/automation/review-epochs.jsonl",
    )
    parser.add_argument(
        "--current", type=Path, default=Path(".tmp/run-coordinator/review-epoch.json")
    )
    args = parser.parse_args()
    if path_authority is None:
        authority = ProjectPathAuthority.production()
        input_path = authority.requested_repository_file(args.input)
        context_packet_path = authority.requested_repository_file(
            args.context_packet
        )
        ledger = authority.state_path(
            "records/automation/review-epochs.jsonl",
            owner_only=True,
        )
        current = authority.repository_output(
            ".tmp/run-coordinator/review-epoch.json"
        )
    else:
        if path_authority.mode != "fixture":
            raise PathAuthorityError(
                "injected path authority is reserved for isolated tests"
            )
        authority = path_authority
        input_path = authority.requested_repository_file(args.input)
        context_packet_path = authority.requested_repository_file(
            args.context_packet
        )
        ledger = authority.requested_state_file(
            args.ledger, owner_only=False
        )
        current = authority.requested_repository_file(
            args.current, required=False
        )
    routing_view = (
        load_fixture_component_registry_routing_view(authority)
        if authority.mode == "fixture"
        else load_validated_component_registry_routing_view(authority)
    )
    routing_selection = (
        routed_configuration_documents_from_view
        if routing_view.get("validation_mode") == "proposed_revision_validation"
        else routed_documents_from_view
    )(
        routing_view,
        profile_id=COMPREHENSIVE_PROFILE,
    )
    record = validate(
        json.loads(input_path.read_text()),
        routing_view=routing_view,
        routing_selection=routing_selection,
        context_packet=json.loads(context_packet_path.read_text()),
        root=authority.repository_root,
        allow_candidate_validation=authority.mode == "fixture",
    )
    validate_finding_continuity(_latest_epoch(ledger), record)
    changed = append(ledger, current, record)
    print(json.dumps({"recorded": changed, "epoch_id": record["epoch_id"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RegistryError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"review-epoch: {exc}")
