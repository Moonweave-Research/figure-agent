from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_driver  # noqa: E402
from audit_evidence_summary import summarize_audit_evidence  # noqa: E402
from fig_loop import run_loop  # noqa: E402
from fig_loop_records import json_stdout_summary  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402
from status import infer_stage  # noqa: E402


def _write_visual_clash_report(fixture: Path, candidate_ids: tuple[str, ...]) -> None:
    report = fixture / "build" / "visual_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "fixture": fixture.name,
                "render_pdf": f"build/{fixture.name}.pdf",
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "text_on_fill",
                        "text": "HV+" if candidate_id == "VC050" else candidate_id,
                        "bbox_px": [10, 20, 30, 40],
                        "metric": {"dark": 0.041, "edge": 0.006},
                        "tex_lines": None,
                    }
                    for candidate_id in candidate_ids
                ],
                "total": len(candidate_ids),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_text_boundary_clash_report(fixture, ())
    _write_label_path_proximity_report(fixture, ())
    _write_undeclared_geometry_report(fixture, ())


def _write_text_boundary_clash_report(fixture: Path, candidate_ids: tuple[str, ...]) -> None:
    report = fixture / "build" / "text_boundary_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-boundary-clash.v1",
                "fixture": fixture.name,
                "render_pdf": f"build/{fixture.name}.pdf",
                "source": "spec.yaml:text_boundary_checks",
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "text_crosses_vertical_boundary",
                        "text": candidate_id,
                        "boundary_id": "column_rule",
                        "boundary_role": "column_rule",
                        "bbox_pt": [10.0, 20.0, 30.0, 40.0],
                        "boundary_pt": {"x": 20.0, "y_range": [0.0, 50.0]},
                        "clearance_pt": 0.5,
                    }
                    for candidate_id in candidate_ids
                ],
                "total": len(candidate_ids),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_label_path_proximity_report(fixture: Path, candidate_ids: tuple[str, ...]) -> None:
    report = fixture / "build" / "label_path_proximity.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.label-path-proximity.v1",
                "fixture": fixture.name,
                "render_pdf": f"build/{fixture.name}.pdf",
                "source": "spec.yaml:label_path_proximity_checks",
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "label_path_near_miss",
                        "text": candidate_id,
                        "path_id": "reference_line",
                        "path_role": "reference_line",
                        "bbox_pt": [10.0, 20.0, 30.0, 40.0],
                        "path_pt": {
                            "kind": "horizontal_line",
                            "y": 25.0,
                            "x_range": [0.0, 50.0],
                        },
                        "clearance_pt": 2.0,
                        "distance_pt": 1.0,
                    }
                    for candidate_id in candidate_ids
                ],
                "total": len(candidate_ids),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_undeclared_geometry_report(fixture: Path, candidate_ids: tuple[str, ...]) -> None:
    report = fixture / "build" / "undeclared_geometry.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.undeclared-geometry.v1",
                "fixture": fixture.name,
                "render_pdf": f"build/{fixture.name}.pdf",
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "text_crosses_undeclared_rect",
                        "text": candidate_id,
                        "bbox_pt": [10.0, 20.0, 30.0, 40.0],
                        "geometry": {
                            "kind": "rect",
                            "bbox_pt": [5.0, 10.0, 35.0, 45.0],
                        },
                        "clearance_pt": -0.5,
                    }
                    for candidate_id in candidate_ids
                ],
                "total": len(candidate_ids),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_crop_manifest(fixture: Path, crop_id: str = "full_q1") -> Path:
    crop_path = fixture / "build" / "audit_crops" / f"{crop_id}.png"
    crop_path.parent.mkdir(parents=True, exist_ok=True)
    crop_path.write_bytes(f"crop:{crop_id}\n".encode())
    manifest = {
        "schema": "figure-agent.audit-crop-manifest.v1",
        "fixture": fixture.name,
        "render_path": f"build/{fixture.name}.png",
        "required_crop_ids": [crop_id],
        "crops": [
            {
                "id": crop_id,
                "kind": "zoom_crop",
                "source": "full_render",
                "path": f"build/audit_crops/{crop_id}.png",
                "source_path": f"build/{fixture.name}.png",
                "bbox_px": [0, 0, 10, 10],
                "sha256": file_sha256(crop_path),
            }
        ],
    }
    (fixture / "build" / "audit_crops" / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return crop_path


def _write_critique(
    fixture: Path,
    *,
    visual_clash_ref: str | None = "VC050",
    label_path_ref: str | None = None,
    undeclared_geometry_ref: str | None = None,
    crop_id: str = "full_q1",
) -> None:
    micro_defects: list[dict[str, Any]] = []
    if visual_clash_ref is not None:
        micro_defects.append(
            {
                "id": "M050",
                "kind": "label_backdrop_overflows_outline",
                "severity": "NIT",
                "observation": "VC050 is accepted as a detector false positive.",
                "linked_finding_id": "",
                "visual_clash_ref": visual_clash_ref,
                "status": "accept_simplification",
                "accept_simplification_reason": "false_positive",
                "accept_simplification_rationale": (
                    "VC050 marks a deliberately high-contrast QA marker."
                ),
            }
        )
    if label_path_ref is not None:
        micro_defects.append(
            {
                "id": "MLP001",
                "kind": "label_path_near_miss",
                "severity": "NIT",
                "observation": f"{label_path_ref} is accounted as label/path proximity.",
                "linked_finding_id": "",
                "visual_clash_ref": "",
                "text_boundary_ref": "",
                "label_path_ref": label_path_ref,
                "status": "open",
            }
        )
    if undeclared_geometry_ref is not None:
        micro_defects.append(
            {
                "id": "MUG001",
                "kind": "label_crosses_column_rule",
                "severity": "NIT",
                "observation": (f"{undeclared_geometry_ref} is accounted as undeclared geometry."),
                "linked_finding_id": "",
                "visual_clash_ref": "",
                "text_boundary_ref": "",
                "label_path_ref": "",
                "undeclared_geometry_ref": undeclared_geometry_ref,
                "status": "open",
            }
        )
    frontmatter = {
        "schema": "figure-agent.critique.v1.10",
        "fixture": fixture.name,
        "verdict": "ready",
        "micro_defects": micro_defects,
        "crop_audit_log": [
            {
                "crop_id": crop_id,
                "path": f"build/audit_crops/{crop_id}.png",
                "source": "full_render",
                "inspected": True,
                "verdict": "no_defect",
                "linked_micro_defect_id": "",
                "rationale": f"{crop_id} was inspected.",
            }
        ],
        "quality_axes": {},
        "findings": [],
        "panels": [],
    }
    (fixture / "critique.md").write_text(
        "---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n# critique\n",
        encoding="utf-8",
    )


def _make_repo_fixture(
    tmp_path: Path,
    *,
    name: str,
    visual_clash: bool = True,
    crop_manifest: bool = True,
    visual_clash_ref: str | None = "VC050",
    stale_crop: bool = False,
) -> Path:
    fixture = tmp_path / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        f"name: {name}\npanels: []\nstyle_profile: polymer-default\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text(
        "## 1. Intent\n"
        "Exercise audit-evidence state propagation across status, driver, and loop "
        "surfaces without publication claims.\n\n"
        "## 3. Semantic rules\n"
        "- Detector evidence must remain attributable to this temporary fixture.\n",
        encoding="utf-8",
    )
    (fixture / f"{name}.tex").write_text("% deterministic QA fixture\n", encoding="utf-8")
    build = fixture / "build"
    build.mkdir()
    (build / f"{name}.pdf").write_bytes(b"%PDF audit evidence fixture\n")
    if visual_clash:
        _write_visual_clash_report(fixture, ("VC050",))
    if crop_manifest:
        crop_path = _write_crop_manifest(fixture)
        if stale_crop:
            crop_path.write_bytes(b"changed crop bytes\n")
    _write_critique(fixture, visual_clash_ref=visual_clash_ref)

    old_time = time.time() - 100
    fresh_time = time.time() + 100
    for path in (fixture / "spec.yaml", fixture / "briefing.md", fixture / f"{name}.tex"):
        os.utime(path, (old_time, old_time))
    os.utime(build / f"{name}.pdf", (fresh_time, fresh_time))
    os.utime(fixture / "critique.md", (fresh_time + 100, fresh_time + 100))
    return fixture


