"""Read-only fixture queue over the dry-run figure driver."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import design_direction_packet  # noqa: E402
import fig_driver  # noqa: E402
import runtime_paths  # noqa: E402
import style_benchmark_comparison  # noqa: E402
import style_benchmark_pack  # noqa: E402
from driver_actor import (  # noqa: E402
    blocking_source_for_driver_summary,
    required_actor_for_driver_summary,
    requires_human_for_driver_summary,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.fixture-driver-queue.v1"
COMMAND_PLAN_SCHEMA = "figure-agent.fixture-command-plan.v1"
OPERATOR_HANDOFF_SCHEMA = "figure-agent.queue-operator-handoff.v1"
HUMAN_DECISION_PACKET_SCHEMA = "figure-agent.human-decision-packet.v1"
RELEASE_DECISION_PACKET_SCHEMA = "figure-agent.release-decision-packet.v1"
STYLE_DIRECTION_PACKET_SCHEMA = "figure-agent.style-direction-packet.v1"
SVG_POLISH_EVIDENCE_PACKET_SCHEMA = "figure-agent.svg-polish-readiness-evidence.v1"
HUMAN_DECISION_RECORD_SCHEMA = "figure-agent.human-decision-record.v1"
HUMAN_DECISION_DIGEST_SCHEMA = "figure-agent.human-decision-digest.v1"
BOTTLENECK_REPORT_SCHEMA = "figure-agent.queue-bottleneck-report.v1"
WORKSPACE_DIAGNOSTIC_SCHEMA = "figure-agent.queue-workspace-diagnostic.v1"
BOTTLENECK_CATEGORIES = (
    "mechanical_tool",
    "host_critique",
    "human_acceptance",
    "reference_context",
    "template_style",
)
BOTTLENECK_CATEGORY_DEFINITIONS = {
    "mechanical_tool": "source, render, export, closeout, or deterministic tool work",
    "host_critique": "host LLM critique or adjudication judgment work",
    "human_acceptance": "human, acceptance, release, publication, or golden-state gate",
    "reference_context": "missing or stale reference, briefing, or context input",
    "template_style": "SVG polish, template, editorial, style, palette, or aesthetic gate",
}
HUMAN_DECISION_KINDS = (
    "accept_current_generated_export",
    "declare_final_artifact",
    "reject_current_artifact",
    "defer_for_dogfood",
    "keep_current_style",
    "request_bounded_tikz_polish",
    "request_restrained_tikz_refinement",
    "request_editorial_redesign_benchmark",
    "request_svg_polish_candidate_evidence",
    "request_svg_polish_handoff_evidence",
    "request_full_style_redesign",
)
MUTATION_BOUNDARIES = (
    "no_source_mutation",
    "source_mutation_allowed",
    "release_state_mutation_allowed",
    "golden_mutation_allowed",
)
_FILTER_KEYS = (
    "required_actor",
    "action",
    "stop_boundary",
    "first_blocker",
    "blocking_source",
    "svg_polish_gate_state",
    "can_start_svg_polish",
    "svg_polish_recommended_path",
    "svg_polish_next_action",
    "svg_polish_blocking_sources",
    "polish_blocker_reason",
    "svg_polish_evidence_state",
    "style_benchmark_pack_state",
    "style_benchmark_comparison_state",
)
_ACTORS = (
    "workflow_agent",
    "host_llm",
    "human",
    "release_operator",
    "svg_editor",
)
_EXECUTABLE_ACTIONS = frozenset(
    {
        fig_driver.ACTION_RUN_ADJUDICATE,
        fig_driver.ACTION_RUN_COMPILE,
        fig_driver.ACTION_RUN_EXPORT,
        fig_driver.ACTION_RUN_FIG_LOOP,
    }
)
_MECHANICAL_ACTIONS = frozenset(
    {
        "error",
        fig_driver.ACTION_CREATE_OR_FIX_SOURCE,
        fig_driver.ACTION_RUN_ADJUDICATE,
        fig_driver.ACTION_RUN_COMPILE,
        fig_driver.ACTION_RUN_EXPORT,
        fig_driver.ACTION_RUN_FIG_LOOP,
    }
)


def _fixture_names(repo_root: Path, fixtures: list[str] | None) -> list[str]:
    if fixtures:
        return list(fixtures)
    examples_dir = repo_root / "examples"
    if not examples_dir.is_dir():
        return []
    return sorted(
        path.name
        for path in examples_dir.iterdir()
        if path.is_dir() and (path / "spec.yaml").is_file()
    )


def _workspace_diagnostic(repo_root: Path, fixtures: list[str] | None) -> dict[str, Any] | None:
    if fixtures:
        return None
    examples_dir = repo_root / "examples"
    if examples_dir.is_dir():
        return None
    return {
        "schema": WORKSPACE_DIAGNOSTIC_SCHEMA,
        "state": "missing_examples",
        "workspace_root": str(repo_root),
        "missing": ["examples"],
        "message": (
            "implicit queue discovery found no examples/ directory; run from the "
            "figure-agent plugin root or set FIGURE_AGENT_WORKSPACE/CLAUDE_PROJECT_DIR "
            "to a workspace with examples/"
        ),
    }


def _print_workspace_diagnostic(queue: dict[str, Any]) -> None:
    diagnostic = queue.get("workspace_diagnostic")
    if not isinstance(diagnostic, dict):
        return
    message = diagnostic.get("message")
    if isinstance(message, str) and message:
        print(f"fig_queue.py: {message}", file=sys.stderr)


def workspace_diagnostic_exit_code(queue: dict[str, Any]) -> int:
    diagnostic = queue.get("workspace_diagnostic")
    if isinstance(diagnostic, dict) and diagnostic.get("state") == "missing_examples":
        return 2
    return 0


def _first_blocker(summary: dict[str, Any]) -> str | None:
    status_explanation = summary.get("status_explanation")
    if not isinstance(status_explanation, dict):
        return None
    blocker = status_explanation.get("first_blocker")
    if not isinstance(blocker, dict):
        return None
    code = blocker.get("code")
    if not isinstance(code, str):
        return None
    stripped = code.strip()
    if not stripped or stripped == "none":
        return None
    return stripped


def _row_from_summary(
    summary: dict[str, Any], *, mode: str, repo_root: Path
) -> dict[str, Any]:
    status = summary.get("status")
    if not isinstance(status, dict):
        status = {}
    raw_action = summary.get("action")
    action = raw_action
    next_action = summary.get("next_action_summary")
    if isinstance(next_action, dict) and next_action.get("action") == fig_driver.ACTION_COMPLETE:
        boundary = next_action.get("decision_boundary")
        blocks_progress = isinstance(boundary, dict) and boundary.get("blocks_progress") is True
        if not blocks_progress:
            action = fig_driver.ACTION_COMPLETE
    row = {
        "fixture": summary.get("fixture"),
        "mode": mode,
        "action": action,
        "driver_action": raw_action,
        "stop_boundary": summary.get("stop_boundary"),
        "first_blocker": _first_blocker(summary),
        "safe_command": (
            None if action == fig_driver.ACTION_COMPLETE else summary.get("safe_command")
        ),
        "render_state": status.get("render_state"),
        "critique_state": status.get("critique_state"),
        "export_state": status.get("export_state"),
        "acceptance_state": status.get("acceptance_state"),
        "final_artifact_state": status.get("final_artifact_state"),
        "final_artifact_kind": status.get("final_artifact_kind"),
        "final_artifact_path": status.get("final_artifact_path"),
        "publication_gate_state": status.get("publication_gate_state"),
        "publication_gate_failures": status.get("publication_gate_failures"),
        "release_ready": status.get("release_ready"),
        "required_actor": required_actor_for_driver_summary(summary),
        "blocking_source": blocking_source_for_driver_summary(summary),
        "requires_human": requires_human_for_driver_summary(summary),
    }
    guidance = summary.get("operator_guidance")
    if isinstance(guidance, dict):
        row["operator_guidance"] = guidance
    closeout = summary.get("closeout")
    if isinstance(closeout, dict):
        if "closeout_complete" in closeout:
            row["closeout_complete"] = closeout.get("closeout_complete") is True
        next_action = closeout.get("next_action")
        if isinstance(next_action, str) and next_action:
            row["closeout_next_action"] = next_action
        blocking_step_ids = closeout.get("blocking_step_ids")
        if isinstance(blocking_step_ids, list):
            row["closeout_blocking_step_ids"] = [
                step_id
                for step_id in blocking_step_ids
                if isinstance(step_id, str) and step_id
            ]
    row.update(_svg_polish_fields(summary, mode=mode))
    fixture = row.get("fixture")
    if isinstance(fixture, str) and fixture:
        row.update(_style_benchmark_pack_fields(fixture, workspace_root=repo_root))
        row.update(_style_benchmark_comparison_fields(fixture, workspace_root=repo_root))
    polish_blocker = _polish_blocker_detail(row, mode=mode)
    if polish_blocker is not None:
        row["polish_blocker"] = polish_blocker
        row["polish_blocker_reason"] = polish_blocker["reason"]
    svg_polish_evidence = _svg_polish_evidence_packet(row, mode=mode)
    if svg_polish_evidence is not None:
        row["svg_polish_evidence_packet"] = svg_polish_evidence
        row["svg_polish_evidence_state"] = svg_polish_evidence["state"]
    if isinstance(fixture, str) and fixture:
        row.update(_design_direction_fields(fixture, row))
    decision_packet = _release_decision_packet(row)
    if decision_packet is not None:
        row["decision_packet"] = decision_packet
    style_packet = _style_direction_packet(row)
    if style_packet is not None:
        row["style_direction_packet"] = style_packet
    category = _bottleneck_category_for_row(row)
    if category is not None:
        row["bottleneck_category"] = category
    return row


def validate_human_decision_record(record: dict[str, Any]) -> list[str]:
    """Return validation errors for a durable human decision record."""
    errors: list[str] = []
    required_string_fields = (
        "fixture",
        "packet_schema",
        "packet_run_id",
        "decision_kind",
        "agent_recommendation",
        "human_decision",
        "human_note",
        "follow_up",
        "mutation_boundary",
    )
    if record.get("schema") != HUMAN_DECISION_RECORD_SCHEMA:
        errors.append("schema must be figure-agent.human-decision-record.v1")
    for field in required_string_fields:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")
    decision_kind = record.get("decision_kind")
    if isinstance(decision_kind, str) and decision_kind not in HUMAN_DECISION_KINDS:
        errors.append(f"decision_kind must be one of {', '.join(HUMAN_DECISION_KINDS)}")
    mutation_boundary = record.get("mutation_boundary")
    if isinstance(mutation_boundary, str) and mutation_boundary not in MUTATION_BOUNDARIES:
        errors.append(f"mutation_boundary must be one of {', '.join(MUTATION_BOUNDARIES)}")
    packet_schema = record.get("packet_schema")
    if packet_schema == STYLE_DIRECTION_PACKET_SCHEMA and mutation_boundary in {
        "release_state_mutation_allowed",
        "golden_mutation_allowed",
    }:
        errors.append("style decisions must not authorize release or golden mutation")
    if decision_kind in {"accept_current_generated_export", "declare_final_artifact"} and (
        mutation_boundary == "golden_mutation_allowed"
    ):
        errors.append("release acceptance decisions must not imply golden mutation")
    return errors


def _style_benchmark_pack_fields(name: str, *, workspace_root: Path) -> dict[str, Any]:
    try:
        payload = style_benchmark_pack.load_pack(name, workspace_root=workspace_root)
    except (
        OSError,
        json.JSONDecodeError,
        style_benchmark_pack.StyleBenchmarkPackError,
    ) as exc:
        return {
            "style_benchmark_pack_state": "invalid",
            "style_benchmark_pack_error": str(exc),
        }
    summary = style_benchmark_pack.summarize_pack(payload)
    state = summary.get("state")
    fields = {
        "style_benchmark_pack_state": state,
        "style_benchmark_pack_path": summary.get("path"),
    }
    if state != "present":
        return {key: value for key, value in fields.items() if value is not None}
    fields["style_benchmark_pack"] = summary
    return fields


def _style_benchmark_comparison_fields(name: str, *, workspace_root: Path) -> dict[str, Any]:
    try:
        payload = style_benchmark_comparison.load_comparison(name, workspace_root=workspace_root)
        if payload.get("state") not in {None, "present"}:
            return {"style_benchmark_comparison_state": payload.get("state")}
    except style_benchmark_comparison.StyleBenchmarkComparisonError as exc:
        state = "missing" if str(exc) == "comparison_missing" else "invalid"
        fields = {"style_benchmark_comparison_state": state}
        if state == "invalid":
            fields["style_benchmark_comparison_error"] = str(exc)
        return fields
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "style_benchmark_comparison_state": "invalid",
            "style_benchmark_comparison_error": str(exc),
        }
    summary = style_benchmark_comparison.summarize_comparison(payload)
    fields = {
        "style_benchmark_comparison_state": summary.get("state"),
        "style_benchmark_comparison_path": summary.get("path"),
    }
    if summary.get("state") == "present":
        fields["style_benchmark_comparison"] = summary
    return {key: value for key, value in fields.items() if value is not None}


def _design_direction_source_payload(
    row: dict[str, Any], *, prefix: str
) -> dict[str, object] | None:
    payload = row.get(prefix)
    if isinstance(payload, dict):
        return payload
    state = row.get(f"{prefix}_state")
    if isinstance(state, str) and state:
        return {"state": state}
    return None


def _design_direction_fields(fixture: str, row: dict[str, Any]) -> dict[str, Any]:
    packet = design_direction_packet.build_design_direction_packet(
        fixture,
        queue_row=row,
        style_pack=_design_direction_source_payload(row, prefix="style_benchmark_pack"),
        comparison=_design_direction_source_payload(row, prefix="style_benchmark_comparison"),
        svg_polish_state={"state": row.get("svg_polish_evidence_state", "not_checked")},
    )
    fields: dict[str, Any] = {
        "design_direction_state": packet.get("state"),
        "design_direction_packet_schema": packet.get("schema"),
        "design_direction_next_agent_action": packet.get("next_agent_action"),
    }
    summary: dict[str, Any] = {
        "state": packet.get("state"),
        "schema": packet.get("schema"),
        "next_agent_action": packet.get("next_agent_action"),
    }
    if packet.get("default_recommendation") is not None:
        fields["design_direction_default"] = packet.get("default_recommendation")
        summary["default_recommendation"] = packet.get("default_recommendation")
    alternatives = packet.get("alternatives")
    if isinstance(alternatives, list):
        normalized_alternatives = [
            alternative for alternative in alternatives if isinstance(alternative, str)
        ]
        fields["design_direction_alternatives"] = normalized_alternatives
        summary["alternatives"] = normalized_alternatives
    if packet.get("mutation_boundary") is not None:
        fields["design_direction_mutation_boundary"] = packet.get("mutation_boundary")
        summary["mutation_boundary"] = packet.get("mutation_boundary")
    alternative_boundaries = packet.get("alternative_mutation_boundaries")
    if isinstance(alternative_boundaries, dict):
        normalized_boundaries = {
            key: value
            for key, value in alternative_boundaries.items()
            if isinstance(key, str) and isinstance(value, str)
        }
        fields["design_direction_alternative_mutation_boundaries"] = normalized_boundaries
        summary["alternative_mutation_boundaries"] = normalized_boundaries
    if packet.get("human_question") is not None:
        fields["design_direction_human_question"] = packet.get("human_question")
        summary["human_question"] = packet.get("human_question")
    evidence_refs = packet.get("evidence_refs")
    if isinstance(evidence_refs, list):
        normalized_refs = [
            ref for ref in evidence_refs if isinstance(ref, str)
        ]
        fields["design_direction_evidence_refs"] = normalized_refs
        summary["evidence_refs"] = normalized_refs
    candidate_evidence = packet.get("candidate_family_evidence")
    if isinstance(candidate_evidence, dict):
        normalized_candidate_evidence = {
            key: value
            for key, value in candidate_evidence.items()
            if isinstance(key, str) and isinstance(value, dict)
        }
        if normalized_candidate_evidence:
            fields["design_direction_candidate_family_evidence"] = (
                normalized_candidate_evidence
            )
            summary["candidate_family_evidence"] = normalized_candidate_evidence
    blocker_reasons = packet.get("blocking_reasons")
    if isinstance(blocker_reasons, list) and blocker_reasons:
        normalized_blockers = [
            reason for reason in blocker_reasons if isinstance(reason, str)
        ]
        if normalized_blockers:
            fields["design_direction_blocker_reason"] = normalized_blockers[0]
            summary["blocking_reasons"] = normalized_blockers
    if row.get("svg_polish_evidence_state") in {
        "blocked_missing_positive_readiness",
        "not_qualified",
    }:
        fields.setdefault("design_direction_blocker_reason", "svg_polish_evidence_missing")
        summary.setdefault("blocking_reasons", ["svg_polish_evidence_missing"])
    fields["design_direction_summary"] = {
        key: value for key, value in summary.items() if value is not None
    }
    if (
        packet.get("state") == "ready_for_human_choice"
        and row.get("action") == fig_driver.ACTION_COMPLETE
    ):
        fields["required_actor"] = "human"
        fields["requires_human"] = True
        fields["blocking_source"] = "design_direction_human_choice"
    return fields


def _svg_polish_fields(summary: dict[str, Any], *, mode: str) -> dict[str, Any]:
    if mode != "polish":
        return {}
    fields: dict[str, Any] = {}
    gate = summary.get("svg_polish_gate")
    if isinstance(gate, dict):
        fields["svg_polish_gate_state"] = gate.get("state")
        fields["can_start_svg_polish"] = gate.get("can_start_svg_polish")
        fields["svg_polish_next_action"] = gate.get("next_action")
        gate_sources = _svg_polish_blocking_sources(gate)
        if gate_sources:
            fields["svg_polish_blocking_sources"] = gate_sources
    readiness = summary.get("svg_polish_readiness")
    if isinstance(readiness, dict):
        fields.setdefault("can_start_svg_polish", readiness.get("can_start_svg_polish"))
        fields.setdefault("svg_polish_next_action", readiness.get("next_action"))
        fields["svg_polish_recommended_path"] = readiness.get("recommended_path")
        positive_evidence = readiness.get("positive_evidence")
        if isinstance(positive_evidence, list):
            normalized_positive = [
                item for item in positive_evidence if isinstance(item, str) and item
            ]
            if normalized_positive:
                fields["svg_polish_positive_evidence"] = normalized_positive
        readiness_sources = _svg_polish_blocking_sources(readiness)
        if readiness_sources:
            fields["svg_polish_blocking_sources"] = _merge_unique_strings(
                fields.get("svg_polish_blocking_sources"),
                readiness_sources,
            )
    return {key: value for key, value in fields.items() if value is not None}


def _merge_unique_strings(existing: Any, incoming: list[str]) -> list[str]:
    merged: list[str] = []
    for values in (existing, incoming):
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, str) and value and value not in merged:
                merged.append(value)
    return merged


def _svg_polish_blocking_sources(readiness: dict[str, Any]) -> list[str]:
    sources: list[str] = []
    blocking_items = readiness.get("blocking_items")
    if not isinstance(blocking_items, list):
        return sources
    for item in blocking_items:
        if not isinstance(item, dict):
            continue
        source = item.get("source")
        if isinstance(source, str) and source and source not in sources:
            sources.append(source)
    return sources


def _error_row(name: str, *, mode: str, stop_boundary: str, error: str) -> dict[str, Any]:
    return {
        "fixture": name,
        "mode": mode,
        "action": "error",
        "stop_boundary": stop_boundary,
        "first_blocker": stop_boundary,
        "safe_command": None,
        "render_state": None,
        "critique_state": None,
        "export_state": None,
        "acceptance_state": None,
        "publication_gate_state": None,
        "release_ready": None,
        "required_actor": "workflow_agent",
        "blocking_source": stop_boundary,
        "requires_human": False,
        "bottleneck_category": "mechanical_tool",
        "error": error,
    }


def _count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(key)
        if isinstance(value, str) and value:
            counts[value] += 1
    return dict(sorted(counts.items()))


def _count_list_items(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str) and item:
                counts[item] += 1
    return dict(sorted(counts.items()))


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "total": len(rows),
        "errors": sum(1 for row in rows if row.get("action") == "error"),
        "by_action": _count(rows, "action"),
        "by_stop_boundary": _count(rows, "stop_boundary"),
        "by_first_blocker": _count(rows, "first_blocker"),
        "by_required_actor": _count(rows, "required_actor"),
        "by_blocking_source": _count(rows, "blocking_source"),
        "by_bottleneck_category": _count(rows, "bottleneck_category"),
    }
    by_svg_gate = _count(rows, "svg_polish_gate_state")
    if by_svg_gate:
        summary["by_svg_polish_gate_state"] = by_svg_gate
    by_svg_path = _count(rows, "svg_polish_recommended_path")
    if by_svg_path:
        summary["by_svg_polish_recommended_path"] = by_svg_path
    by_svg_next = _count(rows, "svg_polish_next_action")
    if by_svg_next:
        summary["by_svg_polish_next_action"] = by_svg_next
    by_svg_blocker = _count_list_items(rows, "svg_polish_blocking_sources")
    if by_svg_blocker:
        summary["by_svg_polish_blocking_source"] = by_svg_blocker
    by_polish_blocker = _count(rows, "polish_blocker_reason")
    if by_polish_blocker:
        summary["by_polish_blocker_reason"] = by_polish_blocker
    by_svg_polish_evidence = _count(rows, "svg_polish_evidence_state")
    if by_svg_polish_evidence:
        summary["by_svg_polish_evidence_state"] = by_svg_polish_evidence
    by_style_pack = _count(rows, "style_benchmark_pack_state")
    if by_style_pack:
        summary["by_style_benchmark_pack_state"] = by_style_pack
    by_style_comparison = _count(rows, "style_benchmark_comparison_state")
    if by_style_comparison:
        summary["by_style_benchmark_comparison_state"] = by_style_comparison
    by_design_direction = _count(rows, "design_direction_state")
    if by_design_direction:
        summary["by_design_direction_state"] = by_design_direction
    return summary


def _active_filters(filters: dict[str, str | None] | None) -> dict[str, str]:
    if not filters:
        return {}
    return {
        key: value.strip()
        for key, value in filters.items()
        if key in _FILTER_KEYS and isinstance(value, str) and value.strip()
    }


def _filter_rows(
    rows: list[dict[str, Any]],
    filters: dict[str, str],
) -> list[dict[str, Any]]:
    if not filters:
        return list(rows)
    return [
        row
        for row in rows
        if all(_filter_value_matches(row.get(key), value) for key, value in filters.items())
    ]


def _filter_value_matches(row_value: Any, filter_value: str) -> bool:
    if isinstance(row_value, bool):
        lowered = filter_value.lower()
        if lowered not in {"true", "false"}:
            return False
        return row_value is (lowered == "true")
    if isinstance(row_value, list):
        return filter_value in row_value
    return row_value == filter_value


def _blocked_reason(row: dict[str, Any]) -> str | None:
    actor = row.get("required_actor")
    if actor != "workflow_agent":
        return f"required_actor:{_cell(actor)}"
    if row.get("requires_human") is True:
        return "requires_human:true"
    stop_boundary = row.get("stop_boundary")
    if isinstance(stop_boundary, str) and stop_boundary:
        return f"stop_boundary:{stop_boundary}"
    safe_command = row.get("safe_command")
    if not isinstance(safe_command, str) or not safe_command:
        return "safe_command:missing"
    action = row.get("action")
    if action not in _EXECUTABLE_ACTIONS:
        return f"action:not_executable:{_cell(action)}"
    if action == fig_driver.ACTION_RUN_EXPORT and not _export_row_is_safe(row):
        return "export:safety_predicate_failed"
    return None


def _export_row_is_safe(row: dict[str, Any]) -> bool:
    command = row.get("safe_command")
    fixture = row.get("fixture")
    if not isinstance(command, str) or not isinstance(fixture, str) or not fixture:
        return False
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    return (
        parts == ["fig-agent", "export", fixture]
        and row.get("acceptance_state") == "NOT_DECLARED"
        and row.get("export_state") in {"MISSING", "STALE"}
        and row.get("critique_state") in {"FRESH", "NOT_REQUIRED"}
    )


def _host_llm_handoff_details(row: dict[str, Any]) -> dict[str, Any]:
    first_blocker = _cell(row.get("first_blocker"))
    blocking_source = _cell(row.get("blocking_source"))
    category = _effective_bottleneck_category(row) or "host_critique"
    details = {
        "first_blocker": first_blocker,
        "blocking_source": blocking_source,
        "bottleneck_category": category,
    }
    if category == "reference_context":
        if first_blocker == "critique_briefing_required":
            return details | {
                "handoff_kind": "critique_briefing_required",
                "next_step": (
                    "Prepare explicit briefing/reference context, then run host-vision "
                    "critique for this fixture."
                ),
                "allowed_scope_extra": [
                    f"examples/{_cell(row.get('fixture'))}/spec.yaml",
                    f"examples/{_cell(row.get('fixture'))}/reference/",
                ],
                "closeout_checks_extra": [
                    "confirm briefing/reference inputs are present before critique",
                ],
            }
        return details | {
            "handoff_kind": "reference_context_required",
            "next_step": (
                "Fix declared reference/context inputs, then run host-vision "
                "critique for this fixture."
            ),
            "allowed_scope_extra": [
                f"examples/{_cell(row.get('fixture'))}/spec.yaml",
                f"examples/{_cell(row.get('fixture'))}/reference/",
            ],
            "closeout_checks_extra": [
                "confirm reference/context paths resolve before critique",
            ],
        }
    if first_blocker == "critique_stale":
        return details | {
            "handoff_kind": "critique_stale_refresh",
            "next_step": "Refresh stale host-vision critique for this fixture.",
            "allowed_scope_extra": [],
            "closeout_checks_extra": [],
        }
    return details | {
        "handoff_kind": "host_critique_refresh",
        "next_step": "Refresh host-vision critique for this fixture.",
        "allowed_scope_extra": [],
        "closeout_checks_extra": [],
    }


def _decision_packet_evidence_refs(row: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("first_blocker", "blocking_source", "stop_boundary"):
        value = row.get(key)
        if isinstance(value, str) and value and value != "-":
            refs.append(f"{key}:{value}")
    if row.get("closeout_complete") is True:
        refs.append("closeout:complete_not_acceptance")
    return refs


def _human_decision_packet(row: dict[str, Any], *, actor: str) -> dict[str, Any]:
    fixture = _cell(row.get("fixture"))
    first_blocker = _cell(row.get("first_blocker"))
    blocking_source = _cell(row.get("blocking_source"))
    stop_boundary = _cell(row.get("stop_boundary"))
    common = {
        "schema": HUMAN_DECISION_PACKET_SCHEMA,
        "fixture": fixture,
        "required_actor": actor,
        "evidence_refs": _decision_packet_evidence_refs(row),
        "follow_up": {
            "after_decision": "rerun /fig_queue",
            "do_not_do": [
                "do not ask the human to inspect raw artifacts without a recommendation",
                "do not mutate accepted, golden, or publication state implicitly",
            ],
        },
    }
    if actor == "release_operator":
        return common | {
            "packet_kind": "approval_packet",
            "human_question": (
                f"I recommend a bounded release/golden decision for `{fixture}`. "
                "Approve the explicit roll-forward only if the prepared visual "
                "preview/diff is acceptable?"
            ),
            "agent_recommendation": (
                "Keep this as an explicit release decision. If the current build "
                "preview is acceptable, approve the bounded roll-forward; otherwise "
                "defer for another dogfood or visual-polish pass."
            ),
            "recommended_choice_id": "approve_bounded_roll_forward",
            "choices": [
                {
                    "id": "approve_bounded_roll_forward",
                    "label": "Approve bounded roll-forward",
                    "effect": "allow the operator to run the explicit force-golden/export step",
                },
                {
                    "id": "reject_and_keep_current_baseline",
                    "label": "Keep current baseline",
                    "effect": "leave tracked golden or release state unchanged",
                },
                {
                    "id": "defer_for_visual_dogfood",
                    "label": "Defer for visual dogfood",
                    "effect": "request another critique/style pass before release mutation",
                },
            ],
            "risks": [
                "approving changes the protected release/golden baseline",
                "rejecting may leave a fresh ready build unpromoted",
                "deferring preserves safety but delays release closure",
            ],
            "gate_context": {
                "first_blocker": first_blocker,
                "blocking_source": blocking_source,
                "stop_boundary": stop_boundary,
            },
        }
    return common | {
        "packet_kind": "choice_packet",
        "human_question": (
            f"`{fixture}` needs a bounded human decision. Should we accept the "
            "current review state, request one local polish pass, or open a broader "
            "redesign direction?"
        ),
        "agent_recommendation": (
            "Ask for a choice among concrete paths instead of asking for open-ended "
            "inspection. Default to accepting the current review state when no "
            "freshness or defect blocker remains."
        ),
        "recommended_choice_id": "accept_current_review_state",
        "choices": [
            {
                "id": "accept_current_review_state",
                "label": "Accept current review state",
                "effect": "record acceptance or proceed to the next release/final gate",
            },
            {
                "id": "request_bounded_polish_pass",
                "label": "Request bounded polish pass",
                "effect": "ask the agent to propose and apply one local style/hierarchy patch",
            },
            {
                "id": "request_redesign_direction",
                "label": "Request redesign direction",
                "effect": "stop local patching and prepare broader art-direction alternatives",
            },
        ],
        "risks": [
            "accepting may lock in a merely solid style",
            "bounded polish can improve finish but may not change the overall style class",
            "redesign can find a better visual language but expands scope materially",
        ],
        "gate_context": {
            "first_blocker": first_blocker,
            "blocking_source": blocking_source,
            "stop_boundary": stop_boundary,
        },
    }


def _release_current_state(row: dict[str, Any]) -> dict[str, Any]:
    state = {
        "render_state": row.get("render_state"),
        "critique_state": row.get("critique_state"),
        "export_state": row.get("export_state"),
        "acceptance_state": row.get("acceptance_state"),
        "final_artifact_state": row.get("final_artifact_state"),
        "final_artifact_kind": row.get("final_artifact_kind"),
        "final_artifact_path": row.get("final_artifact_path"),
        "publication_gate_state": row.get("publication_gate_state"),
        "publication_gate_failures": row.get("publication_gate_failures"),
        "release_ready": row.get("release_ready"),
    }
    if "closeout_complete" in row:
        state["closeout_complete"] = row.get("closeout_complete")
    if "closeout_next_action" in row:
        state["closeout_next_action"] = row.get("closeout_next_action")
    return state


def _release_decision_choices(row: dict[str, Any], *, force_golden: bool) -> list[dict[str, Any]]:
    fixture = _cell(row.get("fixture"))
    final_kind = row.get("final_artifact_kind")
    final_state = row.get("final_artifact_state")
    if force_golden:
        return [
            {
                "id": "approve_force_golden_roll_forward",
                "label": "Approve force-golden roll-forward",
                "effect": "allow the explicit protected golden update after preview/diff review",
                "risk": "changes the tracked release baseline for this fixture",
                "follow_up": {"command": f"fig-agent export {fixture} --force-golden"},
            },
            {
                "id": "reject_and_keep_current_golden",
                "label": "Keep current golden",
                "effect": "leave tracked golden and release state unchanged",
                "risk": "may leave a ready visual update unpromoted",
                "follow_up": {"command": None, "manual_record_path": "release review note"},
            },
            {
                "id": "defer_for_visual_dogfood",
                "label": "Defer for visual dogfood",
                "effect": "request another bounded review/style pass before baseline mutation",
                "risk": "preserves safety but delays release closure",
                "follow_up": {"command": "rerun /fig_queue --mode review"},
            },
        ]
    choices = [
        {
            "id": "accept_current_generated_export",
            "label": "Accept current generated export",
            "effect": (
                "record human acceptance for the generated export when the preview is acceptable"
            ),
            "risk": (
                "may lock in the current solid manuscript style without a broader "
                "visual-language redesign"
            ),
            "follow_up": {
                "command": None,
                "manual_record_path": (
                    f"examples/{fixture}/QUALITY_AUDIT.md and accepted: true in spec.yaml"
                ),
            },
        },
        {
            "id": "declare_final_artifact",
            "label": "Declare final artifact",
            "effect": (
                "record an explicit final artifact such as a polished SVG manifest "
                "when it is the intended release asset"
            ),
            "risk": (
                "a missing, stale, or invalid final artifact keeps release blocked "
                "until the declaration is repaired"
            ),
            "follow_up": {
                "command": None,
                "manual_record_path": f"examples/{fixture}/spec.yaml final_artifact",
            },
        },
        {
            "id": "reject_current_artifact",
            "label": "Reject current artifact",
            "effect": (
                "keep accepted/final-ready state unset and send the fixture back "
                "to dogfood or style work"
            ),
            "risk": "preserves quality control but delays release closure",
            "follow_up": {"command": "rerun /fig_queue after recording rejection"},
        },
        {
            "id": "defer_for_dogfood",
            "label": "Defer for dogfood",
            "effect": "postpone release mutation and request another bounded review/style slice",
            "risk": "safe default, but can keep a visually adequate fixture from shipping",
            "follow_up": {"command": "rerun /fig_queue --mode review"},
        },
    ]
    if final_kind == "polished_svg" and final_state in {
        "MISSING",
        "STALE",
        "INVALID",
        "BLOCKED",
    }:
        choices[1] = choices[1] | {
            "warning": (
                f"declared polished SVG final artifact is {final_state}; "
                "repair or refresh it before treating it as final"
            ),
        }
    if final_kind == "polished_svg" and final_state == "FRESH":
        choices[1] = choices[1] | {
            "evidence": "declared polished SVG final artifact is fresh",
        }
    return choices


def _release_decision_packet(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("action") != fig_driver.ACTION_RELEASE_BLOCKED:
        return None
    stop_boundary = row.get("stop_boundary")
    if stop_boundary not in {
        fig_driver.STOP_ACCEPTED_OR_FINAL_READY,
        fig_driver.STOP_FORCE_GOLDEN,
    }:
        return None
    fixture = _cell(row.get("fixture"))
    force_golden = stop_boundary == fig_driver.STOP_FORCE_GOLDEN
    packet_kind = (
        "force_golden_decision_packet" if force_golden else "release_acceptance_decision_packet"
    )
    question = (
        f"`{fixture}` has a tracked-golden release boundary. Should the release "
        "operator approve, reject, or defer the protected golden change?"
        if force_golden
        else f"`{fixture}` is release-blocked only by acceptance/final-artifact "
        "policy. Which explicit release decision should be recorded?"
    )
    publication_failures = row.get("publication_gate_failures")
    agent_publication_failures = (
        [
            failure
            for failure in publication_failures
            if isinstance(failure, dict) and failure.get("actor") == "agent"
        ]
        if isinstance(publication_failures, list)
        else []
    )
    acceptance_state = row.get("acceptance_state")
    if force_golden:
        recommendation = (
            "Do not force the tracked golden automatically. Ask the release "
            "operator to approve, reject, or defer the protected baseline change "
            "after reviewing the prepared diff."
        )
        recommended_choice = "defer_for_visual_dogfood"
    elif agent_publication_failures:
        recommendation = (
            "Resolve deterministic publication-gate failures before asking for "
            "human acceptance as the release-closing action."
        )
        recommended_choice = "defer_for_dogfood"
    elif acceptance_state == "NOT_ACCEPTED":
        recommendation = (
            "Resolve QUALITY_AUDIT.md defects before setting accepted: true in "
            "spec.yaml; this is not just a missing declaration."
        )
        recommended_choice = "defer_for_dogfood"
    else:
        recommendation = (
            "Keep the release boundary blocked until a human explicitly accepts "
            "the current generated export or declares a fresh final artifact."
        )
        recommended_choice = "accept_current_generated_export"
    return {
        "schema": RELEASE_DECISION_PACKET_SCHEMA,
        "packet_kind": packet_kind,
        "fixture": fixture,
        "boundary": stop_boundary,
        "required_actor": _cell(row.get("required_actor")),
        "current_state": _release_current_state(row),
        "human_question": question,
        "agent_recommendation": recommendation,
        "recommended_choice_id": recommended_choice,
        "choices": _release_decision_choices(row, force_golden=force_golden),
        "evidence_refs": _decision_packet_evidence_refs(row),
        "follow_up": {
            "after_decision": "rerun /fig_queue --mode release",
            "do_not_do": [
                "do not mutate accepted, golden, or publication state implicitly",
                "do not treat numeric scores as release authority",
            ],
        },
    }


def _style_direction_packet(row: dict[str, Any]) -> dict[str, Any] | None:
    action = row.get("action")
    stop_boundary = row.get("stop_boundary")
    eligible = action == fig_driver.ACTION_COMPLETE or (
        action == fig_driver.ACTION_RELEASE_BLOCKED
        and stop_boundary == fig_driver.STOP_ACCEPTED_OR_FINAL_READY
    )
    if not eligible:
        return None
    fixture = _cell(row.get("fixture"))
    release_blocked = action == fig_driver.ACTION_RELEASE_BLOCKED
    recommendation = (
        "keep_current_style_then_record_release_decision"
        if release_blocked
        else "keep_current_style_with_optional_bounded_tikz_polish"
    )
    packet = {
        "schema": STYLE_DIRECTION_PACKET_SCHEMA,
        "fixture": fixture,
        "state": "release_policy_blocked" if release_blocked else "review_complete",
        "current_style_assessment": (
            "No queue-visible defect blocker remains; the current visual language "
            "is acceptable as a solid manuscript schematic unless this fixture is "
            "being promoted to a flagship/cover-level visual."
        ),
        "agent_recommendation": recommendation,
        "evidence_refs": _decision_packet_evidence_refs(row)
        + [
            f"render_state:{_cell(row.get('render_state'))}",
            f"critique_state:{_cell(row.get('critique_state'))}",
            f"export_state:{_cell(row.get('export_state'))}",
        ],
        "choices": [
            {
                "id": "keep_current_style",
                "label": "Keep current style",
                "scope_change": False,
                "risk": "may remain solid-manuscript rather than flagship polish",
                "next_slice": (
                    "record acceptance/final-artifact decision"
                    if release_blocked
                    else "proceed to release queue"
                ),
            },
            {
                "id": "bounded_tikz_source_polish",
                "label": "Bounded TikZ source polish",
                "scope_change": False,
                "risk": "can improve hierarchy but should stay one local pass",
                "next_slice": "open one targeted typography/spacing/stroke polish task",
            },
            {
                "id": "svg_polish_handoff",
                "label": "SVG polish handoff",
                "scope_change": True,
                "risk": "requires positive ready_for_svg_polish evidence and sidecar artifacts",
                "next_slice": "run polish queue and require can_start_svg_polish=true",
            },
            {
                "id": "full_style_redesign",
                "label": "Full style redesign",
                "scope_change": True,
                "risk": "changes visual language and needs benchmark comparison",
                "next_slice": "create redesign alternatives against the benchmark fixture",
            },
        ],
        "does_not_block_release": True,
        "follow_up": {
            "after_decision": "rerun /fig_queue in the chosen mode",
            "do_not_do": [
                "do not mutate source or release state from this packet",
                "do not treat the packet as acceptance",
            ],
        },
    }
    pack_summary = row.get("style_benchmark_pack")
    if isinstance(pack_summary, dict):
        packet["style_benchmark_pack"] = pack_summary
    comparison_summary = row.get("style_benchmark_comparison")
    if isinstance(comparison_summary, dict):
        packet["style_benchmark_comparison"] = comparison_summary
    return packet


def _polish_blocker_detail(row: dict[str, Any], *, mode: str) -> dict[str, Any] | None:
    if mode != "polish" or row.get("stop_boundary") != fig_driver.STOP_MODE_FORBIDDEN:
        return None
    fixture = _cell(row.get("fixture"))
    sources = row.get("svg_polish_blocking_sources")
    source_list = (
        [item for item in sources if isinstance(item, str)]
        if isinstance(sources, list)
        else []
    )
    recommended_path = row.get("svg_polish_recommended_path")
    next_action = row.get("svg_polish_next_action")
    can_start = row.get("can_start_svg_polish")
    positive_evidence = row.get("svg_polish_positive_evidence")
    has_positive_evidence = isinstance(positive_evidence, list) and any(
        isinstance(item, str) and item for item in positive_evidence
    )
    if (
        (can_start is True or recommended_path == "ready_for_svg_polish")
        and not has_positive_evidence
    ):
        reason = "ready_for_svg_polish_positive_evidence_missing"
        upstream_packet = "style_direction_packet"
        next_step = "Collect positive ready_for_svg_polish evidence before opening SVG polish."
    elif can_start is True or recommended_path == "ready_for_svg_polish":
        reason = "ready_for_svg_polish"
        upstream_packet = "svg_polish_handoff"
        next_step = "Start the explicit SVG polish handoff; keep semantic/release gates intact."
    elif next_action == "resolve_release_boundary":
        reason = "accepted_or_final_ready_missing"
        upstream_packet = "release_decision_packet"
        next_step = "Resolve explicit acceptance/final-artifact policy before polish handoff."
    elif "driver_prerequisite" in source_list or next_action in {
        "run_fig_critique",
        "run_fig_adjudicate",
        "run_fig_export",
        "run_fig_compile",
    }:
        reason = "review_loop_prerequisite_not_closed"
        upstream_packet = "review_queue"
        next_step = "Close review/export prerequisites before considering SVG polish."
    elif recommended_path == "continue_tikz" or "tikz_vs_svg_polish_trigger" in source_list:
        reason = "continue_tikz_recommended"
        upstream_packet = "style_direction_packet"
        next_step = "Use bounded TikZ/source polish; SVG polish is not the current route."
    elif (
        any("manifest" in source or "delta" in source for source in source_list)
        or next_action in {
            "refresh_svg_polish_handoff",
            "repair_svg_polish_manifest",
        }
    ):
        reason = "svg_polish_artifact_missing_or_stale"
        upstream_packet = "svg_polish_handoff"
        next_step = "Repair or refresh SVG polish manifest/delta/semantic-diff artifacts."
    else:
        reason = "ready_for_svg_polish_evidence_missing"
        upstream_packet = "style_direction_packet"
        next_step = "Return to review/style-direction evidence before opening SVG polish."
    return {
        "fixture": fixture,
        "reason": reason,
        "upstream_packet": upstream_packet,
        "next_step": next_step,
        "can_start_svg_polish": can_start,
        "recommended_path": recommended_path,
        "blocking_sources": source_list,
    }


def _svg_polish_evidence_packet(row: dict[str, Any], *, mode: str) -> dict[str, Any] | None:
    if mode != "polish":
        return None
    fixture = _cell(row.get("fixture"))
    can_start = row.get("can_start_svg_polish")
    recommended_path = row.get("svg_polish_recommended_path")
    next_action = row.get("svg_polish_next_action")
    positive_evidence = row.get("svg_polish_positive_evidence")
    positive_evidence_list = (
        [item for item in positive_evidence if isinstance(item, str) and item]
        if isinstance(positive_evidence, list)
        else []
    )
    sources = row.get("svg_polish_blocking_sources")
    source_list = (
        [item for item in sources if isinstance(item, str)]
        if isinstance(sources, list)
        else []
    )
    is_positive = (
        can_start is True
        and recommended_path == "ready_for_svg_polish"
        and bool(positive_evidence_list)
    )
    packet: dict[str, Any] = {
        "schema": SVG_POLISH_EVIDENCE_PACKET_SCHEMA,
        "fixture": fixture,
        "state": "ready_for_svg_polish" if is_positive else "not_qualified",
        "can_start_svg_polish": can_start,
        "recommended_path": recommended_path,
        "next_action": next_action,
        "blocking_sources": source_list,
        "forbidden_scope": [
            "scientific repair in SVG",
            "semantic repair in SVG",
            "label-target repair in SVG",
            "release, export, or golden mutation from polish evidence",
        ],
        "human_gate": (
            "SVG artifact mutation still requires an explicit "
            "request_svg_polish_handoff_evidence decision record."
        ),
    }
    if is_positive:
        packet["positive_evidence"] = [
            "can_start_svg_polish=true",
            "recommended_path=ready_for_svg_polish",
            *positive_evidence_list,
        ]
        return packet

    reason = row.get("polish_blocker_reason")
    if not isinstance(reason, str) or not reason:
        reason = "ready_for_svg_polish_evidence_missing"
    if can_start is True and recommended_path == "ready_for_svg_polish":
        reason = "ready_for_svg_polish_positive_evidence_missing"
    packet["missing_prerequisite_reason"] = reason
    packet["required_positive_evidence"] = [
        "can_start_svg_polish=true",
        "recommended_path=ready_for_svg_polish",
        "positive_evidence[]",
    ]
    return packet


def _operator_handoff(row: dict[str, Any], *, reason: str) -> dict[str, Any]:
    fixture = _cell(row.get("fixture"))
    actor = _cell(row.get("required_actor"))
    common_forbidden = [
        "source edits",
        "export mutation",
        "accepted/golden mutation",
        "publication state mutation",
    ]
    if row.get("action") == fig_driver.ACTION_COMPLETE:
        guidance = row.get("operator_guidance")
        if isinstance(guidance, dict):
            next_step = guidance.get("next_step")
            if isinstance(next_step, str) and next_step.strip():
                return {
                    "schema": OPERATOR_HANDOFF_SCHEMA,
                    "fixture": fixture,
                    "required_actor": actor,
                    "style_direction_packet": row.get("style_direction_packet"),
                    "next_step": next_step,
                    "command": None,
                    "reason": reason,
                    "allowed_scope": ["read-only broader-mode inspection"],
                    "forbidden_scope": common_forbidden,
                    "closeout_checks": ["rerun /fig_queue in the next broader mode"],
                }
    if actor == "host_llm":
        details = _host_llm_handoff_details(row)
        return {
            "schema": OPERATOR_HANDOFF_SCHEMA,
            "fixture": fixture,
            "required_actor": actor,
            "handoff_kind": details["handoff_kind"],
            "first_blocker": details["first_blocker"],
            "blocking_source": details["blocking_source"],
            "bottleneck_category": details["bottleneck_category"],
            "next_step": details["next_step"],
            "command": row.get("safe_command"),
            "reason": reason,
            "allowed_scope": [
                f"examples/{fixture}/critique.md",
                f"examples/{fixture}/critique_adjudication.yaml",
                f"examples/{fixture}/build/audit_crops/",
                *details["allowed_scope_extra"],
            ],
            "forbidden_scope": common_forbidden,
            "closeout_checks": [
                "run critique_lint",
                "sync or scaffold critique_adjudication.yaml",
                *details["closeout_checks_extra"],
                "rerun /fig_queue",
            ],
        }
    if actor == "human":
        return {
            "schema": OPERATOR_HANDOFF_SCHEMA,
            "fixture": fixture,
            "required_actor": actor,
            "decision_packet": _human_decision_packet(row, actor=actor),
            "next_step": "Record the required human decision before continuing automation.",
            "command": None,
            "reason": reason,
            "allowed_scope": ["human decision record or acceptance decision"],
            "forbidden_scope": common_forbidden,
            "closeout_checks": ["rerun /fig_queue after recording the decision"],
        }
    if actor == "release_operator":
        return {
            "schema": OPERATOR_HANDOFF_SCHEMA,
            "fixture": fixture,
            "required_actor": actor,
            "decision_packet": row.get("decision_packet")
            or _human_decision_packet(row, actor=actor),
            "style_direction_packet": row.get("style_direction_packet"),
            "next_step": (
                "Review the fixture-specific release decision packet; do not force golden "
                "or acceptance implicitly."
            ),
            "command": None,
            "reason": reason,
            "allowed_scope": ["release/golden review with explicit approval"],
            "forbidden_scope": [
                "implicit --force-golden",
                "implicit accepted mutation",
                "source edits",
                "unreviewed export mutation",
            ],
            "closeout_checks": ["rerun /fig_queue after release decision"],
        }
    if actor == "svg_editor":
        polish_blocker = row.get("polish_blocker")
        return {
            "schema": OPERATOR_HANDOFF_SCHEMA,
            "fixture": fixture,
            "required_actor": actor,
            "polish_blocker": polish_blocker,
            "svg_polish_evidence_packet": row.get("svg_polish_evidence_packet"),
            "next_step": (
                polish_blocker["next_step"]
                if isinstance(polish_blocker, dict)
                else "Complete SVG polish handoff outside queue automation."
            ),
            "command": None,
            "reason": reason,
            "allowed_scope": ["declared polished SVG handoff scope"],
            "forbidden_scope": common_forbidden,
            "closeout_checks": ["rerun /fig_queue after polish handoff"],
        }
    if reason == "stop_boundary:closeout_required":
        return {
            "schema": OPERATOR_HANDOFF_SCHEMA,
            "fixture": fixture,
            "required_actor": actor,
            "next_step": "Run read-only closeout inspection before continuing automation.",
            "command": f"fig-agent closeout {shlex.quote(fixture)} --json",
            "reason": reason,
            "allowed_scope": ["read-only closeout inspection"],
            "forbidden_scope": common_forbidden,
            "closeout_checks": [
                "read JSON output even when exit code is 1",
                "follow closeout.next_action",
                "rerun /fig_queue after resolving the blocked row",
            ],
        }
    return {
        "schema": OPERATOR_HANDOFF_SCHEMA,
        "fixture": fixture,
        "required_actor": actor,
        "next_step": "Inspect the blocked queue row and rerun live driver state.",
        "command": None,
        "reason": reason,
        "allowed_scope": ["read-only inspection"],
        "forbidden_scope": common_forbidden,
        "closeout_checks": ["rerun /fig_queue after resolving the blocked row"],
    }


def build_command_plan(rows: list[dict[str, Any]]) -> dict[str, Any]:
    executable: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    complete: list[dict[str, Any]] = []
    for row in rows:
        if row.get("action") == fig_driver.ACTION_COMPLETE:
            reason = "mode_scoped_complete"
            item = {
                "fixture": row.get("fixture"),
                "action": row.get("action"),
                "required_actor": row.get("required_actor"),
                "blocking_source": row.get("blocking_source"),
                "stop_boundary": row.get("stop_boundary"),
                "reason": reason,
                "operator_handoff": _operator_handoff(row, reason=reason),
                "style_direction_packet": row.get("style_direction_packet"),
                "style_benchmark_pack_state": row.get("style_benchmark_pack_state"),
                "style_benchmark_comparison_state": row.get("style_benchmark_comparison_state"),
                "design_direction_state": row.get("design_direction_state"),
                "design_direction_summary": row.get("design_direction_summary"),
            }
            if row.get("svg_polish_evidence_state") is not None:
                item["svg_polish_evidence_state"] = row.get("svg_polish_evidence_state")
            complete.append(item)
            continue
        reason = _blocked_reason(row)
        if reason is None:
            item = {
                "fixture": row.get("fixture"),
                "action": row.get("action"),
                "safe_command": row.get("safe_command"),
                "required_actor": row.get("required_actor"),
            }
            if row.get("svg_polish_evidence_state") is not None:
                item["svg_polish_evidence_state"] = row.get("svg_polish_evidence_state")
            executable.append(item)
            continue
        item = {
            "fixture": row.get("fixture"),
            "action": row.get("action"),
            "required_actor": row.get("required_actor"),
            "blocking_source": row.get("blocking_source"),
            "stop_boundary": row.get("stop_boundary"),
            "polish_blocker_reason": row.get("polish_blocker_reason"),
            "reason": reason,
            "operator_handoff": _operator_handoff(row, reason=reason),
            "style_benchmark_pack_state": row.get("style_benchmark_pack_state"),
            "style_benchmark_comparison_state": row.get("style_benchmark_comparison_state"),
            "design_direction_state": row.get("design_direction_state"),
            "design_direction_summary": row.get("design_direction_summary"),
        }
        if row.get("svg_polish_evidence_state") is not None:
            item["svg_polish_evidence_state"] = row.get("svg_polish_evidence_state")
        blocked.append(item)
    return {
        "schema": COMMAND_PLAN_SCHEMA,
        "executable_count": len(executable),
        "blocked_count": len(blocked),
        "complete_count": len(complete),
        "executable": executable,
        "blocked": blocked,
        "complete": complete,
    }


def _bottleneck_leaders(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts = _count(rows, key)
    return [
        {"key": value, "count": count}
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _command_plan_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    plan = build_command_plan(rows)
    return {
        "executable": int(plan.get("executable_count", 0)),
        "blocked": int(plan.get("blocked_count", 0)),
        "complete": int(plan.get("complete_count", 0)),
    }




_DIGEST_GROUP_LABELS = {
    "accept_current_candidates": "accept-current candidates",
    "bounded_tikz_polish_candidates": "bounded TikZ polish candidates",
    "redesign_benchmark_candidates": "redesign benchmark candidates",
    "svg_polish_evidence_missing": "SVG-polish evidence missing",
    "dirty_stale_fixtures_excluded": "dirty/stale fixtures excluded from strategy work",
}
_DIGEST_NEXT_ACTIONS = {
    "accept_current_candidates": (
        "Record an explicit human release/style decision, then rerun /fig_queue --mode release."
    ),
    "bounded_tikz_polish_candidates": (
        "Open one bounded TikZ/source polish slice; avoid release/golden mutation."
    ),
    "redesign_benchmark_candidates": (
        "Prepare benchmark alternatives before changing the visual language."
    ),
    "svg_polish_evidence_missing": (
        "Collect or refresh SVG-polish readiness evidence before opening SVG editing."
    ),
    "dirty_stale_fixtures_excluded": (
        "Exclude from strategy work unless the human explicitly targets this fixture."
    ),
}


def _packet_recommendations(row: dict[str, Any]) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    design_schema = row.get("design_direction_packet_schema")
    design_recommendation = row.get("design_direction_default")
    if isinstance(design_schema, str) and isinstance(design_recommendation, str):
        recommendations.append(
            {"packet": design_schema, "recommendation": design_recommendation}
        )
    for key in ("decision_packet", "style_direction_packet"):
        packet = row.get(key)
        if not isinstance(packet, dict):
            continue
        schema = packet.get("schema")
        recommendation = packet.get("agent_recommendation")
        choice_id = packet.get("recommended_choice_id")
        if not isinstance(schema, str) or not isinstance(recommendation, str):
            continue
        item = {"packet": schema, "recommendation": recommendation}
        if isinstance(choice_id, str) and choice_id:
            item["recommended_choice_id"] = choice_id
        recommendations.append(item)
    return recommendations


def _packet_schemas(row: dict[str, Any]) -> list[str]:
    return [item["packet"] for item in _packet_recommendations(row)]


def _choice_risk(packet: dict[str, Any], choice_id: str | None) -> str | None:
    choices = packet.get("choices")
    if not isinstance(choices, list):
        return None
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        if choice_id is not None and choice.get("id") != choice_id:
            continue
        risk = choice.get("risk")
        if isinstance(risk, str) and risk:
            return risk
    return None


def _digest_one_line_risk(row: dict[str, Any]) -> str:
    decision_packet = row.get("decision_packet")
    if isinstance(decision_packet, dict):
        risk = _choice_risk(
            decision_packet,
            decision_packet.get("recommended_choice_id")
            if isinstance(decision_packet.get("recommended_choice_id"), str)
            else None,
        )
        if risk:
            return risk
        risks = decision_packet.get("risks")
        if isinstance(risks, list):
            for item in risks:
                if isinstance(item, str) and item:
                    return item
    style_packet = row.get("style_direction_packet")
    if isinstance(style_packet, dict):
        risk = _choice_risk(style_packet, "keep_current_style")
        if risk:
            return risk
    polish_reason = row.get("polish_blocker_reason")
    if isinstance(polish_reason, str) and polish_reason:
        return f"polish gate is blocked by {polish_reason}"
    first_blocker = row.get("first_blocker")
    if isinstance(first_blocker, str) and first_blocker and first_blocker != "-":
        return f"first blocker remains {first_blocker}"
    return "no queue-visible one-line risk was available"


def _row_is_dirty_stale_excluded(
    row: dict[str, Any], *, targeted_fixtures: set[str]
) -> bool:
    fixture = row.get("fixture")
    if not isinstance(fixture, str):
        return False
    if fixture == "fig5_actuation_mechanism" and fixture not in targeted_fixtures:
        return True
    if fixture in targeted_fixtures:
        return False
    if row.get("required_actor") in {"workflow_agent", "host_llm"}:
        return False
    signal = _row_signal_text(row)
    return "dirty" in signal and "stale" in signal


def _digest_group_key(row: dict[str, Any], *, targeted_fixtures: set[str]) -> str | None:
    if _row_is_dirty_stale_excluded(row, targeted_fixtures=targeted_fixtures):
        return "dirty_stale_fixtures_excluded"
    polish_reason = row.get("polish_blocker_reason")
    if polish_reason in {
        "svg_polish_artifact_missing_or_stale",
        "ready_for_svg_polish_evidence_missing",
        "ready_for_svg_polish_positive_evidence_missing",
    }:
        return "svg_polish_evidence_missing"
    evidence_packet = row.get("svg_polish_evidence_packet")
    if (
        isinstance(evidence_packet, dict)
        and evidence_packet.get("state") == "not_qualified"
        and (
            row.get("svg_polish_gate_state") is not None
            or row.get("svg_polish_recommended_path") is not None
            or row.get("can_start_svg_polish") is not None
        )
        and evidence_packet.get("missing_prerequisite_reason")
        in {
            "ready_for_svg_polish_evidence_missing",
            "ready_for_svg_polish_positive_evidence_missing",
        }
    ):
        return "svg_polish_evidence_missing"
    if polish_reason == "continue_tikz_recommended":
        return "bounded_tikz_polish_candidates"
    style_packet = row.get("style_direction_packet")
    if isinstance(style_packet, dict):
        recommendation = style_packet.get("agent_recommendation")
        if isinstance(recommendation, str) and "redesign" in recommendation:
            return "redesign_benchmark_candidates"
        return "accept_current_candidates"
    decision_packet = row.get("decision_packet")
    if isinstance(decision_packet, dict):
        recommended = decision_packet.get("recommended_choice_id")
        if recommended == "defer_for_visual_dogfood":
            return "redesign_benchmark_candidates"
        return "accept_current_candidates"
    design_state = row.get("design_direction_state")
    if design_state == "ready_for_human_choice":
        return "accept_current_candidates"
    if design_state in {"blocked_missing_style_pack", "blocked_missing_comparison"}:
        return "redesign_benchmark_candidates"
    if row.get("svg_polish_gate_state") == "blocked":
        return "svg_polish_evidence_missing"
    return None


def _digest_row(row: dict[str, Any], *, group: str) -> dict[str, Any]:
    fixture = _cell(row.get("fixture"))
    return {
        "fixture": fixture,
        "action": _cell(row.get("action")),
        "required_actor": _cell(row.get("required_actor")),
        "first_blocker": _cell(row.get("first_blocker")),
        "packet_schemas": _packet_schemas(row),
        "packet_recommendations": _packet_recommendations(row),
        "one_line_risk": _digest_one_line_risk(row),
        "style_benchmark_pack_state": row.get("style_benchmark_pack_state"),
        "style_benchmark_comparison_state": row.get("style_benchmark_comparison_state"),
        "design_direction_state": row.get("design_direction_state"),
        "design_direction_human_question": row.get("design_direction_human_question"),
        "design_direction_alternatives": row.get("design_direction_alternatives"),
        "design_direction_mutation_boundary": row.get("design_direction_mutation_boundary"),
        "design_direction_evidence_refs": row.get("design_direction_evidence_refs"),
        "next_action": _DIGEST_NEXT_ACTIONS[group],
    }


def build_human_decision_digest(
    queue: dict[str, Any], *, targeted_fixtures: list[str] | None = None
) -> dict[str, Any]:
    """Build a compact, read-only digest from live queue decision packets."""

    rows = queue.get("rows")
    source_rows = rows if isinstance(rows, list) else []
    targeted = {fixture for fixture in targeted_fixtures or [] if isinstance(fixture, str)}
    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in _DIGEST_GROUP_LABELS}
    for row in source_rows:
        if not isinstance(row, dict):
            continue
        group = _digest_group_key(row, targeted_fixtures=targeted)
        if group is None:
            continue
        grouped[group].append(_digest_row(row, group=group))
    groups = [
        {
            "id": group,
            "label": _DIGEST_GROUP_LABELS[group],
            "count": len(items),
            "next_action": _DIGEST_NEXT_ACTIONS[group],
            "rows": sorted(items, key=lambda item: item["fixture"]),
        }
        for group, items in grouped.items()
    ]
    packet_schemas = sorted(
        {
            schema
            for group in groups
            for item in group["rows"]
            for schema in item["packet_schemas"]
        }
    )
    return {
        "schema": HUMAN_DECISION_DIGEST_SCHEMA,
        "source": "live fig_queue rows",
        "mode": queue.get("mode"),
        "goal": queue.get("goal"),
        "total_rows": len(source_rows),
        "digest_rows": sum(group["count"] for group in groups),
        "packet_schemas": packet_schemas,
        "groups": groups,
        "safety": {
            "source_mutation": False,
            "release_state_mutation": False,
            "golden_mutation": False,
        },
    }


def print_human_decision_digest(digest: dict[str, Any]) -> None:
    print(
        "human_decision_digest "
        f"mode={_cell(digest.get('mode'))} "
        f"total={digest.get('total_rows', 0)} "
        f"digest_rows={digest.get('digest_rows', 0)}"
    )
    groups = digest.get("groups")
    if not isinstance(groups, list):
        return
    for group in groups:
        if not isinstance(group, dict) or group.get("count") == 0:
            continue
        print(f"\n{_cell(group.get('label'))} ({group.get('count')})")
        print(f"next_action: {_cell(group.get('next_action'))}")
        rows = group.get("rows")
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            recommendations = row.get("packet_recommendations")
            recommendation_text = "-"
            if isinstance(recommendations, list) and recommendations:
                recommendation_text = "; ".join(
                    _cell(item.get("recommended_choice_id") or item.get("recommendation"))
                    for item in recommendations
                    if isinstance(item, dict)
                )
            print(
                "- "
                f"{_cell(row.get('fixture'))}: "
                f"recommend={recommendation_text}; "
                f"risk={_cell(row.get('one_line_risk'))}"
            )


def _row_signal_text(row: dict[str, Any]) -> str:
    values: list[str] = []
    keys = (
        "action",
        "stop_boundary",
        "first_blocker",
        "blocking_source",
        "required_actor",
        "render_state",
        "critique_state",
        "export_state",
        "acceptance_state",
        "publication_gate_state",
        "svg_polish_gate_state",
        "svg_polish_recommended_path",
        "svg_polish_next_action",
    )
    for key in keys:
        value = row.get(key)
        if isinstance(value, str):
            values.append(value.lower())
    blockers = row.get("svg_polish_blocking_sources")
    if isinstance(blockers, list):
        values.extend(item.lower() for item in blockers if isinstance(item, str))
    return " ".join(values)


def _row_mentions(row: dict[str, Any], tokens: tuple[str, ...]) -> bool:
    text = _row_signal_text(row)
    return any(token in text for token in tokens)


def _row_fields_mention(
    row: dict[str, Any], tokens: tuple[str, ...], fields: tuple[str, ...]
) -> bool:
    values = [value.lower() for field in fields if isinstance((value := row.get(field)), str)]
    text = " ".join(values)
    return any(token in text for token in tokens)


def _bottleneck_category_for_row(row: dict[str, Any]) -> str | None:
    action = row.get("action")
    if action == fig_driver.ACTION_COMPLETE and row.get("design_direction_state") in {
        "ready_for_human_choice",
        "blocked_missing_style_pack",
        "blocked_missing_comparison",
    }:
        return "template_style"
    if action == fig_driver.ACTION_COMPLETE:
        return None
    reference_tokens = ("reference", "briefing", "context_pack")
    blocker_fields = ("first_blocker", "stop_boundary", "blocking_source")
    if action == fig_driver.ACTION_RUN_CRITIQUE:
        if _row_fields_mention(row, reference_tokens, blocker_fields):
            return "reference_context"
        return "host_critique"
    if _row_mentions(
        row,
        (
            "svg_polish",
            "polish",
            "style",
            "aesthetic",
            "palette",
            "template",
            "editorial",
            "journal_art_direction",
        ),
    ):
        return "template_style"
    if action in {
        fig_driver.ACTION_HUMAN_GATE_STOP,
        fig_driver.ACTION_RELEASE_BLOCKED,
    }:
        return "human_acceptance"
    if row.get("required_actor") in {"human", "release_operator"}:
        return "human_acceptance"
    if row.get("requires_human") is True:
        return "human_acceptance"
    if _row_fields_mention(
        row,
        ("acceptance", "accepted", "force_golden", "golden", "publication", "provenance"),
        ("action", "stop_boundary", "blocking_source", "publication_gate_state"),
    ):
        return "human_acceptance"
    if row.get("required_actor") == "host_llm":
        if _row_fields_mention(row, reference_tokens, blocker_fields):
            return "reference_context"
        return "host_critique"
    if _row_mentions(row, ("critique_required", "critique_stale", "critique_missing")):
        return "host_critique"
    if action in _MECHANICAL_ACTIONS:
        return "mechanical_tool"
    if _row_fields_mention(row, reference_tokens, ("stop_boundary", "blocking_source")):
        return "reference_context"
    return "mechanical_tool"


def _effective_bottleneck_category(row: dict[str, Any]) -> str | None:
    category = row.get("bottleneck_category")
    if isinstance(category, str) and category in BOTTLENECK_CATEGORIES:
        return category
    return _bottleneck_category_for_row(row)


def _bottleneck_category_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {category: 0 for category in BOTTLENECK_CATEGORIES}
    for row in rows:
        category = _effective_bottleneck_category(row)
        if category is not None:
            counts[category] += 1
    return counts


def _category_signals(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signal_counts: Counter[str] = Counter()
    for row in rows:
        for key in ("action", "first_blocker", "stop_boundary", "blocking_source"):
            value = row.get(key)
            if isinstance(value, str) and value:
                signal_counts[f"{key}:{value}"] += 1
    return [
        {"key": value, "count": count}
        for value, count in sorted(signal_counts.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]


def _bottleneck_category_rollup(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {category: [] for category in BOTTLENECK_CATEGORIES}
    for row in rows:
        category = _effective_bottleneck_category(row)
        if category is not None:
            grouped[category].append(row)
    return [
        {
            "category": category,
            "definition": BOTTLENECK_CATEGORY_DEFINITIONS[category],
            "count": len(category_rows),
            "example_fixtures": [
                fixture
                for fixture in (
                    row.get("fixture")
                    for row in sorted(
                        category_rows,
                        key=lambda item: str(item.get("fixture") or ""),
                    )[:5]
                )
                if isinstance(fixture, str) and fixture
            ],
            "top_signals": _category_signals(category_rows),
        }
        for category, category_rows in grouped.items()
    ]


def build_bottleneck_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize the live queue/status bottlenecks without executing work."""

    return {
        "schema": BOTTLENECK_REPORT_SCHEMA,
        "source": "fig-agent queue over live fig-agent status/driver state",
        "total_rows": len(rows),
        "errors": sum(1 for row in rows if row.get("action") == "error"),
        "dominant_action": _bottleneck_leaders(rows, "action")[:3],
        "dominant_first_blocker": _bottleneck_leaders(rows, "first_blocker")[:3],
        "dominant_required_actor": _bottleneck_leaders(rows, "required_actor")[:3],
        "dominant_blocking_source": _bottleneck_leaders(rows, "blocking_source")[:3],
        "by_bottleneck_category": _bottleneck_category_counts(rows),
        "bottleneck_categories": _bottleneck_category_rollup(rows),
        "command_plan": _command_plan_summary(rows),
    }


