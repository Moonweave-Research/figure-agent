from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_auto_patch import REQUIRED_EVIDENCE, auto_patch_eligibility  # noqa: E402


def _handoff(reason: str, patch_target: str = "Panel A label") -> dict[str, object]:
    return {
        "target_type": "finding",
        "target_id": "C001",
        "patch_target": patch_target,
        "reason": reason,
    }


def test_auto_patch_eligibility_returns_none_without_patch_handoff() -> None:
    assert auto_patch_eligibility({"recommended_next_action": "patch C001"}, None) is None


def test_auto_patch_eligibility_marks_simple_label_fix_as_candidate() -> None:
    result = auto_patch_eligibility(
        {"recommended_next_action": "patch C001: move the label"},
        _handoff("label offset is too tight"),
    )

    assert result == {
        "level": "auto_patch_candidate",
        "target_type": "finding",
        "target_id": "C001",
        "allowed_reasons": ["label offset"],
        "blocked_reasons": [],
        "required_evidence": list(REQUIRED_EVIDENCE),
        "may_edit": False,
    }


def test_auto_patch_eligibility_human_review_wins_over_allowed_terms() -> None:
    result = auto_patch_eligibility(
        {"recommended_next_action": "patch C001: move label after theory review"},
        _handoff("label offset touches physical mechanism interpretation"),
    )

    assert result is not None
    assert result["level"] == "human_review_required"
    assert result["allowed_reasons"] == ["label offset"]
    assert result["blocked_reasons"] == [
        "physical mechanism",
        "theory guard evidence",
        "reference interpretation",
    ]
    assert result["may_edit"] is False


def test_auto_patch_eligibility_defaults_to_patch_assisted_only() -> None:
    result = auto_patch_eligibility(
        {"recommended_next_action": "patch C001"},
        _handoff("local wording is weak", patch_target="Panel B caption"),
    )

    assert result is not None
    assert result["level"] == "patch_assisted_only"
    assert result["allowed_reasons"] == []
    assert result["blocked_reasons"] == []
    assert result["may_edit"] is False
