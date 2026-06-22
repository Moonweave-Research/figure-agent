from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_defect_ledger  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _write_fixture(workspace: Path, name: str = "quality_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: quality_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    return fixture


def _write_text_boundary_report(fixture: Path, candidate_id: str = "TB001") -> None:
    report = fixture / "build" / "text_boundary_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-boundary-clash.v1",
                "fixture": fixture.name,
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "text_crosses_vertical_boundary",
                        "text": "Old Label",
                        "boundary_id": "column_rule",
                    }
                ],
                "total": 1,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_undeclared_geometry_report(
    fixture: Path,
    candidates: list[dict[str, object]],
) -> None:
    report = fixture / "build" / "undeclared_geometry.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.undeclared-geometry.v1",
                "fixture": fixture.name,
                "candidates": candidates,
                "total": len(candidates),
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_quality_defect_ledger_ingests_undeclared_geometry_near_miss(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    _write_undeclared_geometry_report(
        fixture,
        [
            {
                "id": "UG001",
                "kind": "label_endpoint_near_miss",
                "recommended_action": "add_micro_defect",
                "source_line": 1,
                "nearest_text": "Old Label",
                "evidence": "source line 1 is within 2.0 pt of text 'Old Label'",
                "bbox_pt": [10.0, 20.0, 30.0, 20.0],
                "distance_pt": 2.0,
            },
            {
                "id": "UG002",
                "kind": "undeclared_column_rule",
                "recommended_action": "add_spec_check",
                "source_line": 2,
                "nearest_text": "",
                "evidence": "source line 2 line lacks text_boundary_check",
                "bbox_pt": [40.0, 10.0, 40.0, 50.0],
                "distance_pt": None,
            },
        ],
    )

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    defects = ledger["defects"]
    assert len(defects) == 1, defects
    defect = defects[0]
    assert defect["affected_files"] == ["examples/quality_demo/quality_demo.tex"]
    assert defect["defect_class"] == "text_overlap"
    assert defect["selector_hint"] == {"kind": "line_range", "value": "1:1"}
    assert defect["evidence"] == [
        {
            "uri": "figure://quality_demo/audit/undeclared-geometry",
            "node_id": "UG001",
        }
    ]
    assert defect["patchability"]["state"] == "safe_candidate"
    # add_spec_check hygiene noise must not become a defect.
    assert all(
        evidence["node_id"] != "UG002" for entry in defects for evidence in entry["evidence"]
    )


def _write_visual_clash_report(fixture: Path, candidates: list[dict[str, object]]) -> None:
    report = fixture / "build" / "visual_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "fixture": fixture.name,
                "render_pdf": f"build/{fixture.name}.pdf",
                "candidates": candidates,
                "total": len(candidates),
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_empty_detector_reports(fixture: Path) -> None:
    # The v1.10 critique schema requires every detector report and a crop manifest;
    # summarize_audit_evidence short-circuits to missing_input otherwise.
    build = fixture / "build"
    build.mkdir(parents=True, exist_ok=True)
    empty = {"fixture": fixture.name, "candidates": [], "total": 0}
    for filename, schema in (
        ("text_boundary_clash.json", "figure-agent.text-boundary-clash.v1"),
        ("label_path_proximity.json", "figure-agent.label-path-proximity.v1"),
        ("undeclared_geometry.json", "figure-agent.undeclared-geometry.v1"),
    ):
        if (build / filename).exists():
            continue
        (build / filename).write_text(
            json.dumps({"schema": schema, **empty}) + "\n", encoding="utf-8"
        )


def _write_crop_manifest(fixture: Path, crop_id: str = "full_q1") -> None:
    crop_path = fixture / "build" / "audit_crops" / f"{crop_id}.png"
    crop_path.parent.mkdir(parents=True, exist_ok=True)
    crop_path.write_bytes(f"crop:{crop_id}\n".encode())
    manifest = fixture / "build" / "audit_crops" / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
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
        )
        + "\n",
        encoding="utf-8",
    )


