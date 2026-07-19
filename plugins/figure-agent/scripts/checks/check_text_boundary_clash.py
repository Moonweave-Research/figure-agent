#!/usr/bin/env python3
"""Detect rendered text crossing declared figure boundary geometry.

The checker is report-only by default. Pass --strict to return exit 1 when
any candidate is found, matching the collision/visual-clash strict contract.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from check_visual_clash import extract_pdf_words_and_page

SCHEMA = "figure-agent.text-boundary-clash.v1"
CM_TO_PT = 72.0 / 2.54
DEFAULT_MAX_PHRASE_GAP_PT = 6.0
DEFAULT_MAX_PHRASE_Y_CENTER_DELTA_PT = 6.0


class TextBoundaryClashError(ValueError):
    """Controlled error for malformed text boundary configuration."""


def _cm_to_pt(value: float | int) -> float:
    return round(float(value) * CM_TO_PT, 6)


def _pdf_cm_range_to_pt(values: object, *, field: str) -> list[float]:
    if (
        not isinstance(values, list)
        or len(values) != 2
        or not all(isinstance(item, int | float) for item in values)
    ):
        raise TextBoundaryClashError(f"{field} must be a two-number list")
    a = _cm_to_pt(values[0])
    b = _cm_to_pt(values[1])
    return [min(a, b), max(a, b)]


def _bbox_pdf_cm_to_pt(values: object, *, field: str) -> list[float]:
    if (
        not isinstance(values, list)
        or len(values) != 4
        or not all(isinstance(item, int | float) for item in values)
    ):
        raise TextBoundaryClashError(f"{field} must be a four-number list")
    x1 = _cm_to_pt(values[0])
    y1 = _cm_to_pt(values[1])
    x2 = _cm_to_pt(values[2])
    y2 = _cm_to_pt(values[3])
    return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]


def _text_allowlist(check: dict[str, Any]) -> set[str] | None:
    value = check.get("text_allowlist")
    if value is None:
        return None
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise TextBoundaryClashError(
            f"{check['id']}.text_allowlist must be a non-empty string list"
        )
    return {item.strip() for item in value}


def _text_phrases(check: dict[str, Any]) -> list[dict[str, Any]]:
    value = check.get("text_phrases")
    if value is None:
        return []
    if not isinstance(value, list) or not value:
        raise TextBoundaryClashError(f"{check['id']}.text_phrases must be a non-empty list")
    phrases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_phrase in enumerate(value):
        label = f"{check['id']}.text_phrases[{index}]"
        if not isinstance(raw_phrase, dict):
            raise TextBoundaryClashError(f"{label} must be a mapping")
        phrase_id = raw_phrase.get("id")
        if not isinstance(phrase_id, str) or not phrase_id.strip():
            raise TextBoundaryClashError(f"{label}.id must be a non-empty string")
        phrase_id = phrase_id.strip()
        if phrase_id in seen_ids:
            raise TextBoundaryClashError(f"{check['id']}.text_phrases duplicate id: {phrase_id}")
        seen_ids.add(phrase_id)
        words = raw_phrase.get("words")
        if (
            not isinstance(words, list)
            or len(words) < 2
            or not all(isinstance(item, str) and item.strip() for item in words)
        ):
            raise TextBoundaryClashError(f"{label}.words must contain at least two strings")
        phrases.append({"id": phrase_id, "words": [item.strip() for item in words]})
    return phrases


def _non_negative_number(value: object, *, field: str) -> float:
    if not isinstance(value, int | float) or float(value) < 0:
        raise TextBoundaryClashError(f"{field} must be a non-negative number")
    return float(value)


def _phrase_tolerances(check: dict[str, Any]) -> tuple[float, float]:
    max_gap = _non_negative_number(
        check.get("max_phrase_gap_pt", DEFAULT_MAX_PHRASE_GAP_PT),
        field=f"{check['id']}.max_phrase_gap_pt",
    )
    max_center_delta = _non_negative_number(
        check.get("max_phrase_y_center_delta_pt", DEFAULT_MAX_PHRASE_Y_CENTER_DELTA_PT),
        field=f"{check['id']}.max_phrase_y_center_delta_pt",
    )
    return max_gap, max_center_delta


def _ranges_overlap(a_min: float, a_max: float, b_min: float, b_max: float) -> bool:
    return max(a_min, b_min) <= min(a_max, b_max)


def _word_bbox(word: dict[str, Any]) -> list[float]:
    return [
        round(float(word["xmin"]), 6),
        round(float(word["ymin"]), 6),
        round(float(word["xmax"]), 6),
        round(float(word["ymax"]), 6),
    ]


def _word_sort_key(word: dict[str, Any]) -> tuple[float, float, float, float, str]:
    return (
        float(word["ymin"]),
        float(word["xmin"]),
        float(word["ymax"]),
        float(word["xmax"]),
        str(word.get("text", "")),
    )


def _word_center_y(word: dict[str, Any]) -> float:
    return (float(word["ymin"]) + float(word["ymax"])) / 2.0


def _same_phrase_line(
    left: dict[str, Any],
    right: dict[str, Any],
    max_center_delta: float,
) -> bool:
    return _ranges_overlap(
        float(left["ymin"]),
        float(left["ymax"]),
        float(right["ymin"]),
        float(right["ymax"]),
    ) or abs(_word_center_y(left) - _word_center_y(right)) <= max_center_delta


def _check_sort_key(check: dict[str, Any]) -> tuple[str, str]:
    return (str(check.get("id", "")), str(check.get("kind", "")))


def load_text_boundary_checks(spec_path: Path | None) -> list[dict[str, Any]]:
    """Load optional spec.yaml text_boundary_checks."""
    if spec_path is None or not spec_path.is_file():
        return []
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise TextBoundaryClashError(f"malformed spec.yaml: {exc}") from exc
    if spec is None:
        return []
    if not isinstance(spec, dict):
        raise TextBoundaryClashError("spec.yaml must be a mapping")
    raw_checks = spec.get("text_boundary_checks")
    if raw_checks is None:
        return []
    if not isinstance(raw_checks, list):
        raise TextBoundaryClashError("spec.yaml text_boundary_checks must be a list")
    checks: list[dict[str, Any]] = []
    for index, raw_check in enumerate(raw_checks):
        if not isinstance(raw_check, dict):
            raise TextBoundaryClashError(f"text_boundary_checks[{index}] must be a mapping")
        check = dict(raw_check)
        check_id = check.get("id")
        check_kind = check.get("kind")
        role = check.get("role")
        if not isinstance(check_id, str) or not check_id.strip():
            raise TextBoundaryClashError(f"text_boundary_checks[{index}].id is required")
        if check_kind not in {"vertical_line", "horizontal_line", "rect"}:
            raise TextBoundaryClashError(
                f"text_boundary_checks[{index}].kind must be vertical_line, "
                "horizontal_line, or rect"
            )
        if not isinstance(role, str) or not role.strip():
            raise TextBoundaryClashError(f"text_boundary_checks[{index}].role is required")
        checks.append(check)
    return checks


def detect_text_boundary_clashes(
    words: list[dict[str, Any]],
    page_size_pt: tuple[float, float],
    checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return deterministic text-boundary clash candidates."""
    _ = page_size_pt
    candidates: list[dict[str, Any]] = []
    for check in sorted(checks, key=_check_sort_key):
        if check["kind"] == "rect":
            candidates.extend(_rect_candidates(check, words))
            continue
        for word in sorted(words, key=_word_sort_key):
            candidate = _candidate_for_word(check, word)
            if candidate is not None:
                candidates.append(candidate)

    for index, candidate in enumerate(candidates, start=1):
        candidate["id"] = f"TB{index:03d}"
    return candidates


