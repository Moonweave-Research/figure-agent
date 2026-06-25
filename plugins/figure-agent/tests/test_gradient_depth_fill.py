from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import gradient_depth_fill  # noqa: E402

_COORD_RE = re.compile(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")
_PALETTE_SEGMENT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


def _color_values(line: str) -> list[str]:
    """Every `<key> color=<value>` and `fill=<value>` value on the line."""
    return re.findall(r"(?:left|right|bottom|top|inner|outer|)?\s*color\s*=\s*([!\w]+)", line)


# --- PARAMETERIZED: light/dark/axis are inputs ---------------------------


def test_shade_amber_hero_region_line86() -> None:
    # fig2 line 86: beyond-conventional HERO region backdrop (flat cAmber!12).
    line = "\\fill[cAmber!12, rounded corners=3mm] (10.40,5.70) rectangle (17.00,8.95);"
    result = gradient_depth_fill.shade_flat_fill(line, light="cAmber!12", dark="cAmber!28")
    assert result is not None
    assert result.startswith("\\shade[")
    assert "left color=cAmber!12" in result
    assert "right color=cAmber!28" in result
    # the flat fill key must be DROPPED (shade ignores fill=)
    assert "fill=" not in result
    # coords + rounded corners + geometry untouched
    assert "rounded corners=3mm" in result
    assert _COORD_RE.findall(result) == [("10.40", "5.70"), ("17.00", "8.95")]
    assert result.rstrip().endswith("rectangle (17.00,8.95);")


def test_shade_blue_cluster_line91() -> None:
    line = "\\fill[cBlue!10, rounded corners=2mm] (6.45,4.15) rectangle (8.75,5.45);"
    result = gradient_depth_fill.shade_flat_fill(line, light="cBlue!10", dark="cBlue!22")
    assert result is not None
    assert "left color=cBlue!10" in result
    assert "right color=cBlue!22" in result
    assert "rounded corners=2mm" in result


def test_axis_y_uses_bottom_top_color() -> None:
    line = "\\fill[cBlue!18, rounded corners=1mm] (12.20,0.90) rectangle (16.55,1.08);"
    result = gradient_depth_fill.shade_flat_fill(line, light="cBlue!18", dark="cBlue!34", axis="y")
    assert result is not None
    assert "bottom color=cBlue!18" in result
    assert "top color=cBlue!34" in result
    assert "left color" not in result


# --- BOUNDED + palette-locked: same-hue palette pairs only ---------------


def test_cross_hue_pair_rejected() -> None:
    line = "\\fill[cAmber!12, rounded corners=3mm] (10.40,5.70) rectangle (17.00,8.95);"
    # blue dark stop against an amber light stop changes the hue's MEANING.
    assert gradient_depth_fill.shade_flat_fill(line, light="cAmber!12", dark="cBlue!28") is None


def test_non_palette_base_rejected() -> None:
    line = "\\fill[orange!12, rounded corners=3mm] (10.40,5.70) rectangle (17.00,8.95);"
    assert gradient_depth_fill.shade_flat_fill(line, light="orange!12", dark="orange!28") is None


def test_malformed_mix_rejected() -> None:
    line = "\\fill[cAmber!12, rounded corners=3mm] (10.40,5.70) rectangle (17.00,8.95);"
    assert gradient_depth_fill.shade_flat_fill(line, light="cAmber!!12", dark="cAmber!28") is None
    assert gradient_depth_fill.shade_flat_fill(line, light="cAmberX!12", dark="cAmber!28") is None


def test_invalid_axis_rejected() -> None:
    line = "\\fill[cAmber!12, rounded corners=3mm] (10.40,5.70) rectangle (17.00,8.95);"
    assert (
        gradient_depth_fill.shade_flat_fill(line, light="cAmber!12", dark="cAmber!28", axis="z")
        is None
    )


def test_line_without_flat_fill_returns_none() -> None:
    line = "\\node[anchor=west] at (3.0, 2.4) {mobility edge};"
    assert gradient_depth_fill.shade_flat_fill(line, light="cAmber!12", dark="cAmber!28") is None


# --- VALUE-PRESERVING: emitted stops parse as palette `<base>!<int>` ------


def test_emitted_stops_are_well_formed_palette_mixes() -> None:
    line = "\\fill[cAmber!12, rounded corners=3mm] (10.40,5.70) rectangle (17.00,8.95);"
    result = gradient_depth_fill.shade_flat_fill(line, light="cAmber!12", dark="cAmber!28")
    assert result is not None
    for value in _color_values(result):
        if not value:
            continue
        head = value.split("!")[0]
        assert _PALETTE_SEGMENT_RE.fullmatch(head)
        assert head in gradient_depth_fill.PALETTE_TOKENS


def test_topology_coords_unchanged_by_shade() -> None:
    line = "\\fill[cBlue!10, rounded corners=2mm] (6.45,4.15) rectangle (8.75,5.45);"
    before = _COORD_RE.findall(line)
    result = gradient_depth_fill.shade_flat_fill(line, light="cBlue!10", dark="cBlue!22")
    assert result is not None
    assert _COORD_RE.findall(result) == before


def test_known_hue_families_are_same_base() -> None:
    for _family, (light, dark) in gradient_depth_fill.HUE_FAMILIES.items():
        assert light.split("!")[0] == dark.split("!")[0]
        assert light.split("!")[0] in gradient_depth_fill.PALETTE_TOKENS
