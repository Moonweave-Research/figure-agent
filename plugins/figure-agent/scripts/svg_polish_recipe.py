"""Parse and validate SVG polish recipe files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
from quality_manifest import REPO_ROOT, input_manifest_hash
from svg_polish_manifest import ALLOWED_EDIT_CLASSES

SCHEMA = "figure-agent.svg-polish-recipe.v1"
SVG_POLISH_RECIPE_RELATIVE_PATH = "polish/svg_polish_recipe.yaml"
SELECTOR_KINDS = frozenset({"element_id", "css_class", "text_exact"})
ACTION_TYPES = frozenset(
    {
        "translate",
        "set_stroke_width",
        "set_opacity",
        "set_fill_opacity",
        "set_stroke_opacity",
    }
)


class SvgPolishRecipeError(ValueError):
    """Expected user-facing error for malformed SVG polish recipe files."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SvgPolishRecipeError(f"{label} must be a mapping")
    return value


def _require_non_empty_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SvgPolishRecipeError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def _require_bool(data: dict[str, Any], key: str, *, label: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise SvgPolishRecipeError(f"{label}.{key} must be a boolean")
    return value


def _require_sha256(value: str, label: str) -> None:
    if not value.startswith("sha256:") or len(value) != len("sha256:") + 64:
        raise SvgPolishRecipeError(f"{label} must be a sha256:<64 hex chars> string")
    suffix = value.removeprefix("sha256:")
    if any(char not in "0123456789abcdef" for char in suffix):
        raise SvgPolishRecipeError(f"{label} must be lowercase sha256 hex")


def _resolve_fixture_path(example_dir: Path, relative: str, label: str) -> Path:
    if Path(relative).is_absolute():
        raise SvgPolishRecipeError(f"{label} must be fixture-relative")
    root = example_dir.resolve()
    resolved = (example_dir / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SvgPolishRecipeError(f"{label} must stay inside the fixture") from exc
    return resolved


def _validate_source_svg_path(example_dir: Path, value: str) -> Path:
    resolved = _resolve_fixture_path(example_dir, value, "recipe.source_svg")
    relative = resolved.relative_to(example_dir.resolve())
    if not relative.parts or relative.parts[0] != "exports":
        raise SvgPolishRecipeError("recipe.source_svg must live under exports/")
    if resolved.suffix.lower() != ".svg":
        raise SvgPolishRecipeError("recipe.source_svg must point to an SVG file")
    if not resolved.is_file():
        raise SvgPolishRecipeError(f"missing recipe.source_svg: {resolved}")
    return resolved


def _validate_target_svg_path(example_dir: Path, value: str) -> Path:
    resolved = _resolve_fixture_path(example_dir, value, "recipe.target_svg")
    relative = resolved.relative_to(example_dir.resolve())
    if not relative.parts or relative.parts[0] != "polish":
        raise SvgPolishRecipeError("recipe.target_svg must live under polish/")
    if resolved.suffix.lower() != ".svg":
        raise SvgPolishRecipeError("recipe.target_svg must point to an SVG file")
    if "exports" in relative.parts or "build" in relative.parts:
        raise SvgPolishRecipeError("recipe.target_svg must not point to build/exports")
    return resolved


def _validate_selector(selector: Any, label: str) -> None:
    selector = _require_mapping(selector, label)
    kind = _require_non_empty_string(selector, "kind", label=label)
    if kind not in SELECTOR_KINDS:
        allowed = ", ".join(sorted(SELECTOR_KINDS))
        raise SvgPolishRecipeError(f"{label}.kind must be one of: {allowed}")
    _require_non_empty_string(selector, "value", label=label)


def _validate_action(action: Any, label: str) -> None:
    action = _require_mapping(action, label)
    action_type = _require_non_empty_string(action, "type", label=label)
    if action_type not in ACTION_TYPES:
        allowed = ", ".join(sorted(ACTION_TYPES))
        raise SvgPolishRecipeError(f"{label}.type must be one of: {allowed}")
    if action_type == "translate":
        _require_number(action, "dx", label=label)
        _require_number(action, "dy", label=label)
        unit = _require_non_empty_string(action, "unit", label=label)
        if unit != "px":
            raise SvgPolishRecipeError(f"{label}.unit must be px")
    else:
        _require_number(action, "value", label=label)


def _require_number(data: dict[str, Any], key: str, *, label: str) -> float:
    value = data.get(key)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise SvgPolishRecipeError(f"{label}.{key} must be a number")
    return float(value)


def _validate_operation(operation: Any, *, seen_ids: set[str], index: int) -> None:
    label = f"recipe.operations[{index}]"
    operation = _require_mapping(operation, label)
    operation_id = _require_non_empty_string(operation, "id", label=label)
    if operation_id in seen_ids:
        raise SvgPolishRecipeError(f"duplicate operation id: {operation_id}")
    seen_ids.add(operation_id)
    edit_class = _require_non_empty_string(operation, "class", label=label)
    if edit_class not in ALLOWED_EDIT_CLASSES:
        allowed = ", ".join(sorted(ALLOWED_EDIT_CLASSES))
        raise SvgPolishRecipeError(f"{label}.class must be one of: {allowed}")
    _validate_selector(operation.get("selector"), f"{label}.selector")
    _validate_action(operation.get("action"), f"{label}.action")
    _require_non_empty_string(operation, "rationale", label=label)
    semantic_guard = _require_mapping(operation.get("semantic_guard"), f"{label}.semantic_guard")
    allowed = _require_bool(
        semantic_guard,
        "allowed",
        label=f"{label}.semantic_guard",
    )
    if not allowed:
        raise SvgPolishRecipeError(f"{label}.semantic_guard.allowed must be true")
    _require_non_empty_string(semantic_guard, "reason", label=f"{label}.semantic_guard")


def validate_svg_polish_recipe(
    data: dict[str, Any],
    *,
    example_dir: Path,
) -> dict[str, Any]:
    """Validate an SVG polish recipe mapping and return it unchanged."""
    data = _require_mapping(data, "recipe")
    if data.get("schema") != SCHEMA:
        raise SvgPolishRecipeError(f"recipe.schema must be {SCHEMA}")
    fixture = _require_non_empty_string(data, "fixture", label="recipe")
    if fixture != example_dir.name:
        raise SvgPolishRecipeError("recipe.fixture must match the fixture directory name")
    _validate_source_svg_path(
        example_dir,
        _require_non_empty_string(data, "source_svg", label="recipe"),
    )
    _validate_target_svg_path(
        example_dir,
        _require_non_empty_string(data, "target_svg", label="recipe"),
    )
    recipe_hash = _require_non_empty_string(data, "recipe_input_hash", label="recipe")
    _require_sha256(recipe_hash, "recipe.recipe_input_hash")
    operations = data.get("operations")
    if not isinstance(operations, list) or not operations:
        raise SvgPolishRecipeError("recipe.operations must be a non-empty list")
    seen_ids: set[str] = set()
    for index, operation in enumerate(operations):
        _validate_operation(operation, seen_ids=seen_ids, index=index)
    return data


def _canonical_recipe_path(example_dir: Path) -> Path:
    return (example_dir / SVG_POLISH_RECIPE_RELATIVE_PATH).resolve()


def load_svg_polish_recipe(path: Path, *, example_dir: Path) -> dict[str, Any]:
    """Load and validate a fixture SVG polish recipe YAML file."""
    if path.resolve() != _canonical_recipe_path(example_dir):
        raise SvgPolishRecipeError(
            f"SVG polish recipe path must be {SVG_POLISH_RECIPE_RELATIVE_PATH}"
        )
    if not path.is_file():
        raise SvgPolishRecipeError(f"missing SVG polish recipe: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise SvgPolishRecipeError(f"invalid UTF-8 in {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise SvgPolishRecipeError(f"invalid YAML in {path}: {exc}") from exc
    return validate_svg_polish_recipe(data, example_dir=example_dir)


def write_svg_polish_recipe(path: Path, data: dict[str, Any]) -> None:
    """Validate and write an SVG polish recipe YAML file."""
    example_dir = path.parent.parent
    if path.resolve() != _canonical_recipe_path(example_dir):
        raise SvgPolishRecipeError(
            f"SVG polish recipe path must be {SVG_POLISH_RECIPE_RELATIVE_PATH}"
        )
    validated = validate_svg_polish_recipe(data, example_dir=example_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(validated, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def svg_polish_recipe_source_paths(
    example_dir: Path,
    name: str,
    *,
    source_svg: str | None = None,
) -> tuple[Path, ...]:
    """Return files whose content affects recipe freshness."""
    source_relative = source_svg or f"exports/{name}.svg"
    source_path = _validate_source_svg_path(example_dir, source_relative)
    candidates = [
        source_path,
        example_dir / "aesthetic_intent.yaml",
        example_dir / "critique.md",
    ]
    return tuple(path for path in candidates if path.is_file())


def svg_polish_recipe_input_hash(
    example_dir: Path,
    name: str,
    *,
    source_svg: str | None = None,
    base_dir: Path = REPO_ROOT,
) -> str:
    """Compute a hash for the recipe's freshness-sensitive inputs."""
    return input_manifest_hash(
        svg_polish_recipe_source_paths(example_dir, name, source_svg=source_svg),
        base_dir=base_dir,
    )


def svg_polish_recipe_is_stale(
    path: Path,
    *,
    example_dir: Path,
    base_dir: Path = REPO_ROOT,
) -> bool:
    """Return True when recipe_input_hash differs from current inputs."""
    data = load_svg_polish_recipe(path, example_dir=example_dir)
    expected = svg_polish_recipe_input_hash(
        example_dir,
        data["fixture"],
        source_svg=data["source_svg"],
        base_dir=base_dir,
    )
    return data["recipe_input_hash"] != expected


def svg_polish_recipe_template(
    example_dir: Path,
    *,
    base_dir: Path = REPO_ROOT,
) -> str:
    """Return a fixture-specific starter SVG polish recipe."""
    name = example_dir.name
    source_svg = f"exports/{name}.svg"
    _validate_source_svg_path(example_dir, source_svg)
    recipe_hash = svg_polish_recipe_input_hash(
        example_dir,
        name,
        source_svg=source_svg,
        base_dir=base_dir,
    )
    data = {
        "schema": SCHEMA,
        "fixture": name,
        "source_svg": source_svg,
        "target_svg": f"polish/{name}.polished.svg",
        "recipe_input_hash": recipe_hash,
        "operations": [
            {
                "id": "R001_label_micro_position",
                "class": "label_micro_position",
                "selector": {"kind": "element_id", "value": "replace_with_label_id"},
                "action": {"type": "translate", "dx": 0.0, "dy": -1.0, "unit": "px"},
                "rationale": (
                    "Template starter: replace selector with one real label ID for "
                    "a sub-10px optical alignment adjustment."
                ),
                "semantic_guard": {
                    "allowed": True,
                    "reason": "same label, target, and meaning; visual-only micro-position.",
                },
            },
            {
                "id": "R002_stroke_polish",
                "class": "stroke_polish",
                "selector": {"kind": "element_id", "value": "replace_with_line_id"},
                "action": {"type": "set_stroke_width", "value": 1.0},
                "rationale": (
                    "Template starter: replace selector with one decorative or outline "
                    "stroke whose width needs subtle optical normalization."
                ),
                "semantic_guard": {
                    "allowed": True,
                    "reason": "stroke polish only; no geometry, topology, or claim change.",
                },
            },
            {
                "id": "R003_typography_cleanup",
                "class": "typography_cleanup",
                "selector": {"kind": "text_exact", "value": "replace_with_exact_text"},
                "action": {"type": "set_opacity", "value": 0.95},
                "rationale": (
                    "Template starter: replace selector with one exact text node for "
                    "minor optical tone cleanup."
                ),
                "semantic_guard": {
                    "allowed": True,
                    "reason": (
                        "typography tone cleanup only; text content and label "
                        "target unchanged."
                    ),
                },
            },
        ],
    }
    validate_svg_polish_recipe(data, example_dir=example_dir)
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate or template figure-agent SVG polish recipes."
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        help=f"{SVG_POLISH_RECIPE_RELATIVE_PATH} path to validate",
    )
    parser.add_argument(
        "--template",
        type=Path,
        help="print a starter recipe for an example directory",
    )
    parser.add_argument(
        "--write-template",
        action="store_true",
        help=f"write the starter recipe to {SVG_POLISH_RECIPE_RELATIVE_PATH}",
    )
    parser.add_argument("--force", action="store_true", help="overwrite an existing template")
    parser.add_argument("--base-dir", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    try:
        if args.template is not None:
            template = svg_polish_recipe_template(args.template, base_dir=args.base_dir)
            if args.write_template:
                output_path = args.template / SVG_POLISH_RECIPE_RELATIVE_PATH
                if output_path.exists() and not args.force:
                    raise SvgPolishRecipeError(
                        f"refusing to overwrite existing recipe: {output_path}"
                    )
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(template, encoding="utf-8")
                print(f"wrote {SVG_POLISH_RECIPE_RELATIVE_PATH}")
                return 0
            print(template, end="")
            return 0
        if args.write_template:
            parser.error("--write-template requires --template EXAMPLE_DIR")
        if args.path is None:
            parser.error("provide a recipe path or --template EXAMPLE_DIR")
        example_dir = args.path.parent.parent
        load_svg_polish_recipe(args.path, example_dir=example_dir)
    except SvgPolishRecipeError as exc:
        print(f"svg_polish_recipe.py: {exc}", file=sys.stderr)
        return 1
    print(f"OK: SVG polish recipe valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
