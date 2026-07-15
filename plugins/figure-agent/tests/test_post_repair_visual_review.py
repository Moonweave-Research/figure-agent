from __future__ import annotations

import hashlib
import json
from pathlib import Path

import authoring_repair_finalize
import authoring_repair_packet
import critique_zoom_crops
import post_repair_visual_review
import pytest
from PIL import Image


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    workspace = tmp_path / "workspace"
    example = workspace / "examples" / "demo"
    attempt = example / "review" / "failure-first" / "execution-repair-v1"
    build = attempt / "build"
    crops = build / "audit_crops"
    crops.mkdir(parents=True)
    critique = example / "critique.md"
    critique.write_text("---\nschema: figure-agent.critique.v1.17\n---\n", encoding="utf-8")
    adjudication = example / "critique_adjudication.yaml"
    adjudication.write_text(
        "schema: figure-agent.critique-adjudication.v1\n"
        "fixture: demo\n"
        f"source_critique_hash: {_sha256(critique)}\n"
        "decisions:\n"
        "- finding_id: C001\n"
        "  decision: apply\n"
        "  reason: bounded repair\n"
        "  patch_target: panel A\n"
        "  evidence: critique C001\n",
        encoding="utf-8",
    )
    spec = example / "spec.yaml"
    spec.write_text("name: demo\npanels: []\n", encoding="utf-8")
    report = attempt / "collisions.json"
    report.write_text('{"schema":"figure-agent.text-collisions.v1"}\n', encoding="utf-8")
    registry = attempt / "source_selectors.json"
    registry.write_text(
        '{"schema":"figure-agent.source-selector-registry.v1"}\n',
        encoding="utf-8",
    )
    adjudication.write_text(
        "schema: figure-agent.critique-adjudication.v1\n"
        "fixture: demo\n"
        f"source_critique_hash: {_sha256(critique)}\n"
        "decisions:\n"
        "- finding_id: C001\n"
        "  decision: apply\n"
        "  reason: bounded repair\n"
        "  patch_target: panel A\n"
        "  evidence: critique C001\n"
        "  repair_evidence:\n"
        f"    report_path: {report.relative_to(workspace).as_posix()}\n"
        "    finding_id: TC001\n"
        f"    selector_registry_path: {registry.relative_to(workspace).as_posix()}\n",
        encoding="utf-8",
    )
    baseline_source = attempt / "baseline.tex"
    baseline_source.write_text("\\node {baseline};\n", encoding="utf-8")
    before_render = example / "build" / "demo.png"
    before_render.parent.mkdir()
    before_render.write_bytes(b"before-render")
    before_pdf = example / "build" / "demo.pdf"
    before_pdf.write_bytes(b"%PDF-before\n")
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-collisions.v1",
                "fixture": "demo",
                "render_pdf": "build/demo.pdf",
                "render_pdf_sha256": _sha256(before_pdf),
                "render_path": "build/demo.png",
                "render_sha256": _sha256(before_render),
            }
        ),
        encoding="utf-8",
    )
    baseline_manifest = example / "build" / "baseline_audit_crops" / "manifest.json"
    baseline_manifest.parent.mkdir()
    baseline_manifest.write_text(
        json.dumps(
            {
                "schema": "figure-agent.audit-crop-manifest.v1",
                "fixture": "demo",
                "render_path": "build/demo.png",
                "required_crop_ids": [],
                "crops": [],
            }
        ),
        encoding="utf-8",
    )
    target_contract = attempt / "repair_targets.json"
    target_contract.write_text(
        '{"schema":"figure-agent.repair-target-contract.v1"}\n',
        encoding="utf-8",
    )
    source = attempt / "repaired_generated.tex"
    source.write_text("\\node {repaired};\n", encoding="utf-8")
    render = build / "repaired_generated.png"
    render.write_bytes(b"render")
    render_pdf = build / "repaired_generated.pdf"
    render_pdf.write_bytes(b"%PDF-repaired\n")
    strict_status = build / "strict_status.json"
    strict_status.write_text(
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
    detector_records = {}
    for name, schema in authoring_repair_finalize.REQUIRED_DETECTOR_REPORTS.items():
        report_path = build / f"{name}.json"
        report_path.write_text(
            json.dumps({"schema": schema or f"test.{name}.v1"}),
            encoding="utf-8",
        )
        detector_records[name] = {
            "path": report_path.relative_to(workspace).as_posix(),
            "sha256": _sha256(report_path),
            **({"schema": schema} if schema is not None else {}),
        }
    target = crops / "target.png"
    neighbor = crops / "neighbor.png"
    print_scale = crops / "print.png"
    target.write_bytes(b"target")
    neighbor.write_bytes(b"neighbor")
    print_scale.write_bytes(b"print")
    crop_manifest = crops / "manifest.json"
    render_relative = render.relative_to(example).as_posix()
    crop_records = [
        {
            "id": "after_full",
            "kind": "zoom_crop",
            "path": render_relative,
            "source_path": render_relative,
            "bbox_px": [0, 0, 100, 80],
            "sha256": _sha256(render),
        },
        {
            "id": "target",
            "kind": "zoom_crop",
            "path": target.relative_to(example).as_posix(),
            "source_path": render_relative,
            "bbox_px": [10, 10, 50, 50],
            "sha256": _sha256(target),
        },
        {
            "id": "neighbor",
            "kind": "zoom_crop",
            "path": neighbor.relative_to(example).as_posix(),
            "source_path": render_relative,
            "bbox_px": [50, 10, 90, 50],
            "sha256": _sha256(neighbor),
        },
        {
            "id": "print",
            "kind": "print_scale",
            "path": print_scale.relative_to(example).as_posix(),
            "source_path": render_relative,
            "size_px": [360, 288],
            "sha256": _sha256(print_scale),
        },
    ]
    crop_manifest.write_text(
        json.dumps(
            {
                "schema": "figure-agent.audit-crop-manifest.v1",
                "fixture": "demo",
                "render_path": render_relative,
                "required_crop_ids": [item["id"] for item in crop_records],
                "crops": crop_records,
            }
        ),
        encoding="utf-8",
    )
    binding = attempt / "critique_repair_binding.json"
    binding.write_text(
        json.dumps(
            {
                "schema": "figure-agent.adjudicated-repair-binding.v1",
                "fixture": "demo",
                "critique": {
                    "path": critique.relative_to(workspace).as_posix(),
                    "sha256": _sha256(critique),
                    "finding_id": "C001",
                },
                "adjudication": {
                    "path": adjudication.relative_to(workspace).as_posix(),
                    "sha256": _sha256(adjudication),
                    "decision": "apply",
                },
                "machine_finding": {
                    "report_path": report.relative_to(workspace).as_posix(),
                    "report_sha256": _sha256(report),
                    "finding_id": "TC001",
                },
                "selector_registry": {
                    "path": registry.relative_to(workspace).as_posix(),
                    "sha256": _sha256(registry),
                },
                "source": {
                    "path": baseline_source.relative_to(workspace).as_posix(),
                    "sha256": _sha256(baseline_source),
                },
                "spec": {
                    "path": spec.relative_to(workspace).as_posix(),
                    "sha256": _sha256(spec),
                },
                "current_render": {
                    "path": before_render.relative_to(workspace).as_posix(),
                    "sha256": _sha256(before_render),
                },
                "current_pdf": {
                    "path": before_pdf.relative_to(workspace).as_posix(),
                    "sha256": _sha256(before_pdf),
                },
                "crop_manifest": {
                    "path": baseline_manifest.relative_to(workspace).as_posix(),
                    "sha256": _sha256(baseline_manifest),
                },
                "attribution_state": "exact",
                "target_contract": {
                    "path": target_contract.relative_to(workspace).as_posix(),
                    "sha256": _sha256(target_contract),
                },
                "publication_acceptance": "not_claimed",
            }
        ),
        encoding="utf-8",
    )
    packet = attempt / "repair_packet.json"
    packet_payload = {
        "schema": "figure-agent.repair-execution-packet.v3",
        "fixture": "demo",
        "target_contract": {
            "path": target_contract.relative_to(workspace).as_posix(),
            "sha256": _sha256(target_contract),
        },
        "output_path": source.relative_to(workspace).as_posix(),
        "publication_acceptance": "not_claimed",
    }
    packet_payload["packet_sha256"] = (
        authoring_repair_packet.canonical_packet_sha256(packet_payload)
    )
    packet.write_text(json.dumps(packet_payload), encoding="utf-8")
    receipt = attempt / "materialization_receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema": "figure-agent.repair-materialization-receipt.v2",
                "fixture": "demo",
                "decision": "materialized_machine_verified_human_review_pending",
                "packet_sha256": packet_payload["packet_sha256"],
                "output_path": source.relative_to(workspace).as_posix(),
                "output_sha256": _sha256(source),
                "post_render_verification": "passed",
                "external_compile": {
                    "command": [
                        "bash",
                        "scripts/compile.sh",
                        source.relative_to(workspace).as_posix(),
                    ],
                    "returncode": 0,
                    "stdout_sha256": "sha256:" + "0" * 64,
                    "stderr_sha256": "sha256:" + "0" * 64,
                    "strict_status": {
                        "path": strict_status.relative_to(workspace).as_posix(),
                        "sha256": _sha256(strict_status),
                        "schema": authoring_repair_finalize.STRICT_STATUS_SCHEMA,
                        "state": "passed",
                    },
                    "detector_reports": detector_records,
                    "pdf": {
                        "path": render_pdf.relative_to(workspace).as_posix(),
                        "sha256": _sha256(render_pdf),
                    },
                    "png": {
                        "path": render.relative_to(workspace).as_posix(),
                        "sha256": _sha256(render),
                    }
                },
                "human_review": "pending",
                "publication_acceptance": "not_claimed",
                "recovery_required": False,
            }
        ),
        encoding="utf-8",
    )
    return workspace, {
        "attempt": attempt,
        "binding": binding,
        "packet": packet,
        "receipt": receipt,
        "source": source,
        "render": render,
        "render_pdf": render_pdf,
        "strict_status": strict_status,
        "before_render": before_render,
        "before_pdf": before_pdf,
        "binding_critique": critique,
        "target_contract": target_contract,
        "crop_manifest": crop_manifest,
        "target_crop": target,
        "neighbor_crop": neighbor,
        "print_scale": print_scale,
    }


