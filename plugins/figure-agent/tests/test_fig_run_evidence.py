from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_run_evidence  # noqa: E402


def test_fixture_evidence_paths_rejects_unsafe_fixture_name() -> None:
    with pytest.raises(
        ValueError, match="fixture name must be a single examples/<name> directory name"
    ):
        fig_run_evidence.fixture_evidence_paths(Path("/repo"), "../outside")


def test_evidence_snapshot_rejects_unsafe_fixture_name_before_reading_outside_root(
    tmp_path: Path,
) -> None:
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "briefing.md").write_text("outside evidence\n", encoding="utf-8")

    with pytest.raises(
        ValueError, match="fixture name must be a single examples/<name> directory name"
    ):
        fig_run_evidence.evidence_snapshot(tmp_path, "../outside")


def test_snapshot_stale_paths_rejects_unsafe_fixture_name_even_without_snapshot(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError, match="fixture name must be a single examples/<name> directory name"
    ):
        fig_run_evidence.snapshot_stale_paths(tmp_path, "../outside", None)
