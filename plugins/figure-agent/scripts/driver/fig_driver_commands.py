"""Safe command string helpers for fig_driver."""

from __future__ import annotations

import shlex


def _q(value: str) -> str:
    return shlex.quote(value)


def compile_command(name: str) -> str:
    return f"fig-agent compile {_q(name)}"


def strict_compile_command(name: str) -> str:
    return f"fig-agent compile {_q(name)} --strict"


def critique_command(name: str) -> str:
    return f"/fig_critique {_q(name)}"


def adjudicate_command(name: str) -> str:
    return f"fig-agent adjudicate {_q(name)}"


def fig_loop_command(name: str, goal: str) -> str:
    return f"fig-agent loop {_q(name)} --goal {_q(goal)} --json"


def export_command(name: str) -> str:
    return f"fig-agent export {_q(name)}"
