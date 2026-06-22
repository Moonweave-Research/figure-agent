"""Build read-only human review packets for rendered candidates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import candidate_acceptance
import candidate_apply
import fixture_identity
import runtime_paths
import semantic_candidate_review

SCHEMA = "figure-agent.candidate-review-packet.v1"
HUMAN_DECISION_FIELDS = ["decision", "reviewer", "reviewed_at", "rationale"]


class CandidateReviewPacketError(ValueError):
    """Raised when a review packet would leave the candidate sandbox."""


def _candidate_id(value: str) -> str:
    fixture_identity.validate_fixture_name(value)
    return value


def _candidate_sandbox_dir(example_dir: Path, candidate_id: str) -> Path:
    build_dir = example_dir / "build"
    if build_dir.is_symlink():
        raise CandidateReviewPacketError("sandbox_symlink_forbidden: build")
    root = build_dir / "candidates"
    if root.is_symlink():
        raise CandidateReviewPacketError("sandbox_symlink_forbidden: candidates")
    sandbox = root / candidate_id
    if sandbox.is_symlink():
        raise CandidateReviewPacketError(f"sandbox_symlink_forbidden: {candidate_id}")
    try:
        sandbox.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise CandidateReviewPacketError("candidate_id path_escape") from exc
    return sandbox


def _load_manifest(example_dir: Path, candidate_id: str) -> tuple[Path, dict[str, Any]]:
    sandbox = _candidate_sandbox_dir(example_dir, candidate_id)
    manifest_path = sandbox / "candidate_manifest.json"
    if manifest_path.is_symlink():
        raise CandidateReviewPacketError("sandbox_symlink_forbidden: candidate_manifest.json")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateReviewPacketError(f"manifest_unreadable: {candidate_id}") from exc
    if not isinstance(data, dict):
        raise CandidateReviewPacketError(f"manifest_invalid: {candidate_id}")
    return manifest_path, data


def _load_render_manifest(manifest_path: Path) -> tuple[Path, dict[str, Any]] | None:
    render_manifest_path = manifest_path.parent / "render_manifest.json"
    if render_manifest_path.is_symlink():
        raise CandidateReviewPacketError("sandbox_symlink_forbidden: render_manifest.json")
    if not render_manifest_path.exists():
        return None
    try:
        data = json.loads(render_manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateReviewPacketError("render_manifest_unreadable") from exc
    if not isinstance(data, dict):
        raise CandidateReviewPacketError("render_manifest_invalid")
    return render_manifest_path, data


def _artifact_path(manifest_dir: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CandidateReviewPacketError("artifact_path_missing")
    path = Path(value)
    if path.is_absolute():
        raise CandidateReviewPacketError("path_escape")
    lexical_path = manifest_dir / path
    if lexical_path.is_symlink():
        raise CandidateReviewPacketError(f"sandbox_symlink_forbidden: {path.name}")
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


def _fixture_artifact_descriptor(
    example_dir: Path,
    value: Any,
    *,
    kind: str,
) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise CandidateReviewPacketError("artifact_path_missing")
    path = Path(value)
    if path.is_absolute():
        raise CandidateReviewPacketError("path_escape")
    lexical_path = example_dir / path
    if lexical_path.is_symlink():
        raise CandidateReviewPacketError(f"sandbox_symlink_forbidden: {path.name}")
    candidate = lexical_path.resolve()
    try:
        candidate.relative_to(example_dir.resolve())
    except ValueError as exc:
        raise CandidateReviewPacketError("path_escape") from exc
    exists = candidate.is_file()
    return {
        "kind": kind,
        "path": path.as_posix(),
        "exists": exists,
        "size_bytes": candidate.stat().st_size if exists else 0,
    }


def _render_evidence(
    example_dir: Path,
    render_manifest_path: Path,
    render_manifest: dict[str, Any],
) -> dict[str, Any]:
    stages = (
        render_manifest.get("stages")
        if isinstance(render_manifest.get("stages"), dict)
        else {}
    )
    evaluate_stage = stages.get("evaluate") if isinstance(stages.get("evaluate"), dict) else {}
    render_status = str(evaluate_stage.get("status") or "not_rendered")
    artifacts = (
        render_manifest.get("artifacts")
        if isinstance(render_manifest.get("artifacts"), dict)
        else {}
    )
    before_artifacts = [
        item
        for item in [
            _fixture_artifact_descriptor(
                example_dir,
                artifacts.get("before_crop"),
                kind="before_crop",
            )
        ]
        if item is not None
    ]
    after_artifacts = [
        item
        for item in [
            _fixture_artifact_descriptor(
                example_dir,
                artifacts.get("after_crop"),
                kind="after_crop",
            )
        ]
        if item is not None
    ]
    return {
        "render_status": render_status,
        "render_manifest_path": render_manifest_path.relative_to(example_dir).as_posix(),
        "before_artifacts": before_artifacts,
        "after_artifacts": after_artifacts,
        "visual_deltas": (
            render_manifest.get("visual_deltas")
            if isinstance(render_manifest.get("visual_deltas"), dict)
            else {}
        ),
        "hard_gates": {
            "render": render_status,
            "compile": (
                stages.get("compile", {}).get("status")
                if isinstance(stages.get("compile"), dict)
                else None
            ),
            "export": (
                stages.get("export", {}).get("status")
                if isinstance(stages.get("export"), dict)
                else None
            ),
            "crop": (
                stages.get("crop", {}).get("status")
                if isinstance(stages.get("crop"), dict)
                else None
            ),
        },
        "human_review_required": bool(render_manifest.get("human_review_required", True)),
    }


def _manifest_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    verification = manifest.get("verification")
    base = manifest.get("base")
    operations = manifest.get("operations")
    artifacts = manifest.get("artifacts")
    return {
        "schema": manifest.get("schema"),
        "candidate_hash": manifest.get("candidate_hash"),
        "panel": manifest.get("panel"),
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
        "risk": manifest.get("risk"),
        "stages": manifest.get("stages") if isinstance(manifest.get("stages"), dict) else {},
        "visual_review": manifest.get("visual_review")
        if isinstance(manifest.get("visual_review"), dict)
        else {},
        "rollback_strategy": (
            manifest.get("rollback", {}).get("strategy")
            if isinstance(manifest.get("rollback"), dict)
            else None
        ),
    }


def _source_change_summary(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    operations = manifest.get("operations")
    if not isinstance(operations, list):
        return []
    changes: list[dict[str, Any]] = []
    for operation in operations:
        if not isinstance(operation, dict):
            continue
        changes.append(
            {
                "kind": operation.get("kind"),
                "path": operation.get("path"),
                "original": operation.get("original"),
                "replacement": operation.get("replacement"),
            }
        )
    return changes


def _rank_command(name: str, manifest: dict[str, Any]) -> str:
    candidate_set = str(manifest.get("candidate_set_path") or "build/candidates/candidate_set.json")
    return (
        f"fig-agent rank-candidates {name} "
        f"--candidate-set {candidate_set} --json"
    )


def _apply_readiness(
    name: str,
    candidate_id: str,
    manifest_path: Path,
    manifest: dict[str, Any],
    *,
    workspace_root: Path,
    plugin_root: Path | None,
) -> dict[str, Any]:
    apply_result_path = manifest_path.parent / "apply_result.json"
    if apply_result_path.is_file() and not apply_result_path.is_symlink():
        try:
            apply_result = json.loads(apply_result_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            apply_result = {}
        if isinstance(apply_result, dict) and apply_result.get("status") in {
            "applied",
            "applied_with_failed_verification",
        }:
            return {
                "status": str(apply_result["status"]),
                "blocking_reasons": [],
                "required_commands": [],
            }
    acceptance_path = manifest_path.parent / "acceptance.json"
    if acceptance_path.is_file() and not acceptance_path.is_symlink():
        candidate_set_path = Path(
            str(manifest.get("candidate_set_path") or "build/candidates/candidate_set.json")
        )
        dry_run = candidate_apply.apply_candidate(
            name,
            manifest,
            workspace_root=workspace_root,
            plugin_root=plugin_root,
            candidate_set_path=candidate_set_path,
            acceptance_path=Path(f"build/candidates/{candidate_id}/acceptance.json"),
            apply=False,
        )
        if dry_run.get("status") != "ready":
            return {
                "status": "blocked",
                "blocking_reasons": [
                    str(item.get("code", "unknown"))
                    for item in dry_run.get("diagnostics", [])
                    if isinstance(item, dict)
                ],
                "required_commands": [],
            }
        return {
            "status": "accepted_ready_to_apply",
            "blocking_reasons": [],
            "required_commands": [
                (
                    f"fig-agent apply-candidate {name} {candidate_id} "
                    f"--candidate-set {manifest.get('candidate_set_path')} "
                    f"--acceptance build/candidates/{candidate_id}/acceptance.json --json"
                )
            ],
        }
    candidate_set_path = Path(
        str(manifest.get("candidate_set_path") or "build/candidates/candidate_set.json")
    )
    try:
        return candidate_acceptance.build_apply_readiness(
            name,
            candidate_id,
            candidate_set_path=candidate_set_path,
            workspace_root=workspace_root,
            plugin_root=plugin_root,
        )
    except (ValueError, candidate_acceptance.CandidateAcceptanceError) as exc:
        return {
            "schema": "figure-agent.candidate-apply-readiness.v1",
            "figure_name": name,
            "candidate_id": candidate_id,
            "status": "blocked",
            "blocking_reasons": [str(exc)],
            "required_commands": [],
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
    render_manifest = _load_render_manifest(manifest_path)
    render_evidence = (
        _render_evidence(example_dir, render_manifest[0], render_manifest[1])
        if render_manifest is not None
        else {
            "render_status": "not_rendered",
            "render_manifest_path": None,
            "before_artifacts": [],
            "after_artifacts": [],
            "visual_deltas": {},
            "hard_gates": {"render": "not_rendered"},
            "human_review_required": True,
        }
    )
    packet = {
        "schema": SCHEMA,
        "fixture": name,
        "candidate_id": safe_candidate_id,
        "candidate_hash": manifest.get("candidate_hash"),
        "panel": manifest.get("panel"),
        "selectors": (
            manifest.get("selectors")
            if isinstance(manifest.get("selectors"), list)
            else []
        ),
        "visual_review": manifest.get("visual_review")
        if isinstance(manifest.get("visual_review"), dict)
        else {"status": "missing_render"},
        "manifest_summary": _manifest_summary(manifest),
        "artifacts": _artifact_descriptors(manifest_path, manifest.get("artifacts")),
        "source_changes": _source_change_summary(manifest),
        "score_report": {
            "status": "not_available",
            "recommended_command": _rank_command(name, manifest),
        },
        "semantic_invariant_report": semantic_candidate_review.build_semantic_review_state(
            example_dir,
            manifest_path,
            manifest,
            spec=semantic_candidate_review.load_spec(example_dir),
        ),
        "rollback": {
            "status": "manual_reverse_operations",
            "command": None,
        },
        "recommended_next_action": "human_review_required",
        "human_decision_required": True,
        "human_decision_fields": HUMAN_DECISION_FIELDS,
    }
    packet.update(render_evidence)
    packet["apply_readiness"] = _apply_readiness(
        name,
        safe_candidate_id,
        manifest_path,
        manifest,
        workspace_root=paths.workspace_root,
        plugin_root=paths.plugin_root,
    )
    return packet
