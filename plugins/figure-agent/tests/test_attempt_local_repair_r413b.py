from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import attempt_local_post_review  # noqa: E402
import attempt_local_post_review_authority as post_review_authority  # noqa: E402
import attempt_local_post_review_response  # noqa: E402
import attempt_local_repair_binding as packet_boundary  # noqa: E402
import authoring_repair_finalize  # noqa: E402
import authoring_repair_packet  # noqa: E402
import authoring_repair_rollback  # noqa: E402
import closed_loop_machine_repair  # noqa: E402
import closed_loop_post_review  # noqa: E402
import closed_loop_repair_authorization  # noqa: E402
import closed_loop_repair_candidate  # noqa: E402
import fig_run  # noqa: E402
from test_attempt_local_repair_binding import FIXTURE, _repair_bound_attempt  # noqa: E402
from test_authoring_repair_packet import _fake_strict_compiler  # noqa: E402


def _response(packet: dict[str, object], workspace: Path) -> dict[str, str]:
    source = workspace / str(packet["source"]["path"])
    selector = packet["editable_target"]["selector"]
    text = source.read_text(encoding="utf-8")
    start = text.index(selector["anchor_start"]) + len(selector["anchor_start"])
    end = text.index(selector["anchor_end"])
    editable = text[start:end].strip("\n")
    return {
        "replacement_utf8": editable + " % attempt-local repair",
        "change_summary": "Apply the exact attributed local repair.",
    }


def _authorization(packet: dict[str, object], preview: dict[str, object]) -> dict[str, object]:
    return {
        "schema": "figure-agent.human-decision-record.v1",
        "fixture": FIXTURE,
        "packet_schema": packet["schema"],
        "packet_path": packet["attempt_local_repair_binding"]["path"].replace(
            "attempt-local-repair-binding.json", "attempt-local-repair-packet.json"
        ),
        "packet_recommendation": "materialize_authoring_repair_candidate",
        "queue_run_id": "attempt-local-r413b-001",
        "decision_kind": "materialize_authoring_repair_candidate",
        "agent_recommendation": "Materialize only this exact attempt-local repair.",
        "human_decision": "approve this exact additive repair candidate",
        "human_note": "Named human approval binds packet, preview, and sandbox output.",
        "reviewer": "named-human-reviewer",
        "follow_up": {"command": "fig-run repair materialize"},
        "mutation_boundary": "additive_artifact_materialization_allowed",
        "authorized_packet_sha256": packet["packet_sha256"],
        "authorized_output_path": preview["output_path"],
        "authorized_output_sha256": preview["output_sha256"],
        "authorized_preview_sha256": preview["preview_sha256"],
    }


def _prepared(tmp_path: Path) -> tuple[Path, Path, dict[str, object], Path, Path, Path]:
    workspace, repair_bound = _repair_bound_attempt(tmp_path)
    created = packet_boundary.run_attempt_local_repair_packet(
        FIXTURE,
        state_path=repair_bound,
        model_id="test-model",
        execute=True,
        workspace_root=workspace,
    )
    paths = created["artifacts"]
    packet = json.loads(paths["packet"].read_text(encoding="utf-8"))
    response_path = paths["packet"].with_name("repair-response.json")
    response = _response(packet, workspace)
    response_path.write_text(json.dumps(response), encoding="utf-8")
    preview = authoring_repair_packet.materialize_repair_candidate(
        packet, response, workspace_root=workspace, apply=False
    )
    preview_path = paths["packet"].with_name("materialization-preview.json")
    preview_path.write_text(json.dumps(preview), encoding="utf-8")
    return workspace, repair_bound, packet, paths["packet"], response_path, preview_path


def _fake_image_strict_compiler(tmp_path: Path) -> Path:
    plugin_root = _fake_strict_compiler(tmp_path)
    source_png = tmp_path / "strict-render.png"
    Image.new("RGB", (800, 600), "white").save(source_png)
    script = plugin_root / "scripts" / "compile.sh"
    text = script.read_text(encoding="utf-8")
    script.write_text(
        text.replace(
            "printf 'png' > \"$build/$base.png\"",
            f'cp "{source_png}" "$build/$base.png"',
        ),
        encoding="utf-8",
    )
    return plugin_root


