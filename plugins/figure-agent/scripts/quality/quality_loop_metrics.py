"""Measure loop-level automation metrics from durable logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.loop-metrics.v1"


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


def _candidate_key(record: dict[str, Any]) -> str | None:
    fixture = record.get("fixture")
    action = record.get("action") if isinstance(record.get("action"), dict) else {}
    candidate_id = action.get("candidate_id")
    if not isinstance(fixture, str) or not isinstance(candidate_id, str):
        return None
    if not fixture or not candidate_id:
        return None
    return f"{fixture}:{candidate_id}"


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


def _auto_accept_precision(records: list[dict[str, Any]]) -> dict[str, Any]:
    auto_accepted: set[str] = set()
    reverted: set[str] = set()
    seen_auto_accept: set[str] = set()
    for record in records:
        key = _candidate_key(record)
        if key is None:
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
