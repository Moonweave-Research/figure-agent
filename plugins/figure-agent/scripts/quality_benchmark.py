"""Lightweight quality benchmark runner for figure-agent."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import candidate_generator
import candidate_rank
import fixture_identity
import quality_memory_index
import runtime_paths

LIST_SCHEMA = "figure-agent.quality-benchmark-list.v1"
RUN_SCHEMA = "figure-agent.quality-benchmark-run.v1"
COMPARE_SCHEMA = "figure-agent.quality-benchmark-comparison.v1"


class QualityBenchmarkError(ValueError):
    """Raised when benchmark execution would violate local safety boundaries."""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_id(suite: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{suite}"


def _forbidden_write_reason(path: Path) -> str | None:
    resolved = path.expanduser().resolve()
    parts = set(resolved.parts)
    if "CloudStorage" in parts or "Google Drive" in parts:
        return "cloud_storage_write_forbidden"
    if any(part.startswith("GoogleDrive") for part in resolved.parts):
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


def _load_suites(plugin_root: Path) -> dict[str, dict[str, Any]]:
    suites = quality_memory_index._load_quality_suites(plugin_root)  # type: ignore[attr-defined]
    return {
        suite: {"description": "", "fixtures": fixtures}
        for suite, fixtures in sorted(suites.items())
    }


def build_benchmark_list(*, plugin_root: Path | None = None) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(plugin_root=plugin_root)
    return {
        "schema": LIST_SCHEMA,
        "generated_at": _utc_now(),
        "suites": _load_suites(paths.plugin_root),
    }


def _status_summary(example_dir: Path) -> dict[str, Any]:
    try:
        import status

        payload = status.infer_stage(example_dir)
    except Exception as exc:  # noqa: BLE001 - benchmark should degrade into diagnostics.
        return {"state": "unavailable", "reason": str(exc)}
    return {
        "state": "available",
        "workflow_ready": bool(payload.get("workflow_ready")),
        "render_state": payload.get("render_state"),
        "export_state": payload.get("export_state"),
        "critique_state": payload.get("critique_state"),
    }


def _candidate_manifest_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    apply_authority = str(candidate.get("apply_authority") or "review_only")
    if apply_authority == "rejected":
        hard_gate_state = "rejected"
    elif apply_authority == "apply_eligible":
        hard_gate_state = "pass"
    else:
        hard_gate_state = "human_required"
    return {
        "candidate_id": str(candidate.get("id") or "unknown"),
        "apply_authority": apply_authority,
        "edit_class": candidate.get("edit_class"),
        "family": candidate.get("family"),
        "verification": {"hard_gate_state": hard_gate_state},
    }


def _load_fixture_memory_index(example_dir: Path) -> dict[str, Any] | None:
    build_dir = example_dir / "build"
    memory_dir = build_dir / "memory"
    output = memory_dir / "quality_memory_index.json"
    for path in (build_dir, memory_dir, output):
        if path.is_symlink():
            raise QualityBenchmarkError("sandbox_symlink_forbidden: memory_index")
    if not output.is_file():
        return None
    payload = json.loads(output.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QualityBenchmarkError("memory_index_invalid")
    return payload


def _run_fixture(
    fixture: str,
    *,
    paths: runtime_paths.RuntimePaths,
    render: bool,
) -> dict[str, Any]:
    example_dir = paths.examples_dir / fixture
    if not example_dir.is_dir():
        return {
            "fixture": fixture,
            "status": "skipped",
            "reason": "missing_fixture",
            "candidate_count": 0,
            "rendered_count": 0,
            "ranked_count": 0,
            "render_mode": "none",
            "hard_gate_failures": [],
            "best_candidate": None,
            "memory_prior_used": False,
            "metrics": {},
        }
    status_payload = _status_summary(example_dir)
    try:
        candidate_set = candidate_generator.build_candidate_set(
            fixture,
            plugin_root=paths.plugin_root,
            workspace_root=paths.workspace_root,
        )
        memory_index = _load_fixture_memory_index(example_dir)
        scores = []
        for candidate in candidate_set.get("candidates", []):
            if not isinstance(candidate, dict):
                continue
            score = candidate_rank.score_manifest(
                _candidate_manifest_from_candidate(candidate),
                candidate=candidate,
                memory_index=memory_index,
            )
            scores.append(score)
        scores.sort(key=lambda score: (-float(score["rank_score"]), str(score["candidate_id"])))
        hard_gate_failures = [
            str(score["candidate_id"])
            for score in scores
            if score.get("hard_gate_state") == "rejected"
        ]
        mean_rank = (
            round(sum(float(score["rank_score"]) for score in scores) / len(scores), 4)
            if scores
            else 0.0
        )
        return {
            "fixture": fixture,
            "status": "completed",
            "candidate_count": len(candidate_set.get("candidates", [])),
            "rendered_count": 0 if not render else 0,
            "ranked_count": len(scores),
            "render_mode": "none" if not render else "requested_not_implemented",
            "hard_gate_failures": hard_gate_failures,
            "best_candidate": scores[0]["candidate_id"] if scores else None,
            "memory_prior_used": memory_index is not None,
            "status_summary": status_payload,
            "metrics": {
                "compile_success_rate": 1.0 if status_payload.get("state") == "available" else 0.0,
                "render_success_rate": 0.0,
                "new_blocker_count": len(hard_gate_failures),
                "mean_rank_score": mean_rank,
            },
        }
    except Exception as exc:  # noqa: BLE001 - one fixture must not abort the suite.
        return {
            "fixture": fixture,
            "status": "failed",
            "reason": str(exc),
            "candidate_count": 0,
            "rendered_count": 0,
            "ranked_count": 0,
            "render_mode": "none",
            "hard_gate_failures": [],
            "best_candidate": None,
            "memory_prior_used": False,
            "metrics": {},
        }


def _ensure_run_output(workspace_root: Path, run_id: str) -> Path:
    fixture_identity.validate_fixture_name(run_id)
    scratch_root = workspace_root / ".scratch"
    benchmark_root = scratch_root / "figure-agent-benchmarks"
    run_dir = benchmark_root / run_id
    output = run_dir / "run.json"
    for label, path in (
        ("scratch", scratch_root),
        ("benchmark", benchmark_root),
        ("run", run_dir),
        ("output", output),
    ):
        if path.is_symlink():
            raise QualityBenchmarkError(f"sandbox_symlink_forbidden: {label}")
    reason = _forbidden_write_reason(output)
    if reason is not None:
        raise QualityBenchmarkError(reason)
    run_dir.mkdir(parents=True, exist_ok=False)
    return output


def _load_run(workspace_root: Path, run_id: str) -> dict[str, Any]:
    try:
        fixture_identity.validate_fixture_name(run_id)
    except ValueError as exc:
        raise QualityBenchmarkError(str(exc)) from exc
    scratch_root = workspace_root / ".scratch"
    benchmark_root = scratch_root / "figure-agent-benchmarks"
    run_dir = benchmark_root / run_id
    output = run_dir / "run.json"
    for label, path in (
        ("scratch", scratch_root),
        ("benchmark", benchmark_root),
        ("run", run_dir),
        ("output", output),
    ):
        if path.is_symlink():
            raise QualityBenchmarkError(f"sandbox_symlink_forbidden: {label}")
    if not output.is_file():
        raise QualityBenchmarkError(f"benchmark_run_missing: {run_id}")
    payload = json.loads(output.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QualityBenchmarkError(f"benchmark_run_invalid: {run_id}")
    return payload


def _result_by_fixture(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    results = run.get("results")
    if not isinstance(results, list):
        return {}
    mapped: dict[str, dict[str, Any]] = {}
    for result in results:
        if isinstance(result, dict) and isinstance(result.get("fixture"), str):
            mapped[result["fixture"]] = result
    return mapped


def _metric(result: dict[str, Any], key: str) -> float:
    metrics = result.get("metrics")
    if not isinstance(metrics, dict):
        return 0.0
    try:
        return float(metrics.get(key) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _compare_fixture(
    fixture: str,
    baseline: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    regressions: list[str] = []
    if baseline is None:
        regressions.append("new_fixture_without_baseline")
    if candidate is None:
        regressions.append("missing_candidate_fixture")
        return {
            "fixture": fixture,
            "baseline_status": baseline.get("status") if baseline else None,
            "candidate_status": None,
            "regressions": regressions,
        }
    baseline_failures = set(baseline.get("hard_gate_failures", []) if baseline else [])
    candidate_failures = set(candidate.get("hard_gate_failures", []))
    new_failures = sorted(candidate_failures - baseline_failures)
    if new_failures:
        regressions.append(f"new_hard_gate_failures:{','.join(new_failures)}")
    if (
        baseline
        and baseline.get("status") == "completed"
        and candidate.get("status") != "completed"
    ):
        regressions.append(f"status_regression:{candidate.get('status')}")
    if (
        not new_failures
        and _metric(candidate, "new_blocker_count") > _metric(baseline or {}, "new_blocker_count")
    ):
        regressions.append("new_blocker_count_increased")
    return {
        "fixture": fixture,
        "baseline_status": baseline.get("status") if baseline else None,
        "candidate_status": candidate.get("status"),
        "baseline_rank_score": _metric(baseline or {}, "mean_rank_score"),
        "candidate_rank_score": _metric(candidate, "mean_rank_score"),
        "regressions": regressions,
    }


def compare_benchmark_runs(
    baseline_run: str,
    candidate_run: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    baseline = _load_run(paths.workspace_root, baseline_run)
    candidate = _load_run(paths.workspace_root, candidate_run)
    baseline_results = _result_by_fixture(baseline)
    candidate_results = _result_by_fixture(candidate)
    fixtures = sorted(set(baseline_results) | set(candidate_results))
    comparisons = [
        _compare_fixture(
            fixture,
            baseline_results.get(fixture),
            candidate_results.get(fixture),
        )
        for fixture in fixtures
    ]
    regression_count = sum(len(item["regressions"]) for item in comparisons)
    return {
        "schema": COMPARE_SCHEMA,
        "generated_at": _utc_now(),
        "baseline_run": baseline_run,
        "candidate_run": candidate_run,
        "fixture_comparisons": comparisons,
        "summary": {
            "fixture_count": len(fixtures),
            "regression_count": regression_count,
        },
    }


def run_benchmark_suite(
    suite: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
    limit: int | None = None,
    render: bool = False,
    write: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(suite)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    suites = _load_suites(paths.plugin_root)
    if suite not in suites:
        raise QualityBenchmarkError(f"unknown_suite: {suite}")
    fixtures = list(suites[suite]["fixtures"])
    if limit is not None:
        fixtures = fixtures[:limit]
    run_id = run_id or _run_id(suite)
    results = [
        _run_fixture(fixture, paths=paths, render=render)
        for fixture in fixtures
    ]
    summary = {
        "completed": sum(1 for result in results if result["status"] == "completed"),
        "skipped": sum(1 for result in results if result["status"] == "skipped"),
        "failed": sum(1 for result in results if result["status"] == "failed"),
        "regression_count": sum(
            len(result.get("hard_gate_failures", []))
            for result in results
            if result["status"] == "completed"
        ),
    }
    payload = {
        "schema": RUN_SCHEMA,
        "run_id": run_id,
        "suite": suite,
        "generated_at": _utc_now(),
        "fixture_count": len(fixtures),
        "results": results,
        "summary": summary,
        "writes": [],
    }
    if write:
        output = _ensure_run_output(paths.workspace_root, run_id)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payload["writes"] = [
            f".scratch/figure-agent-benchmarks/{run_id}/run.json"
        ]
    return payload


def main(
    argv: list[str] | None = None,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="quality_benchmark.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--json", action="store_true")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--suite", required=True)
    run_parser.add_argument("--limit", type=int)
    run_parser.add_argument("--render", action="store_true")
    run_parser.add_argument("--write", action="store_true")
    run_parser.add_argument("--json", action="store_true")
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("baseline_run")
    compare_parser.add_argument("candidate_run")
    compare_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "list":
        payload = build_benchmark_list(plugin_root=plugin_root)
    elif args.command == "run":
        payload = run_benchmark_suite(
            args.suite,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
            limit=args.limit,
            render=args.render,
            write=args.write,
        )
    else:
        payload = compare_benchmark_runs(
            args.baseline_run,
            args.candidate_run,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
