from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_acceptance  # noqa: E402


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text("source\n", encoding="utf-8")
    candidate_hash = "sha256:" + "1" * 64
    operation_path = f"examples/{name}/{name}.tex"
    candidate_manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "fixture": name,
        "candidate_id": "CAND001",
        "candidate_hash": candidate_hash,
        "candidate_set_path": "build/candidates/candidate_set.json",
        "effective_apply_authority": "review_only",
        "verification": {"hard_gate_state": "human_required"},
        "operations": [
            {
                "kind": "replace_text",
                "path": operation_path,
                "source_sha256": _sha256_text("source\n"),
                "original": "source\n",
                "replacement": "candidate\n",
            }
        ],
        "selectors": [
            {
                "kind": "tex_selector.v1",
                "path": operation_path,
                "source_hash": _sha256_text("source\n"),
            }
        ],
    }
    render_manifest = {
        "schema": "figure-agent.candidate-render-manifest.v1",
        "figure_name": name,
        "candidate_id": "CAND001",
        "candidate_hash": candidate_hash,
        "candidate_set_path": "build/candidates/candidate_set.json",
        "stages": {
            "compile": {"status": "success"},
            "export": {"status": "success"},
            "crop": {"status": "success"},
            "evaluate": {"status": "rendered_needs_human_review"},
        },
    }
    candidate_set = {
        "schema": "figure-agent.candidate-set.v1",
        "candidates": [{"id": "CAND001", "candidate_hash": candidate_hash}],
    }
    (fixture / "build" / "candidates" / "candidate_set.json").write_text(
        json.dumps(candidate_set, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sandbox / "candidate_manifest.json").write_text(
        json.dumps(candidate_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sandbox / "render_manifest.json").write_text(
        json.dumps(render_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return fixture


def test_build_apply_readiness_reports_ready_for_local_acceptance(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    readiness = candidate_acceptance.build_apply_readiness(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    assert readiness["schema"] == "figure-agent.candidate-apply-readiness.v1"
    assert readiness["status"] == "ready_for_local_acceptance"
    assert readiness["blocking_reasons"] == []
    assert readiness["required_commands"][0].startswith("fig-agent accept-candidate")


def test_write_acceptance_artifact_records_manifest_hashes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)

    payload = candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )

    path = fixture / "build" / "candidates" / "CAND001" / "acceptance.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert payload["path"] == "build/candidates/CAND001/acceptance.json"
    assert data["schema"] == "figure-agent.candidate-acceptance.v1"
    assert data["decision"] == "accept"
    assert data["reviewer"] == "local-user"
    assert data["candidate_manifest_sha256"].startswith("sha256:")
    assert data["render_manifest_sha256"].startswith("sha256:")


def test_acceptance_rejects_sandbox_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    acceptance = fixture / "build" / "candidates" / "CAND001" / "acceptance.json"
    acceptance.symlink_to(outside)

    with pytest.raises(candidate_acceptance.CandidateAcceptanceError, match="sandbox_symlink"):
        candidate_acceptance.write_acceptance(
            "candidate_demo",
            "CAND001",
            candidate_set_path=Path("build/candidates/candidate_set.json"),
            decision="accept",
            reviewer="local-user",
            rationale="Rendered evidence reviewed.",
            workspace_root=workspace,
        )


def test_readiness_blocks_missing_source_drift_hash(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    manifest_path = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["operations"][0].pop("source_sha256")
    manifest["selectors"] = []
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")

    readiness = candidate_acceptance.build_apply_readiness(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    assert readiness["status"] == "blocked"
    assert "source_drift_hash_missing:candidate_demo.tex" in readiness["blocking_reasons"]
