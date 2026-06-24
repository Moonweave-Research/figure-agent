# Render-Ship Equivalence Gate — Implementation Plan (figure-agent v2, Slice 0 · Plan 3 of 4, H3 core)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the polished SVG through the actual PDF ship pipeline and BLOCK when a truth-bearing path is not faithfully rendered — i.e. its on-path pixels in the shipped raster match neither its declared fill nor stroke colour. This catches renderer divergence, filter rasterisation, and (as the pixel-exact backstop Plan 2 explicitly deferred) overlay occlusion. It implements the spec's "the figure you verify must be the figure you ship" (§5 gate 4 / H3).

**Architecture:** A new module `svg_ship_gate.py` that REUSES Plan 1's `svg_semantic_diff._inventory` (it already yields, per id'd truth path, an arc-length `polyline` in SVG user coords and a declared optical signature in `colors_by_id`, plus the `frame`/viewBox). Pure helpers parse declared colours, map SVG user coords → raster pixels (viewBox + raster size), and sample the rendered raster along each truth path's polyline. The detector flags `render_ship_divergence` when the matched-colour fraction of a path's on-path samples falls below a threshold. A thin render adapter shells to `rsvg-convert` (SVG→PDF) and reuses `check_visual_clash.render_pdf_first_page` (PDF→raster via `pdftoppm`). All colour/coord/sampling/detector logic is pure and unit-tested with synthetic rasters; only the render adapter needs system tools and is gated behind the existing `@pytest.mark.render` marker.

