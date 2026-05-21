"""Real-fixture checkpoint contracts for /fig_loop --json."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

TESTS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_ROOT))
sys.path.insert(0, str(TESTS_ROOT.parents[0] / "scripts"))

import fig_loop as fig_loop_mod  # noqa: E402
import status as status_mod  # noqa: E402
from fig_loop_records import json_stdout_summary  # noqa: E402
from real_fixture_contract_helpers import (  # noqa: E402
    copy_fixture_to_repo,
    load_yaml_mapping,
    materialize_controlled_artifacts,
    normalize_fixture_mtimes,
    stable_style_lock,
)

STATE_CONTRACT_PATH = Path(__file__).with_name("real_fixture_state_contracts.yaml")
LOOP_CONTRACT_PATH = Path(__file__).with_name("real_fixture_loop_contracts.yaml")


def _load_cases() -> list[dict[str, Any]]:
    cases = load_yaml_mapping(LOOP_CONTRACT_PATH).get("cases")
    assert isinstance(cases, list)
    return cases


def _state_contracts() -> dict[str, dict[str, Any]]:
    fixtures = load_yaml_mapping(STATE_CONTRACT_PATH).get("fixtures")
    assert isinstance(fixtures, list)
    return {contract["fixture"]: contract for contract in fixtures}


def _write_adjudication_decisions(
    fixture: Path,
    decisions: list[dict[str, Any]],
) -> None:
    path = fixture / "critique_adjudication.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    data["decisions"] = decisions
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _remove_fixture_paths(fixture: Path, paths: list[str]) -> None:
    for relative in paths:
        path = fixture / relative
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


@pytest.mark.parametrize("case", _load_cases(), ids=lambda item: item["id"])
def test_real_fixture_loop_checkpoint_contract_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: dict[str, Any],
) -> None:
    state_contract = _state_contracts()[case["fixture"]]
    fixture_name = case["fixture"]
    repo_root, fixture = copy_fixture_to_repo(tmp_path, fixture_name)
    materialize_controlled_artifacts(fixture, fixture_name, state_contract)
    if decisions := case.get("adjudication_decisions"):
        assert isinstance(decisions, list)
        _write_adjudication_decisions(fixture, decisions)
    if remove_paths := case.get("remove_paths"):
        assert isinstance(remove_paths, list)
        _remove_fixture_paths(fixture, remove_paths)
    normalize_fixture_mtimes(fixture, fixture_name)

    style_lock = stable_style_lock(tmp_path)
    monkeypatch.setattr(status_mod, "STYLE_LOCK_PATH", style_lock)
    monkeypatch.setattr(
        status_mod,
        "compute_export_state",
        lambda _example_dir, _name: state_contract["controlled_export_state"],
    )

    status_overrides = case.get("status_overrides", {})
    assert isinstance(status_overrides, dict)
    if status_overrides:
        original_infer_stage = fig_loop_mod.infer_stage

        def infer_stage_with_overrides(example_dir: Path) -> dict[str, Any]:
            result = original_infer_stage(example_dir)
            result.update(status_overrides)
            return result

        monkeypatch.setattr(fig_loop_mod, "infer_stage", infer_stage_with_overrides)

    run_dir = fig_loop_mod.run_loop(
        fixture_name,
        case["goal"],
        repo_root=repo_root,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    manifest_path = run_dir / "run_manifest.json"
    iteration_path = run_dir / "iteration_001.json"
    decision_path = run_dir / "decision.md"
    assert manifest_path.is_file()
    assert iteration_path.is_file()
    assert decision_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    iteration = json.loads(iteration_path.read_text(encoding="utf-8"))
    stdout_summary = json_stdout_summary(run_dir)
    expected = case["expected"]

    assert manifest["schema"] == "figure-agent.fig-loop-run.v1"
    assert manifest["fixture"] == fixture_name
    assert manifest["mode"] == "verify-only"
    assert manifest["goal"] == case["goal"]
    assert manifest["iterations"] == ["iteration_001.json"]

    for key, expected_value in expected["manifest"].items():
        assert manifest.get(key) == expected_value, f"{case['id']} manifest.{key}"
    for key, expected_value in expected["iteration"].items():
        if key == "patch_handoff_present":
            actual_value = iteration.get("patch_handoff") is not None
        else:
            actual_value = iteration.get(key)
        assert actual_value == expected_value, f"{case['id']} iteration.{key}"
    for key, expected_value in expected.get("status", {}).items():
        assert iteration["status"].get(key) == expected_value, f"{case['id']} status.{key}"
    for key, expected_value in expected.get("adjudication", {}).items():
        assert (
            iteration["adjudication"].get(key) == expected_value
        ), f"{case['id']} adjudication.{key}"
    for key, expected_value in expected["stdout"].items():
        assert stdout_summary.get(key) == expected_value, f"{case['id']} stdout.{key}"
