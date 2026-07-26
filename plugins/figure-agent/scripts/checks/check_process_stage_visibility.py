#!/usr/bin/env python3
"""Verify that declared process stages remain visible and ordered in a rendered panel.

Fixtures opt in with ``process_stage_visibility_checks`` in ``spec.yaml``.
The checker does not prescribe geometry or a drawing primitive.  It only requires
that each scientific stage has a rendered text anchor inside its declared panel,
and that the anchors retain the declared reading order.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

if __package__:
    from .check_visual_clash import extract_pdf_words_and_page
else:  # Direct script execution keeps the checks directory on sys.path.
    from check_visual_clash import extract_pdf_words_and_page

SCHEMA = "figure-agent.process-stage-visibility.v1"
CM_TO_PT = 72.0 / 2.54
DEFAULT_MAX_PHRASE_GAP_PT = 7.0
DEFAULT_MAX_PHRASE_Y_CENTER_DELTA_PT = 6.0


class ProcessStageVisibilityError(ValueError):
    """Raised when a fixture's stage-visibility declaration is malformed."""


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _cm_to_pt(value: float | int) -> float:
    return round(float(value) * CM_TO_PT, 6)


def _bbox_from_pdf_cm(
    values: object,
    *,
    page_height_pt: float,
    field: str,
) -> list[float]:
    if (
        not isinstance(values, list)
        or len(values) != 4
        or not all(isinstance(value, int | float) for value in values)
    ):
        raise ProcessStageVisibilityError(f"{field} must be a four-number list")
    x1, y1, x2, y2 = (_cm_to_pt(value) for value in values)
    return [
        min(x1, x2),
        min(page_height_pt - y1, page_height_pt - y2),
        max(x1, x2),
        max(page_height_pt - y1, page_height_pt - y2),
    ]


def _word_key(word: dict[str, Any]) -> tuple[float, float, str]:
    return (float(word["ymin"]), float(word["xmin"]), str(word.get("text", "")))


def _center(word: dict[str, Any], axis: str) -> float:
    return (float(word[f"{axis}min"]) + float(word[f"{axis}max"])) / 2.0


def _leading_edge(box: dict[str, Any], axis: str) -> float:
    """Return the reader-facing anchor edge for an ordered stage label.

    A stage may deliberately contain a long explanatory phrase.  Its visual
    start, rather than the center of all its explanatory words, is what carries
    reading order; otherwise a legitimate long label can falsely appear after
    the following compact stage label.
    """
    return float(box[f"{axis}min"])


def _word_inside_panel(word: dict[str, Any], panel_bbox: list[float]) -> bool:
    return (
        float(word["xmin"]) >= panel_bbox[0]
        and float(word["ymin"]) >= panel_bbox[1]
        and float(word["xmax"]) <= panel_bbox[2]
        and float(word["ymax"]) <= panel_bbox[3]
    )


def _phrase_bbox(words: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "xmin": min(float(word["xmin"]) for word in words),
        "ymin": min(float(word["ymin"]) for word in words),
        "xmax": max(float(word["xmax"]) for word in words),
        "ymax": max(float(word["ymax"]) for word in words),
    }


def _find_phrase(
    words: list[dict[str, Any]],
    phrase_words: list[str],
) -> list[dict[str, Any]]:
    ordered = sorted(words, key=_word_key)
    matches: list[dict[str, Any]] = []
    for index, first in enumerate(ordered):
        if str(first.get("text", "")).strip() != phrase_words[0]:
            continue
        span = [first]
        cursor = index + 1
        for expected in phrase_words[1:]:
            previous = span[-1]
            next_word: dict[str, Any] | None = None
            for candidate in ordered[cursor:]:
                if float(candidate["xmin"]) < float(previous["xmax"]):
                    continue
                if float(candidate["xmin"]) - float(previous["xmax"]) > DEFAULT_MAX_PHRASE_GAP_PT:
                    break
                same_line = abs(_center(candidate, "y") - _center(previous, "y")) <= (
                    DEFAULT_MAX_PHRASE_Y_CENTER_DELTA_PT
                )
                if str(candidate.get("text", "")).strip() == expected and same_line:
                    next_word = candidate
                    break
            if next_word is None:
                break
            span.append(next_word)
            cursor = ordered.index(next_word) + 1
        if len(span) == len(phrase_words):
            matches.append(_phrase_bbox(span))
    return matches


