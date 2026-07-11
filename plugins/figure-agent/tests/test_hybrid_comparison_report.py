from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "hybrid"))

from comparison_report import (  # noqa: E402
    ComparisonReportError,
    aggregate_review_input_hash,
    load_comparison_report,
    validate_comparison_report,
    validate_human_verdict_bindings,
)


def _report() -> dict:
    return {
        "schema": "figure-agent.hybrid-comparison.v1",
        "trial_id": "fig1-complex-panel",
        "protocol": {
            "predeclared": True,
            "same_clean_environment": True,
            "task_boundary": "render and diagnose the declared Panel C geometry",
            "accounting_categories": [
                "preparation",
                "failed_attempts",
                "detector_diagnosis",
                "rendering",
                "repair",
            ],
        },
        "variants": {
            "tikz_only": {"compile_exit": 0, "output_sha256": "sha256:" + "a" * 64},
            "hybrid": {"compile_exit": 0, "output_sha256": "sha256:" + "b" * 64},
        },
        "measurements": {
            "visual_quality": {"value": None, "missing_reason": "pending human review"},
            "scientific_fidelity": {"value": None, "missing_reason": "pending human review"},
            "source_edit_size": {"tikz_only": 10, "hybrid": 20},
            "correction_minutes": {
                "tikz_only": None,
                "hybrid": None,
                "missing_reason": "no predeclared timed run was captured",
            },
            "detector_findings": {"tikz_only": 1, "hybrid": 2},
            "actionable_attribution_rate": {
                "value": None,
                "missing_reason": "pending human adjudication",
            },
            "artifact_reproducibility": {"tikz_only": True, "hybrid": True},
        },
        "verdicts": {
            "scaffold": {
                "status": "pending",
                "review_input_hash": "sha256:" + "c" * 64,
            },
            "artifact": {
                "status": "pending",
                "review_input_hash": "sha256:" + "c" * 64,
            },
        },
        "review_state": "review-ready",
        "publication_acceptance": "not_claimed",
    }


def test_accepts_review_ready_report_with_explicit_missing_measurements() -> None:
    result = validate_comparison_report(_report())
    assert result["review_state"] == "review-ready"


def test_rejects_selectively_trimmed_cost_accounting() -> None:
    report = _report()
    report["protocol"]["accounting_categories"].remove("failed_attempts")
    with pytest.raises(ComparisonReportError, match="accounting_categories"):
        validate_comparison_report(report)


def test_rejects_machine_publication_acceptance() -> None:
    report = _report()
    report["publication_acceptance"] = "accepted"
    with pytest.raises(ComparisonReportError, match="publication_acceptance"):
        validate_comparison_report(report)


def test_requires_distinct_human_scaffold_and_artifact_verdicts() -> None:
    report = _report()
    del report["verdicts"]["artifact"]
    with pytest.raises(ComparisonReportError, match="artifact verdict"):
        validate_comparison_report(report)


def test_review_input_hash_is_order_independent_and_content_bound() -> None:
    inputs = [
        {"role": "artifact", "path": "a.png", "sha256": "sha256:" + "a" * 64},
        {"role": "manifest", "path": "m.json", "sha256": "sha256:" + "b" * 64},
    ]
    first = aggregate_review_input_hash(inputs, {"python": "3.12"})
    assert first == aggregate_review_input_hash(list(reversed(inputs)), {"python": "3.12"})
    assert first != aggregate_review_input_hash(inputs, {"python": "3.13"})


def test_committed_hybrid_comparison_report_passes_contract() -> None:
    report = load_comparison_report(
        PLUGIN_ROOT / "docs" / "trials" / "2026-07-11-hybrid-complex-panel-comparison.md"
    )
    assert report["verdicts"]["scaffold"]["status"] == "pending"
    assert report["verdicts"]["artifact"]["status"] == "pending"


def test_human_verdict_binding_becomes_stale_when_an_input_changes(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.png"
    artifact.write_bytes(b"first")

    sha = "sha256:" + hashlib.sha256(b"first").hexdigest()
    inputs = [{"role": "artifact", "path": "artifact.png", "sha256": sha}]
    toolchain = {"python": "3.12"}
    verdict = {
        "review_input_hash": aggregate_review_input_hash(inputs, toolchain),
        "bound_inputs": inputs,
        "toolchain": toolchain,
    }
    verdict_path = tmp_path / "verdict.yaml"
    verdict_path.write_text(yaml.safe_dump(verdict), encoding="utf-8")

    assert validate_human_verdict_bindings(verdict_path, tmp_path)["stale"] is False
    artifact.write_bytes(b"second")
    assert validate_human_verdict_bindings(verdict_path, tmp_path)["stale"] is True
