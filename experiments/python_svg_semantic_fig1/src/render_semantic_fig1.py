from __future__ import annotations

from pathlib import Path

import drawsvg as draw

from fig1_scene import build_scene
from semantic_scene import Panel, Scene
from stack import drawsvg_helpers as h
from stack.dvisvgm_math import math_svg


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "semantic_fig1.svg"


def build_drawing(scene: Scene) -> draw.Drawing:
    drawing = draw.Drawing(scene.width, scene.height)
    drawing.append(draw.Rectangle(0, 0, scene.width, scene.height, fill="#ffffff"))
    drawing.append(h.style_defs())
    draw_layout_flow(drawing, scene)
    draw_cards(drawing, scene)
    draw_polymer_origin(drawing, scene)
    draw_deep_trap_hero(drawing, scene)
    draw_electrical_evidence(drawing, scene)
    draw_trap_model(drawing, scene)
    draw_macroscopic_probe(drawing, scene)
    return drawing


def draw_cards(drawing: draw.Drawing, scene: Scene) -> None:
    for panel in scene.panels:
        stroke = "#d9a9a9" if panel.role == "hero" else "#e0e4ea"
        stroke_width = 2.0 if panel.role == "hero" else 1.2
        h.rounded_rect(
            drawing,
            panel.bounds.x,
            panel.bounds.y,
            panel.bounds.width,
            panel.bounds.height,
            fill="url(#cardShade)",
            stroke=stroke,
            radius=28,
            stroke_width=stroke_width,
            filter_="url(#cardShadow)",
        )


def draw_layout_flow(drawing: draw.Drawing, scene: Scene) -> None:
    drawing.append(h.semantic_marker("layout_flow"))
    hero = scene.panel_by_id("trap_hero_card").bounds
    arrows = [
        ((488, 154), (535, 196)),
        ((1066, 154), (1022, 196)),
        ((505, 724), (545, 681)),
        ((1050, 724), (1012, 681)),
    ]
    for start, end in arrows:
        h.arrow(drawing, *start, *end, "#9b9fa5", width=6.0, head_length=22, head_width=18, opacity=0.72)
    h.rounded_rect(
        drawing,
        hero.x - 1,
        hero.y - 1,
        hero.width + 2,
        hero.height + 2,
        fill="none",
        stroke="#edd5d5",
        radius=28,
        stroke_width=1.2,
        opacity=0.45,
    )


def draw_panel_icon(drawing: draw.Drawing, panel: Panel, kind: str) -> None:
    x, y = panel.bounds.x + 26, panel.bounds.y + 22
    h.rounded_rect(drawing, x, y, 44, 44, fill="#12366e", stroke="#0a203f", radius=4, stroke_width=1.1)
    if kind == "molecule":
        for cx, cy in [(x + 22, y + 14), (x + 14, y + 25), (x + 30, y + 25), (x + 22, y + 34)]:
            drawing.append(draw.Circle(cx, cy, 4.6, fill="#ffffff", opacity=0.88))
        drawing.append(draw.Line(x + 22, y + 14, x + 14, y + 25, stroke="#ffffff", stroke_width=1.4))
        drawing.append(draw.Line(x + 22, y + 14, x + 30, y + 25, stroke="#ffffff", stroke_width=1.4))
        drawing.append(draw.Line(x + 22, y + 34, x + 14, y + 25, stroke="#ffffff", stroke_width=1.4))
        drawing.append(draw.Line(x + 22, y + 34, x + 30, y + 25, stroke="#ffffff", stroke_width=1.4))
    elif kind == "wave":
        path = draw.Path(fill="none", stroke="#ffffff", stroke_width=2.0)
        path.M(x + 8, y + 28)
        path.C(x + 14, y + 8, x + 20, y + 8, x + 26, y + 28)
        path.C(x + 30, y + 38, x + 35, y + 31, x + 38, y + 26)
        drawing.append(path)
        drawing.append(draw.Circle(x + 35, y + 14, 3, fill="#ffffff"))
        drawing.append(draw.Circle(x + 35, y + 31, 3, fill="#ffffff"))
    elif kind == "brain":
        drawing.append(draw.Circle(x + 17, y + 23, 13, fill="#eef5fb", stroke="#ffffff", stroke_width=1.3))
        drawing.append(draw.Circle(x + 28, y + 23, 13, fill="#eef5fb", stroke="#ffffff", stroke_width=1.3))
        drawing.append(draw.Line(x + 22.5, y + 11, x + 22.5, y + 35, stroke="#12366e", stroke_width=1.1))
    elif kind == "probe":
        drawing.append(draw.Rectangle(x + 7, y + 31, 34, 4, fill="#ffffff"))
        drawing.append(draw.Rectangle(x + 16, y + 11, 28, 9, fill="#b8c3d1", transform=f"rotate(-31 {x + 16} {y + 11})"))
        drawing.append(draw.Line(x + 20, y + 37, x + 20, y + 44, stroke="#ffffff", stroke_width=1.4))


