from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from human_decision_record import (  # noqa: E402
    RELEASE_DECISION_PACKET_SCHEMA,
    SCHEMA,
    STYLE_CHOICE_DECISION_KINDS,
    STYLE_DIRECTION_PACKET_SCHEMA,
    HumanDecisionRecordError,
    validate_decision_record,
)


def _record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "schema": SCHEMA,
        "fixture": "fig3_resistance_mechanism",
        "packet_schema": RELEASE_DECISION_PACKET_SCHEMA,
        "packet_path": "docs/decision-packets/example-release-packet.json",
        "packet_recommendation": "accept_current_generated_export",
        "queue_run_id": "decision-dogfood-001",
        "decision_kind": "accept_current_generated_export",
        "agent_recommendation": "Record explicit acceptance only after human review.",
        "human_decision": "accept current generated export",
        "human_note": "Preview is acceptable for this dogfood pass.",
        "follow_up": {"command": "rerun /fig_queue --mode release"},
        "mutation_boundary": "release_state_mutation_allowed",
    }
    record.update(overrides)
    return record


def test_release_decision_record_validates_without_side_effects(tmp_path: Path) -> None:
    source = tmp_path / "fig3_resistance_mechanism.tex"
    source.write_text("original source\n", encoding="utf-8")

    validated = validate_decision_record(_record())

    assert validated["schema"] == SCHEMA
    assert validated["fixture"] == "fig3_resistance_mechanism"
    assert validated["packet_schema"] == RELEASE_DECISION_PACKET_SCHEMA
    assert validated["packet_path"] == "docs/decision-packets/example-release-packet.json"
    assert validated["packet_recommendation"] == "accept_current_generated_export"
    assert validated["decision_kind"] == "accept_current_generated_export"
    assert validated["mutation_boundary"] == "release_state_mutation_allowed"
    assert source.read_text(encoding="utf-8") == "original source\n"


def test_bounded_tikz_apply_decision_can_authorize_source_mutation() -> None:
    validated = validate_decision_record(
        _record(
            fixture="fig3_trapping_concept",
            decision_kind="apply_bounded_tikz_candidate",
            packet_recommendation="apply_bounded_tikz_candidate",
            agent_recommendation="Apply exactly one hash-bound bounded TikZ source patch.",
            human_decision="approve this exact bounded TikZ source patch",
            human_note="Approval is bound to candidate id and hash.",
            follow_up={
                "command": (
                    "fig-agent bounded-tikz-apply fig3_trapping_concept "
                    "--apply --authorization decision.json"
                )
            },
            mutation_boundary="source_mutation_allowed",
        )
    )

    assert validated["decision_kind"] == "apply_bounded_tikz_candidate"
    assert validated["mutation_boundary"] == "source_mutation_allowed"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("decision_kind", "invent_new_visual_language", "decision_kind_unknown"),
        ("mutation_boundary", "implicit_acceptance", "mutation_boundary_unknown"),
        ("packet_schema", "figure-agent.raw-json.v1", "packet_schema_unknown"),
    ],
)
def test_unknown_enums_are_rejected(field: str, value: str, message: str) -> None:
    with pytest.raises(HumanDecisionRecordError, match=message):
        validate_decision_record(_record(**{field: value}))


def test_legacy_queue_final_artifact_decision_id_is_rejected() -> None:
    with pytest.raises(HumanDecisionRecordError, match="decision_kind_unknown"):
        validate_decision_record(
            _record(
                decision_kind="declare_final_artifact",
                follow_up={"implementation_slice": "declare polished SVG final artifact"},
                mutation_boundary="no_source_mutation",
            )
        )


@pytest.mark.parametrize(
    "decision_kind",
    [
        "accept_current_generated_export",
        "declare_separate_final_artifact",
        "reject_current_artifact",
        "defer_for_dogfood",
    ],
)
def test_wave_one_release_decision_ids_validate_without_mutation(decision_kind: str) -> None:
    validated = validate_decision_record(
        _record(
            decision_kind=decision_kind,
            packet_recommendation="accept_current_generated_export",
            agent_recommendation="Record the release decision separate from the packet.",
            human_decision=decision_kind,
            human_note="Human decision record only; no Wave 1 state mutation.",
            follow_up={"implementation_slice": "record decision only"},
            mutation_boundary="no_source_mutation",
        )
    )

    assert validated["decision_kind"] == decision_kind
    assert validated["mutation_boundary"] == "no_source_mutation"


