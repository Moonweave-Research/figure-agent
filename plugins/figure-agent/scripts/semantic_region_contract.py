"""Validate fixture-local semantic regions and anchored source selectors."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml
from inputs import normalize_bbox_pdf_cm, parse_spec

SCHEMA = "figure-agent.semantic-regions.v1"
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ROTATIONS = {0, 90, 180, 270}


class SemanticRegionContractError(ValueError):
    """Raised when a semantic-region declaration is unsafe or malformed."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def _sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _normalize_geometry(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise SemanticRegionContractError("page_geometry_invalid")
    if raw.get("coordinate_space") != "pdf_cm":
        raise SemanticRegionContractError("coordinate_space_invalid")
    if raw.get("origin") != "bottom_left":
        raise SemanticRegionContractError("origin_invalid")
    page_index = raw.get("page_index")
    if not isinstance(page_index, int) or isinstance(page_index, bool) or page_index < 0:
        raise SemanticRegionContractError("page_index_invalid")
    rotation = raw.get("rotation_deg")
    if rotation not in _ROTATIONS:
        raise SemanticRegionContractError("rotation_deg_invalid")
    try:
        media_box = normalize_bbox_pdf_cm(
            raw.get("media_box_pdf_cm"),
            label="page_geometry.media_box_pdf_cm",
        )
        crop_box = normalize_bbox_pdf_cm(
            raw.get("crop_box_pdf_cm"),
            label="page_geometry.crop_box_pdf_cm",
        )
    except ValueError as exc:
        raise SemanticRegionContractError(str(exc)) from exc
    if not _contains(media_box, crop_box):
        raise SemanticRegionContractError("crop_box_outside_media_box")
    normalized = {
        "coordinate_space": "pdf_cm",
        "page_index": page_index,
        "origin": "bottom_left",
        "media_box_pdf_cm": media_box,
        "crop_box_pdf_cm": crop_box,
        "rotation_deg": rotation,
    }
    declared_hash = raw.get("render_geometry_hash")
    computed_hash = render_geometry_hash(normalized)
    if declared_hash != computed_hash:
        raise SemanticRegionContractError("render_geometry_hash_mismatch")
    normalized["render_geometry_hash"] = computed_hash
    return normalized


def render_geometry_hash(page_geometry: dict[str, Any]) -> str:
    """Hash only normalized geometry fields, excluding a supplied hash value."""
    material = {
        key: page_geometry.get(key)
        for key in (
            "coordinate_space",
            "page_index",
            "origin",
            "media_box_pdf_cm",
            "crop_box_pdf_cm",
            "rotation_deg",
        )
    }
    return _sha256_text(_canonical_json(material))


def _contains(outer: list[float], inner: list[float]) -> bool:
    return (
        outer[0] <= inner[0]
        and outer[1] <= inner[1]
        and inner[2] <= outer[2]
        and inner[3] <= outer[3]
    )


def _safe_source_path(fixture_dir: Path, value: object, *, region_id: str) -> Path:
    relative = Path(str(value or ""))
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        raise SemanticRegionContractError(f"unsafe_source_path: {region_id}")
    path = fixture_dir / relative
    try:
        path.resolve().relative_to(fixture_dir)
    except ValueError as exc:
        raise SemanticRegionContractError(f"unsafe_source_path: {region_id}") from exc
    if path.is_symlink():
        raise SemanticRegionContractError(f"unsafe_source_path: {region_id}")
    if not path.is_file():
        raise SemanticRegionContractError(f"source_missing: {region_id}")
    return path


