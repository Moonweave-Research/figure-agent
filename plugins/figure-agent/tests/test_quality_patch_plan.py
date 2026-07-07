from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_patch_plan  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


def _fixture(workspace: Path, name: str = "quality_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    return fixture


def _ledger(fixture: Path) -> dict:
    source = fixture / f"{fixture.name}.tex"
    return {
        "schema": "figure-agent.quality-defect-ledger.v1",
        "fixture": fixture.name,
        "ledger_hash": "sha256:" + "a" * 64,
        "defects": [
            {
                "id": "QD001",
                "defect_class": "text_overlap",
                "owner": "tool",
                "affected_files": [f"examples/{fixture.name}/{fixture.name}.tex"],
                "evidence": [{"uri": f"figure://{fixture.name}/audit/text-boundary"}],
                "patchability": {
                    "state": "safe_candidate",
                    "reasons": ["mechanical_text_overlap"],
                    "blocked_codes": [],
                    "may_edit": False,
                    "policy_version": "figure-agent.quality-patch-policy.v1",
                },
                "selector_hint": {"kind": "node_name", "value": "label-a"},
                "suggested_change": {
                    "operation_type": "tikz_coordinate_adjust",
                    "summary": "Move label-a slightly right",
                    "patch": (
                        f"--- examples/{fixture.name}/{fixture.name}.tex\n"
                        f"+++ examples/{fixture.name}/{fixture.name}.tex\n"
                        "@@ -1 +1 @@\n"
                        "-\\node (label-a) at (0,0) {Old Label};\n"
                        "+\\node (label-a) at (0.2,0) {Old Label};\n"
                    ),
                },
                "freshness": {
                    "audit_evidence_graph_hash": "sha256:" + "b" * 64,
                    "source_hashes": {
                        f"examples/{fixture.name}/{fixture.name}.tex": file_sha256(source)
                    },
                },
            }
        ],
    }


def test_patch_plan_is_deterministic_and_contains_verification_commands(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    ledger = _ledger(fixture)

    first = quality_patch_plan.build_quality_patch_plan(
        "quality_demo",
        ledger,
        workspace_root=workspace,
    )
    second = quality_patch_plan.build_quality_patch_plan(
        "quality_demo",
        ledger,
        workspace_root=workspace,
    )

    assert first == second
    assert first["schema"] == "figure-agent.quality-patch-plan.v1"
    assert first["plan_id"].startswith("sha256:")
    assert first["operations"][0]["selector"]["confidence"] == "exact"
    assert first["operations"][0]["semantic_guard"]["allowed"] is True
    assert first["verification"]["required_commands"] == [
        "fig-agent compile quality_demo --strict",
        "fig-agent status quality_demo --json",
    ]


def _multiline_fixture(workspace: Path, name: str = "quality_multiline_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text(
        "% Panel A\n\\draw (0.45,6.15) -- (4.78,6.15);\n\\node at (1.0, 2.0) {label};\n",
        encoding="utf-8",
    )
    return fixture


def _multiline_ledger(fixture: Path) -> dict:
    source = fixture / f"{fixture.name}.tex"
    return {
        "schema": "figure-agent.quality-defect-ledger.v1",
        "fixture": fixture.name,
        "ledger_hash": "sha256:" + "c" * 64,
        "defects": [
            {
                "id": "QD001",
                "defect_class": "text_overlap",
                "owner": "tool",
                "affected_files": [f"examples/{fixture.name}/{fixture.name}.tex"],
                "evidence": [{"uri": f"figure://{fixture.name}/audit/text-boundary"}],
                "patchability": {
                    "state": "safe_candidate",
                    "reasons": ["mechanical_text_overlap"],
                    "blocked_codes": [],
                    "may_edit": False,
                    "policy_version": "figure-agent.quality-patch-policy.v1",
                },
                "selector_hint": {"kind": "line_range", "value": "2:2"},
                "suggested_change": {
                    "operation_type": "tikz_coordinate_adjust",
                    "summary": "Clear the dashed baseline endpoint by a bounded amount",
                },
                "freshness": {
                    "audit_evidence_graph_hash": "sha256:" + "d" * 64,
                    "source_hashes": {
                        f"examples/{fixture.name}/{fixture.name}.tex": file_sha256(source)
                    },
                },
            }
        ],
    }


def test_patch_from_selector_emits_bounded_offset_on_target_line(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _multiline_fixture(workspace)
    ledger = _multiline_ledger(fixture)

    plan = quality_patch_plan.build_quality_patch_plan(
        "quality_multiline_demo",
        ledger,
        workspace_root=workspace,
    )

    operation = plan["operations"][0]
    patch = operation["proposed_change"]["patch"]
    assert patch != ""
    assert "@@ -2 +2 @@" in patch
    assert "-\\draw (0.45,6.15) -- (4.78,6.15);" in patch
    assert "+\\draw (0.55, 6.15) -- (4.78,6.15);" in patch


def test_patch_from_selector_handoff_summary_when_no_coordinate(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    name = "quality_no_coord_demo"
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text(
        "% Panel A\n\\node {pure text label};\n",
        encoding="utf-8",
    )
    source = fixture / f"{name}.tex"
    ledger = {
        "schema": "figure-agent.quality-defect-ledger.v1",
        "fixture": name,
        "ledger_hash": "sha256:" + "e" * 64,
        "defects": [
            {
                "id": "QD001",
                "defect_class": "text_overlap",
                "owner": "tool",
                "affected_files": [f"examples/{name}/{name}.tex"],
                "evidence": [{"uri": f"figure://{name}/audit/text-boundary"}],
                "patchability": {
                    "state": "safe_candidate",
                    "reasons": ["mechanical_text_overlap"],
                    "blocked_codes": [],
                    "may_edit": False,
                    "policy_version": "figure-agent.quality-patch-policy.v1",
                },
                "selector_hint": {"kind": "line_range", "value": "2:2"},
                "suggested_change": {"operation_type": "tikz_coordinate_adjust"},
                "freshness": {
                    "audit_evidence_graph_hash": "sha256:" + "f" * 64,
                    "source_hashes": {f"examples/{name}/{name}.tex": file_sha256(source)},
                },
            }
        ],
    }

    plan = quality_patch_plan.build_quality_patch_plan(name, ledger, workspace_root=workspace)

    proposed = plan["operations"][0]["proposed_change"]
    assert proposed["patch"] == ""
    assert proposed.get("manual_only") is True
    assert f"examples/{name}/{name}.tex:2" in proposed["summary"]


def test_alignment_defect_without_axis_delta_is_manual_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    name = "quality_alignment_demo"
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text(
        "\\node[anchor=south] at (6.975, 4.61) {ISPD};\n",
        encoding="utf-8",
    )
    source = fixture / f"{name}.tex"
    ledger = {
        "schema": "figure-agent.quality-defect-ledger.v1",
        "fixture": name,
        "ledger_hash": "sha256:" + "1" * 64,
        "defects": [
            {
                "id": "QD001",
                "defect_class": "label_offset",
                "source_detector": "semantic_assertions",
                "owner": "tool",
                "affected_files": [f"examples/{name}/{name}.tex"],
                "evidence": [
                    {
                        "uri": f"figure://{name}/audit/semantic-assertions",
                        "node_id": "row2-subtitle-baseline",
                        "kind": "baseline_aligned",
                        "edit_target": "ISPD",
                        "measured_delta_cm": 0.418,
                    }
                ],
                "patchability": {
                    "state": "safe_candidate",
                    "reasons": ["mechanical_label_offset"],
                    "blocked_codes": [],
                    "may_edit": False,
                    "policy_version": "figure-agent.quality-patch-policy.v1",
                },
                "selector_hint": {
                    "kind": "line_range",
                    "value": "1:1",
                    "edit_target": "ISPD",
                },
                "suggested_change": {
                    "operation_type": "bounded_coordinate_offset",
                    "summary": "Resolve declared semantic assertion violation",
                },
                "freshness": {
                    "audit_evidence_graph_hash": "sha256:" + "2" * 64,
                    "source_hashes": {f"examples/{name}/{name}.tex": file_sha256(source)},
                },
            }
        ],
    }

    plan = quality_patch_plan.build_quality_patch_plan(name, ledger, workspace_root=workspace)

    proposed = plan["operations"][0]["proposed_change"]
    assert proposed["patch"] == ""
    assert proposed.get("manual_only") is True
    assert "axis/direction" in proposed["summary"]


def test_patch_plan_refuses_forbidden_targets(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    ledger = _ledger(fixture)
    ledger["defects"][0]["affected_files"] = [f"examples/{fixture.name}/critique.md"]

    plan = quality_patch_plan.build_quality_patch_plan(
        "quality_demo",
        ledger,
        workspace_root=workspace,
    )

    assert plan["operations"] == []
    assert plan["refusals"][0]["code"] == "plan_target_forbidden"
