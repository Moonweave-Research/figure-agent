from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from contextlib import contextmanager
from pathlib import Path

import authoring_repair_finalize
import authoring_repair_packet
import pytest
import repair_transaction
import yaml
from inputs import parse_spec
from quality_manifest import (
    compute_critique_input_hash,
    critique_generator_version,
    expected_critique_rubric_version,
)

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
        "packet_schema": packet["schema"],
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


def _adjudicated_binding(
    workspace: Path,
    source: Path,
    contract: Path,
    *,
    fixture: str = "demo",
    include_semantic_attribution: bool = True,
) -> Path:
    example = workspace / "examples" / fixture
    artifacts = {
        "critique": example / "critique.md",
        "adjudication": example / "critique_adjudication.yaml",
        "selector_registry": contract.parent / "source_selectors.json",
        "spec": example / "spec.yaml",
        "current_render": example / "build" / f"{fixture}.png",
        "current_pdf": example / "build" / f"{fixture}.pdf",
        "crop_manifest": example / "build" / "audit_crops" / "manifest.json",
        "reference": example / "reference" / "golden.png",
        "semantic_contract": contract.parent / "semantic_contract.yaml",
        "semantic_attribution": contract.parent / "semantic_attribution.json",
    }
    for path in artifacts.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    artifacts["semantic_contract"].write_text(
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
        "path": artifacts["semantic_contract"].relative_to(workspace).as_posix(),
        "sha256": _sha256(artifacts["semantic_contract"].read_bytes()),
    }
    artifacts["selector_registry"].write_text(
        json.dumps(
            {
                "schema": "figure-agent.source-selector-registry.v1",
                "source_path": source.relative_to(workspace).as_posix(),
                "source_sha256": _sha256(source.read_bytes()),
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
                        "semantic_relation_refs": [
                            "label_remains_clear_of_axis"
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    artifacts["spec"].write_text(
        f"name: {fixture}\n"
        "reference_image: reference/golden.png\n"
        "panels: []\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    artifacts["reference"].write_bytes(b"reference")
    artifacts["current_render"].write_bytes(b"png")
    artifacts["current_pdf"].write_bytes(b"pdf")
    crop_manifest = {"schema": "figure-agent.audit-crop-manifest.v1"}
    if include_semantic_attribution:
        crop_manifest.update(
            {
                "fixture": fixture,
                "render_path": artifacts["current_render"]
                .relative_to(example)
                .as_posix(),
            }
        )
    artifacts["crop_manifest"].write_text(
        json.dumps(crop_manifest), encoding="utf-8"
    )
    spec = parse_spec(artifacts["spec"].read_text(encoding="utf-8"))
    critique_metadata = {
        "fixture": fixture,
        "critique_input_hash": compute_critique_input_hash(
            example,
            fixture,
            spec,
            style_lock_path=PLUGIN_ROOT / "styles" / "polymer-paper-preamble.sty",
            base_dir=PLUGIN_ROOT,
        ),
        "generator_version": critique_generator_version(
            PLUGIN_ROOT / "scripts" / "critique_brief.py"
        ),
        "rubric_version": expected_critique_rubric_version(example),
    }
    artifacts["critique"].write_text(
        "---\n"
        + yaml.safe_dump(critique_metadata, sort_keys=False)
        + "---\n",
        encoding="utf-8",
    )
    report = contract.parent / "collisions.json"
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    report_payload.update(
        {
            "fixture": fixture,
            "render_path": f"build/{fixture}.png",
            "render_sha256": _sha256(artifacts["current_render"].read_bytes()),
            "render_pdf": f"build/{fixture}.pdf",
            "render_pdf_sha256": _sha256(artifacts["current_pdf"].read_bytes()),
        }
    )
    report.write_text(json.dumps(report_payload), encoding="utf-8")
    selector_registry_relative = artifacts["selector_registry"].relative_to(
        workspace
    ).as_posix()
    artifacts["adjudication"].write_text(
        "schema: figure-agent.critique-adjudication.v1\n"
        f"fixture: {fixture}\n"
        f"source_critique_hash: {_sha256(artifacts['critique'].read_bytes())}\n"
        "decisions:\n"
        "- finding_id: C001\n"
        "  decision: apply\n"
        "  reason: bounded repair\n"
        "  patch_target: panel A label\n"
        "  evidence: critique C001 and collision TC001\n"
        "  repair_evidence:\n"
        f"    report_path: {contract.parent.relative_to(workspace).as_posix()}/collisions.json\n"
        "    finding_id: TC001\n"
        f"    selector_registry_path: {selector_registry_relative}\n",
        encoding="utf-8",
    )

    def record(path: Path) -> dict[str, str]:
        return {
            "path": path.relative_to(workspace).as_posix(),
            "sha256": _sha256(path.read_bytes()),
        }

    semantic_attribution = {
        "schema": "figure-agent.semantic-finding-attribution.v1",
        "fixture": fixture,
        "machine_finding": {
            "report_path": (
                contract.parent.relative_to(workspace).as_posix()
                + "/collisions.json"
            ),
            "report_sha256": _sha256(
                (contract.parent / "collisions.json").read_bytes()
            ),
            "finding_id": "TC001",
        },
        "semantic_contract": semantic_contract_record,
        "source": record(source),
        "selector_id": "panel-a-label",
        "semantic_object_refs": ["panel_a.axis", "panel_a.label"],
        "semantic_relation_refs": ["label_remains_clear_of_axis"],
        "attribution_state": "exact",
        "publication_acceptance": "not_claimed",
    }
    artifacts["semantic_attribution"].write_text(
        json.dumps(semantic_attribution), encoding="utf-8"
    )
    binding_payload = {
        "schema": "figure-agent.adjudicated-repair-binding.v1",
        "fixture": fixture,
        "critique": {
            **record(artifacts["critique"]),
            "finding_id": "C001",
        },
        "adjudication": {
            **record(artifacts["adjudication"]),
            "decision": "apply",
        },
        "machine_finding": semantic_attribution["machine_finding"],
        "selector_registry": record(artifacts["selector_registry"]),
        "source": record(source),
        "spec": record(artifacts["spec"]),
        "current_render": record(artifacts["current_render"]),
        "current_pdf": record(artifacts["current_pdf"]),
        "crop_manifest": record(artifacts["crop_manifest"]),
        "attribution_state": "exact",
        "target_contract": record(contract),
        "publication_acceptance": "not_claimed",
    }
    if include_semantic_attribution:
        binding_payload["semantic_attribution"] = record(
            artifacts["semantic_attribution"]
        )
    binding = contract.parent / "critique_repair_binding.json"
    binding.write_text(
        json.dumps(binding_payload),
        encoding="utf-8",
    )
    return binding


def _authorized_materialization(
    tmp_path: Path,
) -> tuple[Path, dict[str, object], dict[str, object], dict[str, object], Path, Path]:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    packet, _ = (
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )
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


def _fake_strict_compiler(
    tmp_path: Path,
    *,
    state: str = "passed",
    returncode: int = 0,
    write_status: bool = True,
    write_render: bool = True,
    expected_workspace: Path | None = None,
) -> Path:
    plugin_root = tmp_path / "plugin"
    script = plugin_root / "scripts" / "compile.sh"
    script.parent.mkdir(parents=True, exist_ok=True)
    detector_failed = "true" if state == "failed" else "false"
    reports = {
        "collisions.json": "figure-agent.text-collisions.v1",
        "visual_clash.json": None,
        "text_boundary_clash.json": "figure-agent.text-boundary-clash.v1",
        "label_path_proximity.json": "figure-agent.label-path-proximity.v1",
        "undeclared_geometry.json": "figure-agent.undeclared-geometry.v1",
        "label_hyphenation.json": "figure-agent.label-hyphenation.v1",
        "semantic_assertions.json": "figure-agent.semantic-assertions.v1",
        "vector_clearance.json": "figure-agent.vector-clearance.v1",
        "tex_assertions.json": "figure-agent.tex-assertions.v1",
        "physics_grounding.json": None,
    }
    report_script = "".join(
        "printf '%s' '"
        + json.dumps({"schema": schema} if schema else {"total": 0})
        + f"' > \"$build/{name}\"\n"
        for name, schema in reports.items()
    )
    render_script = (
        "printf 'pdf' > \"$build/$base.pdf\"\n"
        "printf 'png' > \"$build/$base.png\"\n"
        if write_render
        else ""
    )
    status_script = (
        "cat > \"$build/strict_status.json\" <<'EOF'\n"
        "{\n"
        '  "schema": "figure-agent.strict-status.v1",\n'
        '  "strict_requested": true,\n'
        f'  "detector_failed": {detector_failed},\n'
        f'  "state": "{state}"\n'
        "}\n"
        "EOF\n"
        if write_status
        else ""
    )
    script.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        + (
            f'test "${{FIGURE_AGENT_WORKSPACE:-}}" = "{expected_workspace}"\n'
            if expected_workspace is not None
            else ""
        )
        +
        "tex=\"$1\"\n"
        "base=\"$(basename \"$tex\" .tex)\"\n"
        "build=\"$(dirname \"$tex\")/build\"\n"
        "mkdir -p \"$build\"\n"
        f"{render_script}"
        f"{report_script}"
        f"{status_script}"
        f"exit {returncode}\n",
        encoding="utf-8",
    )
    return plugin_root


def _authorization_artifact(
    receipt_path: Path, authorization: dict[str, object]
) -> Path:
    path = receipt_path.parent / "materialization_authorization.json"
    path.write_text(json.dumps(authorization), encoding="utf-8")
    return path


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

    assert packet["schema"] == "figure-agent.repair-execution-packet.v4"
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
        allow_legacy_packet=True,
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
        allow_legacy_packet=True,
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
            allow_legacy_packet=True,
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
        allow_legacy_packet=True,
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
        allow_legacy_packet=True,
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
            allow_legacy_packet=True,
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


def test_post_render_finalizer_promotes_only_strict_pass_to_human_review_pending(
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
    output_before = output.read_bytes()

    finalized = authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=_authorization_artifact(receipt_path, authorization),
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, expected_workspace=workspace),
    )

    assert output.read_bytes() == output_before
    assert finalized["decision"] == "materialized_machine_verified_human_review_pending"
    assert finalized["post_render_verification"] == "passed"
    assert finalized["external_compile"]["returncode"] == 0
    assert finalized["external_compile"]["strict_status"]["state"] == "passed"
    assert finalized["external_compile"]["pdf"]["sha256"] == _sha256(b"pdf")
    assert finalized["external_compile"]["png"]["sha256"] == _sha256(b"png")
    assert set(finalized["external_compile"]["detector_reports"]) == {
        "collisions",
        "visual_clash",
        "text_boundary_clash",
        "label_path_proximity",
        "undeclared_geometry",
        "label_hyphenation",
        "semantic_assertions",
        "vector_clearance",
        "tex_assertions",
        "physics_grounding",
    }
    assert finalized["human_review"] == "pending"
    assert finalized["publication_acceptance"] == "not_claimed"
    assert json.loads(receipt_path.read_text(encoding="utf-8")) == finalized


def test_post_render_finalizer_revalidates_bound_authority_inside_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    packet, _prompt = (
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )
    )
    response = {
        "replacement_utf8": (
            r"\node[yshift=-2mm] {repeated dispersive trapping};"
        ),
        "change_summary": "Lower the colliding label.",
    }
    preview = authoring_repair_packet.materialize_repair_candidate(
        packet, response, workspace_root=workspace, apply=False
    )
    authorization = _materialization_authorization(
        packet,
        output_sha256=str(preview["output_sha256"]),
        preview_sha256=str(preview["preview_sha256"]),
    )
    output = workspace / str(packet["output_path"])
    receipt_path = output.parent / "materialization_receipt.json"
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
    original_lock = repair_transaction.exclusive_lock

    @contextmanager
    def drift_after_lock(*args: object, **kwargs: object):
        with original_lock(*args, **kwargs):
            binding.write_bytes(binding.read_bytes() + b"\n")
            yield

    monkeypatch.setattr(repair_transaction, "exclusive_lock", drift_after_lock)

    with pytest.raises(
        authoring_repair_finalize.AuthoringRepairFinalizeError,
        match="repair packet authority invalid: adjudicated binding hash drift",
    ):
        authoring_repair_finalize.finalize_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(tmp_path),
        )

    pending = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert pending["decision"] == "materialized_verification_pending"
    assert not (output.parent / "build").exists()


def test_post_render_finalizer_persists_compile_failure_without_promotion(
    tmp_path: Path,
) -> None:
    workspace, packet, response, authorization, output, receipt_path = (
        _authorized_materialization(tmp_path)
    )
    original_receipt = authoring_repair_packet.materialize_repair_candidate(
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

    assert output.is_file()
    assert failed["decision"] == "materialized_verification_failed"
    assert failed["post_render_verification"] == "failed"
    assert failed["external_compile"]["returncode"] == 1
    assert failed["external_compile"]["failure_reason"] == "strict_compile_nonzero"
    assert failed["human_review"] == "pending"
    assert failed["publication_acceptance"] == "not_claimed"
    assert failed["output_sha256"] == original_receipt["output_sha256"]
    assert json.loads(receipt_path.read_text(encoding="utf-8")) == failed


def test_post_render_finalizer_rejects_receipt_summary_drift_before_compile(
    tmp_path: Path,
) -> None:
    workspace, packet, response, authorization, output, receipt_path = (
        _authorized_materialization(tmp_path)
    )
    receipt = authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        authorization=authorization,
        receipt_path=receipt_path,
    )
    receipt["change_summary"] = "Approval did not cover this summary."
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    packet_path = receipt_path.parent / "repair_packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(
        authoring_repair_finalize.AuthoringRepairFinalizeError,
        match="authorization provenance mismatch",
    ):
        authoring_repair_finalize.finalize_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=_authorization_artifact(receipt_path, authorization),
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(tmp_path),
        )

    assert not (output.parent / "build").exists()


