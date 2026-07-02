from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_driver_editorial import (  # noqa: E402
    ROUTE_HUMAN_GATE,
    ROUTE_READY_FOR_SVG_POLISH,
    ROUTE_RUN_LOOP,
    ROUTE_SEMANTIC_BACKPORT,
    editorial_polish_route,
    editorial_review_requires_human_gate,
    svg_polish_gate_from_checkpoint,
    svg_polish_readiness,
    svg_polish_readiness_from_checkpoint,
)


def test_editorial_review_requires_human_gate_for_blocking_summary() -> None:
    assert editorial_review_requires_human_gate(
        {
            "worst_verdict": "pass",
            "verdict_counts": {"pass": 9, "weak": 0, "fail": 0, "needs_human": 0},
            "blocking_high_impact_count": 1,
            "polish_recommended_path": "ready_for_svg_polish",
        }
    )


def test_editorial_review_ignores_nonblocking_weak_summary() -> None:
    assert not editorial_review_requires_human_gate(
        {
            "worst_verdict": "weak",
            "verdict_counts": {"pass": 9, "weak": 1, "fail": 0, "needs_human": 0},
            "blocking_high_impact_count": 0,
            "polish_recommended_path": "ready_for_svg_polish",
        }
    )


def test_editorial_polish_route_maps_all_recommended_paths() -> None:
    assert (
        editorial_polish_route({"polish_recommended_path": "semantic_backport_required"})
        == ROUTE_SEMANTIC_BACKPORT
    )
    assert (
        editorial_polish_route({"polish_recommended_path": "needs_human_art_direction"})
        == ROUTE_HUMAN_GATE
    )
    assert editorial_polish_route({"polish_recommended_path": "continue_tikz"}) == ROUTE_RUN_LOOP
    assert (
        editorial_polish_route({"polish_recommended_path": "ready_for_svg_polish"})
        == ROUTE_READY_FOR_SVG_POLISH
    )


def test_editorial_polish_route_human_gate_wins_over_ready_path() -> None:
    assert (
        editorial_polish_route(
            {
                "worst_verdict": "needs_human",
                "verdict_counts": {"pass": 9, "weak": 0, "fail": 0, "needs_human": 1},
                "blocking_high_impact_count": 0,
                "polish_recommended_path": "ready_for_svg_polish",
            }
        )
        == ROUTE_HUMAN_GATE
    )


def test_editorial_polish_route_ignores_missing_or_malformed_summary() -> None:
    assert editorial_polish_route(None) is None
    assert editorial_polish_route({"polish_recommended_path": "unknown"}) is None


def test_svg_polish_readiness_explains_continue_tikz() -> None:
    readiness = svg_polish_readiness(
        {
            "source": "critique.editorial_art_direction",
            "worst_verdict": "weak",
            "polish_trigger_verdict": "weak",
            "polish_recommended_path": "continue_tikz",
            "polish_route_detail": "source-level label spacing remains patchable in TikZ",
        }
    )

    assert readiness == {
        "schema": "figure-agent.svg-polish-readiness.v1",
        "source": "editorial_art_direction_summary",
        "can_start_svg_polish": False,
        "recommended_path": "continue_tikz",
        "next_action": "run_fig_loop",
        "blocking_reason": (
            "editorial polish trigger recommends continue_tikz: "
            "source-level label spacing remains patchable in TikZ"
        ),
        "blocking_items": [
            {
                "source": "editorial_art_direction_summary",
                "id": "tikz_vs_svg_polish_trigger",
                "recommended_path": "continue_tikz",
                "verdict": "weak",
                "route_detail": "source-level label spacing remains patchable in TikZ",
            }
        ],
    }


def test_svg_polish_readiness_allows_ready_path() -> None:
    readiness = svg_polish_readiness(
        {
            "worst_verdict": "pass",
            "polish_trigger_verdict": "pass",
            "polish_recommended_path": "ready_for_svg_polish",
            "polish_route_detail": "only optical vector edge cleanup remains",
            "positive_evidence": [
                "polish_trigger_verdict=pass",
                "polish_route_detail=only optical vector edge cleanup remains",
            ],
        }
    )

    assert readiness is not None
    assert readiness["can_start_svg_polish"] is True
    assert readiness["recommended_path"] == "ready_for_svg_polish"
    assert readiness["next_action"] == "start_svg_polish_recipe"
    assert readiness["route_detail"] == "only optical vector edge cleanup remains"
    assert readiness["positive_evidence"] == [
        "polish_trigger_verdict=pass",
        "polish_route_detail=only optical vector edge cleanup remains",
    ]
    assert readiness["blocking_items"] == []


