"""Create and validate hash-bound 100/50/33 percent review previews.

The previews are evidence derived from one rendered PNG, not independent
artifacts.  Keeping that relationship in a small manifest prevents a reviewer
from accidentally inspecting an earlier layout after the canonical render has
changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image

SCHEMA = "figure-agent.review-scale-preview-manifest.v1"
PREVIEW_SCALES = (
    ("100pct", 1.0),
    ("50pct", 0.5),
    ("33pct", 0.33),
)
FRESH = "FRESH"
MISSING = "MISSING"
STALE = "STALE"
INVALID = "INVALID"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_path(render_png: Path) -> Path:
    return render_png.with_name(f"{render_png.stem}_review_scale_previews.json")


def preview_path(render_png: Path, label: str) -> Path:
    return render_png.with_name(f"{render_png.stem}_{label}.png")


def _expected_size(width: int, height: int, scale: float) -> tuple[int, int]:
    return max(1, round(width * scale)), max(1, round(height * scale))


def _relative_to_manifest(path: Path, manifest: Path) -> str:
    try:
        return path.relative_to(manifest.parent).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_manifest_path(manifest: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (manifest.parent / candidate).resolve()
    try:
        resolved.relative_to(manifest.parent.resolve())
    except ValueError:
        return None
    return resolved


def build_scale_previews(render_png: Path, output: Path | None = None) -> dict[str, Any]:
    """Regenerate every scale preview and return the evidence manifest.

    Files are written through same-directory temporary paths.  A partially
    generated set therefore cannot look fresh once the manifest is checked.
    """
    render_png = render_png.resolve()
    manifest = (output or manifest_path(render_png)).resolve()
    if not render_png.is_file():
        raise FileNotFoundError(render_png)
    if render_png.suffix.casefold() != ".png":
        raise ValueError("render_png_required")

    with Image.open(render_png) as image:
        source = image.convert("RGBA")
        width, height = source.size
        generated: list[tuple[Path, Path, str, float, tuple[int, int]]] = []
        for label, scale in PREVIEW_SCALES:
            destination = preview_path(render_png, label)
            temporary = destination.with_name(f".{destination.name}.tmp")
            expected = _expected_size(width, height, scale)
            if scale == 1.0:
                shutil.copyfile(render_png, temporary)
            else:
                source.resize(expected, Image.Resampling.LANCZOS).save(temporary, "PNG")
            generated.append((temporary, destination, label, scale, expected))

    previews: list[dict[str, Any]] = []
    for temporary, destination, label, scale, expected in generated:
        temporary.replace(destination)
        previews.append(
            {
                "label": label,
                "scale": scale,
                "path": _relative_to_manifest(destination, manifest),
                "sha256": _sha256(destination),
                "width_px": expected[0],
                "height_px": expected[1],
            }
        )
    payload = {
        "schema": SCHEMA,
        "render": {
            "path": _relative_to_manifest(render_png, manifest),
            "sha256": _sha256(render_png),
            "width_px": width,
            "height_px": height,
        },
        "previews": previews,
    }
    temporary_manifest = manifest.with_name(f".{manifest.name}.tmp")
    temporary_manifest.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary_manifest.replace(manifest)
    return payload


def preview_status(render_png: Path, output: Path | None = None) -> dict[str, Any]:
    """Return a deterministic freshness state for one render's preview set."""
    render_png = render_png.resolve()
    manifest = (output or manifest_path(render_png)).resolve()
    if not render_png.is_file():
        return {"state": MISSING, "reason": "render_png_missing", "manifest": manifest}
    if not manifest.is_file():
        return {"state": MISSING, "reason": "manifest_missing", "manifest": manifest}
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"state": INVALID, "reason": "manifest_invalid", "manifest": manifest}
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return {"state": INVALID, "reason": "manifest_schema_invalid", "manifest": manifest}
    render = payload.get("render")
    previews = payload.get("previews")
    if not isinstance(render, dict) or not isinstance(previews, list):
        return {"state": INVALID, "reason": "manifest_shape_invalid", "manifest": manifest}
    if render.get("sha256") != _sha256(render_png):
        return {"state": STALE, "reason": "render_hash_mismatch", "manifest": manifest}
    if render.get("path") != _relative_to_manifest(render_png, manifest):
        return {"state": STALE, "reason": "render_path_mismatch", "manifest": manifest}
    try:
        with Image.open(render_png) as image:
            width, height = image.size
    except OSError:
        return {"state": INVALID, "reason": "render_png_invalid", "manifest": manifest}
    if render.get("width_px") != width or render.get("height_px") != height:
        return {"state": STALE, "reason": "render_dimensions_mismatch", "manifest": manifest}

    expected = {label: scale for label, scale in PREVIEW_SCALES}
    seen: set[str] = set()
    for entry in previews:
        if not isinstance(entry, dict):
            return {"state": INVALID, "reason": "preview_entry_invalid", "manifest": manifest}
        label = entry.get("label")
        if label not in expected or label in seen or entry.get("scale") != expected[label]:
            return {"state": INVALID, "reason": "preview_set_invalid", "manifest": manifest}
        seen.add(label)
        path = _resolve_manifest_path(manifest, entry.get("path"))
        if path is None or path != preview_path(render_png, label).resolve():
            return {"state": INVALID, "reason": "preview_path_invalid", "manifest": manifest}
        if not path.is_file():
            return {"state": MISSING, "reason": f"preview_missing:{label}", "manifest": manifest}
        if entry.get("sha256") != _sha256(path):
            return {
                "state": STALE,
                "reason": f"preview_hash_mismatch:{label}",
                "manifest": manifest,
            }
        expected_width, expected_height = _expected_size(width, height, expected[label])
        try:
            with Image.open(path) as image:
                actual_size = image.size
        except OSError:
            return {"state": INVALID, "reason": f"preview_invalid:{label}", "manifest": manifest}
        if actual_size != (expected_width, expected_height):
            return {
                "state": STALE,
                "reason": f"preview_dimensions_mismatch:{label}",
                "manifest": manifest,
            }
        if entry.get("width_px") != expected_width or entry.get("height_px") != expected_height:
            return {
                "state": STALE,
                "reason": f"manifest_dimensions_mismatch:{label}",
                "manifest": manifest,
            }
    if seen != set(expected):
        return {"state": INVALID, "reason": "preview_set_incomplete", "manifest": manifest}
    return {"state": FRESH, "reason": "manifest_matches_render", "manifest": manifest}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate hash-bound review scale previews.")
    parser.add_argument("render_png", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.check:
            result = preview_status(args.render_png, args.json_output)
            print(json.dumps({**result, "manifest": str(result["manifest"])}, sort_keys=True))
            return 0 if result["state"] == FRESH else 1
        if args.json_output is None:
            raise ValueError("json_output_required")
        payload = build_scale_previews(args.render_png, args.json_output)
        print(json.dumps(payload, sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR review_scale_previews: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
