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

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fixture_identity  # noqa: E402
from fig_driver_editorial import (  # noqa: E402
    svg_polish_gate_from_checkpoint,
    svg_polish_readiness_from_checkpoint,
)
from fig_loop_adjudication import adjudication_state as build_adjudication_state  # noqa: E402
from fig_loop_assessments import (  # noqa: E402
    aesthetic_lever_summary as build_aesthetic_lever_summary,
)
from fig_loop_assessments import (
    crop_audit_summary as build_crop_audit_summary,
)
from fig_loop_assessments import (
    editorial_art_direction_summary as build_editorial_art_direction_summary,
)
from fig_loop_assessments import (
    external_vision_review_summary as build_external_vision_review_summary,
)
from fig_loop_assessments import (
    journal_art_direction_playbook_summary as build_journal_art_direction_playbook_summary,
)
from fig_loop_assessments import (
    journal_grade_assessment as build_journal_grade_assessment,
)
from fig_loop_assessments import (
    top_tier_audit_summary as build_top_tier_audit_summary,
)
from fig_loop_auto_patch import auto_patch_eligibility as build_auto_patch_eligibility  # noqa: E402
from fig_loop_axes import axis_verdicts as build_axis_verdicts  # noqa: E402
from fig_loop_basin import basin_summary as build_basin_summary  # noqa: E402
from fig_loop_decision import (  # noqa: E402
    loop_decision as build_loop_decision,
)
from fig_loop_escalation import escalation_summary  # noqa: E402
from fig_loop_handoff import patch_handoff as build_patch_handoff  # noqa: E402
from fig_loop_markdown import decision_markdown as build_decision_markdown  # noqa: E402
from fig_loop_patch_evidence import (  # noqa: E402
    patch_evidence_baseline,
    post_patch_evidence_verdict,
)
from fig_loop_records import json_stdout_summary, write_json  # noqa: E402
from next_action_summary import loop_next_action_summary  # noqa: E402
from reference_aesthetic_metrics import (  # noqa: E402
    reference_aesthetic_metrics_summary as build_reference_aesthetic_metrics_summary,
)
from status import infer_stage  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_ROOT = REPO_ROOT / ".scratch" / "fig-loop-runs"
MODE = "verify-only"
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


def _apply_aesthetic_lever_stop(
    loop_decision: dict,
    aesthetic_lever_summary: dict | None,
) -> dict:
    if not aesthetic_lever_summary:
        return loop_decision
    if aesthetic_lever_summary.get("evaluation_state") != "needs_human":
        return loop_decision
    bottleneck = aesthetic_lever_summary.get("next_aesthetic_bottleneck") or {}
    lever_id = bottleneck.get("lever_id", "aesthetic lever")
    updated = dict(loop_decision)
    updated.update(
        {
            "stop_reason": "human_gate_required",
            "recommended_next_action": (
                f"human art-direction review required for {lever_id}"
            ),
            "active_patch_target": None,
            "human_gate_status": "required",
        }
    )
    return updated


def _apply_external_vision_stop(
    loop_decision: dict,
    external_summary: dict | None,
) -> dict:
    if not external_summary:
        return loop_decision
    state = external_summary.get("evaluation_state")
    if state == "needs_human":
        conflicts = external_summary.get("active_conflicts") or []
        findings = external_summary.get("active_findings") or []
        if conflicts:
            detail_text = f"external vision conflict: {', '.join(conflicts)}"
        elif findings:
            detail_text = f"external vision finding: {', '.join(findings)}"
        else:
            detail_text = "external vision review"
        updated = dict(loop_decision)
        updated.update(
            {
                "stop_reason": "human_gate_required",
                "recommended_next_action": (
                    f"human review required for {detail_text}"
                ),
                "active_patch_target": None,
                "human_gate_status": "required",
            }
        )
        return updated
    if state in {"stale", "missing_artifact", "invalid"}:
        if loop_decision.get("stop_reason") == "human_gate_required":
            return loop_decision
        updated = dict(loop_decision)
        updated.update(
            {
                "stop_reason": "status_action_required",
                "recommended_next_action": (
                    "refresh or fix external_vision_review.yaml before relying on "
                    "external vision evidence"
                ),
                "active_patch_target": None,
            }
        )
        return updated
    return loop_decision


