from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_patch_apply  # noqa: E402
import quality_patch_plan  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


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


def _plan(fixture: Path) -> dict:
    name = fixture.name
    source_rel = f"examples/{name}/{name}.tex"
    plan = {
        "schema": "figure-agent.quality-patch-plan.v1",
        "fixture": name,
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
                "repair_family": "label_reflow",
                "selector": {
                    "kind": "semantic_anchor",
                    "selector_id": "panel_f.label.repulsion",
                    "anchor_start": "% figure-agent:start panel_f.label.repulsion",
                    "anchor_end": "% figure-agent:end panel_f.label.repulsion",
                    "source_hash": file_sha256(fixture / f"{name}.tex"),
                },
                "proposed_change": {
                    "summary": "move label",
                    "patch": (
                        f"--- {source_rel}\n"
                        f"+++ {source_rel}\n"
                        "@@ -2 +2 @@\n"
                        "-\\node (label-a) at (0,0) {Old Label};\n"
                        "+\\node (label-a) at (0.2,0) {Old Label};\n"
                    ),
                },
                "protected_invariants": [
                    "Coulomb repulsion",
                    "electrode separation",
                ],
                "change_budget": {
                    "max_source_blocks": 1,
                    "max_changed_lines": 6,
                    "max_rendered_pixel_ratio": 0.03,
                },
                "semantic_guard": {
                    "allowed": False,
                    "state": "pending_post_render_verification",
                },
            }
        ],
        "verification": {
            "required_commands": [
                f"fig-agent compile {name} --strict",
                f"fig-agent status {name} --json",
            ]
        },
    }
    plan["plan_id"] = quality_patch_plan.compute_plan_id(plan)
    return plan


def _write_plan(fixture: Path, plan: dict) -> Path:
    path = fixture / "build" / "quality" / "patch_plan.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _source_mutation_decision(
    plan: dict,
    *,
    authorized_candidate_hash: str | None = None,
    packet_schema: str = "figure-agent.quality-patch-plan.v1",
    packet_path: str = "build/quality/patch_plan.json",
    packet_recommendation: str = "apply_quality_patch_plan",
) -> dict:
    return {
        "schema": "figure-agent.human-decision-record.v1",
        "fixture": plan["fixture"],
        "packet_schema": packet_schema,
        "packet_path": packet_path,
        "packet_recommendation": packet_recommendation,
        "queue_run_id": "quality-patch-apply-001",
        "decision_kind": "apply_quality_patch_plan",
        "agent_recommendation": "Apply exactly one hash-bound quality patch plan.",
        "human_decision": "approve this exact quality patch plan",
        "human_note": "Source mutation is limited to this plan id and hash.",
        "follow_up": {"command": "fig-agent apply-plan quality_demo --apply"},
        "mutation_boundary": "source_mutation_allowed",
        "authorized_candidate_id": plan["plan_id"],
        "authorized_candidate_hash": authorized_candidate_hash or plan["plan_id"],
    }


