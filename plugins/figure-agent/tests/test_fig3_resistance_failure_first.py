from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

import authoring_context_pack  # noqa: E402
from failure_ablation import evaluate_ablation  # noqa: E402

FIXTURE = PLUGIN_ROOT / "examples" / "fig3_resistance_mechanism"
REVIEW = FIXTURE / "review" / "failure-first"
PACKET = REVIEW / "input_packet.yaml"
BOUNDARY = REVIEW / "semantic_object_relation_boundary.yaml"
RENDER_RECEIPT = REVIEW / "render_receipt.yaml"
RAW_RUN = REVIEW / "raw.yaml"
RAW_PROMPT = REVIEW / "raw_authoring_prompt.md"
RAW_SOURCE = REVIEW / "raw_generated.tex"
RAW_MODEL_CONTRACT = REVIEW / "model_contract.yaml"
RAW_BUDGET_CONTRACT = REVIEW / "budget_contract.yaml"
RAW_AUTHORITY_PACKET = REVIEW / "raw_authority_packet.yaml"
RAW_RENDER_RECEIPT = REVIEW / "raw_render_receipt.yaml"
RAW_SELECTOR_REGISTRY = REVIEW / "raw_selector_registry.yaml"
STYLE_CONTROL_RUN = REVIEW / "style_control.yaml"
STYLE_CONTROL_SOURCE = REVIEW / "style_control_generated.tex"
STYLE_CONTROL_RENDER_RECEIPT = REVIEW / "style_control_render_receipt.yaml"
VERIFIED_RUN = REVIEW / "verified.yaml"
VERIFIED_SOURCE = REVIEW / "verified_generated.tex"
VERIFIED_RENDER_RECEIPT = REVIEW / "verified_render_receipt.yaml"
VERIFIED_SELECTOR_REGISTRY = REVIEW / "verified_selector_registry.yaml"
VERIFIED_ATTEMPT1_SOURCE = REVIEW / "verified_attempt1_style_path_failed.tex"
VERIFIED_ATTEMPT1_RECORD = REVIEW / "verified_attempt1_style_path_failed.yaml"
REPAIRED_ATTEMPT = REVIEW / "repaired_layout_lane_attempt.yaml"
REPAIRED_AUTHORITY_PACKET = REVIEW / "repaired_authority_packet.yaml"
REPAIRED_PROMPT = REVIEW / "repaired_authoring_prompt.md"
REPAIRED_SOURCE = REVIEW / "repaired_generated.tex"
REPAIRED_RENDER_RECEIPT = REVIEW / "repaired_render_receipt.yaml"
REPAIRED_REGION_CONTRACT = REVIEW / "repaired_posthoc_region_contract.yaml"
REPAIRED_REGION_REPORT = REVIEW / "repaired_posthoc_region_report.json"
REPAIRED_REGION_EVALUATION = REVIEW / "repaired_posthoc_region_evaluation.yaml"
REGION_GUIDED_ATTEMPT = REVIEW / "region_guided_attempt.yaml"
REGION_GUIDED_AUTHORITY_PACKET = REVIEW / "region_guided_authority_packet.yaml"
REGION_GUIDED_PROMPT = REVIEW / "region_guided_authoring_prompt.md"
REGION_GUIDED_SOURCE = REVIEW / "region_guided_generated.tex"
REGION_GUIDED_RENDER_RECEIPT = REVIEW / "region_guided_render_receipt.yaml"
REGION_GUIDED_REVIEW = REVIEW / "region_guided_adversarial_review.yaml"
REGION_GUIDED_TEXT_CONTRACT = REVIEW / "region_guided_text_inventory_contract.yaml"
REGION_GUIDED_TEXT_REPORT = REVIEW / "region_guided_text_inventory_report.json"
REGION_GUIDED_LABEL_OWNERSHIP_CONTRACT = (
    REVIEW / "region_guided_label_ownership_contract.yaml"
)
REGION_GUIDED_LABEL_OWNERSHIP_REPORT = (
    REVIEW / "region_guided_label_ownership_report.json"
)
REGION_GUIDED_MUTUAL_CLEARANCE_CONTRACT = (
    REVIEW / "region_guided_mutual_clearance_contract.yaml"
)
REGION_GUIDED_MUTUAL_CLEARANCE_REPORT = (
    REVIEW / "region_guided_mutual_clearance_report.json"
)
SHAPE_PROFILE = FIXTURE / "shape_profile_panel_b.yaml"
SHAPE_MODEL_CONTRACT = REVIEW / "shape_experiment_model_contract.yaml"
SHAPE_BUDGET_CONTRACT = REVIEW / "shape_experiment_budget_contract.yaml"
SHAPE_BLANK_START = REVIEW / "shape_experiment_blank_start.txt"
SHAPE_CONTROL_PACKET = REVIEW / "shape_experiment_control_packet.yaml"
SHAPE_TREATMENT_OVERLAY = REVIEW / "shape_profile_treatment_overlay.yaml"
SHAPE_CONTROL_PROMPT = REVIEW / "shape_control_authoring_prompt.md"
SHAPE_PROFILED_PROMPT = REVIEW / "shape_profiled_authoring_prompt.md"
SHAPE_CONTROL_SOURCE = REVIEW / "shape_control_generated.tex"
SHAPE_PROFILED_SOURCE = REVIEW / "shape_profiled_generated.tex"
SHAPE_COMPARISON = REVIEW / "shape_profile_comparison.yaml"
SHAPE_ADVERSARIAL_REVIEW = REVIEW / "shape_profile_adversarial_review.yaml"
SHAPE_HANDOFF = REVIEW / "shape_profile_handoff.md"
EXECUTION_BINDING_V1 = REVIEW / "execution-binding-v1"
EXECUTION_BINDING = REVIEW / "execution-binding-v2"
EXECUTION_BINDING_V4 = REVIEW / "execution-binding-v4"
EXECUTION_BINDING_V5 = REVIEW / "execution-binding-v5"
EXECUTION_BINDING_V6 = REVIEW / "execution-binding-v6"
EXECUTION_SCAFFOLD_EVALUATION = REVIEW / "execution-scaffold-evaluation-v1"
COMPARABLE_V1 = REVIEW / "comparable-v1"
COMPARISON_CONTRACT = COMPARABLE_V1 / "comparison_contract.yaml"
COMPARABLE_V2 = REVIEW / "comparable-v2"
COMPARISON_CONTRACT_V2 = COMPARABLE_V2 / "comparison_contract.yaml"
AUTHORITY_MANIFEST_V2 = REVIEW / "authority_manifest_v2.yaml"
CURRENT_RENDER_REVIEW_SCAFFOLD = REVIEW / "current_render_review_scaffold_v1.yaml"
EXECUTION_REPAIR_V13 = REVIEW / "execution-repair-v13"
EXECUTION_REPAIR_V14 = REVIEW / "execution-repair-v14"
EXECUTION_REPAIR_V15 = REVIEW / "execution-repair-v15"
EXECUTION_REPAIR_V16 = REVIEW / "execution-repair-v16"
EXECUTION_REPAIR_V17 = REVIEW / "execution-repair-v17"
EXECUTION_REPAIR_V18 = REVIEW / "execution-repair-v18"
EXECUTION_REPAIR_V19 = REVIEW / "execution-repair-v19"
EXECUTION_REPAIR_V20 = REVIEW / "execution-repair-v20"
V20_HUMAN_FINDINGS = EXECUTION_REPAIR_V20 / "human_findings.yaml"
EXECUTION_REPAIR_V21 = REVIEW / "execution-repair-v21"
EXECUTION_REPAIR_V22 = REVIEW / "execution-repair-v22"
EXECUTION_REPAIR_V23 = REVIEW / "execution-repair-v23"
EXECUTION_REPAIR_V24 = REVIEW / "execution-repair-v24"
EXECUTION_REPAIR_V25 = REVIEW / "execution-repair-v25"
EXECUTION_REPAIR_V26 = REVIEW / "execution-repair-v26"
EXECUTION_REPAIR_V27 = REVIEW / "execution-repair-v27"
EXECUTION_REPAIR_V28 = REVIEW / "execution-repair-v28"
EXECUTION_REPAIR_V29 = REVIEW / "execution-repair-v29"
EXECUTION_REPAIR_V30 = REVIEW / "execution-repair-v30"
EXECUTION_REPAIR_V31 = REVIEW / "execution-repair-v31"
EXECUTION_REPAIR_V32 = REVIEW / "execution-repair-v32"
EXECUTION_REPAIR_V33 = REVIEW / "execution-repair-v33"
EXECUTION_REPAIR_V34 = REVIEW / "execution-repair-v34"
EXECUTION_REPAIR_V35 = REVIEW / "execution-repair-v35"
EXECUTION_REPAIR_V36 = REVIEW / "execution-repair-v36"
EXECUTION_REPAIR_V37 = REVIEW / "execution-repair-v37"
EXECUTION_REPAIR_V38 = REVIEW / "execution-repair-v38"
EXECUTION_REPAIR_V39 = REVIEW / "execution-repair-v39"
EXECUTION_REPAIR_V40 = REVIEW / "execution-repair-v40"
EXECUTION_REPAIR_V41 = REVIEW / "execution-repair-v41"
EXECUTION_REPAIR_V42 = REVIEW / "execution-repair-v42"
EXECUTION_REPAIR_V43 = REVIEW / "execution-repair-v43"
EXECUTION_REPAIR_V44 = REVIEW / "execution-repair-v44"
EXECUTION_REPAIR_V45 = REVIEW / "execution-repair-v45"
EXECUTION_REPAIR_V46 = REVIEW / "execution-repair-v46"
EXECUTION_REPAIR_V47 = REVIEW / "execution-repair-v47"
EXECUTION_REPAIR_V48 = REVIEW / "execution-repair-v48"
EXECUTION_REPAIR_V49 = REVIEW / "execution-repair-v49"
EXECUTION_REPAIR_V50 = REVIEW / "execution-repair-v50"
EXECUTION_REPAIR_V53 = REVIEW / "execution-repair-v53"
EXECUTION_REPAIR_V56 = REVIEW / "execution-repair-v56"
EXECUTION_REPAIR_V60 = REVIEW / "execution-repair-v60"
EXECUTION_REPAIR_V61 = REVIEW / "execution-repair-v61"
EXECUTION_REPAIR_V62 = REVIEW / "execution-repair-v62"
EXECUTION_REPAIR_V63 = REVIEW / "execution-repair-v63"
EXECUTION_REPAIR_V64 = REVIEW / "execution-repair-v64"
EXECUTION_REPAIR_V66 = REVIEW / "execution-repair-v66"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _scope_extension_paths() -> list[Path]:
    """Return the complete, numerically ordered scope-extension lineage."""
    paths = list(REVIEW.glob("scope_extension_v*.yaml"))
    versions_by_path: dict[Path, int] = {}
    for path in paths:
        match = re.fullmatch(r"scope_extension_v(\d+)\.yaml", path.name)
        assert match is not None, f"unexpected scope-extension filename: {path.name}"
        versions_by_path[path] = int(match.group(1))
    ordered_paths = sorted(paths, key=versions_by_path.__getitem__)
    versions = [versions_by_path[path] for path in ordered_paths]
    assert versions == list(range(2, versions[-1] + 1))
    return ordered_paths


