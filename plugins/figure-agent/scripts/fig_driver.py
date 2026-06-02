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
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_visual_clash_budget as warning_budget_mod  # noqa: E402
import fig_driver_checkpoint as checkpoint_mod  # noqa: E402
import fig_driver_closeout as closeout_mod  # noqa: E402
import fig_driver_commands as command_mod  # noqa: E402
import fig_driver_editorial as editorial_mod  # noqa: E402
import fig_driver_guidance as guidance_mod  # noqa: E402
import fixture_identity  # noqa: E402
import ready_improvement as ready_improvement_mod  # noqa: E402
from next_action_summary import driver_next_action_summary  # noqa: E402
from status import infer_stage  # noqa: E402
from svg_polish_delta import SvgPolishDeltaError, svg_polish_delta_is_stale  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.driver.v1"
MODES = ("authoring", "review", "release", "polish", "final")

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
    "critique_lint_summary",
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
    "final": [
        FORBIDDEN_EDIT_SOURCE,
        FORBIDDEN_EDIT_GENERATED_EXPORT,
        FORBIDDEN_EDIT_POLISHED_SVG,
        FORBIDDEN_SET_ACCEPTED,
        FORBIDDEN_FORCE_GOLDEN,
        FORBIDDEN_BYPASS_SEMANTIC_BACKPORT,
    ],
}


def _compact_status(status: dict[str, Any]) -> dict[str, Any]:
    return {key: status.get(key) for key in _STATUS_COMPACT_KEYS}


def _svg_polish_prerequisite_gate(action: str, reason: str) -> dict[str, Any] | None:
    next_action_by_driver_action = {
        ACTION_RUN_COMPILE: "run_fig_compile",
        ACTION_RUN_CRITIQUE: "run_fig_critique",
        ACTION_RUN_ADJUDICATE: "run_fig_adjudicate",
        ACTION_RUN_EXPORT: "run_fig_export",
    }
    next_action = next_action_by_driver_action.get(action)
    if next_action is None:
        return None
    return {
        "schema": editorial_mod.GATE_SCHEMA,
        "state": "blocked",
        "source": "driver_prerequisite",
        "can_start_svg_polish": False,
        "recommended_path": None,
        "next_action": next_action,
        "reason": reason,
        "required_inputs": list(editorial_mod.REQUIRED_GATE_INPUTS),
        "blocking_items": [{"source": "driver_prerequisite", "id": action}],
    }


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
    warning_budget: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status_explanation = status.get("status_explanation")
    if isinstance(status_explanation, dict):
        first_blocker = status_explanation.get("first_blocker")
        if isinstance(first_blocker, dict):
            code = first_blocker.get("code")
            if isinstance(code, str) and code not in {"", "none"}:
                reason = f"{reason} first blocker {code}."
    audit_evidence = status.get("audit_evidence")
    if isinstance(audit_evidence, dict):
        audit_state = audit_evidence.get("evaluation_state")
        audit_reason = audit_evidence.get("reason")
        if audit_state in {"needs_action", "missing_input", "stale_or_mismatched"}:
            reason = f"{reason} audit evidence {audit_state}: {audit_reason}."
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
    if isinstance(status_explanation, dict):
        summary["status_explanation"] = status_explanation
    critique_freshness = status.get("critique_freshness")
    if isinstance(critique_freshness, dict):
        summary["critique_freshness"] = critique_freshness
    if isinstance(audit_evidence, dict):
        summary["audit_evidence"] = audit_evidence
    if loop_checkpoint is not None:
        summary["loop_checkpoint"] = loop_checkpoint
        svg_polish_readiness = editorial_mod.svg_polish_readiness_from_checkpoint(
            loop_checkpoint
        )
        if svg_polish_readiness is not None:
            summary["svg_polish_readiness"] = svg_polish_readiness
    if mode == "polish":
        prerequisite_gate = _svg_polish_prerequisite_gate(action, reason)
        summary["svg_polish_gate"] = (
            prerequisite_gate
            if prerequisite_gate is not None
            else editorial_mod.svg_polish_gate_from_checkpoint(loop_checkpoint)
        )
    if closeout is not None:
        summary["closeout"] = closeout
    ready_improvement = ready_improvement_mod.build_ready_improvement_summary(
        fixture=name,
        status=status,
        action=action,
        stop_boundary=stop_boundary,
        loop_checkpoint=loop_checkpoint,
    )
    if ready_improvement is not None:
        summary["ready_improvement_summary"] = ready_improvement
    summary["next_action_summary"] = driver_next_action_summary(summary)
    summary["operator_guidance"] = guidance_mod.operator_guidance(summary)
    if mode == "final":
        summary["final_readiness_profile"] = guidance_mod.final_readiness_profile(
            name,
            status=status,
            summary=summary,
            loop_checkpoint=loop_checkpoint,
            warning_budget=warning_budget,
        )
    return summary


