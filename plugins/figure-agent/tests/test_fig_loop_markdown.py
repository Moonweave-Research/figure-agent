from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_markdown import decision_markdown  # noqa: E402


def test_decision_markdown_records_active_finding_and_handoff() -> None:
    markdown = decision_markdown(
        name="loop_demo",
        goal="inspect label",
        status_result={
            "stage": 3,
            "render_state": "FRESH",
            "critique_state": "FRESH",
            "export_state": "STALE",
            "notes": ["note-a", "note-b"],
            "final_artifact_kind": "polished_svg",
            "final_artifact_state": "STALE",
            "final_artifact_path": "polish/demo.svg",
        },
        adjudication={"state": "fresh"},
        loop_decision={
            "stop_reason": "patch_target_recommended",
            "active_patch_target": {
                "finding_id": "C001",
                "patch_target": "panel A label cluster",
            },
            "recommended_next_action": "patch C001: panel A label cluster",
        },
        escalation={"escalation_level": "patch_allowed"},
        patch_handoff={"target_type": "finding", "target_id": "C001"},
    )

    assert "# Fig Loop Decision: loop_demo" in markdown
    assert "- mode: verify-only" in markdown
    assert "- active_patch_target: C001 -> panel A label cluster" in markdown
    assert "- patch_handoff_target: finding C001" in markdown
    assert "- notes: note-a, note-b" in markdown
    assert "- final_artifact_state: polished_svg STALE polish/demo.svg" in markdown
    assert markdown.endswith("\n")


def test_decision_markdown_records_none_defaults() -> None:
    markdown = decision_markdown(
        name="loop_demo",
        goal="inspect complete",
        status_result={
            "stage": 4,
            "render_state": "FRESH",
            "critique_state": "NOT_REQUIRED",
            "export_state": "FRESH",
        },
        adjudication={"state": "missing"},
        loop_decision={
            "stop_reason": "verify_only_complete",
            "active_patch_target": None,
            "recommended_next_action": "inspect figure state",
        },
        escalation={"escalation_level": "none"},
        patch_handoff=None,
    )

    assert "- active_patch_target: (none)" in markdown
    assert "- patch_handoff_target: (none)" in markdown
    assert "- notes: (none)" in markdown
    assert "- final_artifact_state: generated_export NONE " in markdown