def test_fig3_exact_repairs_do_not_mistake_text_text_zero_for_structural_pass() -> None:
    v13 = json.loads(
        (EXECUTION_REPAIR_V13 / "structural_gate.json").read_text(encoding="utf-8")
    )
    v14 = json.loads(
        (EXECUTION_REPAIR_V14 / "execution_review.json").read_text(encoding="utf-8")
    )
    v15 = json.loads(
        (EXECUTION_REPAIR_V15 / "structural_gate.json").read_text(encoding="utf-8")
    )
    v15_review = json.loads(
        (EXECUTION_REPAIR_V15 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert v13["state"] == "failed"
    assert v13["structural_pass"] is False
    assert v13["blocking_counts"] == {
        "semantic_path_crossing": 4,
        "text_on_path_or_fill": 9,
        "text_text": 0,
    }
    assert v14["decision"] == "failed_exact_repair"
    assert v14["semantic_path_crossing_after"] == 3
    assert v15["state"] == "failed"
    assert v15["blocking_counts"] == {
        "semantic_path_crossing": 2,
        "text_on_path_or_fill": 9,
        "text_text": 0,
    }
    assert v15_review["repair_result"] == (
        "upper content and increases crossings removed"
    )
    assert v15_review["band_shape_authority"] == (
        "blocked_pending_physics_math_review"
    )
    assert v15_review["publication_acceptance"] == "not_claimed"


def test_fig3_v16_removes_exact_semantic_arrow_crossings_without_claiming_acceptance() -> None:
    gate = json.loads(
        (EXECUTION_REPAIR_V16 / "structural_gate.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V16 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert gate["blocking_counts"]["semantic_path_crossing"] == 0
    assert gate["state"] == "failed"
    assert gate["structural_pass"] is False
    assert review["repair_result"] == "lower breadth and distribution crossings removed"
    assert review["remaining_priority"] == "panel_a_label_and_path_collisions"
    assert review["band_shape_authority"] == "blocked_pending_physics_math_review"
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v17_preserves_failed_retained_repair_regression() -> None:
    gate = json.loads(
        (EXECUTION_REPAIR_V17 / "structural_gate.json").read_text(encoding="utf-8")
    )
    visual = json.loads(
        (EXECUTION_REPAIR_V17 / "visual_clash.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V17 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert not any(
        candidate.get("kind") == "text_on_path"
        and candidate.get("text") == "retained"
        for candidate in visual["candidates"]
    )
    assert gate["blocking_counts"]["semantic_path_crossing"] == 0
    assert gate["blocking_counts"]["text_text"] == 1
    assert gate["state"] == "failed"
    assert gate["structural_pass"] is False
    assert review["decision"] == "failed_exact_repair"
    assert review["repair_result"] == (
        "retained path clash removed but title collision introduced"
    )
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v18_removes_retained_regression_without_claiming_acceptance() -> None:
    gate = json.loads(
        (EXECUTION_REPAIR_V18 / "structural_gate.json").read_text(encoding="utf-8")
    )
    visual = json.loads(
        (EXECUTION_REPAIR_V18 / "visual_clash.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V18 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert not any(
        candidate.get("kind") == "text_on_path"
        and candidate.get("text") == "retained"
        for candidate in visual["candidates"]
    )
    assert gate["blocking_counts"]["semantic_path_crossing"] == 0
    assert gate["blocking_counts"]["text_text"] == 0
    assert gate["state"] == "failed"
    assert gate["structural_pass"] is False
    assert review["repair_result"] == (
        "retained label clear of title path and electrode"
    )
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v19_preserves_failed_sample_title_reflow() -> None:
    gate = json.loads(
        (EXECUTION_REPAIR_V19 / "structural_gate.json").read_text(encoding="utf-8")
    )
    visual = json.loads(
        (EXECUTION_REPAIR_V19 / "visual_clash.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V19 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert gate["blocking_counts"]["semantic_path_crossing"] == 0
    assert gate["blocking_counts"]["text_text"] == 2
    assert gate["state"] == "failed"
    assert review["decision"] == "failed_exact_repair"
    assert review["repair_result"] == (
        "sample title cleared electrodes but collided with retained label"
    )
    assert any(candidate.get("text") == "film" for candidate in visual["candidates"])
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v20_places_sample_title_in_clear_upper_safe_area() -> None:
    gate = json.loads(
        (EXECUTION_REPAIR_V20 / "structural_gate.json").read_text(encoding="utf-8")
    )
    visual = json.loads(
        (EXECUTION_REPAIR_V20 / "visual_clash.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V20 / "execution_review.json").read_text(encoding="utf-8")
    )

    title_tokens = {"disordered", "sulfur–polymer", "film"}
    assert not any(
        candidate.get("kind") in {"text_on_path", "text_on_fill"}
        and candidate.get("text") in title_tokens
        for candidate in visual["candidates"]
    )
    assert gate["blocking_counts"]["semantic_path_crossing"] == 0
    assert gate["blocking_counts"]["text_text"] == 0
    assert gate["blocking_counts"]["text_on_path_or_fill"] < 7
    assert gate["state"] == "failed"
    assert review["repair_result"] == (
        "sample title clear of electrodes and retained label"
    )
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v20_records_named_human_correction_findings() -> None:
    findings = yaml.safe_load(V20_HUMAN_FINDINGS.read_text(encoding="utf-8"))

    assert findings["reviewer"] == "Moon"
    assert findings["decision"] == "corrections_required"
    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V20 / "repaired_generated.tex"
    )
    assert {item["subject"] for item in findings["findings"]} == {
        "panel_a_retained_label",
        "panel_a_capture_release_labels",
        "panel_a_sign_agnostic_carrier_label",
        "panel_a_direction_arrows",
        "panel_b_magnitude_label",
        "panel_b_single_discrete_state_label",
    }
    assert findings["band_shape_authority"] == (
        "blocked_pending_physics_math_review"
    )
    assert findings["publication_acceptance"] == "not_claimed"


def test_fig3_v21_preserves_machine_passed_visual_regression() -> None:
    gate = json.loads(
        (EXECUTION_REPAIR_V21 / "structural_gate.json").read_text(encoding="utf-8")
    )
    visual = json.loads(
        (EXECUTION_REPAIR_V21 / "visual_clash.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V21 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert not any(
        candidate.get("kind") in {"text_on_path", "text_on_fill"}
        and candidate.get("text") == "sign-agnostic"
        for candidate in visual["candidates"]
    )
    assert gate["blocking_counts"] == {
        "semantic_path_crossing": 0,
        "text_on_path_or_fill": 4,
        "text_text": 0,
    }
    assert gate["state"] == "failed"
    assert review["decision"] == "machine_target_resolved_visual_regression"
    assert review["repair_result"] == (
        "boundary clash removed but label overlaps carrier and trap marks"
    )
    assert review["human_review"] == "corrections_required"


def test_fig3_v22_binds_human_correction_to_failed_v21_source() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V22 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V22 / "repair_packet.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V21 / "repaired_generated.tex"
    )
    assert findings["findings"] == [
        {
            "id": "HF007",
            "subject": "panel_a_sign_agnostic_carrier_label",
            "finding": "label overlaps the carrier and trap marks after boundary repair",
        }
    ]
    assert packet["editable_target"]["finding_id"] == "HF007"
    assert packet["editable_target"]["report_path"].endswith(
        "execution-repair-v22/human_findings.before.json"
    )
    assert packet["publication_acceptance"] == "not_claimed"


def test_fig3_v23_retries_human_correction_from_last_compilable_source() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V23 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V23 / "repair_packet.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V21 / "repaired_generated.tex"
    )
    assert packet["source"]["path"].endswith(
        "execution-repair-v21/repaired_generated.tex"
    )
    assert packet["editable_target"]["finding_id"] == "HF007"
    assert packet["publication_acceptance"] == "not_claimed"


def test_fig3_v24_binds_disorder_dot_overlap_to_v23_source() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V24 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V24 / "repair_packet.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V23 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF008"
    assert packet["editable_target"]["finding_id"] == "HF008"
    assert packet["editable_target"]["repair_family"] == "salience_adjustment"
    assert packet["publication_acceptance"] == "not_claimed"


def test_fig3_v25_binds_residual_dot_sliver_to_v24_source() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V25 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V25 / "repair_packet.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V24 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF009"
    assert packet["editable_target"]["finding_id"] == "HF009"
    assert packet["publication_acceptance"] == "not_claimed"


def test_fig3_v26_binds_single_state_axis_clash_to_v25_source() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V26 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V26 / "repair_packet.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V25 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF010"
    assert packet["editable_target"]["finding_id"] == "HF010"
    assert packet["editable_target"]["repair_family"] == "label_reflow"
    assert packet["publication_acceptance"] == "not_claimed"


def test_fig3_v27_binds_s60_overlap_to_v26_source() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V27 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V27 / "repair_packet.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V26 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF011"
    assert packet["editable_target"]["finding_id"] == "HF011"
    assert packet["publication_acceptance"] == "not_claimed"


def test_fig3_v28_retries_s60_overlap_within_change_budget() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V28 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V28 / "repair_packet.json").read_text(encoding="utf-8")
    )
    collisions = json.loads(
        (EXECUTION_REPAIR_V28 / "collisions.json").read_text(encoding="utf-8")
    )
    gate = json.loads(
        (EXECUTION_REPAIR_V28 / "structural_gate.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V28 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V26 / "repaired_generated.tex"
    )
    assert findings["prior_rejected_attempt"] == "execution-repair-v27"
    assert packet["editable_target"]["finding_id"] == "HF011"
    assert packet["change_budget"]["max_changed_lines"] == 6
    assert packet["publication_acceptance"] == "not_claimed"
    assert collisions["collisions"] == []
    assert gate["blocking_counts"] == {
        "semantic_path_crossing": 0,
        "text_on_path_or_fill": 4,
        "text_text": 0,
    }
    assert review["decision"] == "human_target_resolved_overall_review_required"
    assert review["next_human_target"] == "panel_b_magnitude_label"
    assert review["publication_acceptance"] == "not_claimed"
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v29_binds_magnitude_ownership_to_v28_source() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V29 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V29 / "repair_packet.json").read_text(encoding="utf-8")
    )
    collisions = json.loads(
        (EXECUTION_REPAIR_V29 / "collisions.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V29 / "execution_review.json").read_text(encoding="utf-8")
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V29 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V28 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF012"
    assert packet["editable_target"]["finding_id"] == "HF012"
    assert packet["editable_target"]["repair_family"] == "label_reflow"
    assert packet["publication_acceptance"] == "not_claimed"
    assert collisions["total"] == 2
    assert regression["state"] == "regressed"
    assert regression["regression"]["new_blockers"]
    assert review["decision"] == "candidate_rejected_collision_persisted"
    assert review["next_human_target"] == "panel_b_magnitude_label"
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v30_retries_magnitude_as_compact_key() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V30 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V30 / "repair_packet.json").read_text(encoding="utf-8")
    )
    collisions = json.loads(
        (EXECUTION_REPAIR_V30 / "collisions.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V30 / "execution_review.json").read_text(encoding="utf-8")
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V30 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V29 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF012"
    assert findings["prior_rejected_attempt"] == "execution-repair-v29"
    assert packet["editable_target"]["finding_id"] == "HF012"
    assert packet["change_budget"]["max_changed_lines"] == 6
    assert packet["publication_acceptance"] == "not_claimed"
    assert collisions["collisions"] == []
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []
    assert review["decision"] == "human_target_resolved_overall_review_required"
    assert review["next_human_target"] == "panel_a_transition_label_arrow_grammar"
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v31_starts_panel_a_transition_grammar_without_new_blockers() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V31 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V31 / "repair_packet.json").read_text(encoding="utf-8")
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V31 / "regression_gate.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V31 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V30 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF013"
    assert packet["editable_target"]["finding_id"] == "HF013"
    assert packet["editable_target"]["repair_family"] == "label_reflow"
    assert packet["publication_acceptance"] == "not_claimed"
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []
    assert review["next_human_target"] == "panel_a_duplicate_transition_labels"
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v32_removes_duplicate_transition_labels_without_new_blockers() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V32 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V32 / "repair_packet.json").read_text(encoding="utf-8")
    )
    collisions = json.loads(
        (EXECUTION_REPAIR_V32 / "collisions.json").read_text(encoding="utf-8")
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V32 / "regression_gate.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V32 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V31 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF014"
    assert packet["editable_target"]["finding_id"] == "HF014"
    assert packet["change_budget"]["max_changed_lines"] == 6
    assert packet["publication_acceptance"] == "not_claimed"
    assert collisions["collisions"] == []
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []
    assert review["next_human_target"] == "panel_a_arrow_direction_consistency"
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v33_aligns_arrow_with_path_direction_without_new_blockers() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V33 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V33 / "repair_packet.json").read_text(encoding="utf-8")
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V33 / "regression_gate.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V33 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V32 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF015"
    assert packet["editable_target"]["finding_id"] == "HF015"
    assert packet["editable_target"]["repair_family"] == "relation_restore"
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []
    assert review["next_human_target"] == "panel_a_retained_label_ownership"
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v34_rejects_retained_label_shift_that_creates_new_collisions() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V34 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V34 / "repair_packet.json").read_text(encoding="utf-8")
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V34 / "regression_gate.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V34 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V33 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF016"
    assert packet["editable_target"]["finding_id"] == "HF016"
    assert packet["editable_target"]["repair_family"] == "label_reflow"
    assert regression["regression"]["state"] == "regressed"
    signatures = {
        blocker["signature"] for blocker in regression["regression"]["new_blockers"]
    }
    assert "text_text:film|retained" in signatures
    assert "text_text:retained|sulfur–polymer" in signatures
    assert review["decision"] == "repair_rejected_new_blockers"
    assert review["next_human_target"] == "panel_a_retained_ownership_external_key_retry"
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v35_moves_retained_ownership_to_external_key_without_regression() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V35 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V35 / "repair_packet.json").read_text(encoding="utf-8")
    )
    collisions = json.loads(
        (EXECUTION_REPAIR_V35 / "collisions.json").read_text(encoding="utf-8")
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V35 / "regression_gate.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V35 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V33 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF017"
    assert packet["editable_target"]["finding_id"] == "HF017"
    assert packet["editable_target"]["repair_family"] == "label_reflow"
    assert collisions["collisions"] == []
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []
    assert review["next_human_target"] == "panel_a_external_key_proportion"
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v36_reduces_external_key_without_new_blockers() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V36 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V36 / "repair_packet.json").read_text(encoding="utf-8")
    )
    collisions = json.loads(
        (EXECUTION_REPAIR_V36 / "collisions.json").read_text(encoding="utf-8")
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V36 / "regression_gate.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V36 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V35 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF018"
    assert packet["editable_target"]["finding_id"] == "HF018"
    assert packet["editable_target"]["repair_family"] == "label_reflow"
    assert collisions["collisions"] == []
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []
    assert review["next_human_target"] == "panel_a_transition_grammar_scaffold_review"
    assert review["publication_acceptance"] == "not_claimed"


def test_fig3_v37_removes_floating_arrow_overlays() -> None:
    findings = json.loads(
        (EXECUTION_REPAIR_V37 / "human_findings.before.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (EXECUTION_REPAIR_V37 / "repair_packet.json").read_text(encoding="utf-8")
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V37 / "regression_gate.json").read_text(encoding="utf-8")
    )
    source = (EXECUTION_REPAIR_V37 / "repaired_generated.tex").read_text(
        encoding="utf-8"
    )

    assert findings["bound_source_sha256"] == _sha256(
        EXECUTION_REPAIR_V36 / "repaired_generated.tex"
    )
    assert findings["findings"][0]["id"] == "HF019"
    assert packet["editable_target"]["finding_id"] == "HF019"
    assert packet["editable_target"]["repair_family"] == "relation_restore"
    assert "line width=0.75pt, -{Stealth}" not in source
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []


def test_fig3_v38_owns_inset_axis_labels_without_endpoint_attachment() -> None:
    source = (EXECUTION_REPAIR_V38 / "repaired_generated.tex").read_text(
        encoding="utf-8"
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V38 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert "node[compact label, below left=0pt] {$t$}" not in source
    assert "node[compact label, above right=0pt] {$I(t)$}" not in source
    assert "rotate=90" in source
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []


def test_fig3_v39_rejects_ge_axis_label_that_touches_axis_path() -> None:
    regression = json.loads(
        (EXECUTION_REPAIR_V39 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert regression["regression"]["state"] == "regressed"
    assert regression["regression"]["new_blockers"] == [
        {"count_delta": 1, "signature": "visual:text_on_path:g(E)"}
    ]


def test_fig3_v40_rejects_larger_rotated_ge_offset() -> None:
    regression = json.loads(
        (EXECUTION_REPAIR_V40 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert regression["regression"]["state"] == "regressed"
    assert regression["regression"]["new_blockers"][0]["signature"] == (
        "visual:text_on_path:g(E)"
    )


def test_fig3_v41_uses_horizontal_ge_ordinate_label_clear_of_axis() -> None:
    source = (EXECUTION_REPAIR_V41 / "repaired_generated.tex").read_text(
        encoding="utf-8"
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V41 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert "anchor=south east" in source
    assert "at (-0.05,2.82) {$g(E)$}" in source
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []


def test_fig3_v42_rejects_tight_s60_descriptor_stack() -> None:
    regression = json.loads(
        (EXECUTION_REPAIR_V42 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert regression["regression"]["state"] == "regressed"
    assert regression["regression"]["new_blockers"][0]["signature"] == (
        "visual:text_on_path:S60"
    )


def test_fig3_v43_expands_s60_descriptor_stack_clearance() -> None:
    source = (EXECUTION_REPAIR_V43 / "repaired_generated.tex").read_text(
        encoding="utf-8"
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V43 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert "at (0.965,2.06) {S60}" in source
    assert "at (0.965,1.68) {single discrete state}" in source
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []


def test_fig3_v44_rejects_rho_label_touching_metric_axis() -> None:
    regression = json.loads(
        (EXECUTION_REPAIR_V44 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert regression["regression"]["state"] == "regressed"
    assert regression["regression"]["new_blockers"][0]["signature"] == (
        "visual:text_on_path:ρ"
    )


def test_fig3_v47_separates_magnitude_lane_without_new_blockers() -> None:
    source = (EXECUTION_REPAIR_V47 / "repaired_generated.tex").read_text(
        encoding="utf-8"
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V47 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert "anchor=west, fill=white" in source
    assert "at (4.58,0.765) {magnitude};" in source
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []


def test_fig3_v48_and_v49_preserve_breadth_span_failures() -> None:
    v48 = json.loads(
        (EXECUTION_REPAIR_V48 / "regression_gate.json").read_text(encoding="utf-8")
    )
    v49 = json.loads(
        (EXECUTION_REPAIR_V49 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert v48["regression"]["state"] == "regressed"
    assert len(v48["regression"]["new_blockers"]) == 2
    assert v49["regression"]["state"] == "regressed"
    assert v49["regression"]["new_blockers"][0]["signature"] == (
        "geometry:label_crosses_semantic_path:breadth"
    )


def test_fig3_v50_separates_distribution_breadth_from_fitted_n() -> None:
    source = (EXECUTION_REPAIR_V50 / "repaired_generated.tex").read_text(
        encoding="utf-8"
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V50 / "regression_gate.json").read_text(encoding="utf-8")
    )
    contract = (FIXTURE / "authoring_contract.md").read_text(encoding="utf-8")

    assert "{$n$: breadth}" not in source
    assert "{distribution breadth}" in source
    assert "must not equate geometric width directly with `n`" in contract
    assert regression["regression"]["state"] == "no_new_blockers"
    assert regression["regression"]["new_blockers"] == []


def test_fig3_v53_keeps_single_descriptor_clear_as_a_coupled_stack() -> None:
    source = (EXECUTION_REPAIR_V53 / "repaired_generated.tex").read_text(
        encoding="utf-8"
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V53 / "regression_gate.json").read_text(encoding="utf-8")
    )

    assert "at (0.965,1.68) {single discrete\\\\state}" in source
    assert regression["regression"]["state"] == "no_new_blockers"


def test_fig3_v64_encodes_one_carrier_path_and_preserves_failed_retries() -> None:
    source = (EXECUTION_REPAIR_V64 / "repaired_generated.tex").read_text(
        encoding="utf-8"
    )
    regression = json.loads(
        (EXECUTION_REPAIR_V64 / "regression_gate.json").read_text(encoding="utf-8")
    )
    v56 = json.loads(
        (EXECUTION_REPAIR_V56 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert source.count("\\node[carrier") == 2
    assert "one carrier path over time" in source
    assert "trap contacts: capture/release; solid end: retained" in source
    assert "discrete S60 $\\longrightarrow$ continuous broad S80" not in source
    assert regression["regression"]["state"] == "no_new_blockers"
    assert v56["decision"] == "failed_exact_repair"


def test_fig3_v66_rejects_breadth_lane_transfer_to_axis_labels() -> None:
    regression = json.loads(
        (EXECUTION_REPAIR_V66 / "regression_gate.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (EXECUTION_REPAIR_V66 / "execution_review.json").read_text(encoding="utf-8")
    )

    signatures = {
        item["signature"] for item in regression["regression"]["new_blockers"]
    }
    assert regression["regression"]["state"] == "regressed"
    assert signatures == {"visual:text_on_path:E", "visual:text_on_path:g(E)"}
    assert review["decision"] == "failed_exact_repair"



def test_fig3_comparable_v1_declares_one_shared_contract_and_three_conditions() -> None:
    contract = yaml.safe_load(COMPARISON_CONTRACT.read_text(encoding="utf-8"))

    assert contract["schema"] == "figure-agent.failure-ablation-comparison.v1"
    assert contract["fixture"] == "fig3_resistance_mechanism"
    assert contract["comparison_eligibility"] == "eligible_equal_input"
    assert contract["shared_contract"] == {
        "model_contract_path": "../model_contract.yaml",
        "model_contract_sha256": _sha256(REVIEW / "model_contract.yaml"),
        "input_packet_path": "../input_packet.yaml",
        "input_packet_sha256": _sha256(PACKET),
        "budget_contract_path": "../budget_contract.yaml",
        "budget_contract_sha256": _sha256(REVIEW / "budget_contract.yaml"),
        "starting_artifact_path": "blank_start.txt",
        "starting_artifact_sha256": _sha256(COMPARABLE_V1 / "blank_start.txt"),
    }
    assert set(contract["conditions"]) == {"raw", "verified", "repaired"}
    for variant, condition in contract["conditions"].items():
        prompt = COMPARABLE_V1 / condition["prompt_path"]
        assert condition["condition_id"] == variant
        assert condition["prompt_sha256"] == _sha256(prompt)
        assert condition["authoring_attempts"] == 1
        assert condition["starting_artifact_path"] == "blank_start.txt"
    assert contract["forbidden_authoring_inputs"] == [
        "../../fig3_resistance_mechanism.tex",
        "../raw_generated.tex",
        "../verified_generated.tex",
        "../repaired_generated.tex",
        "../execution-binding-v*/",
        "../execution-repair-v*/",
        "examples/fig1_*/",
    ]
    assert contract["publication_acceptance"] == "not_claimed"


def test_fig3_comparable_v1_is_transcript_bound_but_nonrenderable() -> None:
    contract = yaml.safe_load(COMPARISON_CONTRACT.read_text(encoding="utf-8"))
    runs: dict[str, Path] = {}
    receipts: list[dict[str, str]] = []

    for variant, condition in contract["conditions"].items():
        run_path = COMPARABLE_V1 / f"{variant}.yaml"
        run = yaml.safe_load(run_path.read_text(encoding="utf-8"))
        source = COMPARABLE_V1 / f"{variant}_generated.tex"
        receipt = run["generation_receipt"]
        runs[variant] = run_path
        receipts.append(receipt)

        assert run["comparison_eligibility"] == "eligible_equal_input"
        assert run["comparison_contract_hash"] == _sha256(COMPARISON_CONTRACT)
        assert run["condition_prompt_hash"] == condition["prompt_sha256"]
        assert run["compile_outcome"]["exit"] == 1
        assert run["compile_outcome"]["state"] == (
            "blocked_before_render_by_style_lock"
        )
        assert run["semantic_evaluation"] == "unavailable_nonrenderable"
        assert run["clean_reproduction"] is False
        assert run["human_verdict"] == {"state": "pending"}
        assert run["publication_acceptance"] == "not_claimed"
        assert receipt["generated_artifact_sha256"] == _sha256(source)
        assert receipt["transcript_sha256"] == _sha256(
            COMPARABLE_V1 / receipt["transcript_path"]
        )

    assert {receipt["model_id"] for receipt in receipts} == {"codex-gpt-5.5"}
    assert {receipt["source_commit"] for receipt in receipts} == {"59e64de8"}
    assert {receipt["starting_artifact_sha256"] for receipt in receipts} == {
        contract["shared_contract"]["starting_artifact_sha256"]
    }

    report = evaluate_ablation(runs)
    tracked_report = json.loads(
        (COMPARABLE_V1 / "ablation_report.json").read_text(encoding="utf-8")
    )
    assert report == tracked_report
    assert report["comparison_evidence"] == "transcript_bound"
    assert report["reproduction_gate"] == "failed"
    assert report["deltas"]["verified_vs_raw"][
        "confirmed_defect_occurrence_count"
    ] == 21
    assert report["deltas"]["repaired_vs_raw"][
        "confirmed_defect_occurrence_count"
    ] == 30
    assert report["product_claim"] == "not_authorized"
    assert report["publication_acceptance"] == "not_claimed"


def test_fig3_comparable_v2_binds_pre_authoring_contract_interventions() -> None:
    contract = yaml.safe_load(COMPARISON_CONTRACT_V2.read_text(encoding="utf-8"))

    assert contract["comparison_eligibility"] == "eligible_equal_input"
    assert contract["shared_contract"]["starting_artifact_sha256"] == _sha256(
        COMPARABLE_V2 / "blank_start.txt"
    )
    assert contract["shared_contract"]["authoring_attempts_per_condition"] == 1
    assert contract["shared_contract"]["feedback_rounds"] == 0
    assert contract["shared_contract"]["manual_repairs"] == 0
    assert contract["conditions"]["raw"]["intervention"] == (
        "free_authoring_without_figure_agent_contract"
    )
    assert contract["conditions"]["verified"]["intervention"] == (
        "figure_agent_style_contract_injected_before_authoring"
    )
    assert "declared_layout_lane" in contract["conditions"]["repaired"][
        "intervention"
    ]
    for variant, condition in contract["conditions"].items():
        assert condition["prompt_sha256"] == _sha256(
            COMPARABLE_V2 / condition["prompt_path"]
        )
        if variant != "raw":
            packet = json.loads(
                (COMPARABLE_V2 / condition["packet_path"]).read_text(encoding="utf-8")
            )
            assert packet["packet_sha256"] == condition["packet_sha256"]
            assert packet["feedback_rounds"] == 0
            assert packet["manual_repairs"] == 0
    assert contract["publication_acceptance"] == "not_claimed"


def test_fig3_comparable_v2_is_reproducible_but_still_requires_human_review() -> None:
    runs = {
        variant: COMPARABLE_V2 / f"{variant}.yaml"
        for variant in ("raw", "verified", "repaired")
    }
    for variant, path in runs.items():
        run = yaml.safe_load(path.read_text(encoding="utf-8"))
        receipt = run["generation_receipt"]
        assert run["clean_reproduction"] is True
        assert run["publication_acceptance"] == "not_claimed"
        assert receipt["generated_artifact_sha256"] == _sha256(
            COMPARABLE_V2 / f"{variant}_generated.tex"
        )
        assert receipt["transcript_sha256"] == _sha256(
            COMPARABLE_V2 / receipt["transcript_path"]
        )

    assert yaml.safe_load(runs["raw"].read_text(encoding="utf-8"))[
        "human_verdict"
    ] == {"state": "pending"}
    for variant in ("verified", "repaired"):
        verdict = yaml.safe_load(runs[variant].read_text(encoding="utf-8"))[
            "human_verdict"
        ]
        assert verdict["state"] == "recorded"
        assert verdict["reviewer"] == "moon"
        assert verdict["decision"] == "rejected"
        assert verdict["aesthetic_review_deferred"] is True

    assert yaml.safe_load(runs["raw"].read_text(encoding="utf-8"))[
        "compile_outcome"
    ]["state"] == "blocked_before_render_by_style_lock"
    for variant in ("verified", "repaired"):
        run = yaml.safe_load(runs[variant].read_text(encoding="utf-8"))
        assert run["compile_outcome"]["exit"] == 0
        assert run["layout_gate"]["state"] == "failed"
        assert run["render_receipt"]["pdf_sha256"] == _sha256(
            COMPARABLE_V2 / run["render_receipt"]["pdf_path"]
        )
        assert run["render_receipt"]["png_sha256"] == _sha256(
            COMPARABLE_V2 / run["render_receipt"]["png_path"]
        )

    report = evaluate_ablation(runs)
    assert report == json.loads(
        (COMPARABLE_V2 / "ablation_report.json").read_text(encoding="utf-8")
    )
    assert report["comparison_evidence"] == "transcript_bound"
    assert report["reproduction_gate"] == "passed"
    assert report["variants"]["raw"]["confirmed_defect_occurrence_count"] == 26
    assert report["variants"]["verified"]["confirmed_defect_occurrence_count"] == 6
    assert report["variants"]["repaired"]["confirmed_defect_occurrence_count"] == 3
    assert report["product_claim"] == "not_authorized"
    assert report["publication_acceptance"] == "not_claimed"


def _declared_fixture_path(relative_path: str) -> Path:
    path = (FIXTURE / relative_path).resolve()
    assert path.is_relative_to(FIXTURE.resolve())
    return path


def _isolated_historical_tex(tmp_path: Path, source: Path) -> Path:
    """Copy a historical TeX input before compilation.

    Historical review attempts are immutable evidence, so their ignored build
    directories must never be the output location of a regression test.
    """
    copied = tmp_path / "historical-render-inputs" / source.parent.name / source.name
    copied.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, copied)
    return copied


def _git_pending_paths(repo_root: Path) -> set[str]:
    commands = (
        ("diff", "--name-only", "--cached"),
        ("diff", "--name-only"),
        ("ls-files", "--others", "--exclude-standard"),
    )
    pending: set[str] = set()
    for command in commands:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *command],
            check=True,
            capture_output=True,
            text=True,
        )
        pending.update(path for path in result.stdout.splitlines() if path)
    return pending


def _git_branch_delta_paths(repo_root: Path, base_ref: str) -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--name-only", f"{base_ref}...HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return {path for path in result.stdout.splitlines() if path}


def _scope_violations(pending_paths: set[str], allowed_paths: set[str]) -> set[str]:
    return pending_paths - allowed_paths


def _tool_version(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return next(line for line in (result.stdout + result.stderr).splitlines() if line)


def _compile_receipt_outputs() -> dict[str, object]:
    receipt = yaml.safe_load(RENDER_RECEIPT.read_text(encoding="utf-8"))
    subprocess.run(
        receipt["compile_command"], cwd=PLUGIN_ROOT, check=True, capture_output=True, text=True
    )
    return receipt


def _pdf_content_signature(path: Path) -> dict[str, object]:
    text_result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True
    )
    normalized_text = "\n".join(line.rstrip() for line in text_result.stdout.splitlines()).strip() + "\n"
    info_result = subprocess.run(
        ["pdfinfo", str(path)], check=True, capture_output=True, text=True
    )
    page_count = int(next(line.split(":", 1)[1] for line in info_result.stdout.splitlines() if line.startswith("Pages:")).strip())
    return {
        "schema": "figure-agent.pdf-content-signature.v1",
        "extraction": "pdftotext-layout-trim-right-lines-v1",
        "normalized_text_sha256": "sha256:" + hashlib.sha256(normalized_text.encode()).hexdigest(),
        "page_count": page_count,
    }


def _pdf_normalized_token_inventory(path: Path) -> Counter[str]:
    """Bind visible wording while ignoring layout-only text repositioning."""
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Counter(re.findall(r"\w+|[^\w\s]", result.stdout.casefold()))


def test_fig3_resistance_failure_first_packet_hash_binds_current_authority() -> None:
    packet = yaml.safe_load(PACKET.read_text(encoding="utf-8"))

    assert packet["schema"] == "figure-agent.failure-first-input-packet.v1"
    assert packet["fixture"] == "fig3_resistance_mechanism"
    assert packet["generation_status"] == "not_run"
    assert packet["panels"] == ["A", "B"]
    assert packet["publication_acceptance"] == "not_claimed"
    assert packet["forbidden_import_patterns"] == [
        "examples/fig1_",
        "experiments/python_svg_semantic_fig1",
        "fig1_hybrid_complex_panel_pilot",
    ]
    _compile_receipt_outputs()

    roles = [item["role"] for item in packet["authoritative_inputs"]]
    assert roles == [
        "briefing",
        "specification",
        "authoring_contract",
        "panel_goals",
        "editable_source",
        "rendered_png",
        "rendered_pdf",
        "critique",
        "critique_adjudication",
        "semantic_boundary",
        "scope_protection",
        "render_receipt",
        "shape_profile",
        "shape_experiment_model_contract",
        "shape_experiment_budget_contract",
        "shape_experiment_blank_start",
        "shape_experiment_control_packet",
        "shape_profile_treatment_overlay",
        "shape_control_authoring_prompt",
        "shape_profiled_authoring_prompt",
    ]
    assert len(roles) == len(set(roles))
    for item in packet["authoritative_inputs"]:
        relative_path = Path(item["path"])
        assert not relative_path.is_absolute()
        assert ".." not in relative_path.parts
        assert relative_path.as_posix() == item["path"]
        path = (FIXTURE / relative_path).resolve()
        assert path.is_relative_to(FIXTURE.resolve())
        assert path.relative_to(FIXTURE.resolve()).as_posix() == item["path"]
        assert path.is_file()
        if item["role"] == "rendered_pdf":
            assert "sha256" not in item
            assert item["content_signature"]["schema"] == "figure-agent.pdf-content-signature.v1"
        elif item["role"] in {
            "briefing",
            "specification",
            "authoring_contract",
            "panel_goals",
            "editable_source",
            "rendered_png",
            "critique",
            "critique_adjudication",
            "semantic_boundary",
            "render_receipt",
        }:
            # input_packet.yaml is a preserved historical run packet, not the
            # authority for later live Fig3 source, render, or review evidence.
            assert item["sha256"].startswith("sha256:")
        else:
            assert item["sha256"] == _sha256(path)


def test_fig3_current_authority_manifest_is_additive_and_hash_bound() -> None:
    manifest = yaml.safe_load(AUTHORITY_MANIFEST_V2.read_text(encoding="utf-8"))

    assert manifest["supersedes_for_future_runs"] == "input_packet.yaml"
    assert manifest["historical_packet_policy"] == "preserve_byte_identity"
    for item in manifest["authoritative_inputs"]:
        assert item["sha256"] == _sha256(FIXTURE / item["path"])
    assert manifest["semantic_boundary"] == {
        "fitted_n": "Curie-von Schweidler exponent",
        "distribution_breadth": "schematic mechanism cue",
        "mapping": "model_or_calibration_required",
    }
    assert manifest["publication_acceptance"] == "not_claimed"

    packet = yaml.safe_load(PACKET.read_text(encoding="utf-8"))
    source_roles = {
        "briefing",
        "specification",
        "authoring_contract",
        "panel_goals",
        "editable_source",
        "semantic_boundary",
    }
    for item in packet["authoritative_inputs"]:
        if item["role"] in source_roles:
            contents = (FIXTURE / item["path"]).read_text(encoding="utf-8")
            for forbidden in packet["forbidden_import_patterns"]:
                assert forbidden not in contents


def test_fig3_authoring_contract_requires_named_binding_for_semantic_leaders() -> None:
    contract = (FIXTURE / "authoring_contract.md").read_text(encoding="utf-8")
    spec = yaml.safe_load((FIXTURE / "spec.yaml").read_text(encoding="utf-8"))

    assert "named_endpoint_assertions.required_node_bindings" in contract
    terminal_leader = next(
        assertion
        for assertion in spec["named_endpoint_assertions"]
        if assertion["id"] == "terminal-state-label-binds-to-terminal-trap"
    )
    assert terminal_leader["required_node_bindings"] == [
        {"node": "slow_release_label", "anchor": "slow_release_label_anchor"}
    ]


def test_fig3_resistance_declares_two_panel_semantic_object_relation_boundary() -> None:
    boundary = yaml.safe_load(BOUNDARY.read_text(encoding="utf-8"))

    assert boundary["schema"] == "figure-agent.semantic-object-relation-boundary.v1"
    assert boundary["fixture"] == "fig3_resistance_mechanism"
    assert boundary["declared_scope"] == "three_column_explanatory_schematic_of_composite_fig3"
    assert set(boundary["panels"]) == {"A", "B", "C"}
    assert boundary["panels"]["A"]["required_objects"] == [
        "applied_bias_cell",
        "sign_agnostic_carrier_walk",
        "repeated_trap_release",
    ]
    assert boundary["panels"]["A"]["required_relations"] == [
        "applied_bias_cell_encloses_disordered_sulfur_polymer_film",
        "carrier_walk_contains_repeated_capture_and_release",
    ]
    assert boundary["panels"]["B"]["required_objects"] == [
        "qualitative_cvs_current_decay",
        "applied_voltage_resistance_relation",
    ]
    assert boundary["panels"]["B"]["required_relations"] == [
        "repeated_trapping_causes_qualitative_transient_current_decay",
        "current_decay_implies_resistance_increase_under_applied_voltage",
        "qualitative_curve_is_not_quantitative_measured_data",
    ]
    assert boundary["panels"]["C"]["required_objects"] == [
        "discrete_s60_energy_states",
        "continuous_broad_s80_energy_support",
    ]
    assert boundary["cross_panel_relations"] == [
        "trapping_mechanism_explains_qualitative_current_decay",
        "qualitative_current_decay_connects_to_composition_dependent_energy_landscape",
    ]
    assert boundary["out_of_scope_claims"] == [
        "carrier_polarity",
        "trap_chemistry",
        "quantitative_measured_data",
        "spatial_trap_network",
        "numerical_breadth_to_n_mapping",
    ]


def test_fig3_resistance_scope_allows_one_bounded_source_repair_and_protects_history() -> None:
    packet = yaml.safe_load(PACKET.read_text(encoding="utf-8"))
    scope = yaml.safe_load((REVIEW / "scope_protection.yaml").read_text(encoding="utf-8"))

    assert scope["schema"] == "figure-agent.failure-first-scope-protection.v1"
    assert scope["fixture"] == "fig3_resistance_mechanism"
    assert scope["authorized_change_mode"] == "bounded_source_repair_and_review_artifacts"
    assert scope["allowed_review_paths"] == [
        "fig3_resistance_mechanism.tex",
        "spec.yaml",
        "review/failure-first/input_packet.yaml",
        "review/failure-first/semantic_object_relation_boundary.yaml",
        "review/failure-first/scope_protection.yaml",
        "review/failure-first/render_receipt.yaml",
        "review/failure-first/model_contract.yaml",
        "review/failure-first/budget_contract.yaml",
        "review/failure-first/raw_authoring_prompt.md",
        "review/failure-first/raw_authority_packet.yaml",
        "review/failure-first/raw_generated.tex",
        "review/failure-first/raw_generated.pdf",
        "review/failure-first/raw_generated.png",
        "review/failure-first/raw_render_receipt.yaml",
        "review/failure-first/raw_selector_registry.yaml",
        "review/failure-first/raw.yaml",
        "review/failure-first/raw.transcript.json",
        "review/failure-first/style_control_generated.tex",
        "review/failure-first/style_control_generated.pdf",
        "review/failure-first/style_control_generated.png",
        "review/failure-first/style_control_render_receipt.yaml",
        "review/failure-first/style_control.yaml",
        "review/failure-first/verified_generated.tex",
        "review/failure-first/verified_generated.pdf",
        "review/failure-first/verified_generated.png",
        "review/failure-first/verified_render_receipt.yaml",
        "review/failure-first/verified.yaml",
        "review/failure-first/verified.transcript.json",
        "review/failure-first/verified_selector_registry.yaml",
        "review/failure-first/verified_attempt1_style_path_failed.tex",
        "review/failure-first/verified_attempt1_style_path_failed.yaml",
        "review/failure-first/layout_lane_contract.yaml",
        "review/failure-first/raw_layout_lane_report.json",
        "review/failure-first/verified_layout_lane_report.json",
        "review/failure-first/repaired_authoring_prompt.md",
        "review/failure-first/repaired_authority_packet.yaml",
        "review/failure-first/repaired_generated.tex",
        "review/failure-first/repaired_generated.pdf",
        "review/failure-first/repaired_generated.png",
        "review/failure-first/repaired_layout_lane_report.json",
        "review/failure-first/repaired_visual_clash.json",
        "review/failure-first/repaired_undeclared_geometry.json",
        "review/failure-first/repaired_label_hyphenation.json",
        "review/failure-first/repaired_render_receipt.yaml",
        "review/failure-first/repaired_layout_lane_attempt.yaml",
        "review/failure-first/repaired_posthoc_region_contract.yaml",
        "review/failure-first/repaired_posthoc_region_report.json",
        "review/failure-first/repaired_posthoc_region_evaluation.yaml",
        "review/failure-first/region_guided_authoring_prompt.md",
        "review/failure-first/region_guided_authority_packet.yaml",
        "review/failure-first/region_guided_generated.tex",
        "review/failure-first/region_guided_generated.pdf",
        "review/failure-first/region_guided_generated.png",
        "review/failure-first/region_guided_layout_report.json",
        "review/failure-first/region_guided_visual_clash.json",
        "review/failure-first/region_guided_undeclared_geometry.json",
        "review/failure-first/region_guided_label_hyphenation.json",
        "review/failure-first/region_guided_adversarial_review.yaml",
        "review/failure-first/region_guided_attempt.yaml",
        "review/failure-first/region_guided_render_receipt.yaml",
        "review/failure-first/region_guided_text_inventory_contract.yaml",
        "review/failure-first/region_guided_text_inventory_report.json",
        "review/failure-first/region_guided_label_ownership_contract.yaml",
        "review/failure-first/region_guided_label_ownership_report.json",
        "review/failure-first/region_guided_mutual_clearance_contract.yaml",
        "review/failure-first/region_guided_mutual_clearance_report.json",
        "shape_profile_panel_b.yaml",
        "review/failure-first/shape_experiment_model_contract.yaml",
        "review/failure-first/shape_experiment_budget_contract.yaml",
        "review/failure-first/shape_experiment_blank_start.txt",
        "review/failure-first/shape_experiment_control_packet.yaml",
        "review/failure-first/shape_profile_treatment_overlay.yaml",
        "review/failure-first/shape_control_authoring_prompt.md",
        "review/failure-first/shape_profiled_authoring_prompt.md",
        "review/failure-first/shape_control_generated.tex",
        "review/failure-first/shape_profiled_generated.tex",
        "review/failure-first/shape_control_execution_receipt.yaml",
        "review/failure-first/shape_profiled_execution_receipt.yaml",
        "review/failure-first/shape_profile_comparison.yaml",
        "review/failure-first/shape_profile_adversarial_review.yaml",
        "review/failure-first/shape_profile_handoff.md",
        "review/failure-first/execution-binding-v4/execution_review.json",
        "review/failure-first/execution-binding-v4/control_input_audit.json",
        "review/failure-first/execution-binding-v4/treatment_input_audit.json",
        "review/failure-first/execution-binding-v5/control_packet.json",
        "review/failure-first/execution-binding-v5/control_prompt.md",
        "review/failure-first/execution-binding-v5/treatment_packet.json",
        "review/failure-first/execution-binding-v5/treatment_prompt.md",
        "review/failure-first/execution-binding-v5/preflight.json",
        "review/failure-first/execution-binding-v5/control_generated.tex",
        "review/failure-first/execution-binding-v5/treatment_generated.tex",
        "review/failure-first/execution-binding-v5/control_input_audit.json",
        "review/failure-first/execution-binding-v5/treatment_input_audit.json",
        "review/failure-first/execution-binding-v5/control_input_audit_v2.json",
        "review/failure-first/execution-binding-v5/treatment_input_audit_v2.json",
        "review/failure-first/execution-binding-v5/routing_review.json",
        "review/failure-first/execution-binding-v6/control_packet.json",
        "review/failure-first/execution-binding-v6/control_prompt.md",
        "review/failure-first/execution-binding-v6/treatment_packet.json",
        "review/failure-first/execution-binding-v6/treatment_prompt.md",
        "review/failure-first/execution-binding-v6/preflight.json",
        "review/failure-first/execution-binding-v6/control_generated.tex",
        "review/failure-first/execution-binding-v6/treatment_generated.tex",
        "review/failure-first/execution-binding-v6/control_input_audit.json",
        "review/failure-first/execution-binding-v6/treatment_input_audit.json",
        "review/failure-first/execution-binding-v6/control.touched-files.json",
        "review/failure-first/execution-binding-v6/treatment.touched-files.json",
        "review/failure-first/execution-binding-v6/control_receipt.json",
        "review/failure-first/execution-binding-v6/treatment_receipt.json",
        "review/failure-first/execution-binding-v6/execution_review.json",
        "review/failure-first/execution-binding-v7/binding_receipt.json",
        "review/failure-first/execution-binding-v7/treatment_generated.tex",
        "review/failure-first/execution-repair-v5/execution_review.json",
        "review/failure-first/execution-repair-v5/materialization_receipt.json",
        "review/failure-first/execution-repair-v5/repair_packet.json",
        "review/failure-first/execution-repair-v5/repair_prompt.md",
        "review/failure-first/execution-repair-v5/repair_response.json",
        "review/failure-first/execution-repair-v5/repair_targets.json",
        "review/failure-first/execution-repair-v5/repaired_generated.tex",
        "review/failure-first/execution-repair-v5/source_attribution.json",
        "review/failure-first/execution-repair-v5/source_selector_registry.json",
        "review/failure-first/execution-binding-v8/binding_receipt.json",
        "review/failure-first/execution-binding-v8/treatment_generated.tex",
        "review/failure-first/execution-repair-v6/execution_review.json",
        "review/failure-first/execution-repair-v6/label_hyphenation.before.json",
        "review/failure-first/execution-repair-v6/materialization_receipt.json",
        "review/failure-first/execution-repair-v6/repair_packet.json",
        "review/failure-first/execution-repair-v6/repair_prompt.md",
        "review/failure-first/execution-repair-v6/repair_response.json",
        "review/failure-first/execution-repair-v6/repair_targets.json",
        "review/failure-first/execution-repair-v6/repaired_generated.tex",
        "review/failure-first/execution-repair-v6/source_attribution.json",
        "review/failure-first/execution-repair-v6/source_selector_registry.json",
        "review/failure-first/execution-repair-v7/execution_review.json",
        "review/failure-first/execution-repair-v7/materialization_receipt.json",
        "review/failure-first/execution-repair-v7/repair_packet.json",
        "review/failure-first/execution-repair-v7/repair_prompt.md",
        "review/failure-first/execution-repair-v7/repair_response.json",
        "review/failure-first/execution-repair-v7/repair_targets.json",
        "review/failure-first/execution-repair-v7/repaired_generated.tex",
        "review/failure-first/execution-repair-v7/source_attribution.json",
        "review/failure-first/execution-repair-v8/execution_review.json",
        "review/failure-first/execution-repair-v8/materialization_receipt.json",
        "review/failure-first/execution-repair-v8/repair_packet.json",
        "review/failure-first/execution-repair-v8/repair_prompt.md",
        "review/failure-first/execution-repair-v8/repair_response.json",
        "review/failure-first/execution-repair-v8/repair_targets.json",
        "review/failure-first/execution-repair-v8/repaired_generated.tex",
        "review/failure-first/execution-repair-v8/source_attribution.json",
        "review/failure-first/execution-repair-v8/source_selector_registry.json",
        "review/failure-first/execution-detector-evaluation-v1/evaluation_review.json",
        "review/failure-first/execution-detector-evaluation-v1/undeclared_geometry.json",
        "review/failure-first/execution-repair-v9/execution_review.json",
        "review/failure-first/execution-repair-v9/repaired_generated.tex",
        "review/failure-first/execution-repair-v9/undeclared_geometry.json",
        "review/failure-first/execution-visual-clash-evaluation-v1/calibrated_visual_clash.json",
        "review/failure-first/execution-visual-clash-evaluation-v1/classification_review.json",
        "review/failure-first/execution-visual-clash-evaluation-v1/raw_visual_clash.json",
        "review/failure-first/execution-repair-v10/execution_review.json",
        "review/failure-first/execution-repair-v10/repaired_generated.tex",
        "review/failure-first/execution-repair-v10/visual_clash.json",
        "review/failure-first/execution-repair-v11/execution_review.json",
        "review/failure-first/execution-repair-v11/layout_report.json",
        "review/failure-first/execution-repair-v11/repaired_generated.tex",
        "review/failure-first/execution-repair-v11/visual_clash.json",
        "review/failure-first/execution-repair-v12/execution_review.json",
        "review/failure-first/execution-repair-v12/layout_report.json",
        "review/failure-first/execution-repair-v12/raw_visual_clash.json",
        "review/failure-first/execution-repair-v12/repaired_generated.tex",
        "review/failure-first/execution-repair-v12/visual_clash.json",
        "review/failure-first/execution-visual-clash-evaluation-v2/evaluation_review.json",
        "review/failure-first/execution-visual-clash-evaluation-v2/visual_clash.json",
        "review/failure-first/execution-scaffold-evaluation-v1/evaluation_review.json",
        "review/failure-first/execution-scaffold-evaluation-v1/layout_contract.yaml",
        "review/failure-first/execution-scaffold-evaluation-v1/layout_report.json",
    ]
    assert scope["allowed_repository_paths"] == [
        "examples/fig3_resistance_mechanism/review/failure-first/"
        "execution-binding-v5/control_generated.tex",
        "plugins/figure-agent/_known_false_positives.yaml",
        "plugins/figure-agent/bin/fig-agent",
        "plugins/figure-agent/docs/architecture-overview.md",
        "plugins/figure-agent/docs/execution-plan.md",
        "plugins/figure-agent/docs/product-spec.md",
        "plugins/figure-agent/docs/superpowers/issues/"
        "2026-06-01-issue-100hi-schema-module-map.md",
        "plugins/figure-agent/scripts/compile.sh",
        "plugins/figure-agent/scripts/authoring_context_pack.py",
        "plugins/figure-agent/scripts/authoring_execution_input_audit.py",
        "plugins/figure-agent/scripts/authoring_execution_packet.py",
        "plugins/figure-agent/scripts/authoring_repair_packet.py",
        "plugins/figure-agent/scripts/checks/check_label_hyphenation.py",
        "plugins/figure-agent/scripts/checks/check_undeclared_geometry.py",
        "plugins/figure-agent/scripts/checks/check_visual_clash.py",
        "plugins/figure-agent/scripts/finding_source_attribution.py",
        "plugins/figure-agent/scripts/checks/check_layout_drift.py",
        "plugins/figure-agent/scripts/visual_finding_artifacts.py",
        "plugins/figure-agent/tests/test_authoring_context_pack.py",
        "plugins/figure-agent/tests/test_authoring_execution_input_audit.py",
        "plugins/figure-agent/tests/test_authoring_execution_packet.py",
        "plugins/figure-agent/tests/test_authoring_repair_packet.py",
        "plugins/figure-agent/tests/test_finding_source_attribution.py",
        "plugins/figure-agent/tests/test_label_hyphenation.py",
        "plugins/figure-agent/tests/test_strict_mode.py",
        "plugins/figure-agent/tests/test_undeclared_geometry.py",
        "plugins/figure-agent/tests/test_check_layout_drift.py",
        "plugins/figure-agent/tests/test_compile_contract.py",
        "plugins/figure-agent/tests/test_fig3_resistance_failure_first.py",
        "plugins/figure-agent/tests/test_visual_finding_artifacts.py",
    ]
    assert scope["protected_paths"] == [
        "briefing.md",
        "authoring_contract.md",
        "panel_goals.md",
        "critique.md",
        "critique_adjudication.yaml",
        "../fig3_trap_schematic_slice3_semantic/**",
        "../fig1_*/**",
        "../fig1_direct_svg_cleanroom_baseline/**",
        "../../experiments/python_svg_semantic_fig1/**",
    ]

    scope_item = next(
        item for item in packet["authoritative_inputs"] if item["role"] == "scope_protection"
    )
    assert scope_item["path"] == "review/failure-first/scope_protection.yaml"
    assert scope_item["sha256"] == _sha256(REVIEW / "scope_protection.yaml")
    receipt_item = next(
        item for item in packet["authoritative_inputs"] if item["role"] == "render_receipt"
    )
    assert receipt_item["path"] == "review/failure-first/render_receipt.yaml"
    assert receipt_item["sha256"].startswith("sha256:")
    assert receipt_item["sha256"] != _sha256(RENDER_RECEIPT)


def test_shape_experiment_contracts_bind_identical_one_pass_clean_room_arms() -> None:
    model = yaml.safe_load(SHAPE_MODEL_CONTRACT.read_text(encoding="utf-8"))
    budget = yaml.safe_load(SHAPE_BUDGET_CONTRACT.read_text(encoding="utf-8"))
    control = yaml.safe_load(SHAPE_CONTROL_PACKET.read_text(encoding="utf-8"))

    assert model == {
        "schema": "figure-agent.shape-experiment-model-contract.v1",
        "model_id": "gpt-5.5",
        "authoring_mode": "feedback_derived_controlled_constraints_tikz",
        "output_kind": "standalone_tikz_source",
        "forbidden_import_classes": [
            "prior_generated_sources",
            "prior_generated_renders",
            "historical_fig3_artifacts",
            "fig1_artifacts",
        ],
        "publication_acceptance": "not_claimed",
    }
    assert budget["schema"] == "figure-agent.shape-experiment-budget-contract.v1"
    assert budget["variants"] == ["shape_control", "shape_profiled"]
    assert budget["authoring_attempts_per_variant"] == 1
    assert budget["max_tokens_per_attempt"] == 12000
    assert budget["feedback_between_attempts"] == "none"
    assert budget["manual_repair"] == "forbidden"
    assert SHAPE_BLANK_START.read_bytes() == b""
    assert control["model_contract_sha256"] == _sha256(SHAPE_MODEL_CONTRACT)
    assert control["budget_contract_sha256"] == _sha256(SHAPE_BUDGET_CONTRACT)
    assert control["blank_start"] == {
        "path": SHAPE_BLANK_START.name,
        "sha256": _sha256(SHAPE_BLANK_START),
        "identical_for_arms": ["shape_control", "shape_profiled"],
    }
    assert control["authority_conflicts"] == [
        "s60_peak_count_unresolved",
        "n_and_decay_direction_unresolved",
    ]
    assert control["provenance_status"] == (
        "feedback_derived_controlled_constraints_tikz"
    )
    assert control["execution_status"] == "not_run"
    assert control["execution_receipt_status"] == "not_created"
    assert control["publication_acceptance"] == "not_claimed"


def test_shape_experiment_treatment_is_exact_compiled_profile_only_delta() -> None:
    profile = yaml.safe_load(SHAPE_PROFILE.read_text(encoding="utf-8"))
    overlay = yaml.safe_load(SHAPE_TREATMENT_OVERLAY.read_text(encoding="utf-8"))
    compiled = authoring_context_pack.build_context_pack(
        "fig3_resistance_mechanism",
        plugin_root=PLUGIN_ROOT,
        workspace_root=PLUGIN_ROOT,
        shape_profile=SHAPE_PROFILE.name,
    )["shape_profile"]

    assert profile["schema"] == "figure-agent.shape-profile.v1"
    assert overlay == {
        "schema": "figure-agent.shape-profile-treatment-overlay.v1",
        "arm_id": "shape_profiled",
        "control_packet_sha256": _sha256(SHAPE_CONTROL_PACKET),
        "profile_path": SHAPE_PROFILE.name,
        "profile_sha256": _sha256(SHAPE_PROFILE),
        "authoring_directives": compiled["authoring_directives"],
    }
    assert set(overlay) == {
        "schema",
        "arm_id",
        "control_packet_sha256",
        "profile_path",
        "profile_sha256",
        "authoring_directives",
    }

    control_prompt = SHAPE_CONTROL_PROMPT.read_text(encoding="utf-8")
    treatment_prompt = SHAPE_PROFILED_PROMPT.read_text(encoding="utf-8")
    normalized_control = control_prompt.replace("shape_control", "ARM").replace(
        "AUTHORIZED_INPUTS: control packet only",
        "AUTHORIZED_INPUTS: ARM_INPUTS",
    ).replace(
        "ARM_INSTRUCTION: Apply the control packet constraints. No treatment overlay or profile directives are authorized.",
        "ARM_INSTRUCTION: ARM_ACTION",
    )
    normalized_treatment = treatment_prompt.replace("shape_profiled", "ARM").replace(
        "AUTHORIZED_INPUTS: control packet and treatment overlay",
        "AUTHORIZED_INPUTS: ARM_INPUTS",
    ).replace(
        "ARM_INSTRUCTION: Read the treatment overlay and apply every authoring_directive exactly once in addition to the control packet constraints.",
        "ARM_INSTRUCTION: ARM_ACTION",
    )
    assert normalized_control == normalized_treatment
    assert "AUTHORIZED_INPUTS: control packet only" in control_prompt
    assert "authoring_directives" not in control_prompt
    assert "control packet and treatment overlay" in treatment_prompt
    assert "apply every authoring_directive exactly once" in treatment_prompt
    assert "control packet only" in control_prompt
    for prompt in (control_prompt, treatment_prompt):
        assert "one authoring attempt" in prompt
        assert "TikZ only" in prompt
        assert "publication claim" in prompt
        assert "Do not assert a fixed S60 peak count" in prompt
        assert "Do not assert a monotonic disorder trend" in prompt
        assert "Do not assert how changing `n` changes decay rate or direction" in prompt
        assert "a qualitative current-decay cue remains authorized" in prompt
        assert "feedback-derived" in prompt
        assert "declared posthoc and layout contracts" in prompt
        assert "clean-room" not in prompt.lower()


def test_shape_experiment_packet_hashes_roles_forbidden_imports_and_boundary() -> None:
    packet = yaml.safe_load(PACKET.read_text(encoding="utf-8"))
    control = yaml.safe_load(SHAPE_CONTROL_PACKET.read_text(encoding="utf-8"))
    roles = [item["role"] for item in packet["authoritative_inputs"]]
    for role in (
        "shape_profile",
        "shape_experiment_model_contract",
        "shape_experiment_budget_contract",
        "shape_experiment_blank_start",
        "shape_experiment_control_packet",
        "shape_profile_treatment_overlay",
        "shape_control_authoring_prompt",
        "shape_profiled_authoring_prompt",
    ):
        assert roles.count(role) == 1
    for item in packet["authoritative_inputs"]:
        if item["role"].startswith("shape_"):
            assert item["sha256"] == _sha256(FIXTURE / item["path"])

    assert [item["role"] for item in control["authoritative_inputs"]] == [
        "briefing",
        "specification",
        "authoring_contract",
        "panel_goals",
        "semantic_boundary",
        "repaired_region_contract",
        "text_inventory_contract",
        "label_ownership_contract",
        "mutual_clearance_contract",
    ]
    for item in control["authoritative_inputs"]:
        if item["role"] in {
            "briefing",
            "specification",
            "authoring_contract",
            "panel_goals",
            "semantic_boundary",
        }:
            # This is a historical experiment packet; current authority lives
            # in authority_manifest_v2.yaml.
            assert item["sha256"].startswith("sha256:")
        else:
            assert item["sha256"] == _sha256(FIXTURE / item["path"])
    forbidden = control["forbidden_import_patterns"]
    assert forbidden == [
        "review/failure-first/*generated*",
        "review/failure-first/*render*",
        "docs/historical/fig3*",
        "examples/fig1_*",
        "experiments/python_svg_semantic_fig1",
    ]
    assert control["control_arm_profile_directives"] == "none"
    assert control["forbidden_input_enforcement"] == "prompt_only_not_runtime_enforced"
    assert control["forbidden_input_matching"] == {
        "path_basis": "repository_relative",
        "absolute_paths": "rejected",
        "dotdot_segments": "rejected",
        "symlinks": "rejected",
        "pattern_kind": "glob_interpreted_by_runner",
        "current_packet_claims_enforcement": False,
        "runtime_read_isolation": "unavailable",
        "transcript_audit": "required",
    }
    assert control["execution_receipt_requirements"] == {
        "schema": "figure-agent.shape-experiment-execution-receipt.v1",
        "receipt_location": "external_to_control_packet",
        "control_packet_binding": "receipt_must_record_control_packet_sha256",
        "arms": {
            "shape_control": {
                "required_fields": [
                    "arm_id",
                    "model_contract_sha256",
                    "budget_contract_sha256",
                    "blank_start_sha256",
                    "control_packet_sha256",
                    "prompt_sha256",
                    "transcript_sha256",
                    "generated_source_sha256",
                    "actual_token_usage_or_unavailable_with_reason",
                    "feedback_rounds",
                    "manual_repairs",
                    "forbidden_input_preflight",
                ],
                "fixed_values": {
                    "arm_id": "shape_control",
                    "feedback_rounds": 0,
                    "manual_repairs": 0,
                },
            },
            "shape_profiled": {
                "required_fields": [
                    "arm_id",
                    "model_contract_sha256",
                    "budget_contract_sha256",
                    "blank_start_sha256",
                    "control_packet_sha256",
                    "treatment_overlay_sha256",
                    "prompt_sha256",
                    "transcript_sha256",
                    "generated_source_sha256",
                    "actual_token_usage_or_unavailable_with_reason",
                    "feedback_rounds",
                    "manual_repairs",
                    "forbidden_input_preflight",
                ],
                "fixed_values": {
                    "arm_id": "shape_profiled",
                    "feedback_rounds": 0,
                    "manual_repairs": 0,
                },
            },
        },
    }
    assert "execution_receipt" not in control
    assert control["publication_acceptance"] == "not_claimed"


def test_fig3_raw_clean_room_baseline_is_hash_bound_but_not_publication_accepted() -> None:
    run = yaml.safe_load(RAW_RUN.read_text(encoding="utf-8"))
    receipt = run["generation_receipt"]

    assert run["schema"] == "figure-agent.failure-ablation-run.v1"
    assert run["variant"] == "raw"
    assert run["figure_family"] == "fig3_resistance_mechanism"
    assert run["model_contract_hash"] == _sha256(RAW_MODEL_CONTRACT)
    assert run["input_packet_hash"] == _sha256(RAW_AUTHORITY_PACKET)
    assert run["budget_contract_hash"] == _sha256(RAW_BUDGET_CONTRACT)
    assert run["clean_reproduction"] is False
    assert run["reproduction"]["project_compile"]["result"] == "blocked_by_style_lock"
    assert run["selector_registry_hash"] == _sha256(RAW_SELECTOR_REGISTRY)
    assert run["render_receipt_hash"] == _sha256(RAW_RENDER_RECEIPT)
    assert run["human_verdict"] == {"state": "pending"}
    assert run["publication_acceptance"] == "not_claimed"
    assert run["findings"] == [
        {
            "id": "RAW_STYLE_CONTRACT_MISSING",
            "failure_class": "style",
            "observation_scale": "whole",
            "review_outcome": "confirmed_defect",
            "attribution_state": "exact",
            "selector_id": "document.preamble_and_palette",
        },
        {
            "id": "RAW_SINGLE_DEEP_STATE_OMITTED",
            "failure_class": "semantic",
            "observation_scale": "panel",
            "review_outcome": "confirmed_defect",
            "attribution_state": "exact",
            "selector_id": "panel_b.s60_single_deep_state",
        },
        {
            "id": "RAW_TEXT_AND_LABEL_OVERFLOW",
            "failure_class": "geometry",
            "observation_scale": "whole",
            "review_outcome": "confirmed_defect",
            "attribution_state": "exact",
            "selector_id": "whole.layout_text_extents",
        },
    ]
    assert receipt["starting_artifact_path"] == RAW_PROMPT.name
    assert receipt["generated_artifact_path"] == RAW_SOURCE.name
    for kind, path in (("starting", RAW_PROMPT), ("generated", RAW_SOURCE)):
        assert receipt[f"{kind}_artifact_sha256"] == _sha256(path)
    transcript = RAW_RUN.with_suffix(".transcript.json")
    assert receipt["transcript_path"] == transcript.name
    assert receipt["transcript_sha256"] == _sha256(transcript)
    model_contract = yaml.safe_load(RAW_MODEL_CONTRACT.read_text(encoding="utf-8"))
    authority_packet = yaml.safe_load(RAW_AUTHORITY_PACKET.read_text(encoding="utf-8"))
    raw_source = RAW_SOURCE.read_text(encoding="utf-8")
    assert authority_packet["schema"] == "figure-agent.raw-authority-packet.v1"
    assert [item["role"] for item in authority_packet["authoritative_inputs"]] == [
        "briefing",
        "specification",
        "authoring_contract",
        "panel_goals",
    ]
    for item in authority_packet["authoritative_inputs"]:
        path = FIXTURE / item["path"]
        assert path.is_file()
        assert item["sha256"].startswith("sha256:")
        for forbidden in model_contract["forbidden_import_patterns"]:
            assert forbidden not in item["path"]
            assert forbidden not in path.read_text(encoding="utf-8")
    for forbidden in model_contract["forbidden_import_patterns"]:
        assert forbidden not in raw_source

    selectors = yaml.safe_load(RAW_SELECTOR_REGISTRY.read_text(encoding="utf-8"))
    assert selectors["source_sha256"] == _sha256(RAW_SOURCE)
    selector_ids = {item["id"] for item in selectors["selectors"]}
    assert selector_ids == {item["selector_id"] for item in run["findings"]}

    render = yaml.safe_load(RAW_RENDER_RECEIPT.read_text(encoding="utf-8"))
    assert render["input_authority_packet_sha256"] == _sha256(RAW_AUTHORITY_PACKET)
    assert render["source_sha256"] == _sha256(RAW_SOURCE)
    for output in render["outputs"]:
        assert output["sha256"] == _sha256(REVIEW / output["path"])
    assert render["publication_acceptance"] == "not_claimed"


def test_fig3_style_control_injects_only_the_paper_style_contract() -> None:
    run = yaml.safe_load(STYLE_CONTROL_RUN.read_text(encoding="utf-8"))
    source = STYLE_CONTROL_SOURCE.read_text(encoding="utf-8")
    render = yaml.safe_load(STYLE_CONTROL_RENDER_RECEIPT.read_text(encoding="utf-8"))

    assert run["schema"] == "figure-agent.style-control-run.v1"
    assert run["control_kind"] == "deterministic_style_contract_injection"
    assert run["figure_family"] == "fig3_resistance_mechanism"
    assert run["source_derivation"] == {
        "from_path": RAW_SOURCE.name,
        "from_sha256": _sha256(RAW_SOURCE),
        "permitted_transformations": [
            "paper_preamble_and_palette",
            "paper_font_hierarchy",
        ],
    }
    assert run["clean_reproduction"] is True
    assert run["human_verdict"] == {"state": "pending"}
    assert run["publication_acceptance"] == "not_claimed"
    assert "\\usepackage{polymer-paper-preamble}" in source
    assert "\\definecolor" not in source
    assert "\\tiny" not in source
    assert "\\scriptsize" not in source
    for invariant in (
        "sign-agnostic carrier",
        "repeatedly trapped / released",
        "I(t)\\propto t^{-n}",
        "S60",
        "S80",
        "$n$ = breadth",
        "magnitude",
    ):
        assert invariant in source
    assert render["source_sha256"] == _sha256(STYLE_CONTROL_SOURCE)
    for output in render["outputs"]:
        assert output["sha256"] == _sha256(REVIEW / output["path"])
    assert render["publication_acceptance"] == "not_claimed"


def test_fig3_verified_llm_retry_is_receipt_bound_to_the_same_clean_room_inputs() -> None:
    raw_run = yaml.safe_load(RAW_RUN.read_text(encoding="utf-8"))
    run = yaml.safe_load(VERIFIED_RUN.read_text(encoding="utf-8"))
    source = VERIFIED_SOURCE.read_text(encoding="utf-8")
    receipt = run["generation_receipt"]
    render = yaml.safe_load(VERIFIED_RENDER_RECEIPT.read_text(encoding="utf-8"))

    assert run["schema"] == "figure-agent.failure-ablation-run.v1"
    assert run["variant"] == "verified"
    for field in (
        "model_contract_hash",
        "input_packet_hash",
        "budget_contract_hash",
        "figure_family",
    ):
        assert run[field] == raw_run[field]
    assert run["comparison_eligibility"] == "feedback_guided_not_equal_input"
    assert run["selector_registry_hash"] == _sha256(VERIFIED_SELECTOR_REGISTRY)
    assert receipt["model_id"] == raw_run["generation_receipt"]["model_id"]
    assert receipt["source_commit"] == raw_run["generation_receipt"]["source_commit"]
    assert receipt["starting_artifact_path"] == RAW_PROMPT.name
    assert receipt["starting_artifact_sha256"] == _sha256(RAW_PROMPT)
    assert receipt["generated_artifact_path"] == VERIFIED_SOURCE.name
    assert receipt["generated_artifact_sha256"] == _sha256(VERIFIED_SOURCE)
    assert receipt["transcript_sha256"] == _sha256(VERIFIED_RUN.with_suffix(".transcript.json"))
    assert run["clean_reproduction"] is True
    assert run["human_verdict"] == {"state": "pending"}
    assert run["publication_acceptance"] == "not_claimed"
    assert "\\usepackage{polymer-paper-preamble}" in source
    assert "\\definecolor" not in source
    assert "\\tiny" not in source
    assert "\\scriptsize" not in source
    for invariant in (
        "carrier (sign-agnostic)",
        "repeated trap $\\leftrightarrow$ release",
        "I(t)\\propto t^{-n}",
        "S60",
        "single deep",
        "S80",
        "continuous broad",
        "$n$ = breadth",
        "magnitude",
    ):
        assert invariant in source
    assert render["source_sha256"] == _sha256(VERIFIED_SOURCE)
    assert render["visual_clash_candidates"] == 21
    assert render["undeclared_geometry_candidates"] == 37
    for output in render["outputs"]:
        assert output["sha256"] == _sha256(REVIEW / output["path"])
    assert render["publication_acceptance"] == "not_claimed"
    selectors = yaml.safe_load(VERIFIED_SELECTOR_REGISTRY.read_text(encoding="utf-8"))
    assert selectors["source_sha256"] == _sha256(VERIFIED_SOURCE)
    assert {item["id"] for item in selectors["selectors"]} == {
        item["selector_id"] for item in run["findings"]
    }


def test_fig3_first_verified_retry_preserves_the_style_path_failure() -> None:
    attempt = yaml.safe_load(VERIFIED_ATTEMPT1_RECORD.read_text(encoding="utf-8"))

    assert attempt == {
        "schema": "figure-agent.clean-room-attempt.v1",
        "attempt": "verified_attempt1",
        "source_path": VERIFIED_ATTEMPT1_SOURCE.name,
        "source_sha256": _sha256(VERIFIED_ATTEMPT1_SOURCE),
        "project_compile": {
            "result": "failed",
            "failure_class": "reproducibility",
            "failure": "styles/polymer-paper-preamble.sty not found from nested review path",
        },
        "publication_acceptance": "not_claimed",
    }


def test_fig3_constraint_guided_repaired_attempt_records_failure_without_ablation_claim() -> None:
    attempt = yaml.safe_load(REPAIRED_ATTEMPT.read_text(encoding="utf-8"))
    render = yaml.safe_load(REPAIRED_RENDER_RECEIPT.read_text(encoding="utf-8"))

    assert attempt["schema"] == "figure-agent.constraint-guided-attempt.v1"
    assert attempt["comparison_eligibility"] == "constraint_guided_iterative_not_ablation"
    assert attempt["input_authority_packet_sha256"] == _sha256(
        REPAIRED_AUTHORITY_PACKET
    )
    assert attempt["starting_prompt"]["sha256"] == _sha256(REPAIRED_PROMPT)
    assert attempt["generated_source"]["sha256"] == _sha256(REPAIRED_SOURCE)
    assert attempt["authoring_trace"]["feedback_rounds"] == 4
    assert attempt["machine_outcome"]["strict_compile"] == (
        "failed_detector_gate_after_render"
    )
    assert attempt["machine_outcome"]["declared_layout_lane"] == (
        "failed_0.013_lt_0.015"
    )
    assert attempt["publication_acceptance"] == "not_claimed"

    assert render["source_sha256"] == _sha256(REPAIRED_SOURCE)
    assert render["machine_findings"]["layout_lane"] == {
        "rule_id": "panel_a_narrative_clear_of_bias_marker",
        "measured_clearance": 0.013,
        "required_clearance": 0.015,
        "result": "failed",
    }
    assert render["strict_compile_result"] == "failed_detector_gate_after_render"
    for output in render["outputs"]:
        assert output["sha256"] == _sha256(REVIEW / output["path"])
    for evidence in render["evidence"]:
        assert evidence["sha256"] == _sha256(REVIEW / evidence["path"])
    assert render["publication_acceptance"] == "not_claimed"


def test_fig3_repaired_render_exposes_panel_and_plot_region_failures() -> None:
    contract = yaml.safe_load(REPAIRED_REGION_CONTRACT.read_text(encoding="utf-8"))
    report = json.loads(REPAIRED_REGION_REPORT.read_text(encoding="utf-8"))
    evaluation = yaml.safe_load(
        REPAIRED_REGION_EVALUATION.read_text(encoding="utf-8")
    )

    assert contract["schema"] == "figure-agent.layout-lanes.v1"
    assert contract["evaluation_mode"] == "posthoc_not_generation_input"
    assert report["failure_count"] == 2
    assert {
        result["rule_id"]: result["status"] for result in report["results"]
    } == {
        "panel_a_title_contained": "violation",
        "panel_a_decay_note_clear_of_plot": "violation",
    }
    assert contract["publication_acceptance"] == "not_claimed"
    assert evaluation["schema"] == "figure-agent.posthoc-layout-evaluation.v1"
    assert evaluation["source_sha256"] == _sha256(REPAIRED_SOURCE)
    assert evaluation["contract_sha256"] == _sha256(REPAIRED_REGION_CONTRACT)
    assert evaluation["report_sha256"] == _sha256(REPAIRED_REGION_REPORT)
    assert evaluation["machine_outcome"] == "failed_two_declared_region_rules"
    assert evaluation["human_verdict"] == {"state": "pending"}
    assert evaluation["publication_acceptance"] == "not_claimed"


def test_fig3_region_guided_attempt_passes_selected_rules_but_fails_strict_gate() -> None:
    attempt = yaml.safe_load(REGION_GUIDED_ATTEMPT.read_text(encoding="utf-8"))
    receipt = yaml.safe_load(
        REGION_GUIDED_RENDER_RECEIPT.read_text(encoding="utf-8")
    )

    assert attempt["schema"] == "figure-agent.region-guided-attempt.v1"
    assert attempt["comparison_eligibility"] == "region_guided_not_ablation"
    assert attempt["authority_packet_sha256"] == _sha256(
        REGION_GUIDED_AUTHORITY_PACKET
    )
    assert attempt["prompt_sha256"] == _sha256(REGION_GUIDED_PROMPT)
    assert attempt["source_sha256"] == _sha256(REGION_GUIDED_SOURCE)
    assert attempt["selected_region_rules"] == "passed_two_of_two"
    assert attempt["strict_compile"] == "failed_three_text_collisions"
    assert attempt["human_verdict"] == {
        "reviewer": "moon",
        "state": "rejected",
        "reason": "structural_and_visual_quality_insufficient",
    }
    assert attempt["publication_acceptance"] == "rejected"

    assert receipt["source_sha256"] == _sha256(REGION_GUIDED_SOURCE)
    assert receipt["strict_compile_result"] == "failed_detector_gate_after_render"
    assert receipt["machine_findings"]["collision_candidates"] == 3
    assert receipt["machine_findings"]["layout_region_rules"] == {
        "failure_count": 0,
        "result": "passed",
    }
    for output in receipt["outputs"]:
        assert output["sha256"] == _sha256(REVIEW / output["path"])
    for evidence in receipt["evidence"]:
        assert evidence["sha256"] == _sha256(REVIEW / evidence["path"])
    assert receipt["adversarial_review_sha256"] == _sha256(REGION_GUIDED_REVIEW)
    assert receipt["human_verdict"] == {
        "reviewer": "moon",
        "state": "rejected",
        "reason": "structural_and_visual_quality_insufficient",
    }
    assert receipt["publication_acceptance"] == "rejected"

    review = yaml.safe_load(REGION_GUIDED_REVIEW.read_text(encoding="utf-8"))
    assert review["human_feedback"]["reviewer"] == "moon"
    assert review["human_feedback"]["verdict"] == "rejected"
    assert set(review["human_feedback"]["confirmed_defects"]) == {
        "residual_text_overlap",
        "trap_energy_distribution_shape_is_unnatural",
        "color_system_is_unrefined",
        "figure_aspect_ratio_is_inappropriate",
        "cross_panel_visual_language_is_inconsistent",
        "excessive_figure_text",
    }


def test_fig3_region_guided_text_budget_quantifies_human_density_rejection() -> None:
    contract = yaml.safe_load(REGION_GUIDED_TEXT_CONTRACT.read_text(encoding="utf-8"))
    report = json.loads(REGION_GUIDED_TEXT_REPORT.read_text(encoding="utf-8"))

    assert contract["evaluation_mode"] == "posthoc_human_declared_editorial_budget"
    assert contract["human_authority"] == {
        "reviewer": "moon",
        "source": "rejected_region_guided_attempt_feedback",
    }
    assert report["failure_count"] == 3
    assert {
        item["budget_id"]: (item["word_count"], item["maximum_words"], item["status"])
        for item in report["text_budget_results"]
    } == {
        "figure_text_budget": (75, 45, "violation"),
        "panel_a_text_budget": (33, 22, "violation"),
        "panel_b_text_budget": (42, 23, "violation"),
    }
    assert contract["publication_acceptance"] == "rejected"


def test_fig3_region_guided_label_ownership_detects_clipped_panel_b_axis() -> None:
    contract = yaml.safe_load(
        REGION_GUIDED_LABEL_OWNERSHIP_CONTRACT.read_text(encoding="utf-8")
    )
    report = json.loads(
        REGION_GUIDED_LABEL_OWNERSHIP_REPORT.read_text(encoding="utf-8")
    )

    assert contract["evaluation_mode"] == "posthoc_required_label_ownership"
    assert contract["label_groups"] == [
        {
            "id": "panel_b_x_axis_label",
            "required_phrase": "trap energy E",
            "region": "panel_b",
        }
    ]
    assert report["failure_count"] == 1
    assert report["results"] == [
        {
            "clearance": None,
            "minimum_clearance": 0.005,
            "missing_groups": ["panel_b_x_axis_label"],
            "rule_id": "panel_b_x_axis_label_owned",
            "status": "missing_label_group",
        }
    ]
    assert contract["publication_acceptance"] == "rejected"


def test_fig3_region_guided_inventory_detects_overlapping_distribution_labels() -> None:
    contract = yaml.safe_load(
        REGION_GUIDED_MUTUAL_CLEARANCE_CONTRACT.read_text(encoding="utf-8")
    )
    report = json.loads(
        REGION_GUIDED_MUTUAL_CLEARANCE_REPORT.read_text(encoding="utf-8")
    )

    assert contract["evaluation_mode"] == "posthoc_required_label_clearance"
    assert report["failure_count"] == 1
    assert report["results"] == [
        {
            "clearance": 0.0,
            "minimum_clearance": 0.01,
            "missing_groups": [],
            "rule_id": "distribution_labels_separated",
            "status": "violation",
        }
    ]
    assert contract["publication_acceptance"] == "rejected"


def test_fig3_shape_profile_outcome_binds_failed_render_attempt() -> None:
    comparison = yaml.safe_load(SHAPE_COMPARISON.read_text(encoding="utf-8"))

    assert comparison["schema"] == "figure-agent.shape-profile-comparison.v1"
    assert comparison["intended_experiment_class"] == (
        "controlled_shape_profile_experiment_not_product_ablation"
    )
    assert comparison["comparison_eligibility"] == "execution_unbound"
    assert comparison["comparison_status"] == (
        "ineligible_execution_unbound_and_not_renderable"
    )
    assert comparison["shape_naturalness"] == (
        "blocked_not_applicable_until_new_renderable_experiment"
    )
    assert comparison["publication_acceptance"] == "not_claimed"
    assert comparison["shared_contracts"] == {
        "model_contract_sha256": _sha256(SHAPE_MODEL_CONTRACT),
        "budget_contract_sha256": _sha256(SHAPE_BUDGET_CONTRACT),
        "blank_start_sha256": _sha256(SHAPE_BLANK_START),
        "control_packet_sha256": _sha256(SHAPE_CONTROL_PACKET),
    }
    assert comparison["treatment_overlay_sha256"] == _sha256(
        SHAPE_TREATMENT_OVERLAY
    )

    expected_arm_files = {
        "shape_control": (
            SHAPE_CONTROL_PROMPT,
            SHAPE_CONTROL_SOURCE,
            "41b49492dd40345ed9d74831e05b939704288190c2b24fdc958ec6d2c02b0afb",
        ),
        "shape_profiled": (
            SHAPE_PROFILED_PROMPT,
            SHAPE_PROFILED_SOURCE,
            "a0bfc63c5de41278b77f6d60170a9ce52db3d18ca8027652f7e0cebe74ffc6ad",
        ),
    }
    for arm_id, (prompt, source, executed_prompt_hash) in expected_arm_files.items():
        arm = comparison["arms"][arm_id]
        assert arm["executed_prompt_sha256"] == f"sha256:{executed_prompt_hash}"
        assert arm["declared_prompt_file_sha256"] == _sha256(prompt)
        assert arm["generated_source_sha256"] == _sha256(source)
        assert arm["compile"] == {
            "normal_exit": 1,
            "strict_exit": 1,
            "blocking_finding": "missing_polymer_paper_preamble",
            "warnings": [
                "flagship_macros_unused",
                "extreme_local_font_size_scriptsize",
            ],
        }
        assert arm["render_outputs"] == {
            "pdf": "not_created",
            "png": "not_created",
        }
        assert arm["layout_report"] == "not_created_render_unavailable"


def test_fig3_shape_profile_execution_receipts_bind_actual_runtime_bytes() -> None:
    receipt_paths = {
        "shape_control": REVIEW / "shape_control_execution_receipt.yaml",
        "shape_profiled": REVIEW / "shape_profiled_execution_receipt.yaml",
    }
    expected_transcripts = {
        "shape_control": "sha256:d310f2801b77ee9c1a89c3986f16cda11801b9abcc22047214e8d302d29e92f2",
        "shape_profiled": "sha256:b87f2736900e1c73ad804db3fa4ceecb4778eb8879081b9ef6eb21dbbfa1628e",
    }
    for arm_id, receipt_path in receipt_paths.items():
        receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
        assert receipt["schema"] == "figure-agent.shape-experiment-execution-receipt.v1"
        assert receipt["arm_id"] == arm_id
        assert receipt["prompt_binding_status"] == (
            "mismatch_executed_inline_prompt_not_declared_prompt_file"
        )
        assert receipt["transcript_sha256"] == expected_transcripts[arm_id]
        assert receipt["actual_token_usage_or_unavailable_with_reason"] == (
            "unavailable_witnessd_codex_adapter_did_not_report_actual_usage"
        )
        assert receipt["feedback_rounds"] == 0
        assert receipt["manual_repairs"] == 0
        assert receipt["experiment_eligibility"] == "execution_unbound"


def test_fig3_shape_profile_outcome_binds_external_execution_evidence() -> None:
    comparison = yaml.safe_load(SHAPE_COMPARISON.read_text(encoding="utf-8"))
    evidence = comparison["execution_evidence"]

    assert evidence["run_path"] == (
        ".witnessd/runs/fig3-shape-profile-20260713-sequential"
    )
    assert evidence["team_ledger_sha256"] == (
        "cd318ea50e09ecb59de73ce578f280c9dfc7a80685cbaffc5250061b6ced58f0"
    )
    assert evidence["team_ledger_verdict_sha256"] == (
        "a4c1571397d88bc92d0e7c34252d01fbf30860a07a8986d969baec7e54f1e582"
    )
    assert evidence["proofcheck_verdict_sha256"] == (
        "cf519023d0ac04091aaec20f66d948fbd9266e7cd4e92fd364fbe60012bf7fe5"
    )
    assert evidence["handoff_sha256"] == (
        "3a46fd485521434802501dc5db43061b7568a19e2d757db0673207a7582e0fee"
    )
    assert evidence["report_sha256"] == (
        "44b65daa7bcee23d9c6ae6d56cf8429e4f517b1216a748c88a6d2f559b2d55a7"
    )
    assert evidence["proofcheck_scope"] == "persisted_execution_evidence_only"
    assert evidence["handoff_report_sequence_limitation"] == (
        "report_recorded_binding_mismatch_before_final_proofcheck_rerun"
    )
    assert evidence["runtime_read_isolation"] == "unavailable"
    assert evidence["transcript_audit"] == (
        "no_repository_artifact_reads_observed_global_skill_reads_only"
    )


def test_fig3_shape_profile_review_and_handoff_block_visual_judgment() -> None:
    review = yaml.safe_load(SHAPE_ADVERSARIAL_REVIEW.read_text(encoding="utf-8"))
    handoff = SHAPE_HANDOFF.read_text(encoding="utf-8")

    assert review["schema"] == "figure-agent.shape-profile-adversarial-review.v1"
    assert review["review_state"] == "blocked_no_render"
    assert review["machine_findings"]["compile"] == "failed_before_render"
    assert review["unresolved_scientific_claims"] == [
        "s60_peak_count",
        "n_to_decay_direction",
        "monotonic_disorder",
    ]
    assert [item["question"] for item in review["human_visual_questions"]] == [
        "Do the two distributions share one encoding family?",
        "Does S80 read wider without implying a measured function?",
        "Do n and rho_60s remain visually distinct?",
        "Does the panel look suitable for a contemporary paper?",
    ]
    assert all(
        item["state"] == "not_applicable_until_renderable_attempt"
        for item in review["human_visual_questions"]
    )
    assert review["publication_acceptance"] == "not_claimed"

    assert "ineligible_execution_unbound_and_not_renderable" in handoff
    assert "missing_polymer_paper_preamble" in handoff
    assert "persisted execution evidence only" in handoff
    assert "Publication acceptance is not claimed" in handoff


def test_fig3_resistance_scope_guard_checks_actual_pending_git_surface() -> None:
    scope = yaml.safe_load((REVIEW / "scope_protection.yaml").read_text(encoding="utf-8"))
    extension_paths = _scope_extension_paths()
    extensions = [yaml.safe_load(path.read_text(encoding="utf-8")) for path in extension_paths]
    extension = extensions[-1]
    base_extensions = [item for item in extensions if "scope_base_ref" in item]
    assert len(base_extensions) == 1
    base_extension = base_extensions[0]
    for index, scope_extension in enumerate(extensions):
        parent = REVIEW / scope_extension["extends"]
        expected_parent = (
            REVIEW / "scope_protection.yaml"
            if index == 0
            else extension_paths[index - 1]
        )
        assert parent == expected_parent
        assert scope_extension["extends_sha256"] == _sha256(parent)
    repo_root = PLUGIN_ROOT.parents[1]
    fixture_prefix = "plugins/figure-agent/examples/fig3_resistance_mechanism/"
    allowed_paths = {
        *(fixture_prefix + path for path in scope["allowed_review_paths"]),
        *scope["allowed_repository_paths"],
    }
    for scope_extension in extensions:
        allowed_paths.update(
            fixture_prefix + path for path in scope_extension["allowed_review_paths"]
        )
        allowed_paths.update(scope_extension["allowed_repository_paths"])
    pending_paths = _git_pending_paths(repo_root)
    branch_delta_paths = _git_branch_delta_paths(repo_root, base_extension["scope_base_ref"])
    for scope_extension in extensions:
        for prefix in scope_extension["allowed_review_prefixes"]:
            allowed_paths.update(
                path for path in pending_paths if path.startswith(fixture_prefix + prefix)
            )

    assert _scope_violations({fixture_prefix + "README.md"}, allowed_paths) == {
        fixture_prefix + "README.md"
    }
    assert extension["publication_acceptance"] == "not_claimed"
    assert _scope_violations(pending_paths | branch_delta_paths, allowed_paths) == set()


def test_fig3_current_render_review_scaffold_is_bound_and_human_baseline_recorded() -> None:
    scaffold = yaml.safe_load(CURRENT_RENDER_REVIEW_SCAFFOLD.read_text(encoding="utf-8"))

    assert scaffold["schema"] == "figure-agent.current-render-review-scaffold.v1"
    assert scaffold["fixture"] == "fig3_resistance_mechanism"
    assert scaffold["source_inputs"] == {
        "tex_sha256": _sha256(FIXTURE / "fig3_resistance_mechanism.tex"),
        "briefing_sha256": _sha256(FIXTURE / "briefing.md"),
        "spec_sha256": _sha256(FIXTURE / "spec.yaml"),
    }
    assert scaffold["machine_gate"]["strict_compile"] == "passed"
    assert scaffold["machine_gate"]["visual_clash_strict_candidates"] == 0
    assert scaffold["machine_gate"]["geometry_coverage"] == {
        "parsed_operations": 21,
        "total_operations": 25,
        "coverage_ratio": 0.84,
    }
    assert scaffold["machine_gate"]["publication_acceptance"] == "not_claimed"
    adjudication = yaml.safe_load((FIXTURE / "critique_adjudication.yaml").read_text())
    c001 = next(item for item in adjudication["decisions"] if item["finding_id"] == "C001")
    assert c001["decision"] == "resolved"
    assert scaffold["render_evidence"] == {
        "render_path": "build/fig3_resistance_mechanism.pdf",
        "render_png_path": "build/fig3_resistance_mechanism.png",
        "render_png_sha256": _sha256(FIXTURE / "build" / "fig3_resistance_mechanism.png"),
        "audit_crop_manifest": "build/audit_crops/manifest.json",
        "audit_crop_manifest_sha256": _sha256(
            FIXTURE / "build" / "audit_crops" / "manifest.json"
        ),
        "print_proxy": "build/audit_crops/print_178mm.png",
        "print_proxy_sha256": _sha256(
            FIXTURE / "build" / "audit_crops" / "print_178mm.png"
        ),
        "inspection_method": "full_render_plus_high_zoom_crops_plus_print_proxy",
    }
    assert scaffold["human_review"]["state"] == "recorded"
    assert scaffold["human_review"]["verdict"] == (
        "accepted_development_baseline_subject_to_future_editorial_revision"
    )
    assert scaffold["human_review"]["required_scope"] == (
        "development_baseline_only_not_publication_acceptance"
    )
    assert scaffold["machine_gate"]["publication_acceptance"] == "not_claimed"


def test_lh001_repair_history_preserves_failures_and_binds_resolved_attempt() -> None:
    attempts = {
        version: REVIEW / f"execution-repair-v{version}" for version in (6, 7, 8)
    }
    reviews = {
        version: json.loads(
            (root / "execution_review.json").read_text(encoding="utf-8")
        )
        for version, root in attempts.items()
    }

    assert reviews[6]["decision"] == (
        "machine_target_unresolved_human_not_requested"
    )
    assert reviews[7]["decision"] == (
        "machine_target_unresolved_human_not_requested"
    )
    assert reviews[8]["decision"] == (
        "machine_target_resolved_strict_failed_human_pending"
    )
    assert [reviews[version]["after"]["label_hyphenation"] for version in (6, 7, 8)] == [
        1,
        1,
        0,
    ]
    assert reviews[8]["strict_compile"] == "fail"
    assert reviews[8]["human_review"] == "pending"
    assert reviews[8]["publication_acceptance"] == "not_claimed"
    assert reviews[8]["generated_source_sha256"] == _sha256(
        attempts[8] / "repaired_generated.tex"
    )
    assert reviews[8]["materialization_receipt_sha256"] == _sha256(
        attempts[8] / "materialization_receipt.json"
    )


def test_detector_evaluation_keeps_one_rendered_semantic_crossing_actionable() -> None:
    evaluation_root = REVIEW / "execution-detector-evaluation-v1"
    review = json.loads(
        (evaluation_root / "evaluation_review.json").read_text(encoding="utf-8")
    )
    report = json.loads(
        (evaluation_root / "undeclared_geometry.json").read_text(encoding="utf-8")
    )

    assert review["decision"] == "detector_noise_reduced_actual_defect_remains"
    assert review["before"]["actionable_candidates"] == 15
    assert review["after"]["actionable_candidates"] == 1
    assert review["after"]["report_sha256"] == _sha256(
        evaluation_root / "undeclared_geometry.json"
    )
    assert report["profile"] == "schematic"
    assert report["total"] == 1
    assert [candidate["kind"] for candidate in report["candidates"]] == [
        "label_crosses_semantic_path"
    ]
    assert report["candidates"][0]["nearest_text"] == "landscape"
    assert review["verification"]["human_review"] == "pending"
    assert review["publication_acceptance"] == "not_claimed"


def test_execution_repair_v9_resolves_rendered_landscape_crossing() -> None:
    attempt_root = REVIEW / "execution-repair-v9"
    review = json.loads(
        (attempt_root / "execution_review.json").read_text(encoding="utf-8")
    )
    report = json.loads(
        (attempt_root / "undeclared_geometry.json").read_text(encoding="utf-8")
    )

    assert review["decision"] == "machine_target_resolved_human_pending"
    assert review["before"]["actionable_candidates"] == 1
    assert review["after"]["actionable_candidates"] == 0
    assert review["after"]["report_sha256"] == _sha256(
        attempt_root / "undeclared_geometry.json"
    )
    assert report["profile"] == "schematic"
    assert report["total"] == 0
    assert report["candidates"] == []
    assert review["verification"]["human_review"] == "pending"
    assert review["publication_acceptance"] == "not_claimed"


def test_execution_repair_v10_resolves_material_label_path_contact() -> None:
    attempt_root = REVIEW / "execution-repair-v10"
    review = json.loads(
        (attempt_root / "execution_review.json").read_text(encoding="utf-8")
    )
    report = json.loads(
        (attempt_root / "visual_clash.json").read_text(encoding="utf-8")
    )

    assert review["decision"] == "machine_target_resolved_human_pending"
    assert review["before"]["visual_clash_candidates"] == 5
    assert review["before"]["material_label_candidates"] == 4
    assert review["after"]["visual_clash_candidates"] == 1
    assert review["after"]["material_label_candidates"] == 0
    assert review["after"]["report_sha256"] == _sha256(
        attempt_root / "visual_clash.json"
    )
    assert [candidate["text"] for candidate in report["candidates"]] == ["content"]
    assert review["verification"]["strict_compile"] == "fail_one_unclassified_candidate"
    assert review["verification"]["human_review"] == "pending"
    assert review["publication_acceptance"] == "not_claimed"


def test_visual_clash_evaluation_v2_rejects_neighbor_text_luma_noise() -> None:
    evaluation_root = REVIEW / "execution-visual-clash-evaluation-v2"
    review = json.loads(
        (evaluation_root / "evaluation_review.json").read_text(encoding="utf-8")
    )
    report = json.loads(
        (evaluation_root / "visual_clash.json").read_text(encoding="utf-8")
    )

    assert review["decision"] == "detector_luma_noise_resolved_human_pending"
    assert review["before"]["visual_clash_candidates"] == 1
    source_path = _declared_fixture_path(review["source"]["path"])
    before_report_path = _declared_fixture_path(review["before"]["report_path"])
    after_report_path = _declared_fixture_path(review["after"]["report_path"])
    assert review["source"]["sha256"] == _sha256(source_path)
    assert review["before"]["report_sha256"] == _sha256(before_report_path)
    before_report = json.loads(
        before_report_path.read_text(encoding="utf-8")
    )
    assert [candidate["text"] for candidate in before_report["candidates"]] == [
        "content"
    ]
    assert review["after"]["visual_clash_candidates"] == 0
    assert after_report_path == evaluation_root / "visual_clash.json"
    assert review["after"]["report_sha256"] == _sha256(after_report_path)
    assert review["root_cause"]["class"] == (
        "neighboring_text_bbox_contaminated_luma_only_ring"
    )
    assert review["render_evidence"]["resolution_base"] == (
        "review/failure-first/execution-repair-v10"
    )
    assert review["render_evidence"]["resolved_runtime_path"] == (
        "review/failure-first/execution-repair-v10/build/repaired_generated.pdf"
    )
    assert review["render_evidence"]["tracking"] == (
        "generated_runtime_artifact_not_tracked"
    )
    assert review["render_evidence"]["raw_sha256_status"] == (
        "snapshot_only_nondeterministic"
    )
    assert review["render_evidence"]["content_signature"] == {
        "schema": "figure-agent.pdf-content-signature.v1",
        "extraction": "pdftotext-layout-trim-right-lines-v1",
        "normalized_text_sha256": (
            "sha256:2b866b14001974c016519e7fe81de9932cca25e4c13d1299ab1e69e7c514cb4a"
        ),
        "page_count": 1,
    }
    render_path = _declared_fixture_path(
        review["render_evidence"]["resolved_runtime_path"]
    )
    source_from_plugin = source_path.relative_to(PLUGIN_ROOT)
    assert review["render_evidence"]["working_directory"] == "plugins/figure-agent"
    assert review["render_evidence"]["reproduction_command"] == (
        "FIGURE_AGENT_STRICT=1 bash scripts/compile.sh " f"{source_from_plugin}"
    )
    if render_path.exists():
        assert review["render_evidence"]["content_signature"] == (
            _pdf_content_signature(render_path)
        )
    assert report["total"] == 0
    assert report["candidates"] == []
    assert review["verification"]["strict_compile"] == "pass"
    assert review["verification"]["human_review"] == "pending"
    assert review["publication_acceptance"] == "not_claimed"


@pytest.mark.render
def test_execution_scaffold_v1_exposes_boundary_and_density_failures(
    tmp_path: Path,
) -> None:
    contract = yaml.safe_load(
        (EXECUTION_SCAFFOLD_EVALUATION / "layout_contract.yaml").read_text(
            encoding="utf-8"
        )
    )
    report = json.loads(
        (EXECUTION_SCAFFOLD_EVALUATION / "layout_report.json").read_text(
            encoding="utf-8"
        )
    )
    review = json.loads(
        (EXECUTION_SCAFFOLD_EVALUATION / "evaluation_review.json").read_text(
            encoding="utf-8"
        )
    )

    assert contract["evaluation_mode"] == "posthoc_current_render_review_scaffold"
    assert contract["editorial_budget_authority"] == {
        "reviewer": "moon",
        "source": "rejected_region_guided_attempt_feedback",
    }
    assert contract["boundary_authority"] == {
        "source": "agent_v10_visual_audit",
        "status": "pending_human_confirmation",
        "proposed_minimum_normalized_inset": 0.01,
    }
    assert report["failure_count"] == 7
    assert {
        result["rule_id"]: result["status"] for result in report["results"]
    } == {
        "panel_a_decay_outcome_contained": "violation",
        "panel_b_s60_caption_contained": "violation",
        "panel_b_s80_caption_contained": "violation",
        "panel_b_sulfur_progression_contained": "violation",
        "panel_b_magnitude_label_contained": "violation",
    }
    assert {
        result["budget_id"]: (
            result["word_count"],
            result["maximum_words"],
            result["status"],
        )
        for result in report["text_budget_results"]
    } == {
        "figure_text_budget": (65, 45, "violation"),
        "panel_a_text_budget": (39, 22, "violation"),
        "panel_b_text_budget": (18, 23, "ok"),
    }
    assert review["decision"] == (
        "machine_visible_scaffold_failures_human_pending"
    )
    assert review["source"]["sha256"] == _sha256(
        _declared_fixture_path(review["source"]["path"])
    )
    assert review["contract"]["sha256"] == _sha256(
        EXECUTION_SCAFFOLD_EVALUATION / "layout_contract.yaml"
    )
    assert review["report"]["sha256"] == _sha256(
        EXECUTION_SCAFFOLD_EVALUATION / "layout_report.json"
    )
    assert review["report"]["failure_count"] == report["failure_count"]
    assert review["report"]["reproduction_command"] == (
        "python3 scripts/checks/check_layout_drift.py --pdf "
        "examples/fig3_resistance_mechanism/review/failure-first/"
        "execution-repair-v10/build/repaired_generated.pdf --layout-contract "
        "examples/fig3_resistance_mechanism/review/failure-first/"
        "execution-scaffold-evaluation-v1/layout_contract.yaml --json-output "
        "/tmp/fig3-execution-scaffold-layout-report.json --strict"
    )
    assert review["interpretation"]["universal_rule_claim"] == "not_claimed"
    assert review["interpretation"]["boundary_authority"] == (
        "pending_human_confirmation"
    )
    assert review["verification"]["strict_compile"] == "pass"
    assert review["verification"]["human_review"] == "pending"
    assert review["publication_acceptance"] == "not_claimed"

    source_path = _declared_fixture_path(review["source"]["path"])
    isolated_source = _isolated_historical_tex(tmp_path, source_path)
    compile_result = subprocess.run(
        ["bash", "scripts/compile.sh", str(isolated_source)],
        cwd=PLUGIN_ROOT,
        env={
            **os.environ,
            "FIGURE_AGENT_STRICT": "1",
            "FIGURE_AGENT_FIXTURE_NAME": "fig3_resistance_mechanism",
        },
        capture_output=True,
        text=True,
    )
    assert compile_result.returncode == 0, compile_result.stdout + compile_result.stderr
    render_path = isolated_source.parent / "build" / f"{isolated_source.stem}.pdf"
    assert _pdf_content_signature(render_path) == review["render_evidence"][
        "content_signature"
    ]

    reproduced_report = tmp_path / "layout_report.json"
    layout_result = subprocess.run(
        [
            sys.executable,
            "scripts/checks/check_layout_drift.py",
            "--pdf",
            str(render_path),
            "--layout-contract",
            str(EXECUTION_SCAFFOLD_EVALUATION / "layout_contract.yaml"),
            "--json-output",
            str(reproduced_report),
            "--strict",
        ],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
    )
    assert layout_result.returncode == 1
    assert json.loads(reproduced_report.read_text(encoding="utf-8")) == report


@pytest.mark.render
def test_execution_repair_v11_contains_labels_without_reducing_text(
    tmp_path: Path,
) -> None:
    attempt_root = REVIEW / "execution-repair-v11"
    source = attempt_root / "repaired_generated.tex"
    report_path = attempt_root / "layout_report.json"
    visual_path = attempt_root / "visual_clash.json"
    review = json.loads(
        (attempt_root / "execution_review.json").read_text(encoding="utf-8")
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    visual = json.loads(visual_path.read_text(encoding="utf-8"))

    assert review["decision"] == "boundary_targets_resolved_density_human_pending"
    assert review["source"]["based_on"] == (
        "review/failure-first/execution-repair-v10/repaired_generated.tex"
    )
    based_on_source = _declared_fixture_path(review["source"]["based_on"])
    assert review["source"]["based_on_sha256"] == _sha256(based_on_source)
    assert review["source"]["sha256"] == _sha256(source)
    assert review["contract"]["sha256"] == _sha256(
        EXECUTION_SCAFFOLD_EVALUATION / "layout_contract.yaml"
    )
    assert review["before"]["evidence_sha256"] == _sha256(
        EXECUTION_SCAFFOLD_EVALUATION / "layout_report.json"
    )
    assert {
        key: review["before"][key]
        for key in ("findings", "boundary_findings", "density_findings")
    } == {"findings": 7, "boundary_findings": 5, "density_findings": 2}
    assert review["after"]["findings"] == 3
    assert review["after"]["boundary_findings"] == 0
    assert review["after"]["density_findings"] == 3
    assert review["after"]["newly_exposed_density_debt"] == (
        "panel_b_ownership_restoration_raises_count_from_18_to_26"
    )
    assert review["after"]["layout_report_sha256"] == _sha256(report_path)
    assert review["after"]["visual_clash_sha256"] == _sha256(visual_path)
    assert review["verification"]["strict_compile"] == "pass"
    assert review["verification"]["human_review"] == "pending"
    assert review["boundary_authority"] == "pending_human_confirmation"
    assert review["agent_visual_review"]["scientific_semantics"] == (
        "visual_ownership_pending_human_confirmation"
    )
    assert review["agent_visual_review"]["magnitude_label"] == (
        "detached_floating_key_clear_of_baseline_and_distributions"
    )
    assert "magnitude_key_visual_ownership_pending_human_confirmation" in (
        review["remaining_blockers"]
    )
    assert review["publication_acceptance"] == "not_claimed"
    assert visual["total"] == 0
    assert visual["candidates"] == []

    assert report["failure_count"] == 3
    baseline_report = json.loads(
        (EXECUTION_SCAFFOLD_EVALUATION / "layout_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["page_size_pt"] == baseline_report["page_size_pt"]
    assert {result["status"] for result in report["results"]} == {"ok"}
    assert {
        result["budget_id"]: (result["word_count"], result["status"])
        for result in report["text_budget_results"]
    } == {
        "figure_text_budget": (65, "violation"),
        "panel_a_text_budget": (39, "violation"),
        "panel_b_text_budget": (26, "violation"),
    }

    isolated_based_on_source = _isolated_historical_tex(tmp_path, based_on_source)
    isolated_source = _isolated_historical_tex(tmp_path, source)
    render_path = isolated_source.parent / "build" / "repaired_generated.pdf"
    based_on_render_path = (
        isolated_based_on_source.parent / "build" / "repaired_generated.pdf"
    )
    based_on_compile_result = subprocess.run(
        ["bash", "scripts/compile.sh", str(isolated_based_on_source)],
        cwd=PLUGIN_ROOT,
        env={
            **os.environ,
            "FIGURE_AGENT_STRICT": "1",
            "FIGURE_AGENT_FIXTURE_NAME": "fig3_resistance_mechanism",
        },
        capture_output=True,
        text=True,
    )
    assert based_on_compile_result.returncode == 0, (
        based_on_compile_result.stdout + based_on_compile_result.stderr
    )
    compile_result = subprocess.run(
        ["bash", "scripts/compile.sh", str(isolated_source)],
        cwd=PLUGIN_ROOT,
        env={
            **os.environ,
            "FIGURE_AGENT_STRICT": "1",
            "FIGURE_AGENT_FIXTURE_NAME": "fig3_resistance_mechanism",
        },
        capture_output=True,
        text=True,
    )
    assert compile_result.returncode == 0, compile_result.stdout + compile_result.stderr
    assert review["render_evidence"]["content_signature"] == (
        _pdf_content_signature(render_path)
    )
    assert _pdf_normalized_token_inventory(render_path) == (
        _pdf_normalized_token_inventory(based_on_render_path)
    )
    assert review["reproduction"]["strict_compile_command"] == (
        "FIGURE_AGENT_STRICT=1 bash scripts/compile.sh "
        "examples/fig3_resistance_mechanism/review/failure-first/"
        "execution-repair-v11/repaired_generated.tex"
    )

    reproduced_report = tmp_path / "layout_report.json"
    layout_result = subprocess.run(
        [
            sys.executable,
            "scripts/checks/check_layout_drift.py",
            "--pdf",
            str(render_path),
            "--layout-contract",
            str(EXECUTION_SCAFFOLD_EVALUATION / "layout_contract.yaml"),
            "--json-output",
            str(reproduced_report),
            "--strict",
        ],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
    )
    assert layout_result.returncode == 1
    assert json.loads(reproduced_report.read_text(encoding="utf-8")) == report
    assert review["reproduction"]["layout_command"] == (
        "python3 scripts/checks/check_layout_drift.py --pdf "
        "examples/fig3_resistance_mechanism/review/failure-first/"
        "execution-repair-v11/build/repaired_generated.pdf --layout-contract "
        "examples/fig3_resistance_mechanism/review/failure-first/"
        "execution-scaffold-evaluation-v1/layout_contract.yaml --json-output "
        "/tmp/fig3-execution-repair-v11-layout-report.json --strict"
    )


@pytest.mark.render
def test_execution_repair_v12_resolves_density_with_visual_semantics_pending(
    tmp_path: Path,
) -> None:
    attempt_root = REVIEW / "execution-repair-v12"
    source = attempt_root / "repaired_generated.tex"
    report_path = attempt_root / "layout_report.json"
    raw_visual_path = attempt_root / "raw_visual_clash.json"
    visual_path = attempt_root / "visual_clash.json"
    review = json.loads(
        (attempt_root / "execution_review.json").read_text(encoding="utf-8")
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    raw_visual = json.loads(raw_visual_path.read_text(encoding="utf-8"))
    visual = json.loads(visual_path.read_text(encoding="utf-8"))
    tex = source.read_text(encoding="utf-8")

    assert review["decision"] == "machine_density_targets_resolved_human_pending"
    assert review["source"]["based_on"] == (
        "review/failure-first/execution-repair-v11/repaired_generated.tex"
    )
    based_on_source = _declared_fixture_path(review["source"]["based_on"])
    assert review["source"]["based_on_sha256"] == _sha256(based_on_source)
    assert review["source"]["sha256"] == _sha256(source)
    assert review["contract"]["sha256"] == _sha256(
        EXECUTION_SCAFFOLD_EVALUATION / "layout_contract.yaml"
    )
    assert review["before"]["evidence_sha256"] == _sha256(
        REVIEW / "execution-repair-v11/layout_report.json"
    )
    assert review["after"]["layout_report_sha256"] == _sha256(report_path)
    assert review["after"]["raw_visual_clash_sha256"] == _sha256(raw_visual_path)
    assert review["after"]["visual_clash_sha256"] == _sha256(visual_path)
    assert review["after"]["findings"] == 0
    assert review["after"]["boundary_findings"] == 0
    assert review["after"]["density_findings"] == 0
    assert review["after"]["text_budgets"] == {
        "figure": 45,
        "panel_a": 22,
        "panel_b": 23,
    }
    assert review["verification"]["strict_compile"] == "pass"
    assert review["verification"]["layout_strict"] == "pass"
    assert review["verification"]["v12_voltage_suppression_used"] is False
    assert review["verification"]["human_review"] == "pending"
    assert review["semantic_preservation"] == "not_claimed_pending_human_review"
    assert review["agent_visual_review"]["voltage_ownership"] == "human_pending"
    assert review["agent_visual_review"]["capture_release_glyph_grammar"] == (
        "human_pending"
    )
    assert review["agent_visual_review"]["magnitude_ownership"] == "human_pending"
    assert review["agent_visual_review"]["s60_shallow_deep_nuance"] == (
        "human_review_item"
    )
    assert review["publication_acceptance"] == "not_claimed"
    assert "voltage_ownership_human_review_pending" in review["remaining_blockers"]
    assert "capture_release_glyph_grammar_human_review_pending" in (
        review["remaining_blockers"]
    )

    assert report["failure_count"] == 0
    baseline_report = json.loads(
        (EXECUTION_SCAFFOLD_EVALUATION / "layout_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["page_size_pt"] == baseline_report["page_size_pt"]
    assert {result["status"] for result in report["results"]} == {"ok"}
    assert {
        result["budget_id"]: (result["word_count"], result["status"])
        for result in report["text_budget_results"]
    } == {
        "figure_text_budget": (45, "ok"),
        "panel_a_text_budget": (22, "ok"),
        "panel_b_text_budget": (23, "ok"),
    }
    assert visual["total"] == 0
    assert visual["candidates"] == []
    assert all(candidate["text"] != "V" for candidate in raw_visual["candidates"])

    assert "{$\\times$}" not in tex
    assert "×" not in tex
    assert tex.count("% vector trap cross") == 9
    assert tex.count("\\draw[trap]") == 18
    assert tex.count("% red capture ring") == 4
    assert tex.count("\\draw[cRed, line width=0.42pt]") == 4
    assert "% red capture mark" not in tex
    assert "{electrode}" not in tex
    assert "{trapping during conduction}" in tex
    assert "{disordered sulfur-polymer film}" in tex
    assert "{sign-agnostic carrier: capture/release}" in tex
    assert "increasing sulfur content" not in tex
    assert tex.count("{V}") == 1
    voltage_cue = tex[tex.index("  \\path[draw=cGray!85!black") : tex.index(
        "disordered sulfur-polymer film"
    )]
    assert "Stealth" not in voltage_cue
    for polarity_token in ("{+}", "{-}", "{$+$}", "{$-$}"):
        assert polarity_token not in voltage_cue
    for source_invariant in (
        "\\useasboundingbox (0,0) rectangle (14.152435,4.500765);",
        "minimum width=7.20cm, minimum height=4.25cm",
        "minimum width=5.85cm, minimum height=4.25cm",
        "(0.96,2.18) -- (1.24,2.43) -- (1.58,2.08) -- (1.92,2.54)",
        "-- (2.18,1.82) -- (2.48,2.02) -- (2.78,1.56) -- (3.10,1.88)",
        "-- (3.36,1.52);",
        "(0.66,2.04) -- (0.66,3.08) -- (1.80,3.24);",
        "(3.94,2.04) -- (3.94,3.08) -- (2.80,3.24);",
        "(1.80,3.24) circle (0.04cm);",
        "(2.80,3.24) circle (0.04cm);",
        "(1.24,2.43) circle (0.12cm);",
        "(1.92,2.54) circle (0.12cm);",
        "(2.48,2.02) circle (0.12cm);",
        "(3.10,1.88) circle (0.12cm);",
        "at (0.50,3.25) {S60 $\\rightarrow$\\quad S80};",
    ):
        assert source_invariant in tex
    for protected in (
        "$I(t)$",
        "$I \\propto t^{-n}$",
        "current decays",
        "$\\Rightarrow R$ rises",
        "trap-energy landscape",
        "$g(E)$",
        "trap energy $E$",
        "{S60}",
        "discrete\\\\single deep",
        "{S80}",
        "continuous\\\\broad",
        "$n$ = breadth",
        "$\\rho_{60s}$\\\\magnitude",
    ):
        assert protected in tex

    isolated_source = _isolated_historical_tex(tmp_path, source)
    render_path = isolated_source.parent / "build" / "repaired_generated.pdf"
    compile_result = subprocess.run(
        ["bash", "scripts/compile.sh", str(isolated_source)],
        cwd=PLUGIN_ROOT,
        env={
            **os.environ,
            "FIGURE_AGENT_STRICT": "1",
            "FIGURE_AGENT_FIXTURE_NAME": "fig3_resistance_mechanism",
        },
        capture_output=True,
        text=True,
    )
    assert compile_result.returncode == 0, compile_result.stdout + compile_result.stderr
    assert review["render_evidence"]["content_signature"] == (
        _pdf_content_signature(render_path)
    )
    extracted_text = subprocess.run(
        ["pdftotext", "-layout", str(render_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "disordered sulfur-polymer film" in extracted_text
    assert "disordered sulfur-\npolymer film" not in extracted_text
    assert "×" not in extracted_text

    reproduced_report = tmp_path / "layout_report.json"
    layout_result = subprocess.run(
        [
            sys.executable,
            "scripts/checks/check_layout_drift.py",
            "--pdf",
            str(render_path),
            "--layout-contract",
            str(EXECUTION_SCAFFOLD_EVALUATION / "layout_contract.yaml"),
            "--json-output",
            str(reproduced_report),
            "--strict",
        ],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
    )
    assert layout_result.returncode == 0, layout_result.stdout + layout_result.stderr
    assert json.loads(reproduced_report.read_text(encoding="utf-8")) == report

    reproduced_raw_visual = tmp_path / "raw_visual_clash.json"
    raw_visual_result = subprocess.run(
        [
            sys.executable,
            "scripts/checks/check_visual_clash.py",
            str(render_path),
            "--no-ignore-known-fp",
            "--fixture",
            "fig3_resistance_mechanism",
            "--json-output",
            str(reproduced_raw_visual),
        ],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
    )
    assert raw_visual_result.returncode == 0
    assert json.loads(reproduced_raw_visual.read_text(encoding="utf-8")) == raw_visual
    assert all(candidate["text"] != "V" for candidate in raw_visual["candidates"])

    geometry_report = tmp_path / "undeclared_geometry.json"
    geometry_result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python3",
            "scripts/checks/check_undeclared_geometry.py",
            str(render_path),
            "--tex",
            str(source),
                "--spec",
                str(FIXTURE / "spec.yaml"),
                "--json-output",
                str(geometry_report),
            ],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
    )
    # The repair source is immutable historical evidence. Its source-level
    # report remains reproducible, but a later live coverage floor must not
    # retroactively turn that replay into a strict failure.
    assert geometry_result.returncode == 0, geometry_result.stdout + geometry_result.stderr
    assert json.loads(geometry_report.read_text(encoding="utf-8"))["total"] == 0


@pytest.mark.render
def test_fig3_resistance_render_receipt_reproduces_current_source_outputs() -> None:
    receipt = _compile_receipt_outputs()
    command = ["bash", "scripts/compile.sh", "examples/fig3_resistance_mechanism/fig3_resistance_mechanism.tex"]

    assert receipt["schema"] == "figure-agent.compile-render-receipt.v1"
    assert receipt["fixture"] == "fig3_resistance_mechanism"
    assert receipt["compile_command"] == command
    assert receipt["working_directory"] == "plugins/figure-agent"
    assert receipt["source_path"] == "fig3_resistance_mechanism.tex"
    assert receipt["pdf_path"] == "build/fig3_resistance_mechanism.pdf"
    assert receipt["png_path"] == "build/fig3_resistance_mechanism.png"
    assert receipt["raw_pdf_sha256_status"] == "snapshot_only_nondeterministic"
    assert receipt["toolchain"]["latex_engine"] == "lualatex"
    assert receipt["toolchain"]["lualatex_version"]
    assert receipt["toolchain"]["pdftocairo_version"]
    assert _tool_version(["lualatex", "--version"])
    assert _tool_version(["pdftocairo", "-v"])

    packet = yaml.safe_load(PACKET.read_text(encoding="utf-8"))
    packet_by_role = {item["role"]: item for item in packet["authoritative_inputs"]}
    # The original packet is immutable evidence. The additive authority
    # manifest and this receipt bind the current three-column source.
    assert packet_by_role["editable_source"]["sha256"] != receipt["source_sha256"]
    assert packet_by_role["rendered_png"]["sha256"] != receipt["png_sha256"]
    manifest = yaml.safe_load(AUTHORITY_MANIFEST_V2.read_text(encoding="utf-8"))
    manifest_by_role = {item["role"]: item for item in manifest["authoritative_inputs"]}
    assert manifest_by_role["editable_source"]["sha256"] == receipt["source_sha256"]
    assert receipt["source_sha256"] == _sha256(FIXTURE / receipt["source_path"])

    pdf_path = FIXTURE / receipt["pdf_path"]
    png_path = FIXTURE / receipt["png_path"]
    assert pdf_path.read_bytes().startswith(b"%PDF-")
    assert png_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert _pdf_content_signature(pdf_path) == receipt["pdf_content_signature"]
    assert _sha256(png_path) == receipt["png_sha256"]


def test_fig3_execution_binding_packets_are_additive_and_equal_input() -> None:
    historical_hashes = {
        SHAPE_CONTROL_SOURCE: "sha256:46e58f500368471a491b9cf5cfbf36dc2fdad3b1a5013ba7cd6e43b445dddfc2",
        SHAPE_PROFILED_SOURCE: "sha256:0314182b8f2bbbcf107000d4d806934368ab49f00b5e14f54a1deefeafa5c2a9",
        SHAPE_CONTROL_PROMPT: "sha256:ecaf28ee4d5e8c1b05ad098cba5747391620ea5e981b4c5877c47c46f32a13a7",
        SHAPE_PROFILED_PROMPT: "sha256:c1554202da35fdee1702c275b930463bf6055b10a2f51b9eb5cfbfcebf6b2944",
    }
    assert {path: _sha256(path) for path in historical_hashes} == historical_hashes

    control = json.loads((EXECUTION_BINDING / "control_packet.json").read_text())
    treatment = json.loads((EXECUTION_BINDING / "treatment_packet.json").read_text())
    preflight = json.loads((EXECUTION_BINDING / "preflight.json").read_text())
    for field in (
        "model_id",
        "budget_contract",
        "blank_start",
        "mandatory_source_requirements",
        "feedback_rounds",
        "manual_repairs",
        "publication_acceptance",
    ):
        assert control[field] == treatment[field]
    assert control["context_pack"]["base_sha256"] == treatment["context_pack"][
        "base_sha256"
    ]
    assert control["shape_profile"] is None
    assert treatment["shape_profile"]["path"] == "shape_profile_panel_b.yaml"
    assert control["output_path"] != treatment["output_path"]
    for arm in ("control", "treatment"):
        prompt = (EXECUTION_BINDING / f"{arm}_prompt.md").read_text(encoding="utf-8")
        assert r"\usepackage{polymer-paper-preamble}" in prompt
        assert prompt == (control if arm == "control" else treatment)["prompt"]["utf8"]
    assert preflight["schema"] == "figure-agent.authoring-execution-preflight.v1"
    assert preflight["decision"] == "pass"
    assert preflight["filesystem_read_isolation"] == "unavailable"


def test_fig3_execution_binding_v1_was_blocked_before_model_execution() -> None:
    review = json.loads(
        (EXECUTION_BINDING_V1 / "prompt_context_review.json").read_text(
            encoding="utf-8"
        )
    )
    assert review["decision"] == "blocked"
    assert review["reason"] == "binding_fixture_briefing_omitted_from_prompt"
    assert review["model_execution_started"] is False
    assert review["superseded_by"] == "execution-binding-v2"


def test_fig3_execution_binding_prompt_carries_the_binding_briefing() -> None:
    prompt = (EXECUTION_BINDING / "treatment_prompt.md").read_text(encoding="utf-8")
    assert "n = the BREADTH of the trap energy distribution" in prompt
    assert "Carrier is sign-agnostic" in prompt
    assert "(a) cell + transport + decay" in prompt
    assert "(b) g(E) evolution" in prompt


def test_fig3_execution_binding_v4_receipts_bind_repository_transcripts() -> None:
    for arm in ("control", "treatment"):
        receipt = json.loads(
            (EXECUTION_BINDING_V4 / f"{arm}_receipt.json").read_text(
                encoding="utf-8"
            )
        )
        source = EXECUTION_BINDING_V4 / f"{arm}_generated.tex"

        assert receipt["schema"] == "figure-agent.authoring-execution-receipt.v1"
        assert receipt["transcript_root"] == "repository"
        assert receipt["generated_source_sha256"] == _sha256(source)
        assert receipt["touched_files"] == [
            "plugins/figure-agent/examples/fig3_resistance_mechanism/review/"
            f"failure-first/execution-binding-v4/{arm}_generated.tex"
        ]
        assert receipt["actual_model_id"] == "gpt-5.5"
        assert receipt["feedback_rounds"] == 0
        assert receipt["manual_repairs"] == 0
        assert receipt["publication_acceptance"] == "not_claimed"


def test_fig3_execution_binding_v4_blocks_comparison_and_visual_acceptance() -> None:
    review = json.loads(
        (EXECUTION_BINDING_V4 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert review["comparison_eligibility"] == "ineligible"
    assert review["decision"] == "blocked"
    assert review["control"]["compile"]["normal_exit_code"] == 0
    assert review["control"]["compile"]["strict_exit_code"] == 1
    assert review["treatment"]["compile"]["normal_exit_code"] == 0
    assert review["treatment"]["compile"]["strict_exit_code"] == 1
    assert review["control"]["compile"]["style_lock_blockers"] == []
    assert review["treatment"]["compile"]["style_lock_blockers"] == []
    assert "input_contaminated" in review["treatment"]["execution_state"]
    assert review["control"]["input_audit"]["decision"] == "pass"
    assert review["treatment"]["input_audit"] == {
        "artifact": "treatment_input_audit.json",
        "decision": "blocked",
        "undeclared_repository_reads": [
            "docs/execution-plan.md",
            "docs/product-spec.md",
        ],
    }
    assert review["shape_naturalness"] == "pending_human_review"
    assert review["publication_acceptance"] == "not_claimed"

    control_audit = json.loads(
        (EXECUTION_BINDING_V4 / "control_input_audit.json").read_text(
            encoding="utf-8"
        )
    )
    treatment_audit = json.loads(
        (EXECUTION_BINDING_V4 / "treatment_input_audit.json").read_text(
            encoding="utf-8"
        )
    )
    assert control_audit["decision"] == "pass"
    assert treatment_audit["decision"] == "blocked"
    assert treatment_audit["undeclared_repository_reads"] == [
        "docs/execution-plan.md",
        "docs/product-spec.md",
    ]


def test_fig3_execution_binding_v5_records_path_routing_failure() -> None:
    review = json.loads(
        (EXECUTION_BINDING_V5 / "routing_review.json").read_text(encoding="utf-8")
    )
    control_audit = json.loads(
        (EXECUTION_BINDING_V5 / "control_input_audit_v2.json").read_text(
            encoding="utf-8"
        )
    )
    treatment_audit = json.loads(
        (EXECUTION_BINDING_V5 / "treatment_input_audit_v2.json").read_text(
            encoding="utf-8"
        )
    )

    assert review["comparison_eligibility"] == "ineligible"
    assert review["decision"] == "blocked"
    assert review["control"]["routing_decision"] == (
        "blocked_wrong_output_and_read_coordinate_system"
    )
    assert review["control"]["compile"] == "not_run_expected_packet_path_missing"
    assert review["treatment"]["compile"] == {
        "normal_exit_code": 0,
        "strict_collision_count": 3,
        "strict_exit_code": 1,
    }
    assert control_audit["decision"] == "blocked"
    assert control_audit["undeclared_repository_reads"] == [
        "AGENTS.md",
        "styles/polymer-paper-preamble.sty",
    ]
    assert treatment_audit["decision"] == "pass"
    assert treatment_audit["observed_repository_reads"] == [
        "plugins/figure-agent/AGENTS.md",
        "plugins/figure-agent/styles/polymer-paper-preamble.sty",
    ]
    assert review["publication_acceptance"] == "not_claimed"
    assert not (
        PLUGIN_ROOT.parents[1]
        / "examples/fig3_resistance_mechanism/review/failure-first/"
        "execution-binding-v5/control_generated.tex"
    ).exists()


def test_fig3_execution_binding_v5_preflight_binds_repository_read_allowlist() -> None:
    control = json.loads(
        (EXECUTION_BINDING_V5 / "control_packet.json").read_text(encoding="utf-8")
    )
    treatment = json.loads(
        (EXECUTION_BINDING_V5 / "treatment_packet.json").read_text(encoding="utf-8")
    )
    preflight = json.loads(
        (EXECUTION_BINDING_V5 / "preflight.json").read_text(encoding="utf-8")
    )

    for packet in (control, treatment):
        assert packet["allowed_repository_read_paths"] == [
            "AGENTS.md",
            "styles/polymer-paper-preamble.sty",
        ]
        assert "Read repository file content only from [AGENTS.md]" in packet[
            "prompt"
        ]["utf8"]
    assert preflight["decision"] == "pass"
    assert preflight["control"]["packet_sha256"] == control["packet_sha256"]
    assert preflight["treatment"]["packet_sha256"] == treatment["packet_sha256"]
    assert control["shape_profile"] is None
    assert treatment["shape_profile"]["path"] == "shape_profile_panel_b.yaml"


def test_fig3_execution_binding_v6_uses_one_repository_coordinate_system() -> None:
    control = json.loads(
        (EXECUTION_BINDING_V6 / "control_packet.json").read_text(encoding="utf-8")
    )
    treatment = json.loads(
        (EXECUTION_BINDING_V6 / "treatment_packet.json").read_text(encoding="utf-8")
    )
    preflight = json.loads(
        (EXECUTION_BINDING_V6 / "preflight.json").read_text(encoding="utf-8")
    )

    for arm, packet in (("control", control), ("treatment", treatment)):
        expected_output = (
            "plugins/figure-agent/examples/fig3_resistance_mechanism/review/"
            f"failure-first/execution-binding-v6/{arm}_generated.tex"
        )
        assert packet["repository_output_path"] == expected_output
        assert packet["allowed_repository_read_paths"] == [
            "plugins/figure-agent/AGENTS.md",
            "plugins/figure-agent/styles/polymer-paper-preamble.sty",
        ]
        assert f"Write exactly one new source to [{expected_output}]." in packet[
            "prompt"
        ]["utf8"]
        assert "Do not change directory before resolving paths." in packet["prompt"][
            "utf8"
        ]
        assert "Before resolving the output path, change directory" not in packet[
            "prompt"
        ]["utf8"]
    assert control["context_pack"]["base_sha256"] == treatment["context_pack"][
        "base_sha256"
    ]
    assert control["shape_profile"] is None
    assert treatment["shape_profile"]["path"] == "shape_profile_panel_b.yaml"
    assert preflight["decision"] == "pass"


def test_fig3_execution_binding_v6_receipts_bind_clean_inputs_and_exact_outputs() -> None:
    expected_reads = [
        "plugins/figure-agent/AGENTS.md",
        "plugins/figure-agent/styles/polymer-paper-preamble.sty",
    ]
    for arm in ("control", "treatment"):
        source = EXECUTION_BINDING_V6 / f"{arm}_generated.tex"
        receipt = json.loads(
            (EXECUTION_BINDING_V6 / f"{arm}_receipt.json").read_text(
                encoding="utf-8"
            )
        )
        audit = json.loads(
            (EXECUTION_BINDING_V6 / f"{arm}_input_audit.json").read_text(
                encoding="utf-8"
            )
        )

        assert receipt["schema"] == "figure-agent.authoring-execution-receipt.v1"
        assert receipt["transcript_root"] == "repository"
        assert receipt["generated_source_sha256"] == _sha256(source)
        assert receipt["touched_files"] == [
            "plugins/figure-agent/examples/fig3_resistance_mechanism/review/"
            f"failure-first/execution-binding-v6/{arm}_generated.tex"
        ]
        assert receipt["actual_model_id"] == "gpt-5.5"
        assert receipt["feedback_rounds"] == 0
        assert receipt["manual_repairs"] == 0
        assert receipt["forbidden_input_audit"] == (
            "pass_declared_repository_reads_only"
        )
        assert receipt["publication_acceptance"] == "not_claimed"
        assert audit["decision"] == "pass"
        assert audit["observed_repository_reads"] == expected_reads
        assert audit["undeclared_repository_reads"] == []


def test_fig3_execution_binding_v6_records_machine_limits_and_human_gate() -> None:
    review = json.loads(
        (EXECUTION_BINDING_V6 / "execution_review.json").read_text(encoding="utf-8")
    )

    assert review["comparison_eligibility"] == "ineligible"
    assert review["decision"] == "blocked"
    assert review["control"]["orro"]["decision"] == "pass"
    assert review["treatment"]["orro"]["decision"] == "blocked-explicit"
    assert review["control"]["compile"] == {
        "label_hyphenation_count": 0,
        "normal_exit_code": 0,
        "strict_collision_count": 11,
        "strict_exit_code": 1,
        "style_lock_blockers": [],
        "style_lock_warnings": [
            "flagship_macros_unused",
            "label_fill_source_order",
        ],
    }
    assert review["treatment"]["compile"] == {
        "label_hyphenation_count": 1,
        "normal_exit_code": 0,
        "strict_collision_count": 5,
        "strict_exit_code": 1,
        "style_lock_blockers": [],
        "style_lock_warnings": [
            "flagship_macros_unused",
            "label_fill_source_order",
        ],
    }
    assert review["parallel_compile_incident"]["invalid_results"] == "discarded"
    assert review["shape_naturalness"] == "pending_human_review"
    assert review["publication_acceptance"] == "not_claimed"
