"""Map rendered detector findings to declared regions without spatial guessing."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from inputs import normalize_bbox_pdf_cm, parse_spec
from semantic_region_contract import render_geometry_hash


class VisualFindingAttributionError(ValueError):
    """Raised when detector or geometry evidence is malformed or stale."""


def _number_list(value: object, *, length: int, label: str) -> list[float]:
    if not isinstance(value, list | tuple) or len(value) != length:
        raise VisualFindingAttributionError(f"{label}_invalid")
    try:
        result = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise VisualFindingAttributionError(f"{label}_invalid") from exc
    return result


def _finding(raw: object) -> tuple[str, list[float], float | None]:
    if not isinstance(raw, dict) or not isinstance(raw.get("id"), str) or not raw["id"]:
        raise VisualFindingAttributionError("detector_finding_invalid")
    bbox = _number_list(raw.get("bbox_px"), length=4, label="detector_finding_bbox")
    if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        raise VisualFindingAttributionError("detector_finding_bbox_invalid")
    confidence = raw.get("confidence")
    if confidence is not None:
        if isinstance(confidence, bool) or not isinstance(confidence, int | float):
            raise VisualFindingAttributionError("detector_finding_confidence_invalid")
        confidence = float(confidence)
        if not 0 <= confidence <= 1:
            raise VisualFindingAttributionError("detector_finding_confidence_invalid")
    return raw["id"], bbox, confidence


def _checked_geometry(raw: object, *, label: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise VisualFindingAttributionError(f"{label}_invalid")
    declared_hash = raw.get("render_geometry_hash")
    if declared_hash != render_geometry_hash(raw):
        raise VisualFindingAttributionError(f"{label}_render_geometry_hash_mismatch")
    if raw.get("coordinate_space") != "pdf_cm" or raw.get("origin") != "bottom_left":
        raise VisualFindingAttributionError(f"{label}_coordinate_space_invalid")
    rotation = raw.get("rotation_deg")
    if rotation not in {0, 90, 180, 270}:
        raise VisualFindingAttributionError(f"{label}_rotation_invalid")
    page_index = raw.get("page_index")
    if not isinstance(page_index, int) or isinstance(page_index, bool) or page_index < 0:
        raise VisualFindingAttributionError(f"{label}_page_index_invalid")
    try:
        media = normalize_bbox_pdf_cm(
            raw.get("media_box_pdf_cm"),
            label=f"{label}.media_box_pdf_cm",
        )
        crop = normalize_bbox_pdf_cm(
            raw.get("crop_box_pdf_cm"),
            label=f"{label}.crop_box_pdf_cm",
        )
    except ValueError as exc:
        raise VisualFindingAttributionError(str(exc)) from exc
    return {
        "coordinate_space": "pdf_cm",
        "page_index": page_index,
        "origin": "bottom_left",
        "media_box_pdf_cm": media,
        "crop_box_pdf_cm": crop,
        "rotation_deg": rotation,
        "render_geometry_hash": declared_hash,
    }


def _transform_bbox(bbox: list[float], transform: list[float]) -> list[float]:
    a, b, c, d, e, f = transform
    corners = [
        (bbox[0], bbox[1]),
        (bbox[0], bbox[3]),
        (bbox[2], bbox[1]),
        (bbox[2], bbox[3]),
    ]
    transformed = [(a * x + c * y + e, b * x + d * y + f) for x, y in corners]
    xs = [point[0] for point in transformed]
    ys = [point[1] for point in transformed]
    return [min(xs), min(ys), max(xs), max(ys)]


def _unrotate_point(x: float, y: float, rotation: int) -> tuple[float, float]:
    if rotation == 0:
        return x, 1 - y
    if rotation == 90:
        return y, x
    if rotation == 180:
        return 1 - x, y
    return 1 - y, 1 - x


def _bbox_pdf_cm(
    bbox_px: list[float],
    *,
    image_size: list[float],
    transform: list[float],
    rotation: int,
    raster_box: list[float],
) -> list[float]:
    transformed = _transform_bbox(bbox_px, transform)
    width_px, height_px = image_size
    if width_px <= 0 or height_px <= 0:
        raise VisualFindingAttributionError("detector_render_image_size_invalid")
    corners = [
        (transformed[0] / width_px, transformed[1] / height_px),
        (transformed[0] / width_px, transformed[3] / height_px),
        (transformed[2] / width_px, transformed[1] / height_px),
        (transformed[2] / width_px, transformed[3] / height_px),
    ]
    unrotated = [_unrotate_point(x, y, rotation) for x, y in corners]
    box_width = raster_box[2] - raster_box[0]
    box_height = raster_box[3] - raster_box[1]
    xs = [raster_box[0] + point[0] * box_width for point in unrotated]
    ys = [raster_box[1] + point[1] * box_height for point in unrotated]
    return [min(xs), min(ys), max(xs), max(ys)]


def _intersects(first: list[float], second: list[float]) -> bool:
    return min(first[2], second[2]) > max(first[0], second[0]) and min(first[3], second[3]) > max(
        first[1], second[1]
    )


def _panel_candidates(fixture_dir: Path, bbox: list[float]) -> list[str]:
    try:
        spec = parse_spec((fixture_dir / "spec.yaml").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError) as exc:
        raise VisualFindingAttributionError(f"spec_invalid: {exc}") from exc
    candidates: list[str] = []
    for panel in spec.get("panels", []):
        if not isinstance(panel, dict) or not isinstance(panel.get("bbox_pdf_cm"), list):
            continue
        if _intersects(bbox, panel["bbox_pdf_cm"]):
            candidates.append(str(panel.get("id")))
    return sorted(candidates)


def _winning_region(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(candidates) == 1:
        return candidates[0]
    candidate_ids = {str(region.get("id")) for region in candidates}
    specific = [
        region
        for region in candidates
        if all(
            region is other or str(region.get("id")) in (other.get("contains") or [])
            for other in candidates
        )
    ]
    if len(specific) == 1:
        return specific[0]
    priorities = [region.get("priority") for region in candidates]
    if priorities and all(
        isinstance(priority, int) and not isinstance(priority, bool) for priority in priorities
    ):
        highest = max(priorities)
        winners = [region for region in candidates if region.get("priority") == highest]
        if len(winners) == 1:
            return winners[0]
    _ = candidate_ids
    return None


def _fresh_source_selector(
    fixture_dir: Path,
    source: object,
    *,
    expected_selector_id: str,
) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(source, dict):
        return None, "source_binding_missing"
    binding_state = source.get("binding_state")
    if binding_state != "exact":
        return None, f"source_binding_{binding_state or 'missing'}"
    if source.get("selector_id") != expected_selector_id:
        return None, "source_selector_id_mismatch"
    relative = Path(str(source.get("path") or ""))
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        return None, "source_path_unsafe"
    path = fixture_dir / relative
    try:
        path.resolve().relative_to(fixture_dir.resolve())
        source_bytes = path.read_bytes()
        actual_hash = f"sha256:{hashlib.sha256(source_bytes).hexdigest()}"
        source_text = source_bytes.decode("utf-8")
    except (FileNotFoundError, UnicodeError, ValueError):
        return None, "source_missing"
    if actual_hash != source.get("source_sha256"):
        return None, "source_hash_mismatch"
    anchor_start = source.get("anchor_start")
    anchor_end = source.get("anchor_end")
    if not isinstance(anchor_start, str) or not isinstance(anchor_end, str):
        return None, "source_anchor_missing"
    lines = source_text.splitlines(keepends=True)
    line_values = [line.rstrip("\r\n") for line in lines]
    starts = [index for index, line in enumerate(line_values, start=1) if line == anchor_start]
    ends = [index for index, line in enumerate(line_values, start=1) if line == anchor_end]
    if not starts or not ends:
        return None, "source_anchor_missing"
    if len(starts) != 1 or len(ends) != 1:
        return None, "source_anchor_duplicate"
    resolved_start, resolved_end = starts[0], ends[0]
    if resolved_start > resolved_end:
        return None, "source_anchor_order_invalid"
    declared_lines = (
        source.get("line_start"),
        source.get("line_end"),
        source.get("resolved_line_start"),
        source.get("resolved_line_end"),
    )
    if declared_lines != (
        resolved_start,
        resolved_end,
        resolved_start,
        resolved_end,
    ):
        return None, "source_line_snapshot_stale"
    selected_bytes = "".join(lines[resolved_start - 1 : resolved_end]).encode("utf-8")
    selected_hash = f"sha256:{hashlib.sha256(selected_bytes).hexdigest()}"
    if source.get("selected_content_sha256") != selected_hash:
        return None, "source_selected_content_hash_mismatch"
    keys = (
        "path",
        "selector_id",
        "anchor_start",
        "anchor_end",
        "source_sha256",
        "line_start",
        "line_end",
        "resolved_line_start",
        "resolved_line_end",
        "selected_content_sha256",
    )
    return {key: source[key] for key in keys if key in source}, None


def attribute_visual_finding(
    finding: object,
    *,
    detector_render: object,
    semantic_contract: object,
    fixture_dir: Path,
) -> dict[str, Any]:
    """Attribute one finding while preserving detector uncertainty verbatim."""
    finding_id, detector_bbox, confidence = _finding(finding)
    if not isinstance(semantic_contract, dict):
        raise VisualFindingAttributionError("semantic_contract_invalid")
    contract_geometry = _checked_geometry(
        semantic_contract.get("page_geometry"),
        label="semantic_contract",
    )
    if not isinstance(detector_render, dict):
        raise VisualFindingAttributionError("detector_render_invalid")
    detector_geometry = _checked_geometry(
        detector_render.get("page_geometry"),
        label="detector_render",
    )
    base = {
        "finding_id": finding_id,
        "detector_bbox_px": detector_bbox,
        "detector_confidence": confidence,
    }
    if detector_geometry["page_index"] != contract_geometry["page_index"]:
        return {
            **base,
            "state": "unbound",
            "reason": "page_index_mismatch",
            "panel_candidates": [],
            "region_candidates": [],
        }
    comparable_keys = (
        "coordinate_space",
        "origin",
        "media_box_pdf_cm",
        "crop_box_pdf_cm",
        "rotation_deg",
    )
    if any(detector_geometry[key] != contract_geometry[key] for key in comparable_keys):
        raise VisualFindingAttributionError("detector_render_geometry_mismatch")
    if detector_render.get("pixel_origin") != "top_left":
        raise VisualFindingAttributionError("detector_render_pixel_origin_invalid")
    image_size = _number_list(
        detector_render.get("image_size_px"),
        length=2,
        label="detector_render_image_size",
    )
    transform = _number_list(
        detector_render.get("fragment_transform"),
        length=6,
        label="detector_render_fragment_transform",
    )
    raster_box_name = detector_render.get("raster_box")
    if raster_box_name not in {"media_box", "crop_box"}:
        raise VisualFindingAttributionError("detector_render_raster_box_invalid")
    raster_box = detector_geometry[f"{raster_box_name}_pdf_cm"]
    bbox_pdf = _bbox_pdf_cm(
        detector_bbox,
        image_size=image_size,
        transform=transform,
        rotation=detector_geometry["rotation_deg"],
        raster_box=raster_box,
    )
    base["bbox_pdf_cm"] = bbox_pdf
    base["panel_candidates"] = _panel_candidates(fixture_dir, bbox_pdf)
    regions = semantic_contract.get("regions")
    if not isinstance(regions, list):
        raise VisualFindingAttributionError("semantic_contract_regions_invalid")
    candidates = [
        region
        for region in regions
        if isinstance(region, dict)
        and isinstance(region.get("bbox_pdf_cm"), list)
        and _intersects(bbox_pdf, region["bbox_pdf_cm"])
    ]
    if not candidates:
        return {
            **base,
            "state": "unbound",
            "reason": "no_declared_region_overlap",
            "region_candidates": [],
        }
    winner = _winning_region(candidates)
    if winner is None:
        return {
            **base,
            "state": "ambiguous",
            "reason": "undeclared_overlap_tie",
            "region_candidates": sorted(str(region.get("id")) for region in candidates),
        }
    region_id = str(winner.get("id"))
    selector, source_error = _fresh_source_selector(
        fixture_dir,
        winner.get("source"),
        expected_selector_id=region_id,
    )
    if source_error is not None:
        state = "ambiguous" if "ambiguous" in source_error else "unbound"
        return {
            **base,
            "state": state,
            "reason": source_error,
            "region_candidates": [region_id],
        }
    return {
        **base,
        "state": "exact",
        "reason": "single_declared_winner_with_fresh_source",
        "region_candidates": [region_id],
        "source_selector": selector,
    }
