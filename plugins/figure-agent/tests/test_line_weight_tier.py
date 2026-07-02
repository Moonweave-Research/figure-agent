from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import line_weight_tier  # noqa: E402

_WIDTH_RE = re.compile(r"line width\s*=\s*(\d*\.?\d+)pt")


# --- PARAMETERIZED: tier is an input, not hardcoded -----------------------


def test_retier_primary_on_fig2_backbone_line() -> None:
    # fig2 line 32: S--S backbone draw, currently 0.9pt
    line = "\\draw[line width=0.9pt, cGray!85!black]"
    result = line_weight_tier.retier_line_width(line, tier="primary")
    assert result == "\\draw[line width=0.90pt, cGray!85!black]"


def test_retier_secondary_on_fig2_rim_baseline() -> None:
    # fig2 line 49: shared rim baseline, currently 0.5pt dashed
    line = (
        "\\draw[line width=0.5pt, cGray!45, dash pattern=on 1.5pt off 1.5pt] "
        "(0.45,6.15) -- (4.78,6.15);"
    )
    result = line_weight_tier.retier_line_width(line, tier="secondary")
    assert result is not None
    assert "line width=0.55pt" in result
    # dash pattern's `1.5pt` must NOT be retiered (only the line-width token)
    assert "dash pattern=on 1.5pt off 1.5pt" in result
    assert result.endswith("(0.45,6.15) -- (4.78,6.15);")


def test_retier_annotation_on_fig2_creates_arrow() -> None:
    # fig2 line 44: "creates" connector, currently 0.9pt
    line = "\\draw[-{Stealth[length=5pt,width=3.5pt]}, cGray!60!black, line width=0.9pt]"
    result = line_weight_tier.retier_line_width(line, tier="annotation")
    assert result is not None
    assert "line width=0.70pt" in result
    # arrow head geometry tokens must be untouched
    assert "Stealth[length=5pt,width=3.5pt]" in result


# --- PARAMETERIZED: each tier maps to its named constant ------------------


def test_each_tier_emits_its_named_constant() -> None:
    line = "\\draw[line width=1.40pt]"
    assert "line width=0.90pt" in line_weight_tier.retier_line_width(line, tier="primary")
    assert "line width=0.70pt" in line_weight_tier.retier_line_width(line, tier="annotation")
    assert "line width=0.55pt" in line_weight_tier.retier_line_width(line, tier="secondary")


# --- BOUNDED: out-of-range tier rejected, floor never breached ------------


def test_unknown_tier_returns_none() -> None:
    line = "\\draw[line width=0.9pt, cGray!85!black]"
    assert line_weight_tier.retier_line_width(line, tier="hero") is None
    assert line_weight_tier.retier_line_width(line, tier="0.1") is None
    assert line_weight_tier.retier_line_width(line, tier="") is None


def test_line_without_line_width_returns_none() -> None:
    line = "\\node[anchor=west] at (3.0, 2.4) {mobility edge};"
    assert line_weight_tier.retier_line_width(line, tier="primary") is None


def test_all_tier_values_are_above_floor() -> None:
    for tier, value in line_weight_tier.TIERS.items():
        assert value >= line_weight_tier.FLOOR_PT, tier


def test_tier_ratio_within_narrative_rhythm_band() -> None:
    ratio = line_weight_tier.TIERS["primary"] / line_weight_tier.TIERS["secondary"]
    assert 1.6 <= ratio <= 2.0


# --- VALUE-PRESERVING: only the width numeral changes ---------------------


def test_only_width_numeral_changes_rest_byte_identical() -> None:
    line = "\\draw[line width=1.1pt, cRed!70!black]"
    result = line_weight_tier.retier_line_width(line, tier="primary")
    assert result is not None
    # Everything except the numeral inside `line width=...pt` is identical.
    before_stripped = _WIDTH_RE.sub("line width=Xpt", line)
    after_stripped = _WIDTH_RE.sub("line width=Xpt", result)
    assert before_stripped == after_stripped
    # No coordinate or color token mutated.
    assert "cRed!70!black" in result


def test_first_match_only_when_multiple_widths_present() -> None:
    # A line carrying two line-width tokens (pathological) retiers only the first,
    # so the candidate `original`->count==1 guard is preserved downstream.
    line = "\\draw[line width=0.4pt] -- node[line width=0.7pt] {x};"
    result = line_weight_tier.retier_line_width(line, tier="secondary")
    assert result is not None
    assert result.count("line width=0.55pt") == 1
    assert "line width=0.7pt" in result