def _image_machine_repaired_attempt(
    tmp_path: Path,
) -> tuple[Path, dict[str, object]]:
    workspace, repair_bound, packet, packet_path, response_path, preview_path = _prepared(tmp_path)
    candidate = closed_loop_repair_candidate.run_repair_candidate(
        FIXTURE,
        state_path=repair_bound,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    authorization_path = packet_path.with_name("human-authorization.json")
    authorization_path.write_text(json.dumps(_authorization(packet, preview)), encoding="utf-8")
    authorized = closed_loop_repair_authorization.run_authorization(
        FIXTURE,
        state_path=candidate["next_state_path"],
        authorization_path=authorization_path,
        execute=True,
        workspace_root=workspace,
    )
    repaired = closed_loop_machine_repair.run_machine_repair(
        FIXTURE,
        state_path=authorized["next_state_path"],
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
        plugin_root=_fake_image_strict_compiler(tmp_path),
    )
    return workspace, repaired


def _post_review_state_path(repaired: dict[str, object]) -> Path:
    machine_path = repaired["next_state_path"]
    machine_state = json.loads(machine_path.read_text(encoding="utf-8"))
    return machine_path.with_name(
        f"state-{machine_state['sequence'] + 1:03d}-post_review_requested.json"
    )


def test_v2_candidate_and_named_authorization_do_not_cross_inject_v1(tmp_path: Path) -> None:
    workspace, repair_bound, packet, packet_path, response_path, preview_path = _prepared(tmp_path)
    candidate = closed_loop_repair_candidate.run_repair_candidate(
        FIXTURE,
        state_path=repair_bound,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )
    assert candidate["next_state"] == "repair_candidate_ready"
    recovered = closed_loop_repair_candidate.run_repair_candidate(
        FIXTURE,
        state_path=repair_bound,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )
    assert recovered["created"] is False

    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    authorization_path = packet_path.with_name("human-authorization.json")
    authorization_path.write_text(json.dumps(_authorization(packet, preview)), encoding="utf-8")
    authorized = closed_loop_repair_authorization.run_authorization(
        FIXTURE,
        state_path=candidate["next_state_path"],
        authorization_path=authorization_path,
        execute=True,
        workspace_root=workspace,
    )
    assert authorized["next_state"] == "repair_authorized"
    assert authorized["published_state"]["actor"] == "named-human-reviewer"

    packet["schema"] = authoring_repair_packet.SCHEMA
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(packet)
    with pytest.raises(authoring_repair_packet.RepairExecutionPacketError):
        authoring_repair_packet.validate_bound_packet_authority(packet, workspace)


def test_v2_materialization_is_sandbox_only_and_authorization_drift_fails_closed(
    tmp_path: Path,
) -> None:
    workspace, _repair_bound, packet, packet_path, response_path, preview_path = _prepared(tmp_path)
    response = json.loads(response_path.read_text(encoding="utf-8"))
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    authorization = _authorization(packet, preview)
    source_before = (workspace / packet["source"]["path"]).read_bytes()
    receipt_path = packet_path.with_name("materialization-receipt.json")
    receipt = authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        authorization=authorization,
        receipt_path=receipt_path,
        response_provenance={
            "path": response_path.relative_to(workspace).as_posix(),
            "sha256": "sha256:" + hashlib.sha256(response_path.read_bytes()).hexdigest(),
            "payload": response,
        },
    )
    output = workspace / str(packet["output_path"])
    assert output.is_file()
    assert receipt["output_path"] == packet["output_path"]
    assert (workspace / packet["source"]["path"]).read_bytes() == source_before

    stale = {**authorization, "authorized_preview_sha256": "sha256:" + "0" * 64}
    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="authorization invalid",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace,
            authorization=stale,
            receipt_path=receipt_path.with_name("second-receipt.json"),
        )


