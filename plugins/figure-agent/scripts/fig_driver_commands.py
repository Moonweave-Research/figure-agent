"""Safe command string helpers for fig_driver."""

from __future__ import annotations

import shlex


def compile_command(name: str) -> str:
    return f"bash scripts/compile.sh examples/{name}/{name}.tex"


def critique_command(name: str) -> str:
    return f"/fig_critique {name}"


def adjudicate_command(name: str) -> str:
    return f"uv run python3 scripts/critique_adjudication.py scaffold {name}"


def fig_loop_command(name: str, goal: str) -> str:
    return f"uv run python3 scripts/fig_loop.py {name} --goal {shlex.quote(goal)} --json"


def export_command(name: str) -> str:
    return f"uv run python3 scripts/run_export.py {name}"


def svg_polish_executor_dry_run_command(name: str) -> str:
    return f"uv run python3 scripts/svg_polish_executor.py examples/{name} --dry-run"


def svg_polish_executor_write_command(name: str) -> str:
    return f"uv run python3 scripts/svg_polish_executor.py examples/{name} --write"


def svg_polish_delta_command(name: str) -> str:
    script = (
        "from pathlib import Path; "
        "from svg_polish_delta import build_svg_polish_delta_pack; "
        f"build_svg_polish_delta_pack(Path('examples/{name}'), base_dir=Path('.'))"
    )
    return f"PYTHONPATH=scripts uv run python3 -c {shlex.quote(script)}"
