from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig1_updated_agent_redraw_v1"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

import authoring_context_pack  # noqa: E402
import authoring_execution_packet  # noqa: E402
from semantic_legibility_contract import (  # noqa: E402
    validate_semantic_legibility_contract,
)


def _yaml(relative: str) -> dict:
    return yaml.safe_load((FIXTURE / relative).read_text(encoding="utf-8"))


def _historical_bytes(commit: str, source_path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{source_path}"],
        cwd=PLUGIN_ROOT,
        check=True,
        capture_output=True,
    ).stdout


def test_redraw_pins_unchanged_visual_and_physics_authorities() -> None:
    authority = _yaml("authority.yaml")
    assert authority["schema"] == "figure-agent.reference-authority.v1"
    assert authority["candidate_kind"] == "additive_full_figure_redraw"
    assert authority["historical_inputs_unchanged"] is True
    assert authority["publication_acceptance"] == "not_claimed"

    roles = {item["role"] for item in authority["sources"]}
    assert roles == {
        "visual_and_narrative_baseline",
        "narrative_and_aesthetic_intent",
        "physics_correction_authority",
    }
    for source in authority["sources"]:
        tree = subprocess.run(
            ["git", "rev-parse", f"{source['source_commit']}^{{tree}}"],
            cwd=PLUGIN_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert tree == source["source_tree"]
        historical = _historical_bytes(source["source_commit"], source["source_path"])
        assert hashlib.sha256(historical).hexdigest() == source["sha256"]


def test_redraw_is_independent_and_keeps_floating_panel_f_topology() -> None:
    source = (FIXTURE / "fig1_updated_agent_redraw_v1.tex").read_text(encoding="utf-8")
    assert "fig1_overview_v5f_art_direction_001_vault" not in source
    assert set(
        line.strip() for line in source.splitlines() if line.strip().startswith(r"\input{")
    ) == {
        r"\input{snippets/polymer_chain.snippet.tex}",
        r"\input{snippets/panel-f-floating-cantilever.tex}",
    }
    assert "\\include{" not in source
    assert "floating cantilever" in source
    assert "grounded voltage-source return" in source
    assert "sample and cantilever remain floating" in source
    assert r"\PolymerChain" in source
    assert r"\PanelFFloatingCantilever" in source

    result = validate_semantic_legibility_contract(_yaml("semantic_contract.yaml"))
    assert result["summary"]["object_role_count"] == 9
    assert result["summary"]["visible_connector_count"] == 4
    assert result["summary"]["floating_object_count"] == 1
    assert result["summary"]["visual_review_required"] is True
    assert result["publication_acceptance"] == "not_claimed"


def test_redraw_context_binds_the_curated_assets_used_by_source() -> None:
    payload = authoring_context_pack.build_context_pack(
        "fig1_updated_agent_redraw_v1",
        plugin_root=PLUGIN_ROOT,
        workspace_root=PLUGIN_ROOT,
    )
    selected = payload["visual_assets"]["selected"]
    assert [item["id"] for item in selected] == ["panel_f_floating_cantilever"]
    assert all(item["sha256"].startswith("sha256:") for item in selected)
    assert selected[0]["contract"]["sha256"].startswith("sha256:")
    assert selected[0]["transfer_receipt"]["sha256"].startswith("sha256:")


def test_bound_authoring_prompt_carries_project_cantilever_orientation_rule() -> None:
    context = authoring_context_pack.build_context_pack(
        "fig1_updated_agent_redraw_v1",
        plugin_root=PLUGIN_ROOT,
        workspace_root=PLUGIN_ROOT,
    )

    prompt = authoring_execution_packet.render_authoring_prompt(
        name="fig1_updated_agent_redraw_v1",
        repository_output_path=(
            "examples/fig1_updated_agent_redraw_v1/review/failure-first/"
            "comparable-v99/verified_generated.tex"
        ),
        allowed_repository_read_paths=("AGENTS.md",),
        context_pack=context,
        model_id="test-model",
    )

    assert "polymer_paper_project.cantilever-vertical-clip-top" in prompt
    assert "Draw the polymer cantilever vertical" in prompt
    assert "Horizontal cantilever orientation is wrong" in prompt
    assert "polymer_paper_project.panel-header-and-label-clearance" in prompt
    assert "Reserve a clear header band inside every panel" in prompt
    assert "Do not solve clearance by forcing an equal-cell grid" in prompt


def test_r5_v2_predeclaration_frees_composition_but_binds_vertical_cantilever() -> None:
    run_root = (
        PLUGIN_ROOT
        / "examples"
        / "fig1_updated_agent_redraw_v1"
        / "review"
        / "r5-prospective-v2"
    )
    task = (run_root / "task.md").read_text(encoding="utf-8")
    contract = yaml.safe_load(
        (run_root / "comparison_contract.yaml").read_text(encoding="utf-8")
    )
    normalized_task = " ".join(task.split())

    assert "two rows of three" not in task
    assert "Do not assume an equal-cell grid" in normalized_task
    assert (
        "placement, grouping, reading path, and overall composition are author-selected"
        in normalized_task
    )
    assert "floating polymer cantilever vertically from its top" in normalized_task
    assert "A horizontal cantilever is scientifically wrong" in normalized_task
    assert contract["composition_policy"] == {
        "semantic_roles_required": 6,
        "equal_grid_forbidden_as_a_requirement": True,
        "layout_author_selected": True,
        "visual_hero": "trap_landscape",
    }
    assert contract["conditions"]["B"]["handwritten_packet_summary_forbidden"] is True
    assert contract["conditions"]["B"]["required_rule_id"] == (
        "polymer_paper_project.cantilever-vertical-clip-top"
    )
    assert contract["conditions"]["B"]["required_visual_asset_id"] == (
        "panel_f_floating_cantilever"
    )


def test_r5_v3_predeclaration_reuses_control_and_binds_system_deltas() -> None:
    run_root = (
        PLUGIN_ROOT
        / "examples"
        / "fig1_updated_agent_redraw_v1"
        / "review"
        / "r5-prospective-v3"
    )
    contract = yaml.safe_load(
        (run_root / "comparison_contract.yaml").read_text(encoding="utf-8")
    )

    assert contract["control"]["sha256"] == (
        "0ac43684c00067070fbf9e86aaf6537e48509945006d21af47b5f3fd2d071476"
    )
    assert contract["treatment"]["layout_author_selected"] is True
    assert contract["treatment"]["equal_grid_forbidden_as_a_requirement"] is True
    assert set(contract["treatment"]["required_system_deltas"]) == {
        "exact_compilable_visual_asset_import",
        "malformed_numeric_node_anchor_blocker",
        "global_panel_header_and_label_clearance_rule",
    }
