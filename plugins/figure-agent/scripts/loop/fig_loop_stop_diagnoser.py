# scripts/loop/fig_loop_stop_diagnoser.py
"""Read-only stop-point diagnoser (Slice 3, measure-only).

Enumerates each figure's sub-regions (re-read quality ledger composite keys plus
the active-target set), assembles a per-sub-region signal bundle by re-invoking
three builders read-only and reading the run's persisted summaries, classifies
each sub-region via the pure classifier, writes a stop-report.v1 into the run
dir, and mirrors only dominant-cause rows into subregion_iteration_log.md when
that log exists. Never mutates run state; never applies a candidate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "candidates"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "quality"))

from audit_evidence_summary import summarize_audit_evidence  # noqa: E402
from candidate_generator import build_candidate_set  # noqa: E402
from fig_loop_records import write_json  # noqa: E402
from quality_defect_ledger import build_quality_defect_ledger  # noqa: E402
from stop_cause_classify import QUALITY_CAUSES, StopCause, classify_stop_cause  # noqa: E402
from subregion_active_set import active_subregion_ids, parse_active_target_rows  # noqa: E402
from subregion_iteration_log import (  # noqa: E402
    SubregionIterationLogError,
    append_iteration_row,
)

SCHEMA = "figure-agent.stop-report.v1"
_HISTOGRAM_KEYS = tuple(cause.value for cause in StopCause)


def _plugin_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _example_dir(name: str, repo_root: Path | None = None) -> Path:
    return (repo_root or _plugin_root()) / "examples" / name


def _read_iteration(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "iteration_001.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _read_manifest(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "run_manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _ledger_defects(
    name: str,
    *,
    repo_root: Path | None = None,
    plugin_root: Path | None = None,
) -> list[dict[str, Any]]:
    ledger = build_quality_defect_ledger(
        name,
        workspace_root=repo_root,
        plugin_root=plugin_root,
    )
    return [defect for defect in ledger.get("defects", []) if isinstance(defect, dict)]


def enumerate_subregions(
    name: str,
    run_dir: Path,
    *,
    repo_root: Path | None = None,
    plugin_root: Path | None = None,
) -> list[str]:
    """Union of ledger composite keys (sel:<hex> / <class>#<n>) and active-target
    set ids. Stable, deterministic, deduplicated, order-preserving."""
    ordered: list[str] = []
    seen: set[str] = set()
    for defect in _ledger_defects(name, repo_root=repo_root, plugin_root=plugin_root):
        target = defect.get("target")
        sub = target.get("subregion") if isinstance(target, dict) else None
        if isinstance(sub, str) and sub and sub not in seen:
            seen.add(sub)
            ordered.append(sub)
    log_path = _example_dir(name, repo_root) / "subregion_iteration_log.md"
    if log_path.is_file():
        rows = parse_active_target_rows(log_path.read_text(encoding="utf-8"))
        for sub in active_subregion_ids(rows):
            if sub and sub not in seen:
                seen.add(sub)
                ordered.append(sub)
    return ordered


def build_signal_bundle(
    name: str,
    run_dir: Path,
    *,
    repo_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    """Re-invoke build_candidate_set / build_quality_defect_ledger /
    summarize_audit_evidence read-only; read stored summaries from the run."""
    iteration = _read_iteration(run_dir)
    manifest = _read_manifest(run_dir)
    return {
        "raw_stop_reason": manifest.get("final_stop_reason") or iteration.get("stop_reason") or "",
        "recommended_next_action": iteration.get("recommended_next_action") or "",
        "status_result": iteration.get("status"),
        "candidate_set": build_candidate_set(
            name,
            workspace_root=repo_root,
            plugin_root=plugin_root,
        ),  # output_path=None => read-only
        "defects": _ledger_defects(name, repo_root=repo_root, plugin_root=plugin_root),
        "audit_evidence_summary": summarize_audit_evidence(_example_dir(name, repo_root)),
        "aesthetic_lever_summary": iteration.get("aesthetic_lever_summary"),
        "basin_summary": iteration.get("basin_summary"),
        "reference_aesthetic_metrics_summary": iteration.get("reference_aesthetic_metrics_summary"),
    }


def _panel_of(subregion_id: str, defects: list[dict[str, Any]]) -> str:
    for defect in defects:
        target = defect.get("target")
        if isinstance(target, dict) and target.get("subregion") == subregion_id:
            return str(target.get("panel") or "unknown")
    return "unknown"


def diagnose_run(
    name: str,
    run_dir: Path,
    *,
    mirror: bool = False,
    repo_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    # mirror defaults to False so the diagnoser stays strictly measure-only: it
    # writes stop_report.json into the (transient) run dir but never mutates a
    # committed fixture log unless a caller explicitly opts in. (The mirror would
    # otherwise append to the real examples/<name>/subregion_iteration_log.md.)
    bundle = build_signal_bundle(
        name,
        run_dir,
        repo_root=repo_root,
        plugin_root=plugin_root,
    )
    manifest = _read_manifest(run_dir)
    subregions = enumerate_subregions(
        name,
        run_dir,
        repo_root=repo_root,
        plugin_root=plugin_root,
    )

    histogram = {key: 0 for key in _HISTOGRAM_KEYS}
    report_subregions: list[dict[str, Any]] = []
    for subregion_id in subregions:
        result = classify_stop_cause(subregion_id, bundle)
        histogram[result.cause.value] += 1
        report_subregions.append(
            {
                "subregion_id": subregion_id,
                "panel": _panel_of(subregion_id, bundle["defects"]),
                "stop_cause": result.cause.value,
                "settled": result.cause is StopCause.settled_verified,
                "evidence": list(result.evidence),
            }
        )

    dominant_cause, dominant_count = _dominant_premature(histogram)
    report = {
        "schema": SCHEMA,
        "fixture": name,
        "run_dir": str(run_dir),
        "commit": manifest.get("commit"),
        "branch": manifest.get("branch"),
        "raw_stop_reason": bundle["raw_stop_reason"],
        "subregions": report_subregions,
        "cause_histogram": histogram,
        "dominant_premature_cause": dominant_cause,
        "dominant_premature_count": dominant_count,
    }
    write_json(run_dir / "stop_report.json", report)
    if mirror and dominant_cause is not None:
        _mirror_dominant_rows(name, report_subregions, dominant_cause, repo_root=repo_root)
    return report


def _dominant_premature(histogram: dict[str, int]) -> tuple[str | None, int]:
    best_cause: str | None = None
    best_count = 0
    for cause in QUALITY_CAUSES:
        count = histogram.get(cause.value, 0)
        if count > best_count:
            best_count = count
            best_cause = cause.value
    return (best_cause, best_count)


def _mirror_dominant_rows(
    name: str,
    subregions: list[dict[str, Any]],
    dominant_cause: str,
    *,
    repo_root: Path | None = None,
) -> None:
    """Mirror only dominant-cause rows; skip when no log exists (flood + raise guard)."""
    log_path = _example_dir(name, repo_root) / "subregion_iteration_log.md"
    if not log_path.is_file():
        return
    for sub in subregions:
        if sub["stop_cause"] != dominant_cause:
            continue
        first = sub["evidence"][0] if sub["evidence"] else {}
        key = first.get("signal_key", "n/a")
        ref = first.get("source_ref", "n/a")
        why = f"{sub['stop_cause']}; {key} ({ref})"
        try:
            append_iteration_row(
                log_path,
                iteration="stop-diagnosis",
                subregion_id=sub["subregion_id"],
                problem="measure-only stop diagnosis",
                patch_summary="none (measure-only)",
                result="diagnosed",
                why=why,
                follow_up="none",
            )
        except SubregionIterationLogError:
            return