def test_post_render_finalizer_rejects_output_and_receipt_rebinding(
    tmp_path: Path,
) -> None:
    workspace, packet, response, authorization, output, receipt_path = (
        _authorized_materialization(tmp_path)
    )
    receipt = authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        authorization=authorization,
        receipt_path=receipt_path,
    )
    output.write_text(output.read_text(encoding="utf-8") + "% unauthorized\n", encoding="utf-8")
    rebound_hash = _sha256(output.read_bytes())
    receipt["output_sha256"] = rebound_hash
    receipt["authorization"]["authorized_output_sha256"] = rebound_hash
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    packet_path = receipt_path.parent / "repair_packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(
        authoring_repair_finalize.AuthoringRepairFinalizeError,
        match="authorization provenance mismatch",
    ):
        authoring_repair_finalize.finalize_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=_authorization_artifact(receipt_path, authorization),
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(tmp_path),
        )

    assert not (output.parent / "build").exists()


def test_post_render_finalizer_rejects_symlinked_evidence_inputs(
    tmp_path: Path,
) -> None:
    workspace, packet, response, authorization, _output, receipt_path = (
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
    links = workspace / "links"
    links.mkdir()
    packet_link = links / "repair_packet.json"
    receipt_link = links / "materialization_receipt.json"
    packet_link.symlink_to(packet_path)
    receipt_link.symlink_to(receipt_path)

    with pytest.raises(
        authoring_repair_finalize.AuthoringRepairFinalizeError,
        match="must not be symlinks",
    ):
        authoring_repair_finalize.finalize_materialized_candidate(
            packet_path=packet_link,
            receipt_path=receipt_link,
            authorization_path=_authorization_artifact(receipt_path, authorization),
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(tmp_path),
        )

    pending = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert pending["decision"] == "materialized_verification_pending"


def test_post_render_finalizer_requires_exact_fixture_repair_attempt_boundary(
    tmp_path: Path,
) -> None:
    workspace, packet, response, authorization, _output, receipt_path = (
        _authorized_materialization(tmp_path)
    )
    authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        authorization=authorization,
        receipt_path=receipt_path,
    )
    outside = workspace / "outside"
    outside.mkdir()
    packet_path = outside / "repair_packet.json"
    copied_receipt = outside / "materialization_receipt.json"
    copied_authorization = outside / "materialization_authorization.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    copied_receipt.write_bytes(receipt_path.read_bytes())
    copied_authorization.write_text(json.dumps(authorization), encoding="utf-8")

    with pytest.raises(
        authoring_repair_finalize.AuthoringRepairFinalizeError,
        match="exact execution-repair attempt",
    ):
        authoring_repair_finalize.finalize_materialized_candidate(
            packet_path=packet_path,
            receipt_path=copied_receipt,
            authorization_path=copied_authorization,
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(tmp_path),
        )


