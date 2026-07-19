from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig1_updated_agent_redraw_v1"
REPAIRED_SOURCE = (
    FIXTURE
    / "review"
    / "failure-first"
    / "comparable-v3-repair-c5"
    / "repaired.tex"
)
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
    for panel_id in "ABCDEF":
        assert f"Add exactly one canonical marker [% Panel {panel_id}]" in prompt


def test_repaired_ispd_manual_transfer_survives_print_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    label = source.index("{manual transfer}")
    declaration = source.rfind(r"\node", 0, label)
    transfer_node = source[declaration : label + len("{manual transfer}")]

    assert "small label" in transfer_node
    assert r"\fontsize{3.2}" not in transfer_node


def test_repaired_panel_f_keeps_annotation_lanes_clear() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")

    assert r"{mechanical\\clamp}" in source
    assert "{mechanical clamp}" not in source
    assert r"{trapped charge $q_{\mathrm{tr}}$}" in source
    assert r"(1.09,0.42)--(1.02,0.82)" not in source


def test_repaired_panel_e_caliper_label_interrupts_its_path() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    label = source.index(r"{$\tau_d$}")
    declaration = source.rfind(r"\node", 0, label)
    caliper_label = source[declaration : label + len(r"{$\tau_d$}")]

    assert "fill=white" in caliper_label
    assert "inner xsep" in caliper_label


def test_repaired_panel_e_surface_charge_has_no_undeclared_gradient() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_e = source.split("% Panel E", 1)[1].split("% Panel F", 1)[0]

    assert r"\foreach \x in {1.38,1.56,1.74,2.41,2.59,2.77}" in panel_e
    assert r"\tone" not in panel_e
    assert r"\rad" not in panel_e


def test_repaired_panel_letters_follow_nature_communications_case() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")

    for lower, upper in zip("abcdef", "ABCDEF", strict=True):
        assert f"{{{lower}}};" in source
        assert f"{{{upper}}};" not in source


def test_repaired_lower_row_uses_one_aligned_header_band() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")

    for panel_id, title in {
        "D": "Transient current",
        "E": "ISPD trap distribution",
        "F": "Floating Coulomb response",
    }.items():
        panel = source.split(f"% Panel {panel_id}", 1)[1]
        assert f"at (0.28,4.42) {{{panel_id.lower()}}};" in panel
        assert f"at (0.82,4.42) {{{title}}};" in panel


def test_repaired_top_row_summary_captions_share_one_text_level() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_a = source.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_b = source.split("% Panel B", 1)[1].split("% Panel C", 1)[0]

    assert r"\node[body label, align=center]" in panel_a
    assert r"\node[body label, align=center]" in panel_b
    assert "DIB units linked by polysulfides of increasing sulfur rank" in panel_b


def test_repaired_s8_atom_labels_survive_reduction() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_a = source.split("% Panel A", 1)[1].split("% Panel B", 1)[0]

    assert r"minimum size=1.60mm" in panel_a
    assert r"\fontsize{3.8}{4.6}\selectfont" in panel_a
    assert r"\fontsize{3.1}{3.8}\selectfont" not in panel_a


def test_repaired_panel_a_strokes_survive_nature_double_column_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    separators = source.split("% Panel A", 1)[0].split(
        "% Open publication canvas", 1
    )[1]
    panel_a = source.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    widths = [
        float(value)
        for value in re.findall(
            r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", separators + panel_a
        )
    ]

    # The source is about 150 mm wide and is intended for a 180 mm two-column
    # figure. 0.84 pt at source scale therefore renders at approximately 1 pt.
    assert widths
    assert min(widths) >= 0.84


def test_repaired_panel_b_strokes_survive_nature_double_column_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_b = source.split("% Panel B", 1)[1].split("% Panel C", 1)[0]
    widths = [
        float(value)
        for value in re.findall(
            r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", panel_b
        )
    ]

    assert widths
    assert min(widths) >= 0.84


def test_repaired_panel_c_strokes_survive_nature_double_column_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_c = source.split("% Panel C", 1)[1].split("% Panel D", 1)[0]
    widths = [
        float(value)
        for value in re.findall(
            r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", panel_c
        )
    ]

    assert widths
    assert min(widths) >= 0.84
    assert "circle (0.040);\n    \\draw" not in panel_c
    assert "cBlue!24, dash pattern" in panel_c
    assert "cRed!24, dash pattern" in panel_c
    assert "cBlue!34, opacity=0.68" in panel_c
    assert "cRed!34, opacity=0.68" in panel_c


def test_repaired_shared_semantic_lines_survive_nature_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")

    assert "axis line/.style=" in source
    assert "leader/.style=" in source
    for style_name in ("axis line", "leader"):
        declaration = source.split(f"{style_name}/.style=", 1)[1].splitlines()[0]
        width = re.search(
            r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", declaration
        )
        assert width is not None
        assert float(width.group(1)) >= 0.84


