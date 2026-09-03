#!/usr/bin/env python3
"""Detect rendered labels that are too close to declared semantic paths.

The checker is report-only by default. Pass --strict to return exit 1 when
any candidate is found, matching the collision/visual-clash strict contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__:
    from .check_visual_clash import extract_pdf_words_and_page
    from .phrase_binding import (
        NEAREST_WORD_LIMIT,
        allowlist_unmatched_failure,
        allowlist_word_unmatched_failure,
        binding_state,
        group_phrase_words,
        nearest_phrase_words,
        phrase_unmatched_failure,
        unbound_allowlist_words,
    )
else:  # Direct script execution keeps the checks directory on sys.path.
    from check_visual_clash import extract_pdf_words_and_page
    from phrase_binding import (
        NEAREST_WORD_LIMIT,
        allowlist_unmatched_failure,
        allowlist_word_unmatched_failure,
        binding_state,
        group_phrase_words,
        nearest_phrase_words,
        phrase_unmatched_failure,
        unbound_allowlist_words,
    )

SCHEMA = "figure-agent.label-path-proximity.v1"
CM_TO_PT = 72.0 / 2.54
DEFAULT_MAX_PHRASE_GAP_PT = 6.0
DEFAULT_MAX_PHRASE_Y_CENTER_DELTA_PT = 6.0
ALLOWED_DEFECT_KINDS = frozenset(
    {
        "label_stacked_on_reference_line",
        "label_curve_near_label",
        "label_path_near_miss",
    }
)


class LabelPathProximityError(ValueError):
    """Controlled error for malformed label-path proximity configuration."""


def _sha256_or_none(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _cm_to_pt(value: float | int) -> float:
    return round(float(value) * CM_TO_PT, 6)


def _non_negative_number(value: object, *, field: str) -> float:
    if not isinstance(value, int | float) or float(value) < 0:
        raise LabelPathProximityError(f"{field} must be a non-negative number")
    return float(value)


def _pdf_cm_range_to_pt(values: object, *, field: str) -> list[float]:
    if (
        not isinstance(values, list)
        or len(values) != 2
        or not all(isinstance(item, int | float) for item in values)
    ):
        raise LabelPathProximityError(f"{field} must be a two-number list")
    a = _cm_to_pt(values[0])
    b = _cm_to_pt(values[1])
    return [min(a, b), max(a, b)]


def _points_pdf_cm_to_pt(values: object, *, field: str) -> list[list[float]]:
    if not isinstance(values, list) or len(values) < 2:
        raise LabelPathProximityError(f"{field} must contain at least two points")
    points: list[list[float]] = []
    for index, raw_point in enumerate(values):
        if (
            not isinstance(raw_point, list)
            or len(raw_point) != 2
            or not all(isinstance(item, int | float) for item in raw_point)
        ):
            raise LabelPathProximityError(f"{field}[{index}] must be a two-number list")
        points.append([_cm_to_pt(raw_point[0]), _cm_to_pt(raw_point[1])])
    return points


def _text_allowlist(check: dict[str, Any]) -> set[str] | None:
    value = check.get("text_allowlist")
    if value is None:
        return None
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise LabelPathProximityError(
            f"{check['id']}.text_allowlist must be a non-empty string list"
        )
    return {item.strip() for item in value}


def _text_phrases(check: dict[str, Any]) -> list[dict[str, Any]]:
    value = check.get("text_phrases")
    if value is None:
        return []
    if not isinstance(value, list) or not value:
        raise LabelPathProximityError(f"{check['id']}.text_phrases must be a non-empty list")
    phrases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_phrase in enumerate(value):
        label = f"{check['id']}.text_phrases[{index}]"
        if not isinstance(raw_phrase, dict):
            raise LabelPathProximityError(f"{label} must be a mapping")
        phrase_id = raw_phrase.get("id")
        if not isinstance(phrase_id, str) or not phrase_id.strip():
            raise LabelPathProximityError(f"{label}.id must be a non-empty string")
        phrase_id = phrase_id.strip()
        if phrase_id in seen_ids:
            raise LabelPathProximityError(f"{check['id']}.text_phrases duplicate id: {phrase_id}")
        seen_ids.add(phrase_id)
        words = raw_phrase.get("words")
        if (
            not isinstance(words, list)
            or len(words) < 1
            or not all(isinstance(item, str) and item.strip() for item in words)
        ):
            raise LabelPathProximityError(f"{label}.words must contain at least one string")
        phrases.append({"id": phrase_id, "words": [item.strip() for item in words]})
    return phrases


def _source_binding(check: dict[str, Any]) -> dict[str, str] | None:
    value = check.get("source_binding")
    if value is None:
        return None
    if not isinstance(value, dict):
        raise LabelPathProximityError(f"{check['id']}.source_binding must be a mapping")
    source_name = value.get("source_name")
    selector = value.get("selector")
    if not isinstance(source_name, str) or not source_name.strip():
        raise LabelPathProximityError(
            f"{check['id']}.source_binding.source_name must be a non-empty string"
        )
    source_path = Path(source_name)
    if source_path.is_absolute() or ".." in source_path.parts:
        raise LabelPathProximityError(
            f"{check['id']}.source_binding.source_name must stay inside the fixture"
        )
    if not isinstance(selector, str) or not selector.strip():
        raise LabelPathProximityError(
            f"{check['id']}.source_binding.selector must be a non-empty string"
        )
    return {"source_name": source_name, "selector": selector}


def validate_live_bindings(
    checks: list[dict[str, Any]],
    *,
    spec_path: Path,
    words: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Fail closed when a declared path no longer has unique live source evidence.

    A detector declaration may retain geometry after its authored path or target label
    has moved.  Optional source bindings make that drift explicit without forcing a
    TikZ parser or an authoring primitive: the selector must occur exactly once in
    the current fixture source and every declared phrase must resolve in the render.
    """
    fixture_dir = spec_path.parent.resolve()
    failures: list[dict[str, str]] = []
    for check in sorted(checks, key=_check_sort_key):
        binding = _source_binding(check)
        if binding is None:
            continue
        source_path = (fixture_dir / binding["source_name"]).resolve()
        if fixture_dir not in source_path.parents or not source_path.is_file():
            failures.append(
                {
                    "check_id": str(check["id"]),
                    "kind": "source_missing",
                    "detail": binding["source_name"],
                }
            )
            continue
        source_text = source_path.read_text(encoding="utf-8")
        selector_count = source_text.count(binding["selector"])
        if selector_count != 1:
            failures.append(
                {
                    "check_id": str(check["id"]),
                    "kind": "source_selector_not_unique",
                    "detail": f"{binding['selector']} (matches={selector_count})",
                }
            )
        max_gap, max_center_delta = _phrase_tolerances(check)
        for phrase in _text_phrases(check):
            if not group_phrase_words(
                words,
                phrase,
                max_gap=max_gap,
                max_center_delta=max_center_delta,
            ):
                failures.append(
                    {
                        "check_id": str(check["id"]),
                        "kind": "rendered_phrase_missing",
                        "detail": " ".join(phrase["words"]),
                    }
                )
    return failures


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


