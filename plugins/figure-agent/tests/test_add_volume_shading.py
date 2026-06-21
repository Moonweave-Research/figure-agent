from __future__ import annotations

import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from add_volume_shading import (  # noqa: E402
    _element_bbox,
    _gradient_vector,
    _opacity_for,
    add_volume_shading,
)
from svg_semantic_diff import _compare, _inventory  # noqa: E402
from svg_ship_gate import build_render_ship_findings  # noqa: E402

# ---------------------------------------------------------------------------
# _element_bbox
# ---------------------------------------------------------------------------

_NS = "http://www.w3.org/2000/svg"

_RECT_SVG = f"""<svg xmlns="{_NS}">
  <rect id="r1" x="10" y="20" width="100" height="50"/>
</svg>"""

_CIRCLE_SVG = f"""<svg xmlns="{_NS}">
  <circle id="c1" cx="50" cy="60" r="15"/>
</svg>"""

_ELLIPSE_SVG = f"""<svg xmlns="{_NS}">
  <ellipse id="e1" cx="40" cy="30" rx="20" ry="10"/>
</svg>"""

_PATH_SVG = f"""<svg xmlns="{_NS}">
  <path id="p" d="M0,0 L10,0 L10,5 Z"/>
</svg>"""

_MISSING_SVG = f"""<svg xmlns="{_NS}">
  <rect id="other" x="0" y="0" width="5" height="5"/>
</svg>"""


def test_rect_bbox():
    x, y, w, h = _element_bbox(_RECT_SVG, "r1")
    assert x == pytest.approx(10.0)
    assert y == pytest.approx(20.0)
    assert w == pytest.approx(100.0)
    assert h == pytest.approx(50.0)


def test_circle_bbox():
    x, y, w, h = _element_bbox(_CIRCLE_SVG, "c1")
    assert x == pytest.approx(35.0)  # 50 - 15
    assert y == pytest.approx(45.0)  # 60 - 15
    assert w == pytest.approx(30.0)  # 2 * 15
    assert h == pytest.approx(30.0)  # 2 * 15


def test_ellipse_bbox():
    x, y, w, h = _element_bbox(_ELLIPSE_SVG, "e1")
    assert x == pytest.approx(20.0)  # 40 - 20
    assert y == pytest.approx(20.0)  # 30 - 10
    assert w == pytest.approx(40.0)  # 2 * 20
    assert h == pytest.approx(20.0)  # 2 * 10


def test_path_bbox():
    # canonical_polyline samples curves; allow small numerical tolerance
    x, y, w, h = _element_bbox(_PATH_SVG, "p")
    assert x == pytest.approx(0.0, abs=0.02)
    assert y == pytest.approx(0.0, abs=0.02)
    assert w == pytest.approx(10.0, abs=0.02)
    assert h == pytest.approx(5.0, abs=0.02)


def test_not_found_raises():
    with pytest.raises(ValueError, match="target id not found: missing"):
        _element_bbox(_MISSING_SVG, "missing")


_LINE_SVG = f"""<svg xmlns="{_NS}">
  <line id="ln" x1="0" y1="0" x2="10" y2="10"/>
</svg>"""


def test_unsupported_shape_raises():
    with pytest.raises(ValueError, match="unsupported shape for bbox: line id=ln"):
        _element_bbox(_LINE_SVG, "ln")


# ---------------------------------------------------------------------------
# _opacity_for
# ---------------------------------------------------------------------------


def test_opacity_for_zero():
    assert _opacity_for(0.0) == pytest.approx(0.10)


def test_opacity_for_one():
    assert _opacity_for(1.0) == pytest.approx(0.55)


def test_opacity_for_all_below_occlusion():
    for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
        assert _opacity_for(v) < 0.95


def test_opacity_for_clamp_high():
    assert _opacity_for(2.0) == pytest.approx(0.55)


def test_opacity_for_clamp_low():
    assert _opacity_for(-1.0) == pytest.approx(0.10)


def test_opacity_for_monotonic():
    values = [_opacity_for(v / 10) for v in range(11)]
    for a, b in zip(values, values[1:]):
        assert b >= a


