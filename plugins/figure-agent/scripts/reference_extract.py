"""Layer 2.5 reference analysis — extract coordinate hints from a fixture's
reference PNG.

Inputs:
  examples/<name>/spec.yaml   (must declare reference_image: <relative path>)
  examples/<name>/<reference> (the actual PNG)

Output:
  examples/<name>/coordinate_hints.yaml

The hints carry two structures used as authoring + validation aid in Layer 3
(TikZ source authoring) and Layer 6 (validation gates):

  text_labels[]            OCR-detected labels with bbox + Tesseract confidence.
  palette_shape_clusters{} Connected components of pixels matching each
                           polymer-paper-preamble palette color, after a
                           per-color RGB-distance threshold and min component
                           size filter.

Per-color thresholds reflect empirical tuning on golden_target_001.png
(`output/reference_extract_test/`); see Phase E pre-flight agent report.

This module is *optional* — fixtures without `reference_image` skip cleanly
with a non-zero exit and a clear message. /fig_extract is intended for
golden-class fixtures; ordinary fixtures need not run it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image
from scipy.ndimage import find_objects, label

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inputs import parse_spec  # noqa: E402

EXTRACTION_VERSION = "0.1"

# polymer-paper-preamble.sty palette. Keep in sync with the .sty file; if a new
# palette color is added there, add it here too (no automatic discovery yet).
PALETTE: dict[str, tuple[int, int, int]] = {
    "cAmber": (0x99, 0x7A, 0x1E),
    "cBlue": (0x44, 0x77, 0xAA),
    "cRed": (0xCC, 0x66, 0x77),
    "cTeal": (0x44, 0xAA, 0x99),
    "cGray": (70, 70, 70),
    "cLGray": (200, 200, 200),
    "cBrown": (0x5D, 0x48, 0x20),
    "cArmAmber": (0x8B, 0x6F, 0x3E),
    "cAmberSphere": (0xDD, 0xCC, 0x77),
}

# Per-color RGB Euclidean threshold. Tuned empirically on golden_target_001.png
# to balance detection of meaningful shapes against anti-aliasing noise.
# Specific saturated palette colors get a tighter threshold; broad amber-tan
# tones get a looser one because the reference renders them desaturated.
COLOR_GROUP = {
    "cAmber": "specific",
    "cBlue": "specific",
    "cRed": "specific",
    "cTeal": "specific",
    "cBrown": "specific",
    "cArmAmber": "broad",
    "cAmberSphere": "broad",
    "cGray": "gray",
    "cLGray": "gray",
}
# Empirically calibrated against golden_target_001.png (LLM-rendered, lightly
# desaturated). Tighter thresholds (specific=40, gray=30) lost real palette
# regions like the amber lobe labels because the LLM render does not hit the
# exact palette hex; loosen to 55/35 with min_component=200 so true positives
# survive while cArmAmber-class noise stays bounded by the broad-tone cap.
GROUP_THRESHOLDS = {
    "specific": 55,
    "broad": 55,
    "gray": 35,
}

DEFAULT_MIN_COMPONENT_PIXELS = 200
DEFAULT_OCR_CONFIDENCE_FLOOR = 30.0
# 2x LANCZOS upsample lets Tesseract pick up small LLM-rendered labels
# (axis ticks, panel headers like "Experiment", "CB") that fail at native
# resolution. 3x or 4x degrades — anti-aliasing artifacts amplify and the
# detection set shrinks (measured on golden_target_001.png). 2x is the
# sweet spot empirically.
DEFAULT_OCR_UPSAMPLE_FACTOR = 2.0


def _hash_file(path: Path, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"{algo}:{h.hexdigest()}"


def _load_reference_rgb(reference_path: Path) -> np.ndarray:
    """Load the reference image as an HxWx3 uint8 array, dropping any alpha."""
    with Image.open(reference_path) as im:
        return np.array(im.convert("RGB"))


def palette_shape_clusters(
    image: np.ndarray,
    *,
    palette: dict[str, tuple[int, int, int]] | None = None,
    group_thresholds: dict[str, int] | None = None,
    color_group: dict[str, str] | None = None,
    min_component_pixels: int = DEFAULT_MIN_COMPONENT_PIXELS,
) -> dict[str, dict]:
    """Find connected components per palette color in the reference image.

    Returns:
        {color_name: {target_rgb, threshold, match_count, components: [...] }}
        Colors with no surviving component are omitted.
    """
    palette = palette or PALETTE
    group_thresholds = group_thresholds or GROUP_THRESHOLDS
    color_group = color_group or COLOR_GROUP

    # Upcast to int32 before subtracting and squaring: a single channel diff
    # can hit 255, and 255**2 = 65025 overflows int16 silently, which would
    # turn the whole-image dist_sq vector negative and match every pixel.
    rgb = image.astype(np.int32)
    out: dict[str, dict] = {}
    for color_name, target_rgb in palette.items():
        threshold = group_thresholds.get(color_group.get(color_name, "specific"), 40)
        diff = rgb - np.array(target_rgb, dtype=np.int32)
        dist_sq = (diff * diff).sum(axis=2)
        mask = dist_sq < (threshold * threshold)
        match_count = int(mask.sum())
        if match_count < min_component_pixels:
            continue
        labeled, ncomp = label(mask)
        slices = find_objects(labeled)
        components: list[dict] = []
        for idx, sl in enumerate(slices, start=1):
            if sl is None:
                continue
            ys, xs = sl
            comp_mask = labeled[sl] == idx
            pixel_count = int(comp_mask.sum())
            if pixel_count < min_component_pixels:
                continue
            components.append(
                {
                    "bbox": [int(xs.start), int(ys.start), int(xs.stop), int(ys.stop)],
                    "pixel_count": pixel_count,
                }
            )
        if not components:
            continue
        components.sort(key=lambda c: -c["pixel_count"])
        out[color_name] = {
            "target_rgb": list(target_rgb),
            "threshold": threshold,
            "match_count": match_count,
            "components": components,
        }
    return out


def ocr_text_labels(
    reference_path: Path,
    *,
    confidence_floor: float = DEFAULT_OCR_CONFIDENCE_FLOOR,
    upsample_factor: float = DEFAULT_OCR_UPSAMPLE_FACTOR,
) -> list[dict]:
    """Run Tesseract on the reference and return text labels with bbox+conf.

    When ``upsample_factor`` > 1, the image is enlarged with PIL LANCZOS
    before OCR, then bounding boxes are scaled back to the *original*
    image's coordinate system so downstream consumers (drift gate, status
    overlays) all share one reference frame.

    Raises FileNotFoundError if Tesseract is not on PATH.
    """
    import tempfile

    if shutil.which("tesseract") is None:
        raise FileNotFoundError(
            "tesseract not found on PATH. Install via 'brew install tesseract' (macOS),"
            " 'apt install tesseract-ocr' (Debian/Ubuntu), or skip OCR with --shapes-only."
        )
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


def _resolve_reference_path(example_dir: Path) -> Path | None:
    """Read spec.yaml and return the absolute reference_image path, or None."""
    spec_path = example_dir / "spec.yaml"
    if not spec_path.exists():
        return None
    spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    reference = spec.get("reference_image") if spec else None
    if not reference or not isinstance(reference, str) or not reference.strip():
        return None
    return example_dir / reference.strip()


def extract_coordinate_hints(
    example_dir: Path,
    *,
    rebuild: bool = False,
    min_component_pixels: int = DEFAULT_MIN_COMPONENT_PIXELS,
    confidence_floor: float = DEFAULT_OCR_CONFIDENCE_FLOOR,
    ocr_upsample_factor: float = DEFAULT_OCR_UPSAMPLE_FACTOR,
) -> tuple[Path | None, list[str]]:
    """Run OCR + palette clustering and write coordinate_hints.yaml.

    Returns (output_path, failure_messages). On success, output_path is the
    written file and failure_messages is empty. On skip (no reference_image,
    file missing) output_path is None and failure_messages explains why.
    """
    failures: list[str] = []
    reference_path = _resolve_reference_path(example_dir)
    if reference_path is None:
        return None, [
            f"{example_dir.name}: spec.yaml does not declare reference_image;"
            " /fig_extract is for fixtures with a fixed visual target (golden class)."
        ]
    if not reference_path.exists():
        return None, [f"{example_dir.name}: reference image not found at {reference_path}"]

    hints_path = example_dir / "coordinate_hints.yaml"
    if hints_path.exists() and not rebuild:
        if hints_path.stat().st_mtime >= reference_path.stat().st_mtime:
            return hints_path, [
                f"{example_dir.name}: coordinate_hints.yaml is up to date;"
                " pass --rebuild to overwrite."
            ]

    image = _load_reference_rgb(reference_path)
    height, width = image.shape[:2]
    clusters = palette_shape_clusters(image, min_component_pixels=min_component_pixels)

    text_labels: list[dict] = []
    ocr_status = "skipped (tesseract not available)"
    try:
        text_labels = ocr_text_labels(
            reference_path,
            confidence_floor=confidence_floor,
            upsample_factor=ocr_upsample_factor,
        )
        ocr_status = "ok"
    except FileNotFoundError as exc:
        failures.append(str(exc))

    payload = {
        "metadata": {
            "extraction_version": EXTRACTION_VERSION,
            "created_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "reference_image_path": str(reference_path.relative_to(example_dir)),
            "reference_image_hash": _hash_file(reference_path),
            "ocr_status": ocr_status,
            "parameters": {
                "min_component_pixels": min_component_pixels,
                "ocr_confidence_floor": confidence_floor,
                "ocr_upsample_factor": ocr_upsample_factor,
                "group_thresholds": GROUP_THRESHOLDS,
            },
        },
        "reference_image_size": [width, height],
        "text_labels": text_labels,
        "palette_shape_clusters": clusters,
    }
    hints_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return hints_path, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example_dir", type=Path)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="overwrite coordinate_hints.yaml even if it is fresh",
    )
    parser.add_argument(
        "--min-component-pixels",
        type=int,
        default=DEFAULT_MIN_COMPONENT_PIXELS,
        help="drop palette components smaller than this pixel count",
    )
    parser.add_argument(
        "--ocr-confidence-floor",
        type=float,
        default=DEFAULT_OCR_CONFIDENCE_FLOOR,
        help="drop OCR words below this Tesseract confidence",
    )
    parser.add_argument(
        "--ocr-upsample-factor",
        type=float,
        default=DEFAULT_OCR_UPSAMPLE_FACTOR,
        help="resample reference to this multiple of native size before OCR (1.0 = native)",
    )
    args = parser.parse_args()

    if not args.example_dir.is_dir():
        print(f"FAIL: example directory not found: {args.example_dir}", file=sys.stderr)
        return 1

    hints_path, failures = extract_coordinate_hints(
        args.example_dir,
        rebuild=args.rebuild,
        min_component_pixels=args.min_component_pixels,
        confidence_floor=args.ocr_confidence_floor,
        ocr_upsample_factor=args.ocr_upsample_factor,
    )
    if hints_path is None:
        for msg in failures:
            print(f"FAIL: {msg}", file=sys.stderr)
        return 1
    for msg in failures:
        print(f"WARN: {msg}", file=sys.stderr)
    payload = yaml.safe_load(hints_path.read_text(encoding="utf-8"))
    n_labels = len(payload.get("text_labels", []))
    n_clusters = len(payload.get("palette_shape_clusters", {}))
    n_components = sum(
        len(c["components"]) for c in payload.get("palette_shape_clusters", {}).values()
    )
    print(
        f"OK: extracted {n_labels} text labels, {n_clusters} palette colors"
        f" ({n_components} shape components) → {hints_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
