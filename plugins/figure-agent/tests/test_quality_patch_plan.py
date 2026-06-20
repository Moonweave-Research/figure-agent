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
