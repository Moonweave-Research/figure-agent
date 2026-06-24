import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from svg_ship_gate import (  # noqa: E402
    _color_present_near,
    _numeric,
    _parse_color,
    _parse_viewbox,
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


def test_numeric_rejects_percentage_so_viewbox_gate_still_runs():
    # '100%' is not an absolute length -> None (documented contract).
    assert _numeric("100%") is None
    assert _numeric("20px") == 20.0
    assert _numeric("20") == 20.0
    # percentage canvas dims must NOT trigger the letterbox skip: the gate should
    # run using the viewBox (percentages don't letterbox), so _parse_viewbox returns it.
    frame = {"viewBox": "0 0 40 20", "width": "100%", "height": "100%"}
    assert _parse_viewbox(frame) == (0.0, 0.0, 40.0, 20.0)


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


from quality_manifest import file_sha256 as _file_sha256  # noqa: E402
from svg_polish_manifest import write_svg_polish_manifest  # noqa: E402
from svg_ship_gate import _ship_svg_path, render_ship_gate_failures  # noqa: E402
from test_svg_polish_manifest import _make_fixture, _valid_manifest  # noqa: E402


def test_generated_export_fixture_is_a_render_ship_noop(tmp_path: Path):
    # A spec with no final_artifact -> kind=generated_export -> no polished SVG to
    # render-ship; the gate must no-op (and resolve no path), not target exports/.
    example_dir = tmp_path / "examples" / "x"
    example_dir.mkdir(parents=True)
    spec_path = example_dir / "spec.yaml"
    spec_path.write_text("name: x\n", encoding="utf-8")
    assert _ship_svg_path(example_dir, spec_path) is None
    assert render_ship_gate_failures(example_dir, spec_path) == []


def test_polished_svg_declared_but_manifest_missing_is_a_noop(tmp_path: Path):
    # final_artifact declares a polished_svg but the manifest file is absent ->
    # MISSING state, path is the .yaml -> the .svg suffix guard skips it (no crash).
    example_dir = tmp_path / "examples" / "demo_fig"
    example_dir.mkdir(parents=True)
    spec_path = example_dir / "spec.yaml"
    spec_path.write_text(
        "name: demo_fig\n"
        "final_artifact:\n"
        "  kind: polished_svg\n"
        "  manifest: polish/svg_polish_manifest.yaml\n",
        encoding="utf-8",
    )
    assert _ship_svg_path(example_dir, spec_path) is None
    assert render_ship_gate_failures(example_dir, spec_path) == []


def test_ship_path_is_manifest_driven_not_hardcoded_stem(tmp_path: Path):
    # THE KEY TEST: the polished SVG lives at a stem != {name}.polished.svg. The old
    # hardcoded f"polish/{name}.polished.svg" would miss it; the manifest-driven path
    # must resolve the file the final-artifact gate actually validates.
    fig_dir = _make_fixture(tmp_path)
    name = fig_dir.name
    style_lock = fig_dir / "style.sty"

    custom_svg = fig_dir / "polish" / "custom_polished.svg"
    custom_svg.write_text("<svg><text>polished</text></svg>\n", encoding="utf-8")

    manifest_data = _valid_manifest(fig_dir, style_lock_path=style_lock)
    manifest_data["polished"]["path"] = "polish/custom_polished.svg"
    manifest_data["polished"]["polished_svg_hash"] = _file_sha256(custom_svg)
    write_svg_polish_manifest(fig_dir / "polish" / "svg_polish_manifest.yaml", manifest_data)

    spec_path = fig_dir / "spec.yaml"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8") + "final_artifact:\n"
        "  kind: polished_svg\n"
        "  manifest: polish/svg_polish_manifest.yaml\n",
        encoding="utf-8",
    )

    resolved = _ship_svg_path(
        fig_dir,
        spec_path,
        base_dir=fig_dir.parent.parent,
        style_lock_path=style_lock,
    )
    assert resolved == custom_svg.resolve()
    # and NOT the hardcoded {name} stem
    assert resolved != (fig_dir / "polish" / f"{name}.polished.svg").resolve()
