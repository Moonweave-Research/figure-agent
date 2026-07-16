"""Verify-only figure loop runner.

Records one read-only loop iteration under `.scratch/fig-loop-runs/` without
editing figure source, compile/export state, or acceptance artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import closed_loop_attempt_state  # noqa: E402
import closed_loop_current_state  # noqa: E402
import fixture_identity  # noqa: E402
import narrative_context  # noqa: E402
import repair_transaction  # noqa: E402
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
from fig_loop_stop_diagnoser import diagnose_run as build_stop_diagnosis  # noqa: E402
from fig_loop_stop_router import route_stop_cause  # noqa: E402
from inputs import parse_spec  # noqa: E402
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


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


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
    route = bottleneck.get("route")
    if route != "human_art_direction":
        return loop_decision
    lever_id = bottleneck.get("lever_id", "aesthetic lever")
    updated = dict(loop_decision)
    updated.update(
        {
            "stop_reason": "human_gate_required",
            "recommended_next_action": (f"human art-direction review required for {lever_id}"),
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
                "recommended_next_action": (f"human review required for {detail_text}"),
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
            "human_gate_status": "not_requested",
        }
    )
    return updated


def _stop_diagnosis_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "stop_report": "stop_report.json",
        "dominant_premature_cause": report.get("dominant_premature_cause"),
        "dominant_premature_count": report.get("dominant_premature_count"),
        "cause_histogram": report.get("cause_histogram") or {},
    }


def _stop_route_records(report: dict[str, Any]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for subregion in report.get("subregions") or []:
        if not isinstance(subregion, dict):
            continue
        route = route_stop_cause(subregion)
        routes.append(
            {
                "subregion_id": subregion.get("subregion_id"),
                "stop_cause": route.cause,
                "fix_mode": route.fix_mode,
                "action": route.action,
                "payload": route.payload,
                "blocked_by": route.blocked_by,
            }
        )
    return routes


def _tail(text: str, *, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _run_auto_remedy_command(command: list[str], *, repo_root: Path) -> CommandResult:
    ensure_safe_command(tuple(command))
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(REPO_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(repo_root)
    result = subprocess.run(
        command,
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        errors="replace",
    )
    return CommandResult(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _report_has_signal(report: dict[str, Any], signal_key: str) -> bool:
    for subregion in report.get("subregions") or []:
        if not isinstance(subregion, dict):
            continue
        for evidence in subregion.get("evidence") or []:
            if isinstance(evidence, dict) and evidence.get("signal_key") == signal_key:
                return True
    return False


def _auto_remedy_plan(
    name: str,
    status_result: dict[str, Any],
    stop_report: dict[str, Any],
) -> dict[str, Any] | None:
    critique_state = status_result.get("critique_state")
    fig_agent = str(REPO_ROOT / "bin" / "fig-agent")
    if critique_state in {"MISSING", "STALE"}:
        return {
            "cause": f"critique_{str(critique_state).lower()}",
            "commands": [[fig_agent, "critique-scaffold", name, "--json"]],
        }
    if _report_has_signal(stop_report, "stale_detector_evidence"):
        return {
            "cause": "stale_detector_evidence",
            "commands": [[fig_agent, "compile", name, "--strict"]],
        }
    return None


def _remedy_ineffective(
    *,
    plan: dict[str, Any],
    after_status: dict[str, Any],
    after_report: dict[str, Any],
) -> bool:
    cause = plan.get("cause")
    if cause in {"critique_missing", "critique_stale"}:
        return after_status.get("critique_state") in {"MISSING", "STALE"}
    if cause == "stale_detector_evidence":
        return _report_has_signal(after_report, "stale_detector_evidence")
    return False


def _existing_auto_remedy_for_cause(run_dir: Path, cause: str) -> dict[str, Any] | None:
    for iteration_path in sorted(run_dir.glob("iteration_*.json")):
        try:
            payload = json.loads(iteration_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return {
                "cause": cause,
                "status": "history_unreadable",
                "reason": "auto_remedy_history_unreadable",
                "path": str(iteration_path),
                "error": str(exc),
            }
        if not isinstance(payload, dict):
            return {
                "cause": cause,
                "status": "history_unreadable",
                "reason": "auto_remedy_history_invalid",
                "path": str(iteration_path),
            }
        auto_remedy = payload.get("auto_remedy")
        if isinstance(auto_remedy, dict) and auto_remedy.get("cause") == cause:
            return auto_remedy
    return None


def _apply_auto_remedy(
    name: str,
    run_dir: Path,
    *,
    repo_root: Path,
    status_result: dict[str, Any],
    stop_report: dict[str, Any],
    runner=_run_auto_remedy_command,
    diagnose=build_stop_diagnosis,
    status_reader=infer_stage,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    plan = _auto_remedy_plan(name, status_result, stop_report)
    if plan is None:
        return None, stop_report
    previous = _existing_auto_remedy_for_cause(run_dir, str(plan["cause"]))
    if previous is not None:
        return (
            {
                "cause": plan["cause"],
                "status": "remedy_ineffective",
                "reason": previous.get("reason") or "auto_remedy_already_attempted_for_cause",
                "previous_status": previous.get("status"),
                "command_results": [],
            },
            stop_report,
        )
    command_results: list[dict[str, Any]] = []
    for command in plan["commands"]:
        result = runner(command, repo_root=repo_root)
        command_results.append(
            {
                "command": command,
                "returncode": result.returncode,
                "stdout_tail": _tail(result.stdout),
                "stderr_tail": _tail(result.stderr),
            }
        )
        if result.returncode != 0:
            return (
                {
                    "cause": plan["cause"],
                    "status": "command_failed",
                    "command_results": command_results,
                },
                stop_report,
            )
    after_report = diagnose(
        name,
        run_dir,
        repo_root=repo_root,
        plugin_root=REPO_ROOT,
    )
    after_status = status_reader(repo_root / "examples" / name)
    status = (
        "remedy_ineffective"
        if _remedy_ineffective(
            plan=plan,
            after_status=after_status,
            after_report=after_report,
        )
        else "remedied"
    )
    return (
        {
            "cause": plan["cause"],
            "status": status,
            "command_results": command_results,
            "post_remedy_stop_report": "stop_report.json",
        },
        after_report,
    )


def _git_value(repo_root: Path, args: tuple[str, ...]) -> str | None:
    command = ensure_safe_command(("git", *args))
    result = subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _narrative_spec(example_dir: Path) -> dict[str, Any]:
    try:
        return parse_spec((example_dir / "spec.yaml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return {}


def _narrative_context_summary(example_dir: Path, repo_root: Path) -> dict[str, Any]:
    payload = narrative_context.build_narrative_context(
        example_dir,
        workspace_root=repo_root,
        spec=_narrative_spec(example_dir),
    )
    reader_contract = payload["reader_contract"]
    stop_boundaries = payload["stop_boundaries"]
    return {
        "schema": payload["schema"],
        "read_only": payload["read_only"],
        "first_takeaway_source": reader_contract["first_takeaway_source"],
        "panel_story_input_count": len(reader_contract["panel_story_inputs"]),
        "human_review_question_count": len(reader_contract["human_review_questions"]),
        "rank_scoring": stop_boundaries["rank_scoring"],
        "source_mutation": stop_boundaries["source_mutation"],
    }


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
    """Run one legacy checkpoint only when canonical lifecycle discovery is absent."""
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise FigLoopError(str(exc)) from exc
    root = repo_root.resolve()
    try:
        normalized_runs_root = closed_loop_attempt_state.validate_legacy_runs_root(
            root,
            runs_root or root / ".scratch" / "fig-loop-runs",
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise FigLoopError(str(exc)) from exc
    example_dir = root / "examples" / name
    if not example_dir.is_dir():
        raise FigLoopError(f"examples/{name}/ not found")
    with ExitStack() as stack:
        try:
            stack.enter_context(
                closed_loop_attempt_state.fixture_admission_lock(root, name)
            )
        except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
            raise FigLoopError(f"canonical_preflight:{exc}") from exc
        except closed_loop_attempt_state.FixtureAdmissionLeaseBusy as exc:
            raise FigLoopError(
                "canonical_admission_legacy_coordination_busy; retry canonical admission "
                "or legacy coordination"
            ) from exc
        except repair_transaction.RepairTransactionError as exc:
            raise FigLoopError(str(exc)) from exc
        except OSError as exc:
            raise FigLoopError("canonical_preflight_error") from exc
        try:
            current = closed_loop_current_state.resolve_current_attempt(root, name)
        except OSError as exc:
            raise FigLoopError("canonical_state_resolution_error") from exc
        if current.get("resolution") != "absent":
            raise FigLoopError(
                "canonical_attempt_resolution:"
                f"{current.get('resolution')}:{current.get('reason')}; "
                "use canonical status/lifecycle"
            )
        source = example_dir / f"{name}.tex"
        if source.exists() or source.is_symlink():
            try:
                closed_loop_attempt_state._workspace_artifact(  # noqa: SLF001
                    root, name, source, label="source"
                )
            except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
                raise FigLoopError(f"canonical_preflight:{exc}") from exc
        return _run_loop_after_admission(
            name,
            goal,
            repo_root=root,
            runs_root=normalized_runs_root,
        )


def _run_loop_after_admission(
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
    try:
        runs_root = closed_loop_attempt_state.validate_legacy_runs_root(
            repo_root,
            runs_root or repo_root / ".scratch" / "fig-loop-runs",
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise FigLoopError(str(exc)) from exc
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
        "narrative_context_summary": _narrative_context_summary(example_dir, repo_root),
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
    stop_report = build_stop_diagnosis(
        name,
        run_dir,
        repo_root=repo_root,
        plugin_root=REPO_ROOT,
    )
    iteration["stop_diagnosis"] = _stop_diagnosis_summary(stop_report)
    iteration["stop_routes"] = _stop_route_records(stop_report)
    iteration["auto_remedy"] = None
    manifest["stop_report"] = "stop_report.json"
    manifest["dominant_premature_cause"] = stop_report.get("dominant_premature_cause")
    manifest["dominant_premature_count"] = stop_report.get("dominant_premature_count")
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
