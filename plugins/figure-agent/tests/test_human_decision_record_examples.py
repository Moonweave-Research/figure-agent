from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from human_decision_record import validate_decision_record  # noqa: E402


def test_documented_human_decision_records_validate() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    record_paths = sorted((plugin_root / "docs" / "decision-records").glob("**/*.json"))

    assert record_paths
    for record_path in record_paths:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        validated = validate_decision_record(record)
        assert validated["fixture"] == record["fixture"]


def test_wave_c_fig1_comparison_packet_matches_human_decision_record() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    record_path = (
        plugin_root
        / "docs"
        / "decision-records"
        / "2026-06-30-wave-c"
        / "fig1_overview_v2_pair_001_vault.json"
    )
    packet_path = (
        plugin_root
        / "docs"
        / "decision-packets"
        / "2026-06-30-wave-c"
        / "fig1_overview_v2_pair_001_vault.json"
    )

    record = validate_decision_record(json.loads(record_path.read_text(encoding="utf-8")))
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    assert packet["schema"] == record["packet_schema"]
    assert packet["fixture"] == record["fixture"]
    assert packet["queue_run_id"] == record["queue_run_id"]
    assert packet["source_human_decision_record"] == (
        "docs/decision-records/2026-06-30-wave-c/fig1_overview_v2_pair_001_vault.json"
    )
    assert packet["packet_kind"] == "force_golden_decision_packet"
    assert packet["boundary"] == packet["queue_contract"]["expected_boundary"]
    assert packet["boundary"] == "force_golden_required"
    assert packet["mutation_boundary"] == record["mutation_boundary"] == "no_source_mutation"
    assert record["decision_kind"] == "defer_for_dogfood"
    assert record["human_decision"] == "selected_as_policy_golden_benchmark_anchor"
    assert "protected release/golden boundary" in record["human_note"]
    assert packet["comparison_refs"]["current_generated_export"] == (
        "examples/fig1_overview_v2_pair_001_vault/exports/"
        "fig1_overview_v2_pair_001_vault.svg"
    )
    assert packet["comparison_refs"]["tracked_golden_baseline"] == (
        "examples/fig1_overview_v2_pair_001_vault/exports/"
        "fig1_overview_v2_pair_001_vault.pdf"
    )
    assert packet["recommended_choice_id"] == packet["queue_contract"]["safe_default"]
    assert packet["recommended_choice_id"] == "defer_for_visual_dogfood"
    assert "--force-golden" in " ".join(packet["disallowed_actions"])
    assert record["follow_up"]["implementation_slice"] == (
        packet["follow_up"]["implementation_slice"]
    )
    assert {choice["id"] for choice in packet["choices"]} == {
        "approve_force_golden_roll_forward",
        "reject_and_keep_current_golden",
        "defer_for_visual_dogfood",
    }
    assert not next(
        choice
        for choice in packet["choices"]
        if choice["id"] == "defer_for_visual_dogfood"
    )["requires_explicit_authority"]


def test_wave_c_fig3_accept_current_packet_matches_human_decision_record() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    record_path = (
        plugin_root
        / "docs"
        / "decision-records"
        / "2026-06-30-wave-c"
        / "fig3_trapping_concept.json"
    )
    packet_path = (
        plugin_root
        / "docs"
        / "decision-packets"
        / "2026-06-30-wave-c"
        / "fig3_trapping_concept.json"
    )

    record = validate_decision_record(json.loads(record_path.read_text(encoding="utf-8")))
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    assert packet["schema"] == record["packet_schema"]
    assert packet["fixture"] == record["fixture"]
    assert packet["queue_run_id"] == record["queue_run_id"]
    assert packet["source_human_decision_record"] == (
        "docs/decision-records/2026-06-30-wave-c/fig3_trapping_concept.json"
    )
    assert packet["packet_kind"] == "release_acceptance_decision_packet"
    assert packet["boundary"] == packet["queue_contract"]["expected_boundary"]
    assert packet["boundary"] == "accepted_or_final_ready_required"
    assert packet["mutation_boundary"] == record["mutation_boundary"] == "no_source_mutation"
    assert record["decision_kind"] == packet["recommended_choice_id"]
    assert record["human_decision"] == "selected_as_real_manuscript_accept_current_candidate"
    assert packet["current_state_summary"]["artifact_class"] == "real_manuscript_figure"
    assert packet["current_state_summary"]["critique_verdict"] == "ready"
    assert packet["current_state_summary"]["known_blockers"] == []
    assert packet["recommended_choice_id"] == packet["queue_contract"]["safe_default"]
    assert "implicit human acceptance" in " ".join(packet["disallowed_actions"])
    assert record["follow_up"]["implementation_slice"] == (
        packet["follow_up"]["implementation_slice"]
    )
    accept_choice = next(
        choice for choice in packet["choices"] if choice["id"] == "accept_current_generated_export"
    )
    assert accept_choice["requires_explicit_authority"]
    assert "accepted: true" in accept_choice["follow_up"]["manual_record_path"]
    assert "scientific blocker" in accept_choice["risk"]
    assert {choice["id"] for choice in packet["choices"]} == {
        "accept_current_generated_export",
        "declare_final_artifact",
        "reject_current_artifact",
        "defer_for_dogfood",
    }

def test_fig3_acceptance_defer_record_matches_packet_without_release_mutation() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    record_path = (
        plugin_root
        / "docs"
        / "decision-records"
        / "2026-07-01-acceptance"
        / "fig3_trapping_concept_defer_for_dogfood.json"
    )
    packet_path = (
        plugin_root
        / "docs"
        / "decision-packets"
        / "2026-07-01-acceptance"
        / "fig3_trapping_concept_acceptance_packet.json"
    )

    raw_record = json.loads(record_path.read_text(encoding="utf-8"))
    record = validate_decision_record(raw_record)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    assert packet["schema"] == record["packet_schema"]
    assert packet["fixture"] == record["fixture"]
    assert packet["created_at"] == record["packet_timestamp"]
    assert record["decision_kind"] == "defer_for_dogfood"
    assert record["human_decision"] != packet["recommended_choice_id"]
    assert packet["recommended_choice_id"] == "accept_current_generated_export"
    assert packet["follow_up"]["safe_default_without_human_decision"] == record[
        "decision_kind"
    ]
    assert (
        "docs/decision-packets/2026-07-01-acceptance/"
        "fig3_trapping_concept_acceptance_packet.json"
        in record["agent_recommendation"]
    )
    assert packet["recommended_choice_id"] in record["agent_recommendation"]
    assert record["mutation_boundary"] == packet["mutation_boundary"] == "no_source_mutation"
    assert "Do not treat" in raw_record["human_note"]
    assert "accepted: true" in record["follow_up"]["implementation_slice"]
    assert "final artifact" in record["follow_up"]["implementation_slice"]
    assert "mutate source" in record["follow_up"]["implementation_slice"]
    assert packet["choices"][1]["state_mutation"] == []
