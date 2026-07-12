#!/usr/bin/env python3
"""Declared vector-to-vector clearance checks.

G1 is declaration-gated only: this module never discovers a topology defect on
its own. It verifies `vector_clearance_checks` authored in spec.yaml and reports
selector failures or declared relation violations.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "figure-agent.vector-clearance.v1"
CM_TO_PT = 72.0 / 2.54
TOUCH_TOLERANCE_CM = 0.01
SELECTOR_BBOX_TOLERANCE_CM = 0.015
MARKER_RADIUS_MAX_CM = 0.12

_POINT_RE = r"\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)"
_OPERATION_RE = re.compile(
    r"\\(?P<command>draw|fill|shade)(?:\[(?P<options>[^\]]*)\])?(?P<body>.*?);",
    re.DOTALL,
)
_FOREACH_PAIR_RE = re.compile(
    r"\\foreach\s+\\(?P<xvar>[A-Za-z]\w*)\s*/\s*\\(?P<yvar>[A-Za-z]\w*)"
    r"\s+in\s*\{(?P<pairs>[^}]*)\}\s*\{(?P<body>.*?)\}",
    re.DOTALL,
)
_SEGMENT_RE = re.compile(rf"{_POINT_RE}\s*--\s*{_POINT_RE}")
_RECT_RE = re.compile(rf"{_POINT_RE}\s*rectangle\s*{_POINT_RE}")
_CIRCLE_RE = re.compile(rf"{_POINT_RE}\s*circle\s*\(\s*(-?\d+(?:\.\d+)?)(cm|mm|pt)?\s*\)")
_BEZIER_RE = re.compile(
    rf"{_POINT_RE}\s*\.\.\s*controls\s*{_POINT_RE}\s*and\s*{_POINT_RE}\s*\.\.\s*{_POINT_RE}",
    re.DOTALL,
)


class VectorClearanceError(ValueError):
    """Raised when vector clearance declarations or evidence are malformed."""


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _cm_to_pt(value: float) -> float:
    return value * CM_TO_PT


def _pt_to_cm(value: float) -> float:
    return value / CM_TO_PT


def _radius_cm(value: float, unit: str | None) -> float:
    if unit == "pt":
        return _pt_to_cm(value)
    if unit == "mm":
        return value / 10.0
    return value


def _bbox(points: list[tuple[float, float]]) -> list[float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def _iter_operations(tex_text: str) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for match in _OPERATION_RE.finditer(tex_text):
        prefix = tex_text[: match.start()]
        start_line = prefix.count("\n") + 1
        line_start = prefix.rfind("\n") + 1
        if tex_text[line_start : match.start()].lstrip().startswith("%"):
            continue
        operations.append(
            {
                "text": match.group(0),
                "source_line": start_line,
                "command": str(match.group("command") or ""),
                "options": str(match.group("options") or ""),
            }
        )
    operations.extend(_iter_expanded_foreach_operations(tex_text))
    operations.sort(key=lambda operation: int(operation["source_line"]))
    return operations


def _iter_expanded_foreach_operations(tex_text: str) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for foreach_match in _FOREACH_PAIR_RE.finditer(tex_text):
        xvar = str(foreach_match.group("xvar"))
        yvar = str(foreach_match.group("yvar"))
        body = str(foreach_match.group("body") or "")
        pairs = _parse_foreach_pairs(str(foreach_match.group("pairs") or ""))
        body_start = foreach_match.start("body")
        for x_value, y_value in pairs:
            expanded_body = body.replace(f"\\{xvar}", x_value).replace(f"\\{yvar}", y_value)
            for operation_match in _OPERATION_RE.finditer(expanded_body):
                original_start = body_start + operation_match.start()
                prefix = tex_text[:original_start]
                start_line = prefix.count("\n") + 1
                line_start = prefix.rfind("\n") + 1
                if tex_text[line_start:original_start].lstrip().startswith("%"):
                    continue
                operations.append(
                    {
                        "text": operation_match.group(0),
                        "source_line": start_line,
                        "command": str(operation_match.group("command") or ""),
                        "options": str(operation_match.group("options") or ""),
                    }
                )
    return operations


def _parse_foreach_pairs(raw: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for item in raw.split(","):
        parts = item.strip().split("/")
        if len(parts) != 2:
            continue
        x_raw, y_raw = (part.strip() for part in parts)
        try:
            float(x_raw)
            float(y_raw)
        except ValueError:
            continue
        pairs.append((x_raw, y_raw))
    return pairs


def extract_vector_elements(tex_text: str) -> list[dict[str, Any]]:
    """Return literal TikZ vector elements in source cm coordinates."""
    elements: list[dict[str, Any]] = []
    for operation in _iter_operations(tex_text):
        text = str(operation["text"])
        source_line = int(operation["source_line"])
        base = {
            "source_line": source_line,
            "command": operation["command"],
            "options": operation["options"],
            "tex_anchor": text.strip(),
        }
        for match in _SEGMENT_RE.finditer(text):
            x0, y0, x1, y1 = (float(value) for value in match.groups())
            points = [(x0, y0), (x1, y1)]
            elements.append(
                {
                    **base,
                    "kind": "line",
                    "points_cm": points,
                    "bbox_cm": _bbox(points),
                }
            )
        for match in _RECT_RE.finditer(text):
            x0, y0, x1, y1 = (float(value) for value in match.groups())
            bbox = [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]
            elements.append({**base, "kind": "rect", "bbox_cm": bbox})
        for match in _CIRCLE_RE.finditer(text):
            x, y, radius, unit = match.groups()
            cx = float(x)
            cy = float(y)
            radius_cm = _radius_cm(float(radius), unit)
            kind = (
                "marker"
                if operation["command"] in {"fill", "shade"} and radius_cm <= MARKER_RADIUS_MAX_CM
                else "circle"
            )
            elements.append(
                {
                    **base,
                    "kind": kind,
                    "center_cm": [cx, cy],
                    "radius_cm": radius_cm,
                    "bbox_cm": [
                        cx - radius_cm,
                        cy - radius_cm,
                        cx + radius_cm,
                        cy + radius_cm,
                    ],
                    "clearance_mode": "disc_envelope",
                }
            )
        for match in _BEZIER_RE.finditer(text):
            values = [float(value) for value in match.groups()]
            points = [
                (values[index], values[index + 1])
                for index in range(0, len(values), 2)
            ]
            elements.append(
                {
                    **base,
                    "kind": "curve",
                    "control_hull_cm": points,
                    "bbox_cm": _bbox(points),
                    "clearance_mode": "conservative_hull",
                }
            )
    for index, element in enumerate(elements, start=1):
        element["id"] = f"VE{index:03d}"
    return elements


def parse_vector_clearance_checks(spec: dict[str, Any]) -> list[dict[str, Any]]:
    raw = spec.get("vector_clearance_checks")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise VectorClearanceError("vector_clearance_checks must be a list")
    checks: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise VectorClearanceError(f"vector_clearance_checks[{index}] must be a mapping")
        check_id = item.get("id")
        if not isinstance(check_id, str) or not check_id.strip():
            raise VectorClearanceError(f"vector_clearance_checks[{index}].id is required")
        element_a = _parse_selector(item.get("element_a"), index, "element_a")
        element_b = _parse_selector(item.get("element_b"), index, "element_b")
        relation_keys = [
            key for key in ("min_clearance_cm", "must_touch", "must_not_cross") if key in item
        ]
        if len(relation_keys) != 1:
            raise VectorClearanceError(
                f"vector_clearance_checks[{index}] must declare exactly one relation"
            )
        relation = relation_keys[0]
        parsed: dict[str, Any] = {
            "id": check_id.strip(),
            "element_a": element_a,
            "element_b": element_b,
            "relation": relation,
        }
        if relation == "min_clearance_cm":
            value = item[relation]
            if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
                raise VectorClearanceError(
                    f"vector_clearance_checks[{index}].min_clearance_cm must be > 0"
                )
            parsed["min_clearance_cm"] = float(value)
        else:
            if item[relation] is not True:
                raise VectorClearanceError(
                    f"vector_clearance_checks[{index}].{relation} must be true"
                )
            parsed[relation] = True
        checks.append(parsed)
    return checks


def _parse_selector(raw: object, index: int, field: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise VectorClearanceError(f"vector_clearance_checks[{index}].{field} must be a mapping")
    selector: dict[str, Any] = {}
    if "source_line" in raw:
        source_line = raw["source_line"]
        if isinstance(source_line, bool) or not isinstance(source_line, int) or source_line <= 0:
            raise VectorClearanceError(
                f"vector_clearance_checks[{index}].{field}.source_line must be a positive integer"
            )
        selector["source_line"] = source_line
    if "matched_text" in raw:
        matched_text = raw["matched_text"]
        if not isinstance(matched_text, str) or not matched_text.strip():
            raise VectorClearanceError(
                f"vector_clearance_checks[{index}].{field}.matched_text must be a string"
            )
        selector["matched_text"] = matched_text.strip()
    if "kind" in raw:
        kind = raw["kind"]
        if kind not in {"line", "polyline", "curve", "rect", "circle", "marker", "arrowhead"}:
            raise VectorClearanceError(
                f"vector_clearance_checks[{index}].{field}.kind is unsupported"
            )
        selector["kind"] = kind
    if "bbox_cm" in raw:
        bbox = raw["bbox_cm"]
        if (
            not isinstance(bbox, list)
            or len(bbox) != 4
            or any(isinstance(value, bool) or not isinstance(value, int | float) for value in bbox)
        ):
            raise VectorClearanceError(
                f"vector_clearance_checks[{index}].{field}.bbox_cm must be four numbers"
            )
        x0, y0, x1, y1 = (float(value) for value in bbox)
        selector["bbox_cm"] = [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]
    if not selector or set(selector) == {"kind"}:
        raise VectorClearanceError(
            f"vector_clearance_checks[{index}].{field} needs source_line, matched_text, or bbox_cm"
        )
    return selector


def _selector_has_stable_identity(selector: dict[str, Any]) -> bool:
    return "matched_text" in selector or "bbox_cm" in selector


def _matches_selector(
    element: dict[str, Any],
    selector: dict[str, Any],
    *,
    include_source_line: bool = True,
) -> bool:
    if (
        include_source_line
        and "source_line" in selector
        and element["source_line"] != selector["source_line"]
    ):
        return False
    if "matched_text" in selector and selector["matched_text"] not in element["tex_anchor"]:
        return False
    if "kind" in selector and element["kind"] != selector["kind"]:
        return False
    if "bbox_cm" in selector and not _bbox_almost_equal(element["bbox_cm"], selector["bbox_cm"]):
        return False
    return True


def _bbox_almost_equal(a: list[float], b: list[float]) -> bool:
    return all(
        abs(left - right) <= SELECTOR_BBOX_TOLERANCE_CM
        for left, right in zip(a, b, strict=True)
    )


def _resolve_selector(
    elements: list[dict[str, Any]],
    check_id: str,
    selector_name: str,
    selector: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    matches = [element for element in elements if _matches_selector(element, selector)]
    if not matches and "source_line" in selector and _selector_has_stable_identity(selector):
        matches = [
            element
            for element in elements
            if _matches_selector(element, selector, include_source_line=False)
        ]
        if len(matches) == 1:
            match = dict(matches[0])
            match["_selector_line_drift"] = {
                "selector": selector_name,
                "declared_source_line": selector["source_line"],
                "actual_source_line": match["source_line"],
            }
            return match, None
    if not matches:
        return None, {
            "id": check_id,
            "status": "selector_missing",
            "selector": selector_name,
            "message": f"vector_clearance {check_id!r} {selector_name} selector matched 0 elements",
        }
    if len(matches) > 1:
        return None, {
            "id": check_id,
            "status": "selector_ambiguous",
            "selector": selector_name,
            "match_count": len(matches),
            "message": (
                f"vector_clearance {check_id!r} {selector_name} selector matched "
                f"{len(matches)} elements"
            ),
        }
    return matches[0], None


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    *,
    eps: float = 1e-9,
) -> bool:
    return (
        min(a[0], c[0]) - eps <= b[0] <= max(a[0], c[0]) + eps
        and min(a[1], c[1]) - eps <= b[1] <= max(a[1], c[1]) + eps
    )


def _segments_intersect(
    a0: tuple[float, float],
    a1: tuple[float, float],
    b0: tuple[float, float],
    b1: tuple[float, float],
) -> bool:
    o1 = _orientation(a0, a1, b0)
    o2 = _orientation(a0, a1, b1)
    o3 = _orientation(b0, b1, a0)
    o4 = _orientation(b0, b1, a1)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    return (
        abs(o1) < 1e-9 and _on_segment(a0, b0, a1)
        or abs(o2) < 1e-9 and _on_segment(a0, b1, a1)
        or abs(o3) < 1e-9 and _on_segment(b0, a0, b1)
        or abs(o4) < 1e-9 and _on_segment(b0, a1, b1)
    )


def _point_segment_distance(
    point: tuple[float, float],
    a: tuple[float, float],
    b: tuple[float, float],
) -> float:
    px, py = point
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    denom = dx * dx + dy * dy
    if denom == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / denom))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _segment_distance(
    a0: tuple[float, float],
    a1: tuple[float, float],
    b0: tuple[float, float],
    b1: tuple[float, float],
) -> float:
    if _segments_intersect(a0, a1, b0, b1):
        return 0.0
    return min(
        _point_segment_distance(a0, b0, b1),
        _point_segment_distance(a1, b0, b1),
        _point_segment_distance(b0, a0, a1),
        _point_segment_distance(b1, a0, a1),
    )


def _bbox_distance(a: list[float], b: list[float]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def _line_circle_distance(line: dict[str, Any], circle: dict[str, Any]) -> float:
    a, b = line["points_cm"]
    center = (float(circle["center_cm"][0]), float(circle["center_cm"][1]))
    return max(0.0, _point_segment_distance(center, a, b) - float(circle["radius_cm"]))


def _element_distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    if a["kind"] == "line" and b["kind"] == "line":
        return _segment_distance(
            a["points_cm"][0],
            a["points_cm"][1],
            b["points_cm"][0],
            b["points_cm"][1],
        )
    if a["kind"] == "line" and b["kind"] == "circle":
        return _line_circle_distance(a, b)
    if a["kind"] == "circle" and b["kind"] == "line":
        return _line_circle_distance(b, a)
    return _bbox_distance(a["bbox_cm"], b["bbox_cm"])


def _non_auto_promotable(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return a["kind"] in {"circle", "curve", "marker"} or b["kind"] in {
        "circle",
        "curve",
        "marker",
    }


def check_vector_clearance(tex_text: str, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not checks:
        return []
    elements = extract_vector_elements(tex_text)
    issues: list[dict[str, Any]] = []
    for check in checks:
        element_a, issue = _resolve_selector(elements, check["id"], "element_a", check["element_a"])
        if issue is not None:
            issues.append(issue)
            continue
        element_b, issue = _resolve_selector(elements, check["id"], "element_b", check["element_b"])
        if issue is not None:
            issues.append(issue)
            continue
        assert element_a is not None and element_b is not None
        distance_cm = _element_distance(element_a, element_b)
        relation = check["relation"]
        violated = False
        issue: dict[str, Any] = {
            "id": check["id"],
            "status": "violated",
            "relation": relation,
            "element_a": element_a["id"],
            "element_b": element_b["id"],
            "element_a_kind": element_a["kind"],
            "element_b_kind": element_b["kind"],
            "element_a_source_line": element_a["source_line"],
            "element_b_source_line": element_b["source_line"],
            "element_a_bbox_cm": element_a["bbox_cm"],
            "element_b_bbox_cm": element_b["bbox_cm"],
            "measured_clearance_cm": round(distance_cm, 6),
        }
        if relation == "must_not_cross":
            violated = distance_cm <= 0.0
        elif relation == "must_touch":
            violated = distance_cm > TOUCH_TOLERANCE_CM
            issue["tolerance_cm"] = TOUCH_TOLERANCE_CM
        elif relation == "min_clearance_cm":
            required = float(check["min_clearance_cm"])
            violated = distance_cm < required
            issue["required_clearance_cm"] = required
            issue["clearance_delta_cm"] = round(distance_cm - required, 6)
        if not violated:
            continue
        selector_line_drifts = [
            drift
            for drift in (
                element_a.get("_selector_line_drift"),
                element_b.get("_selector_line_drift"),
            )
            if isinstance(drift, dict)
        ]
        if selector_line_drifts:
            issue["selector_line_drifts"] = selector_line_drifts
        non_auto = _non_auto_promotable(element_a, element_b)
        issue["non_auto_promotable"] = non_auto
        issue["promotion_tier"] = "review_queue" if non_auto else "auto"
        issue["message"] = (
            f"vector_clearance {check['id']!r} violated {relation}: "
            f"clearance {distance_cm:.3f}cm"
        )
        issues.append(issue)
    return issues


def vector_clearance_payload(
    pdf_path: Path,
    issues: list[dict[str, Any]],
    checked: int,
    *,
    tex_path: Path | None = None,
) -> dict[str, Any]:
    fixture_dir = pdf_path.parent.parent
    fixture_name = fixture_dir.name or Path.cwd().name
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "render_pdf": f"build/{pdf_path.name}",
        "checked": checked,
        "issues": issues,
        "total": len(issues),
    }
    if tex_path is not None:
        payload["source_hashes"] = {
            f"examples/{fixture_name}/{tex_path.name}": _hash_file(tex_path)
        }
    return payload


def _load_spec(spec_path: Path) -> dict[str, Any]:
    if not spec_path.is_file():
        return {}
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise VectorClearanceError(f"unreadable spec.yaml: {exc}") from exc
    if spec is None:
        return {}
    if not isinstance(spec, dict):
        raise VectorClearanceError(f"spec.yaml is not a mapping: {spec_path}")
    return spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check declared vector clearance relations.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--tex", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    pdf_path: Path = args.pdf
    tex_path: Path = args.tex
    if not pdf_path.is_file():
        print(f"ERROR: missing PDF: {pdf_path}", file=sys.stderr)
        return 2
    if not tex_path.is_file():
        print(f"ERROR: missing TeX: {tex_path}", file=sys.stderr)
        return 2
    try:
        checks = parse_vector_clearance_checks(_load_spec(pdf_path.parent.parent / "spec.yaml"))
        issues = check_vector_clearance(tex_path.read_text(encoding="utf-8"), checks)
    except VectorClearanceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    output = args.json_output or pdf_path.parent / "vector_clearance.json"
    payload = vector_clearance_payload(pdf_path, issues, len(checks), tex_path=tex_path)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    for issue in issues:
        print(f"WARN vector_clearance: {issue.get('message', issue['status'])}", file=sys.stderr)
    if args.strict and issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
