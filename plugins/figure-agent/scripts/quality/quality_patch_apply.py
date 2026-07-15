"""Apply and verify explicit quality patch plans."""

from __future__ import annotations

import argparse
import difflib
import json
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Any

import human_decision_record
import quality_patch_plan
import repair_transaction
from quality_manifest import file_sha256

SCHEMA = "figure-agent.quality-patch-result.v1"
PLAN_SCHEMA = "figure-agent.quality-patch-plan.v1"
SOURCE_MUTATION_DECISION_KIND = "apply_quality_patch_plan"


class QualityPatchApplyError(ValueError):
    """Expected user-facing error for quality patch apply failures."""


def authorization_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + sha256(encoded).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    repair_transaction.atomic_write_text(path, text)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    repair_transaction.atomic_write_json(path, payload)


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
    if target.is_symlink():
        raise QualityPatchApplyError("plan_target_forbidden: source symlink forbidden")
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
    required_selector_fields = (
        "selector_id",
        "anchor_start",
        "anchor_end",
        "source_hash",
    )
    if (
        not isinstance(selector, dict)
        or selector.get("kind") != "semantic_anchor"
        or any(not selector.get(field) for field in required_selector_fields)
    ):
        raise QualityPatchApplyError("exact_selector_required")
    guard = operation.get("semantic_guard")
    if (
        not isinstance(guard, dict)
        or guard.get("allowed") is not False
        or guard.get("state") != "pending_post_render_verification"
    ):
        raise QualityPatchApplyError("unsafe_patch: semantic guard contract invalid")
    return operation


def _check_source_hash(plan: dict[str, Any], target_rel: str, target: Path) -> None:
    expected = ((plan.get("created_from") or {}).get("source_hashes") or {}).get(target_rel)
    if not isinstance(expected, str):
        raise QualityPatchApplyError("invalid_plan: missing source hash")
    if file_sha256(target) != expected:
        raise QualityPatchApplyError("source_hash_mismatch: source changed since plan")


@contextmanager
def _mutation_lock(fixture: Path) -> Any:
    try:
        with repair_transaction.exclusive_lock(
            fixture / "build" / ".quality-locks" / "mutation.lock",
            owner="quality_patch_apply",
        ):
            yield
    except repair_transaction.RepairTransactionError as exc:
        raise QualityPatchApplyError("operation_in_progress: mutation lock exists") from exc


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


def _candidate_text(target_rel: str, original: str, patch_text: str) -> str:
    with tempfile.TemporaryDirectory(prefix="figure-agent-patch-") as temp_dir:
        root = Path(temp_dir)
        candidate = root / target_rel
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text(original, encoding="utf-8")
        _run_patch(root, patch_text, dry_run=False)
        return candidate.read_text(encoding="utf-8")


def _anchor_bounds(text: str, selector: dict[str, Any]) -> tuple[int, int]:
    start_marker = str(selector["anchor_start"])
    end_marker = str(selector["anchor_end"])
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line == start_marker]
    ends = [index for index, line in enumerate(lines) if line == end_marker]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise QualityPatchApplyError("exact_selector_required")
    return starts[0], ends[0]


def _changed_line_count(patch_text: str) -> int:
    return sum(
        line.startswith(("+", "-"))
        and not line.startswith(("+++", "---"))
        for line in patch_text.splitlines()
    )


def _preflight_candidate(
    operation: dict[str, Any],
    target_rel: str,
    target: Path,
    patch_text: str,
) -> str:
    selector = operation["selector"]
    if file_sha256(target) != selector["source_hash"]:
        raise QualityPatchApplyError("source_hash_mismatch: selector source changed")
    original = target.read_text(encoding="utf-8")
    start, end = _anchor_bounds(original, selector)

    budget = operation.get("change_budget")
    max_changed_lines = budget.get("max_changed_lines") if isinstance(budget, dict) else None
    max_source_blocks = budget.get("max_source_blocks") if isinstance(budget, dict) else None
    old_headers = [
        line.removeprefix("--- ").split("\t", 1)[0]
        for line in patch_text.splitlines()
        if line.startswith("--- ")
    ]
    new_headers = [
        line.removeprefix("+++ ").split("\t", 1)[0]
        for line in patch_text.splitlines()
        if line.startswith("+++ ")
    ]
    if (
        not isinstance(max_changed_lines, int)
        or max_changed_lines < 1
        or not isinstance(max_source_blocks, int)
        or max_source_blocks != 1
        or len(old_headers) != 1
        or len(new_headers) != 1
        or _changed_line_count(patch_text) > max_changed_lines
    ):
        raise QualityPatchApplyError("change_budget_exceeded")
    if old_headers[0] != target_rel or new_headers[0] != target_rel:
        raise QualityPatchApplyError("patch_outside_anchor")

    candidate = _candidate_text(target_rel, original, patch_text)
    try:
        _anchor_bounds(candidate, selector)
    except QualityPatchApplyError as exc:
        raise QualityPatchApplyError("patch_outside_anchor") from exc
    original_lines = original.splitlines()
    candidate_lines = candidate.splitlines()
    matcher = difflib.SequenceMatcher(a=original_lines, b=candidate_lines, autojunk=False)
    for tag, old_start, old_end, _new_start, _new_end in matcher.get_opcodes():
        if tag == "equal":
            continue
        if old_start == old_end:
            inside = start < old_start <= end
        else:
            inside = start < old_start and old_end <= end
        if not inside:
            raise QualityPatchApplyError("patch_outside_anchor")

    invariants = operation.get("protected_invariants")
    if not isinstance(invariants, list) or not invariants:
        raise QualityPatchApplyError("protected_invariants_required")
    for token in invariants:
        if not isinstance(token, str) or not token:
            raise QualityPatchApplyError("protected_invariants_required")
        if original.count(token) != candidate.count(token):
            raise QualityPatchApplyError("protected_invariant_changed")
    return candidate


