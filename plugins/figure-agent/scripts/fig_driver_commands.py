"""Safe command string helpers for fig_driver."""

from __future__ import annotations

import shlex


def _q(value: str) -> str:
    return shlex.quote(value)


def compile_command(name: str) -> str:
    return f"bash scripts/compile.sh {_q(f'examples/{name}/{name}.tex')}"


def critique_command(name: str) -> str:
    return f"/fig_critique {_q(name)}"


def adjudicate_command(name: str) -> str:
    return f"uv run python3 scripts/critique_adjudication.py scaffold {_q(name)}"


def fig_loop_command(name: str, goal: str) -> str:
    return f"uv run python3 scripts/fig_loop.py {_q(name)} --goal {_q(goal)} --json"


def export_command(name: str) -> str:
    return f"uv run python3 scripts/run_export.py {_q(name)}"


def svg_polish_executor_dry_run_command(name: str) -> str:
    return f"uv run python3 scripts/svg_polish_executor.py {_q(f'examples/{name}')} --dry-run"


def svg_polish_executor_write_command(name: str) -> str:
    return f"uv run python3 scripts/svg_polish_executor.py {_q(f'examples/{name}')} --write"


def svg_polish_delta_command(name: str) -> str:
    script = (
        "from pathlib import Path; "
        "from svg_polish_delta import build_svg_polish_delta_pack; "
        f"build_svg_polish_delta_pack(Path('examples/{name}'), base_dir=Path('.'))"
    )
    return f"PYTHONPATH=scripts uv run python3 -c {_q(script)}"
