from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_review_packet  # noqa: E402


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text("source\n", encoding="utf-8")
    (sandbox / f"{name}.tex").write_text("candidate\n", encoding="utf-8")
    (sandbox / "source").mkdir()
    (sandbox / "source" / "candidate.tex").write_text("candidate\n", encoding="utf-8")
    (sandbox / "crops").mkdir()
    (sandbox / "crops" / "original_panel_C.png").write_bytes(b"before")
    (sandbox / "crops" / "candidate_panel_C.png").write_bytes(b"after")
    (sandbox / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.candidate-manifest.v1",
                "candidate_id": "CAND001",
                "candidate_hash": "sha256:" + "3" * 64,
                "fixture": name,
                "panel": "C",
                "selectors": [{"kind": "tex_selector.v1", "line_start": 10, "line_end": 11}],
                "base": {
                    "source_commit": "abc123",
                    "tex_hash": "sha256:" + "1" * 64,
                    "status_hash": "sha256:" + "2" * 64,
                    "render_hash": "sha256:" + "0" * 64,
                },
                "operations": [
                    {
                        "kind": "replace_text",
                        "path": f"examples/{name}/{name}.tex",
                        "original": "source",
                        "replacement": "candidate",
                    }
                ],
                "artifacts": [{"kind": "candidate_source", "path": f"{name}.tex"}],
                "candidate_set_path": "build/candidates/panel_C_candidate_set.json",
                "stages": {
                    "prepare": "passed",
                    "compile": "not_run",
                    "export": "not_run",
                    "crop": "not_run",
                },
                "visual_review": {"status": "missing_render"},
                "verification": {
                    "commands": ["fig-agent status candidate_demo --json"],
                    "hard_gate_state": "human_required",
                },
                "apply_authority": "apply_eligible",
                "effective_apply_authority": "review_only",
                "risk": "low",
                "rollback": {"strategy": "reverse_operations"},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (sandbox / "render_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.candidate-render-manifest.v1",
                "schema_version": 1,
                "figure_name": name,
                "candidate_id": "CAND001",
                "candidate_hash": "sha256:" + "3" * 64,
                "candidate_set_path": "build/candidates/panel_C_candidate_set.json",
                "sandbox_path": "build/candidates/CAND001",
                "panel": "C",
                "stages": {
                    "prepare": {"status": "success"},
                    "compile": {"status": "success"},
                    "export": {"status": "success"},
                    "crop": {"status": "success"},
                    "evaluate": {"status": "rendered_needs_human_review"},
                },
                "artifacts": {
                    "source_copy": "build/candidates/CAND001/source/candidate.tex",
                    "pdf": None,
                    "png": None,
                    "before_crop": "build/candidates/CAND001/crops/original_panel_C.png",
                    "after_crop": "build/candidates/CAND001/crops/candidate_panel_C.png",
                },
                "visual_deltas": {
                    "pixel_diff_mean": 0.12,
                    "pixel_diff_max": 10,
                    "changed_bbox": [1, 2, 3, 4],
                },
                "diagnostics": [],
                "human_review_required": True,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return fixture


def _tree(workspace: Path) -> list[str]:
    return sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))


