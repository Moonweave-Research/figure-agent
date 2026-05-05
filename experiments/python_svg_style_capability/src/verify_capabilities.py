from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "style_capability.svg"

REQUIRED_TOKENS = {
    "linearGradient": "linear gradient definition",
    "radialGradient": "radial gradient definition",
    "filter": "SVG filter definition",
    "clipPath": "clip path definition",
    "mask": "mask definition",
    "pattern": "pattern definition",
    "<svg x=": "nested SVG content",
    "dvisvgm": "dvisvgm math provenance",
}


def main() -> int:
    if not SVG.exists():
        print(f"missing SVG: {SVG}", file=sys.stderr)
        return 1

    ET.parse(SVG)
    svg_text = SVG.read_text()
    missing = [description for token, description in REQUIRED_TOKENS.items() if token not in svg_text]
    if missing:
        for description in missing:
            print(f"missing capability: {description}", file=sys.stderr)
        return 1

    print("capability SVG contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
