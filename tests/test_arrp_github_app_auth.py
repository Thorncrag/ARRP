import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "arrp_nightly_p4", ROOT / "scripts" / "arrp_nightly.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def intent(**updates):
    value = {
        "operation_type": "set_project_field",
        "repository": "Thorncrag/ARRP",
        "target_node_or_number": "PVTI_fixture",
        "source_revision": "a" * 40,
        "authority_record": "framework/project/github/workflow.md",
        "expected_old_state": "old",
        "new_state_or_content": "new",
        "idempotency_key": "fixture-transition-1",
        "privacy_class": "public",
        "human_reserved": False,
        "rollback_or_correction": "restore old after fixture readback",
        "readback_contract": "exact field value equals requested value",
    }
    value.update(updates)
    return value


class GitHubAppCredentialTests(unittest.TestCase):
    def test_keychain_hex_readback_normalizes_private_key(self):
        key_type = "RSA " + "PRIVATE " + "KEY"
        pem = f"-----BEGIN {key_type}-----\nfixture\n-----END {key_type}-----\n"
        completed = mock.Mock(
            returncode=0,
            stdout=pem.encode("utf-8").hex() + "\n",
            stderr="",
        )
        with mock.patch.object(
            MODULE.subprocess, "run", return_value=completed
        ):
            wrapped = MODULE.read_keychain_secret("fixture-service", "fixture-account")
        self.assertEqual(wrapped.reveal(), pem)

    def test_sensitive_value_never_displays_secret(self):
        wrapped = MODULE.SensitiveValue("fixture-token-value")
        self.assertEqual(str(wrapped), "<redacted>")
        self.assertEqual(repr(wrapped), "<redacted>")
        self.assertNotIn("fixture-token-value", json.dumps({"token": repr(wrapped)}))

    def test_identity_file_is_repository_bound_and_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "identity.json"
            path.write_text(
                json.dumps(
                    {
                        "app_id": 1,
                        "installation_id": 2,
                        "repository_id": 3,
                        "repository": "Thorncrag/ARRP",
                    }
                ),
                encoding="utf-8",
            )
            identity = MODULE.GitHubAppIdentity.from_json(path)
            self.assertEqual(identity.installation_id, 2)
            value = json.loads(path.read_text(encoding="utf-8"))
            value["repository"] = "Thorncrag/unrelated"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.GitHubBrokerError, "unexpected fields"):
                MODULE.GitHubAppIdentity.from_json(path)

    def test_installation_token_is_downscoped_to_one_repository_and_permissions(self):
        identity = MODULE.GitHubAppIdentity(1, 2, 3)
        observed = {}

        def api_request(method, path, token, *, payload):
            observed.update(
                method=method,
                path=path,
                token=repr(token),
                payload=payload,
            )
            return {"token": "installation-fixture"}

        with mock.patch.object(
            MODULE,
            "create_github_app_jwt",
            return_value=MODULE.SensitiveValue("jwt-fixture"),
        ):
            token = MODULE.mint_installation_token(
                identity,
                MODULE.SensitiveValue("private-key-fixture"),
                api_request=api_request,
                now=1_700_000_000,
            )
        self.assertEqual(repr(token), "<redacted>")
        self.assertEqual(observed["payload"]["repository_ids"], [3])
        self.assertNotIn("administration", observed["payload"]["permissions"])
        self.assertNotIn("secrets", observed["payload"]["permissions"])
        self.assertNotIn("workflows", observed["payload"]["permissions"])

    def test_push_credential_never_enters_argv_or_environment_value(self):
        completed = mock.Mock(returncode=0, stdout=b"", stderr=b"")
        token = MODULE.SensitiveValue("push-fixture-token")
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            MODULE.subprocess, "run", return_value=completed
        ) as run:
            MODULE.git_push_with_token(
                Path(directory), "HEAD:refs/heads/fixture", token
            )
        arguments = run.call_args.args[0]
        environment = run.call_args.kwargs["env"]
        self.assertNotIn(token.reveal(), " ".join(arguments))
        self.assertNotIn(token.reveal(), json.dumps(environment))
        self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")

    def test_revoked_or_rotated_credentials_fail_closed_without_value(self):
        token = MODULE.SensitiveValue("revoked-fixture-token")
        error = MODULE.urllib.error.URLError("fixture unavailable")
        with mock.patch.object(MODULE.urllib.request, "urlopen", side_effect=error):
            with self.assertRaises(MODULE.GitHubBrokerError) as raised:
                MODULE.github_api_request("GET", "/fixture", token)
        self.assertNotIn(token.reveal(), str(raised.exception))