def draw_polymer_origin(drawing: draw.Drawing, scene: Scene) -> None:
    drawing.append(h.semantic_marker("polymer_origin"))
    panel = scene.panel_by_id("polymer_card")
    x, y = panel.bounds.x, panel.bounds.y
    draw_panel_icon(drawing, panel, "molecule")
    h.multiline_text(drawing, ["Sulfur polymer origin", "(composition tuning)"], x + 86, y + 40, 21, 26, fill=h.BLUE, weight="700")

    center = (x + 76, y + 137)
    ring = [(center[0] + 55 * __import__("math").cos(i * 3.14159 / 3), center[1] + 55 * __import__("math").sin(i * 3.14159 / 3)) for i in range(6)]
    for i, (x1, y1) in enumerate(ring):
        x2, y2 = ring[(i + 1) % len(ring)]
        drawing.append(draw.Line(x1, y1, x2, y2, stroke="#b68111", stroke_width=2.0))
    for atom in ring:
        h.sulfur_atom(drawing, *atom, r=7.2)
    h.text(drawing, "S8", x + 60, y + 204, 18, fill=h.INK)

    h.arrow(drawing, x + 134, y + 130, x + 208, y + 130, "#111111", width=1.5, head_length=12, head_width=9)
    h.text(drawing, "Δ", x + 158, y + 116, 19, fill=h.INK)

    chain_points = [(x + 222, y + 138), (x + 250, y + 121), (x + 278, y + 140), (x + 307, y + 122), (x + 337, y + 141), (x + 366, y + 123), (x + 396, y + 144)]
    for (x1, y1), (x2, y2) in zip(chain_points, chain_points[1:]):
        drawing.append(draw.Line(x1, y1, x2, y2, stroke="#a3680d", stroke_width=2.0))
    for atom in chain_points[1:-1]:
        h.sulfur_atom(drawing, *atom, r=6.5)
    h.text(drawing, "Sx", x + 420, y + 168, 18, fill=h.INK)

    drawing.append(draw.Rectangle(x + 76, y + 230, 322, 14, fill="url(#sulfurRamp)", stroke="#8d6414", stroke_width=1.0))
    h.arrow(drawing, x + 390, y + 237, x + 420, y + 237, h.RED_MID, width=13, head_length=24, head_width=28)
    h.text(drawing, "S60", x + 34, y + 244, 18, fill=h.INK)
    h.text(drawing, "S85", x + 411, y + 244, 18, fill=h.INK)
    h.text(drawing, "Increasing sulfur content", x + 152, y + 269, 15, fill=h.INK, italic=True)

    bullets = ["Higher sulfur fraction", "Longer S-S sequences", "More deep trapping sites"]
    for index, bullet in enumerate(bullets):
        yy = y + 314 + index * 28
        h.text(drawing, "✓", x + 70, yy, 20, fill=h.AMBER_DARK, weight="700")
        h.text(drawing, bullet, x + 100, yy, 16, fill=h.INK, italic=True)


