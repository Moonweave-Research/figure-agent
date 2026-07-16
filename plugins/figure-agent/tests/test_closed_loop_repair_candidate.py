from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path

import authoring_repair_packet
import closed_loop_attempt_state
import closed_loop_current_state
import closed_loop_legacy_candidate_quarantine
import closed_loop_repair_candidate
import fig_run
import pytest
import repair_transaction
from test_authoring_repair_packet import _authorized_materialization


def _repair_bound_attempt(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    workspace, packet, response, _authorization, output, _receipt = (
        _authorized_materialization(tmp_path)
    )
    repair_root = output.parent
    packet_path = repair_root / "repair_packet.json"
    response_path = repair_root / "repair_response.json"
    preview_path = repair_root / "materialization_preview.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    response_path.write_text(json.dumps(response), encoding="utf-8")
    preview_path.write_text(
        json.dumps(
            authoring_repair_packet.materialize_repair_candidate(
                packet,
                response,
                workspace_root=workspace,
                apply=False,
            )
        ),
        encoding="utf-8",
    )
    binding_path = repair_root / "critique_repair_binding.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    source_path = workspace / binding["source"]["path"]
    render_path = workspace / binding["current_render"]["path"]
    evidence_root = repair_root / "closed-loop-seed"
    evidence_root.mkdir()

    def evidence(name: str) -> Path:
        path = evidence_root / f"{name}.json"
        path.write_text(json.dumps({"evidence": name}), encoding="utf-8")
        return path

    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="test-author",
        actor_role="authoring_agent",
        evidence={
            "attempt_manifest": evidence("attempt_manifest"),
            "authored_source": source_path,
            "render": render_path,
        },
    )
    state_path = closed_loop_attempt_state.publish_state(
        state,
        workspace_root=workspace,
    )
    for next_state, actor_role, state_evidence in (
        (
            "critique_unadjudicated",
            "workflow_agent",
            {
                "critique": evidence("critique"),
                "host_review_execution_receipt": evidence(
                    "host_review_execution_receipt"
                ),
            },
        ),
        (
            "repair_bound",
            "human_adjudicator",
            {"adjudicated_repair_binding": binding_path},
        ),
    ):
        state = closed_loop_attempt_state.transition_state(
            state,
            next_state=next_state,
            actor="test",
            actor_role=actor_role,
            evidence=state_evidence,
            workspace_root=workspace,
            previous_state_path=state_path,
        )
        state_path = closed_loop_attempt_state.publish_state(
            state,
            workspace_root=workspace,
        )
    return workspace, state_path, packet_path, response_path, preview_path


