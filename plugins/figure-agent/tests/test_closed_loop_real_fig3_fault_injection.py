from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import authoring_repair_finalize
import authoring_repair_packet
import authoring_repair_rollback
import critique_repair_bridge
import critique_zoom_crops
import pytest
import yaml
from inputs import parse_spec
from quality_manifest import (
    compute_critique_input_hash,
    critique_generator_version,
    expected_critique_rubric_version,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REAL_FIXTURE = PLUGIN_ROOT / "examples" / "fig3_resistance_mechanism"
FIXTURE = "fig3_resistance_mechanism"
TARGET_TEXTS = {"R3TARGET", "R3FAULT"}
REGRESSION_TEXTS = {"R3NEIGHBOR", "R3REGRESSION"}


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _compile(source: Path, *, workspace: Path, strict: bool) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("FIGURE_AGENT_STRICT", None)
    env["FIGURE_AGENT_FIXTURE_NAME"] = FIXTURE
    env["FIGURE_AGENT_LIVE_REPAIR_VERIFY"] = "1"
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    if strict:
        env["FIGURE_AGENT_STRICT"] = "1"
    return subprocess.run(
        ["bash", str(PLUGIN_ROOT / "scripts" / "compile.sh"), str(source)],
        cwd=PLUGIN_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _matching_collision(report: dict[str, object], texts: set[str]) -> dict[str, object]:
    matches = [
        item
        for item in report.get("collisions", [])
        if isinstance(item, dict) and texts <= set(item.get("texts", []))
    ]
    assert len(matches) == 1, report
    return matches[0]


def _authorization(
    packet: dict[str, object], preview: dict[str, object]
) -> dict[str, object]:
    packet_path = (
        f"examples/{FIXTURE}/review/failure-first/execution-repair-v1/"
        "repair_packet.json"
    )
    return {
        "schema": "figure-agent.human-decision-record.v1",
        "fixture": FIXTURE,
        "packet_schema": packet["schema"],
        "packet_path": packet_path,
        "packet_recommendation": "materialize_authoring_repair_candidate",
        "queue_run_id": "r3-real-fig3-controlled-fault-001",
        "decision_kind": "materialize_authoring_repair_candidate",
        "agent_recommendation": "Exercise the bounded regression gate only.",
        "human_decision": "Authorize additive controlled-fault materialization.",
        "human_note": "This does not accept the figure or publication quality.",
        "follow_up": {"implementation_slice": "R3 controlled-fault rollback proof"},
        "mutation_boundary": "additive_artifact_materialization_allowed",
        "reviewer": "test-r3-controller",
        "authorized_packet_sha256": packet["packet_sha256"],
        "authorized_output_path": packet["output_path"],
        "authorized_output_sha256": preview["output_sha256"],
        "authorized_preview_sha256": preview["preview_sha256"],
    }


@pytest.mark.render
def test_current_v4_rejects_and_rolls_back_real_fig3_neighbor_regression(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    example = workspace / "examples" / FIXTURE
    example.mkdir(parents=True)
    for name in (
        "spec.yaml",
        "briefing.md",
        "authoring_contract.md",
        "authoring_plan.md",
        "layout_lanes.yaml",
    ):
        shutil.copy2(REAL_FIXTURE / name, example / name)

    original = (REAL_FIXTURE / f"{FIXTURE}.tex").read_text(encoding="utf-8")
    fault_block = (
        "  % r3-controlled-fault:start\n"
        "  \\node[label] at (7.20,0.55) {R3TARGET};\n"
        "  \\node[label] at (7.20,0.55) {R3FAULT};\n"
        "  % r3-controlled-fault:end\n"
    )
    faulted = original.replace("\\end{tikzpicture}", fault_block + "\\end{tikzpicture}")
    assert faulted.count("r3-controlled-fault:start") == 1
    live_source = example / f"{FIXTURE}.tex"
    live_source.write_text(faulted, encoding="utf-8")
    binding_source = (
        example
        / "review/failure-first/execution-binding-v1/treatment_generated.tex"
    )
    binding_source.parent.mkdir(parents=True)
    binding_source.write_text(faulted, encoding="utf-8")

    baseline_compile = _compile(live_source, workspace=workspace, strict=False)
    assert baseline_compile.returncode == 0, baseline_compile.stderr
    build = example / "build"
    before_report = json.loads((build / "collisions.json").read_text(encoding="utf-8"))
    target = _matching_collision(before_report, TARGET_TEXTS)
    critique_zoom_crops.build_zoom_crop_pack(
        example,
        build / f"{FIXTURE}.png",
        panel_crop_paths=(),
    )

    attempt = example / "review/failure-first/execution-repair-v1"
    attempt.mkdir()
    report_path = attempt / "collisions.before.json"
    report_path.write_bytes((build / "collisions.json").read_bytes())
    semantic_contract = attempt / "semantic_contract.yaml"
    semantic_contract.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.failure-first-semantic-contract.v1",
                "required_objects": [
                    "controlled_target_label",
                    "controlled_fault_label",
                    "declared_neighbor_label",
                    "declared_regression_label",
                ],
                "protected_relations": [
                    "controlled_pair_separation_restored",
                    "declared_neighbor_remains_clear_of_regression",
                ],
                "semantic_legibility": {
                    "object_roles": [
                        {
                            "object_id": "controlled_target_label",
                            "declared_role": "fault_injection_target",
                            "forbidden_readings": [],
                        },
                        {
                            "object_id": "controlled_fault_label",
                            "declared_role": "fault_injection_counterpart",
                            "forbidden_readings": [],
                        },
                        {
                            "object_id": "declared_neighbor_label",
                            "declared_role": "neighbor_regression_guard",
                            "forbidden_readings": [],
                        },
                        {
                            "object_id": "declared_regression_label",
                            "declared_role": "neighbor_regression_probe",
                            "forbidden_readings": [],
                        },
                    ],
                    "visible_connectors": [],
                    "forbidden_connectors": [],
                    "label_ownership": [],
                },
                "publication_acceptance": "not_claimed",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    registry = attempt / "source_selectors.json"
    registry.write_text(
        json.dumps(
            {
                "schema": "figure-agent.source-selector-registry.v1",
                "source_path": binding_source.relative_to(workspace).as_posix(),
                "source_sha256": _sha256(binding_source),
                "semantic_contract": {
                    "path": semantic_contract.relative_to(workspace).as_posix(),
                    "sha256": _sha256(semantic_contract),
                },
                "selectors": [
                    {
                        "selector_id": "r3-controlled-target",
                        "anchor_start": "  % r3-controlled-fault:start",
                        "anchor_end": "  % r3-controlled-fault:end",
                        "rendered_aliases": sorted(TARGET_TEXTS),
                        "repair_role": "movable",
                        "repair_family": "label_reflow",
                        "protected_invariants": ["S80"],
                        "semantic_object_refs": [
                            "controlled_target_label",
                            "controlled_fault_label",
                            "declared_neighbor_label",
                            "declared_regression_label",
                        ],
                        "semantic_relation_refs": [
                            "controlled_pair_separation_restored",
                            "declared_neighbor_remains_clear_of_regression",
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    spec = parse_spec((example / "spec.yaml").read_text(encoding="utf-8"))
    real_critique_text = (REAL_FIXTURE / "critique.md").read_text(encoding="utf-8")
    critique_metadata = yaml.safe_load(real_critique_text.split("---", 2)[1])
    critique_metadata.update(
        {
            "fixture": FIXTURE,
            "generated_at": "2026-07-15T00:00:00Z",
            "generator_version": critique_generator_version(
                PLUGIN_ROOT / "scripts" / "critique_brief.py"
            ),
            "rubric_version": expected_critique_rubric_version(example),
            "critique_input_hash": compute_critique_input_hash(
                example,
                FIXTURE,
                spec,
                style_lock_path=PLUGIN_ROOT / "styles/polymer-paper-preamble.sty",
                base_dir=PLUGIN_ROOT,
            ),
            "verdict": "revise",
            "findings": [
                {
                    "id": "C001",
                    "severity": "MAJOR",
                    "category": "label_placement",
                    "tex_lines": [],
                    "grounded_in_rule": "R3 controlled-fault regression contract",
                    "observation": "Controlled target labels overlap in the live render.",
                    "suggested_fix": "Change only the declared fault-injection block.",
                }
            ],
        }
    )
    for check in critique_metadata["audit_enumeration"]["physical_plausibility"]:
        if check.get("check") == "spatial_proximity":
            check["finding"] = "Live detector confirms the controlled target collision."
            check["verdict"] = "issue"
    critique_metadata["quality_axes"]["composition_layout"].update(
        {
            "verdict": "needs_patch",
            "confidence": "high",
            "rationale": "The controlled target labels overlap.",
            "blocking_items": ["C001"],
            "recommended_action": "patch",
        }
    )
    for slot in ("target_journal_fit", "aesthetic_coherence"):
        critique_metadata["top_tier_audit"][slot].update(
            {
                "verdict": "pass",
                "concrete_fix": "accept_simplification",
                "blocks_high_impact": False,
            }
        )
    for item in critique_metadata["editorial_art_direction"].values():
        item.update(
            {
                "verdict": "pass",
                "concrete_fix": "accept_simplification",
                "blocks_high_impact": False,
            }
        )
    critique = example / "critique.md"
    critique.write_text(
        "---\n" + yaml.safe_dump(critique_metadata, sort_keys=False) + "---\n",
        encoding="utf-8",
    )
    adjudication = example / "critique_adjudication.yaml"
    adjudication.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.critique-adjudication.v1",
                "fixture": FIXTURE,
                "source_critique_hash": _sha256(critique),
                "decisions": [
                    {
                        "finding_id": "C001",
                        "decision": "apply",
                        "reason": "Exercise the real-source regression gate.",
                        "patch_target": "controlled fault block",
                        "evidence": "live detector collision",
                        "repair_evidence": {
                            "report_path": report_path.relative_to(workspace).as_posix(),
                            "finding_id": target["id"],
                            "selector_registry_path": registry.relative_to(
                                workspace
                            ).as_posix(),
                        },
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    critique_repair_bridge.build_adjudicated_repair_target(
        example_dir=example,
        critique_finding_id="C001",
        attempt_dir=attempt,
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )
    packet, _prompt = authoring_repair_packet.compile_adjudicated_repair_execution_packet(
        FIXTURE,
        workspace_root=workspace,
        model_id="gpt-5.5",
        binding_path=(attempt / "critique_repair_binding.json")
        .relative_to(workspace)
        .as_posix(),
        output_path=(attempt / "repaired_generated.tex").relative_to(workspace).as_posix(),
    )
    packet_path = attempt / "repair_packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    response = {
        "replacement_utf8": (
            "  \\node[label] at (5.80,0.30) {R3TARGET};\n"
            "  \\node[label] at (8.60,0.30) {R3FAULT};\n"
            "  \\node[label] at (7.20,0.55) {R3NEIGHBOR};\n"
            "  \\node[label] at (7.20,0.55) {R3REGRESSION};"
        ),
        "change_summary": (
            "Separate the declared controlled target pair while introducing a "
            "declared neighbor-regression collision."
        ),
    }
    preview = authoring_repair_packet.materialize_repair_candidate(
        packet, response, workspace_root=workspace, apply=False
    )
    authorization = _authorization(packet, preview)
    authorization_path = attempt / "materialization_authorization.json"
    authorization_path.write_text(json.dumps(authorization), encoding="utf-8")
    receipt_path = attempt / "materialization_receipt.json"
    authoring_repair_packet.materialize_repair_candidate(
        packet,
        response,
        workspace_root=workspace,
        authorization=authorization,
        receipt_path=receipt_path,
    )

    failed = authoring_repair_finalize.finalize_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )
    after_report_path = attempt / "build/collisions.json"
    after_report = json.loads(after_report_path.read_text(encoding="utf-8"))
    _matching_collision(after_report, REGRESSION_TEXTS)
    assert all(
        not TARGET_TEXTS.intersection(item.get("texts", []))
        for item in after_report["collisions"]
    )
    assert failed["decision"] == "materialized_verification_failed"
    assert failed["external_compile"]["failure_reason"] == "strict_compile_nonzero"
    assert failed["publication_acceptance"] == "not_claimed"

    rolled_back = authoring_repair_rollback.rollback_failed_materialized_candidate(
        packet_path=packet_path,
        receipt_path=receipt_path,
        authorization_path=authorization_path,
        workspace_root=workspace,
    )

    assert not (attempt / "repaired_generated.tex").exists()
    assert report_path.is_file()
    assert after_report_path.is_file()
    assert rolled_back["rollback"]["status"] == "completed"
    assert rolled_back["publication_acceptance"] == "not_claimed"