def draw_deep_trap_hero(drawing: draw.Drawing, scene: Scene) -> None:
    drawing.append(h.semantic_marker("deep_trap_hero"))
    panel = scene.panel_by_id("trap_hero_card")
    x, y = panel.bounds.x, panel.bounds.y
    h.text(drawing, "Converged deep charge trapping", x + panel.bounds.width / 2, y + 51, 27, fill=h.RED, weight="700", anchor="middle")
    h.arrow(drawing, x + 44, y + 438, x + 44, y + 90, "#111111", width=1.7, head_length=13, head_width=10)
    drawing.append(draw.Text("Energy", 17, 0, 0, fill=h.INK, font_family="Helvetica, Arial, sans-serif", transform=f"translate({x + 30} {y + 292}) rotate(-90)", text_anchor="middle"))

    h.rounded_rect(drawing, x + 62, y + 94, 148, 42, fill="#f2f3f5", stroke="#aab0b8", radius=4)
    h.text(drawing, "LUMO", x + 136, y + 122, 20, fill=h.INK, weight="700", anchor="middle")
    h.rounded_rect(drawing, x + 62, y + 416, 148, 42, fill="#f2f3f5", stroke="#aab0b8", radius=4)
    h.text(drawing, "HOMO", x + 136, y + 444, 20, fill=h.INK, weight="700", anchor="middle")

    h.multiline_text(drawing, ["shallow", "states"], x + 64, y + 178, 18, 24, fill=h.BLUE_MID, italic=True)
    for yy in [y + 178, y + 199, y + 220]:
        drawing.append(draw.Line(x + 132, yy, x + 202, yy, stroke=h.BLUE_MID, stroke_width=3))
    h.multiline_text(drawing, ["deep", "states"], x + 65, y + 300, 18, 24, fill=h.RED, italic=True)
    for index, yy in enumerate([y + 253, y + 270, y + 288, y + 306, y + 324, y + 342, y + 360, y + 378]):
        drawing.append(draw.Line(x + 132, yy, x + 202, yy, stroke=h.RED, stroke_width=3.1 + index * 0.06))
    drawing.append(draw.Line(x + 112, y + 240, x + 404, y + 240, stroke="#555555", stroke_width=1.1, stroke_dasharray="7 7"))

    h.text(drawing, "DOS", x + 272, y + 122, 18, fill=h.INK)
    drawing.append(math_svg(r"g(E_t)", x=x + 320, y=y + 104, width=64, prefix="hero_g_label"))
    h.mini_axis(drawing, x + 258, y + 137, 155, 288)
    shallow = draw.Path(fill=h.BLUE_LIGHT, stroke=h.BLUE_MID, stroke_width=2.0, opacity=0.92)
    shallow.M(x + 258, y + 154)
    shallow.C(x + 300, y + 169, x + 300, y + 190, x + 258, y + 205)
    shallow.Z()
    drawing.append(shallow)
    deep = draw.Path(fill="#d78383", stroke=h.RED, stroke_width=2.0, opacity=0.78)
    deep.M(x + 258, y + 236)
    deep.C(x + 345, y + 280, x + 382, y + 324, x + 338, y + 358)
    deep.C(x + 304, y + 386, x + 278, y + 405, x + 258, y + 420)
    deep.Z()
    drawing.append(deep)
    h.text(drawing, "shallow", x + 342, y + 192, 17, fill=h.BLUE_MID, italic=True)
    h.text(drawing, "deep", x + 368, y + 348, 17, fill=h.RED, italic=True)
    h.arrow(drawing, x + 406, y + 240, x + 406, y + 318, h.INK, width=1.2, head_length=9, head_width=7)
    h.arrow(drawing, x + 406, y + 318, x + 406, y + 240, h.INK, width=1.2, head_length=9, head_width=7)
    drawing.append(math_svg(r"E_t", x=x + 356, y=y + 260, width=26, prefix="hero_et_symbol"))
    h.text(drawing, "~ 0.5-1.0 eV", x + 384, y + 276, 13, fill=h.INK)

    h.rounded_rect(drawing, x + 30, y + 490, 414, 102, fill="#fff5f3", stroke="#eed2cd", radius=9)
    h.multiline_text(
        drawing,
        ["Deep states dominate the trap landscape", "near midgap, driving the long-lived", "repulsive response."],
        x + 237,
        y + 522,
        20,
        29,
        fill=h.RED,
        italic=True,
        anchor="middle",
    )


