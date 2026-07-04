"""Acceptance and readiness gates for rendered candidates."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import candidate_contracts
import fixture_identity
import runtime_paths
import semantic_candidate_review

READINESS_SCHEMA = "figure-agent.candidate-apply-readiness.v1"
ACCEPTANCE_SCHEMA = "figure-agent.candidate-acceptance.v1"
ACCEPTANCE_DECISIONS = {"accept", "reject", "defer"}
TERMINAL_APPLY_STATUSES = {
    "applied",
    "applied_unverified",
    "applied_with_failed_verification",
}


class CandidateAcceptanceError(ValueError):
    """Raised when acceptance/readiness would escape the candidate sandbox."""


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _candidate_id(value: str) -> str:
    fixture_identity.validate_fixture_name(value)
    return value


def _candidate_sandbox(example_dir: Path, candidate_id: str) -> Path:
    build_dir = example_dir / "build"
    root = build_dir / "candidates"
    sandbox = root / candidate_id
    for label, path in (("build", build_dir), ("candidates", root), (candidate_id, sandbox)):
        if path.is_symlink():
            raise CandidateAcceptanceError(f"sandbox_symlink_forbidden: {label}")
    try:
        sandbox.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise CandidateAcceptanceError("candidate path_escape") from exc
    return sandbox


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise CandidateAcceptanceError(f"sandbox_symlink_forbidden: {path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateAcceptanceError(f"{label}_unreadable") from exc
    if not isinstance(payload, dict):
        raise CandidateAcceptanceError(f"{label}_invalid")
    return payload


def _fixture_relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError as exc:
        raise CandidateAcceptanceError("path_escape") from exc


def _candidate_set_candidate(
    candidate_set: dict[str, Any],
    candidate_id: str,
) -> dict[str, Any] | None:
    candidates = candidate_set.get("candidates")
    if not isinstance(candidates, list):
        return None
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("id") == candidate_id:
            return candidate
    return None


def _render_gates(render_manifest: dict[str, Any]) -> list[str]:
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


def _operation_path(example_dir: Path, fixture_name: str, operation: dict[str, Any]) -> Path:
    value = operation.get("path")
    if not isinstance(value, str) or not value.strip():
        raise CandidateAcceptanceError("operation_path_missing")
    path = Path(value)
    if path.parts[:2] == ("examples", fixture_name):
        path = Path(*path.parts[2:])
    target = example_dir / path
    if target.is_symlink():
        raise CandidateAcceptanceError("source_symlink_forbidden")
    try:
        target.resolve().relative_to(example_dir.resolve())
    except ValueError as exc:
        raise CandidateAcceptanceError("source_path_escape") from exc
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


def _load_gate_inputs(
    name: str,
    candidate_id: str,
    *,
    candidate_set_path: Path,
    workspace_root: Path | None,
    plugin_root: Path | None,
) -> tuple[Path, Path, dict[str, Any], Path, dict[str, Any], Path, dict[str, Any]]:
    fixture_identity.validate_fixture_name(name)
    safe_candidate_id = _candidate_id(candidate_id)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    sandbox = _candidate_sandbox(example_dir, safe_candidate_id)
    candidate_set_file = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        candidate_set_path.as_posix(),
    )
    candidate_set = _load_json(candidate_set_file, "candidate_set")
    manifest_path = sandbox / "candidate_manifest.json"
    render_manifest_path = sandbox / "render_manifest.json"
    manifest = _load_json(manifest_path, "candidate_manifest")
    render_manifest = _load_json(render_manifest_path, "render_manifest")
    return (
        example_dir,
        candidate_set_file,
        candidate_set,
        manifest_path,
        manifest,
        render_manifest_path,
        render_manifest,
    )


def _source_drift_blocks(
    example_dir: Path,
    fixture_name: str,
    manifest: dict[str, Any],
) -> list[str]:
    operations = manifest.get("operations")
    if not isinstance(operations, list):
        return ["operations_missing"]
    if not operations:
        return ["operations_empty"]
    blocking: list[str] = []
    for operation in operations:
        if not isinstance(operation, dict):
            blocking.append("operation_invalid")
            continue
        target = _operation_path(example_dir, fixture_name, operation)
        relative = target.relative_to(example_dir).as_posix()
        drift_hash = _drift_hash_for_operation(operation, manifest.get("selectors"))
        if drift_hash is None:
            blocking.append(f"source_drift_hash_missing:{relative}")
        elif _sha256_file(target) != drift_hash:
            blocking.append(f"source_drift_hash_mismatch:{relative}")
    return blocking


def build_apply_readiness(
    name: str,
    candidate_id: str,
    *,
    candidate_set_path: Path,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    (
        example_dir,
        candidate_set_file,
        candidate_set,
        manifest_path,
        manifest,
        _render_manifest_path,
        render_manifest,
    ) = _load_gate_inputs(
        name,
        candidate_id,
        candidate_set_path=candidate_set_path,
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    safe_candidate_id = _candidate_id(candidate_id)
    blocking: list[str] = []
    candidate = _candidate_set_candidate(candidate_set, safe_candidate_id)
    if candidate is None:
        blocking.append("candidate_set_missing_candidate")
    elif candidate.get("candidate_hash") != manifest.get("candidate_hash"):
        blocking.append("candidate_hash_mismatch")
    if manifest.get("candidate_hash") != render_manifest.get("candidate_hash"):
        blocking.append("render_candidate_hash_mismatch")
    semantic_state = semantic_candidate_review.build_semantic_review_state(
        example_dir,
        manifest_path,
        manifest,
        spec=semantic_candidate_review.load_spec(example_dir),
    )
    blocking.extend(
        f"semantic_review:{reason}"
        for reason in semantic_candidate_review.semantic_blocking_reasons(semantic_state)
    )
    effective = manifest.get("effective_apply_authority")
    if effective != "review_only":
        blocking.append(f"effective_apply_authority:{effective}")
    blocking.extend(_render_gates(render_manifest))
    blocking.extend(_source_drift_blocks(example_dir, name, manifest))
    apply_result_path = (
        example_dir / "build" / "candidates" / safe_candidate_id / "apply_result.json"
    )
    if apply_result_path.is_file():
        apply_result = _load_json(apply_result_path, "apply_result")
        if apply_result.get("status") in TERMINAL_APPLY_STATUSES:
            blocking.append("already_applied")
    candidate_set_relative = _fixture_relative(example_dir, candidate_set_file)
    status = "ready_for_local_acceptance" if not blocking else "blocked"
    return {
        "schema": READINESS_SCHEMA,
        "figure_name": name,
        "candidate_id": safe_candidate_id,
        "candidate_set_path": candidate_set_relative,
        "status": status,
        "blocking_reasons": blocking,
        "required_commands": []
        if blocking
        else [
            (
                f"fig-agent accept-candidate {name} {safe_candidate_id} "
                f"--candidate-set {candidate_set_relative} "
                "--decision accept --reviewer <name> --rationale <text> --json"
            ),
            (
                f"fig-agent apply-candidate {name} {safe_candidate_id} "
                f"--candidate-set {candidate_set_relative} "
                f"--acceptance build/candidates/{safe_candidate_id}/acceptance.json --json"
            ),
        ],
    }


def write_acceptance(
    name: str,
    candidate_id: str,
    *,
    candidate_set_path: Path,
    decision: str,
    reviewer: str,
    rationale: str,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    if decision not in ACCEPTANCE_DECISIONS:
        raise CandidateAcceptanceError("decision must be accept, reject, or defer")
    if not reviewer.strip() or not rationale.strip():
        raise CandidateAcceptanceError("reviewer and rationale are required")
    (
        example_dir,
        candidate_set_file,
        _candidate_set,
        manifest_path,
        manifest,
        render_manifest_path,
        _render_manifest,
    ) = _load_gate_inputs(
        name,
        candidate_id,
        candidate_set_path=candidate_set_path,
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    if decision == "accept":
        readiness = build_apply_readiness(
            name,
            candidate_id,
            candidate_set_path=candidate_set_path,
            workspace_root=workspace_root,
            plugin_root=plugin_root,
        )
        if readiness["status"] != "ready_for_local_acceptance":
            raise CandidateAcceptanceError("candidate is not ready for local acceptance")
    acceptance_path = manifest_path.parent / "acceptance.json"
    if acceptance_path.is_symlink():
        raise CandidateAcceptanceError("sandbox_symlink_forbidden: acceptance.json")
    payload = {
        "schema": ACCEPTANCE_SCHEMA,
        "figure_name": name,
        "candidate_id": candidate_id,
        "candidate_hash": manifest.get("candidate_hash"),
        "candidate_set_path": _fixture_relative(example_dir, candidate_set_file),
        "candidate_manifest_path": _fixture_relative(example_dir, manifest_path),
        "candidate_manifest_sha256": _sha256_file(manifest_path),
        "render_manifest_path": _fixture_relative(example_dir, render_manifest_path),
        "render_manifest_sha256": _sha256_file(render_manifest_path),
        "decision": decision,
        "reviewer": reviewer,
        "reviewed_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00",
            "Z",
        ),
        "rationale": rationale,
        "human_review_required": True,
    }
    acceptance_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "schema": "figure-agent.candidate-acceptance-write-result.v1",
        "figure_name": name,
        "candidate_id": candidate_id,
        "path": _fixture_relative(example_dir, acceptance_path),
    }
