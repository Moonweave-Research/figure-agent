"""Semantic SVG schema, style-lock, and geometry QA for figure-agent-svg."""

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
import xml.etree.ElementTree as ET
from itertools import combinations
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STYLE_TOKENS = REPO_ROOT / "styles" / "svg_style_tokens.yaml"
REQUIRED_GROUP_IDS = ("semantic-layer", "panels", "objects", "labels")
SVG_NS = "http://www.w3.org/2000/svg"


@dataclasses.dataclass(frozen=True)
class SvgIssue:
    code: str
    message: str
    target: str | None = None


@dataclasses.dataclass(frozen=True)
class BBox:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def intersects(self, other: BBox) -> bool:
        return (
            self.x < other.right
            and self.right > other.x
            and self.y < other.bottom
            and self.bottom > other.y
        )

    def outside(self, width: float, height: float) -> bool:
        return self.x < 0 or self.y < 0 or self.right > width or self.bottom > height

    def margin_violation(self, width: float, height: float, margin: float) -> bool:
        return (
            self.x < margin
            or self.y < margin
            or self.right > width - margin
            or self.bottom > height - margin
        )


@dataclasses.dataclass(frozen=True)
class BBoxRecord:
    elem: ET.Element
    kind: str
    identifier: str
    bbox: BBox


def issue_codes(issues: list[SvgIssue]) -> list[str]:
    """Return stable issue code strings for tests and CLI output."""
    out: list[str] = []
    for issue in issues:
        if issue.code == "missing_group" and issue.target:
            out.append(f"{issue.code}:{issue.target}")
        else:
            out.append(issue.code)
    return out


def load_style_tokens(path: Path = DEFAULT_STYLE_TOKENS) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_by_id(root: ET.Element, elem_id: str) -> ET.Element | None:
    for elem in _iter_semantic_elements(root):
        if elem.get("id") == elem_id:
            return elem
    return None


def _iter_semantic_elements(root: ET.Element):
    """Yield semantic contract elements, treating wrapped generator SVG as opaque."""
    yield root
    if root.get("data-external-svg") == "true":
        return
    for child in list(root):
        yield from _iter_semantic_elements(child)