@pytest.mark.parametrize(
    "decision_kind",
    [
        "request_full_style_redesign",
        "keep_current_style",
        "request_bounded_tikz_source_polish",
        "request_svg_polish_handoff_evidence",
    ],
)
def test_wave_one_style_decision_ids_validate_without_release_acceptance(
    decision_kind: str,
) -> None:
    follow_up = {
        "implementation_slice": (
            "record style policy only with ready_for_svg_polish evidence if SVG handoff is chosen"
        )
    }
    packet_recommendation = (
        "request_svg_polish_handoff_evidence"
        if decision_kind == "request_svg_polish_handoff_evidence"
        else "keep_current_style"
    )

    validated = validate_decision_record(
        _record(
            packet_schema=STYLE_DIRECTION_PACKET_SCHEMA,
            packet_path="docs/decision-packets/example-style-packet.json",
            packet_recommendation=packet_recommendation,
            packet_timestamp="2026-07-01T00:00:00Z",
            queue_run_id=None,
            decision_kind=decision_kind,
            agent_recommendation="Record the style choice without accepting release.",
            human_decision=decision_kind,
            human_note="Style policy only; this does not approve release acceptance.",
            follow_up=follow_up,
            mutation_boundary="no_source_mutation",
        )
    )

    assert validated["decision_kind"] == decision_kind
    assert validated["mutation_boundary"] == "no_source_mutation"


def test_packet_identity_requires_timestamp_or_queue_run_id() -> None:
    with pytest.raises(HumanDecisionRecordError, match="packet_identity_missing"):
        validate_decision_record(_record(queue_run_id=None, packet_timestamp=None))


def test_style_decision_does_not_equal_release_acceptance() -> None:
    with pytest.raises(HumanDecisionRecordError, match="release_decision_requires_release_packet"):
        validate_decision_record(
            _record(
                packet_schema=STYLE_DIRECTION_PACKET_SCHEMA,
                decision_kind="accept_current_generated_export",
                mutation_boundary="no_source_mutation",
            )
        )


def test_style_record_rejects_release_or_golden_mutation_boundary() -> None:
    with pytest.raises(
        HumanDecisionRecordError,
        match="style_decision_cannot_authorize_mutation",
    ):
        validate_decision_record(
            _record(
                packet_schema=STYLE_DIRECTION_PACKET_SCHEMA,
                packet_timestamp="2026-06-30T14:00:00Z",
                queue_run_id=None,
                decision_kind="request_bounded_tikz_polish",
                follow_up={"implementation_slice": "open one bounded TikZ polish pass"},
                mutation_boundary="golden_mutation_allowed",
            )
        )


def test_style_record_rejects_source_mutation_boundary() -> None:
    with pytest.raises(
        HumanDecisionRecordError,
        match="style_decision_cannot_authorize_mutation",
    ):
        validate_decision_record(
            _record(
                packet_schema=STYLE_DIRECTION_PACKET_SCHEMA,
                packet_timestamp="2026-06-30T14:00:00Z",
                queue_run_id=None,
                decision_kind="request_restrained_tikz_refinement",
                follow_up={"implementation_slice": "open a later bounded TikZ refinement slice"},
                mutation_boundary="source_mutation_allowed",
            )
        )


def test_generic_release_record_cannot_borrow_development_state_boundary() -> None:
    with pytest.raises(
        HumanDecisionRecordError,
        match="mutation_boundary_unknown",
    ):
        validate_decision_record(
            _record(
                mutation_boundary="development_baseline_state_mutation_allowed",
            )
        )


def test_style_preference_from_release_packet_cannot_approve_release_state() -> None:
    with pytest.raises(HumanDecisionRecordError, match="style_preference_cannot_approve_release"):
        validate_decision_record(
            _record(
                decision_kind="request_full_style_redesign",
                follow_up={"implementation_slice": "prepare redesign benchmark candidates"},
                mutation_boundary="release_state_mutation_allowed",
            )
        )


def test_follow_up_requires_command_or_implementation_slice() -> None:
    with pytest.raises(HumanDecisionRecordError, match="follow_up_missing_action"):
        validate_decision_record(_record(follow_up={}))


@pytest.mark.parametrize("decision_kind", sorted(STYLE_CHOICE_DECISION_KINDS))
def test_style_choice_decision_ids_validate_without_mutation(decision_kind: str) -> None:
    follow_up = {
        "implementation_slice": (
            "record style policy only; require ready_for_svg_polish evidence before "
            "any SVG handoff"
        )
    }
    packet_recommendation = (
        "request_svg_polish_handoff_evidence"
        if decision_kind == "request_svg_polish_handoff_evidence"
        else decision_kind
    )

    validated = validate_decision_record(
        _record(
            packet_schema=STYLE_DIRECTION_PACKET_SCHEMA,
            packet_timestamp="2026-07-01T00:00:00Z",
            queue_run_id=None,
            decision_kind=decision_kind,
            packet_recommendation=packet_recommendation,
            agent_recommendation="Record the style choice without mutating artifacts.",
            human_decision=decision_kind,
            human_note="Human selected this style route as policy state only.",
            follow_up=follow_up,
            mutation_boundary="no_source_mutation",
        )
    )

    assert validated["decision_kind"] == decision_kind
    assert validated["mutation_boundary"] == "no_source_mutation"


