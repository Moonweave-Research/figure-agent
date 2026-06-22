"""Deterministic image comparison for candidate render evidence."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _read_ppm(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    tokens: list[str] = []
    for line in path.read_text(encoding="ascii").splitlines():
        stripped = line.partition("#")[0].strip()
        if stripped:
            tokens.extend(stripped.split())
    if len(tokens) < 4 or tokens[0] != "P3":
        raise ValueError("unsupported image format")
    width = int(tokens[1])
    height = int(tokens[2])
    max_value = int(tokens[3])
    if width <= 0 or height <= 0 or max_value <= 0:
        raise ValueError("invalid PPM dimensions")
    raw = [int(value) for value in tokens[4:]]
    expected = width * height * 3
    if len(raw) != expected:
        raise ValueError("invalid PPM pixel count")
    scale = 255 / max_value
    pixels = [
        (
            round(raw[index] * scale),
            round(raw[index + 1] * scale),
            round(raw[index + 2] * scale),
        )
        for index in range(0, len(raw), 3)
    ]
    return width, height, pixels


def _read_image(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    if path.suffix.lower() == ".ppm" or path.read_bytes().lstrip().startswith(b"P3"):
        return _read_ppm(path)
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError("PIL not available for non-PPM image comparison") from exc
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        return rgb.width, rgb.height, list(rgb.getdata())


def _diff_pixels(
    before_pixels: list[tuple[int, int, int]],
    after_pixels: list[tuple[int, int, int]],
    width: int,
) -> dict[str, Any]:
    diffs: list[int] = []
    changed: list[tuple[int, int]] = []
    for index, (before, after) in enumerate(zip(before_pixels, after_pixels, strict=True)):
        diff = max(abs(before[channel] - after[channel]) for channel in range(3))
        diffs.append(diff)
        if diff:
            changed.append((index % width, index // width))
    if not diffs:
        return {"pixel_diff_mean": 0.0, "pixel_diff_max": 0, "changed_bbox": None}
    bbox = None
    if changed:
        xs = [item[0] for item in changed]
        ys = [item[1] for item in changed]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
    return {
        "pixel_diff_mean": sum(diffs) / len(diffs),
        "pixel_diff_max": max(diffs),
        "changed_bbox": bbox,
    }


def compare_image_pair(before_path: Path, after_path: Path) -> dict[str, Any]:
    before_width, before_height, before_pixels = _read_image(before_path)
    after_width, after_height, after_pixels = _read_image(after_path)
    before = {
        "path": before_path.as_posix(),
        "dimensions": [before_width, before_height],
        "sha256": _sha256_file(before_path),
    }
    after = {
        "path": after_path.as_posix(),
        "dimensions": [after_width, after_height],
        "sha256": _sha256_file(after_path),
    }
    if (before_width, before_height) != (after_width, after_height):
        return {
            "status": "rendered_needs_human_review",
            "before": before,
            "after": after,
            "visual_deltas": {},
            "diagnostics": [
                {
                    "stage": "evaluate",
                    "category": "dimension_mismatch",
                    "message": "before and after images have different dimensions",
                }
            ],
        }
    return {
        "status": "rendered_needs_human_review",
        "before": before,
        "after": after,
        "visual_deltas": _diff_pixels(before_pixels, after_pixels, before_width),
        "diagnostics": [],
    }
