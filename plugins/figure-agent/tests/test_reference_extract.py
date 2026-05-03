"""Tests for scripts/reference_extract.py — Layer 2.5 coordinate hints."""

from __future__ import annotations

import builtins
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from reference_extract import (  # noqa: E402
    EXTRACTION_VERSION,
    PALETTE,
    extract_coordinate_hints,
    ocr_text_labels,
    palette_shape_clusters,
)

TESSERACT_AVAILABLE = shutil.which("tesseract") is not None


def _make_palette_image(size: tuple[int, int], regions: dict) -> np.ndarray:
    """Build a synthetic RGB image with rectangular palette-color regions."""
    arr = np.full((size[1], size[0], 3), 255, dtype=np.uint8)
    for color_name, ((x1, y1, x2, y2)) in regions.items():
        rgb = PALETTE[color_name]
        arr[y1:y2, x1:x2] = rgb
    return arr


def test_palette_shape_clusters_detects_synthetic_blocks() -> None:
    image = _make_palette_image(
        (200, 200),
        {
            "cAmber": (10, 10, 60, 60),
            "cBlue": (100, 100, 180, 180),
        },
    )
    clusters = palette_shape_clusters(image, min_component_pixels=200)
    assert "cAmber" in clusters
    assert "cBlue" in clusters
    amber_components = clusters["cAmber"]["components"]
    blue_components = clusters["cBlue"]["components"]
    assert len(amber_components) == 1
    assert len(blue_components) == 1
    assert amber_components[0]["bbox"] == [10, 10, 60, 60]
    assert blue_components[0]["bbox"] == [100, 100, 180, 180]


def test_palette_shape_clusters_drops_subthreshold_components() -> None:
    """A 5x5 cAmber blob is far below min_component_pixels=200 and must drop."""
    image = _make_palette_image(
        (50, 50),
        {"cAmber": (10, 10, 15, 15)},  # 25 pixels
    )
    clusters = palette_shape_clusters(image, min_component_pixels=200)
    assert "cAmber" not in clusters


def test_palette_shape_clusters_handles_pure_white() -> None:
    """An all-white image must not match any palette color."""
    image = np.full((100, 100, 3), 255, dtype=np.uint8)
    clusters = palette_shape_clusters(image, min_component_pixels=200)
    assert clusters == {}


def test_palette_shape_clusters_separates_two_components_of_same_color() -> None:
    image = _make_palette_image(
        (200, 200),
        {"cTeal": (10, 10, 50, 50)},
    )
    # Add a second teal block far away
    image[100:140, 100:140] = PALETTE["cTeal"]
    clusters = palette_shape_clusters(image, min_component_pixels=200)
    assert len(clusters["cTeal"]["components"]) == 2


def test_extract_skips_when_spec_missing_reference_image(tmp_path: Path) -> None:
    fixture = tmp_path / "noRef"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: noRef\npanels: []\n", encoding="utf-8")
    out, failures = extract_coordinate_hints(fixture)
    assert out is None
    assert any("does not declare reference_image" in f for f in failures)


def test_extract_skips_when_reference_file_missing(tmp_path: Path) -> None:
    fixture = tmp_path / "missingRef"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text(
        "name: missingRef\nreference_image: reference/ghost.png\n",
        encoding="utf-8",
    )
    out, failures = extract_coordinate_hints(fixture)
    assert out is None
    assert any("reference image not found" in f for f in failures)


def test_extract_writes_hints_for_synthetic_palette_image(tmp_path: Path) -> None:
    fixture = tmp_path / "synthFixture"
    fixture.mkdir()
    (fixture / "reference").mkdir()
    ref = fixture / "reference" / "synth.png"
    image_arr = _make_palette_image(
        (300, 300),
        {
            "cAmber": (20, 20, 80, 80),
            "cBlue": (150, 150, 220, 220),
        },
    )
    Image.fromarray(image_arr).save(ref)
    (fixture / "spec.yaml").write_text(
        "name: synthFixture\nreference_image: reference/synth.png\n",
        encoding="utf-8",
    )
    out, failures = extract_coordinate_hints(fixture)
    assert out is not None
    payload = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert payload["metadata"]["extraction_version"] == EXTRACTION_VERSION
    assert payload["reference_image_size"] == [300, 300]
    assert "cAmber" in payload["palette_shape_clusters"]
    assert "cBlue" in payload["palette_shape_clusters"]
    # OCR should either succeed (no labels in synthetic image, list could be
    # empty) or be flagged as skipped if tesseract is missing.
    assert isinstance(payload["text_labels"], list)
    if TESSERACT_AVAILABLE:
        assert payload["metadata"]["ocr_status"] == "ok"
    else:
        assert payload["metadata"]["ocr_status"].startswith("skipped")
        assert any("tesseract" in f.lower() for f in failures)


def test_extract_respects_rebuild_flag(tmp_path: Path) -> None:
    fixture = tmp_path / "freshFixture"
    fixture.mkdir()
    (fixture / "reference").mkdir()
    ref = fixture / "reference" / "synth.png"
    Image.fromarray(_make_palette_image((200, 200), {"cAmber": (10, 10, 60, 60)})).save(ref)
    (fixture / "spec.yaml").write_text(
        "name: freshFixture\nreference_image: reference/synth.png\n",
        encoding="utf-8",
    )
    # First write
    first, _ = extract_coordinate_hints(fixture)
    assert first is not None
    first_mtime = first.stat().st_mtime

    # Without --rebuild and reference unchanged, the up-to-date hints stay
    second, msgs = extract_coordinate_hints(fixture, rebuild=False)
    assert second is not None
    assert second.stat().st_mtime == first_mtime
    assert any("up to date" in m for m in msgs)

    # With --rebuild the file is rewritten (mtime advances on most filesystems
    # but we cannot guarantee strict monotonicity within the same second; just
    # require that the call succeeds and returns a path).
    third, _ = extract_coordinate_hints(fixture, rebuild=True)
    assert third is not None


