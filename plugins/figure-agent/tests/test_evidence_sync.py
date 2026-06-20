from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import evidence_sync  # noqa: E402
from test_evidence_index import _fixture  # noqa: E402


def _tree(workspace: Path) -> dict[str, str]:
    return {
        path.relative_to(workspace).as_posix(): path.read_text(encoding="utf-8")
        for path in workspace.rglob("*")
        if path.is_file()
    }


def test_evidence_sync_preview_is_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    before = _tree(workspace)

    result = evidence_sync.sync_evidence(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
        write=False,
    )

    assert result["schema"] == "figure-agent.evidence-sync.v1"
    assert result["mode"] == "preview"
    assert result["writes"] == []
    assert _tree(workspace) == before


def test_evidence_sync_write_only_writes_evidence_index(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    manifest_path = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    manifest_before = manifest_path.read_text(encoding="utf-8")

    result = evidence_sync.sync_evidence(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
        write=True,
    )

    assert result["mode"] == "write"
    assert result["writes"] == ["build/evidence/evidence_index.json"]
    assert manifest_path.read_text(encoding="utf-8") == manifest_before
    index = json.loads((fixture / "build" / "evidence" / "evidence_index.json").read_text())
    assert index["candidate"]["render_status"] == "rendered_needs_human_review"


def test_evidence_sync_write_refuses_hash_mismatch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    render_path = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    render = json.loads(render_path.read_text(encoding="utf-8"))
    render["candidate_hash"] = "sha256:" + "9" * 64
    render_path.write_text(json.dumps(render, sort_keys=True) + "\n", encoding="utf-8")

    result = evidence_sync.sync_evidence(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
        write=True,
    )

    assert result["mode"] == "write"
    assert result["blocking_reasons"] == ["hash_mismatch"]
    assert result["writes"] == []
    assert not (fixture / "build" / "evidence" / "evidence_index.json").exists()


def test_evidence_sync_write_refuses_candidate_id_mismatch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    render_path = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    render = json.loads(render_path.read_text(encoding="utf-8"))
    render["candidate_id"] = "CAND999"
    render_path.write_text(json.dumps(render, sort_keys=True) + "\n", encoding="utf-8")

    result = evidence_sync.sync_evidence(
        "candidate_demo",
        candidate_id="CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
        write=True,
    )

    assert result["blocking_reasons"] == ["candidate_id_mismatch"]
    assert result["writes"] == []
    assert not (fixture / "build" / "evidence" / "evidence_index.json").exists()


def test_evidence_sync_write_refuses_evidence_dir_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    outside = tmp_path / "outside"
    outside.mkdir()
    evidence_dir = fixture / "build" / "evidence"
    evidence_dir.symlink_to(outside)

    with pytest.raises(evidence_sync.EvidenceSyncError, match="sandbox_symlink"):
        evidence_sync.sync_evidence(
            "candidate_demo",
            candidate_id="CAND001",
            candidate_set_path=Path("build/candidates/candidate_set.json"),
            workspace_root=workspace,
            write=True,
        )


def test_evidence_sync_write_refuses_build_dir_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    build_dir = fixture / "build"
    outside = tmp_path / "outside-build"
    outside.mkdir()
    for path in sorted(build_dir.rglob("*"), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink()
        else:
            path.rmdir()
    build_dir.rmdir()
    build_dir.symlink_to(outside)

    with pytest.raises(evidence_sync.EvidenceSyncError, match="sandbox_symlink"):
        evidence_sync.sync_evidence(
            "candidate_demo",
            workspace_root=workspace,
            write=True,
        )


def test_evidence_sync_write_refuses_evidence_index_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    evidence_dir = fixture / "build" / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "evidence_index.json").symlink_to(outside)

    with pytest.raises(evidence_sync.EvidenceSyncError, match="sandbox_symlink"):
        evidence_sync.sync_evidence(
            "candidate_demo",
            candidate_id="CAND001",
            candidate_set_path=Path("build/candidates/candidate_set.json"),
            workspace_root=workspace,
            write=True,
        )


def test_evidence_sync_refuses_candidate_set_path_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    with pytest.raises(ValueError, match="path_escape"):
        evidence_sync.sync_evidence(
            "candidate_demo",
            candidate_id="CAND001",
            candidate_set_path=Path("../candidate_set.json"),
            workspace_root=workspace,
            write=True,
        )


def test_evidence_sync_refuses_candidate_set_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set = fixture / "build" / "candidates" / "candidate_set.json"
    candidate_set.unlink()
    outside = tmp_path / "candidate_set.json"
    outside.write_text("{}", encoding="utf-8")
    candidate_set.symlink_to(outside)

    with pytest.raises(evidence_sync.evidence_index.EvidenceIndexError, match="sandbox_symlink"):
        evidence_sync.sync_evidence(
            "candidate_demo",
            candidate_id="CAND001",
            candidate_set_path=Path("build/candidates/candidate_set.json"),
            workspace_root=workspace,
            write=True,
        )
