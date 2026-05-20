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
from fig_loop_assessments import (
    journal_grade_assessment as build_journal_grade_assessment,
)
from fig_loop_assessments import (
    top_tier_audit_summary as build_top_tier_audit_summary,
)
from fig_loop_auto_patch import auto_patch_eligibility as build_auto_patch_eligibility  # noqa: E402
from fig_loop_axes import axis_verdicts as build_axis_verdicts  # noqa: E402
from fig_loop_decision import (  # noqa: E402
    loop_decision as build_loop_decision,
)
from fig_loop_escalation import escalation_summary  # noqa: E402
from fig_loop_handoff import patch_handoff as build_patch_handoff  # noqa: E402
from fig_loop_patch_evidence import (  # noqa: E402
    patch_evidence_baseline,
    post_patch_evidence_verdict,
)
from fig_loop_records import json_stdout_summary, write_json  # noqa: E402
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
    loop_decision = build_loop_decision(status_result, adjudication, example_dir)
    axis_verdicts = build_axis_verdicts(status_result, adjudication, loop_decision, example_dir)
    escalation = escalation_summary(loop_decision)
    patch_handoff = build_patch_handoff(name, loop_decision)
    journal_grade_assessment = build_journal_grade_assessment(
        example_dir,
        status_result.get("critique_state"),
    )
    top_tier_audit_summary = build_top_tier_audit_summary(
        example_dir,
        status_result.get("critique_state"),
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
        "axis_verdicts": axis_verdicts,
        "adjudication": adjudication,
        "stop_reason": loop_decision["stop_reason"],
        "active_patch_target": loop_decision["active_patch_target"],
        "patch_handoff": patch_handoff,
        "journal_grade_assessment": journal_grade_assessment,
        "top_tier_audit_summary": top_tier_audit_summary,
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

    write_json(run_dir / "iteration_001.json", iteration)
    write_json(run_dir / "run_manifest.json", manifest)
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
        print(json.dumps(json_stdout_summary(run_dir), sort_keys=True))
        return 0
    print(f"fig_loop.py: wrote verify-only run to {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
