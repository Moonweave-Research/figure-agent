"""Optional reference-calibration pack for /fig_critique."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REFERENCE_PACK_SCHEMA = "figure-agent.critique-reference-pack.v1"
TARGET_JOURNALS = frozenset(
    {"Nature Communications", "Nature Materials", "Science", "ACS", "internal", "unknown"}
)
REFERENCE_CLASSES = frozenset(
    {
        "mechanism_schematic",
        "apparatus_schematic",
        "multipanel_story",
        "data_plus_schematic",
        "graphical_abstract",
    }
)
VISUAL_AMBITIONS = frozenset(
    {"draft", "solid_manuscript", "high_impact_candidate", "cover_style"}
)
REFERENCE_SOURCES = frozenset({"provided_reference", "paper", "briefing", "human_note"})
REFERENCE_ROLES = frozenset(
    {"layout", "style", "component_fidelity", "storyline", "journal_register"}
)
SEVERITIES = frozenset({"BLOCKER", "MAJOR", "MINOR", "NIT"})


class CritiqueReferencePackError(Exception):
    """Controlled error for malformed critique_reference_pack.yaml."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CritiqueReferencePackError(f"{label} must be a mapping")
    return value


def _require_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CritiqueReferencePackError(f"{label}.{key} must be a non-empty string")
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
        raise CritiqueReferencePackError(f"{label}.{key} must be one of: {allowed_values}")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise CritiqueReferencePackError(f"{label} must be a list")
    return value


def _mapping_items(data: dict[str, Any], key: str, *, label: str) -> list[dict[str, Any]]:
    items = _require_list(data.get(key), f"{label}.{key}")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        result.append(_require_mapping(item, f"{label}.{key}[{index}]"))
    return result


def load_reference_pack(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CritiqueReferencePackError(f"malformed YAML in {path}: {exc}") from exc
    data = _require_mapping(raw, "critique_reference_pack")
    schema = _require_string(data, "schema", label="critique_reference_pack")
    if schema != REFERENCE_PACK_SCHEMA:
        raise CritiqueReferencePackError(
            f"critique_reference_pack.schema must be {REFERENCE_PACK_SCHEMA}"
        )
    _require_string(data, "fixture", label="critique_reference_pack")
    _require_enum(data, "target_journal", TARGET_JOURNALS, label="critique_reference_pack")
    _require_enum(
        data,
        "reference_class",
        REFERENCE_CLASSES,
        label="critique_reference_pack",
    )
    _require_enum(data, "visual_ambition", VISUAL_AMBITIONS, label="critique_reference_pack")

    reference_ids: set[str] = set()
    for index, item in enumerate(
        _mapping_items(data, "comparison_references", label="critique_reference_pack")
    ):
        label = f"critique_reference_pack.comparison_references[{index}]"
        reference_id = _require_string(item, "id", label=label)
        if reference_id in reference_ids:
            raise CritiqueReferencePackError(f"{label}.id is duplicated: {reference_id}")
        reference_ids.add(reference_id)
        _require_enum(item, "source", REFERENCE_SOURCES, label=label)
        _require_string(item, "path_or_citation", label=label)
        _require_enum(item, "role", REFERENCE_ROLES, label=label)

    for index, item in enumerate(
        _mapping_items(data, "must_match_traits", label="critique_reference_pack")
    ):
        label = f"critique_reference_pack.must_match_traits[{index}]"
        _require_string(item, "id", label=label)
        _require_string(item, "trait", label=label)
        reference_id = _require_string(item, "reference_id", label=label)
        if reference_id not in reference_ids:
            raise CritiqueReferencePackError(f"{label}.reference_id is unknown: {reference_id}")

    for index, item in enumerate(
        _mapping_items(data, "must_avoid_traits", label="critique_reference_pack")
    ):
        label = f"critique_reference_pack.must_avoid_traits[{index}]"
        _require_string(item, "id", label=label)
        _require_string(item, "trait", label=label)
        _require_enum(item, "severity", SEVERITIES, label=label)

    for index, item in enumerate(
        _mapping_items(data, "calibration_questions", label="critique_reference_pack")
    ):
        label = f"critique_reference_pack.calibration_questions[{index}]"
        _require_string(item, "id", label=label)
        _require_string(item, "question", label=label)
    return data


def load_optional_reference_pack(example_dir: Path) -> dict[str, Any] | None:
    path = example_dir / "critique_reference_pack.yaml"
    if not path.is_file():
        return None
    return load_reference_pack(path)
