from __future__ import annotations

# ruff: noqa: I001

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "quality"))

import authoring_repair_packet
from failure_ablation import FailureAblationError, evaluate_ablation
from generation_receipt import record_generation_receipt


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_DECISION = (
    PLUGIN_ROOT / "benchmarks" / "failure_first_capability_decision.yaml"
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


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


def add_generation_receipt(
    path: Path,
    *,
    model_id: str = "test-model",
    starting_artifact_path: Path | None = None,
) -> None:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if starting_artifact_path is None:
        starting_artifact_path = path.with_name("starting.tex")
        starting_artifact_path.write_text("starting artifact\n", encoding="utf-8")
    generated_artifact_path = path.with_name(f"{path.stem}.generated.tex")
    generated_artifact_path.write_text(
        f"generated {path.stem} artifact\n", encoding="utf-8"
    )
    transcript = {
        "model_id": model_id,
        "input_packet_sha256": payload["input_packet_hash"],
        "budget_contract_sha256": payload["budget_contract_hash"],
        "source_commit": "0123456789abcdef",
        "starting_artifact_path": starting_artifact_path.name,
        "starting_artifact_sha256": "sha256:"
        + hashlib.sha256(starting_artifact_path.read_bytes()).hexdigest(),
        "generated_artifact_path": generated_artifact_path.name,
        "generated_artifact_sha256": "sha256:"
        + hashlib.sha256(generated_artifact_path.read_bytes()).hexdigest(),
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


def add_v2_generation_receipt(path: Path, *, model_id: str = "test-model") -> None:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    neutral_task = "Author a neutral first-pass schematic for the declared topic.\n"
    packet_path = path.with_name(f"{path.stem}.packet.json")
    prompt = (
        "# Bound raw authoring execution\n\n"
        "## Neutral authoring task\n"
        f"{neutral_task}"
        "\n## Provenance and publication boundary\n"
    )
    packet_path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.authoring-execution-packet.v1",
                "model_id": model_id,
                "context_pack": {
                    "schema": "figure-agent.authoring-context-pack.v1",
                    "base_sha256": "sha256:" + "a" * 64,
                },
                "prompt": {
                    "utf8": prompt,
                    "sha256": "sha256:"
                    + hashlib.sha256(prompt.encode()).hexdigest(),
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    budget_path = path.with_name("budget-v2.yaml")
    budget_path.write_text("attempts: 1\n", encoding="utf-8")
    starting_path = path.with_name("starting-v2.tex")
    generated_path = path.with_name(f"{path.stem}.generated-v2.tex")
    starting_path.write_text("starting artifact\n", encoding="utf-8")
    generated_path.write_text(
        "\n".join(
            [
                f"generated {path.stem} artifact",
                "% repair:start",
                "old bounded content",
                "% repair:end",
                "",
            ]
        ),
        encoding="utf-8",
    )
    payload["input_packet_hash"] = _sha256(packet_path)
    payload["budget_contract_hash"] = _sha256(budget_path)
    payload["shared_task_hash"] = (
        "sha256:" + hashlib.sha256(neutral_task.encode()).hexdigest()
    )
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    record_generation_receipt(
        path,
        model_id=model_id,
        source_commit="0123456789abcdef",
        input_packet=packet_path,
        budget_contract=budget_path,
        starting_artifact=starting_path,
        generated_artifact=generated_path,
    )


def add_repair_lineage(
    paths: dict[str, Path],
    *,
    contract_source_hash: str | None = None,
    selector_start: str = "% repair:start",
    duplicate_finding: bool = False,
    editable_repair_family: str = "label_reflow",
) -> None:
    verified = yaml.safe_load(paths["verified"].read_text(encoding="utf-8"))
    repaired = yaml.safe_load(paths["repaired"].read_text(encoding="utf-8"))
    verified_hash = verified["generation_receipt"]["generated_artifact_sha256"]
    repaired["shared_task_hash"] = verified["shared_task_hash"]
    repaired["budget_contract_hash"] = verified["budget_contract_hash"]

    repaired_artifact = paths["repaired"].with_name("repaired.generated.tex")
    repaired_artifact.write_text("bounded repaired artifact\n", encoding="utf-8")
    repaired_hash = _sha256(repaired_artifact)

    repair_packet = paths["repaired"].with_name("repair_packet.json")
    finding_report = paths["repaired"].with_name("human_findings.json")
    finding = {
        "id": "F1",
        "failure_class": "typography",
        "review_outcome": "confirmed_defect",
    }
    finding_report_payload = {
        "schema": "figure-agent.human-correction-findings.v1",
        "bound_source_sha256": verified_hash,
        "findings": [finding, dict(finding)] if duplicate_finding else [finding],
    }
    finding_report.write_text(
        json.dumps(finding_report_payload, sort_keys=True), encoding="utf-8"
    )
    target_contract = paths["repaired"].with_name("target.json")
    selector = {
        "kind": "semantic_anchor",
        "selector_id": "bounded-content",
        "anchor_start": selector_start,
        "anchor_end": "% repair:end",
    }
    target_payload = {
        "schema": "figure-agent.repair-target-contract.v1",
        "source_path": verified["generation_receipt"]["generated_artifact_path"],
        "source_sha256": contract_source_hash or verified_hash,
        "targets": [
            {
                "finding": {"report_path": finding_report.name, "id": "F1"},
                "attribution": {"state": "exact"},
                "selector": selector,
                "repair_family": "label_reflow",
                "protected_invariants": ["old bounded content"],
            }
        ],
    }
    target_contract.write_text(
        json.dumps(target_payload, sort_keys=True), encoding="utf-8"
    )
    prompt = "bounded repair prompt\n"
    packet_payload: dict[str, object] = {
        "schema": "figure-agent.repair-execution-packet.v3",
        "fixture": "synthetic-ablation",
        "model_id": verified["generation_receipt"]["model_id"],
        "source": {
            "path": verified["generation_receipt"]["generated_artifact_path"],
            "sha256": verified_hash,
        },
        "target_contract": {
            "path": target_contract.name,
            "sha256": _sha256(target_contract),
        },
        "finding_reports": [
            {
                "path": finding_report.name,
                "schema": finding_report_payload["schema"],
                "sha256": _sha256(finding_report),
            }
        ],
        "editable_target": {
            "finding_id": "F1",
            "finding": finding,
            "report_path": finding_report.name,
            "repair_family": editable_repair_family,
            "selector": {**selector, "source_hash": verified_hash},
            "protected_invariants": ["old bounded content"],
        },
        "review_only_findings": [],
        "output_path": repaired_artifact.name,
        "repository_output_path": repaired_artifact.name,
        "execution_cwd": ".",
        "change_budget": {
            "max_attempts": 1,
            "max_source_blocks": 1,
            "max_changed_lines": 6,
        },
        "author_may_compile": False,
        "author_may_write_files": False,
        "verification": "external_sequential_compile_required",
        "publication_acceptance": "not_claimed",
        "response_schema": {"type": "object"},
        "prompt": {
            "utf8": prompt,
            "sha256": "sha256:" + hashlib.sha256(prompt.encode()).hexdigest(),
        },
    }
    packet_payload["packet_sha256"] = authoring_repair_packet.canonical_packet_sha256(
        packet_payload
    )
    repair_packet.write_text(
        json.dumps(packet_payload, sort_keys=True), encoding="utf-8"
    )

    authorization = paths["repaired"].with_name("materialization_authorization.json")
    preview = {
        "schema": "figure-agent.repair-materialization-preview.v1",
        "fixture": "synthetic-ablation",
        "packet_sha256": packet_payload["packet_sha256"],
        "source_sha256": verified_hash,
        "output_path": repaired_artifact.name,
        "output_sha256": repaired_hash,
        "changed_source_blocks": 1,
        "changed_lines": 2,
        "preserved_boundary_blank_lines": 0,
        "change_summary": "bounded repair",
        "publication_acceptance": "not_claimed",
    }
    preview_sha256 = authoring_repair_packet.canonical_materialization_preview_sha256(
        preview
    )
    authorization_payload = {
        "schema": "figure-agent.human-decision-record.v1",
        "fixture": "synthetic-ablation",
        "packet_schema": "figure-agent.repair-execution-packet.v3",
        "packet_path": repair_packet.name,
        "packet_recommendation": "materialize_authoring_repair_candidate",
        "queue_run_id": "synthetic-run",
        "decision_kind": "materialize_authoring_repair_candidate",
        "agent_recommendation": "materialize_authoring_repair_candidate",
        "reviewer": "moon",
        "human_decision": "approve this exact additive repair candidate",
        "human_note": "test authorization",
        "follow_up": {"command": "verify repaired candidate"},
        "mutation_boundary": "additive_artifact_materialization_allowed",
        "authorized_packet_sha256": packet_payload["packet_sha256"],
        "authorized_output_path": repaired_artifact.name,
        "authorized_output_sha256": repaired_hash,
        "authorized_preview_sha256": preview_sha256,
    }
    authorization.write_text(
        json.dumps(authorization_payload, sort_keys=True), encoding="utf-8"
    )
    receipt = paths["repaired"].with_name("materialization_receipt.json")
    authorization_record_sha = "sha256:" + hashlib.sha256(
        json.dumps(
            authorization_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    receipt_payload = {
        "schema": "figure-agent.repair-materialization-receipt.v2",
        "decision": "materialized_machine_verified_human_review_pending",
        **{key: value for key, value in preview.items() if key != "schema"},
        "preview_sha256": preview_sha256,
        "authorization": {
            "reviewer": "moon",
            "record_sha256": authorization_record_sha,
            "authorized_packet_sha256": packet_payload["packet_sha256"],
            "authorized_output_path": repaired_artifact.name,
            "authorized_output_sha256": repaired_hash,
            "authorized_preview_sha256": preview_sha256,
        },
        "post_render_verification": "passed",
        "external_compile": {"returncode": 0, "strict_status": {"state": "passed"}},
        "human_review": "pending",
        "publication_acceptance": "not_claimed",
        "recovery_required": False,
    }
    receipt.write_text(json.dumps(receipt_payload, sort_keys=True), encoding="utf-8")

    repaired["repair_lineage"] = {
        "schema": "figure-agent.bounded-repair-lineage.v1",
        "parent_variant": "verified",
        "parent_generated_artifact_sha256": verified_hash,
        "repaired_artifact_path": repaired_artifact.name,
        "repaired_artifact_sha256": repaired_hash,
        "repair_packet_path": repair_packet.name,
        "repair_packet_sha256": _sha256(repair_packet),
        "human_authorization_path": authorization.name,
        "human_authorization_sha256": _sha256(authorization),
        "finalized_materialization_receipt_path": receipt.name,
        "finalized_materialization_receipt_sha256": _sha256(receipt),
        "authorized_reviewer": "moon",
    }
    repaired.pop("generation_receipt", None)
    paths["repaired"].write_text(
        yaml.safe_dump(repaired, sort_keys=False), encoding="utf-8"
    )


def _bound_repair_paths(tmp_path: Path, **lineage_options: object) -> dict[str, Path]:
    paths = write_comparable_runs(tmp_path)
    add_v2_generation_receipt(paths["raw"])
    add_v2_generation_receipt(paths["verified"])
    add_repair_lineage(paths, **lineage_options)
    return paths


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


def test_reports_defect_occurrences_separately_from_finding_kinds(
    tmp_path: Path,
) -> None:
    paths = write_comparable_runs(tmp_path)
    raw = yaml.safe_load(paths["raw"].read_text(encoding="utf-8"))
    raw["findings"][0]["occurrences"] = 3
    paths["raw"].write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")

    report = evaluate_ablation(paths)

    assert report["variants"]["raw"]["confirmed_defect_count"] == 1
    assert report["variants"]["raw"]["confirmed_defect_occurrence_count"] == 3
    assert report["deltas"]["repaired_vs_raw"][
        "confirmed_defect_occurrence_count"
    ] == -3


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


def test_named_human_rejection_blocks_product_claim(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    for path in paths.values():
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload["human_verdict"] = {
            "state": "recorded",
            "reviewer": "moon",
            "decision": "rejected",
        }
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        add_generation_receipt(path)

    report = evaluate_ablation(paths)

    assert all(
        variant["human_verdict_state"] == "recorded"
        for variant in report["variants"].values()
    )
    assert all(
        variant["human_verdict_decision"] == "rejected"
        for variant in report["variants"].values()
    )
    assert report["product_claim"] == "not_authorized"


def test_missing_prospective_correction_time_blocks_product_claim(
    tmp_path: Path,
) -> None:
    paths = write_comparable_runs(tmp_path)
    for path in paths.values():
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload["human_verdict"] = {
            "state": "recorded",
            "reviewer": "moon",
            "decision": "accepted",
        }
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        add_generation_receipt(path)

    report = evaluate_ablation(paths)

    assert report["correction_time_gate"] == "failed"
    assert report["product_claim"] == "not_authorized"


def test_independent_third_generation_is_not_a_bounded_repair_child(
    tmp_path: Path,
) -> None:
    paths = write_comparable_runs(tmp_path)
    correction_minutes = {"raw": 12.0, "verified": 8.0, "repaired": 3.0}
    for variant, path in paths.items():
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload["human_correction_minutes"] = correction_minutes[variant]
        payload["human_verdict"] = {
            "state": "recorded",
            "reviewer": "moon",
            "decision": "accepted",
        }
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        add_generation_receipt(path)

    report = evaluate_ablation(paths)

    assert report["correction_time_gate"] == "passed"
    assert report["lineage_gate"] == "failed"
    assert report["product_claim"] == "not_authorized"


def test_bounded_repair_child_allows_review_eligibility(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    correction_minutes = {"raw": 12.0, "verified": 8.0, "repaired": 3.0}
    roles = {
        "raw": "raw_authoring",
        "verified": "contract_authoring",
        "repaired": "bounded_repair_child",
    }
    for variant in ("raw", "verified"):
        path = paths[variant]
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload["comparison_role"] = roles[variant]
        payload["human_correction_minutes"] = correction_minutes[variant]
        payload["human_verdict"] = {
            "state": "recorded",
            "reviewer": "moon",
            "decision": "accepted",
        }
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        add_generation_receipt(path)

    verified = yaml.safe_load(paths["verified"].read_text(encoding="utf-8"))
    verified_child_source = tmp_path / verified["generation_receipt"][
        "generated_artifact_path"
    ]
    repaired = yaml.safe_load(paths["repaired"].read_text(encoding="utf-8"))
    repaired["comparison_role"] = roles["repaired"]
    repaired["parent_variant"] = "verified"
    repaired["parent_generated_artifact_sha256"] = verified["generation_receipt"][
        "generated_artifact_sha256"
    ]
    repaired["human_correction_minutes"] = correction_minutes["repaired"]
    repaired["human_verdict"] = {
        "state": "recorded",
        "reviewer": "moon",
        "decision": "accepted",
    }
    paths["repaired"].write_text(
        yaml.safe_dump(repaired, sort_keys=False), encoding="utf-8"
    )
    add_generation_receipt(
        paths["repaired"], starting_artifact_path=verified_child_source
    )

    report = evaluate_ablation(paths)

    assert report["correction_time_gate"] == "passed"
    assert report["lineage_gate"] == "passed"
    assert report["product_claim"] == "review_eligible"


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

    assert report["comparison_evidence"] == "transcript_bound"


def test_ablation_accepts_packet_bound_v2_generation_receipts(
    tmp_path: Path,
) -> None:
    paths = write_comparable_runs(tmp_path)
    for path in paths.values():
        add_v2_generation_receipt(path)

    report = evaluate_ablation(paths)

    assert report["comparison_evidence"] == "authoring_transcript_bound_only"


def test_v2_ablation_requires_repaired_output_to_be_a_bound_child(
    tmp_path: Path,
) -> None:
    paths = _bound_repair_paths(tmp_path)
    for path in paths.values():
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload["human_correction_minutes"] = 1.0
        payload["human_verdict"] = {
            "state": "recorded",
            "reviewer": "moon",
            "decision": "accepted",
        }
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    report = evaluate_ablation(paths)

    assert report["comparison_evidence"] == "transcript_and_repair_bound"
    assert report["repair_lineage_evidence"] == "bound"
    assert report["lineage_gate"] == "passed"
    assert report["product_claim"] == "review_eligible"


def test_v2_ablation_does_not_treat_independent_repaired_generation_as_lineage(
    tmp_path: Path,
) -> None:
    paths = write_comparable_runs(tmp_path)
    add_v2_generation_receipt(paths["raw"])
    add_v2_generation_receipt(paths["verified"])
    add_v2_generation_receipt(paths["repaired"])

    report = evaluate_ablation(paths)

    assert report["comparison_evidence"] == "authoring_transcript_bound_only"
    assert report["repair_lineage_evidence"] == "missing_or_invalid"
    assert report["lineage_gate"] == "failed"
    assert report["product_claim"] == "not_authorized"


def test_v2_repair_lineage_rejects_parent_selector_drift(tmp_path: Path) -> None:
    paths = _bound_repair_paths(tmp_path, selector_start="% not present")

    report = evaluate_ablation(paths)

    assert report["comparison_evidence"] == "authoring_transcript_bound_only"
    assert report["repair_lineage_evidence"] == "missing_or_invalid"


def test_v2_repair_lineage_rejects_packet_hash_drift(tmp_path: Path) -> None:
    paths = _bound_repair_paths(tmp_path)
    packet_path = tmp_path / "repair_packet.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["packet_sha256"] = "sha256:" + "6" * 64
    packet_path.write_text(json.dumps(packet, sort_keys=True), encoding="utf-8")
    repaired = yaml.safe_load(paths["repaired"].read_text(encoding="utf-8"))
    repaired["repair_lineage"]["repair_packet_sha256"] = _sha256(packet_path)
    paths["repaired"].write_text(
        yaml.safe_dump(repaired, sort_keys=False), encoding="utf-8"
    )

    report = evaluate_ablation(paths)

    assert report["comparison_evidence"] == "authoring_transcript_bound_only"
    assert report["repair_lineage_evidence"] == "missing_or_invalid"


def test_ablation_rejects_generation_receipts_from_different_models(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    for variant, path in paths.items():
        add_generation_receipt(path, model_id=f"test-model-{variant}")

    report = evaluate_ablation(paths)

    assert report["comparison_evidence"] == "staged_only"


def test_ablation_rejects_explicitly_ineligible_run_even_with_bound_receipts(
    tmp_path: Path,
) -> None:
    paths = write_comparable_runs(tmp_path)
    for path in paths.values():
        add_generation_receipt(path)

    verified = yaml.safe_load(paths["verified"].read_text(encoding="utf-8"))
    verified["comparison_eligibility"] = "feedback_guided_not_equal_input"
    paths["verified"].write_text(
        yaml.safe_dump(verified, sort_keys=False), encoding="utf-8"
    )

    report = evaluate_ablation(paths)

    assert report["comparison_evidence"] == "staged_only"
    assert report["product_claim"] == "not_authorized"


def test_nonreproducible_run_blocks_product_claim_with_human_verdicts(
    tmp_path: Path,
) -> None:
    paths = write_comparable_runs(tmp_path)
    for path in paths.values():
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload["human_verdict"] = {"state": "recorded", "reviewer": "moon"}
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        add_generation_receipt(path)

    repaired = yaml.safe_load(paths["repaired"].read_text(encoding="utf-8"))
    repaired["clean_reproduction"] = False
    paths["repaired"].write_text(
        yaml.safe_dump(repaired, sort_keys=False), encoding="utf-8"
    )

    report = evaluate_ablation(paths)

    assert report["comparison_evidence"] == "transcript_bound"
    assert report["product_claim"] == "not_authorized"


def test_ablation_rejects_generation_receipts_with_changed_artifacts(
    tmp_path: Path,
) -> None:
    paths = write_comparable_runs(tmp_path)
    for path in paths.values():
        add_generation_receipt(path)
    (tmp_path / "raw.generated.tex").write_text("changed artifact\n", encoding="utf-8")

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


def test_two_family_capability_decision_is_evidence_bound_and_non_promotional() -> None:
    decision = yaml.safe_load(CAPABILITY_DECISION.read_text(encoding="utf-8"))

    assert decision["schema"] == "figure-agent.failure-first-capability-decision.v1"
    assert decision["decision"] == "insufficient_evidence"
    assert decision["publication_acceptance"] == "not_claimed"
    assert decision["product_rule_change"] == "not_authorized"
    assert set(decision["families"]) == {"fig1", "fig3"}
    for family in decision["families"].values():
        for input_item in family["inputs"]:
            path = PLUGIN_ROOT / input_item["path"]
            assert input_item["sha256"] == _sha256(path)

    classifications = {item["id"]: item["classification"] for item in decision["capabilities"]}
    assert "promote" not in classifications.values()
    assert classifications["human_scaffold_verdict"] == "human_only"
    assert classifications["direct_svg_primary_authoring"] == "retire"
