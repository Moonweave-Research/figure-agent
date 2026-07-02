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


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
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
          invariant: carrier_sign_agnostic
        current_sparkline:
          kind: inset_plot
          truth_bearing: true
          anchor_target: carrier_walk
    B:
      objects:
        n_breadth:
          kind: measurement_span
          truth_bearing: true
          invariant: distribution_breadth_not_density
""".lstrip(),
        encoding="utf-8",
    )
    source = fixture / "fig3_resistance_mechanism.tex"
    source.write_text(
        "\n".join(
            [
                "% fig-agent:start object=carrier_walk panel=A kind=path truth_bearing=true",
                r"\draw[walk] (0,0) -- (1,1) -- (2,0);",
                "% fig-agent:end object=carrier_walk",
                "% fig-agent:start object=current_sparkline "
                "panel=A kind=inset_plot truth_bearing=true",
                r"\draw (0,0) -- (1,0) node[right] {$t$};",
                "% fig-agent:end object=current_sparkline",
                "% fig-agent:start object=n_breadth "
                "panel=B kind=measurement_span truth_bearing=true",
                r"\draw[<->] (1,1) -- (3,1) node[midway] {$n$};",
                "% fig-agent:end object=n_breadth",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return workspace, fixture, source


def test_generate_fig3_structural_families_returns_renderable_review_candidates(
    tmp_path: Path,
) -> None:
    import composition_contracts
    import composition_families

    workspace, fixture, _source = _fixture(tmp_path)

    candidate_set = composition_families.generate_structural_family_candidates(
        "fig3_resistance_mechanism",
        workspace_root=workspace,
    )

    assert candidate_set["schema"] == "figure-agent.composition-candidate-set.v1"
    assert candidate_set["fixture"] == "fig3_resistance_mechanism"
    assert candidate_set["authority"] == "creative_review_only"
    assert candidate_set["generation_policy"] == {
        "mode": "host_deterministic_family_templates",
        "model_calls_allowed": False,
        "tex_execution_allowed": False,
        "source_mutation_allowed": False,
    }
    candidates = candidate_set["candidates"]
    assert len(candidates) >= 6
    assert {candidate["family"] for candidate in candidates} == {
        "arrow_clutter_reduction",
        "carrier_walk_morphology",
        "sparkline_anchor",
    }
    assert sum(candidate["edit_class"] == "structural" for candidate in candidates) >= 3
    assert not (fixture / "build").exists()
    assert not (fixture / "exports").exists()

    for candidate in candidates:
        assert candidate["apply_authority"] == "human_required"
        assert candidate["proposal_source"] == "host_deterministic_template"
        assert candidate["composition_lint_delta"]["deterministic"]
        assert "model_payload" not in candidate
        assert "executable_payload" not in candidate
        assert len(candidate["operations"]) == 1
        operation = candidate["operations"][0]
        assert operation["kind"] == "replace_semantic_block"
        assert operation["path"] == (
            "examples/fig3_resistance_mechanism/fig3_resistance_mechanism.tex"
        )
        assert operation["selector"]["kind"] == "semantic_block"
        assert operation["selector"]["object_id"] in {
            "carrier_walk",
            "current_sparkline",
            "n_breadth",
        }
        assert operation["replacement_text_hash"].startswith("sha256:")
        assert operation["rollback"]["kind"] == "restore_original_text"
        assert (
            composition_contracts.validate_candidate_operation(
                operation,
                workspace_root=workspace,
            )["status"]
            == "valid"
        )


def test_arrow_clutter_family_offers_under_axis_breadth_bracket(
    tmp_path: Path,
) -> None:
    import composition_families

    workspace, _fixture_dir, _source = _fixture(tmp_path)

    candidate_set = composition_families.generate_structural_family_candidates(
        "fig3_resistance_mechanism",
        workspace_root=workspace,
    )

    candidates = {
        candidate["variant"]: candidate
        for candidate in candidate_set["candidates"]
        if candidate["family"] == "arrow_clutter_reduction"
    }
    candidate = candidates["under_axis_breadth_bracket"]
    replacement = candidate["operations"][0]["replacement_text"]
    assert "(1.2,-0.25)" in replacement
    assert "at (2.5,-0.55)" in replacement
    assert "$n$ = breadth" in replacement
    assert "tracks distribution breadth" not in replacement


def test_fig_agent_compose_generate_families_outputs_candidate_set(
    tmp_path: Path,
) -> None:
    workspace, fixture, _source = _fixture(tmp_path)

    result = _run(
        workspace,
        "compose-generate-families",
        "fig3_resistance_mechanism",
        "--output",
        "build/candidates/composition_candidate_set.json",
        "--json",
    )

    payload = json.loads(result.stdout)
    output = fixture / "build" / "candidates" / "composition_candidate_set.json"
    assert result.returncode == 0, result.stderr
    assert payload["schema"] == "figure-agent.composition-candidate-set.v1"
    assert len(payload["candidates"]) >= 6
    assert json.loads(output.read_text(encoding="utf-8")) == payload
    assert not (fixture / "exports").exists()


def test_generated_structural_families_can_prepare_all_candidates_without_tex(
    tmp_path: Path,
) -> None:
    import composition_families
    import composition_render

    workspace, fixture, _source = _fixture(tmp_path)
    candidate_set = composition_families.generate_structural_family_candidates(
        "fig3_resistance_mechanism",
        workspace_root=workspace,
    )

    result = composition_render.prepare_composition_render(
        "fig3_resistance_mechanism",
        candidate_set=candidate_set,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/composition_candidate_set.json"),
    )

    assert result["status"] == "prepared"
    assert len(result["rendered"]) == len(candidate_set["candidates"])
    for rendered in result["rendered"]:
        manifest = fixture / rendered["render_manifest"]
        source_copy = manifest.parent / "source" / "candidate.tex"
        assert manifest.is_file()
        assert source_copy.is_file()
    assert not (fixture / "exports").exists()


def test_fig_agent_rank_and_review_can_write_selection_artifacts(
    tmp_path: Path,
) -> None:
    workspace, fixture, _source = _fixture(tmp_path)
    generate = _run(
        workspace,
        "compose-generate-families",
        "fig3_resistance_mechanism",
        "--output",
        "build/candidates/composition_candidate_set.json",
        "--json",
    )
    render = _run(
        workspace,
        "compose-render",
        "fig3_resistance_mechanism",
        "--candidate-set",
        "build/candidates/composition_candidate_set.json",
        "--json",
    )
    assert generate.returncode == 0, generate.stderr
    assert render.returncode == 0, render.stderr

    rank = _run(
        workspace,
        "compose-rank",
        "fig3_resistance_mechanism",
        "--candidate-set",
        "build/candidates/composition_candidate_set.json",
        "--output",
        "build/candidates/composition_rank_result.json",
        "--json",
    )
    review = _run(
        workspace,
        "compose-review",
        "fig3_resistance_mechanism",
        "--candidate-set",
        "build/candidates/composition_candidate_set.json",
        "--candidate-id",
        "CFAM006",
        "--output",
        "build/candidates/CFAM006/composition_review_packet.json",
        "--json",
    )

    rank_path = fixture / "build" / "candidates" / "composition_rank_result.json"
    review_path = fixture / "build" / "candidates" / "CFAM006" / "composition_review_packet.json"
    assert rank.returncode == 0, rank.stderr
    assert review.returncode == 0, review.stderr
    assert json.loads(rank_path.read_text(encoding="utf-8"))["status"] == "ranked"
    assert json.loads(review_path.read_text(encoding="utf-8"))["candidate_id"] == "CFAM006"


def test_fig_agent_compose_generalization_report_names_missing_prerequisites(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "second_fixture"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        """
name: second_fixture
panels:
  - id: A
