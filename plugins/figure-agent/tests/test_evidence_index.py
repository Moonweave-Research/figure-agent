from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import evidence_index  # noqa: E402


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _fixture(workspace: Path, *, with_apply: bool = True) -> Path:
    fixture = workspace / "examples" / "candidate_demo"
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    (fixture / "candidate_demo.tex").write_text("candidate\n", encoding="utf-8")
    candidate_hash = "sha256:" + "1" * 64
    candidate_set = {
        "schema": "figure-agent.candidate-set.v1",
        "candidates": [
            {
                "id": "CAND001",
                "candidate_hash": candidate_hash,
                "visual_review": {"status": "missing_render"},
            }
        ],
    }
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "fixture": "candidate_demo",
        "candidate_id": "CAND001",
        "candidate_hash": candidate_hash,
        "candidate_set_path": "build/candidates/candidate_set.json",
        "visual_review": {"status": "missing_render"},
    }
    render_manifest = {
        "schema": "figure-agent.candidate-render-manifest.v1",
        "figure_name": "candidate_demo",
        "candidate_id": "CAND001",
        "candidate_hash": candidate_hash,
        "candidate_set_path": "build/candidates/candidate_set.json",
        "stages": {
            "prepare": {"status": "success"},
            "compile": {"status": "success"},
            "export": {"status": "success"},
            "crop": {"status": "success"},
            "evaluate": {"status": "rendered_needs_human_review"},
        },
        "visual_deltas": {"pixel_diff_mean": 0.1},
        "diagnostics": [],
    }
    (fixture / "build" / "candidates" / "candidate_set.json").write_text(
        json.dumps(candidate_set, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sandbox / "candidate_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sandbox / "render_manifest.json").write_text(
        json.dumps(render_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if with_apply:
        source_hash = _sha256_file(fixture / "candidate_demo.tex")
        apply_result = {
            "schema": "figure-agent.candidate-apply-result.v1",
            "figure_name": "candidate_demo",
            "candidate_id": "CAND001",
            "status": "applied",
            "changed_files": [
                {
                    "path": "candidate_demo.tex",
                    "before_sha256": "sha256:" + "0" * 64,
                    "after_sha256": source_hash,
                }
            ],
            "rollback_patch": "build/candidates/CAND001/rollback.patch",
            "post_apply": {
                "compile": {"status": "success"},
                "export": {"status": "success"},
                "status": {"status": "success"},
            },
            "diagnostics": [],
        }
        (sandbox / "apply_result.json").write_text(
            json.dumps(apply_result, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return fixture


def test_evidence_index_prefers_render_manifest_over_stale_visual_review(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    index = evidence_index.build_evidence_index(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    assert index["schema"] == "figure-agent.evidence-index.v1"
    assert index["candidate"]["render_status"] == "rendered_needs_human_review"
    assert index["candidate"]["manifest_visual_review"]["status"] == "missing_render"
    assert index["candidate"]["apply_status"] == "applied"
    assert index["candidate"]["post_apply"] == {
        "compile": "success",
        "export": "success",
        "status": "success",
    }
    assert index["diagnostics"] == []


def test_evidence_index_reports_candidate_apply_source_drift(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text("changed\n", encoding="utf-8")

    index = evidence_index.build_evidence_index(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    assert index["candidate"]["apply_status"] == "stale"
    assert "candidate_apply_stale:candidate_demo.tex" in index["diagnostics"]


def test_evidence_index_surfaces_unverified_apply_required_commands(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
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

    index = evidence_index.build_evidence_index(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    assert index["candidate"]["apply_status"] == "applied_unverified"
    assert index["candidate"]["post_apply"] == {}
    assert index["candidate"]["required_commands"] == [
        "/fig_compile candidate_demo",
        "/fig_export candidate_demo --skip-critique",
        "/fig_status candidate_demo --json",
    ]


def test_evidence_index_auto_detects_latest_applied_candidate(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    index = evidence_index.build_evidence_index("candidate_demo", workspace_root=workspace)

    assert index["candidate"]["candidate_id"] == "CAND001"
    assert index["candidate"]["apply_status"] == "applied"


def test_evidence_index_marks_malformed_changed_files_stale(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    apply_path = fixture / "build" / "candidates" / "CAND001" / "apply_result.json"
    apply_result = json.loads(apply_path.read_text(encoding="utf-8"))
    apply_result["changed_files"] = [{"path": "candidate_demo.tex"}]
    apply_path.write_text(json.dumps(apply_result, sort_keys=True) + "\n", encoding="utf-8")

    index = evidence_index.build_evidence_index(
        "candidate_demo",
        candidate_id="CAND001",
        workspace_root=workspace,
    )

    assert index["candidate"]["apply_status"] == "stale"
    assert "candidate_apply_changed_files_invalid" in index["diagnostics"]


def test_evidence_index_reports_render_manifest_candidate_id_mismatch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    render_path = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    render_manifest = json.loads(render_path.read_text(encoding="utf-8"))
    render_manifest["candidate_id"] = "CAND999"
    render_path.write_text(
        json.dumps(render_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    index = evidence_index.build_evidence_index(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    assert "candidate_id_mismatch" in index["diagnostics"]


def test_evidence_index_without_candidate_is_valid(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "plain_demo"
    fixture.mkdir(parents=True)
    (fixture / "plain_demo.tex").write_text("source\n", encoding="utf-8")

    index = evidence_index.build_evidence_index("plain_demo", workspace_root=workspace)

    assert index["candidate"] is None
    assert index["source"]["tex_path"] == "plain_demo.tex"


def test_evidence_index_rejects_sandbox_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    for path in sorted(sandbox.rglob("*"), reverse=True):
        path.unlink()
    sandbox.rmdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    sandbox.symlink_to(outside)

    with pytest.raises(evidence_index.EvidenceIndexError, match="sandbox_symlink"):
        evidence_index.build_evidence_index(
            "candidate_demo",
            candidate_id="CAND001",
            workspace_root=workspace,
        )
