"""Truth-anchored regression tests for scripts/match_snippet.match.

Without a labeled truth set, every "this looks better" tuning of
briefing_hooks / keywords / parser scope is vibes calibration. This test
codifies the expected top-N candidates per briefing so future schema or
parser changes have a falsifier.

Cases live in tests/snippet_match_truth.yaml.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from match_snippet import match  # noqa: E402

TRUTH_PATH = Path(__file__).parent / "snippet_match_truth.yaml"


def _load_cases() -> list[dict]:
    return yaml.safe_load(TRUTH_PATH.read_text())["cases"]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["name"])
def test_top_n_matches_truth(case: dict) -> None:
    expected = case["expected_top"]
    if case.get("expected_behavior") == "applicability_gap":
        pytest.xfail(f"{case['name']}: applicability gap documented — {case.get('note', '')}")

    briefing_path = REPO_ROOT / case["briefing"]
    assert briefing_path.exists(), f"missing fixture: {briefing_path}"

    results = match(briefing_path)
    actual_top = [sid for sid, _ in results[: len(expected)]]

    assert sorted(actual_top) == sorted(expected), (
        f"{case['name']}: top-{len(expected)} mismatch. "
        f"expected={sorted(expected)}, actual={sorted(actual_top)}, "
        f"full_ranking={[(sid, r['score']) for sid, r in results]}"
    )