def test_post_render_finalizer_records_missing_strict_status_as_failure(
    tmp_path: Path,
) -> None:
    workspace, packet, response, authorization, _output, receipt_path = (
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
        plugin_root=_fake_strict_compiler(tmp_path, write_status=False),
    )

    assert failed["decision"] == "materialized_verification_failed"
    assert failed["post_render_verification"] == "failed"
    assert (
        failed["external_compile"]["failure_reason"]
        == "strict_status_missing_or_invalid"
    )
    assert failed["publication_acceptance"] == "not_claimed"


def test_post_render_finalizer_records_missing_render_as_failure(
    tmp_path: Path,
) -> None:
    workspace, packet, response, authorization, _output, receipt_path = (
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
        plugin_root=_fake_strict_compiler(tmp_path, write_render=False),
    )

    assert failed["decision"] == "materialized_verification_failed"
    assert failed["external_compile"]["failure_reason"] == "render_artifact_missing"
    assert failed["publication_acceptance"] == "not_claimed"


def test_post_render_finalizer_refuses_preexisting_build_evidence(
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
    build = output.parent / "build"
    build.mkdir()
    (build / "strict_status.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.strict-status.v1",
                "strict_requested": True,
                "detector_failed": False,
                "state": "passed",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        authoring_repair_finalize.AuthoringRepairFinalizeError,
        match="verification build directory must be absent",
    ):
        authoring_repair_finalize.finalize_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=_authorization_artifact(receipt_path, authorization),
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(tmp_path, write_status=False),
        )

    pending = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert pending["decision"] == "materialized_verification_pending"


