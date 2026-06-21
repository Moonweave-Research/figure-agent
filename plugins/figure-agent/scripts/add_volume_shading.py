from __future__ import annotations

import math
import xml.etree.ElementTree as ET

from svg_path_geometry import canonical_polyline

_SVG_NS = "http://www.w3.org/2000/svg"


def _element_bbox(svg: str, target_id: str) -> tuple[float, float, float, float]:
    """Return axis-aligned bbox (x, y, width, height) of the element with id==target_id."""
    root = ET.fromstring(svg)
    for elem in root.iter():
        if elem.get("id") == target_id:
            local = elem.tag.rpartition("}")[2]
            if local == "rect":
                x = float(elem.get("x", 0.0))
                y = float(elem.get("y", 0.0))
                w = float(elem.get("width", 0.0))
                h = float(elem.get("height", 0.0))
                return (x, y, w, h)
            elif local == "circle":
                cx = float(elem.get("cx", 0.0))
                cy = float(elem.get("cy", 0.0))
                r = float(elem.get("r", 0.0))
                return (cx - r, cy - r, 2 * r, 2 * r)
            elif local == "ellipse":
                cx = float(elem.get("cx", 0.0))
                cy = float(elem.get("cy", 0.0))
                rx = float(elem.get("rx", 0.0))
                ry = float(elem.get("ry", 0.0))
                return (cx - rx, cy - ry, 2 * rx, 2 * ry)
            elif local == "path":
                d = elem.get("d", "")
                pts = canonical_polyline(d)
                if not pts:
                    return (0.0, 0.0, 0.0, 0.0)
                xs = [p.real for p in pts]
                ys = [p.imag for p in pts]
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                return (x_min, y_min, x_max - x_min, y_max - y_min)
    raise ValueError(f"target id not found: {target_id}")


def _opacity_for(hero_strength: float) -> float:
    """Map hero_strength in [0,1] to overlay opacity strictly below 0.95."""
    clamped = max(0.0, min(1.0, hero_strength))
    return 0.10 + 0.45 * clamped


def _gradient_vector(light_direction_degrees: float) -> tuple[float, float, float, float]:
    """Return objectBoundingBox linear-gradient endpoints for light from given angle."""
    rad = math.radians(light_direction_degrees)
    dx = math.cos(rad)
    dy = math.sin(rad)
    x1 = round(0.5 - 0.5 * dx, 4)
    y1 = round(0.5 - 0.5 * dy, 4)
    x2 = round(0.5 + 0.5 * dx, 4)
    y2 = round(0.5 + 0.5 * dy, 4)
    return (x1, y1, x2, y2)
