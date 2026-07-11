from __future__ import annotations

import hashlib
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

    packet = build_review_packet(
        comparator,
        candidate,
        tmp_path / "public",
        seed="run-01",
        private_manifest_path=tmp_path / "private" / "key.yaml",
    )

    assert set(packet["public_options"]) == {"A", "B"}
    assert "tikz" not in json.dumps(packet["public_manifest"]).lower()
    assert "direct-svg" not in json.dumps(packet["public_manifest"]).lower()
    assert packet["blinding_key"]["assignments"]["A"] != packet["blinding_key"][
        "assignments"
    ]["B"]
    public_path = tmp_path / "public" / "public-review-manifest.yaml"
    assert yaml.safe_load(public_path.read_text(encoding="utf-8")) == packet[
        "public_manifest"
    ]
    raw_hashes = {
        f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
        for path in (comparator, candidate)
    }
    assert not raw_hashes & {
        item["sha256"] for item in packet["public_options"].values()
    }
    assert set(packet["blinding_key"]["content_sha256"]) == {"A", "B"}


def test_diagnostics_are_excluded_from_score_inputs(tmp_path: Path) -> None:
    comparator = _write_png(tmp_path / "comparator.png", (240, 240, 240))
    candidate = _write_png(tmp_path / "candidate.png", (230, 235, 240))

    packet = build_review_packet(
        comparator,
        candidate,
        tmp_path / "public",
        seed="run-02",
        private_manifest_path=tmp_path / "private" / "key.yaml",
    )

    public = packet["public_manifest"]
    assert {item["role"] for item in public["score_inputs"]} == {
        "opaque_option_A",
        "opaque_option_B",
    }
    assert all(item["diagnostic_only"] is True for item in public["diagnostics"])
    assert not {
        item["path"] for item in public["diagnostics"]
    } & {item["path"] for item in public["score_inputs"]}


def test_review_packet_rejects_geometry_mismatch_by_default(tmp_path: Path) -> None:
    comparator = _write_png(tmp_path / "authority.png", (240, 240, 240))
    candidate = tmp_path / "option.png"
    Image.new("RGB", (60, 80), (20, 30, 40)).save(candidate, format="PNG")

    with pytest.raises(DirectSvgReviewError, match="review_geometry_mismatch"):
        build_review_packet(
            comparator,
            candidate,
            tmp_path / "public",
            seed="geometry-exact",
            private_manifest_path=tmp_path / "private" / "key.yaml",
        )


def test_contain_policy_preserves_aspect_and_centers_on_white_canvas(
    tmp_path: Path,
) -> None:
    comparator = _write_png(tmp_path / "authority.png", (240, 240, 240))
    candidate = tmp_path / "option.png"
    Image.new("RGB", (60, 80), (20, 30, 40)).save(candidate, format="PNG")

    packet = build_review_packet(
        comparator,
        candidate,
        tmp_path / "public",
        seed="geometry-contain",
        private_manifest_path=tmp_path / "private" / "key.yaml",
        candidate_normalization_policy="contain_white_pad_authority_size.v1",
    )

    normalized_paths = [
        tmp_path / "public" / item["path"]
        for item in packet["public_options"].values()
    ]
    assert all(Image.open(path).size == (120, 80) for path in normalized_paths)
    assert any(Image.open(path).getpixel((0, 40)) == (255, 255, 255) for path in normalized_paths)
    toolchain = packet["public_manifest"]["toolchain"]
    assert toolchain["normalization"]["policy_set"] == [
        "exact_authority_size.v1",
        "contain_white_pad_authority_size.v1",
    ]
    assert toolchain["normalization"]["application"] == "opaque"


def test_private_manifest_is_separate_and_public_hashes_are_deterministic(
    tmp_path: Path,
) -> None:
    comparator = _write_png(tmp_path / "authority.png", (240, 240, 240))
    candidate = _write_png(tmp_path / "option.png", (20, 30, 40))
    packets = []
    for name in ("one", "two"):
        packets.append(
            build_review_packet(
                comparator,
                candidate,
                tmp_path / name / "public",
                seed="stable-seed",
                private_manifest_path=tmp_path / name / "private" / "key.yaml",
            )
        )

    assert not list((tmp_path / "one" / "public").glob("*private*"))
    assert packets[0]["public_manifest"] == packets[1]["public_manifest"]
    assert (
        packets[0]["public_manifest_path"].read_bytes()
        == packets[1]["public_manifest_path"].read_bytes()
    )


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
