"""Validate durable human decision records derived from queue decision packets."""

from __future__ import annotations

from typing import Any

import fixture_identity

SCHEMA = "figure-agent.human-decision-record.v1"
RELEASE_DECISION_PACKET_SCHEMA = "figure-agent.release-decision-packet.v1"
STYLE_DIRECTION_PACKET_SCHEMA = "figure-agent.style-direction-packet.v1"
DESIGN_DIRECTION_PACKET_SCHEMA = "figure-agent.design-direction-packet.v1"

DECISION_KINDS = frozenset(
    {
        "accept_current_generated_export",
        "declare_final_artifact",
        "declare_separate_final_artifact",
        "reject_current_artifact",
        "defer_for_dogfood",
        "keep_current_style",
        "request_bounded_tikz_polish",
        "request_bounded_tikz_source_polish",
        "request_restrained_tikz_refinement",
        "request_editorial_redesign_benchmark",
        "request_svg_polish_candidate_evidence",
        "request_svg_polish_handoff_evidence",
        "request_full_style_redesign",
        "prepare_bounded_tikz_refinement",
        "prepare_editorial_redesign_candidates",
        "prepare_svg_polish_handoff",
        "defer_design_decision",
    }
)
RELEASE_DECISION_KINDS = frozenset(
    {
        "accept_current_generated_export",
        "declare_final_artifact",
        "declare_separate_final_artifact",
        "reject_current_artifact",
        "defer_for_dogfood",
    }
)
STYLE_CHOICE_DECISION_KINDS = frozenset(
    {
        "keep_current_style",
        "request_restrained_tikz_refinement",
        "request_editorial_redesign_benchmark",
        "request_svg_polish_handoff_evidence",
    }
)
LEGACY_STYLE_DECISION_KINDS = frozenset(
    {
        "request_bounded_tikz_polish",
        "request_bounded_tikz_source_polish",
        "request_svg_polish_candidate_evidence",
        "request_full_style_redesign",
    }
)
STYLE_DECISION_KINDS = STYLE_CHOICE_DECISION_KINDS | LEGACY_STYLE_DECISION_KINDS
DESIGN_DIRECTION_DECISION_KINDS = frozenset(
    {
        "keep_current_style",
        "prepare_bounded_tikz_refinement",
        "prepare_editorial_redesign_candidates",
        "prepare_svg_polish_handoff",
        "defer_design_decision",
    }
)
PACKET_SCHEMAS = frozenset(
    {
        RELEASE_DECISION_PACKET_SCHEMA,
        STYLE_DIRECTION_PACKET_SCHEMA,
        DESIGN_DIRECTION_PACKET_SCHEMA,
    }
)
MUTATION_BOUNDARIES = frozenset(
    {
        "no_source_mutation",
        "source_mutation_allowed",
        "release_state_mutation_allowed",
        "golden_mutation_allowed",
    }
)
_RELEASE_MUTATION_BOUNDARIES = frozenset(
    {"release_state_mutation_allowed", "golden_mutation_allowed"}
)
_SVG_POLISH_DECISION_KINDS = frozenset(
    {"request_svg_polish_candidate_evidence", "request_svg_polish_handoff_evidence"}
)


class HumanDecisionRecordError(ValueError):
    """Raised when a human decision record is malformed or crosses boundaries."""


def _required_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HumanDecisionRecordError(f"{key}_invalid")
    return value


def _optional_string(record: dict[str, Any], key: str) -> str | None:
    value = record.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise HumanDecisionRecordError(f"{key}_invalid")
    return value


def _validate_follow_up(value: Any) -> dict[str, str | None]:
    if not isinstance(value, dict):
        raise HumanDecisionRecordError("follow_up_invalid")
    command = value.get("command")
    implementation_slice = value.get("implementation_slice")
    if command is not None and (not isinstance(command, str) or not command.strip()):
        raise HumanDecisionRecordError("follow_up_command_invalid")
    if implementation_slice is not None and (
        not isinstance(implementation_slice, str) or not implementation_slice.strip()
    ):
        raise HumanDecisionRecordError("follow_up_implementation_slice_invalid")
    if command is None and implementation_slice is None:
        raise HumanDecisionRecordError("follow_up_missing_action")
    return {"command": command, "implementation_slice": implementation_slice}


