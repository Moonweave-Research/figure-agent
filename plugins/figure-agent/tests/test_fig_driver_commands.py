from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_driver_commands import (  # noqa: E402
    adjudicate_command,
    compile_command,
    critique_command,
    export_command,
    fig_loop_command,
)


def test_compile_command_matches_driver_contract() -> None:
    assert (
        compile_command("driver_demo")
        == "bash scripts/compile.sh examples/driver_demo/driver_demo.tex"
    )


def test_critique_command_matches_driver_contract() -> None:
    assert critique_command("driver_demo") == "/fig_critique driver_demo"


def test_adjudicate_command_matches_driver_contract() -> None:
    assert (
        adjudicate_command("driver_demo")
        == "uv run python3 scripts/critique_adjudication.py scaffold driver_demo"
    )


def test_fig_loop_command_matches_driver_contract() -> None:
    assert (
        fig_loop_command("driver_demo", "review")
        == "uv run python3 scripts/fig_loop.py driver_demo --goal review --json"
    )


def test_fig_loop_command_shell_quotes_goal() -> None:
    assert (
        fig_loop_command("driver_demo", "it's a goal")
        == "uv run python3 scripts/fig_loop.py driver_demo --goal 'it'\"'\"'s a goal' --json"
    )


def test_export_command_matches_driver_contract() -> None:
    assert export_command("driver_demo") == "uv run python3 scripts/run_export.py driver_demo"
