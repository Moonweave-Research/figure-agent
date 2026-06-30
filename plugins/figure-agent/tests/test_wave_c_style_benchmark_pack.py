from __future__ import annotations

import json
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = (
    PLUGIN_ROOT
    / "docs"
    / "style-benchmark-packs"
    / "2026-06-30-wave-c"
    / "fig1_overview_v2_pair_001_vault.json"
)


def _load_pack() -> dict[str, object]:
    return json.loads(PACK_PATH.read_text(encoding="utf-8"))


def _load_yaml(relative_path: str) -> dict[str, object]:
    return yaml.safe_load((PLUGIN_ROOT / relative_path).read_text(encoding="utf-8"))


def test_wave_c_style_benchmark_pack_links_to_fixture_contracts() -> None:
    pack = _load_pack()
    benchmark = _load_yaml(str(pack["benchmark_contract"]))
    aesthetic = _load_yaml(str(pack["aesthetic_intent"]))

    assert pack["schema"] == "figure-agent.style-benchmark-candidate-pack.v1"
    assert pack["fixture"] == benchmark["fixture"] == aesthetic["fixture"]
    assert pack["fixture"] == "fig1_overview_v2_pair_001_vault"
    assert pack["source_decision_packet"].endswith(
        "decision-packets/2026-06-30-wave-c/fig1_overview_v2_pair_001_vault.json"
    )
    assert pack["target_style_class"] == (
        "restrained editorial multipanel scientific schematic"
    )


def test_wave_c_style_benchmark_pack_has_required_candidate_slots() -> None:
    pack = _load_pack()
    slots = {slot["id"]: slot for slot in pack["candidate_family_slots"]}

    assert set(slots) == {
        "current_style",
        "restrained_tikz_refinement",
        "editorial_redesign",
        "svg_polish_handoff",
    }
    assert slots["current_style"]["mutation_boundary"] == "no_source_mutation"
    assert "source_mutation_requires_separate_approval" in {
        slots["restrained_tikz_refinement"]["mutation_boundary"],
        slots["editorial_redesign"]["mutation_boundary"],
    }
    assert "ready_for_svg_polish evidence is positive" in (
        slots["svg_polish_handoff"]["entry_condition"]
    )


def test_wave_c_style_benchmark_pack_rejects_pretty_semantic_drift() -> None:
    pack = _load_pack()
    forbidden = "\n".join(pack["forbidden_semantic_changes"])
    rejection_rules = "\n".join(pack["candidate_rejection_rules"])

    for required in (
        "A/B/C/D/E/F panel roles",
        "rename symbols",
        "swap shallow/deep trap color semantics",
        "remove required labels",
        "SVG polish to repair scientific",
    ):
        assert required in forbidden
    assert "reject a prettier candidate if it changes semantics" in rejection_rules
    assert "accepted-state, release-state, final-artifact, export, or golden mutation" in (
        rejection_rules
    )


def test_wave_c_style_benchmark_pack_measurable_checks_track_benchmark_contract() -> None:
    pack = _load_pack()
    benchmark = _load_yaml(str(pack["benchmark_contract"]))
    checks = {check["id"]: check for check in pack["measurable_checks"]}

    assert "source_compile_failure" in benchmark["hard_regressions"]
    assert "candidate_hard_gate_rejected" in benchmark["hard_regressions"]
    assert checks["text_boundary_delta"]["metric"] == "text_boundary.blocker_count"
    assert checks["text_boundary_delta"]["expected_movement"] == benchmark[
        "expected_movement"
    ]["text_boundary.blocker_count"]
    assert "no new local tiny/scriptsize/huge overrides" in checks[
        "style_lock_typography"
    ]["must_pass"]


def test_wave_c_style_benchmark_pack_keeps_human_art_direction_separate() -> None:
    pack = _load_pack()
    questions = "\n".join(pack["human_only_questions"])

    assert pack["default_recommendation"] == (
        "keep_current_style_until_candidate_beats_benchmark"
    )
    assert pack["safety"] == {
        "source_mutation": False,
        "accepted_state_mutation": False,
        "release_state_mutation": False,
        "generated_export_mutation": False,
        "golden_mutation": False,
        "svg_polish_default": False,
    }
    assert "journal fit" in questions
    assert "flagship visual" in questions
