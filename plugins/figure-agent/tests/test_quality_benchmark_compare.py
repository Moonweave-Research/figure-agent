from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_benchmark  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _run_payload(
    run_id: str,
    *,
    failures: list[str] | None = None,
    render_success_rate: float = 0.0,
    candidate_specific_rank_rate: float = 0.0,
    best_candidate_rank_basis: str = "candidate_specific",
    best_candidate_render_manifest_path: str = "",
) -> dict:
    failures = failures or []
    return {
        "schema": "figure-agent.quality-benchmark-run.v1",
        "run_id": run_id,
        "suite": "smoke",
        "fixture_count": 1,
        "results": [
            {
                "fixture": "candidate_demo",
                "status": "completed",
                "candidate_count": 1,
                "rendered_count": 0,
                "ranked_count": 1,
                "render_mode": "not_requested",
                "hard_gate_failures": failures,
                "best_candidate": "CAND001",
                "best_candidate_rank_basis": best_candidate_rank_basis,
                "best_candidate_render_manifest_path": best_candidate_render_manifest_path,
                "memory_prior_used": False,
                "metrics": {
                    "compile_success_rate": 1.0,
                    "render_success_rate": render_success_rate,
                    "candidate_specific_rank_rate": candidate_specific_rank_rate,
                    "new_blocker_count": len(failures),
                    "mean_rank_score": 0.5,
                },
            }
        ],
        "summary": {
            "completed": 1,
            "skipped": 0,
            "failed": 0,
            "regression_count": len(failures),
        },
        "writes": [],
    }


def _write_run(workspace: Path, run_id: str, payload: dict) -> Path:
    run_dir = workspace / ".scratch" / "figure-agent-benchmarks" / run_id
    run_dir.mkdir(parents=True)
    path = run_dir / "run.json"
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _run_cli(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), "python", str(FIG_AGENT), *args],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )


def test_benchmark_compare_identical_runs_has_no_regression(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    payload = _run_payload("BASE")
    _write_run(workspace, "BASE", payload)
    _write_run(workspace, "CAND", {**payload, "run_id": "CAND"})

    comparison = quality_benchmark.compare_benchmark_runs(
        "BASE",
        "CAND",
        workspace_root=workspace,
    )

    assert comparison["schema"] == "figure-agent.quality-benchmark-comparison.v1"
    assert comparison["summary"]["regression_count"] == 0
    assert comparison["fixture_comparisons"][0]["regressions"] == []


def test_benchmark_compare_reports_new_hard_gate_failure(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_run(workspace, "BASE", _run_payload("BASE"))
    _write_run(workspace, "CAND", _run_payload("CAND", failures=["CAND001"]))

    comparison = quality_benchmark.compare_benchmark_runs(
        "BASE",
        "CAND",
        workspace_root=workspace,
    )

    assert comparison["summary"]["regression_count"] == 1
    assert comparison["fixture_comparisons"][0]["regressions"] == [
        "new_hard_gate_failures:CAND001"
    ]


def test_benchmark_compare_reports_render_evidence_regression(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_run(
        workspace,
        "BASE",
        _run_payload(
            "BASE",
            render_success_rate=1.0,
            candidate_specific_rank_rate=1.0,
            best_candidate_rank_basis="candidate_specific_render",
            best_candidate_render_manifest_path="build/render/CAND001/manifest.json",
        ),
    )
    _write_run(
        workspace,
        "CAND",
        _run_payload(
            "CAND",
            render_success_rate=0.0,
            candidate_specific_rank_rate=0.0,
            best_candidate_rank_basis="candidate_specific",
            best_candidate_render_manifest_path="",
        ),
    )

    comparison = quality_benchmark.compare_benchmark_runs(
        "BASE",
        "CAND",
        workspace_root=workspace,
    )

    assert comparison["fixture_comparisons"][0]["regressions"] == [
        "render_success_rate_decreased",
        "candidate_specific_rank_rate_decreased",
        "best_candidate_render_evidence_missing",
    ]


def test_benchmark_compare_rejects_missing_run(tmp_path: Path) -> None:
    with pytest.raises(quality_benchmark.QualityBenchmarkError, match="benchmark_run_missing"):
        quality_benchmark.compare_benchmark_runs(
            "BASE",
            "CAND",
            workspace_root=tmp_path / "workspace",
        )


def test_benchmark_compare_rejects_path_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_run(workspace, "BASE", _run_payload("BASE"))

    with pytest.raises(quality_benchmark.QualityBenchmarkError, match="fixture name"):
        quality_benchmark.compare_benchmark_runs(
            "BASE",
            "../CAND",
            workspace_root=workspace,
        )


def test_fig_agent_benchmark_compare_cli(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    payload = _run_payload("BASE")
    _write_run(workspace, "BASE", payload)
    _write_run(workspace, "CAND", {**payload, "run_id": "CAND"})

    result = _run_cli(workspace, "benchmark-compare", "BASE", "CAND", "--json")

    assert result.returncode == 0, result.stderr
    comparison = json.loads(result.stdout)
    assert comparison["schema"] == "figure-agent.quality-benchmark-comparison.v1"
    assert comparison["summary"]["regression_count"] == 0
