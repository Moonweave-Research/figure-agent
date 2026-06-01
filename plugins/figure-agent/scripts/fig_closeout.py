"""Read-only post-patch closeout checklist for one figure."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fixture_identity  # noqa: E402
from critique_adjudication import (  # noqa: E402
    CritiqueAdjudicationError,
    adjudication_is_stale,
    load_adjudication,
)
from next_action_summary import closeout_next_action_summary  # noqa: E402
from status import infer_stage  # noqa: E402
from text_boundary_spec_helper import (  # noqa: E402
    TextBoundarySpecHelperError,
    build_text_boundary_checks,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPLETE_STATES = frozenset({"passed", "not_required"})
FIG_LOOP_SCHEMA = "figure-agent.fig-loop-run.v1"


class FigCloseoutError(ValueError):
    """Expected user-facing error for closeout preflight failures."""


def _step(
    *,
    step_id: str,
    state: str,
    reason: str,
    command: str | None = None,
    evidence_path: Path | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": step_id,
        "state": state,
        "reason": reason,
        "command": command,
        "evidence_path": str(evidence_path) if evidence_path else None,
        "evidence": evidence or {},
    }


def _compile_step(name: str, status_result: dict[str, Any]) -> dict[str, Any]:
    render_state = status_result.get("render_state")
    if render_state == "FRESH":
        return _step(
            step_id="compile",
            state="passed",
            reason="render_state is FRESH",
            evidence={"render_state": render_state},
        )
    if render_state in {"NOT_SCAFFOLDED", "NOT_AUTHORED"}:
        return _step(
            step_id="compile",
            state="blocked",
            reason=f"render_state is {render_state}; source must exist before compile",
            evidence={"render_state": render_state, "next": status_result.get("next")},
        )
    return _step(
        step_id="compile",
        state="needs_action",
        reason=f"render_state is {render_state}",
        command=f"/fig_compile {name}",
        evidence={"render_state": render_state, "next": status_result.get("next")},
    )


def _text_boundary_checks_step(name: str, example_dir: Path) -> dict[str, Any]:
    spec_path = example_dir / "spec.yaml"
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        return _step(
            step_id="text_boundary_checks",
            state="blocked",
            reason=f"cannot read spec.yaml for text boundary checks: {exc}",
            evidence_path=spec_path,
        )
    if not isinstance(spec, dict):
        return _step(
            step_id="text_boundary_checks",
            state="blocked",
            reason="spec.yaml must be a mapping",
            evidence_path=spec_path,
        )
    layout = spec.get("text_boundary_layout")
    if layout is None:
        return _step(
            step_id="text_boundary_checks",
            state="not_required",
            reason="spec.yaml.text_boundary_layout is absent",
            evidence_path=spec_path,
        )
    try:
        expected_checks = build_text_boundary_checks(layout)
    except TextBoundarySpecHelperError as exc:
        return _step(
            step_id="text_boundary_checks",
            state="blocked",
            reason=f"text_boundary_layout is invalid: {exc}",
            evidence_path=spec_path,
        )
    if spec.get("text_boundary_checks") == expected_checks:
        return _step(
            step_id="text_boundary_checks",
            state="passed",
            reason="text_boundary_checks match text_boundary_layout",
            evidence_path=spec_path,
            evidence={"check_count": len(expected_checks)},
        )
    reason = (
        "text_boundary_checks are missing"
        if "text_boundary_checks" not in spec
        else "text_boundary_checks do not match text_boundary_layout"
    )
    return _step(
        step_id="text_boundary_checks",
        state="needs_action",
        reason=reason,
        command=f"uv run python3 scripts/text_boundary_spec_helper.py examples/{name} --write",
        evidence_path=spec_path,
        evidence={"expected_check_count": len(expected_checks)},
    )


def _critique_step(name: str, status_result: dict[str, Any], example_dir: Path) -> dict[str, Any]:
    critique_state = status_result.get("critique_state")
    critique_path = example_dir / "critique.md"
    if critique_state == "NOT_REQUIRED":
        return _step(
            step_id="critique",
            state="not_required",
            reason="critique_state is NOT_REQUIRED",
            evidence={"critique_state": critique_state},
        )
    if critique_state == "FRESH":
        return _step(
            step_id="critique",
            state="passed",
            reason="critique_state is FRESH",
            evidence_path=critique_path if critique_path.is_file() else None,
            evidence={"critique_state": critique_state},
        )
    if critique_state == "REFERENCE_MISSING":
        return _step(
            step_id="critique",
            state="blocked",
            reason="reference input is missing; fix declared reference paths before critique",
            evidence={"critique_state": critique_state, "notes": status_result.get("notes", [])},
        )
    return _step(
        step_id="critique",
        state="needs_action",
        reason=f"critique_state is {critique_state}",
        command=f"/fig_critique {name}",
        evidence_path=critique_path if critique_path.is_file() else None,
        evidence={"critique_state": critique_state, "next": status_result.get("next")},
    )


def _adjudication_step(
    name: str,
    status_result: dict[str, Any],
    example_dir: Path,
) -> dict[str, Any]:
    critique_state = status_result.get("critique_state")
    adjudication_path = example_dir / "critique_adjudication.yaml"
    critique_path = example_dir / "critique.md"
    if critique_state == "NOT_REQUIRED":
        return _step(
            step_id="adjudication",
            state="not_required",
            reason="critique adjudication is not required without a critique requirement",
            evidence={"critique_state": critique_state},
        )
    if critique_state != "FRESH":
        return _step(
            step_id="adjudication",
            state="blocked",
            reason="fresh critique is required before adjudication can be closed",
            evidence={"critique_state": critique_state},
        )
    if not adjudication_path.is_file():
        return _step(
            step_id="adjudication",
            state="needs_action",
            reason="critique_adjudication.yaml is missing",
            command=f"/fig_adjudicate {name}",
            evidence_path=adjudication_path,
        )
    try:
        load_adjudication(adjudication_path)
        stale = adjudication_is_stale(adjudication_path, critique_path)
    except CritiqueAdjudicationError as exc:
        return _step(
            step_id="adjudication",
            state="needs_action",
            reason=f"critique_adjudication.yaml is invalid: {exc}",
            evidence_path=adjudication_path,
            evidence={"repair_target": str(adjudication_path)},
        )
    if stale:
        return _step(
            step_id="adjudication",
            state="needs_action",
            reason="critique_adjudication.yaml is stale against critique.md",
            evidence_path=adjudication_path,
            evidence={"repair_target": str(adjudication_path)},
        )
    return _step(
        step_id="adjudication",
        state="passed",
        reason="critique_adjudication.yaml is fresh",
        evidence_path=adjudication_path,
    )


def _export_step(
    name: str,
    status_result: dict[str, Any],
    compile_step: dict[str, Any],
    critique_step: dict[str, Any],
) -> dict[str, Any]:
    export_state = status_result.get("export_state")
    prerequisite_steps = (compile_step, critique_step)
    incomplete = [
        step["id"]
        for step in prerequisite_steps
        if step["state"] not in COMPLETE_STATES
    ]
    if incomplete:
        return _step(
            step_id="export",
            state="blocked",
            reason=f"closeout prerequisites are incomplete: {', '.join(incomplete)}",
            evidence={"export_state": export_state, "blocked_by": incomplete},
        )
    if export_state == "FRESH":
        return _step(
            step_id="export",
            state="passed",
            reason="export_state is FRESH",
            evidence={"export_state": export_state},
        )
    if export_state == "TRACKED_GOLDEN":
        return _step(
            step_id="export",
            state="blocked",
            reason="tracked golden export requires deliberate manual approval",
            evidence={
                "export_state": export_state,
                "approval_command": f"/fig_export {name} --force-golden",
            },
        )
    return _step(
        step_id="export",
        state="needs_action",
        reason=f"export_state is {export_state}",
        command=f"/fig_export {name}",
        evidence={"export_state": export_state},
    )


def _valid_loop_iteration(iteration_path: Path, name: str) -> bool:
    manifest_path = iteration_path.parent / "run_manifest.json"
    try:
        iteration = json.loads(iteration_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(iteration, dict) or iteration.get("iteration") != 1:
        return False
    if not isinstance(manifest, dict):
        return False
    manifest_iterations = manifest.get("iterations")
    return (
        manifest.get("schema") == FIG_LOOP_SCHEMA
        and manifest.get("fixture") == name
        and isinstance(manifest_iterations, list)
        and "iteration_001.json" in manifest_iterations
    )


def _latest_loop_iteration(runs_root: Path, name: str) -> Path | None:
    candidates = (
        path
        for path in runs_root.glob(f"*-{name}/iteration_001.json")
        if _valid_loop_iteration(path, name)
    )
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _tracked_closeout_inputs(example_dir: Path, name: str) -> list[Path]:
    candidates = [
        example_dir / "spec.yaml",
        example_dir / "briefing.md",
        example_dir / f"{name}.tex",
        example_dir / "critique.md",
        example_dir / "critique_adjudication.yaml",
    ]
    for folder_name in ("build", "exports"):
        folder = example_dir / folder_name
        if folder.is_dir():
            candidates.extend(path for path in folder.rglob("*") if path.is_file())
    return [path for path in candidates if path.is_file()]


def _loop_rerun_step(
    name: str,
    example_dir: Path,
    repo_root: Path,
    runs_root: Path,
    prerequisite_steps: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    incomplete = [
        step["id"]
        for step in prerequisite_steps
        if step["state"] not in COMPLETE_STATES
    ]
    if incomplete:
        return _step(
            step_id="loop_rerun",
            state="blocked",
            reason=f"closeout prerequisites are incomplete: {', '.join(incomplete)}",
            evidence={"blocked_by": incomplete},
        )
    latest_iteration = _latest_loop_iteration(runs_root, name)
    command = f'/fig_loop {name} --goal "<goal>"'
    if latest_iteration is None:
        return _step(
            step_id="loop_rerun",
            state="needs_action",
            reason="no post-patch fig_loop run was found",
            command=command,
        )
    inputs = _tracked_closeout_inputs(example_dir, name)
    newest_input = max(inputs, key=lambda path: path.stat().st_mtime, default=None)
    if newest_input and newest_input.stat().st_mtime > latest_iteration.stat().st_mtime:
        return _step(
            step_id="loop_rerun",
            state="needs_action",
            reason=f"{_display_path(newest_input, repo_root)} is newer than latest loop record",
            command=command,
            evidence_path=latest_iteration,
        )
    return _step(
        step_id="loop_rerun",
        state="passed",
        reason="latest fig_loop record is newer than closeout inputs",
        evidence_path=latest_iteration,
    )


def compute_closeout(
    name: str,
    *,
    repo_root: Path = REPO_ROOT,
    runs_root: Path | None = None,
) -> dict[str, Any]:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise FigCloseoutError(str(exc)) from exc
    repo_root = repo_root.resolve()
    runs_root = (runs_root or repo_root / ".scratch" / "fig-loop-runs").resolve()
    example_dir = repo_root / "examples" / name
    if not example_dir.is_dir():
        raise FigCloseoutError(f"examples/{name}/ not found")

    try:
        status_result = infer_stage(example_dir)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise FigCloseoutError(f"cannot compute status for examples/{name}: {exc}") from exc
    text_boundary_checks_step = _text_boundary_checks_step(name, example_dir)
    compile_step = _compile_step(name, status_result)
    critique_step = _critique_step(name, status_result, example_dir)
    adjudication_step = _adjudication_step(name, status_result, example_dir)
    export_step = _export_step(
        name,
        status_result,
        compile_step,
        critique_step,
    )
    loop_rerun_step = _loop_rerun_step(
        name,
        example_dir,
        repo_root,
        runs_root,
        (
            text_boundary_checks_step,
            compile_step,
            critique_step,
            adjudication_step,
            export_step,
        ),
    )
    steps = [
        text_boundary_checks_step,
        compile_step,
        critique_step,
        adjudication_step,
        export_step,
        loop_rerun_step,
    ]
    incomplete = [step for step in steps if step["state"] not in COMPLETE_STATES]
    next_step = next((step for step in steps if step["state"] == "needs_action"), None)
    if next_step is None:
        next_step = next((step for step in steps if step["state"] == "blocked"), None)
    report = {
        "schema": "figure-agent.closeout.v1",
        "fixture": name,
        "closeout_complete": not incomplete,
        "next_action": (
            next_step["command"] or next_step["reason"] if next_step else "closeout complete"
        ),
        "blocking_step_ids": [step["id"] for step in incomplete],
        "status": {
            "render_state": status_result.get("render_state"),
            "critique_state": status_result.get("critique_state"),
            "export_state": status_result.get("export_state"),
            "workflow_ready": status_result.get("workflow_ready"),
            "next": status_result.get("next"),
        },
        "steps": steps,
    }
    report["next_action_summary"] = closeout_next_action_summary(report)
    return report


def _print_human(report: dict[str, Any]) -> None:
    print(f"fig_closeout.py: {report['fixture']} closeout")
    for step in report["steps"]:
        command = f" -> {step['command']}" if step["command"] else ""
        print(f"- {step['id']}: {step['state']} ({step['reason']}){command}")
    print(f"next: {report['next_action']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="fixture name under examples/")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--runs-root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        report = compute_closeout(args.name, repo_root=args.repo_root, runs_root=args.runs_root)
    except FigCloseoutError as exc:
        print(f"fig_closeout.py: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report["closeout_complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
