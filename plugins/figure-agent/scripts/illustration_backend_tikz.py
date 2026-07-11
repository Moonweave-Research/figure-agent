from __future__ import annotations

from pathlib import Path
from typing import Any

from illustration_backend import load_backend_profile, style_for_slot, validate_scene_tokens


def render_tikz(scene: dict[str, Any], profile_path: Path) -> str:
    profile = load_backend_profile(profile_path, backend="tikz")
    validate_scene_tokens(scene, profile)
    scale = profile["canvas"]["scale_cm"]
    lines = ["% figure-agent illustration grammar: sulfur_trap_domain"]
    for layer in scene["layers"]:
        slot = layer["semantic_id"]
        style = style_for_slot(scene, profile, slot)
        lines.append(f"% figure-agent:start {slot}")
        lines.extend(_render_layer(slot, layer["objects"], style, scale))
        lines.append(f"% figure-agent:end {slot}")
    return "\n".join(lines) + "\n"


def _render_layer(
    slot: str,
    objects: list[dict[str, Any]],
    style: dict[str, Any],
    scale: float,
) -> list[str]:
    options = _options(style)
    if slot == "chain.backbones":
        return [_tikz_curve(item["points"], options, scale) for item in objects]
    if slot == "sulfur.regions":
        return [_tikz_ellipse(item, options, scale) for item in objects]
    if slot in {"sulfur.sites", "trapped.carriers"}:
        return [_tikz_circle(item, options, scale) for item in objects]
    if slot == "trap.levels":
        return [_tikz_trap(item, options, scale) for item in objects]
    return []


def _options(style: dict[str, Any]) -> str:
    color = style["color"]
    return ", ".join(
        [
            f"draw={color['stroke']}",
            f"fill={color['fill']}",
            f"line width={style['stroke']}",
            "line cap=round",
            "line join=round",
            f"opacity={_fmt(style['opacity'])}",
        ]
    )


def _tikz_curve(points: list[list[float]], options: str, scale: float) -> str:
    p0, p1, p2, p3 = (_point(point, scale) for point in points)
    return f"\\draw[{options}] {p0} .. controls {p1} and {p2} .. {p3};"


def _tikz_ellipse(item: dict[str, Any], options: str, scale: float) -> str:
    center = _point(item["center"], scale)
    rx, ry = (_fmt(value * scale) for value in item["radius"])
    return f"\\filldraw[{options}] {center} ellipse [x radius={rx}, y radius={ry}];"


def _tikz_circle(item: dict[str, Any], options: str, scale: float) -> str:
    center = _point(item["center"], scale)
    radius = _fmt(item["radius"] * scale)
    return f"\\filldraw[{options}] {center} circle [radius={radius}];"


def _tikz_trap(item: dict[str, Any], options: str, scale: float) -> str:
    x, y = item["center"]
    half_width = item["width"] / 2
    start = _point([x - half_width, y], scale)
    end = _point([x + half_width, y], scale)
    return f"\\draw[{options}] {start} -- {end};"


def _point(point: list[float], scale: float) -> str:
    return f"({_fmt(point[0] * scale)}, {_fmt((1.0 - point[1]) * scale)})"


def _fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"
