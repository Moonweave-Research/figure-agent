from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import benchmark_contracts  # noqa: E402


def _fixture(workspace: Path, name: str = "contract_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    return fixture


def _write_contract(fixture: Path, *, text: str | None = None) -> None:
    payload = text or """
schema: figure-agent.benchmark-contract.v1
fixture: contract_demo
defect_class: label_overlap
candidate_families:
  - label-repair
candidate_edit_classes:
  - label_offset
required_detectors:
  - text_boundary
detector_reports:
  text_boundary: build/reports/text_boundary.json
expected_movement:
  text_boundary.blocker_count: decrease_or_equal
hard_regressions:
  - source_compile_failure
reference_policy:
  kind: repo_authored_synthetic
  external_images_allowed: false
  golden_target_allowed: true
"""
    (fixture / "benchmark_contract.yaml").write_text(payload.strip() + "\n", encoding="utf-8")


def test_valid_benchmark_contract_loads(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_contract(fixture)

    payload = benchmark_contracts.load_contract(
        "contract_demo",
        workspace_root=workspace,
    )

    assert payload["schema"] == "figure-agent.benchmark-contract.v1"
    assert payload["state"] == "present"
    assert payload["fixture"] == "contract_demo"
    assert payload["defect_class"] == "label_overlap"
    assert payload["candidate_families"] == ["label-repair"]
    assert payload["candidate_edit_classes"] == ["label_offset"]


def test_missing_benchmark_contract_is_structured_state(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = benchmark_contracts.load_contract(
        "contract_demo",
        workspace_root=workspace,
    )

    assert payload["schema"] == "figure-agent.benchmark-contract.v1"
    assert payload["state"] == "missing"
    assert payload["fixture"] == "contract_demo"


def test_benchmark_contract_rejects_path_escape(tmp_path: Path) -> None:
    with pytest.raises(benchmark_contracts.BenchmarkContractError, match="fixture name"):
        benchmark_contracts.load_contract("../escape", workspace_root=tmp_path / "workspace")


def test_benchmark_contract_rejects_unknown_hard_regression(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_contract(
        fixture,
        text="""
schema: figure-agent.benchmark-contract.v1
fixture: contract_demo
defect_class: label_overlap
candidate_families:
  - label-repair
candidate_edit_classes:
  - label_offset
required_detectors: []
expected_movement: {}
hard_regressions:
  - mystery_regression
reference_policy:
  kind: repo_authored_synthetic
  external_images_allowed: false
  golden_target_allowed: true
""",
    )

    with pytest.raises(benchmark_contracts.BenchmarkContractError, match="unknown_hard_regression"):
        benchmark_contracts.load_contract("contract_demo", workspace_root=workspace)


def test_benchmark_contract_rejects_edit_class_as_family(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_contract(
        fixture,
        text="""
schema: figure-agent.benchmark-contract.v1
fixture: contract_demo
defect_class: label_overlap
candidate_families:
  - label_offset
candidate_edit_classes:
  - label_offset
required_detectors: []
expected_movement: {}
hard_regressions:
  - source_compile_failure
reference_policy:
  kind: repo_authored_synthetic
  external_images_allowed: false
  golden_target_allowed: true
""",
    )

    with pytest.raises(
        benchmark_contracts.BenchmarkContractError,
        match="candidate_family_invalid",
    ):
        benchmark_contracts.load_contract("contract_demo", workspace_root=workspace)


def test_benchmark_contract_rejects_detector_path_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_contract(
        fixture,
        text="""
schema: figure-agent.benchmark-contract.v1
fixture: contract_demo
defect_class: label_overlap
candidate_families:
  - label-repair
candidate_edit_classes:
  - label_offset
required_detectors:
  - text_boundary
detector_reports:
  text_boundary: ../outside.json
expected_movement:
  text_boundary.blocker_count: decrease_or_equal
hard_regressions:
  - source_compile_failure
reference_policy:
  kind: repo_authored_synthetic
  external_images_allowed: false
  golden_target_allowed: true
""",
    )

    with pytest.raises(benchmark_contracts.BenchmarkContractError, match="detector_report_path"):
        benchmark_contracts.load_contract("contract_demo", workspace_root=workspace)


def test_pattern_contract_requires_reference_policy(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_contract(
        fixture,
        text="""
schema: figure-agent.benchmark-contract.v1
fixture: contract_demo
defect_class: label_overlap
candidate_families:
  - label-repair
candidate_edit_classes:
  - label_offset
required_detectors: []
expected_movement: {}
hard_regressions:
  - source_compile_failure
""",
    )

    with pytest.raises(
        benchmark_contracts.BenchmarkContractError,
        match="reference_policy_missing",
    ):
        benchmark_contracts.load_contract(
            "contract_demo",
            workspace_root=workspace,
            suite_role="patterns",
        )
