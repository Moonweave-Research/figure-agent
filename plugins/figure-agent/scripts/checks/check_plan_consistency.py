#!/usr/bin/env python3
"""Validate real fixtures against the canonical paper figure map."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import current_candidate  # noqa: E402

MAP_SCHEMA = "figure-agent.paper-figure-map.v2"
REPORT_SCHEMA = "figure-agent.plan-consistency.v2"
ACTIVE_STATUS = "active_candidate"
PLANNED_MISSING_STATUS = "planned_missing"
NON_MAIN_CLASSES = {
    "pilot",
    "reference",
    "regression",
    "sandbox",
    "si",
    "superseded",
}
NON_FIXTURE_CLASSES = {"artifact_collection", "experiment_evidence"}


def _example_dirs(examples_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in examples_dir.iterdir()
        if path.is_dir() and not path.name.startswith("_")
    )


def _fixture_dirs(examples_dir: Path) -> list[Path]:
    return [path for path in _example_dirs(examples_dir) if (path / "spec.yaml").is_file()]


def _load_map(map_path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != MAP_SCHEMA:
        raise ValueError(f"plan map must use schema {MAP_SCHEMA}")
    return payload


def _load_spec(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _finding(
    code: str,
    *,
    severity: str = "blocking",
    **details: object,
) -> dict[str, Any]:
    return {"code": code, "severity": severity, **details}


def _validate_source_pointer(
    fixture_dir: Path,
    fixture: str,
    source_pointer: str,
) -> list[dict[str, Any]]:
    pointer_path = fixture_dir / source_pointer
    if not pointer_path.is_file():
        return [
            _finding(
                "missing_source_pointer",
                fixture=fixture,
                source_pointer=source_pointer,
            )
        ]
    try:
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return [_finding("invalid_source_pointer", fixture=fixture)]
    if not isinstance(pointer, dict):
        return [_finding("invalid_source_pointer", fixture=fixture)]
    if pointer.get("schema") != current_candidate.CURRENT_CANDIDATE_SCHEMA:
        return [
            _finding(
                "invalid_source_pointer_schema",
                fixture=fixture,
                expected=current_candidate.CURRENT_CANDIDATE_SCHEMA,
                actual=pointer.get("schema"),
            )
        ]
    if pointer.get("fixture") != fixture:
        return [
            _finding(
                "source_pointer_fixture_mismatch",
                fixture=fixture,
                declared_fixture=pointer.get("fixture"),
            )
        ]
    expected_pointer = current_candidate.POINTER_RELATIVE_PATH.as_posix()
    if source_pointer != expected_pointer:
        return [
            _finding(
                "invalid_source_pointer_path",
                fixture=fixture,
                expected=expected_pointer,
                actual=source_pointer,
            )
        ]
    resolved = current_candidate.resolve_current_candidate(fixture_dir)
    if resolved.get("state") != "VALID":
        return [
            _finding(
                "invalid_current_candidate_pointer",
                fixture=fixture,
                reason=resolved.get("reason") or resolved.get("state"),
            )
        ]
    return []


def build_report(examples_dir: Path, map_path: Path) -> dict[str, Any]:
    plan_map = _load_map(map_path)
    example_dirs = {path.name: path for path in _example_dirs(examples_dir)}
    fixtures = {path.name: path for path in _fixture_dirs(examples_dir)}
    findings: list[dict[str, Any]] = []
    paper_id = plan_map.get("paper_id")
    if not isinstance(paper_id, str) or not paper_id.strip():
        findings.append(_finding("missing_paper_id"))

    figures = plan_map.get("figures") or {}
    if not isinstance(figures, dict):
        figures = {}
        findings.append(_finding("invalid_figures_mapping"))

    claimed: dict[str, str] = {}
    for figure_key, entry in sorted(figures.items()):
        if not isinstance(entry, dict):
            findings.append(_finding("invalid_figure_entry", figure=str(figure_key)))
            continue
        figure_id = entry.get("figure_id")
        role_id = entry.get("role_id")
        status = entry.get("status")
        if figure_id != figure_key:
            findings.append(
                _finding(
                    "figure_id_mismatch",
                    figure=str(figure_key),
                    declared_figure_id=figure_id,
                )
            )
        if not isinstance(role_id, str) or not role_id.strip():
            findings.append(_finding("missing_role_id", figure=str(figure_key)))

        if status == PLANNED_MISSING_STATUS:
            if entry.get("fixture") or entry.get("source_pointer"):
                findings.append(
                    _finding("planned_missing_has_fixture", figure=str(figure_key))
                )
            findings.append(
                _finding(
                    "planned_figure_missing",
                    severity="advisory",
                    figure=str(figure_key),
                    state=PLANNED_MISSING_STATUS,
                    role_id=role_id,
                )
            )
            continue

        if status != ACTIVE_STATUS:
            findings.append(
                _finding(
                    "invalid_figure_status",
                    figure=str(figure_key),
                    status=status,
                )
            )
            continue

        fixture = entry.get("fixture")
        if not isinstance(fixture, str) or not fixture:
            findings.append(_finding("active_figure_missing_fixture", figure=str(figure_key)))
            continue
        if fixture in claimed:
            findings.append(
                _finding(
                    "fixture_bound_multiple_times",
                    fixture=fixture,
                    figures=[claimed[fixture], str(figure_key)],
                )
            )
        claimed[fixture] = str(figure_key)
        fixture_dir = fixtures.get(fixture)
        if fixture_dir is None:
            findings.append(
                _finding("missing_mapped_fixture", figure=str(figure_key), fixture=fixture)
            )
            continue

        spec = _load_spec(fixture_dir / "spec.yaml")
        expected_binding = {
            "paper_id": paper_id,
            "figure_id": figure_id,
            "role_id": role_id,
        }
        if spec.get("paper_binding") != expected_binding:
            findings.append(
                _finding(
                    "paper_binding_mismatch",
                    figure=str(figure_key),
                    fixture=fixture,
                    expected=expected_binding,
                    actual=spec.get("paper_binding"),
                )
            )

        source_pointer = entry.get("source_pointer")
        if source_pointer is not None:
            if not isinstance(source_pointer, str) or not source_pointer:
                findings.append(_finding("invalid_source_pointer", fixture=fixture))
            else:
                findings.extend(
                    _validate_source_pointer(fixture_dir, fixture, source_pointer)
                )

    non_main = plan_map.get("non_main") or {}
    if not isinstance(non_main, dict):
        non_main = {}
        findings.append(_finding("invalid_non_main_mapping"))
    seen_non_main: set[str] = set()
    for classification, names in sorted(non_main.items()):
        if classification not in NON_MAIN_CLASSES:
            findings.append(
                _finding("invalid_non_main_class", classification=str(classification))
            )
        if not isinstance(names, list):
            findings.append(
                _finding("invalid_non_main_entries", classification=str(classification))
            )
            continue
        for raw_fixture in names:
            fixture = str(raw_fixture)
            if fixture in claimed and not claimed[fixture].startswith("non_main:"):
                findings.append(
                    _finding(
                        "fixture_has_main_and_non_main_binding",
                        fixture=fixture,
                        figure=claimed[fixture],
                        classification=str(classification),
                    )
                )
                continue
            if fixture in seen_non_main:
                findings.append(
                    _finding("duplicate_non_main_fixture", fixture=fixture)
                )
                continue
            seen_non_main.add(fixture)
            claimed[fixture] = f"non_main:{classification}"
            if fixture not in fixtures:
                findings.append(
                    _finding(
                        "missing_mapped_fixture",
                        fixture=fixture,
                        classification=str(classification),
                    )
                )
            else:
                findings.append(
                    _finding(
                        "non_main_fixture",
                        severity="advisory",
                        fixture=fixture,
                        classification=str(classification),
                    )
                )

    for fixture in sorted(set(fixtures) - set(claimed)):
        findings.append(_finding("unmapped_fixture", fixture=fixture))

    exemptions = plan_map.get("non_fixture_artifacts") or []
    exempted: set[str] = set()
    if not isinstance(exemptions, list):
        exemptions = []
        findings.append(_finding("invalid_non_fixture_artifact_registry"))
    for entry in exemptions:
        if not isinstance(entry, dict):
            findings.append(_finding("invalid_non_fixture_artifact_entry"))
            continue
        directory = entry.get("directory")
        classification = entry.get("classification")
        scope = entry.get("scope")
        rationale = entry.get("rationale")
        if (
            not isinstance(directory, str)
            or not directory
            or Path(directory).name != directory
            or directory.startswith("_")
        ):
            findings.append(
                _finding("invalid_non_fixture_artifact_directory", directory=directory)
            )
            continue
        if directory in exempted:
            findings.append(
                _finding("duplicate_non_fixture_artifact", directory=directory)
            )
            continue
        exempted.add(directory)
        if classification not in NON_FIXTURE_CLASSES:
            findings.append(
                _finding(
                    "invalid_non_fixture_artifact_class",
                    directory=directory,
                    classification=classification,
                )
            )
        if not isinstance(scope, str) or not scope.strip():
            findings.append(
                _finding("missing_non_fixture_artifact_scope", directory=directory)
            )
        if not isinstance(rationale, str) or not rationale.strip():
            findings.append(
                _finding("missing_non_fixture_artifact_rationale", directory=directory)
            )
        if directory not in example_dirs:
            findings.append(
                _finding("stale_non_fixture_artifact", directory=directory)
            )
        elif directory in fixtures:
            findings.append(
                _finding("non_fixture_artifact_has_spec", directory=directory)
            )
        else:
            findings.append(
                _finding(
                    "non_fixture_artifact",
                    severity="advisory",
                    directory=directory,
                    classification=classification,
                )
            )

    spec_less = set(example_dirs) - set(fixtures)
    for directory in sorted(spec_less - exempted):
        findings.append(
            _finding("unclassified_spec_less_example", directory=directory)
        )

    blocking_count = sum(item["severity"] == "blocking" for item in findings)
    advisory_count = sum(item["severity"] == "advisory" for item in findings)
    return {
        "schema": REPORT_SCHEMA,
        "map_schema": MAP_SCHEMA,
        "paper_id": paper_id,
        "examples_dir": str(examples_dir),
        "map_path": str(map_path),
        "blocking_count": blocking_count,
        "advisory_count": advisory_count,
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
    return 1 if args.strict and report["blocking_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
