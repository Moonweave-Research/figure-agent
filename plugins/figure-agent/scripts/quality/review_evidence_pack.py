from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageDraw

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from visual_finding_artifacts import draw_attribution_box  # noqa: E402

SCHEMA = "figure-agent.review-evidence-pack.v1"
VARIANTS = ("raw", "verified", "repaired")
SCALES = ("panel", "object_relation", "zoom")


class ReviewEvidencePackError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_render_file(root: Path, relative_value: object) -> Path:
    relative = Path(str(relative_value or ""))
    candidate = (root / relative).resolve()
    if (
        not relative.parts
        or relative.is_absolute()
        or ".." in relative.parts
        or not candidate.is_relative_to(root)
        or candidate.is_symlink()
        or not candidate.is_file()
    ):
        raise ReviewEvidencePackError(f"evidence_render_unsafe: {relative}")
    return candidate


def _fraction_box(value: object, size: tuple[int, int], *, label: str) -> list[int]:
    if not isinstance(value, list) or len(value) != 4:
        raise ReviewEvidencePackError(f"region_invalid: {label}")
    try:
        box = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise ReviewEvidencePackError(f"region_invalid: {label}") from exc
    if not all(0.0 <= item <= 1.0 for item in box) or not (box[0] < box[2] and box[1] < box[3]):
        raise ReviewEvidencePackError(f"region_invalid: {label}")
    width, height = size
    return [
        round(box[0] * width),
        round(box[1] * height),
        round(box[2] * width),
        round(box[3] * height),
    ]


def _variant_images(image: Image.Image, boxes: dict[str, list[int]]) -> dict[str, Image.Image]:
    overlay = image.copy()
    draw_attribution_box(ImageDraw.Draw(overlay), boxes["zoom"], attribution_state="exact")
    return {
        "whole": image,
        **{scale: image.crop(boxes[scale]) for scale in SCALES},
        "overlay": overlay,
    }


def build_review_evidence_pack(fixture_dir: Path) -> dict[str, Any]:
    fixture = fixture_dir.resolve()
    config_path = fixture / "evidence_regions.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("schema") != SCHEMA:
        raise ReviewEvidencePackError("evidence_region_schema_invalid")
    raw_render = _safe_render_file(fixture, config.get("raw_render"))
    repaired_render = _safe_render_file(fixture, config.get("repaired_render"))
    regions = config.get("regions")
    if not isinstance(regions, dict) or set(regions) != set(SCALES):
        raise ReviewEvidencePackError("evidence_region_set_invalid")

    output_root = fixture / "review" / "evidence"
    records: list[dict[str, str]] = []
    for variant in VARIANTS:
        render = repaired_render if variant == "repaired" else raw_render
        with Image.open(render) as opened:
            image = opened.convert("RGB")
        boxes = {scale: _fraction_box(regions[scale], image.size, label=scale) for scale in SCALES}
        variant_dir = output_root / variant
        variant_dir.mkdir(parents=True, exist_ok=True)
        for role, artifact in _variant_images(image, boxes).items():
            path = variant_dir / f"{role}.png"
            artifact.save(path, format="PNG", optimize=False)
            records.append(
                {
                    "variant": variant,
                    "role": role,
                    "path": path.relative_to(fixture).as_posix(),
                    "sha256": _sha256(path),
                }
            )
    manifest = {
        "schema": SCHEMA,
        "fixture": fixture.name,
        "regions": regions,
        "artifacts": records,
        "acceptance": "review_evidence_only",
        "publication_acceptance": "not_claimed",
    }
    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def verify_review_evidence_pack(fixture_dir: Path) -> dict[str, Any]:
    fixture = fixture_dir.resolve()
    config = yaml.safe_load((fixture / "evidence_regions.yaml").read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("schema") != SCHEMA:
        raise ReviewEvidencePackError("evidence_region_schema_invalid")
    regions = config.get("regions")
    if not isinstance(regions, dict) or set(regions) != set(SCALES):
        raise ReviewEvidencePackError("evidence_region_set_invalid")

    render_paths = {
        "raw": _safe_render_file(fixture, config.get("raw_render")),
        "verified": _safe_render_file(fixture, config.get("raw_render")),
        "repaired": _safe_render_file(fixture, config.get("repaired_render")),
    }

    manifest_path = fixture / "review" / "evidence" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("schema") != SCHEMA
        or manifest.get("fixture") != fixture.name
        or manifest.get("regions") != regions
        or manifest.get("acceptance") != "review_evidence_only"
        or manifest.get("publication_acceptance") != "not_claimed"
    ):
        raise ReviewEvidencePackError("evidence_manifest_contract_mismatch")
    records = manifest.get("artifacts")
    if not isinstance(records, list):
        raise ReviewEvidencePackError("evidence_manifest_artifacts_invalid")
    by_key = {
        (str(item.get("variant")), str(item.get("role"))): item
        for item in records
        if isinstance(item, dict)
    }
    expected_keys = {
        (variant, role) for variant in VARIANTS for role in ("whole", *SCALES, "overlay")
    }
    if len(records) != len(expected_keys) or set(by_key) != expected_keys:
        raise ReviewEvidencePackError("evidence_manifest_artifact_set_invalid")

    for variant, render in render_paths.items():
        with Image.open(render) as opened:
            image = opened.convert("RGB")
        boxes = {scale: _fraction_box(regions[scale], image.size, label=scale) for scale in SCALES}
        for role, expected in _variant_images(image, boxes).items():
            record = by_key[(variant, role)]
            path = fixture / str(record.get("path"))
            canonical = f"review/evidence/{variant}/{role}.png"
            if path.is_symlink() or not path.is_file() or record.get("path") != canonical:
                raise ReviewEvidencePackError(
                    f"evidence_artifact_missing_or_unsafe: {variant}.{role}"
                )
            if record.get("sha256") != _sha256(path):
                raise ReviewEvidencePackError(f"evidence_manifest_hash_mismatch: {variant}.{role}")
            with Image.open(path) as opened:
                actual = opened.convert("RGB")
            if actual.size != expected.size or actual.tobytes() != expected.tobytes():
                raise ReviewEvidencePackError(f"review_evidence_stale: {variant}.{role}")
    return manifest
