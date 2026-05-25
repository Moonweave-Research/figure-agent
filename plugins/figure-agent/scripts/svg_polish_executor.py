"""Apply bounded SVG polish recipes to fixture-local polished SVG files."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from svg_polish_recipe import (
    SVG_POLISH_RECIPE_RELATIVE_PATH,
    SvgPolishRecipeError,
    load_svg_polish_recipe,
    svg_polish_recipe_is_stale,
)

MAX_TRANSLATE_PX = 10.0
MAX_CLASS_SELECTOR_MATCHES = 5
MIN_STROKE_WIDTH_RATIO = 0.5
MAX_STROKE_WIDTH_RATIO = 2.0
OPACITY_ATTRIBUTES = {
    "set_opacity": "opacity",
    "set_fill_opacity": "fill-opacity",
    "set_stroke_opacity": "stroke-opacity",
}


class SvgPolishExecutorError(ValueError):
    """Expected user-facing error for unsafe SVG polish execution."""


def _fixture_name(example_dir: Path) -> str:
    name = example_dir.name
    if not name:
        raise SvgPolishExecutorError("example_dir must name one fixture")
    return name


def _fixture_path(example_dir: Path, relative: str, label: str) -> Path:
    if Path(relative).is_absolute():
        raise SvgPolishExecutorError(f"{label} must be fixture-relative")
    root = example_dir.resolve()
    resolved = (example_dir / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SvgPolishExecutorError(f"{label} must stay inside the fixture") from exc
    return resolved


def _format_number(value: float) -> str:
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return text or "0"


def _load_tree(source_path: Path) -> ET.ElementTree:
    try:
        return ET.parse(source_path)
    except ET.ParseError as exc:
        raise SvgPolishExecutorError(f"invalid SVG XML in {source_path}: {exc}") from exc


def _element_text(element: ET.Element) -> str:
    return "".join(element.itertext()).strip()


def _matches_selector(element: ET.Element, selector: dict[str, Any]) -> bool:
    kind = selector["kind"]
    value = selector["value"]
    if kind == "element_id":
        return element.attrib.get("id") == value
    if kind == "css_class":
        return value in element.attrib.get("class", "").split()
    if kind == "text_exact":
        return _element_text(element) == value
    raise SvgPolishExecutorError(f"unsupported selector kind: {kind}")


def _resolve_selector(
    root: ET.Element,
    selector: dict[str, Any],
    operation_id: str,
) -> list[ET.Element]:
    matches = [element for element in root.iter() if _matches_selector(element, selector)]
    if not matches:
        raise SvgPolishExecutorError(f"{operation_id} matched no SVG elements")
    kind = selector["kind"]
    if kind in {"element_id", "text_exact"} and len(matches) != 1:
        raise SvgPolishExecutorError(f"{operation_id} matched too many SVG elements")
    if kind == "css_class" and len(matches) > MAX_CLASS_SELECTOR_MATCHES:
        raise SvgPolishExecutorError(f"{operation_id} matched too many SVG elements")
    return matches


def _number(value: Any, label: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise SvgPolishExecutorError(f"{label} must be numeric")
    return float(value)


def _parse_current_float(element: ET.Element, attribute: str, operation_id: str) -> float:
    value = element.attrib.get(attribute)
    if value is None:
        raise SvgPolishExecutorError(f"{operation_id} target lacks {attribute}")
    try:
        return float(value)
    except ValueError as exc:
        raise SvgPolishExecutorError(f"{operation_id} target {attribute} is not numeric") from exc


def _validate_action_bounds(
    action: dict[str, Any],
    elements: Sequence[ET.Element],
    operation_id: str,
) -> None:
    action_type = action["type"]
    if action_type == "translate":
        dx = _number(action["dx"], f"{operation_id}.dx")
        dy = _number(action["dy"], f"{operation_id}.dy")
        if abs(dx) > MAX_TRANSLATE_PX or abs(dy) > MAX_TRANSLATE_PX:
            raise SvgPolishExecutorError(f"{operation_id} translate exceeds visual-only bounds")
        return
    if action_type in OPACITY_ATTRIBUTES:
        value = _number(action["value"], f"{operation_id}.value")
        if value < 0.0 or value > 1.0:
            raise SvgPolishExecutorError(f"{operation_id} opacity exceeds visual-only bounds")
        return
    if action_type == "set_stroke_width":
        value = _number(action["value"], f"{operation_id}.value")
        if value <= 0:
            raise SvgPolishExecutorError(f"{operation_id} stroke width exceeds visual-only bounds")
        for element in elements:
            current = _parse_current_float(element, "stroke-width", operation_id)
            if current <= 0:
                raise SvgPolishExecutorError(
                    f"{operation_id} current stroke width exceeds visual-only bounds"
                )
            ratio = value / current
            if ratio < MIN_STROKE_WIDTH_RATIO or ratio > MAX_STROKE_WIDTH_RATIO:
                raise SvgPolishExecutorError(
                    f"{operation_id} stroke width exceeds visual-only bounds"
                )
        return
    raise SvgPolishExecutorError(f"{operation_id} unsupported action type: {action_type}")


def _apply_action(action: dict[str, Any], elements: Sequence[ET.Element]) -> dict[str, str]:
    action_type = action["type"]
    if action_type == "translate":
        dx = _format_number(_number(action["dx"], "dx"))
        dy = _format_number(_number(action["dy"], "dy"))
        transform = f"translate({dx} {dy})"
        for element in elements:
            existing = element.attrib.get("transform", "").strip()
            element.set("transform", f"{existing} {transform}".strip())
        return {"attribute": "transform", "value": transform}
    if action_type == "set_stroke_width":
        value = _format_number(_number(action["value"], "value"))
        for element in elements:
            element.set("stroke-width", value)
        return {"attribute": "stroke-width", "value": value}
    if action_type in OPACITY_ATTRIBUTES:
        attribute = OPACITY_ATTRIBUTES[action_type]
        value = _format_number(_number(action["value"], "value"))
        for element in elements:
            element.set(attribute, value)
        return {"attribute": attribute, "value": value}
    raise SvgPolishExecutorError(f"unsupported action type: {action_type}")


def _load_recipe_for_execution(
    recipe_path: Path,
    *,
    example_dir: Path,
    base_dir: Path,
) -> dict[str, Any]:
    try:
        recipe = load_svg_polish_recipe(recipe_path, example_dir=example_dir)
        if svg_polish_recipe_is_stale(recipe_path, example_dir=example_dir, base_dir=base_dir):
            raise SvgPolishExecutorError("SVG polish recipe is stale")
        return recipe
    except SvgPolishRecipeError as exc:
        raise SvgPolishExecutorError(str(exc)) from exc


def _plan_from_tree(recipe: dict[str, Any], root: ET.Element) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for operation in recipe["operations"]:
        operation_id = operation["id"]
        elements = _resolve_selector(root, operation["selector"], operation_id)
        _validate_action_bounds(operation["action"], elements, operation_id)
        action_type = operation["action"]["type"]
        changes.append(
            {
                "operation_id": operation_id,
                "class": operation["class"],
                "action": action_type,
                "matched_count": len(elements),
                "selector": operation["selector"],
            }
        )
    return changes


def plan_svg_polish(
    recipe_path: Path,
    *,
    example_dir: Path,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Return a dry-run plan for an SVG polish recipe without writing files."""
    base_dir = base_dir or example_dir.parent.parent
    recipe = _load_recipe_for_execution(recipe_path, example_dir=example_dir, base_dir=base_dir)
    source_path = _fixture_path(example_dir, recipe["source_svg"], "recipe.source_svg")
    tree = _load_tree(source_path)
    changes = _plan_from_tree(recipe, tree.getroot())
    target_path = _fixture_path(example_dir, recipe["target_svg"], "recipe.target_svg")
    return {
        "schema": "figure-agent.svg-polish-plan.v1",
        "fixture": recipe["fixture"],
        "source_svg": recipe["source_svg"],
        "target_svg": recipe["target_svg"],
        "write_required": not target_path.is_file(),
        "changes": changes,
    }


