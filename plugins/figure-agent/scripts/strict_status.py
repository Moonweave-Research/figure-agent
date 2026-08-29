#!/usr/bin/env python3
"""Write an explicit receipt for the strict-detector outcome of a compile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "figure-agent.strict-status.v1"


def strict_status_payload(
    *,
    strict_requested: bool,
    detector_failed: bool,
    live_assertion_target: bool = True,
) -> dict[str, object]:
    """Return the strict outcome without conflating it with render freshness.

    ``live_assertion_target`` is false when the compile replayed immutable
    execution-repair evidence, where the spec-driven assertions deliberately do
    not gate. Their reports are then clean because nothing was declared, not
    because anything passed, and only this field tells the two apart.
    """
    if not strict_requested:
        state = "not_requested"
    elif detector_failed:
        state = "failed"
    elif not live_assertion_target:
        state = "passed_without_live_assertions"
    else:
        state = "passed"
    return {
        "schema": SCHEMA,
        "strict_requested": strict_requested,
        "detector_failed": detector_failed,
        "live_assertion_target": live_assertion_target,
        "state": state,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--strict-requested", action="store_true")
    parser.add_argument("--detector-failed", action="store_true")
    parser.add_argument("--no-live-assertions", action="store_true")
    args = parser.parse_args(argv)

    payload = strict_status_payload(
        strict_requested=args.strict_requested,
        detector_failed=args.detector_failed,
        live_assertion_target=not args.no_live_assertions,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
