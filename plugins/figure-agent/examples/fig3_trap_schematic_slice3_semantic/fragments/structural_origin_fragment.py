"""Generate geometry-only Panel e structural-origin SVG for the Fig3 Slice 3 pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_svg(inputs: dict) -> str:
    teal = inputs["palette"]["teal"]
    amber = inputs["palette"]["amber"]
    blue = inputs["palette"]["blue"]
    chains = "".join(
        f'<path d="M25 {y} C85 {y - 38} 125 {y + 34} 185 {y} '
        f'S285 {y - 34} 345 {y} S455 {y + 34} 555 {y}"/>'
        for y in inputs["chain_y"]
    )
    regions = "".join(
        f'<ellipse cx="{cluster["cx"]}" cy="{cluster["cy"]}" rx="82" ry="55"/>'
        for cluster in inputs["clusters"]
    )
    sulfur_sites = "".join(
        f'<circle cx="{x}" cy="{y}" r="12"/><path d="M{x - 5} {y + 4} h10"/>'
        for cluster in inputs["clusters"]
        for x, y in cluster["sites"]
    )
    trap_levels = "".join(
        f'<path d="M{x + 12} {y + 18} h38"/>'
        for cluster in inputs["clusters"]
        for x, y in cluster["sites"][::2]
    )
    carriers = "".join(
        f'<circle cx="{x + 31}" cy="{y + 18}" r="8"/>'
        for cluster in inputs["clusters"]
        for x, y in cluster["sites"][::2]
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 580 440">'
        f'<g id="chain.backbones" data-semantic="true" fill="none" stroke="{teal}" '
        f'stroke-width="5" stroke-linecap="round">{chains}</g>'
        f'<g id="sulfur.regions" data-semantic="true" fill="{amber}" opacity="0.22">'
        f'{regions}</g>'
        f'<g id="sulfur.sites" data-semantic="true" fill="#fff4d8" stroke="{amber}" '
        f'stroke-width="4">{sulfur_sites}</g>'
        f'<g id="trap.levels" data-semantic="true" fill="none" stroke="{amber}" '
        f'stroke-width="6">{trap_levels}</g>'
        f'<g id="trapped.carriers" data-semantic="true" fill="{blue}" '
        f'stroke="#ffffff" stroke-width="2">{carriers}</g>'
        '</svg>'
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
