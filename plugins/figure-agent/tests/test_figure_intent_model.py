from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import figure_intent_model  # noqa: E402


def _fixture(workspace: Path, name: str = "intent_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        """
name: intent_demo
panels:
  - id: A
    caption: Kinetic panel
    bbox_pdf_cm: [0.0, 0.0, 4.0, 3.0]
    reference_image: reference/panel_a.png
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "intent_demo.tex").write_text("% source\n", encoding="utf-8")
    (fixture / "reference").mkdir()
    (fixture / "reference" / "panel_a.png").write_bytes(b"fake")
    return fixture


def test_intent_model_reads_fixture_local_inputs(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = figure_intent_model.build_intent_model(
        "intent_demo",
        workspace_root=workspace,
        plugin_root=Path("plugins/figure-agent").resolve(),
    )

    assert payload["schema"] == "figure-agent.intent-model.v1"
    assert payload["fixture"] == "intent_demo"
    assert payload["panels"][0]["id"] == "A"
    assert payload["panels"][0]["role"] == "Kinetic panel"
    assert payload["panels"][0]["apply_authority_floor"] == "apply_eligible"
    assert payload["inputs"]["panel_references"]["state"] == "present"


def test_intent_model_rejects_reference_path_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "spec.yaml").write_text(
        """
name: intent_demo
panels:
  - id: A
    reference_image: ../outside.png
""".strip()
        + "\n",
        encoding="utf-8",
    )

    payload = figure_intent_model.build_intent_model(
        "intent_demo",
        workspace_root=workspace,
        plugin_root=Path("plugins/figure-agent").resolve(),
    )

    assert payload["panels"][0]["apply_authority_floor"] == "review_only"
    assert payload["inputs"]["panel_references"]["state"] == "blocked"
    assert "path_escape" in payload["inputs"]["panel_references"]["reasons"]


def test_intent_model_missing_caption_does_not_invent_claims(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = figure_intent_model.build_intent_model(
        "intent_demo",
        workspace_root=workspace,
        plugin_root=Path("plugins/figure-agent").resolve(),
    )

    assert payload["inputs"]["caption"]["state"] == "missing_optional"
    assert payload["panels"][0]["semantic_claims"] == []
