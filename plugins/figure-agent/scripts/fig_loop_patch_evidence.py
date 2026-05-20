"""Patch evidence baseline helpers for fig_loop."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from quality_manifest import file_sha256

PATCH_EVIDENCE_SCHEMA = "figure-agent.patch-evidence.v1"
PATCH_EVIDENCE_VERDICTS = ["resolved", "unresolved", "regressed", "ambiguous"]


def path_evidence(repo_root: Path, rel_path: str) -> dict[str, Any]:
    path = repo_root / rel_path
    exists = path.is_file()
    return {
        "path": rel_path,
        "exists": exists,
        "sha256": file_sha256(path) if exists else None,
    }


def patch_evidence_baseline(
    repo_root: Path,
    patch_handoff: dict[str, Any] | None,
    *,
    git_commit: Callable[[], str | None],
) -> dict[str, Any] | None:
    if not patch_handoff:
        return None
    return {
        "schema": PATCH_EVIDENCE_SCHEMA,
        "phase": "pre_patch",
        "target_type": patch_handoff["target_type"],
        "target_id": patch_handoff["target_id"],
        "verdict": "not_evaluated",
        "may_edit": False,
        "pre_patch": {
            "allowed_edit_scope": [
                path_evidence(repo_root, rel_path)
                for rel_path in patch_handoff["allowed_edit_scope"]
            ]
        },
        "post_patch_required_verdicts": list(PATCH_EVIDENCE_VERDICTS),
        "rollback_reference": {
            "git_commit": git_commit(),
            "restore_strategy": (
                "restore allowed_edit_scope paths to the recorded pre_patch sha256 values"
            ),
        },
    }