def test_repaired_panel_d_strokes_survive_nature_double_column_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_d = source.split("% Panel D", 1)[1].split("% Panel E", 1)[0]
    widths = [
        float(value)
        for value in re.findall(
            r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", panel_d
        )
    ]

    assert widths
    assert min(widths) >= 0.84
    assert "PI control: low $n$" in panel_d
    assert "S-rich: high $n$" in panel_d
    assert "Debye" not in panel_d
    assert r"\shade" not in panel_d
    assert "opacity=" not in panel_d


def test_repaired_panel_e_strokes_survive_nature_double_column_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_e = source.split("% Panel E", 1)[1].split("% Panel F", 1)[0]
    widths = [
        float(value)
        for value in re.findall(
            r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", panel_e
        )
    ]

    assert widths
    assert min(widths) >= 0.84
    assert "ESVM head" in panel_e
    assert "manual transfer" in panel_e
    assert "{derive};" in panel_e
    assert "anchor=north, text=cGray!78!black] at (3.80,1.18)" in panel_e
    assert "Kelvin" not in panel_e
    assert r"\shade" not in panel_e
    assert "opacity=" not in panel_e


def test_repaired_panel_f_and_full_figure_have_no_source_hairlines() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_f = source.split("% Panel F", 1)[1]
    widths = [
        float(value)
        for value in re.findall(
            r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", source
        )
    ]

    assert widths
    assert min(widths) >= 0.84
    assert r"{mechanical\\clamp}" in panel_f
    assert r"{floating polymer\\cantilever}" in panel_f
    assert r"{trapped charge $q_{\mathrm{tr}}$}" in panel_f
    assert r"\shade" not in panel_f


def test_fig1_visual_clash_registry_has_no_stale_hero_suppression() -> None:
    registry = _yaml("../../_known_false_positives.yaml")
    fig1_patterns = [
        pattern
        for pattern in registry["patterns"]
        if pattern.get("fixture") == "fig1_updated_agent_redraw_v1"
    ]

    assert all(pattern.get("glyph") != "HERO" for pattern in fig1_patterns)


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


def test_r5_v4_predeclaration_opens_repair_for_machine_invalid_b() -> None:
    run_root = (
        PLUGIN_ROOT
        / "examples"
        / "fig1_updated_agent_redraw_v1"
        / "review"
        / "r5-prospective-v4"
    )
    contract = yaml.safe_load(
        (run_root / "comparison_contract.yaml").read_text(encoding="utf-8")
    )

    assert contract["control"]["sha256"] == (
        "0ac43684c00067070fbf9e86aaf6537e48509945006d21af47b5f3fd2d071476"
    )
    assert contract["task_path"] == "../r5-prospective-v3/task.md"
    assert contract["budget_contract_path"] == "../r5-prospective-v3/budget_contract.yaml"
    assert contract["treatment"]["canonical_output"] == (
        "../failure-first/comparable-v3/verified_generated.tex"
    )
    assert set(contract["treatment"]["required_system_deltas"]) == {
        "canonical_panel_attribution_markers",
        "schematic_undeclared_geometry_profile",
        "exact_unique_literal_source_attribution",
    }
    assert contract["admission"]["strict_pass_required_before_repair"] is False
    assert contract["admission"]["reproducible_render_required"] is True
    assert contract["admission"]["named_human_adjudication_required"] is True
    assert contract["publication_acceptance"] == "not_claimed"

    status = json.loads((run_root / "run-status.json").read_text(encoding="utf-8"))
    metrics = json.loads(
        (
            PLUGIN_ROOT
            / "examples"
            / "fig1_updated_agent_redraw_v1"
            / "review"
            / "failure-first"
            / "comparable-v3"
            / "attribution-metrics.json"
        ).read_text(encoding="utf-8")
    )
    assert status["treatment"]["normal_compile_state"] == "passed"
    assert status["treatment"]["strict_compile_state"] == "failed"
    assert status["treatment"]["repair_admission"] == (
        "open_after_named_human_adjudication_of_exact_finding"
    )
    assert metrics["attribution_states"] == {
        "exact": 16,
        "ambiguous": 18,
        "unbound": 1,
    }
    assert metrics["declared_check_coverage"] == {
        "label_path_proximity": 0,
        "text_boundary_clash": 0,
        "vector_clearance": 0,
    }
    assert metrics["repair_performed"] is False
    assert metrics["human_review"] == "pending"
    assert metrics["publication_acceptance"] == "not_claimed"


def test_redraw_uses_schematic_undeclared_geometry_profile() -> None:
    spec = yaml.safe_load(
        (
            PLUGIN_ROOT
            / "examples"
            / "fig1_updated_agent_redraw_v1"
            / "spec.yaml"
        ).read_text(encoding="utf-8")
    )

    assert spec["undeclared_geometry_profile"] == "schematic"
