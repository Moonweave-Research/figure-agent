"""Create deterministic, manifest-bound benchmark crops."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, UnidentifiedImageError

SCHEMA = "figure-agent.direct-svg-crop-authority.v1"
ALGORITHM = "pillow.crop.v1"
PANELS = {"C", "F"}


class CropAuthorityError(ValueError):
    """Raised when crop authority inputs or outputs violate the manifest."""


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CropAuthorityError(f"{field}_invalid")
    return value


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _safe_path(root: Path, value: Any, *, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise CropAuthorityError(f"{field}_path_invalid")
    relative = Path(value)
    unresolved = root / relative
    resolved = unresolved.resolve()
    if relative.is_absolute() or not resolved.is_relative_to(root) or unresolved.is_symlink():
        raise CropAuthorityError(f"{field}_path_unsafe")
    return resolved


def _validate_bbox(value: Any, *, width: int, height: int) -> tuple[int, int, int, int]:
    if (
        not isinstance(value, list)
        or len(value) != 4
        or any(not isinstance(item, int) or isinstance(item, bool) for item in value)
    ):
        raise CropAuthorityError("crop_bbox_invalid")
    left, top, right, bottom = value
    if left < 0 or top < 0 or right > width or bottom > height:
        raise CropAuthorityError("crop_out_of_bounds")
    if left >= right or top >= bottom:
        raise CropAuthorityError("crop_bbox_invalid")
    return left, top, right, bottom


def create_authority_crops(manifest_path: Path) -> dict[str, Any]:
    """Validate a crop manifest, write exact crops, and persist output hashes."""
    try:
        loaded = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise CropAuthorityError("manifest_invalid") from exc
    manifest = _mapping(loaded, "manifest")
    if manifest.get("schema") != SCHEMA:
        raise CropAuthorityError("manifest_schema_invalid")
    if manifest.get("algorithm") != ALGORITHM:
        raise CropAuthorityError("crop_algorithm_invalid")
    if manifest.get("publication_acceptance") != "not_claimed":
        raise CropAuthorityError("publication_claim_forbidden")

    root = manifest_path.parent.resolve()
    source = _mapping(manifest.get("source"), "source")
    source_path = _safe_path(root, source.get("path"), field="source")
    if not source_path.is_file():
        raise CropAuthorityError("source_missing")
    if source.get("sha256") != _sha256(source_path):
        raise CropAuthorityError("source_hash_mismatch")
    width = source.get("width")
    height = source.get("height")
    if (
        not isinstance(width, int)
        or isinstance(width, bool)
        or not isinstance(height, int)
        or isinstance(height, bool)
        or width <= 0
        or height <= 0
    ):
        raise CropAuthorityError("source_geometry_invalid")

    try:
        with Image.open(source_path) as opened:
            if opened.size != (width, height):
                raise CropAuthorityError("source_geometry_mismatch")
            source_image = opened.convert("RGB")
    except UnidentifiedImageError as exc:
        raise CropAuthorityError("source_image_invalid") from exc

    crops = _mapping(manifest.get("crops"), "crops")
    if set(crops) != PANELS:
        raise CropAuthorityError("panels_must_be_C_and_F")
    for panel in sorted(PANELS):
        crop = _mapping(crops[panel], f"panel_{panel}_crop")
        bbox = _validate_bbox(crop.get("bbox"), width=width, height=height)
        output_path = _safe_path(root, crop.get("output"), field=f"panel_{panel}_output")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        source_image.crop(bbox).save(output_path, format="PNG")
        crop["sha256"] = _sha256(output_path)

    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return manifest
