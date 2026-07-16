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
import authoring_repair_rollback
import closed_loop_attempt_state
import closed_loop_current_state
import closed_loop_machine_repair
import closed_loop_repair_authorization
import fig_run
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


def _repair_candidate_ready_attempt(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path, Path, Path]:
    workspace, packet, response, authorization, output, receipt = (
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
    authorization_path = _authorization_artifact(receipt, authorization)
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
        (
            "repair_candidate_ready",
            "workflow_agent",
            {
                "repair_execution_packet": packet_path,
                "repair_response": response_path,
                "materialization_preview": preview_path,
            },
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
    return workspace, state_path, response_path, authorization_path, output, receipt


def _repair_authorized_attempt(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path, Path]:
    workspace, state_path, response_path, authorization_path, output, receipt = (
        _repair_candidate_ready_attempt(tmp_path)
    )
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state = closed_loop_attempt_state.transition_state(
        state,
        next_state="repair_authorized",
        actor="test",
        actor_role="human_repair_authorizer",
        evidence={"human_authorization": authorization_path},
        workspace_root=workspace,
        previous_state_path=state_path,
    )
    state_path = closed_loop_attempt_state.publish_state(
        state,
        workspace_root=workspace,
    )
    return workspace, state_path, response_path, output, receipt


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
    original_lock = repair_transaction.recoverable_exclusive_lock

    @contextmanager
    def drift_after_lock(*args: object, **kwargs: object):
        with original_lock(*args, **kwargs):
            binding.write_bytes(binding.read_bytes() + b"\n")
            yield

    monkeypatch.setattr(
        repair_transaction,
        "recoverable_exclusive_lock",
        drift_after_lock,
    )

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


def test_failed_materialization_rolls_back_only_the_hash_bound_output(
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
    failed = authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, state="failed", returncode=1),
    )
    build = output.parent / "build"
    build_evidence = sorted(path.relative_to(build) for path in build.rglob("*"))

    rolled_back = authoring_repair_rollback.rollback_failed_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
    )

    assert failed["decision"] == "materialized_verification_failed"
    assert not output.exists()
    assert build.is_dir()
    assert sorted(path.relative_to(build) for path in build.rglob("*")) == build_evidence
    assert rolled_back["decision"] == "materialized_rolled_back_after_verification_failure"
    assert rolled_back["rollback"]["status"] == "completed"
    assert rolled_back["rollback"]["output_path"] == packet["output_path"]
    assert rolled_back["rollback"]["output_sha256"] == failed["output_sha256"]
    assert rolled_back["post_render_verification"] == "failed"
    assert rolled_back["publication_acceptance"] == "not_claimed"
    assert rolled_back["recovery_required"] is False
    assert json.loads(receipt_path.read_text(encoding="utf-8")) == rolled_back


def test_failed_materialization_rollback_refuses_output_hash_drift(
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
    authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, state="failed", returncode=1),
    )
    receipt_before = receipt_path.read_bytes()
    output.write_text("drifted candidate\n", encoding="utf-8")

    with pytest.raises(
        authoring_repair_rollback.AuthoringRepairRollbackError,
        match="materialized output hash drift",
    ):
        authoring_repair_rollback.rollback_failed_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
            workspace_root=workspace,
        )

    assert output.read_text(encoding="utf-8") == "drifted candidate\n"
    assert receipt_path.read_bytes() == receipt_before


def test_failed_materialization_rollback_rejects_final_component_symlink(
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
    authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, state="failed", returncode=1),
    )
    receipt_before = receipt_path.read_bytes()
    sibling = output.with_name("sibling.tex")
    output.replace(sibling)
    output.symlink_to(sibling.name)

    with pytest.raises(
        authoring_repair_rollback.AuthoringRepairRollbackError,
        match="materialized output must not be a symlink",
    ):
        authoring_repair_rollback.rollback_failed_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
            workspace_root=workspace,
        )

    assert output.is_symlink()
    assert sibling.is_file()
    assert _sha256(sibling.read_bytes()) == json.loads(
        receipt_before
    )["output_sha256"]
    assert receipt_path.read_bytes() == receipt_before


def test_failed_materialization_rollback_refuses_identity_swap_before_unlink(
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
    authorization_path = _authorization_artifact(receipt_path, authorization)
    authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, state="failed", returncode=1),
    )
    replacement = output.with_name("replacement.tex")
    replacement.write_text("replacement must survive\n", encoding="utf-8")
    original_unlink = authoring_repair_rollback.os.unlink
    swapped = False

    def swap_before_quarantine_unlink(
        path: str | bytes | Path,
        *,
        dir_fd: int | None = None,
    ) -> None:
        nonlocal swapped
        if not swapped and ".rollback-" in os.fsdecode(path):
            replacement.replace(output)
            swapped = True
        original_unlink(path, dir_fd=dir_fd)

    monkeypatch.setattr(
        authoring_repair_rollback.os,
        "unlink",
        swap_before_quarantine_unlink,
    )

    with pytest.raises(
        authoring_repair_rollback.AuthoringRepairRollbackError,
        match="materialized output identity drift",
    ):
        authoring_repair_rollback.rollback_failed_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
            workspace_root=workspace,
        )

    assert output.read_text(encoding="utf-8") == "replacement must survive\n"
    prepared = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert prepared["decision"] == "materialized_rollback_prepared"
    assert prepared["recovery_required"] is True


