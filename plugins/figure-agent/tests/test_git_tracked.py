"""Tests for scripts/git_tracked.is_tracked — git ls-files-based check."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import git_tracked  # noqa: E402
from export_freshness import (  # noqa: E402
    EXPORT_GOLDEN_UNVERIFIABLE,
    EXPORT_TRACKED_GOLDEN,
    compute_export_state,
)
from git_tracked import is_tracked, repo_root_for  # noqa: E402


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


def _init_repo(root: Path, *, commit: bool) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    if not commit:
        return
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@example.com",
            "-c",
            "user.name=Test",
            "commit",
            "-qm",
            "golden",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )


def test_repo_root_resolves_the_tree_that_holds_the_path(tmp_path: Path) -> None:
    external = tmp_path / "workspace"
    (external / "examples" / "demo").mkdir(parents=True)
    target = external / "examples" / "demo" / "demo.pdf"
    target.write_bytes(b"x")
    _init_repo(external, commit=True)

    resolved = repo_root_for(target)

    assert resolved is not None
    assert resolved.resolve() == external.resolve()


def test_repo_root_is_none_outside_any_repository(tmp_path: Path) -> None:
    loose = tmp_path / "loose"
    loose.mkdir()
    target = loose / "demo.pdf"
    target.write_bytes(b"x")

    # tmp_path is not inside a git repository on any supported runner.
    assert repo_root_for(target) is None


def _committed_external_fixture(tmp_path: Path) -> Path:
    external = tmp_path / "workspace"
    exports = external / "examples" / "extfig" / "exports"
    exports.mkdir(parents=True)
    (external / "examples" / "extfig" / "build").mkdir()
    for suffix in ("pdf", "svg", "png", "tif"):
        (exports / f"extfig.{suffix}").write_bytes(b"x")
    (external / "examples" / "extfig" / "build" / "extfig.pdf").write_bytes(b"y")
    _init_repo(external, commit=True)
    return external / "examples" / "extfig"


def test_external_workspace_export_keeps_its_golden_protection(tmp_path: Path) -> None:
    """Tracking was asked of the plugin's own repository, so a committed
    golden export in an external workspace read as untracked and could be
    overwritten without --force-golden."""
    state = compute_export_state(_committed_external_fixture(tmp_path), "extfig")

    assert state == EXPORT_TRACKED_GOLDEN


def test_golden_export_is_protected_when_git_is_absent_from_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _committed_external_fixture(tmp_path)
    empty_bin = tmp_path / "empty_bin"
    empty_bin.mkdir()
    monkeypatch.setenv("PATH", str(empty_bin))
    assert shutil.which("git") is None

    assert compute_export_state(fixture, "extfig") == EXPORT_GOLDEN_UNVERIFIABLE


def test_golden_export_is_protected_when_rev_parse_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exit 128 is not exotic: dubious ownership, a held index.lock, and an
    unreadable repository all produce it, and it used to read as STALE."""
    fixture = _committed_external_fixture(tmp_path)

    def dubious_ownership(args, **kwargs):  # noqa: ANN001, ANN202
        return subprocess.CompletedProcess(
            args,
            128,
            "",
            "fatal: detected dubious ownership in repository at '/somewhere'\n",
        )

    monkeypatch.setattr(git_tracked.subprocess, "run", dubious_ownership)

    assert compute_export_state(fixture, "extfig") == EXPORT_GOLDEN_UNVERIFIABLE


def test_golden_export_is_protected_when_ls_files_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _committed_external_fixture(tmp_path)
    real_run = git_tracked.subprocess.run

    def fatal_ls_files(args, **kwargs):  # noqa: ANN001, ANN202
        if "ls-files" in args:
            return subprocess.CompletedProcess(args, 128, "", "fatal: index file corrupt\n")
        return real_run(args, **kwargs)

    monkeypatch.setattr(git_tracked.subprocess, "run", fatal_ls_files)

    assert compute_export_state(fixture, "extfig") == EXPORT_GOLDEN_UNVERIFIABLE


def test_untracked_export_is_still_untracked_not_unverifiable(tmp_path: Path) -> None:
    """Positive control for the three tests above: with git healthy and the
    export uncommitted, the answer must move off GOLDEN_UNVERIFIABLE."""
    external = tmp_path / "workspace"
    exports = external / "examples" / "extfig" / "exports"
    exports.mkdir(parents=True)
    (external / "examples" / "extfig" / "build").mkdir()
    for suffix in ("pdf", "svg", "png", "tif"):
        (exports / f"extfig.{suffix}").write_bytes(b"x")
    (external / "examples" / "extfig" / "build" / "extfig.pdf").write_bytes(b"y")
    _init_repo(external, commit=False)

    state = compute_export_state(external / "examples" / "extfig", "extfig")

    assert state != EXPORT_GOLDEN_UNVERIFIABLE
    assert state != EXPORT_TRACKED_GOLDEN
    assert git_tracked.tracking_state(exports / "extfig.pdf", external) == git_tracked.UNTRACKED


def test_tracking_state_of_a_missing_git_binary_is_not_untracked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _committed_external_fixture(tmp_path)
    empty_bin = tmp_path / "empty_bin"
    empty_bin.mkdir()
    monkeypatch.setenv("PATH", str(empty_bin))

    target = fixture / "exports" / "extfig.pdf"

    assert git_tracked.tracking_state(target, tmp_path / "workspace") == git_tracked.UNVERIFIABLE
    # is_tracked keeps its bool contract; callers that must protect an artifact
    # branch on tracking_state instead.
    assert git_tracked.is_tracked(target, tmp_path / "workspace") is False
