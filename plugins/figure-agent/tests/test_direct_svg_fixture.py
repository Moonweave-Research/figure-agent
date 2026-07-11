from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml
from direct_svg_candidate import (
    begin_ledger,
    record_iteration,
    semantic_requirements,
    validate_candidate_from_semantic_packet,
)
from direct_svg_packet import validate_packet

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig1_direct_svg_cleanroom_baseline"
DENIED_SOURCE_FAMILIES = {
    "tex",
    "whole_figure_svg",
    "candidate_patch",
    "experience_log",
    "illustration_grammar",
}
EXPECTED_BUDGETS = {
    "utility": {"cycles": 3, "wall_minutes_per_panel": 30},
    "ceiling": {"cycles": 8, "wall_minutes_per_panel": 120},
}


def _load(relative: str) -> dict[str, Any]:
    loaded = yaml.safe_load((FIXTURE / relative).read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def test_fixture_binds_immutable_reference_source_and_crops() -> None:
    receipt = _load("reference/source-receipt.yaml")
    crop_manifest = _load("reference/crop-authority.yaml")

    benchmark = FIXTURE / "reference" / receipt["snapshot"]["path"]
    assert receipt["source"]["sha256"] == receipt["snapshot"]["sha256"]
    assert receipt["snapshot"]["sha256"] == _sha256(benchmark)
    assert crop_manifest["source"]["sha256"] == _sha256(benchmark)
    for crop in crop_manifest["crops"].values():
        assert crop["sha256"] == _sha256(FIXTURE / "reference" / crop["output"])
    assert receipt["publication_acceptance"] == "not_claimed"
    assert crop_manifest["publication_acceptance"] == "not_claimed"


def test_fixture_binds_independently_prepared_semantic_packet() -> None:
    state = _load("contract/experiment-state.yaml")
    semantic = _load("contract/semantic-packet.yaml")
    semantic_path = FIXTURE / "contract" / "semantic-packet.yaml"
    receipt = _load("contract/semantic-packet-preparation-receipt.yaml")
    receipt_path = FIXTURE / "contract" / "semantic-packet-preparation-receipt.yaml"

    assert semantic["schema"] == "figure-agent.direct-svg-semantic-packet.v1"
    assert semantic["panels"] == ["C", "F"]
    assert semantic["authority"]["named_preparer"] == "codex-task:/root/semantic_packet"
    assert semantic["authority"]["prepared_at"].endswith("Z")
    assert semantic["authority"]["source_authority_hashes"] == {
        "examples/fig1_hybrid_complex_panel_pilot/briefing.md": (
            "sha256:1ef22509309ccb0f5404b74552da3f5a6e322ce24e9ec716a68fac1d210c7273"
        ),
        "examples/fig1_hybrid_complex_panel_pilot/caption.md": (
            "sha256:2dfeb596683654b902d96b8592a9cc9c480557461a904c463023e4c933a75bd3"
        ),
        "examples/fig1_hybrid_complex_panel_pilot/panel_goals.md": (
            "sha256:fdf018dcd20fa8c223b1a2c3ba935a9f3fb1ca29643aff36c7ff08fd4dc5ca6c"
        ),
        "examples/fig1_hybrid_complex_panel_pilot/theory_guard.md": (
            "sha256:27550eda8e57b44224d6c248c92dc49335acad5f2081f51ba1b36eda30abca57"
        ),
    }
    assert semantic["authority"]["implementation_details_not_observed_declaration"]
    assert semantic["authority"]["preparation_receipt"] == {
        "path": "semantic-packet-preparation-receipt.yaml",
        "sha256": _sha256(receipt_path),
    }
    assert receipt["receipt_kind"] == "task_authored_access_self_attestation"
    assert receipt["independently_verified_telemetry"] is False
    assert receipt["preparer"] == semantic["authority"]["named_preparer"]
    assert receipt["prepared_at"] == semantic["authority"]["prepared_at"]
    assert receipt["base_commit"] == "0bd81f56"
    assert receipt["branch"] == "codex/direct-svg-semantic-packet"
    assert receipt["source_authority_hashes"] == semantic["authority"]["source_authority_hashes"]
    assert len(receipt["source_authority_hashes"]) == 4
    assert receipt["no_forbidden_access_declaration"]
    assert receipt["tools_used"]
    assert receipt["actions"]
    assert receipt["publication_acceptance"] == "not_claimed"
    assert semantic["scientific_objects"]
    assert semantic["object_relations"]
    assert semantic["text_content"]
    assert semantic["visual_roles"]
    assert semantic["publication_acceptance"] == "not_claimed"

    assert state["semantic_packet_authority"] == {
        "prepared_by_current_session": False,
        "implementation_details_observed": False,
        "preparer": semantic["authority"]["named_preparer"],
        "prepared_at": semantic["authority"]["prepared_at"],
        "sha256": _sha256(semantic_path),
        "receipt_path": "semantic-packet-preparation-receipt.yaml",
        "receipt_sha256": _sha256(receipt_path),
    }
    assert state["run_state"] == "ready"
    assert state["next_valid_transition"] == "run_test_a_or_test_b"
    assert state["publication_acceptance"] == "not_claimed"


def test_standalone_packets_validate_and_test_b_is_semantically_isolated() -> None:
    test_a_path = FIXTURE / "packets" / "test-a-reconstruction.yaml"
    test_b_path = FIXTURE / "packets" / "test-b-synthesis.yaml"

    test_a = validate_packet(test_a_path)
    test_b = validate_packet(test_b_path)

    assert test_a["test_kind"] == "reconstruction"
    assert test_b["test_kind"] == "synthesis"
    assert {item["role"] for item in test_b["allowed_inputs"]} == {
        "semantic_packet",
        "licensed_font",
    }
    assert test_b["reference_pixels_available"] is False
    assert test_b["reference_hashes_available"] is False
    assert test_b["geometry_derivatives_available"] is False
    assert test_b["test_a_history_available"] is False
    assert test_b["test_a_outputs_available"] is False
    assert test_b["publication_acceptance"] == "not_claimed"


def test_fixture_binds_a_licensed_font_and_isolated_fontconfig() -> None:
    receipt = _load("contract/font-receipt.yaml")
    font = FIXTURE / "contract" / receipt["font"]["path"]
    license_path = FIXTURE / "contract" / receipt["license"]["path"]
    fontconfig = FIXTURE / "contract" / receipt["fontconfig"]["path"]

    assert receipt["font"]["family"] == "Latin Modern Sans"
    assert receipt["font"]["sha256"] == _sha256(font)
    assert receipt["license"]["id"] == "GUST-FONT-LICENSE"
    assert receipt["license"]["sha256"] == _sha256(license_path)
    assert receipt["fontconfig"]["sha256"] == _sha256(fontconfig)
    fontconfig_text = fontconfig.read_text(encoding="utf-8")
    assert "fonts" in fontconfig_text
    assert "/System/Library/Fonts" not in fontconfig_text
    assert "/usr/share/fonts" not in fontconfig_text
    assert receipt["publication_acceptance"] == "not_claimed"


def test_test_a_and_b_templates_have_separate_boundaries_and_output_roots() -> None:
    test_a = _load("packets/test-a-reconstruction.template.yaml")
    test_b = _load("packets/test-b-synthesis.template.yaml")

    for packet, kind in ((test_a, "reconstruction"), (test_b, "synthesis")):
        assert packet["schema"] == "figure-agent.direct-svg-packet-template.v1"
        assert packet["target_packet_schema"] == "figure-agent.direct-svg-packet.v1"
        assert packet["test_kind"] == kind
        assert set(packet["panels"]) == {"C", "F"}
        assert set(packet["denied_source_families"]) == DENIED_SOURCE_FAMILIES
        assert packet["budgets"] == EXPECTED_BUDGETS
        assert packet["path_base"] == "fixture_root"
        assert packet["runnable"] is False
        assert packet["blocked_reason"] == "independent_semantic_packet_missing"
        assert packet["publication_acceptance"] == "not_claimed"

    assert test_a["output_root"] != test_b["output_root"]
    assert (FIXTURE / test_a["output_root"] / "run-state.yaml").is_file()
    assert (FIXTURE / test_b["output_root"] / "run-state.yaml").is_file()
    assert {item["role"] for item in test_a["allowed_inputs"]} >= {
        "panel_c_target_crop",
        "panel_f_target_crop",
        "licensed_font",
    }


def test_test_b_template_contains_no_target_or_geometry_derivative_input() -> None:
    test_b = _load("packets/test-b-synthesis.template.yaml")

    for item in test_b["allowed_inputs"]:
        role = item["role"].lower()
        path = str(item.get("path") or "").lower()
        assert "target" not in role
        assert "geometry" not in role
        assert "panel-c.png" not in path
        assert "panel-f.png" not in path
    assert test_b["reference_pixels_available"] is False
    assert test_b["reference_hashes_available"] is False
    assert test_b["geometry_derivatives_available"] is False


def test_run_and_review_states_cannot_claim_machine_or_publication_acceptance() -> None:
    review = _load("review/review-state.yaml")

    assert review["state"].startswith("blocked_")
    assert review["publication_acceptance"] == "not_claimed"


def test_completed_test_a_binds_candidates_ledgers_and_machine_only_state() -> None:
    semantic_hash = _sha256(FIXTURE / "contract" / "semantic-packet.yaml")
    packet_path = FIXTURE / "packets" / "test-a-reconstruction.yaml"
    run_root = FIXTURE / "runs" / "test-a"
    state = _load("runs/test-a/run-state.yaml")
    semantic_packet = FIXTURE / "contract" / "semantic-packet.yaml"

    validate_packet(packet_path)
    assert state["schema"] == "figure-agent.direct-svg-run-state.v1"
    assert state["test_kind"] == "reconstruction"
    assert state["state"] == "machine_review_ready"
    assert state["validated_packet"] == "../../packets/test-a-reconstruction.yaml"
    assert state["validated_packet_sha256"] == _sha256(packet_path)
    assert state["semantic_packet_sha256"] == semantic_hash
    assert state["execution_started"] is True
    assert state["human_quality_review"] == "not_performed"
    assert state["scientific_acceptance"] == "not_claimed"
    assert state["publication_acceptance"] == "not_claimed"
    assert len(state["candidate_artifacts"]) == 2
    assert [artifact["panel"] for artifact in state["candidate_artifacts"]] == [
        "C",
        "F",
    ]
    assert len({artifact["svg_path"] for artifact in state["candidate_artifacts"]}) == 2
    assert len({artifact["render_path"] for artifact in state["candidate_artifacts"]}) == 2
    assert len({artifact["ledger_path"] for artifact in state["candidate_artifacts"]}) == 2

    for artifact in state["candidate_artifacts"]:
        panel = artifact["panel"]
        svg_path = run_root / artifact["svg_path"]
        render_path = run_root / artifact["render_path"]
        ledger_path = run_root / artifact["ledger_path"]
        ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))

        assert artifact["svg_sha256"] == _sha256(svg_path)
        assert artifact["render_sha256"] == _sha256(render_path)
        assert artifact["ledger_sha256"] == _sha256(ledger_path)
        requirements = semantic_requirements(semantic_packet, panel=panel)
        assert requirements["required_ids"]
        assert requirements["required_text"]
        validation = validate_candidate_from_semantic_packet(
            svg_path,
            semantic_packet,
            panel=panel,
        )
        assert validation["validated_relations"]
        assert ledger["panel"] == panel
        assert artifact["cycles_completed"] == ledger["total_attempted_cycles"]
        assert ledger["utility_checkpoint"] == EXPECTED_BUDGETS["utility"]
        assert ledger["budget"] == EXPECTED_BUDGETS["ceiling"]
        assert ledger["ceiling_budget"] == EXPECTED_BUDGETS["ceiling"]
        assert len(ledger["iterations"]) == ledger["total_attempted_cycles"]
        assert ledger["evidence_status"] == "valid"
        assert ledger["valid_review_cycles"] == list(range(1, ledger["total_attempted_cycles"] + 1))

        validated_ledger = begin_ledger(
            ledger["budget"],
            started_at=ledger["started_at"],
            panel=panel,
        )
        for cycle, receipt in enumerate(ledger["iterations"], start=1):
            cycle_source = PLUGIN_ROOT / receipt["source_path"]
            cycle_render = PLUGIN_ROOT / receipt["render_path"]
            assert receipt["cycle"] == cycle
            assert receipt["source_path"].endswith(f"/panel-{panel.lower()}-cycle-{cycle}.svg")
            assert receipt["render_path"].endswith(f"/panel-{panel.lower()}-cycle-{cycle}.png")
            assert receipt["source_sha256"] == _sha256(cycle_source)
            assert receipt["render_sha256"] == _sha256(cycle_render)
            assert receipt["command"][0:3] == ["uv", "run", "python"]
            assert receipt["command"][3] == "scripts/direct_svg_render.py"
            assert receipt["runtime_receipt"]["fontconfig"]["path"] == (
                "examples/fig1_direct_svg_cleanroom_baseline/contract/fontconfig.xml"
            )
            assert receipt["runtime_receipt"]["font"]["path"] == (
                "examples/fig1_direct_svg_cleanroom_baseline/contract/fonts/lmsans10-regular.otf"
            )
            assert receipt["runtime_receipt"]["rsvg"]["version"]
            assert receipt["runtime_receipt"]["python"]["version"]
            assert receipt["runtime_receipt"]["pillow"]["version"]
            assert receipt["runtime_receipt"]["environment"]["FONTCONFIG_FILE"]
            assert receipt["runtime_receipt"]["environment"]["FONTCONFIG_PATH"]
            assert receipt["runtime_receipt"]["path_base"] == "plugin_root"
            assert receipt["runtime_receipt"]["source_path"] == receipt["source_path"]
            assert receipt["runtime_receipt"]["render_path"] == receipt["render_path"]
            assert receipt["runtime_receipt"]["producer"]["head_commit"] == (
                "unavailable_precommit"
            )
            assert (
                receipt["runtime_receipt"]["producer"]["head_commit_status"]
                == "unavailable_precommit"
            )
            assert receipt["tool_model_receipt"]["task"]["mode"] == ("cleanroom_manual_direct_svg")
            assert receipt["tool_model_receipt"]["provider"] == "openai"
            assert receipt["tool_model_receipt"]["model"] == "gpt-5-codex"
            assert receipt["tool_model_receipt"]["model_identity_independently_verified"] is False
            assert receipt["tool_model_receipt"]["snapshot"] is None
            assert receipt["tool_model_receipt"]["reasoning"] is None
            assert receipt["tool_model_receipt"]["task"]["name"]
            assert receipt["tool_model_receipt"]["task"]["base_commit"] == (
                "064a3cc62671ef0f086efb03f26c00d97bb783cd"
            )
            assert receipt["tool_model_receipt"]["tools"]["image_generation"] == ("not_used")
            assert receipt["publication_acceptance"] == "not_claimed"
            validated_ledger = record_iteration(validated_ledger, receipt)

        final = ledger["final_candidate"]
        assert final["source_sha256"] == artifact["svg_sha256"]
        assert final["render_sha256"] == artifact["render_sha256"]
        assert ledger["iterations"][-1]["source_sha256"] == artifact["svg_sha256"]
        assert ledger["iterations"][-1]["render_sha256"] == artifact["render_sha256"]
        assert ledger["publication_acceptance"] == "not_claimed"


