from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

import authoring_repair_packet
import pytest
import repair_transaction

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _materialization_authorization(
    packet: dict[str, object],
    *,
    output_sha256: str,
    preview_sha256: str,
) -> dict[str, object]:
    return {
        "schema": "figure-agent.human-decision-record.v1",
        "fixture": "demo",
        "packet_schema": "figure-agent.repair-execution-packet.v3",
        "packet_path": (
            "examples/demo/review/failure-first/execution-repair-v1/repair_packet.json"
        ),
        "packet_recommendation": "materialize_authoring_repair_candidate",
        "queue_run_id": "authoring-repair-materialize-001",
        "decision_kind": "materialize_authoring_repair_candidate",
        "agent_recommendation": "Materialize exactly this additive repair candidate.",
        "human_decision": "approve this exact additive repair candidate",
        "human_note": "Approval is bound to packet, output path, and output hash.",
        "reviewer": "named-reviewer",
        "follow_up": {
            "command": (
                "fig-agent authoring-repair-materialize "
                "--apply --authorization decision.json"
            )
        },
        "mutation_boundary": "additive_artifact_materialization_allowed",
        "authorized_packet_sha256": packet["packet_sha256"],
        "authorized_output_path": packet["output_path"],
        "authorized_output_sha256": output_sha256,
        "authorized_preview_sha256": preview_sha256,
    }


