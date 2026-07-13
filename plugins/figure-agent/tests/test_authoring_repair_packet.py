from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import authoring_repair_packet
import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


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

    receipt = authoring_repair_packet.materialize_repair_candidate(
        packet,
        {
            "replacement_utf8": replacement,
            "change_summary": "Lower the colliding label.",
        },
        workspace_root=workspace,
    )

    output = workspace / packet["output_path"]
    candidate = source.read_text(encoding="utf-8").replace(
        r"\node {repeated dispersive trapping};", replacement
    )
    assert output.read_text(encoding="utf-8") == candidate
    assert receipt["decision"] == "materialized_verification_pending"
    assert receipt["changed_source_blocks"] == 1
    assert receipt["changed_lines"] == 2
    assert receipt["publication_acceptance"] == "not_claimed"


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
