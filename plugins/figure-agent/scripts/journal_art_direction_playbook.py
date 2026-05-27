"""Optional journal art-direction playbook contract for /fig_critique."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from aesthetic_intent import SEVERITIES, TARGET_JOURNALS, VISUAL_MATURITIES

JOURNAL_ART_DIRECTION_PLAYBOOK_SCHEMA = "figure-agent.journal-art-direction-playbook.v1"
JOURNAL_PLAYBOOK_DIRNAME = "_journal_art_direction_playbooks"

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_VENUE_CONTEXTS = frozenset(
    {"main_text", "extended_data", "supplementary", "graphical_abstract", "cover_like"}
)
_DIMENSIONS = frozenset(
    {
        "maturity",
        "hierarchy",
        "whitespace",
        "typography",
        "color",
        "line_weight",
        "component_detail",
        "hand_craft",
        "cross_panel_consistency",
        "polish_route",
    }
)
_PRIORITIES = frozenset({"required", "recommended", "optional"})
_POLISH_PATHS = frozenset(
    {
        "continue_tikz",
        "ready_for_svg_polish",
        "semantic_backport_required",
        "needs_human_art_direction",
    }
)
_MAX_DESIGN_CENTER_ITEMS = 10
_MIN_DESIGN_CENTER_ITEMS = 3
_MAX_ANTI_PATTERNS = 10
_MIN_ANTI_PATTERNS = 2
_MAX_POSITIVE_SIGNALS = 10
_MIN_POSITIVE_SIGNALS = 2
_MAX_ROUTE_RULES = 8
_MIN_ROUTE_RULES = 2
_MAX_HUMAN_REVIEW_TRIGGERS = 6
_MIN_HUMAN_REVIEW_TRIGGERS = 1


class JournalArtDirectionPlaybookError(Exception):
    """Controlled error for malformed journal art-direction playbook packs."""


def is_safe_journal_playbook_id(value: str) -> bool:
    return bool(_SAFE_ID_RE.fullmatch(value))


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise JournalArtDirectionPlaybookError(f"{label} must be a mapping")
    return value


def _require_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise JournalArtDirectionPlaybookError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def _require_safe_id(data: dict[str, Any], key: str, *, label: str) -> str:
    value = _require_string(data, key, label=label)
    if not is_safe_journal_playbook_id(value):
        raise JournalArtDirectionPlaybookError(
            f"{label}.{key} must be a safe id: start with an ASCII letter or number, "
            "then use only ASCII letters, numbers, _, ., and -"
        )
    return value


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
        raise JournalArtDirectionPlaybookError(
            f"{label}.{key} must be one of: {allowed_values}"
        )
    return value


def _string_items(data: dict[str, Any], key: str, *, label: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise JournalArtDirectionPlaybookError(f"{label}.{key} must be a non-empty list")
    result: list[str] = []
    for index, raw_item in enumerate(value):
        if not isinstance(raw_item, str) or not raw_item.strip():
            raise JournalArtDirectionPlaybookError(
                f"{label}.{key}[{index}] must be a non-empty string"
            )
        result.append(raw_item.strip())
    return result


def _mapping_items(
    data: dict[str, Any],
    key: str,
    *,
    label: str,
    min_items: int,
    max_items: int,
) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list):
        raise JournalArtDirectionPlaybookError(f"{label}.{key} must be a list")
    if not min_items <= len(value) <= max_items:
        raise JournalArtDirectionPlaybookError(
            f"{label}.{key} must contain between {min_items} and {max_items} items"
        )
    result: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(value):
        item_label = f"{label}.{key}[{index}]"
        item = _require_mapping(raw_item, item_label)
        item_id = _require_safe_id(item, "id", label=item_label)
        if item_id in seen_ids:
            raise JournalArtDirectionPlaybookError(f"{item_label}.id is duplicated: {item_id}")
        seen_ids.add(item_id)
        result.append(item)
    return result


def journal_playbook_id_from_spec(spec: dict[str, Any]) -> str | None:
    raw_id = spec.get("journal_art_direction_playbook")
    if raw_id is None:
        return None
    if not isinstance(raw_id, str) or not raw_id.strip():
        raise JournalArtDirectionPlaybookError(
            "spec.journal_art_direction_playbook must be a non-empty string"
        )
    playbook_id = raw_id.strip()
    if not is_safe_journal_playbook_id(playbook_id):
        raise JournalArtDirectionPlaybookError(
            "spec.journal_art_direction_playbook must be a safe id: start with an ASCII "
            "letter or number, then use only ASCII letters, numbers, _, ., and -"
        )
    return playbook_id


def journal_playbook_path_for_id(example_dir: Path, playbook_id: str) -> Path:
    if not is_safe_journal_playbook_id(playbook_id):
        raise JournalArtDirectionPlaybookError(
            "journal_art_direction_playbook id must be a safe id: start with an ASCII "
            "letter or number, then use only ASCII letters, numbers, _, ., and -"
        )
    return example_dir.parent / JOURNAL_PLAYBOOK_DIRNAME / f"{playbook_id}.yaml"


def declared_journal_playbook_path(example_dir: Path, spec: dict[str, Any]) -> Path | None:
    playbook_id = journal_playbook_id_from_spec(spec)
    if playbook_id is None:
        return None
    return journal_playbook_path_for_id(example_dir, playbook_id)


def _validate_design_center(data: dict[str, Any]) -> None:
    for index, item in enumerate(
        _mapping_items(
            data,
            "design_center",
            label="journal_art_direction_playbook",
            min_items=_MIN_DESIGN_CENTER_ITEMS,
            max_items=_MAX_DESIGN_CENTER_ITEMS,
        )
    ):
        label = f"journal_art_direction_playbook.design_center[{index}]"
        _require_enum(item, "dimension", _DIMENSIONS, label=label)
        _require_string(item, "instruction", label=label)
        _require_enum(item, "priority", _PRIORITIES, label=label)
        _string_items(item, "positive_signals", label=label)
        _string_items(item, "anti_patterns", label=label)
        _string_items(item, "evidence_prompts", label=label)


def _validate_anti_patterns(data: dict[str, Any]) -> None:
    for index, item in enumerate(
        _mapping_items(
            data,
            "anti_patterns",
            label="journal_art_direction_playbook",
            min_items=_MIN_ANTI_PATTERNS,
            max_items=_MAX_ANTI_PATTERNS,
        )
    ):
        label = f"journal_art_direction_playbook.anti_patterns[{index}]"
        _require_enum(item, "dimension", _DIMENSIONS, label=label)
        _require_enum(item, "severity", SEVERITIES, label=label)
        _require_string(item, "pattern", label=label)
        _require_enum(item, "preferred_route", _POLISH_PATHS, label=label)


def _validate_positive_signals(data: dict[str, Any]) -> None:
    for index, item in enumerate(
        _mapping_items(
            data,
            "positive_signals",
            label="journal_art_direction_playbook",
            min_items=_MIN_POSITIVE_SIGNALS,
            max_items=_MAX_POSITIVE_SIGNALS,
        )
    ):
        label = f"journal_art_direction_playbook.positive_signals[{index}]"
        _require_enum(item, "dimension", _DIMENSIONS, label=label)
        _require_string(item, "signal", label=label)
        _require_string(item, "evidence_prompt", label=label)


def _validate_route_rules(data: dict[str, Any]) -> None:
    paths: set[str] = set()
    for index, item in enumerate(
        _mapping_items(
            data,
            "polish_route_rules",
            label="journal_art_direction_playbook",
            min_items=_MIN_ROUTE_RULES,
            max_items=_MAX_ROUTE_RULES,
        )
    ):
        label = f"journal_art_direction_playbook.polish_route_rules[{index}]"
        _require_string(item, "condition", label=label)
        recommended_path = _require_enum(item, "recommended_path", _POLISH_PATHS, label=label)
        paths.add(recommended_path)
        _string_items(item, "forbidden_actions", label=label)
    for required_path in ("continue_tikz", "ready_for_svg_polish"):
        if required_path not in paths:
            raise JournalArtDirectionPlaybookError(
                "journal_art_direction_playbook.polish_route_rules must include "
                f"{required_path}"
            )


def _validate_human_review_triggers(data: dict[str, Any]) -> None:
    for index, item in enumerate(
        _mapping_items(
            data,
            "human_review_triggers",
            label="journal_art_direction_playbook",
            min_items=_MIN_HUMAN_REVIEW_TRIGGERS,
            max_items=_MAX_HUMAN_REVIEW_TRIGGERS,
        )
    ):
        label = f"journal_art_direction_playbook.human_review_triggers[{index}]"
        _require_string(item, "condition", label=label)
        _require_enum(item, "severity", SEVERITIES, label=label)


def load_journal_art_direction_playbook(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise JournalArtDirectionPlaybookError(f"malformed YAML in {path}: {exc}") from exc
    data = _require_mapping(raw, "journal_art_direction_playbook")
    schema = _require_string(data, "schema", label="journal_art_direction_playbook")
    if schema != JOURNAL_ART_DIRECTION_PLAYBOOK_SCHEMA:
        raise JournalArtDirectionPlaybookError(
            "journal_art_direction_playbook.schema must equal "
            f"{JOURNAL_ART_DIRECTION_PLAYBOOK_SCHEMA}"
        )
    playbook_id = _require_safe_id(data, "playbook_id", label="journal_art_direction_playbook")
    if playbook_id != path.stem:
        raise JournalArtDirectionPlaybookError(
            "journal_art_direction_playbook.playbook_id must match filename stem"
        )
    _require_enum(data, "target_journal", TARGET_JOURNALS, label="journal_art_direction_playbook")
    _require_enum(data, "venue_context", _VENUE_CONTEXTS, label="journal_art_direction_playbook")
    _require_enum(
        data,
        "visual_maturity",
        VISUAL_MATURITIES,
        label="journal_art_direction_playbook",
    )
    _validate_design_center(data)
    _validate_anti_patterns(data)
    _validate_positive_signals(data)
    _validate_route_rules(data)
    _validate_human_review_triggers(data)
    return data


def load_optional_journal_art_direction_playbook(
    example_dir: Path,
    spec: dict[str, Any],
) -> dict[str, Any] | None:
    path = declared_journal_playbook_path(example_dir, spec)
    if path is None:
        return None
    if not path.is_file():
        raise JournalArtDirectionPlaybookError(f"missing journal_art_direction_playbook: {path}")
    return load_journal_art_direction_playbook(path)


def journal_playbook_anchors(pack: dict[str, Any]) -> set[str]:
    anchors = {
        str(pack.get("playbook_id") or ""),
        str(pack.get("target_journal") or ""),
        str(pack.get("venue_context") or ""),
        str(pack.get("visual_maturity") or ""),
    }
    for key in (
        "design_center",
        "anti_patterns",
        "positive_signals",
        "polish_route_rules",
        "human_review_triggers",
    ):
        for item in pack.get(key, []):
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                anchors.add(item["id"])
    return {anchor for anchor in anchors if anchor}
