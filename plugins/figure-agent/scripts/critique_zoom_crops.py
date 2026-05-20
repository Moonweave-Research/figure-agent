"""High-zoom audit crop generation for critique briefs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image


def _safe_stem(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return safe.strip("._") or "crop"


def _relative_to_example(example_dir: Path, path: Path) -> str:
    return str(path.relative_to(example_dir))


def _quadrant_boxes(width: int, height: int) -> list[list[int]]:
    mid_x = width // 2
    mid_y = height // 2
    return [
        [0, 0, mid_x, mid_y],
        [mid_x, 0, width, mid_y],
        [0, mid_y, mid_x, height],
        [mid_x, mid_y, width, height],
    ]


def _write_quadrants(
    *,
    source_path: Path,
    output_dir: Path,
    id_prefix: str,
    source_label: str,
    example_dir: Path,
) -> list[dict[str, Any]]:
    crops: list[dict[str, Any]] = []
    with Image.open(source_path) as image:
        width, height = image.size
        for index, box in enumerate(_quadrant_boxes(width, height), start=1):
            crop_id = f"{id_prefix}_q{index}"
            output_path = output_dir / f"{crop_id}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.crop(tuple(box)).save(output_path)
            crops.append(
                {
                    "id": crop_id,
                    "source": source_label,
                    "path": _relative_to_example(example_dir, output_path),
                    "source_path": _relative_to_example(example_dir, source_path),
                    "bbox_px": box,
                }
            )
    return crops


def build_zoom_crop_pack(
    example_dir: Path,
    render_path: Path,
    *,
    panel_crop_paths: tuple[Path, ...],
) -> list[dict[str, Any]]:
    output_dir = example_dir / "build" / "audit_crops"
    crops = _write_quadrants(
        source_path=render_path,
        output_dir=output_dir,
        id_prefix="full",
        source_label="full_render",
        example_dir=example_dir,
    )
    for panel_crop_path in panel_crop_paths:
        try:
            panel_crop_path.relative_to(example_dir)
        except ValueError as exc:
            raise ValueError("panel crop must be inside example_dir") from exc
        panel_id = _safe_stem(panel_crop_path.stem)
        crops.extend(
            _write_quadrants(
                source_path=panel_crop_path,
                output_dir=output_dir,
                id_prefix=f"panel_{panel_id}",
                source_label=f"panel:{panel_id}",
                example_dir=example_dir,
            )
        )
    return crops
