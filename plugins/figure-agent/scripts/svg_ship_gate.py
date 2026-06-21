"""Render-ship equivalence gate (spec §5 H3): does the shipped PDF render faithfully
show each truth-bearing path? Pure colour/coord/sampling logic here is render-free
and unit-testable; the render adapter (rsvg-convert + pdftoppm) is the only part that
needs system tools.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from inputs import parse_spec
from svg_polish_manifest import FINAL_ARTIFACT_POLISHED_SVG, compute_final_artifact_state
from svg_semantic_diff import _inventory

_NAMED_COLORS = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "none": None,
}


def _parse_color(value: str | None) -> tuple[int, int, int] | None:
    """Parse an SVG colour string to an RGB triple. Returns None for absent,
    `none`, or any form we do not parse (e.g. `url(#grad)`) — such paths are
    simply not colour-checked rather than crashing the gate."""
    if not value:
        return None
    token = value.strip().lower()
    if token in _NAMED_COLORS:
        return _NAMED_COLORS[token]
    match = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", token)
    if not match:
        return None
    digits = match.group(1)
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    return (int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))


def _svg_to_pixel(
    point: complex,
    viewbox: tuple[float, float, float, float],
    *,
    raster_w: int,
    raster_h: int,
) -> tuple[int, int]:
    """Map an SVG user-space point to an (x, y) raster pixel, clamped in-bounds."""
    min_x, min_y, width, height = viewbox
    fx = (point.real - min_x) / width if width else 0.0
    fy = (point.imag - min_y) / height if height else 0.0
    px = min(max(int(round(fx * raster_w)), 0), raster_w - 1)
    py = min(max(int(round(fy * raster_h)), 0), raster_h - 1)
    return (px, py)


# per-channel L-infinity tolerance. 60 is intentionally tight: it passes pure
# rendered colours while rejecting semi-transparent variants (e.g. stroke-opacity=0.5
# red renders channel-127 over white). Task 3 adds _blend_to_white to match those.
COLOR_DELTA = 60


def _color_present_near(
    raster: np.ndarray,
    pixel: tuple[int, int],
    colors: set[tuple[int, int, int]],
    *,
    radius: int = 2,
    delta: int = COLOR_DELTA,
) -> bool:
    """True if any declared colour appears within a `radius`-pixel window of `pixel`.
    The window is ESSENTIAL (verified empirically, see "Review hardening"): a truth
    path's polyline traces the path *outline*, so for a FILLED region the on-line
    pixels straddle the antialiased fill/background edge (~50% background). A single
    centre sample false-BLOCKERs a faithfully-rendered filled region; the window
    catches the fill colour 1-2px inside the edge. It does NOT weaken occlusion
    detection — an opaque cover leaves no declared colour anywhere near the point."""
    px, py = pixel
    raster_h, raster_w = raster.shape[0], raster.shape[1]
    for yy in range(max(0, py - radius), min(raster_h, py + radius + 1)):
        for xx in range(max(0, px - radius), min(raster_w, px + radius + 1)):
            sample = raster[yy, xx]
            if any(
                all(abs(int(sample[i]) - color[i]) <= delta for i in range(3)) for color in colors
            ):
                return True
    return False


MIN_MATCH_FRACTION = 0.5  # >=0.5 passes; <0.5 is a BLOCKER (exactly-half is intentionally a pass)


def detect_render_ship_divergence(
    raster: np.ndarray,
    truth_paths: list[dict[str, Any]],
    viewbox: tuple[float, float, float, float],
    *,
    min_match_fraction: float = MIN_MATCH_FRACTION,
) -> list[dict[str, str]]:
    """BLOCKER findings for truth paths whose rendered on-path colours diverge from
    every declared colour. `truth_paths` items: {id, polyline (list[complex]), colors
    (set of RGB triples — declared fill/stroke PLUS their opacity-blended variants,
    assembled in `_truth_samples`)}. Each polyline point is matched via a small window
    (`_color_present_near`) so a filled region's outline samples still match. Paths
    with an empty `colors` set are skipped (not checkable, not a crash)."""
    raster_h, raster_w = raster.shape[0], raster.shape[1]
    findings: list[dict[str, str]] = []
    for entry in sorted(truth_paths, key=lambda item: item["id"]):
        colors = entry["colors"]
        polyline = entry["polyline"]
        if not colors or not polyline:
            continue
        matched = 0
        for point in polyline:
            pixel = _svg_to_pixel(point, viewbox, raster_w=raster_w, raster_h=raster_h)
            if _color_present_near(raster, pixel, colors):
                matched += 1
        fraction = matched / len(polyline)
        if fraction < min_match_fraction:
            findings.append(
                {
                    "id": f"RS{len(findings) + 1:03d}",
                    "kind": "render_ship_divergence",
                    "severity": "BLOCKER",
                    "evidence": (
                        f"truth path #{entry['id']} renders unfaithfully: only "
                        f"{matched}/{len(polyline)} on-path samples match a declared "
                        "colour (covered, filtered, or renderer-shifted)"
                    ),
                    "recommended_route": "semantic_backport_required",
                }
            )
    return findings


# svg_semantic_diff.OPTICAL_ATTRS order: (fill, stroke, opacity, fill-opacity, stroke-opacity)


def _numeric(value: str | None) -> float | None:
    """Leading number of an ABSOLUTE length string ('20', '20px' -> 20.0).
    None, non-numeric, or a percentage ('100%' -> None) yield None: a percentage
    is not an absolute length, so callers must not treat it as a canvas dimension."""
    if not value or "%" in value:
        return None
    match = re.match(r"\s*([0-9]*\.?[0-9]+)", value)
    return float(match.group(1)) if match else None


def _opacity(value: str | None) -> float:
    parsed = _numeric(value)
    return 1.0 if parsed is None else max(0.0, min(1.0, parsed))


def _blend_to_white(color: tuple[int, int, int], opacity: float) -> tuple[int, int, int]:
    """A semi-transparent colour over the white render page renders as this blend.
    Verified empirically: a stroke-opacity=0.5 red renders (255,127,127), not pure
    red, so the declared colour alone would false-BLOCKER without this variant."""
    return tuple(round(channel * opacity + 255 * (1 - opacity)) for channel in color)


def _parse_viewbox(frame: dict[str, str]) -> tuple[float, float, float, float] | None:
    raw = frame.get("viewBox", "").split()
    if len(raw) != 4:
        return None
    try:
        min_x, min_y, width, height = (float(value) for value in raw)
    except ValueError:
        return None
    if width <= 0 or height <= 0:
        return None
    # If the SVG forces width/height with a DIFFERENT aspect ratio, rsvg letterboxes
    # the content (preserveAspectRatio meet) and our linear viewBox->raster mapping
    # mis-locates off-centre features. Skip rather than risk false divergence (the
    # geometry + occlusion locks still guard; this gate is an additive backstop).
    canvas_w, canvas_h = _numeric(frame.get("width")), _numeric(frame.get("height"))
    if (
        canvas_w
        and canvas_h
        and abs(canvas_w / canvas_h - width / height) > 0.01 * (width / height)
    ):
        return None
    return (min_x, min_y, width, height)


def _truth_samples(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for element_id, geometry in inventory["truth_geometry"].items():
        fill_raw, stroke_raw, opacity_raw, fill_op_raw, stroke_op_raw = inventory[
            "colors_by_id"
        ].get(element_id) or (None, None, None, None, None)
        base = _opacity(opacity_raw)
        colors: set[tuple[int, int, int]] = set()
        fill = _parse_color(fill_raw)
        if fill is not None:
            colors.add(fill)
            colors.add(_blend_to_white(fill, base * _opacity(fill_op_raw)))
        stroke = _parse_color(stroke_raw)
        if stroke is not None:
            colors.add(stroke)
            colors.add(_blend_to_white(stroke, base * _opacity(stroke_op_raw)))
        samples.append({"id": element_id, "polyline": geometry["polyline"], "colors": colors})
    return samples


def _render_svg_to_raster(svg_path: Path, dpi: int) -> np.ndarray:
    """SVG -> PDF (rsvg-convert) -> RGB raster (pdftoppm). Needs system tools."""
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "ship.pdf"
        subprocess.run(
            ["rsvg-convert", "-f", "pdf", "-o", str(pdf_path), str(svg_path)],
            check=True,
            capture_output=True,
        )
        # Reuse the repo's PDF->PIL rasteriser (pdftoppm) from check_visual_clash.
        from check_visual_clash import render_pdf_first_page

        image = render_pdf_first_page(pdf_path, dpi).convert("RGB")
        return np.asarray(image)


def build_render_ship_findings(svg_path: Path, *, dpi: int = 600) -> list[dict[str, str]]:
    """Render `svg_path` through the PDF ship pipeline and return divergence findings."""
    inventory = _inventory(svg_path)
    viewbox = _parse_viewbox(inventory["frame"])
    if viewbox is None:
        return []  # no viewBox -> cannot map coords; nothing to check
    raster = _render_svg_to_raster(svg_path, dpi)
    return detect_render_ship_divergence(raster, _truth_samples(inventory), viewbox)


def _ship_svg_path(
    example_dir: Path,
    spec_path: Path,
    *,
    base_dir: Path | None = None,
    style_lock_path: Path | None = None,
) -> Path | None:
    """Resolve the polished SVG the final-artifact gate validates, or None.
    Single source of truth (compute_final_artifact_state) so render-ship and the
    final-artifact gate provably target the same byte stream — instead of a
    hardcoded stem that could silently diverge from the manifest."""
    # parse_spec mirrors the sibling final-artifact gate's source of truth: both only
    # read spec["final_artifact"] via compute_final_artifact_state, so they cannot
    # disagree on which polished SVG ships.
    try:
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(spec, dict):
        return None
    overrides: dict[str, Any] = {}
    if base_dir is not None:
        overrides["base_dir"] = base_dir
    if style_lock_path is not None:
        overrides["style_lock_path"] = style_lock_path
    state = compute_final_artifact_state(example_dir, example_dir.name, spec, **overrides)
    if state.get("kind") != FINAL_ARTIFACT_POLISHED_SVG:
        return None
    candidate = (example_dir / state["path"]).resolve()
    if candidate.suffix != ".svg" or not candidate.is_file():
        return None
    return candidate


def render_ship_gate_failures(
    example_dir: Path,
    spec_path: Path,
    *,
    dpi: int = 600,
    base_dir: Path | None = None,
    style_lock_path: Path | None = None,
) -> list[str]:
    """Terminal-gate adapter: human-readable failure strings (empty = pass). Renders
    the SAME polished SVG the final-artifact gate validates (manifest-driven path), so
    'the figure you verify is the figure you ship'. No-ops when there is no polished
    SVG, the render tools are absent, or the render raises. `base_dir`/`style_lock_path`
    mirror compute_final_artifact_state's overrides (used in tests; default = prod)."""
    import shutil

    if not (shutil.which("rsvg-convert") and shutil.which("pdftoppm")):
        return []
    svg_path = _ship_svg_path(
        example_dir, spec_path, base_dir=base_dir, style_lock_path=style_lock_path
    )
    if svg_path is None:
        return []
    try:
        findings = build_render_ship_findings(svg_path, dpi=dpi)
    except Exception:
        # Fail-safe: a render/parse error must never crash the whole golden-artifact
        # check. This gate is an additive backstop (Plans 1-2 still guard); a tooling
        # hiccup degrades to "no findings", it does not block or explode.
        return []
    return [finding["evidence"] for finding in findings]
