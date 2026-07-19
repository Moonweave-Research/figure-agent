from __future__ import annotations

import json
from pathlib import Path

import authoring_repair_finalize
import authoring_repair_packet
import authoring_repair_rollback
import pytest
from test_authoring_repair_packet import (
    _authorization_artifact,
    _authorized_materialization,
    _fake_strict_compiler,
    _fixture,
    _materialization_authorization,
    _sha256,
)


def _complete_evidence_tree(tmp_path: Path) -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    output = workspace / "attempt" / "repaired_generated.tex"
    build = output.parent / "build"
    build.mkdir(parents=True)
    output.write_text("candidate", encoding="utf-8")
    (build / "strict_status.json").write_text(
        json.dumps(
            {
                "schema": authoring_repair_finalize.STRICT_STATUS_SCHEMA,
                "strict_requested": True,
                "detector_failed": False,
                "state": "passed",
            }
        ),
        encoding="utf-8",
    )
    for name, schema in authoring_repair_finalize.REQUIRED_DETECTOR_REPORTS.items():
        payload = {"schema": schema} if schema is not None else {"total": 0}
        (build / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
    (build / f"{output.stem}.pdf").write_bytes(b"pdf")
    (build / f"{output.stem}.png").write_bytes(b"png")
    return workspace, output, build


def test_failed_receipt_hash_binds_observed_detector_reports(tmp_path: Path) -> None:
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
    packet_path = receipt_path.parent / "repair_packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    failed = authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=_authorization_artifact(receipt_path, authorization),
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, state="failed", returncode=1),
    )

    collisions = output.parent / "build" / "collisions.json"
    record = failed["external_compile"]["evidence_manifest"][
        "detector_reports"
    ]["collisions"]
    assert record == {
        "path": collisions.relative_to(workspace).as_posix(),
        "sha256": _sha256(collisions.read_bytes()),
        "status": "valid",
    }


def test_manifest_distinguishes_missing_and_invalid_detector_reports(
    tmp_path: Path,
) -> None:
    workspace, output, build = _complete_evidence_tree(tmp_path)
    (build / "collisions.json").unlink()
    invalid = build / "semantic_assertions.json"
    invalid.write_text("not-json", encoding="utf-8")

    manifest = authoring_repair_finalize.inspect_compile_evidence_manifest(
        build=build,
        output=output,
        workspace_root=workspace,
    )

    assert manifest["detector_reports"]["collisions"] == {
        "path": "attempt/build/collisions.json",
        "status": "missing",
    }
    assert manifest["detector_reports"]["semantic_assertions"] == {
        "path": "attempt/build/semantic_assertions.json",
        "sha256": _sha256(invalid.read_bytes()),
        "status": "invalid_json",
    }


def test_manifest_marks_symlink_and_nonregular_detector_evidence_invalid(
    tmp_path: Path,
) -> None:
    workspace, output, build = _complete_evidence_tree(tmp_path)
    collisions = build / "collisions.json"
    collisions.unlink()
    collisions.symlink_to("visual_clash.json")
    semantic = build / "semantic_assertions.json"
    semantic.unlink()
    semantic.mkdir()

    manifest = authoring_repair_finalize.inspect_compile_evidence_manifest(
        build=build,
        output=output,
        workspace_root=workspace,
    )

    assert manifest["detector_reports"]["collisions"] == {
        "path": "attempt/build/collisions.json",
        "status": "invalid_file",
    }
    assert manifest["detector_reports"]["semantic_assertions"] == {
        "path": "attempt/build/semantic_assertions.json",
        "status": "invalid_file",
    }


def test_manifest_hash_binds_passing_strict_status(tmp_path: Path) -> None:
    workspace, output, build = _complete_evidence_tree(tmp_path)
    strict_status = build / "strict_status.json"

    manifest = authoring_repair_finalize.inspect_compile_evidence_manifest(
        build=build,
        output=output,
        workspace_root=workspace,
    )

    assert manifest["strict_status"] == {
        "path": "attempt/build/strict_status.json",
        "sha256": _sha256(strict_status.read_bytes()),
        "status": "valid",
    }


def test_complete_passing_manifest_has_no_compile_failure(tmp_path: Path) -> None:
    workspace, output, build = _complete_evidence_tree(tmp_path)
    manifest = authoring_repair_finalize.inspect_compile_evidence_manifest(
        build=build,
        output=output,
        workspace_root=workspace,
    )

    assert (
        authoring_repair_finalize.derive_compile_failure_reason(
            returncode=0,
            evidence_manifest=manifest,
        )
        is None
    )


def test_failed_evidence_validator_rejects_forged_failure_for_passed_evidence(
    tmp_path: Path,
) -> None:
    workspace, output, build = _complete_evidence_tree(tmp_path)
    manifest = authoring_repair_finalize.inspect_compile_evidence_manifest(
        build=build,
        output=output,
        workspace_root=workspace,
    )
    forged_receipt = {
        "output_path": output.relative_to(workspace).as_posix(),
        "external_compile": {
            "returncode": 0,
            "failure_reason": "detector_report_missing_or_invalid",
            "evidence_manifest": manifest,
        },
    }

    with pytest.raises(
        authoring_repair_finalize.AuthoringRepairFinalizeError,
        match="failed compile evidence is inconsistent",
    ):
        authoring_repair_finalize.validate_failed_compile_evidence(
            forged_receipt,
            workspace_root=workspace,
        )


