from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_queue  # noqa: E402


def _summary(
    name: str,
    *,
    action: str,
    stop_boundary: str | None,
    first_blocker: str,
    safe_command: str | None = None,
    blocking_source: str | None = None,
    svg_polish_gate: dict[str, Any] | None = None,
    svg_polish_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = {
        "fixture": name,
        "action": action,
        "stop_boundary": stop_boundary,
        "safe_command": safe_command,
        "status": {
            "render_state": "FRESH",
            "critique_state": "FRESH",
            "export_state": "FRESH",
            "acceptance_state": "NOT_DECLARED",
            "final_artifact_state": "FRESH",
            "final_artifact_kind": "generated_export",
            "final_artifact_path": f"exports/{name}.svg",
            "publication_gate_state": "NOT_APPLICABLE",
            "publication_gate_failures": None,
            "release_ready": False,
        },
        "status_explanation": {
            "first_blocker": {
                "code": first_blocker,
                "category": "fixture_freshness",
                "manual": False,
            }
        },
        "next_action_summary": {
            "blocking_source": blocking_source or stop_boundary or "driver.action",
            "requires_human": action in {"human_gate_stop", "release_blocked"},
        },
    }
    if svg_polish_gate is not None:
        summary["svg_polish_gate"] = svg_polish_gate
    if svg_polish_readiness is not None:
        summary["svg_polish_readiness"] = svg_polish_readiness
    return summary


def _write_fixture(root: Path, name: str) -> None:
    fixture = root / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(f"name: {name}\npanels: []\n", encoding="utf-8")


def test_queue_surfaces_missing_style_benchmark_pack_non_fatal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action=fig_queue.fig_driver.ACTION_COMPLETE,
            stop_boundary=None,
            first_blocker="none",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=None,
    )

    row = queue["rows"][0]
    assert row["style_benchmark_pack_state"] == "missing"
    assert row["style_benchmark_pack_path"] == (
        "docs/style-benchmark-packs/2026-06-30-wave-c/alpha.json"
    )
    assert "style_benchmark_pack_error" not in row
    assert queue["summary"]["errors"] == 0
    assert queue["summary"]["by_style_benchmark_pack_state"] == {"missing": 1}


def test_queue_surfaces_present_style_benchmark_pack_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = "fig1_overview_v2_pair_001_vault"
    _write_fixture(tmp_path, fixture)

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action=fig_queue.fig_driver.ACTION_COMPLETE,
            stop_boundary=None,
            first_blocker="none",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=None,
    )

    row = queue["rows"][0]
    pack = row["style_benchmark_pack"]
    assert row["style_benchmark_pack_state"] == "present"
    assert pack["target_style_class"]
    assert pack["default_recommendation"] == (
        "keep_current_style_until_candidate_beats_benchmark"
    )
    assert pack["safety_boundary"] == {
        "accepted_state_mutation": False,
        "generated_export_mutation": False,
        "golden_mutation": False,
        "release_state_mutation": False,
        "source_mutation": False,
        "svg_polish_default": False,
    }
    assert set(pack["candidate_slot_ids"]) == {
        "current_style",
        "restrained_tikz_refinement",
        "editorial_redesign",
        "svg_polish_handoff",
    }
    assert row["acceptance_state"] == "NOT_DECLARED"
    assert row["release_ready"] is False
    assert queue["summary"]["by_style_benchmark_pack_state"] == {"present": 1}


def test_queue_marks_malformed_style_benchmark_pack_invalid_not_recommended(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin_root = tmp_path / "plugin"
    pack_dir = plugin_root / "docs" / "style-benchmark-packs" / "2026-06-30-wave-c"
    pack_dir.mkdir(parents=True)
    (pack_dir / "alpha.json").write_text("{not valid json", encoding="utf-8")
    workspace_root = tmp_path / "workspace"
    _write_fixture(workspace_root, "alpha")
    monkeypatch.setenv("FIGURE_AGENT_PLUGIN_ROOT", str(plugin_root))

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action=fig_queue.fig_driver.ACTION_COMPLETE,
            stop_boundary=None,
            first_blocker="none",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=workspace_root,
        mode="release",
        goal="triage",
        fixtures=None,
    )

    row = queue["rows"][0]
    assert row["style_benchmark_pack_state"] == "invalid"
    assert "style_benchmark_pack_error" in row
    assert "style_benchmark_pack" not in row
    assert queue["summary"]["errors"] == 0
    assert queue["summary"]["by_style_benchmark_pack_state"] == {"invalid": 1}


def test_build_queue_json_rows_and_summaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        assert mode == "release"
        assert goal == "triage"
        assert repo_root == tmp_path
        if name == "alpha":
            return _summary(
                name,
                action="run_critique",
                stop_boundary="host_llm_critique_required",
                first_blocker="critique_stale",
                safe_command="/fig_critique alpha",
            )
        return _summary(
            name,
            action="release_blocked",
            stop_boundary="accepted_or_final_ready_required",
            first_blocker="acceptance_not_declared",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=None,
    )

    assert queue["schema"] == "figure-agent.fixture-driver-queue.v1"
    assert [row["fixture"] for row in queue["rows"]] == ["alpha", "beta"]
    assert queue["rows"][0]["safe_command"] == "/fig_critique alpha"
    assert queue["rows"][0]["required_actor"] == "host_llm"
    assert queue["rows"][0]["blocking_source"] == "host_llm_critique_required"
    assert queue["rows"][0]["requires_human"] is False
    assert queue["summary"]["total"] == 2
    assert queue["summary"]["by_action"] == {"release_blocked": 1, "run_critique": 1}
    assert queue["summary"]["by_required_actor"] == {
        "host_llm": 1,
        "release_operator": 1,
    }
    assert queue["summary"]["by_blocking_source"] == {
        "accepted_or_final_ready_required": 1,
        "host_llm_critique_required": 1,
    }
    assert queue["summary"]["by_stop_boundary"] == {
        "accepted_or_final_ready_required": 1,
        "host_llm_critique_required": 1,
    }
    assert queue["summary"]["by_first_blocker"] == {
        "acceptance_not_declared": 1,
        "critique_stale": 1,
    }
    assert queue["rows"][0]["bottleneck_category"] == "host_critique"
    assert queue["rows"][1]["bottleneck_category"] == "human_acceptance"
    assert queue["summary"]["by_bottleneck_category"] == {
        "host_critique": 1,
        "human_acceptance": 1,
    }
    report = queue["bottleneck_report"]
    assert report["schema"] == "figure-agent.queue-bottleneck-report.v1"
    assert report["source"] == "fig-agent queue over live fig-agent status/driver state"
    assert report["total_rows"] == 2
    assert report["errors"] == 0
    assert report["dominant_action"] == [
        {"key": "release_blocked", "count": 1},
        {"key": "run_critique", "count": 1},
    ]
    assert report["dominant_first_blocker"] == [
        {"key": "acceptance_not_declared", "count": 1},
        {"key": "critique_stale", "count": 1},
    ]
    assert report["dominant_required_actor"] == [
        {"key": "host_llm", "count": 1},
        {"key": "release_operator", "count": 1},
    ]
    assert report["dominant_blocking_source"] == [
        {"key": "accepted_or_final_ready_required", "count": 1},
        {"key": "host_llm_critique_required", "count": 1},
    ]
    assert report["by_bottleneck_category"] == {
        "mechanical_tool": 0,
        "host_critique": 1,
        "human_acceptance": 1,
        "reference_context": 0,
        "template_style": 0,
    }
    assert [item["category"] for item in report["bottleneck_categories"]] == [
        "mechanical_tool",
        "host_critique",
        "human_acceptance",
        "reference_context",
        "template_style",
    ]
    assert report["command_plan"] == {"executable": 0, "blocked": 2, "complete": 0}


def test_bottleneck_report_classifies_five_operator_buckets() -> None:
    rows = [
        {
            "fixture": "needs_render",
            "action": "run_compile",
            "required_actor": "workflow_agent",
            "requires_human": False,
            "safe_command": "fig-agent compile needs_render",
            "stop_boundary": None,
            "first_blocker": "render_missing",
            "blocking_source": "driver.action",
        },
        {
            "fixture": "needs_host_critique",
            "action": "run_critique",
            "required_actor": "host_llm",
            "requires_human": False,
            "safe_command": "/fig_critique needs_host_critique",
            "stop_boundary": "host_llm_critique_required",
            "first_blocker": "critique_stale",
            "blocking_source": "host_llm_critique_required",
        },
        {
            "fixture": "needs_acceptance",
            "action": "release_blocked",
            "required_actor": "release_operator",
            "requires_human": True,
            "safe_command": None,
            "stop_boundary": "accepted_or_final_ready_required",
            "first_blocker": "acceptance_not_declared",
            "blocking_source": "accepted_or_final_ready_required",
        },
        {
            "fixture": "needs_reference",
            "action": "run_critique",
            "required_actor": "host_llm",
            "requires_human": False,
            "safe_command": "/fig_critique needs_reference",
            "stop_boundary": "reference_missing",
            "first_blocker": "reference_missing",
            "blocking_source": "reference_missing",
        },
        {
            "fixture": "needs_style_template",
            "action": "polish_handoff_stop",
            "required_actor": "svg_editor",
            "requires_human": False,
            "safe_command": None,
            "stop_boundary": "mode_forbidden_action",
            "first_blocker": "svg_polish_delta_stale",
            "blocking_source": "svg_polish_manifest",
            "svg_polish_next_action": "refresh_svg_polish_handoff",
            "svg_polish_blocking_sources": ["aesthetic_delta"],
        },
    ]

    report = fig_queue.build_bottleneck_report(rows)

    assert report["by_bottleneck_category"] == {
        "mechanical_tool": 1,
        "host_critique": 1,
        "human_acceptance": 1,
        "reference_context": 1,
        "template_style": 1,
    }
    rollup = {entry["category"]: entry for entry in report["bottleneck_categories"]}
    assert rollup["mechanical_tool"]["example_fixtures"] == ["needs_render"]
    assert rollup["host_critique"]["example_fixtures"] == ["needs_host_critique"]
    assert rollup["human_acceptance"]["example_fixtures"] == ["needs_acceptance"]
    assert rollup["reference_context"]["example_fixtures"] == ["needs_reference"]
    assert rollup["template_style"]["example_fixtures"] == ["needs_style_template"]
    assert {
        "key": "blocking_source:reference_missing",
        "count": 1,
    } in rollup["reference_context"]["top_signals"]
    assert rollup["template_style"]["top_signals"][0] == {
        "key": "action:polish_handoff_stop",
        "count": 1,
    }


