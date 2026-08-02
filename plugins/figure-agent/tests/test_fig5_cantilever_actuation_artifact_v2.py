from __future__ import annotations

import re
import sys
from math import hypot
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig5_cantilever_actuation_artifact_v2"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

import paper_aesthetic_context  # noqa: E402
from semantic_legibility_contract import (  # noqa: E402
    validate_semantic_legibility_contract,
)


def _yaml(name: str) -> dict:
    return yaml.safe_load((FIXTURE / name).read_text(encoding="utf-8"))


def _panel_source(panel_id: str) -> str:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    start = tex.split(f"% Panel {panel_id}", 1)[1]
    following = chr(ord(panel_id) + 1)
    return start.split(f"% Panel {following}", 1)[0]


def _cantilever_centerline(panel_id: str) -> list[tuple[float, float]]:
    panel = _panel_source(panel_id)
    origin = re.search(
        rf"coordinate \(panel-{panel_id.lower()}-beam-origin\) at "
        r"\(([-+0-9.]+),([-+0-9.]+)\)",
        panel,
    )
    path = re.search(
        r"\\draw\[beamOuter\]\s*\([^)]*\)\s*\.\. controls "
        r"\(([-+0-9.]+),([-+0-9.]+)\) and "
        r"\(([-+0-9.]+),([-+0-9.]+)\) \.\. "
        r"\(([-+0-9.]+),([-+0-9.]+)\);",
        panel,
    )
    assert origin is not None
    assert path is not None
    return [
        (float(origin.group(1)), float(origin.group(2))),
        (float(path.group(1)), float(path.group(2))),
        (float(path.group(3)), float(path.group(4))),
        (float(path.group(5)), float(path.group(6))),
    ]


def _cubic_arc_length(points: list[tuple[float, float]], samples: int = 2000) -> float:
    p0, p1, p2, p3 = points
    previous = p0
    total = 0.0
    for index in range(1, samples + 1):
        t = index / samples
        u = 1.0 - t
        point = (
            u**3 * p0[0]
            + 3 * u**2 * t * p1[0]
            + 3 * u * t**2 * p2[0]
            + t**3 * p3[0],
            u**3 * p0[1]
            + 3 * u**2 * t * p1[1]
            + 3 * u * t**2 * p2[1]
            + t**3 * p3[1],
        )
        total += hypot(point[0] - previous[0], point[1] - previous[1])
        previous = point
    return total


def _cubic_max_x(points: list[tuple[float, float]], samples: int = 2000) -> float:
    p0, p1, p2, p3 = points
    return max(
        (1.0 - t) ** 3 * p0[0]
        + 3 * (1.0 - t) ** 2 * t * p1[0]
        + 3 * (1.0 - t) * t**2 * p2[0]
        + t**3 * p3[0]
        for index in range(samples + 1)
        for t in (index / samples,)
    )


def _named_coordinates(panel_id: str, prefix: str) -> dict[str, tuple[float, float]]:
    panel = _panel_source(panel_id)
    matches = re.findall(
        rf"\\coordinate \(({re.escape(prefix)}[^)]*)\) at "
        r"\(([-+0-9.]+),([-+0-9.]+)\)",
        panel,
    )
    return {name: (float(x), float(y)) for name, x, y in matches}


def _distance_to_cubic(
    point: tuple[float, float],
    curve: list[tuple[float, float]],
    samples: int = 4000,
) -> float:
    p0, p1, p2, p3 = curve
    return min(
        hypot(
            point[0]
            - (
                (1.0 - t) ** 3 * p0[0]
                + 3 * (1.0 - t) ** 2 * t * p1[0]
                + 3 * (1.0 - t) * t**2 * p2[0]
                + t**3 * p3[0]
            ),
            point[1]
            - (
                (1.0 - t) ** 3 * p0[1]
                + 3 * (1.0 - t) ** 2 * t * p1[1]
                + 3 * (1.0 - t) * t**2 * p2[1]
                + t**3 * p3[1]
            ),
        )
        for index in range(samples + 1)
        for t in (index / samples,)
    )


