from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "quality"))

import agent_next  # noqa: E402
import promotion_wiring  # noqa: E402
import quality_defect_ledger  # noqa: E402
import semantic_assertions  # noqa: E402
import status  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fixture(workspace: Path, name: str = "fig_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text(
        "% Panel A\n\\node at (0,0) {Energy};\n% Panel E\n\\node at (1,1) {ISPD};\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        "name: fig_demo\n"
        "panels:\n"
        "  - id: A\n"
        "  - id: E\n"
        "tex_assertions:\n"
        "  - id: force-repels\n"
        "    anchor_style: forceArr\n"
        "    axis: x\n"
        "    direction: decreasing\n",
        encoding="utf-8",
    )
    return fixture


def _write_crop(fixture: Path, item_id: str = "VC012") -> Path:
    crop = fixture / "build" / "audit_crops" / "visual_clash" / f"{item_id}_Energy.png"
    crop.parent.mkdir(parents=True, exist_ok=True)
    crop.write_bytes(b"fake-png")
    return crop


def _visual_clash_payload() -> dict:
    return {
        "fixture": "fig_demo",
        "render_pdf": "build/fig_demo.pdf",
        "total": 1,
        "candidates": [
            {
                "id": "VC012",
                "kind": "text_overlap",
                "text": "Energy",
                "bbox_px": [10, 20, 30, 40],
                "metric": {"dark_overlap_ratio": 0.91},
                "tex_lines": None,
            }
        ],
    }


def _semantic_assertions_payload(fixture: Path) -> dict:
    return {
        "schema": "figure-agent.semantic-assertions.v1",
        "render_pdf": "build/fig_demo.pdf",
        "checked": 1,
        "issues": [
            {
                "id": "row-subtitle-baseline",
                "status": "violated",
                "message": "baseline delta 8pt exceeds tolerance",
                "kind": "baseline_aligned",
                "targets": ["kinetic", "ISPD", "mechanical"],
                "edit_target": "ISPD",
                "target_panel": "E",
                "measured_delta_pt": 8.0,
                "measured_delta_cm": 8.0 / (72.0 / 2.54),
                "tolerance_cm": 0.05,
                "tolerance_pt": 0.05 * (72.0 / 2.54),
            }
        ],
        "total": 1,
        "source_hashes": promotion_wiring._current_source_hashes(fixture, "fig_demo"),
    }


def _word(text: str, x: float, y: float) -> dict:
    return {"text": text, "xmin": x, "ymin": y, "xmax": x + 10.0, "ymax": y + 5.0}


def _semantic_report_from_words(fixture: Path, words: list[dict]) -> dict:
    spec = {
        "semantic_assertions": [
            {
                "id": "row-subtitle-baseline",
                "kind": "baseline_aligned",
                "targets": ["kinetic", "ISPD", "mechanical"],
                "target_panel": "E",
            }
        ]
    }
    assertions = semantic_assertions.parse_assertions(spec)
    issues = semantic_assertions.check_semantic_assertions(words, assertions)
    return {
        "schema": "figure-agent.semantic-assertions.v1",
        "render_pdf": "build/fig_demo.pdf",
        "checked": 1,
        "issues": issues,
        "total": len(issues),
        "source_hashes": promotion_wiring._current_source_hashes(fixture, "fig_demo"),
    }

def _vector_clearance_payload(fixture: Path, *, conservative: bool = False) -> dict:
    issue = {
        "id": "declared-crossing",
        "status": "violated",
        "relation": "must_not_cross",
        "element_a": "VE001",
        "element_b": "VE002",
        "element_a_kind": "line",
        "element_b_kind": "circle" if conservative else "line",
        "measured_clearance_cm": 0.0,
        "non_auto_promotable": conservative,
        "promotion_tier": "review_queue" if conservative else "auto",
        "message": "declared vector crossing",
    }
    return {
        "schema": "figure-agent.vector-clearance.v1",
        "render_pdf": "build/fig_demo.pdf",
        "checked": 1,
        "issues": [issue],
        "total": 1,
        "source_hashes": promotion_wiring._current_source_hashes(fixture, "fig_demo"),
    }