def _status_for(example_dir: Path) -> dict[str, Any]:
    """Thin wrapper to keep tests monkeypatch-friendly."""
    return infer_stage(example_dir)


is_safe_fixture_name = fixture_identity.is_safe_fixture_name


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


def _crop_audit_uncertain_ids(summary: Any) -> list[str]:
    if not isinstance(summary, dict):
        return []
    if summary.get("evaluation_state") != "needs_action":
        return []
    crop_ids = summary.get("uncertain_crop_ids")
    if not isinstance(crop_ids, list):
        return []
    return [crop_id.strip() for crop_id in crop_ids if isinstance(crop_id, str) and crop_id.strip()]


def _crop_audit_review_blocker(loop_checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    uncertain_crop_ids = _crop_audit_uncertain_ids(loop_checkpoint.get("crop_audit_summary"))
    if not uncertain_crop_ids:
        return None
    preview = ", ".join(uncertain_crop_ids[:5])
    suffix = "" if len(uncertain_crop_ids) <= 5 else f", +{len(uncertain_crop_ids) - 5} more"
    return {
        "action": ACTION_HUMAN_GATE_STOP,
        "safe_command": None,
        "stop_boundary": STOP_HUMAN_GATE,
        "reason": (
            "latest /fig_loop checkpoint reports uncertain crop audit "
            f"verdicts for {preview}{suffix}; reread those crops or "
            "request human review before export, polish, or release."
        ),
    }


def _aesthetic_lever_review_blocker(loop_checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    summary = loop_checkpoint.get("aesthetic_lever_summary")
    if not isinstance(summary, dict):
        return None
    if summary.get("evaluation_state") != "needs_human":
        return None
    bottleneck = summary.get("next_aesthetic_bottleneck")
    lever_id = None
    if isinstance(bottleneck, dict):
        raw_lever_id = bottleneck.get("lever_id")
        if isinstance(raw_lever_id, str) and raw_lever_id.strip():
            lever_id = raw_lever_id.strip()
    return {
        "action": ACTION_HUMAN_GATE_STOP,
        "safe_command": None,
        "stop_boundary": STOP_HUMAN_GATE,
        "reason": (
            "latest /fig_loop checkpoint reports aesthetic lever human gate"
            + (f" for {lever_id}" if lever_id else "")
            + "; resolve human art-direction review before export, polish, or release."
        ),
    }


def _loop_checkpoint_review_blocker(
    loop_checkpoint: dict[str, Any],
    *,
    include_editorial: bool = True,
) -> dict[str, Any] | None:
    loop_stop = loop_checkpoint["final_stop_reason"]
    loop_action = loop_checkpoint.get("recommended_next_action")
    patch_handoff = loop_checkpoint.get("patch_handoff")
    escalation = loop_checkpoint.get("escalation_level")
    basin = loop_checkpoint.get("basin_summary")
    if loop_stop == "basin_detected" and isinstance(basin, dict):
        signal = basin.get("signal")
        signal_text = "unknown repeated signal"
        if isinstance(signal, dict):
            signal_class = signal.get("signal_class")
            signal_value = signal.get("signal_value")
            if isinstance(signal_class, str) and isinstance(signal_value, str):
                signal_text = f"{signal_class}={signal_value}"
        history_count = basin.get("history_count")
        count_text = f"{history_count} times" if isinstance(history_count, int) else "repeatedly"
        return {
            "action": ACTION_HUMAN_GATE_STOP,
            "safe_command": None,
            "stop_boundary": STOP_HUMAN_GATE,
            "reason": (
                "latest /fig_loop checkpoint reports repeated loop basin: "
                f"{signal_text} appeared {count_text}; step out before another "
                "local patch loop."
            ),
        }
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
    crop_audit_blocker = _crop_audit_review_blocker(loop_checkpoint)
    if crop_audit_blocker is not None:
        return crop_audit_blocker
    aesthetic_lever_blocker = _aesthetic_lever_review_blocker(loop_checkpoint)
    if aesthetic_lever_blocker is not None:
        return aesthetic_lever_blocker
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
    if include_editorial and editorial_mod.editorial_review_requires_human_gate(
        editorial_summary
    ):
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


def _svg_polish_route_hint(example_dir: Path, name: str, *, prefix: str) -> dict[str, str | None]:
    polish_dir = example_dir / "polish"
    recipe_path = polish_dir / "svg_polish_recipe.yaml"
    polished_svg_path = polish_dir / f"{name}.polished.svg"
    delta_manifest_path = polish_dir / "aesthetic_delta" / "delta_manifest.json"
    if not recipe_path.is_file():
        return {
            "safe_command": None,
            "reason": (
                f"{prefix} author a bounded polish/svg_polish_recipe.yaml first; "
                "the driver will not invent visual polish operations."
            ),
        }
    if not polished_svg_path.is_file():
        return {
            "safe_command": command_mod.svg_polish_executor_dry_run_command(name),
            "reason": (
                f"{prefix} polish/svg_polish_recipe.yaml exists; run the SVG polish "
                "executor dry-run first, review the plan, then use "
                f"`{command_mod.svg_polish_executor_write_command(name)}` only "
                "for visual-only edits."
            ),
        }
    if not delta_manifest_path.is_file():
        return {
            "safe_command": command_mod.svg_polish_delta_command(name),
            "reason": (
                f"{prefix} polished SVG exists; generate the SVG polish aesthetic "
                "delta pack before critique or handoff review."
            ),
        }
    try:
        delta_stale = svg_polish_delta_is_stale(delta_manifest_path, example_dir=example_dir)
    except SvgPolishDeltaError:
        return {
            "safe_command": command_mod.svg_polish_delta_command(name),
            "reason": (
                f"{prefix} SVG polish aesthetic delta pack is invalid; regenerate "
                "before critique or handoff review."
            ),
        }
    if delta_stale:
        return {
            "safe_command": command_mod.svg_polish_delta_command(name),
            "reason": (
                f"{prefix} SVG polish aesthetic delta pack is stale; regenerate "
                "before critique or handoff review."
            ),
        }
    return {
        "safe_command": None,
        "reason": (
            f"{prefix} recipe, polished SVG, and aesthetic delta pack are present; "
            "run scripts/svg_polish_handoff.py to scaffold audit and manifest."
        ),
    }


def _publication_gate_blocks_release(status: dict[str, Any]) -> bool:
    return status.get("publication_gate_state") in {
        "HUMAN_ACCEPTANCE_REQUIRED",
        "PROVENANCE_REQUIRED",
    }


def _draft_export_is_runner_executable(status: dict[str, Any]) -> bool:
    return (
        status.get("acceptance_state") == "NOT_DECLARED"
        and status.get("export_state") in {"MISSING", "STALE"}
        and status.get("critique_state") in {"FRESH", "NOT_REQUIRED"}
    )


def _draft_export_block_reason(status: dict[str, Any]) -> str:
    acceptance = status.get("acceptance_state")
    if acceptance != "NOT_DECLARED":
        return (
            f"exports are missing or stale, but acceptance_state is {acceptance}; "
            "/fig_run auto-export is limited to draft fixtures whose "
            "acceptance_state is NOT_DECLARED."
        )
    critique = status.get("critique_state")
    if critique not in {"FRESH", "NOT_REQUIRED"}:
        return (
            f"exports are missing or stale, but critique_state is {critique}; "
            "refresh or resolve critique before auto-export."
        )
    return (
        "exports are missing or stale, but the current state is outside the "
        "/fig_run auto-export policy."
    )


def _final_warning_budget(example_dir: Path, mode: str, render_state: Any) -> dict[str, Any] | None:
    if mode != "final" or render_state != "FRESH":
        return None
    return warning_budget_mod.summarize_fixture(example_dir)


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


def build_driver_summary(
    name: str,
    *,
    mode: str,
    goal: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"unsupported mode: {mode}")
    fixture_identity.validate_fixture_name(name)
    example_dir = repo_root / "examples" / name
    status = _status_for(example_dir)
    workspace_warnings = _workspace_warnings(repo_root)
    loop_checkpoint = (
        checkpoint_mod.latest_loop_checkpoint(repo_root, name, example_dir)
        if mode in {"review", "release", "polish", "final"}
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
        warning_budget: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        effective_warning_budget = warning_budget
        if effective_warning_budget is None:
            effective_warning_budget = _final_warning_budget(example_dir, mode, render)
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
            warning_budget=effective_warning_budget,
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
        compile_command = (
            command_mod.strict_compile_command(name)
            if mode == "final"
            else command_mod.compile_command(name)
        )
        reason = (
            "render is not fresh; run strict compile as the first final-readiness check."
            if mode == "final"
            else "render is not fresh; run /fig_compile to refresh build PDF."
        )
        return make(
            ACTION_RUN_COMPILE,
            safe_command=compile_command,
            stop_boundary=None,
            reason=reason,
        )

    # Render is FRESH from here.
    warning_budget = _final_warning_budget(example_dir, mode, render)
    if isinstance(warning_budget, dict):
        budget_state = warning_budget.get("state")
        if budget_state == "missing_input":
            return make(
                ACTION_RUN_COMPILE,
                safe_command=command_mod.strict_compile_command(name),
                stop_boundary=None,
                reason=(
                    "final warning budget input is missing; run strict compile "
                    "to regenerate detector reports before final readiness."
                ),
                warning_budget=warning_budget,
            )
        if budget_state in {"needs_action", "invalid"}:
            return make(
                ACTION_HUMAN_GATE_STOP,
                safe_command=None,
                stop_boundary=STOP_HUMAN_GATE,
                reason=(
                    "final warning budget exceeded or invalid; fix detector warnings "
                    "or update an explicit reviewed fixture cap before release."
                ),
                warning_budget=warning_budget,
            )

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
            safe_command=command_mod.critique_command(name),
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
                safe_command=command_mod.adjudicate_command(name),
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
                safe_command = command_mod.export_command(name)
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
                safe_command = command_mod.fig_loop_command(name, goal)
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
            safe_command=command_mod.fig_loop_command(name, goal),
            stop_boundary=None,
            reason=(
                "render and critique prerequisites are closed; record a "
                "verify-only loop checkpoint via /fig_loop."
            ),
        )

    if mode in {"release", "final"}:
        if export in ("MISSING", "STALE"):
            if not _draft_export_is_runner_executable(status):
                return make(
                    ACTION_RELEASE_BLOCKED,
                    safe_command=None,
                    stop_boundary=STOP_ACCEPTED_OR_FINAL_READY,
                    reason=_draft_export_block_reason(status),
                )
            return make(
                ACTION_RUN_EXPORT,
                safe_command=command_mod.export_command(name),
                stop_boundary=None,
                reason=(
                    "exports are missing or stale; run /fig_export before "
                    "release readiness can be evaluated."
                ),
            )
        if critique == "FRESH" and _adjudication_needs_action(example_dir, status):
            return make(
                ACTION_RUN_ADJUDICATE,
                safe_command=command_mod.adjudicate_command(name),
                stop_boundary=None,
                reason=(
                    "critique.md is fresh but critique_adjudication.yaml is "
                    "missing or stale; scaffold adjudication before release."
                ),
            )
        if mode == "final" and loop_checkpoint is None:
            return make(
                ACTION_RUN_FIG_LOOP,
                safe_command=command_mod.fig_loop_command(name, goal),
                stop_boundary=None,
                reason=(
                    "final readiness requires a current verify-only /fig_loop "
                    "checkpoint before complete or release guidance."
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
                checkpoint=loop_checkpoint,
            )
        return make(
            ACTION_RELEASE_BLOCKED,
            safe_command=None,
            stop_boundary=STOP_ACCEPTED_OR_FINAL_READY,
            reason=(
                "release_ready is false; resolve accepted/golden/final "
                "artifact gates manually — driver will not mutate them."
            ),
            checkpoint=loop_checkpoint,
        )

    # mode == "polish"
    if export in ("MISSING", "STALE"):
        if not _draft_export_is_runner_executable(status):
            return make(
                ACTION_POLISH_HANDOFF_STOP,
                safe_command=None,
                stop_boundary=STOP_ACCEPTED_OR_FINAL_READY,
                reason=_draft_export_block_reason(status),
            )
        return make(
            ACTION_RUN_EXPORT,
            safe_command=command_mod.export_command(name),
            stop_boundary=None,
            reason=(
                "generated export is not current; refresh /fig_export before "
                "starting SVG polish handoff."
            ),
        )
    if loop_checkpoint is not None:
        loop_blocker = _loop_checkpoint_review_blocker(
            loop_checkpoint,
            include_editorial=False,
        )
        if loop_blocker is not None:
            return make(
                loop_blocker["action"],
                safe_command=loop_blocker["safe_command"],
                stop_boundary=loop_blocker["stop_boundary"],
                reason=loop_blocker["reason"],
                checkpoint=loop_checkpoint,
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
                    safe_command=command_mod.fig_loop_command(name, goal),
                    stop_boundary=STOP_MODE_FORBIDDEN,
                    reason=(
                        "latest /fig_loop editorial art-direction summary "
                        "recommends continue_tikz; leave polish mode and "
                        "resolve source-level illustration issues first."
                    ),
                    checkpoint=loop_checkpoint,
                )
            if polish_route == editorial_mod.ROUTE_READY_FOR_SVG_POLISH:
                route_hint = _svg_polish_route_hint(
                    example_dir,
                    name,
                    prefix=(
                        "latest /fig_loop editorial art-direction summary "
                        "recommends ready_for_svg_polish; generated export is current."
                    ),
                )
                return make(
                    ACTION_POLISH_HANDOFF_STOP,
                    safe_command=route_hint["safe_command"],
                    stop_boundary=None,
                    reason=route_hint["reason"],
                    checkpoint=loop_checkpoint,
                )
    return make(
        ACTION_RUN_FIG_LOOP,
        safe_command=command_mod.fig_loop_command(name, goal),
        stop_boundary=STOP_MODE_FORBIDDEN,
        reason=(
            "generated export is current, but polish mode requires a current "
            "/fig_loop checkpoint whose editorial art-direction summary routes "
            "ready_for_svg_polish before SVG polish handoff can start."
        ),
    )


def main(argv: list[str] | None = None, *, repo_root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(prog="fig_driver.py")
    parser.add_argument("name")
    parser.add_argument("--mode", choices=list(MODES), required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
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
