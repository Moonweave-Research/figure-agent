from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from detector_feedback_ledger import (  # noqa: E402
    build_detector_feedback_ledger,
    compare_reviewed_benchmark_stages,
    main,
)
from quality_manifest import file_sha256  # noqa: E402


def _write_visual_clash_report(fig_dir: Path, candidate_ids: tuple[str, ...]) -> None:
    report = fig_dir / "build" / "visual_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "fixture": fig_dir.name,
                "render_pdf": f"build/{fig_dir.name}.pdf",
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "text_on_path",
                        "text": f"label {candidate_id}",
                        "bbox_px": [1, 2, 3, 4],
                        "metric": {"dark": 0.04},
                        "tex_lines": None,
                    }
                    for candidate_id in candidate_ids
                ],
                "total": len(candidate_ids),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _write_text_boundary_clash_report(fig_dir, ())
    _write_label_path_proximity_report(fig_dir, ())
    _write_undeclared_geometry_report(fig_dir, ())


def _write_text_boundary_clash_report(fig_dir: Path, candidate_ids: tuple[str, ...]) -> None:
    report = fig_dir / "build" / "text_boundary_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-boundary-clash.v1",
                "fixture": fig_dir.name,
                "render_pdf": f"build/{fig_dir.name}.pdf",
                "source": "spec.yaml:text_boundary_checks",
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "text_crosses_vertical_boundary",
                        "text": f"label {candidate_id}",
                        "boundary_id": "de_column_rule",
                        "boundary_role": "column_rule",
                        "bbox_pt": [70.0, 20.0, 75.0, 30.0],
                        "boundary_pt": {"x": 72.0, "y_range": [0.0, 144.0]},
                        "clearance_pt": 0.5,
                    }
                    for candidate_id in candidate_ids
                ],
                "total": len(candidate_ids),
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_label_path_proximity_report(fig_dir: Path, candidate_ids: tuple[str, ...]) -> None:
    report = fig_dir / "build" / "label_path_proximity.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.label-path-proximity.v1",
                "fixture": fig_dir.name,
                "render_pdf": f"build/{fig_dir.name}.pdf",
                "source": "spec.yaml:label_path_proximity_checks",
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "label_touches_reference_line",
                        "text": f"label {candidate_id}",
                        "path_id": "de_baseline",
                        "path_role": "reference_line",
                        "bbox_pt": [70.0, 20.0, 75.0, 30.0],
                        "path_pt": {"kind": "horizontal_line", "y": 25.0},
                        "clearance_pt": 1.0,
                        "distance_pt": 0.5,
                    }
                    for candidate_id in candidate_ids
                ],
                "total": len(candidate_ids),
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_undeclared_geometry_report(fig_dir: Path, candidate_ids: tuple[str, ...]) -> None:
    report = fig_dir / "build" / "undeclared_geometry.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.undeclared-geometry.v1",
                "fixture": fig_dir.name,
                "render_pdf": f"build/{fig_dir.name}.pdf",
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "text_crosses_undeclared_rect",
                        "text": f"label {candidate_id}",
                        "bbox_pt": [70.0, 20.0, 75.0, 30.0],
                        "geometry": {"kind": "rect", "bbox_pt": [65.0, 10.0, 80.0, 40.0]},
                        "clearance_pt": -0.5,
                    }
                    for candidate_id in candidate_ids
                ],
                "total": len(candidate_ids),
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_crop_manifest(fig_dir: Path, crop_ids: tuple[str, ...]) -> None:
    crop_entries = []
    for crop_id in crop_ids:
        crop_path = fig_dir / "build" / "audit_crops" / f"{crop_id}.png"
        crop_path.parent.mkdir(parents=True, exist_ok=True)
        crop_path.write_bytes(f"crop:{crop_id}\n".encode())
        crop_entries.append(
            {
                "id": crop_id,
                "kind": "zoom_crop",
                "source": "full_render",
                "path": f"build/audit_crops/{crop_id}.png",
                "source_path": f"build/{fig_dir.name}.png",
                "bbox_px": [0, 0, 10, 10],
                "sha256": file_sha256(crop_path),
            }
        )
    manifest = fig_dir / "build" / "audit_crops" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "schema": "figure-agent.audit-crop-manifest.v1",
                "fixture": fig_dir.name,
                "render_path": f"build/{fig_dir.name}.png",
                "required_crop_ids": list(crop_ids),
                "crops": crop_entries,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_critique(fig_dir: Path, micro_defects_yaml: str) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    (fig_dir / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1.10\n"
        f"fixture: {fig_dir.name}\n"
        f"{micro_defects_yaml}"
        "crop_audit_log:\n"
        "  - crop_id: full_q1\n"
        "    path: build/audit_crops/full_q1.png\n"
        "    source: full_render\n"
        "    inspected: true\n"
        "    verdict: no_defect\n"
        '    linked_micro_defect_id: ""\n'
        "    rationale: full_q1 was inspected\n"
        "findings: []\n"
        "panels: []\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )


def _write_complete_fixture(
    examples_root: Path,
    name: str,
    *,
    visual_candidates: tuple[str, ...],
    micro_defects_yaml: str,
) -> Path:
    fig_dir = examples_root / name
    _write_visual_clash_report(fig_dir, visual_candidates)
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir, micro_defects_yaml)
    return fig_dir