def _apply_reference_aesthetic_metrics_stop(
    loop_decision: dict,
    metrics_summary: dict | None,
) -> dict:
    if not metrics_summary:
        return loop_decision
    state = metrics_summary.get("evaluation_state")
    if state == "severe_divergence":
        blocking_items = metrics_summary.get("blocking_items") or []
        blocking_text = ", ".join(blocking_items) if blocking_items else "metric threshold"
        updated = dict(loop_decision)
        updated.update(
            {
                "stop_reason": "human_gate_required",
                "recommended_next_action": (
                    "human review required for reference aesthetic metric divergence: "
                    f"{blocking_text}"
                ),
                "active_patch_target": None,
                "human_gate_status": "required",
            }
        )
        return updated
    if state in {"missing", "stale", "invalid"}:
        if loop_decision.get("stop_reason") == "human_gate_required":
            return loop_decision
        updated = dict(loop_decision)
        updated.update(
            {
                "stop_reason": "status_action_required",
                "recommended_next_action": (
                    metrics_summary.get("next_action")
                    or "refresh reference aesthetic metrics before relying on them"
                ),
                "active_patch_target": None,
            }
        )
        return updated
    return loop_decision


def _apply_basin_stop(loop_decision: dict, basin_summary: dict | None) -> dict:
    if not basin_summary:
        return loop_decision
    updated = dict(loop_decision)
    updated.update(
        {
            "stop_reason": "basin_detected",
            "recommended_next_action": basin_summary["next_action"],
            "active_patch_target": None,
            "human_gate_status": "required",
        }
    )
    return updated


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


