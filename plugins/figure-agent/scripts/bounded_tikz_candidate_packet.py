"""Build read-only bounded TikZ candidate packets."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import fixture_identity

SCHEMA = "figure-agent.bounded-tikz-candidate-packet.v1"
MUTATION_BOUNDARY = "no_source_mutation"
CANDIDATE_ID = "BTIKZ001"
CANDIDATE_FAMILY = "restrained_tikz_refinement"
SOURCE_MUTATION_BOUNDARY = "source_mutation_requires_separate_approval"
TARGET_NEEDLE = r"at (3.50, 2.85) {$kT \ll E_t$\\[-1pt](escape negligible)};"
REPLACEMENT_TEXT = r"      at (3.62, 2.82) {$kT \ll E_t$\\[-1pt](escape negligible)};"
DISALLOWED_ACTIONS = [
    "do not edit figure source files from this packet",
    "do not edit generated exports or tracked golden artifacts",
    "do not apply the patch without a separate human source-mutation decision",
]


class BoundedTikzCandidatePacketError(ValueError):
    """Raised when a bounded TikZ candidate packet cannot be built safely."""


def build_bounded_tikz_candidate_packet(
    fixture: str,
    *,
    workspace_root: Path,
    request_packet: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a hash-bound candidate patch packet without writing source files."""

    _validate_fixture(fixture)
    if not _request_is_ready(request_packet):
        return _blocked_packet(
            fixture,
            state="blocked_refinement_request_not_ready",
            next_agent_action="create_ready_bounded_tikz_refinement_request",
        )
    source_rel = Path("examples") / fixture / f"{fixture}.tex"
    source_path = workspace_root / source_rel
    if source_path.is_symlink():
        raise BoundedTikzCandidatePacketError("source_symlink_forbidden")
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BoundedTikzCandidatePacketError("source_missing") from exc
    lines = source_text.splitlines()
    line_number = _find_target_line(lines)
    if line_number is None:
        return _blocked_packet(
            fixture,
            state="blocked_target_selector_missing",
            next_agent_action="refresh_candidate_selector",
        )
    original = lines[line_number - 1]
    operation = {
        "kind": "replace_text",
        "path": source_rel.as_posix(),
        "original": original,
        "replacement": REPLACEMENT_TEXT,
    }
    candidate = {
        "id": CANDIDATE_ID,
        "family": CANDIDATE_FAMILY,
        "edit_class": "label_spacing",
        "target": {
            "panel": "b",
            "subregion": "thermal_escape_label",
        },
        "source_hash": _file_sha256(source_path),
        "selector": {
            "kind": "line_range_with_hash",
            "path": source_rel.as_posix(),
            "start_line": line_number,
            "end_line": line_number,
            "original_hash": _canonical_hash(original),
            "match_text": TARGET_NEEDLE,
        },
        "operations": [operation],
        "expected_delta": [
            "increase weak thermal-escape label clearance from the escape arrow",
            "preserve kT << E_t wording and thermal-escape semantics",
        ],
        "semantic_risks": [
            "thermal escape must remain visibly weaker than injection and capture",
            "E_t label meaning and deep-trap retention story must not change",
        ],
        "rollback": {
            "strategy": "reverse_operations",
            "reverse_operations": [
                {
                    "kind": "replace_text",
                    "path": source_rel.as_posix(),
                    "original": REPLACEMENT_TEXT,
                    "replacement": original,
                }
            ],
        },
        "verification": {
            "required_commands": [
                f"fig-agent compile {fixture} --strict",
                f"fig-agent status {fixture} --json",
                f"fig-agent bounded-tikz-candidate {fixture} --json",
            ],
            "success_metrics": [
                "render_state remains FRESH after compile",
                "semantic assertions for capture/escape direction still pass",
                "no new text-boundary or visual-clash blocker is introduced",
            ],
        },
        "apply_authority": "review_only",
        "source_mutation_boundary": SOURCE_MUTATION_BOUNDARY,
        "authorizes_source_mutation": False,
    }
    candidate["candidate_hash"] = _canonical_hash(
        {
            "fixture": fixture,
            "id": CANDIDATE_ID,
            "source_hash": candidate["source_hash"],
            "selector": candidate["selector"],
            "operations": candidate["operations"],
            "source_mutation_boundary": SOURCE_MUTATION_BOUNDARY,
        }
    )
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "state": "candidate_packet_ready_for_human_review",
        "mutation_boundary": MUTATION_BOUNDARY,
        "authorizes_source_mutation": False,
        "requires_human_decision": True,
        "request_packet_schema": (request_packet or {}).get("schema"),
        "candidate": candidate,
        "human_question": (
            f"I can prepare `{CANDIDATE_ID}` as one bounded TikZ source candidate "
            f"for `{fixture}`. Should source mutation be opened for this exact patch?"
        ),
        "disallowed_actions": list(DISALLOWED_ACTIONS),
        "follow_up": {
            "if_human_approves": "run a separate apply step against this exact hash-bound patch",
            "if_human_rejects": "keep current style as benchmark",
        },
    }


def _validate_fixture(fixture: str) -> None:
    try:
        fixture_identity.validate_fixture_name(fixture)
    except ValueError as exc:
        raise BoundedTikzCandidatePacketError(f"fixture_invalid:{fixture}") from exc


def _request_is_ready(request_packet: dict[str, Any] | None) -> bool:
    if not isinstance(request_packet, dict):
        return False
    family = request_packet.get("candidate_family")
    return (
        request_packet.get("state") == "ready_for_human_source_mutation_choice"
        and request_packet.get("mutation_boundary") == MUTATION_BOUNDARY
        and request_packet.get("authorizes_source_mutation") is False
        and isinstance(family, dict)
        and family.get("id") == CANDIDATE_FAMILY
        and family.get("source_mutation_boundary") == SOURCE_MUTATION_BOUNDARY
    )


def _blocked_packet(fixture: str, *, state: str, next_agent_action: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "state": state,
        "mutation_boundary": MUTATION_BOUNDARY,
        "authorizes_source_mutation": False,
        "requires_human_decision": False,
        "request_packet_schema": None,
        "candidate": None,
        "human_question": "",
        "disallowed_actions": list(DISALLOWED_ACTIONS),
        "next_agent_action": next_agent_action,
        "follow_up": {
            "if_human_approves": "not available until the candidate packet is ready",
            "if_human_rejects": "keep current style as benchmark",
        },
    }


def _find_target_line(lines: list[str]) -> int | None:
    for index, line in enumerate(lines, start=1):
        if TARGET_NEEDLE in line:
            return index
    return None


def _file_sha256(path: Path) -> str:
    digest = sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + sha256(encoded).hexdigest()
