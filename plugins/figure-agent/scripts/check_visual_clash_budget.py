#!/usr/bin/env python3
"""Enforce per-fixture visual-clash WARN budgets from compiled JSON reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import fixture_identity
from inputs import parse_spec

SUMMARY_SCHEMA = "figure-agent.warning-budget.v1"


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


def summarize_fixture(example_dir: Path) -> dict[str, Any]:
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        return {
            "schema": SUMMARY_SCHEMA,
            "fixture": example_dir.name,
            "state": "missing_input",
            "reason": "missing spec.yaml for warning budget",
            "visual_clash": {
                "present": False,
                "total": None,
                "cap": None,
                "over_by": None,
                "status": "missing_spec",
            },
        }
    try:
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return {
            "schema": SUMMARY_SCHEMA,
            "fixture": example_dir.name,
            "state": "invalid",
            "reason": f"invalid spec.yaml: {exc}",
            "visual_clash": {
                "present": False,
                "total": None,
                "cap": None,
                "over_by": None,
                "status": "invalid_spec",
            },
        }
    name = _fixture_name(example_dir, spec)
    try:
        cap = _visual_clash_cap(spec)
    except VisualClashBudgetError as exc:
        return {
            "schema": SUMMARY_SCHEMA,
            "fixture": name,
            "state": "invalid",
            "reason": str(exc),
            "visual_clash": {
                "present": False,
                "total": None,
                "cap": None,
                "over_by": None,
                "status": "invalid_cap",
            },
        }
    report_path = example_dir / "build" / "visual_clash.json"
    if not report_path.is_file():
        return {
            "schema": SUMMARY_SCHEMA,
            "fixture": name,
            "state": "missing_input",
            "reason": "missing build/visual_clash.json for warning budget",
            "visual_clash": {
                "present": False,
                "total": None,
                "cap": cap,
                "over_by": None,
                "status": "missing_report",
            },
        }
    try:
        total = _load_total(report_path)
    except VisualClashBudgetError as exc:
        return {
            "schema": SUMMARY_SCHEMA,
            "fixture": name,
            "state": "invalid",
            "reason": str(exc),
            "visual_clash": {
                "present": True,
                "total": None,
                "cap": cap,
                "over_by": None,
                "status": "invalid_report",
            },
        }
    over_by = max(0, total - cap)
    if over_by:
        return {
            "schema": SUMMARY_SCHEMA,
            "fixture": name,
            "state": "needs_action",
            "reason": "visual clash warning budget exceeded",
            "visual_clash": {
                "present": True,
                "total": total,
                "cap": cap,
                "over_by": over_by,
                "status": "over_budget",
            },
        }
    return {
        "schema": SUMMARY_SCHEMA,
        "fixture": name,
        "state": "pass",
        "reason": "visual clash warnings are within budget",
        "visual_clash": {
            "present": True,
            "total": total,
            "cap": cap,
            "over_by": 0,
            "status": "within_budget",
        },
    }


def check_fixture(example_dir: Path) -> dict[str, Any]:
    summary = summarize_fixture(example_dir)
    name = str(summary.get("fixture") or example_dir.name)
    visual_clash = summary.get("visual_clash")
    if not isinstance(visual_clash, dict):
        raise VisualClashBudgetError(f"{name}: invalid warning budget summary")
    total = visual_clash.get("total")
    cap = visual_clash.get("cap")
    state = summary.get("state")
    if state in {"missing_input", "invalid"}:
        raise VisualClashBudgetError(f"{name}: {summary.get('reason')}")
    if not isinstance(total, int) or not isinstance(cap, int):
        raise VisualClashBudgetError(f"{name}: invalid warning budget totals")
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


def _resolve_target_for_cli(value: Path) -> Path:
    examples_root = Path("examples").resolve()
    if value.is_absolute():
        resolved = value.resolve()
        if resolved == examples_root:
            return Path("examples")
        try:
            relative = resolved.relative_to(examples_root)
        except ValueError as exc:
            raise VisualClashBudgetError(
                "invalid target path: expected examples/ or examples/<fixture-name>"
            ) from exc
        if len(relative.parts) != 1 or ".." in relative.parts:
            raise VisualClashBudgetError(
                "invalid target path: expected examples/<fixture-name>"
            )
        _validate_fixture_name_for_cli(relative.parts[0], str(value))
        return Path("examples") / relative.parts[0]
    if value == Path("examples"):
        return value
    if value.parts and value.parts[0] == "examples":
        if len(value.parts) != 2 or ".." in value.parts:
            raise VisualClashBudgetError(
                "invalid target path: expected examples/ or examples/<fixture-name>"
            )
        _validate_fixture_name_for_cli(value.parts[1], str(value))
        return Path("examples") / value.parts[1]
    if len(value.parts) == 1:
        _validate_fixture_name_for_cli(str(value), str(value))
        examples_path = Path("examples") / value
        if examples_path.is_dir():
            return examples_path
        if value.exists():
            raise VisualClashBudgetError(
                "invalid target path: relative fixture names must resolve under examples/"
            )
        return examples_path
    raise VisualClashBudgetError(
        "invalid target path: expected fixture name, examples/, examples/<fixture-name>, "
        "or an absolute path under examples/"
    )


def _validate_fixture_name_for_cli(name: str, original: str) -> None:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise VisualClashBudgetError(f"invalid target path: {original}: {exc}") from exc


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
        results = check_targets([_resolve_target_for_cli(target) for target in args.targets])
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