def run_loop(
    name: str,
    goal: str,
    *,
    repo_root: Path = REPO_ROOT,
    runs_root: Path | None = None,
) -> Path:
    """Run one verify-only loop iteration and return the run directory."""
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise FigLoopError(str(exc)) from exc
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
    adjudication = build_adjudication_state(example_dir)
    aesthetic_lever_summary = build_aesthetic_lever_summary(
        example_dir,
        status_result.get("critique_state"),
    )
    journal_playbook_summary = build_journal_art_direction_playbook_summary(
        example_dir,
        status_result.get("critique_state"),
    )
    external_vision_review_summary = build_external_vision_review_summary(example_dir)
    reference_aesthetic_metrics_summary = build_reference_aesthetic_metrics_summary(example_dir)
    loop_decision = build_loop_decision(status_result, adjudication, example_dir)
    loop_decision = _apply_aesthetic_lever_stop(loop_decision, aesthetic_lever_summary)
    loop_decision = _apply_external_vision_stop(
        loop_decision,
        external_vision_review_summary,
    )
    loop_decision = _apply_reference_aesthetic_metrics_stop(
        loop_decision,
        reference_aesthetic_metrics_summary,
    )
    basin = build_basin_summary(
        runs_root=runs_root,
        name=name,
        current_status=status_result,
        loop_decision=loop_decision,
        aesthetic_lever_summary=aesthetic_lever_summary,
        reference_aesthetic_metrics_summary=reference_aesthetic_metrics_summary,
    )
    loop_decision = _apply_basin_stop(loop_decision, basin)
    axis_verdicts = build_axis_verdicts(status_result, adjudication, loop_decision, example_dir)
    escalation = escalation_summary(loop_decision)
    patch_handoff = build_patch_handoff(name, loop_decision)
    next_action_summary = loop_next_action_summary(
        loop_decision,
        status_result,
        patch_handoff,
    )
    journal_grade_assessment = build_journal_grade_assessment(
        example_dir,
        status_result.get("critique_state"),
    )
    top_tier_audit_summary = build_top_tier_audit_summary(
        example_dir,
        status_result.get("critique_state"),
    )
    editorial_art_direction_summary = build_editorial_art_direction_summary(
        example_dir,
        status_result.get("critique_state"),
    )
    crop_audit_summary = build_crop_audit_summary(
        example_dir,
        status_result.get("critique_state"),
    )
    svg_polish_readiness_summary = svg_polish_readiness_from_checkpoint(
        {
            "top_tier_audit_summary": top_tier_audit_summary,
            "editorial_art_direction_summary": editorial_art_direction_summary,
            "crop_audit_summary": crop_audit_summary,
            "aesthetic_lever_summary": aesthetic_lever_summary,
        }
    )
    svg_polish_gate_summary = svg_polish_gate_from_checkpoint(
        {
            "top_tier_audit_summary": top_tier_audit_summary,
            "editorial_art_direction_summary": editorial_art_direction_summary,
            "crop_audit_summary": crop_audit_summary,
            "aesthetic_lever_summary": aesthetic_lever_summary,
            "svg_polish_readiness": svg_polish_readiness_summary,
        }
    )
    auto_patch_eligibility = build_auto_patch_eligibility(loop_decision, patch_handoff)
    post_patch_evidence = post_patch_evidence_verdict(
        repo_root,
        runs_root,
        name,
        adjudication,
        status_result,
    )
    patch_evidence = (
        None
        if post_patch_evidence is not None
        else patch_evidence_baseline(
            repo_root,
            patch_handoff,
            git_commit=lambda: _git_value(repo_root, ("rev-parse", "HEAD")),
        )
    )
    completed_at = _utc_now()

    iteration = {
        "iteration": 1,
        "status": status_result,
        "audit_evidence": status_result.get("audit_evidence"),
        "axis_verdicts": axis_verdicts,
        "adjudication": adjudication,
        "stop_reason": loop_decision["stop_reason"],
        "active_patch_target": loop_decision["active_patch_target"],
        "patch_handoff": patch_handoff,
        "next_action_summary": next_action_summary,
        "journal_grade_assessment": journal_grade_assessment,
        "top_tier_audit_summary": top_tier_audit_summary,
        "editorial_art_direction_summary": editorial_art_direction_summary,
        "svg_polish_readiness": svg_polish_readiness_summary,
        "svg_polish_gate": svg_polish_gate_summary,
        "crop_audit_summary": crop_audit_summary,
        "aesthetic_lever_summary": aesthetic_lever_summary,
        "journal_art_direction_playbook_summary": journal_playbook_summary,
        "external_vision_review_summary": external_vision_review_summary,
        "auto_patch_eligibility": auto_patch_eligibility,
        "patch_evidence": patch_evidence,
        "post_patch_evidence": post_patch_evidence,
        "recommended_next_action": loop_decision["recommended_next_action"],
        "human_gate_status": loop_decision["human_gate_status"],
        **escalation,
    }
    if reference_aesthetic_metrics_summary is not None:
        iteration["reference_aesthetic_metrics_summary"] = reference_aesthetic_metrics_summary
    if basin is not None:
        iteration["basin_summary"] = basin
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

    write_json(run_dir / "iteration_001.json", iteration)
    write_json(run_dir / "run_manifest.json", manifest)
    (run_dir / "decision.md").write_text(
        build_decision_markdown(
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="fixture name under examples/")
    parser.add_argument("--goal", required=True, help="natural-language loop goal")
    parser.add_argument("--runs-root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        run_dir = run_loop(args.name, args.goal, runs_root=args.runs_root)
    except FigLoopError as exc:
        print(f"fig_loop.py: {exc}", file=sys.stderr)
        return 1
    if args.json or args.format == "json":
        print(json.dumps(json_stdout_summary(run_dir), sort_keys=True))
        return 0
    print(f"fig_loop.py: wrote verify-only run to {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
