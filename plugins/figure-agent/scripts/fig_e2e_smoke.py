"""Deterministic end-to-end smoke runner for figure-agent loop checks.

Runs compile -> export -> status -> fig_loop for one fixture and emits a JSON
summary. This is an operational smoke harness; it does not edit source,
critique, acceptance, or golden metadata.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from status import infer_stage  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.e2e-smoke.v1"
CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]
_FIG_LOOP_JSON_TYPES = {
    "run_dir": str,
    "manifest_path": str,
    "iteration_path": str,
    "final_stop_reason": str,
    "escalation_level": str,
    "patch_handoff_present": bool,
}


class SmokeError(ValueError):
    """Expected user-facing error for smoke preflight failures."""


def _default_command_runner(
    args: list[str],
    *,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


def _tail(text: str, *, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _command_result(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "args": list(result.args),
        "returncode": result.returncode,
        "stdout_tail": _tail(result.stdout or ""),
        "stderr_tail": _tail(result.stderr or ""),
    }


def _run_process(
    args: list[str],
    *,
    repo_root: Path,
    command_runner: Callable[..., subprocess.CompletedProcess[str]],
) -> subprocess.CompletedProcess[str]:
    return command_runner(args, cwd=repo_root)


def _run_step(
    args: list[str],
    *,
    repo_root: Path,
    command_runner: Callable[..., subprocess.CompletedProcess[str]],
) -> dict[str, Any]:
    return _command_result(_run_process(args, repo_root=repo_root, command_runner=command_runner))


def _loop_goal(goal: str, iteration: int, repeat: int) -> str:
    return f"{goal} (smoke run {iteration}/{repeat})"


def _status_summary(example_dir: Path) -> dict[str, Any]:
    status = infer_stage(example_dir)
    return {
        "stage": status["stage"],
        "render_state": status["render_state"],
        "critique_state": status["critique_state"],
        "export_state": status["export_state"],
        "acceptance_state": status["acceptance_state"],
        "workflow_ready": status["workflow_ready"],
        "golden_ready": status["golden_ready"],
        "release_ready": status["release_ready"],
        "final_ready": status["final_ready"],
        "notes": status["notes"],
        "next": status["next"],
    }


def _fig_loop_command(
    name: str,
    *,
    goal: str,
    runs_root: Path | None,
) -> list[str]:
    command = [
        "uv",
        "run",
        "python3",
        "scripts/fig_loop.py",
        name,
        "--goal",
        goal,
        "--json",
    ]
    if runs_root is not None:
        command.extend(["--runs-root", str(runs_root)])
    return command


def _parse_fig_loop_json(stdout: str) -> dict[str, Any] | None:
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    parsed: dict[str, Any] = {}
    for key, expected_type in _FIG_LOOP_JSON_TYPES.items():
        value = data.get(key)
        if not isinstance(value, expected_type):
            return None
        parsed[key] = value
    return parsed


def _failure(summary: dict[str, Any], run: dict[str, Any], step: str) -> dict[str, Any]:
    summary["success"] = False
    summary["failed_run"] = run["iteration"]
    summary["failed_step"] = step
    return summary


def _stable_outcome(run: dict[str, Any]) -> dict[str, Any]:
    status = run["status"]
    fig_loop = run["fig_loop"]
    return {
        "status": {
            "stage": status["stage"],
            "render_state": status["render_state"],
            "critique_state": status["critique_state"],
            "export_state": status["export_state"],
            "acceptance_state": status["acceptance_state"],
            "workflow_ready": status["workflow_ready"],
            "golden_ready": status["golden_ready"],
            "release_ready": status["release_ready"],
            "final_ready": status["final_ready"],
            "notes": status["notes"],
        },
        "fig_loop": {
            "final_stop_reason": fig_loop["final_stop_reason"],
            "escalation_level": fig_loop["escalation_level"],
            "patch_handoff_present": fig_loop["patch_handoff_present"],
        },
    }


def _stability_failure(
    summary: dict[str, Any],
    run: dict[str, Any],
    *,
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    summary["success"] = False
    summary["failed_run"] = run["iteration"]
    summary["failed_step"] = "repeat_stability"
    summary["stability_mismatch"] = {
        "baseline": baseline,
        "current": current,
    }
    return summary


def run_smoke(
    name: str,
    *,
    goal: str = "deterministic E2E smoke",
    repeat: int = 1,
    repo_root: Path = REPO_ROOT,
    runs_root: Path | None = None,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] = _default_command_runner,
) -> dict[str, Any]:
    """Run deterministic compile/export/status/fig_loop smoke checks."""
    if repeat < 1:
        raise SmokeError("repeat must be >= 1")

    repo_root = repo_root.resolve()
    runs_root = runs_root.resolve() if runs_root is not None else None
    example_dir = repo_root / "examples" / name
    tex_path = example_dir / f"{name}.tex"
    if not example_dir.is_dir():
        raise SmokeError(f"examples/{name}/ not found")
    if not tex_path.is_file():
        raise SmokeError(f"examples/{name}/{name}.tex not found")

    summary: dict[str, Any] = {
        "schema": SCHEMA,
        "fixture": name,
        "goal": goal,
        "repeat": repeat,
        "success": True,
        "runs": [],
    }
    baseline_outcome: dict[str, Any] | None = None

    for iteration in range(1, repeat + 1):
        run: dict[str, Any] = {"iteration": iteration}
        summary["runs"].append(run)

        run["compile"] = _run_step(
            ["bash", "scripts/compile.sh", f"examples/{name}/{name}.tex"],
            repo_root=repo_root,
            command_runner=command_runner,
        )
        if run["compile"]["returncode"] != 0:
            return _failure(summary, run, "compile")

        run["export"] = _run_step(
            ["uv", "run", "python3", "scripts/run_export.py", name],
            repo_root=repo_root,
            command_runner=command_runner,
        )
        if run["export"]["returncode"] != 0:
            return _failure(summary, run, "export")

        run["status_command"] = _run_step(
            ["uv", "run", "python3", "scripts/status.py", f"examples/{name}"],
            repo_root=repo_root,
            command_runner=command_runner,
        )
        if run["status_command"]["returncode"] != 0:
            return _failure(summary, run, "status")
        try:
            run["status"] = _status_summary(example_dir)
        except Exception as exc:
            run["status_error"] = str(exc)
            return _failure(summary, run, "status")

        fig_loop_process = _run_process(
            _fig_loop_command(name, goal=_loop_goal(goal, iteration, repeat), runs_root=runs_root),
            repo_root=repo_root,
            command_runner=command_runner,
        )
        run["fig_loop_command"] = _command_result(fig_loop_process)
        if run["fig_loop_command"]["returncode"] != 0:
            return _failure(summary, run, "fig_loop")
        fig_loop_summary = _parse_fig_loop_json(fig_loop_process.stdout or "")
        if fig_loop_summary is None:
            return _failure(summary, run, "fig_loop")
        run["fig_loop"] = fig_loop_summary
        current_outcome = _stable_outcome(run)
        run["stable_outcome"] = current_outcome
        if baseline_outcome is None:
            baseline_outcome = current_outcome
        elif current_outcome != baseline_outcome:
            return _stability_failure(
                summary,
                run,
                baseline=baseline_outcome,
                current=current_outcome,
            )

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="fixture name under examples/")
    parser.add_argument("--goal", default="deterministic E2E smoke")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--runs-root", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        summary = run_smoke(
            args.name,
            goal=args.goal,
            repeat=args.repeat,
            repo_root=args.repo_root,
            runs_root=args.runs_root,
        )
    except SmokeError as exc:
        summary = {
            "schema": SCHEMA,
            "fixture": args.name,
            "goal": args.goal,
            "repeat": args.repeat,
            "success": False,
            "runs": [],
            "error": str(exc),
        }
        print(json.dumps(summary, sort_keys=True))
        return 1

    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
