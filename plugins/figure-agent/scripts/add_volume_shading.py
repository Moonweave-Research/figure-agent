from __future__ import annotations

import math
import xml.etree.ElementTree as ET

from svg_path_geometry import canonical_polyline

SVG_NS = "http://www.w3.org/2000/svg"


def _svg(tag: str) -> str:
    """Namespaced SVG tag for ET element construction/lookup."""
    return f"{{{SVG_NS}}}{tag}"


def _element_bbox(svg: str, target_id: str) -> tuple[float, float, float, float]:
    """Return axis-aligned bbox (x, y, width, height) of the element with id==target_id."""
    root = ET.fromstring(svg)
    for elem in root.iter():
        if elem.get("id") == target_id:
            local = elem.tag.rpartition("}")[2]
            if local == "rect":
                x = float(elem.get("x", "0"))
                y = float(elem.get("y", "0"))
                w = float(elem.get("width", "0"))
                h = float(elem.get("height", "0"))
                return (x, y, w, h)
            elif local == "circle":
                cx = float(elem.get("cx", "0"))
                cy = float(elem.get("cy", "0"))
                r = float(elem.get("r", "0"))
                return (cx - r, cy - r, 2 * r, 2 * r)
            elif local == "ellipse":
                cx = float(elem.get("cx", "0"))
                cy = float(elem.get("cy", "0"))
                rx = float(elem.get("rx", "0"))
                ry = float(elem.get("ry", "0"))
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
            raise ValueError(f"unsupported shape for bbox: {local} id={target_id}")
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


def add_volume_shading(
    svg: str,
    target_id: str,
    *,
    light_direction: float | None,
    hero_strength: float | None,
) -> str:
    """Add a filter-free volume-shading overlay over the target object.

    Judgment-bearing (spec §4): both knobs are REQUIRED — never silently defaulted.
    Emits a filter-free linear gradient in <defs> plus a translucent hand:* overlay
    inset within the target's interior, mutating no truth path and not recoloring
    the target itself (H9).
    """
    if light_direction is None or hero_strength is None:
        raise ValueError("add_volume_shading requires light_direction and hero_strength")

    bbox_x, bbox_y, width, height = _element_bbox(svg, target_id)

    ET.register_namespace("", SVG_NS)
    root = ET.fromstring(svg)

    parent_of = {child: parent for parent in root.iter() for child in parent}
    target = next((elem for elem in root.iter() if elem.get("id") == target_id), None)
    if target is None:  # pragma: no cover - _element_bbox already raised above
        raise ValueError(f"target id not found: {target_id}")

    defs = root.find(_svg("defs"))
    if defs is None:
        defs = ET.Element(_svg("defs"))
        root.insert(0, defs)

    # Idempotent: a repeat call on the same target must not emit a duplicate
    # gradient id (duplicate ids are invalid SVG).
    gradient_id = f"hand:vshade-{target_id}"
    if defs.find(f'{_svg("linearGradient")}[@id="{gradient_id}"]') is None:
        x1, y1, x2, y2 = _gradient_vector(light_direction)
        gradient = ET.SubElement(
            defs,
            _svg("linearGradient"),
            {"id": gradient_id, "x1": str(x1), "y1": str(y1), "x2": str(x2), "y2": str(y2)},
        )
        # Filter-free Lambert ramp: lit highlight -> shadow.
        ET.SubElement(gradient, _svg("stop"), {"offset": "0", "stop-color": "#ffffff"})
        ET.SubElement(gradient, _svg("stop"), {"offset": "1", "stop-color": "#000000"})

    # Inset the overlay so it covers the INTERIOR fill, not the truth outline stroke.
    # Load-bearing: keeping the translucent overlay off the truth path's polyline
    # points lets the render-ship gate still see the outline's declared colour in
    # >=50% of on-path samples (COLOR_DELTA tolerance).
    # For sub-~2px targets, width-2*inset clamps to 0 -> a zero-size (no-op) overlay:
    # an intentional silent floor for degenerate tiny objects, not a crash.
    inset = max(1.0, 0.08 * min(width, height))
    overlay_w = max(0.0, width - 2 * inset)
    overlay_h = max(0.0, height - 2 * inset)
    overlay = ET.Element(
        _svg("rect"),
        {
            "id": f"hand:vshade-overlay-{target_id}",
            "data-truth-bearing": "false",
            "x": str(bbox_x + inset),
            "y": str(bbox_y + inset),
            "width": str(overlay_w),
            "height": str(overlay_h),
            "fill": f"url(#{gradient_id})",
            "opacity": str(_opacity_for(hero_strength)),
        },
    )

    parent = parent_of.get(target, root)
    parent.insert(list(parent).index(target) + 1, overlay)

    return ET.tostring(root, encoding="unicode")
