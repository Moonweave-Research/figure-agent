"""Hash-gated apply for bounded TikZ candidate packets."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import fixture_identity

SCHEMA = "figure-agent.bounded-tikz-apply-result.v1"
CANDIDATE_PACKET_SCHEMA = "figure-agent.bounded-tikz-candidate-packet.v1"
MUTATION_BOUNDARY = "source_mutation_allowed"


class BoundedTikzCandidateApplyError(ValueError):
    """Raised when bounded TikZ apply would escape the source boundary."""


def apply_bounded_tikz_candidate(
    fixture: str,
    *,
    workspace_root: Path,
    candidate_packet: dict[str, Any],
    apply: bool,
) -> dict[str, Any]:
    """Validate and optionally apply one hash-bound bounded TikZ candidate."""

    _validate_fixture(fixture)
    diagnostics = _packet_diagnostics(fixture, candidate_packet)
    candidate = (
        candidate_packet.get("candidate") if isinstance(candidate_packet, dict) else None
    )
    if diagnostics or not isinstance(candidate, dict):
        return _blocked(fixture, diagnostics or [_diagnostic("candidate_missing")])
    operation = _single_operation(candidate)
    if operation is None:
        return _blocked(fixture, [_diagnostic("operation_invalid")])
    source_path = _source_path(workspace_root, fixture, operation)
    if source_path.is_symlink():
        raise BoundedTikzCandidateApplyError("source_symlink_forbidden")
    try:
        current_source_hash = _file_sha256(source_path)
    except OSError as exc:
        raise BoundedTikzCandidateApplyError("source_missing") from exc
    if current_source_hash != candidate.get("source_hash"):
        return _blocked(fixture, [_diagnostic("source_hash_mismatch")])
    lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
    selector = candidate.get("selector") if isinstance(candidate.get("selector"), dict) else {}
    line_number = selector.get("start_line")
    if not isinstance(line_number, int) or line_number < 1 or line_number > len(lines):
        return _blocked(fixture, [_diagnostic("selector_line_invalid")])
    current_line = lines[line_number - 1].rstrip("\n")
    if _canonical_hash(current_line) != selector.get("original_hash"):
        return _blocked(fixture, [_diagnostic("selector_hash_mismatch")])
    original = operation.get("original")
    replacement = operation.get("replacement")
    if current_line != original or not isinstance(replacement, str):
        return _blocked(fixture, [_diagnostic("operation_original_mismatch")])

    changed_file = {
        "path": str(operation["path"]),
        "source_hash_before": current_source_hash,
        "selector_hash": selector.get("original_hash"),
        "line": line_number,
    }
    if apply:
        newline = "\n" if lines[line_number - 1].endswith("\n") else ""
        lines[line_number - 1] = replacement + newline
        source_path.write_text("".join(lines), encoding="utf-8")
        changed_file["source_hash_after"] = _file_sha256(source_path)
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "candidate_id": candidate.get("id"),
        "status": "applied" if apply else "ready",
        "applied": apply,
        "mutation_boundary": MUTATION_BOUNDARY if apply else "no_source_mutation",
        "changed_files": [changed_file],
        "required_commands": (
            _post_apply_commands(fixture) if apply else _required_commands(candidate)
        ),
        "diagnostics": [],
    }


def _validate_fixture(fixture: str) -> None:
    try:
        fixture_identity.validate_fixture_name(fixture)
    except ValueError as exc:
        raise BoundedTikzCandidateApplyError(f"fixture_invalid:{fixture}") from exc


def _packet_diagnostics(fixture: str, packet: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    if not isinstance(packet, dict) or packet.get("schema") != CANDIDATE_PACKET_SCHEMA:
        diagnostics.append(_diagnostic("candidate_packet_schema_invalid"))
        return diagnostics
    if packet.get("fixture") != fixture:
        diagnostics.append(_diagnostic("fixture_mismatch"))
    if packet.get("state") != "candidate_packet_ready_for_human_review":
        diagnostics.append(_diagnostic("candidate_packet_not_ready"))
    if packet.get("authorizes_source_mutation") is not False:
        diagnostics.append(_diagnostic("candidate_packet_authorizes_mutation"))
    return diagnostics


def _single_operation(candidate: dict[str, Any]) -> dict[str, Any] | None:
    operations = candidate.get("operations")
    if not isinstance(operations, list) or len(operations) != 1:
        return None
    operation = operations[0]
    if not isinstance(operation, dict) or operation.get("kind") != "replace_text":
        return None
    text_keys = ("path", "original", "replacement")
    if not all(isinstance(operation.get(key), str) for key in text_keys):
        return None
    return operation


def _source_path(workspace_root: Path, fixture: str, operation: dict[str, Any]) -> Path:
    raw = operation.get("path")
    if not isinstance(raw, str):
        raise BoundedTikzCandidateApplyError("operation_path_missing")
    path = Path(raw)
    expected = Path("examples") / fixture / f"{fixture}.tex"
    if path != expected:
        raise BoundedTikzCandidateApplyError("operation_path_forbidden")
    target = workspace_root / path
    try:
        target.resolve().relative_to((workspace_root / "examples" / fixture).resolve())
    except ValueError as exc:
        raise BoundedTikzCandidateApplyError("operation_path_escape") from exc
    return target


def _required_commands(candidate: dict[str, Any]) -> list[str]:
    verification = candidate.get("verification")
    commands = verification.get("required_commands") if isinstance(verification, dict) else None
    if not isinstance(commands, list):
        return []
    return [command for command in commands if isinstance(command, str)]


def _post_apply_commands(fixture: str) -> list[str]:
    return [
        f"fig-agent compile {fixture} --strict",
        f"fig-agent status {fixture} --json",
    ]


def _blocked(fixture: str, diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "candidate_id": None,
        "status": "blocked",
        "applied": False,
        "mutation_boundary": "no_source_mutation",
        "changed_files": [],
        "required_commands": [],
        "diagnostics": diagnostics,
    }


def _diagnostic(code: str) -> dict[str, str]:
    return {"code": code}


def _file_sha256(path: Path) -> str:
    digest = sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + sha256(encoded).hexdigest()