def test_failed_evidence_validator_rejects_detector_hash_drift(
    tmp_path: Path,
) -> None:
    workspace, output, build = _complete_evidence_tree(tmp_path)
    (build / "collisions.json").unlink()
    manifest = authoring_repair_finalize.inspect_compile_evidence_manifest(
        build=build,
        output=output,
        workspace_root=workspace,
    )
    receipt = {
        "output_path": output.relative_to(workspace).as_posix(),
        "external_compile": {
            "returncode": 0,
            "failure_reason": "detector_report_missing_or_invalid",
            "evidence_manifest": manifest,
        },
    }
    assert authoring_repair_finalize.validate_failed_compile_evidence(
        receipt,
        workspace_root=workspace,
    ) == manifest

    (build / "label_hyphenation.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.label-hyphenation.v1",
                "issues": ["drift"],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        authoring_repair_finalize.AuthoringRepairFinalizeError,
        match="failed compile evidence hash drift",
    ):
        authoring_repair_finalize.validate_failed_compile_evidence(
            receipt,
            workspace_root=workspace,
        )


def test_finalizer_rejects_materialized_output_symlink_to_sibling(
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
    packet_path = receipt_path.parent / "repair_packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    authorization_path = _authorization_artifact(receipt_path, authorization)
    sibling = output.with_name("authorized-candidate-sibling.tex")
    output.replace(sibling)
    output.symlink_to(sibling.name)

    with pytest.raises(
        authoring_repair_finalize.AuthoringRepairFinalizeError,
        match="materialized output path must not traverse a symlink",
    ):
        authoring_repair_finalize.finalize_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(tmp_path),
        )

    assert output.is_symlink()
    assert sibling.is_file()
    assert not (output.parent / "build").exists()


def test_rollback_rejects_forged_failed_decision_for_passed_receipt(
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
    packet_path = receipt_path.parent / "repair_packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    authorization_path = _authorization_artifact(receipt_path, authorization)
    passed = authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path),
    )
    passed.update(
        {
            "decision": "materialized_verification_failed",
            "post_render_verification": "failed",
        }
    )
    receipt_path.write_text(json.dumps(passed), encoding="utf-8")

    with pytest.raises(
        authoring_repair_rollback.AuthoringRepairRollbackError,
        match="failed compile evidence is inconsistent",
    ):
        authoring_repair_rollback.rollback_failed_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
            workspace_root=workspace,
        )

    assert output.is_file()


def test_rollback_rejects_retained_detector_report_hash_drift(tmp_path: Path) -> None:
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
    packet_path = receipt_path.parent / "repair_packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    authorization_path = _authorization_artifact(receipt_path, authorization)
    authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, state="failed", returncode=1),
    )
    collisions = output.parent / "build" / "collisions.json"
    collisions.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-collisions.v1",
                "collisions": [{"id": "drift"}],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        authoring_repair_rollback.AuthoringRepairRollbackError,
        match="failed compile evidence hash drift",
    ):
        authoring_repair_rollback.rollback_failed_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
            workspace_root=workspace,
        )

    assert output.is_file()


def test_rollback_revalidates_live_adjudicated_binding(tmp_path: Path) -> None:
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
    packet_path = receipt_path.parent / "repair_packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    authorization_path = _authorization_artifact(receipt_path, authorization)
    authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, state="failed", returncode=1),
    )
    binding_path = workspace / packet["adjudicated_repair_binding"]["path"]
    binding_path.write_text(
        binding_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        authoring_repair_rollback.AuthoringRepairRollbackError,
        match="repair packet authority invalid",
    ):
        authoring_repair_rollback.rollback_failed_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
            workspace_root=workspace,
        )

    assert output.is_file()


def test_legacy_v4_rollback_requires_explicit_compatibility_opt_in(
    tmp_path: Path,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    output_relative = (
        "examples/demo/review/failure-first/execution-repair-v1/"
        "repaired_generated.tex"
    )
    packet, _prompt = authoring_repair_packet.compile_repair_execution_packet(
        "demo",
        workspace_root=workspace,
        model_id="gpt-5.5",
        source_path=source.relative_to(workspace).as_posix(),
        target_contract=contract.relative_to(workspace).as_posix(),
        output_path=output_relative,
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
        allow_legacy_packet=True,
    )
    authorization = _materialization_authorization(
        packet,
        output_sha256=preview["output_sha256"],
        preview_sha256=preview["preview_sha256"],
    )
    output = workspace / output_relative
    receipt_path = output.parent / "materialization_receipt.json"
    authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        authorization=authorization,
        receipt_path=receipt_path,
        allow_legacy_packet=True,
    )
    packet_path = output.parent / "repair_packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    authorization_path = _authorization_artifact(receipt_path, authorization)
    authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, state="failed", returncode=1),
        allow_legacy_packet=True,
    )

    with pytest.raises(
        authoring_repair_rollback.AuthoringRepairRollbackError,
        match="explicit compatibility opt-in",
    ):
        authoring_repair_rollback.rollback_failed_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
            workspace_root=workspace,
        )

    assert output.is_file()
    rolled_back = authoring_repair_rollback.rollback_failed_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        allow_legacy_packet=True,
    )
    assert rolled_back["rollback"]["status"] == "completed"
    assert not output.exists()
