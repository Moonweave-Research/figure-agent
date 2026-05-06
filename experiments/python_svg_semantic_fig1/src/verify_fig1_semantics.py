from __future__ import annotations

import sys
import subprocess
import xml.etree.ElementTree as ET
import json
import re
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
SVG = ROOT / "fig1_reference_semantic.svg"
PNG = ROOT / "fig1_reference_semantic.png"
COMPARISON = ROOT / "reference_vs_fig1_reference_semantic.png"
VISUAL_LAYOUT = ROOT / "visual_layout.yaml"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fig1_visual_policies import check_fig1_visual_policies


REQUIRED_KINDS = {
    "SulfurPolymerOrigin",
    "DeepTrapHero",
    "BandDiagram",
    "TrapLevelSet",
    "DOSLobes",
    "EvidenceTrio",
    "PEHysteresisPlot",
    "PowerLawDecayPlot",
    "ISPDPlot",
    "TrapModelFlow",
    "MacroscopicProbe",
    "PolymerCantilever",
    "Electrode",
    "ForceArrow",
    "MaxwellAttractionCue",
    "LayoutFlow",
}

EVIDENCE_MODALITIES = {"P-E", "I(t)"}
FORBIDDEN_RENDERED_TERMS = (
    "force-balance",
    "force balance",
    "actuator",
    "bidirectional",
    "bidirectional-actuation",
)
PLOT_GRAMMAR_BOUNDS = {
    "pe_hysteresis": "pe_plot",
    "power_law_decay": "decay_plot",
    "ispd_plot": "ispd_plot",
}
PLOT_SCHEMATIC_REQUIRED_ROLES = {
    "pe_hysteresis": ("schematic-axis", "schematic-guide", "schematic-curve", "schematic-label"),
    "power_law_decay": (
        "schematic-axis",
        "schematic-decade-hint",
        "schematic-guide",
        "schematic-curve",
        "schematic-label",
    ),
    "ispd_plot": (
        "schematic-axis",
        "schematic-lobe-shallow",
        "schematic-lobe-deep",
        "schematic-dos-threshold",
        "schematic-dos-depth-guide",
        "schematic-dos-depth-label",
        "schematic-label",
    ),
}
PLOT_FORBIDDEN_REAL_PLOT_ROLES = ("plot-frame", "tick-label", "major-tick", "minor-tick")
PLOT_TEXT_ROLES = ("schematic-label", "schematic-dos-depth-label")
MINI_DOS_MAX_LABELS = 3


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _object_by_kind(scene: object, kind: str) -> object:
    for obj in scene.objects:
        if obj.kind == kind:
            return obj
    raise KeyError(kind)


def _close(actual: float, expected: float, tolerance: float = 0.35) -> bool:
    return abs(actual - expected) <= tolerance


def _load_visual_layout() -> dict[str, object]:
    if not VISUAL_LAYOUT.exists():
        raise FileNotFoundError(VISUAL_LAYOUT)
    return json.loads(VISUAL_LAYOUT.read_text())


def _check_required_kinds(scene: object) -> int:
    kinds = {obj.kind for obj in scene.objects}
    missing = sorted(REQUIRED_KINDS - kinds)
    if missing:
        return _fail(f"missing semantic object kinds: {', '.join(missing)}")
    return 0


def _check_trap_dominance(scene: object) -> int:
    traps = _object_by_kind(scene, "TrapLevelSet").payload
    if len(traps.deep_positions) <= len(traps.shallow_positions):
        return _fail("deep trap count is not greater than shallow trap count")

    lobes = _object_by_kind(scene, "DOSLobes").payload
    width_ratio = lobes.deep_width / lobes.shallow_width
    area_ratio = lobes.deep_area / lobes.shallow_area
    if width_ratio < lobes.min_deep_to_shallow_ratio:
        return _fail(f"deep DOS lobe width ratio too small: {width_ratio:.3f}")
    if area_ratio < lobes.min_deep_to_shallow_ratio:
        return _fail(f"deep DOS lobe area ratio too small: {area_ratio:.3f}")
    return 0


def _check_trap_energy_model(scene: object) -> int:
    band = _object_by_kind(scene, "BandDiagram").payload
    traps = _object_by_kind(scene, "TrapLevelSet").payload
    lobes = _object_by_kind(scene, "DOSLobes").payload

    if traps.energy_reference != "normalized_bandgap_lumo_to_homo":
        return _fail(f"unexpected trap energy reference: {traps.energy_reference}")
    if traps.quantitative_status != "schematic_placeholder_until_fig3_ispd":
        return _fail(f"unexpected trap quantitative status: {traps.quantitative_status}")
    if tuple(round(value, 1) for value in traps.deep_depth_range_ev) != (0.5, 1.0):
        return _fail(f"unexpected deep trap depth range: {traps.deep_depth_range_ev}")

    if not all(band.lumo.y < position < band.homo.y for position in traps.shallow_positions):
        return _fail("shallow trap positions are not inside the HOMO-LUMO gap")
    if not all(band.lumo.y < position < band.homo.y for position in traps.deep_positions):
        return _fail("deep trap positions are not inside the HOMO-LUMO gap")
    if max(traps.shallow_positions) >= min(traps.deep_positions):
        return _fail("deep traps are not deeper than shallow traps relative to LUMO")
    if not (band.lumo.y < lobes.shallow_center_y < lobes.deep_center_y < band.homo.y):
        return _fail("DOS shallow/deep centers do not follow LUMO-to-HOMO energy order")
    return 0


