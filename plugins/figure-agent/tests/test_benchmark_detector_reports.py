from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"

sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import benchmark_detector_reports  # noqa: E402


def _tree(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _copy_smoke_fixture(workspace: Path, name: str = "smoke_label_overlap_demo") -> Path:
    source = PLUGIN_ROOT / "examples" / name
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    for relative in (
        "spec.yaml",
        "briefing.md",
        f"{name}.tex",
        "benchmark_contract.yaml",
        "benchmark_reports/text_boundary.json",
    ):
        target = fixture / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((source / relative).read_text(encoding="utf-8"), encoding="utf-8")
    return fixture


def test_smoke_detector_preview_returns_explicit_reports_without_writes() -> None:
    before = _tree(PLUGIN_ROOT / "examples" / "smoke_label_overlap_demo")

    payload = benchmark_detector_reports.build_detector_reports(
        "smoke_label_overlap_demo",
        suite="smoke",
        plugin_root=PLUGIN_ROOT,
        workspace_root=PLUGIN_ROOT,
        write=False,
    )

    assert payload["schema"] == "figure-agent.benchmark-detectors-preview.v1"
    assert payload["fixture"] == "smoke_label_overlap_demo"
    assert payload["suite"] == "smoke"
    assert payload["write_mode"] is False
    assert payload["writes"] == []
    assert payload["reports"][0]["detector"] == "text_boundary"
    assert payload["reports"][0]["state"] == "available"
    report = payload["reports"][0]["report"]
    assert report["schema"] == "figure-agent.benchmark-detector-report.v1"
    assert report["source"]["kind"] == "seed_report"
    assert report["metrics"]["text_boundary.blocker_count"] == {
        "baseline": 2.0,
        "candidate": 1.0,
    }
    assert _tree(PLUGIN_ROOT / "examples" / "smoke_label_overlap_demo") == before


def test_smoke_detector_write_stays_in_generated_report_dir(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _copy_smoke_fixture(workspace)

    payload = benchmark_detector_reports.build_detector_reports(
        "smoke_label_overlap_demo",
        suite="smoke",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
        write=True,
    )

    assert payload["writes"] == [
        "examples/smoke_label_overlap_demo/benchmark_reports/generated/text_boundary.json"
    ]
    output = (
        workspace
        / "examples"
        / "smoke_label_overlap_demo"
        / "benchmark_reports"
        / "generated"
        / "text_boundary.json"
    )
    assert output.is_file()
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["schema"] == "figure-agent.benchmark-detector-report.v1"


def test_detector_write_rejects_symlinked_report_dir(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _copy_smoke_fixture(workspace)
    outside = tmp_path / "outside"
    outside.mkdir()
    generated = fixture / "benchmark_reports" / "generated"
    generated.symlink_to(outside)

    with pytest.raises(
        benchmark_detector_reports.BenchmarkDetectorReportError,
        match="sandbox_symlink_forbidden",
    ):
        benchmark_detector_reports.build_detector_reports(
            "smoke_label_overlap_demo",
            suite="smoke",
            plugin_root=PLUGIN_ROOT,
            workspace_root=workspace,
            write=True,
        )


def test_dogfood_detector_preview_is_read_only_and_non_blocking() -> None:
    fixture = PLUGIN_ROOT / "examples" / "fig1_overview_v2_pair_001_vault"
    before = _tree(fixture)

    payload = benchmark_detector_reports.build_detector_reports(
        "fig1_overview_v2_pair_001_vault",
        suite="dogfood",
        plugin_root=PLUGIN_ROOT,
        workspace_root=PLUGIN_ROOT,
        write=False,
    )

    assert payload["fixture"] == "fig1_overview_v2_pair_001_vault"
    assert payload["suite"] == "dogfood"
    assert payload["write_mode"] is False
    assert payload["writes"] == []
    assert [(report["detector"], report["state"]) for report in payload["reports"]] == [
        ("text_boundary", "available")
    ]
    report = payload["reports"][0]["report"]
    assert report["source"]["kind"] == "checker_report"
    assert report["source"]["checker_schema"] == "figure-agent.text-boundary-clash.v1"
    assert report["metrics"]["text_boundary.blocker_count"]["baseline"] == (
        report["metrics"]["text_boundary.blocker_count"]["candidate"]
    )
    assert _tree(fixture) == before


def test_checker_total_report_adapts_to_benchmark_metric(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "checker_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: checker_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "checker_demo.tex").write_text("\\node at (0,0) {Demo};\n", encoding="utf-8")
    (fixture / "benchmark_contract.yaml").write_text(
        """
schema: figure-agent.benchmark-contract.v1
fixture: checker_demo
defect_class: label_overlap
candidate_families:
  - label-repair
candidate_edit_classes:
  - label_offset
required_detectors:
  - text_boundary
detector_reports:
  text_boundary: build/text_boundary_clash.json
expected_movement:
  text_boundary.blocker_count: decrease_or_equal
hard_regressions:
  - source_compile_failure
reference_policy:
  kind: user_owned_dogfood
  external_images_allowed: true
  golden_target_allowed: false
""".strip()
        + "\n",
        encoding="utf-8",
    )
    report = fixture / "build" / "text_boundary_clash.json"
    report.parent.mkdir()
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-boundary-clash.v1",
                "fixture": "checker_demo",
                "render_pdf": "build/checker_demo.pdf",
                "source": "spec.yaml:text_boundary_checks",
                "total": 3,
                "candidates": [{"id": "TB001"}, {"id": "TB002"}, {"id": "TB003"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = benchmark_detector_reports.build_detector_reports(
        "checker_demo",
        suite="dogfood",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    detector_report = payload["reports"][0]["report"]
    assert payload["reports"][0]["state"] == "available"
    assert detector_report["source"]["kind"] == "checker_report"
    assert detector_report["metrics"]["text_boundary.blocker_count"] == {
        "baseline": 3.0,
        "candidate": 3.0,
    }


def test_fig_agent_benchmark_detectors_cli_preview(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(PLUGIN_ROOT)

    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(FIG_AGENT),
            "benchmark-detectors",
            "smoke_label_overlap_demo",
            "--suite",
            "smoke",
            "--json",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.benchmark-detectors-preview.v1"
    assert payload["reports"][0]["state"] == "available"