def _request(workspace: Path, paths: dict[str, Path]) -> dict[str, object]:
    return post_repair_visual_review.build_review_request(
        binding_path=paths["binding"],
        packet_path=paths["packet"],
        materialization_receipt_path=paths["receipt"],
        crop_manifest_path=paths["crop_manifest"],
        crop_roles={
            "target_crop": "target",
            "neighbor_crop": "neighbor",
            "print_scale": "print",
        },
        workspace_root=workspace,
    )


def _response(
    request: dict[str, object], workspace: Path
) -> dict[str, object]:
    transcript = workspace / "review" / "host-vision-transcript.json"
    transcript.parent.mkdir(parents=True, exist_ok=True)
    if not transcript.exists():
        transcript.write_text('{"review":"completed"}\n', encoding="utf-8")
    execution_receipt = {
        "schema": "figure-agent.host-review-execution-receipt.v1",
        "request_sha256": request["request_sha256"],
        "actor": {
            "kind": "model",
            "identity": "host-vision",
            "model_or_tool": "vision-runtime",
        },
        "transcript": {
            "path": transcript.relative_to(workspace).as_posix(),
            "sha256": _sha256(transcript),
        },
        "inspected_artifacts": [
            request["before_render"],
            *request["inspection_artifacts"],
        ],
    }
    execution_receipt["receipt_sha256"] = (
        post_repair_visual_review._canonical_hash(
            execution_receipt, omitted="receipt_sha256"
        )
    )
    return {
        "schema": "figure-agent.post-repair-visual-review-response.v1",
        "request_sha256": request["request_sha256"],
        "reviewer": "host-vision",
        "inspected_artifacts": request["inspection_artifacts"],
        "inspected_before_render": request["before_render"],
        "verdicts": {
            "target_resolved": "resolved",
            "no_new_local_defect": "pass",
            "unchanged_region_regression": "none",
        },
        "findings": [],
        "execution_receipt": execution_receipt,
        "publication_acceptance": "not_claimed",
    }