def _parse_phrase(raw: object, *, field: str) -> dict[str, Any]:
    if not isinstance(raw, dict) or not _nonempty(raw.get("id")):
        raise ProcessStageVisibilityError(f"{field}.id is required")
    words = raw.get("words")
    if (
        not isinstance(words, list)
        or not words
        or not all(_nonempty(value) for value in words)
    ):
        raise ProcessStageVisibilityError(f"{field}.words must be a non-empty string list")
    return {"id": raw["id"].strip(), "words": [value.strip() for value in words]}


def load_process_stage_visibility_checks(
    spec_path: Path | None,
    *,
    page_size_pt: tuple[float, float],
) -> tuple[dict[str, list[float]], list[dict[str, Any]]]:
    if spec_path is None or not spec_path.is_file():
        return {}, []
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ProcessStageVisibilityError(f"malformed spec.yaml: {exc}") from exc
    if not isinstance(spec, dict):
        raise ProcessStageVisibilityError("spec.yaml must be a mapping")

    panels: dict[str, list[float]] = {}
    for index, panel in enumerate(spec.get("panels", [])):
        if not isinstance(panel, dict) or not _nonempty(panel.get("id")):
            raise ProcessStageVisibilityError(f"panels[{index}].id is required")
        panel_id = panel["id"].strip()
        if panel_id in panels:
            raise ProcessStageVisibilityError("duplicate panel id")
        panels[panel_id] = _bbox_from_pdf_cm(
            panel.get("bbox_pdf_cm"),
            page_height_pt=page_size_pt[1],
            field=f"panels[{index}].bbox_pdf_cm",
        )

    raw_checks = spec.get("process_stage_visibility_checks")
    if raw_checks is None:
        return panels, []
    if not isinstance(raw_checks, list):
        raise ProcessStageVisibilityError("process_stage_visibility_checks must be a list")

    checks: list[dict[str, Any]] = []
    seen_checks: set[str] = set()
    for index, raw in enumerate(raw_checks):
        field = f"process_stage_visibility_checks[{index}]"
        if not isinstance(raw, dict) or not _nonempty(raw.get("id")):
            raise ProcessStageVisibilityError(f"{field}.id is required")
        check_id = raw["id"].strip()
        if check_id in seen_checks:
            raise ProcessStageVisibilityError("duplicate process stage check id")
        seen_checks.add(check_id)
        panel_id = raw.get("panel_id")
        if not _nonempty(panel_id) or panel_id.strip() not in panels:
            raise ProcessStageVisibilityError(f"{field}.panel_id must name a declared panel")
        axis = raw.get("reading_axis")
        if axis not in {"x", "y"}:
            raise ProcessStageVisibilityError(f"{field}.reading_axis must be x or y")
        separation = raw.get("minimum_stage_separation_pt", 0.0)
        if not isinstance(separation, int | float) or float(separation) < 0.0:
            raise ProcessStageVisibilityError(
                f"{field}.minimum_stage_separation_pt must be non-negative"
            )
        raw_stages = raw.get("stages")
        if not isinstance(raw_stages, list) or len(raw_stages) < 2:
            raise ProcessStageVisibilityError(f"{field}.stages must contain at least two stages")
        stages: list[dict[str, Any]] = []
        seen_stages: set[str] = set()
        for stage_index, stage in enumerate(raw_stages):
            stage_field = f"{field}.stages[{stage_index}]"
            if not isinstance(stage, dict) or not _nonempty(stage.get("id")):
                raise ProcessStageVisibilityError(f"{stage_field}.id is required")
            stage_id = stage["id"].strip()
            if stage_id in seen_stages:
                raise ProcessStageVisibilityError("duplicate stage id")
            seen_stages.add(stage_id)
            raw_phrases = stage.get("text_phrases")
            if not isinstance(raw_phrases, list) or not raw_phrases:
                raise ProcessStageVisibilityError(f"{stage_field}.text_phrases is required")
            stages.append(
                {
                    "id": stage_id,
                    "text_phrases": [
                        _parse_phrase(phrase, field=f"{stage_field}.text_phrases[{phrase_index}]")
                        for phrase_index, phrase in enumerate(raw_phrases)
                    ],
                }
            )
        checks.append(
            {
                "id": check_id,
                "panel_id": panel_id.strip(),
                "reading_axis": axis,
                "minimum_stage_separation_pt": float(separation),
                "stages": stages,
            }
        )
    return panels, checks


