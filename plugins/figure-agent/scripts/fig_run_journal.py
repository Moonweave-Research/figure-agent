"""Summarize non-authoritative fig_run journals for safe continuation."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any

import yaml
from journal_art_direction_playbook import (  # noqa: E402
    JournalArtDirectionPlaybookError,
    declared_journal_playbook_path,
)
from paper_aesthetic_context import (  # noqa: E402
    PaperAestheticContextError,
    declared_paper_context_path,
)
from quality_manifest import critique_manifest_paths  # noqa: E402

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


def _fixture_evidence_paths(repo_root: Path, name: str) -> tuple[Path, ...]:
    example_dir = repo_root / "examples" / name
    paths = [
        example_dir / f"{name}.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
        example_dir / "authoring_plan.md",
        example_dir / "authoring_contract.md",
        example_dir / "subregion_iteration_log.md",
        example_dir / "theory_guard.md",
        example_dir / "coordinate_hints.yaml",
        example_dir / "critique_reference_pack.yaml",
        example_dir / "aesthetic_intent.yaml",
        example_dir / "critique.md",
        example_dir / "critique_adjudication.yaml",
        example_dir / "external_vision_review.yaml",
        example_dir / "inspection_trace.yaml",
        example_dir / "build" / "visual_clash.json",
        example_dir / "build" / "text_boundary_clash.json",
        example_dir / "build" / "label_path_proximity.json",
        example_dir / "build" / "audit_crops" / "manifest.json",
        example_dir / "build" / "reference_aesthetic_metrics.json",
        example_dir / "polish" / "svg_polish_recipe.yaml",
        example_dir / "polish" / "aesthetic_delta" / "before.png",
        example_dir / "polish" / "aesthetic_delta" / "after.png",
        example_dir / "polish" / "aesthetic_delta" / "diff.png",
        example_dir / "polish" / "aesthetic_delta" / "delta_manifest.json",
        example_dir / "polish" / "svg_semantic_diff.json",
        example_dir / "polish" / "svg_polish_audit.md",
        example_dir / "polish" / "svg_polish_manifest.yaml",
        example_dir / "polish" / f"{name}.polished.svg",
        example_dir / "build" / f"{name}.pdf",
        example_dir / "build" / f"{name}.png",
    ]
    paths.extend(_critique_manifest_paths(repo_root, example_dir, name))
    paths.extend(_declared_context_paths(example_dir))
    return tuple(dict.fromkeys(paths))


def _critique_manifest_paths(repo_root: Path, example_dir: Path, name: str) -> tuple[Path, ...]:
    spec = _load_spec_mapping(example_dir)
    if spec is None:
        return ()
    return critique_manifest_paths(
        example_dir,
        name,
        spec,
        style_lock_path=repo_root / "styles" / "polymer-paper-preamble.sty",
    )


def _declared_context_paths(example_dir: Path) -> tuple[Path, ...]:
    spec = _load_spec_mapping(example_dir)
    if spec is None:
        return ()
    paths: list[Path] = []
    try:
        paper_context_path = declared_paper_context_path(example_dir, spec)
    except PaperAestheticContextError:
        paper_context_path = None
    if paper_context_path is not None:
        paths.append(paper_context_path)
    try:
        journal_playbook_path = declared_journal_playbook_path(example_dir, spec)
    except JournalArtDirectionPlaybookError:
        journal_playbook_path = None
    if journal_playbook_path is not None:
        paths.append(journal_playbook_path)
    return tuple(paths)


def _load_spec_mapping(example_dir: Path) -> dict[str, Any] | None:
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        return None
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None
    return spec if isinstance(spec, dict) else None


def _repo_relative(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def _stale_against(repo_root: Path, name: str, *, journal_mtime: float) -> list[str]:
    stale_paths: list[str] = []
    for path in _fixture_evidence_paths(repo_root, name):
        if not path.is_file():
            continue
        try:
            if path.stat().st_mtime > journal_mtime:
                stale_paths.append(_repo_relative(repo_root, path))
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
    stale_paths = _stale_against(repo_root, name, journal_mtime=mtime)
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
    summary = latest_journal_summary(args.repo_root, args.name, runs_root=args.runs_root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
