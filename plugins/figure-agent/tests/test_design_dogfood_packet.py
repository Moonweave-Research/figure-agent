# ruff: noqa: E402, I001

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import design_dogfood_packet  # noqa: E402


FIXTURE = "fig3_trapping_concept"


def _queue_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "fixture": FIXTURE,
        "mode": "review",
        "action": "complete",
        "first_blocker": "acceptance_not_declared",
        "render_state": "FRESH",
        "critique_state": "FRESH",
        "export_state": "FRESH",
        "style_benchmark_pack_state": "missing",
        "style_benchmark_comparison_state": "missing",
        "design_direction_state": "blocked_missing_style_pack",
        "design_direction_next_agent_action": "create_style_benchmark_pack",
        "style_direction_packet": {
            "agent_recommendation": "keep_current_style_with_optional_bounded_tikz_polish",
            "recommended_choice_id": "keep_current_style",
            "choices": [
                {
                    "id": "keep_current_style",
                    "label": "Keep current style",
                    "next_slice": "proceed to release queue",
                    "risk": "may remain solid-manuscript rather than flagship polish",
                    "scope_change": False,
                },
                {
                    "id": "bounded_tikz_source_polish",
                    "label": "Bounded TikZ source polish",
                    "next_slice": "open one targeted typography/spacing/stroke polish task",
                    "risk": "can improve hierarchy but should stay one local pass",
                    "scope_change": False,
                },
                {
                    "id": "svg_polish_handoff",
                    "label": "SVG polish handoff",
                    "next_slice": "run polish queue and require can_start_svg_polish=true",
                    "risk": "requires positive ready_for_svg_polish evidence",
                    "scope_change": True,
                },
                {
                    "id": "full_style_redesign",
                    "label": "Full style redesign",
                    "next_slice": "create redesign alternatives against the benchmark fixture",
                    "risk": "changes visual language and needs benchmark comparison",
                    "scope_change": True,
                },
            ],
        },
    }
    row.update(overrides)
    return row


def _queue(*rows: dict[str, object]) -> dict[str, object]:
    return {"schema": "figure-agent.fixture-driver-queue.v1", "rows": list(rows)}


def _run_fig_agent(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(PLUGIN_ROOT)
    return subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), "python", str(FIG_AGENT), *args],
        cwd=PLUGIN_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_packet_builder_turns_style_direction_into_human_options() -> None:
    packet = design_dogfood_packet.build_design_dogfood_packet(
        FIXTURE,
        queue=_queue(_queue_row()),
        mode="review",
    )

    assert packet["schema"] == design_dogfood_packet.SCHEMA
    assert packet["fixture"] == FIXTURE
    assert packet["state"] == "ready_for_human_choice"
    assert packet["mutation_boundary"] == "no_source_mutation"
    assert packet["recommended_choice_id"] == "keep_current_style"
    assert "I recommend" in packet["human_question"]
    assert len(packet["choices"]) == 4
    assert [choice["id"] for choice in packet["choices"]] == [
        "keep_current_style",
        "bounded_tikz_source_polish",
        "svg_polish_handoff",
        "full_style_redesign",
    ]
    assert all(choice["authorizes_mutation"] is False for choice in packet["choices"])
    assert all("agent_position" in choice for choice in packet["choices"])
    assert all("follow_up" in choice for choice in packet["choices"])


def test_missing_style_benchmark_evidence_is_visible() -> None:
    packet = design_dogfood_packet.build_design_dogfood_packet(
        FIXTURE,
        queue=_queue(_queue_row()),
        mode="review",
    )

    assert packet["missing_evidence"] == [
        {
            "id": "style_benchmark_pack",
            "state": "missing",
            "next_agent_action": "create_style_benchmark_pack",
        },
        {
            "id": "style_benchmark_comparison",
            "state": "missing",
            "next_agent_action": "create_style_benchmark_comparison",
        },
        {
            "id": "design_direction",
            "state": "blocked_missing_style_pack",
            "next_agent_action": "create_style_benchmark_pack",
        },
    ]
    redesign = next(
        choice for choice in packet["choices"] if choice["id"] == "full_style_redesign"
    )
    assert "style benchmark" in redesign["follow_up"].lower()


def test_empty_queue_blocks_without_mutation_authority() -> None:
    packet = design_dogfood_packet.build_design_dogfood_packet(
        FIXTURE,
        queue=_queue(),
        mode="review",
    )

    assert packet["state"] == "blocked_missing_queue_row"
    assert packet["choices"] == []
    assert packet["mutation_boundary"] == "no_source_mutation"
    assert packet["disallowed_actions"]


def test_fig_agent_design_dogfood_cli_reads_live_fig3_queue() -> None:
    result = _run_fig_agent("design-dogfood", FIXTURE, "--json")

    assert result.returncode == 0, result.stderr
    packet = json.loads(result.stdout)
    assert packet["schema"] == design_dogfood_packet.SCHEMA
    assert packet["fixture"] == FIXTURE
    assert packet["state"] == "ready_for_human_choice"
    assert packet["mutation_boundary"] == "no_source_mutation"
    assert packet["missing_evidence"]
    assert all(choice["authorizes_mutation"] is False for choice in packet["choices"])
