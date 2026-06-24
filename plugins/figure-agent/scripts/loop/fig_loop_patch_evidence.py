"""Patch evidence baseline helpers for fig_loop."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from quality_manifest import file_sha256

PATCH_EVIDENCE_SCHEMA = "figure-agent.patch-evidence.v1"
POST_PATCH_EVIDENCE_SCHEMA = "figure-agent.post-patch-evidence.v1"
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


def valid_previous_iteration(iteration_path: Path, name: str) -> bool:
    manifest_path = iteration_path.parent / "run_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        iteration = json.loads(iteration_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(manifest, dict)
        and manifest.get("schema") == "figure-agent.fig-loop-run.v1"
        and manifest.get("fixture") == name
        and isinstance(iteration, dict)
        and isinstance(iteration.get("patch_evidence"), dict)
        and iteration["patch_evidence"].get("phase") == "pre_patch"
    )


def latest_patch_evidence_baseline(
    runs_root: Path,
    name: str,
) -> tuple[Path, dict[str, Any]] | None:
    candidates = [
        path
        for path in runs_root.glob(f"*-{name}/iteration_001.json")
        if valid_previous_iteration(path, name)
    ]
    if not candidates:
        return None
    iteration_path = max(candidates, key=lambda path: path.stat().st_mtime)
    iteration = json.loads(iteration_path.read_text(encoding="utf-8"))
    return iteration_path, iteration["patch_evidence"]


def decision_for_target(adjudication: dict[str, Any], target_id: str) -> str | None:
    if adjudication["state"] != "fresh":
        return None
    for decision in adjudication.get("decisions", []):
        if decision.get("finding_id") == target_id:
            return decision.get("decision")
    return None


def post_patch_evidence_verdict(
    repo_root: Path,
    runs_root: Path,
    name: str,
    adjudication: dict[str, Any],
    status_result: dict[str, Any],
) -> dict[str, Any] | None:
    baseline = latest_patch_evidence_baseline(runs_root, name)
    if baseline is None:
        return None
    baseline_path, patch_evidence = baseline
    changed_paths = []
    for item in patch_evidence.get("pre_patch", {}).get("allowed_edit_scope", []):
        rel_path = item.get("path")
        if not isinstance(rel_path, str):
            continue
        current = path_evidence(repo_root, rel_path)
        if current["exists"] != item.get("exists") or current["sha256"] != item.get("sha256"):
            changed_paths.append(rel_path)

    target_id = str(patch_evidence.get("target_id", ""))
    current_decision = decision_for_target(adjudication, target_id)
    allowed_changed = bool(changed_paths)
    if status_result.get("render_state") not in {"FRESH", "MISSING"}:
        verdict = "regressed"
    elif current_decision == "resolved" and allowed_changed:
        verdict = "resolved"
    elif current_decision in {"apply", "defer"} or not allowed_changed:
        verdict = "unresolved"
    else:
        verdict = "ambiguous"

    return {
        "schema": POST_PATCH_EVIDENCE_SCHEMA,
        "baseline_path": str(baseline_path),
        "target_type": patch_evidence.get("target_type"),
        "target_id": target_id,
        "verdict": verdict,
        "allowed_edit_scope_changed": allowed_changed,
        "changed_allowed_paths": changed_paths,
        "current_decision": current_decision,
        "may_edit": False,
    }