def _positive_line(value: object, *, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise SemanticRegionContractError(f"{label}_invalid")
    return value


def _normalize_source(
    fixture_dir: Path,
    raw: object,
    *,
    region_id: str,
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise SemanticRegionContractError(f"source_invalid: {region_id}")
    path = _safe_source_path(fixture_dir, raw.get("path"), region_id=region_id)
    selector_id = str(raw.get("selector_id") or "")
    if not selector_id:
        raise SemanticRegionContractError(f"selector_id_missing: {region_id}")
    anchor_start = str(raw.get("anchor_start") or "")
    anchor_end = str(raw.get("anchor_end") or "")
    if anchor_start != f"% figure-agent:start {selector_id}":
        raise SemanticRegionContractError(f"anchor_start_invalid: {region_id}")
    if anchor_end != f"% figure-agent:end {selector_id}":
        raise SemanticRegionContractError(f"anchor_end_invalid: {region_id}")
    line_start = _positive_line(raw.get("line_start"), label="line_start")
    line_end = _positive_line(raw.get("line_end"), label="line_end")
    if line_end < line_start:
        raise SemanticRegionContractError(f"line_range_reversed: {region_id}")
    declared_source_hash = str(raw.get("source_sha256") or "")
    if not _SHA256_RE.fullmatch(declared_source_hash):
        raise SemanticRegionContractError(f"source_sha256_invalid: {region_id}")
    relative = path.relative_to(fixture_dir).as_posix()
    normalized = {
        "path": relative,
        "selector_id": selector_id,
        "anchor_start": anchor_start,
        "anchor_end": anchor_end,
        "source_sha256": declared_source_hash,
        "line_start": line_start,
        "line_end": line_end,
    }
    source_bytes = path.read_bytes()
    if declared_source_hash != _sha256_bytes(source_bytes):
        return {
            **normalized,
            "binding_state": "unbound",
            "binding_reason": "source_hash_mismatch",
        }
    lines = source_bytes.decode("utf-8").splitlines()
    starts = [index for index, line in enumerate(lines, start=1) if line == anchor_start]
    ends = [index for index, line in enumerate(lines, start=1) if line == anchor_end]
    if not starts or not ends:
        return {
            **normalized,
            "binding_state": "unbound",
            "binding_reason": "anchor_missing",
        }
    if len(starts) != 1 or len(ends) != 1:
        return {
            **normalized,
            "binding_state": "ambiguous",
            "binding_reason": "anchor_duplicated_in_source",
        }
    resolved_start, resolved_end = starts[0], ends[0]
    if resolved_start >= resolved_end:
        return {
            **normalized,
            "binding_state": "ambiguous",
            "binding_reason": "anchor_order_invalid",
        }
    if (line_start, line_end) != (resolved_start, resolved_end):
        return {
            **normalized,
            "binding_state": "ambiguous",
            "binding_reason": "line_snapshot_stale",
        }
    return {
        **normalized,
        "binding_state": "exact",
        "binding_reason": "anchors_and_snapshot_match",
        "resolved_line_start": resolved_start,
        "resolved_line_end": resolved_end,
    }


def load_semantic_region_contract(
    fixture_dir: Path,
    *,
    detector_page_geometry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load a region contract without guessing missing source identity."""
    fixture_dir = fixture_dir.resolve()
    contract_path = fixture_dir / "semantic_regions.yaml"
    spec_path = fixture_dir / "spec.yaml"
    if contract_path.is_symlink() or spec_path.is_symlink():
        raise SemanticRegionContractError("fixture_input_symlink")
    try:
        contract_bytes = contract_path.read_bytes()
        spec_bytes = spec_path.read_bytes()
    except FileNotFoundError as exc:
        raise SemanticRegionContractError("fixture_input_missing") from exc
    try:
        payload = yaml.safe_load(contract_bytes) or {}
    except yaml.YAMLError as exc:
        raise SemanticRegionContractError(f"semantic_regions_yaml_invalid: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise SemanticRegionContractError("semantic_regions_schema_invalid")
    geometry = _normalize_geometry(payload.get("page_geometry"))
    if detector_page_geometry is not None:
        detector_geometry = _normalize_geometry(detector_page_geometry)
        if detector_geometry != geometry:
            raise SemanticRegionContractError("detector_geometry_mismatch")
    try:
        spec = parse_spec(spec_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise SemanticRegionContractError(f"spec_invalid: {exc}") from exc
    panel_ids = {
        str(panel.get("id"))
        for panel in spec.get("panels", [])
        if isinstance(panel, dict) and panel.get("id") is not None
    }
    raw_regions = payload.get("regions")
    if not isinstance(raw_regions, list) or not raw_regions:
        raise SemanticRegionContractError("regions_missing")
    normalized_regions: list[dict[str, Any]] = []
    region_ids: set[str] = set()
    declared_anchors: set[tuple[str, str]] = set()
    for index, raw_region in enumerate(raw_regions):
        if not isinstance(raw_region, dict):
            raise SemanticRegionContractError(f"region_invalid: {index}")
        region_id = str(raw_region.get("id") or "")
        if not region_id or region_id in region_ids:
            raise SemanticRegionContractError(f"duplicate_region_id: {region_id or index}")
        region_ids.add(region_id)
        panel_id = str(raw_region.get("panel_id") or "")
        if panel_id not in panel_ids:
            raise SemanticRegionContractError(f"unknown_panel: {region_id}")
        try:
            bbox = normalize_bbox_pdf_cm(
                raw_region.get("bbox_pdf_cm"),
                label=f"regions[{region_id}].bbox_pdf_cm",
            )
        except ValueError as exc:
            raise SemanticRegionContractError(str(exc)) from exc
        if not _contains(geometry["crop_box_pdf_cm"], bbox):
            raise SemanticRegionContractError(f"outside_crop_box: {region_id}")
        source = _normalize_source(
            fixture_dir,
            raw_region.get("source"),
            region_id=region_id,
        )
        anchor_key = (source["anchor_start"], source["anchor_end"])
        if anchor_key in declared_anchors:
            raise SemanticRegionContractError(f"duplicate_anchor: {region_id}")
        declared_anchors.add(anchor_key)
        role = str(raw_region.get("role") or "")
        provenance = str(raw_region.get("provenance") or "")
        if not role:
            raise SemanticRegionContractError(f"role_missing: {region_id}")
        if not provenance:
            raise SemanticRegionContractError(f"provenance_missing: {region_id}")
        normalized_regions.append(
            {
                "id": region_id,
                "panel_id": panel_id,
                "role": role,
                "bbox_pdf_cm": bbox,
                "source": source,
                "provenance": provenance,
            }
        )
    core = {
        "schema": SCHEMA,
        "page_geometry": geometry,
        "regions": normalized_regions,
        "input_hashes": {
            "semantic_regions_sha256": _sha256_bytes(contract_bytes),
            "spec_sha256": _sha256_bytes(spec_bytes),
        },
    }
    normalized_json = _canonical_json(core)
    return {
        **core,
        "normalized_json": normalized_json,
        "normalized_sha256": _sha256_text(normalized_json),
    }
