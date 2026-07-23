"""Read the explicit fixture-local current-candidate pointer.

The pointer is deliberately advisory: it identifies the candidate evidence
that status should surface, but it never promotes a nested repair to the
fixture's canonical source or release state.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CURRENT_CANDIDATE_SCHEMA = "figure-agent.current-candidate-pointer.v1"
POINTER_RELATIVE_PATH = Path("review") / "current-candidate.json"
_EVIDENCE_KEYS = {
    "render_pdf": "render_pdf",
    "render_png": "render_png",
    "strict_status": "strict_status",
    "physics_grounding": "physics_grounding",
    "text_boundary_clash": "text_boundary_clash",
    "label_path_proximity": "label_path_proximity",
}


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_path(root: Path, relative: object) -> Path | None:
    if not isinstance(relative, str) or not relative.strip():
        return None
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _artifact_state(source: Path, artifact: Path | None) -> str:
    if artifact is None or not artifact.is_file():
        return "MISSING"
    if source.is_file() and artifact.stat().st_mtime < source.stat().st_mtime:
        return "STALE"
    return "FRESH"


def _strict_state(path: Path | None) -> str:
    if path is None or not path.is_file():
        return "MISSING"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "INVALID"
    if payload.get("schema") != "figure-agent.strict-status.v1":
        return "INVALID"
    state = payload.get("state")
    return state if state in {"not_requested", "passed", "failed"} else "INVALID"


def _physics_state(path: Path | None) -> str:
    if path is None or not path.is_file():
        return "UNDECLARED"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "INVALID"
    if not isinstance(payload, dict):
        return "INVALID"
    status = payload.get("status")
    return str(status) if status else "UNDECLARED"


def _checked_count(path: Path | None) -> int | None:
    """Read a detector's declared-check count without treating missing evidence as green."""

    if path is None or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    value = payload.get("checked") if isinstance(payload, dict) else None
    return value if isinstance(value, int) and value >= 0 else None


def resolve_current_candidate(example_dir: Path) -> dict[str, Any]:
    """Return an explicit candidate summary without changing stage inference."""

    pointer_path = example_dir / POINTER_RELATIVE_PATH
    base = {"path": POINTER_RELATIVE_PATH.as_posix(), "state": "NOT_DECLARED"}
    if not pointer_path.is_file():
        return base
    try:
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {**base, "state": "INVALID", "reason": "pointer_not_valid_json"}
    if not isinstance(pointer, dict):
        return {**base, "state": "INVALID", "reason": "pointer_not_mapping"}
    if pointer.get("schema") != CURRENT_CANDIDATE_SCHEMA:
        return {**base, "state": "INVALID", "reason": "pointer_schema_invalid"}
    if pointer.get("fixture") != example_dir.name:
        return {**base, "state": "INVALID", "reason": "pointer_fixture_mismatch"}

    candidate_root = _safe_path(example_dir, pointer.get("candidate_root"))
    source_path = _safe_path(candidate_root, pointer.get("source_path")) if candidate_root else None
    if candidate_root is None or source_path is None:
        return {**base, "state": "INVALID", "reason": "pointer_path_invalid"}
    if not candidate_root.is_dir() or not source_path.is_file():
        return {**base, "state": "INVALID", "reason": "candidate_source_missing"}
    expected_hash = pointer.get("source_sha256")
    if expected_hash is not None and expected_hash != _sha256(source_path):
        return {**base, "state": "INVALID", "reason": "candidate_source_hash_mismatch"}

    evidence = pointer.get("evidence")
    if not isinstance(evidence, dict):
        return {**base, "state": "INVALID", "reason": "pointer_evidence_invalid"}
    artifacts = {
        key: _safe_path(candidate_root, evidence.get(value))
        for key, value in _EVIDENCE_KEYS.items()
    }
    return {
        **base,
        "state": "VALID",
        "candidate_id": pointer.get("candidate_id"),
        "candidate_root": candidate_root.relative_to(example_dir).as_posix(),
        "source_path": source_path.relative_to(example_dir).as_posix(),
        "source_sha256": _sha256(source_path),
        "promotion_state": pointer.get("promotion_state", "candidate_only"),
        "human_gate": pointer.get("human_gate", "pending"),
        "render_state": _artifact_state(source_path, artifacts["render_pdf"]),
        "render_png_state": _artifact_state(source_path, artifacts["render_png"]),
        "strict_state": _strict_state(artifacts["strict_status"]),
        "physics_state": _physics_state(artifacts["physics_grounding"]),
        "text_boundary_state": _artifact_state(
            source_path, artifacts["text_boundary_clash"]
        ),
        "text_boundary_checked": _checked_count(artifacts["text_boundary_clash"]),
        "label_path_state": _artifact_state(source_path, artifacts["label_path_proximity"]),
        "label_path_checked": _checked_count(artifacts["label_path_proximity"]),
        "evidence_paths": {
            key: path.relative_to(example_dir).as_posix() if path else None
            for key, path in artifacts.items()
        },
    }
