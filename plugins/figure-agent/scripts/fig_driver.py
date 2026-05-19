"""Dry-run advisory driver for one figure.

Reads `/fig_status` state via `status.infer_stage()` and emits exactly one
recommended next action as JSON. The driver never writes under
`examples/<name>/`, `build/`, `exports/`, `polish/`, `.scratch/`, or git.

Schema: figure-agent.driver.v1.

The ``forbidden_actions`` field in the JSON output draws from two stable
identifier namespaces:

* the 11 canonical action names below (``ACTION_*`` constants), and
* operational mutation identifiers (``FORBIDDEN_*`` constants) that
  document mutations the driver itself never performs and that no
  downstream executor should perform without an explicit mode/issue
  authorization.

Consumers must treat both namespaces as flat opaque strings and ignore any
unknown top-level field; the ``v1`` schema suffix only changes on
incompatible removal or rename of a documented field.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from status import infer_stage  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.driver.v1"
MODES = ("authoring", "review", "release", "polish")

# Action vocabulary (Issue 8A / 8B contract).
ACTION_CREATE_OR_FIX_SOURCE = "create_or_fix_source"
ACTION_RUN_COMPILE = "run_compile"
ACTION_RUN_CRITIQUE = "run_critique"
ACTION_RUN_ADJUDICATE = "run_adjudicate"
ACTION_RUN_FIG_LOOP = "run_fig_loop"
ACTION_RUN_EXPORT = "run_export"
ACTION_PATCH_HANDOFF_STOP = "patch_handoff_stop"
ACTION_HUMAN_GATE_STOP = "human_gate_stop"
ACTION_POLISH_HANDOFF_STOP = "polish_handoff_stop"
ACTION_RELEASE_BLOCKED = "release_blocked"
ACTION_COMPLETE = "complete"

# Stop-boundary identifiers (Issue 8A contract).
STOP_HOST_LLM_CRITIQUE = "host_llm_critique_required"
STOP_REFERENCE_MISSING = "reference_missing"
STOP_ACCEPTED_OR_FINAL_READY = "accepted_or_final_ready_required"
STOP_SEMANTIC_BACKPORT = "semantic_backport_required"

# Stop boundaries reserved for a future driver that ingests /fig_loop output
# (Issue 8C+). The current Issue 8B driver never consumes a fig_loop run, so it
# cannot detect patch ambiguity, human gates, or force-golden requests; the
# constants are defined for vocabulary stability and downstream type-checking.
STOP_AMBIGUOUS_PATCH = "ambiguous_patch_selection"
STOP_PATCH_HANDOFF = "patch_handoff_required"
STOP_HUMAN_GATE = "human_gate_required"
STOP_FORCE_GOLDEN = "force_golden_required"
STOP_MODE_FORBIDDEN = "mode_forbidden_action"

# Operational mutation identifiers used in ``forbidden_actions``. These are
# stable strings the driver pins so downstream executors can recognise them
# alongside the 11 canonical actions.
FORBIDDEN_EDIT_SOURCE = "edit_source"
FORBIDDEN_EDIT_SOURCE_OUTSIDE_PATCH = "edit_source_outside_patch_handoff"
FORBIDDEN_EDIT_GENERATED_EXPORT = "edit_generated_export"
FORBIDDEN_EDIT_POLISHED_SVG = "edit_polished_svg"
FORBIDDEN_SET_ACCEPTED = "set_accepted"
FORBIDDEN_FORCE_GOLDEN = "force_golden"
FORBIDDEN_BYPASS_SEMANTIC_BACKPORT = "bypass_semantic_backport"

_STATUS_COMPACT_KEYS = (
    "stage",
    "name",
    "notes",
    "render_state",
    "critique_state",
    "export_state",
    "acceptance_state",
    "final_artifact_state",
    "final_artifact_kind",
    "final_artifact_path",
    "workflow_ready",
    "golden_ready",
    "release_ready",
    "final_ready",
)

_FORBIDDEN_BY_MODE: dict[str, list[str]] = {
    "authoring": [
        ACTION_RUN_CRITIQUE,
        ACTION_RUN_ADJUDICATE,
        ACTION_RUN_EXPORT,
        ACTION_RUN_FIG_LOOP,
        ACTION_POLISH_HANDOFF_STOP,
        ACTION_RELEASE_BLOCKED,
    ],
    "review": [
        FORBIDDEN_EDIT_SOURCE_OUTSIDE_PATCH,
        FORBIDDEN_SET_ACCEPTED,
        FORBIDDEN_FORCE_GOLDEN,
        FORBIDDEN_EDIT_GENERATED_EXPORT,
        FORBIDDEN_EDIT_POLISHED_SVG,
    ],
    "release": [
        FORBIDDEN_EDIT_SOURCE,
        FORBIDDEN_SET_ACCEPTED,
        FORBIDDEN_FORCE_GOLDEN,
        FORBIDDEN_EDIT_POLISHED_SVG,
    ],
    "polish": [
        FORBIDDEN_EDIT_SOURCE,
        FORBIDDEN_EDIT_GENERATED_EXPORT,
        FORBIDDEN_SET_ACCEPTED,
        FORBIDDEN_BYPASS_SEMANTIC_BACKPORT,
    ],
}


def _compact_status(status: dict[str, Any]) -> dict[str, Any]:
    return {key: status.get(key) for key in _STATUS_COMPACT_KEYS}


def _summary(
    *,
    name: str,
    mode: str,
    goal: str,
    status: dict[str, Any],
    action: str,
    safe_command: str | None,
    stop_boundary: str | None,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": name,
        "mode": mode,
        "goal": goal,
        "status": _compact_status(status),
        "action": action,
        "safe_command": safe_command,
        "stop_boundary": stop_boundary,
        "reason": reason,
        "forbidden_actions": list(_FORBIDDEN_BY_MODE.get(mode, ())),
        "may_execute": False,
    }


def _status_for(example_dir: Path) -> dict[str, Any]:
    """Thin wrapper to keep tests monkeypatch-friendly."""
    return infer_stage(example_dir)


def _adjudication_needs_action(example_dir: Path, status: dict[str, Any]) -> bool:
    if status.get("critique_state") != "FRESH":
        return False
    adjudication_path = example_dir / "critique_adjudication.yaml"
    critique_path = example_dir / "critique.md"
    if not adjudication_path.is_file():
        return True
    from critique_adjudication import (  # noqa: PLC0415
        CritiqueAdjudicationError,
        adjudication_is_stale,
        load_adjudication,
    )

    try:
        load_adjudication(adjudication_path)
    except (CritiqueAdjudicationError, OSError):
        return True
    return adjudication_is_stale(adjudication_path, critique_path)


def _compile_command(name: str) -> str:
    return f"bash scripts/compile.sh examples/{name}/{name}.tex"


def _critique_command(name: str) -> str:
    return f"/fig_critique {name}"


def _adjudicate_command(name: str) -> str:
    return f"uv run python3 scripts/critique_adjudication.py scaffold {name}"


def _fig_loop_command(name: str, goal: str) -> str:
    return f"uv run python3 scripts/fig_loop.py {name} --goal {shlex.quote(goal)} --json"


def _export_command(name: str) -> str:
    return f"uv run python3 scripts/run_export.py {name}"


def build_driver_summary(
    name: str,
    *,
    mode: str,
    goal: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"unsupported mode: {mode}")
    example_dir = repo_root / "examples" / name
    status = _status_for(example_dir)
    return _select_action(name, mode=mode, goal=goal, status=status, example_dir=example_dir)


def _select_action(
    name: str,
    *,
    mode: str,
    goal: str,
    status: dict[str, Any],
    example_dir: Path,
) -> dict[str, Any]:
    render = status.get("render_state")
    critique = status.get("critique_state")
    export = status.get("export_state")
    final_state = status.get("final_artifact_state")
    final_kind = status.get("final_artifact_kind")
    release_ready = status.get("release_ready") is True

    def make(
        action: str,
        *,
        safe_command: str | None,
        stop_boundary: str | None,
        reason: str,
    ) -> dict[str, Any]:
        return _summary(
            name=name,
            mode=mode,
            goal=goal,
            status=status,
            action=action,
            safe_command=safe_command,
            stop_boundary=stop_boundary,
            reason=reason,
        )

    # Stage 0/1: source must be scaffolded or authored first.
    if render in ("NOT_SCAFFOLDED", "NOT_AUTHORED"):
        return make(
            ACTION_CREATE_OR_FIX_SOURCE,
            safe_command=None,
            stop_boundary=None,
            reason=(
                "fixture directory or <name>.tex is missing; scaffold via "
                "/fig_new and author TikZ source before any compile loop."
            ),
        )

    # Render gate (applies in every mode that builds toward review/release/polish).
    if render in ("MISSING", "STALE"):
        return make(
            ACTION_RUN_COMPILE,
            safe_command=_compile_command(name),
            stop_boundary=None,
            reason="render is not fresh; run /fig_compile to refresh build PDF.",
        )

    # Render is FRESH from here.

    if mode == "authoring":
        return make(
            ACTION_COMPLETE,
            safe_command=None,
            stop_boundary=None,
            reason=(
                "render_state is FRESH; authoring mode does not advance to "
                "critique, export, loop, or polish."
            ),
        )

    # review / release / polish share the critique gate.
    if critique == "REFERENCE_MISSING":
        return make(
            ACTION_RUN_CRITIQUE,
            safe_command=None,
            stop_boundary=STOP_REFERENCE_MISSING,
            reason=(
                "declared reference input is missing; fix spec.yaml path or "
                "add the reference file before critique."
            ),
        )

    if critique in ("MISSING", "STALE"):
        return make(
            ACTION_RUN_CRITIQUE,
            safe_command=_critique_command(name),
            stop_boundary=STOP_HOST_LLM_CRITIQUE,
            reason=(
                "reference-grounded critique is missing or stale; host Claude "
                "must run /fig_critique to refresh critique.md."
            ),
        )

    if mode == "review":
        if critique == "FRESH" and _adjudication_needs_action(example_dir, status):
            return make(
                ACTION_RUN_ADJUDICATE,
                safe_command=_adjudicate_command(name),
                stop_boundary=None,
                reason=(
                    "critique.md is fresh but critique_adjudication.yaml is "
                    "missing or stale; scaffold adjudication next."
                ),
            )
        return make(
            ACTION_RUN_FIG_LOOP,
            safe_command=_fig_loop_command(name, goal),
            stop_boundary=None,
            reason=(
                "render and critique prerequisites are closed; record a "
                "verify-only loop checkpoint via /fig_loop."
            ),
        )

    if mode == "release":
        if export in ("MISSING", "STALE"):
            return make(
                ACTION_RUN_EXPORT,
                safe_command=_export_command(name),
                stop_boundary=None,
                reason=(
                    "exports are missing or stale; run /fig_export before "
                    "release readiness can be evaluated."
                ),
            )
        if release_ready:
            return make(
                ACTION_COMPLETE,
                safe_command=None,
                stop_boundary=None,
                reason="release_ready is true; release loop is closed.",
            )
        return make(
            ACTION_RELEASE_BLOCKED,
            safe_command=None,
            stop_boundary=STOP_ACCEPTED_OR_FINAL_READY,
            reason=(
                "release_ready is false; resolve accepted/golden/final "
                "artifact gates manually — driver will not mutate them."
            ),
        )

    # mode == "polish"
    if export in ("MISSING", "STALE"):
        return make(
            ACTION_RUN_EXPORT,
            safe_command=_export_command(name),
            stop_boundary=None,
            reason=(
                "generated export is not current; refresh /fig_export before "
                "starting SVG polish handoff."
            ),
        )
    if final_state == "BLOCKED":
        return make(
            ACTION_POLISH_HANDOFF_STOP,
            safe_command=None,
            stop_boundary=STOP_SEMANTIC_BACKPORT,
            reason=(
                "final artifact is BLOCKED — polish manifest declares a "
                "semantic backport is required before promotion."
            ),
        )
    if final_kind == "polished_svg" and final_state == "FRESH":
        return make(
            ACTION_COMPLETE,
            safe_command=None,
            stop_boundary=None,
            reason="polished_svg final artifact is FRESH; polish loop is closed.",
        )
    return make(
        ACTION_POLISH_HANDOFF_STOP,
        safe_command=None,
        stop_boundary=None,
        reason=(
            "generated export is current; remaining work is visual-only SVG "
            "polish handoff (see /fig_loop SVG Polish Handoff)."
        ),
    )


def main(argv: list[str] | None = None, *, repo_root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(prog="fig_driver.py")
    parser.add_argument("name")
    parser.add_argument("--mode", choices=list(MODES), required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not args.dry_run:
        print(
            "fig_driver.py: --dry-run is required in Issue 8B",
            file=sys.stderr,
        )
        return 2
    try:
        summary = build_driver_summary(
            args.name, mode=args.mode, goal=args.goal, repo_root=repo_root
        )
    except ValueError as exc:
        print(f"fig_driver.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
