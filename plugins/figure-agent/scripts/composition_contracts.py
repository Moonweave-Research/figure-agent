from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths

COMPOSITION_CANDIDATE_SET_SCHEMA = "figure-agent.composition-candidate-set.v1"
FRESHNESS_VECTOR_SCHEMA = "figure-agent.freshness-vector.v1"
GENERATION_FIELDS = frozenset({"model_prompt", "model_payload", "executable_payload"})
FRESHNESS_AXES = {
    "source": "tex_hash",
    "render": "render_hash",
    "scene_model": "scene_model_hash",
    "composition_lint": "composition_lint_hash",
}


def _workspace_root(workspace_root: Path | None) -> Path:
    return runtime_paths.resolve_runtime_paths(workspace_root=workspace_root).workspace_root


def _diagnostic(code: str, message: str, field: str | None = None) -> dict[str, str]:
    payload = {"code": code, "message": message}
    if field is not None:
        payload["field"] = field
    return payload


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return payload


def _proposal_path(path: Path, workspace_root: Path) -> Path:
    return path if path.is_absolute() else workspace_root / path


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _source_path(name: str, workspace_root: Path) -> Path:
    return workspace_root / "examples" / name / f"{name}.tex"


def _axis_status(captured: str | None, current: str | None) -> str:
    if captured is None or current is None:
        return "unknown"
    if captured == current:
        return "fresh"
    return "stale"


def _freshness_vector(name: str, payload: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    raw_base = payload.get("base")
    base = raw_base if isinstance(raw_base, dict) else {}
    captured = {
        key: value
        for key, value in base.items()
        if isinstance(key, str) and isinstance(value, str)
    }
    current: dict[str, str] = {}
    tex_hash = _sha256_file(_source_path(name, workspace_root))
    if tex_hash is not None:
        current["tex_hash"] = tex_hash

    status = {
        axis: _axis_status(captured.get(hash_key), current.get(hash_key))
        for axis, hash_key in FRESHNESS_AXES.items()
    }
    stale_fields = [axis for axis, state in status.items() if state == "stale"]
    return {
        "schema": FRESHNESS_VECTOR_SCHEMA,
        "captured": captured,
        "current": current,
        "status": status,
        "stale_fields": stale_fields,
        "blocking_for": ["rank", "apply"] if stale_fields else [],
    }


def _base(payload: dict[str, Any]) -> dict[str, Any]:
    raw_base = payload.get("base")
    if not isinstance(raw_base, dict):
        return {}
    return raw_base


def _has_stale_evidence(freshness_vector: dict[str, Any] | None) -> bool:
    if freshness_vector is None:
        return False
    status = freshness_vector.get("status")
    if not isinstance(status, dict):
        return False
    return any(value == "stale" for value in status.values())


def _sanitized_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return []
    sanitized: list[dict[str, Any]] = []
    for candidate in candidates:
        if isinstance(candidate, dict):
            sanitized.append(
                {key: value for key, value in candidate.items() if key not in GENERATION_FIELDS}
            )
    return sanitized


def capture_composition_candidates(
    name: str,
    *,
    proposal_json_path: Path,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    workspace = _workspace_root(workspace_root)
    payload = _load_json(_proposal_path(proposal_json_path, workspace))
    for field in ("model_prompt", "model_payload", "executable_payload"):
        if field in payload:
            return {
                "status": "rejected",
                "diagnostics": [
                    _diagnostic(
                        "goal_generation_forbidden",
                        "plugin-side model generation is not allowed",
                        field,
                    )
                ],
            }
    return {
        "schema": COMPOSITION_CANDIDATE_SET_SCHEMA,
        "fixture": name,
        "status": "proposed_unranked",
        "authority": payload.get("authority", "creative_review_only"),
        "capture_policy": {
            "mode": "host_authored",
            "model_calls_allowed": False,
            "executable_payload_allowed": False,
        },
        "base": _base(payload),
        "freshness_vector": _freshness_vector(name, payload, workspace),
        "candidates": _sanitized_candidates(payload),
        "diagnostics": [],
    }


def rank_composition_candidates(
    name: str,
    *,
    candidate_set: dict[str, Any],
    freshness_vector: dict[str, Any] | None = None,
    lint_packet: dict[str, Any] | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    _workspace_root(workspace_root)
    if _has_stale_evidence(freshness_vector):
        return {
            "status": "proposed_unranked",
            "diagnostics": [
                _diagnostic(
                    "stale_evidence_proposed_unranked",
                    "fresh evidence is required before ranking",
                )
            ],
        }
    return {"status": "ranked", "blockers": [], "diagnostics": []}


def apply_composition_candidate(
    name: str,
    *,
    candidate_set: dict[str, Any],
    freshness_vector: dict[str, Any] | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    _workspace_root(workspace_root)
    if _has_stale_evidence(freshness_vector):
        return {
            "status": "blocked",
            "diagnostics": [_diagnostic("refresh_required", "fresh evidence is required")],
        }
    return {
        "status": "blocked",
        "source_mutation_allowed": False,
        "diagnostics": [
            _diagnostic(
                "source_mutation_not_implemented",
                "P6 records local acceptance readiness only; fixture source mutation is disabled",
            )
        ],
    }


def validate_candidate_operation(
    operation: dict[str, Any],
    *,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    _workspace_root(workspace_root)
    selector = operation.get("selector")
    diagnostics: list[dict[str, str]] = []
    if isinstance(selector, dict) and selector.get("kind") == "line_range":
        diagnostics.append(
            _diagnostic(
                "line_range_selector_read_only",
                "composition operations must target semantic blocks",
                "selector",
            )
        )
    if operation.get("kind") != "replace_semantic_block":
        diagnostics.append(
            _diagnostic("operation_kind_unsupported", "unsupported operation", "kind")
        )
    if not isinstance(operation.get("replacement_text"), str):
        diagnostics.append(
            _diagnostic(
                "replacement_text_missing",
                "replacement text is required",
                "replacement_text",
            )
        )
    if diagnostics:
        return {"status": "invalid", "operation": operation, "diagnostics": diagnostics}
    return {"status": "valid", "operation": operation, "diagnostics": []}


def validate_composition_acceptance(
    acceptance: dict[str, Any],
    *,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    _workspace_root(workspace_root)
    return {
        "status": "accepted",
        "accepted_hashes": acceptance.get("accepted_hashes", {}),
        "permissions_granted": acceptance.get("permissions_granted", []),
        "diagnostics": [],
    }
