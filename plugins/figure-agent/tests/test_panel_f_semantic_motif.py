from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SNIPPET = PLUGIN_ROOT / "styles/snippets/panel-f-floating-cantilever.tex"
CONTRACT = PLUGIN_ROOT / "styles/snippets/panel-f-floating-cantilever.contract.yaml"
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