def _snapshot(root: Path) -> dict[Path, bytes]:
    return {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _pre_r4_8_candidate_leaf(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path, Path, bytes]:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    created = closed_loop_repair_candidate.run_repair_candidate(
        "demo",
        state_path=state_path,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )
    legacy_path = created["next_state_path"]
    legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
    legacy["evidence"] = [
        record
        for record in legacy["evidence"]
        if record["role"] != "repair_response"
    ]
    legacy["state_sha256"] = closed_loop_attempt_state.canonical_state_sha256(
        legacy
    )
    legacy_bytes = json.dumps(legacy).encode("utf-8")
    legacy_path.write_bytes(legacy_bytes)
    return (
        workspace,
        state_path,
        packet_path,
        response_path,
        preview_path,
        legacy_bytes,
    )


def _legacy_quarantine_authorization(
    workspace: Path,
    legacy_path: Path,
) -> Path:
    legacy_bytes = legacy_path.read_bytes()
    legacy = json.loads(legacy_bytes)
    payload = {
        "schema": (
            closed_loop_legacy_candidate_quarantine.AUTHORIZATION_SCHEMA
        ),
        "fixture": "demo",
        "legacy_state": {
            "path": legacy_path.relative_to(workspace).as_posix(),
            "state_sha256": legacy["state_sha256"],
            "file_sha256": (
                "sha256:" + hashlib.sha256(legacy_bytes).hexdigest()
            ),
        },
        "decision": (
            closed_loop_legacy_candidate_quarantine.AUTHORIZATION_DECISION
        ),
        "authorized_by": "test-human-operator",
        "rationale": "Preserve the retired leaf and restart the verified parent.",
        "publication_acceptance": "not_claimed",
    }
    payload["authorization_sha256"] = (
        closed_loop_legacy_candidate_quarantine.canonical_authorization_sha256(
            payload
        )
    )
    path = legacy_path.parent / "legacy_candidate_quarantine_authorization.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_pre_r4_8_candidate_is_preserved_then_parent_can_restart(
    tmp_path: Path,
) -> None:
    (
        workspace,
        state_path,
        packet_path,
        response_path,
        preview_path,
        legacy_bytes,
    ) = _pre_r4_8_candidate_leaf(tmp_path)
    legacy_path = state_path.parent / "state-003-repair_candidate_ready.json"
    authorization_path = _legacy_quarantine_authorization(
        workspace,
        legacy_path,
    )
    before = _snapshot(workspace)

    planned = closed_loop_legacy_candidate_quarantine.quarantine_legacy_candidate(
        "demo",
        state_path=legacy_path,
        authorization_path=authorization_path,
        execute=False,
        workspace_root=workspace,
    )

    assert planned["created"] is False
    assert _snapshot(workspace) == before

    quarantined = (
        closed_loop_legacy_candidate_quarantine.quarantine_legacy_candidate(
            "demo",
            state_path=legacy_path,
            authorization_path=authorization_path,
            execute=True,
            workspace_root=workspace,
        )
    )
    quarantine_path = quarantined["quarantine_path"]
    projection = closed_loop_current_state.resolve_current_attempt(workspace, "demo")
    assert not legacy_path.exists()
    assert quarantine_path.read_bytes() == legacy_bytes
    assert (
        quarantined["quarantine_authorization_path"].read_bytes()
        == authorization_path.read_bytes()
    )
    assert projection["resolution"] == "current"
    assert projection["state"] == "repair_bound"
    assert projection["path"] == state_path.relative_to(workspace).as_posix()

    restarted = closed_loop_repair_candidate.run_repair_candidate(
        "demo",
        state_path=state_path,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )
    assert restarted["created"] is True
    assert restarted["next_state_path"] == legacy_path


def test_pre_r4_8_quarantine_recovers_interrupted_hard_link(
    tmp_path: Path,
) -> None:
    workspace, state_path, *_rest, legacy_bytes = _pre_r4_8_candidate_leaf(
        tmp_path
    )
    legacy_path = state_path.parent / "state-003-repair_candidate_ready.json"
    authorization_path = _legacy_quarantine_authorization(
        workspace,
        legacy_path,
    )
    attempt_id = legacy_path.parent.name
    quarantine_path = (
        workspace
        / "examples/demo/review/closed-loop-legacy"
        / attempt_id
        / legacy_path.name
    )
    quarantine_path.parent.mkdir(parents=True)
    os.link(legacy_path, quarantine_path)

    recovered = (
        closed_loop_legacy_candidate_quarantine.quarantine_legacy_candidate(
            "demo",
            state_path=legacy_path,
            authorization_path=authorization_path,
            execute=True,
            workspace_root=workspace,
        )
    )

    assert recovered["created"] is True
    assert not legacy_path.exists()
    assert quarantine_path.read_bytes() == legacy_bytes
    assert closed_loop_current_state.resolve_current_attempt(
        workspace, "demo"
    )["state"] == "repair_bound"


def test_pre_r4_8_quarantine_recovers_directory_created_before_link(
    tmp_path: Path,
) -> None:
    workspace, state_path, *_rest = _pre_r4_8_candidate_leaf(tmp_path)
    legacy_path = state_path.parent / "state-003-repair_candidate_ready.json"
    authorization_path = _legacy_quarantine_authorization(
        workspace,
        legacy_path,
    )
    quarantine_directory = (
        workspace
        / "examples/demo/review/closed-loop-legacy"
        / legacy_path.parent.name
    )
    quarantine_directory.mkdir(parents=True)

    recovered = (
        closed_loop_legacy_candidate_quarantine.quarantine_legacy_candidate(
            "demo",
            state_path=legacy_path,
            authorization_path=authorization_path,
            execute=True,
            workspace_root=workspace,
        )
    )

    assert recovered["created"] is True
    assert recovered["quarantine_path"].is_file()
    assert not legacy_path.exists()


