from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "semantic_fig1.svg"

REQUIRED_OBJECTS = {
    "polymer_origin",
    "deep_trap_hero",
    "electrical_evidence",
    "trap_model",
    "macroscopic_probe",
    "layout_flow",
}

REQUIRED_ROLES = {
    "visual_anchor",
    "data_visualization",
    "process_flow",
    "annotation",
    "mechanism",
}


def main() -> int:
    try:
        from fig1_scene import build_scene
    except ModuleNotFoundError as exc:
        print(f"missing scene module: {exc}", file=sys.stderr)
        return 1

    scene = build_scene()
    ids = {obj.id for obj in scene.objects}
    roles = {obj.role for obj in scene.objects}

    missing_objects = sorted(REQUIRED_OBJECTS - ids)
    missing_roles = sorted(REQUIRED_ROLES - roles)
    if missing_objects or missing_roles:
        for object_id in missing_objects:
            print(f"missing semantic object: {object_id}", file=sys.stderr)
        for role in missing_roles:
            print(f"missing semantic role: {role}", file=sys.stderr)
        return 1

    assertions = {assertion.id for assertion in scene.assertions}
    required_assertions = {
        "deep_dominates_shallow",
        "hero_is_visual_focus",
        "repulsion_points_away_from_electrode",
        "evidence_trio_is_distinct",
    }
    missing_assertions = sorted(required_assertions - assertions)
    if missing_assertions:
        for assertion_id in missing_assertions:
            print(f"missing semantic assertion: {assertion_id}", file=sys.stderr)
        return 1

    if SVG.exists():
        ET.parse(SVG)
        svg_text = SVG.read_text()
        for token in ["polymer_origin", "deep_trap_hero", "electrical_evidence", "trap_model", "macroscopic_probe"]:
            if token not in svg_text:
                print(f"rendered SVG missing semantic marker: {token}", file=sys.stderr)
                return 1

    print("semantic scene contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
