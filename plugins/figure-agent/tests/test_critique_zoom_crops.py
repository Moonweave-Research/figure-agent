from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_zoom_crops import build_zoom_crop_pack  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


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


def test_build_zoom_crop_pack_adds_visual_clash_crops_and_manifest(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    _write_png(render, size=(120, 80))
    (example_dir / "build" / "visual_clash.json").write_text(
        json.dumps(
            {
                "fixture": "demo",
                "render_pdf": "build/demo.pdf",
                "candidates": [
                    {
                        "id": "VC002",
                        "kind": "text_on_path",
                        "text": "HV+",
                        "bbox_px": [90, 70, 150, 120],
                        "metric": {"dark": 0.041},
                        "tex_lines": None,
                    },
                    {
                        "id": "VC001",
                        "kind": "text_on_fill",
                        "text": "A",
                        "bbox_px": [10, 10, 12, 12],
                        "metric": {"luma_std": 27.4},
                        "tex_lines": [20],
                    },
                ],
                "total": 2,
            }
        ),
        encoding="utf-8",
    )

    crops = build_zoom_crop_pack(example_dir, render, panel_crop_paths=())

    visual_clash_crops = [
        item for item in crops if item["kind"] == "visual_clash_crop"
    ]
    assert [item["id"] for item in visual_clash_crops] == ["VC001_A", "VC002_HV"]
    assert all(
        item["path"].startswith("build/audit_crops/visual_clash/")
        for item in visual_clash_crops
    )
    assert all((example_dir / item["path"]).is_file() for item in visual_clash_crops)
    assert visual_clash_crops[0]["visual_clash_ref"] == "VC001"
    assert visual_clash_crops[0]["source"] == "visual_clash:VC001"
    assert visual_clash_crops[0]["target_bbox_px"] == [10, 10, 12, 12]
    assert visual_clash_crops[0]["upscaled"] is True
    assert visual_clash_crops[0]["size_px"][0] == 600
    assert visual_clash_crops[1]["bbox_px"] == [60, 45, 120, 80]
    assert visual_clash_crops[1]["target_bbox_px"] == [90, 70, 120, 80]

    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "figure-agent.audit-crop-manifest.v1"
    assert manifest["fixture"] == "demo"
    assert manifest["render_path"] == "build/demo.png"
    assert manifest["required_crop_ids"] == sorted(
        item["id"] for item in manifest["crops"]
    )
    manifest_visual = [
        item for item in manifest["crops"] if item["kind"] == "visual_clash_crop"
    ]
    assert [item["visual_clash_ref"] for item in manifest_visual] == ["VC001", "VC002"]
    for crop in manifest["crops"]:
        assert isinstance(crop.get("sha256"), str)
        assert crop["sha256"].startswith("sha256:")
        assert len(crop["sha256"]) == len("sha256:") + 64
        assert crop["sha256"] == file_sha256(example_dir / crop["path"])


def test_build_zoom_crop_pack_writes_label_path_crops_and_manifest(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    _write_png(render, size=(1000, 500))
    (example_dir / "build" / "label_path_proximity.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.label-path-proximity.v1",
                "fixture": "demo",
                "render_pdf": "build/demo.pdf",
                "source": "spec.yaml:label_path_proximity_checks",
                "candidates": [
                    {
                        "id": "LP001",
                        "kind": "label_stacked_on_reference_line",
                        "text": "mobility edge",
                        "path_id": "mobility_edge_reference",
                        "path_role": "reference_line",
                        "bbox_pt": [100.0, 40.0, 150.0, 50.0],
                        "path_pt": {
                            "kind": "horizontal_line",
                            "y": 45.0,
                            "x_range": [90.0, 180.0],
                        },
                        "clearance_pt": 3.0,
                        "distance_pt": 0.0,
                    },
                ],
                "total": 1,
            }
        ),
        encoding="utf-8",
    )

    crops = build_zoom_crop_pack(
        example_dir,
        render,
        panel_crop_paths=(),
        pdf_page_size_cm=(10.0, 5.0),
    )

    label_path_crops = [item for item in crops if item["kind"] == "label_path_crop"]
    assert [item["id"] for item in label_path_crops] == ["LP001_mobility_edge"]
    assert label_path_crops[0]["path"].startswith("build/audit_crops/label_path/")
    assert (example_dir / label_path_crops[0]["path"]).is_file()
    assert label_path_crops[0]["label_path_ref"] == "LP001"
    assert label_path_crops[0]["source"] == "label_path:LP001"
    assert label_path_crops[0]["upscaled"] is True
    assert label_path_crops[0]["size_px"][0] == 600

    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_label_path = [
        item for item in manifest["crops"] if item["kind"] == "label_path_crop"
    ]
    assert [item["label_path_ref"] for item in manifest_label_path] == ["LP001"]
    assert manifest_label_path[0]["sha256"] == file_sha256(
        example_dir / manifest_label_path[0]["path"]
    )


def test_build_zoom_crop_pack_ignores_malformed_visual_clash_json(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    _write_png(render, size=(120, 80))
    (example_dir / "build" / "visual_clash.json").write_text("{", encoding="utf-8")

    crops = build_zoom_crop_pack(example_dir, render, panel_crop_paths=())

    assert not any(item["kind"] == "visual_clash_crop" for item in crops)
    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert not any(item["kind"] == "visual_clash_crop" for item in manifest["crops"])


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