def test_ledger_aggregates_detector_feedback_across_selected_fixtures(
    tmp_path: Path,
) -> None:
    examples_root = tmp_path / "examples"
    _write_complete_fixture(
        examples_root,
        "alpha",
        visual_candidates=("VC001",),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    kind: line_crosses_label\n"
            "    severity: NIT\n"
            "    observation: VC001 is a detector false positive.\n"
            '    linked_finding_id: ""\n'
            "    visual_clash_ref: VC001\n"
            '    text_boundary_ref: ""\n'
            '    undeclared_geometry_ref: ""\n'
            "    status: accept_simplification\n"
            "    accept_simplification_reason: false_positive\n"
            "    accept_simplification_rationale: VC001 marks texture, not a defect.\n"
        ),
    )
    _write_complete_fixture(
        examples_root,
        "beta",
        visual_candidates=("VC010",),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M010\n"
            "    kind: line_crosses_label\n"
            "    severity: MAJOR\n"
            "    observation: VC010 is a real defect.\n"
            "    linked_finding_id: C010\n"
            "    visual_clash_ref: VC010\n"
            '    text_boundary_ref: ""\n'
            '    undeclared_geometry_ref: ""\n'
            "    status: open\n"
            "  - id: M011\n"
            "    kind: print_scale_unreadable\n"
            "    severity: MINOR\n"
            "    observation: host vision found an unlinked defect.\n"
            "    linked_finding_id: C011\n"
            '    visual_clash_ref: ""\n'
            '    text_boundary_ref: ""\n'
            '    undeclared_geometry_ref: ""\n'
            "    status: open\n"
        ),
    )

    ledger = build_detector_feedback_ledger(examples_root, ["beta", "alpha"])

    assert ledger["schema"] == "figure-agent.detector-feedback-ledger.v1"
    assert [row["fixture"] for row in ledger["fixtures"]] == ["alpha", "beta"]
    assert ledger["fixture_count"] == 2
    assert ledger["totals"]["visual_clash"]["candidate_count"] == 2
    assert ledger["totals"]["visual_clash"]["accepted_false_positive_count"] == 1
    assert ledger["totals"]["visual_clash"]["linked_defect_count"] == 1
    assert ledger["totals"]["unlinked_micro_defect_count"] == 1
    assert ledger["totals"]["unlinked_micro_defect_refs"] == ["beta:M011"]


def test_ledger_selects_dominant_reviewed_false_positive_family(
    tmp_path: Path,
) -> None:
    examples_root = tmp_path / "examples"
    alpha = _write_complete_fixture(
        examples_root,
        "alpha",
        visual_candidates=("VC001", "VC002", "VC003"),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    kind: drawing_order_suspect\n"
            "    severity: NIT\n"
            "    observation: reviewed fill false positive\n"
            '    linked_finding_id: ""\n'
            "    visual_clash_ref: VC001\n"
            '    text_boundary_ref: ""\n'
            '    undeclared_geometry_ref: ""\n'
            "    status: accept_simplification\n"
            "    accept_simplification_reason: false_positive\n"
            "    accept_simplification_rationale: reviewed no defect\n"
            "  - id: M002\n"
            "    kind: drawing_order_suspect\n"
            "    severity: NIT\n"
            "    observation: another reviewed fill false positive\n"
            '    linked_finding_id: ""\n'
            "    visual_clash_ref: VC002\n"
            '    text_boundary_ref: ""\n'
            '    undeclared_geometry_ref: ""\n'
            "    status: accept_simplification\n"
            "    accept_simplification_reason: false_positive\n"
            "    accept_simplification_rationale: reviewed no defect\n"
            "  - id: M003\n"
            "    kind: line_crosses_label\n"
            "    severity: MAJOR\n"
            "    observation: reviewed path defect\n"
            "    linked_finding_id: C003\n"
            "    visual_clash_ref: VC003\n"
            '    text_boundary_ref: ""\n'
            '    undeclared_geometry_ref: ""\n'
            "    status: open\n"
        ),
    )
    report = json.loads((alpha / "build" / "visual_clash.json").read_text())
    report["candidates"][0]["kind"] = "text_on_fill"
    report["candidates"][1]["kind"] = "text_on_fill"
    report["candidates"][2]["kind"] = "text_on_path"
    (alpha / "build" / "visual_clash.json").write_text(json.dumps(report) + "\n")

    ledger = build_detector_feedback_ledger(examples_root, [])

    assert ledger["dominant_false_positive_family"] == {
        "detector": "visual_clash",
        "family": "text_on_fill",
        "accepted_false_positive_count": 2,
        "linked_defect_count": 0,
        "reviewed_precision": 0.0,
    }
    assert ledger["reviewed_metrics"] == {
        "reviewed_true_positive_count": 1,
        "reviewed_false_positive_count": 2,
        "unlinked_false_negative_count": 0,
        "precision": pytest.approx(1 / 3),
        "recall": 1.0,
    }


