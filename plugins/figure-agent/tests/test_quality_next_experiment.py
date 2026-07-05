from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_next_experiment  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _write_suite(plugin_root: Path, fixtures: list[str]) -> None:
    suite_path = plugin_root / "benchmarks" / "quality_suites.yaml"
    suite_path.parent.mkdir(parents=True, exist_ok=True)
    suite_path.write_text(
        "schema: figure-agent.quality-benchmark-suites.v1\n"
        "suites:\n"
        "  smoke:\n"
        "    description: test smoke suite\n"
        "    fixtures:\n"
        + "".join(f"      - {fixture}\n" for fixture in fixtures),
        encoding="utf-8",
    )


def _experience_record(
    fixture: str,
    candidate_id: str,
    family: str,
    *,
    quality_movement: str,
) -> dict:
    return {
        "schema": "figure-agent.experience-record.v1",
        "record_id": f"sha256:{fixture}-{candidate_id}",
        "fixture": fixture,
        "created_at": "2026-06-08T00:00:00Z",
        "state": {
            "base_tex_hash": "sha256:" + "0" * 64,
            "target": {"panel": "F", "subregion_key": "sha256:" + "1" * 64},
            "pre_apply_defects": [],
            "critique_finding_id": None,
        },
        "action": {
            "candidate_id": candidate_id,
            "edit_family": family,
            "params": {"operations": []},
            "candidate_hash": "sha256:" + "2" * 64,
            "rank_score": 0.7,
            "rank": 1,
            "n_candidates": 1,
        },
        "outcome": {
            "pipeline_ok": True,
            "apply_status": "applied",
            "quality_movement": quality_movement,
            "verifiers": {},
            "detector_recheck": {},
            "pixel_delta": {"changed_pixel_ratio": 0.01},
            "human_label": None,
            "human_decision_kind": None,
        },
    }


def _write_experience(plugin_root: Path, fixture: str, records: list[dict]) -> None:
    log_path = plugin_root / "docs" / "experience-log" / f"{fixture}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _write_benchmark_contract(workspace_root: Path, fixture: str) -> None:
    fixture_dir = workspace_root / "examples" / fixture
    fixture_dir.mkdir(parents=True, exist_ok=True)
    (fixture_dir / "spec.yaml").write_text(
        f"""
name: {fixture}
panels:
  - id: A
    caption: Demo panel
""".lstrip(),
        encoding="utf-8",
    )
    (fixture_dir / f"{fixture}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    (fixture_dir / "benchmark_contract.yaml").write_text(
        f"""
schema: figure-agent.benchmark-contract.v1
fixture: {fixture}
defect_class: label_overlap
candidate_families:
  - label-repair
candidate_edit_classes:
  - label_offset
required_detectors: []
expected_movement: {{}}
hard_regressions:
  - source_compile_failure
reference_policy:
  kind: repo_authored_synthetic
  external_images_allowed: false
  golden_target_allowed: true
""".lstrip(),
        encoding="utf-8",
    )


def test_quality_next_experiment_selects_highest_uncertainty_fixture_family(
    tmp_path: Path,
) -> None:
    plugin_root = tmp_path / "plugin"
    workspace_root = tmp_path / "workspace"
    fixtures = ["alpha", "beta"]
    _write_suite(plugin_root, fixtures)
    for fixture in fixtures:
        (workspace_root / "examples" / fixture).mkdir(parents=True)
    _write_experience(
        plugin_root,
        "alpha",
        [
            _experience_record(
                "alpha",
                f"ALPHA{index}",
                "apparatus_strengthen",
                quality_movement="improved",
            )
            for index in range(4)
        ],
    )
    _write_experience(plugin_root, "beta", [])

    payload = quality_next_experiment.build_next_experiment(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )

    assert payload["schema"] == "figure-agent.quality-next-experiment.v1"
    assert payload["recommendation"]["kind"] == "fixture_family_uncertainty_probe"
    assert payload["recommendation"]["fixture"] == "beta"
    assert payload["recommendation"]["family"] == "hierarchy_rebalance"
    assert payload["recommendation"]["allowed"] is True
    command = payload["recommendation"]["command"]
    for forbidden in ("--write", "--apply", "--accept", "--overwrite", "--force"):
        assert forbidden not in command
    assert payload["recommendation"]["arm_uncertainty"] == 1.0
    assert payload["recommendation"]["reason_codes"] == [
        "highest_fixture_family_arm_uncertainty",
        "read_only_quality_search_preview",
    ]


def test_quality_next_experiment_routes_contract_fixture_to_benchmark_run(
    tmp_path: Path,
) -> None:
    plugin_root = tmp_path / "plugin"
    workspace_root = tmp_path / "workspace"
    _write_suite(plugin_root, ["contract_demo"])
    _write_benchmark_contract(workspace_root, "contract_demo")
    _write_experience(plugin_root, "contract_demo", [])

    payload = quality_next_experiment.build_next_experiment(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )

    assert payload["recommendation"]["kind"] == "contract_backed_benchmark_probe"
    assert payload["recommendation"]["command"] == "fig-agent benchmark-run --suite smoke --json"
    assert payload["recommendation"]["allowed"] is True
    assert payload["recommendation"]["reason_codes"] == [
        "highest_fixture_family_arm_uncertainty",
        "contract_backed_fixture_uses_benchmark_run",
    ]


def test_fig_agent_quality_next_experiment_cli(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(tmp_path / "workspace")

    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(FIG_AGENT),
            "quality-next-experiment",
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
    assert payload["schema"] == "figure-agent.quality-next-experiment.v1"
    assert payload["recommendation"]["reason_codes"]
