from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig3_trap_schematic_slice3_semantic"
PACKET = FIXTURE / "review" / "failure-first-ablation" / "input_packet.yaml"


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