def test_failed_materialization_rollback_preserves_swap_captured_by_quarantine(
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
    authorization_path = _authorization_artifact(receipt_path, authorization)
    authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, state="failed", returncode=1),
    )
    replacement = output.with_name("replacement.tex")
    replacement.write_text("replacement must survive\n", encoding="utf-8")
    preserved = output.with_name("preserved-authorized-output.tex")
    original_replace = authoring_repair_rollback.os.replace
    swapped = False

    def swap_at_quarantine_boundary(
        source: str | bytes | Path,
        destination: str | bytes | Path,
        *,
        src_dir_fd: int | None = None,
        dst_dir_fd: int | None = None,
    ) -> None:
        nonlocal swapped
        if not swapped and ".rollback-" in os.fsdecode(destination):
            original_replace(output, preserved)
            original_replace(replacement, output)
            swapped = True
        original_replace(
            source,
            destination,
            src_dir_fd=src_dir_fd,
            dst_dir_fd=dst_dir_fd,
        )

    monkeypatch.setattr(
        authoring_repair_rollback.os,
        "replace",
        swap_at_quarantine_boundary,
    )

    with pytest.raises(
        authoring_repair_rollback.AuthoringRepairRollbackError,
        match="materialized output hash drift",
    ):
        authoring_repair_rollback.rollback_failed_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
            workspace_root=workspace,
        )

    assert output.read_text(encoding="utf-8") == "replacement must survive\n"
    assert preserved.is_file()
    quarantine = list(output.parent.glob(f".{output.name}.rollback-*"))
    assert len(quarantine) == 1
    assert quarantine[0].read_text(encoding="utf-8") == "replacement must survive\n"
    prepared = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert prepared["decision"] == "materialized_rollback_prepared"
    assert prepared["recovery_required"] is True


def test_failed_materialization_rollback_recovers_after_write_failure_and_stale_lock(
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
    authorization_path = _authorization_artifact(receipt_path, authorization)
    authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path, state="failed", returncode=1),
    )
    original_atomic_write = repair_transaction.atomic_write_json
    writes = 0

    def fail_completed_receipt(path: Path, payload: dict[str, object]) -> None:
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("rollback receipt interrupted")
        original_atomic_write(path, payload)

    monkeypatch.setattr(repair_transaction, "atomic_write_json", fail_completed_receipt)
    with pytest.raises(OSError, match="rollback receipt interrupted"):
        authoring_repair_rollback.rollback_failed_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
            workspace_root=workspace,
        )

    prepared = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert prepared["decision"] == "materialized_rollback_prepared"
    assert prepared["rollback"]["status"] == "pending"
    assert prepared["recovery_required"] is True
    assert not output.exists()
    (output.parent / ".materialization.lock").write_text(
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

    monkeypatch.setattr(repair_transaction, "atomic_write_json", original_atomic_write)
    recovered = authoring_repair_rollback.rollback_failed_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
    )

    assert recovered["decision"] == (
        "materialized_rolled_back_after_verification_failure"
    )
    assert recovered["rollback"]["status"] == "completed"
    assert recovered["recovery_required"] is False


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


