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
    assert [item["scale_basis"] for item in print_items] == [
        "fixed_width_proxy",
        "fixed_width_proxy",
    ]
    assert [item["target_width_px"] for item in print_items] == [1000, 360]
    assert [item["upscaled"] for item in print_items] == [False, False]
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
    assert [item["upscaled"] for item in print_items] == [False, False]


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


def test_build_zoom_crop_pack_adds_panel_subquadrants_without_instruments(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    panel = example_dir / "build" / "panel_crops" / "E.png"
    _write_png(render)
    _write_png(panel, size=(160, 120))

    crops = build_zoom_crop_pack(
        example_dir,
        render,
        panel_crop_paths=(panel,),
        spec={"panels": [{"id": "E"}]},
    )

    ids = [item["id"] for item in crops]
    assert "panel_E_q1" in ids
    assert "panel_E_q4" in ids
    assert "panel_E_s01" in ids
    assert "panel_E_s16" in ids
    subcrop = next(item for item in crops if item["id"] == "panel_E_s16")
    assert subcrop["bbox_px"] == [120, 90, 160, 120]
    assert (example_dir / "build" / "audit_crops" / "panel_E_s16.png").is_file()


def test_build_zoom_crop_pack_adds_declared_instrument_crops(tmp_path: Path) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    panel = example_dir / "build" / "panel_crops" / "E.png"
    _write_png(render, size=(1000, 500))
    _write_png(panel, size=(160, 120))

    crops = build_zoom_crop_pack(
        example_dir,
        render,
        panel_crop_paths=(panel,),
        spec={
            "panels": [
                {
                    "id": "E",
                    "instruments": [
                        {
                            "name": "HV+ box",
                            "bbox_pdf_cm": [6.10, 4.05, 6.95, 4.45],
                        }
                    ],
                }
            ]
        },
        pdf_page_size_cm=(10.0, 5.0),
    )

    ids = [item["id"] for item in crops]
    assert "panel_E_instr_HV_box" in ids
    assert "panel_E_s01" not in ids
    crop = next(item for item in crops if item["id"] == "panel_E_instr_HV_box")
    assert crop["bbox_px"] == [610, 405, 695, 445]
    assert crop["source"] == "panel:E:instrument:HV+ box"
    assert crop["upscaled"] is True
    assert crop["size_px"][0] == 600
    with Image.open(example_dir / crop["path"]) as image:
        assert image.width == 600


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
