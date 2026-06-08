"""Create candidate sandbox manifests without touching source exports."""

from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path
from typing import Any

import candidate_contracts
import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.candidate-manifest.v1"
RESULT_SCHEMA = "figure-agent.candidate-render-result.v1"
ZERO_HASH = "sha256:" + "0" * 64


class CandidateRenderError(ValueError):
    """Raised when candidate rendering would escape the manifest sandbox."""


def _source_commit(workspace_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=workspace_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _safe_candidate_id(value: Any) -> str:
    candidate_id = str(value)
    if not fixture_identity.is_safe_fixture_name(candidate_id):
        raise CandidateRenderError(f"invalid candidate_id: {candidate_id}")
    return candidate_id


def _sandbox_dir(example_dir: Path, candidate_id: str) -> Path:
    build_dir = example_dir / "build"
    if build_dir.is_symlink():
        raise CandidateRenderError("sandbox_symlink_forbidden: build")
    root = example_dir / "build" / "candidates"
    if root.is_symlink():
        raise CandidateRenderError("sandbox_symlink_forbidden: candidates")
    out_dir = root / candidate_id
    if out_dir.is_symlink():
        raise CandidateRenderError(f"sandbox_symlink_forbidden: {candidate_id}")
    try:
        out_dir.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise CandidateRenderError(f"candidate_id path_escape: {candidate_id}") from exc
    return out_dir


def _write_sandbox_file(path: Path, text: str) -> None:
    if path.is_symlink():
        raise CandidateRenderError(f"sandbox_symlink_forbidden: {path.name}")
    path.write_text(text, encoding="utf-8")


def _fixture_path(example_dir: Path, fixture_name: str, value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CandidateRenderError("operation path missing")
    path = Path(value)
    examples_prefix = ("examples", fixture_name)
    if path.parts[:2] == examples_prefix:
        path = Path(*path.parts[2:])
    return candidate_contracts.fixture_relative_path(example_dir, path.as_posix())


def _candidate_source_text(
    example_dir: Path,
    fixture_name: str,
    candidate: dict[str, Any],
) -> tuple[str, str] | None:
    operations = candidate.get("operations")
    if not isinstance(operations, list):
        return None

    sources: dict[Path, str] = {}
    for operation in operations:
        if not isinstance(operation, dict) or operation.get("kind") != "replace_text":
            continue
        source_path = _fixture_path(example_dir, fixture_name, operation.get("path"))
        text = sources.get(source_path)
        if text is None:
            text = source_path.read_text(encoding="utf-8")
        original = str(operation.get("original", ""))
        replacement = str(operation.get("replacement", ""))
        if original not in text:
            raise CandidateRenderError(f"operation original not found: {source_path.name}")
        sources[source_path] = text.replace(original, replacement, 1)

    if not sources:
        return None
    if len(sources) > 1:
        raise CandidateRenderError("multiple source copies are not supported")
    source_path, text = next(iter(sources.items()))
    return source_path.name, text


def _write_candidate_source_copy(
    *,
    example_dir: Path,
    fixture_name: str,
    candidate: dict[str, Any],
    out_dir: Path,
) -> list[dict[str, str]]:
    source_copy = _candidate_source_text(example_dir, fixture_name, candidate)
    if source_copy is None:
        return []
    filename, text = source_copy
    destination = out_dir / filename
    _write_sandbox_file(destination, text)
    return [{"kind": "candidate_source", "path": destination.name}]


def render_candidate_set(
    name: str,
    candidate_set: dict[str, Any],
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    candidate_set_path: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    rendered: list[dict[str, Any]] = []
    for candidate in candidate_set.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        candidate_id = _safe_candidate_id(candidate.get("id"))
        out_dir = _sandbox_dir(example_dir, candidate_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        artifacts = _write_candidate_source_copy(
            example_dir=example_dir,
            fixture_name=name,
            candidate=candidate,
            out_dir=out_dir,
        )
        hard_gate_state = "human_required"
        effective = candidate_contracts.effective_apply_authority(
            str(candidate.get("apply_authority")),
            hard_gate_state,
        )
        base = candidate_set.get("base") if isinstance(candidate_set.get("base"), dict) else {}
        manifest = {
            "schema": SCHEMA,
            "candidate_id": candidate_id,
            "candidate_hash": candidate.get("candidate_hash"),
            "fixture": name,
            "candidate_set_path": candidate_set_path.as_posix()
            if candidate_set_path is not None
            else "build/candidates/candidate_set.json",
            "panel": (
                candidate.get("target", {}).get("panel")
                if isinstance(candidate.get("target"), dict)
                else candidate.get("panel")
            ),
            "selectors": candidate.get("selectors", []),
            "base": {
                "source_commit": _source_commit(paths.workspace_root),
                "tex_hash": base.get("tex_hash", ZERO_HASH),
                "status_hash": base.get("status_hash", ZERO_HASH),
                "render_hash": ZERO_HASH,
            },
            "tool_versions": {
                "fig_agent": "0.11.x",
                "python": platform.python_version(),
                "tex_engine": "not_run",
            },
            "operations": candidate.get("operations", []),
            "artifacts": artifacts,
            "stages": {
                "prepare": "passed",
                "compile": "not_run",
                "export": "not_run",
                "crop": "not_run",
            },
            "visual_review": candidate.get(
                "visual_review",
                {
                    "status": "missing_render",
                    "reason": "candidate compile/export/crop has not run",
                },
            ),
            "verification": {
                "commands": candidate.get("verification", {}).get(
                    "required_commands",
                    [],
                ),
                "hard_gate_state": hard_gate_state,
            },
            "apply_authority": candidate.get("apply_authority"),
            "effective_apply_authority": effective,
            "risk": candidate.get("risk"),
            "rollback": candidate.get("rollback"),
        }
        path = out_dir / "candidate_manifest.json"
        _write_sandbox_file(
            path,
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        )
        rendered.append({"candidate_id": candidate_id, "manifest": str(path)})
    return {"schema": RESULT_SCHEMA, "fixture": name, "rendered": rendered}
