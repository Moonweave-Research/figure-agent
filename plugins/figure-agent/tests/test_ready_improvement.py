from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ready_improvement import build_ready_improvement_summary  # noqa: E402


def _status(**overrides: Any) -> dict[str, Any]:
    status = {
        "workflow_ready": True,
        "release_ready": False,
        "final_ready": False,
        "critique_state": "FRESH",
    }
    status.update(overrides)
    return status


def _checkpoint(**overrides: Any) -> dict[str, Any]:
    checkpoint = {
        "final_stop_reason": "verify_only_complete",
        "recommended_next_action": "no action required",
        "escalation_level": "none",
    }
    checkpoint.update(overrides)
    return checkpoint


def test_ready_checkpoint_without_optional_evidence_has_no_candidates() -> None:
    summary = build_ready_improvement_summary(
        fixture="demo",
        status=_status(release_ready=True),
        action="complete",
        stop_boundary=None,
        loop_checkpoint=_checkpoint(),
    )

    assert summary["schema"] == "figure-agent.ready-improvement-summary.v1"
    assert summary["state"] == "ready_no_actionable_improvement"
    assert summary["safe_to_ship"] is True
    assert summary["blocks_release"] is False
    assert summary["auto_patch_allowed"] is False
    assert summary["candidate_count"] == 0
    assert summary["candidates"] == []


def test_continue_tikz_route_detail_becomes_optional_candidate() -> None:
    summary = build_ready_improvement_summary(
        fixture="demo",
        status=_status(),
        action="complete",
        stop_boundary=None,
        loop_checkpoint=_checkpoint(
            editorial_art_direction_summary={
                "polish_recommended_path": "continue_tikz",
                "polish_route_detail": "tighten Panel C annotation spacing",
                "worst_verdict": "pass",
                "blocking_high_impact_count": 0,
            }
        ),
    )

    assert summary["state"] == "ready_but_improvable"
    assert summary["candidate_count"] == 1
    candidate = summary["candidates"][0]
    assert candidate["id"] == "I001"
    assert candidate["source"] == "editorial_art_direction_summary"
    assert candidate["source_id"] == "tikz_vs_svg_polish_trigger"
    assert candidate["type"] == "tikz_micro_polish"
    assert candidate["risk"] == "low"
    assert candidate["required_actor"] == "workflow_agent"
    assert candidate["allowed_scope"] == ["examples/demo/demo.tex"]
    assert "tighten Panel C" in candidate["reason"]


def test_weak_top_tier_slot_becomes_optional_candidate_without_blocker() -> None:
    summary = build_ready_improvement_summary(
        fixture="demo",
        status=_status(),
        action="complete",
        stop_boundary=None,
        loop_checkpoint=_checkpoint(
            top_tier_audit_summary={
                "worst_verdict": "weak",
                "blocking_high_impact_count": 0,
                "weak_or_failed_slots": ["aesthetic_coherence"],
            }
        ),
    )

    assert summary["state"] == "ready_but_improvable"
    assert summary["candidates"][0]["source"] == "top_tier_audit_summary"
    assert summary["candidates"][0]["source_id"] == "aesthetic_coherence"
    assert summary["candidates"][0]["risk"] == "medium"


def test_top_tier_fail_count_is_blocking_not_optional() -> None:
    summary = build_ready_improvement_summary(
        fixture="demo",
        status=_status(),
        action="complete",
        stop_boundary=None,
        loop_checkpoint=_checkpoint(
            top_tier_audit_summary={
                "worst_verdict": "weak",
                "blocking_high_impact_count": 0,
                "verdict_counts": {"fail": 1, "needs_human": 0},
                "weak_or_failed_slots": ["aesthetic_coherence"],
            }
        ),
    )

    assert summary["state"] == "not_ready"
    assert summary["safe_to_ship"] is False
    assert summary["candidate_count"] == 0


