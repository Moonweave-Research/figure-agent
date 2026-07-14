from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_evidence_summary import summarize_audit_evidence  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


def test_summary_without_critique_does_not_suggest_host_critique(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "no_critique_required"
    fig_dir.mkdir()

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "not_applicable"
    assert summary["blocking_items"] == []
    assert summary["next_action"] == ""
    assert summary["reason"] == "critique.md is absent; audit evidence is not applicable"
    assert summary["detector_feedback"]["unadjudicated_candidate_count"] == 0
    assert summary["detector_feedback"]["summary"] == "no detector feedback"


def test_summary_without_critique_surfaces_unadjudicated_detector_candidates(
    tmp_path: Path,
) -> None:
    # Detectors run during compile and write build/*.json even when no critique.md
    # exists to account for them. Without surfacing their raw counts the default
    # status view reads "clean" while real flags sit unadjudicated in build/.
    fig_dir = tmp_path / "no_critique_with_candidates"
    fig_dir.mkdir()
    _write_undeclared_geometry_report(fig_dir, ("UG001", "UG002", "UG003"))
    _write_visual_clash_report(fig_dir, ("VC001", "VC002"))

    summary = summarize_audit_evidence(fig_dir)

    # Policy preserved: still not_applicable, no blocker, no critique nag.
    assert summary["evaluation_state"] == "not_applicable"
    assert summary["blocking_items"] == []
    assert summary["next_action"] == ""
    assert summary["reason"] == "critique.md is absent; audit evidence is not applicable"
    # Visibility: raw candidate counts now surfaced instead of all-zero.
    feedback = summary["detector_feedback"]
    assert feedback["unadjudicated_candidate_count"] == 5
    assert feedback["visual_clash"]["candidate_count"] == 2
    assert feedback["undeclared_geometry"]["candidate_count"] == 3
    assert feedback["text_boundary"]["candidate_count"] == 0
    assert "unadjudicated" in feedback["summary"]


def test_summary_with_stale_critique_never_promotes_historical_refs_as_current_blockers(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ())
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir)

    summary = summarize_audit_evidence(fig_dir, critique_is_current=False)

    assert summary["evaluation_state"] == "stale_or_mismatched"
    assert summary["blocking_items"] == []
    assert summary["next_action"] == "/fig_critique demo_fig"
    assert "historical detector references" in summary["reason"]
    assert summary["visual_clash"]["candidate_count"] == 0
    assert summary["visual_clash"]["unknown_refs"] == []


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
    if not (fig_dir / "build" / "text_boundary_clash.json").exists():
        _write_text_boundary_clash_report(fig_dir, ())
    if not (fig_dir / "build" / "undeclared_geometry.json").exists():
        _write_undeclared_geometry_report(fig_dir, ())
    if not (fig_dir / "build" / "label_path_proximity.json").exists():
        _write_label_path_report(fig_dir, ())


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


def _write_label_path_report(fig_dir: Path, candidate_ids: tuple[str, ...]) -> None:
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


def _micro_defect_yaml(
    *,
    visual_clash_ref: str = "VC001",
    text_boundary_ref: str = "",
    undeclared_geometry_ref: str = "",
    status: str = "accept_simplification",
    structured: bool = True,
) -> str:
    fields = (
        "  - id: M001\n"
        "    crop: examples/demo_fig/build/audit_crops/visual_clash/VC001_A.png\n"
        "    kind: line_crosses_label\n"
        "    severity: NIT\n"
        f"    observation: {visual_clash_ref} is accepted as a detector false positive\n"
        '    linked_finding_id: ""\n'
        f"    visual_clash_ref: {visual_clash_ref}\n"
        f"    text_boundary_ref: {text_boundary_ref!r}\n"
        f"    undeclared_geometry_ref: {undeclared_geometry_ref!r}\n"
        f"    status: {status}\n"
    )
    if structured:
        fields += (
            "    accept_simplification_reason: false_positive\n"
            "    accept_simplification_rationale: VC001 marks texture, not a defect.\n"
        )
    return "micro_defects:\n" + fields


def _crop_audit_log_yaml(
    *,
    verdict: str = "no_defect",
    crop_id: str = "full_q1",
) -> str:
    linked = "M001" if verdict == "defect" else ""
    return (
        "crop_audit_log:\n"
        f"  - crop_id: {crop_id}\n"
        f"    path: build/audit_crops/{crop_id}.png\n"
        "    source: full_render\n"
        "    inspected: true\n"
        f"    verdict: {verdict}\n"
        f'    linked_micro_defect_id: "{linked}"\n'
        f"    rationale: {crop_id} was inspected\n"
    )