def test_v2_authorization_packet_path_must_match_the_actual_packet(tmp_path: Path) -> None:
    workspace, repair_bound, packet, packet_path, response_path, preview_path = _prepared(tmp_path)
    candidate = closed_loop_repair_candidate.run_repair_candidate(
        FIXTURE,
        state_path=repair_bound,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    forged = _authorization(packet, preview)
    forged["packet_path"] = "examples/fig3_resistance_mechanism/other-packet.json"
    authorization_path = packet_path.with_name("human-authorization.json")
    authorization_path.write_text(json.dumps(forged), encoding="utf-8")
    with pytest.raises(
        closed_loop_repair_authorization.ClosedLoopRepairAuthorizationError,
        match="materialization_decision_packet_path_mismatch",
    ):
        closed_loop_repair_authorization.run_authorization(
            FIXTURE,
            state_path=candidate["next_state_path"],
            authorization_path=authorization_path,
            execute=True,
            workspace_root=workspace,
        )
    assert not (candidate["next_state_path"].parent / "state-006-repair_authorized.json").exists()


def test_v2_failed_strict_finalize_rolls_back_only_additive_output(tmp_path: Path) -> None:
    workspace, _repair_bound, packet, packet_path, response_path, preview_path = _prepared(tmp_path)
    response = json.loads(response_path.read_text(encoding="utf-8"))
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    authorization = _authorization(packet, preview)
    authorization_path = packet_path.with_name("human-authorization.json")
    authorization_path.write_text(json.dumps(authorization), encoding="utf-8")
    receipt_path = packet_path.with_name("materialization-receipt.json")
    authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        authorization=authorization,
        receipt_path=receipt_path,
    )
    output = workspace / str(packet["output_path"])
    failed = authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, state="failed"),
    )
    assert failed["decision"] == "materialized_verification_failed"
    rolled_back = authoring_repair_rollback.rollback_failed_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
    )
    assert rolled_back["decision"] == "materialized_rolled_back_after_verification_failure"
    assert not output.exists()


def test_v2_machine_repair_stops_before_post_repair_visual_review(tmp_path: Path) -> None:
    workspace, repair_bound, packet, packet_path, response_path, preview_path = _prepared(tmp_path)
    candidate = closed_loop_repair_candidate.run_repair_candidate(
        FIXTURE,
        state_path=repair_bound,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    authorization_path = packet_path.with_name("human-authorization.json")
    authorization_path.write_text(json.dumps(_authorization(packet, preview)), encoding="utf-8")
    authorized = closed_loop_repair_authorization.run_authorization(
        FIXTURE,
        state_path=candidate["next_state_path"],
        authorization_path=authorization_path,
        execute=True,
        workspace_root=workspace,
    )
    repaired = closed_loop_machine_repair.run_machine_repair(
        FIXTURE,
        state_path=authorized["next_state_path"],
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path),
    )
    assert repaired["next_state"] == "machine_repaired"
    assert repaired["stop_boundary"] == "human_or_host_post_repair_review"
    assert repaired["required_actor"] == "human_or_host"


def test_v2_machine_repair_never_falls_through_to_legacy_post_review(
    tmp_path: Path,
) -> None:
    workspace, repair_bound, packet, packet_path, response_path, preview_path = _prepared(tmp_path)
    candidate = closed_loop_repair_candidate.run_repair_candidate(
        FIXTURE,
        state_path=repair_bound,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    authorization_path = packet_path.with_name("human-authorization.json")
    authorization_path.write_text(json.dumps(_authorization(packet, preview)), encoding="utf-8")
    authorized = closed_loop_repair_authorization.run_authorization(
        FIXTURE,
        state_path=candidate["next_state_path"],
        authorization_path=authorization_path,
        execute=True,
        workspace_root=workspace,
    )
    repaired = closed_loop_machine_repair.run_machine_repair(
        FIXTURE,
        state_path=authorized["next_state_path"],
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path),
    )

    with pytest.raises(
        closed_loop_post_review.ClosedLoopPostReviewError,
        match="repair_packet_binding_missing",
    ):
        closed_loop_post_review.run_outbound_handoff(
            FIXTURE,
            state_path=repaired["next_state_path"],
            execute=True,
            workspace_root=workspace,
        )
    assert not (repaired["next_state_path"].parent / "post-repair-review").exists()


