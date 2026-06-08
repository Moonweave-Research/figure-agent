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

from match_snippet import main, match  # noqa: E402

TRUTH_PATH = Path(__file__).parent / "snippet_match_truth.yaml"


def _load_cases() -> list[dict]:
    return yaml.safe_load(TRUTH_PATH.read_text())["cases"]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["name"])
def test_top_n_matches_truth(case: dict) -> None:
    expected = case["expected_top"]
    if case.get("expected_behavior") == "applicability_gap":
        pytest.xfail(f"{case['name']}: applicability gap documented — {case.get('note', '')}")

    briefing_path = REPO_ROOT / case["briefing"]
    if not briefing_path.exists():
        pytest.skip(f"optional real fixture briefing not present: {briefing_path}")

    results = match(briefing_path)
    actual_top = [sid for sid, _ in results[: len(expected)]]

    assert sorted(actual_top) == sorted(expected), (
        f"{case['name']}: top-{len(expected)} mismatch. "
        f"expected={sorted(expected)}, actual={sorted(actual_top)}, "
        f"full_ranking={[(sid, r['score']) for sid, r in results]}"
    )


def test_cli_help_uses_argparse(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "usage:" in captured.out
    assert "briefing.md" in captured.out


def test_cli_rejects_unknown_extra_arguments(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    briefing = tmp_path / "briefing.md"
    briefing.write_text("## 1. Topic\n\nDemo\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main([str(briefing), "--bogus"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "unrecognized arguments: --bogus" in captured.err
