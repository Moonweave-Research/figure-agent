"""Read and write fig_loop run records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def json_stdout_summary(run_dir: Path) -> dict[str, Any]:
    manifest_path = run_dir / "run_manifest.json"
    iteration_path = run_dir / "iteration_001.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    iteration = json.loads(iteration_path.read_text(encoding="utf-8"))
    summary = {
        "run_dir": manifest["run_dir"],
        "manifest_path": str(manifest_path),
        "iteration_path": str(iteration_path),
        "final_stop_reason": manifest["final_stop_reason"],
        "escalation_level": iteration["escalation_level"],
        "patch_handoff_present": iteration.get("patch_handoff") is not None,
        "auto_patch_eligibility": iteration.get("auto_patch_eligibility"),
        "patch_evidence_present": iteration.get("patch_evidence") is not None,
        "post_patch_evidence_verdict": (
            (iteration.get("post_patch_evidence") or {}).get("verdict")
        ),
        "final_artifact_state": (iteration.get("status") or {}).get("final_artifact_state"),
        "final_artifact_kind": (iteration.get("status") or {}).get("final_artifact_kind"),
        "final_artifact_path": (iteration.get("status") or {}).get("final_artifact_path"),
        "journal_grade_assessment": iteration.get("journal_grade_assessment"),
        "top_tier_audit_summary": iteration.get("top_tier_audit_summary"),
        "editorial_art_direction_summary": iteration.get(
            "editorial_art_direction_summary"
        ),
        "crop_audit_summary": iteration.get("crop_audit_summary"),
        "aesthetic_lever_summary": iteration.get("aesthetic_lever_summary"),
        "journal_art_direction_playbook_summary": iteration.get(
            "journal_art_direction_playbook_summary"
        ),
        "recommended_next_action": iteration.get("recommended_next_action"),
    }
    svg_polish_readiness = iteration.get("svg_polish_readiness")
    if svg_polish_readiness is not None:
        summary["svg_polish_readiness"] = svg_polish_readiness
    audit_evidence = iteration.get("audit_evidence")
    if audit_evidence is not None:
        summary["audit_evidence"] = audit_evidence
    return summary
