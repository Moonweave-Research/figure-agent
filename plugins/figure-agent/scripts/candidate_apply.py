"""Evidence-gated candidate source apply."""

from __future__ import annotations

import difflib
import json
import os
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Any

import candidate_contracts
import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.candidate-apply-result.v1"


class CandidateApplyError(ValueError):
    """Raised when candidate apply would escape the fixture boundary."""


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _diagnostic(code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"code": code, "message": message}
    if path is not None:
        payload["path"] = path
    return payload


def _blocked(name: str, candidate_id: str, diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "figure_name": name,
        "candidate_id": candidate_id,
        "status": "blocked",
        "changed_files": [],
        "rollback_patch": None,
        "post_apply": {},
        "diagnostics": diagnostics,
    }


def _candidate_id(manifest: dict[str, Any]) -> str:
    candidate_id = str(manifest.get("candidate_id") or "")
    fixture_identity.validate_fixture_name(candidate_id)
    return candidate_id


def _candidate_sandbox(example_dir: Path, candidate_id: str) -> Path:
    build_dir = example_dir / "build"
    root = build_dir / "candidates"
    sandbox = root / candidate_id
    for label, path in (("build", build_dir), ("candidates", root), (candidate_id, sandbox)):
        if path.is_symlink():
            raise CandidateApplyError(f"sandbox_symlink_forbidden: {label}")
    try:
        sandbox.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise CandidateApplyError("candidate path_escape") from exc
    return sandbox


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise CandidateApplyError(f"sandbox_symlink_forbidden: {path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CandidateApplyError(f"{label}_missing") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateApplyError(f"{label}_unreadable") from exc
    if not isinstance(payload, dict):
        raise CandidateApplyError(f"{label}_invalid")
    return payload


def _fixture_relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError as exc:
        raise CandidateApplyError("path_escape") from exc


def _operation_path(example_dir: Path, fixture_name: str, operation: dict[str, Any]) -> Path:
    value = operation.get("path")
    if not isinstance(value, str) or not value.strip():
        raise CandidateApplyError("operation_path_missing")
    path = Path(value)
    if path.parts[:2] == ("examples", fixture_name):
        path = Path(*path.parts[2:])
    target = example_dir / path
    if target.is_symlink():
        raise CandidateApplyError("source_symlink_forbidden")
    try:
        target.resolve().relative_to(example_dir.resolve())
    except ValueError as exc:
        raise CandidateApplyError("source_path_escape") from exc
    return target


def _drift_hash_for_operation(operation: dict[str, Any], selectors: Any) -> str | None:
    direct = operation.get("source_sha256")
    if isinstance(direct, str) and direct.startswith("sha256:"):
        return direct
    path = operation.get("path")
    if not isinstance(selectors, list):
        return None
    matches = [
        selector
        for selector in selectors
        if isinstance(selector, dict)
        and selector.get("kind") == "tex_selector.v1"
        and selector.get("path") == path
        and isinstance(selector.get("source_hash"), str)
    ]
    if len(matches) == 1:
        return str(matches[0]["source_hash"])
    return None


def _render_gate_failures(render_manifest: dict[str, Any]) -> list[str]:
    stages = (
        render_manifest.get("stages")
        if isinstance(render_manifest.get("stages"), dict)
        else {}
    )
    required = {
        "compile": "success",
        "export": "success",
        "crop": "success",
        "evaluate": "rendered_needs_human_review",
    }
    failures: list[str] = []
    for stage, expected in required.items():
        value = stages.get(stage)
        status = value.get("status") if isinstance(value, dict) else None
        if status != expected:
            failures.append(f"{stage}:{status or 'missing'}")
    return failures


def _active_mutation_lock(example_dir: Path) -> Path | None:
    for relative in (Path("build") / ".quality-locks" / "mutation.lock",):
        lock = example_dir / relative
        if lock.exists():
            return lock
    return None


@contextmanager
def _candidate_apply_lock(example_dir: Path) -> Iterator[Path | None]:
    lock_dir = example_dir / "build" / ".mcp-locks"
    if lock_dir.is_symlink():
        raise CandidateApplyError("sandbox_symlink_forbidden: .mcp-locks")
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "mutation.lock"
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        yield lock_path
        return
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write('{"operation":"apply_candidate"}\n')
        yield None
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _acceptance_hash_diagnostics(
    *,
    acceptance: dict[str, Any],
    candidate_id: str,
    manifest_path: Path,
    render_manifest_path: Path,
    manifest: dict[str, Any],
    render_manifest: dict[str, Any],
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    if acceptance.get("decision") != "accept":
        diagnostics.append(
            _diagnostic("acceptance_not_accepted", "acceptance decision is not accept")
        )
    if acceptance.get("candidate_id") != candidate_id:
        diagnostics.append(_diagnostic("candidate_id_mismatch", "acceptance candidate mismatch"))
    if acceptance.get("candidate_hash") != manifest.get("candidate_hash"):
        diagnostics.append(
            _diagnostic("candidate_hash_mismatch", "acceptance candidate hash mismatch")
        )
    if manifest.get("candidate_hash") != render_manifest.get("candidate_hash"):
        diagnostics.append(
            _diagnostic("render_candidate_hash_mismatch", "render candidate hash mismatch")
        )
    if acceptance.get("candidate_manifest_sha256") != _sha256_file(manifest_path):
        diagnostics.append(
            _diagnostic(
                "candidate_manifest_hash_mismatch",
                "candidate manifest hash mismatch",
            )
        )
    if acceptance.get("render_manifest_sha256") != _sha256_file(render_manifest_path):
        diagnostics.append(
            _diagnostic("render_manifest_hash_mismatch", "render manifest hash mismatch")
        )
    return diagnostics


def _build_changes(
    *,
    example_dir: Path,
    fixture_name: str,
    manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    operations = manifest.get("operations")
    if not isinstance(operations, list):
        return [], [_diagnostic("operations_missing", "candidate operations are missing")]
    if not operations:
        return [], [_diagnostic("operations_empty", "candidate operations are empty")]
    diagnostics: list[dict[str, str]] = []
    by_path: dict[Path, dict[str, Any]] = {}
    for operation in operations:
        if not isinstance(operation, dict) or operation.get("kind") != "replace_text":
            diagnostics.append(
                _diagnostic("unsupported_operation", "only replace_text is supported")
            )
            continue
        target = _operation_path(example_dir, fixture_name, operation)
        relative = target.relative_to(example_dir).as_posix()
        drift_hash = _drift_hash_for_operation(operation, manifest.get("selectors"))
        if drift_hash is None:
            diagnostics.append(
                _diagnostic("source_drift_hash_missing", "source drift hash missing", relative)
            )
            continue
        if _sha256_file(target) != drift_hash:
            diagnostics.append(
                _diagnostic("source_drift_hash_mismatch", "source drift hash mismatch", relative)
            )
            continue
        text = target.read_text(encoding="utf-8")
        original = str(operation.get("original", ""))
        replacement = str(operation.get("replacement", ""))
        if text.count(original) != 1:
            diagnostics.append(
                _diagnostic(
                    "original_text_count",
                    "original text must appear exactly once",
                    relative,
                )
            )
            continue
        entry = by_path.setdefault(
            target,
            {
                "path": target,
                "relative": relative,
                "before": text,
                "after": text,
            },
        )
        entry["after"] = str(entry["after"]).replace(original, replacement, 1)
    return list(by_path.values()), diagnostics


def _rollback_patch(changes: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for change in changes:
        relative = str(change["relative"])
        chunks.extend(
            difflib.unified_diff(
                str(change["after"]).splitlines(keepends=True),
                str(change["before"]).splitlines(keepends=True),
                fromfile=f"a/{relative}",
                tofile=f"b/{relative}",
            )
        )
    return "".join(chunks)


def _output_tail(text: str, limit: int = 1200) -> str:
    return text[-limit:] if len(text) > limit else text


def _post_apply_checks(name: str, paths: runtime_paths.RuntimePaths) -> dict[str, dict[str, Any]]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(paths.plugin_root)
    env["FIGURE_AGENT_WORKSPACE"] = str(paths.workspace_root)
    commands = {
        "compile": [
            "bash",
            str(paths.scripts_dir / "compile.sh"),
            str(paths.examples_dir / name / f"{name}.tex"),
        ],
        "export": [
            sys.executable,
            str(paths.scripts_dir / "run_export.py"),
            name,
            "--force-golden",
            "--skip-critique",
        ],
        "status": [
            sys.executable,
            str(paths.scripts_dir / "status.py"),
            name,
            "--json",
        ],
    }
    checks: dict[str, dict[str, Any]] = {}
    for stage, command in commands.items():
        completed = subprocess.run(
            command,
            cwd=paths.workspace_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        checks[stage] = {
            "status": "success" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "stdout_tail": _output_tail(completed.stdout),
            "stderr_tail": _output_tail(completed.stderr),
        }
    return checks


def apply_candidate(
    name: str,
    manifest: dict[str, Any],
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    candidate_set_path: Path | None = None,
    acceptance_path: Path | None = None,
    apply: bool = False,
    post_apply: bool = True,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    candidate_id = _candidate_id(manifest)
    sandbox = _candidate_sandbox(example_dir, candidate_id)
    candidate_manifest_path = sandbox / "candidate_manifest.json"
    manifest = _load_json(candidate_manifest_path, "candidate_manifest")
    if _candidate_id(manifest) != candidate_id:
        return _blocked(
            name,
            candidate_id,
            [_diagnostic("candidate_id_mismatch", "candidate manifest id mismatch")],
        )
    diagnostics: list[dict[str, str]] = []
    candidate_set_path = candidate_set_path or Path(str(manifest.get("candidate_set_path", "")))
    acceptance_path = acceptance_path or Path(f"build/candidates/{candidate_id}/acceptance.json")

    candidate_set_file = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        candidate_set_path.as_posix(),
    )
    candidate_set = _load_json(candidate_set_file, "candidate_set")
    candidate = None
    for item in candidate_set.get("candidates", []):
        if isinstance(item, dict) and item.get("id") == candidate_id:
            candidate = item
            break
    if candidate is None:
        diagnostics.append(_diagnostic("candidate_set_missing_candidate", "candidate not in set"))
    elif candidate.get("candidate_hash") != manifest.get("candidate_hash"):
        diagnostics.append(_diagnostic("candidate_hash_mismatch", "candidate hash mismatch"))

    render_manifest_path = sandbox / "render_manifest.json"
    render_manifest = _load_json(render_manifest_path, "render_manifest")
    for failure in _render_gate_failures(render_manifest):
        diagnostics.append(_diagnostic("render_gate_failed", failure))

    resolved_acceptance_path = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        acceptance_path.as_posix(),
    )
    try:
        resolved_acceptance_path.resolve().relative_to(sandbox.resolve())
    except ValueError:
        diagnostics.append(_diagnostic("acceptance_path_escape", "acceptance path escapes sandbox"))
    if not resolved_acceptance_path.is_file():
        diagnostics.append(_diagnostic("acceptance_missing", "acceptance artifact missing"))
    else:
        acceptance = _load_json(resolved_acceptance_path, "acceptance")
        diagnostics.extend(
            _acceptance_hash_diagnostics(
                acceptance=acceptance,
                candidate_id=candidate_id,
                manifest_path=candidate_manifest_path,
                render_manifest_path=render_manifest_path,
                manifest=manifest,
                render_manifest=render_manifest,
            )
        )

    apply_result_path = sandbox / "apply_result.json"
    if apply_result_path.is_file():
        apply_result = _load_json(apply_result_path, "apply_result")
        if apply_result.get("status") in {"applied", "applied_with_failed_verification"}:
            diagnostics.append(_diagnostic("already_applied", "candidate is already applied"))

    active_lock = _active_mutation_lock(example_dir)
    if active_lock is not None:
        diagnostics.append(
            _diagnostic(
                "mutation_lock_active",
                "another mutation lock is active",
                _fixture_relative(example_dir, active_lock),
            )
        )

    changes, change_diagnostics = _build_changes(
        example_dir=example_dir,
        fixture_name=name,
        manifest=manifest,
    )
    diagnostics.extend(change_diagnostics)
    if diagnostics:
        return _blocked(name, candidate_id, diagnostics)
    if not apply:
        return {
            "schema": SCHEMA,
            "figure_name": name,
            "candidate_id": candidate_id,
            "status": "ready",
            "changed_files": [],
            "rollback_patch": None,
            "post_apply": {},
            "diagnostics": [],
        }

    with _candidate_apply_lock(example_dir) as lock:
        if lock is not None:
            return _blocked(
                name,
                candidate_id,
                [_diagnostic("mutation_lock_active", "candidate apply lock is active")],
            )
        rollback_path = sandbox / "rollback.patch"
        if rollback_path.is_symlink():
            raise CandidateApplyError("sandbox_symlink_forbidden: rollback.patch")
        rollback_path.write_text(_rollback_patch(changes), encoding="utf-8")
        changed_files: list[dict[str, str]] = []
        for change in changes:
            target = change["path"]
            before_hash = _sha256_file(target)
            target.write_text(str(change["after"]), encoding="utf-8")
            changed_files.append(
                {
                    "path": str(change["relative"]),
                    "before_sha256": before_hash,
                    "after_sha256": _sha256_file(target),
                }
            )
        post_apply_result = _post_apply_checks(name, paths) if post_apply else {}
        result_status = (
            "applied_with_failed_verification"
            if any(item.get("status") != "success" for item in post_apply_result.values())
            else "applied"
        )
        result = {
            "schema": SCHEMA,
            "figure_name": name,
            "candidate_id": candidate_id,
            "status": result_status,
            "changed_files": changed_files,
            "rollback_patch": _fixture_relative(example_dir, rollback_path),
            "post_apply": post_apply_result,
            "diagnostics": [],
        }
        if apply_result_path.is_symlink():
            raise CandidateApplyError("sandbox_symlink_forbidden: apply_result.json")
        apply_result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return result
