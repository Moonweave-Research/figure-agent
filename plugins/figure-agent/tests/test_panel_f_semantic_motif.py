from hashlib import sha256
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SNIPPET = PLUGIN_ROOT / "styles/snippets/panel-f-floating-cantilever.tex"
CONTRACT = PLUGIN_ROOT / "styles/snippets/panel-f-floating-cantilever.contract.yaml"
TRANSFER_RECEIPT = (
    PLUGIN_ROOT / "styles/snippets/panel-f-floating-cantilever.transfer.yaml"
)
FIXTURES = (
    PLUGIN_ROOT
    / "examples/fig1_failure_first_panel_f_pilot/fig1_failure_first_panel_f_pilot.tex",
    PLUGIN_ROOT
    / "examples/fig1_overview_v5f_art_direction_001_vault"
    / "fig1_overview_v5f_art_direction_001_vault.tex",
)
MACRO = r"\PanelFFloatingCantilever"
INPUT = r"\input{snippets/panel-f-floating-cantilever.tex}"
SELECTOR_START = "% figure-agent:start panel_f.mechanism_scene"
SELECTOR_END = "% figure-agent:end panel_f.mechanism_scene"


def test_shared_motif_exposes_stable_semantic_anchors_without_fixture_names() -> None:
    source = SNIPPET.read_text(encoding="utf-8")

    assert rf"\newcommand{{{MACRO}}}[1]" in source
    assert r"\begin{scope}[shift={(#1)}]" in source
    for anchor in (
        "panelFFixedBoundary",
        "panelFFloatingCantilever",
        "panelFDrivenElectrode",
        "panelFSourceReturn",
        "panelFTrappedCharge",
    ):
        assert rf"\coordinate ({anchor})" in source
    assert "fig1_failure_first_panel_f_pilot" not in source
    assert "fig1_overview_v5f_art_direction_001_vault" not in source


def test_contract_declares_owned_roles_and_forbids_sample_ground() -> None:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))

    assert contract["motif"] == "panel-f-floating-cantilever"
    assert set(contract["owns"]) == {
        "fixed_mechanical_boundary",
        "floating_cantilever",
        "driven_electrode",
        "source_return",
        "gap_guides",
        "trapped_charge",
    }
    assert contract["connectors"] == {
        "mechanical_attachment": {
            "role": "mechanical",
            "connects": ["fixed_mechanical_boundary", "floating_cantilever"],
        },
        "electrode_drive": {
            "role": "electrical",
            "connects": ["voltage_source", "driven_electrode"],
        },
        "source_return": {
            "role": "electrical",
            "connects": ["voltage_source", "ground"],
        },
    }
    assert ["floating_cantilever", "ground"] in contract["forbidden_connections"]
    assert contract["objects"]["voltage_source"]["electrical_state"] == "driven"
    assert contract["objects"]["ground"]["electrical_state"] == "reference"
    assert contract["objects"]["floating_cantilever"]["electrical_state"] == "floating"
    assert contract["relations"]["trapped_charge_ownership"] == {
        "subject": "trapped_charge",
        "role": "owned_by",
        "object": "floating_cantilever",
    }


def test_snippet_excludes_fixture_local_force_and_composition_tokens() -> None:
    source = SNIPPET.read_text(encoding="utf-8")

    for forbidden in (
        "panelFCoulombRepulsionArrow",
        "Coulomb",
        "repulsion",
        "panelLetter",
        "figure-agent:start",
        "figure-agent:end",
        r"\resizebox",
        r"\begin{tikzpicture}",
    ):
        assert forbidden not in source


def test_both_fixtures_input_and_invoke_the_same_motif_inside_selector() -> None:
    for fixture in FIXTURES:
        source = fixture.read_text(encoding="utf-8")
        assert source.count(INPUT) == 1
        assert source.count(MACRO + "{") == 1
        assert source.count(SELECTOR_START) == 1
        assert source.count(SELECTOR_END) == 1

        selected = source.split(SELECTOR_START, 1)[1].split(SELECTOR_END, 1)[0]
        assert MACRO + "{" in selected
        assert "panelFCoulombRepulsionArrow" not in selected


def test_transfer_receipt_binds_sources_and_records_non_publication_evidence() -> None:
    receipt = yaml.safe_load(TRANSFER_RECEIPT.read_text(encoding="utf-8"))

    expected_shared_bindings = {
        str(path.relative_to(PLUGIN_ROOT)): "sha256:" + sha256(path.read_bytes()).hexdigest()
        for path in (SNIPPET, CONTRACT)
    }
    expected_bindings = {
        str(fixture.relative_to(PLUGIN_ROOT)): "sha256:" + sha256(fixture.read_bytes()).hexdigest()
        for fixture in FIXTURES
    }
    assert receipt["motif"] == "panel-f-floating-cantilever"
    assert receipt["shared_bindings"] == expected_shared_bindings
    assert receipt["source_bindings"] == expected_bindings
    assert receipt["compile_results"] == {
        path: "passed" for path in expected_bindings
    }
    comparison = receipt["crop_comparison"]
    assert {
        key: comparison[key]
        for key in (
            "status",
            "scope",
            "geometry",
            "absolute_error_pixels",
            "absolute_error_fraction",
        )
    } == {
        "status": "passed_with_fixture_local_differences",
        "scope": "same_family_reuse_only",
        "geometry": "1000x1100+3150+1650",
        "absolute_error_pixels": 4049,
        "absolute_error_fraction": 0.00368091,
    }
    expected_render_paths = {
        str(
            (fixture.parent / "build" / f"{fixture.stem}.png").relative_to(PLUGIN_ROOT)
        )
        for fixture in FIXTURES
    }
    assert set(comparison["render_bindings"]) == expected_render_paths
    assert set(comparison["crop_bindings"]) == {"pilot", "v5f"}
    for value in (
        *comparison["render_bindings"].values(),
        *comparison["crop_bindings"].values(),
        comparison["diff_sha256"],
    ):
        assert value.startswith("sha256:")
        assert len(value) == 71
    assert "1000x1100+3150+1650" in comparison["reproduce"]
    assert "compare -metric AE" in comparison["reproduce"]
    assert receipt["strict_review_evidence"] == "generated_not_passed"
    assert receipt["publication_acceptance"] == "not_claimed"
