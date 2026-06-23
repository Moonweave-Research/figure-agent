from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PLUGIN_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_ROOT))

import release_gate  # noqa: E402


def test_release_gate_targeted_tests_cover_composition_accept_apply_contracts() -> None:
    required = {
        "tests/test_composition_p6_acceptance.py",
        "tests/test_composition_p6_cli.py",
        "tests/test_composition_p7_apply.py",
        "tests/test_composition_p7_cli.py",
    }

    assert required <= set(release_gate.TARGETED_TESTS)


def _benchmark_payload(
    suite: str,
    *,
    failed: int = 0,
    regressions: int = 0,
    render_probe_state: str = "pass",
    render_mode: str = "rendered",
    refusal_count: int = 1,
) -> dict:
    refusals = (
        [{"code": "manual_review", "defect_id": "D1"}]
        if refusal_count
        else []
    )
    return {
        "run_id": f"TEST-{suite}",
        "suite": suite,
        "render_dependency_probe": {
            "state": render_probe_state,
            "tools": {},
            "missing": ["lualatex"] if render_probe_state == "fail" else [],
        },
        "summary": {
            "completed": 1,
            "skipped": 0,
            "failed": failed,
            "regression_count": regressions,
        },
        "results": [
            {
                "fixture": f"{suite}_fixture",
                "status": "completed",
                "render_mode": render_mode,
                "candidate_count": 1,
                "rendered_count": 1 if render_mode == "rendered" else 0,
                "ranked_count": 1,
                "rank_basis_counts": {render_mode: 1},
                "best_candidate": "CAND001",
                "scores": [
                    {
                        "candidate_id": "CAND001",
                        "rank_basis": "candidate_specific_render"
                        if render_mode == "rendered"
                        else render_mode,
                        "render_manifest_path": "build/candidates/CAND001/render_manifest.json"
                        if render_mode == "rendered"
                        else None,
                    }
                ],
                "candidate_refusals": refusals,
                "metrics": {
                    "refusal_count": refusal_count,
                    "render_success_rate": 1.0 if render_mode == "rendered" else 0.0,
                    "candidate_specific_rank_rate": 1.0 if render_mode == "rendered" else 0.0,
                },
            }
        ],
    }


def test_release_gate_runs_render_aware_smoke_and_dogfood_benchmarks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def fake_run_benchmark_suite(
        suite: str,
        *,
        plugin_root: Path,
        workspace_root: Path,
        render: bool = False,
    ) -> dict:
        calls.append(
            {
                "suite": suite,
                "plugin_root": plugin_root,
                "workspace_root": workspace_root,
                "render": render,
            }
        )
        return _benchmark_payload(suite)

    monkeypatch.setattr(
        release_gate.quality_benchmark,
        "run_benchmark_suite",
        fake_run_benchmark_suite,
    )

    smoke_step = release_gate._run_smoke_benchmark()
    dogfood_step = release_gate._run_dogfood_benchmark()

    assert smoke_step["state"] == "passed"
    assert dogfood_step["state"] == "passed"
    assert [call["suite"] for call in calls] == ["smoke", "dogfood"]
    assert all(call["render"] is True for call in calls)
    assert all(call["plugin_root"] == release_gate.PLUGIN_ROOT for call in calls)
    assert all(call["workspace_root"] == release_gate.PLUGIN_ROOT for call in calls)
    assert dogfood_step["details"]["render_dependency_probe"] == {
        "state": "pass",
        "tools": {},
        "missing": [],
    }
    assert dogfood_step["details"]["benchmark_results"] == [
        {
            "fixture": "dogfood_fixture",
            "status": "completed",
            "render_mode": "rendered",
            "candidate_count": 1,
            "rendered_count": 1,
            "ranked_count": 1,
            "best_candidate": "CAND001",
            "metrics": {
                "render_success_rate": 1.0,
                "candidate_specific_rank_rate": 1.0,
                "refusal_count": 1,
            },
            "rank_basis_counts": {"rendered": 1},
            "best_candidate_render_evidence": {
                "rank_basis": "candidate_specific_render",
                "render_manifest_path": "build/candidates/CAND001/render_manifest.json",
            },
        }
    ]
    assert dogfood_step["details"]["residual_refusals"] == [
        {
            "fixture": "dogfood_fixture",
            "refusal_count": 1,
            "refusals": [{"code": "manual_review", "defect_id": "D1"}],
        }
    ]


def test_release_gate_fails_dogfood_benchmark_with_hard_regression(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        release_gate.quality_benchmark,
        "run_benchmark_suite",
        lambda suite, **_kwargs: _benchmark_payload(suite, regressions=1),
    )

    step = release_gate._run_dogfood_benchmark()

    assert step["state"] == "failed"
    assert step["details"]["summary"]["regression_count"] == 1


def test_release_gate_surfaces_dependency_missing_render_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        release_gate.quality_benchmark,
        "run_benchmark_suite",
        lambda suite, **_kwargs: _benchmark_payload(
            suite,
            render_probe_state="fail",
            render_mode="dependency_missing",
            refusal_count=0,
        ),
    )

    step = release_gate._run_dogfood_benchmark()

    assert step["state"] == "passed"
    assert step["details"]["render_dependency_probe"]["state"] == "fail"
    assert step["details"]["benchmark_results"][0]["render_mode"] == "dependency_missing"
    assert step["details"]["benchmark_results"][0]["metrics"]["render_success_rate"] == 0.0
    assert step["details"]["residual_refusals"] == []