def test_post_render_finalizer_rejects_receipt_drift_after_lock_acquisition(
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
    authorization_path = _authorization_artifact(receipt_path, authorization)
    original_lock = repair_transaction.recoverable_exclusive_lock

    @contextmanager
    def drift_after_lock(path: Path, *, owner: str):
        with original_lock(path, owner=owner):
            drifted = json.loads(receipt_path.read_text(encoding="utf-8"))
            drifted["change_summary"] = "racing finalizer changed the receipt"
            receipt_path.write_text(json.dumps(drifted), encoding="utf-8")
            yield

    monkeypatch.setattr(
        authoring_repair_finalize.repair_transaction,
        "recoverable_exclusive_lock",
        drift_after_lock,
    )
    with pytest.raises(
        authoring_repair_finalize.AuthoringRepairFinalizeError,
        match="receipt drifted during finalization",
    ):
        authoring_repair_finalize.finalize_materialized_candidate(
            packet_path=packet_path,
            receipt_path=receipt_path,
            authorization_path=authorization_path,
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
    original_lock = repair_transaction.recoverable_exclusive_lock

    @contextmanager
    def drift_after_lock(*args: object, **kwargs: object):
        with original_lock(*args, **kwargs):
            binding.write_bytes(binding.read_bytes() + b"\n")
            yield

    monkeypatch.setattr(
        repair_transaction,
        "recoverable_exclusive_lock",
        drift_after_lock,
    )

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


def test_closed_loop_machine_repair_plan_only_is_write_free(tmp_path: Path) -> None:
    workspace, state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    before = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    result = closed_loop_machine_repair.run_machine_repair(
        "demo",
        state_path=state_path,
        response_path=response_path,
        execute=False,
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )

    after = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert result["next_state"] == "machine_repaired"
    assert result["created"] is False
    assert result["decision"] == "planned_materialize_strict_verify"
    assert result["publication_acceptance"] == "not_claimed"
    assert not output.exists()
    assert not receipt.exists()
    assert after == before


def test_closed_loop_machine_repair_rejects_identical_response_path_substitution(
    tmp_path: Path,
) -> None:
    workspace, state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    substitute = response_path.with_name("equivalent-repair-response.json")
    substitute.write_text(
        json.dumps(json.loads(response_path.read_text(encoding="utf-8")), indent=2),
        encoding="utf-8",
    )

    with pytest.raises(
        closed_loop_machine_repair.ClosedLoopMachineRepairError,
        match="repair_response_state_binding_mismatch",
    ):
        closed_loop_machine_repair.run_machine_repair(
            "demo",
            state_path=state_path,
            response_path=substitute,
            execute=True,
            workspace_root=workspace,
            plugin_root=PLUGIN_ROOT,
        )

    assert not output.exists()
    assert not receipt.exists()


def test_fig_run_authorization_plan_only_is_hash_bound_and_write_free(
    tmp_path: Path,
) -> None:
    workspace, state_path, _response_path, authorization_path, output, receipt = (
        _repair_candidate_ready_attempt(tmp_path)
    )
    before = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="authorize the explicit repair",
        execute=False,
        closed_loop_state=state_path,
        closed_loop_authorization=authorization_path,
        repo_root=workspace,
    )

    after = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert payload["final_stop_reason"] == "plan_only"
    assert payload["closed_loop"]["input_state"] == "repair_candidate_ready"
    assert payload["closed_loop"]["next_state"] == "repair_authorized"
    assert payload["closed_loop"]["created"] is False
    assert payload["boundary_handoff"]["required_actor"] == "workflow_agent"
    assert payload["boundary_handoff"]["publication_acceptance"] == "not_claimed"
    assert not output.exists()
    assert not receipt.exists()
    assert after == before


def test_fig_run_authorization_execute_publishes_canonical_authorized_state(
    tmp_path: Path,
) -> None:
    workspace, state_path, _response_path, authorization_path, output, receipt = (
        _repair_candidate_ready_attempt(tmp_path)
    )

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="authorize the explicit repair",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_authorization=authorization_path,
        repo_root=workspace,
    )

    next_state_path = workspace / payload["closed_loop"]["next_state_path"]
    next_state = json.loads(next_state_path.read_text(encoding="utf-8"))
    projection = closed_loop_current_state.resolve_current_attempt(workspace, "demo")
    assert payload["final_stop_reason"] == "repair_authorized"
    assert payload["executed_count"] == 1
    assert next_state["state"] == "repair_authorized"
    assert next_state["actor"] == "named-reviewer"
    assert next_state["actor_role"] == "human_repair_authorizer"
    assert next_state["required_actor"] == "workflow_agent"
    assert next_state["publication_acceptance"] == "not_claimed"
    assert next_state["evidence"] == [
        {
            "role": "human_authorization",
            "path": authorization_path.relative_to(workspace).as_posix(),
            "sha256": _sha256(authorization_path.read_bytes()),
        }
    ]
    assert projection["path"] == next_state_path.relative_to(workspace).as_posix()
    assert projection["state_sha256"] == next_state["state_sha256"]
    assert not output.exists()
    assert not receipt.exists()