def test_v2_machine_repair_reconstructs_write_free_post_review_authority(
    tmp_path: Path,
) -> None:
    workspace, repair_bound, packet, packet_path, response_path, preview_path = _prepared(tmp_path)
    candidate = closed_loop_repair_candidate.run_repair_candidate(
        FIXTURE,
        state_path=repair_bound,
        packet_path=packet_path,
        response_path=response_path,
        preview_path=preview_path,
        execute=True,
        workspace_root=workspace,
    )
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    authorization_path = packet_path.with_name("human-authorization.json")
    authorization_path.write_text(json.dumps(_authorization(packet, preview)), encoding="utf-8")
    authorized = closed_loop_repair_authorization.run_authorization(
        FIXTURE,
        state_path=candidate["next_state_path"],
        authorization_path=authorization_path,
        execute=True,
        workspace_root=workspace,
    )
    repaired = closed_loop_machine_repair.run_machine_repair(
        FIXTURE,
        state_path=authorized["next_state_path"],
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path),
    )
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    plan = post_review_authority.plan_attempt_local_post_review(
        FIXTURE, state_path=repaired["next_state_path"], workspace_root=workspace
    )
    assert plan["selected_finding_id"] == packet["selected_finding_id"]
    assert plan["output_path"] == workspace / packet["output_path"]
    assert set(plan["initial_crops"]) == {
        "full_q1",
        "full_q2",
        "full_q3",
        "full_q4",
        "print_178mm",
        "print_thumbnail",
    }
    assert sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*")) == before


def test_v2_post_review_plan_is_write_free_and_execute_publishes_separate_request(
    tmp_path: Path,
) -> None:
    workspace, repaired = _image_machine_repaired_attempt(tmp_path)
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    planned = attempt_local_post_review.run_attempt_local_post_review(
        FIXTURE, state_path=repaired["next_state_path"], execute=False, workspace_root=workspace
    )
    assert planned["stop_reason"] == "plan_only"
    assert sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*")) == before

    result = attempt_local_post_review.run_attempt_local_post_review(
        FIXTURE, state_path=repaired["next_state_path"], execute=True, workspace_root=workspace
    )
    request = json.loads(result["request_path"].read_text(encoding="utf-8"))
    assert request["schema"] == "figure-agent.attempt-local-post-repair-review-request.v2"
    assert request["review_kind"] == "human_or_host_post_repair_review"
    assert request["publication_acceptance"] == "not_claimed"
    assert {crop["id"] for crop in request["initial_crops"]} == {
        "full_q1",
        "full_q2",
        "full_q3",
        "full_q4",
        "print_178mm",
        "print_thumbnail",
    }
    assert all("bbox_px" not in crop for crop in request["initial_crops"])
    assert result["published_state"]["state"] == "post_review_requested"
    assert result["required_actor"] == "host_llm"

    recovered = attempt_local_post_review.run_attempt_local_post_review(
        FIXTURE, state_path=repaired["next_state_path"], execute=True, workspace_root=workspace
    )
    assert recovered["created"] is False
    assert recovered["request"] == request

    crop_path = workspace / "examples" / FIXTURE / request["after_crops"][0]["path"]
    crop_path.write_bytes(b"drift")
    with pytest.raises(
        attempt_local_post_review.AttemptLocalPostReviewError,
        match="post_review_after_crop_hash_drift",
    ):
        attempt_local_post_review.run_attempt_local_post_review(
            FIXTURE,
            state_path=repaired["next_state_path"],
            execute=True,
            workspace_root=workspace,
        )


