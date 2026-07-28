from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig5_cantilever_actuation_artifact_v2"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

from semantic_legibility_contract import (  # noqa: E402
    validate_semantic_legibility_contract,
)


def _yaml(name: str) -> dict:
    return yaml.safe_load((FIXTURE / name).read_text(encoding="utf-8"))


def test_fig5_declares_a_width_limited_physical_print_contract() -> None:
    contract = _yaml("spec.yaml")["final_size_contract"]

    assert contract["basis"] == "width_limited_nature_family_main_figure"
    assert contract["natural_size_mm"] == [180.8, 53.5]
    assert contract["target_width_mm"] == 180.0
    assert contract["max_height_mm"] == 170.0
    assert contract["min_print_font_pt"] == 5.0
    assert contract["scale_basis"] == "width_limited"
    assert contract["double_column_reference_mm"] == {
        "nature_communications": 180.0,
        "nature_figure_guide": 183.0,
    }
    assert contract["natural_size_mm"][1] < contract["max_height_mm"]


def test_fig5_requires_a_transferable_mechanism_contract() -> None:
    spec = _yaml("spec.yaml")
    assert spec["semantic_contract_required"] is True

    contract = validate_semantic_legibility_contract(_yaml("semantic_contract.yaml"))
    assert contract["publication_acceptance"] == "not_claimed"
    assert contract["summary"]["object_role_count"] == 21
    assert contract["summary"]["visible_connector_count"] == 9
    assert contract["summary"]["label_ownership_count"] == 17
    assert contract["summary"]["panel_story_role_count"] == 4


def test_fig5_declares_reader_facing_stage_order_assertions() -> None:
    assertions = _yaml("spec.yaml")["semantic_assertions"]

    assert [item["id"] for item in assertions] == [
        "source-off-before-reversed-drive",
        "reversed-drive-before-recovery",
    ]
    assert {(item["relation"], item["subject"], item["reference"]) for item in assertions} == {
        ("left_of", "source-off", "reversed-drive"),
        ("left_of", "reversed-drive", "recovery"),
    }


def test_fig5_contract_separates_actuation_charge_from_measurement_meanings() -> None:
    contract = _yaml("semantic_contract.yaml")
    protected = set(contract["protected_relations"])
    forbidden = set(contract["forbidden_implications"])

    assert "charge_phase_is_actuation_state" in protected
    assert "cantilever_faces_drive_electrode_across_air_gap" in protected
    assert "air_gap_coupling_is_capacitor_like_schematic_only" in protected
    assert "conditional_reverse_bend_owns_force_hierarchy" in protected
    assert "clamp_axis_aligns_with_cantilever_centerline" in protected
    assert "same_mounted_film_scale_across_panels" in protected
    assert "reverse_response_is_faster_than_initial_attraction" in protected
    assert "positive_plateau_is_explicit" in protected
    assert "trap_label_leader_clears_glyphs" in protected
    assert "lead_separation_is_manual" in protected
    assert "cantilever_remains_clamped_after_manual_lead_lift" in protected
    assert "panel_b_floats_after_source_off" in protected
    assert "residual_attraction_bend_persists_after_source_off" in protected
    assert "cantilever_free_end_follows_local_tangent" in protected
    assert "panel_a.standalone_two_terminal_charger" in forbidden
    assert "panel_b.automated_switch" in forbidden
    assert "panel_a.polarization_measurement_instrument" in forbidden
    assert "panel_a.esvm_measurement_head" in forbidden
    assert "panel_a.corona_needle" in forbidden


def test_fig5_voltage_label_is_owned_by_drive_electrode_not_clip_ground() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]

    charge_subtitle = re.search(
        r"\\node\[labelMute,anchor=west\] at \([^)]*\)\s*\{([^}]*)\};",
        panel_a,
    )
    assert charge_subtitle is not None
    assert "kV" not in charge_subtitle.group(1)
    assert "field-on charge" in charge_subtitle.group(1)

    assert re.search(r"\\node\[labelMute,anchor=west\] at \([^)]*\) \{clip: GND\};", panel_a)
    assert "clip: GND" in panel_a
    assert "text=cRed!82!black,anchor=south" in panel_a
    assert "{$+5\\,\\mathrm{kV}$};" in panel_a
    assert panel_a.count("driveBiasLeader") == 1
    assert re.search(r"\\node\[labelStd,text=cRed!82!black,anchor=south\] at \([^)]*\)", panel_a)


def test_fig5_trapped_charge_label_leader_starts_outside_its_glyphs() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]

    assert re.search(r"anchor=east\] at \([^)]*\)\s*\n?\s*\{trapped", panel_a)
    assert re.search(r"\\draw\[leader,cRed!58!black\] \([^)]*\)--\([^)]*\);", panel_a)
    assert "{trapped $q_{\\mathrm{tr}}}" not in panel_a


