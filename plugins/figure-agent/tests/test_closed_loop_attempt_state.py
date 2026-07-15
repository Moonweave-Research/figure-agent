from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import pytest

_STATE_EVIDENCE_ROLES = {
    "critique_unadjudicated": ("critique", "host_review_execution_receipt"),
    "adjudicated_unbound": ("adjudication", "attribution_handoff"),
    "repair_bound": ("adjudicated_repair_binding",),
    "repair_candidate_ready": (
        "repair_execution_packet",
        "materialization_preview",
    ),
    "repair_authorized": ("human_authorization",),
    "machine_repaired": (
        "materialization_receipt",
        "machine_verification_receipt",
    ),
    "post_review_requested": ("post_repair_visual_review_request",),
    "visually_re_reviewed": (
        "post_repair_visual_review_response",
        "host_review_execution_receipt",
        "post_repair_visual_review_receipt",
    ),
    "development_accepted": ("human_decision_record",),
    "rejected": ("human_decision_record",),
    "repair_required": ("repair_failure_record",),
    "aborted": ("abort_record",),
}


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


def _root_evidence(render: Path) -> dict[str, Path]:
    return {
        "attempt_manifest": _artifact(render, f"{render.stem}-attempt-manifest.json"),
        "authored_source": _artifact(render, f"{render.stem}-authored-source.tex"),
        "render": render,
    }


def _state_evidence(render: Path, state: str, sequence: int) -> dict[str, Path]:
    return {
        role: _artifact(render, f"{sequence}-{state}-{role}.json")
        for role in _STATE_EVIDENCE_ROLES[state]
    }


def _transition(
    previous: dict[str, Any],
    state: str,
    *,
    workspace: Path,
    render: Path,
) -> dict[str, Any]:
    previous_path = closed_loop_attempt_state.state_path(
        previous, workspace_root=workspace
    )
    if not previous_path.exists():
        previous_path = closed_loop_attempt_state.publish_state(
            previous, workspace_root=workspace
        )
    return closed_loop_attempt_state.transition_state(
        previous,
        next_state=state,
        actor=f"{previous['required_actor']}-identity",
        actor_role=previous["required_actor"],
        evidence=_state_evidence(render, state, previous["sequence"] + 1),
        workspace_root=workspace,
        previous_state_path=previous_path,
    )


def test_start_attempt_has_deterministic_identity_and_canonical_state_hash(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)

    first = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    second = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )

    assert first == second
    assert first["schema"] == "figure-agent.closed-loop-attempt-state.v1"
    assert first["state"] == "authored_rendered"
    assert first["attempt_id"].startswith("attempt-")
    assert first["state_sha256"] == (
        closed_loop_attempt_state.canonical_state_sha256(first)
    )
    assert first["publication_acceptance"] == "not_claimed"
    assert closed_loop_attempt_state.validate_state(
        first, workspace_root=workspace
    ) == first