def apply_svg_polish(
    recipe_path: Path,
    *,
    example_dir: Path,
    force: bool = False,
    base_dir: Path | None = None,
) -> Path:
    """Apply a validated SVG polish recipe and return the polished SVG path."""
    base_dir = base_dir or example_dir.parent.parent
    recipe = _load_recipe_for_execution(recipe_path, example_dir=example_dir, base_dir=base_dir)
    source_path = _fixture_path(example_dir, recipe["source_svg"], "recipe.source_svg")
    target_path = _fixture_path(example_dir, recipe["target_svg"], "recipe.target_svg")
    if target_path.exists() and not force:
        raise SvgPolishExecutorError(f"refusing to overwrite existing output: {target_path}")
    tree = _load_tree(source_path)
    root = tree.getroot()
    _plan_from_tree(recipe, root)
    for operation in recipe["operations"]:
        elements = _resolve_selector(root, operation["selector"], operation["id"])
        _apply_action(operation["action"], elements)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(target_path, encoding="unicode", xml_declaration=False)
    return target_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example_dir", type=Path)
    parser.add_argument(
        "--recipe",
        type=Path,
        default=None,
        help=f"Recipe path, default: {SVG_POLISH_RECIPE_RELATIVE_PATH}",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned polish operations without writing; this is the default.",
    )
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--base-dir", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    example_dir = args.example_dir
    recipe_path = args.recipe or example_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    base_dir = args.base_dir or example_dir.parent.parent
    try:
        if args.write:
            output_path = apply_svg_polish(
                recipe_path,
                example_dir=example_dir,
                force=args.force,
                base_dir=base_dir,
            )
            print(f"wrote {output_path.resolve().relative_to(example_dir.resolve())}")
            return 0
        plan = plan_svg_polish(recipe_path, example_dir=example_dir, base_dir=base_dir)
        print(f"dry-run: would write {plan['target_svg']}")
        for change in plan["changes"]:
            print(
                "dry-run: "
                f"{change['operation_id']} {change['class']} "
                f"{change['action']} matched={change['matched_count']}"
            )
        return 0
    except SvgPolishExecutorError as exc:
        print(f"svg_polish_executor.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