def _fixture(tmp_path: Path, *, attribution: str = "exact") -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    attempt = (
        workspace
        / "examples"
        / "demo"
        / "review"
        / "failure-first"
        / "execution-binding-v1"
    )
    attempt.mkdir(parents=True)
    source = attempt / "treatment_generated.tex"
    source.write_text(
        "\\documentclass[tikz,border=4pt]{standalone}\n"
        "\\usepackage{tikz}\n"
        "\\usepackage{polymer-paper-preamble}\n"
        "% repair:label:start\n"
        "\\node {repeated dispersive trapping};\n"
        "% repair:label:end\n"
        "\\node {S60 -> S80};\n",
        encoding="utf-8",
    )
    repair = (
        workspace
        / "examples"
        / "demo"
        / "review"
        / "failure-first"
        / "execution-repair-v1"
    )
    repair.mkdir(parents=True)
    report = repair / "collisions.json"
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-collisions.v1",
                "collisions": [
                    {
                        "id": "TC001",
                        "texts": ["repeated", "trapping"],
                        "source_mapping": None,
                    },
                    {
                        "id": "TC002",
                        "texts": ["S60", "S80"],
                        "source_mapping": None,
                    },
                ],
                "total": 2,
            }
        ),
        encoding="utf-8",
    )
    contract = repair / "repair_targets.json"
    contract.write_text(
        json.dumps(
            {
                "schema": "figure-agent.repair-target-contract.v1",
                "source_path": source.relative_to(workspace).as_posix(),
                "source_sha256": _sha256(source.read_bytes()),
                "targets": [
                    {
                        "finding": {
                            "report_path": report.relative_to(workspace).as_posix(),
                            "id": "TC001",
                        },
                        "attribution": {"state": attribution},
                        "selector": {
                            "kind": "semantic_anchor",
                            "selector_id": "panel-a-label",
                            "anchor_start": "% repair:label:start",
                            "anchor_end": "% repair:label:end",
                        },
                        "repair_family": "label_reflow",
                        "protected_invariants": ["S60 -> S80"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return workspace, source, contract


def _authorized_materialization(
    tmp_path: Path,
) -> tuple[Path, dict[str, object], dict[str, object], dict[str, object], Path, Path]:
    workspace, source, contract = _fixture(tmp_path)
    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )
    response = {
        "replacement_utf8": r"\node[yshift=-2mm] {repeated dispersive trapping};",
        "change_summary": "Lower the colliding label.",
    }
    preview = authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        apply=False,
    )
    output = workspace / packet["output_path"]
    receipt = output.parent / "materialization_receipt.json"
    authorization = _materialization_authorization(
        packet,
        output_sha256=str(preview["output_sha256"]),
        preview_sha256=str(preview["preview_sha256"]),
    )
    return workspace, packet, response, authorization, output, receipt


def test_compiles_one_hash_bound_exact_repair_packet(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)

    packet, prompt = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )

    assert packet["schema"] == "figure-agent.repair-execution-packet.v3"
    assert packet["source"]["sha256"] == _sha256(source.read_bytes())
    assert packet["editable_target"]["finding_id"] == "TC001"
    assert packet["editable_target"]["selector"]["source_hash"] == _sha256(
        source.read_bytes()
    )
    assert packet["change_budget"] == {
        "max_attempts": 1,
        "max_source_blocks": 1,
        "max_changed_lines": 6,
    }
    assert packet["review_only_findings"] == [
        {"finding_id": "TC002", "attribution": "unbound"}
    ]
    assert packet["publication_acceptance"] == "not_claimed"
    assert packet["packet_sha256"] == authoring_repair_packet.canonical_packet_sha256(
        packet
    )
    assert "Do not use filesystem or shell tools" in prompt
    assert packet["response_schema"]["required"] == [
        "replacement_utf8",
        "change_summary",
    ]
    assert "Change content only between the exact anchor lines" in prompt
    assert "S60 -> S80" in prompt
    assert r"\node {repeated dispersive trapping};" in prompt
    assert r"\documentclass" not in prompt


def test_binds_repository_execution_cwd_into_repair_output(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)

    packet, prompt = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
        execution_cwd="plugins/figure-agent",
    )

    assert packet["execution_cwd"] == "plugins/figure-agent"
    assert packet["repository_output_path"] == (
        "plugins/figure-agent/examples/demo/review/failure-first/"
        "execution-repair-v1/repaired_generated.tex"
    )
    assert (
        "The controller will materialize a validated candidate at "
        "[plugins/figure-agent/examples/demo/review/failure-first/"
        "execution-repair-v1/repaired_generated.tex]."
    ) in prompt


def test_accepts_hash_bound_comparable_source_as_repair_seed(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    comparable = (
        workspace
        / "examples/demo/review/failure-first/comparable-v2/verified_generated.tex"
    )
    comparable.parent.mkdir(parents=True)
    comparable.write_bytes(source.read_bytes())
    contract_payload = json.loads(contract.read_text(encoding="utf-8"))
    contract_payload["source_path"] = comparable.relative_to(workspace).as_posix()
    contract_payload["source_sha256"] = _sha256(comparable.read_bytes())
    contract.write_text(json.dumps(contract_payload), encoding="utf-8")

    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=comparable.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )

    assert packet["source"]["path"].endswith(
        "comparable-v2/verified_generated.tex"
    )


def test_accepts_prior_repair_output_as_hash_bound_next_repair_seed(
    tmp_path: Path,
) -> None:
    workspace, source, old_contract = _fixture(tmp_path)
    prior_source = old_contract.parent / "repaired_generated.tex"
    prior_source.write_bytes(source.read_bytes())
    next_attempt = old_contract.parent.parent / "execution-repair-v2"
    next_attempt.mkdir()
    next_report = next_attempt / "collisions.json"
    next_report.write_bytes((old_contract.parent / "collisions.json").read_bytes())
    contract_payload = json.loads(old_contract.read_text(encoding="utf-8"))
    contract_payload["source_path"] = prior_source.relative_to(workspace).as_posix()
    contract_payload["source_sha256"] = _sha256(prior_source.read_bytes())
    contract_payload["targets"][0]["finding"]["report_path"] = (
        next_report.relative_to(workspace).as_posix()
    )
    next_contract = next_attempt / "repair_targets.json"
    next_contract.write_text(json.dumps(contract_payload), encoding="utf-8")

    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=prior_source.relative_to(workspace).as_posix(),
        target_contract=next_contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v2/"
            "repaired_generated.tex"
        ),
    )

    assert packet["source"]["path"].endswith(
        "execution-repair-v1/repaired_generated.tex"
    )