def test_tex_assertions_is_auto_promote_eligible_when_fail_closed_and_p5() -> None:
    state = promotion_wiring.detector_promotion_eligibility("tex_assertions")

    assert state["detector"] == "tex_assertions"
    assert state["promotion_tier"] == "auto"
    assert state["eligible"] is True
    assert state["fail_closed"] is True
    assert state["p5_zero_match"] is True
    assert state["p5_multi_match"] is True


def test_semantic_assertions_auto_promoted_after_p5() -> None:
    state = promotion_wiring.detector_promotion_eligibility("semantic_assertions")

    assert state["detector"] == "semantic_assertions"
    assert state["promotion_tier"] == "auto"
    assert state["eligible"] is True
    assert state["fail_closed"] is True
    assert state["p5_zero_match"] is True
    assert state["p5_multi_match"] is True
    assert state["blocking_reasons"] == []


def test_vector_clearance_report_missing_corrupt_wrong_schema_fail_loud(
    tmp_path: Path,
) -> None:
    with pytest.raises(promotion_wiring.PromotionWiringError, match="vector_clearance_missing"):
        promotion_wiring.load_detector_report(tmp_path / "missing.json", "vector_clearance")

    corrupt = tmp_path / "vector_clearance.json"
    corrupt.write_text("{not-json", encoding="utf-8")
    with pytest.raises(
        promotion_wiring.PromotionWiringError,
        match="vector_clearance_unreadable",
    ):
        promotion_wiring.load_detector_report(corrupt, "vector_clearance")

    wrong = tmp_path / "wrong.json"
    _write_json(wrong, {"schema": "wrong", "issues": []})
    with pytest.raises(promotion_wiring.PromotionWiringError, match="vector_clearance_schema"):
        promotion_wiring.load_detector_report(wrong, "vector_clearance")


def test_auto_promoted_vector_clearance_reaches_quality_ledger(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_json(fixture / "build" / "vector_clearance.json", _vector_clearance_payload(fixture))

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
    )

    defect = next(
        item for item in ledger["defects"] if item.get("source_detector") == "vector_clearance"
    )
    assert defect["promoted_by"] == "auto"
    assert defect["defect_class"] == "vector_clearance_violation"
    assert defect["suggested_change"]["operation_type"] == "human_review_required"
    assert defect["evidence"][0]["measured_clearance_cm"] == 0.0


