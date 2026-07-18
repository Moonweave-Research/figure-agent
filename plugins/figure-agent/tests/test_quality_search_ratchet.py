from __future__ import annotations

import ast
import re
from pathlib import Path

# --- Accretion ratchet for scripts/quality/quality_search.py -----------------
#
# Origin: 2026-07-18 main-branch review finding. quality_search.py had grown to
# 10,076 lines (58% of scripts/quality/) after +2,571 lines in one week, almost
# all bespoke fig1/Panel-F code. The sanctioned alternative already exists and is
# validated: scripts/quality/panel_block_edits.py + panel_block_edits.yaml, whose
# docstring states the policy verbatim:
#
#   "a new iteration on an existing panel is a new entry here, never a new
#    Python family."
#
# The policy existed but nothing enforced it. These constants pin the CURRENT
# counts as an upper bound. NEW bespoke Panel-F code makes CI fail; extracting
# code into panel_block_edits.yaml lets you LOWER a baseline. This is a ratchet:
# ratchet DOWN when you remove debt, never UP to admit more.
#
# When you extract a family into the YAML data path and delete its Python, RE-RUN
# this file and lower the matching constant to the new (smaller) count.

# Baselines pinned 2026-07-18 against origin/main @ 32f7fc0d; lowered 2026-07-18
# after Seam 1 tranche 1 extracted 5 Panel-F families into panel_block_edits.yaml.
MAX_PANEL_F_DEFS = 52
MAX_REPLACEMENT_DEFS = 27
MAX_TEMPLATE_APPLIED_DEFS = 28
MAX_FAMILY_EQ_BRANCHES = 89
MAX_TOTAL_LINES = 9507

_POLICY_LINE = (
    "a new iteration on an existing panel is a new entry here, never a new Python family."
)
_SANCTIONED_PATH = "scripts/quality/panel_block_edits.yaml"

_QUALITY_SEARCH = Path(__file__).resolve().parents[1] / "scripts" / "quality" / "quality_search.py"


def _count_defs(source: str) -> dict[str, int]:
    """Count function defs by name pattern (any nesting depth) via AST."""
    tree = ast.parse(source)
    counts = {"panel_f": 0, "replacement": 0, "template_applied": 0}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if name.startswith("_panel_f"):
                counts["panel_f"] += 1
            if name.endswith("_replacement"):
                counts["replacement"] += 1
            if name.endswith("_template_applied"):
                counts["template_applied"] += 1
    return counts


def _count_family_eq_branches(source: str) -> int:
    """Count `family == "..."` string-equality dispatch branches via regex."""
    return len(re.findall(r"\bfamily\s*==\s*[\"']", source))


def _ratchet_message(metric: str, current: int, baseline: int) -> str:
    return (
        f"quality_search.py accretion ratchet: {metric} rose to {current}, "
        f"above the pinned baseline of {baseline}. Policy (panel_block_edits.py): "
        f'"{_POLICY_LINE}" Add a new element iteration as a YAML entry in '
        f"{_SANCTIONED_PATH}, not a new bespoke Python family. If you instead "
        f"EXTRACTED code and this count went DOWN, lower the baseline constant in "
        f"this test to match (ratchet down, never up)."
    )


def test_panel_f_def_count_does_not_grow() -> None:
    current = _count_defs(_QUALITY_SEARCH.read_text())["panel_f"]
    assert current <= MAX_PANEL_F_DEFS, _ratchet_message(
        "_panel_f* function defs", current, MAX_PANEL_F_DEFS
    )


def test_replacement_def_count_does_not_grow() -> None:
    current = _count_defs(_QUALITY_SEARCH.read_text())["replacement"]
    assert current <= MAX_REPLACEMENT_DEFS, _ratchet_message(
        "*_replacement function defs", current, MAX_REPLACEMENT_DEFS
    )


def test_template_applied_def_count_does_not_grow() -> None:
    current = _count_defs(_QUALITY_SEARCH.read_text())["template_applied"]
    assert current <= MAX_TEMPLATE_APPLIED_DEFS, _ratchet_message(
        "*_template_applied function defs", current, MAX_TEMPLATE_APPLIED_DEFS
    )


def test_family_eq_branch_count_does_not_grow() -> None:
    current = _count_family_eq_branches(_QUALITY_SEARCH.read_text())
    assert current <= MAX_FAMILY_EQ_BRANCHES, _ratchet_message(
        'family == "..." dispatch branches', current, MAX_FAMILY_EQ_BRANCHES
    )


def test_total_line_count_does_not_grow() -> None:
    current = len(_QUALITY_SEARCH.read_text().splitlines())
    assert current <= MAX_TOTAL_LINES, _ratchet_message(
        "total line count", current, MAX_TOTAL_LINES
    )


def test_ratchet_fails_when_a_new_panel_f_family_is_added() -> None:
    """Proof the ratchet has teeth: injecting a bespoke Panel-F def trips it."""
    source = _QUALITY_SEARCH.read_text()
    baseline = _count_defs(source)["panel_f"]
    violated = source + "\n\ndef _panel_f_dummy(state):\n    return state\n"
    assert _count_defs(violated)["panel_f"] == baseline + 1
    assert _count_defs(violated)["panel_f"] > MAX_PANEL_F_DEFS