def _candidate_for_word(check: dict[str, Any], word: dict[str, Any]) -> dict[str, Any] | None:
    kind = check["kind"]
    if kind == "vertical_line":
        return _vertical_candidate(check, word)
    if kind == "horizontal_line":
        return _horizontal_candidate(check, word)
    if kind == "rect":
        return _rect_candidate(check, word)
    return None


def _base_candidate(
    check: dict[str, Any],
    word: dict[str, Any],
    *,
    kind: str,
    boundary_pt: dict[str, float | list[float]],
    clearance_pt: float,
) -> dict[str, Any]:
    return {
        "id": "",
        "kind": kind,
        "text": str(word.get("text", "")),
        "boundary_id": str(check["id"]),
        "boundary_role": str(check["role"]),
        "bbox_pt": _word_bbox(word),
        "boundary_pt": boundary_pt,
        "clearance_pt": round(clearance_pt, 6),
    }


def _phrase_word(
    span: list[dict[str, Any]],
    *,
    phrase_id: str,
    phrase_words: list[str],
) -> dict[str, Any]:
    return {
        "text": " ".join(phrase_words),
        "phrase_id": phrase_id,
        "words": phrase_words,
        "text_source": "text_phrases",
        "xmin": min(float(word["xmin"]) for word in span),
        "ymin": min(float(word["ymin"]) for word in span),
        "xmax": max(float(word["xmax"]) for word in span),
        "ymax": max(float(word["ymax"]) for word in span),
    }


