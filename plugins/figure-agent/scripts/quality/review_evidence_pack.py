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


def _fraction_box(value: object, size: tuple[int, int], *, label: str) -> list[int]:
    if not isinstance(value, list) or len(value) != 4:
        raise ReviewEvidencePackError(f"region_invalid: {label}")
    try:
        box = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise ReviewEvidencePackError(f"region_invalid: {label}") from exc
    if not all(0.0 <= item <= 1.0 for item in box) or not (
        box[0] < box[2] and box[1] < box[3]
    ):
        raise ReviewEvidencePackError(f"region_invalid: {label}")
    width, height = size
    return [
        round(box[0] * width),
        round(box[1] * height),
        round(box[2] * width),
        round(box[3] * height),
    ]


def build_review_evidence_pack(fixture_dir: Path) -> dict[str, Any]:
    fixture = fixture_dir.resolve()
    config_path = fixture / "evidence_regions.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("schema") != SCHEMA:
        raise ReviewEvidencePackError("evidence_region_schema_invalid")
    raw_render = fixture / str(config.get("raw_render"))
    repaired_render = fixture / str(config.get("repaired_render"))
    if any(path.is_symlink() or not path.is_file() for path in (raw_render, repaired_render)):
        raise ReviewEvidencePackError("evidence_render_missing")
    regions = config.get("regions")
    if not isinstance(regions, dict) or set(regions) != set(SCALES):
        raise ReviewEvidencePackError("evidence_region_set_invalid")

    output_root = fixture / "review" / "evidence"
    records: list[dict[str, str]] = []
    for variant in VARIANTS:
        render = repaired_render if variant == "repaired" else raw_render
        with Image.open(render) as opened:
            image = opened.convert("RGB")
        boxes = {
            scale: _fraction_box(regions[scale], image.size, label=scale)
            for scale in SCALES
        }
        variant_dir = output_root / variant
        variant_dir.mkdir(parents=True, exist_ok=True)
        paths = {scale: variant_dir / f"{scale}.png" for scale in SCALES}
        whole_path = variant_dir / "whole.png"
        overlay_path = variant_dir / "overlay.png"
        image.save(whole_path, format="PNG", optimize=False)
        for scale, path in paths.items():
            image.crop(boxes[scale]).save(path, format="PNG", optimize=False)
        overlay = image.copy()
        draw_attribution_box(
            ImageDraw.Draw(overlay), boxes["zoom"], attribution_state="exact"
        )
        overlay.save(overlay_path, format="PNG", optimize=False)
        for role, path in {
            "whole": whole_path,
            **paths,
            "overlay": overlay_path,
        }.items():
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
