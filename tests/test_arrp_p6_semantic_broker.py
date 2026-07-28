import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "arrp_nightly_p6_broker", ROOT / "scripts" / "arrp_nightly.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
REVISION = "a" * 40


def broker_intent(operation, target, expected, new, **updates):
    value = {
        "operation_type": operation,
        "repository": "Thorncrag/ARRP",
        "target_node_or_number": MODULE.encode_broker_target(operation, target),
        "source_revision": REVISION,
        "authority_record": "framework/project/github/workflow.md",
        "expected_old_state": expected,
        "new_state_or_content": new,
        "idempotency_key": "ARRP-IDEMPOTENCY:fixture-1",
        "privacy_class": "public",
        "human_reserved": False,
        "rollback_or_correction": "restore the exact prior state or post a correction",
        "readback_contract": MODULE.BROKER_READBACK_CONTRACTS[operation],
    }
    value.update(updates)
    return value


class BrokerSchemaTests(unittest.TestCase):
    def test_schema_registers_exact_intent_fields_and_excludes_runner_pr(self):
        schema = json.loads(
            (
                ROOT
                / "framework/project/automation/schemas/elim-work-unit-result.schema.json"
            ).read_text(encoding="utf-8")
        )
        requests = schema["properties"]["github_action_requests"]
        incidents = schema["properties"]["incident_reports"]
        item = requests["items"]
        self.assertIn("incident_reports", schema["required"])
        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        self.assertEqual(incidents["maxItems"], 16)
        self.assertFalse(incidents["items"]["additionalProperties"])
        self.assertIn("closure_test", incidents["items"]["required"])
        self.assertIn("recommended_owner", incidents["items"]["required"])
        self.assertEqual(requests["maxItems"], 128)
        self.assertFalse(item["additionalProperties"])
        self.assertEqual(set(item["required"]), MODULE.BROKER_INTENT_FIELDS)
        operations = item["properties"]["operation_type"]["enum"]
        self.assertEqual(set(operations), MODULE.BROKER_OPERATION_TYPES)
        self.assertNotIn("nightly_pull_request", operations)

    def test_targets_require_exact_canonical_json_and_registered_shape(self):
        target = {
            "project_id": "PVT_fixture",
            "item_id": "PVTI_fixture",
            "field_id": "PVTF_fixture",
        }
        encoded = MODULE.encode_broker_target("set_project_field", target)
        self.assertEqual(MODULE.decode_broker_target("set_project_field", encoded), target)
        for invalid in (
            json.dumps(target),
            json.dumps({**target, "other": "x"}, sort_keys=True, separators=(",", ":")),
            "PVTI_fixture",
        ):
            with self.assertRaises(MODULE.GitHubBrokerError):
                MODULE.decode_broker_target("set_project_field", invalid)

    def test_model_requested_nightly_pull_request_is_rejected(self):
        value = broker_intent(
            "read_state",
            {"kind": "issue", "issue_number": 1},
            None,
            None,
        )
        value["operation_type"] = "nightly_pull_request"
        with self.assertRaisesRegex(MODULE.GitHubBrokerError, "runner-owned"):
            MODULE.validate_broker_intent(value, source_revision=REVISION)


