from __future__ import annotations

from pathlib import Path
from typing import Any

from illustration_backend import load_backend_profile, style_for_slot, validate_scene_tokens


def render_svg(scene: dict[str, Any], profile_path: Path) -> str:
    profile = load_backend_profile(profile_path, backend="svg")
    validate_scene_tokens(scene, profile)
    view_box = " ".join(str(value) for value in profile["canvas"]["view_box"])
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}">']
    for layer in scene["layers"]:
        slot = layer["semantic_id"]
        style = style_for_slot(scene, profile, slot)
        lines.append(f'  <g id="{slot}" data-semantic="true">')
        lines.extend(f"    {line}" for line in _render_layer(slot, layer["objects"], style))
        lines.append("  </g>")
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _render_layer(
    slot: str,
    objects: list[dict[str, Any]],
    style: dict[str, Any],
) -> list[str]:
    attributes = _attributes(style, fill=slot not in {"chain.backbones", "trap.levels"})
    if slot == "chain.backbones":
        return [_svg_curve(item["points"], attributes) for item in objects]
    if slot == "sulfur.regions":
        return [_svg_ellipse(item, attributes) for item in objects]
    if slot in {"sulfur.sites", "trapped.carriers"}:
        return [_svg_circle(item, attributes) for item in objects]
    if slot == "trap.levels":
        return [_svg_trap(item, attributes) for item in objects]
    return []


def _attributes(style: dict[str, Any], *, fill: bool) -> str:
    color = style["color"]
    fill_value = color["fill"] if fill else "none"
    return (
        f'fill="{fill_value}" stroke="{color["stroke"]}" '
        f'stroke-width="{_fmt(style["stroke"])}" stroke-linecap="round" '
        f'stroke-linejoin="round" opacity="{_fmt(style["opacity"])}"'
    )


def _svg_curve(points: list[list[float]], attributes: str) -> str:
    p0, p1, p2, p3 = (_point(point) for point in points)
    return f'<path d="M {p0} C {p1} {p2} {p3}" {attributes}/>'


def _svg_ellipse(item: dict[str, Any], attributes: str) -> str:
    cx, cy = (_fmt(value * 100) for value in item["center"])
    rx, ry = (_fmt(value * 100) for value in item["radius"])
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" {attributes}/>'


def _svg_circle(item: dict[str, Any], attributes: str) -> str:
    cx, cy = (_fmt(value * 100) for value in item["center"])
    radius = _fmt(item["radius"] * 100)
    return f'<circle cx="{cx}" cy="{cy}" r="{radius}" {attributes}/>'


def _svg_trap(item: dict[str, Any], attributes: str) -> str:
    x, y = item["center"]
    half_width = item["width"] / 2
    x1, y1 = _point([x - half_width, y]).split()
    x2, y2 = _point([x + half_width, y]).split()
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" {attributes}/>'


def _point(point: list[float]) -> str:
    return f"{_fmt(point[0] * 100)} {_fmt(point[1] * 100)}"


def _fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"
