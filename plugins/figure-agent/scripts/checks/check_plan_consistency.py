#!/usr/bin/env python3
"""Report fixture drift against the canonical paper figure map."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

MAP_SCHEMA = "figure-agent.paper-figure-map.v1"
REPORT_SCHEMA = "figure-agent.plan-consistency.v1"

STOPWORDS = {
    "about",
    "against",
    "current",
    "during",
    "figure",
    "mechanism",
    "schematic",
    "states",
    "with",
}


def _fixture_dirs(examples_dir: Path) -> list[Path]:
    fixtures = []
    for path in sorted(examples_dir.iterdir()):
        if not path.is_dir() or path.name.startswith("_") or path.name.startswith("smoke_"):
            continue
        if (path / "spec.yaml").is_file():
            fixtures.append(path)
    return fixtures


def _load_map(map_path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != MAP_SCHEMA:
        raise ValueError(f"plan map must use schema {MAP_SCHEMA}")
    return payload


def _content_words(text: str) -> set[str]:
    words = set()
    for word in re.findall(r"[A-Za-z][A-Za-z0-9-]+", text.lower()):
        if len(word) >= 4 and word not in STOPWORDS:
            words.add(word)
    return words


def _briefing_head_words(fixture_dir: Path) -> set[str]:
    briefing = fixture_dir / "briefing.md"
    if not briefing.is_file():
        return set()
    return _content_words("\n".join(briefing.read_text(encoding="utf-8").splitlines()[:5]))


def _non_main_entries(plan_map: dict[str, Any]) -> dict[str, str]:
    entries: dict[str, str] = {}
    for figure, spec in (plan_map.get("figures") or {}).items():
        if not isinstance(spec, dict):
            continue
        for fixture in spec.get("sandbox") or []:
            entries[str(fixture)] = "sandbox"
    for state, fixtures in (plan_map.get("non_main") or {}).items():
        for fixture in fixtures or []:
            entries[str(fixture)] = str(state)
    return entries


def build_report(examples_dir: Path, map_path: Path) -> dict[str, Any]:
    plan_map = _load_map(map_path)
    fixtures = {path.name: path for path in _fixture_dirs(examples_dir)}
    findings: list[dict[str, Any]] = []
    figures = plan_map.get("figures") or {}
    main_fixtures: dict[str, str] = {}
    non_main = _non_main_entries(plan_map)

    for figure, spec in figures.items():
        if not isinstance(spec, dict):
            continue
        mapped = [str(item) for item in spec.get("fixtures") or []]
        if not mapped and spec.get("status") == "missing":
            findings.append(
                {
                    "code": "planned_figure_missing",
                    "figure": str(figure),
                    "state": "missing",
                    "role": str(spec.get("role") or ""),
                }
            )
        for fixture in mapped:
            main_fixtures[fixture] = str(figure)
            if fixture not in fixtures:
                findings.append(
                    {
                        "code": "missing_mapped_fixture",
                        "figure": str(figure),
                        "fixture": fixture,
                    }
                )
                continue
            role_words = _content_words(str(spec.get("role") or ""))
            briefing_words = _briefing_head_words(fixtures[fixture])
            matched = sorted(role_words & briefing_words)
            if len(matched) < 2:
                findings.append(
                    {
                        "code": "role_drift",
                        "figure": str(figure),
                        "fixture": fixture,
                        "matched_role_tokens": matched,
                        "required_role_tokens": sorted(role_words),
                    }
                )

    for fixture, state in sorted(non_main.items()):
        if fixture in fixtures:
            findings.append(
                {
                    "code": "non_main_fixture",
                    "fixture": fixture,
                    "state": state,
                }
            )
        else:
            findings.append(
                {
                    "code": "missing_mapped_fixture",
                    "fixture": fixture,
                    "state": state,
                }
            )

    known = set(main_fixtures) | set(non_main)
    for fixture in sorted(set(fixtures) - known):
        findings.append({"code": "unmapped_fixture", "fixture": fixture})

    return {
        "schema": REPORT_SCHEMA,
        "map_schema": MAP_SCHEMA,
        "examples_dir": str(examples_dir),
        "map_path": str(map_path),
        "finding_count": len(findings),
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_plan_consistency.py")
    parser.add_argument("--examples-dir", type=Path, default=Path("examples"))
    parser.add_argument("--map", type=Path, default=Path("docs/paper_figure_map.yaml"))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.examples_dir, args.map)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if args.strict and report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
