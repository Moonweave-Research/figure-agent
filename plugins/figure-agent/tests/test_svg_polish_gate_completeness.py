"""Gate-completeness contract: svg_semantic_diff must inventory every SVG mutation
that svg_polish_executor can write.

WHY this test exists
--------------------
The svg_semantic_diff gate is allowlist-based: it only reports drift on the
attributes/tags it explicitly inventories (OPTICAL_ATTRS, the transform handling,
the text/path/marker counts, the frame attrs). The svg_polish_executor, driven by
recipes whose action set lives in svg_polish_recipe.ACTION_TYPES, mutates a concrete
set of SVG attributes. If the executor gains the ability to write an attribute that
the gate does not inventory, the gate goes silent on that change class and a
semantic edit can slip through unflagged.

This test pins the two surfaces against each other so they cannot drift apart
unnoticed:

  * the recipe-accepted action set (ACTION_TYPES) == the executor's implemented
    action set, so a new live capability cannot appear without this test moving.
  * every SVG attribute _apply_action writes is inventoried by the gate
    (OPTICAL_ATTRS et al.), modulo one tracked exception.
  * the executor's only transform function is translate, whose sanctioned bound
    (MAX_TRANSLATE_PX) is shared with the gate's _transform_within_executor_bounds.

The attribute assertion is intentionally exact, not a subset check, so it fails in
BOTH directions a future change can break the contract:

  * a NEW executor capability (e.g. a `set_fill` action writing `fill`, already
    covered, or a brand-new `rotate`/`set_font_size`) that the gate does not
    inventory  ->  test fails until the gate adds it.
  * the one KNOWN, deliberately-tracked gap (`stroke-width`, see below) being
    closed in the gate without updating this test  ->  test fails so the residual
    set is kept honest.

KNOWN GAP (load-bearing, do not silently delete)
------------------------------------------------
`set_stroke_width` is a live executor action (svg_polish_recipe.ACTION_TYPES, and
the shipped recipe template's R002_stroke_polish op) that writes the `stroke-width`
attribute. svg_semantic_diff does NOT inventory `stroke-width`: it is absent from
OPTICAL_ATTRS and read nowhere else. A bounded stroke-width polish therefore passes
the gate with zero findings today. Whether the correct gate behavior is to flag it
to a human (like the opacity family) or to sanction it within the executor's
0.5x-2x ratio (like bounded translate) is a design decision and out of scope for
this test-only contract. Until that decision lands, the gap is recorded here as an
EXPECTED_UNCOVERED residual rather than hidden.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import svg_polish_executor  # noqa: E402
import svg_semantic_diff  # noqa: E402
from svg_polish_recipe import ACTION_TYPES  # noqa: E402

# The SVG attributes / transform functions svg_polish_executor._apply_action writes.
# OPACITY_ATTRIBUTES is imported live so a new opacity action auto-extends this side.
# The other two writes are string literals inside _apply_action (not data), so they
# are mirrored here with a pointer: add an entry below if you add a branch to
# svg_polish_executor._apply_action that calls element.set(<attr>, ...) or writes a
# new transform function.
EXECUTOR_ATTRIBUTE_WRITES = frozenset(svg_polish_executor.OPACITY_ATTRIBUTES.values()) | {
    "stroke-width",  # _apply_action "set_stroke_width" branch
}

# The SVG attributes svg_semantic_diff._inventory reads for optical/color drift.
# stroke-width is intentionally NOT here today (see KNOWN GAP in the module docstring).
GATE_INVENTORIED_ATTRIBUTES = frozenset(svg_semantic_diff.OPTICAL_ATTRS)

# The single known, deliberately-tracked attribute the executor writes but the gate
# does not yet inventory. Shrinking this to empty (by inventorying stroke-width) is a
# welcome production fix -- but it must update this set in the same change.
EXPECTED_UNCOVERED_ATTRIBUTES = frozenset({"stroke-width"})


def test_executor_action_types_match_recipe_action_types() -> None:
    """Every recipe-accepted action is implemented by the executor and vice versa.

    ACTION_TYPES is the live mutation surface (what a recipe may request); the
    executor's _apply_action/OPACITY_ATTRIBUTES is what actually mutates SVG. If a
    new action type is added to one side only, the enumeration below would miss it,
    so this guards the premise of the whole contract.
    """
    executor_action_types = set(svg_polish_executor.OPACITY_ATTRIBUTES) | {
        "translate",
        "set_stroke_width",
    }
    assert executor_action_types == set(ACTION_TYPES)


def test_gate_inventories_every_executor_attribute_write_except_known_gap() -> None:
    """The gate must inventory every attribute the executor writes, modulo the
    explicitly tracked stroke-width gap.

    Exact equality (not subset) so the test fails if a future executor capability
    writes an un-inventoried attribute, AND fails if the stroke-width gap is closed
    in the gate without updating EXPECTED_UNCOVERED_ATTRIBUTES.
    """
    uncovered = EXECUTOR_ATTRIBUTE_WRITES - GATE_INVENTORIED_ATTRIBUTES
    assert uncovered == EXPECTED_UNCOVERED_ATTRIBUTES, (
        "svg_semantic_diff gate inventory drifted from svg_polish_executor's "
        f"attribute writes: uncovered={sorted(uncovered)}, "
        f"expected_uncovered={sorted(EXPECTED_UNCOVERED_ATTRIBUTES)}. "
        "If you added an executor action, inventory its attribute in the gate "
        "(e.g. OPTICAL_ATTRS); if you closed the stroke-width gap, update "
        "EXPECTED_UNCOVERED_ATTRIBUTES."
    )


def test_translate_bound_is_shared_between_executor_and_gate() -> None:
    """The gate sanctions bounded translates using the same MAX_TRANSLATE_PX as the
    executor enforces. A drift here would either flag sanctioned output or pass
    over-bound translates the executor would never produce.
    """
    assert svg_semantic_diff.MAX_TRANSLATE_PX == svg_polish_executor.MAX_TRANSLATE_PX
