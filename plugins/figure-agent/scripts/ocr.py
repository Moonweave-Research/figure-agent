"""Tesseract OCR text-label detection from a reference PNG.

Layer 2.5 sub-module of `reference_extract`. Runs Tesseract one or more
times at different scales and concatenates results, scaling bboxes back to
the original image's coordinate frame so downstream consumers (drift gate,
status overlays) all share one reference frame.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

DEFAULT_OCR_CONFIDENCE_FLOOR = 30.0
# 2x LANCZOS upsample lets Tesseract pick up small LLM-rendered labels
# (axis ticks, panel headers like "Experiment", "CB") that fail at native
# resolution. 3x or 4x degrades — anti-aliasing artifacts amplify and the
# detection set shrinks (measured on golden_target_001.png). 2x is the
# sweet spot empirically.
#
# Multi-pass: native + 2x recovers the small set of short symbols (e.g. VB)
# that Tesseract reads at 1× but loses at 2× because LANCZOS over-blurs
# tight ascender/descender pairs. The drift gate's spatial matcher picks
# the closest candidate per phrase, so duplicate detections from the two
# passes do not need de-duplication here.
DEFAULT_OCR_UPSAMPLE_FACTOR = 2.0
# Two passes: native (1.0×) recovers short symbols (CB, VB, n, τ) that LANCZOS
# over-blurs at 2×; 2× recovers small axis-tick labels that native resolution
# loses. Spatial matcher in the drift gate deduplicates by closest candidate.
DEFAULT_OCR_PASSES: tuple[float, ...] = (1.0, 2.0)


def _run_ocr_at_scale(
    reference_path: Path,
    upsample_factor: float,
    confidence_floor: float,
) -> list[dict]:
    """Run a single Tesseract pass at the given scale; return labels in native coords."""

    with tempfile.TemporaryDirectory() as td:
        # Tesseract appends ".tsv" to the output base path, so the base must
        # not already carry an extension or .with_suffix-style replacement
        # paths will not align.
        out_base = Path(td) / "ocr_out"
        if upsample_factor and upsample_factor != 1.0:
            with Image.open(reference_path) as src:
                src_rgb = src.convert("RGB")
                new_size = (
                    int(round(src_rgb.width * upsample_factor)),
                    int(round(src_rgb.height * upsample_factor)),
                )
                upsampled = src_rgb.resize(new_size, Image.LANCZOS)
            scaled_path = Path(td) / "upsampled.png"
            upsampled.save(scaled_path)
            ocr_target = scaled_path
        else:
            ocr_target = reference_path
        proc = subprocess.run(
            ["tesseract", str(ocr_target), str(out_base), "tsv"],
            capture_output=True,
            text=True,
            errors="replace",
        )
        tsv_path = out_base.with_name(out_base.name + ".tsv")
        if proc.returncode != 0 or not tsv_path.exists():
            raise RuntimeError(f"tesseract failed: rc={proc.returncode} stderr={proc.stderr}")
        lines = tsv_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    try:
        text_idx = header.index("text")
        conf_idx = header.index("conf")
        left_idx = header.index("left")
        top_idx = header.index("top")
        width_idx = header.index("width")
        height_idx = header.index("height")
    except ValueError as exc:
        raise RuntimeError(f"unexpected tesseract TSV header: {header}") from exc
    scale_back = 1.0 / upsample_factor if upsample_factor and upsample_factor != 1.0 else 1.0
    out: list[dict] = []
    for raw in lines[1:]:
        cols = raw.split("\t")
        if len(cols) <= text_idx:
            continue
        text = cols[text_idx].strip()
        if not text:
            continue
        try:
            conf = float(cols[conf_idx])
            left = int(cols[left_idx])
            top = int(cols[top_idx])
            w = int(cols[width_idx])
            h = int(cols[height_idx])
        except (ValueError, IndexError):
            continue
        if conf < confidence_floor:
            continue
        x1 = int(round(left * scale_back))
        y1 = int(round(top * scale_back))
        x2 = int(round((left + w) * scale_back))
        y2 = int(round((top + h) * scale_back))
        out.append(
            {
                "text": text,
                "bbox": [x1, y1, x2, y2],
                "conf": conf,
            }
        )
    return out


def ocr_text_labels(
    reference_path: Path,
    *,
    confidence_floor: float = DEFAULT_OCR_CONFIDENCE_FLOOR,
    ocr_passes: tuple[float, ...] = DEFAULT_OCR_PASSES,
) -> list[dict]:
    """Run Tesseract one or more times at different scales and concat results.

    Each pass enlarges the image with PIL LANCZOS, runs Tesseract, then scales
    the bounding boxes back to the *original* image's coordinate system so
    downstream consumers (drift gate, status overlays) all share one reference
    frame. Pass list is small (typically 1–2 entries); duplicate detections
    across passes are not de-duplicated because the drift gate's spatial
    matcher already picks the closest candidate per phrase.

    Raises FileNotFoundError if Tesseract is not on PATH.
    """
    if shutil.which("tesseract") is None:
        raise FileNotFoundError(
            "tesseract not found on PATH. Install via 'brew install tesseract' (macOS),"
            " 'apt install tesseract-ocr' (Debian/Ubuntu), or skip OCR with --shapes-only."
        )
    if not ocr_passes:
        return []
    out: list[dict] = []
    for factor in ocr_passes:
        out.extend(_run_ocr_at_scale(reference_path, factor, confidence_floor))
    return out
