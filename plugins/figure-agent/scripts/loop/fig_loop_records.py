"""Read and write fig_loop run records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quality_manifest import file_sha256

# Manifest fields naming the artifacts the iteration actually read, so a
# consumer can bind the record to a render instead of trusting its mtime.
RENDER_PDF_HASH_FIELD = "render_pdf_sha256"
SOURCE_TEX_HASH_FIELD = "source_tex_sha256"


def run_input_hashes(example_dir: Path, name: str) -> dict[str, str | None]:
    """Content hashes of the render and source a loop iteration ran against.

    A run record used to name only the fixture, so two hand-written JSON files
    with a fresh mtime were indistinguishable from a real run and the closeout
    loop_rerun gate could not tell which render the record described."""
    render_pdf = example_dir / "build" / f"{name}.pdf"
    source_tex = example_dir / f"{name}.tex"
    return {
        RENDER_PDF_HASH_FIELD: file_sha256(render_pdf) if render_pdf.is_file() else None,
        SOURCE_TEX_HASH_FIELD: file_sha256(source_tex) if source_tex.is_file() else None,
    }


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
        "editorial_art_direction_summary": iteration.get("editorial_art_direction_summary"),
        "crop_audit_summary": iteration.get("crop_audit_summary"),
        "aesthetic_lever_summary": iteration.get("aesthetic_lever_summary"),
        "journal_art_direction_playbook_summary": iteration.get(
            "journal_art_direction_playbook_summary"
        ),
        "external_vision_review_summary": iteration.get("external_vision_review_summary"),
        "recommended_next_action": iteration.get("recommended_next_action"),
    }
    reference_aesthetic_metrics_summary = iteration.get("reference_aesthetic_metrics_summary")
    if reference_aesthetic_metrics_summary is not None:
        summary["reference_aesthetic_metrics_summary"] = reference_aesthetic_metrics_summary
    next_action_summary = iteration.get("next_action_summary")
    if next_action_summary is not None:
        summary["next_action_summary"] = next_action_summary
    svg_polish_readiness = iteration.get("svg_polish_readiness")
    if svg_polish_readiness is not None:
        summary["svg_polish_readiness"] = svg_polish_readiness
    svg_polish_gate = iteration.get("svg_polish_gate")
    if svg_polish_gate is not None:
        summary["svg_polish_gate"] = svg_polish_gate
    audit_evidence = iteration.get("audit_evidence")
    if audit_evidence is not None:
        summary["audit_evidence"] = audit_evidence
    basin = iteration.get("basin_summary")
    if basin is not None:
        summary["basin_summary"] = basin
    return summary