def build_queue(
    *,
    repo_root: Path = REPO_ROOT,
    mode: str,
    goal: str,
    fixtures: list[str] | None,
    filters: dict[str, str | None] | None = None,
    include_command_plan: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for name in _fixture_names(repo_root, fixtures):
        if not fig_driver.is_safe_fixture_name(name):
            rows.append(
                _error_row(
                    name,
                    mode=mode,
                    stop_boundary="unsafe_fixture_name",
                    error="fixture name must be a single examples/<name> directory name",
                )
            )
            continue
        example_dir = repo_root / "examples" / name
        if not example_dir.is_dir():
            rows.append(
                _error_row(
                    name,
                    mode=mode,
                    stop_boundary="fixture_not_found",
                    error=f"examples/{name}/ not found",
                )
            )
            continue
        try:
            driver_summary = fig_driver.build_driver_summary(
                name,
                mode=mode,
                goal=goal,
                repo_root=repo_root,
            )
        except (OSError, ValueError) as exc:
            rows.append(
                _error_row(
                    name,
                    mode=mode,
                    stop_boundary="driver_error",
                    error=str(exc),
                )
            )
            continue
        rows.append(_row_from_summary(driver_summary, mode=mode, repo_root=repo_root))
    active_filters = _active_filters(filters)
    filtered_rows = _filter_rows(rows, active_filters)
    queue = {
        "schema": SCHEMA,
        "mode": mode,
        "goal": goal,
        "filters": active_filters,
        "unfiltered_total": len(rows),
        "rows": filtered_rows,
        "summary": _summary(filtered_rows),
        "bottleneck_report": build_bottleneck_report(filtered_rows),
    }
    queue["human_decision_digest"] = build_human_decision_digest(
        queue,
        targeted_fixtures=fixtures,
    )
    diagnostic = _workspace_diagnostic(repo_root, fixtures)
    if diagnostic is not None:
        queue["workspace_diagnostic"] = diagnostic
    if include_command_plan:
        queue["command_plan"] = build_command_plan(filtered_rows)
    return queue


def _cell(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, list):
        if not value:
            return "-"
        return ",".join(str(item) for item in value)
    return str(value)


def _table_next_step(row: dict[str, Any]) -> str:
    reason = _blocked_reason(row)
    if row.get("action") == fig_driver.ACTION_COMPLETE:
        guidance = row.get("operator_guidance")
        if isinstance(guidance, dict):
            next_step = guidance.get("next_step")
            if isinstance(next_step, str) and next_step.strip():
                return next_step
    if reason is None:
        return "Executable workflow-agent command."
    handoff = _operator_handoff(row, reason=reason)
    next_step = handoff.get("next_step")
    if isinstance(next_step, str) and next_step:
        return next_step
    return "Inspect blocked row and rerun /fig_queue."


def _table_next_command(row: dict[str, Any]) -> str | None:
    reason = _blocked_reason(row)
    if reason is None:
        command = row.get("safe_command")
        return command if isinstance(command, str) else None
    handoff = _operator_handoff(row, reason=reason)
    command = handoff.get("command")
    return command if isinstance(command, str) and command else None


def print_table(queue: dict[str, Any]) -> None:
    rows = queue.get("rows", [])
    show_svg_columns = _has_svg_polish_columns(rows)
    show_style_columns = _has_style_direction_columns(rows)
    show_design_direction_columns = _has_design_direction_columns(rows)
    show_style_pack_columns = _has_style_benchmark_pack_columns(rows)
    show_style_comparison_columns = _has_style_benchmark_comparison_columns(rows)
    header = ["fixture", "actor", "action", "stop_boundary", "first_blocker"]
    if show_svg_columns:
        header.extend(
            [
                "svg_gate",
                "can_svg",
                "polish_path",
                "polish_next",
                "polish_blockers",
                "polish_reason",
                "svg_evidence",
            ]
        )
    if show_style_columns:
        header.extend(["style_recommendation"])
    if show_design_direction_columns:
        header.extend(["design_direction"])
    if show_style_pack_columns:
        header.extend(["style_pack"])
    if show_style_comparison_columns:
        header.extend(["style_comparison"])
    header.extend(["next_step", "next_command"])
    print("\t".join(header))
    for row in rows:
        cells = [
            _cell(row.get("fixture")),
            _cell(row.get("required_actor")),
            _cell(row.get("action")),
            _cell(row.get("stop_boundary")),
            _cell(row.get("first_blocker")),
        ]
        if show_svg_columns:
            cells.extend(
                [
                    _cell(row.get("svg_polish_gate_state")),
                    _cell(row.get("can_start_svg_polish")),
                    _cell(row.get("svg_polish_recommended_path")),
                    _cell(row.get("svg_polish_next_action")),
                    _cell(row.get("svg_polish_blocking_sources")),
                    _cell(row.get("polish_blocker_reason")),
                    _cell(row.get("svg_polish_evidence_state")),
                ]
            )
        if show_style_columns:
            packet = row.get("style_direction_packet")
            recommendation = (
                packet.get("agent_recommendation") if isinstance(packet, dict) else None
            )
            cells.append(_cell(recommendation))
        if show_design_direction_columns:
            cells.append(_cell(_design_direction_table_cell(row)))
        if show_style_pack_columns:
            cells.append(_cell(row.get("style_benchmark_pack_state")))
        if show_style_comparison_columns:
            cells.append(_cell(row.get("style_benchmark_comparison_state")))
        cells.extend(
            [
                _cell(_table_next_step(row)),
                _cell(_table_next_command(row)),
            ]
        )
        print("\t".join(cells))
    summary = queue.get("summary", {})
    print(f"summary total={summary.get('total', 0)} errors={summary.get('errors', 0)}")
    for key in _summary_table_keys():
        formatted = _format_summary_counts(summary.get(key))
        if formatted:
            print(f"summary {key}={formatted}")


def _summary_table_keys() -> tuple[str, ...]:
    return (
        "by_action",
        "by_stop_boundary",
        "by_first_blocker",
        "by_required_actor",
        "by_blocking_source",
        "by_svg_polish_gate_state",
        "by_svg_polish_recommended_path",
        "by_svg_polish_next_action",
        "by_svg_polish_blocking_source",
        "by_polish_blocker_reason",
        "by_svg_polish_evidence_state",
        "by_style_benchmark_pack_state",
        "by_style_benchmark_comparison_state",
        "by_design_direction_state",
    )


def _format_summary_counts(value: Any) -> str | None:
    if not isinstance(value, dict) or not value:
        return None
    parts: list[str] = []
    for key in sorted(value):
        count = value[key]
        if not isinstance(key, str) or not isinstance(count, int):
            continue
        parts.append(f"{key}:{count}")
    if not parts:
        return None
    return ",".join(parts)


def _has_svg_polish_columns(rows: Any) -> bool:
    if not isinstance(rows, list):
        return False
    keys = {
        "svg_polish_gate_state",
        "can_start_svg_polish",
        "svg_polish_recommended_path",
        "svg_polish_next_action",
        "svg_polish_blocking_sources",
        "svg_polish_evidence_state",
    }
    return any(isinstance(row, dict) and not keys.isdisjoint(row) for row in rows)


def _has_style_direction_columns(rows: Any) -> bool:
    if not isinstance(rows, list):
        return False
    return any(isinstance(row, dict) and "style_direction_packet" in row for row in rows)



def _has_design_direction_columns(rows: Any) -> bool:
    if not isinstance(rows, list):
        return False
    return any(isinstance(row, dict) and "design_direction_summary" in row for row in rows)


def _design_direction_table_cell(row: dict[str, Any]) -> str:
    summary = row.get("design_direction_summary")
    if not isinstance(summary, dict):
        return "-"
    state = _cell(summary.get("state"))
    recommendation = _cell(summary.get("default_recommendation"))
    boundary = _cell(summary.get("mutation_boundary"))
    evidence = summary.get("evidence_refs")
    evidence_count = len(evidence) if isinstance(evidence, list) else 0
    return (
        f"{state}; recommendation={recommendation}; "
        f"boundary={boundary}; evidence_refs={evidence_count}"
    )

def _has_style_benchmark_pack_columns(rows: Any) -> bool:
    if not isinstance(rows, list):
        return False
    return any(isinstance(row, dict) and "style_benchmark_pack_state" in row for row in rows)


def _has_style_benchmark_comparison_columns(rows: Any) -> bool:
    if not isinstance(rows, list):
        return False
    return any(
        isinstance(row, dict) and "style_benchmark_comparison_state" in row for row in rows
    )


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fig_queue.py")
    parser.add_argument("fixtures", nargs="*")
    parser.add_argument("--mode", choices=list(fig_driver.MODES), required=True)
    parser.add_argument("--goal", default="triage fixture queue")
    parser.add_argument("--actor", choices=list(_ACTORS), dest="required_actor")
    parser.add_argument("--action")
    parser.add_argument("--stop-boundary")
    parser.add_argument("--first-blocker")
    parser.add_argument("--blocking-source")
    parser.add_argument("--svg-polish-gate-state")
    parser.add_argument("--can-start-svg-polish", choices=("true", "false"))
    parser.add_argument("--svg-polish-recommended-path")
    parser.add_argument("--svg-polish-next-action")
    parser.add_argument("--svg-polish-blocking-source", dest="svg_polish_blocking_sources")
    parser.add_argument("--svg-polish-evidence-state")
    parser.add_argument("--style-benchmark-pack-state")
    parser.add_argument("--style-benchmark-comparison-state")
    parser.add_argument("--command-plan", action="store_true")
    parser.add_argument("--commands", action="store_true")
    parser.add_argument("--human-decision-digest", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("table", "json"), default="table")
    args = parser.parse_args(argv)

    resolved_repo_root = (
        runtime_paths.resolve_runtime_paths().workspace_root if repo_root is None else repo_root
    )
    queue = build_queue(
        repo_root=resolved_repo_root,
        mode=args.mode,
        goal=args.goal,
        fixtures=list(args.fixtures) or None,
        filters={
            "required_actor": args.required_actor,
            "action": args.action,
            "stop_boundary": args.stop_boundary,
            "first_blocker": args.first_blocker,
            "blocking_source": args.blocking_source,
            "svg_polish_gate_state": args.svg_polish_gate_state,
            "can_start_svg_polish": args.can_start_svg_polish,
            "svg_polish_recommended_path": args.svg_polish_recommended_path,
            "svg_polish_next_action": args.svg_polish_next_action,
            "svg_polish_blocking_sources": args.svg_polish_blocking_sources,
            "svg_polish_evidence_state": args.svg_polish_evidence_state,
            "style_benchmark_pack_state": args.style_benchmark_pack_state,
            "style_benchmark_comparison_state": args.style_benchmark_comparison_state,
        },
        include_command_plan=args.command_plan or args.commands,
    )
    _print_workspace_diagnostic(queue)
    if args.human_decision_digest:
        digest = build_human_decision_digest(queue, targeted_fixtures=list(args.fixtures) or None)
        if args.json or args.format == "json":
            print(json.dumps(digest, indent=2, sort_keys=True))
        else:
            print_human_decision_digest(digest)
    elif args.commands:
        command_plan = queue["command_plan"]
        for item in command_plan["executable"]:
            print(item["safe_command"])
    elif args.json or args.format == "json":
        print(json.dumps(queue, indent=2, sort_keys=True))
    else:
        print_table(queue)
    return workspace_diagnostic_exit_code(queue)


if __name__ == "__main__":
    sys.exit(main())
