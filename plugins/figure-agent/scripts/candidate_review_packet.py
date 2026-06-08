"""Build read-only human review packets for rendered candidates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import candidate_contracts
import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.candidate-review-packet.v1"
HUMAN_DECISION_FIELDS = ["decision", "reviewer", "reviewed_at", "rationale"]


class CandidateReviewPacketError(ValueError):
    """Raised when a review packet would leave the candidate sandbox."""


def _candidate_id(value: str) -> str:
    fixture_identity.validate_fixture_name(value)
    return value


def _load_manifest(example_dir: Path, candidate_id: str) -> tuple[Path, dict[str, Any]]:
    manifest_path = candidate_contracts.fixture_relative_path(
        example_dir,
        f"build/candidates/{candidate_id}/candidate_manifest.json",
    )
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateReviewPacketError(f"manifest_unreadable: {candidate_id}") from exc
    if not isinstance(data, dict):
        raise CandidateReviewPacketError(f"manifest_invalid: {candidate_id}")
    return manifest_path, data


def _artifact_path(manifest_dir: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CandidateReviewPacketError("artifact_path_missing")
    path = Path(value)
    if path.is_absolute():
        raise CandidateReviewPacketError("path_escape")
    candidate = (manifest_dir / path).resolve()
    try:
        candidate.relative_to(manifest_dir.resolve())
    except ValueError as exc:
        raise CandidateReviewPacketError("path_escape") from exc
    return candidate


def _artifact_descriptors(
    manifest_path: Path,
    artifacts: Any,
) -> list[dict[str, Any]]:
    if not isinstance(artifacts, list):
        return []
    descriptors: list[dict[str, Any]] = []
    manifest_dir = manifest_path.parent
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        path_value = artifact.get("path")
        path = _artifact_path(manifest_dir, path_value)
        exists = path.is_file()
        descriptors.append(
            {
                "kind": str(artifact.get("kind", "unknown")),
                "path": str(path_value),
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else 0,
            }
        )
    return descriptors


def _manifest_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    verification = manifest.get("verification")
    base = manifest.get("base")
    operations = manifest.get("operations")
    artifacts = manifest.get("artifacts")
    return {
        "schema": manifest.get("schema"),
        "apply_authority": manifest.get("apply_authority"),
        "effective_apply_authority": manifest.get("effective_apply_authority"),
        "hard_gate_state": (
            verification.get("hard_gate_state")
            if isinstance(verification, dict)
            else None
        ),
        "operation_count": len(operations) if isinstance(operations, list) else 0,
        "artifact_count": len(artifacts) if isinstance(artifacts, list) else 0,
        "source_commit": base.get("source_commit") if isinstance(base, dict) else None,
    }


def build_review_packet(
    name: str,
    candidate_id: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    safe_candidate_id = _candidate_id(candidate_id)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    manifest_path, manifest = _load_manifest(example_dir, safe_candidate_id)
    return {
        "schema": SCHEMA,
        "fixture": name,
        "candidate_id": safe_candidate_id,
        "manifest_summary": _manifest_summary(manifest),
        "artifacts": _artifact_descriptors(manifest_path, manifest.get("artifacts")),
        "human_decision_required": True,
        "human_decision_fields": HUMAN_DECISION_FIELDS,
    }
