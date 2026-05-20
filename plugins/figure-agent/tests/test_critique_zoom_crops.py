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
    zoom_crops = [item for item in crops if item["kind"] == "zoom_crop"]

    assert [item["id"] for item in zoom_crops] == [
        "full_q1",
        "full_q2",
        "full_q3",
        "full_q4",
    ]
    assert all((example_dir / item["path"]).is_file() for item in zoom_crops)
    assert zoom_crops[0]["source"] == "full_render"
    assert zoom_crops[0]["bbox_px"] == [0, 0, 60, 40]
    assert zoom_crops[3]["bbox_px"] == [60, 40, 120, 80]


def test_build_zoom_crop_pack_creates_print_scale_audit_images(tmp_path: Path) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    _write_png(render, size=(1200, 800))

    crops = build_zoom_crop_pack(example_dir, render, panel_crop_paths=())

    print_items = [item for item in crops if item["kind"] == "print_scale"]
    assert [item["id"] for item in print_items] == ["print_178mm", "print_thumbnail"]
    assert [item["scale_label"] for item in print_items] == [
        "178mm_equivalent",
        "thumbnail",
    ]
    for item in print_items:
        path = example_dir / item["path"]
        assert path.is_file()
        with Image.open(path) as image:
            assert image.size == tuple(item["size_px"])
            assert image.width < 1200


def test_build_zoom_crop_pack_keeps_small_print_scale_images_at_original_width(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    _write_png(render, size=(300, 200))

    crops = build_zoom_crop_pack(example_dir, render, panel_crop_paths=())

    print_items = [item for item in crops if item["kind"] == "print_scale"]
    assert [item["size_px"] for item in print_items] == [[300, 200], [300, 200]]


def test_build_zoom_crop_pack_print_scale_size_is_deterministic_for_nonsquare_render(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    _write_png(render, size=(1600, 900))

    crops = build_zoom_crop_pack(example_dir, render, panel_crop_paths=())

    print_items = {item["id"]: item for item in crops if item["kind"] == "print_scale"}
    assert print_items["print_178mm"]["size_px"] == [1000, 562]
    assert print_items["print_thumbnail"]["size_px"] == [360, 202]


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
    print_items = [item for item in crops if item["kind"] == "print_scale"]
    assert [item["id"] for item in print_items] == ["print_178mm", "print_thumbnail"]
    assert all(item["source_path"] == "build/demo.png" for item in print_items)
    assert not any(item["id"].startswith("panel_A") for item in print_items)


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
