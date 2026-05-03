"""Layer 2.5 reference analysis — extract authoring hints from a fixture's
reference PNG.

Inputs:
  examples/<name>/spec.yaml   (must declare reference_image: <relative path>)
  examples/<name>/<reference> (the actual PNG)

Output:
  examples/<name>/coordinate_hints.yaml

The output feeds semantic TikZ authoring in Layer 3 plus layout drift validation
in Layer 6. It is authoring evidence, not final source. The active workflow is:

  reference PNG -> OCR + palette clusters + optional vtracer structural hints
  -> coordinate_hints.yaml -> semantic TikZ authoring

coordinate_hints.yaml can contain:

  text_labels[]            OCR-detected labels with bbox + Tesseract confidence.
  palette_shape_clusters{} Connected components of pixels matching each
                           polymer-paper-preamble palette color, after a
                           per-color RGB-distance threshold and min component
                           size filter.
  structural_regions{}     Optional vtracer-derived regions such as panel arcs,
                           border boxes, chain rows, S atom positions, trap
                           levels, plot boxes, plot curves, and lobes.

structural_regions.status may be ok, unavailable, or failed. If vtracer is
unavailable or fails, OCR + palette clusters still remain useful placement
evidence.

This module is *optional* — fixtures without `reference_image` skip cleanly
with a non-zero exit and a clear message. /fig_extract is intended for
golden-class fixtures; ordinary fixtures need not run it.

This file is a facade over three sub-modules:
  palette.py   palette-color connected-component clusters
  ocr.py       Tesseract OCR text labels
  vtrace.py    vtracer-based structural regions

Public API and CLI behavior are unchanged from the pre-split monolith.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inputs import parse_spec  # noqa: E402
from ocr import (  # noqa: E402
    DEFAULT_OCR_CONFIDENCE_FLOOR,
    DEFAULT_OCR_PASSES,
    DEFAULT_OCR_UPSAMPLE_FACTOR,
    ocr_text_labels,
)
from palette import (  # noqa: E402
    COLOR_GROUP,
    DEFAULT_MIN_COMPONENT_PIXELS,
    GROUP_THRESHOLDS,
    PALETTE,
    palette_shape_clusters,
)
from vtrace import (  # noqa: E402
    DEFAULT_CANVAS_WIDTH_CM,
    structural_regions_from_reference,
)

EXTRACTION_VERSION = "0.3"

__all__ = [
    "EXTRACTION_VERSION",
    "PALETTE",
    "COLOR_GROUP",
    "GROUP_THRESHOLDS",
    "DEFAULT_MIN_COMPONENT_PIXELS",
    "DEFAULT_OCR_CONFIDENCE_FLOOR",
    "DEFAULT_OCR_UPSAMPLE_FACTOR",
    "DEFAULT_OCR_PASSES",
    "DEFAULT_CANVAS_WIDTH_CM",
    "palette_shape_clusters",
    "ocr_text_labels",
    "structural_regions_from_reference",
    "extract_coordinate_hints",
]


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
    ocr_passes: tuple[float, ...] = DEFAULT_OCR_PASSES,
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
            ocr_passes=ocr_passes,
        )
        ocr_status = "ok"
    except FileNotFoundError as exc:
        failures.append(str(exc))

    structural = structural_regions_from_reference(reference_path, (width, height))

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
                "ocr_passes": list(ocr_passes),
                "group_thresholds": GROUP_THRESHOLDS,
            },
        },
        "reference_image_size": [width, height],
        "text_labels": text_labels,
        "palette_shape_clusters": clusters,
        "structural_regions": structural,
    }
    hints_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return hints_path, failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
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
        "--ocr-passes",
        type=float,
        nargs="+",
        default=list(DEFAULT_OCR_PASSES),
        help=(
            "one or more upsample factors; OCR runs once per factor and the"
            " results are concatenated (e.g. --ocr-passes 1.0 2.0)"
        ),
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
        ocr_passes=tuple(args.ocr_passes),
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
    sr_status = payload.get("structural_regions", {}).get("status", "n/a")
    print(
        f"OK: extracted {n_labels} text labels, {n_clusters} palette colors"
        f" ({n_components} shape components), structural_regions: {sr_status}"
        f" → {hints_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