def _group_phrase_words(
    words: list[dict[str, Any]],
    phrase: dict[str, Any],
    *,
    max_gap: float,
    max_center_delta: float,
) -> list[dict[str, Any]]:
    sorted_words = sorted(words, key=_word_sort_key)
    phrase_words = phrase["words"]
    matches: list[dict[str, Any]] = []
    seen_spans: set[tuple[tuple[float, float, float, float], ...]] = set()
    for start_index, first_word in enumerate(sorted_words):
        if str(first_word.get("text", "")).strip() != phrase_words[0]:
            continue
        span = [first_word]
        search_after = start_index + 1
        for expected_text in phrase_words[1:]:
            previous = span[-1]
            next_word = None
            for candidate_index, candidate in enumerate(
                sorted_words[search_after:],
                start=search_after,
            ):
                if float(candidate["xmin"]) < float(previous["xmax"]):
                    continue
                if float(candidate["xmin"]) - float(previous["xmax"]) > max_gap:
                    break
                if str(candidate.get("text", "")).strip() != expected_text:
                    continue
                if not _same_phrase_line(previous, candidate, max_center_delta):
                    continue
                next_word = candidate
                search_after = candidate_index + 1
                break
            if next_word is None:
                break
            span.append(next_word)
        if len(span) != len(phrase_words):
            continue
        span_key = tuple(tuple(_word_bbox(word)) for word in span)
        if span_key in seen_spans:
            continue
        seen_spans.add(span_key)
        matches.append(
            _phrase_word(
                span,
                phrase_id=str(phrase["id"]),
                phrase_words=list(phrase_words),
            )
        )
    return matches


