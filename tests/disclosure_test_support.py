"""Generic disclosure controls for credential-free unit-test fixtures.

These controls are deliberately synthetic. They let mocked GitHub broker tests
exercise behavior after disclosure authorization without depending on the
owner-local production control pack.
"""

from __future__ import annotations

from typing import Any


TEST_CONTROL_PACK = {
    "schema_version": 1,
    "pack_id": "arrp-generic-unit-test-controls",
    "policy_id": "arrp-github-disclosure-v2",
    "control_version": "2026-07-28.1",
    "status": "active",
    "complete": True,
    "restricted_detectors": [
        {
            "id": "generic-unit-test-restricted-canary",
            "pattern": r"OWNER[- ]LOCAL[- ]CONTROL[- ]CANARY",
        }
    ],
    "restricted_path_patterns": ["restricted-local/**"],
}


def install_test_control_pack(module: Any) -> None:
    """Inject the synthetic pack into one dynamically loaded test module."""

    authoritative_require = module.require_outbound_bundle
    authoritative_evaluate = getattr(module, "evaluate_outbound_bundle", None)

    def require_with_test_controls(*args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("control_pack", TEST_CONTROL_PACK)
        return authoritative_require(*args, **kwargs)

    module.require_outbound_bundle = require_with_test_controls
    if authoritative_evaluate is not None:
        def evaluate_with_test_controls(
            *args: Any, **kwargs: Any
        ) -> dict[str, Any]:
            kwargs.setdefault("control_pack", TEST_CONTROL_PACK)
            return authoritative_evaluate(*args, **kwargs)

        module.evaluate_outbound_bundle = evaluate_with_test_controls