# ---------------------------------------------------------------------------
# _gradient_vector
# ---------------------------------------------------------------------------


def test_gradient_vector_0_deg():
    x1, y1, x2, y2 = _gradient_vector(0.0)
    assert x1 == pytest.approx(0.0, abs=1e-4)
    assert y1 == pytest.approx(0.5, abs=1e-4)
    assert x2 == pytest.approx(1.0, abs=1e-4)
    assert y2 == pytest.approx(0.5, abs=1e-4)


def test_gradient_vector_90_deg():
    x1, y1, x2, y2 = _gradient_vector(90.0)
    assert x1 == pytest.approx(0.5, abs=1e-4)
    assert y1 == pytest.approx(0.0, abs=1e-4)
    assert x2 == pytest.approx(0.5, abs=1e-4)
    assert y2 == pytest.approx(1.0, abs=1e-4)


def test_gradient_vector_in_unit_range():
    for deg in [0, 45, 90, 135, 180, 270]:
        coords = _gradient_vector(float(deg))
        for v in coords:
            assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# add_volume_shading (the public op)
# ---------------------------------------------------------------------------

# A truth-bearing dark-outline target (default truth-bearing) plus a second truth
# path, mirroring the demo-fixture shape.
_OP_BASE_SVG = (
    f'<svg xmlns="{_NS}" viewBox="0 0 100 100" width="100" height="100">'
    '<rect id="bead" x="20" y="20" width="40" height="40" fill="#cccccc" stroke="#222222"/>'
    '<path id="axis" d="M0,80 L100,80"/>'
    "</svg>"
)


def _polished(svg: str = _OP_BASE_SVG) -> str:
    return add_volume_shading(svg, "bead", light_direction=45.0, hero_strength=0.5)


def test_op_requires_light_direction():
    with pytest.raises(ValueError):
        add_volume_shading(_OP_BASE_SVG, "bead", light_direction=None, hero_strength=0.5)


def test_op_requires_hero_strength():
    with pytest.raises(ValueError):
        add_volume_shading(_OP_BASE_SVG, "bead", light_direction=45.0, hero_strength=None)


def test_op_missing_target_raises():
    with pytest.raises(ValueError, match="target id not found: nope"):
        add_volume_shading(_OP_BASE_SVG, "nope", light_direction=45.0, hero_strength=0.5)


def test_op_emits_gradient_in_defs():
    root = ET.fromstring(_polished())
    defs = root.find(f"{{{_NS}}}defs")
    assert defs is not None
    grads = defs.findall(f"{{{_NS}}}linearGradient")
    assert any(g.get("id") == "hand:vshade-bead" for g in grads)
    grad = next(g for g in grads if g.get("id") == "hand:vshade-bead")
    stops = grad.findall(f"{{{_NS}}}stop")
    assert len(stops) == 2
    assert stops[0].get("stop-color") == "#ffffff"
    assert stops[1].get("stop-color") == "#000000"


def _find_by_id(root: ET.Element, target_id: str) -> ET.Element | None:
    for elem in root.iter():
        if elem.get("id") == target_id:
            return elem
    return None


def test_op_emits_overlay_after_target():
    root = ET.fromstring(_polished())
    overlay = _find_by_id(root, "hand:vshade-overlay-bead")
    assert overlay is not None
    assert overlay.get("data-truth-bearing") == "false"
    assert overlay.get("fill") == "url(#hand:vshade-bead)"
    assert float(overlay.get("opacity")) < 0.95

    # overlay paints AFTER the target in document order (same parent)
    siblings = list(root)
    ids = [child.get("id") for child in siblings]
    assert ids.index("hand:vshade-overlay-bead") > ids.index("bead")


def test_op_overlay_safe_no_inventory_change(tmp_path):
    base = tmp_path / "base.svg"
    polished = tmp_path / "polished.svg"
    base.write_text(_OP_BASE_SVG, encoding="utf-8")
    polished.write_text(_polished(), encoding="utf-8")
    findings = _compare(_inventory(base), _inventory(polished))
    assert not [f for f in findings if f["kind"] == "element_inventory_change"]


