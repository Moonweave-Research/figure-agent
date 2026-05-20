from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_quality_axes import (  # noqa: E402
    STORY_QUALITY_AXES,
    quality_axis,
    quality_axis_record,
    quality_axis_summary,
)


def test_quality_axis_rejects_missing_or_unknown_verdict() -> None:
    assert quality_axis({}, "message_storyline") is None
    assert quality_axis({"message_storyline": {"verdict": "unknown"}}, "message_storyline") is None


def test_quality_axis_normalizes_optional_fields() -> None:
    axis = quality_axis(
        {
            "message_storyline": {
                "verdict": "needs_human",
                "recommended_action": "rewrite hierarchy",
                "blocking_items": ["missing hero panel", "", 7],
            }
        },
        "message_storyline",
    )

    assert axis == {
        "name": "message_storyline",
        "verdict": "needs_human",
        "recommended_action": "rewrite hierarchy",
        "blocking_items": ["missing hero panel", "", 7],
    }


def test_quality_axis_summary_selects_worst_applicable_verdict() -> None:
    summary = quality_axis_summary(
        {
            "message_storyline": {
                "verdict": "pass",
                "recommended_action": "keep",
                "blocking_items": [],
            },
            "panel_role_coherence": {
                "verdict": "needs_patch",
                "recommended_action": "split panel B",
                "blocking_items": ["Panel B does two jobs"],
            },
            "composition_layout": {
                "verdict": "not_applicable",
                "blocking_items": ["ignored because lower rank"],
            },
        },
        STORY_QUALITY_AXES,
    )

    assert summary == {
        "verdict": "needs_patch",
        "axis_names": ["message_storyline", "panel_role_coherence", "composition_layout"],
        "axis_verdicts": {
            "message_storyline": "pass",
            "panel_role_coherence": "needs_patch",
            "composition_layout": "not_applicable",
        },
        "recommended_actions": {
            "message_storyline": "keep",
            "panel_role_coherence": "split panel B",
        },
        "blocking_items": {
            "panel_role_coherence": ["Panel B does two jobs"],
            "composition_layout": ["ignored because lower rank"],
        },
    }


def test_quality_axis_summary_returns_none_without_valid_axes() -> None:
    assert quality_axis_summary(None, STORY_QUALITY_AXES) is None
    assert (
        quality_axis_summary({"message_storyline": {"verdict": "unknown"}}, STORY_QUALITY_AXES)
        is None
    )


def test_quality_axis_record_converts_summary_to_axis_record(tmp_path: Path) -> None:
    record = quality_axis_record(
        {
            "verdict": "block",
            "axis_names": ["publication_readiness"],
            "axis_verdicts": {"publication_readiness": "block"},
            "recommended_actions": {"publication_readiness": "force accepted gate"},
            "blocking_items": {"publication_readiness": ["missing approval"]},
        },
        tmp_path / "critique.md",
    )

    assert record == {
        "state": "block",
        "verdict": "block",
        "source": "critique.quality_axes",
        "evidence_path": str(tmp_path / "critique.md"),
        "evaluation_state": "blocked",
        "quality_axes": ["publication_readiness"],
        "quality_axis_verdicts": {"publication_readiness": "block"},
        "quality_axis_recommended_actions": {
            "publication_readiness": "force accepted gate"
        },
        "quality_axis_blocking_items": {"publication_readiness": ["missing approval"]},
    }
