#!/usr/bin/env python3
"""Build non-model aesthetic-class metrics against reference-learning anchors."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import fixture_identity
import numpy as np
from critique_reference_pack import CritiqueReferencePackError, load_optional_reference_pack
from PIL import Image, UnidentifiedImageError
from quality_manifest import file_sha256

METRICS_SCHEMA = "figure-agent.reference-aesthetic-metrics.v1"
METRIC_VERSION = "reference-aesthetic-metrics.v1"
OUTPUT_RELATIVE_PATH = Path("build/reference_aesthetic_metrics.json")
SEVERE_THRESHOLDS = {
    "palette_histogram_distance": 0.55,
    "dominant_hue_family_count_delta": 4.0,
    "ink_density_delta": 0.35,
    "edge_density_delta": 0.12,
    "coarse_silhouette_occupancy_delta": 0.5,
    "line_density_proxy_delta": 1.0,
}
WARNING_THRESHOLDS = {
    "palette_histogram_distance": 0.25,
    "dominant_hue_family_count_delta": 2.0,
    "ink_density_delta": 0.15,
    "edge_density_delta": 0.05,
    "coarse_silhouette_occupancy_delta": 0.25,
    "line_density_proxy_delta": 0.4,
}


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
    saturation = np.zeros_like(maxc)
    np.divide(delta, maxc, out=saturation, where=maxc > 1e-6)
    return np.stack([hue, saturation, maxc], axis=-1)


def _dominant_hue_family_count(rgb: np.ndarray) -> int:
    hsv = _rgb_to_hsv(rgb)
    mask = hsv[..., 1] > 0.12
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

    try:
        build_features = _image_features(build_path)
    except (UnidentifiedImageError, OSError) as exc:
        raise ReferenceAestheticMetricsError(f"unreadable build render: {build_path}") from exc
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

        try:
            reference_features = _image_features(reference_path)
        except (UnidentifiedImageError, OSError):
            skip_reasons.append(f"{item['path']}: reference image unreadable")
            continue
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
        "reference_pack": {
            "path": "critique_reference_pack.yaml",
            "hash": file_sha256(example_dir / "critique_reference_pack.yaml"),
        },
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


def _base_summary(example_dir: Path, state: str) -> dict[str, Any]:
    return {
        "schema": METRICS_SCHEMA,
        "metric_version": METRIC_VERSION,
        "fixture": example_dir.name,
        "evaluation_state": state,
        "evidence_path": OUTPUT_RELATIVE_PATH.as_posix(),
        "comparison_count": 0,
        "severe_metric_count": 0,
        "blocking_items": [],
        "next_action": "",
    }


def _metrics_payload(example_dir: Path) -> tuple[dict[str, Any] | None, str | None]:
    output_path = example_dir / OUTPUT_RELATIVE_PATH
    if not output_path.is_file():
        return None, None
    try:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)
    if not isinstance(payload, dict):
        return None, "metrics payload must be a mapping"
    return payload, None


def _payload_reference_pack_stale(example_dir: Path, payload: dict[str, Any]) -> bool:
    current_path = example_dir / "critique_reference_pack.yaml"
    reference_pack = payload.get("reference_pack")
    if not current_path.is_file() or not isinstance(reference_pack, dict):
        return True
    return reference_pack.get("hash") != file_sha256(current_path)


def _artifact_stale(example_dir: Path, artifact: dict[str, Any]) -> str | None:
    path_value = artifact.get("path")
    hash_value = artifact.get("hash")
    if not isinstance(path_value, str) or not isinstance(hash_value, str):
        return "build artifact metadata"
    artifact_path = example_dir / path_value
    if not artifact_path.is_file() or file_sha256(artifact_path) != hash_value:
        return path_value
    return None


def _reference_stale(example_dir: Path, comparison: dict[str, Any]) -> str | None:
    path_value = comparison.get("reference_path")
    hash_value = comparison.get("reference_hash")
    if not isinstance(path_value, str) or not isinstance(hash_value, str):
        return "reference metadata"
    reference_path = example_dir / path_value
    if not reference_path.is_file() or file_sha256(reference_path) != hash_value:
        return path_value
    return None


def _readded_references(
    example_dir: Path,
    learning: dict[str, Any],
    comparisons: list[Any],
) -> list[str]:
    """Find references the pack declares that are now readable but were skipped at build time."""
    recorded = {
        comparison.get("reference_path")
        for comparison in comparisons
        if isinstance(comparison, dict)
    }
    readded: list[str] = []
    for item in learning.get("references", []):
        reference_path = _safe_reference_path(example_dir, str(item["path"]))
        if reference_path is None or not reference_path.is_file():
            continue
        relative = _example_relative_path(example_dir, reference_path)
        if relative in recorded:
            continue
        try:
            _image_features(reference_path)
        except (UnidentifiedImageError, OSError):
            continue
        readded.append(relative)
    return readded


def _threshold_metrics(
    payload: dict[str, Any],
    thresholds: dict[str, float],
) -> list[dict[str, Any]]:
    flagged: list[dict[str, Any]] = []
    for comparison in payload.get("comparisons", []):
        if not isinstance(comparison, dict):
            continue
        reference_path = comparison.get("reference_path", "<unknown reference>")
        metrics = comparison.get("metrics")
        if not isinstance(metrics, dict):
            continue
        for metric_name, threshold in thresholds.items():
            value = metrics.get(metric_name)
            if isinstance(value, int | float) and float(value) > threshold:
                flagged.append(
                    {
                        "reference_path": reference_path,
                        "metric": metric_name,
                        "value": _round(float(value)),
                        "threshold": threshold,
                    }
                )
    return flagged


def reference_aesthetic_metrics_summary(example_dir: Path) -> dict[str, Any] | None:
    """Summarize opt-in reference-aesthetic metrics without generating them."""
    try:
        pack = load_optional_reference_pack(example_dir)
    except CritiqueReferencePackError as exc:
        summary = _base_summary(example_dir, "invalid")
        summary["reason"] = f"critique_reference_pack.yaml invalid: {exc}"
        summary["next_action"] = "fix critique_reference_pack.yaml"
        return summary
    learning = pack.get("reference_learning") if pack is not None else None
    if not isinstance(learning, dict):
        return None

    payload, error = _metrics_payload(example_dir)
    if error is not None:
        summary = _base_summary(example_dir, "invalid")
        summary["reason"] = f"{OUTPUT_RELATIVE_PATH.as_posix()} invalid: {error}"
        summary["next_action"] = (
            f"rerun scripts/reference_aesthetic_metrics.py {example_dir.as_posix()}"
        )
        return summary
    if payload is None:
        summary = _base_summary(example_dir, "missing")
        summary["next_action"] = (
            f"run scripts/reference_aesthetic_metrics.py {example_dir.as_posix()}"
        )
        return summary
    if (
        payload.get("schema") != METRICS_SCHEMA
        or payload.get("metric_version") != METRIC_VERSION
        or payload.get("fixture") != example_dir.name
    ):
        summary = _base_summary(example_dir, "invalid")
        summary["reason"] = "metrics schema, version, or fixture mismatch"
        summary["next_action"] = (
            f"rerun scripts/reference_aesthetic_metrics.py {example_dir.as_posix()}"
        )
        return summary

    blocking_items: list[str] = []
    if _payload_reference_pack_stale(example_dir, payload):
        blocking_items.append("critique_reference_pack.yaml")
    artifact = payload.get("build_artifact")
    if not isinstance(artifact, dict):
        blocking_items.append("build artifact metadata")
    else:
        stale_item = _artifact_stale(example_dir, artifact)
        if stale_item is not None:
            blocking_items.append(stale_item)
    comparisons = payload.get("comparisons", [])
    if not isinstance(comparisons, list):
        summary = _base_summary(example_dir, "invalid")
        summary["reason"] = "metrics comparisons must be a list"
        summary["next_action"] = (
            f"rerun scripts/reference_aesthetic_metrics.py {example_dir.as_posix()}"
        )
        return summary
    for comparison in comparisons:
        if not isinstance(comparison, dict):
            blocking_items.append("reference metadata")
            continue
        stale_item = _reference_stale(example_dir, comparison)
        if stale_item is not None:
            blocking_items.append(stale_item)
    blocking_items.extend(_readded_references(example_dir, learning, comparisons))
    if blocking_items:
        summary = _base_summary(example_dir, "stale")
        summary["comparison_count"] = len(comparisons)
        summary["blocking_items"] = sorted(dict.fromkeys(blocking_items))
        summary["next_action"] = (
            f"rerun scripts/reference_aesthetic_metrics.py {example_dir.as_posix()}"
        )
        return summary

    summary = _base_summary(
        example_dir,
        "passed" if payload.get("state") == "measured" else "skipped",
    )
    summary["comparison_count"] = len(comparisons)
    summary["skip_reasons"] = payload.get("skip_reasons", [])
    severe = _threshold_metrics(payload, SEVERE_THRESHOLDS)
    if severe:
        summary["evaluation_state"] = "severe_divergence"
        summary["severe_metric_count"] = len(severe)
        summary["severe_metrics"] = severe
        summary["blocking_items"] = sorted(
            {f"{item['reference_path']}:{item['metric']}" for item in severe}
        )
        summary["next_action"] = (
            "review reference_aesthetic_metrics.json and route aesthetic-class "
            "divergence to human or agent critique"
        )
    else:
        warnings = _threshold_metrics(payload, WARNING_THRESHOLDS)
        if warnings:
            summary["evaluation_state"] = "warning"
            summary["warning_metric_count"] = len(warnings)
            summary["warning_metrics"] = warnings
            summary["next_action"] = (
                "review reference_aesthetic_metrics.json before declaring aesthetic class alignment"
            )
        elif summary["evaluation_state"] == "skipped":
            summary["next_action"] = "provide at least one readable reference-learning image"
        else:
            summary["next_action"] = "no reference aesthetic metric action required"
    return summary


def _resolve_example_dir_for_cli(value: Path) -> Path:
    examples_root = Path("examples").resolve()
    if value.is_absolute():
        resolved = value.resolve()
        try:
            relative = resolved.relative_to(examples_root)
        except ValueError as exc:
            raise ReferenceAestheticMetricsError(
                "invalid fixture path: expected examples/<fixture-name>"
            ) from exc
        if len(relative.parts) != 1 or ".." in relative.parts:
            raise ReferenceAestheticMetricsError(
                "invalid fixture path: expected examples/<fixture-name>"
            )
        _validate_fixture_name_for_cli(relative.parts[0], str(value))
        return Path("examples") / relative.parts[0]
    if value.parts and value.parts[0] == "examples":
        if len(value.parts) != 2 or ".." in value.parts:
            raise ReferenceAestheticMetricsError(
                "invalid fixture path: expected examples/<fixture-name>"
            )
        _validate_fixture_name_for_cli(value.parts[1], str(value))
        return Path("examples") / value.parts[1]
    if len(value.parts) == 1:
        _validate_fixture_name_for_cli(str(value), str(value))
        examples_path = Path("examples") / value
        if examples_path.is_dir():
            return examples_path
        if value.exists():
            raise ReferenceAestheticMetricsError(
                "invalid fixture path: relative fixture names must resolve under examples/"
            )
        return examples_path
    raise ReferenceAestheticMetricsError(
        "invalid fixture path: expected fixture name, examples/<fixture-name>, "
        "or an absolute path under examples/"
    )


def _validate_fixture_name_for_cli(name: str, original: str) -> None:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise ReferenceAestheticMetricsError(f"invalid fixture path: {original}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example_dir", type=Path)
    args = parser.parse_args(argv)
    try:
        example_dir = _resolve_example_dir_for_cli(args.example_dir)
        payload = build_reference_aesthetic_metrics(example_dir)
    except ReferenceAestheticMetricsError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if payload is None:
        print(f"SKIP: {example_dir.name} has no reference-learning contract")
        return 0
    output = example_dir / OUTPUT_RELATIVE_PATH
    print(f"{payload['state']}: wrote {_example_relative_path(example_dir, output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