def _vertical_candidate(check: dict[str, Any], word: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(check.get("x_pdf_cm"), int | float):
        raise TextBoundaryClashError(f"{check['id']}.x_pdf_cm must be a number")
    y_range = _pdf_cm_range_to_pt(
        check.get("y_range_pdf_cm"),
        field=f"{check['id']}.y_range_pdf_cm",
    )
    x = _cm_to_pt(check["x_pdf_cm"])
    clearance = float(check.get("clearance_pt", 0.0) or 0.0)
    if not _ranges_overlap(float(word["ymin"]), float(word["ymax"]), y_range[0], y_range[1]):
        return None
    if float(word["xmin"]) <= x + clearance and float(word["xmax"]) >= x - clearance:
        return _base_candidate(
            check,
            word,
            kind="text_crosses_vertical_boundary",
            boundary_pt={"x": round(x, 6), "y_range": y_range},
            clearance_pt=clearance,
        )
    return None


def _horizontal_candidate(check: dict[str, Any], word: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(check.get("y_pdf_cm"), int | float):
        raise TextBoundaryClashError(f"{check['id']}.y_pdf_cm must be a number")
    x_range = _pdf_cm_range_to_pt(
        check.get("x_range_pdf_cm"), field=f"{check['id']}.x_range_pdf_cm"
    )
    y = _cm_to_pt(check["y_pdf_cm"])
    clearance = float(check.get("clearance_pt", 0.0) or 0.0)
    if not _ranges_overlap(float(word["xmin"]), float(word["xmax"]), x_range[0], x_range[1]):
        return None
    if float(word["ymin"]) <= y + clearance and float(word["ymax"]) >= y - clearance:
        return _base_candidate(
            check,
            word,
            kind="text_crosses_horizontal_boundary",
            boundary_pt={"y": round(y, 6), "x_range": x_range},
            clearance_pt=clearance,
        )
    return None


def _rect_candidate(check: dict[str, Any], word: dict[str, Any]) -> dict[str, Any] | None:
    rect = _bbox_pdf_cm_to_pt(check.get("bbox_pdf_cm"), field=f"{check['id']}.bbox_pdf_cm")
    mode = check.get("mode")
    if mode not in {"contain_text", "avoid_inside"}:
        raise TextBoundaryClashError(f"{check['id']}.mode must be contain_text or avoid_inside")
    clearance = float(check.get("clearance_pt", 0.0) or 0.0)
    xmin = float(word["xmin"])
    ymin = float(word["ymin"])
    xmax = float(word["xmax"])
    ymax = float(word["ymax"])
    if mode == "contain_text":
        allowlist = _text_allowlist(check)
        has_phrase_source = bool(check.get("text_phrases"))
        if allowlist is not None and str(word.get("text", "")).strip() not in allowlist:
            return None
        if allowlist is None and has_phrase_source and word.get("text_source") != "text_phrases":
            return None
        outside = (
            xmin < rect[0] + clearance
            or ymin < rect[1] + clearance
            or xmax > rect[2] - clearance
            or ymax > rect[3] - clearance
        )
        if not outside:
            return None
        return _base_candidate(
            check,
            word,
            kind="text_outside_rect",
            boundary_pt={"bbox": rect, "mode": "contain_text"},
            clearance_pt=clearance,
        )
    intersects = _ranges_overlap(xmin, xmax, rect[0] - clearance, rect[2] + clearance) and (
        _ranges_overlap(ymin, ymax, rect[1] - clearance, rect[3] + clearance)
    )
    if not intersects:
        return None
    return _base_candidate(
        check,
        word,
        kind="text_inside_forbidden_rect",
        boundary_pt={"bbox": rect, "mode": "avoid_inside"},
        clearance_pt=clearance,
    )


def _rect_candidates(
    check: dict[str, Any],
    words: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if check.get("mode") == "avoid_inside":
        for word in sorted(words, key=_word_sort_key):
            candidate = _rect_candidate(check, word)
            if candidate is not None:
                candidates.append(candidate)
        return candidates

    phrases = _text_phrases(check)
    for word in sorted(words, key=_word_sort_key):
        candidate = _rect_candidate(check, word)
        if candidate is not None:
            candidates.append(candidate)
    if not phrases:
        return candidates
    max_gap, max_center_delta = _phrase_tolerances(check)
    for phrase in phrases:
        for phrase_word in _group_phrase_words(
            words,
            phrase,
            max_gap=max_gap,
            max_center_delta=max_center_delta,
        ):
            candidate = _rect_candidate(check, phrase_word)
            if candidate is None:
                continue
            candidate["text_source"] = "text_phrases"
            candidate["phrase_id"] = phrase_word["phrase_id"]
            candidate["words"] = phrase_word["words"]
            candidates.append(candidate)
    return candidates


def text_boundary_clash_payload(
    pdf_path: Path,
    candidates: list[dict[str, Any]],
    *,
    checked: int,
) -> dict[str, Any]:
    fixture_dir = pdf_path.parent.parent
    fixture_name = fixture_dir.name or Path.cwd().name
    return {
        "schema": SCHEMA,
        "fixture": fixture_name,
        "render_pdf": f"build/{pdf_path.name}",
        "source": "spec.yaml:text_boundary_checks",
        "candidates": candidates,
        "checked": checked,
        "total": len(candidates),
    }


def _infer_spec_path(pdf_path: Path) -> Path:
    return pdf_path.parent.parent / "spec.yaml"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF text-boundary clash detector")
    parser.add_argument("pdf", type=Path, help="Compiled PDF path")
    parser.add_argument("--spec", type=Path, default=None, help="Fixture spec.yaml path")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Machine-readable report path",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="exit 1 when any boundary clash is found",
    )
    args = parser.parse_args()

    if not args.pdf.exists():
        raise FileNotFoundError(f"PDF not found: {args.pdf}")
    try:
        spec_path = args.spec or _infer_spec_path(args.pdf)
        checks = load_text_boundary_checks(spec_path)
        words, page_size_pt = extract_pdf_words_and_page(args.pdf)
        candidates = detect_text_boundary_clashes(words, page_size_pt, checks)
    except TextBoundaryClashError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    payload = text_boundary_clash_payload(args.pdf, candidates, checked=len(checks))
    if args.json_output is not None:
        _write_json(args.json_output, payload)

    if not candidates:
        print(f"OK: no text-boundary clashes found in {args.pdf.name} ({len(words)} words)")
        return 0

    for candidate in candidates:
        print(
            "WARN text_boundary: "
            f"{candidate['id']} kind={candidate['kind']} text=\"{candidate['text']}\" "
            f"boundary={candidate['boundary_id']}"
        )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