def test_unadjudicated_and_unbound_states_stop_for_the_derived_human_actor(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    initial = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    critique = render.parents[1] / "critique.md"
    critique.write_text("finding C001\n", encoding="utf-8")

    unadjudicated = closed_loop_attempt_state.transition_state(
        initial,
        next_state="critique_unadjudicated",
        actor="workflow-agent-1",
        actor_role="workflow_agent",
        evidence=_state_evidence(render, "critique_unadjudicated", 1),
        workspace_root=workspace,
        previous_state_path=closed_loop_attempt_state.publish_state(
            initial, workspace_root=workspace
        ),
    )
    assert unadjudicated["disposition"] == "human_review_required"
    assert unadjudicated["required_actor"] == "human_adjudicator"

    adjudication = render.parents[1] / "adjudication.json"
    adjudication.write_text('{"decision":"apply"}\n', encoding="utf-8")
    unbound = closed_loop_attempt_state.transition_state(
        unadjudicated,
        next_state="adjudicated_unbound",
        actor="reviewer-moon",
        actor_role="human_adjudicator",
        evidence=_state_evidence(render, "adjudicated_unbound", 2),
        workspace_root=workspace,
        previous_state_path=closed_loop_attempt_state.publish_state(
            unadjudicated, workspace_root=workspace
        ),
    )
    assert unbound["disposition"] == "human_review_required"
    assert unbound["required_actor"] == "human_attributor"


def test_valid_chain_reaches_development_acceptance_without_claiming_publication(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    chain = [
        closed_loop_attempt_state.start_attempt(
            workspace_root=workspace,
            fixture="demo",
            actor="authoring_agent",
            actor_role="authoring_agent",
            evidence=_root_evidence(render),
        )
    ]
    for state in (
        "critique_unadjudicated",
        "repair_bound",
        "repair_candidate_ready",
        "repair_authorized",
        "machine_repaired",
        "post_review_requested",
        "visually_re_reviewed",
        "development_accepted",
    ):
        chain.append(
            _transition(chain[-1], state, workspace=workspace, render=render)
        )

    assert closed_loop_attempt_state.validate_chain(
        chain, workspace_root=workspace
    ) == chain
    assert chain[-1]["terminal"] is True
    assert chain[-1]["actor"] == "human_reviewer-identity"
    assert chain[-1]["actor_role"] == "human_reviewer"
    assert chain[-1]["publication_acceptance"] == "not_claimed"


def test_transition_rejects_actor_mismatch_and_illegal_skip(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    initial = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    evidence = {"repair": _artifact(render, "repair.json")}

    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="actor_mismatch",
    ):
        closed_loop_attempt_state.transition_state(
            initial,
            next_state="critique_unadjudicated",
            actor="reviewer-moon",
            actor_role="human_adjudicator",
            evidence=evidence,
            workspace_root=workspace,
            previous_state_path=closed_loop_attempt_state.publish_state(
                initial, workspace_root=workspace
            ),
        )
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="illegal_transition",
    ):
        initial_path = closed_loop_attempt_state.state_path(
            initial, workspace_root=workspace
        )
        closed_loop_attempt_state.transition_state(
            initial,
            next_state="machine_repaired",
            actor="workflow-agent-1",
            actor_role="workflow_agent",
            evidence=evidence,
            workspace_root=workspace,
            previous_state_path=initial_path,
        )


def test_live_evidence_rejects_stale_missing_cross_fixture_and_symlink(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    initial = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    render.write_bytes(b"drift")
    with pytest.raises(closed_loop_attempt_state.ClosedLoopAttemptStateError):
        closed_loop_attempt_state.validate_state(initial, workspace_root=workspace)
    render.unlink()
    with pytest.raises(closed_loop_attempt_state.ClosedLoopAttemptStateError):
        closed_loop_attempt_state.validate_state(initial, workspace_root=workspace)

    other = workspace / "examples" / "other"
    other.mkdir()
    foreign = other / "foreign.png"
    foreign.write_bytes(b"foreign")
    foreign_evidence = _root_evidence(render)
    foreign_evidence["render"] = foreign
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="cross_fixture",
    ):
        closed_loop_attempt_state.start_attempt(
            workspace_root=workspace,
            fixture="demo",
            actor="authoring_agent",
            actor_role="authoring_agent",
            evidence=foreign_evidence,
        )
    target = other / "target.png"
    target.write_bytes(b"target")
    link = workspace / "examples" / "demo" / "linked.png"
    link.symlink_to(target)
    linked_evidence = _root_evidence(render)
    linked_evidence["render"] = link
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="symlink",
    ):
        closed_loop_attempt_state.start_attempt(
            workspace_root=workspace,
            fixture="demo",
            actor="authoring_agent",
            actor_role="authoring_agent",
            evidence=linked_evidence,
        )


