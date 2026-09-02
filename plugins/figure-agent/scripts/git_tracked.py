"""Helper: is a path git-tracked?

Used by the export-staleness pipeline to identify TRACKED_GOLDEN fixtures
whose curated exports/ artifacts must never be auto-clobbered.

Three answers, not two. `UNVERIFIABLE` is the answer git never gave — no git
binary, or a git error such as dubious ownership, a held index.lock, or an
unreadable repository. Reading it as `UNTRACKED` turns golden protection off
exactly when the environment is broken, so callers that protect an artifact
must branch on it instead of on a bool.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

TRACKED = "TRACKED"
UNTRACKED = "UNTRACKED"
UNVERIFIABLE = "UNVERIFIABLE"

# `git rev-parse` reports "no repository here" with the same exit 128 it uses
# for failures, so the message is the only discriminator. Force the C locale to
# keep it stable.
_NO_REPOSITORY = "not a git repository"


def _git(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            check=False,
            text=True,
            env={**os.environ, "LC_ALL": "C", "LANGUAGE": ""},
        )
    except OSError:
        return None


def repo_root_lookup(path: Path) -> tuple[Path | None, bool]:
    """Return (repository root containing `path`, whether git answered at all).

    Golden protection asks whether an export is committed. Asking that of the
    plugin's own repository answers for the wrong tree whenever the fixture
    lives in an external workspace, where the path is not under the plugin at
    all — so a committed golden export reported as untracked and lost its
    protection.
    """
    directory = path if path.is_dir() else path.parent
    result = _git(["-C", str(directory), "rev-parse", "--show-toplevel"])
    if result is None:
        return None, False
    if result.returncode != 0:
        return None, _NO_REPOSITORY in result.stderr
    top = result.stdout.strip()
    return (Path(top) if top else None), True


def repo_root_for(path: Path) -> Path | None:
    """Return the git repository that contains `path`, or None.

    None also covers "git could not be asked"; callers that must not treat the
    two alike use `repo_root_lookup`.
    """
    return repo_root_lookup(path)[0]


def tracking_state(path: Path, repo_root: Path) -> str:
    """Return TRACKED, UNTRACKED, or UNVERIFIABLE for `path` inside `repo_root`.

    `git ls-files --error-unmatch` exits 1 for "known to git? no" and 128 for
    "I cannot answer", so the two are distinguishable here.
    """
    if not path.exists():
        return UNTRACKED
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return UNTRACKED
    result = _git(["ls-files", "--error-unmatch", str(rel)], cwd=repo_root)
    if result is None:
        return UNVERIFIABLE
    if result.returncode == 0:
        return TRACKED
    if result.returncode == 1:
        return UNTRACKED
    return UNVERIFIABLE


def is_tracked(path: Path, repo_root: Path) -> bool:
    """Return True iff `git ls-files --error-unmatch` finds `path` in `repo_root`.

    UNVERIFIABLE reads as False, which is fail-closed for callers asking "may
    this authorize something?". A caller asking "may I overwrite this?" must
    use `tracking_state` — False would be fail-open there.
    """
    return tracking_state(path, repo_root) == TRACKED
