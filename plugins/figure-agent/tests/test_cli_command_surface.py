from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"
SCRIPTS_ROOT = PLUGIN_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

import compatibility_command_contracts  # noqa: E402


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
        "authoring-repair-rollback",
    ]
    assert surface["bounded_repair_transaction_state"] == "complete"
    assert surface["counts"]["total"] == 85
    assert set(surface["commands_by_disposition"]) == {
        "core",
        "internal_compatibility",
        "retired_default",
    }
    assert {
        "adjudicated-repair-target",
        "authoring-repair-review",
    } <= set(surface["commands_by_disposition"]["internal_compatibility"])
    assert surface["compatibility_command_contract_registry"] == (
        compatibility_command_contracts.serialize_registry()
    )


def test_registry_controls_internal_cli_membership_and_public_help() -> None:
    contracts = compatibility_command_contracts.serialize_registry()["contracts"]
    registry_commands = {contract["command"] for contract in contracts}
    source = FIG_AGENT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "_LITERAL_INTERNAL_COMPATIBILITY_COMMANDS"
            for target in node.targets
        )
    )
    assert isinstance(assignment.value, ast.Call)
    assert isinstance(assignment.value.args[0], ast.Set)
    literal_commands = {
        item.value
        for item in assignment.value.args[0].elts
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    }

    assert registry_commands == {"loop", "improve", "e2e-smoke"}
    assert registry_commands.isdisjoint(literal_commands)
    assert "_LITERAL_INTERNAL_COMPATIBILITY_COMMANDS" in source
    assert "compatibility_command_contracts.command_names()" in source

    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(PLUGIN_ROOT)
    doctor = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(FIG_AGENT),
            "doctor",
            "--commands",
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert doctor.returncode == 0, doctor.stderr
    internal_commands = set(
        json.loads(doctor.stdout)["command_surface"]["commands_by_disposition"][
            "internal_compatibility"
        ]
    )
    assert registry_commands <= internal_commands

    for command in sorted(registry_commands):
        result = subprocess.run(
            [str(FIG_AGENT), command, "--help"],
            cwd=PLUGIN_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"{command}: {result.stderr}"


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


def test_rollback_cli_exposes_explicit_legacy_compatibility_opt_in() -> None:
    result = subprocess.run(
        [str(FIG_AGENT), "authoring-repair-rollback", "--help"],
        cwd=PLUGIN_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--legacy-packet" in result.stdout


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
