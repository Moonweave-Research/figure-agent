"""Generate benchmark detector report previews from fixture-local evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import benchmark_contracts
import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.benchmark-detectors-preview.v1"
REPORT_SCHEMA = "figure-agent.benchmark-detector-report.v1"


class BenchmarkDetectorReportError(ValueError):
    """Raised when detector report generation would violate safety boundaries."""


def _metric_value(report: dict[str, Any], metric: str, key: str) -> float | None:
    metrics = report.get("metrics")
    if isinstance(metrics, dict):
        metric_payload = metrics.get(metric)
        if isinstance(metric_payload, dict):
            try:
                return float(metric_payload.get(key))
            except (TypeError, ValueError):
                return None
    bucket = report.get(key)
    if isinstance(bucket, dict):
        try:
            return float(bucket.get(metric))
        except (TypeError, ValueError):
            return None
    return None


def _workspace_relative(path: Path, workspace_root: Path) -> str:
    return path.relative_to(workspace_root).as_posix()


def _forbidden_write_reason(path: Path) -> str | None:
    resolved = path.expanduser().resolve()
    if any(
        part == "CloudStorage"
        or part == "Google Drive"
        or part.startswith("GoogleDrive")
        for part in resolved.parts
    ):
        return "cloud_storage_write_forbidden"
    home = Path.home().resolve()
    try:
        relative = resolved.relative_to(home)
    except ValueError:
        return None
    if len(relative.parts) >= 2 and relative.parts[:2] == ("Library", "Caches"):
        return "home_cache_write_forbidden"
    if relative.parts and relative.parts[0] == ".cache":
        return "home_cache_write_forbidden"
    return None


def _ensure_fixture_local(path: Path, fixture_dir: Path, *, label: str) -> None:
    try:
        path.resolve().relative_to(fixture_dir.resolve())
    except ValueError as exc:
        raise BenchmarkDetectorReportError(f"{label}_path_escape") from exc


def _reject_symlink_chain(path: Path, fixture_dir: Path, *, label: str) -> None:
    current = path
    while True:
        if current.exists() or current.is_symlink():
            if current.is_symlink():
                raise BenchmarkDetectorReportError(f"sandbox_symlink_forbidden: {label}")
        if current == fixture_dir:
            break
        if current.parent == current:
            break
        current = current.parent


def _read_seed_report(
    fixture_dir: Path,
    report_rel: str,
    *,
    detector: str,
    expected_movement: dict[str, str],
) -> dict[str, Any]:
    report_path = fixture_dir / report_rel
    _ensure_fixture_local(report_path, fixture_dir, label="detector_report")
    if report_path.is_symlink():
        return {
            "detector": detector,
            "state": "artifact_missing",
            "diagnostics": [{"code": "detector_report_symlink", "path": report_rel}],
        }
    if not report_path.is_file():
        return {
            "detector": detector,
            "state": "artifact_missing",
            "diagnostics": [{"code": "detector_report_missing", "path": report_rel}],
        }
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "detector": detector,
            "state": "artifact_missing",
            "diagnostics": [{"code": "detector_report_invalid", "message": str(exc)}],
        }
    if not isinstance(payload, dict):
        return {
            "detector": detector,
            "state": "artifact_missing",
            "diagnostics": [{"code": "detector_report_invalid"}],
        }
    metrics: dict[str, dict[str, float]] = {}
    diagnostics: list[dict[str, Any]] = []
    for metric in sorted(expected_movement):
        if metric.split(".", 1)[0] != detector:
            continue
        baseline = _metric_value(payload, metric, "baseline")
        candidate = _metric_value(payload, metric, "candidate")
        if baseline is None or candidate is None:
            diagnostics.append({"code": "metric_missing", "metric": metric})
            continue
        metrics[metric] = {"baseline": baseline, "candidate": candidate}
    if not metrics:
        return {
            "detector": detector,
            "state": "artifact_missing",
            "diagnostics": diagnostics or [{"code": "detector_metric_missing"}],
        }
    return {
        "detector": detector,
        "state": "available",
        "report": {
            "schema": REPORT_SCHEMA,
            "fixture": fixture_dir.name,
            "detector": detector,
            "source": {
                "kind": "seed_report",
                "seed_report": report_rel,
            },
            "metrics": metrics,
            "diagnostics": [],
        },
    }


def _output_path(fixture_dir: Path, suite: str, detector: str) -> Path:
    if suite == "dogfood":
        return fixture_dir / "build" / "benchmark_reports" / f"{detector}.json"
    return fixture_dir / "benchmark_reports" / "generated" / f"{detector}.json"


def _write_report(
    report: dict[str, Any],
    *,
    fixture_dir: Path,
    workspace_root: Path,
    suite: str,
) -> str:
    detector = str(report["detector"])
    output = _output_path(fixture_dir, suite, detector)
    _reject_symlink_chain(output, fixture_dir, label="detector_output")
    _ensure_fixture_local(output, fixture_dir, label="detector_output")
    reason = _forbidden_write_reason(output)
    if reason is not None:
        raise BenchmarkDetectorReportError(reason)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report["report"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return _workspace_relative(output, workspace_root)


def build_detector_reports(
    name: str,
    *,
    suite: str = "smoke",
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Return detector report previews and optional fixture-local writes."""
    fixture_identity.validate_fixture_name(name)
    fixture_identity.validate_fixture_name(suite)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    fixture_dir = paths.examples_dir / name
    try:
        contract = benchmark_contracts.load_contract(
            name,
            plugin_root=paths.plugin_root,
            workspace_root=paths.workspace_root,
            suite_role=suite,
        )
    except benchmark_contracts.BenchmarkContractError as exc:
        return {
            "schema": SCHEMA,
            "fixture": name,
            "suite": suite,
            "write_mode": bool(write),
            "reports": [],
            "writes": [],
            "diagnostics": [{"code": "invalid_contract", "message": str(exc)}],
        }
    required = contract.get("required_detectors")
    required_detectors = required if isinstance(required, list) else []
    report_paths = contract.get("detector_reports")
    report_paths = report_paths if isinstance(report_paths, dict) else {}
    expected = contract.get("expected_movement")
    expected = expected if isinstance(expected, dict) else {}
    reports: list[dict[str, Any]] = []
    for detector_value in required_detectors:
        if not isinstance(detector_value, str):
            continue
        detector = detector_value
        report_rel = report_paths.get(detector)
        if not isinstance(report_rel, str):
            reports.append(
                {
                    "detector": detector,
                    "state": "artifact_missing",
                    "diagnostics": [{"code": "detector_report_path_missing"}],
                }
            )
            continue
        reports.append(
            _read_seed_report(
                fixture_dir,
                report_rel,
                detector=detector,
                expected_movement={str(k): str(v) for k, v in expected.items()},
            )
        )
    writes: list[str] = []
    if write:
        for report in reports:
            if report.get("state") != "available":
                continue
            writes.append(
                _write_report(
                    report,
                    fixture_dir=fixture_dir,
                    workspace_root=paths.workspace_root,
                    suite=suite,
                )
            )
    return {
        "schema": SCHEMA,
        "fixture": name,
        "suite": suite,
        "write_mode": bool(write),
        "reports": reports,
        "writes": writes,
        "diagnostics": [],
    }


def main(
    argv: list[str] | None = None,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--suite", default="smoke")
    parser.add_argument("--candidate-id")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    del args.candidate_id
    try:
        payload = build_detector_reports(
            args.name,
            suite=args.suite,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
            write=args.write,
        )
    except (ValueError, BenchmarkDetectorReportError) as exc:
        print(f"benchmark_detector_reports.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
