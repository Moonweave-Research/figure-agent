from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

RUN_SCHEMA = "figure-agent.failure-ablation-run.v1"
REPORT_SCHEMA = "figure-agent.failure-ablation-report.v1"
VARIANTS = {"raw", "verified", "repaired"}
SCIENTIFIC_CLASSES = {"semantic", "relation"}
GENERATION_RECEIPT_SCHEMA = "figure-agent.generation-receipt.v1"
COMPARISON_ELIGIBLE = "eligible_equal_input"


class FailureAblationError(ValueError):
    pass


def _load_run(path: Path, *, expected_variant: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise FailureAblationError("run_path_invalid")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != RUN_SCHEMA:
        raise FailureAblationError("run_schema_invalid")
    if payload.get("variant") != expected_variant:
        raise FailureAblationError("run_variant_invalid")
    findings = payload.get("findings")
    if not isinstance(findings, list) or any(
        not isinstance(item, dict)
        or (
            "occurrences" in item
            and (
                not isinstance(item["occurrences"], int)
                or isinstance(item["occurrences"], bool)
                or item["occurrences"] < 1
            )
        )
        for item in findings
    ):
        raise FailureAblationError("run_findings_invalid")
    payload["_run_path"] = path
    return payload


def _summarize_run(run: dict[str, Any]) -> dict[str, Any]:
    confirmed = [
        item
        for item in run["findings"]
        if item.get("review_outcome") == "confirmed_defect"
    ]
    class_counts = Counter(str(item.get("failure_class")) for item in confirmed)
    scientific_failed = any(
        item.get("failure_class") in SCIENTIFIC_CLASSES for item in confirmed
    )
    verdict = run.get("human_verdict")
    verdict_state = (
        "recorded"
        if (
            isinstance(verdict, dict)
            and verdict.get("state") == "recorded"
            and isinstance(verdict.get("reviewer"), str)
            and bool(verdict["reviewer"].strip())
        )
        else "pending"
    )
    verdict_decision = (
        str(verdict.get("decision"))
        if verdict_state == "recorded"
        and isinstance(verdict.get("decision"), str)
        and bool(verdict["decision"].strip())
        else "pending"
    )
    summary = {
        "confirmed_defect_count": len(confirmed),
        "confirmed_defect_occurrence_count": sum(
            item.get("occurrences", 1) for item in confirmed
        ),
        "confirmed_defect_counts": dict(sorted(class_counts.items())),
        "scientific_gate": "failed" if scientific_failed else "passed",
        "human_correction_minutes": run.get("human_correction_minutes"),
        "intervention_count": run.get("intervention_count"),
        "clean_reproduction": run.get("clean_reproduction") is True,
        "human_verdict_state": verdict_state,
    }
    if verdict_decision != "pending":
        summary["human_verdict_decision"] = verdict_decision
    return summary


def _delta(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in (
        "confirmed_defect_count",
        "confirmed_defect_occurrence_count",
        "human_correction_minutes",
        "intervention_count",
    ):
        current_value = current.get(key)
        baseline_value = baseline.get(key)
        if (
            isinstance(current_value, int | float)
            and not isinstance(current_value, bool)
            and isinstance(baseline_value, int | float)
            and not isinstance(baseline_value, bool)
        ):
            result[key] = current_value - baseline_value
        else:
            result[key] = None
    return result


def _has_bound_generation_receipt(run: dict[str, Any]) -> bool:
    """Return whether a run has a contract-bound, hash-verified transcript."""
    receipt = run.get("generation_receipt")
    if not isinstance(receipt, dict) or receipt.get("schema") != GENERATION_RECEIPT_SCHEMA:
        return False
    required = (
        "model_id",
        "source_commit",
        "starting_artifact_sha256",
        "generated_artifact_sha256",
    )
    if any(not isinstance(receipt.get(key), str) or not receipt[key] for key in required):
        return False
    if not (
        receipt.get("input_packet_sha256") == run.get("input_packet_hash")
        and receipt.get("budget_contract_sha256") == run.get("budget_contract_hash")
    ):
        return False

    declared_path = receipt.get("transcript_path")
    declared_hash = receipt.get("transcript_sha256")
    run_path = run.get("_run_path")
    if (
        not isinstance(declared_path, str)
        or not declared_path
        or not isinstance(declared_hash, str)
        or not isinstance(run_path, Path)
    ):
        return False
    transcript_path = Path(declared_path)
    if transcript_path.is_absolute() or len(transcript_path.parts) != 1:
        return False
    transcript = run_path.parent / transcript_path
    if transcript.is_symlink() or not transcript.is_file():
        return False
    transcript_bytes = transcript.read_bytes()
    actual_hash = f"sha256:{hashlib.sha256(transcript_bytes).hexdigest()}"
    if actual_hash != declared_hash:
        return False
    for artifact_kind in ("starting", "generated"):
        artifact_path_value = receipt.get(f"{artifact_kind}_artifact_path")
        artifact_hash = receipt.get(f"{artifact_kind}_artifact_sha256")
        if not isinstance(artifact_path_value, str) or not isinstance(artifact_hash, str):
            return False
        artifact_path = Path(artifact_path_value)
        if artifact_path.is_absolute() or len(artifact_path.parts) != 1:
            return False
        artifact = run_path.parent / artifact_path
        if artifact.is_symlink() or not artifact.is_file():
            return False
        if f"sha256:{hashlib.sha256(artifact.read_bytes()).hexdigest()}" != artifact_hash:
            return False
    try:
        transcript_payload = json.loads(transcript_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(transcript_payload, dict):
        return False
    return all(
        transcript_payload.get(key) == receipt.get(key)
        for key in (
            "model_id",
            "input_packet_sha256",
            "budget_contract_sha256",
            "source_commit",
            "starting_artifact_path",
            "starting_artifact_sha256",
            "generated_artifact_path",
            "generated_artifact_sha256",
        )
    )


def _is_explicitly_comparison_ineligible(run: dict[str, Any]) -> bool:
    eligibility = run.get("comparison_eligibility")
    return eligibility is not None and eligibility != COMPARISON_ELIGIBLE


def _has_bounded_repair_lineage(runs: dict[str, dict[str, Any]]) -> bool:
    if {
        name: runs[name].get("comparison_role") for name in VARIANTS
    } != {
        "raw": "raw_authoring",
        "verified": "contract_authoring",
        "repaired": "bounded_repair_child",
    }:
        return False
    raw_receipt = runs["raw"].get("generation_receipt")
    verified_receipt = runs["verified"].get("generation_receipt")
    repaired_receipt = runs["repaired"].get("generation_receipt")
    if not all(
        isinstance(receipt, dict)
        for receipt in (raw_receipt, verified_receipt, repaired_receipt)
    ):
        return False
    verified_generated = verified_receipt.get("generated_artifact_sha256")
    return bool(
        raw_receipt.get("starting_artifact_sha256")
        == verified_receipt.get("starting_artifact_sha256")
        and runs["repaired"].get("parent_variant") == "verified"
        and runs["repaired"].get("parent_generated_artifact_sha256")
        == verified_generated
        and repaired_receipt.get("starting_artifact_sha256") == verified_generated
    )


def evaluate_ablation(run_paths: dict[str, Path]) -> dict[str, Any]:
    if set(run_paths) != VARIANTS:
        raise FailureAblationError("variant_set_invalid")
    runs = {
        name: _load_run(path, expected_variant=name)
        for name, path in run_paths.items()
    }
    keys = (
        "model_contract_hash",
        "input_packet_hash",
        "budget_contract_hash",
        "figure_family",
    )
    if any(
        any(not runs[name].get(key) for name in VARIANTS)
        or len({runs[name][key] for name in VARIANTS}) != 1
        for key in keys
    ):
        raise FailureAblationError("comparison_contract_mismatch")

    variants = {name: _summarize_run(runs[name]) for name in sorted(VARIANTS)}
    raw = variants["raw"]
    verified = variants["verified"]
    repaired = variants["repaired"]
    scientific_pass = all(
        item["scientific_gate"] == "passed" for item in variants.values()
    )
    human_complete = all(
        item["human_verdict_state"] == "recorded" for item in variants.values()
    )
    human_approved = all(
        item.get("human_verdict_decision") == "accepted"
        for item in variants.values()
    )
    reproduction_complete = all(
        item["clean_reproduction"] for item in variants.values()
    )
    correction_time_complete = all(
        isinstance(item["human_correction_minutes"], int | float)
        and not isinstance(item["human_correction_minutes"], bool)
        and item["human_correction_minutes"] >= 0
        for item in variants.values()
    )
    receipts = [runs[name].get("generation_receipt") for name in VARIANTS]
    receipts_bound = (
        not any(_is_explicitly_comparison_ineligible(runs[name]) for name in VARIANTS)
        and all(_has_bound_generation_receipt(runs[name]) for name in VARIANTS)
        and all(
            len({receipt[field] for receipt in receipts if isinstance(receipt, dict)})
            == 1
            for field in ("model_id", "source_commit")
        )
    )
    same_start = receipts_bound and len(
        {
            receipt["starting_artifact_sha256"]
            for receipt in receipts
            if isinstance(receipt, dict)
        }
    ) == 1
    lineage_complete = receipts_bound and _has_bounded_repair_lineage(runs)
    transcript_bound = receipts_bound and (same_start or lineage_complete)
    return {
        "schema": REPORT_SCHEMA,
        "variants": variants,
        "deltas": {
            "verified_vs_raw": _delta(verified, raw),
            "repaired_vs_raw": _delta(repaired, raw),
        },
        "comparison_evidence": (
            "transcript_bound" if transcript_bound else "staged_only"
        ),
        "correction_time_gate": (
            "passed" if correction_time_complete else "failed"
        ),
        "lineage_gate": "passed" if lineage_complete else "failed",
        "reproduction_gate": "passed" if reproduction_complete else "failed",
        "product_claim": (
            "review_eligible"
            if (
                scientific_pass
                and human_complete
                and human_approved
                and reproduction_complete
                and correction_time_complete
                and transcript_bound
                and lineage_complete
            )
            else "not_authorized"
        ),
        "publication_acceptance": "not_claimed",
    }
