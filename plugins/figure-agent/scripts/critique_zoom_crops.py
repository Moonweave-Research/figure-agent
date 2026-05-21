"""High-zoom audit crop generation for critique briefs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PIL import Image

PRINT_SCALE_TARGETS = (
    ("print_178mm", "178mm_equivalent", 1000),
    ("print_thumbnail", "thumbnail", 360),
)


def _safe_stem(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    safe = re.sub(r"_+", "_", safe)
    return safe.strip("._") or "crop"


def _relative_to_example(example_dir: Path, path: Path) -> str:
    return str(path.relative_to(example_dir))


def _grid_boxes(width: int, height: int, *, columns: int, rows: int) -> list[list[int]]:
    boxes: list[list[int]] = []
    for row in range(rows):
        for column in range(columns):
            x0 = round(column * width / columns)
            y0 = round(row * height / rows)
            x1 = round((column + 1) * width / columns)
            y1 = round((row + 1) * height / rows)
            boxes.append([x0, y0, x1, y1])
    return boxes


def _quadrant_boxes(width: int, height: int) -> list[list[int]]:
    return _grid_boxes(width, height, columns=2, rows=2)


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
                    "kind": "zoom_crop",
                    "source": source_label,
                    "path": _relative_to_example(example_dir, output_path),
                    "source_path": _relative_to_example(example_dir, source_path),
                    "bbox_px": box,
                }
            )
    return crops


def _write_subquadrants(
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
        for index, box in enumerate(_grid_boxes(width, height, columns=4, rows=4), start=1):
            crop_id = f"{id_prefix}_s{index:02d}"
            output_path = output_dir / f"{crop_id}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.crop(tuple(box)).save(output_path)
            crops.append(
                {
                    "id": crop_id,
                    "kind": "zoom_crop",
                    "source": source_label,
                    "path": _relative_to_example(example_dir, output_path),
                    "source_path": _relative_to_example(example_dir, source_path),
                    "bbox_px": box,
                }
            )
    return crops


def _panel_specs_by_id(spec: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(spec, dict):
        return {}
    panels = spec.get("panels")
    if not isinstance(panels, list):
        return {}
    panel_map: dict[str, dict[str, Any]] = {}
    for index, panel in enumerate(panels):
        if not isinstance(panel, dict):
            continue
        panel_id = str(panel.get("id") or f"panel_{index + 1}")
        panel_map[_safe_stem(panel_id)] = panel
    return panel_map


def _bbox_cm_to_px(
    bbox_pdf_cm: list[float],
    *,
    page_size_cm: tuple[float, float],
    image_size_px: tuple[int, int],
) -> list[int]:
    page_width_cm, page_height_cm = page_size_cm
    image_width_px, image_height_px = image_size_px
    x0, y0, x1, y1 = bbox_pdf_cm
    return [
        round(x0 / page_width_cm * image_width_px),
        round(y0 / page_height_cm * image_height_px),
        round(x1 / page_width_cm * image_width_px),
        round(y1 / page_height_cm * image_height_px),
    ]


def _valid_bbox_cm(value: Any) -> list[float] | None:
    if not isinstance(value, list) or len(value) != 4:
        return None
    try:
        bbox = [float(item) for item in value]
    except (TypeError, ValueError):
        return None
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        return None
    return bbox


def _write_instrument_crops(
    *,
    render_path: Path,
    output_dir: Path,
    panel_id: str,
    panel: dict[str, Any],
    example_dir: Path,
    pdf_page_size_cm: tuple[float, float],
    min_width_px: int = 600,
) -> list[dict[str, Any]]:
    instruments = panel.get("instruments")
    if not isinstance(instruments, list) or not instruments:
        return []

    crops: list[dict[str, Any]] = []
    with Image.open(render_path) as image:
        width, height = image.size
        resampling = getattr(Image, "Resampling", Image).LANCZOS
        for index, instrument in enumerate(instruments, start=1):
            if not isinstance(instrument, dict):
                continue
            bbox_cm = _valid_bbox_cm(instrument.get("bbox_pdf_cm"))
            if bbox_cm is None:
                continue
            instrument_name = str(instrument.get("name") or f"instrument_{index}")
            bbox_px = _bbox_cm_to_px(
                bbox_cm,
                page_size_cm=pdf_page_size_cm,
                image_size_px=(width, height),
            )
            x0, y0, x1, y1 = bbox_px
            if x0 < 0 or y0 < 0 or x1 > width or y1 > height or x1 <= x0 or y1 <= y0:
                continue
            crop_id = f"panel_{panel_id}_instr_{_safe_stem(instrument_name)}"
            output_path = output_dir / f"{crop_id}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            crop = image.crop((x0, y0, x1, y1))
            upscaled = crop.width < min_width_px
            if upscaled:
                output_height = max(1, round(crop.height * (min_width_px / crop.width)))
                crop = crop.resize((min_width_px, output_height), resampling)
            crop.save(output_path)
            crops.append(
                {
                    "id": crop_id,
                    "kind": "zoom_crop",
                    "source": f"panel:{panel_id}:instrument:{instrument_name}",
                    "path": _relative_to_example(example_dir, output_path),
                    "source_path": _relative_to_example(example_dir, render_path),
                    "bbox_px": bbox_px,
                    "bbox_pdf_cm": bbox_cm,
                    "size_px": [crop.width, crop.height],
                    "upscaled": upscaled,
                }
            )
    return crops


def _scaled_size(width: int, height: int, target_width: int) -> tuple[int, int]:
    output_width = max(1, min(width, target_width))
    output_height = max(1, round(height * (output_width / width)))
    return output_width, output_height


def _write_print_scale_images(
    *,
    source_path: Path,
    output_dir: Path,
    example_dir: Path,
) -> list[dict[str, Any]]:
    audits: list[dict[str, Any]] = []
    with Image.open(source_path) as image:
        width, height = image.size
        resampling = getattr(Image, "Resampling", Image).LANCZOS
        for audit_id, scale_label, target_width in PRINT_SCALE_TARGETS:
            output_size = _scaled_size(width, height, target_width)
            output_path = output_dir / f"{audit_id}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.resize(output_size, resampling).save(output_path)
            audits.append(
                {
                    "id": audit_id,
                    "kind": "print_scale",
                    "scale_label": scale_label,
                    "scale_basis": "fixed_width_proxy",
                    "target_width_px": target_width,
                    "upscaled": output_size[0] > width,
                    "path": _relative_to_example(example_dir, output_path),
                    "source_path": _relative_to_example(example_dir, source_path),
                    "size_px": list(output_size),
                }
            )
    return audits


def build_zoom_crop_pack(
    example_dir: Path,
    render_path: Path,
    *,
    panel_crop_paths: tuple[Path, ...],
    spec: dict[str, Any] | None = None,
    pdf_page_size_cm: tuple[float, float] | None = None,
) -> list[dict[str, Any]]:
    output_dir = example_dir / "build" / "audit_crops"
    panel_specs = _panel_specs_by_id(spec)
    crops = _write_quadrants(
        source_path=render_path,
        output_dir=output_dir,
        id_prefix="full",
        source_label="full_render",
        example_dir=example_dir,
    )
    crops.extend(
        _write_print_scale_images(
            source_path=render_path,
            output_dir=output_dir,
            example_dir=example_dir,
        )
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
        panel = panel_specs.get(panel_id, {})
        instrument_crops = (
            _write_instrument_crops(
                render_path=render_path,
                output_dir=output_dir,
                panel_id=panel_id,
                panel=panel,
                example_dir=example_dir,
                pdf_page_size_cm=pdf_page_size_cm,
            )
            if pdf_page_size_cm is not None
            else []
        )
        if instrument_crops:
            crops.extend(instrument_crops)
        else:
            crops.extend(
                _write_subquadrants(
                    source_path=panel_crop_path,
                    output_dir=output_dir,
                    id_prefix=f"panel_{panel_id}",
                    source_label=f"panel:{panel_id}:subquadrant",
                    example_dir=example_dir,
                )
            )
    return crops
