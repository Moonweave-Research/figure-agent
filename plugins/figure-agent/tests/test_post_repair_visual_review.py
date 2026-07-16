from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from pathlib import Path

import authoring_repair_finalize
import authoring_repair_packet
import closed_loop_attempt_state
import closed_loop_development_verdict
import closed_loop_post_review_response
import critique_zoom_crops
import fig_run
import post_repair_visual_review
import pytest
import repair_transaction
import yaml
from inputs import parse_spec
from PIL import Image
from quality_manifest import (
    compute_critique_input_hash,
    critique_generator_version,
    expected_critique_rubric_version,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(
    tmp_path: Path, *, finding_bbox: tuple[int, int, int, int] | None = (10, 10, 50, 50)
) -> tuple[Path, dict[str, Path]]:
    workspace = tmp_path / "workspace"
    example = workspace / "examples" / "demo"
    attempt = example / "review" / "failure-first" / "execution-repair-v1"
    build = attempt / "build"
    crops = build / "audit_crops"
    crops.mkdir(parents=True)
    critique = example / "critique.md"
    adjudication = example / "critique_adjudication.yaml"
    reference = example / "reference" / "golden.png"
    reference.parent.mkdir(parents=True)
    reference.write_bytes(b"reference")
    spec = example / "spec.yaml"
    spec.write_text(
        "name: demo\n"
        "reference_image: reference/golden.png\n"
        "panels: []\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    parsed_spec = parse_spec(spec.read_text(encoding="utf-8"))
    critique_metadata = {
        "fixture": "demo",
        "critique_input_hash": compute_critique_input_hash(
            example,
            "demo",
            parsed_spec,
            style_lock_path=PLUGIN_ROOT / "styles" / "polymer-paper-preamble.sty",
            base_dir=PLUGIN_ROOT,
        ),
        "generator_version": critique_generator_version(
            PLUGIN_ROOT / "scripts" / "critique_brief.py"
        ),
        "rubric_version": expected_critique_rubric_version(example),
    }
    critique.write_text(
        "---\n"
        + yaml.safe_dump(critique_metadata, sort_keys=False)
        + "---\n",
        encoding="utf-8",
    )
    report = attempt / "collisions.json"
    report.write_text('{"schema":"figure-agent.text-collisions.v1"}\n', encoding="utf-8")
    registry = attempt / "source_selectors.json"
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
    baseline_source.write_text(
        "% repair:label:start\n"
        "\\node {repeated dispersive trapping};\n"
        "% repair:label:end\n"
        "\\node {S60 -> S80};\n",
        encoding="utf-8",
    )
    before_render = example / "build" / "demo.png"
    before_render.parent.mkdir()
    Image.new("RGB", (800, 600), "white").save(before_render)
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
                "collisions": [
                    {
                        "id": "TC001",
                        "texts": ["repeated", "trapping"],
                        **({"bbox_px": list(finding_bbox)} if finding_bbox else {}),
                        "source_mapping": None,
                    }
                ],
                "total": 1,
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
                "render_pdf": "build/demo.pdf",
                "required_crop_ids": [],
                "crops": [],
            }
        ),
        encoding="utf-8",
    )
    semantic_contract = attempt / "semantic_contract.yaml"
    semantic_contract.write_text(
        json.dumps(
            {
                "schema": "figure-agent.failure-first-semantic-contract.v1",
                "required_objects": ["panel_a.label", "panel_a.axis"],
                "protected_relations": ["label_remains_clear_of_axis"],
                "semantic_legibility": {
                    "object_roles": [
                        {
                            "object_id": "panel_a.label",
                            "declared_role": "annotation_label",
                            "forbidden_readings": [],
                        },
                        {
                            "object_id": "panel_a.axis",
                            "declared_role": "plot_axis",
                            "forbidden_readings": [],
                        },
                    ],
                    "visible_connectors": [],
                    "forbidden_connectors": [],
                    "label_ownership": [],
                },
                "publication_acceptance": "not_claimed",
            }
        ),
        encoding="utf-8",
    )
    semantic_contract_record = {
        "path": semantic_contract.relative_to(workspace).as_posix(),
        "sha256": _sha256(semantic_contract),
    }
    registry.write_text(
        json.dumps(
            {
                "schema": "figure-agent.source-selector-registry.v1",
                "source_path": baseline_source.relative_to(workspace).as_posix(),
                "source_sha256": _sha256(baseline_source),
                "semantic_contract": semantic_contract_record,
                "selectors": [
                    {
                        "selector_id": "panel-a-label",
                        "anchor_start": "% repair:label:start",
                        "anchor_end": "% repair:label:end",
                        "rendered_aliases": ["repeated", "trapping"],
                        "repair_role": "movable",
                        "repair_family": "label_reflow",
                        "protected_invariants": ["S60 -> S80"],
                        "semantic_object_refs": ["panel_a.axis", "panel_a.label"],
                        "semantic_relation_refs": ["label_remains_clear_of_axis"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    target_contract = attempt / "repair_targets.json"
    target_contract.write_text(
        json.dumps(
            {
                "schema": "figure-agent.repair-target-contract.v1",
                "source_path": baseline_source.relative_to(workspace).as_posix(),
                "source_sha256": _sha256(baseline_source),
                "targets": [
                    {
                        "finding": {
                            "report_path": report.relative_to(workspace).as_posix(),
                            "id": "TC001",
                        },
                        "attribution": {"state": "exact"},
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
    semantic_attribution = attempt / "semantic_attribution.json"
    semantic_attribution.write_text(
        json.dumps(
            {
                "schema": "figure-agent.semantic-finding-attribution.v1",
                "fixture": "demo",
                "machine_finding": {
                    "report_path": report.relative_to(workspace).as_posix(),
                    "report_sha256": _sha256(report),
                    "finding_id": "TC001",
                },
                "semantic_contract": semantic_contract_record,
                "source": {
                    "path": baseline_source.relative_to(workspace).as_posix(),
                    "sha256": _sha256(baseline_source),
                },
                "selector_id": "panel-a-label",
                "semantic_object_refs": ["panel_a.axis", "panel_a.label"],
                "semantic_relation_refs": ["label_remains_clear_of_axis"],
                "attribution_state": "exact",
                "publication_acceptance": "not_claimed",
            }
        ),
        encoding="utf-8",
    )
    binding = attempt / "critique_repair_binding.json"
    binding_payload = {
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
                "semantic_attribution": {
                    "path": semantic_attribution.relative_to(workspace).as_posix(),
                    "sha256": _sha256(semantic_attribution),
                },
                "publication_acceptance": "not_claimed",
    }
    binding.write_text(
        json.dumps(binding_payload),
        encoding="utf-8",
    )
    packet = attempt / "repair_packet.json"
    packet_payload = {
        "schema": authoring_repair_packet.SCHEMA,
        "fixture": "demo",
        "source": binding_payload["source"],
        "target_contract": binding_payload["target_contract"],
        "adjudicated_repair_binding": {
            "path": binding.relative_to(workspace).as_posix(),
            "sha256": _sha256(binding),
        },
        "authority_contract": {
            "schema": authoring_repair_packet.AUTHORITY_CONTRACT_SCHEMA,
            "mode": authoring_repair_packet.BOUND_AUTHORITY_MODE,
            "required_record": "adjudicated_repair_binding",
        },
        "editable_target": {
            "finding_id": "TC001",
            "report_path": report.relative_to(workspace).as_posix(),
        },
        "finding_reports": [
            {
                "path": report.relative_to(workspace).as_posix(),
                "sha256": _sha256(report),
            }
        ],
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


def _refresh_critique_authority(
    workspace: Path, paths: dict[str, Path]
) -> None:
    example = workspace / "examples" / "demo"
    spec_path = example / "spec.yaml"
    parsed_spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    critique = paths["binding_critique"]
    critique.write_text(
        "---\n"
        + yaml.safe_dump(
            {
                "fixture": "demo",
                "critique_input_hash": compute_critique_input_hash(
                    example,
                    "demo",
                    parsed_spec,
                    style_lock_path=(
                        PLUGIN_ROOT / "styles" / "polymer-paper-preamble.sty"
                    ),
                    base_dir=PLUGIN_ROOT,
                ),
                "generator_version": critique_generator_version(
                    PLUGIN_ROOT / "scripts" / "critique_brief.py"
                ),
                "rubric_version": expected_critique_rubric_version(example),
            },
            sort_keys=False,
        )
        + "---\n",
        encoding="utf-8",
    )
    adjudication_path = example / "critique_adjudication.yaml"
    adjudication = yaml.safe_load(adjudication_path.read_text(encoding="utf-8"))
    adjudication["source_critique_hash"] = _sha256(critique)
    adjudication_path.write_text(
        yaml.safe_dump(adjudication, sort_keys=False),
        encoding="utf-8",
    )
    binding = json.loads(paths["binding"].read_text(encoding="utf-8"))
    binding["critique"]["sha256"] = _sha256(critique)
    binding["adjudication"]["sha256"] = _sha256(adjudication_path)
    paths["binding"].write_text(json.dumps(binding), encoding="utf-8")
    packet = json.loads(paths["packet"].read_text(encoding="utf-8"))
    packet["adjudicated_repair_binding"]["sha256"] = _sha256(paths["binding"])
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(
        packet
    )
    paths["packet"].write_text(json.dumps(packet), encoding="utf-8")
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    receipt["packet_sha256"] = packet["packet_sha256"]
    paths["receipt"].write_text(json.dumps(receipt), encoding="utf-8")


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


def _machine_repaired_state(
    workspace: Path,
    paths: dict[str, Path],
    *,
    render_size: tuple[int, int] = (800, 600),
) -> tuple[dict[str, object], Path]:
    Image.new("RGB", render_size, "white").save(paths["render"])
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    receipt["external_compile"]["png"]["sha256"] = _sha256(paths["render"])
    paths["receipt"].write_text(json.dumps(receipt), encoding="utf-8")

    evidence_root = paths["attempt"] / "closed-loop-evidence"
    evidence_root.mkdir()

    def evidence_file(name: str) -> Path:
        path = evidence_root / f"{name}.json"
        path.write_text(json.dumps({"evidence": name}), encoding="utf-8")
        return path

    state = closed_loop_attempt_state.start_attempt(
        workspace_root=workspace,
        fixture="demo",
        actor="author",
        actor_role="authoring_agent",
        evidence={
            "attempt_manifest": evidence_file("attempt_manifest"),
            "authored_source": paths["source"],
            "render": paths["render"],
        },
    )
    state_path = closed_loop_attempt_state.publish_state(
        state, workspace_root=workspace
    )
    transitions = [
        (
            "critique_unadjudicated",
            "workflow_agent",
            {
                "critique": evidence_file("critique"),
                "host_review_execution_receipt": evidence_file(
                    "host_review_execution_receipt"
                ),
            },
        ),
        (
            "repair_bound",
            "human_adjudicator",
            {"adjudicated_repair_binding": paths["binding"]},
        ),
        (
            "repair_candidate_ready",
            "workflow_agent",
            {
                "repair_execution_packet": paths["packet"],
                "materialization_preview": evidence_file("materialization_preview"),
            },
        ),
        (
            "repair_authorized",
            "human_repair_authorizer",
            {"human_authorization": evidence_file("human_authorization")},
        ),
        (
            "machine_repaired",
            "workflow_agent",
            {
                "materialization_receipt": paths["receipt"],
                "machine_verification_receipt": paths["receipt"],
            },
        ),
    ]
    for next_state, actor_role, evidence in transitions:
        state = closed_loop_attempt_state.transition_state(
            state,
            next_state=next_state,
            actor="test",
            actor_role=actor_role,
            evidence=evidence,
            workspace_root=workspace,
            previous_state_path=state_path,
        )
        state_path = closed_loop_attempt_state.publish_state(
            state, workspace_root=workspace
        )
    return state, state_path


def test_fig_run_closed_loop_plan_only_validates_without_writes(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    state, state_path = _machine_repaired_state(workspace, paths)
    attempt_root = state_path.parent
    before = sorted(path.relative_to(workspace) for path in workspace.rglob("*"))

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=False,
        closed_loop_state=state_path,
        repo_root=workspace,
    )

    assert payload["final_stop_reason"] == "plan_only"
    assert payload["final_action"] == "post_repair_visual_review_request"
    assert payload["closed_loop"]["input_state_sha256"] == state["state_sha256"]
    assert payload["closed_loop"]["next_state"] == "post_review_requested"
    assert payload["boundary_handoff"]["required_actor"] == "workflow_agent"
    assert not (attempt_root / "post-repair-review").exists()
    assert sorted(path.relative_to(workspace) for path in workspace.rglob("*")) == before


def test_default_fig_run_plan_only_discovers_machine_repaired_without_writes(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    state, _ = _machine_repaired_state(workspace, paths)
    before = sorted(path.relative_to(workspace) for path in workspace.rglob("*"))

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=False,
        repo_root=workspace,
    )

    assert payload["final_stop_reason"] == "plan_only"
    assert payload["final_action"] == "post_repair_visual_review_request"
    assert payload["closed_loop"]["input_state_sha256"] == state["state_sha256"]
    assert payload["closed_loop"]["next_state"] == "post_review_requested"
    assert payload["boundary_handoff"]["required_actor"] == "workflow_agent"
    assert sorted(path.relative_to(workspace) for path in workspace.rglob("*")) == before


@pytest.mark.parametrize("execute", [False, True])
def test_default_fig_run_rejects_projected_state_hash_mismatch_without_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    execute: bool,
) -> None:
    workspace, paths = _fixture(tmp_path)
    state, state_path = _machine_repaired_state(workspace, paths)
    summary = fig_run._driver_summary(
        "demo",
        mode="review",
        goal="close loop",
        repo_root=workspace,
    )
    assert summary["closed_loop_attempt"]["state_sha256"] == state["state_sha256"]
    summary["closed_loop_attempt"]["state_sha256"] = "sha256:" + "0" * 64
    monkeypatch.setattr(fig_run, "_driver_summary", lambda *args, **kwargs: summary)
    before = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    with pytest.raises(ValueError, match="projected_state_hash_mismatch"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=execute,
            repo_root=workspace,
        )

    after = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert not (state_path.parent / "post-repair-review").exists()


def test_fig_run_closed_loop_follows_packet_path_from_published_state_lineage(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    renamed_packet = paths["packet"].with_name("bound-repair-packet.json")
    paths["packet"].rename(renamed_packet)
    paths["packet"] = renamed_packet
    _, state_path = _machine_repaired_state(workspace, paths)

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=False,
        closed_loop_state=state_path,
        repo_root=workspace,
    )

    assert payload["final_stop_reason"] == "plan_only"
    assert payload["closed_loop"]["next_state"] == "post_review_requested"


def test_fig_run_closed_loop_rejects_packet_binding_spliced_from_state_lineage(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    state_binding = paths["binding"].with_name("state-only-binding.json")
    state_binding.write_bytes(paths["binding"].read_bytes())
    paths["binding"] = state_binding
    _, state_path = _machine_repaired_state(workspace, paths)

    with pytest.raises(ValueError, match="state_binding_mismatch"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=False,
            closed_loop_state=state_path,
            repo_root=workspace,
        )


def test_fig_run_closed_loop_requires_bound_target_localization_before_output(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path, finding_bbox=None)
    _, state_path = _machine_repaired_state(workspace, paths)

    with pytest.raises(ValueError, match="target_finding_bbox_missing"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            repo_root=workspace,
        )

    assert not (state_path.parent / "post-repair-review").exists()


def test_fig_run_closed_loop_rejects_target_bbox_crossing_quadrant_boundary(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path, finding_bbox=(390, 10, 410, 50))
    _, state_path = _machine_repaired_state(workspace, paths)

    with pytest.raises(ValueError, match="target_finding_bbox_crosses_crop_boundary"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            repo_root=workspace,
        )

    assert not (state_path.parent / "post-repair-review").exists()


def test_fig_run_closed_loop_rejects_incompatible_before_after_render_dimensions(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path = _machine_repaired_state(
        workspace, paths, render_size=(900, 600)
    )

    with pytest.raises(ValueError, match="target_coordinate_space_incompatible"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            repo_root=workspace,
        )

    assert not (state_path.parent / "post-repair-review").exists()


def test_fig_run_closed_loop_detects_render_mutate_generate_restore_race(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path = _machine_repaired_state(workspace, paths)
    original_build_crops = critique_zoom_crops.build_zoom_crop_pack

    def mutate_generate_restore(
        *args: object, **kwargs: object
    ) -> list[dict[str, object]]:
        original_bytes = paths["render"].read_bytes()
        Image.new("RGB", (800, 600), "black").save(paths["render"])
        try:
            return original_build_crops(*args, **kwargs)
        finally:
            paths["render"].write_bytes(original_bytes)

    monkeypatch.setattr(
        critique_zoom_crops, "build_zoom_crop_pack", mutate_generate_restore
    )

    with pytest.raises(ValueError, match="render.*drift|render.*changed"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            repo_root=workspace,
        )

    assert not (state_path.parent / "post-repair-review").exists()
    assert not any(state_path.parent.glob("state-*-post_review_requested.json"))


def test_fig_run_closed_loop_resumes_hash_identical_request_after_state_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path = _machine_repaired_state(workspace, paths)
    original_publish = closed_loop_attempt_state.publish_state
    failed = False

    def fail_next_state_once(
        state: dict[str, object], *, workspace_root: Path
    ) -> Path:
        nonlocal failed
        if state.get("state") == "post_review_requested" and not failed:
            failed = True
            raise closed_loop_attempt_state.ClosedLoopAttemptStateError(
                "injected_state_failure"
            )
        return original_publish(state, workspace_root=workspace_root)

    monkeypatch.setattr(
        closed_loop_attempt_state, "publish_state", fail_next_state_once
    )
    with pytest.raises(ValueError, match="injected_state_failure"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            repo_root=workspace,
        )
    request_path = state_path.parent / "post-repair-review" / "request.json"
    request_bytes = request_path.read_bytes()

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=state_path,
        repo_root=workspace,
    )

    assert request_path.read_bytes() == request_bytes
    assert payload["final_stop_reason"] == "host_boundary"
    assert payload["final_action"] == "post_repair_visual_review_request"
    assert (workspace / payload["closed_loop"]["next_state_path"]).is_file()


@pytest.mark.parametrize("mutation", ["self_rehashed", "missing", "extra"])
def test_fig_run_closed_loop_recovery_rejects_crop_pack_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path = _machine_repaired_state(workspace, paths)
    original_write_once = post_repair_visual_review._write_once

    def fail_request_once(*args: object, **kwargs: object) -> None:
        raise post_repair_visual_review.PostRepairVisualReviewError(
            "injected_request_failure"
        )

    monkeypatch.setattr(post_repair_visual_review, "_write_once", fail_request_once)
    with pytest.raises(ValueError, match="injected_request_failure"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            repo_root=workspace,
        )
    monkeypatch.setattr(post_repair_visual_review, "_write_once", original_write_once)

    manifest_path = state_path.parent / "post-repair-review" / "crops" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    target_record = next(crop for crop in manifest["crops"] if crop["id"] == "full_q1")
    target_path = workspace / "examples" / "demo" / target_record["path"]
    if mutation == "self_rehashed":
        target_path.write_bytes(b"tampered-crop")
        target_record["sha256"] = _sha256(target_path)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    elif mutation == "missing":
        target_path.unlink()
    else:
        target_path.with_name("unexpected-crop.png").write_bytes(b"extra-crop")

    with pytest.raises(ValueError, match="crop_pack.*mismatch|crop.*tamper"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            repo_root=workspace,
        )

    assert not (state_path.parent / "post-repair-review" / "request.json").exists()
    assert not any(state_path.parent.glob("state-*-post_review_requested.json"))


def test_fig_run_closed_loop_execute_publishes_request_state_and_host_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, paths = _fixture(tmp_path)
    stale_detector = workspace / "examples" / "demo" / "build" / "visual_clash.json"
    stale_detector.parent.mkdir(exist_ok=True)
    stale_detector.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "id": "STALE001",
                        "kind": "text_on_path",
                        "text": "stale detector location",
                        "bbox_px": [10, 10, 200, 120],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    _refresh_critique_authority(workspace, paths)
    state, state_path = _machine_repaired_state(workspace, paths)

    def forbidden_host_or_shell(*args: object, **kwargs: object) -> object:
        raise AssertionError("closed-loop outbound handoff must not invoke shell or host")

    monkeypatch.setattr(fig_run, "_run_command", forbidden_host_or_shell)
    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=state_path,
        repo_root=workspace,
    )

    request_path = workspace / payload["closed_loop"]["request_path"]
    next_state_path = workspace / payload["closed_loop"]["next_state_path"]
    request = json.loads(request_path.read_text(encoding="utf-8"))
    next_state = json.loads(next_state_path.read_text(encoding="utf-8"))
    crop_manifest = json.loads(
        (workspace / request["crop_manifest"]["path"]).read_text(encoding="utf-8")
    )
    post_repair_visual_review._validate_request_freshness(
        request, workspace_root=workspace
    )
    assert payload["final_stop_reason"] == "host_boundary"
    assert payload["boundary_handoff"]["required_actor"] == "host_llm"
    assert payload["boundary_handoff"]["request_sha256"] == request["request_sha256"]
    assert payload["closed_loop"]["created"] is True
    assert request["crop_roles"] == {
        "neighbor_crop": "full_q2",
        "print_scale": "print_thumbnail",
        "target_crop": "full_q1",
    }
    assert request["publication_acceptance"] == "not_claimed"
    assert {crop["kind"] for crop in crop_manifest["crops"]} == {
        "zoom_crop",
        "print_scale",
    }
    assert all(not crop["id"].startswith("STALE001") for crop in crop_manifest["crops"])
    assert next_state["state"] == "post_review_requested"
    assert next_state["previous_state_sha256"] == state["state_sha256"]
    assert next_state["evidence"] == [
        {
            "role": "post_repair_visual_review_request",
            "path": request_path.relative_to(workspace).as_posix(),
            "sha256": _sha256(request_path),
        }
    ]
    assert next_state["required_actor"] == "host_llm"
    assert next_state["publication_acceptance"] == "not_claimed"

    before_rerun = sorted(path.relative_to(workspace) for path in workspace.rglob("*"))
    rerun = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=workspace,
    )
    assert rerun["executed_count"] == 0
    assert rerun["final_action"] == "closed_loop_handoff_stop"
    assert rerun["boundary_handoff"]["required_actor"] == "host_llm"
    assert sorted(path.relative_to(workspace) for path in workspace.rglob("*")) == before_rerun


def test_default_fig_run_execute_advances_only_to_host_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, paths = _fixture(tmp_path)
    _refresh_critique_authority(workspace, paths)
    state, _ = _machine_repaired_state(workspace, paths)

    def forbidden_host_or_shell(*args: object, **kwargs: object) -> object:
        raise AssertionError("default closed-loop dispatch must not invoke shell or host")

    monkeypatch.setattr(fig_run, "_run_command", forbidden_host_or_shell)
    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=workspace,
    )

    request_path = workspace / payload["closed_loop"]["request_path"]
    next_state_path = workspace / payload["closed_loop"]["next_state_path"]
    next_state = json.loads(next_state_path.read_text(encoding="utf-8"))
    assert payload["final_stop_reason"] == "host_boundary"
    assert payload["final_action"] == "post_repair_visual_review_request"
    assert payload["executed_count"] == 1
    assert payload["boundary_handoff"]["required_actor"] == "host_llm"
    assert payload["closed_loop"]["input_state_sha256"] == state["state_sha256"]
    assert request_path.is_file()
    assert next_state["state"] == "post_review_requested"
    assert next_state["required_actor"] == "host_llm"
    assert next_state["publication_acceptance"] == "not_claimed"


@pytest.mark.parametrize("stale_artifact", ["receipt", "render", "packet", "binding"])
def test_fig_run_closed_loop_rejects_stale_lineage_before_output(
    tmp_path: Path, stale_artifact: str
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path = _machine_repaired_state(workspace, paths)
    paths[stale_artifact].write_bytes(paths[stale_artifact].read_bytes() + b"\nstale")

    with pytest.raises(ValueError, match="stale|invalid"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            repo_root=workspace,
        )

    assert not (state_path.parent / "post-repair-review").exists()
    assert not any(state_path.parent.glob("state-*-post_review_requested.json"))


def test_fig_run_closed_loop_post_review_rerun_is_idempotent(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path = _machine_repaired_state(workspace, paths)
    first = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=state_path,
        repo_root=workspace,
    )
    next_state_path = workspace / first["closed_loop"]["next_state_path"]
    before = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    second = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=next_state_path,
        repo_root=workspace,
    )

    after = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert second["final_stop_reason"] == "host_boundary"
    assert second["executed_count"] == 0
    assert second["closed_loop"]["created"] is False
    assert second["closed_loop"]["request_path"] == first["closed_loop"]["request_path"]
    assert second["boundary_handoff"]["request_sha256"] == first[
        "boundary_handoff"
    ]["request_sha256"]
    assert after == before


def test_fig_run_closed_loop_rerun_rejects_hash_valid_crop_role_relabeling(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path = _machine_repaired_state(workspace, paths)
    first = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=state_path,
        repo_root=workspace,
    )
    request_path = workspace / first["closed_loop"]["request_path"]
    original_request = json.loads(request_path.read_text(encoding="utf-8"))
    forged_request = post_repair_visual_review.build_review_request(
        binding_path=paths["binding"],
        packet_path=paths["packet"],
        materialization_receipt_path=paths["receipt"],
        crop_manifest_path=workspace / original_request["crop_manifest"]["path"],
        crop_roles={
            "target_crop": "full_q2",
            "neighbor_crop": "full_q1",
            "print_scale": "print_thumbnail",
        },
        workspace_root=workspace,
    )
    request_path.write_text(json.dumps(forged_request), encoding="utf-8")
    next_state_path = workspace / first["closed_loop"]["next_state_path"]
    next_state = json.loads(next_state_path.read_text(encoding="utf-8"))
    next_state["evidence"][0]["sha256"] = _sha256(request_path)
    next_state["state_sha256"] = closed_loop_attempt_state.canonical_state_sha256(
        next_state
    )
    next_state_path.write_text(json.dumps(next_state), encoding="utf-8")

    with pytest.raises(ValueError, match="crop_role_mismatch"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=next_state_path,
            repo_root=workspace,
        )


def test_fig_run_closed_loop_cli_plan_only_never_records(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path = _machine_repaired_state(workspace, paths)
    runs_root = tmp_path / "runs"

    result = fig_run.main(
        [
            "demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--closed-loop-state",
            str(state_path),
            "--record",
            "--runs-root",
            str(runs_root),
            "--json",
        ],
        repo_root=workspace,
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["final_stop_reason"] == "plan_only"
    assert not runs_root.exists()


def _published_post_review_request(
    workspace: Path, paths: dict[str, Path]
) -> tuple[dict[str, object], Path, dict[str, object], Path]:
    _, machine_state_path = _machine_repaired_state(workspace, paths)
    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=machine_state_path,
        repo_root=workspace,
    )
    state_path = workspace / payload["closed_loop"]["next_state_path"]
    request_path = workspace / payload["closed_loop"]["request_path"]
    return (
        json.loads(state_path.read_text(encoding="utf-8")),
        state_path,
        json.loads(request_path.read_text(encoding="utf-8")),
        request_path,
    )


def _write_closed_loop_response(
    workspace: Path,
    state_path: Path,
    request: dict[str, object],
    *,
    verdict_key: str | None = None,
    verdict: str | None = None,
    include_execution_receipt: bool = True,
) -> Path:
    attempt_root = state_path.parent
    transcript = attempt_root / "post-repair-review" / "host-transcript.json"
    transcript.write_text('{"review":"completed"}\n', encoding="utf-8")
    response = _response(request, workspace)
    old_transcript = workspace / response["execution_receipt"]["transcript"]["path"]
    old_transcript.unlink()
    response["execution_receipt"]["transcript"] = {
        "path": transcript.relative_to(workspace).as_posix(),
        "sha256": _sha256(transcript),
    }
    response["execution_receipt"]["receipt_sha256"] = (
        post_repair_visual_review._canonical_hash(
            response["execution_receipt"], omitted="receipt_sha256"
        )
    )
    if verdict_key is not None:
        response["verdicts"][verdict_key] = verdict
    if not include_execution_receipt:
        del response["execution_receipt"]
    response_path = attempt_root / "post-repair-review" / "response.json"
    response_path.write_text(json.dumps(response), encoding="utf-8")
    return response_path


def _visually_re_reviewed_attempt(
    tmp_path: Path,
) -> tuple[Path, Path, Path]:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_response=response_path,
        repo_root=workspace,
    )
    reviewed_state_path = workspace / payload["closed_loop"]["next_state_path"]
    reviewed_state = json.loads(reviewed_state_path.read_text(encoding="utf-8"))
    verdict_path = reviewed_state_path.parent / "development-verdict.json"
    verdict_path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.closed-loop-development-verdict.v1",
                "fixture": "demo",
                "attempt_id": reviewed_state["attempt_id"],
                "reviewed_state_path": reviewed_state_path.relative_to(
                    workspace
                ).as_posix(),
                "decision_kind": "accept_development_baseline",
                "human_decision": (
                    "accept this exact visually re-reviewed artifact as a development baseline"
                ),
                "human_note": "Development baseline only; no release or publication claim.",
                "mutation_boundary": "development_baseline_state_mutation_allowed",
                "reviewer": "named-human-reviewer",
                "reviewed_state_sha256": reviewed_state["state_sha256"],
                "publication_acceptance": "not_claimed",
            }
        ),
        encoding="utf-8",
    )
    return workspace, reviewed_state_path, verdict_path


def test_fig_run_development_verdict_plan_only_is_bound_and_write_free(
    tmp_path: Path,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    before = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="record the named development verdict",
        execute=False,
        closed_loop_state=state_path,
        closed_loop_development_verdict=verdict_path,
        repo_root=workspace,
    )

    after = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert payload["final_stop_reason"] == "plan_only"
    assert payload["closed_loop"]["input_state"] == "visually_re_reviewed"
    assert payload["closed_loop"]["next_state"] == "development_accepted"
    assert payload["closed_loop"]["created"] is False
    assert payload["boundary_handoff"]["required_actor"] == "workflow_agent"
    assert payload["boundary_handoff"]["publication_acceptance"] == "not_claimed"
    assert after == before


def test_fig_run_development_verdict_publishes_named_terminal_state(
    tmp_path: Path,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="record the named development verdict",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_development_verdict=verdict_path,
        repo_root=workspace,
    )

    next_state_path = workspace / payload["closed_loop"]["next_state_path"]
    next_state = json.loads(next_state_path.read_text(encoding="utf-8"))
    assert payload["final_stop_reason"] == "development_accepted"
    assert payload["executed_count"] == 1
    assert next_state["state"] == "development_accepted"
    assert next_state["actor"] == "named-human-reviewer"
    assert next_state["actor_role"] == "human_reviewer"
    assert next_state["required_actor"] == "none"
    assert next_state["terminal"] is True
    assert next_state["publication_acceptance"] == "not_claimed"
    assert next_state["evidence"] == [
        {
            "role": "human_decision_record",
            "path": verdict_path.relative_to(workspace).as_posix(),
            "sha256": _sha256(verdict_path),
        }
    ]


def test_fig_run_development_verdict_recovers_exact_published_state(
    tmp_path: Path,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    created = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="record the named development verdict",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_development_verdict=verdict_path,
        repo_root=workspace,
    )

    recovered = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="record the named development verdict",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_development_verdict=verdict_path,
        repo_root=workspace,
    )

    assert recovered["final_stop_reason"] == "development_accepted_recovered"
    assert recovered["executed_count"] == 0
    assert recovered["closed_loop"]["created"] is False
    assert recovered["closed_loop"]["next_state_path"] == (
        created["closed_loop"]["next_state_path"]
    )
    assert recovered["boundary_handoff"]["evidence_refs"][-1] == (
        "closed_loop_state:" + created["closed_loop"]["next_state_path"]
    )
    assert len(list(state_path.parent.glob("state-*-development_accepted.json"))) == 1


def test_fig_run_development_verdict_recovers_publish_between_match_and_current_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    original_matching = (
        closed_loop_development_verdict._matching_published_acceptance
    )
    injected = False

    def publish_after_first_match(
        fixture: str,
        plan: dict[str, object],
        *,
        workspace_root: Path,
    ) -> dict[str, object] | None:
        nonlocal injected
        published = original_matching(
            fixture,
            plan,
            workspace_root=workspace_root,
        )
        if published is None and not injected:
            injected = True
            expected = closed_loop_development_verdict._expected_accepted_state(
                plan,
                workspace_root=workspace_root,
            )
            closed_loop_attempt_state.publish_state(
                expected,
                workspace_root=workspace_root,
            )
        return published

    monkeypatch.setattr(
        closed_loop_development_verdict,
        "_matching_published_acceptance",
        publish_after_first_match,
    )

    recovered = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="record the named development verdict",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_development_verdict=verdict_path,
        repo_root=workspace,
    )

    assert recovered["final_stop_reason"] == "development_accepted_recovered"
    assert recovered["executed_count"] == 0
    assert recovered["closed_loop"]["created"] is False
    assert len(list(state_path.parent.glob("state-*-development_accepted.json"))) == 1


def test_shared_attempt_transition_lock_blocks_development_acceptance(
    tmp_path: Path,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    lock_path = (
        state_path.parent / closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK
    )

    with repair_transaction.recoverable_exclusive_lock(
        lock_path,
        owner=closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK_OWNER,
    ):
        with pytest.raises(ValueError, match="transaction lock exists"):
            fig_run.run_workflow(
                "demo",
                mode="review",
                goal="record the named development verdict",
                execute=True,
                closed_loop_state=state_path,
                closed_loop_development_verdict=verdict_path,
                repo_root=workspace,
            )

    assert not any(state_path.parent.glob("state-*-development_accepted.json"))


def test_legacy_post_review_response_lock_blocks_development_acceptance(
    tmp_path: Path,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    legacy_lock_path = state_path.parent / ".closed-loop-post-review-response.lock"

    with repair_transaction.exclusive_lock(
        legacy_lock_path,
        owner="closed_loop_post_review_response",
    ):
        with pytest.raises(ValueError, match="transaction lock exists"):
            fig_run.run_workflow(
                "demo",
                mode="review",
                goal="record the named development verdict",
                execute=True,
                closed_loop_state=state_path,
                closed_loop_development_verdict=verdict_path,
                repo_root=workspace,
            )

    assert not any(state_path.parent.glob("state-*-development_accepted.json"))


def test_fig_run_development_verdict_rejects_contradictory_human_text(
    tmp_path: Path,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    verdict["human_decision"] = "reject this development baseline"
    verdict_path.write_text(json.dumps(verdict), encoding="utf-8")

    with pytest.raises(ValueError, match="development_verdict_not_approved"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="record the named development verdict",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_development_verdict=verdict_path,
            repo_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-development_accepted.json"))


def test_fig_run_development_verdict_rejects_state_hash_mismatch(
    tmp_path: Path,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    verdict["reviewed_state_sha256"] = "sha256:" + "0" * 64
    verdict_path.write_text(json.dumps(verdict), encoding="utf-8")

    with pytest.raises(ValueError, match="development_verdict_state_hash_mismatch"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="record the named development verdict",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_development_verdict=verdict_path,
            repo_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-development_accepted.json"))


def test_fig_run_development_verdict_rejects_publication_claim(
    tmp_path: Path,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    verdict["publication_acceptance"] = "accepted"
    verdict_path.write_text(json.dumps(verdict), encoding="utf-8")

    with pytest.raises(ValueError, match="development_verdict_publication_claimed"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="record the named development verdict",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_development_verdict=verdict_path,
            repo_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-development_accepted.json"))


def test_fig_run_development_verdict_requires_exact_state_mutation_boundary(
    tmp_path: Path,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    verdict["mutation_boundary"] = "no_source_mutation"
    verdict_path.write_text(json.dumps(verdict), encoding="utf-8")

    with pytest.raises(ValueError, match="development_verdict_mutation_boundary_invalid"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="record the named development verdict",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_development_verdict=verdict_path,
            repo_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-development_accepted.json"))


def test_fig_run_development_verdict_rejects_input_replacement_under_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    original_lock = repair_transaction.recoverable_exclusive_lock

    @contextmanager
    def replace_after_lock(path: Path, *, owner: str):
        if path.name != closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK:
            with original_lock(path, owner=owner):
                yield
            return
        assert owner == closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK_OWNER
        with original_lock(path, owner=owner):
            verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
            verdict["human_note"] = "A different, still valid decision record."
            verdict_path.write_text(json.dumps(verdict), encoding="utf-8")
            yield

    monkeypatch.setattr(
        closed_loop_development_verdict.repair_transaction,
        "recoverable_exclusive_lock",
        replace_after_lock,
    )

    with pytest.raises(ValueError, match="development_verdict_inputs_drifted"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="record the named development verdict",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_development_verdict=verdict_path,
            repo_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-development_accepted.json"))


def test_fig_run_development_verdict_rejects_evidence_drift_before_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    original_transition = closed_loop_attempt_state.transition_state

    def drift_after_transition(*args: object, **kwargs: object) -> dict[str, object]:
        next_state = original_transition(*args, **kwargs)
        verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
        verdict["human_note"] = "Changed after transition construction."
        verdict_path.write_text(json.dumps(verdict), encoding="utf-8")
        return next_state

    monkeypatch.setattr(
        closed_loop_development_verdict.closed_loop_attempt_state,
        "transition_state",
        drift_after_transition,
    )

    with pytest.raises(ValueError, match="evidence_hash_stale"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="record the named development verdict",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_development_verdict=verdict_path,
            repo_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-development_accepted.json"))


def test_default_fig_run_never_discovers_adjacent_development_verdict(
    tmp_path: Path,
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    assert verdict_path.is_file()

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="continue the lifecycle",
        execute=True,
        repo_root=workspace,
    )

    assert payload["executed_count"] == 0
    assert payload["final_action"] == fig_run.fig_driver.ACTION_CLOSED_LOOP_HANDOFF_STOP
    assert payload["boundary_handoff"]["required_actor"] == "human_reviewer"
    assert payload["boundary_handoff"]["evidence_refs"][0] == (
        state_path.relative_to(workspace).as_posix()
    )
    assert not any(state_path.parent.glob("state-*-development_accepted.json"))


def test_default_fig_run_development_verdict_cli_binds_current_without_journal(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace, state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)
    current = json.loads(state_path.read_text(encoding="utf-8"))
    runs_root = tmp_path / "runs"

    result = fig_run.main(
        [
            "demo",
            "--mode",
            "review",
            "--goal",
            "record the named development verdict",
            "--closed-loop-development-verdict",
            str(verdict_path),
            "--record",
            "--runs-root",
            str(runs_root),
            "--json",
        ],
        repo_root=workspace,
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["closed_loop"]["input_state_sha256"] == current["state_sha256"]
    assert payload["closed_loop"]["next_state"] == "development_accepted"
    assert payload["closed_loop"]["created"] is False
    assert not runs_root.exists()


def test_default_fig_run_development_verdict_closes_current_attempt_without_host(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, _state_path, verdict_path = _visually_re_reviewed_attempt(tmp_path)

    def forbidden_host_or_shell(*args: object, **kwargs: object) -> object:
        raise AssertionError("verdict consumption must not invoke shell or host")

    monkeypatch.setattr(fig_run, "_run_command", forbidden_host_or_shell)
    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="record the named development verdict",
        execute=True,
        closed_loop_development_verdict=verdict_path,
        repo_root=workspace,
    )

    accepted_path = workspace / payload["closed_loop"]["next_state_path"]
    accepted = json.loads(accepted_path.read_text(encoding="utf-8"))
    completed = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="continue the lifecycle",
        execute=True,
        repo_root=workspace,
    )
    assert payload["final_stop_reason"] == "development_accepted"
    assert accepted["state"] == "development_accepted"
    assert accepted["publication_acceptance"] == "not_claimed"
    assert completed["final_stop_reason"] == "complete"
    assert completed["executed_count"] == 0


def test_fig_run_closed_loop_inbound_plan_only_is_truthful_and_write_free(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    before = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=False,
        closed_loop_state=state_path,
        closed_loop_response=response_path,
        repo_root=workspace,
    )

    after = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert payload["final_stop_reason"] == "plan_only"
    assert payload["closed_loop"]["decision"] == (
        "visually_rechecked_human_review_pending"
    )
    assert payload["closed_loop"]["next_state"] == "visually_re_reviewed"
    assert payload["closed_loop"]["publication_acceptance"] == "not_claimed"
    assert after == before


def test_default_fig_run_response_only_plan_binds_current_state_without_writes(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    state, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    before = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=False,
        closed_loop_response=response_path,
        repo_root=workspace,
    )

    after = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert payload["final_stop_reason"] == "plan_only"
    assert payload["closed_loop"]["input_state_sha256"] == state["state_sha256"]
    assert payload["closed_loop"]["next_state"] == "visually_re_reviewed"
    assert payload["boundary_handoff"]["required_actor"] == "human_reviewer"
    assert after == before


def test_default_fig_run_response_only_cli_plan_writes_no_journal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace, paths = _fixture(tmp_path)
    state, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    runs_root = tmp_path / "runs"

    result = fig_run.main(
        [
            "demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--closed-loop-response",
            str(response_path),
            "--record",
            "--runs-root",
            str(runs_root),
            "--json",
        ],
        repo_root=workspace,
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["final_stop_reason"] == "plan_only"
    assert payload["closed_loop"]["input_state_sha256"] == state["state_sha256"]
    assert not runs_root.exists()


def test_default_fig_run_response_only_execute_advances_without_host_or_shell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, paths = _fixture(tmp_path)
    state, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)

    def forbidden_host_or_shell(*args: object, **kwargs: object) -> object:
        raise AssertionError("response consumption must not invoke shell or host")

    monkeypatch.setattr(fig_run, "_run_command", forbidden_host_or_shell)
    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_response=response_path,
        repo_root=workspace,
    )

    next_state = json.loads(
        (workspace / payload["closed_loop"]["next_state_path"]).read_text()
    )
    assert payload["final_stop_reason"] == "human_review_boundary"
    assert payload["closed_loop"]["input_state_sha256"] == state["state_sha256"]
    assert next_state["state"] == "visually_re_reviewed"
    assert next_state["required_actor"] == "human_reviewer"
    assert next_state["publication_acceptance"] == "not_claimed"


def test_default_fig_run_response_only_rejects_state_that_stops_being_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, paths = _fixture(tmp_path)
    state, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    competing_state = closed_loop_attempt_state.transition_state(
        state,
        next_state="repair_required",
        actor="competing-host",
        actor_role="host_llm",
        evidence={"repair_failure_record": response_path},
        workspace_root=workspace,
        previous_state_path=state_path,
    )
    competing_state_path = closed_loop_attempt_state.state_path(
        competing_state,
        workspace_root=workspace,
    )
    original_lock = repair_transaction.recoverable_exclusive_lock

    @contextmanager
    def advance_before_lock(path: Path, *, owner: str):
        if path.name != closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK:
            with original_lock(path, owner=owner):
                yield
            return
        assert owner == closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK_OWNER
        closed_loop_attempt_state.publish_state(
            competing_state,
            workspace_root=workspace,
        )
        yield

    monkeypatch.setattr(
        closed_loop_post_review_response.repair_transaction,
        "recoverable_exclusive_lock",
        advance_before_lock,
    )

    with pytest.raises(ValueError, match="canonical_current_state_drift"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_response=response_path,
            repo_root=workspace,
        )

    receipt_path = state_path.parent / "post-repair-review" / "review-receipt.json"
    visually_reviewed_path = state_path.parent / "state-002-visually_re_reviewed.json"
    assert competing_state_path.is_file()
    assert not receipt_path.exists()
    assert not visually_reviewed_path.exists()


@pytest.mark.parametrize("execute", [False, True])
def test_default_fig_run_response_only_rejects_projected_hash_mismatch_without_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    execute: bool,
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    summary = fig_run._driver_summary(
        "demo",
        mode="review",
        goal="close loop",
        repo_root=workspace,
    )
    assert summary["closed_loop_attempt"]["state"] == "post_review_requested"
    summary["closed_loop_attempt"]["state_sha256"] = "sha256:" + "0" * 64
    monkeypatch.setattr(fig_run, "_driver_summary", lambda *args, **kwargs: summary)
    before = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    with pytest.raises(ValueError, match="projected_state_hash_mismatch"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=execute,
            closed_loop_response=response_path,
            repo_root=workspace,
        )

    after = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert not (state_path.parent / "post-repair-review" / "review-receipt.json").exists()


def test_fig_run_closed_loop_inbound_clean_publishes_human_review_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, paths = _fixture(tmp_path)
    state, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)

    def forbidden_host_or_shell(*args: object, **kwargs: object) -> object:
        raise AssertionError("closed-loop inbound must not invoke shell or host")

    monkeypatch.setattr(fig_run, "_run_command", forbidden_host_or_shell)
    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_response=response_path,
        repo_root=workspace,
    )

    next_state_path = workspace / payload["closed_loop"]["next_state_path"]
    receipt_path = workspace / payload["closed_loop"]["receipt_path"]
    next_state = json.loads(next_state_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["final_stop_boundary"] == "human_reviewer"
    assert payload["closed_loop"]["created"] is True
    assert next_state["state"] == "visually_re_reviewed"
    assert next_state["previous_state_sha256"] == state["state_sha256"]
    assert next_state["actor"] == "model:host-vision:vision-runtime"
    assert next_state["actor_role"] == "host_llm"
    assert [record["role"] for record in next_state["evidence"]] == [
        "host_review_execution_receipt",
        "post_repair_visual_review_receipt",
        "post_repair_visual_review_response",
    ]
    assert next_state["evidence"][0]["path"] == response_path.relative_to(
        workspace
    ).as_posix()
    assert receipt["decision"] == "visually_rechecked_human_review_pending"
    assert receipt["response"] == {
        "path": response_path.relative_to(workspace).as_posix(),
        "sha256": _sha256(response_path),
    }
    assert receipt["publication_acceptance"] == "not_claimed"


def test_fig_run_closed_loop_inbound_rerun_from_request_state_is_no_write(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    first = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_response=response_path,
        repo_root=workspace,
    )
    before = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    second = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_response=response_path,
        repo_root=workspace,
    )

    after = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert second["closed_loop"]["created"] is False
    assert second["closed_loop"]["next_state_path"] == first["closed_loop"][
        "next_state_path"
    ]
    assert after == before


@pytest.mark.parametrize(
    ("verdict_key", "verdict"),
    (
        ("target_resolved", "still_present"),
        ("no_new_local_defect", "fail"),
        ("unchanged_region_regression", "present"),
    ),
)
def test_fig_run_closed_loop_inbound_defect_publishes_repair_required(
    tmp_path: Path, verdict_key: str, verdict: str
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(
        workspace,
        state_path,
        request,
        verdict_key=verdict_key,
        verdict=verdict,
    )

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_response=response_path,
        repo_root=workspace,
    )

    next_state = json.loads(
        (workspace / payload["closed_loop"]["next_state_path"]).read_text()
    )
    assert payload["final_stop_reason"] == "repair_required"
    assert payload["boundary_handoff"]["closeout_checks"] == [
        "start a new attempt from the bound repair failure record"
    ]
    assert next_state["state"] == "repair_required"
    assert next_state["terminal"] is True
    assert [record["role"] for record in next_state["evidence"]] == [
        "repair_failure_record"
    ]


@pytest.mark.parametrize(
    ("verdict_key", "include_execution_receipt"),
    (("target_resolved", True), (None, False)),
)
def test_fig_run_closed_loop_inbound_human_boundary_publishes_nothing(
    tmp_path: Path,
    verdict_key: str | None,
    include_execution_receipt: bool,
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(
        workspace,
        state_path,
        request,
        verdict_key=verdict_key,
        verdict="uncertain" if verdict_key else None,
        include_execution_receipt=include_execution_receipt,
    )

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_response=response_path,
        repo_root=workspace,
    )

    assert payload["final_stop_reason"] == "human_review_boundary"
    assert payload["closed_loop"]["next_state"] == "post_review_requested"
    assert payload["closed_loop"]["created"] is False
    assert not (state_path.parent / "post-repair-review" / "review-receipt.json").exists()
    assert not any(state_path.parent.glob("state-*-visually_re_reviewed.json"))
    assert not any(state_path.parent.glob("state-*-repair_required.json"))


def test_fig_run_closed_loop_inbound_human_boundary_cli_writes_no_journal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(
        workspace,
        state_path,
        request,
        include_execution_receipt=False,
    )
    runs_root = tmp_path / "runs"

    result = fig_run.main(
        [
            "demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--execute",
            "--closed-loop-state",
            str(state_path),
            "--closed-loop-response",
            str(response_path),
            "--runs-root",
            str(runs_root),
            "--json",
        ],
        repo_root=workspace,
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["final_stop_reason"] == "human_review_boundary"
    assert payload["closed_loop"]["created"] is False
    assert not runs_root.exists()


def test_fig_run_closed_loop_inbound_rejects_response_attempt_splice(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    spliced = workspace / "examples" / "demo" / "review" / "response.json"
    spliced.write_bytes(response_path.read_bytes())

    with pytest.raises(ValueError, match="response_attempt_mismatch"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_response=spliced,
            repo_root=workspace,
        )


def test_fig_run_closed_loop_response_requires_current_request_state_or_explicit_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace, paths = _fixture(tmp_path)
    _machine_repaired_state(workspace, paths)
    result = fig_run.main(
        [
            "demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--closed-loop-response",
            "response.json",
            "--json",
        ],
        repo_root=workspace,
    )

    assert result == 2
    assert (
        "closed-loop-response requires current post_review_requested state "
        "or --closed-loop-state"
    ) in capsys.readouterr().err


def test_fig_run_closed_loop_inbound_recovers_identical_receipt_after_state_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    original_publish = closed_loop_attempt_state.publish_state
    failed = False

    def fail_visual_state_once(
        state: dict[str, object], *, workspace_root: Path
    ) -> Path:
        nonlocal failed
        if state.get("state") == "visually_re_reviewed" and not failed:
            failed = True
            raise closed_loop_attempt_state.ClosedLoopAttemptStateError(
                "simulated_state_failure"
            )
        return original_publish(state, workspace_root=workspace_root)

    monkeypatch.setattr(
        closed_loop_attempt_state, "publish_state", fail_visual_state_once
    )
    with pytest.raises(ValueError, match="simulated_state_failure"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_response=response_path,
            repo_root=workspace,
        )
    receipt_path = state_path.parent / "post-repair-review" / "review-receipt.json"
    assert receipt_path.is_file()

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="close loop",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_response=response_path,
        repo_root=workspace,
    )

    assert payload["closed_loop"]["next_state"] == "visually_re_reviewed"
    assert (workspace / payload["closed_loop"]["next_state_path"]).is_file()


def test_fig_run_closed_loop_inbound_partial_recovery_rejects_response_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    original_publish = closed_loop_attempt_state.publish_state

    def fail_visual_state(
        state: dict[str, object], *, workspace_root: Path
    ) -> Path:
        if state.get("state") == "visually_re_reviewed":
            raise closed_loop_attempt_state.ClosedLoopAttemptStateError(
                "simulated_state_failure"
            )
        return original_publish(state, workspace_root=workspace_root)

    monkeypatch.setattr(closed_loop_attempt_state, "publish_state", fail_visual_state)
    with pytest.raises(ValueError, match="simulated_state_failure"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_response=response_path,
            repo_root=workspace,
        )
    monkeypatch.setattr(closed_loop_attempt_state, "publish_state", original_publish)
    response = json.loads(response_path.read_text(encoding="utf-8"))
    response["reviewer"] = "different-host"
    response_path.write_text(json.dumps(response), encoding="utf-8")

    with pytest.raises(ValueError, match="review_receipt_mismatch"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_response=response_path,
            repo_root=workspace,
        )


def test_fig_run_closed_loop_inbound_revalidates_transcript_after_receipt_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    response = json.loads(response_path.read_text(encoding="utf-8"))
    transcript = workspace / response["execution_receipt"]["transcript"]["path"]
    inbound_module = fig_run.closed_loop_post_review_response
    original_publish = inbound_module._existing_or_publish_receipt

    def publish_then_mutate(path: Path, expected: dict[str, object]) -> bool:
        created = original_publish(path, expected)
        transcript.write_text("changed-after-receipt\n", encoding="utf-8")
        return created

    monkeypatch.setattr(
        inbound_module, "_existing_or_publish_receipt", publish_then_mutate
    )

    with pytest.raises(ValueError, match="transcript hash drift"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_response=response_path,
            repo_root=workspace,
        )

    assert (state_path.parent / "post-repair-review" / "review-receipt.json").is_file()
    assert not any(state_path.parent.glob("state-*-visually_re_reviewed.json"))


def test_fig_run_closed_loop_inbound_rejects_request_drift_before_output(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, request_path = _published_post_review_request(
        workspace, paths
    )
    response_path = _write_closed_loop_response(workspace, state_path, request)
    request_path.write_bytes(request_path.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="evidence_hash_stale"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_response=response_path,
            repo_root=workspace,
        )
    assert not (state_path.parent / "post-repair-review" / "review-receipt.json").exists()


def test_fig_run_closed_loop_inbound_rejects_transcript_attempt_splice(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    _, state_path, request, _ = _published_post_review_request(workspace, paths)
    response_path = _write_closed_loop_response(workspace, state_path, request)
    response = json.loads(response_path.read_text(encoding="utf-8"))
    transcript = workspace / "examples" / "demo" / "review" / "spliced.json"
    transcript.write_text('{"review":"completed"}\n', encoding="utf-8")
    execution = response["execution_receipt"]
    execution["transcript"] = {
        "path": transcript.relative_to(workspace).as_posix(),
        "sha256": _sha256(transcript),
    }
    execution["receipt_sha256"] = post_repair_visual_review._canonical_hash(
        execution, omitted="receipt_sha256"
    )
    response_path.write_text(json.dumps(response), encoding="utf-8")

    with pytest.raises(ValueError, match="host_review_transcript_attempt_mismatch"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="close loop",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_response=response_path,
            repo_root=workspace,
        )


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


def test_review_request_rejects_unbound_current_v4_packet(tmp_path: Path) -> None:
    workspace, paths = _fixture(tmp_path)
    packet = json.loads(paths["packet"].read_text(encoding="utf-8"))
    packet.pop("adjudicated_repair_binding")
    packet["authority_contract"] = {
        "schema": authoring_repair_packet.AUTHORITY_CONTRACT_SCHEMA,
        "mode": authoring_repair_packet.LEGACY_AUTHORITY_MODE,
        "required_record": None,
    }
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(
        packet
    )
    paths["packet"].write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="requires adjudicated binding authority",
    ):
        _request(workspace, paths)


def test_review_request_rejects_bound_v4_packet_with_binding_hash_drift(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    packet = json.loads(paths["packet"].read_text(encoding="utf-8"))
    packet["adjudicated_repair_binding"]["sha256"] = "sha256:" + "f" * 64
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(
        packet
    )
    paths["packet"].write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="adjudicated binding hash drift",
    ):
        _request(workspace, paths)


def test_review_request_rejects_rehashed_noncanonical_binding_substitution(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    alternate_binding = paths["binding"].with_name("alternate_binding.json")
    alternate_binding.write_bytes(paths["binding"].read_bytes())
    packet = json.loads(paths["packet"].read_text(encoding="utf-8"))
    packet["adjudicated_repair_binding"] = {
        "path": alternate_binding.relative_to(workspace).as_posix(),
        "sha256": _sha256(alternate_binding),
    }
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(
        packet
    )
    paths["packet"].write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="adjudicated binding must be canonical and target-adjacent",
    ):
        _request(workspace, paths)


def test_review_finalize_rejects_fully_rehashed_binding_substitution(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    request = _request(workspace, paths)
    alternate_binding = paths["binding"].with_name("alternate_binding.json")
    alternate_binding.write_bytes(paths["binding"].read_bytes())
    packet = json.loads(paths["packet"].read_text(encoding="utf-8"))
    packet["adjudicated_repair_binding"] = {
        "path": alternate_binding.relative_to(workspace).as_posix(),
        "sha256": _sha256(alternate_binding),
    }
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(
        packet
    )
    paths["packet"].write_text(json.dumps(packet), encoding="utf-8")
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    receipt["packet_sha256"] = packet["packet_sha256"]
    paths["receipt"].write_text(json.dumps(receipt), encoding="utf-8")
    request["binding"] = {
        "path": alternate_binding.relative_to(workspace).as_posix(),
        "sha256": _sha256(alternate_binding),
    }
    request["repair_packet"] = {
        "path": paths["packet"].relative_to(workspace).as_posix(),
        "sha256": _sha256(paths["packet"]),
        "packet_sha256": packet["packet_sha256"],
    }
    request["materialization_receipt"]["sha256"] = _sha256(paths["receipt"])
    request["request_sha256"] = post_repair_visual_review._canonical_hash(
        request,
        omitted="request_sha256",
    )

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="adjudicated binding must be canonical and target-adjacent",
    ):
        post_repair_visual_review.finalize_review_payload(
            request,
            _response(request, workspace),
            workspace_root=workspace,
        )


def test_review_request_rejects_stored_v3_without_explicit_legacy_boundary(
    tmp_path: Path,
) -> None:
    workspace, paths = _fixture(tmp_path)
    packet = json.loads(paths["packet"].read_text(encoding="utf-8"))
    packet["schema"] = authoring_repair_packet.LEGACY_SCHEMA
    packet.pop("authority_contract")
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(
        packet
    )
    paths["packet"].write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(
        post_repair_visual_review.PostRepairVisualReviewError,
        match="repair packet is invalid",
    ):
        _request(workspace, paths)


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
        match="authority substitution",
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
    _refresh_critique_authority(workspace, paths)
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
