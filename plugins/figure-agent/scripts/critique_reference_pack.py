"""Optional reference-calibration pack for /fig_critique."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

REFERENCE_PACK_SCHEMA_V1 = "figure-agent.critique-reference-pack.v1"
REFERENCE_PACK_SCHEMA = "figure-agent.critique-reference-pack.v1.1"
REFERENCE_PACK_SCHEMAS = frozenset({REFERENCE_PACK_SCHEMA_V1, REFERENCE_PACK_SCHEMA})
REFERENCE_LEARNING_SCHEMA = "figure-agent.reference-learning.v1"
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
REFERENCE_LEARNING_ROLES = frozenset(
    {
        "apparatus_convention",
        "composition_reference",
        "density_reference",
        "journal_tone_reference",
        "style_anchor",
        "typography_reference",
    }
)
SEVERITIES = frozenset({"BLOCKER", "MAJOR", "MINOR", "NIT"})
REFERENCE_LEARNING_ALLOWED_AXES = {
    "palette family": ("palette", "color", "colour", "hue"),
    "density": ("density", "ink", "white space", "whitespace"),
    "typography hierarchy": ("typography", "type hierarchy", "label hierarchy"),
    "abstraction level": ("abstraction", "abstracted", "simplification"),
    "line language": ("line language", "stroke", "line-weight", "line weight"),
    "composition rhythm": ("composition", "rhythm", "stage-to-stage", "layout rhythm"),
}
REFERENCE_LEARNING_FORBIDDEN_GUARDS = {
    "component topology": ("topology", "hardware layout"),
    "exact geometry": ("exact geometry", "coordinate", "pixel similarity"),
    "label text": ("label text", "wording", "copy labels"),
    "claim payload": ("claim payload", "scientific claim", "physics story"),
    "panel semantics": ("panel semantics", "panel meaning", "story"),
}


class CritiqueReferencePackError(Exception):
    """Controlled error for malformed critique_reference_pack.yaml."""


def reference_pack_template(fixture: str) -> str:
    """Return a starter critique_reference_pack.yaml with explicit learning guards."""
    fixture_name = fixture.strip() or "<fixture-name>"
    return f"""schema: {REFERENCE_PACK_SCHEMA}
fixture: {fixture_name}
target_journal: Nature Communications
reference_class: mechanism_schematic
visual_ambition: solid_manuscript
comparison_references:
  - id: R001
    source: human_note
    path_or_citation: reference/<reference-image-or-citation>
    role: journal_register
must_match_traits:
  - id: T001
    trait: restrained journal-grade register grounded in R001
    reference_id: R001
must_avoid_traits:
  - id: A001
    trait: copying reference component topology or unbriefed panel semantics
    severity: BLOCKER
calibration_questions:
  - id: Q001
    question: What does this reference teach about polish without changing fixture semantics?
reference_learning:
  schema: {REFERENCE_LEARNING_SCHEMA}
  references:
    - path: reference/<reference-image>
      roles:
        - style_anchor
        - density_reference
        - typography_reference
        - composition_reference
      allowed_transfer:
        - palette family discipline, not exact colors
        - balanced ink density and white-space rhythm
        - typography hierarchy and compact label scale
        - abstraction level for mechanism simplification
        - line language and stroke hierarchy
        - composition rhythm across panels or stages
      forbidden_transfer:
        - copy component topology
        - copy exact geometry or coordinates
        - copy label text
        - copy claim payload
        - copy panel semantics
      rationale: Learn editorial style only; fixture semantics remain authoritative.