def test_op_no_occlusion_blocker(tmp_path):
    base = tmp_path / "base.svg"
    polished = tmp_path / "polished.svg"
    base.write_text(_OP_BASE_SVG, encoding="utf-8")
    polished.write_text(_polished(), encoding="utf-8")
    findings = _compare(_inventory(base), _inventory(polished))
    blockers = {
        f["kind"]
        for f in findings
        if f["severity"] == "BLOCKER" and f["kind"] in {"truth_path_removed", "truth_path_occluded"}
    }
    assert not blockers


def test_op_does_not_mutate_target_paint():
    root = ET.fromstring(_polished())
    bead = _find_by_id(root, "bead")
    assert bead is not None
    assert bead.get("fill") == "#cccccc"
    assert bead.get("stroke") == "#222222"


def test_op_emits_no_filter():
    root = ET.fromstring(_polished())
    assert root.find(f".//{{{_NS}}}filter") is None


def test_op_idempotent_gradient_id():
    once = _polished()
    twice = add_volume_shading(once, "bead", light_direction=45.0, hero_strength=0.5)
    root = ET.fromstring(twice)
    grads = [g for g in root.iter(f"{{{_NS}}}linearGradient") if g.get("id") == "hand:vshade-bead"]
    assert len(grads) == 1


def test_op_idempotent_overlay_id():
    once = _polished()
    twice = add_volume_shading(once, "bead", light_direction=45.0, hero_strength=0.5)
    root = ET.fromstring(twice)
    overlays = [e for e in root.iter() if e.get("id") == "hand:vshade-overlay-bead"]
    assert len(overlays) == 1


# ---------------------------------------------------------------------------
# First polished-SVG fixture: exercises Plan 2 (occlusion) + Plan 3 (render-ship)
# gates LIVE — both are dormant until a real *.polished.svg exists.
# ---------------------------------------------------------------------------

FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "_volume_shading_demo"
_DEMO_BASE = FIXTURE / "exports" / "_volume_shading_demo.svg"
_DEMO_POLISHED = FIXTURE / "polish" / "_volume_shading_demo.polished.svg"


def test_demo_polished_matches_op_output():
    # The committed polished.svg must be exactly the op output, so the live gate
    # proof below validates the real artifact, not a hand-edited copy.
    base = _DEMO_BASE.read_text(encoding="utf-8")
    produced = add_volume_shading(base, "electrode", light_direction=315, hero_strength=0.6)
    assert produced == _DEMO_POLISHED.read_text(encoding="utf-8")


def test_demo_fixture_passes_occlusion_guard():
    findings = _compare(_inventory(_DEMO_BASE), _inventory(_DEMO_POLISHED))
    assert not [f for f in findings if f["kind"] in {"truth_path_occluded", "truth_path_removed"}]
    assert not [f for f in findings if f["kind"] == "element_inventory_change"]


@pytest.mark.render
@pytest.mark.skipif(
    not (shutil.which("rsvg-convert") and shutil.which("pdftoppm")),
    reason="requires rsvg-convert and pdftoppm",
)
def test_demo_fixture_passes_render_ship_gate():
    # The translucent inset leaves the truth outline's colour intact, so the
    # shipped raster renders faithfully -> no divergence.
    assert build_render_ship_findings(_DEMO_POLISHED, dpi=150) == []


def test_opaque_overlay_variant_is_blocked(tmp_path):
    # The lie the op refuses to emit: an OPAQUE hand:* rect drawn AFTER (on top of)
    # the electrode, covering its bbox. The occlusion guard must BLOCK it.
    base = _DEMO_BASE.read_text(encoding="utf-8")
    opaque = base.replace(
        "</svg>",
        '<rect id="hand:cover" data-truth-bearing="false" '
        'x="18" y="8" width="44" height="64" fill="#1f2a36" opacity="1.0"/></svg>',
    )
    opaque_path = tmp_path / "opaque.svg"
    opaque_path.write_text(opaque, encoding="utf-8")
    findings = _compare(_inventory(_DEMO_BASE), _inventory(opaque_path))
    assert any(f["kind"] == "truth_path_occluded" and f["severity"] == "BLOCKER" for f in findings)