def _check_sort_key(check: dict[str, Any]) -> tuple[str, str]:
    return (str(check.get("id", "")), str(check.get("kind", "")))


def load_label_path_proximity_checks(spec_path: Path | None) -> list[dict[str, Any]]:
    """Load optional spec.yaml label_path_proximity_checks."""
    if spec_path is None or not spec_path.is_file():
        return []
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise LabelPathProximityError(f"malformed spec.yaml: {exc}") from exc
    if spec is None:
        return []
    if not isinstance(spec, dict):
        raise LabelPathProximityError("spec.yaml must be a mapping")
    raw_checks = spec.get("label_path_proximity_checks")
    if raw_checks is None:
        return []
    if not isinstance(raw_checks, list):
        raise LabelPathProximityError("spec.yaml label_path_proximity_checks must be a list")
    checks: list[dict[str, Any]] = []
    for index, raw_check in enumerate(raw_checks):
        if not isinstance(raw_check, dict):
            raise LabelPathProximityError(f"label_path_proximity_checks[{index}] must be a mapping")
        check = dict(raw_check)
        check_id = check.get("id")
        check_kind = check.get("kind")
        role = check.get("role")
        if not isinstance(check_id, str) or not check_id.strip():
            raise LabelPathProximityError(f"label_path_proximity_checks[{index}].id is required")
        if check_kind not in {"horizontal_line", "vertical_line", "polyline"}:
            raise LabelPathProximityError(
                f"label_path_proximity_checks[{index}].kind must be "
                "horizontal_line, vertical_line, or polyline"
            )
        if not isinstance(role, str) or not role.strip():
            raise LabelPathProximityError(f"label_path_proximity_checks[{index}].role is required")
        _non_negative_number(
            check.get("clearance_pt"),
            field=f"label_path_proximity_checks[{index}].clearance_pt",
        )
        defect_kind = check.get("defect_kind")
        if defect_kind is not None and defect_kind not in ALLOWED_DEFECT_KINDS:
            raise LabelPathProximityError(
                f"label_path_proximity_checks[{index}].defect_kind must be one of "
                + ", ".join(sorted(ALLOWED_DEFECT_KINDS))
            )
        _source_binding(check)
        checks.append(check)
    return checks


