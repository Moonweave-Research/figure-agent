"""Tests for scripts/git_tracked.is_tracked — git ls-files-based check."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from git_tracked import is_tracked  # noqa: E402


def test_is_tracked_true_for_known_tracked_file() -> None:
    """polymer-paper-preamble.sty is committed; must report True."""
    sty = REPO_ROOT / "styles" / "polymer-paper-preamble.sty"
    assert sty.is_file()
    assert is_tracked(sty, REPO_ROOT) is True


def test_is_tracked_false_for_known_ignored_file(tmp_path: Path) -> None:
    """A file in build/ (gitignored) must report False even when present on disk.

    Use tmp_path inside the repo to ensure the file is under the repo root yet
    matches the gitignore pattern via name.
    """
    build_dir = REPO_ROOT / "examples" / "_macro_smoke" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    test_file = build_dir / "ephemeral_marker.tmp"
    test_file.write_text("ephemeral", encoding="utf-8")
    try:
        assert is_tracked(test_file, REPO_ROOT) is False
    finally:
        test_file.unlink(missing_ok=True)


def test_is_tracked_false_for_nonexistent_file(tmp_path: Path) -> None:
    """A path that does not exist must report False, not raise."""
    ghost = REPO_ROOT / "examples" / "ghost_fixture" / "exports" / "ghost.pdf"
    assert is_tracked(ghost, REPO_ROOT) is False