def test_weak_aesthetic_lever_becomes_optional_candidate() -> None:
    summary = build_ready_improvement_summary(
        fixture="demo",
        status=_status(),
        action="complete",
        stop_boundary=None,
        loop_checkpoint=_checkpoint(
            aesthetic_lever_summary={
                "evaluation_state": "needs_patch",
                "next_aesthetic_bottleneck": {
                    "lever_id": "hero_balance",
                    "dimension": "visual_hierarchy",
                    "route": "tikz_patch",
                    "linked_evidence": ["editorial_art_direction.visual_identity"],
                },
            }
        ),
    )

    assert summary["state"] == "ready_but_improvable"
    assert summary["candidates"][0]["source"] == "aesthetic_lever_summary"
    assert summary["candidates"][0]["source_id"] == "hero_balance"
    assert summary["candidates"][0]["type"] == "tikz_micro_polish"


def test_human_gated_checkpoint_is_not_ready_and_has_no_candidates() -> None:
    summary = build_ready_improvement_summary(
        fixture="demo",
        status=_status(),
        action="human_gate_stop",
        stop_boundary="human_gate_required",
        loop_checkpoint=_checkpoint(
            final_stop_reason="human_gate_required",
            recommended_next_action="review label semantics",
            escalation_level="human_review_required",
            editorial_art_direction_summary={
                "polish_recommended_path": "continue_tikz",
                "polish_route_detail": "tighten Panel C annotation spacing",
            },
        ),
    )

    assert summary["state"] == "not_ready"
    assert summary["safe_to_ship"] is False
    assert summary["candidate_count"] == 0
    assert summary["candidates"] == []


def test_force_golden_status_action_can_still_be_safe_to_ship() -> None:
    summary = build_ready_improvement_summary(
        fixture="demo",
        status=_status(),
        action="release_blocked",
        stop_boundary="accepted_or_final_ready_required",
        loop_checkpoint=_checkpoint(
            final_stop_reason="status_action_required",
            recommended_next_action="/fig_export demo --force-golden",
            editorial_art_direction_summary={
                "polish_recommended_path": "continue_tikz",
                "polish_route_detail": "optional palette cleanup",
                "worst_verdict": "pass",
                "blocking_high_impact_count": 0,
            },
        ),
    )

    assert summary["state"] == "ready_but_improvable"
    assert summary["safe_to_ship"] is True
    assert summary["candidate_count"] == 1


def test_no_checkpoint_omits_summary() -> None:
    assert (
        build_ready_improvement_summary(
            fixture="demo",
            status=_status(release_ready=True),
            action="complete",
            stop_boundary=None,
            loop_checkpoint=None,
        )
        is None
    )


def test_candidate_ids_are_deterministic_by_source_and_source_id() -> None:
    summary = build_ready_improvement_summary(
        fixture="demo",
        status=_status(),
        action="complete",
        stop_boundary=None,
        loop_checkpoint=_checkpoint(
            top_tier_audit_summary={
                "worst_verdict": "weak",
                "blocking_high_impact_count": 0,
                "weak_or_failed_slots": ["z_slot", "a_slot"],
            },
            editorial_art_direction_summary={
                "polish_recommended_path": "continue_tikz",
                "polish_route_detail": "tighten source-level spacing",
            },
        ),
    )

    assert [(item["id"], item["source"], item["source_id"]) for item in summary["candidates"]] == [
        ("I001", "editorial_art_direction_summary", "tikz_vs_svg_polish_trigger"),
        ("I002", "top_tier_audit_summary", "a_slot"),
        ("I003", "top_tier_audit_summary", "z_slot"),
    ]


def test_journal_playbook_weak_item_becomes_optional_candidate() -> None:
    summary = build_ready_improvement_summary(
        fixture="demo",
        status=_status(),
        action="complete",
        stop_boundary=None,
        loop_checkpoint=_checkpoint(
            journal_art_direction_playbook_summary={
                "evaluation_state": "needs_patch",
                "next_journal_art_direction_bottleneck": {
                    "id": "maturity_restraint",
                    "verdict": "weak",
                    "route": "tikz_patch",
                    "linked_evidence": ["journal_art_direction_playbook_audit"],
                },
            }
        ),
    )

    assert summary["state"] == "ready_but_improvable"
    assert summary["candidates"][0]["source"] == "journal_art_direction_playbook_summary"
    assert summary["candidates"][0]["source_id"] == "maturity_restraint"
