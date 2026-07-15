from __future__ import annotations

import hashlib
import json
from pathlib import Path

import authoring_execution_preflight
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples/fig1_composition_comparison_v1"
ATTEMPT = FIXTURE / "review/failure-first/comparable-v1"


def test_common_input_preserves_scientific_coverage_without_layout_answer() -> None:
    spec = yaml.safe_load((FIXTURE / "spec.yaml").read_text(encoding="utf-8"))
    briefing = (FIXTURE / "briefing.md").read_text(encoding="utf-8")

    assert [panel["id"] for panel in spec["panels"]] == list("ABCDEF")
    assert "visual hero" not in (FIXTURE / "spec.yaml").read_text(encoding="utf-8")
    assert "sole hero" not in briefing
    assert "No grid, hero panel, panel rectangle, coordinate" in briefing
    assert spec["publication_acceptance"] == "not_claimed"


def test_packets_are_base_equal_and_differ_only_by_composition_intervention() -> None:
    free = json.loads(
        (ATTEMPT / "free_composition_packet.json").read_text(encoding="utf-8")
    )
    assisted = json.loads(
        (ATTEMPT / "assisted_composition_packet.json").read_text(encoding="utf-8")
    )

    for field in (
        "model_id",
        "budget_contract",
        "blank_start",
        "visual_assets",
        "allowed_repository_read_paths",
        "feedback_rounds",
        "manual_repairs",
    ):
        assert free[field] == assisted[field]
    assert free["context_pack"]["base_sha256"] == assisted["context_pack"][
        "base_sha256"
    ]
    assert free["composition_profile"] is None
    assert assisted["composition_profile"]["policy"] == "preserve_llm_composition"
    assert free["shape_profile"] == assisted["shape_profile"]
    assert free["publication_acceptance"] == "not_claimed"
    assert assisted["publication_acceptance"] == "not_claimed"

    preflight = authoring_execution_preflight.preflight_authoring_pair(
        ATTEMPT / "free_composition_packet.json",
        ATTEMPT / "assisted_composition_packet.json",
    )
    assert preflight["decision"] == "pass"
    assert preflight["intervention_field"] == "composition_profile"


def test_prompts_do_not_prescribe_coordinates_or_fixed_panel_rectangles() -> None:
    free = (ATTEMPT / "free_composition_prompt.md").read_text(encoding="utf-8")
    assisted = (ATTEMPT / "assisted_composition_prompt.md").read_text(
        encoding="utf-8"
    )

    assert "No optional composition profile selected" in free
    assert "do not default to equal-size panels" in assisted
    assert "no coordinates or panel rectangles are prescribed" in assisted
    assert "publication_acceptance: not_claimed" in free
    assert "publication_acceptance: not_claimed" in assisted


def test_first_pass_artifacts_and_machine_evidence_are_bound() -> None:
    contract = yaml.safe_load(
        (ATTEMPT / "comparison_contract.yaml").read_text(encoding="utf-8")
    )

    for arm in ("free_composition", "assisted_composition"):
        artifact = contract["artifacts"][arm]
        for field, path in (
            ("packet_sha256", ATTEMPT / f"{arm}_packet.json"),
            ("source_sha256", ATTEMPT / f"{arm}_generated.tex"),
            (
                "png_sha256",
                ATTEMPT
                / "review"
                / ("option-b.png" if arm == "free_composition" else "option-a.png"),
            ),
        ):
            assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact[field]

        collision = json.loads(
            (ATTEMPT / f"{arm}_collision.json").read_text(encoding="utf-8")
        )
        undeclared = json.loads(
            (ATTEMPT / f"{arm}_undeclared_geometry.json").read_text(
                encoding="utf-8"
            )
        )
        observation = contract["machine_observations"][arm]
        assert collision["total"] == observation["text_collisions"]
        assert undeclared["total"] == observation["undeclared_geometry_candidates"]
        for report_name, observation_name in (
            ("visual_clash", "visual_clash_candidates"),
            ("text_boundary_clash", "text_boundary_clashes"),
            ("label_path_proximity", "label_path_proximity_candidates"),
        ):
            report = json.loads(
                (ATTEMPT / f"{arm}_{report_name}.json").read_text(
                    encoding="utf-8"
                )
            )
            assert report["total"] == observation[observation_name]

    assert contract["comparison_validity"]["status"] == (
        "invalid_for_causal_composition_claim"
    )
    assert contract["machine_observations"]["assisted_composition"][
        "missing_required_objects"
    ] == ["panel_e.ispd_probe"]
    semantic_review = yaml.safe_load(
        (ATTEMPT / "semantic_coverage_review.yaml").read_text(encoding="utf-8")
    )
    assert semantic_review["arms"]["free_composition"]["status"] == "pass"
    assert semantic_review["arms"]["assisted_composition"]["status"] == "fail"
    assert semantic_review["comparison_eligibility"] == "fail"
    assert contract["human_review"]["verdict"] == "pending"
    assert contract["human_review"]["can_establish_causal_effect"] is False
    assert contract["publication_acceptance"] == "not_claimed"
    physics = json.loads(
        (ATTEMPT / "fixture_physics_grounding.json").read_text(encoding="utf-8")
    )
    assert physics["status"] == contract["machine_observations"][
        "fixture_physics_grounding"
    ]


def test_blind_review_surface_contains_both_first_pass_renders() -> None:
    review = (ATTEMPT / "review/index.html").read_text(encoding="utf-8")

    assert "Option A" in review
    assert "Option B" in review
    assert 'src="option-a.png"' in review
    assert 'src="option-b.png"' in review
    assert "assisted_composition" not in review
    assert "free_composition" not in review
    assert "weakly masked first-pass pair" in review
    assert "invalid for a causal effectiveness claim" in review
