from __future__ import annotations

from pathlib import Path

import drawsvg as draw

from stack import drawsvg_helpers as h


WIDTH = 560
HEIGHT = 640
OUT = Path(__file__).resolve().parents[1] / "panel_B_center.svg"


def build_panel() -> draw.Drawing:
    drawing = draw.Drawing(WIDTH, HEIGHT)
    h.card(drawing, WIDTH, HEIGHT, stroke="#ddb9b9", radius=28)
    add_title(drawing)
    add_energy_axis(drawing)
    add_lumo_box(drawing)
    add_homo_box(drawing)
    return drawing


def add_title(drawing: draw.Drawing) -> None:
    drawing.append(
        draw.Rectangle(
            36,
            28,
            WIDTH - 72,
            80,
            rx=14,
            ry=14,
            fill="#fffafa",
            stroke="#efd6d6",
            stroke_width=1.0,
        )
    )
    h.text(
        drawing,
        "Converged deep charge trapping",
        WIDTH / 2,
        80,
        29,
        fill=h.RED,
        weight="700",
        anchor="middle",
    )


def add_energy_axis(drawing: draw.Drawing) -> None:
    h.arrow(drawing, 78, 542, 78, 134, "#111111", width=2.0, head_length=16, head_width=13)
    drawing.append(
        draw.Text(
            "Energy",
            18,
            0,
            0,
            fill="#111111",
            font_family="Helvetica, Arial, sans-serif",
            transform="translate(48 356) rotate(-90)",
            text_anchor="middle",
        )
    )


def add_lumo_box(drawing: draw.Drawing) -> None:
    drawing.append(
        draw.Rectangle(116, 128, 166, 42, rx=5, ry=5, fill="#f1f4f7", stroke="#a8b0ba", stroke_width=1.2)
    )
    h.text(drawing, "LUMO", 199, 156, 23, fill="#111111", weight="700", anchor="middle")


def add_homo_box(drawing: draw.Drawing) -> None:
    drawing.append(
        draw.Rectangle(116, 492, 166, 42, rx=5, ry=5, fill="#f1f4f7", stroke="#a8b0ba", stroke_width=1.2)
    )
    h.text(drawing, "HOMO", 199, 520, 23, fill="#111111", weight="700", anchor="middle")


def main() -> None:
    h.save_svg(build_panel(), OUT)


if __name__ == "__main__":
    main()