def test_default_fig_run_authorization_plan_binds_current_state_without_journal(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace, state_path, _response_path, authorization_path, output, receipt = (
        _repair_candidate_ready_attempt(tmp_path)
    )
    current = json.loads(state_path.read_text(encoding="utf-8"))
    runs_root = tmp_path / "runs"

    result = fig_run.main(
        [
            "demo",
            "--mode",
            "review",
            "--goal",
            "authorize the explicit repair",
            "--closed-loop-authorization",
            str(authorization_path),
            "--runs-root",
            str(runs_root),
            "--record",
            "--json",
        ],
        repo_root=workspace,
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["closed_loop"]["input_state_sha256"] == current["state_sha256"]
    assert payload["closed_loop"]["next_state"] == "repair_authorized"
    assert payload["closed_loop"]["created"] is False
    assert not runs_root.exists()
    assert not output.exists()
    assert not receipt.exists()


def test_fig_run_authorization_rejects_unbound_human_decision_without_writes(
    tmp_path: Path,
) -> None:
    workspace, state_path, _response_path, authorization_path, output, receipt = (
        _repair_candidate_ready_attempt(tmp_path)
    )
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    authorization["authorized_preview_sha256"] = "sha256:" + "0" * 64
    authorization_path.write_text(json.dumps(authorization), encoding="utf-8")

    with pytest.raises(ValueError, match="materialization_decision_preview_hash_mismatch"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="authorize the explicit repair",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_authorization=authorization_path,
            repo_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-repair_authorized.json"))
    assert not output.exists()
    assert not receipt.exists()


def test_fig_run_authorization_rejects_contradictory_human_decision_without_writes(
    tmp_path: Path,
) -> None:
    workspace, state_path, _response_path, authorization_path, output, receipt = (
        _repair_candidate_ready_attempt(tmp_path)
    )
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    authorization["human_decision"] = "reject this exact additive repair candidate"
    authorization_path.write_text(json.dumps(authorization), encoding="utf-8")

    with pytest.raises(ValueError, match="materialization_decision_not_approved"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="authorize the explicit repair",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_authorization=authorization_path,
            repo_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-repair_authorized.json"))
    assert not output.exists()
    assert not receipt.exists()


def test_fig_run_authorization_rejects_valid_input_replacement_under_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, _response_path, authorization_path, output, receipt = (
        _repair_candidate_ready_attempt(tmp_path)
    )
    original_lock = repair_transaction.recoverable_exclusive_lock

    @contextmanager
    def replace_after_lock(path: Path, *, owner: str):
        if path.name != closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK:
            with original_lock(path, owner=owner):
                yield
            return
        assert owner == closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK_OWNER
        with original_lock(path, owner=owner):
            authorization = json.loads(
                authorization_path.read_text(encoding="utf-8")
            )
            authorization["reviewer"] = "racing-reviewer"
            authorization_path.write_text(json.dumps(authorization), encoding="utf-8")
            yield

    monkeypatch.setattr(
        closed_loop_repair_authorization.repair_transaction,
        "recoverable_exclusive_lock",
        replace_after_lock,
    )
    with pytest.raises(ValueError, match="repair_authorization_inputs_drifted"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="authorize the explicit repair",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_authorization=authorization_path,
            repo_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-repair_authorized.json"))
    assert not output.exists()
    assert not receipt.exists()


def test_fig_run_authorization_rejects_input_drift_during_state_transition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, _response_path, authorization_path, output, receipt = (
        _repair_candidate_ready_attempt(tmp_path)
    )
    original_transition = closed_loop_attempt_state.transition_state

    def drift_after_transition(*args: object, **kwargs: object) -> dict[str, object]:
        next_state = original_transition(*args, **kwargs)
        authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
        authorization["reviewer"] = "racing-reviewer"
        authorization_path.write_text(json.dumps(authorization), encoding="utf-8")
        return next_state

    monkeypatch.setattr(
        closed_loop_repair_authorization.closed_loop_attempt_state,
        "transition_state",
        drift_after_transition,
    )
    with pytest.raises(ValueError, match="evidence_hash_stale"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="authorize the explicit repair",
            execute=True,
            closed_loop_state=state_path,
            closed_loop_authorization=authorization_path,
            repo_root=workspace,
        )

    assert not any(state_path.parent.glob("state-*-repair_authorized.json"))
    assert not output.exists()
    assert not receipt.exists()


def test_default_fig_run_never_discovers_adjacent_human_authorization(
    tmp_path: Path,
) -> None:
    workspace, state_path, _response_path, authorization_path, output, receipt = (
        _repair_candidate_ready_attempt(tmp_path)
    )
    assert authorization_path.is_file()

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="continue the lifecycle",
        execute=True,
        repo_root=workspace,
    )

    projection = closed_loop_current_state.resolve_current_attempt(workspace, "demo")
    assert payload["executed_count"] == 0
    assert payload["final_action"] == fig_run.fig_driver.ACTION_CLOSED_LOOP_HANDOFF_STOP
    assert payload["boundary_handoff"]["required_actor"] == "human_repair_authorizer"
    assert projection["state"] == "repair_candidate_ready"
    assert projection["path"] == state_path.relative_to(workspace).as_posix()
    assert not any(state_path.parent.glob("state-*-repair_authorized.json"))
    assert not output.exists()
    assert not receipt.exists()


def test_default_fig_run_chains_explicit_authorization_into_explicit_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, _state_path, response_path, authorization_path, output, receipt = (
        _repair_candidate_ready_attempt(tmp_path)
    )
    monkeypatch.setattr(
        fig_run,
        "REPO_ROOT",
        _fake_strict_compiler(tmp_path, expected_workspace=workspace),
    )

    authorized = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="authorize the explicit repair",
        execute=True,
        closed_loop_authorization=authorization_path,
        repo_root=workspace,
    )
    repaired = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="execute the explicit repair",
        execute=True,
        closed_loop_repair_response=response_path,
        repo_root=workspace,
    )

    assert authorized["closed_loop"]["next_state"] == "repair_authorized"
    assert repaired["closed_loop"]["input_state"] == "repair_authorized"
    assert repaired["closed_loop"]["next_state"] == "machine_repaired"
    assert repaired["closed_loop"]["publication_acceptance"] == "not_claimed"
    assert output.is_file()
    assert receipt.is_file()


def test_fig_run_authorization_recovers_already_published_matching_state(
    tmp_path: Path,
) -> None:
    workspace, state_path, _response_path, authorization_path, output, receipt = (
        _repair_candidate_ready_attempt(tmp_path)
    )
    created = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="authorize the explicit repair",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_authorization=authorization_path,
        repo_root=workspace,
    )

    recovered = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="authorize the explicit repair",
        execute=True,
        closed_loop_state=state_path,
        closed_loop_authorization=authorization_path,
        repo_root=workspace,
    )
    planned_recovery = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="inspect the explicit repair authorization",
        execute=False,
        closed_loop_state=state_path,
        closed_loop_authorization=authorization_path,
        repo_root=workspace,
    )

    assert recovered["final_stop_reason"] == "repair_authorized_recovered"
    assert recovered["executed_count"] == 0
    assert recovered["closed_loop"]["created"] is False
    assert recovered["closed_loop"]["next_state_path"] == (
        created["closed_loop"]["next_state_path"]
    )
    assert recovered["boundary_handoff"]["evidence_refs"][-1] == (
        "closed_loop_state:" + created["closed_loop"]["next_state_path"]
    )
    assert planned_recovery["final_stop_reason"] == "repair_authorized_recovered"
    assert planned_recovery["boundary_handoff"]["blocking_reason"] == (
        "continue from the authorized repair candidate"
    )
    assert len(list(state_path.parent.glob("state-*-repair_authorized.json"))) == 1
    assert not output.exists()
    assert not receipt.exists()


