import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from svg_ship_gate import (  # noqa: E402
    _color_present_near,
    _parse_color,
    _svg_to_pixel,
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


from svg_ship_gate import detect_render_ship_divergence  # noqa: E402

VIEWBOX = (0.0, 0.0, 10.0, 10.0)


def _solid(color: tuple[int, int, int]) -> np.ndarray:
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