def test_previous_and_parent_files_are_live_lineage_and_child_is_distinct(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    root = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    root_path = closed_loop_attempt_state.publish_state(root, workspace_root=workspace)
    critique = closed_loop_attempt_state.transition_state(
        root,
        next_state="critique_unadjudicated",
        actor="workflow-agent-1",
        actor_role="workflow_agent",
        evidence=_state_evidence(render, "critique_unadjudicated", 1),
        workspace_root=workspace,
        previous_state_path=root_path,
    )
    root_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="previous_state_file_hash_stale",
    ):
        closed_loop_attempt_state.validate_state(critique, workspace_root=workspace)

    workspace2, render2 = _workspace(tmp_path / "parent-case")
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace2,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(render2),
    )
    for name in (
        "critique_unadjudicated",
        "repair_bound",
        "repair_candidate_ready",
        "repair_authorized",
        "repair_required",
    ):
        state = _transition(state, name, workspace=workspace2, render=render2)
    parent_path = closed_loop_attempt_state.publish_state(
        state, workspace_root=workspace2
    )
    child_render = render2.parent / "child-render.png"
    child_render.write_bytes(b"child-render")
    child = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace2,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(child_render),
        parent_state=state,
        parent_state_path=parent_path,
    )
    assert child["attempt_id"] != state["attempt_id"]
    assert closed_loop_attempt_state.state_path(
        child, workspace_root=workspace2
    ) != closed_loop_attempt_state.state_path(state, workspace_root=workspace2)
    assert closed_loop_attempt_state.validate_chain(
        [child],
        workspace_root=workspace2,
        parent_state=state,
        parent_state_path=parent_path,
    ) == [child]
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="terminal_state_continuation",
    ):
        _transition(state, "repair_bound", workspace=workspace2, render=render2)
    render2.write_bytes(b"ancestor-root-drift")
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="evidence_hash_stale",
    ):
        closed_loop_attempt_state.validate_state(child, workspace_root=workspace2)
    render2.write_bytes(b"render-v1")
    parent_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="parent_state_file_hash_stale",
    ):
        closed_loop_attempt_state.validate_state(child, workspace_root=workspace2)


def test_forged_hash_and_publication_claim_fail_closed(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    forged = {**state, "actor": "forged"}
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="state_hash_invalid",
    ):
        closed_loop_attempt_state.validate_state(forged, workspace_root=workspace)
    claimed = {**state, "publication_acceptance": "accepted"}
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="publication_acceptance_claimed",
    ):
        closed_loop_attempt_state.validate_state(claimed, workspace_root=workspace)


def test_initial_attempt_id_is_recomputed_from_root_evidence(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    forged = {**state, "attempt_id": "attempt-000000000000000000000000"}
    forged["state_sha256"] = closed_loop_attempt_state.canonical_state_sha256(
        forged
    )

    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="attempt_id_root_evidence_mismatch",
    ):
        closed_loop_attempt_state.validate_state(forged, workspace_root=workspace)


def test_transitive_previous_lineage_rechecks_root_evidence(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    root = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-1",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    critique = _transition(
        root, "critique_unadjudicated", workspace=workspace, render=render
    )
    bound = _transition(critique, "repair_bound", workspace=workspace, render=render)
    render.write_bytes(b"root-render-drift")

    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="evidence_hash_stale",
    ):
        closed_loop_attempt_state.validate_state(bound, workspace_root=workspace)


def test_generic_human_review_state_is_not_part_of_the_lifecycle(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-1",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    for name in ("critique_unadjudicated", "repair_bound"):
        state = _transition(state, name, workspace=workspace, render=render)
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="next_state_invalid",
    ):
        closed_loop_attempt_state.transition_state(
            state,
            next_state="human_review_required",
            actor="workflow-1",
            actor_role=state["required_actor"],
            evidence={"unknown": _artifact(render, "unknown.json")},
            workspace_root=workspace,
            previous_state_path=closed_loop_attempt_state.publish_state(
                state, workspace_root=workspace
            ),
        )


def test_state_requires_exact_phase_evidence_roles(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="evidence_roles_invalid",
    ):
        closed_loop_attempt_state.start_attempt(
            workspace_root=workspace,
            fixture="demo",
            actor="author-1",
            actor_role="authoring_agent",
            evidence={"render": render},
        )
    unknown = _root_evidence(render)
    unknown["unexpected"] = _artifact(render, "unexpected.json")
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="evidence_roles_invalid",
    ):
        closed_loop_attempt_state.start_attempt(
            workspace_root=workspace,
            fixture="demo",
            actor="author-1",
            actor_role="authoring_agent",
            evidence=unknown,
        )


def test_state_path_rejects_malformed_attempt_id_directly(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-1",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    state["attempt_id"] = "../../escape"
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="attempt_id_invalid",
    ):
        closed_loop_attempt_state.state_path(state, workspace_root=workspace)


