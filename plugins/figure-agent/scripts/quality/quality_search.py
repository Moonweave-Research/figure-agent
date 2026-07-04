"""Plan a global quality-search step for one fixture.

This module is deliberately read-only. It observes the existing status, loop,
quality ledger, and memory surfaces, then separates progress blockers, quality
targets, release blockers, and likely tool defects.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import fig_driver
import fixture_identity
import quality_defect_ledger
import quality_memory_index
import runtime_paths

SCHEMA = "figure-agent.quality-search-plan.v0"

PROGRESS_ACTIONS = {
    "create_or_fix_source",
    "run_compile",
    "run_critique",
    "run_adjudicate",
    "run_fig_loop",
    "run_export",
}


def _compact_status(status: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "render_state",
        "critique_state",
        "export_state",
        "acceptance_state",
        "workflow_ready",
        "release_ready",
        "final_ready",
    )
    return {key: status.get(key) for key in keys}


def _loop_basin(loop_checkpoint: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(loop_checkpoint, dict):
        return None
    basin = loop_checkpoint.get("basin_summary")
    if isinstance(basin, dict) and basin.get("evaluation_state") == "basin_detected":
        return basin
    if loop_checkpoint.get("final_stop_reason") == "basin_detected":
        return {"evaluation_state": "basin_detected"}
    return None


def _aesthetic_bottleneck(loop_checkpoint: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(loop_checkpoint, dict):
        return None
    summary = loop_checkpoint.get("aesthetic_lever_summary")
    if not isinstance(summary, dict):
        return None
    bottleneck = summary.get("next_aesthetic_bottleneck")
    return bottleneck if isinstance(bottleneck, dict) else None


def _release_blockers(driver: dict[str, Any]) -> list[dict[str, Any]]:
    next_action = driver.get("next_action_summary")
    if not isinstance(next_action, dict):
        return []
    blockers = next_action.get("release_blockers")
    if isinstance(blockers, list):
        return [item for item in blockers if isinstance(item, dict)]
    blocker = next_action.get("release_blocker")
    return [blocker] if isinstance(blocker, dict) else []


def _panel_counts(ledger: dict[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for defect in ledger.get("defects", []):
        if not isinstance(defect, dict):
            continue
        target = defect.get("target")
        panel = target.get("panel") if isinstance(target, dict) else None
        counts[str(panel or "unknown")] += 1
    return dict(sorted(counts.items()))


def _representative_targets(ledger: dict[str, Any], *, limit: int = 5) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for defect in ledger.get("defects", []):
        if not isinstance(defect, dict):
            continue
        actionability = defect.get("actionability")
        if isinstance(actionability, dict) and actionability.get("state") != "candidate_supported":
            continue
        selector = (
            defect.get("selector_hint") if isinstance(defect.get("selector_hint"), dict) else {}
        )
        target = defect.get("target") if isinstance(defect.get("target"), dict) else {}
        key = (
            str(target.get("panel") or "unknown"),
            str(target.get("subregion") or "unknown"),
            str(selector.get("value") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        targets.append(
            {
                "defect_id": defect.get("id"),
                "panel": key[0],
                "subregion": key[1],
                "selector": {
                    "kind": selector.get("kind"),
                    "value": selector.get("value"),
                },
                "defect_class": defect.get("defect_class"),
            }
        )
        if len(targets) >= limit:
            break
    return targets


def _unlinked_micro_defect_panels(driver: dict[str, Any]) -> list[str]:
    audit = driver.get("audit_evidence")
    feedback = audit.get("detector_feedback") if isinstance(audit, dict) else None
    ids = feedback.get("unlinked_micro_defect_ids") if isinstance(feedback, dict) else None
    if not isinstance(ids, list):
        return []
    panels: list[str] = []
    for item in ids:
        if not isinstance(item, str):
            continue
        parts = item.upper().split("_")
        for index, part in enumerate(parts):
            if part == "PANEL" and index + 1 < len(parts) and parts[index + 1]:
                panel = parts[index + 1]
                if panel not in panels:
                    panels.append(panel)
    return panels


def _classifications(
    driver: dict[str, Any],
    ledger: dict[str, Any],
) -> list[dict[str, Any]]:
    classifications: list[dict[str, Any]] = []
    action = str(driver.get("action") or "")
    if action in PROGRESS_ACTIONS:
        classifications.append(
            {
                "kind": "progress_blocker",
                "id": action,
                "blocks_search": True,
                "safe_command": driver.get("safe_command"),
                "reason": driver.get("reason"),
            }
        )

    for blocker in _release_blockers(driver):
        source = blocker.get("blocking_source") or blocker.get("stop_boundary") or "release"
        classifications.append(
            {
                "kind": "release_blocker",
                "id": source,
                "blocks_search": False,
                "blocks_release": bool(blocker.get("blocks_release", True)),
                "required_actor": blocker.get("required_actor", "human"),
                "reason": blocker.get("reason"),
            }
        )

    loop_checkpoint = driver.get("loop_checkpoint")
    basin = _loop_basin(loop_checkpoint if isinstance(loop_checkpoint, dict) else None)
    if basin is not None:
        signal = basin.get("signal") if isinstance(basin.get("signal"), dict) else {}
        classifications.append(
            {
                "kind": "quality_basin",
                "id": signal.get("signal_value") or driver.get("stop_boundary") or "basin_detected",
                "blocks_search": False,
                "history_count": basin.get("history_count"),
                "reason": basin.get("next_action") or driver.get("reason"),
            }
        )
    else:
        bottleneck = _aesthetic_bottleneck(
            loop_checkpoint if isinstance(loop_checkpoint, dict) else None
        )
        if bottleneck is not None:
            classifications.append(
                {
                    "kind": "quality_target",
                    "id": bottleneck.get("lever_id") or bottleneck.get("dimension"),
                    "blocks_search": False,
                    "route": bottleneck.get("route"),
                    "reason": "latest loop reports an aesthetic bottleneck",
                }
            )

    metrics = ledger.get("actionability_metrics")
    if isinstance(metrics, dict) and int(metrics.get("candidate_supported_defect_count") or 0) > 0:
        classifications.append(
            {
                "kind": "quality_target",
                "id": "detector_safe_candidates",
                "blocks_search": False,
                "candidate_supported_defect_count": metrics.get("candidate_supported_defect_count"),
                "panel_counts": _panel_counts(ledger),
            }
        )
    return classifications


def _step_out_hypotheses(
    name: str,
    driver: dict[str, Any],
    ledger: dict[str, Any],
) -> list[dict[str, Any]]:
    loop_checkpoint = driver.get("loop_checkpoint")
    basin = _loop_basin(loop_checkpoint if isinstance(loop_checkpoint, dict) else None)
    bottleneck = _aesthetic_bottleneck(
        loop_checkpoint if isinstance(loop_checkpoint, dict) else None
    )
    if basin is None:
        return []
    signal = basin.get("signal") if isinstance(basin.get("signal"), dict) else {}
    signal_value = str(signal.get("signal_value") or "")
    panel_counts = _panel_counts(ledger)
    common = {
        "fixture": name,
        "source": "basin_step_out",
        "mutation_allowed": False,
        "mutation_block_reason": "quality-search v0 is planner-only",
        "expected_detector_movement": "avoid another local typography-only loop",
        "rollback_condition": "candidate worsens compile, semantics, or print-legibility evidence",
    }
    if signal_value == "print_typography_authority":
        density_panels = [
            panel
            for panel in ("C", "E", "F")
            if panel_counts.get(panel, 0) or panel in _unlinked_micro_defect_panels(driver)
        ]
        return [
            {
                **common,
                "family": "hierarchy_rebalance",
                "target_scope": "panel/row",
                "target_hint": {
                    "panels": ["C", "D", "E", "F"],
                    "reason": "make result/mechanism hierarchy read before apparatus details",
                },
                "expected_visual_movement": "stronger Panel C hero and less equal-weight Row 2",
            },
            {
                **common,
                "family": "apparatus_strengthen",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "reason": "redraw charge/force/electrode/air-gap relation, not only label size",
                },
                "expected_visual_movement": (
                    "Panel F apparatus reads as deliberate mechanism evidence"
                ),
            },
            {
                **common,
                "family": "density_reduce",
                "target_scope": "panel",
                "target_hint": {
                    "panels": density_panels,
                    "reason": "detector candidates cluster in repeated label/source-line regions",
                },
                "expected_visual_movement": "fewer micro-label collisions at print scale",
            },
        ]
    route = bottleneck.get("route") if isinstance(bottleneck, dict) else None
    return [
        {
            **common,
            "family": "layout_macro_shift",
            "target_scope": "fixture",
            "target_hint": {
                "route": route,
                "reason": "basin detected without a specialized family mapping",
            },
            "expected_visual_movement": "larger search radius than the repeated local loop",
        }
    ]


def _detector_hypotheses(name: str, ledger: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = ledger.get("actionability_metrics")
    if (
        not isinstance(metrics, dict)
        or int(metrics.get("candidate_supported_defect_count") or 0) <= 0
    ):
        return []
    targets = _representative_targets(ledger)
    return [
        {
            "fixture": name,
            "family": "label_reflow",
            "source": "detector_safe_candidates",
            "mutation_allowed": False,
            "mutation_block_reason": "quality-search v0 is planner-only",
            "target_scope": "label_cluster",
            "target_hint": {"representative_targets": targets},
            "expected_detector_movement": (
                "reduce text_overlap defects without changing semantic labels"
            ),
            "expected_visual_movement": "cleaner print-scale label separations",
            "rollback_condition": "new visual clash, text-boundary, physics, or compile regression",
        }
    ]


def _patch_hypotheses(
    name: str,
    driver: dict[str, Any],
    ledger: dict[str, Any],
) -> list[dict[str, Any]]:
    if str(driver.get("action") or "") in PROGRESS_ACTIONS:
        return []
    basin_hypotheses = _step_out_hypotheses(name, driver, ledger)
    if basin_hypotheses:
        return basin_hypotheses[:3]
    return _detector_hypotheses(name, ledger)[:3]


def _tool_defect_candidates(driver: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    loop_checkpoint = driver.get("loop_checkpoint")
    loop = loop_checkpoint if isinstance(loop_checkpoint, dict) else {}
    bottleneck = _aesthetic_bottleneck(loop)
    basin = _loop_basin(loop)
    if (
        basin is not None
        and isinstance(bottleneck, dict)
        and bottleneck.get("route") == "tikz_patch"
    ):
        candidates.append(
            {
                "id": "TD001",
                "symptom": (
                    "tikz_patch route repeatedly ended in a basin instead of a "
                    "stronger patch-family switch"
                ),
                "expected_behavior": (
                    "promote repeated typography_authority signals into step-out "
                    "search families"
                ),
                "actual_behavior": loop.get("recommended_next_action") or driver.get("reason"),
                "minimal_reproduction": "fig-agent loop <fixture> --goal <goal> --json",
                "recommended_fix": (
                    "teach the search layer to branch from local label fixes to "
                    "hierarchy/apparatus/density families"
                ),
            }
        )
    metrics = ledger.get("actionability_metrics")
    if isinstance(metrics, dict):
        unknown = int(metrics.get("unknown_panel_defect_count") or 0)
        missing = int(metrics.get("missing_selector_hash_count") or 0)
        if unknown or missing:
            candidates.append(
                {
                    "id": f"TD{len(candidates) + 1:03d}",
                    "symptom": (
                        "safe detector candidates are not fully bound to panel and "
                        "selector evidence"
                    ),
                    "expected_behavior": (
                        "safe candidates should carry a declared panel and stable "
                        "selector hash"
                    ),
                    "actual_behavior": {
                        "unknown_panel_defect_count": unknown,
                        "missing_selector_hash_count": missing,
                    },
                    "minimal_reproduction": "fig-agent quality-map <fixture> --json",
                    "recommended_fix": (
                        "tighten undeclared-geometry source-line to panel mapping "
                        "before generating patch plans"
                    ),
                }
            )
    audit = driver.get("audit_evidence")
    feedback = audit.get("detector_feedback") if isinstance(audit, dict) else None
    if isinstance(feedback, dict) and int(feedback.get("unlinked_micro_defect_count") or 0) > 0:
        candidates.append(
            {
                "id": f"TD{len(candidates) + 1:03d}",
                "symptom": (
                    "critique contains unlinked micro defects after detector "
                    "accounting passed"
                ),
                "expected_behavior": (
                    "quality search should classify unlinked micro defects as search "
                    "targets or accounting gaps"
                ),
                "actual_behavior": {
                    "unlinked_micro_defect_ids": feedback.get("unlinked_micro_defect_ids", [])
                },
                "minimal_reproduction": "fig-agent drive <fixture> --mode review --dry-run --json",
                "recommended_fix": (
                    "surface unlinked micro defects in quality-map or a separate "
                    "aesthetic-target ledger"
                ),
            }
        )
    return candidates


def _memory_summary(memory: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(memory, dict):
        return {"state": "unavailable"}
    return {
        "state": "loaded",
        "event_count": memory.get("event_count"),
        "candidate_event_count": memory.get("candidate_event_count"),
        "eligible_prior_count": memory.get("eligible_prior_count"),
        "families": memory.get("families", {}),
    }


def build_quality_search_plan(
    name: str,
    *,
    goal: str,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    driver = fig_driver.build_driver_summary(
        name,
        mode="review",
        goal=goal,
        repo_root=paths.workspace_root,
    )
    ledger = quality_defect_ledger.build_quality_defect_ledger(
        name,
        plugin_root=paths.plugin_root,
        workspace_root=paths.workspace_root,
    )
    try:
        memory = quality_memory_index.build_fixture_index(
            name,
            write=False,
            plugin_root=paths.plugin_root,
            workspace_root=paths.workspace_root,
        )
    except (OSError, ValueError, quality_memory_index.QualityMemoryIndexError) as exc:
        memory = {"state": "unavailable", "reason": str(exc)}
    hypotheses = _patch_hypotheses(name, driver, ledger)
    basin = _loop_basin(
        driver.get("loop_checkpoint") if isinstance(driver.get("loop_checkpoint"), dict) else None
    )
    if str(driver.get("action") or "") in PROGRESS_ACTIONS:
        next_operation = {
            "kind": "run_prerequisite",
            "command": driver.get("safe_command"),
            "reason": driver.get("reason"),
        }
    elif basin is not None:
        next_operation = {
            "kind": "step_out_experiment",
            "candidate_families": [item["family"] for item in hypotheses],
            "reason": basin.get("next_action") or driver.get("reason"),
        }
    elif hypotheses:
        next_operation = {
            "kind": "render_candidate_batch",
            "candidate_families": [item["family"] for item in hypotheses],
            "reason": "detector-backed quality targets are available",
        }
    else:
        next_operation = {
            "kind": "no_actionable_quality_search_step",
            "command": None,
            "reason": driver.get("reason"),
        }
    return {
        "schema": SCHEMA,
        "fixture": name,
        "goal": goal,
        "mode": "plan",
        "read_only": True,
        "state": {
            "driver_action": driver.get("action"),
            "driver_stop_boundary": driver.get("stop_boundary"),
            "status": _compact_status(
                driver.get("status") if isinstance(driver.get("status"), dict) else {}
            ),
            "loop_final_stop_reason": (
                driver.get("loop_checkpoint", {}).get("final_stop_reason")
                if isinstance(driver.get("loop_checkpoint"), dict)
                else None
            ),
            "ledger_actionability_metrics": ledger.get("actionability_metrics", {}),
            "memory": _memory_summary(memory),
        },
        "classifications": _classifications(driver, ledger),
        "patch_hypotheses": hypotheses,
        "tool_defect_candidates": _tool_defect_candidates(driver, ledger),
        "next_recommended_operation": next_operation,
        "safety": {
            "source_mutation": "forbidden_in_plan_mode",
            "accepted_golden_release_mutation": "forbidden_without_explicit_human_approval",
            "writes": [],
        },
    }


def main(
    argv: list[str] | None = None,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent quality-search")
    parser.add_argument("name")
    parser.add_argument("--goal", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--max-iterations", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    fixture_identity.validate_fixture_name(args.name)
    name = args.name
    if args.execute:
        payload = {
            "schema": "figure-agent.quality-search-execute.v0",
            "fixture": name,
            "goal": args.goal,
            "status": "blocked",
            "reason": "execute_not_implemented",
            "max_iterations": args.max_iterations,
            "writes": [],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = build_quality_search_plan(
        name,
        goal=args.goal,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
