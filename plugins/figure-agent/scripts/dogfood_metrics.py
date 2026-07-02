# scripts/dogfood_metrics.py
"""Minimal cohort dogfood roll-up + non-degeneracy gate (Slice 3, measure-only).

Rolls per-run stop-report cause_histograms into a cohort histogram, computes
dominant_premature_cause over the FOUR quality causes only, and --check exits
non-zero when the cohort is degenerate (no quality cause / 100% plumbing or
settled). The ceiling_distance / autonomy_fraction / regression series are
deferred to Slice 4+ and are deliberately NOT emitted here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "loop"))

from stop_cause_classify import QUALITY_CAUSES, StopCause  # noqa: E402

_HISTOGRAM_KEYS = tuple(cause.value for cause in StopCause)
_QUALITY_KEYS = tuple(cause.value for cause in QUALITY_CAUSES)


def load_cohort(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _empty_histogram() -> dict[str, int]:
    return {key: 0 for key in _HISTOGRAM_KEYS}


def _dominant(histogram: dict[str, int]) -> str | None:
    best_cause: str | None = None
    best_count = 0
    for key in _QUALITY_KEYS:
        count = histogram.get(key, 0)
        if count > best_count:
            best_count = count
            best_cause = key
    return best_cause


def roll_up_run_dirs(run_dirs: list[Path]) -> dict[str, Any]:
    cohort_histogram = _empty_histogram()
    counted = 0
    for run_dir in run_dirs:
        report_path = run_dir / "stop_report.json"
        if not report_path.is_file():
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        histogram = report.get("cause_histogram") or {}
        for key in _HISTOGRAM_KEYS:
            cohort_histogram[key] += int(histogram.get(key, 0))
        counted += 1
    return {
        "schema": "figure-agent.dogfood-rollup.v1",
        "runs_counted": counted,
        "cohort_histogram": cohort_histogram,
        "dominant_premature_cause": _dominant(cohort_histogram),
    }


def is_degenerate(summary: dict[str, Any]) -> bool:
    """Degenerate = no quality cause present (100% plumbing/settled/not_stopped)
    or no dominant cause could be chosen."""
    histogram = summary.get("cohort_histogram") or {}
    quality_total = sum(int(histogram.get(key, 0)) for key in _QUALITY_KEYS)
    return quality_total == 0 or summary.get("dominant_premature_cause") is None


def _resolve_run_dirs(args: argparse.Namespace) -> list[Path]:
    if args.run_dir:
        return [Path(d) for d in args.run_dir]
    runs_root = Path(args.runs_root)
    return sorted(p for p in runs_root.iterdir() if (p / "stop_report.json").is_file())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", action="append", help="explicit run dir (repeatable)")
    parser.add_argument(
        "--runs-root",
        default=str(Path(__file__).resolve().parent.parent / ".scratch" / "fig-loop-runs"),
    )
    parser.add_argument("--check", action="store_true", help="exit non-zero on a degenerate cohort")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    run_dirs = _resolve_run_dirs(args)
    summary = roll_up_run_dirs(run_dirs)
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(
            f"dominant_premature_cause={summary['dominant_premature_cause']} "
            f"runs={summary['runs_counted']} histogram={summary['cohort_histogram']}"
        )
    if args.check and is_degenerate(summary):
        print(
            "dogfood_metrics: DEGENERATE cohort (no quality cause; fix plumbing/setup first)",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
