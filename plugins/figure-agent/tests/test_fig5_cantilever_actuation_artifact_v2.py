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


def test_fig5_requires_a_transferable_mechanism_contract() -> None:
    spec = _yaml("spec.yaml")
    assert spec["semantic_contract_required"] is True

    contract = validate_semantic_legibility_contract(_yaml("semantic_contract.yaml"))
    assert contract["publication_acceptance"] == "not_claimed"
    assert contract["summary"]["object_role_count"] == 19
    assert contract["summary"]["visible_connector_count"] == 7
    assert contract["summary"]["label_ownership_count"] == 14
    assert contract["summary"]["panel_story_role_count"] == 4


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
    assert "clip_separation_is_manual" in protected
    assert "cantilever_remains_clamped_during_ground_open" in protected
    assert "fixed_support_reference_is_distinct_from_film_clip" in protected
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
        r"\\node\[labelMute,anchor=west\] at \(0\.44,4\.78\)\s*\{([^}]*)\};",
        panel_a,
    )
    assert charge_subtitle is not None
    assert "kV" not in charge_subtitle.group(1)
    assert "field-on charge" in charge_subtitle.group(1)

    assert "at (1.68,4.52) {clip: GND};" in panel_a
    assert "at (0.82,4.20) {clip: GND};" not in panel_a
    voltage_nodes = re.findall(
        r"\\node\[labelStd,text=cRed!82!black,anchor=(?:west|east)\].*?\{\$\+5\\,\\mathrm\{kV\}\$\};",
        panel_a,
        re.DOTALL,
    )
    assert len(voltage_nodes) == 1
    drive_label = panel_a.index("{drive electrode}")
    voltage_label = panel_a.index("{$+5\\,\\mathrm{kV}$}")
    assert voltage_label > drive_label


def test_fig5_trapped_charge_label_leader_starts_outside_its_glyphs() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]

    assert "anchor=east] at (1.06,3.04)" in panel_a
    assert "(1.13,3.08)--(1.41,3.56)" in panel_a
    assert "anchor=west] at (0.26,3.04)" not in panel_a


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


def test_fig5_declares_rendered_charge_to_isolation_and_response_stages() -> None:
    spec = _yaml("spec.yaml")
    checks = {item["id"]: item for item in spec["process_stage_visibility_checks"]}

    assert [stage["id"] for stage in checks["isolation-boundary-state"]["stages"]] == [
        "source-off",
        "clip-open",
    ]
    clip_open_phrases = checks["isolation-boundary-state"]["stages"][1]["text_phrases"]
    assert {tuple(item["words"]) for item in clip_open_phrases} == {
        ("GND", "open"),
        ("support", "reference"),
    }
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
    assert "(1.38,3.68)--(2.08,3.68)" in panel_d
    assert "at (1.73,4.30) {source OFF};" in panel_d
    assert "at (1.73,4.08) {clip floating};" in panel_d
    assert "(1.82,1.04)--(1.82,3.56)" in panel_d
    assert "at (2.24,3.04)" in panel_d


def test_fig5_response_trace_has_a_visible_sustained_positive_plateau() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_d = tex.split("% Panel D", 1)[1]

    assert "sustained positive plateau" in panel_d
    assert "-- (1.68,3.58)" in panel_d
    assert "rounded summit" not in panel_d


def test_fig5_panel_b_keeps_the_specimen_mounted_and_separates_ground_manually() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]

    assert "clip remains mounted" in panel_b
    assert "manual clip lift" in panel_b
    assert "circle (0.58pt)" in panel_b
    assert "switch" not in panel_b.lower()


def test_fig5_repeats_clamp_state_labels_in_a_shared_top_right_lane() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]
    panel_c = tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0]

    assert "at (1.68,4.52) {clip: GND};" in panel_a
    assert "at (2.00,4.52) {clip remains mounted};" in panel_b
    assert "at (1.67,4.52) {floating clip};" in panel_c


def test_fig5_panel_b_names_the_open_film_clip_and_fixed_support_reference() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_b = tex.split("% Panel B", 1)[1].split("% Panel C", 1)[0]

    assert "film clip GND open" in panel_b
    assert "support reference held at GND" in panel_b
    assert "reference potential fixed" not in panel_b


def test_fig5_declares_deterministic_clamp_axis_geometry_check() -> None:
    spec = _yaml("spec.yaml")
    assertions = {item["id"]: item for item in spec["tex_assertions"]}
    alignment = assertions["clamp-axis-bisects-cantilever-fixed-end"]
    assert alignment["kind"] == "centerline_aligned"
    assert alignment["edge_coordinates"] == [
        "panel-c-cantilever-left",
        "panel-c-cantilever-right",
    ]
    assert alignment["reference_coordinate"] == "panel-c-clamp-axis"

    actuation_alignment = assertions["actuation-clamp-axis-bisects-cantilever-fixed-end"]
    assert actuation_alignment["kind"] == "centerline_aligned"
    assert actuation_alignment["edge_coordinates"] == [
        "panel-a-cantilever-left",
        "panel-a-cantilever-right",
    ]
    assert actuation_alignment["reference_coordinate"] == "panel-a-clamp-axis"

    isolation_alignment = assertions["isolation-clamp-axis-bisects-cantilever-fixed-end"]
    assert isolation_alignment["kind"] == "centerline_aligned"
    assert isolation_alignment["edge_coordinates"] == [
        "panel-b-cantilever-left",
        "panel-b-cantilever-right",
    ]
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
    assert 1.90 < float(match.group(1)) < 2.20
    y = float(match.group(2))
    assert 1.20 < y < 1.50


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

    coordinate_pattern = re.compile(
        r"\\coordinate \(panel-([abc])-cantilever-(left|right)\)"
        r"\s+at \((\d+\.\d+),4\.05\)"
    )
    widths: dict[str, dict[str, float]] = {}
    for panel_id, edge, x in coordinate_pattern.findall(tex):
        widths.setdefault(panel_id, {})[edge] = float(x)
    assert set(widths) == {"a", "b", "c"}
    member_widths = [edges["right"] - edges["left"] for edges in widths.values()]
    assert max(member_widths) - min(member_widths) <= 0.01

    polymer_blocks = [
        panel.split("\\fill[polymer", 1)[1].split("\\node[qmark]", 1)[0]
        for panel in panels
    ]
    free_end_levels = [
        min(float(value) for value in re.findall(r",\s*(\d+\.\d+)\)", block))
        for block in polymer_blocks
    ]
    assert max(free_end_levels) - min(free_end_levels) <= 0.08


def test_fig5_reverse_bend_keeps_the_same_rounded_member_extent() -> None:
    tex = (FIXTURE / "fig5_cantilever_actuation_artifact_v2.tex").read_text(
        encoding="utf-8"
    )
    panel_a = tex.split("% Panel A", 1)[1].split("% Panel B", 1)[0]
    panel_c = tex.split("% Panel C", 1)[1].split("% Panel D", 1)[0]

    assert "rounded corners=0.35mm" in panel_a
    assert "rounded corners=0.45mm" in panel_a
    assert "rounded corners=0.35mm" in panel_c
    assert "rounded corners=0.45mm" in panel_c
    assert "(2.45,1.50)" in panel_a
    assert "(0.35,1.50)" in panel_c
