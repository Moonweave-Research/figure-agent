from __future__ import annotations

import json
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
SVG = ROOT / "fig1_reference_semantic.svg"
MARKDOWN_OUT = ROOT / "fig1_visual_judgment_report.md"
JSON_OUT = ROOT / "fig1_visual_judgment_report.json"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from engine.scene import Rect, Scene
from engine.visual_constraints import BBox, _element_bbox, semantic_group_bboxes
from fig1_l1_scene import build_scene


REPORT_CATEGORIES = (
    "Panel Density",
    "Text / Text Near-Collision",
    "Text / Shape Conflict",
    "Visual Hierarchy",
    "Reading Order",
    "Reference Divergence",
    "Human Review Prompts",
)

PRIMARY_SEMANTIC_IDS = {
    "deep_trap_hero",
    "band_diagram",
    "trap_level_set",
    "dos_lobes",
    "repulsion_arrow",
}
SHAPE_CONFLICT_ROLES = (
    "arrow",
    "axis",
    "curve",
    "deep",
    "dos",
    "flow",
    "guide",
    "lobe",
    "schematic",
    "shallow",
    "threshold",
    "trap",
)
EXPECTED_COMPOSITE_TEXT_PAIRS = {
    frozenset(("Et ~", "0.5-1.0 eV")),
    frozenset(("I(t) ~", "t^-n")),
    frozenset(("Debye", "exp(-t/tau)")),
    frozenset(("deep", "states")),
    frozenset(("shallow", "states")),
    frozenset(("Cantilever", "(probe)")),
    frozenset(("Convergence to deep traps (tau_d)", "extended repulsion.")),
}
PROBE_OWNED_TEXT_LABELS = {
    "+",
    "+ V",
    "Cantilever",
    "(probe)",
    "Force on cantilever",
    "Maxwell attraction",
}


def build_visual_judgment_report(scene: Scene, svg_path: str | Path = SVG) -> dict[str, Any]:
    svg = Path(svg_path)
    if not svg.exists():
        raise FileNotFoundError(f"missing rendered SVG for visual judgment report: {svg}")

    root = ET.parse(svg).getroot()
    semantic_boxes = _semantic_box_records(scene, svg)
    text_boxes = _text_box_records(scene, root)
    shape_boxes = _shape_box_records(scene, root)
    panel_records = _panel_records(scene, semantic_boxes, text_boxes)

    categories = [
        _panel_density_category(panel_records),
        _text_near_collision_category(text_boxes),
        _text_shape_conflict_category(text_boxes, shape_boxes),
        _visual_hierarchy_category(scene, text_boxes, semantic_boxes),
        _reading_order_category(panel_records, text_boxes),
        _reference_divergence_category(scene),
    ]
    review_prompts = _human_review_prompts(categories)
    categories.append(
        {
            "name": "Human Review Prompts",
            "items": [{"severity": "inspect", "message": prompt} for prompt in review_prompts],
        }
    )

    return {
        "schema_version": "fig1_visual_judgment_report_v22",
        "figure_id": scene.id,
        "svg": str(svg.relative_to(ROOT)),
        "report_only": True,
        "blocking_failures": [],
        "non_goals": [
            "does not fail subjective visual risks",
            "does not claim publication-grade approval",
            "does not pixel-trace the reference image",
            "does not add absolute min-font-size rules",
        ],
        "panels": panel_records,
        "semantic_boxes": semantic_boxes,
        "text_boxes": text_boxes,
        "shape_box_count": len(shape_boxes),
        "categories": categories,
    }


