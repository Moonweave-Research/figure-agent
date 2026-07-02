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
DETERMINISTIC_CHECKS = {
    "orphan_plot",
    "floating_annotation",
    "arrow_clutter",
    "anchor_ambiguity",
}
HUMAN_COMMENTARY_CHECKS = {
    "measurement_arrow_crosses_data",
    "thin_glitch_primitive",
    "panel_density_imbalance",
    "path_mechanicalness",
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


def _lint_fixture(tmp_path: Path, *, duplicate: bool = False) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "composition_lint_demo"
    fixture.mkdir(parents=True)
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        """
name: composition_lint_demo
panels:
  - id: A
composition_model:
  panels:
    A:
      objects:
        sparkline:
          kind: inset_plot
          truth_bearing: true
        floating_note:
          kind: annotation
          truth_bearing: false
        arrow_a:
          kind: arrow
          truth_bearing: false
        arrow_b:
          kind: arrow
          truth_bearing: false
        arrow_c:
          kind: arrow
          truth_bearing: false
        arrow_d:
          kind: measurement_span
          truth_bearing: true
        bad_callout:
          kind: annotation
          truth_bearing: false
          anchor_target: missing_object
""".lstrip(),
        encoding="utf-8",
    )
    lines = [
        "% fig-agent:start object=sparkline panel=A kind=inset_plot truth_bearing=true",
        "spark",
        "% fig-agent:end object=sparkline",
        "% fig-agent:start object=floating_note panel=A kind=annotation truth_bearing=false",
        "note",
        "% fig-agent:end object=floating_note",
        "% fig-agent:start object=arrow_a panel=A kind=arrow truth_bearing=false",
        "arrow",
        "% fig-agent:end object=arrow_a",
        "% fig-agent:start object=arrow_b panel=A kind=arrow truth_bearing=false",
        "arrow",
        "% fig-agent:end object=arrow_b",
        "% fig-agent:start object=arrow_c panel=A kind=arrow truth_bearing=false",
        "arrow",
        "% fig-agent:end object=arrow_c",
        "% fig-agent:start object=arrow_d panel=A kind=measurement_span truth_bearing=true",
        "arrow",
        "% fig-agent:end object=arrow_d",
        "% fig-agent:start object=bad_callout panel=A kind=annotation truth_bearing=false",
        "callout",
        "% fig-agent:end object=bad_callout",
    ]
    if duplicate:
        lines.extend(
            [
                "% fig-agent:start object=sparkline panel=A",
                "duplicate",
                "% fig-agent:end object=sparkline",
            ]
        )
    (fixture / "composition_lint_demo.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return workspace, fixture


def _by_check(findings: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(finding["check"]): finding for finding in findings}


def test_composition_lint_emits_deterministic_findings_with_metadata(
    tmp_path: Path,
) -> None:
    import composition_lint

    workspace, fixture = _lint_fixture(tmp_path)

    payload = composition_lint.build_composition_lint(
        "composition_lint_demo",
        workspace_root=workspace,
    )

    findings = _by_check(payload["findings"])
    assert payload["schema"] == "figure-agent.composition-lint.v1"
    assert payload["status"] == "ready"
    assert DETERMINISTIC_CHECKS <= set(findings)
    for check in DETERMINISTIC_CHECKS:
        finding = findings[check]
        assert finding["mode"] == "deterministic"
        assert finding["metric"]
        assert finding["evidence_object"]
        assert finding["threshold"]
    assert not (fixture / "build").exists()
    assert not (fixture / "exports").exists()


def test_composition_lint_demotes_geometry_dependent_checks_to_human_commentary(
    tmp_path: Path,
) -> None:
    import composition_lint

    workspace, _fixture = _lint_fixture(tmp_path)

    payload = composition_lint.build_composition_lint(
        "composition_lint_demo",
        workspace_root=workspace,
    )

    findings = _by_check(payload["findings"])
    assert HUMAN_COMMENTARY_CHECKS <= set(findings)
    for check in HUMAN_COMMENTARY_CHECKS:
        finding = findings[check]
        assert finding["mode"] == "human_commentary"
        assert finding["rank_eligible"] is False
        assert finding["blocking_allowed"] is False
        assert "threshold" not in finding


def test_composition_lint_propagates_blocked_scene_model_without_mutation(
    tmp_path: Path,
) -> None:
    import composition_lint

    workspace, fixture = _lint_fixture(tmp_path, duplicate=True)

    payload = composition_lint.build_composition_lint(
        "composition_lint_demo",
        workspace_root=workspace,
    )

    assert payload["status"] == "blocked"
    assert payload["findings"] == []
    assert payload["diagnostics"][0]["code"] == "semantic_block_duplicate"
    assert not (fixture / "build").exists()
    assert not (fixture / "exports").exists()


def test_fig_agent_lint_composition_outputs_json_without_mutating_fixture(
    tmp_path: Path,
) -> None:
    workspace, fixture = _lint_fixture(tmp_path)

    result = _run(workspace, "lint-composition", "composition_lint_demo", "--json")

    payload = json.loads(result.stdout)
    assert result.returncode == 0, result.stderr
    assert payload["schema"] == "figure-agent.composition-lint.v1"
    assert payload["status"] == "ready"
    assert not (fixture / "build").exists()
    assert not (fixture / "exports").exists()