def test_build_queue_filters_requested_fixtures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")
    seen: list[str] = []

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        seen.append(name)
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        fixtures=["beta"],
    )

    assert seen == ["beta"]
    assert [row["fixture"] for row in queue["rows"]] == ["beta"]


def test_queue_rows_preserve_driver_operator_guidance_for_complete_modes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        summary = _summary(name, action="complete", stop_boundary=None, first_blocker="none")
        summary["operator_guidance"] = {
            "schema": "figure-agent.operator-guidance.v1",
            "state": "complete",
            "required_actor": "none",
            "next_step": (
                "authoring mode is complete; run `/fig_drive alpha --mode review` "
                "for whole-figure review."
            ),
            "decision_boundary": {
                "schema": "figure-agent.decision-boundary.v1",
                "kind": "none",
            },
        }
        return summary

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="authoring",
        goal="triage",
        fixtures=None,
    )

    guidance = queue["rows"][0]["operator_guidance"]
    assert guidance["schema"] == "figure-agent.operator-guidance.v1"
    assert "authoring mode is complete" in guidance["next_step"]
    assert "--mode review" in guidance["next_step"]
    assert queue["rows"][0]["blocking_source"] is None
    assert queue["summary"]["by_blocking_source"] == {}


def test_queue_table_uses_operator_guidance_for_complete_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        summary = _summary(name, action="complete", stop_boundary=None, first_blocker="none")
        summary["operator_guidance"] = {
            "schema": "figure-agent.operator-guidance.v1",
            "state": "complete",
            "required_actor": "none",
            "next_step": (
                "authoring mode is complete; run `/fig_drive alpha --mode review` "
                "for whole-figure review."
            ),
            "decision_boundary": {
                "schema": "figure-agent.decision-boundary.v1",
                "kind": "none",
            },
        }
        return summary

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="authoring",
        goal="triage",
        fixtures=None,
    )

    fig_queue.print_table(queue)

    table = capsys.readouterr().out
    assert "authoring mode is complete" in table
    assert "--mode review" in table


def test_queue_command_plan_uses_operator_guidance_for_complete_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        summary = _summary(name, action="complete", stop_boundary=None, first_blocker="none")
        summary["operator_guidance"] = {
            "schema": "figure-agent.operator-guidance.v1",
            "state": "complete",
            "required_actor": "none",
            "next_step": (
                "authoring mode is complete; run `/fig_drive alpha --mode review` "
                "for whole-figure review."
            ),
        }
        return summary

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="authoring",
        goal="triage",
        fixtures=None,
        include_command_plan=True,
    )

    assert queue["command_plan"]["blocked_count"] == 0
    assert queue["command_plan"]["complete_count"] == 1
    assert queue["command_plan"]["blocked"] == []
    handoff = queue["command_plan"]["complete"][0]["operator_handoff"]
    assert "authoring mode is complete" in handoff["next_step"]
    assert "--mode review" in handoff["next_step"]
    assert handoff["command"] is None
    assert queue["command_plan"]["complete"][0]["reason"] == "mode_scoped_complete"


def test_release_queue_row_includes_fixture_specific_acceptance_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="release_blocked",
            stop_boundary="accepted_or_final_ready_required",
            first_blocker="acceptance_not_declared",
            blocking_source="accepted_or_final_ready_required",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=None,
        include_command_plan=True,
    )

    row = queue["rows"][0]
    packet = row["decision_packet"]
    assert packet["schema"] == "figure-agent.release-decision-packet.v1"
    assert packet["packet_kind"] == "release_acceptance_decision_packet"
    assert packet["boundary"] == "accepted_or_final_ready_required"
    assert packet["current_state"] == {
        "render_state": "FRESH",
        "critique_state": "FRESH",
        "export_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "final_artifact_state": "FRESH",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": "exports/alpha.svg",
        "publication_gate_state": "NOT_APPLICABLE",
        "publication_gate_failures": None,
        "release_ready": False,
    }
    assert packet["recommended_choice_id"] == "accept_current_generated_export"
    assert [choice["id"] for choice in packet["choices"]] == [
        "accept_current_generated_export",
        "declare_final_artifact",
        "reject_current_artifact",
        "defer_for_dogfood",
    ]
    assert packet["choices"][0]["follow_up"]["manual_record_path"] == (
        "examples/alpha/QUALITY_AUDIT.md and accepted: true in spec.yaml"
    )
    assert queue["command_plan"]["blocked"][0]["operator_handoff"]["decision_packet"] == packet


def test_release_packet_distinguishes_force_golden_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="release_blocked",
            stop_boundary="force_golden_required",
            first_blocker="export_tracked_golden",
            blocking_source="force_golden_required",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=None,
        include_command_plan=True,
    )

    packet = queue["rows"][0]["decision_packet"]
    assert packet["packet_kind"] == "force_golden_decision_packet"
    assert packet["boundary"] == "force_golden_required"
    assert packet["recommended_choice_id"] == "defer_for_visual_dogfood"
    assert [choice["id"] for choice in packet["choices"]] == [
        "approve_force_golden_roll_forward",
        "reject_and_keep_current_golden",
        "defer_for_visual_dogfood",
    ]
    assert packet["choices"][0]["follow_up"]["command"] == ("fig-agent export alpha --force-golden")
    assert "Do not force" in packet["agent_recommendation"]


def test_release_packet_flags_declared_polished_svg_final_artifact_states(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "missing_svg")
    _write_fixture(tmp_path, "stale_svg")
    _write_fixture(tmp_path, "fresh_svg")
    _write_fixture(tmp_path, "invalid_svg")
    _write_fixture(tmp_path, "blocked_svg")

    final_states = {
        "missing_svg": "MISSING",
        "stale_svg": "STALE",
        "fresh_svg": "FRESH",
        "invalid_svg": "INVALID",
        "blocked_svg": "BLOCKED",
    }

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        summary = _summary(
            name,
            action="release_blocked",
            stop_boundary="accepted_or_final_ready_required",
            first_blocker="acceptance_not_declared",
            blocking_source="accepted_or_final_ready_required",
        )
        summary["status"]["final_artifact_state"] = final_states[name]
        summary["status"]["final_artifact_kind"] = "polished_svg"
        summary["status"]["final_artifact_path"] = "polish/svg_polish_manifest.json"
        return summary

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=None,
    )

    packets = {row["fixture"]: row["decision_packet"] for row in queue["rows"]}
    assert "is MISSING" in packets["missing_svg"]["choices"][1]["warning"]
    assert "is STALE" in packets["stale_svg"]["choices"][1]["warning"]
    assert "is INVALID" in packets["invalid_svg"]["choices"][1]["warning"]
    assert "is BLOCKED" in packets["blocked_svg"]["choices"][1]["warning"]
    assert packets["fresh_svg"]["choices"][1]["evidence"] == (
        "declared polished SVG final artifact is fresh"
    )


def test_release_packet_defers_when_publication_gate_has_agent_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        summary = _summary(
            name,
            action="release_blocked",
            stop_boundary="accepted_or_final_ready_required",
            first_blocker="publication_gate_required",
            blocking_source="accepted_or_final_ready_required",
        )
        summary["status"]["acceptance_state"] = "NOT_ACCEPTED"
        summary["status"]["publication_gate_state"] = "HUMAN_ACCEPTANCE_REQUIRED"
        summary["status"]["publication_gate_failures"] = [
            {
                "code": "missing_quality_audit",
                "actor": "agent",
                "required_action": "create QUALITY_AUDIT.md",
            }
        ]
        return summary

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=None,
    )

    packet = queue["rows"][0]["decision_packet"]
    assert packet["recommended_choice_id"] == "defer_for_dogfood"
    assert "deterministic publication-gate failures" in packet["agent_recommendation"]
    assert packet["current_state"]["publication_gate_failures"] == [
        {
            "code": "missing_quality_audit",
            "actor": "agent",
            "required_action": "create QUALITY_AUDIT.md",
        }
    ]


def test_release_packet_distinguishes_not_accepted_from_not_declared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        summary = _summary(
            name,
            action="release_blocked",
            stop_boundary="accepted_or_final_ready_required",
            first_blocker="acceptance_not_declared",
            blocking_source="accepted_or_final_ready_required",
        )
        summary["status"]["acceptance_state"] = "NOT_ACCEPTED"
        return summary

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=None,
    )

    packet = queue["rows"][0]["decision_packet"]
    assert packet["recommended_choice_id"] == "defer_for_dogfood"
    assert "QUALITY_AUDIT.md defects" in packet["agent_recommendation"]


def test_release_operator_handoff_includes_decision_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="release_blocked",
            stop_boundary="force_golden_required",
            first_blocker="export_tracked_golden",
            blocking_source="force_golden_required",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="human gate",
        fixtures=None,
        include_command_plan=True,
    )

    handoff = queue["command_plan"]["blocked"][0]["operator_handoff"]
    packet = handoff["decision_packet"]
    assert packet["schema"] == "figure-agent.release-decision-packet.v1"
    assert packet["packet_kind"] == "force_golden_decision_packet"
    assert "alpha" in packet["human_question"]
    assert packet["recommended_choice_id"] == "defer_for_visual_dogfood"
    assert [choice["id"] for choice in packet["choices"]] == [
        "approve_force_golden_roll_forward",
        "reject_and_keep_current_golden",
        "defer_for_visual_dogfood",
    ]
    assert packet["agent_recommendation"]
    assert packet["evidence_refs"] == [
        "first_blocker:export_tracked_golden",
        "blocking_source:force_golden_required",
        "stop_boundary:force_golden_required",
    ]
    assert packet["follow_up"]["after_decision"] == "rerun /fig_queue --mode release"


def test_human_handoff_includes_choice_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="human_gate_stop",
            stop_boundary="human_gate_required",
            first_blocker="acceptance_not_declared",
            blocking_source="human_gate_required",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="human gate",
        fixtures=None,
        include_command_plan=True,
    )

    packet = queue["command_plan"]["blocked"][0]["operator_handoff"]["decision_packet"]
    assert packet["packet_kind"] == "choice_packet"
    assert packet["recommended_choice_id"] == "accept_current_review_state"
    assert [choice["id"] for choice in packet["choices"]] == [
        "accept_current_review_state",
        "request_bounded_polish_pass",
        "request_redesign_direction",
    ]
    assert "alpha" in packet["human_question"]
    assert packet["risks"]


