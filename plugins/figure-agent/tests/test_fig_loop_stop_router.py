# tests/test_fig_loop_stop_router.py
from __future__ import annotations

from fig_loop_stop_router import Route, route_stop_cause


def _subregion_report(cause, *, refusal_codes=None, unused_lever_id=None, blocked_by=None):
    return {
        "subregion_id": "sel:abc",
        "stop_cause": cause,
        "refusal_codes": refusal_codes or [],
        "unused_lever_id": unused_lever_id,
        "blocked_by": blocked_by,
    }


def test_route_is_pure_dataclass_with_fixed_fields():
    route = route_stop_cause(_subregion_report("decision_weak"))
    assert isinstance(route, Route)
    assert set(vars(route)) == {"cause", "fix_mode", "action", "payload", "blocked_by"}


def test_gate_capped_routes_to_gate():
    route = route_stop_cause(_subregion_report("gate_capped", blocked_by="semantic_review"))
    assert route.fix_mode == "gate"
    assert route.action == "evaluate_gate_lift"
    assert route.blocked_by == "semantic_review"


def test_lever_exhausted_payload_is_refusal_code_string_not_anti_pattern_id():
    route = route_stop_cause(
        _subregion_report("lever_exhausted", refusal_codes=["no_supported_candidate"])
    )
    assert route.fix_mode == "hand"
    assert route.action in {"extend_candidate_family", "human_art_direction"}
    assert route.payload == "no_supported_candidate"
    # anti_pattern_id does not exist in candidate_families.py (0 fields) — must not appear.
    assert "anti_pattern_id" not in (route.payload if isinstance(route.payload, dict) else {})


def test_lever_exhausted_no_refusal_routes_to_human_art_direction():
    route = route_stop_cause(_subregion_report("lever_exhausted"))
    assert route.action == "human_art_direction"


def test_decision_weak_routes_to_eye():
    route = route_stop_cause(_subregion_report("decision_weak"))
    assert route.fix_mode == "eye"
    assert route.action == "ground_decision_against_reference"


def test_headroom_blind_routes_to_eye_raise_ceiling():
    route = route_stop_cause(
        _subregion_report("headroom_blind", unused_lever_id="line_weight_tier:hero")
    )
    assert route.fix_mode == "eye"
    assert route.action == "raise_critique_ceiling"
    assert route.payload == "line_weight_tier:hero"


def test_settled_and_plumbing_route_to_none():
    for cause in ("settled_verified", "plumbing_stop", "not_stopped"):
        route = route_stop_cause(_subregion_report(cause))
        assert route.fix_mode == "none"
        assert route.action is None