def test_builds_hash_bound_review_request(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)

    request = _request(workspace, paths)

    assert request["schema"] == "figure-agent.post-repair-visual-review-request.v1"
    assert request["repaired_source"]["sha256"] == _sha256(paths["source"])
    assert request["before_render"]["sha256"] == _sha256(paths["before_render"])
    assert request["render"]["sha256"] == _sha256(paths["render"])
    assert request["render_pdf"]["sha256"] == _sha256(paths["render_pdf"])
    assert {item["role"] for item in request["inspection_artifacts"]} == {
        "full_render",
        "target_crop",
        "neighbor_crop",
        "print_scale",
    }
    assert request["publication_acceptance"] == "not_claimed"


def test_visual_review_advances_only_after_resolved_no_regression(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)

    receipt = post_repair_visual_review.finalize_review_payload(
        request, _response(request, workspace), workspace_root=workspace
    )

    assert receipt["decision"] == "visually_rechecked_human_review_pending"
    assert receipt["publication_acceptance"] == "not_claimed"


@pytest.mark.parametrize(
    ("verdict_key", "verdict", "decision"),
    (
        ("target_resolved", "still_present", "repair_required"),
        ("no_new_local_defect", "fail", "repair_required"),
        ("unchanged_region_regression", "present", "repair_required"),
        ("target_resolved", "uncertain", "human_review_required"),
        ("no_new_local_defect", "uncertain", "human_review_required"),
        ("unchanged_region_regression", "uncertain", "human_review_required"),
    ),
)
def test_visual_review_fail_closed_decisions(
    tmp_path: Path,
    verdict_key: str,
    verdict: str,
    decision: str,
) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    response = _response(request, workspace)
    response["verdicts"][verdict_key] = verdict

    receipt = post_repair_visual_review.finalize_review_payload(
        request, response, workspace_root=workspace
    )

    assert receipt["decision"] == decision