def test_svg_polish_readiness_blocks_ready_path_without_positive_evidence() -> None:
    readiness = svg_polish_readiness(
        {
            "worst_verdict": "pass",
            "polish_trigger_verdict": "pass",
            "polish_recommended_path": "ready_for_svg_polish",
            "polish_route_detail": "only optical vector edge cleanup remains",
        }
    )

    assert readiness is not None
    assert readiness["can_start_svg_polish"] is False
    assert readiness["recommended_path"] == "ready_for_svg_polish"
    assert readiness["next_action"] == "collect_svg_polish_evidence"
    assert readiness["blocking_items"][0]["id"] == "positive_svg_polish_evidence_missing"


def test_svg_polish_readiness_routes_semantic_backport_and_human_gate() -> None:
    semantic = svg_polish_readiness(
        {
            "worst_verdict": "fail",
            "polish_trigger_verdict": "fail",
            "polish_recommended_path": "semantic_backport_required",
        }
    )
    human = svg_polish_readiness(
        {
            "worst_verdict": "needs_human",
            "human_art_direction_gate_verdict": "needs_human",
            "polish_recommended_path": "needs_human_art_direction",
        }
    )

    assert semantic is not None
    assert semantic["can_start_svg_polish"] is False
    assert semantic["next_action"] == "semantic_backport"
    assert semantic["blocking_items"][0]["recommended_path"] == "semantic_backport_required"
    assert human is not None
    assert human["can_start_svg_polish"] is False
    assert human["next_action"] == "human_art_direction_review"
    assert human["blocking_items"][0]["recommended_path"] == "needs_human_art_direction"


def test_svg_polish_readiness_ignores_malformed_or_unknown_summary() -> None:
    assert svg_polish_readiness(None) is None
    assert svg_polish_readiness({"polish_recommended_path": "unknown"}) is None
    assert svg_polish_readiness_from_checkpoint({}) is None
    assert svg_polish_readiness_from_checkpoint(
        {
            "editorial_art_direction_summary": {
                "polish_recommended_path": "ready_for_svg_polish",
                "positive_evidence": ["ready route verified"],
            }
        }
    )["can_start_svg_polish"] is True


def test_svg_polish_readiness_from_checkpoint_preserves_existing_summary() -> None:
    existing = {
        "schema": "figure-agent.svg-polish-readiness.v1",
        "source": "latest_loop_checkpoint",
        "can_start_svg_polish": False,
        "recommended_path": "continue_tikz",
        "next_action": "run_fig_loop",
        "blocking_reason": "existing",
        "blocking_items": [],
    }

    assert svg_polish_readiness_from_checkpoint({"svg_polish_readiness": existing}) == existing


def test_svg_polish_readiness_from_checkpoint_blocks_ready_path_for_top_tier_blocker() -> None:
    readiness = svg_polish_readiness_from_checkpoint(
        {
            "editorial_art_direction_summary": {
                "polish_recommended_path": "ready_for_svg_polish",
                "worst_verdict": "pass",
            },
            "top_tier_audit_summary": {
                "source": "critique.top_tier_audit",
                "worst_verdict": "weak",
                "blocking_high_impact_count": 1,
                "blocking_high_impact_slots": ["aesthetic_coherence"],
            },
        }
    )

    assert readiness is not None
    assert readiness["can_start_svg_polish"] is False
    assert readiness["recommended_path"] == "ready_for_svg_polish"
    assert readiness["next_action"] == "human_art_direction_review"
    assert readiness["blocking_items"][0]["source"] == "top_tier_audit_summary"
    assert readiness["blocking_items"][0]["id"] == "aesthetic_coherence"


def test_svg_polish_readiness_from_checkpoint_blocks_ready_path_for_crop_uncertainty() -> None:
    readiness = svg_polish_readiness_from_checkpoint(
        {
            "editorial_art_direction_summary": {
                "polish_recommended_path": "ready_for_svg_polish",
                "worst_verdict": "pass",
            },
            "crop_audit_summary": {
                "source": "critique.crop_audit_log",
                "evaluation_state": "needs_action",
                "uncertain_crop_ids": ["VC046_crop"],
            },
        }
    )

    assert readiness is not None
    assert readiness["can_start_svg_polish"] is False
    assert readiness["next_action"] == "review_crop_audit"
    assert readiness["blocking_items"][0]["id"] == "VC046_crop"


def test_svg_polish_readiness_from_checkpoint_prefers_human_gate_over_legacy_pass_trigger() -> None:
    readiness = svg_polish_readiness_from_checkpoint(
        {
            "final_stop_reason": "human_gate_required",
            "recommended_next_action": "human review required for C001",
            "editorial_art_direction_summary": {
                "polish_trigger_verdict": "pass",
                "polish_recommended_path": "continue_tikz",
            },
        }
    )

    assert readiness == {
        "schema": "figure-agent.svg-polish-readiness.v1",
        "source": "latest_loop_checkpoint",
        "can_start_svg_polish": False,
        "recommended_path": "continue_tikz",
        "next_action": "human_review",
        "blocking_reason": (
            "latest /fig_loop checkpoint requires human review: "
            "human review required for C001"
        ),
        "blocking_items": [
            {
                "source": "latest_loop_checkpoint",
                "id": "human_gate_required",
                "recommended_next_action": "human review required for C001",
            }
        ],
    }


