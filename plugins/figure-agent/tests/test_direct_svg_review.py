from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from direct_svg_review import (
    DirectSvgReviewError,
    build_review_packet,
    classify_panel_verdict,
    classify_quality_hypothesis,
    panel_verdict,
    validate_review_verdict,
)
from PIL import Image


def _write_png(path: Path, color: tuple[int, int, int]) -> Path:
    Image.new("RGB", (120, 80), color).save(path, format="PNG")
    return path


def test_review_packet_uses_opaque_options(tmp_path: Path) -> None:
    comparator = _write_png(tmp_path / "tikz-comparator.png", (240, 240, 240))
    candidate = _write_png(tmp_path / "direct-svg-candidate.png", (230, 235, 240))

    packet = build_review_packet(comparator, candidate, tmp_path / "review", seed="run-01")

    assert set(packet["public_options"]) == {"A", "B"}
    assert "tikz" not in json.dumps(packet["public_manifest"]).lower()
    assert "direct-svg" not in json.dumps(packet["public_manifest"]).lower()
    assert packet["blinding_key"]["assignments"]["A"] != packet["blinding_key"][
        "assignments"
    ]["B"]
    public_path = tmp_path / "review" / "public-review-manifest.yaml"
    assert yaml.safe_load(public_path.read_text(encoding="utf-8")) == packet[
        "public_manifest"
    ]


def test_diagnostics_are_excluded_from_score_inputs(tmp_path: Path) -> None:
    comparator = _write_png(tmp_path / "comparator.png", (240, 240, 240))
    candidate = _write_png(tmp_path / "candidate.png", (230, 235, 240))

    packet = build_review_packet(comparator, candidate, tmp_path / "review", seed="run-02")

    public = packet["public_manifest"]
    assert {item["role"] for item in public["score_inputs"]} == {
        "opaque_option_A",
        "opaque_option_B",
    }
    assert all(item["diagnostic_only"] is True for item in public["diagnostics"])
    assert not {
        item["path"] for item in public["diagnostics"]
    } & {item["path"] for item in public["score_inputs"]}


def test_scientific_failure_cannot_be_compensated_by_visual_scores() -> None:
    verdict = panel_verdict(
        scientific_fidelity="fail",
        composition="better",
        illustration_quality="better",
        typography="better",
    )

    assert classify_panel_verdict(verdict) == "rejected_scientific_fidelity"


def test_panel_is_better_only_when_no_visual_dimension_is_worse() -> None:
    verdict = panel_verdict(
        scientific_fidelity="pass",
        composition="better",
        illustration_quality="equivalent",
        typography="worse",
    )

    assert classify_panel_verdict(verdict) == "worse"


def test_quality_pass_requires_both_panels_no_worse_and_one_better() -> None:
    assert classify_quality_hypothesis({"C": "equivalent", "F": "better"}) == "passed"
    assert classify_quality_hypothesis({"C": "worse", "F": "better"}) == "failed"
    assert (
        classify_quality_hypothesis({"C": "equivalent", "F": "equivalent"})
        == "not_demonstrated"
    )


def _complete_review_verdict() -> dict[str, object]:
    return {
        "schema": "figure-agent.direct-svg-review-verdict.v1",
        "reviewers": [{"name": "Reviewer One", "reviewed_at": "2026-07-11"}],
        "panels": {
            "C": panel_verdict(
                scientific_fidelity="pass",
                scientific_evidence="bound semantic review notes for Panel C",
                composition="equivalent",
                illustration_quality="equivalent",
                typography="equivalent",
            ),
            "F": panel_verdict(
                scientific_fidelity="pass",
                scientific_evidence="bound semantic review notes for Panel F",
                composition="better",
                illustration_quality="equivalent",
                typography="equivalent",
            ),
        },
        "editability_cost": {
            "verdict": "better",
            "evidence": "live text and bounded correction ledger",
        },
        "borderline": False,
        "second_review_required": False,
        "cold_run_count": 0,
        "review_input_hash": "sha256:" + "a" * 64,
        "publication_acceptance": "not_claimed",
    }


def test_borderline_verdict_requires_second_named_reviewer() -> None:
    verdict = _complete_review_verdict()
    verdict["borderline"] = True
    verdict["second_review_required"] = True

    with pytest.raises(DirectSvgReviewError, match="second_reviewer_required"):
        validate_review_verdict(verdict)


def test_review_verdict_keeps_editability_separate_from_quality() -> None:
    verdict = _complete_review_verdict()

    result = validate_review_verdict(verdict)

    assert result["quality_hypothesis"] == "passed"
    assert result["editability_cost"]["verdict"] == "better"
    assert result["publication_acceptance"] == "not_claimed"


def test_review_verdict_requires_bound_review_input_hash() -> None:
    verdict = _complete_review_verdict()
    del verdict["review_input_hash"]

    with pytest.raises(DirectSvgReviewError, match="review_input_hash_invalid"):
        validate_review_verdict(verdict)
