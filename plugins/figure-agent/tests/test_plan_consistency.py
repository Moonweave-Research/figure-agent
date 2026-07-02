from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

import check_plan_consistency  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _write_fixture(examples: Path, name: str, briefing: str = "alpha beta\n") -> None:
    fixture = examples / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(f"name: {name}\n", encoding="utf-8")
    (fixture / "briefing.md").write_text(briefing, encoding="utf-8")


def test_plan_consistency_reports_unmapped_role_drift_and_non_main(
    tmp_path: Path,
) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped", "totally unrelated words\n")
    _write_fixture(examples, "extra", "extra fixture\n")
    _write_fixture(examples, "sandboxed", "sandbox fixture\n")
    plan_map = tmp_path / "paper_figure_map.yaml"
    plan_map.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.paper-figure-map.v1",
                "plan_doc": "docs/plan.md",
                "figures": {
                    "fig1": {
                        "fixtures": ["mapped"],
                        "role": "charge trapping mechanism",
                    }
                },
                "non_main": {"sandbox": ["sandboxed"]},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = check_plan_consistency.build_report(examples, plan_map)
    findings = {(finding["code"], finding.get("fixture")) for finding in report["findings"]}

    assert ("role_drift", "mapped") in findings
    assert ("unmapped_fixture", "extra") in findings
    assert ("non_main_fixture", "sandboxed") in findings


def test_plan_consistency_reports_missing_and_sandbox_states_from_synthetic_map(
    tmp_path: Path,
) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "sandboxed", "sandbox fixture\n")
    _write_fixture(examples, "superseded", "superseded fixture\n")
    plan_map = tmp_path / "paper_figure_map.yaml"
    plan_map.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.paper-figure-map.v1",
                "plan_doc": "docs/plan.md",
                "figures": {
                    "fig1": {
                        "fixtures": [],
                        "role": "missing figure",
                        "status": "missing",
                    },
                    "fig2": {
                        "fixtures": [],
                        "role": "sandbox figure",
                        "sandbox": ["sandboxed"],
                    },
                },
                "non_main": {"superseded": ["superseded"]},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    report = check_plan_consistency.build_report(examples, plan_map)
    findings = {
        (finding["code"], finding.get("figure"), finding.get("fixture"), finding.get("state"))
        for finding in report["findings"]
    }

    assert ("planned_figure_missing", "fig1", None, "missing") in findings
    assert ("non_main_fixture", None, "sandboxed", "sandbox") in findings
    assert ("non_main_fixture", None, "superseded", "superseded") in findings
    assert report["schema"] == "figure-agent.plan-consistency.v1"


def test_fig_agent_plan_check_is_report_only(tmp_path: Path) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "extra", "extra fixture\n")
    plan_map = tmp_path / "paper_figure_map.yaml"
    plan_map.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.paper-figure-map.v1",
                "plan_doc": "docs/plan.md",
                "figures": {},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "plan-check",
            "--examples-dir",
            str(examples),
            "--map",
            str(plan_map),
        ],
        cwd=PLUGIN_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "unmapped_fixture" in result.stdout


def test_fig_agent_plan_check_defaults_are_plugin_root_relative(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "plan-check",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert '"schema": "figure-agent.plan-consistency.v1"' in result.stdout
    assert str(PLUGIN_ROOT / "docs" / "paper_figure_map.yaml") in result.stdout
    assert str(PLUGIN_ROOT / "examples") in result.stdout