def test_accepts_exact_undeclared_geometry_finding_as_repair_target(
    tmp_path: Path,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    report = contract.parent / "collisions.json"
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.undeclared-geometry.v1",
                "candidates": [
                    {
                        "id": "UG001",
                        "kind": "label_crosses_semantic_path",
                        "nearest_text": "trapping",
                    }
                ],
                "total": 1,
            }
        ),
        encoding="utf-8",
    )
    payload = json.loads(contract.read_text(encoding="utf-8"))
    payload["targets"] = [payload["targets"][0]]
    payload["targets"][0]["finding"]["id"] = "UG001"
    contract.write_text(json.dumps(payload), encoding="utf-8")

    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )

    assert packet["editable_target"]["finding_id"] == "UG001"


def test_accepts_exact_visual_clash_finding_as_repair_target(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    report = contract.parent / "collisions.json"
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.visual-clash.v1",
                "candidates": [
                    {"id": "VC001", "kind": "text_on_path", "text": "retained"}
                ],
                "total": 1,
            }
        ),
        encoding="utf-8",
    )
    payload = json.loads(contract.read_text(encoding="utf-8"))
    payload["targets"] = [payload["targets"][0]]
    payload["targets"][0]["finding"]["id"] = "VC001"
    contract.write_text(json.dumps(payload), encoding="utf-8")

    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )

    assert packet["editable_target"]["finding_id"] == "VC001"


def test_accepts_exact_human_correction_as_repair_target(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    report = contract.parent / "collisions.json"
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.human-correction-findings.v1",
                "bound_source_sha256": _sha256(source.read_bytes()),
                "findings": [
                    {
                        "id": "HF001",
                        "subject": "carrier_label",
                        "finding": "label overlaps the carrier",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    payload = json.loads(contract.read_text(encoding="utf-8"))
    payload["targets"] = [payload["targets"][0]]
    payload["targets"][0]["finding"]["id"] = "HF001"
    contract.write_text(json.dumps(payload), encoding="utf-8")

    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )

    assert packet["editable_target"]["finding_id"] == "HF001"


def test_rejects_human_correction_bound_to_stale_source(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    report = contract.parent / "collisions.json"
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.human-correction-findings.v1",
                "bound_source_sha256": "sha256:" + "0" * 64,
                "findings": [{"id": "HF001", "finding": "stale review"}],
            }
        ),
        encoding="utf-8",
    )
    payload = json.loads(contract.read_text(encoding="utf-8"))
    payload["targets"] = [payload["targets"][0]]
    payload["targets"][0]["finding"]["id"] = "HF001"
    contract.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="human finding source hash drift",
    ):
        authoring_repair_packet.compile_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            source_path=source.relative_to(workspace).as_posix(),
            target_contract=contract.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )


def test_materializes_valid_candidate_only_after_controller_validation(
    tmp_path: Path,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )
    replacement = r"\node[yshift=-2mm] {repeated dispersive trapping};"
    candidate = source.read_text(encoding="utf-8").replace(
        r"\node {repeated dispersive trapping};", replacement
    )
    receipt_path = (
        workspace
        / "examples/demo/review/failure-first/execution-repair-v1/"
        "materialization_receipt.json"
    )
    response = {
        "replacement_utf8": replacement,
        "change_summary": "Lower the colliding label.",
    }
    preview = authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        apply=False,
    )

    receipt = authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        authorization=_materialization_authorization(
            packet,
            output_sha256=_sha256(candidate.encode("utf-8")),
            preview_sha256=str(preview["preview_sha256"]),
        ),
        receipt_path=receipt_path,
    )

    output = workspace / packet["output_path"]
    assert output.read_text(encoding="utf-8") == candidate
    assert receipt["schema"] == "figure-agent.repair-materialization-receipt.v2"
    assert receipt["decision"] == "materialized_verification_pending"
    assert receipt["changed_source_blocks"] == 1
    assert receipt["changed_lines"] == 2
    assert receipt["authorization"]["reviewer"] == "named-reviewer"
    assert receipt["authorization"]["authorized_output_sha256"] == _sha256(
        candidate.encode("utf-8")
    )
    assert receipt["publication_acceptance"] == "not_claimed"
    assert json.loads(receipt_path.read_text(encoding="utf-8")) == receipt