def test_release_gate_builds_and_audits_package_with_skipped_heavy_checks(tmp_path: Path) -> None:
    report = release_gate.run_release_gate(
        output_dir=tmp_path / "dist",
        max_mib=50,
        run_targeted_tests=False,
        run_full_pytest=False,
        run_ruff=False,
        run_claude_validate=False,
    )

    assert report["schema"] == release_gate.SCHEMA
    assert report["success"] is True
    assert Path(report["zip_path"]).is_file()
    assert report["package_size_mib"] < 50
    states = {step["name"]: step["state"] for step in report["steps"]}
    assert states["targeted_tests"] == "skipped"
    assert states["full_pytest"] == "skipped"
    assert states["ruff"] == "skipped"
    assert states["smoke_benchmark"] == "passed"
    assert states["dogfood_benchmark"] == "passed"
    assert states["smoke_detector_generation"] == "passed"
    assert states["benchmark_baseline"] == "warning"
    assert states["package_required_paths"] == "passed"
    assert states["package_smoke_fixtures"] == "passed"
    assert states["package_excluded_paths"] == "passed"
    assert states["package_audit"] == "passed"
    assert states["claude_validate_package"] == "skipped"
    assert states["claude_validate_marketplace"] == "skipped"
    package_audit = next(step for step in report["steps"] if step["name"] == "package_audit")
    assert "--clean" not in package_audit["command"]


def test_release_gate_cli_emits_json_report(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_ROOT / "release_gate.py"),
            "--output",
            str(tmp_path / "dist"),
            "--max-mib",
            "50",
            "--skip-targeted-tests",
            "--skip-full-pytest",
            "--skip-ruff",
            "--skip-claude-validate",
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == release_gate.SCHEMA
    assert payload["success"] is True
    assert Path(payload["zip_path"]).is_file()


def test_fig_agent_release_gate_helper_ignores_workspace_env(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(PLUGIN_ROOT)
    result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "helper",
            "release_gate.py",
            "--output",
            str(tmp_path / "dist"),
            "--max-mib",
            "50",
            "--skip-targeted-tests",
            "--skip-full-pytest",
            "--skip-ruff",
            "--skip-claude-validate",
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == release_gate.SCHEMA
    assert payload["success"] is True


def test_release_gate_zip_contains_release_gate_script(tmp_path: Path) -> None:
    report = release_gate.run_release_gate(
        output_dir=tmp_path / "dist",
        max_mib=50,
        run_targeted_tests=False,
        run_full_pytest=False,
        run_ruff=False,
        run_claude_validate=False,
    )

    import zipfile

    with zipfile.ZipFile(report["zip_path"]) as archive:
        names = set(archive.namelist())

    assert "scripts/release_gate.py" in names


def test_release_gate_reports_missing_required_package_path() -> None:
    names = {".mcp.json", "bin/fig-agent"}

    step = release_gate._verify_required_paths(names)

    assert step["state"] == "failed"
    assert ".claude-plugin/plugin.json" in step["details"]["missing"]
    assert "benchmarks/quality_suites.yaml" in step["details"]["missing"]


def test_release_gate_reports_missing_smoke_fixture_package_paths() -> None:
    names = {
        "benchmarks/quality_suites.yaml",
        "examples/smoke_label_overlap_demo/spec.yaml",
    }

    step = release_gate._verify_smoke_fixture_paths(names)

    assert step["state"] == "failed"
    assert "examples/smoke_label_overlap_demo/benchmark_contract.yaml" in (
        step["details"]["missing"]
    )


def test_release_gate_reports_missing_smoke_detector_report_package_paths() -> None:
    names = {
        "benchmarks/quality_suites.yaml",
        "examples/smoke_label_overlap_demo/spec.yaml",
        "examples/smoke_label_overlap_demo/briefing.md",
        "examples/smoke_label_overlap_demo/smoke_label_overlap_demo.tex",
        "examples/smoke_label_overlap_demo/benchmark_contract.yaml",
    }

    step = release_gate._verify_smoke_fixture_paths(names)

    assert step["state"] == "failed"
    assert "examples/smoke_label_overlap_demo/benchmark_reports/text_boundary.json" in (
        step["details"]["missing"]
    )


def test_release_gate_reports_excluded_package_paths() -> None:
    names = {
        ".mcp.json",
        "examples/fig1_overview_v2/spec.yaml",
        "examples/smoke_trap_demo/build/smoke_trap_demo.pdf",
        ".venv/bin/python",
    }

    step = release_gate._verify_excluded_paths(names)

    assert step["state"] == "failed"
    assert step["details"]["unexpected_count"] == 3


def test_fig_agent_helper_allowlist_includes_release_gate() -> None:
    fig_agent = (PLUGIN_ROOT / "bin" / "fig-agent").read_text(encoding="utf-8")

    assert '"release_gate.py"' in fig_agent