def test_post_render_finalizer_recovers_after_final_receipt_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
    original_atomic_write = repair_transaction.atomic_write_json

    def fail_final_receipt(path: Path, payload: dict[str, object]) -> None:
        if payload.get("decision") == (
            "materialized_machine_verified_human_review_pending"
        ):
            raise OSError("final verification receipt interrupted")
        original_atomic_write(path, payload)

    monkeypatch.setattr(repair_transaction, "atomic_write_json", fail_final_receipt)
    with pytest.raises(OSError, match="final verification receipt interrupted"):
        authoring_repair_finalize.finalize_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=_authorization_artifact(receipt_path, authorization),
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(tmp_path),
        )

    prepared = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert prepared["decision"] == "materialized_verification_prepared"
    assert prepared["recovery_required"] is True
    assert prepared["external_compile"]["candidate_sha256"] == _sha256(
        output.read_bytes()
    )
    assert (output.parent / "build").is_dir()

    monkeypatch.setattr(repair_transaction, "atomic_write_json", original_atomic_write)
    recovered = authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=_authorization_artifact(receipt_path, authorization),
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path),
    )

    assert recovered["post_render_verification"] == "passed"
    assert recovered["recovery_required"] is False
    assert recovered["publication_acceptance"] == "not_claimed"


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
        allow_legacy_packet=True,
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
        allow_legacy_packet=True,
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
            allow_legacy_packet=True,
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
            allow_legacy_packet=True,
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


