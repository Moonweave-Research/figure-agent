from __future__ import annotations

import hashlib
import json
from pathlib import Path

import authoring_execution_packet
import authoring_execution_preflight
import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples/fig1_composition_comparison_v1"
ATTEMPT = FIXTURE / "review/failure-first/comparable-v1"
PAIR_EQUAL_FIELDS = (
    "model_id",
    "execution_cwd",
    "budget_contract",
    "blank_start",
    "mandatory_source_requirements",
    "style_lock_authoring_requirements",
    "allowed_repository_read_paths",
    "feedback_rounds",
    "manual_repairs",
    "forbidden_import_classes",
    "publication_acceptance",
    "visual_assets",
)
INTERVENTION_FIELDS = ("shape_profile", "composition_profile")


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _frozen_pair_snapshot() -> tuple[
    dict[str, dict[str, object]], dict[str, object]
]:
    """Compare only the immutable packet, prompt, and historical receipt bytes."""
    packet_paths = {
        "control": ATTEMPT / "free_composition_packet.json",
        "treatment": ATTEMPT / "assisted_composition_packet.json",
    }
    prompt_paths = {
        "control": ATTEMPT / "free_composition_prompt.md",
        "treatment": ATTEMPT / "assisted_composition_prompt.md",
    }
    packets: dict[str, dict[str, object]] = {}
    for arm, packet_path in packet_paths.items():
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        prompt_bytes = prompt_paths[arm].read_bytes()
        assert packet["schema"] == authoring_execution_packet.SCHEMA
        assert packet["packet_sha256"] == (
            authoring_execution_packet.canonical_packet_sha256(packet)
        )
        prompt = packet["prompt"]
        assert isinstance(prompt, dict)
        assert prompt["utf8"].encode("utf-8") == prompt_bytes
        assert prompt["sha256"] == _sha256_bytes(prompt_bytes)
        assert isinstance(packet["execution_cwd"], str)
        assert isinstance(packet["output_path"], str)
        assert packet["repository_output_path"] == (
            Path(packet["execution_cwd"]) / packet["output_path"]
        ).as_posix()
        assert prompt["utf8"].count(
            f"- Write exactly one new source to [{packet['repository_output_path']}]."
        ) == 1
        packets[arm] = packet

    assert len(set(packet_paths.values())) == len(packet_paths)
    assert len(set(prompt_paths.values())) == len(prompt_paths)
    assert len({packet["output_path"] for packet in packets.values()}) == len(packets)

    control = packets["control"]
    treatment = packets["treatment"]
    for field in PAIR_EQUAL_FIELDS:
        assert control[field] == treatment[field]
    control_context = control["context_pack"]
    treatment_context = treatment["context_pack"]
    assert isinstance(control_context, dict)
    assert isinstance(treatment_context, dict)
    assert control_context["schema"] == treatment_context["schema"]
    assert control_context["base_sha256"] == treatment_context["base_sha256"]
    differing_interventions = {
        field
        for field in INTERVENTION_FIELDS
        if control.get(field) != treatment.get(field)
    }
    assert differing_interventions == {"composition_profile"}

    receipt = json.loads(
        (ATTEMPT / "preflight_result.json").read_text(encoding="utf-8")
    )
    assert receipt["schema"] == "figure-agent.authoring-execution-preflight.v1"
    assert receipt["decision"] == "pass"
    assert receipt["filesystem_read_isolation"] == "unavailable"
    assert receipt["intervention_field"] == "composition_profile"
    for arm, packet in packets.items():
        expected_output_root = Path(packet["output_path"]).parent
        expected_condition = {
            "packet_path": (
                expected_output_root / packet_paths[arm].name
            ).as_posix(),
            "packet_sha256": packet["packet_sha256"],
            "prompt_path": (
                expected_output_root / prompt_paths[arm].name
            ).as_posix(),
            "prompt_sha256": packet["prompt"]["sha256"],
            "output_path": packet["output_path"],
        }
        assert receipt[arm] == expected_condition
    return packets, receipt


def test_common_input_preserves_scientific_coverage_without_layout_answer() -> None:
    spec = yaml.safe_load((FIXTURE / "spec.yaml").read_text(encoding="utf-8"))
    briefing = (FIXTURE / "briefing.md").read_text(encoding="utf-8")

    assert [panel["id"] for panel in spec["panels"]] == list("ABCDEF")
    assert "visual hero" not in (FIXTURE / "spec.yaml").read_text(encoding="utf-8")
    assert "sole hero" not in briefing
    assert "No grid, hero panel, panel rectangle, coordinate" in briefing
    assert spec["publication_acceptance"] == "not_claimed"


def test_packets_are_base_equal_and_differ_only_by_composition_intervention() -> None:
    packets, preflight = _frozen_pair_snapshot()
    free = packets["control"]
    assisted = packets["treatment"]

    assert free["composition_profile"] is None
    assert assisted["composition_profile"]["policy"] == "preserve_llm_composition"
    assert free["shape_profile"] == assisted["shape_profile"]
    assert free["publication_acceptance"] == "not_claimed"
    assert assisted["publication_acceptance"] == "not_claimed"
    assert preflight["decision"] == "pass"


def test_historical_pair_is_stale_under_the_current_canonical_preflight() -> None:
    """The frozen pass receipt is not a successful current-environment preflight."""
    _, historical_receipt = _frozen_pair_snapshot()
    assert historical_receipt["decision"] == "pass"

    with pytest.raises(
        authoring_execution_preflight.AuthoringExecutionPreflightError,
        match=r"^visual asset byte drift: styles/snippets/INDEX\.yaml$",
    ):
        authoring_execution_preflight.preflight_authoring_pair(
            ATTEMPT / "free_composition_packet.json",
            ATTEMPT / "assisted_composition_packet.json",
        )


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
