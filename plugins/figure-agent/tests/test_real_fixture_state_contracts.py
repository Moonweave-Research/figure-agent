"""Real-fixture state-machine contract matrix for /fig_status and /fig_drive."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_driver  # noqa: E402
import status as status_mod  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = Path(__file__).with_name("real_fixture_state_contracts.yaml")


def _load_contracts() -> list[dict[str, Any]]:
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    fixtures = data.get("fixtures")
    assert isinstance(fixtures, list)
    return fixtures


def _copy_fixture_to_repo(tmp_path: Path, fixture_name: str) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    examples_dir = repo_root / "examples"
    examples_dir.mkdir(parents=True)
    source = REPO_ROOT / "examples" / fixture_name
    assert source.is_dir(), f"missing real fixture: {source}"
    fixture = examples_dir / fixture_name
    shutil.copytree(source, fixture)
    return repo_root, fixture


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


@pytest.mark.parametrize("contract", _load_contracts(), ids=lambda item: item["fixture"])
def test_real_fixture_status_contract_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: dict[str, Any],
) -> None:
    fixture_name = contract["fixture"]
    repo_root, fixture = _copy_fixture_to_repo(tmp_path, fixture_name)
    _normalize_fixture_mtimes(fixture, fixture_name)
    style_lock = tmp_path / "polymer-paper-preamble.sty"
    style_lock.write_text("% stable style lock\n", encoding="utf-8")
    os.utime(style_lock, (1_700_000_000.0, 1_700_000_000.0))

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