def test_compiles_adjudicated_binding_into_transitive_packet(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)

    packet, prompt = (
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )
    )

    binding_payload = json.loads(binding.read_text(encoding="utf-8"))
    assert packet["source"] == binding_payload["source"]
    assert packet["target_contract"] == binding_payload["target_contract"]
    assert packet["adjudicated_repair_binding"] == {
        "path": binding.relative_to(workspace).as_posix(),
        "sha256": _sha256(binding.read_bytes()),
    }
    assert packet["authority_contract"] == {
        "schema": "figure-agent.repair-authority-contract.v1",
        "mode": "adjudicated_binding",
        "required_record": "adjudicated_repair_binding",
    }
    assert packet["packet_sha256"] == (
        authoring_repair_packet.canonical_packet_sha256(packet)
    )
    assert packet["adjudicated_repair_binding"]["sha256"] != packet[
        "target_contract"
    ]["sha256"]
    assert "# Bound repair execution: demo" in prompt


def test_current_v4_compile_rejects_legacy_binding_without_semantic_authority(
    tmp_path: Path,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(
        workspace,
        source,
        contract,
        include_semantic_attribution=False,
    )

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="current v4 repair packets require semantic attribution authority",
    ):
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )


@pytest.mark.parametrize("rewrite", ["mode", "schema"])
def test_bound_packet_cannot_be_downgraded_by_removing_binding_and_rehashing(
    tmp_path: Path, rewrite: str
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    packet, _prompt = (
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )
    )
    downgraded = json.loads(json.dumps(packet))
    downgraded.pop("adjudicated_repair_binding")
    if rewrite == "mode":
        downgraded["authority_contract"] = {
            "schema": "figure-agent.repair-authority-contract.v1",
            "mode": "legacy_explicit_inputs",
            "required_record": None,
        }
    else:
        downgraded["schema"] = "figure-agent.repair-execution-packet.v3"
        downgraded.pop("authority_contract")
    downgraded["packet_sha256"] = (
        authoring_repair_packet.canonical_packet_sha256(downgraded)
    )

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="attempt requires adjudicated binding authority",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            downgraded,
            {
                "replacement_utf8": (
                    r"\node[yshift=-2mm] {repeated dispersive trapping};"
                ),
                "change_summary": "Lower the colliding label.",
            },
            workspace_root=workspace,
            apply=False,
        )


def test_bound_packet_rejects_binding_record_deletion_without_mode_rewrite(
    tmp_path: Path,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    packet, _prompt = (
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )
    )
    packet.pop("adjudicated_repair_binding")
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(
        packet
    )

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="authority record is required",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            {
                "replacement_utf8": r"\node {repaired};",
                "change_summary": "Bounded repair.",
            },
            workspace_root=workspace,
            apply=False,
        )