def test_materializer_refuses_to_write_without_human_authorization(
    tmp_path: Path,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )
    output = workspace / packet["output_path"]

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="materialization authorization missing",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            {
                "replacement_utf8": (
                    r"\node[yshift=-2mm] {repeated dispersive trapping};"
                ),
                "change_summary": "Lower the colliding label.",
            },
            workspace_root=workspace,
        )

    assert not output.exists()


def test_materializer_dry_run_exposes_hash_bound_candidate_without_writing(
    tmp_path: Path,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )
    replacement = r"\node[yshift=-2mm] {repeated dispersive trapping};"
    candidate = source.read_text(encoding="utf-8").replace(
        r"\node {repeated dispersive trapping};", replacement
    )

    preview = authoring_repair_packet.materialize_repair_candidate(
        packet,
        {
            "replacement_utf8": replacement,
            "change_summary": "Lower the colliding label.",
        },
        workspace_root=workspace,
        apply=False,
    )

    assert preview["schema"] == "figure-agent.repair-materialization-preview.v1"
    assert preview["packet_sha256"] == packet["packet_sha256"]
    assert preview["output_path"] == packet["output_path"]
    assert preview["output_sha256"] == _sha256(candidate.encode("utf-8"))
    assert preview["publication_acceptance"] == "not_claimed"
    assert not (workspace / packet["output_path"]).exists()


def test_materializer_refuses_when_attempt_transaction_lock_exists(
    tmp_path: Path,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )
    response = {
        "replacement_utf8": r"\node[yshift=-2mm] {repeated dispersive trapping};",
        "change_summary": "Lower the colliding label.",
    }
    preview = authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        apply=False,
    )
    output = workspace / packet["output_path"]
    receipt_path = output.parent / "materialization_receipt.json"
    lock = output.parent / ".materialization.lock"
    lock.write_text("active", encoding="utf-8")

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="materialization transaction already active",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace,
            authorization=_materialization_authorization(
                packet,
                output_sha256=str(preview["output_sha256"]),
                preview_sha256=str(preview["preview_sha256"]),
            ),
            receipt_path=receipt_path,
        )

    assert not output.exists()
    assert not receipt_path.exists()


def test_materializer_refuses_authorization_for_different_output_hash(
    tmp_path: Path,
) -> None:
    workspace, packet, response, authorization, output, receipt_path = (
        _authorized_materialization(tmp_path)
    )
    authorization["authorized_output_sha256"] = "sha256:" + "0" * 64

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="materialization_decision_output_hash_mismatch",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace,
            authorization=authorization,
            receipt_path=receipt_path,
        )

    assert not output.exists()
    assert not receipt_path.exists()


def test_materializer_refuses_summary_drift_after_preview_authorization(
    tmp_path: Path,
) -> None:
    workspace, packet, response, authorization, output, receipt_path = (
        _authorized_materialization(tmp_path)
    )
    response["change_summary"] = "A different provenance claim for the same bytes."

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="materialization_decision_preview_hash_mismatch",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace,
            authorization=authorization,
            receipt_path=receipt_path,
        )

    assert not output.exists()
    assert not receipt_path.exists()


def test_materializer_replay_preserves_existing_output_and_receipt(
    tmp_path: Path,
) -> None:
    workspace, packet, response, authorization, output, receipt_path = (
        _authorized_materialization(tmp_path)
    )
    authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        authorization=authorization,
        receipt_path=receipt_path,
    )
    output_before = output.read_bytes()
    receipt_before = receipt_path.read_bytes()

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="output path already exists",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace,
            authorization=authorization,
            receipt_path=receipt_path,
        )

    assert output.read_bytes() == output_before
    assert receipt_path.read_bytes() == receipt_before


