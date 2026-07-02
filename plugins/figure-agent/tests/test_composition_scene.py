from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.quarantine

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"
FIG3_OBJECTS = {
    "carrier_walk",
    "current_sparkline",
    "bridge_text",
    "distribution_curves",
    "n_breadth",
    "rho60s",
}


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _run(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), "python", str(FIG_AGENT), *args],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )


def _fig3_fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "fig3_resistance_mechanism"
    fixture.mkdir(parents=True)
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        """
name: fig3_resistance_mechanism
panels:
  - id: A
  - id: B
composition_model:
  panels:
    A:
      objects:
        carrier_walk:
          kind: path
          truth_bearing: true
          semantic_claim: tortuous carrier walk
          invariant: carrier_sign_agnostic
          allowed_creative_ops:
            - reshape_path
        current_sparkline:
          kind: inset_plot
          truth_bearing: true
          anchor_target: carrier_walk
        bridge_text:
          kind: annotation
          truth_bearing: false
    B:
      objects:
        distribution_curves:
          kind: distribution
          truth_bearing: true
        n_breadth:
          kind: measurement_span
          truth_bearing: true
        rho60s:
          kind: text_label
          truth_bearing: true
""".lstrip(),
        encoding="utf-8",
    )
    (fixture / "fig3_resistance_mechanism.tex").write_text(
        "\n".join(
            [
                "% fig-agent:start object=carrier_walk panel=A kind=path truth_bearing=true",
                "walk",
                "% fig-agent:end object=carrier_walk",
                "% fig-agent:start object=current_sparkline "
                "panel=A kind=inset_plot truth_bearing=true",
                "spark",
                "% fig-agent:end object=current_sparkline",
                "% fig-agent:start object=bridge_text panel=A kind=annotation truth_bearing=false",
                "bridge",
                "% fig-agent:end object=bridge_text",
                "% fig-agent:start object=distribution_curves "
                "panel=B kind=distribution truth_bearing=true",
                "curves",
                "% fig-agent:end object=distribution_curves",
                "% fig-agent:start object=n_breadth "
                "panel=B kind=measurement_span truth_bearing=true",
                "n span",
                "% fig-agent:end object=n_breadth",
                "% fig-agent:start object=rho60s panel=B kind=text_label truth_bearing=true",
                "rho label",
                "% fig-agent:end object=rho60s",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return workspace, fixture


def test_scene_model_builds_fig3_required_semantic_objects_from_tmp_fixture(
    tmp_path: Path,
) -> None:
    import composition_scene

    workspace, fixture = _fig3_fixture(tmp_path)

    scene = composition_scene.build_semantic_scene_model(
        "fig3_resistance_mechanism",
        workspace_root=workspace,
    )

    assert scene["schema"] == "figure-agent.semantic-scene-model.v1"
    assert scene["status"] == "ready"
    assert set(scene["objects"]) == FIG3_OBJECTS
    assert {panel["id"] for panel in scene["panels"]} == {"A", "B"}
    for object_id in FIG3_OBJECTS:
        selector = scene["source_selectors"][object_id]
        assert selector["kind"] == "semantic_block"
        assert selector["object_id"] == object_id
    assert not (fixture / "build").exists()
    assert not (fixture / "exports").exists()


def test_scene_model_merges_explicit_annotations_without_inventing_invariants(
    tmp_path: Path,
) -> None:
    import composition_scene

    workspace, _fixture = _fig3_fixture(tmp_path)

    scene = composition_scene.build_semantic_scene_model(
        "fig3_resistance_mechanism",
        workspace_root=workspace,
    )

    carrier = scene["objects"]["carrier_walk"]
    bridge = scene["objects"]["bridge_text"]
    assert carrier["kind"] == "path"
    assert carrier["truth_bearing"] is True
    assert carrier["semantic_claim"] == "tortuous carrier walk"
    assert carrier["allowed_creative_ops"] == ["reshape_path"]
    assert bridge["truth_bearing"] is False
    assert scene["invariant_coverage"]["carrier_walk"]["status"] == "covered"
    assert scene["invariant_coverage"]["bridge_text"]["status"] == "not_truth_bearing"
    assert scene["invariant_coverage"]["rho60s"]["status"] == "missing_explicit_invariant"


def test_scene_model_blocks_ambiguous_duplicate_semantic_blocks(tmp_path: Path) -> None:
    import composition_scene

    workspace, fixture = _fig3_fixture(tmp_path)
    tex = fixture / "fig3_resistance_mechanism.tex"
    tex.write_text(
        tex.read_text(encoding="utf-8")
        + "% fig-agent:start object=carrier_walk panel=A\nagain\n"
        + "% fig-agent:end object=carrier_walk\n",
        encoding="utf-8",
    )

    scene = composition_scene.build_semantic_scene_model(
        "fig3_resistance_mechanism",
        workspace_root=workspace,
    )

    assert scene["status"] == "blocked"
    assert scene["diagnostics"][0]["code"] == "semantic_block_duplicate"


def test_scene_model_accepts_indented_semantic_blocks_inside_tex_scopes(
    tmp_path: Path,
) -> None:
    import composition_scene

    workspace, fixture = _fig3_fixture(tmp_path)
    tex = fixture / "fig3_resistance_mechanism.tex"
    tex.write_text(
        "  % fig-agent:start object=n_breadth panel=B kind=measurement_span\n"
        "  span\n"
        "  % fig-agent:end object=n_breadth\n",
        encoding="utf-8",
    )

    scene = composition_scene.build_semantic_scene_model(
        "fig3_resistance_mechanism",
        workspace_root=workspace,
    )

    assert scene["status"] == "ready"
    assert scene["source_selectors"]["n_breadth"]["object_id"] == "n_breadth"


def test_fig_agent_analyze_composition_outputs_scene_model_without_mutating_fixture(
    tmp_path: Path,
) -> None:
    workspace, fixture = _fig3_fixture(tmp_path)

    result = _run(
        workspace,
        "analyze-composition",
        "fig3_resistance_mechanism",
        "--json",
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0, result.stderr
    assert payload["schema"] == "figure-agent.semantic-scene-model.v1"
    assert set(payload["objects"]) == FIG3_OBJECTS
    assert not (fixture / "build").exists()
    assert not (fixture / "exports").exists()
