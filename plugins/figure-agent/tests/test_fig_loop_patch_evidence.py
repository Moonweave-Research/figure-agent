from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_patch_evidence import (  # noqa: E402
    PATCH_EVIDENCE_SCHEMA,
    PATCH_EVIDENCE_VERDICTS,
    POST_PATCH_EVIDENCE_SCHEMA,
    latest_patch_evidence_baseline,
    patch_evidence_baseline,
    path_evidence,
    post_patch_evidence_verdict,
)
from fig_loop_records import write_json  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


def test_path_evidence_records_missing_file(tmp_path: Path) -> None:
    assert path_evidence(tmp_path, "examples/missing.tex") == {
        "path": "examples/missing.tex",
        "exists": False,
        "sha256": None,
    }


def test_path_evidence_records_existing_file_hash(tmp_path: Path) -> None:
    source = tmp_path / "examples" / "loop_demo" / "loop_demo.tex"
    source.parent.mkdir(parents=True)
    source.write_text("source", encoding="utf-8")

    assert path_evidence(tmp_path, "examples/loop_demo/loop_demo.tex") == {
        "path": "examples/loop_demo/loop_demo.tex",
        "exists": True,
        "sha256": file_sha256(source),
    }


def test_patch_evidence_baseline_returns_none_without_patch_handoff(tmp_path: Path) -> None:
    assert patch_evidence_baseline(tmp_path, None, git_commit=lambda: "abc") is None


def test_patch_evidence_baseline_records_allowed_scope_and_rollback(tmp_path: Path) -> None:
    tex = tmp_path / "examples" / "loop_demo" / "loop_demo.tex"
    tex.parent.mkdir(parents=True)
    tex.write_text("source", encoding="utf-8")
    patch_handoff = {
        "target_type": "finding",
        "target_id": "C001",
        "allowed_edit_scope": [
            "examples/loop_demo/loop_demo.tex",
            "examples/loop_demo/authoring_plan.md",
        ],
    }

    assert patch_evidence_baseline(tmp_path, patch_handoff, git_commit=lambda: "abc123") == {
        "schema": PATCH_EVIDENCE_SCHEMA,
        "phase": "pre_patch",
        "target_type": "finding",
        "target_id": "C001",
        "verdict": "not_evaluated",
        "may_edit": False,
        "pre_patch": {
            "allowed_edit_scope": [
                {
                    "path": "examples/loop_demo/loop_demo.tex",
                    "exists": True,
                    "sha256": file_sha256(tex),
                },
                {
                    "path": "examples/loop_demo/authoring_plan.md",
                    "exists": False,
                    "sha256": None,
                },
            ]
        },
        "post_patch_required_verdicts": list(PATCH_EVIDENCE_VERDICTS),
        "rollback_reference": {
            "git_commit": "abc123",
            "restore_strategy": (
                "restore allowed_edit_scope paths to the recorded pre_patch sha256 values"
            ),
        },
    }


def _write_previous_run(
    runs_root: Path,
    *,
    fixture: str = "loop_demo",
    patch_evidence: dict[str, object] | None = None,
) -> Path:
    run_dir = runs_root / f"20260520-000000-{fixture}"
    run_dir.mkdir(parents=True)
    iteration_path = run_dir / "iteration_001.json"
    write_json(
        run_dir / "run_manifest.json",
        {
            "schema": "figure-agent.fig-loop-run.v1",
            "fixture": fixture,
        },
    )
    write_json(
        iteration_path,
        {
            "patch_evidence": patch_evidence
            or {
                "phase": "pre_patch",
                "target_type": "finding",
                "target_id": "C001",
                "pre_patch": {"allowed_edit_scope": []},
            }
        },
    )
    return iteration_path


def test_latest_patch_evidence_baseline_filters_invalid_runs(tmp_path: Path) -> None:
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    valid_path = _write_previous_run(runs_root)
    invalid_dir = runs_root / "20260520-000001-loop_demo"
    invalid_dir.mkdir()
    write_json(invalid_dir / "run_manifest.json", {"schema": "other", "fixture": "loop_demo"})
    write_json(invalid_dir / "iteration_001.json", {"patch_evidence": {"phase": "pre_patch"}})

    assert latest_patch_evidence_baseline(runs_root, "loop_demo") == (
        valid_path,
        {
            "phase": "pre_patch",
            "target_type": "finding",
            "target_id": "C001",
            "pre_patch": {"allowed_edit_scope": []},
        },
    )


def test_post_patch_evidence_verdict_resolved_when_target_resolved_and_file_changed(
    tmp_path: Path,
) -> None:
    tex = tmp_path / "examples" / "loop_demo" / "loop_demo.tex"
    tex.parent.mkdir(parents=True)
    tex.write_text("before", encoding="utf-8")
    before = path_evidence(tmp_path, "examples/loop_demo/loop_demo.tex")
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    baseline_path = _write_previous_run(
        runs_root,
        patch_evidence={
            "phase": "pre_patch",
            "target_type": "finding",
            "target_id": "C001",
            "pre_patch": {"allowed_edit_scope": [before]},
        },
    )
    tex.write_text("after", encoding="utf-8")

    assert post_patch_evidence_verdict(
        tmp_path,
        runs_root,
        "loop_demo",
        {"state": "fresh", "decisions": [{"finding_id": "C001", "decision": "resolved"}]},
        {"render_state": "FRESH"},
    ) == {
        "schema": POST_PATCH_EVIDENCE_SCHEMA,
        "baseline_path": str(baseline_path),
        "target_type": "finding",
        "target_id": "C001",
        "verdict": "resolved",
        "allowed_edit_scope_changed": True,
        "changed_allowed_paths": ["examples/loop_demo/loop_demo.tex"],
        "current_decision": "resolved",
        "may_edit": False,
    }


def test_post_patch_evidence_verdict_regressed_when_render_not_fresh_or_missing(
    tmp_path: Path,
) -> None:
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    _write_previous_run(runs_root)

    verdict = post_patch_evidence_verdict(
        tmp_path,
        runs_root,
        "loop_demo",
        {"state": "fresh", "decisions": []},
        {"render_state": "STALE"},
    )

    assert verdict is not None
    assert verdict["verdict"] == "regressed"
    assert verdict["may_edit"] is False
