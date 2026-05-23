"""Optional fixture aesthetic intent contract for /fig_critique."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

AESTHETIC_INTENT_SCHEMA = "figure-agent.aesthetic-intent.v1"
AESTHETIC_INTENT_SCHEMA_V2 = "figure-agent.aesthetic-intent.v2"
AESTHETIC_INTENT_SCHEMAS = frozenset({AESTHETIC_INTENT_SCHEMA, AESTHETIC_INTENT_SCHEMA_V2})
TARGET_JOURNALS = frozenset(
    {"Nature Communications", "Nature Materials", "Science", "ACS", "internal", "unknown"}
)
VISUAL_MATURITIES = frozenset({"restrained", "polished", "editorial", "cover_like"})
DENSITIES = frozenset({"sparse", "balanced", "dense"})
REFERENCE_STYLES = frozenset(
    {
        "mechanism_schematic",
        "apparatus_schematic",
        "multipanel_story",
        "data_plus_schematic",
        "graphical_abstract",
    }
)
SEVERITIES = frozenset({"BLOCKER", "MAJOR", "MINOR", "NIT"})
POLISH_PATHS = frozenset(
    {
        "continue_tikz",
        "ready_for_svg_polish",
        "needs_human_art_direction",
        "semantic_backport_required",
    }
)
AESTHETIC_LEVER_DIMENSIONS = frozenset(
    {
        "maturity",
        "hero_hierarchy",
        "whitespace_breathing",
        "typography_authority",
        "color_harmony",
        "line_weight_rhythm",
        "component_fidelity",
        "hand_craft",
        "cross_panel_grammar",
        "polish_route",
    }
)
AESTHETIC_LEVER_PRIORITIES = frozenset({"required", "recommended", "optional"})
AESTHETIC_LEVER_ROUTES = frozenset(
    {"tikz_patch", "svg_polish", "semantic_backport", "human_art_direction"}
)
MAX_AESTHETIC_LEVERS = 10


class AestheticIntentError(Exception):
    """Controlled error for malformed aesthetic_intent.yaml."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AestheticIntentError(f"{label} must be a mapping")
    return value


def _require_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AestheticIntentError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def _require_enum(
    data: dict[str, Any],
    key: str,
    allowed: frozenset[str],
    *,
    label: str,
) -> str:
    value = _require_string(data, key, label=label)
    if value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise AestheticIntentError(f"{label}.{key} must be one of: {allowed_values}")
    return value


def _mapping_items(data: dict[str, Any], key: str, *, label: str) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise AestheticIntentError(f"{label}.{key} must be a non-empty list")
    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(value):
        item_label = f"{label}.{key}[{index}]"
        item = _require_mapping(raw_item, item_label)
        item_id = _require_string(item, "id", label=item_label)
        if item_id in seen_ids:
            raise AestheticIntentError(f"{item_label}.id is duplicated: {item_id}")
        seen_ids.add(item_id)
        items.append(item)
    return items


def _string_items(data: dict[str, Any], key: str, *, label: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise AestheticIntentError(f"{label}.{key} must be a non-empty list")
    items: list[str] = []
    for index, raw_item in enumerate(value):
        if not isinstance(raw_item, str) or not raw_item.strip():
            raise AestheticIntentError(f"{label}.{key}[{index}] must be a non-empty string")
        items.append(raw_item.strip())
    return items


def _validate_aesthetic_levers(data: dict[str, Any]) -> None:
    levers = _mapping_items(data, "aesthetic_levers", label="aesthetic_intent")
    if len(levers) > MAX_AESTHETIC_LEVERS:
        raise AestheticIntentError(
            f"aesthetic_intent.aesthetic_levers must contain at most {MAX_AESTHETIC_LEVERS} items"
        )
    for index, item in enumerate(levers):
        label = f"aesthetic_intent.aesthetic_levers[{index}]"
        _require_enum(item, "dimension", AESTHETIC_LEVER_DIMENSIONS, label=label)
        _require_string(item, "intent", label=label)
        _require_enum(item, "priority", AESTHETIC_LEVER_PRIORITIES, label=label)
        _string_items(item, "positive_signals", label=label)
        _string_items(item, "anti_patterns", label=label)
        _string_items(item, "allowed_adjustments", label=label)
        _string_items(item, "forbidden_adjustments", label=label)
        _require_enum(item, "default_route", AESTHETIC_LEVER_ROUTES, label=label)


def load_aesthetic_intent(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise AestheticIntentError(f"malformed YAML in {path}: {exc}") from exc
    data = _require_mapping(raw, "aesthetic_intent")
    schema = _require_string(data, "schema", label="aesthetic_intent")
    if schema not in AESTHETIC_INTENT_SCHEMAS:
        allowed = ", ".join(sorted(AESTHETIC_INTENT_SCHEMAS))
        raise AestheticIntentError(f"aesthetic_intent.schema must be one of: {allowed}")
    _require_string(data, "fixture", label="aesthetic_intent")
    _require_enum(data, "target_journal", TARGET_JOURNALS, label="aesthetic_intent")
    _require_enum(data, "visual_maturity", VISUAL_MATURITIES, label="aesthetic_intent")
    _require_enum(data, "density", DENSITIES, label="aesthetic_intent")
    _require_enum(data, "reference_style", REFERENCE_STYLES, label="aesthetic_intent")

    for index, item in enumerate(
        _mapping_items(data, "design_principles", label="aesthetic_intent")
    ):
        _require_string(item, "instruction", label=f"aesthetic_intent.design_principles[{index}]")

    for index, item in enumerate(_mapping_items(data, "must_avoid", label="aesthetic_intent")):
        label = f"aesthetic_intent.must_avoid[{index}]"
        _require_string(item, "pattern", label=label)
        _require_enum(item, "severity", SEVERITIES, label=label)

    for index, item in enumerate(
        _mapping_items(data, "polish_triggers", label="aesthetic_intent")
    ):
        label = f"aesthetic_intent.polish_triggers[{index}]"
        _require_string(item, "condition", label=label)
        _require_enum(item, "recommended_path", POLISH_PATHS, label=label)
    if schema == AESTHETIC_INTENT_SCHEMA_V2:
        _validate_aesthetic_levers(data)
    return data


def load_optional_aesthetic_intent(example_dir: Path) -> dict[str, Any] | None:
    path = example_dir / "aesthetic_intent.yaml"
    if not path.is_file():
        return None
    pack = load_aesthetic_intent(path)
    fixture = pack.get("fixture")
    if fixture != example_dir.name:
        raise AestheticIntentError(
            "aesthetic_intent.fixture must match example directory name: "
            f"{example_dir.name}"
        )
    return pack
