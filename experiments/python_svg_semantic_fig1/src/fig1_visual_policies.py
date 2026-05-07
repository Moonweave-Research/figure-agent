from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


INTERPRETATION_MAX_STEP_FRAMES = 1
ORIGIN_MAX_BULLET_LABELS = 2
PROBE_MAX_FORCE_LABEL_LINES = 1
REQUIRED_SUPPORT_PANEL_CONCLUSIONS = 4
REQUIRED_GLOBAL_FLOW_ARROWS = 4


def check_fig1_visual_policies(scene: object, svg_path: Path) -> int:
    if not svg_path.exists():
        return _fail(f"missing rendered SVG: {svg_path}")
    root = ET.parse(svg_path).getroot()
    failures: list[str] = []
    failures.extend(_v12_visual_cohesion_failures(root))
    failures.extend(_v13_support_panel_failures(root))
    failures.extend(_v14_global_composition_failures(root))
    if failures:
        return _fail(
            "fig1 visual policy checks failed:\n"
            + "\n".join(f"- {failure}" for failure in failures)
        )
    return 0


def _v12_visual_cohesion_failures(root: ET.Element) -> list[str]:
    failures: list[str] = []

    hero_captions = [
        element
        for element in _panel_role_elements(root, "hero-caption")
        if _text_value(element)
    ]
    if not hero_captions:
        failures.append("hero panel missing v12 restrained caption role")
    elif len(hero_captions) > 2:
        failures.append(
            f"hero caption is too text-dominant: {len(hero_captions)} lines > 2"
        )

    interpretation_group = _semantic_group(root, "trap_model_flow")
    if interpretation_group is None:
        failures.append("interpretation panel missing trap model semantic group")
    else:
        step_frames = [
            element
            for element in interpretation_group.iter()
            if element.tag.rsplit("}", 1)[-1] == "rect"
            and element.attrib.get("fill") == "#f7f9fc"
        ]
        if len(step_frames) > INTERPRETATION_MAX_STEP_FRAMES:
            failures.append(
                f"interpretation flow uses too many boxed UI step frames: {len(step_frames)} > {INTERPRETATION_MAX_STEP_FRAMES}"
            )
    return failures


def _v13_support_panel_failures(root: ET.Element) -> list[str]:
    failures: list[str] = []

    origin_relations = [
        element
        for element in _panel_role_elements(root, "origin-relation")
        if _text_value(element)
    ]
    if not origin_relations:
        failures.append("origin panel missing compact composition relation cue")

    origin_bullets = [
        element
        for element in _panel_role_elements(root, "origin-bullet")
        if _text_value(element)
    ]
    if len(origin_bullets) > ORIGIN_MAX_BULLET_LABELS:
        failures.append(
            f"origin panel remains checklist-dense: {len(origin_bullets)} bullets > {ORIGIN_MAX_BULLET_LABELS}"
        )

    probe_force_labels = [
        element
        for element in _panel_role_elements(root, "probe-force-label")
        if _text_value(element)
    ]
    if not probe_force_labels:
        failures.append("probe panel missing normalized one-line force label")
    elif len(probe_force_labels) > PROBE_MAX_FORCE_LABEL_LINES:
        failures.append(
            f"probe force label is too dominant: {len(probe_force_labels)} lines > {PROBE_MAX_FORCE_LABEL_LINES}"
        )

    probe_group = _semantic_group(root, "macroscopic_probe")
    if probe_group is None:
        failures.append("probe panel missing macroscopic probe semantic group")
    else:
        boxed_footer = [
            element
            for element in probe_group.iter()
            if element.tag.rsplit("}", 1)[-1] == "rect"
            and element.attrib.get("fill") == "#fff8f7"
        ]
        if boxed_footer:
            failures.append("probe panel still uses a boxed footer callout")

    cantilever_group = _semantic_group(root, "polymer_cantilever")
    if cantilever_group is None:
        failures.append("probe panel missing polymer cantilever semantic group")
    else:
        shadowed_parts = [
            element
            for element in cantilever_group.iter()
            if element.attrib.get("filter") == "url(#softInsetShadow)"
        ]
        if shadowed_parts:
            failures.append("probe cantilever still uses heavy inset shadow effects")
    return failures


def _v14_global_composition_failures(root: ET.Element) -> list[str]:
    failures: list[str] = []

    support_titles = _panel_role_elements(root, "panel-title-support")
    hero_titles = _panel_role_elements(root, "panel-title-hero")
    if len(support_titles) < 4:
        failures.append(
            f"support panel titles are not role-tagged consistently: {len(support_titles)} < 4"
        )
    if len(hero_titles) != 1:
        failures.append(
            f"hero panel title role count mismatch: {len(hero_titles)} != 1"
        )

    flow_arrows = _panel_role_elements(root, "global-flow-arrow")
    if len(flow_arrows) < REQUIRED_GLOBAL_FLOW_ARROWS:
        failures.append(
            f"support-to-hero arrows are not globally role-tagged: {len(flow_arrows)} < {REQUIRED_GLOBAL_FLOW_ARROWS}"
        )
    else:
        widths = [
            float(element.attrib.get("stroke-width", "0"))
            for element in flow_arrows
            if element.tag.rsplit("}", 1)[-1] == "line"
        ]
        if widths and max(widths) > 2.0:
            failures.append(
                f"support-to-hero arrows are too visually dominant: max width {max(widths):.2f} > 2.0"
            )

    support_conclusions = [
        element
        for element in _panel_role_elements(root, "panel-conclusion")
        if _text_value(element)
    ]
    if len(support_conclusions) < REQUIRED_SUPPORT_PANEL_CONCLUSIONS:
        failures.append(
            f"support panel conclusion cues are not normalized: {len(support_conclusions)} < {REQUIRED_SUPPORT_PANEL_CONCLUSIONS}"
        )
    return failures


def _panel_role_elements(root: ET.Element, role: str) -> list[ET.Element]:
    return [
        element
        for element in root.iter()
        if role in element.attrib.get("data-panel-role", "").split()
    ]


def _semantic_group(root: ET.Element, semantic_id: str) -> ET.Element | None:
    for element in root.iter():
        if element.attrib.get("data-semantic-id") == semantic_id:
            return element
    return None


def _text_value(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1
