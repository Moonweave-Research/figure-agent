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
        "---\n"
        + yaml.safe_dump(frontmatter, sort_keys=False)
        + "---\n"
        "# critique\n",
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
    (fixture / "briefing.md").write_text("QA-only audit evidence fixture.\n", encoding="utf-8")
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
    return fixture


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
        runs_root=tmp_path / "runs",
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