def test_legacy_packet_has_explicit_authority_contract(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)

    packet, _prompt = authoring_repair_packet.compile_repair_execution_packet(
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

    assert packet["authority_contract"] == {
        "schema": "figure-agent.repair-authority-contract.v1",
        "mode": "legacy_explicit_inputs",
        "required_record": None,
    }
    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="explicit compatibility opt-in",
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
            apply=False,
        )


def test_redirected_target_cannot_silently_downgrade_bound_packet(
    tmp_path: Path,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    packet, _prompt = (
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )
    )
    redirected_target = source.parent / "redirected_repair_targets.json"
    redirected_target.write_bytes(contract.read_bytes())
    packet.pop("adjudicated_repair_binding")
    packet["authority_contract"] = {
        "schema": "figure-agent.repair-authority-contract.v1",
        "mode": "legacy_explicit_inputs",
        "required_record": None,
    }
    packet["target_contract"] = {
        "path": redirected_target.relative_to(workspace).as_posix(),
        "sha256": _sha256(redirected_target.read_bytes()),
    }
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(
        packet
    )

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="explicit compatibility opt-in",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            {
                "replacement_utf8": r"\node {repaired};",
                "change_summary": "Bounded repair.",
            },
            workspace_root=workspace,
            apply=False,
        )


def test_saved_v3_packet_without_authority_contract_remains_readable(
    tmp_path: Path,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    packet, _prompt = authoring_repair_packet.compile_repair_execution_packet(
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
    packet["schema"] = "figure-agent.repair-execution-packet.v3"
    packet.pop("authority_contract")
    packet["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(
        packet
    )

    preview = authoring_repair_packet.materialize_repair_candidate(
        packet,
        {
            "replacement_utf8": (
                r"\node[yshift=-2mm] {repeated dispersive trapping};"
            ),
            "change_summary": "Lower the colliding label.",
        },
        workspace_root=workspace,
        apply=False,
        allow_legacy_packet=True,
    )

    assert preview["packet_sha256"] == packet["packet_sha256"]


def test_rehashed_packet_cannot_reuse_prior_materialization_authorization(
    tmp_path: Path,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    packet, _prompt = authoring_repair_packet.compile_repair_execution_packet(
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
        "replacement_utf8": (
            r"\node[yshift=-2mm] {repeated dispersive trapping};"
        ),
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
        output_sha256=str(preview["output_sha256"]),
        preview_sha256=str(preview["preview_sha256"]),
    )
    rebound = json.loads(json.dumps(packet))
    rebound["model_id"] = "gpt-5.5-rebound"
    rebound["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(
        rebound
    )

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="materialization_decision_packet_hash_mismatch",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            rebound,
            response,
            workspace_root=workspace,
            authorization=authorization,
            receipt_path=(
                workspace
                / "examples/demo/review/failure-first/execution-repair-v1/"
                "materialization_receipt.json"
            ),
            allow_legacy_packet=True,
        )


@pytest.mark.parametrize("drifted_artifact", ["binding", "target", "report"])
def test_bound_packet_authority_drift_blocks_preview_and_apply_without_writes(
    tmp_path: Path, drifted_artifact: str
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    packet, _prompt = (
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )
    )
    response = {
        "replacement_utf8": (
            r"\node[yshift=-2mm] {repeated dispersive trapping};"
        ),
        "change_summary": "Lower the colliding label.",
    }
    drift_path = {
        "binding": binding,
        "target": contract,
        "report": contract.parent / "collisions.json",
    }[drifted_artifact]
    drift_path.write_bytes(drift_path.read_bytes() + b"\n")
    output = workspace / str(packet["output_path"])
    receipt = output.parent / "materialization_receipt.json"

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="hash drift",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace,
            apply=False,
        )
    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="hash drift",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace,
            authorization={},
            receipt_path=receipt,
        )

    assert not output.exists()
    assert not receipt.exists()


