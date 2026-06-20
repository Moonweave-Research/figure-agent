from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _write_fixture(workspace: Path, name: str = "quality_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: quality_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    report = fixture / "build" / "text_boundary_clash.json"
    report.parent.mkdir()
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-boundary-clash.v1",
                "fixture": name,
                "candidates": [{"id": "TB001", "text": "label-a"}],
                "total": 1,
            }
        ),
        encoding="utf-8",
    )
    return fixture


def _run_fig_agent(workspace: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return subprocess.run(
        [sys.executable, str(FIG_AGENT), *args],
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )


def test_fig_agent_quality_map_outputs_json_without_writing(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_fixture(workspace)
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))

    result = _run_fig_agent(workspace, ["quality-map", "quality_demo", "--json"])

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.quality-defect-ledger.v1"
    assert payload["defects"][0]["patchability"]["state"] == "safe_candidate"
    after = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    assert after == before


def test_fig_agent_propose_outputs_patch_plan_and_rejects_unsafe_output(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_fixture(workspace)

    result = _run_fig_agent(workspace, ["propose", "quality_demo", "--json"])

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.quality-patch-plan.v1"
    assert payload["operations"][0]["defect_id"] == "QD001"

    rejected = _run_fig_agent(
        workspace,
        ["propose", "quality_demo", "--output", "../outside.yaml"],
    )
    assert rejected.returncode != 0
    assert "plan_output_forbidden" in rejected.stderr


def test_fig_agent_apply_plan_dry_run_uses_public_entrypoint(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    propose = _run_fig_agent(
        workspace,
        ["propose", "quality_demo", "--output", "build/quality/patch_plan.json"],
    )
    assert propose.returncode == 0, propose.stderr
    before = (fixture / "quality_demo.tex").read_text(encoding="utf-8")

    result = _run_fig_agent(
        workspace,
        ["apply-plan", "quality_demo", "--plan", "build/quality/patch_plan.json", "--dry-run"],
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.quality-patch-result.v1"
    assert payload["applied"] is False
    assert (fixture / "quality_demo.tex").read_text(encoding="utf-8") == before
