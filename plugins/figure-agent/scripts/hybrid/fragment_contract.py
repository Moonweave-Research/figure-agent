"""Validate deterministic, self-contained semantic SVG fragment packages."""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

SCHEMA = "figure-agent.semantic-fragment.v1"
TIKZ_OWNERSHIP = {"global_panel_composition", "text_labels", "inter_panel_arrows"}


class FragmentContractError(ValueError):
    """Raised when a semantic fragment violates its declared contract."""


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _safe_file(base: Path, value: Any, *, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise FragmentContractError(f"{field}_path_invalid")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise FragmentContractError(f"{field}_path_unsafe")
    path = base / relative
    if path.is_symlink() or not path.is_file():
        raise FragmentContractError(f"{field}_missing")
    return path


def _verify_hashed_file(base: Path, item: Any, *, field: str) -> Path:
    if not isinstance(item, dict):
        raise FragmentContractError(f"{field}_invalid")
    path = _safe_file(base, item.get("path"), field=field)
    if item.get("sha256") != _sha256(path):
        raise FragmentContractError(f"{field}_hash_mismatch")
    return path


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _validate_svg(
    svg_path: Path,
    *,
    expected_view_box: list[Any],
    semantic_ids: set[str],
    allowed_assets: set[str],
) -> set[str]:
    text = svg_path.read_text(encoding="utf-8")
    if re.search(r"<!DOCTYPE|<!ENTITY", text, flags=re.IGNORECASE):
        raise FragmentContractError("doctype_forbidden")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise FragmentContractError("svg_xml_invalid") from exc
    if _local_name(root.tag) != "svg":
        raise FragmentContractError("svg_root_invalid")
    actual_view_box = root.get("viewBox")
    if actual_view_box is None:
        raise FragmentContractError("view_box_missing")
    try:
        actual_values = [float(value) for value in actual_view_box.split()]
        expected_values = [float(value) for value in expected_view_box]
    except (TypeError, ValueError) as exc:
        raise FragmentContractError("view_box_invalid") from exc
    if len(actual_values) != 4 or actual_values != expected_values:
        raise FragmentContractError("view_box_mismatch")

    claimed_ids: set[str] = set()
    seen_ids: set[str] = set()
    for element in root.iter():
        if _local_name(element.tag) == "script":
            raise FragmentContractError("script_forbidden")
        if _local_name(element.tag) == "style":
            raise FragmentContractError("ambient_style_forbidden")
        element_id = element.get("id")
        if element_id:
            if element_id in seen_ids:
                raise FragmentContractError("svg_id_duplicate")
            seen_ids.add(element_id)
        if element.get("data-semantic") == "true":
            if not element_id:
                raise FragmentContractError("semantic_id_missing")
            claimed_ids.add(element_id)
        for raw_name, raw_value in element.attrib.items():
            name = _local_name(raw_name).lower()
            value = str(raw_value).strip()
            if name.startswith("on"):
                raise FragmentContractError("event_handler_forbidden")
            if name == "style" and re.search(r"font-family|@import|url\s*\(", value, re.I):
                raise FragmentContractError("ambient_style_forbidden")
            if name not in {"href", "src"}:
                continue
            if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value) or value.startswith("//"):
                raise FragmentContractError("external_url_forbidden")
            if Path(value).is_absolute() or ".." in Path(value).parts:
                raise FragmentContractError("asset_path_unsafe")
            if value.startswith("#"):
                continue
            if value not in allowed_assets:
                raise FragmentContractError("asset_not_allowlisted")

    if claimed_ids != semantic_ids:
        raise FragmentContractError("semantic_id_mismatch")
    return claimed_ids


def validate_fragment_package(manifest_path: Path) -> dict[str, Any]:
    """Validate a fragment manifest and every file it binds."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise FragmentContractError("manifest_invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise FragmentContractError("manifest_schema_invalid")
    base = manifest_path.parent
    view_box = manifest.get("view_box")
    if not isinstance(view_box, list) or len(view_box) != 4:
        raise FragmentContractError("view_box_invalid")

    objects = manifest.get("semantic_objects")
    if not isinstance(objects, list) or not objects:
        raise FragmentContractError("semantic_objects_invalid")
    semantic_ids: set[str] = set()
    for item in objects:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise FragmentContractError("semantic_object_invalid")
        object_id = item["id"]
        if not object_id or object_id in semantic_ids:
            raise FragmentContractError("semantic_object_duplicate")
        semantic_ids.add(object_id)

    relations = manifest.get("relations")
    if not isinstance(relations, list):
        raise FragmentContractError("relations_invalid")
    for relation in relations:
        if not isinstance(relation, dict) or not isinstance(relation.get("predicate"), str):
            raise FragmentContractError("relation_invalid")
        if (
            relation.get("subject") not in semantic_ids
            or relation.get("object") not in semantic_ids
        ):
            raise FragmentContractError("relation_object_unknown")

    ownership = manifest.get("ownership")
    if not isinstance(ownership, dict):
        raise FragmentContractError("ownership_invalid")
    if set(ownership.get("tikz") or []) != TIKZ_OWNERSHIP:
        raise FragmentContractError("tikz_ownership_boundary_invalid")
    if ownership.get("svg") != ["complex_geometry"]:
        raise FragmentContractError("svg_ownership_boundary_invalid")

    _verify_hashed_file(base, manifest.get("generator"), field="generator")
    inputs = manifest.get("inputs")
    if not isinstance(inputs, list):
        raise FragmentContractError("inputs_invalid")
    for item in inputs:
        _verify_hashed_file(base, item, field="input")

    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise FragmentContractError("assets_invalid")
    allowed_assets: set[str] = set()
    for item in assets:
        _verify_hashed_file(base, item, field="asset")
        allowed_assets.add(str(item["path"]))

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise FragmentContractError("artifacts_invalid")
    svg_path = _verify_hashed_file(base, artifacts.get("svg"), field="svg")
    _verify_hashed_file(base, artifacts.get("pdf"), field="pdf")
    claimed_ids = _validate_svg(
        svg_path,
        expected_view_box=view_box,
        semantic_ids=semantic_ids,
        allowed_assets=allowed_assets,
    )
    toolchain = manifest.get("toolchain")
    if not isinstance(toolchain, dict) or not toolchain.get("svg_to_pdf"):
        raise FragmentContractError("toolchain_invalid")
    if manifest.get("publication_acceptance") != "not_claimed":
        raise FragmentContractError("publication_claim_forbidden")
    return {
        "schema": SCHEMA,
        "semantic_ids": sorted(claimed_ids),
        "publication_acceptance": "not_claimed",
    }