@pytest.mark.parametrize(
    ("substitution", "message"),
    [
        ("source", "authority substitution"),
        ("target", "authority substitution"),
        ("editable_finding", "authority substitution"),
        ("finding_report", "finding report substitution"),
    ],
)
def test_bound_packet_rejects_rehashed_authority_substitution(
    tmp_path: Path, substitution: str, message: str
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    packet, _prompt = (
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )
    )
    tampered = json.loads(json.dumps(packet))
    if substitution == "source":
        tampered["source"]["sha256"] = "sha256:" + "0" * 64
    elif substitution == "target":
        tampered["target_contract"]["sha256"] = "sha256:" + "0" * 64
    elif substitution == "editable_finding":
        tampered["editable_target"]["finding_id"] = "TC999"
    else:
        tampered["finding_reports"][0]["sha256"] = "sha256:" + "0" * 64
    tampered["packet_sha256"] = (
        authoring_repair_packet.canonical_packet_sha256(tampered)
    )

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match=message,
    ):
        authoring_repair_packet.materialize_repair_candidate(
            tampered,
            {
                "replacement_utf8": (
                    r"\node[yshift=-2mm] {repeated dispersive trapping};"
                ),
                "change_summary": "Lower the colliding label.",
            },
            workspace_root=workspace,
            apply=False,
        )


def test_bound_packet_authority_is_revalidated_inside_materialization_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    packet, _prompt = (
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )
    )
    response = {
        "replacement_utf8": (
            r"\node[yshift=-2mm] {repeated dispersive trapping};"
        ),
        "change_summary": "Lower the colliding label.",
    }
    preview = authoring_repair_packet.materialize_repair_candidate(
        packet, response, workspace_root=workspace, apply=False
    )
    authorization = _materialization_authorization(
        packet,
        output_sha256=str(preview["output_sha256"]),
        preview_sha256=str(preview["preview_sha256"]),
    )
    output = workspace / str(packet["output_path"])
    receipt = output.parent / "materialization_receipt.json"
    original_lock = repair_transaction.exclusive_lock

    @contextmanager
    def drift_after_lock(*args: object, **kwargs: object):
        with original_lock(*args, **kwargs):
            binding.write_bytes(binding.read_bytes() + b"\n")
            yield

    monkeypatch.setattr(repair_transaction, "exclusive_lock", drift_after_lock)

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="adjudicated binding hash drift",
    ):
        authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace,
            authorization=authorization,
            receipt_path=receipt,
        )

    assert not output.exists()
    assert not receipt.exists()


def test_finding_report_record_uses_one_parsed_byte_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    report = contract.parent / "collisions.json"
    report_bytes = report.read_bytes()
    report_read_bytes = 0
    report_read_text = 0
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text

    def observed_read_bytes(path: Path) -> bytes:
        nonlocal report_read_bytes
        if path == report:
            report_read_bytes += 1
        return original_read_bytes(path)

    def observed_read_text(
        path: Path, encoding: str | None = None, errors: str | None = None
    ) -> str:
        nonlocal report_read_text
        if path == report:
            report_read_text += 1
        return original_read_text(path, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_bytes", observed_read_bytes)
    monkeypatch.setattr(Path, "read_text", observed_read_text)

    packet, _prompt = authoring_repair_packet.compile_repair_execution_packet(
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

    assert report_read_bytes == 1
    assert report_read_text == 0
    assert packet["finding_reports"] == [
        {
            "path": report.relative_to(workspace).as_posix(),
            "schema": "figure-agent.text-collisions.v1",
            "sha256": _sha256(report_bytes),
        }
    ]


def test_adjudicated_binding_rejects_fabricated_partial_binding(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    payload = json.loads(binding.read_text(encoding="utf-8"))
    for field in (
        "critique",
        "adjudication",
        "machine_finding",
        "selector_registry",
        "spec",
        "current_render",
        "current_pdf",
        "crop_manifest",
    ):
        payload.pop(field)
    binding.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="top-level fields",
    ):
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )


def test_adjudicated_binding_requires_canonical_filename(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    wrong_name = binding.with_name("anything.json")
    binding.rename(wrong_name)

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="critique_repair_binding.json",
    ):
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=wrong_name.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("schema", "figure-agent.adjudicated-repair-binding.v2", "schema"),
        ("fixture", "other", "fixture"),
        ("attribution_state", "ambiguous", "exact attribution"),
        ("publication_acceptance", "accepted", "publication acceptance"),
    ],
)
def test_adjudicated_binding_rejects_invalid_authority_fields(
    tmp_path: Path,
    field: str,
    value: str,
    error: str,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    payload = json.loads(binding.read_text(encoding="utf-8"))
    payload[field] = value
    binding.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match=error,
    ):
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )


@pytest.mark.parametrize("record_name", ["source", "target_contract"])
def test_adjudicated_binding_rejects_non_exact_path_hash_records(
    tmp_path: Path,
    record_name: str,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    payload = json.loads(binding.read_text(encoding="utf-8"))
    payload[record_name]["substitution"] = "not-authoritative"
    binding.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match=f"binding {record_name.replace('_', ' ')} record is invalid",
    ):
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )


