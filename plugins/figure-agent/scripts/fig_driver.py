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
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fig_driver_checkpoint as checkpoint_mod  # noqa: E402
import fig_driver_closeout as closeout_mod  # noqa: E402
import fig_driver_editorial as editorial_mod  # noqa: E402
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

# Stop boundaries surfaced when the driver ingests the latest /fig_loop output.
STOP_AMBIGUOUS_PATCH = "ambiguous_patch_selection"
STOP_PATCH_HANDOFF = "patch_handoff_required"
STOP_HUMAN_GATE = "human_gate_required"
STOP_FORCE_GOLDEN = "force_golden_required"
STOP_MODE_FORBIDDEN = "mode_forbidden_action"
STOP_CLOSEOUT = "closeout_required"

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
    "publication_gate_state",
    "publication_gate_failures",
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
    workspace_warnings: list[str] | None = None,
    loop_checkpoint: dict[str, Any] | None = None,
    closeout: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = {
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
        "workspace_warnings": list(workspace_warnings or ()),
        "may_execute": False,
    }
    if loop_checkpoint is not None:
        summary["loop_checkpoint"] = loop_checkpoint
    if closeout is not None:
        summary["closeout"] = closeout
    return summary


def _status_for(example_dir: Path) -> dict[str, Any]:
    """Thin wrapper to keep tests monkeypatch-friendly."""
    return infer_stage(example_dir)


