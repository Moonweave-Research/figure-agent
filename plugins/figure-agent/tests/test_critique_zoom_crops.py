from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_zoom_crops import build_zoom_crop_pack  # noqa: E402


def _write_png(path: Path, size: tuple[int, int] = (120, 80)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, "white").save(path)


def test_build_zoom_crop_pack_creates_full_render_quadrants(tmp_path: Path) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    _write_png(render)

    crops = build_zoom_crop_pack(example_dir, render, panel_crop_paths=())

    assert [item["id"] for item in crops] == [
        "full_q1",
        "full_q2",
        "full_q3",
        "full_q4",
    ]
    assert all((example_dir / item["path"]).is_file() for item in crops)
    assert crops[0]["source"] == "full_render"
    assert crops[0]["bbox_px"] == [0, 0, 60, 40]
    assert crops[3]["bbox_px"] == [60, 40, 120, 80]


def test_build_zoom_crop_pack_adds_panel_quadrants(tmp_path: Path) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    panel = example_dir / "build" / "panel_crops" / "A.png"
    _write_png(render)
    _write_png(panel, size=(80, 60))

    crops = build_zoom_crop_pack(example_dir, render, panel_crop_paths=(panel,))

    ids = [item["id"] for item in crops]
    assert "panel_A_q1" in ids
    assert "panel_A_q4" in ids
    assert (example_dir / "build" / "audit_crops" / "panel_A_q1.png").is_file()


def test_build_zoom_crop_pack_rejects_non_fixture_relative_panel_crop(tmp_path: Path) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    outside = tmp_path / "outside.png"
    _write_png(render)
    _write_png(outside)

    try:
        build_zoom_crop_pack(example_dir, render, panel_crop_paths=(outside,))
    except ValueError as exc:
        assert "panel crop must be inside example_dir" in str(exc)
    else:
        raise AssertionError("expected ValueError")