def test_v2_post_review_rejects_next_state_symlink_before_read(tmp_path: Path) -> None:
    workspace, repaired = _image_machine_repaired_attempt(tmp_path)
    next_state_path = _post_review_state_path(repaired)
    next_state_path.symlink_to(repaired["next_state_path"])

    with pytest.raises(
        attempt_local_post_review.AttemptLocalPostReviewError,
        match="post_review_publication_failed:closed_loop_state_symlink",
    ):
        attempt_local_post_review.run_attempt_local_post_review(
            FIXTURE,
            state_path=repaired["next_state_path"],
            execute=True,
            workspace_root=workspace,
        )
    assert not (next_state_path.parent / "attempt-local-post-repair-review").exists()


def test_v2_post_review_revalidates_all_artifacts_after_transition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, repaired = _image_machine_repaired_attempt(tmp_path)
    original = attempt_local_post_review.closed_loop_attempt_state.transition_state

    def tampering_transition(*args: object, **kwargs: object) -> dict[str, object]:
        state = original(*args, **kwargs)
        request_path = repaired["next_state_path"].parent / (
            "attempt-local-post-repair-review/request.json"
        )
        request = json.loads(request_path.read_text(encoding="utf-8"))
        crop = workspace / request["initial_crops"][0]["path"]
        crop.write_bytes(b"drift-after-transition")
        return state

    monkeypatch.setattr(
        attempt_local_post_review.closed_loop_attempt_state,
        "transition_state",
        tampering_transition,
    )
    with pytest.raises(
        attempt_local_post_review.AttemptLocalPostReviewError,
        match="post_review_request_artifact_hash_drift",
    ):
        attempt_local_post_review.run_attempt_local_post_review(
            FIXTURE,
            state_path=repaired["next_state_path"],
            execute=True,
            workspace_root=workspace,
        )
    assert not _post_review_state_path(repaired).exists()


def test_v2_post_review_write_failure_cleans_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, repaired = _image_machine_repaired_attempt(tmp_path)

    def fail_write(*args: object, **kwargs: object) -> None:
        raise OSError("injected request write failure")

    monkeypatch.setattr(attempt_local_post_review, "_write_request", fail_write)
    with pytest.raises(
        attempt_local_post_review.AttemptLocalPostReviewError,
        match="injected request write failure",
    ):
        attempt_local_post_review.run_attempt_local_post_review(
            FIXTURE,
            state_path=repaired["next_state_path"],
            execute=True,
            workspace_root=workspace,
        )
    attempt_root = repaired["next_state_path"].parent
    assert not (attempt_root / ".attempt-local-post-review-staging").exists()
    assert not (attempt_root / "attempt-local-post-repair-review").exists()
    assert not _post_review_state_path(repaired).exists()


def test_v2_post_review_all_artifact_validation_is_the_final_publish_barrier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, repaired = _image_machine_repaired_attempt(tmp_path)
    attempt_root = repaired["next_state_path"].parent
    request_path = attempt_root / "attempt-local-post-repair-review" / "request.json"
    original = attempt_local_post_review.authority.assert_render_unchanged
    mutated = False

    def mutate_after_render_check(*args: object, **kwargs: object) -> None:
        nonlocal mutated
        original(*args, **kwargs)
        if request_path.is_file() and not mutated:
            request = json.loads(request_path.read_text(encoding="utf-8"))
            crop = workspace / request["initial_crops"][0]["path"]
            crop.write_bytes(b"drift-after-final-render-check")
            mutated = True

    monkeypatch.setattr(
        attempt_local_post_review.authority,
        "assert_render_unchanged",
        mutate_after_render_check,
    )
    with pytest.raises(
        attempt_local_post_review.AttemptLocalPostReviewError,
        match="post_review_request_artifact_hash_drift",
    ):
        attempt_local_post_review.run_attempt_local_post_review(
            FIXTURE,
            state_path=repaired["next_state_path"],
            execute=True,
            workspace_root=workspace,
        )
    assert mutated is True
    assert not _post_review_state_path(repaired).exists()


