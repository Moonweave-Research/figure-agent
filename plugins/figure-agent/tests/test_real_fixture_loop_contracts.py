"""Real-fixture checkpoint contracts for /fig_loop --json."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_loop as fig_loop_mod  # noqa: E402
import status as status_mod  # noqa: E402
from fig_loop_records import json_stdout_summary  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_CONTRACT_PATH = Path(__file__).with_name("real_fixture_state_contracts.yaml")
LOOP_CONTRACT_PATH = Path(__file__).with_name("real_fixture_loop_contracts.yaml")


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _load_cases() -> list[dict[str, Any]]:
    cases = _load_yaml_mapping(LOOP_CONTRACT_PATH).get("cases")
    assert isinstance(cases, list)
    return cases


def _state_contracts() -> dict[str, dict[str, Any]]:
    fixtures = _load_yaml_mapping(STATE_CONTRACT_PATH).get("fixtures")
    assert isinstance(fixtures, list)
    return {contract["fixture"]: contract for contract in fixtures}


def _copy_fixture_to_repo(tmp_path: Path, fixture_name: str) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    examples_dir = repo_root / "examples"
    examples_dir.mkdir(parents=True)
    source = REPO_ROOT / "examples" / fixture_name
    assert source.is_dir(), f"missing real fixture: {source}"
    fixture = examples_dir / fixture_name
    shutil.copytree(source, fixture, ignore=shutil.ignore_patterns("build", "exports"))
    return repo_root, fixture


def _materialize_controlled_artifacts(
    fixture: Path,
    fixture_name: str,
    state_contract: dict[str, Any],
) -> None:
    artifacts = state_contract.get("artifacts", {})
    assert isinstance(artifacts, dict)
    if artifacts.get("build_pdf"):
        build_pdf = fixture / "build" / f"{fixture_name}.pdf"
        build_pdf.parent.mkdir(parents=True, exist_ok=True)
        build_pdf.write_bytes(b"%PDF-1.4\n% controlled test artifact\n")

    exports = artifacts.get("exports", [])
    assert isinstance(exports, list)
    for ext in exports:
        assert isinstance(ext, str)
        export_path = fixture / "exports" / f"{fixture_name}.{ext}"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_bytes(b"controlled test artifact\n")


def _set_tree_mtime(root: Path, timestamp: float) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            os.utime(path, (timestamp, timestamp))


def _normalize_fixture_mtimes(fixture: Path, fixture_name: str) -> None:
    old_time = 1_700_000_000.0
    fresh_time = old_time + 100
    _set_tree_mtime(fixture, old_time)
    for directory_name in ("build", "exports"):
        directory = fixture / directory_name
        if directory.is_dir():
            _set_tree_mtime(directory, fresh_time)
    for path in (
        fixture / "critique.md",
        fixture / "critique_adjudication.yaml",
    ):
        if path.is_file():
            os.utime(path, (fresh_time, fresh_time))
    build_pdf = fixture / "build" / f"{fixture_name}.pdf"
    if build_pdf.is_file():
        os.utime(build_pdf, (fresh_time, fresh_time))


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
    repo_root, fixture = _copy_fixture_to_repo(tmp_path, fixture_name)
    _materialize_controlled_artifacts(fixture, fixture_name, state_contract)
    if decisions := case.get("adjudication_decisions"):
        assert isinstance(decisions, list)
        _write_adjudication_decisions(fixture, decisions)
    if remove_paths := case.get("remove_paths"):
        assert isinstance(remove_paths, list)
        _remove_fixture_paths(fixture, remove_paths)
    _normalize_fixture_mtimes(fixture, fixture_name)

    style_lock = tmp_path / "polymer-paper-preamble.sty"
    style_lock.write_text("% stable style lock\n", encoding="utf-8")
    os.utime(style_lock, (1_700_000_000.0, 1_700_000_000.0))
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