def test_queue_table_keeps_blocked_handoff_when_driver_guidance_is_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        summary = _summary(
            name,
            action="run_critique",
            stop_boundary="host_llm_critique_required",
            first_blocker="critique_stale",
            safe_command="/fig_critique alpha",
        )
        summary["operator_guidance"] = {
            "schema": "figure-agent.operator-guidance.v1",
            "state": "blocked",
            "required_actor": "host_llm",
            "next_step": "driver guidance should not replace queue handoff",
        }
        return summary

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        fixtures=None,
    )

    fig_queue.print_table(queue)

    table = capsys.readouterr().out
    assert "Refresh stale host-vision critique for this fixture." in table
    assert "driver guidance should not replace queue handoff" not in table


def test_polish_queue_rows_surface_svg_polish_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        assert mode == "polish"
        return _summary(
            name,
            action="run_fig_loop",
            stop_boundary="mode_forbidden_action",
            first_blocker="svg_polish_not_ready",
            svg_polish_gate={
                "state": "blocked",
                "can_start_svg_polish": False,
                "next_action": "rerun_fig_loop",
                "reason": "latest loop recommends continue_tikz",
            },
            svg_polish_readiness={
                "can_start_svg_polish": False,
                "recommended_path": "continue_tikz",
                "next_action": "continue_tikz",
                "blocking_items": [
                    {
                        "source": "tikz_vs_svg_polish_trigger",
                        "reason": "source-level lever remains",
                    }
                ],
            },
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="polish",
        goal="polish triage",
        fixtures=None,
    )

    row = queue["rows"][0]
    assert row["svg_polish_gate_state"] == "blocked"
    assert row["can_start_svg_polish"] is False
    assert row["svg_polish_next_action"] == "rerun_fig_loop"
    assert row["svg_polish_recommended_path"] == "continue_tikz"
    assert row["svg_polish_blocking_sources"] == ["tikz_vs_svg_polish_trigger"]
    assert row["polish_blocker_reason"] == "continue_tikz_recommended"
    assert row["polish_blocker"]["upstream_packet"] == "style_direction_packet"
    assert row["svg_polish_evidence_state"] == "not_qualified"
    evidence = row["svg_polish_evidence_packet"]
    assert evidence["schema"] == fig_queue.SVG_POLISH_EVIDENCE_PACKET_SCHEMA
    assert evidence["missing_prerequisite_reason"] == "continue_tikz_recommended"
    assert evidence["required_positive_evidence"] == [
        "can_start_svg_polish=true",
        "recommended_path=ready_for_svg_polish",
    ]
    assert "semantic repair in SVG" in evidence["forbidden_scope"]


def test_polish_queue_summary_counts_svg_gate_and_blockers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        assert mode == "polish"
        if name == "alpha":
            return _summary(
                name,
                action="run_fig_loop",
                stop_boundary="mode_forbidden_action",
                first_blocker="svg_polish_not_ready",
                svg_polish_gate={
                    "state": "blocked",
                    "can_start_svg_polish": False,
                    "next_action": "rerun_fig_loop",
                },
                svg_polish_readiness={
                    "can_start_svg_polish": False,
                    "recommended_path": "continue_tikz",
                    "next_action": "continue_tikz",
                    "blocking_items": [
                        {"source": "tikz_vs_svg_polish_trigger"},
                        {"source": "crop_audit_summary"},
                    ],
                },
            )
        return _summary(
            name,
            action="polish_handoff_stop",
            stop_boundary=None,
            first_blocker="none",
            svg_polish_gate={
                "state": "ready",
                "can_start_svg_polish": True,
                "next_action": "start_svg_polish_recipe",
            },
            svg_polish_readiness={
                "can_start_svg_polish": True,
                "recommended_path": "ready_for_svg_polish",
                "next_action": "start_svg_polish_recipe",
                "blocking_items": [],
            },
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="polish",
        goal="polish triage",
        fixtures=None,
    )

    assert queue["summary"]["by_svg_polish_gate_state"] == {"blocked": 1, "ready": 1}
    assert queue["summary"]["by_svg_polish_recommended_path"] == {
        "continue_tikz": 1,
        "ready_for_svg_polish": 1,
    }
    assert queue["summary"]["by_svg_polish_next_action"] == {
        "rerun_fig_loop": 1,
        "start_svg_polish_recipe": 1,
    }
    assert queue["summary"]["by_svg_polish_blocking_source"] == {
        "crop_audit_summary": 1,
        "tikz_vs_svg_polish_trigger": 1,
    }
    assert queue["summary"]["by_svg_polish_evidence_state"] == {
        "not_qualified": 1,
        "ready_for_svg_polish": 1,
    }
    assert queue["summary"]["by_polish_blocker_reason"] == {
        "continue_tikz_recommended": 1
    }
    by_fixture = {row["fixture"]: row for row in queue["rows"]}
    assert by_fixture["beta"]["svg_polish_evidence_packet"]["positive_evidence"] == [
        "can_start_svg_polish=true",
        "recommended_path=ready_for_svg_polish",
    ]
    assert by_fixture["alpha"]["svg_polish_evidence_packet"][
        "missing_prerequisite_reason"
    ] == "continue_tikz_recommended"


def test_polish_queue_decomposes_mode_forbidden_prerequisites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "needs_review")
    _write_fixture(tmp_path, "needs_release")
    _write_fixture(tmp_path, "needs_svg_manifest")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        if name == "needs_review":
            return _summary(
                name,
                action="run_critique",
                stop_boundary="mode_forbidden_action",
                first_blocker="critique_stale",
                svg_polish_gate={
                    "state": "blocked",
                    "can_start_svg_polish": False,
                    "next_action": "run_fig_critique",
                    "blocking_items": [{"source": "driver_prerequisite"}],
                },
            )
        if name == "needs_release":
            return _summary(
                name,
                action="run_fig_loop",
                stop_boundary="mode_forbidden_action",
                first_blocker="acceptance_not_declared",
                svg_polish_gate={
                    "state": "blocked",
                    "can_start_svg_polish": False,
                    "next_action": "resolve_release_boundary",
                    "blocking_items": [{"source": "driver_prerequisite"}],
                },
            )
        return _summary(
            name,
            action="polish_handoff_stop",
            stop_boundary="mode_forbidden_action",
            first_blocker="svg_polish_manifest_stale",
            svg_polish_gate={
                "state": "blocked",
                "can_start_svg_polish": False,
                "next_action": "refresh_svg_polish_handoff",
                "blocking_items": [{"source": "svg_polish_manifest"}],
            },
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="polish",
        goal="triage",
        fixtures=None,
        include_command_plan=True,
    )

    reasons = {row["fixture"]: row["polish_blocker_reason"] for row in queue["rows"]}
    assert reasons == {
        "needs_release": "accepted_or_final_ready_missing",
        "needs_review": "review_loop_prerequisite_not_closed",
        "needs_svg_manifest": "svg_polish_artifact_missing_or_stale",
    }
    assert queue["summary"]["by_polish_blocker_reason"] == {
        "accepted_or_final_ready_missing": 1,
        "review_loop_prerequisite_not_closed": 1,
        "svg_polish_artifact_missing_or_stale": 1,
    }
    manifest_handoff = queue["command_plan"]["blocked"][2]["operator_handoff"]
    assert manifest_handoff["polish_blocker"]["reason"] == (
        "svg_polish_artifact_missing_or_stale"
    )
    assert manifest_handoff["svg_polish_evidence_packet"]["state"] == "not_qualified"
    assert manifest_handoff["svg_polish_evidence_packet"]["missing_prerequisite_reason"] == (
        "svg_polish_artifact_missing_or_stale"
    )


def test_polish_queue_filters_ready_svg_polish_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        assert mode == "polish"
        if name == "alpha":
            return _summary(
                name,
                action="run_fig_loop",
                stop_boundary="mode_forbidden_action",
                first_blocker="svg_polish_not_ready",
                svg_polish_gate={
                    "state": "blocked",
                    "can_start_svg_polish": False,
                    "next_action": "rerun_fig_loop",
                },
            )
        return _summary(
            name,
            action="polish_handoff_stop",
            stop_boundary=None,
            first_blocker="none",
            svg_polish_gate={
                "state": "ready",
                "can_start_svg_polish": True,
                "next_action": "start_svg_polish_recipe",
            },
            svg_polish_readiness={
                "can_start_svg_polish": True,
                "recommended_path": "ready_for_svg_polish",
                "next_action": "start_svg_polish_recipe",
                "blocking_items": [],
            },
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="polish",
        goal="polish triage",
        fixtures=None,
        filters={"can_start_svg_polish": "true"},
    )

    assert queue["filters"] == {"can_start_svg_polish": "true"}
    assert queue["unfiltered_total"] == 2
    assert [row["fixture"] for row in queue["rows"]] == ["beta"]
    assert queue["summary"]["by_svg_polish_gate_state"] == {"ready": 1}
    assert queue["summary"]["by_svg_polish_recommended_path"] == {"ready_for_svg_polish": 1}


def test_polish_queue_filters_svg_polish_blocking_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        assert mode == "polish"
        sources = (
            ["tikz_vs_svg_polish_trigger", "crop_audit_summary"]
            if name == "alpha"
            else ["driver_prerequisite"]
        )
        return _summary(
            name,
            action="run_fig_loop",
            stop_boundary="mode_forbidden_action",
            first_blocker="svg_polish_not_ready",
            svg_polish_gate={
                "state": "blocked",
                "can_start_svg_polish": False,
                "next_action": "rerun_fig_loop",
            },
            svg_polish_readiness={
                "can_start_svg_polish": False,
                "recommended_path": "continue_tikz",
                "next_action": "rerun_fig_loop",
                "blocking_items": [{"source": source} for source in sources],
            },
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="polish",
        goal="polish triage",
        fixtures=None,
        filters={"svg_polish_blocking_sources": "tikz_vs_svg_polish_trigger"},
    )

    assert queue["filters"] == {"svg_polish_blocking_sources": "tikz_vs_svg_polish_trigger"}
    assert [row["fixture"] for row in queue["rows"]] == ["alpha"]
    assert queue["summary"]["by_svg_polish_blocking_source"] == {
        "crop_audit_summary": 1,
        "tikz_vs_svg_polish_trigger": 1,
    }


