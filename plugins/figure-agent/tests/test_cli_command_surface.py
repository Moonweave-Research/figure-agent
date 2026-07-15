from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def test_doctor_reports_the_canonical_command_surface() -> None:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(PLUGIN_ROOT)

    result = subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), "python", str(FIG_AGENT),
         "doctor", "--commands", "--json"],
        cwd=PLUGIN_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    surface = json.loads(result.stdout)["command_surface"]
    assert surface["canonical_route"] == ["status", "run"]
    assert surface["bounded_repair_entry_route"] == [
        "authoring-repair-packet",
        "authoring-repair-materialize",
        "authoring-repair-finalize",
    ]
    assert surface["bounded_repair_transaction_state"] == "complete"
    assert surface["counts"]["total"] == 84
    assert set(surface["commands_by_disposition"]) == {
        "core",
        "internal_compatibility",
        "retired_default",
    }
    assert {
        "adjudicated-repair-target",
        "authoring-repair-review",
    } <= set(surface["commands_by_disposition"]["internal_compatibility"])


def test_closed_loop_core_commands_are_routed_as_internal_surfaces() -> None:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(PLUGIN_ROOT)

    for command in ("adjudicated-repair-target", "authoring-repair-review"):
        result = subprocess.run(
            [str(FIG_AGENT), command, "--help"],
            cwd=PLUGIN_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr


def test_improve_does_not_reactivate_retired_quality_search() -> None:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(PLUGIN_ROOT)

    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(FIG_AGENT),
            "improve",
            "demo",
            "--goal",
            "inspect",
            "--aggressive-candidates",
        ],
        cwd=PLUGIN_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "unrecognized arguments: --aggressive-candidates" in result.stderr
