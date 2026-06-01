"""Optional paper-wide aesthetic context contract for /fig_critique."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import fixture_identity
import yaml
from aesthetic_intent import DENSITIES, SEVERITIES, TARGET_JOURNALS, VISUAL_MATURITIES

PAPER_AESTHETIC_CONTEXT_SCHEMA = "figure-agent.paper-aesthetic-context.v1"
PAPER_CONTEXT_DIRNAME = "_paper_aesthetic_contexts"

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_SHARED_LANGUAGE_DIMENSIONS = frozenset(
    {
        "palette",
        "typography",
        "line_weight",
        "whitespace",
        "panel_grammar",
        "iconography",
        "data_ink",
        "visual_identity",
        "polish_route",
        "figure_series",
    }
)
_SHARED_LANGUAGE_PRIORITIES = frozenset({"required", "recommended", "optional"})
_FIGURE_ROLES = frozenset(
    {
        "overview_mechanism",
        "mechanism_detail",
        "data_evidence",
        "methods_apparatus",
        "graphical_abstract",
        "supplemental",
    }
)
_MAX_SHARED_LANGUAGE_ITEMS = 12
_MAX_FIGURE_ROLES = 50
_MAX_MUST_AVOID_ITEMS = 12


class PaperAestheticContextError(Exception):
    """Controlled error for malformed paper-wide aesthetic context packs."""


def is_safe_paper_context_id(value: str) -> bool:
    return bool(_SAFE_ID_RE.fullmatch(value))


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PaperAestheticContextError(f"{label} must be a mapping")
    return value


def _require_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PaperAestheticContextError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def _require_safe_id(data: dict[str, Any], key: str, *, label: str) -> str:
    value = _require_string(data, key, label=label)
    if not is_safe_paper_context_id(value):
        raise PaperAestheticContextError(
            f"{label}.{key} must be a safe id: start with an ASCII letter or number, "
            "then use only ASCII letters, numbers, _, ., and -"
        )
    return value


def _require_safe_fixture_name(data: dict[str, Any], key: str, *, label: str) -> str:
    value = _require_string(data, key, label=label)
    try:
        fixture_identity.validate_fixture_name(value)
    except ValueError as exc:
        raise PaperAestheticContextError(
            f"{label}.{key} must be a safe fixture name: {exc}"
        ) from exc
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
        raise PaperAestheticContextError(f"{label}.{key} must be one of: {allowed_values}")
    return value


def _string_items(data: dict[str, Any], key: str, *, label: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise PaperAestheticContextError(f"{label}.{key} must be a non-empty list")
    items: list[str] = []
    for index, raw_item in enumerate(value):
        if not isinstance(raw_item, str) or not raw_item.strip():
            raise PaperAestheticContextError(f"{label}.{key}[{index}] must be a non-empty string")
        items.append(raw_item.strip())
    return items


def _optional_string_items(data: dict[str, Any], key: str, *, label: str) -> list[str]:
    if key not in data:
        return []
    return _string_items(data, key, label=label)


def _mapping_items(
    data: dict[str, Any],
    key: str,
    *,
    label: str,
    id_key: str = "id",
    max_items: int,
) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise PaperAestheticContextError(f"{label}.{key} must be a non-empty list")
    if len(value) > max_items:
        raise PaperAestheticContextError(
            f"{label}.{key} must contain at most {max_items} items"
        )
    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(value):
        item_label = f"{label}.{key}[{index}]"
        item = _require_mapping(raw_item, item_label)
        item_id = _require_string(item, id_key, label=item_label)
        if item_id in seen_ids:
            raise PaperAestheticContextError(f"{item_label}.{id_key} is duplicated: {item_id}")
        seen_ids.add(item_id)
        items.append(item)
    return items


def paper_context_id_from_spec(spec: dict[str, Any]) -> str | None:
    raw_id = spec.get("paper_aesthetic_context")
    if raw_id is None:
        return None
    if not isinstance(raw_id, str) or not raw_id.strip():
        raise PaperAestheticContextError("spec.paper_aesthetic_context must be a non-empty string")
    paper_id = raw_id.strip()
    if not is_safe_paper_context_id(paper_id):
        raise PaperAestheticContextError(
            "spec.paper_aesthetic_context must be a safe id: "
            "start with an ASCII letter or number, then use only ASCII letters, "
            "numbers, _, ., and -"
        )
    return paper_id


def paper_context_path_for_id(example_dir: Path, paper_id: str) -> Path:
    if not is_safe_paper_context_id(paper_id):
        raise PaperAestheticContextError(
            "paper_aesthetic_context id must be a safe id: start with an ASCII "
            "letter or number, then use only ASCII letters, numbers, _, ., and -"
        )
    return example_dir.parent / PAPER_CONTEXT_DIRNAME / f"{paper_id}.yaml"


def declared_paper_context_path(example_dir: Path, spec: dict[str, Any]) -> Path | None:
    paper_id = paper_context_id_from_spec(spec)
    if paper_id is None:
        return None
    return paper_context_path_for_id(example_dir, paper_id)


def _validate_shared_visual_language(data: dict[str, Any]) -> set[str]:
    items = _mapping_items(
        data,
        "shared_visual_language",
        label="paper_aesthetic_context",
        max_items=_MAX_SHARED_LANGUAGE_ITEMS,
    )
    ids: set[str] = set()
    for index, item in enumerate(items):
        label = f"paper_aesthetic_context.shared_visual_language[{index}]"
        item_id = _require_safe_id(item, "id", label=label)
        ids.add(item_id)
        _require_enum(item, "dimension", _SHARED_LANGUAGE_DIMENSIONS, label=label)
        _require_string(item, "instruction", label=label)
        _require_enum(item, "priority", _SHARED_LANGUAGE_PRIORITIES, label=label)
        _string_items(item, "positive_signals", label=label)
        _string_items(item, "anti_patterns", label=label)
    return ids


def _validate_figure_roles(data: dict[str, Any], shared_ids: set[str]) -> None:
    roles = _mapping_items(
        data,
        "figure_roles",
        label="paper_aesthetic_context",
        id_key="fixture",
        max_items=_MAX_FIGURE_ROLES,
    )
    for index, item in enumerate(roles):
        label = f"paper_aesthetic_context.figure_roles[{index}]"
        _require_safe_fixture_name(item, "fixture", label=label)
        _require_enum(item, "role", _FIGURE_ROLES, label=label)
        must_align_with = _string_items(item, "must_align_with", label=label)
        unknown = sorted(set(must_align_with) - shared_ids)
        if unknown:
            raise PaperAestheticContextError(
                f"{label}.must_align_with contains unknown must_align_with ids: "
                + ", ".join(unknown)
            )
        _optional_string_items(item, "allowed_variations", label=label)


def _validate_must_avoid(data: dict[str, Any]) -> None:
    items = _mapping_items(
        data,
        "must_avoid",
        label="paper_aesthetic_context",
        max_items=_MAX_MUST_AVOID_ITEMS,
    )
    for index, item in enumerate(items):
        label = f"paper_aesthetic_context.must_avoid[{index}]"
        _require_safe_id(item, "id", label=label)
        _require_string(item, "pattern", label=label)
        _require_enum(item, "severity", SEVERITIES, label=label)


def load_paper_aesthetic_context(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PaperAestheticContextError(f"malformed YAML in {path}: {exc}") from exc
    data = _require_mapping(raw, "paper_aesthetic_context")
    schema = _require_string(data, "schema", label="paper_aesthetic_context")
    if schema != PAPER_AESTHETIC_CONTEXT_SCHEMA:
        raise PaperAestheticContextError(
            "paper_aesthetic_context.schema must equal "
            f"{PAPER_AESTHETIC_CONTEXT_SCHEMA}"
        )
    paper_id = _require_safe_id(data, "paper_id", label="paper_aesthetic_context")
    if paper_id != path.stem:
        raise PaperAestheticContextError(
            "paper_aesthetic_context.paper_id must match filename stem"
        )
    _require_enum(data, "target_journal", TARGET_JOURNALS, label="paper_aesthetic_context")
    _require_enum(data, "visual_maturity", VISUAL_MATURITIES, label="paper_aesthetic_context")
    _require_enum(data, "density", DENSITIES, label="paper_aesthetic_context")
    shared_ids = _validate_shared_visual_language(data)
    _validate_figure_roles(data, shared_ids)
    _validate_must_avoid(data)
    return data


def matching_figure_role(pack: dict[str, Any], fixture: str) -> dict[str, Any]:
    raw_roles = pack.get("figure_roles")
    if not isinstance(raw_roles, list):
        raise PaperAestheticContextError("paper_aesthetic_context.figure_roles must be a list")
    for role in raw_roles:
        if isinstance(role, dict) and role.get("fixture") == fixture:
            return role
    raise PaperAestheticContextError(
        f"paper_aesthetic_context.figure_roles must include fixture: {fixture}"
    )


def load_optional_paper_aesthetic_context(
    example_dir: Path,
    spec: dict[str, Any],
) -> dict[str, Any] | None:
    path = declared_paper_context_path(example_dir, spec)
    if path is None:
        return None
    if not path.is_file():
        raise PaperAestheticContextError(f"missing paper aesthetic context pack: {path}")
    pack = load_paper_aesthetic_context(path)
    matching_figure_role(pack, example_dir.name)
    return pack


def paper_context_anchors(pack: dict[str, Any], fixture: str) -> set[str]:
    role = matching_figure_role(pack, fixture)
    anchors = {
        str(pack.get("paper_id", "")).strip(),
        str(pack.get("target_journal", "")).strip(),
        str(pack.get("visual_maturity", "")).strip(),
        str(pack.get("density", "")).strip(),
        str(role.get("role", "")).strip(),
    }
    anchors.update(_string_items(role, "must_align_with", label="paper_aesthetic_context.role"))
    raw_must_avoid = pack.get("must_avoid")
    if isinstance(raw_must_avoid, list):
        for item in raw_must_avoid:
            if isinstance(item, dict):
                item_id = item.get("id")
                if isinstance(item_id, str) and item_id.strip():
                    anchors.add(item_id.strip())
    return {anchor for anchor in anchors if anchor}


def paper_aesthetic_context_template(
    *,
    paper_id: str,
    fixture: str,
    target_journal: str = "Nature Communications",
    visual_maturity: str = "restrained",
    density: str = "balanced",
    role: str = "overview_mechanism",
) -> str:
    if not is_safe_paper_context_id(paper_id):
        raise PaperAestheticContextError(
            "paper_id must be a safe id: start with an ASCII letter or number, "
            "then use only ASCII letters, numbers, _, ., and -"
        )
    try:
        fixture_identity.validate_fixture_name(fixture)
    except ValueError as exc:
        raise PaperAestheticContextError(f"fixture must be a safe fixture name: {exc}") from exc
    if target_journal not in TARGET_JOURNALS:
        raise PaperAestheticContextError("target_journal is not supported")
    if visual_maturity not in VISUAL_MATURITIES:
        raise PaperAestheticContextError("visual_maturity is not supported")
    if density not in DENSITIES:
        raise PaperAestheticContextError("density is not supported")
    if role not in _FIGURE_ROLES:
        raise PaperAestheticContextError("role is not supported")
    data = {
        "schema": PAPER_AESTHETIC_CONTEXT_SCHEMA,
        "paper_id": paper_id,
        "target_journal": target_journal,
        "visual_maturity": visual_maturity,
        "density": density,
        "shared_visual_language": [
            {
                "id": "series_palette",
                "dimension": "palette",
                "instruction": (
                    "Reuse semantic color roles across figures and avoid one-off "
                    "decorative hues."
                ),
                "priority": "required",
                "positive_signals": [
                    "the same hue family means the same physical or narrative role",
                ],
                "anti_patterns": [
                    "one figure introduces a saturated accent absent from the series",
                ],
            },
            {
                "id": "series_typography",
                "dimension": "typography",
                "instruction": "Keep label scale and hierarchy consistent across figures.",
                "priority": "required",
                "positive_signals": [
                    "equivalent labels have equivalent visual weight",
                ],
                "anti_patterns": [
                    "one figure reads like a slide while others read like journal artwork",
                ],
            },
            {
                "id": "source_first_polish",
                "dimension": "polish_route",
                "instruction": (
                    "Keep semantic layout changes in source; reserve SVG polish for "
                    "finish-only deltas."
                ),
                "priority": "recommended",
                "positive_signals": [
                    "SVG polish does not alter scientific geometry",
                ],
                "anti_patterns": [
                    "one figure depends on unbackported SVG edits for meaning",
                ],
            },
        ],
        "figure_roles": [
            {
                "fixture": fixture.strip(),
                "role": role,
                "must_align_with": [
                    "series_palette",
                    "series_typography",
                    "source_first_polish",
                ],
                "allowed_variations": [
                    "may carry figure-specific emphasis when explicitly justified",
                ],
            }
        ],
        "must_avoid": [
            {
                "id": "series_drift",
                "pattern": "one figure appears to come from a different visual system",
                "severity": "MAJOR",
            },
            {
                "id": "decorative_context_leak",
                "pattern": "cover-like or decorative treatment leaks into main figures",
                "severity": "MAJOR",
            },
        ],
    }
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def write_paper_aesthetic_context(path: Path, text: str, *, force: bool = False) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"paper_aesthetic_context already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _template_path(examples_dir: Path, paper_id: str) -> Path:
    if not examples_dir.is_dir():
        raise PaperAestheticContextError(f"missing examples directory: {examples_dir}")
    if not is_safe_paper_context_id(paper_id):
        raise PaperAestheticContextError("paper_id must be a safe id")
    return examples_dir / PAPER_CONTEXT_DIRNAME / f"{paper_id}.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, help="paper aesthetic context YAML")
    parser.add_argument("--template", help="paper context id to scaffold")
    parser.add_argument("--fixture", help="fixture name to include in figure_roles")
    parser.add_argument("--examples-dir", type=Path, default=Path("examples"))
    parser.add_argument("--target-journal", default="Nature Communications")
    parser.add_argument("--visual-maturity", default="restrained")
    parser.add_argument("--density", default="balanced")
    parser.add_argument("--role", default="overview_mechanism")
    parser.add_argument("--write-template", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.template is not None:
            if not isinstance(args.fixture, str) or not args.fixture.strip():
                parser.error("--template requires --fixture")
            text = paper_aesthetic_context_template(
                paper_id=args.template,
                fixture=args.fixture,
                target_journal=args.target_journal,
                visual_maturity=args.visual_maturity,
                density=args.density,
                role=args.role,
            )
            if args.write_template:
                path = _template_path(args.examples_dir, args.template)
                write_paper_aesthetic_context(path, text, force=args.force)
                print(path)
            else:
                print(text, end="")
            return 0
        if args.path is None:
            parser.error("provide a context YAML path or --template PAPER_ID")
        load_paper_aesthetic_context(args.path)
        print(f"OK: paper aesthetic context valid: {args.path}")
        return 0
    except (FileExistsError, PaperAestheticContextError) as exc:
        print(f"paper_aesthetic_context.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