def test_current_candidate_cannot_be_downgraded_into_legacy_quarantine(
    tmp_path: Path,
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    created = closed_loop_repair_candidate.run_repair_candidate(
        "demo",
        state_path=state_path,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )
    authorization_path = _legacy_quarantine_authorization(
        workspace,
        created["next_state_path"],
    )

    with pytest.raises(
        closed_loop_legacy_candidate_quarantine.ClosedLoopLegacyCandidateQuarantineError,
        match="evidence_roles_invalid",
    ):
        closed_loop_legacy_candidate_quarantine.quarantine_legacy_candidate(
            "demo",
            state_path=created["next_state_path"],
            authorization_path=authorization_path,
            execute=True,
            workspace_root=workspace,
        )

    assert created["next_state_path"].is_file()


def test_shape_downgrade_cannot_quarantine_without_exact_human_authorization(
    tmp_path: Path,
) -> None:
    workspace, state_path, *_rest = _pre_r4_8_candidate_leaf(tmp_path)
    legacy_path = state_path.parent / "state-003-repair_candidate_ready.json"

    with pytest.raises(
        closed_loop_legacy_candidate_quarantine.ClosedLoopLegacyCandidateQuarantineError,
        match="legacy_candidate_authorization_invalid",
    ):
        closed_loop_legacy_candidate_quarantine.quarantine_legacy_candidate(
            "demo",
            state_path=legacy_path,
            authorization_path=legacy_path.parent / "missing-authorization.json",
            execute=True,
            workspace_root=workspace,
        )

    assert legacy_path.is_file()


def test_legacy_quarantine_authorization_is_bound_to_exact_leaf_bytes(
    tmp_path: Path,
) -> None:
    workspace, state_path, *_rest = _pre_r4_8_candidate_leaf(tmp_path)
    legacy_path = state_path.parent / "state-003-repair_candidate_ready.json"
    authorization_path = _legacy_quarantine_authorization(
        workspace,
        legacy_path,
    )
    legacy_path.write_bytes(legacy_path.read_bytes() + b"\n")

    with pytest.raises(
        closed_loop_legacy_candidate_quarantine.ClosedLoopLegacyCandidateQuarantineError,
        match="legacy_candidate_authorization_invalid",
    ):
        closed_loop_legacy_candidate_quarantine.quarantine_legacy_candidate(
            "demo",
            state_path=legacy_path,
            authorization_path=authorization_path,
            execute=True,
            workspace_root=workspace,
        )

    assert legacy_path.is_file()


def test_repair_candidate_plan_only_is_write_free(tmp_path: Path) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    before = _snapshot(workspace)

    result = closed_loop_repair_candidate.run_repair_candidate(
        "demo",
        state_path=state_path,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=False,
        workspace_root=workspace,
    )

    assert result["next_state"] == "repair_candidate_ready"
    assert result["created"] is False
    assert result["required_actor"] == "workflow_agent"
    assert result["publication_acceptance"] == "not_claimed"
    assert _snapshot(workspace) == before


def test_repair_candidate_execute_publishes_exact_evidence(tmp_path: Path) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )

    result = closed_loop_repair_candidate.run_repair_candidate(
        "demo",
        state_path=state_path,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )

    published = json.loads(result["next_state_path"].read_text(encoding="utf-8"))
    projection = closed_loop_current_state.resolve_current_attempt(workspace, "demo")
    assert result["created"] is True
    assert published["state"] == "repair_candidate_ready"
    assert published["actor"] == "fig_run"
    assert published["actor_role"] == "workflow_agent"
    assert published["required_actor"] == "human_repair_authorizer"
    assert [record["role"] for record in published["evidence"]] == [
        "materialization_preview",
        "repair_execution_packet",
        "repair_response",
    ]
    assert projection["path"] == result["next_state_path"].relative_to(
        workspace
    ).as_posix()
    assert projection["state_sha256"] == published["state_sha256"]


