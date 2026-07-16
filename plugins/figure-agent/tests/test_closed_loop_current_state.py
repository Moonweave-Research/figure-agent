from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import closed_loop_current_state


def _workspace(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "demo"
    fixture.mkdir(parents=True)
    render = fixture / "build" / "demo.png"
    render.parent.mkdir()
    render.write_bytes(b"render-v1")
    return workspace, render


def _artifact(render: Path, name: str) -> Path:
    path = render.parents[1] / name
    path.write_text(name + "\n", encoding="utf-8")
    return path


def _root_evidence(render: Path, suffix: str = "") -> dict[str, Path]:
    return {
        "attempt_manifest": _artifact(render, f"attempt-manifest{suffix}.json"),
        "authored_source": _artifact(render, f"authored-source{suffix}.tex"),
        "render": render,
    }


def _start(
    workspace: Path,
    render: Path,
    *,
    suffix: str = "",
) -> tuple[dict[str, Any], Path]:
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-1",
        actor_role="authoring_agent",
        evidence=_root_evidence(render, suffix),
    )
    path = closed_loop_attempt_state.publish_state(state, workspace_root=workspace)
    return state, path


def _abort(
    workspace: Path,
    render: Path,
    state: dict[str, Any],
    state_path: Path,
    *,
    suffix: str = "",
) -> tuple[dict[str, Any], Path]:
    evidence = _artifact(render, f"abort{suffix}.json")
    terminal = closed_loop_attempt_state.transition_state(
        state,
        next_state="aborted",
        actor="workflow-1",
        actor_role="workflow_agent",
        evidence={"abort_record": evidence},
        workspace_root=workspace,
        previous_state_path=state_path,
    )
    return terminal, closed_loop_attempt_state.publish_state(
        terminal, workspace_root=workspace
    )


def _advance(
    workspace: Path,
    render: Path,
    state: dict[str, Any],
    state_path: Path,
    next_state: str,
    roles: tuple[str, ...],
) -> tuple[dict[str, Any], Path]:
    evidence = {
        role: _artifact(render, f"{state['sequence'] + 1}-{next_state}-{role}.json")
        for role in roles
    }
    advanced = closed_loop_attempt_state.transition_state(
        state,
        next_state=next_state,
        actor=f"{state['required_actor']}-1",
        actor_role=state["required_actor"],
        evidence=evidence,
        workspace_root=workspace,
        previous_state_path=state_path,
    )
    return advanced, closed_loop_attempt_state.publish_state(
        advanced,
        workspace_root=workspace,
    )


def test_no_attempt_directory_projects_absent_without_claiming_publication(
    tmp_path: Path,
) -> None:
    workspace, _ = _workspace(tmp_path)

    result = closed_loop_current_state.resolve_current_attempt(workspace, "demo")

    assert result == {
        "schema": "figure-agent.closed-loop-current-state.v1",
        "fixture": "demo",
        "resolution": "absent",
        "reason": "no_attempt_states",
        "attempt_id": None,
        "sequence": None,
        "path": None,
        "state_sha256": None,
        "state": None,
        "disposition": None,
        "required_actor": None,
        "terminal": None,
        "publication_acceptance": "not_claimed",
    }


