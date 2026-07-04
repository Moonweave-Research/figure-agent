"""Measure loop-level automation metrics from durable logs."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.loop-metrics.v1"
LOOP_RUN_SCHEMA = "figure-agent.fig-loop-run.v1"


class QualityLoopMetricsError(ValueError):
    """Raised when loop metrics inputs are unsafe or malformed."""


def _experience_log_dir(plugin_root: Path) -> Path:
    log_dir = plugin_root / "docs" / "experience-log"
    if log_dir.is_symlink():
        raise QualityLoopMetricsError("experience_log_symlink")
    return log_dir


def _load_experience_records(plugin_root: Path) -> list[dict[str, Any]]:
    log_dir = _experience_log_dir(plugin_root)
    if not log_dir.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(log_dir.glob("*.jsonl")):
        if path.is_symlink():
            raise QualityLoopMetricsError("experience_log_symlink")
        fixture_identity.validate_fixture_name(path.stem)
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise QualityLoopMetricsError(
                    f"experience_record_invalid:{path.name}:{line_number}"
                ) from exc
            if not isinstance(payload, dict):
                raise QualityLoopMetricsError(
                    f"experience_record_invalid:{path.name}:{line_number}"
                )
            records.append(payload)
    return records


def _assert_not_symlink(path: Path, *, root: Path, code: str) -> None:
    current = path
    while True:
        if current.is_symlink():
            raise QualityLoopMetricsError(code)
        if current == root or current.parent == current:
            return
        current = current.parent


def _load_json_object(path: Path, *, root: Path, code: str) -> dict[str, Any]:
    _assert_not_symlink(path, root=root, code=code)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QualityLoopMetricsError(f"{code}:invalid_json:{path.name}") from exc
    if not isinstance(payload, dict):
        raise QualityLoopMetricsError(f"{code}:invalid_json:{path.name}")
    return payload


def _candidate_key(record: dict[str, Any]) -> str | None:
    fixture = record.get("fixture")
    if not isinstance(fixture, str) or not fixture:
        return None
    action = record.get("action") if isinstance(record.get("action"), dict) else {}
    candidate_hash = action.get("candidate_hash")
    if isinstance(candidate_hash, str) and candidate_hash:
        return f"{fixture}:{candidate_hash}"
    return None


def _outcome(record: dict[str, Any]) -> dict[str, Any]:
    outcome = record.get("outcome")
    return outcome if isinstance(outcome, dict) else {}


def _is_auto_accept(record: dict[str, Any]) -> bool:
    outcome = _outcome(record)
    human_decision_kind = str(outcome.get("human_decision_kind") or "")
    human_label = str(outcome.get("human_label") or "")
    return (
        human_decision_kind == "auto_accept"
        or human_label == "auto_accept"
        or (human_decision_kind == "auto" and human_label == "accept")
    )


def _is_revert(record: dict[str, Any]) -> bool:
    outcome = _outcome(record)
    apply_status = str(outcome.get("apply_status") or "")
    quality_movement = str(outcome.get("quality_movement") or "")
    human_label = str(outcome.get("human_label") or "")
    human_decision_kind = str(outcome.get("human_decision_kind") or "")
    return (
        apply_status == "rolled_back"
        or quality_movement == "regressed"
        or human_label in {"reject", "rejected", "defer", "deferred"}
        or human_decision_kind in {"human_revert", "rollback"}
    )


def _candidate_hash(record: dict[str, Any]) -> str | None:
    action = record.get("action") if isinstance(record.get("action"), dict) else {}
    value = action.get("candidate_hash")
    return value if isinstance(value, str) and value else None


def _changed_pixel_ratio(record: dict[str, Any]) -> float | None:
    outcome = _outcome(record)
    pixel_delta = outcome.get("pixel_delta")
    if not isinstance(pixel_delta, dict):
        return None
    try:
        return float(pixel_delta.get("changed_pixel_ratio"))
    except (TypeError, ValueError):
        return None


def _is_iteration_record(record: dict[str, Any]) -> bool:
    outcome = _outcome(record)
    return str(outcome.get("apply_status") or "") not in {"", "unchosen"}


def _auto_accept_precision(records: list[dict[str, Any]]) -> dict[str, Any]:
    auto_accepted: set[str] = set()
    reverted: set[str] = set()
    seen_auto_accept: set[str] = set()
    skipped_missing_candidate_hash_count = 0
    for record in records:
        key = _candidate_key(record)
        if key is None:
            if _is_auto_accept(record) or _is_revert(record):
                skipped_missing_candidate_hash_count += 1
            continue
        if _is_auto_accept(record):
            auto_accepted.add(key)
            seen_auto_accept.add(key)
            continue
        if key in seen_auto_accept and _is_revert(record):
            reverted.add(key)
    auto_count = len(auto_accepted)
    reverted_count = len(reverted)
    precision = None if auto_count == 0 else round((auto_count - reverted_count) / auto_count, 4)
    return {
        "state": "measured" if auto_count else "unmeasured",
        "auto_accepted_count": auto_count,
        "reverted_count": reverted_count,
        "precision": precision,
        "reverted_candidates": sorted(reverted),
        "skipped_missing_candidate_hash_count": skipped_missing_candidate_hash_count,
    }


def _wasted_iteration_rate(records: list[dict[str, Any]]) -> dict[str, Any]:
    seen_hashes: set[str] = set()
    wasted: dict[str, list[str]] = {}
    iteration_count = 0
    wasted_count = 0
    skipped_missing_candidate_hash_count = 0
    for record in records:
        key = _candidate_key(record)
        if not _is_iteration_record(record):
            continue
        if key is None:
            skipped_missing_candidate_hash_count += 1
            continue
        iteration_count += 1
        reasons: list[str] = []
        candidate_hash = _candidate_hash(record)
        if candidate_hash:
            if candidate_hash in seen_hashes:
                reasons.append("historical_repeat")
            seen_hashes.add(candidate_hash)
        changed_pixel_ratio = _changed_pixel_ratio(record)
        if changed_pixel_ratio is not None and changed_pixel_ratio <= 0.0:
            reasons.append("no_op_nudge")
        if reasons:
            wasted_count += 1
            wasted[key] = sorted(set([*wasted.get(key, []), *reasons]))
    return {
        "state": "measured" if iteration_count else "unmeasured",
        "iteration_count": iteration_count,
        "wasted_count": wasted_count,
        "rate": None if iteration_count == 0 else round(wasted_count / iteration_count, 4),
        "wasted_candidates": sorted(wasted),
        "reasons_by_candidate": dict(sorted(wasted.items())),
        "skipped_missing_candidate_hash_count": skipped_missing_candidate_hash_count,
    }


def _week_key(value: Any) -> str:
    timestamp = _parse_timestamp(value)
    if timestamp is None:
        return "unknown"
    year, week, _weekday = timestamp.isocalendar()
    return f"{year}-W{week:02d}"


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp


def _timestamp_text(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _loop_run_manifests(workspace_root: Path) -> list[tuple[Path, dict[str, Any]]]:
    scratch = workspace_root / ".scratch"
    if scratch.is_symlink():
        raise QualityLoopMetricsError("loop_run_symlink")
    if not scratch.is_dir():
        return []
    runs_root = scratch / "fig-loop-runs"
    if runs_root.is_symlink():
        raise QualityLoopMetricsError("loop_run_symlink")
    if not runs_root.is_dir():
        return []
    manifests: list[tuple[Path, dict[str, Any]]] = []
    for manifest_path in sorted(runs_root.glob("*/run_manifest.json")):
        _assert_not_symlink(manifest_path, root=scratch, code="loop_run_symlink")
        manifest = _load_json_object(
            manifest_path,
            root=scratch,
            code="loop_run_manifest",
        )
        if manifest.get("schema") != LOOP_RUN_SCHEMA:
            continue
        manifests.append(
            (
                manifest_path,
                manifest,
            )
        )
    return manifests


def _run_id(manifest_path: Path, manifest: dict[str, Any]) -> str:
    value = manifest.get("run_id")
    if isinstance(value, str) and value:
        return value
    run_dir = manifest.get("run_dir")
    if isinstance(run_dir, str) and run_dir:
        return Path(run_dir).name
    return manifest_path.parent.name


def _record_created_at(record: dict[str, Any]) -> datetime | None:
    return _parse_timestamp(record.get("created_at"))


def _record_fixture(record: dict[str, Any]) -> str | None:
    value = record.get("fixture")
    return value if isinstance(value, str) and value else None


def _run_fixture(manifest: dict[str, Any]) -> str | None:
    value = manifest.get("fixture")
    return value if isinstance(value, str) and value else None


def _run_window(
    manifest: dict[str, Any],
) -> tuple[str | None, str | None, datetime | None, datetime | None]:
    started_text = _timestamp_text(manifest, "started_at", "created_at", "generated_at")
    completed_text = _timestamp_text(manifest, "completed_at", "finished_at", "created_at")
    started_at = _parse_timestamp(started_text)
    completed_at = _parse_timestamp(completed_text) or started_at
    if started_at is not None and completed_at is not None and completed_at < started_at:
        completed_at = started_at
    return started_text, completed_text, started_at, completed_at


def _contains_record(
    *,
    started_at: datetime | None,
    completed_at: datetime | None,
    run_fixture: str | None,
    record: dict[str, Any],
) -> bool:
    record_created_at = _record_created_at(record)
    if started_at is None or completed_at is None or record_created_at is None:
        return False
    record_fixture = _record_fixture(record)
    if run_fixture is not None and record_fixture is not None and run_fixture != record_fixture:
        return False
    return started_at <= record_created_at <= completed_at


def _experience_log_growth(
    *,
    records: list[dict[str, Any]],
    workspace_root: Path,
) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for manifest_path, manifest in _loop_run_manifests(workspace_root):
        started_text, completed_text, started_at, completed_at = _run_window(manifest)
        runs.append(
            {
                "run_id": _run_id(manifest_path, manifest),
                "fixture": _run_fixture(manifest),
                "started_at": started_text,
                "completed_at": completed_text,
                "started_datetime": started_at,
                "completed_datetime": completed_at,
                "record_count": 0,
            }
        )
    runs.sort(key=lambda run: (run["started_at"] or "", run["run_id"]))

    unassigned_record_count = 0
    for record in records:
        matched = False
        for run in runs:
            if _contains_record(
                started_at=run["started_datetime"],
                completed_at=run["completed_datetime"],
                run_fixture=run["fixture"],
                record=record,
            ):
                run["record_count"] += 1
                matched = True
                break
        if not matched:
            unassigned_record_count += 1

    records_by_run = [
        {
            "run_id": run["run_id"],
            "fixture": run["fixture"],
            "started_at": run["started_at"],
            "completed_at": run["completed_at"],
            "record_count": run["record_count"],
        }
        for run in runs
    ]
    runs_without_growth = [
        str(run["run_id"]) for run in records_by_run if run["record_count"] == 0
    ]
    return {
        "state": "measured" if runs else "unmeasured",
        "run_count": len(runs),
        "total_records_attributed": sum(run["record_count"] for run in records_by_run),
        "unassigned_record_count": unassigned_record_count,
        "runs_without_growth": runs_without_growth,
        "records_by_run": records_by_run,
    }


def _increment(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def _sorted_counter(counter: dict[str, int]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def _stop_cause_histogram(workspace_root: Path) -> dict[str, Any]:
    manifests = _loop_run_manifests(workspace_root)
    if not manifests:
        return {
            "state": "unmeasured",
            "run_count": 0,
            "route_count": 0,
            "total_histogram": {},
            "histogram_by_week": {},
            "auto_remedied_count": 0,
            "auto_remedied_fraction": None,
        }
    scratch = workspace_root / ".scratch"
    total_histogram: dict[str, int] = {}
    histogram_by_week: dict[str, dict[str, int]] = {}
    run_count = 0
    route_count = 0
    auto_remedied_count = 0

    for manifest_path, manifest in manifests:
        run_count += 1
        week = _week_key(
            manifest.get("created_at")
            or manifest.get("generated_at")
            or manifest.get("started_at")
        )
        weekly_histogram = histogram_by_week.setdefault(week, {})
        run_auto_remedied = False
        for iteration_path in sorted(manifest_path.parent.glob("iteration_*.json")):
            iteration = _load_json_object(
                iteration_path,
                root=scratch,
                code="loop_run_iteration",
            )
            routes = iteration.get("stop_routes")
            if isinstance(routes, list):
                for route in routes:
                    if not isinstance(route, dict):
                        continue
                    stop_cause = route.get("stop_cause")
                    if not isinstance(stop_cause, str) or not stop_cause:
                        continue
                    route_count += 1
                    _increment(total_histogram, stop_cause)
                    _increment(weekly_histogram, stop_cause)
            auto_remedy = iteration.get("auto_remedy")
            if isinstance(auto_remedy, dict) and auto_remedy.get("status") == "remedied":
                run_auto_remedied = True
        if run_auto_remedied:
            auto_remedied_count += 1

    return {
        "state": "measured" if run_count else "unmeasured",
        "run_count": run_count,
        "route_count": route_count,
        "total_histogram": _sorted_counter(total_histogram),
        "histogram_by_week": {
            week: _sorted_counter(histogram)
            for week, histogram in sorted(histogram_by_week.items())
        },
        "auto_remedied_count": auto_remedied_count,
        "auto_remedied_fraction": (
            None if run_count == 0 else round(auto_remedied_count / run_count, 4)
        ),
    }


def build_loop_metrics(
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    records = _load_experience_records(paths.plugin_root)
    return {
        "schema": SCHEMA,
        "record_count": len(records),
        "metrics": {
            "auto_accept_precision": _auto_accept_precision(records),
            "wasted_iteration_rate": _wasted_iteration_rate(records),
            "stop_cause_histogram": _stop_cause_histogram(paths.workspace_root),
            "experience_log_growth": _experience_log_growth(
                records=records,
                workspace_root=paths.workspace_root,
            ),
        },
    }


def main(
    argv: list[str] | None = None,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.parse_args(argv)
    payload = build_loop_metrics(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
