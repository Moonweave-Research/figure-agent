"""Read-only resolution of the authoritative closed-loop attempt leaf."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import closed_loop_attempt_state

SCHEMA = "figure-agent.closed-loop-current-state.v1"
PUBLICATION_ACCEPTANCE = "not_claimed"

_STATE_FILE = re.compile(r"^state-(?P<sequence>[0-9]{3})-[a-z_]+\.json$")


def _projection(
    fixture: str,
    *,
    resolution: str,
    reason: str,
    leaf: Mapping[str, Any] | None = None,
    path: Path | None = None,
    workspace_root: Path,
) -> dict[str, Any]:
    root = Path(os.path.abspath(workspace_root))
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "resolution": resolution,
        "reason": reason,
        "attempt_id": leaf["attempt_id"] if leaf is not None else None,
        "sequence": leaf["sequence"] if leaf is not None else None,
        "path": path.relative_to(root).as_posix() if path is not None else None,
        "state_sha256": leaf["state_sha256"] if leaf is not None else None,
        "state": leaf["state"] if leaf is not None else None,
        "disposition": leaf["disposition"] if leaf is not None else None,
        "required_actor": leaf["required_actor"] if leaf is not None else None,
        "terminal": leaf["terminal"] if leaf is not None else None,
        "publication_acceptance": PUBLICATION_ACCEPTANCE,
    }


def _fixture_root(workspace_root: Path, fixture: str) -> Path:
    if (
        not isinstance(fixture, str)
        or not fixture
        or fixture in {".", ".."}
        or "/" in fixture
        or "\\" in fixture
    ):
        raise ValueError("fixture_invalid")
    root = Path(os.path.abspath(workspace_root))
    examples = root / "examples"
    fixture_root = examples / fixture
    if examples.is_symlink() or fixture_root.is_symlink():
        raise ValueError("fixture_symlink")
    if not fixture_root.is_dir():
        raise ValueError("fixture_missing")
    return fixture_root


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("state_json_invalid") from exc
    if not isinstance(payload, dict):
        raise ValueError("state_payload_invalid")
    return payload


def _validated_attempt(
    attempt_root: Path,
    *,
    workspace_root: Path,
    require_live_evidence: bool,
) -> tuple[dict[str, Any], Path]:
    state_files: list[tuple[int, Path]] = []
    seen_sequences: set[int] = set()
    for entry in attempt_root.iterdir():
        if not entry.name.startswith("state-"):
            continue
        if entry.is_symlink():
            raise ValueError("state_symlink")
        match = _STATE_FILE.fullmatch(entry.name)
        if match is None or not entry.is_file():
            raise ValueError("state_filename_invalid")
        sequence = int(match.group("sequence"))
        if sequence in seen_sequences:
            raise RuntimeError("duplicate_state_sequence")
        seen_sequences.add(sequence)
        state_files.append((sequence, entry))
    if not state_files:
        raise ValueError("attempt_state_missing")
    state_files.sort(key=lambda item: item[0])
    if [sequence for sequence, _ in state_files] != list(range(len(state_files))):
        raise ValueError("state_sequence_broken")

    states: list[dict[str, Any]] = []
    for sequence, path in state_files:
        payload = _load_json(path)
        try:
            state = closed_loop_attempt_state.validate_state(
                payload,
                workspace_root=workspace_root,
                _require_live_evidence=require_live_evidence,
            )
            canonical_path = closed_loop_attempt_state.state_path(
                state,
                workspace_root=workspace_root,
            )
        except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
            raise ValueError(f"state_invalid:{exc}") from exc
        if state["sequence"] != sequence or canonical_path != path:
            raise ValueError("state_path_mismatch")
        if state["attempt_id"] != attempt_root.name:
            raise ValueError("attempt_directory_mismatch")
        states.append(state)

    chain_args: dict[str, Any] = {}
    first = states[0]
    parent_path_value = first["parent_state_path"]
    if parent_path_value is not None:
        parent_path = Path(os.path.abspath(workspace_root)) / parent_path_value
        if parent_path.is_symlink():
            raise ValueError("parent_state_symlink")
        chain_args = {
            "parent_state": _load_json(parent_path),
            "parent_state_path": parent_path,
        }
    if require_live_evidence:
        try:
            closed_loop_attempt_state.validate_chain(
                states,
                workspace_root=workspace_root,
                **chain_args,
            )
        except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
            raise ValueError(f"state_chain_invalid:{exc}") from exc
    return states[-1], state_files[-1][1]


def resolve_current_attempt(workspace_root: Path, fixture: str) -> dict[str, Any]:
    """Project one authoritative attempt leaf, failing closed on unsafe discovery."""
    root = Path(os.path.abspath(workspace_root))
    try:
        fixture_root = _fixture_root(root, fixture)
    except ValueError as exc:
        resolution = "absent" if str(exc) == "fixture_missing" else "invalid"
        return _projection(
            fixture,
            resolution=resolution,
            reason=str(exc),
            workspace_root=root,
        )
    review_root = fixture_root / "review"
    closed_loop_root = review_root / "closed-loop"
    if review_root.is_symlink() or closed_loop_root.is_symlink():
        return _projection(
            fixture,
            resolution="invalid",
            reason="closed_loop_root_symlink",
            workspace_root=root,
        )
    if not closed_loop_root.exists():
        return _projection(
            fixture,
            resolution="absent",
            reason="no_attempt_states",
            workspace_root=root,
        )
    if not closed_loop_root.is_dir():
        return _projection(
            fixture,
            resolution="invalid",
            reason="closed_loop_root_invalid",
            workspace_root=root,
        )

    leaves: list[tuple[dict[str, Any], Path]] = []
    attempt_entries = sorted(
        (entry for entry in closed_loop_root.iterdir() if entry.name.startswith("attempt-")),
        key=lambda entry: entry.name,
    )
    if not attempt_entries:
        return _projection(
            fixture,
            resolution="absent",
            reason="no_attempt_states",
            workspace_root=root,
        )
    for attempt_root in attempt_entries:
        if attempt_root.is_symlink():
            return _projection(
                fixture,
                resolution="invalid",
                reason="attempt_symlink",
                workspace_root=root,
            )
        if not attempt_root.is_dir():
            return _projection(
                fixture,
                resolution="invalid",
                reason="attempt_directory_invalid",
                workspace_root=root,
            )
        try:
            leaves.append(
                _validated_attempt(
                    attempt_root,
                    workspace_root=root,
                    require_live_evidence=False,
                )
            )
        except RuntimeError as exc:
            return _projection(
                fixture,
                resolution="ambiguous",
                reason=str(exc),
                workspace_root=root,
            )
        except ValueError as exc:
            return _projection(
                fixture,
                resolution="invalid",
                reason=str(exc),
                workspace_root=root,
            )

    nonterminal = [leaf for leaf in leaves if not leaf[0]["terminal"]]
    if len(nonterminal) > 1:
        return _projection(
            fixture,
            resolution="ambiguous",
            reason="multiple_nonterminal_attempts",
            workspace_root=root,
        )
    if len(nonterminal) == 1:
        leaf, path = nonterminal[0]
    else:
        parent_attempt_ids: set[str] = set()
        for candidate, _ in leaves:
            parent_path = candidate.get("parent_state_path")
            if not isinstance(parent_path, str):
                continue
            parts = Path(parent_path).parts
            try:
                closed_loop_index = parts.index("closed-loop")
                parent_attempt_ids.add(parts[closed_loop_index + 1])
            except (ValueError, IndexError):
                return _projection(
                    fixture,
                    resolution="invalid",
                    reason="parent_attempt_path_invalid",
                    workspace_root=root,
                )
        graph_leaves = [
            candidate
            for candidate in leaves
            if candidate[0]["attempt_id"] not in parent_attempt_ids
        ]
        if len(graph_leaves) != 1:
            return _projection(
                fixture,
                resolution="ambiguous",
                reason="multiple_terminal_attempts",
                workspace_root=root,
            )
        leaf, path = graph_leaves[0]
    try:
        leaf, path = _validated_attempt(
            path.parent,
            workspace_root=root,
            require_live_evidence=True,
        )
    except (RuntimeError, ValueError) as exc:
        return _projection(
            fixture,
            resolution="invalid",
            reason=str(exc),
            workspace_root=root,
        )
    return _projection(
        fixture,
        resolution="current",
        reason="one_current_attempt",
        leaf=leaf,
        path=path,
        workspace_root=root,
    )
