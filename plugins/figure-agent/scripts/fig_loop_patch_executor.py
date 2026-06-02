"""Opt-in bounded patch executor for one fig_loop handoff target."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fixture_identity
from fig_loop_patch_evidence import path_evidence

PATCH_APPLY_SCHEMA = "figure-agent.patch-apply.v1"
FORBIDDEN_PATH_PARTS = (
    "/accepted/",
    "/golden_contract",
    "/exports/",
    "/build/",
    "/critique.md",
    "/polish/",
    "/final_artifact",
    "/final-artifact",
)


class PatchExecutorError(Exception):
    """Expected user-facing patch executor error."""


@dataclass(frozen=True)
class LatestLoopRun:
    run_dir: Path
    manifest_path: Path
    iteration_path: Path
    iteration: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PatchExecutorError(f"cannot read JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise PatchExecutorError(f"JSON root must be an object: {path}")
    return payload


def _latest_loop_run(name: str, runs_root: Path) -> LatestLoopRun:
    candidates: list[LatestLoopRun] = []
    for manifest_path in runs_root.glob(f"*-{name}/run_manifest.json"):
        manifest = _read_json(manifest_path)
        if (
            manifest.get("schema") == "figure-agent.fig-loop-run.v1"
            and manifest.get("fixture") == name
        ):
            run_dir = manifest_path.parent
            iteration_path = run_dir / "iteration_001.json"
            candidates.append(
                LatestLoopRun(
                    run_dir=run_dir,
                    manifest_path=manifest_path,
                    iteration_path=iteration_path,
                    iteration=_read_json(iteration_path),
                )
            )
    if not candidates:
        raise PatchExecutorError(f"no fig_loop run found for {name}")
    return max(candidates, key=_loop_checkpoint_mtime)


def _fixture_evidence_paths(repo_root: Path, name: str) -> tuple[Path, ...]:
    example_dir = repo_root / "examples" / name
    return (
        example_dir / "spec.yaml",
        example_dir / "briefing.md",
        example_dir / "authoring_plan.md",
        example_dir / "authoring_contract.md",
        example_dir / "subregion_iteration_log.md",
        example_dir / "theory_guard.md",
        example_dir / "QUALITY_AUDIT.md",
        example_dir / f"{name}.tex",
        example_dir / "critique.md",
        example_dir / "critique_adjudication.yaml",
        example_dir / "build" / f"{name}.pdf",
    )


def _loop_checkpoint_mtime(loop_run: LatestLoopRun) -> float:
    try:
        return max(loop_run.manifest_path.stat().st_mtime, loop_run.iteration_path.stat().st_mtime)
    except OSError as exc:
        raise PatchExecutorError(f"cannot stat fig_loop run evidence: {loop_run.run_dir}") from exc


def _allowed_scope_paths(repo_root: Path, patch_handoff: dict[str, Any]) -> tuple[Path, ...]:
    allowed = patch_handoff.get("allowed_edit_scope")
    if not isinstance(allowed, list):
        return ()
    paths = []
    for rel_path in allowed:
        if isinstance(rel_path, str) and _is_safe_repo_relative_path(rel_path):
            paths.append(repo_root / rel_path)
    return tuple(paths)


def _newer_existing_paths(paths: tuple[Path, ...], checkpoint_mtime: float) -> list[Path]:
    return [path for path in paths if path.is_file() and path.stat().st_mtime > checkpoint_mtime]


def _validate_loop_run_currentness(
    name: str,
    repo_root: Path,
    loop_run: LatestLoopRun,
    patch_handoff: dict[str, Any],
) -> None:
    iteration_fixture = loop_run.iteration.get("fixture")
    if isinstance(iteration_fixture, str) and iteration_fixture != name:
        raise PatchExecutorError(
            f"latest fig_loop iteration fixture mismatch: {iteration_fixture} != {name}"
        )
    checkpoint_mtime = _loop_checkpoint_mtime(loop_run)
    try:
        newer_evidence = _newer_existing_paths(
            _fixture_evidence_paths(repo_root, name),
            checkpoint_mtime,
        )
        newer_allowed_scope = _newer_existing_paths(
            _allowed_scope_paths(repo_root, patch_handoff),
            checkpoint_mtime,
        )
    except OSError as exc:
        raise PatchExecutorError(f"cannot stat fixture evidence for {name}") from exc
    if newer_evidence:
        first = sorted(newer_evidence)[0]
        raise PatchExecutorError(
            f"stale fig_loop run: fixture evidence is newer than checkpoint: {first}"
        )
    if newer_allowed_scope:
        first = sorted(newer_allowed_scope)[0]
        raise PatchExecutorError(
            f"stale fig_loop run: allowed_edit_scope evidence is newer than checkpoint: {first}"
        )


def _validate_no_pending_patch_closeout(name: str, loop_run: LatestLoopRun) -> None:
    for evidence_path in sorted(loop_run.run_dir.glob("patch_apply_*.json")):
        evidence = _read_json(evidence_path)
        evidence_fixture = evidence.get("fixture")
        if isinstance(evidence_fixture, str) and evidence_fixture != name:
            raise PatchExecutorError(
                f"patch apply evidence fixture mismatch in {evidence_path}: "
                f"{evidence_fixture} != {name}"
            )
        if evidence.get("closeout_required") is True:
            raise PatchExecutorError(f"pending patch closeout: {evidence_path}")


def _validate_loop_state(loop_run: LatestLoopRun) -> tuple[dict[str, Any], dict[str, Any]]:
    patch_handoff = loop_run.iteration.get("patch_handoff")
    if not isinstance(patch_handoff, dict):
        raise PatchExecutorError("latest fig_loop record has no patch_handoff")
    if patch_handoff.get("target_type") != "finding":
        raise PatchExecutorError("patch executor requires a single finding target")
    auto_patch_eligibility = loop_run.iteration.get("auto_patch_eligibility")
    if not isinstance(auto_patch_eligibility, dict):
        raise PatchExecutorError("latest fig_loop record has no auto_patch_eligibility")
    if auto_patch_eligibility.get("level") != "auto_patch_candidate":
        raise PatchExecutorError("latest target is not an auto_patch_candidate")
    blocked_reasons = auto_patch_eligibility.get("blocked_reasons")
    if blocked_reasons:
        raise PatchExecutorError("auto_patch_eligibility has blocked_reasons")
    allowed_reasons = auto_patch_eligibility.get("allowed_reasons")
    if not isinstance(allowed_reasons, list) or not allowed_reasons:
        raise PatchExecutorError("auto_patch_eligibility must include allowed_reasons")
    target_id = patch_handoff.get("target_id")
    if not isinstance(target_id, str) or not target_id:
        raise PatchExecutorError("patch_handoff must contain one target_id")
    if auto_patch_eligibility.get("target_id") != target_id:
        raise PatchExecutorError("auto_patch_eligibility target_id does not match patch_handoff")
    adjudication = loop_run.iteration.get("adjudication")
    if not isinstance(adjudication, dict) or adjudication.get("state") != "fresh":
        raise PatchExecutorError("patch executor requires fresh adjudication")
    decisions = adjudication.get("decisions")
    if not isinstance(decisions, list):
        raise PatchExecutorError("adjudication decisions must be a list")
    apply_decisions = [
        decision
        for decision in decisions
        if isinstance(decision, dict) and decision.get("decision") == "apply"
    ]
    if len(apply_decisions) != 1 or apply_decisions[0].get("finding_id") != target_id:
        raise PatchExecutorError("patch executor requires a single apply decision for target_id")
    return patch_handoff, auto_patch_eligibility


def _diff_path(value: str) -> str | None:
    path = value.split("\t", 1)[0].strip()
    if path == "/dev/null":
        return None
    return path


def _normalized_header_pair(
    old_path: str | None,
    new_path: str | None,
) -> tuple[str | None, str | None]:
    old_uses_git_prefix = old_path is None or (
        isinstance(old_path, str) and old_path.startswith("a/")
    )
    new_uses_git_prefix = new_path is None or (
        isinstance(new_path, str) and new_path.startswith("b/")
    )
    if old_uses_git_prefix and new_uses_git_prefix:
        normalized_old = old_path[2:] if isinstance(old_path, str) else None
        normalized_new = new_path[2:] if isinstance(new_path, str) else None
        return normalized_old, normalized_new
    return old_path, new_path


def changed_paths_from_unified_diff(patch_path: Path) -> list[str]:
    try:
        lines = patch_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise PatchExecutorError(f"cannot read patch file: {patch_path}") from exc
    old_paths: list[str] = []
    new_paths: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        if line.startswith("--- ") and next_line.startswith("+++ "):
            old_path, new_path = _normalized_header_pair(
                _diff_path(line[4:]),
                _diff_path(next_line[4:]),
            )
            if old_path:
                old_paths.append(old_path)
            if new_path:
                new_paths.append(new_path)
            index += 2
            continue
        index += 1
    paths = sorted(set(old_paths + new_paths))
    if not paths:
        raise PatchExecutorError("patch file must be a unified diff with file headers")
    return paths


def _patch_strip_level(patch_path: Path) -> int:
    try:
        lines = patch_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise PatchExecutorError(f"cannot read patch file: {patch_path}") from exc
    index = 0
    while index < len(lines):
        line = lines[index]
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        if line.startswith("--- ") and next_line.startswith("+++ "):
            old_path = _diff_path(line[4:])
            new_path = _diff_path(next_line[4:])
            if (
                (isinstance(old_path, str) and old_path.startswith("a/"))
                or (isinstance(new_path, str) and new_path.startswith("b/"))
            ):
                return 1
            return 0
        index += 1
    return 0


def _is_forbidden_path(rel_path: str) -> bool:
    normalized = f"/{rel_path.strip('/')}"
    return any(part in normalized for part in FORBIDDEN_PATH_PARTS)


def _is_safe_repo_relative_path(rel_path: str) -> bool:
    path = Path(rel_path)
    return not path.is_absolute() and ".." not in path.parts


def _validate_patch_scope(paths: list[str], patch_handoff: dict[str, Any]) -> str:
    if len(paths) != 1:
        raise PatchExecutorError("patch executor requires exactly one changed path")
    rel_path = paths[0]
    if not _is_safe_repo_relative_path(rel_path):
        raise PatchExecutorError(f"patch path must be repo-relative: {rel_path}")
    if _is_forbidden_path(rel_path):
        raise PatchExecutorError(f"patch touches forbidden path: {rel_path}")
    allowed = patch_handoff.get("allowed_edit_scope")
    if not isinstance(allowed, list) or not all(isinstance(item, str) for item in allowed):
        raise PatchExecutorError("patch_handoff.allowed_edit_scope must be a string list")
    unsafe_allowed = [item for item in allowed if not _is_safe_repo_relative_path(item)]
    if unsafe_allowed:
        raise PatchExecutorError(
            f"patch_handoff.allowed_edit_scope must contain repo-relative paths: {unsafe_allowed}"
        )
    if rel_path not in allowed:
        raise PatchExecutorError(f"patch path is outside allowed_edit_scope: {rel_path}")
    return rel_path


def _allowed_scope_evidence(repo_root: Path, patch_handoff: dict[str, Any]) -> list[dict[str, Any]]:
    allowed = patch_handoff.get("allowed_edit_scope")
    if not isinstance(allowed, list):
        return []
    return [path_evidence(repo_root, rel_path) for rel_path in allowed if isinstance(rel_path, str)]


def _run_patch(repo_root: Path, patch_path: Path, *, dry_run: bool, strip_level: int) -> None:
    command = [
        "/usr/bin/patch",
        "--forward",
        "--batch",
        f"--strip={strip_level}",
        "--input",
        str(patch_path),
    ]
    if dry_run:
        command.insert(1, "--dry-run")
    result = subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise PatchExecutorError(f"patch command failed: {detail}")


def _next_evidence_path(run_dir: Path) -> Path:
    for index in range(1, 1000):
        candidate = run_dir / f"patch_apply_{index:03d}.json"
        if not candidate.exists():
            return candidate
    raise PatchExecutorError(f"too many patch_apply records in {run_dir}")


def apply_patch_file(
    name: str,
    *,
    repo_root: Path,
    runs_root: Path,
    patch_path: Path,
    apply: bool,
) -> dict[str, Any]:
    if not apply:
        raise PatchExecutorError("explicit --apply is required before mutation")
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise PatchExecutorError(str(exc)) from exc
    loop_run = _latest_loop_run(name, runs_root)
    patch_handoff, _auto_patch_eligibility = _validate_loop_state(loop_run)
    _validate_loop_run_currentness(name, repo_root, loop_run, patch_handoff)
    _validate_no_pending_patch_closeout(name, loop_run)
    changed_paths = changed_paths_from_unified_diff(patch_path)
    changed_path = _validate_patch_scope(changed_paths, patch_handoff)
    pre_patch = _allowed_scope_evidence(repo_root, patch_handoff)
    strip_level = _patch_strip_level(patch_path)
    _run_patch(repo_root, patch_path, dry_run=True, strip_level=strip_level)
    _run_patch(repo_root, patch_path, dry_run=False, strip_level=strip_level)
    post_patch = _allowed_scope_evidence(repo_root, patch_handoff)

    report = {
        "schema": PATCH_APPLY_SCHEMA,
        "fixture": name,
        "target_type": patch_handoff.get("target_type"),
        "target_id": patch_handoff.get("target_id"),
        "changed_paths": [changed_path],
        "pre_patch": {"allowed_edit_scope": pre_patch},
        "post_patch": {"allowed_edit_scope": post_patch},
        "rollback_reference": {
            "restore_strategy": (
                "restore allowed_edit_scope paths to the recorded pre_patch sha256 values"
            ),
            "pre_patch": {"allowed_edit_scope": pre_patch},
        },
        "closeout_required": True,
        "next_action": f"/fig_closeout {name}",
    }
    evidence_path = _next_evidence_path(loop_run.run_dir)
    evidence_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="fixture name")
    parser.add_argument("--patch-file", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / ".scratch" / "fig-loop-runs",
    )
    parser.add_argument("--apply", action="store_true", help="required opt-in to mutate files")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args(argv)

    try:
        report = apply_patch_file(
            args.name,
            repo_root=args.repo_root,
            runs_root=args.runs_root,
            patch_path=args.patch_file,
            apply=args.apply,
        )
    except PatchExecutorError as exc:
        print(f"fig_loop_patch_executor.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