def _check_computed_geometry_models(scene: object) -> int:
    from engine.scientific_geometry import gaussian_lobe_points, pe_hysteresis_points, power_law_loglog_points
    from engine.scene import Point, Rect

    lobes = _object_by_kind(scene, "DOSLobes").payload
    pe = _object_by_kind(scene, "PEHysteresisPlot").payload
    decay = _object_by_kind(scene, "PowerLawDecayPlot").payload
    ispd = _object_by_kind(scene, "ISPDPlot").payload

    if lobes.model != "gaussian_mixture":
        return _fail(f"unexpected DOS model: {lobes.model}")
    if pe.model != "parametric_hysteresis":
        return _fail(f"unexpected P-E model: {pe.model}")
    if decay.model != "power_law_loglog":
        return _fail(f"unexpected decay model: {decay.model}")
    if ispd.model != "gaussian_mixture":
        return _fail(f"unexpected ISPD model: {ispd.model}")

    shallow_profile = gaussian_lobe_points(
        Point(0, 0),
        width=lobes.shallow_width,
        height=lobes.shallow_height,
        samples=lobes.samples,
        upper_sigma=lobes.shallow_sigma[0],
        lower_sigma=lobes.shallow_sigma[1],
    )
    deep_profile = gaussian_lobe_points(
        Point(0, 0),
        width=lobes.deep_width,
        height=lobes.deep_height,
        samples=lobes.samples,
        upper_sigma=lobes.deep_sigma[0],
        lower_sigma=lobes.deep_sigma[1],
    )
    shallow_extent = max(point.x for point in shallow_profile)
    deep_extent = max(point.x for point in deep_profile)
    if deep_extent / shallow_extent < lobes.min_deep_to_shallow_ratio:
        return _fail("computed deep DOS lobe extent is not dominant")
    shallow_area = _profile_area(shallow_profile)
    deep_area = _profile_area(deep_profile)
    if deep_area / shallow_area < lobes.min_deep_to_shallow_ratio:
        return _fail("computed deep DOS lobe area is not dominant")

    pe_points = pe_hysteresis_points(
        Point(0, 0),
        width=pe.loop_width,
        height=pe.loop_height,
        remanence=pe.remanence,
        samples_per_branch=pe.samples_per_branch,
    )
    if len(pe_points) != pe.samples_per_branch * 2:
        return _fail("computed P-E loop sample count mismatch")
    branch_gap = abs(pe_points[pe.samples_per_branch // 2].y - pe_points[pe.samples_per_branch + pe.samples_per_branch // 2].y)
    if branch_gap < pe.loop_height * 0.22:
        return _fail("computed P-E loop lacks remanent branch separation")

    decay_points = power_law_loglog_points(
        Rect(0, 0, 120, 80),
        slope=decay.slope,
        log_t_min=decay.log_t_min,
        log_t_max=decay.log_t_max,
        log_i_top=decay.log_i_top,
        log_i_bottom=decay.log_i_bottom,
        samples=decay.samples,
    )
    if decay.slope >= 0:
        return _fail("power-law decay slope must be negative")
    if not all(decay_points[index].x < decay_points[index + 1].x for index in range(len(decay_points) - 1)):
        return _fail("computed decay points are not monotonic in time")
    if not all(decay_points[index].y <= decay_points[index + 1].y for index in range(len(decay_points) - 1)):
        return _fail("computed decay points do not decay on log-log axes")
    return 0


def _profile_area(points: tuple[object, ...]) -> float:
    return sum((points[index].x + points[index + 1].x) * abs(points[index + 1].y - points[index].y) / 2 for index in range(len(points) - 1))


def _check_reference_visual_layout(scene: object) -> int:
    try:
        layout_data = _load_visual_layout()
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return _fail(f"invalid visual layout contract: {exc}")

    canvas = layout_data["canvas"]
    if (scene.width, scene.height) != (canvas["width"], canvas["height"]):
        return _fail(f"scene canvas does not match visual layout: {scene.width}x{scene.height}")
    if scene.layout.kind != layout_data["target"]:
        return _fail(f"scene layout kind mismatch: {scene.layout.kind}")

    regions = layout_data["regions"]
    columns = scene.layout.columns
    if len(columns) != len(regions):
        return _fail(f"scene region count {len(columns)} != visual layout count {len(regions)}")

    by_region = {region["id"]: region for region in regions}
    for column in columns:
        region = by_region.get(column.id)
        if region is None:
            return _fail(f"scene contains region not in visual layout: {column.id}")
        if column.index != region["index"]:
            return _fail(f"region index mismatch for {column.id}")
        if column.role != region["role"]:
            return _fail(f"region role mismatch for {column.id}")
        if tuple(column.object_ids) != tuple(region["objects"]):
            return _fail(f"region object assignment mismatch for {column.id}")
        expected = region["bounds"]
        found = (column.bounds.x, column.bounds.y, column.bounds.width, column.bounds.height)
        for actual, target in zip(found, expected, strict=True):
            if not _close(actual, target):
                return _fail(f"region bounds mismatch for {column.id}: {found} != {tuple(expected)}")

        expected_boxes = region.get("local_boxes", {})
        actual_boxes = {box.id: box.bounds for box in column.local_boxes}
        if set(actual_boxes) != set(expected_boxes):
            return _fail(f"local layout boxes mismatch for {column.id}: {sorted(actual_boxes)}")
        for box_id, expected_box in expected_boxes.items():
            actual = actual_boxes[box_id]
            absolute_expected = (
                column.bounds.x + expected_box[0],
                column.bounds.y + expected_box[1],
                expected_box[2],
                expected_box[3],
            )
            found_box = (actual.x, actual.y, actual.width, actual.height)
            for found_value, target_value in zip(found_box, absolute_expected, strict=True):
                if not _close(found_value, target_value):
                    return _fail(f"local box bounds mismatch for {column.id}.{box_id}: {found_box}")

    hero_region_id = layout_data["visual_rules"]["hero_region"]
    hero_columns = [column for column in columns if column.role == "hero"]
    if len(hero_columns) != 1 or hero_columns[0].id != hero_region_id:
        return _fail("hero region is not the unique visual-layout hero")
    hero = hero_columns[0].bounds
    canvas_center_x = scene.width / 2
    if abs(hero.center.x - canvas_center_x) > 40:
        return _fail("hero region is not centered in the reference composition")

    polymer = next(column.bounds for column in columns if column.id == "polymer_origin_card")
    electrical = next(column.bounds for column in columns if column.id == "electrical_evidence_card")
    interpretation = next(column.bounds for column in columns if column.id == "interpretation_card")
    probe = next(column.bounds for column in columns if column.id == "macroscopic_probe_card")
    if not (polymer.center.x < hero.center.x < electrical.center.x):
        return _fail("upper support cards do not flank the hero")
    if not (interpretation.center.x < hero.center.x < probe.center.x):
        return _fail("lower support cards do not flank the hero")
    if not (polymer.center.y < hero.center.y and electrical.center.y < hero.center.y):
        return _fail("upper support cards are not above the hero")
    if not (interpretation.center.y > hero.center.y and probe.center.y > hero.center.y):
        return _fail("lower support cards are not below the hero")

    flow = _object_by_kind(scene, "LayoutFlow").payload
    if flow.direction != "support_to_center_hero":
        return _fail(f"layout flow direction mismatch: {flow.direction}")
    if len(flow.arrow_pairs) != len(layout_data["flow_arrows"]):
        return _fail("layout flow arrow count does not match visual layout")
    return 0


def _check_probe_visual_semantics(scene: object) -> int:
    arrow = _object_by_kind(scene, "ForceArrow").payload
    electrode = _object_by_kind(scene, "Electrode").payload
    arrow_dx = arrow.end.x - arrow.start.x
    if arrow_dx <= 0:
        return _fail("reference repulsion arrow is not rightward")
    if electrode.center.x <= arrow.start.x:
        return _fail("reference electrode is not to the right of the repulsion cue")
    if arrow.label != "Coulomb qE":
        return _fail("force arrow is not labeled as Coulomb qE")

    maxwell = _object_by_kind(scene, "MaxwellAttractionCue").payload
    if maxwell.role != "secondary_reference_cue":
        return _fail(f"Maxwell cue role mismatch: {maxwell.role}")
    if maxwell.end.x >= maxwell.start.x:
        return _fail("secondary Maxwell attraction cue is not leftward")
    if maxwell.label != "Maxwell attraction":
        return _fail("secondary Maxwell cue label mismatch")
    return 0


def _check_evidence_trio(scene: object) -> int:
    trio = _object_by_kind(scene, "EvidenceTrio").payload
    modalities = {modality.label for modality in trio.modalities}
    if modalities != EVIDENCE_MODALITIES:
        return _fail(f"evidence trio modalities mismatch: {sorted(modalities)}")
    child_kinds = {modality.object_kind for modality in trio.modalities}
    required = {"PEHysteresisPlot", "PowerLawDecayPlot"}
    if child_kinds != required:
        return _fail(f"evidence trio child kinds mismatch: {sorted(child_kinds)}")
    if _object_by_kind(scene, "ISPDPlot").column != _object_by_kind(scene, "TrapModelFlow").column:
        return _fail("ISPD plot is not grouped with the interpretation model panel")
    return 0


def _check_svg_output(scene: object) -> int:
    if not SVG.exists():
        return _fail(f"missing rendered SVG: {SVG}")
    root = ET.parse(SVG).getroot()
    width = root.attrib.get("width")
    height = root.attrib.get("height")
    view_box = root.attrib.get("viewBox")
    if (width, height, view_box) != (str(scene.width), str(scene.height), f"0 0 {scene.width} {scene.height}"):
        return _fail(f"SVG canvas mismatch: width={width} height={height} viewBox={view_box}")

    svg_text = SVG.read_text()
    lowered = svg_text.lower()

    for obj in scene.objects:
        if f'data-semantic-id="{obj.id}"' not in svg_text:
            return _fail(f"rendered SVG missing semantic id: {obj.id}")
        if f'data-semantic-kind="{obj.kind}"' not in svg_text:
            return _fail(f"rendered SVG missing semantic kind: {obj.kind}")

    for term in FORBIDDEN_RENDERED_TERMS:
        if term in lowered:
            return _fail(f"forbidden framing term rendered: {term}")

    traps = _object_by_kind(scene, "TrapLevelSet").payload
    lobes = _object_by_kind(scene, "DOSLobes").payload
    hero = _object_by_kind(scene, "DeepTrapHero").payload
    pe = _object_by_kind(scene, "PEHysteresisPlot").payload
    decay = _object_by_kind(scene, "PowerLawDecayPlot").payload
    ispd = _object_by_kind(scene, "ISPDPlot").payload
    required_payload_tokens = (
        f"deep_count={len(traps.deep_positions)}",
        f"shallow_count={len(traps.shallow_positions)}",
        f"deep_width={lobes.deep_width:.0f}",
        f"shallow_width={lobes.shallow_width:.0f}",
        f"hero_ratio={hero.hero_ratio:g}",
        f"deep_depth_range_ev={traps.deep_depth_range_ev[0]:.1f}-{traps.deep_depth_range_ev[1]:.1f}",
        f"energy_reference={traps.energy_reference}",
        "direction=support_to_center_hero",
        "arrow_direction=reference_rightward_repulsion",
        "maxwell_role=secondary_reference_cue",
        "local_boxes=6",
        f"dos_model={lobes.model}",
        f"pe_model={pe.model}",
        f"decay_model={decay.model}",
        f"ispd_model={ispd.model}",
    )
    for token in required_payload_tokens:
        if token not in svg_text:
            return _fail(f"rendered SVG missing payload-derived geometry token: {token}")
    return 0


def _check_hero_reference_scaffold(scene: object) -> int:
    if not SVG.exists():
        return _fail(f"missing rendered SVG: {SVG}")
    root = ET.parse(SVG).getroot()
    for role, minimum in _hero_required_roles(scene).items():
        found = _hero_role_elements(root, role)
        if len(found) < minimum:
            return _fail(f"hero reference scaffold missing role {role}: {len(found)} < {minimum}")

    svg_text = SVG.read_text()
    if ">bandgap<" in svg_text:
        return _fail("hero scaffold still renders literal bandgap text instead of a guide line")
    return _check_hero_dos_reference_grammar(scene, root)


def _hero_required_roles(scene: object) -> dict[str, int]:
    traps = _object_by_kind(scene, "TrapLevelSet").payload
    band = _object_by_kind(scene, "BandDiagram").payload
    return {
        "band-edge": len((band.lumo, band.homo)),
        "energy-axis": 1,
        "shallow-trap-state": len(traps.shallow_positions),
        "deep-trap-state": len(traps.deep_positions),
        "trap-track": len(traps.shallow_positions) + len(traps.deep_positions) + 1,
        "dos-axis": 2,
        "dos-lobe-shallow": 1,
        "dos-lobe-deep": 1,
        "dos-label": 1,
        "dos-axis-label": 1,
        "dos-threshold": 1,
        "dos-depth-guide": 2,
        "dos-depth-label": 1,
    }


def _check_hero_dos_reference_grammar(scene: object, root: ET.Element) -> int:
    dos_area = next(column for column in scene.layout.columns if column.role == "hero").box("dos_area")
    shallow = _single_bbox_for_role(root, "dos-lobe-shallow")
    deep = _single_bbox_for_role(root, "dos-lobe-deep")
    threshold = _single_bbox_for_role(root, "dos-threshold")
    depth_guides = [_bbox_from_svg_element(element) for element in _hero_role_elements(root, "dos-depth-guide")]
    labels = [
        bbox
        for role in ("dos-label", "dos-axis-label", "dos-depth-label")
        for bbox in (_bbox_from_svg_element(element) for element in _hero_role_elements(root, role))
        if bbox is not None
    ]

    if shallow is None or deep is None or threshold is None:
        return _fail("hero DOS reference grammar missing lobe or threshold bbox")
    if shallow.bottom > threshold.top + 3.0:
        return _fail("hero DOS shallow lobe overlaps or crosses the threshold guide")
    if deep.top < threshold.bottom - 3.0:
        return _fail("hero DOS deep lobe starts above the threshold guide")
    if deep.right > dos_area.right - 6.0:
        return _fail("hero DOS deep lobe overflows the local DOS area")
    if shallow.right > dos_area.right - 12.0:
        return _fail("hero DOS shallow lobe leaves no label room inside the DOS area")
    if not labels:
        return _fail("hero DOS labels missing bbox markers")
    for label in labels:
        if not _bbox_contains(_rect_bbox(dos_area), label):
            return _fail("hero DOS label escapes the local DOS area")
    label_clearance = _check_hero_dos_label_composition(root, shallow, deep)
    if label_clearance:
        return label_clearance
    if not depth_guides or any(bbox is None for bbox in depth_guides):
        return _fail("hero DOS depth guide missing bbox markers")
    guide_left = min(bbox.left for bbox in depth_guides if bbox is not None)
    if guide_left < deep.right - 10.0:
        return _fail("hero DOS depth guide is not placed to the right of the deep lobe")
    for guide in (bbox for bbox in depth_guides if bbox is not None):
        if _bbox_intersects(guide, _expanded_bbox(deep, 12.0)):
            return _fail("hero DOS depth guide collides with the deep lobe")
    for role in ("dos-lobe-shallow", "dos-lobe-deep"):
        for element in _hero_role_elements(root, role):
            if _sampled_dos_path_score(element) < 20:
                return _fail(f"hero {role} is not a sampled DOS density profile")
            if role == "dos-lobe-deep" and not _deep_dos_lobe_has_tails(element):
                return _fail("hero deep DOS lobe lacks a clear low-density tail at the threshold or band edge")
    return 0


def _check_hero_dos_label_composition(root: ET.Element, shallow: "BBox", deep: "BBox") -> int:
    label_targets = {
        "shallow": shallow,
        "deep": deep,
    }
    for element in _hero_role_elements(root, "dos-label"):
        value = _text_value(element)
        if value not in label_targets:
            continue
        bbox = _bbox_from_svg_element(element)
        if bbox is not None and _bbox_intersects(bbox, _expanded_bbox(label_targets[value], 4.0)):
            return _fail(f"hero DOS {value} label collides with its lobe body")

    for element in _hero_role_elements(root, "dos-depth-label"):
        bbox = _bbox_from_svg_element(element)
        if bbox is not None and _bbox_intersects(bbox, _expanded_bbox(deep, 10.0)):
            return _fail("hero DOS depth label collides with the deep lobe body")
    return 0


def _hero_role_elements(root: ET.Element, role: str) -> list[ET.Element]:
    return [
        element
        for element in root.iter()
        if element.attrib.get("data-hero-role") == role
    ]


def _single_bbox_for_role(root: ET.Element, role: str) -> "BBox | None":
    bboxes = [
        bbox
        for element in _hero_role_elements(root, role)
        for bbox in (_bbox_from_svg_element(element),)
        if bbox is not None
    ]
    if not bboxes:
        return None
    return _union_bboxes(bboxes)


class BBox:
    def __init__(self, left: float, top: float, right: float, bottom: float) -> None:
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom


def _text_value(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _bbox_from_svg_element(element: ET.Element) -> BBox | None:
    tag = element.tag.rsplit("}", 1)[-1]
    if tag == "path":
        values = [float(value) for value in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", element.attrib.get("d", ""))]
        if len(values) < 2:
            return None
        xs = values[0::2]
        ys = values[1::2]
        return BBox(min(xs), min(ys), max(xs), max(ys))
    if tag == "text":
        x = float(element.attrib.get("x", "0"))
        y = float(element.attrib.get("y", "0"))
        size = float(element.attrib.get("font-size", "10"))
        value = "".join(element.itertext())
        width = max(size * 0.6, len(value) * size * 0.55)
        anchor = element.attrib.get("text-anchor", "start")
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        return BBox(x, y - size * 0.9, x + width, y + size * 0.28)
    if tag == "line":
        x1 = float(element.attrib.get("x1", "0"))
        y1 = float(element.attrib.get("y1", "0"))
        x2 = float(element.attrib.get("x2", "0"))
        y2 = float(element.attrib.get("y2", "0"))
        return BBox(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    return None


def _union_bboxes(bboxes: list[BBox]) -> BBox:
    return BBox(
        min(bbox.left for bbox in bboxes),
        min(bbox.top for bbox in bboxes),
        max(bbox.right for bbox in bboxes),
        max(bbox.bottom for bbox in bboxes),
    )


def _rect_bbox(rect: object) -> BBox:
    return BBox(rect.x, rect.y, rect.right, rect.bottom)


def _bbox_contains(outer: BBox, inner: BBox) -> bool:
    return outer.left <= inner.left and inner.right <= outer.right and outer.top <= inner.top and inner.bottom <= outer.bottom


def _expanded_bbox(bbox: BBox, padding: float) -> BBox:
    return BBox(bbox.left - padding, bbox.top - padding, bbox.right + padding, bbox.bottom + padding)


def _bbox_intersects(first: BBox, second: BBox) -> bool:
    return first.left < second.right and first.right > second.left and first.top < second.bottom and first.bottom > second.top


def _check_visual_constraints(scene: object) -> int:
    try:
        from engine.visual_constraints import semantic_bbox_violations
    except ModuleNotFoundError as exc:
        return _fail(f"missing visual constraint layer: {exc}")

    violations = semantic_bbox_violations(scene, SVG)
    if violations:
        return _fail("visual constraint violations:\n" + "\n".join(violations))
    return 0


def _check_scientific_plot_grammar(scene: object) -> int:
    if not SVG.exists():
        return _fail(f"missing rendered SVG: {SVG}")
    root = ET.parse(SVG).getroot()

    for plot_id in PLOT_GRAMMAR_BOUNDS:
        for role in PLOT_FORBIDDEN_REAL_PLOT_ROLES:
            found = _plot_elements(root, plot_id, role)
            if found:
                return _fail(f"{plot_id} uses over-real plot role instead of schematic glyph: {role}")
        for role in PLOT_SCHEMATIC_REQUIRED_ROLES[plot_id]:
            found = _plot_elements(root, plot_id, role)
            if not found:
                return _fail(f"{plot_id} missing schematic plot role: {role}")
        if plot_id == "ispd_plot":
            for role in ("schematic-lobe-shallow", "schematic-lobe-deep"):
                for element in _plot_elements(root, plot_id, role):
                    if _sampled_dos_path_score(element) < 20:
                        return _fail(f"{plot_id} {role} is not a sampled DOS density profile")
                    if role == "schematic-lobe-deep" and not _deep_dos_lobe_has_tails(element):
                        return _fail(f"{plot_id} deep DOS lobe lacks a clear low-density tail")
            mini_composition = _check_mini_dos_label_composition(scene, root)
            if mini_composition:
                return mini_composition

    return _check_plot_label_bounds_via_uv(scene)


def _check_fig1_visual_policies(scene: object) -> int:
    return check_fig1_visual_policies(scene, SVG)


def _plot_elements(root: ET.Element, plot_id: str, role: str) -> list[ET.Element]:
    return [
        element
        for element in root.iter()
        if element.attrib.get("data-plot-id") == plot_id
        and element.attrib.get("data-plot-role") == role
    ]


def _single_plot_bbox_for_role(root: ET.Element, plot_id: str, role: str) -> "BBox | None":
    bboxes = [
        bbox
        for element in _plot_elements(root, plot_id, role)
        for bbox in (_bbox_from_svg_element(element),)
        if bbox is not None
    ]
    if not bboxes:
        return None
    return _union_bboxes(bboxes)


def _check_mini_dos_label_composition(scene: object, root: ET.Element) -> int:
    plot_id = "ispd_plot"
    local_bounds = _rect_bbox(scene.layout.columns[_object_by_kind(scene, "ISPDPlot").column - 1].box(PLOT_GRAMMAR_BOUNDS[plot_id]))
    shallow = _single_plot_bbox_for_role(root, plot_id, "schematic-lobe-shallow")
    deep = _single_plot_bbox_for_role(root, plot_id, "schematic-lobe-deep")
    if shallow is None or deep is None:
        return _fail("mini-DOS schematic missing lobe bbox markers")

    label_bboxes: list[tuple[str, BBox]] = []
    for role in PLOT_TEXT_ROLES:
        for element in _plot_elements(root, plot_id, role):
            value = _text_value(element)
            if not value:
                continue
            bbox = _bbox_from_svg_element(element)
            if bbox is None:
                continue
            label_bboxes.append((value, bbox))
            if not _bbox_contains(local_bounds, bbox):
                return _fail("mini-DOS label escapes local plot bounds")

    if len(label_bboxes) > MINI_DOS_MAX_LABELS:
        return _fail(f"mini-DOS has too many text labels for its box: {len(label_bboxes)} > {MINI_DOS_MAX_LABELS}")

    for value, bbox in label_bboxes:
        if _bbox_intersects(bbox, _expanded_bbox(shallow, 3.0)) or _bbox_intersects(bbox, _expanded_bbox(deep, 3.0)):
            return _fail(f"mini-DOS label overlaps the lobe body: {value}")
    return 0


def _sampled_dos_path_score(element: ET.Element) -> int:
    if element.attrib.get("data-dos-profile") != "payload-sampled-asymmetric":
        return 0
    try:
        samples = int(element.attrib.get("data-dos-samples", "0"))
    except ValueError:
        return 0
    line_count = element.attrib.get("d", "").count(" L")
    return min(samples, line_count)


def _deep_dos_lobe_has_tails(element: ET.Element) -> bool:
    values = [float(value) for value in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", element.attrib.get("d", ""))]
    if len(values) < 8:
        return False
    points = list(zip(values[0::2], values[1::2], strict=False))
    axis_x = min(x for x, _ in points)
    extents = [(x - axis_x, y) for x, y in points]
    peak = max(x for x, _ in extents)
    if peak <= 0:
        return False
    top = min(y for _, y in extents)
    bottom = max(y for _, y in extents)
    height = bottom - top
    top_band = max(x for x, y in extents if y <= top + height * 0.25)
    bottom_band = max(x for x, y in extents if y >= top + height * 0.75)
    return top_band / peak <= 0.62 and bottom_band / peak <= 0.72


def _check_plot_label_bounds_via_uv(scene: object) -> int:
    plot_bounds = {
        plot_id: _plot_bound_values(scene, plot_id)
        for plot_id in PLOT_GRAMMAR_BOUNDS
    }
    script = f"""
import json
import re
import sys
import xml.etree.ElementTree as ET

from shapely.geometry import box
from svgelements import SVG

svg_path = {str(SVG)!r}
plot_bounds = json.loads({json.dumps(plot_bounds)!r})
SVG.parse(svg_path)
root = ET.parse(svg_path).getroot()

def elements(plot_id, role):
    return [
        element for element in root.iter()
        if element.attrib.get("data-plot-id") == plot_id
        and element.attrib.get("data-plot-role") == role
    ]

def local_name(tag):
    return tag.rsplit("}}", 1)[-1]

def text_bbox(element):
    if local_name(element.tag) != "text":
        raise SystemExit("plot label marker is not on text")
    x = float(element.attrib.get("x", "0"))
    y = float(element.attrib.get("y", "0"))
    size = float(element.attrib.get("font-size", "10"))
    value = "".join(element.itertext())
    width = max(size * 0.6, len(value) * size * 0.55)
    anchor = element.attrib.get("text-anchor", "start")
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    return box(x, y - size * 0.9, x + width, y + size * 0.28)

def rect_from_element(element):
    return box(
        float(element.attrib["x"]),
        float(element.attrib["y"]),
        float(element.attrib["x"]) + float(element.attrib["width"]),
        float(element.attrib["y"]) + float(element.attrib["height"]),
    )

for plot_id, values in plot_bounds.items():
    local_bounds = box(*values)
    for role in {PLOT_TEXT_ROLES!r}:
        for label in elements(plot_id, role):
            if not local_bounds.covers(text_bbox(label)):
                raise SystemExit(plot_id + " schematic label escapes local plot bounds")
"""
    result = subprocess.run(
        ["uv", "run", "--with", "shapely", "--with", "svgelements", "python", "-c", script],
        cwd=ROOT.parents[1],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        return _fail((result.stderr or result.stdout).strip())
    return 0


def _plot_bound_values(scene: object, plot_id: str) -> tuple[float, float, float, float]:
    obj = scene.object_by_id(plot_id)
    box_id = PLOT_GRAMMAR_BOUNDS[plot_id]
    bounds = scene.layout.columns[obj.column - 1].box(box_id)
    return (bounds.x, bounds.y, bounds.right, bounds.bottom)


def _check_current_artifacts(scene: object) -> int:
    if getattr(scene.reference, "authority", None) == "ground_truth":
        return _fail("reference PNG must not be marked as ground_truth")

    for path in (PNG, COMPARISON):
        if not path.exists():
            return _fail(f"missing generated artifact: {path}")
        if path.stat().st_size <= 0:
            return _fail(f"generated artifact is empty: {path}")
    return 0


def _check_payload_mutation_changes_output(scene: object) -> int:
    try:
        from render_fig1_l1 import svg_text_for_scene
    except ModuleNotFoundError as exc:
        if exc.name == "drawsvg":
            return _check_payload_mutation_changes_output_via_uv()
        raise

    original_svg = svg_text_for_scene(scene)

    traps = _object_by_kind(scene, "TrapLevelSet")
    lobes = _object_by_kind(scene, "DOSLobes")
    pe = _object_by_kind(scene, "PEHysteresisPlot")
    decay = _object_by_kind(scene, "PowerLawDecayPlot")
    mutations = (
        (traps.id, replace(traps.payload, deep_positions=traps.payload.deep_positions + (traps.payload.deep_positions[-1] + 0.02,))),
        (lobes.id, replace(lobes.payload, deep_width=lobes.payload.deep_width + 18.0, deep_area=lobes.payload.deep_area + 3240.0)),
        (lobes.id, replace(lobes.payload, deep_sigma=(lobes.payload.deep_sigma[0] * 0.82, lobes.payload.deep_sigma[1] * 0.82))),
        (pe.id, replace(pe.payload, remanence=pe.payload.remanence + 0.08)),
        (decay.id, replace(decay.payload, slope=decay.payload.slope - 0.18)),
    )
    for object_id, mutated_payload in mutations:
        mutated_scene = scene.replace_payload(object_id, mutated_payload)
        mutated_svg = svg_text_for_scene(mutated_scene)
        if original_svg == mutated_svg:
            return _fail(f"renderer output did not change after payload mutation: {object_id}")
        if _strip_payload_geometry(original_svg) == _strip_payload_geometry(mutated_svg):
            return _fail(f"visible geometry did not change after payload mutation: {object_id}")

    expected_mutated_count = len(mutations[0][1].deep_positions)
    trap_svg = svg_text_for_scene(scene.replace_payload(traps.id, mutations[0][1]))
    if f"deep_count={expected_mutated_count}" not in trap_svg:
        return _fail("mutated renderer output missing updated deep_count payload token")
    return 0


def _strip_payload_geometry(svg_text: str) -> str:
    return re.sub(r' data-payload-geometry="[^"]*"', "", svg_text)


def _check_payload_mutation_changes_output_via_uv() -> int:
    script = f"""
import sys
import re
from dataclasses import replace
sys.path.insert(0, {str(SRC)!r})
from fig1_l1_scene import build_scene
from render_fig1_l1 import svg_text_for_scene

scene = build_scene()
def strip_payload_geometry(svg_text):
    return re.sub(r' data-payload-geometry="[^"]*"', "", svg_text)

traps = scene.object_by_kind("TrapLevelSet")
lobes = scene.object_by_kind("DOSLobes")
pe = scene.object_by_kind("PEHysteresisPlot")
decay = scene.object_by_kind("PowerLawDecayPlot")
mutations = (
    (traps.id, replace(traps.payload, deep_positions=traps.payload.deep_positions + (traps.payload.deep_positions[-1] + 0.02,))),
    (lobes.id, replace(lobes.payload, deep_width=lobes.payload.deep_width + 18.0, deep_area=lobes.payload.deep_area + 3240.0)),
    (lobes.id, replace(lobes.payload, deep_sigma=(lobes.payload.deep_sigma[0] * 0.82, lobes.payload.deep_sigma[1] * 0.82))),
    (pe.id, replace(pe.payload, remanence=pe.payload.remanence + 0.08)),
    (decay.id, replace(decay.payload, slope=decay.payload.slope - 0.18)),
)
original_svg = svg_text_for_scene(scene)
for object_id, mutated_payload in mutations:
    mutated_svg = svg_text_for_scene(scene.replace_payload(object_id, mutated_payload))
    if original_svg == mutated_svg:
        raise SystemExit("renderer output did not change after payload mutation: " + object_id)
    if strip_payload_geometry(original_svg) == strip_payload_geometry(mutated_svg):
        raise SystemExit("visible geometry did not change after payload mutation: " + object_id)

trap_svg = svg_text_for_scene(scene.replace_payload(traps.id, mutations[0][1]))
if "deep_count=" + str(len(mutations[0][1].deep_positions)) not in trap_svg:
    raise SystemExit("mutated renderer output missing updated deep_count payload token")
"""
    result = subprocess.run(
        ["uv", "run", "--with", "drawsvg", "--with", "matplotlib", "--with", "numpy", "python", "-c", script],
        cwd=ROOT.parents[1],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        return _fail((result.stderr or result.stdout).strip())
    return 0


def main() -> int:
    try:
        from fig1_l1_scene import build_scene
    except ModuleNotFoundError as exc:
        return _fail(f"missing scene module: {exc}")

    scene = build_scene()
    checks = (
        _check_required_kinds,
        _check_trap_dominance,
        _check_trap_energy_model,
        _check_computed_geometry_models,
        _check_reference_visual_layout,
        _check_probe_visual_semantics,
        _check_evidence_trio,
        _check_svg_output,
        _check_hero_reference_scaffold,
        _check_scientific_plot_grammar,
        _check_fig1_visual_policies,
        _check_visual_constraints,
        _check_current_artifacts,
        _check_payload_mutation_changes_output,
    )
    for check in checks:
        result = check(scene)
        if result:
            return result

    print("fig1 semantic contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