def _write_rollback_patch(
    fixture: Path,
    plan_id: str,
    target_rel: str,
    original: str,
    candidate: str,
) -> Path:
    rollback_dir = fixture / "build" / "quality" / "rollback"
    rollback_dir.mkdir(parents=True, exist_ok=True)
    safe_id = plan_id.replace("sha256:", "")[:16]
    path = rollback_dir / f"{safe_id}.patch"
    diff_lines = difflib.unified_diff(
        candidate.splitlines(keepends=True),
        original.splitlines(keepends=True),
        fromfile=target_rel,
        tofile=target_rel,
    )
    rollback_lines: list[str] = []
    for line in diff_lines:
        if line.endswith("\n"):
            rollback_lines.append(line)
            continue
        rollback_lines.append(line + "\n")
        if line.startswith(("+", "-", " ")):
            rollback_lines.append("\\ No newline at end of file\n")
    rollback_text = "".join(rollback_lines)
    path.write_text(rollback_text, encoding="utf-8")
    return path


def apply_quality_patch_plan(
    name: str,
    *,
    plan_path: Path,
    workspace_root: Path,
    source_mutation_decision: dict[str, Any] | None = None,
    apply: bool,
) -> dict[str, Any]:
    fixture = _fixture_root(workspace_root, name)
    _validate_plan_path(plan_path, fixture)
    plan = _read_plan(plan_path)
    if plan.get("fixture") != name:
        raise QualityPatchApplyError("invalid_plan: fixture mismatch")
    if plan.get("plan_id") != quality_patch_plan.compute_plan_id(plan):
        raise QualityPatchApplyError("invalid_plan: plan_id_mismatch")
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
        "publication_acceptance": "not_claimed",
        "post_render_verification": "pending",
        "authorization": None,
        "recovery_required": False,
        "rollback_patch": "",
        "verification_commands": [
            {"command": command, "returncode": None}
            for command in (plan.get("verification") or {}).get("required_commands", [])
        ],
    }
    if not apply:
        _preflight_candidate(operation, target_rel, target, patch_text)
        return result
    if not isinstance(source_mutation_decision, dict):
        raise QualityPatchApplyError("source_mutation_decision_missing")
    try:
        authorization = human_decision_record.validate_source_mutation_authorization(
            source_mutation_decision,
            fixture=name,
            decision_kind=SOURCE_MUTATION_DECISION_KIND,
            candidate_id=str(plan.get("plan_id") or ""),
            candidate_hash=str(plan.get("plan_id") or ""),
            packet_schema=PLAN_SCHEMA,
            packet_recommendation=SOURCE_MUTATION_DECISION_KIND,
            packet_path=plan_path.resolve().relative_to(fixture.resolve()).as_posix(),
        )
    except human_decision_record.HumanDecisionRecordError as exc:
        raise QualityPatchApplyError(f"source_mutation_decision_invalid:{exc}") from exc
    result["authorization"] = {
        "decision_kind": authorization["decision_kind"],
        "record_hash": authorization_record_hash(source_mutation_decision),
        "authorized_candidate_id": authorization["authorized_candidate_id"],
        "authorized_candidate_hash": authorization["authorized_candidate_hash"],
    }

    with _mutation_lock(fixture):
        _check_source_hash(plan, target_rel, target)
        candidate = _preflight_candidate(operation, target_rel, target, patch_text)
        original = target.read_text(encoding="utf-8")
        rollback = _write_rollback_patch(
            fixture,
            str(plan.get("plan_id")),
            target_rel,
            original,
            candidate,
        )
        result["rollback_patch"] = rollback.relative_to(workspace_root).as_posix()
        output = fixture / "build" / "quality" / "patch_result.json"
        result["outcome"] = "mutation_prepared"
        result["recovery_required"] = True
        _atomic_write_json(output, result)
        _atomic_write_text(target, candidate)
        result["applied"] = True
        result["outcome"] = "verification_pending"
        result["recovery_required"] = False
        _atomic_write_json(output, result)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json",), default=None)
    args = parser.parse_args(argv)
    source_mutation_decision = None
    if args.authorization:
        try:
            source_mutation_decision = json.loads(
                args.authorization.read_text(encoding="utf-8")
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            print(f"quality_patch_apply.py: authorization_invalid:{exc}", file=sys.stderr)
            return 1
    try:
        payload = apply_quality_patch_plan(
            args.name,
            plan_path=args.workspace_root / "examples" / args.name / args.plan,
            workspace_root=args.workspace_root,
            source_mutation_decision=source_mutation_decision,
            apply=args.apply,
        )
    except QualityPatchApplyError as exc:
        print(f"quality_patch_apply.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
