from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from driver import fig_driver_closeout  # noqa: E402


def _report(step: dict[str, object]) -> dict[str, object]:
    return {
        "closeout_complete": False,
        "next_action": '/fig_loop demo --goal "<goal>"',
        "blocking_step_ids": ["loop_rerun"],
        "steps": [{"id": "loop_rerun", "state": "needs_action", **step}],
    }


def test_missing_loop_run_is_suppressed_by_structured_record_state() -> None:
    report = _report({"evidence": {"loop_record_state": "absent"}})

    assert fig_driver_closeout.closeout_recommendation(report) is None


def test_reason_sentence_alone_no_longer_suppresses_the_recommendation() -> None:
    # The old gate matched the English reason; rewording it would have silently
    # changed which closeouts the driver ignores.
    report = _report({"reason": "no post-patch fig_loop run was found"})

    recommendation = fig_driver_closeout.closeout_recommendation(report)

    assert recommendation is not None
    assert recommendation.kind == "loop"
