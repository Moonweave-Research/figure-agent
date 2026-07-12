from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "quality"))

from failure_ablation import FailureAblationError, evaluate_ablation


def _write_run(root: Path, variant: str, findings: list[dict[str, str]]) -> Path:
    path = root / f"{variant}.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.failure-ablation-run.v1",
                "variant": variant,
                "model_contract_hash": "sha256:" + "1" * 64,
                "input_packet_hash": "sha256:" + "2" * 64,
                "budget_contract_hash": "sha256:" + "3" * 64,
                "figure_family": "synthetic-ablation",
                "findings": findings,
                "human_correction_minutes": None,
                "intervention_count": 0,
                "clean_reproduction": True,
                "human_verdict": {"state": "pending"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def write_comparable_runs(root: Path) -> dict[str, Path]:
    typography = {
        "id": "TYPO001",
        "failure_class": "typography",
        "review_outcome": "confirmed_defect",
    }
    return {
        "raw": _write_run(root, "raw", [typography]),
        "verified": _write_run(root, "verified", [typography]),
        "repaired": _write_run(root, "repaired", []),
    }


def add_generation_receipt(path: Path, *, model_id: str = "test-model") -> None:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    transcript = {
        "model_id": model_id,
        "input_packet_sha256": payload["input_packet_hash"],
        "budget_contract_sha256": payload["budget_contract_hash"],
        "source_commit": "0123456789abcdef",
        "starting_artifact_sha256": "sha256:" + "4" * 64,
        "generated_artifact_sha256": "sha256:" + "5" * 64,
    }
    transcript_path = path.with_suffix(".transcript.json")
    transcript_bytes = json.dumps(transcript, sort_keys=True).encode("utf-8")
    transcript_path.write_bytes(transcript_bytes)
    payload["generation_receipt"] = {
        "schema": "figure-agent.generation-receipt.v1",
        **transcript,
        "transcript_path": transcript_path.name,
        "transcript_sha256": "sha256:" + hashlib.sha256(transcript_bytes).hexdigest(),
    }
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_ablation_requires_exactly_raw_verified_repaired(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    paths.pop("repaired")
    with pytest.raises(FailureAblationError, match="variant_set_invalid"):
        evaluate_ablation(paths)


def test_ablation_rejects_mismatched_model_input_or_budget(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    payload = yaml.safe_load(paths["verified"].read_text(encoding="utf-8"))
    payload["model_contract_hash"] = "sha256:" + "9" * 64
    paths["verified"].write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(FailureAblationError, match="comparison_contract_mismatch"):
        evaluate_ablation(paths)


def test_scientific_failure_cannot_be_compensated_by_visual_improvement(
    tmp_path: Path,
) -> None:
    paths = write_comparable_runs(tmp_path)
    payload = yaml.safe_load(paths["repaired"].read_text(encoding="utf-8"))
    payload["findings"].append(
        {
            "id": "SEM001",
            "failure_class": "semantic",
            "review_outcome": "confirmed_defect",
        }
    )
    paths["repaired"].write_text(yaml.safe_dump(payload), encoding="utf-8")
    report = evaluate_ablation(paths)
    assert report["variants"]["repaired"]["scientific_gate"] == "failed"
    assert report["product_claim"] == "not_authorized"


def test_reports_failure_reduction_without_claiming_acceptance(tmp_path: Path) -> None:
    report = evaluate_ablation(write_comparable_runs(tmp_path))
    assert report["schema"] == "figure-agent.failure-ablation-report.v1"
    assert report["deltas"]["verified_vs_raw"]["confirmed_defect_count"] <= 0
    assert report["deltas"]["repaired_vs_raw"]["confirmed_defect_count"] < 0
    assert report["publication_acceptance"] == "not_claimed"


def test_ablation_rejects_missing_comparison_contract(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    for path in paths.values():
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload.pop("input_packet_hash")
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(FailureAblationError, match="comparison_contract_mismatch"):
        evaluate_ablation(paths)


def test_recorded_human_verdict_requires_named_reviewer(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    for path in paths.values():
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload["human_verdict"] = {"state": "recorded"}
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    report = evaluate_ablation(paths)
    assert all(
        variant["human_verdict_state"] == "pending"
        for variant in report["variants"].values()
    )
    assert report["product_claim"] == "not_authorized"


def test_ablation_marks_manifests_without_bound_generation_receipts_as_staged(
    tmp_path: Path,
) -> None:
    report = evaluate_ablation(write_comparable_runs(tmp_path))

    assert report["comparison_evidence"] == "staged_only"


def test_ablation_accepts_runs_with_matching_generation_receipts(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    for path in paths.values():
        add_generation_receipt(path)

    report = evaluate_ablation(paths)

    assert report["comparison_evidence"] == "actual_generation_bound"


def test_ablation_rejects_generation_receipts_from_different_models(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    for variant, path in paths.items():
        add_generation_receipt(path, model_id=f"test-model-{variant}")

    report = evaluate_ablation(paths)

    assert report["comparison_evidence"] == "staged_only"


def test_ablation_requires_a_hash_bound_generation_transcript(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    for path in paths.values():
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload["generation_receipt"] = {
            "schema": "figure-agent.generation-receipt.v1",
            "model_id": "test-model",
            "input_packet_sha256": payload["input_packet_hash"],
            "budget_contract_sha256": payload["budget_contract_hash"],
            "source_commit": "0123456789abcdef",
            "starting_artifact_sha256": "sha256:" + "4" * 64,
            "generated_artifact_sha256": "sha256:" + "5" * 64,
        }
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    report = evaluate_ablation(paths)

    assert report["comparison_evidence"] == "staged_only"
