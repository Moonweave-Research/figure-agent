from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_panel_model  # noqa: E402


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        """
name: candidate_demo
panels:
  - id: C
    caption: Energy diagram
    bbox_pdf_cm: [0.0, 0.0, 1.0, 1.0]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(
        "% Panel B\n"
        "\\draw (0,0) -- (1,0);\n"
        "% Panel C\n"
        "\\node at (0,0) {mobility edge};\n"
        "\\draw (0,1) -- (1,1);\n",
        encoding="utf-8",
    )
    return fixture


def test_panel_model_joins_intent_and_tex_selectors(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = candidate_panel_model.build_panel_model(
        "candidate_demo",
        "C",
        workspace_root=workspace,
    )

    assert payload["schema"] == "figure-agent.candidate-panel-model.v1"
    assert payload["fixture"] == "candidate_demo"
    assert payload["panel"]["id"] == "C"
    assert payload["panel"]["role"] == "Energy diagram"
    assert payload["panel"]["bbox_pdf_cm"] == [0.0, 0.0, 1.0, 1.0]
    assert payload["panel"]["coordinate_system"] == "pdf_cm_bottom_left"
    assert payload["selector_count"] == 2
    assert [item["panel"] for item in payload["selectors"]] == ["C", "C"]
    assert payload["visual_review"]["status"] == "missing_render"


def test_panel_model_missing_panel_returns_empty_model(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = candidate_panel_model.build_panel_model(
        "candidate_demo",
        "Z",
        workspace_root=workspace,
    )

    assert payload["panel"]["id"] == "Z"
    assert payload["panel"]["role"] == "unknown"
    assert payload["panel"]["bbox_pdf_cm"] == []
    assert payload["selectors"] == []
    assert payload["refusals"] == [{"code": "panel_not_declared"}]


def test_panel_model_rejects_unsafe_panel_id(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    with pytest.raises(candidate_panel_model.CandidatePanelModelError, match="invalid_panel_id"):
        candidate_panel_model.build_panel_model(
            "candidate_demo",
            "../C",
            workspace_root=workspace,
        )
