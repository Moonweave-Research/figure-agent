from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_review_packet  # noqa: E402


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


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
                "expected_delta": ["increase panel boundary clearance"],
                "semantic_risks": ["panel spacing must preserve panel semantics"],
                "boundedness": {
                    "changes": "increase panel boundary clearance",
                    "does_not_change": [
                        "accepted state",
                        "tracked golden exports",
                        "SVG artifacts",
                    ],
                    "requires_human_review": True,
                    "not_svg_polish": True,
                },
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


def _write_acceptance(fixture: Path, name: str = "candidate_demo") -> None:
    sandbox = fixture / "build" / "candidates" / "CAND001"
    manifest_path = sandbox / "candidate_manifest.json"
    render_manifest_path = sandbox / "render_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload = {
        "schema": "figure-agent.candidate-acceptance.v1",
        "figure_name": name,
        "candidate_id": "CAND001",
        "candidate_hash": manifest["candidate_hash"],
        "candidate_set_path": "build/candidates/panel_C_candidate_set.json",
        "candidate_manifest_path": "build/candidates/CAND001/candidate_manifest.json",
        "candidate_manifest_sha256": _sha256_file(manifest_path),
        "render_manifest_path": "build/candidates/CAND001/render_manifest.json",
        "render_manifest_sha256": _sha256_file(render_manifest_path),
        "decision": "accept",
        "reviewer": "local-user",
        "reviewed_at": "2026-06-08T00:00:00Z",
        "rationale": "reviewed",
        "human_review_required": True,
    }
    (sandbox / "acceptance.json").write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_semantic_review(
    fixture: Path,
    *,
    name: str = "candidate_demo",
    artifact_hash: str | None = None,
    verdict: str = "pass",
    human_required: bool = False,
) -> None:
    sandbox = fixture / "build" / "candidates" / "CAND001"
    manifest_path = sandbox / "candidate_manifest.json"
    render_manifest_path = sandbox / "render_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload = {
        "schema": "figure-agent.semantic-candidate-review.v1",
        "fixture": name,
        "candidate_id": "CAND001",
        "candidate_hash": manifest["candidate_hash"],
        "reviewed_artifacts": [
            {
                "path": render_manifest_path.relative_to(fixture).as_posix(),
                "sha256": artifact_hash or _sha256_file(render_manifest_path),
            }
        ],
        "semantic_invariants": [],
        "findings": [],
        "conflicts": [],
        "verdict": verdict,
        "human_required": human_required,
        "reviewed_at": "2026-06-22T00:00:00Z",
        "reviewer": "host",
    }
    (sandbox / "semantic_review.json").write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _update_manifest(fixture: Path, updates: dict, name: str = "candidate_demo") -> None:
    manifest_path = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(updates)
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")


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
    assert packet["visual_review"] == {
        "status": "rendered_needs_human_review",
        "source": "render_manifest",
    }
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
            "compile": "success",
            "export": "success",
            "crop": "success",
            "evaluate": "rendered_needs_human_review",
        },
        "visual_review": {
            "status": "rendered_needs_human_review",
            "source": "render_manifest",
        },
        "expected_delta": ["increase panel boundary clearance"],
        "semantic_risks": ["panel spacing must preserve panel semantics"],
        "boundedness": {
            "changes": "increase panel boundary clearance",
            "does_not_change": [
                "accepted state",
                "tracked golden exports",
                "SVG artifacts",
            ],
            "requires_human_review": True,
            "not_svg_polish": True,
        },
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


