"""Aggregate detector-feedback signals across figure fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import fixture_identity
import yaml
from audit_evidence_summary import summarize_audit_evidence
from quality_manifest import yaml_frontmatter

SCHEMA = "figure-agent.detector-feedback-ledger.v1"
DETECTOR_KEYS = ("visual_clash", "text_boundary", "label_path", "undeclared_geometry")
DETECTOR_COUNT_KEYS = (
    "candidate_count",
    "accounted_count",
    "accepted_false_positive_count",
    "linked_defect_count",
)
DETECTOR_FAMILY_SOURCES = {
    "visual_clash": ("visual_clash.json", "visual_clash_ref"),
    "text_boundary": ("text_boundary_clash.json", "text_boundary_ref"),
    "label_path": ("label_path_proximity.json", "label_path_ref"),
    "undeclared_geometry": ("undeclared_geometry.json", "undeclared_geometry_ref"),
}


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
        "reviewed_families": _reviewed_families(fixture_dir),
    }


def _candidate_families(report_path: Path) -> dict[str, str]:
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    candidates = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(candidates, list):
        return {}
    families: dict[str, str] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_id = candidate.get("id")
        family = candidate.get("kind")
        if isinstance(candidate_id, str) and candidate_id and isinstance(family, str) and family:
            families[candidate_id] = family
    return families


def _reviewed_families(fixture_dir: Path) -> list[dict[str, Any]]:
    try:
        frontmatter = yaml_frontmatter(fixture_dir / "critique.md")
    except (FileNotFoundError, ValueError):
        return []
    micro_defects = frontmatter.get("micro_defects")
    if not isinstance(micro_defects, list):
        return []

    counts: dict[tuple[str, str], dict[str, set[str]]] = {}
    for detector, (report_name, ref_field) in DETECTOR_FAMILY_SOURCES.items():
        candidate_families = _candidate_families(fixture_dir / "build" / report_name)
        for item in micro_defects:
            if not isinstance(item, dict):
                continue
            ref = item.get(ref_field)
            if not isinstance(ref, str) or ref not in candidate_families:
                continue
            key = (detector, candidate_families[ref])
            outcome_refs = counts.setdefault(
                key,
                {"accepted_false_positive": set(), "linked_defect": set()},
            )
            if (
                item.get("status") == "accept_simplification"
                and item.get("accept_simplification_reason") == "false_positive"
            ):
                outcome_refs["accepted_false_positive"].add(ref)
            else:
                outcome_refs["linked_defect"].add(ref)

    return [
        {
            "detector": detector,
            "family": family,
            "accepted_false_positive_count": len(outcomes["accepted_false_positive"]),
            "linked_defect_count": len(outcomes["linked_defect"]),
        }
        for (detector, family), outcomes in sorted(counts.items())
    ]


def _aggregate_reviewed_families(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], dict[str, int]] = {}
    for row in rows:
        for item in row["reviewed_families"]:
            key = (item["detector"], item["family"])
            total = counts.setdefault(
                key,
                {"accepted_false_positive_count": 0, "linked_defect_count": 0},
            )
            for count_key in total:
                total[count_key] += item[count_key]
    return [
        {"detector": detector, "family": family, **counts[(detector, family)]}
        for detector, family in sorted(counts)
    ]


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _reviewed_metrics(totals: dict[str, Any]) -> dict[str, Any]:
    true_positives = sum(totals[key]["linked_defect_count"] for key in DETECTOR_KEYS)
    false_positives = sum(
        totals[key]["accepted_false_positive_count"] for key in DETECTOR_KEYS
    )
    false_negatives = totals["unlinked_micro_defect_count"]
    return {
        "reviewed_true_positive_count": true_positives,
        "reviewed_false_positive_count": false_positives,
        "unlinked_false_negative_count": false_negatives,
        "precision": _ratio(true_positives, true_positives + false_positives),
        "recall": _ratio(true_positives, true_positives + false_negatives),
    }


def _dominant_false_positive_family(
    families: list[dict[str, Any]],
) -> dict[str, Any] | None:
    candidates = [item for item in families if item["accepted_false_positive_count"] > 0]
    if not candidates:
        return None
    selected = sorted(
        candidates,
        key=lambda item: (
            -item["accepted_false_positive_count"],
            item["detector"],
            item["family"],
        ),
    )[0]
    reviewed_count = (
        selected["accepted_false_positive_count"] + selected["linked_defect_count"]
    )
    return {
        **selected,
        "reviewed_precision": _ratio(selected["linked_defect_count"], reviewed_count),
    }


def compare_reviewed_benchmark_stages(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare reviewed detection quality without treating finding count as success."""
    total_true_positives = sum(
        case.get("review_outcome") == "true_positive" for case in cases
    )
    comparison: dict[str, Any] = {}
    for stage in ("before", "after"):
        detected = [case for case in cases if case.get(f"detected_{stage}") is True]
        true_positives = sum(
            case.get("review_outcome") == "true_positive" for case in detected
        )
        false_positives = sum(
            case.get("review_outcome") == "false_positive" for case in detected
        )
        unbound = sum(case.get("expected_attribution") == "unbound" for case in detected)
        comparison[stage] = {
            "reviewed_true_positive_count": true_positives,
            "reviewed_false_positive_count": false_positives,
            "precision": _ratio(true_positives, true_positives + false_positives),
            "recall": _ratio(true_positives, total_true_positives),
            "unbound_attribution_rate": _ratio(unbound, len(detected)),
        }
    return comparison


def build_detector_feedback_ledger(
    examples_root: Path,
    fixture_names: list[str],
    benchmark_path: Path | None = None,
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
    reviewed_families = _aggregate_reviewed_families(rows)
    ledger = {
        "schema": SCHEMA,
        "examples_root": str(examples_root.resolve()),
        "fixture_count": len(rows),
        "totals": totals,
        "reviewed_metrics": _reviewed_metrics(totals),
        "reviewed_families": reviewed_families,
        "dominant_false_positive_family": _dominant_false_positive_family(
            reviewed_families
        ),
        "fixtures": rows,
    }
    if benchmark_path is not None and benchmark_path.is_file():
        payload = yaml.safe_load(benchmark_path.read_text(encoding="utf-8")) or {}
        cases = payload.get("cases") if isinstance(payload, dict) else None
        if isinstance(cases, list):
            ledger["reviewed_benchmark_comparison"] = compare_reviewed_benchmark_stages(
                [case for case in cases if isinstance(case, dict)]
            )
        selection = payload.get("reviewed_family_selection")
        if isinstance(selection, dict):
            ledger["benchmark_family_selection"] = selection
    return ledger


def _default_examples_root() -> Path:
    return Path(__file__).resolve().parents[1] / "examples"


def _default_benchmark_path() -> Path:
    return Path(__file__).resolve().parents[1] / "benchmarks" / "visual_attribution_suite.yaml"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixtures", nargs="*", help="fixture names; defaults to all critiques")
    parser.add_argument("--examples-root", type=Path, default=_default_examples_root())
    parser.add_argument("--benchmark", type=Path, default=_default_benchmark_path())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json",), default="json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        ledger = build_detector_feedback_ledger(
            args.examples_root,
            args.fixtures,
            benchmark_path=args.benchmark,
        )
    except ValueError as exc:
        print(f"detector_feedback_ledger.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(ledger, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
