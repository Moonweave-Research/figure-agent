#!/usr/bin/env python3
"""Write an explicit receipt for the strict-detector outcome of a compile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "figure-agent.strict-status.v1"


def strict_status_payload(*, strict_requested: bool, detector_failed: bool) -> dict[str, object]:
    """Return the strict outcome without conflating it with render freshness."""
    if not strict_requested:
        state = "not_requested"
    elif detector_failed:
        state = "failed"
    else:
        state = "passed"
    return {
        "schema": SCHEMA,
        "strict_requested": strict_requested,
        "detector_failed": detector_failed,
        "state": state,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--strict-requested", action="store_true")
    parser.add_argument("--detector-failed", action="store_true")
    args = parser.parse_args(argv)

    payload = strict_status_payload(
        strict_requested=args.strict_requested,
        detector_failed=args.detector_failed,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
