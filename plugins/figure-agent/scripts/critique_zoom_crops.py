"""High-zoom audit crop generation for critique briefs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from PIL import Image
from quality_manifest import file_sha256

CROP_MANIFEST_SCHEMA = "figure-agent.audit-crop-manifest.v1"
VISUAL_CLASH_CROP_MIN_WIDTH_PX = 600

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


def _valid_bbox_px(value: Any) -> list[int] | None:
    if not isinstance(value, list) or len(value) != 4:
        return None
    try:
        bbox = [int(round(float(item))) for item in value]
    except (TypeError, ValueError):
        return None
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        return None
    return bbox


def _clamp_bbox_px(bbox: list[int], *, width: int, height: int) -> list[int] | None:
    x0, y0, x1, y1 = bbox
    clamped = [max(0, x0), max(0, y0), min(width, x1), min(height, y1)]
    if clamped[2] <= clamped[0] or clamped[3] <= clamped[1]:
        return None
    return clamped


def _visual_clash_sort_key(candidate: dict[str, Any]) -> tuple[str, str, str, list[int]]:
    bbox = candidate.get("bbox_px")
    bbox_key = bbox if isinstance(bbox, list) else []
    return (
        str(candidate.get("id") or ""),
        str(candidate.get("kind") or ""),
        str(candidate.get("text") or ""),
        bbox_key,
    )


def _load_visual_clash_candidates(example_dir: Path) -> list[dict[str, Any]]:
    report_path = example_dir / "build" / "visual_clash.json"
    if not report_path.is_file():
        return []
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return []
    return sorted(
        (candidate for candidate in candidates if isinstance(candidate, dict)),
        key=_visual_clash_sort_key,
    )


def _visual_clash_crop_id(candidate: dict[str, Any], index: int) -> str:
    candidate_id = str(candidate.get("id") or f"VC{index:03d}")
    label = str(candidate.get("text") or candidate.get("kind") or "candidate")
    return f"{_safe_stem(candidate_id)}_{_safe_stem(label)}"


def _write_visual_clash_crops(
    *,
    source_path: Path,
    output_dir: Path,
    example_dir: Path,
) -> list[dict[str, Any]]:
    candidates = _load_visual_clash_candidates(example_dir)
    if not candidates:
        return []

    crops: list[dict[str, Any]] = []
    with Image.open(source_path) as image:
        width, height = image.size
        resampling = getattr(Image, "Resampling", Image).LANCZOS
        for index, candidate in enumerate(candidates, start=1):
            bbox_px = _valid_bbox_px(candidate.get("bbox_px"))
            if bbox_px is None:
                continue
            target_bbox_px = _clamp_bbox_px(bbox_px, width=width, height=height)
            if target_bbox_px is None:
                continue
            pad_x = max(1, round((bbox_px[2] - bbox_px[0]) / 2))
            pad_y = max(1, round((bbox_px[3] - bbox_px[1]) / 2))
            x0, y0, x1, y1 = target_bbox_px
            crop_box = [
                max(0, x0 - pad_x),
                max(0, y0 - pad_y),
                min(width, x1 + pad_x),
                min(height, y1 + pad_y),
            ]
            if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
                continue
            crop_id = _visual_clash_crop_id(candidate, index)
            output_path = output_dir / "visual_clash" / f"{crop_id}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            crop = image.crop(tuple(crop_box))
            upscaled = crop.width < VISUAL_CLASH_CROP_MIN_WIDTH_PX
            if upscaled:
                output_height = max(
                    1,
                    round(crop.height * (VISUAL_CLASH_CROP_MIN_WIDTH_PX / crop.width)),
                )
                crop = crop.resize((VISUAL_CLASH_CROP_MIN_WIDTH_PX, output_height), resampling)
            crop.save(output_path)
            clash_ref = str(candidate.get("id") or f"VC{index:03d}")
            crops.append(
                {
                    "id": crop_id,
                    "kind": "visual_clash_crop",
                    "source": f"visual_clash:{clash_ref}",
                    "path": _relative_to_example(example_dir, output_path),
                    "source_path": _relative_to_example(example_dir, source_path),
                    "bbox_px": crop_box,
                    "target_bbox_px": target_bbox_px,
                    "size_px": [crop.width, crop.height],
                    "upscaled": upscaled,
                    "visual_clash_ref": clash_ref,
                    "visual_clash_kind": str(candidate.get("kind") or ""),
                    "visual_clash_text": str(candidate.get("text") or ""),
                }
            )
    return crops


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


def _write_crop_manifest(
    *,
    example_dir: Path,
    render_path: Path,
    crops: list[dict[str, Any]],
) -> None:
    output_path = example_dir / "build" / "audit_crops" / "manifest.json"
    manifest_crops: list[dict[str, Any]] = []
    for crop in crops:
        item = dict(crop)
        path = item.get("path")
        if isinstance(path, str) and path.strip():
            crop_path = example_dir / path
            if crop_path.is_file():
                item["sha256"] = file_sha256(crop_path)
        manifest_crops.append(item)
    manifest_crops = sorted(manifest_crops, key=lambda item: str(item.get("id") or ""))
    payload = {
        "schema": CROP_MANIFEST_SCHEMA,
        "fixture": example_dir.name,
        "render_path": _relative_to_example(example_dir, render_path),
        "required_crop_ids": [str(item.get("id") or "") for item in manifest_crops],
        "crops": manifest_crops,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    crops.extend(
        _write_visual_clash_crops(
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
    _write_crop_manifest(example_dir=example_dir, render_path=render_path, crops=crops)
    return crops
