from __future__ import annotations

import re

from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D

from engine.svg_fragments import SvgFragment, prefix_svg_ids, strip_outer_svg


_VIEWBOX_RE = re.compile(r"""viewBox=["']([^"']+)["']""")


def s8_ring_fragment(*, width: float, height: float) -> SvgFragment:
    mol = Chem.MolFromSmiles("S1SSSSSSS1")
    if mol is None:
        raise RuntimeError("RDKit failed to parse S8 ring SMILES")
    rdDepictor.Compute2DCoords(mol)
    drawer = rdMolDraw2D.MolDraw2DSVG(int(width), int(height))
    options = drawer.drawOptions()
    options.clearBackground = False
    options.bondLineWidth = 1.6
    options.fixedFontSize = 13
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol, legend="")
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    view_box = _view_box(svg)
    inner = prefix_svg_ids(strip_outer_svg(svg), "fig1_rdkit_s8")
    return SvgFragment(inner_svg=inner, view_box=view_box, width=width, height=height, subrenderer="rdkit", role="origin-s8-ring")


def _view_box(svg_text: str) -> str:
    match = _VIEWBOX_RE.search(svg_text)
    if not match:
        return "0 0 100 100"
    return match.group(1)
