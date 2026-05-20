from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_patch_evidence import (  # noqa: E402
    PATCH_EVIDENCE_SCHEMA,
    PATCH_EVIDENCE_VERDICTS,
    patch_evidence_baseline,
    path_evidence,
)
from quality_manifest import file_sha256  # noqa: E402


def test_path_evidence_records_missing_file(tmp_path: Path) -> None:
    assert path_evidence(tmp_path, "examples/missing.tex") == {
        "path": "examples/missing.tex",
        "exists": False,
        "sha256": None,
    }


def test_path_evidence_records_existing_file_hash(tmp_path: Path) -> None:
    source = tmp_path / "examples" / "loop_demo" / "loop_demo.tex"
    source.parent.mkdir(parents=True)
    source.write_text("source", encoding="utf-8")

    assert path_evidence(tmp_path, "examples/loop_demo/loop_demo.tex") == {
        "path": "examples/loop_demo/loop_demo.tex",
        "exists": True,
        "sha256": file_sha256(source),
    }


def test_patch_evidence_baseline_returns_none_without_patch_handoff(tmp_path: Path) -> None:
    assert patch_evidence_baseline(tmp_path, None, git_commit=lambda: "abc") is None


def test_patch_evidence_baseline_records_allowed_scope_and_rollback(tmp_path: Path) -> None:
    tex = tmp_path / "examples" / "loop_demo" / "loop_demo.tex"
    tex.parent.mkdir(parents=True)
    tex.write_text("source", encoding="utf-8")
    patch_handoff = {
        "target_type": "finding",
        "target_id": "C001",
        "allowed_edit_scope": [
            "examples/loop_demo/loop_demo.tex",
            "examples/loop_demo/authoring_plan.md",
        ],
    }

    assert patch_evidence_baseline(tmp_path, patch_handoff, git_commit=lambda: "abc123") == {
        "schema": PATCH_EVIDENCE_SCHEMA,
        "phase": "pre_patch",
        "target_type": "finding",
        "target_id": "C001",
        "verdict": "not_evaluated",
        "may_edit": False,
        "pre_patch": {
            "allowed_edit_scope": [
                {
                    "path": "examples/loop_demo/loop_demo.tex",
                    "exists": True,
                    "sha256": file_sha256(tex),
                },
                {
                    "path": "examples/loop_demo/authoring_plan.md",
                    "exists": False,
                    "sha256": None,
                },
            ]
        },
        "post_patch_required_verdicts": list(PATCH_EVIDENCE_VERDICTS),
        "rollback_reference": {
            "git_commit": "abc123",
            "restore_strategy": (
                "restore allowed_edit_scope paths to the recorded pre_patch sha256 values"
            ),
        },
    }