def test_polish_queue_filters_svg_gate_blocking_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        assert mode == "polish"
        source = "driver_blocker" if name == "alpha" else "driver_prerequisite"
        return _summary(
            name,
            action="run_fig_loop",
            stop_boundary="mode_forbidden_action",
            first_blocker="svg_polish_not_ready",
            svg_polish_gate={
                "state": "no_current_checkpoint",
                "can_start_svg_polish": False,
                "next_action": "rerun_fig_loop",
                "blocking_items": [{"source": source, "id": "no_current_checkpoint"}],
            },
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="polish",
        goal="polish triage",
        fixtures=None,
        filters={"svg_polish_blocking_sources": "driver_blocker"},
    )

    assert [row["fixture"] for row in queue["rows"]] == ["alpha"]
    assert queue["rows"][0]["svg_polish_blocking_sources"] == ["driver_blocker"]
    assert queue["summary"]["by_svg_polish_blocking_source"] == {"driver_blocker": 1}


def test_build_queue_records_missing_fixture_as_error(tmp_path: Path) -> None:
    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=["missing"],
    )

    assert queue["summary"]["total"] == 1
    assert queue["summary"]["errors"] == 1
    assert queue["rows"] == [
        {
            "fixture": "missing",
            "mode": "release",
            "action": "error",
            "stop_boundary": "fixture_not_found",
            "first_blocker": "fixture_not_found",
            "safe_command": None,
            "render_state": None,
            "critique_state": None,
            "export_state": None,
            "acceptance_state": None,
            "publication_gate_state": None,
            "release_ready": None,
            "required_actor": "workflow_agent",
            "blocking_source": "fixture_not_found",
            "requires_human": False,
            "bottleneck_category": "mechanical_tool",
            "error": "examples/missing/ not found",
        }
    ]


def test_build_queue_rejects_unsafe_fixture_name_before_driver(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "examples").mkdir()
    (outside / "spec.yaml").write_text("name: outside\n", encoding="utf-8")
    calls: list[str] = []

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        calls.append(name)
        raise AssertionError("unsafe fixture name reached driver")

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        fixtures=["../outside"],
        include_command_plan=True,
    )

    assert calls == []
    assert queue["rows"] == [
        {
            "fixture": "../outside",
            "mode": "review",
            "action": "error",
            "stop_boundary": "unsafe_fixture_name",
            "first_blocker": "unsafe_fixture_name",
            "safe_command": None,
            "render_state": None,
            "critique_state": None,
            "export_state": None,
            "acceptance_state": None,
            "publication_gate_state": None,
            "release_ready": None,
            "required_actor": "workflow_agent",
            "blocking_source": "unsafe_fixture_name",
            "requires_human": False,
            "bottleneck_category": "mechanical_tool",
            "error": "fixture name must be a single examples/<name> directory name",
        }
    ]
    assert queue["command_plan"]["blocked"][0]["reason"] == ("stop_boundary:unsafe_fixture_name")


def test_print_table_outputs_rows_and_summary(capsys: pytest.CaptureFixture[str]) -> None:
    queue = {
        "schema": "figure-agent.fixture-driver-queue.v1",
        "mode": "release",
        "goal": "triage",
        "rows": [
            {
                "fixture": "alpha",
                "mode": "release",
                "action": "run_critique",
                "stop_boundary": "host_llm_critique_required",
                "first_blocker": "critique_stale",
                "safe_command": "/fig_critique alpha",
                "render_state": "FRESH",
                "critique_state": "STALE",
                "export_state": "FRESH",
                "acceptance_state": "NOT_DECLARED",
                "publication_gate_state": "NOT_APPLICABLE",
                "release_ready": False,
                "required_actor": "host_llm",
                "blocking_source": "host_llm_critique_required",
                "requires_human": False,
            }
        ],
        "summary": {
            "total": 1,
            "errors": 0,
            "by_action": {"run_critique": 1},
            "by_stop_boundary": {"host_llm_critique_required": 1},
            "by_first_blocker": {"critique_stale": 1},
            "by_required_actor": {"host_llm": 1},
            "by_blocking_source": {"host_llm_critique_required": 1},
        },
    }

    fig_queue.print_table(queue)

    out = capsys.readouterr().out
    assert "fixture\tactor\taction\tstop_boundary\tfirst_blocker\tnext_step\tnext_command" in out
    assert (
        "alpha\thost_llm\trun_critique\thost_llm_critique_required\t"
        "critique_stale\tRefresh stale host-vision critique for this fixture.\t"
        "/fig_critique alpha"
    ) in out
    assert "summary total=1 errors=0" in out


def test_print_table_outputs_grouped_summary_counts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    queue = {
        "schema": "figure-agent.fixture-driver-queue.v1",
        "mode": "polish",
        "goal": "triage",
        "rows": [],
        "summary": {
            "total": 8,
            "errors": 0,
            "by_action": {"run_critique": 4, "run_compile": 1},
            "by_required_actor": {"host_llm": 4, "workflow_agent": 3},
            "by_svg_polish_next_action": {
                "run_fig_critique": 4,
                "run_fig_compile": 1,
            },
            "by_svg_polish_blocking_source": {
                "driver_prerequisite": 6,
                "driver_blocker": 2,
            },
        },
    }

    fig_queue.print_table(queue)

    out = capsys.readouterr().out
    assert "summary total=8 errors=0" in out
    assert "summary by_action=run_compile:1,run_critique:4" in out
    assert "summary by_required_actor=host_llm:4,workflow_agent:3" in out
    assert "summary by_svg_polish_next_action=run_fig_compile:1,run_fig_critique:4" in out
    assert "summary by_svg_polish_blocking_source=driver_blocker:2,driver_prerequisite:6" in out


def test_print_table_includes_design_direction_summary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    queue = {
        "schema": "figure-agent.fixture-driver-queue.v1",
        "mode": "release",
        "goal": "design-direction-surface",
        "rows": [
            {
                "fixture": "alpha",
                "mode": "release",
                "action": "run_compile",
                "stop_boundary": None,
                "first_blocker": None,
                "safe_command": "/fig_compile alpha",
                "required_actor": "workflow_agent",
                "blocking_source": "driver.action",
                "requires_human": False,
                "design_direction_summary": {
                    "state": "ready_for_human_choice",
                    "default_recommendation": (
                        "keep_current_style_until_candidate_beats_benchmark"
                    ),
                    "mutation_boundary": "no_source_mutation",
                    "evidence_refs": ["style_benchmark_pack:docs/style-benchmark-packs/a.json"],
                },
            }
        ],
        "summary": {"total": 1, "errors": 0},
    }

    fig_queue.print_table(queue)

    out = capsys.readouterr().out
    assert "first_blocker	design_direction	next_step" in out
    assert (
        "ready_for_human_choice; "
        "recommendation=keep_current_style_until_candidate_beats_benchmark; "
        "boundary=no_source_mutation; evidence_refs=1"
    ) in out
    assert "closeout-accept" not in out
    assert "--accept-golden" not in out

def test_print_table_includes_svg_polish_columns_when_present(
    capsys: pytest.CaptureFixture[str],
) -> None:
    queue = {
        "schema": "figure-agent.fixture-driver-queue.v1",
        "mode": "polish",
        "goal": "triage",
        "rows": [
            {
                "fixture": "alpha",
                "mode": "polish",
                "action": "run_fig_loop",
                "stop_boundary": "mode_forbidden_action",
                "first_blocker": "svg_polish_not_ready",
                "safe_command": None,
                "required_actor": "workflow_agent",
                "blocking_source": "mode_forbidden_action",
                "requires_human": False,
                "svg_polish_gate_state": "blocked",
                "can_start_svg_polish": False,
                "svg_polish_next_action": "rerun_fig_loop",
                "svg_polish_recommended_path": "continue_tikz",
                "svg_polish_blocking_sources": ["tikz_vs_svg_polish_trigger"],
            }
        ],
        "summary": {"total": 1, "errors": 0},
    }

    fig_queue.print_table(queue)

    out = capsys.readouterr().out
    assert (
        "fixture\tactor\taction\tstop_boundary\tfirst_blocker\t"
        "svg_gate\tcan_svg\tpolish_path\tpolish_next\tpolish_blockers\t"
        "polish_reason\tsvg_evidence\tnext_step\tnext_command"
    ) in out
    assert (
        "alpha\tworkflow_agent\trun_fig_loop\tmode_forbidden_action\t"
        "svg_polish_not_ready\tblocked\tFalse\tcontinue_tikz\t"
        "rerun_fig_loop\ttikz_vs_svg_polish_trigger\t"
    ) in out


def test_print_table_uses_handoff_command_for_blocked_rows(
    capsys: pytest.CaptureFixture[str],
) -> None:
    queue = {
        "schema": "figure-agent.fixture-driver-queue.v1",
        "mode": "review",
        "goal": "triage",
        "rows": [
            {
                "fixture": "beta",
                "mode": "review",
                "action": "run_export",
                "stop_boundary": "closeout_required",
                "first_blocker": "export_missing",
                "safe_command": "fig-agent export beta",
                "required_actor": "workflow_agent",
                "blocking_source": "closeout_required",
                "requires_human": False,
            }
        ],
        "summary": {"total": 1, "errors": 0},
    }

    fig_queue.print_table(queue)

    out = capsys.readouterr().out
    assert "Run read-only closeout inspection before continuing automation." in out
    assert "fig-agent closeout beta --json" in out
    assert "fig-agent export beta" not in out


