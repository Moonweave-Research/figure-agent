from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig1_updated_agent_redraw_v1"
CURRENT_HANDOFF = FIXTURE / "FIG1_CURRENT_CANDIDATE_HANDOFF.md"
REVIEW_LINEAGE = FIXTURE / "review" / "README.md"
# The comparable-v3-repair-c5 child was promoted byte-for-byte to the fixture
# root, so the repaired-source contracts below must now guard the canonical
# source. The preserved child is promotion history, not the working source.
REPAIRED_SOURCE = FIXTURE / "fig1_updated_agent_redraw_v1.tex"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

import authoring_context_pack  # noqa: E402
import authoring_execution_packet  # noqa: E402
import check_physics_grounding  # noqa: E402
from semantic_legibility_contract import (  # noqa: E402
    validate_semantic_legibility_contract,
)


def _yaml(relative: str) -> dict:
    return yaml.safe_load((FIXTURE / relative).read_text(encoding="utf-8"))


def _tikz_pair(value: str) -> tuple[float, float]:
    match = re.fullmatch(r"\(([0-9.]+),([0-9.]+)\)", value)
    assert match, value
    return float(match.group(1)), float(match.group(2))


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


def test_redraw_handoff_names_the_promoted_root_without_claiming_acceptance() -> None:
    assert CURRENT_HANDOFF.is_file()
    assert not (FIXTURE / "FIG1_CANONICAL_HANDOFF.md").exists()
    handoff = CURRENT_HANDOFF.read_text(encoding="utf-8")
    assert "current-candidate handoff" in handoff
    assert "`fig1_updated_agent_redraw_v1.tex` at the fixture root" in handoff
    assert "promoted_to_canonical_root" in handoff
    # Promotion moves the source only; no acceptance state may be implied.
    assert "publication acceptance are pending" in handoff
    assert "does not make this a paper artifact" in handoff

    pointer = json.loads(
        (FIXTURE / "review" / "current-candidate.json").read_text(encoding="utf-8")
    )
    assert pointer["candidate_root"] == "."
    assert pointer["source_path"] == "fig1_updated_agent_redraw_v1.tex"
    assert pointer["promotion_state"] == "promoted_to_canonical_root"
    assert pointer["human_gate"] == "pending"
    assert (
        pointer["source_sha256"]
        == "sha256:" + hashlib.sha256(REPAIRED_SOURCE.read_bytes()).hexdigest()
    )


def test_review_lineage_distinguishes_promoted_root_from_preserved_history() -> None:
    assert REVIEW_LINEAGE.is_file()
    lineage = REVIEW_LINEAGE.read_text(encoding="utf-8")
    assert "review/current-candidate.json" in lineage
    assert "comparable-v3-repair-c5" in lineage
    assert "promotion origin" in lineage
    assert "not_claimed" in lineage
    for historical_path in (
        "comparable-v1",
        "comparable-v3-repair-c1",
        "r5-prospective-v1",
        "closed-loop-archive/",
    ):
        assert historical_path in lineage


def test_redraw_is_independent_and_keeps_floating_panel_f_topology() -> None:
    source = (FIXTURE / "fig1_updated_agent_redraw_v1.tex").read_text(encoding="utf-8")
    assert "fig1_overview_v5f_art_direction_001_vault" not in source
    assert set(
        line.strip() for line in source.splitlines() if line.strip().startswith(r"\input{")
    ) == {
        r"\input{snippets/panel-f-floating-cantilever.tex}",
    }
    assert "\\include{" not in source
    assert "floating polymer\\\\cantilever" in source
    assert "grounded voltage-source return" in source
    assert "sample and cantilever remain electrically floating" in source

    result = validate_semantic_legibility_contract(_yaml("semantic_contract.yaml"))
    assert result["summary"]["object_role_count"] == 31
    assert result["summary"]["visible_connector_count"] == 21
    assert result["summary"]["label_ownership_count"] == 8
    assert result["summary"]["floating_object_count"] == 1


