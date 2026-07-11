"""Generate the geometry-only semantic SVG for the hybrid Panel C pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_svg(inputs: dict) -> str:
    amber = inputs["palette"]["amber"]
    blue = inputs["palette"]["blue"]
    red = inputs["palette"]["red"]
    gray = inputs["palette"]["gray"]
    shallow = inputs["trap_sites"]["shallow"]
    deep = inputs["trap_sites"]["deep"]
    site_circles = "".join(
        f'<circle cx="{x}" cy="{y}" r="9" fill="{color}" stroke="#ffffff" '
        'stroke-width="2"/>'
        for color, sites in ((blue, shallow), (red, deep))
        for x, y in sites
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 400">'
        '<defs><linearGradient id="film.gradient" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#fff4d8"/><stop offset="1" stop-color="{amber}"/>'
        "</linearGradient></defs>"
        '<g id="film.body" data-semantic="true">'
        '<rect x="55" y="105" width="285" height="190" rx="18" fill="#000" opacity="0.16" '
        'transform="translate(7 8)"/>'
        f'<rect x="55" y="105" width="285" height="190" rx="18" fill="url(#film.gradient)" '
        f'stroke="{amber}" stroke-width="4"/>'
        f'<path d="M75 165 C120 130 175 195 225 155 S300 180 325 150" fill="none" '
        f'stroke="{amber}" stroke-width="5" opacity="0.82"/>'
        f'<path d="M75 215 C125 175 175 245 235 205 S295 225 325 195" fill="none" '
        f'stroke="{amber}" stroke-width="5" opacity="0.9"/>'
        f'<path d="M75 262 C120 225 180 282 230 250 S290 270 325 238" fill="none" '
        f'stroke="{amber}" stroke-width="5" opacity="0.82"/>'
        "</g>"
        f'<g id="trap.sites" data-semantic="true">{site_circles}</g>'
        '<g id="energy.references" data-semantic="true">'
        f'<path d="M405 68 V330" stroke="{gray}" stroke-width="3"/>'
        f'<path d="M415 95 H610 M415 145 H610 M415 320 H610" stroke="{gray}" '
        'stroke-width="3" fill="none"/>'
        f'<path d="M415 118 H610" stroke="{gray}" stroke-width="2" '
        'stroke-dasharray="8 7"/>'
        "</g>"
        '<g id="trap.shallow" data-semantic="true">'
        f'<path d="M420 176 C455 135 485 135 520 176 C485 160 455 160 420 176Z" fill="{blue}" '
        'opacity="0.34"/>'
        f'<path d="M465 184 H555 M475 205 H565" stroke="{blue}" stroke-width="8"/>'
        f'<circle cx="505" cy="184" r="9" fill="{blue}"/><circle cx="525" cy="205" r="9" '
        f'fill="{blue}"/></g>'
        '<g id="trap.deep" data-semantic="true">'
        f'<path d="M420 292 C458 225 505 225 550 292 C505 266 458 266 420 292Z" fill="{red}" '
        'opacity="0.34"/>'
        f'<path d="M465 258 H565 M475 286 H575" stroke="{red}" stroke-width="8"/>'
        f'<circle cx="510" cy="258" r="9" fill="{red}"/><circle cx="535" cy="286" r="9" '
        f'fill="{red}"/></g>'
        '<g id="escape.paths" data-semantic="true" fill="none">'
        f'<path d="M565 258 C615 240 620 190 585 160" stroke="{red}" stroke-width="4"/>'
        f'<path d="M575 286 C650 270 655 190 615 155" stroke="{red}" stroke-width="4"/>'
        "</g>"
        "</svg>"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = json.loads(Path(__file__).with_name("fragment_inputs.json").read_text())
    args.output.write_text(build_svg(inputs) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