def test_reviewed_benchmark_comparison_requires_recall_and_unbound_evidence() -> None:
    cases = [
        {
            "review_outcome": "true_positive",
            "expected_attribution": "exact",
            "detected_before": True,
            "detected_after": True,
        },
        {
            "review_outcome": "true_positive",
            "expected_attribution": "unbound",
            "detected_before": True,
            "detected_after": True,
        },
        {
            "review_outcome": "false_positive",
            "expected_attribution": "unbound",
            "detected_before": True,
            "detected_after": False,
        },
    ]

    assert compare_reviewed_benchmark_stages(cases) == {
        "before": {
            "reviewed_true_positive_count": 2,
            "reviewed_false_positive_count": 1,
            "precision": pytest.approx(2 / 3),
            "recall": 1.0,
            "unbound_attribution_rate": pytest.approx(2 / 3),
        },
        "after": {
            "reviewed_true_positive_count": 2,
            "reviewed_false_positive_count": 0,
            "precision": 1.0,
            "recall": 1.0,
            "unbound_attribution_rate": 0.5,
        },
    }


def test_ledger_default_fixture_selection_skips_directories_without_critiques(
    tmp_path: Path,
) -> None:
    examples_root = tmp_path / "examples"
    _write_complete_fixture(
        examples_root,
        "has_critique",
        visual_candidates=(),
        micro_defects_yaml="micro_defects: []\n",
    )
    (examples_root / "draft_without_critique").mkdir(parents=True)

    ledger = build_detector_feedback_ledger(examples_root, [])

    assert [row["fixture"] for row in ledger["fixtures"]] == ["has_critique"]


def test_ledger_default_fixture_selection_skips_symlink_escape(
    tmp_path: Path,
) -> None:
    examples_root = tmp_path / "examples"
    _write_complete_fixture(
        examples_root,
        "inside",
        visual_candidates=(),
        micro_defects_yaml="micro_defects: []\n",
    )
    outside_fixture = _write_complete_fixture(
        tmp_path / "outside_root",
        "outside",
        visual_candidates=(),
        micro_defects_yaml="micro_defects: []\n",
    )
    (examples_root / "linked_outside").symlink_to(outside_fixture, target_is_directory=True)

    ledger = build_detector_feedback_ledger(examples_root, [])

    assert [row["fixture"] for row in ledger["fixtures"]] == ["inside"]


def test_ledger_rejects_unknown_selected_fixture(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="fixture not found"):
        build_detector_feedback_ledger(tmp_path / "examples", ["missing_fixture"])


def test_ledger_rejects_unsafe_selected_fixture_before_reading_outside_root(
    tmp_path: Path,
) -> None:
    examples_root = tmp_path / "examples"
    examples_root.mkdir()
    _write_complete_fixture(
        tmp_path,
        "outside",
        visual_candidates=(),
        micro_defects_yaml="micro_defects: []\n",
    )

    with pytest.raises(ValueError, match="single examples/<name> directory name"):
        build_detector_feedback_ledger(examples_root, ["../outside"])


def test_cli_rejects_unsafe_selected_fixture_cleanly(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    examples_root = tmp_path / "examples"
    examples_root.mkdir()

    exit_code = main(["--examples-root", str(examples_root), "../outside"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "single examples/<name> directory name" in captured.err
    assert "Traceback" not in captured.err


def test_cli_prints_ledger_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    examples_root = tmp_path / "examples"
    _write_complete_fixture(
        examples_root,
        "alpha",
        visual_candidates=(),
        micro_defects_yaml="micro_defects: []\n",
    )

    exit_code = main(["--examples-root", str(examples_root), "alpha"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.detector-feedback-ledger.v1"
    assert payload["fixtures"][0]["fixture"] == "alpha"


def test_cli_accepts_json_noop_flag(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    examples_root = tmp_path / "examples"
    _write_complete_fixture(
        examples_root,
        "alpha",
        visual_candidates=(),
        micro_defects_yaml="micro_defects: []\n",
    )

    exit_code = main(["--examples-root", str(examples_root), "--json", "alpha"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.detector-feedback-ledger.v1"
    assert payload["fixtures"][0]["fixture"] == "alpha"


def test_cli_accepts_format_json_alias(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    examples_root = tmp_path / "examples"
    _write_complete_fixture(
        examples_root,
        "alpha",
        visual_candidates=(),
        micro_defects_yaml="micro_defects: []\n",
    )

    exit_code = main(["--examples-root", str(examples_root), "--format", "json", "alpha"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.detector-feedback-ledger.v1"
    assert payload["fixtures"][0]["fixture"] == "alpha"