def test_audit_evidence_surfaces_unaccounted_label_path_proximity(
    tmp_path: Path,
) -> None:
    fixture = _make_repo_fixture(tmp_path, name="labelpath_gap")
    _write_label_path_proximity_report(fixture, ("LP001",))

    summary = summarize_audit_evidence(fixture)

    assert summary["evaluation_state"] == "needs_action"
    assert summary["blocking_items"] == ["LP001"]
    assert summary["label_path"]["candidate_count"] == 1
    assert summary["label_path"]["missing_refs"] == ["LP001"]
    assert (
        summary["reason"]
        == "label-path proximity candidates are not fully accounted in micro_defects"
    )


def test_audit_evidence_accepts_accounted_label_path_proximity(
    tmp_path: Path,
) -> None:
    fixture = _make_repo_fixture(tmp_path, name="labelpath_clean")
    _write_label_path_proximity_report(fixture, ("LP001",))
    _write_critique(fixture, visual_clash_ref="VC050", label_path_ref="LP001")

    summary = summarize_audit_evidence(fixture)

    assert summary["evaluation_state"] == "passed"
    assert summary["label_path"]["accounted_count"] == 1
    assert summary["label_path"]["missing_refs"] == []


def test_audit_evidence_blocks_malformed_label_path_proximity_report(
    tmp_path: Path,
) -> None:
    fixture = _make_repo_fixture(tmp_path, name="labelpath_malformed")
    report = fixture / "build" / "label_path_proximity.json"
    report.write_text("{not json", encoding="utf-8")

    summary = summarize_audit_evidence(fixture)

    assert summary["evaluation_state"] == "missing_input"
    assert summary["blocking_items"] == ["build/label_path_proximity.json"]
    assert summary["reason"] == "malformed build/label_path_proximity.json"