def test_fig5_marks_reverse_force_as_conditional_after_isolation() -> None:
    contract = _yaml("semantic_contract.yaml")
    connectors = {
        item["connector_id"]: item
        for item in contract["semantic_legibility"]["visible_connectors"]
    }
    panel_story = {
        item["panel_id"]: item
        for item in contract["semantic_legibility"]["panel_story"]["panels"]
    }

    coulomb = connectors["panel_b.isolation_enables_reversed_force"]
    assert coulomb["epistemic_status"] == "conditional"
    assert coulomb["render_style"] == "force_conditional"
    assert coulomb["condition"]
    assert panel_story["B"]["role"] == "workflow"
    assert panel_story["C"]["role"] == "mechanism"
    sequence = contract["semantic_legibility"]["panel_story"]["causal_sequence"]
    assert [item["stage"] for item in sequence["stages"]] == [
        "preparation",
        "isolation",
        "perturbation",
        "response",
    ]


def test_fig5_declares_the_reverse_bend_as_conditional_not_a_second_snapshot() -> None:
    contract = _yaml("semantic_contract.yaml")
    roles = {
        item["object_id"]: item
        for item in contract["semantic_legibility"]["object_roles"]
    }

    reverse_bend = roles["panel_c.conditional_reverse_bend"]
    assert reverse_bend["declared_role"] == "conditional_reverse_bend_response"
    assert "observed_comparison" in reverse_bend["forbidden_readings"]


def test_fig5_binds_conditional_coulomb_force_to_a_visible_trapped_charge() -> None:
    contract = _yaml("semantic_contract.yaml")
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_c = tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0]
    connectors = {
        item["connector_id"]: item
        for item in contract["semantic_legibility"]["visible_connectors"]
    }

    force_origin = connectors["panel_c.coulomb_originates_at_trapped_charge"]
    assert force_origin["from_object"] == "panel_c.trapped_charge"
    assert force_origin["to_object"] == "panel_c.coulomb_force"
    assert force_origin["epistemic_status"] == "conditional"
    assert panel_c.count("\\node[qmark]") >= 3
    assert re.search(r"\\draw\[forceAway\] \([^)]*\)--\([^)]*\);", panel_c)


def test_fig5_panel_c_reserves_copy_for_the_reverse_bend_threshold() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_c = tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0]

    assert "reverse bend if $|F_{\\mathrm{C}}|>|F_{\\mathrm{M}}|$" in panel_c
    assert "opposes $F_{\\mathrm{M}}$" not in panel_c


def test_fig5_declares_rendered_charge_to_isolation_and_response_stages() -> None:
    spec = _yaml("spec.yaml")
    checks = {item["id"]: item for item in spec["process_stage_visibility_checks"]}

    assert [stage["id"] for stage in checks["isolation-boundary-state"]["stages"]] == [
        "source-off",
        "floating-state",
    ]
    floating_phrases = checks["isolation-boundary-state"]["stages"][1]["text_phrases"]
    assert {tuple(item["words"]) for item in floating_phrases} == {("floating",)}
    assert [stage["id"] for stage in checks["qualitative-response-sequence"]["stages"]] == [
        "observation-origin",
        "source-off-float",
        "reversed-drive",
        "recovery",
    ]
    origin_phrases = checks["qualitative-response-sequence"]["stages"][0]["text_phrases"]
    assert {tuple(item["words"]) for item in origin_phrases} == {
        ("t", "=", "0"),
    }
    off_phrases = checks["qualitative-response-sequence"]["stages"][1]["text_phrases"]
    assert {tuple(item["words"]) for item in off_phrases} == {
        ("OFF",),
        ("floating",),
    }


def test_fig5_response_trace_separates_off_float_from_reversal() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_d = tex.split("% Panel D", 1)[1]

    assert "+5\\,\\mathrm{kV}$ precharge" not in panel_d
    assert "20 min" not in panel_d
    assert re.search(r"\\draw\[[^]]*\] \([^)]*\)--\([^)]*\);", panel_d)
    assert "source OFF" in panel_d
    assert "clip floating" in panel_d
    assert "reverse" in panel_d.lower()


def test_fig5_response_trace_has_a_visible_sustained_positive_plateau() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_d = tex.split("% Panel D", 1)[1]

    assert "sustained positive plateau" in panel_d
    assert re.search(
        r"\)\s*--\s*\([^)]*\)\s*\n\s*\.\. controls",
        panel_d,
    )
    assert "rounded summit" not in panel_d