class BrokerIntentTests(unittest.TestCase):
    def test_registered_intent_requires_exact_revision_and_nonhuman_authority(self):
        accepted = MODULE.validate_broker_intent(
            intent(), source_revision="a" * 40
        )
        self.assertEqual(accepted["operation_type"], "set_project_field")
        for changed in (
            {"source_revision": "b" * 40},
            {"human_reserved": True},
            {"privacy_class": "private"},
            {"repository": "Thorncrag/unrelated"},
            {"operation_type": "delete_repository"},
        ):
            with self.assertRaises(MODULE.GitHubBrokerError):
                MODULE.validate_broker_intent(
                    intent(**changed), source_revision="a" * 40
                )

    def test_project_fixture_round_trip_and_restoration(self):
        state = {"value": "old"}

        def read_field(_intent, _token):
            return state["value"]

        def write_field(_intent, value, _token):
            state["value"] = value

        token = MODULE.SensitiveValue("project-fixture")
        change = intent()
        changed = MODULE.execute_project_field_intent(
            change, token, read_field=read_field, write_field=write_field
        )
        self.assertEqual(changed["new_state"], "new")
        restore = intent(
            expected_old_state="new",
            new_state_or_content="old",
            idempotency_key="fixture-transition-restore",
        )
        restored = MODULE.execute_project_field_intent(
            restore, token, read_field=read_field, write_field=write_field
        )
        self.assertEqual(restored["new_state"], "old")
        self.assertEqual(state["value"], "old")


class ExactPullRequestTests(unittest.TestCase):
    def test_ordinary_app_pr_merges_at_exact_head_and_base(self):
        head = "a" * 40
        base = "b" * 40
        merge = "c" * 40
        calls = []

        def api(method, path, token, *, payload=None):
            calls.append((method, path, payload))
            if path.endswith("/pulls/7"):
                return {"head": {"sha": head}, "base": {"sha": base}}
            if path.endswith("/pulls/7/reviews?per_page=100"):
                return []
            if "check-runs" in path:
                return {
                    "check_runs": [
                        {"name": "ARRP Validation", "conclusion": "success"},
                        {"name": "CodeQL", "conclusion": "success"},
                    ]
                }
            if path.endswith("/status"):
                return {"statuses": []}
            if path.endswith("/pulls/7/merge"):
                self.assertEqual(payload, {"merge_method": "merge", "sha": head})
                return {"merged": True, "sha": merge}
            if path.endswith(f"/git/commits/{merge}"):
                return {"parents": [{"sha": base}, {"sha": head}]}
            raise AssertionError(path)

        observed = MODULE.merge_exact_head(
            MODULE.SensitiveValue("app-fixture"),
            pull_number=7,
            expected_head=head,
            expected_base=base,
            protected=False,
            api_request=api,
        )
        self.assertEqual(observed, merge)
        self.assertIn(
            ("PUT", "/repos/Thorncrag/ARRP/pulls/7/merge", {"merge_method": "merge", "sha": head}),
            calls,
        )

    def test_protected_app_pr_is_blocked_without_benjamin(self):
        head = "a" * 40
        base = "b" * 40

        def api(method, path, token, *, payload=None):
            if path.endswith("/pulls/7"):
                return {"head": {"sha": head}, "base": {"sha": base}}
            if path.endswith("/pulls/7/reviews?per_page=100"):
                return []
            raise AssertionError(path)

        with self.assertRaisesRegex(
            MODULE.GitHubBrokerError, "lacks Benjamin code-owner approval"
        ):
            MODULE.merge_exact_head(
                MODULE.SensitiveValue("app-fixture"),
                pull_number=7,
                expected_head=head,
                expected_base=base,
                protected=True,
                api_request=api,
            )

    def test_workflow_file_is_protected_and_app_has_no_workflow_permission(self):
        self.assertEqual(
            MODULE.classify_path(
                ".github/workflows/fixture.yml", 0o644, tracked=False
            ),
            "protected",
        )
        self.assertNotIn("workflows", MODULE.APP_REPOSITORY_PERMISSIONS)


if __name__ == "__main__":
    unittest.main()
