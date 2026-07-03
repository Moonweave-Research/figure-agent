"""Build advisory fixture-level visual quality metrics from existing artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import fixture_identity
import numpy as np
import runtime_paths
from PIL import Image, UnidentifiedImageError

SCHEMA = "figure-agent.fixture-visual-quality-metrics.v1"
OUTPUT_RELATIVE_PATH = Path("build/visual_quality_metrics.json")


class VisualQualityMetricsError(ValueError):
    """Raised when visual quality metrics cannot be built safely."""


def _validate_fixture_name(name: str) -> str:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise VisualQualityMetricsError(str(exc)) from exc
    return name


def _fixture_dir(workspace_root: Path, name: str) -> Path:
    examples = workspace_root / "examples"
    path = examples / _validate_fixture_name(name)
    if path.is_symlink():
        raise VisualQualityMetricsError(f"fixture_symlink_forbidden: {name}")
    try:
        path.resolve().relative_to(examples.resolve())
    except ValueError as exc:
        raise VisualQualityMetricsError("fixture path_escape") from exc
    return path


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _round(value: float) -> float:
    return round(float(value), 6)


def _load_json(path: Path, *, label: str) -> dict[str, Any] | None:
    if path.is_symlink():
        raise VisualQualityMetricsError(f"{label}_symlink_forbidden")
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VisualQualityMetricsError(f"{label}_unreadable") from exc
    if not isinstance(payload, dict):
        raise VisualQualityMetricsError(f"{label}_invalid")
    return payload


def _candidate_count(payload: dict[str, Any] | None) -> int:
    if payload is None:
        return 0
    total = payload.get("total")
    if isinstance(total, int):
        return total
    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        return len(candidates)
    return 0


def _detector_counts(example_dir: Path) -> dict[str, dict[str, Any]]:
    build = example_dir / "build"
    paths = {
        "visual_clash": build / "visual_clash.json",
        "text_boundary": build / "text_boundary_clash.json",
        "label_path": build / "label_path_proximity.json",
        "undeclared_geometry": build / "undeclared_geometry.json",
    }
    return {
        key: {
            "present": (payload := _load_json(path, label=key)) is not None,
            "candidate_count": _candidate_count(payload),
        }
        for key, path in paths.items()
    }


def _crop_metrics(example_dir: Path) -> dict[str, Any]:
    manifest = _load_json(
        example_dir / "build" / "audit_crops" / "manifest.json",
        label="audit_crop_manifest",
    )
    if manifest is None:
        return {
            "manifest_present": False,
            "required_count": 0,
            "print_scale_evidence": "missing",
    }
    required = manifest.get("required_crop_ids")
    required_ids = (
        [item for item in required if isinstance(item, str)]
        if isinstance(required, list)
        else []
    )
    print_ids = sorted(crop_id for crop_id in required_ids if crop_id.startswith("print_"))
    return {
        "manifest_present": True,
        "required_count": len(required_ids),
        "print_scale_crop_ids": print_ids,
        "print_scale_evidence": "present" if print_ids else "missing",
    }


def _image_metrics(path: Path) -> dict[str, Any]:
    try:
        with Image.open(path) as image:
            rgb = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    except (OSError, UnidentifiedImageError) as exc:
        raise VisualQualityMetricsError("build_png_unreadable") from exc
    gray = rgb.mean(axis=-1)
    ink_mask = gray < 0.96
    horizontal = np.abs(np.diff(gray, axis=1)) > 0.08
    vertical = np.abs(np.diff(gray, axis=0)) > 0.08
    possible_edges = horizontal.size + vertical.size
    edge_density = (
        float(horizontal.sum() + vertical.sum()) / possible_edges if possible_edges else 0.0
    )
    colors = np.unique(np.clip((rgb.reshape(-1, 3) * 8).astype(np.int16), 0, 7), axis=0)
    return {
        "size_px": [int(rgb.shape[1]), int(rgb.shape[0])],
        "ink_density": _round(float(ink_mask.mean())),
        "edge_density": _round(edge_density),
        "quantized_color_count": int(colors.shape[0]),
    }


def _scaffold_load(detectors: dict[str, dict[str, Any]], crops: dict[str, Any]) -> dict[str, Any]:
    detector_total = sum(int(item.get("candidate_count") or 0) for item in detectors.values())
    crop_total = int(crops.get("required_count") or 0)
    score = detector_total + crop_total
    if score >= 120:
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"
    return {
        "level": level,
        "score": score,
        "detector_candidate_count": detector_total,
        "required_crop_count": crop_total,
    }


def build_visual_quality_metrics(
    name: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    example_dir = _fixture_dir(paths.workspace_root, name)
    if not example_dir.is_dir():
        raise VisualQualityMetricsError(f"fixture_missing: {name}")
    png_path = example_dir / "build" / f"{name}.png"
    if not png_path.is_file():
        raise VisualQualityMetricsError("build_png_missing")
    detectors = _detector_counts(example_dir)
    crops = _crop_metrics(example_dir)
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "fixture": name,
        "state": "measured",
        "policy": "advisory_only",
        "build_artifact": {
            "path": _relative(example_dir, png_path),
            "sha256": _file_sha256(png_path),
        },
        "image": _image_metrics(png_path),
        "detectors": detectors,
        "crop_audit": crops,
        "scaffold_load": _scaffold_load(detectors, crops),
        "print_scale": {
            "state": crops["print_scale_evidence"],
            "evidence_crop_ids": crops.get("print_scale_crop_ids", []),
        },
        "mutation_boundary": "writes_build_metrics_only_no_gate_state",
    }
    if write:
        output = example_dir / OUTPUT_RELATIVE_PATH
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main(
    argv: list[str] | None = None,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent visual-metrics")
    parser.add_argument("fixture")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = build_visual_quality_metrics(
            args.fixture,
            workspace_root=workspace_root,
            plugin_root=plugin_root,
            write=not args.no_write,
        )
    except VisualQualityMetricsError as exc:
        print(f"fig-agent visual-metrics: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
