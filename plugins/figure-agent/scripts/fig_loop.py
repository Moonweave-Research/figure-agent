"""Verify-only figure loop runner.

Records one read-only loop iteration under `.scratch/fig-loop-runs/` without
editing figure source, compile/export state, or acceptance artifacts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from critique_adjudication import (  # noqa: E402
    CritiqueAdjudicationError,
    adjudication_is_stale,
    load_adjudication,
)
from quality_manifest import file_sha256, yaml_frontmatter  # noqa: E402
from status import infer_stage  # noqa: E402
from subregion_active_set import active_subregion_ids, parse_active_target_rows  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_ROOT = REPO_ROOT / ".scratch" / "fig-loop-runs"
MODE = "verify-only"
CRITIQUE_SCHEMA_V1_2 = "figure-agent.critique.v1.2"
JOURNAL_ASSESSMENT_SCHEMA = "figure-agent.journal-grade-assessment.v1"
_JOURNAL_SCORE_KEYS = frozenset(
    {
        "storyline",
        "composition",
        "component_fidelity",
        "scientific_plausibility",
        "label_semantics",
        "polish",
        "reference_fidelity",
        "export_scale_readability",
    }
)
_STORY_QUALITY_AXES = (
    "message_storyline",
    "panel_role_coherence",
    "composition_layout",
)
_QUALITY_VERDICT_RANK = {
    "not_applicable": -1,
    "pass": 0,
    "needs_patch": 1,
    "needs_human": 2,
    "block": 3,
}
_QUALITY_EVALUATION_STATE = {
    "not_applicable": "not_configured",
    "pass": "passed",
    "needs_patch": "needs_action",
    "needs_human": "blocked",
    "block": "blocked",
}
_GIT_MUTATIONS = frozenset(
    {"add", "commit", "reset", "checkout", "clean", "push", "merge", "rebase"}
)


class FigLoopError(ValueError):
    """Expected user-facing error for fig loop preflight failures."""


def ensure_safe_command(command: tuple[str, ...]) -> tuple[str, ...]:
    """Reject commands that would mutate git state."""
    if command and command[0] == "git" and any(part in _GIT_MUTATIONS for part in command[1:]):
        joined = " ".join(command)
        raise FigLoopError(f"git mutation command is not allowed in verify-only loop: {joined}")
    return command


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_value(repo_root: Path, args: tuple[str, ...]) -> str | None:
    command = ensure_safe_command(("git", *args))
    result = subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _run_id(name: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    safe_name = "".join(char if char.isalnum() or char in "._-" else "_" for char in name)
    return f"{timestamp}-{safe_name}"


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _adjudication_state(example_dir: Path) -> dict[str, Any]:
    critique_path = example_dir / "critique.md"
    adjudication_path = example_dir / "critique_adjudication.yaml"
    if not adjudication_path.is_file():
        return {"state": "missing", "path": str(adjudication_path), "decision_count": 0}
    try:
        adjudication = load_adjudication(adjudication_path)
        stale = adjudication_is_stale(adjudication_path, critique_path)
    except CritiqueAdjudicationError as exc:
        return {
            "state": "invalid",
            "path": str(adjudication_path),
            "decision_count": 0,
            "error": str(exc),
        }
    return {
        "state": "stale" if stale else "fresh",
        "path": str(adjudication_path),
        "decision_count": len(adjudication.get("decisions", [])),
        "decisions": adjudication.get("decisions", []),
        "source_critique_hash": adjudication["source_critique_hash"],
    }


def _reference_input_missing(status_result: dict[str, Any]) -> bool:
    reference_notes = {
        "critique_reference_missing",
        "reference_image_missing",
        "panel_reference_image_missing",
    }
    return bool(reference_notes.intersection(status_result.get("notes", [])))


def _critique_refresh_action(example_dir: Path, critique_state: Any) -> str:
    state_text = str(critique_state).lower()
    return f"run /fig_critique {example_dir.name} because critique is {state_text}."


def _active_subregion_target(example_dir: Path) -> dict[str, str | None] | None:
    log_path = example_dir / "subregion_iteration_log.md"
    if not log_path.is_file():
        return None
    rows = parse_active_target_rows(log_path.read_text(encoding="utf-8"))
    active_ids = active_subregion_ids(rows)
    if not active_ids:
        return None
    return {
        "finding_id": None,
        "patch_target": active_ids[0],
        "reason": "active sub-region target",
    }


def _first_decision(adjudication: dict[str, Any], decision: str) -> dict[str, Any] | None:
    if adjudication["state"] != "fresh":
        return None
    for item in adjudication.get("decisions", []):
        if item.get("decision") == decision:
            return item
    return None


def _decisions_with_value(adjudication: dict[str, Any], decision: str) -> list[dict[str, Any]]:
    if adjudication["state"] != "fresh":
        return []
    return [item for item in adjudication.get("decisions", []) if item.get("decision") == decision]


def _loop_decision(
    status_result: dict[str, Any],
    adjudication: dict[str, Any],
    example_dir: Path,
) -> dict[str, Any]:
    if _reference_input_missing(status_result):
        return {
            "stop_reason": "reference_input_missing",
            "recommended_next_action": "fix declared reference inputs before continuing",
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }
    if status_result.get("critique_state") in {"MISSING", "STALE"}:
        return {
            "stop_reason": "status_action_required",
            "recommended_next_action": _critique_refresh_action(
                example_dir,
                status_result.get("critique_state"),
            ),
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }
    if adjudication["state"] == "stale":
        return {
            "stop_reason": "stale_adjudication",
            "recommended_next_action": "review or refresh critique_adjudication.yaml",
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }
    if adjudication["state"] == "invalid":
        return {
            "stop_reason": "invalid_adjudication",
            "recommended_next_action": "fix critique_adjudication.yaml",
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    human_decision = _first_decision(adjudication, "needs_human")
    if human_decision:
        finding_id = human_decision["finding_id"]
        return {
            "stop_reason": "human_gate_required",
            "recommended_next_action": f"human review required for {finding_id}",
            "active_patch_target": None,
            "human_gate_status": "required",
        }

    apply_decisions = _decisions_with_value(adjudication, "apply")
    if len(apply_decisions) > 1:
        return {
            "stop_reason": "ambiguous_patch_selection",
            "recommended_next_action": (
                "select exactly one apply decision in critique_adjudication.yaml"
            ),
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }
    if len(apply_decisions) == 1:
        apply_decision = apply_decisions[0]
        finding_id = apply_decision["finding_id"]
        patch_target = apply_decision["patch_target"]
        return {
            "stop_reason": "patch_target_recommended",
            "recommended_next_action": f"patch {finding_id}: {patch_target}",
            "active_patch_target": {
                "finding_id": finding_id,
                "patch_target": patch_target,
                "reason": apply_decision["reason"],
            },
            "human_gate_status": "not_requested",
        }

    if adjudication["state"] == "missing" and (status_result.get("critique_state") == "FRESH"):
        return {
            "stop_reason": "missing_adjudication",
            "recommended_next_action": "create critique_adjudication.yaml",
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    active_subregion = _active_subregion_target(example_dir)
    if active_subregion:
        return {
            "stop_reason": "active_subregion_recommended",
            "recommended_next_action": (
                f"patch active sub-region: {active_subregion['patch_target']}"
            ),
            "active_patch_target": active_subregion,
            "human_gate_status": "not_requested",
        }

    if (
        status_result.get("workflow_ready")
        and status_result.get("acceptance_state") == "NOT_ACCEPTED"
    ):
        return {
            "stop_reason": "status_action_required",
            "recommended_next_action": status_result.get("next", "inspect figure state"),
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    # Issue 7E: polished-SVG final-artifact states (MISSING / INVALID / STALE /
    # BLOCKED) reach this branch via workflow_ready=true + final_ready=false.
    # status.py owns the canonical per-state next-action prose (see
    # _NEXT_FINAL_ARTIFACT_*), so the loop forwards it through status.next
    # rather than duplicating the recommendation text here. BLOCKED routes to
    # semantic backport because status.py emits _NEXT_FINAL_ARTIFACT_BLOCKED
    # for that state.
    if status_result.get("workflow_ready") and not status_result.get("final_ready", True):
        return {
            "stop_reason": "status_action_required",
            "recommended_next_action": status_result.get("next", "inspect figure state"),
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    if not status_result.get("workflow_ready"):
        return {
            "stop_reason": "status_action_required",
            "recommended_next_action": status_result.get("next", "inspect figure state"),
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    if adjudication["state"] == "fresh" and adjudication.get("decisions"):
        return {
            "stop_reason": "no_actionable_findings",
            "recommended_next_action": "no actionable adjudicated findings remain",
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    return {
        "stop_reason": "verify_only_complete",
        "recommended_next_action": status_result.get("next", "inspect figure state"),
        "active_patch_target": None,
        "human_gate_status": "not_requested",
    }


def _quality_axes_frontmatter(example_dir: Path, critique_state: Any) -> dict[str, Any] | None:
    if critique_state != "FRESH":
        return None
    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        return None
    frontmatter = yaml_frontmatter(critique_path)
    if frontmatter.get("schema") != CRITIQUE_SCHEMA_V1_2:
        return None
    quality_axes = frontmatter.get("quality_axes")
    return quality_axes if isinstance(quality_axes, dict) else None


def _quality_axis(quality_axes: dict[str, Any], axis_name: str) -> dict[str, Any] | None:
    axis = quality_axes.get(axis_name)
    if not isinstance(axis, dict):
        return None
    verdict = axis.get("verdict")
    if not isinstance(verdict, str) or verdict not in _QUALITY_VERDICT_RANK:
        return None
    recommended_action = axis.get("recommended_action")
    blocking_items = axis.get("blocking_items")
    return {
        "name": axis_name,
        "verdict": verdict,
        "recommended_action": recommended_action if isinstance(recommended_action, str) else None,
        "blocking_items": blocking_items if isinstance(blocking_items, list) else [],
    }


def _quality_axis_summary(
    quality_axes: dict[str, Any] | None,
    axis_names: tuple[str, ...],
) -> dict[str, Any] | None:
    if not quality_axes:
        return None
    axes = [
        axis
        for axis_name in axis_names
        if (axis := _quality_axis(quality_axes, axis_name)) is not None
    ]
    if not axes:
        return None
    applicable_axes = [axis for axis in axes if axis["verdict"] != "not_applicable"]
    ranked_axes = applicable_axes or axes
    selected = max(ranked_axes, key=lambda axis: _QUALITY_VERDICT_RANK[axis["verdict"]])
    blocking_items: dict[str, list[str]] = {}
    for axis in axes:
        items = [item for item in axis["blocking_items"] if isinstance(item, str) and item.strip()]
        if items:
            blocking_items[axis["name"]] = items
    return {
        "verdict": selected["verdict"],
        "axis_names": [axis["name"] for axis in axes],
        "axis_verdicts": {axis["name"]: axis["verdict"] for axis in axes},
        "recommended_actions": {
            axis["name"]: axis["recommended_action"]
            for axis in axes
            if axis["recommended_action"] is not None
        },
        "blocking_items": blocking_items,
    }


def _quality_axis_record(summary: dict[str, Any], critique_path: Path) -> dict[str, Any]:
    verdict = summary["verdict"]
    return _axis_record(
        state=verdict,
        verdict=verdict,
        source="critique.quality_axes",
        evidence_path=critique_path,
        evaluation_state=_QUALITY_EVALUATION_STATE[verdict],
        quality_axes=summary["axis_names"],
        quality_axis_verdicts=summary["axis_verdicts"],
        quality_axis_recommended_actions=summary["recommended_actions"],
        quality_axis_blocking_items=summary["blocking_items"],
    )


def _is_score_value(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and 0 <= value <= 100
    )


def _has_complete_score_block(record: dict[str, Any]) -> bool:
    if not {"overall_score", "sub_scores", "score_rationale"} <= record.keys():
        return False
    if not _is_score_value(record.get("overall_score")):
        return False
    if (
        not isinstance(record.get("score_rationale"), str)
        or not record["score_rationale"].strip()
    ):
        return False
    sub_scores = record.get("sub_scores")
    return (
        isinstance(sub_scores, dict)
        and set(sub_scores) == _JOURNAL_SCORE_KEYS
        and all(_is_score_value(value) for value in sub_scores.values())
    )


def _journal_grade_assessment(
    example_dir: Path,
    critique_state: Any,
) -> dict[str, Any] | None:
    if critique_state != "FRESH":
        return None
    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        return None
    frontmatter = yaml_frontmatter(critique_path)
    if frontmatter.get("schema") != CRITIQUE_SCHEMA_V1_2:
        return None
    assessment = frontmatter.get("journal_grade_assessment")
    if not isinstance(assessment, dict):
        return None
    record = dict(assessment)
    gateable = (
        record.get("schema") == JOURNAL_ASSESSMENT_SCHEMA
        and record.get("scoring_mode") == "fresh_reaudit"
        and isinstance(record.get("assessed_artifact_hash"), str)
        and record.get("assessed_artifact_hash") == frontmatter.get("critique_input_hash")
        and record.get("score_is_gateable") is True
    )
    record["score_is_gateable"] = gateable
    if not gateable:
        record["evaluation_state"] = "stale"
    elif record.get("benchmark_level") in {"blocked", "needs_human_art_direction"}:
        record["evaluation_state"] = "blocked"
    else:
        record["evaluation_state"] = "passed"
    record["source"] = "critique.journal_grade_assessment"
    record["evidence_path"] = str(critique_path)
    if gateable and _has_complete_score_block(record):
        record["score_policy"] = "advisory_fresh_reaudit_not_gate"
    return record


def _axis_verdicts(
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
    quality_axes = _quality_axes_frontmatter(example_dir, critique_state)
    story_quality = _quality_axis_summary(quality_axes, _STORY_QUALITY_AXES)
    reference_quality = _quality_axis_summary(quality_axes, ("reference_fidelity",))
    publication_quality = _quality_axis_summary(quality_axes, ("publication_readiness",))
    if reference_blocked:
        reference_record = _axis_record(
            state=status_result.get("notes", []),
            verdict="blocked",
            source="status.notes",
            evaluation_state=_reference_fidelity_evaluation_state(
                reference_blocked,
                critique_state,
            ),
        )
    elif reference_quality:
        reference_record = _quality_axis_record(reference_quality, critique_path)
    else:
        reference_record = _axis_record(
            state=status_result.get("notes", []),
            verdict="not_blocked",
            source="status.notes",
            evaluation_state=_reference_fidelity_evaluation_state(
                reference_blocked,
                critique_state,
            ),
        )

    if story_quality:
        story_record = _quality_axis_record(story_quality, critique_path)
    else:
        story_record = _axis_record(
            state="not_evaluated" if story_path else "not_configured",
            verdict="not_evaluated",
            source=story_path.name if story_path else "not configured",
            evidence_path=story_path,
            evaluation_state="not_evaluated" if story_path else "not_configured",
        )

    if loop_decision["human_gate_status"] != "required" and publication_quality:
        publication_record = _quality_axis_record(publication_quality, critique_path)
    else:
        publication_record = _axis_record(
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
            evaluation_state=_publication_safety_evaluation_state(
                status_result.get("acceptance_state"),
                loop_decision["human_gate_status"],
            ),
        )
    return {
        "render": _axis_record(
            state=status_result.get("render_state"),
            verdict="fresh" if status_result.get("render_state") == "FRESH" else "not_ready",
            source="status.render_state",
            evaluation_state=(
                "passed" if status_result.get("render_state") == "FRESH" else "needs_action"
            ),
        ),
        "static_visual": _axis_record(
            state="not_evaluated",
            verdict="not_evaluated",
            source="verify-only runner",
            evaluation_state="not_evaluated",
        ),
        "critique": _axis_record(
            state=critique_state,
            verdict="ready" if critique_state in {"FRESH", "NOT_REQUIRED"} else "needs_action",
            source="status.critique_state",
            evidence_path=critique_path if critique_path.is_file() else None,
            evaluation_state=_status_axis_evaluation(
                critique_state,
                passed_values={"FRESH"},
                not_configured_values={"NOT_REQUIRED"},
                blocked_values={"REFERENCE_MISSING"},
            ),
        ),
        "adjudication": _axis_record(
            state=adjudication["state"],
            verdict=_adjudication_verdict(adjudication, stop_reason),
            source="critique_adjudication.yaml",
            evidence_path=adjudication_path if adjudication_path.is_file() else None,
            evaluation_state=_adjudication_evaluation_state(
                adjudication,
                stop_reason,
                critique_state,
            ),
        ),
        "theory": _axis_record(
            state="not_evaluated" if theory_path.is_file() else "not_configured",
            verdict="human_review_not_requested",
            source="theory_guard.md" if theory_path.is_file() else "not configured",
            evidence_path=theory_path if theory_path.is_file() else None,
            evaluation_state="not_evaluated" if theory_path.is_file() else "not_configured",
        ),
        "reference_fidelity": reference_record,
        "story_hierarchy": story_record,
        "export": _axis_record(
            state=status_result.get("export_state"),
            verdict="fresh" if status_result.get("export_state") == "FRESH" else "not_ready",
            source="status.export_state",
            evaluation_state=(
                "passed" if status_result.get("export_state") == "FRESH" else "needs_action"
            ),
        ),
        "publication_safety": publication_record,
    }


def _axis_record(
    *,
    state: Any,
    verdict: str,
    source: str,
    evaluation_state: str,
    evidence_path: Path | None = None,
    **metadata: Any,
) -> dict[str, Any]:
    record = {
        "state": state,
        "verdict": verdict,
        "source": source,
        "evidence_path": str(evidence_path) if evidence_path else None,
        "evaluation_state": evaluation_state,
    }
    record.update(metadata)
    return record


def _status_axis_evaluation(
    state: Any,
    *,
    passed_values: set[str],
    not_configured_values: set[str] | None = None,
    blocked_values: set[str] | None = None,
) -> str:
    if state in passed_values:
        return "passed"
    if not_configured_values and state in not_configured_values:
        return "not_configured"
    if blocked_values and state in blocked_values:
        return "blocked"
    return "needs_action"


def _adjudication_evaluation_state(
    adjudication: dict[str, Any],
    stop_reason: str,
    critique_state: Any,
) -> str:
    if stop_reason in {"patch_target_recommended", "human_gate_required"}:
        return "needs_action"
    if adjudication["state"] == "missing" and critique_state != "FRESH":
        return "not_configured"
    if adjudication["state"] == "fresh":
        return "passed"
    if adjudication["state"] in {"stale", "invalid", "missing"}:
        return "needs_action"
    return "not_evaluated"


def _reference_fidelity_evaluation_state(reference_blocked: bool, critique_state: Any) -> str:
    if reference_blocked:
        return "blocked"
    if critique_state == "NOT_REQUIRED":
        return "not_configured"
    return "not_evaluated"


def _publication_safety_evaluation_state(
    acceptance_state: Any,
    human_gate_status: str,
) -> str:
    if human_gate_status == "required":
        return "blocked"
    if acceptance_state == "ACCEPTED":
        return "passed"
    if acceptance_state == "NOT_DECLARED":
        return "not_configured"
    return "needs_action"


def _adjudication_verdict(adjudication: dict[str, Any], stop_reason: str) -> str:
    if stop_reason == "patch_target_recommended":
        return "actionable"
    if stop_reason == "human_gate_required":
        return "human_gate"
    if adjudication["state"] in {"stale", "invalid", "missing"}:
        return adjudication["state"]
    if stop_reason == "no_actionable_findings" or (
        adjudication["state"] == "fresh" and adjudication.get("decisions")
    ):
        return "complete"
    return "not_actionable"


def _escalation_summary(loop_decision: dict[str, Any]) -> dict[str, Any]:
    stop_reason = loop_decision["stop_reason"]
    recommended = loop_decision.get("recommended_next_action", "")
    if stop_reason == "human_gate_required":
        level = "human_review_required"
    elif stop_reason in {"patch_target_recommended", "active_subregion_recommended"}:
        level = "patch_allowed"
    elif stop_reason == "ambiguous_patch_selection":
        level = "ambiguous_patch_selection"
    elif stop_reason == "status_action_required" and "--force-golden" in recommended:
        level = "manual_approval_required"
    elif stop_reason == "status_action_required" and "accepted: true" in recommended:
        level = "manual_approval_required"
    elif stop_reason in {
        "status_action_required",
        "missing_adjudication",
        "stale_adjudication",
        "invalid_adjudication",
        "reference_input_missing",
    }:
        level = "agent_action_required"
    elif stop_reason == "no_actionable_findings":
        level = "none"
    else:
        level = "none"

    return {
        "escalation_level": level,
        "requires_user_input": level in {"manual_approval_required", "human_review_required"},
        "requires_domain_review": level == "human_review_required",
    }


_AUTO_PATCH_ALLOWED_TERMS = {
    "label offset": ("label offset", "offset label", "move the label", "move label"),
    "text overlap": ("overlap", "crowding", "crowded", "collision"),
    "clipping": ("clip",),
    "whitespace balance": ("whitespace",),
    "palette/style": ("palette violation", "style violation"),
    "line weight/style": ("line weight", "stroke weight"),
}

_AUTO_PATCH_BLOCKED_TERMS = {
    "chemistry topology": ("chemistry", "topology", "molecule", "bond"),
    "physical mechanism": ("mechanism", "causal", "physics"),
    "causal arrow semantics": ("arrow semantics", "causal arrow"),
    "theory guard evidence": ("theory", "guard"),
    "reference interpretation": ("reference", "interpretation"),
    "accepted/golden/export/build state": ("accepted", "golden", "export", "build"),
    "publication safety": ("publication", "safety"),
    "critique mutation": ("critique.md", "critique mutation"),
    "broad refactor": ("refactor", "rewrite"),
}

_AUTO_PATCH_REQUIRED_EVIDENCE = [
    "before compile/export evidence",
    "after compile/export evidence",
    "rollback path",
]
_PATCH_EVIDENCE_SCHEMA = "figure-agent.patch-evidence.v1"
_POST_PATCH_EVIDENCE_SCHEMA = "figure-agent.post-patch-evidence.v1"
_PATCH_EVIDENCE_VERDICTS = ["resolved", "unresolved", "regressed", "ambiguous"]


def _auto_patch_eligibility(
    loop_decision: dict[str, Any],
    patch_handoff: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not patch_handoff:
        return None

    haystack = " ".join(
        str(value)
        for value in (
            patch_handoff.get("target_id"),
            patch_handoff.get("patch_target"),
            patch_handoff.get("reason"),
            loop_decision.get("recommended_next_action"),
        )
        if value
    ).lower()
    allowed = [
        name
        for name, terms in _AUTO_PATCH_ALLOWED_TERMS.items()
        if any(term in haystack for term in terms)
    ]
    blocked = [
        name
        for name, terms in _AUTO_PATCH_BLOCKED_TERMS.items()
        if any(term in haystack for term in terms)
    ]

    if blocked:
        level = "human_review_required"
    elif allowed:
        level = "auto_patch_candidate"
    else:
        level = "patch_assisted_only"

    return {
        "level": level,
        "target_type": patch_handoff["target_type"],
        "target_id": patch_handoff["target_id"],
        "allowed_reasons": allowed,
        "blocked_reasons": blocked,
        "required_evidence": list(_AUTO_PATCH_REQUIRED_EVIDENCE),
        "may_edit": False,
    }


def _path_evidence(repo_root: Path, rel_path: str) -> dict[str, Any]:
    path = repo_root / rel_path
    exists = path.is_file()
    return {
        "path": rel_path,
        "exists": exists,
        "sha256": file_sha256(path) if exists else None,
    }


def _patch_evidence_baseline(
    repo_root: Path,
    patch_handoff: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not patch_handoff:
        return None
    return {
        "schema": _PATCH_EVIDENCE_SCHEMA,
        "phase": "pre_patch",
        "target_type": patch_handoff["target_type"],
        "target_id": patch_handoff["target_id"],
        "verdict": "not_evaluated",
        "may_edit": False,
        "pre_patch": {
            "allowed_edit_scope": [
                _path_evidence(repo_root, rel_path)
                for rel_path in patch_handoff["allowed_edit_scope"]
            ]
        },
        "post_patch_required_verdicts": list(_PATCH_EVIDENCE_VERDICTS),
        "rollback_reference": {
            "git_commit": _git_value(repo_root, ("rev-parse", "HEAD")),
            "restore_strategy": (
                "restore allowed_edit_scope paths to the recorded pre_patch sha256 values"
            ),
        },
    }


def _valid_previous_iteration(iteration_path: Path, name: str) -> bool:
    manifest_path = iteration_path.parent / "run_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        iteration = json.loads(iteration_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(manifest, dict)
        and manifest.get("schema") == "figure-agent.fig-loop-run.v1"
        and manifest.get("fixture") == name
        and isinstance(iteration, dict)
        and isinstance(iteration.get("patch_evidence"), dict)
        and iteration["patch_evidence"].get("phase") == "pre_patch"
    )


def _latest_patch_evidence_baseline(
    runs_root: Path,
    name: str,
) -> tuple[Path, dict[str, Any]] | None:
    candidates = [
        path
        for path in runs_root.glob(f"*-{name}/iteration_001.json")
        if _valid_previous_iteration(path, name)
    ]
    if not candidates:
        return None
    iteration_path = max(candidates, key=lambda path: path.stat().st_mtime)
    iteration = json.loads(iteration_path.read_text(encoding="utf-8"))
    return iteration_path, iteration["patch_evidence"]


def _decision_for_target(adjudication: dict[str, Any], target_id: str) -> str | None:
    if adjudication["state"] != "fresh":
        return None
    for decision in adjudication.get("decisions", []):
        if decision.get("finding_id") == target_id:
            return decision.get("decision")
    return None


def _post_patch_evidence_verdict(
    repo_root: Path,
    runs_root: Path,
    name: str,
    adjudication: dict[str, Any],
    status_result: dict[str, Any],
) -> dict[str, Any] | None:
    baseline = _latest_patch_evidence_baseline(runs_root, name)
    if baseline is None:
        return None
    baseline_path, patch_evidence = baseline
    changed_paths = []
    for item in patch_evidence.get("pre_patch", {}).get("allowed_edit_scope", []):
        rel_path = item.get("path")
        if not isinstance(rel_path, str):
            continue
        current = _path_evidence(repo_root, rel_path)
        if current["exists"] != item.get("exists") or current["sha256"] != item.get("sha256"):
            changed_paths.append(rel_path)

    target_id = str(patch_evidence.get("target_id", ""))
    current_decision = _decision_for_target(adjudication, target_id)
    allowed_changed = bool(changed_paths)
    if status_result.get("render_state") not in {"FRESH", "MISSING"}:
        verdict = "regressed"
    elif current_decision == "resolved" and allowed_changed:
        verdict = "resolved"
    elif current_decision in {"apply", "defer"} or not allowed_changed:
        verdict = "unresolved"
    else:
        verdict = "ambiguous"

    return {
        "schema": _POST_PATCH_EVIDENCE_SCHEMA,
        "baseline_path": str(baseline_path),
        "target_type": patch_evidence.get("target_type"),
        "target_id": target_id,
        "verdict": verdict,
        "allowed_edit_scope_changed": allowed_changed,
        "changed_allowed_paths": changed_paths,
        "current_decision": current_decision,
        "may_edit": False,
    }


def _patch_handoff(name: str, loop_decision: dict[str, Any]) -> dict[str, Any] | None:
    active_patch_target = loop_decision["active_patch_target"]
    if not active_patch_target:
        return None

    finding_id = active_patch_target.get("finding_id")
    patch_target = active_patch_target["patch_target"]
    target_type = "finding" if finding_id else "subregion"
    target_id = finding_id if finding_id else patch_target
    example_prefix = f"examples/{name}"
    return {
        "target_type": target_type,
        "target_id": target_id,
        "patch_target": patch_target,
        "reason": active_patch_target["reason"],
        "allowed_edit_scope": [
            f"{example_prefix}/{name}.tex",
            f"{example_prefix}/authoring_plan.md",
            f"{example_prefix}/subregion_iteration_log.md",
        ],
        "forbidden_edit_scope": [
            "accepted",
            "golden_contract",
            f"{example_prefix}/exports/",
            f"{example_prefix}/build/",
            f"{example_prefix}/critique.md",
            "unrelated examples",
            "broad refactors",
            "multiple findings in one patch",
        ],
        "required_closeout_checks": [
            f"/fig_compile {name}",
            f"/fig_critique {name} when critique freshness requires it",
            f"update or recreate {example_prefix}/critique_adjudication.yaml",
            "preserve unresolved findings",
            f"/fig_loop {name} --goal <same goal or next goal>",
        ],
        "unresolved_findings_requirement": (
            "Do not delete, rewrite, or hide unresolved critique findings; record only the"
            " selected target decision in critique_adjudication.yaml."
        ),
    }


def _decision_markdown(
    *,
    name: str,
    goal: str,
    status_result: dict[str, Any],
    adjudication: dict[str, Any],
    loop_decision: dict[str, Any],
    escalation: dict[str, Any],
    patch_handoff: dict[str, Any] | None,
) -> str:
    notes = status_result.get("notes", [])
    notes_text = ", ".join(notes) if notes else "(none)"
    active_patch_target = loop_decision["active_patch_target"]
    if active_patch_target:
        finding_id = active_patch_target["finding_id"]
        patch_target = active_patch_target["patch_target"]
        active_patch_text = f"{finding_id} -> {patch_target}" if finding_id else str(patch_target)
    else:
        active_patch_text = "(none)"
    if patch_handoff:
        handoff_text = f"{patch_handoff['target_type']} {patch_handoff['target_id']}"
    else:
        handoff_text = "(none)"
    return "\n".join(
        [
            f"# Fig Loop Decision: {name}",
            "",
            f"- mode: {MODE}",
            f"- goal: {goal}",
            f"- stop_reason: {loop_decision['stop_reason']}",
            f"- escalation_level: {escalation['escalation_level']}",
            f"- stage: {status_result.get('stage')}/4",
            f"- render_state: {status_result.get('render_state')}",
            f"- critique_state: {status_result.get('critique_state')}",
            f"- export_state: {status_result.get('export_state')}",
            (
                "- final_artifact_state: "
                f"{status_result.get('final_artifact_kind', 'generated_export')} "
                f"{status_result.get('final_artifact_state', 'NONE')} "
                f"{status_result.get('final_artifact_path', '')}"
            ),
            f"- adjudication_state: {adjudication['state']}",
            f"- active_patch_target: {active_patch_text}",
            f"- patch_handoff_target: {handoff_text}",
            f"- notes: {notes_text}",
            f"- recommended_next_action: {loop_decision['recommended_next_action']}",
            "",
            "Verify-only mode records loop evidence only. It does not patch source, "
            "compile outputs, export artifacts, or acceptance state.",
            "",
        ]
    )


def run_loop(
    name: str,
    goal: str,
    *,
    repo_root: Path = REPO_ROOT,
    runs_root: Path | None = None,
) -> Path:
    """Run one verify-only loop iteration and return the run directory."""
    repo_root = repo_root.resolve()
    runs_root = (runs_root or repo_root / ".scratch" / "fig-loop-runs").resolve()
    example_dir = repo_root / "examples" / name
    if not example_dir.is_dir():
        raise FigLoopError(f"examples/{name}/ not found")

    started_at = _utc_now()
    run_dir = runs_root / _run_id(name)
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "command_logs").mkdir()

    status_result = infer_stage(example_dir)
    adjudication = _adjudication_state(example_dir)
    loop_decision = _loop_decision(status_result, adjudication, example_dir)
    axis_verdicts = _axis_verdicts(status_result, adjudication, loop_decision, example_dir)
    escalation = _escalation_summary(loop_decision)
    patch_handoff = _patch_handoff(name, loop_decision)
    journal_grade_assessment = _journal_grade_assessment(
        example_dir,
        status_result.get("critique_state"),
    )
    auto_patch_eligibility = _auto_patch_eligibility(loop_decision, patch_handoff)
    post_patch_evidence = _post_patch_evidence_verdict(
        repo_root,
        runs_root,
        name,
        adjudication,
        status_result,
    )
    patch_evidence = (
        None
        if post_patch_evidence is not None
        else _patch_evidence_baseline(repo_root, patch_handoff)
    )
    completed_at = _utc_now()

    iteration = {
        "iteration": 1,
        "status": status_result,
        "axis_verdicts": axis_verdicts,
        "adjudication": adjudication,
        "stop_reason": loop_decision["stop_reason"],
        "active_patch_target": loop_decision["active_patch_target"],
        "patch_handoff": patch_handoff,
        "journal_grade_assessment": journal_grade_assessment,
        "auto_patch_eligibility": auto_patch_eligibility,
        "patch_evidence": patch_evidence,
        "post_patch_evidence": post_patch_evidence,
        "recommended_next_action": loop_decision["recommended_next_action"],
        "human_gate_status": loop_decision["human_gate_status"],
        **escalation,
    }
    manifest = {
        "schema": "figure-agent.fig-loop-run.v1",
        "fixture": name,
        "mode": MODE,
        "goal": goal,
        "run_dir": str(run_dir),
        "started_at": started_at,
        "completed_at": completed_at,
        "final_stop_reason": loop_decision["stop_reason"],
        "branch": _git_value(repo_root, ("rev-parse", "--abbrev-ref", "HEAD")),
        "commit": _git_value(repo_root, ("rev-parse", "HEAD")),
        "iterations": ["iteration_001.json"],
        "command_results": [],
    }

    _write_json(run_dir / "iteration_001.json", iteration)
    _write_json(run_dir / "run_manifest.json", manifest)
    (run_dir / "decision.md").write_text(
        _decision_markdown(
            name=name,
            goal=goal,
            status_result=status_result,
            adjudication=adjudication,
            loop_decision=loop_decision,
            escalation=escalation,
            patch_handoff=patch_handoff,
        ),
        encoding="utf-8",
    )
    return run_dir


def _json_stdout_summary(run_dir: Path) -> dict[str, Any]:
    manifest_path = run_dir / "run_manifest.json"
    iteration_path = run_dir / "iteration_001.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    iteration = json.loads(iteration_path.read_text(encoding="utf-8"))
    return {
        "run_dir": manifest["run_dir"],
        "manifest_path": str(manifest_path),
        "iteration_path": str(iteration_path),
        "final_stop_reason": manifest["final_stop_reason"],
        "escalation_level": iteration["escalation_level"],
        "patch_handoff_present": iteration.get("patch_handoff") is not None,
        "auto_patch_eligibility": iteration.get("auto_patch_eligibility"),
        "patch_evidence_present": iteration.get("patch_evidence") is not None,
        "post_patch_evidence_verdict": (
            (iteration.get("post_patch_evidence") or {}).get("verdict")
        ),
        "final_artifact_state": (iteration.get("status") or {}).get("final_artifact_state"),
        "final_artifact_kind": (iteration.get("status") or {}).get("final_artifact_kind"),
        "final_artifact_path": (iteration.get("status") or {}).get("final_artifact_path"),
        "recommended_next_action": iteration.get("recommended_next_action"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="fixture name under examples/")
    parser.add_argument("--goal", required=True, help="natural-language loop goal")
    parser.add_argument("--runs-root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        run_dir = run_loop(args.name, args.goal, runs_root=args.runs_root)
    except FigLoopError as exc:
        print(f"fig_loop.py: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(_json_stdout_summary(run_dir), sort_keys=True))
        return 0
    print(f"fig_loop.py: wrote verify-only run to {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