def test_publish_fails_closed_when_evidence_drifts_during_create(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, render = _workspace(tmp_path)
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-1",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    original = closed_loop_attempt_state.repair_transaction.atomic_create_json

    def create_then_drift(path: Path, payload: dict[str, Any]) -> None:
        original(path, payload)
        render.write_bytes(b"drift-during-publish")

    monkeypatch.setattr(
        closed_loop_attempt_state.repair_transaction,
        "atomic_create_json",
        create_then_drift,
    )
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="state_published_but_stale:examples/demo/",
    ) as captured:
        closed_loop_attempt_state.publish_state(state, workspace_root=workspace)
    assert captured.value.path == closed_loop_attempt_state.state_path(
        state, workspace_root=workspace
    )
    assert closed_loop_attempt_state.state_path(
        state, workspace_root=workspace
    ).is_file()


def test_validate_state_rejects_forged_transition_and_actor_role(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    root = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-1",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    critique = _transition(
        root, "critique_unadjudicated", workspace=workspace, render=render
    )

    illegal = {**critique, "state": "machine_repaired"}
    illegal.update(
        disposition="continue",
        required_actor="workflow_agent",
        terminal=False,
        evidence=closed_loop_attempt_state._evidence_records(
            _state_evidence(render, "machine_repaired", 1),
            workspace_root=workspace,
            fixture="demo",
        ),
    )
    illegal["state_sha256"] = closed_loop_attempt_state.canonical_state_sha256(
        illegal
    )
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="illegal_transition",
    ):
        closed_loop_attempt_state.validate_state(illegal, workspace_root=workspace)

    wrong_actor = {**critique, "actor_role": "human_adjudicator"}
    wrong_actor["state_sha256"] = closed_loop_attempt_state.canonical_state_sha256(
        wrong_actor
    )
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="actor_mismatch",
    ):
        closed_loop_attempt_state.validate_state(
            wrong_actor, workspace_root=workspace
        )


def test_root_state_requires_authoring_agent_role(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="initial_actor_role_invalid",
    ):
        closed_loop_attempt_state.start_attempt(
            workspace_root=workspace,
            fixture="demo",
            actor="author-1",
            actor_role="workflow_agent",
            evidence=_root_evidence(render),
        )


def test_state_publication_is_write_once_race_safe_and_rejects_symlink_parent(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )

    def publish() -> str:
        try:
            closed_loop_attempt_state.publish_state(state, workspace_root=workspace)
        except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
            return str(exc)
        return "created"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: publish(), range(2)))
    assert sorted(results) == ["created", "state_already_published"]

    workspace2, render2 = _workspace(tmp_path / "symlink-case")
    state2 = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace2,
        fixture="demo",
        actor="authoring_agent",
        actor_role="authoring_agent",
        evidence=_root_evidence(render2),
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    review = workspace2 / "examples" / "demo" / "review"
    review.symlink_to(outside, target_is_directory=True)
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="state_output_symlink",
    ):
        closed_loop_attempt_state.publish_state(state2, workspace_root=workspace2)


def test_transition_rejects_whitespace_only_named_actor(tmp_path: Path) -> None:
    workspace, render = _workspace(tmp_path)
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-1",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    for name in (
        "critique_unadjudicated",
        "repair_bound",
        "repair_candidate_ready",
        "repair_authorized",
        "machine_repaired",
        "post_review_requested",
        "visually_re_reviewed",
    ):
        state = _transition(state, name, workspace=workspace, render=render)
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="actor_invalid",
    ):
        closed_loop_attempt_state.transition_state(
            state,
            next_state="development_accepted",
            actor="   ",
            actor_role="human_reviewer",
            evidence=_state_evidence(
                render, "development_accepted", state["sequence"] + 1
            ),
            workspace_root=workspace,
            previous_state_path=closed_loop_attempt_state.publish_state(
                state, workspace_root=workspace
            ),
        )


def test_attempt_identity_is_order_independent_but_state_evidence_is_canonical(
    tmp_path: Path,
) -> None:
    workspace, render = _workspace(tmp_path)
    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author-1",
        actor_role="authoring_agent",
        evidence=_root_evidence(render),
    )
    assert closed_loop_attempt_state._attempt_id(
        fixture="demo",
        root_evidence=list(reversed(state["evidence"])),
        parent_record=None,
    ) == state["attempt_id"]

    reordered = {**state, "evidence": list(reversed(state["evidence"]))}
    reordered["state_sha256"] = closed_loop_attempt_state.canonical_state_sha256(
        reordered
    )
    with pytest.raises(
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        match="evidence_order_invalid",
    ):
        closed_loop_attempt_state.validate_state(
            reordered, workspace_root=workspace
        )
