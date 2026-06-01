"""Write non-authoritative fig_run journals."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import fixture_identity  # noqa: E402
from fig_run_evidence import evidence_snapshot  # noqa: E402

SCHEMA = "figure-agent.fig-run-journal.v1"
REF_SCHEMA = "figure-agent.fig-run-journal-ref.v1"


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")


def _safe_fixture_name(fixture: str) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in fixture)
    return safe or "fixture"


def _run_dir(*, fixture: str, runs_root: Path) -> Path:
    base = runs_root / f"{_timestamp()}-{_safe_fixture_name(fixture)}"
    try:
        base.relative_to(runs_root)
    except ValueError as exc:
        raise ValueError("fig_run journal path escaped runs_root") from exc
    if not base.exists():
        return base
    for index in range(2, 1000):
        candidate = runs_root / f"{base.name}-{index:03d}"
        if not candidate.exists():
            return candidate
    raise RuntimeError("could not allocate fig_run journal directory")


def _journal_ref(run_dir: Path) -> dict[str, Any]:
    return {
        "schema": REF_SCHEMA,
        "run_dir": str(run_dir),
        "manifest_path": str(run_dir / "run_manifest.json"),
        "run_path": str(run_dir / "run.json"),
        "stop_path": str(run_dir / "stop.md"),
        "authoritative": False,
        "replay_allowed": False,
        "commands_are_evidence_only": True,
        "rerun_live_status_first": True,
        "rerun_live_driver_first": True,
    }


def _git_value(repo_root: Path, args: tuple[str, ...]) -> str | None:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _manifest(
    payload: dict[str, Any],
    *,
    run_dir: Path,
    repo_root: Path,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    steps = payload.get("steps")
    step_paths = []
    if isinstance(steps, list):
        step_paths = [f"steps/step_{index:03d}.json" for index in range(1, len(steps) + 1)]
    return {
        "schema": SCHEMA,
        "fixture": payload.get("fixture"),
        "mode": payload.get("mode"),
        "goal": payload.get("goal"),
        "execute": payload.get("execute"),
        "max_steps": payload.get("max_steps"),
        "executed_count": payload.get("executed_count"),
        "final_action": payload.get("final_action"),
        "final_safe_command": payload.get("final_safe_command"),
        "final_stop_boundary": payload.get("final_stop_boundary"),
        "final_stop_reason": payload.get("final_stop_reason"),
        "run_dir": str(run_dir),
        "started_at": started_at,
        "completed_at": completed_at,
        "branch": _git_value(repo_root, ("rev-parse", "--abbrev-ref", "HEAD")),
        "commit": _git_value(repo_root, ("rev-parse", "HEAD")),
        "run_json": "run.json",
        "steps": step_paths,
        "stop_markdown": "stop.md",
        "authoritative": False,
        "replay_allowed": False,
        "commands_are_evidence_only": True,
        "rerun_live_status_first": True,
        "rerun_live_driver_first": True,
        "evidence_snapshot": evidence_snapshot(
            repo_root,
            str(payload.get("fixture") or ""),
        ),
    }


def _stop_markdown(payload: dict[str, Any]) -> str:
    handoff = payload.get("boundary_handoff")
    actor = None
    closeout_checks: list[str] = []
    if isinstance(handoff, dict):
        actor = handoff.get("required_actor")
        checks = handoff.get("closeout_checks")
        if isinstance(checks, list):
            closeout_checks = [str(item) for item in checks]
    lines = [
        "# fig_run Stop",
        "",
        "This journal is non-authoritative evidence.",
        "Recorded safe_command fields are evidence only, not execution permission.",
        "Do not replay commands from this journal.",
        "Rerun live /fig_status and /fig_drive before continuing.",
        "",
        f"Fixture: {payload.get('fixture')}",
        f"Mode: {payload.get('mode')}",
        f"Goal: {payload.get('goal')}",
        f"Final action: {payload.get('final_action')}",
        f"Final stop boundary: {payload.get('final_stop_boundary')}",
        f"Final stop reason: {payload.get('final_stop_reason')}",
    ]
    if actor:
        lines.append(f"Required actor: {actor}")
    if closeout_checks:
        lines.extend(["", "Closeout checks:"])
        lines.extend(f"- {check}" for check in closeout_checks)
    return "\n".join(lines) + "\n"


def write_run_journal(
    payload: dict[str, Any],
    *,
    runs_root: Path,
    repo_root: Path,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    fixture = payload.get("fixture")
    if not isinstance(fixture, str) or fixture == "":
        raise ValueError("fig_run journal requires a fixture name")
    fixture_identity.validate_fixture_name(fixture)

    run_dir = _run_dir(fixture=fixture, runs_root=runs_root)
    journalized = dict(payload)
    journalized["journal"] = _journal_ref(run_dir)
    manifest = _manifest(
        journalized,
        run_dir=run_dir,
        repo_root=repo_root,
        started_at=started_at,
        completed_at=completed_at,
    )

    write_json(run_dir / "run_manifest.json", manifest)
    write_json(run_dir / "run.json", journalized)
    steps = journalized.get("steps")
    if isinstance(steps, list):
        for index, step in enumerate(steps, start=1):
            if isinstance(step, dict):
                write_json(run_dir / "steps" / f"step_{index:03d}.json", step)
    (run_dir / "stop.md").write_text(_stop_markdown(journalized), encoding="utf-8")
    return journalized