def authoring_context(checks: list[dict[str, Any]]) -> dict[str, Any]:
    """Compile detector declarations into deterministic pre-generation guidance."""

    def number(value: float | int) -> str:
        return f"{float(value):g}"

    def geometry(check: dict[str, Any]) -> str:
        if check["kind"] == "horizontal_line":
            x0, x1 = check["x_range_pdf_cm"]
            return (
                f"PDF-cm horizontal line y={number(check['y_pdf_cm'])}, "
                f"x=[{number(x0)}, {number(x1)}]"
            )
        if check["kind"] == "vertical_line":
            y0, y1 = check["y_range_pdf_cm"]
            return (
                f"PDF-cm vertical line x={number(check['x_pdf_cm'])}, "
                f"y=[{number(y0)}, {number(y1)}]"
            )
        points = ", ".join(f"({number(x)}, {number(y)})" for x, y in check["points_pdf_cm"])
        return f"PDF-cm polyline [{points}]"

    directives: list[str] = []
    for check in sorted(checks, key=_check_sort_key):
        _path_segments(check)
        clearance = _non_negative_number(
            check.get("clearance_pt"), field=f"{check['id']}.clearance_pt"
        )
        path = f"declared path [{check['id']}] ({check['role']}; {geometry(check)})"
        phrases = _text_phrases(check)
        allowlist = _text_allowlist(check)
        for phrase in phrases:
            directives.append(
                f"Keep text phrase [{' '.join(phrase['words'])}] at least "
                f"{clearance:g} pt clear of {path}."
            )
        if allowlist is not None:
            for label in sorted(allowlist):
                directives.append(
                    f"Keep text label [{label}] at least {clearance:g} pt clear of {path}."
                )
        if not phrases and allowlist is None:
            directives.append(f"Keep all rendered text at least {clearance:g} pt clear of {path}.")
    return {
        "schema": SCHEMA,
        "checks": checks,
        "authoring_directives": directives,
    }


def _selected_words(check: dict[str, Any], words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    allowlist = _text_allowlist(check)
    phrases = _text_phrases(check)
    if allowlist is not None:
        for word in sorted(words, key=_word_sort_key):
            if str(word.get("text", "")).strip() in allowlist:
                selected.append(word)
    if phrases:
        max_gap, max_center_delta = _phrase_tolerances(check)
        for phrase in phrases:
            selected.extend(
                group_phrase_words(
                    words,
                    phrase,
                    max_gap=max_gap,
                    max_center_delta=max_center_delta,
                )
            )
    if allowlist is None and not phrases:
        selected.extend(sorted(words, key=_word_sort_key))
    return selected


def _point_rect_distance(x: float, y: float, rect: tuple[float, float, float, float]) -> float:
    x1, y1, x2, y2 = rect
    dx = max(x1 - x, 0.0, x - x2)
    dy = max(y1 - y, 0.0, y - y2)
    return math.hypot(dx, dy)


def _point_segment_distance(
    px: float,
    py: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
) -> float:
    abx = bx - ax
    aby = by - ay
    denom = abx * abx + aby * aby
    if denom == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / denom))
    cx = ax + t * abx
    cy = ay + t * aby
    return math.hypot(px - cx, py - cy)


def _orientation(ax: float, ay: float, bx: float, by: float, cx: float, cy: float) -> float:
    return (by - ay) * (cx - bx) - (bx - ax) * (cy - by)


def _on_segment(ax: float, ay: float, bx: float, by: float, cx: float, cy: float) -> bool:
    return min(ax, cx) <= bx <= max(ax, cx) and min(ay, cy) <= by <= max(ay, cy)