def _write_critique(
    fig_dir: Path,
    *,
    schema: str = "figure-agent.critique.v1.10",
    micro_defects_yaml: str | None = None,
    crop_audit_log_yaml: str | None = None,
) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    (fig_dir / "critique.md").write_text(
        "---\n"
        f"schema: {schema}\n"
        f"fixture: {fig_dir.name}\n"
        f"{micro_defects_yaml if micro_defects_yaml is not None else _micro_defect_yaml()}"
        f"{crop_audit_log_yaml if crop_audit_log_yaml is not None else _crop_audit_log_yaml()}"
        "findings: []\n"
        "panels: []\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )


def test_summary_reports_legacy_schema_without_current_audit_blocker(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.5",
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml="",
    )

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "legacy"
    assert summary["blocking_items"] == []
    assert summary["critique_schema"] == "figure-agent.critique.v1.5"


def test_summary_reports_missing_visual_clash_report_for_current_schema(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir)

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "missing_input"
    assert summary["blocking_items"] == ["build/visual_clash.json"]
    assert summary["next_action"] == "/fig_compile demo_fig"


def test_summary_reports_missing_text_boundary_report_for_current_schema(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    (fig_dir / "build" / "text_boundary_clash.json").unlink()
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir)

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "missing_input"
    assert summary["blocking_items"] == ["build/text_boundary_clash.json"]
    assert summary["next_action"] == "/fig_compile demo_fig"


def test_summary_reports_missing_label_path_report_for_current_schema(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    (fig_dir / "build" / "label_path_proximity.json").unlink()
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir)

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "missing_input"
    assert summary["blocking_items"] == ["build/label_path_proximity.json"]
    assert summary["next_action"] == "/fig_compile demo_fig"


def test_summary_reports_malformed_visual_clash_report(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir)
    report = fig_dir / "build" / "visual_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("{", encoding="utf-8")

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "missing_input"
    assert summary["blocking_items"] == ["build/visual_clash.json"]
    assert "malformed" in summary["reason"]


def test_summary_reports_passed_accounting_counts(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir)

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "passed"
    assert summary["visual_clash"]["candidate_count"] == 1
    assert summary["visual_clash"]["accounted_count"] == 1
    assert summary["crop_audit"]["verdict_counts"] == {
        "defect": 0,
        "no_defect": 1,
        "uncertain": 0,
    }
    assert summary["blocking_items"] == []


def test_summary_reports_detector_feedback_for_false_positive_and_defect_refs(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    micro_defects = (
        "micro_defects:\n"
        "  - id: M001\n"
        "    kind: line_crosses_label\n"
        "    severity: NIT\n"
        "    observation: VC001 is texture, not a defect.\n"
        '    linked_finding_id: ""\n'
        "    visual_clash_ref: VC001\n"
        "    status: accept_simplification\n"
        "    accept_simplification_reason: false_positive\n"
        "    accept_simplification_rationale: VC001 marks texture, not a defect.\n"
        "  - id: M002\n"
        "    kind: label_too_close_to_path\n"
        "    severity: MAJOR\n"
        "    observation: TB001 crosses a declared text boundary.\n"
        "    linked_finding_id: C002\n"
        "    visual_clash_ref: ''\n"
        "    text_boundary_ref: TB001\n"
        "    status: open\n"
    )
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_text_boundary_clash_report(fig_dir, ("TB001",))
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir, micro_defects_yaml=micro_defects)

    summary = summarize_audit_evidence(fig_dir)

    feedback = summary["detector_feedback"]
    assert feedback["visual_clash"]["accepted_false_positive_count"] == 1
    assert feedback["visual_clash"]["linked_defect_count"] == 0
    assert feedback["text_boundary"]["accepted_false_positive_count"] == 0
    assert feedback["text_boundary"]["linked_defect_count"] == 1
    assert feedback["unlinked_micro_defect_count"] == 0
    assert "1 accepted false positive" in feedback["summary"]
    assert "1 detector-linked defect" in feedback["summary"]


def test_summary_reports_unlinked_micro_defects_as_detector_feedback(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    micro_defects = (
        "micro_defects:\n"
        "  - id: M777\n"
        "    kind: print_scale_unreadable\n"
        "    severity: MINOR\n"
        "    observation: print scale issue found by host vision only.\n"
        "    linked_finding_id: C777\n"
        "    visual_clash_ref: ''\n"
        "    text_boundary_ref: ''\n"
        "    label_path_ref: ''\n"
        "    undeclared_geometry_ref: ''\n"
        "    status: open\n"
    )
    _write_visual_clash_report(fig_dir, ())
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir, micro_defects_yaml=micro_defects)

    summary = summarize_audit_evidence(fig_dir)

    feedback = summary["detector_feedback"]
    assert feedback["unlinked_micro_defect_count"] == 1
    assert feedback["unlinked_micro_defect_ids"] == ["M777"]
    assert "1 unlinked micro defect" in feedback["summary"]


def test_summary_reports_unaccounted_visual_clash_candidate(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001", "VC002"))
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir)

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "needs_action"
    assert summary["blocking_items"] == ["VC002"]
    assert summary["visual_clash"]["missing_refs"] == ["VC002"]


def test_summary_reports_unaccounted_text_boundary_candidate(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_text_boundary_clash_report(fig_dir, ("TB001",))
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir)

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "needs_action"
    assert summary["blocking_items"] == ["TB001"]
    assert summary["text_boundary"]["candidate_count"] == 1
    assert summary["text_boundary"]["missing_refs"] == ["TB001"]


def test_summary_reports_missing_undeclared_geometry_report_for_v1_17(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    (fig_dir / "build" / "undeclared_geometry.json").unlink()
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.17",
        micro_defects_yaml=_micro_defect_yaml(undeclared_geometry_ref="UG001"),
    )

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "missing_input"
    assert summary["blocking_items"] == ["build/undeclared_geometry.json"]
    assert summary["next_action"] == "/fig_compile demo_fig"


@pytest.mark.parametrize(
    "schema",
    (
        "figure-agent.critique.v1.10",
        "figure-agent.critique.v1.14",
        "figure-agent.critique.v1.17",
    ),
)
def test_summary_surfaces_undeclared_geometry_before_visual_clash_accounting(
    tmp_path: Path,
    schema: str,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_undeclared_geometry_report(fig_dir, ("UG001",))
    _write_visual_clash_report(fig_dir, ())
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(
        fig_dir,
        schema=schema,
        micro_defects_yaml="micro_defects: []\n",
    )

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "needs_action"
    assert summary["blocking_items"] == ["UG001"]
    assert summary["undeclared_geometry"]["candidate_count"] == 1
    assert summary["undeclared_geometry"]["missing_refs"] == ["UG001"]


def test_summary_reports_malformed_undeclared_geometry_report(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    report = fig_dir / "build" / "undeclared_geometry.json"
    report.write_text("{", encoding="utf-8")
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir, schema="figure-agent.critique.v1.17")

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "missing_input"
    assert summary["blocking_items"] == ["build/undeclared_geometry.json"]
    assert "malformed" in summary["reason"]


def test_summary_reports_unaccounted_undeclared_geometry_candidate(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_undeclared_geometry_report(fig_dir, ("UG001", "UG002"))
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.17",
        micro_defects_yaml=_micro_defect_yaml(undeclared_geometry_ref="UG001"),
    )

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "needs_action"
    assert summary["blocking_items"] == ["UG002"]
    assert summary["undeclared_geometry"]["candidate_count"] == 2
    assert summary["undeclared_geometry"]["missing_refs"] == ["UG002"]


def test_summary_reports_unknown_undeclared_geometry_ref(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_undeclared_geometry_report(fig_dir, ("UG001",))
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.17",
        micro_defects_yaml=_micro_defect_yaml(undeclared_geometry_ref="UG999"),
    )

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "needs_action"
    assert summary["blocking_items"] == ["UG001", "UG999"]
    assert summary["undeclared_geometry"]["missing_refs"] == ["UG001"]
    assert summary["undeclared_geometry"]["unknown_refs"] == ["UG999"]


def test_summary_reports_passed_undeclared_geometry_accounting(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_undeclared_geometry_report(fig_dir, ("UG001",))
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.17",
        micro_defects_yaml=_micro_defect_yaml(undeclared_geometry_ref="UG001"),
    )

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "passed"
    assert summary["undeclared_geometry"]["present"] is True
    assert summary["undeclared_geometry"]["candidate_count"] == 1
    assert summary["undeclared_geometry"]["accounted_count"] == 1


def test_summary_reports_passed_undeclared_geometry_zero_candidates(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_undeclared_geometry_report(fig_dir, ())
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir, schema="figure-agent.critique.v1.17")

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "passed"
    assert summary["undeclared_geometry"]["present"] is True
    assert summary["undeclared_geometry"]["candidate_count"] == 0
    assert summary["undeclared_geometry"]["accounted_count"] == 0


def test_summary_reports_uncertain_crop_ids(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir, crop_audit_log_yaml=_crop_audit_log_yaml(verdict="uncertain"))

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "needs_action"
    assert summary["blocking_items"] == ["full_q1"]
    assert summary["crop_audit"]["uncertain_crop_ids"] == ["full_q1"]
    assert summary["next_action"] == "human_review: reread uncertain audit crops"


def test_summary_reports_missing_crop_manifest(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_critique(fig_dir)

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "missing_input"
    assert summary["blocking_items"] == ["build/audit_crops/manifest.json"]
    assert summary["next_action"] == "/fig_critique demo_fig"


def test_summary_reports_malformed_crop_manifest(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_crop_manifest(fig_dir, ("full_q1",))
    manifest = fig_dir / "build" / "audit_crops" / "manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["crops"] = {}
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    _write_critique(fig_dir)

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "missing_input"
    assert summary["blocking_items"] == ["build/audit_crops/manifest.json"]
    assert "malformed" in summary["reason"]
    assert summary["next_action"] == "/fig_critique demo_fig"


def test_summary_reports_crop_hash_mismatch(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_crop_manifest(fig_dir, ("full_q1",))
    (fig_dir / "build" / "audit_crops" / "full_q1.png").write_bytes(b"changed\n")
    _write_critique(fig_dir)

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "stale_or_mismatched"
    assert summary["blocking_items"] == ["full_q1"]
    assert summary["next_action"] == "/fig_critique demo_fig"


def test_summary_reports_crop_manifest_path_traversal(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_crop_manifest(fig_dir, ("full_q1",))
    manifest = fig_dir / "build" / "audit_crops" / "manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["crops"][0]["path"] = "build/audit_crops/../outside.png"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    _write_critique(fig_dir)

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "stale_or_mismatched"
    assert summary["blocking_items"] == ["full_q1"]


def test_summary_reports_missing_required_crop_audit_log_entry(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_crop_manifest(fig_dir, ("full_q1", "full_q2"))
    _write_critique(fig_dir, crop_audit_log_yaml=_crop_audit_log_yaml(crop_id="full_q1"))

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "needs_action"
    assert summary["blocking_items"] == ["full_q2"]
    assert "crop_audit_log" in summary["reason"]


def test_summary_counts_duplicate_visual_clash_refs_once(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    duplicate_refs = (
        "micro_defects:\n"
        "  - id: M001\n"
        "    kind: line_crosses_label\n"
        "    severity: NIT\n"
        "    observation: first accounting\n"
        '    linked_finding_id: ""\n'
        "    visual_clash_ref: VC001\n"
        "    status: accept_simplification\n"
        "    accept_simplification_reason: false_positive\n"
        "    accept_simplification_rationale: VC001 is texture, not a defect.\n"
        "  - id: M002\n"
        "    kind: line_crosses_label\n"
        "    severity: NIT\n"
        "    observation: duplicate accounting\n"
        '    linked_finding_id: ""\n'
        "    visual_clash_ref: VC001\n"
        "    status: accept_simplification\n"
        "    accept_simplification_reason: false_positive\n"
        "    accept_simplification_rationale: VC001 is still texture, not a defect.\n"
    )
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir, micro_defects_yaml=duplicate_refs)

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "passed"
    assert summary["visual_clash"]["candidate_count"] == 1
    assert summary["visual_clash"]["accounted_count"] == 1


def test_summary_reports_v1_10_accept_simplification_gap(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    _write_visual_clash_report(fig_dir, ("VC001",))
    _write_crop_manifest(fig_dir, ("full_q1",))
    _write_critique(fig_dir, micro_defects_yaml=_micro_defect_yaml(structured=False))

    summary = summarize_audit_evidence(fig_dir)

    assert summary["evaluation_state"] == "needs_action"
    assert summary["blocking_items"] == ["VC001"]
    assert "accept_simplification_reason" in summary["reason"]