def test_visual_review_rejects_stale_render(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    paths["render"].write_bytes(b"changed")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="artifact hash drift",
    ):
        post_repair_visual_review.finalize_review_payload(
            request, _response(request, workspace), workspace_root=workspace
        )


def test_visual_review_requires_every_inspection_role(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    response = _response(request, workspace)
    response["inspected_artifacts"] = response["inspected_artifacts"][:-1]

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="required inspection artifacts",
    ):
        post_repair_visual_review.finalize_review_payload(
            request, response, workspace_root=workspace
        )


def test_visual_review_rejects_symlinked_inspection_artifact(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    alias = paths["target_crop"].with_name("target-alias.png")
    alias.symlink_to(paths["target_crop"])
    manifest = json.loads(paths["crop_manifest"].read_text())
    target = next(item for item in manifest["crops"] if item["id"] == "target")
    target["path"] = alias.relative_to(workspace / "examples" / "demo").as_posix()
    paths["crop_manifest"].write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="must not traverse a symlink",
    ):
        _request(workspace, paths)


def test_visual_review_rejects_hash_valid_request_with_missing_role(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    request["inspection_artifacts"] = request["inspection_artifacts"][:-1]
    request["request_sha256"] = post_repair_visual_review._canonical_hash(
        request, omitted="request_sha256"
    )
    response = _response(request, workspace)

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="required inspection artifacts",
    ):
        post_repair_visual_review.finalize_review_payload(
            request, response, workspace_root=workspace
        )


def test_review_request_rejects_cross_fixture_lineage(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    receipt = json.loads(paths["receipt"].read_text())
    receipt["fixture"] = "other"
    paths["receipt"].write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="fixture lineage",
    ):
        _request(workspace, paths)


def test_review_request_rejects_target_contract_lineage_drift(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    packet = json.loads(paths["packet"].read_text())
    packet["target_contract"]["sha256"] = "sha256:wrong"
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(packet)
    paths["packet"].write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="target contract lineage",
    ):
        _request(workspace, paths)


def test_review_request_rejects_packet_receipt_output_drift(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    receipt = json.loads(paths["receipt"].read_text())
    receipt["output_path"] = paths["target_crop"].relative_to(workspace).as_posix()
    paths["receipt"].write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="machine verification receipt is not ready",
    ):
        _request(workspace, paths)


def test_review_request_rejects_incomplete_machine_verification_receipt(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    receipt = json.loads(paths["receipt"].read_text())
    del receipt["external_compile"]["pdf"]
    paths["receipt"].write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="compile evidence invalid",
    ):
        _request(workspace, paths)