def test_main_prints_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    assert (
        fig_queue.main(
            ["--mode", "review", "--goal", "triage", "--json"],
            repo_root=tmp_path,
        )
        == 0
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.fixture-driver-queue.v1"
    assert payload["rows"][0]["fixture"] == "alpha"


def test_main_warns_when_implicit_workspace_has_no_examples(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        fig_queue.main(
            ["--mode", "review", "--goal", "triage", "--json"],
            repo_root=tmp_path,
        )
        == 2
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["summary"] == {
        "total": 0,
        "errors": 0,
        "by_action": {},
        "by_stop_boundary": {},
        "by_first_blocker": {},
        "by_required_actor": {},
        "by_blocking_source": {},
        "by_bottleneck_category": {},
    }
    assert payload["workspace_diagnostic"] == {
        "schema": "figure-agent.queue-workspace-diagnostic.v1",
        "state": "missing_examples",
        "workspace_root": str(tmp_path),
        "missing": ["examples"],
        "message": (
            "implicit queue discovery found no examples/ directory; run from the "
            "figure-agent plugin root or set FIGURE_AGENT_WORKSPACE/CLAUDE_PROJECT_DIR "
            "to a workspace with examples/"
        ),
    }
    assert "implicit queue discovery found no examples/ directory" in captured.err


def test_main_accepts_format_json_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    assert (
        fig_queue.main(
            ["--mode", "review", "--goal", "triage", "--format", "json"],
            repo_root=tmp_path,
        )
        == 0
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.fixture-driver-queue.v1"
    assert payload["rows"][0]["fixture"] == "alpha"


def test_build_queue_filters_by_actor_and_preserves_unfiltered_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        if name == "alpha":
            return _summary(
                name,
                action="run_critique",
                stop_boundary="host_llm_critique_required",
                first_blocker="critique_stale",
            )
        return _summary(
            name,
            action="run_fig_loop",
            stop_boundary=None,
            first_blocker="acceptance_not_declared",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        fixtures=None,
        filters={"required_actor": "host_llm"},
    )

    assert queue["filters"] == {"required_actor": "host_llm"}
    assert queue["unfiltered_total"] == 2
    assert [row["fixture"] for row in queue["rows"]] == ["alpha"]
    assert queue["summary"]["total"] == 1
    assert queue["summary"]["by_required_actor"] == {"host_llm": 1}


def test_build_queue_filters_compose_with_fixture_args(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")
    seen: list[str] = []

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        seen.append(name)
        return _summary(
            name,
            action="release_blocked",
            stop_boundary="force_golden_required",
            first_blocker="export_tracked_golden",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=["beta"],
        filters={"stop_boundary": "force_golden_required"},
    )

    assert seen == ["beta"]
    assert queue["unfiltered_total"] == 1
    assert [row["fixture"] for row in queue["rows"]] == ["beta"]


def test_main_json_accepts_filter_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="run_critique",
            stop_boundary="host_llm_critique_required",
            first_blocker="critique_stale",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    assert (
        fig_queue.main(
            [
                "--mode",
                "review",
                "--goal",
                "triage",
                "--actor",
                "host_llm",
                "--action",
                "run_critique",
                "--json",
            ],
            repo_root=tmp_path,
        )
        == 0
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["filters"] == {
        "action": "run_critique",
        "required_actor": "host_llm",
    }
    assert payload["unfiltered_total"] == 1
    assert payload["rows"][0]["fixture"] == "alpha"


def test_build_queue_can_include_command_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")
    _write_fixture(tmp_path, "gamma")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        if name == "alpha":
            return _summary(
                name,
                action="run_fig_loop",
                stop_boundary=None,
                first_blocker="acceptance_not_declared",
                safe_command="fig-agent loop alpha --goal triage --json",
            )
        if name == "beta":
            return _summary(
                name,
                action="run_export",
                stop_boundary="closeout_required",
                first_blocker="export_missing",
                safe_command="fig-agent export beta",
            )
        return _summary(
            name,
            action="run_critique",
            stop_boundary="host_llm_critique_required",
            first_blocker="critique_stale",
            safe_command="/fig_critique gamma",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        fixtures=None,
        include_command_plan=True,
    )

    assert queue["command_plan"]["schema"] == "figure-agent.fixture-command-plan.v1"
    assert queue["command_plan"]["executable_count"] == 1
    assert queue["command_plan"]["blocked_count"] == 2
    assert queue["command_plan"]["executable"] == [
        {
            "fixture": "alpha",
            "action": "run_fig_loop",
            "safe_command": "fig-agent loop alpha --goal triage --json",
            "required_actor": "workflow_agent",
        }
    ]
    assert [row["fixture"] for row in queue["command_plan"]["blocked"]] == [
        "beta",
        "gamma",
    ]
    assert queue["command_plan"]["blocked"][0]["reason"] == "stop_boundary:closeout_required"
    assert queue["command_plan"]["blocked"][1]["reason"] == "required_actor:host_llm"
    assert queue["command_plan"]["blocked"][0]["operator_handoff"] == {
        "schema": "figure-agent.queue-operator-handoff.v1",
        "fixture": "beta",
        "required_actor": "workflow_agent",
        "next_step": "Run read-only closeout inspection before continuing automation.",
        "command": "fig-agent closeout beta --json",
        "reason": "stop_boundary:closeout_required",
        "allowed_scope": ["read-only closeout inspection"],
        "forbidden_scope": [
            "source edits",
            "export mutation",
            "accepted/golden mutation",
            "publication state mutation",
        ],
        "closeout_checks": [
            "read JSON output even when exit code is 1",
            "follow closeout.next_action",
            "rerun /fig_queue after resolving the blocked row",
        ],
    }
    assert queue["command_plan"]["blocked"][1]["operator_handoff"] == {
        "schema": "figure-agent.queue-operator-handoff.v1",
        "fixture": "gamma",
        "required_actor": "host_llm",
        "handoff_kind": "critique_stale_refresh",
        "first_blocker": "critique_stale",
        "blocking_source": "host_llm_critique_required",
        "bottleneck_category": "host_critique",
        "next_step": "Refresh stale host-vision critique for this fixture.",
        "command": "/fig_critique gamma",
        "reason": "required_actor:host_llm",
        "allowed_scope": [
            "examples/gamma/critique.md",
            "examples/gamma/critique_adjudication.yaml",
            "examples/gamma/build/audit_crops/",
        ],
        "forbidden_scope": [
            "source edits",
            "export mutation",
            "accepted/golden mutation",
            "publication state mutation",
        ],
        "closeout_checks": [
            "run critique_lint",
            "sync or scaffold critique_adjudication.yaml",
            "rerun /fig_queue",
        ],
    }


def test_command_plan_treats_next_action_complete_as_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        summary = _summary(
            name,
            action="run_fig_loop",
            stop_boundary=None,
            first_blocker="acceptance_not_declared",
            safe_command="fig-agent loop alpha --goal triage --json",
            blocking_source="status_action_required",
        )
        summary["next_action_summary"] = {
            "action": "complete",
            "blocking_source": "status_action_required",
            "requires_human": False,
            "safe_command": None,
            "decision_boundary": {
                "schema": "figure-agent.decision-boundary.v1",
                "kind": "none",
                "authority": "none",
                "blocks_progress": False,
                "blocks_release": False,
            },
        }
        return summary

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        fixtures=None,
        include_command_plan=True,
    )

    assert queue["rows"][0]["action"] == "complete"
    assert queue["rows"][0]["driver_action"] == "run_fig_loop"
    assert queue["rows"][0]["safe_command"] is None
    assert queue["command_plan"]["executable_count"] == 0
    assert queue["command_plan"]["blocked_count"] == 0
    assert queue["command_plan"]["complete_count"] == 1
    assert queue["command_plan"]["complete"][0]["fixture"] == "alpha"


def test_host_llm_operator_handoff_separates_reference_context() -> None:
    rows = [
        {
            "fixture": "needs_briefing",
            "action": "run_critique",
            "required_actor": "host_llm",
            "requires_human": False,
            "safe_command": "/fig_critique needs_briefing",
            "blocking_source": "host_llm_critique_required",
            "stop_boundary": "host_llm_critique_required",
            "first_blocker": "critique_briefing_required",
        },
        {
            "fixture": "needs_reference",
            "action": "run_critique",
            "required_actor": "host_llm",
            "requires_human": False,
            "safe_command": None,
            "blocking_source": "reference_missing",
            "stop_boundary": "reference_missing",
            "first_blocker": "reference_missing",
        },
    ]

    plan = fig_queue.build_command_plan(rows)
    briefing = plan["blocked"][0]["operator_handoff"]
    reference = plan["blocked"][1]["operator_handoff"]

    assert briefing["handoff_kind"] == "critique_briefing_required"
    assert briefing["bottleneck_category"] == "reference_context"
    assert briefing["first_blocker"] == "critique_briefing_required"
    assert "briefing/reference context" in briefing["next_step"]
    assert "examples/needs_briefing/reference/" in briefing["allowed_scope"]
    assert (
        "confirm briefing/reference inputs are present before critique"
        in briefing["closeout_checks"]
    )

    assert reference["handoff_kind"] == "reference_context_required"
    assert reference["bottleneck_category"] == "reference_context"
    assert reference["blocking_source"] == "reference_missing"
    assert "Fix declared reference/context inputs" in reference["next_step"]
    assert "examples/needs_reference/spec.yaml" in reference["allowed_scope"]
    assert "confirm reference/context paths resolve before critique" in reference["closeout_checks"]


def test_wave4_mixed_queue_keeps_authority_boundaries() -> None:
    executable_loop_rows = [
        {
            "fixture": name,
            "action": "run_fig_loop",
            "required_actor": "workflow_agent",
            "requires_human": False,
            "safe_command": f"fig-agent loop {name} --goal Wave4 --json",
            "blocking_source": "driver.action",
            "stop_boundary": None,
            "first_blocker": "acceptance_not_declared",
        }
        for name in [
            "fig5_actuation_mechanism",
            "smoke_annotation_box_demo",
            "smoke_contrast_demo",
            "smoke_label_overlap_demo",
            "smoke_leader_line_demo",
            "smoke_panel_spacing_demo",
            "smoke_trap_demo",
        ]
    ]
    rows = [
        *executable_loop_rows,
        {
            "fixture": "_volume_shading_demo",
            "action": "create_or_fix_source",
            "required_actor": "workflow_agent",
            "requires_human": False,
            "safe_command": None,
            "blocking_source": "driver.action",
            "stop_boundary": None,
            "first_blocker": "source_not_authored",
        },
        *[
            {
                "fixture": name,
                "action": "run_critique",
                "required_actor": "host_llm",
                "requires_human": False,
                "safe_command": f"/fig_critique {name}",
                "blocking_source": "host_llm_critique_required",
                "stop_boundary": "host_llm_critique_required",
                "first_blocker": "critique_stale",
            }
            for name in [
                "fig1_overview_v2_pair_001_vault",
                "fig2_trap_design_space",
                "fig3_resistance_mechanism",
            ]
        ],
        *[
            {
                "fixture": name,
                "action": "run_critique",
                "required_actor": "host_llm",
                "requires_human": False,
                "safe_command": f"/fig_critique {name}",
                "blocking_source": "host_llm_critique_required",
                "stop_boundary": "host_llm_critique_required",
                "first_blocker": "critique_briefing_required",
            }
            for name in [
                "fig3_floating_clip_protocol",
                "fig3_trapping_concept",
                "fig4_trap_energy_diagram",
            ]
        ],
    ]

    plan = fig_queue.build_command_plan(rows)
    report = fig_queue.build_bottleneck_report(rows)

    assert plan["executable_count"] == 7
    assert plan["blocked_count"] == 7
    assert [item["fixture"] for item in plan["executable"]] == [
        row["fixture"] for row in executable_loop_rows
    ]
    assert plan["blocked"][0]["fixture"] == "_volume_shading_demo"
    assert plan["blocked"][0]["reason"] == "safe_command:missing"

    host_handoffs = {
        item["fixture"]: item["operator_handoff"]
        for item in plan["blocked"]
        if item["required_actor"] == "host_llm"
    }
    assert host_handoffs["fig1_overview_v2_pair_001_vault"]["handoff_kind"] == (
        "critique_stale_refresh"
    )
    assert host_handoffs["fig2_trap_design_space"]["forbidden_scope"] == [
        "source edits",
        "export mutation",
        "accepted/golden mutation",
        "publication state mutation",
    ]
    assert host_handoffs["fig3_floating_clip_protocol"]["handoff_kind"] == (
        "critique_briefing_required"
    )
    assert (
        "examples/fig3_floating_clip_protocol/spec.yaml"
        in host_handoffs["fig3_floating_clip_protocol"]["allowed_scope"]
    )
    assert (
        "confirm briefing/reference inputs are present before critique"
        in host_handoffs["fig4_trap_energy_diagram"]["closeout_checks"]
    )

    assert report["command_plan"] == {
        "executable": 7,
        "blocked": 7,
        "complete": 0,
    }
    assert report["by_bottleneck_category"] == {
        "mechanical_tool": 8,
        "host_critique": 3,
        "human_acceptance": 0,
        "reference_context": 3,
        "template_style": 0,
    }
    assert report["dominant_first_blocker"] == [
        {"key": "acceptance_not_declared", "count": 7},
        {"key": "critique_briefing_required", "count": 3},
        {"key": "critique_stale", "count": 3},
    ]


def test_command_plan_quotes_closeout_handoff_fixture_names_with_spaces() -> None:
    plan = fig_queue.build_command_plan(
        [
            {
                "fixture": "beta demo",
                "action": "run_export",
                "required_actor": "workflow_agent",
                "safe_command": "fig-agent export 'beta demo'",
                "stop_boundary": "closeout_required",
                "blocking_source": "closeout_required",
                "requires_human": False,
            }
        ]
    )

    assert plan["blocked"][0]["operator_handoff"]["command"] == (
        "fig-agent closeout 'beta demo' --json"
    )


def test_command_plan_prioritizes_stop_boundary_over_missing_command() -> None:
    plan = fig_queue.build_command_plan(
        [
            {
                "fixture": "alpha",
                "action": "run_fig_loop",
                "required_actor": "workflow_agent",
                "safe_command": None,
                "stop_boundary": "mode_forbidden_action",
                "blocking_source": "mode_forbidden_action",
                "requires_human": False,
            }
        ]
    )

    assert plan["blocked"][0]["reason"] == "stop_boundary:mode_forbidden_action"


@pytest.mark.parametrize(
    ("acceptance_state", "export_state", "critique_state"),
    [
        ("ACCEPTED", "MISSING", "FRESH"),
        ("NOT_DECLARED", "TRACKED_GOLDEN", "FRESH"),
        ("NOT_DECLARED", "MISSING", "STALE"),
    ],
)
def test_command_plan_does_not_mark_unsafe_export_rows_executable(
    acceptance_state: str,
    export_state: str,
    critique_state: str,
) -> None:
    plan = fig_queue.build_command_plan(
        [
            {
                "fixture": "beta",
                "action": "run_export",
                "required_actor": "workflow_agent",
                "requires_human": False,
                "safe_command": "fig-agent export beta",
                "stop_boundary": None,
                "blocking_source": "driver.action",
                "acceptance_state": acceptance_state,
                "export_state": export_state,
                "critique_state": critique_state,
            }
        ]
    )

    assert plan["executable"] == []
    assert plan["blocked"][0]["reason"] == "export:safety_predicate_failed"


def test_command_plan_marks_safe_draft_export_row_executable() -> None:
    plan = fig_queue.build_command_plan(
        [
            {
                "fixture": "beta",
                "action": "run_export",
                "required_actor": "workflow_agent",
                "requires_human": False,
                "safe_command": "fig-agent export beta",
                "stop_boundary": None,
                "blocking_source": "driver.action",
                "acceptance_state": "NOT_DECLARED",
                "export_state": "STALE",
                "critique_state": "FRESH",
            }
        ]
    )

    assert plan["blocked"] == []
    assert plan["executable"] == [
        {
            "fixture": "beta",
            "action": "run_export",
            "safe_command": "fig-agent export beta",
            "required_actor": "workflow_agent",
        }
    ]


def test_command_plan_accepts_quoted_safe_draft_export_fixture_with_spaces() -> None:
    plan = fig_queue.build_command_plan(
        [
            {
                "fixture": "beta demo",
                "action": "run_export",
                "required_actor": "workflow_agent",
                "requires_human": False,
                "safe_command": "fig-agent export 'beta demo'",
                "stop_boundary": None,
                "blocking_source": "driver.action",
                "acceptance_state": "NOT_DECLARED",
                "export_state": "MISSING",
                "critique_state": "NOT_REQUIRED",
            }
        ]
    )

    assert plan["blocked"] == []
    assert plan["executable"][0]["safe_command"] == ("fig-agent export 'beta demo'")


def test_command_plan_blocked_handoff_covers_human_and_release_rows(
    tmp_path: Path,
) -> None:
    rows = [
        {
            "fixture": "needs_human",
            "action": "human_gate_stop",
            "required_actor": "human",
            "requires_human": True,
            "safe_command": None,
            "blocking_source": "human_gate_required",
            "stop_boundary": "human_gate_required",
        },
        {
            "fixture": "needs_release",
            "action": "release_blocked",
            "required_actor": "release_operator",
            "requires_human": True,
            "safe_command": None,
            "blocking_source": "force_golden_required",
            "stop_boundary": "force_golden_required",
        },
    ]

    plan = fig_queue.build_command_plan(rows)

    assert plan["blocked"][0]["operator_handoff"]["next_step"] == (
        "Record the required human decision before continuing automation."
    )
    assert plan["blocked"][0]["operator_handoff"]["command"] is None
    assert plan["blocked"][1]["operator_handoff"]["next_step"] == (
        "Review the fixture-specific release decision packet; do not force golden "
        "or acceptance implicitly."
    )
    assert plan["blocked"][1]["operator_handoff"]["command"] is None


def test_command_plan_uses_filtered_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="run_fig_loop",
            stop_boundary=None,
            first_blocker="acceptance_not_declared",
            safe_command=f"fig-agent loop {name} --goal triage --json",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        fixtures=None,
        filters={"action": "run_critique"},
        include_command_plan=True,
    )

    assert queue["unfiltered_total"] == 2
    assert queue["rows"] == []
    assert queue["command_plan"]["executable"] == []
    assert queue["command_plan"]["blocked"] == []


def test_main_commands_prints_executable_commands_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        if name == "alpha":
            return _summary(
                name,
                action="run_fig_loop",
                stop_boundary=None,
                first_blocker="acceptance_not_declared",
                safe_command="fig-agent loop alpha --goal triage --json",
            )
        return _summary(
            name,
            action="human_gate_stop",
            stop_boundary="human_gate_required",
            first_blocker="not_accepted",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    assert (
        fig_queue.main(
            ["--mode", "review", "--goal", "triage", "--commands"],
            repo_root=tmp_path,
        )
        == 0
    )

    assert capsys.readouterr().out.splitlines() == ["fig-agent loop alpha --goal triage --json"]


def test_wrapper_queue_from_parent_uses_plugin_examples() -> None:
    env = os.environ.copy()
    env.pop("FIGURE_AGENT_WORKSPACE", None)
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("FIGURE_AGENT_PLUGIN_ROOT", None)
    env.pop("CLAUDE_PLUGIN_ROOT", None)

    result = subprocess.run(
        [
            str(Path("figure-agent") / "bin" / "fig-agent"),
            "queue",
            "--mode",
            "review",
            "--goal",
            "cwd trap regression",
            "--json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["unfiltered_total"] > 0
    assert payload["summary"]["total"] > 0


def test_human_decision_digest_groups_queue_packets_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in [
        "accept_me",
        "force_golden_fixture",
        "fig5_actuation_mechanism",
        "needs_svg_evidence",
    ]:
        _write_fixture(tmp_path, name)

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        if name == "force_golden_fixture":
            return _summary(
                name,
                action="release_blocked",
                stop_boundary="force_golden_required",
                first_blocker="export_tracked_golden",
                blocking_source="force_golden_required",
            )
        if name == "needs_svg_evidence":
            return _summary(
                name,
                action="polish_handoff_stop",
                stop_boundary="mode_forbidden_action",
                first_blocker="svg_polish_manifest_stale",
                svg_polish_gate={
                    "state": "blocked",
                    "can_start_svg_polish": False,
                    "next_action": "refresh_svg_polish_handoff",
                    "blocking_items": [{"source": "svg_polish_manifest"}],
                },
            )
        return _summary(
            name,
            action="release_blocked",
            stop_boundary="accepted_or_final_ready_required",
            first_blocker="acceptance_not_declared",
            blocking_source="accepted_or_final_ready_required",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="polish",
        goal="decision-dogfood",
        fixtures=None,
    )
    digest = fig_queue.build_human_decision_digest(queue)

    assert digest["schema"] == "figure-agent.human-decision-digest.v1"
    assert digest["source"] == "live fig_queue rows"
    assert digest["safety"] == {
        "source_mutation": False,
        "release_state_mutation": False,
        "golden_mutation": False,
    }
    assert digest["packet_schemas"] == [
        "figure-agent.release-decision-packet.v1",
        "figure-agent.style-direction-packet.v1",
    ]
    groups = {group["id"]: group for group in digest["groups"]}
    assert [row["fixture"] for row in groups["accept_current_candidates"]["rows"]] == [
        "accept_me"
    ]
    assert groups["accept_current_candidates"]["rows"][0]["packet_schemas"] == [
        "figure-agent.release-decision-packet.v1",
        "figure-agent.style-direction-packet.v1",
    ]
    assert groups["redesign_benchmark_candidates"]["rows"][0]["fixture"] == (
        "force_golden_fixture"
    )
    assert groups["svg_polish_evidence_missing"]["rows"][0]["fixture"] == (
        "needs_svg_evidence"
    )
    assert groups["dirty_stale_fixtures_excluded"]["rows"][0]["fixture"] == (
        "fig5_actuation_mechanism"
    )
    assert "explicitly targets" in groups["dirty_stale_fixtures_excluded"]["next_action"]


def test_human_decision_digest_does_not_exclude_targeted_fig5(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "fig5_actuation_mechanism")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="release_blocked",
            stop_boundary="accepted_or_final_ready_required",
            first_blocker="acceptance_not_declared",
            blocking_source="accepted_or_final_ready_required",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="decision-dogfood",
        fixtures=["fig5_actuation_mechanism"],
    )
    digest = fig_queue.build_human_decision_digest(
        queue,
        targeted_fixtures=["fig5_actuation_mechanism"],
    )

    groups = {group["id"]: group for group in digest["groups"]}
    assert groups["dirty_stale_fixtures_excluded"]["rows"] == []
    assert [row["fixture"] for row in groups["accept_current_candidates"]["rows"]] == [
        "fig5_actuation_mechanism"
    ]


def test_main_outputs_human_decision_digest_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="release_blocked",
            stop_boundary="accepted_or_final_ready_required",
            first_blocker="acceptance_not_declared",
            blocking_source="accepted_or_final_ready_required",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    assert (
        fig_queue.main(
            [
                "--mode",
                "release",
                "--goal",
                "decision-dogfood",
                "--human-decision-digest",
                "--json",
            ],
            repo_root=tmp_path,
        )
        == 0
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.human-decision-digest.v1"
    assert payload["groups"][0]["id"] == "accept_current_candidates"
    assert payload["groups"][0]["rows"][0]["fixture"] == "alpha"


def test_main_outputs_human_decision_digest_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="release_blocked",
            stop_boundary="accepted_or_final_ready_required",
            first_blocker="acceptance_not_declared",
            blocking_source="accepted_or_final_ready_required",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    assert (
        fig_queue.main(
            [
                "--mode",
                "release",
                "--goal",
                "decision-dogfood",
                "--human-decision-digest",
            ],
            repo_root=tmp_path,
        )
        == 0
    )

    out = capsys.readouterr().out
    assert "human_decision_digest mode=release total=1 digest_rows=1" in out
    assert "accept-current candidates (1)" in out
    assert "- alpha: recommend=accept_current_generated_export" in out


def test_queue_row_surfaces_compact_style_benchmark_pack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    def fake_load_pack(name: str, *, workspace_root: Path) -> dict[str, Any]:
        assert name == "alpha"
        assert workspace_root == tmp_path
        return {
            "schema": fig_queue.style_benchmark_pack.SCHEMA,
            "state": "present",
            "fixture": "alpha",
            "path": "docs/style-benchmark-packs/wave/alpha.json",
            "linked_files": {
                "source_decision_packet": "docs/decision-packets/wave/alpha.json",
                "source_decision_record": "docs/decision-records/wave/alpha.json",
                "benchmark_contract": "examples/alpha/benchmark_contract.yaml",
                "aesthetic_intent": "examples/alpha/aesthetic_intent.yaml",
            },
            "target_style_class": "restrained editorial multipanel scientific schematic",
            "default_recommendation": "keep_current_style_until_candidate_beats_benchmark",
            "candidate_family_slots": [
                {"id": "current_style", "mutation_boundary": "no_source_mutation"},
                {
                    "id": "restrained_tikz_refinement",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                },
                {
                    "id": "editorial_redesign",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                },
                {
                    "id": "svg_polish_handoff",
                    "mutation_boundary": "svg_artifact_mutation_requires_separate_approval",
                },
            ],
            "human_only_questions": [
                "Does the candidate improve journal fit?",
                "Is the current style sufficient?",
                "Should this become flagship-level?",
                "Do not copy this fourth question into compact output.",
            ],
            "safety": {
                "source_mutation": False,
                "accepted_state_mutation": False,
                "release_state_mutation": False,
                "generated_export_mutation": False,
                "golden_mutation": False,
                "svg_polish_default": False,
            },
        }

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    monkeypatch.setattr(fig_queue.style_benchmark_pack, "load_pack", fake_load_pack)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="style-benchmark-surface",
        fixtures=None,
        include_command_plan=True,
    )

    row = queue["rows"][0]
    assert row["style_benchmark_pack_state"] == "present"
    summary = row["style_benchmark_pack"]
    assert summary == row["style_direction_packet"]["style_benchmark_pack"]
    assert summary["target_style_class"] == (
        "restrained editorial multipanel scientific schematic"
    )
    assert summary["default_recommendation"] == (
        "keep_current_style_until_candidate_beats_benchmark"
    )
    assert summary["candidate_slot_ids"] == [
        "current_style",
        "restrained_tikz_refinement",
        "editorial_redesign",
        "svg_polish_handoff",
    ]
    assert summary["candidate_mutation_boundaries"]["current_style"] == (
        "no_source_mutation"
    )
    assert summary["linked_files"] == {
        "benchmark_contract": "examples/alpha/benchmark_contract.yaml",
        "aesthetic_intent": "examples/alpha/aesthetic_intent.yaml",
    }
    assert summary["top_human_only_questions"] == [
        "Does the candidate improve journal fit?",
        "Is the current style sufficient?",
        "Should this become flagship-level?",
    ]
    assert summary["safety_boundary"] == {
        "source_mutation": False,
        "accepted_state_mutation": False,
        "release_state_mutation": False,
        "generated_export_mutation": False,
        "golden_mutation": False,
        "svg_polish_default": False,
    }
    assert "measurable_checks" not in summary
    assert queue["summary"]["by_style_benchmark_pack_state"] == {"present": 1}
    assert queue["command_plan"]["complete"][0]["style_benchmark_pack_state"] == "present"


def test_queue_row_surfaces_style_comparison_editorial_handoff_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    def fake_load_pack(name: str, *, workspace_root: Path) -> dict[str, Any]:
        assert name == "alpha"
        assert workspace_root == tmp_path
        return {
            "schema": fig_queue.style_benchmark_pack.SCHEMA,
            "state": "present",
            "fixture": "alpha",
            "path": "docs/style-benchmark-packs/wave/alpha.json",
            "linked_files": {},
            "target_style_class": "restrained editorial multipanel scientific schematic",
            "default_recommendation": "keep_current_style_until_candidate_beats_benchmark",
            "candidate_family_slots": [
                {"id": "current_style", "mutation_boundary": "no_source_mutation"},
                {
                    "id": "restrained_tikz_refinement",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                },
                {
                    "id": "editorial_redesign",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                },
                {
                    "id": "svg_polish_handoff",
                    "mutation_boundary": "svg_artifact_mutation_requires_separate_approval",
                },
            ],
            "human_only_questions": [],
            "safety": {
                "source_mutation": False,
                "accepted_state_mutation": False,
                "release_state_mutation": False,
                "generated_export_mutation": False,
                "golden_mutation": False,
                "svg_polish_default": False,
            },
        }

    def fake_load_comparison(name: str, *, workspace_root: Path) -> dict[str, Any]:
        assert name == "alpha"
        assert workspace_root == tmp_path
        return {
            "schema": fig_queue.style_benchmark_comparison.SCHEMA,
            "fixture": "alpha",
            "path": "docs/style-benchmark-comparisons/wave/alpha.json",
            "human_style_decision": "keep_current_style",
            "target_style_class": "restrained editorial multipanel scientific schematic",
            "default_recommendation": "keep_current_style_until_candidate_beats_benchmark",
            "forbidden_semantic_changes": [
                "do not change panel roles",
                "do not rename labels",
            ],
            "benchmark_measurable_checks": ["style_lock_typography remains clean"],
            "human_only_questions": [
                "Does the candidate improve journal fit?",
                "Does it feel editorial?",
                "Should this become flagship-level?",
                "Do not surface this fourth question.",
            ],
            "candidate_family_comparisons": [
                {
                    "id": "current_style",
                    "result": "winner_candidate",
                    "mutation_boundary": "no_source_mutation",
                },
                {
                    "id": "restrained_tikz_refinement",
                    "result": "blocked_requires_separate_approval",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                },
                {
                    "id": "editorial_redesign",
                    "result": "eligible",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                },
                {
                    "id": "svg_polish_handoff",
                    "result": "blocked_missing_evidence",
                    "mutation_boundary": "svg_artifact_mutation_requires_separate_approval",
                },
            ],
        }

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    monkeypatch.setattr(fig_queue.style_benchmark_pack, "load_pack", fake_load_pack)
    monkeypatch.setattr(
        fig_queue.style_benchmark_comparison, "load_comparison", fake_load_comparison
    )

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="style-comparison-surface",
        fixtures=None,
        include_command_plan=True,
    )

    row = queue["rows"][0]
    assert row["style_benchmark_comparison_state"] == "present"
    comparison = row["style_benchmark_comparison"]
    assert comparison == row["style_direction_packet"]["style_benchmark_comparison"]
    assert comparison["candidate_results"]["editorial_redesign"] == "eligible"
    assert comparison["candidate_handoff_states"]["editorial_redesign"] == "handoff_only"
    assert comparison["candidate_results"]["svg_polish_handoff"] == "blocked_missing_evidence"
    assert comparison["candidate_handoff_states"]["svg_polish_handoff"] == "handoff_blocked"
    assert comparison["candidate_mutation_boundaries"]["editorial_redesign"] == (
        "source_mutation_requires_separate_approval"
    )
    assert comparison["top_human_only_questions"] == [
        "Does the candidate improve journal fit?",
        "Does it feel editorial?",
        "Should this become flagship-level?",
    ]
    assert comparison["safety_boundary"] == {
        "source_mutation": False,
        "semantic_change": False,
        "accepted_state_mutation": False,
        "release_state_mutation": False,
        "generated_export_mutation": False,
        "golden_mutation": False,
    }
    assert queue["summary"]["by_style_benchmark_comparison_state"] == {"present": 1}
    assert queue["command_plan"]["complete"][0]["style_benchmark_comparison_state"] == "present"


def test_queue_row_surfaces_missing_style_comparison_without_failing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    def fake_load_comparison(name: str, *, workspace_root: Path) -> dict[str, Any]:
        assert workspace_root == tmp_path
        raise fig_queue.style_benchmark_comparison.StyleBenchmarkComparisonError(
            "comparison_missing"
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    monkeypatch.setattr(
        fig_queue.style_benchmark_comparison, "load_comparison", fake_load_comparison
    )

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="style-comparison-surface",
        fixtures=None,
    )

    row = queue["rows"][0]
    assert row["style_benchmark_comparison_state"] == "missing"
    assert "style_benchmark_comparison" not in row
    assert "style_benchmark_comparison" not in row["style_direction_packet"]
    assert queue["summary"]["by_style_benchmark_comparison_state"] == {"missing": 1}


def test_malformed_style_comparison_is_invalid_not_editorial_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    def fake_load_comparison(name: str, *, workspace_root: Path) -> dict[str, Any]:
        assert workspace_root == tmp_path
        raise fig_queue.style_benchmark_comparison.StyleBenchmarkComparisonError("schema_invalid")

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    monkeypatch.setattr(
        fig_queue.style_benchmark_comparison, "load_comparison", fake_load_comparison
    )

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="style-comparison-surface",
        fixtures=None,
    )

    row = queue["rows"][0]
    assert row["style_benchmark_comparison_state"] == "invalid"
    assert row["style_benchmark_comparison_error"] == "schema_invalid"
    assert "style_benchmark_comparison" not in row
    assert "style_benchmark_comparison" not in row["style_direction_packet"]
    assert queue["summary"]["by_style_benchmark_comparison_state"] == {"invalid": 1}


def test_queue_row_surfaces_missing_style_benchmark_pack_without_failing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    def fake_load_pack(name: str, *, workspace_root: Path) -> dict[str, Any]:
        assert workspace_root == tmp_path
        return {
            "schema": fig_queue.style_benchmark_pack.SCHEMA,
            "state": "missing",
            "fixture": name,
            "path": "docs/style-benchmark-packs/2026-06-30-wave-c/alpha.json",
        }

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    monkeypatch.setattr(fig_queue.style_benchmark_pack, "load_pack", fake_load_pack)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="style-benchmark-surface",
        fixtures=None,
    )

    row = queue["rows"][0]
    assert row["style_benchmark_pack_state"] == "missing"
    assert "style_benchmark_pack" not in row
    assert "style_benchmark_pack" not in row["style_direction_packet"]
    assert queue["summary"]["by_style_benchmark_pack_state"] == {"missing": 1}


def test_malformed_style_benchmark_pack_is_invalid_not_recommendation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    def fake_load_pack(name: str, *, workspace_root: Path) -> dict[str, Any]:
        assert workspace_root == tmp_path
        raise fig_queue.style_benchmark_pack.StyleBenchmarkPackError("schema_invalid")

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    monkeypatch.setattr(fig_queue.style_benchmark_pack, "load_pack", fake_load_pack)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="style-benchmark-surface",
        fixtures=None,
    )

    row = queue["rows"][0]
    assert row["style_benchmark_pack_state"] == "invalid"
    assert row["style_benchmark_pack_error"] == "schema_invalid"
    assert "style_benchmark_pack" not in row
    assert "style_benchmark_pack" not in row["style_direction_packet"]
    assert queue["summary"]["by_style_benchmark_pack_state"] == {"invalid": 1}


def test_queue_surfaces_design_direction_ready_human_choice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    monkeypatch.setattr(
        fig_queue.style_benchmark_pack,
        "load_pack",
        lambda name, *, workspace_root: {
            "state": "present",
            "path": "docs/style-benchmark-packs/alpha.json",
            "candidate_family_slots": [
                {
                    "id": "current_style",
                    "mutation_boundary": "no_source_mutation",
                },
                {
                    "id": "restrained_tikz_refinement",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                },
                {
                    "id": "editorial_redesign",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                },
                {
                    "id": "svg_polish_handoff",
                    "mutation_boundary": "svg_artifact_mutation_requires_separate_approval",
                },
            ],
            "linked_files": {
                "benchmark_contract": "docs/benchmarks/alpha.yaml",
                "aesthetic_intent": "docs/aesthetic-intents/alpha.yaml",
            },
        },
    )
    monkeypatch.setattr(
        fig_queue.style_benchmark_comparison,
        "load_comparison",
        lambda name, *, workspace_root: {
            "state": "present",
            "path": "docs/style-benchmark-comparisons/alpha.json",
            "default_recommendation": "keep_current_style_until_candidate_beats_benchmark",
            "candidate_family_comparisons": [
                {
                    "id": "current_style",
                    "result": "winner_candidate",
                    "mutation_boundary": "no_source_mutation",
                },
                {
                    "id": "restrained_tikz_refinement",
                    "result": "eligible",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                },
                {
                    "id": "editorial_redesign",
                    "result": "eligible",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                },
                {
                    "id": "svg_polish_handoff",
                    "result": "blocked_missing_evidence",
                    "mutation_boundary": "svg_artifact_mutation_requires_separate_approval",
                },
            ],
        },
    )

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="design-direction-surfacing",
        fixtures=None,
        include_command_plan=True,
    )

    row = queue["rows"][0]
    assert row["design_direction_state"] == "ready_for_human_choice"
    assert row["design_direction_packet_schema"] == "figure-agent.design-direction-packet.v1"
    assert row["design_direction_default"] == (
        "keep_current_style_until_candidate_beats_benchmark"
    )
    assert row["design_direction_next_agent_action"] == (
        "prepare_bounded_candidate_or_stop_for_human_choice"
    )
    assert row["design_direction_alternatives"] == [
        "current_style",
        "restrained_tikz_refinement",
        "editorial_redesign",
        "svg_polish_handoff",
    ]
    assert row["design_direction_mutation_boundary"] == "no_source_mutation"
    assert row["design_direction_alternative_mutation_boundaries"] == {
        "current_style": "no_source_mutation",
        "restrained_tikz_refinement": "source_mutation_requires_separate_approval",
        "editorial_redesign": "source_mutation_requires_separate_approval",
        "svg_polish_handoff": "svg_artifact_mutation_requires_separate_approval",
    }
    assert row["design_direction_evidence_refs"] == [
        "style_benchmark_pack:docs/style-benchmark-packs/alpha.json",
        "benchmark_contract:docs/benchmarks/alpha.yaml",
        "aesthetic_intent:docs/aesthetic-intents/alpha.yaml",
        "style_benchmark_comparison:docs/style-benchmark-comparisons/alpha.json",
    ]
    assert row["design_direction_human_question"].startswith("I recommend keeping")
    assert row["bottleneck_category"] == "template_style"
    assert row["required_actor"] == "human"
    assert queue["summary"]["by_design_direction_state"] == {"ready_for_human_choice": 1}
    assert queue["command_plan"]["executable_count"] == 0


