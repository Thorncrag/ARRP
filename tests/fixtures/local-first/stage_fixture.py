#!/usr/bin/env python3
"""Deterministic typed-output fixture for one local ARRP stage."""

import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--stage-id", required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--value", default="fixture")
parser.add_argument("--exit-code", type=int, default=0)
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(
    json.dumps(
        {
            "schema_version": 1,
            "stage_id": args.stage_id,
            "status": "succeeded",
            "value": args.value,
        },
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
raise SystemExit(args.exit_code)
