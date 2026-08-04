from __future__ import annotations

import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig3_resistance_mechanism"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

from semantic_legibility_contract import (  # noqa: E402
    validate_semantic_legibility_contract,
)


def _yaml(name: str) -> dict:
    return yaml.safe_load((FIXTURE / name).read_text(encoding="utf-8"))


def test_fig3_requires_an_independent_coordinate_free_semantic_contract() -> None:
    spec = _yaml("spec.yaml")
    contract = _yaml("semantic_contract.yaml")
    result = validate_semantic_legibility_contract(
        contract,
        require_transfer_relations=True,
    )

    assert spec["semantic_contract_required"] is True
    assert result["publication_acceptance"] == "not_claimed"
    assert result["summary"] == {
        "object_role_count": 16,
        "visible_connector_count": 13,
        "forbidden_connector_count": 2,
        "label_ownership_count": 6,
        "floating_object_count": 0,
        "electrical_node_count": 0,
        "electrical_connection_count": 0,
        "panel_story_role_count": 3,
        "parallel_comparison_count": 0,
        "protected_relation_count": 11,
        "forbidden_implication_count": 8,
        "visual_review_required": True,
        "transfer_relations_required": True,
    }

    protected = set(result["protected_relations"])
    assert {
        "carrier_placement_encodes_temporal_sequence_not_spatial_drift",
        "capture_precedes_release_and_representative_slow_release_occupancy",
        "current_decay_is_qualitative_under_held_voltage",
        "current_decrease_implies_resistance_increase_under_held_voltage",
        "s60_and_s80_are_sulfur_weight_percent_sample_identities",
        "s80_support_is_broader_and_denser_only_as_a_qualitative_cue",
    } <= protected
    assert {
        "panel_a.carrier_polarity",
        "panel_a.net_spatial_carrier_drift",
        "panel_b.measured_transient_trace",
        "panel_b.fitted_numeric_exponent",
        "panel_c.sample_number_as_sulfur_atom_count",
        "panel_c.fitted_density_of_states",
        "panel_c.numeric_support_width_to_n_mapping",
        "panel_c.verified_trap_chemistry",
    } <= set(contract["forbidden_implications"])


def test_fig3_semantic_transfer_has_no_fig1_private_source_or_asset_import() -> None:
    source = (FIXTURE / "fig3_resistance_mechanism.tex").read_text(encoding="utf-8")
    contract_text = (FIXTURE / "semantic_contract.yaml").read_text(encoding="utf-8")

    assert source.index("% Panel A") < source.index("% Panel B") < source.index("% Panel C")
    assert "fig1" not in source.lower()
    assert "fig1" not in contract_text.lower()
    assert "\\input{" not in source
    assert "styles/snippets" not in source


def test_fig3_spec_exposes_panel_local_claims_without_layout_recipes() -> None:
    spec = _yaml("spec.yaml")
    panels = {panel["id"]: panel for panel in spec["panels"]}

    assert spec["final_size_contract"] == {
        "basis": "width_limited_nature_family_main_figure",
        "natural_size_mm": [169.35, 49.75],
        "target_width_mm": 180.0,
        "max_height_mm": 170.0,
        "min_print_font_pt": 5.0,
        "scale_basis": "width_limited",
        "font_floor_scope": "explicit_tex_fontsize_declarations",
    }

    for panel_id in ("A", "B", "C"):
        assert panels[panel_id]["semantic_claims"]
        assert panels[panel_id]["locked_invariants"]
    serialized = yaml.safe_dump(
        {
            panel_id: {
                "semantic_claims": panels[panel_id]["semantic_claims"],
                "locked_invariants": panels[panel_id]["locked_invariants"],
            }
            for panel_id in ("A", "B", "C")
        }
    )
    assert "bbox" not in serialized
    assert "coordinate" not in serialized
    assert "tikz" not in serialized.lower()

    source = (FIXTURE / "fig3_resistance_mechanism.tex").read_text(encoding="utf-8")
    assert r"\fontsize{4.8}{5.8}\selectfont" in source
    assert r"\fontsize{4.2}{5.0}\selectfont" not in source
