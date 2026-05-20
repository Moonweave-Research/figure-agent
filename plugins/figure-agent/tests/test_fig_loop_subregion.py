from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_subregion import active_subregion_target  # noqa: E402


def test_active_subregion_target_returns_none_without_log(tmp_path: Path) -> None:
    assert active_subregion_target(tmp_path / "loop_demo") is None


def test_active_subregion_target_returns_first_active_target(tmp_path: Path) -> None:
    fixture = tmp_path / "loop_demo"
    fixture.mkdir()
    (fixture / "subregion_iteration_log.md").write_text(
        "## Active Target Set\n\n"
        "| State | Sub-region ID | Evidence | Notes |\n"
        "|---|---|---|---|\n"
        "| active target | D-2 | current loop | label spacing |\n"
        "| active target | E-1 | current loop | whitespace |\n",
        encoding="utf-8",
    )

    assert active_subregion_target(fixture) == {
        "finding_id": None,
        "patch_target": "D-2",
        "reason": "active sub-region target",
    }


def test_active_subregion_target_ignores_inactive_rows(tmp_path: Path) -> None:
    fixture = tmp_path / "loop_demo"
    fixture.mkdir()
    (fixture / "subregion_iteration_log.md").write_text(
        "## Active Target Set\n\n"
        "| State | Sub-region ID | Evidence | Notes |\n"
        "|---|---|---|---|\n"
        "| done | D-2 | previous loop | resolved |\n",
        encoding="utf-8",
    )

    assert active_subregion_target(fixture) is None
