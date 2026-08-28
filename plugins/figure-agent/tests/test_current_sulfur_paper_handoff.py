from __future__ import annotations

import re
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HANDOFF = PLUGIN_ROOT / "docs/current-sulfur-paper-figure-state.md"
PLAN_MAP = PLUGIN_ROOT / "docs/paper_figure_map.yaml"


def _plan_map() -> dict[str, object]:
    payload = yaml.safe_load(PLAN_MAP.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_handoff_describes_every_machine_resolved_main_figure() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    figures = _plan_map()["figures"]
    assert isinstance(figures, dict)

    for figure, entry in figures.items():
        assert isinstance(entry, dict)
        assert figure.casefold() in text.casefold()
        if entry["status"] == "active_candidate":
            fixture = entry["fixture"]
            assert isinstance(fixture, str)
            assert fixture in text
        else:
            assert entry["status"] == "planned_missing"
            assert entry["slot_status"] == "fixed"
            assert "fixed main slot" in text


def test_candidate_map_declares_external_paper_artifact_authority() -> None:
    plan_map = _plan_map()
    registry = plan_map["paper_artifact_registry"]
    assert isinstance(registry, dict)
    assert plan_map["authority_scope"] == "figure_agent_candidate_bindings"
    assert registry["system"] == "researchos"
    assert registry["registry"] == "docs/figure_set/FIGURE_REGISTRY.yaml"
    text = HANDOFF.read_text(encoding="utf-8")
    assert "FIGURE_REGISTRY.yaml" in text


def test_handoff_contains_durable_experiment_contracts() -> None:
    text = HANDOFF.read_text(encoding="utf-8")

    for required in (
        "gridless, two-terminal high-voltage",
        "moved manually",
        "grounded conductive substrate",
        "induction-type electrostatic surface voltmeter",
        "not a Kelvin probe or KPFM schematic",
        "Actuation charge",
        "OFF / float",
        "Reversed drive",
        "Maxwell attraction",
        "q_tr E",
    ):
        assert required in text


def test_handoff_does_not_freeze_transient_repository_state() -> None:
    text = HANDOFF.read_text(encoding="utf-8")

    forbidden_patterns = (
        r"/Users/",
        r"\.worktrees/",
        r"\bbranch:\s",
        r"\bhead:\s",
        r"source_sha256",
        r"sha256:[0-9a-f]+",
        r"checked=\d+",
        r"blocking_total=\d+",
        r"render=FRESH",
        r"Updated:",
        r"next session",
    )
    for pattern in forbidden_patterns:
        assert re.search(pattern, text, flags=re.IGNORECASE) is None


def test_historical_cantilever_fixtures_are_non_main_in_machine_map() -> None:
    plan_map = _plan_map()
    non_main = plan_map["non_main"]
    assert isinstance(non_main, dict)
    classified = {
        fixture: classification
        for classification, fixtures in non_main.items()
        for fixture in fixtures
    }

    assert classified["fig5_actuation_mechanism"] == "regression"
    assert classified["fig5_cantilever_mechanism_v1"] == "superseded"
    assert classified["fig3_floating_clip_protocol"] == "si"


def test_only_current_three_authoring_baselines_are_active() -> None:
    plan_map = _plan_map()
    figures = plan_map["figures"]
    assert isinstance(figures, dict)

    active_fixtures = {
        entry["fixture"]
        for entry in figures.values()
        if isinstance(entry, dict) and entry["status"] == "active_candidate"
    }
    assert active_fixtures == {
        "fig1_updated_agent_redraw_v1",
        "fig2_charge_transport_mechanism",
        "fig5_cantilever_actuation_artifact_v2",
    }
    assert figures["fig3"]["status"] == "planned_missing"
    assert figures["fig4"]["status"] == "planned_missing"
    assert figures["fig3"]["slot_status"] == "fixed"
    assert figures["fig3"]["authoring_scope"] == "external_quantitative_data"
    assert figures["fig3"]["assembly_state"] == "external_full_figure_ready"
    assert figures["fig4"]["slot_status"] == "fixed"
    assert (
        figures["fig4"]["evidence_status"]
        == "run_validated_aggregate_pipeline_pending"
    )
    assert figures["fig4"]["assembly_state"] == "external_full_figure_pending"
    assert figures["fig1"]["fixture_scope"] == "full_figure_candidate"
    assert figures["fig2"]["fixture_scope"] == "panel_a_schematic_candidate"
    assert figures["fig5"]["fixture_scope"] == "mechanism_schematic_candidate"

    non_main = plan_map["non_main"]
    assert isinstance(non_main, dict)
    assert "fig4_trap_energy_diagram" in non_main["superseded"]


def test_named_current_schematic_baseline_matches_active_bindings_and_context() -> None:
    plan_map = _plan_map()
    baseline = plan_map["current_schematic_baseline"]
    assert isinstance(baseline, dict)
    assert baseline["id"] == "pair001-main-schematics"
    assert baseline["aesthetic_context"] == "nc-main-text-series"
    assert baseline["fixtures"] == [
        "fig1_updated_agent_redraw_v1",
        "fig2_charge_transport_mechanism",
        "fig5_cantilever_actuation_artifact_v2",
    ]

    figures = plan_map["figures"]
    assert isinstance(figures, dict)
    active = {
        entry["fixture"]
        for entry in figures.values()
        if isinstance(entry, dict) and entry["status"] == "active_candidate"
    }
    assert set(baseline["fixtures"]) == active

    context_path = (
        PLUGIN_ROOT
        / "examples"
        / "_paper_aesthetic_contexts"
        / f"{baseline['aesthetic_context']}.yaml"
    )
    context = yaml.safe_load(context_path.read_text(encoding="utf-8"))
    assert isinstance(context, dict)
    context_fixtures = {
        role["fixture"]
        for role in context["figure_roles"]
        if isinstance(role, dict) and "fixture" in role
    }
    assert set(baseline["fixtures"]) <= context_fixtures

    for fixture in baseline["fixtures"]:
        spec = yaml.safe_load(
            (PLUGIN_ROOT / "examples" / fixture / "spec.yaml").read_text(encoding="utf-8")
        )
        assert spec["paper_aesthetic_context"] == baseline["aesthetic_context"]


def test_fixed_external_main_slots_are_not_reported_as_optional_plans() -> None:
    import sys

    checks_dir = PLUGIN_ROOT / "scripts/checks"
    sys.path.insert(0, str(checks_dir))
    try:
        import check_plan_consistency

        report = check_plan_consistency.build_report(PLUGIN_ROOT / "examples", PLAN_MAP)
    finally:
        sys.path.remove(str(checks_dir))

    fixed = {
        finding["figure"]: finding
        for finding in report["findings"]
        if finding["code"] == "fixed_main_slot_missing_fixture"
    }
    assert set(fixed) == {"fig3", "fig4"}
    assert fixed["fig3"]["evidence_status"] == "external_canonical_artifact_ready"
    assert (
        fixed["fig4"]["evidence_status"]
        == "run_validated_aggregate_pipeline_pending"
    )