def draw_electrical_evidence(drawing: draw.Drawing, scene: Scene) -> None:
    drawing.append(h.semantic_marker("electrical_evidence"))
    panel = scene.panel_by_id("electrical_card")
    x, y = panel.bounds.x, panel.bounds.y
    draw_panel_icon(drawing, panel, "wave")
    h.text(drawing, "Electrical evidence", x + 96, y + 54, 22, fill=h.BLUE, weight="700")
    h.text(drawing, "P-E response", x + 56, y + 106, 16, fill=h.INK)
    px, py = x + 44, y + 135
    h.mini_axis(drawing, px, py, 160, 180)
    drawing.append(draw.Line(px - 22, py + 104, px + 146, py + 104, stroke="#555555", stroke_dasharray="6 6"))
    drawing.append(draw.Line(px + 58, py + 18, px + 58, py + 188, stroke="#555555", stroke_dasharray="6 6"))
    loop1 = draw.Path(fill="none", stroke=h.RED_MID, stroke_width=2.0)
    loop1.M(px - 12, py + 185)
    loop1.C(px + 42, py + 158, px + 24, py + 58, px + 130, py + 44)
    loop1.C(px + 52, py + 64, px + 72, py + 161, px - 12, py + 185)
    drawing.append(loop1)
    h.text(drawing, "P", px - 26, py + 10, 15, fill=h.INK, italic=True)
    h.text(drawing, "E", px + 145, py + 122, 15, fill=h.INK, italic=True)

    h.text(drawing, "Current decay", x + 322, y + 106, 16, fill=h.BLUE)
    qx, qy = x + 277, y + 143
    h.mini_axis(drawing, qx, qy, 205, 198)
    for index, label in enumerate(["10^-3", "10^-1", "10^1", "10^3"]):
        xx = qx + 5 + index * 60
        drawing.append(draw.Line(xx, qy + 198, xx, qy + 204, stroke=h.INK, stroke_width=0.7))
        h.text(drawing, label, xx, qy + 222, 11, fill=h.INK, anchor="middle")
    for index, label in enumerate(["10^0", "10^-2", "10^-4", "10^-6", "10^-8", "10^-10"]):
        yy = qy + 10 + index * 35
        drawing.append(draw.Line(qx - 6, yy, qx, yy, stroke=h.INK, stroke_width=0.7))
        h.text(drawing, label, qx - 10, yy + 4, 10, fill=h.INK, anchor="end")
    drawing.append(draw.Line(qx + 15, qy + 18, qx + 196, qy + 184, stroke=h.BLUE_MID, stroke_width=2.1))
    drawing.append(draw.Path(d=f"M {qx + 84} {qy + 64} L {qx + 84} {qy + 132} L {qx + 136} {qy + 132}", fill="none", stroke=h.BLUE_MID, stroke_width=1.4, stroke_dasharray="7 7"))
    drawing.append(math_svg(r"I(t)\propto t^{-n}", x=qx + 112, y=qy + 44, width=90, prefix="evidence_it", color=h.BLUE_MID))
    h.text(drawing, "slope = -n", qx + 50, qy + 160, 14, fill=h.BLUE_MID, italic=True)
    h.text(drawing, "t (s)", qx + 100, qy + 250, 15, fill=h.INK, italic=True, anchor="middle")
    drawing.append(draw.Text("I (A)", 14, 0, 0, fill=h.INK, font_family="Helvetica, Arial, sans-serif", transform=f"translate({qx - 54} {qy + 110}) rotate(-90)", text_anchor="middle"))


def draw_trap_model(drawing: draw.Drawing, scene: Scene) -> None:
    drawing.append(h.semantic_marker("trap_model"))
    panel = scene.panel_by_id("model_card")
    x, y = panel.bounds.x, panel.bounds.y
    draw_panel_icon(drawing, panel, "brain")
    h.text(drawing, "Interpretation (converged trap model)", x + 86, y + 50, 18, fill=h.BLUE, weight="700")
    flow = [
        (x + 24, y + 86, 98, 45, r"I(t)\propto t^{-n}", h.BLUE_MID, 80),
        (x + 154, y + 82, 90, 58, r"\mathrm{Debye}\ e^{-t/\tau}", h.INK, 68),
        (x + 278, y + 86, 72, 45, r"\tau_d", h.INK, 42),
        (x + 386, y + 86, 74, 45, r"g(E_t)", h.INK, 52),
    ]
    for index, (fx, fy, fw, fh, label, color, width) in enumerate(flow):
        h.rounded_rect(drawing, fx, fy, fw, fh, fill="#f8fbff" if index == 0 else "#f7f7f7", stroke="#9eb3d0" if index == 0 else "#adb3bb", radius=5)
        drawing.append(math_svg(label, x=fx + (fw - width) / 2, y=fy + 14, width=width, prefix=f"model_flow_{index}", color=color))
    for x1, x2 in [(x + 126, x + 152), (x + 248, x + 276), (x + 354, x + 384)]:
        h.arrow(drawing, x1, y + 108, x2, y + 108, "#6e747b", width=1.5, head_length=10, head_width=8)
    _draw_decay_plot(drawing, x + 62, y + 190, small=True)
    _draw_dos_plot(drawing, x + 348, y + 190, small=True)
    h.rounded_rect(drawing, x + 24, y + 374, 426, 82, fill="#f7fbff", stroke="#d8e2ef", radius=8)
    h.multiline_text(drawing, ["Convergence to deep traps (τd) explains the", "extended repulsion."], x + 237, y + 408, 17, 29, fill=h.BLUE, anchor="middle")


