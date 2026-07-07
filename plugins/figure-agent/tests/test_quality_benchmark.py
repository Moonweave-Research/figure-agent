from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_render  # noqa: E402
import quality_benchmark  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402

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


def _write_undeclared_candidate_defect(fixture: Path) -> None:
    build = fixture / "build"
    build.mkdir(exist_ok=True)
    (build / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "source_hashes": {
                    "examples/candidate_demo/candidate_demo.tex": file_sha256(
                        fixture / "candidate_demo.tex"
                    )
                },
                "candidates": [
                    {
                        "id": "UG001",
                        "recommended_action": "add_micro_defect",
                        "source_line": 1,
                        "panel": "C",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_undeclared_candidate_defects(fixture: Path, source_lines: list[int]) -> None:
    build = fixture / "build"
    build.mkdir(exist_ok=True)
    (build / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "source_hashes": {
                    "examples/candidate_demo/candidate_demo.tex": file_sha256(
                        fixture / "candidate_demo.tex"
                    )
                },
                "candidates": [
                    {
                        "id": f"UG{index:03d}",
                        "recommended_action": "add_micro_defect",
                        "source_line": source_line,
                        "panel": "C",
                    }
                    for index, source_line in enumerate(source_lines, start=1)
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_undeclared_candidate_defects_for_fixture(
    fixture: Path,
    *,
    fixture_name: str,
    source_relative_path: str,
    source_path: Path,
    source_lines: list[int],
    panel: str = "A",
) -> None:
    build = fixture / "build"
    build.mkdir(exist_ok=True)
    (build / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.undeclared-geometry.v1",
                "fixture": fixture_name,
                "source_hashes": {
                    source_relative_path: file_sha256(source_path),
                },
                "candidates": [
                    {
                        "id": f"UG{index:03d}",
                        "kind": "label_endpoint_near_miss",
                        "recommended_action": "add_micro_defect",
                        "source_line": source_line,
                        "nearest_text": "benchmark candidate",
                        "evidence": f"source line {source_line} is a temp benchmark defect",
                        "bbox_pt": [10.0, 20.0, 30.0, 20.0],
                        "distance_pt": 2.0,
                        "panel": panel,
                    }
                    for index, source_line in enumerate(source_lines, start=1)
                ],
                "total": len(source_lines),
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _stub_successful_candidate_render(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        if command[0] == "lualatex":
            (cwd / "render" / "candidate.pdf").write_bytes(b"%PDF-1.7\n")
        if command[0] == "pdftocairo":
            (cwd / "render" / "candidate.png").write_bytes(b"png")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(candidate_render, "_which", lambda name: f"/fake/{name}")
    monkeypatch.setattr(candidate_render, "_run_process", fake_run)


def _dogfood_fixture_with_checker_report(workspace: Path) -> Path:
    name = "fig1_overview_v2_pair_001_vault"
    source = PLUGIN_ROOT / "examples" / name
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    for relative in (
        "spec.yaml",
        "briefing.md",
        f"{name}.tex",
        "benchmark_contract.yaml",
    ):
        target = fixture / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((source / relative).read_text(encoding="utf-8"), encoding="utf-8")
    report = fixture / "build" / "text_boundary_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-boundary-clash.v1",
                "fixture": name,
                "total": 3,
            },
            sort_keys=True,
        )
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


def test_installed_dogfood_checker_report_feeds_detector_evaluation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _dogfood_fixture_with_checker_report(workspace)

    payload = quality_benchmark.run_benchmark_suite(
        "dogfood",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
        limit=1,
    )

    assert payload["summary"]["failed"] == 0
    result = payload["results"][0]
    assert result["fixture"] == "fig1_overview_v2_pair_001_vault"
    assert result["status"] == "completed"
    assert result["detector_evaluation"]["state"] == "passed"
    movement = result["detector_evaluation"]["movements"][0]
    assert movement["metric"] == "text_boundary.blocker_count"
    assert movement["baseline"] == movement["candidate"]


def test_dogfood_render_benchmark_exposes_attribution_or_refusal_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _dogfood_fixture_with_checker_report(workspace)
    fixture_name = fixture.name
    source_name = f"{fixture_name}.tex"
    _write_undeclared_candidate_defects_for_fixture(
        fixture,
        fixture_name=fixture_name,
        source_relative_path=f"examples/{fixture_name}/{source_name}",
        source_path=fixture / source_name,
        source_lines=[67, 68, 1],
    )
    _stub_successful_candidate_render(monkeypatch)

    payload = quality_benchmark.run_benchmark_suite(
        "dogfood",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
        limit=1,
        render=True,
    )

    result = payload["results"][0]
    assert result["fixture"] == fixture_name
    assert result["status"] == "completed"
    assert result["render_mode"] == "rendered"
    assert result["candidate_count"] == 2
    assert result["rendered_count"] == 2
    assert result["ranked_count"] == 2
    assert result["metrics"]["refusal_count"] == 1
    best_score = result["scores"][0]
    assert best_score["rank_basis"] == "candidate_specific_render"
    assert best_score["render_manifest_path"] == (
        f"build/candidates/{best_score['candidate_id']}/render_manifest.json"
    )
    assert "rendered_before_after_available" in best_score["evidence"]["positive"]
    attributed_score_count = sum(
        1
        for score in result["scores"]
        if isinstance(score.get("source_defect"), dict) and score["source_defect"].get("id")
    )
    refusal_details = result.get("candidate_refusals")
    assert attributed_score_count >= 2 or (
        result["metrics"]["refusal_count"] > 0
        and isinstance(refusal_details, list)
        and len(refusal_details) > 0
    )


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
    assert {
        result["fixture"]: result["candidate_count"]
        for result in payload["results"]
    } == {
        "smoke_label_overlap_demo": 1,
        "smoke_leader_line_demo": 1,
        "smoke_panel_spacing_demo": 1,
        "smoke_contrast_demo": 1,
        "smoke_annotation_box_demo": 1,
    }


def test_benchmark_run_preview_is_read_only_and_skips_missing_fixture(tmp_path: Path) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_undeclared_candidate_defect(fixture)
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
    assert payload["results"][0]["render_mode"] == "not_requested"
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
    _write_undeclared_candidate_defect(fixture)
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


def test_benchmark_render_with_stubbed_dependencies_reports_rendered(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_undeclared_candidate_defect(fixture)
    source_before = (fixture / "candidate_demo.tex").read_text(encoding="utf-8")
    _stub_successful_candidate_render(monkeypatch)

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
        limit=1,
        render=True,
    )

    rendered = json.dumps(payload)
    assert "requested_not_implemented" not in rendered
    assert payload["render_dependency_probe"]["state"] == "pass"
    result = payload["results"][0]
    assert result["render_mode"] == "rendered"
    assert result["candidate_count"] == 1
    assert result["rendered_count"] == 1
    assert result["ranked_count"] == 1
    assert result["metrics"]["render_success_rate"] == 1.0
    assert result["metrics"]["candidate_specific_rank_rate"] == 1.0
    assert result["rank_basis_counts"]["candidate_specific_render"] == 1
    assert result["scores"][0]["rank_basis"] == "candidate_specific_render"
    assert result["scores"][0]["render_manifest_path"] == (
        "build/candidates/CAND001/render_manifest.json"
    )
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == source_before
    assert not (fixture / "exports").exists()


def test_benchmark_render_dependency_missing_reports_dependency_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_undeclared_candidate_defect(fixture)
    monkeypatch.setattr(candidate_render, "_which", lambda _name: None)

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
        limit=1,
        render=True,
    )

    assert "requested_not_implemented" not in json.dumps(payload)
    assert payload["render_dependency_probe"]["state"] == "fail"
    result = payload["results"][0]
    assert result["render_mode"] == "dependency_missing"
    assert result["candidate_count"] == 1
    assert result["rendered_count"] == 0
    assert result["ranked_count"] == 1
    assert result["metrics"]["render_success_rate"] == 0.0
    assert result["metrics"]["candidate_specific_rank_rate"] == 0.0
    assert result["rank_basis_counts"]["dependency_missing"] == 1


def test_benchmark_render_missing_fixture_uses_blocked_mode_not_none(
    tmp_path: Path,
) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
        limit=1,
        render=True,
    )

    result = payload["results"][0]
    assert result["status"] == "skipped"
    assert result["render_mode"] == "blocked"
    assert "none" not in json.dumps(payload)


def test_benchmark_candidate_specific_rank_rate_counts_partial_render_basis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "\\node (label-a) at (0,0) {A};\n"
        "\\draw (1.0,2.0) -- (3.0,2.0) node[right] {S};\n",
        encoding="utf-8",
    )
    _write_undeclared_candidate_defects(fixture, [1, 2])
    _stub_successful_candidate_render(monkeypatch)
    original_render = candidate_render.render_candidate_set

    def render_only_first_candidate(*args, **kwargs):
        return original_render(*args, candidate_id="CAND001", **kwargs)

    monkeypatch.setattr(candidate_render, "render_candidate_set", render_only_first_candidate)

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
        limit=1,
        render=True,
    )

    result = payload["results"][0]
    assert result["candidate_count"] == 2
    assert result["rendered_count"] == 1
    assert result["ranked_count"] == 2
    assert result["render_mode"] == "blocked"
    assert result["rank_basis_counts"]["candidate_specific_render"] == 1
    assert result["rank_basis_counts"]["blocked"] == 1
    assert result["metrics"]["candidate_specific_rank_rate"] == 0.5


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


def test_benchmark_run_write_appends_trend_row(tmp_path: Path) -> None:
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
    trend = workspace / ".scratch" / "figure-agent-benchmarks" / "trends" / "smoke.jsonl"
    assert payload["writes"] == [
        ".scratch/figure-agent-benchmarks/RUN001/run.json",
        ".scratch/figure-agent-benchmarks/trends/smoke.jsonl",
    ]
    assert output.is_file()
    assert trend.is_file()
    trend_rows = [json.loads(line) for line in trend.read_text(encoding="utf-8").splitlines()]
    assert trend_rows[0]["run_id"] == "RUN001"
    assert trend_rows[0]["capability_metrics"]["completed_rate"] == 0.5
    files = [
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file()
    ]
    assert ".scratch/figure-agent-benchmarks/RUN001/run.json" in files
    assert ".scratch/figure-agent-benchmarks/trends/smoke.jsonl" in files
    assert "examples/candidate_demo/build/candidates/candidate_set.json" not in files


def test_benchmark_run_trend_regression_emits_tool_defect(tmp_path: Path) -> None:
    plugin_root = _plugin_root(tmp_path)
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    trend = workspace / ".scratch" / "figure-agent-benchmarks" / "trends" / "smoke.jsonl"
    trend.parent.mkdir(parents=True)
    trend.write_text(
        json.dumps(
            {
                "schema": "figure-agent.quality-benchmark-trend.v1",
                "run_id": "BASELINE",
                "suite": "smoke",
                "capability_metrics": {
                    "completed_rate": 0.5,
                    "candidate_specific_rank_rate": 1.0,
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = quality_benchmark.run_benchmark_suite(
        "smoke",
        plugin_root=plugin_root,
        workspace_root=workspace,
        write=True,
        run_id="RUN002",
    )

    defects = payload["tool_defect_candidates"]
    assert defects
    assert defects[0]["symptom"] == "benchmark loop capability regressed"
    assert defects[0]["actual_behavior"]["metric"] == "candidate_specific_rank_rate"
    assert defects[0]["actual_behavior"]["previous"] == 1.0
    assert defects[0]["actual_behavior"]["current"] == 0.0
    assert len(trend.read_text(encoding="utf-8").splitlines()) == 2


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
