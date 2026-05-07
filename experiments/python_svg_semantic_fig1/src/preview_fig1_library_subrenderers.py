from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import drawsvg as draw

from engine.domain_primitives import PowerLawDecayPlot
from engine.matplotlib_subrenderers import power_law_decay_fragment
from engine.rdkit_subrenderers import s8_ring_fragment
from engine.svg_fragments import wrapped_fragment_svg


OUT_DIR = Path("/tmp/fig1_v27_library_subrenderers")
SVG_OUT = OUT_DIR / "library_subrenderer_spike.svg"
PNG_OUT = OUT_DIR / "library_subrenderer_spike.png"


def build_preview_svg() -> str:
    drawing = draw.Drawing(760, 320)
    drawing.append(draw.Rectangle(0, 0, 760, 320, fill="#ffffff"))
    drawing.append(
        draw.Text(
            "v27 library-backed subrenderer spike",
            18,
            28,
            34,
            fill="#182032",
            font_family="Arial",
        )
    )

    decay = PowerLawDecayPlot(
        title="Current decay",
        model="power_law",
        slope=-0.72,
        log_t_min=-3,
        log_t_max=3,
        log_i_top=0,
        log_i_bottom=-8,
        samples=64,
        label="extract n",
        color="#a81016",
    )

    s8 = s8_ring_fragment(width=150, height=130)
    decay_fragment = power_law_decay_fragment(decay, width=210, height=145)

    drawing.append(
        draw.Text("RDKit S8", 12, 70, 78, fill="#5b6470", font_family="Arial")
    )
    drawing.append(
        draw.Raw(
            wrapped_fragment_svg(
                s8,
                x=40,
                y=95,
                semantic_id="preview_s8_ring",
                kind="SulfurPolymerOrigin",
            )
        )
    )

    drawing.append(
        draw.Text(
            "Matplotlib log decay", 12, 270, 78, fill="#5b6470", font_family="Arial"
        )
    )
    drawing.append(
        draw.Raw(
            wrapped_fragment_svg(
                decay_fragment,
                x=240,
                y=92,
                semantic_id="preview_power_decay",
                kind="PowerLawDecayPlot",
            )
        )
    )

    return drawing.as_svg()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SVG_OUT.write_text(build_preview_svg(), encoding="utf-8")
    converter = shutil.which("rsvg-convert")
    if converter:
        subprocess.run(
            [converter, "-w", "1520", "-h", "640", str(SVG_OUT), "-o", str(PNG_OUT)],
            check=True,
        )
    print(f"wrote {SVG_OUT}")
    if PNG_OUT.exists():
        print(f"wrote {PNG_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
