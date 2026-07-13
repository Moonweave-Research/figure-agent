#!/usr/bin/env python3
"""Anchor-based layout drift check for fixtures with coordinate hints."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from check_visual_clash import extract_pdf_words_and_page  # noqa: E402
from inputs import parse_spec  # noqa: E402

DEFAULT_DRIFT_THRESHOLD = 0.05
LAYOUT_LANES_SCHEMA = "figure-agent.layout-lanes.v1"

LabelSpec = str | list[str]


@dataclass(frozen=True)
class DriftResult:
    label: str
    matched_form: str | None
    status: str
    ref_center: tuple[float, float] | None
    pdf_center: tuple[float, float] | None
    drift: float | None


@dataclass(frozen=True)
class LayoutLaneResult:
    """A declared text-group clearance result in page-normalized units."""

    rule_id: str
    status: str
    clearance: float | None
    minimum_clearance: float
    missing_groups: tuple[str, ...]


def _normalize_token(text: str) -> str:
    return text.strip(" \t\n\r.,;:()[]{}'\"!?+").lower()


def _tokens(text: str) -> list[str]:
    return [token for token in (_normalize_token(part) for part in text.split()) if token]


def _compact_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _label_forms(label: LabelSpec) -> list[str]:
    if isinstance(label, list):
        return [str(item) for item in label if str(item).strip()]
    return [str(label)]


def _center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    x0, y0, x1, y1 = bbox
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)


def _union_bbox(words: list[dict[str, Any]]) -> tuple[float, float, float, float]:
    bboxes = [_word_bbox(word) for word in words]
    return (
        min(bbox[0] for bbox in bboxes),
        min(bbox[1] for bbox in bboxes),
        max(bbox[2] for bbox in bboxes),
        max(bbox[3] for bbox in bboxes),
    )


def _word_bbox(word: dict[str, Any]) -> tuple[float, float, float, float]:
    if "bbox" in word and isinstance(word["bbox"], list | tuple) and len(word["bbox"]) == 4:
        return tuple(float(value) for value in word["bbox"])  # type: ignore[return-value]
    return (
        float(word["xmin"]),
        float(word["ymin"]),
        float(word["xmax"]),
        float(word["ymax"]),
    )


def _bbox_clearance(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    """Return Euclidean separation between two axis-aligned boxes in page units."""
    horizontal = max(first[0] - second[2], second[0] - first[2], 0.0)
    vertical = max(first[1] - second[3], second[1] - first[3], 0.0)
    return math.hypot(horizontal, vertical)


def _normalized_region_bbox(
    region: dict[str, Any],
    page_size: tuple[float, float],
) -> tuple[float, float, float, float]:
    bbox = region.get("normalized_bbox")
    if (
        not isinstance(bbox, list | tuple)
        or len(bbox) != 4
        or not all(isinstance(value, int | float) for value in bbox)
    ):
        raise ValueError("layout lane region requires normalized_bbox")
    x0, y0, x1, y1 = (float(value) for value in bbox)
    if not (0.0 <= x0 < x1 <= 1.0 and 0.0 <= y0 < y1 <= 1.0):
        raise ValueError("layout lane normalized_bbox must be ordered within [0, 1]")
    width, height = page_size
    return (x0 * width, y0 * height, x1 * width, y1 * height)


def _normalized_inset(
    inner: tuple[float, float, float, float],
    outer: tuple[float, float, float, float],
    page_size: tuple[float, float],
) -> float:
    width, height = page_size
    return min(
        (inner[0] - outer[0]) / width,
        (outer[2] - inner[2]) / width,
        (inner[1] - outer[1]) / height,
        (outer[3] - inner[3]) / height,
    )


def _group_bbox(
    group: dict[str, Any],
    words: list[dict[str, Any]],
) -> tuple[float, float, float, float] | None:
    terms = group.get("required_terms")
    if not isinstance(terms, list) or not terms:
        raise ValueError("layout lane label group requires non-empty required_terms")
    selected: list[dict[str, Any]] = []
    normalized_words = [_compact_text(str(word.get("text", ""))) for word in words]
    for term in terms:
        normalized_term = _compact_text(str(term))
        if not normalized_term:
            raise ValueError("layout lane required term is empty")
        try:
            index = normalized_words.index(normalized_term)
        except ValueError:
            return None
        selected.append(words[index])
    return _union_bbox(selected)


def evaluate_layout_lanes(
    contract: dict[str, Any],
    pdf_words: list[dict[str, Any]],
    pdf_page_size: tuple[float, float],
) -> list[LayoutLaneResult]:
    """Evaluate declared text-group clearance rules against the rendered PDF."""
    if contract.get("schema") != LAYOUT_LANES_SCHEMA:
        raise ValueError(f"expected {LAYOUT_LANES_SCHEMA}")
    raw_groups = contract.get("label_groups")
    raw_rules = contract.get("rules")
    if not isinstance(raw_groups, list) or not isinstance(raw_rules, list):
        raise ValueError("layout lane contract requires label_groups and rules lists")
    groups: dict[str, tuple[float, float, float, float] | None] = {}
    for group in raw_groups:
        if not isinstance(group, dict) or not isinstance(group.get("id"), str):
            raise ValueError("layout lane label group requires string id")
        group_id = group["id"]
        if group_id in groups:
            raise ValueError(f"duplicate layout lane label group: {group_id}")
        groups[group_id] = _group_bbox(group, pdf_words)

    page_diagonal = math.hypot(*pdf_page_size)
    if page_diagonal <= 0:
        raise ValueError("layout lane page size must be positive")
    raw_regions = contract.get("regions", [])
    if not isinstance(raw_regions, list):
        raise ValueError("layout lane regions must be a list")
    regions: dict[str, tuple[float, float, float, float]] = {}
    for region in raw_regions:
        if not isinstance(region, dict) or not isinstance(region.get("id"), str):
            raise ValueError("layout lane region requires string id")
        region_id = region["id"]
        if region_id in regions:
            raise ValueError(f"duplicate layout lane region: {region_id}")
        regions[region_id] = _normalized_region_bbox(region, pdf_page_size)

    results: list[LayoutLaneResult] = []
    for rule in raw_rules:
        if not isinstance(rule, dict):
            raise ValueError("layout lane rule must be an object")
        rule_id = rule.get("id")
        if not isinstance(rule_id, str):
            raise ValueError("layout lane rule is invalid")
        kind = rule.get("kind")
        if kind in {"contained_in_region", "minimum_clearance_from_region"}:
            group_id = rule.get("group")
            region_id = rule.get("region")
            minimum_key = (
                "minimum_normalized_inset"
                if kind == "contained_in_region"
                else "minimum_normalized_clearance"
            )
            minimum = rule.get(minimum_key)
            if (
                not isinstance(group_id, str)
                or not isinstance(region_id, str)
                or region_id not in regions
                or not isinstance(minimum, int | float)
                or float(minimum) < 0
            ):
                raise ValueError("layout lane region rule is invalid")
            if group_id not in groups or groups[group_id] is None:
                results.append(
                    LayoutLaneResult(
                        rule_id=rule_id,
                        status="missing_label_group",
                        clearance=None,
                        minimum_clearance=float(minimum),
                        missing_groups=(group_id,),
                    )
                )
                continue
            if kind == "contained_in_region":
                clearance = _normalized_inset(
                    groups[group_id], regions[region_id], pdf_page_size  # type: ignore[arg-type]
                )
            else:
                clearance = _bbox_clearance(
                    groups[group_id], regions[region_id]  # type: ignore[arg-type]
                ) / page_diagonal
            results.append(
                LayoutLaneResult(
                    rule_id=rule_id,
                    status="ok" if clearance >= float(minimum) else "violation",
                    clearance=round(clearance, 6),
                    minimum_clearance=float(minimum),
                    missing_groups=(),
                )
            )
            continue
        first_id = rule.get("first")
        second_id = rule.get("second")
        minimum = rule.get("minimum_normalized_clearance")
        if (
            kind != "minimum_clearance"
            or not isinstance(first_id, str)
            or not isinstance(second_id, str)
            or not isinstance(minimum, int | float)
            or float(minimum) < 0
        ):
            raise ValueError("layout lane rule is invalid")
        missing = tuple(
            group_id
            for group_id in (first_id, second_id)
            if group_id not in groups or groups[group_id] is None
        )
        if missing:
            results.append(
                LayoutLaneResult(
                    rule_id=rule_id,
                    status="missing_label_group",
                    clearance=None,
                    minimum_clearance=float(minimum),
                    missing_groups=missing,
                )
            )
            continue
        clearance = _bbox_clearance(groups[first_id], groups[second_id]) / page_diagonal  # type: ignore[arg-type]
        results.append(
            LayoutLaneResult(
                rule_id=rule_id,
                status="ok" if clearance >= float(minimum) else "violation",
                clearance=round(clearance, 6),
                minimum_clearance=float(minimum),
                missing_groups=(),
            )
        )
    return results


def layout_lane_payload(
    contract: dict[str, Any],
    pdf_words: list[dict[str, Any]],
    pdf_page_size: tuple[float, float],
) -> dict[str, Any]:
    results = evaluate_layout_lanes(contract, pdf_words, pdf_page_size)
    return {
        "schema": "figure-agent.layout-lane-report.v1",
        "contract_schema": LAYOUT_LANES_SCHEMA,
        "page_size_pt": list(pdf_page_size),
        "failure_count": sum(result.status != "ok" for result in results),
        "results": [
            {
                "rule_id": result.rule_id,
                "status": result.status,
                "clearance": result.clearance,
                "minimum_clearance": result.minimum_clearance,
                "missing_groups": list(result.missing_groups),
            }
            for result in results
        ],
    }


def _layout_lane_line(
    rule_id: str,
    status: str,
    clearance: float | None,
    minimum: float,
    missing_groups: tuple[str, ...] | list[str],
) -> str:
    if status == "ok":
        return f"OK layout lane {rule_id}: {clearance:.3f} >= {minimum:.3f}"
    if status == "violation":
        return f"WARN layout lane {rule_id}: {clearance:.3f} < {minimum:.3f}"
    return f"WARN layout lane {rule_id}: missing label groups {', '.join(missing_groups)}"


def _find_phrase_bbox(
    phrase: str,
    words: list[dict[str, Any]],
) -> tuple[float, float, float, float] | None:
    phrase_tokens = _tokens(phrase)
    if not phrase_tokens:
        return None
    normalized = [_normalize_token(str(word.get("text", ""))) for word in words]
    for index in range(0, len(words) - len(phrase_tokens) + 1):
        if normalized[index : index + len(phrase_tokens)] == phrase_tokens:
            return _union_bbox(words[index : index + len(phrase_tokens)])
    if len(phrase_tokens) == 1:
        token = phrase_tokens[0]
        for index, normalized_token in enumerate(normalized):
            if normalized_token == token:
                return _word_bbox(words[index])
    phrase_compact = _compact_text(phrase)
    if len(phrase_compact) >= 2:
        max_window = min(3, len(words))
        for window_size in range(1, max_window + 1):
            for index in range(0, len(words) - window_size + 1):
                window_words = words[index : index + window_size]
                window_text = "".join(str(word.get("text", "")) for word in window_words)
                if _compact_text(window_text) == phrase_compact:
                    return _union_bbox(window_words)
    return None


def _required_labels(spec: dict[str, Any]) -> list[LabelSpec]:
    contract = spec.get("golden_contract")
    if not isinstance(contract, dict):
        return []
    labels = contract.get("required_labels")
    if not isinstance(labels, list):
        return []
    return [label for label in labels if isinstance(label, str | list)]


def evaluate_drift(
    required_labels: list[LabelSpec],
    coordinate_hints: dict[str, Any],
    pdf_words: list[dict[str, Any]],
    pdf_page_size: tuple[float, float],
) -> list[DriftResult]:
    reference_size = coordinate_hints.get("reference_image_size") or []
    if not isinstance(reference_size, list | tuple) or len(reference_size) != 2:
        return []
    ref_width, ref_height = float(reference_size[0]), float(reference_size[1])
    pdf_width, pdf_height = pdf_page_size
    if min(ref_width, ref_height, pdf_width, pdf_height) <= 0:
        return []

    ref_words = coordinate_hints.get("text_labels") or []
    if not isinstance(ref_words, list):
        ref_words = []

    results: list[DriftResult] = []
    for label in required_labels:
        best: DriftResult | None = None
        for ref_form in _label_forms(label):
            ref_bbox = _find_phrase_bbox(ref_form, ref_words)
            if ref_bbox is None:
                continue
            ref_center_px = _center(ref_bbox)
            ref_center = (ref_center_px[0] / ref_width, ref_center_px[1] / ref_height)
            for pdf_form in _label_forms(label):
                pdf_bbox = _find_phrase_bbox(pdf_form, pdf_words)
                if pdf_bbox is None:
                    continue
                pdf_center_pt = _center(pdf_bbox)
                pdf_center = (pdf_center_pt[0] / pdf_width, pdf_center_pt[1] / pdf_height)
                drift = math.dist(ref_center, pdf_center)
                matched_form = ref_form if ref_form == pdf_form else f"{ref_form} -> {pdf_form}"
                candidate = DriftResult(
                    label=str(label),
                    matched_form=matched_form,
                    status="matched",
                    ref_center=ref_center,
                    pdf_center=pdf_center,
                    drift=drift,
                )
                if best is None or drift < (best.drift or math.inf):
                    best = candidate
        if best is not None:
            results.append(best)
            continue

        forms = _label_forms(label)
        has_ref = any(_find_phrase_bbox(form, ref_words) is not None for form in forms)
        has_pdf = any(_find_phrase_bbox(form, pdf_words) is not None for form in forms)
        if has_ref:
            status = "uncovered_build"
        elif has_pdf:
            status = "uncovered_ref"
        else:
            status = "uncovered_both"
        results.append(
            DriftResult(
                label=str(label),
                matched_form=None,
                status=status,
                ref_center=None,
                pdf_center=None,
                drift=None,
            )
        )
    return results


def _resolve_fixture_dir(target: str) -> Path:
    path = Path(target)
    if target == ".":
        return Path.cwd()
    if path.is_absolute():
        return path
    if len(path.parts) == 1:
        return Path("examples") / path.parts[0]
    if len(path.parts) == 2 and path.parts[0] == "examples":
        return path
    raise ValueError("expected fixture name, examples/<fixture>, absolute fixture path, or .")


def _fixture_name(fixture_dir: Path) -> str:
    return fixture_dir.resolve().name


def run_check(
    fixture_dir: Path,
    *,
    threshold: float = DEFAULT_DRIFT_THRESHOLD,
) -> tuple[int, list[str]]:
    name = _fixture_name(fixture_dir)
    spec_path = fixture_dir / "spec.yaml"
    hints_path = fixture_dir / "coordinate_hints.yaml"
    lanes_path = fixture_dir / "layout_lanes.yaml"
    pdf_path = fixture_dir / "build" / f"{name}.pdf"
    if not spec_path.is_file():
        return 1, [f"ERROR missing spec.yaml: {spec_path}"]
    spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    required_labels = _required_labels(spec)
    lines: list[str] = []
    failures = 0
    needs_pdf = hints_path.is_file() or lanes_path.is_file()
    if needs_pdf and not pdf_path.is_file():
        return 1, [f"ERROR missing build PDF: {pdf_path}"]
    pdf_words: list[dict[str, Any]] = []
    page_size: tuple[float, float] = (0.0, 0.0)
    if needs_pdf:
        pdf_words, page_size = extract_pdf_words_and_page(pdf_path)

    if not required_labels:
        lines.append(f"SKIP layout drift: no golden_contract.required_labels in {spec_path}")
    elif not hints_path.is_file():
        lines.append(f"SKIP layout drift: missing coordinate_hints.yaml in {fixture_dir}")
    else:
        hints = yaml.safe_load(hints_path.read_text(encoding="utf-8")) or {}
        if not isinstance(hints, dict):
            return 1, [f"ERROR invalid coordinate_hints.yaml: {hints_path}"]
        results = evaluate_drift(required_labels, hints, pdf_words, page_size)
        for result in results:
            if result.drift is not None:
                if result.drift > threshold:
                    failures += 1
                    lines.append(
                        f"WARN layout drift {result.label}: {result.drift:.3f} > {threshold:.3f}"
                    )
                else:
                    lines.append(f"OK layout drift {result.label}: {result.drift:.3f}")
            elif result.status != "uncovered_ref":
                failures += 1
                lines.append(f"WARN layout drift {result.label}: {result.status}")
            else:
                lines.append(f"SKIP layout drift {result.label}: {result.status}")
        if not results:
            lines.append("SKIP layout drift: no comparable labels")

    if lanes_path.is_file():
        lanes = yaml.safe_load(lanes_path.read_text(encoding="utf-8")) or {}
        if not isinstance(lanes, dict):
            return 1, [f"ERROR invalid layout_lanes.yaml: {lanes_path}"]
        for result in evaluate_layout_lanes(lanes, pdf_words, page_size):
            if result.status != "ok":
                failures += 1
            lines.append(
                _layout_lane_line(
                    result.rule_id,
                    result.status,
                    result.clearance,
                    result.minimum_clearance,
                    result.missing_groups,
                )
            )
    return failures, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "fixture",
        nargs="?",
        help="fixture name, examples/<fixture>, absolute fixture path, or .",
    )
    parser.add_argument("--threshold", type=float, default=DEFAULT_DRIFT_THRESHOLD)
    parser.add_argument(
        "--pdf",
        type=Path,
        help="rendered PDF for a direct layout-lane check",
    )
    parser.add_argument(
        "--layout-contract",
        type=Path,
        help="layout_lanes.yaml contract for a direct layout-lane check",
    )
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.pdf is not None or args.layout_contract is not None:
            if args.pdf is None or args.layout_contract is None:
                parser.error("--pdf and --layout-contract must be provided together")
            contract = yaml.safe_load(args.layout_contract.read_text(encoding="utf-8")) or {}
            if not isinstance(contract, dict):
                raise ValueError(f"invalid layout contract: {args.layout_contract}")
            words, page_size = extract_pdf_words_and_page(args.pdf)
            payload = layout_lane_payload(contract, words, page_size)
            failures = int(payload["failure_count"])
            lines = []
            for result in payload["results"]:
                lines.append(
                    _layout_lane_line(
                        str(result["rule_id"]),
                        str(result["status"]),
                        result["clearance"],
                        float(result["minimum_clearance"]),
                        list(result["missing_groups"]),
                    )
                )
            if args.json_output is not None:
                args.json_output.parent.mkdir(parents=True, exist_ok=True)
                args.json_output.write_text(
                    json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
        else:
            if args.fixture is None:
                parser.error("fixture is required unless --pdf and --layout-contract are used")
            failures, lines = run_check(
                _resolve_fixture_dir(args.fixture), threshold=args.threshold
            )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR layout drift: {exc}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 1 if args.strict and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