def test_audit_evidence_surfaces_unaccounted_undeclared_geometry(
    tmp_path: Path,
) -> None:
    fixture = _make_repo_fixture(tmp_path, name="undeclared_gap")
    _write_undeclared_geometry_report(fixture, ("UG001",))

    summary = summarize_audit_evidence(fixture)

    assert summary["evaluation_state"] == "needs_action"
    assert summary["blocking_items"] == ["UG001"]
    assert summary["undeclared_geometry"]["candidate_count"] == 1
    assert summary["undeclared_geometry"]["missing_refs"] == ["UG001"]
    assert (
        summary["reason"]
        == "undeclared-geometry candidates are not fully accounted in micro_defects"
    )


def test_audit_evidence_accepts_accounted_undeclared_geometry(
    tmp_path: Path,
) -> None:
    fixture = _make_repo_fixture(tmp_path, name="undeclared_clean")
    _write_undeclared_geometry_report(fixture, ("UG001",))
    _write_critique(
        fixture,
        visual_clash_ref="VC050",
        undeclared_geometry_ref="UG001",
    )

    summary = summarize_audit_evidence(fixture)

    assert summary["evaluation_state"] == "passed"
    assert summary["undeclared_geometry"]["accounted_count"] == 1
    assert summary["undeclared_geometry"]["missing_refs"] == []


def test_audit_evidence_blocks_malformed_undeclared_geometry_report(
    tmp_path: Path,
) -> None:
    fixture = _make_repo_fixture(tmp_path, name="undeclared_malformed")
    report = fixture / "build" / "undeclared_geometry.json"
    report.write_text("{not json", encoding="utf-8")

    summary = summarize_audit_evidence(fixture)

    assert summary["evaluation_state"] == "missing_input"
    assert summary["blocking_items"] == ["build/undeclared_geometry.json"]
    assert summary["reason"] == "malformed build/undeclared_geometry.json"


def _assert_surfaces_state(
    tmp_path: Path,
    fixture: Path,
    *,
    expected_state: str,
    expected_blocker: str | None = None,
) -> None:
    status = infer_stage(fixture)
    driver = fig_driver.build_driver_summary(
        fixture.name,
        mode="review",
        goal="audit evidence dogfood",
        repo_root=tmp_path,
    )
    run_dir = run_loop(
        fixture.name,
        "audit evidence dogfood",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )
    loop_summary = json_stdout_summary(run_dir)
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")

    assert status["audit_evidence"]["evaluation_state"] == expected_state
    assert driver["audit_evidence"]["evaluation_state"] == expected_state
    assert loop_summary["audit_evidence"]["evaluation_state"] == expected_state
    assert f"- audit_evidence_state: {expected_state}" in decision
    if expected_blocker is not None:
        assert expected_blocker in status["audit_evidence"]["blocking_items"]
        assert expected_blocker in driver["audit_evidence"]["blocking_items"]
        assert expected_blocker in loop_summary["audit_evidence"]["blocking_items"]
        assert expected_blocker in decision


def test_audit_evidence_missing_input_surfaces_through_status_driver_and_loop(
    tmp_path: Path,
) -> None:
    fixture = _make_repo_fixture(tmp_path, name="audit_missing_input", visual_clash=False)

    _assert_surfaces_state(
        tmp_path,
        fixture,
        expected_state="missing_input",
        expected_blocker="build/visual_clash.json",
    )


def test_audit_evidence_needs_action_surfaces_vc_blocker_through_commands(
    tmp_path: Path,
) -> None:
    fixture = _make_repo_fixture(
        tmp_path,
        name="audit_needs_action",
        visual_clash_ref=None,
    )

    _assert_surfaces_state(
        tmp_path,
        fixture,
        expected_state="needs_action",
        expected_blocker="VC050",
    )


def test_audit_evidence_undeclared_geometry_surfaces_through_commands(
    tmp_path: Path,
) -> None:
    fixture = _make_repo_fixture(tmp_path, name="audit_undeclared_gap")
    _write_undeclared_geometry_report(fixture, ("UG001",))

    _assert_surfaces_state(
        tmp_path,
        fixture,
        expected_state="needs_action",
        expected_blocker="UG001",
    )


def test_audit_evidence_stale_crop_surfaces_crop_blocker_through_commands(
    tmp_path: Path,
) -> None:
    fixture = _make_repo_fixture(
        tmp_path,
        name="audit_stale_crop",
        stale_crop=True,
    )

    _assert_surfaces_state(
        tmp_path,
        fixture,
        expected_state="stale_or_mismatched",
        expected_blocker="full_q1",
    )


def test_audit_evidence_passed_surfaces_through_status_driver_and_loop(
    tmp_path: Path,
) -> None:
    fixture = _make_repo_fixture(tmp_path, name="audit_passed")

    _assert_surfaces_state(tmp_path, fixture, expected_state="passed")
