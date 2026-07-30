import inspect
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.arrp_nightly import SensitiveValue
from scripts.refresh_project_console import (
    ConsoleRefreshError,
    _component_registry_configuration_state,
    _production_interpreter,
    _refresh_console,
    refresh_console,
)


class FakeAuthority:
    mode = "production_canonical"

    def __init__(self, repository_root: Path):
        self.repository_root = repository_root

    def repository_path(self, relative: str, *, required: bool = True) -> Path:
        path = self.repository_root / relative
        if required and not path.is_file():
            raise AssertionError(f"missing fixture file: {relative}")
        return path

    def repository_output(self, relative: str) -> Path:
        return self.repository_root / relative


class FakeRunner:
    def __init__(
        self,
        *,
        dirty: bool = False,
        failed_script: str | None = None,
    ):
        self.dirty = dirty
        self.failed_script = failed_script
        self.calls: list[tuple[list[str], dict[str, str] | None]] = []

    def __call__(self, command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        environment = kwargs.get("env")
        self.calls.append(
            (
                list(command),
                dict(environment) if isinstance(environment, dict) else None,
            )
        )
        if command[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=" M tracked-file\n" if self.dirty else "",
                stderr="",
            )
        script = Path(command[1]).name
        if self.failed_script == script:
            return subprocess.CompletedProcess(
                command,
                9,
                stdout="",
                stderr="secret-canary provider detail",
            )
        if script == "build_project_console_progress.py":
            output = Path(command[command.index("--output") + 1])
            output.mkdir(parents=True)
            (output / "progress.json").write_text(
                '{"generation_id":"fixture"}\n',
                encoding="utf-8",
            )
        elif script == "audit_project_consistency.py":
            output = Path(command[command.index("--json-output") + 1])
            output.write_text('{"result":"fixture"}\n', encoding="utf-8")
        elif script == "build_project_integrity_feed.py":
            output = Path(command[command.index("--output") + 1])
            output.write_text(
                '{"current":{"result":"fixture"},"history":[]}\n',
                encoding="utf-8",
            )
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="",
            stderr="",
        )


