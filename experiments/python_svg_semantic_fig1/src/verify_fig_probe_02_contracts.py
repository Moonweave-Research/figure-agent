from __future__ import annotations

import importlib
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SVG = ROOT / "fig_probe_02_semantic.svg"
PNG = ROOT / "fig_probe_02_semantic.png"


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _load_scene() -> object:
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    return importlib.import_module("fig_probe_02_scene").build_scene()


def _read(path: Path) -> str:
    return path.read_text()


def _role_elements(root: ET.Element, role: str) -> list[ET.Element]:
    return [element for element in root.iter() if role in element.attrib.get("data-probe2-role", "").split()]


def _semantic_groups(root: ET.Element) -> list[ET.Element]:
    return [element for element in root.iter() if element.attrib.get("data-semantic-id")]


def _check_source_boundary() -> int:
    for path in (SRC / "fig_probe_02_scene.py", SRC / "render_fig_probe_02.py"):
        if not path.exists():
            return _fail(f"missing probe 02 source file: {path}")
        text = _read(path)
        for token in ("fig1_l1_scene", "render_fig1_l1", "verify_fig1_semantics", "fig1_visual_policies"):
            if token in text:
                return _fail(f"probe 02 source references Fig1-specific module {token}: {path}")
    return 0


def _check_scene_layout(scene: object) -> int:
    if getattr(scene, "id") != "fig_probe_02":
        return _fail(f"unexpected probe 02 scene id: {getattr(scene, 'id', None)}")
    if (scene.width, scene.height) != (1595, 986):
        return _fail(f"probe 02 should use Fig1-scale canvas: {(scene.width, scene.height)}")
    columns = scene.layout.columns
    if len(columns) != 5:
        return _fail(f"probe 02 should use five panels: {len(columns)}")
    hero_count = sum(1 for column in columns if column.role == "hero")
    support_count = sum(1 for column in columns if column.role == "supporting")
    if hero_count != 1 or support_count != 4:
        return _fail(f"probe 02 layout should be 1 hero + 4 support panels: hero={hero_count} support={support_count}")
    for kind in (
        "SulfurPolymerOrigin",
        "EvidenceTrio",
        "PEHysteresisPlot",
        "PowerLawDecayPlot",
        "BandDiagram",
        "TrapLevelSet",
        "DOSLobes",
        "TrapModelFlow",
        "MacroscopicProbe",
        "PolymerCantilever",
        "Electrode",
        "ForceArrow",
        "LayoutFlow",
    ):
        scene.object_by_kind(kind)
    return 0


def _check_rendered_svg(scene: object) -> int:
    if not SVG.exists():
        return _fail(f"missing rendered probe 02 SVG: {SVG}")
    if not PNG.exists():
        return _fail(f"missing rendered probe 02 PNG: {PNG}")
    svg_text = _read(SVG)
    if "data-panel-role" in svg_text:
        return _fail("probe 02 leaked Fig1 data-panel-role attributes")
    for token in ("fig1_visual_policies", "Fig. 1 |", "source_variant_aesthetic_ref"):
        if token in svg_text:
            return _fail(f"probe 02 leaked Fig1 token into SVG: {token}")

    root = ET.parse(SVG).getroot()
    traps = scene.object_by_kind("TrapLevelSet").payload
    dos = scene.object_by_kind("DOSLobes").payload
    flow = scene.object_by_kind("LayoutFlow").payload
    expected = {
        "panel-frame": 5,
        "panel-title": 5,
        "support-to-center-flow": len(flow.arrow_pairs),
        "composition-swatch": len(scene.object_by_kind("SulfurPolymerOrigin").payload.swatches),
        "trap-shallow": len(traps.shallow_positions),
        "trap-deep": len(traps.deep_positions),
        "dos-lobe-shallow": 1,
        "dos-lobe-deep": 1,
        "readout-step": len(scene.object_by_kind("TrapModelFlow").payload.steps),
        "device-force": 1,
    }
    for role, count in expected.items():
        found = _role_elements(root, role)
        if len(found) < count:
            return _fail(f"probe 02 role count mismatch for {role}: {len(found)} < {count}")
    if len(_semantic_groups(root)) < 12:
        return _fail(f"probe 02 semantic group count too low: {len(_semantic_groups(root))} < 12")
    if f"data-dos-samples=\"{dos.samples}\"" not in svg_text:
        return _fail("probe 02 DOS path does not expose payload sample count")
    return 0


def main() -> int:
    if _check_source_boundary():
        return 1
    scene = _load_scene()
    if _check_scene_layout(scene):
        return 1
    if _check_rendered_svg(scene):
        return 1
    print("fig_probe_02 composition contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
