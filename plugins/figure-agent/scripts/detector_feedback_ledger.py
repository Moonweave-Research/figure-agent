"""Aggregate detector-feedback signals across figure fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import fixture_identity
from audit_evidence_summary import summarize_audit_evidence

SCHEMA = "figure-agent.detector-feedback-ledger.v1"
DETECTOR_KEYS = ("visual_clash", "text_boundary", "label_path", "undeclared_geometry")
DETECTOR_COUNT_KEYS = (
    "candidate_count",
    "accounted_count",
    "accepted_false_positive_count",
    "linked_defect_count",
)


def _selected_fixture_dirs(examples_root: Path, fixture_names: list[str]) -> list[Path]:
    examples_root = examples_root.resolve()
    if fixture_names:
        fixture_dirs: list[Path] = []
        for fixture_name in sorted(dict.fromkeys(fixture_names)):
            fixture_identity.validate_fixture_name(fixture_name)
            fixture_dir = examples_root / fixture_name
            if not fixture_dir.is_dir():
                raise ValueError(f"fixture not found: {fixture_name}")
            fixture_dirs.append(fixture_dir)
        return fixture_dirs

    if not examples_root.is_dir():
        return []
    return sorted(
        (
            path
            for path in examples_root.iterdir()
            if _is_fixture_dir_under_examples_root(path, examples_root)
        ),
        key=lambda path: path.name,
    )


def _is_fixture_dir_under_examples_root(path: Path, examples_root: Path) -> bool:
    if not path.is_dir() or not (path / "critique.md").is_file():
        return False
    try:
        path.resolve().relative_to(examples_root)
    except ValueError:
        return False
    return True


def _empty_totals() -> dict[str, Any]:
    totals: dict[str, Any] = {
        detector: {key: 0 for key in DETECTOR_COUNT_KEYS} for detector in DETECTOR_KEYS
    }
    totals["unlinked_micro_defect_count"] = 0
    totals["unlinked_micro_defect_refs"] = []
    return totals


def _int(value: Any) -> int:
    return value if isinstance(value, int) else 0


def _add_feedback_to_totals(
    totals: dict[str, Any],
    fixture: str,
    feedback: dict[str, Any],
) -> None:
    for detector in DETECTOR_KEYS:
        detector_feedback = feedback.get(detector)
        if not isinstance(detector_feedback, dict):
            continue
        for key in DETECTOR_COUNT_KEYS:
            totals[detector][key] += _int(detector_feedback.get(key))

    unlinked_ids = feedback.get("unlinked_micro_defect_ids")
    if not isinstance(unlinked_ids, list):
        unlinked_ids = []
    for item_id in unlinked_ids:
        if isinstance(item_id, str) and item_id.strip():
            totals["unlinked_micro_defect_refs"].append(f"{fixture}:{item_id.strip()}")
    totals["unlinked_micro_defect_count"] = len(totals["unlinked_micro_defect_refs"])


def _fixture_row(fixture_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "fixture": fixture_dir.name,
        "evaluation_state": summary.get("evaluation_state"),
        "reason": summary.get("reason"),
        "blocking_items": summary.get("blocking_items", []),
        "detector_feedback": summary.get("detector_feedback", {}),
    }


def build_detector_feedback_ledger(
    examples_root: Path,
    fixture_names: list[str],
) -> dict[str, Any]:
    """Return a read-only cross-fixture detector-feedback ledger."""
    fixture_dirs = _selected_fixture_dirs(examples_root, fixture_names)
    totals = _empty_totals()
    rows: list[dict[str, Any]] = []
    for fixture_dir in fixture_dirs:
        summary = summarize_audit_evidence(fixture_dir)
        feedback = summary.get("detector_feedback")
        if not isinstance(feedback, dict):
            feedback = {}
        _add_feedback_to_totals(totals, fixture_dir.name, feedback)
        rows.append(_fixture_row(fixture_dir, summary))

    totals["unlinked_micro_defect_refs"] = sorted(
        dict.fromkeys(totals["unlinked_micro_defect_refs"])
    )
    totals["unlinked_micro_defect_count"] = len(totals["unlinked_micro_defect_refs"])
    return {
        "schema": SCHEMA,
        "examples_root": str(examples_root.resolve()),
        "fixture_count": len(rows),
        "totals": totals,
        "fixtures": rows,
    }


def _default_examples_root() -> Path:
    return Path(__file__).resolve().parents[1] / "examples"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixtures", nargs="*", help="fixture names; defaults to all critiques")
    parser.add_argument("--examples-root", type=Path, default=_default_examples_root())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        ledger = build_detector_feedback_ledger(args.examples_root, args.fixtures)
    except ValueError as exc:
        print(f"detector_feedback_ledger.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(ledger, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
