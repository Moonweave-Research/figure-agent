"""Loop-runner decode robustness on non-UTF8 sub-tool stderr.

The verify-only loop shells out to git (`fig_loop._git_value`) and the patch
executor shells out to `/usr/bin/patch` (`fig_loop_patch_executor._run_patch`).
Both capture stderr with text=True; a child that leaks a non-UTF8 byte on
stderr must degrade through errors="replace" instead of raising
UnicodeDecodeError before the runner reaches its returncode guard.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import fig_loop  # noqa: E402
import fig_loop_patch_executor  # noqa: E402


def _passthrough_to_nonutf8_stderr_child(monkeypatch) -> None:
    """Redirect subprocess.run to a real child that fails with non-UTF8 stderr.

    The real subprocess.run performs the text=True decode; **kwargs passthrough
    means the caller's errors= (or its absence) flows into that decode. Without
    errors="replace" this raises UnicodeDecodeError before the returncode guard;
    with it, the call reaches the returncode check.
    """
    real_run = subprocess.run
    child = [
        sys.executable,
        "-c",
        "import os,sys; os.write(2, b'\\xff\\xfe warn'); sys.exit(1)",
    ]

    def _run(_args, *_pos, **kwargs):
        return real_run(child, **kwargs)

    monkeypatch.setattr(subprocess, "run", _run)


def test_git_value_tolerates_nonutf8_stderr(monkeypatch, tmp_path: Path) -> None:
    _passthrough_to_nonutf8_stderr_child(monkeypatch)

    # Non-zero exit -> None, but only if the text=True stderr decode survives.
    assert fig_loop._git_value(tmp_path, ("rev-parse", "HEAD")) is None


def test_run_patch_tolerates_nonutf8_stderr(monkeypatch, tmp_path: Path) -> None:
    patch_file = tmp_path / "change.patch"
    patch_file.write_text("", encoding="utf-8")
    _passthrough_to_nonutf8_stderr_child(monkeypatch)

    # Non-zero exit -> PatchExecutorError, reached only after a clean decode.
    with pytest.raises(fig_loop_patch_executor.PatchExecutorError):
        fig_loop_patch_executor._run_patch(tmp_path, patch_file, dry_run=False, strip_level=1)
