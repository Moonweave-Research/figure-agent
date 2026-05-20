from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_handoff import patch_handoff  # noqa: E402


def test_patch_handoff_returns_none_without_active_target() -> None:
    assert patch_handoff("loop_demo", {"active_patch_target": None}) is None


def test_patch_handoff_describes_single_finding_target() -> None:
    handoff = patch_handoff(
        "loop_demo",
        {
            "active_patch_target": {
                "finding_id": "C001",
                "patch_target": "Panel A label",
                "reason": "label is ambiguous",
            }
        },
    )

    assert handoff == {
        "target_type": "finding",
        "target_id": "C001",
        "patch_target": "Panel A label",
        "reason": "label is ambiguous",
        "allowed_edit_scope": [
            "examples/loop_demo/loop_demo.tex",
            "examples/loop_demo/authoring_plan.md",
            "examples/loop_demo/subregion_iteration_log.md",
        ],
        "forbidden_edit_scope": [
            "accepted",
            "golden_contract",
            "examples/loop_demo/exports/",
            "examples/loop_demo/build/",
            "examples/loop_demo/critique.md",
            "unrelated examples",
            "broad refactors",
            "multiple findings in one patch",
        ],
        "required_closeout_checks": [
            "/fig_compile loop_demo",
            "/fig_critique loop_demo when critique freshness requires it",
            "update or recreate examples/loop_demo/critique_adjudication.yaml",
            "preserve unresolved findings",
            "/fig_loop loop_demo --goal <same goal or next goal>",
        ],
        "unresolved_findings_requirement": (
            "Do not delete, rewrite, or hide unresolved critique findings; record only the"
            " selected target decision in critique_adjudication.yaml."
        ),
    }


def test_patch_handoff_describes_single_subregion_target() -> None:
    handoff = patch_handoff(
        "loop_demo",
        {
            "active_patch_target": {
                "finding_id": None,
                "patch_target": "D-2",
                "reason": "active subregion remains open",
            }
        },
    )

    assert handoff is not None
    assert handoff["target_type"] == "subregion"
    assert handoff["target_id"] == "D-2"
    assert handoff["patch_target"] == "D-2"
