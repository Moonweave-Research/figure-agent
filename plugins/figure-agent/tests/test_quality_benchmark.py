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


def _plugin_root(tmp_path: Path) -> Path:
    plugin_root = tmp_path / "plugin"
    (plugin_root / "benchmarks").mkdir(parents=True)
    (plugin_root / "benchmarks" / "quality_suites.yaml").write_text(
        "\n".join(
            [
                "schema: figure-agent.quality-benchmark-suites.v1",
                "suites:",
                "  smoke:",
                "    description: Test smoke suite.",
                "    fixtures:",
                "      - candidate_demo",
                "      - missing_demo",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return plugin_root


def _fixture(workspace: Path) -> Path:
    fixture = workspace / "examples" / "candidate_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        """
name: candidate_demo
panels:
  - id: C
    caption: Energy diagram
    bbox_pdf_cm: [0.0, 0.0, 1.0, 1.0]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "candidate_demo.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    (fixture / "benchmark_contract.yaml").write_text(
        """
schema: figure-agent.benchmark-contract.v1
fixture: candidate_demo
defect_class: label_overlap
candidate_families:
  - label-repair
candidate_edit_classes:
  - label_offset
required_detectors: []
expected_movement: {}
hard_regressions:
  - source_compile_failure
reference_policy:
  kind: repo_authored_synthetic
  external_images_allowed: false
  golden_target_allowed: true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return fixture


def _tree(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


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


def test_benchmark_list_reads_suite_manifest(tmp_path: Path) -> None:
    plugin_root = _plugin_root(tmp_path)

    payload = quality_benchmark.build_benchmark_list(plugin_root=plugin_root)

    assert payload["schema"] == "figure-agent.quality-benchmark-list.v1"
    assert payload["suites"]["smoke"]["fixtures"] == ["candidate_demo", "missing_demo"]


def test_installed_smoke_suite_has_five_contract_fixtures() -> None:
    payload = quality_benchmark.build_benchmark_list(plugin_root=PLUGIN_ROOT)
    smoke_fixtures = payload["suites"]["smoke"]["fixtures"]

    assert smoke_fixtures == [
        "smoke_label_overlap_demo",
        "smoke_leader_line_demo",
        "smoke_panel_spacing_demo",
        "smoke_contrast_demo",
        "smoke_annotation_box_demo",
    ]
    for fixture in smoke_fixtures:
        fixture_dir = PLUGIN_ROOT / "examples" / fixture
        assert (fixture_dir / "spec.yaml").is_file()
        assert (fixture_dir / "briefing.md").is_file()
        assert (fixture_dir / f"{fixture}.tex").is_file()
        assert (fixture_dir / "benchmark_contract.yaml").is_file()


def test_installed_smoke_suite_has_at_least_one_detector_contract() -> None:
    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=PLUGIN_ROOT,
        workspace_root=PLUGIN_ROOT,
    )

    detector_results = [
        result
        for result in payload["results"]
        if result.get("detector_evaluation", {}).get("state") == "passed"
    ]
    assert detector_results
    first = detector_results[0]["detector_evaluation"]["movements"][0]
    assert first["operator"] == "decrease_or_equal"
    assert first["candidate"] <= first["baseline"]


def test_installed_smoke_suite_all_fixtures_have_passing_detector_contracts() -> None:
    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=PLUGIN_ROOT,
        workspace_root=PLUGIN_ROOT,
    )

    states = {
        result["fixture"]: result.get("detector_evaluation", {}).get("state")
        for result in payload["results"]
    }

    assert states == {
        "smoke_label_overlap_demo": "passed",
        "smoke_leader_line_demo": "passed",
        "smoke_panel_spacing_demo": "passed",
        "smoke_contrast_demo": "passed",
        "smoke_annotation_box_demo": "passed",
    }


def test_benchmark_run_preview_is_read_only_and_skips_missing_fixture(tmp_path: Path) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    before = _tree(workspace)

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
        write=False,
    )

    assert payload["schema"] == "figure-agent.quality-benchmark-run.v1"
    assert payload["suite"] == "smoke"
    assert payload["summary"] == {"completed": 1, "skipped": 1, "failed": 0, "regression_count": 0}
    assert [result["status"] for result in payload["results"]] == ["completed", "skipped"]
    assert payload["results"][0]["render_mode"] == "none"
    assert payload["results"][0]["rendered_count"] == 0
    assert payload["results"][0]["candidate_count"] == 1
    assert payload["results"][0]["ranked_count"] == 1
    assert payload["results"][0]["contract"]["state"] == "present"
    assert payload["results"][1]["contract"]["state"] == "missing"
    assert payload["writes"] == []
    assert _tree(workspace) == before


def test_benchmark_run_evaluates_detector_movement_for_contract(tmp_path: Path) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "benchmark_contract.yaml").write_text(
        """
schema: figure-agent.benchmark-contract.v1
fixture: candidate_demo
defect_class: label_overlap
candidate_families:
  - label-repair
candidate_edit_classes:
  - label_offset
required_detectors:
  - text_boundary
detector_reports:
  text_boundary: build/reports/text_boundary.json
expected_movement:
  text_boundary.blocker_count: decrease_or_equal
hard_regressions:
  - source_compile_failure
reference_policy:
  kind: repo_authored_synthetic
  external_images_allowed: false
  golden_target_allowed: true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    report_dir = fixture / "build" / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "text_boundary.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "text_boundary.blocker_count": {
                        "baseline": 3,
                        "candidate": 1,
                    }
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
        limit=1,
    )

    result = payload["results"][0]
    assert result["detector_evaluation"]["state"] == "passed"
    assert result["detector_evaluation"]["movements"][0] == {
        "metric": "text_boundary.blocker_count",
        "baseline": 3.0,
        "candidate": 1.0,
        "operator": "decrease_or_equal",
        "state": "passed",
    }
    assert result["metrics"]["mean_rank_score"] == 0.65


def test_benchmark_run_fails_release_blocking_missing_detector_report(tmp_path: Path) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "benchmark_contract.yaml").write_text(
        """
schema: figure-agent.benchmark-contract.v1
fixture: candidate_demo
defect_class: label_overlap
candidate_families:
  - label-repair
candidate_edit_classes:
  - label_offset
required_detectors:
  - text_boundary
detector_reports:
  text_boundary: build/reports/text_boundary.json
expected_movement:
  text_boundary.blocker_count: decrease_or_equal
hard_regressions:
  - source_compile_failure
reference_policy:
  kind: repo_authored_synthetic
  external_images_allowed: false
  golden_target_allowed: true
""".strip()
        + "\n",
        encoding="utf-8",
    )

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
        limit=1,
    )

    assert payload["summary"] == {"completed": 0, "skipped": 0, "failed": 1, "regression_count": 0}
    result = payload["results"][0]
    assert result["status"] == "failed"
    assert result["reason"] == "required_detector_missing"
    assert result["detector_evaluation"]["state"] == "missing"


