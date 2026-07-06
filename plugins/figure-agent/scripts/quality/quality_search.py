"""Plan a global quality-search step for one fixture.

This module is deliberately read-only. It observes the existing status, loop,
quality ledger, and memory surfaces, then separates progress blockers, quality
targets, release blockers, and likely tool defects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aesthetic_objective
import candidate_rank
import candidate_render
import candidate_review_packet
import candidate_visual_eval
import convergence_controller
import convergence_models
import experience_log
import fig_driver
import fixture_identity
import journal_guide
import quality_defect_ledger
import quality_memory_index
import runtime_paths
import semantic_candidate_review

SCHEMA = "figure-agent.quality-search-plan.v0"
EXECUTE_SCHEMA = "figure-agent.quality-search-execute.v0"
ZERO_HASH = "sha256:" + "0" * 64
DEPONE_PLAN_SCHEMA = "0.5"
DEPONE_EVIDENCE_CONTRACT_SCHEMA = "v105.verify_wedge"
SEARCH_POLICY_SCHEMA = "figure-agent.quality-search-bandit-policy.v1"
BANDIT_POLICY_KIND = "epsilon_greedy_family_bandit_v1"
BANDIT_EPSILON = 0.15
BANDIT_SELECTED_ARM_BONUS = 0.07

PROGRESS_ACTIONS = {
    "create_or_fix_source",
    "run_compile",
    "run_critique",
    "run_adjudicate",
    "run_fig_loop",
    "run_export",
}
FAMILY_REGISTRY_SCHEMA = "figure-agent.quality-search-family-registry.v0"
APPARATUS_PANEL_F_TEMPLATE_ID = "v5f_panel_f_redraw_overlay_v1"
APPARATUS_PANEL_F_REFRESH_TEMPLATE_ID = "v5f_panel_f_redraw_overlay_refresh_v1"
PANEL_F_BOUNDARY_POLISH_TEMPLATE_ID = "v5f_panel_f_boundary_polish_v1"
PANEL_F_FINAL_FINISH_TEMPLATE_ID = "v5f_panel_f_final_finish_v1"
PANEL_F_LABEL_ROUTE_FINISH_TEMPLATE_ID = "v5f_panel_f_label_route_finish_v1"
PANEL_F_DENSITY_RELIEF_TEMPLATE_ID = "v5f_panel_f_density_relief_v1"
PANEL_F_QTR_LABEL_LANE_TEMPLATE_ID = "v5d_panel_f_qtr_label_lane_v1"
PANEL_F_V5F_QTR_LABEL_LANE_TEMPLATE_ID = "v5f_panel_f_qtr_label_lane_v1"
PANEL_F_V5F_QTR_LABEL_LANE_V2_TEMPLATE_ID = "v5f_panel_f_qtr_label_lane_v2"
PANEL_F_QTR_APPARATUS_LANE_TEMPLATE_ID = "v5d_panel_f_qtr_apparatus_lane_v1"
PANEL_F_FORCE_GAP_LANE_TEMPLATE_ID = "v5d_panel_f_force_gap_lane_v1"
PANEL_F_MECHANICAL_ANCHOR_LANE_TEMPLATE_ID = "v5d_panel_f_mechanical_anchor_lane_v1"
PANEL_F_LEADER_LEFT_LANE_TEMPLATE_ID = "v5d_panel_f_leader_left_lane_v1"
PANEL_F_ELECTRODE_LEAD_LANE_TEMPLATE_ID = "v5d_panel_f_electrode_lead_lane_v1"
PANEL_F_ELECTRODE_CONNECTOR_TEMPLATE_ID = "v5f_panel_f_electrode_connector_v1"
PANEL_F_AUTO_COMPOSITE_LANE_TEMPLATE_ID = "v5d_panel_f_auto_composite_force_anchor_v1"
PANEL_F_AUTO_COMPOSITE_ELECTRODE_TEMPLATE_ID = (
    "v5d_panel_f_auto_composite_force_anchor_electrode_v1"
)
PANEL_C_HERO_FINISH_TEMPLATE_ID = "v5f_panel_c_hero_finish_v1"
DENSITY_PANEL_E_TEMPLATE_ID = "row2_panel_e_density_reduce_v1"
LINE_WIDTH_TEMPLATE_ID = "line_width_minimum_v1"
APPARATUS_PANEL_F_OVERLAY_MARKER = "v5f Panel F art-direction redraw overlay"
NON_MARGINAL_FULL_CHANGED_PIXEL_RATIO = 0.002
NON_MARGINAL_PANEL_CHANGED_PIXEL_RATIO = 0.02
NON_MARGINAL_REVIEW_CANDIDATE_STATE = "non_marginal_review_candidate_ready"
NON_MARGINAL_REVIEW_NEXT_ACTION = "review selected candidate evidence"
PANEL_MARKER_RE = re.compile(
    r"^\s*%\s*(?:=+\s*)?(?:Panel|Column)\s+([A-Za-z0-9_-]+)\b"
)
QUALITY_SEARCH_FAMILY_REGISTRY = {
    "hierarchy_rebalance": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "localized trap model",
            "mobility edge",
            "shallow",
            "deep",
            "real space",
            "energy diagram",
            "Debye",
            "Coulomb",
            "repulsion",
        ],
        "design_moves": [
            "make Panel C the first-read hero",
            "separate Row 2 into kinetic, ISPD, and mechanical evidence modes",
            "foreground result/mechanism before apparatus details",
        ],
        "render_targets": [
            "full",
            "print_thumbnail",
            "panel_C",
            "panel_D",
            "panel_E",
            "panel_F",
        ],
    },
    "panel_c_hero_finish": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "localized trap model",
            "mobility edge",
            "shallow",
            "deep",
            "real space",
            "energy diagram",
            "poly(S-r-DIB) thin film",
            "$\\Delta E_t$",
        ],
        "design_moves": [
            "make Panel C the first-read hero without changing labels",
            "strengthen DOS and trap-level evidence before row-2 apparatus detail",
            "quiet companion labels while preserving the real-space/energy-diagram split",
        ],
        "render_targets": ["full", "print_thumbnail", "panel_C"],
    },
    "apparatus_strengthen": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
            "mechanical",
        ],
        "design_moves": [
            "redraw charge, force, electrode, and air-gap relation as one mechanism",
            "keep the Coulomb response visually stronger than the bias source",
            "make apparatus read as deliberate instrument geometry, not boxes",
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "panel_f_boundary_polish": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
            "mechanical",
        ],
        "design_moves": [
            "keep the trapped-charge label in the left reading lane without clipping",
            "route the trapped-charge leader around the cantilever instead of through it",
            "reduce Panel F boundary density while preserving Coulomb/electrode/air-gap semantics",
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "panel_f_final_finish": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
            "mechanical",
        ],
        "design_moves": [
            "make the bias module a quiet circuit cue instead of a boxy subject",
            "route the apparatus lead as an intentional connection into the electrode",
            (
                "keep trapped-charge typography in the left reading lane with a leader "
                "above the cantilever"
            ),
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "panel_f_label_route_finish": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
            "mechanical",
        ],
        "design_moves": [
            "pull the trapped-charge label into a left label rail without crop clipping",
            "shorten the trapped-charge leader so it does not sweep across the cantilever",
            "make the bias-source lead a restrained vertical connection into the electrode",
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "panel_f_density_relief": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
            "mechanical",
        ],
        "design_moves": [
            "thin the Panel F field-line and electrode-hatch density without deleting semantics",
            "make Coulomb/repulsion typography secondary to the charge trajectory",
            "preserve the air-gap and electrode relation while reducing print-scale crowding",
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "panel_f_qtr_label_lane": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
        ],
        "design_moves": [
            "give q_tr a dedicated label lane instead of enlarging the inline mark",
            "add trapped-charge wording without renaming the charge quantity",
            "keep the leader short and outside the cantilever body",
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "panel_f_qtr_apparatus_lane": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
            "mechanical",
            "$V_{\\mathrm{active}}$",
        ],
        "design_moves": [
            "move q_tr and trapped-charge text into a left label lane",
            "quiet the PSU box so Coulomb response remains the first read",
            "route the PSU lead into the electrode as an instrument connection",
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "panel_f_force_gap_lane": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
            "mechanical",
        ],
        "design_moves": [
            "make the Coulomb arrow and repulsion label read before apparatus boxes",
            "mark the electrode face as the opposing mechanical boundary",
            (
                "raise the air-gap bracket into the force/electrode relation "
                "instead of leaving it as a baseline ruler"
            ),
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "panel_f_mechanical_anchor_lane": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
            "mechanical",
        ],
        "design_moves": [
            "make the clamp/root geometry read as the fixed mechanical anchor",
            "separate the cantilever root from the apparatus box and electrode",
            "keep trapped-charge and force labels visible while strengthening the support",
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "panel_f_leader_left_lane": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
            "mechanical",
        ],
        "design_moves": [
            "move the trapped-charge label into the left reading lane",
            "route the q_tr leader above the cantilever instead of across its body",
            "keep Coulomb, electrode, and air-gap labels stable while fixing label flow",
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "panel_f_electrode_lead_lane": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
            "mechanical",
        ],
        "design_moves": [
            "make the source-to-electrode lead read as one intentional connection",
            "add a clear electrode contact landing instead of a box-wire collision",
            "keep the bottom electrode visually distinct from the source apparatus",
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "panel_f_auto_composite_lane": {
        "builder": "panel_region_composite_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "q_tr",
            "trapped charge",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
            "mechanical",
        ],
        "design_moves": [
            "compose previously verified Panel F transforms into a fresh bounded candidate",
            "move force-gap and mechanical-anchor evidence together instead of one lane at a time",
            "keep source mutation blocked while exploring larger visual movement",
        ],
        "render_targets": ["full", "print_thumbnail", "panel_F"],
    },
    "density_reduce": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "mobility edge",
            "shallow",
            "deep",
            "$I(t)\\!\\sim\\!t^{-n}$",
            "Debye",
            "$g(E_t)$",
            "trapped charge",
            "Coulomb",
            "air gap",
        ],
        "design_moves": [
            "merge or remove repeated micro-labels",
            "reduce secondary decoration before changing science labels",
            "preserve print-scale labels that carry the manuscript claim",
        ],
        "render_targets": [
            "full",
            "print_thumbnail",
            "panel_C",
            "panel_E",
            "panel_F",
        ],
    },
}


def _utc_stamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_id(name: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{name}"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing to write through symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ValueError(f"refusing to write inside symlink directory: {path.parent}")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, payload: str) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing to write through symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ValueError(f"refusing to write inside symlink directory: {path.parent}")
    path.write_text(payload, encoding="utf-8")


def _ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError(f"refusing to write inside symlink directory: {path}")


def _workspace_relative(paths: runtime_paths.RuntimePaths, path: Path) -> str:
    try:
        return path.resolve().relative_to(paths.workspace_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"quality-search evidence escaped workspace: {path}") from exc


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
        if "QTR" in parts and "F" not in panels:
            panels.append("F")
    return panels


def _unlinked_micro_defect_ids(driver: dict[str, Any]) -> list[str]:
    audit = driver.get("audit_evidence")
    feedback = audit.get("detector_feedback") if isinstance(audit, dict) else None
    ids = feedback.get("unlinked_micro_defect_ids") if isinstance(feedback, dict) else None
    if not isinstance(ids, list):
        return []
    return [item for item in ids if isinstance(item, str) and item.strip()]


def _allows_stale_critique_search(
    driver: dict[str, Any],
    *,
    allow_stale_critique_search: bool,
) -> bool:
    if not allow_stale_critique_search:
        return False
    if str(driver.get("action") or "") != "run_critique":
        return False
    status = driver.get("status")
    critique_state = (
        str(status.get("critique_state") or "").upper()
        if isinstance(status, dict)
        else ""
    )
    return critique_state == "STALE"


def _classifications(
    driver: dict[str, Any],
    ledger: dict[str, Any],
    *,
    allow_stale_critique_search: bool = False,
) -> list[dict[str, Any]]:
    classifications: list[dict[str, Any]] = []
    action = str(driver.get("action") or "")
    if action in PROGRESS_ACTIONS:
        bypass_search_block = _allows_stale_critique_search(
            driver,
            allow_stale_critique_search=allow_stale_critique_search,
        )
        classifications.append(
            {
                "kind": "progress_blocker",
                "id": action,
                "blocks_search": not bypass_search_block,
                "blocks_release": True,
                "safe_command": driver.get("safe_command"),
                "reason": driver.get("reason"),
                **(
                    {
                        "diagnostic_bypass": "stale_critique_search",
                        "bypass_scope": "candidate_generation_only_no_release_authority",
                    }
                    if bypass_search_block
                    else {}
                ),
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
                "family": "panel_c_hero_finish",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["C"],
                    "reason": (
                        "make the localized trap model the Row 2 first-read "
                        "mechanism before smaller apparatus evidence"
                    ),
                },
                "expected_visual_movement": (
                    "Panel C reads as the Row 2 hero with stronger trap-landscape "
                    "DOS and level evidence"
                ),
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
                "family": "panel_f_final_finish",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "reason": (
                        "post-redraw Panel F still has typography-authority and "
                        "apparatus-lead finish defects"
                    ),
                },
                "expected_visual_movement": (
                    "Panel F bias module, lead routing, and trapped-charge typography "
                    "read as a finished mechanism composition"
                ),
            },
            {
                **common,
                "family": "panel_f_label_route_finish",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "reason": (
                        "post-final Panel F still clips the trapped-charge label "
                        "and leaves the bias lead too box-like"
                    ),
                },
                "expected_visual_movement": (
                    "Panel F trapped-charge callout sits inside the left label rail "
                    "with a shorter leader and cleaner bias-electrode lead"
                ),
            },
            {
                **common,
                "family": "panel_f_density_relief",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "reason": (
                        "Panel F remains the densest mechanism zone after label-route "
                        "finish; reduce field-line, hatch, and force-label dominance"
                    ),
                },
                "expected_visual_movement": (
                    "Panel F keeps charge/force/electrode semantics but reads less crowded "
                    "at print scale"
                ),
            },
            {
                **common,
                "family": "panel_f_boundary_polish",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "reason": (
                        "move the trapped-charge callout off the left boundary and "
                        "route the leader around the cantilever"
                    ),
                },
                "expected_visual_movement": (
                    "Panel F trapped-charge callout has breathing room and a cleaner leader"
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


def _goal_requests_panel_f_apparatus(goal: str) -> bool:
    normalized = " ".join(goal.lower().replace("_", " ").replace("-", " ").split())
    panel_f = "panel f" in normalized or "column f" in normalized
    apparatus_terms = {
        "apparatus",
        "charge",
        "force",
        "electrode",
        "air gap",
        "coulomb",
        "mechanical",
    }
    return panel_f and any(term in normalized for term in apparatus_terms)


def _goal_hypotheses(name: str, goal: str) -> list[dict[str, Any]]:
    if not _goal_requests_panel_f_apparatus(goal):
        return []
    hypotheses = [
        {
            "fixture": name,
            "family": "apparatus_strengthen",
            "source": "goal_directive",
            "mutation_allowed": False,
            "mutation_block_reason": "quality-search v0 is planner-only",
            "target_scope": "panel",
            "target_hint": {
                "panels": ["F"],
                "reason": (
                    "goal explicitly requests Panel F apparatus/charge/electrode/air-gap "
                    "movement"
                ),
            },
            "expected_detector_movement": (
                "convert apparatus-local feedback into a bounded Panel F mechanism redraw"
            ),
            "expected_visual_movement": (
                "Panel F apparatus reads as deliberate mechanism evidence"
            ),
            "rollback_condition": (
                "candidate worsens compile, semantics, or print-legibility evidence"
            ),
        }
    ]
    normalized = goal.casefold()
    if any(term in normalized for term in ("electrode", "lead", "connector", "wire")):
        hypotheses.append(
            {
                "fixture": name,
                "family": "panel_f_electrode_lead_lane",
                "source": "goal_directive",
                "mutation_allowed": False,
                "mutation_block_reason": "quality-search v0 is planner-only",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "reason": (
                        "goal explicitly requests source-to-electrode lead and "
                        "apparatus connector movement"
                    ),
                },
                "expected_detector_movement": (
                    "convert apparatus/electrode connector feedback into a bounded "
                    "Panel F lead-routing candidate"
                ),
                "expected_visual_movement": (
                    "Panel F source-to-electrode connection reads as one intentional "
                    "electrical path instead of a box-wire collision"
                ),
                "rollback_condition": (
                    "candidate worsens compile, protected labels, or electrode/air-gap semantics"
                ),
            }
        )
    return hypotheses


def _memory_attempt_count(
    memory: dict[str, Any],
    family: str,
    template_id: str | None = None,
) -> int:
    if template_id:
        templates = (
            memory.get("family_templates")
            if isinstance(memory.get("family_templates"), dict)
            else {}
        )
        entry = templates.get(f"{family}::{template_id}") if isinstance(templates, dict) else None
    else:
        families = memory.get("families") if isinstance(memory.get("families"), dict) else {}
        entry = families.get(family) if isinstance(families, dict) else None
    if not isinstance(entry, dict):
        return 0
    return _bounded_int(entry.get("attempts"), default=0)


def _stale_goal_escalation_hypotheses(
    name: str,
    goal: str,
    memory: dict[str, Any] | None,
    existing_hypotheses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(memory, dict) or not _goal_requests_panel_f_apparatus(goal):
        return []
    duplicate_rate = _bounded_float(
        memory.get("duplicate_experience_attempt_rate"),
        default=0.0,
        lower=0.0,
        upper=1.0,
    )
    if duplicate_rate < 0.5:
        return []
    existing_families = {
        str(item.get("family") or "")
        for item in existing_hypotheses
        if isinstance(item, dict)
    }
    apparatus_attempts = _memory_attempt_count(memory, "apparatus_strengthen")
    if apparatus_attempts <= 0 or "apparatus_strengthen" not in existing_families:
        return []
    common = {
        "fixture": name,
        "source": "stale_goal_memory_escalation",
        "mutation_allowed": False,
        "mutation_block_reason": "quality-search v0 is planner-only",
        "target_scope": "panel",
        "expected_detector_movement": (
            "escape repeated Panel F apparatus-strengthen candidates after "
            "convergence stop/defer evidence"
        ),
        "rollback_condition": (
            "candidate worsens compile, protected labels, or Panel F mechanism semantics"
        ),
    }
    return [
        {
            **common,
            "family": "panel_f_qtr_label_lane",
            "target_hint": {
                "panels": ["F"],
                "reason": (
                    "apparatus_strengthen is stale; move charge-trapping notation "
                    "into a fresh left-label lane"
                ),
            },
            "expected_visual_movement": (
                "q_tr and trapped-charge label move toward the left reading lane "
                "with less cantilever crossing"
            ),
        },
        {
            **common,
            "family": "panel_f_leader_left_lane",
            "target_hint": {
                "panels": ["F"],
                "reason": (
                    "apparatus_strengthen is stale; reroute the trapped-charge "
                    "leader away from the cantilever body"
                ),
            },
            "expected_visual_movement": (
                "trapped-charge leader becomes shorter and avoids cutting across the beam"
            ),
        },
        {
            **common,
            "family": "panel_f_electrode_lead_lane",
            "target_hint": {
                "panels": ["F"],
                "reason": (
                    "apparatus_strengthen is stale; make a fresh source-to-electrode "
                    "connection candidate"
                ),
            },
            "expected_visual_movement": (
                "equipment source connects to the electrode through a clear contact path"
            ),
        },
        {
            **common,
            "family": "panel_f_auto_composite_lane",
            "target_hint": {
                "panels": ["F"],
                "reason": (
                    "single apparatus redraw is stale; compose charge, force-gap, "
                    "and mechanical-anchor changes into a fresh bounded candidate"
                ),
                "composite_sequence": [
                    "panel_f_qtr_label_lane",
                    "panel_f_force_gap_lane",
                    "panel_f_mechanical_anchor_lane",
                ],
            },
            "expected_visual_movement": (
                "charge label, Coulomb force, electrode/air-gap, and mechanical support "
                "move together instead of redrawing only the box"
            ),
        },
    ]


def _micro_defect_hypotheses(name: str, driver: dict[str, Any]) -> list[dict[str, Any]]:
    ids = _unlinked_micro_defect_ids(driver)
    normalized = {item.upper() for item in ids}
    hypotheses: list[dict[str, Any]] = []
    if any("QTR" in item for item in normalized):
        hypotheses.append(
            {
                "fixture": name,
                "family": "panel_f_qtr_apparatus_lane",
                "source": "unlinked_micro_defect",
                "mutation_allowed": False,
                "mutation_block_reason": "quality-search v0 is planner-only",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "micro_defect_ids": ids,
                    "reason": (
                        "Panel F q_tr typography and apparatus lead geometry should "
                        "move together so the charge-force-electrode relation reads "
                        "before the equipment box"
                    ),
                },
                "expected_detector_movement": (
                    "convert unlinked q_tr micro-defect plus apparatus awkwardness "
                    "into a bounded Panel F block candidate"
                ),
                "expected_visual_movement": (
                    "Panel F reads as trapped charge driving Coulomb response into "
                    "the electrode/air-gap apparatus"
                ),
                "rollback_condition": (
                    "candidate worsens compile, protected labels, or Panel F print-legibility"
                ),
            }
        )
        hypotheses.append(
            {
                "fixture": name,
                "family": "panel_f_qtr_label_lane",
                "source": "unlinked_micro_defect",
                "mutation_allowed": False,
                "mutation_block_reason": "quality-search v0 is planner-only",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "micro_defect_ids": ids,
                    "reason": (
                        "Panel F q_tr typography is weak at print scale; make a "
                        "dedicated trapped-charge label lane before asking for "
                        "human art-direction review"
                    ),
                },
                "expected_detector_movement": (
                    "convert unlinked q_tr micro-defect into a bounded Panel F candidate"
                ),
                "expected_visual_movement": (
                    "q_tr reads as an authoritative trapped-charge notation at "
                    "thumbnail scale"
                ),
                "rollback_condition": (
                    "candidate worsens compile, protected labels, or Panel F print-legibility"
                ),
            }
        )
        hypotheses.append(
            {
                "fixture": name,
                "family": "panel_f_force_gap_lane",
                "source": "unlinked_micro_defect",
                "mutation_allowed": False,
                "mutation_block_reason": "quality-search v0 is planner-only",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "micro_defect_ids": ids,
                    "reason": (
                        "Panel F needs a fresh Coulomb/repulsion/electrode/air-gap "
                        "candidate after q_tr label and apparatus lanes are exhausted"
                    ),
                },
                "expected_detector_movement": (
                    "convert stale q_tr loop evidence into a bounded Panel F force-gap candidate"
                ),
                "expected_visual_movement": (
                    "Coulomb repulsion reads as acting across the air gap toward the electrode"
                ),
                "rollback_condition": (
                    "candidate worsens compile, protected labels, or Panel F "
                    "force/electrode semantics"
                ),
            }
        )
        hypotheses.append(
            {
                "fixture": name,
                "family": "panel_f_mechanical_anchor_lane",
                "source": "unlinked_micro_defect",
                "mutation_allowed": False,
                "mutation_block_reason": "quality-search v0 is planner-only",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "micro_defect_ids": ids,
                    "reason": (
                        "Panel F still needs a fresh mechanical anchor/root candidate "
                        "after charge label, apparatus, and force-gap lanes are exhausted"
                    ),
                },
                "expected_detector_movement": (
                    "convert stale Panel F mechanism evidence into a bounded "
                    "mechanical-anchor candidate"
                ),
                "expected_visual_movement": (
                    "cantilever root reads as fixed mechanical support before the bend"
                ),
                "rollback_condition": (
                    "candidate worsens compile, protected labels, or mechanical support semantics"
                ),
            }
        )
        hypotheses.append(
            {
                "fixture": name,
                "family": "panel_f_leader_left_lane",
                "source": "unlinked_micro_defect",
                "mutation_allowed": False,
                "mutation_block_reason": "quality-search v0 is planner-only",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "micro_defect_ids": ids,
                    "reason": (
                        "Panel F needs a fresh trapped-charge leader candidate after "
                        "apparatus, label, force-gap, and mechanical-anchor lanes are stale"
                    ),
                },
                "expected_detector_movement": (
                    "convert stale Panel F q_tr evidence into a bounded leader-routing candidate"
                ),
                "expected_visual_movement": (
                    "trapped-charge label sits in the left reading lane with a shorter "
                    "leader that avoids the cantilever body"
                ),
                "rollback_condition": (
                    "candidate worsens compile, protected labels, or charge-leader semantics"
                ),
            }
        )
        hypotheses.append(
            {
                "fixture": name,
                "family": "panel_f_electrode_lead_lane",
                "source": "unlinked_micro_defect",
                "mutation_allowed": False,
                "mutation_block_reason": "quality-search v0 is planner-only",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "micro_defect_ids": ids,
                    "reason": (
                        "Panel F needs a fresh source-to-electrode lead candidate after "
                        "charge, force, anchor, and leader lanes are stale"
                    ),
                },
                "expected_detector_movement": (
                    "convert stale Panel F apparatus evidence into a bounded lead-routing candidate"
                ),
                "expected_visual_movement": (
                    "bias source connects to the electrode through a clear contact landing"
                ),
                "rollback_condition": (
                    "candidate worsens compile, protected labels, or electrode-lead semantics"
                ),
            }
        )
        hypotheses.append(
            {
                "fixture": name,
                "family": "panel_f_auto_composite_lane",
                "source": "unlinked_micro_defect",
                "mutation_allowed": False,
                "mutation_block_reason": "quality-search v0 is planner-only",
                "target_scope": "panel",
                "target_hint": {
                    "panels": ["F"],
                    "micro_defect_ids": ids,
                    "reason": (
                        "Panel F single-lane candidates are stale; compose force-gap "
                        "and mechanical-anchor transforms into a fresh bounded candidate"
                    ),
                    "composite_sequence": [
                        "panel_f_force_gap_lane",
                        "panel_f_mechanical_anchor_lane",
                    ],
                },
                "expected_detector_movement": (
                    "step out from stale single-lane families into a bounded composite candidate"
                ),
                "expected_visual_movement": (
                    "Coulomb/electrode/air-gap relation and fixed mechanical support move together"
                ),
                "rollback_condition": (
                    "candidate worsens compile, protected labels, or composite Panel F semantics"
                ),
            }
        )
    return hypotheses


def _merge_hypotheses(
    primary: list[dict[str, Any]],
    fallback: list[dict[str, Any]],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in [*primary, *fallback]:
        family = str(item.get("family") or "")
        if not family or family in seen:
            continue
        seen.add(family)
        merged.append(item)
        if len(merged) >= limit:
            break
    return merged


def _patch_hypotheses(
    name: str,
    driver: dict[str, Any],
    ledger: dict[str, Any],
    *,
    goal: str = "",
    allow_stale_critique_search: bool = False,
) -> list[dict[str, Any]]:
    if str(driver.get("action") or "") in PROGRESS_ACTIONS and not _allows_stale_critique_search(
        driver,
        allow_stale_critique_search=allow_stale_critique_search,
    ):
        return []
    basin_hypotheses = _step_out_hypotheses(name, driver, ledger)
    micro_hypotheses = _micro_defect_hypotheses(name, driver)
    if basin_hypotheses:
        if micro_hypotheses:
            return _merge_hypotheses(micro_hypotheses, basin_hypotheses, limit=8)
        return basin_hypotheses[:8]
    if micro_hypotheses:
        return _merge_hypotheses(
            micro_hypotheses,
            _merge_hypotheses(
                _goal_hypotheses(name, goal),
                _detector_hypotheses(name, ledger),
                limit=4,
            ),
            limit=7,
        )
    goal_hypotheses = _goal_hypotheses(name, goal)
    if goal_hypotheses:
        return _merge_hypotheses(
            goal_hypotheses,
            _detector_hypotheses(name, ledger),
            limit=3,
        )
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
    stop_routes = loop.get("stop_routes")
    if isinstance(stop_routes, list):
        exhausted = [
            route
            for route in stop_routes
            if isinstance(route, dict) and route.get("stop_cause") == "lever_exhausted"
        ]
        if exhausted:
            candidates.append(
                {
                    "id": f"TD{len(candidates) + 1:03d}",
                    "symptom": "candidate family is exhausted for a loop subregion",
                    "expected_behavior": (
                        "lever_exhausted stop routes should become explicit tool work "
                        "instead of silent no-op loop termination"
                    ),
                    "actual_behavior": {"stop_routes": exhausted},
                    "minimal_reproduction": "fig-agent loop <fixture> --goal <goal> --json",
                    "recommended_fix": (
                        "add or widen the missing candidate family named by the stop route "
                        "payload, then rerun quality-search"
                    ),
                }
            )
    diagnosis = loop.get("stop_diagnosis")
    histogram = diagnosis.get("cause_histogram") if isinstance(diagnosis, dict) else {}
    decision_weak_count = (
        int(histogram.get("decision_weak") or 0) if isinstance(histogram, dict) else 0
    )
    auto_remedy = loop.get("auto_remedy") if isinstance(loop.get("auto_remedy"), dict) else {}
    remedy_ineffective = auto_remedy.get("status") == "remedy_ineffective"
    if decision_weak_count >= 2 or remedy_ineffective:
        candidates.append(
            {
                "id": f"TD{len(candidates) + 1:03d}",
                "symptom": "decision_weak stop recurred after the loop had diagnostic evidence",
                "expected_behavior": (
                    "repeated decision_weak or ineffective plumbing remedies should be "
                    "tracked as tool defects"
                ),
                "actual_behavior": {
                    "decision_weak_count": decision_weak_count,
                    "auto_remedy": auto_remedy,
                },
                "minimal_reproduction": "fig-agent loop <fixture> --goal <goal> --json",
                "recommended_fix": (
                    "repair detector evidence routing or the auto-remedy path before "
                    "spending more iterations on candidate scoring"
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
        "counterfactual_unchosen_count": memory.get("counterfactual_unchosen_count"),
        "duplicate_experience_attempt_count": memory.get(
            "duplicate_experience_attempt_count"
        ),
        "duplicate_experience_attempt_rate": memory.get(
            "duplicate_experience_attempt_rate"
        ),
        "families": memory.get("families", {}),
        "family_templates": memory.get("family_templates", {}),
    }


def _bandit_unit_interval(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) / float(16**16)


def _unique_families(families: list[Any]) -> list[str]:
    ordered: list[str] = []
    for family in families:
        value = str(family or "")
        if not value or value == "null_baseline" or value in ordered:
            continue
        ordered.append(value)
    return ordered


def _arm_statistics(plan: dict[str, Any], families: list[str]) -> dict[str, dict[str, Any]]:
    arms: dict[str, dict[str, Any]] = {}
    for family in families:
        memory = _family_memory(plan, family)
        attempts = _bounded_int(memory.get("attempts"), default=0)
        improved = _bounded_int(memory.get("improved"), default=0)
        neutral = _bounded_int(memory.get("neutral"), default=0)
        regressed = _bounded_int(memory.get("regressed"), default=0)
        empirical_reward = (
            (improved + 0.5 * neutral) / attempts if attempts > 0 else 0.5
        )
        arms[family] = {
            "attempts": attempts,
            "improved": improved,
            "neutral": neutral,
            "regressed": regressed,
            "empirical_reward": round(
                _bounded_float(empirical_reward, default=0.5, lower=0.0, upper=1.0),
                4,
            ),
            "recommended_prior": _memory_prior(plan, family),
            "base_evidence_weight": _family_evidence_weight(family, plan),
        }
    return arms


def _best_exploit_arm(arms: dict[str, dict[str, Any]]) -> str | None:
    if not arms:
        return None
    return max(
        arms,
        key=lambda family: (
            float(arms[family].get("empirical_reward") or 0.0),
            float(arms[family].get("recommended_prior") or 0.0),
            float(arms[family].get("base_evidence_weight") or 0.0),
            family,
        ),
    )


def _best_explore_arm(arms: dict[str, dict[str, Any]]) -> str | None:
    if not arms:
        return None
    return min(
        arms,
        key=lambda family: (
            int(arms[family].get("attempts") or 0),
            -float(arms[family].get("base_evidence_weight") or 0.0),
            family,
        ),
    )


def _epsilon_greedy_bandit_decision(
    plan: dict[str, Any],
    families: list[Any],
    *,
    epsilon: float = BANDIT_EPSILON,
) -> dict[str, Any]:
    epsilon = _bounded_float(epsilon, default=BANDIT_EPSILON, lower=0.0, upper=1.0)
    arms = _arm_statistics(plan, _unique_families(families))
    seed = json.dumps(
        {
            "operation": (plan.get("next_recommended_operation") or {}).get("kind"),
            "families": sorted(arms),
            "eligible_prior_count": (
                (plan.get("state") or {}).get("memory", {}).get("eligible_prior_count")
                if isinstance((plan.get("state") or {}).get("memory"), dict)
                else None
            ),
        },
        sort_keys=True,
    )
    draw = _bandit_unit_interval(seed) if arms else 1.0
    selection_mode = "explore" if arms and draw < epsilon else "exploit"
    selected_family = (
        _best_explore_arm(arms) if selection_mode == "explore" else _best_exploit_arm(arms)
    )
    return {
        "schema": SEARCH_POLICY_SCHEMA,
        "kind": BANDIT_POLICY_KIND,
        "algorithm": "deterministic_epsilon_greedy",
        "epsilon": epsilon,
        "draw": round(draw, 6),
        "selection_mode": selection_mode,
        "selected_family": selected_family,
        "arm_statistics": arms,
        "statistics_source": "experience_log_via_quality_memory_index",
        "opaque_model_dependency": False,
    }


def _search_policy_descriptor(
    next_operation: dict[str, Any],
    memory: dict[str, Any] | None,
) -> dict[str, Any]:
    candidate_families = next_operation.get("candidate_families")
    if not isinstance(candidate_families, list):
        candidate_families = []
    plan = {
        "state": {"memory": _memory_summary(memory)},
        "next_recommended_operation": next_operation,
    }
    bandit_decision = _epsilon_greedy_bandit_decision(plan, candidate_families)
    return {
        "schema": SEARCH_POLICY_SCHEMA,
        "kind": BANDIT_POLICY_KIND,
        "operation_kind": next_operation.get("kind"),
        "selection_score": (
            "base_evidence_score + memory_prior + bandit_bonus "
            "+ render_adjustment + render_penalty"
        ),
        "exploitation_inputs": [
            "candidate_family_priority",
            "fixture_quality_memory_prior",
            "experience_log_arm_empirical_reward",
            "candidate_render_rank_score",
        ],
        "exploration_inputs": [
            "epsilon_greedy_draw",
            "low_attempt_arm_selection",
        ],
        "epsilon": BANDIT_EPSILON,
        "bandit_decision": bandit_decision,
        "mutation_boundary": "review_only_until_explicit_apply_gate",
    }


def build_quality_search_plan(
    name: str,
    *,
    goal: str,
    allow_stale_critique_search: bool = False,
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
    hypotheses = _patch_hypotheses(
        name,
        driver,
        ledger,
        goal=goal,
        allow_stale_critique_search=allow_stale_critique_search,
    )
    stale_goal_hypotheses = _stale_goal_escalation_hypotheses(
        name,
        goal,
        memory,
        hypotheses,
    )
    if stale_goal_hypotheses:
        hypotheses = _merge_hypotheses(hypotheses, stale_goal_hypotheses, limit=8)
    basin = _loop_basin(
        driver.get("loop_checkpoint") if isinstance(driver.get("loop_checkpoint"), dict) else None
    )
    prerequisite_blocks_search = str(
        driver.get("action") or ""
    ) in PROGRESS_ACTIONS and not _allows_stale_critique_search(
        driver,
        allow_stale_critique_search=allow_stale_critique_search,
    )
    if prerequisite_blocks_search:
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
        "classifications": _classifications(
            driver,
            ledger,
            allow_stale_critique_search=allow_stale_critique_search,
        ),
        "patch_hypotheses": hypotheses,
        "tool_defect_candidates": _tool_defect_candidates(driver, ledger),
        "next_recommended_operation": next_operation,
        "search_policy": _search_policy_descriptor(next_operation, memory),
        "safety": {
            "source_mutation": "forbidden_in_plan_mode",
            "accepted_golden_release_mutation": "forbidden_without_explicit_human_approval",
            "stale_critique_search_bypass": (
                "enabled_candidate_generation_only"
                if allow_stale_critique_search
                else "disabled"
            ),
            "writes": [],
        },
    }


def _sha256_text(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def _fixture_source_path(paths: runtime_paths.RuntimePaths, name: str) -> Path:
    return paths.workspace_root / "examples" / name / f"{name}.tex"


def _source_reference(name: str) -> str:
    return f"examples/{name}/{name}.tex"


def _is_structural_panel_marker(line: str) -> bool:
    match = PANEL_MARKER_RE.match(line)
    if match is None:
        return False
    marker = line.strip()
    lowered = marker.lower()
    if " iter " in lowered or " bbox" in lowered:
        return False
    return "===" in marker or "—" in marker or " - " in marker or " -- " in marker


def _panel_region_context(name: str, paths: runtime_paths.RuntimePaths) -> dict[str, Any]:
    source_path = _fixture_source_path(paths, name)
    source_ref = _source_reference(name)
    base = {
        "schema": FAMILY_REGISTRY_SCHEMA,
        "fixture": name,
        "source": source_ref,
        "selectors_by_panel": {},
    }
    if not source_path.exists():
        return {**base, "source_state": "missing", "source_hash": None}
    if source_path.is_symlink():
        return {**base, "source_state": "source_symlink_refused", "source_hash": None}
    resolved = source_path.resolve()
    fixture_dir = (paths.workspace_root / "examples" / name).resolve()
    try:
        resolved.relative_to(fixture_dir)
    except ValueError:
        return {**base, "source_state": "source_escaped_fixture", "source_hash": None}

    source_text = source_path.read_text(encoding="utf-8")
    lines = source_text.splitlines()
    source_hash = _sha256_text(source_text)
    markers: list[tuple[str, int, str]] = []
    for index, line in enumerate(lines):
        if not _is_structural_panel_marker(line):
            continue
        match = PANEL_MARKER_RE.match(line)
        if match is None:
            continue
        panel = match.group(1).upper()
        if not panel or panel == "LETTER":
            continue
        markers.append((panel, index, line.strip()))

    selectors: dict[str, dict[str, Any]] = {}
    for marker_index, (panel, start_index, marker) in enumerate(markers):
        next_start = (
            markers[marker_index + 1][1]
            if marker_index + 1 < len(markers)
            else len(lines)
        )
        selected_text = "\n".join(lines[start_index:next_start])
        selectors.setdefault(
            panel,
            {
                "kind": "quality_search_panel_region.v0",
                "path": source_ref,
                "panel": panel,
                "line_start": start_index + 1,
                "line_end": next_start,
                "marker": marker,
                "source_hash": source_hash,
                "selector_text_hash": _sha256_text(selected_text),
                "binding_state": "bound",
            },
        )
    return {
        **base,
        "source_state": "loaded",
        "source_hash": source_hash,
        "selector_count": len(selectors),
        "selectors_by_panel": selectors,
    }


def _target_panels_from_hint(hypothesis: dict[str, Any]) -> list[str]:
    target_hint = hypothesis.get("target_hint")
    panels: list[str] = []
    if isinstance(target_hint, dict):
        raw_panels = target_hint.get("panels")
        if isinstance(raw_panels, list):
            panels.extend(str(panel).upper() for panel in raw_panels if panel)
        targets = target_hint.get("representative_targets")
        if isinstance(targets, list):
            for target in targets:
                if isinstance(target, dict) and target.get("panel"):
                    panels.append(str(target["panel"]).upper())
    return sorted({panel for panel in panels if panel and panel != "UNKNOWN"})


def _family_registry_entry(family: str) -> dict[str, Any]:
    return QUALITY_SEARCH_FAMILY_REGISTRY.get(
        family,
        {
            "builder": "unregistered_family",
            "apply_authority": "review_only",
            "protected_labels": [],
            "design_moves": [],
            "render_targets": ["full", "print_thumbnail"],
        },
    )


def _source_selectors_for_panels(
    source_context: dict[str, Any],
    panels: list[str],
) -> list[dict[str, Any]]:
    selectors_by_panel = source_context.get("selectors_by_panel")
    if not isinstance(selectors_by_panel, dict):
        selectors_by_panel = {}
    selectors: list[dict[str, Any]] = []
    for panel in panels:
        selector = selectors_by_panel.get(panel)
        if isinstance(selector, dict):
            selectors.append(selector)
            continue
        selectors.append(
            {
                "kind": "quality_search_panel_region.v0",
                "panel": panel,
                "binding_state": "unbound",
                "reason": source_context.get("source_state") or "panel_region_not_found",
            }
        )
    return selectors


def _selector_binding_state(selectors: list[dict[str, Any]]) -> str:
    if not selectors:
        return "unbound"
    bound_count = sum(1 for selector in selectors if selector.get("binding_state") == "bound")
    if bound_count == len(selectors):
        return "bound"
    if bound_count:
        return "partial"
    return "unbound"


def _candidate_hash(payload: dict[str, Any]) -> str:
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return _sha256_text(stable)


def _preferred_operation_scale(family: str) -> str:
    if family == "apparatus_strengthen":
        return "panel_block"
    if family == "panel_c_hero_finish":
        return "panel_block"
    if family == "panel_f_boundary_polish":
        return "panel_block"
    if family == "panel_f_final_finish":
        return "panel_block"
    if family == "panel_f_label_route_finish":
        return "panel_block"
    if family == "panel_f_density_relief":
        return "panel_block"
    if family == "panel_f_qtr_label_lane":
        return "panel_block"
    if family == "panel_f_qtr_apparatus_lane":
        return "panel_block"
    if family == "panel_f_force_gap_lane":
        return "panel_block"
    if family == "panel_f_mechanical_anchor_lane":
        return "panel_block"
    if family == "panel_f_leader_left_lane":
        return "panel_block"
    if family == "panel_f_electrode_lead_lane":
        return "panel_block"
    if family == "panel_f_auto_composite_lane":
        return "panel_block"
    if family == "density_reduce":
        return "panel_block"
    if family == "null_baseline":
        return "baseline"
    return "local_style_token"


def _preferred_template_id(family: str) -> str:
    if family == "apparatus_strengthen":
        return APPARATUS_PANEL_F_TEMPLATE_ID
    if family == "panel_c_hero_finish":
        return PANEL_C_HERO_FINISH_TEMPLATE_ID
    if family == "panel_f_boundary_polish":
        return PANEL_F_BOUNDARY_POLISH_TEMPLATE_ID
    if family == "panel_f_final_finish":
        return PANEL_F_FINAL_FINISH_TEMPLATE_ID
    if family == "panel_f_label_route_finish":
        return PANEL_F_LABEL_ROUTE_FINISH_TEMPLATE_ID
    if family == "panel_f_density_relief":
        return PANEL_F_DENSITY_RELIEF_TEMPLATE_ID
    if family == "panel_f_qtr_label_lane":
        return PANEL_F_QTR_LABEL_LANE_TEMPLATE_ID
    if family == "panel_f_qtr_apparatus_lane":
        return PANEL_F_QTR_APPARATUS_LANE_TEMPLATE_ID
    if family == "panel_f_force_gap_lane":
        return PANEL_F_FORCE_GAP_LANE_TEMPLATE_ID
    if family == "panel_f_mechanical_anchor_lane":
        return PANEL_F_MECHANICAL_ANCHOR_LANE_TEMPLATE_ID
    if family == "panel_f_leader_left_lane":
        return PANEL_F_LEADER_LEFT_LANE_TEMPLATE_ID
    if family == "panel_f_electrode_lead_lane":
        return PANEL_F_ELECTRODE_LEAD_LANE_TEMPLATE_ID
    if family == "panel_f_auto_composite_lane":
        return PANEL_F_AUTO_COMPOSITE_LANE_TEMPLATE_ID
    if family == "density_reduce":
        return DENSITY_PANEL_E_TEMPLATE_ID
    if family == "null_baseline":
        return "null_baseline_v1"
    return LINE_WIDTH_TEMPLATE_ID


def _memory_template_attempts(
    plan: dict[str, Any],
    *,
    family: str,
    template_id: str,
) -> int:
    state = plan.get("state") if isinstance(plan.get("state"), dict) else {}
    memory = state.get("memory") if isinstance(state.get("memory"), dict) else {}
    family_templates = (
        memory.get("family_templates")
        if isinstance(memory.get("family_templates"), dict)
        else {}
    )
    entry = family_templates.get(f"{family}::{template_id}")
    if not isinstance(entry, dict):
        return 0
    return _bounded_int(entry.get("attempts"), default=0)


def _preferred_template_id_for_plan(family: str, plan: dict[str, Any]) -> str:
    preferred = _preferred_template_id(family)
    if family == "panel_f_qtr_label_lane":
        if (
            _memory_template_attempts(
                plan,
                family=family,
                template_id=PANEL_F_V5F_QTR_LABEL_LANE_TEMPLATE_ID,
            )
            > 0
            and _memory_template_attempts(
                plan,
                family=family,
                template_id=PANEL_F_V5F_QTR_LABEL_LANE_V2_TEMPLATE_ID,
            )
            <= 0
        ):
            return PANEL_F_V5F_QTR_LABEL_LANE_V2_TEMPLATE_ID
        return preferred
    if family != "panel_f_auto_composite_lane":
        return preferred
    if (
        _memory_template_attempts(
            plan,
            family=family,
            template_id=PANEL_F_AUTO_COMPOSITE_LANE_TEMPLATE_ID,
        )
        > 0
        and _memory_template_attempts(
            plan,
            family=family,
            template_id=PANEL_F_AUTO_COMPOSITE_ELECTRODE_TEMPLATE_ID,
        )
        <= 0
    ):
        return PANEL_F_AUTO_COMPOSITE_ELECTRODE_TEMPLATE_ID
    return preferred


def _line_width_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
    minimum_pt: float,
) -> tuple[str, str, int] | None:
    try:
        start = int(selector["line_start"])
        end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if start < 1 or end < start or end > len(lines):
        return None
    replacement: tuple[str, str, int] | None = None
    for offset, line in enumerate(lines[start - 1 : end], start=start):
        match = re.search(r"line width=(?P<value>\d+(?:\.\d+)?)pt", line)
        if match is None:
            continue
        value = float(match.group("value"))
        if value >= minimum_pt:
            continue
        replacement_value = f"{minimum_pt:.2f}".rstrip("0").rstrip(".")
        replacement_line = (
            line[: match.start()]
            + f"line width={replacement_value}pt"
            + line[match.end() :]
        )
        replacement = (line, replacement_line, offset)
    return replacement


def _panel_c_block_range(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[int, int] | None:
    if str(selector.get("panel") or "").upper() != "C":
        return None
    try:
        start = int(selector["line_start"])
        end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if start < 1 or end < start or end > len(lines):
        return None
    marker_index = None
    for index in range(start - 1, end):
        line = lines[index]
        if "Panel C" in line and "Localized traps" in line:
            marker_index = index
            break
    if marker_index is None:
        return None
    line_end = end
    for index in range(marker_index + 1, end):
        line = lines[index]
        if ("Row 2" in line and "NC main-text" in line) or (
            "Column F" in line and "Mechanical" in line
        ):
            line_end = index
            break
    return marker_index + 1, line_end


def _panel_c_hero_has_protected_labels(block: str) -> bool:
    lowered = block.lower()
    return all(
        (
            "localized trap model" in lowered,
            "mobility edge" in lowered,
            "shallow" in lowered,
            "deep" in lowered,
            "real space" in lowered,
            "energy diagram" in lowered,
            "poly(s-r-dib) thin film" in lowered,
            "$\\Delta E_t$" in block,
        )
    )


def _panel_c_hero_finish_template_applied(block: str) -> bool:
    required_fragments = (
        "\\fill[cBlue!16, opacity=0.26, rounded corners=1pt]",
        "\\fill[cRed!16, opacity=0.24, rounded corners=1pt]",
        "\\draw[cBlue!84!black, line width=0.68pt]",
        "\\draw[cRed!84!black, line width=0.72pt]",
        "line width=1.24pt, line cap=butt",
        "fontsize{7.4}{8.8}",
        "text=cGray!84!black] at (10.40, 8.95) {localized trap model};",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_c_hero_finish_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[str, str, int, int] | None:
    line_range = _panel_c_block_range(lines=lines, selector=selector)
    if line_range is None:
        return None
    line_start, line_end = line_range
    original = "".join(lines[line_start - 1 : line_end])
    if not _panel_c_hero_has_protected_labels(original):
        return None
    if _panel_c_hero_finish_template_applied(original):
        return None
    replacement = original
    replacements = (
        (
            "\\fill[cBlue!12, opacity=0.20, rounded corners=1pt] "
            "(10.38, 7.18) rectangle (13.55, 7.82);",
            "\\fill[cBlue!16, opacity=0.26, rounded corners=1pt] "
            "(10.38, 7.18) rectangle (13.55, 7.82);",
        ),
        (
            "\\fill[cRed!12, opacity=0.18, rounded corners=1pt] "
            "(10.38, 5.55) rectangle (13.55, 6.55);",
            "\\fill[cRed!16, opacity=0.24, rounded corners=1pt] "
            "(10.38, 5.55) rectangle (13.55, 6.55);",
        ),
        ("\\fill[cBlue!52, opacity=0.85]", "\\fill[cBlue!56, opacity=0.90]"),
        (
            "\\draw[cBlue!80!black, line width=0.60pt]",
            "\\draw[cBlue!84!black, line width=0.68pt]",
        ),
        ("\\fill[cRed!52, opacity=0.80]", "\\fill[cRed!56, opacity=0.86]"),
        (
            "\\draw[cRed!80!black, line width=0.65pt]",
            "\\draw[cRed!84!black, line width=0.72pt]",
        ),
        (
            "line width=1.15pt, line cap=butt",
            "line width=1.24pt, line cap=butt",
        ),
        (
            "text=cGray!65!black] at (8.35, 8.78) {real space};",
            "text=cGray!58!black] at (8.35, 8.78) {real space};",
        ),
        (
            "text=cGray!65!black] at (12.20, 8.78) {energy diagram};",
            "text=cGray!58!black] at (12.20, 8.78) {energy diagram};",
        ),
        ("fontsize{7}{8.4}", "fontsize{7.4}{8.8}"),
        (
            "text=cGray!78!black] at (10.40, 8.92) {localized trap model};",
            "text=cGray!84!black] at (10.40, 8.95) {localized trap model};",
        ),
    )
    for old, new in replacements:
        replacement = replacement.replace(old, new)
    if replacement == original:
        return None
    if not _panel_c_hero_has_protected_labels(replacement):
        return None
    return original, replacement, line_start, line_end


def _panel_f_overlay_range(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[int, int] | None:
    if str(selector.get("panel") or "").upper() != "F":
        return None
    try:
        start = int(selector["line_start"])
        end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if start < 1 or end < start or end > len(lines):
        return None
    marker_index = None
    for index in range(start - 1, end):
        if APPARATUS_PANEL_F_OVERLAY_MARKER in lines[index]:
            marker_index = index
            break
    if marker_index is None:
        return None
    line_end = end
    for index in range(marker_index + 1, end):
        if "v8.6 ROW 2 END" in lines[index]:
            line_end = index + 1
            break
    return marker_index + 1, line_end


def _panel_f_overlay_has_protected_labels(block: str) -> bool:
    lowered = block.lower()
    return all(
        (
            "q_{\\mathrm{tr}}" in block or "q_tr" in lowered,
            "trapped charge" in lowered,
            "coulomb" in lowered,
            "repulsion" in lowered,
            "electrode" in lowered,
            "air gap" in lowered,
            "mechanical" in lowered,
        )
    )


def _strengthened_panel_f_overlay(block: str) -> str | None:
    replacement = block
    replacements = (
        ("opacity=0.045", "opacity=0.03"),
        (
            "\\draw[cGray!58!black, line width=0.26pt]",
            "\\draw[cGray!58!black, line width=0.22pt, rounded corners=1.0pt]",
        ),
        (
            "\\draw[cGray!60!black, line width=0.24pt, rounded corners=1.1pt]",
            "\\draw[cGray!62!black, line width=0.30pt, rounded corners=1.0pt]",
        ),
        (
            "(13.42, 4.01) -- (13.62, 4.01) -- (13.62, 2.82) -- (13.42, 2.82);",
            "(13.42, 4.01) -- (13.66, 4.01) -- (13.66, 2.82) -- (13.42, 2.82);",
        ),
        ("circle ({1.65*\\rr})", "circle ({1.90*\\rr})"),
        ("circle ({1.90*\\rr})", "circle ({2.35*\\rr})"),
        ("ball color=cRed!76!black", "ball color=cRed!82!black"),
        (
            "(11.58,2.35) .. controls (11.28,2.56) and (10.90,2.64) .. (10.48,2.62);",
            "(11.58,2.35) .. controls (11.20,2.58) and (10.42,2.67) .. (9.78,2.63);",
        ),
        ("at (9.80, 2.60) {$q_{\\mathrm{tr}}$};", "at (9.58, 2.63) {$q_{\\mathrm{tr}}$};"),
        ("at (10.08, 2.60) {trapped charge};", "at (9.86, 2.63) {trapped charge};"),
        ("Stealth[length=7.6pt,width=5.6pt]", "Stealth[length=8.6pt,width=6.2pt]"),
        ("Stealth[length=8.6pt,width=6.2pt]", "Stealth[length=9.6pt,width=6.8pt]"),
        ("line width=0.94pt", "line width=1.08pt"),
        ("line width=1.08pt", "line width=1.24pt"),
        (
            "\\draw[<->, cGray!62!black, line width=0.38pt]",
            "\\draw[<->, cGray!64!black, line width=0.70pt]",
        ),
        (
            "\\draw[<->, cGray!62!black, line width=0.50pt]",
            "\\draw[<->, cGray!64!black, line width=0.70pt]",
        ),
        ("opacity=0.13", "opacity=0.08"),
        ("line width=0.34pt, rounded corners=1.2pt", "line width=0.28pt, rounded corners=1.2pt"),
        ("line width=0.56pt", "line width=0.72pt"),
        ("Stealth[length=7pt,width=5pt]", "Stealth[length=8.5pt,width=6.2pt]"),
        ("line width=0.82pt", "line width=1.08pt"),
        ("(10.95, 1.18) -- (9.74, 1.18);", "(11.08, 1.18) -- (9.54, 1.18);"),
        ("(11.02, 1.18) -- (9.60, 1.18);", "(11.18, 1.18) -- (9.18, 1.18);"),
        ("fontsize{4.2}{5.1}", "fontsize{4.8}{5.8}"),
        ("fontsize{4.0}{4.8}", "fontsize{4.8}{5.8}"),
        ("fontsize{3.8}{4.6}", "fontsize{4.4}{5.3}"),
        ("ball color=cRed!72!black", "ball color=cRed!78!black"),
        ("circle ({1.45*\\rr})", "circle ({1.85*\\rr})"),
        (
            "\\draw[<->, cGray!55!black, line width=0.30pt]",
            "\\draw[<->, cGray!64!black, line width=0.70pt]",
        ),
        ("(10.58, 0.54) -- (13.18, 0.54);", "(9.92, 0.54) -- (13.18, 0.54);"),
        ("(10.42, 0.54) -- (13.18, 0.54);", "(9.92, 0.54) -- (13.18, 0.54);"),
        ("opacity=0.03", "opacity=0.018"),
        (
            "(12.65, 3.55) rectangle (13.58, 4.12);",
            "(12.58, 3.78) rectangle (13.48, 4.14);",
        ),
        (
            "\\fill[cGray!3] (12.60, 3.62) rectangle (13.52, 4.17);",
            "\\fill[cGray!3] (12.56, 3.82) rectangle (13.46, 4.16);",
        ),
        (
            "(12.60, 3.62) rectangle (13.52, 4.17);",
            "(12.56, 3.82) rectangle (13.46, 4.16);",
        ),
        (
            "(12.73, 4.00) rectangle (13.14, 4.09);",
            "(12.66, 4.01) rectangle (13.12, 4.10);",
        ),
        (
            "(12.78, 4.045) -- (12.89, 4.045) -- (12.89, 4.075)\n"
            "               -- (13.01, 4.075) -- (13.01, 4.045) -- (13.10, 4.045);",
            "(12.70, 4.045) -- (12.83, 4.045) -- (12.83, 4.075)\n"
            "               -- (12.98, 4.075) -- (12.98, 4.045) -- (13.08, 4.045);",
        ),
        (
            "at (13.06, 3.82) {$V_{\\mathrm{active}}$};",
            "at (12.99, 3.94) {$V_{\\mathrm{active}}$};",
        ),
        ("at (13.06, 3.70) {bias};", "at (12.99, 3.84) {bias};"),
        ("(13.31, 4.01) circle (0.020)", "(13.30, 3.82) circle (0.020)"),
        ("(13.42, 4.01) circle (0.020)", "(13.30, 2.82) circle (0.020)"),
        (
            "\\draw[cGray!62!black, line width=0.30pt, rounded corners=1.0pt]",
            "\\draw[cGray!62!black, line width=0.34pt, rounded corners=0.8pt]",
        ),
        (
            "(13.42, 4.01) -- (13.66, 4.01) -- (13.66, 2.82) -- (13.42, 2.82);",
            "(13.30, 3.78) -- (13.30, 2.82);",
        ),
        (
            "\\draw[cRed!45!black, line width=0.22pt]",
            "\\draw[cRed!55!black, line width=0.32pt]",
        ),
        (
            "(11.58,2.35) .. controls (11.20,2.58) and (10.42,2.67) .. (9.78,2.63);",
            "(11.50,2.38) .. controls (11.10,2.78) and (10.32,3.00) .. (9.62,3.00);",
        ),
        (
            "at (9.58, 2.63) {$q_{\\mathrm{tr}}$};",
            "at (9.56, 2.84) {$q_{\\mathrm{tr}}$};",
        ),
        (
            "at (9.86, 2.63) {trapped charge};",
            "at (9.56, 3.04) {trapped charge};",
        ),
        (
            "\\draw[cGray!62!black, line width=0.34pt, rounded corners=0.8pt]\n"
            "  (13.30, 3.78) -- (13.30, 2.82);",
            "\\draw[cGray!58!black, line width=0.26pt, rounded corners=1.0pt]\n"
            "  (13.30, 3.78) -- (13.04, 3.52) -- (13.04, 3.16)"
            " -- (13.18, 3.02) -- (13.30, 2.82);",
        ),
        (
            "(11.50,2.38) .. controls (11.10,2.78) and (10.32,3.00) .. (9.62,3.00);",
            "(11.48,2.40) .. controls (10.78,3.02) and (10.12,3.36) .. (9.60,3.36);",
        ),
        (
            "at (9.56, 2.84) {$q_{\\mathrm{tr}}$};",
            "at (9.60, 3.12) {$q_{\\mathrm{tr}}$};",
        ),
        (
            "at (9.56, 3.04) {trapped charge};",
            "at (9.60, 3.36) {trapped charge};",
        ),
        (
            "\\node at (12.13, 3.08) {$q_{\\mathrm{tr}}$ trapped charge};",
            "\\node[anchor=west, fill=white, fill opacity=0.96, text opacity=1,\n"
            "      inner xsep=0.9pt, inner ysep=0.45pt,\n"
            "      font=\\sffamily\\bfseries\\fontsize{4.0}{4.8}\\selectfont, text=cRed!76!black]\n"
            "  at (9.56, 2.84) {$q_{\\mathrm{tr}}$};\n"
            "\\node[anchor=west, fill=white, fill opacity=0.94, text opacity=1,\n"
            "      inner xsep=1.0pt, inner ysep=0.45pt,\n"
            "      font=\\sffamily\\bfseries\\fontsize{3.8}{4.6}\\selectfont, text=cRed!76!black]\n"
            "  at (9.56, 3.04) {trapped charge};",
        ),
    )
    for old, new in replacements:
        replacement = replacement.replace(old, new)
    if replacement == block:
        return None
    if not _panel_f_overlay_has_protected_labels(replacement):
        return None
    return replacement


def _panel_f_overlay_template_applied(block: str) -> bool:
    required_fragments = (
        "(13.30, 3.78) -- (13.04, 3.52) -- (13.04, 3.16) -- (13.18, 3.02) -- (13.30, 2.82);",
        "(11.48,2.40) .. controls (10.78,3.02) and (10.12,3.36) .. (9.60,3.36);",
        "at (9.60, 3.12) {$q_{\\mathrm{tr}}$};",
        "at (9.60, 3.36) {trapped charge};",
        "Stealth[length=9.6pt,width=6.8pt]",
        "line width=1.24pt",
        "\\draw[<->, cGray!64!black, line width=0.70pt]",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_overlay_refresh_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search F refresh: left-margin trap label + electrode relation",
        "(11.46,2.50) .. controls (10.82,3.08) and (10.12,3.32) .. (9.54,3.32);",
        "at (9.54, 3.18) {$q_{\\mathrm{tr}}$};",
        "at (9.54, 3.42) {trapped charge};",
        "(10.96, 1.18) -- (9.28, 1.18);",
        "at (9.44, 1.58) {Coulomb};",
        "(9.70, 0.54) -- (13.18, 0.54);",
        "at (11.58, 0.28) {air gap};",
        "(13.30, 3.82) -- (13.06, 3.50) -- (13.06, 3.12) -- (13.18, 2.82);",
    )
    return all(fragment in block for fragment in required_fragments)


def _refreshed_panel_f_overlay(block: str) -> str | None:
    tracked_overlay_replacements = (
        (
            "\\draw[cGray!48!black, line width=0.20pt, "
            "dash pattern=on 1.0pt off 1.0pt, rounded corners=0.7pt]\n"
            "  (13.30, 3.72) -- (13.30, 3.28) -- (13.30, 2.82);",
            "% quality-search F refresh: left-margin trap label + electrode relation\n"
            "\\draw[cGray!56!black, line width=0.30pt, rounded corners=0.9pt]\n"
            "  (13.30, 3.82) -- (13.06, 3.50) -- (13.06, 3.12) -- (13.18, 2.82);",
        ),
        (
            "\\draw[cRed!56!black, line width=0.34pt]\n"
            "  (11.50,2.48) .. controls (11.16,3.04) and (10.48,3.42) .. (10.12,3.60);",
            "\\draw[cRed!62!black, line width=0.46pt]\n"
            "  (11.46,2.50) .. controls (10.82,3.08) and (10.12,3.32) .. (9.54,3.32);",
        ),
        (
            "at (9.74, 3.52) {$q_{\\mathrm{tr}}$};",
            "at (9.54, 3.18) {$q_{\\mathrm{tr}}$};",
        ),
        (
            "at (9.74, 3.80) {trapped charge};",
            "at (9.54, 3.42) {trapped charge};",
        ),
        (
            "\\draw[panelFCoulombRepulsionArrow, "
            "-{Stealth[length=8.2pt,width=5.8pt]}, "
            "cRed!78!black, line width=1.05pt]\n"
            "  (10.86, 1.18) -- (9.48, 1.18);",
            "\\draw[panelFCoulombRepulsionArrow, "
            "-{Stealth[length=9.2pt,width=6.4pt]}, "
            "cRed!82!black, line width=1.18pt]\n"
            "  (10.96, 1.18) -- (9.28, 1.18);",
        ),
        (
            "anchor=south west] at (9.60, 1.50) {Coulomb};",
            "anchor=south west] at (9.44, 1.58) {Coulomb};",
        ),
        (
            "text=cRed!76!black] at (9.60, 1.40) {repulsion};",
            "text=cRed!80!black] at (9.44, 1.45) {repulsion};",
        ),
        (
            "\\draw[<->, cGray!62!black, line width=0.62pt]\n"
            "  (10.36, 0.54) -- (13.18, 0.54);",
            "\\draw[<->, cGray!66!black, line width=0.78pt]\n"
            "  (9.70, 0.54) -- (13.18, 0.54);",
        ),
        (
            "at (11.88, 0.31) {air gap};",
            "at (11.58, 0.28) {air gap};",
        ),
        (
            "\\foreach \\yy in {0.96,1.34,1.72,2.10} {\n"
            "  \\draw[cGray!19, line width=0.22pt, dash pattern=on 1.2pt off 1.5pt]\n"
            "    (11.08,\\yy) -- (13.18,\\yy);\n"
            "}",
            "\\foreach \\yy in {0.96,1.34,1.72,2.10} {\n"
            "  \\draw[cGray!23, line width=0.30pt, dash pattern=on 1.3pt off 1.2pt]\n"
            "    (10.62,\\yy) -- (13.18,\\yy);\n"
            "}",
        ),
    )
    v1_template_replacements = (
        (
            "\\draw[cGray!58!black, line width=0.26pt, rounded corners=1.0pt]\n"
            "  (13.30, 3.78) -- (13.04, 3.52) -- (13.04, 3.16)"
            " -- (13.18, 3.02) -- (13.30, 2.82);",
            "% quality-search F refresh: left-margin trap label + electrode relation\n"
            "\\draw[cGray!56!black, line width=0.30pt, rounded corners=0.9pt]\n"
            "  (13.30, 3.82) -- (13.06, 3.50) -- (13.06, 3.12) -- (13.18, 2.82);",
        ),
        (
            "\\draw[cRed!55!black, line width=0.32pt]\n"
            "  (11.48,2.40) .. controls (10.78,3.02)"
            " and (10.12,3.36) .. (9.60,3.36);",
            "\\draw[cRed!62!black, line width=0.46pt]\n"
            "  (11.46,2.50) .. controls (10.82,3.08) and (10.12,3.32) .. (9.54,3.32);",
        ),
        (
            "at (9.60, 3.12) {$q_{\\mathrm{tr}}$};",
            "at (9.54, 3.18) {$q_{\\mathrm{tr}}$};",
        ),
        (
            "at (9.60, 3.36) {trapped charge};",
            "at (9.54, 3.42) {trapped charge};",
        ),
        (
            "\\draw[panelFCoulombRepulsionArrow, "
            "-{Stealth[length=9.6pt,width=6.8pt]}, "
            "cRed!82!black, line width=1.24pt]\n"
            "  (11.18, 1.18) -- (9.18, 1.18);",
            "\\draw[panelFCoulombRepulsionArrow, "
            "-{Stealth[length=9.2pt,width=6.4pt]}, "
            "cRed!82!black, line width=1.18pt]\n"
            "  (10.96, 1.18) -- (9.28, 1.18);",
        ),
        (
            "\\draw[<->, cGray!64!black, line width=0.70pt]\n"
            "  (9.92, 0.54) -- (13.18, 0.54);",
            "\\draw[<->, cGray!66!black, line width=0.78pt]\n"
            "  (9.70, 0.54) -- (13.18, 0.54);",
        ),
        (
            "at (11.88, 0.31) {air gap};",
            "at (11.58, 0.28) {air gap};",
        ),
    )

    for replacements in (tracked_overlay_replacements, v1_template_replacements):
        replacement = block
        for old, new in replacements:
            if old not in replacement:
                break
            replacement = replacement.replace(old, new)
        else:
            if replacement != block and _panel_f_overlay_has_protected_labels(
                replacement
            ):
                return replacement
    return None


def _apparatus_panel_block_status(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> dict[str, Any]:
    line_range = _panel_f_overlay_range(lines=lines, selector=selector)
    if line_range is None:
        return {"state": "not_found"}
    line_start, line_end = line_range
    original = "".join(lines[line_start - 1 : line_end])
    if not _panel_f_overlay_has_protected_labels(original):
        return {"state": "protected_labels_missing", "line_start": line_start, "line_end": line_end}
    if _panel_f_overlay_refresh_template_applied(original):
        return {"state": "already_applied", "line_start": line_start, "line_end": line_end}
    refresh_replacement = _refreshed_panel_f_overlay(original)
    if refresh_replacement is not None:
        replacement = refresh_replacement
        template_id = APPARATUS_PANEL_F_REFRESH_TEMPLATE_ID
    else:
        replacement = _strengthened_panel_f_overlay(original)
        template_id = APPARATUS_PANEL_F_TEMPLATE_ID
    if replacement is None:
        return {"state": "no_template_movement", "line_start": line_start, "line_end": line_end}
    return {
        "state": "replaceable",
        "original": original,
        "replacement": replacement,
        "line_start": line_start,
        "line_end": line_end,
        "template_id": template_id,
    }


def _apparatus_panel_block_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[str, str, int, int] | None:
    status = _apparatus_panel_block_status(lines=lines, selector=selector)
    if status.get("state") != "replaceable":
        return None
    return (
        str(status["original"]),
        str(status["replacement"]),
        int(status["line_start"]),
        int(status["line_end"]),
    )


def _panel_f_qtr_label_lane_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search C001 q_tr label lane",
        "at (9.58, 2.84) {$q_{tr}$};",
        "at (9.58, 3.12) {trapped charge};",
        "circle (0.155);",
        "(11.90, 2.00) .. controls (11.20, 2.76) and (10.18, 2.92) .. (9.88, 2.92);",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_v5f_qtr_label_lane_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search F qtr-left label lane",
        "(11.42,2.46) .. controls (10.70,2.96) and (9.98,3.20) .. (9.50,3.20);",
        "at (9.50, 3.05) {$q_{\\mathrm{tr}}$};",
        "at (9.50, 3.60) {trapped charge};",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_v5f_qtr_label_lane_v2_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search F qtr-left label lane v2",
        "(11.38,2.42) .. controls (10.58,3.02) and (9.78,3.34) .. (9.30,3.38);",
        "at (9.30, 3.18) {$q_{\\mathrm{tr}}$};",
        "at (9.30, 3.74) {trapped charge};",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_v5f_qtr_label_lane_base_replacement(block: str) -> str | None:
    if not _panel_f_overlay_has_protected_labels(block):
        return None
    replacement = _refreshed_panel_f_overlay(block)
    if replacement is None:
        replacement = _strengthened_panel_f_overlay(block)
    return replacement


def _panel_f_v5f_qtr_label_lane_replacement(block: str) -> str | None:
    if _panel_f_v5f_qtr_label_lane_template_applied(block):
        return None
    replacement = _panel_f_v5f_qtr_label_lane_base_replacement(block)
    if replacement is None:
        return None
    replacements = (
        (
            "\\draw[cRed!62!black, line width=0.46pt]\n"
            "  (11.46,2.50) .. controls (10.82,3.08) and (10.12,3.32) .. (9.54,3.32);",
            "% quality-search F qtr-left label lane -- review-only candidate\n"
            "\\draw[cRed!64!black, line width=0.48pt]\n"
            "  (11.42,2.46) .. controls (10.70,2.96) and (9.98,3.20) .. (9.50,3.20);",
        ),
        (
            "at (9.54, 3.18) {$q_{\\mathrm{tr}}$};",
            "at (9.50, 3.05) {$q_{\\mathrm{tr}}$};",
        ),
        (
            "at (9.54, 3.42) {trapped charge};",
            "at (9.50, 3.60) {trapped charge};",
        ),
    )
    for old, new in replacements:
        if old not in replacement:
            return None
        replacement = replacement.replace(old, new)
    if replacement == block or not _panel_f_overlay_has_protected_labels(replacement):
        return None
    return replacement


def _panel_f_v5f_qtr_label_lane_v2_replacement(block: str) -> str | None:
    if _panel_f_v5f_qtr_label_lane_v2_template_applied(block):
        return None
    replacement = _panel_f_v5f_qtr_label_lane_base_replacement(block)
    if replacement is None:
        return None
    replacements = (
        (
            "\\draw[cRed!62!black, line width=0.46pt]\n"
            "  (11.46,2.50) .. controls (10.82,3.08) and (10.12,3.32) .. (9.54,3.32);",
            "% quality-search F qtr-left label lane v2 -- review-only candidate\n"
            "\\draw[cRed!64!black, line width=0.50pt]\n"
            "  (11.38,2.42) .. controls (10.58,3.02) and (9.78,3.34) .. (9.30,3.38);",
        ),
        (
            "at (9.54, 3.18) {$q_{\\mathrm{tr}}$};",
            "at (9.30, 3.18) {$q_{\\mathrm{tr}}$};",
        ),
        (
            "at (9.54, 3.42) {trapped charge};",
            "at (9.30, 3.74) {trapped charge};",
        ),
    )
    for old, new in replacements:
        if old not in replacement:
            return None
        replacement = replacement.replace(old, new)
    if replacement == block or not _panel_f_overlay_has_protected_labels(replacement):
        return None
    return replacement


def _panel_f_qtr_label_lane_template_id(replacement: str) -> str:
    if _panel_f_v5f_qtr_label_lane_v2_template_applied(replacement):
        return PANEL_F_V5F_QTR_LABEL_LANE_V2_TEMPLATE_ID
    if _panel_f_v5f_qtr_label_lane_template_applied(replacement):
        return PANEL_F_V5F_QTR_LABEL_LANE_TEMPLATE_ID
    return PANEL_F_QTR_LABEL_LANE_TEMPLATE_ID


def _panel_f_qtr_label_lane_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
    template_id: str | None = None,
) -> tuple[str, str, int, int] | None:
    if str(selector.get("panel") or "").upper() != "F":
        return None
    try:
        start = int(selector["line_start"])
        end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if start < 1 or end < start or end > len(lines):
        return None
    block = "".join(lines[start - 1 : end])
    if template_id == PANEL_F_V5F_QTR_LABEL_LANE_V2_TEMPLATE_ID:
        v5f_v2_replacement = _panel_f_v5f_qtr_label_lane_v2_replacement(block)
        if v5f_v2_replacement is not None:
            return block, v5f_v2_replacement, start, end
    v5f_replacement = _panel_f_v5f_qtr_label_lane_replacement(block)
    if v5f_replacement is not None:
        return block, v5f_replacement, start, end
    if _panel_f_qtr_label_lane_template_applied(block):
        return None
    original = (
        "\\draw[cRed!55!black, line width=0.30pt] (11.92, 2) -- (12.35, 2);\n"
        "\\node[labelMute, anchor=west, inner sep=1pt,\n"
        "      font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont, text=cRed!70!black]\n"
        "  at (12.35, 2) {$q_{tr}$};\n"
    )
    replacement = (
        "% quality-search C001 q_tr label lane -- review-only candidate\n"
        "\\fill[white, opacity=0.96, rounded corners=1.0pt]\n"
        "  (9.50, 2.72) rectangle (10.72, 3.25);\n"
        "\\draw[cRed!32!white, line width=0.22pt, rounded corners=1.0pt]\n"
        "  (9.50, 2.72) rectangle (10.72, 3.25);\n"
        "\\draw[cRed!62!black, line width=0.48pt]\n"
        "  (11.90, 2.00) .. controls (11.20, 2.76) and (10.18, 2.92) .. (9.88, 2.92);\n"
        "\\fill[cRed!68!black] (9.88, 2.92) circle (0.024);\n"
        "\\foreach \\cx/\\cy in {11.90/2.00, 11.66/1.48, 11.34/1.07} {\n"
        "  \\fill[cRed!72!black, opacity=0.10] (\\cx, \\cy) circle (0.185);\n"
        "  \\draw[cRed!80!black, line width=0.56pt, opacity=0.86] (\\cx, \\cy) circle (0.155);\n"
        "}\n"
        "\\node[anchor=west, fill=white, fill opacity=0.96, text opacity=1,\n"
        "      inner xsep=1.8pt, inner ysep=0.9pt,\n"
        "      font=\\sffamily\\bfseries\\fontsize{8.2}{9.8}\\selectfont,\n"
        "      text=cRed!86!black]\n"
        "  at (9.58, 2.84) {$q_{tr}$};\n"
        "\\node[labelMute, anchor=west, fill=white, fill opacity=0.94, text opacity=1,\n"
        "      inner xsep=1.6pt, inner ysep=0.7pt,\n"
        "      font=\\sffamily\\fontsize{6.3}{7.5}\\selectfont, text=cRed!74!black]\n"
        "  at (9.58, 3.12) {trapped charge};\n"
    )
    offset = block.find(original)
    if offset < 0:
        return None
    if "q_{tr}" not in replacement or "trapped charge" not in replacement:
        return None
    line_start = start + block[:offset].count("\n")
    line_end = line_start + original.count("\n") - 1
    return original, replacement, line_start, line_end


def _panel_f_qtr_apparatus_lane_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search C001 q_tr + apparatus lane",
        "(11.90, 2.00) .. controls (11.30, 2.72) and (10.30, 2.96) .. (9.96, 2.96);",
        "at (9.70, 2.94) {$q_{tr}$};",
        "at (9.70, 3.18) {trapped charge};",
        "(12.65, 3.50) -- (12.92, 3.50) -- (13.08, 3.10) -- (13.08, 2.68) -- (13.23, 2.58);",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_qtr_apparatus_lane_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[str, str, int, int] | None:
    if str(selector.get("panel") or "").upper() != "F":
        return None
    try:
        line_start = int(selector["line_start"])
        line_end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if line_start < 1 or line_end < line_start or line_end > len(lines):
        return None
    original = "".join(lines[line_start - 1 : line_end])
    required = (
        "$V_{\\mathrm{active}}$",
        "q_{tr}",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
        "Mechanical",
    )
    if not all(label in original for label in required):
        return None
    if _panel_f_qtr_apparatus_lane_template_applied(original):
        return None
    replacement = original
    replacements = (
        (
            "\\fill[cGray!6] (11.8, 3.2) rectangle (12.65, 3.85);",
            "\\fill[cGray!4, opacity=0.74, rounded corners=1.1pt] "
            "(11.86, 3.25) rectangle (12.61, 3.82);",
        ),
        (
            "\\draw[cGray!60!black, line width=0.25pt]\n"
            "  (11.8, 3.2) rectangle (12.65, 3.85);",
            "\\draw[cGray!50!black, line width=0.20pt, rounded corners=1.1pt]\n"
            "  (11.86, 3.25) rectangle (12.61, 3.82);",
        ),
        (
            "\\draw[cGray!35!black, line width=0.18pt] (11.85, 3.25) rectangle (12.60, 3.81);",
            "\\draw[cGray!30!black, line width=0.14pt, rounded corners=0.8pt] "
            "(11.91, 3.31) rectangle (12.56, 3.76);",
        ),
        (
            "\\fill[cGray!18] (11.9, 3.55) rectangle (12.55, 3.78);",
            "\\fill[cGray!14, opacity=0.82, rounded corners=0.7pt] "
            "(11.95, 3.57) rectangle (12.52, 3.75);",
        ),
        (
            "\\draw[cGray!55!black, line width=0.18pt]\n"
            "  (11.9, 3.55) rectangle (12.55, 3.78);",
            "\\draw[cGray!45!black, line width=0.14pt, rounded corners=0.7pt]\n"
            "  (11.95, 3.57) rectangle (12.52, 3.75);",
        ),
        (
            "\\draw[cGray!80!black, line width=0.55pt]\n"
            "  (11.95, 3.58) -- (12.08, 3.58) -- (12.08, 3.73)\n"
            "              -- (12.3, 3.73) -- (12.3, 3.58) -- (12.5, 3.58);",
            "\\draw[cGray!70!black, line width=0.42pt]\n"
            "  (12.00, 3.60) -- (12.10, 3.60) -- (12.10, 3.71)\n"
            "              -- (12.28, 3.71) -- (12.28, 3.60) -- (12.46, 3.60);",
        ),
        (
            "\\node[font=\\sffamily\\bfseries\\fontsize{6}{7.2}\\selectfont, text=cGray!88!black]\n"
            "  at (12.225, 3.36) {$V_{\\mathrm{active}}$};",
            "\\node[font=\\sffamily\\bfseries\\fontsize{5.5}{6.6}\\selectfont, "
            "text=cGray!72!black]\n"
            "  at (12.235, 3.39) {$V_{\\mathrm{active}}$};",
        ),
        (
            "\\draw[cGray!75!black, line width=0.28pt]\n"
            "  (12.65, 3.5) -- (13.23, 3.5) -- (13.23, 2.6);",
            "\\draw[cGray!62!black, line width=0.26pt, rounded corners=1.2pt]\n"
            "  (12.65, 3.50) -- (12.92, 3.50) -- (13.08, 3.10) -- (13.08, 2.68) -- (13.23, 2.58);\n"
            "\\fill[cGray!68!black] (13.23, 2.58) circle (0.020);",
        ),
        (
            "\\draw[cRed!55!black, line width=0.30pt] (11.92, 2) -- (12.35, 2);\n"
            "\\node[labelMute, anchor=west, inner sep=1pt,\n"
            "      font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont, text=cRed!70!black]\n"
            "  at (12.35, 2) {$q_{tr}$};",
            "% quality-search C001 q_tr + apparatus lane -- review-only candidate\n"
            "\\draw[cRed!60!black, line width=0.36pt]\n"
            "  (11.90, 2.00) .. controls (11.30, 2.72) and (10.30, 2.96) .. (9.96, 2.96);\n"
            "\\node[anchor=west, fill=white, fill opacity=0.96, text opacity=1,\n"
            "      inner xsep=1.4pt, inner ysep=0.7pt,\n"
            "      font=\\sffamily\\bfseries\\fontsize{7.4}{8.8}\\selectfont,\n"
            "      text=cRed!84!black]\n"
            "  at (9.70, 2.94) {$q_{tr}$};\n"
            "\\node[labelMute, anchor=west, fill=white, fill opacity=0.94, text opacity=1,\n"
            "      inner xsep=1.3pt, inner ysep=0.5pt,\n"
            "      font=\\sffamily\\fontsize{5.8}{7.0}\\selectfont, text=cRed!72!black]\n"
            "  at (9.70, 3.18) {trapped charge};",
        ),
    )
    for old, new in replacements:
        if old not in replacement:
            return None
        replacement = replacement.replace(old, new)
    if replacement == original:
        return None
    protected = (
        "$V_{\\mathrm{active}}$",
        "q_{tr}",
        "trapped charge",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
    )
    if not all(label in replacement for label in protected):
        return None
    return original, replacement, line_start, line_end


def _panel_f_force_gap_lane_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search C002 Coulomb/electrode/air-gap lane",
        "at (9.68, 3.04) {trapped charge};",
        "(11.62, 1.30) -- (10.42, 1.30);",
        "at (10.42, 1.40) {Coulomb};",
        "at (10.42, 1.20) {repulsion};",
        "(11.14, 0.68) -- (13.23, 0.68);",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_force_gap_lane_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[str, str, int, int] | None:
    if str(selector.get("panel") or "").upper() != "F":
        return None
    try:
        line_start = int(selector["line_start"])
        line_end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if line_start < 1 or line_end < line_start or line_end > len(lines):
        return None
    original = "".join(lines[line_start - 1 : line_end])
    required = (
        "q_{tr}",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
        "Mechanical",
    )
    if not all(label in original for label in required):
        return None
    if _panel_f_force_gap_lane_template_applied(original):
        return None
    replacement = original
    replacements = (
        (
            "\\draw[cRed!55!black, line width=0.30pt] (11.92, 2) -- (12.35, 2);\n"
            "\\node[labelMute, anchor=west, inner sep=1pt,\n"
            "      font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont, text=cRed!70!black]\n"
            "  at (12.35, 2) {$q_{tr}$};",
            "\\draw[cRed!58!black, line width=0.34pt]\n"
            "  (11.90, 2.00) .. controls (11.32, 2.58) and (10.28, 2.80) .. (9.94, 2.80);\n"
            "\\node[anchor=west, fill=white, fill opacity=0.96, text opacity=1,\n"
            "      inner xsep=1.3pt, inner ysep=0.6pt,\n"
            "      font=\\sffamily\\bfseries\\fontsize{7.2}{8.6}\\selectfont,\n"
            "      text=cRed!82!black]\n"
            "  at (9.68, 2.82) {$q_{tr}$};\n"
            "\\node[labelMute, anchor=west, fill=white, fill opacity=0.94, text opacity=1,\n"
            "      inner xsep=1.2pt, inner ysep=0.5pt,\n"
            "      font=\\sffamily\\fontsize{5.8}{7.0}\\selectfont, text=cRed!72!black]\n"
            "  at (9.68, 3.04) {trapped charge};",
        ),
        (
            "\\draw[-{Stealth[length=6pt,width=4.5pt]}, cRed!80!black, line width=0.7pt]\n"
            "  (11.55, 1.3) -- (10.85, 1.3);",
            "% quality-search C002 Coulomb/electrode/air-gap lane -- review-only candidate\n"
            "\\draw[-{Stealth[length=8.2pt,width=5.8pt]}, cRed!84!black, line width=0.92pt]\n"
            "  (11.62, 1.30) -- (10.42, 1.30);",
        ),
        (
            "\\node[font=\\sffamily\\bfseries\\fontsize{7}{8.4}\\selectfont, text=cRed!80!black,\n"
            "      anchor=south east] at (10.85, 1.35) {Coulomb};",
            "\\node[font=\\sffamily\\bfseries\\fontsize{7.4}{8.9}\\selectfont, "
            "text=cRed!84!black,\n"
            "      anchor=south east, fill=white, fill opacity=0.94, text opacity=1,\n"
            "      inner xsep=1.2pt, inner ysep=0.5pt] at (10.42, 1.40) {Coulomb};",
        ),
        (
            "\\node[labelMute, anchor=north east, "
            "font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont,\n"
            "      text=cRed!80!black] at (10.85, 1.27) {repulsion};",
            "\\node[labelMute, anchor=north east, fill=white, fill opacity=0.94, text opacity=1,\n"
            "      inner xsep=1.1pt, inner ysep=0.4pt,\n"
            "      font=\\sffamily\\fontsize{6.8}{8.2}\\selectfont,\n"
            "      text=cRed!82!black] at (10.42, 1.20) {repulsion};",
        ),
        (
            "\\draw[cGray!85!black, line width=0.50pt]\n"
            "  (13.23, 0.4) rectangle (13.4, 2.6);",
            "\\draw[cGray!85!black, line width=0.50pt]\n"
            "  (13.23, 0.4) rectangle (13.4, 2.6);\n"
            "\\draw[cRed!38!black, line width=0.48pt, opacity=0.70]\n"
            "  (13.23, 0.58) -- (13.23, 2.44);",
        ),
        (
            "\\draw[<->, cGray!55!black, line width=0.30pt]\n"
            "  (11.5, 0.55) -- (13.23, 0.55);",
            "\\draw[<->, cGray!62!black, line width=0.44pt]\n"
            "  (11.14, 0.68) -- (13.23, 0.68);",
        ),
        (
            "\\node[labelMute, anchor=north, inner sep=1pt,\n"
            "      font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont]\n"
            "  at (12.365, 0.5) {air gap};",
            "\\node[labelMute, anchor=south, fill=white, fill opacity=0.94, text opacity=1,\n"
            "      inner xsep=1.2pt, inner ysep=0.5pt,\n"
            "      font=\\sffamily\\fontsize{6.8}{8.2}\\selectfont]\n"
            "  at (12.185, 0.74) {air gap};",
        ),
    )
    for old, new in replacements:
        if old not in replacement:
            return None
        replacement = replacement.replace(old, new)
    if replacement == original:
        return None
    protected = (
        "q_{tr}",
        "trapped charge",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
    )
    if not all(label in replacement for label in protected):
        return None
    return original, replacement, line_start, line_end


def _panel_f_mechanical_anchor_lane_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search C003 mechanical anchor lane",
        "(11.72, 2.36) rectangle (12.28, 2.58);",
        "(11.72, 2.68) -- (12.38, 2.68);",
        "(11.86, 2.42) .. controls (11.88, 1.82)",
        "at (9.76, 3.10) {trapped charge};",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_mechanical_anchor_lane_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
    include_qtr_label: bool = True,
) -> tuple[str, str, int, int] | None:
    if str(selector.get("panel") or "").upper() != "F":
        return None
    try:
        line_start = int(selector["line_start"])
        line_end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if line_start < 1 or line_end < line_start or line_end > len(lines):
        return None
    original = "".join(lines[line_start - 1 : line_end])
    required = (
        "q_{tr}",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
        "Mechanical",
    )
    if not all(label in original for label in required):
        return None
    if _panel_f_mechanical_anchor_lane_template_applied(original):
        return None
    replacement = original
    replacements = [
        (
            "\\fill[cGray!10] (11.785, 2.42) rectangle (12.185, 2.52);",
            "% quality-search C003 mechanical anchor lane -- review-only candidate\n"
            "\\fill[cGray!12] (11.72, 2.36) rectangle (12.28, 2.58);\n"
            "\\fill[cGray!45!black, opacity=0.16] (11.72, 2.34) rectangle (12.28, 2.39);",
        ),
        (
            "\\draw[cGray!75!black, line width=0.40pt]\n"
            "  (11.785, 2.42) rectangle (12.185, 2.52);",
            "\\draw[cGray!78!black, line width=0.46pt]\n"
            "  (11.72, 2.36) rectangle (12.28, 2.58);",
        ),
        (
            "\\draw[cGray!50!black, line width=0.40pt] (11.685, 2.65) -- (12.285, 2.65);",
            "\\draw[cGray!58!black, line width=0.48pt] (11.72, 2.68) -- (12.38, 2.68);",
        ),
        (
            "\\foreach \\dx in {0,0.10,0.20,0.30,0.40,0.50} {\n"
            "  \\draw[cGray!50!black, line width=0.25pt]\n"
            "    ({11.685+\\dx}, 2.65) -- ({11.635+\\dx}, 2.72);\n"
            "}",
            "\\foreach \\dx in {0,0.11,0.22,0.33,0.44,0.55} {\n"
            "  \\draw[cGray!54!black, line width=0.28pt]\n"
            "    ({11.74+\\dx}, 2.68) -- ({11.68+\\dx}, 2.78);\n"
            "}",
        ),
        (
            "\\draw[cGray!75!black, line width=0.40pt] (11.985, 2.52) -- (11.985, 2.65);",
            "\\draw[cGray!78!black, line width=0.48pt] (11.99, 2.58) -- (11.99, 2.68);",
        ),
        (
            "\\shade[top color=cAmber!22, bottom color=cAmber!42, rounded corners=0.3mm]\n"
            "  (11.92, 2.42) .. controls (11.94, 1.80) and (11.55, 1.22) ..\n"
            "  (11.11, 0.93) -- (11.21, 0.84) .. controls (11.74, 1.16) and\n"
            "  (12.07, 1.80) .. (12.05, 2.42) -- cycle;",
            "\\shade[top color=cAmber!20, bottom color=cAmber!44, rounded corners=0.35mm]\n"
            "  (11.86, 2.42) .. controls (11.88, 1.82) and (11.52, 1.24) ..\n"
            "  (11.08, 0.93) -- (11.19, 0.82) .. controls (11.76, 1.16) and\n"
            "  (12.10, 1.82) .. (12.10, 2.42) -- cycle;",
        ),
        (
            "\\draw[cAmber!80!black, line width=0.55pt, rounded corners=0.3mm]\n"
            "  (11.92, 2.42) .. controls (11.94, 1.80) and (11.55, 1.22) ..\n"
            "  (11.11, 0.93) -- (11.21, 0.84) .. controls (11.74, 1.16) and\n"
            "  (12.07, 1.80) .. (12.05, 2.42) -- cycle;",
            "\\draw[cAmber!82!black, line width=0.62pt, rounded corners=0.35mm]\n"
            "  (11.86, 2.42) .. controls (11.88, 1.82) and (11.52, 1.24) ..\n"
            "  (11.08, 0.93) -- (11.19, 0.82) .. controls (11.76, 1.16) and\n"
            "  (12.10, 1.82) .. (12.10, 2.42) -- cycle;",
        ),
    ]
    if include_qtr_label:
        replacements.append(
            (
            "\\draw[cRed!55!black, line width=0.30pt] (11.92, 2) -- (12.35, 2);\n"
            "\\node[labelMute, anchor=west, inner sep=1pt,\n"
            "      font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont, text=cRed!70!black]\n"
            "  at (12.35, 2) {$q_{tr}$};",
            "\\draw[cRed!58!black, line width=0.34pt]\n"
            "  (11.90, 2.00) .. controls (11.36, 2.66) and (10.34, 2.88) .. (9.98, 2.88);\n"
            "\\node[anchor=west, fill=white, fill opacity=0.96, text opacity=1,\n"
            "      inner xsep=1.3pt, inner ysep=0.6pt,\n"
            "      font=\\sffamily\\bfseries\\fontsize{7.0}{8.4}\\selectfont,\n"
            "      text=cRed!82!black]\n"
            "  at (9.76, 2.88) {$q_{tr}$};\n"
            "\\node[labelMute, anchor=west, fill=white, fill opacity=0.94, text opacity=1,\n"
            "      inner xsep=1.2pt, inner ysep=0.5pt,\n"
            "      font=\\sffamily\\fontsize{5.8}{7.0}\\selectfont, text=cRed!72!black]\n"
            "  at (9.76, 3.10) {trapped charge};",
            )
        )
    for old, new in replacements:
        if old not in replacement:
            return None
        replacement = replacement.replace(old, new)
    if replacement == original:
        return None
    protected = (
        "q_{tr}",
        "trapped charge",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
    )
    if not all(label in replacement for label in protected):
        return None
    return original, replacement, line_start, line_end


def _panel_f_leader_left_lane_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search C004 q_tr leader-left lane",
        "(9.52, 2.34) rectangle (10.90, 2.94);",
        "circle (0.092);",
        "(11.90, 2.00) .. controls (11.42, 2.36)",
        "at (9.72, 2.54) {$q_{tr}$};",
        "at (9.72, 2.76) {trapped charge};",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_leader_left_lane_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[str, str, int, int] | None:
    if str(selector.get("panel") or "").upper() != "F":
        return None
    try:
        line_start = int(selector["line_start"])
        line_end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if line_start < 1 or line_end < line_start or line_end > len(lines):
        return None
    original = "".join(lines[line_start - 1 : line_end])
    required = (
        "q_{tr}",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
        "Mechanical",
    )
    if not all(label in original for label in required):
        return None
    if _panel_f_leader_left_lane_template_applied(original):
        return None
    marker_old = (
        "\\foreach \\cx/\\cy in {11.90/2.00, 11.66/1.48, 11.34/1.07} {\n"
        "  \\shade[ball color=cRed!70!black] (\\cx, \\cy) circle (0.07);\n"
        "  \\draw[cRed!95!black, line width=0.22pt] (\\cx, \\cy) circle (0.07);\n"
        "}"
    )
    marker_new = (
        "\\foreach \\cx/\\cy in {11.90/2.00, 11.66/1.48, 11.34/1.07} {\n"
        "  \\fill[cRed!72!black, opacity=0.16] (\\cx, \\cy) circle (0.145);\n"
        "  \\shade[ball color=cRed!74!black] (\\cx, \\cy) circle (0.092);\n"
        "  \\draw[cRed!95!black, line width=0.26pt] (\\cx, \\cy) circle (0.092);\n"
        "}"
    )
    label_old = (
        "\\draw[cRed!55!black, line width=0.30pt] (11.92, 2) -- (12.35, 2);\n"
        "\\node[labelMute, anchor=west, inner sep=1pt,\n"
        "      font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont, text=cRed!70!black]\n"
        "  at (12.35, 2) {$q_{tr}$};"
    )
    label_new = (
        "% quality-search C004 q_tr leader-left lane -- review-only candidate\n"
        "\\fill[white, opacity=0.97] (9.52, 2.34) rectangle (10.90, 2.94);\n"
        "\\draw[cRed!38!black, line width=0.22pt, rounded corners=0.9pt]\n"
        "  (9.52, 2.34) rectangle (10.90, 2.94);\n"
        "\\draw[cRed!60!black, line width=0.40pt]\n"
        "  (11.90, 2.00) .. controls (11.42, 2.36) and (10.50, 2.54) .. (9.96, 2.54);\n"
        "\\node[anchor=west, inner sep=1pt,\n"
        "      font=\\sffamily\\bfseries\\fontsize{6.6}{7.9}\\selectfont, text=cRed!82!black]\n"
        "  at (9.72, 2.54) {$q_{tr}$};\n"
        "\\node[labelMute, anchor=west, inner sep=1pt,\n"
        "      font=\\sffamily\\fontsize{5.8}{7.0}\\selectfont, text=cRed!72!black]\n"
        "  at (9.72, 2.76) {trapped charge};"
    )
    if marker_old not in original or label_old not in original:
        return None
    replacement = original.replace(marker_old, marker_new).replace(label_old, label_new)
    protected = (
        "q_{tr}",
        "trapped charge",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
    )
    if not all(label in replacement for label in protected):
        return None
    return original, replacement, line_start, line_end


def _panel_f_electrode_lead_lane_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search C005 electrode lead lane",
        "(12.65, 3.50) -- (12.96, 3.50)",
        "(13.13, 2.56) circle (0.046);",
        "(13.18, 0.4) rectangle (13.43, 2.6);",
        "at (12.35, 1.82) {trapped charge};",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_electrode_lead_connection_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search C005 electrode lead lane",
        "(12.65, 3.50) -- (12.96, 3.50)",
        "(13.13, 2.56) circle (0.046);",
        "(13.18, 0.4) rectangle (13.43, 2.6);",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_v5f_electrode_connector_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search F connector: source-to-electrode lead",
        "(13.28, 3.78) -- (13.08, 3.58) -- (13.08, 2.96) -- (13.18, 2.82);",
        "(13.18, 2.82) circle (0.038);",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_v5f_electrode_connector_replacement(block: str) -> str | None:
    if not _panel_f_overlay_has_protected_labels(block):
        return None
    if _panel_f_v5f_electrode_connector_template_applied(block):
        return None
    connector_base = block
    if not _panel_f_overlay_refresh_template_applied(connector_base):
        refreshed = _refreshed_panel_f_overlay(connector_base)
        if refreshed is None:
            strengthened = _strengthened_panel_f_overlay(connector_base)
            refreshed = (
                _refreshed_panel_f_overlay(strengthened)
                if strengthened is not None
                else None
            )
        if refreshed is None:
            return None
        connector_base = refreshed
    replacements = (
        (
            "\\fill[cGray!30!black, opacity=0.018]\n"
            "  (12.58, 3.78) rectangle (13.48, 4.14);",
            "\\fill[cGray!26!black, opacity=0.014]\n"
            "  (12.70, 3.86) rectangle (13.36, 4.12);",
        ),
        (
            "\\fill[cGray!3] (12.56, 3.82) rectangle (13.46, 4.16);",
            "\\fill[cGray!3] (12.68, 3.88) rectangle (13.38, 4.14);",
        ),
        (
            "\\draw[cGray!58!black, line width=0.22pt, rounded corners=1.0pt]\n"
            "  (12.56, 3.82) rectangle (13.46, 4.16);",
            "\\draw[cGray!48!black, line width=0.18pt, rounded corners=1.0pt]\n"
            "  (12.68, 3.88) rectangle (13.38, 4.14);",
        ),
        (
            "at (12.99, 3.94) {$V_{\\mathrm{active}}$};",
            "at (13.03, 3.98) {$V_{\\mathrm{active}}$};",
        ),
        (
            "at (12.99, 3.84) {bias};",
            "at (13.03, 3.88) {bias};",
        ),
        (
            "% quality-search F refresh: left-margin trap label + electrode relation\n"
            "\\draw[cGray!56!black, line width=0.30pt, rounded corners=0.9pt]\n"
            "  (13.30, 3.82) -- (13.06, 3.50) -- (13.06, 3.12) -- (13.18, 2.82);",
            "% quality-search F connector: source-to-electrode lead\n"
            "\\draw[cGray!64!black, line width=0.46pt, rounded corners=1.2pt]\n"
            "  (13.28, 3.78) -- (13.08, 3.58) -- (13.08, 2.96) -- (13.18, 2.82);\n"
            "\\fill[cGray!82!black] (13.18, 2.82) circle (0.038);",
        ),
        (
            "\\draw[cGray!86!black, line width=0.66pt] (13.18, 0.46) rectangle (13.42, 2.82);",
            "\\draw[cGray!88!black, line width=0.72pt] (13.18, 0.46) rectangle (13.42, 2.82);",
        ),
    )
    replacement = connector_base
    for old, new in replacements:
        if old not in replacement:
            return None
        replacement = replacement.replace(old, new)
    if replacement == block:
        return None
    if not _panel_f_overlay_has_protected_labels(replacement):
        return None
    return replacement


def _panel_f_electrode_lead_lane_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
    include_qtr_label: bool = True,
) -> tuple[str, str, int, int] | None:
    if str(selector.get("panel") or "").upper() != "F":
        return None
    try:
        line_start = int(selector["line_start"])
        line_end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if line_start < 1 or line_end < line_start or line_end > len(lines):
        return None
    original = "".join(lines[line_start - 1 : line_end])
    v5f_replacement = _panel_f_v5f_electrode_connector_replacement(original)
    if v5f_replacement is not None:
        return original, v5f_replacement, line_start, line_end
    required = (
        "q_{tr}",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
        "Mechanical",
    )
    if not all(label in original for label in required):
        return None
    if include_qtr_label and _panel_f_electrode_lead_lane_template_applied(original):
        return None
    if (
        not include_qtr_label
        and _panel_f_electrode_lead_connection_template_applied(original)
    ):
        return None
    replacements = [
        (
            "\\draw[cGray!75!black, line width=0.28pt]\n"
            "  (12.65, 3.5) -- (13.23, 3.5) -- (13.23, 2.6);",
            "% quality-search C005 electrode lead lane -- review-only candidate\n"
            "\\draw[cGray!62!black, line width=0.36pt, rounded corners=1.0pt]\n"
            "  (12.65, 3.50) -- (12.96, 3.50) -- (13.13, 3.06) -- (13.13, 2.56);\n"
            "\\fill[cGray!82!black] (13.13, 2.56) circle (0.046);\n"
            "\\draw[cGray!58!black, line width=0.26pt]\n"
            "  (13.13, 2.56) -- (13.23, 2.44);",
        ),
        (
            "\\fill[cGray!25] (13.23, 0.4) rectangle (13.4, 2.6);",
            "\\fill[cGray!22] (13.18, 0.4) rectangle (13.43, 2.6);\n"
            "\\fill[cGray!45!black, opacity=0.18] (13.18, 2.40) rectangle (13.43, 2.62);",
        ),
        (
            "\\draw[cGray!85!black, line width=0.50pt]\n"
            "  (13.23, 0.4) rectangle (13.4, 2.6);",
            "\\draw[cGray!82!black, line width=0.54pt]\n"
            "  (13.18, 0.4) rectangle (13.43, 2.6);",
        ),
    ]
    if include_qtr_label:
        replacements.insert(
            1,
            (
                "\\draw[cRed!55!black, line width=0.30pt] (11.92, 2) -- (12.35, 2);\n"
                "\\node[labelMute, anchor=west, inner sep=1pt,\n"
                "      font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont, text=cRed!70!black]\n"
                "  at (12.35, 2) {$q_{tr}$};",
                "\\draw[cRed!55!black, line width=0.30pt] (11.92, 2) -- (12.35, 2);\n"
                "\\node[labelMute, anchor=west, inner sep=1pt,\n"
                "      font=\\sffamily\\fontsize{6.5}{7.8}\\selectfont, text=cRed!70!black]\n"
                "  at (12.35, 2) {$q_{tr}$};\n"
                "\\node[labelMute, anchor=west, inner sep=1pt,\n"
                "      font=\\sffamily\\fontsize{5.5}{6.6}\\selectfont, text=cRed!62!black]\n"
                "  at (12.35, 1.82) {trapped charge};",
            ),
        )
    replacement = original
    for old, new in replacements:
        if old not in replacement:
            return None
        replacement = replacement.replace(old, new)
    protected = (
        "q_{tr}",
        "trapped charge",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
    )
    if not all(label in replacement for label in protected):
        return None
    return original, replacement, line_start, line_end


def _panel_f_auto_composite_lane_template_applied(block: str) -> bool:
    required_fragments = (
        "quality-search C002 Coulomb/electrode/air-gap lane",
        "quality-search C003 mechanical anchor lane",
        "(11.62, 1.30) -- (10.42, 1.30);",
        "(11.72, 2.36) rectangle (12.28, 2.58);",
        "at (9.68, 3.04) {trapped charge};",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_auto_composite_electrode_template_applied(block: str) -> bool:
    return _panel_f_auto_composite_lane_template_applied(
        block
    ) and _panel_f_electrode_lead_connection_template_applied(block)


def _replace_lines_with_block(
    lines: list[str],
    *,
    line_start: int,
    line_end: int,
    replacement: str,
) -> list[str]:
    next_lines = list(lines)
    next_lines[line_start - 1 : line_end] = replacement.splitlines(keepends=True)
    return next_lines


def _panel_f_auto_composite_lane_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
    template_id: str = PANEL_F_AUTO_COMPOSITE_LANE_TEMPLATE_ID,
) -> tuple[str, str, int, int] | None:
    if str(selector.get("panel") or "").upper() != "F":
        return None
    try:
        line_start = int(selector["line_start"])
        line_end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if line_start < 1 or line_end < line_start or line_end > len(lines):
        return None
    original = "".join(lines[line_start - 1 : line_end])
    if template_id == PANEL_F_AUTO_COMPOSITE_ELECTRODE_TEMPLATE_ID:
        if _panel_f_auto_composite_electrode_template_applied(original):
            return None
    elif _panel_f_auto_composite_lane_template_applied(original):
        return None

    force_gap = _panel_f_force_gap_lane_replacement(lines=lines, selector=selector)
    if force_gap is None:
        return None
    _, force_replacement, force_start, force_end = force_gap
    if force_start != line_start or force_end != line_end:
        return None

    force_lines = _replace_lines_with_block(
        lines,
        line_start=line_start,
        line_end=line_end,
        replacement=force_replacement,
    )
    force_selector = dict(selector)
    force_selector["line_end"] = line_start + len(force_replacement.splitlines()) - 1
    mechanical_anchor = _panel_f_mechanical_anchor_lane_replacement(
        lines=force_lines, selector=force_selector, include_qtr_label=False
    )
    if mechanical_anchor is None:
        return None
    _, final_replacement, anchor_start, anchor_end = mechanical_anchor
    if anchor_start != line_start or anchor_end != int(force_selector["line_end"]):
        return None
    if final_replacement == original:
        return None
    if template_id == PANEL_F_AUTO_COMPOSITE_ELECTRODE_TEMPLATE_ID:
        anchor_lines = _replace_lines_with_block(
            force_lines,
            line_start=line_start,
            line_end=anchor_end,
            replacement=final_replacement,
        )
        electrode_selector = dict(selector)
        electrode_selector["line_end"] = (
            line_start + len(final_replacement.splitlines()) - 1
        )
        electrode_lead = _panel_f_electrode_lead_lane_replacement(
            lines=anchor_lines, selector=electrode_selector, include_qtr_label=False
        )
        if electrode_lead is None:
            return None
        _, final_replacement, electrode_start, electrode_end = electrode_lead
        if electrode_start != line_start or electrode_end != int(
            electrode_selector["line_end"]
        ):
            return None
    protected = (
        "q_{tr}",
        "trapped charge",
        "Coulomb",
        "repulsion",
        "electrode",
        "air gap",
    )
    if not all(label in final_replacement for label in protected):
        return None
    if template_id == PANEL_F_AUTO_COMPOSITE_ELECTRODE_TEMPLATE_ID:
        if not _panel_f_auto_composite_electrode_template_applied(final_replacement):
            return None
    elif not _panel_f_auto_composite_lane_template_applied(final_replacement):
        return None
    return original, final_replacement, line_start, line_end


def _panel_f_boundary_polish_template_applied(block: str) -> bool:
    required_fragments = (
        "(11.42,2.50) .. controls (10.94,3.24) and (10.34,3.58) .. (9.72,3.46);",
        "at (9.72, 3.20) {$q_{\\mathrm{tr}}$};",
        "at (9.72, 3.46) {trapped charge};",
        "(11.06, 1.18) -- (9.34, 1.18);",
        "anchor=south west] at (9.58, 1.54) {Coulomb};",
        "text=cRed!82!black] at (9.59, 1.45) {repulsion};",
        "(10.18, 0.54) -- (13.18, 0.54);",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_boundary_polish_geometry_applied(block: str) -> bool:
    required_fragments = (
        "(11.42,2.50) .. controls (10.94,3.24) and (10.34,3.58) .. (9.72,3.46);",
        "at (9.72, 3.20) {$q_{\\mathrm{tr}}$};",
        "at (9.72, 3.46) {trapped charge};",
        "(11.06, 1.18) -- (9.34, 1.18);",
        "(10.18, 0.54) -- (13.18, 0.54);",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_boundary_polish_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[str, str, int, int] | None:
    line_range = _panel_f_overlay_range(lines=lines, selector=selector)
    if line_range is None:
        return None
    line_start, line_end = line_range
    original = "".join(lines[line_start - 1 : line_end])
    if not _panel_f_overlay_has_protected_labels(original):
        return None
    if not _panel_f_overlay_template_applied(original):
        return None
    if _panel_f_boundary_polish_template_applied(original):
        return None
    replacement = original
    replacements = (
        (
            "(11.48,2.40) .. controls (10.78,3.02) and (10.12,3.36) .. (9.60,3.36);",
            "(11.42,2.50) .. controls (10.94,3.24) and (10.34,3.58) .. (9.72,3.46);",
        ),
        (
            "font=\\sffamily\\bfseries\\fontsize{4.8}{5.8}\\selectfont, text=cRed!76!black]\n"
            "  at (9.60, 3.12) {$q_{\\mathrm{tr}}$};",
            "font=\\sffamily\\bfseries\\fontsize{4.4}{5.3}\\selectfont, text=cRed!76!black]\n"
            "  at (9.72, 3.20) {$q_{\\mathrm{tr}}$};",
        ),
        (
            "font=\\sffamily\\bfseries\\fontsize{4.4}{5.3}\\selectfont, text=cRed!76!black]\n"
            "  at (9.60, 3.36) {trapped charge};",
            "font=\\sffamily\\bfseries\\fontsize{4.1}{5.0}\\selectfont, text=cRed!76!black]\n"
            "  at (9.72, 3.46) {trapped charge};",
        ),
        (
            "(11.18, 1.18) -- (9.18, 1.18);",
            "(11.06, 1.18) -- (9.34, 1.18);",
        ),
        (
            "anchor=south west] at (9.72, 1.54) {Coulomb};",
            "anchor=south west] at (9.58, 1.54) {Coulomb};",
        ),
        (
            "text=cRed!82!black] at (9.73, 1.45) {repulsion};",
            "text=cRed!82!black] at (9.59, 1.45) {repulsion};",
        ),
        (
            "(9.92, 0.54) -- (13.18, 0.54);",
            "(10.18, 0.54) -- (13.18, 0.54);",
        ),
    )
    for old, new in replacements:
        replacement = replacement.replace(old, new)
    if replacement == original:
        return None
    if not _panel_f_overlay_has_protected_labels(replacement):
        return None
    return original, replacement, line_start, line_end


def _panel_f_final_finish_template_applied(block: str) -> bool:
    required_fragments = (
        "line width=0.22pt, dash pattern=on 1.2pt off 0.9pt",
        "(11.38,2.58) .. controls (10.84,3.42)",
        "at (9.62, 3.32) {$q_{\\mathrm{tr}}$};",
        "at (9.62, 3.58) {trapped charge};",
        "\\fill[cGray!30!black, opacity=0.010]",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_final_finish_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[str, str, int, int] | None:
    line_range = _panel_f_overlay_range(lines=lines, selector=selector)
    if line_range is None:
        return None
    line_start, line_end = line_range
    original = "".join(lines[line_start - 1 : line_end])
    if not _panel_f_overlay_has_protected_labels(original):
        return None
    if not _panel_f_boundary_polish_geometry_applied(original):
        return None
    if _panel_f_final_finish_template_applied(original):
        return None
    replacement = original
    replacements = (
        ("\\fill[cGray!30!black, opacity=0.018]", "\\fill[cGray!30!black, opacity=0.010]"),
        (
            "\\fill[cGray!3] (12.56, 3.82) rectangle (13.46, 4.16);",
            "\\fill[cGray!2] (12.60, 3.86) rectangle (13.40, 4.12);",
        ),
        (
            "\\draw[cGray!58!black, line width=0.22pt, rounded corners=1.0pt]\n"
            "  (12.56, 3.82) rectangle (13.46, 4.16);",
            "\\draw[cGray!46!black, line width=0.18pt, rounded corners=1.0pt]\n"
            "  (12.60, 3.86) rectangle (13.40, 4.12);",
        ),
        (
            "text=cGray!74!black]\n  at (12.99, 3.94) {$V_{\\mathrm{active}}$};",
            "text=cGray!60!black]\n  at (13.00, 3.96) {$V_{\\mathrm{active}}$};",
        ),
        (
            "text=cGray!54!black]\n  at (12.99, 3.84) {bias};",
            "text=cGray!42!black]\n  at (13.00, 3.86) {bias};",
        ),
        (
            "\\draw[cGray!58!black, line width=0.26pt, rounded corners=1.0pt]\n"
            "  (13.30, 3.78) -- (13.04, 3.52) -- (13.04, 3.16) -- (13.18, 3.02) -- (13.30, 2.82);",
            "\\draw[cGray!52!black, line width=0.22pt, "
            "dash pattern=on 1.2pt off 0.9pt, rounded corners=1.0pt]\n"
            "  (13.24, 3.72) -- (13.18, 3.30) -- (13.18, 2.82);",
        ),
        (
            "\\draw[cRed!55!black, line width=0.32pt]\n"
            "  (11.42,2.50) .. controls (10.94,3.24) and (10.34,3.58) .. (9.72,3.46);",
            "\\draw[cRed!58!black, line width=0.36pt]\n"
            "  (11.38,2.58) .. controls (10.84,3.42) and (10.14,3.76) .. (9.62,3.64);",
        ),
        ("fontsize{4.4}{5.3}", "fontsize{4.2}{5.0}"),
        ("fontsize{4.1}{5.0}", "fontsize{4.0}{4.8}"),
        ("at (9.72, 3.20) {$q_{\\mathrm{tr}}$};", "at (9.62, 3.32) {$q_{\\mathrm{tr}}$};"),
        ("at (9.72, 3.46) {trapped charge};", "at (9.62, 3.58) {trapped charge};"),
        (
            "\\draw[<->, cGray!64!black, line width=0.70pt]\n"
            "  (10.18, 0.54) -- (13.18, 0.54);",
            "\\draw[<->, cGray!62!black, line width=0.62pt]\n"
            "  (10.36, 0.54) -- (13.18, 0.54);",
        ),
    )
    for old, new in replacements:
        replacement = replacement.replace(old, new)
    if replacement == original:
        return None
    if not _panel_f_overlay_has_protected_labels(replacement):
        return None
    return original, replacement, line_start, line_end


def _panel_f_label_route_finish_template_applied(block: str) -> bool:
    required_fragments = (
        "circle ({2.05*\\rr})",
        "(11.50,2.48) .. controls (11.16,3.04)",
        "at (9.74, 3.52) {$q_{\\mathrm{tr}}$};",
        "at (9.74, 3.80) {trapped charge};",
        "(13.30, 3.72) -- (13.30, 3.28) -- (13.30, 2.82);",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_label_route_finish_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[str, str, int, int] | None:
    line_range = _panel_f_overlay_range(lines=lines, selector=selector)
    if line_range is None:
        return None
    line_start, line_end = line_range
    original = "".join(lines[line_start - 1 : line_end])
    if not _panel_f_overlay_has_protected_labels(original):
        return None
    if not _panel_f_final_finish_template_applied(original):
        return None
    if _panel_f_label_route_finish_template_applied(original):
        return None
    replacement = original
    replacements = (
        (
            "\\fill[cGray!2] (12.60, 3.86) rectangle (13.40, 4.12);",
            "\\fill[cGray!2] (12.62, 3.82) rectangle (13.42, 4.16);",
        ),
        (
            "\\draw[cGray!46!black, line width=0.18pt, rounded corners=1.0pt]\n"
            "  (12.60, 3.86) rectangle (13.40, 4.12);",
            "\\draw[cGray!44!black, line width=0.17pt, rounded corners=1.0pt]\n"
            "  (12.62, 3.82) rectangle (13.42, 4.16);",
        ),
        (
            "text=cGray!60!black]\n  at (13.00, 3.96) {$V_{\\mathrm{active}}$};",
            "text=cGray!58!black]\n  at (13.02, 4.03) {$V_{\\mathrm{active}}$};",
        ),
        (
            "text=cGray!42!black]\n  at (13.00, 3.86) {bias};",
            "text=cGray!40!black]\n  at (13.02, 3.91) {bias};",
        ),
        (
            "\\draw[cGray!52!black, line width=0.22pt, "
            "dash pattern=on 1.2pt off 0.9pt, rounded corners=1.0pt]\n"
            "  (13.24, 3.72) -- (13.18, 3.30) -- (13.18, 2.82);",
            "\\draw[cGray!48!black, line width=0.20pt, "
            "dash pattern=on 1.0pt off 1.0pt, rounded corners=0.7pt]\n"
            "  (13.30, 3.72) -- (13.30, 3.28) -- (13.30, 2.82);",
        ),
        (
            "opacity=0.36] (\\cx,\\cy) circle ({2.35*\\rr});",
            "opacity=0.26] (\\cx,\\cy) circle ({2.05*\\rr});",
        ),
        (
            "\\draw[cRed!58!black, line width=0.36pt]\n"
            "  (11.38,2.58) .. controls (10.84,3.42) and (10.14,3.76) .. (9.62,3.64);",
            "\\draw[cRed!56!black, line width=0.34pt]\n"
            "  (11.50,2.48) .. controls (11.16,3.04) and (10.48,3.42) .. (10.12,3.60);",
        ),
        ("fontsize{4.0}{4.8}", "fontsize{3.9}{4.7}"),
        ("fontsize{4.2}{5.0}", "fontsize{4.0}{4.8}"),
        (
            "text=cRed!76!black]\n  at (9.62, 3.32) {$q_{\\mathrm{tr}}$};",
            "text=cRed!74!black]\n  at (9.74, 3.52) {$q_{\\mathrm{tr}}$};",
        ),
        (
            "text=cRed!76!black]\n  at (9.62, 3.58) {trapped charge};",
            "text=cRed!74!black]\n  at (9.74, 3.80) {trapped charge};",
        ),
    )
    for old, new in replacements:
        replacement = replacement.replace(old, new)
    if replacement == original:
        return None
    if not _panel_f_overlay_has_protected_labels(replacement):
        return None
    return original, replacement, line_start, line_end


def _panel_f_density_relief_template_applied(block: str) -> bool:
    required_fragments = (
        "\\foreach \\yy in {0.96,1.34,1.72,2.10}",
        "-{Stealth[length=8.2pt,width=5.8pt]}",
        "(10.86, 1.18) -- (9.48, 1.18);",
        "fontsize{5.8}{7.0}",
        "text=cGray!70!black",
    )
    return all(fragment in block for fragment in required_fragments)


def _panel_f_density_relief_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[str, str, int, int] | None:
    line_range = _panel_f_overlay_range(lines=lines, selector=selector)
    if line_range is None:
        return None
    line_start, line_end = line_range
    original = "".join(lines[line_start - 1 : line_end])
    if not _panel_f_overlay_has_protected_labels(original):
        return None
    if not _panel_f_label_route_finish_template_applied(original):
        return None
    if _panel_f_density_relief_template_applied(original):
        return None
    replacement = original
    replacements = (
        (
            "\\foreach \\hy in {0.58,0.74,0.90,1.06,1.22,1.38,1.54,1.70,"
            "1.86,2.02,2.18,2.34,2.50,2.66} {",
            "\\foreach \\hy in {0.62,0.86,1.10,1.34,1.58,1.82,2.06,2.30,2.54} {",
        ),
        (
            "\\draw[cGray!60!black, line width=0.25pt] (13.42, \\hy) -- "
            "(13.18, {\\hy-0.06});",
            "\\draw[cGray!54!black, line width=0.22pt] (13.42, \\hy) -- "
            "(13.18, {\\hy-0.05});",
        ),
        (
            "\\foreach \\yy in {0.92,1.22,1.52,1.82,2.12} {",
            "\\foreach \\yy in {0.96,1.34,1.72,2.10} {",
        ),
        ("\\draw[cGray!25, line width=0.25pt,", "\\draw[cGray!19, line width=0.22pt,"),
        (
            "\\draw[cGray!25, line width=0.25pt, dash pattern=on 1.2pt off 1.5pt]\n"
            "  (11.08,2.42) -- (11.88,2.42);",
            "\\draw[cGray!17, line width=0.20pt, dash pattern=on 1.0pt off 1.7pt]\n"
            "  (11.18,2.42) -- (11.82,2.42);",
        ),
        (
            "\\draw[cGray!25, line width=0.25pt, dash pattern=on 1.2pt off 1.5pt]\n"
            "  (12.92,2.42) -- (13.18,2.42);",
            "\\draw[cGray!17, line width=0.20pt, dash pattern=on 1.0pt off 1.7pt]\n"
            "  (12.98,2.42) -- (13.18,2.42);",
        ),
        ("text=cGray!78!black]", "text=cGray!70!black]"),
        ("fontsize{5.8}{7.0}", "fontsize{5.4}{6.5}"),
        (
            "\\draw[cRed!35!white, line width=0.25pt, opacity=0.26] "
            "(\\cx,\\cy) circle ({2.05*\\rr});",
            "\\draw[cRed!35!white, line width=0.22pt, opacity=0.18] "
            "(\\cx,\\cy) circle ({1.82*\\rr});",
        ),
        (
            "\\draw[panelFCoulombRepulsionArrow, -{Stealth[length=9.6pt,width=6.8pt]}, "
            "cRed!82!black, line width=1.24pt]\n"
            "  (11.06, 1.18) -- (9.34, 1.18);",
            "\\draw[panelFCoulombRepulsionArrow, -{Stealth[length=8.2pt,width=5.8pt]}, "
            "cRed!78!black, line width=1.05pt]\n"
            "  (10.86, 1.18) -- (9.48, 1.18);",
        ),
        ("fontsize{6.5}{7.8}", "fontsize{5.8}{7.0}"),
        ("fontsize{6.0}{7.2}", "fontsize{5.4}{6.5}"),
        ("text=cRed!82!black", "text=cRed!78!black"),
        ("at (9.58, 1.54) {Coulomb};", "at (9.60, 1.50) {Coulomb};"),
        (
            "text=cRed!78!black] at (9.59, 1.45) {repulsion};",
            "text=cRed!76!black] at (9.60, 1.40) {repulsion};",
        ),
    )
    for old, new in replacements:
        replacement = replacement.replace(old, new)
    if replacement == original:
        return None
    if not _panel_f_overlay_has_protected_labels(replacement):
        return None
    return original, replacement, line_start, line_end


def _density_panel_e_block_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> tuple[str, str, int, int] | None:
    if str(selector.get("panel") or "").upper() != "E":
        return None
    try:
        line_start = int(selector["line_start"])
        line_end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if line_start < 1 or line_end < line_start or line_end > len(lines):
        return None
    original = "".join(lines[line_start - 1 : line_end])
    required = (
        "$V_s(t)$",
        "$g(E_t)$",
        "Shallow",
        "Deep",
        "polymer",
        "HV+",
        "$V_s$ probe",
        "$V_s$ meter",
    )
    if not all(label in original for label in required):
        return None
    replacement = original
    replacements = (
        (
            "\\fill[cGray!6, rounded corners=1.2pt] (5.83, 4.12) rectangle (6.48, 4.37);",
            "\\fill[cGray!6, opacity=0.70, rounded corners=1.2pt] "
            "(5.83, 4.12) rectangle (6.48, 4.37);",
        ),
        (
            "\\draw[cGray!60!black, line width=0.30pt, rounded corners=1.2pt]\n"
            "  (5.83, 4.12) rectangle (6.48, 4.37);",
            "\\draw[cGray!48!black, line width=0.22pt, rounded corners=1.2pt]\n"
            "  (5.83, 4.12) rectangle (6.48, 4.37);",
        ),
        (
            "\\fill[cGray!70!black, rounded corners=1pt] (5.90, 4.20) rectangle (6.36, 4.33);",
            "\\fill[cGray!55!black, opacity=0.78, rounded corners=1pt] "
            "(5.90, 4.20) rectangle (6.36, 4.33);",
        ),
        (
            "\\fill[cGray!45!black, opacity=0.5] (5.92, 4.318) rectangle (6.34, 4.324);",
            "\\fill[cGray!45!black, opacity=0.20] (5.92, 4.318) rectangle (6.34, 4.324);",
        ),
        (
            "\\fill[cGray!6, rounded corners=1.2pt] (7.68, 3.70) rectangle (8.68, 4.22);",
            "\\fill[cGray!6, opacity=0.70, rounded corners=1.2pt] "
            "(7.68, 3.70) rectangle (8.68, 4.22);",
        ),
        (
            "\\draw[cGray!60!black, line width=0.30pt, rounded corners=1.2pt]\n"
            "  (7.68, 3.70) rectangle (8.68, 4.22);",
            "\\draw[cGray!48!black, line width=0.22pt, rounded corners=1.2pt]\n"
            "  (7.68, 3.70) rectangle (8.68, 4.22);",
        ),
        (
            "\\fill[cGray!70!black, rounded corners=1pt] (7.80, 4.05) rectangle (8.56, 4.17);",
            "\\fill[cGray!55!black, opacity=0.78, rounded corners=1pt] "
            "(7.80, 4.05) rectangle (8.56, 4.17);",
        ),
        (
            "\\fill[cGray!45!black, opacity=0.5] (7.82, 4.158) rectangle (8.54, 4.165);",
            "\\fill[cGray!45!black, opacity=0.20] (7.82, 4.158) rectangle (8.54, 4.165);",
        ),
        (
            "  \\node[font=\\sffamily\\bfseries\\fontsize{4}{4.8}\\selectfont, text=white,\n"
            "        inner sep=0pt] at (\\cx, 3.62) {$+$};",
            "  \\node[font=\\sffamily\\bfseries\\fontsize{4}{4.8}\\selectfont, text=white,\n"
            "        opacity=0.72, inner sep=0pt] at (\\cx, 3.62) {$+$};",
        ),
    )
    for old, new in replacements:
        replacement = replacement.replace(old, new)
    if replacement == original:
        return None
    if not all(label in replacement for label in required):
        return None
    return original, replacement, line_start, line_end


def _density_panel_e_template_applied(
    *,
    lines: list[str],
    selector: dict[str, Any],
) -> bool:
    if str(selector.get("panel") or "").upper() != "E":
        return False
    try:
        line_start = int(selector["line_start"])
        line_end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return False
    if line_start < 1 or line_end < line_start or line_end > len(lines):
        return False
    original = "".join(lines[line_start - 1 : line_end])
    required = (
        "$V_s(t)$",
        "$g(E_t)$",
        "Shallow",
        "Deep",
        "polymer",
        "HV+",
        "$V_s$ probe",
        "$V_s$ meter",
    )
    applied_fragments = (
        "\\fill[cGray!6, opacity=0.70, rounded corners=1.2pt] (5.83, 4.12) rectangle (6.48, 4.37);",
        "\\draw[cGray!48!black, line width=0.22pt, rounded corners=1.2pt]\n"
        "  (5.83, 4.12) rectangle (6.48, 4.37);",
        "\\fill[cGray!6, opacity=0.70, rounded corners=1.2pt] (7.68, 3.70) rectangle (8.68, 4.22);",
        "\\draw[cGray!48!black, line width=0.22pt, rounded corners=1.2pt]\n"
        "  (7.68, 3.70) rectangle (8.68, 4.22);",
        "        opacity=0.72, inner sep=0pt] at (\\cx, 3.62) {$+$};",
    )
    return all(label in original for label in required) and all(
        fragment in original for fragment in applied_fragments
    )


def _candidate_operation_for_spec(
    spec: dict[str, Any],
    *,
    lines: list[str],
    source_ref: str,
) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    family = str(spec.get("family") or "")
    selectors = spec.get("source_selectors")
    if not isinstance(selectors, list):
        return None, {"code": "missing_source_selectors", "candidate_id": str(spec.get("id"))}
    bound_selectors = [
        selector
        for selector in selectors
        if isinstance(selector, dict) and selector.get("binding_state") == "bound"
    ]
    if not bound_selectors:
        return None, {"code": "no_bound_source_selector", "candidate_id": str(spec.get("id"))}
    preferred_panel = {
        "hierarchy_rebalance": "C",
        "panel_c_hero_finish": "C",
        "apparatus_strengthen": "F",
        "panel_f_boundary_polish": "F",
        "panel_f_final_finish": "F",
        "panel_f_label_route_finish": "F",
        "panel_f_density_relief": "F",
        "panel_f_qtr_label_lane": "F",
        "panel_f_qtr_apparatus_lane": "F",
        "panel_f_force_gap_lane": "F",
        "panel_f_mechanical_anchor_lane": "F",
        "panel_f_leader_left_lane": "F",
        "panel_f_electrode_lead_lane": "F",
        "panel_f_auto_composite_lane": "F",
        "density_reduce": "E",
    }.get(family)
    selector = next(
        (item for item in bound_selectors if item.get("panel") == preferred_panel),
        bound_selectors[0],
    )
    if family == "apparatus_strengthen":
        panel_block = _apparatus_panel_block_status(lines=lines, selector=selector)
        if panel_block.get("state") == "replaceable":
            original = str(panel_block["original"])
            new_text = str(panel_block["replacement"])
            line_start = int(panel_block["line_start"])
            line_end = int(panel_block["line_end"])
            template_id = str(panel_block.get("template_id") or APPARATUS_PANEL_F_TEMPLATE_ID)
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_apparatus_strengthen_panel_block",
                "operation_scale": "panel_block",
                "template_id": template_id,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        if panel_block.get("state") == "already_applied":
            return None, {
                "code": "template_already_applied",
                "candidate_id": str(spec.get("id")),
                "family": family,
                "operation_scale": "panel_block",
                "template_id": APPARATUS_PANEL_F_TEMPLATE_ID,
                "panel": "F",
            }
    if family == "panel_f_boundary_polish":
        boundary_block = _panel_f_boundary_polish_replacement(lines=lines, selector=selector)
        if boundary_block is not None:
            original, new_text, line_start, line_end = boundary_block
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_panel_f_boundary_polish_panel_block",
                "operation_scale": "panel_block",
                "template_id": PANEL_F_BOUNDARY_POLISH_TEMPLATE_ID,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_f_boundary_polish_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": PANEL_F_BOUNDARY_POLISH_TEMPLATE_ID,
            "panel": "F",
        }
    if family == "panel_c_hero_finish":
        panel_c_block = _panel_c_hero_finish_replacement(lines=lines, selector=selector)
        if panel_c_block is not None:
            original, new_text, line_start, line_end = panel_c_block
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_panel_c_hero_finish_panel_block",
                "operation_scale": "panel_block",
                "template_id": PANEL_C_HERO_FINISH_TEMPLATE_ID,
                "panel": "C",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_c_hero_finish_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": PANEL_C_HERO_FINISH_TEMPLATE_ID,
            "panel": "C",
        }
    if family == "panel_f_final_finish":
        finish_block = _panel_f_final_finish_replacement(lines=lines, selector=selector)
        if finish_block is not None:
            original, new_text, line_start, line_end = finish_block
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_panel_f_final_finish_panel_block",
                "operation_scale": "panel_block",
                "template_id": PANEL_F_FINAL_FINISH_TEMPLATE_ID,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_f_final_finish_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": PANEL_F_FINAL_FINISH_TEMPLATE_ID,
            "panel": "F",
        }
    if family == "panel_f_label_route_finish":
        label_route_block = _panel_f_label_route_finish_replacement(
            lines=lines, selector=selector
        )
        if label_route_block is not None:
            original, new_text, line_start, line_end = label_route_block
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_panel_f_label_route_finish_panel_block",
                "operation_scale": "panel_block",
                "template_id": PANEL_F_LABEL_ROUTE_FINISH_TEMPLATE_ID,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_f_label_route_finish_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": PANEL_F_LABEL_ROUTE_FINISH_TEMPLATE_ID,
            "panel": "F",
        }
    if family == "panel_f_qtr_label_lane":
        requested_template_id = str(
            spec.get("template_id") or PANEL_F_QTR_LABEL_LANE_TEMPLATE_ID
        )
        qtr_block = _panel_f_qtr_label_lane_replacement(
            lines=lines,
            selector=selector,
            template_id=requested_template_id,
        )
        if qtr_block is not None:
            original, new_text, line_start, line_end = qtr_block
            template_id = _panel_f_qtr_label_lane_template_id(new_text)
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_panel_f_qtr_label_lane_panel_block",
                "operation_scale": "panel_block",
                "template_id": template_id,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_f_qtr_label_lane_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": PANEL_F_QTR_LABEL_LANE_TEMPLATE_ID,
            "panel": "F",
        }
    if family == "panel_f_qtr_apparatus_lane":
        qtr_apparatus_block = _panel_f_qtr_apparatus_lane_replacement(
            lines=lines, selector=selector
        )
        if qtr_apparatus_block is not None:
            original, new_text, line_start, line_end = qtr_apparatus_block
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_panel_f_qtr_apparatus_lane_panel_block",
                "operation_scale": "panel_block",
                "template_id": PANEL_F_QTR_APPARATUS_LANE_TEMPLATE_ID,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_f_qtr_apparatus_lane_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": PANEL_F_QTR_APPARATUS_LANE_TEMPLATE_ID,
            "panel": "F",
        }
    if family == "panel_f_force_gap_lane":
        force_gap_block = _panel_f_force_gap_lane_replacement(
            lines=lines, selector=selector
        )
        if force_gap_block is not None:
            original, new_text, line_start, line_end = force_gap_block
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_panel_f_force_gap_lane_panel_block",
                "operation_scale": "panel_block",
                "template_id": PANEL_F_FORCE_GAP_LANE_TEMPLATE_ID,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_f_force_gap_lane_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": PANEL_F_FORCE_GAP_LANE_TEMPLATE_ID,
            "panel": "F",
        }
    if family == "panel_f_mechanical_anchor_lane":
        mechanical_anchor_block = _panel_f_mechanical_anchor_lane_replacement(
            lines=lines, selector=selector
        )
        if mechanical_anchor_block is not None:
            original, new_text, line_start, line_end = mechanical_anchor_block
            operation = {
                "kind": "replace_text",
                "semantic_kind": (
                    "quality_search_panel_f_mechanical_anchor_lane_panel_block"
                ),
                "operation_scale": "panel_block",
                "template_id": PANEL_F_MECHANICAL_ANCHOR_LANE_TEMPLATE_ID,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_f_mechanical_anchor_lane_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": PANEL_F_MECHANICAL_ANCHOR_LANE_TEMPLATE_ID,
            "panel": "F",
        }
    if family == "panel_f_leader_left_lane":
        leader_left_block = _panel_f_leader_left_lane_replacement(
            lines=lines, selector=selector
        )
        if leader_left_block is not None:
            original, new_text, line_start, line_end = leader_left_block
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_panel_f_leader_left_lane_panel_block",
                "operation_scale": "panel_block",
                "template_id": PANEL_F_LEADER_LEFT_LANE_TEMPLATE_ID,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_f_leader_left_lane_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": PANEL_F_LEADER_LEFT_LANE_TEMPLATE_ID,
            "panel": "F",
        }
    if family == "panel_f_electrode_lead_lane":
        electrode_lead_block = _panel_f_electrode_lead_lane_replacement(
            lines=lines, selector=selector
        )
        if electrode_lead_block is not None:
            original, new_text, line_start, line_end = electrode_lead_block
            template_id = (
                PANEL_F_ELECTRODE_CONNECTOR_TEMPLATE_ID
                if _panel_f_v5f_electrode_connector_template_applied(new_text)
                else PANEL_F_ELECTRODE_LEAD_LANE_TEMPLATE_ID
            )
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_panel_f_electrode_lead_lane_panel_block",
                "operation_scale": "panel_block",
                "template_id": template_id,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_f_electrode_lead_lane_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": PANEL_F_ELECTRODE_LEAD_LANE_TEMPLATE_ID,
            "panel": "F",
        }
    if family == "panel_f_auto_composite_lane":
        template_id = str(
            spec.get("template_id") or PANEL_F_AUTO_COMPOSITE_LANE_TEMPLATE_ID
        )
        composite_block = _panel_f_auto_composite_lane_replacement(
            lines=lines, selector=selector, template_id=template_id
        )
        if composite_block is not None:
            original, new_text, line_start, line_end = composite_block
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_panel_f_auto_composite_lane_panel_block",
                "operation_scale": "panel_block",
                "template_id": template_id,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_f_auto_composite_lane_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": template_id,
            "panel": "F",
        }
    if family == "panel_f_density_relief":
        density_relief_block = _panel_f_density_relief_replacement(
            lines=lines, selector=selector
        )
        if density_relief_block is not None:
            original, new_text, line_start, line_end = density_relief_block
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_panel_f_density_relief_panel_block",
                "operation_scale": "panel_block",
                "template_id": PANEL_F_DENSITY_RELIEF_TEMPLATE_ID,
                "panel": "F",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
        return None, {
            "code": "no_panel_f_density_relief_block",
            "candidate_id": str(spec.get("id")),
            "family": family,
            "operation_scale": "panel_block",
            "template_id": PANEL_F_DENSITY_RELIEF_TEMPLATE_ID,
            "panel": "F",
        }
    if family == "density_reduce":
        if _density_panel_e_template_applied(lines=lines, selector=selector):
            return None, {
                "code": "template_already_applied",
                "candidate_id": str(spec.get("id")),
                "family": family,
                "operation_scale": "panel_block",
                "template_id": DENSITY_PANEL_E_TEMPLATE_ID,
                "panel": "E",
            }
        density_block = _density_panel_e_block_replacement(lines=lines, selector=selector)
        if density_block is not None:
            original, new_text, line_start, line_end = density_block
            operation = {
                "kind": "replace_text",
                "semantic_kind": "quality_search_density_reduce_panel_block",
                "operation_scale": "panel_block",
                "template_id": DENSITY_PANEL_E_TEMPLATE_ID,
                "panel": "E",
                "path": source_ref,
                "line_start": line_start,
                "line_end": line_end,
                "original": original,
                "replacement": new_text,
            }
            return operation, None
    minimum_pt = {
        "hierarchy_rebalance": 0.9,
        "apparatus_strengthen": 0.8,
        "panel_f_qtr_label_lane": 0.8,
        "panel_f_qtr_apparatus_lane": 0.8,
        "panel_f_force_gap_lane": 0.8,
        "panel_f_mechanical_anchor_lane": 0.8,
        "panel_f_leader_left_lane": 0.8,
        "panel_f_electrode_lead_lane": 0.8,
        "panel_f_auto_composite_lane": 0.8,
        "density_reduce": 0.65,
    }.get(family, 0.65)
    replacement = _line_width_replacement(
        lines=lines,
        selector=selector,
        minimum_pt=minimum_pt,
    )
    if replacement is None:
        return None, {
            "code": "no_supported_style_token",
            "candidate_id": str(spec.get("id")),
            "panel": str(selector.get("panel") or ""),
        }
    original, new_text, line_number = replacement
    operation = {
        "kind": "replace_text",
        "semantic_kind": f"quality_search_{family}",
        "operation_scale": "local_style_token",
        "template_id": LINE_WIDTH_TEMPLATE_ID,
        "panel": str(selector.get("panel") or ""),
        "path": source_ref,
        "line_start": line_number,
        "line_end": line_number,
        "original": original,
        "replacement": new_text,
    }
    return operation, None


def _candidate_set_from_specs(
    name: str,
    specs: list[dict[str, Any]],
    *,
    source_context: dict[str, Any],
    paths: runtime_paths.RuntimePaths,
) -> dict[str, Any]:
    source_path = _fixture_source_path(paths, name)
    source_ref = _source_reference(name)
    base = {
        "tex_hash": source_context.get("source_hash") or ZERO_HASH,
        "status_hash": ZERO_HASH,
        "intent_model_hash": ZERO_HASH,
    }
    if not source_path.is_file() or source_path.is_symlink():
        return {
            "schema": "figure-agent.candidate-set.v1",
            "fixture": name,
            "base": base,
            "candidates": [],
            "refusals": [{"code": str(source_context.get("source_state") or "source_missing")}],
        }
    lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
    candidates: list[dict[str, Any]] = []
    refusals: list[dict[str, str]] = []
    for spec in specs:
        if spec.get("family") == "null_baseline":
            continue
        operation, refusal = _candidate_operation_for_spec(spec, lines=lines, source_ref=source_ref)
        if operation is None:
            if refusal is not None:
                refusals.append(refusal)
            continue
        candidate_id = str(spec.get("id") or f"QS{len(candidates) + 1:03d}")
        target_panels = (
            spec.get("target_panels")
            if isinstance(spec.get("target_panels"), list)
            else []
        )
        operation_scale = str(operation.get("operation_scale") or "local_style_token")
        template_id = str(operation.get("template_id") or LINE_WIDTH_TEMPLATE_ID)
        target_panel = str(operation.get("panel") or "") or (
            target_panels[0] if target_panels else None
        )
        stable_hash_payload = {
            "candidate_id": candidate_id,
            "family": spec.get("family"),
            "source_hash": source_context.get("source_hash"),
            "operation": operation,
        }
        edit_class = (
            "quality_search_panel_block"
            if operation_scale == "panel_block"
            else "quality_search_style_token"
        )
        candidates.append(
            {
                "id": candidate_id,
                "family": spec.get("family"),
                "edit_class": edit_class,
                "edit_family": spec.get("family"),
                "operation_scale": operation_scale,
                "template_id": template_id,
                "expected_visual_movement": str(spec.get("expected_visual_movement") or ""),
                "protected_labels": spec.get("protected_labels", []),
                "design_moves": spec.get("design_moves", []),
                "target": {
                    "panel": target_panel,
                    "subregion": str(spec.get("target_scope") or "quality_search"),
                },
                "selectors": spec.get("source_selectors", []),
                "operations": [operation],
                "risk": "medium",
                "expected_delta": [str(spec.get("expected_visual_movement") or "")],
                "semantic_risks": [
                    "review-only art-direction candidate; scientific labels are protected"
                ],
                "boundedness": {
                    "changes": (
                        "one bounded panel block inside a bound panel region"
                        if operation_scale == "panel_block"
                        else "one style token inside a bound panel region"
                    ),
                    "does_not_change": [
                        "fixture source unless separately applied",
                        "accepted state",
                        "tracked golden exports",
                        "release state",
                    ],
                    "requires_human_review": True,
                },
                "rollback": {"strategy": "reverse_operations"},
                "verification": {
                    "required_commands": [
                        f"fig-agent compile {name} --strict",
                        f"fig-agent status {name} --json",
                    ]
                },
                "apply_authority": "review_only",
                "blocked_if": ["semantic_invariant_failed", "render_failed", "human_rejected"],
                "candidate_hash": _candidate_hash(stable_hash_payload),
            }
        )
    return {
        "schema": "figure-agent.candidate-set.v1",
        "fixture": name,
        "base": base,
        "candidates": candidates,
        "refusals": refusals,
    }


def _render_candidate_batch(
    name: str,
    candidate_set: dict[str, Any],
    *,
    paths: runtime_paths.RuntimePaths,
    candidate_set_path: Path,
) -> dict[str, Any]:
    candidates = [
        candidate
        for candidate in candidate_set.get("candidates", [])
        if isinstance(candidate, dict)
    ]
    if not candidates:
        return {
            "schema": "figure-agent.candidate-render-result.v1",
            "fixture": name,
            "render_mode": "none",
            "rendered": [],
        }
    source_text = _fixture_source_path(paths, name).read_text(encoding="utf-8")
    compile_eligible = (
        "\\documentclass" in source_text
        and "\\begin{document}" in source_text
        and (paths.examples_dir / name / "build" / f"{name}.png").is_file()
    )
    if not compile_eligible:
        result = candidate_render.render_candidate_set(
            name,
            candidate_set,
            workspace_root=paths.workspace_root,
            plugin_root=paths.plugin_root,
            candidate_set_path=candidate_set_path,
            compile=False,
            export=False,
            evaluate=False,
        )
        result["render_mode"] = "prepare_only"
        return result

    rendered: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = str(candidate.get("id") or "")
        target = candidate.get("target") if isinstance(candidate.get("target"), dict) else {}
        crop_panel = str(target.get("panel") or "") or None
        result = candidate_render.render_candidate_set(
            name,
            candidate_set,
            workspace_root=paths.workspace_root,
            plugin_root=paths.plugin_root,
            candidate_set_path=candidate_set_path,
            candidate_id=candidate_id,
            compile=True,
            export=True,
            crop_panel=crop_panel,
            evaluate=True,
        )
        rendered.extend(
            item for item in result.get("rendered", []) if isinstance(item, dict)
        )
    return {
        "schema": "figure-agent.candidate-render-result.v1",
        "fixture": name,
        "render_mode": "compile_export_crop_evaluate",
        "rendered": rendered,
    }


def _candidate_manifest_path(
    paths: runtime_paths.RuntimePaths,
    name: str,
    candidate_id: str,
) -> Path:
    return (
        paths.examples_dir
        / name
        / "build"
        / "candidates"
        / candidate_id
        / "candidate_manifest.json"
    )


def _render_manifest_path(paths: runtime_paths.RuntimePaths, name: str, candidate_id: str) -> Path:
    return (
        paths.examples_dir
        / name
        / "build"
        / "candidates"
        / candidate_id
        / "render_manifest.json"
    )


def _rank_rendered_candidates(
    name: str,
    candidate_set: dict[str, Any],
    *,
    paths: runtime_paths.RuntimePaths,
) -> list[dict[str, Any]]:
    scores: list[dict[str, Any]] = []
    candidates_by_id = {
        str(candidate.get("id")): candidate
        for candidate in candidate_set.get("candidates", [])
        if isinstance(candidate, dict)
    }
    for candidate_id, candidate in candidates_by_id.items():
        manifest_path = _candidate_manifest_path(paths, name, candidate_id)
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        render_manifest_path = _render_manifest_path(paths, name, candidate_id)
        render_manifest = (
            json.loads(render_manifest_path.read_text(encoding="utf-8"))
            if render_manifest_path.is_file()
            else None
        )
        scores.append(
            candidate_rank.score_manifest(
                manifest,
                render_manifest=render_manifest,
                candidate=candidate,
            )
        )
    return sorted(
        scores,
        key=lambda score: (-float(score.get("rank_score") or 0.0), str(score.get("candidate_id"))),
    )


def _fixture_artifact_path(
    paths: runtime_paths.RuntimePaths,
    name: str,
    relative: Any,
) -> Path | None:
    if not isinstance(relative, str) or not relative:
        return None
    example_dir = paths.examples_dir / name
    resolved = (example_dir / relative).resolve()
    try:
        resolved.relative_to(example_dir.resolve())
    except ValueError:
        return None
    return resolved


def _write_contact_sheet(
    *,
    entries: list[tuple[str, Path]],
    out_path: Path,
    max_width: int = 520,
) -> None:
    if not entries:
        return
    if out_path.is_symlink():
        raise ValueError(f"refusing to write through symlink: {out_path}")
    _ensure_output_dir(out_path.parent)
    from PIL import Image, ImageDraw

    tiles: list[tuple[str, Image.Image]] = []
    label_height = 30
    padding = 12
    for label, path in entries:
        with Image.open(path) as image:
            tile = image.convert("RGB")
        if tile.width > max_width:
            height = max(1, round(tile.height * (max_width / tile.width)))
            tile = tile.resize((max_width, height))
        tiles.append((label, tile))
    tile_width = max(tile.width for _label, tile in tiles)
    tile_height = max(tile.height for _label, tile in tiles)
    sheet_width = padding + len(tiles) * (tile_width + padding)
    sheet_height = padding + label_height + tile_height + padding
    sheet = Image.new("RGB", (sheet_width, sheet_height), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (label, tile) in enumerate(tiles):
        x = padding + index * (tile_width + padding)
        y = padding + label_height
        draw.text((x, padding), label, fill=(20, 20, 20))
        sheet.paste(tile, (x, y))
        draw.rectangle(
            [x, y, x + tile.width - 1, y + tile.height - 1],
            outline=(190, 190, 190),
        )
    sheet.save(out_path)


def _quality_search_visual_evidence(
    name: str,
    render_results: dict[str, Any],
    *,
    run_dir: Path,
    paths: runtime_paths.RuntimePaths,
) -> dict[str, Any]:
    render_mode = str(render_results.get("render_mode") or "unknown")
    out_dir = run_dir / "visual_evidence"
    original_full = paths.examples_dir / name / "build" / f"{name}.png"
    manifest: dict[str, Any] = {
        "schema": "figure-agent.quality-search-visual-evidence.v0",
        "fixture": name,
        "render_mode": render_mode,
        "state": "not_applicable",
        "full_comparisons": [],
        "panel_comparisons": [],
        "contact_sheets": [],
        "min_full_changed_pixel_ratio": None,
    }
    rendered = [
        item for item in render_results.get("rendered", []) if isinstance(item, dict)
    ]
    if render_mode != "compile_export_crop_evaluate" or not rendered:
        return manifest
    if not original_full.is_file():
        manifest["state"] = "blocked"
        manifest["diagnostics"] = [
            {
                "stage": "visual_evidence",
                "category": "missing_original_full_render",
                "message": f"build/{name}.png not found",
            }
        ]
        return manifest

    _ensure_output_dir(out_dir)
    full_entries: list[tuple[str, Path]] = [("current", original_full)]
    full_ratios: list[float] = []
    for rendered_item in rendered:
        candidate_id = str(rendered_item.get("candidate_id") or "unknown")
        render_manifest, error = _load_candidate_render_manifest(paths, name, rendered_item)
        if render_manifest is None:
            manifest.setdefault("diagnostics", []).append(
                {
                    "stage": "visual_evidence",
                    "category": str(error or "render_manifest_missing"),
                    "candidate_id": candidate_id,
                }
            )
            continue
        artifacts = render_manifest.get("artifacts")
        artifacts = artifacts if isinstance(artifacts, dict) else {}
        candidate_png = _fixture_artifact_path(paths, name, artifacts.get("png"))
        if candidate_png is None or not candidate_png.is_file():
            manifest.setdefault("diagnostics", []).append(
                {
                    "stage": "visual_evidence",
                    "category": "candidate_full_render_missing",
                    "candidate_id": candidate_id,
                }
            )
            continue
        full_entries.append((candidate_id, candidate_png))
        comparison = candidate_visual_eval.compare_image_pair(original_full, candidate_png)
        visual_deltas = (
            comparison.get("visual_deltas")
            if isinstance(comparison.get("visual_deltas"), dict)
            else {}
        )
        ratio = None
        try:
            ratio = float(visual_deltas.get("changed_pixel_ratio"))
        except (TypeError, ValueError):
            ratio = None
        if ratio is not None:
            full_ratios.append(ratio)
        manifest["full_comparisons"].append(
            {
                "candidate_id": candidate_id,
                "status": comparison.get("status"),
                "visual_deltas": visual_deltas,
                "candidate_png": _workspace_relative(paths, candidate_png),
            }
        )

        before_crop = _fixture_artifact_path(paths, name, artifacts.get("before_crop"))
        after_crop = _fixture_artifact_path(paths, name, artifacts.get("after_crop"))
        if before_crop is not None and after_crop is not None:
            panel = str(render_manifest.get("panel") or "unknown")
            panel_sheet = out_dir / f"{candidate_id}_panel_{panel}_contact_sheet.png"
            _write_contact_sheet(
                entries=[
                    (f"{candidate_id} before", before_crop),
                    (f"{candidate_id} after", after_crop),
                ],
                out_path=panel_sheet,
            )
            manifest["panel_comparisons"].append(
                {
                    "candidate_id": candidate_id,
                    "panel": panel,
                    "before_crop": _workspace_relative(paths, before_crop),
                    "after_crop": _workspace_relative(paths, after_crop),
                    "contact_sheet": _workspace_relative(paths, panel_sheet),
                    "visual_deltas": render_manifest.get("visual_deltas")
                    if isinstance(render_manifest.get("visual_deltas"), dict)
                    else {},
                }
            )

    full_sheet = out_dir / "candidate_full_contact_sheet.png"
    _write_contact_sheet(entries=full_entries, out_path=full_sheet)
    manifest["contact_sheets"].append(
        {
            "kind": "candidate_full_contact_sheet",
            "path": _workspace_relative(paths, full_sheet),
        }
    )
    manifest["state"] = "complete"
    manifest["min_full_changed_pixel_ratio"] = min(full_ratios) if full_ratios else None
    return manifest


def _ratio_from_deltas(payload: Any) -> float | None:
    if not isinstance(payload, dict):
        return None
    try:
        return float(payload.get("changed_pixel_ratio"))
    except (TypeError, ValueError):
        return None


def _visual_change_ratios_by_candidate(
    visual_evidence: dict[str, Any] | None,
) -> tuple[dict[str, float], dict[str, float]]:
    if not isinstance(visual_evidence, dict):
        return ({}, {})

    def collect(key: str) -> dict[str, float]:
        values: dict[str, float] = {}
        comparisons = visual_evidence.get(key)
        if not isinstance(comparisons, list):
            return values
        for item in comparisons:
            if not isinstance(item, dict):
                continue
            candidate_id = item.get("candidate_id")
            ratio = _ratio_from_deltas(item.get("visual_deltas"))
            if candidate_id is not None and ratio is not None:
                values[str(candidate_id)] = ratio
        return values

    return (collect("full_comparisons"), collect("panel_comparisons"))


def _ranking_changed_pixel_ratio(ranking: dict[str, Any] | None) -> float | None:
    if not isinstance(ranking, dict):
        return None
    scores = ranking.get("scores")
    ratio = _ratio_from_deltas(scores)
    if ratio is not None:
        return ratio
    return _ratio_from_deltas(ranking)


def _non_marginal_visual_change(
    *,
    full_changed_pixel_ratio: float | None,
    panel_changed_pixel_ratio: float | None,
) -> bool:
    return (
        full_changed_pixel_ratio is not None
        and full_changed_pixel_ratio >= NON_MARGINAL_FULL_CHANGED_PIXEL_RATIO
    ) or (
        panel_changed_pixel_ratio is not None
        and panel_changed_pixel_ratio >= NON_MARGINAL_PANEL_CHANGED_PIXEL_RATIO
    )


def _quality_search_memory_events(
    *,
    name: str,
    run_id: str,
    candidate_set: dict[str, Any],
    candidate_rankings: list[dict[str, Any]],
    visual_evidence: dict[str, Any],
    paths: runtime_paths.RuntimePaths,
    run_dir: Path,
    selected_acceptance_recommendation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = {
        "schema": "figure-agent.quality-search-memory-events.v0",
        "fixture": name,
        "run_id": run_id,
        "events": [],
        "event_count": 0,
    }
    if visual_evidence.get("state") != "complete":
        return {
            **base,
            "reason": "visual evidence is not complete; no learnable render outcome recorded",
        }
    candidates = [
        candidate
        for candidate in candidate_set.get("candidates", [])
        if isinstance(candidate, dict)
    ]
    rankings_by_id = {
        str(ranking.get("candidate_id")): ranking
        for ranking in candidate_rankings
        if isinstance(ranking, dict)
    }
    full_by_id = {
        str(item.get("candidate_id")): item
        for item in visual_evidence.get("full_comparisons", [])
        if isinstance(item, dict)
    }
    panel_by_id = {
        str(item.get("candidate_id")): item
        for item in visual_evidence.get("panel_comparisons", [])
        if isinstance(item, dict)
    }
    events: list[dict[str, Any]] = []
    source_artifact = _workspace_relative(paths, run_dir / "visual_evidence_000.json")
    recommendation_candidate_id = (
        str(selected_acceptance_recommendation.get("candidate_id") or "")
        if isinstance(selected_acceptance_recommendation, dict)
        else ""
    )
    created_at = _utc_stamp()
    for candidate in candidates:
        candidate_id = str(candidate.get("id") or "")
        ranking = rankings_by_id.get(candidate_id)
        if not isinstance(ranking, dict):
            continue
        full = full_by_id.get(candidate_id, {})
        panel = panel_by_id.get(candidate_id, {})
        full_ratio = _ratio_from_deltas(
            full.get("visual_deltas") if isinstance(full, dict) else None
        )
        panel_ratio = _ratio_from_deltas(
            panel.get("visual_deltas") if isinstance(panel, dict) else None
        )
        render_positive = (
            ranking.get("render_status") == "rendered_needs_human_review"
            and full_ratio is not None
            and full_ratio > 0.0
            and (panel_ratio is None or panel_ratio > 0.0)
        )
        outcome_state = "neutral" if render_positive else "blocked_by_render_evidence"
        outcome_reason = (
            "render_positive_human_unreviewed"
            if render_positive
            else "render_or_pixel_evidence_failed"
        )
        post_state = {
            "render_status": str(ranking.get("render_status") or "unknown"),
            "effective_apply_authority": str(
                ranking.get("effective_apply_authority") or "unknown"
            ),
        }
        target = candidate.get("target") if isinstance(candidate.get("target"), dict) else {}
        payload = {
            "fixture": name,
            "run_id": run_id,
            "event_type": "candidate_ranked",
            "candidate_id": candidate_id,
            "edit_family": candidate.get("edit_family") or candidate.get("family"),
            "target": target,
            "outcome_state": outcome_state,
        }
        evidence_paths = [source_artifact]
        if isinstance(panel, dict) and isinstance(panel.get("contact_sheet"), str):
            evidence_paths.append(str(panel["contact_sheet"]))
        if visual_evidence.get("contact_sheets"):
            contact_sheets = visual_evidence.get("contact_sheets")
            if isinstance(contact_sheets, list) and isinstance(contact_sheets[0], dict):
                path = contact_sheets[0].get("path")
                if isinstance(path, str):
                    evidence_paths.append(path)
        recommendation_evidence = {}
        if (
            isinstance(selected_acceptance_recommendation, dict)
            and candidate_id == recommendation_candidate_id
        ):
            recommendation_evidence = (
                selected_acceptance_recommendation.get("evidence")
                if isinstance(selected_acceptance_recommendation.get("evidence"), dict)
                else {}
            )
            post_state.update(
                {
                    "acceptance_recommendation_status": str(
                        selected_acceptance_recommendation.get("status") or "unknown"
                    ),
                    "acceptance_recommendation": str(
                        selected_acceptance_recommendation.get("recommendation")
                        or "unknown"
                    ),
                    "acceptance_recommendation_authority": str(
                        selected_acceptance_recommendation.get("authority") or "unknown"
                    ),
                    "semantic_precheck_status": str(
                        recommendation_evidence.get("semantic_precheck_status")
                        or "unknown"
                    ),
                    "review_packet_status": str(
                        recommendation_evidence.get("review_packet_status")
                        or "unknown"
                    ),
                    "apply_readiness_status": str(
                        recommendation_evidence.get("apply_readiness_status")
                        or "unknown"
                    ),
                }
            )
            if selected_acceptance_recommendation.get("status") == "auto_accept_recommended":
                outcome_reason = "auto_accept_recommended_not_applied"
            evidence_paths.extend(
                [
                    _workspace_relative(
                        paths, run_dir / "selected_semantic_precheck_000.json"
                    ),
                    _workspace_relative(paths, run_dir / "selected_review_packet_000.json"),
                    _workspace_relative(
                        paths,
                        run_dir / "selected_acceptance_recommendation_000.json",
                    ),
                ]
            )
        events.append(
            {
                "schema": "figure-agent.quality-memory-event.v1",
                "fixture": name,
                "event_id": _sha256_text(
                    json.dumps(payload, sort_keys=True, separators=(",", ":"))
                ),
                "event_type": "candidate_ranked",
                "created_at": created_at,
                "source_artifact": source_artifact,
                "candidate_id": candidate_id,
                "edit_family": str(
                    candidate.get("edit_family") or candidate.get("family") or "unknown"
                ),
                "target": {
                    "panel": str(target.get("panel") or "unknown"),
                    "subregion": str(target.get("subregion") or "unknown"),
                },
                "pre_state": {},
                "post_state": post_state,
                "outcome": {
                    "state": outcome_state,
                    "quality_movement": "neutral" if render_positive else None,
                    "reason": outcome_reason,
                    "evidence_paths": evidence_paths,
                },
                "metrics": {
                    "candidate_rank_score": ranking.get("rank_score"),
                    "full_changed_pixel_ratio": full_ratio,
                    "panel_changed_pixel_ratio": panel_ratio,
                    "semantic_precheck_status": recommendation_evidence.get(
                        "semantic_precheck_status"
                    ),
                    "apply_readiness_status": recommendation_evidence.get(
                        "apply_readiness_status"
                    ),
                    "acceptance_recommendation_status": (
                        selected_acceptance_recommendation.get("status")
                        if isinstance(selected_acceptance_recommendation, dict)
                        and candidate_id == recommendation_candidate_id
                        else None
                    ),
                },
            }
        )
    return {
        **base,
        "events": events,
        "event_count": len(events),
        "reason": (
            "render-positive outcomes are recorded as neutral until human acceptance "
            "or post-apply evidence upgrades them"
        ),
    }


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _current_source_hash(paths: runtime_paths.RuntimePaths, name: str) -> str | None:
    source_path = _fixture_source_path(paths, name)
    if not source_path.is_file() or source_path.is_symlink():
        return None
    return _sha256_text(source_path.read_text(encoding="utf-8"))


def _render_stage_status(render_manifest: dict[str, Any], stage: str) -> str:
    stages = render_manifest.get("stages")
    if not isinstance(stages, dict):
        return "missing"
    value = stages.get(stage)
    if not isinstance(value, dict):
        return "missing"
    return str(value.get("status") or "missing")


def _load_candidate_render_manifest(
    paths: runtime_paths.RuntimePaths,
    name: str,
    rendered_item: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    relative = rendered_item.get("render_manifest")
    if not isinstance(relative, str) or not relative:
        return None, "render_manifest_missing"
    example_dir = paths.examples_dir / name
    manifest_path = (example_dir / relative).resolve()
    try:
        manifest_path.relative_to(example_dir.resolve())
    except ValueError:
        return None, "render_manifest_escaped_fixture"
    if not manifest_path.is_file():
        return None, "render_manifest_file_missing"
    return json.loads(manifest_path.read_text(encoding="utf-8")), None


def _quality_search_contract_verdict(
    *,
    name: str,
    run_id: str,
    manifest: dict[str, Any],
    plan: dict[str, Any],
    policy: dict[str, Any],
    source_context: dict[str, Any],
    candidate_set: dict[str, Any],
    render_results: dict[str, Any],
    visual_evidence: dict[str, Any],
    candidate_rankings: list[dict[str, Any]],
    decision: dict[str, Any],
    selected_semantic_precheck: dict[str, Any] | None = None,
    selected_review_packet: dict[str, Any] | None = None,
    selected_acceptance_recommendation: dict[str, Any] | None = None,
    recommendation_experience: dict[str, Any] | None = None,
    selected_attempt: dict[str, Any] | None = None,
    convergence_decision: dict[str, Any] | None = None,
    paths: runtime_paths.RuntimePaths,
) -> dict[str, Any]:
    failures: list[dict[str, str]] = []

    def require(condition: bool, code: str, message: str) -> None:
        if not condition:
            failures.append({"code": code, "message": message})

    candidates = [
        candidate
        for candidate in candidate_set.get("candidates", [])
        if isinstance(candidate, dict)
    ]
    rendered = [
        item for item in render_results.get("rendered", []) if isinstance(item, dict)
    ]
    render_mode = str(render_results.get("render_mode") or "unknown")
    candidate_ids = {str(candidate.get("id")) for candidate in candidates}
    ranking_ids = {str(score.get("candidate_id")) for score in candidate_rankings}
    evaluated_count = 0
    changed_pixel_ratios: list[float] = []
    full_changed_pixel_ratios: list[float] = []
    prerequisite_required = decision.get("kind") == "prerequisite_required"
    classifications = plan.get("classifications")
    classifications = classifications if isinstance(classifications, list) else []
    diagnostic_search_bypass = any(
        isinstance(item, dict)
        and item.get("diagnostic_bypass") == "stale_critique_search"
        and item.get("blocks_search") is False
        for item in classifications
    )

    require(
        manifest.get("status") == "dry_run_complete",
        "status_not_dry_complete",
        "run did not finish as dry_run_complete",
    )
    require(
        manifest.get("mode") == "execute_dry_witness",
        "mode_not_dry_witness",
        "run mode is not execute_dry_witness",
    )
    require(
        policy.get("source_mutation") == "forbidden",
        "source_mutation_not_forbidden",
        "policy does not forbid source mutation",
    )
    require(
        policy.get("release_mutation") == "forbidden",
        "release_mutation_not_forbidden",
        "policy does not forbid release mutation",
    )
    require(
        decision.get("source_mutation") == "not_performed",
        "source_mutation_performed",
        "decision indicates source mutation",
    )
    if not prerequisite_required:
        require(
            bool(candidates),
            "candidate_batch_empty",
            "candidate_set has no materialized candidates",
        )
        require(
            len(rendered) == len(candidates),
            "render_count_mismatch",
            "rendered candidate count does not match candidate count",
        )
    require(
        render_mode in {"none", "prepare_only", "compile_export_crop_evaluate"},
        "render_mode_unknown",
        "render_results does not declare a known render_mode",
    )
    if not prerequisite_required:
        require(
            ranking_ids == candidate_ids,
            "ranking_id_mismatch",
            "candidate rankings do not cover exactly the materialized candidates",
        )
    require(
        all(candidate.get("apply_authority") == "review_only" for candidate in candidates),
        "non_review_only_candidate",
        "at least one materialized candidate is not review_only",
    )
    require(
        all(
            score.get("effective_apply_authority") == "review_only"
            for score in candidate_rankings
        ),
        "non_review_only_ranking",
        "at least one ranking is not review_only",
    )
    current_hash = _current_source_hash(paths, name)
    require(
        current_hash is not None and current_hash == source_context.get("source_hash"),
        "source_hash_drift",
        "current source hash differs from source_context hash",
    )
    selected_candidate_ready = (
        decision.get("candidate_state") == NON_MARGINAL_REVIEW_CANDIDATE_STATE
    )
    selected_apply_readiness = (
        selected_review_packet.get("apply_readiness")
        if isinstance(selected_review_packet, dict)
        and isinstance(selected_review_packet.get("apply_readiness"), dict)
        else {}
    )
    selected_attempt_journal = (
        selected_attempt.get("journal_constraints")
        if isinstance(selected_attempt, dict)
        and isinstance(selected_attempt.get("journal_constraints"), dict)
        else {}
    )
    selected_attempt_semantic = (
        selected_attempt.get("semantic_score")
        if isinstance(selected_attempt, dict)
        and isinstance(selected_attempt.get("semantic_score"), dict)
        else {}
    )
    selected_attempt_outputs = (
        selected_attempt.get("outputs")
        if isinstance(selected_attempt, dict)
        and isinstance(selected_attempt.get("outputs"), dict)
        else {}
    )
    selected_attempt_id = (
        str(selected_attempt.get("attempt_id"))
        if isinstance(selected_attempt, dict) and selected_attempt.get("attempt_id")
        else None
    )
    selected_convergence_state = (
        convergence_decision.get("decision")
        if isinstance(convergence_decision, dict)
        else None
    )
    convergence_blocks_acceptance = (
        selected_convergence_state is not None and selected_convergence_state != "accept"
    )
    if selected_candidate_ready:
        require(
            isinstance(selected_semantic_precheck, dict)
            and selected_semantic_precheck.get("status") == "pass",
            "selected_semantic_precheck_not_passed",
            "selected non-marginal candidate lacks passing semantic precheck",
        )
        require(
            isinstance(selected_review_packet, dict)
            and selected_review_packet.get("status") == "ready",
            "selected_review_packet_not_ready",
            "selected non-marginal candidate lacks ready review packet",
        )
        require(
            isinstance(selected_acceptance_recommendation, dict)
            and selected_acceptance_recommendation.get("is_acceptance_artifact") is False,
            "selected_acceptance_recommendation_is_authoritative",
            "selected acceptance recommendation must not masquerade as acceptance",
        )
        if diagnostic_search_bypass:
            require(
                isinstance(selected_acceptance_recommendation, dict)
                and selected_acceptance_recommendation.get("status") == "blocked"
                and selected_acceptance_recommendation.get("recommendation") == "defer",
                "diagnostic_bypass_acceptance_not_blocked",
                "stale-critique diagnostic search must defer acceptance",
            )
        elif convergence_blocks_acceptance:
            require(
                isinstance(selected_acceptance_recommendation, dict)
                and selected_acceptance_recommendation.get("status") == "blocked"
                and selected_acceptance_recommendation.get("recommendation") == "defer",
                "convergence_non_accept_not_deferred",
                "convergence non-accept decisions must defer acceptance",
            )
            require(
                isinstance(selected_attempt, dict),
                "selected_attempt_missing",
                "selected convergence decision lacks selected attempt evidence",
            )
            require(
                isinstance(convergence_decision, dict)
                and convergence_decision.get("attempt_id") == selected_attempt_id,
                "selected_convergence_current_attempt_mismatch",
                "convergence decision does not evaluate the selected attempt",
            )
        else:
            require(
                selected_apply_readiness.get("status") == "ready_for_local_acceptance",
                "selected_apply_readiness_not_ready",
                "selected non-marginal candidate is not ready for local acceptance",
            )
            require(
                isinstance(selected_acceptance_recommendation, dict)
                and selected_acceptance_recommendation.get("status")
                == "auto_accept_recommended",
                "selected_acceptance_recommendation_not_ready",
                "selected non-marginal candidate lacks automatic acceptance recommendation",
            )
            require(
                isinstance(recommendation_experience, dict)
                and recommendation_experience.get("writes")
                == [f"docs/experience-log/{name}.jsonl"],
                "selected_recommendation_experience_log_missing",
                "selected automatic recommendation was not persisted to durable experience log",
            )
            experience_record = (
                recommendation_experience.get("record")
                if isinstance(recommendation_experience, dict)
                and isinstance(recommendation_experience.get("record"), dict)
                else {}
            )
            experience_outcome = (
                experience_record.get("outcome")
                if isinstance(experience_record.get("outcome"), dict)
                else {}
            )
            require(
                experience_outcome.get("human_decision_kind")
                == "auto_accept_recommended",
                "selected_recommendation_experience_kind_missing",
                "selected durable experience row does not mark auto_accept_recommended",
            )
            require(
                experience_outcome.get("apply_status") == "blocked",
                "selected_recommendation_experience_apply_status_invalid",
                "selected durable experience row must remain blocked until explicit apply",
            )
            require(
                isinstance(selected_attempt, dict),
                "selected_attempt_missing",
                "selected automatic recommendation lacks selected attempt evidence",
            )
            require(
                selected_attempt_journal.get("passed") is True,
                "selected_attempt_journal_constraints_failed",
                "selected attempt did not pass hard journal constraints",
            )
            require(
                selected_attempt_semantic.get("complete") is True,
                "selected_attempt_semantic_incomplete",
                "selected attempt did not pass semantic correctness",
            )
            require(
                bool(selected_attempt_outputs.get("editable"))
                and bool(selected_attempt_outputs.get("pdf"))
                and bool(selected_attempt_outputs.get("png"))
                and bool(selected_attempt_outputs.get("svg")),
                "selected_attempt_outputs_incomplete",
                "selected attempt is missing editable/pdf/png/svg outputs",
            )
            require(
                isinstance(convergence_decision, dict)
                and convergence_decision.get("decision") == "accept",
                "selected_convergence_decision_not_accept",
                "selected automatic recommendation lacks convergence accept decision",
            )
            require(
                isinstance(convergence_decision, dict)
                and convergence_decision.get("selected_attempt_id")
                == selected_attempt_id,
                "selected_convergence_attempt_mismatch",
                "convergence decision does not select the selected attempt",
            )
    all_candidates_have_bound_selector = all(
        any(
            isinstance(selector, dict) and selector.get("binding_state") == "bound"
            for selector in candidate.get("selectors", [])
            if isinstance(selector, dict)
        )
        for candidate in candidates
    )
    if not prerequisite_required:
        require(
            all_candidates_have_bound_selector,
            "candidate_selectors_unbound",
            "at least one materialized candidate lacks a bound source selector",
        )
    if render_mode == "compile_export_crop_evaluate":
        require(
            visual_evidence.get("state") == "complete",
            "visual_evidence_not_complete",
            "visual evidence did not complete for rendered candidate batch",
        )
        full_comparisons = visual_evidence.get("full_comparisons")
        full_comparisons = full_comparisons if isinstance(full_comparisons, list) else []
        require(
            len(full_comparisons) == len(candidates),
            "full_comparison_count_mismatch",
            "full-render comparisons do not cover every materialized candidate",
        )
        for comparison in full_comparisons:
            if not isinstance(comparison, dict):
                continue
            candidate_id = str(comparison.get("candidate_id") or "unknown")
            visual_deltas = comparison.get("visual_deltas")
            ratio = None
            if isinstance(visual_deltas, dict):
                try:
                    ratio = float(visual_deltas.get("changed_pixel_ratio"))
                except (TypeError, ValueError):
                    ratio = None
            require(
                ratio is not None and ratio > 0.0,
                f"full_changed_pixel_ratio_not_positive:{candidate_id}",
                f"{candidate_id} full-render comparison did not record positive pixel change",
            )
            if ratio is not None:
                full_changed_pixel_ratios.append(ratio)
        for rendered_item in rendered:
            candidate_id = str(rendered_item.get("candidate_id") or "unknown")
            render_manifest, error = _load_candidate_render_manifest(
                paths,
                name,
                rendered_item,
            )
            if render_manifest is None:
                require(
                    False,
                    f"{error}:{candidate_id}",
                    f"{candidate_id} render manifest is unavailable",
                )
                continue
            require(
                _render_stage_status(render_manifest, "compile") == "success",
                f"compile_not_success:{candidate_id}",
                f"{candidate_id} compile stage did not succeed",
            )
            require(
                _render_stage_status(render_manifest, "export") == "success",
                f"export_not_success:{candidate_id}",
                f"{candidate_id} export stage did not succeed",
            )
            crop_was_requested = bool(render_manifest.get("panel"))
            if crop_was_requested:
                require(
                    _render_stage_status(render_manifest, "crop") == "success",
                    f"crop_not_success:{candidate_id}",
                    f"{candidate_id} crop stage did not succeed",
                )
            evaluate_status = _render_stage_status(render_manifest, "evaluate")
            require(
                evaluate_status == "rendered_needs_human_review",
                f"evaluate_not_rendered:{candidate_id}",
                f"{candidate_id} evaluate stage did not produce reviewable render evidence",
            )
            if evaluate_status == "rendered_needs_human_review":
                evaluated_count += 1
            visual_deltas = render_manifest.get("visual_deltas")
            ratio = None
            if isinstance(visual_deltas, dict):
                try:
                    ratio = float(visual_deltas.get("changed_pixel_ratio"))
                except (TypeError, ValueError):
                    ratio = None
            require(
                ratio is not None and ratio > 0.0,
                f"changed_pixel_ratio_not_positive:{candidate_id}",
                f"{candidate_id} render comparison did not record positive pixel change",
            )
            if ratio is not None:
                changed_pixel_ratios.append(ratio)

    return {
        "schema": "figure-agent.quality-search-depone-verdict.v0",
        "fixture": name,
        "run_id": run_id,
        "contract_status": "pass" if not failures else "fail",
        "failures": failures,
        "checks": {
            "decision_kind": decision.get("kind"),
            "prerequisite_required": prerequisite_required,
            "diagnostic_search_bypass": diagnostic_search_bypass,
            "candidate_count": len(candidates),
            "rendered_count": len(rendered),
            "render_mode": render_mode,
            "evaluated_count": evaluated_count,
            "min_changed_pixel_ratio": (
                min(changed_pixel_ratios) if changed_pixel_ratios else None
            ),
            "visual_evidence_state": visual_evidence.get("state"),
            "full_comparison_count": len(visual_evidence.get("full_comparisons", []))
            if isinstance(visual_evidence.get("full_comparisons"), list)
            else 0,
            "min_full_changed_pixel_ratio": (
                min(full_changed_pixel_ratios) if full_changed_pixel_ratios else None
            ),
            "ranking_count": len(candidate_rankings),
            "source_hash": source_context.get("source_hash"),
            "selected_candidate_id": decision.get("selected_candidate_id"),
            "selected_family": decision.get("selected_family"),
            "selected_candidate_state": decision.get("candidate_state"),
            "selected_semantic_precheck_status": (
                selected_semantic_precheck.get("status")
                if isinstance(selected_semantic_precheck, dict)
                else None
            ),
            "selected_review_packet_status": (
                selected_review_packet.get("status")
                if isinstance(selected_review_packet, dict)
                else None
            ),
            "selected_apply_readiness_status": selected_apply_readiness.get("status"),
            "selected_acceptance_recommendation_status": (
                selected_acceptance_recommendation.get("status")
                if isinstance(selected_acceptance_recommendation, dict)
                else None
            ),
            "selected_recommendation_experience_log_status": (
                "written"
                if isinstance(recommendation_experience, dict)
                and recommendation_experience.get("writes")
                == [f"docs/experience-log/{name}.jsonl"]
                else None
            ),
            "selected_attempt_journal_constraints_passed": (
                selected_attempt_journal.get("passed")
                if isinstance(selected_attempt_journal, dict)
                else None
            ),
            "selected_attempt_semantic_complete": (
                selected_attempt_semantic.get("complete")
                if isinstance(selected_attempt_semantic, dict)
                else None
            ),
            "selected_attempt_output_formats": sorted(
                key
                for key in ("editable", "pdf", "png", "svg")
                if selected_attempt_outputs.get(key)
            ),
            "selected_convergence_decision": (
                convergence_decision.get("decision")
                if isinstance(convergence_decision, dict)
                else None
            ),
        },
        "mutation_boundary": {
            "source_mutation": "not_performed",
            "release_mutation": "forbidden",
            "accepted_golden_final_mutation": "forbidden",
        },
    }


def _depone_plan_for_quality_search(
    *,
    name: str,
    run_id: str,
    verdict_hash: str,
) -> dict[str, Any]:
    return {
        "schema_version": DEPONE_PLAN_SCHEMA,
        "plan_id": f"quality-search-depone-{run_id}",
        "created_by": "figure-agent",
        "source_prompt": "Verify quality-search execute evidence contract",
        "activation": {
            "decision": "activate",
            "matched_thresholds": ["adversarial-verification"],
            "downgrade_target": None,
            "reason": "Depone verification over generated quality-search evidence.",
        },
        "objective": (
            "Verify quality-search execute materialized review-only candidates "
            "without source, release, accepted, golden, or final mutation."
        ),
        "surfaces": [
            {
                "id": name,
                "kind": "quality-search-run",
                "locator": run_id,
                "access_mode": "read-only",
            }
        ],
        "assumptions": [],
        "patterns": ["Adversarial Verify"],
        "phases": [
            {
                "id": "phase-1",
                "name": "Generate quality-search evidence",
                "entry_criteria": ["quality-search execute completed"],
                "exit_criteria": ["quality-search-verdict.json is produced"],
                "depends_on": [],
                "worker_ids": ["figure-agent"],
                "outputs": ["quality-search-verdict.json"],
            },
            {
                "id": "phase-2",
                "name": "Verify quality-search evidence",
                "entry_criteria": ["quality-search-verdict.json is available"],
                "exit_criteria": ["contract_status is pass"],
                "depends_on": ["phase-1"],
                "worker_ids": ["depone"],
                "outputs": ["depone verification report"],
            },
        ],
        "workers": [],
        "handoffs": [
            {
                "from_phase": "phase-1",
                "to_phase": "phase-2",
                "artifact": "quality-search-verdict.json",
                "expected_hash": verdict_hash,
                "artifact_schema": {
                    "format": "json",
                    "required_fields": ["contract_status", "failures", "checks"],
                    "validation_command": "python -m json.tool quality-search-verdict.json",
                },
            }
        ],
        "parallelism": {
            "shape": "none",
            "concurrency_cap": 1,
            "barriers": [],
            "fan_in_rule": "single evidence verdict",
        },
        "verification": [
            {
                "claim_or_output": "quality-search contract_status is pass",
                "ground_truth": "quality-search-verdict.json",
                "evaluator": "ground-truth-contains",
                "expected": '"contract_status": "pass"',
                "required": True,
            },
            {
                "claim_or_output": "quality-search source mutation was not performed",
                "ground_truth": "quality-search-verdict.json",
                "evaluator": "ground-truth-contains",
                "expected": '"source_mutation": "not_performed"',
                "required": True,
            },
        ],
        "risk_gates": [],
        "budget": {"max_agents": 2, "max_rounds": 1, "max_retries": 0},
        "resume": {"cacheable_outputs": ["quality-search-verdict.json"], "invalidators": []},
        "execution_path": {
            "mode": "evidence",
            "first_slice": {
                "instruction": "Inspect quality-search evidence verdict.",
                "inputs": ["quality-search-verdict.json"],
                "expected_output": "Depone verification report",
                "completion_check": "Depone verdict is verified.",
                "forbidden_actions": ["source_mutation", "release_mutation"],
            },
            "consumer": "depone",
        },
    }


def _depone_evidence_pack(
    *,
    name: str,
    run_id: str,
    manifest: dict[str, Any],
    plan: dict[str, Any],
    policy: dict[str, Any],
    source_context: dict[str, Any],
    candidate_set: dict[str, Any],
    render_results: dict[str, Any],
    visual_evidence: dict[str, Any],
    candidate_rankings: list[dict[str, Any]],
    decision: dict[str, Any],
    selected_semantic_precheck: dict[str, Any] | None = None,
    selected_review_packet: dict[str, Any] | None = None,
    selected_acceptance_recommendation: dict[str, Any] | None = None,
    recommendation_experience: dict[str, Any] | None = None,
    selected_attempt: dict[str, Any] | None = None,
    convergence_decision: dict[str, Any] | None = None,
    paths: runtime_paths.RuntimePaths,
) -> dict[str, dict[str, Any] | str]:
    verdict = _quality_search_contract_verdict(
        name=name,
        run_id=run_id,
        manifest=manifest,
        plan=plan,
        policy=policy,
        source_context=source_context,
        candidate_set=candidate_set,
        render_results=render_results,
        visual_evidence=visual_evidence,
        candidate_rankings=candidate_rankings,
        decision=decision,
        selected_semantic_precheck=selected_semantic_precheck,
        selected_review_packet=selected_review_packet,
        selected_acceptance_recommendation=selected_acceptance_recommendation,
        recommendation_experience=recommendation_experience,
        selected_attempt=selected_attempt,
        convergence_decision=convergence_decision,
        paths=paths,
    )
    verdict_hash = _sha256_bytes(_json_bytes(verdict))
    plan = _depone_plan_for_quality_search(
        name=name,
        run_id=run_id,
        verdict_hash=verdict_hash,
    )
    evidence_contract = {
        "schema_version": DEPONE_EVIDENCE_CONTRACT_SCHEMA,
        "required_evidence": [
            "run-metadata.json",
            "quality-search-verdict.json",
            "quality-search-summary.md",
        ],
        "expected_exit_code": 0,
    }
    metadata = {
        "run_id": run_id,
        "fixture": name,
        "exit_code": 0,
        "num_rounds": manifest.get("executed_iterations", 1),
    }
    summary = (
        "# Quality Search Depone Evidence\n\n"
        f"- fixture: {name}\n"
        f"- run_id: {run_id}\n"
        f"- contract_status: {verdict['contract_status']}\n"
        f"- candidate_count: {verdict['checks']['candidate_count']}\n"
        f"- selected_family: {verdict['checks']['selected_family']}\n"
        f"- selected_semantic_precheck_status: "
        f"{verdict['checks']['selected_semantic_precheck_status']}\n"
        f"- selected_apply_readiness_status: "
        f"{verdict['checks']['selected_apply_readiness_status']}\n"
        f"- selected_acceptance_recommendation_status: "
        f"{verdict['checks']['selected_acceptance_recommendation_status']}\n"
        f"- selected_recommendation_experience_log_status: "
        f"{verdict['checks']['selected_recommendation_experience_log_status']}\n"
        f"- selected_convergence_decision: "
        f"{verdict['checks']['selected_convergence_decision']}\n"
        "- source_mutation: not_performed\n"
        "- release_mutation: forbidden\n"
    )
    return {
        "depone_plan": plan,
        "evidence-contract.json": evidence_contract,
        "run-metadata.json": metadata,
        "exit-code.txt": "0\n",
        "quality-search-verdict.json": verdict,
        "quality-search-summary.md": summary,
    }


def _candidate_specs_from_plan(
    plan: dict[str, Any],
    *,
    source_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    source_context = source_context or {
        "source_state": "not_loaded",
        "selectors_by_panel": {},
    }
    for index, hypothesis in enumerate(plan.get("patch_hypotheses", []), start=1):
        if not isinstance(hypothesis, dict):
            continue
        family = str(hypothesis.get("family") or "unknown")
        registry = _family_registry_entry(family)
        target_panels = _target_panels_from_hint(hypothesis)
        source_selectors = _source_selectors_for_panels(source_context, target_panels)
        operation_scale = _preferred_operation_scale(family)
        template_id = _preferred_template_id_for_plan(family, plan)
        specs.append(
            {
                "id": f"QS{index:03d}",
                "fixture": plan.get("fixture"),
                "family": family,
                "registry_schema": FAMILY_REGISTRY_SCHEMA,
                "builder": registry["builder"],
                "source": hypothesis.get("source"),
                "target_scope": hypothesis.get("target_scope"),
                "target_hint": hypothesis.get("target_hint", {}),
                "target_panels": target_panels,
                "source_selectors": source_selectors,
                "protected_labels": registry["protected_labels"],
                "design_moves": registry["design_moves"],
                "render_targets": registry["render_targets"],
                "apply_authority": registry["apply_authority"],
                "operation_scale": operation_scale,
                "template_id": template_id,
                "operations": [],
                "operation_state": "not_generated",
                "operation_block_reason": (
                    "family registry slice emits review-only specs, not source mutations"
                ),
                "mutation_allowed": False,
                "mutation_block_reason": "quality-search execute v0 is dry witness mode",
                "expected_detector_movement": hypothesis.get("expected_detector_movement"),
                "expected_visual_movement": hypothesis.get("expected_visual_movement"),
                "rollback_condition": hypothesis.get("rollback_condition"),
                "witness": {
                    "state": "spec_only",
                    "evidence_inputs": ["quality_search_plan", "driver", "quality_defect_ledger"],
                    "source_binding_state": _selector_binding_state(source_selectors),
                },
            }
        )
    specs.append(
        {
            "id": "QSNULL",
            "fixture": plan.get("fixture"),
            "family": "null_baseline",
            "registry_schema": FAMILY_REGISTRY_SCHEMA,
            "builder": "baseline",
            "source": "current_source",
            "target_scope": "fixture",
            "target_hint": {"reason": "baseline comparison for candidate batch"},
            "target_panels": [],
            "source_selectors": [],
            "protected_labels": [],
            "design_moves": [],
            "render_targets": ["full"],
            "apply_authority": "review_only",
            "operation_scale": "baseline",
            "template_id": "null_baseline_v1",
            "operations": [],
            "operation_state": "not_applicable",
            "mutation_allowed": False,
            "mutation_block_reason": "null baseline never mutates source",
            "expected_detector_movement": "none",
            "expected_visual_movement": "none",
            "rollback_condition": "not applicable",
            "witness": {
                "state": "baseline",
                "evidence_inputs": ["current_plan_state"],
            },
        }
    )
    return specs


def _family_evidence_weight(family: str, plan: dict[str, Any]) -> float:
    next_operation = plan.get("next_recommended_operation")
    operation_kind = (
        next_operation.get("kind") if isinstance(next_operation, dict) else "unknown"
    )
    if family == "null_baseline":
        return 0.0
    if operation_kind == "step_out_experiment":
        weights = {
            "hierarchy_rebalance": 0.82,
            "panel_c_hero_finish": 0.88,
            "apparatus_strengthen": 0.78,
            "panel_f_final_finish": 0.86,
            "panel_f_label_route_finish": 0.9,
            "panel_f_density_relief": 0.89,
            "panel_f_qtr_label_lane": 0.9,
            "panel_f_qtr_apparatus_lane": 0.92,
            "panel_f_force_gap_lane": 0.91,
            "panel_f_mechanical_anchor_lane": 0.9,
            "panel_f_leader_left_lane": 0.9,
            "panel_f_electrode_lead_lane": 0.9,
            "panel_f_auto_composite_lane": 0.93,
            "panel_f_boundary_polish": 0.84,
            "density_reduce": 0.72,
            "layout_macro_shift": 0.68,
        }
        return weights.get(family, 0.60)
    if operation_kind == "render_candidate_batch":
        return 0.64
    return 0.30


def _family_memory(plan: dict[str, Any], family: str) -> dict[str, Any]:
    state = plan.get("state")
    memory = state.get("memory") if isinstance(state, dict) else None
    families = memory.get("families") if isinstance(memory, dict) else None
    entry = families.get(family) if isinstance(families, dict) else None
    return entry if isinstance(entry, dict) else {}


def _family_template_memory(
    plan: dict[str, Any],
    family: str,
    template_id: str | None,
) -> dict[str, Any] | None:
    if not template_id:
        return None
    state = plan.get("state")
    memory = state.get("memory") if isinstance(state, dict) else None
    family_templates = (
        memory.get("family_templates") if isinstance(memory, dict) else None
    )
    if not isinstance(family_templates, dict):
        return None
    entry = family_templates.get(f"{family}::{template_id}")
    return entry if isinstance(entry, dict) else {}


def _bounded_float(
    value: Any,
    *,
    default: float = 0.0,
    lower: float = -1.0,
    upper: float = 1.0,
) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, lower), upper)


def _bounded_int(value: Any, *, default: int = 0, lower: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, lower)


def _memory_prior(plan: dict[str, Any], family: str) -> float:
    if family == "null_baseline":
        return 0.0
    entry = _family_memory(plan, family)
    return round(
        _bounded_float(
            entry.get("recommended_prior"),
            default=0.0,
            lower=-0.25,
            upper=0.25,
        ),
        4,
    )


def _ranking_evidence(ranking: dict[str, Any] | None, polarity: str) -> list[str]:
    if not isinstance(ranking, dict):
        return []
    evidence = ranking.get("evidence")
    values = evidence.get(polarity) if isinstance(evidence, dict) else None
    if not isinstance(values, list):
        return []
    return [str(item) for item in values]


def _render_policy_adjustment(ranking: dict[str, Any] | None) -> tuple[float, float]:
    if not isinstance(ranking, dict):
        return (0.0, 0.0)
    rank_score = ranking.get("rank_score")
    if rank_score is None:
        return (0.0, 0.0)
    adjustment = (_bounded_float(rank_score, default=0.5) - 0.5) * 0.16
    negative = set(_ranking_evidence(ranking, "negative"))
    render_status = str(ranking.get("render_status") or "")
    penalty = 0.0
    if "rendered_no_pixel_change" in negative:
        penalty -= 0.08
    elif render_status and render_status not in {
        "not_rendered",
        "rendered_needs_human_review",
    }:
        penalty -= 0.04
    return (round(adjustment, 4), round(penalty, 4))


def _operation_scale_policy_bonus(
    operation_scale: str,
    ranking: dict[str, Any] | None,
) -> float:
    if operation_scale != "panel_block" or not isinstance(ranking, dict):
        return 0.0
    rank_score = _bounded_float(ranking.get("rank_score"), default=0.0, lower=0.0, upper=1.0)
    if rank_score >= 0.75:
        return 0.06
    if rank_score >= 0.65:
        return 0.03
    return 0.0


def _goal_directive_policy_bonus(
    *,
    family: str,
    operation_scale: str,
    plan: dict[str, Any],
) -> float:
    if (
        family == "apparatus_strengthen"
        and operation_scale == "panel_block"
        and _goal_requests_panel_f_apparatus(str(plan.get("goal") or ""))
    ):
        return 0.05
    return 0.0


def _bandit_selected_arm_bonus(family: str, bandit_decision: dict[str, Any]) -> float:
    if family != bandit_decision.get("selected_family"):
        return 0.0
    arms = bandit_decision.get("arm_statistics")
    if not isinstance(arms, dict):
        return 0.0
    has_attempted_arm = any(
        _bounded_int(row.get("attempts"), default=0) > 0
        for row in arms.values()
        if isinstance(row, dict)
    )
    if not has_attempted_arm:
        return 0.0
    return BANDIT_SELECTED_ARM_BONUS


def _duplicate_experience_penalty(
    plan: dict[str, Any],
    family: str,
    template_id: str | None = None,
) -> float:
    memory = (plan.get("state") or {}).get("memory")
    if not isinstance(memory, dict):
        return 0.0
    duplicate_rate = _bounded_float(
        memory.get("duplicate_experience_attempt_rate"),
        default=0.0,
        lower=0.0,
        upper=1.0,
    )
    if duplicate_rate < 0.5:
        return 0.0
    template_memory = _family_template_memory(plan, family, template_id)
    if template_memory is not None:
        if _bounded_int(template_memory.get("attempts"), default=0) <= 0:
            return 0.0
        return -0.05
    family_memory = _family_memory(plan, family)
    if _bounded_int(family_memory.get("attempts"), default=0) <= 0:
        return 0.0
    return -0.05


def _stale_duplicate_experience_family(
    plan: dict[str, Any],
    family: str,
    template_id: str | None = None,
) -> bool:
    return _duplicate_experience_penalty(plan, family, template_id) < 0


def _candidate_policy_score(
    *,
    family: str,
    template_id: str | None,
    operation_scale: str,
    base_evidence_score: float,
    plan: dict[str, Any],
    ranking: dict[str, Any] | None,
    bandit_decision: dict[str, Any],
) -> dict[str, Any]:
    prior = _memory_prior(plan, family)
    render_adjustment, render_penalty = _render_policy_adjustment(ranking)
    operation_scale_bonus = _operation_scale_policy_bonus(operation_scale, ranking)
    goal_directive_bonus = _goal_directive_policy_bonus(
        family=family,
        operation_scale=operation_scale,
        plan=plan,
    )
    bandit_bonus = _bandit_selected_arm_bonus(family, bandit_decision)
    duplicate_penalty = _duplicate_experience_penalty(plan, family, template_id)
    score = round(
        min(
            max(
                base_evidence_score
                + prior
                + bandit_bonus
                + render_adjustment
                + render_penalty
                + operation_scale_bonus
                + goal_directive_bonus
                + duplicate_penalty,
                0.0,
            ),
            1.0,
        ),
        4,
    )
    return {
        "schema": SEARCH_POLICY_SCHEMA,
        "kind": BANDIT_POLICY_KIND,
        "base_evidence_score": base_evidence_score,
        "memory_prior": prior,
        "bandit_bonus": bandit_bonus,
        "bandit_decision": bandit_decision,
        "render_adjustment": render_adjustment,
        "render_penalty": render_penalty,
        "operation_scale_bonus": operation_scale_bonus,
        "goal_directive_bonus": goal_directive_bonus,
        "duplicate_experience_penalty": duplicate_penalty,
        "duplicate_experience_scope": (
            "family_template" if _family_template_memory(plan, family, template_id) is not None
            else "family"
        ),
        "score": score,
    }


def _candidate_scores(
    candidate_specs: list[dict[str, Any]],
    plan: dict[str, Any],
    candidate_rankings: list[dict[str, Any]] | None = None,
    visual_evidence: dict[str, Any] | None = None,
    materialized_candidate_ids: set[str] | None = None,
    candidate_metadata_by_id: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    classifications = plan.get("classifications")
    release_blocker_only = any(
        isinstance(item, dict)
        and item.get("kind") == "release_blocker"
        and item.get("blocks_search") is False
        for item in classifications or []
    )
    rankings_by_id = {
        str(score.get("candidate_id")): score
        for score in candidate_rankings or []
        if isinstance(score, dict)
    }
    full_ratios_by_id, panel_ratios_by_id = _visual_change_ratios_by_candidate(
        visual_evidence
    )
    bandit_decision = _epsilon_greedy_bandit_decision(
        plan,
        [spec.get("family") for spec in candidate_specs if isinstance(spec, dict)],
    )
    scores: list[dict[str, Any]] = []
    for spec in candidate_specs:
        candidate_id = str(spec.get("id"))
        if (
            materialized_candidate_ids is not None
            and candidate_id != "QSNULL"
            and candidate_id not in materialized_candidate_ids
        ):
            continue
        metadata = (
            candidate_metadata_by_id.get(candidate_id)
            if isinstance(candidate_metadata_by_id, dict)
            else None
        )
        metadata = metadata if isinstance(metadata, dict) else {}
        family = str(spec.get("family") or "unknown")
        score = _family_evidence_weight(family, plan)
        if release_blocker_only and family != "null_baseline":
            score += 0.03
        score = round(min(score, 1.0), 4)
        ranking = rankings_by_id.get(candidate_id)
        operation_scale = str(
            metadata.get("operation_scale") or spec.get("operation_scale") or "unknown"
        )
        template_id = str(metadata.get("template_id") or spec.get("template_id") or "")
        policy = _candidate_policy_score(
            family=family,
            template_id=template_id,
            operation_scale=operation_scale,
            base_evidence_score=score,
            plan=plan,
            ranking=ranking,
            bandit_decision=bandit_decision,
        )
        render_status = (
            str(ranking.get("render_status"))
            if isinstance(ranking, dict)
            else "not_rendered"
        )
        full_changed_pixel_ratio = full_ratios_by_id.get(candidate_id)
        if full_changed_pixel_ratio is None:
            full_changed_pixel_ratio = _ranking_changed_pixel_ratio(ranking)
        panel_changed_pixel_ratio = panel_ratios_by_id.get(candidate_id)
        non_marginal_visual_change = _non_marginal_visual_change(
            full_changed_pixel_ratio=full_changed_pixel_ratio,
            panel_changed_pixel_ratio=panel_changed_pixel_ratio,
        )
        scores.append(
            {
                "candidate_id": spec.get("id"),
                "family": family,
                "candidate_hash": metadata.get("candidate_hash"),
                "operation_scale": operation_scale,
                "template_id": template_id,
                "expected_visual_movement": (
                    metadata.get("expected_visual_movement")
                    or spec.get("expected_visual_movement")
                ),
                "evidence_score": score,
                "policy_score": policy["score"],
                "rank_score": ranking.get("rank_score") if isinstance(ranking, dict) else None,
                "full_changed_pixel_ratio": full_changed_pixel_ratio,
                "panel_changed_pixel_ratio": panel_changed_pixel_ratio,
                "non_marginal_visual_change": non_marginal_visual_change,
                "stale_duplicate_experience_family": (
                    _stale_duplicate_experience_family(plan, family, template_id)
                ),
                "non_marginal_thresholds": {
                    "full_changed_pixel_ratio": NON_MARGINAL_FULL_CHANGED_PIXEL_RATIO,
                    "panel_changed_pixel_ratio": NON_MARGINAL_PANEL_CHANGED_PIXEL_RATIO,
                },
                "policy": policy,
                "witness": {
                    "state": "dry_scored",
                    "basis": [
                        "plan_next_operation",
                        "classification_blocks_search",
                        "candidate_family_priority",
                        "candidate_sandbox_manifest",
                        "quality_memory_prior",
                        "candidate_render_policy_adjustment",
                        "non_marginal_visual_change_gate",
                        "stale_duplicate_experience_family_gate",
                    ],
                },
                "render_status": render_status,
                "apply_authority": "review_only",
                "effective_apply_authority": (
                    ranking.get("effective_apply_authority")
                    if isinstance(ranking, dict)
                    else "review_only"
                ),
            }
        )
    return scores


def _materialized_candidate_ids(candidate_set: dict[str, Any]) -> set[str]:
    return {
        str(candidate.get("id"))
        for candidate in candidate_set.get("candidates", [])
        if isinstance(candidate, dict) and candidate.get("id")
    }


def _candidate_metadata_by_id(candidate_set: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for candidate in candidate_set.get("candidates", []):
        if not isinstance(candidate, dict) or not candidate.get("id"):
            continue
        metadata[str(candidate["id"])] = {
            "candidate_hash": candidate.get("candidate_hash"),
            "operation_scale": candidate.get("operation_scale"),
            "template_id": candidate.get("template_id"),
            "expected_visual_movement": candidate.get("expected_visual_movement"),
        }
    return metadata


def _execution_decision(
    plan: dict[str, Any],
    candidate_scores: list[dict[str, Any]],
    *,
    fixture_name: str = "<fixture>",
) -> dict[str, Any]:
    diagnostic_search_bypass = any(
        isinstance(item, dict)
        and item.get("diagnostic_bypass") == "stale_critique_search"
        and item.get("blocks_search") is False
        for item in plan.get("classifications", [])
    )
    blocking = [
        item
        for item in plan.get("classifications", [])
        if isinstance(item, dict) and item.get("blocks_search") is True
    ]
    if blocking:
        return {
            "kind": "prerequisite_required",
            "reason": "progress blocker prevents candidate search",
            "blocking_classifications": blocking,
            "selected_candidate_id": None,
            "source_mutation": "not_performed",
            "diagnostic_search_bypass": diagnostic_search_bypass,
            "evidence_score": 0.0,
            "policy_score": 0.0,
        }
    ranked = sorted(
        candidate_scores,
        key=lambda item: (
            float(item.get("policy_score") or item.get("evidence_score") or 0.0),
            float(item.get("evidence_score") or 0.0),
        ),
        reverse=True,
    )
    eligible = [
        item
        for item in ranked
        if item.get("family") != "null_baseline"
        and item.get("non_marginal_visual_change") is True
        and item.get("stale_duplicate_experience_family") is not True
    ]
    selected = (
        eligible[0]
        if eligible
        and float(eligible[0].get("policy_score") or eligible[0].get("evidence_score") or 0.0)
        > 0
        else None
    )
    if selected is None:
        top = ranked[0] if ranked else {}
        stale_non_marginal = [
            item
            for item in ranked
            if item.get("family") != "null_baseline"
            and item.get("non_marginal_visual_change") is True
            and item.get("stale_duplicate_experience_family") is True
        ]
        reason = (
            "non-marginal candidates were excluded as stale duplicate "
            "experience families; generator must produce a fresh non-marginal "
            "candidate"
            if stale_non_marginal
            else (
                "rendered candidates did not clear the non-marginal visual "
                "movement threshold"
            )
        )
        return {
            "kind": "no_non_marginal_candidate",
            "reason": reason,
            "selected_candidate_id": None,
            "evidence_score": 0.0,
            "policy_score": 0.0,
            "source_mutation": "not_performed",
            "diagnostic_search_bypass": diagnostic_search_bypass,
            "stale_duplicate_non_marginal_candidate_count": len(stale_non_marginal),
            "top_candidate_id": top.get("candidate_id"),
            "top_candidate_family": top.get("family"),
            "top_candidate_operation_scale": top.get("operation_scale"),
            "top_candidate_policy_score": top.get("policy_score"),
            "top_candidate_full_changed_pixel_ratio": top.get(
                "full_changed_pixel_ratio"
            ),
            "top_candidate_panel_changed_pixel_ratio": top.get(
                "panel_changed_pixel_ratio"
            ),
            "non_marginal_thresholds": {
                "full_changed_pixel_ratio": NON_MARGINAL_FULL_CHANGED_PIXEL_RATIO,
                "panel_changed_pixel_ratio": NON_MARGINAL_PANEL_CHANGED_PIXEL_RATIO,
            },
        }
    return {
        "kind": "candidate_batch_ready",
        "candidate_state": NON_MARGINAL_REVIEW_CANDIDATE_STATE,
        "reason": (
            "dry executor selected a rendered non-marginal review-only candidate"
        ),
        "selected_candidate_id": selected.get("candidate_id"),
        "selected_family": selected.get("family"),
        "selected_operation_scale": selected.get("operation_scale"),
        "selected_template_id": selected.get("template_id"),
        "evidence_score": selected.get("evidence_score"),
        "policy_score": selected.get("policy_score"),
        "policy": selected.get("policy"),
        "full_changed_pixel_ratio": selected.get("full_changed_pixel_ratio"),
        "panel_changed_pixel_ratio": selected.get("panel_changed_pixel_ratio"),
        "non_marginal_visual_change": True,
        "non_marginal_thresholds": {
            "full_changed_pixel_ratio": NON_MARGINAL_FULL_CHANGED_PIXEL_RATIO,
            "panel_changed_pixel_ratio": NON_MARGINAL_PANEL_CHANGED_PIXEL_RATIO,
        },
        "automation_boundary": "review_only_candidate_ready",
        "review_command": (
            "fig-agent review-candidate "
            f"{fixture_name} {selected.get('candidate_id')}"
        ),
        "source_mutation": "not_performed",
        "diagnostic_search_bypass": diagnostic_search_bypass,
        "next_action": NON_MARGINAL_REVIEW_NEXT_ACTION,
    }


def _selected_review_packet(
    name: str,
    decision: dict[str, Any],
    *,
    paths: runtime_paths.RuntimePaths,
) -> dict[str, Any] | None:
    candidate_id = decision.get("selected_candidate_id")
    if (
        decision.get("candidate_state") != NON_MARGINAL_REVIEW_CANDIDATE_STATE
        or not isinstance(candidate_id, str)
        or not candidate_id.strip()
    ):
        return None
    try:
        packet = candidate_review_packet.build_review_packet(
            name,
            candidate_id,
            plugin_root=paths.plugin_root,
            workspace_root=paths.workspace_root,
        )
    except (ValueError, candidate_review_packet.CandidateReviewPacketError) as exc:
        return {
            "schema": "figure-agent.selected-candidate-review-packet.v0",
            "status": "error",
            "candidate_id": candidate_id,
            "error": str(exc),
        }
    packet["status"] = "ready"
    return packet


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _semantic_label_present(text: str, label: str) -> bool:
    lowered = text.lower()
    normalized_label = label.lower()
    aliases = {
        "q_tr": ("q_tr", "q_{tr}", "q_{\\mathrm{tr}}"),
        "$v_{\\mathrm{active}}$": (
            "$v_{\\mathrm{active}}$",
            "v_{\\mathrm{active}}",
        ),
    }
    for alias in aliases.get(normalized_label, (normalized_label,)):
        if alias in lowered:
            return True
    return False


def _render_manifest_success(render_manifest: dict[str, Any]) -> bool:
    stages = (
        render_manifest.get("stages")
        if isinstance(render_manifest.get("stages"), dict)
        else {}
    )
    expected = {
        "compile": "success",
        "export": "success",
        "crop": "success",
        "evaluate": "rendered_needs_human_review",
    }
    for stage, expected_status in expected.items():
        value = stages.get(stage)
        status = value.get("status") if isinstance(value, dict) else None
        if status != expected_status:
            return False
    return True


def _selected_candidate(candidate_set: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
    candidates = candidate_set.get("candidates")
    if not isinstance(candidates, list):
        return None
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("id") == candidate_id:
            return candidate
    return None


def _write_selected_semantic_precheck(
    name: str,
    decision: dict[str, Any],
    candidate_set: dict[str, Any],
    *,
    paths: runtime_paths.RuntimePaths,
) -> dict[str, Any] | None:
    candidate_id = decision.get("selected_candidate_id")
    if (
        decision.get("candidate_state") != NON_MARGINAL_REVIEW_CANDIDATE_STATE
        or not isinstance(candidate_id, str)
        or not candidate_id.strip()
    ):
        return None
    candidate = _selected_candidate(candidate_set, candidate_id)
    if candidate is None:
        return {
            "schema": "figure-agent.selected-semantic-precheck.v0",
            "status": "blocked",
            "candidate_id": candidate_id,
            "blocking_reasons": ["candidate_set_missing_candidate"],
        }
    if candidate.get("apply_authority") != "review_only":
        return {
            "schema": "figure-agent.selected-semantic-precheck.v0",
            "status": "blocked",
            "candidate_id": candidate_id,
            "blocking_reasons": ["apply_authority_not_review_only"],
        }
    protected_labels = [
        str(label)
        for label in candidate.get("protected_labels", [])
        if isinstance(label, str) and label.strip()
    ]
    if not protected_labels:
        return {
            "schema": "figure-agent.selected-semantic-precheck.v0",
            "status": "blocked",
            "candidate_id": candidate_id,
            "blocking_reasons": ["protected_labels_missing"],
        }
    example_dir = paths.examples_dir / name
    sandbox = example_dir / "build" / "candidates" / candidate_id
    manifest_path = sandbox / "candidate_manifest.json"
    render_manifest_path = sandbox / "render_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        render_manifest = json.loads(render_manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {
            "schema": "figure-agent.selected-semantic-precheck.v0",
            "status": "blocked",
            "candidate_id": candidate_id,
            "blocking_reasons": ["manifest_unreadable"],
        }
    if not isinstance(manifest, dict) or not isinstance(render_manifest, dict):
        return {
            "schema": "figure-agent.selected-semantic-precheck.v0",
            "status": "blocked",
            "candidate_id": candidate_id,
            "blocking_reasons": ["manifest_invalid"],
        }
    if not _render_manifest_success(render_manifest):
        return {
            "schema": "figure-agent.selected-semantic-precheck.v0",
            "status": "blocked",
            "candidate_id": candidate_id,
            "blocking_reasons": ["render_gates_not_passed"],
        }
    operation_text = "\n".join(
        str(operation.get("replacement") or "")
        for operation in manifest.get("operations", [])
        if isinstance(operation, dict)
    )
    missing_labels = [
        label for label in protected_labels if not _semantic_label_present(operation_text, label)
    ]
    if missing_labels:
        return {
            "schema": "figure-agent.selected-semantic-precheck.v0",
            "status": "blocked",
            "candidate_id": candidate_id,
            "blocking_reasons": ["protected_label_missing"],
            "missing_labels": missing_labels,
        }
    review = {
        "schema": semantic_candidate_review.SCHEMA,
        "fixture": name,
        "candidate_id": candidate_id,
        "candidate_hash": manifest.get("candidate_hash"),
        "reviewed_artifacts": [
            {
                "path": render_manifest_path.relative_to(example_dir).as_posix(),
                "sha256": _file_sha256(render_manifest_path),
            }
        ],
        "semantic_invariants": [
            {"kind": "protected_label_present", "label": label}
            for label in protected_labels
        ],
        "findings": [
            {
                "kind": "deterministic_semantic_precheck",
                "status": "pass",
                "basis": [
                    "render_manifest_gates_passed",
                    "protected_labels_present_in_replacement",
                    "review_only_source_mutation_boundary",
                ],
            }
        ],
        "conflicts": [],
        "verdict": "pass",
        "human_required": False,
        "reviewed_at": _utc_stamp(),
        "reviewer": "fig-agent-auto-semantic-precheck",
    }
    review_path = sandbox / "semantic_review.json"
    _write_json(review_path, review)
    return {
        "schema": "figure-agent.selected-semantic-precheck.v0",
        "status": "pass",
        "candidate_id": candidate_id,
        "review_path": _workspace_relative(paths, review_path),
        "protected_labels": protected_labels,
        "reviewed_artifacts": review["reviewed_artifacts"],
    }


def _selected_acceptance_recommendation(
    decision: dict[str, Any],
    selected_semantic_precheck: dict[str, Any] | None,
    selected_review_packet: dict[str, Any] | None,
    convergence_decision: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    candidate_id = decision.get("selected_candidate_id")
    if (
        decision.get("candidate_state") != NON_MARGINAL_REVIEW_CANDIDATE_STATE
        or not isinstance(candidate_id, str)
        or not candidate_id.strip()
    ):
        return None
    apply_readiness = (
        selected_review_packet.get("apply_readiness")
        if isinstance(selected_review_packet, dict)
        and isinstance(selected_review_packet.get("apply_readiness"), dict)
        else {}
    )
    precheck_status = (
        selected_semantic_precheck.get("status")
        if isinstance(selected_semantic_precheck, dict)
        else None
    )
    ready = (
        precheck_status == "pass"
        and isinstance(selected_review_packet, dict)
        and selected_review_packet.get("status") == "ready"
        and apply_readiness.get("status") == "ready_for_local_acceptance"
        and decision.get("diagnostic_search_bypass") is not True
        and (
            convergence_decision is None
            or convergence_decision.get("decision") == "accept"
        )
    )
    diagnostic_defer = decision.get("diagnostic_search_bypass") is True
    convergence_defer = (
        isinstance(convergence_decision, dict)
        and convergence_decision.get("decision") != "accept"
    )
    required_commands = (
        apply_readiness.get("required_commands")
        if isinstance(apply_readiness.get("required_commands"), list)
        else []
    )
    return {
        "schema": "figure-agent.selected-acceptance-recommendation.v0",
        "status": "auto_accept_recommended" if ready else "blocked",
        "candidate_id": candidate_id,
        "recommendation": "accept" if ready else "defer",
        "authority": "recommendation_only",
        "is_acceptance_artifact": False,
        "source_mutation": "not_performed",
        "acceptance_gate": "explicit acceptance artifact still required",
        "rationale": (
            "selected candidate is non-marginal, render-complete, semantic-prechecked, "
            "and ready for local acceptance"
            if ready
            else (
                "stale-critique diagnostic search cannot recommend acceptance"
                if diagnostic_defer
                else (
                    "convergence controller did not accept the selected attempt"
                    if convergence_defer
                    else "selected candidate has not cleared all automatic readiness checks"
                )
            )
        ),
        "evidence": {
            "semantic_precheck_status": precheck_status,
            "review_packet_status": (
                selected_review_packet.get("status")
                if isinstance(selected_review_packet, dict)
                else None
            ),
            "apply_readiness_status": apply_readiness.get("status"),
            "full_changed_pixel_ratio": decision.get("full_changed_pixel_ratio"),
            "panel_changed_pixel_ratio": decision.get("panel_changed_pixel_ratio"),
            "protected_labels": (
                selected_semantic_precheck.get("protected_labels")
                if isinstance(selected_semantic_precheck, dict)
                else []
            ),
        },
        "required_commands": required_commands if ready else [],
    }


def _selected_candidate_score(
    scores: list[dict[str, Any]],
    candidate_id: str,
) -> dict[str, Any]:
    for score in scores:
        if isinstance(score, dict) and score.get("candidate_id") == candidate_id:
            return score
    return {}


def _first_existing_relative(
    paths: runtime_paths.RuntimePaths,
    candidates: list[Path],
) -> str | None:
    for path in candidates:
        if path.is_file() and not path.is_symlink():
            return _workspace_relative(paths, path)
    return None


def _candidate_attempt_outputs(
    name: str,
    candidate_id: str,
    *,
    paths: runtime_paths.RuntimePaths,
) -> dict[str, str]:
    example_dir = paths.examples_dir / name
    sandbox = example_dir / "build" / "candidates" / candidate_id
    source_path = sandbox / f"{name}.tex"
    if not source_path.is_file():
        source_path = example_dir / f"{name}.tex"
    outputs: dict[str, str] = {}
    editable = _first_existing_relative(paths, [source_path])
    if editable is not None:
        outputs["editable"] = editable
    for fmt in ("pdf", "svg", "png"):
        direct = [
            sandbox / "render" / f"candidate.{fmt}",
            sandbox / "render" / f"{name}.{fmt}",
            sandbox / f"{name}.{fmt}",
            sandbox / f"candidate.{fmt}",
            sandbox / f"preview.{fmt}",
        ]
        recursive = sorted(path for path in sandbox.rglob(f"*.{fmt}") if path.is_file())
        value = _first_existing_relative(paths, [*direct, *recursive])
        if value is not None:
            outputs[fmt] = value
            if fmt == "png":
                outputs["preview_png"] = value
    return outputs


def _semantic_score_from_precheck(
    selected_semantic_precheck: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(selected_semantic_precheck, dict):
        return {
            "complete": False,
            "missing_elements": ["selected_semantic_precheck_missing"],
            "incorrect_relations": [],
        }
    missing = [
        str(item)
        for item in selected_semantic_precheck.get("missing_labels", [])
        if isinstance(item, str) and item.strip()
    ]
    blockers = [
        str(item)
        for item in selected_semantic_precheck.get("blocking_reasons", [])
        if isinstance(item, str) and item.strip()
    ]
    complete = selected_semantic_precheck.get("status") == "pass" and not missing and not blockers
    return {
        "complete": complete,
        "missing_elements": [*missing, *blockers],
        "incorrect_relations": [],
        "protected_labels": selected_semantic_precheck.get("protected_labels", []),
    }


def _float_score(*values: Any, default: float = 0.0) -> float:
    for value in values:
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return default


def _aesthetic_score_from_quality_evidence(
    decision: dict[str, Any],
    candidate_score: dict[str, Any],
    semantic_score: dict[str, Any],
) -> dict[str, Any]:
    base_score = _float_score(
        candidate_score.get("policy_score"),
        decision.get("policy_score"),
        candidate_score.get("rank_score"),
        candidate_score.get("evidence_score"),
        default=0.0,
    )
    readability = 0.82 if semantic_score.get("complete") is True else 0.2
    density = 0.72 if candidate_score.get("non_marginal_visual_change") is True else 0.5
    hierarchy = _float_score(candidate_score.get("rank_score"), base_score, default=base_score)
    objective = aesthetic_objective.score_aesthetic_evidence(
        {
            "rank_score": base_score,
            "label_readability": readability,
            "hierarchy_score": hierarchy,
            "density_control": density,
            "visual_clash_count": len(semantic_score.get("missing_elements", [])),
        }
    )
    return dict(objective["scores"])


def _selected_figure_attempt(
    *,
    name: str,
    goal: str,
    decision: dict[str, Any],
    source_context: dict[str, Any],
    scores: list[dict[str, Any]],
    selected_semantic_precheck: dict[str, Any] | None,
    paths: runtime_paths.RuntimePaths,
    journal_guide_payload: dict[str, Any],
    run_id: str,
) -> dict[str, Any] | None:
    candidate_id = decision.get("selected_candidate_id")
    if (
        decision.get("candidate_state") != NON_MARGINAL_REVIEW_CANDIDATE_STATE
        or not isinstance(candidate_id, str)
        or not candidate_id.strip()
    ):
        return None
    source_hash = source_context.get("source_hash")
    if not isinstance(source_hash, str) or not source_hash.startswith("sha256:"):
        source_hash = _current_source_hash(paths, name) or ZERO_HASH
    candidate_score = _selected_candidate_score(scores, candidate_id)
    outputs = _candidate_attempt_outputs(name, candidate_id, paths=paths)
    journal_constraints = journal_guide.evaluate_journal_constraints(
        journal_guide_payload,
        outputs=outputs,
    )
    semantic_score = _semantic_score_from_precheck(selected_semantic_precheck)
    attempt = {
        "schema": convergence_models.FIGURE_ATTEMPT_SCHEMA,
        "attempt_id": f"{run_id}:{candidate_id}",
        "parent_attempt_id": None,
        "figure_id": name,
        "candidate_id": candidate_id,
        "user_goal": goal,
        "target_medium": "journal_paper",
        "target_journal": journal_guide_payload.get("target_journal", "unknown"),
        "figure_type": "scientific_technical_figure",
        "spec_hash": source_hash,
        "journal_guide_hash": journal_guide_payload["guide_hash"],
        "render_backend": "quality-search-candidate-render",
        "outputs": outputs,
        "journal_constraints": journal_constraints,
        "semantic_score": semantic_score,
        "aesthetic_score": _aesthetic_score_from_quality_evidence(
            decision,
            candidate_score,
            semantic_score,
        ),
        "issues": [
            *journal_constraints.get("violations", []),
            *[
                {"id": item, "severity": "hard", "source": "selected_semantic_precheck"}
                for item in semantic_score.get("missing_elements", [])
            ],
        ],
        "edit_plan": [],
    }
    return convergence_models.validate_figure_attempt(attempt)


def _manual_convergence_decision(
    *,
    decision: str,
    attempt_id: str,
    reasons: list[str],
    score: float,
) -> dict[str, Any]:
    return convergence_models.validate_convergence_decision(
        {
            "schema": convergence_models.CONVERGENCE_DECISION_SCHEMA,
            "decision": decision,
            "attempt_id": attempt_id,
            "selected_attempt_id": attempt_id,
            "best_previous_attempt_id": None,
            "reasons": reasons,
            "current_aesthetic_score": score,
            "selected_aesthetic_score": score,
        }
    )


def _selected_convergence_decision(
    quality_decision: dict[str, Any],
    selected_attempt: dict[str, Any] | None,
    *,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    if selected_attempt is None:
        return None
    score = _float_score(
        (selected_attempt.get("aesthetic_score") or {}).get("overall")
        if isinstance(selected_attempt.get("aesthetic_score"), dict)
        else None,
        default=0.0,
    )
    if quality_decision.get("diagnostic_search_bypass") is True:
        selected_attempt["decision"] = "human_review"
        convergence_models.validate_figure_attempt(selected_attempt)
        return _manual_convergence_decision(
            decision="human_review",
            attempt_id=str(selected_attempt["attempt_id"]),
            reasons=["diagnostic_search_bypass_requires_human_review"],
            score=score,
        )
    convergence_decision = convergence_controller.decide_attempt(
        selected_attempt,
        history=history or [],
    )
    selected_attempt["decision"] = convergence_decision["decision"]
    convergence_models.validate_figure_attempt(selected_attempt)
    return convergence_decision


def build_quality_search_execution(
    name: str,
    *,
    goal: str,
    max_iterations: int,
    allow_stale_critique_search: bool = False,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    if max_iterations < 1:
        raise ValueError("max_iterations must be >= 1")
    plan = build_quality_search_plan(
        name,
        goal=goal,
        allow_stale_critique_search=allow_stale_critique_search,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    run_id = _run_id(name)
    run_dir = paths.workspace_root / ".scratch" / "quality-search-runs" / run_id
    if run_dir.is_symlink():
        raise ValueError(f"refusing to write quality-search run through symlink: {run_dir}")

    source_context = _panel_region_context(name, paths)
    family_registry = {
        "schema": FAMILY_REGISTRY_SCHEMA,
        "fixture": name,
        "source_context": source_context,
        "families": QUALITY_SEARCH_FAMILY_REGISTRY,
    }
    candidate_specs = _candidate_specs_from_plan(plan, source_context=source_context)
    candidate_set = _candidate_set_from_specs(
        name,
        candidate_specs,
        source_context=source_context,
        paths=paths,
    )
    candidate_set_path = run_dir.relative_to(paths.workspace_root) / "candidate_set_000.json"
    render_results = _render_candidate_batch(
        name,
        candidate_set,
        paths=paths,
        candidate_set_path=candidate_set_path,
    )
    candidate_rankings = _rank_rendered_candidates(name, candidate_set, paths=paths)
    visual_evidence = _quality_search_visual_evidence(
        name,
        render_results,
        run_dir=run_dir,
        paths=paths,
    )
    materialized_ids = _materialized_candidate_ids(candidate_set)
    scores = _candidate_scores(
        candidate_specs,
        plan,
        candidate_rankings,
        visual_evidence,
        materialized_candidate_ids=materialized_ids or None,
        candidate_metadata_by_id=_candidate_metadata_by_id(candidate_set),
    )
    decision = _execution_decision(plan, scores, fixture_name=name)
    _write_json(run_dir / "candidate_set_000.json", candidate_set)
    selected_semantic_precheck = _write_selected_semantic_precheck(
        name,
        decision,
        candidate_set,
        paths=paths,
    )
    selected_review_packet = _selected_review_packet(name, decision, paths=paths)
    selected_attempt = None
    if (
        decision.get("candidate_state") == NON_MARGINAL_REVIEW_CANDIDATE_STATE
        and isinstance(decision.get("selected_candidate_id"), str)
    ):
        journal_guide_payload = journal_guide.build_journal_guide(
            name,
            plugin_root=paths.plugin_root,
            workspace_root=paths.workspace_root,
        )
        selected_attempt = _selected_figure_attempt(
            name=name,
            goal=goal,
            decision=decision,
            source_context=source_context,
            scores=scores,
            selected_semantic_precheck=selected_semantic_precheck,
            paths=paths,
            journal_guide_payload=journal_guide_payload,
            run_id=run_id,
        )
    convergence_history = experience_log.convergence_attempt_history(
        name,
        workspace_root=paths.workspace_root,
        plugin_root=paths.plugin_root,
    )
    convergence_decision = _selected_convergence_decision(
        decision,
        selected_attempt,
        history=convergence_history,
    )
    selected_acceptance_recommendation = _selected_acceptance_recommendation(
        decision,
        selected_semantic_precheck,
        selected_review_packet,
        convergence_decision,
    )
    recommendation_experience = None
    recommendation_ready_for_experience = (
        isinstance(selected_acceptance_recommendation, dict)
        and isinstance(selected_acceptance_recommendation.get("candidate_id"), str)
        and (
            selected_acceptance_recommendation.get("status")
            == "auto_accept_recommended"
            or (
                isinstance(convergence_decision, dict)
                and convergence_decision.get("decision") != "accept"
                and selected_acceptance_recommendation.get("status") == "blocked"
                and selected_acceptance_recommendation.get("recommendation") == "defer"
                and "convergence controller did not accept"
                in str(selected_acceptance_recommendation.get("rationale") or "")
            )
        )
    )
    if recommendation_ready_for_experience:
        selected_candidate_id = selected_acceptance_recommendation["candidate_id"]
        recommendation_experience = experience_log.append_recommendation_record(
            name,
            selected_candidate_id,
            candidate_set=candidate_set,
            candidate_rankings=candidate_rankings,
            decision={**decision, "source_context": source_context},
            recommendation=selected_acceptance_recommendation,
            run_dir=run_dir,
            selected_attempt=selected_attempt,
            convergence_decision=convergence_decision,
            workspace_root=paths.workspace_root,
            plugin_root=paths.plugin_root,
        )
    tool_defects = {
        "schema": "figure-agent.quality-search-tool-defects.v0",
        "fixture": name,
        "tool_defect_candidates": plan.get("tool_defect_candidates", []),
    }
    memory_events = _quality_search_memory_events(
        name=name,
        run_id=run_id,
        candidate_set=candidate_set,
        candidate_rankings=candidate_rankings,
        visual_evidence=visual_evidence,
        paths=paths,
        run_dir=run_dir,
        selected_acceptance_recommendation=selected_acceptance_recommendation,
    )
    policy = {
        "schema": "figure-agent.quality-search-policy.v0",
        "fixture": name,
        "kind": (plan.get("next_recommended_operation") or {}).get("kind"),
        "selection_policy": plan.get("search_policy"),
        "max_iterations": max_iterations,
        "source_mutation": "forbidden",
        "release_mutation": "forbidden",
    }
    manifest = {
        "schema": EXECUTE_SCHEMA,
        "fixture": name,
        "goal": goal,
        "created_at": _utc_stamp(),
        "mode": "execute_dry_witness",
        "status": "dry_run_complete",
        "max_iterations": max_iterations,
        "executed_iterations": 1,
        "artifacts": [
            "state_000.json",
            "classification_000.json",
            "policy_000.json",
            "family_registry_000.json",
            "candidate_set_000.json",
            "render_results_000.json",
            "visual_evidence_000.json",
            "candidate_specs_000.json",
            "candidate_scores_000.json",
            "candidate_rankings_000.json",
            "decision_000.json",
            *(
                ["selected_semantic_precheck_000.json"]
                if selected_semantic_precheck is not None
                else []
            ),
            *(
                ["selected_review_packet_000.json"]
                if selected_review_packet is not None
                else []
            ),
            *(
                ["selected_acceptance_recommendation_000.json"]
                if selected_acceptance_recommendation is not None
                else []
            ),
            *(
                ["selected_attempt_000.json"]
                if selected_attempt is not None
                else []
            ),
            *(
                ["convergence_decision_000.json"]
                if convergence_decision is not None
                else []
            ),
            "tool_defect_candidates_000.json",
            "memory_events_000.json",
            "depone_plan_000.json",
            "depone_evidence_000/evidence-contract.json",
            "depone_evidence_000/run-metadata.json",
            "depone_evidence_000/exit-code.txt",
            "depone_evidence_000/quality-search-verdict.json",
            "depone_evidence_000/quality-search-summary.md",
        ],
    }
    depone_pack = _depone_evidence_pack(
        name=name,
        run_id=run_id,
        manifest=manifest,
        plan=plan,
        policy=policy,
        source_context=source_context,
        candidate_set=candidate_set,
        render_results=render_results,
        visual_evidence=visual_evidence,
        candidate_rankings=candidate_rankings,
        decision=decision,
        selected_semantic_precheck=selected_semantic_precheck,
        selected_review_packet=selected_review_packet,
        selected_acceptance_recommendation=selected_acceptance_recommendation,
        recommendation_experience=recommendation_experience,
        selected_attempt=selected_attempt,
        convergence_decision=convergence_decision,
        paths=paths,
    )
    artifacts = {
        "run_manifest.json": manifest,
        "state_000.json": plan.get("state", {}),
        "classification_000.json": {
            "schema": "figure-agent.quality-search-classification.v0",
            "classifications": plan.get("classifications", []),
        },
        "policy_000.json": policy,
        "family_registry_000.json": family_registry,
        "candidate_set_000.json": candidate_set,
        "render_results_000.json": render_results,
        "visual_evidence_000.json": visual_evidence,
        "candidate_specs_000.json": {
            "schema": "figure-agent.quality-search-candidate-specs.v0",
            "candidates": candidate_specs,
        },
        "candidate_scores_000.json": {
            "schema": "figure-agent.quality-search-candidate-scores.v0",
            "scores": scores,
        },
        "candidate_rankings_000.json": {
            "schema": "figure-agent.quality-search-candidate-rankings.v0",
            "scores": candidate_rankings,
        },
        "decision_000.json": decision,
        **(
            {"selected_semantic_precheck_000.json": selected_semantic_precheck}
            if selected_semantic_precheck is not None
            else {}
        ),
        **(
            {"selected_review_packet_000.json": selected_review_packet}
            if selected_review_packet is not None
            else {}
        ),
        **(
            {
                "selected_acceptance_recommendation_000.json": (
                    selected_acceptance_recommendation
                )
            }
            if selected_acceptance_recommendation is not None
            else {}
        ),
        **(
            {"selected_attempt_000.json": selected_attempt}
            if selected_attempt is not None
            else {}
        ),
        **(
            {"convergence_decision_000.json": convergence_decision}
            if convergence_decision is not None
            else {}
        ),
        "tool_defect_candidates_000.json": tool_defects,
        "memory_events_000.json": memory_events,
        "depone_plan_000.json": depone_pack["depone_plan"],
        "depone_evidence_000/evidence-contract.json": depone_pack[
            "evidence-contract.json"
        ],
        "depone_evidence_000/run-metadata.json": depone_pack["run-metadata.json"],
        "depone_evidence_000/exit-code.txt": depone_pack["exit-code.txt"],
        "depone_evidence_000/quality-search-verdict.json": depone_pack[
            "quality-search-verdict.json"
        ],
        "depone_evidence_000/quality-search-summary.md": depone_pack[
            "quality-search-summary.md"
        ],
    }
    writes: list[str] = []
    for filename, artifact in artifacts.items():
        path = run_dir / filename
        if isinstance(artifact, str):
            _write_text(path, artifact)
        else:
            _write_json(path, artifact)
        writes.append(_workspace_relative(paths, path))

    return {
        "schema": EXECUTE_SCHEMA,
        "fixture": name,
        "goal": goal,
        "status": "dry_run_complete",
        "mode": "execute_dry_witness",
        "run_dir": _workspace_relative(paths, run_dir),
        "max_iterations": max_iterations,
        "executed_iterations": 1,
        "plan": plan,
        "source_context": source_context,
        "candidate_specs": candidate_specs,
        "candidate_set": candidate_set,
        "render_results": render_results,
        "visual_evidence": visual_evidence,
        "candidate_rankings": candidate_rankings,
        "candidate_scores": scores,
        "decision": decision,
        "selected_semantic_precheck": selected_semantic_precheck,
        "selected_review_packet": selected_review_packet,
        "selected_acceptance_recommendation": selected_acceptance_recommendation,
        "selected_attempt": selected_attempt,
        "convergence_decision": convergence_decision,
        "experience_log": recommendation_experience["writes"]
        if isinstance(recommendation_experience, dict)
        else [],
        "recommendation_experience_record_count": len(
            recommendation_experience.get("records", [])
        )
        if isinstance(recommendation_experience, dict)
        and isinstance(recommendation_experience.get("records"), list)
        else 0,
        "recommendation_counterfactual_unchosen_count": sum(
            1
            for record in recommendation_experience.get("records", [])
            if isinstance(record, dict)
            and isinstance(record.get("outcome"), dict)
            and record["outcome"].get("apply_status") == "unchosen"
        )
        if isinstance(recommendation_experience, dict)
        and isinstance(recommendation_experience.get("records"), list)
        else 0,
        "recommendation_experience_record": recommendation_experience.get("record")
        if isinstance(recommendation_experience, dict)
        else None,
        "memory_events": memory_events,
        "depone": {
            "plan": _workspace_relative(paths, run_dir / "depone_plan_000.json"),
            "evidence_dir": _workspace_relative(paths, run_dir / "depone_evidence_000"),
            "verdict": depone_pack["quality-search-verdict.json"],
        },
        "tool_defect_candidates": plan.get("tool_defect_candidates", []),
        "writes": writes,
        "safety": {
            "source_mutation": "forbidden_in_dry_executor",
            "accepted_golden_release_mutation": "forbidden_without_explicit_human_approval",
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
    parser.add_argument(
        "--allow-stale-critique-search",
        action="store_true",
        help=(
            "allow candidate-generation diagnostics when the only progress blocker "
            "is a stale critique; release/acceptance authority remains forbidden"
        ),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    fixture_identity.validate_fixture_name(args.name)
    name = args.name
    if args.execute:
        payload = build_quality_search_execution(
            name,
            goal=args.goal,
            max_iterations=args.max_iterations,
            allow_stale_critique_search=args.allow_stale_critique_search,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    payload = build_quality_search_plan(
        name,
        goal=args.goal,
        allow_stale_critique_search=args.allow_stale_critique_search,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