def test_svg_polish_handoff_accepts_structured_packet_recommendation_not_prose() -> None:
    validated = validate_decision_record(
        _record(
            packet_schema=STYLE_DIRECTION_PACKET_SCHEMA,
            packet_timestamp="2026-07-01T00:00:00Z",
            queue_run_id=None,
            packet_recommendation="request_svg_polish_handoff_evidence",
            decision_kind="request_svg_polish_handoff_evidence",
            agent_recommendation="Try SVG polish next.",
            human_decision="request SVG polish",
            human_note="Looks like a polish task.",
            follow_up={"implementation_slice": "prepare an SVG handoff"},
            mutation_boundary="no_source_mutation",
        )
    )

    assert validated["decision_kind"] == "request_svg_polish_handoff_evidence"


def test_svg_polish_handoff_rejects_prose_substring_without_packet_recommendation() -> None:
    with pytest.raises(
        HumanDecisionRecordError,
        match="svg_polish_handoff_requires_packet_recommendation",
    ):
        validate_decision_record(
            _record(
                packet_schema=STYLE_DIRECTION_PACKET_SCHEMA,
                packet_timestamp="2026-07-01T00:00:00Z",
                queue_run_id=None,
                packet_recommendation="keep_current_style",
                decision_kind="request_svg_polish_handoff_evidence",
                agent_recommendation="Try SVG polish next with evidence.",
                human_decision="request SVG polish",
                human_note="This sentence includes evidence but is not structured proof.",
                follow_up={"implementation_slice": "prepare an SVG handoff with evidence"},
                mutation_boundary="no_source_mutation",
            )
        )


def test_design_direction_decision_record_validates_without_mutation() -> None:
    validated = validate_decision_record(
        _record(
            packet_schema="figure-agent.design-direction-packet.v1",
            packet_timestamp="2026-07-01T00:00:00Z",
            queue_run_id=None,
            decision_kind="prepare_bounded_tikz_refinement",
            agent_recommendation=(
                "I recommend keeping the current style unless a candidate beats the benchmark."
            ),
            human_decision="prepare bounded TikZ refinement candidates",
            human_note="Compare one bounded candidate before changing direction.",
            follow_up={"implementation_slice": "prepare a bounded TikZ candidate packet only"},
            mutation_boundary="no_source_mutation",
        )
    )

    assert validated["packet_schema"] == "figure-agent.design-direction-packet.v1"
    assert validated["decision_kind"] == "prepare_bounded_tikz_refinement"
    assert validated["mutation_boundary"] == "no_source_mutation"


@pytest.mark.parametrize(
    "decision_kind",
    [
        "keep_current_style",
        "prepare_bounded_tikz_refinement",
        "prepare_editorial_redesign_candidates",
        "prepare_svg_polish_handoff",
        "defer_design_decision",
    ],
)
def test_design_direction_decision_ids_validate_without_mutation(decision_kind: str) -> None:
    validated = validate_decision_record(
        _record(
            packet_schema="figure-agent.design-direction-packet.v1",
            packet_timestamp="2026-07-01T00:00:00Z",
            queue_run_id=None,
            decision_kind=decision_kind,
            agent_recommendation=(
                "Record a design direction only; no artifact mutation is authorized."
            ),
            human_decision=decision_kind,
            human_note="Human selected this design direction as policy state only.",
            follow_up={"implementation_slice": "record design direction only"},
            mutation_boundary="no_source_mutation",
        )
    )

    assert validated["decision_kind"] == decision_kind


def test_design_direction_record_rejects_mutating_boundary() -> None:
    with pytest.raises(
        HumanDecisionRecordError,
        match="design_direction_decision_cannot_authorize_mutation",
    ):
        validate_decision_record(
            _record(
                packet_schema="figure-agent.design-direction-packet.v1",
                packet_timestamp="2026-07-01T00:00:00Z",
                queue_run_id=None,
                decision_kind="prepare_editorial_redesign_candidates",
                follow_up={"implementation_slice": "prepare non-mutating editorial candidates"},
                mutation_boundary="source_mutation_allowed",
            )
        )


def test_design_direction_record_rejects_legacy_style_decision_ids() -> None:
    with pytest.raises(HumanDecisionRecordError, match="design_direction_decision_kind_unknown"):
        validate_decision_record(
            _record(
                packet_schema="figure-agent.design-direction-packet.v1",
                packet_timestamp="2026-07-01T00:00:00Z",
                queue_run_id=None,
                decision_kind="request_full_style_redesign",
                follow_up={"implementation_slice": "prepare redesign benchmark candidates"},
                mutation_boundary="no_source_mutation",
            )
        )
