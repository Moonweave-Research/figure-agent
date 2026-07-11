from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from illustration_grammar import load_illustration_grammar

_INSTANCE_SCHEMA = "figure-agent.illustration-instance.v1"
_INSTANCE_FIELDS = {"schema", "motif_family", "coordinate_system", "objects"}


class IllustrationSceneError(ValueError):
    """Raised when a motif instance cannot compile to a neutral scene."""


def compile_illustration_scene(
    grammar_path: Path,
    instance_path: Path,
) -> dict[str, Any]:
    grammar = load_illustration_grammar(grammar_path)
    instance = yaml.safe_load(instance_path.read_text(encoding="utf-8"))
    if not isinstance(instance, dict) or set(instance) != _INSTANCE_FIELDS:
        raise IllustrationSceneError("instance_fields_invalid")
    if instance["schema"] != _INSTANCE_SCHEMA:
        raise IllustrationSceneError("instance_schema_unsupported")
    if instance["motif_family"] != grammar["motif_family"]:
        raise IllustrationSceneError("motif_family_mismatch")
    if instance["coordinate_system"] != "normalized_unit_square":
        raise IllustrationSceneError("coordinate_system_unsupported")

    objects = instance["objects"]
    if not isinstance(objects, dict) or set(objects) != set(grammar["semantic_slots"]):
        raise IllustrationSceneError("semantic_slots_invalid")
    _validate_geometry(objects)
    relations = _compile_relations(objects)

    role_bindings = grammar["role_bindings"]
    resolved_tokens = {
        **role_bindings["global"],
        "slot_roles": role_bindings["slots"],
        "optical_rules": grammar["optical_rules"],
    }
    return {
        "schema": "figure-agent.illustration-scene.v1",
        "motif_family": grammar["motif_family"],
        "coordinate_system": instance["coordinate_system"],
        "semantic_ids": list(grammar["layer_order"]),
        "relations": relations,
        "layers": [
            {"semantic_id": slot, "objects": objects[slot]}
            for slot in grammar["layer_order"]
        ],
        "resolved_tokens": resolved_tokens,
    }


def _validate_geometry(objects: dict[str, Any]) -> None:
    object_ids: set[str] = set()
    for slot, items in objects.items():
        if not isinstance(items, list) or not items:
            raise IllustrationSceneError(f"objects_invalid: {slot}")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise IllustrationSceneError(f"object_invalid: {slot}")
            if item["id"] in object_ids:
                raise IllustrationSceneError(f"object_id_duplicate: {item['id']}")
            object_ids.add(item["id"])
            for point in _object_points(item):
                if len(point) != 2 or not all(
                    isinstance(value, int | float) and 0.0 <= value <= 1.0
                    for value in point
                ):
                    raise IllustrationSceneError("point_out_of_bounds")

    backbones = objects["chain.backbones"]
    if len(backbones) != 4 or any(len(item.get("points", [])) < 4 for item in backbones):
        raise IllustrationSceneError("backbone_geometry_invalid")
    if _backbones_cross(backbones):
        raise IllustrationSceneError("backbone_crossing")
    if len(objects["sulfur.regions"]) != 3:
        raise IllustrationSceneError("sulfur_regions_invalid")


def _object_points(item: dict[str, Any]) -> list[list[float]]:
    if "points" in item:
        return item["points"]
    if "center" in item:
        return [item["center"]]
    raise IllustrationSceneError("object_geometry_missing")


def _backbones_cross(backbones: list[dict[str, Any]]) -> bool:
    segment_sets = [
        list(zip(item["points"], item["points"][1:], strict=False)) for item in backbones
    ]
    return any(
        _segments_intersect(a_start, a_end, b_start, b_end)
        for index, first in enumerate(segment_sets)
        for second in segment_sets[index + 1 :]
        for a_start, a_end in first
        for b_start, b_end in second
    )


def _segments_intersect(
    a_start: list[float],
    a_end: list[float],
    b_start: list[float],
    b_end: list[float],
) -> bool:
    def orientation(p: list[float], q: list[float], r: list[float]) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    return (
        orientation(a_start, a_end, b_start) * orientation(a_start, a_end, b_end) < 0
        and orientation(b_start, b_end, a_start) * orientation(b_start, b_end, a_end) < 0
    )


def _compile_relations(objects: dict[str, Any]) -> list[dict[str, str]]:
    ids = {
        slot: {item["id"] for item in items}
        for slot, items in objects.items()
    }
    relations: list[dict[str, str]] = []
    relation_fields = {
        "sulfur.sites": (("attached_to", "chain.backbones"), ("located_in", "sulfur.regions")),
        "trap.levels": (("co_located_with", "sulfur.regions"),),
        "trapped.carriers": (("sits_on", "trap.levels"),),
    }
    for slot, requirements in relation_fields.items():
        for item in objects[slot]:
            for predicate, target_slot in requirements:
                target = item.get(predicate)
                if target is None and slot == "trapped.carriers":
                    raise IllustrationSceneError("carrier_without_trap_level")
                if target not in ids[target_slot]:
                    raise IllustrationSceneError(f"relation_target_invalid: {predicate}")
                relations.append(
                    {"subject": item["id"], "predicate": predicate, "object": target}
                )
    return relations
