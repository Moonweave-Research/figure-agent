#!/usr/bin/env python3
"""Physics-intent grounding meta-check (report-only WARN).

A figure can drift to wrong physics (fig5 drew attraction where the novelty is
repulsion) when its physics intent — documented in the briefing's "Physics
invariants" section — is NOT wired to a machine-checkable guard. A cohort survey
found several figures (fig2, fig3_trapping, fig4) that DECLARE physics invariants
in prose but have ZERO tex_assertions. This meta-check surfaces them: it is the
deterministic backstop for the agent-reads-docs → authors-assertions loop.

Status per figure:
  - grounded            : declares physics invariants AND has tex_assertions
  - declared_unenforced : declares invariants but no tex_assertions  (WARN — the
                          agent should read §6/§7 and author directional assertions)
  - undeclared          : no Physics-invariants section (general-physics fallback)
  - briefing_missing    : briefing.md is absent, so intent cannot be read at all
                          (WARN — this is a gap, not the benign "undeclared" case)
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

_PHYSICS_HEADER = re.compile(r"^#{1,6}\s.*physics invariant", re.IGNORECASE | re.MULTILINE)


def has_physics_invariants(briefing_text: str) -> bool:
    """True when the briefing has a markdown header naming a Physics-invariants section."""
    return _PHYSICS_HEADER.search(briefing_text) is not None


def has_tex_assertions(spec: dict) -> bool:
    raw = spec.get("tex_assertions")
    return isinstance(raw, list) and len(raw) > 0


def has_semantic_assertions(spec: dict) -> bool:
    raw = spec.get("semantic_assertions")
    return isinstance(raw, list) and len(raw) > 0


def classify_grounding(briefing_text: str, spec: dict) -> str:
    # A figure is enforced by EITHER assertion family: tex_assertions for directional
    # facts (force/bend direction), semantic_assertions for label-relational ones
    # (shallow above deep). Counting only tex_assertions false-WARNs the latter.
    if not has_physics_invariants(briefing_text):
        return "undeclared"
    enforced = has_tex_assertions(spec) or has_semantic_assertions(spec)
    return "grounded" if enforced else "declared_unenforced"


SCHEMA = "figure-agent.physics-grounding.v1"


def grounding_status(figure_dir) -> dict:
    briefing = figure_dir / "briefing.md"
    spec_path = figure_dir / "spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) if spec_path.is_file() else {}
    if not briefing.is_file():
        # A missing briefing is a real gap: physics intent cannot be read, so it
        # must not collapse into the benign "undeclared" (no-invariants) bucket.
        return {"figure": figure_dir.name, "status": "briefing_missing"}
    briefing_text = briefing.read_text(encoding="utf-8")
    return {
        "figure": figure_dir.name,
        "status": classify_grounding(briefing_text, spec or {}),
    }


def grounding_payload(figure: str, status: str) -> dict:
    return {"schema": SCHEMA, "figure": figure, "status": status}


def write_grounding_json(figure: str, status: str, output_path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(grounding_payload(figure, status), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Physics-intent grounding meta-check")
    parser.add_argument("figure_dir", type=Path, help="examples/<name> directory")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--strict", action="store_true", default=False)
    args = parser.parse_args()

    result = grounding_status(args.figure_dir)
    if args.json_output:
        write_grounding_json(result["figure"], result["status"], args.json_output)
    non_benign = {"declared_unenforced", "briefing_missing"}
    if result["status"] == "declared_unenforced":
        print(
            f"WARN physics_grounding: {result['figure']} declares physics invariants but has "
            "no tex_assertions or semantic_assertions (read the briefing §6/§7 and author them)"
        )
    elif result["status"] == "briefing_missing":
        print(
            f"WARN physics_grounding: {result['figure']} has no briefing.md, so physics intent "
            "cannot be read (author a briefing with a Physics-invariants section)"
        )
    else:
        print(f"physics grounding: {result['figure']} = {result['status']}")
    return 1 if (args.strict and result["status"] in non_benign) else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
