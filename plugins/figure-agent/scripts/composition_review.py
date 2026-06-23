from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Final

import composition_acceptance
import composition_rank
import fixture_identity
import runtime_paths

SCHEMA: Final = "figure-agent.composition-review-packet.v1"


class CompositionReviewError(ValueError):
    pass


def _workspace_root(workspace_root: Path | None) -> Path:
    return runtime_paths.resolve_runtime_paths(workspace_root=workspace_root).workspace_root


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _fixture_relative(fixture: Path, path: Path) -> str:
    return path.relative_to(fixture).as_posix()


def _candidate_id(value: str) -> str:
    fixture_identity.validate_fixture_name(value)
    return value


def _candidate(candidate_set: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    candidates = candidate_set.get("candidates")
    if not isinstance(candidates, list):
        raise CompositionReviewError("candidate_set_invalid")
    for candidate in candidates:
        if isinstance(candidate, dict) and str(candidate.get("id") or "") == candidate_id:
            return candidate
    raise CompositionReviewError("candidate_missing")


def _operation_source_path(workspace: Path, fixture: Path, operation: dict[str, Any]) -> Path:
    value = operation.get("path")
    if not isinstance(value, str) or not value.strip():
        raise CompositionReviewError("operation_path_missing")
    path = Path(value)
    source = workspace / path if path.parts[:1] == ("examples",) else fixture / path
    return _safe_fixture_path(fixture, source)


def _single_operation(candidate: dict[str, Any]) -> dict[str, Any]:
    operations = candidate.get("operations")
    if not isinstance(operations, list) or len(operations) != 1:
        raise CompositionReviewError("operation_required")
    operation = operations[0]
    if not isinstance(operation, dict):
        raise CompositionReviewError("operation_invalid")
    return operation


def _safe_fixture_path(fixture: Path, path: Path) -> Path:
    try:
        relative = path.relative_to(fixture)
    except ValueError as exc:
        raise CompositionReviewError("path_escape") from exc
    cursor = fixture
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise CompositionReviewError("sandbox_symlink_forbidden")
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(fixture.resolve(strict=False))
    except ValueError as exc:
        raise CompositionReviewError("path_escape") from exc
    return path


def _load_manifest(fixture: Path, candidate_id: str) -> dict[str, Any]:
    manifest = _safe_fixture_path(
        fixture,
        fixture / "build" / "candidates" / candidate_id / "composition_render_manifest.json",
    )
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CompositionReviewError("render_manifest_invalid")
    return payload


def _source_copy_path(fixture: Path, manifest: dict[str, Any]) -> Path:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise CompositionReviewError("artifacts_missing")
    value = artifacts.get("source_copy")
    if not isinstance(value, str) or not value.strip():
        raise CompositionReviewError("source_copy_missing")
    return _safe_fixture_path(fixture, fixture / value)


def _artifact_descriptor(fixture: Path, path: Path, *, kind: str) -> dict[str, Any]:
    exists = path.is_file()
    return {
        "kind": kind,
        "path": _fixture_relative(fixture, path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
        "sha256": _sha256_file(path) if exists else None,
    }


def _hard_gates(manifest: dict[str, Any]) -> dict[str, str]:
    stages = manifest.get("stages") if isinstance(manifest.get("stages"), dict) else {}
    gates: dict[str, str] = {}
    for stage in ("prepare", "compile", "export", "crop", "evaluate"):
        value = stages.get(stage)
        gates[stage] = str(value.get("status") if isinstance(value, dict) else "missing")
    return gates


def _candidate_rank_entry(rank_payload: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    ranked = rank_payload.get("ranked_candidates")
    if isinstance(ranked, list):
        for candidate in ranked:
            if isinstance(candidate, dict) and candidate.get("candidate_id") == candidate_id:
                return candidate
    raise CompositionReviewError("candidate_rank_missing")


def build_composition_review_packet(
    name: str,
    *,
    candidate_set: dict[str, Any],
    candidate_id: str,
    workspace_root: Path | None = None,
    candidate_set_path: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    current_candidate_id = _candidate_id(candidate_id)
    workspace = _workspace_root(workspace_root)
    fixture = workspace / "examples" / name
    candidate = _candidate(candidate_set, current_candidate_id)
    operation = _single_operation(candidate)
    source = _operation_source_path(workspace, fixture, operation)
    manifest = _load_manifest(fixture, current_candidate_id)
    source_copy = _source_copy_path(fixture, manifest)
    rank_payload = composition_rank.rank_composition_candidates(
        name,
        candidate_set=candidate_set,
        workspace_root=workspace,
    )
    rank_entry = _candidate_rank_entry(rank_payload, current_candidate_id)
    readiness = composition_acceptance.build_composition_apply_readiness(
        name,
        current_candidate_id,
        candidate_set=candidate_set,
        candidate_set_path=candidate_set_path,
        workspace_root=workspace,
    )
    return {
        "schema": SCHEMA,
        "fixture": name,
        "candidate_id": current_candidate_id,
        "candidate_set_path": (
            candidate_set_path or Path("build/candidates/composition_candidate_set.json")
        ).as_posix(),
        "render_status": rank_entry["render_status"],
        "hard_gates": _hard_gates(manifest),
        "before_artifacts": [_artifact_descriptor(fixture, source, kind="base_source")],
        "after_artifacts": [
            _artifact_descriptor(fixture, source_copy, kind="candidate_source_copy")
        ],
        "composition_lint_delta": rank_entry["composition_lint_delta"],
        "candidate": {
            "id": current_candidate_id,
            "family": str(candidate.get("family") or "unknown"),
            "effective_apply_authority": rank_entry["effective_apply_authority"],
            "auto_apply_allowed": False,
        },
        "rank_policy": rank_payload["rank_policy"],
        "apply_boundary": {
            "status": readiness["status"],
            "source_mutation_allowed": False,
        },
        "human_review_required": True,
        "diagnostics": [],
    }