def test_repair_candidate_rejects_packet_not_bound_to_state_lineage(
    tmp_path: Path,
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["adjudicated_repair_binding"]["sha256"] = "sha256:" + "0" * 64
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(packet)
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    try:
        closed_loop_repair_candidate.run_repair_candidate(
            "demo",
            state_path=state_path,
            packet_path=packet_path,
            response_path=response_path,
            preview_path=preview_path,
            execute=True,
            workspace_root=workspace,
        )
    except closed_loop_repair_candidate.ClosedLoopRepairCandidateError as exc:
        assert "repair_packet_not_canonical_from_binding" in str(exc)
    else:
        raise AssertionError("mismatched binding authority must fail closed")

    assert not any(state_path.parent.glob("state-*-repair_candidate_ready.json"))


def test_repair_candidate_rejects_packet_with_widened_selector_and_budget(
    tmp_path: Path,
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["editable_target"]["selector"]["anchor_start"] = (
        r"\documentclass[tikz,border=4pt]{standalone}"
    )
    packet["editable_target"]["selector"]["anchor_end"] = r"\node {S60 -> S80};"
    packet["editable_target"]["protected_invariants"] = []
    packet["change_budget"]["max_changed_lines"] = 100
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(packet)
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    response = json.loads(response_path.read_text(encoding="utf-8"))
    preview = authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        apply=False,
    )
    preview_path.write_text(json.dumps(preview), encoding="utf-8")

    with pytest.raises(
        closed_loop_repair_candidate.ClosedLoopRepairCandidateError,
        match="repair_packet_not_canonical_from_binding",
    ):
        closed_loop_repair_candidate.run_repair_candidate(
            "demo",
            state_path=state_path,
            packet_path=packet_path,
            response_path=response_path,
            preview_path=preview_path,
            execute=True,
            workspace_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-repair_candidate_ready.json"))


def test_repair_candidate_rejects_preview_not_recomputed_from_response(
    tmp_path: Path,
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    response = json.loads(response_path.read_text(encoding="utf-8"))
    response["change_summary"] = "Different candidate meaning."
    response_path.write_text(json.dumps(response), encoding="utf-8")

    with pytest.raises(
        closed_loop_repair_candidate.ClosedLoopRepairCandidateError,
        match="materialization_preview_response_mismatch",
    ):
        closed_loop_repair_candidate.run_repair_candidate(
            "demo",
            state_path=state_path,
            packet_path=packet_path,
            response_path=response_path,
            preview_path=preview_path,
            execute=True,
            workspace_root=workspace,
        )


def test_repair_candidate_rejects_preview_schema_extension(
    tmp_path: Path,
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    preview["unbound_note"] = "not part of the candidate contract"
    preview_path.write_text(json.dumps(preview), encoding="utf-8")

    with pytest.raises(
        closed_loop_repair_candidate.ClosedLoopRepairCandidateError,
        match="materialization_preview_invalid",
    ):
        closed_loop_repair_candidate.run_repair_candidate(
            "demo",
            state_path=state_path,
            packet_path=packet_path,
            response_path=response_path,
            preview_path=preview_path,
            execute=True,
            workspace_root=workspace,
        )


def test_repair_candidate_rejects_projected_state_hash_mismatch(
    tmp_path: Path,
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )

    with pytest.raises(
        closed_loop_repair_candidate.ClosedLoopRepairCandidateError,
        match="closed_loop_projected_state_hash_mismatch",
    ):
        closed_loop_repair_candidate.run_repair_candidate(
            "demo",
            state_path=state_path,
            packet_path=packet_path,
            response_path=response_path,
            preview_path=preview_path,
            execute=True,
            workspace_root=workspace,
            expected_state_sha256="sha256:" + "0" * 64,
        )


def test_default_fig_run_consumes_only_explicit_candidate_triplet(
    tmp_path: Path,
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="publish the explicit repair candidate",
        execute=True,
        closed_loop_repair_packet=packet_path,
        closed_loop_candidate_response=response_path,
        closed_loop_materialization_preview=preview_path,
        repo_root=workspace,
    )

    assert payload["closed_loop"]["input_state"] == "repair_bound"
    assert payload["closed_loop"]["input_state_path"] == state_path.relative_to(
        workspace
    ).as_posix()
    assert payload["closed_loop"]["next_state"] == "repair_candidate_ready"
    assert payload["closed_loop"]["created"] is True
    assert payload["boundary_handoff"]["required_actor"] == "human_repair_authorizer"
    assert payload["boundary_handoff"]["publication_acceptance"] == "not_claimed"


def test_default_fig_run_does_not_discover_adjacent_candidate_artifacts(
    tmp_path: Path,
) -> None:
    workspace, state_path, _packet_path, _response_path, _preview_path = (
        _repair_bound_attempt(tmp_path)
    )

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="continue the lifecycle",
        execute=True,
        repo_root=workspace,
    )

    projection = closed_loop_current_state.resolve_current_attempt(workspace, "demo")
    assert payload["executed_count"] == 0
    assert payload["boundary_handoff"]["required_actor"] == "workflow_agent"
    assert projection["state"] == "repair_bound"
    assert projection["path"] == state_path.relative_to(workspace).as_posix()
    assert not any(state_path.parent.glob("state-*-repair_candidate_ready.json"))


def test_repair_candidate_recovers_matching_published_state(tmp_path: Path) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    created = closed_loop_repair_candidate.run_repair_candidate(
        "demo",
        state_path=state_path,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )

    recovered = closed_loop_repair_candidate.run_repair_candidate(
        "demo",
        state_path=state_path,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )

    assert recovered["created"] is False
    assert recovered["stop_reason"] == "repair_candidate_ready_recovered"
    assert recovered["required_actor"] == "human_repair_authorizer"
    assert recovered["next_state_path"] == created["next_state_path"]


def test_repair_candidate_recovers_state_published_between_match_and_current_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    original_match = closed_loop_repair_candidate._matching_published_candidate
    calls = 0

    def publish_after_first_match(
        fixture: str,
        plan: dict[str, object],
        *,
        workspace_root: Path,
    ) -> dict[str, object] | None:
        nonlocal calls
        calls += 1
        if calls == 1:
            next_state = closed_loop_repair_candidate._expected_candidate_state(
                plan,
                workspace_root=workspace_root,
            )
            closed_loop_attempt_state.publish_state(
                next_state,
                workspace_root=workspace_root,
            )
            return None
        return original_match(
            fixture,
            plan,
            workspace_root=workspace_root,
        )

    monkeypatch.setattr(
        closed_loop_repair_candidate,
        "_matching_published_candidate",
        publish_after_first_match,
    )

    recovered = closed_loop_repair_candidate.run_repair_candidate(
        "demo",
        state_path=state_path,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=False,
        workspace_root=workspace,
    )

    assert calls == 2
    assert recovered["created"] is False
    assert recovered["stop_reason"] == "repair_candidate_ready_recovered"
    assert recovered["required_actor"] == "human_repair_authorizer"


def test_repair_candidate_rechecks_output_under_materialization_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    output = workspace / packet["output_path"]
    original_lock = repair_transaction.recoverable_exclusive_lock

    @contextmanager
    def materialize_before_candidate_lock(path: Path, *, owner: str):
        with original_lock(path, owner=owner):
            if path.name == ".materialization.lock":
                output.write_text("concurrent legacy materialization", encoding="utf-8")
            yield

    monkeypatch.setattr(
        closed_loop_repair_candidate.repair_transaction,
        "recoverable_exclusive_lock",
        materialize_before_candidate_lock,
    )

    with pytest.raises(
        closed_loop_repair_candidate.ClosedLoopRepairCandidateError,
        match="repair_candidate_output_already_materialized",
    ):
        closed_loop_repair_candidate.run_repair_candidate(
            "demo",
            state_path=state_path,
            packet_path=packet_path,
            response_path=response_path,
            preview_path=preview_path,
            execute=True,
            workspace_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-repair_candidate_ready.json"))


def test_materializer_reclaims_stale_candidate_materialization_lock(
    tmp_path: Path,
) -> None:
    workspace, packet, response, authorization, output, receipt = (
        _authorized_materialization(tmp_path)
    )
    lock = output.parent / ".materialization.lock"
    lock.write_text(
        json.dumps(
            {
                "schema": "figure-agent.recoverable-lock.v1",
                "owner": repair_transaction.MATERIALIZATION_LOCK_OWNER,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    result = authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        authorization=authorization,
        apply=True,
        receipt_path=receipt,
    )

    assert result["decision"] == "materialized_verification_pending"
    assert output.is_file()
    assert receipt.is_file()
    assert not lock.exists()


def test_repair_candidate_rejects_valid_preview_replacement_under_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    original_lock = repair_transaction.recoverable_exclusive_lock

    @contextmanager
    def replace_after_lock(path: Path, *, owner: str):
        if path.name != closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK:
            with original_lock(path, owner=owner):
                yield
            return
        with original_lock(path, owner=owner):
            response = json.loads(response_path.read_text(encoding="utf-8"))
            response["change_summary"] = "A different valid candidate summary."
            response_path.write_text(json.dumps(response), encoding="utf-8")
            preview = json.loads(preview_path.read_text(encoding="utf-8"))
            preview["change_summary"] = response["change_summary"]
            preview["preview_sha256"] = (
                authoring_repair_packet.canonical_materialization_preview_sha256(
                    preview
                )
            )
            preview_path.write_text(json.dumps(preview), encoding="utf-8")
            yield

    monkeypatch.setattr(
        closed_loop_repair_candidate.repair_transaction,
        "recoverable_exclusive_lock",
        replace_after_lock,
    )

    with pytest.raises(
        closed_loop_repair_candidate.ClosedLoopRepairCandidateError,
        match="repair_candidate_inputs_drifted",
    ):
        closed_loop_repair_candidate.run_repair_candidate(
            "demo",
            state_path=state_path,
            packet_path=packet_path,
            response_path=response_path,
            preview_path=preview_path,
            execute=True,
            workspace_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-repair_candidate_ready.json"))


def test_repair_candidate_rejects_evidence_drift_during_transition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    original_transition = closed_loop_attempt_state.transition_state

    def drift_after_transition(*args: object, **kwargs: object) -> dict[str, object]:
        next_state = original_transition(*args, **kwargs)
        preview = json.loads(preview_path.read_text(encoding="utf-8"))
        preview["change_summary"] = "Drift after state construction."
        preview["preview_sha256"] = (
            authoring_repair_packet.canonical_materialization_preview_sha256(preview)
        )
        preview_path.write_text(json.dumps(preview), encoding="utf-8")
        return next_state

    monkeypatch.setattr(
        closed_loop_repair_candidate.closed_loop_attempt_state,
        "transition_state",
        drift_after_transition,
    )

    with pytest.raises(
        closed_loop_repair_candidate.ClosedLoopRepairCandidateError,
        match="evidence_hash_stale",
    ):
        closed_loop_repair_candidate.run_repair_candidate(
            "demo",
            state_path=state_path,
            packet_path=packet_path,
            response_path=response_path,
            preview_path=preview_path,
            execute=True,
            workspace_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-repair_candidate_ready.json"))


def test_fig_run_requires_candidate_inputs_as_one_explicit_triplet(
    tmp_path: Path,
) -> None:
    workspace, state_path, packet_path, _response_path, _preview_path = (
        _repair_bound_attempt(tmp_path)
    )

    with pytest.raises(ValueError, match="must be supplied together"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="publish an incomplete candidate",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_repair_packet=packet_path,
            repo_root=workspace,
        )


def test_fig_run_candidate_cli_plan_binds_current_state_without_journal(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace, state_path, packet_path, response_path, preview_path = (
        _repair_bound_attempt(tmp_path)
    )
    runs_root = tmp_path / "runs"

    result = fig_run.main(
        [
            "demo",
            "--mode",
            "review",
            "--goal",
            "publish the explicit repair candidate",
            "--closed-loop-repair-packet",
            str(packet_path),
            "--closed-loop-candidate-response",
            str(response_path),
            "--closed-loop-materialization-preview",
            str(preview_path),
            "--runs-root",
            str(runs_root),
            "--record",
            "--json",
        ],
        repo_root=workspace,
    )

    payload = json.loads(capsys.readouterr().out)
    current = json.loads(state_path.read_text(encoding="utf-8"))
    assert result == 0
    assert payload["closed_loop"]["input_state_sha256"] == current["state_sha256"]
    assert payload["closed_loop"]["next_state"] == "repair_candidate_ready"
    assert payload["closed_loop"]["created"] is False
    assert payload["boundary_handoff"]["required_actor"] == "workflow_agent"
    assert not runs_root.exists()