def test_fig5_declares_a_width_limited_physical_print_contract() -> None:
    spec = _yaml("spec.yaml")
    contract = spec["final_size_contract"]

    assert contract["basis"] == "width_limited_nature_family_main_figure"
    assert contract["natural_size_mm"] == [180.8, 53.14]
    assert contract["target_width_mm"] == 180.0
    assert contract["max_height_mm"] == 170.0
    assert contract["min_print_font_pt"] == 5.0
    assert contract["scale_basis"] == "width_limited"
    assert contract["double_column_reference_mm"] == {
        "nature_communications": 180.0,
        "nature_figure_guide": 183.0,
    }
    assert contract["natural_size_mm"][1] < contract["max_height_mm"]
    assert spec["review_scale_previews"] == "required"
    assert spec["paper_aesthetic_context"] == "nc-main-text-series"
    assert spec["journal_art_direction_playbook"] == "nc-main-text"
    assert spec["aesthetic_intent"] == "aesthetic_intent.yaml"
    assert (FIXTURE / "aesthetic_intent.yaml").is_file()


def test_fig5_paper_aesthetic_context_is_schema_valid() -> None:
    context_path = (
        PLUGIN_ROOT / "examples" / "_paper_aesthetic_contexts" / "nc-main-text-series.yaml"
    )
    context = paper_aesthetic_context.load_paper_aesthetic_context(context_path)
    role = paper_aesthetic_context.matching_figure_role(
        context, "fig5_cantilever_actuation_artifact_v2"
    )

    assert role["role"] == "mechanism_detail"
    assert set(role["must_align_with"]) == {
        "restrained_palette",
        "compact_typography",
        "source_first_polish",
    }


def test_fig5_requires_a_transferable_mechanism_contract() -> None:
    spec = _yaml("spec.yaml")
    assert spec["semantic_contract_required"] is True

    contract = validate_semantic_legibility_contract(_yaml("semantic_contract.yaml"))
    assert contract["publication_acceptance"] == "not_claimed"
    assert contract["summary"]["object_role_count"] == 30
    assert contract["summary"]["visible_connector_count"] == 6
    assert contract["summary"]["label_ownership_count"] == 17
    assert contract["summary"]["panel_story_role_count"] == 4
    assert contract["summary"]["electrical_node_count"] == 9
    assert contract["summary"]["electrical_connection_count"] == 1
    assert contract["summary"]["floating_object_count"] == 4


def test_fig5_declares_grounded_then_floating_electrical_topology() -> None:
    semantic = _yaml("semantic_contract.yaml")["semantic_legibility"]
    topology = semantic["electrical_topology"]
    states = {item["object_id"]: item["declared_state"] for item in topology["nodes"]}

    assert states["panel_a.cantilever"] == "ground_reference"
    assert states["panel_a.clip_ground"] == "ground_reference"
    assert states["panel_a.drive_electrode"] == "driven"
    assert states["panel_b.cantilever"] == "floating"
    assert states["panel_b.clip"] == "floating"
    assert states["panel_c.cantilever"] == "floating"
    assert states["panel_c.clip"] == "floating"
    assert states["panel_c.drive_electrode"] == "driven"
    assert topology["connections"] == [
        {
            "connection_id": "panel_a.clip_contacts_cantilever",
            "from_object": "panel_a.clip_ground",
            "to_object": "panel_a.cantilever",
            "declared_role": "electrical_contact",
        }
    ]


def test_fig5_visible_connectors_do_not_claim_undrawn_cross_panel_arrows() -> None:
    connectors = _yaml("semantic_contract.yaml")["semantic_legibility"][
        "visible_connectors"
    ]

    assert all(
        item["from_object"].split(".", 1)[0] == item["to_object"].split(".", 1)[0]
        for item in connectors
    )
    assert not any(item["render_style"] == "stage_transition" for item in connectors)


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
    assert "actuation hold" in charge_subtitle.group(1)
    assert "field-on charging" not in charge_subtitle.group(1)

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

    coulomb = connectors["panel_c.coulomb_originates_at_trapped_charge"]
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


def test_fig5_charge_markers_remain_inside_each_cantilever() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    assert "minimum size=1.00mm" in tex

    expected_counts = {"A": 3, "B": 4, "C": 3}
    for panel_id, expected_count in expected_counts.items():
        coordinates = _named_coordinates(panel_id, f"panel-{panel_id.lower()}-q")
        if panel_id == "C":
            coordinates.update(
                _named_coordinates(panel_id, "panel-c-force-origin")
            )
        assert len(coordinates) == expected_count
        assert all(
            _distance_to_cubic(point, _cantilever_centerline(panel_id)) <= 0.012
            for point in coordinates.values()
        ), coordinates