def test_materializer_output_failure_leaves_write_ahead_recovery_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, packet, response, authorization, output, receipt_path = (
        _authorized_materialization(tmp_path)
    )

    original_atomic_write = (
        authoring_repair_packet.repair_transaction.atomic_write_text
    )

    def fail_only_output(path: Path, text: str) -> None:
        if path == output:
            raise OSError("output storage interrupted")
        original_atomic_write(path, text)

    monkeypatch.setattr(
        authoring_repair_packet.repair_transaction,
        "atomic_write_text",
        fail_only_output,
    )

    with pytest.raises(OSError, match="output storage interrupted"):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace,
            authorization=authorization,
            receipt_path=receipt_path,
        )

    assert not output.exists()
    recovery = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert recovery["decision"] == "materialization_prepared"
    assert recovery["recovery_required"] is True
    assert (
        recovery["rollback"]["strategy"]
        == "delete_materialized_output_if_hash_matches"
    )
    assert recovery["rollback"]["pre_transaction_state"] == "absent"
    assert recovery["rollback"]["output_path"] == packet["output_path"]
    assert recovery["rollback"]["output_sha256"] == recovery["output_sha256"]


def test_materializer_final_receipt_failure_preserves_recovery_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, packet, response, authorization, output, receipt_path = (
        _authorized_materialization(tmp_path)
    )
    original_atomic_json = authoring_repair_packet.repair_transaction.atomic_write_json
    writes = 0

    def fail_final_receipt(path: Path, payload: dict[str, object]) -> None:
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("final receipt interrupted")
        original_atomic_json(path, payload)

    monkeypatch.setattr(
        authoring_repair_packet.repair_transaction,
        "atomic_write_json",
        fail_final_receipt,
    )

    with pytest.raises(OSError, match="final receipt interrupted"):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace,
            authorization=authorization,
            receipt_path=receipt_path,
        )

    recovery = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert recovery["decision"] == "materialization_prepared"
    assert recovery["recovery_required"] is True
    assert output.is_file()
    assert _sha256(output.read_bytes()) == recovery["output_sha256"]
    assert (
        recovery["rollback"]["strategy"]
        == "delete_materialized_output_if_hash_matches"
    )
    assert recovery["rollback"]["output_path"] == packet["output_path"]
    assert recovery["rollback"]["output_sha256"] == recovery["output_sha256"]


def test_atomic_write_fsyncs_parent_directory_after_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "receipt.json"
    events: list[str] = []
    original_replace = repair_transaction.os.replace
    original_fsync = repair_transaction.os.fsync

    def observed_replace(source: str | Path, destination: str | Path) -> None:
        original_replace(source, destination)
        events.append("replace")

    def observed_fsync(fd: int) -> None:
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            events.append("directory_fsync")
        original_fsync(fd)

    monkeypatch.setattr(repair_transaction.os, "replace", observed_replace)
    monkeypatch.setattr(repair_transaction.os, "fsync", observed_fsync)

    repair_transaction.atomic_write_text(path, "durable\n")

    assert path.read_text(encoding="utf-8") == "durable\n"
    assert events[-2:] == ["replace", "directory_fsync"]


def test_materializer_preserves_boundary_blank_padding(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "% repair:label:end",
            "\n% repair:label:end",
        ),
        encoding="utf-8",
    )
    contract_payload = json.loads(contract.read_text(encoding="utf-8"))
    contract_payload["source_sha256"] = _sha256(source.read_bytes())
    contract.write_text(json.dumps(contract_payload), encoding="utf-8")
    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )
    response = {
        "replacement_utf8": r"\node[text width=4cm] {repeated dispersive trapping};",
        "change_summary": "Widen the label without changing block padding.",
    }
    preview = authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        apply=False,
    )

    receipt = authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        authorization=_materialization_authorization(
            packet,
            output_sha256=str(preview["output_sha256"]),
            preview_sha256=str(preview["preview_sha256"]),
        ),
        receipt_path=(
            workspace
            / "examples/demo/review/failure-first/execution-repair-v1/"
            "materialization_receipt.json"
        ),
    )

    output = workspace / packet["output_path"]
    assert (
        r"\node[text width=4cm] {repeated dispersive trapping};"
        "\n\n% repair:label:end"
    ) in output.read_text(encoding="utf-8")
    assert receipt["preserved_boundary_blank_lines"] == 1


def test_materializer_rejects_change_outside_exact_anchor(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )
    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="replacement must not contain anchor lines",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            {
                "replacement_utf8": "% repair:label:end",
                "change_summary": "Unsafe edit.",
            },
            workspace_root=workspace,
        )


