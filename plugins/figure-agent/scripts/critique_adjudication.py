"""Parse and validate critique adjudication decisions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from quality_manifest import file_sha256

SCHEMA = "figure-agent.critique-adjudication.v1"
ALLOWED_DECISIONS = frozenset({"apply", "dismiss", "defer", "needs_human", "resolved"})
_PATCH_EVIDENCE_REQUIRED = frozenset({"apply", "resolved"})


class CritiqueAdjudicationError(ValueError):
    """Expected user-facing error for malformed critique adjudication files."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CritiqueAdjudicationError(f"{label} must be a mapping")
    return value


def _require_non_empty_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CritiqueAdjudicationError(f"{label}.{key} must be a non-empty string")
    return value


def _validate_hash(value: str) -> None:
    if not value.startswith("sha256:") or len(value) <= len("sha256:"):
        raise CritiqueAdjudicationError(
            "adjudication.source_critique_hash must be a sha256-prefixed string"
        )


def validate_adjudication(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a critique adjudication mapping and return it unchanged."""
    data = _require_mapping(data, "adjudication")
    schema = data.get("schema")
    if schema != SCHEMA:
        raise CritiqueAdjudicationError(f"adjudication.schema must be {SCHEMA}")

    _require_non_empty_string(data, "fixture", label="adjudication")
    source_hash = _require_non_empty_string(data, "source_critique_hash", label="adjudication")
    _validate_hash(source_hash)

    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        raise CritiqueAdjudicationError("adjudication.decisions must be a list")

    for index, raw_decision in enumerate(decisions):
        decision_label = f"adjudication.decisions[{index}]"
        decision_item = _require_mapping(raw_decision, decision_label)
        _require_non_empty_string(decision_item, "finding_id", label=decision_label)
        decision_value = _require_non_empty_string(decision_item, "decision", label=decision_label)
        if decision_value not in ALLOWED_DECISIONS:
            allowed = ", ".join(sorted(ALLOWED_DECISIONS))
            raise CritiqueAdjudicationError(
                f"{decision_label}.decision must be one of: {allowed}"
            )
        _require_non_empty_string(decision_item, "reason", label=decision_label)
        if decision_value in _PATCH_EVIDENCE_REQUIRED:
            _require_non_empty_string(decision_item, "patch_target", label=decision_label)
            _require_non_empty_string(decision_item, "evidence", label=decision_label)

    return data


def load_adjudication(path: Path) -> dict[str, Any]:
    """Load and validate a critique adjudication YAML file."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CritiqueAdjudicationError(f"invalid YAML in {path}: {exc}") from exc
    return validate_adjudication(data)


def write_adjudication(path: Path, data: dict[str, Any]) -> None:
    """Validate and write a critique adjudication YAML file."""
    validated = validate_adjudication(data)
    path.write_text(
        yaml.safe_dump(validated, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def adjudication_is_stale(adjudication_path: Path, critique_path: Path) -> bool:
    """Return true when adjudication was made against different critique content."""
    adjudication = load_adjudication(adjudication_path)
    if not critique_path.is_file():
        raise CritiqueAdjudicationError(f"missing critique: {critique_path}")
    return adjudication["source_critique_hash"] != file_sha256(critique_path)
