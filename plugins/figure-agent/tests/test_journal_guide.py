from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import journal_guide  # noqa: E402


def _fixture(root: Path, *, spec: dict[str, object] | None = None) -> Path:
    fixture = root / "examples" / "demo"
    fixture.mkdir(parents=True)
    (fixture / "demo.tex").write_text("% source\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        yaml.safe_dump(spec or {"figure_type": "mechanism_schematic"}),
        encoding="utf-8",
    )
    return fixture


def test_build_journal_guide_uses_explicit_defaults_without_optional_guides(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)

    guide = journal_guide.build_journal_guide(
        "demo",
        workspace_root=tmp_path,
        plugin_root=tmp_path,
    )

    assert guide["schema"] == "figure-agent.journal-guide.v1"
    assert guide["target_journal"] == "unknown"
    assert guide["hard_constraints"]["editable_required"] is True
    assert set(guide["hard_constraints"]["output_formats"]) == {"pdf", "png", "svg"}
    assert guide["sources"] == ["default_kernel_constraints", "spec.yaml"]
    assert guide["invented_external_journal_rules"] is False


def test_build_journal_guide_reads_spec_and_aesthetic_intent_target_journal(
    tmp_path: Path,
) -> None:
    fixture = _fixture(
        tmp_path,
        spec={
            "target_journal": "Nature Materials",
            "journal_constraints": {
                "output_formats": ["pdf", "svg", "tiff"],
                "font_size_min_pt": 6.0,
                "line_width_range_pt": [0.25, 1.2],
                "color_mode": "rgb",
                "colorblind_safe_required": True,
            },
        },
    )
    (fixture / "aesthetic_intent.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.aesthetic-intent.v1",
                "fixture": "demo",
                "target_journal": "Nature Materials",
                "visual_maturity": "polished",
                "density": "balanced",
                "reference_style": "mechanism_schematic",
                "design_principles": [{"id": "p1", "instruction": "restrained"}],
                "must_avoid": [{"id": "m1", "pattern": "marketing", "severity": "MAJOR"}],
                "polish_triggers": [
                    {
                        "id": "t1",
                        "condition": "labels cramped",
                        "recommended_path": "continue_tikz",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    guide = journal_guide.build_journal_guide(
        "demo",
        workspace_root=tmp_path,
        plugin_root=tmp_path,
    )

    assert guide["target_journal"] == "Nature Materials"
    assert guide["hard_constraints"]["output_formats"] == ["pdf", "svg", "tiff"]
    assert guide["hard_constraints"]["font_size_min_pt"] == 6.0
    assert guide["hard_constraints"]["colorblind_safe_required"] is True
    assert "aesthetic_intent.yaml" in guide["sources"]


def test_build_journal_guide_fails_closed_on_malformed_spec(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("not: [valid\n", encoding="utf-8")

    with pytest.raises(journal_guide.JournalGuideError, match="spec_unreadable"):
        journal_guide.build_journal_guide(
            "demo",
            workspace_root=tmp_path,
            plugin_root=tmp_path,
        )


def test_build_journal_guide_refuses_playbook_path_escape(tmp_path: Path) -> None:
    _fixture(tmp_path, spec={"journal_art_direction_playbook": "../escape"})

    with pytest.raises(journal_guide.JournalGuideError, match="playbook_path_escape"):
        journal_guide.build_journal_guide(
            "demo",
            workspace_root=tmp_path,
            plugin_root=tmp_path,
        )


def test_evaluate_journal_constraints_reports_structured_violations(
    tmp_path: Path,
) -> None:
    _fixture(
        tmp_path,
        spec={"journal_constraints": {"output_formats": ["pdf", "svg", "png"]}},
    )
    guide = journal_guide.build_journal_guide(
        "demo",
        workspace_root=tmp_path,
        plugin_root=tmp_path,
    )

    result = journal_guide.evaluate_journal_constraints(
        guide,
        outputs={"editable": "", "pdf": "build/demo.pdf"},
    )

    assert result["passed"] is False
    assert [item["id"] for item in result["violations"]] == [
        "editable_output_missing",
        "required_output_format_missing:png",
        "required_output_format_missing:svg",
    ]
