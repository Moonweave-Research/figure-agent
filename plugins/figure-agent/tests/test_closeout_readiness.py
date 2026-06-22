from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import closeout_readiness  # noqa: E402
from test_evidence_index import _fixture  # noqa: E402


def _passing_closeout(_name, repo_root, runs_root=None):
    return {
        "schema": "figure-agent.closeout.v1",
        "fixture": "candidate_demo",
        "closeout_complete": True,
        "next_action": "closeout complete",
        "blocking_step_ids": [],
        "status": {
            "render_state": "FRESH",
            "critique_state": "FRESH",
            "export_state": "FRESH",
            "workflow_ready": True,
            "release_ready": True,
            "final_ready": True,
            "final_artifact_state": "NONE",
            "final_artifact_kind": "generated_export",
            "final_artifact_path": "exports/candidate_demo.svg",
            "publication_gate_state": "NOT_APPLICABLE",
            "publication_gate_failures": [],
        },
        "steps": [],
    }


def test_closeout_ready_preserves_existing_closeout_blockers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    def fake_closeout(_name, repo_root, runs_root=None):
        return {
            "schema": "figure-agent.closeout.v1",
            "fixture": "candidate_demo",
            "closeout_complete": False,
            "next_action": "fig-agent text-boundary candidate_demo --write",
            "blocking_step_ids": ["text_boundary_checks", "loop_rerun"],
            "status": {
                "render_state": "FRESH",
                "critique_state": "FRESH",
                "export_state": "FRESH",
                "workflow_ready": True,
                "release_ready": False,
                "final_ready": False,
                "final_artifact_state": "NONE",
                "final_artifact_kind": "generated_export",
                "final_artifact_path": "exports/candidate_demo.svg",
                "publication_gate_state": "NOT_APPLICABLE",
                "publication_gate_failures": [],
            },
            "steps": [
                {
                    "id": "text_boundary_checks",
                    "state": "needs_action",
                    "reason": "text boundary checks are missing",
                    "command": "fig-agent text-boundary candidate_demo --write",
                    "evidence_path": "spec.yaml",
                    "evidence": {},
                },
                {
                    "id": "loop_rerun",
                    "state": "blocked",
                    "reason": "closeout prerequisites are incomplete: text_boundary_checks",
                    "command": None,
                    "evidence_path": None,
                    "evidence": {},
                },
            ],
        }

    monkeypatch.setattr(closeout_readiness, "_compute_closeout", fake_closeout)

    readiness = closeout_readiness.build_closeout_readiness(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert readiness["schema"] == "figure-agent.closeout-readiness.v1"
    assert readiness["status"] == "blocked"
    assert [check["id"] for check in readiness["checks"]] == [
        "candidate_apply",
        "text_boundary_checks",
        "golden_acceptance",
        "accepted_state",
        "final_artifact",
        "release",
        "loop_rerun",
    ]
    assert readiness["next_action"] == "fig-agent text-boundary candidate_demo --write"


def test_closeout_ready_blocks_failed_candidate_apply(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    monkeypatch.setattr(closeout_readiness, "_compute_closeout", _passing_closeout)
    apply_path = fixture / "build" / "candidates" / "CAND001" / "apply_result.json"
    apply_result = json.loads(apply_path.read_text(encoding="utf-8"))
    apply_result["status"] = "applied_with_failed_verification"
    apply_path.write_text(json.dumps(apply_result, sort_keys=True) + "\n", encoding="utf-8")

    readiness = closeout_readiness.build_closeout_readiness(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    candidate_check = readiness["checks"][0]
    assert candidate_check["id"] == "candidate_apply"
    assert candidate_check["state"] == "blocked"
    assert candidate_check["reason"] == "candidate apply status is applied_with_failed_verification"


def test_closeout_ready_blocks_unverified_candidate_apply(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    monkeypatch.setattr(closeout_readiness, "_compute_closeout", _passing_closeout)
    apply_path = fixture / "build" / "candidates" / "CAND001" / "apply_result.json"
    apply_result = json.loads(apply_path.read_text(encoding="utf-8"))
    apply_result["status"] = "applied_unverified"
    apply_result["post_apply"] = {}
    apply_result["required_commands"] = [
        "/fig_compile candidate_demo",
        "/fig_export candidate_demo --skip-critique",
        "/fig_status candidate_demo --json",
    ]
    apply_path.write_text(json.dumps(apply_result, sort_keys=True) + "\n", encoding="utf-8")

    readiness = closeout_readiness.build_closeout_readiness(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    candidate_check = readiness["checks"][0]
    assert readiness["status"] == "blocked"
    assert candidate_check["id"] == "candidate_apply"
    assert candidate_check["state"] == "blocked"
    assert candidate_check["reason"] == "candidate apply verification has not run"
    assert candidate_check["evidence"]["required_commands"] == [
        "/fig_compile candidate_demo",
        "/fig_export candidate_demo --skip-critique",
        "/fig_status candidate_demo --json",
    ]


def test_closeout_ready_blocks_malformed_applied_candidate_result(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    monkeypatch.setattr(closeout_readiness, "_compute_closeout", _passing_closeout)
    apply_path = fixture / "build" / "candidates" / "CAND001" / "apply_result.json"
    apply_result = json.loads(apply_path.read_text(encoding="utf-8"))
    apply_result.pop("post_apply")
    apply_path.write_text(json.dumps(apply_result, sort_keys=True) + "\n", encoding="utf-8")

    readiness = closeout_readiness.build_closeout_readiness(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    candidate_check = readiness["checks"][0]
    assert candidate_check["state"] == "blocked"
    assert (
        candidate_check["reason"]
        == "candidate post-apply checks missing: compile, export, status"
    )


def test_closeout_ready_blocks_stale_candidate_apply(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    monkeypatch.setattr(closeout_readiness, "_compute_closeout", _passing_closeout)
    (fixture / "candidate_demo.tex").write_text("changed\n", encoding="utf-8")

    readiness = closeout_readiness.build_closeout_readiness(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    candidate_check = readiness["checks"][0]
    assert candidate_check["id"] == "candidate_apply"
    assert candidate_check["state"] == "blocked"
    assert candidate_check["reason"] == "candidate apply result is stale against current source"


def test_closeout_ready_blocks_final_artifact_failure(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    def fake_closeout(_name, repo_root, runs_root=None):
        payload = _passing_closeout(_name, repo_root, runs_root)
        payload["status"] = {
            **payload["status"],
            "release_ready": False,
            "final_ready": False,
            "final_artifact_state": "STALE",
            "final_artifact_kind": "polished_svg",
            "final_artifact_path": "polish/candidate_demo.polished.svg",
            "publication_gate_state": "NOT_APPLICABLE",
            "publication_gate_failures": [],
        }
        return payload

    monkeypatch.setattr(closeout_readiness, "_compute_closeout", fake_closeout)

    readiness = closeout_readiness.build_closeout_readiness(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    checks = {check["id"]: check for check in readiness["checks"]}
    assert readiness["status"] == "blocked"
    assert checks["final_artifact"]["state"] == "blocked"
    assert checks["final_artifact"]["reason"] == "final_artifact_state is STALE"


def test_closeout_ready_blocks_publication_gate_failures(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    def fake_closeout(_name, repo_root, runs_root=None):
        payload = _passing_closeout(_name, repo_root, runs_root)
        payload["status"] = {
            **payload["status"],
            "release_ready": False,
            "final_ready": False,
            "final_artifact_state": "FRESH",
            "final_artifact_kind": "polished_svg",
            "final_artifact_path": "polish/candidate_demo.polished.svg",
            "publication_gate_state": "PROVENANCE_REQUIRED",
            "publication_gate_failures": [{"code": "missing_submission_safe_true"}],
        }
        return payload

    monkeypatch.setattr(closeout_readiness, "_compute_closeout", fake_closeout)

    readiness = closeout_readiness.build_closeout_readiness(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    checks = {check["id"]: check for check in readiness["checks"]}
    assert readiness["status"] == "blocked"
    assert checks["release"]["state"] == "blocked"
    assert checks["release"]["reason"] == "publication gate reports 1 failure(s)"


def test_closeout_ready_blocks_accepted_but_stale_even_when_publication_gate_passes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    def fake_closeout(_name, repo_root, runs_root=None):
        payload = _passing_closeout(_name, repo_root, runs_root)
        payload["status"] = {
            **payload["status"],
            "acceptance_state": "ACCEPTED",
            "acceptance_freshness_state": "accepted_but_stale",
            "workflow_ready": False,
            "release_ready": False,
            "final_ready": False,
            "publication_gate_state": "PASS",
            "publication_gate_failures": [],
        }
        return payload

    monkeypatch.setattr(closeout_readiness, "_compute_closeout", fake_closeout)

    readiness = closeout_readiness.build_closeout_readiness(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    checks = {check["id"]: check for check in readiness["checks"]}
    assert readiness["status"] == "blocked"
    assert checks["accepted_state"]["state"] == "blocked"
    assert checks["accepted_state"]["reason"] == (
        "accepted_but_stale: fixture has an accepted historical state, but current "
        "source, render, critique, or export evidence is stale. Re-run "
        "compile/critique/export and refresh acceptance before closeout."
    )
    assert readiness["next_action"] != "closeout ready"


def test_closeout_ready_reports_release_ready_false_without_blocking_tracked_golden_closeout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    def fake_closeout(_name, repo_root, runs_root=None):
        payload = _passing_closeout(_name, repo_root, runs_root)
        payload["status"] = {
            **payload["status"],
            "release_ready": False,
            "final_ready": False,
            "final_artifact_state": "NONE",
            "final_artifact_kind": "generated_export",
            "final_artifact_path": "exports/candidate_demo.svg",
            "publication_gate_state": "HUMAN_ACCEPTANCE_REQUIRED",
            "publication_gate_failures": [],
        }
        return payload

    monkeypatch.setattr(closeout_readiness, "_compute_closeout", fake_closeout)

    readiness = closeout_readiness.build_closeout_readiness(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    checks = {check["id"]: check for check in readiness["checks"]}
    assert readiness["status"] == "ready"
    assert checks["release"]["state"] == "passed"
    assert checks["release"]["reason"] == "publication gate has no reported failures"
    assert checks["release"]["evidence"]["release_ready"] is False