def test_review_packet_includes_advisory_narrative_context(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "spec.yaml").write_text(
        """name: candidate_demo
panels:
  - id: C
    caption: Candidate panel role
""",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("## 1. Topic\nCandidate story\n", encoding="utf-8")
    (fixture / "panel_goals.md").write_text(
        "Panel C: preserve the comparison before moving labels.\n",
        encoding="utf-8",
    )
    before = _tree(workspace)

    packet = candidate_review_packet.build_review_packet(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
    )

    assert packet["narrative_review_context"]["rank_eligible"] is False
    assert packet["narrative_review_context"]["blocking_allowed"] is False
    assert packet["narrative_review_context"]["context"]["schema"] == (
        "figure-agent.narrative-context.v1"
    )
    assert packet["narrative_review_context"]["context"]["sources"]["panel_goals"].endswith(
        "panel_goals.md"
    )
    assert _tree(workspace) == before


def test_review_packet_includes_semantic_review_state(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_semantic_review(fixture)

    packet = candidate_review_packet.build_review_packet(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
    )

    assert packet["semantic_invariant_report"]["schema"] == (
        "figure-agent.semantic-review-state.v1"
    )
    assert packet["semantic_invariant_report"]["status"] == "pass"
    assert packet["semantic_invariant_report"]["verdict"] == "pass"
    assert packet["semantic_invariant_report"]["blocks_apply"] is False


def test_review_packet_summarizes_bounded_candidate_context(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    packet = candidate_review_packet.build_review_packet(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
    )

    summary = packet["manifest_summary"]
    assert summary["expected_delta"] == ["increase panel boundary clearance"]
    assert summary["semantic_risks"] == ["panel spacing must preserve panel semantics"]
    assert summary["boundedness"]["not_svg_polish"] is True
    assert "accepted state" in summary["boundedness"]["does_not_change"]


def test_review_packet_reports_optional_missing_semantic_review(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _update_manifest(
        fixture,
        {
            "edit_family": "bounded_coordinate_offset",
            "semantic_risks": [],
            "operations": [{"kind": "coordinate_offset"}],
        },
    )

    packet = candidate_review_packet.build_review_packet(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
    )

    assert packet["semantic_invariant_report"]["status"] == "missing"
    assert packet["semantic_invariant_report"]["required_before_apply"] is False
    assert packet["semantic_invariant_report"]["blocks_apply"] is False


def test_review_packet_reports_stale_required_semantic_review_as_invalid_or_stale(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _update_manifest(
        fixture,
        {
            "edit_family": "semantic_rewrite",
            "semantic_risks": ["candidate changes a locked claim"],
        },
    )
    _write_semantic_review(fixture)
    render_manifest = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    render_manifest.write_text('{"changed": true}\n', encoding="utf-8")

    packet = candidate_review_packet.build_review_packet(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
    )

    assert packet["semantic_invariant_report"]["status"] == "invalid_or_stale"
    assert packet["semantic_invariant_report"]["required_before_apply"] is True
    assert packet["semantic_invariant_report"]["blocks_apply"] is True
    assert "reviewed_artifact_stale" in packet["semantic_invariant_report"]["blocking_reasons"]


def test_review_packet_malformed_spec_fails_closed_for_semantic_state(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _update_manifest(
        fixture,
        {
            "edit_family": "bounded_coordinate_offset",
            "semantic_risks": [],
            "operations": [{"kind": "coordinate_offset"}],
        },
    )
    (fixture / "spec.yaml").write_text("panels: [\n", encoding="utf-8")

    packet = candidate_review_packet.build_review_packet(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
    )

    assert packet["semantic_invariant_report"]["status"] == "missing"
    assert packet["semantic_invariant_report"]["required_before_apply"] is True
    assert packet["semantic_invariant_report"]["blocks_apply"] is True
    assert "spec_unreadable" in packet["semantic_invariant_report"]["blocking_reasons"]


def test_review_packet_broken_spec_symlink_fails_closed_for_semantic_state(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _update_manifest(
        fixture,
        {
            "edit_family": "bounded_coordinate_offset",
            "semantic_risks": [],
            "operations": [{"kind": "coordinate_offset"}],
        },
    )
    (fixture / "spec.yaml").symlink_to(fixture / "missing-spec.yaml")

    packet = candidate_review_packet.build_review_packet(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
    )

    assert packet["semantic_invariant_report"]["status"] == "missing"
    assert packet["semantic_invariant_report"]["required_before_apply"] is True
    assert packet["semantic_invariant_report"]["blocks_apply"] is True
    assert "spec_unreadable" in packet["semantic_invariant_report"]["blocking_reasons"]


def test_review_packet_semantic_pass_does_not_override_deterministic_apply_block(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set = {
        "schema": "figure-agent.candidate-set.v1",
        "candidates": [{"id": "CAND001", "candidate_hash": "sha256:" + "3" * 64}],
    }
    candidate_set_path = fixture / "build" / "candidates" / "panel_C_candidate_set.json"
    candidate_set_path.write_text(
        json.dumps(candidate_set, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest_path = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["operations"][0]["source_sha256"] = _sha256_file(fixture / "candidate_demo.tex")
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    _write_semantic_review(fixture)
    _write_acceptance(fixture)
    (fixture / "candidate_demo.tex").write_text("changed\n", encoding="utf-8")

    packet = candidate_review_packet.build_review_packet(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
    )

    assert packet["semantic_invariant_report"]["status"] == "pass"
    assert packet["semantic_invariant_report"]["blocks_apply"] is False
    assert packet["apply_readiness"]["status"] == "blocked"
    assert "source_drift_hash_mismatch" in packet["apply_readiness"]["blocking_reasons"]


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


def test_review_packet_revalidates_stale_acceptance_before_apply_command(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set = {
        "schema": "figure-agent.candidate-set.v1",
        "candidates": [{"id": "CAND001", "candidate_hash": "sha256:" + "3" * 64}],
    }
    candidate_set_path = fixture / "build" / "candidates" / "panel_C_candidate_set.json"
    candidate_set_path.write_text(
        json.dumps(candidate_set, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest_path = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["operations"][0]["source_sha256"] = _sha256_file(fixture / "candidate_demo.tex")
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    _write_acceptance(fixture)
    (fixture / "candidate_demo.tex").write_text("changed\n", encoding="utf-8")

    packet = candidate_review_packet.build_review_packet(
        "candidate_demo",
        "CAND001",
        workspace_root=workspace,
    )

    assert packet["apply_readiness"]["status"] == "blocked"
    assert "source_drift_hash_mismatch" in packet["apply_readiness"]["blocking_reasons"]
    assert packet["apply_readiness"]["required_commands"] == []


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
