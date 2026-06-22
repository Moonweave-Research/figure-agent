"""Apply and verify explicit quality patch plans."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from quality_manifest import file_sha256

SCHEMA = "figure-agent.quality-patch-result.v1"
PLAN_SCHEMA = "figure-agent.quality-patch-plan.v1"


class QualityPatchApplyError(ValueError):
    """Expected user-facing error for quality patch apply failures."""


def _read_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QualityPatchApplyError("invalid_plan: cannot read plan") from exc
    if not isinstance(payload, dict) or payload.get("schema") != PLAN_SCHEMA:
        raise QualityPatchApplyError(f"invalid_plan: schema must be {PLAN_SCHEMA}")
    return payload


def _fixture_root(workspace_root: Path, name: str) -> Path:
    return workspace_root / "examples" / name


def _validate_plan_path(plan_path: Path, fixture: Path) -> None:
    try:
        resolved = plan_path.resolve(strict=True)
        resolved.relative_to(fixture.resolve())
    except (OSError, ValueError) as exc:
        raise QualityPatchApplyError("invalid_plan: plan must stay inside fixture") from exc


def _validate_target(path_text: str, workspace_root: Path, fixture: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts:
        raise QualityPatchApplyError("plan_target_forbidden: target path escapes workspace")
    if len(path.parts) < 3 or path.parts[0] != "examples" or path.parts[1] != fixture.name:
        raise QualityPatchApplyError("plan_target_forbidden: target must be fixture-local")
    if any(part in {"build", "exports"} for part in path.parts):
        raise QualityPatchApplyError("plan_target_forbidden: build/export targets forbidden")
    if path.name in {"critique.md", "QUALITY_AUDIT.md"}:
        raise QualityPatchApplyError("plan_target_forbidden: protected target")
    target = workspace_root / path
    try:
        resolved = target.resolve(strict=True)
        resolved.relative_to(fixture.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise QualityPatchApplyError("plan_target_forbidden: target escapes fixture") from exc
    return target


def _operation(plan: dict[str, Any]) -> dict[str, Any]:
    operations = plan.get("operations")
    if not isinstance(operations, list) or len(operations) != 1:
        raise QualityPatchApplyError("invalid_plan: exactly one operation is required")
    operation = operations[0]
    if not isinstance(operation, dict):
        raise QualityPatchApplyError("invalid_plan: operation must be a mapping")
    selector = operation.get("selector")
    if isinstance(selector, dict) and selector.get("confidence") == "ambiguous":
        raise QualityPatchApplyError("selector_ambiguous: ambiguous selector blocks apply")
    guard = operation.get("semantic_guard")
    if not isinstance(guard, dict) or guard.get("allowed") is not True:
        raise QualityPatchApplyError("unsafe_patch: semantic guard is not allowed")
    return operation


def _check_source_hash(plan: dict[str, Any], target_rel: str, target: Path) -> None:
    expected = ((plan.get("created_from") or {}).get("source_hashes") or {}).get(target_rel)
    if not isinstance(expected, str):
        raise QualityPatchApplyError("invalid_plan: missing source hash")
    if file_sha256(target) != expected:
        raise QualityPatchApplyError("source_hash_mismatch: source changed since plan")


@contextmanager
def _mutation_lock(fixture: Path) -> Any:
    lock_root = fixture / "build" / ".quality-locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    lock_path = lock_root / "mutation.lock"
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise QualityPatchApplyError("operation_in_progress: mutation lock exists") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("quality_patch_apply\n")
        yield
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _run_patch(
    workspace_root: Path,
    patch_text: str,
    *,
    dry_run: bool,
    reverse: bool = False,
) -> None:
    command = ["/usr/bin/patch", "--forward", "--batch", "--strip=0"]
    if dry_run:
        command.insert(1, "--dry-run")
    if reverse:
        command.append("--reverse")
    result = subprocess.run(
        command,
        cwd=workspace_root,
        input=patch_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise QualityPatchApplyError(f"unsafe_patch: patch command failed: {detail}")


def _write_rollback_patch(fixture: Path, plan_id: str, patch_text: str) -> Path:
    rollback_dir = fixture / "build" / "quality" / "rollback"
    rollback_dir.mkdir(parents=True, exist_ok=True)
    safe_id = plan_id.replace("sha256:", "")[:16]
    path = rollback_dir / f"{safe_id}.patch"
    lines = patch_text.splitlines(keepends=True)
    reversed_lines: list[str] = []
    for line in lines:
        if line.startswith("--- "):
            reversed_lines.append(line.replace("--- ", "+++ ", 1))
        elif line.startswith("+++ "):
            reversed_lines.append(line.replace("+++ ", "--- ", 1))
        elif line.startswith("-") and not line.startswith("--- "):
            reversed_lines.append("+" + line[1:])
        elif line.startswith("+") and not line.startswith("+++ "):
            reversed_lines.append("-" + line[1:])
        else:
            reversed_lines.append(line)
    path.write_text("".join(reversed_lines), encoding="utf-8")
    return path


def apply_quality_patch_plan(
    name: str,
    *,
    plan_path: Path,
    workspace_root: Path,
    apply: bool,
) -> dict[str, Any]:
    fixture = _fixture_root(workspace_root, name)
    _validate_plan_path(plan_path, fixture)
    plan = _read_plan(plan_path)
    if plan.get("fixture") != name:
        raise QualityPatchApplyError("invalid_plan: fixture mismatch")
    operation = _operation(plan)
    target_rel = str(operation.get("file") or "")
    target = _validate_target(target_rel, workspace_root, fixture)
    _check_source_hash(plan, target_rel, target)
    patch_text = ((operation.get("proposed_change") or {}).get("patch") or "")
    if not isinstance(patch_text, str) or not patch_text.strip():
        raise QualityPatchApplyError("invalid_plan: missing patch text")

    result = {
        "schema": SCHEMA,
        "fixture": name,
        "plan_id": plan.get("plan_id"),
        "applied": False,
        "changed_files": [target_rel],
        "outcome": "unchanged",
        "rollback_patch": "",
        "verification_commands": [
            {"command": command, "returncode": None}
            for command in (plan.get("verification") or {}).get("required_commands", [])
        ],
    }
    if not apply:
        _run_patch(workspace_root, patch_text, dry_run=True)
        return result

    with _mutation_lock(fixture):
        _run_patch(workspace_root, patch_text, dry_run=True)
        _run_patch(workspace_root, patch_text, dry_run=False)
        rollback = _write_rollback_patch(fixture, str(plan.get("plan_id")), patch_text)
        result["applied"] = True
        result["outcome"] = "verification_failed"
        result["rollback_patch"] = rollback.relative_to(workspace_root).as_posix()
        output = fixture / "build" / "quality" / "patch_result.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json",), default=None)
    args = parser.parse_args(argv)
    try:
        payload = apply_quality_patch_plan(
            args.name,
            plan_path=args.workspace_root / "examples" / args.name / args.plan,
            workspace_root=args.workspace_root,
            apply=args.apply,
        )
    except QualityPatchApplyError as exc:
        print(f"quality_patch_apply.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