def _segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    ax, ay = a
    bx, by = b
    cx, cy = c
    dx, dy = d
    o1 = _orientation(ax, ay, bx, by, cx, cy)
    o2 = _orientation(ax, ay, bx, by, dx, dy)
    o3 = _orientation(cx, cy, dx, dy, ax, ay)
    o4 = _orientation(cx, cy, dx, dy, bx, by)
    if o1 == 0 and _on_segment(ax, ay, cx, cy, bx, by):
        return True
    if o2 == 0 and _on_segment(ax, ay, dx, dy, bx, by):
        return True
    if o3 == 0 and _on_segment(cx, cy, ax, ay, dx, dy):
        return True
    if o4 == 0 and _on_segment(cx, cy, bx, by, dx, dy):
        return True
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def _segment_rect_distance(
    ax: float,
    ay: float,
    bx: float,
    by: float,
    rect: tuple[float, float, float, float],
) -> float:
    x1, y1, x2, y2 = rect
    if (x1 <= ax <= x2 and y1 <= ay <= y2) or (x1 <= bx <= x2 and y1 <= by <= y2):
        return 0.0
    edges = (
        ((x1, y1), (x2, y1)),
        ((x2, y1), (x2, y2)),
        ((x2, y2), (x1, y2)),
        ((x1, y2), (x1, y1)),
    )
    for edge_start, edge_end in edges:
        if _segments_intersect((ax, ay), (bx, by), edge_start, edge_end):
            return 0.0
    corner_distances = [
        _point_segment_distance(x, y, ax, ay, bx, by)
        for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2))
    ]
    endpoint_distances = [_point_rect_distance(ax, ay, rect), _point_rect_distance(bx, by, rect)]
    return min(corner_distances + endpoint_distances)


def _path_segments(check: dict[str, Any]) -> tuple[list[tuple[float, float, float, float]], dict]:
    if check["kind"] == "horizontal_line":
        if not isinstance(check.get("y_pdf_cm"), int | float):
            raise LabelPathProximityError(f"{check['id']}.y_pdf_cm must be a number")
        x_range = _pdf_cm_range_to_pt(
            check.get("x_range_pdf_cm"),
            field=f"{check['id']}.x_range_pdf_cm",
        )
        y = _cm_to_pt(check["y_pdf_cm"])
        return [(x_range[0], y, x_range[1], y)], {
            "kind": "horizontal_line",
            "y": round(y, 6),
            "x_range": x_range,
        }
    if check["kind"] == "vertical_line":
        if not isinstance(check.get("x_pdf_cm"), int | float):
            raise LabelPathProximityError(f"{check['id']}.x_pdf_cm must be a number")
        y_range = _pdf_cm_range_to_pt(
            check.get("y_range_pdf_cm"),
            field=f"{check['id']}.y_range_pdf_cm",
        )
        x = _cm_to_pt(check["x_pdf_cm"])
        return [(x, y_range[0], x, y_range[1])], {
            "kind": "vertical_line",
            "x": round(x, 6),
            "y_range": y_range,
        }
    points = _points_pdf_cm_to_pt(
        check.get("points_pdf_cm"),
        field=f"{check['id']}.points_pdf_cm",
    )
    segments = [(left[0], left[1], right[0], right[1]) for left, right in zip(points, points[1:])]
    return segments, {"kind": "polyline", "points": points}


def _candidate_kind(check: dict[str, Any]) -> str:
    defect_kind = check.get("defect_kind")
    if isinstance(defect_kind, str) and defect_kind in ALLOWED_DEFECT_KINDS:
        return defect_kind
    if check["kind"] == "polyline":
        return "label_curve_near_label"
    if check["kind"] == "horizontal_line" and "reference" in str(check.get("role", "")):
        return "label_stacked_on_reference_line"
    return "label_path_near_miss"


def _candidate_for_word(
    check: dict[str, Any],
    word: dict[str, Any],
    *,
    segments: list[tuple[float, float, float, float]],
    path_pt: dict,
) -> dict[str, Any] | None:
    clearance = float(check.get("clearance_pt", 0.0))
    bbox = tuple(_word_bbox(word))
    distance = min(_segment_rect_distance(ax, ay, bx, by, bbox) for ax, ay, bx, by in segments)
    if distance > clearance:
        return None
    candidate = {
        "id": "",
        "kind": _candidate_kind(check),
        "text": str(word.get("text", "")),
        "path_id": str(check["id"]),
        "path_role": str(check["role"]),
        "bbox_pt": list(bbox),
        "path_pt": path_pt,
        "clearance_pt": round(clearance, 6),
        "distance_pt": round(distance, 6),
    }
    for field in ("text_source", "phrase_id", "words"):
        if field in word:
            candidate[field] = word[field]
    return candidate