def _v2_post_review_response(
    workspace: Path,
    request: dict[str, object],
    *,
    with_execution: bool = True,
) -> tuple[Path, dict[str, object]]:
    attempt_root = workspace / str(request["after_crop_manifest"]["path"])
    attempt_root = attempt_root.parents[2]
    transcript = attempt_root / "attempt-local-post-repair-review" / "host-transcript.json"
    transcript.write_text('{"review":"completed"}\n', encoding="utf-8")
    inspected = {
        "before_render": request["before_render"],
        "after_render": request["after_render"],
        "materialized_output": request["materialized_output"],
        "materialization_receipt": request["materialization_receipt"],
        "initial_crops": request["initial_crops"],
        "after_crop_manifest": request["after_crop_manifest"],
        "after_crops": request["after_crops"],
    }
    execution: dict[str, object] | None = None
    if with_execution:
        execution = {
            "schema": "figure-agent.attempt-local-host-review-execution-receipt.v2",
            "request_sha256": request["request_sha256"],
            "actor": {
                "kind": "model",
                "identity": "host-vision",
                "model_or_tool": "vision-runtime",
            },
            "transcript": {
                "path": transcript.relative_to(workspace).as_posix(),
                "sha256": "sha256:" + hashlib.sha256(transcript.read_bytes()).hexdigest(),
            },
            "inspected_artifacts": inspected,
        }
        execution["receipt_sha256"] = attempt_local_post_review_response.canonical_hash(
            execution, omitted="receipt_sha256"
        )
    response = {
        "schema": "figure-agent.attempt-local-post-repair-review-response.v2",
        "request_sha256": request["request_sha256"],
        "reviewer": "host-vision",
        "inspected_artifacts": inspected,
        "verdicts": {
            "target_resolved": "resolved",
            "no_new_local_defect": "pass",
            "unchanged_region_regression": "none",
        },
        "findings": [],
        "execution_receipt": execution,
        "publication_acceptance": "not_claimed",
    }
    response_path = attempt_root / "attempt-local-post-repair-review" / "response.json"
    response_path.write_text(json.dumps(response), encoding="utf-8")
    return response_path, response


