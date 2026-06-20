"""Read-only post-patch closeout checklist for one figure."""

from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fixture_identity  # noqa: E402
import runtime_paths  # noqa: E402
from critique_adjudication import (  # noqa: E402
    CritiqueAdjudicationError,
    adjudication_is_stale,
    load_adjudication,
)
from next_action_summary import closeout_next_action_summary  # noqa: E402
from text_boundary_spec_helper import (  # noqa: E402
    TextBoundarySpecHelperError,
    build_text_boundary_checks,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPLETE_STATES = frozenset({"passed", "not_required"})
FIG_LOOP_SCHEMA = "figure-agent.fig-loop-run.v1"


class FigCloseoutError(ValueError):
    """Expected user-facing error for closeout preflight failures."""


def infer_stage(example_dir: Path) -> dict[str, Any]:
    from status import infer_stage as _infer_stage

    return _infer_stage(example_dir)


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
        command=f"fig-agent text-boundary {name} --write",
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
    example_dir: Path,
    status_result: dict[str, Any],
    compile_step: dict[str, Any],
    critique_step: dict[str, Any],
    golden_acceptance: dict[str, Any],
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
        accepted, reason = _golden_acceptance_covers_current_state(
            name,
            example_dir,
            golden_acceptance,
        )
        if accepted:
            return _step(
                step_id="export",
                state="passed",
                reason="tracked golden export has current explicit acceptance",
                evidence={
                    "export_state": export_state,
                    "golden_acceptance": golden_acceptance,
                },
            )
        return _step(
            step_id="export",
            state="blocked",
            reason="tracked golden export requires deliberate manual approval"
            if reason == "missing"
            else f"tracked golden export acceptance is invalid: {reason}",
            evidence={
                "export_state": export_state,
                "approval_command": f"/fig_export {name} --force-golden",
                "golden_acceptance": golden_acceptance,
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


def _fixture_relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _latest_apply_result_path(example_dir: Path) -> Path | None:
    build_dir = example_dir / "build"
    if build_dir.is_symlink():
        return None
    candidates_root = example_dir / "build" / "candidates"
    if not candidates_root.is_dir() or candidates_root.is_symlink():
        return None
    candidates = [
        path
        for path in candidates_root.glob("*/apply_result.json")
        if path.is_file() and not path.is_symlink()
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def _candidate_apply_summary(example_dir: Path) -> dict[str, Any]:
    apply_result_path = _latest_apply_result_path(example_dir)
    if apply_result_path is None:
        return {"status": "not_required", "apply_result_path": None}
    try:
        apply_result = json.loads(apply_result_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {
            "status": "unreadable",
            "apply_result_path": _fixture_relative(example_dir, apply_result_path),
        }
    post_apply = apply_result.get("post_apply")
    post_apply_summary: dict[str, str] = {}
    if isinstance(post_apply, dict):
        for stage in ("compile", "export", "status"):
            value = post_apply.get(stage)
            if isinstance(value, dict):
                post_apply_summary[stage] = str(value.get("status") or "missing")
            elif value is not None:
                post_apply_summary[stage] = str(value)
    return {
        "status": str(apply_result.get("status") or "unknown"),
        "candidate_id": str(apply_result.get("candidate_id") or ""),
        "apply_result_path": _fixture_relative(example_dir, apply_result_path),
        "post_apply": post_apply_summary,
    }


def _golden_acceptance_summary(example_dir: Path) -> dict[str, Any]:
    build_dir = example_dir / "build"
    closeout_dir = build_dir / "closeout"
    path = example_dir / "build" / "closeout" / "golden_acceptance.json"
    relative = _fixture_relative(example_dir, path)
    for label, candidate in (
        ("build", build_dir),
        ("closeout", closeout_dir),
        ("golden_acceptance.json", path),
    ):
        if candidate.is_symlink():
            return {"state": "invalid", "path": relative, "reason": f"{label} symlink"}
    if not path.is_file():
        return {"state": "missing", "path": relative}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"state": "invalid", "path": relative, "reason": "unreadable"}
    return {
        "state": "present",
        "path": relative,
        "decision": payload.get("decision"),
        "reviewer": payload.get("reviewer"),
        "reviewed_at": payload.get("reviewed_at"),
        "accept_golden": bool(payload.get("accept_golden")),
        "source_sha256": payload.get("source_sha256"),
        "exports": payload.get("exports") if isinstance(payload.get("exports"), dict) else {},
    }


def _current_export_hashes(example_dir: Path, name: str) -> dict[str, str]:
    exports_dir = example_dir / "exports"
    hashes: dict[str, str] = {}
    for ext in ("pdf", "svg", "png", "tif", "tiff"):
        path = exports_dir / f"{name}.{ext}"
        if path.is_file() and not path.is_symlink():
            hashes["tif" if ext == "tiff" else ext] = _sha256_file(path)
    return hashes


def _golden_acceptance_covers_current_state(
    name: str,
    example_dir: Path,
    acceptance: dict[str, Any],
) -> tuple[bool, str | None]:
    if acceptance.get("state") != "present":
        return False, str(acceptance.get("reason") or "missing")
    if acceptance.get("decision") != "accept" or not acceptance.get("accept_golden"):
        return False, "acceptance is not an explicit golden acceptance"
    source_path = example_dir / f"{name}.tex"
    if not source_path.is_file():
        return False, "source file is missing"
    if acceptance.get("source_sha256") != _sha256_file(source_path):
        return False, "accepted source hash is stale"
    accepted_exports = acceptance.get("exports")
    if not isinstance(accepted_exports, dict) or not accepted_exports:
        return False, "accepted export hashes are missing"
    current_exports = _current_export_hashes(example_dir, name)
    if set(accepted_exports) != set(current_exports):
        return False, "accepted export set is stale"
    for ext, accepted_hash in accepted_exports.items():
        if current_exports.get(str(ext)) != accepted_hash:
            return False, f"accepted {ext} export hash is stale"
    return True, None


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
    golden_acceptance = _golden_acceptance_summary(example_dir)
    export_step = _export_step(
        name,
        example_dir,
        status_result,
        compile_step,
        critique_step,
        golden_acceptance,
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
            "golden_ready": status_result.get("golden_ready"),
            "release_ready": status_result.get("release_ready"),
            "final_ready": status_result.get("final_ready"),
            "final_artifact_state": status_result.get("final_artifact_state"),
            "final_artifact_kind": status_result.get("final_artifact_kind"),
            "final_artifact_path": status_result.get("final_artifact_path"),
            "publication_gate_state": status_result.get("publication_gate_state"),
            "publication_gate_failures": status_result.get("publication_gate_failures", []),
            "next": status_result.get("next"),
        },
        "evidence_index_path": "build/evidence/evidence_index.json",
        "candidate_apply": _candidate_apply_summary(example_dir),
        "golden_acceptance": golden_acceptance,
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
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        resolved_repo_root = (
            runtime_paths.resolve_runtime_paths().workspace_root
            if args.repo_root == REPO_ROOT
            else args.repo_root
        )
        report = compute_closeout(
            args.name,
            repo_root=resolved_repo_root,
            runs_root=args.runs_root,
        )
    except FigCloseoutError as exc:
        print(f"fig_closeout.py: {exc}", file=sys.stderr)
        return 1
    if args.json or args.format == "json":
        print(json.dumps(report, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report["closeout_complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