def test_svg_polish_readiness_prefers_patch_target_over_legacy_pass_trigger() -> None:
    readiness = svg_polish_readiness_from_checkpoint(
        {
            "final_stop_reason": "patch_target_recommended",
            "recommended_next_action": "patch C002 before polish",
            "editorial_art_direction_summary": {
                "polish_trigger_verdict": "pass",
                "polish_recommended_path": "continue_tikz",
            },
        }
    )

    assert readiness is not None
    assert readiness["can_start_svg_polish"] is False
    assert readiness["next_action"] == "patch_source"
    assert readiness["blocking_items"][0]["id"] == "patch_target_recommended"


def test_svg_polish_readiness_prefers_status_action_over_legacy_pass_trigger() -> None:
    readiness = svg_polish_readiness_from_checkpoint(
        {
            "final_stop_reason": "status_action_required",
            "recommended_next_action": "refresh export before polish",
            "editorial_art_direction_summary": {
                "polish_trigger_verdict": "pass",
                "polish_recommended_path": "continue_tikz",
            },
        }
    )

    assert readiness is not None
    assert readiness["can_start_svg_polish"] is False
    assert readiness["next_action"] == "resolve_status_action"
    assert readiness["blocking_items"][0]["id"] == "status_action_required"


def test_svg_polish_readiness_from_checkpoint_preserves_clean_loop_editorial_fallback() -> None:
    readiness = svg_polish_readiness_from_checkpoint(
        {
            "final_stop_reason": "verify_only_complete",
            "editorial_art_direction_summary": {
                "polish_trigger_verdict": "pass",
                "polish_recommended_path": "ready_for_svg_polish",
                "polish_route_detail": "only optical vector edge cleanup remains",
                "positive_evidence": ["ready route verified"],
            },
        }
    )

    assert readiness is not None
    assert readiness["can_start_svg_polish"] is True
    assert readiness["recommended_path"] == "ready_for_svg_polish"


def test_svg_polish_gate_reports_no_current_checkpoint() -> None:
    gate = svg_polish_gate_from_checkpoint(None)

    assert gate == {
        "schema": "figure-agent.svg-polish-gate.v1",
        "state": "no_current_checkpoint",
        "source": "driver_blocker",
        "can_start_svg_polish": False,
        "recommended_path": None,
        "next_action": "rerun_fig_loop",
        "reason": "no current /fig_loop checkpoint proves ready_for_svg_polish",
        "required_inputs": [
            "critique_fresh",
            "loop_checkpoint_current",
            "tikz_vs_svg_polish_trigger_ready",
            "no_top_tier_blockers",
            "no_crop_uncertainty",
            "no_human_art_direction_gate",
        ],
        "blocking_items": [
            {
                "source": "driver_blocker",
                "id": "no_current_checkpoint",
            }
        ],
    }


def test_svg_polish_gate_normalizes_ready_checkpoint() -> None:
    gate = svg_polish_gate_from_checkpoint(
        {
            "final_stop_reason": "verify_only_complete",
            "editorial_art_direction_summary": {
                "polish_trigger_verdict": "pass",
                "polish_recommended_path": "ready_for_svg_polish",
                "polish_route_detail": "only optical vector cleanup remains",
                "positive_evidence": ["ready route verified"],
            },
        }
    )

    assert gate["schema"] == "figure-agent.svg-polish-gate.v1"
    assert gate["state"] == "ready"
    assert gate["source"] == "latest_loop_checkpoint"
    assert gate["can_start_svg_polish"] is True
    assert gate["next_action"] == "start_svg_polish_recipe"
    assert gate["reason"] == "only optical vector cleanup remains"
    assert gate["positive_evidence"] == ["ready route verified"]
    assert gate["required_inputs"] == [
        "critique_fresh",
        "loop_checkpoint_current",
        "tikz_vs_svg_polish_trigger_ready",
        "no_top_tier_blockers",
        "no_crop_uncertainty",
        "no_human_art_direction_gate",
    ]


def test_svg_polish_gate_preserves_blocker_precedence() -> None:
    gate = svg_polish_gate_from_checkpoint(
        {
            "final_stop_reason": "human_gate_required",
            "recommended_next_action": "human review required for C001",
            "editorial_art_direction_summary": {
                "polish_trigger_verdict": "pass",
                "polish_recommended_path": "ready_for_svg_polish",
            },
        }
    )

    assert gate["state"] == "needs_human"
    assert gate["can_start_svg_polish"] is False
    assert gate["next_action"] == "human_art_direction"
    assert gate["blocking_items"][0]["id"] == "human_gate_required"
