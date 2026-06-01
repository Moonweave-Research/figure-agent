"""Summarize non-authoritative fig_run journals for safe continuation."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

import fixture_identity
from fig_run_evidence import (  # noqa: E402
    fixture_evidence_paths,
    repo_relative,
    snapshot_stale_paths,
)

SCHEMA = "figure-agent.fig-run-journal-summary.v1"
JOURNAL_SCHEMA = "figure-agent.fig-run-journal.v1"


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _default_goal(manifest: dict[str, Any] | None) -> str:
    if manifest is not None:
        goal = manifest.get("goal")
        if isinstance(goal, str) and goal:
            return goal
    return "close loop"


def _default_mode(manifest: dict[str, Any] | None) -> str:
    if manifest is not None:
        mode = manifest.get("mode")
        if isinstance(mode, str) and mode:
            return mode
    return "review"


def _live_commands(name: str, *, mode: str, goal: str) -> list[str]:
    quoted_name = shlex.quote(name)
    return [
        f"/fig_status {quoted_name}",
        f"/fig_drive {quoted_name} --mode {shlex.quote(mode)} --goal {shlex.quote(goal)} --dry-run",
    ]


def _base_summary(
    repo_root: Path,
    name: str,
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": name,
        "runs_root": str(repo_root / ".scratch" / "fig-run-runs"),
        "authoritative": False,
        "replay_allowed": False,
        "resume_command": None,
        "next_live_commands": _live_commands(
            name,
            mode=_default_mode(manifest),
            goal=_default_goal(manifest),
        ),
        "rule": (
            "fig_run journals are context only. Do not replay stored safe_command "
            "values; rerun live /fig_status and /fig_drive before continuing."
        ),
    }


def _journal_mtime(run_dir: Path, manifest: dict[str, Any]) -> float:
    paths = [run_dir / "run_manifest.json"]
    run_path = _safe_run_json_path(run_dir, manifest)
    if run_path is not None:
        paths.append(run_path)
    mtimes: list[float] = []
    for path in paths:
        try:
            mtimes.append(path.stat().st_mtime)
        except OSError:
            continue
    return max(mtimes) if mtimes else 0.0


def _stale_against(repo_root: Path, name: str, *, journal_mtime: float) -> list[str]:
    stale_paths: list[str] = []
    for path in fixture_evidence_paths(repo_root, name):
        if not path.is_file():
            continue
        try:
            if path.stat().st_mtime > journal_mtime:
                stale_paths.append(repo_relative(repo_root, path))
        except OSError:
            continue
    return sorted(stale_paths)


def _read_journal(run_dir: Path, name: str) -> tuple[dict[str, Any], dict[str, Any] | None] | None:
    manifest = _load_json(run_dir / "run_manifest.json")
    if manifest is None:
        return None
    if manifest.get("schema") != JOURNAL_SCHEMA or manifest.get("fixture") != name:
        return None
    run_path = _safe_run_json_path(run_dir, manifest)
    payload = _load_json(run_path) if run_path is not None else None
    return manifest, payload


def _safe_run_json_path(run_dir: Path, manifest: dict[str, Any]) -> Path | None:
    run_json = manifest.get("run_json")
    if not isinstance(run_json, str) or not run_json:
        return None
    relative = Path(run_json)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    path = run_dir / relative
    try:
        path.resolve().relative_to(run_dir.resolve())
    except ValueError:
        return None
    return path


def _candidate_journals(
    runs_root: Path,
    name: str,
) -> list[tuple[Path, dict[str, Any], dict[str, Any] | None]]:
    if not runs_root.is_dir():
        return []
    candidates: list[tuple[Path, dict[str, Any], dict[str, Any] | None]] = []
    for run_dir in runs_root.iterdir():
        if not run_dir.is_dir():
            continue
        journal = _read_journal(run_dir, name)
        if journal is None:
            continue
        manifest, payload = journal
        candidates.append((run_dir, manifest, payload))
    return candidates


def _handoff(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    raw_handoff = payload.get("boundary_handoff")
    return raw_handoff if isinstance(raw_handoff, dict) else None


def latest_journal_summary(
    repo_root: Path,
    name: str,
    *,
    runs_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    runs_root = runs_root or repo_root / ".scratch" / "fig-run-runs"
    candidates = _candidate_journals(runs_root, name)
    if not candidates:
        return {
            **_base_summary(repo_root, name),
            "runs_root": str(runs_root),
            "state": "missing",
            "reason": "no valid fig_run journal found for fixture",
        }

    run_dir, manifest, payload = max(
        candidates,
        key=lambda item: _journal_mtime(item[0], item[1]),
    )
    handoff = _handoff(payload)
    closeout_checks: list[str] = []
    required_actor = None
    blocking_reason = ""
    if handoff is not None:
        required_actor = handoff.get("required_actor")
        blocking_reason = handoff.get("blocking_reason") if isinstance(
            handoff.get("blocking_reason"), str
        ) else ""
        checks = handoff.get("closeout_checks")
        if isinstance(checks, list):
            closeout_checks = [str(item) for item in checks]

    mtime = _journal_mtime(run_dir, manifest)
    stale_paths = sorted(
        dict.fromkeys(
            [
                *_stale_against(repo_root, name, journal_mtime=mtime),
                *snapshot_stale_paths(repo_root, name, manifest.get("evidence_snapshot")),
            ]
        )
    )
    state = "stale" if stale_paths else "available"
    safe_run_path = _safe_run_json_path(run_dir, manifest)
    summary = {
        **_base_summary(repo_root, name, manifest=manifest),
        "runs_root": str(runs_root),
        "state": state,
        "run_dir": str(run_dir),
        "manifest_path": str(run_dir / "run_manifest.json"),
        "run_path": str(safe_run_path) if safe_run_path is not None else None,
        "started_at": manifest.get("started_at"),
        "completed_at": manifest.get("completed_at"),
        "mode": manifest.get("mode"),
        "goal": manifest.get("goal"),
        "execute": manifest.get("execute"),
        "executed_count": manifest.get("executed_count"),
        "final_action": manifest.get("final_action"),
        "final_stop_boundary": manifest.get("final_stop_boundary"),
        "final_stop_reason": manifest.get("final_stop_reason"),
        "required_actor": required_actor,
        "blocking_reason": blocking_reason,
        "closeout_checks": closeout_checks,
        "stale_against": stale_paths,
    }
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize the latest non-authoritative fig_run journal."
    )
    parser.add_argument("name", help="fixture name")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--runs-root", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        fixture_identity.validate_fixture_name(args.name)
    except ValueError as exc:
        print(f"fig_run_journal.py: {exc}", file=sys.stderr)
        return 2
    summary = latest_journal_summary(args.repo_root, args.name, runs_root=args.runs_root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
