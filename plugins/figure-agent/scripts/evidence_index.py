"""Fixture-local evidence index builder."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import candidate_contracts
import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.evidence-index.v1"


class EvidenceIndexError(ValueError):
    """Raised when evidence indexing would leave fixture boundaries."""


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise EvidenceIndexError(f"sandbox_symlink_forbidden: {path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvidenceIndexError(f"{label}_missing") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceIndexError(f"{label}_unreadable") from exc
    if not isinstance(payload, dict):
        raise EvidenceIndexError(f"{label}_invalid")
    return payload


def _fixture_relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError as exc:
        raise EvidenceIndexError("path_escape") from exc


def _candidate_sandbox(example_dir: Path, candidate_id: str) -> Path:
    build_dir = example_dir / "build"
    root = build_dir / "candidates"
    sandbox = root / candidate_id
    for label, path in (("build", build_dir), ("candidates", root), (candidate_id, sandbox)):
        if path.is_symlink():
            raise EvidenceIndexError(f"sandbox_symlink_forbidden: {label}")
    try:
        sandbox.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise EvidenceIndexError("candidate path_escape") from exc
    return sandbox


def _stage_status(payload: dict[str, Any], stage: str) -> str | None:
    stages = payload.get("stages") if isinstance(payload.get("stages"), dict) else {}
    value = stages.get(stage)
    if isinstance(value, dict):
        status = value.get("status")
        return str(status) if status is not None else None
    if value is not None:
        return str(value)
    return None


def _render_status(render_manifest: dict[str, Any]) -> str | None:
    return _stage_status(render_manifest, "evaluate")


def _post_apply_summary(apply_result: dict[str, Any]) -> dict[str, str]:
    post_apply = apply_result.get("post_apply")
    if not isinstance(post_apply, dict):
        return {}
    summary: dict[str, str] = {}
    for stage in ("compile", "export", "status"):
        value = post_apply.get(stage)
        if isinstance(value, dict):
            summary[stage] = str(value.get("status") or "missing")
        elif value is not None:
            summary[stage] = str(value)
    return summary


def _apply_status(
    *,
    example_dir: Path,
    apply_result: dict[str, Any] | None,
    diagnostics: list[str],
) -> str | None:
    if apply_result is None:
        return None
    status = str(apply_result.get("status") or "unknown")
    if status != "applied":
        return status
    changed_files = apply_result.get("changed_files")
    if not isinstance(changed_files, list):
        diagnostics.append("candidate_apply_changed_files_missing")
        return "stale"
    for item in changed_files:
        if not isinstance(item, dict):
            continue
        relative = item.get("path")
        expected = item.get("after_sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            continue
        target = example_dir / relative
        try:
            target.resolve().relative_to(example_dir.resolve())
        except ValueError:
            diagnostics.append(f"candidate_apply_path_escape:{relative}")
            return "stale"
        if not target.is_file() or _sha256_file(target) != expected:
            diagnostics.append(f"candidate_apply_stale:{relative}")
            return "stale"
    return "applied"


def _status_summary(example_dir: Path, name: str) -> dict[str, Any]:
    try:
        import status

        payload = status.infer_stage(example_dir)
    except Exception as exc:  # noqa: BLE001 - evidence should degrade into diagnostics.
        return {"error": str(exc)}
    return {
        "render_state": payload.get("render_state"),
        "critique_state": payload.get("critique_state"),
        "export_state": payload.get("export_state"),
        "workflow_ready": bool(payload.get("workflow_ready")),
        "release_ready": bool(payload.get("release_ready")),
        "stage": payload.get("stage"),
        "next": payload.get("next"),
        "name": name,
    }


def build_evidence_index(
    name: str,
    *,
    candidate_id: str | None = None,
    candidate_set_path: Path | None = None,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    if not example_dir.is_dir():
        raise EvidenceIndexError(f"examples/{name}/ not found")
    tex_path = example_dir / f"{name}.tex"
    source = {
        "tex_path": f"{name}.tex",
        "tex_sha256": _sha256_file(tex_path) if tex_path.is_file() else None,
    }
    diagnostics: list[str] = []
    candidate_payload: dict[str, Any] | None = None
    if candidate_id is not None:
        fixture_identity.validate_fixture_name(candidate_id)
        sandbox = _candidate_sandbox(example_dir, candidate_id)
        manifest_path = sandbox / "candidate_manifest.json"
        render_path = sandbox / "render_manifest.json"
        manifest = _load_json(manifest_path, "candidate_manifest")
        render_manifest = _load_json(render_path, "render_manifest")
        if manifest.get("candidate_id") != candidate_id:
            diagnostics.append("candidate_id_mismatch")
        if render_manifest.get("candidate_id") != candidate_id:
            diagnostics.append("candidate_id_mismatch")
        if manifest.get("candidate_hash") != render_manifest.get("candidate_hash"):
            diagnostics.append("hash_mismatch")
        if candidate_set_path is None:
            candidate_set_path = Path(str(manifest.get("candidate_set_path") or ""))
        candidate_set_file = None
        if candidate_set_path:
            raw_candidate_set_file = example_dir / candidate_set_path
            if raw_candidate_set_file.is_symlink():
                raise EvidenceIndexError("sandbox_symlink_forbidden: candidate_set")
            candidate_set_file = candidate_contracts.fixture_local_output_path(
                paths.workspace_root,
                name,
                candidate_set_path.as_posix(),
            )
            candidate_set = _load_json(candidate_set_file, "candidate_set")
            for item in candidate_set.get("candidates", []):
                if isinstance(item, dict) and item.get("id") == candidate_id:
                    if item.get("candidate_hash") != manifest.get("candidate_hash"):
                        diagnostics.append("hash_mismatch")
                    break
        acceptance_path = sandbox / "acceptance.json"
        apply_result_path = sandbox / "apply_result.json"
        apply_result = (
            _load_json(apply_result_path, "apply_result")
            if apply_result_path.is_file() and not apply_result_path.is_symlink()
            else None
        )
        apply_status = _apply_status(
            example_dir=example_dir,
            apply_result=apply_result,
            diagnostics=diagnostics,
        )
        candidate_payload = {
            "candidate_id": candidate_id,
            "candidate_hash": str(manifest.get("candidate_hash") or ""),
            "candidate_set_path": _fixture_relative(example_dir, candidate_set_file)
            if candidate_set_file is not None
            else None,
            "candidate_manifest_path": _fixture_relative(example_dir, manifest_path),
            "render_manifest_path": _fixture_relative(example_dir, render_path),
            "acceptance_path": _fixture_relative(example_dir, acceptance_path)
            if acceptance_path.is_file()
            else None,
            "apply_result_path": _fixture_relative(example_dir, apply_result_path)
            if apply_result_path.is_file()
            else None,
            "manifest_visual_review": manifest.get("visual_review")
            if isinstance(manifest.get("visual_review"), dict)
            else {},
            "render_status": _render_status(render_manifest),
            "apply_status": apply_status,
            "post_apply": _post_apply_summary(apply_result or {}),
        }
    return {
        "schema": SCHEMA,
        "figure_name": name,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00",
            "Z",
        ),
        "source": source,
        "candidate": candidate_payload,
        "status": _status_summary(example_dir, name),
        "diagnostics": diagnostics,
    }
