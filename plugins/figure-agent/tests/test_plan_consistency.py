from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

import check_plan_consistency  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]



def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write_fixture(
    examples: Path,
    name: str,
    *,
    paper_id: str = "paper-demo",
    figure_id: str = "fig1",
    role_id: str = "role-demo",
    paper_aesthetic_context: str | None = None,
) -> None:
    fixture = examples / name
    fixture.mkdir(parents=True)
    spec = {
        "name": name,
        "paper_binding": {
            "paper_id": paper_id,
            "figure_id": figure_id,
            "role_id": role_id,
        },
    }
    if paper_aesthetic_context is not None:
        spec["paper_aesthetic_context"] = paper_aesthetic_context
    (fixture / "spec.yaml").write_text(
        yaml.safe_dump(spec, sort_keys=False),
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


def test_plan_consistency_binds_named_schematic_baseline_to_active_context(
    tmp_path: Path,
) -> None:
    examples = tmp_path / "examples"
    context = "paper-series"
    _write_fixture(examples, "mapped", paper_aesthetic_context=context)
    context_path = examples / "_paper_aesthetic_contexts" / f"{context}.yaml"
    context_path.parent.mkdir()
    context_path.write_text("schema: placeholder\n", encoding="utf-8")
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map, include_extra_classification=False)
    payload = yaml.safe_load(plan_map.read_text(encoding="utf-8"))
    payload["current_schematic_baseline"] = {
        "id": "paper-main-schematics",
        "aesthetic_context": context,
        "fixtures": ["mapped"],
    }
    plan_map.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    report = check_plan_consistency.build_report(examples, plan_map)

    assert report["blocking_count"] == 0

    payload["current_schematic_baseline"]["fixtures"] = ["mapped", "nonexistent"]
    plan_map.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    invalid = check_plan_consistency.build_report(examples, plan_map)

    assert any(
        finding["code"] == "current_schematic_baseline_active_fixture_mismatch"
        and finding["severity"] == "blocking"
        for finding in invalid["findings"]
    )


def test_plan_consistency_resolves_declared_current_candidate_pointer(
    tmp_path: Path,
) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    candidate_root = examples / "mapped/review/candidate"
    candidate_root.mkdir(parents=True)
    (candidate_root / "repaired.tex").write_text("% candidate\n", encoding="utf-8")
    pointer = examples / "mapped/review/current-candidate.json"
    pointer.write_text(
        json.dumps(
            {
                "schema": "figure-agent.current-candidate-pointer.v1",
                "fixture": "mapped",
                "candidate_id": "candidate-1",
                "candidate_root": "review/candidate",
                "source_path": "repaired.tex",
                "source_sha256": _sha256_file(candidate_root / "repaired.tex"),
                "evidence": {
                    "render_pdf": "build/repaired.pdf",
                    "render_png": "build/repaired.png",
                    "strict_status": "build/strict_status.json",
                    "physics_grounding": "build/physics_grounding.json",
                    "text_boundary_clash": "build/text_boundary_clash.json",
                    "label_path_proximity": "build/label_path_proximity.json",
                },
            }
        ),
        encoding="utf-8",
    )
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map, include_extra_classification=False)
    payload = yaml.safe_load(plan_map.read_text(encoding="utf-8"))
    payload["figures"]["fig1"]["source_pointer"] = "review/current-candidate.json"
    plan_map.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    report = check_plan_consistency.build_report(examples, plan_map)

    assert report["blocking_count"] == 0


def test_plan_consistency_rejects_invalid_current_candidate_pointer_schema(
    tmp_path: Path,
) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    pointer = examples / "mapped/review/current-candidate.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text(json.dumps({"schema": "wrong", "fixture": "mapped"}), encoding="utf-8")
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map, include_extra_classification=False)
    payload = yaml.safe_load(plan_map.read_text(encoding="utf-8"))
    payload["figures"]["fig1"]["source_pointer"] = "review/current-candidate.json"
    plan_map.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    report = check_plan_consistency.build_report(examples, plan_map)

    assert report["blocking_count"] == 1
    assert any(
        finding["code"] == "invalid_source_pointer_schema"
        and finding["fixture"] == "mapped"
        for finding in report["findings"]
    )


