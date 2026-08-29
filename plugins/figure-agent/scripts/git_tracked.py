"""Helper: is a path git-tracked?

Used by the export-staleness pipeline to identify TRACKED_GOLDEN fixtures
whose curated exports/ artifacts must never be auto-clobbered.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def repo_root_for(path: Path) -> Path | None:
    """Return the git repository that contains ``path``, or None.

    Golden protection asks whether an export is committed. Asking that of the
    plugin's own repository answers for the wrong tree whenever the fixture
    lives in an external workspace, where the path is not under the plugin at
    all — so a committed golden export reported as untracked and lost its
    protection.
    """
    directory = path if path.is_dir() else path.parent
    try:
        result = subprocess.run(
            ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    top = result.stdout.strip()
    return Path(top) if top else None


def is_tracked(path: Path, repo_root: Path) -> bool:
    """Return True iff `git ls-files --error-unmatch` finds `path` in `repo_root`.

    Returns False when `path` does not exist, is not under `repo_root`, or is
    not git-tracked. Never raises on subprocess failure — git's exit code 1
    means "not tracked," which is the False answer.
    """
    if not path.exists():
        return False
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(rel)],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0