def test_redraw_semantic_contract_binds_c_d_e_relations() -> None:
    contract = _yaml("semantic_contract.yaml")
    result = validate_semantic_legibility_contract(contract)

    protected = set(result["protected_relations"])
    assert "real_space_trap_populations_correspond_to_energy_diagram_states" in protected
    assert "high_n_power_law_decays_faster_than_low_n_power_law" in protected
    assert (
        "corona_charged_sample_is_manually_transferred_to_noncontact_ispd_measurement"
        in protected
    )
    assert "surface_potential_decay_is_transformed_into_derived_trap_distribution" in protected
    assert "tau_d_remains_energy_domain_interval_between_shallow_and_deep_peaks" in protected

    connectors = {
        item["connector_id"]: item
        for item in result["semantic_legibility"]["visible_connectors"]
    }
    assert (
        connectors["panel_c.shallow_population_corresponds_to_energy_state"]["render_style"]
        == "population_correspondence"
    )
    assert (
        connectors["panel_d.constant_voltage_owns_transient"]["declared_role"]
        == "operating_condition"
    )
    assert (
        connectors["panel_e.decay_feeds_raw_to_derived_transform"]["render_style"]
        == "transformation_arrow"
    )
    assert (
        connectors["panel_e.transform_outputs_trap_distribution"]["to_object"]
        == "panel_e.derived_trap_distribution"
    )
    assert result["summary"]["visual_review_required"] is True
    assert result["publication_acceptance"] == "not_claimed"


def test_redraw_semantic_contract_binds_chemistry_and_composition_evidence_boundary() -> None:
    contract = _yaml("semantic_contract.yaml")
    result = validate_semantic_legibility_contract(contract)

    required = set(contract["required_objects"])
    assert {
        "panel_a.elemental_s8",
        "panel_a.dib_comonomer",
        "panel_a.inverse_vulcanization",
        "panel_a.representative_bis_thiocumyl_motif",
        "panel_a.variable_sulfur_rank",
        "panel_b.s60_sample",
        "panel_b.s75_sample",
        "panel_b.s85_sample",
        "panel_b.qualitative_sulfur_rank_progression",
    } <= required

    protected = set(result["protected_relations"])
    assert {
        "inverse_vulcanization_transforms_s8_and_dib_into_representative_motif",
        "representative_motif_contains_variable_not_fixed_sulfur_rank",
        "s60_s75_s85_are_sulfur_weight_percent_sample_identities",
        "drawn_sulfur_glyph_count_is_qualitative_not_measured_chain_length",
    } <= protected
    assert {
        "panel_a.unique_constitutional_repeat",
        "panel_a.covalent_crosslink_network",
        "panel_b.sample_number_as_sulfur_atom_count",
        "panel_b.exact_composition_derived_chain_length",
    } <= set(contract["forbidden_implications"])

    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_b = source.split("% Panel B", 1)[1].split("% Panel C", 1)[0]
    assert "Representative DIB-linked motifs (schematic sulfur rank)" in panel_b

    spec = _yaml("spec.yaml")
    panels = {panel["id"]: panel for panel in spec["panels"]}
    assert panels["A"]["semantic_claims"]
    assert panels["A"]["locked_invariants"]
    assert panels["B"]["semantic_claims"]
    assert panels["B"]["locked_invariants"]


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
    assert "polymer_paper_project.poly-s-dib-bis-thiocumyl-motif" in prompt
    assert "Ar-C(CH3)2-Sx" in prompt
    assert "Locked invariant [E:tau-d-energy-domain]" in prompt
    assert "pair001.tau-d-energy-domain-exception" in prompt
    assert "Do not move it onto the V_s(t) time axis" in prompt
    for panel_id in "ABCDEF":
        assert f"Add exactly one canonical marker [% Panel {panel_id}]" in prompt


def test_repaired_panel_a_uses_connected_bis_thiocumyl_chemistry() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_a = source.split("% Panel A", 1)[1].split("% Panel B", 1)[0]

    assert panel_a.count("bis-thiocumyl junction: Ar-C(CH3)2-S_x") == 2
    assert "representative DIB-linked repeat unit" in panel_a
    assert "{representative bis(thiocumyl) motif}" not in panel_a
    assert "linear repeat unit" not in panel_a
    assert "circle, draw=cAmber" not in panel_a
    assert "chemically continuous bond to left polysulfide" in panel_a
    assert "chemically continuous bond to right polysulfide" in panel_a


def test_repaired_panel_a_uses_skeletal_junctions_and_declared_continuations() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_a = source.split("% Panel A", 1)[1].split("% Panel B", 1)[0]

    assert "tetrahedral projection; avoid orthogonal cross" in panel_a.lower()
    assert panel_a.count("polymer continuation bond") == 2
    assert "representative DIB-linked repeat unit" in panel_a
    assert "$x,y$: statistical sulfur rank" in panel_a
    assert "bis-thiocumyl connectivity" not in panel_a
    assert "variable sulfur rank and minor microstructures" not in panel_a


