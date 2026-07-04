from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
for path in (
    PLUGIN_ROOT / "scripts",
    PLUGIN_ROOT / "scripts" / "driver",
    PLUGIN_ROOT / "scripts" / "quality",
):
    sys.path.insert(0, str(path))

import quality_search  # noqa: E402

FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _driver_with_basin() -> dict[str, object]:
    return {
        "action": "complete",
        "reason": (
            "latest /fig_loop checkpoint reports repeated loop basin: "
            "aesthetic_bottleneck=print_typography_authority appeared 5 times."
        ),
        "safe_command": None,
        "stop_boundary": "basin_detected",
        "status": {
            "render_state": "FRESH",
            "critique_state": "FRESH",
            "export_state": "FRESH",
            "acceptance_state": "NOT_DECLARED",
            "workflow_ready": True,
            "release_ready": False,
            "final_ready": False,
        },
        "next_action_summary": {
            "release_blockers": [
                {
                    "blocking_source": "acceptance_not_declared",
                    "blocks_release": True,
                    "required_actor": "human",
                    "reason": "explicit acceptance is required for release",
                }
            ]
        },
        "loop_checkpoint": {
            "final_stop_reason": "basin_detected",
            "recommended_next_action": (
                "step out of the local polish loop: repeated aesthetic_bottleneck "
                "print_typography_authority appeared 5 times"
            ),
            "basin_summary": {
                "evaluation_state": "basin_detected",
                "history_count": 5,
                "next_action": (
                    "step out of the local polish loop: repeated aesthetic_bottleneck "
                    "print_typography_authority appeared 5 times"
                ),
                "signal": {
                    "signal_class": "aesthetic_bottleneck",
                    "signal_value": "print_typography_authority",
                },
            },
            "aesthetic_lever_summary": {
                "evaluation_state": "needs_human",
                "next_aesthetic_bottleneck": {
                    "dimension": "typography_authority",
                    "lever_id": "print_typography_authority",
                    "route": "tikz_patch",
                },
            },
        },
        "audit_evidence": {
            "detector_feedback": {
                "unlinked_micro_defect_count": 1,
                "unlinked_micro_defect_ids": ["M_PANEL_F_DENSITY"],
            }
        },
    }


def _ledger_with_actionable_and_unbound_defects() -> dict[str, object]:
    return {
        "actionability_metrics": {
            "candidate_supported_defect_count": 2,
            "safe_candidate_defect_count": 3,
            "unknown_panel_defect_count": 1,
            "missing_selector_hash_count": 1,
        },
        "defects": [
            {
                "id": "QD001",
                "defect_class": "text_overlap",
                "actionability": {"state": "candidate_supported", "gaps": []},
                "selector_hint": {
                    "kind": "line_range",
                    "value": "42:42",
                    "selector_text_hash": "sha256:abc",
                },
                "target": {"panel": "F", "subregion": "sel:abc"},
            },
            {
                "id": "QD002",
                "defect_class": "text_overlap",
                "actionability": {"state": "blocked", "gaps": ["unknown_panel"]},
                "selector_hint": {"kind": "line_range", "value": "0:0"},
                "target": {"panel": "unknown", "subregion": "sel:def"},
            },
        ],
    }


def test_quality_search_plans_basin_step_out_without_human_gate(monkeypatch) -> None:
    monkeypatch.setattr(
        quality_search.fig_driver,
        "build_driver_summary",
        lambda *_args, **_kwargs: _driver_with_basin(),
    )
    monkeypatch.setattr(
        quality_search.quality_defect_ledger,
        "build_quality_defect_ledger",
        lambda *_args, **_kwargs: _ledger_with_actionable_and_unbound_defects(),
    )
    monkeypatch.setattr(
        quality_search.quality_memory_index,
        "build_fixture_index",
        lambda *_args, **_kwargs: {"event_count": 0, "candidate_event_count": 0},
    )

    payload = quality_search.build_quality_search_plan(
        "fig_demo",
        goal="test typography authority basin",
        plugin_root=PLUGIN_ROOT,
        workspace_root=PLUGIN_ROOT,
    )

    assert payload["schema"] == "figure-agent.quality-search-plan.v0"
    assert payload["next_recommended_operation"]["kind"] == "step_out_experiment"
    assert payload["next_recommended_operation"]["candidate_families"][:2] == [
        "hierarchy_rebalance",
        "apparatus_strengthen",
    ]
    release = [item for item in payload["classifications"] if item["kind"] == "release_blocker"][0]
    assert release["id"] == "acceptance_not_declared"
    assert release["blocks_search"] is False
    assert any(item["kind"] == "quality_basin" for item in payload["classifications"])
    assert "human_gate" not in json.dumps(payload["next_recommended_operation"])
    assert {item["family"] for item in payload["patch_hypotheses"]} >= {
        "hierarchy_rebalance",
        "apparatus_strengthen",
    }
    density = [item for item in payload["patch_hypotheses"] if item["family"] == "density_reduce"][
        0
    ]
    assert "F" in density["target_hint"]["panels"]
    assert all(item["mutation_allowed"] is False for item in payload["patch_hypotheses"])
    symptoms = " ".join(item["symptom"] for item in payload["tool_defect_candidates"])
    assert "tikz_patch route" in symptoms
    assert "not fully bound" in symptoms
    assert "unlinked micro defects" in symptoms


def _write_minimal_fixture(workspace: Path, name: str = "quality_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(f"name: {name}\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text("\\node at (0,0) {demo};\n", encoding="utf-8")
    return fixture


def _tree(workspace: Path) -> list[str]:
    return sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))


def test_fig_agent_quality_search_plan_cli_is_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_minimal_fixture(workspace)
    before = _tree(workspace)
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)

    result = subprocess.run(
        [
            sys.executable,
            str(FIG_AGENT),
            "quality-search",
            "quality_demo",
            "--goal",
            "plan only",
            "--plan",
            "--json",
        ],
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.quality-search-plan.v0"
    assert payload["read_only"] is True
    assert payload["safety"]["writes"] == []
    assert _tree(workspace) == before
