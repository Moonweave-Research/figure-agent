from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import style_benchmark_pack  # noqa: E402


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _minimal_pack(plugin_root: Path, fixture: str = "contract_demo") -> Path:
    _write_json(
        plugin_root / "docs" / "decision-packets" / "wave" / f"{fixture}.json",
        {"fixture": fixture},
    )
    _write_json(
        plugin_root / "docs" / "decision-records" / "wave" / f"{fixture}.json",
        {"fixture": fixture},
    )
    _write_yaml(
        plugin_root / "examples" / fixture / "benchmark_contract.yaml",
        {
            "schema": "figure-agent.benchmark-contract.v1",
            "fixture": fixture,
            "expected_movement": {
                "text_boundary.blocker_count": "decrease_or_equal",
            },
            "hard_regressions": [
                "source_compile_failure",
                "candidate_hard_gate_rejected",
            ],
        },
    )
    _write_yaml(
        plugin_root / "examples" / fixture / "aesthetic_intent.yaml",
        {
            "schema": "figure-agent.aesthetic-intent.v2",
            "fixture": fixture,
        },
    )
    pack_path = (
        plugin_root
        / "docs"
        / "style-benchmark-packs"
        / "wave"
        / f"{fixture}.json"
    )
    _write_json(
        pack_path,
        {
            "schema": style_benchmark_pack.SCHEMA,
            "fixture": fixture,
            "source_decision_packet": f"docs/decision-packets/wave/{fixture}.json",
            "source_decision_record": f"docs/decision-records/wave/{fixture}.json",
            "benchmark_contract": f"examples/{fixture}/benchmark_contract.yaml",
            "aesthetic_intent": f"examples/{fixture}/aesthetic_intent.yaml",
            "target_style_class": "restrained editorial multipanel scientific schematic",
            "default_recommendation": "keep_current_style_until_candidate_beats_benchmark",
            "forbidden_semantic_changes": [
                "change panel roles",
                "rename symbols",
                "swap shallow/deep trap color semantics",
                "remove required labels",
                "do not use SVG polish for semantic repair",
            ],
            "candidate_family_slots": [
                {
                    "id": "current_style",
                    "label": "Keep current style",
                    "mutation_boundary": "no_source_mutation",
                    "entry_condition": "No candidate clearly improves manuscript value.",
                    "acceptance_rule": "Accept when alternatives introduce ambiguity.",
                },
                {
                    "id": "restrained_tikz_refinement",
                    "label": "Restrained TikZ refinement",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                    "entry_condition": "A bounded source-level patch can improve style.",
                    "acceptance_rule": "Preserve all forbidden semantics.",
                },
                {
                    "id": "editorial_redesign",
                    "label": "Editorial redesign",
                    "mutation_boundary": "source_mutation_requires_separate_approval",
                    "entry_condition": "Human explicitly asks for a broader alternative.",
                    "acceptance_rule": "Beat current style while preserving meaning.",
                },
                {
                    "id": "svg_polish_handoff",
                    "label": "SVG polish handoff",
                    "mutation_boundary": "svg_artifact_mutation_requires_separate_approval",
                    "entry_condition": (
                        "TikZ/source semantics are locked and "
                        "ready_for_svg_polish evidence is positive."
                    ),
                    "acceptance_rule": "May adjust only optical finish.",
                },
            ],
            "measurable_checks": [
                {
                    "id": "benchmark_contract_hard_regressions",
                    "source": "benchmark_contract.yaml",
                    "must_pass": [
                        "source_compile_failure absent",
                        "candidate_hard_gate_rejected absent",
                    ],
                },
                {
                    "id": "text_boundary_delta",
                    "source": "benchmark_contract.yaml",
                    "metric": "text_boundary.blocker_count",
                    "expected_movement": "decrease_or_equal",
                },
            ],
            "human_only_questions": ["Does the candidate improve journal fit?"],
            "candidate_rejection_rules": [
                "reject a prettier candidate if it changes semantic meaning",
            ],
            "safety": {
                "source_mutation": False,
                "accepted_state_mutation": False,
                "release_state_mutation": False,
                "generated_export_mutation": False,
                "golden_mutation": False,
                "svg_polish_default": False,
            },
        },
    )
    return pack_path


