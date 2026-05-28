#!/usr/bin/env python3
"""Build non-model aesthetic-class metrics against reference-learning anchors."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from critique_reference_pack import CritiqueReferencePackError, load_optional_reference_pack
from PIL import Image
from quality_manifest import file_sha256

METRICS_SCHEMA = "figure-agent.reference-aesthetic-metrics.v1"
METRIC_VERSION = "reference-aesthetic-metrics.v1"
OUTPUT_RELATIVE_PATH = Path("build/reference_aesthetic_metrics.json")


class ReferenceAestheticMetricsError(Exception):
    """Controlled error for reference-aesthetic metric generation."""


def _example_relative_path(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_reference_path(example_dir: Path, value: str) -> Path | None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return example_dir / path


def _round(value: float) -> float:
    return round(float(value), 6)


def _image_array(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0


def _palette_histogram(rgb: np.ndarray) -> np.ndarray:
    quantized = np.clip((rgb.reshape(-1, 3) * 4).astype(np.int16), 0, 3)
    flat = quantized[:, 0] * 16 + quantized[:, 1] * 4 + quantized[:, 2]
    counts = np.bincount(flat, minlength=64).astype(np.float64)
    total = counts.sum()
    if total == 0:
        return counts
    return counts / total


def _rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    maxc = rgb.max(axis=-1)
    minc = rgb.min(axis=-1)
    delta = maxc - minc
    hue = np.zeros_like(maxc)
    nonzero = delta > 1e-6

    red = (rgb[..., 0] == maxc) & nonzero
    green = (rgb[..., 1] == maxc) & nonzero
    blue = (rgb[..., 2] == maxc) & nonzero
    hue[red] = ((rgb[..., 1][red] - rgb[..., 2][red]) / delta[red]) % 6
    hue[green] = ((rgb[..., 2][green] - rgb[..., 0][green]) / delta[green]) + 2
    hue[blue] = ((rgb[..., 0][blue] - rgb[..., 1][blue]) / delta[blue]) + 4
    hue /= 6
    saturation = np.where(maxc > 1e-6, delta / maxc, 0)
    return np.stack([hue, saturation, maxc], axis=-1)


def _dominant_hue_family_count(rgb: np.ndarray) -> int:
    hsv = _rgb_to_hsv(rgb)
    mask = (hsv[..., 1] > 0.12) & (hsv[..., 2] < 0.98)
    if not bool(mask.any()):
        return 0
    hue_bins = np.floor(hsv[..., 0][mask] * 12).astype(np.int16)
    hue_bins = np.clip(hue_bins, 0, 11)
    counts = np.bincount(hue_bins, minlength=12)
    threshold = max(int(mask.sum() * 0.02), 1)
    return int((counts >= threshold).sum())


def _ink_mask(rgb: np.ndarray) -> np.ndarray:
    gray = rgb.mean(axis=-1)
    return gray < 0.96


def _edge_density(rgb: np.ndarray) -> float:
    gray = rgb.mean(axis=-1)
    horizontal = np.abs(np.diff(gray, axis=1)) > 0.08
    vertical = np.abs(np.diff(gray, axis=0)) > 0.08
    edge_pixels = int(horizontal.sum() + vertical.sum())
    possible = horizontal.size + vertical.size
    if possible == 0:
        return 0.0
    return edge_pixels / possible


def _coarse_occupancy(rgb: np.ndarray, *, grid: int = 8) -> np.ndarray:
    mask = _ink_mask(rgb)
    rows = np.array_split(mask, grid, axis=0)
    cells: list[bool] = []
    for row in rows:
        for cell in np.array_split(row, grid, axis=1):
            cells.append(bool(cell.any()))
    return np.asarray(cells, dtype=bool)


def _image_features(path: Path) -> dict[str, Any]:
    rgb = _image_array(path)
    ink_density = float(_ink_mask(rgb).mean())
    edge_density = _edge_density(rgb)
    return {
        "size_px": [int(rgb.shape[1]), int(rgb.shape[0])],
        "palette_histogram": _palette_histogram(rgb),
        "dominant_hue_family_count": _dominant_hue_family_count(rgb),
        "ink_density": _round(ink_density),
        "edge_density": _round(edge_density),
        "line_density_proxy": _round(edge_density / max(ink_density, 0.001)),
        "coarse_occupancy": _coarse_occupancy(rgb),
    }


def _compare_features(build: dict[str, Any], reference: dict[str, Any]) -> dict[str, float]:
    build_occupancy = build["coarse_occupancy"]
    reference_occupancy = reference["coarse_occupancy"]
    return {
        "palette_histogram_distance": _round(
            np.abs(build["palette_histogram"] - reference["palette_histogram"]).sum() / 2
        ),
        "dominant_hue_family_count_delta": _round(
            abs(build["dominant_hue_family_count"] - reference["dominant_hue_family_count"])
        ),
        "ink_density_delta": _round(abs(build["ink_density"] - reference["ink_density"])),
        "edge_density_delta": _round(abs(build["edge_density"] - reference["edge_density"])),
        "coarse_silhouette_occupancy_delta": _round(
            np.not_equal(build_occupancy, reference_occupancy).mean()
        ),
        "line_density_proxy_delta": _round(
            abs(build["line_density_proxy"] - reference["line_density_proxy"])
        ),
    }


def _feature_summary(features: dict[str, Any]) -> dict[str, Any]:
    return {
        "size_px": features["size_px"],
        "dominant_hue_family_count": features["dominant_hue_family_count"],
        "ink_density": features["ink_density"],
        "edge_density": features["edge_density"],
        "line_density_proxy": features["line_density_proxy"],
        "coarse_occupied_cell_count": int(features["coarse_occupancy"].sum()),
    }


def build_reference_aesthetic_metrics(example_dir: Path) -> dict[str, Any] | None:
    try:
        pack = load_optional_reference_pack(example_dir)
    except CritiqueReferencePackError as exc:
        message = f"critique_reference_pack.yaml invalid: {exc}"
        raise ReferenceAestheticMetricsError(message) from exc
    if pack is None:
        return None
    learning = pack.get("reference_learning")
    if not isinstance(learning, dict):
        return None

    name = example_dir.name
    build_path = example_dir / "build" / f"{name}.png"
    if not build_path.is_file():
        raise ReferenceAestheticMetricsError(f"missing build render: {build_path}")

    build_features = _image_features(build_path)
    comparisons: list[dict[str, Any]] = []
    skip_reasons: list[str] = []

    for item in learning.get("references", []):
        reference_path = _safe_reference_path(example_dir, str(item["path"]))
        if reference_path is None:
            skip_reasons.append(f"{item['path']}: reference path must be relative and safe")
            continue
        if not reference_path.is_file():
            skip_reasons.append(f"{item['path']}: reference image missing")
            continue

        reference_features = _image_features(reference_path)
        comparisons.append(
            {
                "reference_path": _example_relative_path(example_dir, reference_path),
                "reference_hash": file_sha256(reference_path),
                "roles": item["roles"],
                "allowed_transfer": item["allowed_transfer"],
                "forbidden_transfer": item["forbidden_transfer"],
                "metrics": _compare_features(build_features, reference_features),
                "reference_features": _feature_summary(reference_features),
            }
        )

    payload = {
        "schema": METRICS_SCHEMA,
        "metric_version": METRIC_VERSION,
        "fixture": name,
        "state": "measured" if comparisons else "skipped",
        "build_artifact": {
            "path": _example_relative_path(example_dir, build_path),
            "hash": file_sha256(build_path),
            "size_px": build_features["size_px"],
        },
        "build_features": _feature_summary(build_features),
        "comparisons": comparisons,
        "skip_reasons": skip_reasons,
    }

    output_path = example_dir / OUTPUT_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example_dir", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = build_reference_aesthetic_metrics(args.example_dir)
    except ReferenceAestheticMetricsError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if payload is None:
        print(f"SKIP: {args.example_dir.name} has no reference-learning contract")
        return 0
    output = args.example_dir / OUTPUT_RELATIVE_PATH
    print(f"{payload['state']}: wrote {_example_relative_path(args.example_dir, output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
