from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import authoring_repair_packet
import generation_receipt
import human_decision_record
import yaml

RUN_SCHEMA = "figure-agent.failure-ablation-run.v1"
REPORT_SCHEMA = "figure-agent.failure-ablation-report.v1"
VARIANTS = {"raw", "verified", "repaired"}
SCIENTIFIC_CLASSES = {"semantic", "relation"}
GENERATION_RECEIPT_SCHEMAS = {
    "figure-agent.generation-receipt.v1",
    "figure-agent.generation-receipt.v2",
}
GENERATION_RECEIPT_V2 = "figure-agent.generation-receipt.v2"
REPAIR_LINEAGE_SCHEMA = "figure-agent.bounded-repair-lineage.v1"
REPAIR_PACKET_SCHEMAS = {
    "figure-agent.repair-execution-packet.v3",
    "figure-agent.repair-execution-packet.v4",
}
MATERIALIZATION_RECEIPT_SCHEMA = "figure-agent.repair-materialization-receipt.v2"
REPORT_COLLECTIONS = {
    "figure-agent.text-collisions.v1": "collisions",
    "figure-agent.label-hyphenation.v1": "issues",
    "figure-agent.undeclared-geometry.v1": "candidates",
    "figure-agent.visual-clash.v1": "candidates",
    "figure-agent.human-correction-findings.v1": "findings",
}
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
    if (
        not isinstance(receipt, dict)
        or receipt.get("schema") not in GENERATION_RECEIPT_SCHEMAS
    ):
        return False
    is_v2 = receipt.get("schema") == "figure-agent.generation-receipt.v2"
    required = (
        "model_id",
        "source_commit",
        "starting_artifact_sha256",
        "generated_artifact_sha256",
    )
    if is_v2:
        required += (
            "input_packet_path",
            "shared_task_sha256",
            "context_pack_base_sha256",
        )
    if any(not isinstance(receipt.get(key), str) or not receipt[key] for key in required):
        return False
    if not (
        receipt.get("input_packet_sha256") == run.get("input_packet_hash")
        and receipt.get("budget_contract_sha256") == run.get("budget_contract_hash")
        and (
            not is_v2
            or receipt.get("shared_task_sha256") == run.get("shared_task_hash")
        )
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
    if is_v2:
        input_packet_path = Path(receipt["input_packet_path"])
        if input_packet_path.is_absolute() or len(input_packet_path.parts) != 1:
            return False
        input_packet = run_path.parent / input_packet_path
        if input_packet.is_symlink() or not input_packet.is_file():
            return False
        if (
            f"sha256:{hashlib.sha256(input_packet.read_bytes()).hexdigest()}"
            != receipt["input_packet_sha256"]
        ):
            return False
        try:
            packet, shared_task_sha256, context_pack_base_sha256 = (
                generation_receipt.load_bound_authoring_packet(input_packet)
            )
        except generation_receipt.GenerationReceiptError:
            return False
        if not (
            packet.get("model_id") == receipt["model_id"]
            and shared_task_sha256 == receipt["shared_task_sha256"]
            and context_pack_base_sha256 == receipt["context_pack_base_sha256"]
        ):
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
    transcript_keys = [
        "model_id",
        "input_packet_sha256",
        "budget_contract_sha256",
        "source_commit",
        "starting_artifact_path",
        "starting_artifact_sha256",
        "generated_artifact_path",
        "generated_artifact_sha256",
    ]
    if is_v2:
        transcript_keys[1:1] = ["input_packet_path"]
        transcript_keys[2:2] = [
            "shared_task_sha256",
            "shared_task_binding_source",
            "context_pack_base_sha256",
        ]
    return all(
        transcript_payload.get(key) == receipt.get(key) for key in transcript_keys
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


def _bound_adjacent_artifact(
    run: dict[str, Any],
    lineage: dict[str, Any],
    *,
    path_key: str,
    hash_key: str,
    workspace_root: Path | None = None,
) -> tuple[Path, bytes] | None:
    """Resolve one lineage artifact and verify both path safety and its digest."""
    run_path = run.get("_run_path")
    declared_path = lineage.get(path_key)
    declared_hash = lineage.get(hash_key)
    if (
        not isinstance(run_path, Path)
        or not isinstance(declared_path, str)
        or not declared_path
        or not isinstance(declared_hash, str)
    ):
        return None
    relative_path = Path(declared_path)
    if relative_path.is_absolute() or any(
        part in {"", ".", ".."} for part in relative_path.parts
    ):
        return None
    if len(relative_path.parts) == 1:
        root = run_path.parent.resolve()
    elif workspace_root is not None:
        root = workspace_root.resolve()
    else:
        return None
    artifact = root / relative_path
    current = root
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            return None
    try:
        artifact.resolve(strict=False).relative_to(root)
    except ValueError:
        return None
    if not artifact.is_file():
        return None
    artifact_bytes = artifact.read_bytes()
    if f"sha256:{hashlib.sha256(artifact_bytes).hexdigest()}" != declared_hash:
        return None
    return artifact, artifact_bytes


def _json_mapping(
    artifact: tuple[Path, bytes] | None,
) -> dict[str, Any] | None:
    if artifact is None:
        return None
    try:
        payload = json.loads(artifact[1])
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _bound_packet_reference(
    record: object,
    *,
    adjacent_dir: Path,
    workspace_root: Path | None,
) -> tuple[Path, bytes] | None:
    """Resolve a packet-relative reference without permitting symlink escapes."""
    if not isinstance(record, dict):
        return None
    value = record.get("path")
    declared_hash = record.get("sha256")
    if not isinstance(value, str) or not value or not isinstance(declared_hash, str):
        return None
    relative = Path(value)
    if relative.is_absolute() or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        return None
    root = adjacent_dir.resolve() if len(relative.parts) == 1 else (
        workspace_root.resolve() if workspace_root is not None else None
    )
    if root is None:
        return None
    artifact = root / relative
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return None
    try:
        artifact.resolve(strict=False).relative_to(root)
    except ValueError:
        return None
    if not artifact.is_file():
        return None
    artifact_bytes = artifact.read_bytes()
    if f"sha256:{hashlib.sha256(artifact_bytes).hexdigest()}" != declared_hash:
        return None
    return artifact, artifact_bytes


def _repair_attribution_is_bound(
    *,
    verified_run: dict[str, Any],
    verified_receipt: dict[str, Any],
    repair_packet: dict[str, Any],
    repair_packet_path: Path,
    parent_hash: str,
    workspace_root: Path | None,
) -> bool:
    """Require one exact finding and selector to resolve against the parent bytes."""
    source_record = repair_packet.get("source")
    verified_run_path = verified_run.get("_run_path")
    if not isinstance(source_record, dict) or not isinstance(verified_run_path, Path):
        return False
    parent_source = _bound_packet_reference(
        {
            "path": verified_receipt.get("generated_artifact_path"),
            "sha256": parent_hash,
        },
        adjacent_dir=verified_run_path.parent,
        workspace_root=None,
    )
    packet_source = _bound_packet_reference(
        source_record,
        adjacent_dir=verified_run_path.parent,
        workspace_root=workspace_root,
    )
    if (
        parent_source is None
        or packet_source is None
        or packet_source[0].resolve() != parent_source[0].resolve()
        or source_record.get("sha256") != parent_hash
    ):
        return False

    target_artifact = _bound_packet_reference(
        repair_packet.get("target_contract"),
        adjacent_dir=repair_packet_path.parent,
        workspace_root=workspace_root,
    )
    target_contract = _json_mapping(target_artifact)
    if (
        target_contract is None
        or target_contract.get("schema") != "figure-agent.repair-target-contract.v1"
        or target_contract.get("source_path") != source_record.get("path")
        or target_contract.get("source_sha256") != parent_hash
    ):
        return False

    report_records = repair_packet.get("finding_reports")
    if not isinstance(report_records, list) or not report_records:
        return False
    reports: dict[str, dict[str, Any]] = {}
    for report_record in report_records:
        artifact = _bound_packet_reference(
            report_record,
            adjacent_dir=repair_packet_path.parent,
            workspace_root=workspace_root,
        )
        report = _json_mapping(artifact)
        if (
            artifact is None
            or report is None
            or report.get("schema") != report_record.get("schema")
            or report.get("schema") not in REPORT_COLLECTIONS
        ):
            return False
        report_path = str(report_record.get("path"))
        if report_path in reports:
            return False
        reports[report_path] = report

    targets = target_contract.get("targets")
    editable = repair_packet.get("editable_target")
    if not isinstance(targets, list) or not isinstance(editable, dict):
        return False
    exact_targets = [
        target
        for target in targets
        if isinstance(target, dict)
        and isinstance(target.get("attribution"), dict)
        and target["attribution"].get("state") == "exact"
    ]
    if len(exact_targets) != 1:
        return False
    target = exact_targets[0]
    finding_ref = target.get("finding")
    selector = target.get("selector")
    invariants = target.get("protected_invariants")
    if (
        not isinstance(finding_ref, dict)
        or not isinstance(selector, dict)
        or selector.get("kind") != "semantic_anchor"
        or not isinstance(invariants, list)
    ):
        return False
    report_path = finding_ref.get("report_path")
    finding_id = finding_ref.get("id")
    report = reports.get(str(report_path))
    if report is None or not isinstance(finding_id, str) or not finding_id:
        return False
    if (
        report.get("schema") == "figure-agent.human-correction-findings.v1"
        and report.get("bound_source_sha256") != parent_hash
    ):
        return False
    collection = REPORT_COLLECTIONS[str(report.get("schema"))]
    findings = report.get(collection)
    if not isinstance(findings, list):
        return False
    matches = [
        finding
        for finding in findings
        if isinstance(finding, dict) and finding.get("id") == finding_id
    ]
    if len(matches) != 1:
        return False
    required_selector_fields = ("selector_id", "anchor_start", "anchor_end")
    if any(
        not isinstance(selector.get(field), str) or not selector[field]
        for field in required_selector_fields
    ):
        return False
    try:
        source_text = parent_source[1].decode("utf-8")
    except UnicodeDecodeError:
        return False
    source_lines = source_text.splitlines()
    starts = [
        index for index, line in enumerate(source_lines) if line == selector["anchor_start"]
    ]
    ends = [
        index for index, line in enumerate(source_lines) if line == selector["anchor_end"]
    ]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        return False
    expected_editable = {
        "finding_id": finding_id,
        "finding": matches[0],
        "report_path": report_path,
        "repair_family": target.get("repair_family"),
        "selector": {**selector, "source_hash": parent_hash},
        "protected_invariants": invariants,
    }
    return editable == expected_editable


def _has_bound_repair_lineage(
    *,
    verified_run: dict[str, Any],
    repaired_run: dict[str, Any],
    workspace_root: Path | None = None,
) -> bool:
    """Require a materialized repair to be an authorized child of verified v2 output."""
    lineage = repaired_run.get("repair_lineage")
    verified_receipt = verified_run.get("generation_receipt")
    if (
        not isinstance(lineage, dict)
        or lineage.get("schema") != REPAIR_LINEAGE_SCHEMA
        or lineage.get("parent_variant") != "verified"
        or not isinstance(verified_receipt, dict)
        or "generation_receipt" in repaired_run
    ):
        return False
    parent_hash = verified_receipt.get("generated_artifact_sha256")
    reviewer = lineage.get("authorized_reviewer")
    if (
        not isinstance(parent_hash, str)
        or lineage.get("parent_generated_artifact_sha256") != parent_hash
        or not isinstance(reviewer, str)
        or not reviewer.strip()
    ):
        return False

    repaired_artifact = _bound_adjacent_artifact(
        repaired_run,
        lineage,
        path_key="repaired_artifact_path",
        hash_key="repaired_artifact_sha256",
        workspace_root=workspace_root,
    )
    repair_packet_artifact = _bound_adjacent_artifact(
        repaired_run,
        lineage,
        path_key="repair_packet_path",
        hash_key="repair_packet_sha256",
        workspace_root=workspace_root,
    )
    authorization = _json_mapping(
        _bound_adjacent_artifact(
            repaired_run,
            lineage,
            path_key="human_authorization_path",
            hash_key="human_authorization_sha256",
            workspace_root=workspace_root,
        )
    )
    receipt = _json_mapping(
        _bound_adjacent_artifact(
            repaired_run,
            lineage,
            path_key="finalized_materialization_receipt_path",
            hash_key="finalized_materialization_receipt_sha256",
            workspace_root=workspace_root,
        )
    )
    repair_packet = _json_mapping(repair_packet_artifact)
    if (
        repaired_artifact is None
        or repair_packet_artifact is None
        or repair_packet is None
        or authorization is None
        or receipt is None
    ):
        return False

    repaired_hash = lineage.get("repaired_artifact_sha256")
    packet_hash = repair_packet.get("packet_sha256")
    source = repair_packet.get("source")
    prompt = repair_packet.get("prompt")
    output_path = repair_packet.get("output_path")
    packet_schema = repair_packet.get("schema")
    if packet_schema not in REPAIR_PACKET_SCHEMAS:
        return False
    if not (
        packet_hash
        == authoring_repair_packet.canonical_packet_sha256(repair_packet)
        and repair_packet.get("model_id") == verified_receipt.get("model_id")
        and isinstance(source, dict)
        and source.get("sha256") == parent_hash
        and output_path == lineage.get("repaired_artifact_path")
        and repair_packet.get("author_may_compile") is False
        and repair_packet.get("author_may_write_files") is False
        and repair_packet.get("verification")
        == "external_sequential_compile_required"
        and repair_packet.get("publication_acceptance") == "not_claimed"
        and isinstance(prompt, dict)
        and isinstance(prompt.get("utf8"), str)
        and prompt.get("sha256")
        == "sha256:" + hashlib.sha256(prompt["utf8"].encode("utf-8")).hexdigest()
        and _repair_attribution_is_bound(
            verified_run=verified_run,
            verified_receipt=verified_receipt,
            repair_packet=repair_packet,
            repair_packet_path=repair_packet_artifact[0],
            parent_hash=parent_hash,
            workspace_root=workspace_root,
        )
        and receipt.get("schema") == MATERIALIZATION_RECEIPT_SCHEMA
        and receipt.get("decision")
        == "materialized_machine_verified_human_review_pending"
        and receipt.get("source_sha256") == parent_hash
        and receipt.get("packet_sha256") == packet_hash
        and receipt.get("output_path") == output_path
        and receipt.get("output_sha256") == repaired_hash
        and receipt.get("preview_sha256")
        == authoring_repair_packet.canonical_materialization_preview_sha256(receipt)
        and receipt.get("post_render_verification") == "passed"
        and isinstance(receipt.get("external_compile"), dict)
        and receipt["external_compile"].get("returncode") == 0
        and isinstance(receipt["external_compile"].get("strict_status"), dict)
        and receipt["external_compile"]["strict_status"].get("state") == "passed"
        and receipt.get("publication_acceptance") == "not_claimed"
    ):
        return False
    try:
        normalized = human_decision_record.validate_additive_materialization_authorization(
            authorization,
            fixture=str(repair_packet.get("fixture") or ""),
            packet_schema=str(packet_schema),
            packet_sha256=str(packet_hash),
            output_path=str(output_path),
            output_sha256=str(repaired_hash),
            preview_sha256=str(receipt.get("preview_sha256")),
        )
    except human_decision_record.HumanDecisionRecordError:
        return False
    receipt_authorization = receipt.get("authorization")
    authorization_record_sha = "sha256:" + hashlib.sha256(
        json.dumps(
            authorization,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    return bool(
        normalized.get("reviewer") == reviewer
        and isinstance(receipt_authorization, dict)
        and receipt_authorization.get("reviewer") == reviewer
        and receipt_authorization.get("record_sha256") == authorization_record_sha
        and receipt_authorization.get("authorized_packet_sha256") == packet_hash
        and receipt_authorization.get("authorized_output_path") == output_path
        and receipt_authorization.get("authorized_output_sha256") == repaired_hash
        and receipt_authorization.get("authorized_preview_sha256")
        == receipt.get("preview_sha256")
    )


def evaluate_ablation(
    run_paths: dict[str, Path], *, workspace_root: Path | None = None
) -> dict[str, Any]:
    if set(run_paths) != VARIANTS:
        raise FailureAblationError("variant_set_invalid")
    runs = {
        name: _load_run(path, expected_variant=name)
        for name, path in run_paths.items()
    }
    shared_task_states = {name: runs[name].get("shared_task_hash") for name in VARIANTS}
    if any(shared_task_states.values()) and not all(shared_task_states.values()):
        raise FailureAblationError("comparison_contract_mismatch")
    keys = (
        "model_contract_hash",
        "shared_task_hash" if all(shared_task_states.values()) else "input_packet_hash",
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
    authoring_receipts = [
        runs[name].get("generation_receipt") for name in ("raw", "verified")
    ]
    authoring_transcript_bound = (
        not any(_is_explicitly_comparison_ineligible(runs[name]) for name in VARIANTS)
        and all(
            _has_bound_generation_receipt(runs[name]) for name in ("raw", "verified")
        )
        and all(
            len(
                {
                    receipt[field]
                    for receipt in authoring_receipts
                    if isinstance(receipt, dict)
                }
            )
            == 1
            for field in ("model_id", "source_commit", "starting_artifact_sha256")
        )
    )
    authoring_v2 = all(
        isinstance(receipt, dict)
        and receipt.get("schema") == GENERATION_RECEIPT_V2
        for receipt in authoring_receipts
    )
    strict_repair_bound = authoring_transcript_bound and authoring_v2 and _has_bound_repair_lineage(
        verified_run=runs["verified"],
        repaired_run=runs["repaired"],
        workspace_root=workspace_root,
    )
    legacy_lineage_complete = receipts_bound and _has_bounded_repair_lineage(runs)
    lineage_complete = strict_repair_bound if authoring_v2 else legacy_lineage_complete
    if authoring_v2:
        transcript_bound = authoring_transcript_bound
    else:
        transcript_bound = receipts_bound and (same_start or legacy_lineage_complete)
    return {
        "schema": REPORT_SCHEMA,
        "variants": variants,
        "deltas": {
            "verified_vs_raw": _delta(verified, raw),
            "repaired_vs_raw": _delta(repaired, raw),
        },
        "comparison_evidence": (
            "transcript_and_repair_bound"
            if strict_repair_bound
            else (
                "authoring_transcript_bound_only"
                if authoring_v2 and authoring_transcript_bound
                else "transcript_bound"
                if transcript_bound
                else "staged_only"
            )
        ),
        "correction_time_gate": (
            "passed" if correction_time_complete else "failed"
        ),
        "lineage_gate": "passed" if lineage_complete else "failed",
        **(
            {
                "repair_lineage_evidence": (
                    "bound" if strict_repair_bound else "missing_or_invalid"
                )
            }
            if authoring_v2
            else {}
        ),
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
