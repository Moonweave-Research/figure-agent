from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_contracts  # noqa: E402


def test_effective_authority_downgrades_hard_gate_states() -> None:
    assert (
        candidate_contracts.effective_apply_authority("apply_eligible", "pass")
        == "apply_eligible"
    )
    assert (
        candidate_contracts.effective_apply_authority("apply_eligible", "human_required")
        == "review_only"
    )
    assert (
        candidate_contracts.effective_apply_authority("apply_eligible", "rejected")
        == "rejected"
    )


def test_effective_authority_rejects_invalid_apply_authority() -> None:
    with pytest.raises(candidate_contracts.CandidateContractError, match="invalid apply_authority"):
        candidate_contracts.effective_apply_authority("auto_apply", "pass")


def test_effective_authority_rejects_invalid_hard_gate_state() -> None:
    with pytest.raises(candidate_contracts.CandidateContractError, match="invalid hard_gate_state"):
        candidate_contracts.effective_apply_authority("apply_eligible", "needs_review")


def test_fixture_path_rejects_escape(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "demo"
    fixture.mkdir(parents=True)

    assert candidate_contracts.fixture_relative_path(fixture, "demo.tex") == fixture / "demo.tex"
    try:
        candidate_contracts.fixture_relative_path(fixture, "../outside.tex")
    except candidate_contracts.CandidateContractError as exc:
        assert "path_escape" in str(exc)
    else:
        raise AssertionError("expected path_escape")


def test_fixture_local_output_path_resolves_inside_fixture(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "demo"
    fixture.mkdir(parents=True)

    assert (
        candidate_contracts.fixture_local_output_path(
            workspace,
            "demo",
            "build/candidates/candidate_set.json",
        )
        == fixture / "build" / "candidates" / "candidate_set.json"
    )


def test_fixture_local_output_path_rejects_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "demo"
    fixture.mkdir(parents=True)

    with pytest.raises(candidate_contracts.CandidateContractError, match="path_escape"):
        candidate_contracts.fixture_local_output_path(workspace, "demo", "../candidate_set.json")
