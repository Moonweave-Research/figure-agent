from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import composition_sandbox
import composition_scene
import fixture_identity
import runtime_paths

COMPOSITION_RENDER_RESULT_SCHEMA = "figure-agent.composition-render-result.v1"
COMPOSITION_RENDER_MANIFEST_SCHEMA = "figure-agent.composition-render-manifest.v1"


class CompositionRenderError(ValueError):
    pass


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _diagnostic(code: str, message: str, stage: str = "prepare") -> dict[str, str]:
    return {"code": code, "stage": stage, "message": message}


def _fixture_relative(fixture: Path, path: Path) -> str:
    return path.relative_to(fixture).as_posix()


def _candidate_id(candidate: dict[str, Any]) -> str:
    value = str(candidate.get("id") or "")
    fixture_identity.validate_fixture_name(value)
    return value


def _selected_candidate(candidate_set: dict[str, Any], candidate_id: str | None) -> dict[str, Any]:
    candidates = candidate_set.get("candidates")
    if not isinstance(candidates, list):
        raise CompositionRenderError("candidate_set_invalid")
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        current_id = _candidate_id(candidate)
        if candidate_id is None or current_id == candidate_id:
            return candidate
    raise CompositionRenderError("candidate_missing")


def _single_operation(candidate: dict[str, Any]) -> dict[str, Any]:
    operations = candidate.get("operations")
    if not isinstance(operations, list) or len(operations) != 1:
        raise CompositionRenderError("operation_required")
    operation = operations[0]
    if not isinstance(operation, dict):
        raise CompositionRenderError("operation_invalid")
    if operation.get("kind") != "replace_semantic_block":
        raise CompositionRenderError("operation_kind_unsupported")
    return operation


def _operation_path(operation: dict[str, Any], fixture_name: str, workspace: Path) -> Path:
    value = operation.get("path")
    if not isinstance(value, str) or not value.strip():
        raise CompositionRenderError("operation_path_missing")
    path = Path(value)
    if path.parts[:2] == ("examples", fixture_name):
        path = Path(*path.parts[2:])
    elif path.parts[:1] == ("examples",):
        return workspace / Path(value)
    return path


def _replace_semantic_block(source_text: str, operation: dict[str, Any]) -> str:
    selector = operation.get("selector")
    if not isinstance(selector, dict):
        raise CompositionRenderError("selector_missing")
    start = selector.get("start_marker")
    end = selector.get("end_marker")
    if (not isinstance(start, str) or not isinstance(end, str)) and isinstance(
        selector.get("object_id"),
        str,
    ):
        try:
            selector = composition_scene.semantic_block_selector_from_text(
                source_text,
                selector["object_id"],
            )
        except composition_scene.CompositionSceneError as exc:
            raise CompositionRenderError(str(exc)) from exc
        start = selector.get("start_marker")
        end = selector.get("end_marker")
    replacement = operation.get("replacement_text")
    if not isinstance(start, str) or not isinstance(end, str) or not isinstance(replacement, str):
        raise CompositionRenderError("operation_payload_missing")
    start_index = source_text.find(start)
    end_index = source_text.find(end, start_index + len(start)) if start_index >= 0 else -1
    if start_index < 0 or end_index < 0:
        raise CompositionRenderError("selector_not_found")
    after_end = end_index + len(end)
    if after_end < len(source_text) and source_text[after_end] == "\n":
        after_end += 1
    return source_text[:start_index] + replacement + source_text[after_end:]


def _manifest(
    name: str,
    candidate_id: str,
    candidate_set_path: str,
    sandbox: Path,
    fixture: Path,
) -> dict[str, Any]:
    source_copy = sandbox / "source" / "candidate.tex"
    return {
        "schema": COMPOSITION_RENDER_MANIFEST_SCHEMA,
        "fixture": name,
        "candidate_id": candidate_id,
        "candidate_set_path": candidate_set_path,
        "sandbox_path": _fixture_relative(fixture, sandbox),
        "artifacts": {"source_copy": _fixture_relative(fixture, source_copy)},
        "stages": {
            "prepare": {"status": "success"},
            "compile": {"status": "not_run"},
            "export": {"status": "not_run"},
            "crop": {"status": "not_run"},
            "evaluate": {"status": "not_run"},
        },
        "render_policy": {
            "tex_execution_allowed": False,
            "model_calls_allowed": False,
            "executable_payload_allowed": False,
        },
        "human_review_required": True,
    }


def prepare_composition_render(
    name: str,
    *,
    candidate_set: dict[str, Any],
    workspace_root: Path | None = None,
    candidate_set_path: Path | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(workspace_root=workspace_root)
    fixture = paths.examples_dir / name
    candidate = _selected_candidate(candidate_set, candidate_id)
    current_candidate_id = _candidate_id(candidate)
    operation = _single_operation(candidate)
    source_path = _operation_path(operation, name, paths.workspace_root)
    source, blocked = composition_sandbox.preflight_candidate_source_path(
        name,
        candidate_source_path=source_path,
        workspace_root=paths.workspace_root,
    )
    if blocked is not None:
        return {"schema": COMPOSITION_RENDER_RESULT_SCHEMA, "status": "blocked", **blocked}
    assert source is not None
    expected_hash = operation.get("base_source_hash")
    if expected_hash != _sha256_file(source):
        return {
            "schema": COMPOSITION_RENDER_RESULT_SCHEMA,
            "fixture": name,
            "status": "rebase_required",
            "rendered": [],
            "diagnostics": [
                {
                    **_diagnostic("source_hash_drift", "source changed since proposal"),
                    "action": "rebase_required",
                }
            ],
        }
    sandbox = fixture / "build" / "candidates" / current_candidate_id
    source_copy = sandbox / "source" / "candidate.tex"
    manifest_path = sandbox / "composition_render_manifest.json"
    source_copy.parent.mkdir(parents=True, exist_ok=True)
    source_copy.write_text(
        _replace_semantic_block(source.read_text(encoding="utf-8"), operation),
        encoding="utf-8",
    )
    manifest = _manifest(
        name,
        current_candidate_id,
        (candidate_set_path or Path("build/candidates/composition_candidate_set.json")).as_posix(),
        sandbox,
        fixture,
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "schema": COMPOSITION_RENDER_RESULT_SCHEMA,
        "fixture": name,
        "status": "prepared",
        "rendered": [
            {
                "candidate_id": current_candidate_id,
                "render_manifest": _fixture_relative(fixture, manifest_path),
            }
        ],
        "diagnostics": [],
    }
