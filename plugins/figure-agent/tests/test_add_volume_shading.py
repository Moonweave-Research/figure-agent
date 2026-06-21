from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from add_volume_shading import _element_bbox, _gradient_vector, _opacity_for  # noqa: E402

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