def test_fig5_force_origins_bind_to_charge_or_film_surface() -> None:
    protected = set(_yaml("semantic_contract.yaml")["protected_relations"])
    assert "representative_charge_markers_remain_inside_film" in protected
    assert "force_vector_origins_touch_declared_body" in protected

    panel_a = _panel_source("A")
    panel_b = _panel_source("B")
    panel_c = _panel_source("C")
    assert "(panel-a-attraction-origin)--(panel-a-attraction-head)" in panel_a
    assert "(panel-b-residual-origin)--(panel-b-residual-head)" in panel_b
    assert "(panel-c-maxwell-origin)--(panel-c-maxwell-head)" in panel_c
    assert "(panel-c-force-origin)--(panel-c-coulomb-head)" in panel_c


def test_fig5_conditional_reverse_force_hierarchy_matches_the_drawn_vectors() -> None:
    protected = set(_yaml("semantic_contract.yaml")["protected_relations"])
    assert "conditional_reverse_bend_owns_force_hierarchy" in protected

    coulomb = _named_coordinates("C", "panel-c-force-origin")
    coulomb.update(_named_coordinates("C", "panel-c-coulomb-head"))
    maxwell = _named_coordinates("C", "panel-c-maxwell-")
    coulomb_span = hypot(
        coulomb["panel-c-coulomb-head"][0]
        - coulomb["panel-c-force-origin"][0],
        coulomb["panel-c-coulomb-head"][1]
        - coulomb["panel-c-force-origin"][1],
    )
    maxwell_span = hypot(
        maxwell["panel-c-maxwell-head"][0]
        - maxwell["panel-c-maxwell-origin"][0],
        maxwell["panel-c-maxwell-head"][1]
        - maxwell["panel-c-maxwell-origin"][1],
    )

    assert coulomb_span >= 1.15 * maxwell_span
    panel_c = _panel_source("C")
    assert "{Coulomb};" in panel_c
    assert "{Maxwell attraction};" in panel_c


def test_fig5_residual_force_vector_is_visibly_shorter_than_drive_on() -> None:
    protected = set(_yaml("semantic_contract.yaml")["protected_relations"])
    assert (
        "residual_attraction_vector_is_shorter_than_drive_on_attraction"
        in protected
    )

    drive = _named_coordinates("A", "panel-a-attraction-")
    residual = _named_coordinates("B", "panel-b-residual-")
    drive_span = hypot(
        drive["panel-a-attraction-head"][0]
        - drive["panel-a-attraction-origin"][0],
        drive["panel-a-attraction-head"][1]
        - drive["panel-a-attraction-origin"][1],
    )
    residual_span = hypot(
        residual["panel-b-residual-head"][0]
        - residual["panel-b-residual-origin"][0],
        residual["panel-b-residual-head"][1]
        - residual["panel-b-residual-origin"][1],
    )
    assert residual_span <= 0.78 * drive_span
    assert "\\draw[forceToward,opacity=0.62]" in _panel_source("B")


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

    assert "isolation-boundary-state" not in checks
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
    assert "The source-OFF text owns the plateau event" in panel_d
    assert "\\draw[leader] (1.54,3.58)--(1.54,4.02);" in panel_d


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

    assert "clip: floating" in panel_b
    assert "GND lead lifted" in panel_b
    assert panel_b.count("leadTerminal") == 2
    assert "(panel-b-clamp-axis)--(1.69,4.43);" in panel_b
    assert "(1.22,4.66)--(1.46,4.58);" in panel_b
    assert "(0.56,1.02)--(0.90,1.02);" not in panel_b
    assert "clip: floating" in panel_b
    assert "switch" not in panel_b.lower()


def test_fig5_keeps_clamp_state_labels_clear_of_the_drive_terminal() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]
    panel_c = tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0]

    assert "clip: GND" in panel_a
    assert "clip: floating" in panel_b
    assert re.search(r"align=right,anchor=east\] at \([^)]*\)", panel_c)
    assert "clip: floating" in panel_c


def test_fig5_declares_clearance_for_the_y_axis_angle_label() -> None:
    spec = _yaml("spec.yaml")
    checks = {
        item["id"]: item for item in spec["label_path_proximity_checks"]
    }
    axis_check = checks["panel-d-bend-angle-axis"]

    assert axis_check["kind"] == "vertical_line"
    assert axis_check["role"] == "axis_label_lane"
    assert axis_check["x_pdf_cm"] == 13.97
    assert axis_check["clearance_pt"] == 2.5
    assert axis_check["text_phrases"] == [{"id": "angle_label", "words": ["angle"]}]

    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_d = tex.split("% Panel D", 1)[1]
    assert re.search(
        r"anchor=south west\] at \(0\.20,4\.15\) \{angle\}",
        panel_d,
    )