def test_review_packet_reads_manifest_and_artifact_descriptors(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    before = _tree(workspace)

    packet = candidate_review_packet.build_review_packet(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
    )

    assert packet["schema"] == "figure-agent.candidate-review-packet.v1"
    assert packet["fixture"] == "candidate_demo"
    assert packet["candidate_id"] == "CAND001"
    assert packet["candidate_hash"] == "sha256:" + "3" * 64
    assert packet["panel"] == "C"
    assert packet["selectors"] == [{"kind": "tex_selector.v1", "line_start": 10, "line_end": 11}]
    assert packet["visual_review"] == {"status": "missing_render"}
    assert packet["manifest_summary"] == {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_hash": "sha256:" + "3" * 64,
        "panel": "C",
        "apply_authority": "apply_eligible",
        "effective_apply_authority": "review_only",
        "hard_gate_state": "human_required",
        "operation_count": 1,
        "artifact_count": 1,
        "source_commit": "abc123",
        "risk": "low",
        "stages": {
            "prepare": "passed",
            "compile": "not_run",
            "export": "not_run",
            "crop": "not_run",
        },
        "visual_review": {"status": "missing_render"},
        "rollback_strategy": "reverse_operations",
    }
    assert packet["artifacts"] == [
        {
            "kind": "candidate_source",
            "path": "candidate_demo.tex",
            "exists": True,
            "size_bytes": len(b"candidate\n"),
        }
    ]
    assert packet["render_status"] == "rendered_needs_human_review"
    assert packet["render_manifest_path"] == "build/candidates/CAND001/render_manifest.json"
    assert packet["before_artifacts"] == [
        {
            "kind": "before_crop",
            "path": "build/candidates/CAND001/crops/original_panel_C.png",
            "exists": True,
            "size_bytes": len(b"before"),
        }
    ]
    assert packet["after_artifacts"] == [
        {
            "kind": "after_crop",
            "path": "build/candidates/CAND001/crops/candidate_panel_C.png",
            "exists": True,
            "size_bytes": len(b"after"),
        }
    ]
    assert packet["visual_deltas"] == {
        "pixel_diff_mean": 0.12,
        "pixel_diff_max": 10,
        "changed_bbox": [1, 2, 3, 4],
    }
    assert packet["hard_gates"]["render"] == "rendered_needs_human_review"
    assert packet["apply_readiness"]["status"] in {
        "blocked",
        "ready_for_local_acceptance",
        "accepted_ready_to_apply",
        "applied",
    }
    assert packet["human_review_required"] is True
    assert packet["human_decision_required"] is True
    assert packet["source_changes"][0]["kind"] == "replace_text"
    assert packet["score_report"]["status"] == "not_available"
    assert packet["score_report"]["recommended_command"] == (
        "fig-agent rank-candidates candidate_demo "
        "--candidate-set build/candidates/panel_C_candidate_set.json --json"
    )
    assert packet["semantic_invariant_report"]["required_before_apply"] is True
    assert packet["rollback"]["status"] == "manual_reverse_operations"
    assert packet["recommended_next_action"] == "human_review_required"
    assert packet["human_decision_fields"] == [
        "decision",
        "reviewer",
        "reviewed_at",
        "rationale",
    ]
    assert _tree(workspace) == before


def test_review_packet_validates_fixture_name(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    with pytest.raises(ValueError, match="fixture name"):
        candidate_review_packet.build_review_packet(
            "../candidate_demo",
            "CAND001",
            workspace_root=workspace,
        )


def test_review_packet_rejects_artifact_path_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    manifest = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["artifacts"] = [{"kind": "candidate_source", "path": "../escape.tex"}]
    manifest.write_text(json.dumps(data) + "\n", encoding="utf-8")

    with pytest.raises(
        candidate_review_packet.CandidateReviewPacketError,
        match="path_escape",
    ):
        candidate_review_packet.build_review_packet(
            "candidate_demo",
            "CAND001",
            workspace_root=workspace,
        )


def test_review_packet_rejects_sandbox_root_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    exports = fixture / "exports"
    exports.mkdir()
    candidates = fixture / "build" / "candidates"
    for path in sorted(candidates.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    candidates.rmdir()
    candidates.symlink_to(exports)

    with pytest.raises(
        candidate_review_packet.CandidateReviewPacketError,
        match="sandbox_symlink_forbidden",
    ):
        candidate_review_packet.build_review_packet(
            "candidate_demo",
            "CAND001",
            workspace_root=workspace,
        )


def test_review_packet_rejects_manifest_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    manifest = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    outside = fixture / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    manifest.unlink()
    manifest.symlink_to(outside)

    with pytest.raises(
        candidate_review_packet.CandidateReviewPacketError,
        match="sandbox_symlink_forbidden",
    ):
        candidate_review_packet.build_review_packet(
            "candidate_demo",
            "CAND001",
            workspace_root=workspace,
        )


def test_review_packet_rejects_artifact_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    outside = fixture / "outside.tex"
    outside.write_text("outside\n", encoding="utf-8")
    artifact = sandbox / "candidate_demo.tex"
    artifact.unlink()
    artifact.symlink_to(outside)

    with pytest.raises(
        candidate_review_packet.CandidateReviewPacketError,
        match="sandbox_symlink_forbidden",
    ):
        candidate_review_packet.build_review_packet(
            "candidate_demo",
            "CAND001",
            workspace_root=workspace,
        )
