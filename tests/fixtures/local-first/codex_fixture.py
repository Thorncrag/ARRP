#!/usr/bin/env python3
"""Codex CLI fixture that records the sealed boundary without a model turn."""

import json
import os
import sys
from pathlib import Path


DISABLED = {
    "apps",
    "browser_use",
    "computer_use",
    "goals",
    "hooks",
    "image_generation",
    "memories",
    "multi_agent",
    "plugin_sharing",
    "plugins",
    "remote_plugin",
    "skill_mcp_dependency_install",
    "skill_search",
    "tool_suggest",
    "workspace_dependencies",
}


def option(name: str) -> str:
    index = sys.argv.index(name)
    return sys.argv[index + 1]


if sys.argv[1:3] == ["features", "list"]:
    for feature in sorted(DISABLED):
        print(f"{feature} stable false")
    raise SystemExit(0)

if len(sys.argv) < 2 or sys.argv[1] != "exec":
    raise SystemExit(64)

worktree = Path.cwd().resolve()
fixture_root = os.path.realpath(os.fspath(worktree.parent.parent))
normalized_run_dir = os.path.realpath(
    os.path.join(fixture_root, os.environ["ARRP_RUN_DIR"])
)
if (
    normalized_run_dir != fixture_root
    and not normalized_run_dir.startswith(fixture_root + os.sep)
):
    raise SystemExit("fixture run directory escapes the fixture root")
run_dir = Path(normalized_run_dir)
prompt = sys.stdin.read()
proof = worktree / "research/elim-fixture.txt"
proof.parent.mkdir(parents=True, exist_ok=True)
proof.write_text("sealed fixture result\n", encoding="utf-8")
(run_dir / "elim-invocation.json").write_text(
    json.dumps(
        {
            "argv": sys.argv[1:],
            "environment_keys": sorted(os.environ),
            "prompt": prompt,
        },
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
result = {
    "schema_version": 1,
    "run_id": json.loads(prompt)["run_id"],
    "unit_id": "fixture-unit",
    "work_type": "integrity",
    "outcome": "completed",
    "authority": {"classification": "mechanical", "basis": "fixture"},
    "issue_id": None,
    "canonical_record": None,
    "files_touched": ["research/elim-fixture.txt"],
    "source_ids": [],
    "validation": [],
    "commit": None,
    "synchronization": [],
    "human_questions": [],
    "continuation": {"state": "complete", "next_action": "none"},
    "discovered_work_units": [],
    "gap_obligation_updates": [],
    "github_action_requests": [],
}
normalized_output = os.path.realpath(option("--output-last-message"))
if not normalized_output.startswith(normalized_run_dir + os.sep):
    raise SystemExit("fixture result path escapes the run directory")
Path(normalized_output).write_text(
    json.dumps(result, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps({"type": "fixture.completed"}))
