# tests/test_stop_cause_classify.py
from __future__ import annotations

from stop_cause_classify import (
    QUALITY_CAUSES,
    REFUSAL_CODE_CAUSE,
    STOP_REASON_CAUSE,
    StopCause,
    classify_stop_cause,
)


def _bundle(
    *,
    refusals=None,
    candidates=None,
    defects=None,
    audit=None,
    aesthetic_lever_summary=None,
    basin_summary=None,
    reference_aesthetic_metrics_summary=None,
    raw_stop_reason="no_actionable_findings",
    recommended_next_action="",
):
    return {
        "raw_stop_reason": raw_stop_reason,
        "recommended_next_action": recommended_next_action,
        "candidate_set": {"candidates": candidates or [], "refusals": refusals or []},
        "defects": defects or [],
        "audit_evidence_summary": audit
        or {
            "crop_audit": {"uncertain_crop_ids": []},
            "detector_feedback": {"unadjudicated_candidate_count": 0},
        },
        "aesthetic_lever_summary": aesthetic_lever_summary,
        "basin_summary": basin_summary,
        "reference_aesthetic_metrics_summary": reference_aesthetic_metrics_summary,
    }


def test_enum_has_exactly_seven_lowercase_members():
    assert {c.value for c in StopCause} == {
        "gate_capped",
        "lever_exhausted",
        "decision_weak",
        "headroom_blind",
        "settled_verified",
        "plumbing_stop",
        "not_stopped",
    }


def test_quality_causes_are_the_four_for_argmax():
    assert QUALITY_CAUSES == (
        StopCause.gate_capped,
        StopCause.lever_exhausted,
        StopCause.decision_weak,
        StopCause.headroom_blind,
    )


def test_plumbing_stop_reasons_all_map_to_plumbing():
    for reason in (
        "status_action_required",
        "reference_input_missing",
        "stale_adjudication",
        "invalid_adjudication",
        "missing_adjudication",
        "ambiguous_patch_selection",
        "patch_target_recommended",
        "active_subregion_recommended",
    ):
        assert STOP_REASON_CAUSE[reason] is StopCause.plumbing_stop


def test_refusal_table_covers_all_codes_with_precedence():
    assert REFUSAL_CODE_CAUSE["stale_detector_evidence"] is StopCause.decision_weak
    assert REFUSAL_CODE_CAUSE["unknown_panel"] is StopCause.decision_weak
    assert REFUSAL_CODE_CAUSE["missing_selector_hash"] is StopCause.decision_weak
    assert REFUSAL_CODE_CAUSE["unsupported_candidate_family"] is StopCause.decision_weak
    assert REFUSAL_CODE_CAUSE["no_bounded_operation"] is StopCause.lever_exhausted
    assert REFUSAL_CODE_CAUSE["no_supported_candidate"] is StopCause.lever_exhausted
    assert REFUSAL_CODE_CAUSE["source_missing"] is StopCause.plumbing_stop


def test_plumbing_precedence_first():
    bundle = _bundle(raw_stop_reason="status_action_required")
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.plumbing_stop
    assert result.evidence[0]["source_module"] == "fig_loop_decision"


def test_stale_refusal_is_decision_weak_not_lever_exhausted():
    bundle = _bundle(
        refusals=[{"code": "stale_detector_evidence", "defect_id": "QD001"}],
        defects=[{"id": "QD001", "target": {"panel": "A", "subregion": "sel:abc"}}],
    )
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.decision_weak
    assert any(e["signal_key"] == "stale_detector_evidence" for e in result.evidence)


def test_no_supported_candidate_is_lever_exhausted():
    bundle = _bundle(
        refusals=[{"code": "no_supported_candidate"}],
        defects=[{"id": "QD001", "target": {"panel": "B", "subregion": "x#0"}}],
    )
    result = classify_stop_cause("x#0", bundle)
    assert result.cause is StopCause.lever_exhausted


def test_fixture_scoped_no_supported_candidate_applies_to_each_subregion():
    bundle = _bundle(
        refusals=[{"code": "no_supported_candidate"}],
        defects=[
            {"id": "QD001", "target": {"panel": "A", "subregion": "sel:a"}},
            {"id": "QD002", "target": {"panel": "B", "subregion": "sel:b"}},
        ],
    )

    result = classify_stop_cause("sel:b", bundle)

    assert result.cause is StopCause.lever_exhausted
    assert any(e["signal_key"] == "no_supported_candidate" for e in result.evidence)


def test_fixture_scoped_source_missing_applies_to_each_subregion():
    bundle = _bundle(
        refusals=[{"code": "source_missing"}],
        defects=[
            {"id": "QD001", "target": {"panel": "A", "subregion": "sel:a"}},
            {"id": "QD002", "target": {"panel": "B", "subregion": "sel:b"}},
        ],
    )

    result = classify_stop_cause("sel:a", bundle)

    assert result.cause is StopCause.plumbing_stop
    assert any(e["signal_key"] == "source_missing" for e in result.evidence)


def test_gate_capped_family_lever_blocked_by_pure_mechanical_check():
    bundle = _bundle(
        candidates=[
            {
                "id": "C1",
                "family": "line-weight-tier",
                "edit_class": "line_weight_style",
                "target": {"panel": "A", "subregion": "sel:abc"},
            }
        ],
        defects=[
            {
                "id": "QD001",
                "patchability": {"state": "safe_candidate"},
                "target": {"panel": "A", "subregion": "sel:abc"},
            }
        ],
    )
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.gate_capped
    assert any(e["signal_key"] == "value_preserving_lever" for e in result.evidence)


def test_decision_weak_from_uncertain_crop():
    bundle = _bundle(
        audit={
            "crop_audit": {"uncertain_crop_ids": ["sel:abc"]},
            "detector_feedback": {"unadjudicated_candidate_count": 0},
        },
        defects=[{"id": "QD001", "target": {"panel": "A", "subregion": "sel:abc"}}],
    )
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.decision_weak


def test_headroom_blind_residual_proxy_with_unused_lever():
    bundle = _bundle(
        candidates=[
            {
                "id": "C1",
                "family": "gradient-depth-fill",
                "edit_class": "gradient_depth_fill",
                "target": {"panel": "A", "subregion": "sel:abc"},
            }
        ],
        defects=[
            {
                "id": "QD001",
                "patchability": {"state": "clean"},
                "target": {"panel": "A", "subregion": "sel:abc"},
            }
        ],
        audit={
            "crop_audit": {"uncertain_crop_ids": []},
            "detector_feedback": {"unadjudicated_candidate_count": 0},
            "text_boundary": {"candidate_count": 3, "accounted_count": 1},
        },
    )
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.headroom_blind


def test_settled_verified_when_no_signal():
    bundle = _bundle(
        defects=[
            {
                "id": "QD001",
                "patchability": {"state": "clean"},
                "target": {"panel": "A", "subregion": "sel:abc"},
            }
        ],
    )
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.settled_verified


def test_every_evidence_entry_cites_a_real_source_module():
    bundle = _bundle(
        refusals=[{"code": "no_supported_candidate"}],
        defects=[{"id": "QD001", "target": {"panel": "B", "subregion": "x#0"}}],
    )
    result = classify_stop_cause("x#0", bundle)
    for entry in result.evidence:
        assert set(entry) >= {"signal_class", "signal_key", "source_module", "source_ref"}
        assert entry["source_module"] and entry["source_ref"]
