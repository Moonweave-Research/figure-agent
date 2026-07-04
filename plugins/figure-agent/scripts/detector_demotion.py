"""Recommend detector demotion from telemetry plus adjudicated feedback."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import fixture_identity
from detector_feedback_ledger import (
    DETECTOR_COUNT_KEYS,
    DETECTOR_KEYS,
    build_detector_feedback_ledger,
)

SCHEMA = "figure-agent.detector-demotion-recommendations.v1"


def _default_examples_root() -> Path:
    return Path(__file__).resolve().parents[1] / "examples"


def _fixture_names_from_feedback(ledger: dict[str, Any]) -> list[str]:
    rows = ledger.get("fixtures")
    if not isinstance(rows, list):
        return []
    names: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        fixture = row.get("fixture")
        if isinstance(fixture, str) and fixture:
            names.append(fixture)
    return names


def _safe_fixture_dir(examples_root: Path, fixture: str) -> Path:
    fixture_identity.validate_fixture_name(fixture)
    examples_root = examples_root.resolve()
    fixture_dir = examples_root / fixture
    resolved = fixture_dir.resolve()
    try:
        resolved.relative_to(examples_root)
    except ValueError as exc:
        raise ValueError(f"fixture_symlink_escape_forbidden: {fixture}") from exc
    return fixture_dir


def _int(value: Any) -> int:
    return value if type(value) is int else 0


def _bool(value: Any) -> bool:
    return value if type(value) is bool else False


def _read_detector_log(fixture_dir: Path) -> dict[str, dict[str, int]]:
    build_dir = fixture_dir / "build"
    if build_dir.is_symlink():
        raise ValueError(f"detector_log_symlink_forbidden: {fixture_dir.name}:build")
    log_path = build_dir / "detector_log.jsonl"
    if not log_path.exists():
        return {}
    if log_path.is_symlink():
        raise ValueError(f"detector_log_symlink_forbidden: {fixture_dir.name}")
    try:
        log_path.resolve().relative_to(fixture_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"detector_log_escape_forbidden: {fixture_dir.name}") from exc

    totals: dict[str, dict[str, int]] = {}
    with log_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"detector_log_invalid_json: {fixture_dir.name}:{line_number}"
                ) from exc
            if not isinstance(record, dict):
                raise ValueError(f"detector_log_invalid_record: {fixture_dir.name}:{line_number}")
            name = record.get("name")
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"detector_log_missing_name: {fixture_dir.name}:{line_number}")
            detector = name.strip()
            row = totals.setdefault(
                detector,
                {"log_run_count": 0, "fired_run_count": 0, "finding_count": 0},
            )
            row["log_run_count"] += 1
            if _bool(record.get("fired")):
                row["fired_run_count"] += 1
            row["finding_count"] += max(0, _int(record.get("finding_count")))
    return totals


def _detector_log_totals(examples_root: Path, fixtures: list[str]) -> dict[str, dict[str, int]]:
    totals: dict[str, dict[str, int]] = {}
    for fixture in fixtures:
        fixture_dir = _safe_fixture_dir(examples_root, fixture)
        for detector, counts in _read_detector_log(fixture_dir).items():
            row = totals.setdefault(
                detector,
                {"log_run_count": 0, "fired_run_count": 0, "finding_count": 0},
            )
            row["log_run_count"] += counts["log_run_count"]
            row["fired_run_count"] += counts["fired_run_count"]
            row["finding_count"] += counts["finding_count"]
    return totals


def _detector_order(feedback_totals: dict[str, Any], log_totals: dict[str, Any]) -> list[str]:
    known = list(DETECTOR_KEYS)
    ordered_extras: set[str] = set()
    for detector in set(feedback_totals).union(log_totals):
        if not isinstance(detector, str) or detector in known:
            continue
        has_feedback_counts = isinstance(feedback_totals.get(detector, {}), dict)
        has_log_counts = detector in log_totals
        if has_feedback_counts or has_log_counts:
            ordered_extras.add(detector)
    extras = sorted(
        ordered_extras,
    )
    return [*known, *extras]


def _recommendation_reason(
    *,
    candidate_count: int,
    false_positive_rate: float,
    log_run_count: int,
    threshold: float,
    min_candidate_count: int,
    recommendation: str,
) -> str:
    if recommendation == "demote":
        return (
            "accepted false-positive rate meets demotion threshold "
            f"({false_positive_rate:.3f} >= {threshold:.3f})"
        )
    if candidate_count < min_candidate_count:
        return (
            "keep: insufficient adjudicated detector candidates "
            f"({candidate_count} < {min_candidate_count})"
        )
    if log_run_count == 0:
        return "keep: no detector_log.jsonl coverage for this detector"
    return (
        "keep: accepted false-positive rate is below demotion threshold "
        f"({false_positive_rate:.3f} < {threshold:.3f})"
    )


def _detector_row(
    detector: str,
    feedback_totals: dict[str, Any],
    log_totals: dict[str, dict[str, int]],
    *,
    false_positive_threshold: float,
    min_candidate_count: int,
) -> dict[str, Any]:
    feedback = feedback_totals.get(detector)
    if not isinstance(feedback, dict):
        feedback = {}
    candidate_count = _int(feedback.get("candidate_count"))
    accepted_false_positive_count = _int(feedback.get("accepted_false_positive_count"))
    false_positive_rate = (
        accepted_false_positive_count / candidate_count if candidate_count > 0 else 0.0
    )
    log_counts = log_totals.get(
        detector,
        {"log_run_count": 0, "fired_run_count": 0, "finding_count": 0},
    )
    recommendation = (
        "demote"
        if candidate_count >= min_candidate_count
        and false_positive_rate >= false_positive_threshold
        else "keep"
    )
    row: dict[str, Any] = {
        "detector": detector,
        "false_positive_rate": round(false_positive_rate, 6),
        "recommendation": recommendation,
        "reason": _recommendation_reason(
            candidate_count=candidate_count,
            false_positive_rate=false_positive_rate,
            log_run_count=log_counts["log_run_count"],
            threshold=false_positive_threshold,
            min_candidate_count=min_candidate_count,
            recommendation=recommendation,
        ),
        "log_run_count": log_counts["log_run_count"],
        "fired_run_count": log_counts["fired_run_count"],
        "finding_count": log_counts["finding_count"],
    }
    for key in DETECTOR_COUNT_KEYS:
        row[key] = _int(feedback.get(key))
    return row


def build_detector_demotion_recommendations(
    examples_root: Path,
    fixture_names: list[str],
    *,
    false_positive_threshold: float = 0.5,
    min_candidate_count: int = 2,
) -> dict[str, Any]:
    """Return read-only detector demotion recommendations.

    The demotion signal is deliberately advisory: adjudicated false positives
    provide the rate, while detector_log.jsonl contributes execution coverage.
    """
    if not 0.0 <= false_positive_threshold <= 1.0:
        raise ValueError("false_positive_threshold must be between 0 and 1")
    if min_candidate_count < 1:
        raise ValueError("min_candidate_count must be at least 1")

    examples_root = examples_root.resolve()
    feedback_ledger = build_detector_feedback_ledger(examples_root, fixture_names)
    fixtures = _fixture_names_from_feedback(feedback_ledger)
    feedback_totals = feedback_ledger.get("totals")
    if not isinstance(feedback_totals, dict):
        feedback_totals = {}
    log_totals = _detector_log_totals(examples_root, fixtures)
    detectors = [
        _detector_row(
            detector,
            feedback_totals,
            log_totals,
            false_positive_threshold=false_positive_threshold,
            min_candidate_count=min_candidate_count,
        )
        for detector in _detector_order(feedback_totals, log_totals)
    ]
    return {
        "schema": SCHEMA,
        "examples_root": str(examples_root),
        "fixtures": fixtures,
        "fixture_count": len(fixtures),
        "thresholds": {
            "false_positive_rate": false_positive_threshold,
            "min_candidate_count": min_candidate_count,
        },
        "detectors": detectors,
        "recommendations": [
            row for row in detectors if row.get("recommendation") == "demote"
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixtures", nargs="*", help="fixture names; defaults to all critiques")
    parser.add_argument("--examples-root", type=Path, default=_default_examples_root())
    parser.add_argument("--false-positive-threshold", type=float, default=0.5)
    parser.add_argument("--min-candidates", type=int, default=2)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json",), default="json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = build_detector_demotion_recommendations(
            args.examples_root,
            args.fixtures,
            false_positive_threshold=args.false_positive_threshold,
            min_candidate_count=args.min_candidates,
        )
    except ValueError as exc:
        print(f"detector_demotion.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
