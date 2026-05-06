from __future__ import annotations

import importlib
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SVG = ROOT / "fig_probe_01_semantic.svg"
PNG = ROOT / "fig_probe_01_semantic.png"

PROBE_SCENE_MODULE = "fig_probe_01_scene"
PROBE_RENDER_MODULE = "render_fig_probe_01"


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _text(path: Path) -> str:
    return path.read_text()


def _load_scene() -> object:
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    module = importlib.import_module(PROBE_SCENE_MODULE)
    return module.build_scene()


def _probe_file(path: str) -> Path:
    return SRC / path


def _elements_with_role(root: ET.Element, role: str) -> list[ET.Element]:
    return [element for element in root.iter() if role in element.attrib.get("data-probe-role", "").split()]


def _semantic_group(root: ET.Element, semantic_id: str) -> ET.Element | None:
    for element in root.iter():
        if element.attrib.get("data-semantic-id") == semantic_id:
            return element
    return None


def _check_probe_boundary() -> int:
    for path in (_probe_file("fig_probe_01_scene.py"), _probe_file("render_fig_probe_01.py")):
        if not path.exists():
            return _fail(f"missing probe source file: {path}")
        text = _text(path)
        forbidden = ("fig1_l1_scene", "verify_fig1_semantics", "fig1_visual_policies")
        for token in forbidden:
            if token in text:
                return _fail(f"probe source imports or references Fig1-specific module {token}: {path}")
    return 0


def _check_scene_contract(scene: object) -> int:
    if getattr(scene, "id") != "fig_probe_01":
        return _fail(f"unexpected probe scene id: {getattr(scene, 'id', None)}")
    if len(scene.layout.columns) != 3:
        return _fail(f"probe should use exactly three columns: {len(scene.layout.columns)}")
    if any(column.role == "hero" for column in scene.layout.columns):
        return _fail("probe should avoid Fig1 hero/support policy roles")
    for kind in ("BandDiagram", "TrapLevelSet", "DOSLobes", "LayoutFlow"):
        scene.object_by_kind(kind)
    return 0


def _check_rendered_svg(scene: object) -> int:
    if not SVG.exists():
        return _fail(f"missing rendered probe SVG: {SVG}")
    if not PNG.exists():
        return _fail(f"missing rendered probe PNG: {PNG}")
    root = ET.parse(SVG).getroot()
    traps = scene.object_by_kind("TrapLevelSet").payload
    dos = scene.object_by_kind("DOSLobes").payload
    expected_roles = {
        "trap-shallow": len(traps.shallow_positions),
        "trap-deep": len(traps.deep_positions),
        "dos-lobe-shallow": 1,
        "dos-lobe-deep": 1,
        "flow-arrow": len(scene.object_by_kind("LayoutFlow").payload.arrow_pairs),
    }
    for role, count in expected_roles.items():
        found = _elements_with_role(root, role)
        if len(found) < count:
            return _fail(f"probe role count mismatch for {role}: {len(found)} < {count}")
    dos_group = _semantic_group(root, "probe_dos")
    if dos_group is None:
        return _fail("probe DOS semantic group missing")
    if f"data-dos-samples=\"{dos.samples}\"" not in SVG.read_text():
        return _fail("probe DOS lobe path does not expose payload sample count")
    if "data-panel-role" in SVG.read_text():
        return _fail("probe SVG leaked Fig1 panel-role attributes")
    return 0


def main() -> int:
    if _check_probe_boundary():
        return 1
    scene = _load_scene()
    if _check_scene_contract(scene):
        return 1
    if _check_rendered_svg(scene):
        return 1
    print("fig_probe_01 framework contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