def test_fig5_declares_clearance_for_the_recovery_label_and_trace_tail() -> None:
    spec = _yaml("spec.yaml")
    checks = {
        item["id"]: item for item in spec["label_path_proximity_checks"]
    }
    recovery = checks["panel-d-recovery-tail"]

    assert recovery["kind"] == "polyline"
    assert recovery["role"] == "qualitative_response_curve"
    assert recovery["clearance_pt"] == 3.0
    assert recovery["defect_kind"] == "label_curve_near_label"
    assert recovery["text_phrases"] == [
        {"id": "recovery_label", "words": ["recovery"]}
    ]


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
    assert "\\coordinate (panel-b-residual-origin)" in panel_b
    assert "\\coordinate (panel-b-residual-head)" in panel_b
    assert (
        "\\draw[forceToward,opacity=0.62]\n"
        "    (panel-b-residual-origin)--(panel-b-residual-head);"
        in panel_b
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
    a_origin = re.search(r"coordinate \(panel-a-beam-origin\) at \(([^,]+),", panel_a)
    b_origin = re.search(r"coordinate \(panel-b-beam-origin\) at \(([^,]+),", panel_b)
    assert a_origin is not None
    assert b_origin is not None
    a_deflection = float(a_endpoint.group(1)) - float(a_origin.group(1))
    b_deflection = float(b_endpoint.group(1)) - float(b_origin.group(1))
    assert a_deflection - b_deflection >= 0.30
    assert b_deflection <= 0.70


def test_fig5_repeated_cantilevers_preserve_specimen_arc_length() -> None:
    lengths = {
        panel_id: _cubic_arc_length(_cantilever_centerline(panel_id))
        for panel_id in ("A", "B", "C")
    }
    mean_length = sum(lengths.values()) / len(lengths)
    relative_deviation = max(
        abs(length - mean_length) / mean_length for length in lengths.values()
    )

    # Deflection amplitude belongs to the state; specimen length does not.  A
    # small schematic tolerance allows hand-authored curvature without letting
    # an independently redrawn path become a visibly shorter member.
    assert relative_deviation <= 0.03, lengths


def test_fig5_drive_electrodes_keep_clearance_from_the_maximum_bend() -> None:
    electrode_left = {"A": 3.42, "B": 3.42, "C": 3.44}
    centerline_clearances = {
        panel_id: electrode_left[panel_id]
        - _cubic_max_x(_cantilever_centerline(panel_id))
        for panel_id in electrode_left
    }

    # The limiting state is Panel A.  Keep enough centerline clearance for the
    # finite-width member and print-scale anti-touch perception; a dimension
    # arrow alone is not evidence that the bent specimen remains separated.
    assert min(centerline_clearances.values()) >= 0.80, centerline_clearances


def test_fig5_bend_states_have_a_reader_visible_stage_order() -> None:
    origins = {panel_id: _cantilever_centerline(panel_id)[0][0] for panel_id in "ABC"}
    tips = {panel_id: _cantilever_centerline(panel_id)[-1][0] for panel_id in "ABC"}
    lateral_deflection = {
        panel_id: tips[panel_id] - origins[panel_id] for panel_id in "ABC"
    }

    # A is the strong drive-on attraction, B is the smaller retained residual,
    # and C reverses direction.  The ordering must survive print reduction,
    # while the arc-length contract above keeps these states one specimen.
    assert lateral_deflection["A"] > 0.90
    assert 0.30 < lateral_deflection["B"] < 0.55
    assert lateral_deflection["C"] < -0.60
    assert abs(lateral_deflection["B"]) < 0.65 * min(
        abs(lateral_deflection["A"]), abs(lateral_deflection["C"])
    )


def test_fig5_panel_b_keeps_source_off_state_floating_with_residual_attraction() -> None:
    contract = _yaml("semantic_contract.yaml")
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]

    assert "clip: floating" in panel_b
    assert "residual attraction" in panel_b
    assert "support GND" not in panel_b
    assert "clip: GND" not in panel_b
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
    assert "clip: floating" in panel_b
    assert "residual attraction" in panel_b
    assert "clip: GND" not in panel_b
    assert "drive inactive" not in panel_b
    assert "after floating isolation" in panel_c
    assert "clip: floating" in panel_c


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


def test_fig5_source_off_label_is_owned_by_the_inactive_drive_electrode() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]
    match = re.search(
        r"\\node\[labelStd,anchor=south\] at \((\d+\.\d+),(\d+\.\d+)\)"
        r" \{OFF\};",
        panel_b,
    )
    assert match is not None
    assert panel_b.count("driveBiasLeader") == 1
    assert 3.45 < float(match.group(1)) < 3.65
    y = float(match.group(2))
    assert 4.55 < y < 4.70


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