def _run_fig_agent(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return subprocess.run(
        ["uv", "run", "python", str(FIG_AGENT), *args],
        cwd=PLUGIN_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


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


def test_apply_plan_refuses_source_mutation_without_authorization(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan_path = _write_plan(fixture, _plan(fixture))
    before = (fixture / "quality_demo.tex").read_text(encoding="utf-8")

    with pytest.raises(
        quality_patch_apply.QualityPatchApplyError,
        match="source_mutation_decision_missing",
    ):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            apply=True,
        )

    assert (fixture / "quality_demo.tex").read_text(encoding="utf-8") == before


def test_apply_plan_refuses_authorization_for_a_different_plan_hash(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    plan_path = _write_plan(fixture, plan)
    before = (fixture / "quality_demo.tex").read_text(encoding="utf-8")

    with pytest.raises(
        quality_patch_apply.QualityPatchApplyError,
        match="source_mutation_decision_candidate_hash_mismatch",
    ):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(
                plan,
                authorized_candidate_hash="sha256:" + "9" * 64,
            ),
            apply=True,
        )

    assert (fixture / "quality_demo.tex").read_text(encoding="utf-8") == before


def test_apply_plan_refuses_authorization_from_an_unrelated_packet_schema(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    plan_path = _write_plan(fixture, plan)
    before = (fixture / "quality_demo.tex").read_text(encoding="utf-8")

    with pytest.raises(
        quality_patch_apply.QualityPatchApplyError,
        match="source_mutation_decision_packet_schema_mismatch",
    ):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(
                plan,
                packet_schema="figure-agent.release-decision-packet.v1",
            ),
            apply=True,
        )

    assert (fixture / "quality_demo.tex").read_text(encoding="utf-8") == before


@pytest.mark.parametrize(
    ("decision_overrides", "error_code"),
    [
        (
            {"packet_path": "build/quality/other_plan.json"},
            "source_mutation_decision_packet_path_mismatch",
        ),
        (
            {"packet_recommendation": "reject_current_artifact"},
            "source_mutation_decision_packet_recommendation_mismatch",
        ),
    ],
)
def test_apply_plan_refuses_authorization_for_different_packet_identity(
    tmp_path: Path,
    decision_overrides: dict[str, str],
    error_code: str,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    plan_path = _write_plan(fixture, plan)

    with pytest.raises(quality_patch_apply.QualityPatchApplyError, match=error_code):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(
                plan,
                **decision_overrides,
            ),
            apply=True,
        )


def test_apply_plan_writes_source_and_rollback_with_hash_bound_authorization(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    plan_path = _write_plan(fixture, plan)
    decision = _source_mutation_decision(plan)
    source = fixture / "quality_demo.tex"
    before = source.read_text(encoding="utf-8")

    result = quality_patch_apply.apply_quality_patch_plan(
        "quality_demo",
        plan_path=plan_path,
        workspace_root=workspace,
        source_mutation_decision=decision,
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
    assert result["authorization"] == {
        "decision_kind": "apply_quality_patch_plan",
        "record_hash": quality_patch_apply.authorization_record_hash(decision),
        "authorized_candidate_id": plan["plan_id"],
        "authorized_candidate_hash": plan["plan_id"],
    }
    quality_patch_apply._run_patch(
        workspace,
        rollback.read_text(encoding="utf-8"),
        dry_run=False,
    )
    assert source.read_text(encoding="utf-8") == before


def test_fig_agent_apply_plan_uses_hash_bound_authorization(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    _write_plan(fixture, plan)
    decision_path = tmp_path / "source-mutation-decision.json"
    decision_path.write_text(
        json.dumps(_source_mutation_decision(plan)),
        encoding="utf-8",
    )

    result = _run_fig_agent(
        workspace,
        "apply-plan",
        "quality_demo",
        "--plan",
        "build/quality/patch_plan.json",
        "--apply",
        "--authorization",
        str(decision_path),
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["applied"] is True
    assert "0.2,0" in (fixture / "quality_demo.tex").read_text(encoding="utf-8")


def test_apply_plan_keeps_source_unchanged_when_rollback_preparation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    plan_path = _write_plan(fixture, plan)
    source = fixture / "quality_demo.tex"
    before = source.read_bytes()

    def fail_rollback(*_args: object, **_kwargs: object) -> Path:
        raise OSError("rollback storage unavailable")

    monkeypatch.setattr(quality_patch_apply, "_write_rollback_patch", fail_rollback)

    with pytest.raises(OSError, match="rollback storage unavailable"):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(plan),
            apply=True,
        )

    assert source.read_bytes() == before


def test_apply_plan_rollback_restores_a_line_count_change(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    source_rel = "examples/quality_demo/quality_demo.tex"
    plan["operations"][0]["proposed_change"]["patch"] = (
        f"--- {source_rel}\n"
        f"+++ {source_rel}\n"
        "@@ -2 +2,2 @@\n"
        "-\\node (label-a) at (0,0) {Old Label};\n"
        "+\\node (label-a) at (0.2,0) {Old Label};\n"
        "+\\coordinate (label-a-guide) at (0.2,0);\n"
    )
    plan["plan_id"] = quality_patch_plan.compute_plan_id(plan)
    plan_path = _write_plan(fixture, plan)
    source = fixture / "quality_demo.tex"
    before = source.read_text(encoding="utf-8")

    result = quality_patch_apply.apply_quality_patch_plan(
        "quality_demo",
        plan_path=plan_path,
        workspace_root=workspace,
        source_mutation_decision=_source_mutation_decision(plan),
        apply=True,
    )

    rollback = workspace / result["rollback_patch"]
    quality_patch_apply._run_patch(
        workspace,
        rollback.read_text(encoding="utf-8"),
        dry_run=False,
    )
    assert source.read_text(encoding="utf-8") == before


def test_apply_plan_rollback_restores_source_without_final_newline(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "quality_demo.tex"
    source.write_text(source.read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8")
    plan = _plan(fixture)
    source_rel = "examples/quality_demo/quality_demo.tex"
    plan["operations"][0]["proposed_change"]["patch"] = (
        f"--- {source_rel}\n"
        f"+++ {source_rel}\n"
        "@@ -2 +2,2 @@\n"
        "-\\node (label-a) at (0,0) {Old Label};\n"
        "+\\node (label-a) at (0.2,0) {Old Label};\n"
        "+\\coordinate (label-a-guide) at (0.2,0);\n"
    )
    plan["plan_id"] = quality_patch_plan.compute_plan_id(plan)
    plan_path = _write_plan(fixture, plan)
    before = source.read_bytes()

    result = quality_patch_apply.apply_quality_patch_plan(
        "quality_demo",
        plan_path=plan_path,
        workspace_root=workspace,
        source_mutation_decision=_source_mutation_decision(plan),
        apply=True,
    )

    rollback = workspace / result["rollback_patch"]
    quality_patch_apply._run_patch(
        workspace,
        rollback.read_text(encoding="utf-8"),
        dry_run=False,
    )
    assert source.read_bytes() == before


def test_rollback_artifact_handles_changed_final_line_without_newline(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "quality_demo"
    fixture.mkdir(parents=True)
    source_rel = "examples/quality_demo/quality_demo.tex"
    source = workspace / source_rel
    source.write_text("candidate", encoding="utf-8")

    rollback = quality_patch_apply._write_rollback_patch(
        fixture,
        "sha256:" + "1" * 64,
        source_rel,
        "original",
        "candidate",
    )

    quality_patch_apply._run_patch(
        workspace,
        rollback.read_text(encoding="utf-8"),
        dry_run=False,
    )
    assert source.read_bytes() == b"original"


def test_apply_plan_source_replace_failure_keeps_original_and_recovery_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    plan_path = _write_plan(fixture, plan)
    source = fixture / "quality_demo.tex"
    before = source.read_bytes()
    real_replace = os.replace

    def fail_source_replace(src: str | Path, dst: str | Path) -> None:
        if Path(dst) == source:
            raise OSError("source replace interrupted")
        real_replace(src, dst)

    monkeypatch.setattr(quality_patch_apply.os, "replace", fail_source_replace)

    with pytest.raises(OSError, match="source replace interrupted"):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(plan),
            apply=True,
        )

    assert source.read_bytes() == before
    receipt = json.loads(
        (fixture / "build" / "quality" / "patch_result.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["applied"] is False
    assert receipt["outcome"] == "mutation_prepared"
    assert receipt["recovery_required"] is True
    assert (workspace / receipt["rollback_patch"]).is_file()


def test_apply_plan_atomic_replace_preserves_source_mode(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "quality_demo.tex"
    source.chmod(0o640)
    plan = _plan(fixture)
    plan_path = _write_plan(fixture, plan)

    quality_patch_apply.apply_quality_patch_plan(
        "quality_demo",
        plan_path=plan_path,
        workspace_root=workspace,
        source_mutation_decision=_source_mutation_decision(plan),
        apply=True,
    )

    assert stat.S_IMODE(source.stat().st_mode) == 0o640


def test_apply_plan_refuses_symlink_source_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "quality_demo.tex"
    backing = fixture / "quality_demo.backing.tex"
    source.rename(backing)
    source.symlink_to(backing.name)
    plan = _plan(fixture)
    plan_path = _write_plan(fixture, plan)
    before = backing.read_bytes()

    with pytest.raises(
        quality_patch_apply.QualityPatchApplyError,
        match="plan_target_forbidden: source symlink forbidden",
    ):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(plan),
            apply=True,
        )

    assert source.is_symlink()
    assert backing.read_bytes() == before


def test_apply_plan_final_receipt_failure_leaves_durable_recovery_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    plan_path = _write_plan(fixture, plan)
    source = fixture / "quality_demo.tex"
    before = source.read_text(encoding="utf-8")
    real_write_json = quality_patch_apply._atomic_write_json
    writes = 0

    def fail_final_receipt(path: Path, payload: dict) -> None:
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("final receipt unavailable")
        real_write_json(path, payload)

    monkeypatch.setattr(quality_patch_apply, "_atomic_write_json", fail_final_receipt)

    with pytest.raises(OSError, match="final receipt unavailable"):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(plan),
            apply=True,
        )

    receipt = json.loads(
        (fixture / "build" / "quality" / "patch_result.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["outcome"] == "mutation_prepared"
    assert receipt["recovery_required"] is True
    assert source.read_text(encoding="utf-8") != before
    rollback = workspace / receipt["rollback_patch"]
    quality_patch_apply._run_patch(
        workspace,
        rollback.read_text(encoding="utf-8"),
        dry_run=False,
    )
    assert source.read_text(encoding="utf-8") == before


def test_apply_plan_refuses_plan_content_that_does_not_match_plan_id(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    source_rel = "examples/quality_demo/quality_demo.tex"
    plan["operations"][0]["proposed_change"]["patch"] = (
        f"--- {source_rel}\n"
        f"+++ {source_rel}\n"
        "@@ -2 +2 @@\n"
        "-\\node (label-a) at (0,0) {Old Label};\n"
        "+\\node (label-a) at (0.4,0) {Old Label};\n"
    )
    plan_path = _write_plan(fixture, plan)
    before = (fixture / "quality_demo.tex").read_text(encoding="utf-8")

    with pytest.raises(
        quality_patch_apply.QualityPatchApplyError,
        match="plan_id_mismatch",
    ):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(plan),
            apply=True,
        )

    assert (fixture / "quality_demo.tex").read_text(encoding="utf-8") == before


def test_apply_plan_refuses_stale_or_replayed_plan(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    plan_path = _write_plan(fixture, plan)
    (fixture / "quality_demo.tex").write_text("changed\n", encoding="utf-8")

    with pytest.raises(quality_patch_apply.QualityPatchApplyError, match="source_hash_mismatch"):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(plan),
            apply=True,
        )


def test_apply_plan_refuses_when_mutation_lock_exists(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    plan_path = _write_plan(fixture, plan)
    lock = fixture / "build" / ".quality-locks" / "mutation.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("active", encoding="utf-8")

    with pytest.raises(quality_patch_apply.QualityPatchApplyError, match="operation_in_progress"):
        quality_patch_apply.apply_quality_patch_plan(
            "quality_demo",
            plan_path=plan_path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(plan),
            apply=True,
        )


def test_apply_refuses_changed_protected_invariant(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    relative = "examples/quality_demo/quality_demo.tex"
    plan["operations"][0]["proposed_change"]["patch"] = (
        f"--- {relative}\n"
        f"+++ {relative}\n"
        "@@ -3 +3 @@\n"
        "-\\node at (1,0) {Coulomb repulsion};\n"
        "+\\node at (1,0) {changed relation};\n"
    )
    plan["plan_id"] = quality_patch_plan.compute_plan_id(plan)
    path = _write_plan(fixture, plan)
    with pytest.raises(
        quality_patch_apply.QualityPatchApplyError,
        match="protected_invariant_changed",
    ):
        quality_patch_apply.apply_quality_patch_plan(
            fixture.name,
            plan_path=path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(plan),
            apply=True,
        )


def test_apply_receipt_keeps_acceptance_unclaimed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    path = _write_plan(fixture, plan)
    result = quality_patch_apply.apply_quality_patch_plan(
        fixture.name,
        plan_path=path,
        workspace_root=workspace,
        source_mutation_decision=_source_mutation_decision(plan),
        apply=True,
    )
    assert result["publication_acceptance"] == "not_claimed"
    assert result["post_render_verification"] == "pending"


def test_apply_refuses_patch_outside_declared_anchor(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    relative = "examples/quality_demo/quality_demo.tex"
    plan["operations"][0]["proposed_change"]["patch"] = (
        f"--- {relative}\n"
        f"+++ {relative}\n"
        "@@ -5 +5 @@\n"
        "-% figure-agent:end panel_f.label.repulsion\n"
        "+% changed end marker\n"
    )
    plan["plan_id"] = quality_patch_plan.compute_plan_id(plan)
    path = _write_plan(fixture, plan)
    with pytest.raises(
        quality_patch_apply.QualityPatchApplyError,
        match="patch_outside_anchor",
    ):
        quality_patch_apply.apply_quality_patch_plan(
            fixture.name,
            plan_path=path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(plan),
            apply=True,
        )


def test_apply_refuses_change_budget_overrun(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    plan["operations"][0]["change_budget"]["max_changed_lines"] = 1
    plan["plan_id"] = quality_patch_plan.compute_plan_id(plan)
    path = _write_plan(fixture, plan)
    with pytest.raises(
        quality_patch_apply.QualityPatchApplyError,
        match="change_budget_exceeded",
    ):
        quality_patch_apply.apply_quality_patch_plan(
            fixture.name,
            plan_path=path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(plan),
            apply=True,
        )


def test_apply_refuses_multiple_source_blocks(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    plan = _plan(fixture)
    relative = "examples/quality_demo/quality_demo.tex"
    plan["operations"][0]["proposed_change"]["patch"] += (
        f"--- {relative}\n"
        f"+++ {relative}\n"
        "@@ -3 +3 @@\n"
        "-\\node at (1,0) {Coulomb repulsion};\n"
        "+\\node at (1.1,0) {Coulomb repulsion};\n"
    )
    plan["plan_id"] = quality_patch_plan.compute_plan_id(plan)
    path = _write_plan(fixture, plan)
    with pytest.raises(
        quality_patch_apply.QualityPatchApplyError,
        match="change_budget_exceeded",
    ):
        quality_patch_apply.apply_quality_patch_plan(
            fixture.name,
            plan_path=path,
            workspace_root=workspace,
            source_mutation_decision=_source_mutation_decision(plan),
            apply=True,
        )
