"""Shared contracts for candidate-search artifacts."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import fixture_identity

APPLY_AUTHORITIES = frozenset({"apply_eligible", "review_only", "rejected"})
HARD_GATE_STATES = frozenset({"pass", "human_required", "rejected"})


class CandidateContractError(ValueError):
    """Expected user-facing candidate contract error."""


def canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + sha256(encoded).hexdigest()


def fixture_relative_path(example_dir: Path, value: str) -> Path:
    candidate = (example_dir / value).resolve()
    try:
        candidate.relative_to(example_dir.resolve())
    except ValueError as exc:
        raise CandidateContractError("path_escape") from exc
    return candidate


def fixture_local_output_path(workspace_root: Path, fixture_name: str, value: str) -> Path:
    fixture_identity.validate_fixture_name(fixture_name)
    example_dir = workspace_root / "examples" / fixture_name
    return fixture_relative_path(example_dir, value)


def effective_apply_authority(apply_authority: str, hard_gate_state: str) -> str:
    if apply_authority not in APPLY_AUTHORITIES:
        raise CandidateContractError(f"invalid apply_authority: {apply_authority}")
    if hard_gate_state not in HARD_GATE_STATES:
        raise CandidateContractError(f"invalid hard_gate_state: {hard_gate_state}")
    if hard_gate_state == "rejected":
        return "rejected"
    if hard_gate_state == "human_required":
        return "review_only"
    return apply_authority