def _workspace_warnings(repo_root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    dirty_paths = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        if path:
            dirty_paths.append(path)
    if not dirty_paths:
        return []
    preview = ", ".join(dirty_paths[:5])
    suffix = "" if len(dirty_paths) <= 5 else f", +{len(dirty_paths) - 5} more"
    return [f"tracked_worktree_dirty: {preview}{suffix}"]


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


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _top_tier_audit_requires_human_gate(summary: Any) -> bool:
    if not isinstance(summary, dict):
        return False
    verdict_counts = summary.get("verdict_counts")
    return (
        _positive_int(summary.get("blocking_high_impact_count"))
        or summary.get("worst_verdict") in {"fail", "needs_human"}
        or (
            isinstance(verdict_counts, dict)
            and (
                _positive_int(verdict_counts.get("fail"))
                or _positive_int(verdict_counts.get("needs_human"))
            )
        )
    )


def _loop_checkpoint_review_blocker(loop_checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    loop_stop = loop_checkpoint["final_stop_reason"]
    loop_action = loop_checkpoint.get("recommended_next_action")
    patch_handoff = loop_checkpoint.get("patch_handoff")
    escalation = loop_checkpoint.get("escalation_level")
    if loop_stop in {"patch_target_recommended", "active_subregion_recommended"}:
        if isinstance(patch_handoff, dict):
            target = patch_handoff.get("target_id") or patch_handoff.get("patch_target")
            return {
                "action": ACTION_PATCH_HANDOFF_STOP,
                "safe_command": None,
                "stop_boundary": STOP_PATCH_HANDOFF,
                "reason": (
                    "latest /fig_loop checkpoint requires one patch handoff"
                    f" for {target}."
                ),
            }
    if loop_stop == "ambiguous_patch_selection":
        return {
            "action": ACTION_PATCH_HANDOFF_STOP,
            "safe_command": None,
            "stop_boundary": STOP_AMBIGUOUS_PATCH,
            "reason": (
                "latest /fig_loop checkpoint is ambiguous: "
                f"{loop_action or 'select exactly one patch target'}."
            ),
        }
    if loop_stop == "human_gate_required" or escalation == "human_review_required":
        return {
            "action": ACTION_HUMAN_GATE_STOP,
            "safe_command": None,
            "stop_boundary": STOP_HUMAN_GATE,
            "reason": (
                "latest /fig_loop checkpoint requires human review: "
                f"{loop_action or 'domain judgment is required'}."
            ),
        }
    top_tier_summary = loop_checkpoint.get("top_tier_audit_summary")
    if _top_tier_audit_requires_human_gate(top_tier_summary):
        return {
            "action": ACTION_HUMAN_GATE_STOP,
            "safe_command": None,
            "stop_boundary": STOP_HUMAN_GATE,
            "reason": (
                "latest /fig_loop checkpoint reports top-tier audit "
                "blockers; resolve fail/needs_human or blocking "
                "high-impact items before export or release."
            ),
        }
    editorial_summary = loop_checkpoint.get("editorial_art_direction_summary")
    if editorial_mod.editorial_review_requires_human_gate(editorial_summary):
        return {
            "action": ACTION_HUMAN_GATE_STOP,
            "safe_command": None,
            "stop_boundary": STOP_HUMAN_GATE,
            "reason": (
                "latest /fig_loop checkpoint reports editorial art-direction "
                "blockers; resolve fail/needs_human or blocking high-impact "
                "items before export, polish, or release."
            ),
        }
    return None


def _publication_gate_blocks_release(status: dict[str, Any]) -> bool:
    return status.get("publication_gate_state") in {
        "HUMAN_ACCEPTANCE_REQUIRED",
        "PROVENANCE_REQUIRED",
    }


def _publication_gate_block_reason(status: dict[str, Any]) -> str:
    state = status.get("publication_gate_state")
    failures = status.get("publication_gate_failures")
    if isinstance(failures, list) and failures:
        first = failures[0]
        if isinstance(first, dict):
            code = first.get("code", "unknown_publication_gate_failure")
            action = str(
                first.get("required_action", "resolve the publication gate manually")
            ).rstrip(".")
            return (
                f"publication gate is {state}; first blocker {code}: {action}. "
                "Driver will not set accepted, force golden state, or mutate provenance."
            )
    return (
        f"publication gate is {state}; resolve human acceptance/provenance manually. "
        "Driver will not set accepted, force golden state, or mutate provenance."
    )


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
    workspace_warnings = _workspace_warnings(repo_root)
    loop_checkpoint = (
        checkpoint_mod.latest_loop_checkpoint(repo_root, name, example_dir)
        if mode in {"review", "polish"}
        else None
    )
    closeout = closeout_mod.closeout_report(name, repo_root=repo_root) if mode == "review" else None
    return _select_action(
        name,
        mode=mode,
        goal=goal,
        status=status,
        example_dir=example_dir,
        workspace_warnings=workspace_warnings,
        loop_checkpoint=loop_checkpoint,
        closeout=closeout,
    )


def _select_action(
    name: str,
    *,
    mode: str,
    goal: str,
    status: dict[str, Any],
    example_dir: Path,
    workspace_warnings: list[str] | None = None,
    loop_checkpoint: dict[str, Any] | None = None,
    closeout: dict[str, Any] | None = None,
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
        checkpoint: dict[str, Any] | None = None,
        closeout_report: dict[str, Any] | None = None,
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
            workspace_warnings=workspace_warnings,
            loop_checkpoint=checkpoint,
            closeout=closeout_report,
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
        if loop_checkpoint is not None:
            loop_blocker = _loop_checkpoint_review_blocker(loop_checkpoint)
            if loop_blocker is not None:
                return make(
                    loop_blocker["action"],
                    safe_command=loop_blocker["safe_command"],
                    stop_boundary=loop_blocker["stop_boundary"],
                    reason=loop_blocker["reason"],
                    checkpoint=loop_checkpoint,
                )
        closeout_result = closeout_mod.closeout_recommendation(closeout)
        if closeout_result is not None:
            if closeout_result.kind == "export":
                action = ACTION_RUN_EXPORT
                safe_command = _export_command(name)
                stop_boundary = STOP_CLOSEOUT
            elif closeout_result.kind == "force_golden":
                action = ACTION_RELEASE_BLOCKED
                safe_command = None
                stop_boundary = STOP_FORCE_GOLDEN
            elif closeout_result.kind == "blocked":
                action = ACTION_HUMAN_GATE_STOP
                safe_command = None
                stop_boundary = STOP_CLOSEOUT
            else:
                action = ACTION_RUN_FIG_LOOP
                safe_command = _fig_loop_command(name, goal)
                stop_boundary = STOP_CLOSEOUT
            return make(
                action,
                safe_command=safe_command,
                stop_boundary=stop_boundary,
                reason=closeout_result.reason,
                closeout_report=closeout_mod.compact_closeout(closeout or {}),
            )
        if loop_checkpoint is not None:
            loop_blocker = _loop_checkpoint_review_blocker(loop_checkpoint)
            if loop_blocker is not None:
                return make(
                    loop_blocker["action"],
                    safe_command=loop_blocker["safe_command"],
                    stop_boundary=loop_blocker["stop_boundary"],
                    reason=loop_blocker["reason"],
                    checkpoint=loop_checkpoint,
                )
            loop_stop = loop_checkpoint["final_stop_reason"]
            loop_action = loop_checkpoint.get("recommended_next_action")
            if loop_stop == "status_action_required" and "--force-golden" in str(loop_action):
                return make(
                    ACTION_RELEASE_BLOCKED,
                    safe_command=None,
                    stop_boundary=STOP_FORCE_GOLDEN,
                    reason=(
                        "latest /fig_loop checkpoint requires explicit golden "
                        "roll-forward approval."
                    ),
                    checkpoint=loop_checkpoint,
                )
            if loop_stop in {"no_actionable_findings", "verify_only_complete"}:
                return make(
                    ACTION_COMPLETE,
                    safe_command=None,
                    stop_boundary=None,
                    reason="latest /fig_loop checkpoint has no actionable review blocker.",
                    checkpoint=loop_checkpoint,
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
        if _publication_gate_blocks_release(status):
            return make(
                ACTION_RELEASE_BLOCKED,
                safe_command=None,
                stop_boundary=STOP_ACCEPTED_OR_FINAL_READY,
                reason=_publication_gate_block_reason(status),
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
    if loop_checkpoint is not None:
        editorial_summary = loop_checkpoint.get("editorial_art_direction_summary")
        polish_route = editorial_mod.editorial_polish_route(editorial_summary)
        if polish_route is not None:
            polish_path = (
                editorial_summary.get("polish_recommended_path")
                if isinstance(editorial_summary, dict)
                else None
            )
            if polish_route == editorial_mod.ROUTE_SEMANTIC_BACKPORT:
                return make(
                    ACTION_POLISH_HANDOFF_STOP,
                    safe_command=None,
                    stop_boundary=STOP_SEMANTIC_BACKPORT,
                    reason=(
                        "latest /fig_loop editorial art-direction summary "
                        "recommends semantic_backport_required; repair TikZ, "
                        "briefing, or spec semantics before SVG polish can count."
                    ),
                    checkpoint=loop_checkpoint,
                )
            if polish_route == editorial_mod.ROUTE_HUMAN_GATE:
                return make(
                    ACTION_HUMAN_GATE_STOP,
                    safe_command=None,
                    stop_boundary=STOP_HUMAN_GATE,
                    reason=(
                        "latest /fig_loop editorial art-direction summary has "
                        "human-gated or high-impact-blocking items "
                        f"({polish_path}); a human must choose the target "
                        "style and polish scope before handoff."
                    ),
                    checkpoint=loop_checkpoint,
                )
            if polish_route == editorial_mod.ROUTE_RUN_LOOP:
                return make(
                    ACTION_RUN_FIG_LOOP,
                    safe_command=_fig_loop_command(name, goal),
                    stop_boundary=STOP_MODE_FORBIDDEN,
                    reason=(
                        "latest /fig_loop editorial art-direction summary "
                        "recommends continue_tikz; leave polish mode and "
                        "resolve source-level illustration issues first."
                    ),
                    checkpoint=loop_checkpoint,
                )
            if polish_route == editorial_mod.ROUTE_READY_FOR_SVG_POLISH:
                return make(
                    ACTION_POLISH_HANDOFF_STOP,
                    safe_command=None,
                    stop_boundary=None,
                    reason=(
                        "latest /fig_loop editorial art-direction summary "
                        "recommends ready_for_svg_polish; generated export is "
                        "current and SVG handoff may proceed without source edits."
                    ),
                    checkpoint=loop_checkpoint,
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
            "fig_driver.py: --dry-run is required",
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
