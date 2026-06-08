from __future__ import annotations

import sys
from pathlib import Path

import pytest

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


def test_intent_model_keeps_blocked_state_with_mixed_references(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "spec.yaml").write_text(
        """
name: intent_demo
panels:
  - id: A
    reference_image: ../outside.png
  - id: B
    reference_image: reference/panel_a.png
""".strip()
        + "\n",
        encoding="utf-8",
    )

    payload = figure_intent_model.build_intent_model(
        "intent_demo",
        workspace_root=workspace,
        plugin_root=Path("plugins/figure-agent").resolve(),
    )

    assert payload["inputs"]["panel_references"]["state"] == "blocked"
    assert "path_escape" in payload["inputs"]["panel_references"]["reasons"]


def test_intent_model_keeps_present_state_with_optional_missing_reference(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "spec.yaml").write_text(
        """
name: intent_demo
panels:
  - id: A
    reference_image: reference/panel_a.png
  - id: B
""".strip()
        + "\n",
        encoding="utf-8",
    )

    payload = figure_intent_model.build_intent_model(
        "intent_demo",
        workspace_root=workspace,
        plugin_root=Path("plugins/figure-agent").resolve(),
    )

    assert payload["inputs"]["panel_references"]["state"] == "present"
    assert "missing" in payload["inputs"]["panel_references"]["reasons"]


def test_intent_model_inherits_figure_reference_for_panels(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "spec.yaml").write_text(
        """
name: intent_demo
reference_image: reference/panel_a.png
panels:
  - id: A
    caption: Kinetic panel
""".strip()
        + "\n",
        encoding="utf-8",
    )

    payload = figure_intent_model.build_intent_model(
        "intent_demo",
        workspace_root=workspace,
        plugin_root=Path("plugins/figure-agent").resolve(),
    )

    assert payload["inputs"]["figure_reference"]["state"] == "present"
    assert payload["inputs"]["panel_references"]["state"] == "present"
    assert payload["panels"][0]["apply_authority_floor"] == "apply_eligible"


def test_intent_model_does_not_treat_plugin_root_cwd_as_workspace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(plugin_root)

    with pytest.raises(figure_intent_model.IntentModelError, match="workspace_missing"):
        figure_intent_model.build_intent_model("smoke_trap_demo", plugin_root=plugin_root)


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