def test_repaired_panel_a_survives_enlarged_chemical_inspection() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_a = source.split("% Panel A", 1)[1].split("% Panel B", 1)[0]

    assert "enlarged-vector audit: alkene lines remain individually traceable" in panel_a
    assert panel_a.count("no mid-bond colour seam") == 2
    assert "shorten >=2.0pt, shorten <=2.0pt" in panel_a
    assert "(105:0.28)" in panel_a
    assert "(-45:0.28)" in panel_a
    assert "(75:0.28)" in panel_a
    assert "(-135:0.28)" in panel_a


def test_repaired_panel_b_preserves_panel_a_chemical_topology() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_b = source.split("% Panel B", 1)[1].split("% Panel C", 1)[0]

    assert "B aromatic DIB rings retain Kekule bonds" in panel_b
    assert "B bis-thiocumyl junctions retained at both chain ends" in panel_b
    assert "direct aryl--sulfur attachment is forbidden" in panel_b
    assert "circle, draw=cAmber" not in panel_b
    assert "Representative DIB-linked motifs (schematic sulfur rank)" in panel_b


def test_repaired_panel_b_declares_qualitative_composition_encoding() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_b = source.split("% Panel B", 1)[1].split("% Panel C", 1)[0]

    assert "S60/S75/S85 are sulfur wt-percent sample names" in panel_b
    assert "drawn S-glyph count is a qualitative artistic correlate only" in panel_b
    assert "not a measured molecular sulfur rank" in panel_b
    assert r"{sulfur content (wt\%)}" in panel_b


def test_repaired_ispd_manual_transfer_survives_print_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    label = source.index(r"{manual sample\\[-0.5pt]transfer}")
    declaration = source.rfind(r"\node", 0, label)
    transfer_node = source[declaration : label + len(r"{manual sample\\[-0.5pt]transfer}")]

    assert "small label" in transfer_node
    assert r"\fontsize{3.2}" not in transfer_node
    assert r"\fontsize{5.0}{5.8}" in transfer_node
    assert "text=cGray!88!black" in transfer_node
    panel_e = source.split("% Panel E", 1)[1].split("% Panel F", 1)[0]
    assert r"(1.78,2.77)--(2.24,2.77)" in panel_e
    assert r"(1.87,2.84)--(2.21,2.84)" not in panel_e


def test_repaired_panel_f_keeps_annotation_lanes_clear() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_f = source.split("% Panel F", 1)[1]

    assert r"{mechanical\\clamp}" in source
    assert "{mechanical clamp}" not in source
    assert r"{trapped charge $q_{\mathrm{tr}}$}" in source
    assert r"(1.09,0.42)--(1.02,0.82)" not in source
    assert "text=cBlue" not in panel_f
    assert "text=cRed!82!black" in panel_f
    assert "text=cGray!88!black" in panel_f
    assert "text=cGray!92!black" in panel_f
    assert r"{$V_{\mathrm{app}}$}" in panel_f
    assert "Trapped-charge family follows the active face of the polymer" in panel_f
    assert panel_f.count("fill[cRed!80]") == 4
    assert "bias circuit neutral gray" in panel_f
    assert "cBlue!66!black" not in panel_f
    assert "cBlue!58!black" not in panel_f
    assert "cGray!54!black, line width=0.66pt" in panel_f
    assert "cAmber!7, rounded corners=0.45mm" in panel_f
    assert r"(1.325,1.43)--(0.34,1.43)" in panel_f
    assert r"{\bfseries Coulomb\\[-0.6pt]\mdseries repulsion}" in panel_f
    assert "Stealth[length=4.8pt,width=3.5pt]" in panel_f
    assert r"(1.38,1.43)--(0.43,1.43)" not in panel_f


def test_repaired_panel_e_caliper_label_interrupts_its_path() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    label = source.index(r"{$\tau_d$}")
    declaration = source.rfind(r"\node", 0, label)
    caliper_label = source[declaration : label + len(r"{$\tau_d$}")]

    assert "fill=white" in caliper_label
    assert "inner xsep" in caliper_label

    panel_e = source.split("% Panel E", 1)[1].split("% Panel F", 1)[0]
    assert panel_e.count("circle (0.040)") == 1
    assert "circle (0.050)" not in panel_e
    assert "both peak projections" in panel_e
    assert "(1.56,0.78)--(1.56,1.31)" in panel_e
    assert "(3.02,1.15)--(3.02,1.31)" in panel_e
    assert "(1.56,1.35)--(3.02,1.35)" in panel_e


