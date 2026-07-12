from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig3_trap_schematic_slice3_semantic"
PACKET = FIXTURE / "review" / "failure-first-ablation" / "input_packet.yaml"
RAW_RUN = FIXTURE / "review" / "failure-first-ablation" / "raw" / "raw.yaml"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_fig3_failure_first_packet_binds_authority_inputs_without_fig1_dependency() -> None:
    packet = yaml.safe_load(PACKET.read_text(encoding="utf-8"))

    assert packet["schema"] == "figure-agent.failure-first-input-packet.v1"
    assert packet["fixture"] == "fig3_trap_schematic_slice3_semantic"
    assert packet["generation_status"] == "not_run"
    assert packet["panels"] == ["a", "b", "c", "d", "e", "f"]
    assert packet["forbidden_import_patterns"] == [
        "examples/fig1_",
        "experiments/python_svg_semantic_fig1",
        "fig1_hybrid_complex_panel_pilot",
    ]

    roles = {item["role"] for item in packet["authoritative_inputs"]}
    assert roles == {
        "reference",
        "briefing",
        "specification",
        "coordinate_hints",
        "editable_source",
        "review_history",
        "semantic_regions",
    }
    for item in packet["authoritative_inputs"]:
        path = FIXTURE / item["path"]
        assert path.is_file()
        assert item["sha256"] == _sha256(path)


def test_fig3_raw_authoring_run_is_hash_bound_and_fig1_independent() -> None:
    run = yaml.safe_load(RAW_RUN.read_text(encoding="utf-8"))
    receipt = run["generation_receipt"]
    run_dir = RAW_RUN.parent

    assert run["variant"] == "raw"
    assert run["input_packet_hash"] == _sha256(PACKET)
    assert run["budget_contract_hash"] == _sha256(
        FIXTURE / "review" / "failure-first-ablation" / "contracts" / "budget_contract.yaml"
    )
    for kind in ("starting", "generated"):
        artifact = run_dir / receipt[f"{kind}_artifact_path"]
        assert artifact.is_file()
        assert receipt[f"{kind}_artifact_sha256"] == _sha256(artifact)
    transcript = run_dir / receipt["transcript_path"]
    assert receipt["transcript_sha256"] == _sha256(transcript)
    assert json.loads(transcript.read_text(encoding="utf-8"))["model_id"] == "codex-gpt-5.5"
    generated = (run_dir / receipt["generated_artifact_path"]).read_text(encoding="utf-8")
    assert "examples/fig1_" not in generated
    assert "fig1_hybrid_complex_panel_pilot" not in generated
