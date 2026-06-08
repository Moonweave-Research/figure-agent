from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_patch_apply  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


def _fixture(workspace: Path, name: str = "quality_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    return fixture


def _plan(fixture: Path) -> dict:
    name = fixture.name
    source_rel = f"examples/{name}/{name}.tex"
    return {
        "schema": "figure-agent.quality-patch-plan.v1",
        "fixture": name,
        "plan_id": "sha256:" + "1" * 64,
        "created_from": {
            "source_hashes": {source_rel: file_sha256(fixture / f"{name}.tex")},
            "defect_ledger_hash": "sha256:" + "2" * 64,
            "audit_evidence_graph_hash": "sha256:" + "3" * 64,
        },
        "operations": [
            {
                "id": "OP001",
                "defect_id": "QD001",
                "file": source_rel,
                "operation_type": "tikz_coordinate_adjust",
                "selector": {"kind": "node_name", "value": "label-a", "confidence": "exact"},
                "proposed_change": {
                    "summary": "move label",
                    "patch": (
                        f"--- {source_rel}\n"
                        f"+++ {source_rel}\n"
                        "@@ -1 +1 @@\n"
                        "-\\node (label-a) at (0,0) {Old Label};\n"
                        "+\\node (label-a) at (0.2,0) {Old Label};\n"
                    ),
                },
                "semantic_guard": {"allowed": True, "reason": "mechanical"},
            }
        ],
        "verification": {
            "required_commands": [
                f"fig-agent compile {name} --strict",
                f"fig-agent status {name} --json",
            ]
        },
    }


def _write_plan(fixture: Path, plan: dict) -> Path:
    path = fixture / "build" / "quality" / "patch_plan.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    return path


def test_apply_plan_dry_run_does_not_mutate_source(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan_path = _write_plan(fixture, _plan(fixture))
    before = (fixture / "quality_demo.tex").read_text(encoding="utf-8")

    result = quality_patch_apply.apply_quality_patch_plan(
        "quality_demo",
        plan_path=plan_path,
        workspace_root=workspace,
        apply=False,
    )

    assert result["schema"] == "figure-agent.quality-patch-result.v1"
    assert result["applied"] is False
    assert (fixture / "quality_demo.tex").read_text(encoding="utf-8") == before


def test_apply_plan_writes_source_and_rollback(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan_path = _write_plan(fixture, _plan(fixture))

    result = quality_patch_apply.apply_quality_patch_plan(
        "quality_demo",
        plan_path=plan_path,
        workspace_root=workspace,
        apply=True,
    )

    assert result["applied"] is True
    assert result["changed_files"] == ["examples/quality_demo/quality_demo.tex"]
    assert "0.2,0" in (fixture / "quality_demo.tex").read_text(encoding="utf-8")
    rollback = workspace / result["rollback_patch"]
    assert rollback.is_file()
    assert "-\\node (label-a) at (0.2,0) {Old Label};" in rollback.read_text(
        encoding="utf-8"
    )


def test_apply_plan_refuses_stale_or_replayed_plan(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan_path = _write_plan(fixture, _plan(fixture))
    (fixture / "quality_demo.tex").write_text("changed\n", encoding="utf-8")

    with pytest.raises(quality_patch_apply.QualityPatchApplyError, match="source_hash_mismatch"):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            apply=True,
        )


def test_apply_plan_refuses_when_mutation_lock_exists(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan_path = _write_plan(fixture, _plan(fixture))
    lock = fixture / "build" / ".quality-locks" / "mutation.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("active", encoding="utf-8")

    with pytest.raises(quality_patch_apply.QualityPatchApplyError, match="operation_in_progress"):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            apply=True,
        )