def test_closed_loop_machine_repair_executes_existing_verified_chain(
    tmp_path: Path,
) -> None:
    workspace, state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    plugin_root = _fake_strict_compiler(
        tmp_path,
        expected_workspace=workspace,
    )

    result = closed_loop_machine_repair.run_machine_repair(
        "demo",
        state_path=state_path,
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
        plugin_root=plugin_root,
    )

    published = json.loads(result["next_state_path"].read_text(encoding="utf-8"))
    finalized = json.loads(receipt.read_text(encoding="utf-8"))
    assert output.is_file()
    assert finalized["decision"] == (
        "materialized_machine_verified_human_review_pending"
    )
    assert finalized["repair_response"] == {
        "path": response_path.relative_to(workspace).as_posix(),
        "sha256": _sha256(response_path.read_bytes()),
        "payload": json.loads(response_path.read_text(encoding="utf-8")),
    }
    assert finalized["publication_acceptance"] == "not_claimed"
    assert published["state"] == "machine_repaired"
    assert {record["role"] for record in published["evidence"]} == {
        "materialization_receipt",
        "machine_verification_receipt",
    }
    assert result["publication_acceptance"] == "not_claimed"


def test_closed_loop_machine_repair_failed_verification_rolls_back(
    tmp_path: Path,
) -> None:
    workspace, state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    plugin_root = _fake_strict_compiler(
        tmp_path,
        state="failed",
        returncode=1,
        expected_workspace=workspace,
    )

    result = closed_loop_machine_repair.run_machine_repair(
        "demo",
        state_path=state_path,
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
        plugin_root=plugin_root,
    )

    published = json.loads(result["next_state_path"].read_text(encoding="utf-8"))
    rolled_back = json.loads(receipt.read_text(encoding="utf-8"))
    assert not output.exists()
    assert rolled_back["decision"] == (
        "materialized_rolled_back_after_verification_failure"
    )
    assert rolled_back["repair_response"] == {
        "path": response_path.relative_to(workspace).as_posix(),
        "sha256": _sha256(response_path.read_bytes()),
        "payload": json.loads(response_path.read_text(encoding="utf-8")),
    }
    assert rolled_back["publication_acceptance"] == "not_claimed"
    assert published["state"] == "repair_required"
    assert result["stop_boundary"] == "repair_required"
    assert result["publication_acceptance"] == "not_claimed"


def test_fig_run_explicit_repair_response_uses_current_authorized_state(
    tmp_path: Path,
) -> None:
    workspace, state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    before = {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="continue repair",
        execute=False,
        closed_loop_repair_response=response_path,
        repo_root=workspace,
    )

    assert payload["final_action"] == "authoring_repair_materialize_and_verify"
    assert payload["closed_loop"]["input_state"] == "repair_authorized"
    assert payload["closed_loop"]["input_state_path"] == state_path.relative_to(
        workspace
    ).as_posix()
    assert payload["closed_loop"]["next_state"] == "machine_repaired"
    assert payload["closed_loop"]["publication_acceptance"] == "not_claimed"
    assert not output.exists()
    assert not receipt.exists()
    assert {
        path.relative_to(workspace): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    } == before