def test_extract_handles_rgba_input(tmp_path: Path) -> None:
    """RGBA reference images must convert cleanly to RGB; the alpha channel
    is dropped so palette matching does not depend on it."""
    fixture = tmp_path / "rgbaFixture"
    fixture.mkdir()
    (fixture / "reference").mkdir()
    ref = fixture / "reference" / "synth.png"
    arr = _make_palette_image((200, 200), {"cAmber": (10, 10, 80, 80)})
    rgba = np.dstack([arr, np.full((200, 200), 128, dtype=np.uint8)])  # alpha=128
    Image.fromarray(rgba, mode="RGBA").save(ref)
    (fixture / "spec.yaml").write_text(
        "name: rgbaFixture\nreference_image: reference/synth.png\n",
        encoding="utf-8",
    )
    out, _ = extract_coordinate_hints(fixture)
    assert out is not None
    payload = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert "cAmber" in payload["palette_shape_clusters"]


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="tesseract not installed")
def test_ocr_text_labels_recovers_simple_words(tmp_path: Path) -> None:
    """Render a couple of words at high contrast and assert OCR finds them."""
    from PIL import ImageDraw, ImageFont

    img = Image.new("RGB", (400, 100), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
    except Exception:
        font = ImageFont.load_default()
    draw.text((20, 30), "Experiment", fill="black", font=font)
    ref = tmp_path / "synth_text.png"
    img.save(ref)

    labels = ocr_text_labels(ref, confidence_floor=20)
    joined = " ".join(label["text"] for label in labels)
    assert "Experiment" in joined


def test_ocr_text_labels_raises_when_tesseract_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("ocr.shutil.which", lambda name: None)
    ref = tmp_path / "synth.png"
    Image.new("RGB", (50, 50), "white").save(ref)
    with pytest.raises(FileNotFoundError):
        ocr_text_labels(ref)


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="tesseract not installed")
def test_ocr_upsample_returns_bbox_in_original_coordinate_frame(tmp_path: Path) -> None:
    """2x upsample must scale bbox back, so coords stay in the native frame."""
    from PIL import ImageDraw, ImageFont

    img = Image.new("RGB", (400, 100), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
    except Exception:
        font = ImageFont.load_default()
    draw.text((20, 30), "Experiment", fill="black", font=font)
    ref = tmp_path / "synth_text.png"
    img.save(ref)

    labels_2x = ocr_text_labels(ref, confidence_floor=20, ocr_passes=(2.0,))
    assert labels_2x, "2x upsample should still detect 'Experiment'"
    for label in labels_2x:
        x1, y1, x2, y2 = label["bbox"]
        assert 0 <= x1 < x2 <= img.width
        assert 0 <= y1 < y2 <= img.height


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="tesseract not installed")
def test_extract_coordinate_hints_records_ocr_passes(tmp_path: Path) -> None:
    """metadata.parameters.ocr_passes must be recorded for reproducibility."""
    example = tmp_path / "fixture"
    example.mkdir()
    (example / "spec.yaml").write_text(yaml.safe_dump({"panels": [], "reference_image": "ref.png"}))
    Image.new("RGB", (200, 100), "white").save(example / "ref.png")

    hints_path, _ = extract_coordinate_hints(example, ocr_passes=(1.0, 2.0))
    assert hints_path is not None
    payload = yaml.safe_load(hints_path.read_text())
    assert payload["metadata"]["parameters"]["ocr_passes"] == [1.0, 2.0]


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="tesseract not installed")
def test_ocr_text_labels_concatenates_multi_pass_results(tmp_path: Path) -> None:
    """Multi-pass OCR returns the union of per-pass detections (no dedup)."""
    from PIL import ImageDraw, ImageFont

    img = Image.new("RGB", (400, 100), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
    except Exception:
        font = ImageFont.load_default()
    draw.text((20, 30), "Experiment", fill="black", font=font)
    ref = tmp_path / "synth.png"
    img.save(ref)

    one_pass = ocr_text_labels(ref, confidence_floor=20, ocr_passes=(2.0,))
    two_pass = ocr_text_labels(ref, confidence_floor=20, ocr_passes=(1.0, 2.0))
    assert len(two_pass) >= len(one_pass)


def test_structural_regions_unavailable_when_vtracer_missing(tmp_path, monkeypatch):
    """structural_regions.status == 'unavailable' when vtracer cannot be imported."""
    real_import = builtins.__import__

    def _block_vtracer(name, *args, **kwargs):
        if name == "vtracer":
            raise ImportError("vtracer blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "vtracer", raising=False)
    monkeypatch.setattr(builtins, "__import__", _block_vtracer)

    # Minimal fixture: 10x10 white image
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    ref_path = tmp_path / "ref.png"
    img.save(ref_path)
    spec_content = "name: test_fix\nreference_image: ref.png\naccepted: false\n"
    (tmp_path / "spec.yaml").write_text(spec_content)

    hints_path, _ = extract_coordinate_hints(tmp_path, rebuild=True)
    assert hints_path is not None
    payload = yaml.safe_load(hints_path.read_text())
    assert payload["structural_regions"]["status"] == "unavailable"
    # Core extractions still work
    assert "text_labels" in payload
    assert "palette_shape_clusters" in payload
