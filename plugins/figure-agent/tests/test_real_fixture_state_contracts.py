"""Real-fixture state-machine contract matrix for /fig_status and /fig_drive."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

TESTS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_ROOT))
sys.path.insert(0, str(TESTS_ROOT.parents[0] / "scripts"))

import fig_driver  # noqa: E402
import status as status_mod  # noqa: E402
from real_fixture_contract_helpers import (  # noqa: E402
    copy_fixture_to_repo,
    load_yaml_mapping,
    materialize_controlled_artifacts,
    normalize_fixture_mtimes,
    stable_style_lock,
)

CONTRACT_PATH = Path(__file__).with_name("real_fixture_state_contracts.yaml")


def _load_contracts() -> list[dict[str, Any]]:
    data = load_yaml_mapping(CONTRACT_PATH)
    fixtures = data.get("fixtures")
    assert isinstance(fixtures, list)
    return fixtures


@pytest.mark.parametrize("contract", _load_contracts(), ids=lambda item: item["fixture"])
def test_real_fixture_status_contract_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: dict[str, Any],
) -> None:
    fixture_name = contract["fixture"]
    repo_root, fixture = copy_fixture_to_repo(tmp_path, fixture_name)
    materialize_controlled_artifacts(fixture, fixture_name, contract)
    normalize_fixture_mtimes(fixture, fixture_name)
    style_lock = stable_style_lock(tmp_path)

    monkeypatch.setattr(status_mod, "STYLE_LOCK_PATH", style_lock)
    monkeypatch.setattr(
        status_mod,
        "compute_export_state",
        lambda _example_dir, _name: contract["controlled_export_state"],
    )
    monkeypatch.setattr(fig_driver, "_workspace_warnings", lambda _repo_root: [])
    monkeypatch.setattr(
        fig_driver.checkpoint_mod,
        "latest_loop_checkpoint",
        lambda _repo_root, _name, _example_dir: None,
    )
    monkeypatch.setattr(
        fig_driver.closeout_mod,
        "closeout_report",
        lambda _name, *, repo_root: {
            "closeout_complete": True,
            "next_action": "closeout not required",
        },
    )

    status = status_mod.infer_stage(fixture)
    for key, expected in contract["status"].items():
        assert status.get(key) == expected, f"{fixture_name} status.{key}"

    for mode, expected in contract.get("driver", {}).items():
        summary = fig_driver.build_driver_summary(
            fixture_name,
            mode=mode,
            goal="contract matrix",
            repo_root=repo_root,
        )
        for key, expected_value in expected.items():
            assert summary.get(key) == expected_value, f"{fixture_name} {mode}.{key}"
