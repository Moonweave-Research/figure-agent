"""Validate the hash-bound current-render human-review scaffold.

This is deliberately a review-state observer: it neither records a human
verdict nor changes figure source.  Its job is to stop status surfaces from
presenting a stale PDF, crop manifest, or print proxy as the current review
target after any of those artifacts have changed.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "figure-agent.current-render-review-scaffold.v1"
RELATIVE_PATH = Path("review/failure-first/current_render_review_scaffold_v1.yaml")

_SOURCE_PATHS = {
    "tex_sha256": lambda directory: directory / f"{directory.name}.tex",
    "briefing_sha256": lambda directory: directory / "briefing.md",
    "spec_sha256": lambda directory: directory / "spec.yaml",
}
_RENDER_HASH_KEYS = {
    "render_png_path": "render_png_sha256",
    "audit_crop_manifest": "audit_crop_manifest_sha256",
    "print_proxy": "print_proxy_sha256",
}


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_relative_file(directory: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    path = directory / relative
    return path if path.is_file() else None


def _invalid(path: Path, reason: str) -> dict[str, Any]:
    return {
        "state": "INVALID",
        "path": path.as_posix(),
        "reason": reason,
        "human_review_state": None,
        "stale_fields": [],
    }


def review_scaffold_summary(example_dir: Path) -> dict[str, Any]:
    """Return the current review packet state without inferring a verdict.

    `NOT_DECLARED` is benign: a fixture may not require this review surface.
    `STALE` means the declared source or review outputs no longer equal their
    bound hashes, so the packet must be regenerated before human review.
    """
    path = example_dir / RELATIVE_PATH
    if not path.is_file():
        return {
            "state": "NOT_DECLARED",
            "path": RELATIVE_PATH.as_posix(),
            "reason": None,
            "human_review_state": None,
            "stale_fields": [],
        }
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return _invalid(path, "parse_error")
    if not isinstance(payload, dict):
        return _invalid(path, "mapping_required")
    if payload.get("schema") != SCHEMA:
        return _invalid(path, "schema_invalid")
    if payload.get("fixture") != example_dir.name:
        return _invalid(path, "fixture_mismatch")

    source_inputs = payload.get("source_inputs")
    if not isinstance(source_inputs, dict):
        return _invalid(path, "source_inputs_invalid")
    stale_fields: list[str] = []
    for key, path_for in _SOURCE_PATHS.items():
        source = path_for(example_dir)
        declared = source_inputs.get(key)
        if not isinstance(declared, str) or not source.is_file():
            return _invalid(path, f"{key}_missing")
        if declared != _sha256(source):
            stale_fields.append(f"source_inputs.{key}")

    render_evidence = payload.get("render_evidence")
    if not isinstance(render_evidence, dict):
        return _invalid(path, "render_evidence_invalid")
    if _safe_relative_file(example_dir, render_evidence.get("render_path")) is None:
        return _invalid(path, "render_path_binding_missing")
    for path_key, hash_key in _RENDER_HASH_KEYS.items():
        artifact = _safe_relative_file(example_dir, render_evidence.get(path_key))
        declared = render_evidence.get(hash_key)
        if artifact is None or not isinstance(declared, str):
            return _invalid(path, f"{path_key}_binding_missing")
        if declared != _sha256(artifact):
            stale_fields.append(f"render_evidence.{hash_key}")

    machine_gate = payload.get("machine_gate")
    if (
        not isinstance(machine_gate, dict)
        or machine_gate.get("publication_acceptance") != "not_claimed"
    ):
        return _invalid(path, "machine_acceptance_boundary_invalid")
    observations = payload.get("agent_observations")
    if not isinstance(observations, list) or not observations:
        return _invalid(path, "agent_observations_missing")
    if any(
        not isinstance(item, dict)
        or not isinstance(item.get("id"), str)
        or not item["id"].strip()
        or not isinstance(item.get("question"), str)
        or not item["question"].strip()
        for item in observations
    ):
        return _invalid(path, "agent_observation_invalid")
    human_review = payload.get("human_review")
    if not isinstance(human_review, dict):
        return _invalid(path, "human_review_invalid")
    human_state = human_review.get("state")
    verdict = human_review.get("verdict")
    if human_state not in {"pending", "recorded"} or not isinstance(verdict, str) or not verdict:
        return _invalid(path, "human_review_state_invalid")
    if human_state == "pending" and verdict != "not_recorded":
        return _invalid(path, "pending_review_has_verdict")
    if human_state == "recorded" and verdict == "not_recorded":
        return _invalid(path, "recorded_review_missing_verdict")

    state = "STALE" if stale_fields else "PENDING" if human_state == "pending" else "RECORDED"
    return {
        "state": state,
        "path": RELATIVE_PATH.as_posix(),
        "reason": None,
        "human_review_state": human_state,
        "stale_fields": stale_fields,
    }