def test_fig_run_repair_response_execute_reaches_machine_repaired(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, _state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    monkeypatch.setattr(
        fig_run,
        "REPO_ROOT",
        _fake_strict_compiler(tmp_path, expected_workspace=workspace),
    )
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda *_args, **_kwargs: pytest.fail(
            "repair response consumption must not invoke the legacy runner or host"
        ),
    )

    payload = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="continue repair",
        execute=True,
        closed_loop_repair_response=response_path,
        repo_root=workspace,
    )

    next_state = json.loads(
        (workspace / payload["closed_loop"]["next_state_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert output.is_file()
    assert receipt.is_file()
    assert next_state["state"] == "machine_repaired"
    assert payload["final_stop_reason"] == "machine_repaired"
    assert payload["boundary_handoff"]["required_actor"] == "workflow_agent"
    assert payload["boundary_handoff"]["publication_acceptance"] == "not_claimed"


def test_fig_run_repair_and_review_responses_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="continue repair",
            closed_loop_response=Path("review-response.json"),
            closed_loop_repair_response=Path("repair-response.json"),
        )


def test_fig_run_repair_response_rejects_projected_hash_drift_without_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, _state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    summary = fig_run._driver_summary(
        "demo",
        mode="review",
        goal="continue repair",
        repo_root=workspace,
    )
    assert summary["closed_loop_attempt"]["state"] == "repair_authorized"
    summary["closed_loop_attempt"]["state_sha256"] = "sha256:" + "0" * 64
    monkeypatch.setattr(fig_run, "_driver_summary", lambda *_args, **_kwargs: summary)

    with pytest.raises(ValueError, match="projected_state_hash_mismatch"):
        fig_run.run_workflow(
            "demo",
            mode="review",
            goal="continue repair",
            execute=True,
            closed_loop_repair_response=response_path,
            repo_root=workspace,
        )

    assert not output.exists()
    assert not receipt.exists()


def test_closed_loop_machine_repair_rechecks_current_state_under_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    original_lock = repair_transaction.recoverable_exclusive_lock

    @contextmanager
    def superseding_lock(path: Path, *, owner: str):
        if path.name != closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK:
            with original_lock(path, owner=owner):
                yield
            return
        assert owner == closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK_OWNER
        current = json.loads(state_path.read_text(encoding="utf-8"))
        terminal = closed_loop_attempt_state.transition_state(
            current,
            next_state="repair_required",
            actor="racing-agent",
            actor_role="workflow_agent",
            evidence={"repair_failure_record": response_path},
            workspace_root=workspace,
            previous_state_path=state_path,
        )
        closed_loop_attempt_state.publish_state(
            terminal,
            workspace_root=workspace,
        )
        yield

    monkeypatch.setattr(
        closed_loop_machine_repair.repair_transaction,
        "recoverable_exclusive_lock",
        superseding_lock,
    )
    with pytest.raises(
        closed_loop_machine_repair.ClosedLoopMachineRepairError,
        match="canonical_current_state_drift",
    ):
        closed_loop_machine_repair.run_machine_repair(
            "demo",
            state_path=state_path,
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
            plugin_root=PLUGIN_ROOT,
        )

    assert not output.exists()
    assert not receipt.exists()


def test_fig_run_repair_response_cli_plan_never_records(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace, _state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    runs_root = tmp_path / "runs"

    result = fig_run.main(
        [
            "demo",
            "--mode",
            "review",
            "--goal",
            "continue repair",
            "--closed-loop-repair-response",
            str(response_path),
            "--runs-root",
            str(runs_root),
            "--record",
            "--json",
        ],
        repo_root=workspace,
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["closed_loop"]["created"] is False
    assert not runs_root.exists()
    assert not output.exists()
    assert not receipt.exists()


def test_closed_loop_machine_repair_recovers_verified_receipt_after_state_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    original_publish = closed_loop_attempt_state.publish_state
    failed = False

    def fail_machine_state_once(
        state: dict[str, object], *, workspace_root: Path
    ) -> Path:
        nonlocal failed
        if state.get("state") == "machine_repaired" and not failed:
            failed = True
            raise closed_loop_attempt_state.ClosedLoopAttemptStateError(
                "injected_machine_state_failure"
            )
        return original_publish(state, workspace_root=workspace_root)

    monkeypatch.setattr(
        closed_loop_attempt_state,
        "publish_state",
        fail_machine_state_once,
    )
    with pytest.raises(
        closed_loop_machine_repair.ClosedLoopMachineRepairError,
        match="injected_machine_state_failure",
    ):
        closed_loop_machine_repair.run_machine_repair(
            "demo",
            state_path=state_path,
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(tmp_path),
        )
    assert output.is_file()
    assert json.loads(receipt.read_text(encoding="utf-8"))["recovery_required"] is False

    projected = fig_run.run_workflow(
        "demo",
        mode="review",
        goal="continue repair",
        execute=False,
        closed_loop_state=state_path,
        closed_loop_repair_response=response_path,
        repo_root=workspace,
    )
    input_state_ref = f"closed_loop_state:{state_path.relative_to(workspace).as_posix()}"
    projected_state_ref = (
        "closed_loop_state:"
        + projected["closed_loop"]["next_state_path"]
    )
    assert input_state_ref in projected["boundary_handoff"]["evidence_refs"]
    assert projected_state_ref not in projected["boundary_handoff"]["evidence_refs"]

    (receipt.parent / ".materialization.lock").write_text(
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

    recovered = closed_loop_machine_repair.run_machine_repair(
        "demo",
        state_path=state_path,
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
        plugin_root=tmp_path / "missing-plugin",
    )

    assert recovered["next_state"] == "machine_repaired"
    assert recovered["stop_reason"] == "machine_repaired_recovered"
    assert recovered["created"] is True


def test_closed_loop_machine_repair_recovers_rollback_after_state_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    original_publish = closed_loop_attempt_state.publish_state
    failed = False

    def fail_repair_required_once(
        state: dict[str, object], *, workspace_root: Path
    ) -> Path:
        nonlocal failed
        if state.get("state") == "repair_required" and not failed:
            failed = True
            raise closed_loop_attempt_state.ClosedLoopAttemptStateError(
                "injected_repair_required_state_failure"
            )
        return original_publish(state, workspace_root=workspace_root)

    monkeypatch.setattr(
        closed_loop_attempt_state,
        "publish_state",
        fail_repair_required_once,
    )
    with pytest.raises(
        closed_loop_machine_repair.ClosedLoopMachineRepairError,
        match="injected_repair_required_state_failure",
    ):
        closed_loop_machine_repair.run_machine_repair(
            "demo",
            state_path=state_path,
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(
                tmp_path,
                state="failed",
                returncode=1,
            ),
        )
    assert not output.exists()
    assert json.loads(receipt.read_text(encoding="utf-8"))["recovery_required"] is False

    (receipt.parent / ".materialization.lock").write_text(
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

    plan = closed_loop_machine_repair.run_machine_repair(
        "demo",
        state_path=state_path,
        response_path=response_path,
        execute=False,
        workspace_root=workspace,
        plugin_root=tmp_path / "missing-plugin",
    )
    assert plan["next_state"] == "repair_required"
    assert plan["required_actor"] == "workflow_agent"

    recovered = closed_loop_machine_repair.run_machine_repair(
        "demo",
        state_path=state_path,
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
        plugin_root=tmp_path / "missing-plugin",
    )

    assert recovered["next_state"] == "repair_required"
    assert recovered["stop_reason"] == "repair_required_recovered"
    assert recovered["created"] is True


@pytest.mark.parametrize("strict_failure", [False, True])
def test_closed_loop_machine_repair_rejects_receipt_mutation_before_transition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    strict_failure: bool,
) -> None:
    workspace, state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    original_publish_result = closed_loop_machine_repair._publish_result_state

    def mutate_before_transition(*args: object, **kwargs: object):
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        payload["repair_response"]["payload"]["change_summary"] = "tampered"
        repair_transaction.atomic_write_json(receipt, payload)
        return original_publish_result(*args, **kwargs)

    monkeypatch.setattr(
        closed_loop_machine_repair,
        "_publish_result_state",
        mutate_before_transition,
    )
    plugin_root = _fake_strict_compiler(
        tmp_path,
        state="failed" if strict_failure else "passed",
        returncode=1 if strict_failure else 0,
    )

    with pytest.raises(
        closed_loop_machine_repair.ClosedLoopMachineRepairError,
        match="terminal_receipt_changed_during_transition",
    ):
        closed_loop_machine_repair.run_machine_repair(
            "demo",
            state_path=state_path,
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
            plugin_root=plugin_root,
        )

    assert not any(state_path.parent.glob("state-*-machine_repaired.json"))
    assert not any(state_path.parent.glob("state-*-repair_required.json"))
    assert output.exists() is (not strict_failure)


def test_closed_loop_machine_repair_recovery_rejects_mutation_before_transition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, response_path, _output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    original_publish_state = closed_loop_attempt_state.publish_state

    def fail_machine_state(
        state: dict[str, object], *, workspace_root: Path
    ) -> Path:
        if state.get("state") == "machine_repaired":
            raise closed_loop_attempt_state.ClosedLoopAttemptStateError(
                "injected_machine_state_failure"
            )
        return original_publish_state(state, workspace_root=workspace_root)

    monkeypatch.setattr(closed_loop_attempt_state, "publish_state", fail_machine_state)
    with pytest.raises(closed_loop_machine_repair.ClosedLoopMachineRepairError):
        closed_loop_machine_repair.run_machine_repair(
            "demo",
            state_path=state_path,
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(tmp_path),
        )
    monkeypatch.setattr(
        closed_loop_attempt_state,
        "publish_state",
        original_publish_state,
    )
    original_publish_result = closed_loop_machine_repair._publish_result_state

    def mutate_before_transition(*args: object, **kwargs: object):
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        payload["repair_response"]["sha256"] = "sha256:" + "0" * 64
        repair_transaction.atomic_write_json(receipt, payload)
        return original_publish_result(*args, **kwargs)

    monkeypatch.setattr(
        closed_loop_machine_repair,
        "_publish_result_state",
        mutate_before_transition,
    )

    with pytest.raises(
        closed_loop_machine_repair.ClosedLoopMachineRepairError,
        match="terminal_receipt_changed_during_transition",
    ):
        closed_loop_machine_repair.run_machine_repair(
            "demo",
            state_path=state_path,
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
            plugin_root=tmp_path / "missing-plugin",
        )
    assert not any(state_path.parent.glob("state-*-machine_repaired.json"))


def test_closed_loop_machine_repair_resumes_prepared_finalize(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    original_run = authoring_repair_finalize.subprocess.run
    monkeypatch.setattr(
        authoring_repair_finalize.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("injected crash")),
    )
    with pytest.raises(
        closed_loop_machine_repair.ClosedLoopMachineRepairError,
        match="injected crash",
    ):
        closed_loop_machine_repair.run_machine_repair(
            "demo",
            state_path=state_path,
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(tmp_path),
        )
    prepared = json.loads(receipt.read_text(encoding="utf-8"))
    assert prepared["decision"] == "materialized_verification_prepared"
    assert prepared["recovery_required"] is True
    monkeypatch.setattr(authoring_repair_finalize.subprocess, "run", original_run)
    (
        state_path.parent / closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK
    ).write_text(
        json.dumps(
            {
                "schema": "figure-agent.recoverable-lock.v1",
                "owner": closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK_OWNER,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    (receipt.parent / ".materialization.lock").write_text(
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

    plan = closed_loop_machine_repair.run_machine_repair(
        "demo",
        state_path=state_path,
        response_path=response_path,
        execute=False,
        workspace_root=workspace,
        plugin_root=tmp_path / "missing-plugin",
    )
    assert plan["next_state"] == "machine_repaired"
    assert plan["required_actor"] == "workflow_agent"

    recovered = closed_loop_machine_repair.run_machine_repair(
        "demo",
        state_path=state_path,
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
        plugin_root=_fake_strict_compiler(tmp_path / "retry"),
    )

    assert output.is_file()
    assert recovered["next_state"] == "machine_repaired"


def test_closed_loop_machine_repair_resumes_prepared_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, state_path, response_path, output, receipt = (
        _repair_authorized_attempt(tmp_path)
    )
    original_unlink = authoring_repair_rollback._unlink_hash_bound_output
    monkeypatch.setattr(
        authoring_repair_rollback,
        "_unlink_hash_bound_output",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("injected crash")),
    )
    with pytest.raises(
        closed_loop_machine_repair.ClosedLoopMachineRepairError,
        match="injected crash",
    ):
        closed_loop_machine_repair.run_machine_repair(
            "demo",
            state_path=state_path,
            response_path=response_path,
            execute=True,
            workspace_root=workspace,
            plugin_root=_fake_strict_compiler(
                tmp_path,
                state="failed",
                returncode=1,
            ),
        )
    prepared = json.loads(receipt.read_text(encoding="utf-8"))
    assert prepared["decision"] == authoring_repair_rollback.PREPARED_DECISION
    assert prepared["recovery_required"] is True
    monkeypatch.setattr(
        authoring_repair_rollback,
        "_unlink_hash_bound_output",
        original_unlink,
    )
    (
        state_path.parent / closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK
    ).write_text(
        json.dumps(
            {
                "schema": "figure-agent.recoverable-lock.v1",
                "owner": closed_loop_attempt_state.ATTEMPT_TRANSITION_LOCK_OWNER,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    (receipt.parent / ".materialization.lock").write_text(
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

    plan = closed_loop_machine_repair.run_machine_repair(
        "demo",
        state_path=state_path,
        response_path=response_path,
        execute=False,
        workspace_root=workspace,
        plugin_root=tmp_path / "missing-plugin",
    )
    assert plan["next_state"] == "repair_required"
    assert plan["required_actor"] == "workflow_agent"

    recovered = closed_loop_machine_repair.run_machine_repair(
        "demo",
        state_path=state_path,
        response_path=response_path,
        execute=True,
        workspace_root=workspace,
        plugin_root=tmp_path / "missing-plugin",
    )

    assert not output.exists()
    assert recovered["next_state"] == "repair_required"
