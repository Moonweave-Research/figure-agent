#!/usr/bin/env python3
"""Generate text_boundary_checks from author-facing boundary layout declarations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


class TextBoundarySpecHelperError(ValueError):
    """Controlled error for malformed text boundary helper input."""


def _require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TextBoundarySpecHelperError(f"{label} must be a mapping")
    return value


def _require_list(value: object, label: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TextBoundarySpecHelperError(f"{label} must be a list")
    return value


def _require_id(item: dict[str, Any], label: str) -> str:
    item_id = item.get("id")
    if not isinstance(item_id, str) or not item_id.strip():
        raise TextBoundarySpecHelperError(f"{label}.id is required")
    return item_id.strip()


def _require_number(item: dict[str, Any], key: str, label: str) -> float:
    value = item.get(key)
    if not isinstance(value, int | float):
        raise TextBoundarySpecHelperError(f"{label}.{key} must be a number")
    return float(value)


def _require_number_list(
    item: dict[str, Any],
    key: str,
    *,
    length: int,
    label: str,
) -> list[float]:
    value = item.get(key)
    if (
        not isinstance(value, list)
        or len(value) != length
        or not all(isinstance(entry, int | float) for entry in value)
    ):
        raise TextBoundarySpecHelperError(f"{label}.{key} must be a {length}-number list")
    return [float(entry) for entry in value]


def _optional_text_allowlist(item: dict[str, Any], label: str) -> list[str] | None:
    value = item.get("text_allowlist")
    if value is None:
        return None
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(entry, str) and entry.strip() for entry in value)
    ):
        raise TextBoundarySpecHelperError(
            f"{label}.text_allowlist must be a non-empty string list"
        )
    return [entry.strip() for entry in value]


def _optional_text_phrases(
    item: dict[str, Any],
    label: str,
) -> list[dict[str, list[str] | str]] | None:
    value = item.get("text_phrases")
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        raise TextBoundarySpecHelperError(f"{label}.text_phrases must be a non-empty list")
    phrases: list[dict[str, list[str] | str]] = []
    seen_ids: set[str] = set()
    for index, raw_phrase in enumerate(value):
        phrase_label = f"{label}.text_phrases[{index}]"
        if not isinstance(raw_phrase, dict):
            raise TextBoundarySpecHelperError(f"{phrase_label} must be a mapping")
        phrase_id = raw_phrase.get("id")
        if not isinstance(phrase_id, str) or not phrase_id.strip():
            raise TextBoundarySpecHelperError(f"{phrase_label}.id is required")
        phrase_id = phrase_id.strip()
        if phrase_id in seen_ids:
            raise TextBoundarySpecHelperError(f"{phrase_label}.id is duplicate")
        seen_ids.add(phrase_id)
        words = raw_phrase.get("words")
        if (
            not isinstance(words, list)
            or len(words) < 2
            or not all(isinstance(word, str) and word.strip() for word in words)
        ):
            raise TextBoundarySpecHelperError(
                f"{phrase_label}.words must contain at least two non-empty strings"
            )
        phrases.append({"id": phrase_id, "words": [word.strip() for word in words]})
    return phrases


def _clearance(item: dict[str, Any], default_clearance: float) -> float:
    value = item.get("clearance_pt", default_clearance)
    if not isinstance(value, int | float):
        raise TextBoundarySpecHelperError("clearance_pt must be a number")
    return float(value)


def _role(item: dict[str, Any], default_role: str) -> str:
    value = item.get("role", default_role)
    if not isinstance(value, str) or not value.strip():
        raise TextBoundarySpecHelperError("role must be a non-empty string")
    return value.strip()


def _layout_clearance(layout: dict[str, Any]) -> float:
    value = layout.get("clearance_pt", 0.5)
    if not isinstance(value, int | float):
        raise TextBoundarySpecHelperError("text_boundary_layout.clearance_pt must be a number")
    return float(value)


def build_text_boundary_checks(layout: dict[str, Any]) -> list[dict[str, Any]]:
    """Build deterministic Issue 29 text_boundary_checks from layout declarations."""
    layout = _require_mapping(layout, "text_boundary_layout")
    default_clearance = _layout_clearance(layout)
    checks: list[dict[str, Any]] = []

    for index, raw_item in enumerate(_require_list(layout.get("row_boxes"), "row_boxes")):
        item = _require_mapping(raw_item, f"row_boxes[{index}]")
        item_id = _require_id(item, f"row_boxes[{index}]")
        check = {
            "id": f"{item_id}_contain_text",
            "kind": "rect",
            "role": _role(item, "row_box"),
            "bbox_pdf_cm": _require_number_list(
                item,
                "bbox_pdf_cm",
                length=4,
                label=f"row_boxes[{index}]",
            ),
            "mode": "contain_text",
            "clearance_pt": _clearance(item, default_clearance),
        }
        text_allowlist = _optional_text_allowlist(item, f"row_boxes[{index}]")
        if text_allowlist is not None:
            check["text_allowlist"] = text_allowlist
        text_phrases = _optional_text_phrases(item, f"row_boxes[{index}]")
        if text_phrases is not None:
            check["text_phrases"] = text_phrases
        checks.append(check)

    for index, raw_item in enumerate(_require_list(layout.get("column_rules"), "column_rules")):
        item = _require_mapping(raw_item, f"column_rules[{index}]")
        item_id = _require_id(item, f"column_rules[{index}]")
        checks.append(
            {
                "id": f"{item_id}_column_rule",
                "kind": "vertical_line",
                "role": _role(item, "column_rule"),
                "x_pdf_cm": _require_number(item, "x_pdf_cm", f"column_rules[{index}]"),
                "y_range_pdf_cm": _require_number_list(
                    item,
                    "y_range_pdf_cm",
                    length=2,
                    label=f"column_rules[{index}]",
                ),
                "clearance_pt": _clearance(item, default_clearance),
            }
        )

    for index, raw_item in enumerate(
        _require_list(layout.get("horizontal_rules"), "horizontal_rules")
    ):
        item = _require_mapping(raw_item, f"horizontal_rules[{index}]")
        item_id = _require_id(item, f"horizontal_rules[{index}]")
        checks.append(
            {
                "id": f"{item_id}_horizontal_rule",
                "kind": "horizontal_line",
                "role": _role(item, "panel_boundary"),
                "y_pdf_cm": _require_number(item, "y_pdf_cm", f"horizontal_rules[{index}]"),
                "x_range_pdf_cm": _require_number_list(
                    item,
                    "x_range_pdf_cm",
                    length=2,
                    label=f"horizontal_rules[{index}]",
                ),
                "clearance_pt": _clearance(item, default_clearance),
            }
        )

    for index, raw_item in enumerate(
        _require_list(layout.get("forbidden_rects"), "forbidden_rects")
    ):
        item = _require_mapping(raw_item, f"forbidden_rects[{index}]")
        item_id = _require_id(item, f"forbidden_rects[{index}]")
        checks.append(
            {
                "id": f"{item_id}_avoid_inside",
                "kind": "rect",
                "role": _role(item, "forbidden_region"),
                "bbox_pdf_cm": _require_number_list(
                    item,
                    "bbox_pdf_cm",
                    length=4,
                    label=f"forbidden_rects[{index}]",
                ),
                "mode": "avoid_inside",
                "clearance_pt": _clearance(item, default_clearance),
            }
        )

    if not checks:
        raise TextBoundarySpecHelperError("text_boundary_layout contains no boundary entries")
    return checks


def _load_spec(spec_path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise TextBoundarySpecHelperError(f"malformed spec.yaml: {exc}") from exc
    if not isinstance(payload, dict):
        raise TextBoundarySpecHelperError("spec.yaml must be a mapping")
    return payload


def _fixture_dir(raw: str) -> Path:
    path = Path(raw)
    if path.name == "spec.yaml":
        return path.parent
    return path


def _dump_checks(checks: list[dict[str, Any]]) -> str:
    return yaml.safe_dump(
        {"text_boundary_checks": checks},
        sort_keys=False,
        allow_unicode=False,
    )


def _write_spec(spec_path: Path, spec: dict[str, Any]) -> None:
    spec_path.write_text(
        yaml.safe_dump(spec, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", help="examples/<name> directory or path to spec.yaml")
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace spec.yaml text_boundary_checks with generated checks",
    )
    args = parser.parse_args(argv)

    fixture_dir = _fixture_dir(args.fixture)
    spec_path = fixture_dir if fixture_dir.name == "spec.yaml" else fixture_dir / "spec.yaml"
    if not spec_path.is_file():
        print(f"ERROR: missing spec.yaml: {spec_path}", file=sys.stderr)
        return 2
    try:
        spec = _load_spec(spec_path)
        layout = spec.get("text_boundary_layout")
        if layout is None:
            raise TextBoundarySpecHelperError("text_boundary_layout is missing")
        checks = build_text_boundary_checks(layout)
    except TextBoundarySpecHelperError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.write:
        spec["text_boundary_checks"] = checks
        _write_spec(spec_path, spec)
        print(f"wrote {len(checks)} text_boundary_checks to {spec_path}")
        return 0

    print(_dump_checks(checks), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