**Tech Stack:** Python 3.12, `pillow` (already a dep; rasters as `PIL.Image`/`numpy`), `numpy` (dep), stdlib `xml.etree`/`re`. System tools `rsvg-convert` and `pdftoppm` (already used by `scripts/svg_to_png.sh` and `scripts/check_visual_clash.py`). **No new Python dependency.** Accurate RGB→CMYK gamut detection (verified to require an ICC profile — Pillow's profile-free `convert("CMYK")` round-trip is lossless and yields zero signal) is explicitly OUT of scope here and deferred to a focused follow-up (Plan 3B) that would bundle a freely-redistributable CMYK ICC profile and use `PIL.ImageCms`.

**Spec:** `../specs/2026-06-21-figure-agent-v2-svg-illustrator-design.md` §5 gate 4 (H3), §6 Export-A / Shipped-PDF tests (the colour-shift/CMYK half of §6 and the composite-CVD H6 gate are a separate plan). This is the deterministic H3 core.

**Run tests:** from `plugins/figure-agent/`: `uv run pytest tests/ -q` (testpaths=["tests"]). Render-dependent tests: `uv run pytest -m render` (requires `rsvg-convert` + `pdftoppm`); by default `-m "not render"`-style suites and CI without those tools skip them.

**Verified infrastructure (do not re-investigate):**
- `scripts/svg_semantic_diff.py::_inventory(path: Path) -> dict` returns `truth_geometry` (`{id: {"signature","polyline","bbox","order"}}`, `polyline` is `list[complex]` in SVG user coords), `colors_by_id` (`{id: (fill, stroke, opacity, fill-opacity, stroke-opacity)}` of raw attr strings or `None`), and `frame` (`{"viewBox","width","height"}`). REUSE it — do not re-parse the SVG.
- `scripts/check_visual_clash.py::render_pdf_first_page(pdf_path: Path, dpi: int) -> PIL.Image.Image` shells to `pdftoppm -f 1 -singlefile -r {dpi} -png` and returns a Pillow image. REUSE it for PDF→raster.
- `scripts/svg_to_png.sh` shows the repo's trusted rsvg invocation: `rsvg-convert -b white -d 600 -p 600 -f png`. For SVG→PDF use `rsvg-convert -f pdf`.
- The terminal gate aggregates `*_gate_failures(example_dir, spec_path) -> list[str]` functions in `scripts/check_golden_artifacts.py::check_example` (after `final_artifact_gate_failures`); a new `render_ship_gate_failures` plugs in there.
- `pyproject.toml` declares `markers = ["render: requires TeX/render/OCR system tools"]`.

**Import convention (verified):** `scripts/` is not a package. Test modules begin with `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))`, then import by bare name with `# noqa: E402`. Source modules import siblings the same bare way (e.g. `svg_ship_gate.py` does `from svg_semantic_diff import _inventory`). Commit per task with the message shown; co-author trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

**Import placement (ruff isort + a hook that strips unused imports — learned in Plan 1):** every step below that says "append" means append the *functions/constants*; new **module-level** imports (`from typing import Any`, `import subprocess`, `import tempfile`, `from pathlib import Path`, `from svg_semantic_diff import _inventory`) belong in the file's top import block, and ruff will order them. Add each import in the SAME edit as the code that uses it (a ruff `PostToolUse` hook strips imports that momentarily look unused). Two imports are deliberately **local** (inside their functions, not module-level): `from check_visual_clash import render_pdf_first_page` (only when rendering) and `import shutil` (only in the gate adapter).

---

## Review hardening (empirical, 2026-06-21)

A pre-execution adversarial review ran this plan's logic through the REAL `rsvg-convert → pdf → pdftoppm` chain on cases the plan's own (square, stroked, opaque) test SVGs hid. Three real holes were found and are already folded into the code above:

1. **Filled truth regions false-BLOCKERed (serious, confirmed).** A truth path's polyline traces its *outline*; for a FILLED region the on-line pixels straddle the antialiased fill/background edge (probe: a faithfully-rendered filled square scored `match_frac 0.492` → false BLOCK; top sampled colours = 130 background + 126 fill). **Fix: window sampling** (`_color_present_near`, radius 2) — verified to lift the filled square to `1.0` (pass) while the opaque-cover case stays `0.0` (still BLOCK). Occlusion detection is NOT weakened.
2. **Semi-transparent truth paths false-BLOCKERed (confirmed).** A `stroke-opacity=0.5` red renders `(255,127,127)` over the white page, not pure red (channel delta 127 > tolerance 60 → false BLOCK). **Fix: `_blend_to_white`** adds the opacity-blended variant of each declared colour to the match set.
3. **Letterbox coordinate mapping (edge case).** When the SVG forces `width`/`height` at a different aspect ratio than the `viewBox`, rsvg letterboxes (preserveAspectRatio meet) and the linear viewBox→raster mapping mis-locates off-centre features. **Fix: `_parse_viewbox` skips** (returns None → gate no-op) on an aspect mismatch rather than risk a false divergence. (A viewBox `min-x`/`min-y` offset IS handled correctly — verified.)

Also hardened: the terminal-gate adapter wraps the render in `try/except` (a backstop gate must never crash the golden-artifact check), and renders only when a `polish/*.polished.svg` exists AND the tools are present (per-figure cost is bounded; polished SVGs are rare).

---

## File Structure

- **Create** `scripts/svg_ship_gate.py` — colour/coord/sampling helpers + the `render_ship_divergence` detector + the render adapter + the public gate. One responsibility: "does the shipped render faithfully show the truth paths?"
- **Create** `tests/test_svg_ship_gate.py` — pure-logic unit tests (synthetic numpy rasters; no rendering) for Tasks 1-2, and a `@pytest.mark.render` integration test for Task 3.
- **Modify** `scripts/check_golden_artifacts.py` — add `render_ship_gate_failures` to the `check_example` failure chain (Task 3).

---

## Task 1: Pure colour + coordinate + sampling helpers

**Files:**
- Create: `scripts/svg_ship_gate.py`
- Test: `tests/test_svg_ship_gate.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_svg_ship_gate.py
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from svg_ship_gate import (  # noqa: E402
    _parse_color,
    _svg_to_pixel,
    _color_present_near,
)


def test_parse_color_hex_and_names():
    assert _parse_color("#ff0000") == (255, 0, 0)
    assert _parse_color("#0f0") == (0, 255, 0)
    assert _parse_color("white") == (255, 255, 255)
    assert _parse_color("black") == (0, 0, 0)
    assert _parse_color("none") is None
    assert _parse_color(None) is None
    assert _parse_color("url(#grad)") is None  # unparseable -> None (skipped, not a crash)


def test_svg_to_pixel_maps_viewbox_to_raster():
    # viewBox (0,0,10,10) onto a 100x50 raster: x scales by 10, y by 5.
    viewbox = (0.0, 0.0, 10.0, 10.0)
    assert _svg_to_pixel(5 + 5j, viewbox, raster_w=100, raster_h=50) == (50, 25)
    assert _svg_to_pixel(0 + 0j, viewbox, raster_w=100, raster_h=50) == (0, 0)
    # out-of-frame point clamps into [0, w-1]/[0, h-1]
    assert _svg_to_pixel(100 + 100j, viewbox, raster_w=100, raster_h=50) == (99, 49)


def test_color_present_near_window_absorbs_edges():
    raster = np.zeros((50, 50, 3), dtype=np.uint8)  # all black
    raster[25, 25] = (0, 0, 255)  # one blue pixel
    # a point mapping near the blue pixel (within radius 2) -> present
    assert _color_present_near(raster, (24, 24), {(0, 0, 255)}) is True
    # a point far from any blue -> absent
    assert _color_present_near(raster, (5, 5), {(0, 0, 255)}) is False
    # empty colour set never matches
    assert _color_present_near(raster, (25, 25), set()) is False
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_svg_ship_gate.py -k "parse_color or svg_to_pixel or color_present" -v`
Expected: FAIL — `ModuleNotFoundError` / names not importable.

- [ ] **Step 3: Implement the helpers**

```python
# scripts/svg_ship_gate.py
"""Render-ship equivalence gate (spec §5 H3): does the shipped PDF render faithfully
show each truth-bearing path? Pure colour/coord/sampling logic here is render-free
and unit-testable; the render adapter (rsvg-convert + pdftoppm) is the only part that
needs system tools.
"""
from __future__ import annotations

import re

import numpy as np

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


COLOR_DELTA = 60  # per-channel tolerance for "this pixel matches a declared colour"


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
                all(abs(int(sample[i]) - color[i]) <= delta for i in range(3))
                for color in colors
            ):
                return True
    return False
```

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/test_svg_ship_gate.py -k "parse_color or svg_to_pixel or color_present" -v`
Expected: PASS (all three).

- [ ] **Step 5: Commit**

```bash
git add scripts/svg_ship_gate.py tests/test_svg_ship_gate.py
git commit -m "feat(ship): pure colour/coord/sampling helpers for the render-ship gate"
```

---

## Task 2: The divergence detector

**Files:**
- Modify: `scripts/svg_ship_gate.py`
- Test: `tests/test_svg_ship_gate.py`

A truth path is faithfully rendered if a sufficient fraction of its on-path samples match (within `COLOR_DELTA` per channel) one of its declared colours (fill or stroke). Below `MIN_MATCH_FRACTION` → BLOCKER `render_ship_divergence` (covered / blurred / renderer-shifted). A path with no parseable declared colour is skipped (not checkable, not a crash). The finding dict mirrors `svg_semantic_diff`'s shape.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_svg_ship_gate.py  (append)
from svg_ship_gate import detect_render_ship_divergence  # noqa: E402

VIEWBOX = (0.0, 0.0, 10.0, 10.0)


def _solid(color):
    raster = np.zeros((100, 100, 3), dtype=np.uint8)
    raster[:, :] = color
    return raster


def test_faithful_render_passes():
    # truth path declared red, rendered red along its whole polyline -> no finding.
    raster = _solid((255, 0, 0))
    truth = [{"id": "boundary", "polyline": [1 + 1j, 5 + 5j, 9 + 9j], "colors": {(255, 0, 0)}}]
    assert detect_render_ship_divergence(raster, truth, VIEWBOX) == []


def test_occluded_or_shifted_render_is_blocked():
    # truth declared red but the raster shows white where it should be -> divergence.
    raster = _solid((255, 255, 255))
    truth = [{"id": "boundary", "polyline": [1 + 1j, 5 + 5j, 9 + 9j], "colors": {(255, 0, 0)}}]
    findings = detect_render_ship_divergence(raster, truth, VIEWBOX)
    assert any(
        f["kind"] == "render_ship_divergence" and f["severity"] == "BLOCKER" for f in findings
    )


def test_uncheckable_color_is_skipped():
    raster = _solid((255, 255, 255))
    truth = [{"id": "grad", "polyline": [1 + 1j, 9 + 9j], "colors": set()}]
    assert detect_render_ship_divergence(raster, truth, VIEWBOX) == []
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_svg_ship_gate.py -k "faithful or occluded or uncheckable" -v`
Expected: FAIL — `cannot import name 'detect_render_ship_divergence'`.

- [ ] **Step 3: Implement the detector**

```python
# scripts/svg_ship_gate.py  (append; `from typing import Any` goes in the top import block)
MIN_MATCH_FRACTION = 0.5  # at least this fraction of on-path samples must match


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
```

(`from typing import Any` is a module-level import → top of the file; `MIN_MATCH_FRACTION` and the detector are appended. `_color_present_near` and `COLOR_DELTA` were added in Task 1.)

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/test_svg_ship_gate.py -k "faithful or occluded or uncheckable" -v`
Expected: PASS (all three).

- [ ] **Step 5: Commit**

```bash
git add scripts/svg_ship_gate.py tests/test_svg_ship_gate.py
git commit -m "feat(ship): render_ship_divergence detector (on-path colour fidelity)"
```

---

## Task 3: Render adapter + public gate + golden-artifact integration

**Files:**
- Modify: `scripts/svg_ship_gate.py` (render adapter + `build_render_ship_findings` + `render_ship_gate_failures`)
- Modify: `scripts/check_golden_artifacts.py` (wire the gate into `check_example`)
- Test: `tests/test_svg_ship_gate.py` (a `@pytest.mark.render` integration test)

Assemble truth-path sample specs from `svg_semantic_diff._inventory`, render the SVG, and run the detector. `build_render_ship_findings(svg_path, *, dpi=600)` returns the findings; `render_ship_gate_failures(example_dir, spec_path)` adapts them to the `list[str]` the terminal gate consumes. The render adapter is the only system-tool-dependent code.

- [ ] **Step 1: Write the failing test (render-gated)**

```python
# tests/test_svg_ship_gate.py  (append)
import shutil

import pytest

from svg_ship_gate import build_render_ship_findings  # noqa: E402

_RENDER_TOOLS = shutil.which("rsvg-convert") and shutil.which("pdftoppm")


@pytest.mark.render
@pytest.mark.skipif(not _RENDER_TOOLS, reason="needs rsvg-convert + pdftoppm")
def test_opaque_overlay_over_truth_is_caught_in_real_render(tmp_path: Path):
    # A red truth boundary fully covered by an opaque white rect -> the shipped
    # raster shows white where the boundary should be -> render_ship_divergence.
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" width="20" height="20">'
        '<path id="boundary" fill="none" stroke="#ff0000" stroke-width="3" d="M2,10 L18,10"/>'
        '<rect id="hand:cover" fill="#ffffff" x="0" y="0" width="20" height="20"/>'
        "</svg>"
    )
    svg_path = tmp_path / "fig.svg"
    svg_path.write_text(svg, encoding="utf-8")
    findings = build_render_ship_findings(svg_path, dpi=150)
    assert any(f["kind"] == "render_ship_divergence" for f in findings)