def draw_macroscopic_probe(drawing: draw.Drawing, scene: Scene) -> None:
    drawing.append(h.semantic_marker("macroscopic_probe"))
    panel = scene.panel_by_id("probe_card")
    x, y = panel.bounds.x, panel.bounds.y
    draw_panel_icon(drawing, panel, "probe")
    h.text(drawing, "Macroscopic probe", x + 82, y + 51, 22, fill=h.BLUE, weight="700")
    h.text(drawing, "Cantilever", x + 52, y + 94, 14, fill=h.INK)
    h.text(drawing, "(probe)", x + 61, y + 116, 14, fill=h.INK)
    h.rounded_rect(drawing, x + 134, y + 86, 70, 20, fill="url(#metalSheen)", stroke="#56606d", radius=2)
    h.rounded_rect(drawing, x + 145, y + 108, 34, 28, fill="#6b7480", stroke="#444e5a", radius=1)
    for yy in [y + 119, y + 158]:
        drawing.append(draw.Line(x + 122, yy, x + 158, yy, stroke=h.INK, stroke_width=1.4))
        drawing.append(draw.Line(x + 132, yy + 8, x + 149, yy + 8, stroke=h.INK, stroke_width=1.4))
        drawing.append(draw.Line(x + 138, yy + 16, x + 144, yy + 16, stroke=h.INK, stroke_width=1.4))

    beam_shadow = draw.Path(fill="none", stroke="#132033", stroke_width=34, stroke_linecap="round", opacity=0.12)
    beam_shadow.M(x + 160, y + 120)
    beam_shadow.C(x + 150, y + 202, x + 178, y + 278, x + 270, y + 348)
    drawing.append(beam_shadow)
    beam = draw.Path(fill="none", stroke="url(#polymerBeam)", stroke_width=30, stroke_linecap="round")
    beam.M(x + 160, y + 120)
    beam.C(x + 150, y + 202, x + 178, y + 278, x + 270, y + 348)
    drawing.append(beam)
    grain = draw.Path(fill="none", stroke="url(#beamGrain)", stroke_width=25, stroke_linecap="round", opacity=0.55)
    grain.M(x + 160, y + 120)
    grain.C(x + 150, y + 202, x + 178, y + 278, x + 270, y + 348)
    drawing.append(grain)
    for cx, cy in [(x + 166, y + 152), (x + 174, y + 184), (x + 188, y + 231), (x + 214, y + 278), (x + 247, y + 313), (x + 275, y + 336)]:
        h.minus_charge(drawing, cx, cy, r=10)
    drawing.append(draw.Rectangle(x + 410, y + 86, 34, 270, fill="url(#metalSheen)", stroke="#3f4b59", stroke_width=1.2))
    for yy in range(int(y + 118), int(y + 330), 34):
        drawing.append(draw.Line(x + 414, yy, x + 438, yy, stroke="#ffffff", stroke_width=1.0, opacity=0.72))
    h.text(drawing, "+ V", x + 452, y + 137, 16, fill=h.RED_MID)
    for cy in [y + 164, y + 218, y + 275]:
        path = draw.Path(fill="none", stroke="#b9c0c8", stroke_width=1.3, stroke_dasharray="8 8", opacity=0.78)
        path.M(x + 206, cy)
        path.C(x + 260, cy + 32, x + 314, cy + 34, x + 376, cy + 12)
        drawing.append(path)
    h.arrow(drawing, x + 312, y + 198, x + 394, y + 198, h.RED_MID, width=16, head_length=29, head_width=32)
    h.multiline_text(drawing, ["Repulsion", "force"], x + 334, y + 145, 18, 22, fill=h.RED, weight="700", italic=True)
    h.arrow(drawing, x + 342, y + 252, x + 294, y + 252, h.BLUE_MID, width=7, head_length=18, head_width=18, opacity=0.75)
    h.multiline_text(drawing, ["Maxwell", "attraction"], x + 314, y + 288, 16, 20, fill=h.BLUE_MID)
    h.rounded_rect(drawing, x + 28, y + 374, 466, 72, fill="#fff5f3", stroke="#eed2cd", radius=8)
    h.text(drawing, "Charge-trapping-induced repulsion", x + 260, y + 408, 18, fill=h.RED, weight="700", italic=True, anchor="middle")
    h.text(drawing, "Repulsion", x + 92, y + 433, 16, fill=h.INK)
    h.text(drawing, "dominates", x + 173, y + 433, 16, fill=h.RED, weight="700")
    h.text(drawing, "over Maxwell attraction.", x + 263, y + 433, 16, fill=h.INK)