def test_repaired_panel_e_schematic_curves_do_not_imply_sampled_data() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_e = source.split("% Panel E", 1)[1].split("% Panel F", 1)[0]

    assert "No point markers are shown" in panel_e
    assert "sampled surface-potential coordinates" in panel_e
    assert "source-bound data" in panel_e
    assert "Representative derived points" not in panel_e
    assert "circle (0.055)" not in panel_e


def test_repaired_panel_e_surface_charge_has_no_undeclared_gradient() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_e = source.split("% Panel E", 1)[1].split("% Panel F", 1)[0]

    assert r"\foreach \x in {1.08,1.27,1.46,2.56,2.75,2.94}" in panel_e
    assert r"\tone" not in panel_e
    assert r"\rad" not in panel_e
    assert r"\foreach \dx in {-0.08,0,0.08}" not in panel_e
    assert "dash pattern=on 1.2pt off 1.1pt" in panel_e
    assert "(1.27,3.15)--(1.27,3.08)" in panel_e


def test_repaired_panel_e_does_not_invent_corona_polarity() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_e = source.split("% Panel E", 1)[1].split("% Panel F", 1)[0]

    assert r"{$+$}" not in panel_e
    assert r"{$-$}" not in panel_e
    assert "polarity-neutral surface-charge markers" in panel_e
    assert "electrical path neutral gray" in panel_e
    assert "cRed!72!black" not in panel_e
    assert "cRed!68!black" not in panel_e


def test_repaired_panel_e_uses_colour_for_measurement_marks_not_text() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_e = source.split("% Panel E", 1)[1].split("% Panel F", 1)[0]

    for colored_text in ("text=cBrown", "text=cTeal", "text=cBlue", "text=cRed"):
        assert colored_text not in panel_e
    assert panel_e.count("text=cGray!88!black") >= 4
    assert "cTeal!78!black, line width=0.66pt" in panel_e
    # g(E_t) is one population: one neutral outline, colour only in the zones.
    assert "cBlue!84!black, line width=0.82pt" not in panel_e
    assert "cRed!84!black, line width=0.82pt" not in panel_e
    assert panel_e.count("cGray!88!black, line width=0.82pt") == 1
    assert panel_e.count("exp(-((\\x-2.36)*(\\x-2.36))/0.52)") == 3


def test_repaired_panel_e_preserves_a_visible_noncontact_esvm_gap() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_e = source.split("% Panel E", 1)[1].split("% Panel F", 1)[0]

    assert "(2.68,3.22) rectangle (2.86,3.96)" in panel_e
    assert "(2.69,3.22) rectangle (2.85,3.27)" in panel_e
    assert "(2.68,3.12) rectangle (2.86,3.86)" not in panel_e
    assert "{ESVM head}" in panel_e
    assert "Kelvin" not in panel_e


def test_repaired_panel_e_uses_keyence_family_level_head_topology() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_e = source.split("% Panel E", 1)[1].split("% Panel F", 1)[0]

    assert "SK-family elongated bar head" in panel_e
    assert "(2.68,3.22) rectangle (2.86,3.96)" in panel_e
    assert "(2.69,3.22) rectangle (2.85,3.27)" in panel_e
    assert "(2.77,3.96)" in panel_e
    assert "(3.38,3.68)" in panel_e
    assert "oscillation" not in panel_e.lower()


def test_repaired_panel_letters_follow_nature_communications_case() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")

    for lower, upper in zip("abcdef", "ABCDEF", strict=True):
        assert f"{{{lower}}};" in source
        assert f"{{{upper}}};" not in source


def test_repaired_declares_height_limited_final_print_size_contract() -> None:
    spec = _yaml("spec.yaml")
    contract = spec["final_size_contract"]

    assert contract["basis"] == "height_limited_nature_family_main_figure"
    natural_width, natural_height = contract["natural_size_mm"]
    target_width = contract["target_width_mm"]
    max_height = contract["max_height_mm"]
    assert math.isclose(natural_width, 150.7, abs_tol=0.1)
    assert math.isclose(natural_height, 153.6, abs_tol=0.1)
    assert math.isclose(target_width, natural_width * max_height / natural_height, abs_tol=0.2)
    assert math.isclose(target_width, 166.8, abs_tol=0.2)
    assert contract["double_column_reference_mm"]["nature_communications"] == 180.0
    assert contract["double_column_reference_mm"]["nature_figure_guide"] == 183.0
    assert natural_height * 180.0 / natural_width > max_height
    assert natural_height * 183.0 / natural_width > max_height


