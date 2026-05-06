from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "fig1_reference_semantic.svg"
HANDBACK = ROOT / "causal_visibility_handback_v17.md"

REQUIRED_VISIBLE_ROLES = {
    "origin-s-rich-segments": ("S-rich segments",),
    "origin-localized-traps": ("localized traps",),
    "decay-extract-n": ("extract n",),
    "interpretation-step-power-law": ("I(t) ~ t^-n",),
    "interpretation-step-exponent-n": ("n",),
    "interpretation-step-debye": ("Debye", "exp(-t/tau)"),
    "interpretation-step-tau-d": ("tau_d",),
    "interpretation-step-trap-depth-distribution": ("g(Et)",),
    "hero-converged-picture": ("Converged trap-depth picture",),
}


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _text_value(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _elements_for_role(root: ET.Element, role: str) -> list[ET.Element]:
    return [
        element
        for element in root.iter()
        if role in element.attrib.get("data-causal-role", "").split()
    ]


def _combined_role_text(root: ET.Element, role: str) -> str:
    return " ".join(_text_value(element) for element in _elements_for_role(root, role)).strip()


def main() -> int:
    if not SVG.exists():
        return _fail(f"missing rendered SVG: {SVG}")
    root = ET.parse(SVG).getroot()

    for role, tokens in REQUIRED_VISIBLE_ROLES.items():
        text = _combined_role_text(root, role)
        if not text:
            return _fail(f"missing visible causal role: {role}")
        for token in tokens:
            if token not in text:
                return _fail(f"causal role {role} missing visible token: {token}")

    for forbidden in ("ground_truth", "pixel-tracing target", "new scaffold"):
        role_text = " ".join(
            element.attrib.get("data-causal-role", "")
            for element in root.iter()
        )
        if forbidden in role_text:
            return _fail(f"causal visibility role over-promotes reference authority: {forbidden}")

    if not HANDBACK.exists():
        return _fail(f"missing v17 causal visibility handback: {HANDBACK}")
    handback = HANDBACK.read_text()
    required_handback_tokens = (
        "intentional visual semantic update",
        "not a new scaffold",
        "Human visual review",
        "previous hash",
        "new hash",
    )
    for token in required_handback_tokens:
        if token not in handback:
            return _fail(f"v17 visibility handback missing token: {token}")

    print("fig1 causal visibility passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
