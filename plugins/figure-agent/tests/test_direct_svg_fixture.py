from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml
from direct_svg_candidate import begin_ledger, record_iteration, validate_candidate
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
    assert receipt["source_authority_hashes"] == semantic["authority"][
        "source_authority_hashes"
    ]
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
    required_ids = {
        "C": {
            "c_polymer_film",
            "c_shallow_trap_population",
            "c_deep_trap_population",
            "c_mobility_edge",
            "c_conduction_band",
            "c_valence_band",
            "c_trap_depth",
            "real_space_to_energy_relations",
        },
        "F": {
            "f_polymer_cantilever",
            "f_fixed_support",
            "f_planar_electrode",
            "f_active_bias",
            "f_trapped_charge",
            "f_coulomb_repulsion",
            "f_air_gap",
        },
    }

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
    assert {artifact["panel"] for artifact in state["candidate_artifacts"]} == {
        "C",
        "F",
    }

    for artifact in state["candidate_artifacts"]:
        panel = artifact["panel"]
        svg_path = run_root / artifact["svg_path"]
        render_path = run_root / artifact["render_path"]
        ledger_path = run_root / artifact["ledger_path"]
        ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))

        assert artifact["cycles_completed"] == 3
        assert artifact["svg_sha256"] == _sha256(svg_path)
        assert artifact["render_sha256"] == _sha256(render_path)
        assert artifact["ledger_sha256"] == _sha256(ledger_path)
        assert validate_candidate(svg_path, required_ids=required_ids[panel])
        assert ledger["panel"] == panel
        assert ledger["budget"] == EXPECTED_BUDGETS["utility"]
        assert ledger["ceiling_budget"] == EXPECTED_BUDGETS["ceiling"]
        assert len(ledger["iterations"]) == 3

        validated_ledger = begin_ledger(
            ledger["budget"],
            started_at=ledger["started_at"],
        )
        for cycle, receipt in enumerate(ledger["iterations"], start=1):
            cycle_render = run_root / f"panel-{panel.lower()}-cycle-{cycle}.png"
            assert receipt["cycle"] == cycle
            assert receipt["render_sha256"] == _sha256(cycle_render)
            assert receipt["tool_model_receipt"]["task"]["mode"] == (
                "cleanroom_manual_direct_svg"
            )
            assert receipt["tool_model_receipt"]["tools"]["image_generation"] == (
                "not_used"
            )
            assert receipt["publication_acceptance"] == "not_claimed"
            validated_ledger = record_iteration(validated_ledger, receipt)

        final = ledger["final_candidate"]
        assert final["source_sha256"] == artifact["svg_sha256"]
        assert final["render_sha256"] == artifact["render_sha256"]
        assert ledger["iterations"][-1]["source_sha256"] == artifact["svg_sha256"]
        assert ledger["iterations"][-1]["render_sha256"] == artifact["render_sha256"]
        assert ledger["publication_acceptance"] == "not_claimed"


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
