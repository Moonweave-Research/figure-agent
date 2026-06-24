"""Read-only basin detection for repeated fig_loop outcomes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASIN_SCHEMA = "figure-agent.loop-basin.v1"
DEFAULT_THRESHOLD = 3
HISTORY_LIMIT = 12


def _signal(label: str, value: str, source: str) -> dict[str, str]:
    return {
        "signal_class": label,
        "signal_value": value,
        "signal_key": f"{label}:{value}",
        "source": source,
    }


def _metric_signals(summary: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(summary, dict) or summary.get("evaluation_state") != "severe_divergence":
        return []
    items = summary.get("blocking_items")
    if isinstance(items, list) and all(isinstance(item, str) for item in items):
        return [
            _signal("reference_aesthetic_metric", item, "reference_aesthetic_metrics_summary")
            for item in items
        ]
    return []


def _aesthetic_lever_signals(summary: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(summary, dict) or summary.get("evaluation_state") != "needs_human":
        return []
    bottleneck = summary.get("next_aesthetic_bottleneck")
    if not isinstance(bottleneck, dict):
        return []
    lever_id = bottleneck.get("lever_id")
    if not isinstance(lever_id, str) or not lever_id:
        return []
    return [_signal("aesthetic_bottleneck", lever_id, "aesthetic_lever_summary")]


def _patch_target_signals(loop_decision: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(loop_decision, dict):
        return []
    target = loop_decision.get("active_patch_target")
    if not isinstance(target, dict):
        return []
    finding_id = target.get("finding_id") or target.get("subregion_id")
    if not isinstance(finding_id, str) or not finding_id:
        return []
    return [_signal("patch_target", finding_id, "active_patch_target")]


def _signals_from_iteration(iteration: dict[str, Any]) -> list[dict[str, str]]:
    return [
        *_patch_target_signals(iteration),
        *_aesthetic_lever_signals(iteration.get("aesthetic_lever_summary")),
        *_metric_signals(iteration.get("reference_aesthetic_metrics_summary")),
    ]


def _current_signals(
    loop_decision: dict[str, Any],
    aesthetic_lever_summary: dict[str, Any] | None,
    reference_aesthetic_metrics_summary: dict[str, Any] | None,
) -> list[dict[str, str]]:
    return [
        *_patch_target_signals(loop_decision),
        *_aesthetic_lever_signals(aesthetic_lever_summary),
        *_metric_signals(reference_aesthetic_metrics_summary),
    ]


def _status_matches_current(
    historical_status: dict[str, Any],
    current_status: dict[str, Any],
) -> bool:
    for key in ("render_state", "critique_state"):
        if historical_status.get(key) != current_status.get(key):
            return False
    return True


def _read_iteration(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def basin_summary(
    *,
    runs_root: Path,
    name: str,
    current_status: dict[str, Any],
    loop_decision: dict[str, Any],
    aesthetic_lever_summary: dict[str, Any] | None,
    reference_aesthetic_metrics_summary: dict[str, Any] | None,
    threshold: int = DEFAULT_THRESHOLD,
) -> dict[str, Any] | None:
    current_signals = _current_signals(
        loop_decision,
        aesthetic_lever_summary,
        reference_aesthetic_metrics_summary,
    )
    if not current_signals:
        return None
    current_by_key = {signal["signal_key"]: signal for signal in current_signals}
    matches: dict[str, list[str]] = {key: [] for key in current_by_key}
    history_paths = sorted(
        runs_root.glob(f"*-{name}/iteration_001.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in history_paths[:HISTORY_LIMIT]:
        iteration = _read_iteration(path)
        if iteration is None:
            continue
        status = iteration.get("status")
        if not isinstance(status, dict) or not _status_matches_current(status, current_status):
            continue
        for signal in _signals_from_iteration(iteration):
            key = signal["signal_key"]
            if key in matches:
                matches[key].append(str(path))

    basin_key: str | None = None
    basin_count = 0
    for key, paths in matches.items():
        count = len(paths) + 1
        if count >= threshold and count > basin_count:
            basin_key = key
            basin_count = count
    if basin_key is None:
        return None

    signal = current_by_key[basin_key]
    evidence_paths = matches[basin_key]
    return {
        "schema": BASIN_SCHEMA,
        "evaluation_state": "basin_detected",
        "threshold": threshold,
        "history_count": basin_count,
        "signal": signal,
        "evidence_paths": evidence_paths,
        "recommended_step_out_actions": [
            "run external second-opinion review on the repeated issue",
            "request human art-direction review before another local patch",
            "revise reference-learning contract if reference style conflicts with intent",
            "revise briefing.md if author intent has shifted",
        ],
        "next_action": (
            "step out of the local polish loop: repeated "
            f"{signal['signal_class']} {signal['signal_value']} appeared "
            f"{basin_count} times"
        ),
    }