@pytest.mark.parametrize(
    ("pack_state", "comparison_state", "expected_state", "expected_blocker"),
    [
        ("missing", "present", "blocked_missing_style_pack", "style_benchmark_pack_missing"),
        ("present", "missing", "blocked_missing_comparison", "style_benchmark_comparison_missing"),
    ],
)
def test_queue_surfaces_design_direction_blockers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pack_state: str,
    comparison_state: str,
    expected_state: str,
    expected_blocker: str,
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    monkeypatch.setattr(
        fig_queue.style_benchmark_pack,
        "load_pack",
        lambda name, *, workspace_root: {"state": pack_state},
    )
    monkeypatch.setattr(
        fig_queue.style_benchmark_comparison,
        "load_comparison",
        lambda name, *, workspace_root: {"state": comparison_state},
    )

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="design-direction-surfacing",
        fixtures=None,
    )

    row = queue["rows"][0]
    assert row["design_direction_state"] == expected_state
    assert row["design_direction_blocker_reason"] == expected_blocker
    assert row["design_direction_summary"]["mutation_boundary"] == "no_source_mutation"
    assert row["design_direction_summary"]["blocking_reasons"] == [expected_blocker]
    assert "command" not in row["design_direction_summary"]
    assert row["bottleneck_category"] == "template_style"