def detect_label_path_proximity(
    words: list[dict[str, Any]],
    page_size_pt: tuple[float, float],
    checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return deterministic label-path proximity candidates."""
    _ = page_size_pt
    candidates: list[dict[str, Any]] = []
    for check in sorted(checks, key=_check_sort_key):
        segments, path_pt = _path_segments(check)
        for word in _selected_words(check, words):
            candidate = _candidate_for_word(check, word, segments=segments, path_pt=path_pt)
            if candidate is not None:
                candidates.append(candidate)
    candidates.sort(
        key=lambda item: (
            str(item.get("path_id", "")),
            float(item.get("bbox_pt", [0, 0, 0, 0])[1]),
            float(item.get("bbox_pt", [0, 0, 0, 0])[0]),
            str(item.get("text", "")),
        )
    )
    for index, candidate in enumerate(candidates, start=1):
        candidate["id"] = f"LP{index:03d}"
    return candidates


def phrase_binding_failures(
    checks: list[dict[str, Any]],
    words: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Report every declared phrase that binds no rendered text.

    A phrase that matches nothing selects no words, so the proximity measure
    never runs and the checker used to print OK.  The declaration is then a
    dead check, so it fails here instead of passing silently.
    """
    failures: list[dict[str, Any]] = []
    for check in sorted(checks, key=_check_sort_key):
        max_gap, max_center_delta = _phrase_tolerances(check)
        for phrase in _text_phrases(check):
            if group_phrase_words(
                words,
                phrase,
                max_gap=max_gap,
                max_center_delta=max_center_delta,
            ):
                continue
            failures.append(
                phrase_unmatched_failure(
                    str(check["id"]),
                    phrase,
                    nearest_phrase_words(
                        words,
                        phrase,
                        max_gap=max_gap,
                        max_center_delta=max_center_delta,
                    ),
                )
            )
    return failures


def declared_phrase_count(checks: list[dict[str, Any]]) -> int:
    return sum(len(_text_phrases(check)) for check in checks)


def _nearest_rendered_words(
    check: dict[str, Any],
    words: list[dict[str, Any]],
    *,
    limit: int = NEAREST_WORD_LIMIT,
) -> list[str]:
    """Name the words the render actually draws nearest the declared path."""
    segments, _ = _path_segments(check)
    ranked = sorted(
        (
            min(
                _segment_rect_distance(ax, ay, bx, by, tuple(_word_bbox(word)))
                for ax, ay, bx, by in segments
            ),
            _word_sort_key(word),
            str(word.get("text", "")).strip(),
        )
        for word in words
    )
    return [text for _, _, text in ranked[:limit]]


def allowlist_binding_failures(
    checks: list[dict[str, Any]],
    words: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Report every declared allowlist word that names no rendered word.

    An allowlist selects only the words it names, so one that names nothing the
    render draws selects nothing: the proximity measure never runs and the
    checker used to print OK.  Resolving the list as a whole hid the same
    defect one word at a time — a word the render never draws stopped selecting
    anything while its neighbours kept the list alive — so each declared word
    has to bind on its own.
    """
    failures: list[dict[str, Any]] = []
    for check in sorted(checks, key=_check_sort_key):
        allowlist = _text_allowlist(check)
        if allowlist is None:
            continue
        unbound = unbound_allowlist_words(words, allowlist)
        if not unbound:
            continue
        nearest = _nearest_rendered_words(check, words)
        if len(unbound) == len(allowlist):
            failures.append(allowlist_unmatched_failure(str(check["id"]), allowlist, nearest))
            continue
        failures.append(allowlist_word_unmatched_failure(str(check["id"]), unbound, nearest))
    return failures


def declared_allowlist_count(checks: list[dict[str, Any]]) -> int:
    return sum(1 for check in checks if _text_allowlist(check) is not None)


def label_path_proximity_payload(
    pdf_path: Path,
    candidates: list[dict[str, Any]],
    *,
    checked: int,
    live_binding_checked: int = 0,
    live_binding_failures: list[dict[str, str]] | None = None,
    phrase_binding_checked: int = 0,
    phrase_binding_failures: list[dict[str, Any]] | None = None,
    allowlist_binding_checked: int = 0,
    allowlist_binding_failures: list[dict[str, Any]] | None = None,
    spec_path: Path | None = None,
) -> dict[str, Any]:
    fixture_dir = pdf_path.parent.parent
    fixture_name = fixture_dir.name or Path.cwd().name
    binding_failures = list(live_binding_failures or [])
    unmatched_phrases = list(phrase_binding_failures or [])
    unmatched_allowlists = list(allowlist_binding_failures or [])
    resolved_spec_path = spec_path or _infer_spec_path(pdf_path)
    return {
        "schema": SCHEMA,
        "compile_run_id": os.environ.get("FIGURE_AGENT_COMPILE_RUN_ID"),
        "fixture": fixture_name,
        "render_pdf": f"build/{pdf_path.name}",
        "render_pdf_sha256": _sha256_or_none(pdf_path),
        "spec_sha256": _sha256_or_none(resolved_spec_path),
        "source": "spec.yaml:label_path_proximity_checks",
        "candidates": candidates,
        "checked": checked,
        "phrase_binding": {
            "checked": phrase_binding_checked,
            "state": binding_state(phrase_binding_checked, unmatched_phrases),
            "failures": unmatched_phrases,
        },
        "allowlist_binding": {
            "checked": allowlist_binding_checked,
            "state": binding_state(allowlist_binding_checked, unmatched_allowlists),
            "failures": unmatched_allowlists,
        },
        "live_binding": {
            "checked": live_binding_checked,
            "state": (
                "failed"
                if binding_failures
                else "passed"
                if live_binding_checked
                else "not_declared"
            ),
            "failures": binding_failures,
        },
        "total": len(candidates),
    }


def _infer_spec_path(pdf_path: Path) -> Path:
    return pdf_path.parent.parent / "spec.yaml"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF label-path proximity detector")
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
        help="exit 1 when any label-path proximity candidate is found",
    )
    args = parser.parse_args()

    if not args.pdf.exists():
        raise FileNotFoundError(f"PDF not found: {args.pdf}")
    try:
        spec_path = args.spec or _infer_spec_path(args.pdf)
        checks = load_label_path_proximity_checks(spec_path)
        words, page_size_pt = extract_pdf_words_and_page(args.pdf)
        binding_failures = validate_live_bindings(
            checks,
            spec_path=spec_path,
            words=words,
        )
        unmatched_phrases = phrase_binding_failures(checks, words)
        phrase_count = declared_phrase_count(checks)
        unmatched_allowlists = allowlist_binding_failures(checks, words)
        allowlist_count = declared_allowlist_count(checks)
        candidates = detect_label_path_proximity(words, page_size_pt, checks)
    except LabelPathProximityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    live_binding_checked = sum(1 for check in checks if _source_binding(check) is not None)
    payload = label_path_proximity_payload(
        args.pdf,
        candidates,
        checked=len(checks),
        live_binding_checked=live_binding_checked,
        live_binding_failures=binding_failures,
        phrase_binding_checked=phrase_count,
        phrase_binding_failures=unmatched_phrases,
        allowlist_binding_checked=allowlist_count,
        allowlist_binding_failures=unmatched_allowlists,
        spec_path=spec_path,
    )
    if args.json_output is not None:
        _write_json(args.json_output, payload)

    if unmatched_phrases:
        for failure in unmatched_phrases:
            print(
                "ERROR label_path_phrase: "
                f"{failure['check_id']}.{failure['phrase_id']} {failure['kind']} "
                f"({failure['detail']})",
                file=sys.stderr,
            )

    if unmatched_allowlists:
        for failure in unmatched_allowlists:
            print(
                "ERROR label_path_allowlist: "
                f"{failure['check_id']} {failure['kind']} ({failure['detail']})",
                file=sys.stderr,
            )

    if binding_failures:
        for failure in binding_failures:
            print(
                "ERROR label_path_binding: "
                f"{failure['check_id']} {failure['kind']} ({failure['detail']})",
                file=sys.stderr,
            )

    if binding_failures or unmatched_phrases or unmatched_allowlists:
        return 2

    if not candidates:
        print(
            f"OK: no label-path proximity candidates found in {args.pdf.name} ({len(words)} words)"
        )
        return 0

    for candidate in candidates:
        print(
            "WARN label_path_proximity: "
            f'{candidate["id"]} kind={candidate["kind"]} text="{candidate["text"]}" '
            f"path={candidate['path_id']} distance_pt={candidate['distance_pt']}"
        )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
