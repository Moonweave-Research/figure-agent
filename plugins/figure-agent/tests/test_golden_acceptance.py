from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import golden_acceptance  # noqa: E402
from test_evidence_index import _fixture  # noqa: E402


def _ready_payload(*, critique_state: str = "passed") -> dict:
    checks = [
        {"id": "candidate_apply", "state": "passed", "reason": "", "command": None},
        {"id": "compile", "state": "passed", "reason": "", "command": None},
        {
            "id": "critique",
            "state": critique_state,
            "reason": "critique_state is STALE" if critique_state != "passed" else "",
            "command": "/fig_critique demo" if critique_state != "passed" else None,
        },
        {
            "id": "export",
            "state": "blocked",
            "reason": "tracked golden export requires deliberate manual approval",
            "command": None,
        },
        {
            "id": "golden_acceptance",
            "state": "blocked",
            "reason": "tracked golden export requires current golden acceptance",
            "command": None,
        },
        {
            "id": "loop_rerun",
            "state": "blocked",
            "reason": "closeout prerequisites are incomplete: export",
        },
    ]
    return {
        "schema": "figure-agent.closeout-readiness.v1",
        "figure_name": "candidate_demo",
        "status": "blocked",
        "checks": checks,
        "next_action": "tracked golden export requires deliberate manual approval",
        "evidence_index": {
            "source": {"tex_sha256": "sha256:" + "1" * 64},
            "candidate": {
                "apply_result_path": "build/candidates/CAND001/apply_result.json",
            },
            "status": {"export_state": "TRACKED_GOLDEN"},
        },
    }


def test_closeout_accept_writes_golden_acceptance_for_tracked_golden(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "critique.md").write_text("critique\n", encoding="utf-8")
    (fixture / "exports").mkdir()
    (fixture / "exports" / "candidate_demo.pdf").write_bytes(b"pdf")
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    result = golden_acceptance.write_golden_acceptance(
        "candidate_demo",
        decision="accept",
        reviewer="local-user",
        rationale="Reviewed tracked golden export.",
        accept_golden=True,
        workspace_root=workspace,
    )

    path = fixture / "build" / "closeout" / "golden_acceptance.json"
    assert result["path"] == "build/closeout/golden_acceptance.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == "figure-agent.golden-acceptance.v1"
    assert payload["decision"] == "accept"
    assert payload["accept_golden"] is True
    assert payload["exports"]["pdf"].startswith("sha256:")


def test_closeout_accept_allows_first_time_tracked_golden_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "exports").mkdir()
    (fixture / "exports" / "candidate_demo.pdf").write_bytes(b"pdf")

    def realistic_readiness(*args, **kwargs):
        return {
            **_ready_payload(),
            "checks": [
                check
                for check in _ready_payload()["checks"]
                if check["id"] in {"candidate_apply", "compile", "critique"}
            ]
            + [
                {
                    "id": "export",
                    "state": "blocked",
                    "reason": (
                        "tracked golden export acceptance is invalid: missing"
                    ),
                    "command": None,
                },
                {
                    "id": "golden_acceptance",
                    "state": "blocked",
                    "reason": "tracked golden export requires current golden acceptance",
                    "command": None,
                },
                {
                    "id": "final_artifact",
                    "state": "passed",
                    "reason": "final_artifact_state is NONE",
                    "command": None,
                },
                {
                    "id": "release",
                    "state": "blocked",
                    "reason": "release_ready is false",
                    "command": None,
                },
                {
                    "id": "loop_rerun",
                    "state": "blocked",
                    "reason": "closeout prerequisites are incomplete: export",
                    "command": None,
                },
            ],
        }

    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        realistic_readiness,
    )

    result = golden_acceptance.write_golden_acceptance(
        "candidate_demo",
        decision="accept",
        reviewer="local-user",
        rationale="Reviewed tracked golden export.",
        accept_golden=True,
        workspace_root=workspace,
    )

    assert result["path"] == "build/closeout/golden_acceptance.json"


def test_closeout_accept_requires_accept_golden_for_tracked_golden(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="accept_golden_required"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=False,
            workspace_root=workspace,
        )


def test_closeout_accept_rejects_stale_critique(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(critique_state="needs_action"),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="closeout_not_ready"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
        )


def test_closeout_accept_rejects_symlinked_output(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    closeout_dir = fixture / "build" / "closeout"
    closeout_dir.mkdir()
    outside = tmp_path / "golden_acceptance.json"
    outside.write_text("{}", encoding="utf-8")
    (closeout_dir / "golden_acceptance.json").symlink_to(outside)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="sandbox_symlink"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
        )


def test_closeout_accept_rejects_symlinked_export(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    exports = fixture / "exports"
    exports.mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"outside")
    (exports / "candidate_demo.pdf").symlink_to(outside)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="sandbox_symlink"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
        )


def test_closeout_accept_rejects_symlinked_build_dir(tmp_path: Path, monkeypatch) -> None:
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
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="sandbox_symlink"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
        )


def test_closeout_accept_rejects_symlinked_closeout_dir(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    closeout_dir = fixture / "build" / "closeout"
    outside = tmp_path / "outside-closeout"
    outside.mkdir()
    closeout_dir.symlink_to(outside)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="sandbox_symlink"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
        )
