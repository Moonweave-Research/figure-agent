from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
for path in (
    PLUGIN_ROOT / "scripts",
    PLUGIN_ROOT / "scripts" / "candidates",
    PLUGIN_ROOT / "scripts" / "driver",
    PLUGIN_ROOT / "scripts" / "quality",
):
    sys.path.insert(0, str(path))

import quality_memory_index  # noqa: E402
import quality_search  # noqa: E402

FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _write_png(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (4, 4), color).save(path)


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


def _driver_with_qtr_micro_defect() -> dict[str, object]:
    driver = _driver_with_basin()
    driver["audit_evidence"] = {
        "detector_feedback": {
            "unlinked_micro_defect_count": 1,
            "unlinked_micro_defect_ids": ["M_PRINT_QTR"],
        }
    }
    return driver


def _driver_ready_without_basin() -> dict[str, object]:
    return {
        "action": "complete",
        "reason": "fixture is ready for quality search",
        "safe_command": None,
        "stop_boundary": "quality_search_ready",
        "status": {
            "render_state": "FRESH",
            "critique_state": "FRESH",
            "export_state": "FRESH",
            "acceptance_state": "NOT_DECLARED",
            "workflow_ready": True,
            "release_ready": False,
            "final_ready": False,
        },
        "next_action_summary": {"release_blockers": []},
        "loop_checkpoint": {
            "final_stop_reason": "human_gate_required",
            "recommended_next_action": "run quality search",
        },
        "audit_evidence": {"detector_feedback": {}},
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
    assert payload["search_policy"]["schema"] == "figure-agent.quality-search-bandit-policy.v1"
    assert payload["search_policy"]["kind"] == "epsilon_greedy_family_bandit_v1"
    assert payload["search_policy"]["bandit_decision"]["selected_family"] in {
        "hierarchy_rebalance",
        "panel_c_hero_finish",
        "apparatus_strengthen",
        "panel_f_final_finish",
        "panel_f_label_route_finish",
        "panel_f_boundary_polish",
        "density_reduce",
    }
    assert payload["next_recommended_operation"]["candidate_families"][:3] == [
        "hierarchy_rebalance",
        "panel_c_hero_finish",
        "apparatus_strengthen",
    ]
    release = [item for item in payload["classifications"] if item["kind"] == "release_blocker"][0]
    assert release["id"] == "acceptance_not_declared"
    assert release["blocks_search"] is False
    assert release["blocks_release"] is True
    assert release["required_actor"] == "human"
    assert any(item["kind"] == "quality_basin" for item in payload["classifications"])
    assert "human_gate" not in json.dumps(payload["next_recommended_operation"])
    assert {item["family"] for item in payload["patch_hypotheses"]} >= {
        "hierarchy_rebalance",
        "panel_c_hero_finish",
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


def test_tool_defect_candidates_include_loop_stop_attribution() -> None:
    candidates = quality_search._tool_defect_candidates(
        {
            "loop_checkpoint": {
                "final_stop_reason": "remedy_ineffective",
                "stop_routes": [
                    {
                        "subregion_id": "sel:abc",
                        "stop_cause": "lever_exhausted",
                        "payload": "no_bounded_operation",
                    }
                ],
                "stop_diagnosis": {
                    "cause_histogram": {
                        "decision_weak": 2,
                        "lever_exhausted": 1,
                    }
                },
                "auto_remedy": {
                    "cause": "stale_detector_evidence",
                    "status": "remedy_ineffective",
                },
            }
        },
        {},
    )

    symptoms = " ".join(item["symptom"] for item in candidates)
    assert "candidate family is exhausted" in symptoms
    assert "decision_weak stop recurred" in symptoms
    assert "stale_detector_evidence" in json.dumps(candidates)


def _write_minimal_fixture(
    workspace: Path,
    name: str = "quality_demo",
    *,
    tex_source: str = "\\node at (0,0) {demo};\n",
) -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(f"name: {name}\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(tex_source, encoding="utf-8")
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


def test_quality_search_execute_writes_dry_run_witness_evidence(
    tmp_path: Path, monkeypatch
) -> None:
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

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="dry witness executor",
        max_iterations=3,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    assert payload["schema"] == "figure-agent.quality-search-execute.v0"
    assert payload["status"] == "dry_run_complete"
    assert payload["executed_iterations"] == 1
    assert payload["safety"]["source_mutation"] == "forbidden_in_dry_executor"
    assert payload["decision"]["kind"] == "no_non_marginal_candidate"
    assert payload["decision"]["selected_candidate_id"] is None
    assert payload["decision"]["source_mutation"] == "not_performed"
    assert payload["decision"]["top_candidate_id"] != "QSNULL"
    assert payload["decision"]["non_marginal_thresholds"] == {
        "full_changed_pixel_ratio": 0.002,
        "panel_changed_pixel_ratio": 0.02,
    }
    assert payload["candidate_set"]["candidates"] == []
    assert payload["render_results"]["render_mode"] == "none"
    assert payload["render_results"]["rendered"] == []
    assert payload["visual_evidence"]["state"] == "not_applicable"
    assert payload["memory_events"]["event_count"] == 0
    assert len(payload["candidate_specs"]) == 9
    assert {item["family"] for item in payload["candidate_specs"]} >= {
        "hierarchy_rebalance",
        "panel_c_hero_finish",
        "apparatus_strengthen",
        "panel_f_final_finish",
        "panel_f_label_route_finish",
        "panel_f_density_relief",
        "panel_f_boundary_polish",
        "density_reduce",
        "null_baseline",
    }
    hierarchy = [
        item for item in payload["candidate_specs"] if item["family"] == "hierarchy_rebalance"
    ][0]
    assert hierarchy["builder"] == "panel_region_spec"
    assert hierarchy["apply_authority"] == "review_only"
    assert hierarchy["operation_scale"] == "local_style_token"
    assert hierarchy["template_id"] == "line_width_minimum_v1"
    assert hierarchy["protected_labels"]
    assert hierarchy["design_moves"]
    assert hierarchy["operation_state"] == "not_generated"
    assert hierarchy["witness"]["source_binding_state"] == "unbound"
    assert all(
        selector["binding_state"] == "unbound"
        for selector in hierarchy["source_selectors"]
    )
    assert all("witness" in item for item in payload["candidate_scores"])
    assert all("policy" in item for item in payload["candidate_scores"])
    assert all("policy_score" in item for item in payload["candidate_scores"])
    assert all("operation_scale" in item for item in payload["candidate_scores"])
    assert all("template_id" in item for item in payload["candidate_scores"])
    assert all("expected_visual_movement" in item for item in payload["candidate_scores"])
    assert all("non_marginal_visual_change" in item for item in payload["candidate_scores"])
    assert all(path.startswith(".scratch/quality-search-runs/") for path in payload["writes"])

    run_dir = tmp_path / payload["run_dir"]
    assert (run_dir / "run_manifest.json").is_file()
    assert (run_dir / "family_registry_000.json").is_file()
    assert (run_dir / "candidate_set_000.json").is_file()
    assert (run_dir / "render_results_000.json").is_file()
    assert (run_dir / "candidate_specs_000.json").is_file()
    assert (run_dir / "candidate_scores_000.json").is_file()
    assert (run_dir / "candidate_rankings_000.json").is_file()
    assert (run_dir / "decision_000.json").is_file()
    decision = json.loads((run_dir / "decision_000.json").read_text(encoding="utf-8"))
    assert decision == payload["decision"]


def test_quality_search_execute_binds_family_specs_to_panel_regions(
    tmp_path: Path, monkeypatch
) -> None:
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
    tex_source = "\n".join(
        [
            "% Panel C -- Localized traps",
            "\\draw[cAmber!75!black, line width=0.60pt] (0,0) -- (1,0);",
            "\\node at (0,0) {mobility edge};",
            "% =============== Column F -- Mechanical =================",
            "\\draw[cRed!75!black, line width=0.50pt] (0,0) -- (1,0);",
            "\\node at (1,1) {Coulomb repulsion};",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="dry witness executor with source bindings",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    assert payload["source_context"]["source_state"] == "loaded"
    assert payload["source_context"]["selector_count"] == 2
    hierarchy = [
        item for item in payload["candidate_specs"] if item["family"] == "hierarchy_rebalance"
    ][0]
    apparatus = [
        item for item in payload["candidate_specs"] if item["family"] == "apparatus_strengthen"
    ][0]
    hierarchy_selectors = {item["panel"]: item for item in hierarchy["source_selectors"]}
    apparatus_selectors = {item["panel"]: item for item in apparatus["source_selectors"]}
    assert hierarchy_selectors["C"]["binding_state"] == "bound"
    assert hierarchy_selectors["C"]["line_start"] == 1
    assert hierarchy_selectors["C"]["line_end"] == 3
    assert hierarchy_selectors["F"]["binding_state"] == "bound"
    assert apparatus_selectors["F"]["binding_state"] == "bound"
    assert apparatus["witness"]["source_binding_state"] == "bound"
    assert len(payload["candidate_set"]["candidates"]) == 3
    first_candidate = payload["candidate_set"]["candidates"][0]
    assert first_candidate["id"] == "QS001"
    assert first_candidate["operation_scale"] == "local_style_token"
    assert first_candidate["template_id"] == "line_width_minimum_v1"
    assert first_candidate["operations"][0]["kind"] == "replace_text"
    assert first_candidate["operations"][0]["operation_scale"] == "local_style_token"
    assert "line width=0.9pt" in first_candidate["operations"][0]["replacement"]
    assert len(payload["render_results"]["rendered"]) == 3
    assert payload["render_results"]["render_mode"] == "prepare_only"
    assert payload["visual_evidence"]["state"] == "not_applicable"
    assert payload["memory_events"]["event_count"] == 0
    assert payload["candidate_rankings"][0]["candidate_id"] == "QS001"
    assert payload["depone"]["verdict"]["contract_status"] == "pass"
    assert payload["depone"]["verdict"]["checks"]["candidate_count"] == 3
    assert payload["depone"]["verdict"]["checks"]["render_mode"] == "prepare_only"
    assert payload["depone"]["verdict"]["checks"]["evaluated_count"] == 0
    sandbox_source = (
        tmp_path
        / "examples"
        / "fig_demo"
        / "build"
        / "candidates"
        / "QS001"
        / "fig_demo.tex"
    )
    assert sandbox_source.is_file()
    assert "line width=0.9pt" in sandbox_source.read_text(encoding="utf-8")
    depone_plan = tmp_path / payload["depone"]["plan"]
    depone_evidence = tmp_path / payload["depone"]["evidence_dir"]
    assert depone_plan.is_file()
    assert (depone_evidence / "evidence-contract.json").is_file()
    assert (depone_evidence / "run-metadata.json").is_file()
    assert (depone_evidence / "exit-code.txt").read_text(encoding="utf-8") == "0\n"
    assert (depone_evidence / "quality-search-summary.md").is_file()
    depone_verdict = json.loads(
        (depone_evidence / "quality-search-verdict.json").read_text(encoding="utf-8")
    )
    assert depone_verdict["contract_status"] == "pass"
    depone_contract = json.loads(
        (depone_evidence / "evidence-contract.json").read_text(encoding="utf-8")
    )
    assert depone_contract["schema_version"] == "v105.verify_wedge"
    assert "quality-search-verdict.json" in depone_contract["required_evidence"]


def test_quality_search_apparatus_strengthen_emits_panel_block_candidate(
    tmp_path: Path, monkeypatch
) -> None:
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
    tex_source = "\n".join(
        [
            "% Panel C -- Localized traps",
            "\\draw[cAmber!75!black, line width=0.60pt] (0,0) -- (1,0);",
            "% =============== Column F -- Mechanical =================",
            "% v5f Panel F art-direction redraw overlay.",
            "\\fill[cGray!35!black, opacity=0.13, rounded corners=1.2pt]",
            "  (12.58, 3.54) rectangle (13.62, 4.14);",
            "\\draw[cGray!64!black, line width=0.34pt, rounded corners=1.2pt]",
            "  (12.52, 3.59) rectangle (13.56, 4.19);",
            "\\node at (13.04, 3.82) {$V_{\\mathrm{active}}$};",
            "\\node at (12.91, 3.64) {DC bias};",
            "\\draw[cGray!86!black, line width=0.56pt] (13.18, 0.46) rectangle (13.42, 2.82);",
            "\\node at (13.64, 1.62) {electrode};",
            "\\node at (12.13, 3.08) {$q_{\\mathrm{tr}}$ trapped charge};",
            (
                "\\draw[panelFCoulombRepulsionArrow, -{Stealth[length=7pt,width=5pt]}, "
                "cRed!82!black, line width=0.82pt]"
            ),
            "  (10.95, 1.18) -- (9.74, 1.18);",
            "\\node at (9.68, 1.55) {Coulomb};",
            "\\node at (9.70, 1.46) {repulsion};",
            "\\draw[<->, cGray!55!black, line width=0.30pt]",
            "  (10.58, 0.54) -- (13.18, 0.54);",
            "\\node at (11.88, 0.31) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
            "% ============================================================",
            "% v8.6 ROW 2 END",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="apparatus panel block",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    specs_by_family = {item["family"]: item for item in payload["candidate_specs"]}
    apparatus_spec = specs_by_family["apparatus_strengthen"]
    assert apparatus_spec["operation_scale"] == "panel_block"
    assert apparatus_spec["template_id"] == "v5f_panel_f_redraw_overlay_v1"

    apparatus = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "apparatus_strengthen"
    ][0]
    operation = apparatus["operations"][0]
    assert apparatus["edit_class"] == "quality_search_panel_block"
    assert apparatus["operation_scale"] == "panel_block"
    assert apparatus["template_id"] == "v5f_panel_f_redraw_overlay_v1"
    assert operation["operation_scale"] == "panel_block"
    assert operation["template_id"] == "v5f_panel_f_redraw_overlay_v1"
    assert operation["line_start"] == 4
    assert operation["line_end"] == 23
    assert "v5f Panel F art-direction redraw overlay" in operation["original"]
    assert "Stealth[length=8.5pt,width=6.2pt]" in operation["replacement"]
    assert "line width=1.08pt" in operation["replacement"]
    for protected in (
        "trapped charge",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
        "mechanical",
    ):
        assert protected in operation["replacement"]

    by_id = {item["candidate_id"]: item for item in payload["candidate_scores"]}
    score = by_id[apparatus["id"]]
    assert score["operation_scale"] == "panel_block"
    assert score["template_id"] == "v5f_panel_f_redraw_overlay_v1"
    assert "Panel F apparatus reads" in score["expected_visual_movement"]


def test_quality_search_apparatus_strengthen_materializes_current_v5f_panel_block(
    tmp_path: Path, monkeypatch
) -> None:
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
    tex_source = "\n".join(
        [
            "% =============== Column F -- Mechanical =================",
            "% v5f Panel F art-direction redraw overlay.",
            "\\fill[cGray!30!black, opacity=0.045]",
            "  (12.65, 3.55) rectangle (13.58, 4.12);",
            "\\draw[cGray!58!black, line width=0.26pt]",
            "  (12.60, 3.62) rectangle (13.52, 4.17);",
            "\\node at (13.06, 3.82) {$V_{\\mathrm{active}}$};",
            "\\node at (13.06, 3.70) {bias};",
            "\\draw[cGray!60!black, line width=0.24pt, rounded corners=1.1pt]",
            "  (13.42, 4.01) -- (13.62, 4.01) -- (13.62, 2.82) -- (13.42, 2.82);",
            "\\draw[cGray!86!black, line width=0.66pt] (13.18, 0.46) rectangle (13.42, 2.82);",
            "\\node at (13.64, 1.62) {electrode};",
            "\\foreach \\cx/\\cy/\\rr in {11.62/2.28/0.075,11.43/1.86/0.082} {",
            (
                "  \\draw[cRed!35!white, line width=0.25pt, opacity=0.36] "
                "(\\cx,\\cy) circle ({1.65*\\rr});"
            ),
            "  \\shade[ball color=cRed!76!black] (\\cx,\\cy) circle (\\rr);",
            "}",
            "\\draw[cRed!45!black, line width=0.22pt]",
            "  (11.58,2.35) .. controls (11.28,2.56) and (10.90,2.64) .. (10.48,2.62);",
            "\\node at (9.80, 2.60) {$q_{\\mathrm{tr}}$};",
            "\\node at (10.08, 2.60) {trapped charge};",
            (
                "\\draw[panelFCoulombRepulsionArrow, "
                "-{Stealth[length=7.6pt,width=5.6pt]}, "
                "cRed!82!black, line width=0.94pt]"
            ),
            "  (11.02, 1.18) -- (9.60, 1.18);",
            "\\node at (9.72, 1.54) {Coulomb};",
            "\\node at (9.73, 1.45) {repulsion};",
            "\\draw[<->, cGray!62!black, line width=0.38pt]",
            "  (10.42, 0.54) -- (13.18, 0.54);",
            "\\node at (11.88, 0.31) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
            "% v8.6 ROW 2 END",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="apparatus panel block current v5f",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    apparatus = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "apparatus_strengthen"
    ][0]
    operation = apparatus["operations"][0]
    assert apparatus["operation_scale"] == "panel_block"
    assert apparatus["template_id"] == "v5f_panel_f_redraw_overlay_v1"
    assert operation["operation_scale"] == "panel_block"
    assert "opacity=0.018" in operation["replacement"]
    assert "rounded corners=1.0pt" in operation["replacement"]
    assert (
        "(13.30, 3.78) -- (13.04, 3.52) -- (13.04, 3.16)"
        " -- (13.18, 3.02) -- (13.30, 2.82);"
    ) in operation["replacement"]
    assert "circle ({2.35*\\rr})" in operation["replacement"]
    assert "ball color=cRed!82!black" in operation["replacement"]
    assert "at (9.60, 3.12) {$q_{\\mathrm{tr}}$};" in operation["replacement"]
    assert "at (9.60, 3.36) {trapped charge};" in operation["replacement"]
    assert "Stealth[length=9.6pt,width=6.8pt]" in operation["replacement"]
    assert "line width=1.24pt" in operation["replacement"]
    assert "\\draw[<->, cGray!64!black, line width=0.70pt]" in operation["replacement"]


def test_quality_search_qtr_micro_defect_emits_panel_f_apparatus_lane_candidate(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        quality_search.fig_driver,
        "build_driver_summary",
        lambda *_args, **_kwargs: _driver_with_qtr_micro_defect(),
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
    tex_source = "\n".join(
        [
            "% Panel C -- Localized traps",
            "\\draw[cAmber!75!black, line width=0.60pt] (0,0) -- (1,0);",
            "% =============== Column F -- Mechanical =================",
            "\\fill[cGray!6] (11.8, 3.2) rectangle (12.65, 3.85);",
            "\\draw[cGray!60!black, line width=0.25pt]",
            "  (11.8, 3.2) rectangle (12.65, 3.85);",
            "\\draw[cGray!35!black, line width=0.18pt] (11.85, 3.25) rectangle (12.60, 3.81);",
            "\\fill[cGray!18] (11.9, 3.55) rectangle (12.55, 3.78);",
            "\\draw[cGray!55!black, line width=0.18pt]",
            "  (11.9, 3.55) rectangle (12.55, 3.78);",
            "\\draw[cGray!80!black, line width=0.55pt]",
            "  (11.95, 3.58) -- (12.08, 3.58) -- (12.08, 3.73)",
            "              -- (12.3, 3.73) -- (12.3, 3.58) -- (12.5, 3.58);",
            "\\node[font=\\sffamily\\bfseries\\fontsize{6}{7.2}\\selectfont, text=cGray!88!black]",
            "  at (12.225, 3.36) {$V_{\\mathrm{active}}$};",
            "\\fill[cGray!85!black] (12.65, 3.5) circle (0.028);",
            "\\fill[cGray!50!black] (12.65, 3.5) circle (0.014);",
            "\\draw[cGray!75!black, line width=0.28pt]",
            "  (12.65, 3.5) -- (13.23, 3.5) -- (13.23, 2.6);",
            "\\fill[cGray!10] (11.785, 2.42) rectangle (12.185, 2.52);",
            "\\draw[cGray!75!black, line width=0.40pt]",
            "  (11.785, 2.42) rectangle (12.185, 2.52);",
            "\\draw[cGray!50!black, line width=0.40pt] (11.685, 2.65) -- (12.285, 2.65);",
            "\\foreach \\dx in {0,0.10,0.20,0.30,0.40,0.50} {",
            "  \\draw[cGray!50!black, line width=0.25pt]",
            "    ({11.685+\\dx}, 2.65) -- ({11.635+\\dx}, 2.72);",
            "}",
            "\\draw[cGray!75!black, line width=0.40pt] (11.985, 2.52) -- (11.985, 2.65);",
            "\\shade[top color=cAmber!22, bottom color=cAmber!42, rounded corners=0.3mm]",
            "  (11.92, 2.42) .. controls (11.94, 1.80) and (11.55, 1.22) ..",
            "  (11.11, 0.93) -- (11.21, 0.84) .. controls (11.74, 1.16) and",
            "  (12.07, 1.80) .. (12.05, 2.42) -- cycle;",
            "\\draw[cAmber!80!black, line width=0.55pt, rounded corners=0.3mm]",
            "  (11.92, 2.42) .. controls (11.94, 1.80) and (11.55, 1.22) ..",
            "  (11.11, 0.93) -- (11.21, 0.84) .. controls (11.74, 1.16) and",
            "  (12.07, 1.80) .. (12.05, 2.42) -- cycle;",
            "\\draw[cRed!55!black, line width=0.30pt] (11.92, 2) -- (12.35, 2);",
            "\\node[labelMute, anchor=west, inner sep=1pt,",
            "      font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont, text=cRed!70!black]",
            "  at (12.35, 2) {$q_{tr}$};",
            "\\fill[cGray!25] (13.23, 0.4) rectangle (13.4, 2.6);",
            "\\draw[cGray!85!black, line width=0.50pt]",
            "  (13.23, 0.4) rectangle (13.4, 2.6);",
            "\\node[labelMute, anchor=south, rotate=270,",
            "      font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont,",
            "      text=cGray!85!black] at (13.58, 1.5) {electrode};",
            "\\draw[-{Stealth[length=6pt,width=4.5pt]}, cRed!80!black, line width=0.7pt]",
            "  (11.55, 1.3) -- (10.85, 1.3);",
            "\\node[font=\\sffamily\\bfseries\\fontsize{7}{8.4}\\selectfont, text=cRed!80!black,",
            "      anchor=south east] at (10.85, 1.35) {Coulomb};",
            "\\node[labelMute, anchor=north east, font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont,",
            "      text=cRed!80!black] at (10.85, 1.27) {repulsion};",
            "\\draw[<->, cGray!55!black, line width=0.30pt]",
            "  (11.5, 0.55) -- (13.23, 0.55);",
            "\\node[labelMute, anchor=north, inner sep=1pt,",
            "      font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont]",
            "  at (12.365, 0.5) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
            "% v8.6 ROW 2 END",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="aggressive C001 qtr typography automation",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    families = [item["family"] for item in payload["candidate_specs"]]
    assert families[:2] == [
        "panel_f_qtr_apparatus_lane",
        "panel_f_qtr_label_lane",
    ]
    assert "panel_f_force_gap_lane" in families
    assert "panel_f_mechanical_anchor_lane" in families
    qtr_apparatus = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "panel_f_qtr_apparatus_lane"
    ][0]
    operation = qtr_apparatus["operations"][0]
    assert qtr_apparatus["edit_class"] == "quality_search_panel_block"
    assert qtr_apparatus["operation_scale"] == "panel_block"
    assert qtr_apparatus["template_id"] == "v5d_panel_f_qtr_apparatus_lane_v1"
    assert operation["operation_scale"] == "panel_block"
    assert operation["template_id"] == "v5d_panel_f_qtr_apparatus_lane_v1"
    assert operation["line_start"] == 3
    assert "quality-search C001 q_tr + apparatus lane" in operation["replacement"]
    assert "at (9.70, 2.94) {$q_{tr}$};" in operation["replacement"]
    assert "at (9.70, 3.18) {trapped charge};" in operation["replacement"]
    assert (
        "(12.65, 3.50) -- (12.92, 3.50) -- (13.08, 3.10)"
        in operation["replacement"]
    )
    assert "rounded corners=1.1pt" in operation["replacement"]
    qtr_label = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "panel_f_qtr_label_lane"
    ][0]
    label_operation = qtr_label["operations"][0]
    assert qtr_label["operation_scale"] == "panel_block"
    assert qtr_label["template_id"] == "v5d_panel_f_qtr_label_lane_v1"
    assert qtr_label["protected_labels"] == ["q_tr", "trapped charge"]
    assert "(9.50, 2.72) rectangle (10.72, 3.25);" in label_operation["replacement"]
    assert "line width=0.48pt" in label_operation["replacement"]
    assert "circle (0.185);" in label_operation["replacement"]
    assert "circle (0.155);" in label_operation["replacement"]
    assert "at (9.58, 2.84) {$q_{tr}$};" in label_operation["replacement"]
    assert "at (9.58, 3.12) {trapped charge};" in label_operation["replacement"]
    force_gap = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "panel_f_force_gap_lane"
    ][0]
    force_operation = force_gap["operations"][0]
    assert force_gap["operation_scale"] == "panel_block"
    assert force_gap["template_id"] == "v5d_panel_f_force_gap_lane_v1"
    assert "quality-search C002 Coulomb/electrode/air-gap lane" in force_operation[
        "replacement"
    ]
    assert "(11.62, 1.30) -- (10.42, 1.30);" in force_operation["replacement"]
    assert "at (10.42, 1.40) {Coulomb};" in force_operation["replacement"]
    assert "at (10.42, 1.20) {repulsion};" in force_operation["replacement"]
    assert "(11.14, 0.68) -- (13.23, 0.68);" in force_operation["replacement"]
    mechanical_anchor = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "panel_f_mechanical_anchor_lane"
    ][0]
    anchor_operation = mechanical_anchor["operations"][0]
    assert mechanical_anchor["operation_scale"] == "panel_block"
    assert mechanical_anchor["template_id"] == "v5d_panel_f_mechanical_anchor_lane_v1"
    assert "quality-search C003 mechanical anchor lane" in anchor_operation[
        "replacement"
    ]
    assert "(11.72, 2.36) rectangle (12.28, 2.58);" in anchor_operation[
        "replacement"
    ]
    assert "(11.72, 2.68) -- (12.38, 2.68);" in anchor_operation["replacement"]
    assert "at (9.76, 3.10) {trapped charge};" in anchor_operation["replacement"]
    by_family = {item["family"]: item for item in payload["candidate_scores"]}
    assert by_family["panel_f_qtr_apparatus_lane"]["operation_scale"] == "panel_block"


def test_quality_search_apparatus_strengthen_progresses_already_redrawn_panel_f() -> None:
    block = "\n".join(
        [
            "% v5f Panel F art-direction redraw overlay.",
            "\\fill[cGray!30!black, opacity=0.018]",
            "  (12.58, 3.78) rectangle (13.48, 4.14);",
            "\\draw[cGray!62!black, line width=0.34pt, rounded corners=0.8pt]",
            "  (13.30, 3.78) -- (13.30, 2.82);",
            "\\node at (13.64, 1.62) {electrode};",
            "\\draw[cRed!55!black, line width=0.32pt]",
            "  (11.50,2.38) .. controls (11.10,2.78) and (10.32,3.00) .. (9.62,3.00);",
            "\\node[anchor=west, fill=white, fill opacity=0.96, text opacity=1]",
            "  at (9.56, 2.84) {$q_{\\mathrm{tr}}$};",
            "\\node[anchor=west, fill=white, fill opacity=0.94, text opacity=1]",
            "  at (9.56, 3.04) {trapped charge};",
            "\\node at (9.72, 1.54) {Coulomb};",
            "\\node at (9.73, 1.45) {repulsion};",
            "\\draw[<->, cGray!62!black, line width=0.50pt]",
            "  (10.42, 0.54) -- (13.18, 0.54);",
            "\\node at (11.88, 0.31) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
        ]
    )

    replacement = quality_search._strengthened_panel_f_overlay(f"{block}\n")

    assert replacement is not None
    assert "at (9.60, 3.12) {$q_{\\mathrm{tr}}$};" in replacement
    assert "at (9.60, 3.36) {trapped charge};" in replacement
    assert (
        "(13.30, 3.78) -- (13.04, 3.52) -- (13.04, 3.16)"
        " -- (13.18, 3.02) -- (13.30, 2.82);"
    ) in replacement
    assert "\\draw[<->, cGray!64!black, line width=0.70pt]" in replacement


def test_quality_search_suppresses_already_applied_panel_f_template(
    tmp_path: Path, monkeypatch
) -> None:
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
    tex_source = "\n".join(
        [
            "% Panel C -- Localized traps",
            "\\draw[cAmber!75!black, line width=0.60pt] (0,0) -- (1,0);",
            "% =============== Column E -- ISPD-paired =================",
            "\\draw[cAmber!70!black, line width=0.25pt] (0,0) -- (1,0);",
            "% =============== Column F -- Mechanical =================",
            "% v5f Panel F art-direction redraw overlay.",
            "\\draw[cGray!58!black, line width=0.26pt, rounded corners=1.0pt]",
            (
                "  (13.30, 3.78) -- (13.04, 3.52) -- (13.04, 3.16)"
                " -- (13.18, 3.02) -- (13.30, 2.82);"
            ),
            "\\node at (13.64, 1.62) {electrode};",
            "\\draw[cRed!55!black, line width=0.32pt]",
            (
                "  (11.48,2.40) .. controls (10.78,3.02)"
                " and (10.12,3.36) .. (9.60,3.36);"
            ),
            "\\node[anchor=west, fill=white, fill opacity=0.96, text opacity=1]",
            "  at (9.60, 3.12) {$q_{\\mathrm{tr}}$};",
            "\\node[anchor=west, fill=white, fill opacity=0.94, text opacity=1]",
            "  at (9.60, 3.36) {trapped charge};",
            (
                "\\draw[panelFCoulombRepulsionArrow, "
                "-{Stealth[length=9.6pt,width=6.8pt]}, "
                "cRed!82!black, line width=1.24pt]"
            ),
            "  (11.18, 1.18) -- (9.18, 1.18);",
            "\\node at (9.72, 1.54) {Coulomb};",
            "\\node at (9.73, 1.45) {repulsion};",
            "\\draw[<->, cGray!64!black, line width=0.70pt]",
            "  (9.92, 0.54) -- (13.18, 0.54);",
            "\\node at (11.88, 0.31) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
            "% v8.6 ROW 2 END",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="post-apply Panel F remaining label route apparatus defects",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    candidate_families = {
        item["family"] for item in payload["candidate_set"]["candidates"]
    }
    score_families = {item["family"] for item in payload["candidate_scores"]}
    assert "apparatus_strengthen" not in candidate_families
    assert "apparatus_strengthen" not in score_families
    assert "panel_f_boundary_polish" in candidate_families
    assert {"hierarchy_rebalance", "density_reduce"} <= candidate_families
    assert any(
        item["code"] == "template_already_applied"
        and item["family"] == "apparatus_strengthen"
        and item["template_id"] == "v5f_panel_f_redraw_overlay_v1"
        for item in payload["candidate_set"]["refusals"]
    )


def test_quality_search_panel_f_boundary_polish_emits_v2_panel_block(
    tmp_path: Path, monkeypatch
) -> None:
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
    tex_source = "\n".join(
        [
            "% Panel C -- Localized traps",
            "\\draw[cAmber!75!black, line width=0.60pt] (0,0) -- (1,0);",
            "% =============== Column E -- ISPD-paired =================",
            "\\draw[cAmber!70!black, line width=0.25pt] (0,0) -- (1,0);",
            "% =============== Column F -- Mechanical =================",
            "% v5f Panel F art-direction redraw overlay.",
            "\\fill[white] (9.52, 0.18) rectangle (13.92, 4.34);",
            "\\draw[cGray!58!black, line width=0.26pt, rounded corners=1.0pt]",
            (
                "  (13.30, 3.78) -- (13.04, 3.52) -- (13.04, 3.16)"
                " -- (13.18, 3.02) -- (13.30, 2.82);"
            ),
            "\\node at (13.64, 1.62) {electrode};",
            "\\draw[cRed!55!black, line width=0.32pt]",
            (
                "  (11.48,2.40) .. controls (10.78,3.02)"
                " and (10.12,3.36) .. (9.60,3.36);"
            ),
            (
                "\\node[anchor=west, fill=white, fill opacity=0.96, text opacity=1,\n"
                "      inner xsep=0.9pt, inner ysep=0.45pt,\n"
                "      font=\\sffamily\\bfseries\\fontsize{4.8}{5.8}\\selectfont, "
                "text=cRed!76!black]\n"
                "  at (9.60, 3.12) {$q_{\\mathrm{tr}}$};"
            ),
            (
                "\\node[anchor=west, fill=white, fill opacity=0.94, text opacity=1,\n"
                "      inner xsep=1.0pt, inner ysep=0.45pt,\n"
                "      font=\\sffamily\\bfseries\\fontsize{4.4}{5.3}\\selectfont, "
                "text=cRed!76!black]\n"
                "  at (9.60, 3.36) {trapped charge};"
            ),
            (
                "\\draw[panelFCoulombRepulsionArrow, "
                "-{Stealth[length=9.6pt,width=6.8pt]}, "
                "cRed!82!black, line width=1.24pt]"
            ),
            "  (11.18, 1.18) -- (9.18, 1.18);",
            "\\node[font=\\sffamily\\bfseries\\fontsize{6.5}{7.8}\\selectfont, text=cRed!82!black,",
            "      anchor=south west] at (9.72, 1.54) {Coulomb};",
            (
                "\\node[labelMute, anchor=north west, fill=white, fill opacity=0.94, "
                "text opacity=1,\n"
                "      inner xsep=1.2pt, inner ysep=0.6pt,\n"
                "      font=\\sffamily\\fontsize{6.0}{7.2}\\selectfont,\n"
                "      text=cRed!82!black] at (9.73, 1.45) {repulsion};"
            ),
            "\\draw[<->, cGray!64!black, line width=0.70pt]",
            "  (9.92, 0.54) -- (13.18, 0.54);",
            "\\node at (11.88, 0.31) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
            "% v8.6 ROW 2 END",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="Panel F trapped charge boundary polish",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    boundary = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "panel_f_boundary_polish"
    ][0]
    operation = boundary["operations"][0]
    assert boundary["operation_scale"] == "panel_block"
    assert boundary["template_id"] == "v5f_panel_f_boundary_polish_v1"
    assert operation["operation_scale"] == "panel_block"
    assert operation["template_id"] == "v5f_panel_f_boundary_polish_v1"
    assert "(9.72,3.46)" in operation["replacement"]
    assert "at (9.72, 3.20) {$q_{\\mathrm{tr}}$};" in operation["replacement"]
    assert "at (9.72, 3.46) {trapped charge};" in operation["replacement"]
    assert "(11.06, 1.18) -- (9.34, 1.18);" in operation["replacement"]
    assert "(10.18, 0.54) -- (13.18, 0.54);" in operation["replacement"]


def test_quality_search_panel_f_final_finish_emits_post_boundary_panel_block(
    tmp_path: Path, monkeypatch
) -> None:
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
    tex_source = "\n".join(
        [
            "% Panel C -- Localized traps",
            "\\draw[cAmber!75!black, line width=0.60pt] (0,0) -- (1,0);",
            "% =============== Column E -- ISPD-paired =================",
            "\\draw[cAmber!70!black, line width=0.25pt] (0,0) -- (1,0);",
            "% =============== Column F -- Mechanical =================",
            "% v5f Panel F art-direction redraw overlay.",
            "\\fill[white] (9.52, 0.18) rectangle (13.92, 4.34);",
            "\\fill[cGray!30!black, opacity=0.018]",
            "  (12.58, 3.78) rectangle (13.48, 4.14);",
            "\\fill[cGray!3] (12.56, 3.82) rectangle (13.46, 4.16);",
            "\\draw[cGray!58!black, line width=0.22pt, rounded corners=1.0pt]",
            "  (12.56, 3.82) rectangle (13.46, 4.16);",
            "\\node at (12.99, 3.94) {$V_{\\mathrm{active}}$};",
            "\\node at (12.99, 3.84) {bias};",
            "\\draw[cGray!58!black, line width=0.26pt, rounded corners=1.0pt]",
            (
                "  (13.30, 3.78) -- (13.04, 3.52) -- (13.04, 3.16)"
                " -- (13.18, 3.02) -- (13.30, 2.82);"
            ),
            "\\node at (13.64, 1.62) {electrode};",
            "\\foreach \\cx/\\cy/\\rr in {11.62/2.28/0.075,11.43/1.86/0.082} {",
            "  \\shade[ball color=cRed!82!black] (\\cx,\\cy) circle (\\rr);",
            "}",
            "\\draw[cRed!55!black, line width=0.32pt]",
            (
                "  (11.42,2.50) .. controls (10.94,3.24)"
                " and (10.34,3.58) .. (9.72,3.46);"
            ),
            (
                "\\node[anchor=west, fill=white, fill opacity=0.96, text opacity=1,\n"
                "      inner xsep=0.9pt, inner ysep=0.45pt,\n"
                "      font=\\sffamily\\bfseries\\fontsize{4.4}{5.3}\\selectfont, "
                "text=cRed!76!black]\n"
                "  at (9.72, 3.20) {$q_{\\mathrm{tr}}$};"
            ),
            (
                "\\node[anchor=west, fill=white, fill opacity=0.94, text opacity=1,\n"
                "      inner xsep=1.0pt, inner ysep=0.45pt,\n"
                "      font=\\sffamily\\bfseries\\fontsize{4.1}{5.0}\\selectfont, "
                "text=cRed!76!black]\n"
                "  at (9.72, 3.46) {trapped charge};"
            ),
            (
                "\\draw[panelFCoulombRepulsionArrow, "
                "-{Stealth[length=9.6pt,width=6.8pt]}, "
                "cRed!82!black, line width=1.24pt]"
            ),
            "  (11.06, 1.18) -- (9.34, 1.18);",
            (
                "\\node[font=\\sffamily\\bfseries\\fontsize{6.5}{7.8}\\selectfont, "
                "text=cRed!82!black,"
            ),
            "      anchor=south west] at (9.58, 1.54) {Coulomb};",
            (
                "\\node[labelMute, anchor=north west, fill=white, "
                "fill opacity=0.94, text opacity=1,"
            ),
            "      inner xsep=1.2pt, inner ysep=0.6pt,",
            "      font=\\sffamily\\fontsize{6.0}{7.2}\\selectfont,",
            "      text=cRed!82!black] at (9.59, 1.45) {repulsion};",
            "\\draw[<->, cGray!64!black, line width=0.70pt]",
            "  (10.18, 0.54) -- (13.18, 0.54);",
            (
                "\\node[labelMute, anchor=north, fill=white, "
                "fill opacity=0.94, text opacity=1,"
            ),
            "      inner xsep=1.4pt, inner ysep=0.9pt,",
            (
                "      font=\\sffamily\\fontsize{6.0}{7.2}\\selectfont, "
                "text=cGray!75!black]"
            ),
            "  at (11.88, 0.31) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
            "% v8.6 ROW 2 END",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="Panel F final finish typography authority",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    finish = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "panel_f_final_finish"
    ][0]
    operation = finish["operations"][0]
    assert finish["operation_scale"] == "panel_block"
    assert finish["template_id"] == "v5f_panel_f_final_finish_v1"
    assert operation["operation_scale"] == "panel_block"
    assert operation["template_id"] == "v5f_panel_f_final_finish_v1"
    assert "dash pattern=on 1.2pt off 0.9pt" in operation["replacement"]
    assert "(11.38,2.58) .. controls (10.84,3.42)" in operation["replacement"]
    assert "at (9.62, 3.32) {$q_{\\mathrm{tr}}$};" in operation["replacement"]
    assert "at (9.62, 3.58) {trapped charge};" in operation["replacement"]


def test_quality_search_panel_f_label_route_finish_emits_panel_block_candidate(
    tmp_path: Path, monkeypatch
) -> None:
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
    tex_source = "\n".join(
        [
            "% Panel C -- Localized traps",
            "\\draw[cAmber!75!black, line width=0.60pt] (0,0) -- (1,0);",
            "% =============== Column E -- ISPD-paired =================",
            "\\draw[cAmber!70!black, line width=0.25pt] (0,0) -- (1,0);",
            "% =============== Column F -- Mechanical =================",
            "% v5f Panel F art-direction redraw overlay.",
            "\\fill[white] (9.52, 0.18) rectangle (13.92, 4.34);",
            "\\fill[cGray!30!black, opacity=0.010]",
            "  (12.58, 3.78) rectangle (13.48, 4.14);",
            "\\fill[cGray!2] (12.60, 3.86) rectangle (13.40, 4.12);",
            "\\draw[cGray!46!black, line width=0.18pt, rounded corners=1.0pt]",
            "  (12.60, 3.86) rectangle (13.40, 4.12);",
            "\\node at (13.00, 3.96) {$V_{\\mathrm{active}}$};",
            "\\node at (13.00, 3.86) {bias};",
            (
                "\\draw[cGray!52!black, line width=0.22pt, "
                "dash pattern=on 1.2pt off 0.9pt, rounded corners=1.0pt]"
            ),
            "  (13.24, 3.72) -- (13.18, 3.30) -- (13.18, 2.82);",
            "\\node at (13.64, 1.62) {electrode};",
            "\\foreach \\cx/\\cy/\\rr in {11.62/2.28/0.075,11.43/1.86/0.082} {",
            (
                "  \\draw[cRed!35!white, line width=0.25pt, opacity=0.36] "
                "(\\cx,\\cy) circle ({2.35*\\rr});"
            ),
            "  \\shade[ball color=cRed!82!black] (\\cx,\\cy) circle (\\rr);",
            "}",
            "\\draw[cRed!58!black, line width=0.36pt]",
            "  (11.38,2.58) .. controls (10.84,3.42) and (10.14,3.76) .. (9.62,3.64);",
            (
                "\\node[anchor=west, fill=white, fill opacity=0.96, text opacity=1,\n"
                "      inner xsep=0.9pt, inner ysep=0.45pt,\n"
                "      font=\\sffamily\\bfseries\\fontsize{4.2}{5.0}\\selectfont, "
                "text=cRed!76!black]\n"
                "  at (9.62, 3.32) {$q_{\\mathrm{tr}}$};"
            ),
            (
                "\\node[anchor=west, fill=white, fill opacity=0.94, text opacity=1,\n"
                "      inner xsep=1.0pt, inner ysep=0.45pt,\n"
                "      font=\\sffamily\\bfseries\\fontsize{4.0}{4.8}\\selectfont, "
                "text=cRed!76!black]\n"
                "  at (9.62, 3.58) {trapped charge};"
            ),
            "\\node at (9.58, 1.54) {Coulomb};",
            "\\node at (9.59, 1.45) {repulsion};",
            "\\draw[<->, cGray!62!black, line width=0.62pt]",
            "  (10.36, 0.54) -- (13.18, 0.54);",
            "\\node at (11.88, 0.31) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
            "% v8.6 ROW 2 END",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="Panel F label routing finish",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    label_route = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "panel_f_label_route_finish"
    ][0]
    operation = label_route["operations"][0]
    assert label_route["operation_scale"] == "panel_block"
    assert label_route["template_id"] == "v5f_panel_f_label_route_finish_v1"
    assert operation["operation_scale"] == "panel_block"
    assert operation["template_id"] == "v5f_panel_f_label_route_finish_v1"
    assert "circle ({2.05*\\rr})" in operation["replacement"]
    assert "(11.50,2.48) .. controls (11.16,3.04)" in operation["replacement"]
    assert "at (9.74, 3.52) {$q_{\\mathrm{tr}}$};" in operation["replacement"]
    assert "at (9.74, 3.80) {trapped charge};" in operation["replacement"]
    assert "(13.30, 3.72) -- (13.30, 3.28) -- (13.30, 2.82);" in operation[
        "replacement"
    ]


def test_quality_search_panel_f_density_relief_emits_panel_block_candidate(
    tmp_path: Path, monkeypatch
) -> None:
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
    tex_source = "\n".join(
        [
            "% Panel C -- Localized traps",
            "\\draw[cAmber!75!black, line width=0.60pt] (0,0) -- (1,0);",
            "% =============== Column E -- ISPD-paired =================",
            "\\draw[cAmber!70!black, line width=0.25pt] (0,0) -- (1,0);",
            "% =============== Column F -- Mechanical =================",
            "% v5f Panel F art-direction redraw overlay.",
            "\\fill[white] (9.52, 0.18) rectangle (13.92, 4.34);",
            "\\node at (13.02, 4.03) {$V_{\\mathrm{active}}$};",
            "\\node at (13.02, 3.91) {bias};",
            (
                "\\draw[cGray!48!black, line width=0.20pt, "
                "dash pattern=on 1.0pt off 1.0pt, rounded corners=0.7pt]"
            ),
            "  (13.30, 3.72) -- (13.30, 3.28) -- (13.30, 2.82);",
            (
                "\\shade[left color=cGray!34, right color=cGray!18] "
                "(13.18, 0.46) rectangle (13.42, 2.82);"
            ),
            "\\draw[cGray!86!black, line width=0.66pt] (13.18, 0.46) rectangle (13.42, 2.82);",
            (
                "\\foreach \\hy in {0.58,0.74,0.90,1.06,1.22,1.38,"
                "1.54,1.70,1.86,2.02,2.18,2.34,2.50,2.66} {"
            ),
            "  \\draw[cGray!60!black, line width=0.25pt] (13.42, \\hy) -- (13.18, {\\hy-0.06});",
            "}",
            "\\foreach \\yy in {0.92,1.22,1.52,1.82,2.12} {",
            "  \\draw[cGray!25, line width=0.25pt, dash pattern=on 1.2pt off 1.5pt]",
            "    (11.08,\\yy) -- (13.18,\\yy);",
            "}",
            "\\draw[cGray!25, line width=0.25pt, dash pattern=on 1.2pt off 1.5pt]",
            "  (11.08,2.42) -- (11.88,2.42);",
            "\\draw[cGray!25, line width=0.25pt, dash pattern=on 1.2pt off 1.5pt]",
            "  (12.92,2.42) -- (13.18,2.42);",
            (
                "\\node[labelMute, anchor=south, rotate=270, fill=white, "
                "fill opacity=0.95, text opacity=1,"
            ),
            "      inner xsep=1.1pt, inner ysep=0.7pt,",
            (
                "      font=\\sffamily\\fontsize{5.8}{7.0}\\selectfont, "
                "text=cGray!78!black]"
            ),
            "  at (13.64, 1.62) {electrode};",
            "\\foreach \\cx/\\cy/\\rr in {11.62/2.28/0.075,11.43/1.86/0.082} {",
            (
                "  \\draw[cRed!35!white, line width=0.25pt, opacity=0.26] "
                "(\\cx,\\cy) circle ({2.05*\\rr});"
            ),
            "  \\shade[ball color=cRed!82!black] (\\cx,\\cy) circle (\\rr);",
            "}",
            "\\draw[cRed!56!black, line width=0.34pt]",
            "  (11.50,2.48) .. controls (11.16,3.04) and (10.48,3.42) .. (10.12,3.60);",
            "\\node at (9.74, 3.52) {$q_{\\mathrm{tr}}$};",
            "\\node at (9.74, 3.80) {trapped charge};",
            (
                "\\draw[panelFCoulombRepulsionArrow, "
                "-{Stealth[length=9.6pt,width=6.8pt]}, "
                "cRed!82!black, line width=1.24pt]"
            ),
            "  (11.06, 1.18) -- (9.34, 1.18);",
            (
                "\\node[font=\\sffamily\\bfseries\\fontsize{6.5}{7.8}\\selectfont, "
                "text=cRed!82!black,"
            ),
            "      anchor=south west] at (9.58, 1.54) {Coulomb};",
            (
                "\\node[labelMute, anchor=north west, fill=white, "
                "fill opacity=0.94, text opacity=1,"
            ),
            "      inner xsep=1.2pt, inner ysep=0.6pt,",
            "      font=\\sffamily\\fontsize{6.0}{7.2}\\selectfont,",
            "      text=cRed!82!black] at (9.59, 1.45) {repulsion};",
            "\\draw[<->, cGray!62!black, line width=0.62pt]",
            "  (10.36, 0.54) -- (13.18, 0.54);",
            (
                "\\node[labelMute, anchor=north, fill=white, "
                "fill opacity=0.94, text opacity=1,"
            ),
            "      inner xsep=1.4pt, inner ysep=0.9pt,",
            (
                "      font=\\sffamily\\fontsize{6.0}{7.2}\\selectfont, "
                "text=cGray!75!black]"
            ),
            "  at (11.88, 0.31) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
            "% v8.6 ROW 2 END",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="Panel F density relief",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    density = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "panel_f_density_relief"
    ][0]
    operation = density["operations"][0]
    assert density["operation_scale"] == "panel_block"
    assert density["template_id"] == "v5f_panel_f_density_relief_v1"
    assert operation["operation_scale"] == "panel_block"
    assert operation["template_id"] == "v5f_panel_f_density_relief_v1"
    assert "\\foreach \\yy in {0.96,1.34,1.72,2.10}" in operation["replacement"]
    assert "-{Stealth[length=8.2pt,width=5.8pt]}" in operation["replacement"]
    assert "(10.86, 1.18) -- (9.48, 1.18);" in operation["replacement"]
    assert "fontsize{5.8}{7.0}" in operation["replacement"]
    assert "text=cGray!70!black" in operation["replacement"]


def test_quality_search_panel_c_hero_finish_emits_panel_block_candidate(
    tmp_path: Path, monkeypatch
) -> None:
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
    tex_source = "\n".join(
        [
            "% Panel C -- Localized traps",
            "\\node at (8.70, 6.03) {poly(S-r-DIB) thin film};",
            "\\fill[cBlue!12, opacity=0.20, rounded corners=1pt] "
            "(10.38, 7.18) rectangle (13.55, 7.82);",
            "\\fill[cRed!12, opacity=0.18, rounded corners=1pt] "
            "(10.38, 5.55) rectangle (13.55, 6.55);",
            "\\node at (12.08, 8.06) {mobility edge};",
            "\\fill[cBlue!52, opacity=0.85]",
            "  plot[domain=7.20:7.80, samples=25, smooth]",
            "    ({10.55 + 0.45*exp(-(\\x-7.49)*(\\x-7.49)/0.01445)}, \\x)",
            "  -- (10.55, 7.80) -- (10.55, 7.20) -- cycle;",
            "\\draw[cBlue!80!black, line width=0.60pt]",
            "  plot[domain=7.20:7.80, samples=25, smooth]",
            "    ({10.55 + 0.45*exp(-(\\x-7.49)*(\\x-7.49)/0.01445)}, \\x);",
            "\\fill[cRed!52, opacity=0.80]",
            "  plot[domain=5.40:6.70, samples=30, smooth]",
            "    ({10.55 + 0.55*exp(-(\\x-6.05)*(\\x-6.05)/0.0648)}, \\x)",
            "  -- (10.55, 6.70) -- (10.55, 5.40) -- cycle;",
            "\\draw[cRed!80!black, line width=0.65pt]",
            "  plot[domain=5.40:6.70, samples=30, smooth]",
            "    ({10.55 + 0.55*exp(-(\\x-6.05)*(\\x-6.05)/0.0648)}, \\x);",
            "\\foreach \\tY in {7.55, 7.35} {",
            "  \\draw[cBlue!80!black, line width=1.15pt, line cap=butt] "
            "(10.95, \\tY) -- (11.55, \\tY);",
            "}",
            "\\foreach \\tY in {6.20, 5.85} {",
            "  \\draw[cRed!80!black, line width=1.15pt, line cap=butt] "
            "(10.95, \\tY) -- (11.55, \\tY);",
            "}",
            "\\node at (12.15, 7.58) {shallow};",
            "\\node at (11.60, 6.02) {deep};",
            "\\node at (13.42, 7.00) {$\\Delta E_t$};",
            "\\node[labelMute, anchor=south,",
            "      font=\\sffamily\\itshape\\fontsize{6}{7.2}\\selectfont,",
            "      text=cGray!65!black] at (8.35, 8.78) {real space};",
            "\\node[labelMute, anchor=south,",
            "      font=\\sffamily\\itshape\\fontsize{6}{7.2}\\selectfont,",
            "      text=cGray!65!black] at (12.20, 8.78) {energy diagram};",
            "\\node[anchor=south,",
            "      font=\\sffamily\\bfseries\\fontsize{7}{8.4}\\selectfont,",
            "      text=cGray!78!black] at (10.40, 8.92) {localized trap model};",
            "% =============== Column F -- Mechanical =================",
            "% v5f Panel F art-direction redraw overlay.",
            "\\node at (13.64, 1.62) {electrode};",
            "\\node at (9.60, 3.36) {trapped charge};",
            "\\node at (9.72, 1.54) {Coulomb};",
            "\\node at (9.73, 1.45) {repulsion};",
            "\\node at (11.88, 0.31) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
            "% v8.6 ROW 2 END",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="Panel C hero finish typography authority",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    panel_c = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "panel_c_hero_finish"
    ][0]
    operation = panel_c["operations"][0]
    assert panel_c["operation_scale"] == "panel_block"
    assert panel_c["template_id"] == "v5f_panel_c_hero_finish_v1"
    assert panel_c["target"]["panel"] == "C"
    assert operation["operation_scale"] == "panel_block"
    assert operation["template_id"] == "v5f_panel_c_hero_finish_v1"
    assert operation["panel"] == "C"
    assert "\\fill[cBlue!16, opacity=0.26, rounded corners=1pt]" in operation["replacement"]
    assert "\\fill[cRed!16, opacity=0.24, rounded corners=1pt]" in operation["replacement"]
    assert "\\draw[cBlue!84!black, line width=0.68pt]" in operation["replacement"]
    assert "\\draw[cRed!84!black, line width=0.72pt]" in operation["replacement"]
    assert "line width=1.24pt, line cap=butt" in operation["replacement"]
    assert "fontsize{7.4}{8.8}" in operation["replacement"]
    assert "text=cGray!58!black] at (8.35, 8.78) {real space};" in operation["replacement"]
    assert "text=cGray!58!black] at (12.20, 8.78) {energy diagram};" in operation[
        "replacement"
    ]


def test_quality_search_density_reduce_emits_panel_e_block_candidate(
    tmp_path: Path, monkeypatch
) -> None:
    ledger = _ledger_with_actionable_and_unbound_defects()
    defect = ledger["defects"][0]
    assert isinstance(defect, dict)
    target = defect["target"]
    assert isinstance(target, dict)
    target["panel"] = "E"
    monkeypatch.setattr(
        quality_search.fig_driver,
        "build_driver_summary",
        lambda *_args, **_kwargs: _driver_with_basin(),
    )
    monkeypatch.setattr(
        quality_search.quality_defect_ledger,
        "build_quality_defect_ledger",
        lambda *_args, **_kwargs: ledger,
    )
    monkeypatch.setattr(
        quality_search.quality_memory_index,
        "build_fixture_index",
        lambda *_args, **_kwargs: {"event_count": 0, "candidate_event_count": 0},
    )
    tex_source = "\n".join(
        [
            "% Panel C -- Localized traps",
            "\\draw[cAmber!75!black, line width=0.60pt] (0,0) -- (1,0);",
            "% =============== Column E -- ISPD-paired =================",
            "\\fill[cGray!6, rounded corners=1.2pt] (5.83, 4.12) rectangle (6.48, 4.37);",
            "\\draw[cGray!60!black, line width=0.30pt, rounded corners=1.2pt]",
            "  (5.83, 4.12) rectangle (6.48, 4.37);",
            "\\fill[cGray!70!black, rounded corners=1pt] (5.90, 4.20) rectangle (6.36, 4.33);",
            "\\fill[cGray!45!black, opacity=0.5] (5.92, 4.318) rectangle (6.34, 4.324);",
            "\\node at (5.80, 4.10) {HV+};",
            "\\foreach \\cx in {6.95, 7.30} {",
            "  \\node[font=\\sffamily\\bfseries\\fontsize{4}{4.8}\\selectfont, text=white,",
            "        inner sep=0pt] at (\\cx, 3.62) {$+$};",
            "}",
            "\\node[font=\\sffamily\\fontsize{5.5}{6.6}\\selectfont, text=cGray!55!black,",
            "      anchor=south] at (7.1, 4.10) {$V_s$ probe};",
            "\\fill[cGray!6, rounded corners=1.2pt] (7.68, 3.70) rectangle (8.68, 4.22);",
            "\\draw[cGray!60!black, line width=0.30pt, rounded corners=1.2pt]",
            "  (7.68, 3.70) rectangle (8.68, 4.22);",
            "\\fill[cGray!70!black, rounded corners=1pt] (7.80, 4.05) rectangle (8.56, 4.17);",
            "\\fill[cGray!45!black, opacity=0.5] (7.82, 4.158) rectangle (8.54, 4.165);",
            "\\node[font=\\sffamily\\fontsize{5.5}{6.6}\\selectfont, text=cGray!55!black]",
            "  at (8.18, 3.86) {$V_s$ meter};",
            "\\node at (4.72, 3.50) {polymer};",
            "\\node at (4.93, 2.55) {$V_s(t)$};",
            "\\node at (4.93, 1.25) {$g(E_t)$};",
            "\\node at (5.9, 0.36) {Shallow};",
            "\\node at (6.98, 0.36) {Deep};",
            "% =============== Column F -- Mechanical =================",
            "% v5f Panel F art-direction redraw overlay.",
            "\\node at (13.64, 1.62) {electrode};",
            "\\node at (9.60, 3.36) {trapped charge};",
            "\\node at (9.72, 1.54) {Coulomb};",
            "\\node at (9.73, 1.45) {repulsion};",
            "\\node at (11.88, 0.31) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
            "% v8.6 ROW 2 END",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="density reduce panel e",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    density = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "density_reduce"
    ][0]
    operation = density["operations"][0]
    assert density["operation_scale"] == "panel_block"
    assert density["template_id"] == "row2_panel_e_density_reduce_v1"
    assert density["target"]["panel"] == "E"
    assert operation["panel"] == "E"
    assert operation["operation_scale"] == "panel_block"
    assert operation["template_id"] == "row2_panel_e_density_reduce_v1"
    assert "\\foreach \\cx in {6.95, 7.30} {" in operation["replacement"]
    assert (
        "  \\node[font=\\sffamily\\bfseries\\fontsize{4}{4.8}\\selectfont, text=white,\n"
        "        opacity=0.72, inner sep=0pt] at (\\cx, 3.62) {$+$};"
        in operation["replacement"]
    )
    assert (
        "\\node[font=\\sffamily\\fontsize{5.5}{6.6}\\selectfont, text=cGray!55!black,\n"
        "      anchor=south] at (7.1, 4.10) {$V_s$ probe};"
        in operation["replacement"]
    )
    assert (
        "\\node[font=\\sffamily\\fontsize{5.5}{6.6}\\selectfont, text=cGray!55!black]\n"
        "  at (8.18, 3.86) {$V_s$ meter};"
        in operation["replacement"]
    )
    score = [
        item
        for item in payload["candidate_scores"]
        if item["candidate_id"] == density["id"]
    ][0]
    assert score["operation_scale"] == "panel_block"
    assert score["template_id"] == "row2_panel_e_density_reduce_v1"
    applied_lines = operation["replacement"].splitlines(keepends=True)
    applied_selector = {
        "kind": "tex_selector.v1",
        "binding_state": "bound",
        "panel": "E",
        "line_start": 1,
        "line_end": len(applied_lines),
    }
    assert quality_search._density_panel_e_template_applied(
        lines=applied_lines,
        selector=applied_selector,
    )
    blocked_operation, refusal = quality_search._candidate_operation_for_spec(
        {
            "id": "QS003",
            "family": "density_reduce",
            "source_selectors": [applied_selector],
        },
        lines=applied_lines,
        source_ref="fig_demo.tex",
    )
    assert blocked_operation is None
    assert refusal == {
        "code": "template_already_applied",
        "candidate_id": "QS003",
        "family": "density_reduce",
        "operation_scale": "panel_block",
        "template_id": "row2_panel_e_density_reduce_v1",
        "panel": "E",
    }


def test_quality_search_goal_promotes_panel_f_apparatus_without_basin(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        quality_search.fig_driver,
        "build_driver_summary",
        lambda *_args, **_kwargs: _driver_ready_without_basin(),
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
    tex_source = "\n".join(
        [
            "% =============== Column B -- Results =================",
            "\\draw[cGray!60, line width=0.30pt] (0,0) -- (1,0);",
            "% =============== Column F -- Mechanical =================",
            "% v5f Panel F art-direction redraw overlay.",
            "\\fill[cGray!30!black, opacity=0.045]",
            "  (12.65, 3.55) rectangle (13.58, 4.12);",
            "\\draw[cGray!58!black, line width=0.26pt]",
            "  (12.60, 3.62) rectangle (13.52, 4.17);",
            "\\node at (13.06, 3.82) {$V_{\\mathrm{active}}$};",
            "\\node at (13.06, 3.70) {bias};",
            "\\draw[cGray!60!black, line width=0.24pt, rounded corners=1.1pt]",
            "  (13.42, 4.01) -- (13.62, 4.01) -- (13.62, 2.82) -- (13.42, 2.82);",
            "\\draw[cGray!86!black, line width=0.66pt] (13.18, 0.46) rectangle (13.42, 2.82);",
            "\\node at (13.64, 1.62) {electrode};",
            "\\foreach \\cx/\\cy/\\rr in {11.62/2.28/0.075,11.43/1.86/0.082} {",
            (
                "  \\draw[cRed!35!white, line width=0.25pt, opacity=0.36] "
                "(\\cx,\\cy) circle ({1.65*\\rr});"
            ),
            "  \\shade[ball color=cRed!76!black] (\\cx,\\cy) circle (\\rr);",
            "}",
            "\\draw[cRed!45!black, line width=0.22pt]",
            "  (11.58,2.35) .. controls (11.28,2.56) and (10.90,2.64) .. (10.48,2.62);",
            "\\node at (9.80, 2.60) {$q_{\\mathrm{tr}}$};",
            "\\node at (10.08, 2.60) {trapped charge};",
            (
                "\\draw[panelFCoulombRepulsionArrow, "
                "-{Stealth[length=7.6pt,width=5.6pt]}, "
                "cRed!82!black, line width=0.94pt]"
            ),
            "  (11.02, 1.18) -- (9.60, 1.18);",
            "\\node at (9.72, 1.54) {Coulomb};",
            "\\node at (9.73, 1.45) {repulsion};",
            "\\draw[<->, cGray!62!black, line width=0.38pt]",
            "  (10.42, 0.54) -- (13.18, 0.54);",
            "\\node at (11.88, 0.31) {air gap};",
            "\\node at (11.70, 4.56) {mechanical};",
            "% v8.6 ROW 2 END",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="Panel F apparatus charge force electrode air gap strengthen",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    families = [item["family"] for item in payload["candidate_specs"]]
    assert families[0] == "apparatus_strengthen"
    apparatus = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "apparatus_strengthen"
    ][0]
    operation = apparatus["operations"][0]
    assert apparatus["operation_scale"] == "panel_block"
    assert apparatus["template_id"] == "v5f_panel_f_redraw_overlay_v1"
    assert operation["operation_scale"] == "panel_block"
    assert "trapped charge" in operation["replacement"]
    assert "air gap" in operation["replacement"]
    by_family = {item["family"]: item for item in payload["candidate_scores"]}
    assert by_family["apparatus_strengthen"]["policy_score"] > by_family[
        "label_reflow"
    ]["policy_score"]


def test_quality_search_policy_uses_epsilon_greedy_bandit_from_memory() -> None:
    decision = quality_search._epsilon_greedy_bandit_decision(
        {
            "state": {
                "memory": {
                    "state": "loaded",
                    "families": {
                        "hierarchy_rebalance": {
                            "attempts": 4,
                            "improved": 4,
                            "neutral": 0,
                            "regressed": 0,
                            "recommended_prior": 0.25,
                        },
                        "apparatus_strengthen": {
                            "attempts": 4,
                            "improved": 0,
                            "neutral": 0,
                            "regressed": 4,
                            "recommended_prior": -0.25,
                        },
                    },
                }
            },
            "next_recommended_operation": {"kind": "step_out_experiment"},
        },
        ["hierarchy_rebalance", "apparatus_strengthen"],
        epsilon=0.0,
    )

    assert decision["schema"] == "figure-agent.quality-search-bandit-policy.v1"
    assert decision["kind"] == "epsilon_greedy_family_bandit_v1"
    assert decision["selection_mode"] == "exploit"
    assert decision["selected_family"] == "hierarchy_rebalance"
    assert decision["opaque_model_dependency"] is False
    assert decision["statistics_source"] == "experience_log_via_quality_memory_index"
    assert decision["arm_statistics"]["hierarchy_rebalance"]["attempts"] == 4
    assert decision["arm_statistics"]["hierarchy_rebalance"]["empirical_reward"] == 1.0


def test_quality_search_policy_uses_memory_prior_and_bandit_bonus() -> None:
    plan = {
        "state": {
            "memory": {
                "state": "loaded",
                "families": {
                    "hierarchy_rebalance": {
                        "attempts": 8,
                        "recommended_prior": -0.1,
                    },
                    "apparatus_strengthen": {
                        "attempts": 0,
                        "recommended_prior": 0.0,
                    },
                },
            }
        },
        "classifications": [],
        "next_recommended_operation": {"kind": "step_out_experiment"},
    }
    candidate_specs = [
        {
            "id": "QS001",
            "family": "hierarchy_rebalance",
            "operation_scale": "local_style_token",
        },
        {
            "id": "QS002",
            "family": "apparatus_strengthen",
            "operation_scale": "panel_block",
        },
    ]
    rankings = [
        {
            "candidate_id": "QS001",
            "rank_score": 0.65,
            "render_status": "rendered_needs_human_review",
            "effective_apply_authority": "review_only",
            "scores": {"changed_pixel_ratio": 0.002},
        },
        {
            "candidate_id": "QS002",
            "rank_score": 0.75,
            "render_status": "rendered_needs_human_review",
            "effective_apply_authority": "review_only",
            "scores": {"changed_pixel_ratio": 0.003},
        },
    ]

    scores = quality_search._candidate_scores(candidate_specs, plan, rankings)
    decision = quality_search._execution_decision(plan, scores)

    by_family = {item["family"]: item for item in scores}
    hierarchy = by_family["hierarchy_rebalance"]
    apparatus = by_family["apparatus_strengthen"]
    assert hierarchy["policy"]["memory_prior"] == -0.1
    assert hierarchy["policy"]["bandit_bonus"] == 0.0
    assert apparatus["policy"]["memory_prior"] == 0.0
    assert apparatus["policy"]["bandit_decision"]["selected_family"] == "apparatus_strengthen"
    assert apparatus["policy"]["bandit_bonus"] > 0
    assert apparatus["policy_score"] > hierarchy["policy_score"]
    assert decision["selected_candidate_id"] == "QS002"
    assert decision["selected_family"] == "apparatus_strengthen"
    assert decision["candidate_state"] == "non_marginal_review_candidate_ready"
    assert decision["automation_boundary"] == "review_only_candidate_ready"
    assert decision["next_action"] == "review selected candidate evidence"
    assert decision["review_command"] == "fig-agent review-candidate <fixture> QS002"
    assert decision["policy"]["schema"] == "figure-agent.quality-search-bandit-policy.v1"
    assert decision["policy"]["kind"] == "epsilon_greedy_family_bandit_v1"


def test_quality_search_memory_summary_preserves_duplicate_diagnostics() -> None:
    summary = quality_search._memory_summary(
        {
            "event_count": 14,
            "candidate_event_count": 14,
            "eligible_prior_count": 0,
            "counterfactual_unchosen_count": 3,
            "duplicate_experience_attempt_count": 10,
            "duplicate_experience_attempt_rate": 0.7143,
            "families": {"panel_f_qtr_apparatus_lane": {"attempts": 1}},
        }
    )

    assert summary["counterfactual_unchosen_count"] == 3
    assert summary["duplicate_experience_attempt_count"] == 10
    assert summary["duplicate_experience_attempt_rate"] == 0.7143


def test_quality_search_policy_penalizes_duplicate_experience_family() -> None:
    plan = {
        "state": {
            "memory": {
                "state": "loaded",
                "duplicate_experience_attempt_rate": 0.7143,
                "families": {
                    "panel_f_qtr_apparatus_lane": {
                        "attempts": 1,
                        "recommended_prior": 0.0,
                    },
                    "panel_f_qtr_label_lane": {
                        "attempts": 0,
                        "recommended_prior": 0.0,
                    },
                },
            }
        },
        "classifications": [],
        "next_recommended_operation": {"kind": "step_out_experiment"},
    }
    candidate_specs = [
        {
            "id": "QS001",
            "family": "panel_f_qtr_apparatus_lane",
            "operation_scale": "panel_block",
        },
        {
            "id": "QS002",
            "family": "panel_f_qtr_label_lane",
            "operation_scale": "panel_block",
        },
    ]
    rankings = [
        {
            "candidate_id": "QS001",
            "rank_score": 0.75,
            "render_status": "rendered_needs_human_review",
            "effective_apply_authority": "review_only",
            "scores": {"changed_pixel_ratio": 0.003},
        },
        {
            "candidate_id": "QS002",
            "rank_score": 0.75,
            "render_status": "rendered_needs_human_review",
            "effective_apply_authority": "review_only",
            "scores": {"changed_pixel_ratio": 0.003},
        },
    ]

    scores = quality_search._candidate_scores(candidate_specs, plan, rankings)
    by_family = {item["family"]: item for item in scores}

    assert by_family["panel_f_qtr_apparatus_lane"]["policy"][
        "duplicate_experience_penalty"
    ] == -0.05
    assert by_family["panel_f_qtr_label_lane"]["policy"][
        "duplicate_experience_penalty"
    ] == 0.0
    assert by_family["panel_f_qtr_label_lane"]["policy_score"] > by_family[
        "panel_f_qtr_apparatus_lane"
    ]["policy_score"]


def test_quality_search_execution_skips_stale_duplicate_family() -> None:
    decision = quality_search._execution_decision(
        {"classifications": []},
        [
            {
                "candidate_id": "QS001",
                "family": "panel_f_qtr_apparatus_lane",
                "operation_scale": "panel_block",
                "template_id": "v5d_panel_f_qtr_apparatus_lane_v1",
                "evidence_score": 0.67,
                "policy_score": 0.95,
                "full_changed_pixel_ratio": 0.005,
                "panel_changed_pixel_ratio": 0.005,
                "non_marginal_visual_change": True,
                "stale_duplicate_experience_family": True,
                "policy": {"duplicate_experience_penalty": -0.05},
            },
            {
                "candidate_id": "QS002",
                "family": "panel_f_qtr_label_lane",
                "operation_scale": "panel_block",
                "template_id": "v5d_panel_f_qtr_label_lane_v1",
                "evidence_score": 0.67,
                "policy_score": 0.72,
                "full_changed_pixel_ratio": 0.004,
                "panel_changed_pixel_ratio": 0.004,
                "non_marginal_visual_change": True,
                "stale_duplicate_experience_family": False,
                "policy": {"duplicate_experience_penalty": 0.0},
            },
        ],
        fixture_name="fig1_overview_v5d_redraw_001_vault",
    )

    assert decision["kind"] == "candidate_batch_ready"
    assert decision["selected_candidate_id"] == "QS002"
    assert decision["selected_family"] == "panel_f_qtr_label_lane"


def test_quality_search_execution_reports_stale_duplicate_when_no_fresh_candidate() -> None:
    decision = quality_search._execution_decision(
        {"classifications": []},
        [
            {
                "candidate_id": "QS001",
                "family": "panel_f_qtr_apparatus_lane",
                "operation_scale": "panel_block",
                "template_id": "v5d_panel_f_qtr_apparatus_lane_v1",
                "evidence_score": 0.67,
                "policy_score": 0.72,
                "full_changed_pixel_ratio": 0.005,
                "panel_changed_pixel_ratio": 0.005,
                "non_marginal_visual_change": True,
                "stale_duplicate_experience_family": True,
                "policy": {"duplicate_experience_penalty": -0.05},
            },
            {
                "candidate_id": "QS002",
                "family": "panel_f_qtr_label_lane",
                "operation_scale": "panel_block",
                "template_id": "v5d_panel_f_qtr_label_lane_v1",
                "evidence_score": 0.67,
                "policy_score": 0.724,
                "full_changed_pixel_ratio": 0.001,
                "panel_changed_pixel_ratio": 0.001,
                "non_marginal_visual_change": False,
                "stale_duplicate_experience_family": False,
                "policy": {"duplicate_experience_penalty": 0.0},
            },
        ],
        fixture_name="fig1_overview_v5d_redraw_001_vault",
    )

    assert decision["kind"] == "no_non_marginal_candidate"
    assert decision["selected_candidate_id"] is None
    assert decision["stale_duplicate_non_marginal_candidate_count"] == 1
    assert "fresh non-marginal candidate" in decision["reason"]


def test_quality_search_policy_prefers_panel_block_with_stronger_render_rank() -> None:
    plan = {
        "state": {"memory": {"state": "loaded", "families": {}}},
        "classifications": [
            {
                "kind": "release_blocker",
                "blocks_search": False,
            }
        ],
        "next_recommended_operation": {"kind": "step_out_experiment"},
    }
    candidate_specs = [
        {
            "id": "QS001",
            "family": "hierarchy_rebalance",
            "operation_scale": "local_style_token",
            "template_id": "line_width_minimum_v1",
            "expected_visual_movement": "local line-width change",
        },
        {
            "id": "QS002",
            "family": "apparatus_strengthen",
            "operation_scale": "panel_block",
            "template_id": "v5f_panel_f_redraw_overlay_v1",
            "expected_visual_movement": "Panel F apparatus reads as deliberate mechanism evidence",
        },
    ]
    rankings = [
        {
            "candidate_id": "QS001",
            "rank_score": 0.65,
            "render_status": "rendered_needs_human_review",
            "effective_apply_authority": "review_only",
            "scores": {"changed_pixel_ratio": 0.0008},
        },
        {
            "candidate_id": "QS002",
            "rank_score": 0.75,
            "render_status": "rendered_needs_human_review",
            "effective_apply_authority": "review_only",
            "scores": {"changed_pixel_ratio": 0.003},
        },
    ]

    scores = quality_search._candidate_scores(candidate_specs, plan, rankings)
    decision = quality_search._execution_decision(plan, scores)

    by_family = {item["family"]: item for item in scores}
    assert by_family["apparatus_strengthen"]["policy_score"] > by_family[
        "hierarchy_rebalance"
    ]["policy_score"]
    assert decision["selected_candidate_id"] == "QS002"
    assert decision["selected_family"] == "apparatus_strengthen"
    assert decision["candidate_state"] == "non_marginal_review_candidate_ready"
    assert decision["selected_operation_scale"] == "panel_block"
    assert decision["selected_template_id"] == "v5f_panel_f_redraw_overlay_v1"
    assert decision["non_marginal_visual_change"] is True
    assert decision["full_changed_pixel_ratio"] == 0.003
    assert decision["next_action"] == "review selected candidate evidence"


def test_quality_search_decision_rejects_only_marginal_rendered_candidates() -> None:
    plan = {
        "state": {"memory": {"state": "loaded", "families": {}}},
        "classifications": [],
        "next_recommended_operation": {"kind": "step_out_experiment"},
    }
    candidate_specs = [
        {
            "id": "QS001",
            "family": "hierarchy_rebalance",
            "operation_scale": "local_style_token",
            "template_id": "line_width_minimum_v1",
            "expected_visual_movement": "local line-width change",
        },
        {
            "id": "QS002",
            "family": "apparatus_strengthen",
            "operation_scale": "local_style_token",
            "template_id": "line_width_minimum_v1",
            "expected_visual_movement": "local line-width change",
        },
    ]
    rankings = [
        {
            "candidate_id": "QS001",
            "rank_score": 0.65,
            "render_status": "rendered_needs_human_review",
            "effective_apply_authority": "review_only",
            "scores": {"changed_pixel_ratio": 0.000816},
        },
        {
            "candidate_id": "QS002",
            "rank_score": 0.55,
            "render_status": "rendered_needs_human_review",
            "effective_apply_authority": "review_only",
            "scores": {"changed_pixel_ratio": 0.000486},
        },
    ]

    scores = quality_search._candidate_scores(candidate_specs, plan, rankings)
    decision = quality_search._execution_decision(plan, scores)

    assert all(item["non_marginal_visual_change"] is False for item in scores)
    assert decision["kind"] == "no_non_marginal_candidate"
    assert decision["selected_candidate_id"] is None
    assert decision["source_mutation"] == "not_performed"
    assert decision["top_candidate_id"] == "QS001"
    assert decision["top_candidate_full_changed_pixel_ratio"] == 0.000816
    assert decision["non_marginal_thresholds"] == {
        "full_changed_pixel_ratio": 0.002,
        "panel_changed_pixel_ratio": 0.02,
    }


def test_quality_search_decision_accepts_panel_crop_non_marginal_candidate() -> None:
    plan = {
        "state": {"memory": {"state": "loaded", "families": {}}},
        "classifications": [],
        "next_recommended_operation": {"kind": "step_out_experiment"},
    }
    candidate_specs = [
        {
            "id": "QS001",
            "family": "hierarchy_rebalance",
            "operation_scale": "local_style_token",
        },
        {
            "id": "QS002",
            "family": "apparatus_strengthen",
            "operation_scale": "panel_block",
        },
    ]
    rankings = [
        {
            "candidate_id": "QS001",
            "rank_score": 0.65,
            "render_status": "rendered_needs_human_review",
            "effective_apply_authority": "review_only",
            "scores": {"changed_pixel_ratio": 0.0009},
        },
        {
            "candidate_id": "QS002",
            "rank_score": 0.75,
            "render_status": "rendered_needs_human_review",
            "effective_apply_authority": "review_only",
            "scores": {"changed_pixel_ratio": 0.001},
        },
    ]
    visual_evidence = {
        "full_comparisons": [
            {
                "candidate_id": "QS001",
                "visual_deltas": {"changed_pixel_ratio": 0.0009},
            },
            {
                "candidate_id": "QS002",
                "visual_deltas": {"changed_pixel_ratio": 0.001},
            },
        ],
        "panel_comparisons": [
            {
                "candidate_id": "QS002",
                "visual_deltas": {"changed_pixel_ratio": 0.021},
            }
        ],
    }

    scores = quality_search._candidate_scores(
        candidate_specs,
        plan,
        rankings,
        visual_evidence,
    )
    decision = quality_search._execution_decision(plan, scores)

    by_id = {item["candidate_id"]: item for item in scores}
    assert by_id["QS001"]["non_marginal_visual_change"] is False
    assert by_id["QS002"]["non_marginal_visual_change"] is True
    assert by_id["QS002"]["panel_changed_pixel_ratio"] == 0.021
    assert decision["selected_candidate_id"] == "QS002"
    assert decision["selected_family"] == "apparatus_strengthen"
    assert decision["candidate_state"] == "non_marginal_review_candidate_ready"
    assert decision["selected_operation_scale"] == "panel_block"
    assert decision["non_marginal_visual_change"] is True
    assert decision["full_changed_pixel_ratio"] == 0.001
    assert decision["panel_changed_pixel_ratio"] == 0.021
    assert decision["non_marginal_thresholds"] == {
        "full_changed_pixel_ratio": 0.002,
        "panel_changed_pixel_ratio": 0.02,
    }
    assert decision["next_action"] == "review selected candidate evidence"


def test_quality_search_builds_selected_review_packet_for_ready_candidate(
    tmp_path: Path, monkeypatch
) -> None:
    paths = quality_search.runtime_paths.resolve_runtime_paths(
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )
    decision = {
        "candidate_state": "non_marginal_review_candidate_ready",
        "selected_candidate_id": "QS002",
    }

    def fake_review_packet(
        name: str,
        candidate_id: str,
        *,
        plugin_root: Path,
        workspace_root: Path,
    ) -> dict[str, object]:
        assert name == "fig_demo"
        assert candidate_id == "QS002"
        assert plugin_root == PLUGIN_ROOT
        assert workspace_root == tmp_path
        return {
            "schema": "figure-agent.candidate-review-packet.v1",
            "candidate_id": candidate_id,
            "render_status": "rendered_needs_human_review",
        }

    monkeypatch.setattr(
        quality_search.candidate_review_packet,
        "build_review_packet",
        fake_review_packet,
    )

    packet = quality_search._selected_review_packet("fig_demo", decision, paths=paths)

    assert packet == {
        "schema": "figure-agent.candidate-review-packet.v1",
        "candidate_id": "QS002",
        "render_status": "rendered_needs_human_review",
        "status": "ready",
    }


def test_quality_search_writes_selected_semantic_precheck_for_protected_panel_block(
    tmp_path: Path,
) -> None:
    name = "fig_demo"
    candidate_id = "QS002"
    paths = quality_search.runtime_paths.resolve_runtime_paths(
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )
    sandbox = paths.examples_dir / name / "build" / "candidates" / candidate_id
    sandbox.mkdir(parents=True)
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "fixture": name,
        "candidate_id": candidate_id,
        "candidate_hash": "sha256:" + "3" * 64,
        "operations": [
            {
                "kind": "replace_text",
                "replacement": (
                    "$q_{tr}$ trapped charge Coulomb repulsion electrode "
                    "air gap Mechanical $V_{\\mathrm{active}}$"
                ),
            }
        ],
    }
    render_manifest = {
        "schema": "figure-agent.candidate-render-manifest.v1",
        "candidate_id": candidate_id,
        "candidate_hash": manifest["candidate_hash"],
        "stages": {
            "compile": {"status": "success"},
            "export": {"status": "success"},
            "crop": {"status": "success"},
            "evaluate": {"status": "rendered_needs_human_review"},
        },
    }
    (sandbox / "candidate_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sandbox / "render_manifest.json").write_text(
        json.dumps(render_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    decision = {
        "candidate_state": "non_marginal_review_candidate_ready",
        "selected_candidate_id": candidate_id,
    }
    candidate_set = {
        "candidates": [
            {
                "id": candidate_id,
                "apply_authority": "review_only",
                "protected_labels": [
                    "q_tr",
                    "trapped charge",
                    "Coulomb",
                    "repulsion",
                    "electrode",
                    "air gap",
                    "mechanical",
                    "$V_{\\mathrm{active}}$",
                ],
            }
        ]
    }

    precheck = quality_search._write_selected_semantic_precheck(
        name,
        decision,
        candidate_set,
        paths=paths,
    )

    review_path = sandbox / "semantic_review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    assert precheck["status"] == "pass"
    assert precheck["review_path"] == (
        "examples/fig_demo/build/candidates/QS002/semantic_review.json"
    )
    assert review["verdict"] == "pass"
    assert review["human_required"] is False
    assert review["reviewer"] == "fig-agent-auto-semantic-precheck"
    assert {item["label"] for item in review["semantic_invariants"]} == set(
        candidate_set["candidates"][0]["protected_labels"]
    )


def test_quality_search_recommends_acceptance_without_authorizing_apply() -> None:
    decision = {
        "candidate_state": "non_marginal_review_candidate_ready",
        "selected_candidate_id": "QS002",
        "full_changed_pixel_ratio": 0.004,
        "panel_changed_pixel_ratio": 0.03,
    }
    semantic_precheck = {
        "status": "pass",
        "protected_labels": ["q_tr", "Coulomb"],
    }
    review_packet = {
        "status": "ready",
        "apply_readiness": {
            "status": "ready_for_local_acceptance",
            "required_commands": [
                (
                    "fig-agent accept-candidate fig_demo QS002 --candidate-set "
                    ".scratch/run/candidate_set_000.json --decision accept "
                    "--reviewer <name> --rationale <text> --json"
                ),
                (
                    "fig-agent apply-candidate fig_demo QS002 --candidate-set "
                    ".scratch/run/candidate_set_000.json --acceptance "
                    "build/candidates/QS002/acceptance.json --json"
                ),
            ],
        },
    }

    recommendation = quality_search._selected_acceptance_recommendation(
        decision,
        semantic_precheck,
        review_packet,
    )

    assert recommendation["schema"] == (
        "figure-agent.selected-acceptance-recommendation.v0"
    )
    assert recommendation["status"] == "auto_accept_recommended"
    assert recommendation["recommendation"] == "accept"
    assert recommendation["authority"] == "recommendation_only"
    assert recommendation["is_acceptance_artifact"] is False
    assert recommendation["source_mutation"] == "not_performed"
    assert recommendation["evidence"]["semantic_precheck_status"] == "pass"
    assert recommendation["evidence"]["apply_readiness_status"] == (
        "ready_for_local_acceptance"
    )
    assert recommendation["required_commands"] == review_packet["apply_readiness"][
        "required_commands"
    ]


def test_quality_search_visual_evidence_writes_full_and_panel_contact_sheets(
    tmp_path: Path,
) -> None:
    fixture = _write_minimal_fixture(tmp_path, name="fig_demo")
    _write_png(fixture / "build" / "fig_demo.png", (255, 255, 255))
    candidate_dir = fixture / "build" / "candidates" / "QS001"
    _write_png(candidate_dir / "render" / "candidate.png", (0, 0, 0))
    _write_png(candidate_dir / "crops" / "original_panel_C.png", (255, 255, 255))
    _write_png(candidate_dir / "crops" / "candidate_panel_C.png", (0, 0, 0))
    render_manifest = {
        "schema": "figure-agent.candidate-render-manifest.v1",
        "candidate_id": "QS001",
        "panel": "C",
        "artifacts": {
            "png": "build/candidates/QS001/render/candidate.png",
            "before_crop": "build/candidates/QS001/crops/original_panel_C.png",
            "after_crop": "build/candidates/QS001/crops/candidate_panel_C.png",
        },
        "stages": {
            "compile": {"status": "success"},
            "export": {"status": "success"},
            "crop": {"status": "success"},
            "evaluate": {"status": "rendered_needs_human_review"},
        },
        "visual_deltas": {"changed_pixel_ratio": 1.0},
    }
    (candidate_dir / "render_manifest.json").write_text(
        json.dumps(render_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths = quality_search.runtime_paths.resolve_runtime_paths(
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )
    run_dir = tmp_path / ".scratch" / "quality-search-runs" / "run-001"

    evidence = quality_search._quality_search_visual_evidence(
        "fig_demo",
        {
            "schema": "figure-agent.candidate-render-result.v1",
            "fixture": "fig_demo",
            "render_mode": "compile_export_crop_evaluate",
            "rendered": [
                {
                    "candidate_id": "QS001",
                    "render_manifest": "build/candidates/QS001/render_manifest.json",
                }
            ],
        },
        run_dir=run_dir,
        paths=paths,
    )

    assert evidence["state"] == "complete"
    assert evidence["min_full_changed_pixel_ratio"] == 1.0
    assert evidence["full_comparisons"][0]["visual_deltas"]["changed_pixel_ratio"] == 1.0
    full_sheet = tmp_path / evidence["contact_sheets"][0]["path"]
    panel_sheet = tmp_path / evidence["panel_comparisons"][0]["contact_sheet"]
    assert full_sheet.is_file()
    assert panel_sheet.is_file()


def test_quality_search_memory_events_record_render_positive_neutral_outcomes(
    tmp_path: Path,
) -> None:
    candidate_set = {
        "schema": "figure-agent.candidate-set.v1",
        "fixture": "fig_demo",
        "candidates": [
            {
                "id": "QS001",
                "edit_family": "hierarchy_rebalance",
                "family": "hierarchy_rebalance",
                "target": {"panel": "C", "subregion": "panel"},
            }
        ],
    }
    visual_evidence = {
        "schema": "figure-agent.quality-search-visual-evidence.v0",
        "fixture": "fig_demo",
        "state": "complete",
        "full_comparisons": [
            {
                "candidate_id": "QS001",
                "visual_deltas": {"changed_pixel_ratio": 0.03},
            }
        ],
        "panel_comparisons": [
            {
                "candidate_id": "QS001",
                "contact_sheet": ".scratch/run/QS001_panel_C_contact_sheet.png",
                "visual_deltas": {"changed_pixel_ratio": 0.02},
            }
        ],
        "contact_sheets": [
            {
                "kind": "candidate_full_contact_sheet",
                "path": ".scratch/run/candidate_full_contact_sheet.png",
            }
        ],
    }
    paths = quality_search.runtime_paths.resolve_runtime_paths(
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    payload = quality_search._quality_search_memory_events(
        name="fig_demo",
        run_id="run-001",
        candidate_set=candidate_set,
        candidate_rankings=[
            {
                "candidate_id": "QS001",
                "rank_score": 0.75,
                "render_status": "rendered_needs_human_review",
                "effective_apply_authority": "review_only",
            }
        ],
        visual_evidence=visual_evidence,
        paths=paths,
        run_dir=tmp_path / ".scratch" / "run-001",
    )

    assert payload["event_count"] == 1
    event = payload["events"][0]
    assert event["event_type"] == "candidate_ranked"
    assert event["outcome"]["state"] == "neutral"
    assert event["metrics"]["candidate_rank_score"] == 0.75
    assert event["metrics"]["full_changed_pixel_ratio"] == 0.03
    index = quality_memory_index.build_memory_index(payload["events"])
    assert index["families"]["hierarchy_rebalance"]["attempts"] == 1
    assert index["families"]["hierarchy_rebalance"]["neutral"] == 1


def test_quality_search_memory_events_attach_selected_acceptance_recommendation(
    tmp_path: Path,
) -> None:
    candidate_set = {
        "candidates": [
            {
                "id": "QS001",
                "edit_family": "panel_f_qtr_apparatus_lane",
                "target": {"panel": "F", "subregion": "qtr_apparatus"},
            }
        ]
    }
    visual_evidence = {
        "state": "complete",
        "full_comparisons": [
            {
                "candidate_id": "QS001",
                "visual_deltas": {"changed_pixel_ratio": 0.005},
            }
        ],
        "panel_comparisons": [
            {
                "candidate_id": "QS001",
                "contact_sheet": ".scratch/run/QS001_panel_F_contact_sheet.png",
                "visual_deltas": {"changed_pixel_ratio": 0.03},
            }
        ],
    }
    recommendation = {
        "status": "auto_accept_recommended",
        "candidate_id": "QS001",
        "recommendation": "accept",
        "authority": "recommendation_only",
        "is_acceptance_artifact": False,
        "source_mutation": "not_performed",
        "evidence": {
            "semantic_precheck_status": "pass",
            "review_packet_status": "ready",
            "apply_readiness_status": "ready_for_local_acceptance",
        },
    }
    paths = quality_search.runtime_paths.resolve_runtime_paths(
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    payload = quality_search._quality_search_memory_events(
        name="fig_demo",
        run_id="run-001",
        candidate_set=candidate_set,
        candidate_rankings=[
            {
                "candidate_id": "QS001",
                "rank_score": 0.81,
                "render_status": "rendered_needs_human_review",
                "effective_apply_authority": "review_only",
            }
        ],
        visual_evidence=visual_evidence,
        paths=paths,
        run_dir=tmp_path / ".scratch" / "run-001",
        selected_acceptance_recommendation=recommendation,
    )

    assert payload["event_count"] == 1
    event = payload["events"][0]
    assert event["event_type"] == "candidate_ranked"
    assert event["outcome"]["state"] == "neutral"
    assert event["outcome"]["reason"] == "auto_accept_recommended_not_applied"
    assert event["post_state"]["acceptance_recommendation_status"] == (
        "auto_accept_recommended"
    )
    assert event["post_state"]["acceptance_recommendation"] == "accept"
    assert event["post_state"]["acceptance_recommendation_authority"] == (
        "recommendation_only"
    )
    assert event["post_state"]["semantic_precheck_status"] == "pass"
    assert event["post_state"]["review_packet_status"] == "ready"
    assert event["post_state"]["apply_readiness_status"] == (
        "ready_for_local_acceptance"
    )
    assert event["metrics"]["acceptance_recommendation_status"] == (
        "auto_accept_recommended"
    )
    assert event["metrics"]["semantic_precheck_status"] == "pass"
    assert event["metrics"]["apply_readiness_status"] == "ready_for_local_acceptance"
    assert (
        ".scratch/run-001/selected_acceptance_recommendation_000.json"
        in event["outcome"]["evidence_paths"]
    )


def test_quality_search_prefers_later_visible_panel_style_token(
    tmp_path: Path, monkeypatch
) -> None:
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
    tex_source = "\n".join(
        [
            "% Panel C -- Localized traps",
            "\\draw[cAmber!75!black, line width=0.60pt] (0,0) -- (1,0);",
            "% =============== Column E -- ISPD-paired =================",
            "\\draw[cAmber!70!black, line width=0.25pt] (0,0) -- (1,0);",
            "% =============== Column F -- Mechanical =================",
            "\\draw[cGray!60!black, line width=0.25pt] (0,0) rectangle (1,1);",
            "% v5f Panel F art-direction redraw overlay.",
            "\\draw[cGray!64!black, line width=0.34pt] (0,0) rectangle (1,1);",
        ]
    )
    _write_minimal_fixture(tmp_path, name="fig_demo", tex_source=f"{tex_source}\n")

    payload = quality_search.build_quality_search_execution(
        "fig_demo",
        goal="visible overlay token selection",
        max_iterations=1,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    apparatus = [
        item
        for item in payload["candidate_set"]["candidates"]
        if item["family"] == "apparatus_strengthen"
    ][0]
    operation = apparatus["operations"][0]
    assert apparatus["operation_scale"] == "local_style_token"
    assert apparatus["template_id"] == "line_width_minimum_v1"
    assert operation["line_start"] == 8
    assert operation["line_end"] == 8
    assert operation["operation_scale"] == "local_style_token"
    assert "line width=0.34pt" in operation["original"]
    assert "line width=0.8pt" in operation["replacement"]


def test_fig_agent_quality_search_execute_cli_writes_only_scratch(tmp_path: Path) -> None:
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
            "execute dry witness loop",
            "--execute",
            "--max-iterations",
            "2",
            "--json",
        ],
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.quality-search-execute.v0"
    assert payload["status"] == "dry_run_complete"
    assert payload["safety"]["source_mutation"] == "forbidden_in_dry_executor"
    assert payload["writes"]
    after = _tree(workspace)
    changed = sorted(set(after) - set(before))
    assert changed
    assert all(
        path == ".scratch"
        or path == ".scratch/quality-search-runs"
        or path.startswith(".scratch/quality-search-runs/")
        for path in changed
    )
