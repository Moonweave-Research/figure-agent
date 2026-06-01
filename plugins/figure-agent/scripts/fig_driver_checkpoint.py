"""Read latest current fig_loop checkpoint for fig_driver."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_loop_checkpoint(run_dir: Path, name: str) -> dict[str, Any] | None:
    manifest_path = run_dir / "run_manifest.json"
    iteration_path = run_dir / "iteration_001.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        iteration = json.loads(iteration_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema") != "figure-agent.fig-loop-run.v1"
        or manifest.get("fixture") != name
        or not isinstance(iteration, dict)
    ):
        return None
    stop_reason = manifest.get("final_stop_reason") or iteration.get("stop_reason")
    if not isinstance(stop_reason, str) or not stop_reason:
        return None
    checkpoint = {
        "run_dir": str(run_dir),
        "manifest_path": str(manifest_path),
        "iteration_path": str(iteration_path),
        "final_stop_reason": stop_reason,
        "escalation_level": iteration.get("escalation_level"),
        "patch_handoff": iteration.get("patch_handoff"),
        "recommended_next_action": iteration.get("recommended_next_action"),
    }
    top_tier_summary = iteration.get("top_tier_audit_summary")
    if isinstance(top_tier_summary, dict):
        checkpoint["top_tier_audit_summary"] = top_tier_summary
    editorial_summary = iteration.get("editorial_art_direction_summary")
    if isinstance(editorial_summary, dict):
        checkpoint["editorial_art_direction_summary"] = editorial_summary
    svg_polish_readiness = iteration.get("svg_polish_readiness")
    if isinstance(svg_polish_readiness, dict):
        checkpoint["svg_polish_readiness"] = svg_polish_readiness
    crop_audit_summary = iteration.get("crop_audit_summary")
    if isinstance(crop_audit_summary, dict):
        checkpoint["crop_audit_summary"] = crop_audit_summary
    aesthetic_lever_summary = iteration.get("aesthetic_lever_summary")
    if isinstance(aesthetic_lever_summary, dict):
        checkpoint["aesthetic_lever_summary"] = aesthetic_lever_summary
    journal_playbook_summary = iteration.get("journal_art_direction_playbook_summary")
    if isinstance(journal_playbook_summary, dict):
        checkpoint["journal_art_direction_playbook_summary"] = journal_playbook_summary
    basin_summary = iteration.get("basin_summary")
    if isinstance(basin_summary, dict):
        checkpoint["basin_summary"] = basin_summary
    return checkpoint


def _loop_checkpoint_is_current(
    checkpoint: dict[str, Any],
    *,
    example_dir: Path,
    name: str,
) -> bool:
    manifest_path = Path(checkpoint["manifest_path"])
    iteration_path = Path(checkpoint["iteration_path"])
    try:
        checkpoint_mtime = max(manifest_path.stat().st_mtime, iteration_path.stat().st_mtime)
    except OSError:
        return False
    evidence_paths = (
        example_dir / "spec.yaml",
        example_dir / "briefing.md",
        example_dir / "authoring_plan.md",
        example_dir / "authoring_contract.md",
        example_dir / "subregion_iteration_log.md",
        example_dir / "theory_guard.md",
        example_dir / "QUALITY_AUDIT.md",
        example_dir / f"{name}.tex",
        example_dir / "critique.md",
        example_dir / "critique_adjudication.yaml",
        example_dir / "build" / f"{name}.pdf",
    )
    try:
        return all(
            not path.is_file() or path.stat().st_mtime <= checkpoint_mtime
            for path in evidence_paths
        )
    except OSError:
        return False


def latest_loop_checkpoint(
    repo_root: Path,
    name: str,
    example_dir: Path,
) -> dict[str, Any] | None:
    runs_root = repo_root / ".scratch" / "fig-loop-runs"
    if not runs_root.is_dir():
        return None
    checkpoints = [
        checkpoint
        for run_dir in runs_root.iterdir()
        if run_dir.is_dir()
        and (checkpoint := _read_loop_checkpoint(run_dir, name)) is not None
        and _loop_checkpoint_is_current(checkpoint, example_dir=example_dir, name=name)
    ]
    if not checkpoints:
        return None
    return max(
        checkpoints,
        key=lambda checkpoint: Path(checkpoint["manifest_path"]).stat().st_mtime,
    )
