"""Bounded, palette-locked gradient depth-fill primitive.

Converts a flat single-color `\\fill[<TOKEN>, ...]` into a `\\shade[...]` with two
stops from the SAME palette hue family, addressing the dead_flat_vector_finish
anti-pattern. Only the fill presentation changes: geometry, coordinates, and the
hue's MEANING (same base token) are preserved. Cross-hue or non-palette pairs are
rejected so the lever can never alter a color's semantic identity.
"""

from __future__ import annotations

import re

# Palette base tokens defined in styles/polymer-paper-preamble.sty.
PALETTE_TOKENS: frozenset[str] = frozenset(
    {
        "cAmber",
        "cBlue",
        "cRed",
        "cTeal",
        "cGray",
        "cLGray",
        "cBrown",
        "cArmAmber",
        "cAmberSphere",
    }
)

# Pre-vetted same-base-hue (light, dark) pairs. The producer may pass any
# same-base palette pair; these are the curated defaults.
HUE_FAMILIES: dict[str, tuple[str, str]] = {
    "amber": ("cAmber!12", "cAmber!28"),
    "blue": ("cBlue!10", "cBlue!22"),
    "red": ("cRed!60", "cRed!80"),
    "teal": ("cTeal!12", "cTeal!28"),
}

# A flat fill: `\fill[<token-or-mix>, <rest opts>] ... ;`
# Capture the leading color token (option 0) and the remaining option block.
_FLAT_FILL_RE = re.compile(
    r"^(?P<indent>\s*)\\fill\[\s*(?P<color>[A-Za-z][A-Za-z0-9]*(?:!\d+)?)\s*"
    r"(?P<rest>(?:,[^\]]*)?)\]"
    r"(?P<tail>.*)$",
    re.DOTALL,
)
# A well-formed palette mix is `<base>` or `<base>!<int>` with base in palette.
_MIX_RE = re.compile(r"^(?P<base>[A-Za-z][A-Za-z0-9]*)(?:!(?P<pct>\d+))?$")


def _mix_base(token: str) -> str | None:
    match = _MIX_RE.fullmatch(token)
    if match is None:
        return None
    base = match.group("base")
    if base not in PALETTE_TOKENS:
        return None
    return base


def shade_flat_fill(line: str, *, light: str, dark: str, axis: str = "x") -> str | None:
    if axis not in ("x", "y"):
        return None
    light_base = _mix_base(light)
    dark_base = _mix_base(dark)
    if light_base is None or dark_base is None:
        return None
    if light_base != dark_base:
        return None
    match = _FLAT_FILL_RE.match(line)
    if match is None:
        return None
    stops = (
        f"left color={light}, right color={dark}"
        if axis == "x"
        else f"bottom color={light}, top color={dark}"
    )
    rest = match.group("rest")
    return f"{match.group('indent')}\\shade[{stops}{rest}]{match.group('tail')}"
