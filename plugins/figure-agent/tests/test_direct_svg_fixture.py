from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig1_direct_svg_cleanroom_baseline"
DENIED_SOURCE_FAMILIES = {
    "tex",
    "whole_figure_svg",
    "candidate_patch",
    "experience_log",
    "illustration_grammar",
}
EXPECTED_BUDGETS = {
    "utility": {"cycles": 3, "wall_minutes_per_panel": 30},
    "ceiling": {"cycles": 8, "wall_minutes_per_panel": 120},
}


def _load(relative: str) -> dict[str, Any]:
    loaded = yaml.safe_load((FIXTURE / relative).read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def test_fixture_binds_immutable_reference_source_and_crops() -> None:
    receipt = _load("reference/source-receipt.yaml")
    crop_manifest = _load("reference/crop-authority.yaml")

    benchmark = FIXTURE / "reference" / receipt["snapshot"]["path"]
    assert receipt["source"]["sha256"] == receipt["snapshot"]["sha256"]
    assert receipt["snapshot"]["sha256"] == _sha256(benchmark)
    assert crop_manifest["source"]["sha256"] == _sha256(benchmark)
    for crop in crop_manifest["crops"].values():
        assert crop["sha256"] == _sha256(FIXTURE / "reference" / crop["output"])
    assert receipt["publication_acceptance"] == "not_claimed"
    assert crop_manifest["publication_acceptance"] == "not_claimed"


def test_fixture_is_honestly_blocked_on_independent_semantic_packet() -> None:
    state = _load("contract/experiment-state.yaml")

    assert state["semantic_packet_authority"] == {
        "prepared_by_current_session": False,
        "implementation_details_observed": False,
        "preparer": None,
        "prepared_at": None,
        "sha256": None,
    }
    assert state["run_state"] == "blocked_pending_independent_semantic_packet"
    assert state["publication_acceptance"] == "not_claimed"


def test_fixture_binds_a_licensed_font_and_isolated_fontconfig() -> None:
    receipt = _load("contract/font-receipt.yaml")
    font = FIXTURE / "contract" / receipt["font"]["path"]
    license_path = FIXTURE / "contract" / receipt["license"]["path"]
    fontconfig = FIXTURE / "contract" / receipt["fontconfig"]["path"]

    assert receipt["font"]["family"] == "Latin Modern Sans"
    assert receipt["font"]["sha256"] == _sha256(font)
    assert receipt["license"]["id"] == "GUST-FONT-LICENSE"
    assert receipt["license"]["sha256"] == _sha256(license_path)
    assert receipt["fontconfig"]["sha256"] == _sha256(fontconfig)
    fontconfig_text = fontconfig.read_text(encoding="utf-8")
    assert "fonts" in fontconfig_text
    assert "/System/Library/Fonts" not in fontconfig_text
    assert "/usr/share/fonts" not in fontconfig_text
    assert receipt["publication_acceptance"] == "not_claimed"


def test_test_a_and_b_templates_have_separate_boundaries_and_output_roots() -> None:
    test_a = _load("packets/test-a-reconstruction.template.yaml")
    test_b = _load("packets/test-b-synthesis.template.yaml")

    for packet, kind in ((test_a, "reconstruction"), (test_b, "synthesis")):
        assert packet["schema"] == "figure-agent.direct-svg-packet-template.v1"
        assert packet["target_packet_schema"] == "figure-agent.direct-svg-packet.v1"
        assert packet["test_kind"] == kind
        assert set(packet["panels"]) == {"C", "F"}
        assert set(packet["denied_source_families"]) == DENIED_SOURCE_FAMILIES
        assert packet["budgets"] == EXPECTED_BUDGETS
        assert packet["path_base"] == "fixture_root"
        assert packet["runnable"] is False
        assert packet["blocked_reason"] == "independent_semantic_packet_missing"
        assert packet["publication_acceptance"] == "not_claimed"

    assert test_a["output_root"] != test_b["output_root"]
    assert (FIXTURE / test_a["output_root"] / "run-state.yaml").is_file()
    assert (FIXTURE / test_b["output_root"] / "run-state.yaml").is_file()
    assert {item["role"] for item in test_a["allowed_inputs"]} >= {
        "panel_c_target_crop",
        "panel_f_target_crop",
        "licensed_font",
    }


def test_test_b_template_contains_no_target_or_geometry_derivative_input() -> None:
    test_b = _load("packets/test-b-synthesis.template.yaml")

    for item in test_b["allowed_inputs"]:
        role = item["role"].lower()
        path = str(item.get("path") or "").lower()
        assert "target" not in role
        assert "geometry" not in role
        assert "panel-c.png" not in path
        assert "panel-f.png" not in path
    assert test_b["reference_pixels_available"] is False
    assert test_b["reference_hashes_available"] is False
    assert test_b["geometry_derivatives_available"] is False


def test_run_and_review_states_cannot_claim_machine_or_publication_acceptance() -> None:
    for relative in (
        "runs/test-a/run-state.yaml",
        "runs/test-b/run-state.yaml",
        "review/review-state.yaml",
    ):
        state = _load(relative)
        assert state["state"].startswith("blocked_")
        assert state["publication_acceptance"] == "not_claimed"
