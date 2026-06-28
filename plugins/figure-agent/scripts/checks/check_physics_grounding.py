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


def classify_grounding(briefing_text: str, spec: dict) -> str:
    if not has_physics_invariants(briefing_text):
        return "undeclared"
    return "grounded" if has_tex_assertions(spec) else "declared_unenforced"


SCHEMA = "figure-agent.physics-grounding.v1"


def grounding_status(figure_dir) -> dict:
    briefing = figure_dir / "briefing.md"
    briefing_text = briefing.read_text(encoding="utf-8") if briefing.is_file() else ""
    spec_path = figure_dir / "spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) if spec_path.is_file() else {}
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
    if result["status"] == "declared_unenforced":
        print(
            f"WARN physics_grounding: {result['figure']} declares physics invariants "
            "but has no tex_assertions (read the briefing §6/§7 and author them)"
        )
    else:
        print(f"physics grounding: {result['figure']} = {result['status']}")
    return 1 if (args.strict and result["status"] == "declared_unenforced") else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
