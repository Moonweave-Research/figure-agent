# ruff: noqa: E402, I001

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import bounded_tikz_refinement_packet  # noqa: E402


FIXTURE = "fig3_trapping_concept"


def _style_pack(**overrides: object) -> dict[str, object]:
    pack: dict[str, object] = {
        "state": "present",
        "target_style_class": "restrained two-panel scientific mechanism schematic",
        "candidate_family_slots": [
            {
                "id": "current_style",
                "mutation_boundary": "no_source_mutation",
                "entry_condition": "No candidate clearly improves manuscript value.",
                "acceptance_rule": "Accept when alternatives introduce ambiguity.",
            },
            {
                "id": "restrained_tikz_refinement",
                "mutation_boundary": "source_mutation_requires_separate_approval",
                "entry_condition": "A bounded source-level patch can improve style.",
                "acceptance_rule": "Preserve all forbidden semantics.",
            },
            {
                "id": "editorial_redesign",
                "mutation_boundary": "source_mutation_requires_separate_approval",
                "entry_condition": "Human explicitly asks for a broader alternative.",
                "acceptance_rule": "Beat current style while preserving meaning.",
            },
            {
                "id": "svg_polish_handoff",
                "mutation_boundary": "svg_artifact_mutation_requires_separate_approval",
                "entry_condition": "ready_for_svg_polish evidence is positive.",
                "acceptance_rule": "May adjust only optical finish.",
            },
        ],
        "measurable_checks": [
            {"id": "text_boundary_delta"},
            {"id": "style_lock_typography"},
        ],
        "linked_files": {
            "benchmark_contract": f"examples/{FIXTURE}/benchmark_contract.yaml",
            "aesthetic_intent": f"examples/{FIXTURE}/aesthetic_intent.yaml",
        },
    }
    pack.update(overrides)
    return pack


def _comparison(**overrides: object) -> dict[str, object]:
    comparison: dict[str, object] = {
        "state": "present",
        "forbidden_semantic_changes": [
            "change panel roles",
            "rename symbols",
            "swap shallow/deep trap color semantics",
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
                "authorizes_mutation": False,
                "semantic_change_allowed": False,
                "comparison_basis": [
                    (
                        "candidate may improve typography, trap-level spacing, "
                        "stroke rhythm, or label breathing room"
                    )
                ],
                "failure_modes": [
                    (
                        "reject if it changes capture, escape, or trap-level meaning "
                        "while looking cleaner"
                    )
                ],
                "prerequisite_evidence": [
                    "separate bounded TikZ implementation approval"
                ],
            },
        ],
    }
    comparison.update(overrides)
    return comparison


def _queue_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "fixture": FIXTURE,
        "render_state": "FRESH",
        "critique_state": "FRESH",
        "export_state": "FRESH",
        "design_direction_state": "ready_for_human_choice",
    }
    row.update(overrides)
    return row


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


def test_packet_prepares_bounded_refinement_without_authorizing_mutation() -> None:
    packet = bounded_tikz_refinement_packet.build_bounded_tikz_refinement_packet(
        FIXTURE,
        style_pack=_style_pack(),
        comparison=_comparison(),
        queue_row=_queue_row(),
    )

    assert packet["schema"] == bounded_tikz_refinement_packet.SCHEMA
    assert packet["fixture"] == FIXTURE
    assert packet["state"] == "ready_for_human_source_mutation_choice"
    assert packet["mutation_boundary"] == "no_source_mutation"
    assert packet["candidate_family"]["id"] == "restrained_tikz_refinement"
    assert packet["candidate_family"]["source_mutation_boundary"] == (
        "source_mutation_requires_separate_approval"
    )
    assert packet["authorizes_source_mutation"] is False
    assert packet["requires_human_decision"] is True
    assert packet["allowed_refinement_classes"] == [
        "label_spacing",
        "stroke_hierarchy",
        "trap_level_clarity",
        "panel_spacing",
    ]
    assert "Should I prepare" in packet["human_question"]


def test_packet_blocks_when_benchmark_evidence_is_missing() -> None:
    packet = bounded_tikz_refinement_packet.build_bounded_tikz_refinement_packet(
        FIXTURE,
        style_pack={"state": "missing"},
        comparison=_comparison(),
        queue_row=_queue_row(),
    )

    assert packet["state"] == "blocked_missing_style_benchmark_pack"
    assert packet["authorizes_source_mutation"] is False
    assert packet["next_agent_action"] == "create_style_benchmark_pack"


def test_packet_rejects_unsafe_fixture() -> None:
    with pytest.raises(
        bounded_tikz_refinement_packet.BoundedTikzRefinementPacketError,
        match="fixture_invalid",
    ):
        bounded_tikz_refinement_packet.build_bounded_tikz_refinement_packet(
            "../escape",
            style_pack=_style_pack(),
            comparison=_comparison(),
            queue_row=_queue_row(),
        )


def test_fig_agent_bounded_tikz_refinement_cli_reads_live_fig3_evidence() -> None:
    result = _run_fig_agent("bounded-tikz-refinement", FIXTURE, "--json")

    assert result.returncode == 0, result.stderr
    packet = json.loads(result.stdout)
    assert packet["schema"] == bounded_tikz_refinement_packet.SCHEMA
    assert packet["fixture"] == FIXTURE
    assert packet["state"] == "ready_for_human_source_mutation_choice"
    assert packet["mutation_boundary"] == "no_source_mutation"
    assert packet["candidate_family"]["id"] == "restrained_tikz_refinement"
    assert packet["authorizes_source_mutation"] is False