def markdown_for_report(report: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Fig1 Visual Judgment Report v22",
        "",
        "This is a report-only visual judgment layer. It surfaces candidate visual risks and review prompts; it does not fail subjective visual issues.",
        "",
        "Human visual review remains required before publication-grade approval.",
        "",
        "## Scope Boundary",
        "",
        "- Report-only: warnings here are not strict gate failures.",
        "- Existing semantic, scaffold, causal, physics, and hash gates remain the hard-fail channels.",
        "- Reference PNG remains layout/style evidence only, not ground truth.",
        "- The v21 leftward cantilever force cue is an intentional reference divergence for physics sanity.",
        "",
        "## Category Findings",
        "",
    ]

    for category in report["categories"]:
        lines.append(f"### {category['name']}")
        if not category["items"]:
            lines.append("- No candidate risk inferred by this report.")
            lines.append("")
            continue
        for item in category["items"]:
            lines.append(f"- {item['severity']}: {item['message']}")
        lines.append("")

    lines.extend(
        [
            "## Evidence Snapshot",
            "",
            "### Panel Bounds And Density",
            "",
            "| Panel | Role | Bounds | Occupied | Text | Semantic Objects |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for panel in report["panels"]:
        bounds = panel["bounds"]
        bounds_text = f"{bounds['x']:.1f},{bounds['y']:.1f},{bounds['width']:.1f},{bounds['height']:.1f}"
        lines.append(
            "| {id} | {role} | {bounds} | {occupied:.3f} | {text:.3f} | {semantic_count} |".format(
                id=panel["id"],
                role=panel["role"],
                bounds=bounds_text,
                occupied=panel["occupied_area_ratio"],
                text=panel["text_area_ratio"],
                semantic_count=panel["semantic_box_count"],
            )
        )
    lines.extend(["", "### Semantic Object BBoxes", "", "| Semantic id | Kind | Panel | BBox |", "| --- | --- | --- | --- |"])
    for item in report["semantic_boxes"]:
        bbox = item["bbox"]
        bbox_text = f"{bbox['left']:.1f},{bbox['top']:.1f},{bbox['right']:.1f},{bbox['bottom']:.1f}"
        lines.append(f"| {item['id']} | {item['kind']} | {item['panel_id']} | {bbox_text} |")

    lines.extend(["", "### Text BBox Summary", "", "| Panel | Text boxes | Font range | Role tags |", "| --- | ---: | --- | --- |"])
    for panel in report["panels"]:
        role_tags = ", ".join(panel["text_role_tags"][:8])
        if len(panel["text_role_tags"]) > 8:
            role_tags += ", ..."
        lines.append(
            f"| {panel['id']} | {panel['text_box_count']} | "
            f"{panel['min_font_size']:.1f}-{panel['max_font_size']:.1f} | {role_tags or 'none'} |"
        )

    lines.append("")
    return "\n".join(lines)


def write_visual_judgment_reports(
    report: dict[str, Any],
    *,
    markdown_path: str | Path = MARKDOWN_OUT,
    json_path: str | Path = JSON_OUT,
) -> None:
    markdown_target = Path(markdown_path)
    json_target = Path(json_path)
    markdown_target.write_text(markdown_for_report(report))
    json_target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def _semantic_box_records(scene: Scene, svg_path: Path) -> list[dict[str, Any]]:
    bboxes = semantic_group_bboxes(svg_path)
    records: list[dict[str, Any]] = []
    for obj in scene.objects:
        bbox = bboxes.get(obj.id)
        if bbox is None:
            continue
        records.append(
            {
                "id": obj.id,
                "kind": obj.kind,
                "label": obj.label,
                "panel_id": _panel_id_for_bbox(scene, bbox),
                "role_tags": _semantic_role_tags(obj.id, obj.kind),
                "bbox": _bbox_record(bbox),
                "area": round(_bbox_area(bbox), 3),
            }
        )
    return records


def _text_box_records(scene: Scene, root: ET.Element) -> list[dict[str, Any]]:
    raw_records: list[dict[str, Any]] = []
    for index, element, semantic_id, semantic_kind in _walk_svg_elements(root):
        if _local_name(element.tag) != "text":
            continue
        bbox = _element_bbox(element)
        if bbox is None:
            continue
        value = " ".join("".join(element.itertext()).split())
        if not value:
            continue
        role_tags = _role_tags(element)
        raw_records.append(
            {
                "index": index,
                "text": value,
                "panel_id": _panel_id_for_bbox(scene, bbox),
                "semantic_id": semantic_id,
                "semantic_kind": semantic_kind,
                "role_tags": role_tags,
                "font_size": round(_float_attr(element, "font-size", 12.0), 3),
                "font_weight": element.attrib.get("font-weight", ""),
                "visible": element.attrib.get("fill") != "none",
                "bbox": _bbox_record(bbox),
                "area": round(_bbox_area(bbox), 3),
            }
        )
    return _merge_invisible_text_role_markers(raw_records)


def _shape_box_records(scene: Scene, root: ET.Element) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, element, semantic_id, semantic_kind in _walk_svg_elements(root):
        tag = _local_name(element.tag)
        if tag in {"text", "svg", "defs", "g", "title", "stop", "filter", "pattern"} or tag.startswith("fe"):
            continue
        bbox = _element_bbox(element)
        if bbox is None or _bbox_area(bbox) <= 0:
            continue
        if _is_invisible_shape(element):
            continue
        role_tags = _role_tags(element)
        records.append(
            {
                "index": index,
                "tag": tag,
                "panel_id": _panel_id_for_bbox(scene, bbox),
                "semantic_id": semantic_id,
                "semantic_kind": semantic_kind,
                "role_tags": role_tags,
                "stroke_width": round(_float_attr(element, "stroke-width", 0.0), 3),
                "bbox": _bbox_record(bbox),
                "bbox_obj": bbox,
            }
        )
    return records


def _panel_records(
    scene: Scene,
    semantic_boxes: list[dict[str, Any]],
    text_boxes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for column in scene.layout.columns:
        panel_bbox = _bbox_from_rect(column.bounds)
        panel_area = _bbox_area(panel_bbox)
        panel_semantic = [
            item
            for item in semantic_boxes
            if item["panel_id"] == column.id and item["id"] != "layout_flow"
        ]
        panel_text = [item for item in text_boxes if item["panel_id"] == column.id]
        semantic_rectangles = [_clipped_bbox(_bbox_from_record(item["bbox"]), panel_bbox) for item in panel_semantic]
        text_rectangles = [_clipped_bbox(_bbox_from_record(item["bbox"]), panel_bbox) for item in panel_text]
        semantic_area = _rectangle_union_area([bbox for bbox in semantic_rectangles if bbox is not None])
        text_area = _rectangle_union_area([bbox for bbox in text_rectangles if bbox is not None])
        occupied_area = _rectangle_union_area([bbox for bbox in (*semantic_rectangles, *text_rectangles) if bbox is not None])
        font_sizes = [item["font_size"] for item in panel_text]
        text_roles = sorted({role for item in panel_text for role in item["role_tags"]})
        records.append(
            {
                "id": column.id,
                "title": column.title,
                "role": column.role,
                "bounds": {
                    "x": column.bounds.x,
                    "y": column.bounds.y,
                    "width": column.bounds.width,
                "height": column.bounds.height,
                },
                "occupied_area_ratio": round(min(occupied_area / panel_area, 1.0), 4),
                "semantic_area_ratio": round(min(semantic_area / panel_area, 1.0), 4),
                "text_area_ratio": round(min(text_area / panel_area, 1.0), 4),
                "semantic_box_count": len(panel_semantic),
                "text_box_count": len(panel_text),
                "min_font_size": round(min(font_sizes), 3) if font_sizes else 0.0,
                "max_font_size": round(max(font_sizes), 3) if font_sizes else 0.0,
                "median_font_size": round(statistics.median(font_sizes), 3) if font_sizes else 0.0,
                "text_role_tags": text_roles,
            }
        )
    return records


def _panel_density_category(panel_records: list[dict[str, Any]]) -> dict[str, Any]:
    items: list[dict[str, str]] = []
    for panel in panel_records:
        ratio = panel["occupied_area_ratio"]
        text_ratio = panel["text_area_ratio"]
        if ratio >= 0.70:
            severity = "possible issue"
            message = (
                f"{panel['id']} has high approximate occupied area ({ratio:.2f}); "
                "inspect whether panel density harms first-pass reading."
            )
        elif ratio >= 0.58:
            severity = "candidate risk"
            message = (
                f"{panel['id']} has moderate-high approximate occupied area ({ratio:.2f}); "
                "inspect whether whitespace is sufficient for scanning."
            )
        elif ratio <= 0.14:
            severity = "candidate risk"
            message = (
                f"{panel['id']} is unusually sparse by bbox area ({ratio:.2f}); "
                "inspect whether the visual weight matches its semantic role."
            )
        else:
            severity = "evidence"
            message = (
                f"{panel['id']} occupied area is {ratio:.2f} with text area {text_ratio:.2f}; "
                "use as layout density evidence, not a pass/fail rule."
            )
        items.append({"severity": severity, "message": message})
    return {"name": "Panel Density", "items": items}


def _text_near_collision_category(text_boxes: list[dict[str, Any]]) -> dict[str, Any]:
    candidates: list[tuple[float, dict[str, Any], dict[str, Any]]] = []
    for index, first in enumerate(text_boxes):
        for second in text_boxes[index + 1 :]:
            if first["panel_id"] != second["panel_id"]:
                continue
            if _is_expected_text_pair(first, second):
                continue
            distance = _bbox_gap(_bbox_from_record(first["bbox"]), _bbox_from_record(second["bbox"]))
            if distance <= 5.0:
                candidates.append((distance, first, second))
    candidates.sort(key=lambda item: (item[0], item[1]["panel_id"], item[1]["index"], item[2]["index"]))

    items: list[dict[str, str]] = []
    for distance, first, second in candidates[:14]:
        severity = "possible issue" if distance <= 1.0 else "candidate risk"
        items.append(
            {
                "severity": severity,
                "message": (
                    f"{first['panel_id']} text boxes may compete at {distance:.1f}px gap: "
                    f"'{_short(first['text'])}' near '{_short(second['text'])}'."
                ),
            }
        )
    if len(candidates) > len(items):
        items.append(
            {
                "severity": "inspect",
                "message": f"{len(candidates) - len(items)} additional near text pairs were omitted from this short report.",
            }
        )
    if not items:
        items.append(
            {
                "severity": "evidence",
                "message": "No text/text near-collision candidate was found with the current approximate bbox margin.",
            }
        )
    return {"name": "Text / Text Near-Collision", "items": items}


def _text_shape_conflict_category(
    text_boxes: list[dict[str, Any]],
    shape_boxes: list[dict[str, Any]],
) -> dict[str, Any]:
    conflict_shapes = [shape for shape in shape_boxes if _shape_has_conflict_role(shape)]
    candidates: list[tuple[float, dict[str, Any], dict[str, Any]]] = []
    for text in text_boxes:
        text_bbox = _bbox_from_record(text["bbox"])
        for shape in conflict_shapes:
            if text["panel_id"] != shape["panel_id"]:
                continue
            if _is_expected_text_shape_pair(text, shape):
                continue
            shape_bbox = shape["bbox_obj"]
            distance = _bbox_gap(text_bbox, shape_bbox)
            if distance <= 4.0 and text["semantic_id"] != shape["semantic_id"]:
                candidates.append((distance, text, shape))
    candidates.sort(key=lambda item: (item[0], item[1]["panel_id"], item[1]["index"], item[2]["index"]))
    candidates = _dedupe_text_shape_candidates(candidates)

    items: list[dict[str, str]] = []
    for distance, text, shape in candidates[:14]:
        roles = ", ".join(shape["role_tags"][:3]) or shape["tag"]
        items.append(
            {
                "severity": "candidate risk" if distance > 0 else "possible issue",
                "message": (
                    f"{text['panel_id']} text '{_short(text['text'])}' is {distance:.1f}px from "
                    f"{shape['tag']} mark ({roles}); inspect label ownership and legibility."
                ),
            }
        )
    if len(candidates) > len(items):
        items.append(
            {
                "severity": "inspect",
                "message": f"{len(candidates) - len(items)} additional text/shape proximity candidates were omitted.",
            }
        )
    if not items:
        items.append(
            {
                "severity": "evidence",
                "message": "No text/shape proximity candidate was found against arrow, curve, lobe, guide, or trap roles.",
            }
        )
    return {"name": "Text / Shape Conflict", "items": items}


def _dedupe_text_shape_candidates(
    candidates: list[tuple[float, dict[str, Any], dict[str, Any]]],
) -> list[tuple[float, dict[str, Any], dict[str, Any]]]:
    best_by_text_and_shape: dict[tuple[object, ...], tuple[float, dict[str, Any], dict[str, Any]]] = {}
    for distance, text, shape in candidates:
        key = (
            text["index"],
            shape.get("semantic_id") or shape["tag"],
            shape["tag"],
        )
        previous = best_by_text_and_shape.get(key)
        if previous is None or distance < previous[0]:
            best_by_text_and_shape[key] = (distance, text, shape)
    return sorted(
        best_by_text_and_shape.values(),
        key=lambda item: (item[0], item[1]["panel_id"], item[1]["index"], item[2]["index"]),
    )


def _visual_hierarchy_category(
    scene: Scene,
    text_boxes: list[dict[str, Any]],
    semantic_boxes: list[dict[str, Any]],
) -> dict[str, Any]:
    items: list[dict[str, str]] = []
    hero_panel = next(column for column in scene.layout.columns if column.role == "hero")
    hero_text = [item for item in text_boxes if item["panel_id"] == hero_panel.id]
    support_text = [item for item in text_boxes if item["panel_id"] != hero_panel.id]
    hero_max = max((item["font_size"] for item in hero_text), default=0.0)
    support_max = max((item["font_size"] for item in support_text), default=0.0)
    if hero_max <= support_max:
        items.append(
            {
                "severity": "possible issue",
                "message": (
                    f"hero maximum text size ({hero_max:.1f}) does not exceed support maximum ({support_max:.1f}); "
                    "inspect whether the center concept reads as primary."
                ),
            }
        )
    else:
        items.append(
            {
                "severity": "evidence",
                "message": (
                    f"hero maximum text size ({hero_max:.1f}) exceeds support maximum ({support_max:.1f}); "
                    "hierarchy appears intentional but still needs visual review."
                ),
            }
        )

    primary_records = [item for item in semantic_boxes if item["id"] in PRIMARY_SEMANTIC_IDS]
    primary_area = sum(item["area"] for item in primary_records)
    all_area = sum(item["area"] for item in semantic_boxes)
    primary_ratio = primary_area / all_area if all_area else 0.0
    items.append(
        {
            "severity": "evidence",
            "message": (
                f"bbox salience proxy: selected primary semantic objects occupy about {primary_ratio:.2f} "
                "of semantic bbox area; use this as evidence only, not a visual hierarchy failure."
            ),
        }
    )
    for text in _large_secondary_text_candidates(scene, text_boxes):
        items.append(
            {
                "severity": "candidate risk",
                "message": (
                    f"support-panel text '{_short(text['text'])}' uses {text['font_size']:.1f}px; "
                    "inspect whether it competes with the center hero."
                ),
            }
        )
    return {"name": "Visual Hierarchy", "items": items}


def _reading_order_category(
    panel_records: list[dict[str, Any]],
    text_boxes: list[dict[str, Any]],
) -> dict[str, Any]:
    ordered_panels = sorted(panel_records, key=lambda item: (item["bounds"]["y"], item["bounds"]["x"]))
    panel_order = " -> ".join(panel["id"] for panel in ordered_panels)
    items: list[dict[str, str]] = [
        {
            "severity": "evidence",
            "message": f"likely panel reading order by top-left position: {panel_order}.",
        }
    ]
    unowned = [
        text
        for text in text_boxes
        if not text["semantic_id"] and "panel-title-support" not in text["role_tags"] and "panel-title-hero" not in text["role_tags"]
    ]
    if unowned:
        preview = ", ".join(f"'{_short(text['text'])}'" for text in unowned[:8])
        items.append(
            {
                "severity": "candidate risk",
                "message": (
                    f"{len(unowned)} text boxes are outside semantic groups ({preview}); "
                    "inspect whether their ownership is visually clear."
                ),
            }
        )

    for panel in ordered_panels:
        panel_text = [text for text in text_boxes if text["panel_id"] == panel["id"]]
        if len(panel_text) <= 1:
            continue
        text_order = " -> ".join(_short(text["text"], limit=18) for text in sorted(panel_text, key=lambda item: (item["bbox"]["top"], item["bbox"]["left"]))[:6])
        items.append(
            {
                "severity": "evidence",
                "message": f"{panel['id']} first text sequence by bbox position: {text_order}.",
            }
        )
    return {"name": "Reading Order", "items": items}


def _reference_divergence_category(scene: Scene) -> dict[str, Any]:
    force_arrow = scene.object_by_id("repulsion_arrow").payload
    target = getattr(force_arrow, "force_target", "") or "unspecified"
    actual_leftward = force_arrow.end.x < force_arrow.start.x
    if target == "cantilever" and actual_leftward:
        direction = "cantilever_leftward_repulsion"
    elif target == "electrode" and not actual_leftward:
        direction = "electrode_rightward_reaction"
    elif target == "interaction_cue":
        direction = "interaction_cue"
    else:
        direction = "force_target_mismatch"
    v21_contract_ok = target == "cantilever" and actual_leftward
    items = [
        {
            "severity": "evidence" if v21_contract_ok else "possible issue",
            "message": (
                ("intentional v21 divergence retained: " if v21_contract_ok else "")
                + f"probe force vector observed: force_target={target}, leftward={actual_leftward}, "
                f"arrow_direction={direction}; v21 contract expects force_target=cantilever and leftward=True."
            ),
        },
        {
            "severity": "inspect",
            "message": (
                "This report records the known v21 probe-force divergence only; inspect any other reference divergence "
                "manually against scaffold, physics, readability, and causal-clarity reasons before treating it as justified."
            ),
        },
    ]
    return {"name": "Reference Divergence", "items": items}


def _human_review_prompts(categories: list[dict[str, Any]]) -> list[str]:
    prompts: list[str] = []
    used_messages: set[str] = set()
    category_by_name = {category["name"]: category for category in categories}
    priority = (
        "Reference Divergence",
        "Text / Text Near-Collision",
        "Text / Shape Conflict",
        "Visual Hierarchy",
        "Panel Density",
        "Reading Order",
    )

    for name in priority:
        category = category_by_name.get(name)
        if not category:
            continue
        item = _first_prompt_item(category, allow_evidence=name in {"Reference Divergence", "Visual Hierarchy", "Reading Order"})
        if item is None:
            continue
        prompts.append(f"Inspect {name.lower()}: {item['message']}")
        used_messages.add(item["message"])
        if len(prompts) >= 8:
            return prompts

    for name in priority:
        category = category_by_name.get(name)
        if not category:
            continue
        for item in category["items"]:
            if item["message"] in used_messages:
                continue
            if item["severity"] not in {"possible issue", "candidate risk"}:
                continue
            prompts.append(f"Inspect {name.lower()}: {item['message']}")
            used_messages.add(item["message"])
            if len(prompts) >= 8:
                return prompts

    return prompts or ["Inspect the rendered figure visually; this report did not infer a candidate risk."]


def _walk_svg_elements(
    root: ET.Element,
    semantic_id: str = "",
    semantic_kind: str = "",
) -> list[tuple[int, ET.Element, str, str]]:
    records: list[tuple[int, ET.Element, str, str]] = []

    def walk(element: ET.Element, current_id: str, current_kind: str) -> None:
        next_id = element.attrib.get("data-semantic-id", current_id)
        next_kind = element.attrib.get("data-semantic-kind", current_kind)
        records.append((len(records), element, next_id, next_kind))
        for child in list(element):
            walk(child, next_id, next_kind)

    walk(root, semantic_id, semantic_kind)
    return records


def _semantic_role_tags(semantic_id: str, semantic_kind: str) -> list[str]:
    tags = [semantic_kind]
    if semantic_id in PRIMARY_SEMANTIC_IDS:
        tags.append("primary")
    return tags


def _role_tags(element: ET.Element) -> list[str]:
    tags: list[str] = []
    for key in ("data-panel-role", "data-hero-role", "data-plot-role", "data-flow-role", "data-causal-role"):
        value = element.attrib.get(key, "")
        tags.extend(token for token in value.split() if token)
    return sorted(set(tags))


def _shape_has_conflict_role(shape: dict[str, Any]) -> bool:
    tags = " ".join(shape["role_tags"]).lower()
    if any(token in tags for token in SHAPE_CONFLICT_ROLES):
        return True
    if shape["tag"] in {"path", "line", "circle"} and shape.get("semantic_id"):
        return True
    return False


def _is_expected_text_pair(first: dict[str, Any], second: dict[str, Any]) -> bool:
    if frozenset((first["text"], second["text"])) in EXPECTED_COMPOSITE_TEXT_PAIRS:
        return True
    if first["semantic_id"] and first["semantic_id"] == second["semantic_id"]:
        return _looks_like_label_continuation(first, second)
    return False


def _looks_like_label_continuation(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_box = first["bbox"]
    second_box = second["bbox"]
    vertical_gap = _bbox_gap(_bbox_from_record(first_box), _bbox_from_record(second_box))
    horizontal_overlap = min(first_box["right"], second_box["right"]) - max(first_box["left"], second_box["left"])
    return vertical_gap <= 6.0 and horizontal_overlap > 0


def _is_expected_text_shape_pair(text: dict[str, Any], shape: dict[str, Any]) -> bool:
    if text["semantic_id"] and text["semantic_id"] == shape["semantic_id"]:
        return True
    if text["panel_id"] == "macroscopic_probe_card" and text["text"] in PROBE_OWNED_TEXT_LABELS:
        return shape.get("semantic_kind") in {
            "MacroscopicProbe",
            "PolymerCantilever",
            "Electrode",
            "ForceArrow",
            "MaxwellAttractionCue",
        }
    return False


def _first_prompt_item(category: dict[str, Any], *, allow_evidence: bool = False) -> dict[str, str] | None:
    severities = {"possible issue", "candidate risk"}
    if allow_evidence:
        severities.add("evidence")
    for item in category["items"]:
        if item["severity"] in severities:
            return item
    return None


def _merge_invisible_text_role_markers(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    visible_records = [record for record in records if record["visible"]]
    invisible_records = [record for record in records if not record["visible"]]
    visible_by_key: dict[tuple[object, ...], dict[str, Any]] = {
        _text_merge_key(record): record
        for record in visible_records
    }
    for invisible in invisible_records:
        visible = visible_by_key.get(_text_merge_key(invisible))
        if visible is None:
            continue
        visible["role_tags"] = sorted(set(visible["role_tags"]) | set(invisible["role_tags"]))
        if not visible["semantic_id"]:
            visible["semantic_id"] = invisible["semantic_id"]
        if not visible["semantic_kind"]:
            visible["semantic_kind"] = invisible["semantic_kind"]
    for record in visible_records:
        record.pop("visible", None)
    return visible_records


def _text_merge_key(record: dict[str, Any]) -> tuple[object, ...]:
    bbox = record["bbox"]
    return (
        record["panel_id"],
        record["text"],
        record["font_size"],
        round(bbox["left"], 1),
        round(bbox["top"], 1),
        round(bbox["right"], 1),
        round(bbox["bottom"], 1),
    )


def _large_secondary_text_candidates(scene: Scene, text_boxes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hero_panel_id = next(column.id for column in scene.layout.columns if column.role == "hero")
    return [
        text
        for text in text_boxes
        if text["panel_id"] != hero_panel_id
        and text["font_size"] >= 18.0
        and "panel-title-support" not in text["role_tags"]
    ][:4]


def _panel_id_for_bbox(scene: Scene, bbox: BBox) -> str:
    center_x = (bbox.left + bbox.right) / 2
    center_y = (bbox.top + bbox.bottom) / 2
    for column in scene.layout.columns:
        if column.bounds.x <= center_x <= column.bounds.right and column.bounds.y <= center_y <= column.bounds.bottom:
            return column.id
    nearest = min(
        scene.layout.columns,
        key=lambda column: _point_rect_distance(center_x, center_y, column.bounds),
    )
    return nearest.id


def _point_rect_distance(x: float, y: float, rect: Rect) -> float:
    dx = max(rect.x - x, 0.0, x - rect.right)
    dy = max(rect.y - y, 0.0, y - rect.bottom)
    return (dx * dx + dy * dy) ** 0.5


def _bbox_record(bbox: BBox) -> dict[str, float]:
    return {
        "left": round(bbox.left, 3),
        "top": round(bbox.top, 3),
        "right": round(bbox.right, 3),
        "bottom": round(bbox.bottom, 3),
        "width": round(bbox.width, 3),
        "height": round(bbox.height, 3),
    }


def _bbox_from_record(record: dict[str, float]) -> BBox:
    return BBox(record["left"], record["top"], record["right"], record["bottom"])


def _bbox_from_rect(rect: Rect) -> BBox:
    return BBox(rect.x, rect.y, rect.right, rect.bottom)


def _bbox_area(bbox: BBox) -> float:
    return max(bbox.width, 0.0) * max(bbox.height, 0.0)


def _intersection_area(first: BBox, second: BBox) -> float:
    width = max(min(first.right, second.right) - max(first.left, second.left), 0.0)
    height = max(min(first.bottom, second.bottom) - max(first.top, second.top), 0.0)
    return width * height


def _clipped_bbox(first: BBox, second: BBox) -> BBox | None:
    left = max(first.left, second.left)
    top = max(first.top, second.top)
    right = min(first.right, second.right)
    bottom = min(first.bottom, second.bottom)
    if left >= right or top >= bottom:
        return None
    return BBox(left, top, right, bottom)


def _rectangle_union_area(rectangles: list[BBox]) -> float:
    if not rectangles:
        return 0.0
    xs = sorted({value for rect in rectangles for value in (rect.left, rect.right)})
    area = 0.0
    for left, right in zip(xs, xs[1:], strict=False):
        if left == right:
            continue
        intervals = sorted(
            (rect.top, rect.bottom)
            for rect in rectangles
            if rect.left < right and rect.right > left
        )
        covered_y = 0.0
        current_top: float | None = None
        current_bottom: float | None = None
        for top, bottom in intervals:
            if current_top is None:
                current_top = top
                current_bottom = bottom
                continue
            if current_bottom is not None and top <= current_bottom:
                current_bottom = max(current_bottom, bottom)
            else:
                covered_y += (current_bottom or 0.0) - current_top
                current_top = top
                current_bottom = bottom
        if current_top is not None and current_bottom is not None:
            covered_y += current_bottom - current_top
        area += (right - left) * covered_y
    return area


def _bbox_gap(first: BBox, second: BBox) -> float:
    dx = max(second.left - first.right, first.left - second.right, 0.0)
    dy = max(second.top - first.bottom, first.top - second.bottom, 0.0)
    return (dx * dx + dy * dy) ** 0.5


def _is_invisible_shape(element: ET.Element) -> bool:
    fill = element.attrib.get("fill", "")
    stroke = element.attrib.get("stroke", "")
    opacity = element.attrib.get("opacity", "1")
    try:
        if float(opacity) <= 0:
            return True
    except ValueError:
        pass
    return fill == "none" and stroke == "none"


def _float_attr(element: ET.Element, name: str, default: float) -> float:
    try:
        return float(element.attrib.get(name, str(default)))
    except ValueError:
        return default


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _short(value: str, *, limit: int = 34) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def main() -> int:
    report = build_visual_judgment_report(build_scene(), SVG)
    write_visual_judgment_reports(report)
    print(f"fig1 visual judgment report written: {MARKDOWN_OUT}")
    print(f"fig1 visual judgment JSON written: {JSON_OUT}")
    print("report-only visual judgment layer: warnings do not fail Fig1 gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
