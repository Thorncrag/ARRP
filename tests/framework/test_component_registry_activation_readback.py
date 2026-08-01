import copy
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import component_registry as registry
from scripts import finalize_component_registry_activation as finalizer
from scripts.path_authority import ProjectPathAuthority


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "framework" / "component-registry.json"
SCHEMA_PATH = (
    ROOT
    / "framework"
    / "standards"
    / "automation"
    / "component-registry.schema.json"
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_candidate_registry() -> dict[str, object]:
    current = load_json(REGISTRY_PATH)
    if current["status"] == "candidate":
        return current
    candidate_revision = current["source_baseline"]["repository_revision"]
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            f"{candidate_revision}:framework/component-registry.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    candidate = json.loads(result.stdout)
    if (
        candidate.get("status") != "candidate"
        or registry._canonical_registry_digest(candidate)
        != current["approval"]["value"]["candidate_registry_sha256"]
    ):
        raise AssertionError("active registry candidate parent is not exact")
    return candidate


def current_source_path(relative: str) -> Path:
    source = ROOT / relative
    if source.exists():
        return source
    for specification in registry.ROUTING_PREDECESSOR_PATHS.values():
        if relative == specification["historical_path"]:
            return ROOT / specification["archived_path"]
    return source


class LegacyStage1ActivationReadbackExamples:
    def git(self, repository: Path, *arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def build_candidate_fixture(
        self,
        fixture_root: Path,
    ) -> tuple[
        ProjectPathAuthority,
        Path,
        dict[str, object],
        dict[str, object],
    ]:
        repository = fixture_root / "repository"
        state = fixture_root / "state"
        output = fixture_root / "output"
        for directory in (repository, state, output):
            directory.mkdir(mode=0o700)

        candidate = load_candidate_registry()
        route = registry._routing_snapshot(candidate)
        source_paths = {
            str(spec["path"]) for spec in route["documents"].values()
        }
        source_paths.update(
            str(entry["canonical_path"])
            for entry in candidate["operational_documents"][
                "entries"
            ].values()
            if entry["digest_policy"] == "pinned"
        )
        source_paths.add(
            "framework/standards/automation/"
            "component-registry.schema.json"
        )
        for relative in sorted(source_paths):
            source = current_source_path(relative)
            destination = repository / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        for identity, spec in route["documents"].items():
            if spec["hash_policy"] != "pinned":
                continue
            digest = registry._sha256(repository / spec["path"])
            spec["sha256"] = digest
            candidate["context_routing"]["documents"][identity][
                "sha256"
            ] = digest
        for entry in candidate["operational_documents"][
            "entries"
        ].values():
            if entry["digest_policy"] == "pinned":
                entry["sha256"] = registry._sha256(
                    repository / entry["canonical_path"]
                )

        route_path = (
            repository
            / "framework"
            / "project"
            / "automation"
            / "context-routes.json"
        )
        route_path.parent.mkdir(parents=True, exist_ok=True)
        route_path.write_text(
            json.dumps(route, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        route_digest = registry._sha256(route_path)
        candidate["context_routing"]["source_import"][
            "sha256"
        ] = route_digest
        candidate["context_routing"]["expected_counts"] = (
            registry.route_counts(route)
        )
        candidate["source_baseline"]["route_source"][
            "sha256"
        ] = route_digest
        candidate["source_baseline"]["working_tree_binding"][
            "sha256"
        ] = registry._route_source_binding(
            candidate["source_baseline"]["repository_revision"],
            route,
        )
        candidate_path = (
            repository / registry.CANONICAL_REGISTRY_PATH
        )
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        authority = ProjectPathAuthority.fixture(
            fixture_root,
            repository_root=repository,
            state_root=state,
            output_root=output,
        )
        return authority, candidate_path, candidate, route

    def build_active_fixture(
        self,
        fixture_root: Path,
    ) -> tuple[
        ProjectPathAuthority,
        dict[str, object],
        dict[str, object],
    ]:
        authority, registry_path, candidate, route = (
            self.build_candidate_fixture(fixture_root)
        )
        repository = authority.repository_root
        self.git(repository, "init", "-b", "main")
        self.git(repository, "config", "user.name", "ARRP Fixture")
        self.git(
            repository,
            "config",
            "user.email",
            "fixture@example.invalid",
        )
        self.git(repository, "add", ".")
        self.git(repository, "commit", "-m", "fixture baseline")
        base_revision = self.git(repository, "rev-parse", "HEAD")

        candidate["source_baseline"][
            "repository_revision"
        ] = base_revision
        candidate["source_baseline"]["working_tree_binding"][
            "sha256"
        ] = registry._route_source_binding(base_revision, route)
        candidate_digest = registry._canonical_registry_digest(
            candidate
        )
        active = copy.deepcopy(candidate)
        predecessor_digests = {
            "context_routing": active["operational_documents"][
                "entries"
            ]["context_routing"]["sha256"],
            "context_routes_source": active["context_routing"][
                "source_import"
            ]["sha256"],
        }
        active["context_routing"]["documents"].pop("context_routing")
        active["context_routing"]["documents"]["codex_bootstrap"][
            "requires"
        ] = [
            identity
            for identity in active["context_routing"]["documents"][
                "codex_bootstrap"
            ]["requires"]
            if identity != "context_routing"
        ]
        active["operational_documents"]["entries"]["codex_bootstrap"][
            "dependencies"
        ] = list(
            active["context_routing"]["documents"]["codex_bootstrap"][
                "requires"
            ]
        )
        context_document = active["operational_documents"]["entries"][
            "context_routing"
        ]
        context_document.update(
            {
                "canonical_path": (
                    "framework/archive/authorities/CONTEXT_ROUTING.md"
                ),
                "current_status": {
                    "state": "known",
                    "value": "retired",
                },
                "authority_role": "archived_predecessor",
                "representations": [],
                "dependencies": [],
                "consumers": [],
                "retention_posture": "archived",
                "digest_policy": "provenance_only",
            }
        )
        route_source_document = copy.deepcopy(context_document)
        route_source_document.update(
            {
                "document_id": "context_routes_source",
                "official_reference_name": {
                    "state": "known",
                    "value": "Historical Context Route Data",
                },
                "document_class": {
                    "state": "known",
                    "value": "archived_route_data_authority",
                },
                "canonical_path": (
                    "framework/archive/authorities/context-routes.json"
                ),
                "console_route": (
                    "operations:component-registry:documents"
                    "?document=context_routes_source"
                ),
                "sha256": predecessor_digests[
                    "context_routes_source"
                ],
            }
        )
        active["operational_documents"]["entries"][
            "context_routes_source"
        ] = route_source_document
        active["representations"]["entries"][
            "human_readable_context_routing"
        ].update(
            {
                "source_revision_binding": (
                    "component_registry_revision:"
                    f"{active['registry_revision']}"
                ),
                "canonical_path": (
                    "framework/project/interfaces/project-console/data/"
                    "component-registry.js"
                ),
                "state": "active",
            }
        )
        active["context_routing"].pop("source_import")
        active["context_routing"].pop("parity_policy")
        active["context_routing"]["predecessor_provenance"] = {
            "schema_version": 1,
            "complete": True,
            "authority_effect": (
                "historical_provenance_only_no_runtime_read"
            ),
            "records": {
                "context_routing": {
                    "stable_id": "context_routing",
                    "artifact_kind": "markdown_authority",
                    "historical_path": "framework/CONTEXT_ROUTING.md",
                    "archived_path": (
                        "framework/archive/authorities/"
                        "CONTEXT_ROUTING.md"
                    ),
                    "sha256": predecessor_digests[
                        "context_routing"
                    ],
                    "source_schema_version": None,
                    "state": "archived_retired_provenance_only",
                    "retirement_proof": {
                        "proof_type": (
                            "authenticated_activation_cutover"
                        ),
                        "governance_change_id": "GOV-2026-001",
                        "implementation_contract_id": (
                            "COMPONENT-REGISTRY-2026-001-ACTIVATION"
                        ),
                        "owner_review_reference": (
                            "github-review:Thorncrag/ARRP#123"
                        ),
                    },
                },
                "context_routes_source": {
                    "stable_id": "context_routes_source",
                    "artifact_kind": "route_data_authority",
                    "historical_path": (
                        "framework/project/automation/"
                        "context-routes.json"
                    ),
                    "archived_path": (
                        "framework/archive/authorities/"
                        "context-routes.json"
                    ),
                    "sha256": predecessor_digests[
                        "context_routes_source"
                    ],
                    "source_schema_version": 2,
                    "state": "archived_retired_provenance_only",
                    "retirement_proof": {
                        "proof_type": (
                            "authenticated_activation_cutover"
                        ),
                        "governance_change_id": "GOV-2026-001",
                        "implementation_contract_id": (
                            "COMPONENT-REGISTRY-2026-001-ACTIVATION"
                        ),
                        "owner_review_reference": (
                            "github-review:Thorncrag/ARRP#123"
                        ),
                    },
                },
            },
            "migration_alias_ids": list(
                registry.ROUTING_PREDECESSOR_ALIAS_IDS
            ),
            "verification_ids": list(
                registry.ROUTING_PREDECESSOR_VERIFICATION_IDS
            ),
        }
        active["context_routing"]["readable_representation"] = {
            "representation_id": "human_readable_context_routing",
            "binding_kind": "component_registry_revision",
            "source_registry_revision": active["registry_revision"],
            "generated_from": "embedded_context_routing",
            "authority_effect": "none",
            "executable": False,
        }
        active["context_routing"]["expected_counts"] = (
            registry.route_counts(
                registry._routing_snapshot(active)
            )
        )
        active["source_baseline"].pop("route_source")
        active["source_baseline"]["repository_state"] = "clean_committed"
        active["source_baseline"]["working_tree_binding"].update(
            {
                "mode": "active_revision_plus_embedded_route",
                "scope": (
                    "complete_embedded_component_registry_route"
                ),
                "sha256": registry._route_source_binding(
                    base_revision,
                    registry._routing_snapshot(active),
                ),
            }
        )
        active["status"] = "active"
        active["context_routing"]["activation_state"] = "active"
        active["context_routing"]["authoritative"] = True
        active["approval"] = {
            "state": "known",
            "value": {
                "approval_type": "stage1_component_registry_activation",
                "approved_by": "@Thorncrag",
                "approval_method": "explicit_recorded_owner_activation",
                "governance_change_id": "GOV-2026-001",
                "implementation_contract_id": (
                    "COMPONENT-REGISTRY-2026-001-ACTIVATION"
                ),
                "base_revision": base_revision,
                "candidate_registry_sha256": candidate_digest,
                "affected_stable_ids": ["COMPONENT-REGISTRY"],
                "purpose_scope": (
                    "Activate the reviewed Stage 1 registry fixture."
                ),
                "bounded_diff_sha256": "b" * 64,
                "approved_at": "2026-07-30T00:00:00-04:00",
                "owner_review_reference": (
                    "github-review:Thorncrag/ARRP#123"
                ),
            },
        }
        active = registry.build_simulated_active_registry(
            candidate,
            repository_revision=base_revision,
            approval_value=active["approval"]["value"],
        )
        registry_path.write_text(
            json.dumps(active, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.git(repository, "add", registry.CANONICAL_REGISTRY_PATH)
        self.git(repository, "commit", "-m", "activate fixture registry")
        reviewed_head = self.git(repository, "rev-parse", "HEAD")
        registry_digest = registry._canonical_registry_digest(active)
        approval_digest = hashlib.sha256(
            registry.canonical_json(
                active["approval"]["value"]
            ).encode("utf-8")
        ).hexdigest()
        readback = {
            "schema_version": 1,
            "verification_type": (
                "component_registry_activation_readback"
            ),
            "verification_state": "authenticated_owner_readback",
            "complete": True,
            "issuer": "component_registry_activation_finalizer",
            "repository": "Thorncrag/ARRP",
            "default_branch": "main",
            "registry_id": "COMPONENT-REGISTRY",
            "registry_path": registry.CANONICAL_REGISTRY_PATH,
            "registry_revision": active["registry_revision"],
            "registry_sha256": registry_digest,
            "governance_change_id": (
                active["approval"]["value"]["governance_change_id"]
            ),
            "implementation_contract_id": (
                active["approval"]["value"][
                    "implementation_contract_id"
                ]
            ),
            "approval_sha256": approval_digest,
            "candidate_registry_sha256": candidate_digest,
            "bounded_diff_sha256": (
                active["approval"]["value"]["bounded_diff_sha256"]
            ),
            "owner_review_reference": (
                active["approval"]["value"]["owner_review_reference"]
            ),
            "pull_request_number": 123,
            "approval_evidence_type": "github_owner_manual_merge",
            "approved_head_revision": reviewed_head,
            "approved_by": "@Thorncrag",
            "merged_by": "Thorncrag",
            "merged_at": "2026-07-30T00:01:00-04:00",
            "merge_commit_revision": reviewed_head,
            "required_checks_state": "success",
            "required_checks_revision": reviewed_head,
            "remote_main_revision": reviewed_head,
            "remote_registry_sha256": registry_digest,
            "verified_at": "2026-07-30T00:02:00-04:00",
        }
        return authority, active, readback

    def write_fixed_readback(
        self,
        authority: ProjectPathAuthority,
        readback: dict[str, object],
    ) -> Path:
        logical = registry._activation_readback_logical_path(
            str(readback["registry_sha256"])
        )
        path = authority.state_root / logical
        current = authority.state_root
        os.chmod(current, 0o700)
        for part in Path(logical).parts[:-1]:
            current = current / part
            current.mkdir(mode=0o700, exist_ok=True)
            os.chmod(current, 0o700)
        path.write_text(
            json.dumps(readback, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.chmod(path, 0o600)
        return path

    def test_production_api_exposes_no_receipt_or_path_bypass(self):
        parameters = inspect.signature(
            registry.load_validated_component_registry_routing_view
        ).parameters
        self.assertEqual(list(parameters), ["path_authority"])
        fixture_parameters = inspect.signature(
            registry.load_fixture_component_registry_routing_view
        ).parameters
        self.assertEqual(
            list(fixture_parameters),
            ["path_authority", "activation_readback"],
        )
        self.assertEqual(
            list(
                inspect.signature(
                    registry.load_component_registry_configuration_routing_view
                ).parameters
            ),
            [],
        )
        self.assertEqual(
            list(
                inspect.signature(
                    registry.load_fixture_component_registry_configuration_routing_view
                ).parameters
            ),
            ["path_authority"],
        )

    def test_candidate_fixture_never_reads_activation_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, _path, _candidate, _route = (
                self.build_candidate_fixture(Path(directory))
            )
            view = (
                registry.load_fixture_component_registry_routing_view(
                    authority
                )
            )
            self.assertEqual(
                view["validation_mode"],
                "candidate_validation_only",
            )
            self.assertFalse(view["authoritative"])
            self.assertFalse(view["executable"])
            self.assertFalse(view["live_activation_verified"])
            self.assertFalse(view["activation_receipt_consulted"])
            self.assertTrue(view["predecessor_route_consulted"])
            self.assertFalse(
                (
                    authority.state_root
                    / registry.ACTIVATION_READBACK_DIRECTORY
                ).exists()
            )

    def test_repository_validation_is_candidate_only(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, _path, _candidate, _route = (
                self.build_candidate_fixture(Path(directory))
            )
            view = (
                registry.load_fixture_component_registry_configuration_routing_view(
                    authority
                )
            )
            self.assertFalse(view["authoritative"])
            self.assertFalse(view["executable"])
            self.assertFalse(view["live_activation_verified"])
            self.assertFalse(view["activation_receipt_consulted"])
            self.assertTrue(view["predecessor_route_consulted"])
        with tempfile.TemporaryDirectory() as directory:
            authority, _active, _readback = self.build_active_fixture(
                Path(directory)
            )
            view = (
                registry.load_fixture_component_registry_configuration_routing_view(
                    authority
                )
            )
            self.assertEqual(
                view["validation_mode"],
                "active_configuration_validation_only",
            )
            self.assertFalse(view["authoritative"])
            self.assertFalse(view["executable"])
            self.assertFalse(view["live_activation_verified"])
            self.assertFalse(view["activation_receipt_consulted"])
            self.assertFalse(view["predecessor_route_consulted"])
            preview = registry.routed_profile_preview_from_view(
                view,
                profile_id="github_sync",
            )
            self.assertFalse(preview["executable"])
            self.assertFalse(preview["authoritative"])
            with self.assertRaisesRegex(
                registry.RegistryError,
                "cannot satisfy an executable consumer",
            ):
                registry.routed_documents_from_view(
                    view,
                    profile_id="github_sync",
                )

    def test_active_fixture_requires_fixed_adapter_and_exact_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, active, readback = self.build_active_fixture(
                Path(directory)
            )
            with self.assertRaisesRegex(
                registry.RegistryError,
                "only through fixed path authority",
            ):
                registry.validated_component_registry_routing_view(
                    active,
                    candidate_source_route=registry._routing_snapshot(
                        active
                    ),
                )
            view = (
                registry.load_fixture_component_registry_routing_view(
                    authority,
                    activation_readback=readback,
                )
            )
            self.assertEqual(
                view["validation_mode"],
                "active_component_registry",
            )
            self.assertTrue(view["authoritative"])
            self.assertTrue(view["executable"])
            self.assertTrue(view["live_activation_verified"])
            self.assertTrue(view["activation_receipt_consulted"])
            self.assertFalse(view["predecessor_route_consulted"])

    def test_active_loader_does_not_read_predecessors(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, _active, _readback = self.build_active_fixture(
                Path(directory)
            )
            predecessor_paths = {
                value
                for specification in (
                    registry.ROUTING_PREDECESSOR_PATHS.values()
                )
                for value in (
                    specification["historical_path"],
                    specification["archived_path"],
                )
            }
            original_contained_file = registry._contained_file

            def guarded_contained_file(
                root: Path,
                relative: object,
                label: str,
            ) -> Path:
                if str(relative) in predecessor_paths:
                    raise AssertionError(
                        "active validation attempted predecessor file I/O"
                    )
                return original_contained_file(root, relative, label)

            with mock.patch.object(
                registry,
                "_contained_file",
                side_effect=guarded_contained_file,
            ):
                view = (
                    registry.load_fixture_component_registry_configuration_routing_view(
                        authority
                    )
                )
            self.assertEqual(
                view["validation_mode"],
                "active_configuration_validation_only",
            )
            self.assertFalse(view["predecessor_route_consulted"])
            self.assertFalse(
                set(registry.ROUTING_PREDECESSOR_IDS)
                & set(view["route"]["documents"])
            )

    def test_active_predecessor_provenance_is_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, active, _readback = self.build_active_fixture(
                Path(directory)
            )
            route = registry._routing_snapshot(active)
            provenance = active["context_routing"][
                "predecessor_provenance"
            ]
            self.assertEqual(
                tuple(provenance["records"]),
                registry.ROUTING_PREDECESSOR_IDS,
            )
            self.assertEqual(
                provenance["authority_effect"],
                "historical_provenance_only_no_runtime_read",
            )
            for identity in registry.ROUTING_PREDECESSOR_IDS:
                document = active["operational_documents"]["entries"][
                    identity
                ]
                self.assertEqual(
                    document["digest_policy"],
                    "provenance_only",
                )
                self.assertEqual(
                    document["current_status"],
                    {"state": "known", "value": "retired"},
                )
                self.assertEqual(
                    document["retention_posture"],
                    "archived",
                )
                self.assertEqual(
                    provenance["records"][identity][
                        "retirement_proof"
                    ]["owner_review_reference"],
                    active["approval"]["value"][
                        "owner_review_reference"
                    ],
                )
            self.assertEqual(
                active["representations"]["entries"][
                    "human_readable_context_routing"
                ]["canonical_path"],
                (
                    "framework/project/interfaces/project-console/data/"
                    "component-registry.js"
                ),
            )
            registry._validate_active_predecessor_exclusion(
                active,
                route,
            )
            for mutation_index, mutate in enumerate((
                lambda value: value["context_routing"].update(
                    {"source_import": {"path": "forbidden"}}
                ),
                lambda value: value["source_baseline"].update(
                    {"route_source": {"path": "forbidden"}}
                ),
                lambda value: value["context_routing"][
                    "predecessor_provenance"
                ]["records"]["context_routing"].update(
                    {"state": "current"}
                ),
                lambda value: value["context_routing"][
                    "readable_representation"
                ].update({"executable": True}),
            )):
                with self.subTest(mutation=mutation_index):
                    invalid = copy.deepcopy(active)
                    mutate(invalid)
                    invalid_route = registry._routing_snapshot(invalid)
                    with self.assertRaises(registry.RegistryError):
                        registry._validate_active_predecessor_exclusion(
                            invalid,
                            invalid_route,
                        )
    def test_schema_keeps_candidate_and_active_authorities_disjoint(self):
        schema = load_json(SCHEMA_PATH)
        with tempfile.TemporaryDirectory() as directory:
            _authority, _path, candidate, _route = (
                self.build_candidate_fixture(Path(directory))
            )
            candidate_with_active_field = copy.deepcopy(candidate)
            candidate_with_active_field["context_routing"][
                "readable_representation"
            ] = {}
            with self.assertRaises(registry.RegistryError):
                registry._validate_against_schema(
                    candidate_with_active_field,
                    schema,
                    schema,
                )
        with tempfile.TemporaryDirectory() as directory:
            _authority, active, _readback = self.build_active_fixture(
                Path(directory)
            )
            for namespace, field in (
                ("context_routing", "source_import"),
                ("context_routing", "parity_policy"),
                ("source_baseline", "route_source"),
            ):
                with self.subTest(namespace=namespace, field=field):
                    invalid = copy.deepcopy(active)
                    invalid[namespace][field] = {}
                    with self.assertRaises(registry.RegistryError):
                        registry._validate_against_schema(
                            invalid,
                            schema,
                            schema,
                        )

    def test_active_selection_uses_registry_not_predecessor_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, active, _readback = self.build_active_fixture(
                Path(directory)
            )
            view = (
                registry.load_fixture_component_registry_configuration_routing_view(
                    authority
                )
            )
            preview = registry.routed_profile_preview_from_view(
                view,
                profile_id="github_sync",
            )
            self.assertEqual(
                preview["source_sha256"],
                view["registry_sha256"],
            )
            predecessor_digests = {
                record["sha256"]
                for record in active["context_routing"][
                    "predecessor_provenance"
                ]["records"].values()
            }
            self.assertNotIn(
                preview["source_sha256"],
                predecessor_digests,
            )
            altered_view = copy.deepcopy(view)
            altered_view["routing_authority_sha256"] = next(
                iter(predecessor_digests)
            )
            with self.assertRaisesRegex(
                registry.RegistryError,
                "authority digest disagrees",
            ):
                registry.routed_profile_preview_from_view(
                    altered_view,
                    profile_id="github_sync",
                )
            with self.assertRaisesRegex(
                registry.RegistryError,
                "candidate predecessor validation only",
            ):
                registry.parity_report(active, view["route"])

    def test_fixed_receipt_reader_accepts_only_derived_owner_only_path(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, active, readback = self.build_active_fixture(
                Path(directory)
            )
            path = self.write_fixed_readback(authority, readback)
            schema = load_json(
                authority.repository_root
                / "framework"
                / "standards"
                / "automation"
                / "component-registry.schema.json"
            )
            loaded = registry._load_fixed_activation_readback(
                authority,
                active,
                schema=schema,
            )
            self.assertEqual(loaded, readback)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(
                path.parent.stat().st_mode & 0o777,
                0o700,
            )

    def test_receipt_binding_mutations_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, _active, readback = self.build_active_fixture(
                Path(directory)
            )
            mutations = {
                "complete": False,
                "issuer": "untrusted_fixture",
                "registry_sha256": "0" * 64,
                "governance_change_id": "GOV-2026-999",
                "implementation_contract_id": "wrong-contract",
                "approval_sha256": "1" * 64,
                "candidate_registry_sha256": "2" * 64,
                "bounded_diff_sha256": "3" * 64,
                "owner_review_reference": "github-review:wrong",
                "pull_request_number": 124,
                "approval_evidence_type": "github_review",
                "approved_by": "@SomeoneElse",
                "merged_by": "SomeoneElse",
                "merge_commit_revision": "6" * 40,
                "required_checks_state": "pending",
                "required_checks_revision": (
                    readback["remote_main_revision"]
                    if readback["remote_main_revision"]
                    != readback["approved_head_revision"]
                    else "4" * 40
                ),
                "remote_registry_sha256": "5" * 64,
            }
            for field, value in mutations.items():
                with self.subTest(field=field):
                    invalid = copy.deepcopy(readback)
                    invalid[field] = value
                    with self.assertRaises(registry.RegistryError):
                        registry.load_fixture_component_registry_routing_view(
                            authority,
                            activation_readback=invalid,
                        )

    def test_receipt_schema_rejects_missing_unknown_and_bad_chronology(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, _active, readback = self.build_active_fixture(
                Path(directory)
            )
            missing = copy.deepcopy(readback)
            missing.pop("complete")
            missing_merge_evidence = copy.deepcopy(readback)
            missing_merge_evidence.pop("approval_evidence_type")
            unknown = copy.deepcopy(readback)
            unknown["receipt_path"] = "/tmp/not-authorized"
            reversed_time = copy.deepcopy(readback)
            reversed_time["merged_at"] = (
                "2026-07-29T23:59:59-04:00"
            )
            invalid_locators = [
                "github-review:Thorncrag/ARRP#0123",
                "github-review:Other/ARRP#123",
                "https://github.com/Thorncrag/ARRP/pull/123",
                "github-review:component-registry-123",
            ]
            invalid_values = [
                missing,
                missing_merge_evidence,
                unknown,
                reversed_time,
            ]
            for locator in invalid_locators:
                invalid = copy.deepcopy(readback)
                invalid["owner_review_reference"] = locator
                invalid_values.append(invalid)
            for invalid in invalid_values:
                with self.assertRaises(registry.RegistryError):
                    registry.load_fixture_component_registry_routing_view(
                        authority,
                        activation_readback=invalid,
                    )

    def test_approved_head_must_contain_exact_active_registry(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, active, readback = self.build_active_fixture(
                Path(directory)
            )
            invalid = copy.deepcopy(readback)
            invalid["approved_head_revision"] = (
                active["approval"]["value"]["base_revision"]
            )
            invalid["required_checks_revision"] = (
                invalid["approved_head_revision"]
            )
            with self.assertRaisesRegex(
                registry.RegistryError,
                "activation revision registry",
            ):
                registry.load_fixture_component_registry_routing_view(
                    authority,
                    activation_readback=invalid,
                )

    def test_fixed_reader_rejects_file_and_parent_mode_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, active, readback = self.build_active_fixture(
                Path(directory)
            )
            path = self.write_fixed_readback(authority, readback)
            schema = load_json(
                authority.repository_root
                / "framework"
                / "standards"
                / "automation"
                / "component-registry.schema.json"
            )
            os.chmod(path, 0o640)
            with self.assertRaisesRegex(
                registry.RegistryError,
                "fixed activation readback is unavailable",
            ):
                registry._load_fixed_activation_readback(
                    authority,
                    active,
                    schema=schema,
                )
            os.chmod(path, 0o600)
            os.chmod(path.parent, 0o750)
            with self.assertRaisesRegex(
                registry.RegistryError,
                "mode 0700",
            ):
                registry._load_fixed_activation_readback(
                    authority,
                    active,
                    schema=schema,
                )

    def test_fixed_reader_rejects_duplicate_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, active, readback = self.build_active_fixture(
                Path(directory)
            )
            path = self.write_fixed_readback(authority, readback)
            text = json.dumps(readback, ensure_ascii=False)
            path.write_text(
                text[:-1] + ',"complete":true}\n',
                encoding="utf-8",
            )
            os.chmod(path, 0o600)
            schema = load_json(
                authority.repository_root
                / "framework"
                / "standards"
                / "automation"
                / "component-registry.schema.json"
            )
            with self.assertRaisesRegex(
                registry.RegistryError,
                "duplicate field",
            ):
                registry._load_fixed_activation_readback(
                    authority,
                    active,
                    schema=schema,
                )

    def test_production_reader_rejects_fixture_or_forged_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            authority, _path, _candidate, _route = (
                self.build_candidate_fixture(Path(directory))
            )
            with self.assertRaisesRegex(
                registry.RegistryError,
                "mode is not permitted",
            ):
                registry.load_validated_component_registry_routing_view(
                    authority
                )
            forged = ProjectPathAuthority(
                "fixture",
                ROOT,
                ROOT,
                ROOT,
                ROOT,
            )
            with self.assertRaises(registry.RegistryError):
                registry.load_fixture_component_registry_routing_view(
                    forged
                )


class ComponentRegistryStage2ReadbackTests(unittest.TestCase):
    def setUp(self):
        self.stage2 = load_json(REGISTRY_PATH)
        self.stage2_receipt = finalizer._build_stage2_synthetic_receipt(
            self.stage2,
            canonical_revision="1" * 40,
            adoption_evidence={
                "adopted_by": "@Thorncrag",
                "adopted_at": "2026-07-31T12:00:00-04:00",
                "pull_request": "github-review:Thorncrag/ARRP#501",
                "reviewed_head": "2" * 40,
                "merge_commit": "1" * 40,
                "checks_revision": "2" * 40,
                "checks_state": "success",
            },
        )

    def test_stage2_receipt_selected_with_stage1_preserved(self):
        preserved_stage1 = {
            "verification_type": "component_registry_activation_readback",
            "registry_sha256": "0" * 64,
        }
        selected = finalizer.select_component_registry_receipt(
            self.stage2,
            [preserved_stage1, self.stage2_receipt],
        )
        self.assertEqual(selected["validation_mode"], "live_authority_validation")
        self.assertEqual(selected["receipt"], self.stage2_receipt)

    def test_wrong_digest_and_duplicate_stage2_receipts_fail_closed(self):
        wrong = copy.deepcopy(self.stage2_receipt)
        wrong["registry_sha256"] = "f" * 64
        with self.assertRaisesRegex(
            finalizer.ActivationFinalizationError, "exactly one"
        ):
            finalizer.select_component_registry_receipt(self.stage2, [wrong])
        with self.assertRaisesRegex(
            finalizer.ActivationFinalizationError, "exactly one"
        ):
            finalizer.select_component_registry_receipt(
                self.stage2, [self.stage2_receipt, copy.deepcopy(self.stage2_receipt)]
            )

    def test_verified_stage1_reversion_selects_preserved_stage1_receipt(self):
        result = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "show",
                "HEAD:framework/component-registry.json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        stage1_registry = json.loads(result.stdout)
        self.assertEqual(stage1_registry["schema_version"], 1)
        preserved_stage1 = {
            "verification_type": "component_registry_activation_readback",
            "registry_sha256": registry._canonical_registry_digest(stage1_registry),
        }
        selected = finalizer.select_component_registry_receipt(
            stage1_registry,
            [self.stage2_receipt, preserved_stage1],
        )
        self.assertEqual(selected["validation_mode"], "active_component_registry")
        self.assertEqual(selected["receipt"], preserved_stage1)

    def test_schema_closes_stage2_receipt(self):
        schema = load_json(SCHEMA_PATH)
        registry._validate_against_schema(
            self.stage2_receipt,
            schema["$defs"]["componentRegistryStage2AdoptionReadback"],
            schema,
        )
        malformed = copy.deepcopy(self.stage2_receipt)
        malformed["adoption_evidence"]["unexpected"] = True
        with self.assertRaises(registry.RegistryError):
            registry._validate_against_schema(
                malformed,
                schema["$defs"]["componentRegistryStage2AdoptionReadback"],
                schema,
            )


if __name__ == "__main__":
    unittest.main()