def test_human_decision_digest_includes_design_direction_surface(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="run_compile", stop_boundary=None, first_blocker="none")

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    monkeypatch.setattr(
        fig_queue.style_benchmark_pack,
        "load_pack",
        lambda name, *, workspace_root: {
            "state": "present",
            "path": "docs/style-benchmark-packs/wave/alpha.json",
            "linked_files": {
                "benchmark_contract": "examples/alpha/benchmark_contract.yaml",
                "aesthetic_intent": "examples/alpha/aesthetic_intent.yaml",
            },
        },
    )
    monkeypatch.setattr(
        fig_queue.style_benchmark_comparison,
        "load_comparison",
        lambda name, *, workspace_root: {
            "state": "present",
            "path": "docs/style-benchmark-comparisons/wave/alpha.json",
            "default_recommendation": "keep_current_style_until_candidate_beats_benchmark",
        },
    )

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="design-direction-surface",
        fixtures=None,
    )

    digest = queue["human_decision_digest"]
    assert digest["packet_schemas"] == ["figure-agent.design-direction-packet.v1"]
    groups = {group["id"]: group for group in digest["groups"]}
    rows = groups["accept_current_candidates"]["rows"]
    assert [row["fixture"] for row in rows] == ["alpha"]
    row = rows[0]
    assert row["packet_recommendations"] == [
        {
            "packet": "figure-agent.design-direction-packet.v1",
            "recommendation": "keep_current_style_until_candidate_beats_benchmark",
        }
    ]
    assert row["design_direction_state"] == "ready_for_human_choice"
    assert row["design_direction_mutation_boundary"] == "no_source_mutation"
    assert row["design_direction_alternatives"] == [
        "current_style",
        "restrained_tikz_refinement",
        "editorial_redesign",
        "svg_polish_handoff",
    ]
    assert row["design_direction_evidence_refs"] == [
        "style_benchmark_pack:docs/style-benchmark-packs/wave/alpha.json",
        "benchmark_contract:examples/alpha/benchmark_contract.yaml",
        "aesthetic_intent:examples/alpha/aesthetic_intent.yaml",
        "style_benchmark_comparison:docs/style-benchmark-comparisons/wave/alpha.json",
    ]
    assert all("fig-agent " not in ref for ref in row["design_direction_evidence_refs"])

def test_polish_queue_surfaces_svg_polish_evidence_missing_as_design_blocker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="human_gate_stop",
            stop_boundary="mode_forbidden",
            first_blocker="svg_polish_not_ready",
            svg_polish_gate={
                "state": "blocked",
                "can_start_svg_polish": False,
                "recommended_path": "continue_tikz",
                "next_action": "run_fig_critique",
                "blocking_sources": ["driver_prerequisite"],
            },
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)
    monkeypatch.setattr(
        fig_queue.style_benchmark_pack,
        "load_pack",
        lambda name, *, workspace_root: {"state": "present"},
    )
    monkeypatch.setattr(
        fig_queue.style_benchmark_comparison,
        "load_comparison",
        lambda name, *, workspace_root: {"state": "present"},
    )

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="polish",
        goal="design-direction-surfacing",
        fixtures=None,
    )

    row = queue["rows"][0]
    assert row["svg_polish_evidence_state"] == "not_qualified"
    assert row["design_direction_state"] == "ready_for_human_choice"
    assert row["design_direction_blocker_reason"] == "svg_polish_evidence_missing"
