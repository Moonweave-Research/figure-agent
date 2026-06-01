"""Tests for the v0.4.2 perception data-only pack."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import perception_pack as perception_pack_mod  # noqa: E402
from perception_pack import build_perception_pack  # noqa: E402

FIG1_DIR = REPO_ROOT / "examples" / "fig1_overview_v2"
FIG1_PDF = FIG1_DIR / "build" / "fig1_overview_v2.pdf"
FIG1_PNG = FIG1_DIR / "build" / "fig1_overview_v2.png"


def _require_fig1_build() -> None:
    if not FIG1_PDF.exists() or not FIG1_PNG.exists():
        pytest.skip(f"{FIG1_PDF} and {FIG1_PNG} not present; run /fig_compile fig1_overview_v2")


def _minimal_extract() -> dict:
    return {
        "schema_version": "0.4.2",
        "source": {"pdf_path": "", "pdf_size_cm": [1.0, 1.0]},
        "coordinate_space": {
            "pdf_origin": "top_left",
            "y_axis": "down",
            "units": "cm",
        },
        "primitives": {"lines": [], "curves": [], "rects": [], "chars": []},
        "counts": {
            "lines": 0,
            "curves": 0,
            "rects": 0,
            "chars": 0,
            "endpoints_total": 0,
        },
    }


def test_perception_pack_rejects_unsafe_name_before_resetting_cwd_perception(
    tmp_path,
    monkeypatch,
) -> None:
    build_dir = tmp_path / "build"
    perception_dir = build_dir / "perception"
    perception_dir.mkdir(parents=True)
    sentinel = perception_dir / "keep.txt"
    sentinel.write_text("preserve me", encoding="utf-8")
    (tmp_path / "outside.pdf").write_bytes(b"%PDF-1.7\n")
    (tmp_path / "outside.png").write_bytes(b"png")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(perception_pack_mod, "_extract_pdf", lambda _pdf_path: _minimal_extract())
    monkeypatch.setattr(perception_pack_mod, "_write_overlay", lambda *_args: None)

    with pytest.raises(ValueError, match="single examples/<name> directory name"):
        build_perception_pack("../outside")

    assert sentinel.read_text(encoding="utf-8") == "preserve me"


def test_perception_pack_preserves_safe_cwd_mode(tmp_path, monkeypatch) -> None:
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "local_fig.pdf").write_bytes(b"%PDF-1.7\n")
    (build_dir / "local_fig.png").write_bytes(b"png")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(perception_pack_mod, "_extract_pdf", lambda _pdf_path: _minimal_extract())
    monkeypatch.setattr(perception_pack_mod, "_write_overlay", lambda *_args: None)

    build_perception_pack("local_fig")

    extract_path = build_dir / "perception" / "extract.yaml"
    extract = yaml.safe_load(extract_path.read_text(encoding="utf-8"))
    assert extract["source"]["pdf_path"].endswith("build/local_fig.pdf")


def test_perception_pack_cli_rejects_unsafe_name_cleanly(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["perception_pack.py", "../outside"])

    assert perception_pack_mod.main() == 1

    captured = capsys.readouterr()
    assert "single examples/<name> directory name" in captured.err
    assert "Traceback" not in captured.err


def test_perception_pack_cli_does_not_mask_later_value_errors(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["perception_pack.py", "safe_name"])

    def fail_after_name_validation(_name: str) -> None:
        raise ValueError("later extraction failure")

    monkeypatch.setattr(perception_pack_mod, "build_perception_pack", fail_after_name_validation)

    with pytest.raises(ValueError, match="later extraction failure"):
        perception_pack_mod.main()


def test_perception_pack_writes_locked_outputs_and_schema(monkeypatch) -> None:
    _require_fig1_build()
    monkeypatch.chdir(REPO_ROOT)

    build_perception_pack("fig1_overview_v2")

    perception_dir = FIG1_DIR / "build" / "perception"
    extract_path = perception_dir / "extract.yaml"
    overlay_path = perception_dir / "overlay.png"
    assert extract_path.exists()
    assert overlay_path.exists()

    generated_names = {path.name for path in perception_dir.iterdir() if path.is_file()}
    assert generated_names == {"extract.yaml", "overlay.png"}

    data = yaml.safe_load(extract_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "0.4.2"
    assert data["source"]["pdf_path"] == "examples/fig1_overview_v2/build/fig1_overview_v2.pdf"
    # Lock the current fig1_overview_v2 dogfood render contract.
    assert data["source"]["pdf_size_cm"] == pytest.approx([18.08, 11.22], abs=0.02)
    assert data["coordinate_space"] == {
        "pdf_origin": "top_left",
        "y_axis": "down",
        "units": "cm",
    }
    assert set(data["primitives"]) == {"lines", "curves", "rects", "chars"}
    assert set(data["counts"]) == {"lines", "curves", "rects", "chars", "endpoints_total"}

    assert data["counts"]["lines"] == pytest.approx(41, abs=3)
    assert data["counts"]["curves"] == pytest.approx(140, abs=3)
    assert data["counts"]["rects"] == pytest.approx(11, abs=3)
    assert data["counts"]["chars"] == pytest.approx(304, abs=3)
    assert data["counts"]["endpoints_total"] == pytest.approx(368, abs=3)

    assert set(data["primitives"]["lines"][0]) == {
        "id",
        "x0",
        "y0",
        "x1",
        "y1",
        "stroke_rgb",
        "linewidth_pt",
    }
    assert set(data["primitives"]["curves"][0]) == {
        "id",
        "pts",
        "stroke_rgb",
        "linewidth_pt",
        "fill_rgb",
    }
    assert set(data["primitives"]["rects"][0]) == {
        "id",
        "x0",
        "y0",
        "x1",
        "y1",
        "stroke_rgb",
        "fill_rgb",
    }
    assert set(data["primitives"]["chars"][0]) == {
        "id",
        "text",
        "x0",
        "y0",
        "x1",
        "y1",
        "fontname",
        "size_pt",
    }

    with Image.open(overlay_path) as overlay:
        overlay.verify()