def test_missing_fixture_is_absent_so_stage_zero_can_scaffold(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples").mkdir(parents=True)

    result = closed_loop_current_state.resolve_current_attempt(workspace, "demo")

    assert result["resolution"] == "absent"
    assert result["reason"] == "fixture_missing"
    assert result["publication_acceptance"] == "not_claimed"


def test_exactly_one_valid_leaf_projects_canonical_lineage_not_mtime(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    state, state_file = _start(workspace, render)

    result = closed_loop_current_state.resolve_current_attempt(workspace, "demo")

    assert result["resolution"] == "current"
    assert result["reason"] == "one_current_attempt"
    assert result["attempt_id"] == state["attempt_id"]
    assert result["sequence"] == 0
    assert result["path"] == state_file.relative_to(workspace).as_posix()
    assert result["state_sha256"] == state["state_sha256"]
    assert result["state"] == "authored_rendered"
    assert result["disposition"] == "continue"
    assert result["required_actor"] == "workflow_agent"
    assert result["terminal"] is False
    assert result["publication_acceptance"] == "not_claimed"


def test_terminal_development_state_can_never_project_publication_acceptance(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    state, state_file = _start(workspace, render)
    terminal, _ = _abort(workspace, render, state, state_file)

    result = closed_loop_current_state.resolve_current_attempt(workspace, "demo")

    assert result["resolution"] == "current"
    assert result["state"] == "aborted"
    assert result["terminal"] is True
    assert terminal["publication_acceptance"] == "not_claimed"
    assert result["publication_acceptance"] == "not_claimed"


def test_stale_evidence_and_broken_lineage_project_invalid_fail_closed(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    state, state_file = _start(workspace, render)
    terminal, _ = _abort(workspace, render, state, state_file)
    assert terminal["sequence"] == 1
    state_file.write_text("{}\n", encoding="utf-8")

    result = closed_loop_current_state.resolve_current_attempt(workspace, "demo")

    assert result["resolution"] == "invalid"
    assert result["reason"].startswith("state_invalid:")
    assert result["path"] is None
    assert result["publication_acceptance"] == "not_claimed"


def test_state_symlink_projects_invalid_without_following_it(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    state, state_file = _start(workspace, render)
    payload = state_file.read_bytes()
    state_file.unlink()
    target = tmp_path / "outside-state.json"
    target.write_bytes(payload)
    state_file.symlink_to(target)

    result = closed_loop_current_state.resolve_current_attempt(workspace, "demo")

    assert result["resolution"] == "invalid"
    assert result["reason"] == "state_symlink"


def test_duplicate_sequence_leaf_projects_ambiguous_even_if_one_is_newer(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    state, state_file = _start(workspace, render)
    duplicate = state_file.with_name("state-000-aborted.json")
    duplicate.write_text(json.dumps(state), encoding="utf-8")

    result = closed_loop_current_state.resolve_current_attempt(workspace, "demo")

    assert result["resolution"] == "ambiguous"
    assert result["reason"] == "duplicate_state_sequence"


def test_two_nonterminal_attempts_project_ambiguous(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    _start(workspace, render, suffix="-one")
    second_render = render.with_name("demo-second.png")
    second_render.write_bytes(b"render-v2")
    _start(workspace, second_render, suffix="-two")

    result = closed_loop_current_state.resolve_current_attempt(workspace, "demo")

    assert result["resolution"] == "ambiguous"
    assert result["reason"] == "multiple_nonterminal_attempts"
    assert result["attempt_id"] is None


def test_one_nonterminal_attempt_is_current_over_terminal_history(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    old_state, old_path = _start(workspace, render, suffix="-old")
    _abort(workspace, render, old_state, old_path, suffix="-old")
    current_render = render.with_name("demo-current.png")
    current_render.write_bytes(b"render-current")
    current, current_path = _start(workspace, current_render, suffix="-current")

    result = closed_loop_current_state.resolve_current_attempt(workspace, "demo")

    assert result["resolution"] == "current"
    assert result["attempt_id"] == current["attempt_id"]
    assert result["path"] == current_path.relative_to(workspace).as_posix()


def test_unrelated_stale_terminal_history_does_not_block_valid_current_attempt(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    old_state, old_path = _start(workspace, render, suffix="-old-stale")
    _abort(workspace, render, old_state, old_path, suffix="-old-stale")
    (render.parents[1] / "attempt-manifest-old-stale.json").write_text(
        "stale\n",
        encoding="utf-8",
    )
    current_render = render.with_name("demo-live-current.png")
    current_render.write_bytes(b"render-current")
    current, current_path = _start(
        workspace,
        current_render,
        suffix="-live-current",
    )

    result = closed_loop_current_state.resolve_current_attempt(workspace, "demo")

    assert result["resolution"] == "current"
    assert result["attempt_id"] == current["attempt_id"]
    assert result["path"] == current_path.relative_to(workspace).as_posix()


def test_parent_link_selects_unique_terminal_descendant(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    parent, parent_path = _start(workspace, render, suffix="-parent")
    for next_state, roles in (
        ("critique_unadjudicated", ("critique", "host_review_execution_receipt")),
        ("repair_bound", ("adjudicated_repair_binding",)),
        (
            "repair_candidate_ready",
            ("repair_execution_packet", "repair_response", "materialization_preview"),
        ),
        ("repair_authorized", ("human_authorization",)),
        ("repair_required", ("repair_failure_record",)),
    ):
        parent, parent_path = _advance(
            workspace,
            render,
            parent,
            parent_path,
            next_state,
            roles,
        )
    parent_terminal = parent
    parent_terminal_path = parent_path
    child_render = render.with_name("demo-child.png")
    child_render.write_bytes(b"render-child")
    child = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-2",
        actor_role="authoring_agent",
        evidence=_root_evidence(child_render, "-child"),
        parent_state=parent_terminal,
        parent_state_path=parent_terminal_path,
    )
    child_path = closed_loop_attempt_state.publish_state(
        child,
        workspace_root=workspace,
    )
    child_terminal, child_terminal_path = _abort(
        workspace,
        child_render,
        child,
        child_path,
        suffix="-child",
    )

    result = closed_loop_current_state.resolve_current_attempt(workspace, "demo")

    assert result["resolution"] == "current"
    assert result["attempt_id"] == child_terminal["attempt_id"]
    assert result["path"] == child_terminal_path.relative_to(workspace).as_posix()
