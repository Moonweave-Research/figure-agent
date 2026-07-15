"""Validate durable human decision records derived from queue decision packets."""

from __future__ import annotations

from typing import Any

import fixture_identity

SCHEMA = "figure-agent.human-decision-record.v1"
RELEASE_DECISION_PACKET_SCHEMA = "figure-agent.release-decision-packet.v1"
STYLE_DIRECTION_PACKET_SCHEMA = "figure-agent.style-direction-packet.v1"
DESIGN_DIRECTION_PACKET_SCHEMA = "figure-agent.design-direction-packet.v1"
QUALITY_PATCH_PLAN_SCHEMA = "figure-agent.quality-patch-plan.v1"
AUTHORING_REPAIR_PACKET_SCHEMAS = frozenset(
    {
        "figure-agent.repair-execution-packet.v3",
        "figure-agent.repair-execution-packet.v4",
    }
)

DECISION_KINDS = frozenset(
    {
        "accept_current_generated_export",
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
        "apply_bounded_tikz_candidate",
        "apply_quality_patch_plan",
        "materialize_authoring_repair_candidate",
        "prepare_editorial_redesign_candidates",
        "prepare_svg_polish_handoff",
        "defer_design_decision",
    }
)
RELEASE_DECISION_KINDS = frozenset(
    {
        "accept_current_generated_export",
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
        QUALITY_PATCH_PLAN_SCHEMA,
        *AUTHORING_REPAIR_PACKET_SCHEMAS,
    }
)
MUTATION_BOUNDARIES = frozenset(
    {
        "no_source_mutation",
        "source_mutation_allowed",
        "release_state_mutation_allowed",
        "golden_mutation_allowed",
        "additive_artifact_materialization_allowed",
    }
)
_RELEASE_MUTATION_BOUNDARIES = frozenset(
    {"release_state_mutation_allowed", "golden_mutation_allowed"}
)
_SVG_POLISH_DECISION_KINDS = frozenset(
    {"request_svg_polish_candidate_evidence", "request_svg_polish_handoff_evidence"}
)
_SOURCE_MUTATION_DECISION_KINDS = frozenset(
    {"apply_bounded_tikz_candidate", "apply_quality_patch_plan"}
)
_ADDITIVE_MATERIALIZATION_DECISION_KINDS = frozenset(
    {"materialize_authoring_repair_candidate"}
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
    if (
        decision_kind in _SOURCE_MUTATION_DECISION_KINDS
        and mutation_boundary != "source_mutation_allowed"
    ):
        raise HumanDecisionRecordError("source_mutation_decision_requires_source_boundary")
    if (
        decision_kind in _ADDITIVE_MATERIALIZATION_DECISION_KINDS
        and mutation_boundary != "additive_artifact_materialization_allowed"
    ):
        raise HumanDecisionRecordError(
            "materialization_decision_requires_additive_artifact_boundary"
        )
    if (
        decision_kind in _SVG_POLISH_DECISION_KINDS
        and packet_recommendation != decision_kind
    ):
        raise HumanDecisionRecordError("svg_polish_handoff_requires_packet_recommendation")

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


def validate_source_mutation_authorization(
    record: dict[str, Any],
    *,
    fixture: str,
    decision_kind: str,
    candidate_id: str,
    candidate_hash: str,
    packet_schema: str | None = None,
    packet_recommendation: str | None = None,
    packet_path: str | None = None,
) -> dict[str, Any]:
    """Validate one named decision bound to one exact source-mutation candidate."""
    normalized = validate_decision_record(record)
    if normalized["fixture"] != fixture:
        raise HumanDecisionRecordError("source_mutation_decision_fixture_mismatch")
    if normalized["decision_kind"] != decision_kind:
        raise HumanDecisionRecordError("source_mutation_decision_kind_invalid")
    if normalized["mutation_boundary"] != "source_mutation_allowed":
        raise HumanDecisionRecordError("source_mutation_decision_boundary_invalid")
    if packet_schema is not None and normalized["packet_schema"] != packet_schema:
        raise HumanDecisionRecordError("source_mutation_decision_packet_schema_mismatch")
    if (
        packet_recommendation is not None
        and normalized["packet_recommendation"] != packet_recommendation
    ):
        raise HumanDecisionRecordError(
            "source_mutation_decision_packet_recommendation_mismatch"
        )
    if packet_path is not None and normalized["packet_path"] != packet_path:
        raise HumanDecisionRecordError("source_mutation_decision_packet_path_mismatch")
    authorized_candidate_id = _required_string(record, "authorized_candidate_id")
    authorized_candidate_hash = _required_string(record, "authorized_candidate_hash")
    if authorized_candidate_id != candidate_id:
        raise HumanDecisionRecordError("source_mutation_decision_candidate_id_mismatch")
    if authorized_candidate_hash != candidate_hash:
        raise HumanDecisionRecordError("source_mutation_decision_candidate_hash_mismatch")
    return {
        **normalized,
        "authorized_candidate_id": authorized_candidate_id,
        "authorized_candidate_hash": authorized_candidate_hash,
    }


def validate_additive_materialization_authorization(
    record: dict[str, Any],
    *,
    fixture: str,
    packet_schema: str,
    packet_sha256: str,
    output_path: str,
    output_sha256: str,
    preview_sha256: str,
) -> dict[str, Any]:
    """Validate one named decision bound to one additive repair artifact."""
    normalized = validate_decision_record(record)
    expected_kind = "materialize_authoring_repair_candidate"
    if normalized["fixture"] != fixture:
        raise HumanDecisionRecordError("materialization_decision_fixture_mismatch")
    if (
        packet_schema not in AUTHORING_REPAIR_PACKET_SCHEMAS
        or normalized["packet_schema"] != packet_schema
    ):
        raise HumanDecisionRecordError("materialization_decision_packet_schema_mismatch")
    if normalized["packet_recommendation"] != expected_kind:
        raise HumanDecisionRecordError(
            "materialization_decision_packet_recommendation_mismatch"
        )
    if normalized["decision_kind"] != expected_kind:
        raise HumanDecisionRecordError("materialization_decision_kind_invalid")
    if normalized["mutation_boundary"] != "additive_artifact_materialization_allowed":
        raise HumanDecisionRecordError("materialization_decision_boundary_invalid")
    reviewer = _required_string(record, "reviewer")
    authorized_packet_sha256 = _required_string(record, "authorized_packet_sha256")
    authorized_output_path = _required_string(record, "authorized_output_path")
    authorized_output_sha256 = _required_string(record, "authorized_output_sha256")
    authorized_preview_sha256 = _required_string(record, "authorized_preview_sha256")
    if authorized_packet_sha256 != packet_sha256:
        raise HumanDecisionRecordError("materialization_decision_packet_hash_mismatch")
    if authorized_output_path != output_path:
        raise HumanDecisionRecordError("materialization_decision_output_path_mismatch")
    if authorized_output_sha256 != output_sha256:
        raise HumanDecisionRecordError("materialization_decision_output_hash_mismatch")
    if authorized_preview_sha256 != preview_sha256:
        raise HumanDecisionRecordError("materialization_decision_preview_hash_mismatch")
    return {
        **normalized,
        "reviewer": reviewer,
        "authorized_packet_sha256": authorized_packet_sha256,
        "authorized_output_path": authorized_output_path,
        "authorized_output_sha256": authorized_output_sha256,
        "authorized_preview_sha256": authorized_preview_sha256,
    }
