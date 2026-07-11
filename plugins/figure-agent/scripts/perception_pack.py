#!/usr/bin/env python3
"""Build the v0.4.2 perception data-only pack from compile artifacts."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

import fixture_identity
import yaml
from PIL import Image, ImageDraw, ImageFont

try:
    import pdfplumber
except ImportError as exc:  # pragma: no cover - exercised only in misconfigured envs
    raise ImportError("pdfplumber required for perception pack — uv add pdfplumber") from exc


CM_PER_PT = 2.54 / 72.0
SCHEMA_VERSION = "0.4.2"


def build_perception_pack(name: str) -> None:
    """Write extract.yaml and overlay.png for a compiled figure."""
    fixture_identity.validate_fixture_name(name)
    figure_dir = _resolve_figure_dir(name)
    build_dir = figure_dir / "build"
    pdf_path = build_dir / f"{name}.pdf"
    png_path = build_dir / f"{name}.png"
    perception_dir = build_dir / "perception"

    if not pdf_path.exists():
        raise FileNotFoundError(f"Missing PDF for perception pack: {pdf_path}")
    if not png_path.exists():
        raise FileNotFoundError(f"Missing PNG for perception overlay: {png_path}")

    extract = _extract_pdf(pdf_path)
    extract["source"]["pdf_path"] = _display_path(pdf_path)

    _reset_perception_dir(perception_dir)
    extract_path = perception_dir / "extract.yaml"
    overlay_path = perception_dir / "overlay.png"
    extract_path.write_text(
        yaml.safe_dump(extract, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    _write_overlay(png_path, overlay_path, extract)


def _resolve_figure_dir(name: str) -> Path:
    cwd = Path.cwd()
    if (cwd / "build" / f"{name}.pdf").exists():
        return cwd

    repo_root = Path(__file__).resolve().parents[1]
    example_dir = repo_root / "examples" / name
    if (example_dir / "build" / f"{name}.pdf").exists():
        return example_dir

    return example_dir


def _display_path(path: Path) -> str:
    repo_root = Path(__file__).resolve().parents[1]
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _reset_perception_dir(perception_dir: Path) -> None:
    perception_dir.mkdir(parents=True, exist_ok=True)
    for child in perception_dir.iterdir():
        if child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)


def _extract_pdf(pdf_path: Path) -> dict[str, Any]:
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            raise RuntimeError(f"PDF has no pages: {pdf_path}")
        page = pdf.pages[0]
        lines = [_line_payload(index, obj) for index, obj in enumerate(page.lines, start=1)]
        curves = [_curve_payload(index, obj) for index, obj in enumerate(page.curves, start=1)]
        rects = [_rect_payload(index, obj) for index, obj in enumerate(page.rects, start=1)]
        chars = [_char_payload(index, obj) for index, obj in enumerate(page.chars, start=1)]

        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_manifests": {
                "visual_findings": "visual_findings/manifest.json",
            },
            "source": {
                "pdf_path": "",
                "pdf_size_cm": [_cm(page.width), _cm(page.height)],
            },
            "coordinate_space": {
                "pdf_origin": "top_left",
                "y_axis": "down",
                "units": "cm",
            },
            "primitives": {
                "lines": lines,
                "curves": curves,
                "rects": rects,
                "chars": chars,
            },
            "counts": {
                "lines": len(lines),
                "curves": len(curves),
                "rects": len(rects),
                "chars": len(chars),
                "endpoints_total": 2 * (len(lines) + len(curves)),
            },
        }


def _line_payload(index: int, obj: dict[str, Any]) -> dict[str, Any]:
    pts = _points_cm(obj.get("pts", []))
    if len(pts) >= 2:
        start = pts[0]
        end = pts[-1]
    else:
        start = [_cm(obj["x0"]), _cm(obj["top"])]
        end = [_cm(obj["x1"]), _cm(obj["bottom"])]
    return {
        "id": f"l_{index:04d}",
        "x0": start[0],
        "y0": start[1],
        "x1": end[0],
        "y1": end[1],
        "stroke_rgb": _rgb(obj.get("stroking_color")),
        "linewidth_pt": _round(obj.get("linewidth", 0.0)),
    }


def _curve_payload(index: int, obj: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"c_{index:04d}",
        "pts": _points_cm(obj.get("pts", [])),
        "stroke_rgb": _rgb(obj.get("stroking_color")),
        "linewidth_pt": _round(obj.get("linewidth", 0.0)),
        "fill_rgb": _rgb(obj.get("non_stroking_color")) if obj.get("fill") else None,
    }


def _rect_payload(index: int, obj: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"r_{index:04d}",
        "x0": _cm(obj["x0"]),
        "y0": _cm(obj["top"]),
        "x1": _cm(obj["x1"]),
        "y1": _cm(obj["bottom"]),
        "stroke_rgb": _rgb(obj.get("stroking_color")),
        "fill_rgb": _rgb(obj.get("non_stroking_color")) if obj.get("fill") else None,
    }


def _char_payload(index: int, obj: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"ch_{index:04d}",
        "text": obj.get("text", ""),
        "x0": _cm(obj["x0"]),
        "y0": _cm(obj["top"]),
        "x1": _cm(obj["x1"]),
        "y1": _cm(obj["bottom"]),
        "fontname": obj.get("fontname", ""),
        "size_pt": _round(obj.get("size", 0.0)),
    }


def _points_cm(points: list[tuple[float, float]]) -> list[list[float]]:
    return [[_cm(x), _cm(y)] for x, y in points]


def _cm(value_pt: float) -> float:
    return _round(value_pt * CM_PER_PT)


def _round(value: float) -> float:
    return round(float(value), 4)


def _rgb(color: Any) -> list[float] | None:
    if color is None:
        return None
    if isinstance(color, int | float):
        value = _round(color)
        return [value, value, value]
    values = list(color)
    if len(values) == 1:
        value = _round(values[0])
        return [value, value, value]
    if len(values) >= 3:
        return [_round(values[0]), _round(values[1]), _round(values[2])]
    return None


def _write_overlay(png_path: Path, overlay_path: Path, extract: dict[str, Any]) -> None:
    with Image.open(png_path) as source:
        image = source.convert("RGBA")

    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    page_w_cm, page_h_cm = extract["source"]["pdf_size_cm"]
    radius_px = 3

    for primitive in extract["primitives"]["lines"]:
        color = _overlay_color(primitive.get("stroke_rgb"))
        _draw_endpoint(
            draw,
            font,
            primitive["id"],
            primitive["x0"],
            primitive["y0"],
            color,
            image.size,
            page_w_cm,
            page_h_cm,
            radius_px,
        )
        _draw_endpoint(
            draw,
            font,
            primitive["id"],
            primitive["x1"],
            primitive["y1"],
            color,
            image.size,
            page_w_cm,
            page_h_cm,
            radius_px,
        )

    for primitive in extract["primitives"]["curves"]:
        points = primitive["pts"]
        if not points:
            continue
        color = _overlay_color(primitive.get("stroke_rgb") or primitive.get("fill_rgb"))
        first = points[0]
        last = points[-1]
        _draw_endpoint(
            draw,
            font,
            primitive["id"],
            first[0],
            first[1],
            color,
            image.size,
            page_w_cm,
            page_h_cm,
            radius_px,
        )
        _draw_endpoint(
            draw,
            font,
            primitive["id"],
            last[0],
            last[1],
            color,
            image.size,
            page_w_cm,
            page_h_cm,
            radius_px,
        )

    image.save(overlay_path)


def _draw_endpoint(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.ImageFont,
    label: str,
    x_cm: float,
    y_cm: float,
    color: tuple[int, int, int, int],
    image_size: tuple[int, int],
    page_w_cm: float,
    page_h_cm: float,
    radius_px: int,
) -> None:
    x_px = round(x_cm / page_w_cm * image_size[0])
    y_px = round(y_cm / page_h_cm * image_size[1])
    draw.ellipse(
        (
            x_px - radius_px,
            y_px - radius_px,
            x_px + radius_px,
            y_px + radius_px,
        ),
        fill=color,
        outline=(255, 255, 255, 220),
    )
    text_xy = (x_px + radius_px + 2, y_px + radius_px + 2)
    draw.text((text_xy[0] + 1, text_xy[1] + 1), label, font=font, fill=(255, 255, 255, 220))
    draw.text(text_xy, label, font=font, fill=color)


def _overlay_color(rgb: list[float] | None) -> tuple[int, int, int, int]:
    if rgb is None:
        return (0, 0, 0, 255)
    values = [max(0, min(255, round(channel * 255))) for channel in rgb[:3]]
    return (values[0], values[1], values[2], 255)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0.4.2 perception data-only pack.")
    parser.add_argument("name", help="figure name")
    args = parser.parse_args()
    try:
        fixture_identity.validate_fixture_name(args.name)
    except ValueError as exc:
        print(f"perception_pack.py: {exc}", file=sys.stderr)
        return 1
    build_perception_pack(args.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
