from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_apply  # noqa: E402


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text("old\n", encoding="utf-8")
    return fixture


def test_apply_refuses_human_required_effective_authority(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    manifest = {
        "candidate_id": "CAND001",
        "effective_apply_authority": "review_only",
        "operations": [
            {
                "kind": "replace_text",
                "path": "examples/candidate_demo/candidate_demo.tex",
                "original": "old",
                "replacement": "new",
            }
        ],
    }

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        apply=True,
    )

    assert result["schema"] == "figure-agent.candidate-apply-result.v1"
    assert result["applied"] is False
    assert result["error"]["code"] == "not_apply_eligible"
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == "old\n"


def test_apply_eligible_dry_run_does_not_mutate_source(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    manifest = {
        "candidate_id": "CAND001",
        "effective_apply_authority": "apply_eligible",
        "operations": [
            {
                "kind": "replace_text",
                "path": "examples/candidate_demo/candidate_demo.tex",
                "original": "old",
                "replacement": "new",
            }
        ],
    }

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        apply=False,
    )

    assert result["applied"] is False
    assert result["dry_run"] is True
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == "old\n"


def test_apply_eligible_apply_path_is_explicitly_not_implemented_yet(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    manifest = {
        "candidate_id": "CAND001",
        "effective_apply_authority": "apply_eligible",
        "operations": [
            {
                "kind": "replace_text",
                "path": "examples/candidate_demo/candidate_demo.tex",
                "original": "old",
                "replacement": "new",
            }
        ],
    }

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        apply=True,
    )

    assert result["applied"] is False
    assert result["error"]["code"] == "apply_not_implemented_for_non_refusal_path"
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == "old\n"


def test_apply_validates_fixture_name_before_result(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    with pytest.raises(ValueError, match="fixture name"):
        candidate_apply.apply_candidate(
            "../candidate_demo",
            {"candidate_id": "CAND001", "effective_apply_authority": "review_only"},
            workspace_root=workspace,
            apply=True,
        )
