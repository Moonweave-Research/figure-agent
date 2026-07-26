from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

import check_plan_consistency  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _write_fixture(
    examples: Path,
    name: str,
    *,
    paper_id: str = "paper-demo",
    figure_id: str = "fig1",
    role_id: str = "role-demo",
) -> None:
    fixture = examples / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        yaml.safe_dump(
            {
                "name": name,
                "paper_binding": {
                    "paper_id": paper_id,
                    "figure_id": figure_id,
                    "role_id": role_id,
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_map(
    path: Path,
    *,
    fixture: str = "mapped",
    include_extra_classification: bool = True,
) -> None:
    non_main = {"regression": ["extra"]} if include_extra_classification else {}
    path.write_text(
        yaml.safe_dump(
            {
                "schema": check_plan_consistency.MAP_SCHEMA,
                "paper_id": "paper-demo",
                "plan_doc": "docs/plan.md",
                "figures": {
                    "fig1": {
                        "figure_id": "fig1",
                        "role_id": "role-demo",
                        "status": "active_candidate",
                        "fixture": fixture,
                    },
                    "fig2": {
                        "figure_id": "fig2",
                        "role_id": "planned-role",
                        "status": "planned_missing",
                    },
                },
                "non_main": non_main,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_plan_consistency_uses_exact_bindings_and_advisory_states(tmp_path: Path) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    _write_fixture(examples, "extra", figure_id="regression", role_id="regression")
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map)

    report = check_plan_consistency.build_report(examples, plan_map)
    advisories = {
        (finding["code"], finding.get("fixture"), finding.get("figure"))
        for finding in report["findings"]
        if finding["severity"] == "advisory"
    }

    assert report["blocking_count"] == 0
    assert ("planned_figure_missing", None, "fig2") in advisories
    assert ("non_main_fixture", "extra", None) in advisories
    assert report["schema"] == "figure-agent.plan-consistency.v2"


def test_plan_consistency_rejects_binding_mismatch_and_unmapped_fixture(
    tmp_path: Path,
) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped", role_id="wrong-role")
    _write_fixture(examples, "unmapped", figure_id="other", role_id="other")
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map, include_extra_classification=False)

    report = check_plan_consistency.build_report(examples, plan_map)
    blocking = {(item["code"], item.get("fixture")) for item in report["findings"]}

    assert ("paper_binding_mismatch", "mapped") in blocking
    assert ("unmapped_fixture", "unmapped") in blocking
    assert report["blocking_count"] == 2


def test_plan_consistency_resolves_declared_current_candidate_pointer(
    tmp_path: Path,
) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    pointer = examples / "mapped/review/current-candidate.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text(json.dumps({"fixture": "mapped"}), encoding="utf-8")
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map, include_extra_classification=False)
    payload = yaml.safe_load(plan_map.read_text(encoding="utf-8"))
    payload["figures"]["fig1"]["source_pointer"] = "review/current-candidate.json"
    plan_map.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    report = check_plan_consistency.build_report(examples, plan_map)

    assert report["blocking_count"] == 0


def test_plan_consistency_blocks_unclassified_spec_less_example(tmp_path: Path) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    (examples / "artifact_without_spec").mkdir(parents=True)
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map, include_extra_classification=False)

    report = check_plan_consistency.build_report(examples, plan_map)

    assert any(
        item["code"] == "unclassified_spec_less_example"
        and item["directory"] == "artifact_without_spec"
        and item["severity"] == "blocking"
        for item in report["findings"]
    )


def test_plan_consistency_allows_scoped_non_fixture_artifact(tmp_path: Path) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    (examples / "artifact_without_spec").mkdir(parents=True)
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map, include_extra_classification=False)
    payload = yaml.safe_load(plan_map.read_text(encoding="utf-8"))
    payload["non_fixture_artifacts"] = [
        {
            "directory": "artifact_without_spec",
            "classification": "experiment_evidence",
            "scope": "A bounded historical experiment packet",
            "rationale": "No source or compile contract exists, so this is not a fixture.",
        }
    ]
    plan_map.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    report = check_plan_consistency.build_report(examples, plan_map)

    assert report["blocking_count"] == 0
    assert any(
        item["code"] == "non_fixture_artifact"
        and item["directory"] == "artifact_without_spec"
        and item["severity"] == "advisory"
        for item in report["findings"]
    )


def test_real_plan_map_classifies_every_top_level_example_directory() -> None:
    report = check_plan_consistency.build_report(
        PLUGIN_ROOT / "examples",
        PLUGIN_ROOT / "docs" / "paper_figure_map.yaml",
    )

    assert report["blocking_count"] == 0
    exemptions = {
        item["directory"]
        for item in report["findings"]
        if item["code"] == "non_fixture_artifact"
    }
    assert exemptions == {
        "fig1_direct_svg_cleanroom_baseline",
        "fig1_panel_f_svg_backend_pilot",
    }


def test_fig_agent_plan_check_strict_allows_advisory_only_map(tmp_path: Path) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    _write_fixture(examples, "extra", figure_id="regression", role_id="regression")
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map)

    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "plan-check",
            "--strict",
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
    assert '"blocking_count": 0' in result.stdout
    assert "planned_figure_missing" in result.stdout


def test_fig_agent_plan_check_strict_blocks_unmapped_fixture(tmp_path: Path) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    _write_fixture(examples, "unmapped", figure_id="other", role_id="other")
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map, include_extra_classification=False)

    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "plan-check",
            "--strict",
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

    assert result.returncode == 1
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
    assert '"schema": "figure-agent.plan-consistency.v2"' in result.stdout
    assert str(PLUGIN_ROOT / "docs" / "paper_figure_map.yaml") in result.stdout
    assert str(PLUGIN_ROOT / "examples") in result.stdout
