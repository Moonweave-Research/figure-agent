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

import candidate_rank
import candidate_render
import fig_driver
import fixture_identity
import quality_defect_ledger
import quality_memory_index
import runtime_paths

SCHEMA = "figure-agent.quality-search-plan.v0"
EXECUTE_SCHEMA = "figure-agent.quality-search-execute.v0"
ZERO_HASH = "sha256:" + "0" * 64

PROGRESS_ACTIONS = {
    "create_or_fix_source",
    "run_compile",
    "run_critique",
    "run_adjudicate",
    "run_fig_loop",
    "run_export",
}
FAMILY_REGISTRY_SCHEMA = "figure-agent.quality-search-family-registry.v0"
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
    "apparatus_strengthen": {
        "builder": "panel_region_spec",
        "apply_authority": "review_only",
        "protected_labels": [
            "$V_{\\mathrm{active}}$",
            "DC bias",
            "$q_{\\mathrm{tr}}$ trapped charge",
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


def _line_width_replacement(
    *,
    lines: list[str],
    selector: dict[str, Any],
    minimum_pt: float,
) -> tuple[str, str] | None:
    try:
        start = int(selector["line_start"])
        end = int(selector["line_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if start < 1 or end < start or end > len(lines):
        return None
    for line in lines[start - 1 : end]:
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
        return line, replacement_line
    return None


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
        "apparatus_strengthen": "F",
        "density_reduce": "E",
    }.get(family)
    selector = next(
        (item for item in bound_selectors if item.get("panel") == preferred_panel),
        bound_selectors[0],
    )
    minimum_pt = {
        "hierarchy_rebalance": 0.9,
        "apparatus_strengthen": 0.8,
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
    original, new_text = replacement
    operation = {
        "kind": "replace_text",
        "semantic_kind": f"quality_search_{family}",
        "path": source_ref,
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
    lines = source_path.read_text(encoding="utf-8").splitlines()
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
        target_panel = target_panels[0] if target_panels else None
        stable_hash_payload = {
            "candidate_id": candidate_id,
            "family": spec.get("family"),
            "source_hash": source_context.get("source_hash"),
            "operation": operation,
        }
        candidates.append(
            {
                "id": candidate_id,
                "family": spec.get("family"),
                "edit_class": "quality_search_style_token",
                "edit_family": spec.get("family"),
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
                    "changes": "one style token inside a bound panel region",
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
) -> dict[str, Any]:
    if not candidate_set.get("candidates"):
        return {
            "schema": "figure-agent.candidate-render-result.v1",
            "fixture": name,
            "rendered": [],
        }
    return candidate_render.render_candidate_set(
        name,
        candidate_set,
        workspace_root=paths.workspace_root,
        plugin_root=paths.plugin_root,
        compile=False,
        export=False,
        evaluate=False,
    )


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
        scores.append(candidate_rank.score_manifest(manifest, candidate=candidate))
    return sorted(
        scores,
        key=lambda score: (-float(score.get("rank_score") or 0.0), str(score.get("candidate_id"))),
    )


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
            "apparatus_strengthen": 0.78,
            "density_reduce": 0.72,
            "layout_macro_shift": 0.68,
        }
        return weights.get(family, 0.60)
    if operation_kind == "render_candidate_batch":
        return 0.64
    return 0.30


def _candidate_scores(
    candidate_specs: list[dict[str, Any]],
    plan: dict[str, Any],
    candidate_rankings: list[dict[str, Any]] | None = None,
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
    scores: list[dict[str, Any]] = []
    for spec in candidate_specs:
        family = str(spec.get("family") or "unknown")
        score = _family_evidence_weight(family, plan)
        if release_blocker_only and family != "null_baseline":
            score += 0.03
        score = round(min(score, 1.0), 4)
        ranking = rankings_by_id.get(str(spec.get("id")))
        render_status = (
            str(ranking.get("render_status"))
            if isinstance(ranking, dict)
            else "not_rendered"
        )
        scores.append(
            {
                "candidate_id": spec.get("id"),
                "family": family,
                "evidence_score": score,
                "rank_score": ranking.get("rank_score") if isinstance(ranking, dict) else None,
                "witness": {
                    "state": "dry_scored",
                    "basis": [
                        "plan_next_operation",
                        "classification_blocks_search",
                        "candidate_family_priority",
                        "candidate_sandbox_manifest",
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


def _execution_decision(
    plan: dict[str, Any],
    candidate_scores: list[dict[str, Any]],
) -> dict[str, Any]:
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
            "evidence_score": 0.0,
        }
    ranked = sorted(
        candidate_scores,
        key=lambda item: float(item.get("evidence_score") or 0.0),
        reverse=True,
    )
    selected = ranked[0] if ranked and float(ranked[0].get("evidence_score") or 0.0) > 0 else None
    if selected is None:
        return {
            "kind": "no_actionable_candidate",
            "reason": "no non-baseline candidate received supporting evidence",
            "selected_candidate_id": None,
            "evidence_score": 0.0,
        }
    return {
        "kind": "candidate_batch_ready",
        "reason": "dry executor selected the strongest evidence-backed candidate family",
        "selected_candidate_id": selected.get("candidate_id"),
        "selected_family": selected.get("family"),
        "evidence_score": selected.get("evidence_score"),
        "source_mutation": "not_performed",
        "next_action": "render selected candidate batch in sandbox",
    }


def build_quality_search_execution(
    name: str,
    *,
    goal: str,
    max_iterations: int,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    if max_iterations < 1:
        raise ValueError("max_iterations must be >= 1")
    plan = build_quality_search_plan(
        name,
        goal=goal,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    run_dir = paths.workspace_root / ".scratch" / "quality-search-runs" / _run_id(name)
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
    render_results = _render_candidate_batch(name, candidate_set, paths=paths)
    candidate_rankings = _rank_rendered_candidates(name, candidate_set, paths=paths)
    scores = _candidate_scores(candidate_specs, plan, candidate_rankings)
    decision = _execution_decision(plan, scores)
    tool_defects = {
        "schema": "figure-agent.quality-search-tool-defects.v0",
        "fixture": name,
        "tool_defect_candidates": plan.get("tool_defect_candidates", []),
    }
    memory_events = {
        "schema": "figure-agent.quality-search-memory-events.v0",
        "fixture": name,
        "events": [],
        "reason": (
            "dry witness executor records no learned outcome until render/apply "
            "evidence exists"
        ),
    }
    policy = {
        "schema": "figure-agent.quality-search-policy.v0",
        "fixture": name,
        "kind": (plan.get("next_recommended_operation") or {}).get("kind"),
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
            "candidate_specs_000.json",
            "candidate_scores_000.json",
            "candidate_rankings_000.json",
            "decision_000.json",
            "tool_defect_candidates_000.json",
            "memory_events_000.json",
        ],
    }
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
        "tool_defect_candidates_000.json": tool_defects,
        "memory_events_000.json": memory_events,
    }
    writes: list[str] = []
    for filename, artifact in artifacts.items():
        path = run_dir / filename
        _write_json(path, artifact if isinstance(artifact, dict) else {"value": artifact})
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
        "candidate_rankings": candidate_rankings,
        "candidate_scores": scores,
        "decision": decision,
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
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    fixture_identity.validate_fixture_name(args.name)
    name = args.name
    if args.execute:
        payload = build_quality_search_execution(
            name,
            goal=args.goal,
            max_iterations=args.max_iterations,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
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
