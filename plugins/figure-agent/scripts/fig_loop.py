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
from status import infer_stage  # noqa: E402
from subregion_active_set import active_subregion_ids, parse_active_target_rows  # noqa: E402

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

    apply_decision = _first_decision(adjudication, "apply")
    if apply_decision:
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


def _axis_verdicts(
    status_result: dict[str, Any],
    adjudication: dict[str, Any],
    loop_decision: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    stop_reason = loop_decision["stop_reason"]
    return {
        "render": {
            "state": status_result.get("render_state"),
            "verdict": "fresh" if status_result.get("render_state") == "FRESH" else "not_ready",
        },
        "static_visual": {
            "state": "not_evaluated",
            "verdict": "not_evaluated",
        },
        "critique": {
            "state": status_result.get("critique_state"),
            "verdict": "ready"
            if status_result.get("critique_state") in {"FRESH", "NOT_REQUIRED"}
            else "needs_action",
        },
        "adjudication": {
            "state": adjudication["state"],
            "verdict": _adjudication_verdict(adjudication, stop_reason),
        },
        "theory": {
            "state": "not_evaluated",
            "verdict": "human_review_not_requested",
        },
        "reference_fidelity": {
            "state": status_result.get("notes", []),
            "verdict": "blocked" if stop_reason == "reference_input_missing" else "not_blocked",
        },
        "story_hierarchy": {
            "state": "not_evaluated",
            "verdict": "not_evaluated",
        },
        "export": {
            "state": status_result.get("export_state"),
            "verdict": "fresh" if status_result.get("export_state") == "FRESH" else "not_ready",
        },
        "publication_safety": {
            "state": status_result.get("acceptance_state"),
            "verdict": "human_gate"
            if loop_decision["human_gate_status"] == "required"
            else "not_cleared",
        },
    }


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
    if stop_reason == "human_gate_required":
        level = "human_review_required"
    elif stop_reason == "patch_target_recommended":
        level = "patch_allowed"
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
    axis_verdicts = _axis_verdicts(status_result, adjudication, loop_decision)
    escalation = _escalation_summary(loop_decision)
    patch_handoff = _patch_handoff(name, loop_decision)
    completed_at = _utc_now()

    iteration = {
        "iteration": 1,
        "status": status_result,
        "axis_verdicts": axis_verdicts,
        "adjudication": adjudication,
        "stop_reason": loop_decision["stop_reason"],
        "active_patch_target": loop_decision["active_patch_target"],
        "patch_handoff": patch_handoff,
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="fixture name under examples/")
    parser.add_argument("--goal", required=True, help="natural-language loop goal")
    parser.add_argument("--runs-root", type=Path, default=None)
    args = parser.parse_args()

    try:
        run_dir = run_loop(args.name, args.goal, runs_root=args.runs_root)
    except FigLoopError as exc:
        print(f"fig_loop.py: {exc}", file=sys.stderr)
        return 1
    print(f"fig_loop.py: wrote verify-only run to {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
