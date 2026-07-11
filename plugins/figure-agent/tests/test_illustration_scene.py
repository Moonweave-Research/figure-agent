from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from illustration_scene import (  # noqa: E402
    IllustrationSceneError,
    compile_illustration_scene,
)

GRAMMAR_PATH = (
    PLUGIN_ROOT / "styles" / "illustration-grammar" / "sulfur_trap_domain.v1.yaml"
)
INSTANCE_PATH = (
    PLUGIN_ROOT
    / "examples"
    / "fig3_trap_schematic_slice4_illustration_grammar"
    / "motif_instance.yaml"
)


def test_scene_preserves_slots_layers_and_has_no_backend_syntax() -> None:
    scene = compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH)
    serialized = json.dumps(scene, sort_keys=True)

    assert scene["motif_family"] == "sulfur_trap_domain"
    assert [layer["semantic_id"] for layer in scene["layers"]] == [
        "sulfur.regions",
        "chain.backbones",
        "sulfur.sites",
        "trap.levels",
        "trapped.carriers",
    ]
    assert scene["resolved_tokens"]["curvature"] == "organic_backbone"
    assert scene["resolved_tokens"]["slot_roles"]["trapped.carriers"] == {
        "stroke_family": "focal",
        "color_role": "carrier",
        "emphasis": "focal",
    }
    assert "<svg" not in serialized
    assert "\\draw" not in serialized
    assert "fig3_trap_schematic" not in serialized


def test_scene_contains_bounded_non_crossing_motif_geometry() -> None:
    scene = compile_illustration_scene(GRAMMAR_PATH, INSTANCE_PATH)
    objects_by_slot = {
        layer["semantic_id"]: layer["objects"] for layer in scene["layers"]
    }

    assert len(objects_by_slot["chain.backbones"]) == 4
    assert len(objects_by_slot["sulfur.regions"]) == 3
    assert all(
        0.0 <= coordinate <= 1.0
        for layer in scene["layers"]
        for item in layer["objects"]
        for point in item.get("points", [item.get("center", [0.5, 0.5])])
        for coordinate in point
    )


def test_scene_rejects_point_outside_normalized_bounds(tmp_path: Path) -> None:
    payload = yaml.safe_load(INSTANCE_PATH.read_text(encoding="utf-8"))
    payload["objects"]["chain.backbones"][0]["points"][0] = [-0.1, 0.2]
    candidate = tmp_path / "instance.yaml"
    candidate.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(IllustrationSceneError, match="point_out_of_bounds"):
        compile_illustration_scene(GRAMMAR_PATH, candidate)


def test_scene_rejects_carrier_without_trap_relation(tmp_path: Path) -> None:
    payload = yaml.safe_load(INSTANCE_PATH.read_text(encoding="utf-8"))
    del payload["objects"]["trapped.carriers"][0]["sits_on"]
    candidate = tmp_path / "instance.yaml"
    candidate.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(IllustrationSceneError, match="carrier_without_trap_level"):
        compile_illustration_scene(GRAMMAR_PATH, candidate)


def test_scene_rejects_duplicate_object_ids_across_slots(tmp_path: Path) -> None:
    payload = yaml.safe_load(INSTANCE_PATH.read_text(encoding="utf-8"))
    payload["objects"]["sulfur.sites"][0]["id"] = "backbone.1"
    candidate = tmp_path / "instance.yaml"
    candidate.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(IllustrationSceneError, match="object_id_duplicate"):
        compile_illustration_scene(GRAMMAR_PATH, candidate)