def test_fig5_panel_b_keeps_the_specimen_mounted_and_lifts_the_lead_manually() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]

    assert "clip remains mounted" in panel_b
    assert "lead lifted manually" in panel_b
    assert panel_b.count("leadTerminal") == 2
    assert "clip floating" in panel_b
    assert "switch" not in panel_b.lower()


def test_fig5_keeps_clamp_state_labels_clear_of_the_drive_terminal() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]
    panel_c = tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0]

    assert "clip: GND" in panel_a
    assert "clip remains mounted" in panel_b
    assert "clip floating" in panel_b
    assert re.search(r"align=right,anchor=east\] at \([^)]*\)", panel_c)
    assert "electrically floating" in panel_c


def test_fig5_declares_clearance_for_the_rotated_bend_angle_label() -> None:
    spec = _yaml("spec.yaml")
    checks = {
        item["id"]: item for item in spec["label_path_proximity_checks"]
    }
    axis_check = checks["panel-d-bend-angle-axis"]

    assert axis_check["kind"] == "vertical_line"
    assert axis_check["role"] == "axis_label_lane"
    assert axis_check["x_pdf_cm"] == 13.97
    assert axis_check["clearance_pt"] == 2.5
    assert axis_check["text_phrases"] == [
        {"id": "bend_angle_label", "words": ["bend", "angle"]}
    ]

    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_d = tex.split("% Panel D", 1)[1]
    assert re.search(
        r"rotate=90,anchor=south\] at \(0\.24,2\.56\) \{bend angle\}",
        panel_d,
    )


def test_fig5_keeps_opposite_drive_labels_on_one_body_rail() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_c = tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0]

    assert "driveBiasLeader" in panel_a
    assert panel_a.count("driveBiasLeader") == 1
    assert "{$+5\\,\\mathrm{kV}$};" in panel_a
    assert panel_c.count("driveBiasLeader") == 1
    assert "{$-5\\,\\mathrm{kV}$};" in panel_c
    assert "{drive electrode}" not in panel_a
    assert "{drive electrode}" not in panel_c


def test_fig5_force_and_gap_endpoints_bind_to_rendered_beam_geometry() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]

    assert re.search(r"\\draw\[gapDimension\] \([^)]*\)--\([^)]*\);", panel_a)
    assert re.search(
        r"\\draw\[forceToward,opacity=0\.62\] \([^)]*\)--\([^)]*\);",
        panel_b,
    )


def test_fig5_air_gap_uses_explicit_dimension_heads_and_witness_ticks() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]

    assert "gapDimension/.style={Stealth-Stealth" in tex
    assert "gapWitness" in panel_a
    assert panel_a.count("\\draw[gapWitness]") == 2
    assert "gapDimension/.style={<->" not in tex


def test_fig5_drive_on_and_residual_bends_have_visible_amplitude_contrast() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]

    endpoint_pattern = (
        r"\.\. controls \([^)]*\) and \([^)]*\) "
        r"\.\. \(([^,]+),([^)]+)\);"
    )
    a_endpoint = re.search(endpoint_pattern, panel_a)
    b_endpoint = re.search(endpoint_pattern, panel_b)
    assert a_endpoint is not None
    assert b_endpoint is not None
    assert float(a_endpoint.group(1)) - float(b_endpoint.group(1)) >= 0.30
    assert float(b_endpoint.group(1)) <= 2.15


def test_fig5_panel_b_keeps_source_off_state_floating_with_residual_attraction() -> None:
    contract = _yaml("semantic_contract.yaml")
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]

    assert "clip floating" in panel_b
    assert "residual attraction" in panel_b
    assert "support GND" not in panel_b
    assert "GND" not in panel_b
    assert any(
        connector["connector_id"]
        == "panel_b.floating_state_retains_residual_attraction"
        for connector in contract["semantic_legibility"]["visible_connectors"]
    )
    assert "fixed support reference" not in panel_b


def test_fig5_makes_the_ground_to_floating_transition_reader_facing() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]
    panel_c = tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0]

    assert "clip: GND" in panel_a
    assert panel_a.count("driveBiasLeader") == 1
    assert panel_c.count("driveBiasLeader") == 1
    assert "clip floating" in panel_b
    assert "clip floating" in panel_b
    assert "residual attraction" in panel_b
    assert "GND" not in panel_b
    assert "drive inactive" not in panel_b
    assert "after floating isolation" in panel_c
    assert "electrically floating" in panel_c


