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
    assert payload["search_policy"]["schema"] == "figure-agent.quality-search-bandit-policy.v0"
    assert payload["search_policy"]["kind"] == "contextual_bandit_beam_v0"
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
    assert len(payload["candidate_specs"]) == 4
    assert {item["family"] for item in payload["candidate_specs"]} >= {
        "hierarchy_rebalance",
        "apparatus_strengthen",
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
    assert "(13.30, 3.78) -- (13.30, 2.82);" in operation["replacement"]
    assert "circle ({1.90*\\rr})" in operation["replacement"]
    assert "ball color=cRed!82!black" in operation["replacement"]
    assert "at (9.56, 2.84) {$q_{\\mathrm{tr}}$};" in operation["replacement"]
    assert "at (9.56, 3.04) {trapped charge};" in operation["replacement"]
    assert "Stealth[length=8.6pt,width=6.2pt]" in operation["replacement"]
    assert "\\draw[<->, cGray!62!black, line width=0.50pt]" in operation["replacement"]


def test_quality_search_policy_uses_memory_prior_and_exploration_bonus() -> None:
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
    assert hierarchy["policy"]["exploration_bonus"] == 0.0
    assert apparatus["policy"]["memory_prior"] == 0.0
    assert apparatus["policy"]["exploration_bonus"] == 0.06
    assert apparatus["policy_score"] > hierarchy["policy_score"]
    assert decision["selected_candidate_id"] == "QS002"
    assert decision["selected_family"] == "apparatus_strengthen"
    assert decision["policy"]["schema"] == "figure-agent.quality-search-bandit-policy.v0"


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
        timeout=10,
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
