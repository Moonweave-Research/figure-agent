from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_benchmark  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
INVALID_CASES = Path(__file__).resolve().parent / "fixtures" / "visual_attribution"


def test_installed_visual_attribution_corpus_locks_reviewed_baseline() -> None:
    corpus = quality_benchmark.load_visual_attribution_corpus(PLUGIN_ROOT)

    assert corpus["schema"] == "figure-agent.visual-attribution-suite.v1"
    assert corpus["historical_evidence"]["review_status"] == "unreviewed_inventory"
    assert corpus["historical_evidence"]["finding_count"] == 46
    assert corpus["historical_evidence"]["source_binding_count"] == 0
    reviewed_evidence = corpus["reviewed_evidence"]
    assert {item["review_outcome"] for item in reviewed_evidence} == {
        "false_positive",
        "linked_defect",
    }
    assert all(item["authority"] == "reviewed_evidence_only" for item in reviewed_evidence)
    assert all(len(item["source_sha256"]) == 64 for item in reviewed_evidence)
    assert {item["detector_ref"] for item in reviewed_evidence} == {"VC009", "LP001"}
    assert corpus["baseline_metrics"] == {
        "finding_count": 4,
        "reviewed_true_positive_count": 3,
        "reviewed_false_positive_count": 1,
        "exact_attribution_rate": 0.25,
        "ambiguous_attribution_rate": 0.25,
        "unbound_attribution_rate": 0.5,
        "human_correction_minutes": None,
    }


def test_corpus_summary_ignores_fixture_names_and_absolute_coordinates() -> None:
    corpus = quality_benchmark.load_visual_attribution_corpus(PLUGIN_ROOT)
    cases = corpus["cases"]
    translated = copy.deepcopy(cases)
    for index, case in enumerate(translated):
        case["fixture"] = f"renamed_fixture_{index}"
        bbox = case["finding"]["bbox_px"]
        case["finding"]["bbox_px"] = [value + 1000 for value in bbox]

    assert quality_benchmark.summarize_visual_attribution_cases(translated) == (
        quality_benchmark.summarize_visual_attribution_cases(cases)
    )


@pytest.mark.parametrize(
    "fixture_name",
    ["fixture_specific_expected.yaml", "coordinate_specific_expected.yaml"],
)
def test_corpus_rejects_fixture_or_coordinate_specific_expected_state_rules(
    tmp_path: Path,
    fixture_name: str,
) -> None:
    plugin_root = tmp_path / "plugin"
    benchmarks = plugin_root / "benchmarks"
    benchmarks.mkdir(parents=True)
    payload = yaml.safe_load((INVALID_CASES / fixture_name).read_text(encoding="utf-8"))
    (benchmarks / "visual_attribution_suite.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(
        quality_benchmark.QualityBenchmarkError,
        match="fixture_specific_expectation_forbidden|coordinate_specific_expectation_forbidden",
    ):
        quality_benchmark.load_visual_attribution_corpus(plugin_root)


def test_visual_attribution_runs_as_machine_only_opt_in_benchmark() -> None:
    payload = quality_benchmark.run_benchmark_suite(
        "visual-attribution",
        plugin_root=PLUGIN_ROOT,
        workspace_root=PLUGIN_ROOT,
    )

    assert payload["schema"] == "figure-agent.quality-benchmark-run.v1"
    assert payload["suite"] == "visual-attribution"
    assert payload["suite_kind"] == "visual_attribution"
    assert payload["acceptance"] == "machine_valid_only"
    assert payload["summary"] == {
        "completed": 4,
        "skipped": 0,
        "failed": 0,
        "regression_count": 0,
    }
    assert payload["attribution_metrics"]["human_correction_minutes"] is None
    assert "publication" not in payload["acceptance"]
