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
            "publication_gate_state": "NOT_APPLICABLE",
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
    assert queue["summary"]["by_svg_polish_recommended_path"] == {
        "ready_for_svg_polish": 1
    }


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

    assert queue["filters"] == {
        "svg_polish_blocking_sources": "tikz_vs_svg_polish_trigger"
    }
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
    assert queue["command_plan"]["blocked"][0]["reason"] == (
        "stop_boundary:unsafe_fixture_name"
    )


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
    assert (
        "fixture\tactor\taction\tstop_boundary\tfirst_blocker\tnext_step\tnext_command"
        in out
    )
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
    assert (
        "summary by_svg_polish_blocking_source=driver_blocker:2,driver_prerequisite:6"
        in out
    )


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
        "next_step\tnext_command"
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

    assert fig_queue.main(
        ["--mode", "review", "--goal", "triage", "--json"],
        repo_root=tmp_path,
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.fixture-driver-queue.v1"
    assert payload["rows"][0]["fixture"] == "alpha"




def test_main_warns_when_implicit_workspace_has_no_examples(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert fig_queue.main(
        ["--mode", "review", "--goal", "triage", "--json"],
        repo_root=tmp_path,
    ) == 2

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

    assert fig_queue.main(
        ["--mode", "review", "--goal", "triage", "--format", "json"],
        repo_root=tmp_path,
    ) == 0

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

    assert fig_queue.main(
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
    ) == 0

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
    assert "examples/fig3_floating_clip_protocol/spec.yaml" in host_handoffs[
        "fig3_floating_clip_protocol"
    ]["allowed_scope"]
    assert "confirm briefing/reference inputs are present before critique" in host_handoffs[
        "fig4_trap_energy_diagram"
    ]["closeout_checks"]

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
    assert plan["executable"][0]["safe_command"] == (
        "fig-agent export 'beta demo'"
    )


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
        "Perform explicit release/golden review; do not force golden implicitly."
    )
    assert plan["blocked"][1]["operator_handoff"]["command"] is None


def test_command_plan_uses_filtered_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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

    assert fig_queue.main(
        ["--mode", "review", "--goal", "triage", "--commands"],
        repo_root=tmp_path,
    ) == 0

    assert capsys.readouterr().out.splitlines() == [
        "fig-agent loop alpha --goal triage --json"
    ]


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