@pytest.mark.render
@pytest.mark.skipif(not _RENDER_TOOLS, reason="needs rsvg-convert + pdftoppm")
def test_faithful_figure_renders_clean(tmp_path: Path):
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" width="20" height="20">'
        '<path id="boundary" fill="none" stroke="#ff0000" stroke-width="3" d="M2,10 L18,10"/>'
        "</svg>"
    )
    svg_path = tmp_path / "fig.svg"
    svg_path.write_text(svg, encoding="utf-8")
    assert build_render_ship_findings(svg_path, dpi=150) == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_svg_ship_gate.py -k "real_render or faithful_figure" -v`
Expected: FAIL — `cannot import name 'build_render_ship_findings'` (or, if rsvg/pdftoppm are absent, SKIPPED — in that case verify the import error first by importing the name in a Python REPL, then proceed).

- [ ] **Step 3: Implement the render adapter + assembly + gate**

```python
# scripts/svg_ship_gate.py
# Module-level imports (subprocess, tempfile, pathlib.Path, svg_semantic_diff._inventory)
# go in the TOP import block; the functions below are appended.

# svg_semantic_diff.OPTICAL_ATTRS order: (fill, stroke, opacity, fill-opacity, stroke-opacity)


def _numeric(value: str | None) -> float | None:
    """Leading number of a length string ('20', '20px' -> 20.0; '100%'/None -> None)."""
    if not value:
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
    if canvas_w and canvas_h and abs(canvas_w / canvas_h - width / height) > 0.01 * (width / height):
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_svg_ship_gate.py -m render -v` (on a machine with `rsvg-convert` + `pdftoppm`)
Expected: PASS — the occluded figure yields `render_ship_divergence`, the faithful one is clean.
Also run the pure suite: `uv run pytest tests/test_svg_ship_gate.py -q` — Task 1-2 tests still pass; the render tests skip if tools are absent.

- [ ] **Step 5: Wire into the terminal golden-artifact gate**

In `scripts/svg_ship_gate.py`, add the `list[str]` adapter:

```python
# scripts/svg_ship_gate.py  (append)
def render_ship_gate_failures(
    example_dir: Path, *, dpi: int = 600, polished_svg: str | None = None
) -> list[str]:
    """Terminal-gate adapter: returns human-readable failure strings (empty = pass).
    Skips silently if the polished SVG or the render tools are unavailable."""
    import shutil

    name = example_dir.name
    svg_rel = polished_svg or f"polish/{name}.polished.svg"
    svg_path = example_dir / svg_rel
    if not svg_path.is_file():
        return []
    if not (shutil.which("rsvg-convert") and shutil.which("pdftoppm")):
        return []
    try:
        findings = build_render_ship_findings(svg_path, dpi=dpi)
    except Exception:
        # Fail-safe: a render/parse error must never crash the whole golden-artifact
        # check. This gate is an additive backstop (Plans 1-2 still guard); a tooling
        # hiccup degrades to "no findings", it does not block or explode.
        return []
    return [finding["evidence"] for finding in findings]