def test_materializer_rejects_literal_escaped_newline(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    packet, _ = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=(
            "examples/demo/review/failure-first/execution-repair-v1/"
            "repaired_generated.tex"
        ),
    )

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="literal escaped newline",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            {
                "replacement_utf8": (
                    r"\node[yshift=-2mm] {repeated\n  dispersive trapping};"
                ),
                "change_summary": "Malformed serialized line break.",
            },
            workspace_root=workspace,
        )


def test_rejects_ambiguous_or_unbound_repair_target(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path, attribution="ambiguous")

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="exact attribution required",
    ):
        authoring_repair_packet.compile_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            source_path=source.relative_to(workspace).as_posix(),
            target_contract=contract.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )


def test_rejects_source_hash_drift(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    source.write_text(source.read_text(encoding="utf-8") + "% drift\n", encoding="utf-8")

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="source hash drift",
    ):
        authoring_repair_packet.compile_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            source_path=source.relative_to(workspace).as_posix(),
            target_contract=contract.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )


def test_rejects_output_outside_additive_repair_attempt(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="execution-repair-vN",
    ):
        authoring_repair_packet.compile_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            source_path=source.relative_to(workspace).as_posix(),
            target_contract=contract.relative_to(workspace).as_posix(),
            output_path=source.relative_to(workspace).as_posix(),
        )


def test_cli_writes_additive_repair_packet_and_prompt(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    repair_root = (
        "examples/demo/review/failure-first/execution-repair-v1"
    )
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "authoring-repair-packet",
            "demo",
            "--model-id",
            "gpt-5.5",
            "--source",
            source.relative_to(workspace).as_posix(),
            "--target-contract",
            contract.relative_to(workspace).as_posix(),
            "--output-path",
            f"{repair_root}/repaired_generated.tex",
            "--packet-out",
            f"{repair_root}/repair_packet.json",
            "--prompt-out",
            f"{repair_root}/repair_prompt.md",
        ],
        cwd=PLUGIN_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (workspace / repair_root / "repair_packet.json").is_file()
    assert (workspace / repair_root / "repair_prompt.md").is_file()
    assert not (workspace / repair_root / "repaired_generated.tex").exists()

    response = workspace / repair_root / "repair_response.json"
    response.write_text(
        json.dumps(
            {
                "replacement_utf8": (
                    r"\node[yshift=-2mm] {repeated dispersive trapping};"
                ),
                "change_summary": "Lower the colliding label.",
            }
        ),
        encoding="utf-8",
    )
    preview_result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "authoring-repair-materialize",
            "--packet",
            f"{repair_root}/repair_packet.json",
            "--response",
            f"{repair_root}/repair_response.json",
            "--receipt-out",
            f"{repair_root}/materialization_receipt.json",
            "--dry-run",
        ],
        cwd=PLUGIN_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert preview_result.returncode == 0, preview_result.stderr
    preview = json.loads(preview_result.stdout)
    assert preview["schema"] == "figure-agent.repair-materialization-preview.v1"
    assert not (workspace / repair_root / "repaired_generated.tex").exists()
    assert not (workspace / repair_root / "materialization_receipt.json").exists()

    packet = json.loads(
        (workspace / repair_root / "repair_packet.json").read_text(encoding="utf-8")
    )
    authorization = workspace / repair_root / "materialization_authorization.json"
    authorization.write_text(
        json.dumps(
            _materialization_authorization(
                packet,
                output_sha256=preview["output_sha256"],
                preview_sha256=preview["preview_sha256"],
            )
        ),
        encoding="utf-8",
    )
    materialize = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "authoring-repair-materialize",
            "--packet",
            f"{repair_root}/repair_packet.json",
            "--response",
            f"{repair_root}/repair_response.json",
            "--receipt-out",
            f"{repair_root}/materialization_receipt.json",
            "--apply",
            "--authorization",
            f"{repair_root}/materialization_authorization.json",
        ],
        cwd=PLUGIN_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert materialize.returncode == 0, materialize.stderr
    assert (workspace / repair_root / "repaired_generated.tex").is_file()
    assert (workspace / repair_root / "materialization_receipt.json").is_file()