def test_plan_consistency_rejects_current_candidate_source_hash_mismatch(
    tmp_path: Path,
) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    candidate_root = examples / "mapped/review/candidate"
    candidate_root.mkdir(parents=True)
    (candidate_root / "repaired.tex").write_text("% candidate\n", encoding="utf-8")
    pointer = examples / "mapped/review/current-candidate.json"
    pointer.write_text(
        json.dumps(
            {
                "schema": "figure-agent.current-candidate-pointer.v1",
                "fixture": "mapped",
                "candidate_root": "review/candidate",
                "source_path": "repaired.tex",
                "source_sha256": "sha256:" + "0" * 64,
                "evidence": {
                    "render_pdf": "build/repaired.pdf",
                    "render_png": "build/repaired.png",
                    "strict_status": "build/strict_status.json",
                    "physics_grounding": "build/physics_grounding.json",
                    "text_boundary_clash": "build/text_boundary_clash.json",
                    "label_path_proximity": "build/label_path_proximity.json",
                },
            }
        ),
        encoding="utf-8",
    )
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map, include_extra_classification=False)
    payload = yaml.safe_load(plan_map.read_text(encoding="utf-8"))
    payload["figures"]["fig1"]["source_pointer"] = "review/current-candidate.json"
    plan_map.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    report = check_plan_consistency.build_report(examples, plan_map)

    assert report["blocking_count"] == 1
    assert any(
        finding["code"] == "invalid_current_candidate_pointer"
        and finding["fixture"] == "mapped"
        for finding in report["findings"]
    )


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

    # Scoped to classification. Blocking findings of other codes are this
    # checker's job to report, not a reason to disable the coverage check.
    classification_codes = {
        "unclassified_spec_less_example",
        "unmapped_fixture",
        "missing_mapped_fixture",
        "stale_non_fixture_artifact",
        "non_fixture_artifact_has_spec",
    }
    assert not [
        item for item in report["findings"] if item["code"] in classification_codes
    ]
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


def test_non_main_fixture_may_not_declare_a_main_slot_binding(tmp_path: Path) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    # Declares the slot role the map assigns to fig2, while the map classifies
    # this fixture as superseded. Nothing in the fixture says it is retired.
    _write_fixture(examples, "extra", figure_id="fig2", role_id="planned-role")
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map)

    report = check_plan_consistency.build_report(examples, plan_map)
    blocking = [item for item in report["findings"] if item["severity"] == "blocking"]

    assert report["blocking_count"] == 1
    assert blocking[0] == {
        "code": "non_main_fixture_declares_slot_binding",
        "severity": "blocking",
        "fixture": "extra",
        "slot": "fig2",
        "classification": "regression",
        "declared_role_id": "planned-role",
        "slot_role_id": "planned-role",
        "slot_status": None,
    }


def test_non_main_fixture_without_a_slot_binding_stays_advisory(tmp_path: Path) -> None:
    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    _write_fixture(examples, "extra", figure_id="regression", role_id="regression")
    plan_map = tmp_path / "paper_figure_map.yaml"
    _write_map(plan_map)

    report = check_plan_consistency.build_report(examples, plan_map)

    assert report["blocking_count"] == 0


def test_real_tree_reports_the_two_open_non_main_slot_bindings() -> None:
    report = check_plan_consistency.build_report(
        PLUGIN_ROOT / "examples",
        PLUGIN_ROOT / "docs" / "paper_figure_map.yaml",
    )
    declared = {
        (item["fixture"], item["slot"], item["classification"])
        for item in report["findings"]
        if item["code"] == "non_main_fixture_declares_slot_binding"
    }

    # The fixtures' spec.yaml is the author's to change; the checker's job is
    # to stop reporting blocking_count 0 while these bindings stand.
    assert declared == {
        ("fig3_resistance_mechanism", "fig3", "regression"),
        ("fig4_trap_energy_diagram", "fig4", "superseded"),
    }


def test_plan_consistency_strict_runs_with_default_relative_arguments(
    tmp_path: Path,
) -> None:
    # A relative --examples-dir used to raise ValueError out of
    # current_candidate.resolve_current_candidate before any finding was built.
    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(PLUGIN_ROOT / "scripts" / "checks" / "check_plan_consistency.py"),
            "--strict",
        ],
        cwd=PLUGIN_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert "Traceback" not in result.stderr, result.stderr
    report = json.loads(result.stdout)
    assert report["schema"] == "figure-agent.plan-consistency.v2"
    assert result.returncode == (1 if report["blocking_count"] else 0)


def test_resolve_current_candidate_accepts_a_relative_example_dir(
    tmp_path: Path, monkeypatch
) -> None:
    sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
    import current_candidate

    examples = tmp_path / "examples"
    _write_fixture(examples, "mapped")
    candidate_root = examples / "mapped/review/candidate"
    candidate_root.mkdir(parents=True)
    (candidate_root / "repaired.tex").write_text("% candidate\n", encoding="utf-8")
    (examples / "mapped/review/current-candidate.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.current-candidate-pointer.v1",
                "fixture": "mapped",
                "candidate_id": "candidate-1",
                "candidate_root": "review/candidate",
                "source_path": "repaired.tex",
                "source_sha256": _sha256_file(candidate_root / "repaired.tex"),
                "evidence": {"render_pdf": "build/repaired.pdf"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    resolved = current_candidate.resolve_current_candidate(Path("examples/mapped"))

    assert resolved["state"] == "VALID"
    assert resolved["candidate_root"] == "review/candidate"