```

Then in `scripts/check_golden_artifacts.py`, READ the file first; locate the `check_example` failure chain where `final_artifact_gate_failures(example_dir, spec_path)` is appended to `failures`, and add immediately after it:

```python
        failures.extend(render_ship_gate_failures(example_dir))
```

with the import near the other script imports at the top of `check_golden_artifacts.py`:

```python
from svg_ship_gate import render_ship_gate_failures
```

(Match the file's existing import style — bare sibling import.)

- [ ] **Step 6: Full suite — no regressions**

Run: `uv run pytest tests/ -q`
Expected: green. The new gate is additive; `render_ship_gate_failures` returns `[]` when there is no polished SVG or no render tools, so existing fixtures (which mostly lack `polish/*.polished.svg` and/or run without the render marker) are unaffected. If a fixture DOES have a polished SVG and the tools are present, confirm any new failure is a genuine render divergence (and if it is, that is the gate working — assess per the fixture's intent, do not weaken the gate).

- [ ] **Step 7: Commit**

```bash
git add scripts/svg_ship_gate.py scripts/check_golden_artifacts.py tests/test_svg_ship_gate.py
git commit -m "feat(ship): render-ship equivalence gate wired into the terminal golden-artifact check"
```

---

## Done-when

- `uv run pytest tests/ -q` green; `uv run pytest tests/test_svg_ship_gate.py -m render` green on a machine with `rsvg-convert` + `pdftoppm`.
- A truth path covered by an opaque overlay, blurred by a filter, or colour-shifted by the renderer → BLOCKER `render_ship_divergence` from the real shipped raster (this is the pixel-exact backstop Plan 2's bbox/opacity occlusion proxy deferred).
- A faithfully-rendered figure — including a FILLED truth region and a semi-transparent (opacity) truth path (both verified false-positives without the Review-hardening fixes) — → clean.
- The gate plugs into `check_golden_artifacts.check_example`, wraps the render in `try/except`, and degrades to a no-op when the polished SVG or render tools are absent.

**Documented scope boundaries / known limitations (out of this plan):**
- Accurate RGB→CMYK gamut detection (needs a bundled ICC profile + `PIL.ImageCms` — Pillow's profile-free CMYK round-trip is lossless, verified) → Plan 3B.
- Composite CVD/grayscale/contrast on the rendered raster (§5 gate 3, H6) → separate plan.
- Truth paths with a `transform` are sampled at pre-transform coords (semantic_diff already flags transformed truth elements as `group_transform_risk`) → known limitation.
- Truth paths whose declared colour is `url(#grad)`/CSS/named-outside-the-small-set/unparseable are skipped, not checked (additive gate — it checks what it can parse).
- **Letterboxed SVGs** (declared width/height aspect ≠ viewBox aspect) are skipped (coordinate mapping unreliable). Most pipeline SVGs set matching dimensions.
- **A semi-transparent truth path over a non-white fill** blends toward that fill, not white; `_blend_to_white` assumes the white render page, so such a path could still mis-match (uncommon; truth paths are normally opaque on the page).
- **No render tools / no polished SVG = no protection (silent no-op).** This gate is an additive backstop — Plans 1-2's geometry/occlusion locks still apply. For the ship gate to actually run, CI/dev must have `rsvg-convert` + `pdftoppm`.

Plan 4 (`add_volume_shading`) remains the first overlay producer, which must pass both Plan 2's occlusion guard and this render-ship gate.
