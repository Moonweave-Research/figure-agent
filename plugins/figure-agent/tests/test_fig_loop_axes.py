from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_axes import axis_verdicts, quality_axes_frontmatter  # noqa: E402


def _write_critique(path: Path, frontmatter: dict[str, object]) -> None:
    path.write_text(
        "---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n\n# Critique\n",
        encoding="utf-8",
    )


def test_quality_axes_frontmatter_requires_fresh_supported_critique(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.2",
            "quality_axes": {"reference_fidelity": {"verdict": "pass"}},
        },
    )

    assert quality_axes_frontmatter(example_dir, "STALE") is None
    assert quality_axes_frontmatter(example_dir, "FRESH") == {
        "reference_fidelity": {"verdict": "pass"}
    }


def test_axis_verdicts_reference_missing_blocks_reference_fidelity(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    records = axis_verdicts(
        {
            "notes": ["reference_image_missing"],
            "render_state": "FRESH",
            "critique_state": "REFERENCE_MISSING",
            "export_state": "MISSING",
            "acceptance_state": "NOT_DECLARED",
        },
        {"state": "missing", "decisions": []},
        {
            "stop_reason": "reference_input_missing",
            "human_gate_status": "not_requested",
        },
        example_dir,
    )

    assert records["reference_fidelity"]["verdict"] == "blocked"
    assert records["reference_fidelity"]["evaluation_state"] == "blocked"
    assert records["critique"]["evaluation_state"] == "blocked"


def test_axis_verdicts_prefers_quality_axes_when_available(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    critique = example_dir / "critique.md"
    _write_critique(
        critique,
        {
            "schema": "figure-agent.critique.v1.2",
            "quality_axes": {
                "publication_readiness": {
                    "verdict": "needs_human",
                    "recommended_action": "review final approval",
                    "blocking_items": ["accepted gate unresolved"],
                }
            },
        },
    )

    records = axis_verdicts(
        {
            "notes": [],
            "render_state": "FRESH",
            "critique_state": "FRESH",
            "export_state": "FRESH",
            "acceptance_state": "NOT_ACCEPTED",
        },
        {"state": "fresh", "decisions": []},
        {
            "stop_reason": "verify_only_complete",
            "human_gate_status": "not_requested",
        },
        example_dir,
    )

    assert records["publication_safety"]["source"] == "critique.quality_axes"
    assert records["publication_safety"]["evidence_path"] == str(critique)
    assert records["publication_safety"]["evaluation_state"] == "blocked"
    assert records["publication_safety"]["quality_axis_recommended_actions"] == {
        "publication_readiness": "review final approval"
    }


def test_axis_verdicts_human_gate_overrides_publication_quality_axis(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.2",
            "quality_axes": {"publication_readiness": {"verdict": "pass"}},
        },
    )

    records = axis_verdicts(
        {
            "notes": [],
            "render_state": "FRESH",
            "critique_state": "FRESH",
            "export_state": "FRESH",
            "acceptance_state": "ACCEPTED",
        },
        {"state": "fresh", "decisions": [{"finding_id": "C001", "decision": "needs_human"}]},
        {
            "stop_reason": "human_gate_required",
            "human_gate_status": "required",
        },
        example_dir,
    )

    assert records["publication_safety"]["source"] == "status.acceptance_state"
    assert records["publication_safety"]["verdict"] == "human_gate"
    assert records["publication_safety"]["evaluation_state"] == "blocked"