@pytest.mark.parametrize("drift", ["source", "target_contract"])
def test_adjudicated_binding_rejects_live_hash_drift(
    tmp_path: Path,
    drift: str,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    drifted = source if drift == "source" else contract
    drifted.write_bytes(drifted.read_bytes() + b"\n")

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match=f"binding {drift.replace('_', ' ')} hash drift",
    ):
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )


def test_adjudicated_binding_rejects_packet_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)

    def substituted_packet(*args: object, **kwargs: object) -> tuple[dict[str, object], str]:
        return (
            {
                "source": {"path": "substituted.tex", "sha256": _sha256(b"x")},
                "target_contract": {
                    "path": "substituted.json",
                    "sha256": _sha256(b"y"),
                },
            },
            "prompt",
        )

    monkeypatch.setattr(
        authoring_repair_packet,
        "compile_repair_execution_packet",
        substituted_packet,
    )
    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="compiled packet authority substitution",
    ):
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )


def test_adjudicated_binding_requires_attempt_local_adjacency(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="binding, target contract, and output must be adjacent",
    ):
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v2/"
                "repaired_generated.tex"
            ),
        )


def test_adjudicated_binding_path_must_be_fixture_repair_attempt(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    wrong = source.parent / binding.name
    wrong.write_bytes(binding.read_bytes())

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="execution-repair-vN",
    ):
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=wrong.relative_to(workspace).as_posix(),
            output_path=(
                "examples/demo/review/failure-first/execution-repair-v1/"
                "repaired_generated.tex"
            ),
        )


@pytest.mark.parametrize("linked_artifact", ["binding", "source", "target_contract"])
def test_adjudicated_binding_rejects_symlinked_authority(
    tmp_path: Path,
    linked_artifact: str,
) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    selected = {
        "binding": binding,
        "source": source,
        "target_contract": contract,
    }[linked_artifact]
    real = selected.with_name(f"real-{selected.name}")
    selected.rename(real)
    selected.symlink_to(real.name)

    with pytest.raises(
        authoring_repair_packet.RepairExecutionPacketError,
        match="must not traverse a symlink",
    ):
        authoring_repair_packet.compile_adjudicated_repair_execution_packet(
            "demo",
            workspace_root=workspace,
            model_id="gpt-5.5",
            binding_path=binding.relative_to(workspace).as_posix(),
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


def test_cli_compiles_from_adjudicated_binding_only(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    repair_root = "examples/demo/review/failure-first/execution-repair-v1"
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
            "--binding",
            binding.relative_to(workspace).as_posix(),
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
    packet = json.loads(
        (workspace / repair_root / "repair_packet.json").read_text(encoding="utf-8")
    )
    assert packet["adjudicated_repair_binding"]["path"] == binding.relative_to(
        workspace
    ).as_posix()
    assert packet["packet_sha256"] == (
        authoring_repair_packet.canonical_packet_sha256(packet)
    )


def test_cli_rejects_binding_mixed_with_legacy_authority(tmp_path: Path) -> None:
    workspace, source, contract = _fixture(tmp_path)
    binding = _adjudicated_binding(workspace, source, contract)
    repair_root = "examples/demo/review/failure-first/execution-repair-v1"
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
            "--binding",
            binding.relative_to(workspace).as_posix(),
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

    assert result.returncode == 2
    assert "mutually exclusive" in result.stderr
    assert not (workspace / repair_root / "repair_packet.json").exists()


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
    rejected_preview = subprocess.run(
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
    assert rejected_preview.returncode == 1
    assert "explicit compatibility opt-in" in rejected_preview.stderr

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
            "--legacy-packet",
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
            "--legacy-packet",
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

    finalize_env = env.copy()
    finalize_env["FIGURE_AGENT_PLUGIN_ROOT"] = str(_fake_strict_compiler(tmp_path))
    finalize = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "authoring-repair-finalize",
            "--packet",
            f"{repair_root}/repair_packet.json",
            "--receipt",
            f"{repair_root}/materialization_receipt.json",
            "--authorization",
            f"{repair_root}/materialization_authorization.json",
            "--legacy-packet",
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        env=finalize_env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert finalize.returncode == 0, finalize.stderr
    finalized = json.loads(finalize.stdout)
    assert finalized["post_render_verification"] == "passed"
    assert finalized["human_review"] == "pending"
    assert finalized["publication_acceptance"] == "not_claimed"