def test_real_wave_c_style_benchmark_pack_loads_and_links_contracts() -> None:
    payload = style_benchmark_pack.load_pack(
        "fig1_overview_v2_pair_001_vault",
        plugin_root=PLUGIN_ROOT,
    )

    assert payload["schema"] == style_benchmark_pack.SCHEMA
    assert payload["state"] == "present"
    assert payload["fixture"] == "fig1_overview_v2_pair_001_vault"
    assert set(payload["linked_files"]) == {
        "source_decision_packet",
        "source_decision_record",
        "benchmark_contract",
        "aesthetic_intent",
    }
    assert {
        slot["id"] for slot in payload["candidate_family_slots"]
    } == style_benchmark_pack.REQUIRED_CANDIDATE_SLOTS
    assert payload["safety"] == {
        "accepted_state_mutation": False,
        "generated_export_mutation": False,
        "golden_mutation": False,
        "release_state_mutation": False,
        "source_mutation": False,
        "svg_polish_default": False,
    }


def test_missing_style_benchmark_pack_is_structured_state() -> None:
    payload = style_benchmark_pack.load_pack(
        "smoke_panel_spacing_demo",
        plugin_root=PLUGIN_ROOT,
    )

    assert payload == {
        "schema": style_benchmark_pack.SCHEMA,
        "state": "missing",
        "fixture": "smoke_panel_spacing_demo",
        "path": (
            "docs/style-benchmark-packs/2026-06-30-wave-c/"
            "smoke_panel_spacing_demo.json"
        ),
    }


def test_style_benchmark_pack_rejects_path_escape(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    pack_path = _minimal_pack(plugin_root)
    payload = json.loads(pack_path.read_text(encoding="utf-8"))
    payload["source_decision_packet"] = "../outside.json"
    _write_json(pack_path, payload)

    with pytest.raises(
        style_benchmark_pack.StyleBenchmarkPackError,
        match="source_decision_packet_path_escape",
    ):
        style_benchmark_pack.load_pack(
            "contract_demo",
            plugin_root=plugin_root,
            pack_path=pack_path,
        )


def test_style_benchmark_pack_requires_exact_candidate_slots(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    pack_path = _minimal_pack(plugin_root)
    payload = json.loads(pack_path.read_text(encoding="utf-8"))
    payload["candidate_family_slots"] = [
        slot
        for slot in payload["candidate_family_slots"]
        if slot["id"] != "svg_polish_handoff"
    ]
    _write_json(pack_path, payload)

    with pytest.raises(
        style_benchmark_pack.StyleBenchmarkPackError,
        match="candidate_family_slots_invalid",
    ):
        style_benchmark_pack.load_pack(
            "contract_demo",
            plugin_root=plugin_root,
            pack_path=pack_path,
        )


def test_style_benchmark_pack_rejects_svg_polish_default(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    pack_path = _minimal_pack(plugin_root)
    payload = json.loads(pack_path.read_text(encoding="utf-8"))
    payload["safety"]["svg_polish_default"] = True
    _write_json(pack_path, payload)

    with pytest.raises(
        style_benchmark_pack.StyleBenchmarkPackError,
        match="safety_invalid",
    ):
        style_benchmark_pack.load_pack(
            "contract_demo",
            plugin_root=plugin_root,
            pack_path=pack_path,
        )


def test_style_benchmark_pack_summary_is_compact_and_read_only(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    pack_path = _minimal_pack(plugin_root)

    pack = style_benchmark_pack.load_pack(
        "contract_demo",
        plugin_root=plugin_root,
        pack_path=pack_path,
    )
    summary = style_benchmark_pack.summarize_pack(pack)

    assert summary["state"] == "present"
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
    assert summary["candidate_mutation_boundaries"] == {
        "current_style": "no_source_mutation",
        "restrained_tikz_refinement": "source_mutation_requires_separate_approval",
        "editorial_redesign": "source_mutation_requires_separate_approval",
        "svg_polish_handoff": "svg_artifact_mutation_requires_separate_approval",
    }
    assert summary["linked_files"] == {
        "benchmark_contract": "examples/contract_demo/benchmark_contract.yaml",
        "aesthetic_intent": "examples/contract_demo/aesthetic_intent.yaml",
    }
    assert summary["top_human_only_questions"] == ["Does the candidate improve journal fit?"]
    assert summary["safety_boundary"] == {
        "source_mutation": False,
        "accepted_state_mutation": False,
        "release_state_mutation": False,
        "generated_export_mutation": False,
        "golden_mutation": False,
        "svg_polish_default": False,
    }
    assert "measurable_checks" not in summary
    assert "candidate_rejection_rules" not in summary
