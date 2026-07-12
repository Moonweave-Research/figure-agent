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
        "% figure-agent:start panel_f.label.repulsion\n"
        "\\node (label-a) at (0,0) {Old Label};\n"
        "\\node at (1,0) {Coulomb repulsion};\n"
        "\\node at (2,0) {electrode separation};\n"
        "% figure-agent:end panel_f.label.repulsion\n",
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
                "repair_family": "label_reflow",
                "affected_files": [f"examples/{fixture.name}/{fixture.name}.tex"],
                "evidence": [{"uri": f"figure://{fixture.name}/audit/text-boundary"}],
                "attribution": {"state": "exact"},
                "patchability": {
                    "state": "safe_candidate",
                    "reasons": ["mechanical_text_overlap"],
                    "blocked_codes": [],
                    "may_edit": False,
                    "policy_version": "figure-agent.quality-patch-policy.v1",
                },
                "selector_hint": {
                    "kind": "semantic_anchor",
                    "selector_id": "panel_f.label.repulsion",
                    "anchor_start": "% figure-agent:start panel_f.label.repulsion",
                    "anchor_end": "% figure-agent:end panel_f.label.repulsion",
                    "source_hash": file_sha256(source),
                },
                "protected_invariants": [
                    "panel_f.coulomb_direction",
                    "panel_f.electrode_relation",
                ],
                "suggested_change": {
                    "operation_type": "tikz_coordinate_adjust",
                    "summary": "Move label-a slightly right",
                    "patch": (
                        f"--- examples/{fixture.name}/{fixture.name}.tex\n"
                        f"+++ examples/{fixture.name}/{fixture.name}.tex\n"
                        "@@ -2 +2 @@\n"
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
    operation = first["operations"][0]
    assert operation["selector"]["selector_id"] == "panel_f.label.repulsion"
    assert "confidence" not in operation["selector"]
    assert operation["protected_invariants"] == [
        "panel_f.coulomb_direction",
        "panel_f.electrode_relation",
    ]
    assert operation["change_budget"] == {
        "max_source_blocks": 1,
        "max_changed_lines": 6,
        "max_rendered_pixel_ratio": 0.03,
    }
    assert operation["semantic_guard"] == {
        "allowed": False,
        "state": "pending_post_render_verification",
    }
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


def test_plan_does_not_upgrade_line_range_to_exact(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _multiline_fixture(workspace)
    ledger = _multiline_ledger(fixture)
    ledger["defects"][0]["patchability"]["state"] = "assisted_only"

    plan = quality_patch_plan.build_quality_patch_plan(
        "quality_multiline_demo",
        ledger,
        workspace_root=workspace,
    )

    assert plan["operations"] == []
    assert plan["refusals"][0]["code"] == "exact_selector_required"


def test_line_range_without_coordinate_is_refused_not_upgraded(tmp_path: Path) -> None:
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
                    "state": "assisted_only",
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

    assert plan["operations"] == []
    assert plan["refusals"][0]["code"] == "exact_selector_required"


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