def detect_process_stage_visibility(
    words: list[dict[str, Any]],
    *,
    page_size_pt: tuple[float, float],
    panel_bboxes: dict[str, list[float]],
    checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    _ = page_size_pt
    candidates: list[dict[str, Any]] = []
    for check in checks:
        panel_id = check["panel_id"]
        panel_words = [word for word in words if _word_inside_panel(word, panel_bboxes[panel_id])]
        stage_anchors: dict[str, dict[str, Any]] = {}
        for stage in check["stages"]:
            matches: list[dict[str, Any]] = []
            missing_phrase_ids: list[str] = []
            for phrase in stage["text_phrases"]:
                phrase_matches = _find_phrase(panel_words, phrase["words"])
                if not phrase_matches:
                    missing_phrase_ids.append(phrase["id"])
                else:
                    matches.extend(phrase_matches)
            if missing_phrase_ids:
                candidates.append(
                    {
                        "id": "",
                        "kind": "process_stage_anchor_missing",
                        "check_id": check["id"],
                        "panel_id": panel_id,
                        "stage_id": stage["id"],
                        "required_phrase_ids": missing_phrase_ids,
                    }
                )
                continue
            stage_anchors[stage["id"]] = _phrase_bbox(matches)
        for before, after in zip(check["stages"], check["stages"][1:]):
            before_anchor = stage_anchors.get(before["id"])
            after_anchor = stage_anchors.get(after["id"])
            if before_anchor is None or after_anchor is None:
                continue
            distance = _leading_edge(after_anchor, check["reading_axis"]) - _leading_edge(
                before_anchor, check["reading_axis"]
            )
            if distance < check["minimum_stage_separation_pt"]:
                candidates.append(
                    {
                        "id": "",
                        "kind": "process_stage_order_invalid",
                        "check_id": check["id"],
                        "panel_id": panel_id,
                        "before_stage_id": before["id"],
                        "after_stage_id": after["id"],
                        "reading_axis": check["reading_axis"],
                        "observed_separation_pt": round(distance, 6),
                        "minimum_stage_separation_pt": check["minimum_stage_separation_pt"],
                    }
                )
    for index, candidate in enumerate(candidates, start=1):
        candidate["id"] = f"PS{index:03d}"
    return candidates


def process_stage_visibility_payload(
    pdf_path: Path,
    candidates: list[dict[str, Any]],
    *,
    checked: int,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": pdf_path.resolve().parent.parent.name,
        "render_pdf": f"build/{pdf_path.name}",
        "source": "spec.yaml:process_stage_visibility_checks",
        "checked": checked,
        "total": len(candidates),
        "candidates": candidates,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        words, page_size_pt = extract_pdf_words_and_page(args.pdf)
        panel_bboxes, checks = load_process_stage_visibility_checks(
            args.spec or args.pdf.parent.parent / "spec.yaml",
            page_size_pt=page_size_pt,
        )
        candidates = detect_process_stage_visibility(
            words,
            page_size_pt=page_size_pt,
            panel_bboxes=panel_bboxes,
            checks=checks,
        )
    except ProcessStageVisibilityError as exc:
        print(f"ERROR process_stage_visibility: {exc}")
        return 2
    payload = process_stage_visibility_payload(args.pdf, candidates, checked=len(checks))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for candidate in candidates:
        print(
            "WARN process_stage_visibility: "
            f"{candidate['id']} kind={candidate['kind']} panel={candidate['panel_id']}"
        )
    return 1 if args.strict and candidates else 0


if __name__ == "__main__":
    raise SystemExit(main())
