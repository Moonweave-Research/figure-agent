from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_records import json_stdout_summary, write_json  # noqa: E402


def test_write_json_serializes_paths_and_tuples(tmp_path: Path) -> None:
    path = tmp_path / "record.json"

    write_json(
        path,
        {
            "artifact_path": tmp_path / "artifact.svg",
            "command": ("uv", "run", "pytest"),
        },
    )

    assert path.read_text(encoding="utf-8").endswith("\n")
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "artifact_path": str(tmp_path / "artifact.svg"),
        "command": ["uv", "run", "pytest"],
    }


def test_json_stdout_summary_reads_manifest_and_iteration_contract(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "loop_demo"
    run_dir.mkdir(parents=True)
    write_json(
        run_dir / "run_manifest.json",
        {
            "run_dir": str(run_dir),
            "final_stop_reason": "status_action_required",
        },
    )
    write_json(
        run_dir / "iteration_001.json",
        {
            "escalation_level": "agent_action_required",
            "patch_handoff": {"target_id": "C001"},
            "auto_patch_eligibility": {"may_auto_patch": False},
            "patch_evidence": None,
            "post_patch_evidence": {"verdict": "needs_human_review"},
            "status": {
                "final_artifact_state": "STALE",
                "final_artifact_kind": "polished_svg",
                "final_artifact_path": "examples/loop_demo/final.svg",
            },
            "top_tier_audit_summary": {"evaluation_state": "passed"},
            "editorial_art_direction_summary": {
                "polish_recommended_path": "ready_for_svg_polish"
            },
            "recommended_next_action": "inspect figure state",
        },
    )

    assert json_stdout_summary(run_dir) == {
        "run_dir": str(run_dir),
        "manifest_path": str(run_dir / "run_manifest.json"),
        "iteration_path": str(run_dir / "iteration_001.json"),
        "final_stop_reason": "status_action_required",
        "escalation_level": "agent_action_required",
        "patch_handoff_present": True,
        "auto_patch_eligibility": {"may_auto_patch": False},
        "patch_evidence_present": False,
        "post_patch_evidence_verdict": "needs_human_review",
        "final_artifact_state": "STALE",
        "final_artifact_kind": "polished_svg",
        "final_artifact_path": "examples/loop_demo/final.svg",
        "top_tier_audit_summary": {"evaluation_state": "passed"},
        "editorial_art_direction_summary": {
            "polish_recommended_path": "ready_for_svg_polish"
        },
        "recommended_next_action": "inspect figure state",
    }
