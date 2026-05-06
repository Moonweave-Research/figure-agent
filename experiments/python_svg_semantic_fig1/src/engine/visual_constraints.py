from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from engine.scene import Rect, Scene


_FLOAT_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")


@dataclass(frozen=True)
class BBox:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    def expanded(self, margin: float) -> BBox:
        return BBox(self.left - margin, self.top - margin, self.right + margin, self.bottom + margin)

    def union(self, other: BBox) -> BBox:
        return BBox(
            min(self.left, other.left),
            min(self.top, other.top),
            max(self.right, other.right),
            max(self.bottom, other.bottom),
        )


def semantic_bbox_violations(scene: Scene, svg_path: str | Path, *, margin: float = 8.0) -> list[str]:
    bboxes = semantic_group_bboxes(svg_path)
    violations: list[str] = []
    for obj in scene.objects:
        if obj.column <= 0 or obj.id not in bboxes:
            continue
        bounds = scene.layout.columns[obj.column - 1].bounds
        allowed = _bbox_from_rect(bounds).expanded(margin)
        found = bboxes[obj.id]
        if not _contains(allowed, found):
            violations.append(
                "{} overflows {}: bbox=({:.1f},{:.1f},{:.1f},{:.1f}) allowed=({:.1f},{:.1f},{:.1f},{:.1f})".format(
                    obj.id,
                    scene.layout.columns[obj.column - 1].id,
                    found.left,
                    found.top,
                    found.right,
                    found.bottom,
                    allowed.left,
                    allowed.top,
                    allowed.right,
                    allowed.bottom,
                )
            )
    violations.extend(_specific_scene_violations(scene, bboxes, margin=margin))
    return violations


def semantic_group_bboxes(svg_path: str | Path) -> dict[str, BBox]:
    root = ET.parse(svg_path).getroot()
    bboxes: dict[str, BBox] = {}
    for group in root.iter():
        semantic_id = group.attrib.get("data-semantic-id")
        if not semantic_id:
            continue
        children = [bbox for bbox in _element_bboxes(group) if bbox is not None]
        if children:
            merged = children[0]
            for bbox in children[1:]:
                merged = merged.union(bbox)
            bboxes[semantic_id] = merged
    return bboxes


def _element_bboxes(parent: ET.Element) -> Iterable[BBox | None]:
    for element in list(parent):
        if element.attrib.get("data-semantic-id"):
            continue
        bbox = _element_bbox(element)
        if bbox is not None:
            yield bbox
        yield from _element_bboxes(element)


def _element_bbox(element: ET.Element) -> BBox | None:
    tag = _local_name(element.tag)
    transform_x, transform_y = _translate(element.attrib.get("transform", ""))
    if tag == "rect":
        return _translated(
            BBox(
                _float(element, "x"),
                _float(element, "y"),
                _float(element, "x") + _float(element, "width"),
                _float(element, "y") + _float(element, "height"),
            ),
            transform_x,
            transform_y,
        )
    if tag == "circle":
        cx = _float(element, "cx")
        cy = _float(element, "cy")
        r = _float(element, "r")
        return _translated(BBox(cx - r, cy - r, cx + r, cy + r), transform_x, transform_y)
    if tag == "line":
        x1 = _float(element, "x1")
        y1 = _float(element, "y1")
        x2 = _float(element, "x2")
        y2 = _float(element, "y2")
        pad = _float(element, "stroke-width", default=1.0) / 2
        return _translated(BBox(min(x1, x2) - pad, min(y1, y2) - pad, max(x1, x2) + pad, max(y1, y2) + pad), transform_x, transform_y)
    if tag == "path":
        values = [float(value) for value in _FLOAT_RE.findall(element.attrib.get("d", ""))]
        if len(values) < 2:
            return None
        xs = values[0::2]
        ys = values[1::2]
        pad = _float(element, "stroke-width", default=1.0) / 2
        return _translated(BBox(min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad), transform_x, transform_y)
    if tag == "polygon":
        values = [float(value) for value in _FLOAT_RE.findall(element.attrib.get("points", ""))]
        if len(values) < 2:
            return None
        xs = values[0::2]
        ys = values[1::2]
        return _translated(BBox(min(xs), min(ys), max(xs), max(ys)), transform_x, transform_y)
    if tag == "text":
        x = _float(element, "x")
        y = _float(element, "y")
        size = _float(element, "font-size", default=12.0)
        text_value = "".join(element.itertext())
        width = max(size * 0.6, len(text_value) * size * 0.55)
        anchor = element.attrib.get("text-anchor", "start")
        left = x
        if anchor == "middle":
            left = x - width / 2
        elif anchor == "end":
            left = x - width
        return _translated(BBox(left, y - size * 0.9, left + width, y + size * 0.25), transform_x, transform_y)
    return None


def _specific_scene_violations(scene: Scene, bboxes: dict[str, BBox], *, margin: float) -> list[str]:
    violations: list[str] = []
    hero = next(column for column in scene.layout.columns if column.role == "hero")
    band_area = hero.box("band_area")
    dos_area = hero.box("dos_area")
    if "dos_lobes" in bboxes and not _contains(_bbox_from_rect(dos_area).expanded(36), bboxes["dos_lobes"]):
        violations.append("dos_lobes escapes hero dos_area")

    band = scene.object_by_kind("BandDiagram").payload
    traps = scene.object_by_kind("TrapLevelSet").payload
    band_rect = hero.box("band_area")
    lumo_y = band_rect.y + band.lumo.y * band_rect.height
    homo_y = band_rect.y + band.homo.y * band_rect.height
    trap_ys = [band_rect.y + position * band_rect.height for position in (*traps.shallow_positions, *traps.deep_positions)]
    if any(abs(y - lumo_y) < 18 or abs(y - homo_y) < 18 for y in trap_ys):
        violations.append("trap level stack is too close to HOMO/LUMO labels")
    return violations


def _bbox_from_rect(rect: Rect) -> BBox:
    return BBox(rect.x, rect.y, rect.right, rect.bottom)


def _contains(outer: BBox, inner: BBox) -> bool:
    return outer.left <= inner.left and outer.top <= inner.top and outer.right >= inner.right and outer.bottom >= inner.bottom


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _float(element: ET.Element, name: str, *, default: float = 0.0) -> float:
    value = element.attrib.get(name)
    if value is None:
        return default
    return float(value)


def _translate(transform: str) -> tuple[float, float]:
    match = re.search(r"translate\(([-+0-9.eE]+)[ ,]+([-+0-9.eE]+)\)", transform)
    if not match:
        return 0.0, 0.0
    return float(match.group(1)), float(match.group(2))


def _translated(bbox: BBox, dx: float, dy: float) -> BBox:
    return BBox(bbox.left + dx, bbox.top + dy, bbox.right + dx, bbox.bottom + dy)