def test_fig5_declares_deterministic_clamp_axis_geometry_check() -> None:
    spec = _yaml("spec.yaml")
    assertions = {item["id"]: item for item in spec["tex_assertions"]}
    alignment = assertions["clamp-axis-bisects-cantilever-fixed-end"]
    assert alignment["kind"] == "path_origin_aligned"
    assert alignment["origin_coordinate"] == "panel-c-beam-origin"
    assert alignment["reference_coordinate"] == "panel-c-clamp-axis"

    actuation_alignment = assertions["actuation-clamp-axis-bisects-cantilever-fixed-end"]
    assert actuation_alignment["kind"] == "path_origin_aligned"
    assert actuation_alignment["origin_coordinate"] == "panel-a-beam-origin"
    assert actuation_alignment["reference_coordinate"] == "panel-a-clamp-axis"

    isolation_alignment = assertions["isolation-clamp-axis-bisects-cantilever-fixed-end"]
    assert isolation_alignment["kind"] == "path_origin_aligned"
    assert isolation_alignment["origin_coordinate"] == "panel-b-beam-origin"
    assert isolation_alignment["reference_coordinate"] == "panel-b-clamp-axis"


def test_fig5_contract_keeps_style_free_and_coordinates_free() -> None:
    contract = _yaml("semantic_contract.yaml")

    def keys(value: object) -> set[str]:
        if isinstance(value, dict):
            result = set(value)
            for child in value.values():
                result.update(keys(child))
            return {str(item) for item in result}
        if isinstance(value, list):
            result: set[str] = set()
            for child in value:
                result.update(keys(child))
            return result
        return set()

    forbidden_keys = {item.lower() for item in keys(contract)}
    assert "tikz" not in forbidden_keys
    assert "coordinates" not in forbidden_keys
    assert "primitive" not in forbidden_keys


def test_fig5_response_trace_has_no_erased_gap_shortcut() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_d = tex.split("% Panel D", 1)[1]
    assert "\\draw[white" not in panel_d
    assert panel_d.count("\\draw[cBlue!82!black,line width=1.05pt]") == 1
    assert "{$t=0$}" in panel_d
    assert "\\mathrm{s}" not in panel_d
    assert "\\mathrm{s}" not in tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]


def test_fig5_source_off_label_uses_the_manual_isolation_lane() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]
    match = re.search(
        r"\\node\[labelStd,anchor=west\] at \((\d+\.\d+),(\d+\.\d+)\)"
        r" \{source OFF\};",
        panel_b,
    )
    assert match is not None
    assert 0.40 < float(match.group(1)) < 0.60
    y = float(match.group(2))
    assert 0.45 < y < 0.70


def test_fig5_repeated_apparatus_keeps_shared_datum_and_electrode_role() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panels = [
        tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0],
        tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0],
        tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0],
    ]
    clamp_pattern = re.compile(
        r"\\fill\[cGray![0-9]+\].*?4\.05\).*?4\.34\)", re.DOTALL
    )
    electrode_pattern = re.compile(
        r"\\fill\[cGray!28\].*?1\.40\).*?4\.34\)", re.DOTALL
    )
    assert all(clamp_pattern.search(panel) for panel in panels)
    assert all(electrode_pattern.search(panel) for panel in panels)
    assert all("\\draw[apparatus]" in panel for panel in panels)
    assert all(
        re.search(r"coordinate \(panel-[abc]-(?:clamp-axis|beam-origin)\)", panel)
        for panel in panels
    )

    assert tex.count("\\draw[beamOuter]") == 3
    assert tex.count("\\draw[beamInner]") == 3


def test_fig5_reverse_bend_keeps_the_same_rounded_member_extent() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_c = tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0]

    assert "beamOuter" in panel_a
    assert "beamInner" in panel_a
    assert "beamOuter" in panel_c
    assert "beamInner" in panel_c
    assert panel_a.count("\\draw[beamOuter]") == 1
    assert panel_a.count("\\draw[beamInner]") == 1
    assert panel_c.count("\\draw[beamOuter]") == 1
    assert panel_c.count("\\draw[beamInner]") == 1
    assert "panel-a-beam-origin" in panel_a
    assert "panel-c-beam-origin" in panel_c


def test_fig5_source_off_residual_bend_is_visibly_smaller_than_drive_bends() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]
    panel_c = tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0]

    assert all("\\draw[beamOuter]" in panel for panel in (panel_a, panel_b, panel_c))
    assert all("\\draw[beamInner]" in panel for panel in (panel_a, panel_b, panel_c))


def test_fig5_centerline_beams_have_deliberate_free_end_terminations() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panels = {
        "a": tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0],
        "b": tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0],
        "c": tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0],
    }
    for panel in panels.values():
        assert panel.count("\\draw[beamOuter]") == 1
        assert panel.count("\\draw[beamInner]") == 1
        assert re.search(r"coordinate \(panel-[abc]-beam-origin\)", panel)