def _draw_decay_plot(drawing: draw.Drawing, x: float, y: float, *, small: bool = False) -> None:
    width = 150 if small else 180
    height = 180 if small else 220
    h.mini_axis(drawing, x, y, width, height)
    drawing.append(draw.Line(x + 16, y + 18, x + width - 16, y + height - 20, stroke=h.BLUE_MID, stroke_width=2.0))
    drawing.append(draw.Line(x + 52, y + 62, x + 52, y + height - 28, stroke=h.BLUE_MID, stroke_width=1.2, stroke_dasharray="6 6"))
    drawing.append(draw.Line(x + 52, y + height - 28, x + 122, y + height - 28, stroke=h.BLUE_MID, stroke_width=1.2, stroke_dasharray="6 6"))
    drawing.append(math_svg(r"I(t)\propto t^{-n}", x=x + 66, y=y + 55, width=92, prefix=f"decay_{int(x)}_{int(y)}", color=h.BLUE_MID))
    h.text(drawing, "slope = -n", x + 18, y + height - 45, 13, fill=h.BLUE_MID, italic=True)
    h.text(drawing, "t (s)", x + width / 2, y + height + 30, 13, fill=h.INK, italic=True, anchor="middle")
    drawing.append(draw.Text("I(t)", 13, 0, 0, fill=h.INK, font_family="Helvetica, Arial, sans-serif", transform=f"translate({x - 34} {y + 86}) rotate(-90)", text_anchor="middle"))


def _draw_dos_plot(drawing: draw.Drawing, x: float, y: float, *, small: bool = False) -> None:
    h.mini_axis(drawing, x, y, 96, 178)
    shallow = draw.Path(fill=h.BLUE_LIGHT, stroke=h.BLUE_MID, stroke_width=1.7, opacity=0.95)
    shallow.M(x, y + 20)
    shallow.C(x + 36, y + 34, x + 34, y + 55, x, y + 68)
    shallow.Z()
    drawing.append(shallow)
    deep = draw.Path(fill="#d78383", stroke=h.RED, stroke_width=1.7, opacity=0.82)
    deep.M(x, y + 76)
    deep.C(x + 56, y + 96, x + 70, y + 126, x + 40, y + 148)
    deep.C(x + 18, y + 162, x + 7, y + 170, x, y + 176)
    deep.Z()
    drawing.append(deep)
    h.text(drawing, "shallow", x + 42, y + 45, 13, fill=h.BLUE_MID, italic=True)
    h.text(drawing, "deep", x + 58, y + 164, 13, fill=h.RED, italic=True)
    drawing.append(draw.Line(x + 18, y + 86, x + 88, y + 86, stroke="#555555", stroke_width=1.0, stroke_dasharray="5 5"))
    h.arrow(drawing, x + 88, y + 86, x + 88, y + 152, h.INK, width=1.0, head_length=8, head_width=6)
    h.arrow(drawing, x + 88, y + 152, x + 88, y + 86, h.INK, width=1.0, head_length=8, head_width=6)
    drawing.append(math_svg(r"E_t", x=x + 96, y=y + 108, width=26, prefix=f"dos_et_{int(x)}_{int(y)}"))
    drawing.append(math_svg(r"g(E_t)", x=x + 35, y=y + 186, width=54, prefix=f"dos_g_{int(x)}_{int(y)}"))
    drawing.append(draw.Text("Energy", 13, 0, 0, fill=h.INK, font_family="Helvetica, Arial, sans-serif", transform=f"translate({x - 24} {y + 92}) rotate(-90)", text_anchor="middle"))


def main() -> None:
    h.save_svg(build_drawing(build_scene()), OUT)


if __name__ == "__main__":
    main()
