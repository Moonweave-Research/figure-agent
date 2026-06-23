from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Final

import fixture_identity
import runtime_paths

RENDER_SCHEMA: Final = "figure-agent.composition-render-manifest.v1"
DEFAULT_SET: Final = Path("build/candidates/composition_candidate_set.json")
LATE_STAGES: Final = ("compile", "export", "crop", "evaluate")


class CompositionAcceptanceError(ValueError):
    pass


def root(workspace_root: Path | None) -> Path:
    return runtime_paths.resolve_runtime_paths(workspace_root=workspace_root).workspace_root


def safe_id(value: str) -> str:
    fixture_identity.validate_fixture_name(value)
    return value


def hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def hash_json(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + sha256(encoded).hexdigest()


def fixture_relative(fixture: Path, path: Path) -> str:
    return path.relative_to(fixture).as_posix()


def safe_fixture_path(fixture: Path, path: Path) -> Path:
    try:
        relative = path.relative_to(fixture)
    except ValueError as exc:
        raise CompositionAcceptanceError("path_escape") from exc
    cursor = fixture
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise CompositionAcceptanceError("sandbox_symlink_forbidden")
    try:
        path.resolve(strict=False).relative_to(fixture.resolve(strict=False))
    except ValueError as exc:
        raise CompositionAcceptanceError("path_escape") from exc
    return path


def selected_candidate(candidate_set: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    candidates = candidate_set.get("candidates")
    if not isinstance(candidates, list):
        raise CompositionAcceptanceError("candidate_set_invalid")
    for candidate in candidates:
        if isinstance(candidate, dict) and str(candidate.get("id") or "") == candidate_id:
            return candidate
    raise CompositionAcceptanceError("candidate_missing")


def single_operation(candidate: dict[str, Any]) -> dict[str, Any]:
    operations = candidate.get("operations")
    if not isinstance(operations, list) or len(operations) != 1:
        raise CompositionAcceptanceError("operation_required")
    operation = operations[0]
    if not isinstance(operation, dict):
        raise CompositionAcceptanceError("operation_invalid")
    return operation


def operation_source(workspace: Path, fixture: Path, operation: dict[str, Any]) -> Path:
    value = operation.get("path")
    if not isinstance(value, str) or not value.strip():
        raise CompositionAcceptanceError("operation_path_missing")
    path = Path(value)
    source = workspace / path if path.parts[:1] == ("examples",) else fixture / path
    return safe_fixture_path(fixture, source)


def load_render_manifest(fixture: Path, candidate_id: str) -> tuple[Path, dict[str, Any]]:
    path = safe_fixture_path(
        fixture,
        fixture / "build" / "candidates" / candidate_id / "composition_render_manifest.json",
    )
    if not path.exists():
        raise CompositionAcceptanceError("render_manifest_missing")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != RENDER_SCHEMA:
        raise CompositionAcceptanceError("render_manifest_invalid")
    if payload.get("fixture") != fixture.name or payload.get("candidate_id") != candidate_id:
        raise CompositionAcceptanceError("render_manifest_identity_mismatch")
    return path, payload


def source_copy_path(fixture: Path, manifest: dict[str, Any]) -> Path:
    artifacts = manifest.get("artifacts")
    value = artifacts.get("source_copy") if isinstance(artifacts, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise CompositionAcceptanceError("source_copy_missing")
    path = safe_fixture_path(fixture, fixture / value)
    if not path.is_file():
        raise CompositionAcceptanceError("source_copy_missing")
    return path


def stage_status(manifest: dict[str, Any], stage: str) -> str:
    stages = manifest.get("stages") if isinstance(manifest.get("stages"), dict) else {}
    value = stages.get(stage)
    return str(value.get("status") if isinstance(value, dict) else "missing")


def has_stale_evidence(candidate_set: dict[str, Any]) -> bool:
    vector = candidate_set.get("freshness_vector")
    status = vector.get("status") if isinstance(vector, dict) else None
    return isinstance(status, dict) and any(value == "stale" for value in status.values())


def truth_bearing_geometry_change(candidate: dict[str, Any]) -> bool:
    metadata = candidate.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    return any(
        value is True
        for value in (
            metadata.get("truth_bearing_geometry_change"),
            metadata.get("change_truth_bearing_geometry"),
            candidate.get("truth_bearing_geometry_change"),
        )
    )


def required_permissions(candidate: dict[str, Any]) -> list[str]:
    permissions: list[str] = []
    if candidate.get("family") == "freeform_structural":
        permissions.append("accept_freeform_structural")
    if truth_bearing_geometry_change(candidate):
        permissions.append("change_truth_bearing_geometry")
    return permissions


def candidate_set_hash(
    path: Path | None,
    candidate_set: dict[str, Any],
    fixture: Path,
) -> str:
    if path is not None:
        candidate_path = safe_fixture_path(fixture, fixture / path)
        if candidate_path.is_file():
            return hash_file(candidate_path)
    return hash_json(candidate_set)


def facts(
    name: str,
    candidate_id: str,
    candidate_set: dict[str, Any],
    workspace_root: Path | None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    current_id = safe_id(candidate_id)
    workspace = root(workspace_root)
    fixture = workspace / "examples" / name
    candidate = selected_candidate(candidate_set, current_id)
    operation = single_operation(candidate)
    manifest_path, manifest = load_render_manifest(fixture, current_id)
    source_copy = source_copy_path(fixture, manifest)
    source = operation_source(workspace, fixture, operation)
    return {
        "id": current_id,
        "workspace": workspace,
        "fixture": fixture,
        "candidate": candidate,
        "operation": operation,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "source_copy": source_copy,
        "source": source,
    }


def evidence_hashes(
    facts_payload: dict[str, Any],
    candidate_set: dict[str, Any],
    candidate_set_path: Path | None,
) -> dict[str, str | None]:
    source = facts_payload["source"]
    return {
        "candidate_set": candidate_set_hash(
            candidate_set_path,
            candidate_set,
            facts_payload["fixture"],
        ),
        "render_manifest": hash_file(facts_payload["manifest_path"]),
        "candidate_source_copy": hash_file(facts_payload["source_copy"]),
        "base_source": hash_file(source) if source.is_file() else None,
        "operations": hash_json(facts_payload["candidate"].get("operations", [])),
    }
