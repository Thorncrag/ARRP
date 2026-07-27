#!/usr/bin/env python3
"""Write deterministic queue or context JSON for the P2 fixture cycle."""

import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--kind", choices=("queue", "context"), required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(
    json.dumps(
        {
            "schema_version": 1,
            "kind": args.kind,
            "unit_id": "fixture-unit",
            "selected": True,
        },
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
