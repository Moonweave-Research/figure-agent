#!/usr/bin/env python3
"""Enforce per-fixture visual-clash WARN budgets from compiled JSON reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from inputs import parse_spec


class VisualClashBudgetError(Exception):
    """Expected user-facing visual-clash budget failure."""


def _fixture_name(example_dir: Path, spec: dict[str, Any]) -> str:
    return str(spec.get("name") or example_dir.name)


def _visual_clash_cap(spec: dict[str, Any]) -> int:
    raw_cap = spec.get("visual_clash_cap", 0)
    if not isinstance(raw_cap, int) or raw_cap < 0:
        raise VisualClashBudgetError("visual_clash_cap must be a non-negative integer")
    return raw_cap


def _load_total(report_path: Path) -> int:
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VisualClashBudgetError(f"malformed build/visual_clash.json: {exc}") from exc
    total = report.get("total")
    if not isinstance(total, int) or total < 0:
        raise VisualClashBudgetError("build/visual_clash.json total must be a non-negative integer")
    return total


def check_fixture(example_dir: Path) -> dict[str, Any]:
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        raise VisualClashBudgetError(f"{example_dir}: missing spec.yaml")
    try:
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise VisualClashBudgetError(f"{example_dir.name}: invalid spec.yaml: {exc}") from exc
    name = _fixture_name(example_dir, spec)
    cap = _visual_clash_cap(spec)
    report_path = example_dir / "build" / "visual_clash.json"
    if not report_path.is_file():
        raise VisualClashBudgetError(f"{name}: missing build/visual_clash.json")
    total = _load_total(report_path)
    if total > cap:
        raise VisualClashBudgetError(f"{name}: visual clash budget exceeded: {total} > {cap}")
    return {"fixture": name, "total": total, "cap": cap, "status": "ok"}


def _fixture_dirs(target: Path) -> list[Path]:
    if (target / "spec.yaml").is_file():
        return [target]
    if not target.is_dir():
        raise VisualClashBudgetError(f"{target}: not a fixture or examples directory")
    return sorted(
        child
        for child in target.iterdir()
        if child.is_dir() and not child.name.startswith("_") and (child / "spec.yaml").is_file()
    )


def check_targets(targets: list[Path]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for target in targets:
        for fixture_dir in _fixture_dirs(target):
            results.append(check_fixture(fixture_dir))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail when build/visual_clash.json exceeds spec.yaml visual_clash_cap"
    )
    parser.add_argument(
        "targets",
        nargs="+",
        type=Path,
        help="fixture directory or examples/ directory",
    )
    args = parser.parse_args()

    try:
        results = check_targets(args.targets)
    except VisualClashBudgetError as exc:
        print(f"check_visual_clash_budget.py: {exc}", file=sys.stderr)
        return 1

    for result in results:
        print(
            f"OK {result['fixture']}: visual_clash total {result['total']} <= "
            f"cap {result['cap']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