def test_repaired_declares_text_boundary_coverage_for_all_six_panels() -> None:
    spec = _yaml("spec.yaml")
    check_ids = {item["id"] for item in spec["text_boundary_checks"]}
    for panel in "ABCDEF":
        assert any(check_id.startswith(f"panel-{panel.lower()}-") for check_id in check_ids)


def test_repaired_declares_compile_visible_physics_grounding() -> None:
    briefing = (FIXTURE / "briefing.md").read_text(encoding="utf-8")
    spec = _yaml("spec.yaml")

    assert check_physics_grounding.has_physics_invariants(briefing) is True
    assert check_physics_grounding.has_semantic_assertions(spec) is True
    assert check_physics_grounding.grounding_status(FIXTURE)["status"] == "grounded"
    assertion_ids = {item["id"] for item in spec["semantic_assertions"]}
    assert assertion_ids == {
        "panel-c-mobility-edge-left-of-thermal-escape",
        "panel-f-coulomb-result-left-of-maxwell-baseline",
        "panel-f-trapped-charge-left-of-driven-electrode",
    }


def test_repaired_font_hierarchy_fits_declared_final_print_size() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    contract = _yaml("spec.yaml")["final_size_contract"]
    scale = contract["target_width_mm"] / contract["natural_size_mm"][0]

    for style_name in ("panel letter", "panel title", "body label", "small label"):
        declaration = source.split(f"{style_name}/.style=", 1)[1].splitlines()[0]
        size = re.search(r"\\fontsize\{([0-9.]+)\}", declaration)
        assert size, style_name
        final_size_pt = float(size.group(1)) * scale
        assert 5.0 <= final_size_pt <= 7.0


def test_repaired_panel_descriptors_do_not_form_a_second_title_band() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    declaration = source.split("panel title/.style=", 1)[1].splitlines()[0]
    panel_c = source.split("% Panel C", 1)[1].split("% Panel D", 1)[0]

    assert r"\bfseries" not in declaration
    size = re.search(r"\\fontsize\{([0-9.]+)\}", declaration)
    assert size
    assert float(size.group(1)) <= 6.5
    assert "text=cGray!90!black" in declaration
    assert (
        r"\node[small label, text=cGray!78!black, anchor=west] at (0.90,4.62) {real space};"
        in panel_c
    )
    assert (
        r"\node[small label, text=cGray!78!black, anchor=west] at (7.72,4.84) {energy diagram};"
        in panel_c
    )
    assert r"\node[body label, anchor=west] at (0.90,4.80) {real space};" not in panel_c
    assert r"\node[body label, anchor=west] at (7.72,5.02) {energy diagram};" not in panel_c


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


def test_repaired_panel_separators_remain_subordinate_to_scientific_marks() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    separators = source.split("% Panel A", 1)[0]

    assert separators.count("cGray!10, line width=0.42pt") == 5
    assert "cGray!18, line width=0.84pt" not in separators


def test_repaired_top_row_summary_captions_share_one_text_level() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_a = source.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_b = source.split("% Panel B", 1)[1].split("% Panel C", 1)[0]

    assert r"\node[body label, align=center]" in panel_a
    assert r"\node[body label, align=center]" in panel_b
    assert "Representative DIB-linked motifs (schematic sulfur rank)" in panel_b


def test_repaired_s8_atom_labels_survive_reduction() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_a = source.split("% Panel A", 1)[1].split("% Panel B", 1)[0]

    assert r"\foreach \i in {1,...,8}" in panel_a
    assert r"\fontsize{4.6}{5.4}\selectfont" in panel_a
    assert "fill=white, inner sep=0.35pt" in panel_a
    assert "circle, draw=cAmber" not in panel_a
    assert r"\fontsize{3.1}{3.8}\selectfont" not in panel_a