def _style_value(elem: ET.Element, name: str) -> str | None:
    direct = elem.get(name)
    if direct is not None:
        return direct.strip()
    style = elem.get("style", "")
    for part in style.split(";"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        if key.strip() == name:
            return value.strip()
    return None


def _normalize_hex(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if value in {"none", "transparent", "currentColor"} or value.startswith("url("):
        return None
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return value.upper()
    return value


def _parse_float(value: str | None) -> float | None:
    if not value:
        return None
    match = re.match(r"^\s*([-+]?\d*\.?\d+)", value)
    return float(match.group(1)) if match else None


def _parse_mm(value: str | None) -> float | None:
    if not value:
        return None
    match = re.fullmatch(r"\s*([-+]?\d*\.?\d+)mm\s*", value)
    return float(match.group(1)) if match else None


def _parse_viewbox(value: str | None) -> tuple[float, float, float, float] | None:
    if not value:
        return None
    parts = [float(part) for part in re.split(r"[\s,]+", value.strip()) if part]
    if len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
        return None
    return parts[0], parts[1], parts[2], parts[3]


def _parse_bbox(value: str | None) -> BBox | None:
    if not value:
        return None
    parts = [float(part) for part in re.split(r"[\s,]+", value.strip()) if part]
    if len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
        return None
    return BBox(*parts)


def _text_content(elem: ET.Element) -> str:
    return " ".join("".join(elem.itertext()).split())


def _append_schema_issues(root: ET.Element, issues: list[SvgIssue]) -> None:
    if root.get("data-figure-agent-svg") != "semantic-v1":
        issues.append(
            SvgIssue(
                "missing_schema_marker",
                'root <svg> must declare data-figure-agent-svg="semantic-v1"',
            )
        )
    for group_id in REQUIRED_GROUP_IDS:
        if _find_by_id(root, group_id) is None:
            issues.append(SvgIssue("missing_group", f"missing required group {group_id}", group_id))
    for elem in _iter_semantic_elements(root):
        if (
            elem.get("id") == "vtracer-underlay"
            or elem.get("data-role") == "coordinate-evidence"
            or elem.get("data-final-source") == "false"
        ):
            issues.append(
                SvgIssue(
                    "coordinate_evidence_in_source",
                    "locked vtracer underlay belongs under underlay/, not source/",
                    elem.get("id"),
                )
            )


def _append_journal_issues(root: ET.Element, tokens: dict, issues: list[SvgIssue]) -> None:
    presets = tokens["journal_presets"]
    preset_name = root.get("data-journal-preset")
    if preset_name not in presets:
        issues.append(SvgIssue("unknown_journal_preset", "unknown or missing journal preset"))
        width_mm = _parse_mm(root.get("width"))
        allowed_widths = {float(preset["width_mm"]) for preset in presets.values()}
        if width_mm is not None and all(abs(width_mm - width) > 0.01 for width in allowed_widths):
            issues.append(SvgIssue("journal_width_mismatch", "root width does not match preset"))
        return

    width_mm = _parse_mm(root.get("width"))
    if width_mm is None:
        issues.append(SvgIssue("missing_width_mm", "root width must be expressed in mm"))
    elif abs(width_mm - float(presets[preset_name]["width_mm"])) > 0.01:
        issues.append(SvgIssue("journal_width_mismatch", "root width does not match preset"))

    height_mm = _parse_mm(root.get("height"))
    if height_mm is None:
        issues.append(SvgIssue("missing_height_mm", "root height must be expressed in mm"))
    elif height_mm > float(presets[preset_name]["max_height_mm"]):
        issues.append(SvgIssue("journal_height_too_large", "root height exceeds preset"))


def _append_style_issues(root: ET.Element, tokens: dict, issues: list[SvgIssue]) -> None:
    palette = {value.upper() for value in tokens["palette"].values()}
    allowed_fonts = set(tokens["font_families"])
    text_roles = tokens["text_roles"]
    stroke_widths = {float(value) for value in tokens["stroke_widths"]}

    for elem in _iter_semantic_elements(root):
        for attr, code in (("fill", "fill_not_in_palette"), ("stroke", "stroke_not_in_palette")):
            value = _normalize_hex(_style_value(elem, attr))
            if value is not None and value not in palette:
                issues.append(SvgIssue(code, f"{attr} {value} is outside the style palette"))

        stroke = _normalize_hex(_style_value(elem, "stroke"))
        stroke_width = _parse_float(_style_value(elem, "stroke-width"))
        if stroke is not None and stroke_width is not None and stroke_width not in stroke_widths:
            issues.append(
                SvgIssue("stroke_width_not_allowed", "stroke-width is outside style tokens")
            )

        if _local_name(elem.tag) != "text":
            continue

        role = elem.get("data-text-role")
        if not role:
            issues.append(SvgIssue("missing_text_role", "text must declare data-text-role"))
        elif role not in text_roles:
            issues.append(SvgIssue("unknown_text_role", f"unknown text role {role}"))

        font_family = _style_value(elem, "font-family")
        if not font_family:
            issues.append(SvgIssue("font_family_missing", "text must declare font-family"))
        elif font_family.strip("'\"") not in allowed_fonts:
            issues.append(SvgIssue("font_family_not_allowed", "font-family is not allowed"))

        font_size = _parse_float(_style_value(elem, "font-size"))
        expected = text_roles.get(role or "", {}).get("font_size")
        if font_size is None or expected is None or abs(font_size - float(expected)) > 0.01:
            issues.append(SvgIssue("font_size_mismatch", "font-size does not match text role"))


def _collect_bboxes(root: ET.Element, issues: list[SvgIssue]) -> list[BBoxRecord]:
    records: list[BBoxRecord] = []
    for elem in _iter_semantic_elements(root):
        kind = ""
        identifier = elem.get("id") or elem.get("data-object-id") or _text_content(elem)
        if _local_name(elem.tag) == "text":
            kind = "text"
        elif elem.get("data-object-id"):
            kind = "object"
        elif elem.get("data-role") == "panel":
            kind = "panel"
        elif not elem.get("data-bbox"):
            continue
        else:
            kind = "object"

        bbox = _parse_bbox(elem.get("data-bbox"))
        if bbox is None:
            issues.append(SvgIssue("missing_or_invalid_bbox", "semantic elements need data-bbox"))
            continue
        records.append(BBoxRecord(elem, kind, identifier, bbox))
    return records


def _allowed_overlap(record: BBoxRecord) -> bool:
    return (
        record.elem.get("data-overlap") == "allow"
        or record.elem.get("data-collision") == "allow"
    )


def _append_geometry_issues(
    root: ET.Element,
    tokens: dict,
    issues: list[SvgIssue],
) -> None:
    viewbox = _parse_viewbox(root.get("viewBox"))
    if viewbox is None:
        issues.append(SvgIssue("missing_viewbox", "root viewBox is required"))
        return

    _, _, width, height = viewbox
    layout = tokens["layout"]
    margin_min = float(layout["margin_min"])
    panel_gap_min = float(layout["panel_gap_min"])
    records = _collect_bboxes(root, issues)

    for record in records:
        if record.bbox.outside(width, height):
            issues.append(SvgIssue("bbox_outside_viewbox", "semantic bbox extends outside viewBox"))
        if record.bbox.margin_violation(width, height, margin_min):
            issues.append(SvgIssue("content_margin_violation", "semantic bbox violates min margin"))

    panels = [record for record in records if record.kind == "panel"]
    for left, right in combinations(panels, 2):
        if left.bbox.intersects(right.bbox):
            issues.append(SvgIssue("panel_overlap", "panel bboxes overlap"))
            continue
        horizontal_overlap = left.bbox.x < right.bbox.right and left.bbox.right > right.bbox.x
        vertical_overlap = left.bbox.y < right.bbox.bottom and left.bbox.bottom > right.bbox.y
        if vertical_overlap:
            gap = max(right.bbox.x - left.bbox.right, left.bbox.x - right.bbox.right)
            if 0 < gap < panel_gap_min:
                issues.append(SvgIssue("panel_gap_too_small", "panel horizontal gap is too small"))
        if horizontal_overlap:
            gap = max(right.bbox.y - left.bbox.bottom, left.bbox.y - right.bbox.bottom)
            if 0 < gap < panel_gap_min:
                issues.append(SvgIssue("panel_gap_too_small", "panel vertical gap is too small"))

    for kind, code in (("text", "text_overlap"), ("object", "object_overlap")):
        candidates = [record for record in records if record.kind == kind]
        for first, second in combinations(candidates, 2):
            if _allowed_overlap(first) or _allowed_overlap(second):
                continue
            if first.bbox.intersects(second.bbox):
                issues.append(SvgIssue(code, f"{kind} bboxes overlap"))


def _append_requirement_issues(root: ET.Element, spec: dict | None, issues: list[SvgIssue]) -> None:
    spec = spec or {}
    labels = {
        _text_content(elem)
        for elem in _iter_semantic_elements(root)
        if _local_name(elem.tag) == "text"
    }
    objects = {
        elem.get("data-object-id")
        for elem in _iter_semantic_elements(root)
        if elem.get("data-object-id")
    }

    for label in spec.get("required_labels", []) or []:
        if label not in labels:
            issues.append(SvgIssue("missing_required_label", f"missing required label {label}"))
    for object_id in spec.get("required_objects", []) or []:
        if object_id not in objects:
            issues.append(
                SvgIssue("missing_required_object", f"missing required object {object_id}")
            )


def validate_semantic_svg(
    svg_path: Path,
    *,
    spec: dict | None = None,
    style_tokens_path: Path = DEFAULT_STYLE_TOKENS,
) -> list[SvgIssue]:
    """Validate semantic SVG source for paper-figure production."""
    root = ET.parse(svg_path).getroot()
    tokens = load_style_tokens(style_tokens_path)
    issues: list[SvgIssue] = []
    _append_schema_issues(root, issues)
    _append_journal_issues(root, tokens, issues)
    _append_style_issues(root, tokens, issues)
    _append_geometry_issues(root, tokens, issues)
    _append_requirement_issues(root, spec, issues)
    return issues


def _load_spec(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate semantic SVG source contract.")
    parser.add_argument("source_svg", type=Path)
    parser.add_argument("--spec", type=Path)
    args = parser.parse_args()

    issues = validate_semantic_svg(args.source_svg, spec=_load_spec(args.spec))
    if issues:
        for issue in issues:
            suffix = f" [{issue.target}]" if issue.target else ""
            print(f"FAIL: {issue.code}{suffix}: {issue.message}", file=sys.stderr)
        return 1
    print("OK: semantic SVG contract passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