def test_review_request_rejects_forged_strict_pass_receipt(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    strict_status = json.loads(paths["strict_status"].read_text())
    strict_status["detector_failed"] = True
    paths["strict_status"].write_text(json.dumps(strict_status), encoding="utf-8")
    receipt = json.loads(paths["receipt"].read_text())
    receipt["external_compile"]["strict_status"]["sha256"] = _sha256(
        paths["strict_status"]
    )
    paths["receipt"].write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="strict status invalid",
    ):
        _request(workspace, paths)


def test_review_request_rejects_missing_required_detector_receipt(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    receipt = json.loads(paths["receipt"].read_text())
    del receipt["external_compile"]["detector_reports"]["collisions"]
    paths["receipt"].write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="detector reports invalid",
    ):
        _request(workspace, paths)


def test_review_finalize_rejects_repair_packet_metadata_hash_drift(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    request["repair_packet"]["packet_sha256"] = "sha256:" + "f" * 64
    request["request_sha256"] = post_repair_visual_review._canonical_hash(
        request, omitted="request_sha256"
    )

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="review request lineage invalid",
    ):
        post_repair_visual_review.finalize_review_payload(
            request,
            _response(request, workspace),
            workspace_root=workspace,
        )


def test_review_request_rejects_stale_binding_internal_record(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    paths["binding_critique"].write_text("changed\n", encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="binding critique hash drift",
    ):
        _request(workspace, paths)


def test_review_request_rejects_incomplete_binding_repair_evidence(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    adjudication_path = workspace / "examples" / "demo" / "critique_adjudication.yaml"
    adjudication = adjudication_path.read_text(encoding="utf-8")
    adjudication = adjudication.split("  repair_evidence:\n", 1)[0]
    adjudication_path.write_text(adjudication, encoding="utf-8")
    binding = json.loads(paths["binding"].read_text(encoding="utf-8"))
    binding["adjudication"]["sha256"] = _sha256(adjudication_path)
    paths["binding"].write_text(json.dumps(binding), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="repair evidence lineage",
    ):
        _request(workspace, paths)


def test_review_request_rejects_stale_current_pdf(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    paths["before_pdf"].write_bytes(b"changed-pdf")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="current_pdf hash drift",
    ):
        _request(workspace, paths)


def test_review_finalize_rechecks_binding_internal_freshness(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    paths["binding_critique"].write_text("changed-after-request\n", encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="binding critique hash drift",
    ):
        post_repair_visual_review.finalize_review_payload(
            request, _response(request, workspace), workspace_root=workspace
        )


def test_review_request_rejects_unbound_crop_geometry(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    manifest = json.loads(paths["crop_manifest"].read_text())
    target = next(item for item in manifest["crops"] if item["id"] == "target")
    del target["bbox_px"]
    paths["crop_manifest"].write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="crop geometry",
    ):
        _request(workspace, paths)


def test_review_request_rejects_manifest_bound_to_other_render(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    other = workspace / "examples" / "demo" / "build" / "other.png"
    other.write_bytes(b"other")
    manifest = json.loads(paths["crop_manifest"].read_text())
    manifest["render_path"] = "build/other.png"
    paths["crop_manifest"].write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="not bound to verified render",
    ):
        _request(workspace, paths)


def test_visual_review_requires_three_explicit_verdicts(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    response = _response(request, workspace)
    del response["verdicts"]["no_new_local_defect"]

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="explicit verdicts",
    ):
        post_repair_visual_review.finalize_review_payload(
            request, response, workspace_root=workspace
        )


def test_visual_review_requires_before_render_inspection(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    response = _response(request, workspace)
    del response["inspected_before_render"]

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="before render was not inspected",
    ):
        post_repair_visual_review.finalize_review_payload(
            request, response, workspace_root=workspace
        )


def test_review_output_write_once_honors_transaction_lock(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    output = paths["attempt"] / "review_receipt.json"
    lock = output.parent / ".post-repair-review.lock"
    lock.write_text("other-owner\n", encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="transaction already active",
    ):
        post_repair_visual_review._write_once(
            output,
            post_repair_visual_review.finalize_review_payload(
                request, _response(request, workspace), workspace_root=workspace
            ),
        )


def test_review_request_accepts_unmodified_real_crop_producer_manifest(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    example = workspace / "examples" / "demo"
    Image.new("RGB", (800, 600), "white").save(paths["render"])
    receipt = json.loads(paths["receipt"].read_text())
    receipt["external_compile"]["png"]["sha256"] = _sha256(paths["render"])
    paths["receipt"].write_text(json.dumps(receipt), encoding="utf-8")
    critique_zoom_crops.build_zoom_crop_pack(
        example,
        paths["render"],
        panel_crop_paths=(),
    )
    manifest_path = example / "build" / "audit_crops" / "manifest.json"

    request = post_repair_visual_review.build_review_request(
        binding_path=paths["binding"],
        packet_path=paths["packet"],
        materialization_receipt_path=paths["receipt"],
        crop_manifest_path=manifest_path,
        crop_roles={
            "target_crop": "full_q1",
            "neighbor_crop": "full_q2",
            "print_scale": "print_thumbnail",
        },
        workspace_root=workspace,
    )

    assert [
        item["crop_id"]
        for item in request["inspection_artifacts"]
        if "crop_id" in item
    ] == [
        "full_q2",
        "print_thumbnail",
        "full_q1",
    ]


def test_visual_review_without_execution_receipt_requires_human_review(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    response = _response(request, workspace)
    del response["execution_receipt"]

    receipt = post_repair_visual_review.finalize_review_payload(
        request, response, workspace_root=workspace
    )

    assert receipt["decision"] == "human_review_required"


def test_visual_review_rejects_execution_receipt_for_other_request(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    response = _response(request, workspace)
    execution = response["execution_receipt"]
    execution["request_sha256"] = "sha256:" + "b" * 64
    execution["receipt_sha256"] = post_repair_visual_review._canonical_hash(
        execution, omitted="receipt_sha256"
    )

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="execution receipt invalid",
    ):
        post_repair_visual_review.finalize_review_payload(
            request, response, workspace_root=workspace
        )


def test_visual_review_rejects_transcript_artifact_drift(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    response = _response(request, workspace)
    transcript = workspace / response["execution_receipt"]["transcript"]["path"]
    transcript.write_text("changed\n", encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="transcript hash drift",
    ):
        post_repair_visual_review.finalize_review_payload(
            request, response, workspace_root=workspace
        )


def test_visual_review_rejects_missing_transcript_artifact(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    response = _response(request, workspace)
    transcript = workspace / response["execution_receipt"]["transcript"]["path"]
    transcript.unlink()

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="transcript must be a regular file",
    ):
        post_repair_visual_review.finalize_review_payload(
            request, response, workspace_root=workspace
        )


def test_visual_review_rejects_symlinked_transcript_artifact(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    response = _response(request, workspace)
    transcript = workspace / response["execution_receipt"]["transcript"]["path"]
    alias = transcript.with_name("transcript-alias.json")
    alias.symlink_to(transcript)
    execution = response["execution_receipt"]
    execution["transcript"] = {
        "path": alias.relative_to(workspace).as_posix(),
        "sha256": _sha256(transcript),
    }
    execution["receipt_sha256"] = post_repair_visual_review._canonical_hash(
        execution, omitted="receipt_sha256"
    )

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="transcript must not traverse a symlink",
    ):
        post_repair_visual_review.finalize_review_payload(
            request, response, workspace_root=workspace
        )


def test_review_publish_race_preserves_competing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    output = paths["attempt"] / "review_receipt.json"
    original = post_repair_visual_review.repair_transaction.atomic_create_json

    def race_write(path: Path, payload: dict[str, object]) -> None:
        path.write_text("competing-writer\n", encoding="utf-8")
        original(path, payload)

    monkeypatch.setattr(
        post_repair_visual_review.repair_transaction,
        "atomic_create_json",
        race_write,
    )

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="already exists",
    ):
        post_repair_visual_review._write_once(
            output,
            post_repair_visual_review.finalize_review_payload(
                request, _response(request, workspace), workspace_root=workspace
            ),
        )

    assert output.read_text(encoding="utf-8") == "competing-writer\n"