def test_panel_c_symbolic_depth_is_one_editable_text_tree() -> None:
    svg = ET.parse(FIXTURE / "runs" / "test-a" / "panel-c.svg").getroot()
    trap_depth = next(element for element in svg.iter() if element.get("id") == "c_trap_depth")
    labels = [element for element in trap_depth.iter() if element.tag.rsplit("}", 1)[-1] == "text"]

    assert len(labels) == 1
    assert labels[0].get("data-semantic-text") == "ΔE_t^d"
    assert "".join(labels[0].itertext()) == "ΔEtd"
    assert len(list(labels[0])) == 2


def test_test_a_valid_cycles_replay_byte_identically_from_current_and_copied_checkout(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "copied-checkout"
    copied_root.mkdir()
    for relative in (
        "pyproject.toml",
        "uv.lock",
        "scripts/direct_svg_candidate.py",
        "scripts/direct_svg_render.py",
    ):
        target = copied_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PLUGIN_ROOT / relative, target)
    for relative in (
        "examples/fig1_direct_svg_cleanroom_baseline/contract/semantic-packet.yaml",
        "examples/fig1_direct_svg_cleanroom_baseline/contract/fontconfig.xml",
        "examples/fig1_direct_svg_cleanroom_baseline/contract/fonts/lmsans10-regular.otf",
    ):
        target = copied_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PLUGIN_ROOT / relative, target)

    for panel in ("c", "f"):
        ledger = _load(f"runs/test-a/panel-{panel}-ledger.yaml")
        valid_cycles = set(ledger["valid_review_cycles"])
        assert valid_cycles
        for receipt in ledger["iterations"]:
            if receipt["cycle"] not in valid_cycles:
                continue
            command = list(receipt["command"])
            for root in (PLUGIN_ROOT, copied_root):
                if root == copied_root:
                    for relative in (receipt["source_path"], receipt["render_path"]):
                        target = copied_root / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if relative == receipt["source_path"]:
                            shutil.copy2(PLUGIN_ROOT / relative, target)
                completed = subprocess.run(
                    command, check=True, capture_output=True, cwd=root, text=True
                )
                runtime_receipt = json.loads(completed.stdout)
                assert runtime_receipt["source_sha256"] == receipt["source_sha256"]
                assert runtime_receipt["render_sha256"] == receipt["render_sha256"]
                assert _sha256(root / receipt["render_path"]) == receipt["render_sha256"]
                assert runtime_receipt == receipt["runtime_receipt"]


def test_ready_test_b_binds_validated_packet_without_execution_claim() -> None:
    semantic_hash = _sha256(FIXTURE / "contract" / "semantic-packet.yaml")
    packet_path = FIXTURE / "packets" / "test-b-synthesis.yaml"
    state = _load("runs/test-b/run-state.yaml")

    validate_packet(packet_path)
    assert state == {
        "schema": "figure-agent.direct-svg-run-state.v1",
        "test_kind": "synthesis",
        "state": "ready_not_started",
        "validated_packet": "../../packets/test-b-synthesis.yaml",
        "validated_packet_sha256": _sha256(packet_path),
        "semantic_packet_sha256": semantic_hash,
        "execution_started": False,
        "candidate_artifacts": [],
        "publication_acceptance": "not_claimed",
    }