def _combined_decision_text(record: dict[str, Any], follow_up: dict[str, str | None]) -> str:
    parts = [
        record.get("agent_recommendation"),
        record.get("human_decision"),
        record.get("human_note"),
        follow_up.get("command"),
        follow_up.get("implementation_slice"),
    ]
    return "\n".join(part for part in parts if isinstance(part, str))


def validate_decision_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized durable decision record or raise a schema error.

    Validation is intentionally side-effect free: it does not edit fixture source,
    accepted state, golden state, final artifacts, or queue packets.
    """
    if not isinstance(record, dict):
        raise HumanDecisionRecordError("record_invalid")
    if record.get("schema") != SCHEMA:
        raise HumanDecisionRecordError("schema_invalid")

    fixture = _required_string(record, "fixture")
    try:
        fixture_identity.validate_fixture_name(fixture)
    except ValueError as exc:
        raise HumanDecisionRecordError(f"fixture_invalid:{fixture}") from exc

    packet_schema = _required_string(record, "packet_schema")
    packet_path = _required_string(record, "packet_path")
    packet_recommendation = _required_string(record, "packet_recommendation")
    if packet_schema not in PACKET_SCHEMAS:
        raise HumanDecisionRecordError(f"packet_schema_unknown:{packet_schema}")
    packet_timestamp = _optional_string(record, "packet_timestamp")
    queue_run_id = _optional_string(record, "queue_run_id")
    if packet_timestamp is None and queue_run_id is None:
        raise HumanDecisionRecordError("packet_identity_missing")

    decision_kind = _required_string(record, "decision_kind")
    if decision_kind not in DECISION_KINDS:
        raise HumanDecisionRecordError(f"decision_kind_unknown:{decision_kind}")
    mutation_boundary = _required_string(record, "mutation_boundary")
    if mutation_boundary not in MUTATION_BOUNDARIES:
        raise HumanDecisionRecordError(f"mutation_boundary_unknown:{mutation_boundary}")
    follow_up = _validate_follow_up(record.get("follow_up"))

    if packet_schema == STYLE_DIRECTION_PACKET_SCHEMA:
        if mutation_boundary != "no_source_mutation":
            raise HumanDecisionRecordError("style_decision_cannot_authorize_mutation")
        if decision_kind in RELEASE_DECISION_KINDS:
            raise HumanDecisionRecordError("release_decision_requires_release_packet")
    if packet_schema == DESIGN_DIRECTION_PACKET_SCHEMA:
        if mutation_boundary != "no_source_mutation":
            raise HumanDecisionRecordError(
                "design_direction_decision_cannot_authorize_mutation"
            )
        if decision_kind not in DESIGN_DIRECTION_DECISION_KINDS:
            raise HumanDecisionRecordError(
                f"design_direction_decision_kind_unknown:{decision_kind}"
            )
    if packet_schema == RELEASE_DECISION_PACKET_SCHEMA and decision_kind in STYLE_DECISION_KINDS:
        if mutation_boundary in _RELEASE_MUTATION_BOUNDARIES:
            raise HumanDecisionRecordError("style_preference_cannot_approve_release")
    if decision_kind in STYLE_DECISION_KINDS and mutation_boundary != "no_source_mutation":
        raise HumanDecisionRecordError("style_decision_cannot_authorize_mutation")
    if decision_kind in _SVG_POLISH_DECISION_KINDS:
        decision_text = _combined_decision_text(record, follow_up)
        if (
            "ready_for_svg_polish" not in decision_text
            and "evidence" not in decision_text.lower()
        ):
            raise HumanDecisionRecordError("svg_polish_handoff_requires_evidence")

    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "packet_schema": packet_schema,
        "packet_path": packet_path,
        "packet_recommendation": packet_recommendation,
        "packet_timestamp": packet_timestamp,
        "queue_run_id": queue_run_id,
        "decision_kind": decision_kind,
        "agent_recommendation": _required_string(record, "agent_recommendation"),
        "human_decision": _required_string(record, "human_decision"),
        "human_note": _required_string(record, "human_note"),
        "follow_up": follow_up,
        "mutation_boundary": mutation_boundary,
    }
