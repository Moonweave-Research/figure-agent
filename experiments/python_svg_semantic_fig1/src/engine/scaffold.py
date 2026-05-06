from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engine.scene import Column, Layout, LayoutBox, Point, Rect


SCAFFOLD_SCHEMA_VERSION = "scaffold_contract_v1"
SUPPORTED_SOURCE_SCHEMA = "fig1_reference_visual_layout_v1"
SCAFFOLD_REFERENCE_AUTHORITY = "style_layout_evidence"
REFERENCE_PROVENANCE_NOTE = (
    "Reference PNG is layout/style evidence for a human-authored scaffold; "
    "it is not ground_truth and is not a pixel-tracing source."
)


@dataclass(frozen=True)
class ScaffoldCanvas:
    width: int
    height: int


@dataclass(frozen=True)
class ScaffoldLocalBox:
    id: str
    local_bounds: Rect
    bounds: Rect


@dataclass(frozen=True)
class ScaffoldPanel:
    id: str
    index: int
    title: str
    role: str
    bounds: Rect
    object_slots: tuple[str, ...]
    local_boxes: tuple[ScaffoldLocalBox, ...]

    def box(self, box_id: str) -> Rect:
        for box in self.local_boxes:
            if box.id == box_id:
                return box.bounds
        raise KeyError(box_id)


@dataclass(frozen=True)
class ScaffoldFlowAnchor:
    id: str
    start_panel_id: str
    end_panel_id: str
    start: Point
    end: Point
    start_side: str
    end_side: str


@dataclass(frozen=True)
class ScaffoldProvenance:
    source: str
    authority: str
    source_authority: str
    note: str


@dataclass(frozen=True)
class ScaffoldContract:
    schema_version: str
    source_schema: str
    layout_kind: str
    canvas: ScaffoldCanvas
    panels: tuple[ScaffoldPanel, ...]
    flow_anchors: tuple[ScaffoldFlowAnchor, ...]
    flow_object_id: str
    composition_rules: dict[str, Any]
    provenance: ScaffoldProvenance

    def panel_by_id(self, panel_id: str) -> ScaffoldPanel:
        for panel in self.panels:
            if panel.id == panel_id:
                return panel
        raise KeyError(panel_id)

    def panel_by_index(self, index: int) -> ScaffoldPanel:
        for panel in self.panels:
            if panel.index == index:
                return panel
        raise KeyError(index)


def load_scaffold_contract(path: str | Path) -> ScaffoldContract:
    raw = _load_json_object(Path(path))
    source_schema = str(raw["schema"])
    if source_schema != SUPPORTED_SOURCE_SCHEMA:
        raise ValueError(f"unsupported scaffold source schema: {source_schema}")

    canvas_raw = raw["canvas"]
    canvas = ScaffoldCanvas(width=int(canvas_raw["width"]), height=int(canvas_raw["height"]))
    panels = tuple(_panel_from_region(region) for region in raw["regions"])
    panels_by_id = {panel.id: panel for panel in panels}
    flow_anchors = tuple(_flow_anchor_from_arrow(arrow, panels_by_id) for arrow in raw["flow_arrows"])

    return ScaffoldContract(
        schema_version=SCAFFOLD_SCHEMA_VERSION,
        source_schema=source_schema,
        layout_kind=str(raw["target"]),
        canvas=canvas,
        panels=panels,
        flow_anchors=flow_anchors,
        flow_object_id="layout_flow",
        composition_rules=dict(raw.get("visual_rules", {})),
        provenance=ScaffoldProvenance(
            source=str(raw["reference_image"]),
            authority=SCAFFOLD_REFERENCE_AUTHORITY,
            source_authority=str(raw["reference_authority"]),
            note=REFERENCE_PROVENANCE_NOTE,
        ),
    )


def columns_from_scaffold(contract: ScaffoldContract) -> tuple[Column, ...]:
    return tuple(
        Column(
            index=panel.index,
            id=panel.id,
            title=panel.title,
            role=panel.role,
            ratio=1.0,
            bounds=panel.bounds,
            object_ids=panel.object_slots,
            local_boxes=tuple(LayoutBox(id=box.id, bounds=box.bounds) for box in panel.local_boxes),
        )
        for panel in contract.panels
    )


def layout_from_scaffold(contract: ScaffoldContract, columns: tuple[Column, ...]) -> Layout:
    return Layout(
        kind=contract.layout_kind,
        ratio=tuple(1.0 for _ in columns),
        columns=columns,
        flow_object_id=contract.flow_object_id,
    )


def _load_json_object(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise ValueError(f"scaffold contract must be a JSON object: {path}")
    return loaded


def _panel_from_region(region: dict[str, Any]) -> ScaffoldPanel:
    bounds = _rect(region["bounds"])
    local_boxes = tuple(
        ScaffoldLocalBox(
            id=box_id,
            local_bounds=_rect(box_bounds),
            bounds=Rect(
                bounds.x + float(box_bounds[0]),
                bounds.y + float(box_bounds[1]),
                float(box_bounds[2]),
                float(box_bounds[3]),
            ),
        )
        for box_id, box_bounds in region.get("local_boxes", {}).items()
    )
    return ScaffoldPanel(
        id=str(region["id"]),
        index=int(region["index"]),
        title=str(region["title"]),
        role=str(region["role"]),
        bounds=bounds,
        object_slots=tuple(str(object_id) for object_id in region["objects"]),
        local_boxes=local_boxes,
    )


def _flow_anchor_from_arrow(arrow: dict[str, Any], panels_by_id: dict[str, ScaffoldPanel]) -> ScaffoldFlowAnchor:
    start_panel_id = str(arrow["start_region"])
    end_panel_id = str(arrow["end_region"])
    start = _point(arrow["start"])
    end = _point(arrow["end"])
    start_panel = panels_by_id[start_panel_id]
    end_panel = panels_by_id[end_panel_id]
    return ScaffoldFlowAnchor(
        id=str(arrow["id"]),
        start_panel_id=start_panel_id,
        end_panel_id=end_panel_id,
        start=start,
        end=end,
        start_side=_nearest_side(start_panel.bounds, start),
        end_side=_nearest_side(end_panel.bounds, end),
    )


def _rect(values: list[float] | tuple[float, ...]) -> Rect:
    return Rect(float(values[0]), float(values[1]), float(values[2]), float(values[3]))


def _point(values: list[float] | tuple[float, ...]) -> Point:
    return Point(values[0], values[1])


def _nearest_side(rect: Rect, point: Point) -> str:
    distances = {
        "left": abs(point.x - rect.x),
        "right": abs(point.x - rect.right),
        "top": abs(point.y - rect.y),
        "bottom": abs(point.y - rect.bottom),
    }
    return min(distances, key=distances.__getitem__)