def fixture_authority(root: Path) -> FakeAuthority:
    for relative in (
        ".venv/bin/python",
        "scripts/build_project_console_progress.py",
        "scripts/audit_project_consistency.py",
        "scripts/build_project_integrity_feed.py",
        "scripts/build_project_console.py",
        "framework/project/interfaces/project-console-progress.json",
        "inventory/github_issue_registry.csv",
        "framework/project/interfaces/project-console/data/integrity.js",
        "framework/status/project-integrity-report.md",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    return FakeAuthority(root)


class ConsoleAuthenticatedRefreshTest(unittest.TestCase):
    def test_configuration_validation_is_nonlive_and_zero_argument(self) -> None:
        view = {
            "schema_version": 1,
            "validation_mode": "active_configuration_validation_only",
            "registry_status": "active",
            "registry_path": "framework/component-registry.json",
            "authoritative": False,
            "executable": False,
            "live_activation_verified": False,
            "activation_receipt_consulted": False,
            "predecessor_route_consulted": False,
        }
        with patch(
            "scripts.refresh_project_console."
            "load_component_registry_configuration_routing_view",
            return_value=view,
        ) as loader:
            self.assertEqual(
                _component_registry_configuration_state(),
                "active_configuration_validation_only",
            )
        loader.assert_called_once_with()

        candidate = {
            **view,
            "validation_mode": "candidate_validation_only",
            "registry_status": "candidate",
            "predecessor_route_consulted": True,
        }
        with patch(
            "scripts.refresh_project_console."
            "load_component_registry_configuration_routing_view",
            return_value=candidate,
        ) as candidate_loader:
            self.assertEqual(
                _component_registry_configuration_state(),
                "candidate_validation_only",
            )
        candidate_loader.assert_called_once_with()

        incompatible = dict(view)
        incompatible["live_activation_verified"] = True
        with patch(
            "scripts.refresh_project_console."
            "load_component_registry_configuration_routing_view",
            return_value=incompatible,
        ):
            with self.assertRaisesRegex(
                ConsoleRefreshError,
                "incompatible authority mode",
            ):
                _component_registry_configuration_state()

    def test_exact_subprocesses_receive_only_the_project_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            authority = fixture_authority(root)
            runner = FakeRunner()
            keychain_calls: list[tuple[str, str]] = []

            def read_secret(service: str, account: str) -> SensitiveValue:
                keychain_calls.append((service, account))
                return SensitiveValue("secret-canary")

            with patch(
                "scripts.refresh_project_console."
                "_component_registry_configuration_state",
                return_value="candidate_validation_only",
            ):
                result = _refresh_console(
                    authority=authority,
                    interpreter=root / ".venv/bin/python",
                    run=runner,
                    secret_reader=read_secret,
                    base_environment={
                        "PATH": "/usr/bin",
                        "ARRP_PROJECT_TOKEN": "inherited-project-token",
                        "GH_TOKEN": "inherited-gh-token",
                        "GITHUB_TOKEN": "inherited-actions-token",
                    },
                )

        self.assertEqual(result["status"], "refreshed")
        self.assertEqual(
            result["component_registry_validation_mode"],
            "candidate_validation_only",
        )
        self.assertEqual(len(keychain_calls), 1)
        self.assertEqual(
            [Path(call[0][1]).name for call in runner.calls[1:]],
            [
                "build_project_console_progress.py",
                "audit_project_consistency.py",
                "build_project_integrity_feed.py",
                "build_project_console.py",
            ],
        )
        integrity_command = next(
            command
            for command, _environment in runner.calls[1:]
            if Path(command[1]).name == "audit_project_consistency.py"
        )
        self.assertEqual(
            integrity_command.count("--routing-authority"),
            1,
        )
        self.assertEqual(
            integrity_command[
                integrity_command.index("--routing-authority") + 1
            ],
            "production-canonical",
        )
        for command, environment in runner.calls[1:]:
            self.assertNotIn("secret-canary", command)
            self.assertNotIn("GH_TOKEN", environment)
            self.assertNotIn("GITHUB_TOKEN", environment)
            if Path(command[1]).name == "build_project_integrity_feed.py":
                self.assertNotIn("ARRP_PROJECT_TOKEN", environment)
            else:
                self.assertEqual(
                    environment["ARRP_PROJECT_TOKEN"],
                    "secret-canary",
                )

    def test_dirty_tree_fails_before_keychain_access(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            authority = fixture_authority(Path(temporary))
            runner = FakeRunner(dirty=True)
            keychain_called = False

            def read_secret(service: str, account: str) -> SensitiveValue:
                nonlocal keychain_called
                keychain_called = True
                return SensitiveValue("secret-canary")

            with self.assertRaisesRegex(
                ConsoleRefreshError,
                "tracked tree must be clean",
            ):
                with patch(
                    "scripts.refresh_project_console."
                    "_component_registry_configuration_state",
                    return_value="candidate_validation_only",
                ):
                    _refresh_console(
                        authority=authority,
                        interpreter=Path(temporary) / ".venv/bin/python",
                        run=runner,
                        secret_reader=read_secret,
                    )

        self.assertFalse(keychain_called)
        self.assertEqual(len(runner.calls), 1)

    def test_configuration_failure_precedes_keychain_access(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            authority = fixture_authority(Path(temporary))
            runner = FakeRunner()
            keychain_called = False

            def read_secret(service: str, account: str) -> SensitiveValue:
                nonlocal keychain_called
                keychain_called = True
                return SensitiveValue("secret-canary")

            with patch(
                "scripts.refresh_project_console."
                "_component_registry_configuration_state",
                side_effect=ConsoleRefreshError(
                    "Component Registry configuration validation is unavailable."
                ),
            ):
                with self.assertRaisesRegex(
                    ConsoleRefreshError,
                    "configuration validation is unavailable",
                ):
                    _refresh_console(
                        authority=authority,
                        interpreter=Path(temporary) / ".venv/bin/python",
                        run=runner,
                        secret_reader=read_secret,
                    )

        self.assertFalse(keychain_called)
        self.assertEqual(len(runner.calls), 1)

    def test_child_failure_does_not_echo_sensitive_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            authority = fixture_authority(Path(temporary))
            runner = FakeRunner(
                failed_script="build_project_console_progress.py"
            )
            with self.assertRaises(ConsoleRefreshError) as raised:
                with patch(
                    "scripts.refresh_project_console."
                    "_component_registry_configuration_state",
                    return_value="candidate_validation_only",
                ):
                    _refresh_console(
                        authority=authority,
                        interpreter=Path(temporary) / ".venv/bin/python",
                        run=runner,
                        secret_reader=lambda service, account: SensitiveValue(
                            "secret-canary"
                        ),
                    )

        message = str(raised.exception)
        self.assertIn("Authenticated Project projection failed", message)
        self.assertNotIn("secret-canary", message)
        self.assertNotIn("provider detail", message)

    def test_production_entry_point_has_no_caller_selected_authority(self) -> None:
        self.assertEqual(dict(inspect.signature(refresh_console).parameters), {})

    def test_production_interpreter_preserves_verified_venv_launcher(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bin_directory = root / ".venv/bin"
            bin_directory.mkdir(parents=True)
            interpreter = bin_directory / "python"
            interpreter.symlink_to(Path(sys.executable).resolve())
            with patch(
                "scripts.refresh_project_console.sys.prefix",
                str(root / ".venv"),
            ):
                self.assertEqual(
                    _production_interpreter(root),
                    interpreter,
                )


if __name__ == "__main__":
    unittest.main()
