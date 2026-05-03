"""Tests for scripts/export_freshness.compute_export_state — sub-state logic.

Layer A end-to-end invariant test (`test_freshness_invariant_after_export`)
is added in Task 7 of the implementation plan; this file currently covers
only the four sub-state branches.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from export_freshness import (  # noqa: E402
    EXPORT_FRESH,
    EXPORT_MISSING,
    EXPORT_STALE,
    EXPORT_TRACKED_GOLDEN,
    compute_export_state,
)


def _scaffold_minimal_fixture(root: Path, name: str, body: str = "hello") -> Path:
    """Create a fixture dir with a minimal compiled PDF in build/."""
    fixture = root / "examples" / name
    (fixture / "build").mkdir(parents=True, exist_ok=True)
    (fixture / "exports").mkdir(parents=True, exist_ok=True)
    (fixture / f"{name}.tex").write_text(
        r"\documentclass[border=2pt]{standalone}"
        "\n"
        rf"\begin{{document}}{body}\end{{document}}"
        "\n",
        encoding="utf-8",
    )
    if shutil.which("lualatex") is None:
        pytest.skip("requires lualatex")
    subprocess.run(
        [
            "lualatex",
            "-output-directory",
            str(fixture / "build"),
            "-interaction=nonstopmode",
            str(fixture / (name + ".tex")),
        ],
        check=True,
        capture_output=True,
    )
    return fixture


def test_state_missing_when_no_exports_pdf(tmp_path: Path) -> None:
    fixture = _scaffold_minimal_fixture(tmp_path, "fix_missing")
    assert compute_export_state(fixture, "fix_missing") == EXPORT_MISSING


def test_state_fresh_when_exports_pdf_matches_build(tmp_path: Path) -> None:
    fixture = _scaffold_minimal_fixture(tmp_path, "fix_fresh")
    shutil.copy(fixture / "build" / "fix_fresh.pdf", fixture / "exports" / "fix_fresh.pdf")
    assert compute_export_state(fixture, "fix_fresh") == EXPORT_FRESH


def test_state_stale_when_exports_pdf_differs_from_build(tmp_path: Path) -> None:
    fixture = _scaffold_minimal_fixture(tmp_path, "fix_stale_a", body="hello")
    other = _scaffold_minimal_fixture(tmp_path, "fix_stale_b", body="goodbye world")
    shutil.copy(other / "build" / "fix_stale_b.pdf", fixture / "exports" / "fix_stale_a.pdf")
    assert compute_export_state(fixture, "fix_stale_a") == EXPORT_STALE


def test_state_tracked_golden_when_exports_pdf_is_git_tracked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The repo's golden_trap_depth_picture fixture has its exports/ artifacts
    git-tracked via .gitignore exclusion. compute_export_state must see them
    as TRACKED_GOLDEN regardless of build state."""
    fixture = REPO_ROOT / "examples" / "golden_trap_depth_picture"
    pdf = fixture / "exports" / "golden_trap_depth_picture.pdf"
    if not pdf.is_file():
        pytest.skip("golden fixture exports/PDF not present in checkout")
    state = compute_export_state(fixture, "golden_trap_depth_picture")
    assert state == EXPORT_TRACKED_GOLDEN