def _v2_post_review_requested(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    workspace, repaired = _image_machine_repaired_attempt(tmp_path)
    requested = attempt_local_post_review.run_attempt_local_post_review(
        FIXTURE,
        state_path=repaired["next_state_path"],
        execute=True,
        workspace_root=workspace,
    )
    return workspace, requested


def test_v2_post_review_response_advances_only_with_complete_execution(
    tmp_path: Path,
) -> None:
    workspace, requested = _v2_post_review_requested(tmp_path)
    response_path, _ = _v2_post_review_response(
        workspace, requested["request"], with_execution=True
    )
    planned = attempt_local_post_review_response.run_inbound_response(
        FIXTURE,
        state_path=requested["next_state_path"],
        response_path=response_path,
        execute=False,
        workspace_root=workspace,
    )
    assert planned["next_state"] == "visually_re_reviewed"
    assert not planned["receipt_path"].exists()

    result = attempt_local_post_review_response.run_inbound_response(
        FIXTURE,
        state_path=requested["next_state_path"],
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
    )
    assert result["next_state"] == "visually_re_reviewed"
    assert result["required_actor"] == "human_reviewer"
    assert result["published_state"]["publication_acceptance"] == "not_claimed"


def test_v2_post_review_response_without_execution_is_write_free(
    tmp_path: Path,
) -> None:
    workspace, requested = _v2_post_review_requested(tmp_path)
    response_path, _ = _v2_post_review_response(
        workspace, requested["request"], with_execution=False
    )
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    result = attempt_local_post_review_response.run_inbound_response(
        FIXTURE,
        state_path=requested["next_state_path"],
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
    )
    assert result["decision"] == "human_review_required"
    assert result["next_state"] == "post_review_requested"
    assert sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*")) == before


def test_v2_post_review_response_defect_requires_repair(tmp_path: Path) -> None:
    workspace, requested = _v2_post_review_requested(tmp_path)
    response_path, response = _v2_post_review_response(workspace, requested["request"])
    response["verdicts"]["no_new_local_defect"] = "fail"
    response_path.write_text(json.dumps(response), encoding="utf-8")
    result = attempt_local_post_review_response.run_inbound_response(
        FIXTURE,
        state_path=requested["next_state_path"],
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
    )
    assert result["next_state"] == "repair_required"
    assert result["required_actor"] == "none"


def test_v2_post_review_response_rejects_inspection_artifact_drift(tmp_path: Path) -> None:
    workspace, requested = _v2_post_review_requested(tmp_path)
    response_path, _ = _v2_post_review_response(workspace, requested["request"])
    after_render = workspace / str(requested["request"]["after_render"]["path"])
    after_render.write_bytes(b"drift")
    with pytest.raises(
        attempt_local_post_review_response.AttemptLocalPostReviewResponseError,
        match="post_review_request_artifact_hash_drift",
    ):
        attempt_local_post_review_response.run_inbound_response(
            FIXTURE,
            state_path=requested["next_state_path"],
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
        )


def test_v2_post_review_response_recovers_receipt_only_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, requested = _v2_post_review_requested(tmp_path)
    response_path, _ = _v2_post_review_response(workspace, requested["request"])
    original = attempt_local_post_review_response.closed_loop_attempt_state.publish_state

    def fail_state(*args: object, **kwargs: object) -> Path:
        state_module = attempt_local_post_review_response.closed_loop_attempt_state
        raise state_module.ClosedLoopAttemptStateError("injected state failure")

    monkeypatch.setattr(
        attempt_local_post_review_response.closed_loop_attempt_state,
        "publish_state",
        fail_state,
    )
    with pytest.raises(
        attempt_local_post_review_response.AttemptLocalPostReviewResponseError,
        match="injected state failure",
    ):
        attempt_local_post_review_response.run_inbound_response(
            FIXTURE,
            state_path=requested["next_state_path"],
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
        )
    receipt_path = (
        requested["next_state_path"].parent
        / "attempt-local-post-repair-review"
        / "review-receipt.json"
    )
    assert receipt_path.is_file()
    monkeypatch.setattr(
        attempt_local_post_review_response.closed_loop_attempt_state,
        "publish_state",
        original,
    )
    recovered = attempt_local_post_review_response.run_inbound_response(
        FIXTURE,
        state_path=requested["next_state_path"],
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
    )
    assert recovered["next_state"] == "visually_re_reviewed"
    assert recovered["published_state"]["state"] == "visually_re_reviewed"


def test_v2_post_review_response_revalidates_after_receipt_before_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, requested = _v2_post_review_requested(tmp_path)
    response_path, _ = _v2_post_review_response(workspace, requested["request"])
    original = attempt_local_post_review_response.closed_loop_attempt_state.transition_state

    def drift_response(*args: object, **kwargs: object) -> dict[str, object]:
        state = original(*args, **kwargs)
        response_path.write_text('{"drift":true}\n', encoding="utf-8")
        return state

    monkeypatch.setattr(
        attempt_local_post_review_response.closed_loop_attempt_state,
        "transition_state",
        drift_response,
    )
    with pytest.raises(
        attempt_local_post_review_response.AttemptLocalPostReviewResponseError,
        match="response_drift",
    ):
        attempt_local_post_review_response.run_inbound_response(
            FIXTURE,
            state_path=requested["next_state_path"],
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
        )
    assert not any(
        requested["next_state_path"].parent.glob("state-*-visually_re_reviewed.json")
    )


def test_fig_run_dispatches_attempt_local_machine_repaired_to_v2_outbound(
    tmp_path: Path,
) -> None:
    workspace, repaired = _image_machine_repaired_attempt(tmp_path)

    payload = fig_run.run_workflow(
        FIXTURE,
        mode="review",
        goal="close loop",
        execute=False,
        closed_loop_state=repaired["next_state_path"],
        repo_root=workspace,
    )

    assert payload["final_action"] == attempt_local_post_review.ACTION
    assert payload["closed_loop"]["next_state"] == "post_review_requested"
    assert payload["closed_loop"]["publication_acceptance"] == "not_claimed"
    assert not (repaired["next_state_path"].parent / "attempt-local-post-repair-review").exists()


def test_attempt_local_request_has_public_cross_module_validator(tmp_path: Path) -> None:
    workspace, requested = _v2_post_review_requested(tmp_path)

    attempt_local_post_review.validate_request(
        requested["request"], root=workspace, fixture=FIXTURE
    )


def test_fig_run_executes_attempt_local_outbound_and_complete_inbound(
    tmp_path: Path,
) -> None:
    workspace, repaired = _image_machine_repaired_attempt(tmp_path)
    outbound = fig_run.run_workflow(
        FIXTURE,
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=repaired["next_state_path"],
        repo_root=workspace,
    )
    request_path = workspace / outbound["closed_loop"]["request_path"]
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert request["schema"] == attempt_local_post_review.SCHEMA
    response_path, _ = _v2_post_review_response(workspace, request, with_execution=True)

    inbound = fig_run.run_workflow(
        FIXTURE,
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=workspace / outbound["closed_loop"]["next_state_path"],
        closed_loop_response=response_path,
        repo_root=workspace,
    )

    assert inbound["closed_loop"]["next_state"] == "visually_re_reviewed"
    assert inbound["closed_loop"]["publication_acceptance"] == "not_claimed"
    assert inbound["final_stop_boundary"] == "human_reviewer"
    assert inbound["boundary_handoff"]["closeout_checks"] == [
        "record a named human verdict before development acceptance"
    ]


def test_fig_run_attempt_local_missing_execution_remains_write_free(
    tmp_path: Path,
) -> None:
    workspace, requested = _v2_post_review_requested(tmp_path)
    response_path, _ = _v2_post_review_response(
        workspace, requested["request"], with_execution=False
    )
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))

    inbound = fig_run.run_workflow(
        FIXTURE,
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=requested["next_state_path"],
        closed_loop_response=response_path,
        repo_root=workspace,
    )

    assert inbound["closed_loop"]["next_state"] == "post_review_requested"
    assert inbound["final_stop_reason"] == "human_review_boundary"
    handoff = inbound["boundary_handoff"]
    assert handoff["required_actor"] == "human_reviewer"
    assert "complete or clarify the exact host execution and response" in handoff[
        "blocking_reason"
    ]
    assert handoff["closeout_checks"] == [
        "complete or clarify the exact hash-bound host execution and response"
    ]
    assert "named human verdict" not in json.dumps(handoff)
    assert sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*")) == before


def test_fig_run_unknown_post_review_schema_fails_before_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, repaired = _image_machine_repaired_attempt(tmp_path)
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    monkeypatch.setattr(fig_run, "_bound_evidence_schema", lambda *args, **kwargs: "unknown.v9")

    with pytest.raises(ValueError, match="unsupported_repair_execution_packet_schema:unknown.v9"):
        fig_run.run_workflow(
            FIXTURE,
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=repaired["next_state_path"],
            repo_root=workspace,
        )

    assert sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*")) == before


def test_fig_run_unknown_review_request_schema_fails_before_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, requested = _v2_post_review_requested(tmp_path)
    response_path, _ = _v2_post_review_response(workspace, requested["request"])
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    monkeypatch.setattr(fig_run, "_bound_evidence_schema", lambda *args, **kwargs: "unknown.v9")

    with pytest.raises(
        ValueError, match="unsupported_post_repair_visual_review_request_schema:unknown.v9"
    ):
        fig_run.run_workflow(
            FIXTURE,
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=requested["next_state_path"],
            closed_loop_response=response_path,
            repo_root=workspace,
        )

    assert sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*")) == before