class BrokerExecutorTests(unittest.TestCase):
    def test_production_semantic_preflight_precedes_project_credential_access(self):
        prohibited_value = "api" + "_key=" + ("x" * 24)
        value = broker_intent(
            "set_project_field",
            {
                "project_id": "PVT_fixture",
                "item_id": "PVTI_fixture",
                "field_id": "PVTF_fixture",
            },
            "old",
            prohibited_value,
        )
        with mock.patch.object(MODULE, "read_keychain_secret") as credential:
            with self.assertRaisesRegex(
                MODULE.DisclosurePreventionError,
                "disclosure blocked",
            ):
                MODULE.execute_production_semantic_actions(
                    [value],
                    source_revision=REVISION,
                    github_token=MODULE.SensitiveValue("fixture"),
                )
        credential.assert_not_called()

    def test_project_field_disclosure_gate_runs_before_read_or_write(self):
        calls = []
        prohibited_value = "api" + "_key=" + ("x" * 24)
        value = broker_intent(
            "set_project_field",
            {
                "project_id": "PVT_fixture",
                "item_id": "PVTI_fixture",
                "field_id": "PVTF_fixture",
            },
            "old",
            prohibited_value,
        )

        def unexpected(*args):
            calls.append(args)
            raise AssertionError("Project access must not occur")

        with self.assertRaisesRegex(MODULE.GitHubBrokerError, "disclosure blocked"):
            MODULE.execute_project_field_intent(
                value,
                MODULE.SensitiveValue("fixture"),
                read_field=unexpected,
                write_field=unexpected,
            )
        self.assertEqual(calls, [])

    def test_issue_and_discussion_disclosure_gates_run_before_network(self):
        calls = []
        prohibited_value = "authorization" + ": " + "bearer " + ("x" * 24)

        def unexpected(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("Network access must not occur")

        issue = broker_intent(
            "update_issue_wrapper",
            {
                "issue_number": 17,
                "marker": "<!-- ARRP-WRAPPER:fixture-1 -->",
            },
            {"body": "old"},
            {"body": prohibited_value},
        )
        with self.assertRaisesRegex(MODULE.GitHubBrokerError, "disclosure blocked"):
            MODULE.execute_issue_wrapper_intent(
                issue,
                MODULE.SensitiveValue("fixture"),
                api_request=unexpected,
            )
        discussion = broker_intent(
            "post_discussion_reply",
            {"discussion_number": 12, "reply_to_comment_id": 345},
            {"reply_absent": "fixture"},
            {"body": prohibited_value},
        )
        with self.assertRaisesRegex(MODULE.GitHubBrokerError, "disclosure blocked"):
            MODULE.execute_discussion_reply_intent(
                discussion,
                MODULE.SensitiveValue("fixture"),
                graphql_request=unexpected,
            )
        self.assertEqual(calls, [])

    def test_project_field_requires_prior_state_and_is_idempotent(self):
        state = {"value": "old"}
        writes = []

        def read_field(_target, _token):
            return state["value"]

        def write_field(_target, value, _token):
            writes.append(value)
            state["value"] = value

        value = broker_intent(
            "set_project_field",
            {
                "project_id": "PVT_fixture",
                "item_id": "PVTI_fixture",
                "field_id": "PVTF_fixture",
            },
            "old",
            "new",
        )
        MODULE.validate_broker_intent(value, source_revision=REVISION)
        first = MODULE.execute_project_field_intent(
            value,
            MODULE.SensitiveValue("fixture"),
            read_field=read_field,
            write_field=write_field,
        )
        second = MODULE.execute_project_field_intent(
            value,
            MODULE.SensitiveValue("fixture"),
            read_field=read_field,
            write_field=write_field,
        )
        self.assertFalse(first["already_applied"])
        self.assertTrue(second["already_applied"])
        self.assertEqual(writes, ["new"])

    def test_issue_wrapper_uses_exact_prior_state_and_readback(self):
        marker = "<!-- ARRP-WRAPPER:fixture-1 -->"
        state = {"body": "old"}
        calls = []

        def api(method, path, _token, *, payload=None):
            calls.append((method, path, payload))
            if method == "PATCH":
                state["body"] = payload["body"]
            return {"number": 17, "body": state["body"], "state": "open"}

        value = broker_intent(
            "update_issue_wrapper",
            {"issue_number": 17, "marker": marker},
            {"body": "old"},
            {"body": f"bounded wrapper\n\n{marker}"},
        )
        MODULE.validate_broker_intent(value, source_revision=REVISION)
        first = MODULE.execute_issue_wrapper_intent(
            value, MODULE.SensitiveValue("fixture"), api_request=api
        )
        second = MODULE.execute_issue_wrapper_intent(
            value, MODULE.SensitiveValue("fixture"), api_request=api
        )
        self.assertFalse(first["already_applied"])
        self.assertTrue(second["already_applied"])
        self.assertEqual([call[0] for call in calls].count("PATCH"), 1)

    def test_issue_wrapper_rejects_prior_state_mismatch_before_write(self):
        marker = "<!-- ARRP-WRAPPER:fixture-2 -->"
        methods = []

        def api(method, _path, _token, *, payload=None):
            methods.append(method)
            return {"number": 17, "body": "unexpected", "state": "open"}

        value = broker_intent(
            "update_issue_wrapper",
            {"issue_number": 17, "marker": marker},
            {"body": "old"},
            {"body": f"bounded wrapper\n\n{marker}"},
        )
        with self.assertRaisesRegex(MODULE.GitHubBrokerError, "prior-state"):
            MODULE.execute_issue_wrapper_intent(
                value, MODULE.SensitiveValue("fixture"), api_request=api
            )
        self.assertEqual(methods, ["GET"])

    def test_discussion_reply_posts_once_and_reads_back_exactly(self):
        marker = "<!-- ARRP-ELIM-REPLY:fixture -->"
        replies = []
        calls = []

        def graphql(query, variables, _token):
            calls.append((query.lstrip().split("(", 1)[0], dict(variables)))
            if query.lstrip().startswith("mutation"):
                replies.append({"id": "DC_reply_fixture", "body": variables["body"]})
                return {
                    "addDiscussionComment": {
                        "comment": {"id": "DC_reply_fixture", "body": variables["body"]}
                    }
                }
            return {
                "repository": {
                    "discussion": {
                        "id": "D_fixture",
                        "comments": {
                            "nodes": [
                                {
                                    "id": "DC_parent_fixture",
                                    "databaseId": 345,
                                    "body": "submission",
                                    "replies": {
                                        "nodes": list(replies),
                                        "pageInfo": {"hasNextPage": False},
                                    },
                                }
                            ],
                            "pageInfo": {"hasNextPage": False},
                        },
                    }
                }
            }

        value = broker_intent(
            "post_discussion_reply",
            {"discussion_number": 12, "reply_to_comment_id": 345},
            {"reply_absent": marker},
            {"body": f"Validated informative reply.\n\n{marker}"},
            idempotency_key=marker,
        )
        MODULE.validate_broker_intent(value, source_revision=REVISION)
        first = MODULE.execute_discussion_reply_intent(
            value, MODULE.SensitiveValue("fixture"), graphql_request=graphql
        )
        second = MODULE.execute_discussion_reply_intent(
            value, MODULE.SensitiveValue("fixture"), graphql_request=graphql
        )
        self.assertFalse(first["already_applied"])
        self.assertTrue(second["already_applied"])
        self.assertEqual(sum(name.startswith("mutation") for name, _ in calls), 1)

    def test_discussion_duplicate_idempotency_marker_fails_closed(self):
        marker = "<!-- ARRP-ELIM-REPLY:duplicate -->"

        def graphql(_query, _variables, _token):
            return {
                "repository": {
                    "discussion": {
                        "id": "D_fixture",
                        "comments": {
                            "nodes": [
                                {
                                    "id": "DC_parent_fixture",
                                    "databaseId": 345,
                                    "body": "submission",
                                    "replies": {
                                        "nodes": [
                                            {"id": "DC_one", "body": f"one\n{marker}"},
                                            {"id": "DC_two", "body": f"two\n{marker}"},
                                        ],
                                        "pageInfo": {"hasNextPage": False},
                                    },
                                }
                            ],
                            "pageInfo": {"hasNextPage": False},
                        },
                    }
                }
            }

        value = broker_intent(
            "post_discussion_reply",
            {"discussion_number": 12, "reply_to_comment_id": 345},
            {"reply_absent": marker},
            {"body": f"Validated reply.\n\n{marker}"},
            idempotency_key=marker,
        )
        with self.assertRaisesRegex(MODULE.GitHubBrokerError, "duplicated"):
            MODULE.execute_discussion_reply_intent(
                value, MODULE.SensitiveValue("fixture"), graphql_request=graphql
            )

    def test_read_state_checks_exact_snapshot_without_mutation(self):
        calls = []

        def api(method, path, _token, *, payload=None):
            calls.append((method, path, payload))
            return {"number": 9, "body": "wrapper", "state": "open"}

        value = broker_intent(
            "read_state",
            {"kind": "issue", "issue_number": 9},
            {"body": "wrapper", "state": "open"},
            None,
        )
        MODULE.validate_broker_intent(value, source_revision=REVISION)
        result = MODULE.execute_read_state_intent(
            value, MODULE.SensitiveValue("fixture"), api_request=api
        )
        self.assertEqual(result["state"], value["expected_old_state"])
        self.assertFalse(result["mutated"])
        self.assertEqual(calls[0][0], "GET")


if __name__ == "__main__":
    unittest.main()
