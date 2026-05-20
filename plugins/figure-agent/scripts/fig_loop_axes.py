"""Axis verdict assembly for fig_loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fig_loop_assessments import CRITIQUE_SCHEMAS_WITH_QUALITY_AXES
from fig_loop_axis_records import (
    adjudication_evaluation_state,
    adjudication_verdict,
    axis_record,
    publication_safety_evaluation_state,
    reference_fidelity_evaluation_state,
    status_axis_evaluation,
)
from fig_loop_quality_axes import (
    STORY_QUALITY_AXES,
    quality_axis_record,
    quality_axis_summary,
)
from quality_manifest import yaml_frontmatter


def quality_axes_frontmatter(example_dir: Path, critique_state: Any) -> dict[str, Any] | None:
    if critique_state != "FRESH":
        return None
    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        return None
    frontmatter = yaml_frontmatter(critique_path)
    if frontmatter.get("schema") not in CRITIQUE_SCHEMAS_WITH_QUALITY_AXES:
        return None
    quality_axes = frontmatter.get("quality_axes")
    return quality_axes if isinstance(quality_axes, dict) else None


def axis_verdicts(
    status_result: dict[str, Any],
    adjudication: dict[str, Any],
    loop_decision: dict[str, Any],
    example_dir: Path,
) -> dict[str, dict[str, Any]]:
    stop_reason = loop_decision["stop_reason"]
    theory_path = example_dir / "theory_guard.md"
    story_path = next(
        (
            path
            for path in (
                example_dir / "authoring_plan.md",
                example_dir / "authoring_contract.md",
                example_dir / "subregion_iteration_log.md",
            )
            if path.is_file()
        ),
        None,
    )
    adjudication_path = example_dir / "critique_adjudication.yaml"
    critique_path = example_dir / "critique.md"
    critique_state = status_result.get("critique_state")
    reference_blocked = stop_reason == "reference_input_missing"
    quality_axes = quality_axes_frontmatter(example_dir, critique_state)
    story_quality = quality_axis_summary(quality_axes, STORY_QUALITY_AXES)
    reference_quality = quality_axis_summary(quality_axes, ("reference_fidelity",))
    publication_quality = quality_axis_summary(quality_axes, ("publication_readiness",))
    if reference_blocked:
        reference_record = axis_record(
            state=status_result.get("notes", []),
            verdict="blocked",
            source="status.notes",
            evaluation_state=reference_fidelity_evaluation_state(
                reference_blocked,
                critique_state,
            ),
        )
    elif reference_quality:
        reference_record = quality_axis_record(reference_quality, critique_path)
    else:
        reference_record = axis_record(
            state=status_result.get("notes", []),
            verdict="not_blocked",
            source="status.notes",
            evaluation_state=reference_fidelity_evaluation_state(
                reference_blocked,
                critique_state,
            ),
        )

    if story_quality:
        story_record = quality_axis_record(story_quality, critique_path)
    else:
        story_record = axis_record(
            state="not_evaluated" if story_path else "not_configured",
            verdict="not_evaluated",
            source=story_path.name if story_path else "not configured",
            evidence_path=story_path,
            evaluation_state="not_evaluated" if story_path else "not_configured",
        )

    if loop_decision["human_gate_status"] != "required" and publication_quality:
        publication_record = quality_axis_record(publication_quality, critique_path)
    else:
        publication_record = axis_record(
            state=status_result.get("acceptance_state"),
            verdict="human_gate"
            if loop_decision["human_gate_status"] == "required"
            else "not_cleared",
            source="status.acceptance_state",
            evidence_path=(
                example_dir / "QUALITY_AUDIT.md"
                if (example_dir / "QUALITY_AUDIT.md").is_file()
                else None
            ),
            evaluation_state=publication_safety_evaluation_state(
                status_result.get("acceptance_state"),
                loop_decision["human_gate_status"],
            ),
        )
    return {
        "render": axis_record(
            state=status_result.get("render_state"),
            verdict="fresh" if status_result.get("render_state") == "FRESH" else "not_ready",
            source="status.render_state",
            evaluation_state=(
                "passed" if status_result.get("render_state") == "FRESH" else "needs_action"
            ),
        ),
        "static_visual": axis_record(
            state="not_evaluated",
            verdict="not_evaluated",
            source="verify-only runner",
            evaluation_state="not_evaluated",
        ),
        "critique": axis_record(
            state=critique_state,
            verdict="ready" if critique_state in {"FRESH", "NOT_REQUIRED"} else "needs_action",
            source="status.critique_state",
            evidence_path=critique_path if critique_path.is_file() else None,
            evaluation_state=status_axis_evaluation(
                critique_state,
                passed_values={"FRESH"},
                not_configured_values={"NOT_REQUIRED"},
                blocked_values={"REFERENCE_MISSING"},
            ),
        ),
        "adjudication": axis_record(
            state=adjudication["state"],
            verdict=adjudication_verdict(adjudication, stop_reason),
            source="critique_adjudication.yaml",
            evidence_path=adjudication_path if adjudication_path.is_file() else None,
            evaluation_state=adjudication_evaluation_state(
                adjudication,
                stop_reason,
                critique_state,
            ),
        ),
        "theory": axis_record(
            state="not_evaluated" if theory_path.is_file() else "not_configured",
            verdict="human_review_not_requested",
            source="theory_guard.md" if theory_path.is_file() else "not configured",
            evidence_path=theory_path if theory_path.is_file() else None,
            evaluation_state="not_evaluated" if theory_path.is_file() else "not_configured",
        ),
        "reference_fidelity": reference_record,
        "story_hierarchy": story_record,
        "export": axis_record(
            state=status_result.get("export_state"),
            verdict="fresh" if status_result.get("export_state") == "FRESH" else "not_ready",
            source="status.export_state",
            evaluation_state=(
                "passed" if status_result.get("export_state") == "FRESH" else "needs_action"
            ),
        ),
        "publication_safety": publication_record,
    }