""".lstrip(),
        encoding="utf-8",
    )
    (fixture / "second_fixture.tex").write_text(
        "\\begin{tikzpicture}\n\\draw (0,0) -- (1,1);\n\\end{tikzpicture}\n",
        encoding="utf-8",
    )

    result = _run(
        workspace,
        "compose-generalization-report",
        "second_fixture",
        "--output",
        "build/candidates/composition_generalization_report.json",
        "--json",
    )

    payload = json.loads(result.stdout)
    output = fixture / "build" / "candidates" / "composition_generalization_report.json"
    assert result.returncode == 0, result.stderr
    assert payload["schema"] == "figure-agent.composition-generalization-report.v1"
    assert payload["status"] == "missing_prerequisites"
    assert payload["fixture"] == "second_fixture"
    assert payload["can_generate_structural_families"] is False
    assert payload["missing_prerequisites"] == [
        "semantic_blocks",
        "composition_model.objects",
        "family_target:carrier_walk",
        "family_target:current_sparkline",
        "family_target:n_breadth",
    ]
    assert payload["source_mutation_allowed"] is False
    assert payload["tex_execution_allowed"] is False
    assert payload["model_calls_allowed"] is False
    assert payload["recommended_next_action"] == "add semantic composition annotations"
    assert json.loads(output.read_text(encoding="utf-8")) == payload