def test_benchmark_run_fails_release_blocking_detector_regression(tmp_path: Path) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "benchmark_contract.yaml").write_text(
        """
schema: figure-agent.benchmark-contract.v1
fixture: candidate_demo
defect_class: label_overlap
candidate_families:
  - label-repair
candidate_edit_classes:
  - label_offset
required_detectors:
  - text_boundary
detector_reports:
  text_boundary: build/reports/text_boundary.json
expected_movement:
  text_boundary.blocker_count: decrease_or_equal
hard_regressions:
  - source_compile_failure
reference_policy:
  kind: repo_authored_synthetic
  external_images_allowed: false
  golden_target_allowed: true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    report_dir = fixture / "build" / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "text_boundary.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "text_boundary.blocker_count": {
                        "baseline": 1,
                        "candidate": 3,
                    }
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
        limit=1,
    )

    assert payload["summary"] == {"completed": 0, "skipped": 0, "failed": 1, "regression_count": 0}
    result = payload["results"][0]
    assert result["status"] == "failed"
    assert result["reason"] == "expected_detector_movement_failed"
    assert result["detector_evaluation"]["state"] == "failed"


def test_benchmark_run_reports_malformed_contract_per_fixture(tmp_path: Path) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "benchmark_contract.yaml").write_text(
        """
schema: figure-agent.benchmark-contract.v1
fixture: candidate_demo
defect_class: label_overlap
candidate_families:
  - label_offset
candidate_edit_classes:
  - label_offset
required_detectors: []
expected_movement: {}
hard_regressions:
  - source_compile_failure
reference_policy:
  kind: repo_authored_synthetic
  external_images_allowed: false
  golden_target_allowed: true
""".strip()
        + "\n",
        encoding="utf-8",
    )

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
    )

    assert payload["summary"] == {"completed": 0, "skipped": 1, "failed": 1, "regression_count": 0}
    assert payload["results"][0]["status"] == "failed"
    assert payload["results"][0]["reason"].startswith("candidate_family_invalid")
    assert payload["results"][1]["status"] == "skipped"


def test_benchmark_run_write_writes_only_run_manifest(tmp_path: Path) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
        write=True,
        run_id="RUN001",
    )

    output = workspace / ".scratch" / "figure-agent-benchmarks" / "RUN001" / "run.json"
    assert payload["writes"] == [".scratch/figure-agent-benchmarks/RUN001/run.json"]
    assert output.is_file()
    files = [
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file()
    ]
    assert ".scratch/figure-agent-benchmarks/RUN001/run.json" in files
    assert "examples/candidate_demo/build/candidates/candidate_set.json" not in files


def test_benchmark_run_write_refuses_symlinked_run_dir(tmp_path: Path) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    outside = tmp_path / "outside"
    outside.mkdir()
    run_root = workspace / ".scratch" / "figure-agent-benchmarks"
    run_root.mkdir(parents=True)
    (run_root / "RUN001").symlink_to(outside)

    with pytest.raises(quality_benchmark.QualityBenchmarkError, match="sandbox_symlink"):
        quality_benchmark.run_benchmark_suite(
            "smoke",
            plugin_root=plugin_root,
            workspace_root=workspace,
            write=True,
            run_id="RUN001",
        )


def test_benchmark_run_limit_one_runs_one_fixture(tmp_path: Path) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
        limit=1,
    )

    assert len(payload["results"]) == 1
    assert payload["summary"] == {"completed": 1, "skipped": 0, "failed": 0, "regression_count": 0}


def test_fig_agent_benchmark_list_and_run_cli(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "smoke_label_overlap_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: smoke_label_overlap_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "smoke_label_overlap_demo.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )

    list_result = _run_cli(workspace, "benchmark-list", "--json")
    run_result = _run_cli(
        workspace,
        "benchmark-run",
        "--suite",
        "smoke",
        "--limit",
        "1",
        "--json",
    )

    assert list_result.returncode == 0, list_result.stderr
    assert run_result.returncode == 0, run_result.stderr
    assert "smoke" in json.loads(list_result.stdout)["suites"]
    payload = json.loads(run_result.stdout)
    assert payload["schema"] == "figure-agent.quality-benchmark-run.v1"
    assert payload["summary"]["completed"] == 1
    assert payload["writes"] == []