def _write_visual_clash_critique(fixture: Path, *, kept_visual_clash_ref: str) -> None:
    # A kept (not false-positive) micro_defect links to a finding that carries the
    # two-int tex_lines; this is the real critique convention (tex_lines on findings).
    name = fixture.name
    crop = f"examples/{name}/build/audit_crops/visual_clash/{kept_visual_clash_ref}_A.png"
    (fixture / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1.10\n"
        f"fixture: {name}\n"
        "micro_defects:\n"
        "  - id: M001\n"
        f"    crop: {crop}\n"
        "    kind: line_crosses_label\n"
        "    severity: MAJOR\n"
        f"    observation: {kept_visual_clash_ref} label sits on a filled region.\n"
        "    linked_finding_id: C001\n"
        f"    visual_clash_ref: {kept_visual_clash_ref}\n"
        "    status: open\n"
        "crop_audit_log:\n"
        "  - crop_id: full_q1\n"
        "    path: build/audit_crops/full_q1.png\n"
        "    source: full_render\n"
        "    inspected: true\n"
        "    verdict: defect\n"
        '    linked_micro_defect_id: "M001"\n'
        "    rationale: full_q1 was inspected\n"
        "findings:\n"
        "  - id: C001\n"
        "    severity: MAJOR\n"
        "    category: label_placement\n"
        "    tex_lines:\n"
        "    - 1\n"
        "    - 1\n"
        f"    observation: {kept_visual_clash_ref} label crosses a fill.\n"
        "    suggested_fix: Move the label off the fill.\n"
        "    status: open\n"
        "panels: []\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )


def test_quality_defect_ledger_ingests_adjudicated_visual_clash(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    _write_visual_clash_report(
        fixture,
        [
            {
                "id": "VC001",
                "kind": "text_on_fill",
                "tex_lines": None,
                "text": "Origin",
                "bbox_px": [1, 2, 3, 4],
                "metric": {"luma_std": 33.7},
            }
        ],
    )
    _write_empty_detector_reports(fixture)
    _write_crop_manifest(fixture)
    _write_visual_clash_critique(fixture, kept_visual_clash_ref="VC001")

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    defects = ledger["defects"]
    assert len(defects) == 1, defects
    defect = defects[0]
    assert defect["affected_files"] == ["examples/quality_demo/quality_demo.tex"]
    assert defect["selector_hint"] == {"kind": "line_range", "value": "1:1"}
    assert defect["patchability"]["state"] == "safe_candidate"
    assert defect["evidence"] == [
        {
            "uri": "figure://quality_demo/audit/visual-clash",
            "node_id": "VC001",
        }
    ]


def test_quality_defect_ledger_visual_clash_suppressed_when_audit_evidence_incomplete(
    tmp_path: Path,
) -> None:
    # Identical to the passing visual_clash test EXCEPT the crop manifest is absent, so
    # summarize_audit_evidence yields missing_input / linked_defect_count 0. This locks in
    # the summarize gate as load-bearing: it suppresses the defect to avoid fabricating it
    # from stale evidence (e.g. a git clean that removed build/audit_crops/manifest.json).
    # The _kept_visual_clash_finding_ids filter alone -- which only reads the critique
    # frontmatter -- would still find VC001's kept ref->finding->tex_lines and emit a defect.
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    _write_visual_clash_report(
        fixture,
        [
            {
                "id": "VC001",
                "kind": "text_on_fill",
                "tex_lines": None,
                "text": "Origin",
                "bbox_px": [1, 2, 3, 4],
                "metric": {"luma_std": 33.7},
            }
        ],
    )
    _write_empty_detector_reports(fixture)
    # Deliberately NO crop manifest -> audit evidence is incomplete.
    _write_visual_clash_critique(fixture, kept_visual_clash_ref="VC001")

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    visual_clash_evidence = [
        {"uri": "figure://quality_demo/audit/visual-clash", "node_id": "VC001"}
    ]
    assert all(defect["evidence"] != visual_clash_evidence for defect in ledger["defects"])


def test_quality_defect_ledger_drops_false_positive_visual_clash(tmp_path: Path) -> None:
    # Isolate the _kept_visual_clash_finding_ids false-positive predicate. VC001 is a kept
    # defect that OPENS the summarize gate (linked_defect_count > 0), so the gate cannot be
    # what suppresses VC002 -- only the per-candidate false-positive predicate in _kept can.
    # Both candidates carry valid findings + tex_lines + linked_finding_id, so VC002 differs
    # from VC001 ONLY in its accept_simplification/false_positive status. If the predicate
    # were removed, VC002 would leak through and this test would fail.
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    _write_visual_clash_report(
        fixture,
        [
            {
                "id": "VC001",
                "kind": "text_on_fill",
                "tex_lines": None,
                "text": "Origin",
                "bbox_px": [1, 2, 3, 4],
                "metric": {"luma_std": 33.7},
            },
            {
                "id": "VC002",
                "kind": "text_on_fill",
                "tex_lines": None,
                "text": "Texture",
                "bbox_px": [5, 6, 7, 8],
                "metric": {"luma_std": 33.7},
            },
        ],
    )
    _write_empty_detector_reports(fixture)
    _write_crop_manifest(fixture)
    (fixture / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1.10\n"
        f"fixture: {fixture.name}\n"
        "micro_defects:\n"
        "  - id: M001\n"
        f"    crop: examples/{fixture.name}/build/audit_crops/visual_clash/VC001_A.png\n"
        "    kind: line_crosses_label\n"
        "    severity: MAJOR\n"
        "    observation: VC001 label sits on a filled region.\n"
        "    linked_finding_id: C001\n"
        "    visual_clash_ref: VC001\n"
        "    status: open\n"
        "  - id: M002\n"
        f"    crop: examples/{fixture.name}/build/audit_crops/visual_clash/VC002_A.png\n"
        "    kind: line_crosses_label\n"
        "    severity: NIT\n"
        "    observation: VC002 marks fill texture, not a real label defect.\n"
        "    linked_finding_id: C002\n"
        "    visual_clash_ref: VC002\n"
        "    status: accept_simplification\n"
        "    accept_simplification_reason: false_positive\n"
        "    accept_simplification_rationale: VC002 marks fill texture, not a real label defect.\n"
        "crop_audit_log:\n"
        "  - crop_id: full_q1\n"
        "    path: build/audit_crops/full_q1.png\n"
        "    source: full_render\n"
        "    inspected: true\n"
        "    verdict: defect\n"
        '    linked_micro_defect_id: "M001"\n'
        "    rationale: full_q1 was inspected\n"
        "findings:\n"
        "  - id: C001\n"
        "    severity: MAJOR\n"
        "    category: label_placement\n"
        "    tex_lines:\n"
        "    - 1\n"
        "    - 1\n"
        "    observation: VC001 label crosses a fill.\n"
        "    suggested_fix: Move the label off the fill.\n"
        "    status: open\n"
        "  - id: C002\n"
        "    severity: MAJOR\n"
        "    category: label_placement\n"
        "    tex_lines:\n"
        "    - 2\n"
        "    - 2\n"
        "    observation: VC002 label crosses a fill.\n"
        "    suggested_fix: Move the label off the fill.\n"
        "    status: open\n"
        "panels: []\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    visual_clash_nodes = {
        evidence["node_id"]
        for defect in ledger["defects"]
        for evidence in defect["evidence"]
        if "visual-clash" in evidence["uri"]
    }
    # The kept VC001 is emitted; the false-positive VC002 is dropped by the predicate.
    assert "VC001" in visual_clash_nodes
    assert "VC002" not in visual_clash_nodes


def test_quality_defect_ledger_is_read_only_and_deterministic(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    _write_text_boundary_report(fixture)
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))

    first = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    second = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert first == second
    assert first["schema"] == "figure-agent.quality-defect-ledger.v1"
    assert first["fixture"] == "quality_demo"
    assert first["defects"][0]["id"] == "QD001"
    assert first["defects"][0]["evidence"] == [
        {
            "uri": "figure://quality_demo/audit/text-boundary",
            "node_id": "checker:text_boundary",
        }
    ]
    assert first["defects"][0]["patchability"]["state"] == "safe_candidate"
    assert first["defects"][0]["freshness"]["audit_evidence_graph_hash"].startswith("sha256:")
    after = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    assert after == before


def test_quality_defect_ledger_handles_missing_critique_without_raising(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_fixture(workspace)

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert ledger["defects"]
    assert ledger["defects"][0]["defect_class"] == "render_missing"
    assert ledger["defects"][0]["owner"] == "human"
    assert ledger["defects"][0]["patchability"]["state"] == "human_required"


def test_quality_defect_ledger_blocks_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    outside = tmp_path / "outside.tex"
    outside.write_text("secret", encoding="utf-8")
    (fixture / "quality_demo.tex").unlink()
    (fixture / "quality_demo.tex").symlink_to(outside)

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert ledger["defects"][0]["patchability"]["state"] == "unsupported"
    assert "path_escape" in ledger["defects"][0]["patchability"]["blocked_codes"]
