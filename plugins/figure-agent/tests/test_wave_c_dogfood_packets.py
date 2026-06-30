from __future__ import annotations

import json
from pathlib import Path


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_smoke_panel_spacing_packet_tracks_human_decision_record() -> None:
    plugin_root = _plugin_root()
    packet_path = (
        plugin_root
        / "docs"
        / "decision-packets"
        / "2026-06-30-wave-c"
        / "smoke_panel_spacing_demo.json"
    )
    packet = _load_json(packet_path)
    record = _load_json(plugin_root / packet["source_decision_record"])

    assert packet["schema"] == record["packet_schema"]
    assert packet["fixture"] == record["fixture"] == "smoke_panel_spacing_demo"
    assert packet["packet_schema"] == record["packet_schema"]
    assert packet["source_queue_run_id"] == record["queue_run_id"]
    assert packet["decision_kind"] == record["decision_kind"]
    assert packet["human_decision"] == record["human_decision"]
    assert packet["agent_recommendation"] == record["agent_recommendation"]
    assert packet["follow_up"] == record["follow_up"]
    assert packet["mutation_boundary"] == record["mutation_boundary"] == "no_source_mutation"


def test_smoke_panel_spacing_packet_stays_outside_release_mutation() -> None:
    plugin_root = _plugin_root()
    packet = _load_json(
        plugin_root
        / "docs"
        / "decision-packets"
        / "2026-06-30-wave-c"
        / "smoke_panel_spacing_demo.json"
    )

    assert packet["packet_schema"] == "figure-agent.style-direction-packet.v1"
    assert packet["packet_kind"] == "bounded_spacing_style_lock_packet"
    assert packet["bounded_packet"]["packet_kind"] == "bounded_spacing_style_lock_packet"
    assert packet["bounded_packet"]["recommended_choice_id"] == "extract_spacing_style_lock"
    assert "manuscript release acceptance" in packet["bounded_packet"]["non_goals"]
    assert "manuscript acceptance" in packet["risk"]["primary"]
    assert packet["safety"] == {
        "source_mutation": False,
        "release_state_mutation": False,
        "golden_mutation": False,
        "generated_export_mutation": False,
    }


def test_fig3_accept_current_packet_tracks_human_decision_record() -> None:
    plugin_root = _plugin_root()
    packet = _load_json(
        plugin_root
        / "docs"
        / "decision-packets"
        / "2026-06-30-wave-c"
        / "fig3_trapping_concept.json"
    )
    record = _load_json(plugin_root / packet["source_human_decision_record"])

    assert packet["schema"] == record["packet_schema"]
    assert packet["fixture"] == record["fixture"] == "fig3_trapping_concept"
    assert packet["queue_run_id"] == record["queue_run_id"]
    assert packet["mutation_boundary"] == record["mutation_boundary"] == "no_source_mutation"
    assert record["decision_kind"] == "accept_current_generated_export"
    assert packet["queue_contract"]["expected_packet_kind"] == (
        "release_acceptance_decision_packet"
    )
    assert packet["queue_contract"]["safe_default"] == "accept_current_generated_export"
    assert packet["recommended_choice_id"] == "accept_current_generated_export"
    assert record["follow_up"]["implementation_slice"] == (
        packet["follow_up"]["implementation_slice"]
    )


def test_fig3_accept_current_packet_stays_outside_release_mutation() -> None:
    plugin_root = _plugin_root()
    packet = _load_json(
        plugin_root
        / "docs"
        / "decision-packets"
        / "2026-06-30-wave-c"
        / "fig3_trapping_concept.json"
    )

    assert packet["packet_kind"] == "release_acceptance_decision_packet"
    assert packet["required_actor"] == "release_operator"
    assert packet["boundary"] == "accepted_or_final_ready_required"
    assert packet["current_state_summary"]["workflow_ready"] is True
    assert packet["current_state_summary"]["known_blockers"] == []
    assert "do not edit accepted state from this packet" in packet["disallowed_actions"]
    assert "do not edit release state" in packet["disallowed_actions"]
    assert "do not treat the recommendation as implicit human acceptance" in (
        packet["disallowed_actions"]
    )
    assert {choice["id"] for choice in packet["choices"]} == {
        "accept_current_generated_export",
        "declare_final_artifact",
        "reject_current_artifact",
        "defer_for_dogfood",
    }
