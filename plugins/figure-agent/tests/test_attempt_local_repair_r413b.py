from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import attempt_local_repair_binding as packet_boundary  # noqa: E402
import authoring_repair_finalize  # noqa: E402
import authoring_repair_packet  # noqa: E402
import authoring_repair_rollback  # noqa: E402
import closed_loop_machine_repair  # noqa: E402
import closed_loop_repair_authorization  # noqa: E402
import closed_loop_repair_candidate  # noqa: E402
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
    authorization_path.write_text(
        json.dumps(_authorization(packet, preview)), encoding="utf-8"
    )
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
            "sha256": "sha256:"
            + hashlib.sha256(response_path.read_bytes()).hexdigest(),
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
    authorization_path.write_text(
        json.dumps(_authorization(packet, preview)), encoding="utf-8"
    )
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