"""


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


def _require_string_list(
    data: dict[str, Any],
    key: str,
    *,
    label: str,
    allowed: frozenset[str] | None = None,
) -> list[str]:
    raw_items = _require_list(data.get(key), f"{label}.{key}")
    if not raw_items:
        raise CritiqueReferencePackError(f"{label}.{key} must be a non-empty list")
    items: list[str] = []
    for index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, str) or not raw_item.strip():
            raise CritiqueReferencePackError(
                f"{label}.{key}[{index}] must be a non-empty string"
            )
        item = raw_item.strip()
        if allowed is not None and item not in allowed:
            allowed_values = ", ".join(sorted(allowed))
            raise CritiqueReferencePackError(
                f"{label}.{key}[{index}] must be one of: {allowed_values}"
            )
        items.append(item)
    return items


def _require_safe_relative_path(value: str, label: str) -> None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise CritiqueReferencePackError(f"{label}.path must be a safe relative path")


def _missing_keyword_groups(items: list[str], groups: dict[str, tuple[str, ...]]) -> list[str]:
    text = " \n".join(items).lower()
    return [
        group_name
        for group_name, keywords in groups.items()
        if not any(keyword in text for keyword in keywords)
    ]


def _validate_reference_learning_transfer_quality(
    allowed_transfer: list[str],
    forbidden_transfer: list[str],
    label: str,
) -> None:
    missing_allowed = _missing_keyword_groups(
        allowed_transfer,
        REFERENCE_LEARNING_ALLOWED_AXES,
    )
    if missing_allowed:
        missing = ", ".join(missing_allowed)
        raise CritiqueReferencePackError(
            f"{label}.allowed_transfer must cover reference-learning axes: {missing}"
        )
    missing_forbidden = _missing_keyword_groups(
        forbidden_transfer,
        REFERENCE_LEARNING_FORBIDDEN_GUARDS,
    )
    if missing_forbidden:
        missing = ", ".join(missing_forbidden)
        raise CritiqueReferencePackError(
            f"{label}.forbidden_transfer must cover anti-copy guards: {missing}"
        )


def _validate_reference_learning(data: dict[str, Any], *, strict_authoring: bool) -> None:
    raw_learning = data.get("reference_learning")
    if raw_learning is None:
        return
    learning = _require_mapping(raw_learning, "critique_reference_pack.reference_learning")
    schema = _require_string(
        learning,
        "schema",
        label="critique_reference_pack.reference_learning",
    )
    if schema != REFERENCE_LEARNING_SCHEMA:
        raise CritiqueReferencePackError(
            "critique_reference_pack.reference_learning.schema must be "
            f"{REFERENCE_LEARNING_SCHEMA}"
        )
    references = _mapping_items(
        learning,
        "references",
        label="critique_reference_pack.reference_learning",
    )
    if not references:
        raise CritiqueReferencePackError(
            "critique_reference_pack.reference_learning.references must be non-empty"
        )
    all_allowed_transfer: list[str] = []
    all_forbidden_transfer: list[str] = []
    for index, item in enumerate(references):
        label = f"critique_reference_pack.reference_learning.references[{index}]"
        _require_safe_relative_path(_require_string(item, "path", label=label), label)
        _require_string_list(item, "roles", label=label, allowed=REFERENCE_LEARNING_ROLES)
        all_allowed_transfer.extend(_require_string_list(item, "allowed_transfer", label=label))
        all_forbidden_transfer.extend(_require_string_list(item, "forbidden_transfer", label=label))
        _require_string(item, "rationale", label=label)
    if strict_authoring:
        _validate_reference_learning_transfer_quality(
            all_allowed_transfer,
            all_forbidden_transfer,
            "critique_reference_pack.reference_learning",
        )


def load_reference_pack(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CritiqueReferencePackError(f"malformed YAML in {path}: {exc}") from exc
    data = _require_mapping(raw, "critique_reference_pack")
    schema = _require_string(data, "schema", label="critique_reference_pack")
    if schema not in REFERENCE_PACK_SCHEMAS:
        allowed_values = ", ".join(sorted(REFERENCE_PACK_SCHEMAS))
        raise CritiqueReferencePackError(
            f"critique_reference_pack.schema must be one of: {allowed_values}"
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
    _validate_reference_learning(data, strict_authoring=schema == REFERENCE_PACK_SCHEMA)
    return data


def load_optional_reference_pack(example_dir: Path) -> dict[str, Any] | None:
    path = example_dir / "critique_reference_pack.yaml"
    if not path.is_file():
        return None
    pack = load_reference_pack(path)
    fixture = pack.get("fixture")
    if fixture != example_dir.name:
        raise CritiqueReferencePackError(
            "critique_reference_pack.fixture must match example directory name: "
            f"{example_dir.name}"
        )
    return pack


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate or template figure-agent critique_reference_pack.yaml files."
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="critique_reference_pack.yaml path to validate",
    )
    parser.add_argument(
        "--template",
        metavar="FIXTURE",
        help="print a starter critique_reference_pack.yaml for FIXTURE",
    )
    args = parser.parse_args(argv)
    if args.template is not None:
        print(reference_pack_template(args.template), end="")
        return 0
    if args.path is None:
        parser.error("provide a pack path or --template FIXTURE")
    load_reference_pack(args.path)
    print(f"OK: reference pack valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
