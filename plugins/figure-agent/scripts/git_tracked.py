"""Helper: is a path git-tracked?

Used by the export-staleness pipeline to identify TRACKED_GOLDEN fixtures
whose curated exports/ artifacts must never be auto-clobbered.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


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
