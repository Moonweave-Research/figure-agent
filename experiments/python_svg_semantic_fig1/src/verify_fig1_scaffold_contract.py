from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
VISUAL_LAYOUT = ROOT / "visual_layout.yaml"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

EXPECTED_CONTRACT_SCHEMA = "scaffold_contract_v1"
EXPECTED_SOURCE_SCHEMA = "fig1_reference_visual_layout_v1"


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _contains(outer: object, inner: object) -> bool:
    return outer.x <= inner.x and inner.right <= outer.right and outer.y <= inner.y and inner.bottom <= outer.bottom


def _point_inside_canvas(canvas: object, point: object) -> bool:
    return 0 <= point.x <= canvas.width and 0 <= point.y <= canvas.height


def _near_panel_edge(rect: object, point: object, tolerance: float = 24.0) -> bool:
    inside_expanded = (
        rect.x - tolerance <= point.x <= rect.right + tolerance
        and rect.y - tolerance <= point.y <= rect.bottom + tolerance
    )
    near_edge = min(
        abs(point.x - rect.x),
        abs(point.x - rect.right),
        abs(point.y - rect.y),
        abs(point.y - rect.bottom),
    ) <= tolerance
    return inside_expanded and near_edge


def main() -> int:
    try:
        from engine.scaffold import load_scaffold_contract
    except ModuleNotFoundError as exc:
        return _fail(f"missing scaffold contract module: {exc}")

    try:
        from fig1_l1_scene import build_scene
    except ModuleNotFoundError as exc:
        return _fail(f"missing Fig1 scene module: {exc}")

    contract = load_scaffold_contract(VISUAL_LAYOUT)
    scene = build_scene()

    if contract.schema_version != EXPECTED_CONTRACT_SCHEMA:
        return _fail(f"unexpected scaffold contract schema: {contract.schema_version}")
    if contract.source_schema != EXPECTED_SOURCE_SCHEMA:
        return _fail(f"unexpected source layout schema: {contract.source_schema}")

    if (scene.width, scene.height) != (contract.canvas.width, contract.canvas.height):
        return _fail("scene canvas does not match scaffold canvas")
    if scene.layout.kind != contract.layout_kind:
        return _fail(f"scene layout kind does not match scaffold: {scene.layout.kind}")

    panels_by_id = {panel.id: panel for panel in contract.panels}
    if len(panels_by_id) != len(contract.panels):
        return _fail("scaffold panel ids are not unique")
    if {column.id for column in scene.layout.columns} != set(panels_by_id):
        return _fail("scene layout regions do not match scaffold panels")

    scene_object_ids = {obj.id for obj in scene.objects}
    panel_ids_by_index = {panel.index: panel.id for panel in contract.panels}
    hero_region_id = contract.composition_rules.get("hero_region")
    hero_panels = [panel for panel in contract.panels if panel.role == "hero"]
    if len(hero_panels) != 1 or hero_panels[0].id != hero_region_id:
        return _fail("scaffold must declare exactly one hero panel matching composition rules")

    for column in scene.layout.columns:
        panel = panels_by_id[column.id]
        if panel.role not in {"hero", "supporting"}:
            return _fail(f"panel role is invalid: {panel.id}")
        if column.index != panel.index:
            return _fail(f"panel index mismatch: {panel.id}")
        if column.title != panel.title:
            return _fail(f"panel title mismatch: {panel.id}")
        if column.role != panel.role:
            return _fail(f"panel role mismatch: {panel.id}")
        if column.bounds != panel.bounds:
            return _fail(f"panel bounds mismatch: {panel.id}")
        if tuple(column.object_ids) != panel.object_slots:
            return _fail(f"panel object-slot mismatch: {panel.id}")

        column_boxes = {box.id: box.bounds for box in column.local_boxes}
        panel_boxes = {box.id: box.bounds for box in panel.local_boxes}
        if set(column_boxes) != set(panel_boxes):
            return _fail(f"local box ids mismatch: {panel.id}")
        for box_id, box in panel_boxes.items():
            if not _contains(panel.bounds, box):
                return _fail(f"local box escapes parent panel: {panel.id}.{box_id}")
            if column_boxes[box_id] != box:
                return _fail(f"scene local box mismatch: {panel.id}.{box_id}")

        missing = sorted(set(panel.object_slots) - scene_object_ids)
        if missing:
            return _fail(f"panel references missing scene objects: {panel.id}: {', '.join(missing)}")

    for obj in scene.objects:
        if obj.id == scene.layout.flow_object_id:
            continue
        if obj.column not in panel_ids_by_index:
            return _fail(f"scene object has invalid scaffold region index: {obj.id}")
        panel = panels_by_id[panel_ids_by_index[obj.column]]
        if obj.id not in panel.object_slots:
            return _fail(f"scene object is not bound to its scaffold panel slot: {obj.id}")

    flow = scene.object_by_id(scene.layout.flow_object_id)
    if flow.id != contract.flow_object_id:
        return _fail("scene flow object id does not match scaffold")
    if len(flow.payload.arrow_pairs) != len(contract.flow_anchors):
        return _fail("scene flow anchor count does not match scaffold")

    for anchor, arrow_pair in zip(contract.flow_anchors, flow.payload.arrow_pairs, strict=True):
        if anchor.start_panel_id not in panels_by_id:
            return _fail(f"flow anchor has missing start panel: {anchor.id}")
        if anchor.end_panel_id not in panels_by_id:
            return _fail(f"flow anchor has missing end panel: {anchor.id}")
        if arrow_pair != (anchor.start, anchor.end):
            return _fail(f"flow anchor point mismatch: {anchor.id}")
        if anchor.start_side not in {"left", "right", "top", "bottom"}:
            return _fail(f"flow anchor start side is invalid: {anchor.id}")
        if anchor.end_side not in {"left", "right", "top", "bottom"}:
            return _fail(f"flow anchor end side is invalid: {anchor.id}")
        if not _point_inside_canvas(contract.canvas, anchor.start):
            return _fail(f"flow anchor start is outside the scaffold canvas: {anchor.id}")
        if not _point_inside_canvas(contract.canvas, anchor.end):
            return _fail(f"flow anchor end is outside the scaffold canvas: {anchor.id}")
        if not _near_panel_edge(panels_by_id[anchor.start_panel_id].bounds, anchor.start):
            return _fail(f"flow anchor start is not near its panel edge: {anchor.id}")
        if not _near_panel_edge(panels_by_id[anchor.end_panel_id].bounds, anchor.end):
            return _fail(f"flow anchor end is not near its panel edge: {anchor.id}")

    if contract.provenance.authority == "ground_truth":
        return _fail("scaffold provenance must not mark the reference as ground_truth")
    if scene.reference.authority == "ground_truth":
        return _fail("scene reference must not mark the reference as ground_truth")
    if contract.provenance.authority != "style_layout_evidence":
        return _fail(f"unexpected scaffold provenance authority: {contract.provenance.authority}")
    if "layout/style evidence" not in contract.provenance.note:
        return _fail("scaffold provenance note must preserve layout/style evidence wording")

    print("fig1 scaffold contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
