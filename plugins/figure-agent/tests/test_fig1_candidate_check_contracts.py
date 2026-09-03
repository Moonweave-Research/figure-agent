"""Regression contract for the Fig1 candidate's high-risk inspection net."""

from __future__ import annotations

from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIGURE_ROOT = PLUGIN_ROOT / "examples" / "fig1_updated_agent_redraw_v1"


def _spec() -> dict:
    return yaml.safe_load((FIGURE_ROOT / "spec.yaml").read_text(encoding="utf-8"))


def test_fig1_candidate_declares_high_risk_boundary_and_path_checks() -> None:
    spec = _spec()
    boundary_ids = {item["id"] for item in spec["text_boundary_checks"]}
    path_ids = {item["id"] for item in spec["label_path_proximity_checks"]}

    assert {
        "panel-c-title-band",
        "panel-c-energy-split",
        "panel-d-plot-header",
        "panel-e-apparatus-header",
        "panel-f-title-band",
    } <= boundary_ids
    assert {
        "panel-c-mobility-edge",
        "panel-c-thermal-escape",
        "panel-e-probe-shaft",
        "panel-e-vs-meter-lead",
        "panel-e-sample-transfer",
        "panel-e-grounded-substrate",
        "panel-f-observed-bend-arrow",
        "panel-f-ground-return",
    } <= path_ids
    assert len(boundary_ids) > 0
    assert len(path_ids) > 0


def test_fig1_candidate_briefing_and_semantic_assertion_ground_physics() -> None:
    briefing = (FIGURE_ROOT / "briefing.md").read_text(encoding="utf-8")
    spec = _spec()

    assert "## Physics invariants" in briefing
    assert spec["semantic_assertions"]
    assert spec["semantic_assertions"][0]["id"] == ("panel-c-mobility-edge-left-of-thermal-escape")


def test_fig1_current_candidate_pointer_binds_detector_evidence() -> None:
    pointer = yaml.safe_load(
        (FIGURE_ROOT / "review" / "current-candidate.json").read_text(encoding="utf-8")
    )
    evidence = pointer["evidence"]

    assert evidence["text_boundary_clash"] == "build/text_boundary_clash.json"
    assert evidence["label_path_proximity"] == "build/label_path_proximity.json"
