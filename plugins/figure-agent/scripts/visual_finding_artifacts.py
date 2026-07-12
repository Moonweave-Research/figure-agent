#!/usr/bin/env python3
"""Emit deterministic review overlays and crops for visual-clash findings."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

SCHEMA = "figure-agent.visual-finding-artifacts.v1"
_STYLES = {
    "exact": {"color": "#0072B2", "pattern": "solid"},
    "ambiguous": {"color": "#E69F00", "pattern": "dash"},
    "unbound": {"color": "#CC79A7", "pattern": "dot"},
}
_SAFE_FINDING_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SAFE_ARTIFACT_BASE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._-]*$")


class VisualFindingArtifactError(ValueError):
    """Raised when review artifacts cannot be grounded in detector evidence."""


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _bbox(value: object, *, finding_id: str) -> list[int]:
    if not isinstance(value, list) or len(value) != 4:
        raise VisualFindingArtifactError(f"finding_bbox_invalid: {finding_id}")
    try:
        bbox = [int(round(float(item))) for item in value]
    except (TypeError, ValueError) as exc:
        raise VisualFindingArtifactError(f"finding_bbox_invalid: {finding_id}") from exc
    if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        raise VisualFindingArtifactError(f"finding_bbox_invalid: {finding_id}")
    return bbox


def _clamp(bbox: list[int], size: tuple[int, int], *, padding: int = 0) -> list[int]:
    width, height = size
    value = [
        max(0, bbox[0] - padding),
        max(0, bbox[1] - padding),
        min(width, bbox[2] + padding),
        min(height, bbox[3] + padding),
    ]
    if value[2] <= value[0] or value[3] <= value[1]:
        raise VisualFindingArtifactError("finding_bbox_outside_render")
    return value


def _draw_patterned_box(
    draw: ImageDraw.ImageDraw,
    bbox: list[int],
    *,
    color: str,
    pattern: str,
) -> None:
    if pattern == "solid":
        draw.rectangle(bbox, outline=color, width=4)
        return
    step = 12 if pattern == "dash" else 7
    length = 7 if pattern == "dash" else 2
    x0, y0, x1, y1 = bbox
    for start in range(x0, x1, step):
        draw.line((start, y0, min(start + length, x1), y0), fill=color, width=4)
        draw.line((start, y1, min(start + length, x1), y1), fill=color, width=4)
    for start in range(y0, y1, step):
        draw.line((x0, start, x0, min(start + length, y1)), fill=color, width=4)
        draw.line((x1, start, x1, min(start + length, y1)), fill=color, width=4)


def draw_attribution_box(
    draw: ImageDraw.ImageDraw, bbox: list[int], *, attribution_state: str
) -> None:
    """Draw the shared exact/ambiguous/unbound visual-attribution grammar."""
    state = attribution_state if attribution_state in _STYLES else "unbound"
    style = _STYLES[state]
    _draw_patterned_box(
        draw,
        bbox,
        color=style["color"],
        pattern=style["pattern"],
    )


def _write_overlay(
    source: Image.Image,
    output: Path,
    *,
    bbox: list[int],
    finding_id: str,
    state: str,
) -> None:
    image = source.convert("RGBA")
    draw = ImageDraw.Draw(image)
    style = _STYLES[state]
    _draw_patterned_box(
        draw,
        bbox,
        color=style["color"],
        pattern=style["pattern"],
    )
    label = f"{finding_id} {state}"
    font = ImageFont.load_default()
    label_box = draw.textbbox((bbox[0], max(0, bbox[1] - 13)), label, font=font)
    draw.rectangle(label_box, fill="white")
    draw.text(
        (bbox[0], max(0, bbox[1] - 13)),
        label,
        fill=style["color"],
        font=font,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=False)


def _fallback_pdf_bbox(
    pdf_path: Path,
    bbox_px: list[int],
    image_size: tuple[int, int],
) -> list[float]:
    """Map rendered pixels to PDF centimetres using the installed Poppler tool."""
    try:
        result = subprocess.run(
            ["pdfinfo", str(pdf_path)],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:  # pragma: no cover - environment failure
        raise VisualFindingArtifactError("pdfinfo_unavailable") from exc
    if result.returncode:
        raise VisualFindingArtifactError("render_pdf_unreadable")
    match = re.search(
        r"^Page size:\s*([0-9.]+)\s+x\s+([0-9.]+)\s+pts",
        result.stdout,
        flags=re.MULTILINE,
    )
    if not match:
        raise VisualFindingArtifactError("render_pdf_page_size_unknown")
    width_cm = float(match.group(1)) * 2.54 / 72.0
    height_cm = float(match.group(2)) * 2.54 / 72.0
    width_px, height_px = image_size
    return [
        round(bbox_px[0] / width_px * width_cm, 6),
        round((height_px - bbox_px[3]) / height_px * height_cm, 6),
        round(bbox_px[2] / width_px * width_cm, 6),
        round((height_px - bbox_px[1]) / height_px * height_cm, 6),
    ]


def _pdf_bbox(
    candidate: dict[str, Any],
    *,
    pdf_path: Path,
    bbox_px: list[int],
    image_size: tuple[int, int],
) -> tuple[list[float], str]:
    attribution = candidate.get("attribution")
    if isinstance(attribution, dict):
        value = attribution.get("bbox_pdf_cm")
        if isinstance(value, list) and len(value) == 4:
            try:
                return [float(item) for item in value], "validated_attribution"
            except (TypeError, ValueError):
                pass
    return (
        _fallback_pdf_bbox(pdf_path, bbox_px, image_size),
        "display_page_geometry_fallback",
    )


def build_visual_finding_artifacts(
    fixture_dir: Path,
    *,
    artifact_base: str | None = None,
) -> dict[str, Any]:
    """Build a review-only artifact set without modifying manuscript outputs."""
    fixture_dir = fixture_dir.resolve()
    build_dir = fixture_dir / "build"
    name = fixture_dir.name
    artifact_base = artifact_base or name
    if not _SAFE_ARTIFACT_BASE.fullmatch(artifact_base):
        raise VisualFindingArtifactError("artifact_base_invalid")
    png_path = build_dir / f"{artifact_base}.png"
    pdf_path = build_dir / f"{artifact_base}.pdf"
    report_path = build_dir / "visual_clash.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise VisualFindingArtifactError("visual_clash_report_invalid") from exc
    candidates = report.get("candidates") if isinstance(report, dict) else None
    if not isinstance(candidates, list):
        raise VisualFindingArtifactError("visual_clash_candidates_invalid")
    artifact_dir = build_dir / "perception" / "visual_findings"
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir)
    overlays_dir = artifact_dir / "overlays"
    crops_dir = artifact_dir / "crops"
    overlays_dir.mkdir(parents=True)
    crops_dir.mkdir(parents=True)
    with Image.open(png_path) as opened:
        source = opened.convert("RGB")
    records: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            raise VisualFindingArtifactError(f"visual_clash_candidate_invalid: {index}")
        finding_id = str(candidate.get("id") or f"VC{index:03d}")
        if not _SAFE_FINDING_ID.fullmatch(finding_id):
            raise VisualFindingArtifactError(f"finding_id_invalid: {finding_id}")
        bbox = _clamp(_bbox(candidate.get("bbox_px"), finding_id=finding_id), source.size)
        attribution = candidate.get("attribution")
        state = (
            str(attribution.get("state"))
            if isinstance(attribution, dict)
            else "unbound"
        )
        if state not in _STYLES:
            state = "unbound"
        bbox_pdf_cm, bbox_source = _pdf_bbox(
            candidate,
            pdf_path=pdf_path,
            bbox_px=bbox,
            image_size=source.size,
        )
        overlay_relative = Path("visual_findings") / "overlays" / f"{finding_id}.png"
        crop_relative = Path("visual_findings") / "crops" / f"{finding_id}.png"
        overlay_path = build_dir / "perception" / overlay_relative
        crop_path = build_dir / "perception" / crop_relative
        _write_overlay(
            source,
            overlay_path,
            bbox=bbox,
            finding_id=finding_id,
            state=state,
        )
        crop_box = _clamp(bbox, source.size, padding=12)
        source.crop(crop_box).save(crop_path, format="PNG", optimize=False)
        records.append(
            {
                "finding_id": finding_id,
                "attribution_state": state,
                "input_render_sha256": _sha256(png_path),
                "bbox_px": bbox,
                "bbox_pdf_cm": bbox_pdf_cm,
                "bbox_pdf_cm_source": bbox_source,
                "overlay_path": overlay_relative.as_posix(),
                "overlay_sha256": _sha256(overlay_path),
                "crop_path": crop_relative.as_posix(),
                "crop_sha256": _sha256(crop_path),
            }
        )
    manifest = {
        "schema": SCHEMA,
        "fixture": name,
        "artifact_base": artifact_base,
        "input_render_sha256": _sha256(png_path),
        "input_visual_clash_sha256": _sha256(report_path),
        "finding_count": len(records),
        "findings": records,
        "acceptance": "review_evidence_only",
    }
    manifest_path = artifact_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _resolve_fixture(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_dir():
        return candidate
    if Path.cwd().name == value and (Path.cwd() / "build").is_dir():
        return Path.cwd()
    return Path(__file__).resolve().parents[1] / "examples" / value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture")
    parser.add_argument("--artifact-base")
    args = parser.parse_args()
    build_visual_finding_artifacts(
        _resolve_fixture(args.fixture),
        artifact_base=args.artifact_base,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