def test_conservative_vector_clearance_is_not_auto_promoted(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_json(
        fixture / "build" / "vector_clearance.json",
        _vector_clearance_payload(fixture, conservative=True),
    )

    defects = promotion_wiring.auto_promoted_defects(fixture, "fig_demo")

    assert [item for item in defects if item["source_detector"] == "vector_clearance"] == []


def test_non_promoting_detectors_are_recorded_as_intentional() -> None:
    notes = promotion_wiring.non_promoting_detector_notes()

    assert notes["layout_drift"]["promotion_tier"] == "non_promoting"
    assert notes["hyphenation"]["promotion_tier"] == "non_promoting"
    assert notes["physics_grounding"]["promotion_tier"] == "non_promoting"
    assert "advisory" in notes["layout_drift"]["reason"]


def test_detector_report_loader_fails_loud_for_missing_corrupt_and_wrong_schema(
    tmp_path: Path,
) -> None:
    with pytest.raises(promotion_wiring.PromotionWiringError, match="tex_assertions_missing"):
        promotion_wiring.load_detector_report(tmp_path / "missing.json", "tex_assertions")

    corrupt = tmp_path / "tex_assertions.json"
    corrupt.write_text("{not-json", encoding="utf-8")
    with pytest.raises(promotion_wiring.PromotionWiringError, match="tex_assertions_unreadable"):
        promotion_wiring.load_detector_report(corrupt, "tex_assertions")

    wrong = tmp_path / "wrong.json"
    _write_json(wrong, {"schema": "wrong", "issues": []})
    with pytest.raises(promotion_wiring.PromotionWiringError, match="tex_assertions_schema"):
        promotion_wiring.load_detector_report(wrong, "tex_assertions")


def test_auto_promoted_tex_assertion_carries_trust_tier_provenance(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_json(
        fixture / "build" / "tex_assertions.json",
        {
            "schema": "figure-agent.tex-assertions.v1",
            "issues": [
                {
                    "id": "force-repels",
                    "status": "violated",
                    "message": "arrow reversed",
                    "measured_delta_cm": -0.42,
                }
            ],
            "total": 1,
            "checked": 1,
            "source_tex": "fig_demo.tex",
            "source_hashes": promotion_wiring._current_source_hashes(fixture, "fig_demo"),
        },
    )

    defects = promotion_wiring.auto_promoted_defects(fixture, "fig_demo")

    assert defects[0]["promoted_by"] == "auto"
    assert defects[0]["source_detector"] == "tex_assertions"
    assert defects[0]["evidence"][0]["measured_delta_cm"] == -0.42
    assert defects[0]["freshness"]["state"] == "fresh"


def test_auto_promoted_semantic_alignment_uses_label_offset_edit_family(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _write_json(
        fixture / "build" / "semantic_assertions.json",
        _semantic_assertions_payload(fixture),
    )

    defects = promotion_wiring.auto_promoted_defects(fixture, "fig_demo")

    defect = next(item for item in defects if item["source_detector"] == "semantic_assertions")
    assert defect["promoted_by"] == "auto"
    assert defect["defect_class"] == "label_offset"
    assert defect["suggested_change"]["operation_type"] == "bounded_coordinate_offset"
    assert defect["evidence"][0]["measured_delta_cm"] == pytest.approx(8.0 / (72.0 / 2.54))
    assert defect["selector_hint"]["kind"] == "line_range"
    assert defect["selector_hint"]["value"] == "4:4"
    assert defect["selector_hint"]["selector_text_hash"].startswith("sha256:")
    assert defect["target"]["panel"] == "E"
    assert defect["freshness"]["state"] == "fresh"


def test_semantic_alignment_auto_promotion_is_candidate_supported_in_ledger(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _write_json(
        fixture / "build" / "semantic_assertions.json",
        _semantic_assertions_payload(fixture),
    )

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
    )

    defect = next(
        item for item in ledger["defects"] if item["source_detector"] == "semantic_assertions"
    )
    assert defect["actionability"]["state"] == "candidate_supported"
    assert defect["selector_hint"]["kind"] == "line_range"
    assert defect["selector_hint"]["selector_text_hash"].startswith("sha256:")


def test_semantic_alignment_detector_output_targets_unique_outlier_label(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    report = _semantic_report_from_words(
        fixture,
        [
            _word("kinetic", 10, 100.0),
            _word("ISPD", 40, 92.0),
            _word("mechanical", 80, 100.0),
        ],
    )
    _write_json(fixture / "build" / "semantic_assertions.json", report)

    defects = promotion_wiring.auto_promoted_defects(fixture, "fig_demo")

    defect = next(item for item in defects if item["source_detector"] == "semantic_assertions")
    assert defect["evidence"][0]["edit_target"] == "ISPD"
    assert defect["selector_hint"]["value"] == "4:4"
    assert defect["suggested_change"]["operation_type"] == "bounded_coordinate_offset"


def test_semantic_alignment_without_unique_outlier_stays_human_review(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    report = _semantic_report_from_words(
        fixture,
        [
            _word("kinetic", 10, 100.0),
            _word("ISPD", 40, 92.0),
            _word("mechanical", 80, 108.0),
        ],
    )
    _write_json(fixture / "build" / "semantic_assertions.json", report)

    defects = promotion_wiring.auto_promoted_defects(fixture, "fig_demo")

    defect = next(item for item in defects if item["source_detector"] == "semantic_assertions")
    assert "edit_target" not in defect["evidence"][0]
    assert defect["selector_hint"] == {"kind": "assertion_id", "value": "row-subtitle-baseline"}
    assert defect["defect_class"] == "semantic_assertion_violation"
    assert defect["suggested_change"]["operation_type"] == "human_review_required"


def test_semantic_assertions_report_missing_corrupt_wrong_schema_fail_loud(
    tmp_path: Path,
) -> None:
    with pytest.raises(promotion_wiring.PromotionWiringError, match="semantic_assertions_missing"):
        promotion_wiring.load_detector_report(tmp_path / "missing.json", "semantic_assertions")

    corrupt = tmp_path / "semantic_assertions.json"
    corrupt.write_text("{not-json", encoding="utf-8")
    with pytest.raises(
        promotion_wiring.PromotionWiringError,
        match="semantic_assertions_unreadable",
    ):
        promotion_wiring.load_detector_report(corrupt, "semantic_assertions")

    wrong = tmp_path / "wrong.json"
    _write_json(wrong, {"schema": "wrong", "issues": []})
    with pytest.raises(promotion_wiring.PromotionWiringError, match="semantic_assertions_schema"):
        promotion_wiring.load_detector_report(wrong, "semantic_assertions")


def test_semantic_assertions_source_hash_mismatch_fails_loud(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    payload = _semantic_assertions_payload(fixture)
    payload["source_hashes"] = {"examples/fig_demo/fig_demo.tex": "sha256:" + "0" * 64}
    _write_json(fixture / "build" / "semantic_assertions.json", payload)

    with pytest.raises(
        promotion_wiring.PromotionWiringError,
        match="semantic_assertions_source_hash_mismatch",
    ):
        promotion_wiring.auto_promoted_defects(fixture, "fig_demo")


def test_missing_tex_assertions_report_does_not_auto_promote(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    (fixture / "spec.yaml").write_text(
        "name: fig_demo\n"
        "panels:\n"
        "  - id: A\n"
        "tex_assertions:\n"
        "  - id: force-repels\n"
        "    anchor_style: forceArr\n"
        "    axis: x\n"
        "    direction: decreasing\n",
        encoding="utf-8",
    )

    assert promotion_wiring.auto_promoted_defects(fixture, "fig_demo") == []


def test_tex_assertions_source_hash_mismatch_fails_loud(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_json(
        fixture / "build" / "tex_assertions.json",
        {
            "schema": "figure-agent.tex-assertions.v1",
            "source_tex": "fig_demo.tex",
            "source_hashes": {"examples/fig_demo/fig_demo.tex": "sha256:" + "0" * 64},
            "issues": [
                {
                    "id": "force-repels",
                    "status": "violated",
                    "message": "arrow reversed",
                }
            ],
            "total": 1,
            "checked": 1,
        },
    )

    with pytest.raises(
        promotion_wiring.PromotionWiringError,
        match="tex_assertions_source_hash_mismatch",
    ):
        promotion_wiring.auto_promoted_defects(fixture, "fig_demo")


def test_clean_tex_assertions_source_hash_mismatch_fails_loud(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_json(
        fixture / "build" / "tex_assertions.json",
        {
            "schema": "figure-agent.tex-assertions.v1",
            "source_tex": "fig_demo.tex",
            "source_hashes": {"examples/fig_demo/fig_demo.tex": "sha256:" + "0" * 64},
            "issues": [],
            "total": 0,
            "checked": 1,
        },
    )

    with pytest.raises(
        promotion_wiring.PromotionWiringError,
        match="tex_assertions_source_hash_mismatch",
    ):
        promotion_wiring.auto_promoted_defects(fixture, "fig_demo")


def test_tex_assertions_checked_count_mismatch_fails_loud(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_json(
        fixture / "build" / "tex_assertions.json",
        {
            "schema": "figure-agent.tex-assertions.v1",
            "source_tex": "fig_demo.tex",
            "source_hashes": promotion_wiring._current_source_hashes(fixture, "fig_demo"),
            "issues": [],
            "total": 0,
            "checked": 0,
        },
    )

    with pytest.raises(
        promotion_wiring.PromotionWiringError,
        match="tex_assertions_checked_count_mismatch",
    ):
        promotion_wiring.auto_promoted_defects(fixture, "fig_demo")


def test_tex_assertion_count_includes_applicable_named_endpoint_contracts(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    (fixture / "spec.yaml").write_text(
        (fixture / "spec.yaml").read_text(encoding="utf-8")
        + "named_endpoint_assertions:\n"
        + "  - id: carrier-path-endpoints\n"
        + "    source_name: fig_demo.tex\n"
        + "    anchor_style: forceArr\n"
        + "    minimum_paths: 1\n"
        + "    required_anchors: [left, right]\n"
        + "    allowed_anchors: [left, right]\n",
        encoding="utf-8",
    )
    _write_json(
        fixture / "build" / "tex_assertions.json",
        {
            "schema": "figure-agent.tex-assertions.v1",
            "source_tex": "fig_demo.tex",
            "source_hashes": promotion_wiring._current_source_hashes(fixture, "fig_demo"),
            "issues": [],
            "total": 0,
            "checked": 2,
        },
    )

    assert promotion_wiring.auto_promoted_defects(fixture, "fig_demo") == []


def test_tex_assertions_total_must_match_issue_count(tmp_path: Path) -> None:
    report = tmp_path / "tex_assertions.json"
    _write_json(
        report,
        {
            "schema": "figure-agent.tex-assertions.v1",
            "issues": [],
            "total": 1,
            "checked": 1,
        },
    )

    with pytest.raises(promotion_wiring.PromotionWiringError, match="tex_assertions_schema:total"):
        promotion_wiring.load_detector_report(report, "tex_assertions")


def test_promotion_queue_contains_inline_crop_evidence_and_non_promoting_notes(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _write_crop(fixture)
    _write_json(fixture / "build" / "visual_clash.json", _visual_clash_payload())

    queue = promotion_wiring.build_promotion_queue(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
        write=True,
    )

    assert queue["schema"] == "figure-agent.promotion-queue.v1"
    assert queue["top_items"] == ["VC012"]
    assert queue["items"][0]["evidence_inline"][0]["path"].endswith("VC012_Energy.png")
    assert queue["items"][0]["tex_lines"] == [2, 2]
    assert queue["items"][0]["source_attribution"] == {
        "state": "exact",
        "reason": "unique_literal_text_in_panel_block",
        "panel": "A",
        "tex_lines": [2, 2],
    }
    assert queue["items"][0]["defect_class"] is None
    assert {item["detector"] for item in queue["non_promoting_detectors"]} == {
        "layout_drift",
        "hyphenation",
        "physics_grounding",
    }


def test_promotion_queue_fails_loud_when_crop_evidence_is_missing(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_json(fixture / "build" / "visual_clash.json", _visual_clash_payload())

    with pytest.raises(
        promotion_wiring.PromotionWiringError,
        match="promotion_queue_missing_crop:VC012",
    ):
        promotion_wiring.build_promotion_queue(
            "fig_demo",
            plugin_root=ROOT,
            workspace_root=tmp_path,
            write=True,
        )


def test_promotion_queue_loader_fails_loud_for_corrupt_or_wrong_schema(tmp_path: Path) -> None:
    corrupt = tmp_path / "promotion_queue.json"
    corrupt.write_text("[not-object]", encoding="utf-8")
    with pytest.raises(promotion_wiring.PromotionWiringError, match="promotion_queue_unreadable"):
        promotion_wiring.load_promotion_queue(corrupt)

    _write_json(corrupt, {"schema": "wrong", "items": []})
    with pytest.raises(promotion_wiring.PromotionWiringError, match="promotion_queue_schema"):
        promotion_wiring.load_promotion_queue(corrupt)


def test_triage_accept_synthesizes_bounded_fields_and_ledger_reads_them(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _write_crop(fixture)
    _write_json(fixture / "build" / "visual_clash.json", _visual_clash_payload())
    promotion_wiring.build_promotion_queue(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
        write=True,
    )

    triage = promotion_wiring.triage_promotion_queue(
        "fig_demo",
        accept="VC012",
        reject_rest=True,
        tex_lines=["VC012:2:2"],
        defect_classes=["VC012:text_overlap"],
        plugin_root=ROOT,
        workspace_root=tmp_path,
    )
    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
    )

    assert triage["accepted"][0]["promoted_by"] == "triage"
    defect = next(
        item for item in ledger["defects"] if item.get("source_detector") == "visual_clash"
    )
    assert defect["promoted_by"] == "triage"
    assert defect["defect_class"] == "text_overlap"
    assert defect["selector_hint"]["kind"] == "line_range"
    assert defect["selector_hint"]["value"] == "2:2"
    assert defect["selector_hint"]["selector_text_hash"].startswith("sha256:")
    assert defect["target"]["panel"] == "A"
    assert defect["actionability"]["state"] == "candidate_supported"


def test_triage_accept_reuses_exact_queue_source_attribution(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_crop(fixture)
    _write_json(fixture / "build" / "visual_clash.json", _visual_clash_payload())
    promotion_wiring.build_promotion_queue(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
        write=True,
    )

    triage = promotion_wiring.triage_promotion_queue(
        "fig_demo",
        accept="VC012",
        reject_rest=True,
        tex_lines=[],
        defect_classes=["VC012:text_overlap"],
        plugin_root=ROOT,
        workspace_root=tmp_path,
    )

    assert triage["accepted"][0]["tex_lines"] == [2, 2]
    assert triage["accepted"][0]["target"]["panel"] == "A"


def test_promotion_queue_does_not_guess_when_candidate_text_is_duplicated(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    source = fixture / "fig_demo.tex"
    source.write_text(
        source.read_text(encoding="utf-8") + "\\node at (2,2) {Energy};\n",
        encoding="utf-8",
    )
    _write_crop(fixture)
    _write_json(fixture / "build" / "visual_clash.json", _visual_clash_payload())

    queue = promotion_wiring.build_promotion_queue(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
    )

    item = queue["items"][0]
    assert item["tex_lines"] is None
    assert item["source_attribution"]["state"] == "ambiguous"
    assert item["source_attribution"]["reason"] == "literal_text_matches_multiple_lines"


def test_promotion_queue_supports_explicit_prospective_attempt_directory(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    attempt = fixture / "review" / "failure-first" / "comparable-v3"
    attempt.mkdir(parents=True)
    (attempt / "verified_generated.tex").write_text(
        "% Panel A\n\\node at (0,0) {Energy};\n",
        encoding="utf-8",
    )
    _write_json(attempt / "build" / "visual_clash.json", _visual_clash_payload())
    crop = attempt / "build" / "perception" / "visual_findings" / "crops" / "VC012.png"
    crop.parent.mkdir(parents=True)
    crop.write_bytes(b"prospective-crop")

    queue = promotion_wiring.build_promotion_queue(
        "fig_demo",
        attempt_dir="review/failure-first/comparable-v3",
        plugin_root=ROOT,
        workspace_root=tmp_path,
        write=True,
    )

    assert queue["attempt_dir"] == "review/failure-first/comparable-v3"
    assert list(queue["source_hashes"]) == [
        "examples/fig_demo/review/failure-first/comparable-v3/verified_generated.tex"
    ]
    assert queue["items"][0]["crop_paths"] == [
        "build/perception/visual_findings/crops/VC012.png"
    ]
    assert (attempt / "build" / "promotion_queue.json").is_file()


def test_triage_accept_hashes_multi_line_tex_range_before_ledger_reads_it(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _write_crop(fixture)
    _write_json(fixture / "build" / "visual_clash.json", _visual_clash_payload())
    promotion_wiring.build_promotion_queue(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
        write=True,
    )

    triage = promotion_wiring.triage_promotion_queue(
        "fig_demo",
        accept="VC012",
        reject_rest=True,
        tex_lines=["VC012:1:2"],
        defect_classes=["VC012:text_overlap"],
        plugin_root=ROOT,
        workspace_root=tmp_path,
    )
    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
    )

    selector_hint = triage["accepted"][0]["selector_hint"]
    assert selector_hint["value"] == "1:2"
    assert selector_hint["selector_text_hash"].startswith("sha256:")
    defect = next(
        item for item in ledger["defects"] if item.get("source_detector") == "visual_clash"
    )
    assert defect["selector_hint"]["value"] == "1:2"
    assert defect["actionability"]["state"] == "candidate_supported"


def test_triage_promoted_defects_requires_current_queue_and_detector_report(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _write_json(
        fixture / "build" / "promotion_triage.json",
        {
            "schema": "figure-agent.promotion-triage.v1",
            "fixture": "fig_demo",
            "promotion_queue_sha256": "sha256:" + "0" * 64,
            "visual_clash_report_sha256": "sha256:" + "0" * 64,
            "source_hashes": promotion_wiring._current_source_hashes(fixture, "fig_demo"),
            "accepted": [],
            "rejected": [],
        },
    )

    with pytest.raises(promotion_wiring.PromotionWiringError, match="promotion_queue_missing"):
        promotion_wiring.triage_promoted_defects(fixture, "fig_demo")


def test_triage_promoted_defects_rejects_stale_queue_hash(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_crop(fixture)
    _write_json(fixture / "build" / "visual_clash.json", _visual_clash_payload())
    promotion_wiring.build_promotion_queue(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
        write=True,
    )
    promotion_wiring.triage_promotion_queue(
        "fig_demo",
        accept="VC012",
        reject_rest=True,
        tex_lines=["VC012:2:2"],
        defect_classes=["VC012:text_overlap"],
        plugin_root=ROOT,
        workspace_root=tmp_path,
    )
    queue_path = fixture / "build" / "promotion_queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    queue["top_items"] = []
    _write_json(queue_path, queue)

    with pytest.raises(
        promotion_wiring.PromotionWiringError,
        match="promotion_triage_queue_hash_mismatch",
    ):
        promotion_wiring.triage_promoted_defects(fixture, "fig_demo")


def test_triage_promoted_defects_rebuilds_evidence_from_queue(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_crop(fixture)
    _write_json(fixture / "build" / "visual_clash.json", _visual_clash_payload())
    promotion_wiring.build_promotion_queue(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
        write=True,
    )
    promotion_wiring.triage_promotion_queue(
        "fig_demo",
        accept="VC012",
        reject_rest=True,
        tex_lines=["VC012:2:2"],
        defect_classes=["VC012:text_overlap"],
        plugin_root=ROOT,
        workspace_root=tmp_path,
    )
    triage_path = fixture / "build" / "promotion_triage.json"
    triage = json.loads(triage_path.read_text(encoding="utf-8"))
    triage["accepted"][0]["evidence"] = [
        {"uri": "figure://fig_demo/audit/tampered", "node_id": "wrong"}
    ]
    _write_json(triage_path, triage)

    defects = promotion_wiring.triage_promoted_defects(fixture, "fig_demo")

    assert defects[0]["evidence"][0]["uri"] == "figure://fig_demo/audit/visual-clash"
    assert defects[0]["evidence"][0]["node_id"] == "VC012"
    assert defects[0]["evidence"][0]["evidence_inline"][0]["path"].endswith(
        "VC012_Energy.png"
    )


def test_triage_accept_requires_inline_crop_evidence(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_json(fixture / "build" / "visual_clash.json", _visual_clash_payload())
    _write_json(
        fixture / "build" / "promotion_queue.json",
        {
            "schema": "figure-agent.promotion-queue.v1",
            "fixture": "fig_demo",
            "source_detector": "visual_clash",
            "source_hashes": promotion_wiring._current_source_hashes(fixture, "fig_demo"),
            "visual_clash_report_sha256": promotion_wiring._hash_file(
                fixture / "build" / "visual_clash.json"
            ),
            "status": "review_required",
            "total": 1,
            "top_items": ["VC012"],
            "items": [
                {
                    "id": "VC012",
                    "source_detector": "visual_clash",
                    "promotion_tier": "review_queue",
                    "bbox_px": [10, 20, 30, 40],
                    "crop_paths": [],
                    "evidence_inline": [],
                }
            ],
        },
    )

    with pytest.raises(
        promotion_wiring.PromotionWiringError,
        match="triage_missing_evidence_crop:VC012",
    ):
        promotion_wiring.triage_promotion_queue(
            "fig_demo",
            accept="VC012",
            reject_rest=True,
            tex_lines=["VC012:2:2"],
            defect_classes=["VC012:text_overlap"],
            plugin_root=ROOT,
            workspace_root=tmp_path,
        )


def test_status_and_next_surface_promotion_queue(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_json(
        fixture / "build" / "promotion_queue.json",
        {
            "schema": "figure-agent.promotion-queue.v1",
            "fixture": "fig_demo",
            "status": "review_required",
            "total": 1,
            "top_items": ["VC012"],
            "items": [{"id": "VC012"}],
        },
    )

    status_payload = status.infer_stage(fixture)
    next_payload = agent_next.build_next("fig_demo", plugin_root=ROOT, workspace_root=tmp_path)

    assert status_payload["promotion_queue"]["total"] == 1
    assert status_payload["promotion_queue"]["top_items"] == ["VC012"]
    assert next_payload["next"]["action"] == "promotion_queue_triage"
    assert next_payload["next"]["requires_human"] is True


def test_vc012_cli_e2e_flows_from_queue_to_triage_to_quality_map(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_crop(fixture)
    _write_json(fixture / "build" / "visual_clash.json", _visual_clash_payload())
    env = {
        **os.environ,
        "FIGURE_AGENT_PLUGIN_ROOT": str(ROOT),
        "FIGURE_AGENT_WORKSPACE": str(tmp_path),
    }

    queue = subprocess.run(
        [str(ROOT / "bin" / "fig-agent"), "promotion-queue", "fig_demo", "--write", "--json"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert queue.returncode == 0, queue.stderr
    assert json.loads(queue.stdout)["top_items"] == ["VC012"]

    triage = subprocess.run(
        [
            str(ROOT / "bin" / "fig-agent"),
            "triage",
            "fig_demo",
            "--accept",
            "VC012",
            "--reject-rest",
            "--tex-lines",
            "VC012:2:2",
            "--defect-class",
            "VC012:text_overlap",
            "--json",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert triage.returncode == 0, triage.stderr
    assert json.loads(triage.stdout)["accepted"][0]["source_detector"] == "visual_clash"

    ledger = subprocess.run(
        [str(ROOT / "bin" / "fig-agent"), "quality-map", "fig_demo", "--json"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert ledger.returncode == 0, ledger.stderr
    defects = json.loads(ledger.stdout)["defects"]
    assert any(
        defect.get("source_detector") == "visual_clash"
        and defect.get("promoted_by") == "triage"
        and defect.get("actionability", {}).get("state") == "candidate_supported"
        for defect in defects
    )


def test_acceptance_guard_reads_declared_detector_outputs() -> None:
    source = (ROOT / "scripts" / "promotion_wiring.py").read_text(encoding="utf-8")
    ledger = (ROOT / "scripts" / "quality" / "quality_defect_ledger.py").read_text(
        encoding="utf-8"
    )

    assert "tex_assertions.json" in source
    assert "semantic_assertions.json" in source
    assert "visual_clash.json" in source
    assert "promotion_triage.json" in source
    assert "auto_promoted_defects" in ledger
    assert "triage_promoted_defects" in ledger
    assert "layout_drift" in source and "non_promoting" in source
    assert "hyphenation" in source and "non_promoting" in source
    assert "physics_grounding" in source and "non_promoting" in source
