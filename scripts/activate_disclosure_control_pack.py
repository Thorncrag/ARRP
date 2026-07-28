#!/usr/bin/env python3
"""Activate one validated owner-local ARRP disclosure control pack."""

from __future__ import annotations

import argparse
import json

try:
    from github_disclosure_gate import (
        DisclosureBlocked,
        activate_candidate_control_pack,
    )
except ModuleNotFoundError:
    from scripts.github_disclosure_gate import (
        DisclosureBlocked,
        activate_candidate_control_pack,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-id", required=True)
    args = parser.parse_args()
    try:
        result = activate_candidate_control_pack(args.candidate_id)
    except DisclosureBlocked as error:
        print(json.dumps(error.decision, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
