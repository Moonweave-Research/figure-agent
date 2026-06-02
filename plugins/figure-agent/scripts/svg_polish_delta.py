"""Generate before/after review inputs for SVG polish recipes."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops
from quality_manifest import REPO_ROOT, file_sha256
from svg_polish_recipe import (
    SVG_POLISH_RECIPE_RELATIVE_PATH,
    SvgPolishRecipeError,
    load_svg_polish_recipe,
    svg_polish_recipe_is_stale,
)

SCHEMA = "figure-agent.svg-polish-delta.v1"
SVG_POLISH_DELTA_DIR = "polish/aesthetic_delta"
SVG_POLISH_DELTA_MANIFEST_RELATIVE_PATH = f"{SVG_POLISH_DELTA_DIR}/delta_manifest.json"
Renderer = Callable[[Path, Path], None]


class SvgPolishDeltaError(ValueError):
    """Expected user-facing error for SVG polish delta generation."""


def _fixture_path(example_dir: Path, relative: str, label: str) -> Path:
    if Path(relative).is_absolute():
        raise SvgPolishDeltaError(f"{label} must be fixture-relative")
    root = example_dir.resolve()
    resolved = (example_dir / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SvgPolishDeltaError(f"{label} must stay inside the fixture") from exc
    return resolved


def _relative(example_dir: Path, path: Path) -> str:
    return str(path.resolve().relative_to(example_dir.resolve()))


def _load_fresh_recipe(
    recipe_path: Path,
    *,
    example_dir: Path,
    base_dir: Path,
) -> dict[str, Any]:
    try:
        recipe = load_svg_polish_recipe(recipe_path, example_dir=example_dir)
        if svg_polish_recipe_is_stale(recipe_path, example_dir=example_dir, base_dir=base_dir):
            raise SvgPolishDeltaError("SVG polish recipe is stale")
        return recipe
    except SvgPolishRecipeError as exc:
        raise SvgPolishDeltaError(str(exc)) from exc


def _default_renderer(source_svg: Path, output_png: Path) -> None:
    script = REPO_ROOT / "scripts" / "svg_to_png.sh"
    output_png.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["bash", str(script), str(source_svg), str(output_png)],
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise SvgPolishDeltaError(f"SVG render failed for {source_svg}: {detail}")


def _renderer_provenance(renderer: Renderer | None) -> dict[str, str]:
    script = REPO_ROOT / "scripts" / "svg_to_png.sh"
    executable = "scripts/svg_to_png.sh"
    if renderer is not None:
        executable = f"callable:{getattr(renderer, '__name__', renderer.__class__.__name__)}"
    return {
        "executable": executable,
        "version": "unknown",
        "script_hash": file_sha256(script),
    }


def _write_diff_image(before_png: Path, after_png: Path, diff_png: Path) -> None:
    with Image.open(before_png) as before_image, Image.open(after_png) as after_image:
        before = before_image.convert("RGBA")
        after = after_image.convert("RGBA")
        if before.size != after.size:
            raise SvgPolishDeltaError("before/after render dimensions differ")
        diff = ImageChops.difference(before, after)
        diff_png.parent.mkdir(parents=True, exist_ok=True)
        diff.save(diff_png)


def _manifest_payload(
    example_dir: Path,
    *,
    recipe: dict[str, Any],
    recipe_path: Path,
    source_svg_path: Path,
    polished_svg_path: Path,
    before_png: Path,
    after_png: Path,
    diff_png: Path,
    renderer: Renderer | None,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": recipe["fixture"],
        "source_svg": recipe["source_svg"],
        "polished_svg": recipe["target_svg"],
        "recipe": _relative(example_dir, recipe_path),
        "source_svg_hash": file_sha256(source_svg_path),
        "polished_svg_hash": file_sha256(polished_svg_path),
        "recipe_hash": file_sha256(recipe_path),
        "artifact_hashes": {
            "before_png_hash": file_sha256(before_png),
            "after_png_hash": file_sha256(after_png),
            "diff_png_hash": file_sha256(diff_png),
        },
        "renderer": _renderer_provenance(renderer),
        "operation_ids": [operation["id"] for operation in recipe["operations"]],
        "artifacts": {
            "before_png": _relative(example_dir, before_png),
            "after_png": _relative(example_dir, after_png),
            "diff_png": _relative(example_dir, diff_png),
        },
    }


def build_svg_polish_delta_pack(
    example_dir: Path,
    *,
    recipe_path: Path | None = None,
    renderer: Renderer | None = None,
    base_dir: Path = REPO_ROOT,
    force: bool = True,
) -> Path:
    """Render before/after polish images, write diff image, and return manifest path."""
    recipe_path = recipe_path or example_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    recipe = _load_fresh_recipe(recipe_path, example_dir=example_dir, base_dir=base_dir)
    source_svg_path = _fixture_path(example_dir, recipe["source_svg"], "recipe.source_svg")
    polished_svg_path = _fixture_path(example_dir, recipe["target_svg"], "recipe.target_svg")
    if not polished_svg_path.is_file():
        raise SvgPolishDeltaError(f"missing polished SVG: {polished_svg_path}")
    delta_dir = example_dir / SVG_POLISH_DELTA_DIR
    before_png = delta_dir / "before.png"
    after_png = delta_dir / "after.png"
    diff_png = delta_dir / "diff.png"
    manifest_path = example_dir / SVG_POLISH_DELTA_MANIFEST_RELATIVE_PATH
    if not force:
        existing = [
            path for path in (before_png, after_png, diff_png, manifest_path) if path.exists()
        ]
        if existing:
            joined = ", ".join(str(path) for path in existing)
            raise SvgPolishDeltaError(f"refusing to overwrite existing delta artifact(s): {joined}")
    renderer_provenance = renderer
    renderer = renderer or _default_renderer
    delta_dir.mkdir(parents=True, exist_ok=True)
    renderer(source_svg_path, before_png)
    renderer(polished_svg_path, after_png)
    _write_diff_image(before_png, after_png, diff_png)
    manifest = _manifest_payload(
        example_dir,
        recipe=recipe,
        recipe_path=recipe_path,
        source_svg_path=source_svg_path,
        polished_svg_path=polished_svg_path,
        before_png=before_png,
        after_png=after_png,
        diff_png=diff_png,
        renderer=renderer_provenance,
    )
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SvgPolishDeltaError(f"{label} must be a mapping")
    return value


def _require_non_empty_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SvgPolishDeltaError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def _require_sha256(value: str, label: str) -> None:
    if not value.startswith("sha256:") or len(value) != len("sha256:") + 64:
        raise SvgPolishDeltaError(f"{label} must be a sha256:<64 hex chars> string")
    suffix = value.removeprefix("sha256:")
    if any(char not in "0123456789abcdef" for char in suffix):
        raise SvgPolishDeltaError(f"{label} must be lowercase sha256 hex")


def load_svg_polish_delta_manifest(path: Path, *, example_dir: Path) -> dict[str, Any]:
    """Load and validate an SVG polish delta manifest JSON file."""
    canonical = (example_dir / SVG_POLISH_DELTA_MANIFEST_RELATIVE_PATH).resolve()
    if path.resolve() != canonical:
        raise SvgPolishDeltaError(
            f"SVG polish delta manifest path must be {SVG_POLISH_DELTA_MANIFEST_RELATIVE_PATH}"
        )
    if not path.is_file():
        raise SvgPolishDeltaError(f"missing SVG polish delta manifest: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise SvgPolishDeltaError(f"invalid UTF-8 in {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SvgPolishDeltaError(f"invalid JSON in {path}: {exc}") from exc
    data = _require_mapping(data, "delta_manifest")
    if data.get("schema") != SCHEMA:
        raise SvgPolishDeltaError(f"delta_manifest.schema must be {SCHEMA}")
    fixture = _require_non_empty_string(data, "fixture", label="delta_manifest")
    if fixture != example_dir.name:
        raise SvgPolishDeltaError("delta_manifest.fixture must match fixture directory")
    _fixture_path(
        example_dir,
        _require_non_empty_string(data, "source_svg", label="delta_manifest"),
        "source_svg",
    )
    _fixture_path(
        example_dir,
        _require_non_empty_string(data, "polished_svg", label="delta_manifest"),
        "polished_svg",
    )
    _fixture_path(
        example_dir,
        _require_non_empty_string(data, "recipe", label="delta_manifest"),
        "recipe",
    )
    artifacts = _require_mapping(data.get("artifacts"), "delta_manifest.artifacts")
    for key in ("before_png", "after_png", "diff_png"):
        path_value = _require_non_empty_string(artifacts, key, label="delta_manifest.artifacts")
        artifact_path = _fixture_path(example_dir, path_value, f"artifacts.{key}")
        if not artifact_path.is_file():
            raise SvgPolishDeltaError(f"missing delta artifact: {artifact_path}")
    artifact_hashes = _require_mapping(
        data.get("artifact_hashes"),
        "delta_manifest.artifact_hashes",
    )
    for key in ("before_png_hash", "after_png_hash", "diff_png_hash"):
        value = _require_non_empty_string(
            artifact_hashes,
            key,
            label="delta_manifest.artifact_hashes",
        )
        _require_sha256(value, f"delta_manifest.artifact_hashes.{key}")
    renderer = _require_mapping(data.get("renderer"), "delta_manifest.renderer")
    _require_non_empty_string(renderer, "executable", label="delta_manifest.renderer")
    _require_non_empty_string(renderer, "version", label="delta_manifest.renderer")
    script_hash = _require_non_empty_string(
        renderer,
        "script_hash",
        label="delta_manifest.renderer",
    )
    _require_sha256(script_hash, "delta_manifest.renderer.script_hash")
    operation_ids = data.get("operation_ids")
    if not isinstance(operation_ids, list) or not all(
        isinstance(item, str) and item.strip() for item in operation_ids
    ):
        raise SvgPolishDeltaError("delta_manifest.operation_ids must be a string list")
    for key in ("source_svg_hash", "polished_svg_hash", "recipe_hash"):
        value = _require_non_empty_string(data, key, label="delta_manifest")
        _require_sha256(value, f"delta_manifest.{key}")
    return data


def svg_polish_delta_is_stale(path: Path, *, example_dir: Path) -> bool:
    """Return True when the delta manifest hashes differ from current files."""
    data = load_svg_polish_delta_manifest(path, example_dir=example_dir)
    source_svg = _fixture_path(example_dir, data["source_svg"], "source_svg")
    polished_svg = _fixture_path(example_dir, data["polished_svg"], "polished_svg")
    recipe_path = _fixture_path(example_dir, data["recipe"], "recipe")
    artifacts = data["artifacts"]
    artifact_hashes = data["artifact_hashes"]
    before_png = _fixture_path(example_dir, artifacts["before_png"], "artifacts.before_png")
    after_png = _fixture_path(example_dir, artifacts["after_png"], "artifacts.after_png")
    diff_png = _fixture_path(example_dir, artifacts["diff_png"], "artifacts.diff_png")
    return (
        data["source_svg_hash"] != file_sha256(source_svg)
        or data["polished_svg_hash"] != file_sha256(polished_svg)
        or data["recipe_hash"] != file_sha256(recipe_path)
        or artifact_hashes["before_png_hash"] != file_sha256(before_png)
        or artifact_hashes["after_png_hash"] != file_sha256(after_png)
        or artifact_hashes["diff_png_hash"] != file_sha256(diff_png)
    )