def test_repaired_panel_a_strokes_survive_declared_final_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    separators = source.split("% Panel A", 1)[0].split("% Open publication canvas", 1)[1]
    panel_a = source.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    widths = [
        float(value)
        for value in re.findall(r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", separators + panel_a)
    ]

    # Overview structure now follows the thinner Fig. 2 baseline; separators
    # are intentionally lighter and are checked separately below.
    assert widths
    assert (
        min(
            float(value)
            for value in re.findall(r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", panel_a)
        )
        >= 0.66
    )


def test_repaired_panel_b_strokes_survive_declared_final_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_b = source.split("% Panel B", 1)[1].split("% Panel C", 1)[0]
    widths = [
        float(value) for value in re.findall(r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", panel_b)
    ]

    assert widths
    assert min(widths) >= 0.66


def test_repaired_panel_c_strokes_survive_declared_final_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_c = source.split("% Panel C", 1)[1].split("% Panel D", 1)[0]
    widths = [
        float(value) for value in re.findall(r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", panel_c)
    ]

    assert widths
    # Claim-bearing DOS, edge, and correspondence strokes keep the publication
    # floor; low-contrast host texture and tiny marker outlines are intentional
    # supporting marks and must not be judged by a raw minimum-width check.
    assert "cAmber!58!black, line width=0.74pt" in panel_c
    assert "line width=0.66pt" in panel_c
    assert "circle (0.040);\n    \\draw" not in panel_c
    assert "cBlue!32, dash pattern" in panel_c
    assert "cRed!32, dash pattern" in panel_c
    assert "cBlue!24, dash pattern" not in panel_c
    assert "cRed!24, dash pattern" not in panel_c
    # Trap markers must remain subordinate to the DOS curves and level lines;
    # oversized discs make a scientific schematic read like an infographic.
    assert "circle (0.10)" not in panel_c
    assert panel_c.count("circle (0.075)") == 8  # fill + outline for four cores
    assert panel_c.count("circle (0.070)") == 2
    assert "(1.55,1.63) circle (0.075)" in panel_c
    assert "(4.64,2.84) circle (0.075)" in panel_c
    assert "(2.72,3.64) circle (0.075)" in panel_c
    assert "(5.42,1.64) circle (0.075)" in panel_c
    # Population correspondence begins at the perimeter of a representative
    # localized site rather than cutting through or floating beside the dot.
    assert "(4.695,2.84)--(7.40,2.88)" in panel_c
    assert "(5.495,1.62)--(7.40,1.68)" in panel_c
    real_space = panel_c.split("% Energy-space view", 1)[0]
    host_texture = real_space.split("% Local contrast follows", 1)[0]
    assert "both trap classes are localized sites in one disordered film" in real_space
    assert r"\foreach \xx/\yy" not in real_space
    assert "specimen-spanning amorphous host" in real_space
    assert r"\fill[cBlue!30" not in real_space
    assert r"\fill[cRed!28" not in real_space
    assert r"\fill[cBlue!13]" not in real_space
    assert r"\fill[cRed!12]" not in real_space
    assert "Five low-contrast irregular traces" in real_space
    assert host_texture.count("plot[smooth] coordinates") == 5
    assert real_space.count("opacity=") >= 5
    assert "trap-free cross-field trace" in real_space
    assert "structural cues, not literal chain topology" in real_space
    assert real_space.count("line width=1.20pt") == 0
    assert "(1.06,4.02)" in real_space
    assert "(3.46,1.45)" in real_space
    assert "(6.02,3.92)" not in real_space
    assert "(6.02,2.38)" not in real_space
    assert "surface-wrinkle decoration" in real_space
    assert "cAmber!36!black" not in real_space
    assert "fill=cBlue!9" not in real_space
    assert "fill=cRed!8" not in real_space
    assert "cGray!46" not in real_space
    assert "cGray!48!black" not in real_space
    assert "cGray!64!black" not in real_space
    # Escape paths leave the upper edge of an occupied trap marker and end at
    # the mobility edge; detached arrows imply an unrelated transport path.
    assert "(9.62,3.11) .. controls" in panel_c
    assert "(9.88,1.95) .. controls" in panel_c
    # A material field is not a colored cartoon object: keep its broad area
    # neutral and nearly white rather than reusing the sulfur palette.
    assert "\\fill[cAmber!8" in panel_c
    assert "\\fill[cGray!3]" not in panel_c
    assert "\\draw[cAmber!58!black, line width=0.74pt, rounded corners" in panel_c
    # Colour encodes the trap populations in marks and curves, not in text;
    # neutral labels remain readable in grayscale and colour-blind viewing.
    assert "text=cBlue" not in panel_c
    assert "text=cRed" not in panel_c
    assert "rotate=90, text=cGray!92!black" in panel_c
    # Keep the DOS legible through its publication-weight outline instead of
    # locking a saturated area fill that makes the schematic read as artwork.
    # The population is ONE curve, so it carries one neutral outline and the
    # shallower/deeper zones are tint only.
    for color in ("Blue", "Red"):
        fill = re.search(rf"\\fill\[c{color}!(\d+), opacity=([0-9.]+)\]", panel_c)
        assert fill
        assert int(fill.group(1)) <= 20
        assert float(fill.group(2)) <= 0.60
        assert f"c{color}!84!black, line width=0.82pt" not in panel_c
    assert panel_c.count("cGray!88!black, line width=0.82pt") == 1
    assert panel_c.count("exp(-((\\x-2.20)*(\\x-2.20))/0.52)") == 3
    assert "rectangular population wash" in panel_c
    assert "(7.72,2.42) rectangle (11.80,3.34)" not in panel_c
    assert "(7.72,0.98) rectangle (11.80,2.38)" not in panel_c
    assert "{Localized trap landscape};" in panel_c
    assert "{Localized trap model};" not in panel_c
    assert "{Localized shallow and deep traps};" not in panel_c
    assert "One continuous distribution of localized states" in panel_c
    assert "no shallow-to-deep ratio is drawn or claimed" in panel_c


def test_repaired_shared_semantic_lines_survive_nature_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")

    assert "axis line/.style=" in source
    assert "leader/.style=" in source
    for style_name in ("axis line", "leader"):
        declaration = source.split(f"{style_name}/.style=", 1)[1].splitlines()[0]
        width = re.search(r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", declaration)
        assert width is not None
        assert float(width.group(1)) >= 0.66


def test_repaired_panel_d_strokes_survive_declared_final_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_d = source.split("% Panel D", 1)[1].split("% Panel E", 1)[0]
    widths = [
        float(value)
        for value in re.findall(
            r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", panel_d
        )
    ]

    assert widths
    assert "line width=0.90pt" in panel_d
    assert "line width=0.66pt" in panel_d
    assert "line width=0.25pt" in panel_d  # neutral shared-anchor outline
    assert "{low $n$}" in panel_d
    assert "{high $n$}" in panel_d
    assert "PI control" not in panel_d
    assert "S-rich" not in panel_d
    assert "circle (0.045)" in panel_d  # neutral shared initial-state anchor
    assert "circle (0.060)" not in panel_d
    for colored_text in ("text=cBrown", "text=cBlue", "text=cRed"):
        assert colored_text not in panel_d
    assert panel_d.count("text=cGray!92!black") == 2
    assert "(0.48,2.62) rectangle (1.47,3.44)" in panel_d
    assert "(0.55,2.70) rectangle (1.40,3.36)" not in panel_d
    for rotation, end_y in ((-13.5, 1.12), (-21.1, 0.66)):
        slope_angle = math.degrees(math.atan2(end_y - 1.88, 4.02 - 0.86))
        assert abs(rotation - slope_angle) <= 0.3
        assert f"rotate={rotation}" in panel_d
    assert "Debye" not in panel_d
    assert r"\shade" not in panel_d
    assert "opacity=" not in panel_d
    assert "measurement-like data points" in panel_d


def test_repaired_panel_d_uses_the_shared_three_bar_ground_symbol() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_d = source.split("% Panel D", 1)[1].split("% Panel E", 1)[0]

    assert "shared three-bar tapered ground grammar" in panel_d
    assert "(4.09,2.57)--(4.35,2.57)" in panel_d
    assert "(4.13,2.51)--(4.31,2.51)" in panel_d
    assert "(4.17,2.46)--(4.27,2.46)" in panel_d


def test_repaired_panel_d_high_n_line_is_geometrically_steeper() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_d = source.split("% Panel D", 1)[1].split("% Panel E", 1)[0]

    assert "(0.86,1.88)--(4.02,1.12)" in panel_d
    assert "(0.86,1.88)--(4.02,0.66)" in panel_d
    low_drop = 1.88 - 1.12
    high_drop = 1.88 - 0.66
    assert high_drop > low_drop
    assert "rotate=-13.5" in panel_d
    assert "rotate=-21.1" in panel_d


def test_repaired_panel_e_strokes_survive_declared_final_scale() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_e = source.split("% Panel E", 1)[1].split("% Panel F", 1)[0]
    widths = [
        float(value)
        for value in re.findall(
            r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", panel_e
        )
    ]

    assert widths
    assert "line width=0.82pt" in panel_e
    assert "line width=0.66pt" in panel_e
    assert "ESVM head" in panel_e
    assert r"manual sample\\[-0.5pt]transfer" in panel_e
    assert "anchor=north, align=center" in panel_e
    assert "{manual transfer}" not in panel_e
    assert "{derive};" in panel_e
    transform = re.search(
        r"Explicit raw-to-derived transformation\.\n"
        r"\s*\\draw\[[^\]]*Stealth[^\]]*\][^\n]*\n"
        r"\s*(\([0-9.]+,[0-9.]+\))--(\([0-9.]+,[0-9.]+\));\n"
        r"\s*\\node\[small label, anchor=west, text=cGray!78!black\] at "
        r"(\([0-9.]+,[0-9.]+\)) \{derive\};",
        panel_e,
    )
    assert transform
    tail = _tikz_pair(transform.group(1))
    head = _tikz_pair(transform.group(2))
    label = _tikz_pair(transform.group(3))
    source_plot_boundary = {"x_min": 0.66, "x_max": 4.24, "y_axis": 1.52}
    derived_region = {"x_min": 0.66, "x_max": 4.24, "y_min": 0.36, "y_max": 1.42}
    assert math.isclose(tail[1], source_plot_boundary["y_axis"], abs_tol=0.01)
    assert source_plot_boundary["x_min"] <= tail[0] <= source_plot_boundary["x_max"]
    assert derived_region["x_min"] <= head[0] <= derived_region["x_max"]
    assert derived_region["y_min"] <= head[1] <= derived_region["y_max"]
    assert math.isclose(tail[0], head[0], abs_tol=0.01)
    assert label[0] > tail[0] and head[1] < label[1] < tail[1]
    assert "Kelvin" not in panel_e
    assert r"\shade" not in panel_e
    assert "opacity=" not in panel_e
    assert "(4.02,1.58)" in panel_e
    assert "(4.02,1.52)" not in panel_e
    assert "ratio ~1.86" not in panel_e
    assert "qualitatively deep-dominant" in panel_e


def test_repaired_panel_f_and_full_figure_keep_role_appropriate_strokes() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_f = source.split("% Panel F", 1)[1]
    widths = [
        float(value)
        for value in re.findall(
            r"line width\s*=\s*([0-9]+(?:\.[0-9]+)?)pt", source
        )
    ]

    assert widths
    assert "line width=0.82pt" in panel_f
    assert "line width=0.86pt" in panel_f
    assert "line width=0.66pt" in panel_f
    assert "line width=0.42pt" in panel_f  # low-contrast Maxwell baseline
    assert "text=cRed!82!black" in panel_f
    assert r"{mechanical\\clamp}" in panel_f
    assert r"{floating polymer\\cantilever}" in panel_f
    assert r"{trapped charge $q_{\mathrm{tr}}$}" in panel_f
    assert r"\shade" not in panel_f


def test_repaired_panel_f_keeps_source_ground_off_the_floating_sample() -> None:
    source = REPAIRED_SOURCE.read_text(encoding="utf-8")
    panel_f = source.split("% Panel F", 1)[1]

    assert "grounded voltage-source return closes only the driven-electrode circuit" in panel_f
    assert "sample and cantilever remain electrically floating" in panel_f
    assert "result arrow begins on the trapped-charge perimeter" in panel_f
    assert "charge-label leader terminates at the marker perimeter" in panel_f
    assert "(0.88,0.46)--(0.96,0.81)" in panel_f
    assert "(1.325,1.43)--(0.34,1.43)" in panel_f
    assert "(3.50,3.58)--(3.65,3.58)--(3.65,3.02)" in panel_f
    assert "(3.00,3.45)--(2.76,3.45)--(2.76,3.30)" in panel_f


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
        PLUGIN_ROOT / "examples" / "fig1_updated_agent_redraw_v1" / "review" / "r5-prospective-v2"
    )
    task = (run_root / "task.md").read_text(encoding="utf-8")
    contract = yaml.safe_load((run_root / "comparison_contract.yaml").read_text(encoding="utf-8"))
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
        PLUGIN_ROOT / "examples" / "fig1_updated_agent_redraw_v1" / "review" / "r5-prospective-v3"
    )
    contract = yaml.safe_load((run_root / "comparison_contract.yaml").read_text(encoding="utf-8"))

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
        PLUGIN_ROOT / "examples" / "fig1_updated_agent_redraw_v1" / "review" / "r5-prospective-v4"
    )
    contract = yaml.safe_load((run_root / "comparison_contract.yaml").read_text(encoding="utf-8"))

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
        (PLUGIN_ROOT / "examples" / "fig1_updated_agent_redraw_v1" / "spec.yaml").read_text(
            encoding="utf-8"
        )
    )

    assert spec["undeclared_geometry_profile"] == "schematic"
